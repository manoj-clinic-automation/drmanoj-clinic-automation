#!/usr/bin/env python3
"""walk_s940.py -- kit S940 walked on a COPY of finance.db (never the live one). argv: <code dir: S939 + S940> <copy.db> [control]
With order.d1053 = 1 on the copy and the pushes into a stub file (ORDER_PUSH_STUB, never a phone):
 * order_rules' tick pass (_s454_pass) makes and sends A when today's Marg sheet is in: Darpan in Devanagari to his tab, the staff in
   Roman Hindi to the order screen; the old sheet notice is not pushed but kept as replaced;
 * B after Darpan's final: the staff and the doctor; C once every order message after the final is answered: the doctor and Darpan;
 * D: an order of the flow that arrived after the messages began: Darpan; nothing twice on the next tick;
 * his Purchase orders page opens with the four steps; order.d1053 = 0: the tick makes nothing, his page as before.
CONTROL (S939 alone) goes red."""
import atexit, datetime as dt, json, os, shutil, sys
CODE, SRC = sys.argv[1], sys.argv[2]
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, CODE)
os.environ["NEEDS_YOU_WITHOUT_S408"] = "1"
STUB = SRC + ".stub940"
open(STUB, "w").close()
os.environ["ORDER_PUSH_STUB"] = STUB
DB = SRC + ".walk940"
shutil.copy(SRC, DB)
os.environ["FINANCE_DB"] = DB
FAIL = []
DONE = [False]
atexit.register(lambda: None if DONE[0] else print("RESULT: stopped on an error, %d FAIL" % (len(FAIL) + 1)))
def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAIL.append(what)
import sqlite3
from flask import Flask
import porders as PO
import darpan_kal as DK
WHO = {"u": "manoj"}
USERS = {"manoj": ["checker"], "alisha": ["maker"], "darpan": ["maker"]}
_CON = {}
def db_getter():
    if "c" not in _CON:
        _CON["c"] = sqlite3.connect(DB, timeout=5, check_same_thread=False)
        _CON["c"].row_factory = sqlite3.Row
    return _CON["c"]
def require_fn(*roles, unit=None):
    u = WHO["u"]
    return dict(user=u, login=u, roles=USERS[u]), None
app = Flask(__name__)
PO.init(app, db_getter, require_fn)
DK.init(app, db_getter, require_fn, "medical")
cl = app.test_client()
import order_sheet as OS, order_rules as OR
con = db_getter()
def setv(k, v):
    con.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v)); con.commit()
def pushes():
    return [json.loads(l) for l in open(STUB, encoding="utf-8") if l.strip()]
def post(who, url, body):
    WHO["u"] = who; r = cl.post(url, json=body); return r.status_code, (r.get_json(silent=True) or {})
def tickpass():
    with app.app_context():
        return OR._s454_pass(con)
setv("order.d1053", "1")
start = (dt.datetime.now() - dt.timedelta(days=3)).replace(microsecond=0).isoformat()
setv("order.d1053_msg_since", start)
ns = OS.newest_sheet(con)
con.execute("UPDATE order_sheet SET taken_at=? WHERE id=?", (OS.now_iso(), ns["id"]))
__import__("order_d1053").ensure(con); con.execute("DELETE FROM order_d1053_final"); con.commit()
OS._sheet_notice(con, ns["id"]) if hasattr(OS, "_sheet_notice") else None
r = tickpass()
print("INFO tick: %s" % json.dumps((r or {}).get("d1053"), ensure_ascii=False)[:300])
P = pushes()
ok(isinstance((r or {}).get("d1053"), dict), "order_rules' tick pass runs the messages")
a_d = [p for p in P if p["user"] == "darpan" and p["payload"]["tag"] == "d1053-A"]
a_s = [p for p in P if p["user"] in ("alisha", "shivani") and p["payload"]["tag"] == "d1053-A"]
ok(len(a_d) == 1 and "ऑर्डर सूची" in a_d[0]["payload"]["body"] and a_d[0]["payload"]["url"].endswith("#order"), "A to Darpan, Devanagari, opens his tab")
ok(len(a_s) >= 1 and "Darpan" in a_s[0]["payload"]["body"] and a_s[0]["payload"]["url"] == "/finance/porders/s454/order", "A to the staff, Roman Hindi, opens the order screen")
ok(not any(p["payload"].get("tag") == "porders" for p in P), "the old sheet notice is not pushed")
nt = json.loads(con.execute("SELECT notice FROM order_sheet WHERE id=?", (ns["id"],)).fetchone()[0] or "{}")
ok(nt.get("replaced") == "d1053", "the old notice is kept as replaced by the flow (%s)" % nt.get("replaced"))
n0 = len(P)
tickpass()
ok(len(pushes()) == n0 or all(p["payload"]["tag"] == "d1053-D" for p in pushes()[n0:]), "nothing sent twice on the next tick")
# B: Darpan answers everything and makes it final
WHO["u"] = "darpan"
j = cl.get("/finance/darpan/kal/api/order").get_json()
for o in j["d1053"]["old"]:
    post("darpan", "/finance/darpan/kal/api/order/d1053", dict(do="decide", kind=o["kind"], ref=o["ref"], act="later"))
