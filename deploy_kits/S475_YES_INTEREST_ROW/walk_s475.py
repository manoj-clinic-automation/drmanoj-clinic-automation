#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s475.py -- S475_YES_INTEREST_ROW (session 293, 04-Oct-2026, F-720). Hermetic (F-709): the two readers copied to a
scratch folder twice (old / new), fed made-up statement TEXT in each bank layout (no PDF, no database, no network, no live
file opened). Nothing on the box is touched.

  1. the branch layout, the bank's quarter-end interest row (TXN 01-OCT, VALUE 30-SEP) inside September's totals:
     SHOWN refused on the old reader ('falls outside the printed period'); READ on the new one, every row and figure as
     printed; the same statement WITHOUT that row reads the same on both (nothing else changed).
  2. the e-statement PDF layout, the same row: SHOWN refused on the old, READ on the new.
  3. still refused on the new reader: a row whose txn AND value dates both fall outside (the arithmetic made to pass);
     a row whose value date is missing is judged by its txn date; the arithmetic proofs refuse exactly as before.
  4. a row with its txn date inside and its value date outside (a cheque clearing after the month) is accepted by both.
Last line: WALK_S475 GREEN|RED.
   usage: walk_s475.py --apply apply_s475.py --finance /root/finance
"""
import argparse
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

FAILS, CHECKS = [], 0


def check(name, ok, detail=""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(name)
        print("  FAIL %s %s" % (name, str(detail)[:400]))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- the branch layout (yes_branch.py)
def branch_text(rows, foot):
    """rows: (txn, value, desc, ref, dr, cr, bal) in the branch's own print; foot: (opening, debits, credits, closing)."""
    hdr = "TXN DATE     VALUE DATE   DESCRIPTION                         REFERENCE      DEBITS         CREDITS        BALANCE"
    out = ["STATEMENT OF ACCOUNT", "Branch:  WALKTOWN", "A/C type: SA - SAVINGS EXCLUSIVE",
           "WALK HOLDER ONE                                   OD Limit: 0", "A/C Number: 000000001234",
           "Period : 01-SEP-2026  To  30-SEP-2026", hdr]
    for txn, val, desc, ref, dr, cr, bal in rows:
        out.append("%-12s %-12s %-35s %-14s %-14s %-14s %s" % (txn, val, desc, ref, dr, cr, bal))
    o, d, c, cl = foot
    out += ["Opening Balance : %s C" % o, "Total Debit Amt  : %s" % d, "Total Credit Amt : %s     Dr Count : 1" % c,
            "Closing Balance  : %s     Cr Count : 2" % cl, "******END OF STATEMENT******",
            "calling on our YES TOUCH toll free number"]
    return "\n".join(out) + "\n"


BF = ("01-SEP-2026", "01-SEP-2026", "B/F", "", "0.00", "0.00", "1,000.00")
R1 = ("05-SEP-2026", "05-SEP-2026", "CHQ DEP BANK 05-SEP-26 WALKTOWN", "000123", "0.00", "500.00", "1,500.00")
R2 = ("12-SEP-2026", "12-SEP-2026", "ATM WDL", "000124", "200.00", "0.00", "1,300.00")
INT = ("01-OCT-2026", "30-SEP-2026", "CREDIT INTEREST CAPITALISED ON SB", "", "0.00", "12.00", "1,312.00")
BOTH_OUT = ("02-OCT-2026", "02-OCT-2026", "SOMETHING LATE", "", "0.00", "12.00", "1,312.00")
CLEARING = ("30-SEP-2026", "02-OCT-2026", "CTS CLG CHEQUE", "000125", "0.00", "12.00", "1,312.00")

B_WITH = branch_text([BF, R1, R2, INT], ("1,000.00", "200.00", "512.00", "1,312.00"))
B_WITHOUT = branch_text([BF, R1, R2], ("1,000.00", "200.00", "500.00", "1,300.00"))
B_BOTH_OUT = branch_text([BF, R1, R2, BOTH_OUT], ("1,000.00", "200.00", "512.00", "1,312.00"))
B_CLEARING = branch_text([BF, R1, R2, CLEARING], ("1,000.00", "200.00", "512.00", "1,312.00"))
B_BAD_SUM = branch_text([BF, R1, R2, INT], ("1,000.00", "200.00", "512.00", "1,399.00"))


