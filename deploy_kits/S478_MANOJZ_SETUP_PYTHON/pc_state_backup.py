#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
pc_state_backup.py  (S459)  --  THIS PC'S OWN STATE, zipped to the SSD every night.

Why. A whole reading of this PC on 03-Oct-2026 found that much of the clinic's work that lives ONLY
here was in no backup: the follow-up tracker's code and its settings and key files, the Marg pull's
settings and this PC's signing key, the Docterz archive, and the definitions of the scheduled tasks
that run everything. (The tracker's twelve ledger files have had a nightly Drive copy since before
S230 -- F-261 records it -- and the patient master is mirrored to its Google Sheet every morning.
Those stay as they are; this step does not replace them.) The nightly mirrored the knowledge base
and the server's code. This step puts the whole of this PC's own state in one place, and it is what
the "Clinic PCs" page's setup kit for this PC restores from.

What it copies (never moves, never deletes), into ONE dated zip:
   tracker\            C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker   (code, ledgers, settings)
   margsync_config\    D:\Downloads\margsync\_config
   margsync_MargPull\  D:\Downloads\margsync\MargPull          (not its _logs)
   margsync_off\       D:\Downloads\margsync\_off
   margsync_SendToClinic\  D:\Downloads\margsync\SendToClinic
   margsync_analysis\  D:\Downloads\margsync\_analysis
   margsync_top\       the loose files at D:\Downloads\margsync   (not its folders)
   DocterzArchive\     D:\Downloads\DocterzArchive
   kbtools\            D:\Downloads\_kbtools                    (not vps_code, not manifest_backups)
   clinic_writer\      D:\clinic_writer
   tasks\              every scheduled task in Task Scheduler's top folder, as Windows exports it (.xml)
   MACHINE_FACTS.txt   the Python and its packages, git, the drives, the start-up entries -- names only

Where: F:\ClinicBackup\DrManojClinic_Automation\05_PC_STATE\manojz\manojz_state_<date>.zip , reopened and
every CRC tested. The newest 7 stay; older ones are MOVED into 99_SUPERSEDED beside them.

THE ZIP HOLDS PATIENT DATA AND THIS PC'S SECRETS. It goes to the SSD at this PC and nowhere else.
This script prints and logs counts and sizes only.

A folder that is not there is said, not counted as a pass. An unreadable file is counted and said.
stdlib only.  Exit 0 = OK.  2 = WARN (something was absent or unreadable).  3 = FAIL (no verified zip).
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime

VERSION = "S459 v1.0"
RC_OK, RC_WARN, RC_FAIL = 0, 2, 3
SKIP_DIRS = {"__pycache__"}
SOURCES = [   # (name in the zip, folder, folders inside it that are not taken, loose files only?)
    ("tracker", r"C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker", (), False),
    ("margsync_config", r"D:\Downloads\margsync\_config", (), False),
    ("margsync_MargPull", r"D:\Downloads\margsync\MargPull", ("_logs",), False),
    ("margsync_off", r"D:\Downloads\margsync\_off", (), False),
    ("margsync_SendToClinic", r"D:\Downloads\margsync\SendToClinic", (), False),
    ("margsync_analysis", r"D:\Downloads\margsync\_analysis", (), False),
    ("margsync_top", r"D:\Downloads\margsync", (), True),
    ("DocterzArchive", r"D:\Downloads\DocterzArchive", (), False),
    ("kbtools", r"D:\Downloads\_kbtools", ("vps_code", "manifest_backups"), False),
    ("clinic_writer", r"D:\clinic_writer", (), False),
]
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def md5_of(path, chunk=1024 * 1024):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def run(cmd, timeout=120):
    """(rc, text) of a short helper command; never raises."""
    try:
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout, creationflags=NO_WINDOW)
        return p.returncode, p.stdout.decode("utf-8", "replace")
    except Exception as ex:                                    # noqa: BLE001
        return -1, "%s: %s" % (ex.__class__.__name__, ex)


def walk(folder, skip, loose_only):
    """(relative path, full path) of every file to take."""
    if loose_only:
        try:
            for n in sorted(os.listdir(folder)):
                p = os.path.join(folder, n)
                if os.path.isfile(p):
                    yield n, p
        except OSError:
            return
        return
    for root, dirs, names in os.walk(folder):
        rel_root = os.path.relpath(root, folder)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS
                         and not (rel_root == "." and d in skip))
        for n in sorted(names):
            if n.endswith((".pyc", ".pyo")):
                continue
            p = os.path.join(root, n)
            yield os.path.relpath(p, folder), p


