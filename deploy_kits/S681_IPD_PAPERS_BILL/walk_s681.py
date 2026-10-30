#!/usr/bin/env python3
"""walk_s681.py (kit S681; carried from walk_s680.py) -- the walk for surgery_cases.py (kit S579 -> S581 -> S680 IPD cases, the record; S680 FINAL, S370, D804; S681 kits 2+3: section K). S581's and S680 v3's checks carried
(those S680 changes by design are rewritten and say so) plus section V for S680. Runs the REAL module in a small Flask app against a database:
either a made-up one (default), or a COPY of the live finance.db (--db /root/finance/finance.db: copied to a temp folder first;
the live file is never opened for writing). Every row the walk writes is made up and dated 2099; papers go to a temp folder.
    python3 walk_s579.py [path/to/surgery_cases.py] [--db /path/to/finance.db]
S370 (D804): the checks D804 changes are marked [D804] and rewritten; section Y is new. A made-up console patients mirror and a made-up
Case Pack ledger stand in for /root/wa/console.db and case_ledger.csv (the live ones are never read by the walk).
Prints one line per check and a count. Exit 0 only if every check is green."""
import csv, importlib.util, io, json, os, re, shutil, sqlite3, sys, tempfile
from urllib.parse import quote

args = [a for a in sys.argv[1:]]
DBSRC = None
if "--db" in args:
    i = args.index("--db"); DBSRC = args[i + 1]; del args[i:i + 2]
MOD = os.path.abspath(args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), "surgery_cases.py"))
R = []


def check(name, cond):
    R.append((name, bool(cond))); print(("GREEN " if cond else "RED   ") + name)


def finish():
    g = sum(1 for _, ok in R if ok)
    print("\nwalk_s681: %d of %d green" % (g, max(len(R), 1)))
    sys.exit(0 if R and g == len(R) else 1)


TMP = tempfile.mkdtemp(prefix="walk680_")
os.environ["SURGERY_PAPER_DIR"] = os.path.join(TMP, "papers")
os.environ["SURGERY_NOW"] = "2099-01-15T10:00:00"
DB = os.path.join(TMP, "finance.db")
os.environ["SURGERY_CONSOLE_DB"] = os.path.join(TMP, "console.db")          # D804: made-up stand-ins, never the live ones
os.environ["SURGERY_CASE_LEDGER"] = os.path.join(TMP, "case_ledger.csv")
# S370: the IVR call -- a stand-in for call_api.py on a free local port (MyOperator is never reached), a made-up key and call list
import http.server, threading
CALLS = []
CALLMODE = {"m": "ok"}


class _FakeCall(http.server.BaseHTTPRequestHandler):
    def do_POST(self):                         # noqa: N802
        n = int(self.headers.get("Content-Length") or 0)
        CALLS.append((self.headers.get("X-Call-Key"), json.loads(self.rfile.read(n) or b"{}")))
        code, body = {"ok": (200, {"ok": True, "accepted": True}), "refuse": (502, {"ok": False, "reason": "number 98765" "43210 blocked"})}[CALLMODE["m"]]
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *a):
        pass


_srv = http.server.HTTPServer(("127.0.0.1", 0), _FakeCall)
threading.Thread(target=_srv.serve_forever, daemon=True).start()
os.environ["SURGERY_CALL_URL"] = "http://127.0.0.1:%d/call" % _srv.server_address[1]
os.environ["SURGERY_WA_ENV"] = os.path.join(TMP, "wa.env")
os.environ["SURGERY_RING_AGENTS"] = os.path.join(TMP, "ring_agents.json")
open(os.environ["SURGERY_WA_ENV"], "w").write("# walk\nCALL_API_SECRET=walkcallkey\n")
json.dump({"agents": {"90000" "00001": {"user": "shavez", "name": "WALK SHAVEZ"}}}, open(os.environ["SURGERY_RING_AGENTS"], "w"))
_cc = sqlite3.connect(os.environ["SURGERY_CONSOLE_DB"])
_cc.executescript("CREATE TABLE patients (phone10 TEXT, name TEXT, diagnosis TEXT, age TEXT, gender TEXT, last_visit TEXT, patient_uid TEXT, clinic_id TEXT);"
                  "INSERT INTO patients VALUES ('90000" "11111','WALKTEST RAMESH','','','','2099-01-01','WALKUID1','WALK9901');"
                  "INSERT INTO patients VALUES ('98888" "77777','WALKTEST CONSOLE ONLY','','','','2099-01-02','WALKUID2','WALKCONSOLE');")
_cc.commit(); _cc.close()
with open(os.environ["SURGERY_CASE_LEDGER"], "w", newline="", encoding="utf-8") as _fh:
    _w = csv.writer(_fh)
    _w.writerow(["Case_ID", "Patient_UID", "Clinic_Specific_Id", "Patient_Name", "Case_Date", "Consent_Procedure", "OT_Tier", "OT_Procedure",
                 "Estimate_Title", "Estimate_Total", "Bundle_File", "Consent_File", "Generated_By", "Written_At"])
    _w.writerow(["C-2099-000001", "WALKUID1", "WALK9901", "WALKTEST RAMESH", "2099-01-05", "", "", "WALK PFN", "", "", "", "", "walk", "2099-01-05"])
    _w.writerow(["C-2099-000002", "WALKUID1", "WALK9901", "WALKTEST RAMESH", "2099-01-09", "", "", "WALK PFN 2", "", "", "", "", "walk", "2099-01-09"])
    _w.writerow(["C-2099-000009", "WALKUID9", "WALK9999", "WALKTEST SOMEONE", "2099-01-09", "", "", "WALK OTHER", "", "", "", "", "walk", "2099-01-09"])
if DBSRC:
    src = sqlite3.connect("file:%s?mode=ro" % DBSRC, uri=True); dst = sqlite3.connect(DB); src.backup(dst); src.close(); dst.close()