# ---------------------------------------------------------------- the e-statement PDF layout (finance_yesbank.parse_pdf_text)
def estmt_text(rows, foot):
    """rows: (txn, value, ref, desc, kind, amount, balance) with kind 'wd' | 'dep'; amounts right-aligned under the
    header words the way pdftotext -layout prints them."""
    hdr = "Date          Value Date    Cheque No/Reference No   Transaction details                 Withdrawals          Deposits    Running Balance"
    wd_end, dep_end, bal_end = hdr.index("Withdrawals") + len("Withdrawals"), hdr.index("Deposits") + len("Deposits"), hdr.index("Running Balance") + len("Running Balance")
    out = ["Statement of account: 000000005678", "Period: 1 Sep 2026 - 30 Sep 2026", "", hdr]
    for txn, val, ref, desc, kind, amt, bal in rows:
        left = "%-13s %-13s %-24s %s" % (txn, val, ref, desc)
        end = wd_end if kind == "wd" else dep_end
        line = left + " " * max(1, end - len(left) - len(amt)) + amt
        line = line + " " * max(1, bal_end - len(line) - len(bal)) + bal
        out.append(line)
    o, w, d, c = foot
    out += ["", "Opening Balance: %s" % o, "Total Withdrawals: %s" % w, "Total Deposits: %s" % d, "Closing Balance: %s" % c]
    return "\n".join(out) + "\n"


E1 = ("5 Sep 2026", "5 Sep 2026", "000123", "CHQ DEP WALKTOWN", "dep", "500.00", "1,500.00")
E2 = ("12 Sep 2026", "12 Sep 2026", "000124", "ATM WDL", "wd", "200.00", "1,300.00")
EINT = ("1 Oct 2026", "30 Sep 2026", "INT", "CREDIT INTEREST CAPITALISED", "dep", "12.00", "1,312.00")
EBOTH = ("2 Oct 2026", "2 Oct 2026", "LATE", "SOMETHING LATE", "dep", "12.00", "1,312.00")

E_WITH = estmt_text([E1, E2, EINT], ("1,000.00", "200.00", "512.00", "1,312.00"))
E_WITHOUT = estmt_text([E1, E2], ("1,000.00", "200.00", "500.00", "1,300.00"))
E_BOTH_OUT = estmt_text([E1, E2, EBOTH], ("1,000.00", "200.00", "512.00", "1,312.00"))


