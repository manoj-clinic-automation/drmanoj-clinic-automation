#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_darpan_kal_s243.py -- the LIVE-SHAPE walk for S243_DARPAN_KAL.

A real Flask app -- the finance_app.py named by FIN_APP, patched IN MEMORY by
this kit's own patcher so the walk proves the mount the installer will make --
over a real sqlite database built from finance_schema.sql + finance_returns.sql
+ darpan_kal_schema.sql, with the real sibling modules copied beside it.
Yesterday is seeded exactly as the D354 autofile leaves it (day_entry
submitted, day_line cash/upi, sale_item bills incl. a Home Medicine bill, a UPI
bill and a credit note, one typed procedure bill, the bank statement and its
transactions, a large return).  Nothing live is touched.

    FIN_APP=<finance_app.py> FIN_MODS=<folder with the modules> python3 -B walk_darpan_kal_s243.py

On the box after install (builds its own db; copies nothing live):
    FIN_APP=/root/finance/finance_app.py FIN_MODS=/root/finance \
        /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S243_DARPAN_KAL/walk_darpan_kal_s243.py
"""
import datetime as dt
import json
import os
import shutil
import sqlite3
import sys
import tempfile

KIT = os.path.dirname(os.path.abspath(__file__))
FIN_APP = os.environ.get("FIN_APP", "/root/finance/finance_app.py")
FIN_MODS = os.environ.get("FIN_MODS", os.path.dirname(os.path.abspath(FIN_APP)) or "/root/finance")
TMP = tempfile.mkdtemp(prefix="walk_s243_kal_")
MOD = os.path.join(TMP, "mods")
UI = os.path.join(TMP, "ui")
DB = os.path.join(TMP, "finance.db")
os.makedirs(MOD)
os.makedirs(UI)

sys.path.insert(0, KIT)
import patch_finance_app_darpan_kal_s243 as PATCHER                   # noqa: E402

src = open(FIN_APP, encoding="utf-8").read()
patched, st = PATCHER.patch_fa(src)
open(os.path.join(MOD, "finance_app.py"), "w", encoding="utf-8", newline="\n").write(patched)
for m in ("finance_ingest", "finance_returns", "finance_upi", "marg_report", "finance_identity",
          "darpan_app", "returns_desk", "finance_returns_audit", "finance_money", "finance_returns_escalate",
          "finance_intent", "staff_pages", "joiner_app", "stock_app", "finance_clinic_day", "clinic_register",
          "purchase_app", "bank_mpr_status", "clinic_day_pdf", "marg_door", "amir_day", "marg_take",
          "marg_spine", "sale_bill", "amir_salts", "docterz_ingest", "docterz_day"):
    p = os.path.join(FIN_MODS, m + ".py")
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(MOD, m + ".py"))
for f in ("darpan_card.html", "darpan_corrections.html", "returns_desk.html", "pipeline_status.html",
          "staff_manage.html", "stock_desk.html", "stock_amir.html", "stock_pad.html"):
    p = os.path.join(FIN_MODS, f)
    if os.path.exists(p):
        shutil.copyfile(p, os.path.join(MOD, f))
for f in ("darpan_kal.py", "darpan_kal_schema.sql", "darpan_kal.html"):
    shutil.copyfile(os.path.join(KIT, f), os.path.join(MOD, f))
for f in ("finance_daily.html", "finance_review.html", "finance_approvals.html", "finance_entry.html",
          "finance_workbench.html", "finance_entry_clinic.html"):
    open(os.path.join(UI, f), "w").write("<html><body>walk stub %s</body></html>" % f)
HUB_SRC = os.path.join(FIN_MODS, "finance_ui", "finance_approvals.html")
HUB_ST = "absent"
if os.path.exists(HUB_SRC):
    _hub, HUB_ST = PATCHER.patch_hub(open(HUB_SRC, encoding="utf-8").read())
    open(os.path.join(UI, "finance_approvals.html"), "w", encoding="utf-8", newline="\n").write(_hub)

Y = (dt.date.today() - dt.timedelta(days=1)).isoformat()
D2 = (dt.date.today() - dt.timedelta(days=2)).isoformat()

con = sqlite3.connect(DB)
con.executescript(open(os.path.join(FIN_MODS, "finance_schema.sql"), encoding="utf-8").read())
con.executescript(open(os.path.join(FIN_MODS, "finance_returns.sql"), encoding="utf-8").read())
con.execute("ALTER TABLE sale_item ADD COLUMN home_med INTEGER DEFAULT 0")
con.execute("CREATE TABLE IF NOT EXISTS upi_txn (id INTEGER PRIMARY KEY, merchant_id TEXT NOT NULL, unit TEXT, "
            "txn_date TEXT NOT NULL, amount_p INTEGER NOT NULL, rrn TEXT NOT NULL, mode TEXT, txn_time TEXT, "
            "source_sha TEXT, ingested_at TEXT)")
con.execute("CREATE TABLE IF NOT EXISTS cash_custody_event (id INTEGER PRIMARY KEY, unit TEXT, event_date TEXT, "
            "from_party TEXT, to_party TEXT, amount_p INTEGER, counter_person_id INTEGER, month_end_kind TEXT, "
            "note TEXT, entered_by TEXT, entered_at TEXT)")
con.execute("CREATE VIEW IF NOT EXISTS v_cash_custody_balance AS SELECT unit, party, SUM(amount_p) AS held_p FROM ("
            " SELECT unit, to_party AS party, amount_p FROM cash_custody_event UNION ALL"
            " SELECT unit, from_party AS party, -amount_p FROM cash_custody_event) GROUP BY unit, party")
con.execute("CREATE TABLE IF NOT EXISTS counter_person (id INTEGER PRIMARY KEY, unit TEXT, name TEXT, hindi_name TEXT, "
            "role_kind TEXT, hands_cash_to TEXT, note TEXT, active INTEGER DEFAULT 1)")
for user, role in (("zzwalkdoc", "checker"), ("zzwalkmaker", "maker"), ("zzwalkbhawna", "viewer"), ("zzwalkother", "viewer")):
    con.execute("INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('medical',?,?,1)", (user, role))
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('darpan_kal.recipients', 'zzwalkdoc:dr_manoj,zzwalkbhawna:dr_bhawna')")
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('returns.act_from', '2026-01-01')")

# ---- yesterday, as the D354 autofile leaves it -------------------------------
# bills: A1 300 cash, A2 450 cash, A3 620 UPI, A4 HOME MEDICINE 275 cash (home_med=1),
#        A5 1500 cash (later returned in part), CN1 -1200 return of A5 (large return)
# typed: procedure bill P9 150 (day_noncash_bill)
# bank: statement in; one txn 620 (A3) and one 210 settled against a bill rung CASH (A1... no: extra)
NET = 300 + 450 + 620 + 275 + 1500 - 1200          # 1945 -> the printout's day sale
BANK = 620 + 210
cur = con.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) "
                  "VALUES ('medical',?,'submitted','app','auto',?)", (Y, dt.datetime.now().isoformat()))
EID = cur.lastrowid
con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,'pharmacy_sale','cash',?)", (EID, (NET - BANK) * 100))
con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,'pharmacy_sale','upi',?)", (EID, BANK * 100))
bills = [("A1", "WALKIN ONE", 300, "cash", 0, "pharmacy"), ("A2", "WALKIN TWO", 450, "cash", 0, "pharmacy"),
         ("A3", "WALKIN THREE", 620, "upi", 0, "pharmacy"), ("A4", "HOME MEDISUN", 275, "cash", 1, "pharmacy"),
         ("A5", "WALKIN FIVE", 1500, "cash", 0, "pharmacy"), ("CN1", "WALKIN FIVE", 1200, "cash", 0, "pharmacy_return")]
for bno, desc, amt, mode, hm, svc in bills:
    con.execute("INSERT INTO sale_item (day_entry_id, unit, service, description, amount_p, mode, home_med, source, source_ref) "
                "VALUES (?,'medical',?,?,?,?,?,'manual',?)", (EID, svc, desc, amt * 100, mode, hm, bno))
con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, qty_raw, amount_p) "
            "VALUES (?,'medical',?,'CN1',1,1,'KNEE SUPPORT HINGED L','knee support hinged l','1:0',120000)", (EID, Y))
con.execute("INSERT INTO day_noncash_bill (day_entry_id, unit, bill_date, head, bill_no, amount_p, entered_by, entered_at) "
            "VALUES (?,'medical',?,'procedure_medicine','P9',15000,'zzwalkmaker',?)", (EID, Y, dt.datetime.now().isoformat()))
con.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, parsed_total_p, txn_count) VALUES ('MIDWALK','medical',?,?,2)", (Y, BANK * 100))
con.execute("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, rrn, mode, txn_time) VALUES ('MIDWALK','medical',?,62000,'RRNWALK1','UPI','10:12')", (Y,))
con.execute("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, rrn, mode, txn_time) VALUES ('MIDWALK','medical',?,21000,'RRNWALK2','UPI','17:40')", (Y,))
# day before yesterday: applied, NO bank statement yet (provisional online) -- for the excess case
cur = con.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) "
                  "VALUES ('medical',?,'submitted','app','auto',?)", (D2, dt.datetime.now().isoformat()))
EID2 = cur.lastrowid
con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,'pharmacy_sale','cash',100000)", (EID2,))
con.execute("INSERT INTO sale_item (day_entry_id, unit, service, description, amount_p, mode, home_med, source, source_ref) "
            "VALUES (?,'medical','pharmacy','WALKIN',100000,'cash',0,'manual','B1')", (EID2,))
con.commit()
con.close()

EXPECTED_Y = (NET - 275 - 150 - BANK) * 100          # 1945 - 275 - 150 - 830 = 690 -> 69000 paise

os.environ.update(FINANCE_DB=DB, FINANCE_UI_DIR=UI, FINANCE_ALLOW_HEADER_AUTH="1",
                  FINANCE_PORTAL_LOGIN="/portal", FINANCE_SCAN_DIR=os.path.join(TMP, "scans"),
                  FINANCE_MARG_TOKEN="DUMMY-TOKEN-PUT-HERE", FINANCE_UPI_DIR=os.path.join(TMP, "upi"),
                  FINANCE_AUTOAPPLY_OFF=os.path.join(TMP, "AUTOAPPLY_OFF"))
sys.path.insert(0, MOD)
import finance_app as FA                                                # noqa: E402

print("walking %s (patched in memory: %s)" % (FIN_APP, st))
print("  temp db %s" % DB)
PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % str(detail)[:300]) if detail and not cond else ""))


c = FA.app.test_client()
DOC = {"X-Clinic-User": "zzwalkdoc", "X-Clinic-Role": "doctor"}
MAK = {"X-Clinic-User": "zzwalkmaker", "X-Clinic-Role": "staff"}
BHA = {"X-Clinic-User": "zzwalkbhawna", "X-Clinic-Role": "doctor"}
OTH = {"X-Clinic-User": "zzwalkother", "X-Clinic-Role": "staff"}


def get(u, h):
    r = c.get(u, headers=h)
    return r.status_code, (r.get_json(silent=True) or {})


def post(u, h, body):
    r = c.post(u, headers=h, data=json.dumps(body), content_type="application/json")
    return r.status_code, (r.get_json(silent=True) or {})


# ---- 0 mount + old pages ------------------------------------------------------
ck("darpan_kal is mounted", "darpan_kal" in FA.app.blueprints)
ck("healthz still 200", c.get("/finance/healthz").status_code == 200)
ck("old /finance/darpan still opens for the maker", c.get("/finance/darpan", headers=MAK).status_code == 200)
ck("old /finance/darpan/corrections still opens for the checker", c.get("/finance/darpan/corrections", headers=DOC).status_code == 200)
ck("/finance/darpan/kal opens for the maker", c.get("/finance/darpan/kal", headers=MAK).status_code == 200)
ck("/finance/darpan/kal/<date> opens for the checker", c.get("/finance/darpan/kal/" + Y, headers=DOC).status_code == 200)
ck("a viewer NOT named in recipients is refused", c.get("/finance/darpan/kal", headers=BHA).status_code == 200
   and c.get("/finance/darpan/kal", headers=OTH).status_code == 403)
ck("anonymous is sent to login / refused", c.get("/finance/darpan/kal").status_code in (302, 401, 403))

# ---- 0b THE PAGE WALK (S208 rule: a kit is proven by the rendered page, not the API) ----------
r = c.get("/finance/darpan/kal", headers=MAK)
html = r.get_data(as_text=True)
ck("PAGE maker: 200, text/html", r.status_code == 200 and "text/html" in (r.content_type or ""), r.content_type)
ck("PAGE maker: the Hindi section labels are in the page",
   all(t in html for t in ("\u0915\u0932 \u0915\u0940 \u092c\u093f\u0915\u094d\u0930\u0940",           # kal ki bikri
                           "\u0918\u0930 / \u092a\u094d\u0930\u094b\u0938\u0940\u091c\u0930",           # ghar / procedure
                           "\u0907\u0924\u0928\u093e cash \u0939\u094b\u0928\u093e \u091a\u093e\u0939\u093f\u090f",  # itna cash hona chahiye
                           "\u0915\u0932 \u0915\u0940 \u0935\u093e\u092a\u0938\u0940")))               # kal ki vaapsi
ck("PAGE maker: the two inputs (cash amount, Dr Manoj / Dr Bhawna)",
   'id="handed"' in html and "\u0915\u093f\u0924\u0928\u093e cash \u0926\u093f\u092f\u093e" in html
   and "\u0915\u093f\u0938\u0915\u094b \u0926\u093f\u092f\u093e" in html and "Dr Manoj" in html and "Dr Bhawna" in html)
ck("PAGE maker: the five reasons and the five return answers are in the page",
   all(k in html for k in ("home_not_in_print", "online_not_on_pos", "return_cash", "carried", "other"))
   and all(k in html for k in ("slip_checked", "wrong_bill", "exchange", "doctor_said")))
ck("PAGE: no deterrent line, no phone-number field", "deterrent" not in html.lower() and "mobile" not in html.lower())
r = c.get("/finance/darpan/kal", headers=BHA)
ck("PAGE Dr Bhawna (viewer named in recipients): 200 html with her 'received' view",
   r.status_code == 200 and "text/html" in (r.content_type or "") and "renderMine" in r.get_data(as_text=True)
   and "\u092e\u093f\u0932\u093e" in r.get_data(as_text=True))
s0, j0 = get("/finance/darpan/kal/api/mine", BHA)
ck("PAGE Dr Bhawna: her list answers (empty before any handover)", s0 == 200 and j0.get("party") == "dr_bhawna" and j0.get("days") == [])
r = c.get("/finance/darpan/kal")
ck("PAGE anonymous: redirected to the portal", r.status_code == 302 and "/portal" in (r.headers.get("Location") or ""), (r.status_code, r.headers.get("Location")))
r = c.get("/finance/approvals", headers=DOC)
hub_html = r.get_data(as_text=True)
ck("PAGE owner hub /finance/approvals: 200 (real page, patched %s)" % HUB_ST, r.status_code == 200 and HUB_ST in ("patched", "already"))
ck("PAGE owner hub: the card 'Darpan \u2014 needs you' is present with its loader and tab",
   "Darpan \u2014 needs you" in hub_html and 'id="kalCard"' in hub_html and "function loadKal()" in hub_html and 'href="#kalCard"' in hub_html)
D9 = (dt.date.today() - dt.timedelta(days=9)).isoformat()
r = c.get("/finance/darpan/kal/" + D9, headers=MAK)
s0, j0 = get("/finance/darpan/kal/api/day?date=" + D9, MAK)
ck("PAGE a day with NO sale report: 200 page, api answers ok with applied=false (no exception)",
   r.status_code == 200 and s0 == 200 and j0.get("ok") and j0["calc"]["applied"] is False and j0.get("day") is None
   and "\u0905\u092d\u0940 \u0928\u0939\u0940\u0902 \u0906\u0908" in html, (r.status_code, s0, j0.get("calc")))

# ---- 1 the arithmetic ---------------------------------------------------------
s, j = get("/finance/darpan/kal/api/day?date=" + Y, MAK)
calc = j.get("calc") or {}
ck("api/day answers for the maker", s == 200 and j.get("ok"), j)
ck("net sale = printout (bills net of the credit note)", calc.get("net_sale_p") == NET * 100, calc.get("net_sale_p"))
ck("home medicine found from the ingest tag (A4 275)", calc.get("home_p") == 27500 and [b["bill"] for b in calc.get("home_bills", [])] == ["A4"], calc.get("home_bills"))
ck("procedure medicine from the typed head (P9 150)", calc.get("proc_p") == 15000, calc.get("proc_bills"))
ck("online = the bank's settled total, not provisional", calc.get("online_p") == BANK * 100 and calc.get("online_provisional") == 0, calc)
ck("expected cash = sale - home - proc - online", calc.get("expected_p") == EXPECTED_Y, calc.get("expected_p"))
ck("returns: count 1, the large one flagged", j["returns"]["count"] == 1 and len(j["returns"]["flagged"]) == 1
   and j["returns"]["flagged"][0]["bill"] == "CN1", j.get("returns"))
ck("no deterrent line anywhere in the page", "deterrent" not in open(os.path.join(KIT, "darpan_kal.html"), encoding="utf-8").read().lower())

# ---- 2 match -> complete, cash_movement landed --------------------------------
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": EXPECTED_Y, "handed_to": "dr_bhawna"})
ck("exact match -> complete, no reason asked", s == 200 and j.get("state") == "complete" and j.get("reason") == "none" and not j.get("needs_reason"), j)
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
mv = con.execute("SELECT * FROM cash_movement WHERE day_entry_id=?", (EID,)).fetchall()
ck("ONE cash_movement out -> dr_bhawna landed on the day's own day_entry", len(mv) == 1 and mv[0]["party"] == "dr_bhawna"
   and mv[0]["direction"] == "out" and mv[0]["amount_p"] == EXPECTED_Y, [dict(m) for m in mv])
ck("v_cash_ledger sees the handover (cash_out_p)", con.execute("SELECT cash_out_p FROM v_cash_ledger WHERE business_date=?", (Y,)).fetchone()[0] == EXPECTED_Y)
s, j = get("/finance/api/cash-position", DOC)
ck("/finance/api/cash-position still answers", s == 200 and j.get("ok"), j)
con.close()

# ---- 3 within tolerance -------------------------------------------------------
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": EXPECTED_Y - 3000, "handed_to": "dr_bhawna"})
ck("Rs 30 short -> still complete (tolerance Rs 50)", j.get("state") == "complete", j)
con = sqlite3.connect(DB)
ck("re-typing updates the SAME cash_movement row", con.execute("SELECT COUNT(*), MIN(amount_p) FROM cash_movement WHERE day_entry_id=?", (EID,)).fetchone() == (1, EXPECTED_Y - 3000))
con.close()

# ---- 4 short: reason asked; online -> confirmed / contradicted ----------------
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": EXPECTED_Y - 21000, "handed_to": "dr_bhawna"})
ck("Rs 210 short -> state open, reason list offered", j.get("state") == "open" and j.get("needs_reason") and j.get("diff_p") == -21000, j)
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": EXPECTED_Y - 21000, "handed_to": "dr_bhawna", "reason": "online_not_on_pos"})
ck("reason 'online not on POS' with a matching bank txn (210) -> confirmed, complete", j.get("verdict") == "confirmed" and j.get("state") == "complete", j)
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": EXPECTED_Y - 33300, "handed_to": "dr_bhawna", "reason": "online_not_on_pos"})
ck("same reason, Rs 333 short, no such txn -> contradicted, needs_owner", j.get("verdict") == "contradicted" and j.get("state") == "needs_owner", j)
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": EXPECTED_Y - 27500, "handed_to": "dr_bhawna", "reason": "home_not_in_print"})
ck("reason 'home medicine not in printout', Rs 275 = the home bill -> confirmed", j.get("verdict") == "confirmed", j)
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": EXPECTED_Y - 40000, "handed_to": "dr_bhawna", "reason": "return_cash"})
ck("reason 'return refunded in cash', no slip, CN exists -> not confirmable (his word stands)", j.get("verdict") == "not_confirmable" and j.get("state") == "explained", j)
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": EXPECTED_Y - 40000, "handed_to": "dr_bhawna", "reason": "other"})
ck("'other' without words is refused", s == 400 and j.get("error") == "note_required", j)
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": EXPECTED_Y - 40000, "handed_to": "dr_bhawna", "reason": "other", "reason_note": "note ka page phat gaya"})
ck("'other' with words -> not confirmable, explained", j.get("verdict") == "not_confirmable" and j.get("state") == "explained", j)
s, j = get("/finance/darpan/kal/api/day?date=" + Y, DOC)
ck("checks are recorded with evidence", len(j.get("checks") or []) >= 5 and all("evidence" in x for x in j["checks"]))

# ---- 5 excess -> owed back, no reason asked -----------------------------------
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": D2, "handed_p": 100000 + 12000, "handed_to": "dr_manoj"})
ck("Rs 120 MORE than expected -> complete, no reason asked", j.get("state") == "complete" and not j.get("needs_reason"), j)
ck("the excess is recorded as owed back to Darpan (provisional: bank not in)",
   len(j.get("owed") or []) == 1 and j["owed"][0]["amount_p"] == 12000 and j["owed"][0]["provisional"] == 1, j.get("owed"))
s, j = get("/finance/darpan/kal/api/day?date=" + D2, MAK)
ck("day before yesterday shows online as provisional (Marg modes)", j["calc"]["online_provisional"] == 1 and j["calc"]["statement_in"] is False)

# ---- 6 flagged return answered ------------------------------------------------
s, j = post("/finance/darpan/kal/api/return-answer", MAK, {"date": Y, "cn_bill": "CN1", "answer": "slip_checked", "flag": "LARGE RETURN"})
ck("return answered 'slip checked'", s == 200 and j.get("ok"), j)
s, j = get("/finance/darpan/kal/api/day?date=" + Y, MAK)
ck("the answer shows on the flagged row", (j["returns"]["flagged"][0].get("answered") or {}).get("answer") == "slip_checked")
s, j = post("/finance/darpan/kal/api/return-answer", MAK, {"date": Y, "cn_bill": "CN1", "answer": "other"})
ck("'other' return answer without words is refused", s == 400)

# ---- 7 Bhawna: mine + received ------------------------------------------------
s, j = get("/finance/darpan/kal/api/mine", BHA)
ck("Dr Bhawna sees the day handed to her", s == 200 and j.get("party") == "dr_bhawna" and [d["business_date"] for d in j["days"]] == [Y], j)
s, j = get("/finance/darpan/kal/api/day?date=" + D2, BHA)
ck("Dr Bhawna cannot open a day handed to Dr Manoj", s == 403, j)
s, j = post("/finance/darpan/kal/api/received", BHA, {"date": D2})
ck("Dr Bhawna cannot mark Dr Manoj's day received", s == 403, j)
s, j = post("/finance/darpan/kal/api/received", BHA, {"date": Y})
ck("Dr Bhawna marks yesterday received", s == 200 and j.get("received_by") == "zzwalkbhawna", j)
s, j = post("/finance/darpan/kal/api/received", BHA, {"date": Y})
ck("a second 'received' is refused (409)", s == 409)
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": 1, "handed_to": "dr_bhawna"})
ck("Darpan cannot change a handover already received", s == 409 and j.get("error") == "already_received", j)

# ---- 8 the owner's card -------------------------------------------------------
s, j = get("/finance/darpan/kal/api/owner", DOC)
kinds = [i["kind"] for i in (j.get("items") or [])]
ck("owner card answers for the checker", s == 200 and j.get("ok"), j)
ck("owner card: the owed-back row is listed", "owed" in kinds, kinds)
ck("owner card: the unreceived Dr Manoj handover is amber", any(i.get("amber") and i["date"] == D2 for i in j["items"]), j.get("items"))
ck("owner card: yesterday is NOT listed as needing him (explained, not contradicted)", not any(i["kind"] == "day" and i["date"] == Y for i in j["items"]), kinds)
ck("owner card: the LARGE RETURN answered 'slip checked' is not raised (only money flags / 'other')", not any(i["kind"] == "return" for i in j["items"]), kinds)
ck("owner card refused to the maker", get("/finance/darpan/kal/api/owner", MAK)[0] == 403)
# make yesterday a contradiction again (owner un-receives is not a thing; use the checker's own hand)
s, j = post("/finance/darpan/kal/api/handover", DOC, {"date": Y, "handed_p": EXPECTED_Y - 33300, "handed_to": "dr_bhawna", "reason": "online_not_on_pos"})
ck("the checker may re-type a received day", s == 200 and j.get("state") == "needs_owner", j)
s, j = get("/finance/darpan/kal/api/owner", DOC)
day_items = [i for i in j["items"] if i["kind"] == "day"]
ck("owner card now lists exactly the contradicted day, one English line with the why",
   len(day_items) == 1 and day_items[0]["date"] == Y and "contradicted" in day_items[0]["line"] and "statement in" in day_items[0]["line"], day_items)
s, j = post("/finance/darpan/kal/api/owner/decide", DOC, {"date": Y, "decision": "ask", "note": "which bill was that payment for?"})
ck("owner 'ask' re-opens the day for Darpan", s == 200 and j.get("state") == "open", j)
s, j = post("/finance/darpan/kal/api/owner/decide", DOC, {"date": Y, "decision": "accept"})
ck("owner 'accept' closes it as explained", s == 200 and j.get("state") == "explained", j)
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": Y, "handed_p": 5, "handed_to": "dr_bhawna"})
ck("after the owner's decision Darpan cannot re-type", s == 409 and j.get("error") == "owner_decided", j)
s, j = get("/finance/darpan/kal/api/owner", DOC)
oid = [i for i in j["items"] if i["kind"] == "owed"][0]["id"]
s, j = post("/finance/darpan/kal/api/owed/returned", DOC, {"id": oid})
ck("owner marks the owed cash returned to Darpan", s == 200 and j.get("status") == "returned", j)
s, j = get("/finance/darpan/kal/api/owner", DOC)
ck("owed row leaves the card; owed total 0", j.get("owed_p") == 0 and not any(i["kind"] == "owed" for i in j["items"]))

# ---- 9 patterns ---------------------------------------------------------------
con = sqlite3.connect(DB)
for k in range(3, 7):
    d = (dt.date.today() - dt.timedelta(days=k)).isoformat()
    con.execute("INSERT INTO darpan_kal_day (unit, business_date, handed_p, handed_to, diff_p, reason, state, verdict) "
                "VALUES ('medical',?,50000,'dr_manoj',-9000,'home_not_in_print','explained','not_confirmable')", (d,))
con.commit()
con.close()
s, j = get("/finance/darpan/kal/api/owner", DOC)
pats = [i for i in j["items"] if i["kind"] == "pattern"]
ck("repeat pattern: same reason 4x in 30 days is one card line", any("home/procedure" in p["line"] and "4 times" in p["line"] for p in pats), pats)

# ---- 10 a day whose report is not in yet --------------------------------------
D9 = (dt.date.today() - dt.timedelta(days=9)).isoformat()
s, j = post("/finance/darpan/kal/api/handover", MAK, {"date": D9, "handed_p": 40000, "handed_to": "dr_manoj"})
ck("a claim on a day with no report is saved as waiting_report", s == 200 and j.get("state") == "waiting_report", j)
con = sqlite3.connect(DB)
ck("no day_entry was created by this kit", con.execute("SELECT COUNT(*) FROM day_entry WHERE business_date=?", (D9,)).fetchone()[0] == 0)
ck("no darpan_kal write touched sale_item / day_line / day_noncash_bill",
   con.execute("SELECT COUNT(*) FROM sale_item").fetchone()[0] == 7 and con.execute("SELECT COUNT(*) FROM day_line").fetchone()[0] == 3
   and con.execute("SELECT COUNT(*) FROM day_noncash_bill").fetchone()[0] == 1)
ck("every act is in darpan_kal_audit", con.execute("SELECT COUNT(*) FROM darpan_kal_audit").fetchone()[0] >= 15)
con.close()

# ---- 11 the recipients seed, twice --------------------------------------------
import subprocess                                                       # noqa: E402
con = sqlite3.connect(DB)
con.execute("DELETE FROM setting WHERE key='darpan_kal.recipients'")     # the walk's own logins are a hand edit; clear them
con.commit(); con.close()
r1 = subprocess.run([sys.executable, "-B", os.path.join(KIT, "seed_kal_recipients_s243.py"), DB], capture_output=True, text=True)
r2 = subprocess.run([sys.executable, "-B", os.path.join(KIT, "seed_kal_recipients_s243.py"), DB], capture_output=True, text=True)
con = sqlite3.connect(DB)
ck("seed_kal_recipients: runs, sets manoj/bhawna, adds bhawna viewer once; second run changes nothing",
   r1.returncode == 0 and r2.returncode == 0
   and con.execute("SELECT value FROM setting WHERE key='darpan_kal.recipients'").fetchone()[0] == "manoj:dr_manoj,bhawna:dr_bhawna"
   and con.execute("SELECT COUNT(*) FROM unit_role WHERE unit='medical' AND username='bhawna' AND role='viewer'").fetchone()[0] == 1
   and "NOT changed" in r2.stdout, (r1.stdout, r2.stdout))
con.close()

print()
print("WALK: %d passed, %d failed" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED:", f)
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if not FAILED else 1)
