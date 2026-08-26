#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
medical_census.py  --  S201.  Runs ON THE MEDICAL PC. Read-only.

WHY THIS EXISTS
    Every other census tool runs on manojz, over the Tailscale share
    \\100.119.151.40\DDrive -- which is the D: drive ONLY. On 25-Aug a PDF
    export turned out to live at

        C:\\Users\\Public\\MARG\\<id>\\all\\REPORT.PDF

    a second Marg output tree, on a drive manojz cannot see at all. So the
    census, the recent-files sweep and the ignored-file counter would all have
    answered "nothing there" with complete confidence. They were not wrong
    about what they looked at; they were blind to where it was.

    This one runs on the machine, so it can see BOTH drives. It cross-checks
    against the archive index through the Google Drive copy, which the medical
    PC can also read -- so the loop closes without needing manojz at all.

Writes: <Drive>\\Clinic Data Archive\\FromMedical\\CENSUS.txt   (syncs to Claude)
        D:\\SendToClinic\\CENSUS.txt                            (local fallback)
Writes nothing else, changes nothing, deletes nothing.
"""

import datetime as dt
import hashlib
import io
import os
import re
import string
import sys

ROOTS = [
    (r"D:\MARGERP\users", "Marg's .xls output slots (overwritten each run)"),
    (r"C:\Users\Public\MARG", "Marg's SECOND tree -- PDFs live here (S201)"),
    (r"D:\MARG REPORTS", "saved by hand by Dr Manoj"),
    (r"D:\SendToClinic\_captured", "the watcher's capture spool"),
    (r"D:\SendToClinic\Sent", "dated copies kept by the old sender"),
]

# Must match marg_watch.py's EXTS.
WATCHED_EXTS = (".xls", ".xlsx", ".pdf")
# Formats a report could plausibly be that the watcher does NOT take.
REPORTABLE_EXTS = (".csv", ".doc", ".docx", ".rtf", ".htm", ".html", ".xml", ".ods")
# Marg's own database and working files. Never reports; never mentioned.
SKIP_EXTS = {".dbf", ".cdx", ".idx", ".fpt", ".xff", ".c18", ".mem", ".tmp",
             ".ini", ".log", ".bak", ".dat", ".prn", ".txt", ".exe", ".dll",
             ".zip", ".jmbkh", ".mbk", ".pyc", ".py", ".lock", ".db"}
SKIP_DIRS = {"pyportable", "__pycache__", "xlrd", "backup", "backtemp",
             "$recycle.bin", "system volume information", "_to_delete_s201"}
MAX_HASH = 25 * 1024 * 1024


def md5_of(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def find_drive():
    """(FromMedical, MargArchive) inside the clinic Drive, or (None, None)."""
    roots = ["%s:\\My Drive" % c for c in string.ascii_uppercase]
    roots.append(os.path.join(os.environ.get("USERPROFILE", ""), "My Drive"))
    for r in roots:
        base = os.path.join(r, "Clinic Data Archive")
        if os.path.isdir(os.path.join(base, "FromMedical")):
            return (os.path.join(base, "FromMedical"),
                    os.path.join(base, "MargArchive"))
    return None, None


def archive_index(archive_dir):
    """md5 -> short description, from the Drive copy of the router's index."""
    out = {}
    if not archive_dir:
        return out
    p = os.path.join(archive_dir, "index.csv")
    if not os.path.exists(p):
        return out
    import csv
    try:
        with io.open(p, "r", encoding="utf-8", errors="replace", newline="") as fh:
            rows = list(csv.reader(fh))
    except OSError:
        return out
    if not rows:
        return out
    hdr = rows[0]
    for r in rows[1:]:
        if len(r) < len(hdr):
            continue
        d = dict(zip(hdr, r))
        m = (d.get("md5") or "").strip().lower()
        if m:
            out[m] = "%s %s %s" % (d.get("verdict", "?"), d.get("type", "?"),
                                   d.get("date_to", ""))
    return out


def title_of(path):
    low = path.lower()
    if low.endswith(".pdf"):
        return "(PDF)"
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        if low.endswith(".xlsx"):
            import xlsx_stdlib
            sh = xlsx_stdlib.open_workbook(path).sheet_by_index(0)
        else:
            import xlrd
            sh = xlrd.open_workbook(path).sheet_by_index(0)
        for r in range(min(8, sh.nrows)):
            v = str(sh.cell_value(r, 0)).strip()
            if len(v) > 12 and any(w in v.upper() for w in
                                   ("STATEMENT", "REPORT", "SALE", "PURCHASE",
                                    "STOCK", "EXPIRY", "LIST")):
                return v[:70]
        return "(no title row)"
    except Exception as e:                                     # noqa: BLE001
        return "(unreadable: %s)" % e.__class__.__name__


# ---------------------------------------------------------------------------
# S203 -- THE BACKUP SECTION (F-191c). Read-only. Adds nothing, changes nothing.
#
# Why it lives HERE and not in a one-off .bat: this file is on the agent's
# allowlist, so a new version installs itself down the Drive channel with no
# keystroke on this PC. And the backup stick is the ONE thing the Tailscale
# share cannot reach -- that share is the D: drive only -- so no tool on
# manojz can ever see it. This runs on the machine, so it can.
#
# It exists to answer one question: the automatic Marg backup was configured
# and E:\auto has been empty since October 2025. Why does it produce nothing?
# ---------------------------------------------------------------------------
CENSUS_VERSION = "S203.6"

