#!/usr/bin/env python3
"""
patch_portal_vaapsi_tile.py -- S218: two tile fixes in one anchored change.
1. Daily Sale tile pointed at /finance/entry -- the page RETIRED at S218; staff
   tapping their tile landed on the retirement notice. Now /finance/daily.
2. NEW "Vaapsi Desk" tile (roles staff + doctor): alisha, shivani, darpan,
   shavez AND the owner all get it. A tile is convenience, never authorisation
   (F-84); the desk routes guard themselves.
SAFETY: exact-once anchor (verbatim from the pinned S200_R8 bytes == live
24ea2c0b), timestamped backup, compile-with-restore.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get("PORTAL_PATH", "/root/portal/portal.py")
MARK = "Vaapsi Desk"

OLD = '''     "desc": "Enter today's shop sale", "live": True,
     "url": "/finance/entry",
     "daily_sale_counts": True,
     "roles": ["staff"]},'''

NEW = '''     "desc": "Enter today's shop sale", "live": True,
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


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched (%s tile present) -- nothing to do" % MARK)
        return 0
    n = src.count(OLD)
    if n != 1:
        raise SystemExit("REFUSED: anchor matches %d times (need 1) -- portal drifted." % n)
    bak = TARGET + ".bak_S218_tile_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copyfile(TARGET, bak)
    out = src.replace(OLD, NEW, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: compile failed (%s); restored from %s" % (ex, bak))
    print("patched %s (Daily Sale -> /finance/daily; Vaapsi Desk tile added); backup %s"
          % (TARGET, bak))
    return 0


if __name__ == "__main__":
    sys.exit(main())
