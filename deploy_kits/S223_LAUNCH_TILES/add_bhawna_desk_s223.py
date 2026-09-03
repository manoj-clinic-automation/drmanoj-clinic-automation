#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""add_bhawna_desk_s223.py -- S223: Dr Bhawna joins the Vaapsi desk allow-list.

THE OWNER: "dr bhawna also i wd like to have vapsi desk too"

The Vaapsi tile is not what stops her -- `returns.desk_users` is (F-296, the S222 allow-list).
This ADDS one name to that row. It does not replace the row, does not touch unit_role, and does
not remove anybody: it reads what is there, appends `bhawna` if she is not already in it, and
prints the value before and after so the change is visible rather than asserted.

Re-runnable: if she is already listed it says so and writes nothing.

    /root/wa/venv/bin/python3 -B /root/finance/add_bhawna_desk_s223.py /root/finance/finance.db
"""
import sqlite3
import sys

KEY = "returns.desk_users"
ADD = "bhawna"


def main(db):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    r = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()
    if r is None:
        print("REFUSING: %s does not exist. The S222 desk-users kit is not installed; adding a "
              "name to a row that is not there would turn the gate ON for the first time and "
              "lock everyone else out." % KEY)
        return 2
    cur = (r["value"] or "").strip()
    names = [n.strip() for n in cur.split(",") if n.strip()]
    print("before  %s = %s" % (KEY, cur))
    if ADD in names:
        print("already listed -- nothing written")
        return 0
    names.append(ADD)
    new = ",".join(names)
    con.execute("UPDATE setting SET value=? WHERE key=?", (new, KEY))
    con.commit()
    back = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()["value"]
    print("after   %s = %s" % (KEY, back))
    if back != new:
        print("REFUSING: read-back does not match what was written")
        return 3
    print("OK      %s added. No restart needed -- the desk reads this row per request." % ADD)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/root/finance/finance.db"))
