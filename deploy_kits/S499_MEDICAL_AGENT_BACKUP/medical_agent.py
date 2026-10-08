#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
medical_agent.py  --  S201 Part 1.  Runs ON THE MEDICAL PC.

Two jobs, both of which exist because of what happened on 25-Aug-2026:

  1. SUPERVISE THE WATCHER. On 25-Aug the capture watcher died at 10:37, in the
     same minute the owner generated a report, and was discovered four hours
     later only because a survey happened to be run. That day's report survived
     purely because manojz's 10-minute pull reads the Marg folder directly. Two
     paths existed and one of them worked; nothing told anyone the other had
     failed. This agent owns the watcher as a child process and restarts it
     within a minute of it dying.

  2. REPORT IN. Nothing on the clinic server can see this machine. Every
     server-side health check watches ARRIVAL at the VPS, so "watcher dead",
     "nothing exported today" and "a report was ignored for being a PDF" are
     all structurally invisible there. This agent writes a heartbeat into the
     clinic Google Drive folder, which syncs up and reaches both Dr Manoj's PC
     and Cowork with no inbound access to this machine at all.

Stdlib only -- the bundled python has no third-party packages.
Reads Marg's folders; writes only inside D:\\SendToClinic and the Drive
FromMedical folder. Never writes inside D:\\MARGERP.

