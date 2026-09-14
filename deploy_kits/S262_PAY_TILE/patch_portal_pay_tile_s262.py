#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_pay_tile_s262.py -- S262: the Vendor payments tile.

ONE new tile -> /finance/purchase/page/pay, immediately after Marg Purchases in
Money & Accounts, because the two are read together: what came in, and what is
owed for it. roles ["doctor"] in code; granted BY NAME in tile_grants.json v17 to
shavez alone -- so a lost grants file leaves it with the owner (fail closed for
staff, never locked out for the doctor), exactly as every tile since S223.

The PAGE's own gate is unchanged and still decides what each of them may do:
purchase_app's medical unit_role. A viewer sees the sheet read-only -- no carry
forward typed, no verification run, no lock. That is Shavez's face of it by
construction, not by a second page.

Two anchors, each must match exactly once. Not one existing line is edited:
the tile block is inserted after Marg Purchases, and the group map gains one
name at the end of the row that already carries the other two purchase tiles.

Run:
    PORTAL_PATH=/root/portal/portal.py python3 -B patch_portal_pay_tile_s262.py --from <md5>
"""
import argparse
import hashlib
import io
import os
import shutil
import sys

PORTAL = os.environ.get("PORTAL_PATH", "/root/portal/portal.py")
MARK = '"name": "Vendor payments"'

A_OLD = '''     "url": "/finance/purchase/page/hub",
     "roles": ["doctor"]},'''
A_NEW = '''     "url": "/finance/purchase/page/hub",
     "roles": ["doctor"]},
    {"icon": "\\U0001F4B8", "name": "Vendor payments",
     # S262 NEW. The month's payment sheet, prepared inside the system: every vendor
     # with its two fortnights, what is carried in and what is payable; NEFT where the
     # account is confirmed, cheque where it is not; then verified against Marg's own
     # supplier-wise statement, then locked. The advice file and its letter come off
     # THIS sheet and nothing else. Granted by name in tile_grants.json v17.
     "desc": "Month\\u2019s NEFT sheet \\u00b7 cheques \\u00b7 verify against Marg",
     "live": True,
     "url": "/finance/purchase/page/pay",
     "roles": ["doctor"]},'''

B_OLD = '''"Marg Purchases": "Money & Accounts", "Order Medicines": "Money & Accounts",'''
B_NEW = '''"Marg Purchases": "Money & Accounts", "Order Medicines": "Money & Accounts", "Vendor payments": "Money & Accounts",'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=PORTAL)
    ap.add_argument("--from", dest="from_md5", default=None)
    a = ap.parse_args()
    path = a.file
    if not os.path.exists(path):
        sys.exit("REFUSING: %s not found" % path)
    raw = io.open(path, "rb").read()
    cur = hashlib.md5(raw).hexdigest()
    src = raw.decode("utf-8")
    if MARK in src:
        print("ALREADY PATCHED (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if a.from_md5 and cur != a.from_md5.lower():
        sys.exit("REFUSING: %s is %s, you said %s" % (path, cur, a.from_md5))
    for label, old in (("Marg Purchases tile", A_OLD), ("group map row", B_OLD)):
        if src.count(old) != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1"
                     % (label, src.count(old)))
    new = src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1)
    bak = path + ".bak_S262_" + cur[:8]
    shutil.copy2(path, bak)
    io.open(path, "w", encoding="utf-8", newline="\n").write(new)
    got = hashlib.md5(io.open(path, "rb").read()).hexdigest()
    print("patched %s" % path)
    print("   was  %s" % cur)
    print("   now  %s" % got)
    print("   backup %s" % bak)


if __name__ == "__main__":
    main()
