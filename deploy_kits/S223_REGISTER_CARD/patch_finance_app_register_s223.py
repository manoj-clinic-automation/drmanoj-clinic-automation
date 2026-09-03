#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_finance_app_register_s223.py -- S223: mount the daily register card.

THE OWNER: "put the sheet on vps as a day entry card, easy to fill, less errors, automatic
matching by your setup"

TWO LINES, at IMPORT time, in the same place and shape as the five modules already mounted there.
`audit` is passed in so every save is recorded in the app's own audit log -- this is the first
WRITE screen added in this series, and a money row that changes without a trail is not a record.

Target: /root/finance/finance_app.py   (from pin fd478faf9fb8142234554564feb24ed8, the
        S223_CLINIC_DAY result)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_finance_app_register_s223.py
Offline:         FA_PATH=./finance_app.py python3 -B patch_finance_app_register_s223.py
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
FROM_MD5 = "fd478faf9fb8142234554564feb24ed8"
MARK = "S223_CLINIC_REGISTER begin"

A_OLD = '''import finance_clinic_day                                     # noqa: E402
finance_clinic_day.init(app, db, require, unit=CLINIC_UNIT)
# --- S223_CLINIC_DAY end ---'''

A_NEW = '''import finance_clinic_day                                     # noqa: E402
finance_clinic_day.init(app, db, require, unit=CLINIC_UNIT)
# --- S223_CLINIC_DAY end ---

# --- S223_CLINIC_REGISTER begin -- the counter's own register, entered here ---
# The THIRD record of a day's money, beside Docterz and the bank. It creates its
# own table on import and writes only that table. `audit` is passed in because
# this is a screen that WRITES: every save records who, when, and what changed.
import clinic_register                                        # noqa: E402
clinic_register.init(app, db, require, audit, unit=CLINIC_UNIT)
# --- S223_CLINIC_REGISTER end ---'''


def main():
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    src = io.open(TARGET, encoding="utf-8").read()
    cur = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != FROM_MD5:
        sys.exit("REFUSING: %s is %s, expected %s (D172/D188). Install S223_CLINIC_DAY first."
                 % (TARGET, cur, FROM_MD5))
    if src.count(A_OLD) != 1:
        sys.exit("REFUSING: the mount anchor did not match exactly once")
    for name in ("def audit(", "CLINIC_UNIT"):
        if name not in src:
            sys.exit("REFUSING: %r is not in this file; the mount would fail at import and take "
                     "the whole finance app down" % name)
    new = src.replace(A_OLD, A_NEW, 1)
    bak = TARGET + ".bak_S223_register_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as e:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: syntax error after patch (%s); restored %s" % (e, bak))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % FROM_MD5)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % got)
    print("next     put clinic_register.py beside it, then restart clinic-finance.service")


if __name__ == "__main__":
    main()
