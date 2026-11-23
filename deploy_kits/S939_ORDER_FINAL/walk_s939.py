#!/usr/bin/env python3
"""walk_s939.py -- kit S939 walked on a COPY of finance.db (never the live one). argv: <code dir> <copy.db> [control]
Through the real porders and darpan_kal blueprints in a Flask test app, with order.d1053 = 1 on the copy:
 * Darpan's tab is the one list (no proposals) and carries the questions; a made-up Marg purchase of an asked line takes it out (F-1623),
   a purchase on the carry's own bill does not;
 * WhatsApp all, its confirm screen and its door are locked until the final; reception's page shows the waiting line and no red box;
 * reception raises a card line; her remove and her strip's Out of stock are refused; Darpan answers; final refused while anything waits;
 * each answer does what it says (later / add / na / keep); the final opens the door; the sent record replaces the day's done list;
 * order.d1053 = 0: every screen and door as before.
CONTROL (the FROM files) goes red."""
import os, shutil, sys
CODE, SRC = sys.argv[1], sys.argv[2]
CONTROL = len(sys.argv) > 3 and sys.argv[3] == "control"
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, CODE)
os.environ["NEEDS_YOU_WITHOUT_S408"] = "1"
os.environ["ORDER_PUSH_NONE"] = "1"
DB = SRC + ".walk939"
shutil.copy(SRC, DB)
FAIL = []
import atexit
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
USERS = {"manoj": ["checker"], "alisha": ["maker"], "darpan": ["maker"], "reception": ["maker"]}
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
import order_s778 as S7, order_sheet as OS
con = db_getter()
S7.ensure(con)
def setv(k, v):
    con.execute("INSERT INTO setting (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v)); con.commit()
def post(who, url, body):
    WHO["u"] = who; r = cl.post(url, json=body); return r.status_code, (r.get_json(silent=True) or {})
def get(who, url):
    WHO["u"] = who; r = cl.get(url); return r.status_code, r.data.decode("utf-8", "replace")
def tab(who="darpan"):
    WHO["u"] = who; r = cl.get("/finance/darpan/kal/api/order"); return r.status_code, (r.get_json(silent=True) or {})
setv("order.d1053", "1")
print("INFO source %s, newest sheet %s" % (OS.source(con), (OS.newest_sheet(con) or {}).get("id")))
st, j = tab()
d = j.get("d1053") or {}
ok(st == 200 and bool(d), "Darpan's tab carries the one list on marg_sheet (%s)" % st)
ok(j.get("suppliers") == [], "no engine proposals beside it (F-1624)")
cards = OS.entries(con)
ok(len(d.get("cards") or []) == len(cards), "the tab's cards are reception's cards (%d / %d)" % (len(d.get("cards") or []), len(cards)))
print("INFO questions: old %d, raised %d, came %s, transit %s, cards %d" % (len(d.get("old") or []), len(d.get("raised") or []), d.get("came_n"), d.get("transit_n"), len(cards)))
# F-1623: a made-up Marg purchase of an asked line takes it out
old = d.get("old") or []
EFF = (con.execute("SELECT md5 FROM purchase_export WHERE superseded_by IS NULL ORDER BY rowid DESC LIMIT 1").fetchone() or ["walk939"])[0]
MAXL = con.execute("SELECT COALESCE(MAX(id),0) FROM purchase_line").fetchone()[0]
if old:
    c = next(x for x in S7.red_lines(con) if x["kind"] == old[0]["kind"] and x["ref"] == old[0]["ref"])
    own = None
    if c["kind"] in ("carry", "late") and c.get("from_order"):
        r = con.execute("SELECT billed_bill_no FROM purchase_order_line WHERE order_id=? AND billed_bill_no IS NOT NULL LIMIT 1", (int(c["from_order"]),)).fetchone()
        own = r[0] if r else None
    if own:
        con.execute("INSERT INTO purchase_line (supplier_norm, item, bill_no, bill_date, direction, source_md5, qty) VALUES (?,?,?,?, 'PURCHASE', ?, 1)", (c["sn"], c["item"], own, c["day"], EFF))
        con.commit()
        st, j = tab()
        ok(any(x["ref"] == c["ref"] for x in j["d1053"]["old"]), "a purchase on the carry's own bill does NOT clear it")
    cols = [r[1] for r in con.execute("PRAGMA table_info(purchase_line)")]
    con.execute("INSERT INTO purchase_line (supplier_norm, item, bill_no, bill_date, direction, source_md5, qty) VALUES (?,?,?,?, 'PURCHASE', ?, 1)", (c["sn"], c["item"], "WALK939", OS.today().isoformat(), EFF))
    st, j = tab()
    ok(not any(x["kind"] == c["kind"] and x["ref"] == c["ref"] for x in j["d1053"]["old"]), "a Marg purchase of %s from its dealer takes it out (F-1623)" % c["item"])
    ok(int(j["d1053"]["came_n"] or 0) >= 1, "and the tab counts it as come (%s)" % j["d1053"]["came_n"])
    con.execute("DELETE FROM purchase_line WHERE id>?", (MAXL,)); con.commit()
    st, j = tab()
    ok(any(x["kind"] == c["kind"] and x["ref"] == c["ref"] for x in j["d1053"]["old"]), "without it the line is asked again")
# the lock
con.execute("DELETE FROM order_d1053_final"); con.commit()
st, j = post("alisha", "/finance/porders/api/s454/whatsapp", dict(sns=[]))
ok(st == 409 and j.get("error") == "not_final", "WhatsApp all's door is locked before the final (%s %s)" % (st, j.get("error")))
code, html = get("alisha", "/finance/porders/s454/order")
ok(code == 200 and 'id="d1053wait"' in html, "reception's screen says it waits for Darpan (%s)" % code)
ok('class="s778box"' not in html, "the red box with its buttons is gone for reception")
ok('href="/finance/porders/s454/order/whatsapp"' not in html, "no live WhatsApp-all link while locked")
ok('id="donehead"' not in html, "the day's done list is replaced by the sent record")
code, html = get("alisha", "/finance/porders/s454/order/whatsapp")
ok(code == 200 and 'id="d1053wait"' in html and 'id="wayes"' not in html, "the confirm screen is locked too")
# a made-up line on Marg's newest sheet, to be ordered today (the copy's sheet is all ordered)
ns = OS.newest_sheet(con)
src_row = dict(con.execute("SELECT * FROM order_sheet_line WHERE last_sheet=? ORDER BY id LIMIT 1", (ns["id"],)).fetchone())
src_row.pop("id")
src_row.update(item="WALKTEST TAB 939", item_printed="WALKTEST TAB 939", state="to_order", order_id=None, line_date=OS.today().isoformat(), reorder_day=None,
               entry_no="W939", resolved=0)
src_row = {k: v for k, v in src_row.items() if k in [r[1] for r in con.execute("PRAGMA table_info(order_sheet_line)")]}
con.execute("INSERT INTO order_sheet_line (%s) VALUES (%s)" % (",".join(src_row), ",".join("?" * len(src_row))), list(src_row.values())); con.commit()
# reception raises a card line; her remove and her strip's Out of stock are refused
pend = [e for e in OS.entries(con) if e.get("state") == "pending" and not e.get("draft") and any(l["src"] != "draft" for l in e["lines"])]
print("INFO pending cards: %d" % len(pend))
qid = None
if pend:
    e = pend[0]; l = next(x for x in e["lines"] if x["src"] != "draft")
    st, j = post("alisha", "/finance/porders/api/d1053/raise", dict(sn=e["sn"], src=l["src"], ref=str(l["ref"]), item=l["item"]))
    qid = j.get("id")
    ok(st == 200 and qid, "reception raises %s to Darpan (%s)" % (l["item"], st))
    code, html = get("alisha", "/finance/porders/s454/order/" + __import__("urllib.parse").parse.quote(e["sn"], safe=""))
    ok(code == 200 and "Darpan ko bheja" in html, "her supplier screen shows it went to Darpan")
    st, j = post("alisha", "/finance/porders/api/s454/qty", dict(src=l["src"], ref=str(l["ref"]), item=l["item"], remove=1, reason="dealer_no"))
    ok(st == 409 and j.get("error") == "raise_only", "her remove is refused: she raises (%s)" % st)
    st, j = tab()
    ok(any(r["id"] == qid for r in j["d1053"]["raised"]), "Darpan's tab has her raise")
st, j = post("darpan", "/finance/darpan/kal/api/order/d1053", dict(do="final"))
ok((st == 409 and j.get("error") == "pending") or not (j.get("d1053") or d).get("old"), "the final is refused while questions wait (%s %s)" % (st, j.get("error")))
oid = con.execute("SELECT id FROM purchase_order WHERE order_src='s454' ORDER BY id DESC LIMIT 1").fetchone()
if oid:
    st, j = post("alisha", "/finance/porders/api/flow/rec", dict(do="oos", oid=oid[0], lid=1))
    ok(st == 409 and j.get("error") == "raise_only", "her strip's Out of stock is refused (%s)" % st)
    st, j = post("alisha", "/finance/porders/api/flow/rec", dict(do="raise", oid=oid[0]))
    ok(st == 200 and j.get("ok"), "her strip's raise is taken (%s %s)" % (st, j.get("error")))
    st, j = post("alisha", "/finance/porders/api/s778/na", dict(kind="carry", ref="1"))
    ok(st == 409 and j.get("error") == "raise_only", "her Out of stock door is refused (%s)" % st)
    st, j = post("alisha", "/finance/porders/api/s454/reorder", dict(line=1))
    ok(st == 409 and j.get("error") == "raise_only", "her Dobara door is refused (%s)" % st)
# a late order raised from her strip before it is in the red lines: its open lines are Darpan's questions
lo = None
for (o_id,) in con.execute("SELECT id FROM purchase_order WHERE order_src='s454' AND status='sent' ORDER BY id DESC LIMIT 30").fetchall():
    s_ = __import__("order_track").light_all(con, OS.now(), oids=[o_id])
    if s_ and any(x["state"] in ("open", "part", "short") for x in s_[0]["lines"]) and not any(c.get("from_order") == o_id for c in S7.red_lines(con)):
        lo = o_id
        break
print("INFO an order with open lines outside the red lines: %s" % lo)
if lo:
    st, j = post("alisha", "/finance/porders/api/flow/rec", dict(do="raise", oid=lo))
    st, j = tab()
    ol = [x for x in j["d1053"]["old"] if x["kind"] == "oline" and x["ref"].startswith("%d:" % lo)]
    ok(len(ol) >= 1 and ol[0]["said"], "her raise of order %d is Darpan's question with her name (%d lines)" % (lo, len(ol)))
    if ol:
        st, r = post("darpan", "/finance/darpan/kal/api/order/d1053", dict(do="decide", kind="oline", ref=ol[0]["ref"], act="later"))
        ok(st == 200 and not any(x["ref"] == ol[0]["ref"] for x in r["d1053"]["old"]), "Darpan's 'not now' on it is taken (%s)" % st)
# Darpan answers
st, j = tab(); D = j["d1053"]
acts = {}
for i, o in enumerate(D["old"]):
    act = ("na", "add", "later")[i % 3] if i < 3 else "later"
    st, r = post("darpan", "/finance/darpan/kal/api/order/d1053", dict(do="decide", kind=o["kind"], ref=o["ref"], act=act))
    acts[act] = acts.get(act, 0) + (1 if st == 200 else 0)
    if st == 200:
        ok(not any(x["kind"] == o["kind"] and x["ref"] == o["ref"] for x in (r.get("d1053") or {}).get("old", [])), "the answer's own tab no longer asks %s (%s)" % (o["item"], act))
    if st != 200:
        print("INFO decide %s %s -> %s %s" % (o["item"], act, st, r.get("error") or r.get("message")))
    if i < 3:
        if act == "na":
            ok(con.execute("SELECT 1 FROM order_s778_na WHERE item=? AND cleared_at IS NULL", (o["item"],)).fetchone() is not None, "out of stock → the doctor: the tap row is written (%s)" % o["item"])
        if act == "add":
            on = any(OS._pa().norm(x["item"]) == OS._pa().norm(o["item"]) for e2 in OS.entries(con) for x in e2["lines"])
            ok(on, "add: %s is on today's cards" % o["item"])
for r in D["raised"]:
    st, x = post("darpan", "/finance/darpan/kal/api/order/d1053", dict(do="decide", qid=r["id"], act="keep"))
    ok(st == 200, "Darpan keeps reception's raised line (%s)" % st)
print("INFO answers: %s" % acts)
st, j = tab()
left = j["d1053"]["old"] + j["d1053"]["raised"]
for o in left:
    post("darpan", "/finance/darpan/kal/api/order/d1053", dict(do="decide", kind=o.get("kind"), ref=o.get("ref"), act="later") if "kind" in o else dict(do="decide", qid=o["id"], act="keep"))
st, j = post("darpan", "/finance/darpan/kal/api/order/d1053", dict(do="final"))
ok(st == 200 and (j.get("d1053") or {}).get("final"), "सूची पक्की करो once every question is answered (%s %s)" % (st, j.get("error") or j.get("message")))
st, j = post("alisha", "/finance/porders/api/s454/whatsapp", dict(sns=[]))
ok(j.get("error") != "not_final", "after the final the door is open (%s %s)" % (st, j.get("error")))
code, html = get("alisha", "/finance/porders/s454/order")
ok('id="d1053final"' in html, "reception's screen says Darpan made it final")
sr = __import__("order_d1053").sent_record(con)
print("INFO sent record rows: %d" % len(sr))
if sr:
    ok('id="d1053senthead"' in html, "the sent record is on reception's screen")
    code, html2 = get("reception", "/finance/porders/s454/order")
    ok(code == 200 and 'id="d1053senthead"' in html2 and 'id="donehead"' not in html2, "the shared reception login gets the sent record too (%s, who-script %s)" % (code, "WHO_SHARED" in html2))
    wa = [x for x in sr if x["via"].startswith("whatsapp")]
    sentm = [x for x in wa if con.execute("SELECT 1 FROM supplier_msg WHERE kind='order' AND ref=? AND status='sent'", (x["id"],)).fetchone()]
    if sentm:
        ok(sentm[0]["word_hi"].startswith("✓ WhatsApp gaya"), "a WhatsApp the phone reported reads 'WhatsApp gaya hh:mm' (%s)" % sentm[0]["word_hi"])
# the switch off
setv("order.d1053", "0")
st, j = tab()
ok("d1053" not in j, "switched off: the tab as before")
con.execute("DELETE FROM order_d1053_final"); con.commit()
st, j = post("alisha", "/finance/porders/api/s454/whatsapp", dict(sns=[]))
ok(j.get("error") != "not_final", "switched off: the door as before (%s)" % j.get("error"))
os.remove(DB)
DONE[0] = True
print("RESULT: " + ("ALL PASS" if not FAIL else "%d FAIL" % len(FAIL)))
