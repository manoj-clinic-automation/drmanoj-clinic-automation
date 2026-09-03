#!/usr/bin/env python3
"""seed_amir_role_s221.py -- S221: Amir's permission, as one unit_role row.

He was onboarded on 03-Sep-2026: Emp Code 101, roster row, portal login `amir`
as role `staff`. The portal login gets him THROUGH the front door; it does not
decide which rooms open. That is `unit_role`, and he had no row -- so every page
his own card offers him would have refused him on his next visit.

    unit='medical'  username='amir'  role='viewer'

`viewer` is the scoped role this system already uses for named staff on one desk
-- Reception holds it for the Vaapsi desk and writes return slips with it
(S214). With the S221 patches it opens exactly:

    his corrections desk        read the list, tick what he has fixed in Marg
    the stock count screen      count, and submit the count
    the stock differences list  see what his count produced
    the Vaapsi desk             (viewer has always opened it)
    the audit finding           read it, and answer a line

and nothing else. He cannot file a day, approve one, touch the drawer, move
money between ledgers, set a price, name a cause, or rule on a difference.

Idempotent -- run it as often as you like. It adds the row only if it is
missing, and prints the whole medical unit afterwards so the answer to "who can
do what" is on the screen rather than in somebody's memory.

    /root/wa/venv/bin/python3 -B seed_amir_role_s221.py /root/finance/finance.db
"""
import sqlite3
import sys

WHO = "amir"
NOTE = ("S221 purchase/corrections/stock (viewer: his three desks and nothing "
        "else -- not maker, because maker files the day)")


def main(db):
    con = sqlite3.connect(db)
    n = con.execute(
        "SELECT COUNT(*) FROM unit_role WHERE unit='medical' AND "
        "lower(username)=? AND role='viewer' AND active=1", (WHO,)).fetchone()[0]
    if n:
        print("already there: %s already holds viewer on medical" % WHO)
    else:
        con.execute("INSERT INTO unit_role (unit, username, role, active, note) "
                    "VALUES ('medical', ?, 'viewer', 1, ?)", (WHO, NOTE))
        con.commit()
        print("added: %s -> viewer on medical" % WHO)
    rows = con.execute("SELECT username, role FROM unit_role WHERE unit='medical' "
                       "AND active=1 ORDER BY role, username").fetchall()
    print("medical unit now: %s" % ", ".join("%s(%s)" % r for r in rows))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/root/finance/finance.db"))
