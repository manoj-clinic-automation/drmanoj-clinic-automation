#!/usr/bin/env python3
"""
patch_finance_app_margtotal_s220.py -- S220 F-281: the owner's "Marg -- total" told two lies.

FOUND 02-Sep-2026, 22:40 IST, on the first day through the S220 system. The owner's
day page read "Marg -- total 17,674 . 20 bills . variance 30 (within Rs 2,000)"
while Darpan's card read "Din ki sale 15,614". Read from the code and the live db:

  1  `marg_total_p = sum(amount_p)` over the day's sale rows -- the query fetches
     `service` and then IGNORES it, so a sale return (stored POSITIVE, service
     '<base>_return' -- S180) is ADDED instead of subtracted. CN00198 Rs 1,030 was
     added: 16,644 + 1,030 = 17,674. The true net of those bills is 15,614.
  2  the seven bills the ingest parked for review (confidence 0.5 -- a name but
     no clinic ID) are not sale rows, so their Rs 2,030 was in NEITHER screen's
     total. Marg sold them; only the patient is unknown.

The day's true Marg net = 15,614 + 2,030 = 17,644 -- EXACTLY the declared cash.
The "variance 30" was two errors nearly cancelling. `v_day_attribution` has known
both facts since S180 (it subtracts returns, and it carries in_review_p) -- this
helper simply never read it. One source, one rule (D349): read the view.

ONE anchored change to finance_app.py. The anchor is sliced verbatim; the
patcher refuses unless it matches exactly once.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_finance_app_margtotal_s220.py
Offline: FA_PATH=/path/to/finance_app.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('FA_PATH', '/root/finance/finance_app.py')
MARK = 'S220 F-281'

A_OLD = '''    marg_total_p = sum(
        (b_r["amount_p"] or 0) for b_r in con.execute(
            "SELECT s.amount_p, s.service FROM sale_item s JOIN day_entry e "
            "ON e.id=s.day_entry_id WHERE e.unit=? AND e.business_date=?",
            (UNIT, iso))) if st.get("exists") else 0
'''
A_NEW = '''    # S220 F-281: the Marg total is the day's SIGNED bill money, attributed or
    # not -- v_day_attribution subtracts returns (S180) and carries the bills
    # parked for review, whose money is real even while the patient is unknown.
    # The old sum added returns and dropped the parked bills; on 02-Sep-2026 it
    # read 17,674 against a true 17,644, and the two errors nearly cancelled.
    if st.get("exists"):
        _va = con.execute("SELECT attributed_p, in_review_p FROM v_day_attribution "
                          "WHERE unit=? AND business_date=?", (UNIT, iso)).fetchone()
        if _va is not None:
            marg_total_p = int(_va["attributed_p"] or 0) + int(_va["in_review_p"] or 0)
        else:
            marg_total_p = sum(
                ((b_r["amount_p"] or 0) * (-1 if "return" in (b_r["service"] or "") else 1))
                for b_r in con.execute(
                    "SELECT s.amount_p, s.service FROM sale_item s JOIN day_entry e "
                    "ON e.id=s.day_entry_id WHERE e.unit=? AND e.business_date=?",
                    (UNIT, iso)))
    else:
        marg_total_p = 0
'''
PAIRS = [("A", A_OLD, A_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S220_f281_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). RESTORED from %s." % (ex, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
