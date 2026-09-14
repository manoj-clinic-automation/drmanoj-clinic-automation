#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_advice_s265.py -- S265: the bank advice, previewed exactly, on the sheet.

ONE anchored edit (the payment sheet's body gains a fourth card) and ONE append
(the block that builds it). Nothing else in the file is touched.

    python3 -B patch_advice_s265.py --file /root/finance/purchase_app.py [--from <md5>]
"""
import argparse
import hashlib
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "_advice_card_s265"

A_OLD = r"""            '</div>%s%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),
               strip, sheet_card, verify_card, cheque_card, nextcard))"""
A_NEW = r"""            '</div>%s%s%s%s%s%s%s'
            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),
               strip, sheet_card, verify_card, cheque_card, nextcard,
               _advice_card_s265(con, month, prefix, final)))"""


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
    if src.count(A_OLD) != 1:
        sys.exit("REFUSING: the sheet's body matched %d times, expected exactly 1"
                 % src.count(A_OLD))
    block = io.open(a.block, encoding="utf-8").read()
    new = src.replace(A_OLD, A_NEW, 1).rstrip("\n") + "\n" + block.rstrip("\n") + "\n"
    bak = a.file + ".bak_S265_" + cur[:8]
    shutil.copy2(a.file, bak)
    io.open(a.file, "w", encoding="utf-8", newline="\n").write(new)
    got = hashlib.md5(io.open(a.file, "rb").read()).hexdigest()
    print("patched %s" % a.file)
    print("   was  %s" % cur)
    print("   now  %s" % got)
    print("   backup %s" % bak)


if __name__ == "__main__":
    main()
