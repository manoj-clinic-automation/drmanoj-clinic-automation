#!/usr/bin/env python3
"""seed_s324.py -- the 'slips' unit and who holds which role in it (S324, owner 19-Sep-2026).
INSERT OR IGNORE only: a second run changes nothing, and nothing existing is altered.
  business_unit  slips  'OPD & X-ray/Proc slips'
  unit_role      makers   shavez, alisha, shivani, bhati (the chamber assistants) and awdhesh (the room)
                 checkers manoj, bhawna (the report)
Usage: seed_s324.py DB_PATH
"""
import sqlite3
import sys

ROLES = [("shavez", "maker"), ("alisha", "maker"), ("shivani", "maker"), ("bhati", "maker"),
         ("awdhesh", "maker"), ("manoj", "checker"), ("bhawna", "checker")]


def seed(path):
    con = sqlite3.connect(path, timeout=30)
    con.execute("PRAGMA foreign_keys = ON")
    cols = [r[1] for r in con.execute("PRAGMA table_info(business_unit)")]
    if "open_sunday" in cols and "active" in cols:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) "
                    "VALUES ('slips','OPD & X-ray/Proc slips',1,1)")
    else:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('slips','OPD & X-ray/Proc slips')")
    for user, role in ROLES:
        have = con.execute("SELECT 1 FROM unit_role WHERE unit='slips' AND username=? AND role=?",
                           (user, role)).fetchone()
        if not have:
            con.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES ('slips',?,?,1,'S324')",
                        (user, role))
    con.commit()
    got = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='slips' AND active=1"))
    con.close()
    for user, role in ROLES:
        if (user, role) not in got:
            print("SEED MISSING: slips/%s %s" % (user, role))
            return 1
    print("seed: slips unit + %d roles present" % len(ROLES))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
