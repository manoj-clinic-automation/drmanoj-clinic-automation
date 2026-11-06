#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s737_app.py -- S737_RECENT_SCANS on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given asset_register.py (the kit's TO -- or the live FROM for the control), on a COPY of a database (SQLite's backup
API). Made-up rows only: papers stamped Z-2031-7*, suppliers 'WALK737 ...', a made-up owner login. The reader is off; nothing is
sent. The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s737_app.py --live <the app folder> --files <folder holding asset_register.py> [--db <assets.db>] [--expect-red]
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
KIT_FILES = ("asset_register.py",)
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
MUST_RED = ("A0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s737app_")
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
            if "NOT mounted" in l or "S737" in l or "Traceback" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S737_WALK_DEBUG"):
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
ck("A0 the real app loads with its seven parts mounted; asset_register.py is S737's (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and getattr(ar, "RECENT_S737", "") == "S737")
ar.S737_NOW = "2031-06-05 08:00:00"                                  # made-up now: 05-Jun-2031 13:30 IST
import datetime as _dt                                                # noqa: E402
sys.modules["sorting_desk"]._today = lambda: _dt.date(2031, 6, 5)     # the desk's own clock on the same made-up day
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-01-01')")   # the copy only: a made-up desk floor
db.execute("DELETE FROM settings WHERE key='recent.on'")                                  # installed OFF
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
for u, role in (("walk_own_s737", "owner"), ("walk_mgr_s737", "manager")):
    if not db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
        db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]


def client(u):
    c = ar.app.test_client()
    with c.session_transaction() as ss:
        ss["uid"] = db.execute("SELECT id FROM users WHERE username=?", (u,)).fetchone()[0]
        ss["epoch"] = epoch
    return c


own, mgr = client("walk_own_s737"), client("walk_mgr_s737")
SEQ = [0]


def mk(created, vendor="WALK737 SURGICALS", status="draft", lane="clinic", sub="", ocr="read", doc="bill", bill_date="2031-06-01", **cols):
    SEQ[0] += 1
    tag = "%02d" % SEQ[0]
    vals = dict(kind="Pharmacy" if lane == "pharmacy" else "Consumable", vendor=vendor, stamp_no="Z-2031-7" + tag, status=status, lane=lane,
                created_at=created, submitted_at=created[:16], submitted_by="walkscan", doc_kind=doc, bill_no="W737-" + tag,
                bill_date=bill_date, total_amount=100, subgroup=sub, ocr_status=ocr)
    vals.update(cols)
    db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values()))
    db.commit()
    return "Z-2031-7" + tag


def html(c, url):
    r = c.get(url)
    return r.status_code, r.get_data(as_text=True)


def row_of(h, stamp):
    m = re.search(r'<a href="[^"]*" class=s737row[^>]*>(.*?)</a>', h[h.find(stamp) - 900:h.find(stamp) + 900], re.S) if stamp in h else None
    seg = h[h.find(stamp):h.find(stamp) + 700] if stamp in h else ""
    return re.sub(r"<[^>]+>", "|", seg)


def section(h):
    i = h.find("id=s737recent")
    return h[i:h.find("Older scans:", i)] if i >= 0 else ""


# made-up papers (UTC created_at; IST = +5:30)
P_DESK = mk("2031-06-05 07:10:00")                                                   # 12:40 IST today, unsorted draft -> on the desk
P_PH = mk("2031-06-05 06:30:00", vendor="WALK737 PHARMA", status="captured", lane="pharmacy")
P_REJ = mk("2031-06-05 05:00:00", status="rejected")
P_BAD = mk("2031-06-05 04:00:00", vendor="", ocr="failed")
P_PROC = mk("2031-06-04 10:00:00", status="approved", sub="procedure")             # yesterday
P_PERS = mk("2031-06-04 09:00:00", status="approved", sub="personal", lane="owner_expense")
P_LATE = mk("2031-06-04 20:00:00", status="approved", sub="others")                 # UTC 4th, IST 05-Jun 01:30 -> TODAY
P_OLD = mk("2031-05-20 06:00:00", status="approved", sub="others")                  # 16 days back: in 30, not in 14
P_TYPO = mk("2031-06-03 06:00:00", status="approved", sub="others", bill_date="2062-11-25")
_proc_id = db.execute("SELECT id FROM bills WHERE stamp_no=?", (P_PROC,)).fetchone()[0]
P_DUP = mk("2031-06-03 05:00:00", status="rejected", dup_of=_proc_id, dup_flag="yes", approved_by=sys.modules["sorting_desk"].S441_WHO,
           approved_at="2031-06-03 10:31")                       # set aside by the after-the-fact check: the desk lists it to check
