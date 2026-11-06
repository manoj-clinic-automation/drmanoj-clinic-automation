#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s732_page.py -- S732's desk PAGE in a real Chromium: the desk's own template and script (from the given sorting_desk.py),
served by a small stand-in server that answers the desk's API with MADE-UP data only (a made-up paper 'B-9732', made-up suppliers
'Walk732 ...', made-up items). Nothing real is read or written; no network beyond 127.0.0.1.

    python3 -B walk_s732_page.py <sorting_desk.py> [--expect-red]

Exit 0 when every check is green (or, with --expect-red, when every S732 check is red and the K checks green).
"""
import importlib.util
import json
import os
import socket
import sys
import threading
import time

from flask import Flask, jsonify, redirect, render_template_string, request

SRC = sys.argv[1]
EXPECT_RED = "--expect-red" in sys.argv
spec = importlib.util.spec_from_file_location("sorting_desk_walk732", SRC)
sd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd)

app = Flask(__name__)
app.secret_key = "walk732"
SAVED, REREAD = [], []
STATE = {"read": False, "v": "", "owner": True}
ITEMS = [{"id": 101, "name": "Walk715 A4 paper (75 gsm)", "unit": "ream", "rate": None},
         {"id": 102, "name": "Walk715 Register 72 pages", "unit": "piece", "rate": 20},
         {"id": 103, "name": "Walk715 Register 192 pages", "unit": "piece", "rate": None},
         {"id": 104, "name": "Walk715 File folder", "unit": "piece", "rate": None}]
PR_ITEMS = [{"id": 201, "name": "Walk715 Gypsona 4 inch", "unit": "roll", "brands": [], "rare": False},
            {"id": 202, "name": "Walk715 Gypsona 6 inch", "unit": "roll", "brands": [], "rare": True},
            {"id": 203, "name": "Walk715 Cotton roll", "unit": "roll", "brands": [], "rare": False}]
SUPPLIERS = [{"name": "Walk715 Variety Stationers", "key": "walk715 variety", "n": 12, "listed": True, "note": "12 papers · stationery list — Clinic or NK on each line"},
             {"name": "Walk715 Yuvika Surgicals", "key": "walk715 yuvika", "n": 30, "listed": False, "note": "30 papers"},
             {"name": "Walk715 Jasoria Brothers", "key": "walk715 jasoria", "n": 3, "listed": False, "note": "3 papers"}]


def paper():
    v = STATE["v"]
    return {"ok": True, "id": 9715, "stamp": "B-9732", "supplier": "Walk715 Jasoria Brothers", "bill_no": "4410", "date": "05-11-2031", "amount": "540",
            "claude": {}, "own_line": "", "scanned": "05-11-2031", "month": "Nov 2031", "file": "/scanapp/bills/9715/file",
            "items": "2 items read.", "bill_names": [], "kind": "bill", "kind_from": "paper", "dest": "stationery" if v == "stat" else "others",
            "dest_line": "Where it is now.", "current": "Others", "who": "mk", "hints": [], "supplier_note": "",
            "mode": "", "covers": [], "flags": {"date": False, "nothing": False, "hold": "", "s441": ""}, "can_page": True,
            "status": "not accepted yet", "lane": "Clinic", "linked": "", "owner_line": "",
            "pay": {"state": "unpaid", "paid": 0, "total": None, "of": "", "last_on": "", "lines": [], "edit": None, "word": ""},
            "rc": {"recorded": False, "paid_on": "", "cands": [], "stmts": []}, "st": {"recorded": False, "cands": []},
            "to_acc": False, "fix": None, "aside": None, "mixed": False,
            "stk": {"lines": [{"no": 1, "name": "", "qty": "", "unit": "", "rate": None, "item": "", "hand": True, "sug": False, "saved": False, "flag": "", "side": ""}],
                    "items": ITEMS, "noread": True, "counts": True, "why": "", "listed": False},
            "pr": None, "bat": None,
            "fo": None if v == "nofo" else {"lines": ([] if v == "noread" else [{"name": "WALK732 EXIDE BATTERY", "qty": 2.0, "unit": "piece", "rate": 200.0},
                                                                              {"name": "WALK732 TERMINAL GREASE", "qty": 1.0, "unit": "", "rate": None}]),
                                            "noread": v == "noread"}}


@app.route("/scanapp/desk")
def desk():
    STATE["v"] = request.args.get("v", "")
    STATE["owner"] = request.args.get("owner", "1") != "0"
    cfg = {"list": "/scanapp/desk/api/list", "paper": "/scanapp/desk/api/paper/0", "find": "/scanapp/desk/api/find",
           "save": "/scanapp/desk/api/save", "groups": [list(g) if not isinstance(g, list) else g for g in
                                                        [[t, [list(d) for d in items]] for t, items in sd.DESTINATIONS]],
           "kinds": [list(k) for k in sd.KINDS], "notes": sd.NOTES, "owner": True, "fix": "/x", "void": "/x", "restore": "/x",
           "modes": [list(m) for m in sd.PAY_MODES], "names": dict(sd.DEST_NAME), "open": "9715"}
    cfg["owner"] = STATE["owner"]
    if hasattr(sd, "_s715_cfg"):
        cfg.update({"sup715": "/scanapp/desk/api/suppliers", "reread": "/scanapp/bills/0/reread",
                    "units": ["piece", "pack", "packet", "ream", "box", "roll", "dozen"]})
    return render_template_string(sd.DESK_TPL, bg="#eef1f4", cfg=cfg, n=1, owner=STATE["owner"], chip="desk ON", title="Sorting desk",
                                  cant="", add_href="")


@app.route("/scanapp/desk/awaited")
def s551_awaited():
    return "x"


@app.route("/scanapp/desk/implants")
def s551_implants():
    return "x"


@app.route("/scanapp/desk/month")
def s551_month():
    return "x"


@app.route("/scanapp/desk/api/list")
def api_list():
    return jsonify(papers=[{"id": 9715, "stamp": "B-9732", "month": "Nov 2031", "supplier": "", "hint": "challan — supplier not read"}], total=1)


@app.route("/scanapp/desk/api/paper/<int:bid>")
def api_paper(bid):
    return jsonify(paper())


@app.route("/scanapp/desk/api/suppliers")
def api_sup():
    return jsonify(ok=True, suppliers=SUPPLIERS)


@app.route("/scanapp/desk/api/save", methods=["POST"])
def api_save():
    SAVED.append(request.get_json(silent=True))
    return jsonify(ok=True, message="saved (walk)", next=0)


@app.route("/scanapp/bills/<int:bid>/reread", methods=["POST"])
def reread(bid):
    REREAD.append(bid)
    STATE["read"] = True
    return redirect("/scanapp/bills/%d" % bid)


@app.route("/scanapp/bills/<int:bid>")
def bill(bid):
    return "<html><body>bill</body></html>"


@app.route("/scanapp/bills/<int:bid>/file")
def bill_file(bid):
    return "<html><body>the made-up scan</body></html>"


s = socket.socket()
s.bind(("127.0.0.1", 0))
PORT = s.getsockname()[1]
s.close()
threading.Thread(target=lambda: app.run(port=PORT, use_reloader=False), daemon=True).start()
time.sleep(1.0)

RES = {}


def ck(name, ok, detail=""):
    RES[name.split(" ")[0]] = bool(ok)
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(detail)[:300]) if (detail and not ok) else ""))


from playwright.sync_api import sync_playwright  # noqa: E402

errors = []
U = "http://127.0.0.1:%d/scanapp/desk?open=9715" % PORT
with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page(viewport={"width": 1366, "height": 900})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "favicon" not in m.text else None)
    ev = pg.evaluate
    pg.goto(U)
    pg.wait_for_timeout(1500)
    ck("K1 the desk opens the made-up paper B-9732", ev("document.getElementById('hstamp').textContent.indexOf('B-9732')==0"))
    shown = ev("(document.getElementById('fo732')||{style:{}}).style.display=='flex' && document.getElementById('fo732').textContent.indexOf('Other lines')>=0")
    ck("V1 a paper in Others shows the Other lines panel", shown)
    ck("V2 the panel starts from the lines read (name, qty, unit, rate in boxes)",
       ev("(function(){var n=document.querySelector('[data-fon=\"0\"]'),q=document.querySelector('[data-foq=\"0\"]'),u=document.querySelector('[data-fou=\"0\"]'),r=document.querySelector('[data-fr=\"0\"]');return !!(n&&n.value=='WALK732 EXIDE BATTERY'&&q.value=='2'&&u.value=='piece'&&r.value=='200'&&document.querySelectorAll('#fo732 .fol732').length==2);})()"))
    ck("V3 each line's amount and the lines' total against the paper are shown",
       ev("(document.querySelector('[data-foa=\"0\"]')||{}).textContent=='₹400' && (document.getElementById('fotot732')||{}).textContent=='Lines total ₹400 · the paper ₹540'"),
       ev("[(document.querySelector('[data-foa=\"0\"]')||{}).textContent,(document.getElementById('fotot732')||{}).textContent]"))
    n0 = len(SAVED)
    if ev("!document.getElementById('save').disabled"):
        pg.click("#save")
        pg.wait_for_timeout(600)
    b0 = SAVED[-1] if len(SAVED) > n0 else None
    ck("K2 a Save with the panel untouched sends no lines (the read item lines stay)", b0 is not None and "fo_lines" not in b0 and b0.get("dest") == "others", b0)
    pg.goto(U)
    pg.wait_for_timeout(1200)
    if ev("!!document.querySelector('[data-fr=\"1\"]')"):
        pg.fill("[data-fr='1']", "140")
        pg.fill("[data-fon='0']", "Walk732 Inverter battery 150Ah")
        pg.fill("[data-fr='0']", "200")
        pg.wait_for_timeout(200)
    ck("V4 typing a rate updates the line's amount and the total", ev("(document.querySelector('[data-foa=\"1\"]')||{}).textContent=='₹140' && (document.getElementById('fotot732')||{}).textContent.indexOf('Lines total ₹540')==0"),
       ev("[(document.querySelector('[data-foa=\"1\"]')||{}).textContent,(document.getElementById('fotot732')||{}).textContent]"))
    if ev("!!document.querySelector('[data-foadd]')"):
        pg.click("[data-foadd]")
        pg.wait_for_timeout(200)
    ck("V5 '+ Add a line' adds an empty line", ev("document.querySelectorAll('#fo732 .fol732').length==3 && document.querySelector('[data-fon=\"2\"]').value==''"))
    if ev("!!document.querySelector('[data-foq=\"2\"]')"):
        pg.fill("[data-foq='2']", "3")
        pg.wait_for_timeout(150)
    ck("V6 a line with a quantity and no name says 'what is it?'", ev("(document.querySelector('[data-foe=\"2\"]')||{}).textContent=='what is it?'"),
       ev("(document.querySelector('[data-foe=\"2\"]')||{}).textContent"))
    if ev("!!document.querySelector('[data-fox=\"2\"]')"):
        pg.click("[data-fox='2']")
        pg.wait_for_timeout(200)
    ck("V7 × removes the line", ev("document.querySelectorAll('#fo732 .fol732').length==2"))
    n0 = len(SAVED)
    if ev("!document.getElementById('save').disabled"):
        pg.click("#save")
        pg.wait_for_timeout(600)
    b1 = SAVED[-1] if len(SAVED) > n0 else {}
    ck("V8 the Save sends the changed lines as typed",
       (b1 or {}).get("fo_lines") == [{"name": "Walk732 Inverter battery 150Ah", "qty": "2", "unit": "piece", "rate": "200"}, {"name": "WALK732 TERMINAL GREASE", "qty": "1", "unit": "", "rate": "140"}],
       (b1 or {}).get("fo_lines"))
    pg.goto(U + "&v=noread")
    pg.wait_for_timeout(1200)
    ck("V9 nothing read: 'No items read — fill the lines by hand.' and one empty line", ev("(document.getElementById('fo732')||{textContent:''}).textContent.indexOf('No items read')>=0 && document.querySelectorAll('#fo732 .fol732').length==1"))
    pg.goto(U + "&v=stat")
    pg.wait_for_timeout(1200)
    ck("K3 a paper in Stationery shows its Stationery panel and no Other lines", ev("document.getElementById('st568').style.display=='flex' && (document.getElementById('fo732')||{style:{display:'none'}}).style.display=='none'"))
    pg.click("#groups [data-d='others']")
    pg.wait_for_timeout(300)
    ck("V10 choosing Others on the desk brings the Other lines panel", ev("(document.getElementById('fo732')||{style:{}}).style.display=='flex' && document.getElementById('st568').style.display!='flex'"))
    ck("K4 the destinations and kinds still draw", ev("document.querySelectorAll('#groups [data-d]').length")>=10 and ev("document.querySelectorAll('#kinds [data-k]').length")>=3)
    ck("K5 no script error on the page", not [e for e in errors if "Failed to load resource" not in e], errors[:5])
    pg.set_viewport_size({"width": 1024, "height": 768})
    pg.goto(U)
    pg.wait_for_timeout(1200)
    ck("K6 at 1024 px the page has no sideways scroll", ev("document.documentElement.scrollWidth<=document.documentElement.clientWidth+1"))
    br.close()

MUST_RED = ["V%d" % k for k in range(1, 11)]
if EXPECT_RED:
    red = [k for k in MUST_RED if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S732 checks red; K green %d of %d" % (len(red), len(MUST_RED), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST_RED) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("PAGE WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
