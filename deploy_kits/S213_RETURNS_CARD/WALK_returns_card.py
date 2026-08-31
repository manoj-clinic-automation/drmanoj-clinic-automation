#!/usr/bin/env python3
# =============================================================================
#  WALK_returns_card.py · S213 · the LIVE-SHAPE walk for the returns card
#
#  Reproduces the LIVE darpan_app.py bytes' patched form, builds a REAL
#  database from the real schemas, loads returns in all three populations,
#  and drives the REAL routes through a real Flask test client:
#
#   1  the patch applies to the live bytes and refuses everything else
#   2  cn-detail: three populations, counts, money, verdicts
#   3  THE GET WRITES NOTHING (the S212 defect, proven fixed)
#   4  approve/reject: the POST creates the row; a rejection needs a note
#   5  a decided return stops counting as pending
#   6  the r2 finance_app patch: returns= and payment= reach the JSON
#   7  the html: sump renderer present, old body gone
#
#  Run:  python -B WALK_returns_card.py
# =============================================================================
import hashlib, json, os, shutil, sqlite3, subprocess, sys, tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = []
def check(name, cond):
    CHECKS.append((name, bool(cond)))
    print("  [%s] %s" % ("ok " if cond else "FAIL", name))

tmp = tempfile.mkdtemp(prefix="walk_card_")
sys.path.insert(0, tmp)

# ---- where the pieces live: sibling kits, by RELATIVE path ------------------
# (S212 lesson: three kits were hard-coded to the assistant's sandbox mount and
# could not run on the owner's machine at all. Everything here is relative to
# THIS file, so the walk runs from inside the kit folder on any machine.)
KITS = os.path.dirname(HERE)                       # .../deploy_kits
REPO = os.path.dirname(KITS)                       # the repository root
def _find(*cands):
    for c in cands:
        if os.path.exists(c):
            return c
    print("!! missing:", cands[0]); sys.exit(2)
SUMP   = _find(os.path.join(KITS, "S212_SUMP"), HERE)
MATCH  = _find(os.path.join(KITS, "S211_MATCH"), HERE)
SQL    = _find(os.path.join(REPO, "finance", "finance_returns.sql"),
               os.path.join(HERE, "finance_returns.sql"))
sys.path.insert(1, SUMP)     # finance_money, finance_returns_audit
sys.path.insert(2, MATCH)    # finance_daily_gaps, finance_patient_match

# ---- 1 · REPRODUCE the live darpan bytes, then apply the patch --------------
# live pin b694bfdd... = S208_CONSOLE base + S209_LEDGERMSG + S210_HANDOVER
# (KB Register v5.61 row for /root/finance/darpan_app.py)
base = os.path.join(HERE, "base_darpan_app.py")
if not os.path.exists(base):
    base = os.path.join(tmp, "base_darpan_app.py")
    shutil.copy(_find(os.path.join(KITS, "S208_CONSOLE", "darpan_app.py")), base)
    for pk in (os.path.join(KITS, "S209_LEDGERMSG", "patch_darpan_msg.py"),
               os.path.join(KITS, "S210_HANDOVER", "patch_darpan_app_handover.py")):
        rr = subprocess.run([sys.executable, "-B", _find(pk), base],
                            capture_output=True, text=True)
        if rr.returncode != 0:
            print("!! base rebuild failed at", pk, rr.stdout, rr.stderr); sys.exit(2)
h = hashlib.md5(open(base, "rb").read()).hexdigest()
check("the rebuilt base IS the live pin (b694bfdd...)",
      h == "b694bfddf7766965b6552abbe341698e")
shutil.copy(base, os.path.join(tmp, "darpan_app.py"))
r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_darpan_returns.py"),
                    os.path.join(tmp, "darpan_app.py")], capture_output=True, text=True)
check("patch applies to the live bytes", r.returncode == 0 and "patched OK" in r.stdout)
r2 = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_darpan_returns.py"),
                     os.path.join(tmp, "darpan_app.py")], capture_output=True, text=True)
check("second apply is a no-op", "already patched" in r2.stdout)

# ---- the database, from the real schemas ------------------------------------
db_path = os.path.join(tmp, "walk.db")
con = sqlite3.connect(db_path)
con.row_factory = sqlite3.Row
con.executescript("""
CREATE TABLE business_unit (code TEXT PRIMARY KEY);
INSERT INTO business_unit VALUES ('medical');
CREATE TABLE day_entry (id INTEGER PRIMARY KEY, unit TEXT NOT NULL,
  business_date TEXT NOT NULL, status TEXT);
CREATE TABLE ingest_batch (id INTEGER PRIMARY KEY);
CREATE TABLE sale_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER,
  unit TEXT, service TEXT, source_ref TEXT, amount_p INTEGER,
  patient_ref_id INTEGER, mode TEXT, gross_p INTEGER, disc_p INTEGER,
  description TEXT);
CREATE TABLE day_line (id INTEGER PRIMARY KEY, day_entry_id INTEGER,
  mode TEXT, amount_p INTEGER);
CREATE TABLE upi_statement (id INTEGER PRIMARY KEY, unit TEXT,
  statement_date TEXT, parsed_total_p INTEGER, txn_count INTEGER);
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT,
  phone_last4 TEXT, admin_pd_pct REAL, patient_uid TEXT,
  mobile TEXT);  -- mobile/admin_pd_pct/gross_p/disc_p/description mirror LIVE-ONLY columns (D356/S193)
CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
""")
con.executescript(open(SQL).read()
                  .replace("BEGIN;", "").replace("COMMIT;", ""))

