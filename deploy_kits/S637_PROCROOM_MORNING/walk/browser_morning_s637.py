#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser_morning_s637.py -- S637's morning screen ("Kal ke procedures") and his page's new sections in a real headless Chromium
(Playwright), on a scratch copy of the app with a fresh made-up database and a MADE-UP slip book (finance) database: a manager (Shavez)
fills yesterday's cast slip at 390 px (a phone) and at 1366 px and presses Save once; his page at 390 px. Not run on the box.

    python3 -B browser_morning_s637.py --live <the app folder> --files <folder with the files to test> [--expect-red] [--shots <folder>]
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
    work = tempfile.mkdtemp(prefix="s637br_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in ("procroom.py",):
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
        if r.returncode not in (0, 1) or os.environ.get("S637_WALK_DEBUG"):
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
for k, v in (("read.claude", "off"), ("desk.on", "on"), ("proc.morning", "on")):
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
for u, role in (("walk_own_s637b", "owner"), ("walk_mgr_s637b", "manager")):
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.commit()
if pr is not None:
    pr.seed_step(os.environ["ASSETS_DB"], out=lambda *_: None)
    import datetime as _d
    pr.TODAY = _d.date(2031, 5, 20)
f = sqlite3.connect(os.environ["FINANCE_DB_FOR_SCANS"])
f.executescript("""
CREATE TABLE slip(id INTEGER PRIMARY KEY, series TEXT, slip_no INTEGER, day TEXT, clinic_id TEXT DEFAULT '', no_id_name TEXT DEFAULT '', state TEXT DEFAULT 'ok');
CREATE TABLE slip_item(id INTEGER PRIMARY KEY, slip_id INTEGER, kind TEXT, service_id INTEGER, name TEXT DEFAULT '', side TEXT DEFAULT '', price_p INTEGER DEFAULT 0, sort INTEGER DEFAULT 0);
CREATE TABLE clinic_day_line(business_date TEXT, section TEXT, sn INTEGER, patient TEXT DEFAULT '', clinic_id TEXT DEFAULT '', amount_p INTEGER DEFAULT 0, mode TEXT DEFAULT '');
CREATE TABLE clinic_day_revenue(business_date TEXT PRIMARY KEY, taken_at TEXT);
CREATE TABLE owner_service(id INTEGER PRIMARY KEY, kind TEXT, name TEXT, price_p INTEGER DEFAULT 0, active INTEGER DEFAULT 1, grp TEXT DEFAULT '', status TEXT DEFAULT 'approved');
CREATE TABLE owner_service_item(id INTEGER PRIMARY KEY, service_id INTEGER, item TEXT, qty REAL DEFAULT 1, unit TEXT DEFAULT '', ask TEXT DEFAULT '', sizes TEXT DEFAULT '', note TEXT DEFAULT '');
CREATE TABLE patient_ref(id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT DEFAULT '', merged_into TEXT);
INSERT INTO owner_service(id, kind, name, grp) VALUES (1,'proc','B/K (Below knee) fibre cast','Cast / slab');
INSERT INTO owner_service_item(service_id, item, ask, sizes) VALUES (1,'Cast padding','size_qty','4",6"'), (1,'Fibrecast bandage','size_qty','2",3",4",5"'), (1,'Roller bandage','size_qty','4",6"'), (1,'Stockinette','used_yesno','');
INSERT INTO slip(id, series, slip_no, day, clinic_id) VALUES (901,'xp',9187,'2031-05-19','W99004821');
INSERT INTO slip_item(slip_id, kind, service_id, name, side) VALUES (901,'proc',1,'B/K (Below knee) fibre cast','R');
INSERT INTO clinic_day_revenue VALUES ('2031-05-19','2031-05-19 23:00');
INSERT INTO clinic_day_line(business_date, section, sn, patient, clinic_id) VALUES ('2031-05-19','proc',1,'WALKPATIENT ONE','W99004821');
""")
f.commit()
f.close()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
ser = ar.app.session_interface.get_signing_serializer(ar.app)
cookie_name = ar.app.config.get("SESSION_COOKIE_NAME", "session")


def cookie(user):
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    return ser.dumps({"uid": uid, "epoch": epoch})


def used():
    try:
        return sorted((r[0], r[1]) for r in db.execute("SELECT name, qty FROM proc_use WHERE voided_at='' AND src='kit'"))
    except sqlite3.Error:
        return []


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
    for w in (390, 1366):
        ctx = br.new_context(viewport={"width": w, "height": 900})
        ctx.add_cookies([{"name": cookie_name, "value": cookie("walk_mgr_s637b"), "url": base}])
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        r = pg.goto(base + "/procroom/morning")
        pg.wait_for_timeout(400)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        t = pg.locator("body").inner_text() if r and r.ok else ""
        sels = pg.locator('[data-slip="9187"] select')
        n = sels.count()
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True)
            pg.screenshot(path=os.path.join(SHOTS, "morning_%d.png" % w), full_page=True)
        if w == 390:
            ok_ = n >= 3
            if ok_:
                sels.nth(1).select_option('4"')
                pg.locator('[data-slip="9187"] input.q').nth(1).fill("3")
                pg.locator('[data-slip="9187"] input[type=checkbox]').first.check()
                pg.click("#s637 form button.btn")
                pg.wait_for_timeout(1200)
            t2 = pg.locator("body").inner_text()
            ck("M1 Shavez at 390 px (a phone): the cast slip with its kit, sizes to choose, no sideways scroll (%s px); one Save stores 3 Fibrecast 4\" and the stockinette" % sw,
               lambda: bool(r and r.ok) and "Kal ke procedures" in t and ok_ and sw <= w + 1 and "Save ho gaya" in t2
               and ("Fibrecast bandage", 3) in used() and ("Stockinette", 1) in used(), lambda: (sw, n, used(), t2[:200]))
        else:
            ck("M2 at 1366 px the same slip opens saved (“Save ho chuka”) with the count kept, no sideways scroll", lambda: "Save ho chuka" in t and sw <= w + 1, lambda: (sw, t[:300]))
        ctx.close()
    ctx = br.new_context(viewport={"width": 390, "height": 900})
    ctx.add_cookies([{"name": cookie_name, "value": cookie("walk_own_s637b"), "url": base}])
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    r = pg.goto(base + "/procroom?ym=2031-05")
    pg.wait_for_timeout(400)
    sw = pg.evaluate("document.documentElement.scrollWidth")
    t = pg.locator("body").inner_text() if r and r.ok else ""
    if SHOTS:
        pg.screenshot(path=os.path.join(SHOTS, "procroom_owner_390.png"), full_page=True)
    ck("M3 his page at 390 px: the morning screen's card (on), Used and in stock, the month-end match; no sideways scroll (%s px)" % sw,
       lambda: bool(r and r.ok) and "Shavez's next-morning screen" in t and "Used and in stock" in t and "Month-end match" in t and sw <= 391, lambda: (sw, t[:300]))
    ctx.close()
    br.close()
srv.shutdown()
ck("M4 no script error on any page", lambda: not errs, lambda: errs[:3])
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in ("M1", "M2", "M3") if RES.get(k, True)]
    print("BROWSER S637 CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("BROWSER S637: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
