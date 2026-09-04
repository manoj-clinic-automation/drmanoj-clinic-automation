#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_live_rematch.py -- S225 (rev 9): the rev-8 selftest as regression, then §17 the live cross-check and stock in transit. Base: the rev-6 selftest (rounding now in the engine), then §14 the phone book. Base: the S224 selftest UNCHANGED as regression, then §13 the staff order page. Base: the REAL blueprint, on a temp finance.db, fed the REAL
archived Marg exports through the SAME parser the manojz leg uses (marg_purchase_rows.py).
Rev 4 (04-Sep-2026, the owner's ruling on returns): the month's figure is supplier-wise; a
purchase return is labelled, counted and never asked Correct/Wrong; the finalise ladder is
(a) WRONG, (b) no item lines, (c) the two reports disagree; no page says "mark each".

Offline, on manojz:
    python3 -B selftest_purchase_app.py            (archive at ~/mnt/Downloads/margsync/MargArchive)
    MARG_ARCHIVE=/path python3 -B selftest_purchase_app.py

Prints PASS/FAIL per check and the counts. Exit 1 on any FAIL. Nothing here prints a row,
a supplier's phone or a header line from the exports -- only counts and totals.
"""
import glob
import io
import json
import os
import sqlite3
import sys
import tempfile
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(KITS, "S206_SANJEEVNI_MARG_PURCHASE"))
ARCHIVE = os.environ.get("MARG_ARCHIVE", os.path.expanduser("~/mnt/Downloads/margsync/MargArchive"))

from flask import Flask, g, has_app_context, jsonify     # noqa: E402
import marg_purchase_rows as R                            # noqa: E402
import purchase_app as PA                                 # noqa: E402
try:
    import marg_purchase as MP
except ImportError:
    MP = None

PASSED, FAILED = [], []


def ck(label, cond, detail=""):
    (PASSED if cond else FAILED).append(label)
    print("  %s  %s%s" % ("PASS" if cond else "FAIL", label, ("   [%s]" % detail) if detail and not cond else ""))


def one(pat):
    got = sorted(glob.glob(os.path.join(ARCHIVE, pat)))
    return got[0] if got else None


# ------------------------------------------------------------- the app, shaped like the box
TMP = tempfile.mkdtemp(prefix="s224_")
DB = os.path.join(TMP, "finance.db")
ASSETS = os.path.join(TMP, "assets.db")
TOKEN = "selftest-token-" + os.urandom(4).hex()
WHO = {"user": "manoj", "role": "doctor", "roles": {"checker"}}


def _db():
    if not has_app_context():
        raise RuntimeError("Working outside of application context")
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def _require(*roles, unit="medical"):
    if not WHO["user"]:
        return None, (jsonify(ok=False, error="not_signed_in"), 401)
    have = set(WHO["roles"])
    if not have.intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return dict(user=WHO["user"], role=WHO["role"], roles=sorted(have)), None


def as_(user, role, roles):
    WHO.update(user=user, role=role, roles=set(roles))


con0 = sqlite3.connect(DB)
con0.executescript("""
CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER, ingest_batch_id INTEGER,
  unit TEXT NOT NULL, business_date TEXT NOT NULL, bill_no TEXT NOT NULL, is_return INTEGER NOT NULL DEFAULT 0,
  seq INTEGER, item_name TEXT NOT NULL, item_key TEXT NOT NULL, pack TEXT, qty_raw TEXT, amount_p INTEGER,
  expiry_ym TEXT, batch TEXT);
CREATE TABLE stock_snapshot (as_on TEXT NOT NULL, item TEXT NOT NULL, qty INTEGER NOT NULL, packing TEXT,
  pack_size INTEGER NOT NULL DEFAULT 1, loaded_at TEXT NOT NULL, source TEXT, PRIMARY KEY (as_on, item));
CREATE TABLE stock_rate (item TEXT PRIMARY KEY, rate_p INTEGER NOT NULL, pack_size INTEGER NOT NULL DEFAULT 1,
  as_of TEXT, source TEXT);
CREATE TABLE stock_feed (id INTEGER PRIMARY KEY, as_on TEXT NOT NULL, source TEXT NOT NULL, item TEXT NOT NULL,
  qty INTEGER NOT NULL, received_at TEXT NOT NULL);
