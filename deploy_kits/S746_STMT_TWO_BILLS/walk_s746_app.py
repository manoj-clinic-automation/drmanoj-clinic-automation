#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s746_app.py -- S746_STMT_TWO_BILLS on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
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
MUST_RED = ("A0", "V1", "V2", "V3", "V4", "V5", "V7", "V9", "V10", "V11", "V12")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s746app_")
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


ck("V1 the statement holds both sides and the NK bill's columns are on the table",
   lambda: sorted(stmt()["sides"]) == ["clinic", "nk"] and "nk_bill_id" in {r[1] for r in db.execute("PRAGMA table_info(stationery_stmt)")}, lambda: (stmt().get("sides"), nl))
pg = own.get("/stationery").get_data(as_text=True)
ck("V2 his Stationery page shows the Clinic's bill and NK Pathology's bill, each with its own join",
   lambda: 'id="s746clinic"' in pg and 'id="s746nk"' in pg and pg.count('name=side value="') >= 2 and "moved to the NK Pathology lane by this join" in pg)
r3 = own.post("/stationery/statement/join", data={"id": str(sid), "side": "nk", "bill": str(BN), "r%d" % lines["nk"]: "0.92", "r%d" % lines["clinic"]: "999"})
db.commit()
ck("V3 NK's bill joined: the paper moves to the NK Pathology lane (audited), only the NK line takes a rate",
   lambda: r3.status_code in (200, 302) and row("bills", BN)["lane"] == "lab_purchase" and stmt()["nk_bill_id"] == BN and row("stationery_line", lines["nk"])["rate"] == 0.92
   and row("stationery_line", lines["clinic"])["rate"] is None and db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='relane'", (BN,)).fetchone(),
   lambda: (row("bills", BN)["lane"], stmt().get("nk_bill_id"), row("stationery_line", lines["nk"])["rate"], row("stationery_line", lines["clinic"])["rate"]))
ck("V4 the NK line is billed, the clinic line still on statement, the statement part billed",
   lambda: state("nk") == "billed" and state("clinic") == "on statement" and stmt()["state"] == "part billed", lambda: (state("nk"), state("clinic"), stmt()["state"]))
try:
    st.stmt_join(db, sid, BL, {}, side="clinic")
    v5 = "joined"
except Exception as e:                                               # noqa: BLE001
    v5 = str(e)
db.rollback()
ck("V5 a paper on the NK lane is refused as the Clinic's bill", lambda: "join it as NK Pathology's bill" in v5, lambda: v5)
try:
    st.stmt_join(db, sid, BN, {}, side="clinic")
    v9 = "joined"
except Exception as e:                                               # noqa: BLE001
    v9 = str(e)
db.rollback()
ck("V9 a paper already joined (as NK's bill) is not joined again", lambda: "already joined" in v9 or "NK Pathology lane" in v9, lambda: v9)
r6 = own.post("/stationery/statement/join", data={"id": str(sid), "side": "clinic", "bill": str(BC), "r%d" % lines["clinic"]: "834"})
db.commit()
ck("K2 the Clinic's bill joined: its line billed at its rate, the paper stays on the clinic lane, the statement billed",
   lambda: stmt()["bill_id"] == BC and row("stationery_line", lines["clinic"])["rate"] == 834 and row("bills", BC)["lane"] == "clinic" and stmt()["state"] == "billed",
   lambda: (stmt().get("bill_id"), row("stationery_line", lines["clinic"])["rate"], stmt()["state"]))
own.post("/stationery/statement/paid", data={"id": str(sid), "side": "nk", "ref": "WALK cheque"})
db.commit()
ck("V7 NK pays its own: the NK line paid, the statement not yet paid", lambda: state("nk") == "paid" and state("clinic") == "billed" and stmt()["state"] == "billed"
   and stmt()["nk_paid_ref"] == "WALK cheque" and not stmt()["paid_at"], lambda: (state("nk"), state("clinic"), stmt()["state"]))
def _box():
    try:
        return st.account_view(db)["box"]
    except Exception as e:                                           # noqa: BLE001
        return {"err": repr(e)}


bx = _box()
ck("K4 NK paid, the Clinic not yet: NK's amount counts as paid this year, not unpaid (its own payment)",
   lambda: bx.get("unpaid_nk", (1, 1))[0] == 0 and bx.get("paid_nk", 0) > 0, lambda: bx)
own.post("/stationery/statement/paid", data={"id": str(sid), "side": "clinic", "ref": "WALK UPI"})
db.commit()
ck("K3 the Clinic pays: the statement reads paid", lambda: stmt()["state"] == "paid" and state("clinic") == "paid", lambda: stmt()["state"])
pg2 = own.get("/stationery").get_data(as_text=True)
ck("V10 the page says each bill paid, NK's 'by NK Pathology'", lambda: "by NK Pathology." in pg2 and pg2.count("· paid ") >= 2, lambda: pg2.count("· paid "))
C2 = paper("C2")
db.execute("UPDATE bills SET bill_date='2031-06-10', created_at='2031-06-10 05:00:00' WHERE id=?", (C2,))
db.commit()
sort(C2, "WALK746 A4 PAPER", 1, "ream", "clinic")
sid2, _n = st.stmt_make(db, "2031-06", key, who="walk")
db.commit()
pg3 = own.get("/stationery").get_data(as_text=True)
ck("V11 a statement with Clinic lines only shows only the Clinic's bill", lambda: 'id="s746clinic"' in pg3 and 'id="s746nk"' not in pg3, lambda: (sid2, 'id="s746nk"' in pg3))
try:
    st.stmt_join(db, sid2, BL, {}, side="nk")
    v12 = "joined"
except Exception as e:                                               # noqa: BLE001
    v12 = str(e)
db.rollback()
ck("V12 NK's bill is refused on a statement that holds no NK line", lambda: "no NK Pathology lines" in v12, lambda: v12)
ck("K1 the desk and the home page still open; the Stationery page 200", lambda: own.get("/desk").status_code == 200 and own.get("/").status_code in (200, 302) and own.get("/stationery").status_code == 200)
db.close()

if EXPECT_RED:
    red = [k for k in MUST_RED if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S746 checks red; K green %d of %d" % (len(red), len(MUST_RED), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST_RED) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("APP WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
