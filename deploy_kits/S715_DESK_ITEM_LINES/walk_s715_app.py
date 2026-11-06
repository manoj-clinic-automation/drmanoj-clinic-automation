#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s715_app.py -- S715_DESK_ITEM_LINES on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given sorting_desk.py (the kit's TO -- or the live FROM for the control), on a COPY of a database (SQLite's backup
API). Made-up rows only: suppliers 'WALK715 ...', papers stamped Z-2031-*, products 'Walk715 ...'; made-up owner and manager
logins; the reader off; nothing sent. In the SCRATCH COPY only, the made-up supplier is the one listed stationery supplier (the live
setting is never written). The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s715_app.py --live <the app folder> --files <folder holding sorting_desk.py> [--db <assets.db>] [--expect-red]
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
MUST_RED = ("A0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11", "V12", "V13")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s715app_")
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
            if "NOT mounted" in l or "S715" in l or "Traceback" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S715_WALK_DEBUG"):
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
st = mods.get("stationery")
sd = mods.get("sorting_desk")
ck("A0 the real app loads with its seven parts mounted; sorting_desk.py is S715's (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and getattr(sd, "ITEMS", "") == "S715")
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('stationery.suppliers','walk715 variety|walk715 onlylisted')")   # the scratch copy: the made-up supplier only
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('stationery.suppliers_from','2031-05-01')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):                                     # a fresh database (the rehearsal) lacks what the live one has
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
for u, role in (("walk_own_s715", "owner"), ("walk_mgr_s715", "manager")):
    if not db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
        db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.execute("CREATE TABLE IF NOT EXISTS claude_reading(bill_id INTEGER PRIMARY KEY, at TEXT NOT NULL, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT)")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]


def client(user):
    c = ar.app.test_client()
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    with c.session_transaction() as ss:
        ss["uid"] = uid
        ss["epoch"] = epoch
    return c


own, mgr = client("walk_own_s715"), client("walk_mgr_s715")
VEND = "WALK715 VARIETY STATIONERS"


def mk(tag, vendor, lane="clinic", dk="challan", created="2031-05-10 05:00:00", **cols):
    vals = dict(kind={"clinic": "Consumable", "lab_purchase": "Lab", "pharmacy": "Pharmacy", "other_doc": "Other"}.get(lane, "Consumable"),
                vendor=vendor, stamp_no="Z-2031-" + tag, status="draft" if lane == "clinic" else "captured", lane=lane, created_at=created,
                submitted_at=created[:16], submitted_by="walkscan", doc_kind=dk, bill_date=created[:10], bill_no=cols.pop("bill_no", "W" + tag))
    vals.update(cols)
    bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
    db.commit()
    return bid


def row(bid):
    return db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()


def lines(bid):
    try:
        return [dict(r) for r in db.execute("SELECT * FROM stationery_line WHERE bill_id=? AND voided_at='' ORDER BY line_no, id", (bid,))]
    except sqlite3.Error:
        return []


def item(name):
    r = db.execute("SELECT * FROM stationery_item WHERE name=?", (name,)).fetchone()
    return dict(r) if r else None


def save(cl, bid, **kw):
    body = dict(id=bid, vendor=VEND, bill_no="W715", bill_date="2031-05-12", total_amount="90", kind="challan", dest="stationery", who="mk",
                flag="", joins=[])
    body.update(kw)
    r = cl.post("/desk/api/save", data=json.dumps(body), content_type="application/json")
    return r.get_json(silent=True) or {"ok": False, "error": "status %s" % r.status_code}


own.post("/stationery/item", data={"do": "add", "name": "Walk715 Register 72", "unit": "piece", "rate": "20", "low": "2"})
REG = (item("Walk715 Register 72") or {}).get("id")
C1 = mk("C1", VEND)
C2 = mk("C2", VEND)
C3 = mk("C3", VEND)
N1 = mk("N1", "WALK715 PLAIN SUPPLIER")
N2 = mk("N2", "WALK715 PLAIN SUPPLIER")
B1 = mk("B1", VEND, dk="bill")
mk("A1", VEND, status="approved")                                     # sorted papers: the supplier list is made from these
mk("A2", "WALK715 PLAIN SUPPLIER", status="approved")
mk("P1", "WALK715 PERSONAL PERSON", subgroup="personal", status="approved")
mk("R1", "WALK715 RESUME PERSON", lane="other_doc", subgroup="resume", status="approved")
mk("PH", "WALK715 PHARMA SUPPLIER", lane="pharmacy", status="approved")
mk("OE", "WALK715 OWNER EXPENSE SHOP", lane="owner_expense", status="approved")
mk("D1", "WALK715 DRAFT ONLY NAME")
mk("SD", "WALK715 SORTED DRAFT CO", subgroup="others")              # a challan waiting for its bill, put in a section by a person
mk("OL", "WALK715 ONLYLISTED TRADERS")                                # a listed supplier with no sorted paper yet                                    # waiting, never sorted: never offered
db.execute("UPDATE bills SET subgroup='stationery' WHERE id IN (?,?,?,?,?,?)", (C1, C2, C3, N1, N2, B1))
db.commit()

