#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RENDER_TEST_diffs_role_s224.py -- the diffs page RENDERED for every login,
with the page's own JavaScript actually run (jsdom, node 22).

The S208/S209 lesson: green gates behind a dead screen. So this does not grep
the template. It mounts the kit's stock_app.py (the live 4e929d0b bytes plus
this kit's patch) on a real Flask server over a temp finance.db seeded with
THREE differences, opens /page/diffs in jsdom as the owner (checker), Darpan
(maker) and Amir (viewer) and counts the buttons each of them is offered --
then TAPS: the owner names a cause, Darpan records a reason, and both land in
the rows. The server is then asked directly, without the page, because the
page is the courtesy and the server is the rule.

The fake login has the LIVE shape (finance_app.require): role = the broker's
clinic-wide role ('doctor', 'staff'), roles = the unit roles. That is what
proves _has_role: the owner is role='doctor', roles=['checker'].

Runs OFFLINE only (the VPS has no node). Needs jsdom:
    JSDOM_PATH=/path/to/node_modules   (default $HOME/s224live/node/node_modules)
    STOCK_SCHEMA=/path/to/stock_schema.sql (default $HOME/s224live/stock_schema.sql)
    python3 -B RENDER_TEST_diffs_role_s224.py      (from inside the kit folder)
"""

import importlib.util
import json
import os
import re
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
SCHEMA = os.environ.get("STOCK_SCHEMA", os.path.join(HOME, "s224live", "stock_schema.sql"))

PEOPLE = {
    "manoj":  dict(user="manoj",  role="doctor", roles=["checker"]),
    "darpan": dict(user="darpan", role="staff",  roles=["maker", "viewer"]),
    "amir":   dict(user="amir",   role="staff",  roles=["viewer"]),
    "alisha": dict(user="alisha", role="staff",  roles=["viewer"]),
}
N_CAUSES, N_REASONS = 8, 7
TEN = re.compile(r"\d{10}")

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
const base = process.argv[1], who = process.argv[2], tap = process.argv[3] || '';
const hdr = {'X-Test-User': who};
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function run(){
  const out = {who};
  const r = await fetch(base + '/finance/stock/page/diffs', {headers: hdr});
  out.status = r.status; const html = await r.text();
  if (r.status !== 200){ out.body = html.slice(0, 300); return out; }
  const vc = new VirtualConsole(); const errs = []; vc.on('jsdomError', e => errs.push(String(e && e.message || e)));
  const dom = new JSDOM(html, {url: base + '/finance/stock/page/diffs', runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w){ w.fetch = (u, o) => { o = o || {}; o.headers = Object.assign({}, o.headers || {}, hdr); return fetch(new URL(u, base).href, o); }; }});
  const w = dom.window, d = w.document;
  for (let i = 0; i < 40 && !d.querySelector('.card'); i++) await sleep(100);
  await sleep(200);
  out.jsErrors = errs;
  out.cards = d.querySelectorAll('.card').length;
  out.causeButtons = d.querySelectorAll('.causes[data-kind="cause"] button').length;
  out.answerButtons = d.querySelectorAll('.causes[data-kind="answer"] button').length;
  out.buttons = d.querySelectorAll('button').length;
  out.inputs = d.querySelectorAll('input, textarea, select').length;
  out.sub = d.getElementById('sub').textContent;
  out.text = d.body.textContent;
  out.recLines = Array.from(d.querySelectorAll('.rec')).map(e => e.textContent.trim());
  if (tap === 'cause'){
    const b = Array.from(d.querySelectorAll('.causes[data-kind="cause"] button')).find(x => x.dataset.k === 'BREAKAGE');
    d.querySelector('.note').value = 'dropped the strip';
    b.click(); await sleep(500);
    out.tapDone = d.querySelector('.done').textContent; out.tapOn = b.dataset.on;
  }
  if (tap === 'answer'){
    const cards = d.querySelectorAll('.card');
    const b = Array.from(cards[1].querySelectorAll('.causes[data-kind="answer"] button')).find(x => x.dataset.k === 'not_billed');
    b.click(); await sleep(500);
    out.tapDone = cards[1].querySelector('.done').textContent; out.tapOn = b.dataset.on;
  }
  return out;
}
run().then(o => { console.log(JSON.stringify(o)); process.exit(0); })
  .catch(e => { console.log(JSON.stringify({who, error: String(e && e.stack || e)})); process.exit(0); });
"""


