#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_advice_s266.py -- S266: the bank advice, previewed exactly, on the sheet.

ONE anchored edit (the payment sheet's body gains a fifth card) and ONE append
(the block that builds it, its own print page and its API). Nothing else is touched.

    python3 -B patch_advice_s266.py --file /root/finance/purchase_app.py [--from <md5>]
"""
import argparse
import hashlib
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "_letter_card_s266"

B_OLD = '                      "{:,}".format(r["rupees"])))'
B_NEW = '                      _rupees_s266(r["rupees"])))'
C_OLD = '               "".join(trs), "{:,}".format(total)))'
C_NEW = '               "".join(trs), _rupees_s266(total)))'

A_OLD = r"""            '</div>%s%s%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),
               strip, sheet_card, verify_card, cheque_card, nextcard,
               _advice_card_s265(con, month, prefix, final)))"""
A_NEW = r"""            '</div>%s%s%s%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),
               strip, sheet_card, verify_card, cheque_card, nextcard,
               _advice_card_s265(con, month, prefix, final),
               _letter_card_s266(con, month, prefix, final,
                                 _advice_rows_s265(con, month)[1])))"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="from_md5", default=None)
    ap.add_argument("--block", default=os.path.join(HERE, "block.py"))
    a = ap.parse_args()
    if not os.path.exists(a.file):
        sys.exit("REFUSING: %s not found" % a.file)
    raw = io.open(a.file, "rb").read()
    cur = hashlib.md5(raw).hexdigest()
    src = raw.decode("utf-8")
    if MARK in src:
        print("ALREADY PATCHED (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if a.from_md5 and cur != a.from_md5.lower():
        sys.exit("REFUSING: %s is %s, you said %s" % (a.file, cur, a.from_md5))
    for label, old in (("the sheet's body", A_OLD),
                       ("the advice's amount column", B_OLD),
                       ("the advice's total", C_OLD)):
        if src.count(old) != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1"
                     % (label, src.count(old)))
    block = io.open(a.block, encoding="utf-8").read()
    new = src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1).replace(
        C_OLD, C_NEW, 1).rstrip("\n") + "\n" + block.rstrip("\n") + "\n"
    bak = a.file + ".bak_S266_" + cur[:8]
    shutil.copy2(a.file, bak)
    io.open(a.file, "w", encoding="utf-8", newline="\n").write(new)
    got = hashlib.md5(io.open(a.file, "rb").read()).hexdigest()
    print("patched %s" % a.file)
    print("   was  %s" % cur)
    print("   now  %s" % got)
    print("   backup %s" % bak)


if __name__ == "__main__":
    main()
