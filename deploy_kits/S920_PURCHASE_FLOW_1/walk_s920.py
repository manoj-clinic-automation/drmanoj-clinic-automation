#!/usr/bin/env python3
"""walk_s920.py -- kit S920 walked on a COPY of finance.db (never the live one). argv: <code dir with the patched porders.py> <copy.db> [control]
Checks: the groups on the copy; every button on a copy; the owner page / Shavez / reception doors; a CONTROL that must go red."""
import datetime as dt
import os
import shutil
import sqlite3
import sys

CODE, SRC = sys.argv[1], sys.argv[2]
CONTROL = len(sys.argv) > 3 and sys.argv[3] == "control"
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, CODE)
os.environ["PORDERS_SOURCE"] = "tables"
DB = SRC + ".walk920"
shutil.copy(SRC, DB)
FAIL = []


def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAIL.append(what)


import order_flow as F                                            # noqa: E402

if CONTROL:                                                       # the control: the S499 fix taken out -- an old line takes a new tap
    _orig = F._settle

    def _bad(con, s, x, carry, na, mk_line, ordered_since):
        return _orig(con, s, x, carry, na, mk_line, lambda *a: None)
    F._settle = _bad

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
NOW = dt.datetime(2026, 11, 21, 19, 30)
# a made-up late order (nothing real): a dealer and a medicine that do not exist
cols = {r[1] for r in con.execute("PRAGMA table_info(purchase_order)")}
o = dict(vendor="WALK920 MADE-UP DEALER", supplier_norm="WALK920", status="sent", created_at="2026-11-16T10:00:00", created_by="walk")
o = {k: v for k, v in o.items() if k in cols}
cur = con.execute("INSERT INTO purchase_order (%s) VALUES (%s)" % (", ".join(o), ",".join("?" * len(o))), list(o.values()))
WOID = cur.lastrowid
lc = {r[1] for r in con.execute("PRAGMA table_info(purchase_order_line)")}
def _line(oid, item, packs):
    l = {k: v for k, v in dict(order_id=oid, item=item, packs=packs, pack_size=10).items() if k in lc}
    con.execute("INSERT INTO purchase_order_line (%s) VALUES (%s)" % (", ".join(l), ",".join("?" * len(l))), list(l.values()))
