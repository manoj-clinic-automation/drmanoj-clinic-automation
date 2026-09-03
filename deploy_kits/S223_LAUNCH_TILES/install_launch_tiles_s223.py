#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_launch_tiles_s223.py -- S223: launch the staff app to everybody.

THE OWNER, at the S223 open: "Attendance and staff ledger -- we can leave provision to add later.
Right now, if we launch the PWA app for everybody, the operational layer will be ready. Only their
personal part will not be visible... Then I would like you to launch the PWA app also."

That is the ruling the S222 kit asked for and did not take. `USER_TILE_MASK["darpan"]` hid
Attendance, Staff Register and Scan Purchase from the one person who uses this system most, on a
reason recorded in S179 -- "darpan is role=staff, which is shared" -- that died the day he got his
own login and his own phone.

WHAT THIS DOES:  replaces /root/portal/tile_grants.json with the same file minus darpan's mask.
WHAT IT DOES NOT DO:  touch portal.py, touch any other user, restart anything. The portal reads
this file per request, so the change is live the moment the file lands.

GATED: refuses unless the file on the box is byte-identical to the one S222 installed.
PROVEN OFFLINE: walk_s223.py ran the REAL _visible_sections() out of a byte-exact reproduction of
the live portal.py (d15acef3fcb0237563475968c2eec921, rebuilt from S204_VPS_LIVE through the S218
and three S222 patchers) over 48 user x role x PC combinations. Result: darpan gains exactly
{Attendance, Staff Register, Scan Purchase}, loses nothing, and NOT ONE other combination moves.

Run on the box:  /root/wa/venv/bin/python3 -B /root/portal/install_launch_tiles_s223.py
"""
import datetime as dt, hashlib, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.environ.get("GRANTS_PATH", "/root/portal/tile_grants.json")
NEW = os.path.join(HERE, "tile_grants.json")
FROM_MD5 = "2150b3e12b8d7048be5415c346709f8b"   # what S222 installed
TO_MD5   = "bfdf40dd4bde510010ae358e5c432bcb"   # what this kit installs


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    if not os.path.exists(NEW):
        sys.exit("REFUSING: tile_grants.json not found beside this script")
    if md5(NEW) != TO_MD5:
        sys.exit("REFUSING: the kit's own tile_grants.json is not %s" % TO_MD5)
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s does not exist -- the S222 grants kit is not installed" % TARGET)
    cur = md5(TARGET)
    if cur == TO_MD5:
        print("ALREADY DONE  %s is already %s -- nothing to do" % (TARGET, TO_MD5))
        return
    if cur != FROM_MD5:
        sys.exit("REFUSING: %s is %s, expected %s. Something else changed this file; "
                 "reconcile before patching (D172/D188)." % (TARGET, cur, FROM_MD5))
    bak = TARGET + ".bak_S223_launch_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    shutil.copy2(NEW, TARGET)
    got = md5(TARGET)
    if got != TO_MD5:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: wrote %s, restored the backup" % got)
    print("current pin  %s" % FROM_MD5)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % got)
    print("next     nothing. The portal reads this file per request -- no restart, no downtime.")


if __name__ == "__main__":
    main()
