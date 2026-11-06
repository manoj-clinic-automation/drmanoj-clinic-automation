#!/usr/bin/env python3
"""walk_s728.py -- kit S728 (session 390, the parent). The Zerodha papers on a made-up shelf, through the real shelf steps of the
file under test: PDFs laid out as the real ones are (pdftotext -layout), the locked one opened by stmt_shelf.py unlock after the
password is typed, the quarter's cells read back.
   python walk_s728.py <packs.py under test> <stmt_shelf.py>          exit 0 = WALK OK
   (python walk_s728.py --fixtures  builds fixtures/ -- needs reportlab and qpdf; the kit ships them built)
The control (the live packs.py) must go RED."""
import importlib.util, os, shutil, sqlite3, subprocess, sys, tempfile

BUILD = sys.argv[1:2] == ["--fixtures"]
if BUILD:
    sys.argv[1:] = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "packs.py"),
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "orig", "stmt_shelf.py")]
src, shelf = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")    # made-up papers, built once by make_fixtures_s728.py
T = tempfile.mkdtemp(prefix="s728_")
FIN = os.path.join(T, "finance")
os.makedirs(FIN)
shutil.copy(src, os.path.join(FIN, "packs.py"))
shutil.copy(shelf, os.path.join(FIN, "stmt_shelf.py"))
os.environ.update(FINANCE_DB=os.path.join(T, "finance.db"), STMT_INBOX=os.path.join(T, "inbox"), STMT_VENV_PYTHON=sys.executable,
                  PACKS_DIR=os.path.join(T, "packs"), ASSETS_UPLOADS=os.path.join(T, "up"), PACKS_ENV=os.path.join(T, "none.env"))
sys.path.insert(0, FIN)
s = importlib.util.spec_from_file_location("packs", os.path.join(FIN, "packs.py"))
P = importlib.util.module_from_spec(s)
s.loader.exec_module(P)
oks, fails = [], []


def ck(n, c):
    (oks if c else fails).append(n)
    print(("  ok   " if c else "  FAIL ") + n)


def pdf(name, lines, pw=None):
    fx = os.path.join(FIX, name)
    if BUILD:
        from reportlab.lib.pagesizes import landscape, A3            # noqa: PLC0415
        from reportlab.pdfgen import canvas                           # noqa: PLC0415
        os.makedirs(FIX, exist_ok=True)
        c = canvas.Canvas(fx, pagesize=landscape(A3))
        c.setFont("Courier", 7)
        y = 800
        for ln in lines:
            c.drawString(20, y, ln)
            y -= 10
        c.save()
        if pw:
            subprocess.run(["qpdf", "--encrypt", pw, pw, "256", "--", fx, fx + ".enc"], check=True)
            os.replace(fx + ".enc", fx)
    p = os.path.join(T, name)
    shutil.copy(fx, p)
    return p


PAD = " " * 70
HEAD = lambda ucc, name: ["     " + ucc, "     " + name + PAD + "Zerodha Broking Limited",
                          "     " + PAD + "  #153/154, 4th Cross, JP Nagar 4th Phase,", "     PAN: XXXXX0000X" + PAD + "Bengaluru, Karnataka, India",
                          "     UCC: " + ucc, ""]
ACCT = lambda ucc, name: HEAD(ucc, name) + [
    "From Date: 2026-07-04" + PAD + "SEBI REGN.No.: INZ000000000", "To Date: 2026-10-16",
    "Sr. No       Cost Center        Voc. No         Voc. date            Particular                                   Debit      Credit",
    "1        NSE-EQ - Z        JV-26/27-20010   2026-07-18      AMC for Demat Account for 12-03-2026 to 10-06-2026     88.50",
    "15       NSE-EQ - Z        BR-26/27-12086   2026-09-20      Funds added using payment gateway from HDFC BANK XXXXXXXX9012        5000.00",
    "18       NSE-EQ - Z        BP-26/27-27011   2026-10-16      Funds transferred back as part of quarterly settlement      4911.50"]
RET = lambda ucc, name: HEAD(ucc, name) + [
    "Retention Date: 2026-10-16" + PAD + "SEBI REGN.No.: INZ000000000", "Retention Statement as on 2026-10-16",
    "Unencumbered balance in the client ledger (after reversing value of unsettled bills if any)", "(D) Retention of Funds",
    "Total funds retained from client                         0.00"]
SOT = HEAD("ZZ7777", "BHAWNA AGARWAL") + [
    "STATEMENT OF TRANSACTIONS FOR THE PERIOD FROM 01-07-2026 TO 30-09-2026", "DP ID: IN000000  Client ID: 00000000",
    "ISIN           Security                Date         Debit    Credit   Balance", "INE000A01010   SOME LTD EQ            2026-08-03   0        10       10"]
