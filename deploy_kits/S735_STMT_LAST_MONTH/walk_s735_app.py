#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s735_app.py -- S735_STMT_LAST_MONTH on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given stationery.py (the kit's TO -- or the live FROM for the control), on a COPY of a database (SQLite's backup
API). Made-up rows only: papers stamped Z-2031-9*, suppliers 'WALK735 ...', a made-up owner login. The reader is off; nothing is
sent. The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s735_app.py --live <the app folder> --files <folder holding stationery.py> [--db <assets.db>] [--expect-red]
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
MUST_RED = ("A0", "V1", "V2", "V6")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s735app_")
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
            if "NOT mounted" in l or "S735" in l or "Traceback" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S735_WALK_DEBUG"):
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


import datetime                                                      # noqa: E402
import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
st = mods.get("stationery")
ck("A0 the real app loads with its seven parts mounted; stationery.py is S735's (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and getattr(st, "STMT_LAST", "") == "S735")
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):                                     # a fresh database (the rehearsal) lacks what the live one has
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s735'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s735','Walk owner','owner','x',1)")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_own_s735'").fetchone()[0]
    ss["epoch"] = epoch
own.get("/stationery")                                               # the first request: S568's and S674's tables made (additive)
try:                                                                 # the live shape, counts only (no name, no amount): what the page will offer today
    with ar.app.test_request_context("/stationery"):
        f0 = st.flow_view(db, st._ym())
    if f0.get("prev_first"):
        print("LIVE SHAPE (counts only): %d listed supplier(s); the page will offer %s's statement first -- %d lines on %d papers"
              % (len(f0["sups"]), ar._month_label(f0["prev"]), len(f0["prev_pending"]), len(f0["prev_pending_papers"])))
    else:
        print("LIVE SHAPE (counts only): %d listed supplier(s); no last-month statement offered; this month's: %d lines on %d papers"
              % (len(f0["sups"]), len(f0["pending"]), len(f0["pending_papers"])))
except Exception as e:                                               # noqa: BLE001
    print("LIVE SHAPE: not read -- %r" % e)
SEQ = [0]


def supplier(name, today):
    """Made-up: this supplier is the ONLY listed one, and 'today' is fixed (the copy only)."""
    key = st._skey(name)
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (st.SUPPLIERS_KEY, key))
    db.commit()
    st.TODAY = today
    return key


def paper(name, day, lines):
    SEQ[0] += 1
    tag = "%02d" % SEQ[0]
    ca = "%s 05:%s:00" % (day, tag)
    vals = dict(kind="Consumable", vendor=name, stamp_no="Z-2031-9" + tag, status="draft", lane="clinic", created_at=ca,
                submitted_at=ca[:16], submitted_by="walkscan", doc_kind="challan", bill_no="W735-" + tag, bill_date=day,
                total_amount=0, subgroup="stationery", ocr_status="read")
    bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
    for i, (n, q) in enumerate(lines, 1):
        db.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, rate, day, ts, by_whom, at, side) "
                   "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (bid, ca, i, n, q, "piece", None, day, 0, "walk", ca, "clinic"))
    db.commit()
    return bid, "W735-" + tag


def page():
    r = own.get("/stationery")
    return r.status_code, r.get_data(as_text=True)


def prev_ym_of(html):
    m = re.search(r'<form[^>]*id=s735prev[^>]*>\s*<input type=hidden name=ym value="([0-9-]+)"', html)
    return m.group(1) if m else None


def make(ym):
    return own.post("/stationery/statement/make", data={"ym": ym}).status_code


def stmts(key):
    return [dict(r) for r in db.execute("SELECT * FROM stationery_stmt WHERE supplier=? AND voided_at='' ORDER BY id", (key,))]


def lines_of(bid):
    return [dict(r) for r in db.execute("SELECT * FROM stationery_line WHERE bill_id=? AND voided_at='' ORDER BY line_no", (bid,))]


# 1 -- the month just ended has lines, no statement stands: it is offered first (today 05-Jun-2031)
K1 = supplier("WALK735 ALPHA STATIONERS", datetime.date(2031, 6, 5))
A, An = paper("WALK735 ALPHA STATIONERS", "2031-04-20", [("Walk735 register", 2), ("Walk735 file", 1)])
B, Bn = paper("WALK735 ALPHA STATIONERS", "2031-05-03", [("Walk735 ream", 2)])
C, Cn = paper("WALK735 ALPHA STATIONERS", "2031-06-02", [("Walk735 slip book", 5)])
code, h = page()
ck("V1 last month first: 'Make May 2031's statement' (3 lines on 2 papers up to its end; June's after it), no June button",
   lambda: code == 200 and prev_ym_of(h) == "2031-05" and "Make May 2031&#39;s statement" in h.replace("'", "&#39;")
   and "3 lines on 2 papers up to its end ready" in h and "June 2031&#39;s comes after it." in h.replace("'", "&#39;")
   and "Make June 2031" not in h and "Monthly statement — May 2031" in h,
   lambda: (code, prev_ym_of(h), re.findall(r"Make [A-Za-z]+ \d{4}", h)))
