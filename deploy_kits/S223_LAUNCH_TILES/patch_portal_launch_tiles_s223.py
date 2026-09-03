#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_launch_tiles_s223.py -- S223: the launch tile set.

THE OWNER, at the S223 open, launching the staff app to everybody:
  "daily sale, its for darpan and bhawna and myself only"
  "stk check - alisha, shavez and sivani are named users in it, along with darpan and amir,
   i and dr bhawna also shd have it"
  "forms - all staff"
  "meds return (vapsi desk) included ... dr bhawna also i wd like to have vapsi desk too"

THREE EDITS, and one new tile:

  1. Daily Sale    roles ["staff"]           -> ["doctor"]   + granted by name in tile_grants.json
  2. Vaapsi Desk   roles ["staff", "doctor"] -> ["doctor"]   + granted by name
  3. Stock Check   NEW tile -> /finance/stock/page/count, roles ["doctor"], granted by name
  4. The S179 darpan mask is STRUCK from the code dicts too -- found by the walk: without this,
     a lost grants file would silently put his mask back and nobody would know why.

WHY roles ["doctor"] AND NOT [] -- the fail-safe, stated:
A tile with no roles at all disappears for EVERYONE if tile_grants.json is ever missing or
malformed. These are money screens, so a lost grants file must fail CLOSED for staff -- but it
must never lock the owner out of his own clinic. roles ["doctor"] is exactly that: with no grants
file, staff lose these three and the doctor keeps everything. (The same shape as returns.desk_users
and the S222 corrections hide: fail safe for the owner, fail closed for everyone else.)

WHAT THIS DOES NOT TOUCH: Scan Purchase, Staff Register, Attendance, Forms & Downloads -- all
unchanged, all staff. No route, no gate, no permission. Every server-side check stays exactly as
it is: this file decides what a person is SHOWN, never what they may reach.

Target: /root/portal/portal.py   (from pin d15acef3fcb0237563475968c2eec921)
Run on the box:  /root/wa/venv/bin/python3 -B /root/portal/patch_portal_launch_tiles_s223.py
Offline:         PORTAL_PATH=./portal.py python3 -B patch_portal_launch_tiles_s223.py
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

PORTAL = os.environ.get("PORTAL_PATH", "/root/portal/portal.py")
FROM_MD5 = "d15acef3fcb0237563475968c2eec921"
MARK = '"name": "Stock Check"'

A_OLD = '''     "daily_sale_counts": True,
     "roles": ["staff"]},'''
A_NEW = '''     "daily_sale_counts": True,
     # S223: named people only (owner: "daily sale, its for darpan and bhawna and
     # myself only"). Granted by name in tile_grants.json; doctor keeps it if that
     # file is ever lost.
     "roles": ["doctor"]},'''

B_OLD = '''     "url": "/finance/returns/desk",
     "roles": ["staff", "doctor"]},'''
B_NEW = '''     "url": "/finance/returns/desk",
     # S223: the tile now follows the desk's own allow-list (returns.desk_users)
     # instead of the staff role -- a tile that only refuses you is a trap.
     "roles": ["doctor"]},
    {"icon": "\\U0001F9FE", "name": "Stock Check",
     # S223 NEW. The count and difference screens have existed since S213 and were
     # scoped for a named viewer at S221; they had no tile until now.
     "desc": "\\u0938\\u094d\\u091f\\u0949\\u0915 \\u0917\\u093f\\u0928\\u0924\\u0940 \\u2014 count & differences",
     "live": True,
     "url": "/finance/stock/page/count",
     "roles": ["doctor"]},'''

D_OLD = '''# S179: darpan is role=staff, which is shared. He only needs Daily Sale.
USER_TILE_MASK.setdefault("darpan", set()).update({"Attendance", "Staff Register", "Scan Purchase"})'''
D_NEW = '''# S179 (STRUCK at S223): "darpan is role=staff, which is shared. He only needs Daily
# Sale." That premise died when he got his own login and his own phone. The owner's
# ruling at the S223 open launched the app to everybody with the same operational
# layer, so the mask is gone from the grants file AND from here -- otherwise a lost
# grants file would quietly put it back and nobody would know why his tiles moved.
# Kept as a struck comment, not deleted, because the reason is part of the record.'''

C_OLD = '''    "Vaapsi Desk": "Money & Accounts",'''
C_NEW = '''    "Vaapsi Desk": "Money & Accounts", "Stock Check": "Money & Accounts",'''


def main():
    if not os.path.exists(PORTAL):
        sys.exit("REFUSING: %s not found" % PORTAL)
    src = io.open(PORTAL, encoding="utf-8").read()
    cur = hashlib.md5(io.open(PORTAL, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != FROM_MD5:
        sys.exit("REFUSING: %s is %s, expected %s (D172/D188)" % (PORTAL, cur, FROM_MD5))
    for label, old in (("Daily Sale roles", A_OLD), ("Vaapsi roles", B_OLD),
                      ("group map", C_OLD), ("darpan S179 mask", D_OLD)):
        n = src.count(old)
        if n != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1" % (label, n))
    new = (src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1)
              .replace(C_OLD, C_NEW, 1).replace(D_OLD, D_NEW, 1))
    bak = PORTAL + ".bak_S223_tiles_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
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
    print("next     put tile_grants.json beside portal.py, then restart clinic-portal")


if __name__ == "__main__":
    main()
