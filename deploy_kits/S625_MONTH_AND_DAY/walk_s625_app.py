#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s625_app.py -- S625 on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch folder with the
given TO (or FROM) files, on a COPY of a database (SQLite's backup API) -- or a fresh one the app makes itself. Made-up rows only
(a machine 'WALK625 machine', papers 'B-96xx' of 'MADE-UP' suppliers, dated 2031); a made-up owner login;
no reader, no paid call, nothing sent; Flask's test client, no port. The scratch folder is removed at the end.

    python3 -B walk_s625_app.py --live <the app folder> --files <folder with clinic_papers.py and asset_register.py to test> [--db <assets.db to copy>] [--expect-red]
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
MUST_RED = ("F1", "F6", "F9", "F12", "D1", "D3")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s625app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):                                   # the app's CODE only (top-level .py / .js / .json) -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in ("clinic_papers.py", "asset_register.py"):
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
ck("A0 the real app loads with its six parts mounted", lambda: all(mods.values()), lambda: [m for m, x in mods.items() if x is None])
cp = mods["clinic_papers"]
KEY = "papers.month_from_bill_date"
db = sqlite3.connect(os.environ["ASSETS_DB"])
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):                                     # on the scratch copy only: columns later kits' data steps added on the box
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s625'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s625','Walk Owner','owner','x',1)")
loc = db.execute("SELECT id FROM locations WHERE visibility='general' ORDER BY id LIMIT 1").fetchone()
if loc is None:
    db.execute("INSERT INTO locations(name, visibility) VALUES('WALK625 room','general')")
    loc = db.execute("SELECT id FROM locations ORDER BY id DESC LIMIT 1").fetchone()
real = [r[0] for r in db.execute("SELECT id FROM bills")]                  # the papers already in the database (a copy of the live one on the box)
db.execute("DELETE FROM settings WHERE key=?", (KEY,))
before = dict(db.execute("SELECT b.id, " + cp.MONTH_OF + " FROM bills b"))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?, datetime('now'))", (KEY,))
after_now = dict(db.execute("SELECT b.id, " + cp.MONTH_OF + " FROM bills b"))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?, '')", (KEY,))
after_empty = dict(db.execute("SELECT b.id, " + cp.MONTH_OF + " FROM bills b"))
ck("F13 switched on NOW, every paper already in the database keeps its month (%d papers); an empty switch value changes nothing either" % len(real),
   lambda: before == after_now == after_empty, lambda: [k for k in before if before[k] != after_now.get(k) or before[k] != after_empty.get(k)][:10])
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?, '2031-01-01 00:00:00')", (KEY,))      # the switch, on the COPY: from 2031
ids = {}
for k, made, bm, bd in (("F1", "2031-03-10 05:00:00", "2031-03", "2031-01-15"), ("F2", "2030-12-20 05:00:00", "2030-12", "2030-11-02"),
                        ("F3", "2031-03-10 05:00:00", "2031-02", "2031-01-15"), ("F4", "2031-03-10 05:00:00", "2031-03", "2029-12-01"),
                        ("F5", "2031-03-10 05:00:00", "2031-03", "2031-04-02"), ("F6", "2031-03-31 20:00:00", "2031-04", "2031-03-31"),
                        ("F7", "2031-03-10 05:00:00", "2031-03", "15/01/2031"), ("F11", "2031-03-10 05:00:00", "", "2031-01-15")):
    ids[k] = db.execute("INSERT INTO bills(vendor, created_at, stamp_no, status, lane, doc_kind, subgroup, bill_month, bill_date) "
                        "VALUES(?, ?, ?, 'draft', 'clinic', 'bill', 'stationery', ?, ?)",
                        ("MADE-UP SUPPLIER " + k, made, "B-96%02d" % len(ids), bm or None, bd)).lastrowid
db.commit()


def mo(k):
    return db.execute("SELECT " + cp.MONTH_OF + " FROM bills b WHERE b.id=?", (ids[k],)).fetchone()[0]


