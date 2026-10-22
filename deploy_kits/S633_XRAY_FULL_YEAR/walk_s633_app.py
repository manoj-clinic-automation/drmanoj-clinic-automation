#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s633_app.py -- S633_XRAY_FULL_YEAR on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given xray_costs.py (TO, or FROM for the control), on a COPY of a database (SQLite's backup API) -- or a fresh one the
app makes itself. Made-up rows only, dated 2030-2031 (a machine 'WALK632 machine' with a made-up scan row, battery places 'WALK632 ...',
papers 'B-973x'); made-up owner and manager logins; no reader, no paid call, nothing sent; Flask's test client, no port. The scratch
folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s632_app.py --live <the app folder> --files <folder holding the xray_costs.py to test> [--db <assets.db>] [--expect-red]
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
MUST_RED = ("C1", "C2", "C3", "C4", "C5", "C8")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s633app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):                                   # the app's CODE only (top-level .py / .js / .json) -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        shutil.copy(os.path.join(FILES, "xray_costs.py"), os.path.join(app, "xray_costs.py"))
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
            if "NOT mounted" in l:
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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:400]) if (d and not ok) else ""))


def txt(h):
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h))


import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
ck("A0 the real app loads with its six parts mounted (%s)" % ", ".join(m for m, x in mods.items() if x is not None), lambda: all(mods.values()))
xc = mods["xray_costs"]
for m in ("batteries", "xray_costs", "asset_machine"):
    if mods.get(m) is not None:
        mods[m].TODAY = datetime.date(2031, 6, 15)
db = sqlite3.connect(os.environ["ASSETS_DB"])
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
for u, role in (("walk_own_s633", "owner"), ("walk_mgr_s633", "manager")):
    if not db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
        db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('batteries.on','on')")
loc = db.execute("SELECT id FROM locations ORDER BY id LIMIT 1").fetchone()
if loc is None:
    db.execute("INSERT INTO locations(name, visibility) VALUES('WALK633 room','general')")
    loc = db.execute("SELECT id FROM locations ORDER BY id DESC LIMIT 1").fetchone()
MC = "2030-01-01 10:00:00"
def mkasset(name, vendor, serial, day, price, created):
    return db.execute("INSERT INTO assets(name, location_id, category, vendor, serial_no, purchase_date, price, created_at) VALUES(?,?,?,?,?,?,?,?)",
                      (name, loc[0], "Other", vendor, serial, day, price, created)).lastrowid
XM = mkasset("WALK633 xray machine", "MADE-UP xray co", "", "2030-01-01", 100000, MC)
FA = mkasset("WALK633 film bill", "MADE-UP filmco", "DHL 8*10 150SH", "2031-04-20", 5000, "2031-04-21 10:00:00")
FD = mkasset("WALK633 film twin", "MADE-UP filmco", "DHL 8*10 150SH", "2031-05-10", 5929, "2031-05-11 10:00:00")
cc = {r[1]: r for r in db.execute("PRAGMA table_info(asset_cover)")}
AP = db.execute("INSERT INTO bills(vendor, bill_date, created_at, stamp_no, status, lane, doc_kind, subgroup, total_amount, kind) "
                "VALUES('MADE-UP xray co','2031-04-01','2031-04-02 10:00:00','B-9742','approved','clinic','bill','clinic_equipment',12000,'Asset')").lastrowid
cov = {"bill_id": AP, "bill_created_at": "2031-04-02 10:00:00", "asset_id": XM, "kind": "amc", "provider": "MADE-UP xray co", "from_day": "2031-04-01", "till_day": "2032-03-31", "cost": 12000,
       "asset_created_at": MC, "voided_at": ""}
for k, r in cc.items():
    if r[3] and r[4] is None and not r[5] and k not in cov:
        cov[k] = ""
db.execute("INSERT INTO asset_cover(%s) VALUES(%s)" % (",".join(cov), ",".join("?" * len(cov))), tuple(cov.values()))
def mkrow(table, **kw):
    cols = {r[1]: r for r in db.execute("PRAGMA table_info(%s)" % table)}
    for k, r in cols.items():
        if r[3] and r[4] is None and not r[5] and k not in kw:
            kw[k] = ""
    return db.execute("INSERT INTO %s(%s) VALUES(%s)" % (table, ",".join(kw), ",".join("?" * len(kw))), tuple(kw.values())).lastrowid
