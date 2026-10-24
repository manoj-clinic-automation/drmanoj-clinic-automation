#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser_desk_s635.py -- S635's desk panel (his order; a slip against it) and the month-end page in a real headless Chromium
(Playwright), on a scratch copy of the app with a fresh made-up database: made-up papers of 2031, the owner's and a manager's session
cookies made with the app's own signer, the app served on 127.0.0.1 by werkzeug in a thread. The panel's JavaScript end to end -- mark
a paper as his order with its book page, Save; a slip nothing was read from is pre-joined and filled from the order, a quantity
corrected, Save; another slip's lines replaced by "Fill the lines from this order" -- then the database is read; the month end at the
phone width 390 and at 1280, a made-up photo added through its own form. Not run on the box.

    python3 -B browser_desk_s635.py --live <the app folder> --files <folder with the files to test> [--expect-red] [--shots <folder>]
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
    work = tempfile.mkdtemp(prefix="s635br_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in ("sorting_desk.py", "procroom.py"):
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
        if r.returncode not in (0, 1) or os.environ.get("S635_WALK_DEBUG"):
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
for u, role in (("walk_own_s635b", "owner"), ("walk_mgr_s635b", "manager")):
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.commit()
if pr is not None:
    pr.seed_step(os.environ["ASSETS_DB"], out=lambda *_: None)
    if hasattr(pr, "floor_step"):
        pr.floor_step(os.environ["ASSETS_DB"], out=lambda *_: None)
    if hasattr(pr, "NO_THREAD"):
        pr.NO_THREAD = True


def mk(tag, items, created):
    b = db.execute("INSERT INTO bills(kind, vendor, stamp_no, status, lane, created_at, submitted_at, submitted_by, doc_kind, bill_date) "
                   "VALUES('Consumable','WALK635 YUVIKA SURGICALS',?,'draft','clinic',?,?,'Walk','estimate',?)",
                   ("Z-2031-" + tag, created, created[:16], created[:10])).lastrowid
    for it in items:
        db.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?,?,?,?,?)", (b, it[0], it[1], it[2], it[1] * it[2]))
    db.commit()
    return b


O = mk("O1", (('Gloster 5"', 6, 0.0), ("Bandage 13 cm x 4 m", 12, 0.0)), "2031-05-03 05:00:00")
D = mk("D1", (), "2031-05-06 05:00:00")
D2 = mk("D2", (('Gloster 4"', 2, 77.0),), "2031-05-07 05:00:00")          # a made-up printed rate
F5 = db.execute("SELECT id FROM proc_item WHERE name='Fibrecast bandage 5\"'").fetchone()
R6 = db.execute("SELECT id FROM proc_item WHERE name='Roller bandage 6\"'").fetchone()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
ser = ar.app.session_interface.get_signing_serializer(ar.app)
cookie_name = ar.app.config.get("SESSION_COOKIE_NAME", "session")


def cookie(user):
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    return ser.dumps({"uid": uid, "epoch": epoch})


def role(bid):
    try:
        r = db.execute("SELECT role, order_bill_id, book_no FROM proc_paper WHERE bill_id=? AND voided_at=''", (bid,)).fetchone()
    except sqlite3.Error:
        return None
    return tuple(r) if r else None


def lines(bid):
    try:
        return [(r[0], r[1]) for r in db.execute("SELECT item_id, qty FROM proc_line WHERE bill_id=? AND voided_at='' ORDER BY line_no", (bid,))]
    except sqlite3.Error:
        return []


srv = make_server("127.0.0.1", 0, ar.app, threaded=True)
port = srv.server_port
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = "http://127.0.0.1:%d" % port
errs = []


def open_desk(ctx, bid):
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(base + "/desk?open=%d" % bid)
    pg.wait_for_timeout(1500)
    btn = pg.locator('button.d[data-d="procedure"]')
    if btn.count() == 1:
        btn.click()
        pg.wait_for_timeout(500)
    return pg


def save(pg):
    sv = pg.locator("#save")
    if sv.count() and sv.is_enabled():
        sv.click()
    pg.wait_for_timeout(1500)