ym = prev_ym_of(h) or ""
rc = make(ym) if ym else None
s = stmts(K1)
ck("V2 the page's own button makes May's: April's and May's lines on it (April's named earlier), June's line left unbilled",
   lambda: rc == 302 and len(s) == 1 and s[0]["ym"] == "2031-05" and all(l["stmt_id"] == s[0]["id"] for l in lines_of(A) + lines_of(B))
   and all(l["stmt_id"] is None for l in lines_of(C)) and (An + " · 20-04-2031" in s[0]["text"] or An in s[0]["text"])
   and "earlier, not billed yet" in [x for x in s[0]["text"].splitlines() if An in x][0]
   and "earlier" not in [x for x in s[0]["text"].splitlines() if Bn in x][0] and Cn not in s[0]["text"],
   lambda: (rc, s and s[0]["ym"], s and s[0]["text"][:400]))
code, h = page()
ck("V3 once May's stands: no last-month button; June's button as before (1 line on 1 paper); the header names May's statement",
   lambda: code == 200 and prev_ym_of(h) is None and "Make June 2031" in h and "1 line on 1 paper ready" in h
   and "Monthly statement — May 2031" in h, lambda: (code, prev_ym_of(h), re.findall(r"Make [A-Za-z]+ \d{4}", h)))

# 2 -- nothing in the month just ended: the page is as before
K2 = supplier("WALK735 BETA STATIONERS", datetime.date(2031, 6, 5))
paper("WALK735 BETA STATIONERS", "2031-06-01", [("Walk735 ream", 1)])
code, h = page()
ck("K1 no lines in the month just ended: only 'Make June 2031's statement', exactly as before (header June)",
   lambda: code == 200 and prev_ym_of(h) is None and "Make June 2031" in h and "Make May 2031" not in h and "Monthly statement — June 2031" in h,
   lambda: (code, re.findall(r"Make [A-Za-z]+ \d{4}", h)))

# 3 -- this month's statement already stands: a late May line never brings the May button back
K3 = supplier("WALK735 GAMMA STATIONERS", datetime.date(2031, 6, 5))
paper("WALK735 GAMMA STATIONERS", "2031-06-01", [("Walk735 ream", 1)])
r3 = make("2031-06")
G, Gn = paper("WALK735 GAMMA STATIONERS", "2031-05-28", [("Walk735 file", 3)])
code, h = page()
ck("K2 June's already stands: a May line sorted late does not bring a May button; no make button at all",
   lambda: r3 == 302 and code == 200 and prev_ym_of(h) is None and "Make May 2031" not in h and "Make June 2031" not in h
   and len(stmts(K3)) == 1, lambda: (r3, code, re.findall(r"Make [A-Za-z]+ \d{4}", h)))

# 4 -- the year's turn: in January, December is the month just ended
K4 = supplier("WALK735 DELTA STATIONERS", datetime.date(2032, 1, 10))
paper("WALK735 DELTA STATIONERS", "2031-12-15", [("Walk735 register", 4)])
code, h = page()
ck("V6 the year's turn: on 10-Jan-2032 the page offers 'Make December 2031's statement'",
   lambda: code == 200 and prev_ym_of(h) == "2031-12" and "Make December 2031" in h and "Make January 2032" not in h,
   lambda: (code, prev_ym_of(h), re.findall(r"Make [A-Za-z]+ \d{4}", h)))

# keep -- what must not change
K5 = supplier("WALK735 EPSILON STATIONERS", datetime.date(2031, 6, 5))
E, En = paper("WALK735 EPSILON STATIONERS", "2031-05-10", [("Walk735 ream", 2)])
r5 = make("2031-06")
ck("K3 the make door is unchanged: a month posted by hand (June) takes every unbilled line up to its end, May's too",
   lambda: r5 == 302 and [x["ym"] for x in stmts(K5)] == ["2031-06"] and all(l["stmt_id"] for l in lines_of(E)),
   lambda: (r5, stmts(K5)))
r6 = make("2031-06")
ck("K4 a second statement for the same month is still refused (one statement per month)", lambda: r6 == 302 and len(stmts(K5)) == 1)
ck("K5 the staff sort screen and the scan app's home still open",
   lambda: own.get("/stationery/sort").status_code == 200 and own.get("/").status_code in (200, 302))
db.close()

if EXPECT_RED:
    red = [k for k in MUST_RED if not RES.get(k)]
    kg = [k for k in RES if k.startswith("K") and RES[k]]
    kn = [k for k in RES if k.startswith("K")]
    print("CONTROL: %d of %d S735 checks red; K green %d of %d" % (len(red), len(MUST_RED), len(kg), len(kn)))
    sys.exit(0 if len(red) == len(MUST_RED) and len(kg) == len(kn) else 1)
bad = [k for k, v in RES.items() if not v]
print("APP WALK: %d of %d green" % (len(RES) - len(bad), len(RES)))
sys.exit(0 if not bad else 1)