S203 added the Drive MargBackups folder (the offsite copy of the backups).
S499 adds ONE folder on the backup stick, E:\\MargAuto_by_agent -- the agent's
own; it writes and deletes there and nowhere else on the stick.
"""

import datetime as dt
import json
import os
import re
import string
import subprocess
import sys
import time

AGENT_VERSION = "S499.1"

PY = r"D:\SendToClinic\pyportable\python.exe"
WATCHER = r"D:\SendToClinic\marg_watch.py"
SPOOL = r"D:\SendToClinic\_captured"
# S201.7 -- Marg has a SECOND output tree, on C:. A PDF export goes to
#   C:\Users\Public\MARG\<id>\all\REPORT.PDF
# which is (a) not under D:\MARGERP at all, and (b) on a drive manojz
# cannot see -- the Tailscale share is DDrive only. So a PDF report was
# invisible to every part of this pipeline, and no amount of pulling
# from manojz could ever have found it. The watcher runs ON this machine
# and can read C: perfectly well; it simply was never told to look.
# REPORT.PDF is a FIXED slot, overwritten every export -- the same race
# the .XLS slots have, and the same reason capture must be local.
WATCH_DIRS = [r"D:\MARGERP\users", r"D:\MARG REPORTS",
              r"C:\Users\Public\MARG"]
PIDFILE = r"D:\SendToClinic\_watcher.pid"
LOCAL_BEAT = r"D:\SendToClinic\heartbeat.txt"
AGENT_LOG = r"D:\SendToClinic\agent.log"

BEAT_EVERY = 300          # seconds between heartbeats
# S203: the offsite backup leg.
BACKUP_STICK = "E:\\"
SERVERBACKUP = r"D:\MARGERP\serverbackup"
OFFSITE_SUBDIR = "MargBackups"
BACKUP_STATE = r"D:\SendToClinic\backup_state.json"
BACKUP_EVERY = 3600       # at most once an hour; the work is idempotent
BACKUP_WARN_DAYS = 3      # a backup older than this is called out, loudly
BACKUP_BYTES_PER_PASS = 64 * 1024 * 1024  # bounded, but not a trickle
BACKUP_CATCHUP_EVERY = 120                # while a backlog remains
BACKUP_EXTS = (".mbk", ".jmbkh", ".zip", ".bak", ".rar", ".7z")
# S499: the stick leg. The .mbk on the stick is made only when a person accepts
# Marg's prompt; Marg's OWN automatic backup was copied offsite every hour and
# never to the stick. Now it goes to the agent's own folder there.
STICK_AUTO_DIRNAME = "MargAuto_by_agent"
STICK_AUTO_KEEP = 30          # newest sets kept in that folder -- and only there
STICK_SET_WINDOW = 300        # s: written this close to the database file = its set
STICK_QUIET_SECS = 120        # s: a folder written this recently is left alone
STICK_MTIME_SLACK = 3.0       # s: a FAT stick keeps times to two seconds
STICK_ABSENT_LOUD_DAYS = 1    # the stick unplugged longer than this is called out
STICK_FREE_FACTOR = 10        # copy only with ten times the set's size free
FUTURE_SLACK = 86400          # s: a file dated further ahead is ignored for ages
HANDMADE_CALM_DAYS = 7        # an older hand-made backup is mentioned, calmly
ZIP_COMPARE_EVERY = 86400     # s: the file-list comparison, at most once a day
KIT_BACKUP_KEEP = 3           # .before_ copies the prune keeps per kit file
CHECK_EVERY = 30          # seconds between watcher liveness checks
# MUST match marg_watch.py's EXTS. S201.6: .pdf added there, and this list
# was left behind -- so the IGNORED counter would have called a captured
# PDF "ignored". A census that does not track the thing it audits is the
# fault it exists to catch.
WATCHED_EXTS = (".xls", ".xlsx", ".pdf")


def now():
    return dt.datetime.now()


def log(msg):
    """Log to the FILE first, then the console if there is one.

    Under pythonw.exe there is no console and sys.stdout is None. Writing to
    stdout first killed v1 on its very first line, before agent.log existed --
    so the agent failed leaving no trace of why, which is the exact failure
    class this agent was built to end. The file is the record; the console is
    a convenience.
    """
    line = "%s  %s\n" % (now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        # keep the log from growing without bound; this machine has one job
        if os.path.exists(AGENT_LOG) and os.path.getsize(AGENT_LOG) > 512 * 1024:
            with open(AGENT_LOG, "r", encoding="utf-8", errors="replace") as fh:
                tail = fh.readlines()[-2000:]
            with open(AGENT_LOG, "w", encoding="utf-8") as fh:
                fh.writelines(tail)
        with open(AGENT_LOG, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass
    try:
        if sys.stdout is not None:
            sys.stdout.write(line)
            sys.stdout.flush()
    except Exception:                                          # noqa: BLE001
        pass


# --------------------------------------------------------------------------
# where does the clinic Drive live today?
# --------------------------------------------------------------------------
def find_drive_out():
    """The FromMedical folder inside the clinic Drive, or None.

    Searched fresh every heartbeat, never cached: Drive for Desktop changes
    its drive letter when it is switched between streaming and mirrored mode,
    and a cached path would silently stop working the day someone does that.
    """
    roots = []
    for letter in string.ascii_uppercase:
        roots.append("%s:\\My Drive" % letter)
    roots.append(os.path.join(os.environ.get("USERPROFILE", ""), "My Drive"))
    for r in roots:
        p = os.path.join(r, "Clinic Data Archive", "FromMedical")
        if os.path.isdir(p):
            return p
    return None


# --------------------------------------------------------------------------
# updates, delivered down the Drive channel
# --------------------------------------------------------------------------
# An ALLOWLIST, deliberately. The agent copies these names and no others, so a
# stray file appearing in the kit folder can never become code that runs here.
# medical_agent.py is NOT in it: a process that overwrites itself while running
# is how an unattended machine bricks itself. The agent is updated by hand, at
# logon, which is rare; everything it supervises updates itself.
KIT_FILES = {
    "marg_watch.py":     WATCHER,
    "xlsx_stdlib.py":    r"D:\SendToClinic\xlsx_stdlib.py",
    "medical_census.py": r"D:\SendToClinic\medical_census.py",
    # S205: the sender. AF-1 lived in this file and its cure had to be carried
    # here by hand, on a trip to the machine, because nothing could deliver a
    # .bat. That is the fault this version removes.
    "SEND_TO_CLINIC.bat": r"D:\SendToClinic\SEND_TO_CLINIC.bat",
}

# ---------------------------------------------------------------------------
# S205: THE KIT MANIFEST -- so a NEW file never again needs a trip to the PC.
#
# The dict above is the built-in floor and never goes away. On top of it, an
# OPTIONAL file `_kit\KIT_MANIFEST.txt` may declare further deliveries, one
# per line:
#
#       <name-in-kit> | <destination path> | <expected md5>
#
# Lines beginning # are comments. A malformed line is REPORTED and skipped,
# never guessed at.
#
# WHY THIS IS STILL SAFE -- the guarantee the allowlist gave is kept by three
# rules, not by the hardcoded list:
#
#   1. THE DESTINATION MUST LIE UNDER KIT_DEST_ROOT. Nothing can be written to
#      Startup, to D:\MARGERP, to Windows, or anywhere else. A manifest cannot
#      widen its own reach.
#   2. THE MD5 MUST BE DECLARED AND MUST MATCH before anything is copied. A
#      half-synced Drive placeholder, a truncated file or a swapped one is
#      refused. This is STRONGER than the compile check it replaces for
#      non-python files: it proves the file is the one intended, not merely
#      that it parses.
#   3. .py FILES ARE STILL COMPILE-CHECKED, in addition to the hash.
#
# So the worst a tampered manifest can do is install bytes that are already
# sitting in the kit folder, to a path under D:\SendToClinic. That is a
# bounded blast radius, stated out loud rather than assumed.
#
# medical_agent.py remains excluded by name, manifest or not. A process that
# overwrites itself while running is still how an unattended machine bricks
# itself, and no convenience is worth reopening that.
# ---------------------------------------------------------------------------
KIT_DEST_ROOT = r"D:\SendToClinic"
KIT_MANIFEST = "KIT_MANIFEST.txt"
KIT_NEVER = ("medical_agent.py",)
# Only a watcher change is worth restarting the watcher for.
RESTART_FOR = ("marg_watch.py",)
# After this many consecutive failures the agent stops trying until the
# source bytes change. A retry loop that cannot succeed is not resilience.
MAX_KIT_TRIES = 3

# Formats a Marg report could plausibly come out as, which the watcher
# does NOT take. .xls/.xlsx/.pdf are absent because they ARE taken.
REPORTABLE_EXTS = (".csv", ".doc", ".docx", ".rtf", ".htm",
                   ".html", ".xml", ".ods")

# S201.10 -- Marg's own working files that happen to wear a reportable
# extension. margstart.csv sits in every user folder and never changes, so it
# would hold this counter at 2 for ever. A number that is never zero tells you
# nothing on the day it should have been 3.
SKIP_NAMES = ("margstart.csv",)
SKIP_PREFIXES = ("marg_system_shutdown", "user_", "~$")


def find_drive_in():
    """The ToMedical folder inside the clinic Drive, or None."""
    out = find_drive_out()
    if not out:
        return None
    inn = os.path.join(os.path.dirname(out), "ToMedical")
    return inn if os.path.isdir(inn) else None


def agent_drift():
    """Is the medical_agent.py running here the one sitting on Drive?

    S201.11. The agent updates the KIT (watcher, xlsx reader, census) but
    deliberately NEVER updates ITSELF: a supervisor that overwrites its own
    file while running can leave this PC with no watcher at all. The cost of
    that safety is that a new agent needs a human to double-click
    INSTALL_AGENT.bat -- and on 25-Aug S201.10 sat on Drive for hours while
    S201.9 kept running, because nobody was told. The heartbeat could not
    show it: it printed the running version with nothing to compare it to.

    So the agent does not update itself, it REPORTS on itself. Comparison is
    by md5, never by version string alone -- a filename is not provenance
    (D188), and neither is a constant a file claims about itself.

    S499: the heartbeat's FIX line names ToMedical\\INSTALL_AGENT_S499.bat
    in the Drive folder found here, with no drive letter of its own. The old
    INSTALL_AGENT.bat (v3, 25-Aug) stops the S387 guard and must not be run.
    """
    out = {"running_version": AGENT_VERSION, "checked": False,
           "drive_version": None, "differs": False,
           "running_md5": None, "drive_md5": None, "note": ""}
    try:
        here = os.path.abspath(__file__)
    except NameError:
        out["note"] = "cannot locate the running file"
        return out
    out["running_md5"] = _md5(here)
    inn = find_drive_in()
    if not inn:
        out["note"] = "ToMedical folder not found"
        return out
    out["installer"] = os.path.join(inn, "INSTALL_AGENT_S499.bat")
    there = os.path.join(inn, "medical_agent.py")
    if not os.path.isfile(there):
        out["note"] = "no medical_agent.py on Drive"
        return out
    out["drive_md5"] = _md5(there)
    if not out["drive_md5"] or not out["running_md5"]:
        out["note"] = "could not hash one of the two copies"
        return out
    try:
        with open(there, "r", encoding="utf-8", errors="replace") as fh:
            head = fh.read(4096)
        m = re.search(r"""AGENT_VERSION\s*=\s*["']([^"']+)["']""", head)
        out["drive_version"] = m.group(1) if m else None
    except OSError:
        pass
    out["checked"] = True
    out["differs"] = (out["drive_md5"] != out["running_md5"])
    return out


def find_drive_kit():
    """The _kit folder inside ToMedical, or None."""
    out = find_drive_out()
    if not out:
        return None
    kit = os.path.join(os.path.dirname(out), "ToMedical", "_kit")
    return kit if os.path.isdir(kit) else None


def _md5(path):
    import hashlib
    h = hashlib.md5()
    try:
        with open(path, "rb") as fh:
            for c in iter(lambda: fh.read(1 << 20), b""):
                h.update(c)
    except OSError:
        return None
    return h.hexdigest()


def _win_norm(p):
    """Normalise a WINDOWS path without touching the filesystem.

    Deliberately NOT os.path.abspath/normcase: those give the answer of the
    machine running them, so this check would be correct on the medical PC and
    meaningless anywhere it could be TESTED before being deployed. That is
    F-217's exact shape -- a check that can only pass where the thing it
    guards cannot be exercised. This resolves `.` and `..` by hand and gives
    the same answer on any platform.
    """
    p = str(p).replace("/", "\\")
    parts = []
    for seg in p.split("\\"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    return "\\".join(parts).lower()


def _dest_ok(dest):
    r"""The destination must lie inside KIT_DEST_ROOT.

    `..` is resolved first, so a manifest cannot walk out with
    D:\SendToClinic\..\..\Windows\System32\x.dll, and a different drive or a
    UNC path does not match at all.
    """
    try:
        root, want = _win_norm(KIT_DEST_ROOT), _win_norm(dest)
        return bool(root) and (want == root or want.startswith(root + "\\"))
    except Exception:                                          # noqa: BLE001
        return False


def manifest_files(kit):
    """KIT_FILES, plus whatever `_kit\KIT_MANIFEST.txt` legally adds.

    Returns (mapping, notes). `notes` carries a line per rejected entry so the
    refusal reaches the heartbeat instead of a log nobody reads -- the same
    reason kit_status() reports a folder it cannot find.
    """
    out = dict(KIT_FILES)
    want = {}
    notes = []
    if not kit:
        return out, want, notes
    path = os.path.join(kit, KIT_MANIFEST)
    if not os.path.isfile(path):
        return out, want, notes
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except OSError as ex:
        notes.append("manifest unreadable: %s" % ex)
        return out, want, notes
    for n, line in enumerate(raw.splitlines(), 1):
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        parts = [p.strip() for p in t.split("|")]
        if len(parts) != 3 or not all(parts):
            notes.append("manifest line %d ignored: expected "
                         "name | destination | md5" % n)
            continue
        name, dest, md5 = parts
        if name in KIT_NEVER:
            notes.append("manifest line %d REFUSED: %s can never be delivered "
                         "this way" % (n, name))
            continue
        if not _dest_ok(dest):
            notes.append("manifest line %d REFUSED: %s is outside %s"
                         % (n, dest, KIT_DEST_ROOT))
            continue
        if len(md5) != 32:
            notes.append("manifest line %d REFUSED: %s has no usable md5"
                         % (n, name))
            continue
        out[name] = dest
        want[name] = md5.lower()
    return out, want, notes


def _kit_gate_ok(name, src, want_md5=None):
    """May this file be installed?

    A .py must COMPILE. Anything else cannot be compile-checked, so it must be
    ACCOMPANIED BY ITS INTENDED md5 -- either from the manifest, or from a
    companion `<name>.md5` beside it in the kit folder. A non-python file that
    arrives with no declared hash is refused, on purpose: there would be
    nothing to check it against, and 'it was in the folder' is not a check.
    """
    if name.lower().endswith(".py"):
        return _compiles(src), "does not compile"
    if not want_md5:
        try:
            with open(src + ".md5", "r", encoding="utf-8-sig",
                      errors="replace") as fh:
                want_md5 = fh.read().split()[0].strip().lower()
        except Exception:                                      # noqa: BLE001
            return False, ("no declared md5 -- a non-python file needs one, "
                           "either in %s or in a companion .md5" % KIT_MANIFEST)
    got = _md5(src)
    if got is None:
        return False, "unreadable (Drive placeholder?)"
    if got.lower() != want_md5:
        return False, ("md5 does not match what was declared (%s vs %s)"
                       % (got[:8], want_md5[:8]))
    return True, ""


def _compiles(path):
    """Refuse to install a file python cannot even parse.

    Cheap, and it removes the worst outcome of remote delivery: a half-synced
    or corrupted script replacing a working one on a machine nobody is sitting
    at. If it will not compile it does not go in.
    """
    import py_compile
    import tempfile
    try:
        py_compile.compile(path, cfile=os.path.join(tempfile.gettempdir(),
                                                    "_kitcheck.pyc"),
                           doraise=True)
        return True
    except Exception:                                          # noqa: BLE001
        return False


def kit_status():
    """(folder_or_None, {name: {...}}) -- what the kit folder holds right now.

    Reported in EVERY heartbeat, whether or not anything needs doing. v3 said
    nothing when the folder was missing or a file was unreadable, so "not
    synced yet", "nothing to do" and "silently failing" all looked identical
    from the clinic side. An update mechanism that cannot be observed is not
    better than no update mechanism.
    """
    kit = find_drive_kit()
    info = {}
    if not kit:
        return None, info
    files, _want, _notes = manifest_files(kit)
    for _n in _notes:
        info["! " + _n[:60]] = {"in_kit": False, "note": _n}
    for name, dest in files.items():
        src = os.path.join(kit, name)
        row = {"in_kit": os.path.isfile(src)}
        if row["in_kit"]:
            row["kit_md5"] = _md5(src)
            if row["kit_md5"] is None:
                row["note"] = "present but unreadable (Drive placeholder?)"
        row["installed_md5"] = _md5(dest)
        row["matches"] = bool(row.get("kit_md5")
                              and row["kit_md5"] == row["installed_md5"])
        info[name] = row
    return kit, info


def pending_kit(failures=None):
    """Files that genuinely need installing: readable, different, and they
    compile. Anything else is reported, not attempted."""
    kit, info = kit_status()
    out = []
    if not kit:
        return out
    files, want, _notes = manifest_files(kit)
    for name, row in info.items():
        if name.startswith("! "):
            continue                      # a manifest complaint, not a file
        if not row.get("in_kit") or not row.get("kit_md5") or row["matches"]:
            continue
        src = os.path.join(kit, name)
        ok, why = _kit_gate_ok(name, src, want.get(name))
        if not ok:
            log("REFUSING kit %s -- %s" % (name, why))
            row["note"] = "REFUSED: %s" % why
            continue
        f = (failures or {}).get(row["kit_md5"])
        if f and f["tries"] >= MAX_KIT_TRIES:
            continue                      # given up until the bytes change
        dest = files.get(name)
        if not dest or not _dest_ok(dest):
            log("REFUSING kit %s -- destination is outside %s"
                % (name, KIT_DEST_ROOT))
            continue
        out.append((name, src, dest, row["kit_md5"]))
    return out


def install_kit(items, failures):
    """Install, then VERIFY by hash. Called only while the watcher is stopped.

    S201.5 — three faults from S201.3, all found by watching it loop:

      1. It wrote a BACKUP before knowing the write could succeed. 343 failed
         attempts left 343 backups (4.1 MB) on the medical PC in three hours,
         mirrored to manojz. Now: clear read-only, prove the destination is
         writable, and only then take a backup.
      2. The backup was named by timestamp, so every retry made a NEW one.
         Now it is named by the SOURCE md5 -- one backup per distinct update,
         however many times it is attempted.
      3. It retried forever, every 30 seconds, logging the same line. Now a
         file that fails MAX_KIT_TRIES times is left alone until its source
         bytes change, and the refusal is carried in the heartbeat instead of
         only in a log nobody reads.
    """
    import shutil as _sh
    import stat as _st
    done = []
    for name, src, dest, want in items:
        try:
            # S205: a manifest may deliver into a subfolder that does not exist
            # yet (a vendored package, for instance). Creating it is bounded by
            # _dest_ok, which pending_kit already asserted.
            _d = os.path.dirname(dest)
            if _d and not os.path.isdir(_d):
                os.makedirs(_d)
                log("created %s for a manifest delivery" % _d)
            if os.path.exists(dest):
                try:
                    os.chmod(dest, _st.S_IWRITE)       # clear read-only
                except OSError:
                    pass
                if not os.access(dest, os.W_OK):
                    raise OSError("destination is not writable")
                bak = "%s.before_%s" % (dest, want[:8])
                if not os.path.exists(bak):
                    _sh.copy2(dest, bak)
            _sh.copy2(src, dest)
        except OSError as ex:
            f = failures.setdefault(want, {"tries": 0, "last": ""})
            f["tries"] += 1
            f["last"] = str(ex)
            if f["tries"] <= MAX_KIT_TRIES:
                log("could not install %s (try %d/%d): %s"
                    % (name, f["tries"], MAX_KIT_TRIES, ex))
            if f["tries"] == MAX_KIT_TRIES:
                log("GIVING UP on %s until its bytes change. It is reported in "
                    "the heartbeat." % name)
            continue
        got = _md5(dest)
        if got == want:
            log("installed %s from the kit and verified (%s)" % (name, want[:8]))
            failures.pop(want, None)
            done.append(name)
        else:
            log("INSTALL OF %s FAILED VERIFICATION (wanted %s, on disk %s)"
                % (name, want[:8], (got or "unreadable")[:8]))
    return done


# S499: what the last prune did, so the heartbeat can judge the prune by the
# prune's own rule instead of by a number picked in S201 (see kit_backup_state).
_PRUNE_LAST = {"ran": False, "removed": 0, "failed": 0, "failed_names": [],
               "covered": []}


def _kit_dests():
    """Every file the kit channel manages on this PC: the built-in list plus
    whatever the manifest legally adds.

    S499. The prune and its count walked KIT_FILES only, so a file delivered by
    KIT_MANIFEST.txt had its .before_ copies neither pruned nor counted.
    """
    try:
        files, _want, _notes = manifest_files(find_drive_kit())
    except Exception:                                          # noqa: BLE001
        files = dict(KIT_FILES)
    seen, out = set(), []
    for dest in files.values():
        k = _win_norm(dest)
        if k not in seen:
            seen.add(k)
            out.append(dest)
    return out


def _kit_baks(dest):
    """(folder, [names]) of the .before_ copies lying beside one kit file."""
    d = os.path.dirname(dest) or "."
    base = os.path.basename(dest) + ".before_"
    return d, [f for f in os.listdir(d) if f.startswith(base)]


def prune_kit_backups(keep=KIT_BACKUP_KEEP):
    """Keep the newest few .before_ backups beside each kit file; bin the rest.

    S201.6: clear the read-only flag before removing, and report FAILURES as
    well as successes. S201.5 removed nothing and said nothing, because every
    os.remove hit the same read-only attribute that had blocked the install,
    and the log line only fired when something was actually deleted. A tidy-up
    that cannot tidy, silently, is the fault it was written to clean up after.

    S499: every file the kit channel manages, the manifest's included, and the
    result is kept for the heartbeat.
    """
    import stat as _st
    removed = failed = 0
    failed_names, covered = [], []
    for dest in _kit_dests():
        try:
            d, names = _kit_baks(dest)
            baks = sorted(names,
                          key=lambda f: os.path.getmtime(os.path.join(d, f)),
                          reverse=True)
        except OSError:
            continue
        covered.append(_win_norm(dest))
        for f in baks[keep:]:
            fp = os.path.join(d, f)
            try:
                try:
                    os.chmod(fp, _st.S_IWRITE)
                except OSError:
                    pass
                os.remove(fp)
                removed += 1
            except OSError:
                failed += 1
                failed_names.append(fp)
    _PRUNE_LAST.update({"ran": True, "removed": removed, "failed": failed,
                        "failed_names": failed_names[:5], "covered": covered})
    if removed or failed:
        log("pruned %d stale kit backup(s)%s"
            % (removed, ("; %d could NOT be removed" % failed) if failed else ""))
    return removed, failed


def backup_count():
    """How many .before_ files are lying beside the kit files right now."""
    n = 0
    for dest in _kit_dests():
        try:
            n += len(_kit_baks(dest)[1])
        except OSError:
            pass
    return n


def kit_backup_state(keep=KIT_BACKUP_KEEP):
    """The .before_ copies, judged by what the prune actually allows.

    S499. The heartbeat said "the prune is not working" above FIVE files, while
    the prune keeps THREE per kit file -- twelve are legal for the four
    built-in files alone -- so the line was a false alarm for weeks. Now it
    fires only when a prune could not remove a file, or when a file the prune
    has been over still has more than it keeps.
    """
    dests = _kit_dests()
    covered = set(_PRUNE_LAST.get("covered") or [])
    n, over = 0, []
    for dest in dests:
        try:
            c = len(_kit_baks(dest)[1])
        except OSError:
            continue
        n += c
        if c > keep and _win_norm(dest) in covered:
            over.append("%s: %d" % (os.path.basename(dest), c))
    return {"count": n, "files": len(dests), "keep": keep,
            "allowed": keep * len(dests), "over": over[:5],
            "prune_ran": bool(_PRUNE_LAST.get("ran")),
            "prune_failed": int(_PRUNE_LAST.get("failed") or 0),
            "prune_failed_names": list(_PRUNE_LAST.get("failed_names") or [])[:3]}


# --------------------------------------------------------------------------
# the watcher, as a supervised child
# --------------------------------------------------------------------------
def watcher_cmd():
    cmd = [PY, WATCHER, "--watch"] + WATCH_DIRS + ["--spool", SPOOL]
    return cmd


def kill_pid(pid):
    try:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                       capture_output=True, timeout=15)
    except Exception:                                          # noqa: BLE001
        pass


def kill_stale_watcher():
    """A watcher left behind by a previous agent, or by the old autostart.

    Only ever kills the pid this agent itself recorded -- never every python on
    the machine, because this agent is python too.
    """
    try:
        if not os.path.exists(PIDFILE):
            return
        with open(PIDFILE, "r", encoding="utf-8") as fh:
            pid = int((fh.read() or "0").strip() or 0)
        if pid:
            log("killing stale watcher pid %d from a previous run" % pid)
            kill_pid(pid)
        os.remove(PIDFILE)
    except Exception as ex:                                    # noqa: BLE001
        log("could not clear the stale pid file: %s" % ex)


def start_watcher():
    os.makedirs(SPOOL, exist_ok=True)
    flags = 0
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        flags = subprocess.CREATE_NO_WINDOW
    p = subprocess.Popen(watcher_cmd(), creationflags=flags,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        with open(PIDFILE, "w", encoding="utf-8") as fh:
            fh.write(str(p.pid))
    except OSError:
        pass
    log("watcher started, pid %d, watching %s" % (p.pid, " + ".join(WATCH_DIRS)))
    return p


# --------------------------------------------------------------------------
# what the heartbeat carries
# --------------------------------------------------------------------------
def captures_today():
    """(count today, newest name, newest iso time) from the capture spool."""
    today = now().date()
    n, newest, newest_t = 0, None, None
    try:
        for f in os.listdir(SPOOL):
            p = os.path.join(SPOOL, f)
            if not os.path.isfile(p):
                continue
            m = dt.datetime.fromtimestamp(os.path.getmtime(p))
            if m.date() == today:
                n += 1
            if newest_t is None or m > newest_t:
                newest, newest_t = f, m
    except OSError:
        pass
    return n, newest, newest_t.isoformat(timespec="seconds") if newest_t else None


def ignored_files(days=2):
    """Files in the WATCHED folders that the watcher will never take.

    This is the PDF blind spot made countable. A report printed or exported as
    PDF lands in a folder we watch and is skipped for its extension, with no
    log line anywhere. Nothing downstream can see it, and the alarm that does
    eventually fire blames the network. Counting it here is the only place the
    truth exists.
    """
    cut = now() - dt.timedelta(days=days)
    out = []
    for d in WATCH_DIRS:
        for base, _dirs, files in os.walk(d):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                # S201.8 -- an ALLOWLIST, not a denylist. Watching Marg's C:
                # tree brought its whole working database into view (.dbf,
                # .cdx, .idx, .fpt, .xff, .C18) and 18 of them were reported as
                # "ignored" on the first beat. None of those is a report, and
                # no denylist would have stayed ahead of them.
                #
                # The question this counter exists to answer is narrow: "is
                # there something here that COULD be a report and that the
                # watcher cannot take?" Only these can be. Everything else is
                # silence, deliberately.
                if ext not in REPORTABLE_EXTS:
                    continue
                low = f.lower()
                if low in SKIP_NAMES or low.startswith(SKIP_PREFIXES):
                    continue
                p = os.path.join(base, f)
                try:
                    m = dt.datetime.fromtimestamp(os.path.getmtime(p))
                except OSError:
                    continue
                if m >= cut:
                    out.append({"path": p, "ext": ext,
                                "when": m.isoformat(timespec="seconds")})
    return out


def marg_slots():
    """The report slots Marg writes into, and when each was last written."""
    out = []
    root = WATCH_DIRS[0]
    try:
        for user in os.listdir(root):
            rd = os.path.join(root, user, "report")
            if not os.path.isdir(rd):
                continue
            for f in os.listdir(rd):
                if not f.lower().endswith(WATCHED_EXTS):
                    continue
                p = os.path.join(rd, f)
                try:
                    m = dt.datetime.fromtimestamp(os.path.getmtime(p))
                except OSError:
                    continue
                out.append({"slot": "%s/%s" % (user, f),
                            "when": m.isoformat(timespec="seconds"),
                            "bytes": os.path.getsize(p)})
    except OSError:
        pass
    return out


# --------------------------------------------------------------------------
# S203: the offsite backup leg
# --------------------------------------------------------------------------
def _is_backup_file(name):
    low = name.lower()
    return low.endswith(BACKUP_EXTS) or "_c18_" in low or "_c17_" in low


def _offsite_dir():
    """<clinic Drive>\\MargBackups, created if absent. None if Drive is away."""
    out = find_drive_out()
    if not out:
        return None
    d = os.path.join(os.path.dirname(out), OFFSITE_SUBDIR)
    try:
        if not os.path.isdir(d):
            os.makedirs(d)
    except OSError:
        return None
    return d


def _backup_sources():
    """(path, size, mtime) for every closed backup file worth copying.

    D:\\MARGERP\\Data is deliberately absent: open tables, see the header."""
    rows = []
    if os.path.isdir(BACKUP_STICK):
        for base, dirs, files in os.walk(BACKUP_STICK):
            dirs[:] = [d for d in dirs if d.lower() not in
                       ("system volume information", "$recycle.bin")]
            # S499: the agent's own folder at the top of the stick holds copies
            # of serverbackup, which goes offsite from D: itself (below).
            if _same_dir(base, BACKUP_STICK):
                dirs[:] = [d for d in dirs
                           if d.lower() != STICK_AUTO_DIRNAME.lower()]
            for f in files:
                if not _is_backup_file(f):
                    continue
                p = os.path.join(base, f)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                rows.append((p, st.st_size, st.st_mtime))
    sb = []
    if os.path.isdir(SERVERBACKUP):
        for f in os.listdir(SERVERBACKUP):
            p = os.path.join(SERVERBACKUP, f)
            if not os.path.isfile(p):
                continue
            try:
                st = os.stat(p)
            except OSError:
                continue
            sb.append((p, st.st_size, st.st_mtime))
    sb.sort(key=lambda r: r[2], reverse=True)
    rows.extend(sb[:6])
    rows.sort(key=lambda r: r[2], reverse=True)
    return rows


def _copy_one(src, dst):
    """Copy via a temp name, then rename. A half-copied file must never be
    mistaken for a whole one -- that is how a backup lies."""
    tmp = dst + ".part"
    try:
        with open(src, "rb") as fi, open(tmp, "wb") as fo:
            while True:
                chunk = fi.read(1 << 20)
                if not chunk:
                    break
                fo.write(chunk)
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(tmp, dst)
        return True, ""
    except OSError as e:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        return False, "%s: %s" % (e.__class__.__name__, e)


# --------------------------------------------------------------------------
# S499: the stick leg, the ages said truthfully, the file-list comparison
# --------------------------------------------------------------------------
_SET_NAME = re.compile(r"^\d{4}-\d\d-\d\d_\d{6}$")
_NOT_WHOLE = (".part", ".copying")


def _when(ts, fmt="%d-%b-%Y %H:%M"):
    """A file's time in words -- or '?' for a time Windows cannot express (a
    year before 1970 or after 9999 raises OverflowError / OSError /
    ValueError there). One bad file must never stop a pass or a heartbeat."""
    try:
        return dt.datetime.fromtimestamp(float(ts)).strftime(fmt)
    except (OverflowError, OSError, ValueError, TypeError):
        return "?"


def _same_dir(a, b):
    return (os.path.normcase(os.path.abspath(a))
            == os.path.normcase(os.path.abspath(b)))


def _is_marg_blob(name):
    """Marg's own automatic database backup, <n>_c18_d_<x>.<y>_<n>.

    The financial year sits in the name (c18 = 2026-27, c17 the year before),
    so the digits are not spelt out: next April's files will say c19."""
    return re.search(r"_c\d\d_", name.lower()) is not None


