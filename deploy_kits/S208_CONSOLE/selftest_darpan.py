#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""selftest_darpan.py — the day card driven end to end, on the 27-Aug shape.

Builds a temp database carrying the real tables this touches (day_entry,
day_line, day_noncash_bill, day_expense, cash_movement, cash_adjustment,
sale_item, sale_line_item, upi_txn/statement/match via bank_match, setting,
data_flag, marg_push_staging and the v_cash_ledger view), mounts darpan_app
on a bare Flask app, and walks Darpan's actual day: evening count -> morning
card -> answer the three exceptions -> submit. Then the owner's side:
corrections tick, re-file grant, flag dismissal, staged rejection — and the
duplicate-filing guard refusing a second form.

    python3 selftest_darpan.py     exit 0 = all passed, 1 = a check failed
"""
import json
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, jsonify           # noqa: E402
import darpan_app                           # noqa: E402
import bank_match as BM                     # noqa: E402

_fail, _pass = [], 0


def ck(label, cond, detail=""):
    global _pass
    if cond:
        _pass += 1
        print("  ok   %s" % label)
    else:
        _fail.append(label)
        print("  FAIL %s   %s" % (label, detail))


tmp = tempfile.mkdtemp(prefix="darpan_")
DB = os.path.join(tmp, "t.db")
CON = sqlite3.connect(DB, check_same_thread=False)
CON.row_factory = sqlite3.Row

CON.executescript("""
CREATE TABLE day_entry (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT,
  status TEXT);
CREATE TABLE day_line (id INTEGER PRIMARY KEY, day_entry_id INT, mode TEXT,
  amount_p INT);
CREATE TABLE day_noncash_bill (id INTEGER PRIMARY KEY, day_entry_id INT,
  unit TEXT, bill_date TEXT, head TEXT, head_text TEXT, bill_no TEXT,
  amount_p INT, status TEXT DEFAULT 'open');
CREATE TABLE day_expense (id INTEGER PRIMARY KEY, day_entry_id INT,
  amount_p INT, amount_known INT DEFAULT 1);
CREATE TABLE cash_movement (id INTEGER PRIMARY KEY, day_entry_id INT,
  direction TEXT, party TEXT, amount_p INT, reference TEXT);
CREATE TABLE cash_custody_event (id INTEGER PRIMARY KEY, unit TEXT,
  event_date TEXT, from_party TEXT, to_party TEXT, amount_p INT,
  counter_person_id INT, month_end_kind TEXT, note TEXT, entered_by TEXT,
  entered_at TEXT);
CREATE TABLE cash_adjustment (id INTEGER PRIMARY KEY, day_entry_id INT,
  amount_p INT);
CREATE TABLE sale_item (id INTEGER PRIMARY KEY, day_entry_id INT, unit TEXT,
  service TEXT, amount_p INT, mode TEXT, source_ref TEXT, patient_ref_id INT);
CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, unit TEXT,
  business_date TEXT, bill_no TEXT, is_return INT DEFAULT 0, item_name TEXT,
  qty_raw TEXT, amount_p INT, batch TEXT, expiry_ym TEXT);
CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE data_flag (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT,
  code TEXT, severity TEXT, detail TEXT);
CREATE TABLE marg_push_staging (id INTEGER PRIMARY KEY, unit TEXT,
  status TEXT DEFAULT 'pending', parsed_json TEXT, survey_json TEXT);
CREATE TABLE upi_statement (merchant_id TEXT, unit TEXT, statement_date TEXT,
  parsed_total_p INT, txn_count INT, UNIQUE(merchant_id, statement_date));
CREATE TABLE upi_txn (id INTEGER PRIMARY KEY, merchant_id TEXT, unit TEXT,
  txn_date TEXT, amount_p INT, rrn TEXT, mode TEXT, txn_time TEXT,
  source_sha TEXT, ingested_at TEXT);
CREATE TABLE pipeline_status (id INTEGER PRIMARY KEY, received_at TEXT,
  source TEXT, payload_json TEXT);
CREATE TABLE ingest_batch (id INTEGER PRIMARY KEY, day_entry_id INT,
  adapter TEXT, status TEXT);
