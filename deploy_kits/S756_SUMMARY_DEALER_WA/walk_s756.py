#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s756.py -- S756_SUMMARY_DEALER_WA on a MADE-UP root (no real data): S755's walk's fixture (a made-up finance.db, assets.db and scan
files; the finance code copied to a temp folder of the walk's own), then the dealer reminder, the snapshot, row 7's count and words, the
reception phone's road, pause / resume, the day turning, fails-closed, the 7th, Sundays, the switch, and owner_notice.py tick run the way
cron runs it (F-1207).
    python3 -B walk_s756.py <finance code dir to test> <purchase_schema.sql> [<dir holding scan_quality.py>]
Run on the TO files: every check green.  CONTROL: on the live files (the 09-Nov bundle) every [S756] check goes red.
The last line: 'walk_s756: N check(s) failed (M of them S756 checks)'."""
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import traceback

os.environ["ORDER_TODAY"] = "2026-11-09"                      # S756: October has ended; the 9th, as the owner's go

CODE, SCHEMA = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
SHARED = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.join(os.path.dirname(CODE), "shared")
PORTAL = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else ""
TMP = tempfile.mkdtemp(prefix="s756walk_")
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
    print(("  ok   " if cond else "  FAIL ") + ("[S756] " if s750 else "") + name)
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




# ====================================================================================================================================
#  S756: the dealer reminder, the snapshot, row 7's count and words
# ====================================================================================================================================
import subprocess                                             # noqa: E402

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
WORDS = "संजीवनी मेडिकोज़, बरेली: अक्टूबर 2026 के बिलों की समरी अभी तक हमें नहीं मिली है। समय से पेमेंट के लिए शीघ्र भेज दें, धन्यवाद।"
TEN = re.compile(r"(?<!\d)\d{10}(?!\d)")


def num(seed):
    """A made-up ten-digit mobile built at run time -- the walk's source holds no number."""
    return "9" + str(seed) * 9


def at(day, hh, mm):
    return dt.datetime(2026, 11, day, hh, mm, tzinfo=IST)


def q(now):
    return safe(getattr(SR, "s756_queue", None), con, now) or {}


def msgs(where="1=1", args=()):
    try:
        return [dict(r) for r in con.execute("SELECT * FROM supplier_msg WHERE kind='summary' AND %s ORDER BY id" % where, args)]
    except sqlite3.Error:
        return []


cols = [r[1] for r in con.execute("PRAGMA table_info(purchase_vendor_contact)")]
for nm, seed in (("DEEPAM PHARMA", 1), ("GUNINA PHARMACEUTICALS", 2), ("OMEGA REMEDIES", 3)):
    k = PA.supplier_key(nm)
    con.execute("INSERT OR REPLACE INTO purchase_vendor_contact (vendor_norm, vendor, phone, updated_at) VALUES (?,?,?,?)", (k, nm, num(seed), "2026-11-01T10:00:00"))
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('supplier_msg.phone_token', 'walk-token-756')")
con.commit()
DS = {d["key"]: d for d in (safe(SR.s750_dealers, con, "2026-10") or [])}
AW = sorted(k for k, d in DS.items() if d.get("state") == "awaited" and k)
WITH_NO = sorted(k for k in AW if k in (PA.supplier_key("DEEPAM PHARMA"), PA.supplier_key("GUNINA PHARMACEUTICALS"), PA.supplier_key("OMEGA REMEDIES")))
print("    (October in the fixture: %d dealers, %d awaited, %d of them with a number)" % (len(DS), len(AW), len(WITH_NO)))

print("10 · S756: the owner's words")
ck("10 the message is his wording to the letter, the month in Hindi", safe(getattr(SR, "s756_body", None), "2026-10") == WORDS)
ck("10 November reads नवंबर 2026", "नवंबर 2026 के बिलों" in (safe(getattr(SR, "s756_body", None), "2026-11") or ""))

print("11 · S756: the snapshot at the top of October's purchase check (the doctor only)")
st, h, r7, r8 = rows7("2026-10")
snap = between(h, '<div id="s756">', '<div class="strip')
ck("11 the page opens (200) and carries the snapshot right under the message line", st == 200 and '<div id="s736msg"></div><style>' in h and 'id="s756"' in h)
ck("11 the heading and the days: 'Where October stands' · 'October ended 9 days ago' · reminders from 07-Nov",
   "Where October stands" in snap and "October ended 9 days ago" in snap and "reminders from 07-Nov" in snap)