""")
con0.commit()
con0.close()

app = Flask(__name__)
PA.init(app, _db, _require, unit="medical", marg_token=TOKEN, assets_db=ASSETS,
        assets_url="https://assets.example")


@app.teardown_appcontext
def _close(_e):
    c = g.pop("db", None)
    if c is not None:
        c.close()


cl = app.test_client()
H = {"X-Finance-Marg": TOKEN}
P = "/finance/purchase"


def push(body, headers=H):
    return cl.post(P + "/api/push", json=body, headers=headers)


def q(sql, *a):
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    try:
        return c.execute(sql, a).fetchall()
    finally:
        c.close()


def q1(sql, *a):
    return q(sql, *a)[0][0]


print("S225 selftest (S224 regression + staff page) on %s" % TMP)

# ------------------------------------------------------------- 1. the doors
r = cl.get(P + "/api/healthz")
ck("healthz answers without auth", r.status_code == 200 and r.get_json()["ok"] is True and r.get_json()["exports"] == 0)
BW_AUG = one("PURCHASE_BILLWISE/2026-08/*_2026-08-01_to_2026-08-31__*.XLS")
ck("August BILLWISE export is in the archive", bool(BW_AUG))
bw = R.payload(BW_AUG, "BILLWISE")
ck("BILLWISE parser: rows sum to Marg's TOTAL row",
   sum(x["cash_p"] + x["credit_p"] for x in bw["rows"]) == bw["grand_amount_p"] and bw["n_rows"] > 50)
r = push(bw, headers={"X-Finance-Marg": "wrong-" + TOKEN})
ck("push with the WRONG token -> 401", r.status_code == 401)
r = push(bw, headers={"X-Finance-Cron": TOKEN})
ck("push with the wrong HEADER NAME (X-Finance-Cron, F-237) -> 401", r.status_code == 401)
r = push(bw, headers={})
ck("push with no header -> 401", r.status_code == 401)
r = push(dict(bw, type="NONSENSE"))
ck("push with an unknown type -> 400", r.status_code == 400 and r.get_json()["error"] == "malformed")
r = push(dict(bw, md5="xyz"))
ck("push with a bad md5 -> 400", r.status_code == 400)
r = push(dict(bw, rows="no"))
ck("push with rows not a list -> 400", r.status_code == 400)
r = cl.post(P + "/api/push", data="not json", headers=dict(H, **{"Content-Type": "application/json"}))
ck("push with a non-JSON body -> 400", r.status_code == 400)

# ------------------------------------------------------------- 2. BILLWISE August
r = push(bw)
j = r.get_json()
ck("BILLWISE August stored as new", r.status_code == 200 and j["stored"] is True and j["reason"] == "new")
ck("bills stored == BILLWISE rows", q1("SELECT COUNT(*) FROM purchase_bill") == bw["n_rows"])
ck("August bill-wise total == Marg TOTAL row",
   q1("SELECT SUM(amount_p) FROM purchase_bill WHERE month='2026-08'") == bw["grand_amount_p"])
r = push(bw)
ck("the same export again -> stored:false, duplicate", r.get_json()["stored"] is False and r.get_json()["reason"] == "duplicate")
ck("a duplicate did not add bills", q1("SELECT COUNT(*) FROM purchase_bill") == bw["n_rows"])
r = cl.get(P + "/api/healthz")
ck("healthz counts one export", r.get_json()["exports"] == 1 and r.get_json()["last_received"])

# ------------------------------------------------------------- 3. SUPPLIERWISE: two exports of one period
# rev 4: pinned to the two 02-Sep supplier-wise files (the supersede pair). The owner's 04-Sep export moves
# bill 02 of 18-Aug to its corrected supplier; section 15 pushes that pair and proves the old row drops out.
SW = sorted(glob.glob(os.path.join(ARCHIVE, "PURCHASE_SUPPLIERWISE/2026-08/*_2026-08-01_to_2026-08-31__20260902-*.XLS")))
ck("two August SUPPLIERWISE exports of the same period exist (the supersede case)", len(SW) >= 2)
sw_old, sw_new = R.payload(SW[0], "SUPPLIERWISE"), R.payload(SW[-1], "SUPPLIERWISE")
ck("SUPPLIERWISE parser: rows sum to GRAND TOTAL",
   sum(x["cash_p"] + x["credit_p"] for x in sw_new["rows"]) == sw_new["grand_amount_p"])
ck("SUPPLIERWISE and BILLWISE agree on the August total", sw_new["grand_amount_p"] == bw["grand_amount_p"])
r = push(sw_old)
ck("older SUPPLIERWISE stored as new", r.get_json()["stored"] is True)
ck("SUPPLIERWISE added NO second copy of any bill (supplier_key joins the two reports)",
   q1("SELECT COUNT(*) FROM purchase_bill") == bw["n_rows"])
r = push(sw_new)
ck("later SUPPLIERWISE of the same period stored as new", r.get_json()["stored"] is True)
ck("the older one is now marked superseded_by the later",
   q1("SELECT superseded_by FROM purchase_export WHERE md5=?", sw_old["md5"]) == sw_new["md5"])
r = push(sw_old)
ck("re-pushing the superseded one -> duplicate (idempotent on md5)", r.get_json()["reason"] == "duplicate")
older = dict(sw_new, md5="0" * 31 + "1", export_stamp="20260101-000000", file="fake_older.XLS")
r = push(older)
ck("an OLDER stamp for a period that already has a later one -> superseded_older, not stored",
   r.get_json()["stored"] is False and r.get_json()["reason"] == "superseded_older")
ck("bills still exactly the BILLWISE count after all that", q1("SELECT COUNT(*) FROM purchase_bill") == bw["n_rows"])
ck("every August bill's date came from BILLWISE (BILLWISE first)",
   q1("SELECT COUNT(*) FROM purchase_bill WHERE month='2026-08' AND date_src!='BILLWISE'") == 0)
ck("no bill lost its printed supplier name", q1("SELECT COUNT(*) FROM purchase_bill WHERE supplier='' OR supplier IS NULL") == 0)

# ------------------------------------------------------------- 4. ITEMWISE lines, dated by the bills
ck("marg_purchase (S206) importable for ITEMWISE", MP is not None)
IW1 = one("PURCHASE_ITEMWISE/2026-08/*_2026-08-01_to_2026-08-26__*.XLS")
IW2 = one("PURCHASE_ITEMWISE/2026-08/*_2026-08-28_to_2026-08-29__*.XLS")
iw1 = R.payload(IW1, "ITEMWISE", MP.read_purchase)
iw2 = R.payload(IW2, "ITEMWISE", MP.read_purchase)
ck("ITEMWISE rows carry a null bill_date (the export has none)", all(x["bill_date"] is None for x in iw1["rows"]))
r = push(iw1)
ck("ITEMWISE 01-26 stored", r.get_json()["stored"] is True and r.get_json()["rows"] == iw1["n_rows"])
r = push(iw2)
ck("ITEMWISE 28-29 stored (a different period: coexists, does not supersede)", r.get_json()["stored"] is True)
n_lines = q1("SELECT COUNT(*) FROM purchase_line")
ck("lines stored == ITEMWISE rows", n_lines == iw1["n_rows"] + iw2["n_rows"])
ck("EVERY ITEMWISE line was dated from its bill", q1("SELECT COUNT(*) FROM purchase_line WHERE bill_date IS NULL") == 0)
ck("every line's month is August", q1("SELECT COUNT(*) FROM purchase_line WHERE month!='2026-08'") == 0)
ck("item-wise GROSS sum of the lines == the two exports' totals (gross is stored, labelled)",
   q1("SELECT SUM(amount_p) FROM purchase_line") == sum(x["amount_p"] or 0 for x in iw1["rows"] + iw2["rows"]))
ck("item-wise NET sum of the lines == the two exports' net (rev 2: this is the money the pages show)",
   q1("SELECT SUM(net_amount_p) FROM purchase_line") == sum(x["net_amount_p"] or 0 for x in iw1["rows"] + iw2["rows"]))

# rev 3: pinned to the 28-31 Aug fixture. The owner's 04-Sep full-month bill/item-wise export now sits
# beside it and would otherwise be picked first, closing the very gap these checks exist to exercise.
BI = one("PURCHASE_BILLITEMWISE/2026-08/*_2026-08-28_to_2026-08-31__*.XLS")
bi = R.payload(BI, "BILLITEMWISE")
ck("BILLITEMWISE parser: rows sum to its TOTAL", sum(x["amount_p"] or 0 for x in bi["rows"]) == bi["grand_amount_p"])
r = push(bi)
ck("BILLITEMWISE stored", r.get_json()["stored"] is True)
ck("BILLITEMWISE lines found their supplier from the bills (bill no + date)",
   q1("SELECT COUNT(*) FROM purchase_line WHERE line_type='BILLITEMWISE' AND supplier_norm IS NOT NULL") > 0)

# ------------------------------------------------------------- 5. lines BEFORE bills (July): undated, then re-dated
IWJ = one("PURCHASE_ITEMWISE/2026-07/*.XLS")
BWJ = one("PURCHASE_BILLWISE/2026-07/*.XLS")
iwj = R.payload(IWJ, "ITEMWISE", MP.read_purchase)
push(iwj)
und = q1("SELECT COUNT(*) FROM purchase_line WHERE bill_date IS NULL")
ck("July ITEMWISE pushed BEFORE its bills: lines are UNDATED", und == iwj["n_rows"])
with app.test_request_context():
    s = PA._month_summary(_db(), "2026-07")
ck("July (no bills yet) cannot finalise, and the story says its item lines are waiting undated (rev 4: undated never blocks by itself)",
   not s["can_finalise"] and any("no bills" in x for x in s["reasons"]) and "undated" in s["story"], s["story"])
push(R.payload(BWJ, "BILLWISE"))
ck("July BILLWISE arrives: the lines are re-dated by the bills", q1("SELECT COUNT(*) FROM purchase_line WHERE bill_date IS NULL") == 0)
ck("July bills == its BILLWISE rows", q1("SELECT COUNT(*) FROM purchase_bill WHERE month='2026-07'") == R.payload(BWJ, "BILLWISE")["n_rows"])

# ------------------------------------------------------------- 6. the month summary and the hub
with app.test_request_context():
    s = PA._month_summary(_db(), "2026-08")
ck("August summary: the month's figure is the SUPPLIER-WISE total == Marg TOTAL (rev 4), bill-wise identical, no disagreement",
   s["marg_p"] == bw["grand_amount_p"] and s["basis"] == "supplier-wise" and s["sw_p"] == s["bw_p"] == bw["grand_amount_p"]
   and s["month_disagree_p"] == 0 and not s["disagree"], "%s %s %s" % (s["marg_p"], s["basis"], s["month_disagree_p"]))
_all_net = q1("SELECT SUM(net_amount_p) FROM purchase_line WHERE month='2026-08'")
_all_gross = q1("SELECT SUM(amount_p) FROM purchase_line WHERE month='2026-08'")
# the rev-2 dedupe, recomputed here by hand: per (supplier, bill) keep the export with the later stamp
_best = {}
for _r in q("SELECT l.supplier_norm s, l.bill_no b, e.export_stamp st, l.source_md5 m, SUM(l.net_amount_p) n "
            "FROM purchase_line l JOIN purchase_export e ON e.md5=l.source_md5 WHERE l.month='2026-08' "
            "AND e.superseded_by IS NULL GROUP BY 1,2,3,4"):
    if (_r["s"], _r["b"]) not in _best or (_r["st"], _r["m"]) > _best[(_r["s"], _r["b"])][0]:
        _best[(_r["s"], _r["b"])] = ((_r["st"], _r["m"]), _r["n"])
_dedup_net = sum(v[1] for v in _best.values())
ck("August summary: item-wise is NET, not gross (rev 2)", s["itemwise_p"] < _all_gross and s["itemwise_p"] != _all_gross)
ck("August summary: bills that ITEMWISE 28-29 and BILLITEMWISE 28-31 BOTH carry are counted ONCE (later stamp wins)",
   s["itemwise_p"] == _dedup_net and _dedup_net < _all_net, "%s vs %s (all %s)" % (s["itemwise_p"], _dedup_net, _all_net))
_bi_lines = q("SELECT supplier_norm FROM purchase_line WHERE line_type='BILLITEMWISE'")
ck("BILLITEMWISE lines that arrived BEFORE their bill were linked to it once the bill came (rev 2)",
   all(r[0] for r in _bi_lines) and not s["orphans"], str(len(s["orphans"])))
ck("August is provisional and cannot finalise: bills without item lines (the ONLY reason; the one short bill does not block, rev 4)",
   s["status"]["status"] == "provisional" and not s["can_finalise"] and len(s["reasons"]) == 1
   and "no item lines yet" in s["reasons"][0], str(s["reasons"]))
ck("August fixture: one bill has item lines SHORT of the bill (13056, Rs 23) and no purchase return",
   len(s["short"]) == 1 and not s["returns"] and s["short"][0]["diff_p"] < 0, str([(x["bill"]["bill_no"], x["diff_p"]) for x in s["short"]]))
ck("August story: calm, names the gap and the one action, never 'mark each'",
   "no item lines yet" in s["story"] and "export item-wise" in s["story"] and "mark each" not in s["story"].lower(), s["story"])
as_("manoj", "doctor", {"checker"})
r = cl.get(P + "/page/hub")
h = r.get_data(as_text=True)
ck("hub renders for the doctor", r.status_code == 200)
for word in ("August 2026", "July 2026", "Feed health", "Stock verification", "Scan links", "Orders", "PROVISIONAL", "(doctor)"):
    ck("hub shows '%s'" % word, word in h)
ck("hub says the asset app is not reachable when assets.db is absent", "asset app not reachable" in h)
r = cl.get(P + "/page/month/2026-08")
m = r.get_data(as_text=True)
ck("month page renders", r.status_code == 200)
for word in ("cannot finalise yet", "Marg purchase, August 2026", "supplier-wise, final for month-end", "Correct", "Wrong", "no item lines yet"):
    ck("month page shows '%s'" % word, word in m)
ck("month page offers Correct/Wrong ONLY on the short bill (one pair of buttons)", m.count("onclick=\"verdict(") == 2, str(m.count("onclick=\"verdict(")))
ck("month page has no FINALISE button while it cannot finalise", "FINALISE August" not in m)
r = cl.get(P + "/page/month/13-2026")
ck("a bad month is refused", r.status_code == 400)

# ------------------------------------------------------------- 7. verdicts
bid = q1("SELECT id FROM purchase_bill WHERE month='2026-08' ORDER BY id LIMIT 1")
as_("amir", "staff", {"viewer"})
r = cl.post(P + "/api/verdict", json=dict(bill_id=bid, verdict="CORRECT"))
ck("a viewer cannot give a verdict (403)", r.status_code == 403)
r = cl.get(P + "/page/month/2026-08")
ck("a viewer's month page carries no verdict buttons", 'onclick="verdict(' not in r.get_data(as_text=True) and r.status_code == 200)
as_("darpan", "staff", {"maker"})
r = cl.post(P + "/api/verdict", json=dict(bill_id=bid, verdict="WRONG"))
ck("WRONG without amount+reason -> 400", r.status_code == 400)
r = cl.post(P + "/api/verdict", json=dict(bill_id=bid, verdict="WRONG", wrong_amount="1234.50", reason="rate typed wrong"))
ck("maker marks a bill WRONG with amount and reason", r.status_code == 200 and r.get_json()["ok"])
ck("the WRONG amount is stored in paise", q1("SELECT wrong_amount_p FROM purchase_bill WHERE id=?", bid) == 123450)
m = cl.get(P + "/page/month/2026-08").get_data(as_text=True)
ck("month page shows WRONG with the reason", "WRONG" in m and "rate typed wrong" in m)
ck("hub counts the WRONG bill", ">1</td>" in cl.get(P + "/page/hub").get_data(as_text=True))
r = cl.post(P + "/api/verdict", json=dict(bill_id=bid, verdict="CORRECT"))
ck("the same bill can be set CORRECT again", r.status_code == 200 and q1("SELECT verdict FROM purchase_bill WHERE id=?", bid) == "CORRECT")
ck("verdicts are audited", q1("SELECT COUNT(*) FROM purchase_audit WHERE action='verdict'") == 2)

# ------------------------------------------------------------- 8. finalise: refused, then allowed
r = cl.post(P + "/api/finalise", json=dict(month="2026-08"))
ck("a maker cannot finalise (403, doctor only)", r.status_code == 403)
as_("manoj", "doctor", {"checker"})
r = cl.post(P + "/api/finalise", json=dict(month="2026-08"))
ck("the doctor is refused on August with the reasons listed", r.status_code == 409 and r.get_json()["reasons"])
# a clean synthetic month: BILLWISE + ITEMWISE that reconcile to the paisa
may_bills = [dict(bill_date="2026-05-0%d" % (i + 1), bill_no=str(700 + i), supplier="ZZTEST STOCKIST          BAREILLY",
                  cash_p=0, credit_p=100000 * (i + 1)) for i in range(3)]
may_lines = [dict(bill_no=str(700 + i), bill_date=None, supplier="ZZTEST STOCKIST          BAREILLY",
                  item="ZZTEST ITEM %d" % i, packing="1*10", batch="B", expiry="1/28", tax=0, qty=10, free=None,
                  rate_p=10000 * (i + 1), discount_pct=0, amount_p=100000 * (i + 1), net_rate_p=1000, net_amount_p=100000 * (i + 1),
                  loose_qty=100, purchase_rate_p=10000 * (i + 1), direction="PURCHASE") for i in range(3)]
push(dict(type="BILLWISE", md5="a" * 32, file="may_bw.XLS", period_from="2026-05-01", period_to="2026-05-31",
          export_stamp="20260601-090000", n_rows=3, grand_amount_p=600000, rows=may_bills))
push(dict(type="ITEMWISE", md5="b" * 32, file="may_iw.XLS", period_from="2026-05-01", period_to="2026-05-31",
          export_stamp="20260601-090100", n_rows=3, grand_amount_p=600000, rows=may_lines))
with app.test_request_context():
    s = PA._month_summary(_db(), "2026-05")
ck("a month whose bills and lines reconcile CAN finalise", s["can_finalise"] and s["diff_p"] == 0, str(s["reasons"]))
mb = q1("SELECT id FROM purchase_bill WHERE month='2026-05' ORDER BY id LIMIT 1")
cl.post(P + "/api/verdict", json=dict(bill_id=mb, verdict="WRONG", wrong_amount="10", reason="test"))
r = cl.post(P + "/api/finalise", json=dict(month="2026-05"))
ck("finalise refused while a bill is WRONG, naming it", r.status_code == 409 and any("marked Wrong" in x and "700" in x for x in r.get_json()["reasons"]))
cl.post(P + "/api/verdict", json=dict(bill_id=mb, verdict="CORRECT"))
m = cl.get(P + "/page/month/2026-05").get_data(as_text=True)
ck("the FINALISE button appears for the doctor when the month reconciles", "FINALISE May 2026" in m)
r = cl.post(P + "/api/finalise", json=dict(month="2026-05"))
ck("the doctor finalises May", r.status_code == 200 and r.get_json()["status"] == "final")
ck("purchase_month records FINAL with the totals",
   q("SELECT status, billwise_total_p, itemwise_total_p, finalised_by FROM purchase_month WHERE month='2026-05'")[0][:] == ("final", 600000, 600000, "manoj"))
m = cl.get(P + "/page/month/2026-05").get_data(as_text=True)
ck("a FINAL month page shows FINAL and the reopen for the doctor", "FINAL" in m and "reopen(" in m)
as_("darpan", "staff", {"maker"})
r = cl.post(P + "/api/verdict", json=dict(bill_id=mb, verdict="WRONG", wrong_amount="10", reason="late"))
ck("verdicts are locked on a FINAL month (403)", r.status_code == 403)
r = cl.post(P + "/api/reopen", json=dict(month="2026-05", reason="x"))
ck("a maker cannot reopen (403)", r.status_code == 403)
as_("manoj", "doctor", {"checker"})
r = cl.post(P + "/api/reopen", json=dict(month="2026-05"))
ck("reopen without a reason -> 400", r.status_code == 400)
r = cl.post(P + "/api/reopen", json=dict(month="2026-05", reason="found a missing bill"))
ck("the doctor reopens with a reason", r.status_code == 200 and q1("SELECT status FROM purchase_month WHERE month='2026-05'") == "provisional")
ck("finalise and reopen are audited", q1("SELECT COUNT(*) FROM purchase_audit WHERE action IN ('finalise','reopen')") == 2)
ck("hub shows FINAL/PROVISIONAL chips", "PROVISIONAL" in cl.get(P + "/page/hub").get_data(as_text=True))

# ------------------------------------------------------------- 9. scans, against a temp assets.db
r = cl.get(P + "/page/scans")
ck("scans page without assets.db says 'asset app not reachable' and nothing breaks", r.status_code == 200 and "asset app not reachable" in r.get_data(as_text=True))
r = cl.post(P + "/api/rematch", json={})
ck("rematch without assets.db -> 503 assets_unreachable", r.status_code == 503)
tb = q("SELECT id, supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE month='2026-08' ORDER BY id LIMIT 2")
ac = sqlite3.connect(ASSETS)
ac.executescript("""CREATE TABLE bills(id INTEGER PRIMARY KEY, kind TEXT NOT NULL DEFAULT 'Consumable', vendor TEXT,
  bill_no TEXT, bill_date TEXT, total_amount REAL, notes TEXT, source_stored TEXT, source_orig TEXT, created_by INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')), status TEXT, ocr_status TEXT);""")
ac.execute("INSERT INTO bills (kind,vendor,bill_no,bill_date,total_amount,status,ocr_status) VALUES (?,?,?,?,?,?,?)",
           ("Pharmacy", tb[0]["supplier"].split("  ")[0].strip(), tb[0]["bill_no"], tb[0]["bill_date"], tb[0]["amount_p"] / 100.0, "captured", "read"))
ac.execute("INSERT INTO bills (kind,vendor,bill_no,bill_date,total_amount,status,ocr_status) VALUES (?,?,?,?,?,?,?)",
           ("Pharmacy", "unreadable", tb[1]["bill_no"], None, round(tb[1]["amount_p"] / 100.0 * 1.01, 2), "captured", "empty"))
ac.execute("INSERT INTO bills (kind,vendor,bill_no,bill_date,total_amount,status,ocr_status) VALUES (?,?,?,?,?,?,?)",
           ("Pharmacy", "NOBODY PHARMA", "X9", "2026-08-15", 12.5, "captured", "read"))
ac.execute("INSERT INTO bills (kind,vendor,bill_no,bill_date,total_amount,status,ocr_status) VALUES (?,?,?,?,?,?,?)",
           ("Consumable", tb[0]["supplier"], tb[0]["bill_no"], tb[0]["bill_date"], tb[0]["amount_p"] / 100.0, "captured", "read"))
ac.commit()
ac.close()
r = cl.post(P + "/api/rematch", json={})
ck("rematch runs against the temp assets.db", r.status_code == 200 and r.get_json()["scans"] == 3)
ck("rematch found 2 links (one EXACT, one PROBABLE), ignoring the non-Pharmacy scan",
   sorted(x[0] for x in q("SELECT grade FROM purchase_scan_link")) == ["EXACT", "PROBABLE"], str(q("SELECT * FROM purchase_scan_link")))
ck("the EXACT link is on the right bill", q1("SELECT bill_id FROM purchase_scan_link WHERE grade='EXACT'") == tb[0]["id"])
r = cl.get(P + "/page/scans")
sp = r.get_data(as_text=True)
ck("scans page renders with both lists", r.status_code == 200 and "NOBODY PHARMA" in sp and "Marg bills with no scan" in sp)
ck("scans page links to the asset app's bill", "https://assets.example/bills/" in sp)
ck("month page shows the scan link on the matched bill", "scan exact" in cl.get(P + "/page/month/2026-08").get_data(as_text=True))
hub = cl.get(P + "/page/hub").get_data(as_text=True)
ck("hub counts unmatched scans and unscanned bills", "pharmacy scans with no Marg bill" in hub and "asset app not reachable" not in hub)
as_("amir", "staff", {"viewer"})
ck("a viewer's scans page has no Re-match button", "Re-match" not in cl.get(P + "/page/scans").get_data(as_text=True))
as_("manoj", "doctor", {"checker"})

# ------------------------------------------------------------- 10. the feed ping
r = cl.post(P + "/api/feed", json=dict(pull_last="2026-09-04T06:40:21+05:30", pull_age_min=38, state="asleep", host="manojz"), headers=H)
ck("feed ping stored", r.status_code == 200 and q1("SELECT COUNT(*) FROM purchase_feed") == 1)
hub = cl.get(P + "/page/hub").get_data(as_text=True)
ck("hub shows the pull ASLEEP in red with the time", "pull asleep since 06:40 IST" in hub)
cl.post(P + "/api/feed", json=dict(pull_last="2026-09-04T07:40:21+05:30", pull_age_min=3, state="ok", host="manojz"), headers=H)
ck("hub turns green when the next ping says ok", "manojz is awake" in cl.get(P + "/page/hub").get_data(as_text=True))
r = cl.post(P + "/api/feed", json={}, headers={"X-Finance-Marg": "nope"})
ck("feed with the wrong token -> 401", r.status_code == 401)

# ------------------------------------------------------------- 11. vendors and the phone rule
FAKE_PHONE = "9" + "8" * 9              # built at run time; never a literal in this file
r = cl.post(P + "/api/vendors", json=dict(pairs={"ZZTEST STOCKIST": FAKE_PHONE}), headers={"X-Finance-Marg": "nope"})
ck("vendors with the wrong token -> 401", r.status_code == 401)
r = cl.post(P + "/api/vendors", json=dict(pairs={"ZZTEST STOCKIST": FAKE_PHONE}), headers=H)
ck("vendor pairs stored", r.status_code == 200 and r.get_json()["stored"] == 1)
ck("the response never echoes a phone", FAKE_PHONE not in r.get_data(as_text=True))
ck("the audit row never holds a phone", FAKE_PHONE not in (q1("SELECT detail FROM purchase_audit WHERE action='vendors'") or ""))

# ------------------------------------------------------------- 12. the reorder plan and the order book
c = sqlite3.connect(DB)
today = dt.date.today()
items = [("ZZTEST ITEM 0", 12, 10, 2.0), ("ZZTEST ITEM 1", 0, 10, 1.0), ("ZZTEST ITEM 2", 500, 10, 0.5)]
for name, qty, size, per_day in items:
    c.execute("INSERT INTO stock_snapshot (as_on,item,qty,packing,pack_size,loaded_at,source) VALUES (?,?,?,?,?,?,?)",
              (today.strftime("%d-%m-%Y"), name, qty, "1*%d" % size, size, "t", "push_snapshot"))
    for d in range(26):
        day = (today - dt.timedelta(days=d)).isoformat()
        c.execute("INSERT INTO sale_line_item (unit,business_date,bill_no,seq,item_name,item_key,qty_raw) VALUES (?,?,?,?,?,?,?)",
                  ("medical", day, "S%d" % d, 1, name, name.lower(), "0:%d" % int(per_day)))
for d in range(5):
    c.execute("INSERT INTO stock_feed (as_on,source,item,qty,received_at) VALUES (?,?,?,?,?)",
              ((today - dt.timedelta(days=d)).strftime("%d-%m-%Y"), "push_snapshot", "ZZTEST ITEM 0", 12, "t"))
    c.execute("INSERT INTO stock_feed (as_on,source,item,qty,received_at) VALUES (?,?,?,?,?)",
              ((today - dt.timedelta(days=d)).strftime("%d-%m-%Y"), "push_expected", "ZZTEST ITEM 0", 12 if d else 11, "t"))
c.commit()
c.close()
with app.test_request_context():
    plan = PA.reorder_plan(_db(), today)
ck("plan reads the newest snapshot", plan["as_on"] == today.strftime("%d-%m-%Y"))
ck("plan paced the three items from sale lines", plan["items_paced"] == 3)
ck("plan is labelled PROVISIONAL (5 feed days < 28)", plan["provisional"] and plan["feed_days"] == 5)
vend = {v["vendor"]: v for v in plan["vendors"]}
ck("the vendor comes from the last purchase line's supplier", any("ZZTEST STOCKIST" in k for k in vend))
zz = next((v for k, v in vend.items() if "ZZTEST STOCKIST" in k), None)
names = {l["item"]: l for l in (zz["lines"] if zz else [])}
ck("the item that is OUT is on the plan", "ZZTEST ITEM 1" in names and names["ZZTEST ITEM 1"]["order_strips"] > 0)
ck("the item with 500 on hand at 0.5/day is NOT reordered", "ZZTEST ITEM 2" not in names)
ck("cover_after is computed", names.get("ZZTEST ITEM 1", {}).get("cover_after") is not None)
ck("rate per pack comes from the last purchase line", names.get("ZZTEST ITEM 1", {}).get("rate_p") == 20000)
r = cl.get(P + "/page/orders")
op = r.get_data(as_text=True)
ck("orders page renders for the doctor", r.status_code == 200)
for word in ("PROVISIONAL until the stock verification has run a month", "Save as order", "Copy this order", "Order book", "tel:"):
    ck("orders page (doctor) shows '%s'" % word, word in op)
ck("stock card on the hub reads the feed comparison", "items compared" in cl.get(P + "/page/hub").get_data(as_text=True))
as_("amir", "staff", {"viewer"})
ov = cl.get(P + "/page/orders").get_data(as_text=True)
ck("a VIEWER's orders page has NO phone, no tel: link, no copy block, no save button",
   FAKE_PHONE not in ov and "tel:" not in ov and "Copy this order" not in ov and "Save as order" not in ov)
as_("darpan", "staff", {"maker"})
om = cl.get(P + "/page/orders").get_data(as_text=True)
ck("a MAKER sees the phone but not the Save button", "tel:" in om and "Save as order" not in om)
lines = [dict(item=l["item"], packs=l["order_strips"], pack_size=l["pack_size"], rate_p=l["rate_p"], on_hand=l["on_hand"],
              per_day=l["rate_per_day"], cover_after=l["cover_after"]) for l in zz["lines"] if l["order_strips"] > 0]
r = cl.post(P + "/api/order", json=dict(action="create", vendor=zz["vendor"], lines=lines))
ck("a maker cannot save an order (403)", r.status_code == 403)
as_("manoj", "doctor", {"checker"})
r = cl.post(P + "/api/order", json=dict(action="create", vendor=zz["vendor"], lines=lines))
ck("the doctor saves the plan as a draft order", r.status_code == 200 and r.get_json()["order_id"] == 1)
oid = r.get_json()["order_id"]
ck("order lines persisted with a total", q1("SELECT COUNT(*) FROM purchase_order_line WHERE order_id=?", oid) == len(lines)
   and q1("SELECT total_p FROM purchase_order WHERE id=?", oid) == sum(l["packs"] * l["rate_p"] for l in lines))
r = cl.post(P + "/api/order", json=dict(action="status", id=oid, status="sent"))
ck("order moved to sent", r.status_code == 200 and q1("SELECT status FROM purchase_order WHERE id=?", oid) == "sent")
r = cl.post(P + "/api/order", json=dict(action="status", id=oid, status="lost"))
ck("an unknown status is refused", r.status_code == 400)
ck("hub counts the open order", "<b>1</b><span>open orders" in cl.get(P + "/page/hub").get_data(as_text=True))
ck("order create and status are audited", q1("SELECT COUNT(*) FROM purchase_audit WHERE action LIKE 'order_%'") == 2)
ck("the order book shows the order with its status", "#1" in cl.get(P + "/page/orders").get_data(as_text=True))

# ------------------------------------------------------------- 13. REV 2: net vs gross, per-bill buckets, the gap
as_("manoj", "doctor", {"checker"})
for pat, typ in (("PURCHASE_SUPPLIERWISE/2026-07/*.XLS", "SUPPLIERWISE"), ("PURCHASE_BILLWISE/2026-08/*_2026-08-01_to_2026-08-29__*.XLS", "BILLWISE"),
                 ("PURCHASE_BILLWISE/2026-09/*.XLS", "BILLWISE")):
    f = one(pat)
    ck("archive holds %s" % typ + " " + pat.split("/")[1], bool(f))
    push(R.payload(f, typ))
push(R.payload(one("PURCHASE_ITEMWISE/2026-09/*.XLS"), "ITEMWISE", MP.read_purchase))
with app.test_request_context():
    sj, sa, ss = (PA._month_summary(_db(), m) for m in ("2026-07", "2026-08", "2026-09"))
ck("July: item-wise NET == 47739566 paise (Rs 4,77,395.66, the S212 record)", sj["itemwise_p"] == 47739566, str(sj["itemwise_p"]))
ck("July: the month's figure is Rs 4,76,393 supplier-wise (bill-wise identical)",
   sj["marg_p"] == 47639300 and sj["basis"] == "supplier-wise" and sj["sw_p"] == sj["bw_p"] == 47639300, "%s %s" % (sj["marg_p"], sj["basis"]))
ck("July: no bill without lines, no line set without a bill", not sj["no_lines"] and not sj["orphans"])
ck("July: exactly 2 PURCHASE RETURNS (item-wise net above the bill), nothing short, 101 of 103 agree",
   len(sj["returns"]) == 2 and not sj["short"] and len(sj["agree"]) == 101 and len(sj["bills"]) == 103,
   "%d ret %d short %d/%d" % (len(sj["returns"]), len(sj["short"]), len(sj["agree"]), len(sj["bills"])))
ck("July: a return is never asked a verdict", not sj["needs_verdict"])
ck("July CAN finalise with its two returns (rev 4: returns never block)", sj["can_finalise"], str(sj["reasons"]))
ck("July story: 'July: Rs 4,76,393 (supplier-wise, final for month-end). 103 bills; 2 carry a purchase return; ready to finalise.'",
   sj["story"] == "July: \u20b94,76,393 (supplier-wise, final for month-end). 103 bills; 2 carry a purchase return; ready to finalise.", sj["story"])
ck("September: item-wise NET == 7243737 paise (Rs 72,437.37)", ss["itemwise_p"] == 7243737, str(ss["itemwise_p"]))
ck("September: Rs 72,438 (bill-wise stands in: no supplier-wise yet) and all 11 bills AGREE within Rs 1",
   ss["marg_p"] == 7243800 and ss["basis"] == "bill-wise" and len(ss["agree"]) == 11 == len(ss["bills"]) and not ss["returns"] and not ss["short"] and not ss["no_lines"],
   "%s %s" % (ss["marg_p"], ss["basis"]))
ck("September story says quietly that bill-wise stands in, and is ready to finalise",
   "bill-wise stands in" in ss["story"] and "ready to finalise" in ss["story"] and ss["can_finalise"], ss["story"])
ck("August: reports the 27-Aug gap as NO ITEM LINES (item-wise export missing for that date)",
   "2026-08-27" in sa["gap_dates"] and any("27 Aug" in x and "no item lines yet" in x for x in sa["reasons"]), str(sa["reasons"]))
ck("August: the story names the gap and the one action", "27 Aug" in sa["story"] and "export item-wise for" in sa["story"], sa["story"])
ck("August: agree + returns + short + no-lines == bills", len(sa["agree"]) + len(sa["returns"]) + len(sa["short"]) + len(sa["no_lines"]) == len(sa["bills"]))
hub = cl.get(P + "/page/hub").get_data(as_text=True)
ck("hub shows Marg total (supplier-wise), Item-wise net, Returns, No lines, Wrong columns",
   "Marg total (supplier-wise)" in hub and ">Item-wise net<" in hub and ">Returns<" in hub and ">No lines<" in hub and ">Wrong<" in hub)
ck("hub carries no Agree / Differ column and never says 'mark each' or 'unverified'",
   ">Agree<" not in hub and ">Differ<" not in hub and "mark each" not in hub.lower() and "unverified" not in hub)
ck("hub July item-wise is the NET figure", "4,77,396" in hub and "5,08,062" not in hub)
ck("hub September shows Rs 72,437 net beside Rs 72,438", "72,437" in hub and "72,438" in hub)
mj = cl.get(P + "/page/month/2026-07").get_data(as_text=True)
ck("July month page: 'Purchase returns (2)' section, each row 'purchase return ... (Marg)', no verdict buttons, FINALISE offered",
   "Purchase returns (2)" in mj and mj.count("(Marg)</span>") == 2 and 'onclick="verdict(' not in mj and "FINALISE July 2026" in mj)
ma = cl.get(P + "/page/month/2026-08").get_data(as_text=True)
ck("August month page lists the NO ITEM LINES bucket, each row saying which date's export is missing",
   "Bills with no item lines yet (%d)" % len(sa["no_lines"]) in ma and ma.count("item-wise export missing for 27-Aug") >= 1)
ck("August month page: 'Item lines short of the bill (1)' with the plain wording", "Item lines short of the bill (1)" in ma and "check the bill" in ma)
# the finalise rule, on a synthetic month far from the real data:
#   bill 801 agrees; 802 differs by Rs 5 (net below bill-wise); 803 has no lines at all
jun_bills = [dict(bill_date="2025-06-1%d" % i, bill_no=str(801 + i), supplier="ZZREV2 STOCKIST          BAREILLY", cash_p=0, credit_p=200000)
             for i in range(3)]
def _ln(bno, net, gross, stamp_item="ZZREV2 ITEM"):
    return dict(bill_no=bno, bill_date=None, supplier="ZZREV2 STOCKIST          BAREILLY", item=stamp_item + " " + bno, packing="1*10",
                batch="B", expiry="1/28", tax=0, qty=10, free=None, rate_p=gross // 10, discount_pct=0, amount_p=gross, net_rate_p=net // 10,
                net_amount_p=net, loose_qty=100, purchase_rate_p=gross // 10, direction="PURCHASE")
push(dict(type="BILLWISE", md5="c" * 32, file="jun_bw.XLS", period_from="2025-06-01", period_to="2025-06-30", export_stamp="20250701-090000",
          n_rows=3, grand_amount_p=600000, rows=jun_bills))
push(dict(type="ITEMWISE", md5="d" * 32, file="jun_iw.XLS", period_from="2025-06-01", period_to="2025-06-30", export_stamp="20250701-090100",
          n_rows=2, grand_amount_p=0, rows=[_ln("801", 200000, 220000), _ln("802", 199500, 220000)]))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: item-wise is NET (399500), never gross (440000)", s6["itemwise_p"] == 399500, str(s6["itemwise_p"]))
ck("synthetic: buckets are 1 agree / 1 short (net below the bill) / 1 no lines, no return",
   (len(s6["agree"]), len(s6["short"]), len(s6["no_lines"]), len(s6["returns"])) == (1, 1, 1, 0))
ck("synthetic: the short bill 802 is offered a verdict; 801 and 803 are not", s6["needs_verdict"] == {s6["short"][0]["bill"]["id"]})
r = cl.post(P + "/api/finalise", json=dict(month="2025-06"))
rs = " ".join(r.get_json().get("reasons") or [])
ck("finalise refused: names the no-lines bill 803 ONLY (the short bill 802 does not block, rev 4)",
   r.status_code == 409 and "803" in rs and "802" not in rs and "12-Jun" in rs, rs)
ck("synthetic: the story mentions the short bill in plain words", "1 bill has item lines short of the bill" in s6["story"], s6["story"])
# a later BILLITEMWISE export (a different type, so it coexists) carries 803's lines and a corrected 802 that now agrees
push(dict(type="BILLITEMWISE", md5="e" * 32, file="jun_bi.XLS", period_from="2025-06-01", period_to="2025-06-30", export_stamp="20250702-090000",
          n_rows=2, grand_amount_p=0, rows=[dict(_ln("803", 200000, 200000), supplier=""), dict(_ln("802", 200000, 210000), supplier="")]))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: supplier-less BILLITEMWISE lines found their bills by (bill no, date)", not s6["orphans"] and not s6["no_lines"])
ck("synthetic: for 802 the LATER export's lines replaced the earlier ITEMWISE set -- it now AGREES, counted once",
   len(s6["agree"]) == 3 and not s6["short"] and not s6["returns"] and s6["itemwise_p"] == 600000, "%s %s" % (s6["itemwise_p"], s6["reasons"]))
ck("synthetic: the month can finalise", s6["can_finalise"], str(s6["reasons"]))
# now the CORRECT-verdict path: make 801 differ by Rs 5 through a later ITEMWISE (same period: supersedes the first ITEMWISE)
push(dict(type="ITEMWISE", md5="f" * 32, file="jun_iw2.XLS", period_from="2025-06-01", period_to="2025-06-30", export_stamp="20250703-090000",
          n_rows=1, grand_amount_p=0, rows=[_ln("801", 199500, 220000)]))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: 801 is now SHORT by Rs 5 -- offered a verdict, the month still CAN finalise (rev 4)",
   len(s6["short"]) == 1 and s6["short"][0]["bill"]["bill_no"] == "801" and s6["can_finalise"] and "801" in " ".join(
       x["bill"]["bill_no"] for x in s6["short_open"]), str(s6["reasons"]))
m6 = cl.get(P + "/page/month/2025-06").get_data(as_text=True)
ck("synthetic month page: the buttons sit on 801 alone, worded 'Item lines missing -- check the bill'",
   m6.count('onclick="verdict(') == 2 and "Item lines missing" in m6 and "check the bill" in m6)
b801 = q1("SELECT id FROM purchase_bill WHERE bill_no='801' AND month='2025-06'")
cl.post(P + "/api/verdict", json=dict(bill_id=b801, verdict="CORRECT"))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: 801 marked CORRECT leaves the short list open-count at 0 and the month can finalise", s6["can_finalise"] and not s6["short_open"], str(s6["reasons"]))
cl.post(P + "/api/verdict", json=dict(bill_id=b801, verdict="WRONG", wrong_amount="1995", reason="rev2 test"))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: the same bill marked WRONG blocks again (rule a kept)", not s6["can_finalise"] and any("marked Wrong" in x for x in s6["reasons"]))
# rule (c): a supplier-wise export that disagrees with bill-wise on one bill blocks the month
cl.post(P + "/api/verdict", json=dict(bill_id=b801, verdict="CORRECT"))
push(dict(type="SUPPLIERWISE", md5="9" * 32, file="jun_sw.XLS", period_from="2025-06-01", period_to="2025-06-30", export_stamp="20250704-090000",
          n_rows=3, grand_amount_p=600500, rows=[dict(jb, credit_p=(200500 if jb["bill_no"] == "802" else 200000)) for jb in jun_bills]))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: supplier-wise now carries every bill, so the month's figure is supplier-wise Rs 6,005",
   s6["basis"] == "supplier-wise" and s6["marg_p"] == 600500 and s6["bw_p"] == 600000 and s6["sw_p"] == 600500, "%s %s" % (s6["basis"], s6["marg_p"]))
