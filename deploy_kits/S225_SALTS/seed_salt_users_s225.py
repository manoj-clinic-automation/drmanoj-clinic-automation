#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_salt_users_s225.py -- ONE setting row in finance.db: purchase.salt_users = "amir" (the owner: the salt list is for
Amir and him; the doctor always by role). Idempotent. FINANCE_DB=/root/finance/finance.db /root/wa/venv/bin/python3 -B seed_salt_users_s225.py"""
import os, sqlite3, sys
DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db"); KEY, USERS = "purchase.salt_users", "amir"
if not os.path.exists(DB): sys.exit("REFUSING: %s not found" % DB)
con = sqlite3.connect(DB)
con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
r = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()
if r is not None: print("setting %s already = %r -- left as it is" % (KEY, r[0]))
else:
    cols = {x[1] for x in con.execute("PRAGMA table_info(setting)")}
    if "note" in cols: con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?)", (KEY, USERS, "S225 salt-list editors; the doctor always"))
    else: con.execute("INSERT INTO setting (key, value) VALUES (?,?)", (KEY, USERS))
    con.commit(); print("setting %s = %r written" % (KEY, USERS))
con.close()
