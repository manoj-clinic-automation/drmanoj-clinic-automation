#!/usr/bin/env python3
"""seed_desk_roles.py -- S214: the Vaapsi Desk staff list, as unit_role rows.

The owner's ruling: the desk is worked by NAMED reception staff, fallbacks
Darpan and Shavez. Their permission lives where every other permission lives
-- `unit_role` -- as role `viewer` on the medical unit. The unit_role CHECK allows only
maker/checker/viewer (a fourth word was refused by the constraint at the
first install -- correctly), and no other finance route accepts viewer, so
it grants the desk and NOTHING else. darpan (maker) and manoj (checker) already reach the desk through
their existing roles; rows are added only where missing. Idempotent.

    /root/wa/venv/bin/python3 -B seed_desk_roles.py /root/finance/finance.db
"""
import sqlite3
import sys

STAFF = ("alisha", "shivani", "shavez")
NOTE = "S214 Vaapsi Desk operator (viewer role: the desk and nothing else)"


def main(db):
    con = sqlite3.connect(db)
    added = 0
    for name in STAFF:
        n = con.execute(
            "SELECT COUNT(*) FROM unit_role WHERE unit='medical' AND "
            "lower(username)=? AND role='viewer' AND active=1", (name,)).fetchone()[0]
        if not n:
            con.execute("INSERT INTO unit_role (unit, username, role, active, note) "
                        "VALUES ('medical', ?, 'viewer', 1, ?)", (name, NOTE))
            added += 1
    con.commit()
    rows = con.execute("SELECT username, role FROM unit_role WHERE unit='medical' "
                       "AND active=1 ORDER BY username").fetchall()
    print("desk roles: %d added; medical unit now: %s"
          % (added, ", ".join("%s(%s)" % r for r in rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/root/finance/finance.db"))
