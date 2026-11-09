#!/usr/bin/env python3
"""walk_s711.py -- S711 on a MADE-UP root (no real data, no phone): the finance code to test, a made-up finance.db (the real schema file plus
the columns the live box carries) and a made-up assets.db. The order rows and S628's two readers (order_track.wrong_dealer / paper_dealer)
are stood in by made-up ones; the card, the doors, the dealer core, the S454 tie and the old reception list are the real code.
    python3 -B walk_s711.py <finance code dir to test> <purchase_schema.sql>
CONTROL: run it on the code before S711 (order_track_page b6181b62, porders_s454 1bc312dd, order_sheet 1bba95ab) -- the S711 checks go red."""
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import tempfile

CODE, SCHEMA = sys.argv[1], sys.argv[2]
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(CODE)), "shared"))
ok = bad = 0


def check(name, cond):
    global ok, bad
    print(("  ok   " if cond else "  RED  ") + name)
    ok += bool(cond)
    bad += (not cond)


from flask import Flask                                       # noqa: E402

import order_sheet as OS                                      # noqa: E402
import order_track as OT                                      # noqa: E402
import porders                                                # noqa: E402
import porders_s454 as P4                                     # noqa: E402
import purchase_app                                           # noqa: E402
import order_track_page as OTP                                # noqa: E402

tmp = tempfile.mkdtemp(prefix="s711walk_")
FDB, ADB = os.path.join(tmp, "finance.db"), os.path.join(tmp, "assets.db")
NOW = OS.now().replace(microsecond=0, tzinfo=None)
TODAY = NOW.date().isoformat()

a = sqlite3.connect(ADB)
a.executescript("""
CREATE TABLE bills (id INTEGER PRIMARY KEY, stamp_no TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, bill_month TEXT, total_amount REAL,
  submitted_at TEXT, created_at TEXT, ocr_status TEXT, dup_of INTEGER, lane TEXT, status TEXT, kind TEXT, page_of INTEGER, rescan_of INTEGER,
  source_stored TEXT, doc_kind TEXT);
CREATE TABLE claude_reading (bill_id INTEGER, data TEXT, ok INTEGER, at TEXT);
CREATE TABLE scan_lie (bill_id INTEGER, file TEXT, at TEXT);
CREATE TABLE settings (key TEXT, value TEXT);
""")


def bill(i, stamp, vendor, no, total, hours=3, read_vendor=None):
    at = (NOW - dt.timedelta(hours=hours)).isoformat()
    a.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, "
              "source_stored) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (i, stamp, vendor, no, TODAY, TODAY[:7], total, at, at, "read", "pharmacy", "captured", "Pharmacy", "f%d.pdf" % i))
    a.execute("INSERT INTO claude_reading VALUES (?,?,1,?)", (i, json.dumps(dict(bill_no=no, total_amount=total, vendor=read_vendor or vendor,
                                                                              items=[dict(name="ALPHA TAB", amount=total)])), at))


bill(239, "B-0239", "A.A. PHARMACEUTICALS", "7001", 1200.0, read_vendor="A.A.I.PHARMACEUTICALS")   # the owner's case: slanted, misread
bill(240, "B-0240", "DEALER ONE", "7002", 800.0)               # tied to DEALER ONE's order (arrived by the tie); its paper is DEALER TWO's
bill(241, "B-0241", "DEALER NINE", "7003", 500.0)              # a scan already with reception for a rescan
bill(250, "B-0250", "KAPPA MED", "8001", 300.0, hours=4)       # F-1120: one paper twice -- 250 picked as the copy, 251 kept
bill(251, "B-0251", "KAPPA MED", "8001", 300.0, hours=3)
a.commit()
a.close()
purchase_app._assets_db = ADB

con = sqlite3.connect(FDB)
con.row_factory = sqlite3.Row
con.executescript(open(SCHEMA).read())
for col in ("received_at", "received_by", "sent_by", "section"):
    try:
        con.execute("ALTER TABLE purchase_order ADD COLUMN %s TEXT" % col)
    except sqlite3.Error:
        pass
porders.ensure_schema(con)
OS.ensure(con)
OTP.ensure(con)


def order(vendor, days=1, status="sent", oid=None):
    cur = con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, note, supplier_norm) VALUES (?,?,?,?,?,?,?)",
                      (oid, (NOW - dt.timedelta(days=days)).isoformat(), "walk", vendor, status, "walk", OS._pa().supplier_key(vendor)))
    return cur.lastrowid


