#!/usr/bin/env python3
"""seed_s332.py -- the 'records' unit and its two checkers (S332, owner 19/20-Sep-2026:
"only the doctors can open patient records"). INSERT only where absent; nothing existing is altered.
  business_unit  records  'Patient records'
  unit_role      checkers manoj, bhawna -- and nobody else
Usage: seed_s332.py DB_PATH
"""
import sqlite3
import sys

ROLES = [("manoj", "checker"), ("bhawna", "checker")]


def seed(path):
    con = sqlite3.connect(path, timeout=30)
    con.execute("PRAGMA foreign_keys = ON")
    cols = [r[1] for r in con.execute("PRAGMA table_info(business_unit)")]
    if "open_sunday" in cols and "active" in cols:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES ('records','Patient records',1,1)")
    else:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('records','Patient records')")
    for user, role in ROLES:
        if not con.execute("SELECT 1 FROM unit_role WHERE unit='records' AND username=? AND role=?", (user, role)).fetchone():
            con.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES ('records',?,?,1,'S332')", (user, role))
    con.commit()
    got = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='records' AND active=1"))
    con.close()
    if got != sorted(ROLES):
        print("SEED WRONG: records roles are %s" % got)
        return 1
    print("seed: records unit + %d roles (doctors only)" % len(ROLES))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
