#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s651_app.py -- S651_CLEARER_DUPLICATE (D761) on the REAL scan app: asset_register.py and every part it mounts, copied into
a scratch folder with the given asset_register.py / sorting_desk.py, and scan_checks_s441.py in a scratch shared folder; on a COPY
of a database (SQLite's backup API) or a fresh one the app makes itself. MADE-UP papers only (suppliers named WALKSUP S651 ...),
a MADE-UP finance database (never the real one); made-up owner and manager logins; no reader, no paid call, nothing sent; Flask's
test client, no port. The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s651_app.py --live <the app folder> --files <folder holding the three files> [--db <assets.db>] [--expect-red]
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
APP_FILES = ("asset_register.py", "sorting_desk.py")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
MUST_RED = ("A0", "D1", "D4c", "D5", "D6", "D7", "D8", "D9")   # the control on the live files: the swaps red; every "as before" check green

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s651app_")
    try:
        app = os.path.join(work, "app")
        shared = os.path.join(work, "shared")
        os.makedirs(app)
        os.makedirs(shared)
        for f in os.listdir(LIVE):                                   # the app's CODE only (top-level .py / .js / .json) -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in APP_FILES:
            shutil.copy(os.path.join(FILES, f), os.path.join(app, f))
        shutil.copy(os.path.join(FILES, "scan_checks_s441.py"), os.path.join(shared, "scan_checks_s441.py"))
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
        env = dict(os.environ, ASSETS_DB=db, ASSETS_UPLOADS=os.path.join(work, "uploads"), SHARED_LIB_DIR=shared,
                   SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"), SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1",
                   CLINIC_PORTAL_DIR=os.path.join(work, "noportal"), FINANCE_LOCAL_URL="http://127.0.0.1:9",
                   FINANCE_DB_FOR_SCANS=os.path.join(work, "fin.db"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=600)
        sys.stdout.write(r.stdout)
        for l in r.stderr.splitlines():
            if "NOT mounted" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S651_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
APPD = ARGS[ARGS.index("--inner") + 1]
sys.path.insert(0, APPD)
RES = {}
FDB = os.environ["FINANCE_DB_FOR_SCANS"]
f = sqlite3.connect(FDB)                                             # a MADE-UP finance database with the tables that tie a scan
f.executescript("""
CREATE TABLE purchase_bill(id INTEGER PRIMARY KEY, supplier TEXT, bill_no TEXT, scan_bill_id INTEGER);
CREATE TABLE purchase_scan_link(id INTEGER PRIMARY KEY, asset_bill_id INTEGER, purchase_bill_id INTEGER);
CREATE TABLE order_scan_tie(id INTEGER PRIMARY KEY, order_id INTEGER, asset_bill_id INTEGER, stamp TEXT, scan_at TEXT);
CREATE TABLE purchase_scan_alias(id INTEGER PRIMARY KEY, scan_id INTEGER);
CREATE TABLE stock_voucher(id INTEGER PRIMARY KEY, scan_ref TEXT);
""")
f.commit()
f.close()


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
S = ar.S441
ck("A0 the real app loads with its seven parts mounted and the checks are S651's (scan_checks_s441 %s)" % (getattr(S, "VERSION", None),),
   lambda: all(mods.values()) and S is not None and S.VERSION.startswith("S441.2") and hasattr(S, "clearer"))
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
for u, role in (("walk_own_s651", "owner"), ("walk_mgr_s651", "manager")):
    if not db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
        db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u, "Walk " + role, role))
db.commit()
S.ensure(db)
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]


def client(user):
    c = ar.app.test_client()
    uid = db.execute("SELECT id FROM users WHERE username=?", (user,)).fetchone()[0]
    with c.session_transaction() as ss:
        ss["uid"] = uid
        ss["epoch"] = epoch
    return c


own = client("walk_own_s651")


def flashes(cl):
    with cl.session_transaction() as ss:
        fl = list(ss.get("_flashes") or [])
        ss.pop("_flashes", None)
    return " | ".join(x[1] for x in fl)


N = [0]
NOW = datetime.datetime.now()


