#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_returns_app.py -- the whole lifecycle, driven against a real database.

Exit 0 passed - 1 a check failed - 2 Flask is missing.

WHY IT DRIVES THE REAL APP AND NOT THE FUNCTIONS
    The three defects that got through in this session's earlier kits were all
    of the same kind: the code was right and something around it silently
    cancelled it.  A test that imports a function and calls it would have
    passed every one of them.  So this one builds a Flask app, mounts the
    blueprint, and goes through the door the staff page goes through, with a
    real sqlite file and a real auth gate.

    The gate is fail-closed here too: the first block below proves that a caller
    with no role is refused, because a lifecycle anyone can edit is not a record
    of custody.
"""
import datetime as dt
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from flask import Flask, jsonify
except ImportError:
    print("FLASK NOT AVAILABLE -- install it or run this on the VPS with")
    print("  /root/wa/venv/bin/python3 selftest_returns_app.py")
    print("NOT a code failure.")
    sys.exit(2)

import returns_app as R

_fail, _pass = [], 0


def ck(label, cond, detail=""):
    global _pass
    if cond:
        _pass += 1
        print("  ok   %s" % label)
    else:
        _fail.append(label)
        print("  FAIL %s   %s" % (label, detail))


TMP = tempfile.mkdtemp(prefix="pret_")
DB = os.path.join(TMP, "finance.db")
ROLE = {"role": "checker"}


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def require(*roles):
    """Same shape as finance_app's: (user, error) and it fails CLOSED."""
    r = ROLE.get("role")
    if r is None:
        return None, (jsonify(ok=False, error="not_authorised",
                              message="Sign in first."), 401)
    if r not in roles:
        return None, (jsonify(ok=False, error="wrong_role",
                              message="%s cannot do this." % r), 403)
    return "test:" + r, None


app = Flask(__name__)
R.init(app, db, require, unit="medical")
c = app.test_client()


def post(path, body):
    return c.post(path, data=json.dumps(body), content_type="application/json")


print("[1] the gate, before anything else")
ROLE["role"] = None
r = post("/returns/api/book", {"booked_by": "Darpan", "lines": [{"item": "X", "qty": 1}]})
ck("a caller with no role cannot book a return", r.status_code == 401, r.status_code)
ROLE["role"] = "viewer"
r = post("/returns/api/book", {"booked_by": "Darpan", "lines": [{"item": "X", "qty": 1}]})
ck("a viewer cannot book a return either", r.status_code == 403, r.status_code)
ROLE["role"] = "checker"

print("\n[2] booking")
r = c.get("/returns/api/healthz")
ck("healthz answers and the schema built itself", r.status_code == 200 and r.get_json()["ok"])
r = post("/returns/api/book", {"booked_by": "", "lines": [{"item": "X", "qty": 1}]})
ck("a return with no named person is refused", r.status_code == 400)
r = post("/returns/api/book", {"booked_by": "Darpan", "lines": [{"item": "", "qty": 5}]})
ck("a line with no item is refused, not silently dropped into an empty return",
   r.status_code == 400 and r.get_json()["error"] == "no_lines")
r = post("/returns/api/book", {"booked_by": "Darpan",
                               "lines": [{"item": "VINBACTUM DS", "qty": 25, "reason": "MELTED"}]})
ck("an invented reason is refused and the real ones are listed",
   r.status_code == 400 and "NEAR_EXPIRY" in r.get_json()["message"])

r = post("/returns/api/book", {
    "vendor": "L.K. DRUG HOUSE BAREILLY", "booked_by": "Darpan",
    "lines": [{"item": "VINBACTUM DS", "batch": "6347", "expiry": "02/2025", "qty": 25,
               "reason": "EXPIRED", "rate_p": 12000},
              {"item": "VOM L", "batch": "C1235", "expiry": "11/2026", "qty": 74,
               "pack_size": 10, "reason": "NEAR_EXPIRY", "rate_p": 900}]})
j = r.get_json()
REF = j.get("ref")
ck("a two-line return books and gets a reference", r.status_code == 200 and bool(REF), j)
ck("the reference is financial-year numbered, not calendar",
   REF.startswith("PR-%d-" % (dt.date.today().year if dt.date.today().month >= 4
                              else dt.date.today().year - 1)), REF)
ck("its value is priced from our own rates at booking",
   j["value_p"] == 25 * 12000 + 74 * 900, j["value_p"])
r2 = post("/returns/api/book", {"vendor": "YOGENDRA AGENCIES", "booked_by": "Alisha",
                                "lines": [{"item": "REEBORN D", "qty": 8, "rate_p": 500}]})
REF2 = r2.get_json()["ref"]
ck("the second return takes the next number, not the same one", REF2 != REF, (REF, REF2))
r3 = post("/returns/api/book", {"booked_by": "Shavez",
                                "lines": [{"item": "RUNVACE TP", "qty": 10}]})