def day(d):
    cur = con.execute("INSERT INTO day_entry (unit, business_date, status) "
                      "VALUES ('medical', ?, 'locked')", (d,))
    return cur.lastrowid

def bill(deid, ref, amount_p, pid=None, service="pharmacy"):
    con.execute("INSERT INTO sale_item (day_entry_id, unit, service, source_ref,"
                " amount_p, patient_ref_id) VALUES (?,?,?,?,?,?)",
                (deid, 'medical', service, ref, amount_p, pid))

def line(d, ref, seq, item, qty, rate_p, ret=1, pack="1*10", batch="B1", exp="2027-01"):
    key = item.lower().replace(" ", "")
    con.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date,"
                " bill_no, is_return, seq, item_name, item_key, pack, qty_raw,"
                " amount_p, expiry_ym, batch) VALUES "
                " ((SELECT id FROM day_entry WHERE business_date=?),'medical',?,?,?,?,?,?,?,?,?,?,?)",
                (d, d, ref, ret, seq, item, key, pack, qty, rate_p, exp, batch))

con.execute("INSERT INTO patient_ref (id, clinic_id, name, phone_last4) "
            "VALUES (1,'842','Nanhi Devi','4321')")
M = "2026-08"
d_prior = day(M + "-10"); d_ret = day(M + "-20")
# the patient's own earlier sale: SALE10 with two items
bill(d_prior, "SALE10", 45000, pid=1)
line(M + "-10", "SALE10", 1, "AXIMAL 200", "1:0", 15000, ret=0)
line(M + "-10", "SALE10", 2, "TRAMAVIN P", "1:0", 15000, ret=0)
# CN001 -- audited, clean: same item, same qty, same rate
bill(d_ret, "CN001", 15000, pid=1, service="pharmacy_return")
line(M + "-20", "CN001", 1, "AXIMAL 200", "1:0", 15000)
# CN002 -- audited, NEVER BOUGHT
bill(d_ret, "CN002", 9000, pid=1, service="pharmacy_return")
line(M + "-20", "CN002", 1, "ETOZOX 90", "1:0", 9000)
# CN003 -- bill row only, no lines (unexaminable)
bill(d_ret, "CN003", 5000, pid=1, service="pharmacy_return")
# OR004 -- orphan: lines, no bill row
line(M + "-20", "OR004", 1, "RUNVACE TP", "1:0", 4000)
# CN005 -- discounted return: goods worth 150.00, refunded 130.00 (Rs 20 withheld)
bill(d_ret, "CN005", 13000, pid=1, service="pharmacy_return")
line(M + "-20", "CN005", 1, "TRAMAVIN P", "1:0", 15000)
con.commit()

# ---- mount the PATCHED module in a real Flask app ---------------------------
from flask import Flask
import darpan_app as D
check("the patched module carries the mark", "S213 (returns sump r1)" in open(
    os.path.join(tmp, "darpan_app.py"), encoding="utf-8").read())

app = Flask(__name__)
def get_db():
    c = sqlite3.connect(db_path); c.row_factory = sqlite3.Row
    return c
USER = {"user": "drmanoj", "role": "owner"}
def require(role):
    return USER, None
D.init(app, get_db, require, "medical")
D._is_owner = lambda con, u: True
c = app.test_client()

print("— 2 · cn-detail over the sump")
j = c.get("/finance/darpan/api/cn-detail?month=" + M).get_json()
check("ok", j and j.get("ok") is True)
check("all five returns seen (old card saw three)", j["count"] == 5)
check("populations: 3 audited · 1 orphan · 1 no-item-detail",
      j["audited"] == 3 and j["orphans"] == 1 and j["no_item_detail"] == 1)
by = {n["bill"]: n for n in j["notes"]}
check("CN001 is ok", by["CN001"]["verdict"] == "ok")
check("CN002 is NEVER BOUGHT", by["CN002"]["verdict"] == "NEVER BOUGHT")
check("CN003 says not examinable, not clean",
      by["CN003"]["verdict"] == "not examinable" and by["CN003"]["needs_approval"])
check("OR004 has no patient attributed and shows its Marg lines",
      by["OR004"]["verdict"] == "no patient attributed" and len(by["OR004"]["marg_lines"]) == 1)
check("CN005 is a DISCOUNTED RETURN with Rs 20.00 withheld",
      by["CN005"]["verdict"] == "DISCOUNTED RETURN" and
      by["CN005"]["refund_shortfall_p"] == 2000)
