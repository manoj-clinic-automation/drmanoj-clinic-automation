# walk_s882.py -- S882's walk on a MADE-UP root (made-up Drive folder, made-up papers, made-up register; no real name,
# no real number -- F-185). Usage: python3 walk_s882.py <kit dir> <scratch dir>. Last line: "WALK n/N".
import hashlib, json, os, re, shutil, sqlite3, stat, subprocess, sys

KIT, SCR = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]   # F-1441
shutil.rmtree(SCR, ignore_errors=True)
FIN = os.path.join(SCR, "finance"); STUB = os.path.join(SCR, "stub"); os.makedirs(os.path.join(FIN, "_off"))
os.environ.update(FIN_DIR=FIN, FINANCE_DB=os.path.join(FIN, "finance.db"), PAYMENT_RECORDS_STUB=STUB,
                  PAYMENT_RECORDS_DIR=os.path.join(FIN, "payment_records"), PAYMENT_RECORDS_STATE=os.path.join(FIN, "pr.state.json"))
for f in ("payment_records.py", "payment_ledgers.py"):
    if os.path.exists(os.path.join(KIT, f)):
        shutil.copy(os.path.join(KIT, f), FIN)
sys.path.insert(0, FIN)
R = []
MOB = "%d %d" % (9876 * 10 + 5, 4321 * 10)                         # a made-up mobile, built at run time (F-185)
def ok(name, cond):
    R.append((name, bool(cond)))
    if not cond:
        print("FAIL", name)

def pdf(path, lines):
    content = "BT /F1 10 Tf 40 800 Td 12 TL " + " ".join("(%s) '" % l.replace("\\", "").replace("(", "[").replace(")", "]") for l in lines) + " ET"
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            "<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content), "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offs = "%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += "%d 0 obj\n%s\nendobj\n" % (i, o)
    x = len(out)
    out += "xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + "".join("%010d 00000 n \n" % o for o in offs)
    out += "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="latin-1").write(out)

P = os.path.join(STUB, "Payment Records")
ag = os.path.join(P, "Agilus (NK Pathology)")
pdf(os.path.join(ag, "2026-10-05_Invoice.pdf"), ["TAX INVOICE", "Bill To N K PATHOLOGY", "Patient Name Testone Kumarx", "Rate 1200.00"])
pdf(os.path.join(ag, "2026-10-20_Invoice.pdf"), ["TAX INVOICE", "Bill To N K PATHOLOGY", "Patient Name Zebulon Kumarx", "Grand Total 2,450.50"])
shutil.copy(os.path.join(ag, "2026-10-20_Invoice.pdf"), os.path.join(ag, "2026-10-20_Invoice (1).pdf"))      # saved twice
pdf(os.path.join(ag, "2026-11-04_Invoice.pdf"), ["TAX INVOICE", "Bill To N K PATHOLOGY", "Patient Name Testtwo Kumarx",
    "Mobile " + MOB, "Grand Total 900.00", "Amount Paid 950.00"])
pdf(os.path.join(ag, "2026-11-10_Account.pdf"), ["Account statement", "Closing balance 5,000.00"])               # not an invoice
open(os.path.join(ag, "2026-11-12_Invoice.pdf"), "wb").write(b"%PDF-1.4 locked made-up\n%%EOF\n")          # unreadable (locked/scan)
air = os.path.join(P, "Airtel")
pdf(os.path.join(air, "2026-11-15_AirtelReceipt_PR1.pdf"), ["payment receipt", "Paid amount 3108.42"])
pdf(os.path.join(air, "2026-11-09_1010_Nov2026.pdf"), ["One Airtel Monthly Statement", "Total Amount Payable 3,208.42"])
open(os.path.join(air, "2026-11-09_"), "wb").write(b"\x89PNG fake picture")
pdf(os.path.join(air, "2026-11-20_AirtelReceipt_REFUSE.pdf"), ["payment receipt", "Paid amount 100.00"])    # Drive refuses it
dz = os.path.join(P, "Docterz EMR"); os.makedirs(dz)
open(os.path.join(dz, "2026-09-01_clinical data report.csv"), "w").write("made,up\n")
open(os.path.join(dz, "2026-09-01_Docterz_Blue.png"), "wb").write(b"\x89PNG")
mo = os.path.join(P, "MyOperator")
pdf(os.path.join(mo, "2026-09-03_10000000000001.pdf"), ["INR 0.00", "Monthly statement", "Statement period", "03 Aug 2026 to 02 Sep 2026",
    "This Month's Charges", "(All charges from this month without taxes)", "99.50", "Total Amount Payable This Month",
    "(Final amount payable including taxes)", "INR 0.00", "Pre-paid Balance", "(Pre-paid balance after current month's deduction)", "12345.67"])
