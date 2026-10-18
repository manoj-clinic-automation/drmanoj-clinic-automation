#!/usr/bin/env python3
"""walk_s579.py -- the walk for surgery_cases.py (kit S579). Runs the REAL module in a small Flask app against a database:
either a made-up one (default), or a COPY of the live finance.db (--db /root/finance/finance.db: copied to a temp folder first;
the live file is never opened for writing). Every row the walk writes is made up and dated 2099; papers go to a temp folder.
    python3 walk_s579.py [path/to/surgery_cases.py] [--db /path/to/finance.db]
Prints one line per check and a count. Exit 0 only if every check is green."""
import importlib.util, io, json, os, re, shutil, sqlite3, sys, tempfile

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
    print("\nwalk_s579: %d of %d green" % (g, max(len(R), 1)))
    sys.exit(0 if R and g == len(R) else 1)


TMP = tempfile.mkdtemp(prefix="walk579_")
os.environ["SURGERY_PAPER_DIR"] = os.path.join(TMP, "papers")
os.environ["SURGERY_NOW"] = "2099-01-15T10:00:00"
DB = os.path.join(TMP, "finance.db")
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
    spec = importlib.util.spec_from_file_location("surgery_cases_walk", MOD)
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
check("A the doctor's very first visit opens the list, with the money columns", r.status_code == 200 and b"Due from hospital" in r.data)
as_("nobody")
r = get("/finance/surgery")
check("A a login not on the unit is refused (403)", r.status_code == 403)
check("A the unit and its two logins were made on the first request",
      q1("SELECT COUNT(*) FROM unit_role WHERE unit='surgery' AND active=1")[0] == 2 and q1("SELECT code FROM business_unit WHERE code='surgery'"))
as_("shavez")
r = get("/finance/surgery")
check("A Shavez sees the list WITHOUT the money columns", r.status_code == 200 and b"Due from hospital" not in r.data)

# ---- B/C new cases (Shavez)
r = post("/finance/surgery/new", dict(patient="WALKTEST RAMESH", clinic_id="WALK9901", payer="ayushman", hospital="WALK HOSPITAL",
                                       procedure_text="PFN right", surgery_date="2099-01-10"))
c1 = q1("SELECT * FROM surg_case WHERE patient='WALKTEST RAMESH'")
check("B Shavez makes an Ayushman case: S-2099-0001, stage 'pre-approval applied'", r.status_code == 302 and c1 and c1["case_no"] == "S-2099-0001"
      and c1["stage"] == "applied")
r = post("/finance/surgery/new", dict(patient="WALKTEST SITA", payer="cash", hospital="WALK HOSPITAL", surgery_date="2099-01-11"))
c2 = q1("SELECT * FROM surg_case WHERE patient='WALKTEST SITA'")
check("C a cash case: S-2099-0002, stage planned", c2 and c2["case_no"] == "S-2099-0002" and c2["stage"] == "planned")
r = post("/finance/surgery/new", dict(patient="WALKTEST X", payer="bogus"))
check("C a payer that is not one of the four is refused", r.status_code == 302 and "err=payer" in r.headers["Location"])
r = post("/finance/surgery/new", dict(patient="", payer="cash"))
check("C a case without a name is refused", "err=patient" in r.headers["Location"])
# numbering under a race: a row already holding the next number
con = db(); con.execute("INSERT INTO surg_case (case_no, patient, payer) VALUES ('S-2099-0003','WALKTEST RACE','cash')"); con.commit(); con.close()
post("/finance/surgery/new", dict(patient="WALKTEST AFTER", payer="cashless", insurer="WALK TPA"))
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
check("F the case page lists ten kinds of paper incl. MLC and police memo, and what is still missing",
      b"Medicolegal (MLC) papers" in r.data and b"Police memo" in r.data and b"missing" in r.data and r.data.count(b"Scan / upload") == 10)

# ---- G implants
r = post("/finance/surgery/case/%d/implant" % cid2, dict(vendor_new="WALK ORTHO VENDOR", item="WALK PLATE", qty="1", bill="30000",
                                                           bill_to="doctor", charge="36000", payable="1"))
i2 = q1("SELECT * FROM surg_implant WHERE case_id=?", (cid2,))
check("G Shavez adds an implant with a new vendor; the money only Dr Manoj writes is NOT taken from him",
      i2 and i2["bill_p"] == 3000000 and i2["charge_p"] is None and i2["payable_p"] is None)
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
rid = q1("SELECT id FROM surg_receipt")[0]
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
check("M Shavez's case page shows no money", b"Money from the hospital" not in r.data and b"Actually due to vendor" not in r.data)
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
r = get("/finance/surgery?t=credit&show=all")
check("R the Credit tab shows the Ayushman and cashless cases, not the cash one", b"WALKTEST RAMESH" in r.data and b"WALKTEST AFTER" in r.data
      and b"WALKTEST SITA" not in r.data)
r = get("/finance/surgery?t=cash&show=all")
check("R the Cash tab shows only cash cases", b"WALKTEST SITA" in r.data and b"WALKTEST RAMESH" not in r.data)
r = get("/finance/surgery?t=ayushman&show=all")
check("R the Ayushman tab shows only Ayushman", b"WALKTEST RAMESH" in r.data and b"WALKTEST AFTER" not in r.data)

# ---- S the record, T a file outside the folder
check("S every write left an audit line", q1("SELECT COUNT(*) FROM audit_log WHERE table_name LIKE 'surg_%'")[0] >= 10)
con = db(); con.execute("UPDATE surg_paper SET path='/etc/passwd' WHERE id=?", (p1["id"],)); con.commit(); con.close()
check("T a paper whose path leaves the papers folder is never served", get("/finance/surgery/paper/%d" % p1["id"]).status_code == 404)
r = get("/finance/surgery/case/999999")
check("T an unknown case is a plain 'not found'", r.status_code == 404)

shutil.rmtree(TMP, ignore_errors=True)
finish()
