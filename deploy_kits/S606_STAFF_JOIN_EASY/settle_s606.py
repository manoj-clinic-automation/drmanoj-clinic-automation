#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""settle_s606.py -- kit S606's data step: the same _settle() the Add-staff page runs on
every open, run once now so the owner's page opens already settled.

    python3 settle_s606.py FINANCE_DIR [report|apply]

report: says what would change, changes nothing.   apply: changes it.
Idempotent: a second apply changes nothing. Live paths come from the same env/defaults
the service uses (FINANCE_DB, STAFF_EASY_SR_DB, ATT_STAFF_MASTER, CLINIC_USERS_FILE).
"""
import os
import sqlite3
import sys

fdir, mode = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "report")
sys.path.insert(0, fdir)
sys.dont_write_bytecode = True
import joiner_app as J  # noqa: E402
import staff_easy as E  # noqa: E402

fin = sqlite3.connect(os.environ.get("FINANCE_DB", os.path.join(fdir, "finance.db")), timeout=15)
fin.row_factory = sqlite3.Row
J._db = lambda: fin
J.ensure_schema(fin)
rows = fin.execute("SELECT ref,person,username FROM joiner WHERE kind='JOIN' AND status!='COMPLETE'").fetchall()
print("    open joinings: %d" % len(rows))
for r in rows:
    u = r["username"] or ""
    flag = " -- login has a space/capitals, will become '%s'" % E._pick_username(fin, r["person"], own_ref=r["ref"]) \
        if (u and E._clean(u) != u) else ""
    print("      %s  %s  login '%s'%s" % (r["ref"], r["person"], u or "-", flag))
if mode != "apply":
    sys.exit(0)
sr = E._sr()
try:
    notes = E._settle(fin, sr, "Claude (kit S606)")
finally:
    sr.close()
print("    settled: %s" % ("; ".join(notes) if notes else "nothing to change"))
