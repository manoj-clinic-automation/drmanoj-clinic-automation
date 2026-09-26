#!/usr/bin/env python3
"""seed_s409.py -- kit S409_SCAN_LANES (D625). Two databases, INSERT OR IGNORE only:
  finance.db  setting porders.scan_from = 2026-09-01  (the owner: Sanjeevni purchase bill scanning starts from 1st September)
  assets.db   user_lane_default: sukhveer -> lab_purchase, awdhesh -> clinic, darpan -> pharmacy, manoj -> owner_expense
              (the table is also made by the asset app's migrate(); the app falls back to the same list when a row is absent)
Usage: seed_s409.py FINANCE_DB ASSETS_DB
"""
import datetime
import sqlite3
import sys

LANE_DEFAULTS = {"sukhveer": "lab_purchase", "awdhesh": "clinic", "darpan": "pharmacy", "manoj": "owner_expense"}


def seed(fin, ast):
    con = sqlite3.connect(fin, timeout=30)
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES ('porders.scan_from', '2026-09-01', "
                "'S409 D625 -- pharmacy bill scanning counts purchase bills from this date; a data edit changes it')")
    con.commit()
    sf = con.execute("SELECT value FROM setting WHERE key='porders.scan_from'").fetchone()
    con.close()
    a = sqlite3.connect(ast, timeout=30)
    a.execute("CREATE TABLE IF NOT EXISTS user_lane_default(username TEXT PRIMARY KEY, lane TEXT NOT NULL, set_by TEXT, set_at TEXT)")
    now = datetime.datetime.now().replace(microsecond=0).isoformat()
    for u, lane in LANE_DEFAULTS.items():
        a.execute("INSERT OR IGNORE INTO user_lane_default(username, lane, set_by, set_at) VALUES(?,?,?,?)", (u, lane, "seed S409", now))
    a.commit()
    got = dict(a.execute("SELECT username, lane FROM user_lane_default").fetchall())
    a.close()
    if not sf or not all(u in got for u in LANE_DEFAULTS):
        print("SEED WRONG: scan_from=%s lanes=%s" % (sf, got))
        return 1
    print("seed: porders.scan_from=%s; lane defaults %s" % (sf[0], ", ".join("%s=%s" % (u, got[u]) for u in sorted(LANE_DEFAULTS))))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1], sys.argv[2]))
