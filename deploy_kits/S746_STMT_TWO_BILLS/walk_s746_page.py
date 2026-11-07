#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s746_page.py -- S746_STMT_TWO_BILLS on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given sorting_desk.py (the kit's TO -- or the live FROM for the control), on a COPY of a database (SQLite's backup
API). Made-up rows only: papers stamped Z-2031-6*, suppliers 'WALK746 ...', a made-up owner login. The reader is off; nothing is
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
MUST_RED = ("P1", "P2", "P1w", "P2w")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s746page_")
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
            if "NOT mounted" in l or "S746" in l or "Traceback" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S746_WALK_DEBUG"):
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


import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
sd, st = mods.get("sorting_desk"), mods.get("stationery")
ck("A0 the real app loads with its seven parts mounted; stationery.py is S746's", lambda: all(mods.values()) and getattr(st, "STMT_S746", "") == "S746")
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s746'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s746','Walk owner','owner','x',1)")
VAR = "WALK746 VARIETY STATIONERS"
keys = [k for k in (db.execute("SELECT value FROM settings WHERE key=?", (st.SUPPLIERS_KEY,)).fetchone() or [""])[0].split("|") if k.strip()]
key = sd._key(VAR)
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (st.SUPPLIERS_KEY, "|".join([key] + keys)))     # first: the page's own supplier
if not (db.execute("SELECT value FROM settings WHERE key=?", (st.FLOOR_KEY,)).fetchone() or [""])[0]:
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (st.FLOOR_KEY, "2026-10-26"))
st.add_item(db, "WALK746 A4 PAPER", "ream", None, None, "walk")
st.add_item(db, "WALK746 NK PAD", "piece", None, None, "walk")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_own_s746'").fetchone()[0]
    ss["epoch"] = epoch


def paper(tag, kind="challan", lane="clinic", no="", amt=None, status=None):
    vals = dict(kind="Lab" if lane == "lab_purchase" else "Consumable", vendor=VAR, stamp_no="Z-2031-6" + tag, status=status or ("captured" if lane == "lab_purchase" else "draft"),
                lane=lane, created_at="2031-05-10 05:00:00", submitted_at="2031-05-10 05:00", submitted_by="walkscan", doc_kind=kind, bill_no=no or ("W746" + tag),
                bill_date="2031-05-10", total_amount=amt, subgroup="", ocr_status="read")
    bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
    db.commit()
    return bid


def sort(bid, name, qty, unit, side):
    r = own.post("/stationery/sort/save", data={"paper": str(bid), "back": "stock", "n1": name, "q1": str(qty), "u1": unit, "f1": side})
    db.commit()
    return r.status_code


C1, N1 = paper("C1"), paper("N1")
sort(C1, "WALK746 A4 PAPER", 2, "ream", "clinic")
sort(N1, "WALK746 NK PAD", 500, "piece", "nk")
sid, nl = st.stmt_make(db, "2031-05", key, who="walk")
db.commit()
lines = {r["side"]: r["id"] for r in db.execute("SELECT id, side FROM stationery_line WHERE stmt_id=? AND voided_at=''", (sid,))}
BC = paper("BC", kind="bill", no="V-118", amt=1668)                 # their bill for the clinic, on the clinic lane
BN = paper("BN", kind="bill", no="V-119", amt=460)                  # their bill for NK, scanned on the clinic lane by mistake
BL = paper("BL", kind="bill", no="V-120", amt=99, lane="lab_purchase")


def row(t, i):
    return db.execute("SELECT * FROM %s WHERE id=?" % t, (i,)).fetchone()


def stmt():
    return next(s for s in st.stmt_rows(db) if s["id"] == sid)


def state(side):
    return next(l["state"] for l in st.account_rows(db) if l["id"] == lines[side])


r3 = own.post("/stationery/statement/join", data={"id": str(sid), "side": "nk", "bill": str(BN), "r%d" % lines["nk"]: "0.92"})
db.commit()
import threading                                                     # noqa: E402
from werkzeug.serving import make_server                             # noqa: E402
uid = db.execute("SELECT id FROM users WHERE username='walk_own_s746'").fetchone()[0]
cookie = ar.app.session_interface.get_signing_serializer(ar.app).dumps({"uid": uid, "epoch": epoch})
srv = make_server("127.0.0.1", 0, ar.app, threaded=True)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d" % srv.server_port
from playwright.sync_api import sync_playwright                     # noqa: E402
with sync_playwright() as p:
    br = p.chromium.launch()
    for W in (1366, 390):
        ctx = br.new_context(viewport={"width": W, "height": 900})
        ctx.add_cookies([{"name": ar.app.config.get("SESSION_COOKIE_NAME", "session"), "value": cookie, "url": BASE}])
        pg = ctx.new_page()
        pg.set_default_timeout(6000)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        sfx = "" if W == 1366 else "w"
        pg.goto(BASE + "/stationery")
        pg.wait_for_timeout(500)
        g = pg.evaluate("(function(){var c=document.getElementById('s746clinic'),n=document.getElementById('s746nk');if(!c||!n){return null;}var a=c.getBoundingClientRect(),b=n.getBoundingClientRect();"
                        "return {cv:a.width>0,nv:b.width>0,side:Math.abs(a.top-b.top)<5,stack:b.top>=a.bottom-1,ctext:c.innerText,ntext:n.innerText};})()")
        ck("P1%s (%dpx) both bills drawn -- side by side on the PC, one under the other on a phone" % (sfx, W),
           lambda: g and g["cv"] and g["nv"] and (g["side"] if W == 1366 else g["stack"]), lambda: g)
        ck("P2%s the Clinic's box offers its join; NK's box says billed, on the NK Pathology lane, with 'Mark paid by NK'" % sfx,
           lambda: g and "Join and save the rates" in g["ctext"] and "on the NK Pathology lane" in g["ntext"] and "Mark paid by NK" in g["ntext"], lambda: g)
        ck("P3%s no horizontal scroll; no script error" % sfx, lambda: pg.evaluate("document.documentElement.scrollWidth<=window.innerWidth+1") and not errs, lambda: errs)
        ctx.close()
    br.close()
srv.shutdown()
db.close()
MUST = list(MUST_RED)
if EXPECT_RED:
    red = [k for k in MUST if not RES.get(k)]
    print("CONTROL: %d of %d S746 page checks red" % (len(red), len(MUST)))
    sys.exit(0 if len(red) == len(MUST) else 1)
bad = [k for k, v in RES.items() if not v]
print("PAGE WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
