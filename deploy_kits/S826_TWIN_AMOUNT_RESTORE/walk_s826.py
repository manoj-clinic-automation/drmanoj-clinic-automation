#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s826.py -- kit S826_TWIN_AMOUNT_RESTORE on the REAL scan app: the app's code copied into a scratch folder with the given
asset_register.py and scan_checks_s441.py (the kit's TO -- or the live FROM for the control), on a MADE-UP, empty database the app creates
itself. Made-up rows only ('WALK826 ...' suppliers, made-up bill numbers and amounts); nothing is sent anywhere; the scratch is removed.

    python3 -B walk_s826.py --live <the app folder> --files <folder with asset_register.py and scan_checks_s441.py> [--control]
The last line: 'WALK S826 GREEN' (all checks) -- or, with --control on the live files, 'CONTROL S826 RED as it must be' when every
S826 check is red and every other check green."""
import datetime as dt
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


LIVE, FILES, CONTROL = opt("--live", "/root/assetapp"), opt("--files"), "--control" in ARGS

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s826walk_")
    try:
        app, shared = os.path.join(work, "app"), os.path.join(work, "shared")
        os.makedirs(app)
        os.makedirs(shared)
        for f in os.listdir(LIVE):                                   # the app's CODE only -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        shutil.copy(os.path.join(FILES, "asset_register.py"), os.path.join(app, "asset_register.py"))
        shutil.copy(os.path.join(FILES, "scan_checks_s441.py"), os.path.join(shared, "scan_checks_s441.py"))
        os.makedirs(os.path.join(work, "uploads"))
        env = dict(os.environ, ASSETS_DB=os.path.join(work, "assets.db"), ASSETS_UPLOADS=os.path.join(work, "uploads"), SHARED_LIB_DIR=shared,
                   SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "nokey"), SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1",
                   CLINIC_PORTAL_DIR=os.path.join(work, "noportal"), FINANCE_LOCAL_URL="http://127.0.0.1:9",
                   FINANCE_DB_FOR_SCANS=os.path.join(work, "nofinance.db"), PYTHONPYCACHEPREFIX=os.path.join(work, "pyc"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", "-W", "ignore", os.path.abspath(__file__), "--inner", app] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=300)
        sys.stdout.write(r.stdout)
        last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        if not (last.startswith("WALK S826") or last.startswith("CONTROL S826")):
            print(r.stderr[-2500:])
            print("WALK S826 STOPPED: the inner run did not finish")
            sys.exit(2)
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
APPD = ARGS[ARGS.index("--inner") + 1]
sys.path.insert(0, APPD)
RES = []          # (name, ok, is_s826)


def ck(name, fn, s826=True):
    try:
        ok, d = bool(fn()), ""
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, "(raised: %s)" % repr(e)[:160]
    print(("  ok   " if ok else "  RED  ") + ("[S826] " if s826 else "") + name + ((" " + d) if d and not ok else ""))
    RES.append((name, ok, s826))


import asset_register as ar                                          # noqa: E402
S441 = ar.S441
ck("0 the real app loads with scan_checks_s441 mounted", lambda: ar.app is not None and S441 is not None, s826=False)
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
S441.ensure(db)
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.commit()
cols = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
NOW = dt.datetime.now()
WHEN = (NOW - dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
FP = iter("%016x" % (0x1111111111111111 * (i % 15 + 1) ^ (i * 0x0F0F0F0F)) for i in range(1, 200))
STAMP = iter(range(1, 999))


def scan(vendor, bill_no, amount, lane="pharmacy", status="captured", **extra):
    row = dict(stamp_no="W-%04d" % next(STAMP), vendor=vendor, bill_no=bill_no, total_amount=amount, lane=lane,
               kind=("Pharmacy" if lane == "pharmacy" else "Consumable"), status=status, submitted_at=WHEN, ocr_status="read",
               fpc=next(FP), created_by=1)
    row["submitted_by"] = row["scanned_by"] = "walker%d" % int(row["stamp_no"][2:])   # a different person each scan: never a forgotten page
    row.update(extra)
    row = {k: v for k, v in row.items() if k in cols}
    cur = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(row), ",".join("?" * len(row))), tuple(row.values()))
    db.commit()
    return cur.lastrowid


def bill(bid):
    return db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()


def q_of(bid):
    return db.execute("SELECT * FROM scan_question WHERE bill_id=? AND kind='twin'", (bid,)).fetchone()


def run(bid):
    S441.run_pass(db, only=bid, now=NOW)
    db.row_factory = sqlite3.Row


print("A · the twin question and two amounts")
a1 = scan("WALK826 JANTA PHARMA", "JP90001", 4450.0)
run(a1)
a2 = scan("WALK826 JANTA PHARMA", "JP90001", 3205.0)                 # the revised bill: the same number, the return taken off
run(a2)
ck("A1 a revised bill (the same supplier and number, 28% less) is NOT asked about", lambda: q_of(a2) is None)
ck("A1 ... and both scans stay filed (captured)", lambda: bill(a1)["status"] == "captured" and bill(a2)["status"] == "captured", s826=False)
b1 = scan("WALK826 KEDAR PHARMA", "KP55501", 5000.0)
run(b1)
b2 = scan("WALK826 KEDAR PHARMA", "KP55501", 5000.0)                 # a true double scan
run(b2)
ck("A2 a true double (the same supplier, number and amount) is still set aside by itself, a duplicate of the first",
   lambda: bill(b2)["status"] == "rejected" and bill(b2)["dup_of"] == b1, s826=False)
c1 = scan("WALK826 SHREE AGENCIES", "", 1000.0)
run(c1)
c2 = scan("WALK826 SHREE AGENCIES", "", 1015.0)                      # within 2%, no bill number read: a near match
run(c2)
ck("A3 a near match within 2% with no bill number is still asked (the twin question as before)", lambda: q_of(c2) is not None, s826=False)
d1 = scan("WALK826 MAHAVIR DRUG", "MD77001", 2500.0)
run(d1)
d2 = scan("WALK826 MAHAVIR DRUG", "MD77001", None)                   # the amount not read
run(d2)
ck("A4 a near match whose second amount was not read is still asked (an amount not read is not a difference)", lambda: q_of(d2) is not None, s826=False)
# an old question already open on a pair of two amounts (asked before the kit): settled 'different' by the next pass
e1 = scan("WALK826 RAJ MEDICOSE", "RM12001", 1800.0)
e2 = scan("WALK826 RAJ MEDICOSE", "RM12001", 2600.0)
for x in (e1, e2):
    S441._verdict(db, x, "clear")
db.execute("INSERT INTO scan_question(bill_id, kind, cand_id, detail, asked_at) VALUES(?,?,?,?,?)", (e2, "twin", e1, "walk: an old question", WHEN))
db.commit()
f1 = scan("WALK826 NEW LIFE", "NL40001", 900.0)
run(f1)                                                             # any pass settles it
qe = q_of(e2)
ck("A5 an old open question on a pair 44% apart is settled 'different' by the server's next pass", lambda: qe["answer"] == "different" and "S826" in (qe["answered_by"] or ""))
ck("A5 ... recorded on the scan (bill_audit not_duplicate, how S826)",
   lambda: db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='not_duplicate' AND detail LIKE '%S826%'", (e2,)).fetchone() is not None)
ck("A5 ... and the question no longer shows on Scan ka kaam", lambda: all(o["q"] != qe["id"] for o in S441.open_questions(db)))
ck("A5 ... an open question on a near pair (A3) is NOT settled by it", lambda: q_of(c2)["answer"] is None, s826=False)
# a 'same' answer on a pair of two amounts (a race: the question was open when it was answered)
g1 = scan("WALK826 ARIHANT", "AR33001", 1245.0)
g2 = scan("WALK826 ARIHANT", "AR33001", 4450.0)
for x in (g1, g2):
    S441._verdict(db, x, "clear")
cur = db.execute("INSERT INTO scan_question(bill_id, kind, cand_id, detail, asked_at) VALUES(?,?,?,?,?)", (g2, "twin", g1, "walk", WHEN))
db.commit()
ok, msg = S441.answer(db, cur.lastrowid, "same", "walk person")
db.row_factory = sqlite3.Row
ck("A6 'same paper' answered on two amounts 3.6x apart: answered ok, but NEITHER scan is set aside",
   lambda: ok and bill(g1)["status"] == "captured" and bill(g2)["status"] == "captured")
ck("A6 ... and the question is recorded 'different' (both kept)", lambda: q_of(g2)["answer"] == "different")
j1 = scan("WALK826 SAI PHARMA", "SP1", 900.0)
j2 = scan("WALK826 SAI PHARMA", "SP1", 1900.0, status="rejected", dup_of=j1)
cur = db.execute("INSERT INTO scan_question(bill_id, kind, cand_id, detail, asked_at) VALUES(?,?,?,?,?)", (j2, "twin", j1, "walk", WHEN))
db.commit()
S441.settle_differing_s826(db) if hasattr(S441, "settle_differing_s826") else None
db.commit()
ck("A8 an open question where one scan is already set aside is NOT settled by S826 (no misleading record)", lambda: q_of(j2)["answer"] is None, s826=False)
h1 = scan("WALK826 ARIHANT", "AR33002", 700.0)
h2 = scan("WALK826 ARIHANT", "AR33002", 707.0)
for x in (h1, h2):
    S441._verdict(db, x, "clear")
cur = db.execute("INSERT INTO scan_question(bill_id, kind, cand_id, detail, asked_at) VALUES(?,?,?,?,?)", (h2, "twin", h1, "walk", WHEN))
db.commit()
S441.answer(db, cur.lastrowid, "same", "walk person")
db.row_factory = sqlite3.Row
ck("A7 'same paper' on two amounts within 2%: the newer set aside as before", lambda: bill(h2)["status"] == "rejected" and bill(h2)["dup_of"] == h1, s826=False)

for _x in (a1, a2, b1, b2, d1, d2):
    _r = bill(_x); _v = db.execute("SELECT verdict, other_id, detail FROM scan_check_s441 WHERE bill_id=?", (_x,)).fetchone()
    print("   DBG", _x, _r["status"], _r["dup_of"], _r["lane"], _r["total_amount"], tuple(_v) if _v else None) if "--debug" in ARGS else None
print("B · the owner's Restore")
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
uid = db.execute("SELECT id FROM users WHERE username='manoj'").fetchone()[0]
with own.session_transaction() as ss:
    ss["uid"] = uid
    ss["epoch"] = epoch
uc = {r[1] for r in db.execute("PRAGMA table_info(users)")}
mrow = {k: v for k, v in dict(username="walk826mgr", display_name="Walk Manager", role="manager", password_hash="x", pw_hash="x", active=1).items() if k in uc}
db.execute("INSERT INTO users(%s) VALUES(%s)" % (",".join(mrow), ",".join("?" * len(mrow))), tuple(mrow.values()))
db.commit()
mgr = ar.app.test_client()
with mgr.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk826mgr'").fetchone()[0]
    ss["epoch"] = epoch
stamp_b2 = bill(b2)["stamp_no"]
page = own.get("/bills/%d" % b2).get_data(as_text=True)
ck("B1 the owner's page of a pharmacy scan set aside as a duplicate shows 'Restore — not a duplicate'", lambda: "id=s826restore" in page and "Restore — not a duplicate" in page)
k1 = scan("WALK826 CLINIC VENDOR", "CV1", 300.0, lane="clinic", status="rejected", dup_of=a1)
ck("B1 ... a clinic-lane duplicate shows no Restore", lambda: "id=s826restore" not in own.get("/bills/%d" % k1).get_data(as_text=True), s826=False)
pg = scan("WALK826 KEDAR PHARMA", "KP55502", 100.0, status="rejected", dup_of=b1, page_of=b1)
ck("B1 ... a joined page shows no Restore", lambda: "id=s826restore" not in own.get("/bills/%d" % pg).get_data(as_text=True), s826=False)
rm = mgr.post("/bills/%d/restore_s826" % b2)
ck("B2 a manager cannot restore (refused) and nothing changes",
   lambda: rm.status_code in (302, 403) and "restore_s826" not in (rm.headers.get("Location") or "") and bill(b2)["status"] == "rejected" and rm.status_code == 403)
r = own.post("/bills/%d/restore_s826" % b2)
nb = bill(b2)
ck("B3 the owner's Restore: back to Filed (captured), dup_of cleared, not a duplicate (dup_flag no), the stamp kept",
   lambda: r.status_code in (302, 303) and nb["status"] == "captured" and nb["dup_of"] is None and nb["dup_flag"] == "no" and nb["stamp_no"] == stamp_b2)
au = db.execute("SELECT who, detail FROM bill_audit WHERE bill_id=? AND action='restore_s826'", (b2,)).fetchone()
ck("B3 ... recorded: who (the owner's name), what it was a duplicate of, why it was set aside",
   lambda: au is not None and au["who"] and '"was_dup_of": %d' % b1 in au["detail"] and "S441 sure" in au["detail"])
db.execute("DELETE FROM scan_check_s441 WHERE bill_id=?", (b2,))     # make the pass judge it afresh (else it is skipped as judged)
db.commit()
run(b2)
ck("B4 a fresh pass on the restored scan does not set it aside again", lambda: bill(b2)["status"] == "captured")
ar._dup_after_ocr(db, b1)                                            # the kept partner re-read (the intake's own duplicate check)
db.commit()
ck("B4 ... nor does a re-read of its partner set the PARTNER aside (the reviewer's repro)", lambda: bill(b1)["status"] == "captured" and bill(b1)["dup_flag"] == "no")
ck("B4 ... the pair is recorded as two papers (scan_question 'different')", lambda: S441._refused_pair(db, b1, b2))
st1 = bill(k1)["status"]
own.post("/bills/%d/restore_s826" % k1)
ck("B5 Restore on a clinic-lane duplicate or a joined page changes nothing",
   lambda: bill(k1)["status"] == st1 == "rejected" and (own.post("/bills/%d/restore_s826" % pg) is not None) and bill(pg)["status"] == "rejected" and bill(pg)["page_of"] == b1, s826=False)
nd = scan("WALK826 RAJ MEDICOSE", "RM12009", 50.0, status="rejected", reject_reason="walk: rejected by hand")
own.post("/bills/%d/restore_s826" % nd)
ck("B5 ... and on a scan rejected by hand (not a duplicate)", lambda: bill(nd)["status"] == "rejected", s826=False)
ck("B6 the version mark: asset_register.KIT_S826", lambda: getattr(ar, "KIT_S826", "") == "S826_TWIN_AMOUNT_RESTORE")

s826 = [x for x in RES if x[2]]
other = [x for x in RES if not x[2]]
print("  -- %d checks: %d S826 (%d green), %d others (%d green)" % (len(RES), len(s826), sum(1 for x in s826 if x[1]), len(other), sum(1 for x in other if x[1])))
if CONTROL:
    good = all(not x[1] for x in s826) and all(x[1] for x in other)
    print("CONTROL S826 RED as it must be" if good else "CONTROL S826 NOT AS EXPECTED")
    sys.exit(0 if good else 1)
print("WALK S826 GREEN" if all(x[1] for x in RES) else "WALK S826 RED")
sys.exit(0 if all(x[1] for x in RES) else 1)
