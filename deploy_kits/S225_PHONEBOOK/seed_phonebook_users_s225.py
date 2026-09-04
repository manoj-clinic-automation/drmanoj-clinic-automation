#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_phonebook_users_s225.py -- writes ONE setting row in finance.db: purchase.phonebook_users =
"manoj,darpan,shavez" (the owner: "I and Darpan and Shavez should have access to the stockist phone book").
Idempotent: an existing row is left as it is and printed. Touches nothing else.
    FINANCE_DB=/root/finance/finance.db /root/wa/venv/bin/python3 -B seed_phonebook_users_s225.py"""
import os, sqlite3, sys
DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
KEY, USERS = "purchase.phonebook_users", "manoj,darpan,shavez"
if not os.path.exists(DB):
    sys.exit("REFUSING: %s not found" % DB)
con = sqlite3.connect(DB)
con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
r = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()
if r is not None:
    print("setting %s already = %r -- left as it is" % (KEY, r[0]))
else:
    cols = {x[1] for x in con.execute("PRAGMA table_info(setting)")}
    if "note" in cols:
        con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?)",
                    (KEY, USERS, "S225 phone book editors -- the owner's list of 04-Sep-2026; the doctor always"))
    else:
        con.execute("INSERT INTO setting (key, value) VALUES (?,?)", (KEY, USERS))
    con.commit()
    print("setting %s = %r written" % (KEY, USERS))
con.close()