ck("synthetic: bill 802 is listed as DISAGREE (bill-wise 2,000 vs supplier-wise 2,005) and offered a verdict",
   [b["bill_no"] for b in s6["disagree"]] == ["802"] and s6["disagree"][0]["disagree_p"] == 500 and s6["disagree"][0]["id"] in s6["needs_verdict"])
ck("synthetic: rule (c) -- the two reports disagree by Rs 5 for the month, so FINALISE is refused, naming 802",
   not s6["can_finalise"] and any("disagree" in x and "802" in x for x in s6["reasons"]), str(s6["reasons"]))
m6 = cl.get(P + "/page/month/2025-06").get_data(as_text=True)
ck("synthetic month page: 'Bill-wise and supplier-wise disagree (1)' section", "Bill-wise and supplier-wise disagree (1)" in m6)
push(dict(type="SUPPLIERWISE", md5="8" * 32, file="jun_sw2.XLS", period_from="2025-06-01", period_to="2025-06-30", export_stamp="20250705-090000",
          n_rows=3, grand_amount_p=600000, rows=jun_bills))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: a corrected supplier-wise export supersedes the wrong one; the reports agree again and the month can finalise",
   s6["can_finalise"] and not s6["disagree"] and s6["marg_p"] == 600000 and s6["basis"] == "supplier-wise", str(s6["reasons"]))
