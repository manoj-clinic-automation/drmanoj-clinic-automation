#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s715_page.py -- S715's desk PAGE in a real Chromium: the desk's own template and script (from the given sorting_desk.py),
served by a small stand-in server that answers the desk's API with MADE-UP data only (a made-up paper 'B-9715', made-up suppliers
'Walk715 ...', made-up items). Nothing real is read or written; no network beyond 127.0.0.1.

    python3 -B walk_s715_page.py <sorting_desk.py> [--expect-red]

Exit 0 when every check is green (or, with --expect-red, when every S715 check is red and the K checks green).
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
spec = importlib.util.spec_from_file_location("sorting_desk_walk", SRC)
sd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd)

app = Flask(__name__)
app.secret_key = "walk715"
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
    read = STATE["read"]
    v = STATE["v"]
    return {"ok": True, "id": 9715, "stamp": "B-9715", "supplier": "Walk715 Variety Stationers" if (read or v == "bill") else "",
            "bill_no": "2787" if read else "", "date": ("30-02-2031" if v == "baddate" else ("05-11-2031" if read else "")), "amount": "",
            "claude": {}, "own_line": "", "scanned": "05-11-2031", "month": "Nov 2031", "file": "/scanapp/bills/9715/file",
            "items": "No items read.", "bill_names": [], "kind": "bill" if v == "bill" else "challan", "kind_from": "paper", "dest": "stationery",
            "dest_line": "Where it is now.", "current": "Stationery & packaging", "who": "mk", "hints": [], "supplier_note": "",
            "mode": "", "covers": [], "flags": {"date": False, "nothing": True, "hold": "", "s441": ""}, "can_page": True,
            "status": "not accepted yet", "lane": "Clinic", "linked": "", "owner_line": "",
            "pay": {"state": "unpaid", "paid": 0, "total": None, "of": "", "last_on": "", "lines": [], "edit": None, "word": ""},
            "rc": {"recorded": False, "paid_on": "", "cands": [], "stmts": []}, "st": {"recorded": False, "cands": []},
            "to_acc": False, "fix": None, "aside": None, "mixed": False,
            "stk": {"lines": ([{"no": 1, "name": "WALK715 REG 72PG", "qty": "5", "unit": "piece", "rate": 25, "item": "102", "hand": False,
                                "sug": True, "saved": False, "flag": "", "side": ""}] if v == "readline" else
                              [{"no": 1, "name": "", "qty": "", "unit": "", "rate": None, "item": "", "hand": True, "sug": False,
                               "saved": False, "flag": "", "side": ""}]),
                    "items": ITEMS, "noread": True, "counts": True, "why": "", "listed": v == "bill"},
            "pr": {"lines": [{"no": 1, "name": "", "qty": "", "unit": "", "brand": "", "place": "proc", "item": "", "hand": True,
                              "sug": False, "saved": False, "orth": False}],
                   "items": PR_ITEMS, "places": [["proc", "Procedure room"], ["home", "Home use (Dr MK)"]], "owner": True,
                   "noread": True, "counts": True, "filled": False, "role": "slip", "orders": [], "order": "", "olines": {}, "book": ""},
            "bat": None}


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
    return jsonify(papers=[{"id": 9715, "stamp": "B-9715", "month": "Nov 2031", "supplier": "", "hint": "challan — supplier not read"}], total=1)


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
with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page(viewport={"width": 1366, "height": 900})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "favicon" not in m.text else None)
    pg.goto("http://127.0.0.1:%d/scanapp/desk?open=9715" % PORT)
    pg.wait_for_timeout(1500)
    ev = pg.evaluate
    ck("K1 the desk opens the made-up paper B-9715 and its Stationery lines panel shows", ev("document.getElementById('hstamp').textContent.indexOf('B-9715')==0 && document.getElementById('st568').style.display=='flex'"))
    # ---- Read it again (first, on the fresh paper)
    has_rr = ev("!!document.querySelector('[data-rr715]')")
    ck("V1 'Read it again' sits under 'Nothing could be read'", has_rr)
    if has_rr:
        pg.click("[data-rr715]")
        pg.wait_for_timeout(800)
        ck("V2 Read it again asks the app's own re-read door once and says so", REREAD == [9715] and "Asked again" in ev("document.getElementById('rr715msg').textContent"),
           (REREAD, ev("(document.getElementById('rr715msg')||{}).textContent")))
        pg.wait_for_timeout(21500)
        ck("V3 the empty boxes fill by themselves when it reads (number 2787, date 2031-11-05, supplier), and it says what it filled",
           ev("document.getElementById('f_no').value=='2787' && document.getElementById('f_date').value=='2031-11-05' && document.getElementById('f_vendor').value=='Walk715 Variety Stationers' && document.getElementById('rr715msg').textContent.indexOf('Read again: filled')==0"),
           ev("[document.getElementById('f_no').value,document.getElementById('f_date').value,document.getElementById('f_vendor').value,(document.getElementById('rr715msg')||{}).textContent]"))
    else:
        ck("V2 Read it again asks the app's own re-read door once and says so", False)
        ck("V3 the empty boxes fill by themselves when it reads", False)
    STATE["read"] = False
    pg.goto("http://127.0.0.1:%d/scanapp/desk?open=9715" % PORT)
    pg.wait_for_timeout(1500)
    # ---- the supplier
    pg.fill("#f_vendor", "Walk715 Var")
    pg.wait_for_timeout(300)
    dd = ev("(document.getElementById('sup715')||{style:{}}).style.display=='block' ? document.getElementById('sup715').textContent : ''")
    ck("V4 typing in Supplier opens the list of known suppliers (Walk715 Variety Stationers offered)", "Walk715 Variety Stationers" in dd, dd)
    ck("V5 a typed name not picked is not taken: Save reads 'Pick the supplier from the list'",
       ev("document.getElementById('save').disabled && document.getElementById('save').textContent=='Pick the supplier from the list'"),
       ev("[document.getElementById('save').disabled,document.getElementById('save').textContent]"))
    if ev("!!document.querySelector('[data-sp715]')"):
        pg.dispatch_event("[data-sp715='walk715 variety']", "mousedown")
        pg.wait_for_timeout(300)
    ck("V6 picking fills the full name and Save is free again",
       ev("document.getElementById('f_vendor').value=='Walk715 Variety Stationers' && !document.getElementById('save').disabled"),
       ev("[document.getElementById('f_vendor').value,document.getElementById('save').textContent]"))
    ck("V7 the supplier is on the stationery list: each line asks Clinic or NK Pathology", ev("!!document.querySelector('#st568 [data-s7s]')"))
    # ---- the date
    ck("V8 the date is a calendar box with Scan day and Today", ev("document.getElementById('f_date').type=='date' && document.querySelectorAll('[data-dt715]').length==2"))
    if ev("!!document.querySelector('[data-dt715]')"):
        pg.click("[data-dt715]")
        pg.wait_for_timeout(200)
    ck("V9 Scan day sets 2031-11-05 and the Read line shows it as 05-11-2031",
       ev("document.getElementById('f_date').value=='2031-11-05' && document.getElementById('readsum').textContent.indexOf('05-11-2031')>=0"),
       ev("[document.getElementById('f_date').value,document.getElementById('readsum').textContent]"))
    # ---- the lines
    pk = "#st568 [data-pk='st:0']"
    if ev("!!document.querySelector(\"%s\")" % pk):
        pg.click(pk)
        pg.fill(pk, "regis")
        pg.wait_for_timeout(300)
    opts = ev("Array.prototype.map.call(document.querySelectorAll('#st568 [data-pkk=\"st:0\"]'),function(b){return b.textContent;}).join(' | ')")
    ck("V10 the item box searches the list (both registers offered, and '+ Add “regis” to the list')",
       "Walk715 Register 72 pages" in opts and "Walk715 Register 192 pages" in opts and "Add “regis” to the list" in opts, opts)
    if ev("!!document.querySelector('#st568 [data-pko=\"102\"]')"):
        pg.dispatch_event("#st568 [data-pko='102']", "mousedown")
        pg.wait_for_timeout(300)
    ck("V11 picking shows the tick at once (✓ Walk715 Register 72 pages — on the list)", "✓ Walk715 Register 72 pages" in ev("(document.getElementById('tag715_0')||{}).textContent||''"))
    ck("V12 a chosen item with no quantity stops Save: 'Type the quantity on line 1'", ev("document.getElementById('save').textContent")=="Type the quantity on line 1",
       ev("document.getElementById('save').textContent"))
    if ev("!!document.querySelector('[data-s7q=\"0\"]')"):
        pg.fill("[data-s7q='0']", "4")
    ck("V13 then 'Choose Clinic or NK on line 1'", ev("document.getElementById('save').textContent")=="Choose Clinic or NK on line 1", ev("document.getElementById('save').textContent"))
    if ev("!!document.querySelector('[data-s7s=\"0\"]')"):
        pg.select_option("[data-s7s='0']", "clinic")
    ck("K5 with Clinic chosen Save is free (a free Save, as before)", ev("!document.getElementById('save').disabled && document.getElementById('save').textContent=='Save — next paper'"),
       ev("document.getElementById('save').textContent"))
    # + Add a line and a new item with unit and rate
    if ev("!!document.querySelector('[data-s7add]')"):
        pg.click("[data-s7add]")
        pg.wait_for_timeout(300)
    pk1 = "#st568 [data-pk='st:1']"
    ck("V15 '+ Add a line' gives a second line with its own item box", ev("!!document.querySelector(\"%s\")" % pk1))
    if ev("!!document.querySelector(\"%s\")" % pk1):
        pg.click(pk1)
        pg.fill(pk1, "Walk715 Stapler pins")
        pg.wait_for_timeout(300)
        if ev("!!document.querySelector('#st568 [data-pkk=\"st:1\"][data-pko=\"__new\"]')"):
            pg.dispatch_event("#st568 [data-pkk='st:1'][data-pko='__new']", "mousedown")
            pg.wait_for_timeout(300)
    ck("V16 '+ Add … to the list' opens the small form with the name filled, a unit and a rate",
       ev("!!document.querySelector('[data-a7n]') && document.querySelector('[data-a7n]').value=='Walk715 Stapler pins' && !!document.querySelector('[data-a7u]') && !!document.querySelector('[data-a7r]')"))
    if ev("!!document.querySelector('[data-a7u]')"):
        pg.select_option("[data-a7u]", "box")
        pg.fill("[data-a7r]", "45")
        pg.click("[data-a7ok]")
        pg.wait_for_timeout(300)
    ck("V17 the line reads '+ new on the list: Walk715 Stapler pins (box)' and keeps rate 45",
       "+ new on the list: Walk715 Stapler pins (box)" in ev("(document.getElementById('tag715_1')||{}).textContent||''") and ev("(document.querySelector('[data-s7r=\"1\"]')||{}).value")=="45")
    if ev("!!document.querySelector('[data-s7q=\"1\"]')"):
        pg.fill("[data-s7q='1']", "2")
        pg.select_option("[data-s7s='1']", "nk")
        pg.fill("[data-s7r='0']", "30")
        pg.fill("#f_amt", "210")
        pg.wait_for_timeout(200)
    ck("V18 the lines total against the paper: 'Lines total ₹210 · paper ₹210 · matches'",
       "Lines total ₹210 · paper ₹210 · matches" in ev("(document.getElementById('tot715')||{}).textContent||''"), ev("(document.getElementById('tot715')||{}).textContent"))
    # remove a line
    if ev("!!document.querySelector('[data-s7add]')"):
        pg.click("[data-s7add]")
        pg.wait_for_timeout(200)
        pg.click("[data-s7x='2']")
        pg.wait_for_timeout(200)
    ck("V19 × takes a line away", ev("document.querySelectorAll('#st568 .l715').length")==2, ev("document.querySelectorAll('#st568 .l715').length"))
    # every line NK
    if ev("!!document.querySelector('[data-s7s=\"0\"]')"):
        pg.select_option("[data-s7s='0']", "nk")
    ck("V20 every line NK stops Save: 'Every line is NK Pathology’s — sort it on the Stationery page'",
       ev("document.getElementById('save').textContent")=="Every line is NK Pathology’s — sort it on the Stationery page", ev("document.getElementById('save').textContent"))
    if ev("!!document.querySelector('[data-s7s=\"0\"]')"):
        pg.select_option("[data-s7s='0']", "clinic")
    # a new supplier whose first word matches a known one
    pg.fill("#f_vendor", "Walk715 Paper Mart")
    pg.wait_for_timeout(300)
    if ev("!!document.querySelector('[data-spnew715]')"):
        pg.dispatch_event("[data-spnew715]", "mousedown")
        pg.wait_for_timeout(200)
    ck("V21 a new supplier whose first word matches a known one is warned (looks like Walk715 …)",
       "This looks like Walk715" in ev("(document.getElementById('supw715')||{}).textContent||''"), ev("(document.getElementById('supw715')||{}).textContent"))
    pg.fill("#f_vendor", "Walk715 Var")
    pg.wait_for_timeout(200)
    if ev("!!document.querySelector('[data-sp715]')"):
        pg.dispatch_event("[data-sp715='walk715 variety']", "mousedown")
        pg.wait_for_timeout(200)
    # Save
    n0 = len(SAVED)
    if not ev("document.getElementById('save').disabled"):
        pg.click("#save")
        pg.wait_for_timeout(800)
    b = SAVED[-1] if len(SAVED) > n0 else {}
    lines = (b or {}).get("st_lines") or []
    ok = (b.get("vendor") == "Walk715 Variety Stationers" and b.get("bill_date") == "2031-11-05" and len(lines) == 2
          and lines[0].get("item") == "102" and str(lines[0].get("qty")) == "4" and lines[0].get("side") == "clinic" and str(lines[0].get("rate")) == "30"
          and lines[1].get("item") == "new" and lines[1].get("name") == "Walk715 Stapler pins" and lines[1].get("unit") == "box"
          and str(lines[1].get("rate")) == "45" and lines[1].get("side") == "nk" and b.get("mixed") is True)
    ck("V22 Save sends the picked supplier, the ISO date, both lines (item, qty, rate, unit, side) and marks it mixed", ok, json.dumps(b)[:600])
    # the procedure room panel
    pg.goto("http://127.0.0.1:%d/scanapp/desk?open=9715" % PORT)
    pg.wait_for_timeout(1500)
    pg.click("#groups [data-d='procedure']")
    pg.wait_for_timeout(300)
    ppk = "#pr634 [data-pk='pr:0']"
    ck("V23 the procedure room lines search the product list (no long drop-down)", ev("!!document.querySelector(\"%s\") && !document.querySelector('#pr634 [data-pri]')" % ppk))
    if ev("!!document.querySelector(\"%s\")" % ppk):
        pg.click(ppk)
        pg.fill(ppk, "gyps")
        pg.wait_for_timeout(300)
        if ev("!!document.querySelector('#pr634 [data-pko=\"202\"]')"):
            pg.dispatch_event("#pr634 [data-pko='202']", "mousedown")
            pg.wait_for_timeout(300)
    ck("V24 picking a product sets the line (Walk715 Gypsona 6 inch, marked rarely used in the list)",
       ev("(document.querySelector(\"%s\")||{}).value" % ppk)=="Walk715 Gypsona 6 inch", ev("(document.querySelector(\"%s\")||{}).value" % ppk))
    # V25 a stored date the calendar cannot show is kept on Save (never wiped)
    pg.goto("http://127.0.0.1:%d/scanapp/desk?open=9715&v=baddate" % PORT)
    pg.wait_for_timeout(1500)
    n0 = len(SAVED)
    if not ev("document.getElementById('save').disabled"):
        pg.click("#save")
        pg.wait_for_timeout(800)
    b = SAVED[-1] if len(SAVED) > n0 else {}
    ck("K6 a stored date the calendar cannot show is sent back as it was (never wiped)", b.get("bill_date") == "30-02-2031", json.dumps(b)[:200])
    # V26 x on a read line keeps it as 'not a stock item' (it never comes back counted)
    pg.goto("http://127.0.0.1:%d/scanapp/desk?open=9715&v=readline" % PORT)
    pg.wait_for_timeout(1500)
    if ev("!!document.querySelector('[data-s7x=\"0\"]')"):
        pg.click("[data-s7x='0']")
        pg.wait_for_timeout(200)
    n0 = len(SAVED)
    if not ev("document.getElementById('save').disabled"):
        pg.click("#save")
        pg.wait_for_timeout(800)
    b = SAVED[-1] if len(SAVED) > n0 else {}
    sl = b.get("st_lines") or []
    ck("V26 × on a line read from the paper sends it as 'not a stock item' (it does not come back counted)",
       len(sl) == 1 and sl[0].get("item") == "ns" and sl[0].get("no") == 1, json.dumps(b)[:300])
    # V27 the procedure room product can be cleared
    pg.goto("http://127.0.0.1:%d/scanapp/desk?open=9715" % PORT)
    pg.wait_for_timeout(1500)
    pg.click("#groups [data-d='procedure']")
    pg.wait_for_timeout(300)
    ok27 = False
    if ev("!!document.querySelector(\"%s\")" % ppk):
        pg.click(ppk)
        pg.fill(ppk, "cotton")
        pg.wait_for_timeout(200)
        if ev("!!document.querySelector('#pr634 [data-pko=\"203\"]')"):
            pg.dispatch_event("#pr634 [data-pko='203']", "mousedown")
            pg.wait_for_timeout(300)
        pg.click(ppk)
        pg.wait_for_timeout(200)
        if ev("!!document.querySelector('#pr634 [data-pko=\"\"]')"):
            pg.dispatch_event("#pr634 [data-pko='']", "mousedown")
            pg.wait_for_timeout(300)
            ok27 = ev("(document.querySelector(\"%s\")||{}).value" % ppk) == ""
    ck("V27 a procedure room line's product can be cleared ('— no product —')", ok27)
    # V28 Shavez's screen (not the owner): no rate box, no rate in the line's note, no lines total
    pg.goto("http://127.0.0.1:%d/scanapp/desk?open=9715&v=readline&owner=0" % PORT)
    pg.wait_for_timeout(1500)
    note = ev("(document.querySelector('#st568 [data-stf=\"0\"]')||{}).textContent||''")
    ck("V28 Shavez's screen shows no rate: no rate box, no 'rate ₹' in the line's note, no total",
       ev("!!document.querySelector('#st568 [data-pk]') && !document.querySelector('#st568 [data-s7r]')") and "rate" not in note.lower()
       and not ev("(document.getElementById('tot715')||{}).textContent||''"), note)
    # V29 a Variety paper read as a Bill, corrected to Challan: the Clinic / NK boxes appear (Save never asks for a box that is not there)
    pg.goto("http://127.0.0.1:%d/scanapp/desk?open=9715&v=bill" % PORT)
    pg.wait_for_timeout(1500)
    before = ev("!!document.querySelector('#st568 [data-s7s]')")
    if ev("!!document.querySelector('#kinds [data-k=\"challan\"]')"):
        pg.click("#kinds [data-k='challan']")
        pg.wait_for_timeout(300)
    if ev("!!document.querySelector('#st568 [data-pk=\"st:0\"]')"):
        pg.click("#st568 [data-pk='st:0']")
        pg.fill("#st568 [data-pk='st:0']", "file")
        pg.wait_for_timeout(200)
        if ev("!!document.querySelector('#st568 [data-pko=\"104\"]')"):
            pg.dispatch_event("#st568 [data-pko='104']", "mousedown")
            pg.wait_for_timeout(200)
        pg.fill("[data-s7q='0']", "1")
        pg.wait_for_timeout(200)
    ck("V29 a Variety paper read as a Bill and changed to Challan shows Clinic / NK on its lines, and Save asks for it",
       (not before) and ev("!!document.querySelector('#st568 [data-s7s]')") and ev("document.getElementById('save').textContent") == "Choose Clinic or NK on line 1",
       (before, ev("!!document.querySelector('#st568 [data-s7s]')"), ev("document.getElementById('save').textContent")))
    # the unchanged parts
    pg.click("#groups [data-d='stationery']")
    pg.wait_for_timeout(200)
    ck("K2 'Where does it go?' and 'What kind of paper' are as before (the destinations and kinds draw)",
       ev("document.querySelectorAll('#groups [data-d]').length")>=10 and ev("document.querySelectorAll('#kinds [data-k]').length")>=3)
    ck("K3 no script error on the page", not [e for e in errors if "Failed to load resource" not in e], errors[:5])
    # phone-width check of the right pane: the line and the add form never push the page sideways
    pg.set_viewport_size({"width": 1024, "height": 768})
    pg.wait_for_timeout(200)
    ck("K4 at 1024 px the page has no sideways scroll", ev("document.documentElement.scrollWidth<=document.documentElement.clientWidth+1"))
    br.close()

MUST_RED = ["V%d" % k for k in range(1, 30) if k not in (14, 25)]
if EXPECT_RED:
    red = [k for k in MUST_RED if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    print("CONTROL: %d of %d S715 checks red; K green %d of %d" % (len(red), len(MUST_RED), len(kg), len([k for k in RES if k.startswith('K')])))
    sys.exit(0 if len(red) == len(MUST_RED) and len(kg) == len([k for k in RES if k.startswith('K')]) else 1)
bad = [k for k, v in RES.items() if not v]
print("PAGE WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