pdf(os.path.join(mo, "2026-05-20_c991e48d.pdf"), ["Tax Invoice", "Invoice No N9905-0001", "Total 2,12,400.00"])
pdf(os.path.join(P, "eatsure.com", "2025-01-15_EatSure.pdf"), ["invoice", "Total 450"])
pdf(os.path.join(P, "swiggy.in", "2026-11-01_order_invoice.pdf"), ["Tax invoice", "Total 300"])
pdf(os.path.join(P, "Insurance", "2026-07-15_Policy-461.pdf"), ["Policy Schedule"])
pdf(os.path.join(P, "Insurance", "2026-04-27_PF_COLLECTIONRECEIPT_7.pdf"), ["ADJUSTMENT VOUCHER", "Received with thanks", "Total = 3805.00"])
pdf(os.path.join(P, "dellstore.com", "2025-09-09_invoice.pdf"), ["Tax Invoice cum Delivery Challan", "Grand Total 12,999.00"])

con = sqlite3.connect(os.environ["FINANCE_DB"]); con.row_factory = sqlite3.Row
con.executescript("""CREATE TABLE payment_register (row_no INTEGER PRIMARY KEY, date_iso TEXT, vendor TEXT, description TEXT, amount_paise INTEGER, in_drive INTEGER);
INSERT INTO payment_register VALUES (1,'2026-10-05','Agilus (NK Pathology)','Invoice for N K PATHOLOGY',120000,1);
INSERT INTO payment_register VALUES (2,'2026-10-20','Agilus (NK Pathology)','Invoice for N K PATHOLOGY',NULL,1);
INSERT INTO payment_register VALUES (3,'2026-11-04','Agilus (NK Pathology)','Invoice for N K PATHOLOGY',NULL,1);
INSERT INTO payment_register VALUES (4,'2026-05-20','MyOperator','AB12CD: Your invoice (N9905-0001) has been generated',21240000,1);
INSERT INTO payment_register VALUES (5,'2026-05-20','MyOperator','AB12CD: Your payment has been successfully received',21240000,1);
INSERT INTO payment_register VALUES (8,'2026-05-20','MyOperator','AB12CD: Your payment has been successfully received',21240000,1);
INSERT INTO payment_register VALUES (6,'2026-09-03','MyOperator','[NOT A PAYMENT] Statement From MyOperator',0,1);
INSERT INTO payment_register VALUES (9,'2026-05-21','MyOperator','AB12CD: Your payment for invoice (N9905-0001) has been successfully received',100,1);
INSERT INTO payment_register VALUES (7,'2025-08-23','MyOperator','Your MyOperator payment is successfully received',500000,0);""")
con.commit()

try:
    import payment_records as pr
except Exception as e:                                                  # noqa: BLE001
    print("FAIL import payment_records: %s" % e); print("WALK 0/55"); sys.exit(0)

