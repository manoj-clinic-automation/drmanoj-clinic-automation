#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_anchor_s224.py -- the Vaapsi page and the counting page, rendered
for EVERY login, with the page's own JavaScript actually run.

The S208/S209 lesson: green gates behind a dead screen. So this does not grep
a template. It mounts the kit's returns_desk.py and the live-shape stock_app.py
on a real Flask server, opens each page in jsdom (a DOM with the page's script
executing, node 22), and TAPS: "gin liya" with no bill number must be refused
on the page; with one it must reach the server and land in the row with the
anchor. The server is then asked the same question directly, without the page,
because the page is the courtesy and the server is the rule.

Logins walked: darpan (maker) . shavez alisha shivani (viewer, desk users) .
amir (viewer, NOT a desk user -- must be refused in Hindi, F-296) . manoj
(checker, the owner).

Runs OFFLINE only (the VPS has no node). Needs jsdom:
    JSDOM_PATH=/path/to/node_modules   (default $HOME/s224live/node/node_modules)
    STOCK_DIR=/path/with/stock_app.py+stock_schema.sql+stock_check_live.html
             (the live-shape stock_app.py reproduced at 4e929d0b)
    python3 -B RENDER_TEST_anchor_s224.py
"""

import importlib.util
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
JSDOM = os.environ.get("JSDOM_PATH", os.path.join(HOME, "s224live", "node", "node_modules"))
STOCK_DIR = os.environ.get("STOCK_DIR", os.path.join(HOME, "s224live"))

PEOPLE = {
    "darpan":  dict(user="darpan",  role="staff",  roles=["maker", "viewer"]),
    "shavez":  dict(user="shavez",  role="staff",  roles=["viewer"]),
    "alisha":  dict(user="alisha",  role="staff",  roles=["viewer"]),
    "shivani": dict(user="shivani", role="staff",  roles=["viewer"]),
    "amir":    dict(user="amir",    role="staff",  roles=["viewer"]),
    "manoj":   dict(user="manoj",   role="doctor", roles=["checker"]),
}
DESK_USERS = "darpan,shavez,alisha,shivani"          # the live setting row (S222)
DESK = ("darpan", "shavez", "alisha", "shivani", "manoj")
ANCHOR_LABEL = "आख़िरी सेल बिल नंबर (Marg)"

N = {"pass": 0, "fail": 0}


def check(name, got, want=True):
    ok = (got == want)
    N["pass" if ok else "fail"] += 1
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name,
                        "" if ok else "   got=%r want=%r" % (got, want)))
    return ok


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


NODE_JS = r"""
const {JSDOM, VirtualConsole} = require('jsdom');
const base = process.argv[2], who = process.argv[3], mode = process.argv[4];
const hdr = {'X-Test-User': who};
async function get(path){ const r = await fetch(base+path, {headers: hdr}); return {status: r.status, text: await r.text()}; }
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function vaapsi(){
  const out = {who};
  const pg = await get('/finance/returns/desk/');
  out.status = pg.status;
  if (pg.status !== 200){ out.body = pg.text.slice(0, 300); return out; }
  const vc = new VirtualConsole(); const errs = []; vc.on('jsdomError', e => errs.push(String(e && e.message || e)));
  // fetch and alert are injected BEFORE the page's own scripts run, so the
  // page's parse-time loadSlips()/loadJaankari() go to the real server.
  const dom = new JSDOM(pg.text, {url: base+'/finance/returns/desk/', runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w){
      w.fetch = (u, o) => { o = o || {}; o.headers = Object.assign({}, o.headers || {}, hdr); return fetch(new URL(u, base).href, o); };
      w.alert = m => { out.alerts = (out.alerts || []).concat([String(m)]); };
    }});
  const w = dom.window;
  for (let i = 0; i < 40 && !w.document.getElementById('jkAnchor'); i++) await sleep(100);
  const d = w.document;
  out.jsErrors = errs;
  out.cardVisible = d.getElementById('jkCard') && !d.getElementById('jkCard').classList.contains('hide');
  const a = d.getElementById('jkAnchor');
  out.anchorPresent = !!a;
  const lab = d.querySelector('label[for="jkAnchor"]');
  out.anchorLabel = lab ? lab.textContent : null;
  out.anchorPlaceholder = a ? a.placeholder : null;
  out.spotHeading = Array.from(d.querySelectorAll('#jkList b')).map(b => b.textContent);
  out.rowsBefore = d.querySelectorAll('[id^="jkq_"]').length;
  if (mode !== 'tap' || !a) return out;
  // TAP 1: a quantity but no bill -- must be refused on the page, nothing posted
  const q = d.querySelector('[id^="jkq_"]'); const ref = q.id.slice(4);
  q.value = '7';
  const btn = Array.from(d.querySelectorAll('button')).find(b => b.textContent.trim() === 'गिन लिया');
  btn.click(); await sleep(400);
  out.msgAfterEmpty = d.getElementById('jkAnchorMsg') ? d.getElementById('jkAnchorMsg').textContent : null;
  out.focusedIsAnchor = d.activeElement === d.getElementById('jkAnchor');
  out.rowsAfterEmpty = d.querySelectorAll('[id^="jkq_"]').length;
  // TAP 2: type the bill, count again
  const a2 = d.getElementById('jkAnchor'); a2.value = 'a003195'; a2.dispatchEvent(new w.Event('input'));
  out.anchorUpper = w.JK_ANCHOR;
  d.getElementById('jkq_'+ref).value = '7';
  Array.from(d.querySelectorAll('button')).find(b => b.textContent.trim() === 'गिन लिया').click();
  for (let i = 0; i < 40 && d.querySelectorAll('[id^="jkq_"]').length >= out.rowsBefore; i++) await sleep(100);
  out.rowsAfterCounted = d.querySelectorAll('[id^="jkq_"]').length;
  out.anchorSurvivesRerender = d.getElementById('jkAnchor') ? d.getElementById('jkAnchor').value : null;
  out.doneLine = d.getElementById('jkDone').textContent;
  out.countedRef = ref;
  return out;
}
async function count(){
  const out = {who};
  const pg = await get('/finance/stock/page/count');
  out.status = pg.status;
  if (pg.status !== 200){ out.body = pg.text.slice(0, 300); return out; }
  const vc = new VirtualConsole(); const errs = []; vc.on('jsdomError', e => errs.push(String(e && e.message || e)));
  const dom = new JSDOM(pg.text, {url: base+'/finance/stock/page/count', runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc});
  const d = dom.window.document; await sleep(300);
  out.jsErrors = errs;
  const b = d.getElementById('bill');
  out.billPresent = !!b; out.billLabel = (d.querySelector('label[for="bill"]')||{}).textContent || null;
  out.billDatePresent = !!d.getElementById('billdate');
  out.startDisabledAtLoad = d.getElementById('start').disabled;
  out.lang = d.documentElement.lang;
  return out;
}
(mode === 'count' ? count() : vaapsi()).then(o => { console.log(JSON.stringify(o)); process.exit(0); })
  .catch(e => { console.log(JSON.stringify({who, error: String(e && e.stack || e)})); process.exit(0); });