else:
    c = sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE business_unit (code TEXT PRIMARY KEY, name TEXT, merchant_id TEXT, open_sunday INTEGER, active INTEGER, entity_code TEXT);
    CREATE TABLE unit_role (id INTEGER PRIMARY KEY, unit TEXT NOT NULL REFERENCES business_unit(code), username TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('maker','checker','viewer')), active INTEGER NOT NULL DEFAULT 1, note TEXT, UNIQUE (unit, username, role));
    CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT NOT NULL, note TEXT);
    CREATE TABLE audit_log (id INTEGER PRIMARY KEY, table_name TEXT NOT NULL, row_id INTEGER, action TEXT NOT NULL, before_json TEXT,
        after_json TEXT, by_whom TEXT, at TEXT NOT NULL);
    CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT NOT NULL UNIQUE, name TEXT, phone_last4 TEXT, first_seen TEXT,
        merged_into INTEGER, note TEXT);
    CREATE TABLE bank_statement_line (id INTEGER PRIMARY KEY, account_ref TEXT, txn_date TEXT, value_date TEXT, description TEXT, reference TEXT,
        withdrawal_p INTEGER, deposit_p INTEGER, balance_p INTEGER, is_cash_deposit INTEGER, source_file TEXT, sha256 TEXT, ingested_at TEXT);
    """)
    c.commit(); c.close()
c = sqlite3.connect(DB)
c.execute("INSERT OR IGNORE INTO patient_ref (clinic_id, name, phone_last4) VALUES ('WALK9901','WALKTEST RAMESH','0000')")
try:
    c.execute("INSERT INTO bank_statement_line (account_ref, txn_date, description, deposit_p, withdrawal_p, reference) "
              "VALUES ('WALKACC0001','2099-01-14','WALK NEFT HOSPITAL',10000000,0,'WALKREF')")
except Exception as e:                       # noqa: BLE001
    print("note: no bank_statement_line here (%s)" % e)
c.commit(); c.close()

try:
    from flask import Flask, jsonify
    spec = importlib.util.spec_from_file_location("surgery_cases_walk680", MOD)
    sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
except Exception as e:                       # noqa: BLE001
    check("the module loads (%s)" % type(e).__name__, False); finish()

app = Flask(__name__)
app.config["TESTING"] = True
WHO = {"u": ""}


def db():
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def require(*roles, unit="medical"):
    """As finance_app.require: roles per unit from unit_role."""
    con = db()
    have = {r["role"] for r in con.execute("SELECT role FROM unit_role WHERE unit=? AND lower(username)=lower(?) AND active=1", (unit, WHO["u"]))}
    if not have.intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return {"user": WHO["u"], "role": "", "roles": sorted(have)}, None


def audit(con, table, row_id, action, before=None, after=None, who=""):
    con.execute("INSERT INTO audit_log (table_name,row_id,action,before_json,after_json,by_whom,at) VALUES (?,?,?,?,?,?,?)",
                (table, row_id, action, json.dumps(before), json.dumps(after), who, "2099-01-15"))


sc.init(app, db, require, audit, unit="surgery")
cl = app.test_client()


def as_(u):
    WHO["u"] = u


def get(path):
    return cl.get(path)


def post(path, data):
    return cl.post(path, data=data)


def q1(sql, a=()):
    con = db(); r = con.execute(sql, a).fetchone(); con.close(); return r


PDF = b"%PDF-1.4\n% walk test page\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
PDF2 = b"%PDF-1.4\n% walk test page two\n%%EOF\n"

# ---- A the gate
as_("manoj")
r = get("/finance/surgery")
check("A [D804] the doctor's very first visit opens the list, with the hospital money as a status and a filter", r.status_code == 200
      and b"Hospital money" in r.data and b"name=money" in r.data)
as_("nobody")
r = get("/finance/surgery")
check("A a login not on the unit is refused (403)", r.status_code == 403)
check("A the unit and its two logins were made on the first request",
      q1("SELECT COUNT(*) FROM unit_role WHERE unit='surgery' AND active=1")[0] == 2 and q1("SELECT code FROM business_unit WHERE code='surgery'"))
as_("shavez")
r = get("/finance/surgery")
check("A [S680][D804] Shavez sees the list WITH the hospital money (D801: only the implant's actual cost is hidden)",
      r.status_code == 200 and b"Hospital money" in r.data and b"name=money" in r.data)

# ---- B/C new cases (Shavez)
r = post("/finance/surgery/new", dict(patient="WALKTEST RAMESH", clinic_id="WALK9901", payer="ayushman", hospital="WALK HOSPITAL",
                                       procedure_text="PFN right", surgery_date="2099-01-10", source="Clinic"))
c1 = q1("SELECT * FROM surg_case WHERE patient='WALKTEST RAMESH'")
check("B Shavez makes an Ayushman case: S-2099-0001, stage 'pre-approval applied'", r.status_code == 302 and c1 and c1["case_no"] == "S-2099-0001"
      and c1["stage"] == "applied")
r = post("/finance/surgery/new", dict(patient="WALKTEST SITA", payer="cash", hospital="WALK HOSPITAL", surgery_date="2099-01-11", source="DTH"))
c2 = q1("SELECT * FROM surg_case WHERE patient='WALKTEST SITA'")
check("C a cash case: S-2099-0002, stage planned", c2 and c2["case_no"] == "S-2099-0002" and c2["stage"] == "planned")
r = post("/finance/surgery/new", dict(patient="WALKTEST X", payer="bogus", source="Clinic"))
check("C a payer that is not one of the five is refused", r.status_code == 302 and "err=payer" in r.headers["Location"])
r = post("/finance/surgery/new", dict(patient="", payer="cash"))
check("C a case without a name is refused", "err=patient" in r.headers["Location"])
# numbering under a race: a row already holding the next number
con = db(); con.execute("INSERT INTO surg_case (case_no, patient, payer) VALUES ('S-2099-0003','WALKTEST RACE','cash')"); con.commit(); con.close()
post("/finance/surgery/new", dict(patient="WALKTEST AFTER", payer="cashless", insurer="WALK TPA", source="Imran"))
check("C the next case number steps past one already taken (S-2099-0004)", q1("SELECT case_no FROM surg_case WHERE patient='WALKTEST AFTER'")[0] == "S-2099-0004")

# ---- D/E the Case Pack link and the search
r = get("/finance/surgery/new?cid=WALK9901&name=WALKTEST%20RAMESH&payer=ayush&cp=C-2099-000001")
check("D the Case Pack's link prefills the name, ID and Ayushman, and names the Case Pack case",
      b"WALKTEST RAMESH" in r.data and b"value='WALK9901'" in r.data and b"value='ayushman' checked" in r.data and b"C-2099-000001" in r.data)
r = get("/finance/surgery/new?q=WALK9901")
check("E the patient search finds the register's own and the patient master's", b"WALKTEST RAMESH" in r.data)

# ---- F papers
cid1, cid2 = c1["id"], c2["id"]
r = get("/finance/surgery/case/%d/scan/preapproval" % cid1)
check("F the scan page hosts the shared scanner with this case and kind", r.status_code == 200 and b"/finance/scan/widget.js" in r.data
      and b'"kind": "preapproval"' in r.data and b"/finance/surgery/api/case/%d/paper/preapproval" % cid1 in r.data)
r = cl.post("/finance/surgery/api/case/%d/paper/preapproval" % cid1, data={"file": (io.BytesIO(PDF), "a.pdf")}, content_type="multipart/form-data")
p1 = q1("SELECT * FROM surg_paper WHERE case_id=? AND kind='preapproval'", (cid1,))
check("F a PDF is filed against the case, the file kept under the papers folder", r.status_code == 200 and p1 and os.path.isfile(p1["path"])
      and p1["path"].startswith(os.environ["SURGERY_PAPER_DIR"]))
r = cl.post("/finance/surgery/api/case/%d/paper/xray" % cid1, data={"file": (io.BytesIO(b"\xff\xd8\xff\xe0 walk jpeg"), "x.jpg")}, content_type="multipart/form-data")
check("F a photo (X-ray) is filed too", r.status_code == 200 and q1("SELECT mime FROM surg_paper WHERE case_id=? AND kind='xray'", (cid1,))[0] == "image/jpeg")
r = cl.post("/finance/surgery/api/case/%d/paper/police" % cid1, data={"file": (io.BytesIO(b"just text"), "t.txt")}, content_type="multipart/form-data")
check("F a file that is neither PDF nor photo is refused (415)", r.status_code == 415)
r = cl.post("/finance/surgery/api/case/%d/paper/preapproval" % cid1, data={"file": (io.BytesIO(PDF), "a.pdf")}, content_type="multipart/form-data")
check("F the same file twice is not filed twice", r.get_json().get("duplicate") is True and q1("SELECT COUNT(*) FROM surg_paper WHERE case_id=?", (cid1,))[0] == 2)
r = cl.post("/finance/surgery/api/case/%d/paper/notakind" % cid1, data={"file": (io.BytesIO(PDF2), "a.pdf")}, content_type="multipart/form-data")
check("F an unknown kind of paper is refused", r.status_code == 400)
r = get("/finance/surgery/paper/%d" % p1["id"])
check("F the filed paper opens", r.status_code == 200 and r.data.startswith(b"%PDF"))
r = get("/finance/surgery/case/%d" % cid1)
check("F [S681] the case page offers fourteen kinds of paper -- MLC, police memo and the new police FIR copy, previous hospital, LAMA, DOPR -- and what is still missing",
      b"Medicolegal (MLC) papers" in r.data and b"Police memo" in r.data and b"Police FIR copy" in r.data and b"LAMA" in r.data and b"DOPR" in r.data
      and b"Previous hospital" in r.data and b"missing" in r.data and r.data.count(b"Scan / upload") == 14)

# ---- G implants
r = post("/finance/surgery/case/%d/implant" % cid2, dict(vendor_new="WALK ORTHO VENDOR", item="WALK PLATE", qty="1", bill="30000",
                                                           bill_to="doctor", charge="36000", payable="1"))
i2 = q1("SELECT * FROM surg_implant WHERE case_id=?", (cid2,))
check("G [S680] Shavez adds an implant with a new vendor; 'charged to the patient' is taken from him, the actual cost is NOT",
      i2 and i2["bill_p"] == 3000000 and i2["charge_p"] == 3600000 and i2["payable_p"] is None)
vid = i2["vendor_id"]
as_("manoj")
con = db(); con.execute("UPDATE surg_implant SET voided_at='x' WHERE id=?", (i2["id"],)); con.commit(); con.close()
post("/finance/surgery/case/%d/implant" % cid2, dict(vendor_id=str(vid), item="WALK PLATE", qty="1", bill="30000", bill_to="doctor", charge="36000"))
post("/finance/surgery/case/%d/implant" % cid1, dict(vendor_id=str(vid), item="WALK PFN", qty="1", bill="50000", bill_to="patient", payable="40000"))
i1 = q1("SELECT * FROM surg_implant WHERE case_id=? AND voided_at=''", (cid1,))
check("G Dr Manoj adds a credit implant with 'actually due to the vendor' less than the bill", i1 and i1["bill_p"] == 5000000 and i1["payable_p"] == 4000000)
r = post("/finance/surgery/case/%d/implant" % cid1, dict(vendor_id=str(vid), item="X", bill="abc"))
check("G a bill amount that is not a number is refused", "err=amount" in r.headers["Location"])

# ---- H/I/J the vendor ledger
rows, bal, waiting, unas = sc.vendor_ledger(db(), vid)
check("H cash case: Dr Manoj owes the vendor the bill (₹30,000); the credit case waits for its cheque", bal == 3000000 and len(waiting) == 1)
post("/finance/surgery/vendor/%d/pay" % vid, dict(day="2099-01-12", amount="10000", mode="cash"))
post("/finance/surgery/vendor/%d/cheque" % vid, dict(day="2099-01-13", amount="50000", cheque_no="WALK001", from_whom="WALK HOSPITAL"))
qid = q1("SELECT id FROM surg_cheque WHERE vendor_id=?", (vid,))[0]
rows, bal, waiting, unas = sc.vendor_ledger(db(), vid)
check("H a cash payment counts; an unassigned cheque is listed, not yet counted", bal == 2000000 and len(unas) == 1)
r = post("/finance/surgery/cheque/%d" % qid, {"c%d" % cid1: "60000"})
check("J a cheque cannot be assigned beyond its amount", "err=over" in r.headers["Location"])
r = post("/finance/surgery/cheque/%d" % qid, {"c%d" % cid1: "50000", "c%d" % cid2: "100"})
rows, bal, waiting, unas = sc.vendor_ledger(db(), vid)
check("I a cheque goes only to that vendor's CREDIT patients (the cash case is ignored)",
      q1("SELECT COUNT(*) FROM surg_cheque_alloc WHERE cheque_id=?", (qid,))[0] == 1)
check("H the cheque ₹50,000 counts for Dr Manoj, the ₹40,000 actually due against him: the gap of ₹10,000 is in his favour (balance ₹10,000)",
      bal == 1000000 and not waiting and not unas)
r = get("/finance/surgery/vendor/%d" % vid)
check("H the vendor's page states the balance and offers print to share", b"Dr Manoj owes WALK ORTHO VENDOR" in r.data and b"10,000" in r.data
      and b"window.print()" in r.data)

# ---- K receipts
post("/finance/surgery/case/%d/edit" % cid1, dict(stage="discharged", patient="WALKTEST RAMESH", payer="ayushman", hospital="WALK HOSPITAL",
                                                   due="70000", surgery_date="2099-01-10"))
post("/finance/surgery/case/%d/edit" % cid2, dict(stage="discharged", patient="WALKTEST SITA", payer="cash", hospital="WALK HOSPITAL", due="30000"))
check("K Dr Manoj writes the amount due from the hospital", q1("SELECT due_p FROM surg_case WHERE id=?", (cid1,))[0] == 7000000)
post("/finance/surgery/receipts", dict(day="2099-01-14", amount="100000", from_whom="WALK HOSPITAL", period="December 2098"))
rid = q1("SELECT id FROM surg_receipt WHERE period='December 2098' AND voided_at=''")[0]   # S581: never the first row -- the live copy holds others
r = get("/finance/surgery/receipt/%d" % rid)
check("K the payment page lists this hospital's open cases with what is still due", b"WALKTEST RAMESH" in r.data and b"WALKTEST SITA" in r.data
      and b"70,000" in r.data)
r = post("/finance/surgery/receipt/%d" % rid, {"a%d" % cid1: "70000", "a%d" % cid2: "40000"})
check("K amounts beyond the payment are refused", "err=over" in r.headers["Location"])
post("/finance/surgery/receipt/%d" % rid, {"a%d" % cid1: "60000", "a%d" % cid2: "30000"})
check("K the amounts against each patient are saved; the case shows received and balance",
      sc.received(db(), cid1) == 6000000 and b"balance \xe2\x82\xb9 10,000" in get("/finance/surgery/case/%d" % cid1).data)
r = get("/finance/surgery/receipt/%d" % rid)
check("K a fully paid case stays on the form while it is against this payment (the form is the whole truth)", b"WALKTEST SITA" in r.data)
r = cl.post("/finance/surgery/api/receipt/%d/statement" % rid, data={"file": (io.BytesIO(PDF2), "s.pdf")}, content_type="multipart/form-data")
check("K the hospital's statement is scanned against the payment", r.status_code == 200 and q1("SELECT COUNT(*) FROM surg_paper WHERE receipt_id=?", (rid,))[0] == 1)
sp = q1("SELECT id FROM surg_paper WHERE receipt_id=?", (rid,))[0]

# ---- L the bank line
r = get("/finance/surgery/receipt/%d" % rid)
has_bank = q1("SELECT name FROM sqlite_master WHERE name='bank_statement_line'") is not None
bl = q1("SELECT id FROM bank_statement_line WHERE reference='WALKREF'") if has_bank else None
check("L a bank credit of exactly the amount near the date is offered", (not bl) or (b"WALK NEFT HOSPITAL" in r.data and b"\xe2\x80\xa60001" in r.data))
if bl:
    r = post("/finance/surgery/receipt/%d/bank" % rid, dict(line="bank_statement_line:%d" % (bl[0] + 999)))
    check("L a line that was not offered is refused", "err=line" in r.headers["Location"])
    post("/finance/surgery/receipt/%d/bank" % rid, dict(line="bank_statement_line:%d" % bl[0]))
    check("L tied to the bank line", q1("SELECT bank_line_id FROM surg_receipt WHERE id=?", (rid,))[0] == bl[0])

# ---- M what Shavez may not do
as_("shavez")
check("M Shavez cannot open the vendors' ledger", get("/finance/surgery/vendors").status_code == 403)
check("M Shavez cannot open the hospital payments", get("/finance/surgery/receipt/%d" % rid).status_code == 403)
check("M Shavez cannot open the hospital's statement", get("/finance/surgery/paper/%d" % sp).status_code == 403)
post("/finance/surgery/case/%d/edit" % cid1, dict(stage="billed", patient="WALKTEST RAMESH", payer="ayushman", hospital="WALK HOSPITAL", due="1"))
check("M Shavez can move the stage but cannot change the amount due", q1("SELECT stage, due_p FROM surg_case WHERE id=?", (cid1,))[:] == ("billed", 7000000))
r = get("/finance/surgery/case/%d" % cid1)
check("M [S680] Shavez's case page shows the hospital money but not the actual cost, and no link to the payment pages",
      b"Money from the hospital" in r.data and b"Actually due to vendor" not in r.data and b"/finance/surgery/receipt/" not in r.data
      and b"40,000" not in r.data)
r = post("/finance/surgery/void", dict(kind="receipt", id=str(rid), why="wrong", back="/finance/surgery"))
check("M Shavez cannot remove a payment", q1("SELECT voided_at FROM surg_receipt WHERE id=?", (rid,))[0] == "")

# ---- N removing with a reason
p2 = q1("SELECT id FROM surg_paper WHERE case_id=? AND kind='xray'", (cid1,))[0]
r = post("/finance/surgery/void", dict(kind="paper", id=str(p2), why="", back="/finance/surgery/case/%d" % cid1))
check("N a removal without a reason is refused", "err=why" in r.headers["Location"])
post("/finance/surgery/void", dict(kind="paper", id=str(p2), why="wrong", back="/finance/surgery/case/%d" % cid1))
check("N a paper is removed with its reason and kept in the record", q1("SELECT void_why FROM surg_paper WHERE id=?", (p2,))[0] == "wrong")

# ---- O the switch
as_("manoj")
post("/finance/surgery/switch", dict(on="0"))
as_("shavez")
check("O switched off: Shavez gets the closed page", get("/finance/surgery").status_code == 403)
as_("manoj")
check("O ...while Dr Manoj still sees everything", get("/finance/surgery").status_code == 200)
post("/finance/surgery/switch", dict(on="1"))

# ---- R the tabs
r = get("/finance/surgery?p=credit&show=all")
check("R [S680 filters] Credit shows the Ayushman and cashless cases, not the cash one", b"WALKTEST RAMESH" in r.data and b"WALKTEST AFTER" in r.data
      and b"WALKTEST SITA" not in r.data)
r = get("/finance/surgery?p=cash&show=all")
check("R [S680 filters] Cash shows only cash cases", b"WALKTEST SITA" in r.data and b"WALKTEST RAMESH" not in r.data)
r = get("/finance/surgery?p=ayushman&show=all")
check("R [S680 filters] Ayushman shows only Ayushman", b"WALKTEST RAMESH" in r.data and b"WALKTEST AFTER" not in r.data)

# ---- U the S581 fixes (from the live dummy-case test, 18-Oct-2026)
as_("manoj")
check("U1 amounts in Indian grouping (₹ 1,50,000 · ₹ 12,34,567)", sc._r(15000000) == "₹ 1,50,000" and sc._r(123456700) == "₹ 12,34,567"
      and sc._r(99900) == "₹ 999" and sc._r(-15000000) == "− ₹ 1,50,000")
r = get("/finance/surgery/receipt/%d" % rid)
row1 = re.search(rb"WALKTEST RAMESH.*?</tr>", r.data, re.S)
row2 = re.search(rb"WALKTEST SITA.*?</tr>", r.data, re.S)
check("U2 the payment page shows what is still due AFTER this payment (₹ 10,000 and ₹ 0)", b"Still due after this" in r.data
      and row1 and b"10,000" in row1.group(0) and row2 and b"\xe2\x82\xb9 0<" in row2.group(0))
post("/finance/surgery/receipts", dict(day="2099-01-14", amount="500", from_whom="WALK HOSPITAL", ref="WALKUTR77"))
rid2 = q1("SELECT id FROM surg_receipt WHERE ref='WALKUTR77'")[0]
check("U3 the UTR / reference is shown on the payment page", b"UTR / ref WALKUTR77" in get("/finance/surgery/receipt/%d" % rid2).data)
cl.post("/finance/surgery/api/receipt/%d/statement" % rid2, data={"file": (io.BytesIO(PDF + b"u3"), "s.pdf")}, content_type="multipart/form-data")
sp2 = q1("SELECT id FROM surg_paper WHERE receipt_id=?", (rid2,))[0]
check("U7 a payment's statement opens while the payment stands", get("/finance/surgery/paper/%d" % sp2).status_code == 200)
post("/finance/surgery/void", dict(kind="receipt", id=str(rid2), why="wrong", back="/finance/surgery/receipts"))
check("U7 ...and stops opening once the payment is removed", get("/finance/surgery/paper/%d" % sp2).status_code == 404)
post("/finance/surgery/new", dict(patient="WALKTEST GONE", payer="cash", hospital="WALK HOSPITAL", source="Clinic"))
cg = q1("SELECT id FROM surg_case WHERE patient='WALKTEST GONE'")[0]
cl.post("/finance/surgery/api/case/%d/paper/billing" % cg, data={"file": (io.BytesIO(PDF + b"u7"), "b.pdf")}, content_type="multipart/form-data")
pg = q1("SELECT id FROM surg_paper WHERE case_id=?", (cg,))[0]
ok_before = get("/finance/surgery/paper/%d" % pg).status_code == 200
post("/finance/surgery/void", dict(kind="case", id=str(cg), why="wrong", back="/finance/surgery"))
check("U7 a case's papers stop opening once the case is removed", ok_before and get("/finance/surgery/paper/%d" % pg).status_code == 404)
r = get("/finance/surgery/vendor/%d" % vid)
check("U4 the remove-a-payment list starts with '— choose —' (nothing picked by itself)",
      b"<select name=what class='note'><option value=''>" in r.data)
check("U6 a vendor with live entries cannot be taken off the lists", b"Remove this vendor from the lists" not in r.data
      and post("/finance/surgery/vendor/%d/hide" % vid, {}).headers.get("Location", "").endswith("err=gone"))
check("U9 the vendor page's wording", b"Only you can see this page" in r.data)
check("U5 the implants table shows the quantity", b"<th class=r>Qty</th>" in get("/finance/surgery/case/%d" % cid1).data)
post("/finance/surgery/vendors", dict(name="WALK EMPTY VENDOR"))
ev = q1("SELECT id FROM surg_vendor WHERE name='WALK EMPTY VENDOR'")[0]
r = get("/finance/surgery/vendor/%d" % ev)
check("U6 a vendor with no entries offers 'Remove from the lists'", b"Remove this vendor from the lists" in r.data)
post("/finance/surgery/vendor/%d/hide" % ev, {})
check("U6 ...then it is gone from the vendors page and from the implant picker, kept in the record",
      b"WALK EMPTY VENDOR" not in get("/finance/surgery/vendors").data and b"WALK EMPTY VENDOR" not in get("/finance/surgery/case/%d" % cid1).data
      and q1("SELECT hidden FROM surg_vendor WHERE id=?", (ev,))[0] != "")
post("/finance/surgery/vendors", dict(name="WALK EMPTY VENDOR"))
check("U6 writing the same name again brings it back", b"WALK EMPTY VENDOR" in get("/finance/surgery/vendors").data)
r = get("/finance/surgery/case/%d/scan/billing" % cid1)
check("U8 the scanner page carries no second title bar of its own", b"class=top" not in r.data and b"/finance/scan/widget.js" in r.data)

# ---- V the S680 record (D801): IPD cases -- name, type, source, payer of five, settings, who sees what
def section_v():
    global bal
    as_("manoj")
    con = db()
    cols = {r[1] for r in con.execute("PRAGMA table_info(surg_case)")}
    con.close()
    check("V1 the record's new fields are on the table (type, source, payer kind, admission, IPD no., diagnosis, MLC)",
          {"case_type", "source_id", "payer_kind", "admit_date", "ipd_no", "diagnosis", "mlc"} <= cols)
    check("V1 the sources list is seeded Clinic · DTH · Imran · Awdhesh",
          {r[0] for r in db().execute("SELECT name FROM surg_source")} >= {"Clinic", "DTH", "Imran", "Awdhesh"})
    r = get("/finance/surgery")
    check("V2 the list is called IPD cases, one record per admission", b"<h1>IPD cases" in r.data and b"Surgery cases" not in r.data)
    check("V2 the unit is named IPD cases", q1("SELECT name FROM business_unit WHERE code='surgery'")[0] == "IPD cases")
    r = get("/finance/surgery/new")
    check("V2 the new-case page: New IPD case, five payers, three types, the source box with the list",
          b"New IPD case" in r.data and all(w.encode() in r.data for w in ("Cash · package", "TPA cashless", "Other scheme", "Conservative",
                                                                            "Surgical · no implant", "list=ipd_sources", "value='Awdhesh'")))
    as_("shavez")
    r = post("/finance/surgery/new", dict(patient="WALKTEST NOSRC", payer="cash"))
    check("V3 a case without a source is refused", "err=source" in r.headers["Location"] and not q1("SELECT id FROM surg_case WHERE patient='WALKTEST NOSRC'"))
    r = post("/finance/surgery/new", dict(patient="WALKTEST PKG", clinic_id="WALK9902", payer="package", case_type="surgical", source="walk new source",
                                           admit_date="2099-01-05", ipd_no="WALK/2099/77", diagnosis="WALK OA KNEE", procedure_text="WALK TKR",
                                           surgery_date="2099-01-06", hospital="WALK HOSPITAL"))
    cp = q1("SELECT c.*, s.name AS sname FROM surg_case c LEFT JOIN surg_source s ON s.id=c.source_id WHERE c.patient='WALKTEST PKG'")
    check("V4 a cash-package case: payer kind 'package', ledger class cash, admitted (admission date given), the new source joined the list",
          cp and cp["payer_kind"] == "package" and cp["payer"] == "cash" and cp["stage"] == "admitted" and cp["sname"] == "walk new source"
          and cp["ipd_no"] == "WALK/2099/77" and cp["diagnosis"] == "WALK OA KNEE")
    post("/finance/surgery/new", dict(patient="WALKTEST PKG2", payer="package", source="WALK NEW SOURCE"))
    check("V4 the same source typed in other letters is the same source, not a second one",
          q1("SELECT COUNT(*) FROM surg_source WHERE name='walk new source'")[0] == 1
          and q1("SELECT source_id FROM surg_case WHERE patient='WALKTEST PKG2'")[0] == cp["source_id"])
    post("/finance/surgery/new", dict(patient="WALKTEST TPA", payer="tpa", insurer="WALK STAR", source="Awdhesh"))
    post("/finance/surgery/new", dict(patient="WALKTEST SCHEME", payer="other", insurer="Deendayal", source="Awdhesh", mlc="1"))
    post("/finance/surgery/new", dict(patient="WALKTEST CONS", payer="cash", case_type="conservative", source="Clinic", admit_date="2099-01-14",
                                      diagnosis="WALK DISC PROLAPSE", procedure_text="WALK TRACTION"))
    ct, cs, cc = (q1("SELECT * FROM surg_case WHERE patient=?", (n,)) for n in ("WALKTEST TPA", "WALKTEST SCHEME", "WALKTEST CONS"))
    check("V4 TPA cashless -> class cashless, stage pre-approval applied; other scheme -> class deendayal (credit)",
          ct["payer_kind"] == "tpa" and ct["payer"] == "cashless" and ct["stage"] == "applied" and cs["payer_kind"] == "other" and cs["payer"] == "deendayal")
    check("V5 a conservative case never asks for the implant page; a medicolegal case asks for the MLC papers and the police memo",
          "implant" not in sc.missing_papers(db(), cc) and "implant" in sc.missing_papers(db(), ct)
          and {"mlc", "police"} <= set(sc.missing_papers(db(), cs)) and "mlc" not in sc.missing_papers(db(), ct))
    r = get("/finance/surgery/case/%d" % cc["id"])
    check("V5 [D804] the conservative case's page: type, source, admission (14-Jan, the year shown only when not this year), diagnosis, treatment, days admitted",
          b"Conservative" in r.data and b"Clinic" in r.data and b"done 14-Jan" in r.data and b"WALK DISC PROLAPSE" in r.data and b"WALK TRACTION" in r.data
          and b"1 day" in r.data)
    post("/finance/surgery/new", dict(patient="WALKTEST OLDFORM", payer="cashless", source="Clinic"))
    check("V6 a form with the old payer word still lands (cashless -> TPA cashless)",
          q1("SELECT payer_kind FROM surg_case WHERE patient='WALKTEST OLDFORM'")[0] == "tpa")
    # the list: filters and the count per source
    r = get("/finance/surgery?show=all")
    check("V7 the list shows source, type, payer, admission and the count per source",
          b"By source:" in r.data and b"Awdhesh 2" in r.data and b"Conservative" in r.data and b"Cash \xc2\xb7 package" in r.data and b"WALK/2099/77" in r.data)
    sid_aw = q1("SELECT id FROM surg_source WHERE name='Awdhesh'")[0]
    r = get("/finance/surgery?show=all&src=%d" % sid_aw)
    check("V7 the Source filter shows only that source's patients", b"WALKTEST TPA" in r.data and b"WALKTEST SCHEME" in r.data
          and b"WALKTEST PKG" not in r.data and b"WALKTEST CONS" not in r.data)
    r = get("/finance/surgery?show=all&type=conservative")
    check("V7 the Type filter shows only conservative cases", b"WALKTEST CONS" in r.data and b"WALKTEST TPA" not in r.data)
    r = get("/finance/surgery?show=all&p=package")
    check("V7 the Payer filter shows only cash-package cases", b"WALKTEST PKG" in r.data and b"WALKTEST SITA" not in r.data)
    r = get("/finance/surgery?show=all&q=WALK/2099/77")
    check("V7 the search finds a case by its IPD number", b"WALKTEST PKG" in r.data and b"WALKTEST TPA" not in r.data)
    # the edit, by Shavez
    post("/finance/surgery/case/%d/edit" % ct["id"], dict(stage="admitted", patient="WALKTEST TPA", payer="ayushman", case_type="noimplant",
                                                         source="Imran", admit_date="2099-01-02", ipd_no="WALK/9", diagnosis="WALK DX", mlc="1",
                                                         hospital="WALK HOSPITAL", due="999"))
    e = q1("SELECT c.*, s.name AS sname FROM surg_case c JOIN surg_source s ON s.id=c.source_id WHERE c.id=?", (ct["id"],))
    check("V8 Shavez changes source, type, payer, admission, IPD no., diagnosis and MLC; the payer's ledger class follows; the amount due is not his",
          e["sname"] == "Imran" and e["case_type"] == "noimplant" and e["payer_kind"] == "ayushman" and e["payer"] == "ayushman"
          and e["admit_date"] == "2099-01-02" and e["ipd_no"] == "WALK/9" and e["mlc"] == 1 and e["due_p"] is None)
    post("/finance/surgery/case/%d/edit" % ct["id"], dict(stage="admitted", patient="WALKTEST TPA", payer="ayushman", case_type="noimplant",
                                                         hospital="WALK HOSPITAL"))
    check("V8 a form without the source box keeps the case's source", q1("SELECT source_id FROM surg_case WHERE id=?", (ct["id"],))[0] == e["source_id"])
    r = post("/finance/surgery/case/%d/edit" % ct["id"], dict(stage="admitted", patient="WALKTEST TPA", payer="ayushman", case_type="bogus", source="Imran"))
    check("V8 a type that is not one of the three is refused", "err=type" in r.headers["Location"])
    r = post("/finance/surgery/case/%d/edit" % ct["id"], dict(stage="admitted", patient="WALKTEST TPA", payer="ayushman", case_type="surgical", source=""))
    check("V8 the source cannot be emptied", "err=source" in r.headers["Location"])
    # who sees what
    r = get("/finance/surgery/case/%d" % cid1)
    check("V9 Shavez: the implant's 'Charged to patient' column, never the actual cost", b"Charged to patient" in r.data and b"Actually due to vendor" not in r.data
          and b"name=payable" not in r.data and b"name=charge" in r.data)
    check("V9 Shavez cannot open Settings", get("/finance/surgery/settings").status_code == 403)
    r = post("/finance/surgery/settings", dict(admission="1", nursing="1", share="1"))
    check("V9 ...nor save them", r.status_code == 403 and q1("SELECT value FROM setting WHERE key='ipd.admission_p'") is None)
    as_("manoj")
    r = get("/finance/surgery/case/%d" % cid1)
    check("V9 Dr Manoj sees the actual cost on the same page (marked 'you only')", b"Actually due to vendor" in r.data and b"40,000" in r.data
          and b"you only" in r.data)
    # settings
    r = get("/finance/surgery/settings")
    check("V10 Settings opens for Dr Manoj with the defaults: admission 1200, nursing 500, share not set, the sources with their counts",
          r.status_code == 200 and b"value='1200'" in r.data and b"value='500'" in r.data and b"not set yet" in r.data and b"Awdhesh" in r.data
          and b"/finance/surgery/vendors" in r.data)
    check("V10 the settings read as Rs 1,200 · Rs 500 · not set", sc.ipd_settings(db()) == (120000, 50000, None))
    post("/finance/surgery/settings", dict(admission="1300", nursing="550.50", share="62.5"))
    check("V10 saving them: Rs 1,300 · Rs 550.50 · 62.5%", sc.ipd_settings(db()) == (130000, 55050, 62.5))
    r = post("/finance/surgery/settings", dict(admission="1300", nursing="550", share="150"))
    check("V10 a share above 100 is refused and nothing changes", "err=share" in r.headers["Location"] and sc.ipd_settings(db()) == (130000, 55050, 62.5))
    r = post("/finance/surgery/settings", dict(admission="", nursing="550", share=""))
    check("V10 a blank admission charge is refused", "err=amount" in r.headers["Location"])
    post("/finance/surgery/settings", dict(admission="1200", nursing="500", share=""))
    check("V10 the share can be cleared back to not set", sc.ipd_settings(db()) == (120000, 50000, None))
    sid_new = q1("SELECT id FROM surg_source WHERE name='walk new source'")[0]
    post("/finance/surgery/settings/source", dict(do="hide", id=str(sid_new)))
    r = get("/finance/surgery/new")
    check("V11 a source taken off the list leaves the new-case box but keeps its cases",
          b"value='walk new source'" not in r.data and q1("SELECT COUNT(*) FROM surg_case WHERE source_id=?", (sid_new,))[0] == 2)
    post("/finance/surgery/settings/source", dict(do="show", id=str(sid_new)))
    check("V11 ...and can be put back", b"value='walk new source'" in get("/finance/surgery/new").data)
    post("/finance/surgery/settings/source", dict(do="add", name="WALK REFERRER"))
    check("V11 a source added on Settings joins the list", b"value='WALK REFERRER'" in get("/finance/surgery/new").data)
    # a package case is a cash case to the vendor ledger
    post("/finance/surgery/case/%d/implant" % cp["id"], dict(vendor_id=str(vid), item="WALK TKR", qty="1", bill="52000", bill_to="doctor"))
    rows, bal2, waiting2, unas2 = sc.vendor_ledger(db(), vid)
    check("V12 a cash-package implant is owed by Dr Manoj like a cash one, never waiting for a hospital cheque",
          bal2 == bal + 5200000 and cp["id"] not in [w["id"] for w in waiting2])
    # an old row heals by itself
    con = db()
    con.execute("INSERT INTO surg_case (case_no, patient, payer) VALUES ('S-2099-0900','WALKTEST OLDROW','deendayal')")
    con.commit(); con.close()
    sc._schema_done = False
    get("/finance/surgery")
    check("V13 a row from before S680 heals by itself: deendayal -> other scheme, surgical, no source",
          tuple(q1("SELECT payer_kind, case_type, source_id FROM surg_case WHERE patient='WALKTEST OLDROW'")) == ("other", "surgical", None))
    r = get("/finance/surgery?show=all&p=other")
    check("V13 ...and is listed under Other scheme with 'no source' counted", b"WALKTEST OLDROW" in r.data and b"no source 1" in r.data)
    r = get("/finance/surgery/new?cid=WALK9901&name=X&payer=tpa&cp=C-2099-000002")
    check("V14 the Case Pack's 'tpa' lands as TPA cashless", b"value='tpa' checked" in r.data)


try:
    section_v()
except Exception as e:                       # noqa: BLE001 -- the control (an old module) stops here: counted red
    check("V the S680 section ran to its end (%s: %s)" % (type(e).__name__, str(e)[:80]), False)

# ---- W the cold review's fixes (S680, before install)
def section_w():
    as_("manoj")
    cw = q1("SELECT id FROM surg_case WHERE patient='WALKTEST CONS'")[0]
    r = post("/finance/surgery/case/%d/edit" % cw, dict(stage="admitted", patient="WALKTEST CONS", payer="cash", case_type="conservative",
                                                       source="WALK HALF SOURCE", due="abc", hospital="WALK HOSPITAL"))
    check("W1 an edit refused for a bad amount writes nothing -- not even a new source",
          "err=amount" in r.headers["Location"] and q1("SELECT id FROM surg_source WHERE name='WALK HALF SOURCE'") is None)
    con = db(); con.execute("UPDATE surg_case SET note='walk w1 probe' WHERE id=?", (cw,)); con.commit(); con.close()
    check("W1 ...and the database is free for the next write", q1("SELECT note FROM surg_case WHERE id=?", (cw,))[0] == "walk w1 probe")
    r = get("/finance/surgery/new")
    check("W2 [D804] the new-case form leaves the admission date blank (a case made before admission is not 'admitted')",
          re.search(rb"<input type=date name=admit_date class='in s'>", r.data) is not None)
    check("W2 [D804] the source chips and the payer choice are required on the form", b"name=source value='Clinic' required" in r.data
          and b"name=payer value='cash' required" in r.data)
    post("/finance/surgery/new", dict(patient="WALKTEST PLANNED", payer="cash", source="Clinic"))
    check("W2 a cash case with no admission date is 'planned'", q1("SELECT stage FROM surg_case WHERE patient='WALKTEST PLANNED'")[0] == "planned")
    con = db(); con.execute("UPDATE surg_case SET payer='cashless' WHERE patient='WALKTEST SITA'"); con.commit(); con.close()
    sc._schema_done = False
    get("/finance/surgery")
    check("W3 a payer changed by the old module after an undo heals its kind (cash -> TPA cashless)",
          q1("SELECT payer_kind FROM surg_case WHERE patient='WALKTEST SITA'")[0] == "tpa"
          and q1("SELECT payer_kind FROM surg_case WHERE patient='WALKTEST PKG'")[0] == "package")
    con = db(); con.execute("UPDATE surg_case SET payer='cash' WHERE patient='WALKTEST SITA'"); con.commit(); con.close()
    sc._schema_done = False
    get("/finance/surgery")
    old = q1("SELECT id FROM surg_case WHERE patient='WALKTEST OLDROW'")[0]
    r = get("/finance/surgery/case/%d" % old)
    check("W4 [D804] a case from before S680 (no source) opens with the source chips not required", b"name=source value='Clinic'>" in r.data
          and b"name=source value='Clinic' required" not in r.data)
    post("/finance/surgery/case/%d/edit" % old, dict(stage="discharged", patient="WALKTEST OLDROW", payer="other", case_type="surgical",
                                                    source="", hospital="WALK HOSPITAL"))
    check("W4 ...and can be saved without inventing a source", tuple(q1("SELECT stage, source_id FROM surg_case WHERE id=?", (old,))) == ("discharged", None))
    r = post("/finance/surgery/case/%d/edit" % cw, dict(stage="admitted", patient="WALKTEST CONS", payer="cash", case_type="conservative",
                                                       source="", hospital="WALK HOSPITAL"))
    check("W4 a case that has a source cannot have it emptied", "err=source" in r.headers["Location"])
    r = get("/finance/surgery?t=credit&show=all")
    check("W5 an old ?t=credit link still filters (credit only)", b"WALKTEST AFTER" in r.data and b"WALKTEST SITA" not in r.data)


try:
    section_w()
except Exception as e:                       # noqa: BLE001
    check("W the review's section ran to its end (%s: %s)" % (type(e).__name__, str(e)[:80]), False)

# ---- X backfill: old cases from 1-Apr-2025 (the owner, 30-Oct-2026 04:06) -- [D804] REWRITTEN: the same compact form, nothing
#      compulsory but the name and the payer, the implant and both payment statuses on it, the same list
def section_x():
    as_("shavez")
    r = get("/finance/surgery")
    check("X1 every login of the page sees '+ Old case (backfill)'", b"/finance/surgery/backfill" in r.data and b"Old case (backfill)" in r.data)
    r = get("/finance/surgery/backfill")
    check("X1 [D804] the backfill page: from 01-Apr-2025, the count so far, dates limited from 1-Apr-2025, source not required, "
          "the implant and both payment statuses offered", r.status_code == 200 and b"01-Apr-2025" in r.data and b"min='2025-04-01'" in r.data
          and b"0 entered so far" in r.data and b"name=source value='Clinic' required" not in r.data
          and b"name=implant_status value='cheque'" in r.data and b"name=money_status value='received'" in r.data and b"name=item" in r.data)
    base = dict(patient="WALKTEST OLD ONE", clinic_id="WALK9905", payer="ayushman", case_type="surgical", hospital="WALK HOSPITAL",
                diagnosis="WALK OLD FRACTURE", procedure_text="WALK OLD NAIL", ipd_no="WALK/2025/9")
    r = post("/finance/surgery/backfill", dict(base, admit_date="2025-03-31"))
    check("X2 an admission before 1-Apr-2025 is refused", "err=early" in r.headers["Location"])
    r = post("/finance/surgery/backfill", dict(base, admit_date="2099-02-01"))
    check("X2 an admission after today is refused", "err=date" in r.headers["Location"])
    r = post("/finance/surgery/backfill", dict(base, admit_date="2025-06-10", discharge_date="2025-06-01"))
    check("X2 a discharge before the admission is refused", "err=date" in r.headers["Location"]
          and q1("SELECT COUNT(*) FROM surg_case WHERE patient='WALKTEST OLD ONE'")[0] == 0)
    r = post("/finance/surgery/backfill", dict(base, payer="", admit_date="2025-06-10"))
    check("X2 [D804] the payer is still needed", "err=payer" in r.headers["Location"])
    r = post("/finance/surgery/backfill", dict(base, admit_date="2025-06-10", item="WALK OLD NAIL 9"))
    check("X2 [D804] an implant without its vendor is refused, nothing written", "err=vendor" in r.headers["Location"]
          and q1("SELECT COUNT(*) FROM surg_case WHERE patient='WALKTEST OLD ONE'")[0] == 0)
    r = post("/finance/surgery/backfill", dict(base, admit_date="2025-06-10", surgery_date="2025-06-11", discharge_date="2025-06-15", mlc="1",
                                               item="WALK BIPOLAR 46", vendor_new="WALK OLD VENDOR", bill="21000",
                                               implant_status="cheque", money_status="received"))
    o1 = q1("SELECT * FROM surg_case WHERE patient='WALKTEST OLD ONE'")
    io1 = q1("SELECT i.*, v.name AS vname FROM surg_implant i JOIN surg_vendor v ON v.id=i.vendor_id WHERE i.case_id=?", (o1["id"],)) if o1 else None
    check("X3 [D804] an old case is saved: numbered in its admission year (S-2025-0001), marked backfill, no source needed, its implant "
          "with the new vendor, the implant at 'cheque received', the hospital money received",
          o1 and o1["case_no"] == "S-2025-0001" and o1["backfill"] == 1 and o1["source_id"] is None and o1["payer_kind"] == "ayushman"
          and o1["discharge_date"] == "2025-06-15" and o1["mlc"] == 1 and o1["implant_status"] == "cheque" and o1["money_status"] == "received"
          and io1 and io1["vname"] == "WALK OLD VENDOR" and io1["bill_p"] == 2100000 and io1["bill_to"] == "patient"
          and "msg=backfill" in r.headers["Location"] and "no=S-2025-0001" in r.headers["Location"])
    r = get(r.headers["Location"].replace("http://localhost", ""))
    check("X3 ...and the page opens empty for the next one, naming the saved case with a link to open it",
          b"Saved as <b>S-2025-0001</b>" in r.data and b"1 entered so far" in r.data and (b"open=%d#c%d" % (o1["id"], o1["id"])) in r.data)
    r = post("/finance/surgery/backfill", dict(base, patient="SOMEONE ELSE", admit_date="2025-06-10"))
    check("X4 the same clinic ID with the same admission date is not entered twice", "err=dup" in r.headers["Location"]
          and "no=S-2025-0001" in r.headers["Location"] and q1("SELECT COUNT(*) FROM surg_case WHERE backfill=1")[0] == 1)
    post("/finance/surgery/backfill", dict(patient="WALKTEST OLD TWO", payer="cash", case_type="conservative", admit_date="2025-09-02", source="DTH"))
    m26 = q1("SELECT case_no FROM surg_case WHERE case_no LIKE 'S-2026-%' ORDER BY case_no DESC LIMIT 1")   # the live copy holds two of 2026
    want26 = "S-2026-%04d" % ((int(m26[0].split("-")[-1]) + 1) if m26 else 1)
    post("/finance/surgery/backfill", dict(patient="WALKTEST OLD THREE", payer="tpa", admit_date="2026-02-20", source="Clinic"))
    check("X5 numbering follows the admission year: S-2025-0002, then the next 2026 number (%s)" % want26,
          q1("SELECT case_no FROM surg_case WHERE patient='WALKTEST OLD TWO'")[0] == "S-2025-0002"
          and q1("SELECT case_no FROM surg_case WHERE patient='WALKTEST OLD THREE'")[0] == want26)
    r = post("/finance/surgery/backfill", dict(patient="WALKTEST OLD TWO", payer="cash", admit_date="2025-09-02"))
    check("X4 without a clinic ID, the same name with the same admission date is not entered twice", "err=dup" in r.headers["Location"])
    r = post("/finance/surgery/backfill", dict(patient="WALKTEST OLD NODATE", payer="cash", surgery_date="2025-11-03"))
    check("X2 [D804] nothing compulsory but the name and the payer: an old case without an admission date is saved, numbered in its "
          "surgery's year", "msg=backfill" in r.headers["Location"]
          and q1("SELECT case_no FROM surg_case WHERE patient='WALKTEST OLD NODATE'")[0].startswith("S-2025-"))
    oid = q1("SELECT id FROM surg_case WHERE patient='WALKTEST OLD NODATE'")[0]
    post("/finance/surgery/case/%d/edit" % oid, dict(patient="WALKTEST OLD NODATE", admit_date="2025-11-01", ipd_no="WALK/OLD/1"))
    r = get("/finance/surgery?pt=discharged&show=old")
    check("X2 [S370] an old case filled in later (admission date, no discharge date) stays a discharged case -- its stage, its chip and the filter",
          q1("SELECT stage FROM surg_case WHERE id=?", (oid,))[0] == "discharged" and b"WALKTEST OLD NODATE" in r.data
          and b"WALKTEST OLD NODATE" not in get("/finance/surgery?pt=admitted").data)
    r = get("/finance/surgery?show=old")
    check("X6 'Old cases only' lists only the old cases, marked 'old case', papers not counted as missing",
          b"WALKTEST OLD ONE" in r.data and b"WALKTEST OLD TWO" in r.data and b"WALKTEST CONS" not in r.data
          and b"old case" in r.data and b"Scan the missing papers" not in r.data)
    r = get("/finance/surgery")
    check("X6 [D804] old cases sit in the SAME list as the new ones", b"WALKTEST OLD ONE" in r.data and b"WALKTEST CONS" in r.data)
    r = get("/finance/surgery/case/%d" % o1["id"])
    check("X6 an old case's page says so and asks for no paper", b"An old case, entered afterwards" in r.data and b"'warn'>missing" not in r.data)
    post("/finance/surgery/new", dict(patient="WALKTEST NEWYEAR", payer="cash", source="Clinic", admit_date="2098-12-30"))
    check("X7 a new case is numbered in its admission year too (S-2098-0001)", q1("SELECT case_no FROM surg_case WHERE patient='WALKTEST NEWYEAR'")[0] == "S-2098-0001")


try:
    section_x()
except Exception as e:                       # noqa: BLE001
    check("X the backfill section ran to its end (%s: %s)" % (type(e).__name__, str(e)[:80]), False)


def rowblock(data, cid):
    """One case's row on the list, its opened sections included (up to the next row)."""
    i = data.find(b"<details class='crow' id='c%d'" % cid)
    if i < 0:
        return None
    j = data.find(b"<details class='crow' id='c", i + 10)
    return data[i:j if j > 0 else len(data)]


