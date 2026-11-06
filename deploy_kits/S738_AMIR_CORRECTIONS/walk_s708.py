#!/usr/bin/env python3
"""walk_s708.py -- S708 on a MADE-UP root (no real data, no phone): the finance code to test, a made-up finance.db (the real schema file)
and a made-up assets.db. The order rows are made-up S619 rows (order_track.light_all / full_all are stood in by them); the scan half,
the picks, the doors and the pages are the real code.
    python3 -B walk_s708.py <finance code dir to test> <purchase_schema.sql>
CONTROL: run it on the unchanged bundle code (no order_track_page.py) -- every S708 check must go red."""
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

try:
    import order_track_page as OTP                            # noqa: E402
except Exception:                                             # noqa: BLE001
    OTP = None

tmp = tempfile.mkdtemp(prefix="s708walk_")
FDB, ADB = os.path.join(tmp, "finance.db"), os.path.join(tmp, "assets.db")

# ---- the made-up assets.db: the scan app's columns the readers use
a = sqlite3.connect(ADB)
a.executescript("""
CREATE TABLE bills (id INTEGER PRIMARY KEY, stamp_no TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, bill_month TEXT, total_amount REAL,
  submitted_at TEXT, created_at TEXT, ocr_status TEXT, dup_of INTEGER, lane TEXT, status TEXT, kind TEXT, page_of INTEGER, rescan_of INTEGER,
  source_stored TEXT, doc_kind TEXT);
CREATE TABLE claude_reading (bill_id INTEGER, data TEXT, ok INTEGER, at TEXT);
CREATE TABLE scan_lie (bill_id INTEGER, file TEXT, at TEXT);
CREATE TABLE settings (key TEXT, value TEXT);
""")
NOW = OS.now().replace(microsecond=0)
T = (NOW - dt.timedelta(hours=6)).isoformat()


def bill(i, stamp, vendor, no, total, created=None, ext="pdf"):
    a.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, "
              "source_stored) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (i, stamp, vendor, no, NOW.date().isoformat(), NOW.date().isoformat()[:7], total, created or T, created or T, "read", "pharmacy", "captured",
               "Pharmacy", "f%d.%s" % (i, ext)))
    a.execute("INSERT INTO claude_reading VALUES (?,?,1,?)", (i, json.dumps(dict(bill_no=no, total_amount=total, vendor=vendor,
                                                                              items=[dict(name="ALPHA TAB", amount=total / 2), dict(name="BETA CAP", amount=total / 2)])), T))


bill(101, "B-9001", "DEALER ONE", "0447", 2340.0)            # one paper scanned twice: 101 and 102
bill(102, "B-9002", "DEALER ONE", "447", 2340.0, ext="jpg")
bill(103, "B-9003", "DEALER TWO", "5512", 990.0)             # a scan of its own (the not-in-Marg order's)
bill(104, "B-9004", "DEALER THREE", "7781", 410.0)           # saved under the wrong dealer, the paper unread
a.commit()
a.close()
purchase_app._assets_db = ADB

# ---- the made-up finance.db: the real schema, then the modules' own ensure
con = sqlite3.connect(FDB)
con.row_factory = sqlite3.Row
con.executescript(open(SCHEMA).read())
porders.ensure_schema(con)
OS.ensure(con)
for name in ("DEALER ONE", "DEALER TWO", "DEALER FOUR"):
    con.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, note) VALUES (?,?,?,?,?)",
                ((NOW - dt.timedelta(days=1)).isoformat(), "walk", name, "sent", "walk"))
con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, note) VALUES (7,?,?,?,?,?)",
            ((NOW - dt.timedelta(days=2)).isoformat(), "walk", "DEALER EIGHT", "received", "walk"))
con.execute("INSERT INTO scan_rescan_ask (asset_bill_id, stamp, reason, asked_by, asked_at) VALUES (102,'B-9002','blurred','shavez',?)", (T,))
con.commit()
ASK_ID = con.execute("SELECT id FROM scan_rescan_ask").fetchone()[0]