PL = mkrow("battery_place", grp="online_ups", name="WALK633 xray UPS", sub="Clinic", payer="clinic", supplier="MADE-UP batteries",
           life_months=10, owner_only=0, active=1, sort=9101, made_at="2030-01-01 10:00:00")
mkrow("battery_fit", place_id=PL, fitted_on="2031-04-05", supplier="MADE-UP batteries", price=2500, old_amount=500)
PL2 = mkrow("battery_place", grp="online_ups", name="WALK633 early out", sub="Clinic", payer="clinic", supplier="MADE-UP batteries",
            life_months=12, owner_only=0, active=1, sort=9102, made_at="2030-01-02 10:00:00")
mkrow("battery_fit", place_id=PL2, fitted_on="2031-04-10", removed_on="2031-05-20", supplier="MADE-UP batteries", price=1200)
FB = db.execute("INSERT INTO bills(vendor, bill_date, created_at, stamp_no, status, lane, doc_kind, subgroup, total_amount, kind) "
                "VALUES('MADE-UP filmco two','2031-04-25','2031-04-25 10:00:00','B-9743','approved','clinic','bill','clinic_equipment',700,'Asset')").lastrowid
FX = mkasset("WALK633 film with paper", "MADE-UP filmco two", "8*10", "2031-04-25", 700, "2031-04-26 10:00:00")
try:
    db.execute("UPDATE assets SET bill_id=? WHERE id=?", (FB, FX))
except sqlite3.Error:
    pass
db.execute("INSERT INTO xray_mark(kind, ref_id, ref_created_at, by_whom, at) VALUES('battery_place',?,?,'walk','2031-01-01')", (PL2, "2030-01-02 10:00:00"))
db.execute("INSERT INTO xray_mark(kind, ref_id, ref_created_at, by_whom, at) VALUES('paper',?,?,'walk','2031-01-01')", (FB, "2031-04-25 10:00:00"))
BP = db.execute("INSERT INTO bills(vendor, bill_no, bill_date, created_at, stamp_no, status, lane, doc_kind, subgroup, total_amount, kind) "
                "VALUES('MADE-UP filmco','W633','2031-05-10','2031-05-10 10:00:00','B-9741','approved','clinic','bill','xray_small',5929,'Consumable')").lastrowid
db.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?, 'DHL 8*10 150SH', 2, 2823.5, 5647)", (BP,))
for kind, rid, fp in (("machine", XM, MC), ("battery_place", PL, "2030-01-01 10:00:00")):
    db.execute("INSERT INTO xray_mark(kind, ref_id, ref_created_at, by_whom, at) VALUES(?,?,?,'walk','2031-01-01')", (kind, rid, fp))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]


def client(user):
    c = ar.app.test_client()
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    with c.session_transaction() as ss:
        ss["uid"] = uid
        ss["epoch"] = epoch
    return c


cl = client("walk_own_s633")
r1 = cl.post("/xray/film", data={"do": "add", "asset": FA, "size": "8×10", "boxes": "1", "amount": "5000", "ym": "2031-04"})
r3 = cl.post("/xray/film", data={"do": "add", "asset": FX, "size": "8×10", "boxes": "1", "amount": "700", "ym": "2031-04"})
r2 = cl.post("/xray/film", data={"do": "add", "asset": FD, "size": "8×10", "boxes": "1", "amount": "5929", "ym": "2031-05"})
pg = cl.get("/xray?ym=2031-06")
t = pg.get_data(as_text=True)


def fyrow(ym):
    i = t.find('data-fy="%s"' % ym)
    seg = t[i:t.find("</tr>", i)] if i >= 0 else ""
    return [c for c in re.findall(r"₹[\d,\.]+", seg)]


ck("C0 the page answers 200 for the owner", lambda: pg.status_code == 200, lambda: pg.status_code)
ck("C1 the financial year from April: April, May and June 2031 each have a row", lambda: all('data-fy="%s"' % m in t for m in ("2031-04", "2031-05", "2031-06")),
   lambda: t.count("data-fy="))
