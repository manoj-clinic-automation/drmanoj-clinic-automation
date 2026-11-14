#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s740.py -- S740_PURCHASE_RETURNS on a MADE-UP root (no real data): the finance code to test (its .py files copied to a temp folder of
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
TMP = tempfile.mkdtemp(prefix="s740walk_")
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


if os.environ.get("S740_WALK_SEED_ONLY"):                    # the installer's rehearsal runs the proof and the seed on these
    _out = os.environ["S740_WALK_SEED_ONLY"]
    os.makedirs(_out, exist_ok=True)
    con.commit()
    shutil.copy(FDB, os.path.join(_out, "finance.db"))
    shutil.copy(ADB, os.path.join(_out, "assets.db"))
    shutil.copytree(UP, os.path.join(_out, "uploads"), dirs_exist_ok=True)
    print("walk_s740: seeded %s (finance.db, assets.db, uploads)" % _out)
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
print("5 · the roads")
scan(408, "JANTA PHARMACEUTICALS", "21965", 3205.0, "2026-10-02", [dict(name="BETA CAP", quantity=10, rate=200.5, amount=2005.0),
                                                                    dict(name="GAMMA SYP", quantity=4, rate=300.0, amount=1200.0)], hours=5)
jr = ret(jkey("jan"))
ck("5 Janta: the dealer's REVISED bill (scan B-0408, ₹3,205) with Marg at ₹3,205 settles it", bool(jr) and jr["resolved"] and jr["road"] == "revised"
   and jr["ref"] == "B-0408")
reg = safe(SR.register, con, "2026-10") or {"rows": []}
rj = next((x for x in reg["rows"] if x["id"] == BID["jan"]), {})
ck("5 ... the register's Janta row is settled (has its scan, Nobody)", rj.get("state") == "has_scan" and rj.get("whose") == "Nobody")
scan(420, "KEDAR PHARMACEUTICAL", "CN-5", -500.0, "2026-10-20", [dict(name="RETURN ETA GEL", quantity=-1, rate=500.0, amount=-500.0)], hours=4)
kr = ret(jkey("ked"))
ck("5 Kedar waits -- its credit note scanned with minus lines BEFORE Marg's entry settles nothing", bool(kr) and kr["stage"] == "waiting" and not kr["resolved"])
mbill("kcn", "KEDAR PHARMACEUTICAL", "CN-5", "2026-10-20", -500)
kr = ret(jkey("ked"))
ck("5 Kedar: the credit note in Marg, the bill still net -> Amir 'Ab Marg mein bill ₹2,000 kijiye (poora bill)'", bool(kr) and kr["stage"] == "do_full"
   and "Ab Marg mein bill &#8377;2,000 kijiye (poora bill)" in kr.get("hi", ""))
con.execute("UPDATE purchase_bill SET amount_p=200000 WHERE id=?", (BID["ked"],))
con.commit()
kr = ret(jkey("ked"))
ck("5 ... full bill in Marg: the credit note's paper is reception's", bool(kr) and kr["stage"] == "paper" and kr.get("whose") == "Return: reception scans the credit note")
ck("5 ... the credit note is not a second return ('marg' kind absent for CN-5)", bool(kr) and ret("mret:%s|cn-5" % PA.supplier_key("KEDAR PHARMACEUTICAL")) is None)
scan(407, "KEDAR PHARMACEUTICAL", "CN-5", 500.0, "2026-10-20", [dict(name="ETA GEL", quantity=1, rate=500.0, amount=500.0)], hours=3)
link("kcn", 407)
kr = ret(jkey("ked"))
ck("5 ... its paper scanned and agreeing (by its size): settled by the credit note", bool(kr) and kr["resolved"] and kr["road"] == "credit" and kr["ref"] == "CN-5")
dr = ret(jkey("del"))
ck("5 Delta waits", bool(dr) and dr["stage"] == "waiting")
scan(414, "DELTA DRUGS", "D-8", 1700.0, "2026-10-28", [dict(name="KAPPA TAB", quantity=20, rate=100.0, amount=2000.0),
                                                        dict(name="LESS: RETURN D-3", quantity=1, rate=-300.0, amount=-300.0)], hours=2)
dr = ret(jkey("del"))
ck("5 Delta: the dealer took ₹300 off a later bill D-8 (scan B-0414), not yet in Marg -> Amir: enter D-8 at the goods' ₹2,000", bool(dr) and not dr["resolved"]
   and dr["stage"] == "do_goods" and "&#8377;2,000 (poora maal)" in dr.get("hi", ""))
mbill("d8", "DELTA DRUGS", "D-8", "2026-10-28", 1700)                    # Amir entered D-8 at the paper's net figure: the return counted twice
link("d8", 414)
dr = ret(jkey("del"))
reg = safe(SR.register, con, "2026-10") or {"rows": []}
r8 = next((x for x in reg["rows"] if x["id"] == BID["d8"]), {})
ck("5 ... D-8 in Marg at the net ₹1,700: Amir is told to set it to ₹2,000; its register row is the return's (not 'all clear')",
   bool(dr) and dr["stage"] == "do_goods" and "Marg mein yeh bill &#8377;2,000" in dr.get("hi", "") and r8.get("state") == "amount_differs"
   and r8.get("whose") == "Return: Amir enters it in Marg")
con.execute("UPDATE purchase_bill SET amount_p=205000 WHERE id=?", (BID["d8"],))
con.commit()
model()
ck("5 ... D-8 at ₹2,050 (not the goods): Amir's card says ₹2,000, and S440 never asks reception (no WRONG mark at ₹1,700)",
   (ret(jkey("del")) or {}).get("stage") == "do_goods" and not porders._s440_differs(170000, 205000, "2026-10"))
