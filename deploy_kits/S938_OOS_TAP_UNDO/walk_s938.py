#!/usr/bin/env python3
"""walk_s938.py -- kit S938 walked on a COPY of finance.db (never the live one). argv: <code dir with the kit's files> <copy.db> [control]
Through the real porders blueprint (porders_s454, order_s778 and order_flow mounted by their own init) in a Flask test app:
 * a real 'Out of stock' tap on a red-box line of the copy (order_s778.na) and its Undo by reception through the new door: the line is back
   in the red box, the tap row gone, the whole row kept in purchase_audit; the screen listed the tap with Undo before, not after;
 * a made-up tap on a carry and on a Marg sheet line: the dropped carry and the sheet hold given back;
 * reception cannot undo yesterday's tap, the doctor can; a tap the doctor answered (keep) or put a word on (wait) is refused for both;
 * his page: an unanswered tap's row carries 'Tapped by mistake -- put back' and do=undo_tap puts it back.
CONTROL (the FROM files) goes red."""
import datetime as dt
import os
import shutil
import sys

CODE, SRC = sys.argv[1], sys.argv[2]
CONTROL = len(sys.argv) > 3 and sys.argv[3] == "control"
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, CODE)
os.environ["NEEDS_YOU_WITHOUT_S408"] = "1"
DB = SRC + ".walk938"
shutil.copy(SRC, DB)
FAIL = []


def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAIL.append(what)


import sqlite3                                                    # noqa: E402
from flask import Flask                                           # noqa: E402
import porders as P                                               # noqa: E402

WHO = {"u": "manoj"}
USERS = {"manoj": ["checker"], "alisha": ["maker"]}   # alisha: a porders sender (the shared reception login asks a name first)
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
P.init(app, db_getter, require_fn)
cl = app.test_client()
import order_s778 as S7                                           # noqa: E402
import order_sheet as OS                                          # noqa: E402
con = db_getter()
S7.ensure(con)
TODAY = OS.today().isoformat()
print("INFO today on the walk's clock: %s" % TODAY)


def post(who, url, body):
    WHO["u"] = who
    r = cl.post(url, json=body)
    return r.status_code, (r.get_json(silent=True) or {})


def page(who, url):
    WHO["u"] = who
    r = cl.get(url)
    return r.status_code, r.data.decode("utf-8", "replace")


def na_row(i):
    return con.execute("SELECT * FROM order_s778_na WHERE id=?", (int(i),)).fetchone()


# 1 -- a real red-box line of the copy, tapped and taken back
lines = [c for c in S7.red_lines(con, True) if c["kind"] in ("carry", "late", "old") and not c.get("on_card")]
print("INFO red-box lines on the copy: %d" % len(lines))
if lines:
    c = lines[0]
    st, j = post("alisha", "/finance/porders/api/s778/na", dict(kind=c["kind"], ref=c["ref"]))
    nid = int(j.get("id") or 0)
    ok(st == 200 and nid, "a real red-box line tapped Out of stock on the copy (%s, %s)" % (st, c["item"]))
    code, html = page("alisha", "/finance/porders/s454/order")
    ok(code == 200 and 'id="s938taps"' in html and ('data-na="%d"' % nid) in html, "reception's screen lists today's tap with Undo (%s)" % code)
    ok("na_undo" in html, "the Undo button calls the new door")
    st, j = post("alisha", "/finance/porders/api/s778/na_undo", dict(id=nid))
    ok(st == 200 and j.get("ok") and j.get("item") == c["item"], "reception's Undo is taken (%s %s)" % (st, j.get("error") or ""))
    ok(na_row(nid) is None, "the tap row is gone")
    au = con.execute("SELECT 1 FROM purchase_audit WHERE action='s778_na_undo' AND ref=?", (str(nid),)).fetchone()
    ok(au is not None, "the whole tap is kept in purchase_audit (s778_na_undo)")
    back = [x for x in S7.red_lines(con, True) if x["kind"] == c["kind"] and x["ref"] == c["ref"]]
    ok(len(back) == 1, "the line is back in the red box")
    code, html = page("alisha", "/finance/porders/s454/order")
    ok(code == 200 and ('data-na="%d"' % nid) not in html, "the screen no longer lists it under today's taps")
else:                                                             # the live box may be empty because every line was tapped: take one back
    ts = [dict(r) for r in con.execute("SELECT id, item FROM order_s778_na WHERE status='asked' AND cleared_at IS NULL AND substr(at,1,10)=? ORDER BY id", (TODAY,))]
    print("INFO no red-box line on the copy; today's taps waiting: %d" % len(ts))
    if ts:
        t0 = ts[0]
        code, html = page("alisha", "/finance/porders/s454/order")
        ok(code == 200 and ('data-na="%d"' % t0["id"]) in html, "reception's screen lists today's tap with Undo (%s)" % code)
        st, j = post("alisha", "/finance/porders/api/s778/na_undo", dict(id=t0["id"]))
        ok(st == 200 and na_row(t0["id"]) is None, "reception's Undo of a real tap is taken (%s %s)" % (st, j.get("error") or ""))
        back = [x for x in S7.red_lines(con, True) if S7.norm(x["item"]) == S7.norm(t0["item"])]
        ok(len(back) >= 1, "the line is back in the red box (%s)" % t0["item"])

# 2 -- made-up taps: a carry, a Marg sheet line, yesterday's, answered, with his word
now = OS.now_iso()
yday = (OS.today() - dt.timedelta(days=1)).isoformat() + "T12:00:00"


