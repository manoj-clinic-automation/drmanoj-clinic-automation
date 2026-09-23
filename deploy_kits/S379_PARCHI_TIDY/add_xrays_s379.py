#!/usr/bin/env python3
"""add_xrays_s379.py -- kit S379_PARCHI_TIDY. Six X-ray lines on the owner's rate page (owner_service), on his word of
23-Sep-2026 (the question put to him, his answer): Both knees AP standing (small film, Rs 300), Humerus (arm) AP &
Lateral (Rs 500), Femur (thigh) AP & Lateral (11 x 14, Rs 600), Hip AP & Lateral (Rs 500), and -- his addition --
Foot AP & Oblique and Hand AP & Oblique (small film, Rs 500 each pair). Approved (his word), side asked for the limbs.
A line already there by the same name is left alone. He edits any name or price himself on his rate page.
  python3 add_xrays_s379.py <finance.db> [--dry-run]
"""
import datetime as dt, sqlite3, sys
ROWS = [  # name, price in rupees, code, side
    ("Both knees AP standing view", 300, "KNEES_STANDING", ""),
    ("Humerus (arm) AP & Lateral view", 500, "HUMERUS", "ask"),
    ("Femur (thigh) AP & Lateral view (11 x 14)", 600, "FEMUR", "ask"),
    ("Hip AP & Lateral view", 500, "HIP", "ask"),
    ("Foot AP & Oblique view", 500, "FOOT_OBL", "ask"),
    ("Hand AP & Oblique view", 500, "HAND_OBL", "ask"),
]
db, dry = sys.argv[1], "--dry-run" in sys.argv
con = sqlite3.connect(db)
now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
have = {r[0].strip().lower() for r in con.execute("SELECT name FROM owner_service WHERE kind='xray'")}   # the (kind, name) index is unique
added = 0
for name, rs, code, side in ROWS:
    if name.lower() in have:
        print("   already there:", name)
        continue
    if not dry:
        con.execute("INSERT INTO owner_service (kind, name, price_p, active, note, created_by, created_ts, updated_by, "
                    "updated_ts, code, status, seen, grp, forms, source, side) VALUES ('xray',?,?,1,'',?,?,?,?,?,"
                    "'approved',0,'X-ray','','owner-S379',?)", (name, rs * 100, "manoj", now, "manoj", now, code, side))
    added += 1
    print("   %s %s  Rs %d%s" % ("would add" if dry else "added", name, rs, "  (side asked)" if side else ""))
if not dry:
    con.commit()
n = con.execute("SELECT COUNT(*) FROM owner_service WHERE kind='xray' AND active=1 AND status<>'rejected'").fetchone()[0]
print("XRAYS_S379 OK: %d added, %d X-rays on the list now" % (added, n + (added if dry else 0)))
