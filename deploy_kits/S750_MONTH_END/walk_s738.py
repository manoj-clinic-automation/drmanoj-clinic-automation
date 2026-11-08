#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s738.py -- S738_AMIR_CORRECTIONS on a MADE-UP root (no real data): the finance code to test (its .py files copied to a temp folder of
the walk's own, the schema beside them), a made-up finance.db and a made-up assets.db with made-up scan files.
    python3 -B walk_s738.py <finance code dir to test> <purchase_schema.sql> [<dir holding scan_quality.py>]
Run on the TO files: every check green.  CONTROL: on the live files (scan_register 4d8432ea, amir_day 10a5f9c4, purchase_app 5fde52aa) every
[S738] check goes red.  The last line: 'walk_s738: N check(s) failed (M of them S738 checks)'."""
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
TMP = tempfile.mkdtemp(prefix="s738walk_")
_code = os.path.join(TMP, "code")
os.makedirs(_code)
for _n in os.listdir(CODE):
    if _n.endswith(".py") and os.path.isfile(os.path.join(CODE, _n)):
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
FAILS, S738F = [], []


def ck(name, cond, s738=True):
    print(("  ok   " if cond else "  FAIL ") + ("[S738] " if s738 else "") + name)
    if not cond:
        FAILS.append(name)
        if s738:
            S738F.append(name)


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
  source_stored TEXT, doc_kind TEXT);
CREATE TABLE claude_reading (bill_id INTEGER, data TEXT, ok INTEGER, at TEXT);
CREATE TABLE scan_lie (bill_id INTEGER, file TEXT, at TEXT, legible INTEGER, whole_bill INTEGER, totals_visible INTEGER, blur_kept INTEGER);
CREATE TABLE settings (key TEXT, value TEXT);
""")


def scan(i, vendor, no, total, date, items):
    at = ago(48)
    a.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, "
              "source_stored) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (i, "B-%04d" % i, vendor, no, date, date[:7], total, at[:16], at, "read", "pharmacy", "captured", "Pharmacy", "s%d.pdf" % i))
    a.execute("INSERT INTO claude_reading VALUES (?,?,1,?)", (i, json.dumps(dict(bill_no=no, total_amount=total, vendor=vendor, doc_kind="tax_invoice",
                                                                          items=items)), at))
    open(os.path.join(UP, "s%d.pdf" % i), "wb").write(b"%PDF-1.4 made-up scan " + str(i).encode())


scan(401, "YOGENDRA AGENCIES", "19612", 1575.0, "2026-10-07", [dict(name="ALPHA TAB", quantity=5, rate=315.0, amount=1575.0)])
scan(402, "JANTA PHARMACEUTICALS", "21965", 4450.0, "2026-10-02",
     [dict(name="BETA CAP", quantity=10, rate=200.5, amount=2005.0), dict(name="GAMMA SYP", quantity=4, rate=300.0, amount=1200.0),
      dict(name="ZETOMAX INJECTION", quantity=3, rate=415.0, amount=1245.0)])
scan(403, "OMEGA REMEDIES", "O-55", 900.0, "2026-10-09", [dict(name="DELTA GEL", quantity=3, rate=300.0, amount=900.0)])
scan(404, "SIGMA MEDICOS", "S-77", 1200.0, "2026-10-11", [dict(name="EPS TAB", quantity=1, rate=1200.0, amount=1200.0)])
scan(405, "TAU PHARMA", "T-1", 700.0, "2026-10-12", [dict(name="ZETA TAB", quantity=2, rate=350.0, amount=700.0)])   # paper more, lines unclear
a.commit()
a.close()
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
            "CREATE TABLE IF NOT EXISTS s454_paper_missing (bill_id INTEGER PRIMARY KEY, by TEXT, at TEXT NOT NULL, accepted_by TEXT, accepted_at TEXT)"):
    con.execute(ddl)