"""


def main():
    from flask import Flask, jsonify, request
    tmp = tempfile.mkdtemp(prefix="s224render_")
    try:
        for f in ("returns_desk.py", "returns_desk.html"):
            shutil.copy(os.path.join(HERE, f), os.path.join(tmp, f))
        for f in ("stock_app.py", "stock_schema.sql", "stock_check_live.html", "stock_diffs.html"):
            shutil.copy(os.path.join(STOCK_DIR, f), os.path.join(tmp, f))
        rd = load(os.path.join(tmp, "returns_desk.py"), "rd_s224")
        sa = load(os.path.join(tmp, "stock_app.py"), "sa_s224")

        db = os.path.join(tmp, "finance.db")
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
        con.execute("INSERT INTO setting (key, value) VALUES ('returns.desk_users', ?)", (DESK_USERS,))
        con.execute("CREATE TABLE IF NOT EXISTS stock_spot_check ("
                    " id INTEGER PRIMARY KEY, unit TEXT NOT NULL, business_date TEXT NOT NULL,"
                    " bill_no TEXT NOT NULL, item_key TEXT NOT NULL, item_name TEXT, batch TEXT,"
                    " reason TEXT NOT NULL, requested_at TEXT NOT NULL,"
                    " status TEXT NOT NULL DEFAULT 'due' CHECK (status IN ('due','done','skipped')),"
                    " counted_qty TEXT, counted_by TEXT, counted_at TEXT, note TEXT,"
                    " UNIQUE(unit, bill_no, item_key))")
        for i, (item, key) in enumerate((("TEST TAB A", "ta"), ("TEST CAP B", "cb"), ("TEST SYR C", "sc"))):
            con.execute("INSERT INTO stock_spot_check (unit, business_date, bill_no, item_key, item_name,"
                        " batch, reason, requested_at) VALUES ('medical','2026-09-04',?,?,?,?,?,?)",
                        ("A00000%d" % i, key, item, "B%d" % i, "large_return", "2026-09-04T10:0%d:00" % i))
        con.commit()
        con.close()
        sa.ensure_schema(sqlite3.connect(db))
        con = sqlite3.connect(db)
        con.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) "
                    "VALUES ('04-09-2026','TEST TAB A',10,'1*10',10,'2026-09-04T09:00:00','render_test')")
        con.commit()
        con.close()

        def getdb():
            c = sqlite3.connect(db)
            c.row_factory = sqlite3.Row
            return c

        def require(*roles, **kw):
            who = request.headers.get("X-Test-User", "")
            u = PEOPLE.get(who)
            if not u or not set(u["roles"]).intersection(roles):
                return None, (jsonify(ok=False, error="not_permitted"), 403)
            return dict(u), None

        import logging
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        app = Flask("s224render")
        rd.init(app, getdb, require, unit="medical")
        sa.init(app, getdb, require, unit="medical")
        port = free_port()
        import flask.cli
        flask.cli.show_server_banner = lambda *a, **k: None
        th = threading.Thread(target=lambda: app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False),
                              daemon=True)
        th.start()
        time.sleep(0.8)
        base = "http://127.0.0.1:%d" % port
        js = os.path.join(tmp, "render.js")
        with open(js, "w", encoding="utf-8") as fh:
            fh.write(NODE_JS)
        env = dict(os.environ, NODE_PATH=JSDOM)

        def node(who, mode):
            p = subprocess.run(["node", js, base, who, mode], env=env, capture_output=True, text=True, timeout=60)
            try:
                return json.loads(p.stdout.strip().splitlines()[-1])
            except Exception:
                return {"who": who, "error": (p.stdout + p.stderr)[-600:]}

        print("== 1  THE VAAPSI PAGE, every login, JS running (jsdom) ==")
        for who in PEOPLE:
            o = node(who, "tap" if who == "darpan" else "look")
            if who not in DESK:
                check("%s: refused at the desk (403, F-296)" % who, o.get("status"), 403)
                check("%s: refusal is in Hindi" % who, "Vaapsi desk aapke naam par nahin hai" in (o.get("body") or ""))
                continue
            check("%s: page 200" % who, o.get("status"), 200)
            check("%s: no JS errors" % who, o.get("jsErrors"), [])
            check("%s: jaankari card visible" % who, o.get("cardVisible"))
            check("%s: THE ANCHOR BOX IS THERE" % who, o.get("anchorPresent"))
            check("%s: anchor label is Hindi" % who, o.get("anchorLabel"), ANCHOR_LABEL)
            check("%s: anchor placeholder A003195" % who, o.get("anchorPlaceholder"), "A003195")
            # darpan (walked first) counts one row; everyone after him sees two
            want_rows = 3 if who == "darpan" else 2
            check("%s: the spot rows render (%d)" % (who, want_rows), o.get("rowsBefore"), want_rows)
            if who == "darpan":
                check("darpan TAP 1: 'gin liya' with no bill is REFUSED on the page (Hindi line)",
                      "आख़िरी सेल बिल" in (o.get("msgAfterEmpty") or ""))
                check("darpan TAP 1: focus moves to the anchor box", o.get("focusedIsAnchor"))
                check("darpan TAP 1: nothing left the list", o.get("rowsAfterEmpty"), 3)
                check("darpan TAP 2: anchor upper-cased by the page", o.get("anchorUpper"), "A003195")
                check("darpan TAP 2: the counted row leaves the list", o.get("rowsAfterCounted"), 2)
                check("darpan TAP 2: anchor survives the re-render", o.get("anchorSurvivesRerender"), "A003195")
                check("darpan TAP 2: done line counts 1", "1" in (o.get("doneLine") or ""))
                c = sqlite3.connect(db)
                row = c.execute("SELECT answer, value, anchor_bill, answered_by FROM jaankari_answer "
                                "WHERE kind='spot' AND ref=?", (o.get("countedRef"),)).fetchone()
                c.close()
                check("darpan TAP 2: the ROW carries the anchor (D367)", row, ("counted", "7", "A003195", "darpan"))

        print("\n== 2  THE SERVER IS THE RULE (no page) ==")
        cl = app.test_client()
        for who in DESK:
            h = {"X-Test-User": who}
            r = cl.post("/finance/returns/desk/api/jaankari/answer", json=dict(kind="spot", ref="2", answer="counted", value="4"), headers=h)
            check("%s: counted WITHOUT anchor -> 400 anchor_required" % who, (r.status_code, r.get_json().get("error")), (400, "anchor_required"))
            check("%s: the refusal is Hindi" % who, r.get_json().get("message", "").startswith("आख़िरी"))
        h = {"X-Test-User": "shavez"}
        r = cl.post("/finance/returns/desk/api/jaankari/answer", json=dict(kind="spot", ref="2", answer="counted", value="4", anchor_bill=" a003200 "), headers=h)
        check("shavez: counted WITH anchor -> ok", r.get_json().get("ok"))
        r = cl.post("/finance/returns/desk/api/jaankari/answer", json=dict(kind="spot", ref="3", answer="dont_know"), headers=h)
        check("shavez: 'abhi nahin' needs NO anchor (it is not a count)", r.get_json().get("ok"))
        r = cl.post("/finance/returns/desk/api/jaankari/answer", json=dict(kind="identity", ref="CN1", answer="ok"), headers=h)
        check("shavez: identity answer unaffected", r.get_json().get("ok"))
        c = sqlite3.connect(db)
        rows = c.execute("SELECT ref, answer, anchor_bill FROM jaankari_answer ORDER BY id").fetchall()
        c.close()
        check("rows: anchor stored upper-cased and trimmed", ("2", "counted", "A003200") in rows)
        check("rows: non-count answers carry no anchor", all(a is None for r_, ans, a in rows if ans != "counted"))
        r = cl.get("/finance/returns/desk/api/jaankari", headers=h)
        lists = r.get_json()["lists"]
        got = dict((x["ref"], (x.get("answered") or {}).get("anchor")) for x in lists["spot"])
        check("api/jaankari reads the anchor back on the answered row", got.get("2"), "A003200")
        check("api/jaankari: 3 spot rows still listed (status untouched -- evidence only)", len(lists["spot"]), 3)

        print("\n== 3  THE COUNTING PAGE, every login (jsdom) ==")
        for who in PEOPLE:
            o = node(who, "count")
            check("%s: count page 200" % who, o.get("status"), 200)
            check("%s: no JS errors" % who, o.get("jsErrors"), [])
            check("%s: #bill anchor input present" % who, o.get("billPresent"))
            check("%s: #billdate present" % who, o.get("billDatePresent"))
            check("%s: Start counting disabled until the anchor is typed" % who, o.get("startDisabledAtLoad"))
            if who == "manoj":
                check("manoj (owner console): count-page label is English (D366)", o.get("billLabel"), "Last sale bill number")
            r = cl.post("/finance/stock/api/count", json=dict(marg_as_on="04-09-2026", items=[dict(item="TEST TAB A", marg_qty=10, counted_qty=9)]),
                        headers={"X-Test-User": who})
            check("%s: stock /api/count without bill_no -> 400 (the S208 rule holds)" % who, r.status_code, 400)

        print("\n%s  %d passed, %d failed" % ("RENDER GREEN" if not N["fail"] else "RENDER RED", N["pass"], N["fail"]))
        return 0 if not N["fail"] else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