h = own.get("/desk").get_data(as_text=True)
ck("V1 the desk page carries S715: the supplier list box, the calendar date, '+ Add a line', the re-read door",
   lambda: all(x in h for x in ("id=sup715", "id=f_date type=date", "data-s7add", "S715_DESK_ITEM_LINES", "/bills/0/reread", "/desk/api/suppliers")),
   lambda: [x for x in ("id=sup715", "id=f_date type=date", "data-s7add", "S715_DESK_ITEM_LINES", "/bills/0/reread", "/desk/api/suppliers") if x not in h])

r = own.get("/desk/api/suppliers")
sj = r.get_json(silent=True) or {}
names = {x.get("name"): x for x in sj.get("suppliers", [])} if isinstance(sj, dict) else {}
rm = mgr.get("/desk/api/suppliers")
mnames = {x.get("name") for x in (rm.get_json(silent=True) or {}).get("suppliers", [])} if rm.status_code == 200 else set()
ck("V2 the supplier list from sorted papers: the listed supplier marked, a plain one offered; never a personal, resume, pharmacy or waiting-only name; the owner's expense shop to the owner only",
   lambda: r.status_code == 200 and names.get(VEND, {}).get("listed") is True and names.get("WALK715 PLAIN SUPPLIER", {}).get("listed") is False
   and not ({"WALK715 PERSONAL PERSON", "WALK715 RESUME PERSON", "WALK715 PHARMA SUPPLIER", "WALK715 DRAFT ONLY NAME"} & (set(names) | mnames))
   and VEND in mnames and "WALK715 OWNER EXPENSE SHOP" in names and "WALK715 OWNER EXPENSE SHOP" not in mnames,
   lambda: (r.status_code, {k: v.get("listed") for k, v in names.items() if k.startswith("WALK715")}, sorted(x for x in mnames if x.startswith("WALK715"))))

pj = own.get("/desk/api/paper/%d" % C1).get_json(silent=True) or {}
ck("V3 a listed supplier's paper tells the page so (stk.listed) and each line carries its side",
   lambda: (pj.get("stk") or {}).get("listed") is True and all("side" in l for l in (pj.get("stk") or {}).get("lines") or []),
   lambda: json.dumps(pj.get("stk"))[:300])

s1 = save(own, C1, st_lines=[{"no": 1, "name": "Walk715 Register 72", "qty": "3", "unit": "piece", "rate": "20", "item": str(REG), "side": "clinic"},
                            {"no": 2, "name": "Walk715 Lab pad", "qty": "2", "unit": "pad", "rate": "15", "item": "new", "side": "nk"}])
L1 = lines(C1)
ck("V4 a listed supplier's challan is sorted on the desk: both lines kept with their sides, the new item on the list with its unit and rate, the paper mixed",
   lambda: s1.get("ok") and [(l["line_no"], l["side"]) for l in L1] == [(1, "clinic"), (2, "nk")] and (item("Walk715 Lab pad") or {}).get("unit") == "pad"
   and abs(float((item("Walk715 Lab pad") or {}).get("rate") or 0) - 15) < 0.01 and int(row(C1)["mixed"] or 0) == 1,
   lambda: (s1, [(l["line_no"], l["side"], l["item_id"]) for l in L1], item("Walk715 Lab pad"), row(C1)["mixed"]))
pj2 = own.get("/desk/api/paper/%d" % C1).get_json(silent=True) or {}
ck("V5 opened again, the saved lines come back with their sides (a re-save never turns NK into Clinic)",
   lambda: [l.get("side") for l in (pj2.get("stk") or {}).get("lines") or [] if l.get("saved")] == ["clinic", "nk"],
   lambda: json.dumps((pj2.get("stk") or {}).get("lines"))[:300])