ck("11 the awaited table lists each awaited dealer once, with Pause reminders", all(_ := [DS[k]["name"].split()[0].title() in snap for k in AW]) and snap.count("Pause reminders") == len(AW))
ck("11 a dealer with no number reads 'number missing'", "number missing" in snap)
ck("11 a summary not yet named (scan 604) holds the month's reminders, and says so", "Reminders held" in snap)
ck("11 Bass's difference is under 'Differs — yours' with Ask the dealer and Accept", "Differs — yours" in snap and "Bass Medical Store" in between(snap, "Differs — yours", "</div></div>")
   and "Ask the dealer" in snap and "Accept the dealer&#x27;s figure" in snap)
ck("11 the agreeing dealers are folded with the payable", "Agree · " in snap and "nothing for you · payable" in snap)
ck("11 September is named as parked, not chased", "September 2026 — parked; not chased" in snap)
ck("11 no ten-digit number anywhere on the page", not TEN.search(h))
st9, h9, _a, _b = rows7("2026-09")
st11, h11, _c, _d = rows7("2026-11")
ck("11 no snapshot on the parked September or the running November", st9 == 200 and st11 == 200 and 'id="s756"' not in h9 and 'id="s756"' not in h11)

print("12 · S756: row 7 -- the count line names every dealer; the awaited line is true to the month")
m7 = re.search(r'data-row="7">.*?<span class="n">([^<]*)</span>', h, re.S)
words7 = m7.group(1) if m7 else ""
ck("12 the count line adds up to every dealer of the month (%s)" % words7, sum(int(x) for x in re.findall(r"(\d+) ", words7)) == len(DS) and len(DS) > 0)
ck("12 October's awaited line: reception's list · told each morning · reminded on WhatsApp each day from 07-Nov",
   "reminded on WhatsApp each day from 07-Nov" in r7)
_s, _h, r7s, _x = rows7("2026-09")
ck("12 September's awaited line: 'Parked month · nobody is asked' -- never reception's list", "Parked month · nobody is asked" in r7s and "On reception&#x27;s list" not in r7s and "On reception's list" not in r7s)

print("13 · S756: the queue -- from the 7th, at 11:30 IST, once a day, Sundays too")
r = q(at(8, 11, 30))
ck("13 HELD: on the 8th, with a summary not yet named, nothing is queued for October", not msgs() and r.get("held") == "2026-10" and r.get("error") is None)
a.execute("UPDATE bills SET status='rejected' WHERE id=604")             # the unnamed summary set aside: the month is no longer held
a.commit()
r = q(at(9, 11, 29))
ck("13 at 11:29 nothing is queued", not msgs() and r.get("error") is None and "queued" in r)
r = q(at(9, 11, 30))
day1 = msgs("ref=20261109")
ck("13 at 11:30 one row per awaited dealer (%d): queued with a number, skipped 'number nahi' without" % len(AW),
   len(day1) == len(AW) and sorted(m["vendor_norm"] for m in day1 if m["status"] == "queued") == WITH_NO
   and all(m["status"] == "skipped" and m["last_error"] == "number nahi" and not m["to_number"] for m in day1 if m["vendor_norm"] not in WITH_NO))
ck("13 every body is his words; month 2026-10; only the October dealers", all(m["body"] == WORDS and m["month"] == "2026-10" for m in day1))
ck("13 nothing for September (parked) or November (running)", not msgs("month<>'2026-10'"))
q(at(9, 11, 35)), q(at(9, 15, 0))
ck("13 a second and third tick the same day add nothing", len(msgs("ref=20261109")) == len(AW))
ck("13 the payment readers never see them (supplier_msg.messages: neft and cheque only)",
   all(x["kind"] in ("neft", "cheque") for x in (safe(__import__("supplier_msg").messages, con, "2026-10") or [])))

print("14 · S756: the reception phone takes them on the supplier_msg road")
rr = cl.get("/finance/api/supplier-msg/next", headers={"X-Phone-Token": "walk-token-756"})
j = rr.get_json() or {}
ck("14 the phone's next message is a summary reminder with his words", rr.status_code == 200 and j.get("text") == WORDS and j.get("to"))
rr2 = cl.post("/finance/api/supplier-msg/done", data=json.dumps(dict(id=j.get("id"), ok=True)), content_type="application/json",
              headers={"X-Phone-Token": "walk-token-756"})
sent1 = msgs("id=?", (j.get("id") or 0,))
ck("14 done -> sent by the reception phone", rr2.status_code == 200 and sent1 and sent1[0]["status"] == "sent")
rr3 = cl.get("/finance/api/supplier-msg/next", headers={"X-Phone-Token": "walk-token-756"})
j3 = rr3.get_json() or {}
cl.post("/finance/api/supplier-msg/done", data=json.dumps(dict(id=j3.get("id"), ok=False, error="walk: no signal")), content_type="application/json",
        headers={"X-Phone-Token": "walk-token-756"})