con.execute("UPDATE purchase_bill SET amount_p=200000 WHERE id=?", (BID["d8"],))
con.commit()
dr = ret(jkey("del"))
reg = safe(SR.register, con, "2026-10") or {"rows": []}
r8 = next((x for x in reg["rows"] if x["id"] == BID["d8"]), {})
ck("5 Delta: D-8 at the goods' ₹2,000 in Marg -- settled (road 'adjusted', B-0414)", bool(dr) and dr["resolved"] and dr["road"] == "adjusted" and dr["ref"] == "B-0414")
ck("5 ... reception is never asked D-8's amount (paper ₹1,700, Marg the goods' ₹2,000), and an answer is refused (no WRONG mark)",
   not porders._s440_differs(170000, 200000, "2026-10") and porders._s440_differs(170000, 210000, "2026-10")
   and con.execute("SELECT verdict FROM purchase_bill WHERE id=?", (BID["d8"],)).fetchone()[0] in (None, ""))
ck("5 ... D-8's row: settled, Nobody, the note names the return; S738 never tells Amir to lower D-8", r8.get("state") == "has_scan" and r8.get("whose") == "Nobody"
   and "took return D-3" in (r8.get("note") or "") and BID["d8"] not in {f["bill_id"] for f in (safe(SR.s738_fixes, con) or [])})
lr = ret("mret:%s|6708" % PA.supplier_key("L.K. DRUG HOUSE"))
ck("5 L.K. 6708 (from stock): pending its paper", bool(lr) and lr["stage"] == "paper" and not lr["resolved"])
scan(409, "L.K. DRUG HOUSE", "6708", 2005.0, "2026-10-30", [dict(name="BRUTAFLAM GEL", quantity=18, rate=111.4, amount=2005.0)], hours=1)
link("lk", 409)
lr = ret("mret:%s|6708" % PA.supplier_key("L.K. DRUG HOUSE"))
ck("5 ... its credit note scanned and agreeing: settled", bool(lr) and lr["resolved"])
ck("5 September's purchase return is never a return here (D848)", model() is not None and ret("6115") is None)
con.execute("UPDATE purchase_bill SET amount_p=90000 WHERE id=?", (BID["mu"],))
con.commit()
m = model()
ck("5 Mu: Marg reached the paper by itself -- the question leaves (F-1161)", m is not None and not m.get("questions"))

print("6 · the owner's step view")
as_(OWNER)
na = con.execute("SELECT COUNT(*) FROM purchase_audit").fetchone()[0]
snap = [tuple(r) for r in con.execute("SELECT * FROM s740_track ORDER BY rkey")] if nt >= 0 else []
tc0 = con.total_changes
st, h = get("/finance/purchase/page/check?month=2026-10")
ck("6 the step view answers (200)", st == 200, s740=False)
ck("6 row 8 'Returns (pending until the dealer's credit note or revised bill)'", "Returns (pending until the dealer&#x27;s credit note or revised bill)" in h
   or "Returns (pending until the dealer's credit note or revised bill)" in h)
ck("6 Janta resolved with its road ('the dealer revised the bill to ₹3,205 (scan B-0408)')", "the dealer revised the bill to ₹3,205 (scan B-0408)" in h)
ck("6 the count shortage: 'Possibly returned — no paper', ZUPRINOR 5 · 2 pcs, bought only from SIGMA MEDICOS", "Possibly returned — no paper" in h
   and "ZUPRINOR 5 · 2 pcs" in h and "Bought only from SIGMA MEDICOS" in h)
ck("6 ... a shortage that is not whole strips (TYRO BR 121) and one bought from two dealers are not asked", h.count("Possibly returned — no paper") == 1)
ck("6 the Record-a-return form (dealer, item, the − / + quantity; nothing typed)", 'id="s740rec"' in h and 'id="s740sup"' in h and 'id="s740qty"' in h
   and "<input" not in h.split('id="s740rec"')[1].split("</div></div>")[0] if 'id="s740rec"' in h else False)
ck("6 the GET wrote nothing", nt >= 0 and con.total_changes == tc0 and con.execute("SELECT COUNT(*) FROM purchase_audit").fetchone()[0] == na and
   ([tuple(r) for r in con.execute("SELECT * FROM s740_track ORDER BY rkey")] if nt >= 0 else []) == snap)
mbill("sr0", "SIGMA MEDICOS", "SR-0", "2026-10-15", -659)                  # an older purchase return of ZUPRINOR, its paper scanned: settled
mline("SIGMA MEDICOS", "SR-0", "2026-10-15", "ZUPRINOR 5", 1, 659.0, "1*1")
scan(421, "SIGMA MEDICOS", "SR-0", 659.0, "2026-10-15", [dict(name="ZUPRINOR 5", quantity=1, rate=659.0, amount=659.0)], hours=30)
link("sr0", 421)
as_(AMIR)
get("/finance/amir/step/1")                                   # the tracker sees SR-0 as a return of its own, settled
as_(OWNER)
lid = con.execute("SELECT id FROM stock_watch_loss_line WHERE item='ZUPRINOR 5'").fetchone()[0]
as_(AMIR)
st, j = post("/finance/purchase/api/s740/flag", dict(loss=lid, yes=True))
ck("6 Amir cannot answer the owner's shortage (403)", st == 403)
as_(OWNER)
st, j = post("/finance/purchase/api/s740/flag", dict(loss=lid, yes=True))
ck("6 the owner: 'Yes, returned to SIGMA MEDICOS' (200)", st == 200 and j.get("ok"))
orr = next((r for r in (model() or {}).get("returns") or [] if r["kind"] == "own"), None)
ck("6 ... a pending return of his own: SIGMA, ZUPRINOR 5 · 2 pcs, ₹1,318 at the last rate, Amir enters it", bool(orr) and orr["sup"] == PA.supplier_key("SIGMA MEDICOS")
   and orr["amount_p"] == 131800 and orr["stage"] == "do_own" and "ZUPRINOR 5 · 2 pcs" in orr.get("hi", ""))
