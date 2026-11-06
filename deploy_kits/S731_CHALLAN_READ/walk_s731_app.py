#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s731_app.py -- S731_CHALLAN_READ on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch folder
with the given asset_register.py and sorting_desk.py (the kit's TO -- or the live FROM for the control), on a COPY of a database
(SQLite's backup API). Made-up rows only: papers stamped Z-2031-7*, suppliers 'WALK731 ...', a made-up owner login, made-up scan
files in the scratch uploads. The reader is ON in the scratch copy but Claude is never called: read_bill and lie_pass are replaced
in the scratch process by a stand-in that records which paper was put to it. The scratch folder is removed at the end; the database
given is only read (copied).

    python3 -B walk_s731_app.py --live <the app folder> --files <folder holding the two files> [--db <assets.db>] [--expect-red]
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
KIT_FILES = ("asset_register.py", "sorting_desk.py")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
MUST_RED = ("A0", "V1", "V2", "V3", "V4", "V5")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s731app_")
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
            if "NOT mounted" in l or "S731" in l or "Traceback" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S731_WALK_DEBUG"):
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


import time                                                          # noqa: E402
import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
sd = mods.get("sorting_desk")
ck("A0 the real app loads with its seven parts mounted; both files are S731's and the lane button is wrapped (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and getattr(ar, "CHALLAN_READ_S731", "") == "S731" and getattr(sd, "CHALLAN_READ", "") == "S731"
   and getattr(ar.app.view_functions.get("bill_lane"), "_s731", False))
dbp = os.environ["ASSETS_DB"]
UP = os.environ["ASSETS_UPLOADS"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','on')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.sarvam','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):                                     # a fresh database (the rehearsal) lacks what the live one has
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s731'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s731','Walk owner','owner','x',1)")
db.execute("CREATE TABLE IF NOT EXISTS claude_reading(bill_id INTEGER PRIMARY KEY, at TEXT NOT NULL, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT)")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]

ASKED = []                                                           # the stand-in: which paper was put to "Claude"


def fake_read_bill(path, bid=None, db_path=None):
    ASKED.append(bid)
    c = sqlite3.connect(dbp, timeout=20)
    c.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data, error) VALUES(?, '2031-05-12 10:00:00', 'walk', 1, 'challan', '{}', NULL)", (bid,))
    c.commit()
    c.close()
    return {"vendor": "WALK731 READ CO", "bill_no": "W731", "bill_date": "2031-05-12", "total_amount": "50"}, [{"name": "Walk731 Register", "qty": "2"}]


ar.CLAUDE.read_bill = fake_read_bill
ar.CLAUDE.lie_pass = lambda *a, **k: "skipped"
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_own_s731'").fetchone()[0]
    ss["epoch"] = epoch


def mk(tag, lane, dk, ocr="failed", reading=None, **cols):
    stored = "walk731_%s.pdf" % tag
    open(os.path.join(UP, stored), "wb").write(b"%PDF-1.4 made-up walk scan\n")
    vals = dict(kind={"clinic": "Consumable", "other_doc": "Document"}[lane], stamp_no="Z-2031-7" + tag, status="draft" if lane == "clinic" else "captured",
                lane=lane, created_at="2031-05-10 05:00:00", submitted_at="2031-05-10 05:00", submitted_by="walkscan", doc_kind=dk,
                ocr_status=ocr, source_stored=stored)
    vals.update(cols)
    bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
    if reading is not None:
        db.execute("INSERT INTO claude_reading(bill_id, at, model, ok, error) VALUES(?, '2031-05-10 05:01:00', 'walk', ?, ?)", (bid, reading, None if reading else "photo too large to send"))
    db.commit()
    return bid


def row(bid):
    return db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()


def waited(bid, s=6.0):
    t = time.time()
    while time.time() - t < s:
        if bid in ASKED and (row(bid)["ocr_status"] or "") != "reading":
            return True
        time.sleep(0.1)
    return bid in ASKED


def not_asked(bid, s=1.5):
    time.sleep(s)
    return bid not in ASKED


def save(bid, **kw):
    body = dict(id=bid, vendor="WALK731 PLAIN CO", bill_no="W731-%d" % bid, bill_date="2031-05-12", total_amount="50", kind="bill", dest="stationery", who="mk", flag="", joins=[])
    body.update(kw)
    r = own.post("/desk/api/save", data=json.dumps(body), content_type="application/json")
    return r.get_json(silent=True) or {"ok": False, "error": "status %s" % r.status_code}


