#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s741_page.py -- S741_STATIONERY_PRODUCT_PICK: the Stationery pages in a real Chromium, served by the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given sorting_desk.py (the kit's TO -- or the live FROM for the control), on a COPY of a database (SQLite's backup
API). Made-up rows only: papers stamped Z-2031-7*, suppliers 'WALK741 ...', a made-up owner login. The reader is off; nothing is
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
KIT_FILES = ("stationery.py",)
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
MUST_RED = ("A0", "P1", "P2", "P3", "P4")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s741page_")
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
            if "NOT mounted" in l or "S741" in l or "Traceback" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S741_WALK_DEBUG"):
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
ck("A0 the real app loads; stationery.py is S741's", lambda: st is not None and getattr(st, "PICK_S741", "") == "S741")
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s741'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s741','Walk owner','owner','x',1)")
VAR = "WALK741 VARIETY STATIONERS"
keys = [k for k in (db.execute("SELECT value FROM settings WHERE key=?", (st.SUPPLIERS_KEY,)).fetchone() or [""])[0].split("|") if k.strip()]
keys.append(sd._key(VAR))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (st.SUPPLIERS_KEY, "|".join(keys)))
if not (db.execute("SELECT value FROM settings WHERE key=?", (st.FLOOR_KEY,)).fetchone() or [""])[0]:
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (st.FLOOR_KEY, "2026-10-26"))
for nm, un in (("WALK741 A4 PAPER 75 GSM", "ream"), ("WALK741 A4 PAPER 70 GSM", "ream"), ("WALK741 STAPLER PIN 24/6", "box")):
    st.add_item(db, nm, un, None, None, "walk")
vals = dict(kind="Consumable", vendor=VAR, stamp_no="Z-2031-7P1", status="draft", lane="clinic", created_at="2031-05-10 05:00:00",
            submitted_at="2031-05-10 05:00", submitted_by="walkscan", doc_kind="challan", bill_no="W741", bill_date="2031-05-10", subgroup="", ocr_status="read")
P1 = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
db.execute("INSERT INTO bill_items(bill_id, item_name, quantity) VALUES(?,?,?)", (P1, "WALK741 PAPER RIM", 2))
vals.update(stamp_no="Z-2031-7P2", bill_no="W741B")
P2 = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
db.execute("INSERT INTO bill_items(bill_id, item_name, quantity) VALUES(?,?,?)", (P2, "WALK741 PAPER RIM", 3))
db.commit()
uid = db.execute("SELECT id FROM users WHERE username='walk_own_s741'").fetchone()[0]
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
        pg.set_default_timeout(6000)
        FORM = "form[data-paper='%d']" % (P1 if W == 1366 else P2)
        pg.goto(BASE + "/stationery")
        pg.wait_for_timeout(600)
        inp = FORM + " input[name=n1]"
        ck("K5%s the item list's own unit boxes (outside the sorting form) are left as they were" % sfx,
           lambda: pg.evaluate("(function(){var a=document.querySelectorAll('input[list=s568units]');return a.length>0&&!document.querySelector('form:not(.s674) .pk741');})()"))
        ck("P1%s (%dpx) the product box is a searchable list (no browser datalist)" % (sfx, W),
           lambda: pg.evaluate("(function(){var i=document.querySelector(\"%s\");return !!(i&&!i.getAttribute('list')&&i.parentNode.className.indexOf('pk741')>=0);})()" % inp))
        try:
            pg.focus(inp)
            pg.fill(inp, "a4 paper")
            pg.wait_for_timeout(300)
            opts = pg.evaluate("Array.prototype.map.call(document.querySelectorAll(\"%s\"),function(b){return b.textContent;})" % (FORM + " .dd741 [data-v]"))
            pg.dispatch_event(FORM + " .dd741 [data-v] >> nth=0", "mousedown")
            pg.wait_for_timeout(200)
            val = pg.input_value(inp)
        except Exception as e:                                       # noqa: BLE001
            opts, val = [], repr(e)[:120]
        ck("P2%s typing 'a4 paper' lists both A4 papers; one tap fills the box" % sfx,
           lambda: sorted(opts) == ["WALK741 A4 PAPER 70 GSM", "WALK741 A4 PAPER 75 GSM"] and val in opts, lambda: (opts, val))
        try:
            pg.fill(inp, "WALK741 FILE COVER")
            pg.wait_for_timeout(300)
            nw = pg.inner_text(FORM + " .dd741 .nw")
        except Exception as e:                                       # noqa: BLE001
            nw = repr(e)[:120]
        ck("P3%s a name not on the list says it is added on Save" % sfx, lambda: "is not on the list" in nw and "WALK741 FILE COVER" in nw, lambda: nw)
        try:
            pg.focus(FORM + " input[name=u1]")
            pg.fill(FORM + " input[name=u1]", "re")
            pg.wait_for_timeout(300)
            uo = pg.evaluate("Array.prototype.map.call(document.querySelectorAll(\"%s\"),function(b){return b.textContent;})" % (FORM + " .pk741.u .dd741 [data-v]"))
        except Exception as e:                                       # noqa: BLE001
            uo = [repr(e)[:120]]
        ck("P4%s the unit box is a searchable list too ('re' -> ream)" % sfx, lambda: "ream" in uo, lambda: uo)
        if W == 1366:
            try:
                pg.fill(inp, "WALK741 A4 PAPER 75 GSM")
                pg.fill(FORM + " input[name=q1]", "2")
                pg.fill(FORM + " input[name=u1]", "ream")
                pg.click(FORM + " label:has(input[name=f1][value=clinic])")
                pg.click(FORM + " button.btn")
                pg.wait_for_timeout(1200)
            except Exception as e:                                   # noqa: BLE001
                print("  save: " + repr(e)[:160])
            con = sqlite3.connect(dbp)
            con.row_factory = sqlite3.Row
            bb = con.execute("SELECT * FROM bills WHERE id=?", (P1,)).fetchone()
            ln = [(r["item_id"], r["qty"]) for r in con.execute("SELECT * FROM stationery_line WHERE bill_id=? AND COALESCE(voided_at,'')=''", (P1,))] if bb else []
            con.close()
            ck("K1 the Save of the form records the picked product's line (the server unchanged)", lambda: len(ln) == 1 and ln[0][1] == 2 and ln[0][0] is not None, lambda: ln)
        pg.goto(BASE + "/stationery/sort")
        pg.wait_for_timeout(500)
        ck("K2%s the staff Stationery sort page opens" % sfx, lambda: "Stationery sort" in pg.inner_text("body"))
        ck("K3%s no script error" % sfx, lambda: not errs, lambda: errs)
        ck("K4%s no horizontal scroll of the page" % sfx, lambda: W == 1366 or pg.evaluate("document.documentElement.scrollWidth<=window.innerWidth+1"))
        ctx.close()
    br.close()
srv.shutdown()
db.close()

MUST = [k for k in RES if k[:2] in ("A0", "P1", "P2", "P3", "P4")]
if EXPECT_RED:
    red = [k for k in MUST if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S741 checks red; K green %d of %d" % (len(red), len(MUST), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("PAGE WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
