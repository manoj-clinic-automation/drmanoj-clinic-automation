#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s443.py -- kit S443_DOCTERZ_PICKUP. docterz_pickup.py's own rules on a SCRATCH COPY of finance.db and a scratch
store, with crafted exports (names and numbers invented here: 'W443 Walk', 9-digit fakes) -- Drive is not touched. Then the
owner's money page (the real clinic_money.py beside it, when S442's hook is there) through the finance app's test client.

  --app DIR (a copy of /root/finance carrying docterz_pickup.py) --db PATH
"""
import argparse
import datetime as dt
import os
import sqlite3
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--app", required=True)
ap.add_argument("--db", required=True)
a = ap.parse_args()
a.app, a.db = os.path.abspath(a.app), os.path.abspath(a.db)
assert "scratch" in a.db or "walk" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
store = os.path.join(os.path.dirname(a.db), "w443_store")
os.environ["DOCTERZ_EXPORT_STORE"] = store
os.environ["FINANCE_DB"] = a.db
sys.path.insert(0, a.app)
import docterz_pickup as P  # noqa: E402

n, fails = 0, []


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


con = sqlite3.connect(a.db, timeout=30)
con.row_factory = sqlite3.Row
P.ensure(con)
con.execute("DELETE FROM docterz_export WHERE drive_id LIKE 'w443%'")
D1 = "2030-03-04"                                                    # a Monday, far ahead: no real row can be touched


def cons(day, k):
    head = "Sr No,Patient UID,Patient Name,Clinic Specific Id,Mobile,Consultation Date,Mode Of Payment,Bill Amount\n"
    clinic = ",,,,,,,\n".replace(",,", "Dr. Manoj Agarwal Clinic,,", 1)
    d = dt.date.fromisoformat(day).strftime("%d-%m-%Y")
    return (head + clinic + "".join("%d,W443U%d,W443 Walk %d,%d,W443MOB%d,%s 10:15 AM,Cash,600\n" % (i, i, i, 990000 + i, i % 10, d)
                                    for i in range(1, k + 1))).encode()


def fu(due, k):
    d = dt.date.fromisoformat(due).strftime("%d-%m-%Y")
    return ("Appointment ID,Patient Name,Mobile No,Followup Date\n" + "".join("W443A%d,W443 Walk %d,W443MOB%d,%s\n" % (i, i, i % 10, d)
                                                                         for i in range(1, k + 1))).encode()


def f(i, mt):
    return {"id": "w443%03d" % i, "name": "anything_%d.csv" % i, "modifiedTime": "2030-03-05T0%d:00:00Z" % mt}


r1 = P.take(con, f(1, 1), cons(D1, 12))
r2 = P.take(con, f(2, 2), cons(D1, 12))                              # the same bytes again
r3 = P.take(con, f(3, 3), cons(D1, 14))                              # a newer export with more rows: replaces
r4 = P.take(con, f(4, 4), cons(D1, 9))                               # a newer export with FEWER rows: quarantined
r5 = P.take(con, f(5, 5), fu("2030-03-05", 7))                       # the follow-up log: its day = due - 1
r6 = P.take(con, f(6, 6), b"Item,Qty\nA,1\n")                         # neither report
r7 = P.take(con, {"id": "w443007", "name": "consultation_report_2030-03-09.csv", "modifiedTime": "2030-03-05T07:00:00Z"}, cons(D1, 15))
check("CONTENT: a consultation report is known by its columns and dated by its latest consultation (not the file name)",
      r1[:4] == ("consultation", D1, 12, "current") and r7[:2] == ("consultation", D1), (r1, r7))
check("DUPLICATE: the same bytes again change nothing", r2[3] == "duplicate", r2)
check("REPLACE: a newer export with more rows replaces the day (the old one kept as superseded)", r3[3] == "current", r3)
check("QUARANTINE: a newer export with FEWER rows is set aside and shouted, never taken", r4[3] == "quarantined" and "FEWER" in r4[4], r4)
check("FOLLOW-UP: the follow-up log is known by its columns; its day is the due date minus one", r5[:4] == ("followup", "2030-03-04", 7, "current"), r5)
check("UNKNOWN: anything else is recorded and left alone", r6[0] == "unknown" and r6[3] == "unknown", r6)
cur = [dict(x) for x in con.execute("SELECT drive_id, status, rows FROM docterz_export WHERE kind='consultation' AND business_date=? ORDER BY id", (D1,))]
check("ONE DAY = ONE CURRENT EXPORT: exactly one current consultation report for the day (the newest with the most rows)",
      [x["status"] for x in cur].count("current") == 1 and [x for x in cur if x["status"] == "current"][0]["drive_id"] == "w443007", cur)
mode = oct(os.stat([x for x in con.execute("SELECT stored FROM docterz_export WHERE drive_id='w443007'")][0][0]).st_mode & 0o777)
check("STORE: the bytes stay on the box, readable by root only", mode == "0o600", mode)
# the alarm: Tuesday 09:59 nothing; 10:01 red when Monday has no export; heals once it lands; Monday's alarm asks for Saturday
D2 = "2030-03-12"                                                    # Tuesday; Monday 11-Mar has nothing
lines_a = P.owner_lines(con, dt.datetime.fromisoformat(D2 + "T09:59:00"))
lines_b = P.owner_lines(con, dt.datetime.fromisoformat(D2 + "T10:01:00"))
P.take(con, f(8, 8), cons("2030-03-11", 5))
lines_c = P.owner_lines(con, dt.datetime.fromisoformat(D2 + "T10:30:00"))
lines_d = P.owner_lines(con, dt.datetime.fromisoformat("2030-03-11T10:30:00"))
check("ALARM: nothing before 10:00; a red line after it while the last working day has no export", not [x for x in lines_a if "No Docterz export" in x]
      and [x for x in lines_b if "No Docterz export for Mon 11-Mar" in x], (lines_a, lines_b))
check("ALARM: it heals by itself the moment the export lands", not [x for x in lines_c if "No Docterz export" in x], lines_c)
check("ALARM: on a Monday it asks for Saturday (Sunday is closed)", [x for x in lines_d if "Sat 09-Mar" in x], lines_d)
con.execute("DELETE FROM docterz_export WHERE drive_id LIKE 'w443%'")
con.commit()
print("WALK_S443 %s -- %d checks, %d failed%s" % ("GREEN" if not fails else "RED", n, len(fails), (": " + "; ".join(fails)) if fails else ""))
sys.exit(0 if not fails else 1)