ck("6 ... the older, settled SR-0 is NOT claimed by it (SR-0 stays its own, settled)", bool(orr) and not orr.get("mb")
   and bool(ret("mret:%s|sr-0" % PA.supplier_key("SIGMA MEDICOS"))) and ret("mret:%s|sr-0" % PA.supplier_key("SIGMA MEDICOS"))["resolved"])
st, h = get("/finance/purchase/page/check?month=2026-10")
ck("6 ... the shortage line has left the page", "Possibly returned — no paper" not in h and 'id="s740rt"' in h)
st, h = get("/finance/purchase/page/check?month=2026-11")
ck("6 November: the NEFT strip holds on its pending return and October's still pending (Nu, R-6800): '3 pending returns'",
   re.search(r'id="s726strip">NEFT on hold · 3 pending returns<', h) is not None
   and "ZUPRINOR 5 · 2 pcs" in h)
st, j = get("/finance/purchase/api/s740/items?supplier=" + PA.supplier_key("SIGMA MEDICOS"))
items = (json.loads(j) if st == 200 else {}).get("items") or []
ck("6 the form's items for SIGMA (ZUPRINOR 5 by the pc, TYRO BR by the strip)", sorted((i["item"], i["unit"]) for i in items) == [("TYRO BR", "strip"), ("ZUPRINOR 5", "pc")])
st, j = post("/finance/purchase/api/s740/record", dict(supplier=PA.supplier_key("SIGMA MEDICOS"), item="TYRO BR", qty=2))
ck("6 'Record a return': TYRO BR · 2 strips from SIGMA (200)", st == 200 and j.get("ok"))
st, j = post("/finance/purchase/api/s740/record", dict(supplier=PA.supplier_key("SIGMA MEDICOS"), item="NOT AN ITEM", qty=2))
ck("6 ... an item not in the list is refused (400)", st == 400)
st, j = post("/finance/purchase/api/s740/record", dict(supplier=PA.supplier_key("SIGMA MEDICOS"), item="TYRO BR", qty=2.5))
ck("6 ... a part quantity is refused (400)", st == 400)
rec = [r for r in (model() or {}).get("returns") or [] if r["kind"] == "own" and r.get("item") == "TYRO BR"]
ck("6 ... recorded: TYRO BR · 2 strips, ₹370", len(rec) == 1 and rec[0]["amount_p"] == 37000 and "2 strips" in rec[0].get("hi", ""))
st, j = post("/finance/purchase/api/s740/withdraw", dict(id=rec[0]["own_id"] if rec else 0))
ck("6 ... withdrawn (recorded by mistake)", st == 200 and not [r for r in (model() or {}).get("returns") or [] if r.get("item") == "TYRO BR"])
mbill("scn", "SIGMA MEDICOS", "SR-2", "2026-10-25", -1318)
con.execute("UPDATE purchase_bill SET first_seen_day=? WHERE id=?", (OS.today().isoformat(), BID["scn"]))   # entered after the owner's record
con.commit()
mline("SIGMA MEDICOS", "SR-2", "2026-10-25", "ZUPRINOR 5", 2, 659.0, "1*1")
orr = next((r for r in (model() or {}).get("returns") or [] if r["kind"] == "own"), None)
ck("6 Amir's purchase return SR-2 in Marg is claimed by the owner's return (item matched): now its paper", bool(orr) and (orr.get("mb") or {}).get("bill_no") == "SR-2"
   and orr["stage"] == "paper" and ret("mret:%s|sr-2" % PA.supplier_key("SIGMA MEDICOS")) is None)

