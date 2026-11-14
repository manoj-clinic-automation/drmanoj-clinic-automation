#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s824.py -- S824_REVISED_BILL_SETASIDE (F-1378), on S740's MADE-UP root (no real data): the finance code to test (its .py files copied to a temp folder of
the walk's own, the schema beside them), a made-up finance.db and a made-up assets.db with made-up scan files.
    python3 -B walk_s740.py <finance code dir to test> <purchase_schema.sql> [<dir holding scan_quality.py>]
Run on the TO files: every check green.  CONTROL: on the live files (S738's TO + porders_s454 f683b7ed) every [S740] check goes red.
The last line: 'walk_s740: N check(s) failed (M of them S740 checks)'."""
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
TMP = tempfile.mkdtemp(prefix="s824walk_")
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
FAILS, S740F = [], []


def ck(name, cond, s740=True):
    print(("  ok   " if cond else "  FAIL ") + ("[S740] " if s740 else "") + name)
    if not cond:
        FAILS.append(name)
        if s740:
            S740F.append(name)


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


def scan(i, vendor, no, total, date, items, hours=48):
    at = ago(hours)
    a.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, "
              "source_stored) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (i, "B-%04d" % i, vendor, no, date, date[:7], total, at[:16], at, "read", "pharmacy", "captured", "Pharmacy", "s%d.pdf" % i))
    a.execute("INSERT INTO claude_reading VALUES (?,?,1,?)", (i, json.dumps(dict(bill_no=no, total_amount=total, vendor=vendor, doc_kind="tax_invoice",
                                                                          items=items)), at))
    open(os.path.join(UP, "s%d.pdf" % i), "wb").write(b"%PDF-1.4 made-up scan " + str(i).encode())
    a.commit()


scan(401, "YOGENDRA AGENCIES", "19612", 1575.0, "2026-10-07", [dict(name="ALPHA TAB", quantity=5, rate=315.0, amount=1575.0)])
scan(402, "JANTA PHARMACEUTICALS", "21965", 4450.0, "2026-10-02",
     [dict(name="BETA CAP", quantity=10, rate=200.5, amount=2005.0), dict(name="GAMMA SYP", quantity=4, rate=300.0, amount=1200.0),
      dict(name="ZETOMAX INJECTION", quantity=3, rate=415.0, amount=1245.0)])
scan(405, "TAU PHARMA", "T-1", 700.0, "2026-10-12", [dict(name="ZETA TAB", quantity=2, rate=350.0, amount=700.0)])
scan(406, "KEDAR PHARMACEUTICAL", "K-9", 2000.0, "2026-10-14", [dict(name="ETA GEL", quantity=4, rate=500.0, amount=2000.0)])
scan(412, "DELTA DRUGS", "D-3", 1300.0, "2026-10-15", [dict(name="THETA TAB", quantity=13, rate=100.0, amount=1300.0)])
scan(413, "MU MEDICOS", "M-1", 900.0, "2026-10-16", [dict(name="IOTA SYP", quantity=3, rate=300.0, amount=900.0)])
scan(416, "NU PHARMA", "N-2", 1100.0, "2026-10-17", [dict(name="OMICRON TAB", quantity=11, rate=100.0, amount=1100.0),
                                                      dict(name="RETURN OMICRON TAB", quantity=-3, rate=100.0, amount=-300.0)])
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
            "packing TEXT, mrp_p INTEGER, point_id INTEGER, void_at TEXT, void_why TEXT)"):
    con.execute(ddl)
for k, v in (("purchase.register_from", "2026-10-01"), ("purchase.parked_months", "2026-09"), ("porders.scan_from", "2026-09-01"),
             ("purchase.total_noise_rs", "10"), ("purchase.scan_file_users", "amir"), ("porders.senders", "reception,shavez,darpan")):
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
    con.commit()


def mline(supplier, no, date, item, qty, rate, packing="1*10"):
    con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, qty, rate_p, discount_pct, tax, direction, source_md5, "
                "line_type) VALUES (?,?,?,?,?,?,?,?,0,0,'PURCHASE','i0i0','BILLITEMWISE')",
                (PA.supplier_key(supplier), no, date, date[:7], item, packing, qty, int(round(rate * 100))))
    con.commit()


def link(bk, sid, paper_p=None, state=None):
    con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                (BID[bk], sid, "EXACT", "number + date", "2026-10-25T10:00:00"))
    con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (sid, BID[bk]))
    if paper_p is not None:
        con.execute("INSERT INTO purchase_scan_state (asset_bill_id, why, detail, checked_at, paper_amount, amount_state, confirmed_by, confirmed_at) "
                    "VALUES (?,?,?,?,?,?,?,?)", (sid, "linked", "linked", "2026-10-20T10:00:00", paper_p, state, "reception", "2026-10-20T10:00:00"))
    con.commit()


mbill("yog", "YOGENDRA AGENCIES", "19612", "2026-10-07", 2000)            # less: S738's, never a return question
mbill("jan", "JANTA PHARMACEUTICALS", "21965", "2026-10-02", 3205)        # more: the return written on the bill (the revised-bill road)
mline("JANTA PHARMACEUTICALS", "21965", "2026-10-02", "BETA CAPSULE", 10, 200.5)
mline("JANTA PHARMACEUTICALS", "21965", "2026-10-02", "GAMMA SYRUP", 4, 300.0)
mbill("tau", "TAU PHARMA", "T-1", "2026-10-12", 500)                     # more: reception says "Nahi"
mbill("ked", "KEDAR PHARMACEUTICAL", "K-9", "2026-10-14", 1500)           # more: the credit-note road
mbill("del", "DELTA DRUGS", "D-3", "2026-10-15", 1000)                   # more: the dealer takes it off a later bill
mbill("mu", "MU MEDICOS", "M-1", "2026-10-16", 600)                      # more: Marg reaches the paper by itself (the question leaves)
mbill("lk", "L.K. DRUG HOUSE", "6708", "2026-10-30", -2005)               # a purchase return from stock, in Marg, no paper yet
mbill("lksep", "L.K. DRUG HOUSE", "6115", "2026-09-15", -1862)            # September (parked): never a return here
mbill("nu", "NU PHARMA", "N-2", "2026-10-17", 800)                       # more: the return line is on the bill's OWN scan (never settles it)
mbill("lkd1", "L.K. DRUG HOUSE", "R-6800", "2026-10-22", -100)              # a purchase return entered twice in Marg
mbill("lkd2", "L.K. DRUG HOUSE", "r-6800", "2026-10-22", -100)
mbill("sig", "SIGMA MEDICOS", "S-77", "2026-10-11", 1200)                # bought ZUPRINOR 5 (one dealer only)
mline("SIGMA MEDICOS", "S-77", "2026-10-11", "ZUPRINOR 5", 2, 659.0, "1*1")
mbill("om1", "OMEGA REMEDIES", "O-1", "2026-10-03", 800)                  # TYRO BR from two dealers
mline("OMEGA REMEDIES", "O-1", "2026-10-03", "TYRO BR", 5, 185.0)
mline("SIGMA MEDICOS", "S-77", "2026-10-11", "TYRO BR", 5, 185.0)
link("yog", 401, 157500, "marg_wrong")
link("jan", 402, 445000, "marg_wrong")
link("tau", 405, 70000, "marg_wrong")
link("ked", 406, 200000, "marg_wrong")
link("del", 412, 130000, "marg_wrong")
link("mu", 413, 90000, "marg_wrong")
link("nu", 416, 110000, "marg_wrong")
con.execute("INSERT INTO stock_watch_loss_line (at, item, gap_units, pack, packing, mrp_p) VALUES ('2026-10-20T10:00:00', 'ZUPRINOR 5', 2, 1, '1*1', 131800)")
con.execute("INSERT INTO stock_watch_loss_line (at, item, gap_units, pack, packing, mrp_p) VALUES ('2026-10-20T10:00:00', 'TYRO BR', 121, 10, '1*10', 223850)")
con.execute("INSERT INTO stock_watch_loss_line (at, item, gap_units, pack, packing, mrp_p) VALUES ('2026-10-21T10:00:00', 'TYRO BR', 20, 10, '1*10', 37000)")
con.commit()

app = Flask("s740walk")
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


def model():
    getattr(SR, "_S740_MEMO", {}).clear()                     # the walk changes assets.db between reads: never a remembered model
    return safe(SR.s740_model, con) if hasattr(SR, "s740_model") else None


def ret(key_part):
    m = model() or {}
    return next((r for r in m.get("returns") or [] if key_part in r["key"]), None)


def jkey(k):
    b = con.execute("SELECT supplier_norm, bill_no, bill_date FROM purchase_bill WHERE id=?", (BID[k],)).fetchone()
    return "bill:%s|%s|%s" % (b[0], str(b[1]).strip().lower(), b[2])


if os.environ.get("S824_WALK_SEED_ONLY"):                    # the installer's rehearsal runs the proof and the seed on these
    _out = os.environ["S824_WALK_SEED_ONLY"]
    os.makedirs(_out, exist_ok=True)
    con.commit()
    shutil.copy(FDB, os.path.join(_out, "finance.db"))
    shutil.copy(ADB, os.path.join(_out, "assets.db"))
    shutil.copytree(UP, os.path.join(_out, "uploads"), dirs_exist_ok=True)
    print("walk_s824: seeded %s (finance.db, assets.db, uploads)" % _out)
    sys.exit(0)
print("1 · reception's one question")
m = model()
qs = {q["bill_id"]: q for q in (m or {}).get("questions") or []}
ck("1 the model reads", m is not None)
ck("1 asked for the bills whose paper reads MORE: Janta, Tau, Kedar, Delta, Mu, Nu (6)", sorted(qs) == sorted(BID[k] for k in ("jan", "tau", "ked", "del", "mu", "nu")))
ck("1 never for a paper reading LESS (Yogendra)", m is not None and BID["yog"] not in qs)
ck("1 Janta's question carries paper 4,450 / Marg 3,205 / the scan", (qs.get(BID["jan"]) or {}).get("paper_p") == 445000
   and (qs.get(BID["jan"]) or {}).get("marg_p") == 320500 and (qs.get(BID["jan"]) or {}).get("scan") == 402)
as_(RECEP, "sender")
st, h = get("/finance/porders/s454/billkaam")
ck("1 the page answers (200)", st == 200, s740=False)
ck("1 the group 'Ek sawaal · wapsi · 6' on Aaj ka bill kaam", "Ek sawaal · wapsi · 6" in h)
ck("1 the words: 'Bill par ya parchi par wapsi (return) likhi hai?' with Haan / Nahi", "Bill par ya parchi par wapsi (return) likhi hai?" in h
   and "Haan, wapsi likhi hai" in h and h.count('data-q740="') == 6)
ck("1 the card shows paper and Marg (Kaagaz par ₹4,450 · Marg mein ₹3,205) and the scan's photo", "Kaagaz par ₹4,450 · Marg mein ₹3,205" in h
   and "/scanapp/bills/402/file" in h)
ck("1 the L.K. purchase return in Marg reads 'Wapsi ka kaagaz (credit note)' with its size, never a minus figure",
   "Wapsi ka kaagaz (credit note) · L.K. DRUG HOUSE" in h and "−₹2,005" not in h and "₹2,005" in h)
ck("1 no 'all done' line while a question stands", 'id="alldone"' not in h and 'id="g_q740"' in h)
st, j = post("/finance/porders/api/s740/wapsi", dict(bill=BID["tau"], yes=False))
ck("1 Tau: 'Nahi' taken (200)", st == 200 and j.get("ok"))
st, j = post("/finance/porders/api/s740/wapsi", dict(bill=BID["tau"], yes=True))
ck("1 ... a second answer to the same bill is refused (409)", st == 409)
st, j = post("/finance/porders/api/s740/wapsi", dict(bill=BID["yog"], yes=True))
ck("1 an answer for a bill that is not a question is refused (409)", st == 409)
for k in ("ked", "del", "nu"):
    post("/finance/porders/api/s740/wapsi", dict(bill=BID[k], yes=True))
LOGIN["kind"] = "viewer"
st, j = post("/finance/porders/api/s740/wapsi", dict(bill=BID["mu"], yes=True))
ck("1 a view-only login cannot answer (403)", st == 403, s740=False)
as_(RECEP, "sender")
ck("1 answers audited (s740_answer: 4)", con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s740_answer'").fetchone()[0] == 4
   if con.execute("SELECT 1 FROM sqlite_master WHERE name='s740_answer'").fetchone() else False)

print("2 · the owner's word seeds Janta (D839)")
r_ = safe(SR.s740_seed, con, PA.supplier_key("JANTA PHARMACEUTICALS"), "21965", "2026-10-02", "manoj (D839, S740 seed)", "D839") if hasattr(SR, "s740_seed") else None
ck("2 seeded", r_ == "seeded")
ck("2 ... idempotent ('already')", (safe(SR.s740_seed, con, PA.supplier_key("JANTA PHARMACEUTICALS"), "21965", "2026-10-02", "x", "D839")
                                     if hasattr(SR, "s740_seed") else None) == "already")
ck("2 ... a bill that is not a question is never seeded", (safe(SR.s740_seed, con, PA.supplier_key("YOGENDRA AGENCIES"), "19612", "2026-10-07", "x", "t")
                                                            if hasattr(SR, "s740_seed") else None) == "not_a_question")
m = model()
qs = {q["bill_id"] for q in (m or {}).get("questions") or []}
ck("2 the question list is now Mu alone", qs == {BID["mu"]})
jr = ret(jkey("jan"))
ck("2 Janta is a pending return 'on_bill', ₹1,245, waiting for the dealer's paper", bool(jr) and jr["kind"] == "on_bill" and jr["amount_p"] == 124500
   and jr["stage"] == "waiting" and not jr["resolved"])

print("3 · the register and S738 carry a return once")
fx = {f["bill_id"]: f for f in (safe(SR.s738_fixes, con) or [])}
ck("3 S738's list keeps Yogendra (less) and Tau ('Nahi': more), drops Janta, Kedar, Delta (returns)", BID["yog"] in fx and BID["tau"] in fx
   and not ({BID["jan"], BID["ked"], BID["del"]} & set(fx)))
reg = safe(SR.register, con, "2026-10") or {"rows": []}
rj = next((x for x in reg["rows"] if x["id"] == BID["jan"]), {})
ck("3 the register's Janta row: whose 'Return: waiting for the dealer's paper', the note names the return", rj.get("whose") == "Return: waiting for the dealer's paper"
   and "A return of ₹1,245 is written on the paper" in (rj.get("note") or ""))
rl = next((x for x in reg["rows"] if x["id"] == BID["lk"]), {})
ck("3 the L.K. purchase return row is noted 'Purchase return (Marg)'", (rl.get("note") or "").startswith("Purchase return (Marg)."))
ck("3 porders' amount question is never raised for a purchase return (S440 would mark it WRONG at a plus figure); a bill's is as before",
   not porders._s440_differs(200500, -200500, "2026-10") and not porders._s440_differs(190000, -200500, "2026-10")
   and porders._s440_differs(190000, 200500, "2026-10"))

print("4 · Amir's page")
as_(AMIR)
st, h = get("/finance/amir/step/1")
ck("4 his page answers (200)", st == 200, s740=False)
ck("4 'Wapsi baaki · 6' (Janta, Kedar, Delta, Nu, L.K. 6708, L.K. R-6800 entered twice)", "Wapsi baaki &middot; 6" in h)
ck("4 Janta waits: 'Dealer ka credit note ya naya bill aane par hi Marg mein badlaav kijiye.'", "Dealer ka credit note ya naya bill aane par hi Marg mein badlaav kijiye." in h
   and "wapsi &#8377;1,245" in h)
ck("4 L.K.: 'Wapsi Marg mein hai (purchase return 6708). Dealer ka kaagaz (credit note) scan hona baaki hai.'",
   "Wapsi Marg mein hai (purchase return 6708). Dealer ka kaagaz (credit note) scan hona baaki hai." in h)
ck("4 Tau ('Nahi'): S738's card says only add the line ('Bill ki yeh line Marg mein nahi hai. Jodiye, aur Marg mein bill ₹700 kijiye.')",
   "Bill ki yeh line Marg mein nahi hai. Jodiye, aur Marg mein bill &#8377;700 kijiye." in h)
ck("4 S738's old both-roads sentence is gone from his page", "poora bill aur purchase return" not in h)
ck("4 Mu (unanswered): 'Reception se poochha gaya hai ... Wapsi ho to abhi Marg mat badaliye'", "Reception se poochha gaya hai ki bill par wapsi likhi hai ya nahi" in h)
ck("4 'Kaagaz dekhiye' on Janta's return opens its scan through the door", "/finance/purchase/api/s738/scan/402" in h.split("id=s740>")[-1] and "id=s740>" in h)
st, _h = get("/finance/purchase/api/s738/scan/402")
ck("4 ... and the door lets Amir open it (200)", st == 200, s740=False)
nt = con.execute("SELECT COUNT(*) FROM s740_track").fetchone()[0] if con.execute("SELECT 1 FROM sqlite_master WHERE name='s740_track'").fetchone() else -1
ck("4 his page kept the tracker (s740_track: 6 rows)", nt == 6)
S = safe(AD.state, con, AD._today(), "amir")
ck("4 nothing for him to enter yet: the card is not his line ('returns pending: 6 (0 to enter)')", bool(S) and any(r[0] == "s740" and r[3] is False
   and r[2] == "returns pending: 6 (0 to enter)" for r in S.card))

nr = ret(jkey("nu"))
ck("4 Nu: a return line on the bill's OWN scan never settles its own return (still waiting)", bool(nr) and nr["stage"] == "waiting" and not nr["resolved"])
dd = [r for r in (model() or {}).get("returns") or [] if r["kind"] == "marg" and r["bill_no"].lower() == "r-6800"]

ck("4 L.K. R-6800 entered twice in Marg: ONE return, 'double'; Amir's S738 list keeps it (remove one)", len(dd) == 1 and dd[0]["stage"] == "double"
   and any(f.get("kind") == "double" for f in (safe(SR.s738_fixes, con) or [])))
# ---------------------------------------------------------------- S824 (F-1378): a revised bill the scan app SET ASIDE as a second scan
# Steps 1-4 above are S740's own walk, unchanged (they must stay green on the new file). Step 5 is S824's.
S824F = []


def ck8(name, cond):
    print(("  ok   " if cond else "  FAIL ") + "[S824] " + name)
    if not cond:
        FAILS.append(name)
        S824F.append(name)


def aside(i, vendor, no, total, date, dup, page=None, hours=5):
    at = ago(hours)
    a.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, "
              "source_stored, dup_of, page_of) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (i, "B-%04d" % i, vendor, no, date, date[:7], total, at[:16], at, "read", "pharmacy", "rejected", "Pharmacy", "s%d.pdf" % i, dup, page))
    a.commit()


def jstage():
    jr_ = ret(jkey("jan")) or {}
    return jr_.get("stage"), bool(jr_.get("resolved")), jr_.get("road"), jr_.get("ref")


def others():
    return {r["key"]: (r.get("stage"), bool(r.get("resolved")), r.get("road")) for r in (model() or {}).get("returns") or [] if r["key"] != jkey("jan")}


print("5 · S824: the dealer's revised bill set aside as a 'second scan'")
base = others()
ck8("5 Janta is waiting before any set-aside scan", jstage()[:2] == ("waiting", False))
ck8("5 the reader exists and reads nothing yet", (safe(SR.s824_set_aside, con) if hasattr(SR, "s824_set_aside") else None) == {})
aside(409, "JANTA PHARMACEUTICALS", "21965", 4450.0, "2026-10-02", dup=402)          # a TRUE double: the paper's own amount
ck8("5a a true double (B-0409, Rs 4,450 = the paper) settles nothing", jstage()[:2] == ("waiting", False))
aside(410, "JANTA PHARMACEUTICALS", "21965", 3205.0, "2026-10-02", dup=402, page=402)  # a page of a bill, not a bill
ck8("5b a set-aside PAGE of a bill (page_of set) settles nothing", jstage()[:2] == ("waiting", False))
aside(411, "KEDAR PHARMACEUTICAL", "21965", 3205.0, "2026-10-02", dup=402)           # another dealer
ck8("5c another dealer's set-aside scan settles nothing", jstage()[:2] == ("waiting", False))
aside(413 + 7, "JANTA PHARMACEUTICALS", "21966", 3205.0, "2026-10-02", dup=402)      # another bill number
ck8("5d a set-aside scan of another bill number settles nothing", jstage()[:2] == ("waiting", False))
aside(408, "JANTA PHARMACEUTICALS", "21965", 3205.0, "2026-10-02", dup=402)          # THE revised bill, set aside by a 'same paper' answer
con.execute("UPDATE purchase_bill SET amount_p=445000 WHERE id=?", (BID["jan"],)); con.commit()     # Marg NOT at the revised figure
ck8("5e0 Marg not at the revised figure: a set-aside scan settles nothing (never Amir's 'set Marg to' from a scan he cannot open)",
    jstage()[:2] != ("resolved", True) and (ret(jkey("jan")) or {}).get("stage") != "do_revised")
con.execute("UPDATE purchase_bill SET amount_p=320500 WHERE id=?", (BID["jan"],)); con.commit()
sa = safe(SR.s824_set_aside, con) if hasattr(SR, "s824_set_aside") else None
ck8("5e the reader returns the four set-aside bills, never the page (408, 409, 411, 420)", sorted(sa or {}) == [408, 409, 411, 420])
st8 = jstage()
ck8("5e Janta SETTLED by the set-aside revised bill B-0408 (road revised, Marg at Rs 3,205)", st8 == ("resolved", True, "revised", "B-0408"))
jr = ret(jkey("jan")) or {}
ck8("5e ... its words name the scan ('the dealer revised the bill to ₹3,205 (scan B-0408)')", "(scan B-0408)" in str(jr.get("en") or ""))
ck8("5e ... no link is offered to a set-aside scan (the door serves captured scans only)", not jr.get("revised"))
ck8("5e every other return reads exactly as before", others() == base)
reg = safe(SR.register, con, "2026-10") or {"rows": []}
rj = next((x for x in reg["rows"] if x["id"] == BID["jan"]), {})
ck8("5e the register's Janta row is no longer 'waiting for the dealer's paper'", rj.get("whose") != "Return: waiting for the dealer's paper" and bool(rj))
as_(AMIR)
st, h = get("/finance/amir/step/1")
ck8("5e Amir's page answers and never links scan 408", st == 200 and "/finance/purchase/api/s738/scan/408" not in h)
ck8("5e ... and his 'Wapsi baaki' drops Janta (6 -> 5)", "Wapsi baaki &middot; 5" in h)
as_(RECEP, "sender")
scan(421, "JANTA PHARMACEUTICALS", "21965", 3205.0, "2026-10-02", [dict(name="BETA CAP", quantity=10, rate=200.5, amount=2005.0)], hours=1)
ck8("5f a CAPTURED revised scan is tried first (ref B-0421)", jstage() == ("resolved", True, "revised", "B-0421"))
keep_db = PA._assets_db
PA._assets_db = os.path.join(TMP, "no_such_assets.db")
ck8("5g the assets store unreachable: the reader gives {} and never raises", (safe(SR.s824_set_aside, con) if hasattr(SR, "s824_set_aside") else None) == {})
ck8("5g ... and the model still reads", model() is not None)
PA._assets_db = keep_db
print("walk_s824: %d check(s) failed (%d of them S824 checks, %d S740 checks)" % (len(FAILS), len(S824F), len(S740F)))
sys.exit(1 if FAILS else 0)