# W1 the fetch (stub)
st = pr.fetch(con)
ok("W1 fetch ok", st["ok"] and st["folders"] == 1 and st["vendors"] == 8)
ok("W1 papers wanted 12, copied 11, Drive refused 1 (the run went on)", st["wanted"] == 12 and st["fetched"] == 11 and st["failed"] == 1)
sk = st["skipped"]
ok("W1 Airtel bill left", sk.get("Airtel bill or statement (its receipt is the payment)") == 1)
ok("W1 report/export/picture left (csv, png x2)", sk.get("not a payment paper (report, export or picture)") == 2)
ok("W1 the unnamed picture left as not a PDF", sk.get("not a PDF") == 1)
ok("W1 senders not on the list left (eatsure, a new swiggy)", sk.get("a sender not on the clinic's list (personal or new) -- left in Drive") == 2)
ok("W1 policy paper left", sk.get("policy paper, not a receipt") == 1)
# W2 idempotent
st2 = pr.fetch(con)
ok("W2 second fetch copies nothing new (the refused one tried again)", st2["ok"] and st2["fetched"] == 0 and st2["already"] == 11 and st2["failed"] == 1)
pr._state_write(st2)
ok("W2 one row per file", con.execute("SELECT COUNT(*) FROM payment_record_file").fetchone()[0] == 11)
# W3 nothing but PDFs, private
held = [os.path.join(d, f) for d, _x, fs in os.walk(os.environ["PAYMENT_RECORDS_DIR"]) for f in fs]
ok("W3 only PDFs on the box", held and all(h.lower().endswith(".pdf") for h in held))
ok("W3 files 0600", all(stat.S_IMODE(os.stat(h).st_mode) == 0o600 for h in held))
ok("W3 no .part left", not any(h.endswith(".part") for h in held))
# W4 kinds
k = {r["name"]: r["kind"] for r in con.execute("SELECT name, kind FROM payment_record_file")}
ok("W4 MyOperator statement", k.get("2026-09-03_10000000000001.pdf") == "statement")
ok("W4 MyOperator invoice is an invoice, not a statement", k.get("2026-05-20_c991e48d.pdf") == "invoice")
ok("W4 Airtel receipt", k.get("2026-11-15_AirtelReceipt_PR1.pdf") == "receipt")
ok("W4 Agilus invoice", k.get("2026-10-05_Invoice.pdf") == "invoice")
ok("W4 Agilus account paper is not an invoice", k.get("2026-11-10_Account.pdf") == "paper")
ok("W4 collection receipt", k.get("2026-04-27_PF_COLLECTIONRECEIPT_7.pdf") == "receipt")
# W5 MyOperator ledger
mo_rows = pr.myoperator_rows(con)
stm = [r for r in mo_rows if r["what"].startswith("Monthly statement")]
ok("W5 statement usage 99.50 and balance 12345.67 (read at the copy)", stm and stm[0]["usage"] == 9950 and stm[0]["balance"] == 1234567 and stm[0]["payable"] == 0)
ok("W5 statement period read", stm and "2026-08-03 to 2026-09-02" in stm[0]["what"])
inv = [r for r in mo_rows if r["what"].startswith("Invoice raised")]
ok("W5 invoice with its number and paper", inv and "N9905-0001" in inv[0]["what"] and inv[0]["charged"] == 21240000 and inv[0]["files"])
ok("W5 a payment mail repeated is one payment; a payment quoting the invoice number is a payment", len([r for r in mo_rows if r["what"].startswith("Payment made")]) == 3)
ok("W5 '[NOT A PAYMENT]' rows not in the ledger", not any("NOT A PAYMENT" in r["what"] for r in mo_rows))
ok("W5 running = paid - charged (5,000 + 2,12,400 + 1 - 2,12,400)", mo_rows[-1]["running"] == 500100)
# W6 Agilus ledger
ag_rows = pr.agilus_rows(con)
ok("W6 four invoices (a paper saved twice is one; the account paper is not one; a locked one stays, unfigured)", len(ag_rows) == 4 and ag_rows[3]["amount"] is None and ag_rows[3]["source"] == "")
ok("W6 the mail's figure when the invoice has none and the day has one invoice", ag_rows[0]["amount"] == 120000 and ag_rows[0]["source"] == "the mail")
ok("W6 the invoice's own total first", ag_rows[1]["amount"] == 245050 and ag_rows[1]["source"] == "read from the invoice")
ok("W6 two labelled figures that disagree stay blank (never a guess)", ag_rows[2]["amount"] is None)
ok("W6 running total", ag_rows[-1]["running"] == 365050)
# W7 the masked layout: the newest Agilus paper names a made-up patient, a common surname in every paper, a mobile
lay = pr.masked_layout(con)
ok("W7 no made-up name, no common surname, no mobile in the layout", all(w not in lay for w in ["Testtwo", "Kumarx", "Zebulon"] + MOB.split()))
ok("W7 template words kept", "INVOICE" in lay and "PATHOLOGY" in lay)
ok("W7 Devanagari, accents and single letters are masked", "राम" not in pr.mask_line("Name राम José Q 12") and "9" in pr.mask_line("12") and "Jos" not in pr.mask_line("José"))
# W8 never a guess on a date / next line
ok("W8 a 'Total' heading over a date is no figure", pr.labelled_total("Total\n12-11-2026\n") is None and pr.labelled_total("Total 12-11-2026") is None)
ok("W8 a labelled total still reads", pr.labelled_total("Sub Total 100\nTotal 118.00") == 118.0)
# W9 _place: a name held by another content gets its own name; the bytes are read back
vd = os.path.join(SCR, "place"); os.makedirs(vd)
a1 = pr._place(vd, "x.pdf", b"one", hashlib.sha256(b"one").hexdigest())
a2 = pr._place(vd, "x.pdf", b"two", hashlib.sha256(b"two").hexdigest())
a3 = pr._place(vd, "x.pdf", b"three", hashlib.sha256(b"three").hexdigest())
ok("W9 three contents, three files, each its own bytes", len({a1, a2, a3}) == 3 and open(a3, "rb").read() == b"three" and open(a1, "rb").read() == b"one")
ok("W9 the same content twice is the same file", pr._place(vd, "x.pdf", b"two", hashlib.sha256(b"two").hexdigest()) == a2)
# W10 the live Drive door: records_drive.die() (SystemExit) on one paper and on one folder never stops the run
fake = '''import sys, os, json
API = "https://made-up/files"
def die(m):
    sys.stderr.write(m + "\\n"); sys.exit(2)
def headers():
    return {}
class _R(object):
    def __init__(s, d=None, c=b""):
        s.d, s.content = d, c
    def json(s):
        return s.d
def get(url, params, h, timeout=60):
    import payment_records as pr
    stub = pr._Stub(os.environ["W_STUB"])
    if "alt" in params:
        try:
            return _R(c=stub.media(url.rsplit("/", 1)[1]))
        except Exception:
            die("Drive said 403")
    q = params["q"]
    if "sharedWithMe" in q:
        return _R({"files": stub.roots()})
    fid = q.split("'")[1]
    if "MyOperator" in fid:
        die("Drive said 404")
    return _R({"files": stub.children(fid)})
'''
open(os.path.join(FIN, "records_drive.py"), "w").write(fake)
os.environ["W_STUB"] = STUB
con2 = sqlite3.connect(os.path.join(SCR, "live.db")); con2.row_factory = sqlite3.Row
pr.STUB = ""
pr.STATE = os.path.join(SCR, "live.state.json")
try:
    st4 = pr.fetch(con2)
    ok("W10 the live door: a refused paper and a refused folder are counted, the run ends OK", st4["ok"] and st4["failed"] == 2 and st4["fetched"] == 9)