for k, v in (("purchase.register_from", "2026-10-01"), ("purchase.parked_months", "2026-09"), ("porders.scan_from", "2026-09-01"),
             ("purchase.total_noise_rs", "10"), ("purchase.scan_file_users", "amir")):
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?,?)", (k, v))
con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows) VALUES "
            "('e0e0', 'BILLWISE', 'walk.xls', '2026-09-01', '2026-11-30', '20261106-100000', '2026-11-06T10:00:00', 1)")
con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows) VALUES "
            "('i0i0', 'BILLITEMWISE', 'walki.xls', '2026-09-01', '2026-11-30', '20261106-100000', '2026-11-06T10:00:00', 1)")
BID = {}


def mbill(key, supplier, no, date, rs_):
    cur = con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, first_seen_day) VALUES (?,?,?,?,?,?,?,?)",
                      (PA.supplier_key(supplier), supplier, no, date, date[:7], int(round(rs_ * 100)), "e0e0", date))
    BID[key] = cur.lastrowid


def mline(supplier, no, date, item, qty, rate):
    con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, qty, rate_p, discount_pct, tax, direction, source_md5, line_type) "
                "VALUES (?,?,?,?,?,?,?,0,0,'PURCHASE','i0i0','BILLITEMWISE')", (PA.supplier_key(supplier), no, date, date[:7], item, qty, int(round(rate * 100))))


def link(bk, sid, paper_p=None, state=None):
    con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                (BID[bk], sid, "EXACT", "number + date", "2026-10-25T10:00:00"))
    con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (sid, BID[bk]))
    if paper_p is not None:
        con.execute("INSERT INTO purchase_scan_state (asset_bill_id, why, detail, checked_at, paper_amount, amount_state, confirmed_by, confirmed_at) "
                    "VALUES (?,?,?,?,?,?,?,?)", (sid, "linked", "linked", "2026-10-20T10:00:00", paper_p, state, "reception", "2026-10-20T10:00:00"))


mbill("yog", "YOGENDRA AGENCIES", "19612", "2026-10-07", 2000)            # Marg 2,000 · the paper 1,575: Rs 425 less
mbill("jan", "JANTA PHARMACEUTICALS", "21965", "2026-10-02", 3205)        # Marg 3,205 · the paper 4,450: one line Marg lacks (Rs 1,245)
mline("JANTA PHARMACEUTICALS", "21965", "2026-10-02", "BETA CAPSULE", 10, 200.5)
mline("JANTA PHARMACEUTICALS", "21965", "2026-10-02", "GAMMA SYRUP", 4, 300.0)
mbill("dbl1", "OMEGA REMEDIES", "O-55", "2026-10-09", 900)               # entered twice ("O-55" and "o-55")
mbill("dbl2", "OMEGA REMEDIES", "o-55", "2026-10-09", 900)
mbill("ok", "SIGMA MEDICOS", "S-77", "2026-10-11", 1200)                 # agrees: never on the list
mbill("tau", "TAU PHARMA", "T-1", "2026-10-12", 500)                     # Marg 500 · the paper 700, no line to name
link("yog", 401, 157500, "marg_wrong")
link("jan", 402, 445000, "marg_wrong")
link("dbl1", 403)
link("ok", 404)
link("tau", 405, 70000, "marg_wrong")
con.commit()

app = Flask("s738walk")
WHO = {"u": dict(user="manoj", username="manoj", role="checker", roles=["checker"])}


def require_stub(*roles, **kw):
    u = WHO["u"]
    if u is None or not set(u.get("roles") or []).intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return u, None


PA.init(app, lambda: con, require_stub, url_prefix="/finance/purchase", assets_db=ADB)
AD.init(app, lambda: con, require_stub, unit="medical")
porders._db = lambda: con
cl = app.test_client()
OWNER = dict(user="manoj", username="manoj", role="checker", roles=["checker"])
AMIR = dict(user="amir", username="amir", role="viewer", roles=["viewer"])
OTHER = dict(user="darpan", username="darpan", role="maker", roles=["maker"])