print("7 · undo, and the tracker")
as_(AMIR)
get("/finance/amir/step/1")
row = con.execute("SELECT resolved_at, road FROM s740_track WHERE rkey=?", (jkey("jan"),)).fetchone() if nt >= 0 else None
ck("7 the tracker: Janta resolved, road 'revised'", bool(row) and row[0] and row[1] == "revised")
ck("7 ... resolution audited (s740_resolved)", con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s740_resolved'").fetchone()[0] >= 1)
mbill("phi", "PHI PHARMA", "P-4", "2026-10-26", 400)
scan(415, "PHI PHARMA", "P-4", 600.0, "2026-10-26", [dict(name="PHI TAB", quantity=6, rate=100.0, amount=600.0)], hours=1)
link("phi", 415, 60000, "marg_wrong")
as_(RECEP, "sender")
post("/finance/porders/api/s740/wapsi", dict(bill=BID["phi"], yes=True))
as_(AMIR)
get("/finance/amir/step/1")
pk = jkey("phi")
ck("7 Phi: a return, tracked", bool(con.execute("SELECT 1 FROM s740_track WHERE rkey=? AND gone_at IS NULL", (pk,)).fetchone()) if nt >= 0 else False)
as_(OWNER)
st, j = post("/finance/purchase/api/s740/undo", dict(bill=BID["phi"]))
ck("7 the owner undoes a wrong answer (200)", st == 200 and j.get("ok"))
ck("7 ... the question is back with reception", BID["phi"] in {q["bill_id"] for q in (model() or {}).get("questions") or []})
as_(AMIR)
get("/finance/amir/step/1")
ck("7 ... the tracker marks it gone (never resolved)", bool(con.execute("SELECT 1 FROM s740_track WHERE rkey=? AND gone_at IS NOT NULL AND resolved_at IS NULL",
                                                                       (pk,)).fetchone()) if nt >= 0 else False)
S = safe(AD.state, con, AD._today(), "amir")
ck("7 his day: something to enter now (Sigma's return paper is reception's; Kedar done) -> the card is his line only when a 'do' stands",
   bool(S) and any(r[0] == "s740" for r in S.card) and all((r[3] is True) == ("(0 to enter)" not in r[2]) for r in S.card if r[0] == "s740"))

as_(RECEP, "sender")
post("/finance/porders/api/s740/wapsi", dict(bill=BID["phi"], yes=True))
pend0 = sorted(r["key"] for r in (model() or {}).get("returns") or [] if not r["resolved"])
con.execute("CREATE TABLE IF NOT EXISTS purchase_month (month TEXT PRIMARY KEY, status TEXT)") if not con.execute(
    "SELECT 1 FROM sqlite_master WHERE name='purchase_month'").fetchone() else None
con.execute("INSERT OR REPLACE INTO purchase_month (month, status) VALUES ('2026-10', 'final')") if "status" in {
    r[1] for r in con.execute("PRAGMA table_info(purchase_month)")} else None
con.commit()
pend1 = sorted(r["key"] for r in (model() or {}).get("returns") or [] if not r["resolved"])
ck("8 October finalised: its pending returns stay (Phi, Nu among them)", bool(pend0) and pend1 == pend0 and pk in pend1)
_adb = PA._assets_db
snap = [tuple(r) for r in con.execute("SELECT * FROM s740_track ORDER BY rkey")] if nt >= 0 else []
PA._assets_db = os.path.join(TMP, "no_such_assets.db")
getattr(SR, "_S740_MEMO", {}).clear()
r8 = safe(SR.s740_sync, con) if hasattr(SR, "s740_sync") else None
PA._assets_db = _adb
ck("8 the scan database down: the tracker is not touched (nothing flips)", r8 == (0, 0, 0) and
   [tuple(r) for r in con.execute("SELECT * FROM s740_track ORDER BY rkey")] == snap)

print("9 · R2: the cold review's second round")
con.execute("UPDATE purchase_month SET status='open' WHERE month='2026-10'")      # October open again for these
con.commit()
scan(430, "NU PHARMA", "", 1100.0, "2026-10-17", [dict(name="OMICRON TAB", quantity=11, rate=100.0, amount=1100.0),
                                                   dict(name="RETURN OMICRON TAB", quantity=-3, rate=100.0, amount=-300.0)], hours=1)
nr = ret(jkey("nu"))
ck("9 a second scan of Nu's OWN bill (its number not read, its own return line) never settles Nu's return", bool(nr) and not nr["resolved"])
ck("9 ... nor is it listed as a dealer's deduction no return matches", model() is not None and 430 not in [o["scan"] for o in (model() or {}).get("adjusted") or []])
as_(OWNER)
st, h = get("/finance/purchase/page/check?month=2026-10")
ck("9 Tau's 'Nahi' is on the owner's row with 'Undo the answer'", 'data-s740no="%d"' % BID["tau"] in h and "Reception said: no return written" in h)
mbill("psi1", "PSI PHARMA", "P-1", "2026-10-05", 600)
mline("PSI PHARMA", "P-1", "2026-10-05", "PSI TAB", 6, 100.0, "1*1")
mbill("pzr1", "PSI PHARMA", "PZR-1", "2026-10-20", -300)                 # an OLDER purchase return of PSI TAB, settled, the tracker never saw it
mline("PSI PHARMA", "PZR-1", "2026-10-20", "PSI TAB", 3, 100.0, "1*1")
scan(431, "PSI PHARMA", "PZR-1", 300.0, "2026-10-20", [dict(name="PSI TAB", quantity=3, rate=100.0, amount=300.0)], hours=60)
link("pzr1", 431)
st, j = post("/finance/purchase/api/s740/record", dict(supplier=PA.supplier_key("PSI PHARMA"), item="PSI TAB", qty=3))
pr = [r for r in (model() or {}).get("returns") or [] if r["kind"] == "own" and r.get("item") == "PSI TAB"]
ck("9 the owner records PSI TAB · 3: the older settled PZR-1 is NOT claimed (tracker or not) -- Amir enters it", st == 200 and len(pr) == 1
   and not pr[0].get("mb") and pr[0]["stage"] == "do_own")
st, j = post("/finance/purchase/api/s740/record", dict(supplier=PA.supplier_key("PSI PHARMA"), item="PSI TAB", qty=3))
ck("9 ... a second tap of the same record is refused (400)", st == 400 and len([r for r in (model() or {}).get("returns") or [] if r.get("item") == "PSI TAB"
                                                                              and r["kind"] == "own"]) == 1)
con.execute("INSERT INTO stock_watch_loss_line (at, item, gap_units, pack, packing, mrp_p) VALUES ('2026-11-01T10:00:00', 'PSI TAB', 2, 1, '1*1', 20000)")
mbill("pzr2", "PSI PHARMA", "PZR-2", "2026-11-02", -200)                 # Amir entered it from the slip after the count
mline("PSI PHARMA", "PZR-2", "2026-11-02", "PSI TAB", 2, 100.0, "1*1")
con.execute("UPDATE purchase_bill SET first_seen_day='2026-11-03' WHERE id=?", (BID["pzr2"],))
con.commit()
lid2 = con.execute("SELECT id FROM stock_watch_loss_line WHERE item='PSI TAB'").fetchone()[0]
st, j = post("/finance/purchase/api/s740/flag", dict(loss=lid2, yes=True))
ck("9 a count shortage already entered in Marg (PZR-2, after the count): 'Yes' records nothing more and says so", st == 200 and "PZR-2" in (j.get("message") or "")
   and len([r for r in (model() or {}).get("returns") or [] if r["kind"] == "own" and r.get("item") == "PSI TAB"]) == 1)
st, j = post("/finance/purchase/api/s740/flag", dict(loss=lid2, yes=False))
ck("9 ... a second answer to the same line is refused (409)", st == 409)

print("10 · R3: the cold review's third round")
as_(OWNER)
psi = lambda: next((r for r in (model() or {}).get("returns") or [] if r["kind"] == "own" and r.get("item") == "PSI TAB"), None)
scan(440, "PSI PHARMA", "P-9", 900.0, "2026-11-04", [dict(name="ADALAT RET 20 TAB", quantity=3, rate=100.0, amount=300.0),
                                                     dict(name="PARA 500", quantity=6, rate=100.0, amount=600.0)], hours=1)
ck("10 an ordinary later bill with 'ADALAT RET 20' (a medicine, not a return) never settles the owner's PSI return", bool(psi()) and psi()["stage"] == "do_own")
ck("10 ... nor is it listed as a dealer's deduction", model() is not None and 440 not in [o["scan"] for o in (model() or {}).get("adjusted") or []])
mbill("exp1", "PSI PHARMA", "EXP-1", "2026-11-05", -300)                 # an unrelated expiry return of another item, the same value
mline("PSI PHARMA", "EXP-1", "2026-11-05", "EXPIRO TAB", 3, 100.0, "1*1")
con.execute("UPDATE purchase_bill SET first_seen_day=? WHERE id=?", (OS.today().isoformat(), BID["exp1"]))
con.commit()
ck("10 an unrelated purchase return of the same dealer and value (EXPIRO TAB) is NOT claimed by the owner's PSI TAB return",
   bool(psi()) and psi()["stage"] == "do_own" and not psi().get("mb") and bool(ret("mret:%s|exp-1" % PA.supplier_key("PSI PHARMA"))))
mbill("tcn", "TAU PHARMA", "TCN-1", "2026-10-28", -500)                   # a purchase return whose credit note the scanner misread (550)
scan(441, "TAU PHARMA", "TCN-1", 550.0, "2026-10-28", [dict(name="ZETA TAB", quantity=1, rate=550.0, amount=550.0)], hours=1)
link("tcn", 441)
tr_ = ret("mret:%s|tcn-1" % PA.supplier_key("TAU PHARMA"))
ck("10 a misread credit note: Amir checks the paper ('do_amount'), the owner's row offers 'The scan misread'", bool(tr_) and tr_["stage"] == "do_amount"
   and "The scan misread — the paper is Marg" in get("/finance/purchase/page/check?month=2026-10")[1])
st, j = post("/finance/purchase/api/s740/cnlook", dict(bill=BID["tcn"]))
tr_ = ret("mret:%s|tcn-1" % PA.supplier_key("TAU PHARMA"))
reg = safe(SR.register, con, "2026-10") or {"rows": []}
rt = next((x for x in reg["rows"] if x["id"] == BID["tcn"]), {})
ck("10 ... the owner's look settles it and its register row (has its scan, Nobody)", st == 200 and bool(tr_) and tr_["resolved"] and rt.get("state") == "has_scan"
   and rt.get("whose") == "Nobody")
as_(AMIR)
st, j = post("/finance/purchase/api/s740/cnlook", dict(bill=BID["tcn"]))
ck("10 ... Amir cannot make that look (403)", st == 403)
as_(OWNER)
r_ = cl.post("/finance/purchase/api/s740/record", data='{"supplier": "%s", "item": "PSI TAB", "qty": NaN}' % PA.supplier_key("PSI PHARMA"),
             content_type="application/json")
ck("10 a quantity of NaN is refused (400), never a crash", r_.status_code == 400)
getattr(SR, "_S740_MEMO", {}).clear()
m1 = safe(SR.s740_model, con) if hasattr(SR, "s740_model") else None
m2 = safe(SR.s740_model, con) if hasattr(SR, "s740_model") else None
ck("10 outside a request the model is read once while nothing changes (the memo works)", m1 is not None and m1 is m2)

print("11 · R4")
mbill("zr1", "OMEGA REMEDIES", "ZR-1", "2026-10-29", -400)                # a purchase return in Marg whose credit note never comes
scan(470, "OMEGA REMEDIES", "Z-77", 1600.0, "2026-11-03", [dict(name="SIGMA GEL", quantity=4, rate=500.0, amount=2000.0),
                                                           dict(name="LESS: RETURN ZR-1", quantity=1, rate=-400.0, amount=-400.0)], hours=1)
mbill("z77", "OMEGA REMEDIES", "Z-77", "2026-11-03", 2000)
link("z77", 470)
zr = ret("mret:%s|zr-1" % PA.supplier_key("OMEGA REMEDIES"))
ck("11 a purchase return in Marg settled by the dealer's deduction on a later bill (Z-77 'LESS: RETURN ZR-1')", bool(zr) and zr["resolved"] and zr["road"] == "adjusted"
   and zr["ref"] == "B-0470")
ck("11 ... and that deduction is not listed as unmatched", model() is not None and 470 not in [o["scan"] for o in (model() or {}).get("adjusted") or []])
as_(OWNER)
mbill("pzr3", "PSI PHARMA", "PZR-3", "2026-11-06", -300)                  # Marg prints the return's quantity with its minus
mline("PSI PHARMA", "PZR-3", "2026-11-06", "PSI TAB", -3, 100.0, "1*1")
con.execute("UPDATE purchase_bill SET first_seen_day=? WHERE id=?", (OS.today().isoformat(), BID["pzr3"]))
con.commit()
ck("11 the owner's PSI TAB · 3 claims PZR-3 whose line reads -3 (a minus quantity)", bool(psi()) and (psi().get("mb") or {}).get("bill_no") == "PZR-3"
   and ret("mret:%s|pzr-3" % PA.supplier_key("PSI PHARMA")) is None)

scan(497, "OMEGA REMEDIES", "ZR-1", 400.0, "2026-10-29", [dict(name="ETA GEL", quantity=1, rate=400.0, amount=400.0)], hours=1)
link("zr1", 497)
zr = ret("mret:%s|zr-1" % PA.supplier_key("OMEGA REMEDIES"))
reg = safe(SR.register, con, "2026-11") or {"rows": []}
rz = next((x for x in reg["rows"] if x["id"] == BID["z77"]), {})
ck("11 ZR-1's credit note scanned AND taken off Z-77: settled, and Z-77 stays held at the goods (its row settled, no S440 question, not unmatched)",
   bool(zr) and zr["resolved"] and (zr.get("adj") or {}).get("scan") == 470 and rz.get("whose") == "Nobody" and rz.get("state") in ("has_scan", "verified")
   and not porders._s440_differs(160000, 200000, "2026-11") and 470 not in [o["scan"] for o in (model() or {}).get("adjusted") or []])
mbill("vcn", "VEGA PHARMA", "VCN-1", "2026-10-20", -400)                 # a credit note scanned, and "LESS CN VCN-1" on the next bill
scan(612, "VEGA PHARMA", "VCN-1", 400.0, "2026-10-20", [dict(name="VEGA GEL", quantity=1, rate=400.0, amount=400.0)], hours=1)
link("vcn", 612)
scan(613, "VEGA PHARMA", "V-77", 1700.0, "2026-11-04", [dict(name="VEGA TAB", quantity=21, rate=100.0, amount=2100.0),
                                                        dict(name="LESS CN VCN-1", quantity=1, rate=-400.0, amount=-400.0)], hours=1)
mbill("v77", "VEGA PHARMA", "V-77", "2026-11-04", 2100)
link("v77", 613)
vr = ret("mret:%s|vcn-1" % PA.supplier_key("VEGA PHARMA"))
ck("11 'LESS CN VCN-1' is read as the return taken off: V-77 held at the goods (no S440 question)", bool(vr) and vr["resolved"] and (vr.get("adj") or {}).get("scan") == 613
   and not porders._s440_differs(170000, 210000, "2026-11"))
mbill("ocn", "OMICRON DRUGS", "OCN-1", "2026-10-20", -400)                # an unnamed "LESS: CREDIT NOTE ADJ", then the credit note scanned
scan(611, "OMICRON DRUGS", "O-77", 1800.0, "2026-11-04", [dict(name="OMI TAB", quantity=22, rate=100.0, amount=2200.0),
                                                          dict(name="LESS: CREDIT NOTE ADJ", quantity=1, rate=-400.0, amount=-400.0)], hours=1)
mbill("o77", "OMICRON DRUGS", "O-77", "2026-11-04", 2200)
link("o77", 611)
as_(AMIR)
get("/finance/amir/step/1")                                   # the tracker ties B-0611 to OCN-1
scan(614, "OMICRON DRUGS", "OCN-1", 400.0, "2026-10-20", [dict(name="OMI TAB", quantity=4, rate=100.0, amount=400.0)], hours=1)
link("ocn", 614)
orr_ = ret("mret:%s|ocn-1" % PA.supplier_key("OMICRON DRUGS"))
ck("11 an unnamed deduction already tied, then the credit note scanned: O-77 stays held at the goods (no S440 question)", bool(orr_) and orr_["resolved"]
   and (orr_.get("adj") or {}).get("scan") == 611 and not porders._s440_differs(180000, 220000, "2026-11"))
mbill("x9", "XI PHARMA", "X-9", "2026-10-10", 2000)                       # the full bill; credit note XCN-1; "LESS: RETURN AGST BILL X-9" on X-20
mbill("xcn", "XI PHARMA", "XCN-1", "2026-10-12", -500)
scan(620, "XI PHARMA", "XCN-1", 500.0, "2026-10-12", [dict(name="XI TAB", quantity=5, rate=100.0, amount=500.0)], hours=1)
link("xcn", 620)
scan(621, "XI PHARMA", "X-20", 500.0, "2026-11-03", [dict(name="XI SYP", quantity=10, rate=100.0, amount=1000.0),
                                                     dict(name="LESS: RETURN AGST BILL X-9", quantity=1, rate=-500.0, amount=-500.0)], hours=1)
mbill("x20", "XI PHARMA", "X-20", "2026-11-03", 1000)
link("x20", 621)
xr = ret("mret:%s|xcn-1" % PA.supplier_key("XI PHARMA"))
ck("11 a deduction naming XCN-1's original bill (X-9) is still its own: X-20 held at the goods, no S440 question; 'LESS RATE DIFF CN' never a return",
   bool(xr) and xr["resolved"] and (xr.get("adj") or {}).get("scan") == 621 and not porders._s440_differs(50000, 100000, "2026-11")
   and SR._s740_taken_off([dict(name="LESS RATE DIFF CN", quantity=1, amount=-500.0), dict(name="A", quantity=1, amount=2000.0)], 150000) == (0, ""))
mbill("pp1", "PI PHARMA", "PP-1", "2026-10-08", 800)                      # Haan; then "LESS: CREDIT NOTE ADJ" on PP-9 AND the credit note entered
scan(630, "PI PHARMA", "PP-1", 1000.0, "2026-10-08", [dict(name="PI TAB", quantity=10, rate=100.0, amount=1000.0)], hours=1)
link("pp1", 630, 100000, "marg_wrong")
as_(RECEP, "sender")
post("/finance/porders/api/s740/wapsi", dict(bill=BID["pp1"], yes=True))
scan(631, "PI PHARMA", "PP-9", 1300.0, "2026-11-02", [dict(name="PI SYP", quantity=15, rate=100.0, amount=1500.0),
                                                      dict(name="LESS: CREDIT NOTE ADJ", quantity=1, rate=-200.0, amount=-200.0)], hours=1)
mbill("pp9", "PI PHARMA", "PP-9", "2026-11-02", 1500)
link("pp9", 631)
as_(AMIR)
get("/finance/amir/step/1")
mbill("pcn", "PI PHARMA", "PCN-45", "2026-11-03", -200)
scan(632, "PI PHARMA", "PCN-45", 200.0, "2026-11-03", [dict(name="PI TAB", quantity=2, rate=100.0, amount=200.0)], hours=1)
link("pcn", 632)
pc = ret("mret:%s|pcn-45" % PA.supplier_key("PI PHARMA"))
as_(OWNER)
ck("11 settled by a deduction, then a credit note of that amount entered after it: never silent -- the owner is asked 'the same return or another?'",
   bool(pc) and pc["stage"] == "check_same" and not pc["resolved"] and "The same return" in get("/finance/purchase/page/check?month=2026-11")[1])
st, j = post("/finance/purchase/api/s740/same", dict(bill=BID["pcn"], same=True))
pr_ = ret(jkey("pp1"))
ck("11 ... 'the same return': PP-1 claims it and Amir is told to enter the full bill; PP-9 still held at the goods",
   st == 200 and bool(pr_) and pr_["stage"] == "do_full" and not porders._s440_differs(130000, 150000, "2026-11")
   and ret("mret:%s|pcn-45" % PA.supplier_key("PI PHARMA")) is None)
ck("11 'LESS: RETURNED GOODS' and 'D/N 12' are read as return lines", hasattr(SR, "_s740_taken_off") and SR._s740_taken_off([dict(name="LESS: RETURNED GOODS", amount=-300.0),
   dict(name="A", amount=2000.0)], 170000)[0] == 30000 and SR._s740_taken_off([dict(name="LESS D/N 12", amount=-300.0), dict(name="A", amount=2000.0)], 170000)[0] == 30000)
mbill("pr77", "DELTA DRUGS", "PR-77", "2026-11-03", -300)                  # an unrelated later purchase return of Delta, the same ₹300
dr = ret(jkey("del"))
p77 = ret("mret:%s|pr-77" % PA.supplier_key("DELTA DRUGS"))
ck("11 Delta, settled by D-8's deduction, never claims a later purchase return PR-77 of the same amount by itself (no wrong 'full bill' card)",
   bool(dr) and dr["resolved"] and bool(p77) and p77["stage"] == "check_same")
as_(OWNER)
st, j = post("/finance/purchase/api/s740/same", dict(bill=BID["pr77"], same=False))
dr, p77 = ret(jkey("del")), ret("mret:%s|pr-77" % PA.supplier_key("DELTA DRUGS"))
ck("11 ... 'another return': PR-77 is its own (its paper awaited), Delta stays settled", st == 200 and bool(dr) and dr["resolved"] and bool(p77)
   and p77["stage"] == "paper")
as_(AMIR)
st, j = post("/finance/purchase/api/s740/same", dict(bill=BID["pr77"], same=True))
ck("11 ... only the doctor answers it (403 for Amir)", st == 403)
ck("11 'LESS CN 37' names return 37; 'LESS RET 2 STRIPS' is a return line", hasattr(SR, "_s740_tokens") and "37" in SR._s740_tokens("LESS CN 37")
   and "2" not in SR._s740_tokens("LESS RET 2 STRIPS") and SR._s740_taken_off([dict(name="LESS RET 2 STRIPS", amount=-100.0), dict(name="A", amount=900.0)], 80000)[0] == 10000)
mbill("ra1", "RHO AGENCIES", "RA-1", "2026-10-09", 1200)                 # Haan; RA-9 takes it off; then RPR-5 of that amount, dated after RA-9
scan(640, "RHO AGENCIES", "RA-1", 1500.0, "2026-10-09", [dict(name="RHO TAB", quantity=15, rate=100.0, amount=1500.0)], hours=1)
link("ra1", 640, 150000, "marg_wrong")
as_(RECEP, "sender")
post("/finance/porders/api/s740/wapsi", dict(bill=BID["ra1"], yes=True))
scan(641, "RHO AGENCIES", "RA-9", 1700.0, "2026-11-02", [dict(name="RHO SYP", quantity=20, rate=100.0, amount=2000.0),
                                                         dict(name="LESS RETURN", quantity=1, rate=-300.0, amount=-300.0)], hours=1)
mbill("ra9", "RHO AGENCIES", "RA-9", "2026-11-02", 2000)
link("ra9", 641)
mbill("rpr5", "RHO AGENCIES", "RPR-5", "2026-11-04", -300)
rp = ret("mret:%s|rpr-5" % PA.supplier_key("RHO AGENCIES"))
ck("11 before any tracker sync: a purchase return dated after the deduction is put to the owner, never claimed (no wrong 'full bill' card)",
   bool(rp) and rp["stage"] == "check_same" and (ret(jkey("ra1")) or {}).get("stage") == "resolved")
as_(OWNER)
st, j = post("/finance/purchase/api/s740/same", dict(bill=BID["rpr5"], same=True))
ra = ret(jkey("ra1"))
ck("11 ... 'the same': RA-1 claims it (full bill), and RA-9 stays held at the goods though its date is before RPR-5",
   st == 200 and bool(ra) and ra["stage"] == "do_full" and (ra.get("adj") or {}).get("scan") == 641 and not porders._s440_differs(170000, 200000, "2026-11"))
mbill("ox1", "OXY PHARMA", "OX-1", "2026-10-10", 1000)                   # two returns of one dealer and amount; the deduction names OY-2
mbill("oy2", "OXY PHARMA", "OY-2", "2026-10-11", 1000)
scan(650, "OXY PHARMA", "OX-1", 1300.0, "2026-10-10", [dict(name="OX TAB", quantity=13, rate=100.0, amount=1300.0)], hours=1)
scan(651, "OXY PHARMA", "OY-2", 1300.0, "2026-10-11", [dict(name="OY TAB", quantity=13, rate=100.0, amount=1300.0)], hours=1)
link("ox1", 650, 130000, "marg_wrong")
link("oy2", 651, 130000, "marg_wrong")
as_(RECEP, "sender")
post("/finance/porders/api/s740/wapsi", dict(bill=BID["ox1"], yes=True))
post("/finance/porders/api/s740/wapsi", dict(bill=BID["oy2"], yes=True))
scan(652, "OXY PHARMA", "OX-50", 1700.0, "2026-11-03", [dict(name="OX SYP", quantity=20, rate=100.0, amount=2000.0),
                                                        dict(name="LESS RETURN AGST BILL OY-2", quantity=1, rate=-300.0, amount=-300.0)], hours=1)
mbill("ox50", "OXY PHARMA", "OX-50", "2026-11-03", 2000)
link("ox50", 652)
ck("11 a deduction naming OY-2 settles OY-2, never OX-1 (same dealer, same amount)", (ret(jkey("oy2")) or {}).get("resolved") is True
   and (ret(jkey("ox1")) or {}).get("resolved") is False)
scan(660, "NU PHARMA", "N-7", 1100.0, "2026-10-20", [dict(name="OMICRON TAB", quantity=11, rate=100.0, amount=1100.0),
                                                     dict(name="RETURN OMICRON TAB", quantity=-3, rate=100.0, amount=-300.0)], hours=1)
nr = ret(jkey("nu"))
ck("11 Nu's own paper re-scanned and its number misread (N-7): never a deduction -- no 'enter bill N-7' card, Nu not settled", bool(nr)
   and not nr["resolved"] and nr.get("stage") != "do_goods" and (nr.get("adj") or {}).get("scan") != 660)
print("12 · R5")
con.execute("UPDATE purchase_bill SET amount_p=110000 WHERE id=?", (BID["nu"],))   # Nu: full bill in Marg, and a purchase return of the bill's day
mbill("ncn", "NU PHARMA", "NCN-1", "2026-10-17", -300)
nr = ret(jkey("nu"))
ck("12 Nu: its OWN paper's return line never settles it by the purchase-return road either (its credit note is awaited)", bool(nr) and not nr["resolved"]
   and nr["stage"] == "paper")
mbill("ar10", "ARC PHARMA", "AR-10", "2026-10-20", -250)
mbill("ar20", "ARC PHARMA", "AR-20", "2026-10-21", -250)
scan(480, "ARC PHARMA", "A-300", 750.0, "2026-11-02", [dict(name="RHO TAB", quantity=10, rate=100.0, amount=1000.0),
                                                       dict(name="LESS: RETURN AR-20", quantity=1, rate=-250.0, amount=-250.0)], hours=1)
mbill("a300", "ARC PHARMA", "A-300", "2026-11-02", 1000)
link("a300", 480)
a10, a20 = ret("mret:%s|ar-10" % PA.supplier_key("ARC PHARMA")), ret("mret:%s|ar-20" % PA.supplier_key("ARC PHARMA"))
ck("12 a deduction naming AR-20 settles AR-20, never AR-10 (same dealer, same amount)", bool(a10) and bool(a20) and a20["resolved"] and not a10["resolved"])
as_(OWNER)
mbill("chi", "CHI PHARMA", "C-1", "2026-10-05", 600)
mline("CHI PHARMA", "C-1", "2026-10-05", "CHI TAB", 6, 100.0, "1*1")
post("/finance/purchase/api/s740/record", dict(supplier=PA.supplier_key("CHI PHARMA"), item="CHI TAB", qty=3))
mbill("cr1", "CHI PHARMA", "CR-1", "2026-11-06", -300)                    # Marg prints the item on two batch lines, 2 and 1
mline("CHI PHARMA", "CR-1", "2026-11-06", "CHI TAB", 2, 100.0, "1*1")
con.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, packing, batch, qty, rate_p, discount_pct, tax, direction, source_md5, "
            "line_type) VALUES (?,?,?,?,?,?,?,?,?,0,0,'PURCHASE','i0i0','BILLITEMWISE')",
            (PA.supplier_key("CHI PHARMA"), "CR-1", "2026-11-06", "2026-11", "CHI TAB", "1*1", "B2", 1, 10000))
