#!/usr/bin/env python3
"""selftest_s360.py -- kit S360_YESBANK_PDF (F-603).

Proves finance_yesbank v1.1 in three layers, every one with a deliberate failure:
  A. the S186 selftest, unchanged (the CSV path and the reconciler still hold)
  B. the PDF reader on a laid-out statement text built here with FAKE figures:
     reads it, and REFUSES it when a figure is broken in each of the ways the
     proof is meant to catch
  C. a real PDF, generated here in pure Python from the same fake statement,
     read through pdftotext exactly as an upload is (skipped only if pdftotext
     is absent AND --allow-no-pdftotext is given; the installer never gives it)
No real statement, account number or bank reference is in this file.
Usage: python3 selftest_s360.py [path/to/finance_yesbank.py]
"""
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
target = next((a for a in sys.argv[1:] if a.endswith(".py")), os.path.join(HERE, "finance_yesbank.py"))
spec = importlib.util.spec_from_file_location("fyb_under_test", target)
y = importlib.util.module_from_spec(spec); spec.loader.exec_module(y)

checks, fails = 0, []
def ok(label, cond):
    global checks
    checks += 1
    if not cond: fails.append(label)

def refused(label, fn, must=None):
    try:
        fn(); ok(label, False)
    except y.StatementRejected as e:
        ok(label, must is None or must.lower() in str(e).lower())

# ---- A ---------------------------------------------------------------------
ok("A: module is v1.1", getattr(y, "VERSION", "") == "1.1")
ok("A: the S186 selftest is still green", y.selftest() == 0)

# ---- B: a laid-out statement, FAKE figures (fixtures_s360.py) -------------
sys.path.insert(0, HERE)
from fixtures_s360 import statement, row, GOOD, make_pdf
p = y.parse_pdf_text(statement(GOOD))
ok("B: period read", (p["period_from"], p["period_to"]) == ("2026-08-01", "2026-09-20"))
ok("B: account kept as last-4 only", p["account_ref"] == "0011")
ok("B: opening and closing read", (p["opening_p"], p["closing_p"]) == (5000000, 6800000))
ok("B: three rows", len(p["lines"]) == 3)
ok("B: withdrawal in its column", p["lines"][0]["withdrawal_p"] == 1200000 and p["lines"][0]["deposit_p"] == 0)
ok("B: deposit in its column", p["lines"][1]["deposit_p"] == 2000000 and p["lines"][1]["withdrawal_p"] == 0)
ok("B: wrapped description joined", p["lines"][1]["description"].endswith("BAREILLY"))
ok("B: two cash deposits, the tax debit is not one", [l["is_cash_deposit"] for l in p["lines"]] == [0, 1, 1])
ok("B: reference read", p["lines"][2]["reference"] == "REF0000000C")
ok("B: parse_statement sends a %PDF blob to the PDF reader",
   getattr(y.parse_statement, "__code__", None) and "parse_pdf" in y.parse_statement.__code__.co_names)

# the deliberate failures -- each must be REFUSED, and say why
refused("B-neg: no period line", lambda: y.parse_pdf_text(statement(GOOD, period="")), "Period")
refused("B-neg: no closing figure", lambda: y.parse_pdf_text(statement(GOOD).replace("Closing Balance:", "Closing:")), "Closing Balance")
refused("B-neg: a running balance that does not add up",
        lambda: y.parse_pdf_text(statement([GOOD[0], GOOD[1].replace("80,000.00", "81,000.00"), GOOD[2]])), "running balance")
refused("B-neg: a missing row (the chain breaks)", lambda: y.parse_pdf_text(statement([GOOD[0], GOOD[2]])), "running balance")
refused("B-neg: the deposit printed under Withdrawals",
        lambda: y.parse_pdf_text(statement([GOOD[0], row("10 Sep 2026", "REF0000000B", "CASH DEP-SELF-X", "20,000.00", "", "80,000.00"), GOOD[2]])))
refused("B-neg: totals that do not match the rows",
        lambda: y.parse_pdf_text(statement(GOOD, td="31,000.00")), "Total Deposits")
refused("B-neg: a row outside the printed period",
        lambda: y.parse_pdf_text(statement(GOOD, period="Period: 05 Aug 2026 - 20 Sep 2026")), "outside")
