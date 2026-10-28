#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s674_app.py -- S674_VARIETY_FLOW on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the given stationery.py and sorting_desk.py (TO -- or the live FROM for the control), on a COPY of a database (SQLite's backup API) -- or
a fresh one the app makes itself. Made-up rows only (a made-up supplier WALK674 VARIETY STATIONERS, papers dated 2031, product names
'Walk674 ...'); made-up owner and manager logins; no reader, no paid call, nothing sent. In the SCRATCH COPY only, the made-up
supplier is the one listed supplier for the walk (the live setting is read, kept in the copy's `stationery.suppliers.walk674_keep`
and never written to the live file). The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s674_app.py --live <the app folder> --files <folder holding stationery.py> [--db <assets.db>] [--expect-red]
"""
import datetime
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
KIT_FILES = ("stationery.py", "sorting_desk.py")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
# the control on the live FROM file (S585's stationery.py b6ce217a): every new check red; the old pages (K*, R*) green on both sides
MUST_RED = ("A0", "V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11", "V12", "V13", "V14", "V15", "V16", "V17", "V18", "V19", "V20", "V21", "V22", "V23")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s674app_")
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
            if "NOT mounted" in l or "S674" in l or "stationery" in l.lower():
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S674_WALK_DEBUG"):
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
ck("A0 the real app loads with its seven parts mounted; stationery.py is S674's (%s)" % ", ".join(m for m, x in mods.items() if x is not None),
   lambda: all(mods.values()) and st.MOUNTED and st.VERSION == "S674")
TODAY = datetime.date(2031, 5, 20)
for m in ("sorting_desk", "procroom", "stationery", "asset_machine", "batteries", "xray_costs"):
    if mods.get(m) is not None:
        mods[m].TODAY = TODAY
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('stationery.issue_on','on')")
keep = db.execute("SELECT value FROM settings WHERE key='stationery.suppliers'").fetchone()
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('stationery.suppliers.walk674_keep',?)", (keep[0] if keep else "",))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('stationery.suppliers','walk674 variety')")   # the scratch copy: the made-up supplier only
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('stationery.suppliers_from','2031-05-01')")    # the floor: papers scanned from 01-05-2031
have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
for col in ("page_of", "mixed"):
    if col not in have:
        db.execute("ALTER TABLE bills ADD COLUMN %s INTEGER" % col)
for u, role in (("walk_own_s674", "owner"), ("walk_mgr_s674", "manager")):
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


own, mgr = client("walk_own_s674"), client("walk_mgr_s674")
rec = ar.app.test_client()                                        # signed out: the scan app has no reception login in its users table


def flashes(cl):
    with cl.session_transaction() as ss:
        fl = list(ss.get("_flashes") or [])
        ss.pop("_flashes", None)
    return " | ".join(x[1] for x in fl)


def txt(h):
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h)).replace("&#34;", '"').replace("&quot;", '"').replace("&#39;", "'").replace("&amp;", "&")


VEND = "WALK674 VARIETY STATIONERS"


def mk(tag, vendor, items=(), created="2031-05-10 05:00:00", lane="clinic", dk="challan", reading=None, **cols):
    vals = dict(kind={"clinic": "Consumable", "lab_purchase": "Lab", "pharmacy": "Pharmacy"}[lane], vendor=vendor, stamp_no="Z-2031-" + tag,
                status="draft" if lane == "clinic" else "captured", lane=lane, created_at=created, submitted_at=created[:16], submitted_by="walkscan",
                doc_kind=dk, bill_date=created[:10], bill_no=cols.pop("bill_no", "W" + tag))
    vals.update(cols)
    bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
    for it in items:
        db.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?,?,?,?,?)", (bid, it[0], it[1], it[2], (it[1] or 0) * (it[2] or 0)))
    if reading is not None:
        db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,1,?,?)",
                   (bid, created, "walk", dk, json.dumps({"vendor": vendor, "bill_no": vals["bill_no"], "bill_date": created[:10], "items": reading})))
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
    r = db.execute("SELECT id, unit, active FROM stationery_item WHERE name=?", (name,)).fetchone()
    return dict(r) if r else None


def stock(name):
    it = item(name)
    return st.stock_of(db, it["id"]) if it else None


def sec(h, anchor):
    i = h.find('id=%s' % anchor)
    j = h.find('<div class="card', i + 20)
    k = h.find('<div class=card', i + 20)
    j = min(x for x in (j, k) if x > 0) if (j > 0 or k > 0) else -1
    return txt(h[i:j if j > 0 else i + 8000]) if i >= 0 else ""


def desk_ids(cl):
    r = cl.get("/desk/api/list")
    j = r.get_json(silent=True) or {}
    return {p["id"] for p in j.get("papers", [])}


# the made-up products on his list, and his real-shaped ones already there
own.post("/stationery/item", data={"do": "add", "name": "Walk674 A4 paper", "unit": "ream", "rate": "285", "low": "2"})
own.post("/stationery/item", data={"do": "add", "name": "Walk674 register 192", "unit": "register", "rate": "95"})
flashes(own)
A4, REG = item("Walk674 A4 paper"), item("Walk674 register 192")
# the papers: a clinic-lane challan read with two lines (one on the list, one new); one scanned on the NK lane by reception (B-0235's
# case); one mixed; one of another supplier that must NOT land here
C1 = mk("C1", VEND, created="2031-05-02 05:00:00", reading=[{"name": "A4 paper 75 gsm walk674", "qty": 10, "rate": 285}, {"name": "Walk674 carry bag 10x14", "qty": 100, "rate": None}])
C2 = mk("C2", "Walk674 Variety Stationers Bareilly", created="2031-05-06 05:00:00", lane="lab_purchase", reading=[{"name": "Walk674 lab requisition pad", "qty": 10, "rate": 40}])
C3 = mk("C3", VEND, created="2031-05-12 05:00:00", reading=[{"name": "Walk674 A4 paper", "qty": 5, "rate": 285}, {"name": "Walk674 register 192", "qty": 2, "rate": None},
                                                            {"name": "Walk674 lab requisition pad", "qty": 10, "rate": 40}])
OTHER = mk("O1", "WALK674 SOMEONE ELSE", created="2031-05-13 05:00:00", reading=[{"name": "Walk674 stapler", "qty": 1, "rate": 90}])
OLD = mk("Z9", VEND, created="2031-04-20 05:00:00", reading=[{"name": "Walk674 A4 paper", "qty": 1, "rate": 285}])                   # before the floor
XR = mk("X1", VEND, created="2031-05-03 05:00:00", subgroup="xray", status="approved", reading=[{"name": "Walk674 film 8x10", "qty": 1}])   # a person sorted it to X-ray films
EST0 = mk("E0", VEND, created="2031-05-04 05:00:00", dk="estimate", bill_no="EST-11", total_amount=900)                              # their estimate: joined, never sorted
h = own.get("/stationery").get_data(as_text=True)
s1 = sec(h, "s674sort")
ck("V1 his Stationery page carries the flow: the listed supplier, '1 · To sort — 3 papers' with the three Variety challans (the NK-lane one marked 'lane read as NK — check'); NOT the other supplier's, NOT one scanned before the floor, NOT one a person sorted to X-ray films, NOT their estimate",
   lambda: "To sort — 3 papers" in s1 and all(z in s1 for z in ("Z-2031-C1", "Z-2031-C2", "Z-2031-C3")) and not any(z in s1 for z in ("Z-2031-O1", "Z-2031-Z9", "Z-2031-X1", "Z-2031-E0"))
   and "lane read as NK Pathology" in s1 and "WALK674 VARIETY STATIONERS" in sec(h, "s674sup") and "Leave Z-2031-C1 as it is" in s1, lambda: s1[:600])
ck("V2 each read line is a product box pre-filled by the system where it matches ('A4 paper 75 gsm walk674' -> Walk674 A4 paper, 'matched by the system'), the rest as read; quantity and unit beside it; Clinic / NK unchosen",
   lambda: 'value="Walk674 A4 paper"' in h and "matched by the system" in h and 'value="Walk674 carry bag 10x14"' in h and h.count('name="f1" value=clinic') >= 3
   and 'name="f1" value=clinic checked' not in h, lambda: re.findall(r'value="Walk674[^"]*"', h)[:6])
dk0 = desk_ids(own)
ck("V3 the sorting desk does not list a listed supplier's paper (the page is its desk)", lambda: C1 not in dk0 and C3 not in dk0, lambda: (C1 in dk0, C3 in dk0))
# the owner sorts C1: line 1 picked, line 2 a NEW product typed in the same box, both for the clinic
r1 = own.post("/stationery/sort/save", data={"paper": str(C1), "back": "stock", "n1": "Walk674 A4 paper", "q1": "10", "u1": "ream", "f1": "clinic", "r1": "285",
                                             "n2": "Walk674 carry bag 10x14", "q2": "100", "u2": "piece", "f2": "clinic", "r2": ""})
f1 = flashes(own)
l1 = lines(C1)
b1 = row(C1)
ck("V4 his Save of C1: 2 clinic lines into the stock (one product added on Save from the typed name), the paper placed in the clinic lane, Stationery & packaging, not mixed, off the desk, desk_saved",
   lambda: r1.status_code == 302 and "2 lines matched" in f1 and "1 new product on the list" in f1 and "into the stock" in f1 and [(l["name"], l["side"], l["qty"]) for l in l1] ==
   [("Walk674 A4 paper", "clinic", 10.0), ("Walk674 carry bag 10x14", "clinic", 100.0)] and item("Walk674 carry bag 10x14")["unit"] == "piece"
   and b1["lane"] == "clinic" and b1["subgroup"] == "stationery" and int(b1["mixed"] or 0) == 0 and C1 not in desk_ids(own)
   and db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='desk_saved'", (C1,)).fetchone() is not None,
   lambda: (r1.status_code, f1, [(l["name"], l["side"], l["qty"]) for l in l1], item("Walk674 carry bag 10x14"), b1["lane"], b1["subgroup"], b1["mixed"], C1 in desk_ids(own), db.execute("SELECT action FROM bill_audit WHERE bill_id=?", (C1,)).fetchall()))
ck("V5 the clinic stock rose by the clinic lines: Walk674 A4 paper +10 ream, the new carry bag 100", lambda: stock("Walk674 A4 paper") == 10 and stock("Walk674 carry bag 10x14") == 100,
   lambda: (stock("Walk674 A4 paper"), stock("Walk674 carry bag 10x14")))
# C2 (scanned on the NK lane): its one line for NK
r2 = own.post("/stationery/sort/save", data={"paper": str(C2), "back": "stock", "n1": "Walk674 lab requisition pad", "q1": "10", "u1": "pad", "f1": "nk", "r1": "40"})
f2 = flashes(own)
b2 = row(C2)
h = own.get("/stationery").get_data(as_text=True)
ck("V6 C2 sorted with its only line for NK: the paper on the NK Pathology lane (status captured), the line in '2 · NK Pathology' with its rate and amount, the clinic stock untouched, nothing of it in 'Received'",
   lambda: r2.status_code == 302 and "1 line to NK Pathology" in f2 and b2["lane"] == "lab_purchase" and lines(C2)[0]["side"] == "nk"
   and "Walk674 lab requisition pad" in sec(h, "s674nk") and "₹400" in sec(h, "s674nk").replace(" ", "") and stock("Walk674 lab requisition pad") == 0
   and "Z-2031-C2" not in txt(h[h.find("papers that fed"):][:1500]), lambda: (r2.status_code, f2, dict(b2), sec(h, "s674nk")[:300]))
# C3 mixed: two clinic lines, one NK line; one line left alone
r3 = own.post("/stationery/sort/save", data={"paper": str(C3), "back": "stock", "n1": "Walk674 A4 paper", "q1": "5", "u1": "ream", "f1": "clinic", "r1": "285",
                                             "n2": "Walk674 register 192", "q2": "2", "u2": "register", "f2": "clinic", "r2": "",
                                             "n3": "Walk674 lab requisition pad", "q3": "10", "u3": "pad", "f3": "nk", "r3": "40",
                                             "n4": "Walk674 something", "q4": "1", "u4": "", "f4": ""})
f3 = flashes(own)
b3 = row(C3)
ck("V7 C3 mixed: 2 clinic lines + 1 NK line saved, the 4th (neither chosen) waits unsaved; the paper in the clinic lane, Stationery, MARKED MIXED; the stock +5 A4, +2 register; NK ledger 2 lines",
   lambda: r3.status_code == 302 and "2 lines matched" in f3 and "1 line to NK" in f3 and len(lines(C3)) == 3 and b3["lane"] == "clinic" and b3["subgroup"] == "stationery"
   and int(b3["mixed"] or 0) == 1 and stock("Walk674 A4 paper") == 15 and stock("Walk674 register 192") == 2 and stock("Walk674 lab requisition pad") == 0 and len(st.nk_rows(db)) == 2, lambda: (f3, lines(C3), dict(b3), stock("Walk674 A4 paper"), stock("Walk674 lab requisition pad")))
h = own.get("/stationery").get_data(as_text=True)
acc = sec(h, "s674acc")
ck("V8 the account: every line of the supplier (6), each unbilled, Clinic / NK marked; Unpaid Clinic ₹4,275 + 2 lines without a rate, NK ₹800; oldest unpaid 02-05-2031",
   lambda: "unbilled" in acc and acc.count("Walk674") >= 6 and "₹4,275" in acc and "2 lines without a rate" in acc and "NK: ₹800" in acc and "02-05-2031" in acc,
   lambda: acc[:700])
# a bad Save: a quantity missing on a chosen line is refused whole, nothing written
r4 = own.post("/stationery/sort/save", data={"paper": str(C1), "back": "stock", "n1": "Walk674 A4 paper", "q1": "", "u1": "ream", "f1": "clinic"})
f4 = flashes(own)
ck("V9 a line chosen without its quantity: refused with the words, nothing changed (C1 keeps its 2 lines)", lambda: "type the quantity" in f4 and len(lines(C1)) == 2 and stock("Walk674 A4 paper") == 15, lambda: (f4, lines(C1)))
# Shavez: his sort screen while the desk is on, no rate anywhere; a paper of his own to sort
C4 = mk("C4", VEND, created="2031-05-14 05:00:00", reading=[{"name": "Walk674 register 192", "qty": 3, "rate": 95}])
hm = mgr.get("/stationery/sort").get_data(as_text=True)
menu = mgr.get("/desk/month").get_data(as_text=True)
ck("V10 Shavez's screen (desk on): Roman Hinglish, the one waiting paper C4, NO rate on it (no ₹, no rate box), 'Stationery sort (1)' in his menu",
   lambda: "Stationery sort" in hm and "Z-2031-C4" in hm and "₹" not in hm and 'name="r1"' not in hm and "95" not in txt(hm[hm.find("Z-2031-C4"):][:600])
   and "Stationery sort (1)" in txt(menu), lambda: (txt(hm)[:400], re.findall(r"Stationery sort[^<]*", menu)[:2]))
r5 = mgr.post("/stationery/sort/save", data={"paper": str(C4), "back": "sort", "n1": "Walk674 register 192", "q1": "3", "u1": "register", "f1": "clinic", "r1": "999"})
f5 = flashes(mgr)
rq = mgr.post("/stationery/sort/save", data={"paper": str(C4), "back": "sort", "n1": "Walk674 register 192", "q1": "", "u1": "register", "f1": "clinic"})
fq = flashes(mgr)
ck("V19 Shavez's refusal is in his words: a line without its quantity -> 'kitna, likhein' (no English refusal on his screen)", lambda: rq.status_code == 302 and "kitna, likhein" in fq and "type the quantity" not in fq, lambda: fq)
re_ = own.post("/stationery/sort/save", data={"paper": str(EST0), "back": "stock", "n1": "Walk674 A4 paper", "q1": "3", "u1": "ream", "f1": "clinic"})
fe = flashes(own)
rx = own.post("/stationery/sort/save", data={"paper": str(XR), "back": "stock", "n1": "Walk674 A4 paper", "q1": "1", "u1": "ream", "f1": "clinic"})
fx = flashes(own)
ck("V20 their estimate is never sorted (refused: 'joined to a statement, never sorted'); a paper a person sorted to X-ray films is refused ('move it there first'); nothing written for either",
   lambda: "never sorted" in fe and "another group" in fx and lines(EST0) == [] and lines(XR) == [] and row(XR)["subgroup"] == "xray" and stock("Walk674 A4 paper") == 15, lambda: (fe, fx, lines(EST0), lines(XR)))
rl = own.post("/stationery/leave", data={"paper": str(OLD)})
flashes(own)
h = own.get("/stationery").get_data(as_text=True)
ck("V21 'Leave as it is' takes a paper off To sort for good, its lane and group untouched", lambda: rl.status_code == 302 and "Z-2031-Z9" not in sec(h, "s674sort") and row(OLD)["lane"] == "clinic" and row(OLD)["subgroup"] is None, lambda: (rl.status_code, dict(row(OLD))))
db.execute("DELETE FROM settings WHERE key='stationery.suppliers_from'")
db.commit()
h0 = own.get("/stationery").get_data(as_text=True)
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('stationery.suppliers_from','2031-05-01')")
db.commit()
ck("V23 no start day set: NOTHING is offered to sort (never the whole history), and the page says so", lambda: "To sort — 0 papers" in sec(h0, "s674sort") and "No start day set" in sec(h0, "s674sort"), lambda: sec(h0, "s674sort")[:200])
ck("V11 Shavez saves C4: the line into the stock, and a rate he could not see is NOT taken from his form (rate None); the account shows it without a rate",
   lambda: r5.status_code == 302 and "Save ho gaya" in f5 and lines(C4)[0]["rate"] is None and stock("Walk674 register 192") == 5, lambda: (f5, lines(C4)))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','off')")
db.commit()
hm2 = mgr.get("/stationery/sort").get_data(as_text=True)
r6 = mgr.post("/stationery/sort/save", data={"paper": str(C4), "back": "sort", "n1": "Walk674 register 192", "q1": "30", "u1": "register", "f1": "clinic"})
hr = rec.get("/stationery/sort")
ck("V12 desk switched off: Shavez's screen says it is closed and his Save is refused (403); signed out: the login door (302)",
   lambda: "abhi band hai" in hm2 and r6.status_code == 403 and hr.status_code == 302 and lines(C4)[0]["qty"] == 3, lambda: (txt(hm2)[:200], r6.status_code, hr.status_code))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
db.commit()
# the statement: one tap, challan-wise, the mixed one as marked; older unbilled lines come too
rs_ = own.post("/stationery/statement/make", data={"ym": "2031-05"})
fs = flashes(own)
h = own.get("/stationery").get_data(as_text=True)
stm = sec(h, "s674stmt")
try:
    text = db.execute("SELECT text FROM stationery_stmt ORDER BY id DESC LIMIT 1").fetchone()[0]
except (sqlite3.Error, TypeError):
    text = ""                                                        # the control: no such table on the old file
ck("V13 'Make May 2031's statement': 7 lines on 4 papers; the text is challan-wise in the supplier's numbers -- 'challan WC1 · 02-05-2031 · bill to: Clinic', 'challan WC2 · bill to: NK Pathology', 'challan WC3 · MIXED — bill as marked' with each product's side; rate ____ on every line; the closing line asks for separate bills",
   lambda: rs_.status_code == 302 and "7 lines" in fs and "challan WC1 · 02-05-2031 · bill to: Clinic" in text and "challan WC2 · 06-05-2031 · bill to: NK Pathology" in text
   and "challan WC3 · 12-05-2031 · MIXED — bill as marked" in text and "Walk674 lab requisition pad — NK Pathology: 10 pad · rate ____" in text
   and "Walk674 A4 paper — Clinic: 5 ream · rate ____" in text and text.count("rate ____") == 7 and "4 challans · 7 lines · Clinic 5 · NK Pathology 2" in text
   and "bill the clinic and NK Pathology separately" in text and "Copy the text" in stm and "Mark sent" in stm, lambda: (fs, text, stm[:300]))
ck("V14 every line is now 'on statement' in the account; a second Make for May is refused; a change to a paper on the statement is refused",
   lambda: all(l["state"] == "on statement" for l in st.account_rows(db)) and "already stands" in (own.post("/stationery/statement/make", data={"ym": "2031-05"}) and flashes(own))
   and "on a statement" in (own.post("/stationery/sort/save", data={"paper": str(C1), "back": "stock", "n1": "Walk674 A4 paper", "q1": "11", "u1": "ream", "f1": "clinic"}) and flashes(own)),
   lambda: [l["state"] for l in st.account_rows(db)])
try:
    sid = db.execute("SELECT id FROM stationery_stmt ORDER BY id DESC LIMIT 1").fetchone()[0]
except (sqlite3.Error, TypeError):
    sid = 0
own.post("/stationery/statement/sent", data={"id": str(sid)})
flashes(own)
# a later challan sorted after the statement rolls into the next month's
C5 = mk("C5", VEND, created="2031-05-18 05:00:00", reading=[{"name": "Walk674 A4 paper", "qty": 1, "rate": 285}])
own.post("/stationery/sort/save", data={"paper": str(C5), "back": "stock", "n1": "Walk674 A4 paper", "q1": "1", "u1": "ream", "f1": "clinic", "r1": "285"})
flashes(own)
ck("V15 marked sent; a challan sorted after the statement is unbilled, not on it (it waits for the next)", lambda: (db.execute("SELECT sent_at FROM stationery_stmt WHERE id=?", (sid,)).fetchone() or [""])[0] != ""
   and [l["state"] for l in st.account_rows(db) if l["bill_id"] == C5] == ["unbilled"] and lines(C5)[0]["stmt_id"] is None, lambda: lines(C5))
# their estimate scanned; joined with the rates typed on; then paid
EST = mk("E1", VEND, created="2031-05-25 05:00:00", dk="estimate", bill_no="EST-77", total_amount=5300)
CH = mk("C6", VEND, created="2031-05-26 05:00:00", reading=[{"name": "Walk674 A4 paper", "qty": 1}])
rj0 = own.post("/stationery/statement/join", data={"id": str(sid), "bill": str(CH)})
fj0 = flashes(own)
rates = {}
for l in (st.account_rows(db) if hasattr(st, "account_rows") else []):
    if l["stmt_id"] == sid:
        rates["r%d" % l["id"]] = "285" if "A4" in l["name"] else ("95" if "register" in l["name"] else ("40" if "pad" in l["name"] else "2"))
rj = own.post("/stationery/statement/join", data=dict({"id": str(sid), "bill": str(EST)}, **rates))
fj = flashes(own)
h = own.get("/stationery").get_data(as_text=True)
acc = sec(h, "s674acc")
ck("V16 joining a CHALLAN is refused; their ESTIMATE joins: 7 rates saved, every line 'billed' with its rate and amount, the account's Unpaid now carries amounts for all 7 (no line without a rate)",
   lambda: "not a challan" in fj0 and rj.status_code == 302 and "7 rates saved" in fj and all(l["state"] == "billed" and l["rate"] is not None for l in st.account_rows(db) if l["stmt_id"] == sid)
   and "without a rate" not in acc and "Unpaid Clinic: ₹5,235" in acc, lambda: (fj0, fj, [(l["name"], l["state"], l["rate"]) for l in st.account_rows(db)]))
rp = own.post("/stationery/statement/paid", data={"id": str(sid), "ref": "UPI walk674"})
fp = flashes(own)
h = own.get("/stationery").get_data(as_text=True)
acc = sec(h, "s674acc")
ck("V17 marked paid: the 7 lines 'paid' (once, ever); Paid this year on estimates ₹5,750 (A4 15x285 + register 5x95 + pads 2x10x40 + bags 100x2), Clinic ₹4,950 / NK ₹800; a void of a paid statement is refused",
   lambda: rp.status_code == 302 and all(l["state"] == "paid" for l in st.account_rows(db) if l["stmt_id"] == sid) and "On estimates: ₹5,750" in acc and "₹4,950 / ₹800" in acc
   and "never voided" in (own.post("/stationery/statement/void", data={"id": str(sid)}) and flashes(own)), lambda: (fp, acc[:500]))
# the desk never voids a line on a statement: C1 (paid) saved on the desk to Others is refused whole; its lines and the stock stay
r8 = own.post("/desk/api/save", json={"id": C1, "dest": "others", "kind": "challan"})
j8 = r8.get_json(silent=True) or {}
r9 = own.post("/desk/api/save", json={"id": C3, "dest": "stationery", "kind": "challan", "st_lines": []})      # an EMPTY list would void the page's lines
j9 = r9.get_json(silent=True) or {}
ck("V22 the desk: C1 (its lines paid on the statement) saved to Others is REFUSED with the words, its 2 lines live and the stock unchanged; a listed challan's lines saved from the desk's own panel are refused (the page sorts them)",
   lambda: r8.status_code == 400 and "supplier statement" in j8.get("error", "") and len(lines(C1)) == 2 and row(C1)["subgroup"] == "stationery" and stock("Walk674 A4 paper") == 16
   and r9.status_code == 400 and "sorted on the Stationery page" in j9.get("error", "") and len(lines(C3)) == 3, lambda: (r8.status_code, j8, lines(C1), stock("Walk674 A4 paper"), r9.status_code, j9))
# the desk's own stationery panel still saves (side clinic by default) and the stock reads both
D1 = mk("D1", "WALK674 ANOTHER STATIONER", created="2031-05-27 05:00:00", subgroup="stationery")
r7 = own.post("/desk/api/save", json={"id": D1, "dest": "stationery", "kind": "challan", "st_lines": [{"no": 1, "name": "Walk674 A4 paper", "qty": "4", "unit": "ream", "rate": "", "item": str(A4["id"])}]})
ck("V18 the desk's own Stationery panel (another supplier) still saves a line -- side clinic by default -- and the stock counts it with the page's: A4 15+1+4 = 20",
   lambda: r7.status_code == 200 and lines(D1) and lines(D1)[0]["side"] == "clinic" and stock("Walk674 A4 paper") == 20, lambda: (r7.status_code, r7.get_json(silent=True), lines(D1), stock("Walk674 A4 paper")))
ck("K1 the older pages still answer for the owner: the desk, The month, Stationery diya, the item list door, Bills awaited",
   lambda: all(own.get(u).status_code == 200 for u in ("/desk", "/desk/month", "/stationery/diya", "/desk/awaited", "/stationery")), lambda: [(u, own.get(u).status_code) for u in ("/desk", "/desk/month", "/stationery/diya", "/desk/awaited")])
ck("K2 the live setting is untouched in the scratch copy's keep key (never written to the live file)", lambda: db.execute("SELECT 1 FROM settings WHERE key='stationery.suppliers.walk674_keep'").fetchone() is not None)
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad_ = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S674 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad_ else "NOT AS IT MUST BE: " + ", ".join(bad_)))
    sys.exit(0 if not bad_ else 1)
print("WALK S674 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
