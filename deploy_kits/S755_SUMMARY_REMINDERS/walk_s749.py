#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s749.py -- S749_ONE_SOURCE on a MADE-UP root (no real data): the finance code to test (copied to a temp folder of the walk's own, the
schema beside it), a made-up finance.db and a made-up assets.db with made-up scan files; the portal file read as text.
    python3 -B walk_s749.py <finance code dir to test> <purchase_schema.sql> [<dir holding scan_quality.py>] [<portal.py to test>]
Run on the TO files: every check green.  CONTROL: on the live files (the 08-Nov bundle) every [S749] check goes red.
The last line: 'walk_s749: N check(s) failed (M of them S749 checks)'."""
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import traceback

CODE, SCHEMA = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
SHARED = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.join(os.path.dirname(CODE), "shared")
PORTAL = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else ""
TMP = tempfile.mkdtemp(prefix="s749walk_")
_code = os.path.join(TMP, "code")
os.makedirs(_code)
for _n in os.listdir(CODE):
    if (_n.endswith(".py") or _n.endswith(".json") or _n.endswith(".html")) and os.path.isfile(os.path.join(CODE, _n)):
        shutil.copy(os.path.join(CODE, _n), os.path.join(_code, _n))
shutil.copy(SCHEMA, os.path.join(_code, "purchase_schema.sql"))
CODE = _code
os.environ["SHARED_LIB_DIR"] = SHARED
for k in ("ASSETS_DB", "FINANCE_DB", "ASSETS_UPLOADS"):
    os.environ.pop(k, None)
sys.path.insert(0, CODE)
sys.path.insert(0, SHARED)
import warnings                                               # noqa: E402
warnings.simplefilter("ignore")
FAILS, S749F = [], []


def ck(name, cond, s749=True):
    print(("  ok   " if cond else "  FAIL ") + ("[S749] " if s749 else "") + name)
    if not cond:
        FAILS.append(name)
        if s749:
            S749F.append(name)


def safe(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception:                                         # noqa: BLE001 -- the CONTROL: an absent function is a red check
        print("    (raised: %s)" % traceback.format_exc().strip().splitlines()[-1][:200])
        return None


from flask import Flask, jsonify                              # noqa: E402

import order_sheet as OS                                      # noqa: E402
import porders                                                # noqa: E402
import porders_s454 as P4                                     # noqa: E402
import purchase_app as PA                                     # noqa: E402
import scan_register as SR                                    # noqa: E402
import amir_day as AD                                         # noqa: E402
import month_read as MR                                       # noqa: E402

FDB, ADB = os.path.join(TMP, "finance.db"), os.path.join(TMP, "assets.db")
UP = os.path.join(TMP, "uploads")
os.makedirs(UP)
NOW = OS.now().replace(microsecond=0, tzinfo=None)


def ago(hours=0):
    return (NOW - dt.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")


a = sqlite3.connect(ADB)
a.executescript("""
CREATE TABLE bills (id INTEGER PRIMARY KEY, stamp_no TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, bill_month TEXT, total_amount REAL,
  submitted_at TEXT, created_at TEXT, ocr_status TEXT, dup_of INTEGER, lane TEXT, status TEXT, kind TEXT, page_of INTEGER, rescan_of INTEGER,
  source_stored TEXT, doc_kind TEXT, subgroup TEXT);
