#!/usr/bin/env python3
"""
patch_card_mobile_s220.py -- S220 FULL MOBILE, part 3 of 3: Darpan's card shows the number.

darpan_card.html (pin a0bc0c4c). ONE anchored change: the phone column shows the full
mobile when the parked bill carries it, the last four (with the ellipsis) when the export
predates the ruling, a dash when there is none.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_card_mobile_s220.py
Offline: CARD_PATH=/path/to/darpan_card.html.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('CARD_PATH', '/root/finance/darpan_card.html')
MARK = 'S220 FULL MOBILE'

A_OLD = '''{k:"last4",f:x=>(x.last4?("…"+x.last4):"—")}'''
A_NEW = '''{k:"mobile",f:x=>(x.mobile||(x.last4?("…"+x.last4):"—"))} /* S220 FULL MOBILE */'''
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
    if len(out) <= len(src) or out.count(MARK) != 1:
        raise SystemExit("REFUSED: the result is not the expected shape. NOTHING was changed.")
    open(TARGET, "w", encoding="utf-8").write(out)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("restart  systemctl restart clinic-finance.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