ck("C2 the AMC of Rs 12,000 (April 2031 to March 2032) is Rs 1,000 a month, not Rs 12,000 in April", lambda: fyrow("2031-04")[1] == "₹1,000" and fyrow("2031-06")[1] == "₹1,000",
   lambda: fyrow("2031-04"))
ck("C3 the battery (Rs 2,500 less Rs 500 for the old one) is spread over its 10 months (Rs 200 a month); one taken out in its second month is spread over those two months only (Rs 600 each)", lambda: fyrow("2031-04")[2] == "₹800" and fyrow("2031-05")[2] == "₹800" and fyrow("2031-06")[2] == "₹200",
   lambda: fyrow("2031-04"))
ck("C4 film bills kept on the Machines list count in April once their lines are typed (Rs 5,000 + Rs 700); the desk twin does not count again in May (Rs 5,929 once); a record's own bill marked for X-ray is not counted again under Papers marked",
   lambda: r1.status_code == 302 and fyrow("2031-04")[0] == "₹5,700" and fyrow("2031-05")[0] == "₹5,929" and fyrow("2031-04")[3] == "₹0", lambda: (r1.status_code, fyrow("2031-04"), fyrow("2031-05")))
led = t[t.find('id=s633ledger'):t.find('id=s633fassets')] if 'id=s633ledger' in t else ""
ck("C5 film purchases by size: 8×10 runs 1 box Rs 5,000, 2 boxes Rs 5,700, then 4 boxes Rs 11,629; the size line says 4 boxes, Rs 11,629, Rs 2,907 a box",
   lambda: "1 box · ₹5,000" in led and "2 boxes · ₹5,700" in led and "4 boxes · ₹11,629" in led and re.search(r'data-size="8×10">.*?>4<.*?₹11,629.*?₹2,907', led, re.S) is not None,
   lambda: re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", led))[:400])
mg = client("walk_mgr_s633")
rm = mg.post("/xray/film", data={"do": "add", "asset": FA, "size": "8×10", "amount": "1"})
anon = ar.app.test_client().post("/xray/film", data={"do": "add", "asset": FA, "size": "8×10", "amount": "1"})
nl = db.execute("SELECT COUNT(*) FROM xray_film_line WHERE voided_at=''").fetchone()[0] if db.execute("SELECT 1 FROM sqlite_master WHERE name='xray_film_line'").fetchone() else -1
ck("C6 a manager is refused (403) and logged out goes to the login (302); nothing written", lambda: (rm.status_code == 403 and anon.status_code == 302 and nl == 3) or (EXPECT_RED and rm.status_code == 404 and anon.status_code in (302, 404) and nl == -1),
   lambda: (rm.status_code, anon.status_code, nl))
ck("C7 the month pages still answer (October 2026 and the desk's The month)", lambda: cl.get("/xray?ym=2026-10").status_code == 200 and cl.get("/desk/month").status_code == 200)
try:
    lid = db.execute("SELECT id FROM xray_film_line WHERE asset_id=? AND voided_at=''", (FA,)).fetchone()
except sqlite3.Error:
    lid = None
rv = cl.post("/xray/film", data={"do": "void", "line": lid[0] if lid else 0, "ym": "2031-04"})
t = cl.get("/xray?ym=2031-06").get_data(as_text=True)
ck("C8 a film line removed (kept, voided) no longer counts: April films Rs 700", lambda: rv.status_code == 302 and fyrow("2031-04")[0] == "₹700" and
   db.execute("SELECT voided_at FROM xray_film_line WHERE id=?", (lid[0],)).fetchone()[0] != "", lambda: fyrow("2031-04"))
t4 = cl.get("/xray?ym=2031-04").get_data(as_text=True)
mf = t4[t4.find("id=s582machines"):t4.find("id=s582batteries")]
ck("C9 the AMC's own paper is claimed once: no 'one paper, two entries' on its monthly shares, and the paper shows under it",
   lambda: "B-9742" in mf and "one paper, two entries" not in mf, lambda: re.sub(r"\\s+", " ", re.sub("<[^>]+>", " ", mf))[:300])
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S633 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad else "NOT AS IT MUST BE: " + ", ".join(bad)))
    sys.exit(0 if not bad else 1)
print("WALK S633 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
