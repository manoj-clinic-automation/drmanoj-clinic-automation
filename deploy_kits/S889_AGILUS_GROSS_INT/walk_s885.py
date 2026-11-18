# walk_s885.py -- S885 (S884's walk + rows wider than the rate)'s walk on a MADE-UP root: made-up Agilus papers laid out as the real one's masked layout
# (S882 /finance/ledgers/agilus/layout), made-up names and numbers only (F-185).
# Usage: python3 walk_s884.py <kit dir> <scratch dir> [<dir holding S882's payment_records.py>]. Last line "WALK n/N".
import json, os, shutil, sqlite3, subprocess, sys

KIT, SCR = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
PRD = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else KIT
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]   # F-1441
shutil.rmtree(SCR, ignore_errors=True)
FIN = os.path.join(SCR, "finance"); os.makedirs(FIN)
os.environ.update(FIN_DIR=FIN, FINANCE_DB=os.path.join(FIN, "finance.db"), PAYMENT_RECORDS_DIR=os.path.join(FIN, "payment_records"),
                  PAYMENT_RECORDS_STATE=os.path.join(FIN, "pr.state.json"))
for d, f in ((KIT, "agilus_ledger.py"), (KIT, "payment_ledgers.py"), (PRD, "payment_records.py")):
    if os.path.exists(os.path.join(d, f)):
        shutil.copy(os.path.join(d, f), FIN)
sys.path.insert(0, FIN)
R = []
def ok(name, cond):
    R.append((name, bool(cond)))
    if not cond:
        print("FAIL", name)

PHONE = "%d" % (5000000000 + 7)
def sample(no, amt, rows):
    P = 140
    L = [" " * P + "Agilus Diagnostics Ltd", " " * 73 + "BILL OF SUPPLY" + " " * 53 + "State: UTTAR PRADESH",
         "  Details of Recipient (Bill to)" + " " * 41 + "Details of Recipient (Ship to)", "  N K PATHOLOGY" + " " * 59 + "N K PATHOLOGY",
         "  12/A345, CIVIL LINES, BAREILLY UP/25/1," + " " * 33 + "12/A345, CIVIL LINES, BAREILLY UP/25/1," + " " * 27 + "Bill of Supply No",
         " " * P + no, "  BAREILLY BAREILLY 243001" + " " * 47 + "BAREILLY BAREILLY 243001", " " * P + "Bill of Supply Amount",
         "  " + PHONE + " India Uttar Pradesh" + " " * 41 + PHONE + " India Uttar Pradesh", " " * (P + 6) + amt,
         "  Date Accession #" + " " * 21 + "Client Code" + " " * 21 + "Patient Name" + " " * 27 + "HSN/SAC Code Service Name" + " " * 28 + "Rate",
         " Client - A100000001 N K PATHOLOGY"]
    for r in rows:
        if r[0] == "ODD":                                              # a dd/mm/yy row in an odd layout, then a page-2 header
            L.append("  09/11/26 2611BR000888" + " " * 22 + "Z9" + " " * 30 + "TESTH ODDROW".ljust(33) + "999311" + " " * 16 + "XYZ - ODD TEST, 150.00")
            L.append("\f  Date Accession #" + " " * 21 + "Client Code" + " " * 21 + "Patient Name" + " " * 27 + "HSN/SAC Code Service Name" + " " * 28 + "Rate")
            continue
        if r[0] == "BROKEN":
            L.append("  09/11 2611BR000999" + " " * 25 + "A100000001" + " " * 22 + "TESTX BROKEN".ljust(33) + "999311" + " " * 16 + "SOMETHING WITHOUT A RATE")
            continue
        tail = ("" if len(r) < 8 else "        1" + " " * 8 + r[4] + " " * 8 + r[7][0] + " " * 8 + r[7][1])     # Qty, Rate, Discount, Amount
        L.append("  %s %s" % (r[0], r[1]) + " " * 25 + "A100000001" + " " * 22 + r[2].ljust(33) + "999311" + " " * 16 + ("%s, %s" % (r[3], r[4])).ljust(36) + tail)
        L.append(" " * 77 + r[5] + " " * 46 + r[6])
    L.append(" " * 141 + "TOTAL:    " + amt)
    L.append(" " * 140 + "GRAND TOTAL:")
    return "\n".join(L) + "\n"

