#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s741_app.py -- S741_STATIONERY_PRODUCT_PICK on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
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
MUST_RED = ("A0", "V1", "V2", "V3")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s741app_")
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
                           capture_output=True, text=True, timeout=300)
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


import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
sd, st = mods.get("sorting_desk"), mods.get("stationery")
ck("A0 the real app loads with its seven parts mounted; stationery.py is S741's", lambda: all(mods.values()) and getattr(st, "PICK_S741", "") == "S741")
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
iid, _m = st.add_item(db, "WALK741 A4 PAPER 75 GSM", "ream", None, None, "walk")
vals = dict(kind="Consumable", vendor=VAR, stamp_no="Z-2031-7A1", status="draft", lane="clinic", created_at="2031-05-10 05:00:00",
            submitted_at="2031-05-10 05:00", submitted_by="walkscan", doc_kind="challan", bill_no="W741", bill_date="2031-05-10", subgroup="", ocr_status="read")
P1 = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
db.execute("INSERT INTO bill_items(bill_id, item_name, quantity) VALUES(?,?,?)", (P1, "WALK741 PAPER RIM", 2))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_own_s741'").fetchone()[0]
    ss["epoch"] = epoch
r1 = own.get("/stationery")
h1 = r1.get_data(as_text=True)
ck("V1 his Stationery page carries the searchable list (S741) and the products it reads",
   lambda: r1.status_code == 200 and "S741 (F-1160)" in h1 and "datalist id=s674items" in h1 and "WALK741 A4 PAPER 75 GSM" in h1 and "data-paper=\"%d\"" % P1 in h1, lambda: r1.status_code)
r2 = own.get("/stationery/sort")
h2 = r2.get_data(as_text=True)
ck("V2 the staff Stationery sort page carries it too", lambda: r2.status_code == 200 and "S741 (F-1160)" in h2 and "Naya saamaan" in h2, lambda: r2.status_code)
ck("V3 the S741 script appears once per page", lambda: h1.count("S741 (F-1160)") == 1 and h2.count("S741 (F-1160)") == 1)
r3 = own.post("/stationery/sort/save", data={"paper": str(P1), "back": "stock", "n1": "WALK741 A4 PAPER 75 GSM", "q1": "2", "u1": "ream", "f1": "clinic"})
ln = [(r["item_id"], r["qty"]) for r in db.execute("SELECT * FROM stationery_line WHERE bill_id=? AND voided_at=''", (P1,))]
ck("K1 a Save with a picked product records its line as before", lambda: r3.status_code in (200, 302) and ln == [(iid, 2.0)], lambda: (r3.status_code, ln))
ck("K2 the desk and the home page still open", lambda: own.get("/desk").status_code == 200 and own.get("/").status_code in (200, 302))
db.close()

if EXPECT_RED:
    red = [k for k in MUST_RED if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S741 checks red; K green %d of %d" % (len(red), len(MUST_RED), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST_RED) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("APP WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
