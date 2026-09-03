#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_desk_users_s222.py -- S222: NAME the Vaapsi desk staff. F-296.

The owner's list, given at the S221 close:  Darpan . Shavez . Alisha . Shivani.

Writes ONE row: setting `returns.desk_users`. It does NOT touch unit_role, so
nobody loses a role and nothing else they reach changes -- Amir keeps his
corrections desk and his stock count exactly as they are. He simply stops
being able to open a cash-refund screen.

IT NEVER OVERWRITES. If the owner has already edited the row by hand, this
prints what is there and changes nothing. Re-runnable.

    /root/wa/venv/bin/python3 -B /root/finance/seed_desk_users_s222.py /root/finance/finance.db
"""
import sqlite3
import sys

KEY = "returns.desk_users"
STAFF = "darpan,shavez,alisha,shivani"
NOTE = ("S222 F-296 -- the Vaapsi desk allow-list. Only these logins, plus any "
        "maker/checker, may open /finance/returns/desk. BLANK OR DELETED = the "
        "gate is off and every viewer reaches the desk again (that is the "
        "designed fail-safe, not a bug). Comma-separated logins.")


def main(db):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    r = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()
    if r is not None:
        print("already set -- NOT changed")
        print("  %s = %s" % (KEY, r["value"]))
        return 0
    try:
        con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?)",
                    (KEY, STAFF, NOTE))
    except sqlite3.OperationalError:
        con.execute("INSERT INTO setting (key, value) VALUES (?,?)", (KEY, STAFF))
    con.commit()
    print("seeded  %s = %s" % (KEY, STAFF))
    rows = con.execute("SELECT username, role FROM unit_role WHERE unit='medical' "
                       "AND active=1 ORDER BY username").fetchall()
    print("medical unit roles (unchanged): %s"
          % ", ".join("%s(%s)" % (x["username"], x["role"]) for x in rows))
    print("-> a viewer NOT in the list can no longer open the Vaapsi desk.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/root/finance/finance.db"))