# ---- Y S680 final (D804): mobile, UHID, TPA list, Case Pack pick, three statuses, the case in place, stage sections, compact forms
def section_y():
    as_("shavez")
    con = db()
    cols = {r[1] for r in con.execute("PRAGMA table_info(surg_case)")}
    has_tpa = con.execute("SELECT name FROM sqlite_master WHERE name='surg_tpa'").fetchone() is not None
    con.close()
    check("Y1 the new fields are on the table (UHID, mobile, implant payment, hospital money) and the TPA list is its own table",
          {"uhid", "mobile", "implant_status", "money_status"} <= cols and has_tpa)
    r = post("/finance/surgery/new", dict(patient="WALKTEST MOBILE", mobile="98765" " 43210, 0-91234" "-56789", uhid="WALKUH77", payer="tpa",
                                           insurer="+", insurer_new="WALK STAR HEALTH", source_new="WALK SRC TYPED", admit_date="2099-01-12",
                                           ipd_no="WALK/IPD/5", diagnosis="WALK FR FEMUR", case_type="surgical", casepack_id="C-2099-000007",
                                           surgery_date="2099-01-13", procedure_text="WALK NAIL"))
    cm = q1("SELECT c.*, s.name AS sname FROM surg_case c LEFT JOIN surg_source s ON s.id=c.source_id WHERE c.patient='WALKTEST MOBILE'")
    check("Y2 a case made with no clinic ID: two mobiles kept as ten digits each, the UHID, a new TPA written with '+ add', a new source "
          "typed in the '+' box, the Case Pack number", cm and cm["clinic_id"] == "" and cm["mobile"] == "98765" "43210, 91234" "56789"
          and cm["uhid"] == "WALKUH77" and cm["insurer"] == "WALK STAR HEALTH" and cm["sname"] == "WALK SRC TYPED"
          and cm["casepack_id"] == "C-2099-000007" and q1("SELECT COUNT(*) FROM surg_tpa WHERE name='WALK STAR HEALTH'")[0] == 1)
    check("Y2 ...and the form goes straight back to the list with that case open", "open=%d" % cm["id"] in r.headers["Location"]
          and r.headers["Location"].endswith("#c%d" % cm["id"]) and "msg=new" in r.headers["Location"])
    r = post("/finance/surgery/new", dict(patient="WALKTEST BADMOB", mobile="12345", payer="cash", source="Clinic"))
    check("Y2 a mobile that is not ten digits is refused, nothing made", "err=mobile" in r.headers["Location"]
          and q1("SELECT id FROM surg_case WHERE patient='WALKTEST BADMOB'") is None)
    r = get("/finance/surgery/new")
    check("Y3 the new-case form offers the TPA name in its drop-down, with '+ add a name'", b"<option value='WALK STAR HEALTH'>" in r.data
          and b"+ add a name" in r.data and b"name=uhid" in r.data and b"Clinic ID <span class=sm>(optional)</span>" in r.data)
    check("Y3 compact: the fields are sized (no full-width boxes of the old form on this page)", b"class='note'" not in r.data
          and b"class='in s'" in r.data and b"@media (max-width:760px)" in r.data)
    for q, what in (("98765" "43210", "the full mobile"), ("43210", "the last five digits"), ("91234" "56789", "the second mobile"), ("WALKUH77", "the UHID")):
        r = get("/finance/surgery?q=" + q)
        check("Y4 the list's search finds the case by %s" % what, b"WALKTEST MOBILE" in r.data and b"WALKTEST SITA" not in r.data)
    r = get("/finance/surgery?q=90000" "11111")
    check("Y4 the search by a phone the console's mirror holds finds a case that has no mobile of its own (WALK9901's)",
          b"WALKTEST RAMESH" in r.data and b"WALKTEST MOBILE" not in r.data)
    r = get("/finance/surgery/new?q=90000111")
    check("Y5 [S370 review] the new-case Find reads the console's mirror: the patient with the full mobile; the pick carries the UID, "
          "never the number", b"WALKTEST RAMESH" in r.data and b"90000" b" 11111" in r.data and b"uid=WALKUID1" in r.data and b"mob=" not in r.data)
    r = get("/finance/surgery/new?q=WALKCONSOLE")
    check("Y5 a patient only the console's mirror knows is found and offered", b"WALKTEST CONSOLE ONLY" in r.data and b"uid=WALKUID2" in r.data)
    r = get("/finance/surgery/new?cid=WALKCONSOLE&name=WALKTEST%20CONSOLE%20ONLY&uid=WALKUID2")
    check("Y5 [S370 review] ...and picking fills the full mobile from the mirror on the server", b"value='98888" b" 77777'" in r.data)
    r = get("/finance/surgery/new?cid=WALK9901&name=WALKTEST%20RAMESH&mob=90000" "11111&uid=WALKUID1")
    check("Y6 the Case Pack number is picked from that patient's Case Pack cases (newest first; another patient's never offered)",
          b"<option value='C-2099-000002'>C-2099-000002" in r.data and b"<option value='C-2099-000001'>C-2099-000001" in r.data
          and r.data.find(b"C-2099-000002") < r.data.find(b"C-2099-000001") and b"C-2099-000009" not in r.data
          and b"value='90000" b" 11111'" in r.data)
    r = get("/finance/surgery/new?cid=WALK9901&name=WALKTEST%20RAMESH&cp=C-2099-000002")
    check("Y6 the Case Pack's own link preselects its case", b"<option value='C-2099-000002' selected>" in r.data)
    # the three statuses
    con = db()
    ids = {n: q1("SELECT id FROM surg_case WHERE patient=?", (n,))[0] for n in ("WALKTEST MOBILE", "WALKTEST CONS", "WALKTEST PLANNED", "WALKTEST RAMESH", "WALKTEST OLD ONE")}
    con.close()
    r = get("/finance/surgery?pt=admitted")
    check("Y7 Patient: Admitted -- the admitted cases, not the discharged nor the not-yet-admitted",
          b"WALKTEST MOBILE" in r.data and b"WALKTEST CONS" in r.data and b"WALKTEST RAMESH" not in r.data and b"WALKTEST PLANNED" not in r.data)
    r = get("/finance/surgery?pt=discharged")
    check("Y7 Patient: Discharged -- includes the old cases", b"WALKTEST RAMESH" in r.data and b"WALKTEST OLD ONE" in r.data and b"WALKTEST MOBILE" not in r.data)
    r = get("/finance/surgery?pt=planned")
    check("Y7 Patient: Not admitted yet", b"WALKTEST PLANNED" in r.data and b"WALKTEST CONS" not in r.data)
    r = get("/finance/surgery?money=received")
    check("Y7 Hospital money: Received -- the old case marked received", b"WALKTEST OLD ONE" in r.data and b"WALKTEST MOBILE" not in r.data)
    r = get("/finance/surgery?money=pending")
    check("Y7 Hospital money: Pending -- a discharged case with its money not in", b"WALKTEST RAMESH" in r.data and b"WALKTEST OLD ONE" not in r.data)
    r = get("/finance/surgery?imp=na")
    check("Y7 Implant payment: Not needed -- the conservative case", b"WALKTEST CONS" in r.data and b"WALKTEST MOBILE" not in r.data)
    r = get("/finance/surgery?imp=pending")
    check("Y7 Implant payment: Pending -- surgical cases not yet paid (the old case at 'cheque received' too)",
          b"WALKTEST MOBILE" in r.data and b"WALKTEST OLD ONE" in r.data and b"WALKTEST CONS" not in r.data)
    # the Python and the SQL forms of each status agree, case by case (the filters and the chips never disagree)
    con = db()
    bad = []
    for c in con.execute("SELECT c.* FROM surg_case c WHERE c.voided_at=''").fetchall():
        got = sc.received(con, c["id"])
        for key, table, val in (("p", sc.SQL_P, sc.pstatus(c)), ("m", sc.SQL_M, sc.mstatus(c, got)), ("i", sc.SQL_I, sc.istatus(c)[0])):
            for k, sql in table.items():
                inside = con.execute("SELECT 1 FROM surg_case c WHERE c.id=? AND %s" % sql, (c["id"],)).fetchone() is not None
                if inside != (val == k):
                    bad.append((c["case_no"], key, k))
    con.close()
    check("Y7 every case's status chips and the filters' SQL agree (%d disagreements%s)" % (len(bad), (": " + str(bad[:4])) if bad else ""), not bad)
    r = post("/finance/surgery/case/%d/status" % ids["WALKTEST MOBILE"], dict(implant_status="raised", ret="/finance/surgery?imp=pending&open=%d#c%d" % (ids["WALKTEST MOBILE"], ids["WALKTEST MOBILE"])))
    check("Y8 Shavez moves the implant payment on (bill raised), from the case open in the list -- and is taken back there",
          q1("SELECT implant_status FROM surg_case WHERE id=?", (ids["WALKTEST MOBILE"],))[0] == "raised"
          and r.headers["Location"].startswith("/finance/surgery?imp=pending&open=%d&msg=status#c%d" % (ids["WALKTEST MOBILE"], ids["WALKTEST MOBILE"])))
    r = post("/finance/surgery/case/%d/status" % ids["WALKTEST MOBILE"], dict(implant_status="bogus"))
    check("Y8 a status not on the list is refused", "err=status" in r.headers["Location"]
          and q1("SELECT implant_status FROM surg_case WHERE id=?", (ids["WALKTEST MOBILE"],))[0] == "raised")
    r = post("/finance/surgery/case/%d/status" % ids["WALKTEST MOBILE"], dict(money_status="received", due="1", ret="https://evil.example/x"))
    check("Y8 the hospital money marked received; a 'ret' to another site is never followed; the amount due is not Shavez's",
          q1("SELECT money_status, due_p FROM surg_case WHERE id=?", (ids["WALKTEST MOBILE"],))[:] == ("received", None)
          and r.headers["Location"].startswith("/finance/surgery/case/%d" % ids["WALKTEST MOBILE"]))
    # the list: compact rows that open in place
    r = get("/finance/surgery")
    row = rowblock(r.data, ids["WALKTEST MOBILE"])
    check("Y9 [S370, the owner 12:49] the list's row is compact: name, UHID, IPD, the FULL mobile(s), source, payer with its TPA, the three "
          "statuses, the next step -- and its body is empty until tapped", row and b"UHID WALKUH77" in row and b"98765" b" 43210, 91234" b" 56789" in row
          and b"xxx" not in row and b"WALK STAR HEALTH" in row and b"Implant: bill raised" in row
          and b"Hospital money: received" in row and b"<span class='cn'>" in row and b"<div class='cbody'></div>" in row)
    r = get("/finance/surgery?open=%d" % ids["WALKTEST MOBILE"])
    row = rowblock(r.data, ids["WALKTEST MOBILE"])
    check("Y9 ?open= opens that case IN PLACE: its Next line and the eight stage sections, every form carrying the way back to the list",
          row and (b"<details class='crow' id='c%d' data-id='%d' open>" % (ids["WALKTEST MOBILE"], ids["WALKTEST MOBILE"])) in row and b"<b>Next</b>" in row and all((b"<details class='sec stg'" in row) and (("id='s%d'" % n).encode() in row) for n in range(1, 9))
          and row.count(b"name=ret value='/finance/surgery?open=%d#c%d'" % (ids["WALKTEST MOBILE"], ids["WALKTEST MOBILE"])) >= 4)
    r = get("/finance/surgery/case/%d?frag=1&ret=%s" % (ids["WALKTEST MOBILE"], quote("/finance/surgery?q=WALK&open=%d#c%d" % (ids["WALKTEST MOBILE"], ids["WALKTEST MOBILE"]), safe="")))
    check("Y9 the case's sections alone (what the list fetches when a row is tapped): no page around them, the full mobile on the case",
          r.status_code == 200 and b"<html" not in r.data and b"<div class='case'>" in r.data and b"98765" b" 43210, 91234" b" 56789" in r.data
          and b"name=ret value='/finance/surgery?q=WALK&amp;open=" in r.data)
    check("Y9 the list page carries the script that fetches a case when its row is tapped", b"?frag=1&ret=" in get("/finance/surgery").data)
    # a section's form changes only its own fields
    post("/finance/surgery/case/%d/edit" % ids["WALKTEST MOBILE"], dict(discharge_date="2099-01-14", ret="/finance/surgery"))
    cm2 = q1("SELECT * FROM surg_case WHERE id=?", (ids["WALKTEST MOBILE"],))
    check("Y10 the discharge section's form writes the discharge date and leaves everything else as it was (name, mobile, UHID, TPA, source)",
          cm2["discharge_date"] == "2099-01-14" and cm2["patient"] == "WALKTEST MOBILE" and cm2["mobile"] == cm["mobile"]
          and cm2["uhid"] == "WALKUH77" and cm2["insurer"] == "WALK STAR HEALTH" and cm2["source_id"] == cm["source_id"] and cm2["stage"] == "discharged")
    r = post("/finance/surgery/case/%d/edit" % ids["WALKTEST MOBILE"], dict(discharge_date="2099-01-01"))
    check("Y10 a discharge before the admission is refused", "err=date" in r.headers["Location"]
          and q1("SELECT discharge_date FROM surg_case WHERE id=?", (ids["WALKTEST MOBILE"],))[0] == "2099-01-14")
    # the Next line
    post("/finance/surgery/new", dict(patient="WALKTEST NOIMPLANT", payer="cash", source="Clinic", case_type="surgical", admit_date="2099-01-13",
                                      surgery_date="2099-01-14", procedure_text="WALK ORIF"))
    nc = q1("SELECT * FROM surg_case WHERE patient='WALKTEST NOIMPLANT'")
    t, n = sc.next_step(db(), nc, 0)
    check("Y11 the Next line: an admitted surgical case with its surgery but no implant -> 'Add the implant', in section 2", n == 2 and "implant" in t)
    t, n = sc.next_step(db(), q1("SELECT * FROM surg_case WHERE patient='WALKTEST PLANNED'"), 0)
    check("Y11 ...a case not yet admitted -> the admission date and IPD number, section 1", n == 1 and "admission" in t)
    r = get("/finance/surgery?open=%d" % nc["id"])
    sec2 = re.search(rb"<details class='sec stg'( open)? id='s2'>", r.data)
    check("Y11 ...and that section is the one open", sec2 and sec2.group(1) == b" open" and b"<details class='sec stg' open id='s1'>" not in r.data)
    # removal reasons are tapped
    r = get("/finance/surgery/case/%d" % ids["WALKTEST RAMESH"])
    check("Y12 the reason for removing a paper or an implant line is tapped (chips), not chosen from a drop-down",
          b"name=why value='wrong'" in r.data and b"<select name=why" not in r.data)
    # the TPA list on Settings
    as_("manoj")
    r = get("/finance/surgery/settings")
    check("Y13 Settings lists the TPA / scheme names with their counts (the names written on cases joined it)",
          b"TPA and scheme names" in r.data and b"WALK STAR HEALTH" in r.data and b"WALK TPA" in r.data)
    tid = q1("SELECT id FROM surg_tpa WHERE name='WALK TPA'")[0]
    post("/finance/surgery/settings/tpa", dict(do="hide", id=str(tid)))
    check("Y13 a TPA name taken off the list leaves the drop-down", b"<option value='WALK TPA'>" not in get("/finance/surgery/new").data)
    post("/finance/surgery/settings/tpa", dict(do="show", id=str(tid)))
    post("/finance/surgery/settings/tpa", dict(do="add", name="WALK CARE TPA"))
    check("Y13 ...put back, and a name added on Settings joins it", b"<option value='WALK TPA'>" in get("/finance/surgery/new").data
          and b"<option value='WALK CARE TPA'>" in get("/finance/surgery/new").data)
    as_("shavez")
    check("Y13 Shavez cannot change the TPA list", post("/finance/surgery/settings/tpa", dict(do="add", name="WALK SHAVEZ TPA")).status_code == 403
          and q1("SELECT id FROM surg_tpa WHERE name='WALK SHAVEZ TPA'") is None)
    # the actual cost stays Dr Manoj's on the in-place case too
    r = get("/finance/surgery/case/%d?frag=1" % ids["WALKTEST RAMESH"])
    check("Y14 the in-place case never shows Shavez the implant's actual cost (40,000) nor the payment pages",
          b"Actually due to vendor" not in r.data and b"40,000" not in r.data and b"name=payable" not in r.data and b"/finance/surgery/receipt/" not in r.data)
    as_("manoj")
    r = get("/finance/surgery/case/%d?frag=1" % ids["WALKTEST RAMESH"])
    check("Y14 ...Dr Manoj sees it there, marked 'you only', and the amount due box", b"Actually due to vendor" in r.data and b"40,000" in r.data
          and b"name=due" in r.data)
    as_("shavez")
    r = get("/finance/surgery/case/%d/scan/billing?ret=%s" % (ids["WALKTEST MOBILE"], quote("/finance/surgery?open=%d#c%d" % (ids["WALKTEST MOBILE"], ids["WALKTEST MOBILE"]), safe="")))
    check("Y15 a scan asked for from the list goes back to the list with the case open", ('"backUrl": "/finance/surgery?open=%d&msg=paper#c%d"' % (ids["WALKTEST MOBILE"], ids["WALKTEST MOBILE"])).encode() in r.data)
    r = post("/finance/surgery/void", dict(kind="implant", id="999999", why="wrong", back="/finance/surgery?open=5#c5"))
    check("Y15 a removal from the list goes back to the list, its anchor last", r.headers["Location"].endswith("/finance/surgery?open=5&err=gone#c5"))
    def nested(data):
        depth, worst = 0, 0
        for m in re.finditer(rb"<(/?)form\b", data):
            depth += -1 if m.group(1) else 1
            worst = max(worst, depth)
        return worst
    pages = {"new": get("/finance/surgery/new?q=WALK").data, "backfill": get("/finance/surgery/backfill?q=WALK").data,
             "list with a case open": get("/finance/surgery?open=%d" % ids["WALKTEST MOBILE"]).data,
             "case": get("/finance/surgery/case/%d" % ids["WALKTEST MOBILE"]).data}
    bad = [k for k, d in pages.items() if nested(d) > 1]
    check("Y16 no form sits inside another on any IPD page (the Find box has its own form, tied by form=ipdfind)%s" % (
          (" -- nested on: " + ", ".join(bad)) if bad else ""), not bad and b"<form id=ipdfind method='post'" in pages["new"]
          and b"<button class='btn sec2' form=ipdfind>Find</button>" in pages["new"])


