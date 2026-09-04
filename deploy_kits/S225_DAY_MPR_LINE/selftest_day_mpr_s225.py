#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_day_mpr_s225.py -- patch the EXACT live bytes of finance_clinic_day.py (dceb79a0, held in
S223_DAY_PAGE_EDITS), mount it with the REAL bank_mpr_status.py (S224) on a temp finance.db, and read the
day page and the month page as the clinic checker: applied-and-matching, applied-and-differing, waiting,
module-absent. Run from inside the kit folder:  python3 -B selftest_day_mpr_s225.py"""
import datetime as dt, hashlib, io, json, os, shutil, sqlite3, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); KITS = os.path.dirname(HERE)
LIVE = "dceb79a06e71f7e35150c69e1f5dd175"
W = tempfile.mkdtemp(prefix="s225mpr_")
def md5(p): return hashlib.md5(io.open(p, "rb").read()).hexdigest()
P, F = [], []
def ck(label, cond, detail=""):
    (P if cond else F).append(label); print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % detail) if detail and not cond else ""))
src = os.path.join(KITS, "S223_DAY_PAGE_EDITS", "finance_clinic_day.py")
ck("the repo holds the live bytes of finance_clinic_day.py (%s)" % LIVE, md5(src) == LIVE, md5(src))
tgt = os.path.join(W, "finance_clinic_day.py"); shutil.copy(src, tgt)
shutil.copy(os.path.join(KITS, "S224_BANK_MPR_STATUS", "bank_mpr_status.py"), W)
env = dict(os.environ, FCD_PATH=tgt)
r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_clinic_day_mpr_s225.py"), "0" * 32], env=env, capture_output=True, text=True)
ck("wrong md5 REFUSES, file untouched", r.returncode != 0 and "REFUSING" in r.stdout + r.stderr and md5(tgt) == LIVE)
r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_clinic_day_mpr_s225.py"), LIVE], env=env, capture_output=True, text=True)
ck("patch applies, prints NEW PIN", r.returncode == 0 and "NEW PIN" in r.stdout, (r.stdout + r.stderr)[-300:])
NEW = md5(tgt); print("     NEW PIN (predicted)  %s" % NEW)
r2 = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_clinic_day_mpr_s225.py"), NEW], env=env, capture_output=True, text=True)
ck("second run: ALREADY PATCHED, pin unchanged", r2.returncode == 0 and "ALREADY PATCHED" in r2.stdout and md5(tgt) == NEW)
# ---- the app
sys.path.insert(0, W)
from flask import Flask, g, jsonify
import finance_clinic_day as FCD, bank_mpr_status as BMS
DB = os.path.join(W, "finance.db")
con0 = sqlite3.connect(DB)
sch = io.open(os.path.join(KITS, "S223_DAY_ENTRIES", "docterz_ingest.py"), encoding="utf-8").read()
i = sch.index("CREATE TABLE IF NOT EXISTS clinic_day_revenue"); j = sch.index('"""', i)
con0.executescript(sch[i:j])
con0.executescript("""CREATE TABLE upi_statement (id INTEGER PRIMARY KEY, merchant_id TEXT NOT NULL, unit TEXT, statement_date TEXT NOT NULL,
  source_msg_id TEXT, filename TEXT, sha256 TEXT, parsed_total_p INTEGER, txn_count INTEGER, ingested_at TEXT);
CREATE TABLE data_flag (id INTEGER PRIMARY KEY, code TEXT, detail TEXT);
CREATE TABLE clinic_day_tender (business_date TEXT, clinic_id TEXT, invoice_no TEXT, tender TEXT, amount_p INTEGER);""")
def day(d, online_p, total_p):
    con0.execute("INSERT INTO clinic_day_revenue VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 (d, "f", "s", "m", "t", 3, total_p - online_p, 0, 0, 0, 0, 3, total_p, 2, 1, 0, 0, 0,
                  json.dumps({"Cash": total_p - online_p, "Online Payment": online_p}), None, None, None, ""))
    con0.execute("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?)", (d, "CONSULT", 1, "P", "C1", total_p, "Cash", "morning"))
day("2026-09-01", 170000, 400000)   # bank applied, matches
day("2026-09-02", 800000, 1000000)  # bank applied 1000000 -> differs by +2000
day("2026-09-03", 210000, 400000)   # nothing from the bank yet
con0.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
             ("M1", "clinic", "2026-09-01", "f1", 170000, 4, "2026-09-02T12:05:00"))
