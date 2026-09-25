#!/usr/bin/env python3
"""seed_s400.py -- the 'salecheck' unit (S400, the owner 25-Sep-2026, D616): Bhati checks the pharmacy days.
INSERT only where absent; nothing existing is altered. Bhati gets NO medical row (the brief's rule).
  business_unit  salecheck  'Medical sale check'
  unit_role      maker bhati · checker manoj
Usage: seed_s400.py DB_PATH
"""
import sqlite3
import sys

ROLES = [("bhati", "maker"), ("manoj", "checker")]


def seed(path):
    con = sqlite3.connect(path, timeout=30)
    cols = [r[1] for r in con.execute("PRAGMA table_info(business_unit)")]
    if "open_sunday" in cols and "active" in cols:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES ('salecheck','Medical sale check',1,1)")
    else:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('salecheck','Medical sale check')")
    for user, role in ROLES:
        if not con.execute("SELECT 1 FROM unit_role WHERE unit='salecheck' AND username=? AND role=?", (user, role)).fetchone():
            con.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES ('salecheck',?,?,1,'S400')", (user, role))
    con.commit()
    got = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='salecheck' AND active=1"))
    med = con.execute("SELECT COUNT(*) FROM unit_role WHERE unit='medical' AND lower(username)='bhati'").fetchone()[0]
    con.close()
    if got != sorted(ROLES):
        print("SEED WRONG: salecheck roles are %s" % got)
        return 1
    if med:
        print("SEED WRONG: bhati holds a medical row -- the brief forbids it")
        return 1
    print("seed: salecheck unit + %d roles; bhati has no medical row" % len(ROLES))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