def pdf(path, text, size=5):
    lines = text.splitlines()
    body = "BT /F1 %d Tf 10 820 Td %d TL " % (size, size + 2) + " ".join("(%s) '" % l.replace("\\", "").replace("(", "\\(").replace(")", "\\)") for l in lines) + " ET"
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1000 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            "<< /Length %d >>\nstream\n%s\nendstream" % (len(body), body), "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"]
    out, offs = "%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += "%d 0 obj\n%s\nendobj\n" % (i, o)
    x = len(out)
    out += "xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + "".join("%010d 00000 n \n" % o for o in offs)
    out += "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="latin-1").write(out)

A = [("05/11", "2611BR000123", "TESTA PERSONB", "1234E - TOTAL IGE", "1250.00", "REF0000001", "SERUM"),
     ("06/11", "2611BR000124", "TESTC PERSOND", "CBC - COMPLETE BLOOD", "200.00", "REF0000002", "COUNT")]
store = os.environ["PAYMENT_RECORDS_DIR"]; ag = os.path.join(store, "Agilus (NK Pathology)")
papers = [("2026-11-10_Invoice.pdf", "invoice", sample("A12345678901", "1450.00", A)),
          ("2026-11-12_Invoice.pdf", "invoice", sample("A12345678902", "1500.00", A)),                         # lines 1,450 vs 1,500
          ("2026-01-03_Invoice.pdf", "invoice", sample("A12345678903", "300.00", [("28/12", "2512BR000001", "TESTE YEARROLL", "TSH - THYROID", "300.00", "REF0000003", "STIMULATING")])),
          ("2026-11-14_Invoice.pdf", "invoice", sample("A12345678904", "1250.00", [A[0], ("BROKEN",)])),
          ("2026-11-16_Invoice.pdf", "unreadable", None),
          ("2026-11-17_Invoice (1).pdf", "invoice", sample("A12345678901", "1450.00", A)),                     # the first, saved twice
          ("2026-11-18_Invoice.pdf", "invoice", sample("A12345678905", "500.00", [A[0][:4] + ("200.00",) + A[0][5:], ("ODD",), ("06/11", "2611BR000777", "TESTF PERSONG", "LFT - LIVER", "300.00", "REF0000007", "FUNCTION")]).replace("PAGEBREAK", "")),
          ("2026-11-19_Invoice.pdf", "invoice", "EMPTY"),
          ("2026-11-20_Invoice.pdf", "invoice", sample("A12345678906", "1100.00", [
              ("10/11", "2611BR000501", "TESTJ WIDEONE", "1234E - TOTAL IGE", "1250.00", "REF0000011", "SERUM", ("250.00", "1000.00")),
              ("11/11", "2611BR000502", "TESTK WIDETWO", "CBC - COMPLETE BLOOD", "200.00", "REF0000012", "COUNT", ("100.00", "100.00"))]))]
import payment_records as pr
con = sqlite3.connect(os.environ["FINANCE_DB"]); con.row_factory = sqlite3.Row
pr.ensure_schema(con)
import hashlib
for name, kind, text in papers:
    p = os.path.join(ag, name)
    if text is None or text == "EMPTY":
        os.makedirs(ag, exist_ok=True); open(p, "wb").write(b"%PDF-1.4 locked made-up\n%%EOF\n" if text is None else b"%PDF-1.4 text failed made-up\n%%EOF\n")
    else:
        pdf(p, text)
    b = open(p, "rb").read()
    sha = hashlib.sha256(sample("A12345678901", "1450.00", A).encode()).hexdigest() if name.endswith("(1).pdf") else hashlib.sha256(b).hexdigest()
    if name.endswith("(1).pdf"):
        sha = con.execute("SELECT sha256 FROM payment_record_file WHERE name='2026-11-10_Invoice.pdf'").fetchone()[0]
    con.execute("INSERT INTO payment_record_file(drive_id, drive_md5, vendor, mail_date, name, size, sha256, local_path, kind, fetched_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)", ("d-" + name, "m", "Agilus (NK Pathology)", name[:10], name, len(b), sha, p, kind, "x"))
