#!/usr/bin/env python3
"""seed_s340.py -- the 'checks' unit (S340, owner 20-Sep-2026: reception answers "Check karein", Shavez the
checker, the doctors see it). INSERT only where absent; nothing existing is altered.
  business_unit  checks  'Check karein (records)'
  unit_role      makers alisha, shivani, reception, shavez · checkers manoj, bhawna
Usage: seed_s340.py DB_PATH
"""
import sqlite3
import sys

ROLES = [("alisha", "maker"), ("shivani", "maker"), ("reception", "maker"), ("shavez", "maker"),
         ("manoj", "checker"), ("bhawna", "checker")]


def seed(path):
    con = sqlite3.connect(path, timeout=30)
    cols = [r[1] for r in con.execute("PRAGMA table_info(business_unit)")]
    if "open_sunday" in cols and "active" in cols:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES ('checks','Check karein (records)',1,1)")
    else:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('checks','Check karein (records)')")
    for user, role in ROLES:
        if not con.execute("SELECT 1 FROM unit_role WHERE unit='checks' AND username=? AND role=?", (user, role)).fetchone():
            con.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES ('checks',?,?,1,'S340')", (user, role))
    con.commit()
    got = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='checks' AND active=1"))
    con.close()
    if got != sorted(ROLES):
        print("SEED WRONG: checks roles are %s" % got)
        return 1
    print("seed: checks unit + %d roles" % len(ROLES))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