CNOTE = HEAD("AB1234", "MANOJ KUMAR AGARWAL") + ["CONTRACT NOTE CUM TAX INVOICE", "Trade Date: 2026-08-03", "Settlement No: 2026150",
                                                 "Securities Transaction Tax   12.00"]
HDFC = ["HDFC BANK LIMITED", "Statement of account", "MRS BHAWNA AGARWAL", "SAVINGS ACCOUNT", "Account No : XXXXXXXXXX4321",
        "Statement From : 01/09/2026 To : 30/09/2026",
        "03/09/2026  NEFT-ZERODHA BROKING LIMITED-PAYOUT     0.00   4911.50   99000.00"]

P.ensure(sqlite3.connect(os.environ["FINANCE_DB"]))
con = sqlite3.connect(os.environ["FINANCE_DB"])
con.row_factory = sqlite3.Row
files = [(133, "2026-10-21_AB1234-account.pdf", pdf("a1.pdf", ACCT("AB1234", "MANOJ KUMAR AGARWAL"))),
         (134, "2026-10-21_AB1234-retention.pdf", pdf("r1.pdf", RET("AB1234", "MANOJ KUMAR AGARWAL"))),
         (135, "2026-10-21_ZZ7777-account.pdf", pdf("a2.pdf", ACCT("ZZ7777", "BHAWNA AGARWAL"))),
         (136, "2026-10-21_ZZ7777-retention.pdf", pdf("r2.pdf", RET("ZZ7777", "BHAWNA AGARWAL"))),
         (132, "2026-10-19_ZZ7777-sot.pdf", pdf("s2.pdf", SOT, pw="walk-only-pw")),
         (137, "2026-08-03_AB1234-contract-note.pdf", pdf("c1.pdf", CNOTE))]
for fid, name, lp in files:
    con.execute("INSERT INTO stmt_file (id, drive_id, name, folder, local_path, mtime) VALUES (?,?,?,?,?,?)",
                (fid, "drv%d" % fid, name, "bank", lp, "2026-10-21T10:00:00"))
con.commit()

print("-- 1  the head reads (the real layout, pdftotext -layout)")
txt = {fid: P._file_text(lp)[0] for fid, _n, lp in files if fid != 132}
i133, i134, i137 = P.identify_text(txt[133]), P.identify_text(txt[134]), P.identify_text(txt[137])
ck("1a the account statement is Zerodha's, its own kind, no tail (the HDFC number in its narration is not taken)",
   (i133["bank"], i133.get("sbi_type"), i133["tail"]) == ("ZERODHA", "z_account", ""))
ck("1b the holder is the line left of 'Zerodha Broking Limited'", i133["holder"] == "MANOJ KUMAR AGARWAL")
ck("1c its period is From Date -> To Date", (i133["period_from"], i133["period_to"]) == ("2026-07-04", "2026-10-16"))
ck("1d the retention statement: its kind, dated the day it was made", (i134.get("sbi_type"), i134["period_from"], i134["period_to"]) == ("z_retention", "2026-10-16", "2026-10-16"))
ck("1e a contract note is Zerodha's but none of the three (no slot takes it)", (i137["bank"], i137.get("sbi_type")) == ("ZERODHA", "z_other"))
hd = P.identify_text(P._file_text(pdf("h.pdf", HDFC))[0])
ck("1f an HDFC statement whose narration names Zerodha stays HDFC's", hd["bank"] == "HDFC")
ICICI = ("ICICI Bank Limited\nYour Details With Us:\nMANOJ KUMAR AGARWAL\nAccount Number XXXXXXXX1234   Savings Account\n"
         "Statement period 01/07/2026 to 30/09/2026\nS No.  Value Date  Transaction Date  Cheque Number  Transaction Remarks\n"
         "1  01/07/2026  01/07/2026  -  NEFT-ZERODHA BROKING LTD-PAYOUT  0.00  50000.00  150000.00\n")
SBI = ("State Bank of India\nAccount Name : MANOJ KUMAR AGARWAL\nAccount Number : XXXXXXX5678\nStatement from 01 Jul 2026 to 30 Sep 2026\n"
       "Txn Date  Value Date  Description  Debit  Credit  Balance\n1 Jul 2026  1 Jul 2026  BY TRANSFER-NEFT ZERODHA BROKING LIMITED  -  5000.00\n")