def _stick_auto_dir():
    return os.path.join(BACKUP_STICK, STICK_AUTO_DIRNAME)


def _serverbackup_files():
    """(path, size, mtime) for every file in Marg's own backup folder, newest
    first. Empty if the folder is away or cannot be read."""
    sb = []
    try:
        if os.path.isdir(SERVERBACKUP):
            for f in os.listdir(SERVERBACKUP):
                p = os.path.join(SERVERBACKUP, f)
                if not os.path.isfile(p):
                    continue
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                sb.append((p, st.st_size, st.st_mtime))
    except OSError:
        pass
    sb.sort(key=lambda r: r[2], reverse=True)
    return sb


def _newest_auto_set(sb):
    """Marg's newest automatic backup as a SET: the newest database file first,
    then every file written in that folder within STICK_SET_WINDOW of it.

    Measured on this PC (census, 26-Aug-2026): <weekday>.mst is written first,
    the database file under a minute later, <n>_d01_retail_<x> seconds after
    that. A day on which Marg writes only the .mst has no database file and is
    not a backup. Returns ([rows], why_not)."""
    blobs = [r for r in sb if _is_marg_blob(os.path.basename(r[0]))]
    if not blobs:
        return [], "there is no database file in %s" % SERVERBACKUP
    blob = blobs[0]
    rows = [blob] + [r for r in sb if r is not blob
                     and abs(r[2] - blob[2]) <= STICK_SET_WINDOW]
    return rows[:12], ""


