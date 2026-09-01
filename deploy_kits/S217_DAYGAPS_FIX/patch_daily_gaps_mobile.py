#!/usr/bin/env python3
"""
patch_daily_gaps_mobile.py -- S217: fix the CounterGaps 500.

THE FAULT (journalctl, 01-Sep): /finance/api/day-gaps crashes with
    sqlite3.OperationalError: no such column: mobile
at finance_daily_gaps.py line 217. The module was written expecting the D356
patient-master push to add a `mobile` column to patient_ref; that push never
ran. The live table has `phone_last4` (and a fingerprint), never `mobile`.
The line only executes for a day carrying an UNMATCHED bill -- which is why
four green days proved nothing (a green test proves only the path it walked)
and the first real unmatched bill killed the card.

THE FIX: select only the columns the table has ever had, and show the masked
last-4 (which is also the masking rule). No behaviour change on matched days.

SAFETY: byte-anchored (must match EXACTLY once or abort), timestamped backup,
in-process compile check with automatic restore on failure.

USAGE:  /root/wa/venv/bin/python3 -B /root/finance/patch_daily_gaps_mobile.py
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get("DG_PATH", "/root/finance/finance_daily_gaps.py")
MARK = "S217 (no-mobile column fix)"

OLD = '''            pr = con.execute("SELECT name, mobile, phone_last4 FROM patient_ref "
                             "WHERE id=?", (pid,)).fetchone()
            if pr is not None:
                nm = nm or (pr["name"] or "")
                mob = (pr["mobile"] or "")
                if not mob and (pr["phone_last4"] or ""):
                    mob = "xxxxxx" + pr["phone_last4"]'''

NEW = '''            # S217 (no-mobile column fix): patient_ref has never had a
            # `mobile` column (D356 not deployed); it has phone_last4. The
            # masked last-4 is also the display rule, so select only what
            # exists and show that.
            pr = con.execute("SELECT name, phone_last4 FROM patient_ref "
                             "WHERE id=?", (pid,)).fetchone()
            if pr is not None:
                nm = nm or (pr["name"] or "")
                if pr["phone_last4"]:
                    mob = "xxxxxx" + pr["phone_last4"]'''


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched (%s) -- nothing to do" % MARK)
        return 0
    n = src.count(OLD)
    if n != 1:
        raise SystemExit("REFUSED: anchor matches %d times (need exactly 1). "
                         "The file has drifted -- do not guess." % n)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S217_mobile_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src.replace(OLD, NEW, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: compile failed (%s); original restored from %s" % (ex, bak))
    print("patched %s (%s); backup %s" % (TARGET, MARK, bak))
    return 0


if __name__ == "__main__":
    sys.exit(main())
