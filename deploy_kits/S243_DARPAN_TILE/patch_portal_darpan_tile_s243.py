#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_portal_darpan_tile_s243.py -- S243: Darpan's day gets its door.

THE OWNER, 13-Sep-2026: Darpan's day now lives at /finance/darpan/kal ("Kal ka hisaab", kit
S243_DARPAN_KAL: the report fills yesterday's numbers, he types two things -- how much cash, to
whom).  His tile must open it.  A page with no tile can only be reached by typing the address
(the S242 lesson), so:

ONE TILE IS ADDED.  "Kal ka hisaab" -> /finance/darpan/kal, `roles: ["doctor"]` like every other
granted tile, so a lost or malformed grants file leaves it with the doctor and nobody else (fail
closed).  Darpan is given it BY NAME in tile_grants.json v14, which ships beside this patcher and
must be installed in the same step: a grant matches a tile by its name, and a name that matches no
tile grants nothing.  The owner's `manoj` login sees it by role (the page shows him the English
owner view of the same day).

WHY A NEW TILE AND NOT A REPOINT.  A tile has one address for everybody.  "Daily Sale" is the
owner's too (his now lands on Review, S243_SCREEN_FIXES), so repointing it would move HIS door;
ruled out.  Daily Sale stays exactly as it is for everyone, Darpan included -- the manual form is
the fallback and is untouched.

WHERE IT SITS.  Immediately BEFORE "Daily Sale" in TILES, so in Darpan's Money & Accounts section
his day page is the first tile, the old form second, Vaapsi Desk third.  Section order is the
grants file's, unchanged.

_TILE_GROUP is keyed by tile NAME and the file asserts at import that every tile is grouped, so the
group row is added in the same edit.  A tile without its group row 503s the portal on restart.

NOTHING IS REMOVED OR MOVED.  Every other tile keeps its roles, its address and its place.
"Corrections" (the CA retired it as Darpan's task) was never in his grants -- it is roles [doctor]
with no name-grant to anyone -- so there is nothing to take away; the walk proves he is not shown it.

Two anchors, each must match EXACTLY ONCE, or nothing is changed.  Idempotent by the MARK.
Timestamped backup, compile-with-restore.

Run on the box:
    /root/wa/venv/bin/python3 -B patch_portal_darpan_tile_s243.py [portal.py] [expected md5]
Offline:
    python3 -B patch_portal_darpan_tile_s243.py ./portal.py
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/root/portal/portal.py"
FROM = sys.argv[2] if len(sys.argv) > 2 else "4bb6bde0e2e07033ac0e0f5d7a7daaf6"
MARK = '"name": "Kal ka hisaab"'

# A -- the tile itself, immediately before Daily Sale (the form it supersedes for Darpan)
A_OLD = '''    # --- Sanjeevni finance (S179) ------------------------------------------
    {"icon": "\\U0001F3EA", "name": "Daily Sale",'''
A_NEW = '''    # --- Sanjeevni finance (S179) ------------------------------------------
    {"icon": "\\U0001F9EE", "name": "Kal ka hisaab",
     # S243 NEW. Darpan's morning page (owner's ruling, 13-Sep-2026): yesterday's Marg report
     # fills the numbers, he types two things -- kitna cash diya, kisko diya -- and answers
     # yesterday's flagged returns. Kit S243_DARPAN_KAL. Granted by name to darpan in
     # tile_grants.json v14; the doctor keeps it by role and is shown the owner view of the
     # same day. Daily Sale below is untouched: the manual form stays as the fallback.
     "desc": "Kal ka cash \\u2014 kitna diya, kisko diya",
     "live": True,
     "url": "/finance/darpan/kal",
     "roles": ["doctor"]},
    {"icon": "\\U0001F3EA", "name": "Daily Sale",'''

# B -- the group map, keyed by tile name; an ungrouped tile fails the import assert
B_OLD = '''    "Daily Sale": "Money & Accounts", "Sanjeevni Medicos": "Money & Accounts",
'''
B_NEW = '''    "Kal ka hisaab": "Money & Accounts",
    "Daily Sale": "Money & Accounts", "Sanjeevni Medicos": "Money & Accounts",
'''

PAIRS = (("the Kal ka hisaab tile", A_OLD, A_NEW),
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
    bak = P + ".bak_S243_darpantile_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
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
    print("next     put tile_grants.json v14 beside it, then restart clinic-portal")


if __name__ == "__main__":
    main()