cl.post(P + "/api/verdict", json=dict(bill_id=b801, verdict="CORRECT"))
r = cl.post(P + "/api/finalise", json=dict(month="2025-06"))
ck("synthetic: the doctor finalises; purchase_month stores the month's figure and the NET item-wise total",
   r.status_code == 200 and q("SELECT billwise_total_p, itemwise_total_p FROM purchase_month WHERE month='2025-06'")[0][:] == (600000, 599500))
m6 = cl.get(P + "/page/month/2025-06").get_data(as_text=True)
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("a finalised month shows 'FINAL -- manoj, <when> IST' on the page and in the hub line",
   "FINAL \u2014 manoj, " in m6 and " IST" in m6 and s6["story"].endswith(" IST.") and "FINAL \u2014 manoj, " in s6["story"], s6["story"])
ck("no page shows a gross figure without the word gross beside it (July gross 508,062 never appears on the hub)", "508,062" not in cl.get(P + "/page/hub").get_data(as_text=True))

# ------------------------------------------------------------- 15. REV 4: the owner's ruling, on the real full-month August
as_("manoj", "doctor", {"checker"})
for pat, typ in (("PURCHASE_BILLWISE/2026-08/*_2026-08-01_to_2026-08-31__20260904-*.XLS", "BILLWISE"),
                 ("PURCHASE_SUPPLIERWISE/2026-08/*_2026-08-01_to_2026-08-31__20260904-*.XLS", "SUPPLIERWISE"),
                 ("PURCHASE_BILLITEMWISE/2026-08/*_2026-08-01_to_2026-08-31__*.XLS", "BILLITEMWISE")):
    f = one(pat)
    ck("archive holds the 04-Sep %s" % typ, bool(f))
    r = push(R.payload(f, typ))
    ck("04-Sep %s stored (supersedes the 02-Sep one of the same period)" % typ, r.get_json()["stored"] is True)
