#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s739_app.py -- S739_DESK_YUVIKA_LISTED on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given sorting_desk.py (the kit's TO -- or the live FROM for the control), on a COPY of a database (SQLite's backup
API). Made-up rows only: papers stamped Z-2031-9*, suppliers 'WALK739 ...', a made-up owner login. The reader is off; nothing is
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
MUST_RED = ("A0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11", "V12")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s739app_")
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
            if "NOT mounted" in l or "S739" in l or "Traceback" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S739_WALK_DEBUG"):
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
sd, st = mods.get("sorting_desk"), mods.get("stationery")
ck("A0 the real app loads with its seven parts mounted; sorting_desk.py is S739's (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and getattr(sd, "DESK_S739", "") == "S739")
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):                                     # a fresh database (the rehearsal) lacks what the live one has
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s739'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s739','Walk owner','owner','x',1)")
VAR = "WALK739 VARIETY STATIONERS"
keys = [k for k in (db.execute("SELECT value FROM settings WHERE key=?", (st.SUPPLIERS_KEY,)).fetchone() or [""])[0].split("|") if k.strip()]
keys.append(sd._key(VAR))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (st.SUPPLIERS_KEY, "|".join(keys)))
if not (db.execute("SELECT value FROM settings WHERE key=?", (st.FLOOR_KEY,)).fetchone() or [""])[0]:
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (st.FLOOR_KEY, "2026-10-26"))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_own_s739'").fetchone()[0]
    ss["epoch"] = epoch


def mk(tag, vendor, lane="clinic", sub="", items=(), created="2031-05-10 05:00:00", **cols):
    vals = dict(kind="Consumable", vendor=vendor, stamp_no="Z-2031-9" + tag, status="draft", lane=lane, created_at=created,
                submitted_at=created[:16], submitted_by="walkscan", doc_kind="challan", bill_no="", bill_date="2031-05-10", total_amount=None,
                subgroup=sub, ocr_status="read")
    vals.update(cols)
    bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
    for n, q in items:
        db.execute("INSERT INTO bill_items(bill_id, item_name, quantity) VALUES(?,?,?)", (bid, n, q))
    db.commit()
    return bid


def row(bid):
    return db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()


def pj(bid):
    return own.get("/desk/api/paper/%d" % bid).get_json(silent=True) or {}


def save(bid, vendor, dest, kind="challan", **kw):
    body = dict(id=bid, vendor=vendor, bill_no="", bill_date="2031-05-10", total_amount="", kind=kind, dest=dest, who="mk", flag="", joins=[])
    body.update(kw)
    r = own.post("/desk/api/save", data=json.dumps(body), content_type="application/json")
    db.commit()
    return r.get_json(silent=True) or {"ok": False, "error": "status %s" % r.status_code}


def setsw(on):
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.yuvika',?)", ("on" if on else "off",))
    db.commit()


LINES = (("WALK739 A4 PAPER RIM", 2), ("WALK739 STAPLER PIN", 5))
V1 = mk("V1", VAR, items=LINES)
j1 = pj(V1)
ck("V1 a listed supplier's challan on the flow: the desk's paper says so, with the Stationery page's link",
   lambda: (j1.get("s739") or {}).get("flow") is True and "/stationery" in (j1.get("s739") or {}).get("go", "") and (j1.get("s739") or {}).get("name") == VAR,
   lambda: j1.get("s739", "no s739"))
s2 = save(V1, VAR, "others")
ck("V2 its Save to Others is refused ('sorted on the Stationery page'); the paper keeps no group",
   lambda: not s2.get("ok") and "sorted on the Stationery page" in (s2.get("error") or "") and (row(V1)["subgroup"] or "") == "", lambda: (s2, row(V1)["subgroup"]))
s3 = save(V1, VAR, "lab")
ck("V3 its Save to NK Pathology is refused too (F-1159: the lane is not moved)",
   lambda: not s3.get("ok") and (row(V1)["lane"] or "clinic") == "clinic", lambda: (s3, row(V1)["lane"]))
M1 = mk("M1", "WALK739 VARITY STATNRS", items=LINES)
j4 = pj(M1)
s4 = save(M1, VAR, "others", st_lines=[{"item": "", "qty": "2", "side": "nk"}])
ts = [x["b"]["id"] for x in st.to_sort(db)]
ck("V4 a misread supplier picked as the listed one: its Save sends it to Stationery & packaging with no lines; the Stationery page offers it",
   lambda: (j4.get("s739") or {}).get("could") is True and s4.get("ok") and (row(M1)["subgroup"] or "") == "stationery" and row(M1)["vendor"] == VAR
   and not st.saved_lines(db, row(M1)) and M1 in ts and "Stationery page" in s4.get("message", ""), lambda: (j4.get("s739"), s4, row(M1)["subgroup"], M1 in ts))
V11P = mk("VB", VAR, doc_kind="", items=LINES)
s13 = save(V11P, VAR, "lab", kind="bill")
ck("V11 a Variety challan with a kind pre-chosen from the reading (bill) is refused too; it stays on the clinic lane",
   lambda: not s13.get("ok") and (row(V11P)["lane"] or "clinic") == "clinic" and (row(V11P)["doc_kind"] or "") == "", lambda: (s13, row(V11P)["lane"]))
FIRST = mk("VF", "WALK739 JASORIA BROTHERS", items=LINES)
AS = mk("VA", VAR, lane="lab_purchase", status="rejected", dup_of=FIRST, dup_flag="yes", approved_by=sd.S441_WHO,
        approved_at="2031-05-10 06:00", kind="Lab", items=LINES)