check("money: total is net where a bill row exists, gross for the orphan",
      j["total_p"] == 15000 + 9000 + 5000 + 4000 + 13000)
check("four need approval, none decided yet", j["pending_approval"] == 4)

print("— 3 · the GET wrote nothing")
n_rows = get_db().execute("SELECT COUNT(*) c FROM darpan_return_approval").fetchone()["c"]
check("darpan_return_approval is EMPTY after the read", n_rows == 0)

print("— 4 · the POST is what decides — and creates")
r = c.post("/finance/darpan/api/cn-approve", json={"bill": "CN002", "decision": "rejected"})
check("a rejection without a note is refused", r.status_code == 400)
r = c.post("/finance/darpan/api/cn-approve",
           json={"bill": "CN002", "decision": "rejected", "note": "counter to explain"})
check("reject with note lands", r.get_json().get("ok") is True)
r = c.post("/finance/darpan/api/cn-approve", json={"bill": "CN003", "decision": "approved"})
check("approve creates the row on POST", r.get_json().get("ok") is True)
r = c.post("/finance/darpan/api/cn-approve", json={"bill": "NOPE99", "decision": "approved"})
check("a bill this server never saw is refused", r.status_code == 404)
rows = get_db().execute("SELECT cn_bill, status, business_date FROM "
                        "darpan_return_approval ORDER BY cn_bill").fetchall()
check("exactly the two decided rows exist, dated from the data",
      [ (r2["cn_bill"], r2["status"]) for r2 in rows ] ==
      [("CN002", "rejected"), ("CN003", "approved")] and
      all(r2["business_date"] == M + "-20" for r2 in rows))

print("— 5 · decided returns stop counting as pending")
j2 = c.get("/finance/darpan/api/cn-detail?month=" + M).get_json()
check("pending fell 4 -> 2", j2["pending_approval"] == 2)
check("the decision is visible on the card",
      by2 := {n["bill"]: n for n in j2["notes"]},)
check("CN002 shows REJECTED with the note",
      by2["CN002"]["approval"]["status"] == "rejected" and
      "counter" in (by2["CN002"]["approval"]["note"] or ""))

print("— 6 · the r2 finance_app patch: returns/payment reach the JSON")
mini = '''import sqlite3
from flask import Flask, jsonify, request
app = Flask(__name__)
UNIT = "medical"
DBP = %r
def db():
    c = sqlite3.connect(DBP); c.row_factory = sqlite3.Row
    return c
def require(role):
    return {"user": "drmanoj"}, None
@app.route("/finance/api/marg-push/apply", methods=["POST"])
def marg_apply():
    return jsonify(ok=True)
''' % db_path
open(os.path.join(tmp, "mini_finance_app.py"), "w").write(mini)
# the LIVE box's path: r1 was found already installed (31-Aug) -- so walk the
# UPGRADE: apply the original S211 patch first, then r2 on top of it.
r1p = _find(os.path.join(KITS, "S211_PANEL", "patch_finance_app_panel.py"),
            os.path.join(HERE, "patch_finance_app_panel.py"))
r = subprocess.run([sys.executable, "-B", r1p, os.path.join(tmp, "mini_finance_app.py")],
                   capture_output=True, text=True)
check("r1 (the S211 patch) applies first, as on the live box",
      r.returncode == 0 and "patched OK" in r.stdout)
r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_finance_app_panel_r2.py"),
                    os.path.join(tmp, "mini_finance_app.py")], capture_output=True, text=True)
check("r2 patch UPGRADES the r1-installed file", r.returncode == 0 and "patched OK" in r.stdout)
import mini_finance_app as F
fc = F.app.test_client()
jj = fc.get("/finance/api/day-gaps?d=" + M + "-20").get_json()
check("day-gaps answers ok", jj and jj.get("ok") is True)
check("returns= is IN the JSON (the dropped key, restored)",
      isinstance(jj.get("returns"), list) and len(jj["returns"]) == 5)
check("returns_summary carries the day's money",
      jj.get("returns_summary", {}).get("value_p") == 46000)
check("payment= is IN the JSON", "payment" in jj)

print("— 7 · the html")
h = open(os.path.join(HERE, "finance_approvals.html"), encoding="utf-8").read()
check("sump renderer present (S213 mark)", "S213 (returns sump r1)" in h)
check("populations named on the card", "UNEXAMINABLE, not clean" in h)
check("the Marg-export table is offered", "as Marg exported it" in h)
check("approve/reject buttons kept", "cnDecide" in h and "Reject — recover" in h)
check("day-gaps card renders the returns line", "Sale returns this day" in h)
check("no localStorage anywhere", "localStorage" not in h)
check("the gaps card of S211_PANEL survives", 'id="gapCard"' in h)

fails = [n for n, ok in CHECKS if not ok]
print()
if fails:
    print("WALK FAILED:", ", ".join(fails)); sys.exit(1)
print("ALL WALK CHECKS PASS (%d)" % len(CHECKS))
