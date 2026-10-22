#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s621.py -- kit S621 (S336, 22-Oct-2026, D754): SBI on the packs page.

    python3 walk_s621.py OLD_DIR NEW_DIR [--live-db FILE]
      OLD_DIR / NEW_DIR hold packs.py, packs.html and the modules beside them (stmt_shelf.py ...).

Part A, made-up only (a fresh database, made-up holders' statements written as PDFs here, one locked with a made-up password):
  * SBI is told by its head: savings / loan / PPF, the 'Account Name' line (Bhavna is Bhawna), the tail, the period in the
    forms SBI prints;
  * 'Add statements' takes several PDFs at once, any name: each is filed on its account (the locked one after its password
    is typed into its own SBI box), the same bytes twice are one file, a non-PDF is refused in words;
  * a quarterly slot is asked for only in Jun / Sep / Dec / Mar, a PPF only in Sep / Mar, and needs ONE statement covering
    the whole period (Jul-Sep for September; Apr-Sep for the PPF); October asks for none of them;
  * the statement road leaves the uploads and SBI out; the page carries the upload and one SBI box per account; its script parses.
Part B (--live-db, on the box): a scratch COPY of the live finance.db -- the old and the new file give the same cells for every
other account in Aug, Sep and Oct, the same statement-road verdict; September's pack carries seven SBI rows, October's none.
Exit 0 = GREEN (last line 'WALK OK ...'); the S568 file goes RED.
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
T = tempfile.mkdtemp(prefix="s621_walk_")


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


SAV_M = ["STATE BANK OF INDIA", "Account Name      : MR. WALKMANOJ AGARWAL", "Address           : 1 Made Up Road",
         "Account Number    : 00000041111111001", "Account Description : REGULAR SB CHQ-INDIVIDUALS", "IFS Code : SBIN0000001",
         "Account Statement from 1 Jul 2026 to 30 Sep 2026", "Txn Date  Value Date  Description  Debit  Credit  Balance",
         "1 Jul 2026  1 Jul 2026  BY TRANSFER  0  100  1,100"]
SAV_HUF = ["STATE BANK OF INDIA", "Account Name : WALKMANOJ KUMAR AGARWAL HUF", "Account Number : 00000041111111002",
           "Account Description : SAVINGS BANK", "Statement From : 01-07-2026 To : 30-09-2026", "Date Particulars Withdrawal Deposit Balance"]
SAV_B = ["State Bank of India", "Account Name : MRS. BHAVNA WALKAGARWAL", "Account Number : 00000041111111003",
         "Period : 01/07/2026 to 19/10/2026", "Txn Date Description Debit Credit Balance"]
LOAN_M = ["STATE BANK OF INDIA", "Name : DR WALKMANOJ AGARWAL", "Loan Account Number : 00000041111111004",
          "Account Description : SBI HOME LOAN - TERM LOAN", "From Date 1-Jul-2026 To Date 30-Sep-2026", "Date Particulars Debit Credit Balance"]
PPF_B = ["STATE BANK OF INDIA", "Customer Name : BHAWNA WALKAGARWAL", "Account Number : 00000041111111005",
         "Account Description : PUBLIC PROVIDENT FUND (PPF)", "Account Statement from 01 Jul 2026 to 30 Sep 2026"]

try:
    # ------------------------------------------------------------------ Part A
    db, inbox = os.path.join(T, "a.db"), os.path.join(T, "inbox")
    os.makedirs(inbox)
    P = load(NEW, "new", db, inbox)
    if not check(hasattr(P, "SLOT_EVERY") and hasattr(P, "add_uploads") and hasattr(P, "sbi_ident"), "the packs know SBI and its cadence"):
        print("WALK RED S621: no SBI (the S568 file)")
        sys.exit(1)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    P.ensure(con)
    # made-up holders: the slot words are pointed at made-up names (the real words are checked below, on the live copy)
    for k, w in (("sbi_sav_manoj", "WALKMANOJ AGARWAL"), ("sbi_sav_bhawna", "BHAWNA WALKAGARWAL"), ("sbi_sav_huf", "WALKMANOJ KUMAR AGARWAL HUF"),
                 ("sbi_loan_manoj", "WALKMANOJ AGARWAL"), ("sbi_loan_bhawna", "BHAWNA WALKAGARWAL"), ("sbi_ppf_manoj", "WALKMANOJ AGARWAL"),
                 ("sbi_ppf_bhawna", "BHAWNA WALKAGARWAL")):
        con.execute("UPDATE stmt_slot SET ident_words=? WHERE key=?", (w, k))
    con.commit()
    n_sbi = con.execute("SELECT COUNT(*) FROM stmt_slot WHERE bank='SBI'").fetchone()[0]
    check(n_sbi == 7, "seven SBI slots on the shelf (%d) -- savings x3, loans x2, PPF x2" % n_sbi)
    for lines, want_type, want_hold, want_pf, want_pt in ((SAV_M, "savings", "MR. WALKMANOJ AGARWAL", "2026-07-01", "2026-09-30"),
                                                          (SAV_HUF, "savings", "WALKMANOJ KUMAR AGARWAL HUF", "2026-07-01", "2026-09-30"),
                                                          (SAV_B, "savings", "MRS. BHAWNA WALKAGARWAL", "2026-07-01", "2026-10-19"),
                                                          (LOAN_M, "loan", "DR WALKMANOJ AGARWAL", "2026-07-01", "2026-09-30"),
                                                          (PPF_B, "ppf", "BHAWNA WALKAGARWAL", "2026-07-01", "2026-09-30")):
        idt = P.identify_text("\n".join(lines))
        check(idt["bank"] == "SBI" and idt.get("sbi_type") == want_type and idt["holder"] == want_hold
              and (idt["period_from"], idt["period_to"]) == (want_pf, want_pt),
              "SBI head read: %s / %s / %s -> %s" % (want_type, want_hold, lines[-1][:28] if False else "%s..%s" % (want_pf, want_pt),
                                                     "%s %s %s %s..%s" % (idt["bank"], idt.get("sbi_type"), idt["holder"], idt["period_from"], idt["period_to"])))
    icici = ["ICICI Bank", "Your Details With Us:", "WALK CLINIC", "Statement period 01/09/2026 to 30/09/2026", "NEFT SBIN0001234 STATE BANK OF INDIA"]
    check(P.identify_text("\n".join(icici))["bank"] == "ICICI", "an ICICI statement whose lines name SBI stays ICICI")

    from flask import Flask
    app = Flask("walk")
    P.init(app, lambda: con, lambda *a, **k: ({"user": "walk", "role": "checker"}, None))
    C = app.test_client()
    blobs = {"AccountStatement_1.pdf": pdf(SAV_M), "x.pdf": pdf(SAV_HUF), "loan (1).pdf": pdf(LOAN_M), "ppf.PDF": pdf(PPF_B),
             "bhavna.pdf": lock(pdf(SAV_B), "walk-made-up-pw")}
    data = {"files": [(io.BytesIO(b), n) for n, b in blobs.items()] + [(io.BytesIO(b"hello"), "notes.txt")]}
    r = C.post("/finance/packs/api/upload", data=data, content_type="multipart/form-data")
    j = r.get_json() or {}
    acc = {x["name"]: x for x in j.get("files", [])}
    check(r.status_code == 200 and j.get("added") == 5 and [x["name"] for x in j.get("refused", [])] == ["notes.txt"],
          "five PDFs added at once; the .txt refused in words (%s)" % (j.get("refused"),))
    check((acc.get("AccountStatement_1.pdf") or {}).get("account") == "Dr Manoj Agarwal (SBI savings)"
          and (acc.get("x.pdf") or {}).get("account") == "Manoj Kumar Agarwal HUF (SBI savings)"
          and (acc.get("loan (1).pdf") or {}).get("account") == "Dr Manoj Agarwal (SBI loan)"
          and (acc.get("ppf.PDF") or {}).get("account") == "Dr Bhawna Agarwal (SBI PPF)",
          "each filed on its own account by its content, whatever its name (savings, HUF, loan, PPF)")
    check(not (acc.get("bhavna.pdf") or {}).get("account") and "password" in (acc.get("bhavna.pdf") or {}).get("why", ""),
          "the locked one waits, and says it wants its password")
    r2 = C.post("/finance/packs/api/upload", data={"files": [(io.BytesIO(blobs["x.pdf"]), "same again.pdf")]}, content_type="multipart/form-data")
    j2 = r2.get_json() or {}
    check(j2.get("added") == 0 and j2.get("same") == 1 and con.execute("SELECT COUNT(*) FROM stmt_file").fetchone()[0] == 5,
          "the same bytes twice are one file")
    keys = [b for b, _l, _a in P.secret_keys(con)]
    check(sum(1 for k in keys if k.startswith("SBI:")) == 7 and "SBI" in keys, "a password box per SBI account, and SBI bank-wide")
    body, code = P.set_secret(con, "SBI:sbi_sav_bhawna", "walk-made-up-pw", "walk")
    placed = con.execute("SELECT s.key, f.period_from, f.period_to FROM stmt_file f JOIN stmt_slot s ON s.id=f.slot_id WHERE f.name='bhavna.pdf'").fetchone()
    check(code == 200 and placed and placed[0] == "sbi_sav_bhawna" and placed[2] == "2026-10-19",
          "its password typed once: opened by the shelf, filed on Dr Bhawna's savings (%s)" % (tuple(placed) if placed else None,))
    LOAN_B = ["STATE BANK OF INDIA", "Account Name : DR BHAVNA WALKAGARWAL", "Account Number : 00000041111111006",
              "Account Description : SBI TERM LOAN", "Statement from 01-07-2026 to 30-09-2026"]
    r3 = C.post("/finance/packs/api/upload", data={"files": [(io.BytesIO(lock(pdf(LOAN_B), "walk-made-up-pw")), "Untitled.pdf")]},
                content_type="multipart/form-data")
    f3 = ((r3.get_json() or {}).get("files") or [{}])[0]
    check(f3.get("account") == "Dr Bhawna Agarwal (SBI loan)", "a locked one added after its password is set is opened and filed at once (%s)" % f3.get("account"))
    check("walk-made-up-pw" not in json.dumps(body) and "walk-made-up-pw" not in json.dumps(P.secret_state(con)), "the password is never sent back")
    # the cadence
    c9 = {c["slot"]: c for c in P.cells(con, "2026-09")}
    c10 = {c["slot"]: c for c in P.cells(con, "2026-10")}
    c12 = {c["slot"]: c for c in P.cells(con, "2026-12")}
    c3 = {c["slot"]: c for c in P.cells(con, "2027-03")}
    check(all(k in c9 for k in P.SLOT_EVERY) and not any(k in c10 for k in P.SLOT_EVERY), "September asks for all seven; October for none")
    check(all(k in c12 for k in P.SLOT_EVERY if P.SLOT_EVERY[k] == 3) and not any(k in c12 for k in P.SLOT_EVERY if P.SLOT_EVERY[k] == 6)
          and all(k in c3 for k in P.SLOT_EVERY), "December asks for the quarterly five only; March for all seven")
    check(c9["sbi_sav_manoj"]["state"] == "arrived" and c9["sbi_loan_manoj"]["state"] == "arrived" and c9["sbi_sav_huf"]["state"] == "arrived"
          and c9["sbi_sav_bhawna"]["state"] == "arrived", "Jul-Sep statements make September's quarterly cells (savings, HUF, loan, Bhawna to 19-Oct)")
    check(c9["sbi_ppf_bhawna"]["state"] == "partial" and c9["sbi_ppf_manoj"]["state"] == "empty",
          "the PPF's September cell wants April-September: a Jul-Sep statement is only part of it")
    check(c9["sbi_sav_manoj"]["period_words"] == "July – September 2026" and c9["sbi_ppf_bhawna"]["period_words"] == "April – September 2026"
          and c3["sbi_ppf_bhawna"]["period_words"] == "October 2026 – March 2027", "each period said in words")
    r = P.statement_road(con)
    other = [c for c in P.cells(con, "2026-09") if c["kind"] != "card" and c["bank"] != "SBI" and c["state"] in ("empty", "partial")]
    check(r["last"] == "" and r["this_month"] == 0 and r["waiting"] == len(other),
          "the statement road counts neither the uploads nor SBI (%s, %d awaited, all of them relay banks)" % (r["state"], r["waiting"]))
    html = open(os.path.join(NEW, "packs.html"), encoding="utf-8").read()
    check('id="upf"' in html and 'fetch("/finance/packs/api/upload"' in html and "SBI account" in html, "the page carries Add statements and the SBI boxes")
    node = shutil.which("node")
    if node:
        sc = "\n".join(re.findall(r"<script>(.*?)</script>", html, re.S))
        sc = sc.replace("{{month}}", "2026-09").replace("{{me}}", "walk")
        open(os.path.join(T, "p.js"), "w").write(sc)
        check(subprocess.run([node, "--check", os.path.join(T, "p.js")], capture_output=True).returncode == 0, "the page's script parses")
    con.close()

    # ------------------------------------------------------------------ Part B
    if LIVE_DB:
        print("[B] a scratch copy of the live finance.db")
        dbo, dbn = os.path.join(T, "live_old.db"), os.path.join(T, "live_new.db")
        src = sqlite3.connect("file:%s?mode=ro" % LIVE_DB, uri=True)
        for p in (dbo, dbn):
            d = sqlite3.connect(p)
            src.backup(d)
            d.close()
        src.close()
        O = load(OLD, "o", dbo, os.path.join(T, "inbox_o"))
        co = sqlite3.connect(dbo)
        co.row_factory = sqlite3.Row
        N = load(NEW, "n", dbn, os.path.join(T, "inbox_n"))
        cn = sqlite3.connect(dbn)
        cn.row_factory = sqlite3.Row
        strip = lambda c: {k: v for k, v in c.items() if k not in ("every", "period_words")}
        same = True
        for m in ("2026-08", "2026-09", "2026-10"):
            a = [strip(c) for c in O.cells(co, m)]
            b = [strip(c) for c in N.cells(cn, m) if c["bank"] != "SBI"]
            same = same and a == b
        check(same, "every other account's cells are the same in Aug, Sep and Oct")
        ro, rn = O.statement_road(co), N.statement_road(cn)
        check((ro["state"], ro["missing"], ro["waiting"]) == (rn["state"], rn["missing"], rn["waiting"]),
              "the statement road's verdict is the same (%s)" % rn["state"])
        rows9, _a = N.pack_rows(cn, "2026-09", light=True)
        rows10, _b = N.pack_rows(cn, "2026-10", light=True)
        s9 = [r for r in rows9 if r["key"].startswith("stmt:sbi_")]
        check(len(s9) == 7 and all(r["title"].endswith("September 2026)") for r in s9) and not [r for r in rows10 if r["key"].startswith("stmt:sbi_")],
              "September's pack carries seven SBI rows with their periods; October's none")
        miss = [r for r in s9 if r["status"] == "missing"]
        check(all("download it from SBI" in r["why"] for r in miss), "a missing SBI row says: download it from SBI, then Add statements")
        words = {r[0]: r[1] for r in cn.execute("SELECT key, ident_words FROM stmt_slot WHERE bank='SBI'")}
        check(words.get("sbi_sav_huf") == "MANOJ KUMAR AGARWAL HUF" and words.get("sbi_sav_bhawna") == "BHAWNA AGARWAL",
              "the real slots carry the holders' words")
        co.close()
        cn.close()
finally:
    shutil.rmtree(T, ignore_errors=True)

print("")
print(("WALK OK" if not failed else "WALK RED") + " S621: %d passed, %d failed" % (len(passed), len(failed)))
sys.exit(0 if not failed else 1)