def _copy_verified(src, dst, size, mtime):
    """Copy src to dst so that dst only ever appears WHOLE, CHECKED and DATED.

    Through a temp name (_copy_one), then: the size, the md5 against the
    source, the source not changed meanwhile, the source's own time put on the
    copy (so its age stays the backup's age, not the copy's) -- and only then
    the real name."""
    tmp = dst + ".copying"
    ok, err = _copy_one(src, tmp)
    if not ok:
        return False, err
    try:
        with open(tmp, "rb+") as fh:           # to the stick itself, not a cache,
            os.fsync(fh.fileno())               # before the md5 is believed
        if os.path.getsize(tmp) != size:
            raise OSError("the copy's size differs from the source's")
        _a, _b = _md5(src), _md5(tmp)
        if not _a or _a != _b:
            raise OSError("the copy's md5 differs from the source's")
        _s = os.stat(src)
        if _s.st_size != size or _s.st_mtime != mtime:
            raise OSError("the source changed while it was being copied")
        os.utime(tmp, (mtime, mtime))
        os.replace(tmp, dst)
        return True, ""
    except OSError as e:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        return False, "%s: %s" % (e.__class__.__name__, e)


def _stick_auto_blobs():
    """(path, size, mtime) of every database file in the agent's own folder on
    the stick, newest first. The time is the SOURCE's, kept by _copy_verified."""
    rows = []
    auto = _stick_auto_dir()
    try:
        sets = [d for d in os.listdir(auto) if _SET_NAME.match(d)]
    except OSError:
        return rows
    for d in sets:
        p = os.path.join(auto, d)
        if not _really_inside(p, auto):
            continue
        try:
            for f in os.listdir(p):
                if f.endswith(_NOT_WHOLE) or not _is_marg_blob(f):
                    continue
                fp = os.path.join(p, f)
                if not os.path.isfile(fp):
                    continue
                st = os.stat(fp)
                rows.append((fp, st.st_size, st.st_mtime))
        except OSError:
            continue
    rows.sort(key=lambda r: r[2], reverse=True)
    return rows


def _really_inside(path, top):
    """True only when `path` itself -- links and junctions resolved -- lies
    inside `top`, and is not a link. A link with a set's name must never lead
    the pruner out of the agent's own folder."""
    try:
        if os.path.islink(path):
            return False
        rp = os.path.normcase(os.path.realpath(path))
        rt = os.path.normcase(os.path.realpath(top))
        return rp.startswith(rt.rstrip("\\/") + os.sep)
    except (OSError, ValueError):
        return False


