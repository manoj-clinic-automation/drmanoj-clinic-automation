#!/usr/bin/env python3
"""seed_s404.py -- the 'stockmatch' unit and the rename memory (S404, the owner 26-Sep-2026, D619 / D620).
INSERT only where absent; nothing existing is altered.
  business_unit    stockmatch  'Stock milaan'
  unit_role        maker darpan · checker manoj   (nobody else)
  marg_item_rename the 22 of S268_ORTHOTIC_NAME_FIX_THE_22 v2 (item_alias.seed; refuses on any collision at 20/27/29)
Usage: seed_s404.py DB_PATH [--finance DIR]     (DIR = where item_alias.py sits; default /root/finance)
"""
import os
import sqlite3
import sys

ROLES = [("darpan", "maker"), ("manoj", "checker")]


def seed(path, finance_dir="/root/finance"):
    if finance_dir not in sys.path:
        sys.path.insert(0, finance_dir)
    import item_alias                                         # noqa: E402 -- from the placed copy, never from a kit folder
    con = sqlite3.connect(path, timeout=30)
    cols = [r[1] for r in con.execute("PRAGMA table_info(business_unit)")]
    if "open_sunday" in cols and "active" in cols:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES ('stockmatch','Stock milaan',1,1)")
    else:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name) VALUES ('stockmatch','Stock milaan')")
    for user, role in ROLES:
        if not con.execute("SELECT 1 FROM unit_role WHERE unit='stockmatch' AND username=? AND role=?", (user, role)).fetchone():
            con.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES ('stockmatch',?,?,1,'S404')", (user, role))
    added, kept, problems = item_alias.seed(con, by_user="S404")
    if problems:
        con.rollback()
        con.close()
        print("SEED REFUSED: the rename list would collide -- %s" % "; ".join(problems))
        return 1
    con.commit()
    got = sorted(tuple(r) for r in con.execute("SELECT username, role FROM unit_role WHERE unit='stockmatch' AND active=1"))
    n = con.execute("SELECT COUNT(*) FROM marg_item_rename").fetchone()[0]
    longest = con.execute("SELECT MAX(length(new_name)) FROM marg_item_rename").fetchone()[0]
    con.close()
    if got != sorted(ROLES):
        print("SEED WRONG: stockmatch roles are %s" % got)
        return 1
    if n != 22 or int(longest or 0) > 29:
        print("SEED WRONG: marg_item_rename holds %d rows, longest new name %s" % (n, longest))
        return 1
    print("seed: stockmatch unit + %d roles; rename memory %d rows (%d added, %d kept), longest new name %d" % (len(ROLES), n, added, kept, longest))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(2)
    fin = a[a.index("--finance") + 1] if "--finance" in a else "/root/finance"
    sys.exit(seed(a[0], fin))
