#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s750_app.py -- S750_MONTH_END on the REAL scan app (the Scan App's two files, PLANNED): asset_register.py and every part it mounts,
copied into a scratch folder, with the given asset_register.py and claude_reader.py (the kit's TO -- or the live FROM for the control) on a
MADE-UP, empty database the app creates itself. Made-up rows only ('WALK750 ...' dealers); the reader's HTTP call is replaced by a stub;
nothing is sent anywhere. The scratch folder is removed at the end.

    python3 -B walk_s750_app.py --live <the app folder> --files <folder holding asset_register.py and claude_reader.py> [--expect-red]
The last line: 'walk_s750_app: N check(s) failed (M of them S750 checks)'."""
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
KIT_FILES = ("asset_register.py", "claude_reader.py")

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s750app_")
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
        os.makedirs(os.path.join(work, "uploads"))
        os.makedirs(os.path.join(work, "key"))
        open(os.path.join(work, "key", "anthropic.key"), "w").write("made-up-walk-key\n")
        env = dict(os.environ, ASSETS_DB=os.path.join(work, "assets.db"), ASSETS_UPLOADS=os.path.join(work, "uploads"), SHARED_LIB_DIR=os.path.join(work, "noshared"),
                   SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"), SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1",
                   CLINIC_PORTAL_DIR=os.path.join(work, "noportal"), FINANCE_LOCAL_URL="http://127.0.0.1:9", FINANCE_DB_FOR_SCANS=os.path.join(work, "nofinance.db"),
                   PYTHONPYCACHEPREFIX=os.path.join(work, "pyc"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", "-W", "ignore", os.path.abspath(__file__), "--inner", app] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=300)
        sys.stdout.write(r.stdout)
        if r.returncode not in (0, 1) or os.environ.get("S750_WALK_DEBUG"):
            print(r.stderr[-3000:])
        if not r.stdout.strip().splitlines() or not r.stdout.strip().splitlines()[-1].startswith("walk_s750_app:"):
            print("walk_s750_app: the inner run did not finish (%s)" % (r.stderr.strip().splitlines()[-1][:200] if r.stderr.strip() else "no error text"))
            sys.exit(2)
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
APPD = ARGS[ARGS.index("--inner") + 1]
sys.path.insert(0, APPD)
FAILS, S750F = [], []


def ck(name, fn, s750=True):
    try:
        ok = bool(fn())
        d = ""
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, "(raised: %s)" % repr(e)[:160]
    print(("  ok   " if ok else "  FAIL ") + ("[S750] " if s750 else "") + name + ((" " + d) if d and not ok else ""))
    if not ok:
        FAILS.append(name)
        if s750:
            S750F.append(name)


import asset_register as ar                                          # noqa: E402

CR = sys.modules.get("claude_reader")
ck("A0 the real app loads; claude_reader is mounted", lambda: ar.app is not None and CR is not None, s750=False)
ck("A0 asset_register is S750's (KIT_S750) and claude_reader has read_summary / clean_summary / summary_to_bill",
   lambda: getattr(ar, "KIT_S750", "") == "S750_MONTH_END" and all(hasattr(CR, n) for n in ("read_summary", "clean_summary", "summary_to_bill", "SUMMARY_PROMPT")))
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='manoj'").fetchone()[0]
    ss["epoch"] = epoch

print("1 · the intake page: the summary button beside the challan button")
r = own.get("/intake?lane=pharmacy")
h = r.get_data(as_text=True)
ck("1 the intake answers (200)", lambda: r.status_code == 200, s750=False)
ck("1 the challan button is still there", lambda: 'id=challan_btn' in h, s750=False)
ck("1 the summary button, its hint, the hidden field and the JS (_summarySet) are on the page",
   lambda: 'id=summary_btn' in h and "DEALER KA MAHINE KA HISAAB (SUMMARY) HAI?" in h and 'id=summary_hint' in h and 'name=summary id=summary_basic' in h and "function _summarySet(" in h)
ck("1 the lane line says SUMMARY when the flag is on; Save resets both buttons", lambda: "' · SUMMARY'" in h and "_challanSet(false);_summarySet(false);" in h)
ck("1 the summary click is wired; a summary click clears a challan and the other way round", lambda: "sb.addEventListener('click'" in h and "_summarySet(false);}});}" in h and "_challanSet(false);}if(typeof _laneLine" in h)


def capture(lane, **fields):
    data = dict(lane=lane, note="", **{k: v for k, v in fields.items()})
    data["bill_file"] = (io.BytesIO(b"%PDF-1.4 made-up walk paper " + os.urandom(6)), "walk.pdf")
    rr = own.post("/intake/submit", data=data, content_type="multipart/form-data", follow_redirects=False)
    loc = rr.headers.get("Location") or ""
    m = re.search(r"/intake/slip/(\d+)", loc)
    return rr.status_code, (int(m.group(1)) if m else None), loc


print("2 · the capture: the tick lands as kind 'Summary', doc_kind 'summary' -- on the pharmacy lane only; a challan wins")
st, b1, loc = capture("pharmacy", summary="1")
row1 = db.execute("SELECT kind, doc_kind, lane, status FROM bills WHERE id=?", (b1,)).fetchone() if b1 else None
ck("2 a pharmacy scan with the summary tick: redirected to its slip", lambda: st in (302, 303) and b1 is not None, s750=False)
ck("2 ... lands as kind 'Summary', doc_kind 'summary', lane pharmacy, status captured",
   lambda: row1 is not None and row1["kind"] == "Summary" and row1["doc_kind"] == "summary" and row1["lane"] == "pharmacy" and row1["status"] == "captured")
ck("2 ... audited ('summary')", lambda: db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='summary'", (b1,)).fetchone() is not None)
slip = own.get(loc).get_data(as_text=True) if loc else ""
ck("2 ... the slip says 'SUMMARY — dealer ka mahine ka hisaab liya. Doctor sahab ki list par chala gaya.'", lambda: "SUMMARY — dealer ka mahine ka hisaab liya" in slip)
st, b2, loc2 = capture("pharmacy")
row2 = db.execute("SELECT kind, doc_kind FROM bills WHERE id=?", (b2,)).fetchone() if b2 else None
ck("2 a pharmacy scan WITHOUT the tick: kind 'Pharmacy' as before, no doc_kind; its slip carries no SUMMARY line",
   lambda: row2 is not None and row2["kind"] == "Pharmacy" and not row2["doc_kind"] and "SUMMARY —" not in own.get(loc2).get_data(as_text=True), s750=False)
st, b3, _ = capture("pharmacy", summary="1", challan="1")
row3 = db.execute("SELECT kind, doc_kind FROM bills WHERE id=?", (b3,)).fetchone() if b3 else None
ck("2 both ticks: the challan wins (kind 'Challan'), never 'Summary'", lambda: row3 is not None and row3["kind"] == "Challan" and row3["doc_kind"] == "challan")
st, b4, _ = capture("clinic", summary="1")
row4 = db.execute("SELECT kind, doc_kind FROM bills WHERE id=?", (b4,)).fetchone() if b4 else None
ck("2 the clinic lane ignores the tick (kind 'Consumable', no doc_kind)", lambda: row4 is not None and row4["kind"] == "Consumable" and not row4["doc_kind"])
ck("2 the widget's own door (/intake/scan_submit) carries the same field (the source names 'summary' twice: both call sites)",
   lambda: open(os.path.join(APPD, "asset_register.py"), encoding="utf-8").read().count('summary=(request.form.get("summary") == "1")') == 2)

print("3 · the reader: a Summary is read with the summary prompt; its row gets the dealer's name and figure, no items")
calls = []


def fake_post(body, key):
    calls.append(body)
    txt = body["messages"][0]["content"][-1]["text"]
    if "MONTHLY" in txt or "SUMMARY" in txt:
        ans = {"is_summary": True, "dealer": "WALK750 KEDAR PHARMA", "period_from": "2026-10-01", "period_to": "2026-10-31",
               "lines": [{"kind": "bill", "no": "A000198", "date": "2026-10-03", "amount": 7400}, {"kind": "bill", "no": "A000211", "date": "2026-10-17", "amount": 7290},
                         {"kind": "credit", "no": "CN-9", "date": "2026-10-20", "amount": -110}, {"kind": "weird", "no": "X", "date": None, "amount": 5},
                         {"kind": "payment", "no": "NEFT", "date": "2026-10-05", "amount": 30000}],
               "total_bills": 14690, "closing": 14580, "opening": None, "handwritten": False}
    else:
        ans = {"doc_kind": "bill", "vendor": "WALK750 BILL VENDOR", "bill_no": "B-1", "bill_date": "2026-10-02", "total_amount": 100, "items": []}
    return 200, {"content": [{"type": "text", "text": json.dumps(ans)}], "stop_reason": "end_turn"}, ""


if CR is not None:
    CR._post = fake_post
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','on')")
db.commit()
p1 = os.path.join(os.environ["ASSETS_UPLOADS"], db.execute("SELECT source_stored FROM bills WHERE id=?", (b1,)).fetchone()[0]) if b1 else ""
data = getattr(CR, "read_summary", lambda *a, **k: None)(p1, bid=b1, db_path=dbp) if CR else None
ck("3 read_summary returns the cleaned reading: doc_kind 'summary', the dealer, the period, 5 lines -> the unknown kind kept as 'other', amounts positive",
   lambda: data is not None and data["doc_kind"] == "summary" and data["dealer"] == "WALK750 KEDAR PHARMA" and data["period_to"] == "2026-10-31"
   and len(data["lines"]) == 5 and data["lines"][3]["kind"] == "other" and data["lines"][2]["amount"] == 110 and data["total_bills"] == 14690 and data["closing"] == 14580)
ck("3 ... the prompt sent was the SUMMARY prompt, not the bill's", lambda: calls and "MONTHLY" in calls[-1]["messages"][0]["content"][-1]["text"])
db.execute("CREATE TABLE IF NOT EXISTS claude_reading(bill_id INTEGER PRIMARY KEY, at TEXT NOT NULL, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT)")
rd = db.execute("SELECT ok, doc_kind, data FROM claude_reading WHERE bill_id=?", (b1,)).fetchone()
ck("3 ... recorded in claude_reading with doc_kind 'summary' (ok=1)", lambda: rd is not None and rd["ok"] == 1 and rd["doc_kind"] == "summary" and json.loads(rd["data"])["dealer"] == "WALK750 KEDAR PHARMA")
got = getattr(ar, "_s550_claude", lambda *a: None)(b1, p1)
ck("3 _s550_claude on a Summary: (hdr, []) -- the dealer's name, the period's last day and the closing figure; no items",
   lambda: got is not None and got[0].get("vendor") == "WALK750 KEDAR PHARMA" and got[0].get("total_amount") == 14580 and got[0].get("bill_date") == "2026-10-31" and got[1] == [])
p2 = os.path.join(os.environ["ASSETS_UPLOADS"], db.execute("SELECT source_stored FROM bills WHERE id=?", (b2,)).fetchone()[0]) if b2 else ""
got2 = getattr(ar, "_s550_claude", lambda *a: None)(b2, p2)
ck("3 _s550_claude on a Pharmacy bill: the bill prompt as before (vendor 'WALK750 BILL VENDOR')", lambda: got2 is not None and got2[0].get("vendor") == "WALK750 BILL VENDOR", s750=False)
ck("3 ... that call sent the BILL prompt", lambda: calls and "MONTHLY" not in calls[-1]["messages"][0]["content"][-1]["text"], s750=False)
sb = getattr(CR, "summary_to_bill", lambda d: (None, None))({"dealer": "X", "closing": None, "total_bills": 500, "period_to": "2026-09-30"})
ck("3 summary_to_bill falls back to total_bills when there is no closing", lambda: sb[0] is not None and sb[0]["total_amount"] == 500 and sb[0]["bill_no"] is None and sb[1] == [])
cs = getattr(CR, "clean_summary", lambda d: None)({"is_summary": False, "dealer": "Y", "lines": "not a list"})
ck("3 clean_summary: is_summary False kept, a non-list 'lines' -> []", lambda: cs is not None and cs["is_summary"] is False and cs["lines"] == [])
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.commit()
n0 = len(calls)
d0 = getattr(CR, "read_summary", lambda *a, **k: None)(p1, bid=b1, db_path=dbp) if CR else None
ck("3 the reader OFF: read_summary returns None and sends nothing", lambda: d0 is None and len(calls) == n0)
ck("3 the edit form's kind whitelists keep 'Summary' (as 'Challan')",
   lambda: open(os.path.join(APPD, "asset_register.py"), encoding="utf-8").read().count('"Challan", "Pharmacy expense", "Summary"') == 1
   and "'Challan','Pharmacy expense','Summary'" in open(os.path.join(APPD, "asset_register.py"), encoding="utf-8").read())

print("walk_s750_app: %d check(s) failed (%d of them S750 checks)" % (len(FAILS), len(S750F)))
sys.exit(1 if FAILS else 0)
