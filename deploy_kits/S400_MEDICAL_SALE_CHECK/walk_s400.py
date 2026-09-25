#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s400.py -- kit S400_MEDICAL_SALE_CHECK. THE REAL finance_app.py (the kit's files placed in a copy of
/root/finance) over a SCRATCH COPY of the live finance.db, driven through Flask's test client with header
identity (walk only). Its OWN rows are dated 2099-12-01..04 and found by key, never by counting.

  --app NEW     a copy of /root/finance carrying the kit's files          --old OLD  a copy as the box is (negative control)
  --db PATH     the scratch copy (refused unless its path says so)
  --portal-new DIR / --portal-old DIR   portal.py + tile_grants.json, built and live

Prints dates, bill keys of its own, counts and rupees. No name, no number.
"""
import argparse
import datetime as dt
import io
import json
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--app", required=True)
ap.add_argument("--old", required=True)
ap.add_argument("--db", required=True)
ap.add_argument("--portal-new", required=True)
ap.add_argument("--portal-old", required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
n, fails = 0, []


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


D1, D2, D3, D4 = "2099-12-01", "2099-12-02", "2099-12-03", "2099-12-04"
NOW = dt.datetime.now().replace(microsecond=0).isoformat()

# ------------------------------------------------------------------ the walk's own rows
con = sqlite3.connect(a.db, timeout=30)
con.row_factory = sqlite3.Row
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s400  # noqa: E402
assert seed_s400.seed(a.db) == 0, "seed failed"


def plant():
    c = con
    c.execute("INSERT OR IGNORE INTO patient_ref (clinic_id, name, first_seen) VALUES ('W400-01','Walk Patient One',?)", (D1,))
    pid = c.execute("SELECT id FROM patient_ref WHERE clinic_id='W400-01'").fetchone()[0]
    for d, st, cash, upi in ((D1, "submitted", 100000, 50000), (D2, "submitted", 200000, 0), (D3, "approved", 10000, 0), (D4, "submitted", 30000, 0)):
        c.execute("DELETE FROM day_entry WHERE unit='medical' AND business_date=?", (d,))
        c.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at, approved_by, approved_at) "
                  "VALUES ('medical',?,?,'app','auto',?,?,?)", (d, st, NOW, "manoj" if st == "approved" else None, NOW if st == "approved" else None))
        eid = c.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (d,)).fetchone()[0]
        c.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,'pharmacy_sale','cash',?)", (eid, cash))
        if upi:
            c.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) VALUES (?,'pharmacy_sale','upi',?)", (eid, upi))
    E = {d: c.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (d,)).fetchone()[0] for d in (D1, D2, D3, D4)}
    for k in ("sale_bill", "identity_resolution", "upi_statement", "upi_txn", "darpan_kal_day", "sale_check_day",
              "sale_check_issue", "sale_check_cash"):
        col = "business_date" if k not in ("upi_statement", "upi_txn") else ("statement_date" if k == "upi_statement" else "txn_date")
        if c.execute("SELECT 1 FROM sqlite_master WHERE name=?", (k,)).fetchone():
            c.execute("DELETE FROM %s WHERE %s LIKE '2099-12-%%'" % (k, col))
    c.execute("DELETE FROM sale_line_item WHERE unit='medical' AND bill_no LIKE 'W400%'")
    c.execute("DELETE FROM cash_movement WHERE reference LIKE '[kal] 2099-12-%'")
    for d, bill, net, cashp in ((D1, "W400A001", 100000, 100000), (D1, "W400A002", 50000, 0), (D2, "W400B001", 150000, 150000),
                                (D2, "W400B002", 50000, 50000), (D3, "W400C001", 10000, 10000)):
        c.execute("INSERT INTO sale_bill (unit, business_date, bill_no, gross_p, disc_p, tax_p, drcr_p, net_p, cash_p, noncash_p, "
                  "is_credit_note, round_p, source_name, source_stamp, source_md5, written_at) VALUES "
                  "('medical',?,?,?,0,0,0,?,?,?,0,0,'walk_s400','20991201-000000','walk',?)", (d, bill, net, net, cashp, net - cashp, NOW))
        c.execute("INSERT INTO sale_item (day_entry_id, unit, patient_ref_id, service, description, amount_p, mode, source, source_ref) "
                  "VALUES (?,'medical',?,'pharmacy','walk',?,?,'ocr',?)",
                  (E[d], None if bill == "W400B002" else pid, net, "cash" if cashp else "upi", bill))
    c.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) "
              "VALUES (?,'medical',?,'W400A001',0,1,'WALK TAB','walktab','10','1:0',100000)", (E[D1], D1))
    c.execute("INSERT INTO identity_resolution (unit, business_date, bill_no, rung, clinic_id, bill_name, master_name, noted_at) "
              "VALUES ('medical',?,'W400B002','walk',NULL,'HOME MEDICINE WALK',NULL,?)", (D2, NOW))
    c.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, parsed_total_p, txn_count, ingested_at) "
              "VALUES ('W400MID','medical',?,50000,1,?)", (D1, NOW))
    c.execute("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, rrn, mode, txn_time) VALUES ('W400MID','medical',?,50000,'W400RRN01','upi','10:00:00')", (D1,))
    c.execute("INSERT INTO darpan_kal_day (unit, business_date, handed_p, handed_to, state, created_by, created_at, updated_at) "
              "VALUES ('medical',?,100000,'dr_bhawna','open','darpan',?,?)", (D1, NOW, NOW))
    c.commit()
    return E


E = plant()
real = con.execute("SELECT MAX(business_date) FROM day_entry WHERE unit='medical' AND status IN ('submitted','draft') "
                   "AND business_date < '2099-01-01'").fetchone()[0] or "2026-09-23"
print("-- own rows planted: %s (clean, Darpan 1,000 to Dr Bhawna) · %s (crafted) · %s (approved) · %s (no Marg sheet) · real unapproved day %s"
      % (D1, D2, D3, D4, real))

# ------------------------------------------------------------------ the probes (each app in its own process)
PROBE = r'''
import json, os, sys
sys.path.insert(0, os.environ["APPDIR"]); os.chdir(os.environ["APPDIR"])
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
import finance_app as fa
c = fa.app.test_client()
NEW = os.environ["MODE"] == "new"
D1, D2, D3, D4, REAL = os.environ["D1"], os.environ["D2"], os.environ["D3"], os.environ["D4"], os.environ["REAL"]
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
def P(u, p, b):
    r = c.post(p, json=b, headers=H(u)); return [r.status_code, r.get_json(silent=True)]
out = {"unit": fa._unit_for_path("/finance/salecheck/api/days"), "mounted": "sale_check" in fa.app.blueprints}
GATE = ["/finance/approvals", "/finance/sanjeevni/api/day/" + D1, "/finance/sanjeevni/api/days", "/finance/sanjeevni/api/months",
        "/finance/sanjeevni/api/bank", "/finance/sanjeevni/api/needs-you", "/finance/darpan/kal/month", "/finance/darpan/kal/api/month",
        "/finance/darpan/kal/api/owner", "/finance/salecheck/api/day/" + D3]
out["bhati_gate"] = {p: G("bhati", p)[0] for p in GATE}
out["owner_gate"] = {p: G("manoj", p)[0] for p in GATE}
out["bhati_page"] = G("bhati", "/finance/salecheck")
out["bhati_page"][1] = out["bhati_page"][1][:400] if isinstance(out["bhati_page"][1], str) else out["bhati_page"][1]
out["others_page"] = {u: G(u, "/finance/salecheck")[0] for u in ("darpan", "bhawna", "shavez", "stranger")}
out["real_day_old_shape"] = G("manoj", "/finance/sanjeevni/api/day/" + REAL)
out["real_needs"] = G("manoj", "/finance/sanjeevni/api/needs-you")
out["days_owner"] = G("manoj", "/finance/sanjeevni/api/days")
if not NEW:
    print("JSON:" + json.dumps(out)); raise SystemExit
import sqlite3
db = sqlite3.connect(os.environ["FINANCE_DB"]); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
def moves(d):
    return q("SELECT m.id, m.party, m.amount_p, m.reference FROM cash_movement m JOIN day_entry e ON e.id=m.day_entry_id "
             "WHERE e.unit='medical' AND e.business_date=?", d)
out["list"] = G("bhati", "/finance/salecheck/api/days")
out["day1"] = G("bhati", "/finance/salecheck/api/day/" + D1)
out["day2"] = G("bhati", "/finance/salecheck/api/day/" + D2)
out["day4"] = G("bhati", "/finance/salecheck/api/day/" + D4)
out["day3_owner"] = G("manoj", "/finance/salecheck/api/day/" + D3)[0]
# Sahi hai, twice
out["ok1"] = P("bhati", "/finance/salecheck/api/verdict", {"date": D1})
out["ok2"] = P("bhati", "/finance/salecheck/api/verdict", {"date": D1})
out["ok_rows"] = q("SELECT verdict, checked_by FROM sale_check_day WHERE unit='medical' AND business_date=?", D1)
out["ok_approved"] = P("bhati", "/finance/salecheck/api/verdict", {"date": D3})[0]
# Galti hai on D2
out["g1"] = P("bhati", "/finance/salecheck/api/issue", {"date": D2, "bill": "W400B002", "problem": "amount_differs"})
out["g_other_nonote"] = P("bhati", "/finance/salecheck/api/issue", {"date": D2, "bill": "DAY", "problem": "other", "note": ""})
out["g2"] = P("bhati", "/finance/salecheck/api/issue", {"date": D2, "bill": "DAY", "problem": "other", "note": "walk note"})
out["g_dup"] = P("bhati", "/finance/salecheck/api/issue", {"date": D2, "bill": "W400B002", "problem": "amount_differs"})
out["g_badbill"] = P("bhati", "/finance/salecheck/api/issue", {"date": D2, "bill": "NOPE", "problem": "amount_differs"})[0]
out["issues_after_add"] = q("SELECT id, bill_no, problem, note, added_by FROM sale_check_issue WHERE unit='medical' AND business_date=? AND removed_at IS NULL", D2)
out["sahi_with_issues"] = P("bhati", "/finance/salecheck/api/verdict", {"date": D2})[0]
out["g_remove"] = P("bhati", "/finance/salecheck/api/issue/remove", {"id": out["g2"][1]["id"]})
out["issues_after_remove"] = q("SELECT id, bill_no, problem FROM sale_check_issue WHERE unit='medical' AND business_date=? AND removed_at IS NULL", D2)
out["verdict_d2"] = q("SELECT verdict FROM sale_check_day WHERE unit='medical' AND business_date=?", D2)
# cash on D2 (no Darpan row): default party, re-save, toggle
out["c1"] = P("bhati", "/finance/salecheck/api/cash", {"date": D2, "amount_p": 200000})
out["moves_c1"] = moves(D2)
out["kal_c1"] = q("SELECT handed_p, handed_to, created_by, landed_movement_id, state FROM darpan_kal_day WHERE unit='medical' AND business_date=?", D2)
out["c2"] = P("bhati", "/finance/salecheck/api/cash", {"date": D2, "amount_p": 190000, "party": "dr_bhawna"})
out["moves_c2"] = moves(D2)
out["c3"] = P("bhati", "/finance/salecheck/api/cash", {"date": D2, "amount_p": 190000, "party": "dr_manoj"})
out["moves_c3"] = moves(D2)
out["c_bad"] = P("bhati", "/finance/salecheck/api/cash", {"date": D2, "amount_p": "x"})[0]
out["c_approved"] = P("bhati", "/finance/salecheck/api/cash", {"date": D3, "amount_p": 100})[0]
out["c_badparty"] = P("bhati", "/finance/salecheck/api/cash", {"date": D2, "amount_p": 100, "party": "pool"})[0]
# cash on D1 where Darpan recorded 1,000: Bhati counts 900
out["c_d1"] = P("bhati", "/finance/salecheck/api/cash", {"date": D1, "amount_p": 90000})
out["moves_d1"] = moves(D1)
out["day1_after"] = G("bhati", "/finance/salecheck/api/day/" + D1)
out["day2_after"] = G("bhati", "/finance/salecheck/api/day/" + D2)
out["audit"] = q("SELECT who, action FROM darpan_kal_audit WHERE action LIKE 'salecheck_%' ORDER BY id")
# the owner's side
out["days_owner_after"] = G("manoj", "/finance/sanjeevni/api/days")
out["needs_after"] = G("manoj", "/finance/sanjeevni/api/needs-you")
out["panel_d2"] = G("manoj", "/finance/sanjeevni/api/day/" + D2)
out["panel_d1"] = G("manoj", "/finance/sanjeevni/api/day/" + D1)
out["real_day_new"] = G("manoj", "/finance/sanjeevni/api/day/" + REAL)
out["real_needs_new"] = G("manoj", "/finance/sanjeevni/api/needs-you")
out["page_owner"] = G("manoj", "/finance/approvals")
out["page_owner"][1] = ["bhatiLine(d)" in out["page_owner"][1], "salecheck/api/owner/move" in out["page_owner"][1], "S400_MEDICAL_SALE_CHECK" in out["page_owner"][1]]
# owner change: person, then date
out["mv_party"] = P("manoj", "/finance/salecheck/api/owner/move", {"date": D2, "party": "dr_bhawna"})
out["moves_mvp"] = moves(D2)
out["mv_bhati"] = P("bhati", "/finance/salecheck/api/owner/move", {"date": D2, "party": "dr_manoj"})[0]
out["mv_date"] = P("manoj", "/finance/salecheck/api/owner/move", {"date": D2, "new_date": D4})
out["moves_after_mv"] = {"D2": moves(D2), "D4": moves(D4)}
out["kal_after_mv"] = {"D2": q("SELECT handed_p FROM darpan_kal_day WHERE unit='medical' AND business_date=?", D2),
                       "D4": q("SELECT handed_p, handed_to, created_by FROM darpan_kal_day WHERE unit='medical' AND business_date=?", D4)}
out["sc_after_mv"] = q("SELECT business_date, amount_p, party, moved_from FROM sale_check_cash WHERE unit='medical' AND business_date IN (?,?)", D2, D4)
out["mv_to_approved"] = P("manoj", "/finance/salecheck/api/owner/move", {"date": D4, "new_date": D3})[0]
out["mv_to_handed"] = P("manoj", "/finance/salecheck/api/owner/move", {"date": D4, "new_date": D1})[0]
out["audit_mv"] = q("SELECT who, action FROM darpan_kal_audit WHERE action LIKE 'salecheck_owner%' ORDER BY id")
out["days_owner_final"] = G("manoj", "/finance/sanjeevni/api/days")
print("JSON:" + json.dumps(out))
'''


def probe(appdir, mode):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=a.db, D1=D1, D2=D2, D3=D3, D4=D4, REAL=real,
               FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1")
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s" % (mode, p.stderr[-2500:]))
    return O


O = probe(a.old, "old")            # read-only: nothing in the old app writes
N = probe(a.app, "new")

# ------------------------------------------------------------------ 1 · mounted, the gate
print("-- 1  the unit, the page, the gate")
check("finance_app resolves /finance/salecheck/... to the unit 'salecheck' and mounts sale_check", N["unit"] == "salecheck" and N["mounted"], (N["unit"], N["mounted"]))
check("bhati opens his page (200) and it is the S400 page", N["bhati_page"][0] == 200 and "Medical sale check" in N["bhati_page"][1], N["bhati_page"][0])
bad = {p: s for p, s in N["bhati_gate"].items() if s not in (302, 401, 403)}
check("bhati is refused on every §6 address: approvals, day/days/months/bank/needs-you, Darpan's month page + APIs, owner card, an APPROVED day", not bad, bad or N["bhati_gate"])
bad = {p: s for p, s in N["owner_gate"].items() if s != 200}
check("the owner keeps everything on the same addresses (all 200)", not bad, bad or "all 200")
check("darpan, bhawna, shavez, a stranger cannot open Bhati's page", all(s in (302, 403) for s in N["others_page"].values()), N["others_page"])
check("the approved day answers 200 to the owner on Bhati's own API", N["day3_owner"] == 200, N["day3_owner"])

# ------------------------------------------------------------------ 2 · the list and a day
print("-- 2  the list, one day, what is never shown")
L = [d["date"] for d in N["list"][1]["days"]]
mine = [d for d in L if d.startswith("2099-12")]
check("the list carries the three unapproved walk days oldest first and NOT the approved one", mine == [D1, D2, D4], mine)
check("the list is in date order from the log-from date (oldest first)", L == sorted(L) and all(d >= N["list"][1]["log_from"] for d in L), (L[:2], L[-2:]))
row = next(d for d in N["list"][1]["days"] if d["date"] == D1)
check("a card: date, weekday, Marg bills count and sale, one status chip", row["bills"] == 2 and row["sale"] == "1,500" and row["chip"]["text"] == "Jaanch baaki" and row["weekday"], row)
d1 = N["day1"][1]
check("a day opens: Marg bills each with bill no, name as the system shows it, amount, its medicines",
      d1["sale"]["bills"] == 2 and d1["sale"]["list"][0]["bill"] == "W400A001" and d1["sale"]["list"][0]["name"].startswith("Walk Patient")
      and d1["sale"]["list"][0]["amount"] == "1,000" and d1["sale"]["list"][0]["items"][0]["item"] == "WALK TAB", d1["sale"])
check("returns · UPI from the bank (time, last 4 of the reference) · Home/Procedure · Cash received",
      d1["returns"]["count"] == 0 and d1["upi"]["total"] == "500" and d1["upi"]["payments"][0]["time"] == "10:00" and d1["upi"]["payments"][0]["ref"] == "...RN01"
      and d1["without_cash"]["total"] == "0" and d1["cash_received"] == "1,000", (d1["upi"], d1["cash_received"]))
check("what Darpan recorded as handed is shown (1,000 to Dr Bhawna)", d1["darpan"] and d1["darpan"]["handed"] == "1,000" and d1["darpan"]["to"] == "dr_bhawna", d1["darpan"])
hidden = [k for k in ("drawer", "drawer_p", "went", "position", "pool", "paid_elsewhere", "adjustments", "expenses", "needs_you", "banked", "months") if k in d1]
check("NEVER shown to Bhati: drawer, where it went, position/pool, deposits, banks, months, other days' totals", not hidden, hidden or "none of them")
check("every rupee here is the owner's day panel's own (cash_received_p = 1,00,000 paise)", d1["cash_received_p"] == 100000, d1["cash_received_p"])

# ------------------------------------------------------------------ 3 · the red flags
print("-- 3  the red flags: each fires on a crafted day, all quiet on a clean one")
f2 = N["day2"][1]["flags"]
check("crafted day: 'Darpan recorded no handover' fires", any("Darpan ne cash ka hisaab nahi likha" in f for f in f2), f2)
check("crafted day: 'a bill with no patient name' fires and names it", any("naam nahi" in f and "W400B002" in f for f in f2), f2)
check("crafted day: 'a HOME bill with no deduction' fires (identity_resolution text, no day_noncash_bill row)", any("W400B002 HOME" in f and "kata nahi" in f for f in f2), f2)
f4 = N["day4"][1]["flags"]
check("a day with no Marg sale report: 'Marg ki sale report abhi nahi aayi' fires", any("Marg ki sale report" in f for f in f4), f4)
check("the clean day carries no flag at all", N["day1"][1]["flags"] == [], N["day1"][1]["flags"])
f1 = N["day1_after"][1]["flags"]
check("after Bhati counts 900 against 1,000 expected: 'handover ≠ cash received' fires with the difference (100 kam)",
      any("900" in f and "1,000" in f and "kam" in f and "100" in f for f in f1) and len(f1) == 1, f1)
check("the list's card carries the same flags as the day", next(d for d in N["list"][1]["days"] if d["date"] == D2)["flags"] == f2)

# ------------------------------------------------------------------ 4 · Sahi hai / Galti hai
print("-- 4  Sahi hai · Galti hai")
check("Sahi hai stores once (verdict ok, by bhati)", N["ok1"][0] == 200 and not N["ok1"][1]["already"] and N["ok_rows"] == [{"verdict": "ok", "checked_by": "bhati"}], (N["ok1"], N["ok_rows"]))
check("a second tap does not create a second entry (answers 'already'; still ONE row)", N["ok2"][0] == 200 and N["ok2"][1]["already"] and len(N["ok_rows"]) == 1, N["ok2"])
check("Sahi hai on an approved day is refused to Bhati (403)", N["ok_approved"] == 403, N["ok_approved"])
check("a galti with bill + problem stores", N["g1"][0] == 200 and N["g1"][1]["problem"] == "amount_differs" and N["g1"][1]["bill"] == "W400B002", N["g1"])
check("'Aur kuch' without a note is refused (400)", N["g_other_nonote"][0] == 400, N["g_other_nonote"])
check("'Aur kuch' with a note stores against 'Poora din'", N["g2"][0] == 200 and N["g2"][1]["bill"] == "Poora din", N["g2"])
check("the same galti again is refused (409 already) -- no duplicate", N["g_dup"][0] == 409 and N["g_dup"][1].get("already"), N["g_dup"])
check("a bill not of the day is refused", N["g_badbill"] == 400, N["g_badbill"])
check("stored in English keys; two active issues; verdict 'wrong'", [i["problem"] for i in N["issues_after_add"]] == ["amount_differs", "other"]
      and N["issues_after_add"][1]["note"] == "walk note" and N["verdict_d2"] == [{"verdict": "wrong"}], N["issues_after_add"])
check("Sahi hai while a galti stands is refused (409)", N["sahi_with_issues"] == 409, N["sahi_with_issues"])
check("Bhati removes his own galti; one remains", N["g_remove"][0] == 200 and len(N["issues_after_remove"]) == 1, N["issues_after_remove"])
check("the day's chip reads 'Galti — 1'", N["day2_after"][1]["chip"]["text"] == "Galti — 1", N["day2_after"][1]["chip"])

# ------------------------------------------------------------------ 5 · the cash
print("-- 5  the cash Darpan handed: one movement through darpan_kal's own path")
check("Bhati's amount lands: darpan_kal_day row created by bhati, party dr_bhawna BY DEFAULT, state decided",
      N["c1"][0] == 200 and N["kal_c1"] == [{"handed_p": 200000, "handed_to": "dr_bhawna", "created_by": "bhati", "landed_movement_id": N["moves_c1"][0]["id"], "state": N["kal_c1"][0]["state"]}]
      and N["kal_c1"][0]["state"] in ("complete", "open", "explained"), (N["c1"], N["kal_c1"]))
check("exactly ONE cash_movement on the day, reference '[kal] <date> -> dr_bhawna', 2,000", len(N["moves_c1"]) == 1 and N["moves_c1"][0]["amount_p"] == 200000
      and N["moves_c1"][0]["reference"] == "[kal] %s -> dr_bhawna" % D2, N["moves_c1"])
check("a re-save (1,900) UPDATES the same row -- same id, new amount, still one", len(N["moves_c2"]) == 1 and N["moves_c2"][0]["id"] == N["moves_c1"][0]["id"]
      and N["moves_c2"][0]["amount_p"] == 190000, N["moves_c2"])
check("the toggle to Dr Manoj changes the same row's party", len(N["moves_c3"]) == 1 and N["moves_c3"][0]["id"] == N["moves_c1"][0]["id"] and N["moves_c3"][0]["party"] == "dr_manoj", N["moves_c3"])
check("the date is always the sale date (the movement sits on that day's own entry; no date is typed)", N["c3"][1]["date"] == D2 and "date" not in {k for k in N["c3"][1] if k == "new_date"}, N["c3"][1]["date"])
check("a bad amount 400, an approved day 403, a bad party 400", (N["c_bad"], N["c_approved"], N["c_badparty"]) == (400, 403, 400), (N["c_bad"], N["c_approved"], N["c_badparty"]))
c = N["day1_after"][1]["cash"]
check("Darpan recorded 1,000, Bhati counted 900: Bhati's figure is the checked one, the difference (100) shown, Darpan's figure kept",
      N["c_d1"][0] == 200 and c and c["amount"] == "900" and c["darpan"] == "1,000" and c["diff_p"] == -10000 and c["diff"] == "100"
      and N["day1_after"][1]["darpan"]["handed"] == "1,000", c)
check("that day too has exactly one movement, 900 (the row Darpan's own entry would have used)", len(N["moves_d1"]) == 1 and N["moves_d1"][0]["amount_p"] == 90000, N["moves_d1"])
check("every write is in darpan_kal_audit under bhati", [x["action"] for x in N["audit"]] == ["salecheck_ok", "salecheck_issue", "salecheck_issue", "salecheck_issue_removed",
      "salecheck_cash", "salecheck_cash", "salecheck_cash", "salecheck_cash"] and all(x["who"] == "bhati" for x in N["audit"]), N["audit"])

# ------------------------------------------------------------------ 6 · the owner's side
print("-- 6  the owner's side")
DA = {d["date"]: d for d in N["days_owner_after"][1]["days"]}
check("the owner's days API carries Bhati's mark: 'Bhati ✓ <time>' on the checked day, with his cash entry and Darpan's differing figure",
      DA[D1]["bhati"]["verdict"] == "ok" and DA[D1]["bhati"]["text"].startswith("Bhati ✓ ") and DA[D1]["bhati"]["cash"]["amount"] == "900"
      and DA[D1]["bhati"]["cash"]["darpan"] == "1,000" and DA[D1]["bhati"]["cash"]["diff_p"] == -10000, DA[D1].get("bhati"))
check("'Bhati: 1 mistake' with the list (bill, problem, note) on the day with a galti", DA[D2]["bhati"]["text"] == "Bhati: 1 mistake"
      and DA[D2]["bhati"]["issues"] == [{"bill": "W400B002", "problem": "amount differs", "note": ""}], DA[D2].get("bhati"))
check("nothing on an unchecked day", DA[D4]["bhati"] is None, DA[D4].get("bhati"))
NL = [l["text"] for l in N["needs_after"][1]["lines"]]
check("Needs you gains 'Bhati found mistakes on 1 day'", "Bhati found mistakes on 1 day" in NL, NL)
ck = [x["text"] for x in N["panel_d2"][1]["checks"] if "Bhati" in x["text"]]
check("the day panel's Checks say what Bhati found (the galti list) and the cash he entered", any("Bhati found 1 mistake" in t and "W400B002" in t for t in ck)
      and any("Bhati entered the cash" in t and "1,900" in t and "you" in t for t in ck), ck)
ck1 = [x for x in N["panel_d1"][1]["checks"] if "Bhati" in x["text"]]
check("on the checked day: his verdict (ok) and his cash with Darpan's figure named", any(x["ok"] is True and "correct" in x["text"] for x in ck1)
      and any("Darpan had recorded 1,000" in x["text"] for x in ck1), [x["text"] for x in ck1])
check("the approvals page carries the S400 line and the owner's change control", N["page_owner"][0] == 200 and all(N["page_owner"][1]), N["page_owner"])
check("the owner changes the PERSON of Bhati's entry (-> Dr Bhawna): the same movement's party changes", N["mv_party"][0] == 200 and len(N["moves_mvp"]) == 1
      and N["moves_mvp"][0]["party"] == "dr_bhawna", N["moves_mvp"])
check("Bhati cannot use the owner's change (403)", N["mv_bhati"] == 403, N["mv_bhati"])
check("the owner moves the DATE (%s -> %s): the movement now sits on the new day only, the kal row and the check row follow" % (D2[-2:], D4[-2:]),
      N["mv_date"][0] == 200 and N["moves_after_mv"]["D2"] == [] and len(N["moves_after_mv"]["D4"]) == 1 and N["moves_after_mv"]["D4"][0]["amount_p"] == 190000
      and N["kal_after_mv"]["D2"] == [] and N["kal_after_mv"]["D4"] == [{"handed_p": 190000, "handed_to": "dr_bhawna", "created_by": "bhati"}]
      and N["sc_after_mv"] == [{"business_date": D4, "amount_p": 190000, "party": "dr_bhawna", "moved_from": D2}], (N["mv_date"], N["moves_after_mv"], N["sc_after_mv"]))
check("a move onto an APPROVED day is refused (409); onto a day that already has a handover is refused (409)", (N["mv_to_approved"], N["mv_to_handed"]) == (409, 409),
      (N["mv_to_approved"], N["mv_to_handed"]))
check("both owner changes are audited", [x["action"] for x in N["audit_mv"]] == ["salecheck_owner_party", "salecheck_owner_move"] and all(x["who"] == "manoj" for x in N["audit_mv"]), N["audit_mv"])
DF = {d["date"]: d for d in N["days_owner_final"][1]["days"]}
check("after the move the days API shows the cash on the new day, none on the old", DF[D4]["bhati"]["cash"]["amount"] == "1,900" and (DF[D2]["bhati"] or {}).get("cash") is None, (DF[D4].get("bhati"), DF[D2].get("bhati")))

# ------------------------------------------------------------------ 7 · unchanged for a real day; the negative control
print("-- 7  a real unapproved day is unchanged; the negative control (the box as it is)")
o, nw = O["real_day_old_shape"][1], N["real_day_new"][1]
check("the owner's day panel for the real unapproved day %s is unchanged (every key, every rupee; Checks identical)" % real, o == nw,
      [k for k in set(o) | set(nw) if o.get(k) != nw.get(k)])
on = [l["text"] for l in O["real_needs"][1]["lines"]]
nn = [l["text"] for l in N["real_needs_new"][1]["lines"] if not l["text"].startswith("Bhati found")]
check("Needs you is unchanged except the new Bhati line", on == nn, (on, nn))
check("NEGATIVE CONTROL: on the box as it is, bhati's page does not open (the route is behind the medical gate)", O["bhati_page"][0] != 200, O["bhati_page"][0])
check("NEGATIVE CONTROL: on the box as it is, bhati is refused on every §6 address too (the leak never existed; this kit adds his door without opening another)",
      all(s in (302, 401, 403) for s in O["bhati_gate"].values()), O["bhati_gate"])
check("NEGATIVE CONTROL: the old days API carries no Bhati mark, the old Needs you no Bhati line, the old page no S400 code",
      all("bhati" not in d for d in O["days_owner"][1]["days"]) and not any(t.startswith("Bhati found") for t in on) and O["unit"] == "medical" and not O["mounted"],
      (O["unit"], O["mounted"]))

# ------------------------------------------------------------------ 8 · the portal tile
print("-- 8  the portal tile")


def tiles(pdir):
    src = io.open(os.path.join(pdir, "portal.py"), encoding="utf-8").read()
    head = src[:src.index("# ---------------------------------------------------------------------------\n# AUTH HELPERS")]
    ns = {"__name__": "p", "__file__": os.path.join(pdir, "portal.py")}
    exec(compile(head, "<p>", "exec"), ns)
    return {(u, r): sorted(sum([[t["name"] for t in ts] for g, ts in ns["_visible_sections"](r, False, u)], []))
            for u in ("manoj", "bhawna", "darpan", "shavez", "bhati", "alisha", "shivani", "amir", "nobody") for r in ("doctor", "staff", "manager")}


try:
    T0, T1 = tiles(a.portal_old), tiles(a.portal_new)
    changed = sorted(k for k in T0 if T0[k] != T1[k])
    check("the tile 'Medical sale check' shows for bhati (staff) and the owner (doctor)", "Medical sale check" in T1[("bhati", "staff")] and "Medical sale check" in T1[("manoj", "doctor")],
          (T1[("bhati", "staff")]))
    check("darpan, bhawna, shavez and every other staff login see NO change; nothing is lost anywhere",
          all(k[0] == "bhati" or k[1] == "doctor" for k in changed) and all(not (set(T0[k]) - set(T1[k])) for k in changed)
          and all(set(T1[k]) - set(T0[k]) == {"Medical sale check"} for k in changed), changed)
    g = json.load(open(os.path.join(a.portal_new, "tile_grants.json"), encoding="utf-8"))
    check("tile_grants.json is v26 and grants the tile to bhati by name", g["version"] == 26 and "Medical sale check" in g["users"]["bhati"]["extra"], g["version"])
except Exception as ex:  # noqa: BLE001
    check("the portal head executes for the tile check", False, repr(ex)[:200])

print(("WALK_S400 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S400 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