CREATE TABLE claude_reading (bill_id INTEGER, data TEXT, ok INTEGER, at TEXT);
CREATE TABLE scan_lie (bill_id INTEGER, file TEXT, at TEXT, legible INTEGER, whole_bill INTEGER, totals_visible INTEGER, blur_kept INTEGER);
CREATE TABLE settings (key TEXT, value TEXT);
""")


def scan(i, vendor, no, total, date, items=None, hours=48):
    at = ago(hours)
    items = items or [dict(name="ITEM %d" % i, quantity=1, rate=total, amount=total)]
    a.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, "
              "source_stored) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (i, "B-%04d" % i, vendor, no, date, date[:7], total, at[:16], at, "read", "pharmacy", "captured", "Pharmacy", "s%d.pdf" % i))
    a.execute("INSERT INTO claude_reading VALUES (?,?,1,?)", (i, json.dumps(dict(bill_no=no, total_amount=total, vendor=vendor, doc_kind="tax_invoice",
                                                                          items=items)), at))
    open(os.path.join(UP, "s%d.pdf" % i), "wb").write(b"%PDF-1.4 made-up scan " + str(i).encode())
    a.commit()


scan(501, "YOGENDRA AGENCIES", "19612", 5861.0, "2026-10-16")            # less: paper typed, Amir's
scan(502, "KEDAR PHARMACEUTICAL", "A000211", 5360.0, "2026-10-15")      # the owner's answer 'You' -> Amir now
scan(503, "SHIVAAZ MEDICOS", "3688", 7979.0, "2026-10-14")             # round-off: paper 7,979 / Marg 7,978
scan(504, "GUNINA PHARMACEUTICALS", "81974", 12972.0, "2026-10-15")    # round-off: 12,972 / 12,973
scan(505, "A.A. PHARMACEUTICALS", "440", 1097.0, "2026-10-01")         # paper matches
scan(506, "OMEGA REMEDIES", "O-77", 2200.5, "2026-10-09")              # 50 paise off: paper matches
scan(507, "DELTA DRUGS", "D-21", 1503.0, "2026-10-11")                 # Rs 3 off, nothing typed: reception's question
scan(508, "SIGMA MEDICOS", "S-80", 640.0, "2026-10-19")                # a misread number; paired to the WRONG bill (S-8) -- the owner: Not this bill
scan(509, "VEGA DISTRIBUTORS", "V-61", 3001.0, "2026-09-12")           # September (parked): the noise band keeps it Verified
scan(510, "TAU PHARMA", "T-5", 4201.0, "2026-10-21")                   # reception typed the paper 4,201 (Marg 4,200: scan_wrong) -- a rupee off: Amir's, never nobody's
os.environ["ASSETS_UPLOADS"] = UP
PA._assets_db = ADB

con = sqlite3.connect(FDB, check_same_thread=False)
con.row_factory = sqlite3.Row
con.executescript(open(SCHEMA).read())
PA._schema_done = False
PA._ensure(con)
PA._ensure_s439(con)
porders.ensure_schema(con)
OS.ensure(con)
for ddl in ("CREATE TABLE IF NOT EXISTS s454_scan_answer (asset_bill_id INTEGER NOT NULL, kind TEXT NOT NULL, answer TEXT, value TEXT, by TEXT,"
            " at TEXT NOT NULL, PRIMARY KEY (asset_bill_id, kind))",
            "CREATE TABLE IF NOT EXISTS s454_paper_missing (bill_id INTEGER PRIMARY KEY, by TEXT, at TEXT NOT NULL, accepted_by TEXT, accepted_at TEXT)",
            "CREATE TABLE IF NOT EXISTS stock_watch_loss_line (id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT, item TEXT, gap_units REAL, pack INTEGER, "
            "packing TEXT, mrp_p INTEGER, point_id INTEGER, void_at TEXT, void_why TEXT)",
            "CREATE TABLE IF NOT EXISTS day_entry (id INTEGER PRIMARY KEY AUTOINCREMENT, unit TEXT, business_date TEXT, status TEXT)"):
    con.execute(ddl)
for k, v in (("purchase.register_from", "2026-10-01"), ("purchase.parked_months", "2026-09"), ("porders.scan_from", "2026-09-01"),
             ("purchase.total_noise_rs", "10"), ("purchase.scan_file_users", "amir"), ("porders.senders", "reception,shavez,darpan"),
             ("purchase.owner_confirm_suppliers", "RAVI MEDICAL AGENCY")):
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?,?)", (k, v))
con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows) VALUES "
            "('e0e0', 'BILLWISE', 'walk.xls', '2026-09-01', '2026-11-30', '20261106-100000', '2026-11-06T10:00:00', 1)")
con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows) VALUES "
            "('i0i0', 'ITEMWISE', 'walki.xls', '2026-10-01', '2026-10-31', '20261106-100000', '2026-11-06T10:00:00', 1)")
BID = {}


def mbill(key, supplier, no, date, rs_):
    cur = con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, first_seen_day) VALUES (?,?,?,?,?,?,?,?)",
                      (PA.supplier_key(supplier), supplier, no, date, date[:7], int(round(rs_ * 100)), "e0e0", date))
    BID[key] = cur.lastrowid
    con.commit()


def mline(supplier, no, date, item, qty, rate, md5="i0i0", undated=False):
    con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, rate_p, discount_pct, tax, amount_p, net_amount_p, "
                "direction, source_md5, line_type) VALUES (?,?,?,?,?,?,?,?,0,0,?,?,'PURCHASE',?,'ITEMWISE')",
                (PA.supplier_key(supplier) if supplier else None, no, None if undated else date, None if undated else date[:7], item, "1*10", qty,
                 int(round(rate * 100)), int(round(qty * rate * 100)), int(round(qty * rate * 100)), md5))
    con.commit()


def link(bk, sid, paper_p=None, state=None, grade="EXACT"):
    con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                (BID[bk], sid, grade, "number + date", "2026-10-25T10:00:00"))
    con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (sid, BID[bk]))
    if paper_p is not None:
        con.execute("INSERT INTO purchase_scan_state (asset_bill_id, why, detail, checked_at, paper_amount, amount_state, confirmed_by, confirmed_at) "
                    "VALUES (?,?,?,?,?,?,?,?)", (sid, "linked", "linked", "2026-10-20T10:00:00", paper_p, state, "reception", "2026-10-20T10:00:00"))
    con.commit()


mbill("yog", "YOGENDRA AGENCIES", "19612", "2026-10-16", 6286)
mbill("ked", "KEDAR PHARMACEUTICAL", "A000211", "2026-10-15", 5470)
mbill("shi", "SHIVAAZ MEDICOS", "3688", "2026-10-14", 7978)
mbill("gun", "GUNINA PHARMACEUTICALS", "81974", "2026-10-15", 12973)
mbill("aa", "A.A. PHARMACEUTICALS", "440", "2026-10-01", 1097)
mbill("om", "OMEGA REMEDIES", "O-77", "2026-10-09", 2200)
mbill("del", "DELTA DRUGS", "D-21", "2026-10-11", 1500)
mbill("sig9", "SIGMA MEDICOS", "S-9", "2026-10-19", 640)                 # the right bill for scan 508 (unscanned at first)
mbill("sig8", "SIGMA MEDICOS", "S-8", "2026-10-12", 640)                 # the wrong bill scan 508 is paired to
mbill("ravi", "RAVI MEDICAL AGENCY", "9012", "2026-10-05", 4710)         # owner-confirmed supplier, no scan
mbill("nos", "NANDI DRUG HOUSE", "555", "2026-10-20", 910)               # an ordinary unscanned bill: reception's
mbill("gcl", "GUNINA PHARMACEUTICALS", "GPPL2678591", "2026-10-05", 2513)    # no dated lines; the item-wise export clipped its number
mbill("kcl", "KEDAR PHARMACEUTICAL", "A000207_", "2026-10-06", 7400)         # no dated lines; the export printed no number
mbill("dbl1", "L.K. DRUG HOUSE", "R-6800", "2026-10-22", 100)              # entered twice in Marg
mbill("dbl2", "L.K. DRUG HOUSE", "r-6800", "2026-10-22", 100)
mbill("veg", "VEGA DISTRIBUTORS", "V-61", "2026-09-12", 3000)              # September, parked
mbill("tau", "TAU PHARMA", "T-5", "2026-10-21", 4200)
mline("A.A. PHARMACEUTICALS", "440", "2026-10-01", "ALPHA TAB", 1, 1097.0)
mline("GUNINA PHARMACEUTICALS", "L2678591", "2026-10-05", "BETA CAP", 1, 2512.71, undated=True)       # clipped: L2678591 ends GPPL2678591
mline("KEDAR PHARMACEUTICAL", None, "2026-10-06", "TYRO BR", 1, 7400.0, undated=True)                 # no number read; the amount names it
mline("STRAY TRADERS", None, "2026-10-06", "STRAY LINE", 1, 999.0, undated=True)                       # fits no bill: stays undated
mbill("omi", "OMICRON DISTRIBUTORS", "X-1", "2026-10-08", 500)                                         # no dated lines; two no-number lines (500 + 300) -- the set fits nothing,
mline("OMICRON DISTRIBUTORS", None, "2026-10-08", "OMI TAB", 1, 500.0, undated=True)                    # and a single line names a bill only by a number: X-1 stays "no item lines"
mline("OMICRON DISTRIBUTORS", None, "2026-10-08", "OMI SYP", 1, 300.0, undated=True)
link("yog", 501, 586100, "marg_wrong")
link("ked", 502, 536000, "owner")
link("shi", 503)
link("gun", 504)
link("aa", 505)
link("om", 506)
link("del", 507)
link("sig8", 508, grade="PROBABLE")
link("veg", 509)
link("tau", 510, 420100, "scan_wrong")
con.commit()

app = Flask("s749walk")
P4.init(app)
LOGIN = {}
porders._auth = lambda: (LOGIN["u"], con, LOGIN["kind"], None)
WHO = {"u": None}


def require_stub(*roles, **kw):
    u = WHO["u"]
    if u is None or not set(u.get("roles") or []).intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return u, None


PA.init(app, lambda: con, require_stub, url_prefix="/finance/purchase", assets_db=ADB)
AD.init(app, lambda: con, require_stub, unit="medical")
porders._db = lambda: con
OS.book_card = lambda con_, vendor: ("", "", False, False)
cl = app.test_client()
OWNER = dict(user="manoj", username="manoj", login="manoj", role="checker", roles=["checker"])
SHAVEZ = dict(user="shavez", username="shavez", login="shavez", role="maker", roles=["maker"])
AMIR = dict(user="amir", username="amir", login="amir", role="viewer", roles=["viewer"])
RECEP = dict(user="reception", login="reception", roles=["maker"])


def as_(u, kind=None):
    WHO["u"] = u
    LOGIN["u"], LOGIN["kind"] = u, kind


def get(path):
    r = cl.get(path, follow_redirects=True)
    return r.status_code, r.get_data(as_text=True)


def post(path, body):
    r = cl.post(path, data=json.dumps(body), content_type="application/json")
    try:
        return r.status_code, r.get_json() or {}
    except Exception:                                         # noqa: BLE001
        return r.status_code, {}


def reg(month="2026-10"):
    getattr(SR, "_S740_MEMO", {}).clear()
    return safe(SR.register, con, month) or {"rows": [], "counts": {}}


def row_of(key, month="2026-10"):
    return next((x for x in reg(month)["rows"] if x["id"] == BID[key]), {})


def between(h, a, b):
    i = h.find(a)
    if i < 0:
        return ""
    j = h.find(b, i + len(a))
    return h[i:j if j > 0 else len(h)]


as_(OWNER, "checker")
print("1 · the register in his words (one source)")
r = reg()
ck("1 the register reads", bool(r["rows"]), s749=False)
ck("1 the words: STATE_EN says 'Paper matches' for verified AND has_scan, 'Difference → Amir' for amount_differs; 'has its scan' is gone",
   getattr(SR, "STATE_EN", {}).get("verified") == "Paper matches" and getattr(SR, "STATE_EN", {}).get("has_scan") == "Paper matches"
   and getattr(SR, "STATE_EN", {}).get("amount_differs") == "Difference → Amir" and "Has its scan" not in getattr(SR, "STATE_EN", {}).values())
ck("1 A.A. 440 (paper = Marg): Paper matches", row_of("aa").get("state") == "verified", s749=False)
ck("1 Omega O-77 (50 paise off): Paper matches -- paise never hold a bill", row_of("om").get("state") in ("verified", "has_scan"), s749=False)
sh = row_of("shi")
ck("1 Shivaaz 3688 (7,979 / 7,978): a DIFFERENCE, Amir's, a round-off (never 'rounding -- supplier's figure paid')",
   sh.get("state") == "amount_differs" and str(sh.get("whose") or "").startswith("Amir") and sh.get("s749") == "roundoff"
   and "supplier's figure paid" not in (sh.get("note") or "") and "Round-off" in (sh.get("note") or ""))
ck("1 Gunina 81974 (12,972 / 12,973): the same", row_of("gun").get("state") == "amount_differs" and str(row_of("gun").get("whose") or "").startswith("Amir"))
kd = row_of("ked")
ck("1 Kedar A000211 ('You' with Shavez, 22-Oct): now Amir's -- the You state is gone", kd.get("state") == "amount_differs" and kd.get("whose") == "Amir: a Marg correction")
ck("1 Yogendra 19612 (paper typed, less): Amir's, as before", row_of("yog").get("whose") == "Amir: a Marg correction", s749=False)
tu = row_of("tau")
ck("1 Tau T-5 (reception typed 4,201 against Marg 4,200 -- 'scan_wrong'): a difference is never nobody's -- Amir's, a round-off", tu.get("state") == "amount_differs"
   and tu.get("whose") == "Amir: a Marg correction" and tu.get("s749") == "roundoff")
dl = row_of("del")
ck("1 Delta D-21 (Rs 3 off, nothing typed): a difference, reception confirms the paper's figure first", dl.get("state") == "amount_differs"
   and str(dl.get("whose") or "").startswith("Reception"), s749=False)
rv = row_of("ravi")
ck("1 Ravi 9012 (owner-confirmed supplier, no scan): state 'confirm', whose 'You: confirm' -- never 'no scan'", rv.get("state") == "confirm" and rv.get("whose") == "You: confirm")
ck("1 Nandi 555 (an ordinary bill, no scan): No scan, reception's", row_of("nos").get("state") == "no_scan" and str(row_of("nos").get("whose") or "").startswith("Reception"), s749=False)
ck("1 the counts carry 'confirm' and the settled count reads Paper matches + accepted + confirmed", "confirm" in r["counts"] and r.get("settled") == r["counts"]["verified"] + r["counts"]["has_scan"] + r["counts"]["accepted"] + r["counts"]["confirmed"])
ck("1 no build or decision number in any note or whose line", not any(re.search(r"\b(S\d{3}|D\d{3}|F-\d{3,4})\b", "%s %s" % (x.get("note"), x.get("whose"))) for x in r["rows"]), s749=False)
vg = row_of("veg", "2026-09")
ck("1 September (parked) keeps the noise band: Vega 61 stays Paper matches, the rupee shown", vg.get("state") == "verified" and "rounding" in (vg.get("note") or ""), s749=False)
ck("1 porders: a round-off asks reception nothing; Rs 3 does; a parked month keeps its band",
   not porders._s440_differs(797900, 797800, "2026-10") and porders._s440_differs(150300, 150000, "2026-10") and not porders._s440_differs(300100, 300000, "2026-09")
   and hasattr(SR, "s749_reception_asks"))
fx = {f["bill_id"]: f for f in (safe(SR.s738_fixes, con) or [])}
ck("1 Amir's list (s738_fixes): Yogendra, Kedar A000211, Shivaaz (roundoff), Gunina (roundoff), the double -- never Delta (reception first)",
   {BID["yog"], BID["ked"], BID["shi"], BID["gun"], BID["tau"]} <= set(fx) and BID["del"] not in fx and (fx.get(BID["shi"]) or {}).get("kind") == "roundoff"
   and (fx.get(BID["gun"]) or {}).get("kind") == "roundoff" and (fx.get(BID["ked"]) or {}).get("kind") == "less")

print("2 · reception's list and Amir's card")
un = safe(porders.unscanned_bills, con) or []
ck("2 Ravi 9012 is NOT on reception's Scan karo; Nandi 555 is", BID["ravi"] not in {x["bill_id"] for x in un} and BID["nos"] in {x["bill_id"] for x in un})
as_(RECEP, "sender")
st, h = get("/finance/porders/s454/scan")
ck("2 reception's own screen 'Bill scan karna hai' (200)", st == 200, s749=False)
ck("2 ... Ravi 9012 is not on it; Nandi 555 is", "RAVI MEDICAL" not in h and "NANDI DRUG HOUSE" in h and "555" in h)
ck("2 the owner's Needs-you no longer carries 'Scan amount to settle' for the old You state", safe(porders._s440_owner_lines, con) == [])
as_(AMIR)
st, h = get("/finance/amir/step/1")
ck("2 Amir's page answers (200)", st == 200, s749=False)
ck("2 the round-off card: 'Marg mein bill ₹7,979 kijiye (round-off)' and 'Marg mein bill ₹12,972 kijiye (round-off)'",
   "Marg mein bill &#8377;7,979 kijiye (round&#8209;off)" in h and "Marg mein bill &#8377;12,972 kijiye (round&#8209;off)" in h)
ck("2 Kedar A000211 on his card: 'Marg mein bill ₹5,360 kijiye'", "Marg mein bill &#8377;5,360 kijiye" in h)
ck("2 the card's count carries the round-offs (5 corrections + the double = 6)", "Purchase bill Marg mein theek karein &middot; 6" in h)
as_(OWNER, "checker")
st, h = get("/finance/amir/day")
ck("2 the owner's English summary answers (200)", st == 200, s749=False)
ck("2 ... reads his list: 'Marg sudhar: 5 bills to correct (… Shivaaz Medicos 3688 …)', 'Wapsi baaki', 'Proved by his exports'",
   'id=s749amir' in h and "Marg sudhar: <b>6</b> bill" in h and "Shivaaz Medicos 3688" in h and "Wapsi baaki" in h and "Proved by his exports" in h)

print("3 · the step view: eight rows, one language, everything inline")
st, h = get("/finance/purchase/page/check?month=2026-10")
ck("3 the step view answers (200)", st == 200, s749=False)
labs = re.findall(r'<details class="(?:row|grey)[^"]*" data-row="(\d)"[^>]*><summary><span class="l"><b>\d</b> ([^<]+)<span class="s749sub">', h)
ck("3 the eight rows in order: Paper matches · Differences → Amir · Confirm — yours · With reception · You & Shavez · Returns · Dealer summaries · Lock & NEFT",
   [x[1] for x in labs] == ["Paper matches", "Differences → Amir", "Confirm — yours", "With reception", "You &amp; Shavez", "Returns", "Dealer summaries", "Lock &amp; NEFT"])
ck("3 gone from his page: 'Has its scan', 'Rounding (supplier', 'Scans paired', 'D839', 'S740 seed', the read-quality block",
   "Has its scan" not in h and "Rounding (supplier" not in h and "Scans paired" not in h and "D839" not in h and "S740 seed" not in h and "How well the scan reads" not in h)
ck("3 the month strip (Oct filled, Sep parked)", 's749strip' in h and 'class="s749m on"' in h and 'class="s749m park"' in h)
r1 = between(h, 'data-row="1"', 'data-row="2"')
ck("3 row 1: '3 / 16' (A.A., Omega, Sigma S-8 as it stands; the double is one row; Vega is September) and 'Nothing to do here'",
   '<span class="n">3 / 16</span>' in r1 and "Nothing to do here" in r1)
r2 = between(h, 'data-row="2"', 'data-row="3"')
ck("3 row 2 'Differences → Amir' counts 6 (Yogendra, Kedar, Shivaaz, Gunina, Tau, the double)", '<span class="n">6</span>' in r2 and "Differences → Amir" in r2)
ck("3 ... Shivaaz: 'paper ₹7,979 · Marg ₹7,978 · round-off' and 'Next: Marg bill → ₹7,979 (round-off). Proved by his export.'",
   "paper ₹7,979 · Marg ₹7,978 · round&#8209;off" in r2 and "Next: Marg bill → ₹7,979 (round-off). Proved by his export." in r2)
ck("3 ... Kedar A000211 carries 'Amir' (no 'You')", "KEDAR PHARMACEUTICAL A000211" in r2 and "<span class=\"c5\">You" not in r2)
ck("3 ... every line carries its scan folded ('Show scan') and the inline actions 'Not this bill' and 'Ask reception to rescan'",
   r2.count("Show scan") >= 4 and r2.count(">Not this bill<") >= 4 and r2.count(">Ask reception to rescan<") >= 4)
r3 = between(h, 'data-row="3"', 'data-row="4"')
ck("3 row 3 'Confirm — yours': Ravi 9012 · ₹4,710 with 'Confirm' and 'Ask reception for the paper'; the suppliers named",
   '<span class="n">1</span>' in r3 and "RAVI MEDICAL AGENCY 9012" in r3 and ">Confirm<" in r3 and ">Ask reception for the paper<" in r3 and "Ravi Medical Agency" in r3)
r4 = between(h, 'data-row="4"', 'data-row="5"')
ck("3 row 4 'With reception': Nandi 555, Sigma S-9 and Omicron X-1 'to scan', the two clipped bills, Delta D-21 'the paper's figure to confirm' (6); the register and the audit say the same of Delta", "NANDI DRUG HOUSE 555" in r4 and row_of("del") and "reception confirms the figure" in (safe(SR.s749_word, row_of("del")) or "")
   and "DELTA DRUGS D-21" in r4 and "SIGMA MEDICOS S-9" in r4 and "to scan" in r4 and "the paper's figure to confirm" in r4 and '<span class="n">6</span>' in r4)
ck("3 row 4: the Sigma S-8 pair (the wrong one) is not reception's -- it is Paper matches until the owner says otherwise", "SIGMA MEDICOS S-8" not in r4, s749=False)
r8 = between(h, '<details class="row last" data-row="8"', "</details>")
ck("3 row 8 'Lock & NEFT': 'Holding: 6 differences · 1 to confirm · 6 with reception' and Marg's reports named", "Holding: 6 differences · 1 to confirm · 6 with reception" in r8
   and "Marg&#x27;s month-end reports: supplier-wise — not yet" in r8)
ck("3 the strip: 'NEFT on hold · 13 open'", 'id="s726strip">NEFT on hold · 13 open</div>' in h)
ck("3 the way out: the register, the audit, the payment sheet, reception's list -- in one line", "the register</a>" in h and "the purchase audit</a>" in h and "the payment sheet</a>" in h)
st, hs = get("/finance/purchase/page/check?month=2026-09")
ck("3 September's step view: read only, 'All clear' (nobody is asked)", st == 200 and "is parked: shown for reading only" in hs and 'id="s726strip">All clear' in hs, s749=False)
n0 = con.execute("SELECT COUNT(*) FROM purchase_audit").fetchone()[0]
get("/finance/purchase/page/check?month=2026-10")
ck("3 the GET wrote nothing", con.execute("SELECT COUNT(*) FROM purchase_audit").fetchone()[0] == n0, s749=False)

print("4 · Confirm (yours)")
as_(SHAVEZ)
st, j = post("/finance/purchase/api/s749/confirm", dict(bill=BID["ravi"], decision="confirm"))
ck("4 Shavez cannot confirm (403)", st == 403)
as_(OWNER, "checker")
st, j = post("/finance/purchase/api/s749/confirm", dict(bill=BID["nos"], decision="confirm"))
ck("4 an ordinary supplier's bill is refused (409: not settled by you)", st == 409)
st, j = post("/finance/purchase/api/s749/confirm", dict(bill=BID["ravi"], decision="confirm"))
ck("4 Ravi 9012 confirmed (200)", st == 200 and j.get("ok"))
rv = row_of("ravi")
ck("4 ... the register: state 'confirmed', settled, whose Nobody, 'Confirmed by you on …'", rv.get("state") == "confirmed" and rv.get("whose") == "Nobody" and "Confirmed by you on" in (rv.get("note") or "")
   and reg()["settled"] == 4)
ck("4 ... audited (s749_confirm)", con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s749_confirm'").fetchone()[0] == 1)
st, h = get("/finance/purchase/page/check?month=2026-10")
ck("4 ... the step view: row 3 empty, row 1 carries Ravi 'confirmed by you' with Undo, the strip 7 open", '<span class="n">0</span>' in between(h, 'data-row="3"', 'data-row="4"')
   and "confirmed by you" in between(h, 'data-row="1"', 'data-row="2"') and 'NEFT on hold · 12 open' in h)
st, j = post("/finance/purchase/api/s749/confirm", dict(bill=BID["ravi"], decision="undo"))
ck("4 Undo (200) -> 'confirm' again", st == 200 and row_of("ravi").get("state") == "confirm")
st, j = post("/finance/purchase/api/s749/confirm", dict(bill=BID["ravi"], decision="scan"))
un = safe(porders.unscanned_bills, con) or []
ck("4 'Ask reception for the paper': Ravi 9012 is back on reception's Scan karo, 'No scan' on the register", st == 200 and BID["ravi"] in {x["bill_id"] for x in un}
   and row_of("ravi").get("state") == "no_scan" and "You asked reception for this paper" in (row_of("ravi").get("note") or ""))
post("/finance/purchase/api/s749/confirm", dict(bill=BID["ravi"], decision="undo"))
ck("4 ... undone: 'confirm' again, off reception's list", row_of("ravi").get("state") == "confirm" and BID["ravi"] not in {x["bill_id"] for x in (safe(porders.unscanned_bills, con) or [])})

print("5 · Not this bill → pick the right bill (the owner's re-pair, audited, Undo)")
st, j = post("/finance/purchase/api/s749/unpair", dict(scan=508, bill=BID["sig8"]))
ck("5 scan B-0508 unpaired from Sigma S-8 (200)", st == 200 and j.get("ok"))
ck("5 ... the link is gone, the bill's scan_bill_id cleared, hint_no carries S-8 (the matcher never pairs them again), audited (s749_unpaired)",
   con.execute("SELECT COUNT(*) FROM purchase_scan_link WHERE asset_bill_id=508").fetchone()[0] == 0
   and con.execute("SELECT scan_bill_id FROM purchase_bill WHERE id=?", (BID["sig8"],)).fetchone()[0] is None
   and str(BID["sig8"]) in str(con.execute("SELECT hint_no FROM purchase_scan_state WHERE asset_bill_id=508").fetchone()[0] or "")
   and con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s749_unpaired'").fetchone()[0] == 1)
st, hp = get("/finance/purchase/api/s749/pick?scan=508")
opts = {}
try:
    opts = {o["id"]: o for o in (json.loads(hp).get("options") or [])}
except Exception:                                             # noqa: BLE001
    pass
ck("5 the pick list offers Sigma's unscanned bills (S-9 and S-8), the supplier's own first; never a paired bill", BID["sig9"] in opts and BID["sig8"] in opts and BID["aa"] not in opts
   and bool(opts) and list(opts.values())[0]["same"])
st, j = post("/finance/purchase/api/s749/pair", dict(scan=508, bill=BID["aa"]))
ck("5 pairing with a bill that has its scan is refused (409)", st == 409)
st, j = post("/finance/purchase/api/s749/pair", dict(scan=508, bill=BID["sig9"]))
ck("5 paired with Sigma S-9 (200): grade CONFIRMED 'the owner picked it', audited (scan_link), Paper matches", st == 200
   and tuple(con.execute("SELECT grade, matched_on FROM purchase_scan_link WHERE asset_bill_id=508").fetchone()) == ("CONFIRMED", "the owner picked it")
   and row_of("sig9").get("state") in ("verified", "has_scan"))
try:
    acts = con.execute("SELECT id, kind, undone_at FROM s749_act ORDER BY id").fetchall()
except sqlite3.Error:
    acts = [(0, "", None), (0, "", None)]
ck("5 two acts kept (unpair, pair), both open", [a[1] for a in acts] == ["unpair", "pair"] and all(a[2] is None for a in acts))
st, h = get("/finance/purchase/page/check?month=2026-10")
ck("5 the step view's 'Decided' lists both with Undo", "unpaired from scan 508" in h and "paired by you with scan 508" in h)
st, j = post("/finance/purchase/api/s749/undo", dict(act=acts[0][0]))
ck("5 undoing the unpair while the scan is paired elsewhere is refused (409)", st == 409)
st, j = post("/finance/purchase/api/s749/undo", dict(act=acts[1][0]))
ck("5 undo the pair (200): the link gone", st == 200 and con.execute("SELECT COUNT(*) FROM purchase_scan_link WHERE asset_bill_id=508").fetchone()[0] == 0)
st, j = post("/finance/purchase/api/s749/undo", dict(act=acts[0][0]))
ck("5 undo the unpair (200): the old pair back as it was (PROBABLE), hint_no cleared", st == 200
   and (con.execute("SELECT grade FROM purchase_scan_link WHERE asset_bill_id=508").fetchone() or [None])[0] == "PROBABLE"
   and str(BID["sig8"]) not in str(con.execute("SELECT hint_no FROM purchase_scan_state WHERE asset_bill_id=508").fetchone()[0] or ""))
st, j = post("/finance/purchase/api/s749/unpair", dict(scan=501, bill=BID["ked"]))
ck("5 a scan not paired with that bill is refused (409)", st == 409)
as_(SHAVEZ)
st, j = post("/finance/purchase/api/s749/unpair", dict(scan=508, bill=BID["sig8"]))
ck("5 Shavez cannot unpair (403)", st == 403)
as_(OWNER, "checker")

print("6 · the clipped item-wise numbers (F-1181), the one gate, the audit page, the hub, the payment sheet")
s = safe(PA._month_summary, con, "2026-10") or {}
nl = {b["id"] for b in s.get("no_lines") or []}
ck("6 _month_summary: Gunina GPPL2678591 (lines under 'L2678591', ₹2,512.71) and Kedar A000207_ (no number, ₹7,400 -- one line of two) have their lines and agree",
   bool(s) and BID["gcl"] not in nl and BID["kcl"] not in nl and {BID["gcl"], BID["kcl"]} <= {b["id"] for b in s.get("agree") or []})
ck("6 ... the stray line (₹999, fits no bill) and Omicron's two lines stay undated (3); the matched lines left the undated list", len(s.get("undated") or []) == 3 if s else False)
ck("6 ... a single no-number line (Omicron 500 of 500 + 300) never names a bill by its amount alone: X-1 stays on 'no item lines'", bool(s) and BID["omi"] in nl, s749=False)
ck("6 ... the clipped set is the bill's set (_bill_lines: 1 line, ₹2,512.71)", bool(s) and (PA._bill_lines(next(b for b in s["bills"] if b["id"] == BID["gcl"]), s["sets"], s["stray"]) or {}).get("net_p") == 251271)
gate = safe(PA._lock_gate, con, "2026-10", s) if s else None
ck("6 the one gate holds on the register's rows: 'the purchase check holds: 5 differences → Amir …', '… 1 bill to confirm …', '… 2 with reception …'",
   bool(gate) and not gate[0] and any("6 differences → Amir" in x for x in gate[1]) and any("1 bill to confirm" in x for x in gate[1]) and any("6 with reception" in x for x in gate[1]))
st, h = get("/finance/purchase/page/month/2026-10")
ck("6 the audit page answers (200)", st == 200, s749=False)
ck("6 ... the register's state column: 'Paper matches', 'Difference → Amir', 'Confirm (yours)', 'No scan'; and 'Next · whose'",
   "<th>Purchase check</th>" in h and "<b>Paper matches</b>" in h and "<b>Difference → Amir</b>" in h and "<b>Confirm (yours)</b>" in h and "<b>No scan</b>" in h
   and "Next: Marg bill → ₹7,979 (round-off)" in h)
ck("6 ... no Correct / Wrong buttons on the doctor's view; the month strip", "onclick=\"verdict(" not in h and 's749strip' in h)
ck("6 ... the 4 'no item lines' are closed: Gunina GPPL2678591 agrees with 1 line", "GPPL2678591</td><td class=\"n\">₹2,513</td><td class=\"n\">₹2,513</td>" in h.replace("₹", "₹"))
con.execute("UPDATE purchase_bill SET amount_p=150000, bw_amount_p=150000 WHERE id=?", (BID["del"],))
con.commit()
as_(SHAVEZ)
st, h2 = get("/finance/purchase/page/month/2026-10")
ck("6 ... a maker (Shavez) still sees the page (200); his buttons, where any, are not the doctor's", st == 200, s749=False)
as_(OWNER, "checker")
st, h = get("/finance/purchase/page/hub")
ck("6 the hub answers (200)", st == 200, s749=False)
ck("6 ... a 'Purchase check' column with the register's words for October (… 6 differences → Amir · 1 to confirm · 6 with reception …) linking to the step view",
   "<th>Purchase check</th>" in h and "6 differences → Amir · 1 to confirm · 6 with reception" in h and "/finance/purchase/page/check?month=2026-10" in h)
ck("6 ... the scan card counts counted months only: no 'Marg bills with no scan' all-time line; 'Counted months only (from October 2026)'",
   "Marg bills with no scan" not in h and "Counted months only (from October 2026)" in h)
st, h = get("/finance/purchase/page/pay/2026-10")
ck("6 the payment sheet answers (200)", st == 200, s749=False)
ck("6 ... no 'Check it now' tap; Step 2 waits for the statement by itself; Step 3 lists the gate's holds incl. the purchase check; the month strip",
   "Check it now" not in h and "Waiting for Marg's supplier-wise statement" in h and "the purchase check holds: 6 differences → Amir" in h and 's749strip' in h)
con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p) VALUES "
            "('s0s0', 'SUPPLIERWISE', 'walks.xls', '2026-10-01', '2026-10-31', '20261106-110000', '2026-11-06T11:00:00', 15, ?)",
            (sum(int(b["amount_p"]) for b in con.execute("SELECT amount_p FROM purchase_bill WHERE month='2026-10'")),))
con.execute("UPDATE purchase_bill SET sw_md5='s0s0', sw_amount_p=amount_p WHERE month='2026-10'")
con.commit()
st, h = get("/finance/purchase/page/pay/2026-10")
chk = con.execute("SELECT who, ok FROM purchase_pay_check WHERE month='2026-10' ORDER BY id DESC LIMIT 1").fetchone()
ck("6 ... the statement arrives: Step 2 run by the server ('Verified against Marg's supplier-wise statement', kept once, who 'server')",
   "Verified against Marg's supplier-wise statement" in h and bool(chk) and chk[0] == "server" and chk[1] == 1
   and con.execute("SELECT COUNT(*) FROM purchase_pay_check WHERE month='2026-10'").fetchone()[0] == 1)
get("/finance/purchase/page/pay/2026-10")
ck("6 ... a second read keeps no second row", con.execute("SELECT COUNT(*) FROM purchase_pay_check WHERE month='2026-10'").fetchone()[0] == 1)

print("7 · the register page (the full list), the console month line, the tile")
st, h = get("/finance/purchase/page/scans?month=2026-10")
ck("7 the register page answers (200)", st == 200, s749=False)
ck("7 ... the same words: 'Paper matches', 'Difference → Amir', 'Confirm (yours)'; the month strip; the read quality folded; no 'verified'/'has its scan' chips",
   ">Paper matches<" in h and ">Difference → Amir<" in h and ">Confirm (yours)<" in h and 's749strip' in h and "<details class=\"card\" id=\"s454sarvam\">" in h
   and "has its scan" not in h.lower())
ck("7 ... one line per bill with Marg and paper: 'SHIVAAZ MEDICOS · 3688 · Marg ₹7,978 · paper ₹7,979'", "SHIVAAZ MEDICOS · 3688 · Marg ₹7,978 · paper ₹7,979" in h)
env = dict(assets=ADB, register=FDB)
g = safe(MR.g_sanjeevni, con, env, "2026-10", NOW.date(), "ended", [])
texts = [x.get("text") or "" for x in (g or {}).get("rows") or []]
ck("7 the console month page, Sanjeevni group: 'Purchase check — October · 3 paper matches · 6 differences → Amir · 1 to confirm · 6 with reception · NEFT on hold' -> the step view",
   any(t.startswith("Purchase check — October · 3 paper matches · 6 differences → Amir · 1 to confirm · 6 with reception") and t.endswith("NEFT on hold") for t in texts)
   and any((x.get("href") or "") == "/finance/purchase/page/check?month=2026-10" for x in (g or {}).get("rows") or []))
o = safe(MR.others, con, env, "2026-10", NOW.date(), "ended", [])
ck("7 ... 'Pharmacy bills scanned' opens the register for THAT month", any(x.get("k") == "Pharmacy bills scanned" and x.get("href") == "/finance/purchase/page/scans?month=2026-10"
                                                                         for x in (o or {}).get("rows") or []))
if PORTAL:
    pt = open(PORTAL, encoding="utf-8").read()
    ck("7 the Marg Purchases tile opens the step view (/finance/purchase/page/check), not the hub", '"url": "/finance/purchase/page/check"' in pt
       and '"name": "Marg Purchases"' in pt and pt.count('"url": "/finance/purchase/page/hub"') == 0)

print("walk_s749: %d check(s) failed (%d of them S749 checks)" % (len(FAILS), len(S749F)))
shutil.rmtree(TMP, ignore_errors=True)