_st = sys.modules.get("stationery")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (_st.SUPPLIERS_KEY, _st._skey("WALK737 STATIONERS")))
db.commit()
P_STAT = mk("2031-06-03 04:00:00", vendor="WALK737 STATIONERS", doc="challan")

# OFF (as installed)
c0, h0 = html(own, "/")
b0c, b0 = html(own, "/bills")
ck("K1 switched OFF (as installed): no Recent scans on the home page, no Scanned / Where it sits on All papers, Date heading as before",
   lambda: c0 == 200 and "s737recent" not in h0 and "Recent scans" not in h0 and b0c == 200 and "<th>Scanned</th>" not in b0
   and "Where it sits" not in b0 and "<th>Date</th>" in b0 and "s737order" not in b0, lambda: (c0, b0c))
legacy = [r[0] for r in db.execute("SELECT stamp_no FROM bills b WHERE 1=1 ORDER BY (b.status='draft') DESC, b.bill_date DESC, b.id DESC LIMIT 300")]
seen0 = [s for s in re.findall(r"Z-2031-7\d\d", b0)]
ck("K2 switched OFF: All papers keeps today's order (drafts first, then the printed date)",
   lambda: [s for s in legacy if s and s.startswith("Z-2031-7")] == list(dict.fromkeys(seen0)), lambda: (seen0, [s for s in legacy if s and s.startswith("Z-2031-7")]))
a0c, a0 = html(own, "/admin")
rr = own.post("/admin", data={"action": "set_recent_s737", "on": "1"})
on_now = (db.execute("SELECT value FROM settings WHERE key='recent.on'").fetchone() or [""])[0]
ck("V1 the switch on /admin: a 'Recent scans by scan date' card, OFF; its Switch ON writes recent.on = on",
   lambda: a0c == 200 and "id=s737switch" in a0 and "Now: <b>OFF</b>" in a0[a0.find("id=s737switch"):a0.find("id=s737switch") + 900]
   and rr.status_code in (200, 302) and on_now == "on", lambda: (a0c, rr.status_code, on_now))

# ON
c1, h1 = html(own, "/")
sec = section(h1)
today_i, yday_i = sec.find("Today · Thu 05-Jun"), sec.find("Yesterday · Wed 04-Jun")
ck("V2 home (owner): three counts and Recent scans -- Today / Yesterday groups by IST day, newest first; a 01:30 IST scan is today's",
   lambda: c1 == 200 and "Scanned today" in h1 and "Read failed — scan again" in h1 and today_i >= 0 and yday_i > today_i
   and all(today_i < sec.find(s) < yday_i for s in (P_DESK, P_PH, P_REJ, P_BAD, P_LATE)) and sec.find(P_PROC) > yday_i
   and sec.find(P_DESK) < sec.find(P_PH) < sec.find(P_REJ) < sec.find(P_BAD) < sec.find(P_LATE) and P_OLD not in sec
   and re.search(r"Scanned today</div><b[^>]*>5 papers", h1) and re.search(r"Read failed — scan again</div><b[^>]*>1 paper<", h1),
   lambda: (c1, today_i, yday_i, [sec.find(s) for s in (P_DESK, P_PH, P_REJ, P_BAD, P_LATE, P_PROC)], re.findall(r"Scanned today</div><b[^>]*>[^<]*", h1)))