WEEK = ["YOGENDRA AGENCIES", "SHRADDHA MEDICOSE", "SHIVAAZ FORMULATIONS", "MANNAT PHARMA", "L.K. DRUG HOUSE", "KEDAR PHARMACEUTICAL"]
for i, v in enumerate(WEEK):                                  # six dealers ordered from that week -- S708 cut the saved dealer off here
    order(v, days=1 + i * 0.1)
O_ONE = order("DEALER ONE", days=2, status="received")
O_TWO = order("DEALER TWO", days=1)
O_KAPPA = order("KAPPA MED", days=1)
con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month) VALUES (?,?,?,?,?)",
            (OS._pa().supplier_key("A.A. PHARMACEUTICALS"), "A.A. PHARMACEUTICALS", "X1", "2026-10-01", "2026-10"))
con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month) VALUES (?,?,?,?,?)",
            (OS._pa().supplier_key("ZETA REMEDIES"), "ZETA REMEDIES", "Z1", "2026-09-01", "2026-09"))   # a dealer of no order that week
con.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month) VALUES (?,?,?,?,?)",
            ("XSCRIPT", "X</script><b>EVIL", "E1", "2026-08-01", "2026-08"))                                # markup in a dealer's name
at240 = (NOW - dt.timedelta(hours=3)).isoformat()
con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,1)",
            (O_ONE, 240, "B-0240", at240, at240, "scan"))
con.execute("UPDATE purchase_order SET received_at=?, received_by=? WHERE id=?", (at240, "bill scan B-0240", O_ONE))
con.execute("INSERT INTO scan_rescan_ask (asset_bill_id, stamp, reason, asked_by, asked_at) VALUES (241,'B-0241','blurred','shavez',?)", (at240,))
con.execute("INSERT INTO s708_scan_pick (keep_id, drop_id, picked_by, picked_at) VALUES (251, 250, 'shavez', ?)", (NOW.isoformat(),))   # F-1120
con.commit()

ROWS = []
OT.light_all = lambda con_, now_, *a_, **k_: [dict(r) for r in ROWS]
OT.full_all = lambda con_, now_, en=True, ctx=None, rows=None: rows
PAPER = {}                                                    # scan -> the paper's dealer key when its reading names a known dealer
WRONG = {239: ("A.A. PHARMACEUTICALS", "A.A.I.PHARMACEUTICALS"), 240: ("DEALER ONE", "DEALER TWO"), 241: ("DEALER NINE", "DEALER X")}


def _wrong(con_, ctx):
    return [dict(scan=s, stamp="B-%04d" % s, date=TODAY, saved=v[0], paper=v[1]) for s, v in sorted(WRONG.items()) if s not in getattr(ctx, "chosen", {})]


OT.wrong_dealer = _wrong
OT.paper_dealer = lambda con_, ctx, sid: PAPER.get(int(sid), "")
OS.book_card = lambda con_, vendor: ("", "", False, False)
P4._tel = lambda p: "0"

app = Flask("s711walk")
P4.init(app)
LOGIN = {}
porders._auth = lambda: (LOGIN["u"], con, LOGIN["kind"], None)
cl = app.test_client()
OWNER = dict(user="manoj", login="manoj", roles=["checker"])
SHAVEZ = dict(user="shavez", login="shavez", roles=["maker"])
DARPAN = dict(user="darpan", login="darpan", roles=["maker"])


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


def card(h, sid):
    i = h.find('data-wrong="%d"' % sid)
    if i < 0:
        return ""
    j = h.find('<div class="s7c"', i + 10)
    return h[i:j if j > 0 else i + 20000]


def ex(sql, *p):
    try:
        con.execute(sql, p)
        con.commit()
    except sqlite3.Error:
        pass


def one(sql, *p):
    try:
        r = con.execute(sql, p).fetchone()
    except sqlite3.Error:
        return None
    return r[0] if r else None


K_AA = OS._pa().supplier_key("A.A. PHARMACEUTICALS")
K_TWO = OS._pa().supplier_key("DEALER TWO")
K_ZETA = OS._pa().supplier_key("ZETA REMEDIES")
print("S711 walk on %s" % CODE)

# ---- 1 the viewer on a PC
src = open(os.path.join(CODE, "order_track_page.py"), encoding="utf-8").read()
check("1.1 on a PC the viewer is two columns: the bill left, the card's words and buttons right", "#s7v .vb>.vact{grid-column:2" in src
      and "grid-template-columns:minmax(0,1fr) clamp(240px,26%,340px)" in src)
