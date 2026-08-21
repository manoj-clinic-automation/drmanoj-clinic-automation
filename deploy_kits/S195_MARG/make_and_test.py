#!/usr/bin/env python3
"""Synthesize Marg-layout .xls exports and run guard_and_send.py against them.
Proves the guard on the real parser, offline, without the live sample files."""
import datetime, os, subprocess, sys
import xlwt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "testdata")
os.makedirs(DATA, exist_ok=True)
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
TODAY = datetime.datetime.now(IST).date()

HEADER = ["BILL NO.", "DESCRIPTION", "D.R.", "GROSS AMT.", "DISCOUNT",
          "TAX", "DR/CR", "NET AMT.", "CASH"]


def ddmmyyyy(d):
    return d.strftime("%d-%m-%Y")


def _write(path, rows, ncols=9):
    wb = xlwt.Workbook()
    sh = wb.add_sheet("Sheet1")
    for r, row in enumerate(rows):
        for c in range(ncols):
            v = row[c] if c < len(row) else ""
            if v == "":
                continue
            sh.write(r, c, v)
    wb.save(path)


def build_detail(path, day, include_grand=True, break_arith=False, summary1=False):
    """A single-day Detail export. Two bills: one CASH, one UPI."""
    if summary1:
        rows = [
            ["SANJEEVNI MEDICOS"],
            ["35G/15B Rampur Bagh, Bareilly"],
            ["Phone : 9358008080"],
            ["BILL WISE SALES STATEMENT AS ON %s" % ddmmyyyy(day)],
            ["BILL NO.", "DESCRIPTION", "BILL VALUE"],
            [day.strftime("%d-%m-%Y")],
            ["A0012345", "9519825641 MANOSHA 6503", 1000.00],
        ]
        _write(path, rows, ncols=3)
        return

    # amounts in rupees; xlrd will hand these back as floats -> paise() reads str()
    b1_net, b1_cash = 1000.00, 1000.00          # CASH bill
    b2_net, b2_cash = 500.00, 0.00              # UPI bill (cash 0)
    day_net = b1_net + b2_net
    day_cash = b1_cash + b2_cash
    grand_net = day_net + (0.02 if break_arith else 0.0)   # inject a mismatch

    rows = [
        ["SANJEEVNI MEDICOS"],
        ["35G/15B Rampur Bagh, Bareilly"],
        ["Phone : 9358008080"],
        ["BILL WISE SALES STATEMENT AS ON %s" % ddmmyyyy(day)],
        HEADER,
        [day.strftime("%d-%m-%Y")],
        # BILL NO, DESC, D.R., GROSS, DISC, TAX, DR/CR, NET, CASH
        ["A0012345", "9519825641 MANOSHA 6503", ".CASH", 1000.00, 0.0, 0.0, 0.0, b1_net, b1_cash],
        ["A0012346", "7088144921 UTKARSH GUPTA", ".UPI", 500.00, 0.0, 0.0, 0.0, b2_net, b2_cash],
        ["", "", "DAY TOTAL :", 1500.00, 0.0, 0.0, 0.0, day_net, day_cash],
    ]
    if include_grand:
        rows.append(["Total No. of", "Bills: 2", "GRAND TOTAL :", 1500.00, 0.0, 0.0, 0.0,
                     grand_net, day_cash])
    _write(path, rows)


def run(path, expect):
    p = subprocess.run([sys.executable, os.path.join(HERE, "guard_and_send.py"),
                        path, "--expect", expect, "--json",
                        "--alert", os.path.join(DATA, "guard_alerts.txt")],
                       capture_output=True, text=True)
    out = (p.stdout or p.stderr or "").strip().splitlines()
    return p.returncode, (out[-1] if out else "")


CASES = []


def case(name, expect, want_code):
    CASES.append((name, expect, want_code))


# --- build fixtures ----------------------------------------------------------
good = os.path.join(DATA, "REPORT_good_today.XLS")
build_detail(good, TODAY)

trunc = os.path.join(DATA, "REPORT_truncated.XLS")
build_detail(trunc, TODAY, include_grand=False)

wrongdate = os.path.join(DATA, "REPORT_wrongday.XLS")
build_detail(wrongdate, TODAY - datetime.timedelta(days=3))

badarith = os.path.join(DATA, "REPORT_badarith.XLS")
build_detail(badarith, TODAY, break_arith=True)

summ = os.path.join(DATA, "REPORT_summary1.XLS")
build_detail(summ, TODAY, summary1=True)

# --- expectations ------------------------------------------------------------
print("Testing guard_and_send.py against synthetic Marg exports (today=%s)\n" % TODAY)
results = [
    ("valid single-day, expect today", good, "today", 0),
    ("valid single-day, expect yesterday (date mismatch)", good, "yesterday", 2),
    ("valid single-day, expect any", good, "any", 0),
    ("TRUNCATED (no GRAND TOTAL), expect today", trunc, "today", 2),
    ("wrong business date, expect today", wrongdate, "today", 2),
    ("wrong business date, pinned to its real date", wrongdate,
     (TODAY - datetime.timedelta(days=3)).isoformat(), 0),
    ("arithmetic mismatch (grand != days), expect today", badarith, "today", 2),
    ("Summary-1 (no CASH column), expect today", summ, "today", 2),
]

passed = 0
for name, path, expect, want in results:
    code, line = run(path, expect)
    ok = code == want
    passed += ok
    print("  [%s] %-52s exit=%d (want %d)" % ("PASS" if ok else "FAIL", name, code, want))
    print("        %s" % line)

print("\n%d/%d cases passed" % (passed, len(results)))
sys.exit(0 if passed == len(results) else 1)
