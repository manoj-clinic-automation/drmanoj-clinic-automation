#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s622.py -- kit S622 (S336, 22-Oct-2026, D755, F-975): SBI's real heads.

    python3 walk_s622.py OLD_DIR NEW_DIR [--live-db FILE]
      OLD_DIR / NEW_DIR hold packs.py, packs.html and the modules beside them (stmt_shelf.py ...).

Part A, made-up only: heads in the layout SBI really prints (the holder left of 'State Bank of India' on its line, printed
KUMARAGARWAL; 'Statement From :' on savings, 'Statement :' on the Auto Loan; no 'Account Name' label) are read -- the holder,
savings / loan, the period -- and filed by 'Add statements' onto their own accounts; the HUF stays the HUF's; the S621 layouts
still read; a locked upload's line carries the jump to its password box; the page's script parses.
Part B (--live-db, on the box): a scratch COPY of the live finance.db -- every SBI file on the shelf whose text can be read is
placed on an SBI account of its own kind, with its period.
Exit 0 = GREEN (last line 'WALK OK ...'); the S621 file goes RED.
"""
import importlib.util
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

OLD, NEW = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
LIVE_DB = sys.argv[sys.argv.index("--live-db") + 1] if "--live-db" in sys.argv else ""
passed, failed = [], []
T = tempfile.mkdtemp(prefix="s622_walk_")


def check(c, label):
    (passed if c else failed).append(label)
    print(("  ok   " if c else "  FAIL ") + label)
    return c


def load(d, tag, db, inbox):
    os.environ.update(FINANCE_DB=db, STMT_INBOX=inbox, PACKS_DIR=os.path.join(T, "packs_" + tag), PACKS_TODAY="2026-10-22",
                      STMT_VENV_PYTHON=os.environ.get("WALK_VPY", sys.executable))
    sys.path.insert(0, d)
    for k in [k for k in sys.modules if k in ("packs", "stmt_shelf")]:
        del sys.modules[k]
    spec = importlib.util.spec_from_file_location("packs_" + tag, os.path.join(d, "packs.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sys.path.remove(d)
    return m


def pdf(lines):
    """A one-page PDF of text lines (Helvetica), no library needed."""
    esc = lambda s: s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    body = "BT /F1 9 Tf 12 TL 36 806 Td " + " ".join("(%s) '" % esc(x) for x in lines) + " ET"
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            "<< /Length %d >>\nstream\n%s\nendstream" % (len(body), body), "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offs = io.BytesIO(), []
    out.write(b"%PDF-1.4\n")
    for i, o in enumerate(objs, 1):
        offs.append(out.tell())
        out.write(("%d 0 obj\n%s\nendobj\n" % (i, o)).encode("latin-1"))
    x = out.tell()
    out.write(("xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)).encode())
    for o in offs:
        out.write(("%010d 00000 n \n" % o).encode())
    out.write(("trailer << /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)).encode())
    return out.getvalue()


def lock(blob, pw):
    """Encrypt with pypdf under whichever python has it (the box: the venv)."""
    src, dst = os.path.join(T, "plain.pdf"), os.path.join(T, "locked.pdf")
    open(src, "wb").write(blob)
    code = ("import pypdf,sys; r=pypdf.PdfReader(sys.argv[1]); w=pypdf.PdfWriter(); [w.add_page(p) for p in r.pages]; "
            "w.encrypt(sys.argv[3]); w.write(open(sys.argv[2],'wb'))")
    subprocess.run([os.environ.get("WALK_VPY", sys.executable), "-c", code, src, dst, pw], check=True)
    return open(dst, "rb").read()


SP = "                                             "
SAV_M = ["Welcome:", SP + "As on 20-10-2026", SP + "Mr. WALKMANOJ KUMARAGARWAL", " Account Summary", SP + "STATEMENT OF ACCOUNT", "",
         "         Mr. WALKMANOJ KUMARAGARWAL" + SP + "State Bank of India", SP + "MADE UP BRANCH,", "         1 MADE UP ROAD, WALKTOWN",
         SP + "Branch Code          : 00001", "     Date of Statement  : 20-10-2026", SP + "IFSC Code  : SBIN0000001",
         "  Account Number  : 00000041111111001", "  Interest Rate  : 2.50 % p.a.", "  Statement From  : 01-04-2026 to 20-10-2026",
         "  Balance", "03/04/2026  03/04/2026  WDL TFR LOCKER CHARGES  4,720.00  -  1,38,520.00"]
LOAN_M = ["  As on 20-10-2026" + SP + "Welcome:", SP + "Customer XXXXXXX1111", " Account Summary", SP + "STATEMENT OF ACCOUNT", "",
          "         WALKMANOJ KUMARAGARWAL" + SP + "State Bank of India", SP + "WALKTOWN", "         1 MADE UP ROAD, WALKTOWN",
          SP + "Branch Code  : 00001", "     Date of Statement  : 20-10-2026", SP + "IFSC Code  : SBIN0000001",
          "  Sanctioned Amount  : 1,00,000.00", "  Outstanding Amount  : 50,000.00  Account No  : 00000041111111004",
          "  Rate of Interest  : 8.65%  Product  : Auto Loan", "  Loan Term  : 84 Months  Currency  : INR", "  EMI  : 1,000.00",
          "  Account open Date  : 28-03-2023", "  Statement  : 01-04-2026 to 20-10-2026", "  Value Date  Ref No/Cheque", "Post Date  Details  Debit  Credit  Balance",
          "30/09/2026  30/09/2026  INTEREST  -  622.00  -"]
LOAN_B = ["  As on 20-10-2026" + SP + "Welcome:", " Account Summary", SP + "STATEMENT OF ACCOUNT", "",
          "         BHAWNA WALKAGARWAL" + SP + "State Bank of India", "     Date of Statement  : 20-10-2026",
          "  Outstanding Amount  : 20,000.00  Account No  : 00000041111111006", "  Product  : Auto Loan",
          "  Statement  : 01-04-2026 to 20-10-2026", "Post Date  Details  Debit  Credit  Balance"]
SAV_B = ["Welcome:", SP + "Dr.(Mrs.) BHAVNA WALKAGARWAL", " Account Summary", SP + "STATEMENT OF ACCOUNT", "",
         "         Dr.(Mrs.) BHAVNA WALKAGARWAL" + SP + "State Bank of India", "  Account Number  : 00000041111111003",
         "  Statement From  : 01-04-2026 to 20-10-2026", "  Balance"]
SAV_HUF = ["Welcome:", SP + "WALKMANOJ KUMAR AGARWAL HUF", " Account Summary", SP + "STATEMENT OF ACCOUNT", "",
           "         WALKMANOJ KUMAR AGARWAL HUF" + SP + "State Bank of India", "  Account Number  : 00000041111111002",
           "  Statement From  : 01-07-2026 to 30-09-2026", "  Balance"]
OLD_FORM = ["STATE BANK OF INDIA", "Account Name : MRS. BHAVNA WALKAGARWAL", "Account Number : 00000041111111007",
            "Account Description : PUBLIC PROVIDENT FUND (PPF)", "Period : 01/04/2026 to 30/09/2026"]

try:
    db, inbox = os.path.join(T, "a.db"), os.path.join(T, "inbox")
    os.makedirs(inbox)
    P = load(NEW, "new", db, inbox)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    P.ensure(con)
    for k, w in (("sbi_sav_manoj", "WALKMANOJ AGARWAL"), ("sbi_sav_bhawna", "BHAWNA WALKAGARWAL"), ("sbi_sav_huf", "WALKMANOJ KUMAR AGARWAL HUF"),
                 ("sbi_loan_manoj", "WALKMANOJ AGARWAL"), ("sbi_loan_bhawna", "BHAWNA WALKAGARWAL"), ("sbi_ppf_manoj", "WALKMANOJ AGARWAL"),
                 ("sbi_ppf_bhawna", "BHAWNA WALKAGARWAL")):
        con.execute("UPDATE stmt_slot SET ident_words=? WHERE key=?", (w, k))
    con.commit()
    want = ((SAV_M, "savings", "WALKMANOJ KUMAR AGARWAL", "2026-04-01", "2026-10-20"),
            (LOAN_M, "loan", "WALKMANOJ KUMAR AGARWAL", "2026-04-01", "2026-10-20"),
            (LOAN_B, "loan", "BHAWNA WALKAGARWAL", "2026-04-01", "2026-10-20"),
            (SAV_B, "savings", "BHAWNA WALKAGARWAL", "2026-04-01", "2026-10-20"),
            (SAV_HUF, "savings", "WALKMANOJ KUMAR AGARWAL HUF", "2026-07-01", "2026-09-30"),
            (OLD_FORM, "ppf", "BHAWNA WALKAGARWAL", "2026-04-01", "2026-09-30"))
    for lines, typ, hold, pf, pt in want:
        idt = P.identify_text("\n".join(lines))
        check(idt["bank"] == "SBI" and idt.get("sbi_type") == typ and hold in (idt["holder"] or "") and (idt["period_from"], idt["period_to"]) == (pf, pt),
              "read as SBI %s, %s, %s..%s (got %s %s '%s' %s..%s)" % (typ, hold, pf, pt, idt["bank"], idt.get("sbi_type"), idt["holder"], idt["period_from"], idt["period_to"]))
    from flask import Flask
    app = Flask("walk")
    P.init(app, lambda: con, lambda *a, **k: ({"user": "walk", "role": "checker"}, None))
    C = app.test_client()
    blobs = (("MKA SBI.pdf", pdf(SAV_M), "Dr Manoj Agarwal (SBI savings)"), ("MKA SBI LOAN.pdf", pdf(LOAN_M), "Dr Manoj Agarwal (SBI loan)"),
             ("BHAWNA LOAN.pdf", lock(pdf(LOAN_B), "walk-pw"), None), ("BHAWNA SBI STATEMENT.pdf", pdf(SAV_B), "Dr Bhawna Agarwal (SBI savings)"),
             ("huf.pdf", pdf(SAV_HUF), "Manoj Kumar Agarwal HUF (SBI savings)"))
    got = {}
    for name, blob, _a in blobs:
        r = C.post("/finance/packs/api/upload", data={"files": [(io.BytesIO(blob), name)]}, content_type="multipart/form-data")
        got[name] = ((r.get_json() or {}).get("files") or [{}])[0]
    for name, _b, acc in blobs:
        if acc:
            check(got[name].get("account") == acc and got[name].get("period_to"), "'%s' filed on %s with its period (%s)" % (name, acc, got[name].get("account")))
    check(not got["BHAWNA LOAN.pdf"].get("account") and got["BHAWNA LOAN.pdf"].get("why", "").startswith("locked"), "the locked one waits for its password")
    P.set_secret(con, "SBI:sbi_loan_bhawna", "walk-pw", "walk")
    r = con.execute("SELECT s.key, f.period_from, f.period_to FROM stmt_file f JOIN stmt_slot s ON s.id=f.slot_id WHERE f.name='BHAWNA LOAN.pdf'").fetchone()
    check(bool(r) and r[0] == "sbi_loan_bhawna" and r[2] == "2026-10-20", "its password typed: Dr Bhawna's loan, with its period (%s)" % (tuple(r) if r else None,))
    c9 = {c["slot"]: c for c in P.cells(con, "2026-09")}
    check(all(c9[k]["state"] == "arrived" for k in ("sbi_sav_manoj", "sbi_loan_manoj", "sbi_sav_bhawna", "sbi_loan_bhawna", "sbi_sav_huf")),
          "September's five quarterly SBI cells are full (%s)" % ", ".join("%s=%s" % (k[4:], c9[k]["state"]) for k in sorted(c9) if k.startswith("sbi_")))
    html = open(os.path.join(NEW, "packs.html"), encoding="utf-8").read()
    check("function goPw()" in html and "Go to its password box" in html, "a locked upload's line carries the jump to its password box")
    node = shutil.which("node")
    if node:
        sc = "\n".join(re.findall(r"<script>(.*?)</script>", html, re.S)).replace("{{month}}", "2026-09").replace("{{me}}", "walk")
        open(os.path.join(T, "p.js"), "w").write(sc)
        check(subprocess.run([node, "--check", os.path.join(T, "p.js")], capture_output=True).returncode == 0, "the page's script parses")
    con.close()

    if LIVE_DB:
        print("[B] a scratch copy of the live finance.db")
        dbn = os.path.join(T, "live_new.db")
        src = sqlite3.connect("file:%s?mode=ro" % LIVE_DB, uri=True)
        d = sqlite3.connect(dbn)
        src.backup(d)
        d.close()
        src.close()
        N = load(NEW, "n", dbn, os.path.join(T, "inbox_n"))
        cn = sqlite3.connect(dbn)
        cn.row_factory = sqlite3.Row
        N.ensure(cn)
        rows = [dict(r) for r in cn.execute("SELECT * FROM stmt_file WHERE folder='bank' AND (bank='SBI' OR COALESCE(subfolder,'')='upload') ORDER BY id")]
        n_ok, n_seen, bad = 0, 0, []
        for f in rows:
            lp = f.get("unlocked_path") or f.get("local_path") or ""
            if not lp or not os.path.exists(lp):
                continue
            text, locked = N._file_text(lp)
            if not text:
                continue
            idt = N.identify_text(text)
            if idt["bank"] != "SBI":
                continue
            n_seen += 1
            slot, how = N.place(cn, idt)
            ok = bool(slot) and slot["bank"] == "SBI" and N.SLOT_TYPE.get(slot["key"]) == idt.get("sbi_type") and bool(idt["period_to"])
            n_ok += ok
            if not ok:
                bad.append("file %d: %s" % (f["id"], how if not slot else "no period"))
        print("    SBI files on the shelf with readable text: %d" % n_seen)
        check(n_ok == n_seen, "every one is placed on an SBI account of its own kind, with its period (%d of %d)%s"
              % (n_ok, n_seen, (" -- " + "; ".join(bad[:4])) if bad else ""))
        cn.close()
finally:
    shutil.rmtree(T, ignore_errors=True)

print("")
print(("WALK OK" if not failed else "WALK RED") + " S622: %d passed, %d failed" % (len(passed), len(failed)))
sys.exit(0 if not failed else 1)