check("1.2 the bill's frame fills the height (no room left below it for the buttons)", "#s7v .vimg iframe{height:calc(100vh - 170px)}" in src)
check("1.3 S710's PDF opening kept (no thumbnail strip, full width)", "fr.src=f+'#navpanes=0&view=FitH';" in src)

# ---- 2 the wrong-dealer card (the owner's B-0239)
as_(OWNER, "owner")
st, h = get("/finance/porders/s454/track")
c = card(h, 239)
check("2.1 the owner's page draws (200), the S708 page", st == 200 and 'class="s7sec' in h)
check("2.2 B-0239 says the dealer could not be read clearly, and what was read", "could not be read clearly" in c and "A.A.I.PHARMACEUTICALS" in c)
check("2.3 ... with 'A.A. PHARMACEUTICALS is right (as saved)' even after six dealers that week", "A.A. PHARMACEUTICALS is right (as saved)</button>" in c)
nweek = sum(1 for v in WEEK + ["DEALER ONE", "DEALER TWO", "KAPPA MED"] if ("%s</button>" % v) in c)
check("2.4 ... the week's dealers still offered beside it (8 of the 9 ordered from that week, newest first)", nweek == 8)
check("2.5 ... 'Other dealer' with the full list on the page (a dealer of no order that week is in it)", "s7other(this" in c and "var S7DL=" in h
      and "ZETA REMEDIES" in h[h.find("var S7DL="):h.find("var S7DL=") + 4000])
check("2.6 ... 'Send back for rescan' on the card", "/api/s454/rescan" in c and "Send back for rescan" in c)
check("2.7 a scan already with reception for a rescan is not asked about its dealer too", 'data-wrong="241"' not in h)
check("2.8 no 'Change dealer' when the paper is not read", "Change dealer to" not in c)
if os.environ.get("S711_DUMP"):                              # the Chromium layout check reads this page (js_s711.py)
    open(os.environ["S711_DUMP"], "w", encoding="utf-8").write(h)
as_(SHAVEZ, "sender")
st, hs = get("/finance/porders/s454/track")
cs = card(hs, 239)
check("2.9 Shavez's card in Roman Hindi", "saaf nahi padha gaya" in cs and "sahi hai (jaisa save hai)" in cs and "Koi aur dealer" in cs)
_i = hs.find("var S7DL=")
_dl = hs[_i:hs.find(";</script>", _i)] if _i >= 0 else ""
check("2.10 the dealer list is plain data: a name with markup ('X</script><b>EVIL') rides escaped, never as markup", _i >= 0 and "EVIL" in _dl
      and "<" not in _dl and "</script><b>EVIL" not in hs)

# ---- 3 the dealer door
as_(DARPAN, "sender")
check("3.1 Darpan cannot change a dealer (403)", post("/finance/porders/api/s454/s708/dealer", dict(scan=239, dealer=K_AA))[0] == 403)
as_(SHAVEZ, "sender")
st, j = post("/finance/porders/api/s454/s708/dealer", dict(scan=239, dealer="NOBODY AT ALL"))
check("3.2 a dealer on none of the server's lists is refused", st == 409 and j.get("error") == "not_a_choice")
st, j = post("/finance/porders/api/s454/s708/dealer", dict(scan=239, dealer=K_AA))
check("3.3 'is right (as saved)': filed as A.A. PHARMACEUTICALS, the reply offers Undo", st == 200 and j.get("ok") and "/s711/dealer/undo" in str(j.get("html"))
      and one("SELECT value FROM s454_scan_answer WHERE asset_bill_id=239 AND kind='vendor' AND answer='chosen'") == K_AA)
as_(OWNER, "owner")
st, h = get("/finance/porders/s454/track")
check("3.4 after a reload B-0239 has left the wrong-dealer list and shows under 'Dealer changed (7 days)' with Undo", 'data-wrong="239"' not in h
      and "Dealer changed (7 days)" in h and 'data-chg="' in h)
cid = one("SELECT id FROM s711_dealer_change WHERE scan=239")
st, j = post("/finance/porders/api/s454/s711/dealer/undo", dict(id=cid))
st2, h = get("/finance/porders/s454/track")
check("3.5 Undo: the answer is gone, B-0239 is back on the list", st == 200 and one("SELECT COUNT(*) FROM s454_scan_answer WHERE asset_bill_id=239") == 0
      and 'data-wrong="239"' in h)