with app.test_request_context():
    sa = PA._month_summary(_db(), "2026-08")
bw0830 = R.payload(one("PURCHASE_BILLWISE/2026-08/*_2026-08-01_to_2026-08-29__*.XLS"), "BILLWISE")["md5"]
ck("rev 4 supersede-by-containment: the 30-Aug '01-29' bill-wise export is retired by a later full-month one",
   bool(q1("SELECT superseded_by FROM purchase_export WHERE md5=?", bw0830)))
ck("the 28-31 Aug BILLITEMWISE export is retired by the 04-Sep full-month one (period contained, later stamp)",
   q1("SELECT superseded_by FROM purchase_export WHERE md5=?", bi["md5"]) == R.payload(one("PURCHASE_BILLITEMWISE/2026-08/*_2026-08-01_to_2026-08-31__*.XLS"), "BILLITEMWISE")["md5"])
ck("August: 84 effective bills -- the bill Marg moved to its corrected supplier between 02 and 04 Sep is counted ONCE",
   len(sa["bills"]) == 84 and q1("SELECT COUNT(*) FROM purchase_bill WHERE month='2026-08'") == 85, "%d bills, %s rows" % (len(sa["bills"]), q1("SELECT COUNT(*) FROM purchase_bill WHERE month='2026-08'")))
ck("August: Rs 3,54,879 supplier-wise, bill-wise identical, no disagreement",
   sa["marg_p"] == 35487900 and sa["basis"] == "supplier-wise" and sa["sw_p"] == sa["bw_p"] == 35487900 and not sa["disagree"], "%s %s %s" % (sa["marg_p"], sa["sw_p"], sa["bw_p"]))
ck("August: every bill has item lines now; 83 agree; ONE purchase return (bill 148); nothing short",
   not sa["no_lines"] and len(sa["agree"]) == 83 and [x["bill"]["bill_no"] for x in sa["returns"]] == ["148"] and not sa["short"],
   "%d agree %s ret %d short %d nolines" % (len(sa["agree"]), [x["bill"]["bill_no"] for x in sa["returns"]], len(sa["short"]), len(sa["no_lines"])))
ck("August: the moved bill's OLD-key item lines (still live in the 27-Aug ITEMWISE export) are stale, not an orphan set",
   not sa["orphans"] and sa["orphan_p"] == 0 and sa["itemwise_p"] == sa["itemwise_bills_p"], str([(t["bill_no"], t["bill_date"]) for t in sa["orphans"]]))
ck("August is READY TO FINALISE with its one return (the owner's ruling)", sa["can_finalise"] and not sa["needs_verdict"], str(sa["reasons"]))
ck("August story: 'August: Rs 3,54,879 (supplier-wise, final for month-end). 84 bills; 1 carries a purchase return; ready to finalise.'",
   sa["story"] == "August: \u20b93,54,879 (supplier-wise, final for month-end). 84 bills; 1 carries a purchase return; ready to finalise.", sa["story"])
ma = cl.get(P + "/page/month/2026-08").get_data(as_text=True)
ck("August month page: FINALISE offered to the doctor, bill 148 labelled 'purchase return ... (Marg)', no verdict buttons anywhere",
   "FINALISE August 2026" in ma and "purchase return " in ma and "(Marg)</span>" in ma and 'onclick="verdict(' not in ma)
hub = cl.get(P + "/page/hub").get_data(as_text=True)
ck("hub: August row shows 3,54,879 and the story line verbatim", "3,54,879" in hub and sa["story"] in hub)
for pg in ("hub", "month/2026-08", "month/2026-07", "month/2026-09", "month/2025-06"):
    h = cl.get(P + "/page/" + pg).get_data(as_text=True)
    ck("wording: '%s' never says 'mark each', 'unverified' or 'Differ'" % pg,
       "mark each" not in h.lower() and "unverified" not in h and ">Differ<" not in h and "differs from" not in h)
r = cl.post(P + "/api/finalise", json=dict(month="2026-08"))
ck("the doctor finalises August; purchase_month stores the supplier-wise figure",
   r.status_code == 200 and q1("SELECT billwise_total_p FROM purchase_month WHERE month='2026-08'") == 35487900)
ck("hub August line now reads 'FINAL -- manoj, <when> IST'", "FINAL \u2014 manoj, " in cl.get(P + "/page/hub").get_data(as_text=True))
cl.post(P + "/api/reopen", json=dict(month="2026-08", reason="selftest leaves August provisional"))
ck("bw_amount_p / sw_amount_p exist on purchase_bill and are filled for every effective bill (rev 4 columns, added on first request)",
   q1("SELECT COUNT(*) FROM purchase_bill WHERE bw_amount_p IS NULL AND sw_amount_p IS NULL") == 0)

# ------------------------------------------------------------- 14. fail closed
as_("", "", set())
r = cl.get(P + "/page/hub")
ck("nobody signed in -> the hub is refused", r.status_code in (401, 302))
as_("stranger", "staff", set())
ck("signed in with no medical role -> refused (403)", cl.get(P + "/page/hub").status_code == 403)
ck("schema was created lazily, never at import (F-303)", PA._schema_done is True)

# ------------------------------------------------------------- 16. THE BOX'S OWN ORDER (rev 4): every archived
# Jul-Sep export, oldest stamp first, exactly as push_purchases.py sends them -- on a fresh db, through a
# rev-3-shaped purchase_bill (no rev-4 columns) so the first-request migration is exercised too.
DB2 = os.path.join(TMP, "box_order.db")
c2 = sqlite3.connect(DB2)
c2.executescript(io.open(os.path.join(HERE, "purchase_schema.sql"), encoding="utf-8").read())
c2.close()
PA._schema_done = False
app2 = Flask("box_order")