with sync_playwright() as p:
    exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
    try:
        br = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
    except Exception:                                                # noqa: BLE001
        br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 1366, "height": 900})
    ctx.add_cookies([{"name": cookie_name, "value": cookie("walk_mgr_s635b"), "url": base}])
    pg = open_desk(ctx, O)
    radio = pg.locator('input[data-prr][value="order"]')
    has = radio.count() == 1
    if has:
        radio.check()
        pg.wait_for_timeout(300)
        if pg.locator("[data-prbk]").count():
            pg.fill("[data-prbk]", "24")
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        pg.screenshot(path=os.path.join(SHOTS, "desk_order_1366.png"), full_page=True)
    save(pg)
    ck("B1 the manager marks a paper as Dr Manoj's order (book page 24) in the panel and saves: kept as his order, its two lines kept", lambda: has and role(O) == ("order", None, "24") and len(lines(O)) == 2,
       lambda: (has, role(O), lines(O)))
    pg.close()
    pg = open_desk(ctx, D)
    box = pg.locator("#pr634")
    html = box.inner_html() if box.count() else ""
    osel = pg.locator("[data-pro]").input_value() if pg.locator("[data-pro]").count() else ""
    sel = [pg.locator('[data-pri="%d"]' % i).input_value() if pg.locator('[data-pri="%d"]' % i).count() else "" for i in range(2)]
    qty = [pg.locator('[data-prq="%d"]' % i).input_value() if pg.locator('[data-prq="%d"]' % i).count() else "" for i in range(2)]
    if SHOTS:
        pg.screenshot(path=os.path.join(SHOTS, "desk_slip_1366.png"), full_page=True)
    ck("B2 a slip nothing was read from: “Against order” shows Z-2031-O1 chosen and its lines are filled from the order (6 Fibrecast 5\", 12 Roller 6\") -- no rupee, no rate",
       lambda: osel == str(O) and F5 and sel[0] == str(F5[0]) and R6 and sel[1] == str(R6[0]) and qty == ["6", "12"] and "₹" not in html and "filled from the order" in html,
       lambda: (osel, sel, qty, html[:300]))
    if pg.locator('[data-prq="1"]').count():
        pg.fill('[data-prq="1"]', "10")
    save(pg)
    ck("B3 Shavez corrects the Roller to 10 and saves: the slip joined to the order, its lines 6 and 10", lambda: role(D) == ("slip", O, "") and [q for _, q in lines(D)] == [6, 10],
       lambda: (role(D), lines(D)))
    pg.close()
    pg = open_desk(ctx, D2)
    if pg.locator("[data-pro]").count():
        pg.select_option("[data-pro]", str(O))
        pg.wait_for_timeout(300)
    link = pg.locator("[data-prfill]")
    hl = link.count() == 1
    if hl:
        link.click()
        pg.wait_for_timeout(300)
    sel2 = [pg.locator('[data-pri="%d"]' % i).input_value() if pg.locator('[data-pri="%d"]' % i).count() else "" for i in range(3)]
    html2 = pg.locator("#pr634").inner_html() if pg.locator("#pr634").count() else ""
    ck("B4 another slip: its order chosen by hand, “Fill the lines from this order” replaces its read line with the order's two (nothing saved yet), and the slip's printed ₹77 is nowhere in the panel",
       lambda: hl and F5 and R6 and sel2[:2] == [str(F5[0]), str(R6[0])] and sel2[2] == "" and "77" not in html2 and lines(D2) == [], lambda: (hl, sel2, lines(D2)))
    pg.close()
    ctx.close()
    for w in (390, 1280):
        ctx = br.new_context(viewport={"width": w, "height": 900})
        ctx.add_cookies([{"name": cookie_name, "value": cookie("walk_own_s635b"), "url": base}])
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        r = pg.goto(base + "/procroom/month?ym=2031-05")
        pg.wait_for_timeout(400)
        added = False
        if r and r.ok and w == 390 and pg.locator('#s635add input[type=file]').count():
            pg.set_input_files('#s635add input[type=file]', files=[{"name": "wa-walk.jpg", "mimeType": "image/jpeg", "buffer": b"\xff\xd8\xff\xe0WALK635-browser" + os.urandom(32)}])
            pg.click("#s635add button")
            pg.wait_for_timeout(800)
            added = "1 photo added" in pg.locator("body").inner_text()
        if w == 1280:
            ph = pg.locator("#s635tab a").first
            if ph.count():
                ph.click()
                pg.wait_for_timeout(500)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        t = pg.locator("body").inner_text() if r and r.ok else ""
        if SHOTS:
            pg.screenshot(path=os.path.join(SHOTS, "month_%d.png" % w), full_page=True)
        if w == 390:
            ck("B5a the month end at 390 px: answers, a made-up photo added through its own form (kept; the reader off says so), no sideways scroll (%s px)" % sw,
               lambda: bool(r and r.ok) and added and "To pay Yuvika for May 2031" in t and sw <= w + 1, lambda: (r.status if r else None, added, sw, t[:200]))
        else:
            ck("B5b the month end at 1280 px: the photo opened -- its lines box, the scan to choose, Save (%s px wide)" % sw,
               lambda: bool(r and r.ok) and "the lines" in t and "Its scan" in t and sw <= w + 1, lambda: (sw, t[:300]))
        ctx.close()
    br.close()
srv.shutdown()
ck("B6 no script error on any page", lambda: not errs, lambda: errs[:3])
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in ("B1", "B2", "B3", "B4", "B5a", "B5b") if RES.get(k, True)]
    print("BROWSER S635 CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("BROWSER S635: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
