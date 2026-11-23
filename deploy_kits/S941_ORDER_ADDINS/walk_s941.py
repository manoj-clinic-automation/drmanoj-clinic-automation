#!/usr/bin/env python3
"""walk_s941.py -- kit S941 walked on a COPY of finance.db (never the live one) and a MADE-UP assets db (no patient paper).
argv: <code dir: S939+S940+S941> <copy.db> [control]. Pushes into a stub file. Checks E late, F nudges (and the doctor after them),
G summary, H wrong bill (its page, Keep / Send back, reception's Wapas kar diya), his step 1 = Marg's open order. CONTROL (S940) red."""
import atexit, datetime as dt, json, os, shutil, sqlite3, sys, tempfile
CODE, SRC = sys.argv[1], sys.argv[2]
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, CODE)
os.environ["NEEDS_YOU_WITHOUT_S408"] = "1"
TMP = tempfile.mkdtemp(prefix="w941_", dir=os.environ.get("TMPDIR") or "/tmp")
STUB = os.path.join(TMP, "stub.jsonl"); open(STUB, "w").close()
os.environ["ORDER_PUSH_STUB"] = STUB
DB = os.path.join(TMP, "copy.db"); shutil.copy(SRC, DB)
os.environ["FINANCE_DB"] = DB
ADB = os.path.join(TMP, "assets.db")
os.environ["ASSETS_DB"] = ADB
FAIL = []; DONE = [False]
def _bye():
    shutil.rmtree(TMP, ignore_errors=True)
    if not DONE[0]:
        print("RESULT: stopped on an error, %d FAIL" % (len(FAIL) + 1))
atexit.register(_bye)
def ok(c, w):
    print(("PASS " if c else "FAIL ") + w)
    if not c:
        FAIL.append(w)
from flask import Flask
import porders as PO, darpan_kal as DK, order_sheet as OS, order_rules as OR, purchase_app as PA
PA._assets_db = ADB
WHO = {"u": "manoj"}
USERS = {"manoj": ["checker"], "alisha": ["maker"], "darpan": ["maker"]}
_C = {}
def dbg():
    if "c" not in _C:
        _C["c"] = sqlite3.connect(DB, timeout=5, check_same_thread=False); _C["c"].row_factory = sqlite3.Row
    return _C["c"]
def req(*r, unit=None):
    return dict(user=WHO["u"], login=WHO["u"], roles=USERS[WHO["u"]]), None
app = Flask(__name__); app.config["PROPAGATE_EXCEPTIONS"] = True
PO.init(app, dbg, req); DK.init(app, dbg, req, "medical")
cl = app.test_client(); con = dbg()
import order_d1053 as D, order_d1053_msg as M
D.ensure(con); M.ensure(con)
def setv(k, v):
    con.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v)); con.commit()
def push(kind=None):
    P = [json.loads(l) for l in open(STUB, encoding="utf-8") if l.strip()]
    return [p for p in P if kind is None or p["payload"]["tag"] == "d1053-" + kind]
def tick():
    with app.app_context():
        return OR._s454_pass(con)
def post(w, url, b):
    WHO["u"] = w; r = cl.post(url, json=b); return r.status_code, (r.get_json(silent=True) or {})
def page(w, url):
    WHO["u"] = w; r = cl.get(url); return r.status_code, r.data.decode("utf-8", "replace")
now = OS.now()
setv("order.d1053", "1")
setv("order.d1053_msg_since", (now - dt.timedelta(days=6)).replace(microsecond=0).isoformat())
setv("order.d1053_late_hour", "0")
setv("order.d1053_summary_at", "00:00")
ns = OS.newest_sheet(con)
con.execute("UPDATE order_sheet SET taken_at=? WHERE id=?", ((now - dt.timedelta(minutes=50)).replace(microsecond=0).isoformat(), ns["id"]))
con.execute("DELETE FROM order_d1053_final"); con.commit()
# the made-up assets db: one scan tied to a recent order of the flow; its reading names one ordered line (more than ordered),
# one medicine on no order of that dealer
o = dict(con.execute("SELECT o.id, o.vendor, o.supplier_norm FROM purchase_order o WHERE o.order_src='s454' AND EXISTS (SELECT 1 FROM purchase_order_line l "
                     "WHERE l.order_id=o.id AND l.packs>0) ORDER BY o.id DESC LIMIT 1").fetchone())
