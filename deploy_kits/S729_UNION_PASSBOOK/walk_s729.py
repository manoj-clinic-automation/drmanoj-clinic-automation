#!/usr/bin/env python3
"""walk_s729.py -- kit S729 (session 390, the parent). The Union Bank passbooks on a made-up shelf, through the real shelf steps of
the file under test: a scanned passbook (a PDF with no text) added through the Add statements box and filed by the owner's tap, a
Union Bank statement with text placed by itself, the half-year cells read back; bank statements that name Union Bank in a row stay
their banks'.
   python walk_s729.py <packs.py under test> <stmt_shelf.py>          exit 0 = WALK OK
   (python walk_s729.py --fixtures  builds fixtures/ -- needs reportlab; the kit ships them built)
The control (the live packs.py) must go RED."""
import importlib.util, os, shutil, sqlite3, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
BUILD = sys.argv[1:2] == ["--fixtures"]
if BUILD:
    sys.argv[1:] = [os.path.join(HERE, "packs.py"), os.path.join(HERE, "..", "..", "orig", "stmt_shelf.py")]
src, shelf = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
T = tempfile.mkdtemp(prefix="s729_")
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


def pdf(name, lines, scan=False):
    fx = os.path.join(FIX, name)
    if BUILD:
        from reportlab.lib.pagesizes import A4                        # noqa: PLC0415
        from reportlab.pdfgen import canvas                           # noqa: PLC0415
        os.makedirs(FIX, exist_ok=True)
        c = canvas.Canvas(fx, pagesize=A4)
        if scan:                                                      # a scanned page: shapes, no text layer
            for i in range(30):
                c.rect(40, 780 - i * 22, 500, 14, stroke=1, fill=0)
        else:
            c.setFont("Courier", 8)
            y = 800
            for ln in lines:
                c.drawString(20, y, ln)
                y -= 11
        c.save()
    return open(fx, "rb").read()


UNION = ["UNION BANK OF INDIA", "BAREILLY CIVIL LINES BRANCH", "Customer Name : MANOJ KUMAR AGARWAL", "Account Type : SAVINGS",
         "Account No : XXXXXXXXXX0001", "Statement Period : 01/04/2026 to 30/09/2026",
         "Date        Particulars                         Withdrawal   Deposit   Balance",
         "02/04/2026  NEFT-ICICI BANK-SALARY                  0.00     5000.00   15000.00"]
ICICI = ["ICICI Bank Limited", "Your Details With Us:", "MANOJ KUMAR AGARWAL", "Account Number XXXXXXXX1234   Savings Account",
         "Statement period 01/07/2026 to 30/09/2026", "S No.  Value Date  Transaction Date  Remarks",
         "1  01/07/2026  01/07/2026  NEFT-UNION BANK OF INDIA-TRF  0.00  50000.00  150000.00"]
SBI = ["State Bank of India", "Account Name : MANOJ KUMAR AGARWAL", "Account Number : XXXXXXX5678",
       "Statement from 01 Jul 2026 to 30 Sep 2026", "Txn Date  Value Date  Description  Debit  Credit",
       "1 Jul 2026  1 Jul 2026  BY TRANSFER-NEFT UNION BANK OF INDIA  -  5000.00"]

con = sqlite3.connect(os.environ["FINANCE_DB"])
con.row_factory = sqlite3.Row
P.ensure(con)
slot = {r["key"]: r["id"] for r in con.execute("SELECT key, id FROM stmt_slot")}
B_PASS, B_UNION, B_ICICI, B_SBI = pdf("passbook.pdf", [], scan=True), pdf("union.pdf", UNION), pdf("icici.pdf", ICICI), pdf("sbi.pdf", SBI)

print("-- 1  the heads")
txt = lambda b: P._file_text(os.path.join(FIX, b))[0]                     # noqa: E731
iu, ii, isb = P.identify_text(txt("union.pdf")), P.identify_text(txt("icici.pdf")), P.identify_text(txt("sbi.pdf"))
ck("1a a Union Bank statement with text is Union Bank's, its period read", (iu["bank"], iu["period_from"], iu["period_to"]) == ("UNION", "2026-04-01", "2026-09-30"))
ck("1b an ICICI statement whose row names Union Bank stays ICICI's", ii["bank"] == "ICICI")
ck("1c an SBI statement whose row names Union Bank stays SBI's", isb["bank"] == "SBI")
ck("1d the scanned passbook has no text", txt("passbook.pdf").strip() == "")

