#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s750.py -- S750_MONTH_END (its fixture is S749's walk's, extended) on a MADE-UP root (no real data): the finance code to test (copied to a temp folder of the walk's own, the
schema beside it), a made-up finance.db and a made-up assets.db with made-up scan files; the portal file read as text.
    python3 -B walk_s750.py <finance code dir to test> <purchase_schema.sql> [<dir holding scan_quality.py>] [<portal.py to test>]
Run on the TO files: every check green.  CONTROL: on the live files (the 08-Nov bundle) every [S750] check goes red.
The last line: 'walk_s750: N check(s) failed (M of them S750 checks)'."""
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
TMP = tempfile.mkdtemp(prefix="s750walk_")
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
FAILS, S750F = [], []


def ck(name, cond, s750=True):
    print(("  ok   " if cond else "  FAIL ") + ("[S750] " if s750 else "") + name)
    if not cond:
        FAILS.append(name)
        if s750:
            S750F.append(name)


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



# ====================================================================================================================================
#  S750 fixture: the dealers' summaries of October (made-up), a Marg purchase return, item lines, and a carried amount into November
# ====================================================================================================================================
mline("SHIVAAZ MEDICOS", "3688", "2026-10-14", "GAMMA TAB", 10, 797.80)
mline("YOGENDRA AGENCIES", "19612", "2026-10-16", "DELTA SYP", 2, 3143.0)
mline("YOGENDRA AGENCIES", "19612", "2026-10-16", "DELTA SYP", 0, 0.0)          # a free line
mbill("yret", "YOGENDRA AGENCIES", "PR-7", "2026-10-28", -286)                   # Marg's own purchase return (a minus bill)
mbill("bass1", "BASS MEDICAL STORE", "A017450", "2026-10-11", 1500)
mbill("bass2", "BASS MEDICAL STORE", "A017456", "2026-10-25", 1597)
mbill("dee1", "DEEPAM PHARMA", "641", "2026-10-03", 4751)
mbill("dee2", "DEEPAM PHARMA", "702", "2026-10-21", 3230)
mbill("nov1", "BASS MEDICAL STORE", "A017470", "2026-11-04", 900)                # November: the carry lands here
con.commit()


def summary(i, vendor, month_to, lines, total=None, closing=None, read=True, hours=20, dealer=None, is_summary=True, bill_prompt=False):
    """A dealer's month summary scanned under Pharmacy with the 'summary' tick (kind 'Summary') and its reading (doc_kind 'summary')."""
    at = ago(hours)
    a.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, doc_kind, "
              "source_stored) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (i, "B-%04d" % i, vendor, None, None, month_to[:7], total, at[:16], at, "read" if read else "failed", "pharmacy", "captured", "Summary", "summary", "s%d.pdf" % i))
    if read:
        data = dict(doc_kind="summary", is_summary=is_summary, dealer=dealer if dealer is not None else vendor, period_from=month_to[:7] + "-01", period_to=month_to,
                    lines=[dict(kind=k, no=n, date=d_, amount=amt) for k, n, d_, amt in lines], total_bills=total, closing=closing, opening=None, handwritten=False)
        if bill_prompt:
            data = dict(doc_kind="tax_invoice", vendor=vendor, bill_no=None, total_amount=total, items=[])
        a.execute("INSERT INTO claude_reading (bill_id, data, ok, at) VALUES (?,?,1,?)", (i, json.dumps(data), at))
    else:
        a.execute("INSERT INTO claude_reading (bill_id, data, ok, at) VALUES (?,?,0,?)", (i, None, at))
    open(os.path.join(UP, "s%d.pdf" % i), "wb").write(b"%PDF-1.4 made-up summary " + str(i).encode())
    a.commit()


a.execute("ALTER TABLE claude_reading ADD COLUMN doc_kind TEXT")
a.execute("ALTER TABLE claude_reading ADD COLUMN error TEXT")
a.execute("ALTER TABLE claude_reading ADD COLUMN model TEXT")
a.commit()
summary(601, "SHIVAAZ MEDICOS", "2026-10-31", [("bill", "3688", "2026-10-14", 7978.0)], total=7978.0, closing=7978.0)                  # agrees
summary(602, "YOGENDRA AGENCIES", "2026-10-31", [("bill", "19612", "2026-10-16", 6286.0), ("credit", "CN-7", "2026-10-28", 286.0)], total=6286.0, closing=6000.0)   # agrees via Marg's return
summary(603, "BASS MEDICAL STORE", "2026-10-31", [("bill", "A017450", "2026-10-11", 1500.0), ("bill", "A017456", "2026-10-25", 1597.0),
                                                   ("bill", "A017460", "2026-10-28", 2140.0)], total=5237.0, closing=5237.0)             # a bill we do not have: HIS
summary(604, "", "2026-10-31", [("bill", "Z-1", "2026-10-02", 100.0)], total=100.0, dealer="ZETA PHARMA UNKNOWN")                          # no dealer of the month: pick
summary(605, "KEDAR PHARMACEUTICAL", "2026-10-31", [], read=False)                                                                       # could not be read
a.execute("UPDATE claude_reading SET doc_kind='summary' WHERE bill_id IN (601,602,603,604)")
a.execute("UPDATE claude_reading SET error='no answer' WHERE bill_id=605")
a.commit()
# Deepam: no summary at all -> awaited.  Gunina, A.A., Omega, Delta, Sigma, Nandi, L.K., Tau, Omicron: awaited too (the walk marks two as 'gives no summary').


def G(o, *ks, default=None):
    """A safe dig for the CONTROL: a missing key or an absent function is a red check, never a crash."""
    try:
        for k in ks:
            o = o[k]
        return o
    except Exception:                                         # noqa: BLE001
        return default


def rows7(month="2026-10"):
    st, h = get("/finance/purchase/page/check?month=%s" % month)
    return st, h, between(h, 'data-row="7">', 'data-row="8">'), between(h, 'data-row="8">', "</details>")


