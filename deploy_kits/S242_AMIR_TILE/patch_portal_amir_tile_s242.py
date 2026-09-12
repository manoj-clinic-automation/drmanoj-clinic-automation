#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_amir_tile_s242.py -- S242: Amir's own page gets a door.

THE OWNER, 12-Sep-2026: "allow him only the one u made today, forms and dnloads not needed for
him, Marg Purchases - Order Medicines - Stock Check - Scan Purchase is not for him for now, so
park these too, will decide these later."

WHAT WAS WRONG. `/finance/amir` -- his seven steps -- went live at S241 and has NO TILE anywhere
in this file. It could only be reached by typing the address. Measured, not assumed: the owner's
own portal was read live and carries no such tile, and the owner's portal shows every tile there
is.

ONE TILE IS ADDED. "Amir ka kaam" -> /finance/amir, `roles: ["doctor"]` like every other granted
tile, so a lost or malformed grants file leaves it with the doctor and nobody else (fail closed).
Amir is given it BY NAME in tile_grants.json v12, which ships beside this patcher and must be
installed in the same step: a grant matches a tile by its name, and a name that matches no tile
grants nothing.

_TILE_GROUP is keyed by tile NAME and the file asserts at import that every tile is grouped, so
the group row is added in the same edit. A tile without its group row 503s the portal on restart.

NOTHING IS REMOVED HERE. The five tiles the owner parked -- Forms & Downloads, Scan Purchase,
Marg Purchases, Order Medicines, Stock Check -- are parked for AMIR in the grants file, by mask
and by dropping his `extra`. Every one of them stays in this file, keeps its roles, and stays
exactly as it is for everybody else. Bringing any of them back for him is one line.

Two anchors, each must match EXACTLY ONCE, or nothing is changed. Idempotent by the MARK.
Timestamped backup, compile-with-restore.

Run on the box:
    /root/wa/venv/bin/python3 -B patch_portal_amir_tile_s242.py [portal.py] [expected md5]
Offline:
    python3 -B patch_portal_amir_tile_s242.py ./portal.py
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/root/portal/portal.py"
FROM = sys.argv[2] if len(sys.argv) > 2 else "ed558b3663c3dd100a24f58aafc32363"
MARK = '"name": "Amir ka kaam"'

# A -- the tile itself, immediately after Order Medicines (the other purchase-side door)
A_OLD = '''     "url": "/finance/purchase/page/staff",
     "roles": ["doctor"]},'''
A_NEW = '''     "url": "/finance/purchase/page/staff",
     "roles": ["doctor"]},
    {"icon": "\\U0001F9ED", "name": "Amir ka kaam",
     # S242 NEW (D483). Amir's seven steps, live since S241 and until now with no door at all --
     # the page could only be reached by typing the address. The owner's ruling of 12-Sep-2026:
     # this is the ONLY tile Amir carries. Forms & Downloads, Scan Purchase, Marg Purchases,
     # Order Medicines and Stock Check are PARKED for him in tile_grants.json v12 -- parked, not
     # removed, and unchanged for everybody else. Granted by name; doctor keeps it by role.
     "desc": "Aaj ka kaam \\u2014 1 se 7 tak",
     "live": True,
     "url": "/finance/amir",
     "roles": ["doctor"]},'''

# B -- the group map, keyed by tile name; an ungrouped tile fails the import assert
B_OLD = '''    "Docterz daily collection": "Money & Accounts", "Marg Purchases": "Money & Accounts", "Order Medicines": "Money & Accounts",'''
B_NEW = '''    "Docterz daily collection": "Money & Accounts", "Marg Purchases": "Money & Accounts", "Order Medicines": "Money & Accounts",
    "Amir ka kaam": "Money & Accounts",'''

PAIRS = (("the Amir tile", A_OLD, A_NEW),
         ("the group map row", B_OLD, B_NEW))


def main():
    if not os.path.exists(P):
        sys.exit("REFUSING: %s not found" % P)
    src = io.open(P, encoding="utf-8").read()
    cur = hashlib.md5(io.open(P, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != FROM:
        sys.exit("REFUSING: %s is %s, expected %s. Read the box's pin again." % (P, cur, FROM))
    for label, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1" % (label, n))
    new = src
    for _label, old, rep in PAIRS:
        new = new.replace(old, rep, 1)
    bak = P + ".bak_S242_amirtile_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(P, bak)
    io.open(P, "w", encoding="utf-8", newline="\n").write(new)
    try:
        import py_compile
        import tempfile
        _fd, _cf = tempfile.mkstemp(suffix=".pyc")
        os.close(_fd)
        try:
            py_compile.compile(P, cfile=_cf, doraise=True)
        finally:
            try:
                os.remove(_cf)
            except OSError:
                pass
    except Exception as e:                       # noqa: BLE001
        shutil.copy2(bak, P)
        sys.exit("REFUSING: compile failed (%s); restored %s" % (e, bak))
    got = hashlib.md5(io.open(P, "rb").read()).hexdigest()
    print("current pin  %s" % FROM)
    print("patched  %s" % P)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- the line the close records (A0: never from memory)" % got)
    print("next     put tile_grants.json v12 beside it, then restart clinic-portal")


if __name__ == "__main__":
    main()
