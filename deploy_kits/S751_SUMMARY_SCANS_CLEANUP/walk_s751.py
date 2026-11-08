#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s751.py -- kit S751: the clean-up walked on MADE-UP databases built by the real scan app's own init (never a live file).
    python3 -B walk_s751.py --live <assetapp dir> --shared <shared dir> --kit <kit dir>
Green = the DRY run reads all sixteen and refuses nothing; the REAL run removes exactly the sixteen, writes sixteen audit rows, clears the
derived rows and finance's scratch rows, keeps the audit history, the other papers and the stamp counter; a second REAL run refuses (not
found). CONTROL = seven databases each broken in one way (an amount off by Rs 2; scanned by someone else; an outside paper's dup_of pointing
in; a payment proved by one; a finance s750_dealer_of decision) -- each MUST refuse with nothing changed."""
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


LIVE, SHARED, KIT = opt("--live", "/root/assetapp"), opt("--shared", "/root/shared"), opt("--kit", os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
FAILS = []


def ck(name, ok, d=""):
    print(("  ok   " if ok else "  FAIL ") + "[S751] " + name + ((" " + d) if d and not ok else ""))
    if not ok:
        FAILS.append(name)


TARGETS = [(274, "YOGENDRA AGENCIES", 8512, "Pharmacy", "pharmacy", "captured"), (275, "DAANSHI PHARMA", 8603, "Consumable", "clinic", "rejected"),
           (276, "AGARWAL SURGICAL & MEDICALS", 1238, "Consumable", "clinic", "draft"), (277, "ESS KAY AGENCIES (EXTN)", 6859, "Pharmacy", "pharmacy", "captured"),
           (278, "DEEPAM PHARMA", 32114, "Pharmacy", "pharmacy", "captured"), (279, "GUNINA PHARMACEUTIC PVT. LTD.", 60682, "Consumable", "clinic", "draft"),
           (280, "MANNAT PHARMA", 24212, "Pharmacy", "pharmacy", "captured"), (281, "MANNAT PHARMA", 24212, "Pharmacy", "pharmacy", "captured"),
           (282, None, 3656, "Consumable", "clinic", "rejected"), (283, "JANTA PHARMACEUTICALS", 13146, "Pharmacy", "pharmacy", "captured"),
           (284, "SHIVAAZ FORMULATIONS", 65357, "Pharmacy", "pharmacy", "captured"), (285, "DRUG DEALS", 1557, "Consumable", "clinic", "rejected"),
           (286, "RADHA MEDICAL & SCIENTIFIC", 4038, "Pharmacy", "pharmacy", "captured"), (287, "A.A.PHARMACEUTICALS", 12818, "Consumable", "clinic", "draft"),
           (288, "SHRADDHA MEDICOSE", 9395, "Pharmacy", "pharmacy", "captured"), (289, "YUVIKA SURGICALS", 5940, "Consumable", "clinic", "draft")]
IDS = [t[0] for t in TARGETS]


def build(work):
    """The real app's init makes assets.db (every table, the seed users); then the made-up papers."""
    app = os.path.join(work, "app")
    os.makedirs(app)
    for f in os.listdir(LIVE):
        p = os.path.join(LIVE, f)
        if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
            shutil.copy(p, os.path.join(app, f))
    os.makedirs(os.path.join(work, "uploads"))
    adb = os.path.join(work, "assets.db")
    env = dict(os.environ, ASSETS_DB=adb, ASSETS_UPLOADS=os.path.join(work, "uploads"), SHARED_LIB_DIR=SHARED, CLINIC_PORTAL_DIR=os.path.join(work, "noportal"),
               FINANCE_LOCAL_URL="http://127.0.0.1:9", FINANCE_DB_FOR_SCANS=os.path.join(work, "nofinance.db"), PYTHONPYCACHEPREFIX=os.path.join(work, "pyc"),
               SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "nokey"), SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1")
    for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
        env.pop(k, None)
    r = subprocess.run([PY, "-B", "-W", "ignore", "-c", "import asset_register, claude_reader, sqlite3, os; claude_reader.ensure(sqlite3.connect(os.environ['ASSETS_DB']))"], env=env, cwd=app, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(r.stderr[-1500:])
        raise SystemExit("the real app did not load")
    a = sqlite3.connect(adb)
    tabs = {r[0] for r in a.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ("bills", "bill_items", "bill_audit", "claude_reading", "scan_check_s441", "scan_question", "users", "settings", "assets"):
        if t not in tabs:
            raise SystemExit("the made-up assets.db lacks %s" % t)
    uid = a.execute("SELECT id FROM users WHERE username='manoj'").fetchone()[0]
    a.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('stamp_seq','289')")
    # two older papers that must survive, and one older paper 273 the outside dup_of controls will point from
    for bid, stamp, vendor, amt, day in ((151, "B-0151", "DAANSHI PHARMA", 8603, "2026-10-12"), (182, "B-0182", "DRUG DEALS", 1557, "2026-10-16"),
                                         (273, "B-0273", "AGARWAL SURGICAL & MEDICALS", 487, "2026-11-07")):
        a.execute("INSERT INTO bills(id, kind, vendor, bill_no, bill_date, total_amount, created_by, created_at, stamp_no, status, submitted_by, submitted_at, lane) "
                  "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (bid, "Pharmacy", vendor, "X%d" % bid, day, amt, uid, "2026-11-08 03:14:00", stamp, "approved", "Shivani", "2026-11-08 08:44:00", "pharmacy"))
        a.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?,?,?,?,?)", (bid, "ITEM %d" % bid, 1, amt, amt))
        a.execute("INSERT INTO claude_reading(bill_id, at, model, ok, doc_kind, data, error) VALUES(?,?,?,1,'bill','{}',NULL)", (bid, "2026-11-08", "m"))
        a.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (bid, "2026-11-08 08:44:00", "Shivani", "submitted", "{}"))
    for i, (bid, vendor, amt, kind, lane, status) in enumerate(TARGETS):
        a.execute("INSERT INTO bills(id, kind, vendor, bill_no, bill_date, total_amount, created_by, created_at, stamp_no, status, submitted_by, submitted_at, lane, source_stored, dup_of) "
                  "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (bid, kind, vendor, None, None, float(amt), uid, "2026-11-08 06:%02d:00" % (24 + i), "B-%04d" % bid, status, "Shivani", "2026-11-08 11:%02d:00" % (54 + i) if i < 6 else "2026-11-08 12:%02d:00" % (i - 6),
                   lane, "bill_2026-11-08_%d.pdf" % (i + 1), 151 if bid == 275 else (182 if bid == 285 else None)))
        a.execute("INSERT INTO claude_reading(bill_id, at, model, ok, doc_kind, data, error) VALUES(?,?,?,1,'bill','{}',NULL)", (bid, "2026-11-08", "m"))
        a.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (bid, "2026-11-08 12:00:00", "Shivani", "submitted", "{}"))
        a.execute("INSERT OR REPLACE INTO scan_check_s441(bill_id, verdict, other_id, at) VALUES(?,?,?,?)", (bid, "ok", None, "2026-11-08"))
    a.execute("UPDATE bills SET dup_cand=280, dup_flag='maybe', dup_why='x' WHERE id=273")      # a later paper's 'second scan of B-0280?' question
    a.execute("INSERT INTO scan_question(bill_id, kind, at) VALUES(281, 'dup', '2026-11-08')") if "at" in {r[1] for r in a.execute("PRAGMA table_info(scan_question)")} else None
    a.commit()
    a.close()
    fdb = os.path.join(work, "finance.db")
    f = sqlite3.connect(fdb)
    f.executescript("""
    CREATE TABLE purchase_scan_state(asset_bill_id INTEGER PRIMARY KEY, why TEXT NOT NULL, detail TEXT, dup_cand INTEGER, dup_bill INTEGER, hint_bill INTEGER, checked_at TEXT NOT NULL);
    CREATE TABLE purchase_scan_link(bill_id INTEGER PRIMARY KEY, asset_bill_id INTEGER NOT NULL, grade TEXT NOT NULL, matched_on TEXT, linked_at TEXT NOT NULL);
    CREATE TABLE purchase_scan_alias(ocr_norm TEXT PRIMARY KEY, supplier_norm TEXT NOT NULL, scan_id INTEGER, who TEXT, at TEXT);
    CREATE TABLE s736_decision(asset_bill_id INTEGER PRIMARY KEY, decision TEXT NOT NULL);
    CREATE TABLE purchase_sarvam_check(asset_bill_id INTEGER PRIMARY KEY, x TEXT);
    INSERT INTO purchase_sarvam_check VALUES(277,'y');
    CREATE TABLE s749_act(id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, scan INTEGER, bill_id INTEGER);
    CREATE TABLE s750_dealer_of(scan INTEGER PRIMARY KEY, dealer TEXT NOT NULL, by TEXT, at TEXT NOT NULL);
    ALTER TABLE purchase_scan_state ADD COLUMN confirmed_by TEXT; ALTER TABLE purchase_scan_state ADD COLUMN chosen_vendor TEXT; ALTER TABLE purchase_scan_state ADD COLUMN dup_ok INTEGER;
    INSERT INTO purchase_scan_state(asset_bill_id, why, detail, checked_at) VALUES(274,'no_bill_yet','x','2026-11-08');
    INSERT INTO purchase_scan_state(asset_bill_id, why, detail, checked_at) VALUES(284,'amount_differs','x','2026-11-08');
    INSERT INTO purchase_scan_state(asset_bill_id, why, detail, checked_at) VALUES(150,'no_bill_yet','old','2026-10-20');
    INSERT INTO purchase_scan_link VALUES(9001,151,'EXACT','no+amt','2026-10-12');
    INSERT INTO purchase_scan_alias VALUES('DRUGDEALS','DRUG DEAL BAREILLY',285,'S439','2026-11-08');
    """)
    f.commit()
    f.close()
    return adb, fdb