as_(OWNER, "checker")
print("1 · the summaries read (assets.db READ ONLY) and the dealers of October")
scans = safe(getattr(SR, "s750_summary_scans", None), con)
ck("1 five summary scans read, kind 'Summary' only -- never a Pharmacy bill scan", scans is not None and set(scans) == {601, 602, 603, 604, 605})
ck("1 the month comes from the period's last day (601 -> 2026-10); the figure = bills less credits (602: 6,286 - 286 = 6,000)",
   scans is not None and scans[601]["month"] == "2026-10" and scans[602]["figure_p"] == 600000 and scans[601]["figure_p"] == 797800)
ck("1 an unread summary says so (605: 'no answer')", scans is not None and not scans[605]["read"] and "no answer" in scans[605]["read_error"])
ds = {d["key"] or "?": d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-10") or [])}
ck("1 every dealer of October is on the list (12 with bills + the unknown summary)", len(ds) >= 12 and "?" in ds)
ck("1 Shivaaz: agrees (7,978 = 7,978)", ds.get(PA.supplier_key("SHIVAAZ MEDICOS"), {}).get("state") == "agrees")
yg = ds.get(PA.supplier_key("YOGENDRA AGENCIES"), {})
ck("1 Yogendra: agrees -- the credit note on the summary is Marg's own purchase return PR-7 (net 6,000)", yg.get("state") == "agrees" and yg.get("net_p") == 600000 and yg.get("returns_p") == 28600)
bs = ds.get(PA.supplier_key("BASS MEDICAL STORE"), {})
ck("1 Bass: differs by 2,140 -- bill A017460 on the summary, not in Marg, no paper: HIS (unexplained, holds)",
   bs.get("state") == "differs" and bs.get("diff_p") == 214000 and not bs.get("explained") and bs.get("holds") and any(i["kind"] == "on_summary" and i["no"] == "A017460" for i in bs.get("issues", [])))
ck("1 Deepam: awaited (holds)", ds.get(PA.supplier_key("DEEPAM PHARMA"), {}).get("state") == "awaited" and G(ds, PA.supplier_key("DEEPAM PHARMA"), "holds"))
ck("1 Kedar: unreadable (holds; a rescan is the next step)", ds.get(PA.supplier_key("KEDAR PHARMACEUTICAL"), {}).get("state") == "unreadable")
ck("1 Ravi (owner-confirmed): 'confirm' -- his Confirm counts as the summary; never awaited", ds.get(PA.supplier_key("RAVI MEDICAL AGENCY"), {}).get("state") == "confirm")
ck("1 the unknown summary (Zeta): state 'unknown', holds", ds.get("?", {}).get("state") == "unknown" and G(ds, "?", "holds"))
op = safe(getattr(SR, "s750_open", None), con, "2026-10") or {}
ck("1 s750_open counts: 2 agree · 1 differ · awaited >= 9 · 2 unread (Kedar, Zeta)", op.get("agree") == 2 and op.get("differ") == 1 and op.get("awaited", 0) >= 9 and op.get("unread") == 2)
mo = safe(SR.s749_month_open, con, "2026-10") or {}
ck("1 s749_month_open keeps its keys and gains 'dealers'; open counts them; the words say so", all(k in mo for k in ("match", "amir", "confirm", "reception", "you", "returns", "open", "words", "neft"))
   and mo.get("dealers") == op.get("n") and "dealer summar" in (mo.get("words") or "") and mo.get("neft") == "NEFT on hold")
lr = safe(SR.s749_lock_reasons, con, "2026-10") or []
ck("1 s749_lock_reasons carries the dealers' holds (differ, awaited, unread)", any("differ" in x for x in lr) and any("awaited" in x for x in lr) and any("could not be read or named" in x for x in lr))
opn = safe(getattr(SR, "s750_open", None), con, "2026-11") or {}
dsn = {d["key"] or "?": d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-11") or [])}
ck("1 November (the running month): no dealer is awaited and nothing holds -- 'Month running' until the month ends (the owner, 11:30)",
   opn.get("awaited") == 0 and opn.get("n") == 0 and opn.get("running", 0) >= 1 and G(dsn, PA.supplier_key("BASS MEDICAL STORE"), "state") == "running"
   and "after the month ends" in (opn.get("words") or ""))
ck("1 September (parked) holds nothing for the dealers", (safe(getattr(SR, "s750_open", None), con, "2026-09") or {}).get("n") == 0 and safe(getattr(SR, "s750_lock_reasons", None), con, "2026-09") == [])

print("2 · row 7 on the step view, row 8 waits for it")
st, h, r7, r8 = rows7()
ck("2 the step view answers (200)", st == 200, s750=False)
ck("2 row 7 is 'Dealer summaries' with the dealers' count words, not 'later'", "Dealer summaries" in r7 and "later" not in r7 and "2 agree" in r7 and "awaited" in r7)
ck("2 the header line of row 7: Dealer · summary / Scanned / Scan / What / Whose · next", "Dealer · summary" in r7 and "Whose · next" in r7)
ck("2 Shivaaz's line: Agrees ✓, the scan folded ('Show summary'), 'Nobody. Payable ₹7,978.'", "Agrees ✓" in r7 and "Show summary" in r7 and "Nobody. Payable ₹7,978." in r7)
ck("2 Bass's line: 'Summary ₹2,140 more than Marg', the why names A017460, 'Yours.', the three buttons", "Summary ₹2,140 more than Marg" in r7 and "A017460" in r7
   and "<b>Yours.</b>" in r7 and "Ask the dealer" in r7 and "Carry to November" in r7 and "Accept the dealer" in r7)
ck("2 Deepam's line: Awaited, on reception's list by itself (S755: no 'Ask reception' button), 'Deepam Pharma gives no summary'", "Awaited · 2 bills" in r7 and "list by itself since the month ended" in r7 and "Deepam Pharma gives no summary" in r7)
ck("2 Kedar's line: could not be read, 'Ask reception to rescan'", "could not be read" in r7 and "Ask reception to rescan" in r7)
ck("2 the unknown summary: 'Pick the dealer' with the month's dealers in a list", "Pick the dealer" in r7 and 'id="s750pick604"' in r7 and "This dealer" in r7)
ck("2 Ravi's line says his Confirm counts; Yogendra's why names Marg's purchase return", "Confirm on row 3 counts as the summary" in r7 and "Yogendra Agencies" in r7)
from urllib.parse import quote as _q                          # noqa: E402
ck("2 the way to the ledgers on row 7 and on each dealer's line (the key URL-quoted)", "/finance/purchase/page/ledger\">the dealer ledgers" in r7 and "/page/ledger/%s\">" % _q(PA.supplier_key("SHIVAAZ MEDICOS"), safe="") in r7)
ck("2 row 8: 'opens when rows 2–7 are clear and Marg's re-export after the last correction is in'; Holding names the dealer summaries; D849 said",
   "rows 2–7 are clear" in r8 and "dealer summar" in r8 and "D849" in r8 and "Holding:" in r8)
n_open = re.search(r'id="s726strip">NEFT on hold · (\d+) open', h)
ck("2 the strip's open count carries the dealers (register open + %d)" % op.get("n", 0), n_open is not None and int(n_open.group(1)) == (safe(getattr(SR, "_s749_month_open_before_s750", None), con, "2026-10") or {}).get("open", -1) + op.get("n", 0))
ck("2 no build or decision number on the owner's row 7 but D849 on row 8", not re.search(r"\b(S\d{3}|F-\d{3,4})\b", re.sub(r"<[^>]+>", " ", r7)), s750=False)

print("3 · the owner's answers (audited, Undo) and their effect")
bass = PA.supplier_key("BASS MEDICAL STORE")
dee = PA.supplier_key("DEEPAM PHARMA")
ked = PA.supplier_key("KEDAR PHARMACEUTICAL")
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=dee, month="2026-10", decision="none"))
ck("3 'Deepam gives no summary' taken (200)", st == 200 and j.get("ok") and "gives no summary" in j.get("message", ""))
ds = {d["key"] or "?": d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-10") or [])}
ck("3 ... Deepam: state 'none', holds nothing; the word stands for November too", G(ds, dee, "state") == "none" and G(ds, dee, "holds") is False
   and (safe(getattr(SR, "s750_answers", None), con, "2026-11") or {}).get((dee, "2026-11"), {}).get("kind") == "none")
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=dee, month="2026-10", decision="scan"))
ck("3 a scan ask on a dealer who gives none is refused (409): 'undo that word first'", st == 409 and "undo that word first" in j.get("message", ""))
st, j = post("/finance/purchase/api/s750/answer", dict(dealer="NOBODY LTD", month="2026-10", decision="none"))
ck("3 a dealer Marg does not know is refused (409)", st == 409)
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=PA.supplier_key("GUNINA PHARMACEUTICALS"), month="2026-10", decision="scan"))
ck("3 'Ask reception to scan it' for Gunina (200): 'Reception's list asks'", st == 200 and "Reception" in j.get("message", ""))
asks = safe(getattr(SR, "s750_reception_asks", None), con) or []
ck("3 reception's asks carry Gunina's October summary", any(x["dealer"] == PA.supplier_key("GUNINA PHARMACEUTICALS") and x["month"] == "2026-10" and x["kind"] == "scan" for x in asks))
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=ked, month="2026-10", decision="rescan"))
ck("3 'Ask reception to rescan' for Kedar (200)", st == 200 and any(x["dealer"] == ked and x["kind"] == "rescan" and x["scan"] == 605 for x in (safe(getattr(SR, "s750_reception_asks", None), con) or [])))
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=bass, month="2026-10", decision="ask"))
ck("3 'Ask the dealer' on Bass (200): the line waits, 'asked'", st == 200 and "Asked the dealer" in j.get("message", ""))
ds = {d["key"] or "?": d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-10") or [])}
ck("3 ... Bass still holds (asked, waiting); s750_open counts it as asked, not differ", G(ds, bass, "holds") and (safe(getattr(SR, "s750_open", None), con, "2026-10") or {}).get("asked") == 1)
st, h, r7, r8 = rows7()
ck("3 ... his line says 'Asked the dealer dd-Mon -- waiting' with Carry / Accept / Undo the ask", "Asked the dealer" in r7 and "waiting" in r7 and "Undo the ask" in r7 and "Carry to November" in r7)
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=bass, month="2026-10", decision="carry"))
ck("3 'Carry to November' on Bass (200): ₹2,140 carried", st == 200 and "2,140" in j.get("message", "") and "November" in j.get("message", ""))
ds = {d["key"] or "?": d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-10") or [])}
ck("3 ... Bass no longer holds; October's dealer holds: the awaited ones only", G(ds, bass, "holds") is False and (safe(getattr(SR, "s750_open", None), con, "2026-10") or {}).get("differ") == 0)
cin = safe(getattr(SR, "s750_carried_in", None), con, "2026-11") or {}
ck("3 ... November carries ₹2,140 in for Bass", cin.get(bass) == 214000)
mbill("bass_late", "BASS MEDICAL STORE", "A017460", "2026-10-28", 2140)          # the paper came: Amir entered the bill in Marg
ck("3 ... once Marg carries A017460 the carry is stale: nothing is carried into November; October's Bass line agrees and names the stale carry",
   not (safe(getattr(SR, "s750_carried_in", None), con, "2026-11") or {}).get(bass)
   and G({d["key"]: d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-10") or [])}, bass, "state") == "agrees" and "is stale" in rows7()[2])
con.execute("DELETE FROM purchase_bill WHERE id=?", (BID["bass_late"],)); con.commit()
sh = safe(getattr(SR, "s750_sheet", None), con, "2026-11") or {}
ck("3 ... the November sheet reads it (carried_in_p)", (sh.get(bass) or {}).get("carried_in_p") == 214000)
try:
    acts = con.execute("SELECT id, kind FROM s750_answer WHERE dealer=? AND month='2026-10' AND undone_at IS NULL ORDER BY id DESC", (bass,)).fetchall()
except sqlite3.Error:
    acts = []
st, j = post("/finance/purchase/api/s750/undo", dict(act=int(acts[0][0]) if acts else 0))
ck("3 Undo the carry (200)", st == 200 and j.get("ok") and "Undone" in j.get("message", ""))
ck("3 ... November carries nothing in; the ask stands again", not (safe(getattr(SR, "s750_carried_in", None), con, "2026-11") or {}).get(bass)
   and (safe(getattr(SR, "s750_answers", None), con, "2026-10") or {}).get((bass, "2026-10"), {}).get("kind") == "ask")
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=bass, month="2026-10", decision="accept"))
ck("3 'Accept the dealer's figure' on Bass (200): ₹5,237 stands; Amir's card asks", st == 200 and "5,237" in j.get("message", "") and "Amir" in j.get("message", ""))
sh = safe(getattr(SR, "s750_sheet", None), con, "2026-10") or {}
ck("3 ... the October sheet: Bass payable = the dealer's figure 5,237 ('accepted')", (sh.get(bass) or {}).get("payable_p") == 523700 and (sh.get(bass) or {}).get("words") == "accepted")
ent = safe(getattr(SR, "s750_amir_enter", None), con) or []
ck("3 ... Amir is to enter A017460 ₹2,140 (s750_amir_enter)", any(x["no"] == "A017460" and x["amount_p"] == 214000 for x in ent))
st, j = post("/finance/purchase/api/s750/dealer_of", dict(scan=604, dealer=PA.supplier_key("DELTA DRUGS")))
ck("3 the unknown summary named as Delta's (200)", st == 200 and j.get("ok"))
ds = {d["key"] or "?": d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-10") or [])}
ck("3 ... Zeta's scan is now Delta's summary: differs (100 against 1,500), no unknown line left", "?" not in ds and G(ds, PA.supplier_key("DELTA DRUGS"), "state") == "differs")
ck("3 ... Delta's line offers 'Not Delta Drugs' summary' (the pick's Undo; S755's possessive)", "Not Delta Drugs&#x27; summary" in rows7()[2])
st, j = post("/finance/purchase/api/s750/dealer_of", dict(scan=604, dealer=""))
ck("3 the pick undone (200): the scan is nobody's again", st == 200 and "nobody's again" in j.get("message", "")
   and "?" in {d["key"] or "?": d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-10") or [])})
post("/finance/purchase/api/s750/dealer_of", dict(scan=604, dealer=PA.supplier_key("DELTA DRUGS")))
mbill("shi_ret", "SHIVAAZ MEDICOS", "PR-9", "2026-10-29", -100)                   # Marg's purchase return the summary does not credit
ds = {d["key"] or "?": d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-10") or [])}
ck("3 a Marg purchase return the summary does not credit: Shivaaz differs by ₹100, the why names PR-9, unexplained (holds)",
   G(ds, PA.supplier_key("SHIVAAZ MEDICOS"), "state") == "differs" and G(ds, PA.supplier_key("SHIVAAZ MEDICOS"), "holds") and any("PR-9" in w for w in G(ds, PA.supplier_key("SHIVAAZ MEDICOS"), "why", default=[])))
con.execute("DELETE FROM purchase_bill WHERE id=?", (BID["shi_ret"],)); con.commit()
aud = G(con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action IN ('s750_answer','s750_answer_undone','s750_dealer_of','s750_dealer_of_undone')").fetchone(), 0, default=0)
ck("3 every answer, undo and pick is in purchase_audit (>= 10 rows)", aud >= 10)
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=bass, month="2026-10", decision="pay"))
ck("3 an answer that is not one of the row's is refused (409)", st == 409 and not j.get("ok"))
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=bass, month="2026-09", decision="none"))
ck("3 a parked month is refused (409)", st == 409)
as_(AMIR)
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=bass, month="2026-10", decision="none"))
ck("3 Amir (viewer) is refused the doors (403)", st == 403)
as_(SHAVEZ, "sender")
st, j = post("/finance/purchase/api/s750/undo", dict(act=1))
ck("3 Shavez (maker) is refused the doors (403)", st == 403)
WHO["u"] = None
st, j = post("/finance/purchase/api/s750/answer", dict(dealer=bass, month="2026-10", decision="none"))
ck("3 a stranger is refused (403)", st == 403)
as_(OWNER, "checker")

a_nov = (safe(getattr(SR, "s750_answers", None), con, "2026-11") or {}).get((dee, "2026-11")) or {}
ck("3 November: Deepam's standing 'gives no summary' carries the word's own id (so a later month can undo it)", a_nov.get("kind") == "none" and int(a_nov.get("id") or 0) > 0 and a_nov.get("standing"))
print("4 · the lock gate, the payment sheet, the hub")
s_ = safe(PA._month_summary, con, "2026-10")
gate = safe(PA._lock_gate, con, "2026-10", s_) if s_ else None
ck("4 the one gate names the dealer summaries' holds -- once each, through the purchase check's line (never twice)", gate is not None and not gate[0]
   and sum(1 for x in gate[1] if "dealer summaries awaited" in x) == 1 and sum(1 for x in gate[1] if "dealer summar" in x and "differ" in x) <= 1)
st, h = get("/finance/purchase/page/pay/2026-10")
ck("4 the payment sheet answers (200)", st == 200, s750=False)
ck("4 the sheet has the column 'Dealer's summary' and the TOTAL row has eight cells", "Dealer's summary" in h and h.count('<th class="n">') >= 14)
ck("4 Shivaaz's row: ₹7,978 with the chip 'agrees'", re.search(r"SHIVAAZ MEDICOS.*?₹7,978 <span class=\"chip ok\">agrees</span>", h, re.S) is not None)
ck("4 Bass's row: ₹5,237 'accepted' and Payable ₹5,237", re.search(r"BASS MEDICAL STORE.*?₹5,237 <span class=\"chip ok\">accepted</span>.*?id=\"py_%s\">₹5,237" % re.escape(bass), h, re.S) is not None)
ck("4 Deepam's row: 'none given'; Gunina's: 'awaited'", "none given" in h and "awaited" in h)
neft = re.search(r"NEFT[^<]*?₹([\d,]+)", h)
ck("4 the sheet's footer says the dealer's figure is followed, with the ledgers link", "Payable follows it" in h and "/page/ledger\">The dealer ledgers" in h)
s_, groups = safe(PA._pay_rows, con, "2026-10") or (None, [])
gb = next((g for g in groups if g["norm"] == bass), {})
ck("4 _pay_rows: Bass payable_p = 523,700 paise (accepted) -- the NEFT total follows", gb.get("payable_p") == 523700 and (gb.get("s750") or {}).get("words") == "accepted")
post("/finance/purchase/api/s750/answer", dict(dealer=bass, month="2026-10", decision="carry"))     # a second answer replaces the accept for November's test
s_, groups = safe(PA._pay_rows, con, "2026-11") or (None, [])
gb = next((g for g in groups if g["norm"] == bass), {})
ck("4 November's sheet: Bass 'Carried in' ₹2,140 by the owner's carry (nothing typed), payable 900 + 2,140", gb.get("carry_p") == 214000 and gb.get("s750_carry_auto") and gb.get("payable_p") == 304000)
st, h = get("/finance/purchase/page/pay/2026-11")
ck("4 ... the sheet says 'carried by you (row 7)' under it; the input is EMPTY with the figure as placeholder (never typed by the kit)",
   "carried by you (row 7)" in h and re.search(r'id="cf_%s" value="" placeholder="2140"' % re.escape(bass), h) is not None)
st, h = get("/finance/purchase/page/hub")
ck("4 the hub has the way to the dealer ledgers", st == 200 and "/page/ledger\">The dealer ledgers" in h)

print("5 · the dealer ledger")
st, h = get("/finance/purchase/page/ledger")
ck("5 the dealers page answers (200) and lists Bass, Shivaaz, Yogendra with this financial year's purchases", st == 200 and "Bass Medical Store" in h and "Shivaaz Medicos" in h and "FY 2026-27" in h)
st, h = get("/finance/purchase/page/ledger/%s" % PA.supplier_key("YOGENDRA AGENCIES"))
ck("5 Yogendra's ledger answers (200)", st == 200)
ck("5 the FY block: purchases ₹6,286 · returns ₹286 · payable ₹6,000; items 'DELTA SYP' qty 2", "FY 2026-27" in h and "purchases <b>₹6,286</b>" in h and "returns <b>₹286</b>" in h
   and "payable <b>₹6,000</b>" in h and re.search(r"DELTA SYP</td><td class=\"mut\">[^<]*</td><td class=\"n\">2</td>", h) is not None)
ck("5 October's fold is open; the reconciliation line reads purchases − returns = payable; the summary 'Agrees ✓'", '<details class="m" open>' in h and "Reconciliation:" in h
   and "purchases ₹6,286 − returns ₹286 = payable <b>₹6,000</b>" in h and "Agrees ✓" in h)
ck("5 the bill 19612 is a fold with its item lines; the purchase return PR-7 is marked", "<b>19612</b>" in h and "DELTA SYP" in h and "Purchase return " in h and "PR-7" in h)
ck("5 paid: 'nothing recorded yet'; balance ₹6,000", "nothing recorded yet" in h and "balance ₹6,000" in h)
st, h2 = get("/finance/purchase/page/ledger/%s?print=1" % PA.supplier_key("YOGENDRA AGENCIES"))
ck("5 ?print=1 opens every fold and prints", h2.count("<details class=\"b\" open>") >= 2 and "window.print()" in h2)
L = safe(getattr(PA, "s750_ledger", None), con, bass) or {}
ck("5 Bass's ledger: two months (Nov, Oct), FY purchases 900 + 3,097 = 3,997; November carries 2,140 in; October's summary 'differs'",
   [m["month"] for m in L.get("months", [])] == ["2026-11", "2026-10"] and G(L, "fys", "FY 2026-27", "purchases_p") == 399700
   and G(L, "months", 0, "carry_in_p") == 214000 and G(L, "months", 1, "summary", "state") == "differs")
st, h = get("/finance/purchase/page/ledger/nobody-here")
ck("5 an unknown dealer: 404", st == 404, s750=False)
as_(AMIR)
st, h = get("/finance/purchase/page/ledger")
ck("5 Amir (viewer, not a sender) is refused the ledgers (403)", st == 403)
as_(SHAVEZ, "sender")
st, h = get("/finance/purchase/page/ledger")
ck("5 Shavez (a sender, or not one in this walk) is answered by the ledger door (200 or 403, never 404)", st in (200, 403))
as_(OWNER, "checker")

print("6 · reception's list and Amir's card")
as_(RECEP, "sender")
st, h = get("/finance/porders/s454/billkaam")
ck("6 Aaj ka bill kaam answers (200)", st == 200, s750=False)
ck("6 the group 'Dealer ka hisaab (summary) scan karo' with Gunina's October and Kedar's rescan, the instruction and the scan link",
   "Dealer ka hisaab (summary) scan karo" in h and "Gunina Pharmaceuticals ka October 2026 ka hisaab (summary) scan karo" in h
   and "Kedar Pharmaceutical ke hisaab (summary) ko dobara scan karo" in h and "button dabaiye" in h and "lane=pharmacy" in h and "/scanapp/bills/605/file" in h)
m6 = safe(P4.s736_model, con) or {}
ck("6 the model's count carries the asks (s750)", len(m6.get("s750") or []) >= 2 and m6.get("n", 0) >= len(m6.get("s750") or []))
as_(AMIR)
st, h = get("/finance/amir/step/1")
ck("6 Amir's page answers (200)", st == 200, s750=False)
post_accept = None
as_(OWNER, "checker")
post("/finance/purchase/api/s750/answer", dict(dealer=bass, month="2026-10", decision="accept"))
as_(AMIR)
st, h = get("/finance/amir/step/1")
ck("6 Amir's card: 'Dealer ke hisaab ka bill, Marg mein nahi · 1' -- Bass A017460 ₹2,140, 'kaagaz aane par Marg mein entry karein'",
   "Dealer ke hisaab ka bill, Marg mein nahi &middot; 1" in h and "A017460" in h and "2,140" in h and "kaagaz aane par Marg mein entry karein" in h)
as_(OWNER, "checker")

print("7 · the register's other pages still read; nothing changed in the earlier rows")
st, h = get("/finance/purchase/page/scans?month=2026-10")
ck("7 the register page answers (200)", st == 200, s750=False)
st, h = get("/finance/purchase/page/month/2026-10")
ck("7 the audit page answers (200)", st == 200, s750=False)
st, h = get("/finance/purchase/page/check?month=2026-09")
ck("7 September (parked): row 7 holds nothing, the strip is as before", st == 200 and "is parked" in h, s750=False)


# ============================================================================================================================================
#  S753_SUMMARY_SCANS_READ (Sanjeevni session 408, 08-Nov-2026) -- the checks of this kit, on walk_s750's fixture (every S750 check above must
#  stay green on the kit's files). CONTROL: on the live files (S750's TO) every [S753] check goes red.
# ============================================================================================================================================
S753F = []


def ck753(name, cond):
    print(("  ok   " if cond else "  FAIL ") + "[S753] " + name)
    if not cond:
        FAILS.append(name)
        S753F.append(name)


def body(path):
    r = cl.get(path)
    return r.status_code, r.get_data()


as_(OWNER, "checker")
print("8 · S753: the summary viewer opens a Summary (the doctor only)")
st, b = body("/finance/purchase/api/s738/scan/601")
ck753("8 /api/s738/scan/<summary id> answers 200 with the PDF bytes for the doctor (601)", st == 200 and b[:4] == b"%PDF")
st, b = body("/finance/purchase/api/s738/scan/501")
ck("8 a bill's scan still opens (501)", st == 200 and b[:4] == b"%PDF", s750=False)
st, b = body("/finance/purchase/api/s738/scan/999")
ck("8 an unknown id is 404", st == 404, s750=False)
as_(AMIR)
st, b = body("/finance/purchase/api/s738/scan/601")
ck("8 Amir is refused a summary scan (not on his list)", st in (403, 409) or (st == 200 and b[:4] != b"%PDF"), s750=False)
as_(OWNER, "checker")

print("9 · S753: the month from the bills, never the pharmacy itself, the dealer from its bills")
# Marg: Daanshi's one October bill; L.K.'s two statement bills; two dealers sharing bill '777' for Rs 500 (the tie)
mbill("daan1", "DAANSHI PHARMA", "A000217", "2026-10-12", 8603.0)
mbill("lk1", "L.K. DRUG HOUSE", "RT-090058", "2026-10-02", 958.0)
mbill("lk2", "L.K. DRUG HOUSE", "RT-092205", "2026-10-06", 2698.0)
mbill("tie1", "ALPHA DISTRIBUTORS", "777", "2026-10-05", 500.0)
mbill("tie2", "BETA AGENCIES", "777", "2026-10-05", 500.0)
# 606 Daanshi's statement read as the BUYER, printed 'as on 02-11': its one bill is October's
summary(606, "SANJEEVNI MEDICOS", "2026-11-02", [("bill", "A000217", "2026-10-12", 8603.0)], total=8603.0, closing=8603.0, dealer="SANJEEVNI MEDICOS")
# 607 L.K.'s statement with no seller name printed: the reader names no dealer; its bills are L.K.'s in Marg
summary(607, "", "2026-10-15", [("bill", "RT-090058", "2026-10-02", 958.0), ("bill", "RT-092205", "2026-10-06", 2698.0)], total=3656.0, closing=3656.0, dealer="")
# 608 a name nobody knows and one bill two dealers hold: the owner picks
summary(608, "", "2026-10-31", [("bill", "777", "2026-10-05", 500.0)], total=500.0, dealer="ZETA TWO UNKNOWN")
# 610 a statement with one October and one November bill, period_to in November: the tie falls back to the period
summary(610, "KEDAR PHARMACEUTICAL", "2026-11-30", [("bill", "K-1", "2026-10-20", 100.0), ("bill", "K-2", "2026-11-03", 100.0)], total=200.0)
# 611 the buyer's name, a bill Marg does not have: unknown, and the row never says Sanjeevni
summary(611, "SANJEEVNI MEDICOSE", "2026-10-31", [("bill", "Q-1", "2026-10-09", 50.0)], total=50.0, dealer="Sanjeevni Medicose")
a.execute("UPDATE claude_reading SET doc_kind='summary' WHERE bill_id IN (606,607,608,610,611)")
a.execute("UPDATE claude_reading SET data=json_set(data,'$.dealer',null) WHERE bill_id=607")
a.commit()
scans = safe(getattr(SR, "s750_summary_scans", None), con) or {}
ck753("9 606: the month is the bills' (2026-10), not the printed 'as on 02-11'", G(scans, 606, "month") == "2026-10")
ck("9 610: October and November tie -> the period's month (2026-11)", G(scans, 610, "month") == "2026-11", s750=False)
ck("9 601's month unchanged (2026-10)", G(scans, 601, "month") == "2026-10", s750=False)
daan, lk = PA.supplier_key("DAANSHI PHARMA"), PA.supplier_key("L.K. DRUG HOUSE")
dof = safe(getattr(SR, "_s750_dealer_of", None), con, scans) or {}
ck753("9 606: 'SANJEEVNI MEDICOS' is never the dealer; Daanshi named by its bill A000217", dof.get(606) == daan)
ck753("9 607: no name printed -> L.K. named by its two bills (the fallback), flagged dealer_by_bills", dof.get(607) == lk and G(scans, 607, "dealer_by_bills") is True)
ck("9 608: one bill two dealers hold -> nobody (the owner picks)", dof.get(608, "x") == "", s750=False)
ck753("9 611: the buyer's name and no Marg bill -> nobody, never Sanjeevni", dof.get(611, "x") == "")
ck("9 601, 602 named by their printed names as before (not by bills)", dof.get(601) == PA.supplier_key("SHIVAAZ MEDICOS") and not G(scans, 601, "dealer_by_bills"), s750=False)
ds = {d["key"] or ("?" + str(G(d, "summary", "id", default=""))): d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-10") or [])}
ck753("9 row 7: Daanshi agrees by its summary (8,603 = Marg)", G(ds, daan, "state") == "agrees" and G(ds, daan, "summary", "id") == 606)
ck753("9 row 7: L.K.'s summary sits on L.K.'s line", G(ds, lk, "summary", "id") == 607)
unk = [d for d in ds.values() if d["state"] == "unknown"]
ck753("9 row 7: the unknown rows (608, 611; 604 was picked as Delta's above) never carry 'Sanjeevni'", {G(d, "summary", "id") for d in unk} == {608, 611}
      and not any("sanjeevni" in str(d["name"]).lower() for d in unk) and any("could not name" in str(d["name"]) for d in unk if G(d, "summary", "id") == 611))

print("10 · S753: the folded viewer's footer counts the bills")
st, h, r7, r8 = rows7()
ck("10 the step view answers (200)", st == 200, s750=False)
ck753("10 603: '3 bills ₹5,237' on its footer", "3 bills " in r7 and "3 bills %s" % SR.rs(523700) in r7)
ck753("10 601: '1 bill ₹7,978' (singular)", "1 bill %s" % SR.rs(797800) in r7)
ck753("10 607: 'dealer named by its bills' on L.K.'s footer", "dealer named by its bills" in r7)
ck("10 'Pick the dealer' still offered on the unknown rows", r7.count("Pick the dealer") >= 2, s750=False)
ck("10 the register and the sheet still answer", get("/finance/purchase/page/scans?month=2026-10")[0] == 200 and get("/finance/purchase/page/pay/2026-10")[0] == 200, s750=False)


# ============================================================================================================================================
#  S755_SUMMARY_REMINDERS (Sanjeevni session 408, 08-Nov-2026) -- the checks of this kit, on walk_s753's fixture (every S750 and S753 check
#  above must stay green on the kit's files). CONTROL: on the live files (S753's TO) every [S755] check goes red.
# ============================================================================================================================================
S755F = []


def ck755(name, cond):
    print(("  ok   " if cond else "  FAIL ") + "[S755] " + name)
    if not cond:
        FAILS.append(name)
        S755F.append(name)


as_(OWNER, "checker")
print("11 · S755: the awaited dealers of an ended month reach reception's list by themselves")
asks = safe(getattr(SR, "s750_reception_asks", None), con) or []
auto = [a for a in asks if a.get("auto")]
owned = [a for a in asks if not a.get("auto")]
aw_oct = [d for d in (safe(getattr(SR, "s750_dealers", None), con, "2026-10") or []) if d["state"] == "awaited"]
ck("11 October has awaited dealers in the fixture (Deepam, Gunina, ...)", len(aw_oct) >= 3, s750=False)
aw_set = {(d["key"], "2026-10") for d in aw_oct}
ck755("11 every awaited dealer of October is on the list -- by itself (auto) unless the owner already asked; nothing else is auto",
      aw_set <= ({(a["dealer"], a["month"]) for a in auto} | {(a["dealer"], a["month"]) for a in owned}) and {(a["dealer"], a["month"]) for a in auto} <= aw_set
      and len(auto) >= len(aw_set) - 1 and all(a["kind"] == "scan" and a.get("at") == "" for a in auto))
ck755("11 the owner's own asks keep their words (at set, not auto) and are not doubled", all(a.get("at") for a in owned) and
      not ({(a["dealer"], a["month"]) for a in owned} & {(a["dealer"], a["month"]) for a in auto}))
ck("11 nothing of the running month (2026-11) is on the list", not any(a["month"] >= "2026-11" for a in asks), s750=False)
m11 = safe(P4.s736_model, con) or {}
ck755("11 reception's model counts the automatic asks", len(m11.get("s750") or []) == len(asks) and len(asks) > len(owned))
as_(RECEP, "sender")
st, h = get("/finance/porders/s454/billkaam")
ck("11 Aaj ka bill kaam answers (200)", st == 200, s750=False)
ck755("11 the automatic card says the month has ended ('khatam ... abhi tak nahi aaya'), the owner's says 'Doctor sahab ne'",
      "khatam" in h and "abhi tak nahi aaya" in h and "Doctor sahab ne" in h and h.count("ka hisaab (summary) scan karo") >= len(auto))
as_(OWNER, "checker")

print("12 · S755: row 7's awaited line, the possessive, the plain words; row 1 and the hub count alike (F-1188)")
import html as _html                                          # noqa: E402
st, h, r7, r8 = rows7()
ck("12 the step view answers (200)", st == 200, s750=False)
ck755("12 the awaited line: 'On reception's list by itself since the month ended'", "On reception's list by itself since the month ended" in _html.unescape(r7))
ck755("12 'Ask reception to scan it' is gone from row 7", "Ask reception to scan it" not in r7)
u7 = _html.unescape(r7)
ck755("12 the possessive: 'Yogendra Agencies' ledger' / 'Shivaaz Medicos' ledger'", "Yogendra Agencies' ledger" in u7 and "Shivaaz Medicos' ledger" in u7
      and "Agencies's" not in u7 and "Medicos's" not in u7 and "Delta Drugs' summary" in u7)
ck755("12 the help sentence in plain English", "already explains needs nothing from you" in r7 and "already carry holds nothing new" not in r7)
ck755("12 ' -- ' read as ' · ' on rows 7 and 8", " -- " not in r7 and " -- " not in r8 and "reports · nothing else" in r8)
nb = con.execute("SELECT id FROM purchase_bill WHERE COALESCE(month, substr(bill_date,1,7))='2026-10' AND scan_bill_id IS NULL AND amount_p > 0 ORDER BY id LIMIT 1").fetchone()
con.execute("INSERT OR REPLACE INTO s454_paper_missing (bill_id, by, at, accepted_by, accepted_at) VALUES (?, 'reception', '2026-11-02T10:00:00', 'manoj', '2026-11-03T10:00:00')", (int(nb[0]),))
con.commit()
r = reg("2026-10")
c = r.get("counts") or {}
ck("12 the fixture now carries one bill accepted without paper", c.get("accepted", 0) >= 1, s750=False)
st, h, r7, r8 = rows7()
n_head = c.get("verified", 0) + c.get("has_scan", 0) + c.get("accepted", 0) + c.get("confirmed", 0)
mo = safe(getattr(SR, "s749_month_open", None), con, "2026-10") or {}
ck755("12 F-1188: s749_month_open's match = verified + has_scan + accepted + confirmed (%d)" % n_head, mo.get("match") == n_head and n_head > c.get("verified", 0) + c.get("has_scan", 0))
r1 = between(h, 'data-row="1">', 'data-row="2">')
ck755("12 row 1's body counts as its heading does (The %d bills that match)" % n_head, ("The %d bill" % n_head) in r1)
ck("12 the strip and the hub still answer", get("/finance/purchase/page/hub")[0] == 200, s750=False)

print("13 · S755: F-1189 -- a month before the register began reads 'settled outside the system' on the ledger")
# a dealer with a September bill (before purchase.register_from 2026-10-01)
con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
con.commit()
mbill("sep1", "OMEGA REMEDIES", "OM-900", "2026-09-12", 1200.0)
omega = PA.supplier_key("OMEGA REMEDIES")
L = safe(PA.s750_ledger, con, omega) or {}
sep = next((m for m in (L.get("months") or []) if m["month"] == "2026-09"), {})
octm = next((m for m in (L.get("months") or []) if m["month"] == "2026-10"), {})
ck("13 the ledger carries September and October for Omega", bool(sep) and bool(octm), s750=False)
ck755("13 September: settled, paid = payable, balance 0", sep.get("settled") is True and sep.get("paid_p") == sep.get("payable_p") and sep.get("balance_p") == 0 and sep.get("payable_p", 0) > 0)
ck755("13 October: not settled by this rule (the register's month)", octm.get("settled") is False)
fy = next((f for f in (L.get("fys") or {}).values() if "2026" in f["fy"]), {})
ck755("13 the FY block counts the settled months (1)", fy.get("settled") == 1)
st, h = get("/finance/purchase/page/ledger/%s" % omega)
ck755("13 the ledger page says 'settled outside the system' once for the month and once in the FY block", st == 200 and h.count("settled outside the system") == 2)
con.executescript(PA.PAY_SHEET)
con.execute("INSERT INTO purchase_pay_line (month, vendor_norm, paid_p, updated_by, updated_at) VALUES ('2026-09', ?, 50000, 'manoj', '2026-10-01T10:00:00')", (omega,))
con.commit()
L2 = safe(PA.s750_ledger, con, omega) or {}
sep2 = next((m for m in (L2.get("months") or []) if m["month"] == "2026-09"), {})
ck755("13 a typed Paid still wins (September paid 500, balance 700, not 'settled')", sep2.get("settled") is False and sep2.get("paid_p") == 50000 and sep2.get("balance_p") == 70000)

print("14 · S755: the daily line to the owner and Shavez (owner_notice, read only; nothing leaves a walk)")
import importlib                                              # noqa: E402
import types                                                  # noqa: E402
os.environ["FINANCE_OFF_DIR"] = os.path.join(TMP, "nooff")
ON = importlib.import_module("owner_notice")
ON.ensure(con)
import datetime as _dt                                        # noqa: E402
now = _dt.datetime(2026, 11, 8, 11, 0, tzinfo=ON.IST)
msgs, errs = safe(ON.collect, con, now) or ([], ["collect raised"])
summ = [m for m in msgs if str(m["key"]).startswith("summaries:")]
names = sorted(d["name"].title() for d in aw_oct)
ck755("14 at 11:00 one 'October 2026: N summaries awaited' message, the dealers named, none for November", len(summ) == 1 and summ[0]["key"] == "summaries:2026-10:2026-11-08"
      and summ[0]["title"].startswith("October 2026: %d summar" % len(aw_oct)) and all(n in summ[0]["body"] for n in names))
early = [m for m in (safe(ON.collect, con, _dt.datetime(2026, 11, 8, 9, 0, tzinfo=ON.IST)) or ([], []))[0] if str(m["key"]).startswith("summaries:")]
ck755("14 nothing before owner_notice.summaries_hhmm (10:30)", early == [])
pl = safe(getattr(ON, "_payload", None), "summaries:2026-10:2026-11-08", "t", "b") or {}
ck755("14 the message opens the month's purchase check", pl.get("url") == "/finance/purchase/page/check?month=2026-10")
sent_to = []
fake = types.ModuleType("order_rules")
fake._push = lambda u, p: (sent_to.append(u) or (1, 0))
sys.modules["order_rules"] = fake
ON._is_live = lambda c: True
for k in ("ORDER_PUSH_STUB", "ORDER_PUSH_NONE", "OWNER_NOTICE_STUB"):
    os.environ.pop(k, None)
ok1, how1 = ON.deliver(con, "summaries:2026-10:2026-11-08", "t", "b")
ok2, how2 = ON.deliver(con, "pair:2026-11-08", "t", "b")
ck755("14 the summaries line goes to manoj and shavez; an ordinary message to manoj alone", ok1 and sent_to[:2] == ["manoj", "shavez"] and ok2 and sent_to[2:] == ["manoj"])
con.execute("INSERT OR IGNORE INTO owner_notice (key, kind, title, body, made_at) VALUES ('summaries:2026-10:2026-11-08','summaries','t','b','2026-11-08T10:31:00')")
con.commit()
again = [m for m in (safe(ON.collect, con, now) or ([], []))[0] if str(m["key"]).startswith("summaries:")]
ck755("14 said today -> not made again today", again == [])
later = [m for m in (safe(ON.collect, con, _dt.datetime(2026, 11, 9, 11, 0, tzinfo=ON.IST)) or ([], []))[0] if str(m["key"]).startswith("summaries:")]
ck755("14 tomorrow it is said again while dealers are awaited", len(later) == 1 and later[0]["key"] == "summaries:2026-10:2026-11-09")
for d in aw_oct:
    post("/finance/purchase/api/s750/answer", dict(dealer=d["key"], month="2026-10", decision="none"))
none_left = [m for m in (safe(ON.collect, con, _dt.datetime(2026, 11, 10, 11, 0, tzinfo=ON.IST)) or ([], []))[0] if str(m["key"]).startswith("summaries:")]
asks2 = [a for a in (safe(getattr(SR, "s750_reception_asks", None), con) or []) if a.get("auto")]
ck755("14 every awaited dealer marked 'gives no summary' -> no line, and reception's automatic cards are gone", none_left == [] and asks2 == [])

print("walk_s755: %d check(s) failed (%d of them S755 checks, %d S753, %d S750)" % (len(FAILS), len(S755F), len(S753F), len(S750F)))
shutil.rmtree(TMP, ignore_errors=True)
