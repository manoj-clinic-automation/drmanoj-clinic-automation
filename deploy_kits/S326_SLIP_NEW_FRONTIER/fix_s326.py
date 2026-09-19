#!/usr/bin/env python3
"""fix_s326.py -- re-decides NEW on every slip already written, by the S326 rule (19-Sep-2026):
a slip is NEW when its clinic ID is above the highest ID issued BEFORE the slip's day (Docterz day
lines, visits, and master rows actually seen). It undoes S325's over-correction, which had used a
stray master row as the ceiling and so called today's genuine new patients old. slip table only,
column is_new only; a second run changes nothing.
Usage: fix_s326.py DB_PATH"""
import sqlite3
import sys

Q = ("SELECT MAX(CAST(clinic_id AS INTEGER)) FROM clinic_day_line WHERE clinic_id GLOB '[0-9]*' AND business_date<?",
     "SELECT MAX(CAST(clinic_id AS INTEGER)) FROM patient_visit WHERE clinic_id GLOB '[0-9]*' AND visit_date<?",
     "SELECT MAX(CAST(clinic_id AS INTEGER)) FROM patient_ref WHERE clinic_id GLOB '[0-9]*' "
     "AND last_seen IS NOT NULL AND last_seen<>'' AND last_seen<?")


def ceiling(con, day):
    best = 0
    for q in Q:
        try:
            v = con.execute(q, (day,)).fetchone()[0]
        except sqlite3.Error:
            v = None
        if v and int(v) > best:
            best = int(v)
    return best


con = sqlite3.connect(sys.argv[1], timeout=30)
if not con.execute("SELECT 1 FROM sqlite_master WHERE name='slip'").fetchone():
    print("fix: no slip table yet -- nothing to re-decide")
    sys.exit(0)
changed, cache = 0, {}
for sid, day, cid, was in con.execute("SELECT id, day, clinic_id, is_new FROM slip WHERE state='ok' "
                                      "AND clinic_id GLOB '[0-9]*'").fetchall():
    if day not in cache:
        cache[day] = ceiling(con, day)
    now = 1 if (cache[day] and int(cid) > cache[day]) or not cache[day] else 0
    if now != was:
        con.execute("UPDATE slip SET is_new=? WHERE id=?", (now, sid))
        changed += 1
con.commit()
print("fix: %d slip(s) re-decided; ceiling by day %s" % (changed, ", ".join("%s=%d" % kv for kv in sorted(cache.items()))))