con.commit()

try:
    import agilus_ledger as al
except Exception as e:                                                  # noqa: BLE001
    print("FAIL import agilus_ledger: %s" % type(e).__name__); print("WALK 0/31"); sys.exit(0)

n = al.build(con)
ok("A1 eight papers read (the one saved twice is one)", n == 8)
st = {r["invoice_no"] or r["status"]: r for r in con.execute("SELECT * FROM agilus_invoice")}
ok("A2 the paper's number and amount read", "A12345678901" in st and st["A12345678901"]["amount_paise"] == 145000)
ok("A2 lines that add up -> ok", st["A12345678901"]["status"] == "ok" and st["A12345678901"]["n_lines"] == 2)
ok("A3 lines that do not add up are said so", st["A12345678902"]["status"] == "lines differ" and st["A12345678902"]["lines_paise"] == 145000)
ok("A4 a row this reader cannot take is counted, never dropped silently", st["A12345678904"]["unread_rows"] == 1 and st["A12345678904"]["status"] == "lines differ")
ok("A5 a locked paper stays in the ledger as unreadable", any(r["status"] == "unreadable" for r in st.values()))
ln = {r["patient_name"]: dict(r) for r in con.execute("SELECT l.* FROM agilus_line l JOIN payment_record_file f ON f.id=l.file_id WHERE f.name IN ('2026-11-10_Invoice.pdf', '2026-01-03_Invoice.pdf')")}
ok("A6 the patient, reference, test (wrapped) and amount", ln.get("TESTA PERSONB", {}).get("patient_ref") == "REF0000001"
   and ln["TESTA PERSONB"]["test"] == "1234E - TOTAL IGE SERUM" and ln["TESTA PERSONB"]["amount_paise"] == 125000 and ln["TESTA PERSONB"]["accession"] == "2611BR000123")
ok("A6 the test date takes the paper's year", ln["TESTA PERSONB"]["test_date"] == "2026-11-05")
ok("A7 a December test on a January paper is last year's", ln.get("TESTE YEARROLL", {}).get("test_date") == "2025-12-28")
ok("A8 the address phone line is never read as the amount", st["A12345678903"]["amount_paise"] == 30000)
ok("A9 a second build reads only the paper whose text failed (tried again)", al.build(con) == 1)
ok("A9 a rebuild reads all again, no line twice", al.build(con, force=True) == 8 and con.execute("SELECT COUNT(*) FROM agilus_line").fetchone()[0] == 10)
c = al.counts(con)
ok("A10 counts", c["invoices"] == 8 and c["ok"] == 3 and c["lines differ"] == 3 and c["unreadable"] == 2 and c["lines"] == 10 and c["rows_not_read"] == 2)
led = al.ledger(con)
ok("A11 the ledger runs oldest first on the paper's amount", [x["inv_date"] for x in led] == sorted(x["inv_date"] for x in led) and led[-1]["running"] == 30000 + 145000 + 150000 + 125000 + 50000 + 110000)
st5 = {r["invoice_no"]: dict(r) for r in con.execute("SELECT * FROM agilus_invoice")}
ok("A17 an odd dd/mm/yy row is counted, never glued onto the patient before it", st5["A12345678905"]["unread_rows"] == 1 and st5["A12345678905"]["status"] == "lines differ"
   and all("ODDROW" not in (r["patient_name"] or "") and "ODD TEST" not in (r["test"] or "") for r in con.execute("SELECT * FROM agilus_line")))
