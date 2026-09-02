#!/usr/bin/env python3
"""
patch_darpan_card_html_s220.py -- S220 F-282, part 2: the card says what identity is owed.

darpan_card.html (pin fa6f0a86). ONE anchored change: under "Din ki sale", after the
CN bills line, a line in Darpan's own words -- "bina pehchaan ke bill (N) -- Rs X" --
shown only when there are any. Staff page: Hindi by the owner's rule.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_card_html_s220.py
Offline: CARD_PATH=/path/to/darpan_card.html.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('CARD_PATH', '/root/finance/darpan_card.html')
MARK = 'S220 F-282'

A_OLD = '''  '<details><summary>CN bills ('+j.sale.cn_bills.length+') — '+R(j.sale.returned_p)+
  '</summary>'+tbl(j.sale.cn_bills,[{k:"bill"},{k:"amount_p",n:1,f:x=>R(x.amount_p)}])+
  '</details>');
'''
A_NEW = '''  '<details><summary>CN bills ('+j.sale.cn_bills.length+') — '+R(j.sale.returned_p)+
  '</summary>'+tbl(j.sale.cn_bills,[{k:"bill"},{k:"amount_p",n:1,f:x=>R(x.amount_p)}])+
  '</details>'+
  /* S220 F-282: bills Marg sold whose patient is still unknown -- counted in the
     sale above, named here so the identity owed is visible, not hidden. */
  ((j.sale.review_n||0) ? '<div class="row"><span class="k mut">bina pehchaan ke bill ('+j.sale.review_n+')</span>'+
     '<span class="v mut">'+R(j.sale.review_p||0)+'</span></div>' : ''));
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
    bak = TARGET + ".bak_S220_f282_" + stamp
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