con0.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
             ("M1", "clinic", "2026-09-02", "f2", 1000000, 9, "2026-09-03T13:40:00"))
con0.commit(); con0.close()
def _db():
    if "db" not in g:
        g.db = sqlite3.connect(DB); g.db.row_factory = sqlite3.Row
    return g.db
WHO = {"user": "manoj", "roles": {"checker"}}
def _require(*roles, unit="clinic"):
    if not WHO["user"]: return None, (jsonify(ok=False), 401)
    if not set(WHO["roles"]).intersection(roles): return None, (jsonify(ok=False), 403)
    return dict(user=WHO["user"], roles=sorted(WHO["roles"])), None
app = Flask(__name__)
BMS.init(app, _db, _require, unit="clinic", upi_dir=os.path.join(W, "nodir"))
FCD.init(app, _db, _require, unit="clinic")
@app.teardown_appcontext
def _c(_e):
    c = g.pop("db", None)
    if c is not None: c.close()
cl = app.test_client()
h = cl.get("/finance/clinic/day/2026-09-01").get_data(as_text=True)
ck("day page 01-Sep renders with a Bank MPR card", "Bank MPR" in h and 'data-state="applied"' in h)
ck("  it says APPLIED with the bank's own line", "APPLIED at" in h and "4 rows" in h)
ck("  it says Matches: ours 1,700 and bank 1,700", "Matches" in h and "1,700" in h)
ck("  it links to the day's MPR page", 'href="/finance/clinic/bank/mpr/2026-09-01"' in h)
h2 = cl.get("/finance/clinic/day/2026-09-02").get_data(as_text=True)
ck("day page 02-Sep: applied LATE, and 'Does not match ... bank is higher by ₹ 2,000'", 'data-state="late"' in h2 and "Does not match" in h2 and "bank is higher by" in h2 and "2,000" in h2)
h3 = cl.get("/finance/clinic/day/2026-09-03").get_data(as_text=True)
ck("day page 03-Sep: WAITING or NOT RECEIVED, no match line, link present", ('data-state="waiting"' in h3 or 'data-state="not_received"' in h3) and "Matches" not in h3 and 'href="/finance/clinic/bank/mpr/2026-09-03"' in h3)
m = cl.get("/finance/clinic/day?m=2026-09").get_data(as_text=True)
ck("month page has a Bank column", "<th class=\"n\">Bank</th>" in m)
ck("  01-Sep reads Applied, 02-Sep Applied late, 03-Sep Waiting/Not received, each linking to its MPR",
   "href='/finance/clinic/bank/mpr/2026-09-01'" in m and ">Applied<" in m and ">Applied late<" in m and ("href='/finance/clinic/bank/mpr/2026-09-03'" in m) and (">Waiting<" in m or ">Not received<" in m))
ck("month page still renders its totals row", "3 days" in m)
ck("the MPR page itself still answers", cl.get("/finance/clinic/bank/mpr/2026-09-01").status_code == 200)
WHO.update(user="", roles=set())
_x = cl.get("/finance/clinic/day/2026-09-01").get_data(as_text=True)
ck("signed out: the page's own 'Not permitted' answer, and no bank card on it (unchanged S223 behaviour)", "Not permitted" in _x and "Bank MPR" not in _x)
# module absent
WHO.update(user="manoj", roles={"checker"})
FCD._mpr = None
h4 = cl.get("/finance/clinic/day/2026-09-01").get_data(as_text=True)
ck("with bank_mpr_status absent the page still renders and says so", "bank-status module is not installed" in h4 and "Bank MPR" in h4)
m4 = cl.get("/finance/clinic/day?m=2026-09").get_data(as_text=True)
ck("month page with the module absent shows — in the Bank column and renders", "3 days" in m4 and "<td class='n'>—</td>" in m4)
FCD._mpr = BMS
io.open(os.path.join(HERE, "PREDICTED_PINS.txt"), "w", encoding="utf-8").write(
    "# S225_DAY_MPR_LINE -- predicted. A0: the close records what the box prints.\n/root/finance/finance_clinic_day.py  before %s  after %s\n# bank_mpr_status.py a0e740ce, finance_app.py 0aa211fb -- NOT touched.\n" % (LIVE, NEW))
shutil.rmtree(W, ignore_errors=True)
print("\n%d PASS  %d FAIL" % (len(P), len(F)))
for f in F: print("  FAILED: " + f)
sys.exit(1 if F else 0)