def mk(tag, items, lane="clinic", status="draft", vendor=None, bill_no=None, total=5360.0, minutes_ago=600, **extra):
    """A made-up scan: its own stamp, a made-up supplier, `items` item lines."""
    N[0] += 1
    st = "W651-%03d" % N[0]
    at = (NOW - datetime.timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M:%S")
    cols = dict(kind="Pharmacy" if lane == "pharmacy" else "Consumable", vendor=vendor or ("WALKSUP S651 %s" % tag), bill_no=bill_no or ("A9%04d" % N[0]),
                total_amount=total, stamp_no=st, status=status, lane=lane, submitted_by="walk", submitted_at=at, ocr_status="read", scanned_by="Walk")
    cols.update(extra)
    cur = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(cols), ",".join("?" * len(cols))), list(cols.values()))
    bid = cur.lastrowid
    for i in range(items):
        db.execute("INSERT INTO bill_items(bill_id, item_name, quantity) VALUES(?,?,?)", (bid, "WALK ITEM %d" % (i + 1), 10))
    if cols.get("ocr_status") == "read":                             # K1 B1: as the reading writes it on EVERY read scan
        db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
                   (bid, at, "", "filled", json.dumps({"by": "claude", "items": items})))
    db.commit()
    return bid


def row(bid):
    return db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()


def verdict(bid):
    r = db.execute("SELECT verdict, other_id, detail FROM scan_check_s441 WHERE bill_id=?", (bid,)).fetchone()
    return tuple(r) if r else None


def audits(bid):
    return [r[0] for r in db.execute("SELECT action FROM bill_audit WHERE bill_id=? ORDER BY id", (bid,))]


def checker_pair(a_items, b_items, **a_extra):
    """The checker's two taps on an amber pair: A (older) and B (newer, amber 'maybe' on A); the owner taps Duplicate on B."""
    tag = "P%d" % (N[0] + 1)
    a = mk(tag, a_items, **a_extra)
    b = mk(tag, b_items, minutes_ago=300)
    db.execute("UPDATE bills SET dup_flag='maybe', dup_cand=?, dup_why='image (walk)' WHERE id=?", (a, b))
    db.commit()
    r = own.post("/bills/%d/dup" % b, data={"what": "yes"})
    return a, b, r.status_code, flashes(own)


def kept_older(a, b):
    ra, rb = row(a), row(b)
    return rb["status"] == "rejected" and rb["dup_of"] == a and ra["status"] != "rejected"


def kept_newer(a, b):
    ra, rb = row(a), row(b)
    return ra["status"] == "rejected" and ra["dup_of"] == b and rb["status"] != "rejected" and (rb["dup_flag"] or "") in ("", "no") \
        and not (rb["dup_flag"] == "maybe" and rb["dup_cand"] == a)                # K1 C5: its amber closed only when it pointed at the one set aside


# D1 -- the case of F-992: the older scan has no item lines, the newer the whole bill
a1, b1, sc1, f1 = checker_pair(0, 3)
sa1, sb1 = row(a1)["stamp_no"], row(b1)["stamp_no"]
ck("D1 the checker's Duplicate on two scans of one paper: the older has no item lines, the newer three -- the NEWER is kept, the older set aside "
   "(dup_of the newer), the words say so, both audited, the verdicts follow",
   lambda: sc1 == 302 and kept_newer(a1, b1) and ("%s kept; %s is set aside as its second scan." % (sb1, sa1)) in f1
   and "kept_clearer" in audits(b1) and "duplicate" in audits(a1) and verdict(a1) and verdict(a1)[0] == "double" and verdict(a1)[1] == b1
   and "D761" in (row(a1)["dup_why"] or ""), lambda: (sc1, f1, dict(row(a1)), audits(a1), audits(b1), verdict(a1)))
a2, b2, sc2, f2 = checker_pair(3, 0)
ck("D2 the older has the item lines, the newer none: as before -- the newer set aside, the older kept, the old words",
   lambda: kept_older(a2, b2) and "marked a duplicate of" in f2, lambda: (f2, dict(row(b2))))
