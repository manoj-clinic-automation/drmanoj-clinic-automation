#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_fix_s754.py -- the data step of S754 (fix_s754.py) on the REAL scan app with the kit's files, on MADE-UP databases the app makes
itself: nine made-up papers shaped like today's (the ids and stamps of the line, made-up files, made-up readings), a made-up finance
database. The reader's HTTP call is a stub; nothing is sent anywhere; the scratch folder is removed at the end.

    python3 -B walk_fix_s754.py --live <the app folder> --files <folder holding the kit's three files and fix_s754.py>
The last line: 'walk_fix_s754: N check(s) failed'. Each CONTROL is a database broken one way, which must REFUSE with nothing changed."""
import contextlib
import io
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


LIVE, FILES = opt("--live", "/root/assetapp"), opt("--files")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s754fix_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in ("asset_register.py", "claude_reader.py", "fix_s754.py"):
            shutil.copy(os.path.join(FILES, f), os.path.join(app, f))
        shared = os.path.join(work, "shared")
        os.makedirs(shared)
        shutil.copy(os.path.join(FILES, "scan_checks_s441.py"), os.path.join(shared, "scan_checks_s441.py"))
        os.makedirs(os.path.join(work, "uploads"))
        os.makedirs(os.path.join(work, "key"))
        open(os.path.join(work, "key", "anthropic.key"), "w").write("made-up-walk-key\n")
        env = dict(os.environ, ASSETS_DB=os.path.join(app, "assets.db"), ASSETS_UPLOADS=os.path.join(work, "uploads"), SHARED_LIB_DIR=shared,
                   SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"), SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1",
                   CLINIC_PORTAL_DIR=os.path.join(work, "noportal"), FINANCE_LOCAL_URL="http://127.0.0.1:9", FINANCE_DB_FOR_SCANS=os.path.join(work, "nofin.db"),
                   S441_MERGE_PY=os.path.join(work, "no-python"), S618_TURN_PY=os.path.join(work, "no-python"), PYTHONPYCACHEPREFIX=os.path.join(work, "pyc"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", "-W", "ignore", os.path.abspath(__file__), "--inner", app, work] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=300)
        sys.stdout.write(r.stdout)
        if r.returncode not in (0, 1) or os.environ.get("S754_WALK_DEBUG"):
            print(r.stderr[-3000:])
        if not r.stdout.strip().splitlines() or not r.stdout.strip().splitlines()[-1].startswith("walk_fix_s754:"):
            print("walk_fix_s754: the inner run did not finish")
            sys.exit(2)
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

APPD, WORK = ARGS[ARGS.index("--inner") + 1], ARGS[ARGS.index("--inner") + 2]
sys.path.insert(0, APPD)
FAILS = []


def ck(name, fn):
    try:
        ok, d = bool(fn()), ""
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, "(raised: %s)" % repr(e)[:160]
    print(("  ok   " if ok else "  FAIL ") + name + ((" " + d) if d and not ok else ""))
    if not ok:
        FAILS.append(name)


import asset_register as ar                                          # noqa: E402
import claude_reader as CR                                           # noqa: E402
import fix_s754 as FX                                                # noqa: E402

ADB, UP = os.environ["ASSETS_DB"], os.environ["ASSETS_UPLOADS"]
FDB = os.path.join(WORK, "finance.db")
CALLS = []


def fake_post(body, key):
    CALLS.append(body)
    t = body["messages"][0]["content"][-1]["text"]
    if "MONTHLY" not in t:                                           # the S618 page check, or anything else: a plain upright answer
        return 200, {"content": [{"type": "text", "text": json.dumps({"pages": [{"text_top": "top"}], "whole_bill": True, "totals_visible": True, "legible": True, "note": ""})}], "stop_reason": "end_turn"}, ""
    ans = {"is_summary": True, "dealer": "SANJEEVNI MEDICOS", "period_from": None, "period_to": "2026-11-02", "as_on": "2026-11-02", "continued": False,
           "lines": [{"kind": "bill", "no": "WALK-A1", "date": "2026-10-14", "amount": 1200}], "total_bills": 1200, "closing": 1200, "handwritten": False}
    return 200, {"content": [{"type": "text", "text": json.dumps(ans)}], "stop_reason": "end_turn"}, ""


CR._post = fake_post
SEED = [  # id, stamp, lane, kind, status, vendor, amount, doc_kind, page_of, reject_reason, approved_by
    (291, "B-0291", "clinic", "Consumable", "draft", "SANJEEVNI MEDICOS", 2453, None, None, None, None),
    (292, "B-0292", "clinic", "Consumable", "draft", "DRUG DEALS", 1557, None, None, None, None),
    (293, "B-0293", "clinic", "Consumable", "draft", "A.A.PHARMACEUTICALS", 12818, None, None, None, None),
    (295, "B-0295", "pharmacy", "Summary", "captured", "JANTA PHARMACEUTICALS", 13146, "summary", None, None, None),
    (296, "B-0296", "pharmacy", "Pharmacy", "rejected", None, 3656, None, 295, "page 2 of B-0295 (joined automatically)", "server (S441 forgotten page)"),
    (297, "B-0297", "pharmacy", "Pharmacy", "captured", "MANNAT PHARMA", 24212, None, None, None, None),
    (298, "B-0298", "pharmacy", "Pharmacy", "captured", "GUNINA PHARMACEUTICALS PVT. LTD.", 60682, None, None, None, None),
    (299, "B-0299", "pharmacy", "Pharmacy", "captured", "DEEPAM PHARMA", 32114, None, None, None, None),
    (303, "B-0303", "pharmacy", "Summary", "captured", "SANJEEVNI MEDICOS", 8603, "summary", None, None, None),
]


def seed(adb, fdb):
    for p in (adb + "-wal", adb + "-shm"):
        if os.path.exists(p):
            os.remove(p)
    d = sqlite3.connect(adb)
    CR.ensure(d)                                                     # the reader's own table, as on the box
    if ar.S441 is not None:
        ar.S441.ensure(d)
    d.execute("DELETE FROM bills WHERE id>=290")
    for t in ("bill_audit", "claude_reading", "scan_check_s441", "scan_question", "scan_lie", "bill_items"):
        try:
            d.execute("DELETE FROM %s WHERE bill_id>=290" % t)
        except sqlite3.Error:
            pass
    for (i, st, lane, kind, status, vendor, amt, dk, po, rr, ab) in SEED:
        fn = "bill_walk754_%d.pdf" % i
        open(os.path.join(UP, fn), "wb").write(b"%PDF-1.4 made-up walk754 " + st.encode())
        d.execute("INSERT INTO bills(id, stamp_no, kind, lane, status, vendor, total_amount, doc_kind, page_of, reject_reason, approved_by, "
                  "submitted_by, submitted_at, source_stored, ocr_status, bill_month) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (i, st, kind, lane, status, vendor, amt, dk, po, rr, ab, "Alisha", "2026-11-08 15:%02d:00" % (i - 290), fn, "read", "2026-11"))
        d.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (i, "2026-11-08 15:%02d" % (i - 290), "", "filled", '{"by": "claude"}'))
        d.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,1,?,?)",
                  (i, "2026-11-08 15:00:00", "walk", "summary" if dk == "summary" else "bill", json.dumps({"vendor": vendor})))
        d.execute("INSERT OR REPLACE INTO scan_check_s441(bill_id, verdict, other_id, detail, at) VALUES(?,?,?,?,?)",
                  (i, "page" if i == 296 else "clear", 295 if i == 296 else None, "", "2026-11-08 15:30:00"))
    open(os.path.join(UP, "bill_walk754_merged.pdf"), "wb").write(b"%PDF-1.4 made-up merged")
    d.execute("UPDATE bills SET source_stored='bill_walk754_merged.pdf' WHERE id=295")
    d.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
              (295, "2026-11-08 15:13", "server (S441)", "s441_page_merged", json.dumps({"page": 296, "page_stamp": "B-0296", "before": "bill_walk754_295.pdf", "after": "bill_walk754_merged.pdf"})))
    d.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (295, "2026-11-08 15:12", "Alisha", "summary", '{"lane": "pharmacy"}'))
    d.execute("INSERT INTO scan_question(bill_id, kind, cand_id, detail, asked_at) VALUES(291, 'lane', NULL, 'walk', '2026-11-08 15:30:00')")
    d.commit()
    d.close()
    if os.path.exists(fdb):
        os.remove(fdb)
    f = sqlite3.connect(fdb)
    f.execute("CREATE TABLE purchase_scan_link(asset_bill_id INTEGER, bill_id INTEGER)")
    f.execute("CREATE TABLE purchase_scan_state(asset_bill_id INTEGER, confirmed_by TEXT, chosen_vendor TEXT, dup_ok INTEGER)")
    f.execute("CREATE TABLE s736_decision(asset_bill_id INTEGER)")
    f.execute("CREATE TABLE s749_act(scan INTEGER)")
    f.execute("CREATE TABLE s750_dealer_of(scan INTEGER, dealer TEXT)")
    f.execute("INSERT INTO purchase_scan_state(asset_bill_id) VALUES(297)")         # the pairing's scratch, no decision: left, reported
    f.execute("INSERT INTO s750_dealer_of(scan, dealer) VALUES(303, 'WALK DAANSHI')")  # the Sanjeevni side chose B-0303's dealer: kept
    f.commit()
    f.close()


def run(*extra):
    sys.argv = ["fix_s754.py", "--assets", ADB, "--uploads", UP, "--finance", FDB] + list(extra)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = FX.main()
    return rc, buf.getvalue()


def snap():
    d = sqlite3.connect(ADB)
    try:
        return (d.execute("SELECT id, kind, lane, status, doc_kind, page_of, vendor, bill_date, total_amount, source_stored FROM bills WHERE id>=290 ORDER BY id").fetchall(),
                d.execute("SELECT COUNT(*) FROM bill_audit").fetchone()[0], d.execute("SELECT COUNT(*) FROM claude_reading WHERE doc_kind='summary'").fetchone()[0])
    finally:
        d.close()


def baks():
    return [f for f in os.listdir(os.path.dirname(ADB)) if ".bak_S754_" in f]


def R(i):
    d = sqlite3.connect(ADB)
    d.row_factory = sqlite3.Row
    try:
        return d.execute("SELECT * FROM bills WHERE id=?", (i,)).fetchone()
    finally:
        d.close()


print("1 · the DRY read on papers shaped like today's")
seed(ADB, FDB)
s0 = snap()
rc, out = run()
ck("1 DRY: every guard green, 9 to put right, nothing written, no backup", lambda: rc == 0 and "DRY OK" in out and "9 paper(s)" in out and snap() == s0 and not baks())
ck("1 DRY prints the B-0303 dealer kept on the Sanjeevni side and the pairing scratch row left", lambda: "B-0303's dealer chosen" in out and "rows 1, a person's decision on 0" in out)

print("2 · REAL")
rc, out = run("--real")
ck("2 REAL: DONE, a backup beside the database", lambda: rc == 0 and "S754_SUMMARY_RECOGNISE: DONE." in out and len(baks()) == 1)
ck("2 B-0291/0292/0293: the pharmacy lane, captured, kind 'Summary', doc_kind 'summary' (off the desk)",
   lambda: all(R(i)["lane"] == "pharmacy" and R(i)["status"] == "captured" and R(i)["kind"] == "Summary" and R(i)["doc_kind"] == "summary" for i in (291, 292, 293)))
ck("2 ... B-0291's open lane question answered by the server", lambda: sqlite3.connect(ADB).execute("SELECT answer, answered_by FROM scan_question WHERE bill_id=291").fetchone() == ("pharmacy", "server (S754_SUMMARY_RECOGNISE)"))
ck("2 B-0297/0298/0299: kind 'Summary', doc_kind 'summary', still captured on the pharmacy lane",
   lambda: all(R(i)["kind"] == "Summary" and R(i)["doc_kind"] == "summary" and R(i)["status"] == "captured" for i in (297, 298, 299)))
ck("2 B-0296: unjoined (page_of empty), captured, kind 'Summary'; its S441 verdict 'clear'",
   lambda: R(296)["page_of"] is None and R(296)["status"] == "captured" and R(296)["kind"] == "Summary" and not R(296)["reject_reason"]
   and sqlite3.connect(ADB).execute("SELECT verdict FROM scan_check_s441 WHERE bill_id=296").fetchone()[0] == "clear")
ck("2 B-0295: its own single file back (bill_walk754_295.pdf), audited 's441_page_unmerged'", lambda: R(295)["source_stored"] == "bill_walk754_295.pdf"
   and sqlite3.connect(ADB).execute("SELECT 1 FROM bill_audit WHERE bill_id=295 AND action='s441_page_unmerged'").fetchone() is not None)
ck("2 every re-read paper: the buyer's name gone (vendor empty), bill_date the end of October (from the bills), the figure, ocr 'read'",
   lambda: all(R(i)["vendor"] is None and R(i)["bill_date"] == "2026-10-31" and float(R(i)["total_amount"]) == 1200 and R(i)["ocr_status"] == "read"
               for i in (291, 292, 293, 296, 297, 298, 299, 303)))
ck("2 ... their readings: doc_kind 'summary', period_by 'bills', dealer null with dealer_was_buyer",
   lambda: all((lambda d: d["period_by"] == "bills" and d["dealer"] is None and d.get("dealer_was_buyer") is True)(json.loads(sqlite3.connect(ADB).execute(
       "SELECT data FROM claude_reading WHERE bill_id=? AND doc_kind='summary'", (i,)).fetchone()[0])) for i in (291, 296, 303)))
ck("2 one audit row per change ('relane' + 'summary' for a moved paper; 'reread_summary' with what the bill reading had lent)",
   lambda: sqlite3.connect(ADB).execute("SELECT COUNT(*) FROM bill_audit WHERE bill_id=291 AND action IN ('relane','summary','reread_summary')").fetchone()[0] == 3)
ck("2 finance.db never written (the scratch and the dealer rows as seeded)", lambda: sqlite3.connect(FDB).execute("SELECT COUNT(*) FROM purchase_scan_state").fetchone()[0] == 1
   and sqlite3.connect(FDB).execute("SELECT COUNT(*) FROM s750_dealer_of").fetchone()[0] == 1)
s1 = snap()
rc, out = run("--real")
ck("2 a second REAL run: ALREADY DONE, nothing changed, no second backup", lambda: rc == 0 and "ALREADY DONE" in out and snap() == s1 and len(baks()) == 1)

print("2b · a re-read cut short after the row was cleared (B-0303) -- the same line again carries on")
for b in baks():
    os.remove(os.path.join(os.path.dirname(ADB), b))
seed(ADB, FDB)
_d = sqlite3.connect(ADB)
_d.execute("UPDATE bills SET vendor=NULL, bill_no=NULL, bill_date=NULL, total_amount=NULL, ocr_status='reading' WHERE id=303")
_d.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(303, '2026-11-08 19:40', 'S754 (the owner''s line)', 'reread_summary', '{}')")
_d.commit()
_d.close()
rc, out = run("--real")
ck("2b ... DONE, B-0303 re-read and filled (the end of October, the figure)", lambda: rc == 0 and "DONE." in out and R(303)["bill_date"] == "2026-10-31" and float(R(303)["total_amount"]) == 1200)

print("3 · the CONTROLS: each database broken one way refuses with nothing changed and no backup")


def control(name, breaker, fin=None):
    for b in baks():
        os.remove(os.path.join(os.path.dirname(ADB), b))
    seed(ADB, FDB)
    d = sqlite3.connect(ADB)
    d.execute(breaker) if isinstance(breaker, str) else breaker(d)
    d.commit()
    d.close()
    if fin:
        f = sqlite3.connect(FDB)
        f.execute(fin)
        f.commit()
        f.close()
    s = snap()
    rc, out = run("--real")
    ck("3 CONTROL %s -> REFUSED, nothing changed" % name, lambda: rc == 1 and "REFUSED" in out and snap() == s and not baks())


control("an amount off by Rs 2 (B-0298)", "UPDATE bills SET total_amount=60684 WHERE id=298")
control("scanned by someone else (B-0292)", "UPDATE bills SET submitted_by='Shivani' WHERE id=292")
control("scanned another day (B-0297)", "UPDATE bills SET submitted_at='2026-11-07 15:14:00' WHERE id=297")
control("a person approved / moved it after the scan (B-0293)", "INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(293, '2026-11-08 16:00', 'Shavez', 'relane', '{}')")
control("a person answered its question (B-0299)", "INSERT INTO scan_question(bill_id, kind, cand_id, detail, asked_at, answer, answered_by) VALUES(299, 'twin', 297, '', '2026-11-08', 'not', 'Shavez')")
control("an item line on it (B-0297)", "INSERT INTO bill_items(bill_id, item_name) VALUES(297, 'WALK754 ITEM')")
control("B-0296 no longer a page of B-0295", "UPDATE bills SET page_of=NULL WHERE id=296")
control("B-0295's file is not the merged one", "UPDATE bills SET source_stored='bill_walk754_other.pdf' WHERE id=295")
control("an outside paper set aside as a double of B-0291", lambda d: (d.execute("INSERT INTO bills(id, stamp_no, kind, lane, status, dup_of, submitted_at) VALUES(305, 'B-0305', 'Pharmacy', 'pharmacy', 'rejected', 291, '2026-11-08 18:00:00')")))
control("finance: B-0297 linked to a Marg bill", "SELECT 1", fin="INSERT INTO purchase_scan_link(asset_bill_id, bill_id) VALUES(297, 9)")
control("finance: a person confirmed B-0299's pairing", "SELECT 1", fin="INSERT INTO purchase_scan_state(asset_bill_id, confirmed_by) VALUES(299, 'Amir')")

print("walk_fix_s754: %d check(s) failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