ln = dict(con.execute("SELECT item, packs FROM purchase_order_line WHERE order_id=? AND packs>0 ORDER BY id LIMIT 1", (o["id"],)).fetchone())
a = sqlite3.connect(ADB)
a.execute("CREATE TABLE bills (id INTEGER PRIMARY KEY, stamp_no TEXT)")
a.execute("CREATE TABLE claude_reading (bill_id INTEGER PRIMARY KEY, at TEXT, model TEXT, ok INTEGER, doc_kind TEXT, data TEXT, error TEXT)")
a.execute("INSERT INTO bills VALUES (990001, 'B-W941')")
a.execute("INSERT INTO claude_reading VALUES (990001, ?, 'walk', 1, 'bill', ?, NULL)", (now.isoformat(), json.dumps(dict(items=[
    dict(name=ln["item"], qty=int(ln["packs"]) + 5), dict(name="ZZWALK UNORDERED TAB 941", qty=3)]))))
a.execute("INSERT INTO bills VALUES (990002, 'B-W942')")
a.execute("INSERT INTO claude_reading VALUES (990002, ?, 'walk', 1, 'bill', ?, NULL)", (now.isoformat(), json.dumps(dict(items=[]))))
a.commit(); a.close()
o2 = con.execute("SELECT id FROM purchase_order WHERE order_src='s454' AND id<>? AND id NOT IN (SELECT order_id FROM order_scan_tie) ORDER BY id DESC LIMIT 1", (o["id"],)).fetchone()
if o2:
    con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,1)",
                (o2[0], 990002, "B-W942", now.isoformat(), now.replace(microsecond=0).isoformat(), "scan")); con.commit()
con.execute("DELETE FROM order_scan_tie WHERE order_id=?", (o["id"],))
con.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,1)",
            (o["id"], 990001, "B-W941", now.isoformat(), now.replace(microsecond=0).isoformat(), "scan")); con.commit()
# a made-up late order: one of the flow's orders not arrived, moved 5 days back (due 3 days ago)
for (oid,) in con.execute("SELECT id FROM purchase_order WHERE order_src='s454' AND status='sent' ORDER BY id DESC").fetchall():
    s_ = __import__("order_track").light_all(con, now, oids=[oid])
    if s_ and not s_[0]["arrived"] and oid != o["id"]:
        con.execute("UPDATE purchase_order SET created_at=? WHERE id=?", ((now - dt.timedelta(days=5)).replace(microsecond=0).isoformat(), oid)); con.commit()
        print("INFO made order %d late" % oid)
        break
r = tick()
print("INFO tick: %s" % json.dumps((r or {}).get("d1053"), ensure_ascii=False)[:300])
ok(isinstance((r or {}).get("d1053"), dict) and "H" in r["d1053"], "the tick runs E-H")
# E
E = push("E")
late = [s for s in __import__("order_track").light_all(con, now, oids=M._flow_orders(con)) if s.get("late") and s.get("due_at") and s["due_at"].date() < now.date()]
print("INFO late orders past their due day: %d, E messages %d" % (len(late), len(E)))
ok(bool(late), "a late order past its due day exists on the walk")
if late:
    ok(any(p["user"] == "darpan" for p in E) and any(p["payload"]["url"] == "/finance/porders/s454/late" for p in E), "E to Darpan and the staff (the late page)")