q(at(9, 11, 50))
f3 = msgs("id=?", (j3.get("id") or 0,))
ck("14 a send the phone reports failed is withdrawn at the next tick -- never retried the same day", f3 and f3[0]["status"] == "skipped"
   and f3[0]["last_error"] == "the reception phone could not send it")
jx_ = cl.get("/finance/api/supplier-msg/next", headers={"X-Phone-Token": "walk-token-756"}).get_json() or {}
ck("14 the phone is never handed the failed one again", jx_.get("id") != j3.get("id"))
st, h, r7, r8 = rows7("2026-10")
ck("14 the snapshot says the phone could not send it", "could not send it" in between(h, '<div id="s756">', '<div class="strip'))
ck("14 the snapshot shows the reminder sent ('· 1 sent')", "· 1 sent" in between(h, '<div id="s756">', '<div class="strip'))

print("15 · S756: pause and resume (the doctor only)")
dee = PA.supplier_key("DEEPAM PHARMA")
as_(SHAVEZ, "maker")
sx, jx = post("/finance/purchase/api/s756/pause", dict(dealer=dee, on=True))
as_(OWNER, "checker")
ck("15 Shavez cannot pause (the doctor only)", sx in (401, 403) or jx.get("ok") is False)
before = [m for m in msgs("vendor_norm=? AND ref=20261109", (dee,))]
sp, jp = post("/finance/purchase/api/s756/pause", dict(dealer=dee, on=True))
after = msgs("vendor_norm=? AND ref=20261109", (dee,))
ck("15 the doctor pauses Deepam: 200, and his unsent row is withdrawn 'paused' (a sent one stays sent)",
   sp == 200 and jp.get("ok") and all((m["status"] == "sent") or (m["status"] == "skipped" and m["last_error"] in ("paused", "number nahi")) for m in after) and before)
st, h, r7, r8 = rows7("2026-10")
snap = between(h, '<div id="s756">', '<div class="strip')
ck("15 the snapshot says 'Paused by you' with Resume", "Paused by you" in snap and ">Resume<" in snap)

print("16 · S756: the day turns -- no backlog, the paused dealer skipped")
q(at(10, 0, 5))
y = msgs("ref=20261109 AND status='queued' AND handed_at IS NULL")
ck("16 at 00:05 nothing of yesterday is left for the phone", not y)
q(at(10, 11, 31))
d2 = msgs("ref=20261110")
ck("16 at 11:31 the next day's rows, Deepam (paused) left out", len(d2) == len(AW) - 1 and dee not in [m["vendor_norm"] for m in d2])
sr_, jr = post("/finance/purchase/api/s756/pause", dict(dealer=dee, on=False))
q(at(11, 11, 30))
ck("16 resumed: Deepam is back on the 11th", sr_ == 200 and dee in [m["vendor_norm"] for m in msgs("ref=20261111")])

print("17 · S756: a dealer no longer awaited is withdrawn at once and never queued again")
gun = PA.supplier_key("GUNINA PHARMACEUTICALS")
sn, jn = post("/finance/purchase/api/s750/answer", dict(dealer=gun, month="2026-10", decision="none"))
q(at(11, 11, 40))
g11 = msgs("vendor_norm=? AND ref=20261111", (gun,))
ck("17 Gunina marked 'gives no summary': its unsent row withdrawn 'no longer awaited'", sn == 200 and g11 and g11[0]["status"] == "skipped" and g11[0]["last_error"] == "no longer awaited")
q(at(12, 11, 30))
ck("17 and nothing for Gunina on the 12th", gun not in [m["vendor_norm"] for m in msgs("ref=20261112")] and msgs("ref=20261112"))

print("18 · S756: fails closed, the 7th, Sundays, the switch")
keep = PA._assets_db
PA._assets_db = os.path.join(TMP, "no-such-assets.db")
r = q(at(13, 11, 30))
PA._assets_db = keep
ck("18 assets.db unreadable: nothing queued, and it says why", not msgs("ref=20261113") and "fails closed" in str(r.get("why")))
os.environ["ORDER_TODAY"] = "2026-11-06"
r = q(dt.datetime(2026, 11, 6, 11, 40, tzinfo=IST))
os.environ["ORDER_TODAY"] = "2026-11-09"
ck("18 before the 7th (6-Nov 11:40): nothing", not msgs("ref=20261106"))
q(at(15, 11, 30))
ck("18 Sunday 15-Nov: the reminders go (Sundays too)", bool(msgs("ref=20261115")) and at(15, 11, 30).weekday() == 6)
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('summary_wa.on', 'off')")
con.commit()
r = q(at(16, 11, 30))
con.execute("DELETE FROM setting WHERE key='summary_wa.on'")
con.commit()
ck("18 summary_wa.on = off: nothing on the 16th", not msgs("ref=20261116") and "off" in str(r.get("why")))
ck("18 never a September row, ever", not msgs("month='2026-09'"))