def refused(fn, text):
    try:
        fn(text)
        return None
    except Exception as ex:                                  # noqa: BLE001
        return str(ex)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True)
    a = ap.parse_args()
    scr = tempfile.mkdtemp(prefix="s475_walk_")
    before = {f: hashlib.md5(open(os.path.join(a.finance, f), "rb").read()).hexdigest() for f in ("yes_branch.py", "finance_yesbank.py")}
    try:
        old, new = os.path.join(scr, "old"), os.path.join(scr, "new")
        os.makedirs(old); os.makedirs(new)
        for f in ("yes_branch.py", "finance_yesbank.py"):
            shutil.copy2(os.path.join(a.finance, f), os.path.join(old, f))
            shutil.copy2(os.path.join(a.finance, f), os.path.join(new, f))
        r = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "yes_branch.py"), os.path.join(new, "finance_yesbank.py")],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check("apply on scratch", r.returncode == 0, r.stderr.decode()[-300:])
        YB_OLD, YB_NEW = load(os.path.join(old, "yes_branch.py"), "yb_old"), load(os.path.join(new, "yes_branch.py"), "yb_new")
        FY_OLD, FY_NEW = load(os.path.join(old, "finance_yesbank.py"), "fy_old"), load(os.path.join(new, "finance_yesbank.py"), "fy_new")

        # 1 the branch layout
        check("1 the fixture is the branch layout", YB_NEW.is_branch(B_WITH) and YB_OLD.is_branch(B_WITH))
        why = refused(YB_OLD.parse_text, B_WITH)
        check("1 SHOWN on the old reader: the interest row refused", why is not None and "falls outside the printed period" in why and "2026-10-01" in why, why)
        p = None
        why = refused(lambda t: globals().__setitem__("_p", YB_NEW.parse_text(t)), B_WITH)
        check("1 the new reader reads it", why is None, why)
        p = globals().get("_p")
        if p:
            check("1 period as printed", (p["period_from"], p["period_to"]) == ("2026-09-01", "2026-09-30"))
            check("1 three rows (B/F is not a row)", len(p["lines"]) == 3, len(p["lines"]))
            check("1 the interest row kept with both dates", p["lines"][-1]["txn_date"] == "2026-10-01" and p["lines"][-1]["value_date"] == "2026-09-30")
            check("1 opening and closing as printed", (p["opening_p"], p["closing_p"]) == (100000, 131200))
            check("1 account last four only", p["account_ref"] == "1234")
        po, pn = refused(lambda t: globals().__setitem__("_po", YB_OLD.parse_text(t)), B_WITHOUT), refused(lambda t: globals().__setitem__("_pn", YB_NEW.parse_text(t)), B_WITHOUT)
        check("1 without the row: both readers read it", po is None and pn is None, (po, pn))
        check("1 without the row: old and new give the same result", globals().get("_po") == globals().get("_pn"))
        check("1 the module still names its version", YB_NEW.VERSION == YB_OLD.VERSION)

        # 2 the e-statement layout
        why = refused(FY_OLD.parse_pdf_text, E_WITH)
        check("2 SHOWN on the old e-statement reader: the interest row refused", why is not None and "falls outside the printed period" in why and "2026-10-01" in why, why)
        why = refused(lambda t: globals().__setitem__("_e", FY_NEW.parse_pdf_text(t)), E_WITH)
        check("2 the new e-statement reader reads it", why is None, why)
        e = globals().get("_e")
        if e:
            check("2 three rows, period, closing as printed", len(e["lines"]) == 3 and (e["period_from"], e["period_to"]) == ("2026-09-01", "2026-09-30") and e["closing_p"] == 131200, (len(e["lines"]), e.get("closing_p")))
            check("2 the interest row kept with both dates", e["lines"][-1]["txn_date"] == "2026-10-01" and e["lines"][-1]["value_date"] == "2026-09-30")
            check("2 account last four only", e["account_ref"] == "5678")
        eo, en = refused(lambda t: globals().__setitem__("_eo", FY_OLD.parse_pdf_text(t)), E_WITHOUT), refused(lambda t: globals().__setitem__("_en", FY_NEW.parse_pdf_text(t)), E_WITHOUT)
        check("2 without the row: both e-statement readers read it the same", eo is None and en is None and globals().get("_eo") == globals().get("_en"), (eo, en))
        check("2 the CSV path is untouched (SAMPLE parses as before)", FY_NEW.parse_statement(FY_NEW.SAMPLE) == FY_OLD.parse_statement(FY_OLD.SAMPLE))

        # 3 still refused
        why = refused(YB_NEW.parse_text, B_BOTH_OUT)
        check("3 branch: both dates outside -> refused, both dates named", why is not None and "falls outside" in why and "2026-10-02" in why and "value date" in why, why)
        why = refused(FY_NEW.parse_pdf_text, E_BOTH_OUT)
        check("3 e-statement: both dates outside -> refused, both dates named", why is not None and "falls outside" in why and "2026-10-02" in why, why)
        why = refused(YB_NEW.parse_text, B_BAD_SUM)
        check("3 the arithmetic proof refuses exactly as before", why is not None and "closing balance" in why and refused(YB_OLD.parse_text, B_BAD_SUM) == why, why)
        _ipf = getattr(FY_NEW, "in_period", lambda *x: False)
        _ipb = getattr(YB_NEW, "in_period", lambda *x: False)
        check("3 a row with no value date is judged by its txn date",
              _ipf(dict(txn_date="2026-09-15", value_date=None), "2026-09-01", "2026-09-30")
              and not _ipf(dict(txn_date="2026-10-02", value_date=None), "2026-09-01", "2026-09-30"))
        check("3 in_period: value date inside, txn outside -> in; both outside -> out",
              _ipb(dict(txn_date="2026-10-01", value_date="2026-09-30"), "2026-09-01", "2026-09-30")
              and not _ipb(dict(txn_date="2026-10-01", value_date="2026-10-01"), "2026-09-01", "2026-09-30"))

        # 4 txn inside, value outside (a cheque clearing after the month): accepted before, accepted now
        check("4 branch: txn inside / value outside accepted by old and new", refused(YB_OLD.parse_text, B_CLEARING) is None and refused(YB_NEW.parse_text, B_CLEARING) is None)

        # hermetic
        after = {f: hashlib.md5(open(os.path.join(a.finance, f), "rb").read()).hexdigest() for f in before}
        check("hermetic: the box's two readers untouched", after == before)
    finally:
        shutil.rmtree(scr, ignore_errors=True)
    print("WALK_S475 %s %d checks, %d fail" % ("GREEN" if not FAILS else "RED", CHECKS, len(FAILS)))
    sys.exit(0 if not FAILS else 1)


if __name__ == "__main__":
    main()
