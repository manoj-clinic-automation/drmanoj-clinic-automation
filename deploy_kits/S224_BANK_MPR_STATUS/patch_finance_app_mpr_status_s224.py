#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_finance_app_mpr_status_s224.py -- S224: mount bank_mpr_status inside the finance app.

ONE EDIT, anchored on an exact line, refused unless the anchor is found EXACTLY ONCE and the
file's md5 is the one you hand it (F-299 / D172 / D188).  It chains AFTER the last S224 mount
already in the file -- today that is `# --- S224_MARG_PURCHASES end ---` (S224_MARG_PURCHASES,
installed 04-Sep).  Nothing else in finance_app.py is touched: no gate change (the routes sit
behind the ordinary login like the Day Revenue page), no PUBLIC_PATHS change.

Run on the box:
    md5sum /root/finance/finance_app.py
    /root/wa/venv/bin/python3 -B /root/finance/patch_finance_app_mpr_status_s224.py <that md5>
Offline:
    FA_PATH=./finance_app.py python3 -B patch_finance_app_mpr_status_s224.py <md5 of that copy>

If a later S224 kit has added its own `# --- S224_<NAME> end ---` after MARG_PURCHASES, set
MPR_ANCHOR to that exact line to chain after it instead (the default is the one above).
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
MARK = "S224_BANK_MPR_STATUS begin"
ANCHOR = os.environ.get("MPR_ANCHOR", "# --- S224_MARG_PURCHASES end ---")

BLOCK = '''

# --- S224_BANK_MPR_STATUS begin -- "where is the bank MPR for <date>?" in one line ---
# Reads upi_statement / data_flag / the raw statement store; writes nothing, creates no
# table. /finance/clinic/bank/mpr/<date> (HTML line or ?json=1) and /finance/clinic/bank/mpr (last 8 days).
# UPI_DIR is the same store api_upi_statement writes to, defined above.
import bank_mpr_status                                        # noqa: E402
bank_mpr_status.init(app, db, require, unit=CLINIC_UNIT, upi_dir=UPI_DIR)
# --- S224_BANK_MPR_STATUS end ---'''

REQUIRED = ("\ndef require(", "\ndef db(", "\nUPI_DIR = ", "\nCLINIC_UNIT = ", '\nif __name__ == "__main__":')


def main():
    if len(sys.argv) < 2 or len(sys.argv[1]) != 32:
        sys.exit("USAGE: patch_finance_app_mpr_status_s224.py <md5 of the finance_app.py you are patching>\n"
                 "       read it with:  md5sum /root/finance/finance_app.py")
    from_md5 = sys.argv[1].lower()
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    cur = hashlib.md5(raw).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != from_md5:
        sys.exit("REFUSING: %s is %s, you said %s (D172/D188). Read the box's pin again."
                 % (TARGET, cur, from_md5))
    if b"\r\n" in raw:
        sys.exit("REFUSING: %s has CRLF line endings; the box's file is LF (F-294)" % TARGET)
    for name in REQUIRED:
        if src.count(name) != 1:
            sys.exit("REFUSING: %r occurs %d times, expected exactly 1" % (name.strip(), src.count(name)))
    anchor_line = "\n" + ANCHOR + "\n"
    if src.count(anchor_line) != 1:
        sys.exit("REFUSING: the anchor line %r did not match exactly once (found %d). "
                 "Install S224_MARG_PURCHASES first, or set MPR_ANCHOR to the last "
                 "'# --- S224_<NAME> end ---' line in the file." % (ANCHOR, src.count(anchor_line)))
    if src.index(anchor_line) > src.index('\nif __name__ == "__main__":'):
        sys.exit("REFUSING: the anchor sits after __main__; that is not the mount region")
    if "\nUPI_DIR = " not in src[:src.index(anchor_line)]:
        sys.exit("REFUSING: UPI_DIR is defined after the anchor; the mount would NameError")
    new = src.replace(anchor_line, "\n" + ANCHOR + BLOCK + "\n", 1)
    bak = TARGET + ".bak_S224_mprstatus_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as e:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: syntax error after patch (%s); restored %s" % (e, bak))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % from_md5)
    print("anchor       %s" % ANCHOR)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % got)
    print("next     bank_mpr_status.py beside it, then restart clinic-finance.service")


if __name__ == "__main__":
    main()
