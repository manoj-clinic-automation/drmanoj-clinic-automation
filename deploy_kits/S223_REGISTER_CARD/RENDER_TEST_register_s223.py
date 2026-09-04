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
def _h(iso):
    return CR._human(iso)
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
# THE DB GETTER MUST BEHAVE LIKE THE REAL ONE. finance_app's db() lives on flask.g and RAISES
# outside an application context. The first version of this test handed the module a plain
# connector that worked anywhere, so init() calling db() passed here and 503'd the whole finance
# app on the box. That is F-286 exactly: a walk that supplies its own scaffolding proves the
# scaffolding. This getter now refuses outside a request, like the real one.
from flask import has_app_context
def _db_like_the_box():
    if not has_app_context():
        raise RuntimeError("Working outside of application context")
    return _db()

app = Flask(__name__)
CR.init(app, _db_like_the_box, _require, _audit, unit="clinic", url_prefix="")
cl = app.test_client()

print("-- 0  init() must not touch the database -----------------------------")
ck("init() completed with NO application context, exactly as gunicorn imports it", True)
ck("and it created NO table yet -- nothing ran at import time", not bool(_db().execute(
    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='clinic_register_day'").fetchone()))

print("\n-- 1  the schema and the gate ---------------------------------------")
cl.get("/finance/clinic/register")
ck("the table is created on FIRST REQUEST instead", bool(_db().execute(
    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='clinic_register_day'").fetchone()))
# the entry point now REDIRECTS to the next unfilled day (minimum taps), so follow it
ck("the entry point answers for a clinic maker",
   cl.get("/finance/clinic/register", follow_redirects=True).status_code == 200)
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

print("\n-- 8  the owner's changes of 04-Sep ----------------------------------")
# dressing + physio
big = {"cons_cash_p":"1000","cons_upi_p":"0","cons_card_p":"0","xray_cash_p":"0","xray_upi_p":"0",
       "xray_card_p":"0","proc_cash_p":"0","proc_upi_p":"0","proc_card_p":"0",
       "dress_cash_p":"300","dress_upi_p":"200","dress_card_p":"0",
       "physio_cash_p":"700","physio_upi_p":"400"}
cl.post("/finance/clinic/register/%s" % DAY, data=big)
w = _db()
rr = w.execute("SELECT * FROM clinic_register_day WHERE business_date=?", (DAY,)).fetchone()
pr = w.execute("SELECT * FROM clinic_physio_day WHERE business_date=?", (DAY,)).fetchone()
ck("dressing is stored on its own line", rr["dress_cash_p"] == 30000 and rr["dress_upi_p"] == 20000)
ck("physio went to its OWN table, not the register table", pr is not None
   and pr["cash_p"] == 70000 and pr["upi_p"] == 40000)
ck("physio is not a column of the register table", "physio_cash_p" not in rr.keys())
t = CR.three_way(_db(), DAY)
ck("dressing CLUBS into the register totals (1000+300 cash, 0+200 upi)",
   t["r_cash"] == 130000 and t["r_upi"] == 20000)
h = cl.get("/finance/clinic/register/%s" % DAY).get_data(as_text=True)
ck("the card shows a Dressing row", "Dressing" in h)
ck("and says it counts with Procedures", "counts with Procedures" in h)
ck("the card shows a Physiotherapy row", "Physiotherapy" in h)
ck("physio has no card box -- cash and UPI only, as asked",
   h.count("physio_cash_p") == 1 and h.count("physio_upi_p") == 1 and "physio_card_p" not in h)

print("\n-- 8b  physio is OUT of the bank arithmetic --------------------------")
w2 = _db()
doc2 = CR.docterz_day(w2, DAY)
w2.execute("UPDATE clinic_register_day SET cons_upi_p=?, xray_upi_p=0, proc_upi_p=0, dress_upi_p=0 "
           "WHERE business_date=?", (doc2["upi"], DAY))
w2.execute("UPDATE clinic_physio_day SET upi_p=? WHERE business_date=?", (77700, DAY))
w2.execute("DELETE FROM upi_txn")
w2.execute("INSERT INTO upi_txn (unit,txn_date,amount_p,mode) VALUES ('clinic',?,?,'UPI')",
           (DAY, doc2["upi"]))
w2.commit()
t2 = CR.three_way(_db(), DAY)
ck("with physio present on its own channel, all three still AGREE",
   t2["verdict"] == "all agree", "%s (physio was Rs 777)" % t2["verdict"])
h2 = cl.get("/finance/clinic/register/%s" % DAY).get_data(as_text=True)
ck("the screen says physio is on its own channel and not in the bank line",
   "own UPI channel" in h2 and "not in the bank line" in h2)
ck("and it never claims the bank line includes physio", "includes physio" not in h2)

print("\n-- 9  minimum taps, and a filled day disappears ----------------------")
r = cl.get("/finance/clinic/register")
ck("the entry point REDIRECTS straight to a day, it does not show a list first",
   r.status_code in (301, 302), str(r.status_code))
lst = cl.get("/finance/clinic/register/list").get_data(as_text=True)
ck("the filled day is still reachable from 'all days'", DAY[8:10] in lst or _h(DAY) in lst)
todo = cl.get("/finance/clinic/register", follow_redirects=True).get_data(as_text=True)
ck("the filled day is NOT offered again as something to fill",
   ("Days still to fill" not in todo) or (CR._human(DAY) not in
    todo.split("Days still to fill")[-1].split("</table>")[0]))

print("\n-- 10  clearing an accidental save -----------------------------------")
h = cl.post("/finance/clinic/register/%s" % DAY, data={"clear": "yes"}).get_data(as_text=True)
ck("it says it cleared", "Cleared." in h)
ck("the register row is gone",
   _db().execute("SELECT COUNT(*) c FROM clinic_register_day WHERE business_date=?",
                 (DAY,)).fetchone()["c"] == 0)
ck("the physio row went with it",
   _db().execute("SELECT COUNT(*) c FROM clinic_physio_day WHERE business_date=?",
                 (DAY,)).fetchone()["c"] == 0)
ck("the removal was audited", any(a[2] == "delete" for a in AUD))

print("\n-- 11  readable on a phone -------------------------------------------")
h = cl.get("/finance/clinic/register/%s" % DAY).get_data(as_text=True)
import re as _re
sizes = [float(x) for x in _re.findall(r"font-size:\s*([0-9.]+)px", h)]
ck("no font on the page is under 15px (smallest is %spx)" % (min(sizes) if sizes else "n/a"),
   sizes and min(sizes) >= 15)
ck("the entry boxes have a real border, not a hairline", "border:2px solid #5b6b76" in h)
ck("tap targets are at least 54px tall", "min-height:54px" in h)
ck("the page is not on stark white", "--bg:#dfe5e9" in h)
ck("it has a phone breakpoint", "@media (max-width:620px)" in h)
ck("the viewport allows zooming (never disable it)", "maximum-scale=5" in h
   and "user-scalable=no" not in h)

print("\n-- 12  the end-of-day drawer count ------------------------------------")
# a clean day: register cash 1000+300 (dressing) + physio cash 700 = 2000
base = {"cons_cash_p":"1000","cons_upi_p":"0","cons_card_p":"0","xray_cash_p":"0","xray_upi_p":"0",
        "xray_card_p":"0","proc_cash_p":"0","proc_upi_p":"0","proc_card_p":"0",
        "dress_cash_p":"300","dress_upi_p":"0","dress_card_p":"0",
        "physio_cash_p":"700","physio_upi_p":"0"}
cl.post("/finance/clinic/register/%s" % DAY, data=base)
ck("expected cash = register cash PLUS physio cash (1000+300+700)",
   CR.expected_cash_p(_db(), DAY) == 200000, str(CR.expected_cash_p(_db(), DAY)))
h = cl.get("/finance/clinic/register/%s" % DAY).get_data(as_text=True)
ck("the count asks for QUANTITIES, not an amount", "How many" in h and "data-rs=" in h)
ck("every note denomination is offered", all(("name='n%d'" % d) in h for d in (500,200,100,50,20,10)))
ck("coins are offered, at the bottom", ">Coins<" in h and "name='c1'" in h)
ck("the coin band comes after the note band", h.index(">Coins<") > h.index(">Notes<"))
# an exact count
exact = {"drawer":"count","n500":"3","n200":"2","n100":"1"}   # 1500+400+100 = 2000
h = cl.post("/finance/clinic/register/%s" % DAY, data=exact).get_data(as_text=True)
dr = _db().execute("SELECT * FROM clinic_drawer_day WHERE business_date=?", (DAY,)).fetchone()
ck("the quantities are stored as quantities", dr["n500"] == 3 and dr["n200"] == 2)
ck("it sums them itself (3x500 + 2x200 + 1x100 = 2,000)", dr["counted_p"] == 200000)
ck("it says the drawer matches the day", "exactly what the day" in h)
ck("and offers the handover", "handed over, correct" in h and "Count again" in h)
ck("it defaults the handover to Dr Bhawna", "Dr Bhawna" in h)
ck("status starts as counted, not confirmed", dr["status"] == "counted")
# confirm
h = cl.post("/finance/clinic/register/%s" % DAY,
            data={"drawer":"confirm","handed_to":"Dr Bhawna"}).get_data(as_text=True)
dr = _db().execute("SELECT * FROM clinic_drawer_day WHERE business_date=?", (DAY,)).fetchone()
ck("confirming records the handover", dr["status"] == "confirmed" and bool(dr["confirmed_at"]))
ck("and it is audited", any(a[2] == "confirm" for a in AUD))
# a short count
cl.post("/finance/clinic/register/%s" % DAY, data={"drawer":"recount"})
ck("recount clears it",
   _db().execute("SELECT COUNT(*) c FROM clinic_drawer_day").fetchone()["c"] == 0)
h = cl.post("/finance/clinic/register/%s" % DAY,
            data={"drawer":"count","n500":"3","n200":"1"}).get_data(as_text=True)  # 1500+200=1700
flat12 = " ".join(h.split()).lower()
ck("a short drawer states both figures and the difference (1,700 vs 2,000, short 300)",
   "1,700" in h and "2,000" in h and "300" in h)
ck("it says 'less in the drawer', never that anyone is short",
   "less in the drawer" in flat12 and "is short" not in flat12 and "shortage" not in flat12)
ck("it offers a recount rather than a verdict", "count again" in flat12)
# a bad quantity
h = cl.post("/finance/clinic/register/%s" % DAY,
            data={"drawer":"count","n500":"three"}).get_data(as_text=True)
ck("a word where a count should be is refused, nothing saved",
   "Nothing was saved" in h and "not a whole number" in h)
ck("the previous count survives the refusal",
   _db().execute("SELECT counted_p FROM clinic_drawer_day WHERE business_date=?",
                 (DAY,)).fetchone()["counted_p"] == 170000)

print("\n-- 13  the drawer CLOSES the loop with the bank ------------------------")
# Build one honest day: Docterz says UPI 1000 / cash 2000. The counter rang a 300 UPI bill as
# cash, so the register says cash 2300 / UPI 700 -- and the drawer will be 300 light while the
# bank is 300 over. Two records, opposite directions, same mistake.
w3 = _db()
w3.execute("DELETE FROM clinic_drawer_day"); w3.execute("DELETE FROM upi_txn")
w3.execute("DELETE FROM clinic_day_line WHERE business_date=?", (DAY,))
# DOCTERZ carries the mistake: the 300 bill was RUNG AS CASH, so Docterz reads cash 2300 /
# UPI 700. The bank still received 1000, because the money really did travel by UPI.
w3.executemany("INSERT INTO clinic_day_line (business_date,section,sn,patient,clinic_id,amount_p,"
               "mode,shift) VALUES (?,?,?,?,?,?,?,?)",
               [(DAY,"consult",1,"A","111",230000,"Cash","Morning"),
                (DAY,"consult",2,"B","222",70000,"Online Payment","Morning")])
w3.execute("INSERT INTO upi_txn (unit,txn_date,amount_p,mode) VALUES ('clinic',?,?,'UPI')",
           (DAY, 100000))
w3.commit()
cl.post("/finance/clinic/register/%s" % DAY, data={
    "cons_cash_p":"2300","cons_upi_p":"700","cons_card_p":"0","xray_cash_p":"0","xray_upi_p":"0",
    "xray_card_p":"0","proc_cash_p":"0","proc_upi_p":"0","proc_card_p":"0",
    "dress_cash_p":"0","dress_upi_p":"0","dress_card_p":"0",
    "physio_cash_p":"0","physio_upi_p":"0"})
ck("expected drawer cash follows the register (2,300)",
   CR.expected_cash_p(_db(), DAY) == 230000)
# drawer holds only 2000 -- 4x500
h = cl.post("/finance/clinic/register/%s" % DAY,
            data={"drawer":"count","n500":"4"}).get_data(as_text=True)
t3 = CR.three_way(_db(), DAY)
ck("the drawer is 300 light", t3["drawer_diff"] == -30000)
ck("the bank is 300 over", t3["bank_diff"] == 30000)
ck("the two are recognised as the SAME mistake", t3["closed"] is True)
flat13 = " ".join(h.split())
ck("the screen says so, in words, with the figure",
   "short by exactly what the bank is over" in flat13 and "300" in flat13)
ck("and says plainly that no money is missing", "No money is missing" in flat13)
ck("the drawer line appears in the three-record table", "Drawer counted" in flat13)
# make them disagree: bank over by 500 instead
w3.execute("UPDATE upi_txn SET amount_p=? WHERE txn_date=?", (120000, DAY)); w3.commit()
# bank now 1200 vs Docterz 700 = over by 500, while the drawer is only 300 light
t4 = CR.three_way(_db(), DAY)
ck("when they point the same way but do not match, it says that instead",
   t4["closed"] is False and t4["same_way"] is True)
h = cl.get("/finance/clinic/register/%s" % DAY).get_data(as_text=True)
ck("and it says something else is in there too",
   "something else is in there too" in " ".join(h.split()))

print("\n%s  %d checks, %d failed" % ("RED" if F else "GREEN", len(N), len(F)))
sys.exit(1 if F else 0)
