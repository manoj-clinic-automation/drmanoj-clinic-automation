#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_purchase_tile_s224.py -- S224: the Marg Purchases tile.

ONE new tile -> /finance/purchase/page/hub, immediately after Stock Check in Money &
Accounts, because the two are read together: what Marg says came in, and what the shelf
says is there. roles ["doctor"] in code; granted by name in tile_grants.json v6 to amir,
shavez, darpan, alisha and shivani -- so a lost grants file leaves it with the owner alone
(fail closed for staff, never locked out for the doctor), exactly as the S223 tiles do.
The PAGE's own gate is the medical unit_role, which still decides what each of them may do.

THE PIN. portal.py on the box is ahead of the repo (the S223 chain), so the expected md5
is passed in, not hard-coded. Anchors are exact and each must match exactly once.

Run on the box:
    md5sum /root/portal/portal.py
    /root/wa/venv/bin/python3 -B /root/portal/patch_portal_purchase_tile_s224.py <that md5>
Offline:
    PORTAL_PATH=./portal.py python3 -B patch_portal_purchase_tile_s224.py <md5 of that copy>
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

PORTAL = os.environ.get("PORTAL_PATH", "/root/portal/portal.py")
MARK = '"name": "Marg Purchases"'

A_OLD = '''     "url": "/finance/stock/page/count",
     "roles": ["doctor"]},'''
A_NEW = '''     "url": "/finance/stock/page/count",
     "roles": ["doctor"]},
    {"icon": "\\U0001F4E6", "name": "Marg Purchases",
     # S224 NEW. Marg's purchase bills, pushed nightly from manojz: each bill marked
     # Correct or Wrong, the month FINALISED by the doctor, scans paired with bills,
     # and the reorder plan. Granted by name in tile_grants.json v6.
     "desc": "Purchases \\u00b7 scans \\u00b7 orders \\u00b7 stock check",
     "live": True,
     "url": "/finance/purchase/page/hub",
     "roles": ["doctor"]},'''

B_OLD = '''    "Daily Register": "Money & Accounts",'''
B_NEW = '''    "Daily Register": "Money & Accounts", "Marg Purchases": "Money & Accounts",'''


def main():
    if len(sys.argv) < 2 or len(sys.argv[1]) != 32:
        sys.exit("USAGE: patch_portal_purchase_tile_s224.py <md5 of the portal.py you are patching>\n"
                 "       read it with:  md5sum /root/portal/portal.py")
    from_md5 = sys.argv[1].lower()
    if not os.path.exists(PORTAL):
        sys.exit("REFUSING: %s not found" % PORTAL)
    src = io.open(PORTAL, encoding="utf-8").read()
    cur = hashlib.md5(io.open(PORTAL, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != from_md5:
        sys.exit("REFUSING: %s is %s, you said %s. Read the box's pin again." % (PORTAL, cur, from_md5))
    for label, old in (("Stock Check tile", A_OLD), ("group map (S223 Daily Register row)", B_OLD)):
        if src.count(old) != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1" % (label, src.count(old)))
    new = src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1)
    bak = PORTAL + ".bak_S224_purchtile_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
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
    print("current pin  %s" % from_md5)
    print("patched  %s" % PORTAL)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % got)
    print("next     put tile_grants.json (v6) beside it, then restart clinic-portal")


if __name__ == "__main__":
    main()