def run(adb, fdb, real=False):
    cmd = [PY, "-B", os.path.join(KIT, "cleanup_s751.py"), "--assets", adb, "--finance", fdb] + (["--real"] if real else [])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr


def snap(adb, fdb):
    a = sqlite3.connect(adb)
    f = sqlite3.connect(fdb)
    s = (a.execute("SELECT COUNT(*) FROM bills").fetchone()[0], a.execute("SELECT COUNT(*) FROM bill_items").fetchone()[0],
         a.execute("SELECT COUNT(*) FROM bill_audit").fetchone()[0], a.execute("SELECT COUNT(*) FROM claude_reading").fetchone()[0],
         f.execute("SELECT COUNT(*) FROM purchase_scan_state").fetchone()[0], f.execute("SELECT COUNT(*) FROM purchase_scan_link").fetchone()[0])
    a.close()
    f.close()
    return s


work = tempfile.mkdtemp(prefix="s751walk_")
try:
    adb, fdb = build(work)
    before = snap(adb, fdb)
    print("1 · DRY on the made-up databases")
    rc, out = run(adb, fdb)
    ck("1 DRY exits 0 and says DRY OK", rc == 0 and "DRY OK" in out, out[-600:])
    ck("1 DRY lists all sixteen stamps", all(("B-%04d" % i) in out for i in IDS))
    ck("1 DRY wrote nothing", snap(adb, fdb) == before, repr(snap(adb, fdb)))
    ck("1 DRY reports the two finance scratch rows and the kept alias", re.search(r"purchase_scan_state\s*\.asset_bill_id\s+2\s", out) is not None and re.search(r"purchase_scan_alias\s*\.scan_id\s+1\s+\(kept", out) is not None)
    print("2 · REAL")
    rc, out = run(adb, fdb, real=True)
    ck("2 REAL exits 0 and says DONE", rc == 0 and "S751_SUMMARY_SCANS_CLEANUP: DONE." in out, out[-800:])
    after = snap(adb, fdb)
    ck("2 bills 19 -> 3 (the sixteen gone, the three older papers kept)", before[0] == 19 and after[0] == 3, repr((before, after)))
    a = sqlite3.connect(adb)
    f = sqlite3.connect(fdb)
    ck("2 B-0151, B-0182, B-0273 still there with their items and readings",
       a.execute("SELECT COUNT(*) FROM bills WHERE id IN (151,182,273)").fetchone()[0] == 3 and a.execute("SELECT COUNT(*) FROM bill_items").fetchone()[0] == 3
       and a.execute("SELECT COUNT(*) FROM claude_reading WHERE bill_id IN (151,182,273)").fetchone()[0] == 3)
    ck("2 no reading, s441 check or question left for the sixteen",
       a.execute("SELECT COUNT(*) FROM claude_reading WHERE bill_id BETWEEN 274 AND 289").fetchone()[0] == 0
       and a.execute("SELECT COUNT(*) FROM scan_check_s441 WHERE bill_id BETWEEN 274 AND 289").fetchone()[0] == 0
       and a.execute("SELECT COUNT(*) FROM scan_question WHERE bill_id BETWEEN 274 AND 289").fetchone()[0] == 0)
    ck("2 sixteen paper_deleted audit rows by S751, the old audit history kept (19 'submitted' rows)",
       a.execute("SELECT COUNT(*) FROM bill_audit WHERE action='paper_deleted' AND who LIKE 'S751%'").fetchone()[0] == 16
       and a.execute("SELECT COUNT(*) FROM bill_audit WHERE action='submitted'").fetchone()[0] == 19)
    det = a.execute("SELECT detail FROM bill_audit WHERE action='paper_deleted' AND bill_id=284").fetchone()[0]
    ck("2 the audit detail carries the stamp, created_at, vendor and amount (B-0284 Shivaaz 65357)", '"stamp": "B-0284"' in det and "SHIVAAZ" in det and "65357" in det and '"created_at"' in det, det[:200])
    ck("2 B-0273's 'second scan of B-0280?' question is cleared, the paper itself kept",
       a.execute("SELECT dup_cand, dup_flag, dup_why, status FROM bills WHERE id=273").fetchone() == (None, None, None, "approved"))
    ck("2 finance: purchase_sarvam_check row for B-0277 gone", f.execute("SELECT COUNT(*) FROM purchase_sarvam_check").fetchone()[0] == 0)
    ck("2 the stamp counter stays 289 (the next paper is B-0290)", a.execute("SELECT value FROM settings WHERE key='stamp_seq'").fetchone()[0] == "289")
    ck("2 finance: the two scratch rows gone, the old one and the alias and the old link kept",
       f.execute("SELECT COUNT(*) FROM purchase_scan_state").fetchone()[0] == 1 and f.execute("SELECT asset_bill_id FROM purchase_scan_state").fetchone()[0] == 150
       and f.execute("SELECT COUNT(*) FROM purchase_scan_link").fetchone()[0] == 1 and f.execute("SELECT COUNT(*) FROM purchase_scan_alias").fetchone()[0] == 1)
    a.close()
    f.close()
    ck("2 both backups written beside the databases", any(x.startswith("assets.db.bak_S751_") for x in os.listdir(work)) and any(x.startswith("finance.db.bak_S751_") for x in os.listdir(work)))
    print("3 · REAL again")
    rc, out = run(adb, fdb, real=True)
    ck("3 a second run REFUSES (not found) and changes nothing", rc == 1 and "REFUSED" in out and "NOT FOUND" in out and snap(adb, fdb) == after, out[-400:])
    print("4 · CONTROL -- seven broken databases, each must refuse with nothing changed")
    controls = {
        "amount off by Rs 2 on B-0278": ("a", "UPDATE bills SET total_amount=32116 WHERE id=278"),
        "B-0283 scanned by Darpan": ("a", "UPDATE bills SET submitted_by='Darpan' WHERE id=283"),
        "an outside paper's dup_of points at B-0280": ("a", "UPDATE bills SET dup_of=280 WHERE id=273"),
        "a payment proved by B-0286": ("a", "INSERT INTO paper_payment_bill(payment_id, bill_id, bill_created_at, amount) VALUES(1, 286, '', 4038)"),
        "a finance s750_dealer_of decision on B-0287": ("f", "INSERT INTO s750_dealer_of VALUES(287,'A.A.','manoj','2026-11-08')"),
        "a person's decision on a finance scratch row (B-0284 confirmed_by)": ("f", "UPDATE purchase_scan_state SET confirmed_by='manoj' WHERE asset_bill_id=284"),
        "an outside paper's dup_of points at B-0274": ("a", "UPDATE bills SET dup_of=274 WHERE id=273"),
    }
    for name, (which, sql) in controls.items():
        w2 = tempfile.mkdtemp(prefix="s751ctl_")
        try:
            a2, f2 = build(w2)
            c = sqlite3.connect(a2 if which == "a" else f2)
            try:
                c.execute(sql)
                c.commit()
            except sqlite3.DatabaseError as e:
                c.close()
                ck("4 CONTROL set-up for '%s'" % name, False, repr(e))
                continue
            c.close()
            b2 = snap(a2, f2)
            rc, out = run(a2, f2, real=True)
            ck("4 CONTROL '%s' refuses, writes nothing, no backup made" % name, rc == 1 and "REFUSED" in out and snap(a2, f2) == b2
               and not any(x.startswith("assets.db.bak_") for x in os.listdir(w2)), out[-500:])
        finally:
            shutil.rmtree(w2, ignore_errors=True)
finally:
    shutil.rmtree(work, ignore_errors=True)
print("walk_s751: %d check(s) failed" % len(FAILS) + ("" if not FAILS else " -- " + "; ".join(FAILS)))
sys.exit(1 if FAILS else 0)