a3, b3, sc3, f3 = checker_pair(0, 0)
a3b, b3b, sc3b, f3b = checker_pair(2, 4)
ck("D3 neither has item lines, or both have: as before -- the newer set aside", lambda: kept_older(a3, b3) and kept_older(a3b, b3b), lambda: (f3, f3b))
# D4 -- the guards: each one alone keeps the older (as before)
g = {}
a, b, _s, _f = checker_pair(0, 3, status="approved")
g["approved"] = (a, b)
tag_a = mk("LANE", 0)
tag_b = mk("LANE", 3, lane="pharmacy", minutes_ago=300)
db.execute("UPDATE bills SET dup_flag='maybe', dup_cand=? WHERE id=?", (tag_a, tag_b))
db.commit()
own.post("/bills/%d/dup" % tag_b, data={"what": "yes"})
flashes(own)
g["another lane"] = (tag_a, tag_b)
a, b, _s, _f = checker_pair(0, 3, rescan_of=1)
g["a rescan"] = (a, b)


PRE = {}


def guard_pair(setup, label):
    tag = "G%d" % (N[0] + 1)
    a = mk(tag, 0)
    b = mk(tag, 3, minutes_ago=300)
    PRE[label] = bool(hasattr(S, "clearer") and S.clearer(db, row(a), row(b))[2])     # the swap would happen without this guard
    setup(a)
    db.commit()
    db.execute("UPDATE bills SET dup_flag='maybe', dup_cand=? WHERE id=?", (a, b))
    db.commit()
    own.post("/bills/%d/dup" % b, data={"what": "yes"})
    flashes(own)
    g[label] = (a, b)


def fin(sql, args):
    c = sqlite3.connect(FDB)
    c.execute(sql, args)
    c.commit()
    c.close()


guard_pair(lambda a: fin("INSERT INTO purchase_scan_link(asset_bill_id, purchase_bill_id) VALUES(?,1)", (a,)), "linked to a Marg bill")
guard_pair(lambda a: fin("INSERT INTO order_scan_tie(order_id, asset_bill_id) VALUES(25,?)", (a,)), "tied to an order")
guard_pair(lambda a: fin("INSERT INTO purchase_bill(supplier, bill_no, scan_bill_id) VALUES('WALKSUP','X',?)", (a,)), "a pharmacy bill's scan")
guard_pair(lambda a: fin("INSERT INTO purchase_scan_alias(scan_id) VALUES(?)", (a,)), "an alias in the finance database (scan_id)")
guard_pair(lambda a: fin("INSERT INTO stock_voucher(scan_ref) VALUES((SELECT ?))", (row(a)["stamp_no"],)), "named by its stamp in the finance database")
guard_pair(lambda a: db.execute("UPDATE bills SET bill_month='2026-09' WHERE id=?", (a,)), "a month confirmed on it alone")
guard_pair(lambda a: db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (a, "x", "Walk", "desk_saved", "{}")), "a desk Save")
guard_pair(lambda a: db.execute("INSERT INTO bills(kind, stamp_no, status, page_of) VALUES('Consumable','W651-PG','rejected',?)", (a,)), "a joined page")
guard_pair(lambda a: db.execute("UPDATE bills SET lane='pharmacy', kind='Pharmacy', status='captured' WHERE id IN (?,?)", (a, a + 1)), "both in the pharmacy lane")
guard_pair(lambda a: db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (a, "x", "Walk", "month", "{}")), "its month set by a person")
guard_pair(lambda a: db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (a, "x", "Walk", "relane", "{}")), "moved to its lane by a person")
guard_pair(lambda a: db.execute("UPDATE bills SET doc_kind='challan' WHERE id=?", (a,)), "a challan against a bill")
guard_pair(lambda a: db.execute("UPDATE bills SET pe_who='bhawna' WHERE id=?", (a,)), "another person's paper")
guard_pair(lambda a: db.execute("UPDATE bills SET ocr_status='reading' WHERE id=?", (a,)), "not read yet")
guard_pair(lambda a: db.execute("INSERT INTO xray_mark(kind, ref_id, by_whom, at) VALUES('paper', ?, 'Walk', 'x')", (a,)), "an X-ray mark")
guard_pair(lambda a: db.execute("INSERT INTO bills(kind, stamp_no, status, dup_of, dup_flag) VALUES('Consumable','W651-DP','rejected',?,'yes')", (a,)), "another copy on it")
db.execute("INSERT OR IGNORE INTO locations(name) VALUES('WALK PLACE S651')")
LOC = db.execute("SELECT id FROM locations WHERE name='WALK PLACE S651'").fetchone()[0]
guard_pair(lambda a: db.execute("INSERT INTO assets(name, location_id, bill_id) VALUES('WALK MACHINE S651', ?, ?)", (LOC, a)), "a machine record")
ck("D4 the guards -- each alone keeps the older scan, as before: %s" % ", ".join(g),
   lambda: all(kept_older(a, b) for a, b in g.values()), lambda: [(k, dict(row(a))["status"], dict(row(b))["status"]) for k, (a, b) in g.items()])
