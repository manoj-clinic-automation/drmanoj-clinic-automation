#!/usr/bin/env python3
"""
patch_portal_vaapsi_tile.py -- S218 v2. Two anchored edits:
  1. Daily Sale tile -> /finance/daily (the S218-retired /finance/entry killed
     the maker's tap-through).
  2. NEW "Vaapsi Desk" tile (roles staff + doctor) AND its _TILE_GROUP entry.
     The portal asserts every tile is grouped at IMPORT (a runtime assert
     compile() cannot catch -- the v1 miss that 503'd the portal). Both edits
     are required together or the module refuses to boot.
SAFETY: two exact-once anchors, timestamped backup, compile-with-restore.
Idempotent by the MARK.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get("PORTAL_PATH", "/root/portal/portal.py")
MARK = "Vaapsi Desk"

OLD_TILE = '''     "desc": "Enter today's shop sale", "live": True,
     "url": "/finance/entry",
     "daily_sale_counts": True,
     "roles": ["staff"]},'''

NEW_TILE = '''     "desc": "Enter today's shop sale", "live": True,
     "url": "/finance/daily",
     "daily_sale_counts": True,
     "roles": ["staff"]},
    {"icon": "\\U0001F4E6", "name": "Vaapsi Desk",
     # S218: the reception returns desk (D358). Staff phones run it as a PWA;
     # this tile is the same door from the portal, for staff AND the owner.
     "desc": "\\u0935\\u093e\\u092a\\u0938\\u0940 \\u092a\\u0930\\u094d\\u091a\\u0940 \\u2014 sale return",
     "live": True,
     "url": "/finance/returns/desk",
     "roles": ["staff", "doctor"]},'''

OLD_GRP = '''    "Daily Sale": "Money & Accounts", "Sanjeevni Medicos": "Money & Accounts",'''
NEW_GRP = '''    "Daily Sale": "Money & Accounts", "Sanjeevni Medicos": "Money & Accounts",
    "Vaapsi Desk": "Money & Accounts",'''


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for label, old in (("tile", OLD_TILE), ("group", OLD_GRP)):
        if src.count(old) != 1:
            raise SystemExit("REFUSED: %s anchor matches %d (need 1) -- drifted."
                             % (label, src.count(old)))
    bak = TARGET + ".bak_S218_tile_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copyfile(TARGET, bak)
    out = src.replace(OLD_TILE, NEW_TILE, 1).replace(OLD_GRP, NEW_GRP, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: compile failed (%s); restored." % ex)
    print("patched (Daily Sale -> /finance/daily; Vaapsi Desk tile + group); backup %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
