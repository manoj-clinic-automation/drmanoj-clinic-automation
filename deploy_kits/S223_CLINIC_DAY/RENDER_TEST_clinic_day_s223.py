#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RENDER_TEST_clinic_day_s223.py -- mount the real blueprint on a real Flask app, over a real
database filled by the real ingester, and read what a browser would actually receive.

A page is not proven by reading its source (F-289: a wrong code point rendered as a Devanagari
letter and passed every text check). This asks the app for the page over HTTP and asserts on the
bytes that come back.

    python3 -B RENDER_TEST_clinic_day_s223.py /path/to/xlsx_dir
"""
import glob, os, re, sqlite3, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flask import Flask
import docterz_ingest as ING
import finance_clinic_day as CD

F = []
def ck(l, c, d=""):
    print("  %s  %s%s" % ("PASS" if c else "FAIL", l, ("   [%s]" % d) if d else ""))
    if not c: F.append(l)

SRC = sys.argv[1] if len(sys.argv) > 1 else "/tmp/xlsx"
paths = sorted(glob.glob(os.path.join(SRC, "Staff_Action_Today_*.xlsx")))
BY = {os.path.basename(p): p for p in paths}
ING.fetch_bytes = lambda fid: open(BY[fid], "rb").read()
ING.list_day_files = lambda: [(os.path.basename(p), os.path.basename(p),
                               "2026-09-04T00:00:00Z") for p in paths]
db = os.path.join(tempfile.mkdtemp(), "t.db")
sys.argv = ["x", "--db", db]
print("-- 0  fill the store with the real ingester --------------------------")
ck("ingest ran clean", ING.main() == 0)

# a real app, the real blueprint, a real gate
ROLE = {"who": "checker"}
def _db():
    c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
def _require(*roles, unit="clinic"):
    if ROLE["who"] in roles:
        return {"user": "manoj", "roles": [ROLE["who"]]}, None
    return None, ("forbidden", 403)
app = Flask(__name__)
CD.init(app, _db, _require, unit="clinic", url_prefix="")
cl = app.test_client()

print("\n-- 1  the page renders, and the gate is real -------------------------")
r = cl.get("/finance/clinic/day")
ck("HTTP 200 for a clinic checker", r.status_code == 200, str(r.status_code))
html = r.get_data(as_text=True)
ck("it is a complete HTML document", html.startswith("<!doctype html") and html.rstrip().endswith("</html>"))
ROLE["who"] = "nobody"
r2 = cl.get("/finance/clinic/day")
h2 = r2.get_data(as_text=True)
ck("someone with no clinic role is refused, in words not a stack trace",
   "Not permitted" in h2 and "₹" not in h2)
ck("the refusal leaks no money at all", not re.search(r"\d{1,3},\d{3}", h2))
ROLE["who"] = "checker"

print("\n-- 2  the numbers on the page ARE the numbers in the table -----------")
con = _db()
rows = list(con.execute("SELECT * FROM clinic_day_revenue ORDER BY business_date DESC"))
newest = rows[0]
r = cl.get("/finance/clinic/day?m=%s" % newest["business_date"][:7])
html = r.get_data(as_text=True)
want = "{:,}".format(int(round(newest["total_amount_p"] / 100.0)))
ck("the newest day's total appears on the page (Rs %s)" % want, want in html)
month = newest["business_date"][:7]
mrows = [x for x in rows if x["business_date"].startswith(month)]
mtot = "{:,}".format(int(round(sum(x["total_amount_p"] for x in mrows) / 100.0)))
ck("the month footer total is the sum of its own days (Rs %s over %d days)" % (mtot, len(mrows)),
   mtot in html)
ck("every day of that month has a row", all(
    __import__("datetime").date(int(x["business_date"][:4]), int(x["business_date"][5:7]),
                                int(x["business_date"][8:10])).strftime("%d-%b-%Y") in html
    for x in mrows))

print("\n-- 3  D367: the sheet's own figures are NOWHERE on the page ----------")
# A sheet figure that EQUALS the row-derived one is not a leak -- it is the same number, and on
# most days the two agree. The only thing that can prove a leak is a day where they DIFFER.
# (F-293: a test's own incompleteness must not be reportable as the subject's fault.)
import json as _json
leaked, tested = [], 0
for x in rows:
    if not x["business_date"].startswith(month):
        continue
    t = CD._tender(x)
    for col, key in (("sheet_cash_p", "cash"), ("sheet_online_p", "online")):
        v = x[col]
        if v is None or v == t[key]:
            continue                      # they agree; the number is legitimately on the page
        tested += 1
        s = "{:,}".format(int(round(v / 100.0)))
        if s in html:
            leaked.append((x["business_date"], col, s))
ck("on days where the sheet DISAGREES with the lines, the sheet's figure is not shown "
   "(%d such figures in this month)" % tested, not leaked, str(leaked[:3]))
ck("the word 'variance' never reaches the reader", "variance" not in html.lower())

print("\n-- 4  print and PDF ---------------------------------------------------")
ck("a Print / Save as PDF control exists", "Print / Save as PDF" in html)
ck("the print stylesheet hides the navigation", "@media print" in html and ".noprint" in html)
ck("no <script> tag anywhere -- nothing to fail silently", "<script" not in html.lower())

print("\n-- 5  the empty and missing cases say so ------------------------------")
r = cl.get("/finance/clinic/day?m=2019-01")
ck("a month with no data says so instead of showing zero",
   "No days stored for this month" in r.get_data(as_text=True))
empty = os.path.join(tempfile.mkdtemp(), "e.db")
def _edb():
    c = sqlite3.connect(empty); c.row_factory = sqlite3.Row; return c
app2 = Flask(__name__); CD._db = _edb
r = app2.test_client() if False else None
CD._db = _edb
r = cl.get("/finance/clinic/day")
ck("with no table at all the page is empty and says so, not a 500",
   "Nothing read yet" in r.get_data(as_text=True))
CD._db = _db

print("\n-- 6  F-185 ----------------------------------------------------------")
r = cl.get("/finance/clinic/day?m=%s" % month)
html = r.get_data(as_text=True)
ck("no mobile-shaped number on the page", not re.search(r"[6-9]\d{9}", html))
ck("no Docterz patient-UID shape on the page", not re.search(r"\b[A-Z]{5}\d{5}\b", html))

print("\n%s  %d checks, %d failed" % ("RED" if F else "GREEN", 16, len(F)))
sys.exit(1 if F else 0)
