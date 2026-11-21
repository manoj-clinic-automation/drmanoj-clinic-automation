#!/usr/bin/env python3
"""walk_s922.py -- kit S922 walked on a COPY of finance.db (never the live one). argv: <code dir with the kit's files> <copy.db> [control]
Checks: Darpan's read-only view from the one reader (a late order's medicines; a medicine ordered again leaves it; the team list in his
script); his door (staff / owner 200, others refused); his page's script; reception's strip laid out for a phone; a CONTROL that must go
red (the 'ordered again' rule taken out)."""
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
DB = SRC + ".walk922"
shutil.copy(SRC, DB)
FAIL = []


def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAIL.append(what)


import order_flow as F                                            # noqa: E402

if CONTROL:                                                       # the control: a medicine ordered again no longer leaves the list
    F._ot()._ordered_since = lambda *a, **k: None

con = sqlite3.connect(DB, timeout=30)
con.row_factory = sqlite3.Row
NOW = dt.datetime(2026, 11, 21, 19, 30)
cols = {r[1] for r in con.execute("PRAGMA table_info(purchase_order)")}
lc = {r[1] for r in con.execute("PRAGMA table_info(purchase_order_line)")}


def _order(at):
    o = {k: v for k, v in dict(vendor="WALK922 MADE-UP DEALER", supplier_norm="WALK922", status="sent", created_at=at, created_by="walk").items() if k in cols}
    return con.execute("INSERT INTO purchase_order (%s) VALUES (%s)" % (", ".join(o), ",".join("?" * len(o))), list(o.values())).lastrowid


def _line(oid, item, packs):
    l = {k: v for k, v in dict(order_id=oid, item=item, packs=packs, pack_size=10).items() if k in lc}
    return con.execute("INSERT INTO purchase_order_line (%s) VALUES (%s)" % (", ".join(l), ",".join("?" * len(l))), list(l.values())).lastrowid


W1 = _order("2026-11-16T10:00:00")
_line(W1, "WALK922 MADE-UP TAB", 5)
_line(W1, "WALK922 MADE-UP GEL", 3)
con.commit()
v = F.dar_view(con, NOW)
mine = [r for r in v["rows"] if r["vendor"] == F._short("WALK922 MADE-UP DEALER")]
ok(bool(mine) and mine[0]["status"] == "late" and {i["item"] for i in mine[0]["items"]} == {"WALK922 MADE-UP TAB", "WALK922 MADE-UP GEL"},
   "his view: the late order with both medicines")
W2 = _order("2026-11-20T10:00:00")                                # the GEL ordered again on a later order of the same dealer
_line(W2, "WALK922 MADE-UP GEL", 3)
con.commit()
v = F.dar_view(con, NOW)
late = [r for r in v["rows"] if r["vendor"] == F._short("WALK922 MADE-UP DEALER") and r["status"] == "late"]
ok(bool(late) and [i["item"] for i in late[0]["items"]] == ["WALK922 MADE-UP TAB"], "a medicine ordered again leaves the late row by itself")
G = F.groups(con, NOW)
ok(len(v["team"]) == G["counts"]["team"], "his team list is the one list")
ok(F._qty_dev("10 patte") == "10 पत्ते" and F._qty_dev("1 nag") == "1 नग", "quantities in his script")
html = F.rec_body(con, NOW, G)
ok('class="lb"' in html or not any(l["state"] in ("short", "part") for g in ("arr", "gap") for r in G[g] for l in r["lines"]), "reception: a line's buttons on their own row")
ok('<div class="tm">' in html or not G["team"], "reception: the team list as short blocks")
ok("max-width:150px" in html and "table-layout:fixed" in html, "reception: a small scan, a table that fits a phone")
con.commit()

try:
    from flask import Flask, g
    import darpan_kal as DK
    import porders as PO
    app = Flask("walk922")
    who = {"u": None}

    def req(*roles, **k):
        return who["u"], None

    def dbg():
        if "wdb" not in g:
            g.wdb = sqlite3.connect(DB, timeout=30)
            g.wdb.row_factory = sqlite3.Row
        return g.wdb

    @app.teardown_appcontext
    def _td(e):
        d = g.pop("wdb", None)
        if d is not None:
            d.close()
    DK.init(app, dbg, req)
    PO.init(app, dbg, req)
    cl = app.test_client()
    who["u"] = dict(user="darpan", roles=["maker"])
    rv = cl.get("/finance/darpan/kal/api/order/flow")
    j = rv.get_json() or {}
    ok(rv.status_code == 200 and j.get("ok") and isinstance(j.get("rows"), list), "Darpan's door 200")
    t = cl.get("/finance/darpan/kal").get_data(as_text=True)
    ok("loadFlow()" in t and "डीलर से अभी आना बाकी" in t, "his page carries the two blocks")
    ok(cl.get("/finance/darpan/kal/api/order").status_code == 200, "his order list as before")
    who["u"] = dict(user="manoj", roles=["checker"])
    ok(cl.get("/finance/darpan/kal/api/order/flow").status_code == 200, "the owner reads it")
    who["u"] = dict(user="nobody_walk", roles=["viewer"])
    ok(cl.get("/finance/darpan/kal/api/order/flow").status_code in (401, 403), "anyone else refused")
    who["u"] = dict(user="alisha", roles=["maker"])
    t = cl.get("/finance/porders").get_data(as_text=True)
    ok("s921strip" in t, "reception's home still carries her strip")
except Exception as e:                                            # noqa: BLE001
    ok(False, "flask walk: %r" % (e,))
con.close()
os.remove(DB)
print("RESULT:", "ALL PASS" if not FAIL else "%d FAIL" % len(FAIL))
sys.exit(1 if FAIL else 0)
