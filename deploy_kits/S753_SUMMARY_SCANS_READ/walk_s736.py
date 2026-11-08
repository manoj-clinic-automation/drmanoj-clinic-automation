#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s736.py -- S736_RECEPTION_BILL_LIST on a MADE-UP root (no real data, no phone): the finance code to test, a made-up finance.db (the
real schema file) and a made-up assets.db (its own temp folder; never the live paths).
    python3 -B walk_s736.py <finance code dir to test> <purchase_schema.sql> [<dir holding scan_quality.py>]
Run on the TO files: every check green.  CONTROL: run it on the live files (porders_s454 8fd445b3, scan_register 57ca3088, purchase_app
4b6ea083) -- every [S736] check goes red.  Prints the last line 'walk_s736: N check(s) failed (M of them S736 checks)'."""
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import tempfile
import traceback

CODE, SCHEMA = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
SHARED = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.join(os.path.dirname(CODE), "shared")
TMP = tempfile.mkdtemp(prefix="s736walk_")
import shutil                                                 # noqa: E402
_code = os.path.join(TMP, "code")                             # the code is walked from a copy of its own (purchase_app reads its schema beside it)
os.makedirs(_code)
for _n in os.listdir(CODE):                                   # the top-level .py files only (the live folder holds databases and logs)
    if _n.endswith(".py") and os.path.isfile(os.path.join(CODE, _n)):
        shutil.copy(os.path.join(CODE, _n), os.path.join(_code, _n))
shutil.copy(SCHEMA, os.path.join(_code, "purchase_schema.sql"))
CODE = _code
os.environ["SHARED_LIB_DIR"] = SHARED
os.environ.pop("ASSETS_DB", None)
os.environ.pop("FINANCE_DB", None)
sys.path.insert(0, CODE)
sys.path.insert(0, SHARED)
import warnings                                               # noqa: E402
warnings.simplefilter("ignore")
FAILS, S736F = [], []


def ck(name, cond, s736=True):
    print(("  ok   " if cond else "  FAIL ") + ("[S736] " if s736 else "") + name)
    if not cond:
        FAILS.append(name)
        if s736:
            S736F.append(name)


def safe(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception:                                         # noqa: BLE001 -- the CONTROL: an absent S736 function is a red check, never a crash
        print("    (raised: %s)" % traceback.format_exc().strip().splitlines()[-1][:200])
        return None


from flask import Flask, jsonify                              # noqa: E402

import order_sheet as OS                                      # noqa: E402
import porders                                                # noqa: E402
import porders_s454 as P4                                     # noqa: E402
import purchase_app as PA                                     # noqa: E402
import scan_register as SR                                    # noqa: E402
import order_track_page as OTP                                # noqa: E402

FDB, ADB = os.path.join(TMP, "finance.db"), os.path.join(TMP, "assets.db")
NOW = OS.now().replace(microsecond=0, tzinfo=None)


def ago(hours=0, minutes=0):
    return (NOW - dt.timedelta(hours=hours, minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------------------------------------------- the made-up assets.db
a = sqlite3.connect(ADB)
a.executescript("""
CREATE TABLE bills (id INTEGER PRIMARY KEY, stamp_no TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, bill_month TEXT, total_amount REAL,
  submitted_at TEXT, created_at TEXT, ocr_status TEXT, dup_of INTEGER, lane TEXT, status TEXT, kind TEXT, page_of INTEGER, rescan_of INTEGER,
  source_stored TEXT, doc_kind TEXT);