def _prune_stick_sets(auto, keep=STICK_AUTO_KEEP):
    """Keep the newest `keep` sets in the agent's own folder; remove the older.

    ONLY inside that folder, ONLY folders this agent named itself
    (YYYY-MM-DD_HHMMSS), ONLY the files directly inside them. Nothing else on
    the stick is listed for removal, let alone removed -- not a hand-made
    backup, not a folder anyone else made. Returns (kept, removed, errors)."""
    import stat as _st
    kept = removed = 0
    errors = []
    if not _same_dir(os.path.dirname(os.path.abspath(auto)), BACKUP_STICK) \
            or os.path.basename(auto) != STICK_AUTO_DIRNAME:
        return kept, removed, ["refused: %s is not the agent's own folder" % auto]
    try:
        names = sorted((d for d in os.listdir(auto) if _SET_NAME.match(d)
                        and os.path.isdir(os.path.join(auto, d))), reverse=True)
    except OSError:
        return kept, removed, errors
    with_blob = 0
    for d in names:
        p = os.path.join(auto, d)
        if not _really_inside(p, auto):
            errors.append("refused: %s is a link or leads outside %s -- left alone"
                          % (d, auto))
            continue
        if with_blob < keep:
            try:
                has = any(_is_marg_blob(f) and not f.endswith(_NOT_WHOLE)
                          for f in os.listdir(p))
            except OSError:
                has = False
            if has:
                with_blob += 1
                kept += 1
            else:
                try:
                    os.rmdir(p)            # only ever succeeds on an EMPTY one
                except OSError:
                    pass
            continue
        try:
            for f in os.listdir(p):
                fp = os.path.join(p, f)
                if os.path.isdir(fp) or not _really_inside(fp, auto):
                    raise OSError("it holds a folder or a link this agent did not make")
                try:
                    os.chmod(fp, _st.S_IWRITE)
                except OSError:
                    pass
                os.remove(fp)
            os.rmdir(p)
            removed += 1
        except OSError as e:
            errors.append("could not remove the old set %s: %s: %s"
                          % (d, e.__class__.__name__, e))
    return kept, removed, errors


def stick_leg(sb, hand_rows=()):
    """S499. Marg's newest automatic backup set, onto the stick.

    The .mbk on the stick exists only when a person accepts Marg's prompt --
    every two to four days, nobody's duty -- so the stick was stale and the
    alarm stood for days, while Marg's own daily backup sat on D:, the same
    disk as the data. This puts that backup where a dead disk cannot take it.

    Never raises for a stick that is absent, full or write-protected: the
    reason goes into the state and from there into the heartbeat.

    A drive at E: is written to ONLY when it is the backup stick: its own
    folder is already there, or a hand-made Marg backup (.mbk, or a _cNN_
    file) lies on it. Any other drive that happens to take the letter E: --
    a phone, a camera card, someone's pen drive -- is left untouched."""
    auto = _stick_auto_dir()
    out = {"dir": auto, "present": os.path.isdir(BACKUP_STICK), "set": None,
           "recognised": False, "free_mb": None,
           "set_files": 0, "copied": 0, "copied_bytes": 0, "already_there": 0,
           "waiting": "", "errors": [], "sets_kept": 0, "sets_removed": 0}
    if not out["present"]:
        return out
    out["recognised"] = os.path.isdir(auto) or any(
        r[0].lower().endswith(".mbk") or _is_marg_blob(os.path.basename(r[0]))
        for r in hand_rows)
    if not out["recognised"]:
        out["waiting"] = ("%s does not look like the backup stick (no Marg backup"
                          " on it, no %s folder) -- nothing is written to it"
                          % (BACKUP_STICK, STICK_AUTO_DIRNAME))
        return out
    members, why = _newest_auto_set(sb)
    if not members:
        out["waiting"] = why
    else:
        _gap = time.time() - sb[0][2]
        if -STICK_QUIET_SECS < _gap < STICK_QUIET_SECS:
            out["waiting"] = ("Marg wrote to its backup folder %d second(s) ago"
                              " -- it is copied once that folder has been quiet"
                              " for %d seconds"
                              % (max(0, int(_gap)), STICK_QUIET_SECS))
            members = []
    if members:
        setname = _when(members[0][2], "%Y-%m-%d_%H%M%S")
        if setname == "?":
            out["errors"].append("%s carries a time this PC cannot express -- "
                                 "not copied" % os.path.basename(members[0][0]))
            members = []
        setdir = os.path.join(auto, setname)
        out["set"] = setname
        out["set_files"] = len(members)

        def _there(src, size, mt):
            try:
                _d = os.stat(os.path.join(setdir, os.path.basename(src)))
                return (_d.st_size == size
                        and abs(_d.st_mtime - mt) <= STICK_MTIME_SLACK)
            except OSError:
                return False
        if not all(_there(*m) for m in members):
            import shutil as _sh
            need = STICK_FREE_FACTOR * sum(m[1] for m in members)
            try:
                free = _sh.disk_usage(BACKUP_STICK).free
                out["free_mb"] = round(free / 1048576.0, 1)
            except OSError:
                free = None
            if free is not None and free < need:
                out["errors"].append(
                    "the stick has only %.1f MB free; Marg's backup set needs"
                    " %.1f MB (ten times its size) -- nothing copied"
                    % (free / 1048576.0, need / 1048576.0))
                members = []
        for src, size, mt in members:
            name = os.path.basename(src)
            dst = os.path.join(setdir, name)
            try:
                _d = os.stat(dst)
                if (_d.st_size == size
                        and abs(_d.st_mtime - mt) <= STICK_MTIME_SLACK):
                    out["already_there"] += 1
                    continue
            except OSError:
                pass
            try:
                _s = os.stat(src)
            except OSError as e:
                out["errors"].append("%s: %s: %s" % (name, e.__class__.__name__, e))
                break
            if _s.st_size != size or _s.st_mtime != mt:
                out["waiting"] = ("%s changed while it was being read -- left"
                                  " for the next pass" % name)
                break
            try:
                if not os.path.isdir(setdir):
                    os.makedirs(setdir)        # only when there is a file for it
            except OSError as e:
                out["errors"].append("cannot make %s: %s: %s"
                                     % (setdir, e.__class__.__name__, e))
                break
            ok, err = _copy_verified(src, dst, size, mt)
            if not ok:
                # the database file is first: no companion goes without it
                out["errors"].append("%s: %s" % (name, err))
                break
            out["copied"] += 1
            out["copied_bytes"] += size
        try:
            if os.path.isdir(setdir) and not os.listdir(setdir):
                os.rmdir(setdir)
        except OSError:
            pass
    if os.path.isdir(auto):
        kept, removed, errs = _prune_stick_sets(auto)
        out["sets_kept"], out["sets_removed"] = kept, removed
        out["errors"].extend(errs)
    return out


def _offsite_names(rows, sb_rows):
    """The name each source file gets in the offsite folder.

    S499. The offsite folder is flat and the name was always the file's own --
    so three backups called d1-sanjeevni-20250401-20260331.mbk, in three
    folders of the stick and of three sizes, shared ONE offsite name: every
    pass copied all three over each other (7,429,171 bytes an hour, the
    heartbeat's "copied: 3"), and only the one copied last -- the oldest --
    was kept. A name is still the file's own unless two sources share it; then
    the one in Marg's own folder, else the one at the top of the stick, keeps
    the plain name and every other carries its folder in its name.
    Returns ({source path: offsite name}, [the names that were changed])."""
    import hashlib
    groups = {}
    for r in rows:
        groups.setdefault(os.path.basename(r[0]).lower(), []).append(r)
    names, renamed = {}, []
    for grp in groups.values():
        if len(grp) == 1:
            names[grp[0][0]] = os.path.basename(grp[0][0])
            continue
        plain = None
        for r in grp:
            if r in sb_rows:
                plain = r
                break
        if plain is None:
            for r in grp:
                if _same_dir(os.path.dirname(r[0]), BACKUP_STICK):
                    plain = r
                    break
        for r in grp:
            base = os.path.basename(r[0])
            if r is plain:
                names[r[0]] = base
                continue
            if r in sb_rows:
                rel = "serverbackup"
            else:
                try:
                    rel = os.path.relpath(os.path.dirname(r[0]), BACKUP_STICK)
                except ValueError:
                    rel = os.path.dirname(r[0])
            slug = re.sub(r"[^A-Za-z0-9]+", "_", rel).strip("_")[:40] or "top"
            h = hashlib.md5(rel.lower().encode("utf-8", "replace")).hexdigest()[:6]
            stem, ext = os.path.splitext(base)
            names[r[0]] = "%s__in_%s_%s%s" % (stem, slug, h, ext)
            renamed.append(names[r[0]])
    return names, renamed


def _zip_listing(path, mtime):
    """The FILE LIST of a zip -- its central directory -- and nothing else.

    Marg's backups are password-protected zips. Listing one needs no password;
    no member is opened, read or extracted here, ever. Returns (facts, names):
    the facts go into the heartbeat, the names stay in this process."""
    import hashlib
    import zipfile
    out = {"name": os.path.basename(path), "bytes": None,
           "written_at": _when(mtime, "%Y-%m-%dT%H:%M:%S"),
           "is_zip": False, "members": None, "uncompressed_bytes": None,
           "password_protected_members": None, "names_hash": None, "note": ""}
    names = None
    try:
        out["bytes"] = os.path.getsize(path)
        with zipfile.ZipFile(path, "r") as z:
            infos = z.infolist()
        names = sorted(i.filename for i in infos)
        out["is_zip"] = True
        out["members"] = len(infos)
        out["uncompressed_bytes"] = sum(i.file_size for i in infos)
        out["password_protected_members"] = sum(1 for i in infos
                                                if i.flag_bits & 0x1)
        out["names_hash"] = hashlib.sha1(
            "\n".join(names).encode("utf-8", "replace")).hexdigest()[:12]
    except Exception as e:                                     # noqa: BLE001
        out["note"] = ("its file list could not be read: %s: %s"
                       % (e.__class__.__name__, str(e)[:80]))
    return out, names