except BaseException as e:                                              # noqa: BLE001
    ok("W10 the live door stood (%s)" % type(e).__name__, False)
o = subprocess.run([sys.executable, os.path.join(FIN, "payment_records.py"), "fetch"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                   env=dict(os.environ, PAYMENT_RECORDS_STUB="", FINANCE_DB=os.path.join(SCR, "live2.db"), PAYMENT_RECORDS_STATE=os.path.join(SCR, "l2.json"))).stdout.decode()
s2 = json.load(open(os.path.join(SCR, "l2.json")))
ok("W10 the command run writes its state and says OK", s2.get("ok") is True and "OK" in o and "Kumarx" not in o)
pr.STUB = STUB
pr.STATE = os.environ["PAYMENT_RECORDS_STATE"]
# W11 the switch and a missing share
open(os.path.join(FIN, "_off", "ALL_OFF"), "w").close()
o = subprocess.run([sys.executable, os.path.join(FIN, "payment_records.py"), "fetch"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode()
ok("W11 ALL_OFF stops the fetch", "switched off" in o)
os.remove(os.path.join(FIN, "_off", "ALL_OFF"))
os.makedirs(os.path.join(SCR, "nostub")); pr.STUB = os.path.join(SCR, "nostub")
st3 = pr.fetch(con)
ok("W11 the share not seen is said, not guessed", not st3["ok"] and "not seen" in st3["error"])
pr.STUB = STUB
o = subprocess.run([sys.executable, os.path.join(FIN, "payment_records.py"), "status"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode()
ok("W11 status names no paper and no patient", "Kumarx" not in o and "Invoice.pdf" not in o and "on the server" in o)
# W12 the pages (Flask), every role
try:
    from flask import Flask, g
    import payment_ledgers as pl
    app = Flask("w882")
    DBP = os.environ["FINANCE_DB"]
    def dbget():
        if "db" not in g:
            g.db = sqlite3.connect(DBP); g.db.row_factory = sqlite3.Row
        return g.db
    ROLE = {"r": "checker"}
    def req(*roles, unit="packs"):
        return (({"user": "x"}, None) if ROLE["r"] in roles else (None, ("no", 403)))
    pl.init(app, dbget, req, "packs")
    c = app.test_client()
    a = c.get("/finance/ledgers"); ok("W12 index 200 for the owner (10 distinct papers)", a.status_code == 200 and b"Receipts on the server" in a.data and b"10 papers" in a.data and b"Left in Drive" in a.data)
    a = c.get("/finance/ledgers/agilus"); ok("W12 Agilus page 200 + running total", a.status_code == 200 and b"Rs 3,650.50" in a.data and b"see the invoice" in a.data and b"Kumarx" not in a.data)
    a = c.get("/finance/ledgers/myoperator"); ok("W12 MyOperator page 200 + balance", a.status_code == 200 and b"Rs 12,345.67" in a.data and b"Rs 2,12,400" in a.data)
    fid = con.execute("SELECT id FROM payment_record_file WHERE vendor='MyOperator' AND kind='statement'").fetchone()[0]
    a = c.get("/finance/ledgers/file/%d" % fid); ok("W12 a paper opens in place (PDF)", a.status_code == 200 and a.data[:5] == b"%PDF-" and "inline" in a.headers.get("Content-Disposition", "inline"))
    ok("W12 a missing paper is 404", c.get("/finance/ledgers/file/99999").status_code == 404)
    a = c.get("/finance/ledgers/agilus/layout"); ok("W12 the masked layout page names no made-up patient", a.status_code == 200 and b"Kumarx" not in a.data and b"INVOICE" in a.data)
    ok("W12 no dialog on the pages", b"confirm(" not in c.get("/finance/ledgers").data)
    con.execute("UPDATE payment_record_file SET local_path='/etc/passwd' WHERE id=?", (fid,)); con.commit()
    ok("W12 a path outside the store is never served", c.get("/finance/ledgers/file/%d" % fid).status_code == 404)
    for role in ("maker", "viewer", "reception"):
        ROLE["r"] = role
        ok("W12 %s gets the owner's-page notice (403)" % role, all(c.get(u).status_code == 403 for u in ("/finance/ledgers", "/finance/ledgers/agilus", "/finance/ledgers/myoperator", "/finance/ledgers/file/1", "/finance/ledgers/agilus/layout")))
except Exception as e:                                                  # noqa: BLE001
    ok("W12 pages (%s)" % type(e).__name__, False)
# W13 the mount line in owner_console (TO): present once; the console stands when the ledgers fail to mount
oc = os.path.join(KIT, "owner_console.py")
s = open(oc, encoding="utf-8").read() if os.path.exists(oc) else ""
ok("W13 owner_console mounts the ledgers once", s.count("import payment_ledgers as _s882_pl") == 1 and s.count("_s882_pl.init(app, db_getter, require_fn, unit)") == 1)
m = re.search(r"(    try:[^\n]*# S882.*?file=sys.stderr\)\n)", s, re.S)
stood = False
if m:
    bad = os.path.join(SCR, "bad"); os.makedirs(bad)
    open(os.path.join(bad, "payment_ledgers.py"), "w").write("def init(*a):\n    raise RuntimeError('made-up failure')\n")
    sys.path.insert(0, bad); sys.modules.pop("payment_ledgers", None)
    code = "def _m(app, db_getter, require_fn, unit):\n" + m.group(1) + "    return True\n"
    ns = {"sys": sys}
    try:
        exec(code, ns); stood = ns["_m"](None, None, None, "packs") is True
    except BaseException:                                               # noqa: BLE001
        stood = False
ok("W13 the console stands when payment_ledgers fails to mount", stood)
n = sum(1 for _n, c in R if c)
print("WALK %d/%d" % (n, len(R)))