print("-- 2  added through the Add statements box")
body = P.add_uploads(con, [("union passbook bhawna.pdf", B_PASS), ("union estatement.pdf", B_UNION)], "manoj")
row = lambda fid: dict(con.execute("SELECT f.*, s.key FROM stmt_file f LEFT JOIN stmt_slot s ON s.id=f.slot_id WHERE f.id=?", (fid,)).fetchone())   # noqa: E731
ids = [f["id"] for f in body["files"]]
pb, ue = ids[0], ids[1]
ck("2a the statement with text went to Dr Manoj's Union Bank cell by itself, read", (row(ue)["key"], row(ue)["read_status"]) == ("union_sav_manoj", "read"))
ck("2b the scanned passbook waits for the owner's tap", row(pb)["slot_id"] is None)
r, code = P.assign(con, pb, slot.get("union_sav_bhawna", -1), "manoj") if "union_sav_bhawna" in slot else ({}, 0)
ck("2c the tap files it as Dr Bhawna's passbook, read", code == 200 and (row(pb)["key"], row(pb)["read_status"]) == ("union_sav_bhawna", "read"))
ck("2d it is dated the day it was added", row(pb)["period_to"] == str(row(pb)["fetched_at"])[:10])

print("-- 3  the half-year cells")
con.execute("UPDATE stmt_file SET period_to='2026-11-05', fetched_at='2026-11-05T10:00:00' WHERE id=?", (pb,))   # printed in November
con.commit()
E = dict(state="", file=None, period_words="")
sep = {c["slot"]: c for c in P.cells(con, "2026-09")}
g = lambda m, k: m.get(k) or E                                                     # noqa: E731
ck("3a two Union Bank cells in September, both read", g(sep, "union_sav_manoj")["state"] == "read" and g(sep, "union_sav_bhawna")["state"] == "read")
ck("3b they say 'April – September 2026'", g(sep, "union_sav_bhawna")["period_words"] == "April – September 2026")
ck("3c a passbook printed in November is April - September's", (g(sep, "union_sav_bhawna")["file"] or {}).get("id") == pb)
ck("3d no copies list on a Union Bank cell", not g(sep, "union_sav_manoj").get("copies"))
ck("3e no Union Bank cell in October or December", not [c for m in ("2026-10", "2026-12") for c in P.cells(con, m) if c["slot"].startswith("union_")])
mar = {c["slot"]: c for c in P.cells(con, "2027-03")}
ck("3f in March 2027 the cells are empty (nothing printed January - June yet)", g(mar, "union_sav_bhawna")["state"] == "empty" and "union_sav_manoj" in mar)
con.execute("UPDATE stmt_file SET period_to='2027-01-12' WHERE id=?", (pb,))
con.commit()
mar = {c["slot"]: c for c in P.cells(con, "2027-03")}
sep = {c["slot"]: c for c in P.cells(con, "2026-09")}
ck("3g printed in January it is October - March's, and April - September is empty again",
   (g(mar, "union_sav_bhawna")["file"] or {}).get("id") == pb and g(sep, "union_sav_bhawna")["state"] == "empty")

print("-- 4  the pack and the mail-road check")
ck("4a Union Bank is a hand-added bank", "UNION" in getattr(P, "MANUAL_BANKS", ()))
try:
    rows, _att = P.pack_rows(con, "2026-09", light=True)[:2]
    why = " ".join(str(x.get("why") or "") for x in rows)
except Exception as ex:                                                  # noqa: BLE001
    why = "pack_rows: %r" % ex
ck("4b the empty cell says: scan the printed passbook pages, then the Add statements box", "scan the printed passbook pages" in why)
try:
    rd = P.statement_road(con, today=P.dt.date(2026, 10, 12))
    want = len([c for c in P.cells(con, "2026-09") if c["kind"] != "card" and c["bank"] not in ("SBI", "UNION") and c["state"] == "empty"])
    ck("4c the 'no statement by mail' check does not count the Union Bank cells", rd.get("missing") == want)
except Exception as ex:                                                  # noqa: BLE001
    ck("4c the 'no statement by mail' check runs (%r)" % ex, False)

print("\n%d ok, %d failed" % (len(oks), len(fails)))
print(("WALK OK %d/%d" % (len(oks), len(oks))) if not fails else ("WALK RED (%d failed)" % len(fails)))
sys.exit(0 if not fails else 1)