CREATE TABLE claude_reading (bill_id INTEGER, data TEXT, ok INTEGER, at TEXT);
CREATE TABLE scan_lie (bill_id INTEGER, file TEXT, at TEXT, legible INTEGER, whole_bill INTEGER, totals_visible INTEGER, blur_kept INTEGER);
CREATE TABLE settings (key TEXT, value TEXT);
INSERT INTO settings VALUES ('scan.redo_since', '2026-10-08');
""")
SC = {}


def scan(i, vendor, no, total, month="2026-10", hours=3, minutes=0, status="captured", rescan_of=None, lie=None, read=True, date=None, items=None):
    at = ago(hours, minutes)
    d = date or (month + "-20")
    a.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, "
              "source_stored, rescan_of) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (i, "B-%04d" % i, vendor, no, d, month, total, at[:16], at, "read", "pharmacy", status, "Pharmacy", "f%d.pdf" % i, rescan_of))
    if read:
        it = items if items is not None else ([dict(name="ALPHA TAB", amount=total)] if total else [])
        a.execute("INSERT INTO claude_reading VALUES (?,?,1,?)", (i, json.dumps(dict(bill_no=no, total_amount=total, vendor=vendor, doc_kind="tax_invoice",
                                                                              items=it)), at))
    if lie:
        a.execute("INSERT INTO scan_lie (bill_id, file, at, legible, whole_bill, totals_visible, blur_kept) VALUES (?,?,?,?,?,?,?)",
                  (i, "f%d.pdf" % i, at, lie.get("legible", 1), lie.get("whole_bill", 1), lie.get("totals_visible", 1), lie.get("blur_kept", 0)))
    SC[i] = dict(vendor=vendor, no=no, total=total)


scan(301, "SHRADDHA MEDICOSE", "", None, read=False)                    # paired by reception, nothing read -> the server asks (try 1, 'unread')
scan(302, "NOVA ONE", "N-55", None)                                      # a reading with no total -> 'no_total' -> asked
scan(303, "SEPT ONLY", "S-1", 500.0, month="2026-09", lie=dict(legible=0))   # September: blurred -> NOT asked (D848)
scan(304, "PERSON GONE", "P-1", 700.0, lie=dict(whole_bill=0))           # cut, but Shavez withdrew his ask -> NOT asked again
scan(305, "FRESH ONE", "F-1", 300.0, hours=0, minutes=10, lie=dict(legible=0))   # blurred, 10 minutes old -> not yet
scan(306, "CHAIN TWO", "C-1", 900.0, status="rejected", lie=dict(legible=0))     # 306 -> 307 -> 308: two rescans behind 308
scan(307, "CHAIN TWO", "C-1", 900.0, status="rejected", rescan_of=306, lie=dict(legible=0))
scan(308, "CHAIN TWO", "C-1", 900.0, rescan_of=307, lie=dict(legible=0))  # still blurred after two tries -> escalated, never asked
scan(310, "CHAIN ONE", "D-1", 400.0, status="rejected", lie=dict(whole_bill=0))
scan(309, "CHAIN ONE", "D-1", 400.0, rescan_of=310, lie=dict(whole_bill=0))      # one rescan behind, still cut -> asked, try 2
scan(311, "FINE NOW", "G-1", 250.0)                                      # an open SERVER ask, the scan is fine now -> withdrawn
scan(312, "PICKED AWAY", "H-1", 150.0, lie=dict(legible=0))              # S708's picked-away copy -> NOT asked
scan(313, "DEEPAM PHARMA", "641", 4751.0, date="2026-10-07", lie=dict(legible=0))   # a second scan of Deepam 641 (why 'dup') -> NOT asked
scan(314, "ALL GOOD", "J-1", 600.0)                                      # nothing wrong -> NOT asked
scan(316, "ACCEPTED TWICE", "", None, status="rejected", read=False)
scan(317, "ACCEPTED TWICE", "", None, status="rejected", rescan_of=316, read=False)
scan(318, "ACCEPTED TWICE", "", None, rescan_of=317, read=False)         # paired, nothing read, two rescans behind -> escalated (accept below)
scan(320, "BASS HEALTHCARE", "17465", 1597.0, date="2026-11-02", month="2026-11")    # Ek sawaal: the number read differently
scan(321, "DEEPAM PHARMA", "641", 4762.5)                                # Second look: reception typed 4,751 = Marg; the scan reads 4,762.50
scan(324, "COPY ONE", "K-1", 220.0, lie=dict(legible=0))                 # the Scan App's own duplicate copy (dup_of) -> NOT asked
a.execute("UPDATE bills SET dup_of=314 WHERE id=324")
a.commit()
a.close()
PA._assets_db = ADB

# ---------------------------------------------------------------------------------------------------------------- the made-up finance.db
con = sqlite3.connect(FDB)
con.row_factory = sqlite3.Row
con.executescript(open(SCHEMA).read())
for col in ("received_at", "received_by", "sent_by", "section"):
    try:
        con.execute("ALTER TABLE purchase_order ADD COLUMN %s TEXT" % col)
    except sqlite3.Error:
        pass
PA._schema_done = False
PA._ensure(con)
PA._ensure_s439(con)
porders.ensure_schema(con)
OS.ensure(con)
OTP.ensure(con)
for ddl in ("CREATE TABLE IF NOT EXISTS s454_scan_answer (asset_bill_id INTEGER NOT NULL, kind TEXT NOT NULL, answer TEXT, value TEXT, by TEXT,"
            " at TEXT NOT NULL, PRIMARY KEY (asset_bill_id, kind))",
            "CREATE TABLE IF NOT EXISTS s454_paper_missing (bill_id INTEGER PRIMARY KEY, by TEXT, at TEXT NOT NULL, accepted_by TEXT, accepted_at TEXT)"):
    con.execute(ddl)
for k, v in (("porders.simple", "1"), ("purchase.register_from", "2026-10-01"), ("purchase.parked_months", "2026-09"), ("porders.scan_from", "2026-09-01"),
             ("purchase.total_noise_rs", "10")):
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?,?)", (k, v))
con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows) VALUES "
            "('e0e0', 'BILLWISE', 'walk.xls', '2026-09-01', '2026-11-30', '20261106-100000', '2026-11-06T10:00:00', 1)")
BID = {}


def mbill(key, supplier, no, date, rs_):
    cur = con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, first_seen_day) VALUES (?,?,?,?,?,?,?,?)",
                      (PA.supplier_key(supplier), supplier, no, date, date[:7], int(round(rs_ * 100)), "e0e0", date))
    BID[key] = cur.lastrowid


mbill("shr", "SHRADDHA MEDICOSE", "10480", "2026-10-15", 2100)
mbill("acc", "ACCEPTED TWICE", "77", "2026-10-16", 800)
mbill("deep", "DEEPAM PHARMA", "641", "2026-10-07", 4751)
mbill("bass", "BASS HEALTHCARE", "A017456", "2026-11-02", 1597)
mbill("noscan", "ZETA REMEDIES", "Z-901", "2026-10-28", 3230)       # Scan karo: in Marg, no scan
for bk, sid in (("shr", 301), ("acc", 318), ("deep", 321)):
    con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                (BID[bk], sid, "CONFIRMED", "paired by reception; nothing was read on the paper", "2026-10-25T10:00:00"))
    con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (sid, BID[bk]))
con.execute("INSERT INTO purchase_scan_state (asset_bill_id, why, detail, checked_at, paper_amount, amount_state, confirmed_by, confirmed_at) "
            "VALUES (321,'linked','linked','2026-10-20T10:00:00',475100,'scan_wrong','reception','2026-10-20T10:00:00')")
con.execute("INSERT INTO purchase_scan_state (asset_bill_id, why, detail, checked_at) VALUES (313,'dup','second scan','2026-10-20T10:00:00')")
con.execute("INSERT INTO scan_rescan_ask (asset_bill_id, stamp, reason, asked_by, asked_at, withdrawn_at, withdrawn_by) VALUES "
            "(304,'B-0304','cut','shavez',?,?,'shavez')", (ago(5), ago(4)))
con.execute("INSERT INTO scan_rescan_ask (asset_bill_id, stamp, reason, asked_by, asked_at) VALUES (311,'B-0311','no_total','server',?)", (ago(2),))
con.execute("INSERT INTO s708_scan_pick (keep_id, drop_id, picked_by, picked_at) VALUES (314, 312, 'shavez', ?)", (ago(1),))
con.commit()

app = Flask("s736walk")
P4.init(app)
LOGIN = {}
porders._auth = lambda: (LOGIN["u"], con, LOGIN["kind"], None)
WHO = {"u": dict(user="manoj", role="checker", roles=["checker"])}


def require_stub(*roles):
    u = WHO["u"]
    if u is None or not set(u.get("roles") or []).intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return u, None


PA.init(app, lambda: con, require_stub, url_prefix="/finance/purchase", assets_db=ADB)
porders._db = lambda: con
OS.book_card = lambda con_, vendor: ("", "", False, False)
cl = app.test_client()
OWNER = dict(user="manoj", login="manoj", roles=["checker"])
RECEP = dict(user="reception", login="reception", roles=["maker"])
SHAVEZ = dict(user="shavez", login="shavez", roles=["maker"])
DARPAN = dict(user="darpan", login="darpan", roles=["maker"])
con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('porders.senders', 'reception,shavez,darpan')")
con.execute("INSERT OR IGNORE INTO unit_role (username, unit, role, active) VALUES ('manoj', 'porders', 'checker', 1)") if \
    "unit_role" in {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")} else None
con.commit()


def as_(u, kind):
    LOGIN["u"], LOGIN["kind"] = u, kind


def get(path):
    r = cl.get(path)
    return r.status_code, r.get_data(as_text=True)


def post(path, body):
    r = cl.post(path, data=json.dumps(body), content_type="application/json")
    try:
        j = r.get_json() or {}
    except Exception:                                         # noqa: BLE001
        j = {}
    return r.status_code, j


def asks(sid):
    return [dict(r) for r in con.execute("SELECT * FROM scan_rescan_ask WHERE asset_bill_id=? ORDER BY id", (sid,))]


def open_server(sid):
    return [x for x in asks(sid) if x["asked_by"] == "server" and not x["done_at"] and not x["withdrawn_at"]]


if os.environ.get("S736_WALK_SEED_ONLY"):                    # the installer's rehearsal runs the proof on these two
    _out = os.environ["S736_WALK_SEED_ONLY"]
    os.makedirs(_out, exist_ok=True)
    con.commit()
    shutil.copy(FDB, os.path.join(_out, "finance.db"))
    shutil.copy(ADB, os.path.join(_out, "assets.db"))
    print("walk_s736: seeded %s (finance.db, assets.db)" % _out)
    sys.exit(0)
print("1 · the server's plan and its asking")
plan = safe(P4.s736_plan, con) if hasattr(P4, "s736_plan") else None
ck("1 the plan reads (assets.db and scan_quality reachable)", bool(plan and plan.get("ok")))
PLAN_OK = bool(plan and plan.get("ok"))
pa_ = {x["scan"]: x for x in (plan or {}).get("ask") or []}
pe_ = {x["scan"]: x for x in (plan or {}).get("escalated") or []}
ck("1 B-0301 (paired, nothing read) is asked for: reason 'unread', try 1", (pa_.get(301) or {}).get("reason") == "unread" and pa_[301]["tries"] == 0)
ck("1 B-0302 (no total read) is asked for: 'no_total'", (pa_.get(302) or {}).get("reason") == "no_total")
ck("1 B-0309 (one rescan behind, still cut) is asked for: 'cut', try 2", (pa_.get(309) or {}).get("reason") == "cut" and pa_[309]["tries"] == 1)
ck("1 September's blurred B-0303 is NOT asked (D848)", PLAN_OK and 303 not in pa_ and 303 not in pe_)
ck("1 B-0304 -- a person withdrew its ask -- is NOT asked again", PLAN_OK and 304 not in pa_)
ck("1 B-0305 -- 10 minutes old -- is not asked yet", PLAN_OK and 305 not in pa_)
ck("1 B-0308 -- two rescans behind, still blurred -- is NOT asked: it is the owner's and Shavez's", 308 not in pa_ and (pe_.get(308) or {}).get("tries") == 2)
ck("1 the set-aside scans of a chain (306, 307, 310) are never asked", PLAN_OK and not ({306, 307, 310} & (set(pa_) | set(pe_))))
ck("1 S708's picked-away copy B-0312 is NOT asked", PLAN_OK and 312 not in pa_)
ck("1 a second scan (why dup) B-0313 is NOT asked", PLAN_OK and 313 not in pa_)
ck("1 a good scan B-0314 is NOT asked", PLAN_OK and 314 not in pa_)
ck("1 the Scan App's duplicate copy B-0324 (dup_of) is NOT asked", PLAN_OK and 324 not in pa_ and 324 not in pe_)
ck("1 B-0318 -- paired, nothing read, two rescans behind -- is escalated", (pe_.get(318) or {}).get("reason") == "unread")
ck("1 the open server ask on B-0311 (fine now) is to be withdrawn", any(x["asset_bill_id"] == 311 for x in asks(311)) and
   set((plan or {}).get("withdraw") or []) == {asks(311)[0]["id"]})
ck("1 the plan wrote nothing", PLAN_OK and len([r for r in con.execute("SELECT id FROM scan_rescan_ask")]) == 2)
res = safe(P4.s736_raise, con) if hasattr(P4, "s736_raise") else None
ck("1 s736_raise: 3 asked, 1 withdrawn", bool(res) and res["asked"] == 3 and res["withdrawn"] == 1)
ck("1 B-0301's ask: asked_by 'server', reason 'unread'", [(x["asked_by"], x["reason"]) for x in asks(301)] == [("server", "unread")])
ck("1 B-0311's server ask withdrawn by the server", bool(asks(311)) and (asks(311)[0]["withdrawn_by"] or "").startswith("server"))
ck("1 every ask audited (s736_server_ask x3, s736_server_ask_withdrawn x1)",
   con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s736_server_ask'").fetchone()[0] == 3 and
   con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s736_server_ask_withdrawn'").fetchone()[0] == 1)
res2 = safe(P4.s736_raise, con) if hasattr(P4, "s736_raise") else None
ck("1 a second run asks nothing new and withdraws nothing", bool(res2) and res2["asked"] == 0 and res2["withdrawn"] == 0)
ck("1 the asks count on reception's duty (_s618_open_count = 3)", P4._s618_open_count(con) == 3)

print("2 · the words")
sq = P4._sq()
ck("2 'unread' is said in words to reception", bool(sq) and sq.words("unread", "reception").startswith("Kuch padha nahi gaya"))
ck("2 a scan_quality code keeps its own words", bool(sq) and sq.words("cut", "reception").startswith("Poora bill nahi aaya"), s736=False)
ck("2 the server as the sender: 'Server ne khud bheja'", bool(sq) and sq.sent_by("", "server") == "Server ne khud bheja")
ck("2 a person as the sender unchanged ('Shavez ne bheja')", bool(sq) and sq.sent_by("", "shavez") == "Shavez ne bheja", s736=False)
ck("2 scan_quality's CHIPS reach through", bool(sq) and tuple(sq.CHIPS) == ("blurred", "cut", "not_bill"), s736=False)

print("3 · reception's page: Aaj ka bill kaam")
as_(RECEP, "sender")
st, h = get("/finance/porders/s454/billkaam")
ck("3 the page answers reception (200)", st == 200)
ck("3 its title: Aaj ka bill kaam", "<title>Aaj ka bill kaam</title>" in h)
ck("3 Dobara scan karo · 3", "Dobara scan karo · 3" in h)
if "Dobara scan karo · 3" not in h:
    print("    seen:", re.findall(r"Dobara scan karo · \d+", h), [(x["asset_bill_id"], x["asked_by"], x["done_at"], x["withdrawn_at"]) for x in con.execute("SELECT * FROM scan_rescan_ask")])
c301 = h[h.find('data-redo='):] if 'data-scan="301"' in h else ""
i = h.find('data-scan="301"')
c301 = h[i:h.find('</div></div>', i) + 12] if i >= 0 else ""
ck("3 B-0301's card names Marg's supplier and bill: SHRADDHA MEDICOSE · Bill 10480 · scan B-0301", "SHRADDHA MEDICOSE · Bill 10480 · scan B-0301" in c301)
ck("3 ... the reason in words: Kuch padha nahi gaya — bill seedha rakh kar, roshni mein, saaf scan kijiye",
   "Kuch padha nahi gaya — bill seedha rakh kar, roshni mein, saaf scan kijiye" in c301)
ck("3 ... 'Pehli baar · server ne dd-mm ko bheja'", re.search(r"Pehli baar · server ne \d\d-\d\d ko bheja", c301) is not None)
ck("3 ... Scan karo opens the intake with rescan_of=301 and comes back here", "rescan_of=301" in c301 and "from=%2Ffinance%2Fporders%2Fs454%2Fbillkaam" in c301)
i = h.find('data-scan="309"')
c309 = h[i:h.find('</div></div>', i) + 12] if i >= 0 else ""
ck("3 B-0309: 'Doosri baar (aakhri) · iske baad Doctor sahab aur Shavez dekhenge'", "Doosri baar (aakhri) · iske baad Doctor sahab aur Shavez dekhenge" in c309)
ck("3 B-0308 (escalated) is not on reception's list", "Dobara scan karo" in h and 'data-scan="308"' not in h)
ck("3 Scan karo — Marg mein hai, scan nahi: ZETA REMEDIES · Bill Z-901 with days waited and Bill nahi mil raha",
   "Scan karo — Marg mein hai, scan nahi" in h and "ZETA REMEDIES · Bill Z-901" in h and re.search(r"\d+ din se baaki", h) is not None and "Bill nahi mil raha" in h)
ck("3 Ek sawaal: 'Kya yeh wahi bill hai?' for B-0320 against BASS A017456", "Kya yeh wahi bill hai?" in h and 'data-q="320"' in h)
i = h.find('data-q="320"')
q320 = h[i:h.find('</button></div></div>', i)] if i >= 0 else ""
ck("3 ... it names the field and what the scan read: bill number “17465” — Marg mein A017456", "Scan par bill number “17465” padha gaya — Marg mein A017456." in q320)
ck("3 ... and what matches: Supplier, amount aur date mil rahe hain.", "Supplier, amount aur date mil rahe hain." in q320)
ck("3 ... Haan, yahi hai / Nahi post to the existing confirm door", "Haan, yahi hai" in q320 and "Nahi" in q320 and "/api/s454/confirm" in q320)
ck("3 today's scans line", re.search(r"Aaj ke scan: \d+ bill scan hue", h) is not None)
ck("3 the page carries no ten-digit run (no phone number)", re.search(r"\d{10}", re.sub(r"<[^>]+>", " ", h)) is None, s736=False)
st, j = post("/finance/porders/api/s454/paper_missing", {"bills": [BID["noscan"]]})
st2, h2 = get("/finance/porders/s454/billkaam")
ck("3 'Bill nahi mil raha' takes the bill off the list (paper not found, the S454 door)", st == 200 and st2 == 200 and "ZETA REMEDIES · Bill Z-901" not in h2)

print("4 · reception's home")
def home():
    with app.test_request_context("/finance/porders"):
        r = P4.home()
    return r[1], r[0]


st, h = home()
ck("4 reception's home has ONE row 'Aaj ka bill kaam'", 'id="row_billkaam"' in h and "Aaj ka bill kaam" in h)
if 'id="row_billkaam"' not in h:
    print("    home:", st, re.sub(r"\s+", " ", re.sub(r"<style>.*?</style>|<script>.*?</script>", "", h, flags=re.S))[:900])
ck("4 ... and no Phir se scan karo / Bill scan karna hai rows", 'id="row_rescan"' not in h and 'id="row_scan"' not in h)
m = re.search(r'id="row_billkaam"[^>]*><span class="n">(\d+)</span>', h)
mm = safe(P4.s736_model, con) if hasattr(P4, "s736_model") else None
ck("4 its count = the page's lines", bool(m and mm) and int(m.group(1)) == mm["n"])
mq = re.search(r'id="row_q" href="([^"]+)"', h)
ck("4 Photo dekh kar bataiye (if shown) opens the questions that are not on Aaj ka bill kaam", (mq is None) or mq.group(1).endswith("?nobill=1"))
as_(DARPAN, "sender")
st, h = home()
ck("4 Darpan's home is as before (no Aaj ka bill kaam row)", 'id="row_billkaam"' not in h, s736=False)

print("5 · Shavez's Scans to redo")
as_(SHAVEZ, "sender")
st, h = get("/finance/porders/s454/scans")
ck("5 the page answers (200)", st == 200, s736=False)
ck("5 the scans after two tries are his and the owner's: B-0308 and B-0318 listed", 'data-esc="308"' in h and 'data-esc="318"' in h)
ck("5 the server's asks show as sent to reception, 'Server ne khud bheja'", "Server ne khud bheja" in h)

print("6 · the owner's step view and his decisions")
WHO["u"] = dict(user="manoj", role="checker", roles=["checker"])
st, h = get("/finance/purchase/page/check?month=2026-10")
ck("6 the step view answers (200)", st == 200, s736=False)
ck("6 row 3 is 'Differences' (F-1154)", re.search(r'data-row="3"><summary><span class="l"><b>3</b> Differences</span>', h) is not None)
ck("6 row 2 lists the server's asks with the try", "rescan asked by the server, try 1" in h and "try 2" in h)
ck("6 row 5: the Second look buttons for Deepam 641", 'data-d="paper"' in h and 'data-d="scan_misread"' in h)
ck("6 row 5: the scan after two tries with Open paper and Accept", "rescanned 2 times, still: nothing read" in h and 'data-d="accept"' in h and "Open paper" in h)
ck("6 the strip holds the month", "NEFT on hold" in h, s736=False)
n_before = con.execute("SELECT COUNT(*) FROM purchase_audit").fetchone()[0]
_aud = [tuple(r) for r in con.execute("SELECT action, ref FROM purchase_audit")]
get("/finance/purchase/page/check?month=2026-10")
print("    new audit:", [tuple(r) for r in con.execute("SELECT action, ref FROM purchase_audit")][len(_aud):][:8], len(list(con.execute("SELECT id FROM scan_rescan_ask"))))
ck("6 the GET wrote nothing", con.execute("SELECT COUNT(*) FROM purchase_audit").fetchone()[0] == n_before and
   len(list(con.execute("SELECT id FROM scan_rescan_ask"))) == 5)
WHO["u"] = dict(user="amir", role="maker", roles=["maker"])
st, j = post("/finance/purchase/api/s736/decide", {"scan": 321, "decision": "scan_misread"})
ck("6 a maker is refused (403)", st == 403)
WHO["u"] = dict(user="manoj", role="checker", roles=["checker"])


def reg_row(bk):
    r = SR.register(con, "2026-10")
    return next((x for x in r["rows"] if x["id"] == BID[bk]), {})


ck("6 Deepam 641 is a second look before the tap", reg_row("deep").get("state") == "second_look", s736=False)
st, j = post("/finance/purchase/api/s736/decide", {"scan": 321, "decision": "scan_misread"})
ck("6 'Scan misread — settled' is taken (200)", st == 200 and j.get("ok"))
x = reg_row("deep")
ck("6 ... Deepam 641 is settled on the amount given (verified / has its scan) and the note says so",
   x.get("state") in ("verified", "has_scan") and "Your second look: the scan misread" in (x.get("note") or ""))
st, j = post("/finance/purchase/api/s736/decide", {"scan": 321, "decision": "paper"})
ck("6 a second decision is refused until undone (409)", st == 409)
st, j = post("/finance/purchase/api/s736/decide", {"scan": 321, "decision": "undo"})
ck("6 Undo (200) -- the pair is a second look again", st == 200 and reg_row("deep").get("state") == "second_look")
st, j = post("/finance/purchase/api/s736/decide", {"scan": 321, "decision": "paper"})
x = reg_row("deep")
ck("6 'Paper's figure stands' -> Amount differs, Amir's correction, ₹11.50", st == 200 and x.get("state") == "amount_differs" and
   x.get("whose") == "Amir: a Marg correction" and abs(int((x.get("agree") or {}).get("diff") or 0)) == 1150)
st, h = get("/finance/purchase/page/check?month=2026-10")
ck("6 ... the step view's Differences row carries Deepam 641 with Amir's name", "DEEPAM PHARMA 641 ₹11.50" in h and "Amir: a Marg correction" in h)
ck("6 ... and row 5 shows the decision with Undo", "<b>Decided</b>" in h and "DEEPAM PHARMA 641 · scan B-0321" in h and 'data-d="undo"' in h)
pst = con.execute("SELECT paper_amount, amount_state FROM purchase_scan_state WHERE asset_bill_id=321").fetchone()
ck("6 ... written as reception's own 'Marg galat' answer, so Amir's screen asks him (paper 4,762.50, marg_wrong)", bool(pst) and tuple(pst) == (476250, "marg_wrong"))
pb = con.execute("SELECT verdict, wrong_amount_p FROM purchase_bill WHERE id=?", (BID["deep"],)).fetchone()
ck("6 ... and the bill marked WRONG at 4,762.50 (S440's own branch)", bool(pb) and tuple(pb) == ("WRONG", 476250))
st, j = post("/finance/purchase/api/s736/decide", {"scan": 321, "decision": "undo"})
pst = con.execute("SELECT paper_amount, amount_state FROM purchase_scan_state WHERE asset_bill_id=321").fetchone()
ck("6 Undo of 'paper' puts reception's answer back (4,751, scan_wrong) -- a second look again", st == 200 and bool(pst) and tuple(pst) == (475100, "scan_wrong")
   and reg_row("deep").get("state") == "second_look")
pb = con.execute("SELECT verdict, wrong_amount_p FROM purchase_bill WHERE id=?", (BID["deep"],)).fetchone()
ck("6 ... and takes its WRONG mark off the bill", bool(pb) and tuple(pb) == (None, None))
st, j = post("/finance/purchase/api/s736/decide", {"scan": 321, "decision": "scan_misread"})
ck("6 'Scan misread' again (200)", st == 200 and reg_row("deep").get("state") in ("verified", "has_scan"))
a2 = sqlite3.connect(ADB)
a2.execute("UPDATE bills SET total_amount=4770.0 WHERE id=321")
a2.commit()
a2.close()
ck("6 a changed reading of the scan voids the decision (a second look again)", PLAN_OK and reg_row("deep").get("state") == "second_look")
a2 = sqlite3.connect(ADB)
a2.execute("UPDATE bills SET total_amount=4762.5 WHERE id=321")
a2.commit()
a2.close()
st, j = post("/finance/purchase/api/s736/decide", {"scan": 318, "decision": "accept"})
ck("6 Accept on the scan after two tries (200)", st == 200 and j.get("ok"))
ck("6 ... ACCEPTED TWICE 77 is no longer 'Paired, nothing read'", reg_row("acc").get("state") not in ("unread_pair", None))
p2 = safe(P4.s736_plan, con) if hasattr(P4, "s736_plan") else None
ck("6 ... and is no longer escalated; the server never asks for it", bool(p2) and 318 not in {x["scan"] for x in p2["escalated"] + p2["ask"]})
st, j = post("/finance/purchase/api/s736/decide", {"scan": 314, "decision": "accept"})
ck("6 Accept on a scan that is not waiting for the owner is refused", st == 409)
st, j = post("/finance/purchase/api/s736/decide", {"scan": 301, "decision": "paper"})
ck("6 'paper' on a pair that is not a second look is refused", st == 409)
ck("6 every decision audited", con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action IN ('s736_decision','s736_decision_undone')").fetchone()[0] == 6)

print("7 · the old pages still stand")
as_(RECEP, "sender")
for path in ("/finance/porders/s454/rescan", "/finance/porders/s454/rescan?old=1", "/finance/porders/s454/scan", "/finance/porders/s454/q",
             "/finance/porders/s454/q?nobill=1"):
    st, h = get(path)
    ck("7 %s answers 200" % path, st == 200, s736=False)
st, h = get("/finance/porders/s454/rescan")
ck("7 S708's reception page draws the server's asks in words (never the bare code 'unread')", "Kuch padha nahi gaya" in h and ">unread<" not in h)
st, h = get("/finance/porders/s454/q?nobill=1")
ck("7 ?nobill=1 leaves out the bill question of B-0320", PLAN_OK and ("17465" not in h or "Kya yeh" not in h))

if os.environ.get("S736_WALK_PAGES"):                        # the pages as drawn, for a reviewer's eyes
    _pd = os.environ["S736_WALK_PAGES"]
    os.makedirs(_pd, exist_ok=True)
    as_(RECEP, "sender")
    open(os.path.join(_pd, "billkaam.html"), "w").write(get("/finance/porders/s454/billkaam")[1])
    open(os.path.join(_pd, "home_reception.html"), "w").write(home()[1])
    as_(SHAVEZ, "sender")
    open(os.path.join(_pd, "scans_shavez.html"), "w").write(get("/finance/porders/s454/scans")[1])
    WHO["u"] = dict(user="manoj", role="checker", roles=["checker"])
    open(os.path.join(_pd, "check_owner.html"), "w").write(get("/finance/purchase/page/check?month=2026-10")[1])
print("8 · September raises nothing; a finalised month raises nothing; a scan moved off the lane loses its server ask")
ck("8 no ask was ever written for a September scan", PLAN_OK and not asks(303))

f8 = safe(P4._s736_facts, con) if hasattr(P4, "_s736_facts") else None
if f8:
    f8["final"] = set(f8["final"]) | {"2026-10"}
p8 = safe(P4.s736_plan, con, None, f8) if f8 else None
open_oct = {x["id"] for x in con.execute("SELECT id FROM scan_rescan_ask WHERE asked_by='server' AND done_at IS NULL AND withdrawn_at IS NULL")}
ck("8 a finalised October: nothing asked, nothing for the owner, its open server asks withdrawn", bool(p8) and not p8["ask"] and
   not [x for x in p8["escalated"] if x["month"] == "2026-10"] and set(p8["withdraw"]) == open_oct)
a2 = sqlite3.connect(ADB)
a2.execute("UPDATE bills SET lane='clinic' WHERE id=309")
a2.commit()
a2.close()
r8 = safe(P4.s736_raise, con) if hasattr(P4, "s736_raise") else None
ck("8 B-0309 moved to the clinic lane: its server ask is withdrawn by the server", bool(r8) and r8["withdrawn"] == 1 and not open_server(309))
n_s = len(S736F)
print("walk_s736: %d check(s) failed (%d of them S736 checks)" % (len(FAILS), n_s))
sys.exit(1 if FAILS else 0)
