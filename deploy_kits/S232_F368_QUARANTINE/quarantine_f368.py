#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quarantine_f368.py  --  S232  --  F-368: stale secrets and stale code in live folders.

WHAT IS WRONG
    /root/wa/ holds SIX old copies of the secrets file, each carrying
    MYOP_AUTH_TOKEN and MYOP_LOGS_TOKEN -- and every OTHER secret in that file,
    including ones that have never been rotated. It also holds three stale code
    copies. Those are the files a future sweep finds and BELIEVES.

WHY NOW AND NOT AFTER THE ROTATION
    The record said "not to be touched mid-rotation". The rotation has not
    started. Doing this BEFORE it shrinks the blast radius: six fewer files
    holding the old token on the day it is replaced. Mid-rotation is the one
    moment this must not happen.

WHAT IT DOES, AND EVERY LIMIT ON IT
    * It MOVES. It never deletes. Everything lands in one dated folder, mode 700.
    * It works from an EXPLICIT LIST of nine filenames. No globs, no patterns,
      no "*.bak" -- a sweep that matches by shape is how a live file gets moved
      by accident.
    * It REFUSES to run if /root/wa/.env is missing: that would mean something
      is already wrong and this is not the tool for it.
    * It NEVER touches /root/wa/.env, and never the _backup_S231_* copies, which
      the S231 close recorded as CURRENT.
    * It prints every path before it moves anything, and prints the one-line
      undo at the end.
    * It PRINTS NO FILE CONTENT. Ever. These are secrets; the whole point is to
      handle them without reading them.

RUN (VPS, root) -- --check changes nothing:
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S232_F368_QUARANTINE/quarantine_f368.py --check
    /root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S232_F368_QUARANTINE/quarantine_f368.py --apply
"""

import datetime
import os
import shutil
import sys

WA = "/root/wa"
LIVE_ENV = os.path.join(WA, ".env")

# The nine, named one by one from the F-368 entry. Nothing is matched by pattern.
STALE_SECRETS = [
    ".env.bak_20260707_162509",
    ".env.bak.20260708-102630",
    ".env.preswap.102831",
    ".env.bak_s126_20260708_212316",
    ".env.bak_s127_pre_rotation_20260708_232229",
    ".env.bak_s127_step2_20260709_085801",
]
STALE_CODE = [
    "waba.py.bak.20260814_172324",
    "portal_console.py.bak-20260812-0729",
    os.path.join("wa_logs", "portal_console.py.new"),
]

STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
DEST = "/root/_quarantine_S232_F368_%s" % STAMP


def say(m=""):
    print(m, flush=True)


def main():
    mode = "--check"
    for a in sys.argv[1:]:
        if a in ("--check", "--apply"):
            mode = a

    say("=" * 68)
    say("F-368 quarantine  --  mode %s  --  %s" % (mode, STAMP))
    say("=" * 68)

    say("\n[1] the live secrets file must be there")
    if not os.path.isfile(LIVE_ENV):
        say("    REFUSING -- %s not found. Something else is wrong; fix that first." % LIVE_ENV)
        return 2
    say("    %s present -- and it is NEVER touched by this script" % LIVE_ENV)

    say("\n[2] what is on the list, and what is actually there")
    found, missing = [], []
    for rel in STALE_SECRETS + STALE_CODE:
        p = os.path.join(WA, rel)
        (found if os.path.isfile(p) else missing).append(rel)
    for rel in found:
        p = os.path.join(WA, rel)
        kind = "SECRETS" if rel in STALE_SECRETS else "code   "
        say("    %s  %-46s %8d bytes" % (kind, rel, os.path.getsize(p)))
    for rel in missing:
        say("    gone already                                  %s" % rel)
    say("\n    %d of %d present" % (len(found), len(STALE_SECRETS) + len(STALE_CODE)))

    if not found:
        say("\n    nothing to do -- all nine are already gone.")
        return 0

    if mode == "--check":
        say("\n[3] --check only. NOTHING WAS MOVED.")
        say("    Re-run with --apply to move the %d file(s) above into" % len(found))
        say("    %s" % DEST)
        return 0

    say("\n[3] moving into %s (mode 700)" % DEST)
    os.makedirs(DEST, exist_ok=True)
    os.chmod(DEST, 0o700)
    moved = []
    for rel in found:
        src = os.path.join(WA, rel)
        dst = os.path.join(DEST, rel.replace(os.sep, "__"))
        shutil.move(src, dst)
        os.chmod(dst, 0o600)
        moved.append((rel, dst))
        say("    moved  %s" % rel)

    say("\n[4] checking")
    still = [r for r, _ in moved if os.path.exists(os.path.join(WA, r))]
    if still:
        say("    PROBLEM -- these did not move: %s" % ", ".join(still))
        return 1
    if not os.path.isfile(LIVE_ENV):
        say("    PROBLEM -- the live .env is gone. RESTORE IT NOW from %s" % DEST)
        return 1
    say("    all %d moved; /root/wa/.env still present and untouched" % len(moved))

    say("\n" + "=" * 68)
    say("DONE. %d file(s) out of the live folder and into one 700 folder." % len(moved))
    say("They are NOT deleted. After the WABA rotation, delete that folder.")
    say("=" * 68)
    say("UNDO (one line):")
    say("  for f in %s/*; do n=$(basename $f); mv $f /root/wa/${n//__//}; done" % DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