CREATE TABLE stock_rate (item TEXT PRIMARY KEY, rate_p INT, pack_size INT,
  as_of TEXT, source TEXT);
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT);
CREATE VIEW v_day_cash AS SELECT e.id day_entry_id, e.unit, e.business_date,
  COALESCE((SELECT SUM(l.amount_p) FROM day_line l WHERE l.day_entry_id=e.id
    AND l.mode='cash'),0) cash_in_p,
  COALESCE((SELECT SUM(l.amount_p) FROM day_line l WHERE l.day_entry_id=e.id
    AND l.mode='upi'),0) upi_in_p,
  COALESCE((SELECT SUM(l.amount_p) FROM day_line l WHERE l.day_entry_id=e.id),0)
    revenue_p,
  COALESCE((SELECT SUM(b.amount_p) FROM day_noncash_bill b
    WHERE b.day_entry_id=e.id),0) noncash_p,
  COALESCE((SELECT SUM(x.amount_p) FROM day_expense x WHERE x.day_entry_id=e.id
    AND x.amount_known=1),0) expense_p,
  COALESCE((SELECT SUM(m.amount_p) FROM cash_movement m WHERE m.day_entry_id=e.id
    AND m.direction='out'),0) cash_out_p,
  COALESCE((SELECT SUM(m.amount_p) FROM cash_movement m WHERE m.day_entry_id=e.id
    AND m.direction='in'),0) cash_back_p,
  COALESCE((SELECT SUM(a.amount_p) FROM cash_adjustment a
    WHERE a.day_entry_id=e.id),0) adjust_p
  FROM day_entry e;
