#!/usr/bin/env python3
"""
patch_darpan_mobile_s220.py -- S220 FULL MOBILE, part 2 of 3: the card API carries it.

The owner's ruling, 02-Sep 23:05: "phone full 10 for me and Darpan." ONE anchored change
to darpan_app.py (pin c740456e): each parked bill also carries `mobile` -- the full number
when the lines CSV carried it (part 1, marg_report), blank when the export predates the
ruling (then the card falls back to the last four).

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_mobile_s220.py
Offline: DARPAN_PATH=/path/to/darpan_app.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('DARPAN_PATH', '/root/finance/darpan_app.py')
MARK = 'S220 FULL MOBILE'

A_OLD = '''                clinic_id=(r["guess_clinic_id"] or raw.get("clinic_id") or ""),
                last4=(raw.get("phone_last4") or "")))
'''
A_NEW = '''                clinic_id=(r["guess_clinic_id"] or raw.get("clinic_id") or ""),
                mobile=(raw.get("mobile") or ""),   # S220 FULL MOBILE (owner's ruling)
                last4=(raw.get("phone_last4") or "")))
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
    bak = TARGET + ".bak_S220_mobile_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src.replace(A_OLD, A_NEW, 1)
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
