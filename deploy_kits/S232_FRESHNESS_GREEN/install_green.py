#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_green.py  --  S232 : the freshness layer says good morning.

THE OWNER'S ASK, 08-Sep-2026, and it is a real gap not a preference:
    "phone stayed quiet, better if it lists all it checks with check marks"

Until now silence was the passing grade. But **silence cannot tell "all 26 legs
are healthy" apart from "the job never ran"**. The S231 brief says as much -- a
missing 08:05 line is itself the finding -- yet nothing was watching for that
missing line except the owner remembering to look.

WHAT CHANGES
    One push a day when everything is fresh. Title is ASCII and one line, so on
    the phone it collapses to:   Clinic freshness: all 26 fresh
    Expanded, every leg with a tick and its age.
    At most ONCE per calendar day. A stale leg still shouts exactly as before.

    So the ABSENCE of the morning line is now readable, which is the whole point.

WHY THE TITLE HAS NO EMOJI
    ntfy sends Title as an HTTP header and a non-ASCII header breaks the push.
    That is recorded in clinic_health_report.py and it is why the tick marks
    live in the body.

CONFIGURATION, NOT CODE (D417/D423)
    DAILY_GREEN in the conf. Absent = on. Set it to 0/off/no/false to silence
    the morning line without touching a line of code.

RUN (VPS, root):
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S232_FRESHNESS_GREEN/install_green.py --check
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S232_FRESHNESS_GREEN/install_green.py --install
"""

import os
import sys
import shutil
import hashlib
import datetime
import subprocess

SRC   = "/root/deploy/repo/deploy_kits/S232_FRESHNESS_GREEN/freshness.py"
LIVE  = "/root/finance/freshness.py"
STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP = "/root/_backup_S232_green_%s" % STAMP

EXPECTED_OLD = "6476d1d28d47055813737a66514dacaf"   # the S230 pin, still live
EXPECTED_NEW = "66d93a631c6c46ebb6536620450efa74"


def say(m=""):
    print(m, flush=True)


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def main():
    mode = "--check"
    for a in sys.argv[1:]:
        if a in ("--check", "--install"):
            mode = a

    say("=" * 70)
    say("S232 freshness daily-green  --  mode %s  --  %s" % (mode, STAMP))
    say("=" * 70)

    say("\n[1] the two files")
    for p in (SRC, LIVE):
        if not os.path.exists(p):
            say("    REFUSING -- %s not found" % p)
            return 2
    s, l = md5(SRC), md5(LIVE)
    say("    repo : %s" % s)
    say("    live : %s" % l)
    if s != EXPECTED_NEW:
        say("\n    REFUSING -- the repo copy is not the version this kit was built")
        say("    for (expected %s). Publish and pull again." % EXPECTED_NEW)
        return 2
    if l == EXPECTED_NEW:
        say("\n    already installed -- nothing to do")
        return 0
    if l != EXPECTED_OLD:
        say("\n    REFUSING -- the LIVE file has drifted. It is neither the S230")
        say("    pin (%s) nor the new version." % EXPECTED_OLD)
        say("    Something edited it outside the repository. Tell Claude both hashes.")
        return 2
    say("    live is exactly the S230 pin -- safe to replace")

    if mode == "--check":
        say("\n[2] --check only. NOTHING WAS CHANGED.")
        return 0

    say("\n[2] backing up")
    os.makedirs(BACKUP, exist_ok=True)
    shutil.copy2(LIVE, os.path.join(BACKUP, "freshness.py.bak"))
    say("    %s" % BACKUP)

    say("\n[3] installing")
    shutil.copy2(SRC, LIVE)
    if md5(LIVE) != EXPECTED_NEW:
        say("    REFUSING -- copy did not land. Restore:")
        say("      \\cp %s/freshness.py.bak %s" % (BACKUP, LIVE))
        return 2
    try:
        import py_compile
        py_compile.compile(LIVE, cfile="/tmp/_green_check.pyc", doraise=True)
        os.remove("/tmp/_green_check.pyc")
    except Exception as e:
        say("    REFUSING -- installed file does not compile: %s" % e)
        shutil.copy2(os.path.join(BACKUP, "freshness.py.bak"), LIVE)
        say("    rolled back.")
        return 2
    say("    copied and compiles")

    say("\n[4] running it once, for real -- this sends the push NOW")
    say("    (nothing is scheduled differently; the 08:05 cron is untouched)")
    r = subprocess.run(["/root/wa/venv/bin/python3", LIVE, "--shout"],
                       capture_output=True, text=True, timeout=180)
    tail = [x for x in (r.stdout or "").splitlines() if x.strip()][-6:]
    for x in tail:
        say("    %s" % x)
    if r.returncode != 0:
        say("    exit code %d -- stderr:" % r.returncode)
        for x in (r.stderr or "").splitlines()[-6:]:
            say("      %s" % x)
        say("    The file is installed and compiles. Read the lines above before")
        say("    deciding whether to roll back.")
        return 1

    say("\n" + "=" * 70)
    say("DONE. Check your phone -- a push should have just arrived.")
    say("From tomorrow it comes once each morning after the 08:05 run, and only once.")
    say("A stale leg still shouts separately, exactly as before.")
    say("=" * 70)
    say("To silence the morning line later, without touching code:")
    say("  add   DAILY_GREEN=off   to /root/finance/freshness.conf")
    say("Undo:")
    say("  \\cp %s/freshness.py.bak %s" % (BACKUP, LIVE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
