#!/usr/bin/env python3
"""walk_s734.py -- kit S734_PACKS_HEAD_STOP (session 394, the parent) . F-1148
Where a statement's head ends, on papers laid out like the real ones (fixtures/: made-up names and numbers), through
pdftotext -layout and the file's own identify_text(). The live file (S729) is loaded beside it as the reference.

    python walk_s734.py <packs.py under test> <live packs.py> <stmt_shelf.py>      exit 0 = WALK OK

The control (the live packs.py as the file under test) must go RED."""
import importlib.util
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")
src, ref, shelf = (os.path.abspath(a) for a in sys.argv[1:4])
T = tempfile.mkdtemp(prefix="s734_")
os.environ.update(FINANCE_DB=os.path.join(T, "finance.db"), STMT_INBOX=os.path.join(T, "inbox"), STMT_VENV_PYTHON=sys.executable,
                  PACKS_DIR=os.path.join(T, "packs"), ASSETS_UPLOADS=os.path.join(T, "up"), PACKS_ENV=os.path.join(T, "none.env"))


def load(path, name):
    d = os.path.join(T, name)
    os.makedirs(d)
    shutil.copy(path, os.path.join(d, "packs.py"))
    shutil.copy(shelf, os.path.join(d, "stmt_shelf.py"))
    sys.path.insert(0, d)
    s = importlib.util.spec_from_file_location(name, os.path.join(d, "packs.py"))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    sys.path.remove(d)
    return m


N = load(src, "packs_new")
O = load(ref, "packs_old")
oks, fails = [], []


def ck(n, c):
    (oks if c else fails).append(n)
    print(("  ok   " if c else "  FAIL ") + n)


def text(name):
    t, _locked = N._file_text(os.path.join(FIX, name))
    return t


KEYS = ("bank", "kind", "tail", "period_from", "period_to", "sbi_type")
icici, sbi = text("icici.pdf"), text("sbi.pdf")
ck("1 the fixtures read (ICICI, SBI)", "ICICI" in icici and "State Bank" in sbi)
hi, hs = N._header(icici), N._header(sbi)
ck("2 ICICI: the head stops before the first row ('1 01/07/2026 ... NEFT-UNION BANK')", "NEFT" not in hi and "Statement period" in hi)
ck("3 SBI: the head stops before the first row ('1 Jul 2026 ... UNION BANK')", "NEFT" not in hs and "Statement from" in hs)
ck("4 ICICI: the holder words carry no narration", "UNION" not in N.identify_text(icici)["up"])
ck("5 SBI: the holder words carry no narration", "UNION" not in N.identify_text(sbi)["up"])
# a head line that merely begins with a date or a number is not a row (no amount on it)
head_like = ("XYZ Bank\nCustomer : RAM LAL\n01 Jul 2026 to 30 Sep 2026\n12 Civil Lines 243001\n"
             "1 01/07/2026 statement copy\nAccount Number : XXXXXX1111\n05-Jul-2026 NEFT-FOO   0.00   10.00   20.00\n")
h = N._header(head_like)
ck("6 a period line beginning with a date stays in the head", "01 Jul 2026 to 30 Sep 2026" in h)
ck("7 an address beginning with a number stays in the head", "12 Civil Lines" in h)
ck("8 a serial and a date with no amount stays in the head", "statement copy" in h and "Account Number" in h)
ck("9 a d-Mon-yyyy row with an amount ends the head", "NEFT-FOO" not in h)
rows = "1 01.07.2026 IMPS-ABC   1,250.00   9,999.00\n"
ck("10 a serial row with dots and thousands commas ends the head", "IMPS" not in N._header("Bank\nName : A\n" + rows))
# nothing else moves: every fixture's bank, kind, tail, period and SBI type are the live file's
same = []
for f in sorted(os.listdir(FIX)):
    t = text(f)
    if not t:
        continue
    a, b = O.identify_text(t), N.identify_text(t)
    same.append(all(a.get(k) == b.get(k) for k in KEYS))
ck("11 every readable fixture (%d): bank, kind, tail, period, SBI type unchanged" % len(same), same and all(same))
ck("12 the old rule's rows still end the head (dd-mm-yyyy, B/F, pipe)",
   "ROW" not in N._header("Bank\nName : A\n05-07-2026 ROW 1.00\n") and "ROW" not in N._header("Bank\nB/F ROW\n")
   and "ROW" not in N._header("Bank\n123456|ROW\n"))
# the cold review's lines: a head line that is not a row never ends the head
keep = ("1 Jul 2026 to 30.09.2026", "06 Nov 2026 14.32.05",
        "01 Jul 2026 to 30 Sep 2026   Interest Rate(% p.a.) : 8.50",
        "1-Jul-2026 to 30-Sep-2026  Opening Balance 1,234.00", "15 Aug, 2026  04 Sep, 2026  12,345.00  617.00",
        "1 01.07.2026 to 30.09.2026")
ck("13 none of six head-like lines (a period, a time, a rate, an opening balance, a card summary) ends the head",
   all(k in N._header("Bank\nName : A\n" + k + "\nAccount Number : XXXX1111\n") for k in keep))
ck("14 an HDFC row with a two-digit year ends the head", "UPI-XYZ" not in N._header(
   "HDFC BANK\nName : A\n03/09/26  UPI-XYZ-PAYMENT  03/09/26  0.00  250.00  9,750.00\n"))
ck("15 a row ending 'Cr' ends the head", "SALARY" not in N._header("Bank\nName : A\n2 Jul 2026 NEFT SALARY 5,000.00 Cr\n"))
shutil.rmtree(T, ignore_errors=True)
n = len(oks) + len(fails)
print("WALK OK %d/%d" % (n, n) if not fails else "WALK RED %d of %d failed" % (len(fails), n))
sys.exit(0 if not fails else 1)