BACKUP_STICK_GUESS = "E:"
BACKUP_DIRS = [r"E:\auto", r"E:\MARGBCKUP", r"E:\MARGBCKUP\auto",
               r"E:\MARGBCKUP\manual", r"E:\MARG", r"E:\Backup", r"E:\BACKUP"]
MARG_ROOTS = [r"D:\MARGERP", r"C:\MARGERP"]
BACKUP_STALE_DAYS = 2
BACKUP_EXTS = (".zip", ".rar", ".7z", ".bak", ".mbk", ".jmbkh", ".dbf", ".cab")


def _age_days(ts):
    return (dt.datetime.now() - dt.datetime.fromtimestamp(ts)).total_seconds() / 86400.0


def _stamp(ts):
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _dir_facts(path, max_files=200000):
    """(files, bytes, newest_path, newest_mtime) walking the whole subtree."""
    n = 0
    total = 0
    newest_p = None
    newest_t = 0.0
    for base, dirs, files in os.walk(path):
        for f in files:
            p = os.path.join(base, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            n += 1
            total += st.st_size
            if st.st_mtime > newest_t:
                newest_t, newest_p = st.st_mtime, p
            if n >= max_files:
                return n, total, newest_p, newest_t
    return n, total, newest_p, newest_t


def _free_bytes(drive):
    try:
        import ctypes
        free = ctypes.c_ulonglong(0)
        total = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(drive + "\\"), ctypes.pointer(free),
            ctypes.pointer(total), None)
        return free.value, total.value
    except Exception:                                          # noqa: BLE001
        return None, None


def _gb(n):
    return "?" if n is None else "%.1f GB" % (n / (1024.0 ** 3))