try:
    section_y()
except Exception as e:                       # noqa: BLE001
    check("Y the D804 section ran to its end (%s: %s)" % (type(e).__name__, str(e)[:120]), False)

# ---- Z S370 (the owner, 30-Oct 12:49 and 13:07): call the patient from the case through MyOperator's IVR
def section_z():
    as_("shavez")
    cid = q1("SELECT id FROM surg_case WHERE patient='WALKTEST MOBILE'")[0]
    ret = "/finance/surgery?open=%d#c%d" % (cid, cid)
    r = get("/finance/surgery?open=%d" % cid)
    blk = rowblock(r.data, cid)
    check("Z1 the case opened in place offers one 'Call (IVR)' button per stored mobile, for a login on the IVR call list",
          blk and blk.count(b"/case/%d/call" % cid) == 2 and b"Call 98765" b" 43210 (IVR)" in blk and b"Call 91234" b" 56789 (IVR)" in blk)
    CALLS.clear()
    r = post("/finance/surgery/case/%d/call" % cid, dict(n="1", number="99999" "99999", ret=ret))
    k = q1("SELECT * FROM surg_call WHERE case_id=? ORDER BY id DESC LIMIT 1", (cid,))
    check("Z2 Shavez presses it: the call service gets HIS IVR name, the case's STORED second number (never one from the page), the key in "
          "the header; the page goes back to the list with the case open; the call is kept with the last 4 digits only",
          len(CALLS) == 1 and CALLS[0][0] == "walkcallkey" and CALLS[0][1] == {"agent": "WALK SHAVEZ", "patient_number": "91234" "56789", "reference_id": "IPD%d" % cid}
          and r.headers["Location"].endswith("open=%d&msg=call#c%d" % (cid, cid)) and k and k["last4"] == "6789" and k["result"] == "accepted"
          and "91234" "56789" not in json.dumps(dict(k)))
    r = post("/finance/surgery/case/%d/call" % cid, dict(n="0", ret=ret))
    check("Z3 a second press within a minute is refused and nothing is sent", "err=callwait" in r.headers["Location"] and len(CALLS) == 1)
    os.environ["SURGERY_NOW"] = "2099-01-15T10:02:00"
    r = post("/finance/surgery/case/%d/call" % cid, dict(n="7", ret=ret))
    check("Z4 a number the case does not hold is refused and nothing is sent", "err=callnum" in r.headers["Location"] and len(CALLS) == 1)
    pid = q1("SELECT id FROM surg_case WHERE patient='WALKTEST PLANNED'")[0]
    r = post("/finance/surgery/case/%d/call" % pid, dict(n="0"))
    check("Z4 ...as is a case with no mobile", "err=callnum" in r.headers["Location"] and len(CALLS) == 1)
    CALLMODE["m"] = "refuse"
    r = post("/finance/surgery/case/%d/call" % cid, dict(n="0", ret=ret))
    k = q1("SELECT * FROM surg_call WHERE case_id=? ORDER BY id DESC LIMIT 1", (cid,))
    check("Z5 MyOperator's refusal is said plainly and kept, its digits cut to the last 4", "err=callno" in r.headers["Location"]
          and k["result"] == "refused" and "98765" "43210" not in k["why"] and "…3210" in k["why"])
    CALLMODE["m"] = "ok"
    os.environ["SURGERY_NOW"] = "2099-01-15T10:04:00"
    good = os.environ["SURGERY_CALL_URL"]
    sc.CALL_URL = "http://127.0.0.1:9/call"
    r = post("/finance/surgery/case/%d/call" % cid, dict(n="0", ret=ret))
    sc.CALL_URL = good
    check("Z6 the call service down: 'did not answer', kept as an error", "err=calldown" in r.headers["Location"]
          and q1("SELECT result FROM surg_call WHERE case_id=? ORDER BY id DESC LIMIT 1", (cid,))[0] == "error")
    os.environ["SURGERY_NOW"] = "2099-01-15T10:06:00"
    n0 = len(CALLS)
    sc.WA_ENV = os.path.join(TMP, "no.env")
    r = post("/finance/surgery/case/%d/call" % cid, dict(n="0", ret=ret))
    sc.WA_ENV = os.environ["SURGERY_WA_ENV"]
    check("Z7 no key on the server: refused before anything is sent", "err=callkey" in r.headers["Location"] and len(CALLS) == n0)
    as_("manoj")
    os.environ["SURGERY_NOW"] = "2099-01-15T10:08:00"
    r = post("/finance/surgery/case/%d/call" % cid, dict(n="0", ret=ret))
    blk = rowblock(get("/finance/surgery?open=%d" % cid).data, cid)
    check("Z8 a login not on the IVR call list: the button is greyed with the reason, and a press is refused, nothing sent",
          "err=callagent" in r.headers["Location"] and len(CALLS) == n0 and b"IVR not set for your login" in blk and b"/case/%d/call" % cid not in blk)
    check("Z9 the case's history names each call (who, when, the last 4)", b"IVR call to \xe2\x80\xa66789 (placed)" in blk
          and b"IVR call to \xe2\x80\xa63210 (not placed)" in blk)
    os.environ["SURGERY_NOW"] = "2099-01-15T10:00:00"