ck("F1 scanned in March, month left at March, the bill dated 15-Jan: counts in January (the bill's own month)", lambda: mo("F1") == "2031-01", lambda: mo("F1"))
ck("F2 scanned BEFORE the switch-on: keeps its scan month (past months stay as they are)", lambda: mo("F2") == "2030-12", lambda: mo("F2"))
ck("F3 a person's earlier month (February) still wins", lambda: mo("F3") == "2031-02", lambda: mo("F3"))
ck("F4 a date more than 12 months before the scan is not used", lambda: mo("F4") == "2031-03", lambda: mo("F4"))
ck("F5 a date after the scan month is not used", lambda: mo("F5") == "2031-03", lambda: mo("F5"))
ck("F6 scanned 01-Apr IST (31-Mar in UTC), bill dated 31-Mar: counts in March", lambda: mo("F6") == "2031-03", lambda: mo("F6"))
ck("F7 a date that is not a plain date is not used", lambda: mo("F7") == "2031-03", lambda: mo("F7"))
ck("F11 no month on it and a bill date: the bill's month, as before", lambda: mo("F11") == "2031-01", lambda: mo("F11"))
db.execute("UPDATE settings SET value='off' WHERE key=?", (KEY,))
db.commit()
off = mo("F1")
db.execute("DELETE FROM settings WHERE key=?", (KEY,))
db.commit()
absent = mo("F1")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?, '2031-01-01 00:00:00')", (KEY,))
db.commit()
ck("F8 the switch 'off' or absent = the old rule (March)", lambda: off == "2031-03" and absent == "2031-03", lambda: (off, absent))
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
uid = db.execute("SELECT id FROM users WHERE username='walk_own_s625'").fetchone()[0]
cl = ar.app.test_client()
with cl.session_transaction() as ss:
    ss["uid"] = uid
    ss["epoch"] = epoch
r = cl.get("/bills/%d" % ids["F1"])
t = r.get_data(as_text=True)
ck("F9 the paper's own page (200) says it counts in January 2031, the bill's own date, scanned as March",
   lambda: r.status_code == 200 and "id=s625month" in t and "January 2031" in t, lambda: (r.status_code, re.findall(r"Month:</b>[^<]*", t)[:2]))
r3 = cl.get("/bills/%d" % ids["F3"])
ck("F10 a paper whose month a person chose shows that month as before", lambda: r3.status_code == 200 and "id=s625month" not in r3.get_data(as_text=True))
pm = cl.get("/papers/month?ym=2031-01")
pmt = pm.get_data(as_text=True)
ck("F12 The month for January 2031 (200) counts the moved paper (its supplier 'MADE-UP SUPPLIER F1' listed); the desk answers (200)",
   lambda: pm.status_code == 200 and re.search(r"MADE-UP SUPPLIER F1(?!\d)", pmt) is not None and cl.get("/desk").status_code == 200, lambda: (pm.status_code, re.findall(r"MADE-UP SUPPLIER \w+", pmt)))

aid = db.execute("INSERT INTO assets(name, location_id, category, purchase_date, coverage_start, emi, emi_start, emi_count, created_at) "
                 "VALUES('WALK625 machine', ?, 'Other', '2031-04-28', '2031-04-28', 1, '2031-04-15', 3, '2031-04-28 10:00:00')", (loc[0],)).lastrowid
db.commit()
form = {"name": "WALK625 machine", "location_id": str(loc[0]), "category": "Other", "status": "Active", "kind": "Asset",
        "purchase_year": "2031", "purchase_month": "04", "coverage_year": "2031", "coverage_month": "04", "contract_type": "None",
        "contract_period": "none", "emi": "1", "emi_year": "2031", "emi_month": "04", "emi_count": "3"}
r = cl.post("/assets/%d/edit" % aid, data=form)
row = db.execute("SELECT purchase_date, coverage_start, emi_start FROM assets WHERE id=?", (aid,)).fetchone()
ck("D1 a machine edited with the same month and year keeps its day: purchase 28-04-2031 stays 28-04 (not 01-04)",
   lambda: r.status_code in (200, 302) and row["purchase_date"] == "2031-04-28" and row["coverage_start"] == "2031-04-28", lambda: (r.status_code, tuple(row)))
ck("D3 the EMI start keeps its day too (15-04)", lambda: row["emi_start"] == "2031-04-15", lambda: tuple(row))
form2 = dict(form, purchase_month="05", coverage_month="05")
cl.post("/assets/%d/edit" % aid, data=form2)
row2 = db.execute("SELECT purchase_date, coverage_start FROM assets WHERE id=?", (aid,)).fetchone()
ck("D2 a changed month takes the dropdowns' value (01-05-2031)", lambda: row2["purchase_date"] == "2031-05-01" and row2["coverage_start"] == "2031-05-01", lambda: tuple(row2))
form3 = dict(form, name="WALK625 new machine")
cl.post("/assets/new", data=form3)
row3 = db.execute("SELECT purchase_date FROM assets WHERE name='WALK625 new machine'").fetchone()
ck("D4 a new machine takes the dropdowns' value (01-04-2031), as before", lambda: row3 is not None and row3["purchase_date"] == "2031-04-01", lambda: row3 and tuple(row3))
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S625 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("WALK S625 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
