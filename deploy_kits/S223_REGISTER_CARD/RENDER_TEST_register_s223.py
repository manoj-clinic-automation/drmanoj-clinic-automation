#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RENDER_TEST_register_s223.py -- the register card, on a real app over a real database.

It is a WRITE screen, so the test posts real forms and reads the database back, then reads the
delivered HTML. A money form that half-saves is worse than one that refuses, so that is tested too.
"""
import glob, os, re, sqlite3, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/claude/s223d")
from flask import Flask
import docterz_ingest as ING
import clinic_register as CR

F, N = [], []
def ck(l, c, d=""):
    N.append(l); print("  %s  %s%s" % ("PASS" if c else "FAIL", l, ("   [%s]" % d) if d else ""))
    if not c: F.append(l)

SRC = sys.argv[1] if len(sys.argv) > 1 else "/tmp/xlsx"
paths = sorted(glob.glob(os.path.join(SRC, "Staff_Action_Today_*.xlsx")))
BY = {os.path.basename(p): p for p in paths}
ING.fetch_bytes = lambda fid: open(BY[fid], "rb").read()
ING.list_day_files = lambda: [(os.path.basename(p), os.path.basename(p),
                               "2026-09-04T00:00:00Z") for p in paths]
db = os.path.join(tempfile.mkdtemp(), "t.db")
sys.argv = ["x", "--db", db]
import io as _io, contextlib
with contextlib.redirect_stdout(_io.StringIO()):
    ING.main()
con0 = sqlite3.connect(db)
con0.execute("CREATE TABLE upi_txn (id INTEGER PRIMARY KEY, unit TEXT, txn_date TEXT, "
             "amount_p INTEGER, mode TEXT)")
DAY = con0.execute("SELECT business_date FROM clinic_day_revenue "
                   "ORDER BY business_date DESC LIMIT 1").fetchone()[0]
con0.commit()

ROLE = {"who": "maker"}
def _db():
    c = sqlite3.connect(db); c.row_factory = sqlite3.Row; return c
def _require(*roles, unit="clinic"):
    return ({"user": "alisha"}, None) if ROLE["who"] in roles else (None, ("no", 403))
AUD = []
def _audit(con, table, row_id, action, before=None, after=None, who=""):
    AUD.append((table, row_id, action, who))
app = Flask(__name__)
CR.init(app, _db, _require, _audit, unit="clinic", url_prefix="")
cl = app.test_client()

print("-- 1  the schema and the gate ---------------------------------------")
ck("the table was created on init", bool(_db().execute(
    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='clinic_register_day'").fetchone()))
ck("the list renders for a clinic maker", cl.get("/finance/clinic/register").status_code == 200)
ROLE["who"] = "nobody"
d = cl.get("/finance/clinic/register/%s" % DAY).get_data(as_text=True)
ck("someone off the clinic desk is refused, with no money on the page",
   "Not permitted" in d and "₹" not in d)
p = cl.post("/finance/clinic/register/%s" % DAY, data={"cons_cash_p": "9999"})
ck("and cannot POST either", "Not permitted" in p.get_data(as_text=True))
ck("nothing was written by the refused POST",
   _db().execute("SELECT COUNT(*) c FROM clinic_register_day").fetchone()["c"] == 0)
ROLE["who"] = "maker"

print("\n-- 2  a bad number REFUSES, and saves nothing ------------------------")
r = cl.post("/finance/clinic/register/%s" % DAY,
            data={"cons_cash_p": "6000", "cons_upi_p": "12oo", "xray_cash_p": "-5"})
h = r.get_data(as_text=True)
ck("it says nothing was saved", "Nothing was saved" in h)
ck("it names BOTH bad fields", "cons upi" in h and "xray cash" in h)
ck("the database is still empty — no half-save",
   _db().execute("SELECT COUNT(*) c FROM clinic_register_day").fetchone()["c"] == 0)

print("\n-- 3  a good save ----------------------------------------------------")
good = {"cons_cash_p": "6000", "cons_upi_p": "1200", "cons_card_p": "",
        "xray_cash_p": "1500", "xray_upi_p": "500", "xray_card_p": "600",
        "proc_cash_p": "", "proc_upi_p": "", "proc_card_p": "", "note": "counter register"}
h = cl.post("/finance/clinic/register/%s" % DAY, data=good).get_data(as_text=True)
row = _db().execute("SELECT * FROM clinic_register_day WHERE business_date=?", (DAY,)).fetchone()
ck("it saved", row is not None)
ck("rupees became paise", row["cons_cash_p"] == 600000 and row["xray_card_p"] == 60000)
ck("a blank box became a real zero", row["proc_cash_p"] == 0)
ck("who and when are recorded", row["entered_by"] == "alisha" and bool(row["entered_at"]))
ck("the save was audited", any(a[0] == "clinic_register_day" and a[2] == "insert" for a in AUD))
ck("it says it saved", "Saved." in h)
ck("the card comes back filled in, not blank", "6000" in h and "1200" in h)

print("\n-- 4  editing the same day updates, never duplicates -----------------")
good["cons_cash_p"] = "6500"
cl.post("/finance/clinic/register/%s" % DAY, data=good)
rows = list(_db().execute("SELECT * FROM clinic_register_day WHERE business_date=?", (DAY,)))
ck("still exactly one row for the day", len(rows) == 1)
ck("the change took", rows[0]["cons_cash_p"] == 650000)
ck("the first entry's author is kept", rows[0]["entered_by"] == "alisha")
ck("the edit was audited as an update", any(a[2] == "update" for a in AUD))

print("\n-- 5  the three-way verdict, each branch -----------------------------")
w = _db()
doc = CR.docterz_day(w, DAY)
def setreg(upi_p):
    w.execute("UPDATE clinic_register_day SET cons_upi_p=?, xray_upi_p=0, proc_upi_p=0 "
              "WHERE business_date=?", (upi_p, DAY)); w.commit()
def bank(v):
    w.execute("DELETE FROM upi_txn"); 
    if v is not None:
        w.execute("INSERT INTO upi_txn (unit,txn_date,amount_p,mode) VALUES ('clinic',?,?,'UPI')",
                  (DAY, v))
    w.commit()
setreg(doc["upi"]); bank(doc["upi"])
ck("all three agree -> 'all agree'", CR.three_way(_db(), DAY)["verdict"] == "all agree")
bank(doc["upi"] + 50000)
t = CR.three_way(_db(), DAY)
ck("register+docterz agree, bank differs -> points at the FEED", t["verdict"] == "bank differs"
   and "not at the counter" in t["why"])
setreg(doc["upi"] + 50000)
t = CR.three_way(_db(), DAY)
ck("register+bank agree, docterz differs -> points at the ENTRY",
   t["verdict"] == "docterz differs" and "mis-keyed" in t["why"])
setreg(doc["upi"] + 999900)
t = CR.three_way(_db(), DAY)
ck("all three differ -> asks for a person", t["verdict"] == "all differ" and "person" in t["why"])
bank(None)
t = CR.three_way(_db(), DAY)
ck("no statement yet -> 'waiting_bank', never shown as zero",
   t["verdict"] == "waiting_bank" and t["bank"] is None)
h = cl.get("/finance/clinic/register/%s" % DAY).get_data(as_text=True)
ck("the page says the statement has not arrived rather than printing 0",
   "statement not arrived" in h)

print("\n-- 6  it never accuses ------------------------------------------------")
# HTML wraps, so match on whitespace-normalised text -- a phrase split across a line break is
# still on the page (F-293: a test's own crudeness must not be reported as the subject's fault).
flat = " ".join(h.split()).lower()
for phrase in ("shortage", "cash short", "is short", "money is missing", "theft", "fraud",
               "you are responsible"):
    ck("the page never says %r" % phrase, phrase not in flat)
ck("it says plainly that it does not decide who is right",
   "does not decide who is right" in flat)
ck("and that it accuses nobody", "never accuses anyone" in flat)

print("\n-- 7  F-185 ----------------------------------------------------------")
ck("no patient name or id is asked for or shown",
   "Patient" not in h and not re.search(r"[6-9]\d{9}", h))

print("\n%s  %d checks, %d failed" % ("RED" if F else "GREEN", len(N), len(F)))
sys.exit(1 if F else 0)