# ---- made-up S619 rows (the shape full_all leaves)
def row(i, vendor, key, **k):
    created = NOW - dt.timedelta(days=k.pop("age", 1))
    s = dict(id=i, sn="sn%d" % i, vendor=vendor, key=key, late=False, created_at=created.isoformat(), created=created, via="whatsapp", sent_at=created.isoformat(),
             n=2, came=0, short=0, open=2, part=False, arrived=False, arrived_at=None, arrived_how="", tap_at=None, due_at=created + dt.timedelta(days=1),
             scans=[], bills=[], complete=False, in_marg=False, scan_conflict=False, thumb="", file="", notes=[], soft={}, outside="",
             lines=[dict(id=i * 10 + 1, item="ALPHA TAB", state="open", short_text="10", how="", notes=[]),
                    dict(id=i * 10 + 2, item="BETA CAP", state="open", short_text="5", how="", notes=[])])
    s.update(k)
    return s


def scan(sid, stamp):
    return dict(scan=sid, stamp=stamp, head=sid, head_stamp=stamp, set_aside=False, head_set_aside=False, other="", scan_at=T)


ROWS = [row(1, "DEALER ONE", "not_arrived", late=True, age=3), row(2, "DEALER FOUR", "not_arrived"), row(3, "DEALER FIVE", "not_arrived"),
        row(4, "DEALER SIX", "not_arrived"), row(5, '<img src=x onerror=alert(1)> \'");x//', "not_arrived"),
        row(6, "DEALER TWO", "awaiting", arrived=True, arrived_at=NOW - dt.timedelta(hours=3), arrived_how="scan", scans=[scan(103, "B-9003")],
            thumb="/scanapp/bills/103/thumb", file="/scanapp/bills/103/file"),
        row(7, "DEALER EIGHT", "complete", arrived=True, arrived_at=NOW - dt.timedelta(days=2), in_marg=True, complete=True, came=2, open=0, bills=["A1"],
            lines=[dict(id=71, item="ALPHA TAB", state="came", short_text="", how="", notes=[])]),                       # never scanned
        row(8, "DEALER NINE", "complete", arrived=True, arrived_at=NOW - dt.timedelta(days=2), in_marg=True, complete=True, came=2, open=0,
            scans=[scan(103, "B-9003")], lines=[dict(id=81, item="ALPHA TAB", state="came", short_text="", how="", notes=[])]),
        row(9, "DEALER TEN", "short", arrived=True, arrived_at=NOW - dt.timedelta(days=2), in_marg=True, short=1, came=1, scans=[scan(103, "B-9003")],
            lines=[dict(id=91, item="ALPHA TAB", state="came", short_text="", how="", notes=[]), dict(id=92, item="GAMMA SYP", state="short", short_text="2", how="", notes=[])])]
OT.light_all = lambda con_, now_, *a_, **k_: [dict(r) for r in ROWS]
OT.full_all = lambda con_, now_, en=True, ctx=None, rows=None: rows
OT.wrong_dealer = lambda con_, ctx: [dict(scan=104, stamp="B-9004", date=NOW.date().isoformat(), saved="DEALER THREE", paper="DEALER ?")]
OT.paper_dealer = lambda con_, ctx, sid: ""
OT.short_words = lambda con_, s, x, en, marg=None, carries=None: "on the next order" if en else "agle order mein"
OS.book_card = lambda con_, vendor: ("x", "", True, True) if vendor == "DEALER ONE" else ("", "", False, False)
P4._tel = lambda p: "0"

# ---- the app and the logins
app = Flask("s708walk")
P4.init(app)
LOGIN = {}


def auth():
    u = LOGIN["u"]
    return u, con, LOGIN["kind"], None


porders._auth = auth
cl = app.test_client()
OWNER = dict(user="manoj", login="manoj", roles=["checker"])
SHAVEZ = dict(user="shavez", login="shavez", roles=["maker"])
RECEP = dict(user="reception", login="reception", roles=["maker"])
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


con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('porders.senders', 'shavez,reception')") if con.execute(
    "SELECT 1 FROM sqlite_master WHERE name='setting'").fetchone() else None
con.commit()

def sp(ctx):
    try:
        return OT.same_paper(con, ctx, asked_too=True)
    except TypeError:
        return []


