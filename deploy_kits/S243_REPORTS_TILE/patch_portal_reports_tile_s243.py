#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_reports_tile_s243.py -- S243: the Marg report generator's page gets a door.

THE OWNER, 13-Sep-2026: Shavez becomes the Marg report generator -- the morning job on the
medical PC, before any sale starts, and on Amir's days too.  His page is /finance/reports/aaj
(kit S243_REPORTS_TILE, module reports_tile.py on the finance app).  A page with no tile can only
be reached by typing the address (the S242 lesson), so:

ONE TILE IS ADDED.  "Aaj ki reports" -> /finance/reports/aaj, `roles: ["doctor"]` like every other
granted tile, so a lost or malformed grants file leaves it with the doctor and nobody else (fail
closed).  Shavez and Amir are given it BY NAME in tile_grants.json v13, which ships beside this
patcher and must be installed in the same step: a grant matches a tile by its name, and a name
that matches no tile grants nothing.  The owner's `manoj` login sees it by role.

_TILE_GROUP is keyed by tile NAME and the file asserts at import that every tile is grouped, so
the group row is added in the same edit.  A tile without its group row 503s the portal on restart.

NOTHING IS REMOVED OR MOVED.  Every other tile keeps its roles and its place.

Two anchors, each must match EXACTLY ONCE, or nothing is changed.  Idempotent by the MARK.
Timestamped backup, compile-with-restore.

Run on the box:
    /root/wa/venv/bin/python3 -B patch_portal_reports_tile_s243.py [portal.py] [expected md5]
Offline:
    python3 -B patch_portal_reports_tile_s243.py ./portal.py
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/root/portal/portal.py"
FROM = sys.argv[2] if len(sys.argv) > 2 else "d08721f69bc7c3e3a79a50192b20affb"
MARK = '"name": "Aaj ki reports"'

# A -- the tile itself, immediately after Amir ka kaam (the other Marg morning door)
A_OLD = '''     "url": "/finance/amir",
     "roles": ["doctor"]},'''
A_NEW = '''     "url": "/finance/amir",
     "roles": ["doctor"]},
    {"icon": "\\U0001F4CB", "name": "Aaj ki reports",
     # S243 NEW. The Marg report generator's morning page (owner's ruling, 13-Sep-2026: Shavez
     # generates the reports on the medical PC before any sale starts, and on Amir's days too).
     # The server sees each export arrive through the one door and ticks it here; refused and
     # still-due ones are the only things the page asks about. Granted by name to shavez and
     # amir in tile_grants.json v13; the doctor keeps it by role.
     "desc": "Marg ki reports \\u2014 aa gayi / baaki",
     "live": True,
     "url": "/finance/reports/aaj",
     "roles": ["doctor"]},'''

# B -- the group map, keyed by tile name; an ungrouped tile fails the import assert
B_OLD = '''    "Amir ka kaam": "Money & Accounts",
'''
B_NEW = '''    "Amir ka kaam": "Money & Accounts",
    "Aaj ki reports": "Money & Accounts",
'''

PAIRS = (("the reports tile", A_OLD, A_NEW),
         ("the group map row", B_OLD, B_NEW))


def patch_text(src):
    """(new_text, status) -- 'already' | 'patched' | 'refused: ...'.  Used by the walk too."""
    if MARK in src:
        return src, "already"
    for label, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            return src, "refused: anchor %r matched %d times, expected exactly 1" % (label, n)
    new = src
    for _label, old, rep in PAIRS:
        new = new.replace(old, rep, 1)
    return new, "patched"


def main():
    if not os.path.exists(P):
        sys.exit("REFUSING: %s not found" % P)
    src = io.open(P, encoding="utf-8").read()
    cur = hashlib.md5(io.open(P, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if FROM and cur != FROM:
        sys.exit("REFUSING: %s is %s, expected %s. Read the box's pin again." % (P, cur, FROM))
    new, st = patch_text(src)
    if st != "patched":
        sys.exit("REFUSING: " + st[len("refused: "):])
    bak = P + ".bak_S243_reportstile_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
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
    print("next     put tile_grants.json v13 beside it, then restart clinic-portal")


if __name__ == "__main__":
    main()
