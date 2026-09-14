#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_cheque_months_s271.py -- S271: the register's months come from the BOOK,
not from the cheques already in it.

WHAT WAS WRONG, seen on the live screen the hour S270 went in. The register's
month strip was built from `SELECT DISTINCT month FROM purchase_cheque`. With no
cheque logged yet it offered nothing but "Every cheque" -- so September, which
OWES 400 on the cheque lane and has nothing written against it, could not be
reached from the register at all.

**The most useful state of a register is the one where money is owed and nothing
has been written. That was the one state the page could not show.**

ONE anchored change and one helper appended. Nothing else is touched:

  A  the month list becomes _cheque_months_s271(con) -- every month with a
     cheque, UNION every month the purchase book knows.
  B  the helper is appended at the end of the file.

    python3 -B patch_cheque_months_s271.py --file /root/finance/purchase_app.py
"""
import argparse
import hashlib
import io
import os
import re
import shutil
import sys

MARK = "_cheque_months_s271"

A_OLD = '''    months = [r[0] for r in con.execute(
        "SELECT DISTINCT month FROM purchase_cheque ORDER BY month DESC").fetchall()]'''

A_NEW = '''    months = _cheque_months_s271(con)'''

HELPER = '''

def _cheque_months_s271(con):
    """The months the register offers.

    S270 built this strip from the cheques already logged, which meant a month
    that owed money on the cheque lane and had nothing written against it was
    unreachable -- the register hid its own most useful state. It is now every
    month that has a cheque, UNION every month the purchase book knows, newest
    first. _months() is wrapped because a box without the book must still get a
    working register rather than a 500."""
    got = [r[0] for r in con.execute(
        "SELECT DISTINCT month FROM purchase_cheque ORDER BY month DESC").fetchall()]
    try:
        more = [m for m in (_months(con) or []) if m]
    except Exception:
        more = []
    return sorted(set(got) | set(more), reverse=True)
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--from", dest="from_md5", default=None)
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
    if "_cheque_card_s270" not in src:
        sys.exit("REFUSING: S270 is not in this file. S271 has nothing to correct.")
    n = src.count(A_OLD)
    if n != 1:
        sys.exit("REFUSING: the month-list anchor matched %d times, expected exactly 1.\n"
                 "          Nothing was written. The file is at %s." % (n, cur))

    out = src.replace(A_OLD, A_NEW).rstrip("\n") + "\n" + HELPER
    if re.search(r"^CSS = CSS \\+ CHEQUE_CSS", out, re.M):
        sys.exit("REFUSING: the page-wide stylesheet must stay untouched (F-478).")

    new = out.encode("utf-8")
    if a.check:
        print("would write %s -> %s  (+%d bytes)" % (cur, md5(new), len(new) - len(raw)))
        return 0
    bak = "%s.bak_S271_%s" % (a.file, cur[:8])
    if not os.path.exists(bak):
        shutil.copy2(a.file, bak)
    io.open(a.file, "wb").write(new)
    back = md5(io.open(a.file, "rb").read())
    print("patched %s" % a.file)
    print("   was  %s" % cur)
    print("   now  %s   <-- READ BACK FROM DISK. This is the pin." % back)
    print("   backup %s" % bak)
    return 0 if back == md5(new) else 4


if __name__ == "__main__":
    sys.exit(main())