try:
    section_z()
except Exception as e:                       # noqa: BLE001
    check("Z the IVR call section ran to its end (%s: %s)" % (type(e).__name__, str(e)[:120]), False)

# ---- R S370: the cold review's findings, each with its check
def section_r():
    as_("shavez")
    cid = q1("SELECT id FROM surg_case WHERE patient='WALKTEST MOBILE'")[0]
    r = cl.post("/finance/surgery", data=dict(q="98765" "43210"))
    check("R1 the list's search is posted and finds the case by its full mobile", r.status_code == 200 and b"WALKTEST MOBILE" in r.data)
    hrefs = b" ".join(re.findall(rb"(?:href|action)='[^']*'|name=ret value='[^']*'|var here=[^;]*", r.data))
    check("R1 ...and no address the page builds carries the number (links, forms, the way back, the script's fetch)",
          b"98765" b"43210" not in hrefs and b"98765" not in hrefs and b"43210" not in hrefs)
    r = cl.post("/finance/surgery/new", data=dict(find="1", q="90000111"))
    check("R1 the new-case Find is posted too; its pick links carry no number", r.status_code == 200 and b"WALKTEST RAMESH" in r.data
          and not re.search(rb"href='[^']*90000" rb"11111", r.data))
    r = post("/finance/surgery/new", dict(patient="WALKTEST NOSRC2", mobile="98123" " 45678", payer="cash"))
    check("R1 a refused new case goes back without the number in its address", "err=source" in r.headers["Location"]
          and "98123" "45678" not in r.headers["Location"] and "98123" not in r.headers["Location"])
    r = post("/finance/surgery/backfill", dict(patient="WALKTEST OLDNOPAY", mobile="98123" " 45678"))
    check("R1 ...nor a refused old case", "err=payer" in r.headers["Location"] and "98123" not in r.headers["Location"])
    as_("manoj")
    post("/finance/surgery/backfill", dict(patient="WALKTEST OLDCASHIMP", payer="cash", admit_date="2025-08-01", item="WALK OLD PLATE",
                                           vendor_new="WALK LEDGER VENDOR", bill="9000", implant_status="paid"))
    post("/finance/surgery/backfill", dict(patient="WALKTEST OLDCREDIMP", payer="ayushman", admit_date="2025-08-02", item="WALK OLD NAIL",
                                           vendor_new="WALK LEDGER VENDOR", bill="8000", implant_status="pending"))
    lv = q1("SELECT id FROM surg_vendor WHERE name='WALK LEDGER VENDOR'")[0]
    rows, bal, waiting, unas = sc.vendor_ledger(db(), lv)
    check("R2 an old case's implant stays out of the vendor's balance and the awaiting-cheque list (settled before the register)",
          bal == 0 and not rows and not waiting)
    pid = q1("SELECT id FROM surg_case WHERE patient='WALKTEST PLANNED'")[0]
    r = get("/finance/surgery/case/%d" % pid)
    check("R3 on a case with nothing stored, neither status chip is ticked", b"name=money_status value='pending' checked" not in r.data
          and b"name=implant_status value='pending' checked" not in r.data)
    post("/finance/surgery/case/%d/status" % pid, dict(due="5000"))
    check("R3 saving only the amount due leaves the hospital money unset (the case is not counted as money pending)",
          tuple(q1("SELECT money_status, due_p FROM surg_case WHERE id=?", (pid,))) == ("", 500000)
          and b"WALKTEST PLANNED" not in get("/finance/surgery?money=pending").data)
    as_("shavez")
    post("/finance/surgery/case/%d/edit" % cid, dict(insurer="+", insurer_new=""))
    check("R4 '+ add a name' saved with the box empty keeps the case's TPA", q1("SELECT insurer FROM surg_case WHERE id=?", (cid,))[0] == "WALK STAR HEALTH")
    for qq in ("+91 98765" " 43210", "09876543210"):
        r = cl.post("/finance/surgery", data=dict(q=qq))
        check("R1 [round 2] a phone typed as %s is found" % qq, b"WALKTEST MOBILE" in r.data)
    r = get("/finance/surgery/new?cid=WALK9901&name=WALKTEST%20RAMESH&err=source")
    check("R1 [round 2] after a refused save the mobile box is left empty to be written again (never filled from elsewhere)",
          b"(write it again)" in r.data and b"value='90000" b" 11111'" not in r.data)
    r = get("/finance/surgery?pt=planned&open=%d" % cid)
    check("R1 [round 2] a case opened from a search the address no longer carries is still on the page, open", rowblock(r.data, cid) is not None
          and (b"id='c%d' data-id='%d' open>" % (cid, cid)) in r.data)
    r = cl.post("/finance/surgery", data=dict(q="X90000111"))
    check("R5 a search with letters in it is never read as a phone (the mirror's patient is not pulled in)", b"WALKTEST RAMESH" not in r.data)
    as_("manoj")
    sid = q1("SELECT id FROM surg_source WHERE name='WALK REFERRER'")[0]
    post("/finance/surgery/settings/source", dict(do="hide", id=str(sid)))
    as_("shavez")
    post("/finance/surgery/new", dict(patient="WALKTEST HIDDENSRC", payer="cash", source_new="WALK REFERRER"))
    check("R6 Shavez writing a source Dr Manoj took off the list: the case takes it, the list does not bring it back",
          q1("SELECT source_id FROM surg_case WHERE patient='WALKTEST HIDDENSRC'")[0] == sid
          and q1("SELECT hidden FROM surg_source WHERE id=?", (sid,))[0] != "")
    bads = ("https://evil.example/x", "//evil.example/x", "/finance/surgery/../portal", "/finance/surgery\\x", "/finance/surgery?x=1\r\nSet-Cookie: a=b",
            "/finance/surgeryX", "/portal")
    ok = True
    for b in bads:
        r = post("/finance/surgery/case/%d/status" % cid, dict(implant_status="raised", ret=b))
        ok = ok and r.headers["Location"].startswith("/finance/surgery/case/%d?" % cid)
    check("R7 a 'ret' to another site, another page, with '..', a backslash or a line break is never followed", ok)