check("3.6 Undo twice is refused", post("/finance/porders/api/s454/s711/dealer/undo", dict(id=cid))[0] == 409)
as_(DARPAN, "sender")
check("3.6b Darpan cannot undo (403)", post("/finance/porders/api/s454/s711/dealer/undo", dict(id=cid))[0] == 403)
as_(OWNER, "owner")
st, j = post("/finance/porders/api/s454/s708/dealer", dict(scan=239, dealer=K_ZETA))
check("3.7 a dealer from the full list only (no order that week) is accepted", st == 200 and j.get("ok"))
cz = one("SELECT MAX(id) FROM s711_dealer_change WHERE scan=239")
st, h = get("/finance/porders/s454/track")
check("3.7b the changed card names the dealer as written ('now: ZETA REMEDIES')", "now: ZETA REMEDIES" in h)
O_P = order("PERSON TIE", days=1)
con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,0)",
            (O_P, 239, "B-0239", at240, (NOW + dt.timedelta(minutes=5)).isoformat(), "paper_ask"))
con.commit()
st, j = post("/finance/porders/api/s454/s711/dealer/undo", dict(id=cz))
check("3.7c a person's tie made after the change is never removed by Undo (refused)", st == 409 and j.get("error") == "moved_on"
      and one("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=239") == O_P)
ex("UPDATE order_scan_tie SET how='scan_made_order' WHERE asset_bill_id=239")
ex("UPDATE s711_dealer_change SET tie_to=? WHERE id=?", O_P, cz)
st, j = post("/finance/porders/api/s454/s711/dealer/undo", dict(id=cz))
check("3.7d an order made from this bill by the S454 tie: Undo refused, nothing changed", st == 409 and j.get("error") == "made_order"
      and one("SELECT undone_at FROM s711_dealer_change WHERE id=?", cz) is None)
ex("DELETE FROM order_scan_tie WHERE asset_bill_id=239")
ex("UPDATE s711_dealer_change SET tie_to=NULL WHERE id=?", cz)
post("/finance/porders/api/s454/s711/dealer/undo", dict(id=cz))

# ---- 4 F-1121: the dealer core no longer ties by itself; the S454 tie does; Undo puts the ties back
PAPER[240] = K_TWO
st, h = get("/finance/porders/s454/track")
c = card(h, 240)
check("4.1 a paper read as a known dealer: 'Change dealer to DEALER TWO' (one door), the saved dealer, Other dealer, rescan", "Change dealer to DEALER TWO" in c
      and "/api/s454/s708/dealer" in c and "DEALER ONE is right (as saved)" in c and "s7other(this" in c and "/api/s454/rescan" in c)
st, j = post("/finance/porders/api/s454/s708/dealer", dict(scan=240, dealer=K_TWO))
t = con.execute("SELECT order_id, how FROM order_scan_tie WHERE asset_bill_id=240").fetchone()
o1 = con.execute("SELECT status, received_by FROM purchase_order WHERE id=?", (O_ONE,)).fetchone()
check("4.2 changed to DEALER TWO (a read paper is no longer refused here)", st == 200 and j.get("ok"))
check("4.3 DEALER ONE's tie is removed and the arrival only that tie made is undone (the order waits again)", o1[0] == "sent" and o1[1] is None)
check("4.4 the scan is tied to DEALER TWO's waiting order by the S454 tie (how 'scan'), not by the door", t is not None and t[0] == O_TWO and t[1] == "scan")
check("4.5 the reply names the order it is tied to", "tied to the order of" in str(j.get("html")))
check("4.6 no tie of the door's own kind is made any more", one("SELECT COUNT(*) FROM order_scan_tie WHERE how='dealer_fix'") == 0)
cid = one("SELECT MAX(id) FROM s711_dealer_change WHERE scan=240")
st, j = post("/finance/porders/api/s454/s711/dealer/undo", dict(id=cid))
t = con.execute("SELECT order_id FROM order_scan_tie WHERE asset_bill_id=240").fetchone()
o1 = con.execute("SELECT status, received_by FROM purchase_order WHERE id=?", (O_ONE,)).fetchone()
o2 = con.execute("SELECT status FROM purchase_order WHERE id=?", (O_TWO,)).fetchone()
check("4.7 Undo: back on DEALER ONE's order, which is arrived again; DEALER TWO's order waits again", st == 200 and t is not None and t[0] == O_ONE
      and o1[0] == "received" and o1[1] == "bill scan B-0240" and o2[0] == "sent")
