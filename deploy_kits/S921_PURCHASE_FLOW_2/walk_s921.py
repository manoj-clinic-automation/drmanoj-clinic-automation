#!/usr/bin/env python3
"""walk_s921.py -- kit S921 walked on a COPY of finance.db (never the live one). argv: <code dir with the kit's files> <copy.db> [control]
Checks: reception's strip from the one reader; her buttons on a copy; his row reads her word; the doors (reception / viewer / owner);
the order screen's words; the switch; a CONTROL that must go red (her word taken out of the reader)."""
import datetime as dt
import os
import re
import shutil
import sqlite3
import sys

CODE, SRC = sys.argv[1], sys.argv[2]
CONTROL = len(sys.argv) > 3 and sys.argv[3] == "control"
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, CODE)
os.environ["PORDERS_SOURCE"] = "tables"
DB = SRC + ".walk921"
shutil.copy(SRC, DB)
FAIL = []


def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAIL.append(what)


import order_flow as F                                            # noqa: E402

if CONTROL:                                                       # the control: reception's word taken out of the reader
    F.rec_marks = lambda con: {}

con = sqlite3.connect(DB, timeout=30)
con.row_factory = sqlite3.Row
NOW = dt.datetime(2026, 11, 21, 19, 30)
cols = {r[1] for r in con.execute("PRAGMA table_info(purchase_order)")}
o = dict(vendor="WALK921 MADE-UP DEALER", supplier_norm="WALK921", status="sent", created_at="2026-11-16T10:00:00", created_by="walk")
o = {k: v for k, v in o.items() if k in cols}
WOID = con.execute("INSERT INTO purchase_order (%s) VALUES (%s)" % (", ".join(o), ",".join("?" * len(o))), list(o.values())).lastrowid
lc = {r[1] for r in con.execute("PRAGMA table_info(purchase_order_line)")}


def _line(oid, item, packs):
    l = {k: v for k, v in dict(order_id=oid, item=item, packs=packs, pack_size=10).items() if k in lc}
    return con.execute("INSERT INTO purchase_order_line (%s) VALUES (%s)" % (", ".join(l), ",".join("?" * len(l))), list(l.values())).lastrowid


L1 = _line(WOID, "WALK921 MADE-UP TAB", 5)
L2 = _line(WOID, "WALK921 MADE-UP GEL", 3)
con.commit()
G = F.groups(con, NOW, with_bills=False)
c = G["counts"]
print("counts", c)
ok(any(r["id"] == WOID for r in G["late"]), "the made-up order is late")
html = F.rec_body(con, NOW, G)
ok('id="s921strip"' in html and "Order ka maal nahi aaya" in html, "her strip, with the duty's door words")
ok(("Maal baaki: %d order" % (c["late"] + c["way"] + c["arr"] + c["gap"])) in html, "her count is his count (one reader)")
ok(html.count("Maal aa gaya</a>") == c["way"], "every on-the-way row has Maal aa gaya")
ok("Order again" not in html and "Close: never came" not in html and "Ab nahi milta" not in html and "Stock khatam" not in html, "her words only")
ok("alert(" not in html and "confirm(" not in html and "dobara dabaiye" in html, "two taps, no dialog")
ok(F.qty_en("50 patte") == "50 strips" and F.qty_en("1 nag") == "1 pc" and F.qty_en("3 botal") == "3 bottles", "F-1551 English quantities")