def _zip_compare(prev, hand_rows, blob_rows):
    """For the record, at most once a day: is Marg's automatic backup the same
    KIND of file as the hand-made .mbk?

    The newest hand-made .mbk on the stick against the automatic database file
    nearest to it in time. File lists only -- see _zip_listing. It is evidence
    about what the two files ARE; it is not a restore, and no restore of either
    has ever been tested."""
    now_ts = time.time()
    prev = prev if isinstance(prev, dict) else {}
    try:
        if (prev.get("checked_ts") is not None
                and 0 <= now_ts - float(prev["checked_ts"]) < ZIP_COMPARE_EVERY):
            return prev
    except (TypeError, ValueError):
        pass
    mbk = [r for r in hand_rows if r[0].lower().endswith(".mbk")]
    if not mbk or not blob_rows:
        return {"checked_at": None, "checked_ts": None,
                "note": "nothing to compare yet: %s"
                        % ("no hand-made .mbk on the stick" if not mbk
                           else "no automatic database file")}
    hand = max(mbk, key=lambda r: r[2])
    auto = min(blob_rows, key=lambda r: abs(r[2] - hand[2]))
    a, na = _zip_listing(hand[0], hand[2])
    b, nb = _zip_listing(auto[0], auto[2])
    out = {"checked_at": now().isoformat(timespec="seconds"),
           "checked_ts": int(now_ts), "handmade": a, "automatic": b,
           "hours_apart": round(abs(auto[2] - hand[2]) / 3600.0, 1),
           "same_member_names": None, "same_base_names": None,
           "names_in_both": None, "only_in_handmade": None,
           "only_in_automatic": None,
           "note": "file lists only -- no member was opened; this says what "
                   "the two files are, not that either restores"}
    if na is not None and nb is not None:
        sa, sb_ = set(na), set(nb)
        out["same_member_names"] = (na == nb)
        out["names_in_both"] = len(sa & sb_)
        out["only_in_handmade"] = len(sa - sb_)
        out["only_in_automatic"] = len(sb_ - sa)
        _base = lambda ns: sorted(n.replace("\\", "/").rsplit("/", 1)[-1].lower()
                                  for n in ns)                # noqa: E731
        out["same_base_names"] = (_base(na) == _base(nb))
    return out


def backup_pass():
    """Marg's own backup onto the stick, then what is missing offsite.

    Offsite: newest first, a few megabytes at a time; never deletes; never
    overwrites a file that is already there at the same size.
    Stick (S499): only inside the agent's own folder -- see stick_leg.
    Returns the state dict that the heartbeat prints. Every key S205 wrote is
    still written, with the same meaning; S499 only adds."""
    st = {"checked_at": now().isoformat(timespec="seconds"),
          "offsite": None, "copied": 0, "copied_bytes": 0,
          "already_there": 0, "pending": 0, "errors": [],
          "newest_stick": None, "newest_stick_age_days": None,
          "newest_serverbackup_age_days": None,
          "offsite_files": 0, "offsite_bytes": 0, "note": "",
          # ---- S499: added, nothing renamed ----
          "stick_present": False,
          "newest_handmade": None, "newest_handmade_age_days": None,
          "newest_auto_on_stick": None, "newest_auto_on_stick_age_days": None,
          "newest_serverbackup_blob": None,
          "newest_serverbackup_blob_age_days": None,
          "newest_serverbackup_offsite": None,
          "newest_serverbackup_offsite_age_days": None,
          "stick_copy": {}, "offsite_renamed": [], "zip_compare": {},
          "stick_absent_since": None, "stick_absent_since_ts": None,
          "stick_unrecognised_since": None, "stick_unrecognised_since_ts": None,
          "offsite_measured": False, "future_dated": []}
    prev = backup_state_read()
    if not isinstance(prev, dict):
        prev = {}

    def _days(ts):
        return round((time.time() - ts) / 86400.0, 1)

    rows = _backup_sources()
    sb_all = _serverbackup_files()
    # The two ages are NOT interchangeable and are never mixed: the stick is
    # the only copy that survives this disk dying. serverbackup is reported
    # beside it, never in place of it.
    _stick = [r for r in rows
              if os.path.abspath(r[0]).lower().startswith(
                  os.path.abspath(BACKUP_STICK).lower())]
    _sb = [r for r in rows if r not in _stick]
    _hand_all = list(_stick)
    # A file dated more than a day ahead (a PC clock that was wrong) would be
    # "the newest" for months: it is left out of every choice and every age,
    # and named in one calm line.
    _lim = time.time() + FUTURE_SLACK
    _fut = [r for r in sb_all + rows if r[2] > _lim]
    st["future_dated"] = sorted(set(
        "%s (dated %s)" % (os.path.basename(r[0]),
                           _when(r[2], "%d-%b-%Y"))
        for r in _fut))[:5]
    sb_all = [r for r in sb_all if r[2] <= _lim]
    _stick = [r for r in _stick if r[2] <= _lim]
    _sb = [r for r in _sb if r[2] <= _lim]
    _blobs = [r for r in sb_all if _is_marg_blob(os.path.basename(r[0]))]

    # ---- 1. the stick leg. It does not wait for Drive: the day Drive is away
    # ---- is the day the stick matters most.
    try:
        st["stick_copy"] = stick_leg(sb_all, _hand_all)
    except Exception as e:                                     # noqa: BLE001
        st["stick_copy"] = {"dir": _stick_auto_dir(),
                            "present": os.path.isdir(BACKUP_STICK),
                            "waiting": "", "copied": 0,
                            "errors": ["%s: %s" % (e.__class__.__name__, e)]}
    _sc = st["stick_copy"]
    st["stick_present"] = bool(_sc.get("present"))
    # Since when is there no backup stick at E:? Two cases, each its own
    # clock: nothing plugged in at all -- or a drive plugged in that holds no
    # Marg backup (a new, blank stick: a hand-made backup onto it starts the
    # copies). A stick that is in and recognised has neither.
    for _key, _now_true in (("stick_absent_since", not st["stick_present"]),
                            ("stick_unrecognised_since",
                             st["stick_present"] and not _sc.get("recognised"))):
        if not _now_true:
            continue
        try:
            _ts = float(prev.get(_key + "_ts"))
        except (TypeError, ValueError):
            _ts = time.time()
        st[_key + "_ts"] = round(_ts)
        st[_key] = _when(_ts, "%Y-%m-%dT%H:%M:%S")
    if _sc.get("copied"):
        log("stick copy: %d file(s), %.1f MB of Marg's own backup -> %s\\%s"
            % (_sc["copied"], _sc.get("copied_bytes", 0) / 1048576.0,
               _sc.get("dir"), _sc.get("set")))
    for _e in (_sc.get("errors") or [])[:2]:
        log("stick copy FAILED: %s" % _e)
    if _sc.get("sets_removed"):
        log("stick copy: %d old set(s) removed from %s (the newest %d are kept)"
            % (_sc["sets_removed"], _sc.get("dir"), STICK_AUTO_KEEP))

    # ---- 2. the ages. newest_stick keeps its meaning -- the newest backup
    # ---- file of ANY kind on the stick -- and now has two parts beside it:
    # ---- the hand-made one and the automatic copy.
    _auto = [r for r in _stick_auto_blobs() if r[2] <= _lim]
    if _stick:
        st["newest_handmade"] = os.path.basename(_stick[0][0])
        st["newest_handmade_age_days"] = _days(_stick[0][2])
    if _auto:
        st["newest_auto_on_stick"] = os.path.basename(_auto[0][0])
        st["newest_auto_on_stick_age_days"] = _days(_auto[0][2])
    _any = sorted(_stick[:1] + _auto[:1], key=lambda r: r[2], reverse=True)
    if _any:
        st["newest_stick"] = os.path.basename(_any[0][0])
        st["newest_stick_age_days"] = _days(_any[0][2])
    if _sb:
        st["newest_serverbackup_age_days"] = _days(_sb[0][2])
    if _blobs:
        st["newest_serverbackup_blob"] = os.path.basename(_blobs[0][0])
        st["newest_serverbackup_blob_age_days"] = _days(_blobs[0][2])

    # ---- 3. the offsite leg, as S203 made it
    dest = _offsite_dir()
    have = None
    if not dest:
        st["note"] = "clinic Drive not found -- nothing copied"
    else:
        st["offsite"] = dest
        have = {}
        try:
            for f in os.listdir(dest):
                p = os.path.join(dest, f)
                if os.path.isfile(p) and not f.endswith(".part"):
                    have[f] = os.path.getsize(p)
        except OSError as e:
            st["errors"].append("cannot read %s: %s" % (dest, e.__class__.__name__))
            have = None
    if have is not None:
        st["offsite_measured"] = True
        st["offsite_files"] = len(have)
        st["offsite_bytes"] = sum(have.values())
        names, renamed = _offsite_names(rows, _sb)
        st["offsite_renamed"] = renamed[:10]

        budget = BACKUP_BYTES_PER_PASS
        for src, size, _mt in rows:
            name = names.get(src) or os.path.basename(src)
            if have.get(name) == size:
                st["already_there"] += 1
                continue
            if budget <= 0:
                st["pending"] += 1
                continue
            ok, err = _copy_one(src, os.path.join(dest, name))
            if ok:
                st["copied"] += 1
                st["copied_bytes"] += size
                budget -= size
                have[name] = size
            else:
                st["errors"].append("%s: %s" % (name, err))
                budget -= size
        if st["copied"]:
            log("offsite backup: copied %d file(s), %.1f MB, %d still pending"
                % (st["copied"], st["copied_bytes"] / 1048576.0, st["pending"]))
        try:
            _f = [f for f in os.listdir(dest)
                  if os.path.isfile(os.path.join(dest, f)) and not f.endswith(".part")]
            st["offsite_files"] = len(_f)
            st["offsite_bytes"] = sum(os.path.getsize(os.path.join(dest, f)) for f in _f)
        except OSError:
            pass
        # the newest of Marg's own database files that is in the offsite
        # folder under its name and at its size (the offsite leg's own test)
        for r in _blobs:
            if have.get(names.get(r[0]) or os.path.basename(r[0])) == r[1]:
                st["newest_serverbackup_offsite"] = os.path.basename(r[0])
                st["newest_serverbackup_offsite_age_days"] = _days(r[2])
                break

    # ---- 4. for the record, once a day
    try:
        st["zip_compare"] = _zip_compare(prev.get("zip_compare"), _stick,
                                         _blobs + _auto)
    except Exception as e:                                     # noqa: BLE001
        st["zip_compare"] = {"checked_at": None, "checked_ts": None,
                             "note": "the comparison failed: %s: %s"
                                     % (e.__class__.__name__, str(e)[:80])}

    _tmp = BACKUP_STATE + ".tmp"              # whole or not at all
    try:
        _blob = json.dumps(st, indent=2)
        with open(_tmp, "w", encoding="utf-8") as fh:
            fh.write(_blob)
        os.replace(_tmp, BACKUP_STATE)
    except OSError:
        try:
            if os.path.exists(_tmp):
                os.remove(_tmp)
        except OSError:
            pass
    return st