def get(path):
    r = cl.get(path, follow_redirects=True)
    return r.status_code, r.get_data(as_text=True), r


if os.environ.get("S738_WALK_SEED_ONLY"):                    # the installer's rehearsal runs the proof on these
    _out = os.environ["S738_WALK_SEED_ONLY"]
    os.makedirs(_out, exist_ok=True)
    con.commit()
    shutil.copy(FDB, os.path.join(_out, "finance.db"))
    shutil.copy(ADB, os.path.join(_out, "assets.db"))
    shutil.copytree(UP, os.path.join(_out, "uploads"), dirs_exist_ok=True)
    print("walk_s738: seeded %s (finance.db, assets.db, uploads)" % _out)
    sys.exit(0)
print("1 · the list of Amir's corrections")
fx = safe(SR.s738_fixes, con) if hasattr(SR, "s738_fixes") else None
by = {f["bill_id"]: f for f in (fx or [])}
ck("1 the list reads", fx is not None)
y = by.get(BID["yog"]) or {}
ck("1 Yogendra 19612: 'less' -- Marg 2,000, the paper 1,575, Rs 425", y.get("kind") == "less" and y.get("marg_p") == 200000 and y.get("paper_p") == 157500
   and y.get("diff_p") == -42500 and y.get("date") == "2026-10-07" and y.get("stamp") == "B-0401")
j = by.get(BID["jan"]) or {}
ck("1 Janta 21965: 'more' with the one line Marg lacks (ZETOMAX INJECTION, 3, Rs 1,245)", j.get("kind") == "more" and len(j.get("items") or []) == 1
   and (j["items"][0]["name"], j["items"][0]["amount_p"]) == ("ZETOMAX INJECTION", 124500))
t = by.get(BID["tau"]) or {}
ck("1 Tau T-1: 'more' with no line named (nothing adds up to Rs 200)", t.get("kind") == "more" and not t.get("items"))
d = by.get(BID["dbl1"]) or by.get(BID["dbl2"]) or {}
ck("1 Omega O-55: entered twice, both numbers named", d.get("kind") == "double" and sorted(x.lower() for x in d.get("numbers") or []) == ["o-55", "o-55"])
ck("1 Sigma S-77 (agrees) is not on the list", fx is not None and BID["ok"] not in by)
ck("1 four corrections in all", len(fx or []) == 4)

print("2 · Amir's page")
WHO["u"] = AMIR
st, h, _r = get("/finance/amir/step/1")
ck("2 his page answers (200)", st == 200, s738=False)
ck("2 the card: 'Purchase bill Marg mein theek karein · 4'", "Purchase bill Marg mein theek karein &middot; 4" in h)
ck("2 each card carries 'Bill ki tareekh' (07-10-2026 for Yogendra)", "Bill ki tareekh: 07-10-2026" in h and h.count("Bill ki tareekh:") == 4)
ck("2 Yogendra: Marg ₹2,000 · kaagaz par ₹1,575 — ₹425 kam · Marg mein bill ₹1,575 kijiye",
   "Marg mein &#8377;2,000 &middot; kaagaz par &#8377;1,575 &mdash; <b class=bad>&#8377;425 kam</b>" in h and "Marg mein bill &#8377;1,575 kijiye" in h)
ck("2 Janta: the line Marg lacks, and both roads (return / add the line)", "ZETOMAX INJECTION" in h and "Bill par yeh item hain, Marg mein nahi" in h and
   "poora bill aur purchase return" in h)
ck("2 Omega: 'Marg mein ek entry hataiye'", "Marg mein ek entry hataiye" in h)
ck("2 'Kaagaz dekhiye' opens the scan through the S738 door", "/finance/purchase/api/s738/scan/401" in h and "Kaagaz dekhiye" in h)
ck("2 no 'export again' / 'check' sentence on his card (D708)", "Purchase bill Marg mein theek karein" in h and not re.search(r"(?i)dobara export|check kijiye|jaanch", h))
ck("2 the back-to-top link (no JavaScript)", "id=s738up" in h and "href='#'" in h)
n_fix = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='s738_fix'").fetchone()[0]
ck("2 his page kept the list (s738_fix: 4 rows)", n_fix == 1 and con.execute("SELECT COUNT(*) FROM s738_fix").fetchone()[0] == 4)

