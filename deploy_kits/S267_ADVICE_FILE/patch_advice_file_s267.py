#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_advice_file_s267.py -- S267: the .xlsx the bank is emailed.

TWO anchored edits (the advice card gains a download button) and ONE append (the
workbook writer and its route). Nothing else in the file is touched.

    python3 -B patch_advice_file_s267.py --file /root/finance/purchase_app.py [--from <md5>]
"""
import argparse
import hashlib
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "_advice_xlsx_s267"

A_OLD = ("            '<button class=\"p noprint\" onclick=\"window.print()\">Print this"
         "</button></div>%s'")
A_NEW = ("            '<button class=\"p noprint\" onclick=\"window.print()\">Print this"
         "</button> '\n"
         "            '<a class=\"p noprint\" href=\"%s/page/pay/%s/advice.xlsx\">Download "
         "the file for the email</a></div>%s'")

B_OLD = "            % (warn,"
B_NEW = "            % (prefix, month, warn,"


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
    for label, old in (("the advice card's button row", A_OLD),
                       ("the advice card's arguments", B_OLD)):
        if src.count(old) != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1"
                     % (label, src.count(old)))
    block = io.open(a.block, encoding="utf-8").read()
    new = (src.replace(A_OLD, A_NEW, 1).replace(B_OLD, B_NEW, 1).rstrip("\n")
           + "\n" + block.rstrip("\n") + "\n")
    bak = a.file + ".bak_S267_" + cur[:8]
    shutil.copy2(a.file, bak)
    io.open(a.file, "w", encoding="utf-8", newline="\n").write(new)
    got = hashlib.md5(io.open(a.file, "rb").read()).hexdigest()
    print("patched %s" % a.file)
    print("   was  %s" % cur)
    print("   now  %s" % got)
    print("   backup %s" % bak)


if __name__ == "__main__":
    main()