def one(sql):
    try:
        return con.execute(sql).fetchone()[0]
    except (sqlite3.Error, TypeError):
        return 0


print("S708 walk on %s" % CODE)
# ---- 1 the page
as_(OWNER, "owner")
st, h = get("/finance/porders/s454/track")
check("1.1 the owner's page draws (200)", st == 200)
check("1.2 it is the S708 page (collapsible sections)", 'class="s7sec' in h)
check("1.3 every section is folded when the page opens", 'class="s7sec' in h and not re.search(r'<details class="s7sec[^"]*" id="\w+" open', h))
check("1.4 Expand all and Collapse all at the top", "s7all(true)" in h and "s7all(false)" in h and h.find("s7all(true)") < h.find('id="sec_na"'))
check("1.5 the Top button", 'class="s7up"' in h)
check("1.6 the scan viewer is on the page", 'id="s7v"' in h and "s7open(this)" in h)
check("1.7 not arrived: 5, the late one first, with Call and Goods arrived", re.search(r'id="sec_na".*?<span class="c"[^>]*>5<', h) is not None
      and h.find('data-order="1"') < h.find('data-order="2"') and "tel:" in h and "/s454/maal/1" in h)
check("1.8 only 3 not-arrived cards open, the other 2 behind 'Show the other 2'", "Show the other 2" in h)
check("1.9 the never-scanned order (7) is under Scan problems, not under Complete", 'data-nosc="7"' in h
      and 'data-order="7"' not in h[h.find('id="sec_done"'):])
check("1.10 Complete holds the scanned complete order (8) only", re.search(r'id="sec_done".*?<span class="c"[^>]*>1<', h) is not None)
check("1.11 the pair (B-9001 / B-9002) with two 'This one is right'", 'data-pair="101-102"' in h and h.count("This one is right</button>") == 2)
check("1.12 the open rescan ask, with its picture and View large", 'data-card="ask-%d"' % ASK_ID in h)
check("1.13 the unread wrong-dealer scan offers the dealers of the week's orders", 'data-wrong="104"' in h and "DEALER ONE</button>" in h and "DEALER FOUR</button>" in h)
nq = h.count('data-vq="1"')
check("1.14 'Check all scans one by one (%d)' counts the scan-problem pictures" % nq, nq >= 4 and ("Check all scans one by one (%d)" % nq) in h)
check("1.15 the To do box: the late call, the pair, the paper, the dealer", all(w in h for w in ("Late orders: 1", "Bills scanned twice: 1", "Bills never scanned: 1",
                                                                                                  "Under the wrong dealer: 1")))
check("1.16 no Roman Hindi on the owner's page", not any(w in h for w in ("kijiye", "dabaiye", "Nahi aaye", "Kam aaye")))
check("1.17 a PDF scan opens in the viewer as a PDF, a photo as a picture", 'data-vf="/scanapp/bills/101/file"' in h and 'data-vpdf="1"' in h and 'data-vpdf="0"' in h)
check("1.18 ?old=1 is the S619 page", 'class="grp"' in get("/finance/porders/s454/track?old=1")[1])
as_(SHAVEZ, "sender")
st, hs = get("/finance/porders/s454/track")
check("1.19 Shavez's page in Roman Hindi", st == 200 and "Nahi aaye" in hs and "Sab kholiye" in hs and "Yeh sahi hai" in hs)
check("1.20 a staff page under 100 KB", len(hs.encode()) < 100000)
as_(DARPAN, "sender")
check("1.21 Darpan is refused the list (403)", get("/finance/porders/s454/track")[0] == 403)
# a failing new page falls back to the old one
if OTP is not None:
    keep = OTP.page
    OTP.page = lambda *a_, **k_: 1 / 0
as_(OWNER, "owner")
st, hf = get("/finance/porders/s454/track")
check("1.23 a dealer name with markup is shown as text, never as markup", "<img src=x onerror" not in h and "&lt;img src=x onerror" in h)
check("1.22 if the new page fails, the S619 page is drawn", OTP is not None and st == 200 and 'class="grp"' in hf)
if OTP is not None:
    OTP.page = keep

