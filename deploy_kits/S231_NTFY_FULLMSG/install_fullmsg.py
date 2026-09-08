#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_fullmsg.py  --  S231 : the WhatsApp push carries the FULL message text.

Owner's ruling, 08-Sep-2026: "full message - as most are small messages already".
Until now the push carried the patient's NAME only, and he still had to open the
callback tracker, wait for a reload and go to the WhatsApp section to read it.

WHAT IT DOES
    /root/deploy/repo/notifier/notifier_wa.py  ->  /root/wa/notifier_wa.py
    then restarts wa-notifier.service and PROVES it came back working.

WHAT IT REFUSES TO DO
    It will not overwrite a live file that is not byte-identical to what the
    repository held BEFORE this change. If the live copy has drifted, someone
    edited it outside the repo and copying over it would destroy that work
    silently. It stops and prints both hashes instead.

PROOF, not assumption. After the restart it checks three things:
    1. the unit is active
    2. the running process still carries NTFY_TOPIC
    3. the log says the message column was FOUND
Point 3 is the one that matters: if the column is missing the code falls back
to name-only pushes and nothing appears broken. That silent half-success is
exactly what this checks for.

RUN (VPS, root):
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S231_NTFY_FULLMSG/install_fullmsg.py --check
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S231_NTFY_FULLMSG/install_fullmsg.py --install
"""

import os
import sys
import time
import shutil
import hashlib
import datetime
import subprocess

SRC     = "/root/deploy/repo/notifier/notifier_wa.py"
LIVE    = "/root/wa/notifier_wa.py"
SERVICE = "wa-notifier.service"
STAMP   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP  = "/root/_backup_S231_fullmsg_%s" % STAMP

EXPECTED_OLD = "feeea7efca7bbe3c02baa4ffd120de27"   # repo copy before this change
EXPECTED_NEW = "08219ae8fe995a8c85cc93f9a67ab16f"   # repo copy after it


def say(m=""):
    print(m, flush=True)


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def proc_has(key):
    r = subprocess.run(["systemctl", "show", SERVICE, "-p", "MainPID", "--value"],
                       capture_output=True, text=True, timeout=30)
    pid = r.stdout.strip()
    if not pid or pid == "0":
        return False, "no MainPID"
    try:
        raw = open("/proc/%s/environ" % pid, "rb").read().decode("utf-8", "ignore")
    except Exception as e:
        return False, str(e)
    return any(i.startswith(key + "=") for i in raw.split("\0")), "pid %s" % pid


def main():
    mode = "--check"
    for a in sys.argv[1:]:
        if a in ("--check", "--install"):
            mode = a

    say("=" * 72)
    say("S231 full-message push  --  mode %s  --  %s" % (mode, STAMP))
    say("=" * 72)

    say("\n[1] the two files")
    for p in (SRC, LIVE):
        if not os.path.exists(p):
            say("    REFUSING -- %s not found" % p)
            return 2
    src_md5, live_md5 = md5(SRC), md5(LIVE)
    say("    repo copy : %s  %s" % (src_md5, SRC))
    say("    live copy : %s  %s" % (live_md5, LIVE))

    if src_md5 != EXPECTED_NEW:
        say("\n    REFUSING -- the repo copy is not the version this kit was built")
        say("    for. Expected %s. Publish and pull again." % EXPECTED_NEW)
        return 2
    if live_md5 == EXPECTED_NEW:
        say("\n    already installed -- nothing to do")
        return 0
    if live_md5 != EXPECTED_OLD:
        say("\n    REFUSING -- the LIVE file has drifted. It is neither the old")
        say("    version (%s) nor the new one." % EXPECTED_OLD)
        say("    Someone edited it outside the repository. Copying over it would")
        say("    destroy that change silently. Tell Claude both hashes above.")
        return 2
    say("    live matches the pre-change repo version exactly -- safe to replace")

    if mode == "--check":
        say("\n[2] --check only. NOTHING WAS CHANGED.")
        return 0

    say("\n[2] backing up")
    os.makedirs(BACKUP, exist_ok=True)
    shutil.copy2(LIVE, os.path.join(BACKUP, "notifier_wa.py.bak"))
    say("    %s" % BACKUP)

    say("\n[3] installing")
    shutil.copy2(SRC, LIVE)
    if md5(LIVE) != EXPECTED_NEW:
        say("    REFUSING -- copy did not land. Restore:")
        say("      \\cp %s/notifier_wa.py.bak %s" % (BACKUP, LIVE))
        return 2
    try:
        import py_compile
        py_compile.compile(LIVE, cfile="/tmp/_fullmsg_check.pyc", doraise=True)
        os.remove("/tmp/_fullmsg_check.pyc")
    except Exception as e:
        say("    REFUSING -- installed file does not compile: %s" % e)
        shutil.copy2(os.path.join(BACKUP, "notifier_wa.py.bak"), LIVE)
        say("    rolled back.")
        return 2
    say("    copied and compiles")

    def rollback(why):
        say("    REFUSING -- %s" % why)
        shutil.copy2(os.path.join(BACKUP, "notifier_wa.py.bak"), LIVE)
        subprocess.run(["systemctl", "restart", SERVICE], capture_output=True, timeout=90)
        time.sleep(3)
        r = subprocess.run(["systemctl", "is-active", SERVICE],
                           capture_output=True, text=True, timeout=30)
        say("    rolled back; %s is now %s" % (SERVICE, r.stdout.strip()))

    say("\n[4] restart, and prove it")
    subprocess.run(["systemctl", "restart", SERVICE], capture_output=True, timeout=90)
    time.sleep(5)
    r = subprocess.run(["systemctl", "is-active", SERVICE],
                       capture_output=True, text=True, timeout=30)
    state = r.stdout.strip()
    say("    is-active            : %s" % state)
    if state != "active":
        rollback("%s did not come back active" % SERVICE)
        return 2

    ok, where = proc_has("NTFY_TOPIC")
    say("    NTFY_TOPIC in process: %s (%s)" % (ok, where))
    if not ok:
        rollback("the running process has no NTFY_TOPIC")
        return 2

    say("\n[5] did it find the message column?")
    found = None
    for attempt in range(6):
        j = subprocess.run(["journalctl", "-u", SERVICE, "-n", "60", "--no-pager"],
                           capture_output=True, text=True, timeout=45)
        out = j.stdout
        if "message column found at index" in out:
            found = True
            for line in out.splitlines():
                if "message column" in line:
                    say("    %s" % line.strip()[-90:])
            break
        if "message column NOT FOUND" in out:
            found = False
            for line in out.splitlines():
                if "message column" in line:
                    say("    %s" % line.strip()[-90:])
            break
        time.sleep(5)

    say("\n" + "=" * 72)
    if found is True:
        say("DONE. The next inbound WhatsApp will arrive with its text.")
    elif found is False:
        say("INSTALLED, BUT: the WA_Inbox sheet has no column this recognises as")
        say("the message. It is running SAFELY on the old name-only behaviour.")
        say("Nothing is broken and nothing needs undoing -- but the text will not")
        say("appear until the column name is known. Tell Claude the WA_Inbox")
        say("column headings and it will be a one-word fix.")
    else:
        say("INSTALLED, and running. The log did not show either message-column")
        say("line within 30s -- it prints on startup, so check again shortly:")
        say("  journalctl -u %s -n 40 --no-pager | grep -i 'message column'" % SERVICE)
    say("=" * 72)
    say("Undo:")
    say("  \\cp %s/notifier_wa.py.bak %s" % (BACKUP, LIVE))
    say("  systemctl restart %s" % SERVICE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