_line(WOID, "WALK920 MADE-UP TAB", 5)
_line(WOID, "WALK920 MADE-UP GEL", 3)                            # re-ordered on the next order, then tapped out of stock there
o2 = dict(o, created_at="2026-11-19T10:00:00")
cur = con.execute("INSERT INTO purchase_order (%s) VALUES (%s)" % (", ".join(o2), ",".join("?" * len(o2))), list(o2.values()))
WOID2 = cur.lastrowid
_line(WOID2, "WALK920 MADE-UP GEL", 3)
F._s7().ensure(con)
con.execute("INSERT INTO order_s778_na (item_norm, item, supplier_norm, vendor, kind, ref, qty, by, at, max_line) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (F._norm("WALK920 MADE-UP GEL"), "WALK920 MADE-UP GEL", "WALK920", "WALK920 MADE-UP DEALER", "late", "x", "3", "walk", "2026-11-20T11:00:00", 0))
con.commit()
G = F.groups(con, NOW, with_bills=False)
c = G["counts"]
print("counts", c)
gel = [r["id"] for g in F.GROUPS for r in G[g] for x in r["lines"] if x["item"] == "WALK920 MADE-UP GEL" and x["state"] == "oos"]
ok(gel == [WOID2], "an out-of-stock tap answers only the newest order of the medicine (got orders %s)" % gel)
ok(c["gap"] <= 12, "gap stays small: superseded lines settle (got %d)" % c["gap"])
ok(c["team"] == len([1 for r in con.execute("SELECT 1 FROM order_s778_na WHERE status='asked' AND cleared_at IS NULL")]), "team = the open 'Ab nahi milta' rows")
ok(any(r["id"] == WOID for r in G["late"]), "the made-up order of 16-Nov is in Late")
ok(not any(r["vendor"].startswith("YUVIKA") and r["day"] == "2026-11-13" for r in G["late"]), "Yuvika 13-Nov: its two re-ordered lines settle it out of Late")
ids = [r["id"] for g in F.GROUPS for r in G[g] if r.get("id")]
ok(len(ids) == len(set(ids)), "each order in exactly one group")
ok(sum(c[g] for g in F.GROUPS) == len(ids), "the groups add up to the orders read")
for r in G["arr"] + G["gap"]:
    for l in r["missing"]:
        ok(l["state"] in ("short", "part", "oos", "sub", "open"), "missing named: %s" % l["item"][:20])
        break
if CONTROL:
    print("CONTROL RESULT:", "RED (as it must)" if FAIL else "GREEN -- THE CONTROL DID NOT BITE")
    sys.exit(0 if FAIL else 1)

# ---- the buttons, on the copy
def first(g, st):
    for r in G[g]:
        for l in r["lines"]:
            if l["state"] in st and r.get("id") and l.get("id"):
                return r, l
    return None, None

r, l = first("arr", ("short",))
res, st = F.act(con, "walk", dict(do="oos", oid=r["id"], lid=l["id"]))
ok(st == 200 and res.get("ok"), "Out of stock on %s -> %s" % (l["item"][:20], res))
G2 = F.groups(con, NOW, with_bills=False)
ok(G2["counts"]["team"] == c["team"] + (0 if res.get("already") else 1), "the team list grew by one")
r2, l2 = None, None
for rr in G2["arr"]:
    for ll in rr["lines"]:
        if ll["state"] == "short" and ll["id"] != l["id"]:
            r2, l2 = rr, ll
if r2:
    res, st = F.act(con, "walk", dict(do="close", oid=r2["id"], lid=l2["id"]))
    ok(st == 200, "Close: never came -> %s" % res)
    G3 = F.groups(con, NOW, with_bills=False)
    st3 = [x["state"] for g in F.GROUPS for rr in G3[g] if rr["id"] == r2["id"] for x in rr["lines"] if x["id"] == l2["id"]]
    ok(st3 == ["settled"], "the closed line reads settled (%s)" % st3)
rl, ll = first("late", ("open",))
if rl:
    res, st = F.act(con, "walk", dict(do="chase", oid=rl["id"]))
    ok(st == 200, "Chase now")
    n0 = con.execute("SELECT COUNT(*) FROM order_s778_again WHERE cleared_at IS NULL AND done_at IS NULL").fetchone()[0]
    res, st = F.act(con, "walk", dict(do="again", oid=rl["id"], lid=ll["id"]))
    ok(st == 200 and res.get("ok"), "Order again on a late line -> %s" % res)
    n = con.execute("SELECT COUNT(*) FROM order_s778_again WHERE cleared_at IS NULL AND done_at IS NULL").fetchone()[0]
    ok(n == n0 + (0 if res.get("already") else 1), "an again row waits for today's card (%d -> %d)" % (n0, n))
    res2, st2 = F.act(con, "walk", dict(do="again", oid=rl["id"], lid=ll["id"]))
    ok(st2 == 200 and con.execute("SELECT COUNT(*) FROM order_s778_again WHERE cleared_at IS NULL AND done_at IS NULL").fetchone()[0] == n, "a second Order again writes nothing more")
T = F.team(con)
oos = [t for t in T if t["kind"] == "oos"]
if len(oos) >= 3:
    res, st = F.act(con, "walk", dict(do="drop", na=oos[0]["id"]))
    ok(st == 200 and con.execute("SELECT status FROM order_s778_na WHERE id=?", (oos[0]["id"],)).fetchone()[0] == "stop", "Drop it -> stop")
    res, st = F.act(con, "walk", dict(do="wait", na=oos[1]["id"]))
    ok(st == 200, "Wait — order next week")
    ok(F.wait_pass(con, dt.date.today()) == 0, "wait_pass: not before the day")
    ok(F.wait_pass(con, dt.date.today() + dt.timedelta(days=8)) == 1, "wait_pass: on the day it becomes keep ordering")
    ok(con.execute("SELECT status FROM order_s778_na WHERE id=?", (oos[1]["id"],)).fetchone()[0] == "keep", "the waited medicine is back on the list")
lc = F._line_ctx(con, WOID, con.execute("SELECT id FROM purchase_order_line WHERE order_id=?", (WOID,)).fetchone()[0])
lid_w = con.execute("SELECT id FROM purchase_order_line WHERE order_id=?", (WOID,)).fetchone()[0]
k0 = con.execute("SELECT COUNT(*) FROM order_s778_again").fetchone()[0]
F._again_direct(con, "walk", lc, lid_w)
F._again_direct(con, "walk", lc, lid_w)
ok(con.execute("SELECT COUNT(*) FROM order_s778_again").fetchone()[0] == k0, "the direct door never writes a second row for the same line")
res, st = F.act(con, "walk", dict(do="close", oid="x1", lid=2))
ok(st == 400, "a non-numeric id is refused, not a crash")
res, st = F.act(con, "walk", ["not", "a", "dict"])
ok(st == 400, "a body that is not a dict is refused")
res, st = F.act(con, "walk", dict(do="nonsense"))
ok(st == 400, "a bad button is refused")
res, st = F.act(con, "walk", dict(do="close", oid=999999, lid=1))
ok(st == 409, "a line that is gone is refused")
# a substitute (reception's door is kit 2): the owner's two answers
mid = F._mark(con, "walk", "sub", order_id=r["id"], line_id=l["id"], item=l["item"], vendor=r["vendor"], sub_item="MADE-UP SUB 10")
ok(any(t["kind"] == "sub" for t in F.team(con)), "a substitute is on the team list")
res, st = F.act(con, "walk", dict(do="sub_ok", sub=mid))
ok(st == 200 and not any(t["kind"] == "sub" for t in F.team(con)), "Substitute OK takes it off the list")
html = F.owner_body(con, NOW)
ok("Not complete:" in html and "Delivered and complete" in html and "confirm(" not in html and "alert(" not in html, "the page: strips, no dialog")
ok("tap again" in html, "two taps")

# ---- the doors through flask (owner / Shavez / reception)
try:
    from flask import Flask
    import porders as PO
    app = Flask("walk920")
    who = {"u": None}

    def req(*roles, unit=None):
        return who["u"], None

    def dbg():
        cx = sqlite3.connect(DB)
        cx.row_factory = sqlite3.Row
        return cx
    PO.init(app, dbg, req)
    cl = app.test_client()
    who["u"] = dict(user="manoj", roles=["checker", "maker"])
    rv = cl.get("/finance/porders?old=1")
    t = rv.get_data(as_text=True)
    ok(t.index("Not complete:") < t.index("Ordering cards, settings") < t.index('<div id="body">') < t.index("</details>", t.index('<div id="body">')), "the fold wraps the old page in order")
    ok(rv.status_code == 200 and "Not complete:" in t and "Ordering cards, settings and the full ledger" in t and t.count('<div id="body">') == 1, "owner ?old=1: grouped view first, old page folded")
    ok(cl.get("/finance/porders/flow").status_code == 200, "owner /flow 200")
    who["u"] = dict(user="shavez", roles=["maker"])
    ok(cl.get("/finance/porders/flow").status_code == 200, "Shavez /flow 200")
    rv = cl.get("/finance/porders?old=1")
    ok("Not complete:" not in rv.get_data(as_text=True), "a sender's old page unchanged")
    who["u"] = dict(user="alisha", roles=["maker"])
    ok(cl.get("/finance/porders/flow").status_code == 403, "reception /flow 403")
    ok(cl.post("/finance/porders/api/flow/act", json=dict(do="chase", oid=1)).status_code in (403, 428), "reception cannot press his buttons")
    ok(cl.get("/finance/porders/api/flow/healthz").get_json().get("kit") == F.KIT, "healthz names the kit")
except Exception as e:                                            # noqa: BLE001
    ok(False, "flask walk: %s" % e)
con.close()
os.remove(DB)
print("RESULT:", "ALL PASS" if not FAIL else "%d FAIL" % len(FAIL))
sys.exit(1 if FAIL else 0)
