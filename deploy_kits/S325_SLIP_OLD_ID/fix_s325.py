#!/usr/bin/env python3
"""fix_s325.py -- the one correction S325 makes to data already written (19-Sep-2026, the first live
morning): a slip whose clinic ID is AT OR BELOW the highest ID the patient master knows was marked NEW
because the master has no row for that ID (2681 was the owner's example). Such a slip is an old patient:
is_new -> 0. Only the slip table, only those rows; a second run changes nothing.
Usage: fix_s325.py DB_PATH"""
import sqlite3
import sys

con = sqlite3.connect(sys.argv[1], timeout=30)
if not con.execute("SELECT 1 FROM sqlite_master WHERE name='slip'").fetchone():
    print("fix: no slip table yet -- nothing to correct")
    sys.exit(0)
hi = con.execute("SELECT MAX(CAST(clinic_id AS INTEGER)) FROM patient_ref WHERE clinic_id GLOB '[0-9]*'").fetchone()[0] or 0
n = con.execute("UPDATE slip SET is_new=0 WHERE is_new=1 AND clinic_id GLOB '[0-9]*' "
                "AND CAST(clinic_id AS INTEGER) <= ?", (hi,)).rowcount
con.commit()
print("fix: %d slip(s) corrected from NEW to old patient (highest known ID %d)" % (n, hi))
