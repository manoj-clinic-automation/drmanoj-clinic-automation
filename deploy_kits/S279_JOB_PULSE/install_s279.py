#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_s279.py -- S279_JOB_PULSE

Puts job_pulse.py on the box and gives it one hourly cron line.

WHAT IT TOUCHES
    /root/finance/job_pulse.py   -- new file, did not exist before
    root's crontab               -- ONE line appended, nothing else altered
    nothing else. No existing job is edited. No database is opened.

SAFETY
    * the crontab is backed up to /root/finance/crontab.bak_S279_<stamp> BEFORE
      anything is written, and the backup is read back and compared before the
      new crontab is installed.
    * the new crontab is checked line for line against the old one: it must be
      the old crontab plus exactly one line, or nothing is installed.
    * already installed -> says so and changes nothing.
    * if the crontab read-back does not match what was written, the backup is
      restored and the script says so.
    * job_pulse.py itself is read-only on the rest of the system.
"""
import datetime as dt
import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "job_pulse.py")
DEST = "/root/finance/job_pulse.py"
PY = "/root/wa/venv/bin/python3"
LINE = ("17 * * * * %s -B %s >> /root/finance/job_pulse.log 2>&1"
        "  # S279_JOB_PULSE" % (PY, DEST))
MARK = "S279_JOB_PULSE"


def md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def crontab_read():
    r = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError("crontab -l failed: %s" % (r.stderr or "").strip())
    return r.stdout


def crontab_write(text):
    r = subprocess.run(["crontab", "-"], input=text, capture_output=True,
                       text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError("crontab - failed: %s" % (r.stderr or "").strip())


def fail(msg):
    print("REFUSED: %s" % msg)
    sys.exit(1)


def main():
    if not os.path.isfile(SRC):
        fail("job_pulse.py is not beside this installer")
    if not os.path.isdir(os.path.dirname(DEST)):
        fail("%s is not there" % os.path.dirname(DEST))
    if not os.path.exists(PY):
        fail("%s is not there" % PY)

    # the script itself must pass its own tests on THIS box before it is installed
    r = subprocess.run([PY, SRC, "--selftest"], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        fail("job_pulse.py did not pass its own selftest on this machine")
    print("selftest : passed on this box")

    before = crontab_read()
    installed_file = os.path.exists(DEST) and md5(DEST) == md5(SRC)
    installed_cron = MARK in before
    if installed_file and installed_cron:
        print("Already installed -- the file and the cron line are both there. "
              "Nothing changed.")
        return run_once()

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    # derived from DEST so the whole installer can be walked in a sandbox
    bak = os.path.join(os.path.dirname(DEST), "crontab.bak_S279_%s" % stamp)
    with open(bak, "w", encoding="utf-8") as fh:
        fh.write(before)
    with open(bak, "r", encoding="utf-8") as fh:
        if fh.read() != before:
            fail("the crontab backup did not read back identically")
    print("crontab backed up: %s (%d lines)" % (bak, len(before.splitlines())))

    if not installed_file:
        shutil.copy2(SRC, DEST)
        os.chmod(DEST, 0o755)
        print("installed : %s  (%s)" % (DEST, md5(DEST)))

    if not installed_cron:
        after = before if before.endswith("\n") or not before else before + "\n"
        after = after + LINE + "\n"
        old_lines, new_lines = before.splitlines(), after.splitlines()
        added = [x for x in new_lines if x not in old_lines]
        if len(new_lines) != len(old_lines) + 1 or len(added) != 1:
            fail("the new crontab is not the old one plus exactly one line")
        crontab_write(after)
        back = crontab_read()
        if MARK not in back or len(back.splitlines()) != len(old_lines) + 1:
            print("the crontab did not read back as expected -- restoring")
            crontab_write(before)
            fail("crontab restored from %s; nothing is scheduled" % bak)
        print("cron line : added, and read back from the crontab itself")
        print("            %s" % LINE)

    return run_once()


def run_once():
    print("")
    print("first run --------------------------------------------------------")
    r = subprocess.run([PY, "-B", DEST, "--print"], capture_output=True,
                       text=True, timeout=300)
    sys.stdout.write(r.stdout[-6000:])
    if r.stderr.strip():
        sys.stdout.write("\n" + r.stderr[-1500:])
    print("------------------------------------------------------------------")
    print("")
    print("DONE. It runs at 17 minutes past every hour and writes:")
    print("  /root/finance/JOB_PULSE_LATEST.txt")
    print("  /root/finance/job_pulse.json")
    print("")
    print("To undo:  crontab -l | grep -v %s | crontab - && rm -f %s" % (MARK, DEST))
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
