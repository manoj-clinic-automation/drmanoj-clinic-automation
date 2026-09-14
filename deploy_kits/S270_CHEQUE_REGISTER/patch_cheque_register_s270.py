#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_cheque_register_s270.py -- S270: the cheque register gets its own screen.

WHAT IT DOES. Two anchored edits, and not one line of existing behaviour changed:

  A  the block is inserted before the purchase audit page -- the register's
     table, its four routes, its card, its script and its CSS.
  B  ONE ARGUMENT on the payment sheet's body line is repointed: the card built
     for the cheque lane is now _cheque_card_s270(...), which shows the same
     vendors PLUS the cheque logged against each and what is still to write.

     The S261 `cheque_card` string above it is left exactly as it is -- computed
     and no longer used. It is not deleted, so removing this kit restores the
     file byte for byte (the S256 rule: wrap, don't edit).

     It is passed (not _is_viewer_only(u)) and NOT `editable`, on purpose: a
     cheque is written AFTER the month is locked, so a FINAL month must still
     accept one. Logging a cheque moves no figure the sheet reads.

    python3 -B patch_cheque_register_s270.py --file /root/finance/purchase_app.py
    python3 -B patch_cheque_register_s270.py --file X --check   say what it would do

NO PIN IS PREDICTED (F-472). The new md5 is printed after the file is read back
from disk; that value, and nothing else, is what goes into the record.
"""
import argparse
import hashlib
import re
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "_cheque_card_s270"

A_BLOCK = '@bp.route("/page/month/<month>")\ndef page_month(month):'

B_OLD = r"""            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),
               strip, sheet_card, verify_card, cheque_card, nextcard,
               _advice_card_s265(con, month, prefix, final),
               _letter_card_s266(con, month, prefix, final,
                                 _advice_rows_s265(con, month)[1])))"""

B_NEW = r"""            % (_esc(_month_name(month)), prefix, month,
               _pay_months_nav_s264(con, month, prefix),
               strip, sheet_card, verify_card,
               _cheque_card_s270(con, month, prefix, groups, not _is_viewer_only(u)),
               nextcard,
               _advice_card_s265(con, month, prefix, final),
               _letter_card_s266(con, month, prefix, final,
                                 _advice_rows_s265(con, month)[1])))"""


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="from_md5", default=None)
    ap.add_argument("--block", default=os.path.join(HERE, "block.py"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(a.file):
        sys.exit("REFUSING: %s not found" % a.file)
    raw = io.open(a.file, "rb").read()
    cur = md5(raw)
    src = raw.decode("utf-8")

    if MARK in src:
        print("ALREADY PATCHED (%s present); pin %s -- nothing to do" % (MARK, cur))
        return 0
    if a.from_md5 and cur != a.from_md5.lower():
        sys.exit("REFUSING: %s is %s, you said %s" % (a.file, cur, a.from_md5))

    for label, anchor in (("the purchase audit route", A_BLOCK),
                          ("the payment sheet's body line", B_OLD)):
        n = src.count(anchor)
        if n != 1:
            sys.exit("REFUSING: the anchor for %s matched %d times, expected exactly 1.\n"
                     "          Nothing was written. The file is at %s." % (label, n, cur))

    block = io.open(a.block, encoding="utf-8").read()
    out = src.replace(B_OLD, B_NEW)
    out = out.replace(A_BLOCK, block.rstrip("\n") + "\n\n\n" + A_BLOCK)

    # The block is free to sit after page_pay -- python resolves a module-level
    # name when the call runs, not when the def is read. What it may NOT do is
    # sit before PAY_JS and CSS, because it EXTENDS both at import time.
    if out.index("PAY_JS = PAY_JS + CHEQUE_JS") < out.index('PAY_JS = """'):
        sys.exit("REFUSING: the block would extend PAY_JS before PAY_JS exists. Nothing written.")
    # anchored to the start of a line -- the block MENTIONS this string in a
    # comment explaining why it must never be a statement (F-478)
    if re.search(r"^CSS = CSS \+ CHEQUE_CSS", out, re.M):
        sys.exit("REFUSING: this block must NOT extend the page-wide stylesheet (F-478).\n"
                 "          Four screens grew by 1,287 bytes the last time it did.")

    new = out.encode("utf-8")
    if a.check:
        print("would write %s -> %s  (+%d bytes)" % (cur, md5(new), len(new) - len(raw)))
        return 0

    bak = "%s.bak_S270_%s" % (a.file, cur[:8])
    if not os.path.exists(bak):
        shutil.copy2(a.file, bak)
    io.open(a.file, "wb").write(new)
    back = md5(io.open(a.file, "rb").read())
    print("patched %s" % a.file)
    print("   was  %s" % cur)
    print("   now  %s   <-- READ BACK FROM DISK. This is the pin." % back)
    print("   backup %s" % bak)
    if back != md5(new):
        print("   !! what is on disk is not what was built. Restart nothing; tell Claude.")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
