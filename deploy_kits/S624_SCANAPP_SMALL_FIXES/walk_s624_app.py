#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s624_app.py -- S624 on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch folder with the
given TO (or FROM) files, on a COPY of a database (SQLite's backup API) -- or a fresh one the app makes itself. Made-up rows only
(a machine 'WALK624 machine', papers 'B-97xx' of 'MADE-UP' suppliers, a battery place 'WALK624 place'); a made-up owner login;
no reader, no paid call, nothing sent; Flask's test client, no port. The scratch folder is removed at the end.

    python3 -B walk_s624_app.py --live <the app folder> --files <folder with the three files to test> [--db <assets.db to copy>] [--expect-red]
"""
import datetime
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
MUST_RED = ("A1", "A2", "A3", "A6")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s624app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):                                   # the app's CODE only (top-level .py / .js / .json) -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in ("batteries.py", "asset_machine.py", "stationery.py"):
            shutil.copy(os.path.join(FILES, f), os.path.join(app, f))
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
        notm = [l for l in r.stderr.splitlines() if "NOT mounted" in l]
        for l in notm:
            print("  stderr: " + l[:200])
        if r.returncode not in (0, 1):
            print(r.stderr[-1500:])
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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:500]) if (d and not ok) else ""))


import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
ck("A0 the real app loads with its six parts mounted (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()))
for m in ("batteries", "asset_machine", "stationery"):
    if mods.get(m) is not None:
        mods[m].TODAY = datetime.date(2026, 10, 22)
db = sqlite3.connect(os.environ["ASSETS_DB"])
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
if True:                                                             # on the scratch copy only: the columns later kits' data steps added on the box
    have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
    for col in ("page_of", "mixed"):
        if col not in have:
            db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s624'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s624','Walk Owner','owner','x',1)")
loc = db.execute("SELECT id FROM locations ORDER BY id LIMIT 1").fetchone()
if loc is None:
    db.execute("INSERT INTO locations(name, visibility) VALUES('WALK624 room','general')")
    loc = db.execute("SELECT id FROM locations ORDER BY id DESC LIMIT 1").fetchone()
mid = db.execute("INSERT INTO assets(name, location_id, category, created_at) VALUES('WALK624 machine', ?, 'Other', '2031-01-01 10:00:00')", (loc[0],)).lastrowid
pid = db.execute("INSERT INTO bills(vendor, created_at, stamp_no, status, lane, doc_kind, subgroup) VALUES('MADE-UP AMC','2031-01-02 10:00:00','B-9701','draft','clinic','bill','clinic_equipment')").lastrowid
cid = db.execute("INSERT INTO asset_cover(asset_id, kind, provider, till_day, asset_created_at, voided_at) VALUES(?, 'amc', 'MADE-UP AMC', '2031-12-31', '2031-01-01 10:00:00', '')", (mid,)).lastrowid
cols = {r[1]: r for r in db.execute("PRAGMA table_info(battery_place)")}
pl = {"grp": "gen_inv", "name": "WALK624 place", "supplier": "MADE-UP batteries", "warranty_months": 12, "life_months": 48, "owner_only": 0, "active": 1}
for k, r in cols.items():
    if r[3] and r[4] is None and not r[5] and k not in pl:
        pl[k] = ""
plid = db.execute("INSERT INTO battery_place(%s) VALUES(%s)" % (",".join(pl), ",".join("?" * len(pl))), tuple(pl.values())).lastrowid
fc = {r[1]: r for r in db.execute("PRAGMA table_info(battery_fit)")}
ft = {"place_id": plid, "fitted_on": "2024-01-01", "warranty_months": 12, "supplier": "MADE-UP batteries"}
for k, r in fc.items():
    if r[3] and r[4] is None and not r[5] and k not in ft:
        ft[k] = ""
db.execute("INSERT INTO battery_fit(%s) VALUES(%s)" % (",".join(ft), ",".join("?" * len(ft))), tuple(ft.values()))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
uid = db.execute("SELECT id FROM users WHERE username='walk_own_s624'").fetchone()[0]
cl = ar.app.test_client()
with cl.session_transaction() as ss:
    ss["uid"] = uid
    ss["epoch"] = epoch

r = cl.get("/batteries")
t = r.get_data(as_text=True)
blk = t[t.find("WALK624 place"):][:3000] if "WALK624 place" in t else ""
ck("A1 the owner's Batteries page (200) shows the made-up battery past its warranty as 'Out of warranty since 01-01-2025'",
   lambda: r.status_code == 200 and "Out of warranty since 01-01-2025" in t, lambda: (r.status_code, re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", blk))[:300]))
r = cl.get("/assets/%d" % mid)
t = r.get_data(as_text=True)
ck("A2 the machine page (200) offers a link box on the cover that has no paper", lambda: r.status_code == 200 and "/assets/%d/covers/%d/paper" % (mid, cid) in t,
   lambda: r.status_code)
r = cl.post("/assets/%d/covers/%d/paper" % (mid, cid), data={"paper": "B-9701"})
t2 = cl.get("/assets/%d" % mid).get_data(as_text=True)
ck("A3 linking B-9701 there: stored with its fingerprint; the page then shows B-9701 as its paper",
   lambda: r.status_code == 302 and tuple(db.execute("SELECT bill_id, bill_created_at FROM asset_cover WHERE id=?", (cid,)).fetchone()) == (pid, "2031-01-02 10:00:00")
   and ">B-9701<" in t2, lambda: (r.status_code, tuple(db.execute("SELECT bill_id FROM asset_cover WHERE id=?", (cid,)).fetchone())))
r = cl.get("/stationery")
ck("A4 the owner's Stationery page renders (200)", lambda: r.status_code == 200 and "Stationery &amp; packaging" in r.get_data(as_text=True), lambda: r.status_code)
ck("A5 the desk and The month answer (200)", lambda: cl.get("/desk").status_code == 200 and cl.get("/papers/month").status_code in (200, 302))
ck("A6 the new routes are mounted on the real app", lambda: {"s624_cover_paper", "s624_part_paper"} <= set(ar.app.view_functions))
anon = ar.app.test_client().post("/assets/%d/covers/%d/paper" % (mid, cid), data={"paper": "B-9701"})
ck("A7 logged out, the new route sends to the login door (302), never links", lambda: anon.status_code == 302 or (EXPECT_RED and anon.status_code == 404))
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S624 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("WALK S624 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