print("3 · the scan door")
st, h3, r3 = get("/finance/purchase/api/s738/scan/401")
ck("3 Amir opens a scan on his list: 200, PDF, inline", st == 200 and r3.mimetype == "application/pdf" and r3.headers.get("Content-Disposition", "").startswith("inline"))
st, h3, r3 = get("/finance/purchase/api/s738/scan/404")
ck("3 Amir is refused a scan not on his list (403)", st == 403)
WHO["u"] = OTHER
st, h3, r3 = get("/finance/purchase/api/s738/scan/401")
ck("3 another staff login is refused (403)", st == 403)
WHO["u"] = OWNER
st, h3, r3 = get("/finance/purchase/api/s738/scan/404")
ck("3 the doctor opens any scan (200, PDF)", st == 200 and r3.mimetype == "application/pdf")

print("4 · the owner's step view")
before = [tuple(r) for r in con.execute("SELECT * FROM s738_fix ORDER BY bill_id")] if n_fix else []
na = con.execute("SELECT COUNT(*) FROM purchase_audit").fetchone()[0]
st, h, _r = get("/finance/purchase/page/check?month=2026-10")
ck("4 the step view answers (200)", st == 200, s738=False)
ck("4 each scanned line carries the bill date and its scan (Yogendra: 07-10-2026 · scan B-0401)",
   '<span class="c1">YOGENDRA AGENCIES 19612</span><span class="c2">07-10-2026</span><span class="c3">scan B-0401</span>' in h)
ck("4 a folded 'Show scan' on each scanned line, loading /api/s738/scan/<id> only when opened", h.count('<details class="s738v"') >= 4 and
   'data-src="/finance/purchase/api/s738/scan/401"' in h and "<iframe" not in h.split("<script>")[0])
ck("4 beside the scan: what it read against Marg (Total ₹1,575 · ₹2,000; the paper amount given)", "<tr><th>Total</th><td>₹1,575</td><td>₹2,000</td></tr>" in h
   and "Paper amount given" in h)
ck("4 row 3 'Differences' says since when it is on Amir's list", "on Amir&#x27;s list since" in h or "on Amir's list since" in h)
ck("4 the back-to-top button", 'id="s738up"' in h)
ck("4 the PC layout (wide column, grid lines) and the phone fallback", "#s726chk{max-width:1100px}" in h and "@media(min-width:900px)" in h)
ck("4 the GET wrote nothing", bool(n_fix) and [tuple(r) for r in con.execute("SELECT * FROM s738_fix ORDER BY bill_id")] == before and
   con.execute("SELECT COUNT(*) FROM purchase_audit").fetchone()[0] == na)