CREATE VIEW v_cash_ledger AS SELECT unit, business_date, day_entry_id,
  cash_in_p, upi_in_p, revenue_p, noncash_p, expense_p, cash_out_p, cash_back_p,
  adjust_p,
  (cash_in_p-noncash_p-expense_p-cash_out_p+cash_back_p+adjust_p) net_p,
  COALESCE(SUM(cash_in_p-noncash_p-expense_p-cash_out_p+cash_back_p+adjust_p)
   OVER (PARTITION BY unit ORDER BY business_date, day_entry_id
         ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) opening_p,
  SUM(cash_in_p-noncash_p-expense_p-cash_out_p+cash_back_p+adjust_p)
   OVER (PARTITION BY unit ORDER BY business_date, day_entry_id
         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) closing_p
  FROM v_day_cash;
""")

D = "2026-08-27"
# ---- the filed day: bills as sale_item, plus items, categories, ledger ----
CON.execute("INSERT INTO day_entry (id, unit, business_date, status) "
            "VALUES (1,'medical',?, 'approved')", (D,))
BILLS = [("A003228", 41300, "upi"), ("A003240", 110000, "upi"),
         ("A003241", 105000, "upi"), ("A003244", 164000, "upi"),
         ("A003249", 153000, "upi"),
         ("A003230", 250000, "cash"), ("A003242", 89000, "cash"),
         ("A003235", 73500, "cash"), ("A003216", 200, "cash"),
         ("A003217", 150000, "cash")]
for b, p, m in BILLS:
    CON.execute("INSERT INTO sale_item (day_entry_id, unit, service, amount_p, "
                "mode, source_ref) VALUES (1,'medical','pharmacy',?,?,?)", (p, m, b))
CON.execute("INSERT INTO sale_item (day_entry_id, unit, service, amount_p, mode, "
            "source_ref) VALUES (1,'medical','pharmacy_return',18930,'cash','CN0140')")
# categories: one home bill, one procedure bill, one orthotic item line
CON.execute("INSERT INTO day_noncash_bill (day_entry_id, unit, bill_date, head, "
            "bill_no, amount_p) VALUES (1,'medical',?, 'home_medicine','A003217',150000)", (D,))
CON.execute("INSERT INTO sale_line_item (unit, business_date, bill_no, item_name, "
            "qty_raw, amount_p) VALUES ('medical',?, 'A003244','KNEE CAP UNISON L LYCRA','1.0',35000)", (D,))
CON.execute("INSERT INTO setting VALUES ('orthotics.vocab','KNEE CAP, ARM SLING')")
CON.execute("INSERT INTO setting VALUES ('darpan.owners','manoj')")
# the drawer ledger: cash entered 8,42 style — day_line cash
CON.execute("INSERT INTO day_line (day_entry_id, mode, amount_p) VALUES (1,'cash',3161600)")
CON.execute("INSERT INTO day_line (day_entry_id, mode, amount_p) VALUES (1,'upi',573300)")
# bank + matcher rows (reuse bank_match itself so shapes never drift)
BANK = [(41300, "R1"), (105000, "R2"), (81200, "R3"), (164000, "R4"),
        (50000, "R5"), (73500, "R6"), (153000, "R7"), (110000, "R8"),
        (250000, "R9"), (89000, "R10")]
for amt, rrn in BANK:
    CON.execute("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, rrn, "
                "mode) VALUES ('100000000312505','medical',?,?,?,'UPI')", (D, amt, rrn))
CON.execute("INSERT INTO upi_statement VALUES ('100000000312505','medical',?,?,10)",
            (D, sum(a for a, _ in BANK)))
CON.commit()
code, msg = BM.run_day(CON, "medical", D)
assert code == 0, msg

# ---------------------------------------------------------------- the app
ROLE = {"user": "darpan", "roles": ["maker"]}


def db():
    return CON


def require(*roles):
    have = set(ROLE.get("roles") or [])
    if not have.intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return dict(ROLE), None


app = Flask(__name__)


@app.route("/finance/api/day", methods=["POST"])
def fake_filing():
    return jsonify(ok=True, saved=True)     # stands in for api_save_day


darpan_app.init(app, db, require, unit="medical")
c = app.test_client()

print("[1] the card, assembled from the real shapes")
j = c.get("/finance/darpan/api/card?date=%s" % D).get_json()
ck("card answers", j and j["ok"])
ck("day sale is net of returns (11,17,­.. − CN)",
   j["sale"]["day_sale_p"] == sum(p for _, p, _ in BILLS) - 18930,
   j["sale"]["day_sale_p"])
ck("the CN bill is listed", j["sale"]["cn_bills"][0]["bill"] == "CN0140")
ck("UPI = the five agreed bills", j["upi"]["total_p"] == 573300
   and len(j["upi"]["bills"]) == 5, j["upi"]["total_p"])
ck("net cash = sale − UPI − home − procedure",
   j["net_cash_p"] == j["sale"]["day_sale_p"] - 573300 - 150000 - 0)
ck("home bill under its category",
   j["categories"]["home"]["bills"][0]["bill"] == "A003217")
ck("the orthotic item is found by the vocab",
   j["categories"]["orthotics"]["items"][0]["item"].startswith("KNEE CAP"))
ck("bank section carries all 10 txns", len(j["bank"]["txns"]) == 10)
ck("three exceptions (3 cash + 2 orphans = 5)", len(j["exceptions"]) == 5,
   len(j["exceptions"]))
ck("drawer says the evening count is missing",
   j["drawer"]["counted_p"] is None)

print("\n[2] submit refuses until the day is answered and counted")
r = c.post("/finance/darpan/api/submit", json={"date": D})
ck("refused with exceptions open", r.status_code == 400
   and r.get_json()["error"] == "exceptions_open")

print("\n[3] the evening count")
r = c.post("/finance/darpan/api/drawer", json={"date": D, "counted_p": 2438300})
ck("count recorded", r.status_code == 200)
j = c.get("/finance/darpan/api/card?date=%s" % D).get_json()
exp = j["drawer"]["expected_p"]
ck("expected comes from v_cash_ledger", exp is not None)
ck("a gap over Rs 50 is shown with the arithmetic",
   j["drawer"]["show"] and j["drawer"]["parts"], j["drawer"])
r = c.post("/finance/darpan/api/drawer", json={"date": D, "counted_p": exp + 4900})
j = c.get("/finance/darpan/api/card?date=%s" % D).get_json()
ck("Rs 49 inside the Rs 50 tolerance is auto-OK, not shown",
   j["drawer"]["show"] is False)

print("\n[4] answering the exceptions, two taps each")
ex = {e["kind"]: e for e in j["exceptions"]}
cash_ids = [e["id"] for e in j["exceptions"] if e["kind"] == "cash"]
orph_ids = [e["id"] for e in j["exceptions"] if e["kind"] == "bank_orphan"]
for i in cash_ids:
    r = c.post("/finance/darpan/api/exception/%d/answer" % i,
               json={"answer": "was_upi"})
    ck("cash #%d answered was_upi" % i, r.status_code == 200)
r = c.post("/finance/darpan/api/exception/%d/answer" % cash_ids[0],
           json={"answer": "was_upi"})
ck("a second answer on the same row is refused", r.status_code == 409)
r = c.post("/finance/darpan/api/exception/%d/answer" % orph_ids[0],
           json={"answer": "advance", "note": "plaster advance"})
ck("orphan -> advance creates a log row", r.status_code == 200 and CON.execute(
    "SELECT COUNT(*) FROM darpan_advance WHERE status='open'").fetchone()[0] == 1)
r = c.post("/finance/darpan/api/exception/%d/answer" % orph_ids[1],
           json={"answer": "attach_bill", "bill_no": "a003231"})
ck("orphan -> attached to a bill, upper-cased", r.status_code == 200 and
   "ATTACH:A003231" in (CON.execute("SELECT resolution FROM upi_match WHERE id=?",
                                    (orph_ids[1],)).fetchone()[0] or "").upper())

print("\n[5] submit now verifies the day")
r = c.post("/finance/darpan/api/submit", json={"date": D})
ck("verified", r.status_code == 200 and r.get_json()["status"] == "verified",
   r.get_json())

print("\n[6] the corrections list and the tick")
ROLE.update(user="manoj", roles=["checker"])
j = c.get("/finance/darpan/api/corrections?month=2026-08").get_json()
ck("three correction rows, none ticked", j["pending"] == 3 and j["corrected"] == 0)
ck("the instruction names the bill",
   "A003230" in [x["bill"] for x in j["rows"]])
mid = j["rows"][0]["id"]
r = c.post("/finance/darpan/api/correction/%d/tick" % mid, json={})
ck("tick recorded", r.status_code == 200)
ck("double tick refused", c.post("/finance/darpan/api/correction/%d/tick" % mid,
                                 json={}).status_code == 409)
j = c.get("/finance/darpan/api/corrections?month=2026-08").get_json()
ck("counts move", j["pending"] == 2 and j["corrected"] == 1)

print("\n[7] the duplicate-filing guard — OFF by default, an owner switch")
ROLE.update(user="darpan", roles=["maker"])
r = c.post("/finance/api/day", json={"business_date": D, "x": 1})
ck("guard OFF: a re-save passes untouched (the app's own flow survives)",
   r.status_code == 200)
ck("darpan cannot flip the switch", c.post("/finance/darpan/api/guard",
   json={"on": True}).status_code == 403)
ROLE.update(user="manoj", roles=["checker"])
r = c.post("/finance/darpan/api/guard", json={"on": True})
ck("the owner turns the guard ON", r.status_code == 200 and r.get_json()["on"])
ROLE.update(user="darpan", roles=["maker"])
r = c.post("/finance/api/day", json={"business_date": D, "x": 1})
ck("a second form for a filed day is refused 403", r.status_code == 403
   and r.get_json()["error"] == "already_filed")
r = c.post("/finance/api/day", json={"business_date": "2026-09-01"})
ck("a NEW day passes straight through", r.status_code == 200)
ROLE.update(user="manoj", roles=["checker"])
r = c.post("/finance/darpan/api/refile-grant", json={"date": D})
ck("the owner grants a re-file", r.status_code == 200)
ROLE.update(user="darpan", roles=["maker"])
ck("darpan cannot grant one", c.post("/finance/darpan/api/refile-grant",
                                     json={"date": D}).status_code == 403)
r = c.post("/finance/api/day", json={"business_date": D})
ck("with the grant, the re-file goes through once", r.status_code == 200)
r = c.post("/finance/api/day", json={"business_date": D})
ck("and the grant is spent — refused again", r.status_code == 403)

print("\n[8] the owner tools")
ROLE.update(user="manoj", roles=["checker"])
CON.execute("INSERT INTO data_flag (unit, business_date, code, severity, detail) "
            "VALUES ('medical','2026-06-12','MARG_DAY_NOT_FILED','high','x')")
CON.commit()
r = c.post("/finance/darpan/api/dismiss-flag",
           json={"date": "2026-06-12", "reason": "deliberate backfill, ruled"})
ck("the 2026-06-12 flag is dismissed, with a reason", r.status_code == 200
   and r.get_json()["removed"] == 1)
ck("no reason, no dismissal", c.post("/finance/darpan/api/dismiss-flag",
   json={"date": "2026-06-12"}).status_code == 400)
CON.execute("INSERT INTO marg_push_staging (id, unit, status) VALUES (9,'medical','pending')")
CON.commit()
r = c.post("/finance/darpan/api/reject-staged", json={"id": 9, "reason": "duplicate"})
ck("a pending push can be rejected", r.status_code == 200 and CON.execute(
    "SELECT status FROM marg_push_staging WHERE id=9").fetchone()[0] == "rejected")
ck("audit trail has rows for all of it", CON.execute(
    "SELECT COUNT(*) FROM darpan_audit").fetchone()[0] >= 8)

print("\n[9] Sprint 3 — the ledgers, diagnosed and repaired")
ROLE.update(user="darpan", roles=["maker"])
ck("ledger-check is owner-only", c.get(
    "/finance/darpan/api/ledger-check").status_code == 403)
ROLE.update(user="manoj", roles=["checker"])
# the 27-Aug shape: the transfer-out exists, the balance VIEW does not
CON.execute("INSERT INTO cash_movement (day_entry_id, direction, party, "
            "amount_p, reference) VALUES (1,'out','dr_bhawna',500000,'to Dr Bhawna')")
CON.commit()
j = c.get("/finance/darpan/api/ledger-check?date=%s" % D).get_json()
ck("the check finds the transfer-out row", any(
    m["party"] == "dr_bhawna" and m["amount_p"] == 500000 for m in j["movements"]))
ck("and names the MISSING balance view as the fault",
   j["balance_view"]["exists"] is False and
   any("v_cash_custody_balance is MISSING" in p for p in j["problems"]))
r = c.post("/finance/darpan/api/ledger-repair-view", json={})
ck("the repair creates the view", r.status_code == 200 and r.get_json()["created"])
ck("running it again says already there",
   c.post("/finance/darpan/api/ledger-repair-view", json={}).get_json()["created"]
   is False)
r = c.post("/finance/darpan/api/transfer",
           json={"from": "drawer", "to": "dr_bhawna", "date": D,
                 "amount": 5000.00, "note": "repair: 27-Aug landing"})
ck("the owner records the 27-Aug transfer", r.status_code == 200)
j = c.get("/finance/darpan/api/ledger-check?date=%s" % D).get_json()
ck("the view now shows Bhawna holding it", any(
    b["party"] == "dr_bhawna" and b["held_p"] == 500000
    for b in j["balance_view"]["rows"]), j["balance_view"])
ck("a transfer without a note is refused", c.post(
    "/finance/darpan/api/transfer", json={"from": "drawer", "to": "dr_manoj",
    "date": D, "amount": 100}).status_code == 400)
ck("bad parties refused", c.post("/finance/darpan/api/transfer",
   json={"from": "drawer", "to": "drawer", "date": D, "amount": 100,
         "note": "x"}).status_code == 400)
ROLE.update(user="darpan", roles=["maker"])
ck("darpan cannot record an owner transfer", c.post(
    "/finance/darpan/api/transfer", json={"from": "drawer", "to": "dr_bhawna",
    "date": D, "amount": 100, "note": "x"}).status_code == 403)

print("\n[10] Sprint 4 — the pipeline page")
ROLE.update(user="darpan", roles=["maker"])
CON.execute("INSERT INTO pipeline_status (received_at, source, payload_json) "
            "VALUES ('2026-08-30T07:00:00','manojz','{\"pull\":\"ok\"}')")
CON.commit()
j = c.get("/finance/darpan/api/pipeline").get_json()
ck("pipeline answers with all six legs", j["ok"] and
   set(j["legs"]) == {"manojz_heartbeat", "marg_pushes", "filed_days",
                      "bank", "matcher", "stock"}, sorted(j.get("legs", {})))
ck("heartbeat leg carries the posted time",
   j["legs"]["manojz_heartbeat"]["posted"].startswith("2026-08-30"))
ck("bank leg counts the transactions",
   j["legs"]["bank"]["transactions"] >= 10)
ck("matcher leg shows the matched day",
   any(x["business_date"] == D and x["status"] == "matched"
       for x in j["legs"]["matcher"]))
ck("a MISSING table is reported, not fatal (stock)",
   "error" in j["legs"]["stock"])
ck("the page itself is served",
   c.get("/finance/pipeline").status_code == 200)

print("\n[11] S208_CONSOLE — status computed fresh, never a stale record")
ROLE.update(user="manoj", roles=["checker"])
# the 27-Aug day: filed + APPLIED batch + a stale NOT-FILED flag from push time
CON.execute("INSERT INTO ingest_batch (day_entry_id, adapter, status) "
            "VALUES (1,'marg_export','ok')")
CON.execute("INSERT INTO data_flag (unit, business_date, code, severity, detail) "
            "VALUES ('medical',?, 'MARG_DAY_NOT_FILED','high','from push time')", (D,))
# a filed day with a STAGED (unapplied) report
CON.execute("INSERT INTO day_entry (id, unit, business_date, status) "
            "VALUES (7,'medical','2026-08-26','submitted')")
CON.execute("INSERT INTO marg_push_staging (unit, status, parsed_json) "
            "VALUES ('medical','pending','x')")
CON.execute("UPDATE marg_push_staging SET parsed_json=NULL WHERE parsed_json='x'")
CON.execute("INSERT INTO marg_push_staging (id, unit, status) VALUES (77,'medical','pending')")
CON.execute("UPDATE marg_push_staging SET survey_json='{\"survey\":[{\"date\":\"2026-08-26\"}]}' "
            "WHERE id=77")
# a filed day with NOTHING
CON.execute("INSERT INTO day_entry (id, unit, business_date, status) "
            "VALUES (8,'medical','2026-08-25','submitted')")
# an unfiled day whose report was pushed (flagged at push time)
CON.execute("INSERT INTO data_flag (unit, business_date, code, severity, detail) "
            "VALUES ('medical','2026-08-28','MARG_DAY_NOT_FILED','high','x')")
CON.commit()
j = c.get("/finance/darpan/api/coverage?days=60").get_json()
byd = {r["date"]: r for r in j["rows"]}
ck("filed+applied day is OK", byd[D]["verdict"] == "OK", byd.get(D))
ck("and its old flag is marked STALE (dismiss lives beside it)",
   byd[D]["stale"] is True)
ck("filed+staged day says REPORT WAITING",
   byd["2026-08-26"]["verdict"] == "REPORT WAITING", byd.get("2026-08-26"))
ck("filed+nothing says EXPORT MISSING",
   byd["2026-08-25"]["verdict"] == "EXPORT MISSING")
ck("unfiled flagged day says DAY NOT FILED and flag is NOT stale",
   byd["2026-08-28"]["verdict"] == "DAY NOT FILED"
   and byd["2026-08-28"]["stale"] is False)

print("\n[12] a credit note is a SALES RETURN — verified against the same "
      "patient's own earlier sale (owner-ruled)")
CON.execute("INSERT INTO patient_ref (id, clinic_id, name) VALUES (9,'6002','RAM AVTAR')")
CON.execute("UPDATE sale_item SET patient_ref_id=9 WHERE source_ref='CN0140'")
# the CN's item lines: one that HE bought earlier, one he never bought
CON.execute("INSERT INTO sale_line_item (unit, business_date, bill_no, is_return, "
            "item_name, qty_raw, amount_p) VALUES ('medical',?, 'CN0140',1,"
            "'PATOPAN DSR','0:6',12930)", (D,))
CON.execute("INSERT INTO sale_line_item (unit, business_date, bill_no, is_return, "
            "item_name, qty_raw, amount_p) VALUES ('medical',?, 'CN0140',1,"
            "'NEVER BOUGHT TAB','0:2',6000)", (D,))
# his earlier sale: bill A003217 (already a sale_item row) sold PATOPAN DSR
CON.execute("UPDATE sale_item SET patient_ref_id=9 WHERE source_ref='A003217'")
CON.execute("INSERT INTO sale_line_item (unit, business_date, bill_no, is_return, "
            "item_name, qty_raw, amount_p) VALUES ('medical','2026-08-20',"
            "'A003217',0,'PATOPAN DSR','1:0',21000)")
CON.commit()
j = c.get("/finance/darpan/api/cn-detail?month=2026-08").get_json()
ck("the month's CNs listed with totals", j["count"] == 1 and j["total_p"] == 18930, j)
n0 = j["notes"][0]
ck("the CN knows its patient", n0["patient"]
   and n0["patient"]["name"] == "RAM AVTAR", n0.get("patient"))
byitem = {l["item"]: l for l in n0["lines"]}
ck("the returned item traces to HIS OWN earlier sale bill",
   byitem["PATOPAN DSR"]["verified"] and
   byitem["PATOPAN DSR"]["earlier_sales"][0]["bill"] == "A003217" and
   byitem["PATOPAN DSR"]["earlier_sales"][0]["date"] == D,
   byitem.get("PATOPAN DSR"))
ck("an item he NEVER bought is flagged unverified — the one to ask about",
   byitem["NEVER BOUGHT TAB"]["verified"] is False)

print("\n[12b] an untraceable return is NOT entertained without the owner")
j = c.get("/finance/darpan/api/cn-detail?month=2026-08").get_json()
n0 = j["notes"][0]
ck("the CN with an unverified line NEEDS APPROVAL, pending opens itself",
   n0["needs_approval"] and n0["approval"]["status"] == "pending", n0.get("approval"))
ck("the month header counts it", j["pending_approval"] == 1)
ROLE.update(user="darpan", roles=["maker"])
ck("darpan cannot decide a return", c.post("/finance/darpan/api/cn-approve",
   json={"bill": "CN0140", "decision": "approved"}).status_code == 403)
ROLE.update(user="manoj", roles=["checker"])
ck("a rejection without a reason is refused", c.post(
   "/finance/darpan/api/cn-approve",
   json={"bill": "CN0140", "decision": "rejected"}).status_code == 400)
r = c.post("/finance/darpan/api/cn-approve",
           json={"bill": "CN0140", "decision": "approved",
                 "note": "old stock, known case"})
ck("the owner approves, named and dated", r.status_code == 200)
j = c.get("/finance/darpan/api/cn-detail?month=2026-08").get_json()
ck("the decision shows on the card and pending drops to zero",
   j["pending_approval"] == 0 and
   j["notes"][0]["approval"]["status"] == "approved" and
   j["notes"][0]["approval"]["decided_by"] == "manoj")

print("\n[13] the short-ID lookup (842 is a real patient)")
CON.execute("INSERT INTO patient_ref (clinic_id, name) VALUES ('842','NANHI DEVI')")
CON.commit()
j = c.get("/finance/darpan/api/idlookup?ids=842,75").get_json()
by = {x["clinic_id"]: x for x in j["results"]}
ck("842 resolves to Nanhi Devi", by["842"]["known"] and by["842"]["name"] == "NANHI DEVI")
ck("75 honestly unknown", by["75"]["known"] is False)
ROLE.update(user="darpan", roles=["maker"])
ck("coverage is checker-only", c.get(
    "/finance/darpan/api/coverage").status_code == 403)
ROLE.update(user="manoj", roles=["checker"])

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail:
    print("  FAILED:", f)
CON.close()
import shutil                                # noqa: E402
shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if _fail else 0)