# F1 (not final 50 min after the sheet) and the doctor after it
F1 = push("F1")
ok(len(F1) == 1 and F1[0]["user"] == "darpan" and "पक्की नहीं" in F1[0]["payload"]["body"], "F: Darpan nudged when the sheet is not final after 45 min")
con.execute("UPDATE order_d1053_msg SET sent_at=? WHERE kind='F1'", ((now - dt.timedelta(minutes=31)).replace(microsecond=0).isoformat(),)); con.commit()
tick()
ok(any(p["user"] == "manoj" for p in push("F1o")), "F: the doctor hears only after the nudge stays unanswered 30 min")
# G
G = push("G")
ok(any(p["user"] == "manoj" and p["payload"]["body"].startswith("Today:") for p in G) and any(p["user"] == "darpan" for p in G), "G: the summary to the doctor and Darpan")
n = len(push("G")); tick()
ok(len(push("G")) == n, "G once a day")
# H
H = push("H")
ok(any(p["user"] == "manoj" and "ZZWALK UNORDERED TAB 941" in p["payload"]["body"] for p in H), "H: the doctor told of the medicine not ordered (%s)" % (H[0]["payload"]["body"][:90] if H else "none"))
ok(any("%s" % ln["item"] in p["payload"]["body"] for p in H), "H: and of the one more than ordered")
ok(any(p["user"] == "darpan" and p["payload"]["url"] == "/finance/porders/d1053/bill/990001" for p in H), "H: Darpan's opens the bill's page")
code, html = page("manoj", "/finance/porders/d1053/bill/990001")
ok(code == 200 and "ZZWALK UNORDERED TAB 941" in html and "Send back" in html and "confirm(" not in html, "the bill page: the lines with Keep / Send back, no dialog")
rows = M.bill_lines(con, 990001)
ex = next(r for r in rows if r["kind"] == "extra"); mo = next(r for r in rows if r["kind"] == "more")
st, j = post("alisha", "/finance/porders/api/d1053/bill", dict(id=ex["id"], act="back"))
ok(st == 403, "reception cannot decide Keep / Send back (%s)" % st)
st, j = post("darpan", "/finance/porders/api/d1053/bill", dict(id=ex["id"], act="back"))
ok(st == 200, "Darpan sends the unordered medicine back (%s)" % st)
st, j = post("manoj", "/finance/porders/api/d1053/bill", dict(id=mo["id"], act="keep"))
ok(st == 200, "the doctor keeps the extra quantity (%s)" % st)
code, html = page("alisha", "/finance/porders/s454/order")
ok('id="d941back"' in html and "ZZWALK UNORDERED TAB 941" in html, "reception's screen: Wapas bhejna hai")
st, j = post("alisha", "/finance/porders/api/d1053/bill", dict(id=ex["id"], act="returned"))
ok(st == 200 and not M.returns_open(con), "her 'Wapas kar diya' closes it (%s)" % st)
if o2:
    ok(con.execute("SELECT n FROM order_d1053_billseen WHERE scan=990002").fetchone() is not None, "a good reading with no lines is judged once (never re-read)")
nH = len(push("H")); tick()
ok(len(push("H")) == nH, "a bill judged once")
# F2: final by Darpan, nothing sent 31 min after, a card still to order
src_row = dict(con.execute("SELECT * FROM order_sheet_line WHERE last_sheet=? ORDER BY id LIMIT 1", (ns["id"],)).fetchone()); src_row.pop("id")
src_row.update(item="WALKTEST TAB 941", item_printed="WALKTEST TAB 941", state="to_order", order_id=None, line_date=OS.today().isoformat(), reorder_day=None, entry_no="W941", resolved=0)
cols = [c[1] for c in con.execute("PRAGMA table_info(order_sheet_line)")]
src_row = {k: v for k, v in src_row.items() if k in cols}
con.execute("INSERT INTO order_sheet_line (%s) VALUES (%s)" % (",".join(src_row), ",".join("?" * len(src_row))), list(src_row.values()))
key = D.sheet_now(con)[0]
fat = (now - dt.timedelta(minutes=31)).replace(microsecond=0).isoformat()
con.execute("INSERT INTO order_d1053_final (sheet_key, day, at, by, counts) VALUES (?,?,?,?,?)", (key, now.date().isoformat(), fat, "darpan", "{}")); con.commit()
tick()
F2 = push("F2")
ok(any(p["user"] in ("alisha", "shivani") and "WhatsApp sab ko" in p["payload"]["body"] for p in F2), "F: reception nudged when the final list has not gone in 30 min")
# his step 1 = Marg's open order
WHO["u"] = "manoj"
h = cl.get("/finance/porders/flow").data.decode("utf-8", "replace")
oo = OS.open_order(con)
ok("%d suppliers · %d medicines" % (oo["suppliers"], oo["count"]) in h, "his step 1 counts Marg's open order (%d / %d), as reception's screen" % (oo["suppliers"], oo["count"]))
DONE[0] = True
print("RESULT: " + ("ALL PASS" if not FAIL else "%d FAIL" % len(FAIL)))