print("5 · proof by his own export")
con.execute("UPDATE purchase_bill SET amount_p=157500 WHERE id=?", (BID["yog"],))          # his correction, as the next bill-wise export carries it
con.execute("UPDATE purchase_export SET received_at='2026-11-07T09:30:00' WHERE md5='e0e0'")
con.commit()
WHO["u"] = AMIR
st, h, _r = get("/finance/amir/step/1")
ck("5 Yogendra has left his card (3 left)", "Purchase bill Marg mein theek karein &middot; 3" in h and "YOGENDRA AGENCIES" not in h.split("Purchase bill Marg")[1].split("</div></div>")[0][:4000])
row = con.execute("SELECT settled_at, settled_export FROM s738_fix WHERE bill_id=?", (BID["yog"],)).fetchone() if n_fix else None
ck("5 ... proved: s738_fix settled, with the export's arrival 2026-11-07T09:30:00", bool(row) and row[0] and row[1] == "2026-11-07T09:30:00")
ck("5 ... audited (s738_fix_proved)", con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s738_fix_proved'").fetchone()[0] == 1)
ck("5 his green line: 'Pichhli visit ke sudhar Marg mein mil gaye ✓ · 1'", "Pichhli visit ke sudhar Marg mein mil gaye &#10003; &middot; 1" in h)
WHO["u"] = OWNER
st, h, _r = get("/finance/purchase/page/check?month=2026-10")
ck("5 the owner's row 3: Yogendra 'corrected — his export of 07-11 shows Marg = the paper ✓'", "corrected — his export of 07-11 shows Marg = the paper ✓" in h)
st, h3, r3 = get("/finance/purchase/api/s738/scan/401")
ck("5 the doctor still opens the scan (200)", st == 200)
WHO["u"] = AMIR
st, h3, r3 = get("/finance/purchase/api/s738/scan/401")
ck("5 Amir no longer opens it -- not on his list now (403)", st == 403)
con.execute("UPDATE purchase_bill SET amount_p=200000 WHERE id=?", (BID["yog"],))          # a later export undoes it
con.commit()
st, h, _r = get("/finance/amir/step/1")
row = con.execute("SELECT settled_at FROM s738_fix WHERE bill_id=?", (BID["yog"],)).fetchone() if n_fix else None
ck("5 a later export undoing it puts it back on his card, open again", "Purchase bill Marg mein theek karein &middot; 4" in h and bool(row) and row[0] is None)

con.execute("UPDATE purchase_scan_state SET paper_amount=50000, amount_state='scan_wrong' WHERE asset_bill_id=405")   # reception re-typed Marg's figure
con.commit()
st, h, _r = get("/finance/amir/step/1")
row = con.execute("SELECT settled_at, gone_at FROM s738_fix WHERE bill_id=?", (BID["tau"],)).fetchone() if n_fix else None
ck("5 a line that left because reception re-typed the amount is NOT credited to Amir (gone, not settled)", bool(row) and row[0] is None and row[1] is not None)
_orig_reg = SR.register


def _boom(c, m):
    if m == "2026-10":
        raise RuntimeError("made-up fault")
    return _orig_reg(c, m)


SR.register = _boom
snap = [tuple(r) for r in con.execute("SELECT * FROM s738_fix ORDER BY bill_id")] if n_fix else []
st, h, _r = get("/finance/amir/step/1")
ck("5 a month that cannot be read: nothing synced, nothing proved", bool(n_fix) and [tuple(r) for r in con.execute("SELECT * FROM s738_fix ORDER BY bill_id")] == snap
   and st == 200)
SR.register = _orig_reg
ck("5 a negative amount prints right on his card (-12345 -> -123.45)", hasattr(AD, "_s738_rs") and AD._s738_rs(-12345) == "-123.45")

print("6 · his day")
WHO["u"] = AMIR
S = safe(AD.state, con, AD._today(), "amir")
ck("6 the card holds his day as Marg work (step 6's tick)", bool(S) and getattr(S, "card_has_his_line", False) and any(r[0] == "s738" for r in S.card))
ck("6 the owner's English line names it ('purchase bill corrections: 3')", bool(S) and any(r[2] == "purchase bill corrections: 3" for r in S.card))

if os.environ.get("S738_WALK_PAGES"):                        # the pages as drawn, for a reviewer's eyes
    _pd = os.environ["S738_WALK_PAGES"]
    os.makedirs(_pd, exist_ok=True)
    WHO["u"] = AMIR
    open(os.path.join(_pd, "amir_step1.html"), "w").write(get("/finance/amir/step/1")[1])
    WHO["u"] = OWNER
    open(os.path.join(_pd, "owner_check.html"), "w").write(get("/finance/purchase/page/check?month=2026-10")[1])
n_s = len(S738F)
print("walk_s738: %d check(s) failed (%d of them S738 checks)" % (len(FAILS), n_s))
sys.exit(1 if FAILS else 0)