def backup_state_read():
    try:
        with open(BACKUP_STATE, "r", encoding="utf-8") as fh:
            _s = json.load(fh)
        # S499: a spoiled file (a list, a string) must not stop the heartbeat
        return _s if isinstance(_s, dict) else {}
    except (OSError, ValueError):
        return {}


def build_beat(watcher_alive, watcher_pid, started_at, restarts, failures=None):
    _kf, _ki = kit_status()
    for _m, _f in (failures or {}).items():
        for _n, _row in (_ki or {}).items():
            if _row.get("kit_md5") == _m:
                _row["note"] = ("install FAILED %d time(s): %s"
                                % (_f["tries"], _f["last"][:60]))
    n_today, newest, newest_t = captures_today()
    ign = ignored_files()
    free = None
    try:
        free = round(__import__("shutil").disk_usage("D:\\").free / (1024 ** 3), 1)
    except Exception:                                          # noqa: BLE001
        pass
    return {
        "agent_version": AGENT_VERSION,
        "written_at": now().isoformat(timespec="seconds"),
        "computer": os.environ.get("COMPUTERNAME", "?"),
        "user": os.environ.get("USERNAME", "?"),
        "python": sys.version.split()[0],
        "agent_started": started_at,
        "watcher": {
            "alive": watcher_alive,
            "pid": watcher_pid,
            "watching": WATCH_DIRS,
            "restarts_since_agent_start": restarts,
        },
        "captures": {
            "today": n_today,
            "newest_file": newest,
            "newest_at": newest_t,
        },
        "ignored_by_watcher": {
            "count": len(ign),
            "files": ign[:20],
        },
        "agent_self": agent_drift(),
        "watcher_file": {"path": WATCHER, "md5": _md5(WATCHER)},
        "kit": {"folder": _kf, "files": _ki},
        "marg_slots": marg_slots(),
        "kit_backups": backup_count(),
        "kit_backup_state": kit_backup_state(),
        "disk_free_gb_D": free,
        "backup": backup_state_read(),
    }


def human(beat):
    L = []
    a = L.append
    a("MEDICAL PC HEARTBEAT   %s" % beat["written_at"])
    a("agent %s on %s (python %s)" % (beat["agent_version"], beat["computer"],
                                      beat["python"]))
    _as = beat.get("agent_self") or {}
    if _as.get("differs"):
        a("")
        a("*** THIS AGENT IS OUT OF DATE ***")
        a("    running  %s   (md5 %s)"
          % (_as.get("running_version"), (_as.get("running_md5") or "?")[:8]))
        a("    on Drive %s   (md5 %s)"
          % (_as.get("drive_version") or "unknown",
             (_as.get("drive_md5") or "?")[:8]))
        a("    FIX: double-click  %s  on this PC."
          % (_as.get("installer")
             or "INSTALL_AGENT_S499.bat in ToMedical of the clinic Drive"))
    elif _as.get("checked"):
        a("AGENT   : up to date (matches the copy on Drive)")
    else:
        a("AGENT   : self-check skipped -- %s"
          % (_as.get("note") or "reason not recorded"))
    w = beat["watcher"]
    a("")
    a("WATCHER : %s%s" % ("ALIVE, pid %s" % w["pid"] if w["alive"] else "DOWN",
                          "  (restarted %d time(s) since the agent started)"
                          % w["restarts_since_agent_start"]
                          if w["restarts_since_agent_start"] else ""))
    a("          watching: %s" % " + ".join(w["watching"]))
    c = beat["captures"]
    a("CAPTURES: %d today; newest %s at %s"
      % (c["today"], c["newest_file"] or "-", c["newest_at"] or "-"))
    ig = beat["ignored_by_watcher"]
    a("IGNORED : %d file(s) in the watched folders the watcher cannot take"
      % ig["count"])
    for f in ig["files"]:
        a("            %s  %s" % (f["when"], f["path"]))
    a("SLOTS   :")
    for s in beat["marg_slots"]:
        a("            %-24s %s  %d bytes" % (s["slot"], s["when"], s["bytes"]))
    wf = beat.get("watcher_file", {})
    a("WATCHER FILE: %s  md5 %s" % (wf.get("path"),
                                    (wf.get("md5") or "UNREADABLE")[:8]))
    k = beat.get("kit", {})
    if not k.get("folder"):
        a("KIT     : folder NOT FOUND (nothing can be delivered automatically)")
    else:
        a("KIT     : %s" % k["folder"])
        for n, v in (k.get("files") or {}).items():
            if not v.get("in_kit"):
                a("            %-18s not present in the kit" % n)
            elif v.get("matches"):
                a("            %-18s up to date (%s)" % (n, (v.get("kit_md5") or "")[:8]))
            else:
                a("            %-18s DIFFERS: kit %s vs installed %s  %s"
                  % (n, (v.get("kit_md5") or "unreadable")[:8],
                     (v.get("installed_md5") or "unreadable")[:8],
                     v.get("note", "")))
    _ks = beat.get("kit_backup_state") or {}
    if _ks.get("prune_failed"):
        a("BACKUPS : the prune could NOT remove %d old kit copy file(s) "
          "(.before_) under %s" % (_ks["prune_failed"], KIT_DEST_ROOT))
        a("          it keeps %d per kit file; %d are there now%s"
          % (_ks.get("keep", KIT_BACKUP_KEEP), _ks.get("count", 0),
             ("; first: %s" % _ks["prune_failed_names"][0])
             if _ks.get("prune_failed_names") else ""))
    elif _ks.get("over"):
        a("BACKUPS : more than %d old copies (.before_) still sit beside a kit "
          "file under %s" % (_ks.get("keep", KIT_BACKUP_KEEP), KIT_DEST_ROOT))
        a("          after the prune ran -- %s" % "; ".join(_ks["over"]))
    _bk = beat.get("backup") or {}
    if not _bk:
        a("BACKUP  : not checked yet (the agent has just started)")
    else:
        _age = _bk.get("newest_stick_age_days")
        _s499 = "stick_copy" in _bk          # a state this version wrote
        _sc = _bk.get("stick_copy")
        _sc = _sc if isinstance(_sc, dict) else {}
        _aa = _bk.get("newest_auto_on_stick_age_days")
        _ha = _bk.get("newest_handmade_age_days")
        _bba = _bk.get("newest_serverbackup_blob_age_days")
        _oa = _bk.get("newest_serverbackup_offsite_age_days")
        _since = None
        try:
            _since = float(_bk.get("stick_absent_since_ts"))
        except (TypeError, ValueError):
            pass
        _since_txt = _when(_since) if _since is not None else ""
        _blank = None
        try:
            _blank = float(_bk.get("stick_unrecognised_since_ts"))
        except (TypeError, ValueError):
            pass
        if _age is None:
            a("BACKUP  : NO BACKUP FILE ON %s -- the stick is empty or absent"
              % BACKUP_STICK)
        else:
            a("BACKUP  : newest backup on the stick is %.1f day(s) old  (%s)"
              % (_age, _bk.get("newest_stick") or "?"))
        if _s499 and not _bk.get("stick_present"):
            a("          STICK ABSENT: %s is not there%s -- Marg's automatic"
              % (BACKUP_STICK, (" since " + _since_txt) if _since_txt else ""))
            a("          backup cannot be copied to a stick until it is plugged in.")
        elif _s499 and not _sc.get("recognised", True):
            a("          STICK HOLDS NO MARG BACKUP: %s is plugged in%s but holds no"
              % (BACKUP_STICK, (" since " + _when(_blank)) if _blank is not None else ""))
            a("          Marg backup -- nothing is written to it. Take one in Marg by hand")
            a("          onto this stick; then the copies start by themselves.")
        elif _s499:
            if _aa is not None:
                a("          automatic copy on the stick: %.1f day(s) old  (%s)"
                  % (_aa, _bk.get("newest_auto_on_stick") or "?"))
            else:
                a("          automatic copy on the stick: none yet")
            if _sc.get("errors"):
                a("          STICK COPY FAILED: %s" % _sc["errors"][0])
                a("          Marg's newest automatic backup is NOT on the stick --")
                a("          is the stick full, write-protected or faulty?")
            elif _sc.get("waiting"):
                a("          stick copy waiting: %s" % _sc["waiting"])
            if _ha is None:
                a("          hand-made backup on the stick: none")
            elif (_ha > HANDMADE_CALM_DAYS and _aa is not None
                  and _aa <= BACKUP_WARN_DAYS):
                a("          hand-made backup on the stick: %.1f day(s) old  (%s)"
                  % (_ha, _bk.get("newest_handmade") or "?"))
                a("          -- optional; the automatic copy is on the stick")
            else:
                a("          hand-made backup on the stick: %.1f day(s) old  (%s)"
                  % (_ha, _bk.get("newest_handmade") or "?"))
        for _fd in (_bk.get("future_dated") or [])[:3]:
            a("          ignored, dated in the future: %s" % _fd)
        _sba = _bk.get("newest_serverbackup_age_days")
        if _sba is not None:
            a("          Marg's own serverbackup: %.1f day(s) old -- on D:, the same"
              % _sba)
            a("          disk as the data. Not a disaster copy by itself.")
        if _s499:
            if _bba is not None:
                a("          its newest database file: %.1f day(s) old  (%s)"
                  % (_bba, _bk.get("newest_serverbackup_blob") or "?"))
            else:
                a("          it holds no database file yet")
            if _oa is not None:
                a("          newest automatic backup in the offsite folder: "
                  "%.1f day(s) old" % _oa)
            elif _bk.get("offsite"):
                a("          no automatic backup is in the offsite folder yet")
        if _bk.get("offsite"):
            a("          offsite: %d file(s), %.2f GB in %s"
              % (_bk.get("offsite_files", 0),
                 _bk.get("offsite_bytes", 0) / (1024.0 ** 3),
                 _bk["offsite"]))
            if _bk.get("pending"):
                a("          %d file(s) still to copy -- it works through them"
                  % _bk["pending"])
            else:
                a("          offsite copy is COMPLETE")
        else:
            a("          offsite: %s" % (_bk.get("note") or "not available"))
        for _e in (_bk.get("errors") or [])[:3]:
            a("          ERROR: %s" % _e)
        _zc = _bk.get("zip_compare")
        _zc = _zc if isinstance(_zc, dict) else {}
        _zh, _za = _zc.get("handmade"), _zc.get("automatic")
        if isinstance(_zh, dict) and isinstance(_za, dict) and _zh and _za:
            if _zh.get("is_zip") and _za.get("is_zip"):
                a("          for the record (file lists only, nothing opened): the"
                  " hand-made")
                a("          .mbk lists %s member(s), Marg's automatic file %s;"
                  " same names: %s"
                  % (_zh.get("members"), _za.get("members"),
                     "yes" if _zc.get("same_member_names") else "no"))
            else:
                a("          for the record: a file list could not be read "
                  "(hand-made: %s, automatic: %s)"
                  % ("zip" if _zh.get("is_zip") else "not readable as a zip",
                     "zip" if _za.get("is_zip") else "not readable as a zip"))
        # The loud lines, and only these: the newest backup of ANY kind on the
        # stick is over 3 days old -- or the stick has been out for over a day.
        # A gap in Marg's own backup alone is ordinary on this PC: it is the
        # calm "its newest database file" line above, never a loud one.
        _stale = _age is not None and _age > BACKUP_WARN_DAYS
        if _stale:
            a("")
            a("*** NO MARG BACKUP ON THE STICK FOR %.1f DAYS ***" % _age)
            if (_s499 and _bba is not None and _bba < _age
                    and _bba <= BACKUP_WARN_DAYS):
                a("    Marg's own automatic backup is fresh on D: (%.1f day(s) old)"
                  % _bba)
                a("    but it is not reaching the stick. Check the stick in %s --"
                  % BACKUP_STICK)
                a("    plugged in, not full, not write-protected -- or take a")
                a("    backup in Marg by hand.")
            else:
                a("    Take one in Marg today (it goes to the stick).")
            # said only when this pass MEASURED it: the stick in and stale, the
            # offsite folder read, and nothing newer than the stick's in it
            if (_s499 and _bk.get("stick_present") and _bk.get("offsite")
                    and _bk.get("offsite_measured")
                    and (_oa is None or _oa >= _age)
                    and (_ha is None or _ha > BACKUP_WARN_DAYS)
                    and (_aa is None or _aa > BACKUP_WARN_DAYS)):
                a("    Nothing newer is in the offsite folder either: everything the")
                a("    pharmacy has done since then exists in exactly one place --")
                a("    this PC's D: disk.")
        if (_s499 and _since is not None
                and time.time() - _since > STICK_ABSENT_LOUD_DAYS * 86400.0):
            a("")
            a("*** NO MARG BACKUP ON THE STICK -- the backup stick is not plugged"
              " in since %s ***" % _since_txt)
            a("    Plug the Marg backup stick back into this PC (it shows as %s)."
              % BACKUP_STICK)
        if (_s499 and _blank is not None and _bk.get("stick_present")
                and time.time() - _blank > STICK_ABSENT_LOUD_DAYS * 86400.0):
            a("")
            a("*** NO MARG BACKUP ON THE STICK -- %s is plugged in but holds no Marg"
              " backup since %s ***" % (BACKUP_STICK, _when(_blank)))
            a("    Take one in Marg by hand onto this stick (then copies start by"
              " themselves).")
    a("DISK    : %s GB free on D:" % beat["disk_free_gb_D"])
    return "\n".join(L) + "\n"