# ---- 2 one bill scanned twice: the pick
ctx = OT.Ctx(con)
check("2.0 (before) the two scans are one paper twice", len(sp(ctx)) == 1)
as_(DARPAN, "sender")
st, j = post("/finance/porders/api/s454/s708/pick", dict(keep=101, drop=102))
check("2.1 Darpan cannot pick (403)", st == 403)
as_(SHAVEZ, "sender")
st, j = post("/finance/porders/api/s454/s708/pick", dict(keep=101, drop=103))
check("2.2 two scans that are not one paper are refused", st == 409 and j.get("error") == "not_a_pair")
st, j = post("/finance/porders/api/s454/s708/pick", dict(keep=101, drop=102))
check("2.3 Shavez keeps B-9001: done, and the card says so with Undo", st == 200 and j.get("ok") and "Kept" not in str(j.get("html")) and "Rakha gaya" in str(j.get("html"))
      and "/s708/pick/undo" in str(j.get("html")))
ctx = OT.Ctx(con)
check("2.4 the pair is gone; B-9002's head is B-9001; B-9002 is not usable", not sp(ctx) and ctx.head(102) == 101 and not ctx.usable(102) and ctx.usable(101))
r = con.execute("SELECT withdrawn_at, withdrawn_by FROM scan_rescan_ask WHERE id=?", (ASK_ID,)).fetchone()
check("2.5 B-9002's rescan request to reception is withdrawn by the pick", r[0] is not None and "S708" in str(r[1]))
st, j2 = post("/finance/porders/api/s454/s708/pick", dict(keep=101, drop=102))
check("2.6 picking again is refused", st == 409)
pid = one("SELECT id FROM s708_scan_pick")
st, j = post("/finance/porders/api/s454/s708/pick/undo", dict(id=pid))
ctx = OT.Ctx(con)
check("2.7 Undo: the pair is back", st == 200 and len(sp(ctx)) == 1)
st, j = post("/finance/porders/api/s454/s708/pick/undo", dict(id=pid))
check("2.8 Undo twice is refused", st == 409)
post("/finance/porders/api/s454/s708/pick", dict(keep=102, drop=101))
ctx = OT.Ctx(con)
check("2.9 picked the other way: B-9001 heads to B-9002", ctx.head(101) == 102 and not ctx.usable(101))

st, hk = get("/finance/porders/s454/track")
check("2.10 after a reload the picked pair shows the kept scan, with Undo", 'data-kept="' in hk and "/s708/pick/undo" in hk)
keep_sp = OT.same_paper
OT.same_paper = lambda con_, ctx, asked_too=False: [dict(a=101, b=102, sa="B-9001", sb="B-9002", bill="447")]
st, j = post("/finance/porders/api/s454/s708/pick", dict(keep=101, drop=102))
check("2.11 an opposite pick at the same moment is refused (one open pick per scan)", st == 409 and j.get("error") == "already_picked")
OT.same_paper = keep_sp
st, j = post("/finance/porders/api/s454/s708/pick", dict(keep=101, drop=103))
check("2.12 Shavez's refusals are in Roman Hindi", st == 409 and "nahi" in str(j.get("message")))
a4 = sqlite3.connect(ADB)
a4.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, "
           "source_stored) VALUES (106,'B-9006','DEALER ONE','447',?,?,2340.0,?,?,'read','pharmacy','captured','Pharmacy','f106.pdf')",
           (NOW.date().isoformat(), NOW.date().isoformat()[:7], T, T))
a4.execute("INSERT INTO claude_reading VALUES (106,?,1,?)", (json.dumps(dict(bill_no="447", total_amount=2340.0, items=[dict(name="ALPHA TAB", amount=1170.0),
                                                                                                                   dict(name="BETA CAP", amount=1170.0)])), T))
a4.commit()
a4.close()
st, j = post("/finance/porders/api/s454/s708/pick", dict(keep=102, drop=106))
ctx = OT.Ctx(con)
check("2.13 one bill scanned three times: the kept scan can be kept against the third too", st == 200 and ctx.head(106) == 102 and not sp(ctx))