try:
    section_r()
except Exception as e:                       # noqa: BLE001
    check("R the review's section ran to its end (%s: %s)" % (type(e).__name__, str(e)[:120]), False)


# ---- K S681 (IPD kits 2 and 3): papers as thumbnails, each implant's payment, assistants; the bill and the share, both ways
def section_k():
    as_("shavez")
    cid = q1("SELECT id FROM surg_case WHERE patient='WALKTEST MOBILE'")[0]
    for kind, blob in (("fir", PDF + b"k-fir"), ("lama", b"\xff\xd8\xff\xe0 walk k lama")):
        cl.post("/finance/surgery/api/case/%d/paper/%s" % (cid, kind), data={"file": (io.BytesIO(blob), "k.bin")}, content_type="multipart/form-data")
    pf = q1("SELECT id FROM surg_paper WHERE case_id=? AND kind='fir'", (cid,))
    pl = q1("SELECT id FROM surg_paper WHERE case_id=? AND kind='lama'", (cid,))
    check("K1 the new kinds are filed: police FIR copy (a PDF), LAMA (a photo)", pf and pl)
    r = get("/finance/surgery/case/%d" % cid)
    check("K1 each paper is a thumbnail that opens large -- a photo shows itself, a PDF a PDF tile -- with its name",
          (b"<a class='thumb' href='/finance/surgery/paper/%d' target=_blank><img src='/finance/surgery/paper/%d'" % (pl[0], pl[0])) in r.data
          and (b"<a class='thumb' href='/finance/surgery/paper/%d' target=_blank><span class='pdf'>PDF</span>" % pf[0]) in r.data
          and b"<span class='pw'>Police FIR copy</span>" in r.data)
    check("K1 the papers still missing show as dashed tiles that go to the scanner", b"<a class='thumb miss' href='/finance/surgery/case/%d/scan/" % cid in r.data)
    r = post("/finance/surgery/void", dict(kind="paper", id=str(pl[0]), back="/finance/surgery/case/%d" % cid))
    check("K2 Delete on a thumbnail without a tapped reason is refused", "err=why" in r.headers["Location"]
          and q1("SELECT voided_at FROM surg_paper WHERE id=?", (pl[0],))[0] == "")
    post("/finance/surgery/void", dict(kind="paper", id=str(pl[0]), why="case", back="/finance/surgery/case/%d" % cid))
    check("K2 ...with a reason it goes, kept in the record with the reason", q1("SELECT void_why FROM surg_paper WHERE id=?", (pl[0],))[0] == "case")
    # each implant's payment
    post("/finance/surgery/case/%d/implant" % cid, dict(vendor_new="WALK K VENDOR", item="WALK K NAIL", qty="1", bill="20000", bill_to="patient"))
    post("/finance/surgery/case/%d/implant" % cid, dict(vendor_new="WALK K VENDOR", item="WALK K SCREWS", qty="4", bill="4000", bill_to="patient"))
    i1, i2 = [r_[0] for r_ in db().execute("SELECT id FROM surg_implant WHERE case_id=? AND voided_at='' ORDER BY id", (cid,)).fetchall()][-2:]
    post("/finance/surgery/case/%d/implant/%d/pay" % (cid, i1), dict(pay_status="paid"))
    post("/finance/surgery/case/%d/implant/%d/pay" % (cid, i2), dict(pay_status="cheque"))
    check("K3 each implant has its own step; the case's implant payment follows the least advanced (paid + cheque -> cheque received)",
          q1("SELECT pay_status FROM surg_implant WHERE id=?", (i1,))[0] == "paid" and q1("SELECT implant_status FROM surg_case WHERE id=?", (cid,))[0] == "cheque")
    post("/finance/surgery/void", dict(kind="implant", id=str(i2), why="wrong", back="/finance/surgery/case/%d" % cid))
    cz = q1("SELECT id FROM surg_case WHERE patient='WALKTEST NOIMPLANT'")[0]
    post("/finance/surgery/case/%d/implant" % cz, dict(vendor_new="WALK K VENDOR", item="WALK Z", qty="1", bill="100", bill_to="doctor"))
    iz = q1("SELECT id FROM surg_implant WHERE case_id=?", (cz,))[0]
    post("/finance/surgery/case/%d/implant/%d/pay" % (cz, iz), dict(pay_status="raised"))
    post("/finance/surgery/void", dict(kind="implant", id=str(iz), why="wrong", back="/finance/surgery/case/%d" % cz))
    check("K3 [review] every implant removed: the case's step is unset again", q1("SELECT implant_status FROM surg_case WHERE id=?", (cz,))[0] == "")
    check("K3 an implant removed: the case follows the ones still standing (paid)", q1("SELECT implant_status FROM surg_case WHERE id=?", (cid,))[0] == "paid")
    r = post("/finance/surgery/case/%d/implant/%d/pay" % (cid, i1), dict(pay_status="bogus"))
    check("K3 a step not on the list is refused", "err=status" in r.headers["Location"])
    other = q1("SELECT id FROM surg_case WHERE patient='WALKTEST CONS'")[0]
    r = post("/finance/surgery/case/%d/implant/%d/pay" % (other, i1), dict(pay_status="raised"))
    check("K3 an implant of another case is never moved from this one", "err=gone" in r.headers["Location"]
          and q1("SELECT pay_status FROM surg_implant WHERE id=?", (i1,))[0] == "paid")
    r = get("/finance/surgery/case/%d" % cid)
    check("K3 the implants table shows each implant's step as a choice", b"/implant/%d/pay" % i1 in r.data and b"<th>Implant payment</th>" in r.data)
    con = db()
    con.execute("UPDATE surg_implant SET pay_status='' WHERE case_id=(SELECT id FROM surg_case WHERE patient='WALKTEST OLD ONE')")
    con.commit(); con.close()
    sc._schema_done = False
    get("/finance/surgery")
    o1 = q1("SELECT id FROM surg_case WHERE patient='WALKTEST OLD ONE'")[0]
    check("K3 [review] an implant from before S681 (no step) takes its case's step once, on the first request (cheque received)",
          q1("SELECT pay_status FROM surg_implant WHERE case_id=?", (o1,))[0] == "cheque")
    check("K3 an old case's implant carries the step it was entered with", q1("SELECT pay_status FROM surg_implant WHERE case_id=?", (o1,))[0] == "cheque")
    r = post("/finance/surgery/case/%d/status" % cid, dict(implant_status="raised"))
    check("K3 [review] with implants on the case, a step for the whole case is refused (each implant carries its own) -- nothing moves",
          "err=status" in r.headers["Location"] and q1("SELECT implant_status FROM surg_case WHERE id=?", (cid,))[0] == "paid"
          and q1("SELECT pay_status FROM surg_implant WHERE id=?", (i1,))[0] == "paid")
    post("/finance/surgery/case/%d/status" % cid, dict(implant_status="na"))
    r = get("/finance/surgery/case/%d" % cid)
    check("K3 [review] 'not needed' can be undone: the case offers 'Follow the implants again'", b"Follow the implants again" in r.data
          and q1("SELECT implant_status FROM surg_case WHERE id=?", (cid,))[0] == "na")
    post("/finance/surgery/case/%d/status" % cid, dict(implant_status="follow"))
    check("K3 [review] ...and following again takes the implants' step (paid)", q1("SELECT implant_status FROM surg_case WHERE id=?", (cid,))[0] == "paid")
    post("/finance/surgery/case/%d/implant" % cid, dict(vendor_id=str(q1("SELECT vendor_id FROM surg_implant WHERE id=?", (i1,))[0]), item="WALK K PLATE",
                                                     qty="1", bill="6000", bill_to="patient"))
    i3 = q1("SELECT id FROM surg_implant WHERE case_id=? AND item='WALK K PLATE'", (cid,))[0]
    check("K3 [review] a new implant moves the case back to its step (not raised yet)", q1("SELECT implant_status FROM surg_case WHERE id=?", (cid,))[0] == "pending")
    post("/finance/surgery/case/%d/implant/%d/pay" % (cid, i3), dict(pay_status="paid"))
    post("/finance/surgery/case/%d/implant/%d/pay" % (cid, i1), dict(pay_status="paid"))
    r = get("/finance/surgery/case/%d" % cid)
    check("K2 [screens] a paper's Delete offers its own reasons (wrong patient, wrong paper, unclear / blurred, scanned twice)",
          b"name=why value='blurred'> unclear / blurred" in r.data and b"name=why value='paper'> wrong paper" in r.data)
    pb = q1("SELECT id FROM surg_paper WHERE case_id=? AND kind='fir' AND voided_at=''", (cid,))[0]
    post("/finance/surgery/void", dict(kind="paper", id=str(pb), why="blurred", back="/finance/surgery/case/%d" % cid))
    check("K2 [screens] ...and 'unclear / blurred' is taken", q1("SELECT void_why FROM surg_paper WHERE id=?", (pb,))[0] == "blurred")
    check("K3 [screens] on a phone each implant is a card (labels beside each figure)", b"table.itab td::before{content:attr(data-l)" in r.data
          and b"data-l='Implant payment'" in r.data)
    # assistants
    post("/finance/surgery/case/%d/assistant" % cid, dict(role="technician", name="WALK TECH RAKESH", pay="500"))
    a1 = q1("SELECT * FROM surg_assistant WHERE case_id=? AND role='technician'", (cid,))
    check("K4 Shavez writes the technician; a pay he sends is never taken", a1 and a1["name"] == "WALK TECH RAKESH" and a1["pay_p"] is None)
    r = post("/finance/surgery/case/%d/assistant" % cid, dict(role="nurse", name="X"))
    check("K4 a role other than technician / assisting doctor is refused", "err=role" in r.headers["Location"])
    as_("manoj")
    post("/finance/surgery/case/%d/assistant" % cid, dict(role="assisting", name="WALK DR VERMA", pay="2000"))
    check("K4 Dr Manoj writes the assisting doctor with what he was paid", q1("SELECT pay_p FROM surg_assistant WHERE name='WALK DR VERMA'")[0] == 200000)
    r = get("/finance/surgery/case/%d" % cid)
    check("K4 ...and sees it, marked 'you only'", b"WALK DR VERMA" in r.data and b"paid \xe2\x82\xb9 2,000" in r.data)
    as_("shavez")
    r = get("/finance/surgery/case/%d?frag=1" % cid)
    check("K4 Shavez sees both names, never the pay nor the pay box", b"WALK DR VERMA" in r.data and b"WALK TECH RAKESH" in r.data
          and b"2,000" not in r.data and b"name=pay " not in r.data)
    a2 = q1("SELECT id FROM surg_assistant WHERE name='WALK DR VERMA'")[0]
    r = post("/finance/surgery/void", dict(kind="assistant", id=str(a2), why="wrong", back="/finance/surgery/case/%d" % cid))
    check("K4 [review] Shavez cannot remove a line that carries Dr Manoj's pay", "err=gone" in r.headers["Location"]
          and q1("SELECT voided_at FROM surg_assistant WHERE id=?", (a2,))[0] == "")
    post("/finance/surgery/void", dict(kind="assistant", id=str(a1["id"]), why="wrong", back="/finance/surgery/case/%d" % cid))
    check("K4 a wrong assistant line is removed with its reason", q1("SELECT void_why FROM surg_assistant WHERE id=?", (a1["id"],))[0] == "wrong")
    # ---- kit 3: the bill and the share
    c3 = q1("SELECT id FROM surg_case WHERE patient='WALKTEST NOIMPLANT'")[0]          # cash, admitted 13-Jan, surgery 14-Jan
    post("/finance/surgery/case/%d/edit" % c3, dict(discharge_date="2099-01-15"))
    r = get("/finance/surgery/case/%d" % c3)
    check("K5 the cash bill form: the statement's four heads, then his formula's fields; admission and nursing prefilled (Rs 1,200; 2 days x Rs 500)",
          all((b"name=b_%s " % k.encode()) in r.data for k in ("visit", "misc", "bed", "surgery", "total", "discount", "admission", "nursing", "otherdocs", "xraypath", "misc2"))
          and b"name=b_admission class='in s amt' inputmode=decimal value='1200'" in r.data and b"name=b_nursing class='in s amt' inputmode=decimal value='1000'" in r.data)
    t, n = sc.next_step(db(), q1("SELECT * FROM surg_case WHERE id=?", (cid,)), 0, miss=[])
    check("K5 a discharged case with its implant and papers and no bill: Next says enter the hospital's bill (section 4)", n == 4 and "bill" in t)
    r = post("/finance/surgery/case/%d/bill" % c3, dict(b_visit="1000", b_misc="abc"))
    check("K6 an amount that is not a number is refused and nothing is saved", "err=amount" in r.headers["Location"]
          and q1("SELECT COUNT(*) FROM surg_bill WHERE case_id=?", (c3,))[0] == 0)
    post("/finance/surgery/case/%d/bill" % c3, dict(bill_no="WALK992", bill_date="2099-01-15", b_visit="1000", b_misc="340", b_bed="3100", b_surgery="",
                                                     b_total="9000", b_discount="500", b_admission="1200", b_nursing="1000", b_otherdocs="", b_xraypath="800", b_misc2=""))
    r = get("/finance/surgery/case/%d" % c3)
    check("K7 the hospital's way: 1,000 + 340 + 3,100 = 4,440, the share 50% = 2,220 (as the September statement works it)",
          b"\xe2\x82\xb9 4,440" in r.data and b"\xe2\x82\xb9 2,220" in r.data)
    m = sc.bill_math(db(), q1("SELECT * FROM surg_case WHERE id=?", (c3,)), sc.bill_of(db(), c3)[1])
    check("K7 his formula (cash): 9,000 - 500 discount - 1,200 admission - 1,000 nursing - 800 X-ray = 5,500; his % not set, so no share yet",
          m["mine"] == 550000 and m["mine_share"] is None)
    check("K7 [review] Shavez sees the hospital's way only -- his formula and his % are Dr Manoj's", b"Your formula" not in r.data and b"% not set" not in r.data
          and b"How your formula is worked out" not in r.data)
    post("/finance/surgery/case/%d/bill" % c3, dict(b_visit="1000", b_misc="340", b_bed="3100", b_total="9000", b_discount="500", b_admission="1200",
                                                     b_nursing="1000", b_xraypath="800"))
    check("K8 a second save replaces the bill: one live row, the old one kept voided 'replaced'",
          q1("SELECT COUNT(*) FROM surg_bill WHERE case_id=? AND voided_at=''", (c3,))[0] == 1
          and q1("SELECT void_why FROM surg_bill WHERE case_id=? AND voided_at<>''", (c3,))[0] == "replaced")
    as_("manoj")
    post("/finance/surgery/settings", dict(admission="1200", nursing="500", share="40", hshare="50"))
    r = get("/finance/surgery/case/%d" % c3)
    check("K9 with his % set (40): his share 2,200 beside the hospital's 2,220, the difference said, and both offered as the amount due",
          b"\xe2\x82\xb9 2,200" in r.data and b"The hospital's way is \xe2\x82\xb9 20 above your formula." in r.data
          and b"Use \xe2\x82\xb9 2,220 as the amount due" in r.data and b"Use \xe2\x82\xb9 2,200 as the amount due" in r.data)
    post("/finance/surgery/case/%d/status" % c3, dict(due="2220"))
    check("K9 'Use as the amount due' writes it", q1("SELECT due_p FROM surg_case WHERE id=?", (c3,))[0] == 222000)
    as_("shavez")
    r = get("/finance/surgery/case/%d" % c3)
    check("K9 [review] Shavez sees the bill and the hospital's way (2,220), never his formula's 2,200 nor 'Use as the amount due'",
          b"\xe2\x82\xb9 2,220" in r.data and b"\xe2\x82\xb9 2,200" not in r.data and b"as the amount due" not in r.data)
    r = post("/finance/surgery/case/%d/bill" % c3, dict(b_visit="", b_total=""))
    check("K8 [review] a bill saved with every box blank is refused, the bill kept", "err=billblank" in r.headers["Location"]
          and q1("SELECT COUNT(*) FROM surg_bill WHERE case_id=? AND voided_at=''", (c3,))[0] == 1)
    con = db()
    con.execute("INSERT INTO surg_bill (case_id, vals, by_whom, at) VALUES (?, '{}', 'walk', '2099-01-15 10:00:00')", (c3,))
    con.commit(); con.close()
    post("/finance/surgery/case/%d/bill" % c3, dict(b_visit="1000", b_misc="340", b_bed="3100", b_total="9000", b_discount="500", b_admission="1200",
                                                     b_nursing="1000", b_xraypath="800"))
    check("K8 [review] a save voids EVERY live bill of the case (two saves at once leave one)",
          q1("SELECT COUNT(*) FROM surg_bill WHERE case_id=? AND voided_at=''", (c3,))[0] == 1)
    # credit: the remainder uses the implant's actual cost -- Dr Manoj's alone
    cr = q1("SELECT id FROM surg_case WHERE patient='WALKTEST RAMESH'")[0]      # Ayushman; implant bill 50,000, actually due 40,000
    r = get("/finance/surgery/case/%d" % cr)
    check("K10 the credit bill form asks billed, sanctioned, received and the deductions (anaesthesia ... MRI, other doctors)",
          all((b"name=b_%s " % k.encode()) in r.data for k in ("billed", "sanctioned", "received", "anaesthesia", "medicines", "pathology", "xray", "ct", "mri", "otherdocs")))
    post("/finance/surgery/case/%d/bill" % cr, dict(b_visit="4800", b_misc="700", b_bed="18000", b_surgery="6000", b_billed="90000", b_sanctioned="80000",
                                                     b_received="75000", b_anaesthesia="3000", b_medicines="5000"))
    r = get("/finance/surgery/case/%d" % cr)
    check("K10 Shavez: the hospital's way (29,500 -> 14,750) but not his formula's remainder, which uses the implant's actual cost",
          b"\xe2\x82\xb9 29,500" in r.data and b"\xe2\x82\xb9 14,750" in r.data and b"Your formula" not in r.data and b"40,000" not in r.data
          and b"Implant paid" not in r.data)
    as_("manoj")
    m = sc.bill_math(db(), q1("SELECT * FROM surg_case WHERE id=?", (cr,)), sc.bill_of(db(), cr)[1])
    r = get("/finance/surgery/case/%d" % cr)
    check("K10 Dr Manoj: received 75,000 - 3,000 - 5,000 - the implant paid 40,000 = 27,000; at 40% = 10,800, marked 'you only'",
          m["mine"] == 2700000 and m["mine_share"] == 1080000 and b"\xe2\x82\xb9 10,800" in r.data and b"Your formula <span class='you'>you only</span>" in r.data)
    # package: the assistants' pay is his alone, and survives Shavez's save
    pk = q1("SELECT id FROM surg_case WHERE patient='WALKTEST PKG'")[0]
    r = get("/finance/surgery/case/%d" % pk)
    check("K11 the package form for Dr Manoj has the assistants' line; the implant prefilled from the vendors' bills (52,000)",
          b"name=b_assistants" in r.data and b"name=b_implant class='in s amt' inputmode=decimal value='52000'" in r.data)
    post("/finance/surgery/case/%d/bill" % pk, dict(b_package="100000", b_admission="1200", b_implant="52000", b_assistants="3000"))
    as_("shavez")
    r = get("/finance/surgery/case/%d" % pk)
    check("K11 Shavez's package form has no assistants' line", b"name=b_assistants" not in r.data and b"name=b_package" in r.data)
    post("/finance/surgery/case/%d/bill" % pk, dict(b_package="100000", b_admission="1200", b_implant="52000", b_medicines="4000", b_assistants="1"))
    v = sc.bill_of(db(), pk)[1]
    check("K11 Shavez's save keeps Dr Manoj's assistants figure and never takes his own", v.get("assistants") == 300000 and v.get("medicines") == 400000)
    check("K11 the history names the bill", b"hospital bill saved" in get("/finance/surgery/case/%d" % pk).data)
    pk2 = q1("SELECT id FROM surg_case WHERE patient='WALKTEST PKG2'")[0]
    post("/finance/surgery/case/%d/bill" % pk2, dict(b_package="50000", b_assistants="999"))
    check("K11 [mutant] on a package with no figure of Dr Manoj's, Shavez's assistants figure is still never taken",
          "assistants" not in sc.bill_of(db(), pk2)[1] and sc.bill_of(db(), pk2)[1].get("package") == 5000000)
    as_("manoj")
    r = post("/finance/surgery/settings", dict(admission="1200", nursing="500", share="", hshare="150"))
    check("K12 Settings: the statement's % above 100 is refused", "err=share" in r.headers["Location"] and sc.hospital_share_pct(db()) == 50)
    post("/finance/surgery/settings", dict(admission="1200", nursing="500", share="", hshare="50"))
    check("K12 ...and Settings shows it (50)", b"name=hshare class='in s amt' inputmode=decimal value='50'" in get("/finance/surgery/settings").data)


try:
    section_k()
except Exception as e:                       # noqa: BLE001
    check("K the IPD kits 2+3 section ran to its end (%s: %s)" % (type(e).__name__, str(e)[:120]), False)


# ---- S the record, T a file outside the folder
check("S every write left an audit line", q1("SELECT COUNT(*) FROM audit_log WHERE table_name LIKE 'surg_%'")[0] >= 10)
con = db(); con.execute("UPDATE surg_paper SET path='/etc/passwd' WHERE id=?", (p1["id"],)); con.commit(); con.close()
check("T a paper whose path leaves the papers folder is never served", get("/finance/surgery/paper/%d" % p1["id"]).status_code == 404)
r = get("/finance/surgery/case/999999")
check("T an unknown case is a plain 'not found'", r.status_code == 404)

shutil.rmtree(TMP, ignore_errors=True)
finish()
