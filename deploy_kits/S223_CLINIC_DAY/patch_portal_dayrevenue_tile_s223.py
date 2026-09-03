#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_dayrevenue_tile_s223.py -- S223: the Day Revenue tile.

THE OWNER: "then add the docterz tile, which will show them its stage 1 data" and, on who:
"the docterz - view for shavez, shivani and alisha also needed, with a pdf print feature also"
-- alongside himself and Dr Bhawna.

ONE new tile -> /finance/clinic/day. Named for what it GIVES you, not for where it comes from;
Docterz is in the description. roles ["doctor"], granted by name in tile_grants.json to
shavez, shivani, alisha and bhawna -- the same fail-closed shape as the other money tiles: if
the grants file is ever lost, staff lose it and the owner keeps it.

CHAINED: built on S223_CORRECTIONS_TILE (fbd4029b3dec43cb9586950b80b15fc1). Refuses on anything
else. Install that first (F-298).

The tile is DISPLAY. The page's own gate -- require("maker","checker", unit="clinic") -- is what
decides who may actually open it, and the two lists are the same five people by construction:
everyone granted the tile already holds a clinic role, and nobody else is granted the tile.

Run on the box:  /root/wa/venv/bin/python3 -B /root/portal/patch_portal_dayrevenue_tile_s223.py
Offline:         PORTAL_PATH=./portal.py python3 -B patch_portal_dayrevenue_tile_s223.py
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

PORTAL = os.environ.get("PORTAL_PATH", "/root/portal/portal.py")
FROM_MD5 = "fbd4029b3dec43cb9586950b80b15fc1"
MARK = '"name": "Day Revenue"'

A_OLD = '''     "url": "/finance/darpan/corrections",
     "roles": ["doctor"]},'''
A_NEW = '''     "url": "/finance/darpan/corrections",
     "roles": ["doctor"]},
    {"icon": "\\U0001F4C8", "name": "Day Revenue",
     # S223 NEW. The clinic's daily takings, read from the Docterz Day Revenue
     # sheet that already reaches Drive every day. Read-only, and every figure on
     # it is computed from the itemised lines, never from the sheet's own summary
     # block (D367). Print / Save as PDF is on the page.
     "desc": "Clinic takings by day \\u2014 from Docterz",
     "live": True,
     "url": "/finance/clinic/day",
     "roles": ["doctor"]},'''

B_OLD = '''"Corrections": "Money & Accounts",'''
B_NEW = '''"Corrections": "Money & Accounts", "Day Revenue": "Money & Accounts",'''


def main():
    if not os.path.exists(PORTAL):
        sys.exit("REFUSING: %s not found" % PORTAL)
    src = io.open(PORTAL, encoding="utf-8").read()
    cur = hashlib.md5(io.open(PORTAL, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != FROM_MD5:
        sys.exit("REFUSING: %s is %s, expected %s. Install S223_CORRECTIONS_TILE first -- this "
                 "kit is chained on it (F-298)." % (PORTAL, cur, FROM_MD5))
    for label, old in (("Corrections tile", A_OLD), ("group map", B_OLD)):
        n = src.count(old)
        if n != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1" % (label, n))
    new = src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1)
    bak = PORTAL + ".bak_S223_dayrev_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(PORTAL, bak)
    io.open(PORTAL, "w", encoding="utf-8", newline="\n").write(new)
    try:
        import py_compile
        import tempfile
        _fd, _cf = tempfile.mkstemp(suffix=".pyc")
        os.close(_fd)
        try:
            py_compile.compile(PORTAL, cfile=_cf, doraise=True)
        finally:
            try:
                os.remove(_cf)
            except OSError:
                pass
    except Exception as e:
        shutil.copy2(bak, PORTAL)
        sys.exit("REFUSING: compile failed (%s); restored %s" % (e, bak))
    got = hashlib.md5(io.open(PORTAL, "rb").read()).hexdigest()
    print("current pin  %s" % FROM_MD5)
    print("patched  %s" % PORTAL)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % got)
    print("next     put tile_grants.json beside it, then restart clinic-portal")


if __name__ == "__main__":
    main()
