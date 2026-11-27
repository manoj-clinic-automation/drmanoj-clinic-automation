#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s973_app.py -- S973_VOUCHER_SCANS on the REAL scan app: the app folder copied into a scratch folder with the given asset_register.py
and claude_reader.py (TO -- or the live files for the control), on a fresh database the app makes itself. Made-up rows only (dated 2031); the
reader's answer is made up in the process (nothing leaves it). The scratch is removed.

    python3 -B walk_s973_app.py --live <the app folder> --shared <the shared folder> --files <folder holding the files to test> [--expect-red]
"""
import io, json, os, re, shutil, sqlite3, subprocess, sys, tempfile

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


LIVE, FILES = opt("--live", "/root/assetapp"), opt("--files")
EXPECT_RED = "--expect-red" in ARGS
KIT_FILES = ("asset_register.py", "claude_reader.py")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
GREEN_BOTH = ("A0", "R3", "I2", "I3", "I4", "Z1", "L3", "I6", "H5", "T3")   # the app loads; a bill, a statement, a credit note, an ordinary edit, a dealer's link,
#                                                                      a clinic-lane paper and a person's way back: as before (nothing marks them)

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s973app_")
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
            if "NOT mounted" in l or "S973" in l or "NOT installed" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S973_WALK_DEBUG"):
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
db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s973','Walk owner','owner','x',1)")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-01-01')")
db.execute("CREATE TABLE IF NOT EXISTS claude_reading(bill_id INTEGER PRIMARY KEY, at TEXT, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT)")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_own_s973'").fetchone()[0]
    ss["epoch"] = epoch
N = [0]
D = "Walk Dealer973"


def mk(no, amt=None, lane="pharmacy", kind="Pharmacy", status="captured", dk=None, sub=None, vendor=None):
    N[0] += 1
    f = os.path.join(os.environ["ASSETS_UPLOADS"], "walk973_%d.pdf" % N[0])
    open(f, "wb").write(b"%PDF-1.4 made-up walk paper\n")
    cur = db.execute("INSERT INTO bills(kind, vendor, bill_no, bill_date, total_amount, status, lane, subgroup, doc_kind, created_at, stamp_no, source_stored) "
                     "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (kind, vendor, no, None, amt, status, lane, sub, dk, "2031-03-12 06:00:00",
                                                         "B-%04d" % (9730 + N[0]), "walk973_%d.pdf" % N[0]))
    db.commit()
    return cur.lastrowid, f


def row(i):
    return db.execute("SELECT * FROM bills WHERE id=?", (i,)).fetchone()


def items(i):
    return [tuple(r) for r in db.execute("SELECT item_name, quantity, batch FROM bill_items WHERE bill_id=? ORDER BY id", (i,))]


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
SV = {"doc_kind": "stock_voucher", "is_summary": False, "voucher_type": "ISSUE", "vendor": "SANJEEVNI MEDICOS", "bill_no": "L 000045",
      "bill_date": "2031-03-12", "total_amount": 840,
      "items": [{"name": "KNEE IMMOBILIZER L UNISON", "qty": 1, "batch": "K1"}, {"name": "WALKTAB 10", "qty": "2:5", "batch": "W9"}]}
CNA = {"doc_kind": "credit_note", "is_summary": False, "vendor": D, "bill_no": "CN-973", "bill_date": "2031-03-12", "total_amount": 500,
       "against_no": "WD-803", "items": [{"name": "WALKITEM", "qty": 1, "rate": 500, "amount": 500}]}
BILL = {"doc_kind": "tax_invoice", "is_summary": False, "vendor": D, "bill_no": "WD-900", "bill_date": "2031-03-10", "total_amount": 1410,
        "items": [{"name": "WALKITEM", "qty": 2, "rate": 705, "amount": 1410}]}
STMT = {"is_summary": True, "dealer": D, "period_from": "2031-02-01", "period_to": "2031-02-28", "as_on": None, "continued": False,
        "lines": [{"kind": "bill", "no": "WD-1", "date": "2031-02-03", "amount": 100}], "total_bills": 100, "closing": 100, "opening": None, "handwritten": False}
SANJ = "SELECT id FROM bills WHERE kind='Pharmacy' AND status='captured'"    # scan_register.py's / purchase_app._s452_scan_rows' own selection


def intake(answer, **kw):
    i, f = mk(kw.pop("no", None), **kw)
    ANSWER[0] = answer
    ar._bg_extract(i, f)
    return i


def link_post(no, answer, vendor=None):
    """reception's / Amir's scan link: POST /intake/submit with lane=pharmacy and the number (no reading thread: the walk reads it next)."""
    before = ar._reader_on
    ar._reader_on = lambda: False
    try:
        data = {"lane": "pharmacy", "bill_no": no, "bill": (io.BytesIO(b"%PDF-1.4 made-up link scan " + no.encode()), "v.pdf")}
        if vendor:
            data["vendor"] = vendor
        r = own.post("/intake/submit", data=data, content_type="multipart/form-data")
    finally:
        ar._reader_on = before
    i = db.execute("SELECT MAX(id) FROM bills").fetchone()[0]
    marked = row(i)["kind"]
    ANSWER[0] = answer
    ar._bg_extract(i, os.path.join(os.environ["ASSETS_UPLOADS"], row(i)["source_stored"]))
    return r.status_code, i, marked


# ---- R: the reader
ph, ph0, pr = getattr(cr, "PHARMACY_PROMPT", ""), getattr(cr, "_S783_PROMPT_BEFORE", ""), getattr(cr, "PROMPT", "")
c1 = cr.clean_pharmacy(dict(SV)) or {}
c2 = cr.clean_pharmacy(dict(BILL)) or {}
c3 = cr.clean_pharmacy(dict(CNA)) or {}
ck("R1 the pharmacy reader (and its long-bill fallback) asks for a stock voucher with its own rule; the desk's reader is unchanged; S841's credit note stays",
   lambda: '| "stock_voucher" |' in ph and "A STOCK VOUCHER is the pharmacy's OWN" in ph and '| "stock_voucher" |' in ph0 and "A STOCK VOUCHER" in ph0
   and ph.count('"doc_kind": "tax_invoice"') == 1 and "STOCK VOUCHER" not in pr and "BACK to the pharmacy" in ph and '| "credit_note" |' in ph)
ck("R2 a stock-voucher answer is kept as one: its type, no seller, no amount, its lines with batch",
   lambda: c1.get("doc_kind") == "stock_voucher" and c1.get("voucher_type") == "ISSUE" and c1.get("vendor") is None and c1.get("total_amount") is None
   and [x["name"] for x in c1.get("items", [])] == ["KNEE IMMOBILIZER L UNISON", "WALKTAB 10"] and c1["items"][1]["batch"] == "W9", lambda: c1)
ck("R3 a bill's answer stays a bill and a credit note a credit note (no voucher_type)",
   lambda: c2.get("doc_kind") == "tax_invoice" and "voucher_type" not in c2 and c3.get("doc_kind") == "credit_note" and "voucher_type" not in c3,
   lambda: (c2, c3))

# ---- I: the reading road (scanned on the lane without the link)
i1 = intake(SV)
r1 = row(i1)
au = db.execute("SELECT who, detail FROM bill_audit WHERE bill_id=? AND action='kind'", (i1,)).fetchall()
ck("I1 a stock voucher scanned on the pharmacy lane: kind 'Stock voucher', its number in Marg's form, no seller, no amount, its lines -- "
   "and Sanjeevni's bill selection never sees it",
   lambda: r1["kind"] == "Stock voucher" and r1["doc_kind"] == "stock_voucher" and r1["bill_no"] == "L000045" and not r1["vendor"]
   and r1["total_amount"] is None and r1["lane"] == "pharmacy" and r1["status"] == "captured" and len(items(i1)) == 2
   and any("S973" in (w or "") for w, _ in au) and i1 not in [x[0] for x in db.execute(SANJ)],
   lambda: (dict(r1), items(i1), [tuple(x) for x in au]))
ck("I5 the words the pharmacy reader was sent ask for a stock voucher", lambda: any("CAME IN ON THE PHARMACY LANE" in x and "STOCK VOUCHER" in x for x in SENT),
   lambda: [x[:60] for x in SENT])
i2 = intake(BILL)
r2 = row(i2)
ck("I2 a pharmacy bill stays kind 'Pharmacy' (Sanjeevni pairs it as before)",
   lambda: r2["kind"] == "Pharmacy" and (r2["doc_kind"] or "") == "" and r2["bill_no"] == "WD-900" and i2 in [x[0] for x in db.execute(SANJ)], lambda: dict(r2))
i3 = intake(STMT)
ck("I3 a dealer's statement is still recognised as a Summary (S754)", lambda: row(i3)["kind"] == "Summary", lambda: dict(row(i3)))
i4 = intake(CNA)
ck("I4 a credit note is still kind 'Pharmacy credit note' (S841)", lambda: row(i4)["kind"] == "Pharmacy credit note", lambda: dict(row(i4)))
i6 = intake(dict(SV, bill_no="AD00046", voucher_type="RECEIVE"), lane="clinic", kind="Consumable", status="draft", vendor="Walk Clinic973")
ck("I6 a voucher read on the CLINIC lane is left to the desk (no S973 mark)",
   lambda: row(i6)["kind"] == "Consumable" and not db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND who LIKE '%S973%'", (i6,)).fetchone(),
   lambda: dict(row(i6)))

# ---- L: the link road
sc, l1, mk1 = link_post("L000047", dict(SV, bill_no="L000047"))
ck("L1 the scan link (pharmacy lane, the voucher's number, no seller): marked 'Stock voucher' at once, before any reading; then read and filled",
   lambda: sc in (302, 200) and mk1 == "Stock voucher" and row(l1)["kind"] == "Stock voucher" and row(l1)["bill_no"] == "L000047" and len(items(l1)) == 2
   and db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND who='server (S973 link)'", (l1,)).fetchone() is not None and not row(l1)["vendor"],
   lambda: (sc, mk1, dict(row(l1)), items(l1)))
sc, l1b, mk1b = link_post("L000047", dict(BILL, bill_no="WD-904"))       # the same page's NEXT Save: the scanner still carries the number
ck("L1b only the FIRST paper of a link carries its number: a dealer's bill saved next on that page is not marked, keeps its own number",
   lambda: mk1b == "Pharmacy" and row(l1b)["kind"] == "Pharmacy" and row(l1b)["bill_no"] == "WD-904" and row(l1b)["vendor"] == D
   and db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND who='server (S973 link once)'", (l1b,)).fetchone() is not None, lambda: (mk1b, dict(row(l1b))))
sc, l2, mk2 = link_post("L000048", dict(BILL, bill_no="WD-901"))
ck("L2 a paper scanned through the link that the reader says is a BILL goes back to 'Pharmacy' and is read on the lane's own road",
   lambda: mk2 == "Stock voucher" and row(l2)["kind"] == "Pharmacy" and row(l2)["vendor"] == D and l2 in [x[0] for x in db.execute(SANJ)],
   lambda: (mk2, dict(row(l2))))
sc, l3, mk3 = link_post("L000049", dict(BILL, bill_no="WD-902"), vendor=D)
ck("L3 a dealer's link (it carries the vendor) is never marked", lambda: mk3 == "Pharmacy" and row(l3)["kind"] == "Pharmacy", lambda: (mk3, dict(row(l3))))

# ---- T: the thread reads before the link's mark (review M3); a reading with no voucher number (review S1)
t1, tf1 = mk("L000056")
ANSWER[0] = dict(SV, bill_no="L000056")
ar._bg_extract(t1, tf1)
ck("T1 the link's paper read BEFORE the request marked it: the reading thread marks it itself and reads it as a voucher",
   lambda: row(t1)["kind"] == "Stock voucher" and row(t1)["bill_no"] == "L000056" and not row(t1)["vendor"] and len(items(t1)) == 2, lambda: (dict(row(t1)), items(t1)))
t2, tf2 = mk("L000057")
ANSWER[0] = dict(BILL, bill_no="WD-903")
ar._bg_extract(t2, tf2)
ck("T2 ... and if that paper is a dealer's bill, it goes back to 'Pharmacy' with ITS OWN number, seller and amount",
   lambda: row(t2)["kind"] == "Pharmacy" and row(t2)["bill_no"] == "WD-903" and row(t2)["vendor"] == D and float(row(t2)["total_amount"] or 0) == 1410
   and t2 in [x[0] for x in db.execute(SANJ)], lambda: dict(row(t2)))
t3 = intake(dict(SV, bill_no="WD-77", vendor=D, total_amount=990))
ck("T3 a reading that says 'stock voucher' but carries no Marg voucher number is never marked and keeps its seller and amount",
   lambda: row(t3)["kind"] == "Pharmacy" and row(t3)["vendor"] == D and float(row(t3)["total_amount"] or 0) == 990, lambda: dict(row(t3)))

r_ = own.get("/intake?lane=pharmacy&bill_no=L000099&from=/finance/amir")
pg_ = r_.get_data(as_text=True)
ck("L4 the intake page drops a link's voucher number after the FIRST Save (a seller-less link: S973; S618's rescan_of as before)",
   lambda: r_.status_code == 200 and pg_.count("if(!window.SCANNER_CONFIG.uploadFields.vendor){delete window.SCANNER_CONFIG.uploadFields.bill_no;}") == 2
   and pg_.count("delete window.SCANNER_CONFIG.uploadFields.rescan_of") == 2, lambda: (r_.status_code, pg_.count("uploadFields.bill_no")))

# ---- H: the heal
h1, _ = mk("L000050", dk="stock_voucher")
own.post("/desk/api/save", json={})
ck("H1 a stock voucher back on the pharmacy lane as 'Pharmacy' is healed after a POST", lambda: row(h1)["kind"] == "Stock voucher", lambda: dict(row(h1)))
h2, _ = mk("L000051")
db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,1,?,?)",
           (h2, "2031-03-12 07:00", "walk", "stock_voucher", json.dumps(dict(SV, bill_no="L000051"))))
db.commit()
n = ar._s973_heal() if hasattr(ar, "_s973_heal") else 0
ck("H2 a paper whose reading says stock voucher but whose row was never marked is healed (what the start does)",
   lambda: row(h2)["kind"] == "Stock voucher" and row(h2)["doc_kind"] == "stock_voucher", lambda: (n, dict(row(h2))))
h5 = intake(dict(SV, bill_no="L000052"))
db.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)", (h5, "2031-03-12 08:00", "walk", "relane", "{}"))
db.execute("UPDATE bills SET kind='Pharmacy' WHERE id=?", (h5,))
db.commit()
own.post("/desk/api/save", json={})
ck("H5 the way back: a paper this kit marked that a person moves off the lane and back stays 'Pharmacy'", lambda: row(h5)["kind"] == "Pharmacy",
   lambda: dict(row(h5)))

# ---- G: the history rule
for k_ in range(3):
    mk("WC-%d" % k_, 100, lane="clinic", kind="Consumable", status="approved", sub="procedure", vendor="Walk Clinic973b")
gi, _ = mk("L000053", None, kind="Stock voucher", dk="stock_voucher", vendor="Walk Clinic973b")
g = cp.auto_home(db, gi) if hasattr(cp, "auto_home") else None
db.commit()
ck("G1 the history rule never moves a stock voucher", lambda: g == [] and row(gi)["lane"] == "pharmacy" and row(gi)["kind"] == "Stock voucher",
   lambda: (g, dict(row(gi))))

# ---- E: the edit page keeps the kind
r = own.get("/bills/%d/edit" % i1)
page = r.get_data(as_text=True)
ck("E2 the edit page shows the kind kept, no kind choice", lambda: r.status_code == 200 and "<b>Stock voucher</b>" in page,
   lambda: (r.status_code, re.findall(r"Kind</label>.{0,200}", page)[:1]))
r = own.post("/bills/%d/edit" % i1, data={"vendor": "", "bill_no": "L000045", "bill_date": "12-03-2031", "total_amount": ""})
ck("E1 an edit of a stock voucher keeps kind 'Stock voucher'", lambda: r.status_code in (200, 302) and row(i1)["kind"] == "Stock voucher",
   lambda: (r.status_code, dict(row(i1))))
z, _ = mk("Z-1", 50, lane="clinic", kind="Consumable", status="draft", vendor="Walk Other973")
r = own.post("/bills/%d/edit" % z, data={"kind": "Asset", "vendor": "Walk Other973", "bill_no": "Z-1", "bill_date": "12-03-2031", "total_amount": "50"})
ck("Z1 an ordinary clinic draft's edit still takes the form's kind", lambda: r.status_code in (200, 302) and row(z)["kind"] == "Asset", lambda: dict(row(z)))

# ---- S: the switch
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.stock_voucher','off')")
db.commit()
s1 = intake(dict(SV, bill_no="L000054"))
sc, s2, mk_s2 = link_post("L000055", dict(SV, bill_no="L000055"))
db.execute("DELETE FROM settings WHERE key='read.stock_voucher'")
db.commit()
ck("S1 with read.stock_voucher off nothing is marked, by the reading or the link (the reading is still kept)",
   lambda: row(s1)["kind"] == "Pharmacy" and mk_s2 == "Pharmacy" and row(s2)["kind"] == "Pharmacy"
   and db.execute("SELECT doc_kind FROM claude_reading WHERE bill_id=?", (s1,)).fetchone()[0] == "stock_voucher", lambda: (dict(row(s1)), mk_s2))

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