def main():
    from flask import Flask, jsonify, request
    tmp = tempfile.mkdtemp(prefix="s224diffs_")
    try:
        for f in ("stock_app.py", "stock_diffs.html"):
            shutil.copy(os.path.join(HERE, f), os.path.join(tmp, f))
        shutil.copy(SCHEMA, os.path.join(tmp, "stock_schema.sql"))
        sa = load(os.path.join(tmp, "stock_app.py"), "sa_s224d")
        check("the stock app under test carries the S224 DIFFS ROLE mark",
              "S224 DIFFS ROLE" in open(sa.__file__, encoding="utf-8").read())

        db = os.path.join(tmp, "finance.db")
        sa.ensure_schema(sqlite3.connect(db))

        def getdb():
            c = sqlite3.connect(db)
            c.row_factory = sqlite3.Row
            return c

        def require(*roles, **kw):
            who = request.headers.get("X-Test-User", "")
            u = PEOPLE.get(who)
            if not u or not set(u["roles"]).intersection(roles):
                return None, (jsonify(ok=False, error="not_permitted",
                                      message="Your login is not permitted to do this."), 403)
            return dict(u), None

        app = Flask("s224diffs")
        sa.init(app, getdb, require, unit="medical", url_prefix="/finance/stock", marg_token="t")
        port = free_port()
        base = "http://127.0.0.1:%d" % port
        threading.Thread(target=lambda: app.run(port=port, threaded=True, use_reloader=False),
                         daemon=True).start()
        time.sleep(1.2)

        cl = app.test_client()
        H = lambda who: {"X-Test-User": who}
        AS_ON = "03-09-2026"
        j = cl.post("/finance/stock/api/snapshot", headers=H("manoj"), json=dict(
            as_on=AS_ON, source="render",
            items=[dict(item="ZZR ALPHA 200", qty=100, packing="1*10", pack_size=10, rate_p=250),
                   dict(item="ZZR BETA SYP", qty=30, packing="1*1", pack_size=1, rate_p=9000),
                   dict(item="ZZR GAMMA INJ", qty=12, packing="1*1", pack_size=1, rate_p=4500)])).get_json()
        check("seed: the snapshot loads", j.get("ok"))
        j = cl.post("/finance/stock/api/count", headers=H("amir"), json=dict(
            marg_as_on=AS_ON, bill_no="A003195", bill_date=AS_ON, items_total=3,
            items=[dict(item="ZZR ALPHA 200", marg_qty=100, counted_qty=92, pack_size=10,
                        counted_by="amir", entered_by="amir"),
                   dict(item="ZZR BETA SYP", marg_qty=30, counted_qty=27, pack_size=1,
                        counted_by="amir", entered_by="amir"),
                   dict(item="ZZR GAMMA INJ", marg_qty=12, counted_qty=14, pack_size=1,
                        counted_by="amir", entered_by="amir")])).get_json()
        check("seed: Amir (viewer) submits the count", j.get("ok"), True)
        cid = j.get("count_id")
        op = cl.get("/finance/stock/api/open", headers=H("manoj")).get_json()
        check("seed: three open differences", op.get("open"), 3)
        ids = [x["id"] for x in op["items"]]

        # ---- the API's word on who is looking (live-shape logins)
        for who, want in (("manoj", (True, False)), ("darpan", (False, True)),
                          ("amir", (False, False)), ("alisha", (False, False))):
            y = cl.get("/finance/stock/api/open", headers=H(who)).get_json().get("you", {})
            check("/api/open you: %s -> may_cause=%s may_answer=%s" % (who, want[0], want[1]),
                  (y.get("may_cause"), y.get("may_answer")), want)
            check("/api/open you.user is %s" % who, y.get("user"), who)
        it = cl.get("/finance/stock/api/open", headers=H("manoj")).get_json()["items"][0]
        check("/api/open still carries every S213 field (additive)",
              all(k in it for k in ("id", "item", "found_on", "marg_qty", "counted_qty",
                                    "diff", "value_p", "cause", "cause_note", "counted_by")))
        check("/api/open lines carry answer (None yet) and cause_label",
              ("answer" in it) and it.get("cause_label") == "not yet explained")
        f = cl.get("/finance/stock/api/finding/%d" % cid, headers=H("manoj")).get_json()
        check("/api/finding you.may_decide is TRUE for the live-shape owner (role=doctor, roles=[checker])",
              (f.get("you") or {}).get("may_decide"), True)
        f2 = cl.get("/finance/stock/api/finding/%d" % cid, headers=H("darpan")).get_json()
        check("/api/finding you.may_decide is FALSE for Darpan", (f2.get("you") or {}).get("may_decide"), False)

        # ---- the page, rendered and tapped
        def render(who, tap=""):
            p = subprocess.run(["node", "-e", NODE_JS, base, who, tap], capture_output=True, text=True,
                               env=dict(os.environ, NODE_PATH=JSDOM), timeout=60)
            try:
                return json.loads(p.stdout.strip().splitlines()[-1])
            except Exception:
                return {"who": who, "error": (p.stdout + p.stderr)[-600:]}

        # VIEWER (Amir, then Alisha): text only
        for who in ("amir", "alisha"):
            o = render(who)
            check("%s: page 200, no JS error" % who, (o.get("status"), o.get("jsErrors")), (200, []))
            check("%s: three cards" % who, o.get("cards"), 3)
            check("%s: ZERO buttons and ZERO inputs -- nothing that would refuse" % who,
                  (o.get("buttons"), o.get("inputs")), (0, 0))
            check("%s: the cause is shown as text" % who,
                  sum(1 for l in o.get("recLines", []) if l.startswith("cause: not yet explained")), 3)
            check("%s: the sub-line is the viewer's" % who, "shown here as recorded" in (o.get("sub") or ""))
            check("%s: no 10-digit run on the page" % who, bool(TEN.search(o.get("text") or "")), False)

        # MAKER (Darpan): the staff reason buttons, no cause buttons, no note box; taps one
        o = render("darpan", "answer")
        check("darpan: page 200, no JS error", (o.get("status"), o.get("jsErrors")), (200, []))
        check("darpan: 7 reason buttons per card (21), ZERO cause buttons",
              (o.get("answerButtons"), o.get("causeButtons")), (3 * N_REASONS, 0))
        check("darpan: no note box (that is the checker's)", o.get("inputs"), 0)
        check("darpan: the sub-line is the maker's", "recorded against your name" in (o.get("sub") or ""))
        check("darpan: tapping a reason is recorded on the page",
              (o.get("tapDone") or "").startswith("recorded: ") and o.get("tapOn") == "1", True, )
        check("darpan: no 10-digit run on the page", bool(TEN.search(o.get("text") or "")), False)
        con = sqlite3.connect(db)
        a = con.execute("SELECT diff_id, reason, answered_by FROM stock_diff_answer ORDER BY id DESC LIMIT 1").fetchone()
        con.close()
        check("darpan: the answer landed in stock_diff_answer under his name",
              (a[0], a[1], a[2]) if a else None, (ids[1], "not_billed", "darpan"))
        o2 = render("darpan")
        check("darpan: reloading shows his reason as text and the button lit",
              any("staff's reason:" in l and "darpan" in l for l in o2.get("recLines", [])))

        # CHECKER (the owner): the eight cause buttons + note, the staff answer as text; taps one
        o = render("manoj", "cause")
        check("manoj: page 200, no JS error", (o.get("status"), o.get("jsErrors")), (200, []))
        check("manoj: 8 cause buttons per card (24), ZERO reason buttons",
              (o.get("causeButtons"), o.get("answerButtons")), (3 * N_CAUSES, 0))
        check("manoj: a note box per card", o.get("inputs"), 3)
        check("manoj: the sub-line is the checker's", "UNEXPLAINED is an honest answer" in (o.get("sub") or ""))
        check("manoj: he sees Darpan's reason as text",
              any("staff's reason:" in l and "darpan" in l for l in o.get("recLines", [])))
        check("manoj: tapping a cause is recorded on the page",
              (o.get("tapDone"), o.get("tapOn")), ("recorded: broken or damaged", "1"))
        check("manoj: no 10-digit run on the page", bool(TEN.search(o.get("text") or "")), False)
        con = sqlite3.connect(db)
        r = con.execute("SELECT cause, cause_note, cause_by FROM stock_diff WHERE id=?", (ids[0],)).fetchone()
        con.close()
        check("manoj: the cause and note landed in stock_diff under his name",
              tuple(r), ("BREAKAGE", "dropped the strip", "manoj"))
        o3 = render("amir")
        check("amir: now reads the owner's cause and Darpan's reason as text",
              any(l.startswith("cause: broken or damaged") for l in o3.get("recLines", []))
              and any("staff's reason:" in l for l in o3.get("recLines", [])))

        # ---- the server's own refusals, unchanged (the page is the courtesy)
        for who in ("darpan", "amir"):
            s = cl.post("/finance/stock/api/diff/%d/cause" % ids[2], headers=H(who),
                        json=dict(cause="THEFT")).status_code
            check("server still refuses %s on /cause (403)" % who, s, 403)
            s = cl.post("/finance/stock/api/diff/%d/decision" % ids[2], headers=H(who),
                        json=dict(decision="WRITE_OFF")).status_code
            check("server still refuses %s on /decision (403)" % who, s, 403)
        s = cl.post("/finance/stock/api/diff/%d/cause" % ids[2], headers=H("manoj"),
                    json=dict(cause="THEFT")).status_code
        check("server accepts the owner on /cause (200)", s, 200)
        s = cl.get("/finance/stock/page/diffs", headers=H("nobody")).status_code
        check("an unknown login gets 403 on the page", s, 403)

        # ---- the shipped files carry no 10-digit run
        for f in ("stock_app.py", "stock_diffs.html"):
            t = open(os.path.join(HERE, f), encoding="utf-8").read()
            check("%s: no 10-digit run in the file" % f, bool(TEN.search(t)), False)
            check("%s: LF line endings" % f, "\r" in t, False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n%d PASS  %d FAIL" % (N["pass"], N["fail"]))
    return 0 if N["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
