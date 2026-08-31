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
"""

import datetime as dt
import json
import os
import re
import string
import subprocess
import sys
import time

AGENT_VERSION = "S205.1"

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


def prune_kit_backups(keep=3):
    """Keep the newest few .before_ backups beside each kit file; bin the rest.

    S201.6: clear the read-only flag before removing, and report FAILURES as
    well as successes. S201.5 removed nothing and said nothing, because every
    os.remove hit the same read-only attribute that had blocked the install,
    and the log line only fired when something was actually deleted. A tidy-up
    that cannot tidy, silently, is the fault it was written to clean up after.
    """
    import stat as _st
    removed = failed = 0
    for dest in KIT_FILES.values():
        d = os.path.dirname(dest) or "."
        base = os.path.basename(dest) + ".before_"
        try:
            baks = sorted((f for f in os.listdir(d) if f.startswith(base)),
                          key=lambda f: os.path.getmtime(os.path.join(d, f)),
                          reverse=True)
        except OSError:
            continue
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
    if removed or failed:
        log("pruned %d stale kit backup(s)%s"
            % (removed, ("; %d could NOT be removed" % failed) if failed else ""))
    return removed, failed


def backup_count():
    """How many .before_ files are lying beside the kit files right now."""
    n = 0
    for dest in KIT_FILES.values():
        d = os.path.dirname(dest) or "."
        base = os.path.basename(dest) + ".before_"
        try:
            n += sum(1 for f in os.listdir(d) if f.startswith(base))
        except OSError:
            pass
    return n


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


def backup_pass():
    """Copy what is missing offsite. Newest first, a few megabytes at a time.

    Never deletes. Never overwrites a file that is already there at the same
    size. Returns the state dict that the heartbeat prints."""
    st = {"checked_at": now().isoformat(timespec="seconds"),
          "offsite": None, "copied": 0, "copied_bytes": 0,
          "already_there": 0, "pending": 0, "errors": [],
          "newest_stick": None, "newest_stick_age_days": None,
          "newest_serverbackup_age_days": None,
          "offsite_files": 0, "offsite_bytes": 0, "note": ""}

    dest = _offsite_dir()
    if not dest:
        st["note"] = "clinic Drive not found -- nothing copied"
        return st
    st["offsite"] = dest

    have = {}
    try:
        for f in os.listdir(dest):
            p = os.path.join(dest, f)
            if os.path.isfile(p) and not f.endswith(".part"):
                have[f] = os.path.getsize(p)
    except OSError as e:
        st["errors"].append("cannot read %s: %s" % (dest, e.__class__.__name__))
        return st
    st["offsite_files"] = len(have)
    st["offsite_bytes"] = sum(have.values())

    rows = _backup_sources()
    # The two ages are NOT interchangeable and are never mixed: the stick is
    # the only copy that survives this disk dying. serverbackup is reported
    # beside it, never in place of it.
    _stick = [r for r in rows
              if os.path.abspath(r[0]).lower().startswith(
                  os.path.abspath(BACKUP_STICK).lower())]
    if _stick:
        st["newest_stick"] = os.path.basename(_stick[0][0])
        st["newest_stick_age_days"] = round(
            (time.time() - _stick[0][2]) / 86400.0, 1)
    _sb = [r for r in rows if r not in _stick]
    if _sb:
        st["newest_serverbackup_age_days"] = round(
            (time.time() - _sb[0][2]) / 86400.0, 1)

    budget = BACKUP_BYTES_PER_PASS
    for src, size, _mt in rows:
        name = os.path.basename(src)
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
    try:
        with open(BACKUP_STATE, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(st, indent=2))
    except OSError:
        pass
    return st


def backup_state_read():
    try:
        with open(BACKUP_STATE, "r", encoding="utf-8") as fh:
            return json.load(fh) or {}
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
        a("    FIX: double-click  F:\\My Drive\\Clinic Data Archive\\"
          "ToMedical\\INSTALL_AGENT.bat  on this PC.")
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
    _kb = beat.get("kit_backups", 0)
    if _kb > 5:
        a("BACKUPS : %d kit backup files are lying about - the prune is "
          "not working" % _kb)
    _bk = beat.get("backup") or {}
    if not _bk:
        a("BACKUP  : not checked yet (the agent has just started)")
    else:
        _age = _bk.get("newest_stick_age_days")
        if _age is None:
            a("BACKUP  : NO BACKUP FILE ON %s -- the stick is empty or absent"
              % BACKUP_STICK)
        else:
            a("BACKUP  : newest backup on the stick is %.1f day(s) old  (%s)"
              % (_age, _bk.get("newest_stick") or "?"))
        _sba = _bk.get("newest_serverbackup_age_days")
        if _sba is not None:
            a("          Marg's own serverbackup: %.1f day(s) old -- but on D:,"
              % _sba)
            a("          the same disk as the data. Not a disaster copy.")
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
        if _age is not None and _age > BACKUP_WARN_DAYS:
            a("")
            a("*** NO MARG BACKUP FOR %.1f DAYS ***" % _age)
            a("    Take one in Marg. Everything the pharmacy has done since")
            a("    then exists in exactly one place.")
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
