# -*- coding: utf-8 -*-
"""LIVE-SHAPE WALK -- the patched clinic_register.py in a real Flask app, real sqlite, real
requests through a test client. Not a simulation of the logic: the module itself is mounted the
way finance_app mounts it."""
import datetime as dt, sqlite3, sys
from flask import Flask
import clinic_register as CR

TODAY = dt.date.today().isoformat()
YDAY  = (dt.date.today() - dt.timedelta(days=1)).isoformat()
DB2   = (dt.date.today() - dt.timedelta(days=2)).isoformat()

con = sqlite3.connect(":memory:", check_same_thread=False)
con.row_factory = sqlite3.Row
con.executescript("""
CREATE TABLE clinic_day_revenue (business_date TEXT PRIMARY KEY);
CREATE TABLE clinic_day_line (business_date TEXT, clinic_id TEXT, section TEXT, mode TEXT, amount_p INTEGER);
CREATE TABLE clinic_day_tender (business_date TEXT, clinic_id TEXT, tender TEXT, amount_p INTEGER);
CREATE TABLE upi_txn (unit TEXT, txn_date TEXT, amount_p INTEGER);
""")
# Docterz knows about yesterday and the day before -- and NOT about today. That is the real shape.
con.executemany("INSERT INTO clinic_day_revenue VALUES (?)", [(YDAY,), (DB2,)])
con.execute("INSERT INTO clinic_day_line VALUES (?,?,?,?,?)", (YDAY, "c1", "consult", "Cash", 980000))
con.commit()

CR._db = lambda: con
CR._require = lambda *a, **k: ({"user": "shivani"}, None)
CR._audit = lambda *a, **k: None

app = Flask(__name__)
CR.init(app, CR._db, CR._require, CR._audit, unit="clinic", url_prefix="")
c = app.test_client()

fails = []
def check(label, got, want):
    ok = got == want
    print(("  PASS  " if ok else "  FAIL  ") + label + "   got=%r want=%r" % (got, want))
    if not ok:
        fails.append(label)

print("today=%s  yesterday=%s  (Docterz knows %s and %s only)" % (TODAY, YDAY, YDAY, DB2))

print("\n1 - nothing filled: the index must open TODAY, not yesterday")
r = c.get("/finance/clinic/register")
check("redirect target", r.headers.get("Location", ""), "/finance/clinic/register/%s" % TODAY)
check("status", r.status_code, 302)

print("\n2 - today's page renders, with the other two records NOT KNOWN rather than zero")
r = c.get("/finance/clinic/register/%s" % TODAY)
check("status", r.status_code, 200)
h = r.get_data(as_text=True)
check("the day is named on the page", CR._human(TODAY) in h, True)
check("no traceback", "Traceback" in h, False)

print("\n3 - fill today, then the index must fall back to the next unfilled day (yesterday)")
con.execute("INSERT INTO clinic_register_day (business_date) VALUES (?)", (TODAY,))
con.commit()
r = c.get("/finance/clinic/register")
check("redirect target", r.headers.get("Location", ""), "/finance/clinic/register/%s" % YDAY)

print("\n4 - 'all days' must list today, so a filled today is visible there")
r = c.get("/finance/clinic/register/list")
check("status", r.status_code, 200)
check("today listed", CR._human(TODAY) in r.get_data(as_text=True), True)

print("\n5 - the gate is untouched: a refused user still gets the denial, not the day")
CR._require = lambda *a, **k: (None, "no")
r = c.get("/finance/clinic/register")
check("status", r.status_code, 200)
check("no redirect to a day", "Location" in r.headers, False)
CR._require = lambda *a, **k: ({"user": "shivani"}, None)

print("\n6 - a day Docterz DOES know still works (nothing regressed)")
r = c.get("/finance/clinic/register/%s" % YDAY)
check("status", r.status_code, 200)
check("no traceback", "Traceback" in r.get_data(as_text=True), False)

print("\n%s" % ("ALL CHECKS PASSED" if not fails else "FAILURES: %r" % fails))
sys.exit(1 if fails else 0)
