#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_purchase_app.py -- S224: the REAL blueprint, on a temp finance.db, fed the REAL
archived Marg exports through the SAME parser the manojz leg uses (marg_purchase_rows.py).

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


print("S224 selftest on %s" % TMP)

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
SW = sorted(glob.glob(os.path.join(ARCHIVE, "PURCHASE_SUPPLIERWISE/2026-08/*_2026-08-01_to_2026-08-31__*.XLS")))
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

BI = one("PURCHASE_BILLITEMWISE/2026-08/*.XLS")
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
ck("July month cannot finalise while lines are undated, and says so",
   not s["can_finalise"] and any("could not be dated" in x for x in s["reasons"]))
push(R.payload(BWJ, "BILLWISE"))
ck("July BILLWISE arrives: the lines are re-dated by the bills", q1("SELECT COUNT(*) FROM purchase_line WHERE bill_date IS NULL") == 0)
ck("July bills == its BILLWISE rows", q1("SELECT COUNT(*) FROM purchase_bill WHERE month='2026-07'") == R.payload(BWJ, "BILLWISE")["n_rows"])

# ------------------------------------------------------------- 6. the month summary and the hub
with app.test_request_context():
    s = PA._month_summary(_db(), "2026-08")
ck("August summary: bill-wise == Marg TOTAL", s["billwise_p"] == bw["grand_amount_p"])
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
ck("August is provisional and cannot finalise (bills without item lines, one that differs)",
   s["status"]["status"] == "provisional" and not s["can_finalise"] and any("differs" in x for x in s["reasons"])
   and any("no item-wise lines" in x for x in s["reasons"]))
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
for word in ("cannot finalise yet", "bill-wise total", "Correct", "Wrong", "unverified"):
    ck("month page shows '%s'" % word, word in m)
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
ck("finalise refused while a bill is WRONG, naming it", r.status_code == 409 and any("WRONG" in x for x in r.get_json()["reasons"]))
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
ck("hub turns green when the next ping says ok", "manojz pull ok" in cl.get(P + "/page/hub").get_data(as_text=True))
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
ck("July: bill-wise == Rs 4,76,393", sj["billwise_p"] == 47639300, str(sj["billwise_p"]))
ck("July: no bill without lines, no line set without a bill", not sj["no_lines"] and not sj["orphans"])
ck("July: the DIFFERS bucket holds <= 2 bills (the two purchase returns)", 0 < len(sj["differ"]) <= 2, str(len(sj["differ"])))
ck("July: 101 of 103 bills AGREE", len(sj["agree"]) == 101 and len(sj["bills"]) == 103, "%d/%d" % (len(sj["agree"]), len(sj["bills"])))
ck("July: each DIFFERS bill carries the 'purchase return?' hint (item-wise > bill-wise)",
   all(x["hint"].startswith("purchase return") for x in sj["differ"]))
ck("July: the refusal NAMES the differing bills", not sj["can_finalise"] and all(x["bill"]["bill_no"] in " ".join(sj["reasons"]) for x in sj["differ"]))
ck("September: item-wise NET == 7243737 paise (Rs 72,437.37)", ss["itemwise_p"] == 7243737, str(ss["itemwise_p"]))
ck("September: bill-wise == Rs 72,438 and all 11 bills AGREE within Rs 1",
   ss["billwise_p"] == 7243800 and len(ss["agree"]) == 11 == len(ss["bills"]) and not ss["differ"] and not ss["no_lines"])
ck("September CAN finalise on the rev-2 rule", ss["can_finalise"], str(ss["reasons"]))
ck("August: reports the 27-Aug gap as NO ITEM LINES (item-wise export missing for that date)",
   "2026-08-27" in sa["gap_dates"] and any("27-Aug" in x and "no item-wise lines" in x for x in sa["reasons"]))
ck("August: the hub verdict names the gap and the one-line fix", "27-Aug" in sa["story"] and "export item-wise 01-31 Aug once" in sa["story"])
ck("August: agree + differ + no-lines == bills", len(sa["agree"]) + len(sa["differ"]) + len(sa["no_lines"]) == len(sa["bills"]))
hub = cl.get(P + "/page/hub").get_data(as_text=True)
ck("hub shows Item-wise (net), Agree / Differ / No lines columns and the verdict line",
   "Item-wise (net)" in hub and ">Agree<" in hub and ">Differ<" in hub and ">No lines<" in hub and "export item-wise 01-31 Aug once" in hub)
ck("hub July item-wise is the NET figure", "477,396" in hub and "508,062" not in hub)
ck("hub September shows Rs 72,437 net beside Rs 72,438 bill-wise", "72,437" in hub and "72,438" in hub)
mj = cl.get(P + "/page/month/2026-07").get_data(as_text=True)
ck("July month page lists the DIFFERS bucket with the hint and a gross column labelled gross",
   "Bills that differ from their item lines (2)" in mj and "purchase return?" in mj and "Item-wise (gross)" in mj)
