#!/usr/bin/env python3
"""
patch_hub_disputed_s220.py -- S220 F-277, part 4 of 4: the colour.

finance_ui/finance_approvals.html (pin 735c7958) paints three verdicts AMBER
-- the ones that mean THE AUDIT COULD NOT RUN -- and lets any verdict it has
not been told about fall through to RED, the colour reserved for a finding
about money. That default is exactly how a new question-verdict would arrive
on the owner's card wearing the colour of an accusation (S219 M7 said so).
"identity disputed" is added to the amber list. ONE anchored change, sliced
verbatim from the live bytes. HTML: the check is that the file grew.

Run on the box:
  /root/wa/venv/bin/python3 -B /root/finance/patch_hub_disputed_s220.py
Offline: HUB_PATH=/path/to/finance_approvals.html.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('HUB_PATH', '/root/finance/finance_ui/finance_approvals.html')
MARK = 'identity disputed'

A_OLD = ('             : (n.verdict==="no patient attributed"||n.verdict==="not examinable"\n'
         '                ||n.verdict==="identity needed")\n')

A_NEW = ('             : (n.verdict==="no patient attributed"||n.verdict==="not examinable"\n'
         '                ||n.verdict==="identity needed"\n'
         '                ||n.verdict==="identity disputed")   /* S220 F-277: a question, amber */\n')

PAIRS = [("A", A_OLD, A_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S220_f277_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    if len(out) <= len(src) or out.count(MARK) != 1:
        raise SystemExit("REFUSED: the result is not the expected shape. NOTHING was changed.")
    open(TARGET, "w", encoding="utf-8").write(out)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("restart  systemctl restart clinic-finance.service")
    return 0


if __name__ == "__main__":
    sys.exit(main())
