#!/usr/bin/env python3
"""walk_s923.py -- kit S923 walked on a COPY of finance.db (never the live one). argv: <code dir with the kit's files> <copy.db> [control]
Checks: the round-off allowance (tonight's eight scans read right; a real misread still asks); his setting moves it; his word (count /
aside / undo) on the copy; the page's top renders (needs one look, read right folded, still to come pointing away, no dialog); the doors
(owner only); a CONTROL that must go red (the allowance taken out)."""
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
DB = SRC + ".walk923"
shutil.copy(SRC, DB)
FAIL = []


def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAIL.append(what)


import provisional_s781 as PV                                    # noqa: E402

con = sqlite3.connect(DB, timeout=30)
con.row_factory = sqlite3.Row
PV.load_tol(con)
if CONTROL:                                                       # the control: the allowance taken out
    PV.load_tol = lambda c: PV.TOL
    PV.TOL[0], PV.TOL[1] = 0, 0.0


def x(lines_p, total_p):
    return dict(known=True, dealer="WALK923", bill_no="A000123", date="2026-11-20", day="2026-11-20", total_p=total_p,
                lines=[dict(amount="%.2f" % (p / 100.0)) for p in lines_p])


ok(PV.judge(x([188190], 187700)) == [], "lines ₹1,881.90 against a total of ₹1,877 read right (round-off)")
ok(PV.judge(x([330000], 329200)) == [], "lines ₹3,300 against ₹3,292 read right")
ok(PV.judge(x([250000], 187700)) != [], "lines ₹2,500 against ₹1,877 still ask (a real misread)")
ok(PV.judge(x([100000], 100000)) == [] and PV.judge(x([100000], 115000)) == [], "the old rules stand (equal; total up to 18% above)")
if not CONTROL:
    r, st = PV.set_tol(con, "walk", 2, 0.1)
    PV.load_tol(con)
    ok(st == 200 and PV.judge(x([188190], 187700)) != [], "his setting moves the allowance (₹2 / 0.1% -- the ₹4.90 gap asks again)")
    r, st = PV.set_tol(con, "walk", 10, 0.5)
    PV.load_tol(con)
    ok(st == 200 and PV.judge(x([188190], 187700)) == [], "back to ₹10 / 0.5%")
    ok(PV.set_tol(con, "walk", 900, 0.5)[1] == 400 and PV.set_tol(con, "walk", "x", 1)[1] == 400, "a value out of range refused")
r, st = PV.scan_word(con, "walk", 987654321, "count", "the lines read come to X")
ok(st == 200 and PV.scan_words(con).get(987654321, {}).get("word") == "count", "his word 'count it' kept")
r, st = PV.scan_word(con, "walk", 987654321, "aside", "")
ok(st == 200 and PV.scan_words(con)[987654321]["word"] == "aside", "his word changed to 'set aside'")
r, st = PV.scan_word(con, "walk", 987654321, "undo", "")
ok(st == 200 and 987654321 not in PV.scan_words(con), "Undo takes it back")
ok(PV.scan_word(con, "walk", 5, "drop", "")[1] == 400 and PV.scan_word(con, "walk", "x", "count", "")[1] == 400, "a bad word refused")
month = dt.date.today().strftime("%Y-%m")
prov = PV.provisional(con, month)
chk = [p for p in prov if p["why"]]
print("INFO the copy's month %s: %d scans waiting, %d to look at" % (month, len(prov), len(chk)))
if chk:
    sid = chk[0]["id"]
    PV.scan_word(con, "walk", sid, "count", chk[0]["why"][0])
    after = {p["id"]: p for p in PV.provisional(con, month)}
    ok(sid in after and not after[sid]["why"] and after[sid].get("counted_by_you"), "a real doubtful scan counted by his word")
    PV.scan_word(con, "walk", sid, "aside", "")
    ok(sid not in {p["id"] for p in PV.provisional(con, month)}, "set aside: it leaves the waiting list")
    PV.scan_word(con, "walk", sid, "undo", "")
html = PV.summary_html(con, month, "/finance/purchase", True)
ok('id="s923look"' in html and "Read right, counted:" in html and "Arrived and scanned, not yet in Marg" in html, "the page's top: needs one look, read right folded")
ok("Still to come" in html and "/finance/porders/flow" in html, "still to come: a tile pointing to the orders page, never listed here")
ok("alert(" not in html and "confirm(" not in html and "tap again" in html, "two taps, no dialog")
ok('id="s923rs"' in html and "Save" in html, "his allowance setting on the page")
html2 = PV.summary_html(con, month, "/finance/purchase", False)
ok('id="s923rs"' not in html2 and "s923two(this" not in html2, "a non-owner sees no buttons and no setting")
con.commit()

try:
    from flask import Flask, g
    import porders as PO
    app = Flask("walk923")
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
    PO.init(app, dbg, req)
    cl = app.test_client()
    who["u"] = dict(user="manoj", roles=["checker", "maker"])
    ok(cl.post("/finance/porders/api/flow/scanset", json=dict(rs=10, pct=0.5)).status_code == 200, "his Save 200")
    ok(cl.post("/finance/porders/api/flow/scan", json=dict(scan=987654322, do="count")).status_code == 200, "his word 200")
    ok(cl.post("/finance/porders/api/flow/scan", json=[1]).status_code == 400, "a body that is not an object refused")
    who["u"] = dict(user="alisha", roles=["maker"])
    ok(cl.post("/finance/porders/api/flow/scan", json=dict(scan=1, do="count")).status_code == 403, "reception cannot answer it")
    who["u"] = dict(user="shavez", roles=["maker"])
    ok(cl.post("/finance/porders/api/flow/scanset", json=dict(rs=99, pct=1)).status_code == 403, "nobody but the doctor moves the allowance")
    who["u"] = dict(user="alisha", roles=["maker"])
    ok("s921strip" in cl.get("/finance/porders").get_data(as_text=True), "reception's home still carries her strip")
except Exception as e:                                            # noqa: BLE001
    ok(False, "flask walk: %r" % (e,))
con.close()
os.remove(DB)
print("RESULT:", "ALL PASS" if not FAIL else "%d FAIL" % len(FAIL))
sys.exit(1 if FAIL else 0)
