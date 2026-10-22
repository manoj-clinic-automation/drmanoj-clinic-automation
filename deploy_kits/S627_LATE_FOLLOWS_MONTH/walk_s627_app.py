#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s627_app.py -- S627 on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch folder with the
given TO (or FROM) files, on a COPY of a database (SQLite's backup API) -- or a fresh one the app makes itself. Made-up rows only
(a machine 'WALK625 machine', papers 'B-96xx' of 'MADE-UP' suppliers, dated 2031; the papers 'B-95xx'); a made-up owner login;
no reader, no paid call, nothing sent; Flask's test client, no port. The scratch folder is removed at the end.

    python3 -B walk_s627_app.py --live <the app folder> --files <folder with asset_register.py and sorting_desk.py to test> [--db <assets.db to copy>] [--expect-red]
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
MUST_RED = ("L1", "L4", "L6", "L8")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s627app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):                                   # the app's CODE only (top-level .py / .js / .json) -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in ("asset_register.py", "sorting_desk.py"):
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
KEY = "papers.month_from_bill_date"
db = sqlite3.connect(os.environ["ASSETS_DB"])
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):                                     # on the scratch copy only
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s627'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s627','Walk Owner','owner','x',1)")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?, '2031-01-01 00:00:00')", (KEY,))      # the switch, on the COPY: from 2031
ids = {}
for k, made, bm, bd in (("L1", "2031-03-10 05:00:00", "2031-03", "2031-01-15"), ("L2", "2030-12-20 05:00:00", "2030-12", "2030-11-02"),
                        ("L3", "2031-03-10 05:00:00", "2031-02", "2031-01-15"), ("L5", "2031-03-10 05:00:00", "2031-03", "2031-03-02"),
                        ("L8", "2031-03-31 20:00:00", "2031-04", "2031-03-15"), ("L10", "2031-03-10 05:00:00", "2031-03", "2030-01-15")):
    ids[k] = db.execute("INSERT INTO bills(vendor, created_at, stamp_no, status, lane, doc_kind, subgroup, bill_month, bill_date) "
                        "VALUES(?, ?, ?, 'draft', 'clinic', 'bill', 'stationery', ?, ?)",
                        ("MADE-UP SUPPLIER " + k, made, "B-95%02d" % len(ids), bm, bd)).lastrowid
db.commit()
for k in ids:
    ar._set_late(db, ids[k])
db.commit()


def late(k):
    return db.execute("SELECT late_for FROM bills WHERE id=?", (ids[k],)).fetchone()[0]


ck("L1 scanned in March, its bill dated January (counted in January by S625's rule): marked late for January", lambda: late("L1") == "2031-01", lambda: late("L1"))
ck("L2 a paper scanned before the switch-on, its month the scan month: not late, as before", lambda: late("L2") is None, lambda: late("L2"))
ck("L3 a person's earlier month (February): late for February, as before", lambda: late("L3") == "2031-02", lambda: late("L3"))
ck("L5 a bill of the scan month itself: not late", lambda: late("L5") is None, lambda: late("L5"))
ck("L8 scanned 01-Apr 01:30 IST (31-Mar in UTC), its bill dated 15-Mar: late for March (the IST scan month)", lambda: late("L8") == "2031-03", lambda: late("L8"))
ck("L10 a bill dated more than 12 months back: not moved, not late", lambda: late("L10") is None, lambda: late("L10"))
db.execute("UPDATE settings SET value='off' WHERE key=?", (KEY,))
hid = db.execute("INSERT INTO bills(vendor, created_at, stamp_no, status, lane, doc_kind, subgroup, bill_month, bill_date) "
                 "VALUES('MADE-UP SUPPLIER L9', '2031-03-10 05:00:00', 'B-9590', 'draft', 'clinic', 'bill', 'stationery', '2031-03', '2031-01-15')").lastrowid
db.commit()
ar._set_late(db, hid)
db.commit()
ck("L9 with the rule switched off: not late (the old rule)", lambda: db.execute("SELECT late_for FROM bills WHERE id=?", (hid,)).fetchone()[0] is None)
db.execute("UPDATE settings SET value='2031-01-01 00:00:00' WHERE key=?", (KEY,))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
uid = db.execute("SELECT id FROM users WHERE username='walk_own_s627'").fetchone()[0]
cl = ar.app.test_client()
with cl.session_transaction() as ss:
    ss["uid"] = uid
    ss["epoch"] = epoch
r = cl.get("/bills/%d" % ids["L1"])
t = r.get_data(as_text=True)
ck("L4 the paper's own page (200) carries 'late — belongs to 2031-01'", lambda: r.status_code == 200 and "belongs to 2031-01" in t, lambda: (r.status_code, re.findall(r"late[^<]{0,40}", t)[:3]))
r = cl.get("/desk/month?ym=2031-01")
t = r.get_data(as_text=True)
ck("L6 the desk's The month page (200) says a bill dated earlier than its scan counts in its own month", lambda: r.status_code == 200 and "counts in its own month" in t,
   lambda: r.status_code)
ck("L7 the desk and the papers' month answer (200)", lambda: cl.get("/desk").status_code == 200 and cl.get("/papers/month?ym=2031-01").status_code == 200)
import subprocess                                                    # noqa: E402
heal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heal_s627.py")
db.close()
h1 = subprocess.run([sys.executable, "-B", heal, os.environ["ASSETS_DB"], APPD], capture_output=True, text=True)
h2 = subprocess.run([sys.executable, "-B", heal, os.environ["ASSETS_DB"], APPD], capture_output=True, text=True)
db = sqlite3.connect(os.environ["ASSETS_DB"])
db.row_factory = sqlite3.Row
ck("L11 the data step marks a paper read before S627 (B-9590, no mark) late for January; a second run marks nothing",
   lambda: db.execute("SELECT late_for FROM bills WHERE id=?", (hid,)).fetchone()[0] == "2031-01" and "B-9590 -> 2031-01" in h1.stdout
   and "heal: 0 paper" in h2.stdout, lambda: (h1.stdout + h1.stderr[-300:], h2.stdout))
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S627 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("WALK S627 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
