#!/usr/bin/env python3
"""seed_s289.py -- the 'petty' unit and who holds which role in it (S289, owner 17-Sep-2026).
INSERT OR IGNORE only: a second run changes nothing, and nothing existing is altered.
  business_unit  petty  'Petty book'
  unit_role      petty/bhati maker · petty/manoj checker · petty/bhawna checker
                 petty/shavez, petty/shivani, petty/alisha viewer (reception: the availability line only)
Usage: seed_s289.py DB_PATH
"""
import sqlite3
import sys

ROLES = [("bhati", "maker"), ("manoj", "checker"), ("bhawna", "checker"),
         ("shavez", "viewer"), ("shivani", "viewer"), ("alisha", "viewer")]


def seed(path):
    con = sqlite3.connect(path, timeout=30)
    con.execute("PRAGMA foreign_keys = ON")
    cols = [r[1] for r in con.execute("PRAGMA table_info(business_unit)")]
    if "entity_code" in cols:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES ('petty','Petty book',1,1)")
    else:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('petty','Petty book')")
    for user, role in ROLES:
        con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active, note) VALUES ('petty',?,?,1,'S289')",
                    (user, role))
    con.commit()
    got = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='petty' AND active=1"))
    con.close()
    for user, role in ROLES:
        if (user, role) not in got:
            print("SEED MISSING: petty/%s %s" % (user, role))
            return 1
    print("seed: petty unit + %d roles present" % len(ROLES))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