def write_beat(beat):
    text = human(beat)
    blob = json.dumps(beat, indent=2)
    wrote = []
    for path, data in ((LOCAL_BEAT, text),):
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(data)
            wrote.append(path)
        except OSError as ex:
            log("could not write %s: %s" % (path, ex))
    out = find_drive_out()
    if out:
        for name, data in (("heartbeat.json", blob), ("heartbeat.txt", text)):
            try:
                with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
                    fh.write(data)
                wrote.append(os.path.join(out, name))
            except OSError as ex:
                log("could not write %s: %s" % (name, ex))
    else:
        log("clinic Drive FromMedical folder not found -- heartbeat is LOCAL ONLY")
    return wrote


# --------------------------------------------------------------------------
def main():
    started_at = now().isoformat(timespec="seconds")
    log("=" * 60)
    log("medical_agent %s starting (python %s)" % (AGENT_VERSION,
                                                   sys.version.split()[0]))
    if not os.path.exists(PY):
        log("FATAL: bundled python missing at %s" % PY)
        return 2
    if not os.path.exists(WATCHER):
        log("FATAL: watcher script missing at %s" % WATCHER)
        return 2

    kill_stale_watcher()
    proc = start_watcher()
    restarts = 0
    last_beat = 0.0
    last_backup = 0.0
    backup_every = BACKUP_EVERY
    kit_failures = {}
    prune_kit_backups()

    try:
        while True:
            todo = pending_kit(kit_failures)
            if todo:
                names = [t[0] for t in todo]
                needs_restart = any(n in RESTART_FOR for n in names)
                if needs_restart:
                    log("kit updates %s -- stopping the watcher to install" % names)
                    kill_pid(proc.pid)
                    time.sleep(2)
                else:
                    log("kit updates %s -- no watcher restart needed" % names)
                install_kit(todo, kit_failures)
                prune_kit_backups()
                if needs_restart:
                    proc = start_watcher()
                last_beat = 0.0

            if proc.poll() is not None:
                restarts += 1
                log("WATCHER DIED (exit %s) -- restart #%d" % (proc.returncode,
                                                               restarts))
                proc = start_watcher()
                last_beat = 0.0            # report the restart immediately

            # S203: the offsite backup leg. Guarded and bounded -- it may
            # never delay watcher supervision, and a failure here must never
            # stop the agent doing its first job.
            if time.time() - last_backup >= backup_every:
                last_backup = time.time()
                backup_every = BACKUP_EVERY
                try:
                    # S499: at the start Drive may not be up yet, and the
                    # manifest's files are known only when it is.
                    prune_kit_backups()
                except Exception as _pe:                       # noqa: BLE001
                    log("kit backup prune FAILED: %s: %s"
                        % (_pe.__class__.__name__, _pe))
                try:
                    _bs = backup_pass()
                    if (_bs or {}).get("pending"):
                        # a backlog is being worked through -- come back soon
                        backup_every = BACKUP_CATCHUP_EVERY
                except Exception as _be:                       # noqa: BLE001
                    log("offsite backup pass FAILED: %s: %s"
                        % (_be.__class__.__name__, _be))

            if time.time() - last_beat >= BEAT_EVERY:
                beat = build_beat(proc.poll() is None, proc.pid, started_at,
                                  restarts, kit_failures)
                write_beat(beat)
                last_beat = time.time()

            time.sleep(CHECK_EVERY)
    except KeyboardInterrupt:
        log("agent stopped by hand")
    finally:
        try:
            if proc and proc.poll() is None:
                log("leaving the watcher running (pid %d)" % proc.pid)
        except Exception:                                      # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    # Nothing above may be trusted to have a console. If the agent dies for any
    # reason, the reason is written where a human can find it -- locally, and
    # in the clinic Drive if it is reachable.
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:                                      # noqa: BLE001
        import traceback
        tb = traceback.format_exc()
        stamp = dt.datetime.now().isoformat(timespec="seconds")
        blob = "medical_agent %s CRASHED at %s\n\n%s" % (AGENT_VERSION, stamp, tb)
        for path in (r"D:\SendToClinic\agent_crash.txt", AGENT_LOG):
            try:
                with open(path, "a", encoding="utf-8") as fh:
                    fh.write(blob + "\n")
            except OSError:
                pass
        try:
            out = find_drive_out()
            if out:
                with open(os.path.join(out, "agent_crash.txt"), "w",
                          encoding="utf-8") as fh:
                    fh.write(blob)
        except Exception:                                      # noqa: BLE001
            pass
        raise
