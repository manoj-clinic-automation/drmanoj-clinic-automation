#!/usr/bin/env python3
"""
patch_darpan_card_parked_s220.py -- S220 F-282b, part 2: the tap on Darpan's card.

darpan_card.html (pin fb129eee). ONE anchored change: the "bina pehchaan ke bill (N)" row
becomes a <details> like "CN bills" -- tap to see bill . naam . ID (as typed; blank when none was) . phone ke aakhri 4 . rupees. Staff page, Hindi.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_card_parked_s220.py
Offline: CARD_PATH=/path/to/darpan_card.html.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('CARD_PATH', '/root/finance/darpan_card.html')
MARK = 'S220 F-282b'

A_OLD = '''  ((j.sale.review_n||0) ? '<div class="row"><span class="k mut">bina pehchaan ke bill ('+j.sale.review_n+')</span>'+
     '<span class="v mut">'+R(j.sale.review_p||0)+'</span></div>' : ''));
'''
A_NEW = '''  /* S220 F-282b: tap to see WHICH bills -- bill . rupees . naam jaisa likha . phone ke aakhri 4 */
  ((j.sale.review_n||0) ? '<details><summary>bina pehchaan ke bill ('+j.sale.review_n+') — '+R(j.sale.review_p||0)+
     ' <span class="mut">(sale mein gina hai; naam / ID abhi bharna hai)</span></summary>'+
     tbl(j.sale.review_bills||[],[{k:"bill"},{k:"name"},{k:"clinic_id",f:x=>(x.clinic_id||"—")},{k:"last4",f:x=>(x.last4?("…"+x.last4):"—")},{k:"amount_p",n:1,f:x=>R(x.amount_p)}])+
     '</details>' : ''));
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
    bak = TARGET + ".bak_S220_f282b_" + stamp
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