CH = mk("CH", "other_doc", "challan")
LT = mk("LT", "other_doc", "bill")
PS = mk("PS", "other_doc", "challan", subgroup="personal")
RS = mk("RS", "other_doc", "challan", subgroup="resume")
PP = mk("PP", "other_doc", "challan", subgroup="patient_paper")
ck("V1 a challan on Other document is one Claude is asked to read", lambda: ar._s601_asked(CH) is True)
ck("K1 still never asked: a letter on Other document, a challan in Personal, in Resumes, a patient's paper",
   lambda: not any(ar._s601_asked(b) for b in (LT, PS, RS, PP)), lambda: [ar._s601_asked(b) for b in (LT, PS, RS, PP)])
st = ar._bg_extract(CH, os.path.join(UP, row(CH)["source_stored"]))
ck("V2 the scan's own read (_bg_extract) puts the Other-document challan to Claude and fills it (B-0250's case)",
   lambda: CH in ASKED and st == "read" and row(CH)["vendor"] == "WALK731 READ CO" and row(CH)["lane"] == "other_doc",
   lambda: (st, CH in ASKED, dict(row(CH))["vendor"], row(CH)["lane"]))
st2 = ar._bg_extract(LT, os.path.join(UP, row(LT)["source_stored"]))
ck("K2 a letter on Other document is still not put to Claude by the scan's read", lambda: LT not in ASKED and st2 == "failed", lambda: (st2, LT in ASKED))

M1 = mk("M1", "other_doc", "bill")                                   # never put to Claude (the old lane rule), then sorted on the desk
s1 = save(M1)
ck("V3 the desk's Save moves a never-read paper off Other document into Stationery and it is read then, audited read_after_move",
   lambda: s1.get("ok") and waited(M1) and row(M1)["vendor"] and db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='read_after_move'", (M1,)).fetchone(),
   lambda: (s1, M1 in ASKED, dict(row(M1)).get("ocr_status")))
M2 = mk("M2", "other_doc", "bill")
r2 = own.post("/bills/%d/lane" % M2, data={"lane": "clinic", "back": "/"})
ck("V4 the lane button moves a never-read paper to the clinic lane and it is read then",
   lambda: r2.status_code in (302, 303) and row(M2)["lane"] == "clinic" and waited(M2), lambda: (r2.status_code, row(M2)["lane"], M2 in ASKED))
M7 = mk("M7", "clinic", "bill")                                      # on the clinic lane, failed, never put to Claude (the reader was stopped)
s7 = save(M7)
ck("V5 a never-read paper already on the clinic lane is read after its desk Save", lambda: s7.get("ok") and waited(M7), lambda: (s7, M7 in ASKED))
M3 = mk("M3", "clinic", "bill", reading=0)                           # Claude tried and failed (a photo too large)
s3 = save(M3)
ck("K3 a paper Claude already tried and failed on is NOT re-read by a Save", lambda: s3.get("ok") and not_asked(M3), lambda: (s3, M3 in ASKED))
M4 = mk("M4", "clinic", "bill", ocr="read", reading=1)
s4 = save(M4)
ck("K4 a paper already read is NOT re-read by a Save", lambda: s4.get("ok") and not_asked(M4, 0.5), lambda: (s4, M4 in ASKED))
M6 = mk("M6", "other_doc", "bill")
s6 = save(M6, dest="personal")
ck("K5 a paper sorted into Personal is NOT put to Claude", lambda: s6.get("ok") and not_asked(M6), lambda: (s6, M6 in ASKED))
db.execute("UPDATE settings SET value='off' WHERE key='read.claude'"); db.commit()
M5 = mk("M5", "other_doc", "bill")
s5 = save(M5)
ck("K6 the reader switched off: a never-read paper sorted on the desk is NOT put to Claude", lambda: s5.get("ok") and not_asked(M5), lambda: (s5, M5 in ASKED))
db.execute("UPDATE settings SET value='on' WHERE key='read.claude'"); db.commit()
ck("K7 the desk's list and the sorting desk still open", lambda: own.get("/desk/api/list").status_code == 200 and own.get("/desk").status_code == 200)
db.close()

if EXPECT_RED:
    red = [k for k in MUST_RED if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S731 checks red; K green %d of %d" % (len(red), len(MUST_RED), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST_RED) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("APP WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
