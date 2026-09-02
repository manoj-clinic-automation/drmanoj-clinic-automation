#!/usr/bin/env python3
"""
patch_darpan_card_review_s220.py -- S220 F-282: Darpan's "Din ki sale" counts every bill Marg sold.

The card's day sale was sold - returned over ACCEPTED sale rows only. A bill the
ingest parks for review (a name but no clinic ID, confidence 0.5) is not a sale
row, so its money vanished from the card: 02-Sep read 15,614 where Marg sold
17,644 (seven parked bills, Rs 2,030 net). The patient being unknown does not
make the sale unreal. TWO anchored changes to darpan_app.py, ONE to
darpan_card.html (part 2): the parked bills' signed money joins the day sale,
and the card says so under it -- "bina pehchaan ke bill (7) -- Rs 2,030" -- so
Darpan sees exactly what identity is still owed.

Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_card_review_s220.py
Offline: DARPAN_PATH=/path/to/darpan_app.py.
"""
import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('DARPAN_PATH', '/root/finance/darpan_app.py')
MARK = 'S220 F-282'

A_OLD = '    day_sale_p = sold_p - ret_p\n'
A_NEW = '''    # S220 F-282: the bills parked for review are Marg's sales too -- only the
    # patient is unknown. Their SIGNED money (v_day_attribution, S180) joins the
    # day sale, and the card shows them as identity still owed.
    _va = con.execute("SELECT in_review_p, in_review_count FROM v_day_attribution "
                      "WHERE unit=? AND business_date=?", (_unit, iso)).fetchone()
    review_p = int(_va["in_review_p"] or 0) if _va is not None else 0
    review_n = int(_va["in_review_count"] or 0) if _va is not None else 0
    day_sale_p = sold_p - ret_p + review_p
'''
B_OLD = '                   sale=dict(day_sale_p=day_sale_p, sold_p=sold_p,\n'
B_NEW = ('                   sale=dict(day_sale_p=day_sale_p, sold_p=sold_p,\n'
         '                             review_p=review_p, review_n=review_n,   # S220 F-282\n')
PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW)]


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