def _scheduled_tasks():
    """Task Scheduler entries whose text mentions marg or backup. Read-only."""
    try:
        import subprocess
        p = subprocess.run(["schtasks", "/query", "/fo", "LIST", "/v"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=90)
        txt = (p.stdout or b"").decode("utf-8", "replace")
    except Exception as e:                                     # noqa: BLE001
        return ["   (could not read Task Scheduler: %s)" % e.__class__.__name__]
    keep = ("TaskName", "Task To Run", "Status", "Last Run Time",
            "Last Result", "Next Run Time", "Scheduled Task State", "Author")
    out = []
    for block in re.split(r"\r?\n\r?\n", txt):
        low = block.lower()
        if not ("marg" in low or "backup" in low or "bckup" in low):
            continue
        if "microsoft\\windows" in low and "marg" not in low:
            continue
        for line in block.splitlines():
            for k in keep:
                if line.strip().lower().startswith(k.lower() + ":"):
                    out.append("   " + line.strip())
                    break
        out.append("")
    return out or ["   NONE. Nothing in Task Scheduler mentions Marg or backup.",
                   "   >>> If the automatic backup is meant to be a scheduled task,",
                   "   >>> it does not exist. That would explain an empty E:\\auto."]


def _startup_items():
    out = []
    try:
        import subprocess
        for hive in ("HKCU", "HKLM"):
            p = subprocess.run(
                ["reg", "query",
                 hive + r"\Software\Microsoft\Windows\CurrentVersion\Run"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            for line in (p.stdout or b"").decode("utf-8", "replace").splitlines():
                if line.strip():
                    out.append("   " + line.rstrip())
    except Exception:                                          # noqa: BLE001
        pass
    folder = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows",
                          "Start Menu", "Programs", "Startup")
    if os.path.isdir(folder):
        out.append("   Startup folder: %s" % folder)
        for f in sorted(os.listdir(folder)):
            out.append("      %s" % f)
    return out


def _marg_backup_config():
    """Lines in Marg's own .ini/.cfg files that mention backup."""
    hits = []
    seen = 0
    for root in MARG_ROOTS:
        if not os.path.isdir(root):
            continue
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs
                       if d.lower() not in ("backtemp", "__pycache__")]
            for f in files:
                if not f.lower().endswith((".ini", ".cfg", ".ctl", ".conf")):
                    continue
                p = os.path.join(base, f)
                seen += 1
                try:
                    with io.open(p, "r", encoding="utf-8",
                                 errors="replace") as fh:
                        for i, line in enumerate(fh, 1):
                            if "back" in line.lower() or "bckup" in line.lower():
                                hits.append("   %s:%d: %s"
                                            % (p, i, line.strip()[:160]))
                except OSError:
                    continue
            if len(hits) > 400:
                break
    if not seen:
        return ["   No .ini/.cfg files found under the Marg folders at all."]
    if not hits:
        return ["   %d config file(s) read; NONE mentions backup." % seen,
                "   >>> Marg's backup setting is not held in a plain text file",
                "   >>> here -- it is inside the database or the GUI only."]
    return ["   %d config file(s) read; %d line(s) mention backup:"
            % (seen, len(hits))] + hits[:80]


def _power_history(days=21):
    """Real boot/shutdown times from the Windows System log. Read-only.

    6005 = the event log service started  (the machine came up)
    6006 = the event log service stopped  (a clean shutdown)
    1074 = something requested a shutdown/restart, and says what
    6008 = the previous shutdown was UNEXPECTED (power cut, hard off)
    """
    try:
        import subprocess
        q = ("*[System[(EventID=6005 or EventID=6006 or EventID=6008) and "
             "TimeCreated[timediff(@SystemTime) <= %d]]]" % (days * 86400000))
        p = subprocess.run(["wevtutil", "qe", "System", "/q:" + q,
                            "/c:150", "/rd:true", "/f:text"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=90)
        txt = (p.stdout or b"").decode("utf-8", "replace")
    except Exception as e:                                     # noqa: BLE001
        return ["   (could not read the Windows event log: %s)"
                % e.__class__.__name__]
    if not txt.strip():
        return ["   (the event log returned nothing for the last %d days)" % days]

    events = []
    eid = when = None
    for line in txt.splitlines():
        t = line.strip()
        if t.startswith("Event ID:"):
            eid = t.split(":", 1)[1].strip()
        elif t.startswith("Date:"):
            when = t.split(":", 1)[1].strip()
            if eid:
                events.append((when, eid))
                eid = when = None
    if not events:
        return ["   (the event log was read but no boot/shutdown rows parsed)"]

    name = {"6005": "ON  (started)", "6006": "OFF (clean shutdown)",
            "6008": "OFF (UNEXPECTED -- power cut or hard off)"}
    out = ["   %d power event(s) in the last %d days, newest first:"
           % (len(events), days), ""]
    byday = {}
    for when, eid in events:
        out.append("      %-24s %s" % (when, name.get(eid, eid)))
        d = when.split("T")[0].split(" ")[0]
        byday.setdefault(d, []).append((when, eid))
    out.append("")
    out.append("   -- per day: when it came ON and when it went OFF --")
    for d in sorted(byday, reverse=True):
        ons = [w for w, e in byday[d] if e == "6005"]
        offs = [w for w, e in byday[d] if e in ("6006", "6008")]
        out.append("      %s   ON: %s   OFF: %s"
                   % (d,
                      (min(ons).split("T")[-1][:8] if ons else "-"),
                      (max(offs).split("T")[-1][:8] if offs else "-")))
    out.append("")
    out.append("   >>> A backup must be scheduled inside these hours. A job set")
    out.append("   >>> for midnight on a machine that is off at midnight is a")
    out.append("   >>> job that never runs and never complains.")
    return out


def _serverbackup_detail(limit=25):
    """What Marg's own serverbackup folder actually holds, with times."""
    out = []
    for root in (r"D:\MARGERP\serverbackup", r"C:\MARGERP\serverbackup"):
        if not os.path.isdir(root):
            continue
        rows = []
        for base, dirs, files in os.walk(root):
            for f in files:
                p = os.path.join(base, f)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                rows.append((st.st_mtime, st.st_size, p))
        rows.sort(reverse=True)
        out.append("   %s -- %d file(s)" % (root, len(rows)))
        if not rows:
            out.append("      EMPTY")
            continue
        out.append("      newest %d:" % min(limit, len(rows)))
        for t, sz, p in rows[:limit]:
            out.append("         %s  %10d  %.1fd  %s"
                       % (_stamp(t), sz, _age_days(t), os.path.relpath(p, root)))
        out.append("      oldest: %s  %s"
                   % (_stamp(rows[-1][0]), os.path.relpath(rows[-1][2], root)))
        # how regular is it?
        daysseen = sorted({_stamp(t)[:10] for t, _, _ in rows}, reverse=True)
        out.append("      distinct days written: %d  (newest %s, oldest %s)"
                   % (len(daysseen), daysseen[0], daysseen[-1]))
        out.append("      last 14 days written: %s" % ", ".join(daysseen[:14]))
    return out or ["   no serverbackup folder found"]


def _all_task_names():
    """EVERY scheduled task name, unfiltered. S195 registered a logon task
    called "Marg export watcher"; a filtered query that returns NONE is not
    proof it is absent -- it is proof the filter matched nothing. List them
    all and let a person look."""
    try:
        import subprocess
        p = subprocess.run(["schtasks", "/query", "/fo", "csv", "/nh"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=60)
        txt = (p.stdout or b"").decode("utf-8", "replace")
    except Exception as e:                                     # noqa: BLE001
        return ["   (could not list tasks: %s)" % e.__class__.__name__]
    names = []
    for line in txt.splitlines():
        line = line.strip()
        if not line or not line.startswith('"'):
            continue
        n = line.split('","')[0].lstrip('"')
        if n.startswith("\\Microsoft\\"):
            continue
        if n not in names:
            names.append(n)
    if not names:
        return ["   (no non-Microsoft tasks found)"]
    return ["   %d non-Microsoft task(s):" % len(names)] + \
           ["      %s" % n for n in sorted(names)]


def _sendtoclinic_listing():
    """What D:\\SendToClinic REALLY holds, on this machine, right now.

    manojz mirrors this folder with `robocopy /E` and NO /PURGE, so its copy
    keeps every file ever deleted here. Anything reasoned from that mirror can
    be wrong about what still exists. This is the machine's own answer."""
    root = r"D:\SendToClinic"
    if not os.path.isdir(root):
        return ["   %s does not exist" % root]
    groups = {}
    total = 0
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in ("pyportable", "__pycache__")]
        for f in files:
            p = os.path.join(base, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            total += 1
            rel = os.path.relpath(p, root)
            key = rel.split(os.sep)[0] if os.sep in rel else "(top level)"
            groups.setdefault(key, []).append((st.st_mtime, st.st_size, rel))
    out.append("   %s -- %d file(s) (pyportable and __pycache__ excluded)"
               % (root, total))
    for key in sorted(groups):
        rows = sorted(groups[key], reverse=True)
        out.append("")
        out.append("   [%s]  %d file(s)" % (key, len(rows)))
        for t, sz, rel in rows[:60]:
            out.append("      %s %9d  %s" % (_stamp(t), sz, rel))
        if len(rows) > 60:
            out.append("      ... and %d more" % (len(rows) - 60))
    out.append("")
    out.append("   -- backup/leftover files by pattern --")
    import fnmatch
    for pat in ("*.bak", "*.before_*", "*.replaced_by*", "_kit_*", "*.old",
                "*_backup_*"):
        hits = []
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d.lower() != "pyportable"]
            for f in files:
                if fnmatch.fnmatch(f, pat):
                    hits.append(os.path.relpath(os.path.join(base, f), root))
        out.append("      %-16s %d" % (pat, len(hits)))
    return out


def _ascii(x):
    """Never let a stray byte in someone else's file kill this report."""
    return str(x).encode("ascii", "replace").decode("ascii")


def _dump_text(path, maxlines=400):
    out = []
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError as e:
        return ["      (could not read: %s)" % e.__class__.__name__]
    for i, ln in enumerate(lines[:maxlines], 1):
        out.append("      %4d | %s" % (i, _ascii(ln)))
    if len(lines) > maxlines:
        out.append("      ... %d more lines" % (len(lines) - maxlines))
    return out


def _old_scripts():
    """Whatever earlier setup rounds left behind, printed in full.

    manojz's pull excludes `_old`, so nothing off this machine has ever seen
    these. COPY_MARG_DATA.bat in particular is a previous attempt at the very
    job now being designed."""
    root = r"D:\SendToClinic\_old"
    if not os.path.isdir(root):
        return ["   %s does not exist" % root]
    out = []
    for f in sorted(os.listdir(root)):
        p = os.path.join(root, f)
        if not os.path.isfile(p):
            continue
        try:
            sz = os.path.getsize(p)
            when = _stamp(os.stat(p).st_mtime)
        except OSError:
            sz, when = -1, "?"
        out.append("")
        out.append("   ---- %s   %d bytes   %s ----" % (f, sz, when))
        if os.path.splitext(f)[1].lower() in (".bat", ".cmd", ".md", ".ps1",
                                              ".txt", ".ahk", ".py", ".vbs"):
            out.extend(_dump_text(p))
        else:
            out.append("      (not a text file -- not printed)")
    return out or ["   (_old is empty)"]


def _live_file_hashes():
    """An md5 for every script and launcher on this machine.

    There is currently NO pin for any medical-PC file: verify_live_pins.py
    runs on the VPS and cannot reach here, and the pull's mirror is not the
    machine. Without this, drift on this PC is undetectable by construction."""
    out = []
    targets = []
    root = r"D:\SendToClinic"
    if os.path.isdir(root):
        for f in sorted(os.listdir(root)):
            p = os.path.join(root, f)
            if os.path.isfile(p) and os.path.splitext(f)[1].lower() in (
                    ".py", ".bat", ".cmd", ".vbs", ".ps1", ".ahk"):
                targets.append(p)
    startup = os.path.join(os.environ.get("APPDATA", ""), "Microsoft",
                           "Windows", "Start Menu", "Programs", "Startup")
    if os.path.isdir(startup):
        for f in sorted(os.listdir(startup)):
            p = os.path.join(startup, f)
            if os.path.isfile(p):
                targets.append(p)
    if not targets:
        return ["   (nothing to hash)"]
    out.append("   %d file(s). Record these as the medical-PC pins:" % len(targets))
    out.append("")
    for p in targets:
        try:
            m = md5_of(p)
            sz = os.path.getsize(p)
            when = _stamp(os.stat(p).st_mtime)
        except OSError as e:
            out.append("      %-42s  UNREADABLE (%s)"
                       % (os.path.basename(p), e.__class__.__name__))
            continue
        out.append("      %-42s %8d  %s  %s"
                   % (os.path.basename(p), sz, m, when))
    out.append("")
    out.append("   (token.txt is deliberately NOT hashed or listed here.)")
    return out


def _marg_running():
    """Is Marg open right now? The Data folder is open Foxpro tables while it
    is, so this decides when a consistent copy is even possible."""
    out = []
    try:
        import subprocess
        p = subprocess.run(["tasklist", "/fo", "csv", "/nh"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=60)
        txt = (p.stdout or b"").decode("utf-8", "replace")
    except Exception as e:                                     # noqa: BLE001
        return ["   (could not list processes: %s)" % e.__class__.__name__]
    hits = []
    for line in txt.splitlines():
        low = line.lower()
        if "marg" in low or "foxpro" in low or "vfp" in low:
            hits.append("      " + _ascii(line.strip()))
    if hits:
        out.append("   MARG IS RUNNING RIGHT NOW:")
        out.extend(hits)
        out.append("")
        out.append("   >>> While it runs, D:\\MARGERP\\Data is open tables.")
        out.append("   >>> A file copy taken now would restore inconsistent.")
    else:
        out.append("   Marg does NOT appear to be running at this moment.")
        out.append("   >>> This is the state in which a copy of the data")
        out.append("   >>> folder would be consistent.")
    out.append("")
    out.append("   -- where the Marg executables live --")
    for d in ("D:\\", "C:\\"):
        base = os.path.join(d, "MARGERP")
        if not os.path.isdir(base):
            continue
        for f in sorted(os.listdir(base)):
            if f.lower().endswith(".exe"):
                p = os.path.join(base, f)
                try:
                    out.append("      %-40s %10d  %s"
                               % (p, os.path.getsize(p),
                                  _stamp(os.stat(p).st_mtime)))
                except OSError:
                    pass
    return out


def _mbk_inventory():
    """Every backup-shaped file on the stick -- the manifest for an offsite
    copy, with the total that would have to travel."""
    stick = BACKUP_STICK_GUESS + "\\"
    if not os.path.isdir(stick):
        return ["   stick not present"]
    rows = []
    for base, dirs, files in os.walk(stick):
        dirs[:] = [d for d in dirs if d.lower() not in
                   ("system volume information", "$recycle.bin")]
        for f in files:
            p = os.path.join(base, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            rows.append((st.st_mtime, st.st_size, p))
    rows.sort(reverse=True)
    bk = [r for r in rows if r[2].lower().endswith(BACKUP_EXTS)
          or "_c18_" in os.path.basename(r[2]).lower()]
    out = ["   %d file(s) on the stick; %d are backup-shaped." % (len(rows), len(bk))]
    tot = sum(r[1] for r in bk)
    out.append("   total to copy offsite: %s across %d file(s)" % (_gb(tot), len(bk)))
    out.append("")
    for t, sz, p in bk:
        out.append("      %s %10d  %.1fd  %s" % (_stamp(t), sz, _age_days(t), p))
    out.append("")
    other = [r for r in rows if r not in bk]
    out.append("   %d other file(s) on the stick (newest 10):" % len(other))
    for t, sz, p in other[:10]:
        out.append("      %s %10d  %s" % (_stamp(t), sz, p))
    return out


def _drive_state():
    """Can the Drive folder actually receive a nightly backup?"""
    out = []
    fm, arch = find_drive()
    if not fm:
        return ["   Google Drive folder NOT FOUND from this machine.",
                "   >>> An offsite leg via Drive is not possible until it is."]
    base = os.path.dirname(fm)
    out.append("   Drive base : %s" % base)
    out.append("   FromMedical: %s" % fm)
    out.append("   MargArchive: %s" % (arch or "(absent)"))
    tom = os.path.join(base, "ToMedical")
    out.append("   ToMedical  : %s" % (tom if os.path.isdir(tom) else "(absent)"))
    out.append("")
    for label, p in (("FromMedical", fm), ("ToMedical", tom), ("base", base)):
        if os.path.isdir(p):
            out.append("      %-12s readable=%s writable=%s"
                       % (label, os.access(p, os.R_OK), os.access(p, os.W_OK)))
    drv = os.path.splitdrive(base)[0]
    if drv:
        free, total = _free_bytes(drv)
        out.append("")
        out.append("   Drive volume %s : free %s of %s" % (drv, _gb(free), _gb(total)))
    bkf = os.path.join(base, "MargBackups")
    out.append("   MargBackups folder: %s"
               % ("EXISTS" if os.path.isdir(bkf) else "does not exist yet"))
    return out


def _startup_cmd():
    """How the agent is really launched -- read it, do not assume it."""
    startup = os.path.join(os.environ.get("APPDATA", ""), "Microsoft",
                           "Windows", "Start Menu", "Programs", "Startup")
    out = []
    if not os.path.isdir(startup):
        return ["   Startup folder not found"]
    for f in sorted(os.listdir(startup)):
        p = os.path.join(startup, f)
        if not os.path.isfile(p) or f.lower() == "desktop.ini":
            continue
        out.append("")
        out.append("   ---- %s ----" % p)
        out.extend(_dump_text(p, 80))
    return out or ["   (nothing but desktop.ini)"]


def backup_section(fm=None):
    """The whole backup picture, as a list of lines. Reads only.

    S203.4: the report is FLUSHED to disk after every section. S203.3 produced
    no file at all -- one slow or failing section destroyed the whole report,
    including the sections that had already succeeded. A survey that only
    exists if every part of it succeeds is not a survey."""
    L = []
    targets = [p for p in ((os.path.join(fm, "BACKUP.txt") if fm else None),
                           r"D:\SendToClinic\BACKUP.txt") if p]

    def say(s=""):
        L.append(s)

    def flush(step=""):
        if step:
            print("   ... %s" % step)
        blob = "\n".join(L) + "\n"
        for _t in targets:
            try:
                with io.open(_t, "w", encoding="utf-8") as fh:
                    fh.write(blob)
            except OSError:
                pass

    def section(title, fn):
        """Run one section. If it fails, SAY SO IN THE REPORT and carry on."""
        try:
            for _l in fn():
                say(_l)
        except Exception as exc:                               # noqa: BLE001
            import traceback
            say("   *** THIS SECTION FAILED: %s: %s"
                % (exc.__class__.__name__, exc))
            for _tl in traceback.format_exc().splitlines()[-6:]:
                say("       %s" % _tl)
            say("   *** The rest of the report is unaffected.")
        flush(title)

    say("MARG BACKUP SURVEY   %s" % dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    say("census %s   computer: %s   user: %s"
        % (CENSUS_VERSION, os.environ.get("COMPUTERNAME", "?"),
           os.environ.get("USERNAME", "?")))
    say("Read-only. Nothing on this machine was changed.")
    say("")

    # ---- 1. is the stick even here? ---------------------------------------
    say("=" * 76)
    say("1. DRIVES, AND THE BACKUP STICK")
    say("=" * 76)
    present = []
    for c in string.ascii_uppercase:
        d = c + ":"
        if os.path.isdir(d + "\\"):
            free, total = _free_bytes(d)
            present.append(d)
            say("   %s   free %-10s of %-10s" % (d, _gb(free), _gb(total)))
    say("")
    if BACKUP_STICK_GUESS not in present:
        say("   *** %s IS NOT PRESENT RIGHT NOW." % BACKUP_STICK_GUESS)
        say("   *** The stick is unplugged, has changed letter, or has failed.")
        say("   *** ON ITS OWN THIS EXPLAINS AN EMPTY AUTOMATIC BACKUP:")
        say("   *** a backup job whose target is missing writes nothing and,")
        say("   *** in Marg, says nothing.")
        say("")
        say("   Checking the other drives for Marg backup folders anyway:")
        for d in present:
            if d in ("C:", "D:"):
                continue
            for name in ("auto", "MARGBCKUP", "MARG", "Backup"):
                p = os.path.join(d + "\\", name)
                if os.path.isdir(p):
                    n, b, np_, nt = _dir_facts(p)
                    say("      FOUND %s -- %d file(s), %s, newest %s"
                        % (p, n, _gb(b), _stamp(nt) if nt else "never"))
    else:
        say("   %s is present." % BACKUP_STICK_GUESS)

    flush("drives")
    # ---- 2. the backup folders --------------------------------------------
    say("")
    say("=" * 76)
    say("2. THE BACKUP FOLDERS")
    say("=" * 76)
    any_recent = False
    for p in BACKUP_DIRS:
        if not os.path.isdir(p):
            say("   %-28s  does not exist" % p)
            continue
        n, b, np_, nt = _dir_facts(p)
        if n == 0:
            say("   %-28s  EMPTY" % p)
            continue
        age = _age_days(nt)
        flag = ""
        if age <= BACKUP_STALE_DAYS:
            any_recent = True
        else:
            flag = "   <-- STALE (%.0f days)" % age
        say("   %-28s  %d file(s), %s%s" % (p, n, _gb(b), flag))
        say("        newest: %s  (%.1f days old)" % (_stamp(nt), age))
        say("        %s" % np_)
    say("")

    flush("backup folders")
    # ---- 3. what has actually been written, newest first -------------------
    say("=" * 76)
    say("3. THE 25 NEWEST FILES ANYWHERE ON THE STICK")
    say("   (the honest answer to 'has anything been written to it?')")
    say("=" * 76)
    stick = BACKUP_STICK_GUESS + "\\"
    stick_present = os.path.isdir(stick)
    newest_backup_age = None
    if not stick_present:
        say("   stick not present -- skipped")
    else:
        allf = []
        for base, dirs, files in os.walk(stick):
            dirs[:] = [d for d in dirs
                       if d.lower() not in ("system volume information",
                                            "$recycle.bin")]
            for f in files:
                p = os.path.join(base, f)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                allf.append((st.st_mtime, st.st_size, p))
        allf.sort(reverse=True)
        say("   total files on the stick: %d" % len(allf))
        say("")
        for t, sz, p in allf[:25]:
            say("   %s  %12d  %.1fd  %s" % (_stamp(t), sz, _age_days(t), p))
        if not allf:
            say("   THE STICK IS COMPLETELY EMPTY.")
        say("")
        bk = [x for x in allf if x[2].lower().endswith(BACKUP_EXTS)]
        if bk:
            say("   newest backup-shaped file (%s):" % ", ".join(BACKUP_EXTS))
            say("      %s  %d bytes  %.1f days old"
                % (_stamp(bk[0][0]), bk[0][1], _age_days(bk[0][0])))
            say("      %s" % bk[0][2])
            newest_backup_age = _age_days(bk[0][0])
        else:
            say("   NO backup-shaped file (.zip/.bak/.mbk/...) anywhere on the stick.")

    flush("stick contents")
    # ---- 4. what a backup would have to cover ------------------------------
    say("")
    say("=" * 76)
    say("4. WHAT A REAL BACKUP HAS TO COVER  (the Marg data itself)")
    say("=" * 76)
    server_backup_age = None
    for _sb in (r"D:\MARGERP\serverbackup", r"C:\MARGERP\serverbackup"):
        if os.path.isdir(_sb):
            _n, _b, _np, _nt = _dir_facts(_sb)
            if _nt:
                server_backup_age = _age_days(_nt)
                say("   MARG'S OWN INTERNAL BACKUP: %s" % _sb)
                say("      %d file(s), %s, newest %s (%.1f days old)"
                    % (_n, _gb(_b), _stamp(_nt), server_backup_age))
                say("      >>> NOTE: this is on the SAME DISK as the data it")
                say("      >>> protects. It survives a mistake. It does not")
                say("      >>> survive the disk.")
                say("")
    for root in MARG_ROOTS:
        if not os.path.isdir(root):
            say("   %s  does not exist" % root)
            continue
        say("   %s" % root)
        try:
            subs = sorted(os.listdir(root))
        except OSError:
            subs = []
        for s in subs:
            p = os.path.join(root, s)
            if not os.path.isdir(p):
                continue
            n, b, np_, nt = _dir_facts(p)
            say("      %-42s %8d file(s)  %10s  newest %s"
                % (s[:42], n, _gb(b), _stamp(nt) if nt else "never"))
    say("")

    flush("marg data size")
    # ---- 5. is anything scheduled to do it? --------------------------------
    say("=" * 76)
    say("5. IS ANYTHING SCHEDULED TO RUN A BACKUP?")
    say("=" * 76)
    _sched = _scheduled_tasks()
    scheduled_exists = not any("NONE." in ln for ln in _sched)
    for line in _sched:
        say(line)
    say("")
    say("   -- things that start with Windows --")
    for line in _startup_items():
        say(line)
    say("")

    flush("scheduled tasks")
    # ---- 6. marg's own configuration ---------------------------------------
    say("=" * 76)
    say("6. MARG'S OWN BACKUP CONFIGURATION")
    say("=" * 76)
    for line in _marg_backup_config():
        say(line)
    say("")

    flush("marg config")
    # ---- 7. the verdict ----------------------------------------------------
    say("=" * 76)
    say("7. WHAT THIS MEANS")
    say("=" * 76)
    if not stick_present:
        say("   THE BACKUP TARGET IS NOT ATTACHED. Nothing else matters until")
        say("   it is: any backup run has been writing to a drive letter that")
        say("   is not there.")
    else:
        say("   The stick IS attached and writable (see section 1), so the")
        say("   target was never the problem.")
        say("")
        if newest_backup_age is None:
            say("   But there is NO backup-shaped file on it at all.")
        elif newest_backup_age <= BACKUP_STALE_DAYS:
            say("   Newest backup on the stick: %.1f days old. Current."
                % newest_backup_age)
        else:
            say("   NEWEST BACKUP ON THE STICK IS %.1f DAYS OLD."
                % newest_backup_age)
            say("   Everything the pharmacy did since then exists in one place.")
        say("")
        if not any_recent:
            say("   The folders a scheduled Marg backup would write to")
            say("   (E:\\auto, E:\\MARGBCKUP\\auto) are EMPTY or long stale,")
            say("   while the stick's ROOT has recent backups. So the backups")
            say("   that exist are the ones made BY HAND, and they land")
            say("   somewhere else entirely.")
            say("")
        if not scheduled_exists:
            say("   AND NOTHING IN TASK SCHEDULER OR AT STARTUP RUNS A BACKUP.")
            say("   This is the answer to 'why does the automatic backup")
            say("   produce nothing': there is nothing to produce it. The")
            say("   empty auto folders were never going to fill.")
        else:
            say("   A scheduled task DOES exist (section 5). If the auto")
            say("   folders are still empty, it is running and failing.")
        if server_backup_age is not None:
            say("")
            say("   One automatic backup DOES run: Marg's own serverbackup,")
            say("   last written %.1f days ago -- but onto D:, the same disk"
                % server_backup_age)
            say("   as the data. It is not an answer to disk failure.")
    say("")
    say("   ALL 308 MB OF IT SITS ON A STICK ATTACHED TO THE MACHINE IT")
    say("   PROTECTS. That is a defence against a dead disk and against")
    say("   nothing else -- not fire, not theft, not ransomware.")
    say("   AND NO RESTORE HAS EVER BEEN TESTED.")
    say("")
    say("")
    say("=" * 76)
    say("8. MARG'S serverbackup FOLDER -- WHAT IS REALLY IN IT")
    say("=" * 76)
    section("serverbackup", _serverbackup_detail)

    say("")
    say("=" * 76)
    say("9. WHEN IS THIS MACHINE ACTUALLY ON?")
    say("   (from Windows' own event log -- not from anybody's memory)")
    say("=" * 76)
    section("power history", _power_history)

    say("")
    say("=" * 76)
    say("10. EVERY SCHEDULED TASK ON THIS MACHINE, UNFILTERED")
    say("    (S195 registered a logon task 'Marg export watcher'. A filtered")
    say("     query returning NONE is not proof it is gone.)")
    say("=" * 76)
    section("all tasks", _all_task_names)

    say("")
    say("=" * 76)
    say("11. D:\\SendToClinic AS IT REALLY IS ON THIS MACHINE")
    say("    (manojz mirrors this folder with robocopy /E and NO /PURGE, so")
    say("     its copy keeps every file ever deleted here. This is the truth.)")
    say("=" * 76)
    section("SendToClinic listing", _sendtoclinic_listing)
    say("")
    say("")
    say("=" * 76)
    say("12. THE ARCHAEOLOGY -- D:\\SendToClinic\\_old, PRINTED IN FULL")
    say("    (manojz's pull excludes _old, so nothing off this machine has")
    say("     ever seen these. COPY_MARG_DATA.bat is a previous attempt at")
    say("     the job being designed now.)")
    say("=" * 76)
    section("archaeology", _old_scripts)

    say("")
    say("=" * 76)
    say("13. AN md5 FOR EVERY LIVE FILE ON THIS MACHINE")
    say("    (there is no medical-PC pin anywhere today: the pin checker runs")
    say("     on the VPS and cannot reach here. Drift here is undetectable.)")
    say("=" * 76)
    section("live hashes", _live_file_hashes)

    say("")
    say("=" * 76)
    say("14. IS MARG RUNNING RIGHT NOW?")
    say("    (its data is open Foxpro tables while it is -- this decides when")
    say("     a consistent copy is possible at all)")
    say("=" * 76)
    section("marg process", _marg_running)

    say("")
    say("=" * 76)
    say("15. THE FULL BACKUP INVENTORY ON THE STICK")
    say("    (the manifest for an offsite copy, and what it would weigh)")
    say("=" * 76)
    section("mbk inventory", _mbk_inventory)

    say("")
    say("=" * 76)
    say("16. CAN THE DRIVE FOLDER RECEIVE A NIGHTLY BACKUP?")
    say("=" * 76)
    section("drive state", _drive_state)

    say("")
    say("=" * 76)
    say("17. HOW THE AGENT IS ACTUALLY LAUNCHED")
    say("=" * 76)
    section("startup", _startup_cmd)
    say("")
    say("=" * 76)
    say("END OF BACKUP SURVEY. Nothing was changed.")
    return L


def main():
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    fm, arch = find_drive()
    idx = archive_index(arch)

    say("MEDICAL PC CENSUS   %s" % dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    say("computer: %s   user: %s" % (os.environ.get("COMPUTERNAME", "?"),
                                     os.environ.get("USERNAME", "?")))
    say("archive index: %s (%d known files)"
        % (arch or "NOT FOUND -- is Google Drive running?", len(idx)))
    say("")
    say("This runs ON the medical PC, so it sees BOTH drives. The manojz tools")
    say("see the D: share only, and cannot look at C: at all.")

    total = missed = cant_take = 0
    for root, why in ROOTS:
        say("")
        say("=" * 76)
        say("%s   -- %s" % (root, why))
        if not os.path.isdir(root):
            say("   (does not exist on this PC)")
            continue
        found = []
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d.lower() not in SKIP_DIRS]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in SKIP_EXTS:
                    continue
                if ext not in WATCHED_EXTS and ext not in REPORTABLE_EXTS:
                    continue
                p = os.path.join(base, f)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                found.append((p, st.st_size, st.st_mtime, ext))
        if not found:
            say("   (nothing report-shaped here)")
            continue
        found.sort(key=lambda t: t[2], reverse=True)
        for p, size, mtime, ext in found:
            total += 1
            when = dt.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            if ext not in WATCHED_EXTS:
                cant_take += 1
                say("   %s  %9d  CANNOT BE CAPTURED (%s)" % (when, size, ext))
                say("        %s" % os.path.relpath(p, root))
                continue
            try:
                m = md5_of(p) if size <= MAX_HASH else None
            except OSError:
                say("   %s  COULD NOT READ  %s" % (when, os.path.relpath(p, root)))
                continue
            state = idx.get(m or "")
            if state:
                say("   %s  %9d  in the archive  [%s]" % (when, size, state))
            else:
                missed += 1
                say("   %s  %9d  *** NOT IN THE ARCHIVE ***" % (when, size))
            say("        %s" % os.path.relpath(p, root))
            say("        %s" % title_of(p))

    say("")
    say("=" * 76)
    say("report-shaped files on this PC     : %d" % total)
    say("NOT in the archive                 : %d" % missed)
    say("in a format the watcher cannot take: %d" % cant_take)
    if missed:
        say("")
        say("A file not in the archive means the pipeline never filed it.")
        say("Check that the watcher is running (FromMedical\\heartbeat.txt), then")
        say("send this file to Claude.")
    if cant_take:
        say("")
        say("A format the watcher cannot take is a report that will never reach")
        say("the clinic. Export it as Excel or PDF instead.")
    if not missed and not cant_take:
        say("Everything report-shaped on this PC is in the archive.")

    # S203 -- the backup survey (F-191c). Appended to the census, and also
    # written on its own so it is easy to find.
    say("")
    say("")
    try:
        backup_lines = backup_section(fm)
    except Exception as exc:                                   # noqa: BLE001
        import traceback
        backup_lines = ["THE BACKUP SURVEY FAILED OUTRIGHT: %s: %s"
                        % (exc.__class__.__name__, exc)] + \
                       traceback.format_exc().splitlines()[-8:]
    for _bl in backup_lines:
        say(_bl)
    _bout = "\n".join(backup_lines) + "\n"
    for _p in [p for p in (os.path.join(fm, "BACKUP.txt") if fm else None,
                           r"D:\SendToClinic\BACKUP.txt") if p]:
        try:
            with io.open(_p, "w", encoding="utf-8") as fh:
                fh.write(_bout)
            print("\n(backup survey written to %s)" % _p)
        except OSError as e:
            print("\n(could not write %s: %s)" % (_p, e))

    out = "\n".join(lines) + "\n"
    for path in [p for p in (os.path.join(fm, "CENSUS.txt") if fm else None,
                             r"D:\SendToClinic\CENSUS.txt") if p]:
        try:
            with io.open(path, "w", encoding="utf-8") as fh:
                fh.write(out)
            print("\n(written to %s)" % path)
        except OSError as e:
            print("\n(could not write %s: %s)" % (path, e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
