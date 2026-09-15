#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_s280.py -- S280_JOB_PULSE_FIX

Replaces /root/finance/job_pulse.py with v1.1. Nothing else: the cron line from
S279 already exists and is untouched, so this installer never opens the crontab.

WHY
    The first live run of v1.0 exposed two faults in it.
    1. Two systemd timers reported a run in the FUTURE and an age of -329 min.
       v1.0 forced UTC onto systemd's timestamp, which is printed in the box's
       own zone, and then added 5:30 on top. v1.1 asks systemd for a unix epoch,
       which carries no zone to get wrong, and refuses to call a negative age
       healthy -- it reports AHEAD? and counts it as a problem.
    2. marg_ingest.py read SILENT at 2.3 days while its own mi_run table showed
       it had run at 01:00 that morning. It runs every five minutes and prints
       nothing on a quiet pass, so its log does not move. v1.1 reads the run
       table for the seven jobs that keep one, and falls back to the log only
       where there is none. Each line now says which it read.

SAFETY
    refuses unless v1.0 is what is installed * backs up to
    job_pulse.py.bak_S280_<md5> * runs the new file's own selftest ON THIS BOX
    before putting it in place * restores the backup if the first run fails.
"""
import hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "job_pulse.py")
DEST = "/root/finance/job_pulse.py"
PY = "/root/wa/venv/bin/python3"
EXPECT_OLD = "cbeb6d72d09a3c8114056dfabb8f70fd"


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def fail(m):
    print("REFUSED: %s" % m)
    sys.exit(1)


def main():
    if not os.path.isfile(SRC):
        fail("job_pulse.py is not beside this installer")
    if not os.path.isfile(DEST):
        fail("%s is not there -- install S279 first" % DEST)
    cur = md5(DEST)
    if cur == md5(SRC):
        print("Already installed -- v1.1 is in place. Nothing changed.")
        return 0
    if cur != EXPECT_OLD:
        fail("job_pulse.py is %s, expected v1.0 %s. It has moved on since this "
             "kit was built; rebuild against the file as it is now." % (cur, EXPECT_OLD))

    r = subprocess.run([PY, SRC, "--selftest"], capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(r.stdout[-2500:])
        fail("v1.1 did not pass its own selftest on this machine")
    print("selftest : passed on this box (%d checks)"
          % r.stdout.count("\nok   "))

    bak = "%s.bak_S280_%s" % (DEST, EXPECT_OLD[:8])
    shutil.copy2(DEST, bak)
    print("backup   : %s (%s)" % (bak, md5(bak)))
    shutil.copy2(SRC, DEST)
    os.chmod(DEST, 0o755)
    print("job_pulse: %s -> %s" % (cur, md5(DEST)))

    r = subprocess.run([PY, "-B", DEST, "--print"], capture_output=True,
                       text=True, timeout=300)
    if r.returncode != 0:
        print(r.stdout[-1500:])
        print(r.stderr[-1500:])
        shutil.copy2(bak, DEST)
        print("restored : %s" % md5(DEST))
        fail("the new version would not run; the old one is back")
    sys.stdout.write("\n" + r.stdout[-6500:])
    print("")
    print("DONE. Same hourly cron line, unchanged.")
    print("To undo:  \\cp %s %s" % (bak, DEST))
    return 0


if __name__ == "__main__":
    sys.exit(main())