print("19 · S756: the cron shape -- owner_notice.py tick, as cron runs it (F-1207: S755's morning line runs too)")
stub = os.path.join(TMP, "notice_stub.jsonl")
env = dict(os.environ, OWNER_NOTICE_STUB=stub, SHARED_LIB_DIR=SHARED, ASSETS_DB=ADB, ORDER_TODAY="2026-11-17", OWNER_NOTICE_LOCK=os.path.join(TMP, "on.lock"),
           FINANCE_OFF_DIR=os.path.join(TMP, "_off"))
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('owner_notice.on', 'on')")
con.commit()
RUN = ("import runpy, sys; import purchase_app as PA; PA._assets_db = %r; "          # cron's shape: the FILE run as __main__ (runpy), cwd the code dir;
       "sys.argv = ['owner_notice.py', 'tick', '--db', %r, '--now', '2026-11-17T11:31:00']; "   # only the made-up assets.db path is set first
       "runpy.run_path('owner_notice.py', run_name='__main__')" % (ADB, FDB))
p = subprocess.run([sys.executable, "-B", "-c", RUN], cwd=CODE, env=env, capture_output=True, text=True, timeout=120)
line = (p.stdout or "").strip().splitlines()[-1:] or [""]
print("    (%s)" % line[0][:300])
told = open(stub, encoding="utf-8").read() if os.path.exists(stub) else ""
ck("19 the tick ran (exit 0) and queued the 17th's reminders", p.returncode == 0 and bool(msgs("ref=20261117")))
ck("19 S755's morning line was made from cron -- 'October 2026: N summaries awaited' (F-1207)", "summaries:2026-10:2026-11-17" in told and "summaries awaited" in told)
ck("19 the morning line's names carry no padding", "  " not in "".join(json.loads(x).get("body", "") for x in told.splitlines() if "summaries:" in x))

print("20 · S756: the cold review's cases -- nothing stale, nothing twice, nothing late")
def fresh(day):
    """A day's rows, made but not taken by the phone."""
    q(at(day, 11, 30))
    return msgs("ref=? AND status='queued' AND handed_at IS NULL", (int("202611%02d" % day),))
ok20 = fresh(20)
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('summary_wa.on', 'off')")
con.commit()
q(at(20, 11, 40))
con.execute("DELETE FROM setting WHERE key='summary_wa.on'")
con.commit()
ck("20 summary_wa.on = off withdraws today's unsent reminders too ('switched off')", ok20 and not msgs("ref=20261120 AND status='queued' AND handed_at IS NULL")
   and all(m["last_error"] in ("switched off", "number nahi") for m in msgs("ref=20261120") if m["status"] == "skipped"))
ok21 = fresh(21)
keep = PA._assets_db
PA._assets_db = os.path.join(TMP, "no-such-assets.db")
q(at(21, 11, 40))
PA._assets_db = keep
ck("20 assets.db unreadable withdraws today's unsent reminders ('assets.db unreadable')", ok21 and not msgs("ref=20261121 AND status='queued' AND handed_at IS NULL")
   and any(m["last_error"] == "assets.db unreadable" for m in msgs("ref=20261121")))
ok22 = fresh(22)
q(at(22, 20, 5))
ck("20 after 20:00 nothing is left for the phone ('too late in the day')", ok22 and not msgs("ref=20261122 AND status='queued' AND handed_at IS NULL")
   and any(m["last_error"] == "too late in the day" for m in msgs("ref=20261122")))
mbill("dee3", "DEEPAM PHARMA", "880", "2026-11-05", 1000)               # Deepam awaited for November too
os.environ["ORDER_TODAY"] = "2026-12-08"
q(dt.datetime(2026, 12, 8, 11, 30, tzinfo=IST))
os.environ["ORDER_TODAY"] = "2026-11-09"
d8 = msgs("ref=20261208")
dd = [m for m in d8 if m["vendor_norm"] == dee]
per = {}
for m in d8:
    per[m["vendor_norm"]] = per.get(m["vendor_norm"], 0) + 1
ck("20 a dealer awaited for two months gets ONE message a day, about the older month only", len(dd) == 1 and dd[0]["month"] == "2026-10"
   and "अक्टूबर 2026 के" in dd[0]["body"] and "नवंबर" not in dd[0]["body"] and max(per.values() or [0]) == 1)