v0 = row(C2)["vendor"]
s2 = save(own, C2, bill_no="W715-C2", st_lines=[{"no": 1, "name": "Walk715 Register 72", "qty": "1", "unit": "piece", "item": str(REG), "side": ""}])
ck("V6 a listed supplier's line with no side is refused in words, and nothing is saved",
   lambda: not s2.get("ok") and "choose Clinic or NK Pathology on each line" in (s2.get("error") or "") and not lines(C2) and row(C2)["bill_no"] == "WC2",
   lambda: (s2, lines(C2), row(C2)["bill_no"]))
s3 = save(own, C3, st_lines=[{"no": 1, "name": "Walk715 Register 72", "qty": "1", "unit": "piece", "item": str(REG), "side": "nk"}])
ck("V7 every line NK is refused: 'sort it on the Stationery page'",
   lambda: not s3.get("ok") and "sort it on the Stationery page" in (s3.get("error") or "") and not lines(C3),
   lambda: (s3, lines(C3)))
s4 = save(mgr, C2, st_lines=[{"no": 1, "name": "Walk715 Register 72", "qty": "2", "unit": "piece", "item": str(REG), "side": "clinic"}])
ck("V8 the manager sorts a listed supplier's challan on the desk too (Clinic line kept)",
   lambda: s4.get("ok") and [(l["line_no"], l["side"]) for l in lines(C2)] == [(1, "clinic")], lambda: (s4, lines(C2)))
s5 = save(own, N1, vendor="WALK715 PLAIN SUPPLIER", st_lines=[{"no": 1, "name": "Walk715 Register 72", "qty": "4", "unit": "piece", "rate": "20", "item": str(REG)}])
ck("K1 a plain supplier's stationery lines save as before (no side asked; the line is the clinic's)",
   lambda: s5.get("ok") and [(l["line_no"], l["side"]) for l in lines(N1)] == [(1, "clinic")], lambda: (s5, lines(N1)))
ck("V9 a listed challan's lines sorted on the desk carry the paper's own date (2031-05-12), as the Stationery page's do",
   lambda: L1 and all(l["day"] == "2031-05-12" for l in lines(C1)), lambda: [(l["line_no"], l["day"]) for l in lines(C1)])
s6 = save(own, N2, vendor="WALK715 PLAIN SUPPLIER", st_lines=[{"no": 1, "name": "Walk715 Register 72", "qty": "1", "unit": "piece", "item": str(REG), "side": "nk"}])
r12 = own.get("/desk/api/suppliers").get_json(silent=True) or {}
n12 = {x.get("name"): x for x in r12.get("suppliers", [])}
ck("V12 the list carries a sorted waiting challan's supplier and a listed supplier with no sorted paper (marked listed)",
   lambda: "WALK715 SORTED DRAFT CO" in n12 and n12.get("WALK715 ONLYLISTED TRADERS", {}).get("listed") is True,
   lambda: sorted(k for k in n12 if k.startswith("WALK715")))
s8 = save(own, C1, kind="bill", st_lines=[{"no": 1, "name": "Walk715 Register 72", "qty": "3", "unit": "piece", "rate": "20", "item": str(REG), "side": "clinic"},
                                         {"no": 2, "name": "Walk715 Lab pad", "qty": "2", "unit": "pad", "rate": "15", "item": str((item("Walk715 Lab pad") or {}).get("id")), "side": "nk"}])
ck("V13 a paper holding NK lines that would leave the listed-challan flow (re-typed as a Bill) is refused -- its NK lines never turn Clinic",
   lambda: not s8.get("ok") and "holds NK Pathology lines" in (s8.get("error") or "") and [l["side"] for l in lines(C1)] == ["clinic", "nk"],
   lambda: (s8, [l["side"] for l in lines(C1)]))
ck("V10 a plain supplier's line sent as NK is stored as the clinic's (an NK side only on the listed flow)",
   lambda: s6.get("ok") and [l["side"] for l in lines(N2)] == ["clinic"], lambda: (s6, lines(N2)))
s7 = save(own, B1, kind="bill", st_lines=[{"no": 1, "name": "Walk715 Register 72", "qty": "1", "unit": "piece", "item": str(REG), "side": "nk"}])
ck("V11 a listed supplier's BILL (not a challan) saves its lines as the clinic's, no side asked",
   lambda: s7.get("ok") and [l["side"] for l in lines(B1)] == ["clinic"], lambda: (s7, lines(B1)))
ck("K2 the desk's list and the Stationery page still open", lambda: own.get("/desk/api/list").status_code == 200 and own.get("/stationery").status_code == 200)
db.close()

if EXPECT_RED:
    red = [k for k in MUST_RED if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S715 checks red; K green %d of %d" % (len(red), len(MUST_RED), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST_RED) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("APP WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