# ---- 3 the paper never scanned -> reception
as_(SHAVEZ, "sender")
st, j = post("/finance/porders/api/s454/s708/paper", dict(order=8))
check("3.1 an order with its scan is refused", st == 409 and j.get("error") == "not_needed")
st, j = post("/finance/porders/api/s454/s708/paper", dict(order=7))
check("3.2 order 7 sent to reception", st == 200 and j.get("ok"))
st, j = post("/finance/porders/api/s454/s708/paper", dict(order=7))
check("3.3 sent twice is refused", st == 409)
check("3.4 reception's home row counts it", getattr(P4, "_s708_papers", lambda c_: -1)(con) == 1)
as_(RECEP, "sender")
st, hr = get("/finance/porders/s454/rescan")
pa_id = one("SELECT id FROM s708_paper_ask")
check("3.5 reception's list: the paper, with Scan karo to the intake (dealer, month, back to this list)", st == 200 and 'data-paper="%d"' % pa_id in hr
      and "/scanapp/intake?lane=pharmacy&amp;vendor=DEALER+EIGHT" in hr and "from=%2Ffinance%2Fporders%2Fs454%2Frescan" in hr and "Scan karo" in hr)
st, j = post("/finance/porders/api/s454/s708/lost", dict(kind="paper", id=pa_id))
check("3.6 reception: Kaagaz nahi mila", st == 200 and j.get("ok"))
st, hr = get("/finance/porders/s454/rescan")
check("3.7 reception's card now says so, with Mil gaya", "Mil gaya" in hr and "/s708/lost/clear" in hr)
as_(OWNER, "owner")
st, h = get("/finance/porders/s454/track")
check("3.8 the owner's page shows reception could not find it, and 'Ask again'", "Reception: paper not found" in h and "Ask again" in h and "Papers reception could not find: 1" in h)
lid = one("SELECT id FROM s708_lost")
st, j = post("/finance/porders/api/s454/s708/lost/clear", dict(id=lid))
check("3.9 Ask again clears it", st == 200 and "Reception: paper not found" not in get("/finance/porders/s454/track")[1])
as_(DARPAN, "sender")
check("3.10 Darpan cannot mark a paper lost", post("/finance/porders/api/s454/s708/lost", dict(kind="paper", id=pa_id))[0] == 403)
as_(RECEP, "sender")
check("3.11 a rescan ask that is not open cannot be marked lost", post("/finance/porders/api/s454/s708/lost", dict(kind="rescan", id=ASK_ID))[0] == 409)
as_(SHAVEZ, "sender")
st, j = post("/finance/porders/api/s454/s708/paper/withdraw", dict(id=pa_id))
check("3.12 withdrawn: off reception's list", st == 200 and getattr(P4, "_s708_papers", lambda c_: -1)(con) == 0)

# ---- 4 the dealer of an unread paper
as_(SHAVEZ, "sender")
st, j = post("/finance/porders/api/s454/s708/dealer", dict(scan=104, dealer="SOMEONE ELSE"))
check("4.1 a dealer not on the server's list is refused", st == 409 and j.get("error") == "not_a_choice")
k1 = OT._pa().supplier_key("DEALER FOUR")
st, j = post("/finance/porders/api/s454/s708/dealer", dict(scan=104, dealer=k1))
r = con.execute("SELECT value FROM s454_scan_answer WHERE asset_bill_id=104 AND kind='vendor' AND answer='chosen'").fetchone()
check("4.2 DEALER FOUR chosen: the answer is filed through S628's own door", st == 200 and j.get("ok") and r is not None and r[0] == k1)
OT.paper_dealer = lambda con_, ctx, sid: OT._pa().supplier_key("DEALER ONE")
check("4.3 a paper that IS read is refused here (Change dealer is its door)", post("/finance/porders/api/s454/s708/dealer", dict(scan=104, dealer=k1))[0] == 409)
st, j = post("/finance/porders/api/s454/dealer_fix", dict(scan=104))
r = con.execute("SELECT value FROM s454_scan_answer WHERE asset_bill_id=104 AND kind='vendor' AND answer='chosen'").fetchone()
check("4.4 Change dealer (S628) still works the same: filed as the paper's dealer", st == 200 and j.get("ok") and j.get("dealer") == OT._pa().supplier_key("DEALER ONE")
      and r is not None and r[0] == OT._pa().supplier_key("DEALER ONE"))