ck("20 every row of the 8th names exactly its own month (so the re-check is exact)", bool(d8) and all(m["body"] == SR.s756_body(m["month"]) for m in d8))
os.environ["ORDER_TODAY"] = "2026-12-08"
summary(620, "DEEPAM PHARMA", "2026-10-31", [("bill", "641", "2026-10-03", 4751.0), ("bill", "702", "2026-10-21", 3230.0)], total=7981.0, closing=7981.0)
a.execute("UPDATE claude_reading SET doc_kind='summary' WHERE bill_id=620")
a.commit()
sd = 200 if (safe(SR.s750_dealers, con, "2026-10") and {d["key"]: d for d in SR.s750_dealers(con, "2026-10")}.get(dee, {}).get("state") == "agrees") else 0
q(dt.datetime(2026, 12, 8, 11, 40, tzinfo=IST))
w8 = [m for m in msgs("ref=20261208") if m["vendor_norm"] == dee]
q(dt.datetime(2026, 12, 9, 11, 30, tzinfo=IST))
n9 = [m for m in msgs("ref=20261209") if m["vendor_norm"] == dee]
os.environ["ORDER_TODAY"] = "2026-11-09"
ck("20 the older month settles (Deepam's October summary scanned, it agrees): the day's unsent October row is withdrawn at once",
   sd == 200 and w8 and (w8[0]["status"] == "sent" or w8[0]["last_error"] == "no longer awaited"))
ck("20 and the next day's message is about November, alone", len(n9) == 1 and n9[0]["month"] == "2026-11" and "नवंबर 2026 के" in n9[0]["body"]
   and "अक्टूबर" not in n9[0]["body"])
os.environ["ORDER_TODAY"] = "2026-11-09"
ok23 = fresh(23)
env3 = dict(env, ORDER_TODAY="2026-11-23")
os.makedirs(os.path.join(TMP, "_off"), exist_ok=True)
open(os.path.join(TMP, "_off", "ALL_OFF"), "w").write("walk")
RUN3 = ("import runpy, sys; import purchase_app as PA; PA._assets_db = %r; "
        "sys.argv = ['owner_notice.py', 'tick', '--db', %r, '--now', '2026-11-23T11:40:00']; "
        "runpy.run_path('owner_notice.py', run_name='__main__')" % (ADB, FDB))
p3 = subprocess.run([sys.executable, "-B", "-c", RUN3], cwd=CODE, env=env3, capture_output=True, text=True, timeout=120)
os.remove(os.path.join(TMP, "_off", "ALL_OFF"))
ck("20 ALL_OFF: cron's tick withdraws today's unsent reminders", ok23 and p3.returncode == 0 and not msgs("ref=20261123 AND status='queued' AND handed_at IS NULL")
   and any(str(m["last_error"]).startswith("switched off (ALL_OFF") for m in msgs("ref=20261123")))
ok24 = fresh(24)
q(at(25, 0, 5))
ck("20 the day turns: yesterday's unsent reminders are withdrawn 'superseded' (no backlog)", ok24 and not msgs("ref=20261124 AND status='queued' AND handed_at IS NULL")
   and all(m["last_error"] in ("superseded", "number nahi") for m in msgs("ref=20261124") if m["status"] == "skipped"))
ome = PA.supplier_key("OMEGA REMEDIES")
con.execute("UPDATE purchase_vendor_contact SET phone=(SELECT phone FROM purchase_vendor_contact WHERE vendor_norm=?) WHERE vendor_norm=?", (ome, dee))
con.commit()
q(at(26, 11, 30))
d26 = msgs("ref=20261126 AND to_number IS NOT NULL")
ck("20 two dealers on one number get ONE message that day", len(d26) == len({m["to_number"] for m in d26}) and len([m for m in d26 if m["vendor_norm"] in (dee, ome)]) == 1)
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('summary_wa.on', 'off')")
con.commit()
st, h, r7, r8 = rows7("2026-10")
con.execute("DELETE FROM setting WHERE key='summary_wa.on'")
con.commit()
ck("20 the snapshot says 'Reminders switched off' while the switch is off", "Reminders switched off" in h)
w_ = safe(getattr(SR, "s756_withdraw_all", None), con, "walk") or 0
ck("20 s756_withdraw_all (the restore and the undo use the same) leaves nothing for the phone", not msgs("status='queued' AND handed_at IS NULL"))

print("")
print("walk_s756: %d check(s) failed (%d of them S756 checks)" % (len(FAILS), len(S750F)))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILS else 0)