def export_tasks(dest):
    """Every task in Task Scheduler's top folder as <name>.xml in dest. Returns (count, note)."""
    ps = ("$o=$args[0]; $n=0; Get-ScheduledTask -TaskPath '\\' | ForEach-Object { try { "
          "$f=Join-Path $o (($_.TaskName -replace '[\\\\/:*?\"<>|]','_') + '.xml'); "
          "Export-ScheduledTask -TaskName $_.TaskName -TaskPath '\\' | Out-File -LiteralPath $f -Encoding Unicode; $n++ } catch {} }; "
          "Write-Output ('exported ' + $n)")
    script = os.path.join(dest, "_export.ps1")
    with open(script, "w", encoding="utf-8") as fh:
        fh.write(ps)
    rc, out = run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, dest], 180)
    try:
        os.remove(script)
    except OSError:
        pass
    n = len([x for x in os.listdir(dest) if x.lower().endswith(".xml")])
    return n, ("" if (rc == 0 and n) else "powershell rc %s: %s" % (rc, out.strip()[-160:]))


def machine_facts():
    lines = ["MACHINE FACTS -- %s -- written %s" % (VERSION, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
             "computer : %s    user : %s" % (os.environ.get("COMPUTERNAME", "?"), os.environ.get("USERNAME", "?")),
             "python   : %s  (%s)" % (sys.version.split()[0], sys.executable), ""]
    for title, cmd in (("PYTHON PACKAGES (python -m pip freeze)", [sys.executable, "-m", "pip", "freeze"]),
                       ("GIT", ["git", "--version"]),
                       ("TAILSCALE", ["tailscale", "version"]),
                       ("STORED LOGINS (cmdkey /list -- targets only, Windows never shows a password)", ["cmdkey", "/list"])):
        rc, out = run(cmd, 90)
        lines.append("== %s ==" % title)
        lines += [("   " + x.rstrip()) for x in out.splitlines() if x.strip()][:400] or ["   (nothing; rc %s)" % rc]
        lines.append("")
    lines.append("== DRIVES ==")
    lines.append("   " + " ".join("%s:" % c for c in "CDEFGHIJ" if os.path.isdir("%s:\\" % c)))
    lines.append("")
    for title, d in (("START-UP FOLDER, this account", os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")),
                     ("START-UP FOLDER, every account", os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs", "StartUp"))):
        lines.append("== %s ==" % title)
        try:
            lines += ["   " + n for n in sorted(os.listdir(d))] or ["   (empty)"]
        except OSError:
            lines.append("   (not readable)")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="S459 -- this PC's own state to the SSD.")
    ap.add_argument("--tools", default=r"D:\Downloads\_kbtools")
    ap.add_argument("--dest", default=r"F:\ClinicBackup\DrManojClinic_Automation\05_PC_STATE\manojz")
    ap.add_argument("--keep", type=int, default=7)
    ap.add_argument("--no-tasks", action="store_true", help="skip the Task Scheduler export and the machine facts' commands")
    ap.add_argument("--source", action="append", default=[], metavar="NAME=FOLDER",
                    help="replace the built-in list (for the offline walk)")
    a = ap.parse_args(argv)
    sources = SOURCES
    if a.source:
        skips = {n: sk for n, _f, sk, _l in SOURCES}
        sources = [(s.split("=", 1)[0], s.split("=", 1)[1], skips.get(s.split("=", 1)[0], ()), s.split("=", 1)[0].endswith("_top"))
                   for s in a.source]
    worst, out = [RC_OK], []

    def say(line=""):
        out.append(line)

    def verdict(code):
        worst[0] = max(worst[0], code)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    say("PC STATE BACKUP -- %s" % VERSION)
    say("when       : %s (local clock on this PC)" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    say("to         : %s" % a.dest)
    say()
    t0 = time.time()
    name = "manojz_state_%s.zip" % datetime.now().strftime("%Y-%m-%d")
    target = os.path.join(a.dest, name)
    try:
        os.makedirs(a.dest, exist_ok=True)
    except (OSError, ValueError) as ex:
        say("RESULT     : FAIL -- the SSD folder is not reachable (%s). Nothing was written." % ex.__class__.__name__)
        verdict(RC_FAIL)
        return finish(a, out, worst[0], stamp)
    tmp = target + ".part"
    total, nbytes, unread = 0, 0, 0
    work = tempfile.mkdtemp(prefix="pcstate_")
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
            for zname, folder, skip, loose in sources:
                if not os.path.isdir(folder):
                    say("  %-24s NOT THERE -- %s  (said, not counted as a pass)" % (zname, folder))
                    verdict(RC_WARN)
                    continue
                n = b = bad = 0
                for rel, full in walk(folder, skip, loose):
                    try:
                        z.write(full, zname + "/" + rel.replace(os.sep, "/"))
                        n += 1
                        b += os.path.getsize(full)
                    except (OSError, ValueError):
                        bad += 1
                total, nbytes, unread = total + n, nbytes + b, unread + bad
                say("  %-24s %6d file(s)  %15s%s" % (zname, n, "{:,} B".format(b), ("   %d UNREADABLE" % bad) if bad else ""))
                if bad:
                    verdict(RC_WARN)
            if a.no_tasks:
                say("  %-24s SKIPPED by --no-tasks.  Not a pass." % "tasks")
                verdict(RC_WARN)
            else:
                tdir = os.path.join(work, "tasks")
                os.makedirs(tdir)
                n, note = export_tasks(tdir)
                for x in sorted(os.listdir(tdir)):
                    z.write(os.path.join(tdir, x), "tasks/" + x)
                total += n
                say("  %-24s %6d task definition(s)%s" % ("tasks", n, ("   NOTE: " + note) if note else ""))
                if not n:
                    verdict(RC_WARN)
                z.writestr("MACHINE_FACTS.txt", machine_facts())
                total += 1
        with zipfile.ZipFile(tmp) as z:
            bad_member = z.testzip()
            count = len(z.namelist())
        if bad_member is not None or count != total:
            say("RESULT     : FAIL -- the zip did not read back whole (%s entries, %s expected). Kept as .part for a look." % (count, total))
            verdict(RC_FAIL)
            return finish(a, out, worst[0], stamp)
        os.replace(tmp, target)
    except Exception as ex:                                    # noqa: BLE001
        say("RESULT     : FAIL -- %s: %s" % (ex.__class__.__name__, str(ex)[:160]))
        verdict(RC_FAIL)
        return finish(a, out, worst[0], stamp)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    say()
    say("  zip       : %s" % target)
    say("  files     : %d  (%s on disk, %s zipped)%s" % (total, "{:,} B".format(nbytes), "{:,} B".format(os.path.getsize(target)),
                                                         ("   %d UNREADABLE" % unread) if unread else ""))
    say("  md5       : %s" % md5_of(target))
    say("  proof     : reopened, every CRC tested, entry count matches")
    # retention: MOVE, never delete
    olds = sorted(n for n in os.listdir(a.dest) if n.startswith("manojz_state_") and n.endswith(".zip"))
    moved = 0
    for n in olds[:-a.keep] if len(olds) > a.keep else []:
        try:
            sup = os.path.join(a.dest, "99_SUPERSEDED")
            os.makedirs(sup, exist_ok=True)
            shutil.move(os.path.join(a.dest, n), os.path.join(sup, n))
            moved += 1
        except OSError:
            verdict(RC_WARN)
    say("  retention : %d older cop%s moved to 99_SUPERSEDED\\ (nothing deleted)" % (moved, "y" if moved == 1 else "ies"))
    say("  RESULT    : %s" % ("OK" if worst[0] == RC_OK else "WARN -- see the lines above"))
    say()
    say("took       : %.1f s" % (time.time() - t0))
    return finish(a, out, worst[0], stamp)


def finish(a, out, worst, stamp):
    out.append("VERDICT    : %s" % {RC_OK: "OK", RC_WARN: "WARN", RC_FAIL: "FAIL"}[worst])
    text = "\n".join(out) + "\n"
    sys.stdout.write(text)
    try:
        os.makedirs(os.path.join(a.tools, "reports"), exist_ok=True)
        with open(os.path.join(a.tools, "PC_STATE_BACKUP_LATEST.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        shutil.copyfile(os.path.join(a.tools, "PC_STATE_BACKUP_LATEST.txt"), os.path.join(a.tools, "reports", "PC_STATE_%s.txt" % stamp))
    except OSError as ex:
        sys.stderr.write("could not write the report: %s\n" % ex)
        return RC_FAIL
    return worst


if __name__ == "__main__":
    sys.exit(main())
