#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s739_page.py -- S739_DESK_YUVIKA_LISTED: the desk PAGE in a real Chromium, served by the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given sorting_desk.py (the kit's TO -- or the live FROM for the control), on a COPY of a database (SQLite's backup
API). Made-up rows only: papers stamped Z-2031-9*, suppliers 'WALK739 ...', a made-up owner login. The reader is off; nothing is
sent. The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s732_app.py --live <the app folder> --files <folder holding sorting_desk.py> [--db <assets.db>] [--expect-red]
"""
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


LIVE, FILES, SRC = opt("--live", "/root/assetapp"), opt("--files"), opt("--db")
EXPECT_RED = "--expect-red" in ARGS
KIT_FILES = ("sorting_desk.py",)
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
MUST_RED = ("P1", "P2", "P3", "P4", "P5", "P6", "P7")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s739page_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):                                   # the app's CODE only (top-level .py / .js / .json) -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in KIT_FILES:
            p = os.path.join(FILES, f)
            if os.path.isfile(p):
                shutil.copy(p, os.path.join(app, f))
        db = os.path.join(work, "assets.db")
        if SRC:
            s = sqlite3.connect("file:%s?mode=ro" % SRC, uri=True)
            d = sqlite3.connect(db)
            s.backup(d)
            d.close()
            s.close()
        os.makedirs(os.path.join(work, "uploads"))
        os.makedirs(os.path.join(work, "key"))
        open(os.path.join(work, "key", "anthropic.key"), "w").write("made-up-walk-key\n")
        env = dict(os.environ, ASSETS_DB=db, ASSETS_UPLOADS=os.path.join(work, "uploads"), SHARED_LIB_DIR=os.path.join(work, "noshared"),
                   SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"), SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1",
                   CLINIC_PORTAL_DIR=os.path.join(work, "noportal"), FINANCE_LOCAL_URL="http://127.0.0.1:9",
                   FINANCE_DB_FOR_SCANS=os.path.join(work, "nofinance.db"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=400)
        sys.stdout.write(r.stdout)
        for l in r.stderr.splitlines():
            if "NOT mounted" in l or "S739" in l or "Traceback" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S739_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
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


import threading                                                     # noqa: E402
from werkzeug.serving import make_server                             # noqa: E402
import asset_register as ar                                          # noqa: E402

sd, st = sys.modules.get("sorting_desk"), sys.modules.get("stationery")
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.yuvika','on')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s739'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s739','Walk owner','owner','x',1)")
VAR = "WALK739 VARIETY STATIONERS"
keys = [k for k in (db.execute("SELECT value FROM settings WHERE key=?", (st.SUPPLIERS_KEY,)).fetchone() or [""])[0].split("|") if k.strip()]
keys.append(sd._key(VAR))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (st.SUPPLIERS_KEY, "|".join(keys)))
if not (db.execute("SELECT value FROM settings WHERE key=?", (st.FLOOR_KEY,)).fetchone() or [""])[0]:
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (st.FLOOR_KEY, "2026-10-26"))
db.commit()


def mk(tag, vendor, sub="", items=(), **cols):
    vals = dict(kind="Consumable", vendor=vendor, stamp_no="Z-2031-9" + tag, status="draft", lane="clinic", created_at="2031-05-10 05:00:00",
                submitted_at="2031-05-10 05:00", submitted_by="walkscan", doc_kind="challan", bill_no="", bill_date="2031-05-10", total_amount=None,
                subgroup=sub, ocr_status="read")
    vals.update(cols)
    bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
    for n, q in items:
        db.execute("INSERT INTO bill_items(bill_id, item_name, quantity) VALUES(?,?,?)", (bid, n, q))
    db.commit()
    return bid


LINES = (("WALK739 A4 PAPER RIM", 2),)
mk("V0", VAR, items=LINES, created_at="2031-05-01 05:00:00")       # a second Variety paper, so the supplier list carries it
V1 = mk("V1", VAR, items=LINES)
M1 = mk("M1", "WALK739 VARITY STATNRS", items=LINES)
M2 = mk("M2", "WALK739 VARITY STATNRS", items=LINES)
Y1 = mk("Y1", "WALK739 YUVIKA SURGICALS", doc_kind="", items=(("WALK739 GLOSTER 5 INCH", 4),))
Y2 = mk("Y2", "WALK739 YUVIKA SURGICALS", doc_kind="bill", bill_no="YS/W739/1", total_amount=1380, items=(("WALK739 SHOULDER IMMOBILIZER", 2),))
Y3 = mk("Y3", "WALK739 YUVIKA SURGICALS", doc_kind="")
OT = mk("OT", "WALK739 JASORIA BROTHERS", items=LINES)
uid = db.execute("SELECT id FROM users WHERE username='walk_own_s739'").fetchone()[0]
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
cookie = ar.app.session_interface.get_signing_serializer(ar.app).dumps({"uid": uid, "epoch": epoch})
srv = make_server("127.0.0.1", 0, ar.app, threaded=True)
port = srv.server_port
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d" % port

from playwright.sync_api import sync_playwright                     # noqa: E402

with sync_playwright() as pw:
    br = pw.chromium.launch()
    for W in (1366, 390):
        ctx = br.new_context(viewport={"width": W, "height": 900})
        ctx.add_cookies([{"name": ar.app.config.get("SESSION_COOKIE_NAME", "session"), "value": cookie, "url": BASE}])
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        sfx = "" if W == 1366 else "w"

        def opn(stamp):
            pg.goto(BASE + "/desk?open=" + stamp)
            pg.wait_for_function("document.getElementById('hstamp').textContent.indexOf('%s')>=0" % stamp, timeout=10000)
            pg.wait_for_timeout(400)

        def on(dest):
            return pg.evaluate("(function(){var b=document.querySelector('#groups .d[data-d=\"%s\"]');return !!(b&&b.className.indexOf(' on')>=0);})()" % dest)

        opn("Z-2031-9V1")
        c1 = pg.evaluate("(function(){var b=document.getElementById('s739');return b?[getComputedStyle(b).display,b.textContent,(b.querySelector('a.go739')||{}).href||'',"
                         "document.getElementById('save').disabled,document.getElementById('save').textContent,"
                         "Array.prototype.every.call(document.querySelectorAll('#groups .d'),function(x){return x.disabled;})]:null;})()")
        ck("P1%s (%dpx) a Variety challan: the card 'sorted on the Stationery page' with its link; Save off; the destinations off" % (sfx, W),
           lambda: c1 and c1[0] == "flex" and "sorted on the Stationery page" in c1[1] and "/stationery" in c1[2] and c1[3] and c1[4] == "Sorted on the Stationery page" and c1[5],
           lambda: c1)
        opn("Z-2031-9M1" if W == 1366 else "Z-2031-9M2")
        pg.evaluate("document.getElementById('readbox').open=true")
        pg.fill("#f_vendor", "WALK739 VARI")
        pg.wait_for_timeout(500)
        opt = pg.locator("#sup715 .o715", has_text=VAR)
        picked = False
        if opt.count():
            opt.first.dispatch_event("mousedown")
            picked = True
        pg.wait_for_timeout(400)
        c2 = pg.evaluate("(function(){var b=document.getElementById('s739');if(!b){return ['none','',true,''];}return [getComputedStyle(b).display,b.textContent,document.getElementById('save').disabled,document.getElementById('save').textContent];})()")
        ck("P2%s a misread supplier picked as Variety: 'Save sends it to the Stationery page', Save on" % sfx,
           lambda: picked and c2[0] == "flex" and "Save sends it to the Stationery page" in c2[1] and not c2[2] and "send it to the Stationery page" in c2[3], lambda: (picked, c2))
        if W == 1366:
            try:
                pg.click("#save", timeout=3000)
            except Exception:                                    # noqa: BLE001
                pass
            pg.wait_for_timeout(1200)
            r = sqlite3.connect(dbp).execute("SELECT vendor, subgroup FROM bills WHERE id=?", (M1,)).fetchone()
            note = pg.inner_text("#savednote")
            ck("P3 its Save files it under Variety in Stationery & packaging and says: sort its lines on the Stationery page",
               lambda: r == (VAR, "stationery") and "sort its lines on the Stationery page" in note, lambda: (r, note))
        opn("Z-2031-9Y1")
        ck("P4%s Yuvika's handwritten slip opens with Procedure room chosen and its lines panel shown" % sfx,
           lambda: on("procedure") and pg.evaluate("getComputedStyle(document.getElementById('pr634')).display") != "none"
           and "handwritten slip" in pg.inner_text("#destnote"), lambda: (on("procedure"), pg.inner_text("#destnote")))
        opn("Z-2031-9Y2")
        ck("P5%s her printed bill opens with Pharmacy (Sanjeevni) chosen" % sfx, lambda: on("pharmacy") and "printed bill" in pg.inner_text("#destnote"),
           lambda: (on("pharmacy"), pg.inner_text("#destnote")))
        opn("Z-2031-9Y3")
        n2 = pg.locator("#s739 [data-s739]").count()
        if n2:
            pg.click("#s739 [data-s739=slip]")
            pg.wait_for_timeout(300)
        ck("P6%s lines not read: two buttons; 'Handwritten slip' chooses Procedure room and Estimate slip, the card goes" % sfx,
           lambda: n2 == 2 and on("procedure") and pg.evaluate("document.querySelector('#kinds .b.on')&&document.querySelector('#kinds .b.on').getAttribute('data-k')") == "estimate"
           and pg.evaluate("(function(){var b=document.getElementById('s739');return b?getComputedStyle(b).display:'none';})()") == "none", lambda: n2)
        ck("P7%s no horizontal scroll of the page at this width" % sfx,
           lambda: pg.evaluate("document.documentElement.scrollWidth<=window.innerWidth+1") or W == 1366)
        opn("Z-2031-9OT")
        ck("K1%s any other supplier: no card, the destinations on" % sfx,
           lambda: pg.evaluate("(function(){var b=document.getElementById('s739');return b?getComputedStyle(b).display:'none';})()") == "none"
           and not pg.evaluate("Array.prototype.some.call(document.querySelectorAll('#groups .d'),function(x){return x.disabled;})"))
        ck("K2%s no script error on the page" % sfx, lambda: not errs, lambda: errs)
        ctx.close()
    br.close()
srv.shutdown()
db.close()

MUST = [k for k in RES if k[:2] in ("P1", "P2", "P3", "P4", "P5", "P6")]
if EXPECT_RED:
    red = [k for k in MUST if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S739 page checks red; K green %d of %d" % (len(red), len(MUST), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("PAGE WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
