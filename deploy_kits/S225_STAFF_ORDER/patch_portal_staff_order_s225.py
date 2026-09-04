#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_staff_order_s225.py -- S225: the "Order Medicines" tile.

ONE new tile -> /finance/purchase/page/staff, immediately after Marg Purchases in Money &
Accounts. It is the staff face of the same app: Item / Stock now / Order qty, one tap to
WhatsApp, Call, Print A4 -- and none of the doctor's rates, values or reasons. roles ["doctor"]
in code; granted by name in tile_grants.json v8 to amir, shavez, darpan, alisha and shivani --
the same five who hold Marg Purchases -- so a lost grants file leaves it with the owner alone
(fail closed for staff, never locked out for the doctor), exactly as the S223/S224 tiles do.
The PAGE's own gate is the medical unit_role, unchanged.

THE PIN. portal.py on the box is ahead of the repo (the S223/S224 chain), so the expected md5 is
passed in, not hard-coded. Anchors are exact and each must match exactly once.

Run on the box:
    md5sum /root/portal/portal.py
    /root/wa/venv/bin/python3 -B /root/portal/patch_portal_staff_order_s225.py <that md5>
Offline:
    PORTAL_PATH=./portal.py python3 -B patch_portal_staff_order_s225.py <md5 of that copy>
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

PORTAL = os.environ.get("PORTAL_PATH", "/root/portal/portal.py")
MARK = '"name": "Order Medicines"'

A_OLD = '''     "url": "/finance/purchase/page/hub",
     "roles": ["doctor"]},'''
A_NEW = '''     "url": "/finance/purchase/page/hub",
     "roles": ["doctor"]},
    {"icon": "\\U0001F6D2", "name": "Order Medicines",
     # S225 NEW. The staff face of Marg Purchases, as the owner dictated on 04-Sep: item,
     # stock now and order quantity only; one tap sends the order to the stockist on
     # WhatsApp; Call; Print A4. Granted by name in tile_grants.json v8.
     "desc": "Item \\u00b7 stock \\u00b7 quantity \\u2014 send to the stockist on WhatsApp",
     "live": True,
     "url": "/finance/purchase/page/staff",
     "roles": ["doctor"]},'''

B_OLD = '''"Marg Purchases": "Money & Accounts",'''
B_NEW = '''"Marg Purchases": "Money & Accounts", "Order Medicines": "Money & Accounts",'''

PAIRS = (("Marg Purchases tile (url+roles lines)", A_OLD, A_NEW),
         ("group map (Marg Purchases row)", B_OLD, B_NEW))


def main():
    if len(sys.argv) < 2 or len(sys.argv[1]) != 32:
        sys.exit("USAGE: patch_portal_staff_order_s225.py <md5 of the portal.py you are patching>\n"
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
    for label, old, _new in PAIRS:
        if src.count(old) != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1" % (label, src.count(old)))
    new = src
    for _label, old, rep in PAIRS:
        new = new.replace(old, rep, 1)
    bak = PORTAL + ".bak_S225_ordertile_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
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
    print("next     put tile_grants.json (v8) beside it, then restart clinic-portal")


if __name__ == "__main__":
    main()