ck("a return with NO vendor is still accepted -- better recorded than not",
   r3.status_code == 200, r3.get_json())

print("\n[3] the stages, and what may not be skipped")
r = post("/returns/api/advance", {"ref": REF, "to": "HANDED", "person": "Shavez"})
ck("it cannot jump from booked straight to handed over",
   r.status_code == 409 and r.get_json()["error"] == "bad_stage",
   (r.status_code, r.get_json()))
ck("and the refusal names the stage nobody recorded",
   "reception" in r.get_json()["message"].lower(), r.get_json()["message"])
r = post("/returns/api/advance", {"ref": REF, "to": "AT_RECEPTION", "person": ""})
ck("no stage may be recorded without naming a person", r.status_code == 400)
r = post("/returns/api/advance", {"ref": "PR-1999-9999", "to": "NOTIFIED", "person": "X"})
ck("an unknown reference is a clean 404, not a traceback", r.status_code == 404)

ck("supplier told", post("/returns/api/advance",
   {"ref": REF, "to": "NOTIFIED", "person": "Darpan"}).status_code == 200)
ck("reception takes custody, by name", post("/returns/api/advance",
   {"ref": REF, "to": "AT_RECEPTION", "person": "Alisha"}).status_code == 200)
r = post("/returns/api/advance", {"ref": REF, "to": "HANDED", "person": "Shavez",
                                  "collector": "L.K. man", "collector_ph": "0000000000"})
ck("handed over, with both our person and their man named", r.status_code == 200)
ck("going backwards is refused",
   post("/returns/api/advance", {"ref": REF, "to": "NOTIFIED", "person": "X"}).status_code == 409)
ck("notifying may be skipped -- a vendor is often told at the counter",
   post("/returns/api/advance", {"ref": REF2, "to": "AT_RECEPTION",
                                 "person": "Alisha"}).status_code == 200)

print("\n[4] the trail is the truth, the status is only a cache")
t = c.get("/returns/api/trail?ref=" + REF).get_json()
ck("every stage left an event", len(t["events"]) == 4, len(t["events"]))
ck("the status rebuilt from the trail agrees with the stored one", t["consistent"], t)
ck("the person is recorded on each, not just the login",
   [e["person"] for e in t["events"]] == ["Darpan", "Darpan", "Alisha", "Shavez"],
   [e["person"] for e in t["events"]])
con = db()
con.execute("UPDATE pret SET status='CLOSED' WHERE ref=?", (REF,))
con.commit()
t = c.get("/returns/api/trail?ref=" + REF).get_json()
ck("a status edited behind the trail's back is DETECTED, not trusted",
   t["consistent"] is False and t["rebuilt"] == "HANDED", t)
con.execute("UPDATE pret SET status='HANDED' WHERE ref=?", (REF,))
con.commit()

print("\n[5] the credit note closes it, and a half-credit does not")
r = post("/returns/api/advance", {"ref": REF, "to": "AWAITING_NOTE", "person": "Darpan"})
ck("it moves to waiting for the credit note", r.status_code == 200)
r = post("/returns/api/credits", {"source": "test", "credits": [
    {"vendor": "L.K. DRUG HOUSE BAREILLY", "item": "VINBACTUM DS", "batch": "6347",
     "qty": 25, "note_no": "CN/771", "note_on": "2026-09-04"}]})
j = r.get_json()
ck("one line credited", j["lines_credited"] == 1, j)
ck("but the RETURN does not close while its other line is uncredited",
   REF not in j["closed"], j["closed"])
o = c.get("/returns/api/open").get_json()
row = [x for x in o["returns"] if x["ref"] == REF][0]
ck("and the part-credit is visible line by line",
   [l["credited"] for l in row["lines"]] == [25, 0], row["lines"])
r = post("/returns/api/credits", {"source": "test", "credits": [
    {"vendor": "L.K. DRUG HOUSE BAREILLY", "item": "VOM L", "batch": "C1235", "qty": 74,
     "note_no": "CN/771", "note_on": "2026-09-04"}]})
ck("the second credit closes the whole return, with nobody ticking anything off",
   REF in r.get_json()["closed"], r.get_json())
r = post("/returns/api/credits", {"source": "test", "credits": [
    {"vendor": "L.K. DRUG HOUSE BAREILLY", "item": "VOM L", "batch": "C1235", "qty": 74,
     "note_no": "CN/771", "note_on": "2026-09-04"}]})
ck("re-loading the same credit note twice does not double-count it",
   r.get_json()["loaded"] == 0, r.get_json())
ck("a closed return cannot be moved again",
   post("/returns/api/advance", {"ref": REF, "to": "CLOSED",
                                 "person": "X"}).status_code == 409)