ic, sb = P.identify_text(ICICI), P.identify_text(SBI)
ck("1g an ICICI statement with a Zerodha row in its first lines stays ICICI's, its tail kept", (ic["bank"], ic["tail"]) == ("ICICI", "1234"))
ck("1h an SBI statement with a Zerodha row stays SBI's", sb["bank"] == "SBI")
zr = P.identify_text("BHAVNA AGARWAL     ZERODHA BROKING LIMITED\nUCC: ZZ7777\nRetention Statement as on 03-Oct-2026\n")
ck("1i a retention statement dated '03-Oct-2026', the holder spelt BHAVNA: read, folded", (zr["bank"], zr["period_to"], zr["holder"]) == ("ZERODHA", "2026-10-03", "BHAWNA AGARWAL"))
cn = P.identify_text("MANOJ KUMAR AGARWAL     Zerodha Broking Limited\nTax P&L statement\nSecurities Transaction Tax  120.00\n")
ck("1j a P&L paper that names 'Securities Transaction Tax' is not a statement of transactions", cn.get("sbi_type") == "z_other")

print("-- 2  the shelf places them")
r = P.process_inbox(con)
row = lambda fid: dict(con.execute("SELECT f.*, s.key FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.id=?", (fid,)).fetchone())
want = {133: "zerodha_acct_manoj", 134: "zerodha_ret_manoj", 135: "zerodha_acct_bhawna", 136: "zerodha_ret_bhawna"}
ck("2a the four open papers go to their four slots", all(row(k)["key"] == v for k, v in want.items()))
ck("2b each is filed as read (the broker's statement)", all(row(k)["read_status"] == "read" for k in want))
ck("2c no tail is learned onto a Zerodha slot", not con.execute("SELECT 1 FROM stmt_slot WHERE bank='ZERODHA' AND COALESCE(ident_tail,'')<>''").fetchone())
ck("2d the locked statement of transactions waits, unplaced, with the password note", row(132)["slot_id"] is None and row(132)["locked"] == 1)
ck("2e the contract note waits unplaced (the owner's one tap)", row(137)["slot_id"] is None)
ck("2f 'Zerodha' has its password box", "ZERODHA" in [k for k, _l, _a in P.secret_keys(con)])

print("-- 3  the password typed once opens it")
try:
    body, code = P.set_secret(con, "zerodha", "walk-only-pw", "manoj")
except Exception as ex:                                          # noqa: BLE001
    body, code = repr(ex), 0
ck("3a the password is taken", code == 200 and "walk-only-pw" not in str(body))
ck("3b the paper opened and went to Dr Bhawna's statement of transactions", row(132)["key"] == "zerodha_txn_bhawna" and bool(row(132)["unlocked_path"]))
ck("3c its period is the one it prints", (row(132)["period_from"], row(132)["period_to"]) == ("2026-07-01", "2026-09-30"))

print("-- 4  the quarter's cells")
cs = {c["slot"]: c for c in P.cells(con, "2026-09")}
z = {k: v for k, v in cs.items() if k.startswith("zerodha_")}
E = dict(state="", file=dict(id=None), period_words="", kind="")
g = lambda k: z.get(k) or E                                      # noqa: E731  (the control has no such cell: RED, not a crash)
ck("4a six Zerodha cells in September (the quarter's end)", len(z) == 6)
ck("4b five read, Dr Manoj's statement of transactions empty",
   all(g(k)["state"] == "read" for k in list(want.values()) + ["zerodha_txn_bhawna"]) and g("zerodha_txn_manoj")["state"] == "empty")
ck("4c the paper settled in October is July - September's", (g("zerodha_acct_manoj")["file"] or {}).get("id") == 133 and (g("zerodha_ret_bhawna")["file"] or {}).get("id") == 136)
ck("4d the cell says 'July – September 2026' and the paper's own kind",
   g("zerodha_acct_manoj")["period_words"] == "July – September 2026" and g("zerodha_ret_manoj")["kind"] == "retention statement"
   and g("zerodha_txn_bhawna")["kind"] == "statement of transactions")
ck("4e no Zerodha cell in October (not a quarter's end)", not [c for c in P.cells(con, "2026-10") if c["slot"].startswith("zerodha_")])
dec = {c["slot"]: c for c in P.cells(con, "2026-12")}
ck("4f in December the cells are empty (October's papers are not October - December's)",
   all(dec[k]["state"] == "empty" for k in dec if k.startswith("zerodha_")) and len([k for k in dec if k.startswith("zerodha_")]) == 6)
jun = {c["slot"]: c for c in P.cells(con, "2026-06")}
ck("4g in June the cells are empty too", all(jun[k]["state"] == "empty" for k in jun if k.startswith("zerodha_")))
ck("4h no other slot took a Zerodha paper",
   not con.execute("SELECT 1 FROM stmt_file f JOIN stmt_slot s ON s.id=f.slot_id WHERE f.bank='ZERODHA' AND s.bank<>'ZERODHA'").fetchone())

print("\n%d ok, %d failed" % (len(oks), len(fails)))
print(("WALK OK %d/%d" % (len(oks), len(oks))) if not fails else ("WALK RED (%d failed)" % len(fails)))
sys.exit(0 if not fails else 1)
