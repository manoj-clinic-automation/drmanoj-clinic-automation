#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_register_tile_s223.py -- S223: the Daily Register tile.

THE OWNER: "all goes thru pwa, clinic section - subsection, filled forms dissapear, shavez,
alisha shivani, and me and dr bhawna"

ONE new tile -> /finance/clinic/register, sitting immediately beside Day Revenue in
Money & Accounts, because the two are read together and a person looking for one is looking for
the other. roles ["doctor"], granted by name to shavez, alisha, shivani, bhawna and manoj -- his
list, and the same five who already hold the clinic desk, so the tile and the page's own gate
admit exactly the same people by construction.

Tapping it does NOT open a list: it opens the next day that has not been filled in, because that
is what the person opening it came to do. A day that has been filled disappears from the list --
it is a to-do, not an archive.

CHAINED on S223_CLINIC_DAY's tile kit (e2f907527113588e7ce8287d678525a1). Refuses on anything else.

Run on the box:  /root/wa/venv/bin/python3 -B /root/portal/patch_portal_register_tile_s223.py
Offline:         PORTAL_PATH=./portal.py python3 -B patch_portal_register_tile_s223.py
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

PORTAL = os.environ.get("PORTAL_PATH", "/root/portal/portal.py")
FROM_MD5 = "e2f907527113588e7ce8287d678525a1"
MARK = '"name": "Daily Register"'

A_OLD = '''     "url": "/finance/clinic/day",
     "roles": ["doctor"]},'''
A_NEW = '''     "url": "/finance/clinic/day",
     "roles": ["doctor"]},
    {"icon": "\\U0001F4D2", "name": "Daily Register",
     # S223 NEW. What the counter's own register says for the day -- nine boxes, no
     # patient, no bill. It is the THIRD record beside Docterz and the bank, and it is
     # what turns "these two disagree" into "these two agree, so look at the third".
     "desc": "The counter's day totals \\u2014 cash, UPI, card",
     "live": True,
     "url": "/finance/clinic/register",
     "roles": ["doctor"]},'''

B_OLD = '''"Corrections": "Money & Accounts", "Day Revenue": "Money & Accounts",'''
B_NEW = ('''"Corrections": "Money & Accounts", "Day Revenue": "Money & Accounts",
    "Daily Register": "Money & Accounts",''')


def main():
    if not os.path.exists(PORTAL):
        sys.exit("REFUSING: %s not found" % PORTAL)
    src = io.open(PORTAL, encoding="utf-8").read()
    cur = hashlib.md5(io.open(PORTAL, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != FROM_MD5:
        sys.exit("REFUSING: %s is %s, expected %s. Install S223_CLINIC_DAY first (F-298)."
                 % (PORTAL, cur, FROM_MD5))
    for label, old in (("Day Revenue tile", A_OLD), ("group map", B_OLD)):
        if src.count(old) != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1"
                     % (label, src.count(old)))
    new = src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1)
    bak = PORTAL + ".bak_S223_regtile_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
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
