#!/usr/bin/env python3
# amir_s957.py · kit S957_COUNT_LEFTOVERS · the owner's word 26-Nov 09:31 ("remind ktros dt stk issue"): ONE tap job on Amir's card.
# python amir_s957.py add | remove   (FINANCE_DB = the database). remove takes it off only while Amir has not tapped it done.
import datetime as dt
import os
import sqlite3
import sys

KEY = "S957:ktros:7-11"
TEXT = "KT ROS DT — Marg mein STOCK ISSUE kijiye: 7 patte + 11 goli"
SUB = ("Darpan ki 23-11 ki ginti: shelf 19 patte 14 goli, Marg 27 patte 10 goli. Pichhli do baar 'Kar diya' dabaya tha par Marg ka stock "
       "nahi ghata -- voucher save karke Marg mein KT ROS DT ka stock dekhiye, phir 'Kar diya' dabaiye.")
c = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
arg = sys.argv[1] if len(sys.argv) > 1 else ""
if arg == "add":
    if c.execute("SELECT 1 FROM amir_job WHERE key=?", (KEY,)).fetchone():
        print("S957 Amir: the KT ROS DT job is already on his card")
    else:
        now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                  (KEY, "tap", "KT ROS DT", TEXT, SUB, now, "S957 (the owner's word, 26-Nov)", now))
        c.commit()
        print("S957 Amir: KT ROS DT job put on his card")
elif arg == "remove":
    n = c.execute("DELETE FROM amir_job WHERE key=? AND done_at IS NULL", (KEY,)).rowcount
    c.commit()
    print("S957 Amir: %d job removed" % n)
else:
    print("usage: amir_s957.py add | remove")
    sys.exit(2)
