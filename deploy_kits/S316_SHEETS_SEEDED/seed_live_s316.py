#!/usr/bin/env python3
"""seed_live_s316.py -- loads the two lists into the LIVE tables and prints what is there, so the
install proves itself rather than the owner discovering it on the page. Idempotent: owner_sheets.seed
never overwrites a row he has touched. Usage: seed_live_s316.py FINANCE_DIR FINANCE_DB"""
import sqlite3
import sys

fin, dbp = sys.argv[1], sys.argv[2]
sys.path.insert(0, fin)
import owner_sheets  # noqa: E402

owner_sheets.SEED_DIR = fin
con = sqlite3.connect(dbp)
con.row_factory = sqlite3.Row
owner_sheets.ensure(con)
rows = owner_sheets.services(con)
x = [r for r in rows if r["kind"] == "xray"]
p = [r for r in rows if r["kind"] == "proc"]
print("SEEDED x-rays %d · procedures %d · waiting for him %d · already answered %d"
      % (len(x), len(p),
         len([r for r in rows if r["status"] == "pending"]),
         len([r for r in rows if r["status"] != "pending"])))