def tap(item, kind, ref, at=None, by="alisha", status="asked"):
    cur = con.execute("INSERT INTO order_s778_na (item_norm, item, supplier_norm, vendor, kind, ref, qty, by, at, last_bought, max_line, status) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,0,?)", (S7.norm(item), item, "WALKTEST DEALER", "WALKTEST DEALER", kind, str(ref), "1", by, at or now, "", status))
    con.commit()
    return cur.lastrowid


try:
    from order_track import _ensure_carry                         # noqa: PLC0415
    _ensure_carry(con)
except Exception:                                                 # noqa: BLE001
    pass
cols = [r[1] for r in con.execute("PRAGMA table_info(order_carry)")]
cid = None
if cols:
    vals = {k: None for k in cols if k != "id"}
    for k in cols:
        if k in ("supplier_norm", "vendor"):
            vals[k] = "WALKTEST DEALER"
        elif k == "item":
            vals[k] = "WALKTEST CARRY TAB"
        elif k in ("qty", "pack_size", "from_order_id", "from_line_id"):
            vals[k] = 1 if k != "from_line_id" else 999999001
        elif k in ("at", "from_at"):
            vals[k] = now
        elif k == "dropped_at":
            vals[k] = now
        elif k == "dropped_by":
            vals[k] = "s778_na"
    for r in con.execute("PRAGMA table_info(order_carry)"):          # any other NOT NULL column without a default: a made-up value
        if r[1] != "id" and r[3] and r[4] is None and vals.get(r[1]) is None:
            vals[r[1]] = 1 if "INT" in str(r[2]).upper() else ("marg_short" if r[1] == "reason" else "walk938")
    try:
        cur = con.execute("INSERT INTO order_carry (%s) VALUES (%s)" % (",".join(vals), ",".join("?" * len(vals))), list(vals.values()))
        cid = cur.lastrowid
        con.commit()
    except sqlite3.Error as e:
        print("INFO a made-up carry could not be written: %s" % e)
if cid:
    n1 = tap("WALKTEST CARRY TAB", "carry", cid)
    st, j = post("alisha", "/finance/porders/api/s778/na_undo", dict(id=n1))
    d = con.execute("SELECT dropped_at, dropped_by FROM order_carry WHERE id=?", (cid,)).fetchone()
    ok(st == 200 and d[0] is None and d[1] is None, "a carry the tap dropped is open again (%s)" % st)
else:
    ok(False, "the made-up carry was written")

S7._hold_sheet(con, "alisha", "sheet", "999999002", "WALKTEST SHEET TAB")
n2 = tap("WALKTEST SHEET TAB", "sheet", "999999002")
st, j = post("alisha", "/finance/porders/api/s778/na_undo", dict(id=n2))
h = con.execute("SELECT 1 FROM s454_line_edit WHERE src='sheet' AND ref='999999002' AND reason='s778_na'").fetchone()
ok(st == 200 and h is None, "the Marg sheet line's hold is taken off (%s)" % st)

n3 = tap("WALKTEST OLD TAP", "late", "1:1", at=yday)
st, j = post("alisha", "/finance/porders/api/s778/na_undo", dict(id=n3))
ok(st == 409 and j.get("error") == "old_tap" and na_row(n3) is not None, "reception cannot take back yesterday's tap (%s %s)" % (st, j.get("error")))
st, j = post("manoj", "/finance/porders/api/s778/na_undo", dict(id=n3))
ok(st == 200 and na_row(n3) is None, "the doctor can (%s)" % st)

n4 = tap("WALKTEST KEPT", "late", "1:2", status="keep")
st, j = post("manoj", "/finance/porders/api/s778/na_undo", dict(id=n4))
ok(st == 409 and na_row(n4) is not None, "a tap the doctor answered is refused, even to him (%s)" % st)

n5 = tap("WALKTEST WAITING", "late", "1:3")
import order_flow as OF                                           # noqa: E402
OF.ensure(con)
con.execute("INSERT INTO order_flow_mark (kind, na_id, item, until, by, at) VALUES ('wait', ?, 'WALKTEST WAITING', ?, 'manoj', ?)", (n5, TODAY, now))
con.commit()
st, j = post("alisha", "/finance/porders/api/s778/na_undo", dict(id=n5))
ok(st == 409 and na_row(n5) is not None, "a tap with his word on it (wait) is refused (%s)" % st)

# 3 -- his page: the row's button and do=undo_tap
n6 = tap("WALKTEST HIS ROW", "late", "1:4")
s = dict(item="WALKTEST HIS ROW", sn="WALKTEST DEALER", state="oos", na=dict(na_row(n6)), vendor="WALKTEST DEALER", other=None, suggest=None, word=None)
try:
    btns = OF._sh_buttons(s)
except Exception as e:                                            # noqa: BLE001
    btns = "ERROR %r" % (e,)
ok("undo_tap" in btns and "Tapped by mistake" in btns, "his row of an unanswered tap carries 'Tapped by mistake -- put back'")
st, j = post("manoj", "/finance/porders/api/flow/act", dict(do="undo_tap", na=n6, item="WALKTEST HIS ROW", sn="WALKTEST DEALER"))
ok(st == 200 and na_row(n6) is None, "do=undo_tap from his page puts it back (%s %s)" % (st, j.get("error") or ""))
code, html = page("manoj", "/finance/porders/flow")
ok(code == 200, "his flow page renders on the copy (%s)" % code)
code, html = page("manoj", "/finance/porders/s454/order")
ok(code == 200, "the order screen renders for him on the copy (%s)" % code)
ok("finance_app" not in sys.modules, "the walk never loaded the whole app (no path to the live database)")
_CON.get("c") and _CON["c"].close()
os.remove(DB)
print("RESULT:", "ALL PASS" if not FAIL else "%d FAIL" % len(FAIL))
sys.exit(1 if FAIL else 0)
