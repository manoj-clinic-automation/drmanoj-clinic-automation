#!/usr/bin/env python3
"""s938_fix.py -- kit S938 one-off (the owner 18:01 IST 23-Nov-2026: "She did it by mistake ... need to undo these ... LANZOL JUNIOR ... needs to
be put back for now"). argv: <finance dir> <finance.db> [--live]. Takes back Alisha's 'Out of stock' taps of 23-Nov 17:20-17:30 IST on the ten
medicines he named through order_s778.na_undo (the doctor's door) -- only taps still waiting for him. Without --live: prints what it would do."""
import sqlite3
import sys

FIN, DB = sys.argv[1], sys.argv[2]
LIVE = "--live" in sys.argv
sys.path.insert(0, FIN)
ITEMS = {"C2CALZ", "LANZOL JUNIOR", "ANKLE BINDER BAMBOO M", "TYRO BR", "BIO D3 MAX", "L S BELT L CONT GRAY UNISON", "PRETOL 8",
         "ANKLE BINDER L TYNOR", "KNEE SUPPORT XL HINGED", "KNEE SUPPORT XXL HINGED UNISO"}
import order_s778 as S7                                           # noqa: E402
con = sqlite3.connect(DB, timeout=30)
con.row_factory = sqlite3.Row
S7.ensure(con)
rows = [dict(r) for r in con.execute("SELECT id, item, by, at FROM order_s778_na WHERE status='asked' AND cleared_at IS NULL "
                                     "AND at >= '2026-11-23T17:20' AND at < '2026-11-23T17:31' AND LOWER(COALESCE(by,'')) LIKE '%alisha%' ORDER BY id")]
mine = [r for r in rows if r["item"] in ITEMS]
print("S938 one-off: %d of Alisha's 23-Nov 17:2x taps still waiting, %d on his list" % (len(rows), len(mine)))
done = 0
for r in mine:
    if LIVE:
        res, st = S7.na_undo(con, "manoj (S938: tapped by mistake, his word 18:01)", r["id"], owner=True)
        print("   %s %s -- %s" % (r["at"][11:16], r["item"], "put back" if st == 200 else "NOT put back: %s" % res.get("error")))
        done += 1 if st == 200 else 0
    else:
        print("   would put back: %s %s" % (r["at"][11:16], r["item"]))
miss = sorted(ITEMS - {r["item"] for r in mine})
if miss:
    print("   not found waiting (already answered or never tapped): %s" % ", ".join(miss))
print("S938 one-off: %s %d" % ("PUT BACK" if LIVE else "WOULD PUT BACK", done if LIVE else len(mine)))
con.close()
