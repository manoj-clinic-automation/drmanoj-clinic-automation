#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s841_app.py -- S841_PHARMACY_CREDIT_NOTE on the REAL scan app: the app folder copied into a scratch folder with the given
asset_register.py and claude_reader.py (TO -- or the live files for the control), on a fresh database the app makes itself. Made-up
rows only ("Walk Dealer841", dated 2031); the reader's answer is made up in the process (nothing leaves it). The scratch is removed.

    python3 -B walk_s841_app.py --live <the app folder> --shared <the shared folder> --files <folder holding the files to test> [--expect-red]
"""
import json, os, re, shutil, sqlite3, subprocess, sys, tempfile

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


LIVE, FILES = opt("--live", "/root/assetapp"), opt("--files")
EXPECT_RED = "--expect-red" in ARGS
KIT_FILES = ("asset_register.py", "claude_reader.py")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
GREEN_BOTH = ("A0", "R2", "I2", "I3", "I5", "H3", "H5", "S1", "Z1")       # the app loads; clean() (S835) keeps an answered credit note; a bill,
#                                                                     a statement, a clinic paper, a person's
#                                                                     answer, the switch off and an ordinary edit are as before

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s841app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in KIT_FILES:
            p = os.path.join(FILES, f)
            if os.path.isfile(p):
                shutil.copy(p, os.path.join(app, f))
        SHARED = opt("--shared")
        if SHARED:
            shutil.copytree(SHARED, os.path.join(work, "shared"), ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
        for d in ("uploads", "key"):
            os.makedirs(os.path.join(work, d))
        open(os.path.join(work, "key", "anthropic.key"), "w").write("made-up-walk-key\n")
        fin, spn = os.path.join(work, "finance.db"), os.path.join(work, "spine.db")
        for p_ in (fin, spn):
            sqlite3.connect(p_).close()
        env = dict(os.environ, ASSETS_DB=os.path.join(work, "assets.db"), ASSETS_UPLOADS=os.path.join(work, "uploads"),
                   SHARED_LIB_DIR=os.path.join(work, "shared" if SHARED else "noshared"),
                   SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"),
                   SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1", CLINIC_PORTAL_DIR=os.path.join(work, "noportal"),
                   FINANCE_LOCAL_URL="http://127.0.0.1:9", FINANCE_DB_FOR_SCANS=fin, SPINE_DB_FOR_SCANS=spn,
                   READER_WATCH_STATE=os.path.join(work, "rw_state.json"), READER_WATCH_STUB=os.path.join(work, "rw_sent.jsonl"),
                   READER_WATCH_ALL_OFF=os.path.join(work, "_off", "ALL_OFF"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app, work] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=600)
        sys.stdout.write(r.stdout)
        for l in r.stderr.splitlines():
            if "NOT mounted" in l or "S841" in l or "NOT installed" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S841_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
APPD = ARGS[ARGS.index("--inner") + 1]
WORK = ARGS[ARGS.index("--inner") + 2]
_me = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") not in (_me, os.path.abspath("."))]   # never the kit's own copies (F-1415)
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
ck("A0 the real app loads with its seven parts mounted", lambda: all(mods.values()), lambda: [m for m, x in mods.items() if x is None])
cr = sys.modules.get("claude_reader") or __import__("claude_reader")
cp = mods["clinic_papers"]
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s841','Walk owner','owner','x',1)")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-01-01')")
db.execute("CREATE TABLE IF NOT EXISTS claude_reading(bill_id INTEGER PRIMARY KEY, at TEXT, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT)")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_own_s841'").fetchone()[0]
    ss["epoch"] = epoch
N = [0]
D = "Walk Dealer841"


def mk(no, amt=None, lane="pharmacy", kind="Pharmacy", status="captured", dk=None, sub=None, vendor=None):
    N[0] += 1
    f = os.path.join(os.environ["ASSETS_UPLOADS"], "walk841_%d.pdf" % N[0])
    open(f, "wb").write(b"%PDF-1.4 made-up walk paper\n")
    cur = db.execute("INSERT INTO bills(kind, vendor, bill_no, bill_date, total_amount, status, lane, subgroup, doc_kind, created_at, stamp_no, source_stored) "
                     "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (kind, vendor, no, None, amt, status, lane, sub, dk, "2031-03-12 06:00:00",
                                                         "B-%04d" % (8410 + N[0]), "walk841_%d.pdf" % N[0]))
    db.commit()
    return cur.lastrowid, f


def row(i):
    return db.execute("SELECT * FROM bills WHERE id=?", (i,)).fetchone()


SENT = []
ANSWER = [None]


def fake_post(body, key):
    try:
        SENT.append("".join(c.get("text", "") for m in body.get("messages") or [] for c in m.get("content") or [] if isinstance(c, dict)))
    except Exception:                                                # noqa: BLE001
        SENT.append("")
    return 200, {"content": [{"type": "text", "text": json.dumps(ANSWER[0])}], "stop_reason": "end_turn"}, ""


cr._post_before_s783 = fake_post
cr._block = lambda path: ({"type": "text", "text": "made-up page"}, None)
CNA = {"doc_kind": "credit_note", "is_summary": False, "vendor": D, "bill_no": "CN-841", "bill_date": "2031-03-12", "total_amount": 500,
       "against_no": "WD-803", "items": [{"name": "WALKITEM", "qty": 1, "rate": 500, "amount": 500}]}
BILL = {"doc_kind": "tax_invoice", "is_summary": False, "vendor": D, "bill_no": "WD-900", "bill_date": "2031-03-10", "total_amount": 1410,
        "items": [{"name": "WALKITEM", "qty": 2, "rate": 705, "amount": 1410}]}
STMT = {"is_summary": True, "dealer": D, "period_from": "2031-02-01", "period_to": "2031-02-28", "as_on": None, "continued": False,
        "lines": [{"kind": "bill", "no": "WD-1", "date": "2031-02-03", "amount": 100}, {"kind": "credit", "no": "CN-1", "date": "2031-02-09", "amount": 20}],
        "total_bills": 100, "closing": 80, "opening": None, "handwritten": False}
SANJ = "SELECT id FROM bills WHERE kind='Pharmacy' AND status='captured'"    # scan_register.py's own selection (Sanjeevni)


def intake(answer, **kw):
    i, f = mk(kw.pop("no", None), **kw)
    ANSWER[0] = answer
    ar._bg_extract(i, f)
    return i


# ---- R: the reader
ph, ph0, pr = getattr(cr, "PHARMACY_PROMPT", ""), getattr(cr, "_S783_PROMPT_BEFORE", ""), getattr(cr, "PROMPT", "")
c1 = cr.clean_pharmacy(dict(CNA)) or {}
c2 = cr.clean_pharmacy(dict(BILL)) or {}
ck("R1 the pharmacy reader (and its long-bill fallback) asks for a credit note with its own rule; the desk's reader is unchanged",
   lambda: '| "credit_note" |' in ph and "money a supplier gives BACK to the pharmacy" in ph and '| "credit_note" |' in ph0
   and "BACK to the pharmacy" in ph0 and ph.count('"doc_kind": "tax_invoice"') == 1 and "BACK to the pharmacy" not in pr
   and "money the supplier gives BACK to the clinic" in pr)
ck("R2 a credit-note answer is kept as a credit note with the invoice it names; a bill's answer stays a bill",
   lambda: c1.get("doc_kind") == "credit_note" and c1.get("against_no") == "WD-803" and c2.get("doc_kind") == "tax_invoice" and "against_no" not in c2,
   lambda: (c1, c2))

# ---- I: intake on the pharmacy lane, through the app's own _bg_extract
i1 = intake(CNA)
r1 = row(i1)
au = db.execute("SELECT who, detail FROM bill_audit WHERE bill_id=? AND action='kind'", (i1,)).fetchall()
ck("I1 a credit note scanned on the pharmacy lane: kind 'Pharmacy credit note', doc_kind credit_note, its no. and amount filled, "
   "recorded -- and Sanjeevni's register selection never sees it",
   lambda: r1["kind"] == "Pharmacy credit note" and r1["doc_kind"] == "credit_note" and r1["bill_no"] == "CN-841"
   and float(r1["total_amount"] or 0) == 500 and r1["lane"] == "pharmacy" and r1["status"] == "captured"
   and any("S841" in (w or "") for w, _ in au) and i1 not in [x[0] for x in db.execute(SANJ)],
   lambda: (dict(r1), [tuple(x) for x in au]))
ck("I4 the words the pharmacy reader was sent for that paper ask for a credit note",
   lambda: any("CAME IN ON THE PHARMACY LANE" in x and "BACK to the pharmacy" in x for x in SENT),
   lambda: [x[:60] for x in SENT])
i2 = intake(BILL)
r2 = row(i2)
ck("I2 a pharmacy bill stays kind 'Pharmacy' (Sanjeevni pairs it as before)",
   lambda: r2["kind"] == "Pharmacy" and (r2["doc_kind"] or "") == "" and r2["bill_no"] == "WD-900" and i2 in [x[0] for x in db.execute(SANJ)],
   lambda: dict(r2))
i3 = intake(STMT)
r3 = row(i3)
ck("I3 a dealer's statement is still recognised as a Summary (S754)", lambda: r3["kind"] == "Summary" and r3["doc_kind"] == "summary", lambda: dict(r3))
i5 = intake(dict(CNA, bill_no="CN-CL", vendor="Walk Fresh841"), lane="clinic", kind="Consumable", status="draft")
r5 = row(i5)
ck("I5 a credit note on the clinic lane is left to the desk (kind unchanged, no S841 mark)",
   lambda: r5["kind"] == "Consumable" and r5["lane"] == "clinic"
   and not db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND who LIKE '%S841%'", (i5,)).fetchone(), lambda: dict(r5))
i6 = intake(dict(CNA, bill_no="CN-HIST"), lane="clinic", kind="Consumable", status="draft")      # this dealer's papers are all pharmacy
r6 = row(i6)
ck("I6 a clinic credit note the history rule moves onto the pharmacy lane is never kind 'Pharmacy' there",
   lambda: r6["lane"] == "pharmacy" and r6["kind"] == "Pharmacy credit note" and i6 not in [x[0] for x in db.execute(SANJ)], lambda: dict(r6))

# ---- D: the desk opens it with S835's box (the owner)
r = own.get("/desk/api/paper/%d" % i1)
j = r.get_json(silent=True) or {}
ck("D1 the intake's credit note opens on the desk with the credit note box", lambda: r.status_code == 200 and j.get("cn") is not None,
   lambda: (r.status_code, str(j)[:300]))

# ---- H: the heal
h1, _ = mk("CN-H1", 300, dk="credit_note")
db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (h1, "2031-03-12 07:00", "walk", "relane", "{}"))
db.commit()
own.post("/desk/api/save", json={})                                  # any POST: the after-request heal
ck("H1 a credit note put back on the pharmacy lane as 'Pharmacy' is healed after a POST", lambda: row(h1)["kind"] == "Pharmacy credit note",
   lambda: dict(row(h1)))
h2, _ = mk("CN-H2", 200)
db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,1,?,?)",
           (h2, "2031-03-12 07:00", "walk", "credit_note", json.dumps(dict(CNA, bill_no="CN-H2"))))
h3, _ = mk("CN-H3", 200, dk="bill")                                  # a person on the desk said: a bill
h4, _ = mk("CN-H4", 200)                                             # a clinic credit note a PERSON moved onto the pharmacy lane
for h in (h3, h4):
    db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,1,?,?)",
               (h, "2031-03-12 07:00", "walk", "credit_note", json.dumps(CNA)))
db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (h4, "2031-03-12 07:10", "walk", "relane", "{}"))
db.commit()
heal = getattr(ar, "_s841_heal", None)
n = heal() if heal else 0
ck("H2 a paper whose reading says credit note but whose row was never marked is healed (what the start does)",
   lambda: row(h2)["kind"] == "Pharmacy credit note" and row(h2)["doc_kind"] == "credit_note", lambda: (n, dict(row(h2))))
ck("H3 a person's answer stands: a paper the desk saved as a bill is not healed", lambda: row(h3)["kind"] == "Pharmacy")
ck("H6 a credit note a person moved onto the pharmacy lane (read as one) is marked, never left as 'Pharmacy'",
   lambda: row(h4)["kind"] == "Pharmacy credit note", lambda: dict(row(h4)))
h5 = intake(dict(CNA, bill_no="CN-H5"))                              # marked by this kit at intake ...
db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (h5, "2031-03-12 08:00", "walk", "relane", "{}"))
db.execute("UPDATE bills SET kind='Pharmacy' WHERE id=?", (h5,))     # ... then a person moved it off the lane and back (a wrong recognition)
db.commit()
own.post("/desk/api/save", json={})
ck("H5 the way back: a paper this kit marked that a person moves off the lane and back stays 'Pharmacy' (not marked again)",
   lambda: row(h5)["kind"] == "Pharmacy", lambda: dict(row(h5)))

# ---- G: the papers page's history rule holds a pharmacy credit note
for k_ in range(3):                                                  # a dealer whose earlier papers are all sorted into one clinic group
    mk("WC-%d" % k_, 100, lane="clinic", kind="Consumable", status="approved", sub="procedure", vendor="Walk Clinic841")
gi, _ = mk("CN-G1", 100, kind="Pharmacy credit note", dk="credit_note", vendor="Walk Clinic841")
g = cp.auto_home(db, gi) if hasattr(cp, "auto_home") else None
db.commit()
ck("G1 the history rule never moves a pharmacy credit note (even a dealer whose papers are all clinic)",
   lambda: g == [] and row(gi)["lane"] == "pharmacy" and row(gi)["kind"] == "Pharmacy credit note", lambda: (g, dict(row(gi))))

# ---- E: the bill's edit page keeps the kind (F-1422)
r = own.get("/bills/%d/edit" % i1)
page = r.get_data(as_text=True)
ck("E2 the edit page shows the kind kept, no kind choice", lambda: r.status_code == 200 and "<b>Pharmacy credit note</b>" in page,
   lambda: (r.status_code, re.findall(r"Kind</label>.{0,200}", page)[:1]))
r = own.post("/bills/%d/edit" % i1, data={"vendor": D, "bill_no": "CN-841", "bill_date": "12-03-2031", "total_amount": "500"})
ck("E1 an edit of a pharmacy credit note keeps kind 'Pharmacy credit note' (no fall-through to Consumable)",
   lambda: r.status_code in (200, 302) and row(i1)["kind"] == "Pharmacy credit note", lambda: (r.status_code, dict(row(i1))))
z, _ = mk("Z-1", 50, lane="clinic", kind="Consumable", status="draft", vendor="Walk Other841")
r = own.post("/bills/%d/edit" % z, data={"kind": "Asset", "vendor": "Walk Other841", "bill_no": "Z-1", "bill_date": "12-03-2031", "total_amount": "50"})
ck("Z1 an ordinary clinic draft's edit still takes the form's kind", lambda: r.status_code in (200, 302) and row(z)["kind"] == "Asset", lambda: dict(row(z)))

# ---- S: the switch
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.pharmacy_cn','off')")
db.commit()
s1 = intake(dict(CNA, bill_no="CN-S1"))
db.execute("DELETE FROM settings WHERE key='read.pharmacy_cn'")
db.commit()
ck("S1 with read.pharmacy_cn off nothing is marked (the reading is still kept)", lambda: row(s1)["kind"] == "Pharmacy", lambda: dict(row(s1)))

red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    must = [k for k in RES if k not in GREEN_BOTH]
    stayed = [k for k in must if RES[k]]
    bad = [k for k in GREEN_BOTH if k in RES and not RES[k]]
    print("CONTROL: %d of %d went red as they must%s%s" % (len(must) - len(stayed), len(must),
          (" -- STAYED GREEN: " + ", ".join(stayed)) if stayed else "", (" -- BROKE: " + ", ".join(bad)) if bad else ""))
    sys.exit(0 if not stayed and not bad else 1)
print("WALK: %d green, %d red%s" % (len(RES) - len(red), len(red), (" -- " + ", ".join(red)) if red else ""))
sys.exit(0 if not red else 1)