W = {s: row_of(sec, s) for s in (P_DESK, P_PH, P_REJ, P_BAD, P_PROC, P_PERS)}
ck("V3 each row: time, stamp, supplier, kind, lane, where it sits -- desk / pharmacy / set aside / read failed / Procedure room / Dr MK",
   lambda: "12:40" in sec[sec.find(P_DESK) - 300:sec.find(P_DESK)] and "On the desk — waiting" in W[P_DESK] and "|Clinic|" in W[P_DESK]
   and "|Bill|" in W[P_DESK] and "Filed (pharmacy)" in W[P_PH] and "|Pharmacy|" in W[P_PH] and "Set aside" in W[P_REJ]
   and "Read failed — scan again" in W[P_BAD] and "(not read)" in W[P_BAD] and "Procedure room" in W[P_PROC]
   and "|Dr MK|" in W[P_PERS], lambda: W)
c2, h2 = html(own, "/?rs=30")
c3, h3 = html(own, "/?rf=need")
c4, h4 = html(own, "/?rf=pharmacy")
s3, s4 = section(h3), section(h4)
ck("V4 30 days brings the 16-day-old scan; Needs someone = the desk and the unread; Pharmacy = the pharmacy paper only",
   lambda: P_OLD in section(h2) and P_DESK in s3 and P_BAD in s3 and not any(x in s3 for x in (P_PH, P_REJ, P_PROC, P_LATE))
   and P_PH in s4 and not any(x in s4 for x in (P_DESK, P_BAD, P_PROC)), lambda: (P_OLD in section(h2), re.findall(r"Z-2031-7\d\d", s3), re.findall(r"Z-2031-7\d\d", s4)))
m1, hm = html(mgr, "/")
ck("V5 Shavez's login sees the card but never a Personal paper; the owner sees it",
   lambda: m1 == 200 and "s737recent" in hm and P_DESK in section(hm) and P_PERS not in hm and P_PERS in sec, lambda: (m1, P_PERS in hm))
b1c, b1 = html(own, "/bills")
seen1 = list(dict.fromkeys(re.findall(r"Z-2031-7\d\d", b1)))
want1 = [r[0] for r in db.execute("SELECT stamp_no FROM bills WHERE stamp_no LIKE 'Z-2031-7%' ORDER BY created_at DESC, id DESC")]
ck("V6 All papers (ON): newest scan first, a Scanned column (IST) and Where it sits; the order switch shows",
   lambda: b1c == 200 and "<th>Scanned</th>" in b1 and "<th>Where it sits</th>" in b1 and "<th>Bill date</th>" in b1 and "id=s737order" in b1
   and seen1 == want1 and "05-06-2031 12:40" in b1 and "05-06-2031 01:30" in b1, lambda: (b1c, seen1, want1))
b2c, b2 = html(own, "/bills?order=bill")
seen2 = list(dict.fromkeys(re.findall(r"Z-2031-7\d\d", b2)))
ck("V7 'Bill date' gives today's order back (drafts first, then the printed date -- the 2062 typo near the top), columns kept",
   lambda: b2c == 200 and seen2 == [s for s in legacy if s and s.startswith("Z-2031-7")] and "<th>Scanned</th>" in b2
   and "By the date printed on the bill" in b2, lambda: (seen2,))
s1 = section(h1)
ck("V8 a confirmed second scan the desk lists to check reads 'On the desk — waiting' and is under Needs someone",
   lambda: "On the desk — waiting" in row_of(s1, P_DUP) and P_DUP in s3, lambda: (row_of(s1, P_DUP), P_DUP in s3))
ck("V9 a listed supplier's challan reads 'Stationery page'", lambda: "Stationery page" in row_of(s1, P_STAT), lambda: row_of(s1, P_STAT))
mb, bm = html(mgr, "/bills")
ck("V10 Shavez's All papers (ON): the new columns, and never a Personal paper",
   lambda: mb == 200 and "<th>Scanned</th>" in bm and P_DESK in bm and P_PERS not in bm and P_PERS in b1, lambda: (mb, P_PERS in bm))
ck("K3 the sorting desk, the Stationery page and reception's intake still open",
   lambda: own.get("/desk").status_code == 200 and own.get("/stationery").status_code == 200 and own.get("/intake").status_code in (200, 302))
db.close()

if EXPECT_RED:
    red = [k for k in MUST_RED if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S737 checks red; K green %d of %d" % (len(red), len(MUST_RED), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST_RED) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("APP WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
