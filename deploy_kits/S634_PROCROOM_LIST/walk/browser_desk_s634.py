#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser_desk_s634.py -- S634's desk panel and the owner's page in a real headless Chromium (Playwright), on a scratch copy of the
app with a fresh made-up database: one made-up estimate slip (2031), the owner's and a manager's session cookies made with the app's own
signer, the app served on 127.0.0.1 by werkzeug in a thread. Checks the panel's JavaScript end to end -- choose Procedure room, the
lines appear pre-chosen with their places and NO rate, a quantity is changed and a line added, Save -- then reads the database, and
opens his page at the phone width 390 and at 1280.

    python3 -B browser_desk_s634.py --live <the app folder> --files <folder with the files to test> [--expect-red] [--shots <folder>]
"""
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


LIVE, FILES, SHOTS = opt("--live"), opt("--files"), opt("--shots")
EXPECT_RED = "--expect-red" in ARGS
if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s634br_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in ("sorting_desk.py", "asset_register.py", "procroom.py"):
            if os.path.isfile(os.path.join(FILES, f)):
                shutil.copy(os.path.join(FILES, f), os.path.join(app, f))
            elif os.path.exists(os.path.join(app, f)):
                os.remove(os.path.join(app, f))
        os.makedirs(os.path.join(work, "uploads"))
        env = dict(os.environ, ASSETS_DB=os.path.join(work, "assets.db"), ASSETS_UPLOADS=os.path.join(work, "uploads"),
                   SHARED_LIB_DIR=os.path.join(work, "noshared"), SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "nokey"),
                   SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1", CLINIC_PORTAL_DIR=os.path.join(work, "noportal"),
                   FINANCE_LOCAL_URL="http://127.0.0.1:9", FINANCE_DB_FOR_SCANS=os.path.join(work, "nofinance.db"))
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=300)
        sys.stdout.write(r.stdout)
        if r.returncode not in (0, 1) or os.environ.get("S634_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

APPD = ARGS[ARGS.index("--inner") + 1]
sys.path.insert(0, APPD)
RES = {}


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = "" if ok or detail is None else detail()
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, repr(e)
    RES[name.split(" ")[0]] = ok
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:300]) if (d and not ok) else ""))


import asset_register as ar                                          # noqa: E402
from werkzeug.serving import make_server                             # noqa: E402
from playwright.sync_api import sync_playwright                      # noqa: E402

pr = sys.modules.get("procroom")
db = sqlite3.connect(os.environ["ASSETS_DB"])
db.row_factory = sqlite3.Row
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
for k, v in (("read.claude", "off"), ("desk.on", "on")):
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
for u, role in (("walk_own_s634b", "owner"), ("walk_mgr_s634b", "manager")):
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.commit()
if pr is not None:
    pr.seed_step(os.environ["ASSETS_DB"], out=lambda *_: None)
bid = db.execute("INSERT INTO bills(kind, vendor, stamp_no, status, lane, created_at, submitted_at, submitted_by, doc_kind, bill_date) "
                 "VALUES('Consumable','WALK634 SURGICALS','Z-2031-Q1','draft','clinic','2031-05-10 05:00:00','2031-05-10 05:00','Walk','estimate','2031-05-10')").lastrowid
for it in (('Gloster 5"', 5, 123.0), ("Bandage 13 cm x 4 m", 5, 21.0), ("Thumb spica Urban", 2, 37.0)):      # made-up rates
    db.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?,?,?,?,?)", (bid, it[0], it[1], it[2], it[1] * it[2]))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
ser = ar.app.session_interface.get_signing_serializer(ar.app)
cookie_name = ar.app.config.get("SESSION_COOKIE_NAME", "session")


def cookie(user):
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    return ser.dumps({"uid": uid, "epoch": epoch})


srv = make_server("127.0.0.1", 0, ar.app, threaded=True)
port = srv.server_port
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = "http://127.0.0.1:%d" % port
errs = []
with sync_playwright() as p:
    exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
    try:
        br = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    except Exception:                                                # noqa: BLE001
        br = p.chromium.launch()
    for who, user in (("manager", "walk_mgr_s634b"),):
        ctx = br.new_context(viewport={"width": 1366, "height": 900})
        ctx.add_cookies([{"name": cookie_name, "value": cookie(user), "url": base}])
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(base + "/desk?open=%d" % bid)
        pg.wait_for_timeout(1500)
        btn = pg.locator('button.d[data-d="procedure"]')
        ok_btn = btn.count() == 1
        if ok_btn:
            btn.click()
            pg.wait_for_timeout(500)
        box = pg.locator("#pr634")
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True)
            pg.screenshot(path=os.path.join(SHOTS, "desk_procroom_1366.png"), full_page=True)
        vis = box.count() == 1 and box.is_visible()
        html = box.inner_html() if box.count() else ""
        sel = [pg.locator('[data-pri="%d"]' % i).input_value() if pg.locator('[data-pri="%d"]' % i).count() else "" for i in range(3)]
        plc = [pg.locator('[data-prp="%d"]' % i).input_value() if pg.locator('[data-prp="%d"]' % i).count() else "" for i in range(3)]
        F5 = db.execute("SELECT id FROM proc_item WHERE name='Fibrecast bandage 5\"'").fetchone() if pr else None
        ck("K1 the manager's desk: Procedure room chosen, the panel shows three lines -- Fibrecast 5\" pre-chosen, the spica at Sanjeevni -- and no rupee, no rate",
           lambda: ok_btn and vis and F5 is not None and sel[0] == str(F5[0]) and plc[2] == "sanj" and "₹" not in html and "123" not in html and "+ Add to the list" not in html,
           lambda: (ok_btn, vis, sel, plc, html[:200]))
        if vis:
            pg.fill('[data-prq="0"]', "4")
            pg.click("[data-pradd]")
            pg.wait_for_timeout(300)
            if pg.locator('[data-prn="3"]').count():
                pg.fill('[data-prn="3"]', "WALK634 cool pack")
                pg.fill('[data-prq="3"]', "1")
                pg.select_option('[data-pri="3"]', "free")
                pg.select_option('[data-prp="3"]', "home")
            pg.wait_for_timeout(200)
            sv = pg.locator("#save")
            if sv.is_enabled():
                sv.click()
            pg.wait_for_timeout(1500)
        try:
            rows = [dict(r) for r in db.execute("SELECT line_no, name, qty, place, item_id FROM proc_line WHERE bill_id=? AND voided_at='' ORDER BY line_no", (bid,))]
        except sqlite3.Error:
            rows = []
        ck("K2 one Save from the browser: four lines stored -- 4 Fibrecast 5\" (changed from 5), the bandage, the spica at Sanjeevni, a cool pack for home use",
           lambda: len(rows) == 4 and rows[0]["qty"] == 4 and rows[2]["place"] == "sanj" and rows[3]["place"] == "home" and rows[3]["name"] == "WALK634 cool pack",
           lambda: rows)
        ctx.close()
    for w in (390, 1280):
        ctx = br.new_context(viewport={"width": w, "height": 900})
        ctx.add_cookies([{"name": cookie_name, "value": cookie("walk_own_s634b"), "url": base}])
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        r = pg.goto(base + "/procroom?ym=2031-05")
        pg.wait_for_timeout(500)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        wide = pg.evaluate("""(w)=>{var o=[];document.querySelectorAll('body *').forEach(function(e){var r=e.getBoundingClientRect(),q=e.parentElement,inb=false;while(q){var ov=getComputedStyle(q).overflowX;if(ov=='auto'||ov=='scroll'){inb=true;break;}q=q.parentElement;}if(!inb&&r.right>w+1&&e.children.length<6){o.push(e.tagName+'#'+(e.id||'')+'.'+(e.className||'')+' '+Math.round(r.right)+' '+(e.textContent||'').slice(0,30));}});return o.slice(0,8);}""", w)
        t = pg.locator("body").inner_text() if r and r.ok else ""
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True)
            pg.screenshot(path=os.path.join(SHOTS, "procroom_%d.png" % w), full_page=True)
        ck("K3%s his page at %d px: answers, shows the slip and the cool pack kept elsewhere, and the page itself does not scroll sideways (%s px)" % ("a" if w == 390 else "b", w, sw),
           lambda: bool(r and r.ok) and "Fibrecast bandage 5" in t and "WALK634 cool pack" in t and sw <= w + 1, lambda: (r.status if r else None, sw, wide))
        ctx.close()
    br.close()
srv.shutdown()
ck("K4 no script error on any page", lambda: not errs, lambda: errs[:3])
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in ("K1", "K2", "K3a", "K3b") if RES.get(k, True)]
    print("BROWSER S634 CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("BROWSER S634: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
