#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s754.py -- S754_SUMMARY_RECOGNISE on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch folder,
with the given asset_register.py, claude_reader.py and scan_checks_s441.py (the kit's TO -- or the live FROM for the control) on a MADE-UP,
empty database the app creates itself. Made-up rows only ('WALK754 ...' dealers); the reader's HTTP call is replaced by a stub; nothing is
sent anywhere. The scratch folder is removed at the end.

    python3 -B walk_s754.py --live <the app folder> --files <folder holding the three files> [--shared <folder holding scan_checks_s441.py>]
The last line: 'walk_s754: N check(s) failed (M of them S754 checks)'. The control (the live files) must end with M > 0."""
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
SHARED = opt("--shared", FILES)
KIT_FILES = ("asset_register.py", "claude_reader.py")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s754walk_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):                                   # the app's CODE only (top-level .py / .js / .json) -- never a stored scan
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in KIT_FILES:
            p = os.path.join(FILES, f)
            if not os.path.isfile(p):
                print("walk_s754: %s is not in %s" % (f, FILES))
                sys.exit(2)
            shutil.copy(p, os.path.join(app, f))
        shared = os.path.join(work, "shared")
        os.makedirs(shared)
        p = os.path.join(SHARED, "scan_checks_s441.py")
        if not os.path.isfile(p):
            print("walk_s754: scan_checks_s441.py is not in %s" % SHARED)
            sys.exit(2)
        shutil.copy(p, os.path.join(shared, "scan_checks_s441.py"))
        os.makedirs(os.path.join(work, "uploads"))
        os.makedirs(os.path.join(work, "key"))
        open(os.path.join(work, "key", "anthropic.key"), "w").write("made-up-walk-key\n")
        env = dict(os.environ, ASSETS_DB=os.path.join(work, "assets.db"), ASSETS_UPLOADS=os.path.join(work, "uploads"), SHARED_LIB_DIR=shared,
                   SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"), SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1",
                   CLINIC_PORTAL_DIR=os.path.join(work, "noportal"), FINANCE_LOCAL_URL="http://127.0.0.1:9", FINANCE_DB_FOR_SCANS=os.path.join(work, "nofinance.db"),
                   S441_MERGE_PY=os.path.join(work, "no-python"), S618_TURN_PY=os.path.join(work, "no-python"),
                   PYTHONPYCACHEPREFIX=os.path.join(work, "pyc"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", "-W", "ignore", os.path.abspath(__file__), "--inner", app] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=300)
        sys.stdout.write(r.stdout)
        if r.returncode not in (0, 1) or os.environ.get("S754_WALK_DEBUG"):
            print(r.stderr[-3000:])
        if not r.stdout.strip().splitlines() or not r.stdout.strip().splitlines()[-1].startswith("walk_s754:"):
            print("walk_s754: the inner run did not finish (%s)" % (r.stderr.strip().splitlines()[-1][:200] if r.stderr.strip() else "no error text"))
            sys.exit(2)
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
APPD = ARGS[ARGS.index("--inner") + 1]
sys.path.insert(0, APPD)
FAILS, S754F = [], []


def ck(name, fn, s754=True):
    try:
        ok = bool(fn())
        d = ""
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, "(raised: %s)" % repr(e)[:160]
    print(("  ok   " if ok else "  FAIL ") + ("[S754] " if s754 else "") + name + ((" " + d) if d and not ok else ""))
    if not ok:
        FAILS.append(name)
        if s754:
            S754F.append(name)


import asset_register as ar                                          # noqa: E402

CR = sys.modules.get("claude_reader")
S441 = sys.modules.get("scan_checks_s441")
ck("A0 the real app loads; claude_reader and scan_checks_s441 are mounted", lambda: ar.app is not None and CR is not None and S441 is not None, s754=False)
ck("A0 the three files are S754's (KIT_S754 in the app and the reader; read_pharmacy; the S441 statement test)",
   lambda: getattr(ar, "KIT_S754", "") == "S754_SUMMARY_RECOGNISE" and getattr(CR, "KIT_S754", "") == "S754_SUMMARY_RECOGNISE"
   and hasattr(CR, "read_pharmacy") and hasattr(S441, "_s754_statement"))
ck("A0 S750 is still there underneath (read_summary, summary_to_bill, KIT_S750)",
   lambda: getattr(ar, "KIT_S750", "") == "S750_MONTH_END" and hasattr(CR, "read_summary") and hasattr(CR, "summary_to_bill"), s754=False)
dbp = os.environ["ASSETS_DB"]
UP = os.environ["ASSETS_UPLOADS"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='manoj'").fetchone()[0]
    ss["epoch"] = epoch

# ---------------------------------------------------------------- the stub reader: what the paper "is" is set per test
MODE = {"m": "statement"}
calls = []
ANS = {
    "statement": {"is_summary": True, "dealer": "WALK754 KEDAR PHARMA", "period_from": None, "period_to": "2026-11-02", "as_on": "2026-11-02",
                  "continued": False,
                  "lines": [{"kind": "bill", "no": "A000198", "date": "2026-10-03", "amount": 7400},
                            {"kind": "bill", "no": "A000211", "date": "2026-10-17", "amount": 7290}],
                  "total_bills": 14690, "closing": 14690, "opening": None, "handwritten": False},
    "statement_buyer": {"is_summary": True, "dealer": "SANJEEVNI MEDICOS", "period_from": "2026-10-01", "period_to": "2026-10-15",
                        "lines": [{"kind": "bill", "no": "RT-1", "date": "2026-10-04", "amount": 1000},
                                  {"kind": "bill", "no": "RT-2", "date": "2026-10-12", "amount": 2656}],
                        "total_bills": 3656, "closing": 3656, "continued": False, "handwritten": False},
    "continued": {"is_summary": True, "dealer": None, "period_from": None, "period_to": None, "continued": True,
                  "lines": [{"kind": "bill", "no": "A000230", "date": "2026-10-25", "amount": 500},
                            {"kind": "bill", "no": "A000231", "date": "2026-10-26", "amount": 600}],
                  "total_bills": None, "closing": 15790, "handwritten": False},
    "bill": {"is_summary": False, "doc_kind": "tax_invoice", "vendor": "WALK754 BILL VENDOR", "bill_no": "INV-77", "bill_date": "2026-10-02",
             "total_amount": 100, "items": [{"name": "WALK754 TAB", "qty": 1, "rate": 100, "amount": 100}]},
    "page": {"is_summary": False, "doc_kind": "bill", "vendor": None, "bill_no": None, "bill_date": None, "total_amount": 50, "items": []},
}


def fake_post(body, key):
    calls.append(body)
    return 200, {"content": [{"type": "text", "text": json.dumps(ANS[MODE["m"]])}], "stop_reason": "end_turn"}, ""


CR._post = fake_post


def txt(i=-1):
    return calls[i]["messages"][0]["content"][-1]["text"] if calls else ""


def capture(lane, **fields):
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")      # no background read at capture: the walk reads
    db.commit()
    data = dict(lane=lane, note="", **fields)
    data["bill_file"] = (io.BytesIO(b"%PDF-1.4 made-up walk754 paper " + os.urandom(8)), "walk.pdf")
    rr = own.post("/intake/submit", data=data, content_type="multipart/form-data", follow_redirects=False)
    m = re.search(r"/intake/slip/(\d+)", rr.headers.get("Location") or "")
    bid = int(m.group(1)) if m else None
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','on')")
    db.commit()
    return bid


def row(bid):
    return db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()


def path(bid):
    return os.path.join(UP, row(bid)["source_stored"])


def reading(bid):
    r = db.execute("SELECT ok, doc_kind, data FROM claude_reading WHERE bill_id=?", (bid,)).fetchone()
    return (r["ok"], r["doc_kind"], json.loads(r["data"]) if r["data"] else {}) if r else (None, None, {})


print("1 · the cleaner: the dealer is never the buyer; the period from the bills")
cs = CR.clean_summary(dict(ANS["statement"]))
ck("1 an 'as on 02-11' statement of October bills: the period is October (01 .. 31), the read period kept beside it, period_by 'bills'",
   lambda: cs["period_from"] == "2026-10-01" and cs["period_to"] == "2026-10-31" and cs["period_by"] == "bills"
   and cs["period_to_as_read"] == "2026-11-02" and cs["as_on"] == "2026-11-02")
cb = CR.clean_summary(dict(ANS["statement_buyer"]))
ck("1 a dealer read as 'SANJEEVNI MEDICOS' (the buyer) -> null, dealer_was_buyer true; a printed 01..15 Oct period kept ('paper')",
   lambda: cb["dealer"] is None and cb.get("dealer_was_buyer") is True and cb["period_from"] == "2026-10-01" and cb["period_to"] == "2026-10-15" and cb["period_by"] == "paper")
ck("1 the buyer in other spellings (Sanjivani Medicose, M/s Sanjeevani Medical Store, Sanjeevni) -> null; a real dealer's name is kept",
   lambda: all(CR.clean_summary({"dealer": n, "lines": []})["dealer"] is None for n in ("Sanjivani Medicose", "M/s Sanjeevani Medical Store", "SANJEEVNI", "Medicos"))
   and CR.clean_summary({"dealer": "L.K. DRUG HOUSE", "lines": []})["dealer"] == "L.K. DRUG HOUSE"
   and CR.clean_summary({"dealer": "DAANSHI PHARMA", "lines": []})["dealer"] == "DAANSHI PHARMA")
cn = CR.clean_summary({"dealer": "X", "period_from": None, "period_to": None, "lines": [{"kind": "bill", "no": "1", "date": "2026-09-30", "amount": 1},
                                                                                     {"kind": "bill", "no": "2", "date": "2026-10-02", "amount": 1},
                                                                                     {"kind": "bill", "no": "3", "date": "2026-10-09", "amount": 1}]})
ck("1 no period printed: the month most bills fall in (October, 2 of 3)", lambda: cn["period_from"] == "2026-10-01" and cn["period_to"] == "2026-10-31")
cp2 = CR.clean_summary({"dealer": "X", "period_from": "2026-08-01", "period_to": "2026-10-31", "lines": [{"kind": "bill", "no": "1", "date": "2026-09-03", "amount": 1},
                                                                                                    {"kind": "bill", "no": "2", "date": "2026-09-20", "amount": 1}]})
ck("1 a PRINTED period (01-08 .. 31-10) is kept as printed even when most bills fall in one month", lambda: cp2["period_from"] == "2026-08-01" and cp2["period_to"] == "2026-10-31" and cp2["period_by"] == "paper")
c0 = CR.clean_summary({"dealer": "X", "period_from": None, "period_to": "2026-11-02", "lines": [{"kind": "bill", "no": "1", "date": None, "amount": 1}]})
ck("1 no dated line: the period stays as read", lambda: c0["period_to"] == "2026-11-02" and c0["period_from"] is None)
ck("1 the contract keys S750's reader writes are all still there (is_summary, dealer, period_from, period_to, lines[kind,no,date,amount], total_bills, opening, closing)",
   lambda: all(k in cs for k in ("is_summary", "dealer", "period_from", "period_to", "lines", "total_bills", "opening", "closing"))
   and all(k in cs["lines"][0] for k in ("kind", "no", "date", "amount")), s754=False)
ck("1 the summary prompt names the seller rule and the 'as on' rule", lambda: "the BUYER" in CR.SUMMARY_PROMPT and "as_on" in CR.SUMMARY_PROMPT)
ck("1 the bill prompt itself is untouched (no statement paragraph in PROMPT)", lambda: "PHARMACY LANE" not in CR.PROMPT, s754=False)

print("2 · a pharmacy paper WITHOUT the tick: one call; a statement lands as kind 'Summary'")
MODE["m"] = "statement"
b1 = capture("pharmacy")
n0 = len(calls)
got = ar._s550_claude(b1, path(b1))
r1 = row(b1)
ok1, dk1, d1 = reading(b1)
ck("2 ONE call to the reader, with the pharmacy prompt (the statement paragraph)", lambda: len(calls) == n0 + 1 and "THIS PAPER CAME IN ON THE PHARMACY LANE" in txt())
ck("2 the row is now kind 'Summary', doc_kind 'summary', lane pharmacy, status captured",
   lambda: r1["kind"] == "Summary" and r1["doc_kind"] == "summary" and r1["lane"] == "pharmacy" and r1["status"] == "captured")
ck("2 audited 'summary' via 'recognised (S754)'",
   lambda: db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='summary' AND detail LIKE '%recognised (S754)%'", (b1,)).fetchone() is not None)
ck("2 claude_reading: ok, doc_kind 'summary', is_summary true, recognised true, the period October from the bills",
   lambda: ok1 == 1 and dk1 == "summary" and d1.get("is_summary") is True and d1.get("recognised") is True and d1.get("period_to") == "2026-10-31")
ck("2 the row is lent the dealer, the period's last day and the figure -- no bill number, no items",
   lambda: got is not None and got[0]["vendor"] == "WALK754 KEDAR PHARMA" and got[0]["bill_no"] is None and got[0]["bill_date"] == "2026-10-31"
   and got[0]["total_amount"] == 14690 and got[1] == [])

MODE["m"] = "bill"
b2 = capture("pharmacy")
n0 = len(calls)
got2 = ar._s550_claude(b2, path(b2))
ok2, dk2, d2 = reading(b2)
ck("2 a single bill stays a bill: kind 'Pharmacy', its vendor, bill number and items as before; one call",
   lambda: row(b2)["kind"] == "Pharmacy" and not row(b2)["doc_kind"] and got2 is not None and got2[0]["vendor"] == "WALK754 BILL VENDOR"
   and got2[0]["bill_no"] == "INV-77" and len(got2[1]) == 1 and len(calls) == n0 + 1, s754=False)
ck("2 ... its reading is recorded as a bill (doc_kind 'tax_invoice'), in the bill's own shape", lambda: ok2 == 1 and dk2 == "tax_invoice" and d2.get("vendor") == "WALK754 BILL VENDOR", s754=False)

print("3 · the tick still wins; the clinic lane and the switch")
MODE["m"] = "statement_buyer"
b3 = capture("pharmacy", summary="1")
got3 = ar._s550_claude(b3, path(b3))
ck("3 a ticked summary is read with the SUMMARY prompt (not the pharmacy one)", lambda: "MONTHLY" in txt() and "THIS PAPER CAME IN ON THE PHARMACY LANE" not in txt(), s754=False)
ck("3 ... its buyer-named dealer is lent to the row as nothing (vendor null), the printed period kept",
   lambda: got3 is not None and got3[0]["vendor"] is None and got3[0]["bill_date"] == "2026-10-15")
MODE["m"] = "statement"
b4 = capture("clinic")
got4 = ar._s550_claude(b4, path(b4))
ck("3 the clinic lane: the bill prompt as before (no statement paragraph), the row stays kind 'Consumable'",
   lambda: "THIS PAPER CAME IN ON THE PHARMACY LANE" not in txt() and "MONTHLY" not in txt() and row(b4)["kind"] == "Consumable" and not row(b4)["doc_kind"], s754=False)
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.summary_recognise','off')")
db.commit()
b5 = capture("pharmacy")
ar._s550_claude(b5, path(b5))
ck("3 the switch 'read.summary_recognise' = off: a pharmacy paper is read with the plain bill prompt and stays 'Pharmacy'",
   lambda: "THIS PAPER CAME IN ON THE PHARMACY LANE" not in txt() and row(b5)["kind"] == "Pharmacy")
db.execute("DELETE FROM settings WHERE key='read.summary_recognise'")
db.commit()
MODE["m"] = "bill"
b6 = capture("pharmacy", challan="1")
ar._s550_claude(b6, path(b6))
ck("3 a challan is never asked the statement question (kind 'Challan', the plain prompt)",
   lambda: "THIS PAPER CAME IN ON THE PHARMACY LANE" not in txt() and row(b6)["kind"] == "Challan", s754=False)

print("4 · the whole reading (_bg_extract) and the forgotten-page rule")


def age_all():
    """Every paper so far scanned an hour earlier, so each scenario below stands alone in the five-minute window."""
    db.execute("UPDATE bills SET submitted_at=datetime(submitted_at, '-60 minutes')")
    db.commit()


age_all()
MODE["m"] = "statement_buyer"
h1 = capture("pharmacy", summary="1")                                  # a ticked Summary (Janta's B-0295 in the story)
ar._bg_extract(h1, path(h1))
MODE["m"] = "statement"
p1 = capture("pharmacy")                                               # a minute later, the same person, another statement, no tick
db.execute("UPDATE bills SET vendor=NULL WHERE id=?", (p1,)); db.commit()
ANS["statement_nv"] = dict(ANS["statement"], dealer=None)
MODE["m"] = "statement_nv"                                             # no seller printed (L.K. Drug House's B-0296)
st = ar._bg_extract(p1, path(p1))
rp1 = row(p1)
ck("4 the whole reading of an untick statement: kind 'Summary', ocr 'read', bill_date 2026-10-31, the figure, no bill number",
   lambda: rp1["kind"] == "Summary" and rp1["ocr_status"] == "read" and rp1["bill_date"] == "2026-10-31" and float(rp1["total_amount"]) == 14690 and not rp1["bill_no"])
ck("4 a complete statement scanned a minute after a Summary by the same person is NOT joined as its page 2 (not set aside, page_of empty)",
   lambda: rp1["status"] == "captured" and not rp1["page_of"])
ck("4 ... and the Summary before it keeps its own single file (no merge audited)",
   lambda: db.execute("SELECT COUNT(*) FROM bill_audit WHERE bill_id=? AND action='s441_page_merged'", (h1,)).fetchone()[0] == 0)
MODE["m"] = "statement_buyer"
age_all()
h2 = capture("pharmacy", summary="1")
ar._bg_extract(h2, path(h2))
MODE["m"] = "continued"
p2 = capture("pharmacy")
ar._bg_extract(p2, path(p2))
ck("4 a statement's CONTINUED page (no heading) right after a Summary still joins it as its page (set aside, page_of = the Summary)",
   lambda: row(p2)["page_of"] == h2 and row(p2)["status"] == "rejected")
MODE["m"] = "bill"
age_all()
h3 = capture("pharmacy")
ar._bg_extract(h3, path(h3))
MODE["m"] = "continued"
p3 = capture("pharmacy")
ar._bg_extract(p3, path(p3))
ck("4 a continued statement page after a plain BILL is not joined to that bill", lambda: not row(p3)["page_of"] and row(p3)["status"] != "rejected")
ANS["bill2"] = dict(ANS["bill"], vendor="WALK754 OTHER TRADERS", bill_no="Z-5150", total_amount=777)     # not a double of the bill above
MODE["m"] = "bill2"
age_all()
h4 = capture("pharmacy")
ar._bg_extract(h4, path(h4))
MODE["m"] = "page"
p4 = capture("pharmacy")
ar._bg_extract(p4, path(p4))
ck("4 the rule as before: a bill's forgotten page (no header, a total) is joined to the bill before it", lambda: row(p4)["page_of"] == h4, s754=False)

print("5 · the lane button: a summary keeps kind 'Summary' on the pharmacy lane; a person can undo a wrong recognition")
own.post("/bills/%d/lane" % b3, data={"lane": "clinic"})
ck("5 a (ticked) Summary moved to the clinic lane takes the clinic's kind (Consumable, a draft) -- doc_kind 'summary' kept",
   lambda: row(b3)["lane"] == "clinic" and row(b3)["kind"] == "Consumable" and row(b3)["doc_kind"] == "summary", s754=False)
rr = own.post("/bills/%d/approve" % b3, data={})
ck("5 ... a summary on the clinic lane (a draft) is never approved as spend: Approve refuses it, it stays a draft",
   lambda: row(b3)["status"] == "draft" and row(b3)["doc_kind"] == "summary")
own.post("/bills/%d/lane" % b3, data={"lane": "pharmacy"})
ck("5 ... moved back to the pharmacy lane: kind 'Summary' again (healed after the POST), audited 'kind'",
   lambda: row(b3)["lane"] == "pharmacy" and row(b3)["kind"] == "Summary"
   and db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='kind' AND who='server (S754 heal)'", (b3,)).fetchone() is not None)
db.execute("UPDATE bills SET lane='pharmacy', kind='Pharmacy', status='captured' WHERE id=?", (b3,))      # as another road (the desk) would put it
db.commit()
ck("5 a summary put on the pharmacy lane as 'Pharmacy' by another road is healed (at start / after a POST / after a reading)",
   lambda: ar._s754_heal() >= 1 and row(b3)["kind"] == "Summary")
db.execute("UPDATE bills SET kind='Pharmacy' WHERE id=?", (b3,))
db.commit()
MODE["m"] = "statement"
n0 = len(calls)
ar._s550_claude(b3, path(b3))
ck("5 ... and a reading that starts before the heal (S731's read after the lane button) takes the summary road, not the bill's",
   lambda: row(b3)["kind"] == "Summary" and "MONTHLY" in txt() and len(calls) == n0 + 1)
own.post("/bills/%d/lane" % b1, data={"lane": "clinic"})
own.post("/bills/%d/lane" % b1, data={"lane": "pharmacy"})
ck("5 a WRONG recognition undone by a person (the recognised B moved off the pharmacy lane and back): it stays 'Pharmacy', not healed",
   lambda: row(b1)["lane"] == "pharmacy" and row(b1)["kind"] == "Pharmacy" and ar._s754_heal(only=b1) == 0)
own.post("/bills/%d/lane" % b2, data={"lane": "clinic"})
own.post("/bills/%d/lane" % b2, data={"lane": "pharmacy"})
ck("5 a bill moved off and back stays 'Pharmacy'", lambda: row(b2)["kind"] == "Pharmacy", s754=False)
ck("5 the lane button keeps S731's wrap (S754 heals after the POST instead of wrapping it)",
   lambda: getattr(ar.app.view_functions["bill_lane"], "_s731", False), s754=False)
cp = sys.modules.get("clinic_papers")
ck("5 the papers page's history rule never moves a summary (auto_home returns nothing for it)",
   lambda: cp is not None and getattr(cp.auto_home, "_s754", False) and cp.auto_home(db, b3) == [])
b8 = capture("pharmacy")
db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?, '2026-11-08 19:00:00', 'walk', 1, 'summary', ?)",
           (b8, json.dumps({"doc_kind": "summary", "is_summary": True, "recognised": True, "lines": []})))
db.commit()
ck("5 a recognised reading whose row was never made a Summary (the database was busy) is healed from the reading",
   lambda: ar._s754_heal() >= 1 and row(b8)["kind"] == "Summary" and row(b8)["doc_kind"] == "summary")

print("6 · the reader OFF: nothing is sent")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.commit()
n0 = len(calls)
MODE["m"] = "statement"
b7 = capture("pharmacy")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.commit()
ck("6 _s550_claude with the reader off returns None and sends nothing", lambda: ar._s550_claude(b7, path(b7)) is None and len(calls) == n0 and row(b7)["kind"] == "Pharmacy", s754=False)

print("walk_s754: %d check(s) failed (%d of them S754 checks)" % (len(FAILS), len(S754F)))
sys.exit(1 if FAILS else 0)