con.execute("UPDATE purchase_bill SET first_seen_day=? WHERE id=?", (OS.today().isoformat(), BID["cr1"]))
con.commit()
cr = next((r for r in (model() or {}).get("returns") or [] if r["kind"] == "own" and r.get("item") == "CHI TAB"), None)
ck("12 the owner's CHI TAB · 3 claims CR-1 printed on two batch lines (2 + 1)", bool(cr) and (cr.get("mb") or {}).get("bill_no") == "CR-1"
   and ret("mret:%s|cr-1" % PA.supplier_key("CHI PHARMA")) is None)

print("13 · R9")
scan(495, "KAPPA KEMICALS", "KK-5", 900.0, (OS.today().replace(day=1) - dt.timedelta(days=5)).isoformat(),
     [dict(name="KAPPA SYP", quantity=4, rate=300.0, amount=1200.0), dict(name="LESS: GOODS RETURN", quantity=1, rate=-300.0, amount=-300.0)], hours=1)
ck("13 last month's dealer deduction that no return matches is read and listed for the owner's review", 495 in [o["scan"] for o in (model() or {}).get("adjusted") or []])

if os.environ.get("S740_WALK_PAGES"):                        # the pages as drawn, for a reviewer's eyes
    _pd = os.environ["S740_WALK_PAGES"]
    os.makedirs(_pd, exist_ok=True)
    as_(AMIR)
    open(os.path.join(_pd, "amir_step1.html"), "w").write(get("/finance/amir/step/1")[1])
    as_(OWNER)
    open(os.path.join(_pd, "owner_check.html"), "w").write(get("/finance/purchase/page/check?month=2026-10")[1])
    as_(RECEP, "sender")
    open(os.path.join(_pd, "billkaam.html"), "w").write(get("/finance/porders/s454/billkaam")[1])
n_s = len(S740F)
print("walk_s740: %d check(s) failed (%d of them S740 checks)" % (len(FAILS), n_s))
sys.exit(1 if FAILS else 0)
