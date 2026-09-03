#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_finance_app_clinicday_s223.py -- S223: mount the clinic day-revenue screen.

TWO LINES, at IMPORT time, in the same place and the same shape as the four modules already
mounted there (stock_app, darpan_app, joiner_app, returns_desk). gunicorn imports
finance_app:app and never reaches __main__, so a mount inside a `if __name__` block would exist
only when nobody is looking.

The screen is READ-ONLY and gated on the clinic roles that already exist:
`require("maker", "checker", unit="clinic")` admits exactly the people who already work the
clinic desk -- the owner, Dr Bhawna, Shavez, Shivani and Alisha -- and nobody else. No new list
is introduced, so there is no new list to drift out of date.

PROVENANCE. The from-pin below was not taken on trust. `finance_app.py`'s live bytes were
REPRODUCED OFFLINE before this patcher was written: the S217/218 live capture (`80c2323a…`)
replayed through `S219_MARG_AUTOAPPLY` -> `b42b1f08…` -> `S219_RETURNS_M7` -> `a57980c2…`
(the S219 close pin, exact) -> `S220_DAY_TOTAL_TRUTH` -> `f7dd9e57…` (the S220 close pin, exact).
Every intermediate matched its recorded pin. This patcher is anchored on bytes that were read,
not on a filename that looked right (F-280, F-299).

Target: /root/finance/finance_app.py   (from pin f7dd9e57231454c17bcb4687d38165ca)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_finance_app_clinicday_s223.py
Offline:         FA_PATH=./finance_app.py python3 -B patch_finance_app_clinicday_s223.py
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
FROM_MD5 = "f7dd9e57231454c17bcb4687d38165ca"
MARK = "S223_CLINIC_DAY begin"

A_OLD = '''returns_desk.init(app, db, require, unit=UNIT)
# --- S214_RETURNS_DESK end ---'''

A_NEW = '''returns_desk.init(app, db, require, unit=UNIT)
# --- S214_RETURNS_DESK end ---

# --- S223_CLINIC_DAY begin -- the clinic's day revenue, on a screen ---
# Read-only. Every figure it shows was computed from the itemised lines of the
# day's own Docterz sheet by docterz_ingest.py and stored in clinic_day_revenue;
# the sheet's own summary block is stored beside it and never displayed (D367,
# the owner's ruling of 04-Sep-2026). Gated on the CLINIC roles that already
# exist, so the people who work that desk are exactly the people who see it.
import finance_clinic_day                                     # noqa: E402
finance_clinic_day.init(app, db, require, unit=CLINIC_UNIT)
# --- S223_CLINIC_DAY end ---'''


def main():
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    src = io.open(TARGET, encoding="utf-8").read()
    cur = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != FROM_MD5:
        sys.exit("REFUSING: %s is %s, expected %s (D172/D188). Reconcile before patching."
                 % (TARGET, cur, FROM_MD5))
    n = src.count(A_OLD)
    if n != 1:
        sys.exit("REFUSING: the mount anchor matched %d times, expected exactly 1" % n)
    if "CLINIC_UNIT" not in src:
        sys.exit("REFUSING: CLINIC_UNIT is not defined in this file; the mount would NameError "
                 "at import and take the whole finance app down")
    new = src.replace(A_OLD, A_NEW, 1)
    bak = TARGET + ".bak_S223_clinicday_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
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
    print("next     put finance_clinic_day.py beside it, then restart clinic-finance.service")


if __name__ == "__main__":
    main()
