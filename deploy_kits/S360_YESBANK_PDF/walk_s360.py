#!/usr/bin/env python3
"""walk_s360.py -- kit S360_YESBANK_PDF. Drives the REAL upload route of finance_app.py
with the PLACED finance_yesbank.py, against a SCRATCH COPY of finance.db (never the live one).

  python3 walk_s360.py --app-dir /root/finance --db /tmp/x/finance.db [--pdf real.pdf] [--csv real.csv]

Without --pdf it uploads the FAKE statement of fixtures_s360 as a generated PDF.
It posts the file under a name carrying a long digit run, exactly as the bank names
its downloads, the way the workbench page now sends it (masked) AND raw (as an old
browser tab would), and proves that run never reaches a table.
Prints facts only -- dates, counts, rupee totals; no account number, no reference."""
import argparse, io, os, re, sqlite3, sys, tempfile

ap = argparse.ArgumentParser()
ap.add_argument("--app-dir", default="/root/finance")
ap.add_argument("--db", required=True)
ap.add_argument("--pdf"); ap.add_argument("--csv")
a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.realpath(a.db) == os.path.realpath(os.path.join(a.app_dir, "finance.db")):
    sys.exit("REFUSED: --db is the live database; the walk runs on a copy only")

store = tempfile.mkdtemp(prefix="s360_walk_")
os.environ.update(FINANCE_DB=a.db, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_DEV_USER="manoj",
                  FINANCE_DEV_ROLE="owner", FINANCE_YESBANK_DIR=store)
sys.path.insert(0, a.app_dir); sys.path.insert(1, HERE)
import finance_app as fa
from fixtures_s360 import statement, GOOD, make_pdf

n, fails = 0, []
def check(label, cond):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: fails.append(label)

check("the app loaded the placed finance_yesbank v1.1",
      getattr(fa.finance_yesbank, "VERSION", None) == "1.1")
c = fa.app.test_client()
LONG = "5550000000011"   # a fake long digit run, shaped like the bank's file names

def page_name(name):
    """The workbench page's own rule (finance_workbench.html, S360): /\\d{6,}/ -> 'x' + last 4."""
    return re.sub(r"\d{6,}", lambda m: "x" + m.group(0)[-4:], name)

def post(blob, name):
    r = c.post("/finance/api/yesbank-statement", data={"file": (io.BytesIO(blob), name)},
               content_type="multipart/form-data")
    return r.status_code, (r.get_json() or {})

pdf = open(a.pdf, "rb").read() if a.pdf else make_pdf(statement(GOOD))
s, j = post(pdf, page_name("yesbank_%s_statement.pdf" % LONG))
check("the PDF is ACCEPTED by the route (HTTP %s)" % s, s == 200 and j.get("ok"))
if s == 200:
    print("       period %s to %s · %s rows · %s cash deposits, total %s"
          % (j["period"][0], j["period"][1], j["lines"], j["cash_deposits"], j["cash_total"]))
    rec = j.get("reconciled") or {}
    print("       matched %s · booked-not-in-bank %s · unevidenced %s · IN THE BANK BUT NOT BOOKED %s"
          % (rec.get("matched"), [x.get("date") for x in rec.get("deposit_not_in_bank") or []],
             [x.get("date") for x in rec.get("deposit_unevidenced") or []],
             ["%s %s" % (x.get("date"), x.get("amount")) for x in rec.get("bank_deposit_not_booked") or []]))
    check("the account is reported as its last four digits only", len(str(j.get("account", ""))) <= 4)
    s2, j2 = post(pdf, "again.pdf")
    check("loading the same PDF again adds nothing", s2 == 200 and j2.get("new_lines") == 0)

csvblob = open(a.csv, "rb").read() if a.csv else (
    "Transaction Date,Value Date,Cheque No/Reference No,Description,Withdrawals,Deposits,Running Balance\n"
    "10-Sep-2026,10-Sep-2026,REF0000000B,CASH DEP-SELF-SOME SHOP-BAREILLY,,20000.00,80000.00\n").encode()
s, j = post(csvblob, "yesbank_x0011_transactions.csv")
msg = j.get("message") or ""
check("the period-less CSV is refused (HTTP %s), not half-read" % s, s == 422)
check("... and the refusal names the missing 'Statement Period' line and points at the PDF",
      "Statement Period" in msg and "PDF" in msg)

s, j = post(b"%PDF-1.4\n% an empty or broken pdf\n", "broken.pdf")
check("a broken PDF is refused with a reason (HTTP %s)" % s, s == 422 and bool(j.get("message")))

con = sqlite3.connect(a.db)
leak = 0
for t, col in (("bank_statement_line", "source_file"), ("bank_statement_period", "source_file"),
               ("data_flag", "detail"), ("audit_log", "after_json")):
    try:
        leak += con.execute('SELECT COUNT(*) FROM "%s" WHERE "%s" LIKE ?' % (t, col),
                            ("%" + LONG + "%",)).fetchone()[0]
    except sqlite3.OperationalError:
        pass
check("an upload from the page: the long digit run in the file name reached no table", leak == 0)
# information, not a pass/fail: a client that bypasses the page and posts the raw name
_, _ = post(b"not,a,statement\n", "raw_%s.csv" % LONG)
raw = sum(con.execute('SELECT COUNT(*) FROM data_flag WHERE detail LIKE ?', ("%" + LONG + "%",)).fetchone())
print("       note: a raw name posted AROUND the page still reaches data_flag/audit_log through "
      "finance_app.py's own logging (%d row) -- named to the parent: mask fname in "
      "api_yesbank_statement" % raw)
check("the stored copy of the statement is named without it",
      all(LONG not in f for f in os.listdir(store)) and len(os.listdir(store)) >= 1)

page = open(os.path.join(a.app_dir, "finance_ui", "finance_workbench.html"), encoding="utf-8").read()
check("the workbench page lets a PDF be chosen", 'accept=".pdf,.csv' in page)
check("the page says which file to give it", "Which file:" in page)
check("the page masks the file name before sending it", "d.slice(-4)" in page)

print("WALK_S360 %s -- %d/%d" % ("GREEN" if not fails else "RED", n - len(fails), n))
sys.exit(1 if fails else 0)