for o in j["d1053"]["raised"]:
    post("darpan", "/finance/darpan/kal/api/order/d1053", dict(do="decide", qid=o["id"], act="keep"))
st, j = post("darpan", "/finance/darpan/kal/api/order/d1053", dict(do="final"))
ok(st == 200, "Darpan makes it final (%s)" % st)
n1 = len(pushes())
tickpass()
B = [p for p in pushes()[n1:] if p["payload"]["tag"] == "d1053-B"]
ok(any(p["user"] == "manoj" and "final" in p["payload"]["body"] and p["payload"]["url"] == "/finance/porders/flow" for p in B), "B to the doctor, opens his page")
ok(any(p["user"] in ("alisha", "shivani") and "WhatsApp bhejiye" in p["payload"]["body"] for p in B), "B to the staff: WhatsApp bhejiye")
# C: a made-up batch after the final, every message answered
fr = con.execute("SELECT at FROM order_d1053_final").fetchone()[0]
later = (dt.datetime.fromisoformat(fr) + dt.timedelta(minutes=1)).isoformat()
o = dict(con.execute("SELECT * FROM purchase_order WHERE order_src='s454' ORDER BY id DESC LIMIT 1").fetchone())
cols = [c[1] for c in con.execute("PRAGMA table_info(purchase_order)")]
o.pop("id"); o.update(created_at=later, order_via="whatsapp", status="sent")
cur = con.execute("INSERT INTO purchase_order (%s) VALUES (%s)" % (",".join(o), ",".join("?" * len(o))), list(o.values()))
oid = cur.lastrowid
con.execute("INSERT INTO supplier_msg (month, vendor_norm, vendor, kind, ref, channel, body, status, queued_at, sent_at, attempts) VALUES (?,?,?,?,?,?,?,?,?,?,1)",
            (later[:7], o.get("supplier_norm") or "W", o["vendor"], "order", str(oid), "whatsapp", "walk", "queued", later, None))
con.commit()
n2 = len(pushes()); tickpass()
ok(not [p for p in pushes()[n2:] if p["payload"]["tag"] == "d1053-C"], "C waits while a message is still with the phone")
con.execute("UPDATE supplier_msg SET status='sent', sent_at=? WHERE ref=? AND kind='order'", (later, str(oid))); con.commit()
n3 = len(pushes()); tickpass()
C = [p for p in pushes()[n3:] if p["payload"]["tag"] == "d1053-C"]
ok(any(p["user"] == "manoj" and "WhatsApp 1" in p["payload"]["body"] for p in C) and any(p["user"] == "darpan" for p in C), "C to the doctor and Darpan once all went (%s)" % [p["payload"]["body"] for p in C][:1])
# D: an arrival of the flow since the messages began
D = [p for p in pushes() if p["payload"]["tag"] == "d1053-D"]
print("INFO D messages so far: %d" % len(D))
nd = con.execute("SELECT COUNT(*) FROM order_d1053_msg WHERE kind='D'").fetchone()[0]
if D:
    ok(all(p["user"] == "darpan" and "माल आया" in p["payload"]["body"] for p in D), "D to Darpan: <dealer> का माल आया")
n4 = len(pushes()); tickpass()
ok(con.execute("SELECT COUNT(*) FROM order_d1053_msg WHERE kind='D'").fetchone()[0] == nd, "no arrival announced twice")
# his page
WHO["u"] = "manoj"
r = cl.get("/finance/porders/flow"); h = r.data.decode("utf-8", "replace")
ok(r.status_code == 200 and 'id="d1053steps"' in h and "Today's order" in h, "his page opens with the four steps (%s)" % r.status_code)
ok("Final ·" in h and "Sent ·" in h, "the steps show the final and what went")
# off
setv("order.d1053", "0")
r = tickpass()
ok((r or {}).get("d1053") == {"off": True}, "switched off: the tick makes nothing")
h = cl.get("/finance/porders/flow").data.decode("utf-8", "replace")
ok('id="d1053steps"' not in h, "switched off: his page as before")
os.remove(DB); os.remove(STUB)
DONE[0] = True
print("RESULT: " + ("ALL PASS" if not FAIL else "%d FAIL" % len(FAIL)))