# ---- 5 reception's rescans
con.execute("INSERT INTO scan_rescan_ask (asset_bill_id, stamp, reason, asked_by, asked_at) VALUES (103,'B-9003','cut','shavez',?)", (T,))
con.commit()
a2 = con.execute("SELECT MAX(id) FROM scan_rescan_ask").fetchone()[0]
as_(RECEP, "sender")
st, hr = get("/finance/porders/s454/rescan")
check("5.1 reception's rescan card: the old scan, what was wrong, how to scan it, Scan karo (rescan_of)", 'data-ask="%d"' % a2 in hr and "Pichhla scan" in hr
      and "Chaaron kone" in hr and "rescan_of=103" in hr)
check("5.2 ?old=1 is S618's list", "s7c" not in get("/finance/porders/s454/rescan?old=1")[1])
# ---- 6 a paper scanned for an ask: reception says so, a person picks the scan, nothing is tied by itself
as_(SHAVEZ, "sender")
st, j = post("/finance/porders/api/s454/s708/paper", dict(order=7))
check("6.1 order 7 sent to reception again", st == 200)
ask7 = one("SELECT MAX(id) FROM s708_paper_ask")
a3 = sqlite3.connect(ADB)
later = (NOW + dt.timedelta(minutes=2)).isoformat()
a3.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, "
           "source_stored) VALUES (105,'B-9005','DEALER EIGHT','881',?,?,500,?,?,'read','pharmacy','captured','Pharmacy','f105.pdf')",
           (NOW.date().isoformat(), NOW.date().isoformat()[:7], later, later))
a3.execute("INSERT INTO claude_reading VALUES (105,?,1,?)", (json.dumps(dict(bill_no="881", total_amount=500.0, items=[dict(name="ALPHA TAB", amount=500.0)])), later))
a3.commit()
a3.close()
P4._every_read(con)
check("6.2 reception's new scan is NOT tied to the order by itself", one("SELECT COUNT(*) FROM order_scan_tie WHERE asset_bill_id=105") == 0)
as_(RECEP, "sender")
st, j = post("/finance/porders/api/s454/s708/paper/scanned", dict(id=ask7))
check("6.3 reception: Scan ho gaya -- off reception's row and list", st == 200 and getattr(P4, "_s708_papers", lambda c_: -1)(con) == 0
      and 'data-paper="' not in get("/finance/porders/s454/rescan")[1])
as_(SHAVEZ, "sender")
st, h6 = get("/finance/porders/s454/track")
check("6.4 Shavez sees 'which scan is this order's bill?' with B-9005 (and not an older or other dealer's scan)", "kaunsa scan is order ka bill hai" in h6
      and "B-9005" in h6 and "Yeh iska bill hai" in h6 and h6.count("/s708/paper/tie") == 1)
st, j = post("/finance/porders/api/s454/s708/paper/reask", dict(id=ask7))
ask7b = one("SELECT MAX(id) FROM s708_paper_ask")
check("6.5 Send to reception again: the old ask kept as withdrawn, a new one on reception's row", st == 200 and ask7b != ask7
      and one("SELECT COUNT(*) FROM s708_paper_ask WHERE id=%d AND withdrawn_at IS NOT NULL" % int(ask7 or 0)) == 1 and P4._s708_papers(con) == 1)