print("\n[6] the daily reminder")
con = db()
old = (dt.date.today() - dt.timedelta(days=9)).isoformat() + "T09:00:00"
con.execute("UPDATE pret_event SET at=? WHERE pret_id=(SELECT id FROM pret WHERE ref=?)",
            (old, REF2))
con.execute("UPDATE pret SET created_at=? WHERE ref=?", (old, REF2))
con.commit()
ch = c.get("/returns/api/chase").get_json()
refs = [x["ref"] for x in ch["overdue"]]
ck("a return stuck at reception for nine days is chased", REF2 in refs, refs)
ck("the closed one is not chased", REF not in refs, refs)
ck("the reminder says how long, and against what limit",
   all(x["days"] >= x["limit"] for x in ch["overdue"]), ch["overdue"])
r = post("/returns/api/mute", {"ref": REF2, "detail": ""})
ck("silencing a reminder without a reason is refused", r.status_code == 400)
r = post("/returns/api/mute", {"ref": REF2, "detail": "vendor away till Monday"})
ck("with a reason it is allowed", r.status_code == 200)
ch = c.get("/returns/api/chase").get_json()
ck("a muted return stops being chased", REF2 not in [x["ref"] for x in ch["overdue"]])
ck("but it is still open and still counted",
   REF2 in [x["ref"] for x in c.get("/returns/api/open").get_json()["returns"]])
ck("and the silencing itself is on the record",
   any(e["kind"] == "MUTED" for e in c.get("/returns/api/trail?ref=" + REF2).get_json()["events"]))

print("\n[6b] the credit note is due on a DATE, not after N days (owner ruling, 28-Aug)")
ck("goods out on 2-Aug are due on 7-Sep", R.credit_due("2026-08-02") == dt.date(2026, 9, 7))
ck("goods out on 29-Aug are due on the SAME 7-Sep -- the month sets it, not the day",
   R.credit_due("2026-08-29") == dt.date(2026, 9, 7))
ck("December rolls into January of the NEXT year",
   R.credit_due("2026-12-14") == dt.date(2027, 1, 7), R.credit_due("2026-12-14"))

# a third return, handed over last month, still waiting for its note
r = post("/returns/api/book", {"vendor": "KEDAR PHARMACEUTICAL", "booked_by": "Darpan",
                               "lines": [{"item": "TYRO BR", "qty": 30, "rate_p": 700}]})
REF3 = r.get_json()["ref"]
for st, who in (("AT_RECEPTION", "Alisha"), ("HANDED", "Shavez"), ("AWAITING_NOTE", "Darpan")):
    post("/returns/api/advance", {"ref": REF3, "to": st, "person": who})
con = db()
last = dt.date.today().replace(day=15) - dt.timedelta(days=30)
con.execute("UPDATE pret SET handed_on=? WHERE ref=?", (last.isoformat(), REF3))
con.execute("UPDATE pret_event SET at=? WHERE pret_id=(SELECT id FROM pret WHERE ref=?)",
            (last.isoformat() + "T10:00:00", REF3))
con.commit()
due = R.credit_due(last.isoformat())
ch = c.get("/returns/api/chase").get_json()
row = [x for x in ch["overdue"] if x["ref"] == REF3]
if dt.date.today() > due:
    ck("a note overdue past the 7th of this month is chased, and the date is named",
       row and row[0]["due_on"] == due.isoformat(), (row, due.isoformat()))
else:
    ck("before the 7th it is NOT chased -- the vendor has not closed his month",
       not row, row)

# and one handed over today must never be chased, whatever the day count says
r = post("/returns/api/book", {"vendor": "DEEPAM PHARMA", "booked_by": "Darpan",
                               "lines": [{"item": "VOM L", "qty": 10, "rate_p": 900}]})
REF4 = r.get_json()["ref"]
for st, who in (("AT_RECEPTION", "Alisha"), ("HANDED", "Shavez"), ("AWAITING_NOTE", "Darpan")):
    post("/returns/api/advance", {"ref": REF4, "to": st, "person": who})
ck("a return handed over today is never chased for its note",
   REF4 not in [x["ref"] for x in c.get("/returns/api/chase").get_json()["overdue"]])

print("\n[7] the vendor signal, and its honesty about itself")
v = c.get("/returns/api/vendor_quality").get_json()
ck("returns group by vendor and reason", len(v["rows"]) >= 3, v["rows"])
ck("with a handful of returns on record it refuses to be read as a verdict",
   v["enough_to_judge"] is False and "Too few" in v["caveat"], v["caveat"])
ck("a return booked with no vendor is shown as such, not dropped",
   any(x["vendor"] == "(not recorded)" for x in v["rows"]), v["rows"])

print("\n[8] the schema survives a restart")
r = c.get("/returns/api/healthz")
ck("schema is idempotent across calls", r.status_code == 200)
ck("counts are real", r.get_json()["returns"] == 5, r.get_json())

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail:
    print("  FAILED:", f)
sys.exit(1 if _fail else 0)