ck("D4c ... and each of those guards is what stops it: the same pair, before its guard was set, would have been swapped (%d)" % len(PRE),
   lambda: len(PRE) == 17 and all(PRE.values()), lambda: PRE)
keep_fdb = S.FIN_DB
S.FIN_DB = FDB + ".absent"
a4, b4, sc4, f4 = checker_pair(0, 3)
S.FIN_DB = keep_fdb
fin("CREATE TABLE made_up_unknown(id INTEGER PRIMARY KEY, scan_owner_id INTEGER)", ())
a4c, b4c, sc4c, f4c = checker_pair(0, 3)
fin("DROP TABLE made_up_unknown", ())
ck("D4b the finance database cannot be read, or has a column named *scan* the rule does not know: nothing is swapped (as before)",
   lambda: kept_older(a4, b4) and kept_older(a4c, b4c), lambda: (f4, f4c))
# D5 -- the owner's 'same' answer on Scan ka kaam (S441 answer)
tag = "Q%d" % (N[0] + 1)
a5 = mk(tag, 0)
b5 = mk(tag, 3, minutes_ago=300)
S._verdict(db, b5, "twin_q", a5, "near match (walk)")
db.execute("INSERT INTO scan_question(bill_id, kind, cand_id, detail, asked_at) VALUES(?,?,?,?,?)", (b5, "twin", a5, "walk", "x"))
db.execute("UPDATE bills SET dup_flag='maybe', dup_cand=?, dup_why='image (walk)' WHERE id=?", (a5, b5))   # K1 B2: an amber too
db.commit()
q5 = db.execute("SELECT id FROM scan_question WHERE bill_id=?", (b5,)).fetchone()[0]
ok5 = S.answer(db, q5, "same", "Walk owner")
ck("D5 the owner's 'same' on Scan ka kaam: the scan with item lines kept, the empty older one set aside, the reason names D761",
   lambda: ok5[0] and row(a5)["status"] == "rejected" and row(a5)["dup_of"] == b5 and row(b5)["status"] == "draft" and "D761" in (row(a5)["dup_why"] or "")
   and verdict(a5)[0] == "double", lambda: (ok5, dict(row(a5)), dict(row(b5))))
r9 = own.post("/bills/%d/dup" % b5, data={"what": "yes"})
f9 = flashes(own)
q1 = db.execute("INSERT INTO scan_question(bill_id, kind, cand_id, detail, asked_at) VALUES(?,?,?,?,?)", (a1, "twin", b1, "walk", "x")).lastrowid
db.commit()
ok9 = S.answer(db, q1, "same", "Walk owner")
ck("D9 after a swap no later tap sets the kept scan aside: the kept scan's amber is closed (its Duplicate tap: nothing to decide), its "
   "verdict reads clear; a late 'same' on the pair kept the other way changes nothing",
   lambda: row(b5)["status"] == "draft" and (row(b5)["dup_flag"] or "") == "no" and "Nothing to decide" in f9 and verdict(b5)[0] == "clear"
   and row(b1)["status"] != "rejected" and row(a1)["status"] == "rejected", lambda: (dict(row(b5)), f9, verdict(b5), ok9, dict(row(b1))["status"]))
