#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_s283.py -- S283_JOB_PULSE_EMPTY

Replaces /root/finance/job_pulse.py v1.1 with v1.2. Nothing else: the hourly
cron line from S279 is untouched, so this installer never opens the crontab.

WHY (F-498, second half)
    A log that is OLD, a log that is EMPTY and a log that is NOT THERE are three
    different facts. v1.1 read the first two alike, and that cost S259 an hour
    on salts_refresh, which was healthy. v1.2 gives each its own word:
    SILENT / LATE, EMPTY, NEVER RAN -- and a run table still beats all three.

SAFETY
    refuses unless v1.1 917713f5... is what is installed * runs the new file's
    own selftest ON THIS BOX first * backs up to job_pulse.py.bak_S283_917713f5
    * restores the backup byte-identically if the first real run fails *
    running it twice is harmless and says so.

One line on the VPS:
    cd /root/deploy/repo && git pull --ff-only && /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S283_JOB_PULSE_EMPTY/install_s283.py
Undo:
    \\cp /root/finance/job_pulse.py.bak_S283_917713f5 /root/finance/job_pulse.py

Env (rehearsal only): ROOT=/some/dir  PY=/path/to/python3
"""
import hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("ROOT", "/root")
SRC = os.path.join(HERE, "job_pulse.py")
DEST = os.path.join(ROOT, "finance", "job_pulse.py")
PY = os.environ.get("PY", "/root/wa/venv/bin/python3")
EXPECT_OLD = "917713f5269bb6af46ea355fc212ad2c"
EXPECT_NEW = "5eae0eb742bd79b202545fdc83cc05b2"


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def fail(m):
    print("REFUSED: %s" % m)
    sys.exit(1)


def main():
    print("== S283_JOB_PULSE_EMPTY -- job_pulse.py v1.1 -> v1.2 ==")
    if not os.path.isfile(SRC) or md5(SRC) != EXPECT_NEW:
        fail("the kit's own job_pulse.py is missing or not %s -- the kit is damaged" % EXPECT_NEW)
    if not os.path.isfile(DEST):
        fail("%s is not there" % DEST)
    cur = md5(DEST)
    if cur == EXPECT_NEW:
        print("Already installed -- v1.2 is in place. Nothing changed.")
        return 0
    if cur != EXPECT_OLD:
        fail("job_pulse.py is %s, expected v1.1 %s. It has moved on since this kit "
             "was built; rebuild against the file as it is now." % (cur, EXPECT_OLD))

    r = subprocess.run([PY, "-B", SRC, "--selftest"], capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(r.stdout[-2500:])
        fail("v1.2 did not pass its own selftest on this machine; nothing was changed")
    print("selftest : passed on this box (%d checks)" % r.stdout.count("ok   "))

    bak = "%s.bak_S283_%s" % (DEST, EXPECT_OLD[:8])
    shutil.copy2(DEST, bak)
    if md5(bak) != EXPECT_OLD:
        fail("the backup did not copy exactly; nothing was changed")
    print("backup   : %s" % bak)
    shutil.copy2(SRC, DEST)
    os.chmod(DEST, 0o755)
    print("job_pulse: %s -> %s" % (cur, md5(DEST)))

    r = subprocess.run([PY, "-B", DEST, "--print"], capture_output=True, text=True, timeout=300)
    if r.returncode != 0 or md5(DEST) != EXPECT_NEW:
        print(r.stdout[-1500:]); print(r.stderr[-1500:])
        shutil.copy2(bak, DEST)
        print("restored : %s" % md5(DEST))
        fail("the new version would not run; the old one is back")
    sys.stdout.write("\n" + r.stdout[-6500:] + "\n")
    print("DONE. Same hourly cron line, unchanged.")
    print("To undo:  \\cp %s %s" % (bak, DEST))
    return 0


if __name__ == "__main__":
    sys.exit(main())
