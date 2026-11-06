#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s732_app.py -- S732_DESK_OTHER_LINES on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given sorting_desk.py (the kit's TO -- or the live FROM for the control), on a COPY of a database (SQLite's backup
API). Made-up rows only: papers stamped Z-2031-8*, suppliers 'WALK732 ...', a made-up owner login. The reader is off; nothing is
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
MUST_RED = ("A0", "V1", "V2", "V3", "V4", "V5", "V6")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s732app_")
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
            if "NOT mounted" in l or "S732" in l or "Traceback" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S732_WALK_DEBUG"):
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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:400]) if (d and not ok) else ""))


import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
sd = mods.get("sorting_desk")
ck("A0 the real app loads with its seven parts mounted; sorting_desk.py is S732's (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and getattr(sd, "OTHERLINES", "") == "S732")
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):                                     # a fresh database (the rehearsal) lacks what the live one has
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s732'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s732','Walk owner','owner','x',1)")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_own_s732'").fetchone()[0]
    ss["epoch"] = epoch


def mk(tag, lane="clinic", sub="others", items=(), **cols):
    vals = dict(kind="Pharmacy" if lane == "pharmacy" else "Consumable", vendor="WALK732 JASORIA BROTHERS", stamp_no="Z-2031-8" + tag,
                status="captured" if lane == "pharmacy" else "draft", lane=lane, created_at="2031-05-10 05:00:00", submitted_at="2031-05-10 05:00",
                submitted_by="walkscan", doc_kind="bill", bill_no="W732-" + tag, bill_date="2031-05-10", total_amount=500, subgroup=sub, ocr_status="read")
    vals.update(cols)
    bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
    for n, q, u, r in items:
        db.execute("INSERT INTO bill_items(bill_id, item_name, pack_size, quantity, rate, amount) VALUES(?,?,?,?,?,?)", (bid, n, u, q, r, (q or 0) * (r or 0)))
    db.commit()
    return bid


def items(bid):
    return [(r["item_name"], r["pack_size"], r["quantity"], r["rate"], r["amount"]) for r in
            db.execute("SELECT * FROM bill_items WHERE bill_id=? ORDER BY id", (bid,))]


def save(bid, **kw):
    body = dict(id=bid, vendor="WALK732 JASORIA BROTHERS", bill_no="W732-%d" % bid, bill_date="2031-05-10", total_amount="500", kind="bill",
                dest="others", who="mk", flag="", joins=[])
    body.update(kw)
    r = own.post("/desk/api/save", data=json.dumps(body), content_type="application/json")
    return r.get_json(silent=True) or {"ok": False, "error": "status %s" % r.status_code}


READ = (("WALK732 EXIDE INVERTER BATTERY", 2, "piece", 200.0), ("WALK732 TERMINAL GREASE", 1, None, None))
P1 = mk("P1", items=READ)
pj = own.get("/desk/api/paper/%d" % P1).get_json(silent=True) or {}
ck("V1 an Others paper's desk data carries its read lines for the Other lines panel (name, quantity, unit, rate)",
   lambda: (pj.get("fo") or {}).get("lines") == [{"name": "WALK732 EXIDE INVERTER BATTERY", "qty": 2.0, "unit": "piece", "rate": 200.0},
                                                {"name": "WALK732 TERMINAL GREASE", "qty": 1.0, "unit": "", "rate": None}],
   lambda: pj.get("fo", "no fo"))
s1 = save(P1, fo_lines=[{"name": " Walk732  Inverter battery 150Ah ", "qty": "2", "unit": "piece", "rate": "240"},
                        {"name": "Walk732 Terminal grease", "qty": "1", "unit": "", "rate": ""}, {"name": "", "qty": "", "unit": "", "rate": ""}])
ck("V2 the Save writes the changed lines as the paper's item lines (amount = qty x rate; a blank line dropped), audited desk_lines",
   lambda: s1.get("ok") and items(P1) == [("Walk732 Inverter battery 150Ah", "piece", 2.0, 240.0, 480.0), ("Walk732 Terminal grease", None, 1.0, None, None)]
   and "2 item lines saved." in s1.get("message", "") and db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='desk_lines'", (P1,)).fetchone(),
   lambda: (s1, items(P1)))
P2 = mk("P2", items=READ)
s2 = save(P2, fo_lines=[{"name": "", "qty": "3", "unit": "", "rate": "10"}])
ck("V3 a line with no name is refused ('Line 1: what is it?') and nothing changes", lambda: not s2.get("ok") and "Line 1: what is it?" in (s2.get("error") or "") and items(P2) == items(mk("PX", items=READ)),
   lambda: (s2, items(P2)))
s3 = save(P2, fo_lines=[{"name": "Walk732 thing", "qty": "", "unit": "", "rate": "10"}])
ck("V4 a line with no quantity is refused ('Line 1: the quantity?') and nothing changes", lambda: not s3.get("ok") and "Line 1: the quantity?" in (s3.get("error") or ""),
   lambda: (s3, items(P2)))
s4 = save(P2, fo_lines=[{"name": "Walk732 thing", "qty": "two", "unit": "", "rate": ""}])
ck("V5 a quantity that is not a number is refused", lambda: not s4.get("ok") and "not a number" in (s4.get("error") or ""), lambda: s4)
ph = db.execute("SELECT * FROM bills WHERE id=?", (mk("PH", lane="pharmacy", sub=None, items=READ),)).fetchone()
ck("V6 a pharmacy paper and a person's paper get no Other lines panel", lambda: sd._s732_paper(db, ph) == {"fo": None}
   and sd._s732_paper(db, db.execute("SELECT * FROM bills WHERE id=?", (mk("PS", sub="personal"),)).fetchone()) == {"fo": None})
P3 = mk("P3", items=READ)
before = items(P3)
s5 = save(P3)
ck("K1 a Save without the panel changed leaves the item lines as read", lambda: s5.get("ok") and items(P3) == before, lambda: (s5, items(P3)))
P4 = mk("P4", sub="", items=READ)
s6 = save(P4, dest="stationery", fo_lines=[{"name": "Walk732 x", "qty": "1"}])
ck("K2 lines sent with another group (Stationery) never touch the item lines", lambda: s6.get("ok") and items(P4) == before, lambda: (s6, items(P4)))
P5 = mk("P5", items=READ)
s7 = save(P5, fo_lines=[{"name": "", "qty": "", "unit": "", "rate": ""}])
ck("K3 only blank lines: the item lines stay as they are", lambda: s7.get("ok") and items(P5) == before, lambda: (s7, items(P5)))
ck("K4 the desk's list and the sorting desk still open", lambda: own.get("/desk/api/list").status_code == 200 and own.get("/desk").status_code == 200)
db.close()

if EXPECT_RED:
    red = [k for k in MUST_RED if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S732 checks red; K green %d of %d" % (len(red), len(MUST_RED), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST_RED) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("APP WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