refused("B-neg: a row with no running balance",
        lambda: y.parse_pdf_text(statement([GOOD[0], row("10 Sep 2026", "R", "CASH DEP", "", "20,000.00", ""), GOOD[2]])))

# the CSV download without a period: refused, and the message names the rule and the way out
CSV = ("Transaction Date,Value Date,Cheque No/Reference No,Description,Withdrawals,Deposits,Running Balance\n"
       "10-Sep-2026,10-Sep-2026,REF0000000B,CASH DEP-SELF-SOME SHOP-BAREILLY,,20000.00,80000.00\n")
refused("B: a CSV with no Statement Period line is refused", lambda: y.parse_statement(CSV.encode()), "Statement Period")
refused("B: ... and the message points at the PDF", lambda: y.parse_statement(CSV.encode()), "PDF")
csvp = y.parse_statement(("Statement Period,2026-09-01,To,2026-09-20,\n" + CSV).encode())
ok("B: the same CSV WITH a period is read, reference column 'Cheque No/Reference No' included",
   csvp["lines"][0]["reference"] == "REF0000000B" and csvp["lines"][0]["is_cash_deposit"] == 1)

ok("B: mask_name keeps only the last four digits of a long run",
   y.mask_name("yesbank_5550000000011_x.csv") == "yesbank_x0011_x.csv" and y.mask_name("a_12345.pdf") == "a_12345.pdf")
import sqlite3
_c = sqlite3.connect(":memory:")
_c.executescript("""CREATE TABLE bank_statement_line(id INTEGER PRIMARY KEY, account_ref TEXT, txn_date TEXT,
  value_date TEXT, description TEXT, reference TEXT, withdrawal_p INT DEFAULT 0, deposit_p INT DEFAULT 0,
  balance_p INT, is_cash_deposit INT DEFAULT 0, source_file TEXT, sha256 TEXT, ingested_at TEXT,
  UNIQUE(account_ref,txn_date,reference,deposit_p,withdrawal_p));
CREATE TABLE bank_statement_period(id INTEGER PRIMARY KEY, account_ref TEXT, period_from TEXT, period_to TEXT,
  opening_p INT, closing_p INT, source_file TEXT, sha256 TEXT, ingested_at TEXT,
  UNIQUE(account_ref,period_from,period_to));""")
_csv = ("Statement Period,2026-09-01,To,2026-09-20,\n" + CSV).encode()
y.ingest_statement(_c, "yesbank_5550000000011_x.csv", _csv, None)
ok("B: the stored source_file carries no long digit run",
   all("5550000000011" not in (r[0] or "") for r in _c.execute("SELECT source_file FROM bank_statement_line UNION ALL SELECT source_file FROM bank_statement_period")))
ok("B: re-loading the same CSV adds nothing (the reference column is read, so no NULL twins)",
   y.ingest_statement(_c, "again.csv", _csv, None)["new_lines"] == 0)

# ---- C: a real PDF through pdftotext ---------------------------------------
import shutil
if shutil.which("pdftotext"):
    pdf = make_pdf(statement(GOOD))
    rp = y.parse_statement(pdf)
    ok("C: a real PDF read through pdftotext -- 3 rows, 2 cash deposits",
       len(rp["lines"]) == 3 and sum(l["is_cash_deposit"] for l in rp["lines"]) == 2)
    ok("C: ... proved against its own totals", rp["closing_p"] == 6800000 and rp["source"] == "pdf")
    bad = make_pdf(statement([GOOD[0], GOOD[1].replace("80,000.00", "81,000.00"), GOOD[2]]))
    refused("C-neg: the same PDF with one balance altered is refused", lambda: y.parse_statement(bad), "running balance")
    refused("C-neg: a PDF with no text layer is refused loudly",
            lambda: y.parse_statement(make_pdf("")), "no text")
elif "--allow-no-pdftotext" in sys.argv:
    print("  NOTE: pdftotext absent -- layer C skipped by request")
else:
    ok("C: pdftotext is installed (the PDF path needs it)", False)

print("selftest_s360: %d/%d checks passed" % (checks - len(fails), checks))
for f in fails: print("  FAILED:", f)
print("SELFTEST_S360 GREEN" if not fails else "SELFTEST_S360 RED")
sys.exit(1 if fails else 0)