as_(RECEP, "sender")
post("/finance/porders/api/s454/s708/paper/scanned", dict(id=ask7b))
as_(SHAVEZ, "sender")
st, j = post("/finance/porders/api/s454/s708/paper/tie", dict(id=ask7b, scan=103))
check("6.6 a scan that cannot be this order's is refused", st == 409 and j.get("error") == "not_a_cand")
as_(RECEP, "sender")
check("6.7 reception cannot tie a scan", post("/finance/porders/api/s454/s708/paper/tie", dict(id=ask7b, scan=105))[0] == 403)
as_(SHAVEZ, "sender")
st, j = post("/finance/porders/api/s454/s708/paper/tie", dict(id=ask7b, scan=105))
t = con.execute("SELECT order_id, how FROM order_scan_tie WHERE asset_bill_id=105").fetchone()
check("6.8 This is its bill: B-9005 tied to order 7 (how paper_ask)", st == 200 and t is not None and t[0] == 7 and t[1] == "paper_ask")
check("6.9 the ask has closed itself", OTP is not None and 7 not in OTP.paper_asks(con))
check("6.10 tying again is refused", post("/finance/porders/api/s454/s708/paper/tie", dict(id=ask7b, scan=105))[0] == 409)
# ---- 7 R3: a scan-app family whose scan is picked as the copy; cancelled and "came another way" asks
a5 = sqlite3.connect(ADB)
for i, dup in ((120, None), (121, 120), (122, None)):
    a5.execute("INSERT INTO bills (id, stamp_no, vendor, bill_no, bill_date, bill_month, total_amount, submitted_at, created_at, ocr_status, lane, status, kind, "
               "source_stored, dup_of) VALUES (?,?,'DEALER ELEVEN','9901',?,?,300.0,?,?,'read','pharmacy','captured','Pharmacy',?,?)",
               (i, "B-%d" % (9000 + i), NOW.date().isoformat(), NOW.date().isoformat()[:7], T, T, "f%d.pdf" % i, dup))
    a5.execute("INSERT INTO claude_reading VALUES (?,?,1,?)", (i, json.dumps(dict(bill_no="9901", total_amount=300.0, items=[dict(name="ALPHA TAB", amount=150.0),
                                                                                                                       dict(name="BETA CAP", amount=150.0)])), T))
a5.commit()
a5.close()
ctx = OT.Ctx(con)
pr = [p for p in sp(ctx) if {int(p["a"]), int(p["b"])} == {120, 122}]
as_(SHAVEZ, "sender")
st, j = post("/finance/porders/api/s454/s708/pick", dict(keep=122, drop=120))
ctx = OT.Ctx(con)
check("7.1 the scan app's copy of a picked copy stays a copy (heads to the kept scan, never usable)", len(pr) == 1 and st == 200 and ctx.head(121) == 122
      and not ctx.usable(121) and not [p for p in sp(ctx) if 121 in (int(p["a"]), int(p["b"]))])
con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, note) VALUES (12,?,?,?,?,?)", (T, "walk", "DEALER TWELVE", "cancelled", "walk"))
con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, note) VALUES (8,?,?,?,?,?)", (T, "walk", "DEALER NINE", "received", "walk"))
n0 = getattr(P4, "_s708_papers", lambda c_: -1)(con)
if OTP is not None:
    OTP.ensure(con)
try:
    con.execute("INSERT INTO s708_paper_ask (order_id, asked_by, asked_at) VALUES (12,'shavez',?)", (T,))
    con.execute("INSERT INTO s708_paper_ask (order_id, asked_by, asked_at) VALUES (8,'shavez',?)", (T,))
except sqlite3.Error:
    pass
con.commit()
ask12, ask8 = one("SELECT id FROM s708_paper_ask WHERE order_id=12"), one("SELECT id FROM s708_paper_ask WHERE order_id=8")
check("7.2 an ask on a cancelled order is not reception's work and cannot be sent again", n0 >= 0 and P4._s708_papers(con) == n0 + 1
      and post("/finance/porders/api/s454/s708/paper/reask", dict(id=ask12))[0] == 409)
st, h7 = get("/finance/porders/s454/track")
check("7.3 an ask whose order has its scan another way is shown with Withdraw", 'data-stale="%d"' % int(ask8 or 0) in h7 and "reception wala kaam wapas lijiye" in h7)
st, j = post("/finance/porders/api/s454/s708/paper/withdraw", dict(id=ask8))
check("7.4 ... and Withdraw takes it off reception's row", st == 200 and P4._s708_papers(con) == n0)
check("7.5 the never-scanned card names the order's medicines", re.search(r'data-nosc="7".*?ALPHA TAB', h7, re.S) is not None)
print("WALK S708: %d ok, %d red" % (ok, bad))