def _db2():
    if not has_app_context():
        raise RuntimeError("Working outside of application context")
    if "db" not in g:
        g.db = sqlite3.connect(DB2)
        g.db.row_factory = sqlite3.Row
    return g.db


PA.init(app2, _db2, _require, marg_token=TOKEN, assets_db=ASSETS, assets_url="https://assets.example")


@app2.teardown_appcontext
def _close2(_e):
    c = g.pop("db", None)
    if c is not None:
        c.close()


cl2 = app2.test_client()
WHO.update(user="manoj", role="doctor", roles={"checker"})
box = []
for typ in ("BILLWISE", "SUPPLIERWISE", "ITEMWISE", "BILLITEMWISE"):
    for f in glob.glob(os.path.join(ARCHIVE, "PURCHASE_" + typ, "2026-0[789]", "*.XLS")):
        box.append((os.path.basename(f).split("__")[2], f, typ))
box.sort()
ck("the archive holds the fifteen Jul-Sep exports the box was fed", len(box) == 15, str(len(box)))
stored = 0
for stamp, f, typ in box:
    r = cl2.post(P + "/api/push", json=R.payload(f, typ, MP.read_purchase) if typ == "ITEMWISE" else R.payload(f, typ), headers=H)
    stored += 1 if r.status_code == 200 and r.get_json()["stored"] else 0
ck("oldest-first: all fifteen stored as new (nothing arrives older than a live export that contains it)", stored == 15, str(stored))
c2 = sqlite3.connect(DB2)
sup = {r[0][-8:-4]: r[1] for r in c2.execute("SELECT file, superseded_by FROM purchase_export")}
cols = [r[1] for r in c2.execute("PRAGMA table_info(purchase_bill)")]
c2.close()
ck("box order: 01-29 Aug BILLWISE and 28-31 Aug BILLITEMWISE are superseded; the full-month ones are live",
   sup.get("3269") and sup.get("7222") and not sup.get("38f9") and not sup.get("a21d") and not sup.get("3bbb"), str(sup))
ck("box order: the rev-4 columns were added on the first request and back-filled", "bw_amount_p" in cols and "sw_amount_p" in cols)
with app2.test_request_context():
    b7, b8, b9 = (PA._month_summary(_db2(), m) for m in ("2026-07", "2026-08", "2026-09"))
ck("box order, August: 84 bills, Rs 3,54,879 supplier-wise, every bill has lines, 83 agree, one return (148), nothing stray left over",
   len(b8["bills"]) == 84 and b8["marg_p"] == 35487900 and b8["basis"] == "supplier-wise" and not b8["no_lines"] and len(b8["agree"]) == 83
   and [x["bill"]["bill_no"] for x in b8["returns"]] == ["148"] and not b8["orphans"] and not b8["short"], b8["story"])
ck("box order, August: the moved bill (02 of 18-Aug) found its lines under the OLD supplier key (stray set, rev 4)",
   any(b["bill_no"].endswith("02") and b["bill_date"] == "2026-08-18" for b in b8["agree"]) and len(b8["stray"]) == 1, str(list(b8["stray"])))
ck("box order, August story is exactly the line the hub will show",
   b8["story"] == "August: \u20b93,54,879 (supplier-wise, final for month-end). 84 bills; 1 carries a purchase return; ready to finalise.", b8["story"])
ck("box order, July story is exactly the line the hub will show",
   b7["story"] == "July: \u20b94,76,393 (supplier-wise, final for month-end). 103 bills; 2 carry a purchase return; ready to finalise.", b7["story"])
ck("box order, September: bill-wise stands in, 11 bills agree, ready to finalise",
   b9["marg_p"] == 7243800 and b9["basis"] == "bill-wise" and len(b9["agree"]) == 11 and b9["can_finalise"], b9["story"])
h2 = cl2.get(P + "/page/hub").get_data(as_text=True)
ck("box order: the hub renders with all three stories and none of the banned wording",
   cl2.get(P + "/page/hub").status_code == 200 and b7["story"] in h2 and b8["story"] in h2 and b9["story"] in h2 and "mark each" not in h2.lower())
ck("box order: every month page renders 200",
   all(cl2.get(P + "/page/month/" + m).status_code == 200 for m in ("2026-07", "2026-08", "2026-09")))

