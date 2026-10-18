#!/usr/bin/env python3
"""seed_s579.py -- kit S579, the data step (idempotent; a second run changes nothing and says so).
    python3 -B seed_s579.py <finance.db> <surgery_cases.py>
Makes the module's surg_* tables (its own SCHEMA, CREATE IF NOT EXISTS), the unit row 'surgery' (INSERT OR IGNORE) and, only when
the unit has no rows yet, its two logins: shavez maker, manoj checker. Touches no other table. Prints one line of what it did."""
import importlib.util
import sqlite3
import sys


def main(dbp, mod):
    spec = importlib.util.spec_from_file_location("surgery_cases_seed", mod)
    sc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sc)
    con = sqlite3.connect(dbp, timeout=30)
    con.execute("PRAGMA foreign_keys=ON")
    before = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'surg_%'")}
    con.executescript(sc.SCHEMA)
    after = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'surg_%'")}
    u = con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES ('surgery','Surgery cases',1,1)").rowcount
    n = con.execute("SELECT COUNT(*) FROM unit_role WHERE unit='surgery'").fetchone()[0]
    made = []
    if not n:
        for user, role, note in sc.SEED_ROLES:
            con.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES ('surgery',?,?,1,?)", (user, role, note))
            made.append("%s %s" % (user, role))
    con.commit()
    roles = sorted("%s %s" % (r[0], r[1]) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='surgery' AND active=1"))
    con.close()
    print("data step: %d new surg_* tables (%d in all) · unit 'surgery' %s · logins %s · active now: %s" % (
        len(after - before), len(after), "made" if u else "already there", ("made: " + ", ".join(made)) if made else "already there",
        "; ".join(roles)))
    return 0 if len(after) == 9 and "manoj checker" in roles else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