res, st = F.rec_act(con, "reception (walk)", dict(do="called", oid=WOID))
ok(st == 200, "Call kiya -- aa raha hai saved")
rr = [r for r in F.groups(con, NOW, with_bills=False)["late"] if r["id"] == WOID][0]
ok("Reception called" in F._row_acts(rr), "his late row reads her word")
ok("Call kiya" in F.rec_row(con, rr), "her row reads her word")
res, st = F.rec_act(con, "reception (walk)", dict(do="refused", oid=WOID))
rr = [r for r in F.groups(con, NOW, with_bills=False)["late"] if r["id"] == WOID][0]
ok(st == 200 and "will not send" in F._row_acts(rr), "Nahi bhejenge: the newest word wins on his row")
res, st = F.rec_act(con, "reception (walk)", dict(do="sub", oid=WOID, lid=L2))
ok(st == 200 and any(t["kind"] == "sub" and t["item"] == "WALK921 MADE-UP GEL → substitute" for t in F.team(con)), "Substitute aaya on the team list")
res, st = F.rec_act(con, "reception (walk)", dict(do="sub", oid=WOID, lid=L2))
ok(st == 200 and res.get("already"), "Substitute aaya twice: once")
res, st = F.rec_act(con, "reception (walk)", dict(do="oosrow", oid=WOID))
ok(st == 200 and any(t["kind"] == "oos" and t["item"] == "WALK921 MADE-UP TAB" for t in F.team(con)), "Out of stock on the late row: its lines on the team list")
res, st = F.rec_act(con, "reception (walk)", dict(do="called", oid=99999999))
ok(st == 409, "a gone order refused")
res, st = F.rec_act(con, "reception (walk)", dict(do="drop", na=1))
ok(st == 400, "his buttons are not hers")
con.commit()

try:
    from flask import Flask, g
    import porders as PO
    app = Flask("walk921")
    who = {"u": None}

    def req(*roles, unit=None):
        return who["u"], None

    def dbg():                                                    # one connection a request, closed at its end -- as the app does
        if "wdb" not in g:
            g.wdb = sqlite3.connect(DB, timeout=30)
            g.wdb.row_factory = sqlite3.Row
        return g.wdb

    @app.teardown_appcontext
    def _td(e):
        d = g.pop("wdb", None)
        if d is not None:
            d.close()
    PO.init(app, dbg, req)
    cl = app.test_client()
    who["u"] = dict(user="alisha", roles=["maker"])
    t = cl.get("/finance/porders").get_data(as_text=True)
    ok("s921strip" in t and 'id="row_late"' not in t and 'id="row_maal"' not in t, "reception's home: the strip, the two old rows gone")
    ok('id="park_' not in t and "alert(" not in t, "reception's home: no September link, no dialog")
    rv = cl.post("/finance/porders/api/flow/rec", json=dict(do="called", oid=WOID))
    ok(rv.status_code == 200, "reception's door 200")
    ok(cl.post("/finance/porders/api/flow/act", json=dict(do="chase", oid=WOID)).status_code in (403, 428), "reception cannot press his buttons")
    ok(cl.get("/finance/porders/flow?rec=1").status_code == 403, "reception cannot open his preview")
    t = cl.get("/finance/porders/s454/order").get_data(as_text=True)
    ok("Ab nahi milta" not in t, "the order screen says Out of stock")
    who["u"] = dict(user="bhati", roles=["viewer"])
    ok(cl.post("/finance/porders/api/flow/rec", json=dict(do="called", oid=WOID)).status_code == 403, "a viewer refused")
    who["u"] = dict(user="darpan", roles=["maker"])
    ok("s921strip" not in cl.get("/finance/porders").get_data(as_text=True), "Darpan's home unchanged (his tab is kit 3)")
    who["u"] = dict(user="manoj", roles=["checker", "maker"])
    t = cl.get("/finance/porders/flow?rec=1").get_data(as_text=True)
    ok("s921strip" in t, "his preview of her strip")
    t = cl.get("/finance/porders?old=1").get_data(as_text=True)
    ok("Not complete:" in t and not re.search(r">\d+ (patte|nag|goli|botal)<", t) and "alert(" not in t, "his page: English quantities, no dialog")
    ok("s921strip" not in cl.get("/finance/porders").get_data(as_text=True), "his home has no strip")
    ok(cl.get("/finance/porders/api/flow/healthz").get_json().get("kit") == F.KIT, "healthz names the kit")
    cx = sqlite3.connect(DB, timeout=30)
    cx.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('order_flow.rec_on','0')")
    cx.commit()
    cx.close()
    who["u"] = dict(user="alisha", roles=["maker"])
    ok("s921strip" not in cl.get("/finance/porders").get_data(as_text=True), "the switch off: her home as before")
except Exception as e:                                            # noqa: BLE001
    ok(False, "flask walk: %s" % e)
con.close()
os.remove(DB)
print("RESULT:", "ALL PASS" if not FAIL else "%d FAIL" % len(FAIL))
sys.exit(1 if FAIL else 0)