# D6 -- the sure double-scan rule (same supplier, bill-number tail, amount): run_pass on the newer
tag = "R%d" % (N[0] + 1)
a6 = mk(tag, 0, vendor="WALKSUP S651 SURE", bill_no="A000611", total=7100.0)
b6 = mk(tag, 2, vendor="WALKSUP S651 SURE", bill_no="A000611", total=7100.0, minutes_ago=300)
S.run_pass(db, only=a6, fin_path=FDB)
S.run_pass(db, only=b6, fin_path=FDB)
db.commit()
ck("D6 the sure double-scan rule: the newer (2 item lines) kept, the older (none) set aside; the newer's verdict 'clear', the older's 'double'",
   lambda: row(a6)["status"] == "rejected" and row(a6)["dup_of"] == b6 and row(b6)["status"] != "rejected" and verdict(a6)[0] == "double"
   and verdict(b6)[0] == "clear", lambda: (dict(row(a6))["status"], dict(row(b6))["status"], verdict(a6), verdict(b6)))
# D7 -- the guard after the reading (vendor + bill number + amount)
tag = "T%d" % (N[0] + 1)
a7 = mk(tag, 0, vendor="WALKSUP S651 TRIPLE", bill_no="B000777", total=990.0)
b7 = mk(tag, 4, vendor="WALKSUP S651 TRIPLE", bill_no="B000777", total=990.0, minutes_ago=300)
ar._dup_after_ocr(db, b7)
db.commit()
ck("D7 the guard after the reading (supplier + bill number + amount): the newer (4 item lines) kept, the older (none) set aside",
   lambda: kept_newer(a7, b7), lambda: (dict(row(a7)), dict(row(b7))))
tag = "U%d" % (N[0] + 1)
a7b = mk(tag, 4, vendor="WALKSUP S651 TRIPLE2", bill_no="B000778", total=991.0)
b7b = mk(tag, 0, vendor="WALKSUP S651 TRIPLE2", bill_no="B000778", total=991.0, minutes_ago=300)
ar._dup_after_ocr(db, b7b)
db.commit()
ck("D7b ... and with the item lines on the older: the newer set aside, as before", lambda: kept_older(a7b, b7b), lambda: (dict(row(a7b)), dict(row(b7b))))
# D8 -- the desk's 'same' answer on a held paper (D710), the paper it looks like untouched and empty
tag = "H%d" % (N[0] + 1)
a8 = mk(tag, 0)
b8 = mk(tag, 3, minutes_ago=300)
db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
           (b8, "x", "server", "d710_not_accepted", json.dumps({"same_as": row(a8)["stamp_no"]})))
db.commit()
r8 = own.post("/desk/api/save", json={"id": b8, "flag": "same"})
j8 = r8.get_json(silent=True) or {}
ck("D8 the desk's 'same' on a held paper: the scan with item lines kept, the empty one set aside, the desk's words say so",
   lambda: r8.status_code == 200 and j8.get("ok") and kept_newer(a8, b8) and ("is kept; %s is set aside as its second scan." % row(a8)["stamp_no"]) in (j8.get("message") or ""),
   lambda: (r8.status_code, j8, dict(row(a8))["status"], dict(row(b8))["status"]))
# the pages keep answering
ck("R1 the desk, the papers, Scan ka kaam's own page, the month and the Procedure room still answer for the owner",
   lambda: all(own.get(u).status_code == 200 for u in ("/desk", "/bills", "/desk/month", "/procroom", "/assets")),
   lambda: [(u, own.get(u).status_code) for u in ("/desk", "/bills", "/desk/month", "/procroom", "/assets")])
n_rej = db.execute("SELECT COUNT(*) FROM bills WHERE stamp_no LIKE 'W651-%' AND status='rejected' AND dup_of IS NOT NULL").fetchone()[0]
ck("R2 every pair set exactly one scan aside (no pair lost both, none set two aside)",
   lambda: all((row(a)["status"] == "rejected") != (row(b)["status"] == "rejected")
               for a, b in [(a1, b1), (a2, b2), (a3, b3), (a3b, b3b), (a4, b4), (a4c, b4c), (a5, b5), (a6, b6), (a7, b7), (a7b, b7b), (a8, b8)]
               + [v for k_, v in g.items() if k_ not in ("both in the pharmacy lane",)]
               if row(a)["status"] != "approved"), lambda: n_rej)
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad_ = [k for k in MUST_RED if RES.get(k, True)] + [k for k in red if k not in MUST_RED]
    print("WALK S651 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE" if not bad_ else "NOT AS IT MUST BE: " + ", ".join(bad_)))
    sys.exit(0 if not bad_ else 1)
print("WALK S651 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
