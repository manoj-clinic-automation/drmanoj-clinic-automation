#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
setup_pc.py -- kit S458_MEDICAL_PC_KIT. Puts the clinic's tools back on the MEDICAL PC (the pharmacy
counter PC that runs Marg) after a Windows reinstall. Run by the file the "Clinic PCs" page hands
out; safe to run by hand and safe to run again.

THE ONE RULE: IT ONLY FILLS WHAT IS MISSING. A file that is already in D:\SendToClinic is never
replaced, whatever the kit holds -- so running this on the working PC changes nothing, and a tool
the Sanjeevni side has updated since this kit was packed is left as it is. (The agent's own road,
the clinic Drive's ToMedical\_kit folder, keeps bringing the current tools once Drive is signed in.)

What it does, in order:
  1  the kit is whole (every row of MD5SUMS.txt)
  2  D:\SendToClinic exists (made if not); a PC with no D: drive is refused
  3  its own Python 3.11.9 at D:\SendToClinic\pyportable (unpacked only if absent)
  4  each tool that is missing is placed and read back; each one already there is left alone
  5  this account starts the agent at every sign-in (MargAgent.cmd), unless that is already so
  6  the agent is started if it is not running; its heartbeat is read back

It never touches token.txt, _captured, _off, a log, Marg, or any other folder.
Standard library only. Prints counts and file names of tools only.

    python setup_pc.py --kit <folder this file is in> [--pyzip <pyportable.zip>] [--log <file>]
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import time
import zipfile

VERSION = "S458.1"
IS_WIN = os.name == "nt"
TARGET = os.environ.get("CLINIC_SETUP_TARGET", r"D:\SendToClinic")
ENTRY = "MargAgent.cmd"
STARTER = "START_AGENT.cmd"
FRESH_SECONDS = 600                     # a heartbeat younger than this means the agent is running
_LOG = [None]
ATTENTION = []


def say(msg=""):
    print(msg)
    sys.stdout.flush()
    if _LOG[0]:
        try:
            with open(_LOG[0], "a", encoding="utf-8") as fh:
                fh.write(msg + "\n")
        except OSError:
            pass


def md5(path):
    try:
        h = hashlib.md5()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def stop(why):
    say("")
    say("STOP: %s." % why)
    say("Nothing else was changed. Tell Claude what this window says.")
    return 1


def kit_rows(kit):
    """[(md5, relative path)] from MD5SUMS.txt, or None when it cannot be read."""
    rows = []
    try:
        with open(os.path.join(kit, "MD5SUMS.txt"), "r", encoding="ascii") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                if line.strip():
                    m, n = line.split("  ", 1)
                    rows.append((m.strip().lower(), n.strip()))
    except (OSError, ValueError):
        return None
    return rows


def startup_dirs():
    allusers = os.environ.get("CLINIC_SETUP_ALLUSERS") or os.path.join(
        os.environ.get("ProgramData", r"C:\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs", "StartUp")
    mine = os.environ.get("CLINIC_SETUP_MINE") or os.path.join(
        os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    return allusers, mine


def heartbeat_age(target):
    try:
        return time.time() - os.path.getmtime(os.path.join(target, "heartbeat.txt"))
    except OSError:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--pyzip", default="")
    ap.add_argument("--log", default="")
    ap.add_argument("--no-start", action="store_true", help="place everything but do not start the agent")
    a = ap.parse_args(argv)
    _LOG[0] = a.log or None
    kit, target = os.path.abspath(a.kit), TARGET
    say("Setting up the Medical PC -- kit %s -- %s on %s" % (
        VERSION, os.environ.get("USERNAME", "?"), os.environ.get("COMPUTERNAME", "?")))
    say("")

    # 1 -- the kit is whole
    rows = kit_rows(kit)
    if not rows:
        return stop("the kit has no readable MD5SUMS.txt")
    bad = [n for m, n in rows if md5(os.path.join(kit, n.replace("/", os.sep))) != m]
    if bad:
        return stop("the kit is not whole -- %d file(s) are not as listed: %s" % (len(bad), ", ".join(bad[:5])))
    payload = sorted(n[len("payload/"):] for m, n in rows if n.startswith("payload/"))
    if STARTER not in payload or "medical_agent.py" not in payload or "agent_guard.py" not in payload:
        return stop("the kit does not hold the agent, its guard and its starter")
    say("  1 of 6  the kit is whole                      ok  (%d files, %d of them tools)" % (len(rows), len(payload)))

    # 2 -- the folder
    drive = os.path.splitdrive(target)[0]
    if IS_WIN and drive and not os.path.isdir(drive + os.sep):
        return stop("this PC has no %s drive -- Marg and the clinic's tools live on %s (README, step A)" % (drive, drive))
    try:
        os.makedirs(target, exist_ok=True)
        probe = os.path.join(target, "_write_probe_setup.txt")
        with open(probe, "w") as fh:
            fh.write("probe")
        os.remove(probe)
    except OSError as ex:
        return stop("this account cannot write in %s (%s)" % (target, ex.__class__.__name__))
    say("  2 of 6  %s                     ok" % target)

    # 3 -- its own Python
    py, pyw = (os.path.join(target, "pyportable", n) for n in ("python.exe", "pythonw.exe"))
    if os.path.isfile(py) and os.path.isfile(pyw):
        say("  3 of 6  its own Python                        ok  (already there, left alone)")
    else:
        src = a.pyzip if (a.pyzip and os.path.isfile(a.pyzip)) else os.path.join(kit, "pyportable.zip")
        if not os.path.isfile(src):
            return stop("the Python part did not come with the kit and %s has none" % target)
        try:
            with zipfile.ZipFile(src) as z:
                names = [n for n in z.namelist() if n.startswith("pyportable/") and ".." not in n]
                z.extractall(target, names)
        except (OSError, zipfile.BadZipFile) as ex:
            return stop("the Python part could not be unpacked (%s)" % ex.__class__.__name__)
        if not (os.path.isfile(py) and os.path.isfile(pyw)):
            return stop("the Python part was unpacked but python.exe is not in %s\\pyportable" % target)
        say("  3 of 6  its own Python                        ok  (unpacked, %d files)" % len(names))

    # 4 -- the tools: only what is missing
    placed, same, kept = [], [], []
    for rel in payload:
        src, dst = os.path.join(kit, "payload", rel.replace("/", os.sep)), os.path.join(target, rel.replace("/", os.sep))
        if not os.path.exists(dst):
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst + ".part")
                os.replace(dst + ".part", dst)
            except OSError as ex:
                return stop("could not place %s (%s)" % (rel, ex.__class__.__name__))
            if md5(dst) != md5(src):
                return stop("%s was placed but did not read back as the kit's" % rel)
            placed.append(rel)
        elif md5(dst) == md5(src):
            same.append(rel)
        else:
            kept.append(rel)
    say("  4 of 6  the tools                             ok  (%d placed, %d already here and the same, %d kept as this PC has them)"
        % (len(placed), len(same), len(kept)))
    for rel in placed:
        say("            placed: %s" % rel)
    for rel in kept:
        say("            kept, NOT replaced (it differs from the kit's -- the PC's own stays): %s" % rel)

    # 5 -- start at every sign-in
    starter = os.path.join(target, STARTER)
    allusers, mine = startup_dirs()
    here = [(p, md5(p)) for p in (os.path.join(allusers, ENTRY), os.path.join(mine, ENTRY)) if os.path.isfile(p)]
    want = md5(starter)
    if any(m == want for _p, m in here):
        say("  5 of 6  start at every sign-in                ok  (already set%s)"
            % (" for every account" if os.path.isfile(os.path.join(allusers, ENTRY)) and md5(os.path.join(allusers, ENTRY)) == want else " for this account"))
    elif here:
        say("  5 of 6  start at every sign-in                kept  (a different %s is there and was left alone)" % ENTRY)
        ATTENTION.append("the start-up entry %s is not the kit's starter -- left alone; tell Claude" % ENTRY)
    else:
        try:
            os.makedirs(mine, exist_ok=True)
            shutil.copyfile(starter, os.path.join(mine, ENTRY))
            ok = md5(os.path.join(mine, ENTRY)) == want
        except OSError:
            ok = False
        if not ok:
            return stop("could not put the starter in this account's start-up folder")
        say("  5 of 6  start at every sign-in                ok  (set for this account)")
        ATTENTION.append("the staff account: sign in as it once and double-click "
                         "%s\\ENABLE_AGENT_THIS_ACCOUNT.bat" % target)

    # 6 -- the agent
    age = heartbeat_age(target)
    if age is not None and age < FRESH_SECONDS:
        say("  6 of 6  the agent                             ok  (already running; its heartbeat is %d minute(s) old)" % (age // 60))
    elif a.no_start or not IS_WIN:
        say("  6 of 6  the agent                             not started (asked not to)")
    else:
        try:
            subprocess.Popen([os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "cmd.exe"), "/d", "/c", starter],
                             cwd=target, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=0x08000000 | 0x00000200)
        except OSError as ex:
            return stop("the agent could not be started (%s)" % ex.__class__.__name__)
        t0 = time.time()
        while time.time() - t0 < 90:
            age = heartbeat_age(target)
            if age is not None and age < 120:
                break
            time.sleep(3)
        if age is not None and age < 120:
            say("  6 of 6  the agent                             ok  (started; first heartbeat written)")
        else:
            say("  6 of 6  the agent                             started -- no heartbeat yet; look at %s\\heartbeat.txt in five minutes" % target)
            ATTENTION.append("no heartbeat in the first 90 seconds -- read %s\\agent_guard.log" % target)

    if not os.path.isfile(os.path.join(target, "token.txt")):
        ATTENTION.append("token.txt is not in %s -- the capture works, the send to the clinic server is shut until "
                         "it is put back (it is in no kit; Claude gives the one line)" % target)

    say("")
    say("DONE. The clinic's tools are in place on this PC.")
    if ATTENTION:
        say("")
        say("LOOK AT THESE:")
        for line in ATTENTION:
            say("  * " + line)
    say("")
    say("Only a person can do these (README_REINSTALL_MEDICAL.txt, part A):")
    say("  - Marg itself and its data on D:\\MARGERP (the Marg engineer)")
    say("  - the two Windows accounts and signing in at power-on")
    say("  - Google Drive: sign in with the clinic account")
    say("  - Tailscale: sign in;  D: shared as DDrive for the owner's PC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