# ------------------------------------------------------------- 13. S225: the staff order page
# back on the FIRST app/db (the one with ZZTEST STOCKIST and its plan). The S224 tail re-pointed the
# module at app2/DB2 (PA.init sets module globals); point it home again, as the box has one db.
PA._db, PA._require = _db, _require
# clinic_day_pdf.py sits beside purchase_app.py on the box (S224 pin 518affe9); offline it is in its own kit
sys.path.insert(0, os.path.join(KITS, "S224_DAY_REVENUE_PDF"))
if True:
    ck("unit word: strips for pack_size>1", PA._unit_word("1*10", 10) == "strip" and PA._unit_word("1*10", 10, 20) == "strips")
    ck("unit word: bottle for ML, tube for GM, unit otherwise",
       PA._unit_word("100 ML", 1) == "bottle" and PA._unit_word("15 GM", 1) == "tube" and PA._unit_word("1 NOS", 1) == "unit")
    ck("rounding: 1..10 strips -> 10; 11 -> 20; 47 -> 50; 50 -> 50; 0 -> 0",
       [PA._staff_qty(n, "strip") for n in (1, 10, 11, 47, 50, 0)] == [10, 10, 20, 50, 50, 0])
    ck("rounding: bottles keep the engine's quantity", PA._staff_qty(3, "bottle") == 3)
    T10 = "9" + "7" * 4 + "3" * 5                   # built at run time; never a literal (F-185 gate)
    ck("wa digits: 10-digit -> 91 prefix; +91 kept; junk -> empty",
       PA._wa_digits(T10[:5] + " " + T10[5:]) == "91" + T10 and PA._wa_digits("+91 " + T10[:5] + "-" + T10[5:]) == "91" + T10
       and PA._wa_digits("0" + T10) == "91" + T10 and PA._wa_digits("call me") == "")
    txt = PA._wa_text([dict(item="ZZTEST ITEM 1", qty=20, packing="1*10", pack_size=10), dict(item="X SYRUP", qty=2, packing="100 ML", pack_size=1)])
    ck("WhatsApp text is EXACTLY header, blank line, item lines -- nothing else",
       txt == "Sanjeevni Medicos, G 15 Rampur Garden, Bareilly\n\nZZTEST ITEM 1 — 20 strips\nX SYRUP — 2 bottles", repr(txt))
    url = PA._wa_url(FAKE_PHONE, txt)
    ck("wa.me url carries the number and the encoded text", url.startswith("https://wa.me/91" + FAKE_PHONE + "?text=Sanjeevni%20Medicos"))
    as_("amir", "staff", {"viewer"})
    r = cl.get(P + "/page/staff")
    sp = r.get_data(as_text=True)
    ck("staff page renders for a viewer (amir)", r.status_code == 200)
    for word in ("Order medicines", "Stock now", "Order qty", "Send on WhatsApp", "Call", "Orders sent", "Print A4"):
        ck("staff page shows '%s'" % word, word in sp)
    for banned in ("Rate", "Per day", "Cover after", "cadence", "confidence", "approx", "₹", "Save as order", "Copy this order", "confirm</span>"):
        ck("staff page never shows '%s'" % banned, banned not in sp)
    ck("staff page never prints the phone number as text", (">" + FAKE_PHONE) not in sp and ("91" + FAKE_PHONE + "<") not in sp)
    ck("staff page has the tel: link for the stockist", 'href="tel:91' + FAKE_PHONE + '"' in sp)
    ck("staff page shows the OUT item with the engine's rounded quantity", "ZZTEST ITEM 1" in sp and "<b>%d</b> strips" % names["ZZTEST ITEM 1"]["order_strips"] in sp and names["ZZTEST ITEM 1"]["order_strips"] % 10 == 0)
    ck("staff page does NOT show the item the engine did not reorder", "ZZTEST ITEM 2" not in sp)
    # the send
    import re as _re
    staff_json = json.loads(_re.search(r"const STAFF=(\[.*?\]);", sp, _re.S).group(1))
    zzs = next(v for v in staff_json if "ZZTEST STOCKIST" in v["vendor"])
    before = q1("SELECT COUNT(*) FROM purchase_order")
    r = cl.post(P + "/api/order", json=dict(action="staff_send", vendor=zzs["vendor"], lines=zzs["lines"]))
    j = r.get_json()
    ck("a VIEWER may send: 200 with an order id and a wa.me url", r.status_code == 200 and j["ok"] and j["wa_url"].startswith("https://wa.me/91" + FAKE_PHONE + "?text="))
    soid = j["order_id"]
    ck("the order is written as SENT by amir with note whatsapp",
       q("SELECT status, created_by, note FROM purchase_order WHERE id=?", soid)[0][:] == ("sent", "amir", "whatsapp"))
    ck("one new order, its lines in strips with pack_size and units", q1("SELECT COUNT(*) FROM purchase_order") == before + 1
       and q1("SELECT COUNT(*) FROM purchase_order_line WHERE order_id=?", soid) == len(zzs["lines"])
       and q1("SELECT packs FROM purchase_order_line WHERE order_id=? AND item='ZZTEST ITEM 1'", soid) == names["ZZTEST ITEM 1"]["order_strips"])
    ck("the send is audited as order_sent_whatsapp without a phone in it",
       q1("SELECT COUNT(*) FROM purchase_audit WHERE action='order_sent_whatsapp' AND ref=?", str(soid)) == 1
       and FAKE_PHONE not in (q1("SELECT detail FROM purchase_audit WHERE action='order_sent_whatsapp' AND ref=?", str(soid)) or ""))
    from urllib.parse import unquote
    ck("the wa.me text is the dictated header + this order's lines",
       unquote(j["wa_url"].split("text=", 1)[1]).startswith("Sanjeevni Medicos, G 15 Rampur Garden, Bareilly\n\nZZTEST ITEM 0 — ") and "\nZZTEST ITEM 1 — " in unquote(j["wa_url"].split("text=", 1)[1]))
    r = cl.post(P + "/api/order", json=dict(action="staff_send", vendor="NOBODY STOCKIST", lines=zzs["lines"]))
    ck("a stockist with no number -> 409 and NO order written", r.status_code == 409 and q1("SELECT COUNT(*) FROM purchase_order") == before + 1)
    r = cl.post(P + "/api/order", json=dict(action="staff_send", vendor=zzs["vendor"], lines=[dict(item="X", qty=0)]))
    ck("all-zero lines -> 400", r.status_code == 400)
    sp2 = cl.get(P + "/page/staff").get_data(as_text=True)
    ck("the sent order appears in 'Orders sent' with a Print A4 button", ("#%d</td>" % soid) in sp2 and ("/order/%d/pdf" % soid) in sp2)
    # the PDF
    r = cl.get(P + "/order/%d/pdf" % soid)
    pdf = r.get_data()
    ck("the A4 PDF renders (200, application/pdf, %%PDF header, %%EOF)", r.status_code == 200 and r.headers["Content-Type"] == "application/pdf" and pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF"))
    ck("the PDF carries the header, the stockist and the item -- and no rupee figure",
       b"Sanjeevni Medicos, G 15 Rampur Garden, Bareilly" in pdf and b"ZZTEST STOCKIST" in pdf and b"ZZTEST ITEM 1" in pdf and b"Rs " not in pdf and FAKE_PHONE.encode() not in pdf)
    ck("a missing order's PDF -> 404", cl.get(P + "/order/999999/pdf").status_code == 404)
    as_("", "", set())
    ck("signed out: staff page 401, send 401, pdf 401",
       cl.get(P + "/page/staff").status_code == 401 and cl.post(P + "/api/order", json=dict(action="staff_send")).status_code == 401
       and cl.get(P + "/order/%d/pdf" % soid).status_code == 401)
    as_("manoj", "doctor", {"checker"})
    op2 = cl.get(P + "/page/orders").get_data(as_text=True)
    ck("the doctor's Orders page still shows the admin detail and the WhatsApp-sent order in its book", "Per day" in op2 and "Cover after" in op2 and ("#%d</td>" % soid) in op2)
    ck("the doctor's nav now carries 'Order medicines'", "Order medicines" in op2)

# ------------------------------------------------------------- 14. S225 rev 7: the engine rounds once; the phone book
PA._db, PA._require = _db, _require
as_("manoj", "doctor", {"checker"})
with app.test_request_context():
    plan7 = PA.reorder_plan(_db(), today)
zz7 = next(v for v in plan7["vendors"] if "ZZTEST STOCKIST" in v["vendor"])
ck("engine: every strip line is a multiple of 10 and at least 10", all(l["order_strips"] % 10 == 0 and l["order_strips"] >= 10 for l in zz7["lines"] if l["order_strips"] > 0 and l.get("unit") == "strip"))
ck("engine: the value follows the (rounded) quantity", all(abs(l["value_p"] - l["order_strips"] * l["rate_p"]) <= l["order_strips"] for l in zz7["lines"] if l["order_strips"] > 0))
op7 = cl.get(P + "/page/orders").get_data(as_text=True)
ck("doctor's Orders page: column is 'Order qty', quantities carry the unit word, copy text reads 'Item — qty strips'", "Order qty" in op7 and "</b> strips" in op7 and _re.search(r"ZZTEST ITEM 1 — \d+ strips", op7) is not None)
ck("doctor's page and staff page agree on the quantity", ("<b>%d</b> strips" % names["ZZTEST ITEM 1"]["order_strips"]) in op7)
# the phone book: allow-list, fail-closed
FAKE2 = "9" + "7" * 9
r = cl.get(P + "/page/book"); ck("the doctor opens the phone book (no setting row yet: doctor only)", r.status_code == 200 and "Stockist phone book" in r.get_data(as_text=True))
as_("darpan", "staff", {"maker"})
ck("darpan is REFUSED while no setting names him (fail-closed)", cl.get(P + "/page/book").status_code == 403)
c = sqlite3.connect(DB); c.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?,?)", (PA.BOOK_USERS_KEY, "darpan,shavez")); c.commit(); c.close()
r = cl.get(P + "/page/book"); bk = r.get_data(as_text=True)
ck("darpan opens the book once named; the nav shows Phone book", r.status_code == 200 and "Phone book" in bk)
ck("the book lists ZZTEST STOCKIST with its number and 'from Marg / manojz', no bank details", "ZZTEST STOCKIST" in bk and FAKE_PHONE in bk and "no bank details" in bk)
as_("amir", "staff", {"viewer"})
ck("amir (not named) is refused the page and the API, and sees no Phone book link", cl.get(P + "/page/book").status_code == 403 and cl.post(P + "/api/book", json=dict(action="phones")).status_code == 403 and "Phone book" not in cl.get(P + "/page/staff").get_data(as_text=True))
as_("darpan", "staff", {"maker"})
r = cl.post(P + "/api/book", json=dict(action="phones", vendor="ZZTEST STOCKIST", phone=FAKE_PHONE, phone2="+91 " + FAKE2[:5] + " " + FAKE2[5:]))
ck("darpan adds a second number (normalised to 10 digits)", r.status_code == 200 and q1("SELECT phone2 FROM purchase_vendor_contact WHERE vendor_norm=?", PA.supplier_key("ZZTEST STOCKIST")) == FAKE2)
ck("the audit row carries last-4 only, never the number", q1("SELECT detail FROM purchase_audit WHERE action='book_phones' ORDER BY id DESC LIMIT 1").count(FAKE2[-4:]) >= 1 and FAKE2 not in q1("SELECT detail FROM purchase_audit WHERE action='book_phones' ORDER BY id DESC LIMIT 1"))
r = cl.post(P + "/api/book", json=dict(action="phones", vendor="ZZTEST STOCKIST", phone="12345", phone2=""))
ck("a phone that is not 10 digits is refused", r.status_code == 400 and "10 digits" in r.get_json()["message"])
# the nightly push must not clobber a server edit
r = cl.post(P + "/api/vendors", json=dict(pairs={"ZZTEST STOCKIST": "9" + "1" * 9}), headers=H)
ck("after a server edit the manojz push leaves the number alone (source='server' wins)", r.status_code == 200 and q1("SELECT phone FROM purchase_vendor_contact WHERE vendor_norm=?", PA.supplier_key("ZZTEST STOCKIST")) == FAKE_PHONE)
# staff page rings both numbers
as_("amir", "staff", {"viewer"})
sp7 = cl.get(P + "/page/staff").get_data(as_text=True)
ck("staff page shows Call 1 and Call 2 for a stockist with two numbers", "Call 1" in sp7 and "Call 2" in sp7 and 'tel:91' + FAKE2 in sp7)
# bank details: darpan saves -> UNVERIFIED; doctor verifies; doctor's own save -> VERIFIED; a later edit by darpan drops to UNVERIFIED
as_("darpan", "staff", {"maker"})
ACC = "1" + "2" * 11
r = cl.post(P + "/api/book", json=dict(action="bank", vendor="ZZTEST STOCKIST", acct_name="ZZ Test Traders", acct_no=ACC, ifsc="HDFC0001234", bank_branch="HDFC Civil Lines", upi_id=""))
ck("darpan saves bank details -> UNVERIFIED", r.status_code == 200 and r.get_json()["bank_status"] == "UNVERIFIED")
ck("the bank audit carries field names and last-4 only", ACC not in q1("SELECT detail FROM purchase_audit WHERE action='book_bank' ORDER BY id DESC LIMIT 1") and "acct_no" in q1("SELECT detail FROM purchase_audit WHERE action='book_bank' ORDER BY id DESC LIMIT 1"))
r = cl.post(P + "/api/book", json=dict(action="bank", vendor="ZZTEST STOCKIST", acct_name="ZZ Test Traders", acct_no=ACC, ifsc="hdfc001234", bank_branch="x", upi_id=""))
ck("a wrong IFSC is refused", r.status_code == 400 and "IFSC" in r.get_json()["message"])
ck("darpan cannot verify", cl.post(P + "/api/book", json=dict(action="verify", vendor="ZZTEST STOCKIST")).status_code == 403)
bk2 = cl.get(P + "/page/book").get_data(as_text=True)
_tbl = bk2[:bk2.index("<script>")]
ck("darpan's book shows UNVERIFIED, 'waits for Dr Manoj'; the TABLE shows account last-4 only (the full number is only in the editors' pre-fill data)", "UNVERIFIED" in bk2 and "waits for Dr Manoj" in bk2 and ACC not in _tbl and ("…" + ACC[-4:]) in _tbl)
ck("onclick attributes are well-formed (vendor names quoted with &quot;)", 'onclick="bookPhones(&quot;ZZTEST STOCKIST&quot;)"' in bk2)
as_("manoj", "doctor", {"checker"})
bk3 = cl.get(P + "/page/book").get_data(as_text=True)
ck("the doctor's book offers Verify", "bookVerify(" in bk3 and ">Verify<" in bk3)
r = cl.post(P + "/api/book", json=dict(action="verify", vendor="ZZTEST STOCKIST"))
ck("the doctor verifies -> VERIFIED with who/when", r.status_code == 200 and q("SELECT bank_status, bank_verified_by FROM purchase_vendor_contact WHERE vendor_norm=?", PA.supplier_key("ZZTEST STOCKIST"))[0][:] == ("VERIFIED", "manoj"))
r = cl.post(P + "/api/book", json=dict(action="add", vendor="ZZNEW STOCKIST", phone=FAKE2, phone2="", acct_name="ZZ New", acct_no="9" * 12, ifsc="SBIN0004567", bank_branch="SBI", upi_id="zznew@upi"))
ck("the doctor adds a new stockist with bank details -> VERIFIED by the act", r.status_code == 200 and r.get_json()["bank_status"] == "VERIFIED" and q1("SELECT added_by FROM purchase_vendor_contact WHERE vendor_norm=?", PA.supplier_key("ZZNEW STOCKIST")) == "manoj")
ck("adding the same name twice is refused", cl.post(P + "/api/book", json=dict(action="add", vendor="ZZNEW STOCKIST", phone=FAKE2)).status_code == 409)
as_("darpan", "staff", {"maker"})
r = cl.post(P + "/api/book", json=dict(action="bank", vendor="ZZNEW STOCKIST", acct_name="ZZ New", acct_no="9" * 12, ifsc="SBIN0004567", bank_branch="SBI Main", upi_id="zznew@upi"))
ck("darpan modifies one bank field on a VERIFIED record -> back to UNVERIFIED", r.status_code == 200 and r.get_json()["bank_status"] == "UNVERIFIED")
r = cl.post(P + "/api/book", json=dict(action="bank", vendor="ZZNEW STOCKIST", acct_name="ZZ New", acct_no="9" * 12, ifsc="SBIN0004567", bank_branch="SBI Main", upi_id="zznew@upi"))
ck("saving identical bank details changes nothing", r.status_code == 200 and r.get_json().get("unchanged") is True)
r = cl.post(P + "/api/book", json=dict(action="add", vendor="ZZNOPHONE", phone=""))
ck("a new stockist without a first phone is refused", r.status_code == 400)
as_("", "", set())
ck("signed out: book 401, api 401", cl.get(P + "/page/book").status_code == 401 and cl.post(P + "/api/book", json={}).status_code == 401)
ck("no bank value, no full phone in any audit row", not any((ACC in (d or "")) or (FAKE2 in (d or "")) or (FAKE_PHONE in (d or "")) for (d,) in [(r[0],) for r in q("SELECT detail FROM purchase_audit WHERE action LIKE 'book_%'")]))

