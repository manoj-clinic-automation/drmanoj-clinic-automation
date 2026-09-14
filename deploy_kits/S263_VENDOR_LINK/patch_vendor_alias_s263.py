#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_vendor_alias_s263.py -- S263: link Marg's bill name to the account row.

ONE anchored APPEND at the very end of purchase_app.py. Not one existing line is
edited: _vendor_bank is wrapped, the way S261 wrapped _book_nav, so the original
stays exactly as it is and the wrapper only adds lanes it can prove.

    python3 -B patch_vendor_alias_s263.py --file /root/finance/purchase_app.py [--from <md5>]
"""
import argparse
import hashlib
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "_ALIAS_S263"
TAIL = ('    return pdf.build(), 200, {"Content-Type": "application/pdf", '
        '"Cache-Control": "no-store", "Content-Disposition": '
        '\'inline; filename="salt_corrections.pdf"\'}')


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
    if src.count(TAIL) != 1:
        sys.exit("REFUSING: the file's last line matched %d times, expected exactly 1"
                 % src.count(TAIL))
    if not src.rstrip("\n").endswith(TAIL):
        sys.exit("REFUSING: purchase_app.py does not end where this kit expects it to")
    block = io.open(a.block, encoding="utf-8").read()
    new = src.rstrip("\n") + "\n" + block.rstrip("\n") + "\n"
    bak = a.file + ".bak_S263_" + cur[:8]
    shutil.copy2(a.file, bak)
    io.open(a.file, "w", encoding="utf-8", newline="\n").write(new)
    got = hashlib.md5(io.open(a.file, "rb").read()).hexdigest()
    print("patched %s" % a.file)
    print("   was  %s" % cur)
    print("   now  %s" % got)
    print("   backup %s" % bak)


if __name__ == "__main__":
    main()