ma = cl.get(P + "/page/month/2026-08").get_data(as_text=True)
ck("August month page lists the NO ITEM LINES bucket, each row saying which date's export is missing",
   "Bills with no item lines (%d)" % len(sa["no_lines"]) in ma and ma.count("item-wise export missing for 27-Aug") >= 1)
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
ck("synthetic: buckets are 1 agree / 1 differs / 1 no lines", (len(s6["agree"]), len(s6["differ"]), len(s6["no_lines"])) == (1, 1, 1))
ck("synthetic: the DIFFERS hint for net < bill-wise is not 'purchase return'", not s6["differ"][0]["hint"].startswith("purchase return"))
r = cl.post(P + "/api/finalise", json=dict(month="2025-06"))
rs = " ".join(r.get_json().get("reasons") or [])
ck("finalise refused: names the no-lines bill 803 AND the differing bill 802", r.status_code == 409 and "803" in rs and "802" in rs and "12-Jun" in rs)
# a later BILLITEMWISE export (a different type, so it coexists) carries 803's lines and a corrected 802 that now agrees
push(dict(type="BILLITEMWISE", md5="e" * 32, file="jun_bi.XLS", period_from="2025-06-01", period_to="2025-06-30", export_stamp="20250702-090000",
          n_rows=2, grand_amount_p=0, rows=[dict(_ln("803", 200000, 200000), supplier=""), dict(_ln("802", 200000, 210000), supplier="")]))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: supplier-less BILLITEMWISE lines found their bills by (bill no, date)", not s6["orphans"] and not s6["no_lines"])
ck("synthetic: for 802 the LATER export's lines replaced the earlier ITEMWISE set -- it now AGREES, counted once",
   len(s6["agree"]) == 3 and not s6["differ"] and s6["itemwise_p"] == 600000, "%s %s" % (s6["itemwise_p"], s6["reasons"]))
ck("synthetic: the month can finalise", s6["can_finalise"], str(s6["reasons"]))
# now the CORRECT-verdict path: make 801 differ by Rs 5 through a later ITEMWISE (same period: supersedes the first ITEMWISE)
push(dict(type="ITEMWISE", md5="f" * 32, file="jun_iw2.XLS", period_from="2025-06-01", period_to="2025-06-30", export_stamp="20250703-090000",
          n_rows=1, grand_amount_p=0, rows=[_ln("801", 199500, 220000)]))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: 801 now DIFFERS by Rs 5 and the month is refused, naming 801",
   len(s6["differ"]) == 1 and s6["differ"][0]["bill"]["bill_no"] == "801" and not s6["can_finalise"] and "801" in " ".join(s6["reasons"]))
b801 = q1("SELECT id FROM purchase_bill WHERE bill_no='801' AND month='2025-06'")
cl.post(P + "/api/verdict", json=dict(bill_id=b801, verdict="CORRECT"))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: a DIFFERS bill marked CORRECT no longer blocks -- the month can finalise", s6["can_finalise"], str(s6["reasons"]))
cl.post(P + "/api/verdict", json=dict(bill_id=b801, verdict="WRONG", wrong_amount="1995", reason="rev2 test"))
with app.test_request_context():
    s6 = PA._month_summary(_db(), "2025-06")
ck("synthetic: the same bill marked WRONG blocks again (rule a kept)", not s6["can_finalise"] and any("WRONG" in x for x in s6["reasons"]))
cl.post(P + "/api/verdict", json=dict(bill_id=b801, verdict="CORRECT"))
r = cl.post(P + "/api/finalise", json=dict(month="2025-06"))
ck("synthetic: the doctor finalises; purchase_month stores the NET item-wise total",
   r.status_code == 200 and q("SELECT billwise_total_p, itemwise_total_p FROM purchase_month WHERE month='2025-06'")[0][:] == (600000, 599500))
ck("no page shows a gross figure without the word gross beside it (July gross 508,062 never appears on the hub)", "508,062" not in cl.get(P + "/page/hub").get_data(as_text=True))

# ------------------------------------------------------------- 14. fail closed
as_("", "", set())
r = cl.get(P + "/page/hub")
ck("nobody signed in -> the hub is refused", r.status_code in (401, 302))
as_("stranger", "staff", set())
ck("signed in with no medical role -> refused (403)", cl.get(P + "/page/hub").status_code == 403)
ck("schema was created lazily, never at import (F-303)", PA._schema_done is True)

print("\n%d PASS  %d FAIL" % (len(PASSED), len(FAILED)))
for f in FAILED:
    print("  FAILED: " + f)
sys.exit(1 if FAILED else 0)