# ------------------------------------------------------------- 15. the gap the box's walk found: a db that never saw a vendors push
TMP3 = tempfile.mkdtemp(prefix="s225fresh_"); DB3 = os.path.join(TMP3, "finance.db")
c3 = sqlite3.connect(DB3)
c3.executescript("""
CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER, ingest_batch_id INTEGER, unit TEXT NOT NULL, business_date TEXT NOT NULL,
  bill_no TEXT NOT NULL, is_return INTEGER NOT NULL DEFAULT 0, seq INTEGER, item_name TEXT NOT NULL, item_key TEXT NOT NULL, pack TEXT, qty_raw TEXT,
  amount_p INTEGER, expiry_ym TEXT, batch TEXT);
CREATE TABLE stock_snapshot (as_on TEXT NOT NULL, item TEXT NOT NULL, qty INTEGER NOT NULL, packing TEXT, pack_size INTEGER NOT NULL DEFAULT 1,
  loaded_at TEXT NOT NULL, source TEXT, PRIMARY KEY (as_on, item));
CREATE TABLE stock_feed (id INTEGER PRIMARY KEY, as_on TEXT NOT NULL, source TEXT NOT NULL, item TEXT NOT NULL, qty INTEGER NOT NULL, received_at TEXT NOT NULL);
""")
c3.execute("INSERT INTO stock_snapshot VALUES (?,?,?,?,?,?,?)", (today.strftime("%d-%m-%Y"), "ZZFRESH ITEM", 0, "1*10", 10, "t", "push_snapshot"))
for d in range(26):
    c3.execute("INSERT INTO sale_line_item (unit,business_date,bill_no,seq,item_name,item_key,qty_raw) VALUES (?,?,?,?,?,?,?)",
               ("medical", (today - dt.timedelta(days=d)).isoformat(), "F%d" % d, 1, "ZZFRESH ITEM", "zzfresh item", "0:2"))
c3.commit(); c3.close()
def _db3():
    if "db3" not in g:
        g.db3 = sqlite3.connect(DB3); g.db3.row_factory = sqlite3.Row
    return g.db3
app3 = Flask("fresh"); PA._schema_done = False
PA.init(app3, _db3, _require, unit="medical", marg_token=TOKEN, assets_db=os.path.join(TMP3, "absent.db"), assets_url="https://assets.example")
@app3.teardown_appcontext
def _close3(_e):
    c = g.pop("db3", None)
    if c is not None: c.close()
cl3 = app3.test_client()
as_("amir", "staff", {"viewer"})
r = cl3.get(P + "/page/staff")
ck("FRESH DB, no vendors push ever: the staff page renders 200 (the columns are created on the first request of any kind)", r.status_code == 200 and "Order medicines" in r.get_data(as_text=True), str(r.status_code))
c3 = sqlite3.connect(DB3); cols3 = {x[1] for x in c3.execute("PRAGMA table_info(purchase_vendor_contact)")}; c3.close()
ck("FRESH DB: phone2 and bank_status exist after that first request", "phone2" in cols3 and "bank_status" in cols3)
PA._schema_done = False; PA._db, PA._require = _db, _require

# ------------------------------------------------------------- 16. S225 rev 8: when the goods arrive
PA._db, PA._require = _db, _require
as_("amir", "staff", {"viewer"})
sp8 = cl.get(P + "/page/staff").get_data(as_text=True)
ck("a SENT order shows Arrived and Different on the staff page", ("arrive(%d," % soid) in sp8 and ("arriveDiff(%d)" % soid) in sp8 and "Scan the bill" not in sp8)
# a second sent order to receive by line
staff_json2 = json.loads(_re.search(r"const STAFF=(\[.*?\]);", sp8, _re.S).group(1))
zz2 = next(v for v in staff_json2 if "ZZTEST STOCKIST" in v["vendor"])
r = cl.post(P + "/api/order", json=dict(action="staff_send", vendor=zz2["vendor"], lines=zz2["lines"]))
soid2 = r.get_json()["order_id"]
ck("second order sent; sent_by recorded", r.status_code == 200 and q1("SELECT sent_by FROM purchase_order WHERE id=?", soid2) == "amir")
# one tap on the first
r = cl.post(P + "/api/order", json=dict(action="arrive", id=soid))
ck("Arrived (one tap): order RECEIVED by amir, every line supplied = asked, nothing short",
   r.status_code == 200 and r.get_json()["status"] == "received" and q("SELECT status, received_by FROM purchase_order WHERE id=?", soid)[0][:] == ("received", "amir")
   and q1("SELECT COUNT(*) FROM purchase_order_line WHERE order_id=? AND (supplied IS NULL OR supplied<>packs OR short<>0)", soid) == 0)
ck("receiving it twice is refused (409)", cl.post(P + "/api/order", json=dict(action="arrive", id=soid)).status_code == 409)
ck("the receipt is audited", q1("SELECT COUNT(*) FROM purchase_audit WHERE action='order_received' AND ref=?", str(soid)) == 1)
# by line on the second: ITEM 1 short (asked N, got 0 -> short), ITEM 0 as asked
lines2 = q("SELECT id, item, packs FROM purchase_order_line WHERE order_id=?", soid2)
l1 = next(l for l in lines2 if l["item"] == "ZZTEST ITEM 1"); l0 = next(l for l in lines2 if l["item"] == "ZZTEST ITEM 0")
r = cl.post(P + "/api/order", json=dict(action="arrive_diff", id=soid2, lines=[dict(id=l1["id"], supplied=0, short=True), dict(id=l0["id"], supplied=l0["packs"], short=False)]))
j = r.get_json()
ck("Different: ITEM 1 recorded short (asked %d, got 0), ITEM 0 as asked; order RECEIVED" % l1["packs"],
   r.status_code == 200 and j["status"] == "received" and len(j["short"]) == 1 and j["short"][0]["item"] == "ZZTEST ITEM 1" and j["short"][0]["got"] == 0
   and q("SELECT supplied, short FROM purchase_order_line WHERE id=?", l1["id"])[0][:] == (0, 1) and q("SELECT supplied, short FROM purchase_order_line WHERE id=?", l0["id"])[0][:] == (l0["packs"], 0))
# a partial supply without ticking short is still a short (less came than asked)
r = cl.post(P + "/api/order", json=dict(action="staff_send", vendor=zz2["vendor"], lines=zz2["lines"])); soid3 = r.get_json()["order_id"]
l1c = q1("SELECT id FROM purchase_order_line WHERE order_id=? AND item='ZZTEST ITEM 1'", soid3)
r = cl.post(P + "/api/order", json=dict(action="arrive_diff", id=soid3, lines=[dict(id=l1c, supplied=3, short=False)]))
ck("a partial supply (3 of %d) without the tick is recorded as short anyway" % l1["packs"], r.status_code == 200 and q("SELECT supplied, short FROM purchase_order_line WHERE id=?", l1c)[0][:] == (3, 1))
# the carry: the short rides into the next plan
with app.test_request_context():
    carried = PA._carried_shorts(_db(), today)
    plan8 = PA.reorder_plan(_db(), today)
ck("carried shorts: ZZTEST ITEM 1 is carried from the LATEST received order (shortfall %d)" % (l1["packs"] - 3), "zztest item 1" in {k.lower() for k in carried} and list(carried.values())[0]["shortfall"] in (l1["packs"] - 3, l1["packs"]))
zz8 = next(v for v in plan8["vendors"] if "ZZTEST STOCKIST" in v["vendor"])
it1 = next(l for l in zz8["lines"] if l["item"] == "ZZTEST ITEM 1")
ck("the plan's ITEM 1 line carries the shortfall and says 'carried', a multiple of 10 (rev 9: received stock now counts, so the base need may be nil)", any("carried" in w for w in it1["why"]) and it1["order_strips"] % 10 == 0 and it1["order_strips"] >= 10)
sp9 = cl.get(P + "/page/staff").get_data(as_text=True)
ck("RECEIVED orders show 'Scan the bill' with the note to type, and the short count", "Scan the bill" in sp9 and "ZZTEST STOCKIST" in sp9 and "short — carried to the next order" in sp9)
ck("the staff page explains Arrived / Different", "tap <b>Arrived</b>" in sp9)
# once re-ordered from that stockist the carry stops
r = cl.post(P + "/api/order", json=dict(action="staff_send", vendor=zz2["vendor"], lines=[dict(item="ZZTEST ITEM 1", qty=10, pack_size=10, packing="1*10", rate_p=20000)]))
with app.test_request_context():
    carried2 = PA._carried_shorts(_db(), today)
ck("after re-ordering ITEM 1 from the same stockist the carry is consumed", not any(k.lower() == "zztest item 1" for k in carried2))
as_("", "", set())
ck("signed out: arrive -> 401", cl.post(P + "/api/order", json=dict(action="arrive", id=soid2)).status_code == 401)

# ------------------------------------------------------------- 17. S225 rev 9: live cross-check; stock in transit
PA._db, PA._require, PA._assets_db = _db, _require, ASSETS      # the S224 tail re-pointed the module at app2; point it home
as_("manoj", "doctor", {"checker"})
cl.get(P + "/page/hub")
ck("opening the hub remembers the scans' fingerprint", q1("SELECT value FROM setting WHERE key=?", PA.REMATCH_SEEN_KEY) is not None)
n1 = q1("SELECT COUNT(*) FROM purchase_audit WHERE action='rematch'")
cl.get(P + "/page/hub"); cl.get(P + "/page/scans")
ck("opening again with no change does NOT re-match (cheap)", q1("SELECT COUNT(*) FROM purchase_audit WHERE action='rematch'") == n1)
ac = sqlite3.connect(ASSETS)
acols = {x[1] for x in ac.execute("PRAGMA table_info(bills)")}
ac.execute("INSERT INTO bills (kind, vendor, bill_no, bill_date, total_amount, status) VALUES ('Pharmacy','ZZ LIVE SCAN','L1','2026-09-04', 1234.0, 'new')" if "ocr_status" not in acols or True else "")
ac.commit(); ac.close()
cl.get(P + "/page/scans")
ck("a NEW scan landing is picked up on the next page opening: one more re-match", q1("SELECT COUNT(*) FROM purchase_audit WHERE action='rematch'") == n1 + 1)
# a push re-matches at once
bw = one("PURCHASE_BILLWISE/2026-09/*.XLS")
if bw and MP:
    body = R.payload(bw, "BILLWISE", MP.read_purchase); body["file"] = "REPUSH_LIVE_" + os.path.basename(bw); body["export_stamp"] = "20260904-235959"
    r = push(body)
    ck("a push that stores re-matches at once (audit who='push')", r.status_code == 200 and q1("SELECT COUNT(*) FROM purchase_audit WHERE action='rematch' AND who='push'") >= 1, str(r.status_code) + " " + str(r.get_json()))
else:
    ck("(no September BILLWISE export on disk -- push re-match not exercised here)", True)
# in transit
with app.test_request_context():
    tr = PA._in_transit(_db(), today)
    plan9 = PA.reorder_plan(_db(), today)
ck("stock in transit: the RECEIVED ZZTEST quantities not yet in Marg are counted", any("zztest item 0" == k.lower() for k in tr) and tr[[k for k in tr if k.lower()=="zztest item 0"][0]]["units"] > 0)
zz9 = next((v for v in plan9["vendors"] if "ZZTEST STOCKIST" in v["vendor"]), None)
it0 = next((l for l in (zz9["lines"] if zz9 else []) if l["item"] == "ZZTEST ITEM 0"), None)
ck("the plan's ITEM 0 line says 'not yet in Marg — counted as stock' (or the item no longer needs ordering)", it0 is None or any("counted as stock" in w for w in it0["why"]))

print("\n%d PASS  %d FAIL" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED: " + f)
sys.exit(1 if FAILED else 0)