ok("A18 a page-2 header never sticks to the last patient", all("Patient Name" not in (r["patient_name"] or "") and "Rate" not in (r["test"] or "") for r in con.execute("SELECT * FROM agilus_line")))
ok("A19 a paper whose text failed is tried again tomorrow", con.execute("SELECT parser FROM agilus_invoice i JOIN payment_record_file f ON f.id=i.file_id WHERE f.name='2026-11-19_Invoice.pdf'").fetchone()[0] == "")
oid = con.execute("SELECT id FROM payment_record_file WHERE name='2026-11-18_Invoice.pdf'").fetchone()[0]
con.execute("UPDATE payment_record_file SET kind='paper' WHERE id=?", (oid,)); con.commit(); al.build(con)
ok("A20 a paper gone from the copy leaves the ledger and the counts", con.execute("SELECT COUNT(*) FROM agilus_invoice WHERE file_id=?", (oid,)).fetchone()[0] == 0 and al.counts(con)["invoices"] == 7)
con.execute("UPDATE payment_record_file SET kind='invoice' WHERE id=?", (oid,)); con.commit(); al.build(con)
con.execute("UPDATE payment_record_file SET total_paise=99900 WHERE name='2026-11-16_Invoice.pdf'"); con.commit()
ok("A21 a locked paper keeps the figure S882 had (its own total / the mail's)", any(x["amount"] == 99900 for x in al.ledger(con)))
con.execute("UPDATE payment_record_file SET total_paise=NULL WHERE name='2026-11-16_Invoice.pdf'"); con.commit()
w = {r["patient_name"]: dict(r) for r in con.execute("SELECT * FROM agilus_line WHERE patient_name LIKE 'TEST_ WIDE%'")}
ok("A22 a row wider than the rate: the amount column that adds up to the paper (after discount)", w.get("TESTJ WIDEONE", {}).get("amount_paise") == 100000 and w.get("TESTK WIDETWO", {}).get("amount_paise") == 10000
   and w["TESTJ WIDEONE"]["test"] == "1234E - TOTAL IGE SERUM" and w["TESTJ WIDEONE"]["patient_ref"] == "REF0000011")
iv = con.execute("SELECT status FROM agilus_invoice WHERE invoice_no='A12345678906'").fetchone()
ok("A22 that paper adds up", iv and iv[0] == "ok")
sh = al.counts(con).get("row_shapes") or []
ok("A23 the check carries row shapes in classes only, never a word", sh and all(set(k.split()) <= {"D", "A", "C", "W", "H", "S,", "S", "M", "Q"} for k, _n in sh))
o = subprocess.run([sys.executable, os.path.join(FIN, "agilus_ledger.py"), "build"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode()
ok("A12 the command prints counts, never a name", "invoices" in o and "TESTA" not in o and "PERSON" not in o and "REF00" not in o)
try:
    from flask import Flask, g
    import payment_ledgers as pl
    app = Flask("w884")
    DBP = os.environ["FINANCE_DB"]
    def dbget():
        if "db" not in g:
            g.db = sqlite3.connect(DBP); g.db.row_factory = sqlite3.Row
        return g.db
    ROLE = {"r": "checker"}
    def req(*roles, unit="packs"):
        return (({"user": "x"}, None) if ROLE["r"] in roles else (None, ("no", 403)))
    pl.init(app, dbget, req, "packs")
    cl = app.test_client()
    a = cl.get("/finance/ledgers/agilus"); d = a.data.decode()
    ok("A13 his Agilus page: every line, the check, the search box", a.status_code == 200 and "TESTA PERSONB" in d and "lines add up" in d and "lines do not add up" in d and "id=q" in d and "A12345678901" in d)
    ok("A13 the running total on the newest", "Rs 6,100" in d)
    ok("A13 no dialog", "confirm(" not in d and "alert(" not in d)
    a = cl.get("/finance/ledgers/agilus/check"); j = a.get_json() or {}
    ok("A14 the check answers counts only", a.status_code == 200 and j.get("invoices") == 8 and "TESTA" not in a.data.decode())
    ok("A15 the other pages still stand", cl.get("/finance/ledgers").status_code == 200 and cl.get("/finance/ledgers/myoperator").status_code == 200)
    for role in ("maker", "viewer", "reception"):
        ROLE["r"] = role
        ok("A16 %s gets the owner's-page notice" % role, all(cl.get(u).status_code == 403 for u in ("/finance/ledgers/agilus", "/finance/ledgers/agilus/check")))
except Exception as e:                                                  # noqa: BLE001
    ok("A13 pages (%s)" % type(e).__name__, False)
print("WALK %d/%d" % (sum(1 for _n, x in R if x), len(R)))