post("/finance/porders/api/s454/s708/dealer", dict(scan=240, dealer=K_TWO))
c1 = one("SELECT MAX(id) FROM s711_dealer_change WHERE scan=240")
post("/finance/porders/api/s454/s711/dealer/undo", dict(id=c1))
post("/finance/porders/api/s454/s708/dealer", dict(scan=240, dealer=K_TWO))
c2 = one("SELECT MAX(id) FROM s711_dealer_change WHERE scan=240")
ex("DELETE FROM s454_scan_answer WHERE asset_bill_id=240")    # back on the wrong-dealer list, so a newer change can be made
post("/finance/porders/api/s454/s708/dealer", dict(scan=240, dealer=K_ZETA))
st, j = post("/finance/porders/api/s454/s711/dealer/undo", dict(id=c2))
check("4.8 an older change cannot be undone once a newer one was made", st == 409 and j.get("error") == "moved_on")
c3 = one("SELECT MAX(id) FROM s711_dealer_change WHERE scan=240")
ex("UPDATE s454_scan_answer SET value=?, at=? WHERE asset_bill_id=240 AND kind='vendor'", K_TWO, (NOW + dt.timedelta(hours=1)).isoformat())
st, j = post("/finance/porders/api/s454/s711/dealer/undo", dict(id=c3))
check("4.9 a dealer answered another way after the change (S440's door) is never overwritten by Undo (refused)", st == 409 and j.get("error") == "moved_on"
      and one("SELECT value FROM s454_scan_answer WHERE asset_bill_id=240 AND kind='vendor'") == K_TWO)
keep_tp = OS.tie_pass
OS.tie_pass = lambda con_, who="tie": (con_.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, note) VALUES ('x','x','HALF','sent','x')"), 1 / 0)
st, j = post("/finance/porders/api/s454/s708/dealer", dict(scan=239, dealer=K_AA))
OS.tie_pass = keep_tp
check("4.10 a tie pass that fails inside a change: the change is kept, the pass's half-written order is not", st == 200 and j.get("ok")
      and one("SELECT COUNT(*) FROM purchase_order WHERE vendor='HALF'") == 0 and one("SELECT value FROM s454_scan_answer WHERE asset_bill_id=239 AND kind='vendor'") == K_AA)

# ---- 5 F-1120: the S454 tie never ties a scan picked as the copy
OS.tie_pass(con, "walk")
t = con.execute("SELECT asset_bill_id FROM order_scan_tie WHERE order_id=?", (O_KAPPA,)).fetchone()
check("5.1 KAPPA MED's order is tied to the KEPT scan B-0251, never the copy B-0250", t is not None and t[0] == 251
      and one("SELECT COUNT(*) FROM order_scan_tie WHERE asset_bill_id=250") == 0)

# ---- 6 F-1123: S618's old reception list with the scan app's database unreachable
keep = OS._assets
OS._assets = lambda: None
try:
    x = P4.rescan_list(con)
    shape = all("by_owner" in q and "vendor" in q and "month" in q for q in x["asks"]) and len(x["asks"]) >= 1
except Exception:                                             # noqa: BLE001
    shape = False
as_(SHAVEZ, "sender")
st, hr = get("/finance/porders/s454/rescan?old=1")
OS._assets = keep
check("6.1 the asks have their whole shape when the scan app cannot be opened", shape)
check("6.2 the old reception list draws (200) then", st == 200)

# ---- 7 S708's own walk on the same code: green but for 4.3, the one S708 rule S711 changes on purpose (a read paper may be set by a person too)
import subprocess                                             # noqa: E402
w708 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "walk_s708.py")
r = subprocess.run([sys.executable, "-W", "ignore", "-B", w708, os.path.abspath(CODE), os.path.abspath(SCHEMA)], capture_output=True, text=True, timeout=600, cwd="/tmp")
reds = [ln.strip() for ln in r.stdout.splitlines() if ln.startswith("  RED")]
last = (r.stdout.strip().splitlines() or [""])[-1]
check("7.1 S708's walk on the same code: %s -- the only red its 4.3 (changed on purpose)" % last,
      last == "WALK S708: 69 ok, 1 red" and len(reds) == 1 and reds[0].startswith("RED  4.3"))
print("WALK S711: %d ok, %d red" % (ok, bad))
