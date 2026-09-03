#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_corrections_tile_s223.py -- S223: the Corrections tile, for the owner.

THE OWNER: "add corrections for me"

ONE new tile -> /finance/darpan/corrections, roles ["doctor"], nobody granted by name.
That page's list belongs to Darpan and Amir (viewer, S221); its BOTTOM HALF is the owner's --
the ledger check for one date and the owner transfer, which S222 taught the page to hide from
anyone the server would refuse. This tile is the owner's own door to it. It was reachable only
by typing the address until now.

CHAINED: this kit is built on the S223_LAUNCH_TILES result (2cfd2f62a1c46671f0facf04c1c9e774)
and refuses on anything else. Install S223_LAUNCH_TILES first. (F-298: a kit chained on another
kit's output names its predecessor in its own INSTALL, and the order is stated beside both.)

This changes what the owner is SHOWN and nothing else. Every server-side gate on that page and
its APIs is untouched: `_require("checker")` still decides who may act, exactly as before.

Target: /root/portal/portal.py
Run on the box:  /root/wa/venv/bin/python3 -B /root/portal/patch_portal_corrections_tile_s223.py
Offline:         PORTAL_PATH=./portal.py python3 -B patch_portal_corrections_tile_s223.py
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

PORTAL = os.environ.get("PORTAL_PATH", "/root/portal/portal.py")
FROM_MD5 = "2cfd2f62a1c46671f0facf04c1c9e774"          # the S223_LAUNCH_TILES result
MARK = '"name": "Corrections"'

A_OLD = '''     "url": "/finance/stock/page/count",
     "roles": ["doctor"]},'''
A_NEW = '''     "url": "/finance/stock/page/count",
     "roles": ["doctor"]},
    {"icon": "\\U0001F58A\\uFE0F", "name": "Corrections",
     # S223: the owner asked for his own door to the corrections desk. The LIST on
     # that page is Darpan's and Amir's (viewer, S221); the bottom half -- ledger
     # check for one date, and the owner transfer -- is his, and S222 taught the
     # page to hide it from anyone the server would refuse. Until now he reached it
     # only by typing the address.
     "desc": "Ledger check & transfer \\u2014 bill corrections desk",
     "live": True,
     "url": "/finance/darpan/corrections",
     "roles": ["doctor"]},'''

B_OLD = '''"Vaapsi Desk": "Money & Accounts", "Stock Check": "Money & Accounts",'''
B_NEW = '''"Vaapsi Desk": "Money & Accounts", "Stock Check": "Money & Accounts",
    "Corrections": "Money & Accounts",'''


def main():
    if not os.path.exists(PORTAL):
        sys.exit("REFUSING: %s not found" % PORTAL)
    src = io.open(PORTAL, encoding="utf-8").read()
    cur = hashlib.md5(io.open(PORTAL, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != FROM_MD5:
        sys.exit("REFUSING: %s is %s, expected %s. Install S223_LAUNCH_TILES first -- this kit is "
                 "chained on it (F-298)." % (PORTAL, cur, FROM_MD5))
    for label, old in (("Stock Check tile", A_OLD), ("group map", B_OLD)):
        n = src.count(old)
        if n != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1" % (label, n))
    new = src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1)
    bak = PORTAL + ".bak_S223_corr_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
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
    print("next     systemctl restart clinic-portal")


if __name__ == "__main__":
    main()