s14 = save(AS, VAR, "others", flag="restore")
ck("V12 a set-aside Variety challan already sorted to NK, restored on the desk: the answer stands, it stays on the NK lane",
   lambda: s14.get("ok") and "stays where it is" in s14.get("message", "") and row(AS)["lane"] == "lab_purchase" and not row(AS)["dup_of"],
   lambda: (s14, row(AS)["lane"], row(AS)["subgroup"]))
LF = mk("LF", VAR, items=LINES)
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (st.LEFT_KEY, ((db.execute("SELECT value FROM settings WHERE key=?", (st.LEFT_KEY,)).fetchone() or [""])[0] + "|%d" % LF).strip("|")))
db.commit()
s15 = save(LF, VAR, "others")
ck("K8 a Variety paper he left as it is on the Stationery page is sorted on the desk as before",
   lambda: s15.get("ok") and (row(LF)["subgroup"] or "") == "others", lambda: s15)
setsw(True)
Y1 = mk("Y1", "WALK739 YUVIKA SURGICALS", doc_kind="", items=(("WALK739 GLOSTER 5 INCH", 4), ("WALK739 ZIG ZAG COTTON", 2)))
j5 = pj(Y1)
ck("V5 switch ON: Yuvika's handwritten slip (no number) opens with Procedure room chosen and the S739 line",
   lambda: j5.get("dest") == "procedure" and "handwritten slip" in j5.get("dest_line", "") and (j5.get("s739") or {}).get("yuv") == "slip"
   and j5.get("pr") is not None, lambda: (j5.get("dest"), j5.get("dest_line"), j5.get("s739")))
Y2 = mk("Y2", "WALK739 YUVIKA SURGICALS", doc_kind="bill", bill_no="YS/W739/1", total_amount=1380, items=(("WALK739 SHOULDER IMMOBILIZER", 2),))
j6 = pj(Y2)
ck("V6 switch ON: her printed bill (a bill number) opens with Pharmacy (Sanjeevni) chosen",
   lambda: j6.get("dest") == "pharmacy" and "printed bill" in j6.get("dest_line", "") and (j6.get("s739") or {}).get("yuv") == "bill", lambda: (j6.get("dest"), j6.get("s739")))
Y3 = mk("Y3", "WALK739 YUVIKA SURGICALS", doc_kind="")
j7 = pj(Y3)
ck("V7 switch ON: no number and no line read: nothing is chosen, the page's two buttons ('unread')",
   lambda: j7.get("dest") == "" and (j7.get("s739") or {}).get("yuv") == "unread", lambda: (j7.get("dest"), j7.get("s739")))
lst = own.get("/desk/api/list").get_json(silent=True) or {}
hint = {p["id"]: p.get("hint") for p in lst.get("papers", [])}
ck("V8 the waiting list names it: 'Yuvika — handwritten slip: Procedure room suggested'",
   lambda: hint.get(Y1) == "Yuvika — handwritten slip: Procedure room suggested", lambda: hint.get(Y1))
ck("V9 the owner's Switches card carries 'Yuvika slips on the desk'",
   lambda: "Yuvika slips on the desk" in dict(sd.SWITCHES).values() and "desk.yuvika" in sd.switch_states(db))
s10 = save(Y1, "WALK739 YUVIKA SURGICALS", "procedure", kind="estimate")
ck("K1 a Yuvika slip saves to the Procedure room", lambda: s10.get("ok") and (row(Y1)["subgroup"] or "") == "procedure", lambda: s10)
setsw(False)
Y4 = mk("Y4", "WALK739 YUVIKA SURGICALS", doc_kind="", items=(("WALK739 GLOSTER 5 INCH", 4),))
j8 = pj(Y4)
ck("K2 switch OFF: a Yuvika slip opens as before -- nothing chosen, 'a person always chooses'",
   lambda: j8.get("dest") == "" and any("a person always chooses" in h for h in j8.get("hints", [])), lambda: (j8.get("dest"), j8.get("hints")))
setsw(True)
Y5 = mk("Y5", "WALK739 YUVIKA SURGICALS", doc_kind="", sub="others", items=(("WALK739 GLOSTER 5 INCH", 4),))
j9 = pj(Y5)
ck("V10 switch ON: a place a person gave it stays (Others: 'Where it is now.')", lambda: j9.get("dest") == "others" and j9.get("dest_line") == "Where it is now.", lambda: (j9.get("dest"), j9.get("dest_line")))
setsw(False)
OLD = mk("OL", VAR, created="2026-10-01 05:00:00", items=LINES)
s11 = save(OLD, VAR, "others")
ck("K4 a listed supplier's challan from before the start day saves on the desk as before", lambda: s11.get("ok") and (row(OLD)["subgroup"] or "") == "others", lambda: s11)
OT = mk("OT", "WALK739 JASORIA BROTHERS", items=LINES)
s12 = save(OT, "WALK739 JASORIA BROTHERS", "others")
ck("K5 any other supplier's challan saves to Others as before", lambda: s12.get("ok") and (row(OT)["subgroup"] or "") == "others", lambda: s12)
ck("K6 the desk's list and the sorting desk still open", lambda: own.get("/desk/api/list").status_code == 200 and own.get("/desk").status_code == 200)
page = own.get("/desk").get_data(as_text=True)
ck("K7 the desk page renders whole (its script and the Save button)", lambda: "id=save" in page and "function paint2" in page)
db.close()

if EXPECT_RED:
    red = [k for k in MUST_RED if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S739 checks red; K green %d of %d" % (len(red), len(MUST_RED), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST_RED) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("APP WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
