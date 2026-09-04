#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_finance_app_daypdf_s224.py -- S224: mount the Day Revenue PDF + WhatsApp share page.

ONE EDIT, anchored on ONE exact line -- the last line of the S224_MARG_PURCHASES block, which
is the last mount in the file today:

    # --- S224_MARG_PURCHASES end ---

Three lines go in after it, in the shape of every other mount. Nothing else in the file is
touched: no gate change (the routes live under /finance/clinic/, which the front gate already
resolves to the clinic unit), no PUBLIC_PATHS change (nothing here is public).

THE PIN. The repo's finance_app.py is BEHIND the box, so the expected md5 is NOT hard-coded:
you pass the one you read on the box. It refuses if the file is not that, if the anchor is not
there exactly once, or if the result does not compile (then it puts the backup back). Running
it twice is harmless: the second run says ALREADY PATCHED and changes nothing.

Run on the box:
    md5sum /root/finance/finance_app.py
    /root/wa/venv/bin/python3 -B /root/finance/patch_finance_app_daypdf_s224.py <that md5>
Offline:
    FA_PATH=./finance_app.py python3 -B patch_finance_app_daypdf_s224.py <md5 of that copy>
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
MARK = "S224_DAY_REVENUE_PDF begin"
ANCHOR = "# --- S224_MARG_PURCHASES end ---"

BLOCK = '''# --- S224_MARG_PURCHASES end ---

# --- S224_DAY_REVENUE_PDF begin -- the day sheet as a PDF, handed to WhatsApp from a phone ---
# Same day, same lines, same sections as finance_clinic_day's A4 page (which is NOT touched);
# a dependency-free PDF writer, and /finance/clinic/share as the one bookmark. Checker only.
import clinic_day_pdf                                         # noqa: E402
clinic_day_pdf.init(app, db, require, unit=CLINIC_UNIT)
# --- S224_DAY_REVENUE_PDF end ---'''

REQUIRED = ("\ndef require(", "\ndef db(", "\nCLINIC_UNIT = ")


def main():
    if len(sys.argv) < 2 or len(sys.argv[1]) != 32:
        sys.exit("USAGE: patch_finance_app_daypdf_s224.py <md5 of the finance_app.py you are patching>\n"
                 "       read it with:  md5sum /root/finance/finance_app.py")
    from_md5 = sys.argv[1].lower()
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    src = io.open(TARGET, encoding="utf-8").read()
    cur = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != from_md5:
        sys.exit("REFUSING: %s is %s, you said %s (D172/D188). Read the box's pin again."
                 % (TARGET, cur, from_md5))
    for name in REQUIRED:
        if src.count(name) != 1:
            sys.exit("REFUSING: %r occurs %d times, expected exactly 1" % (name.strip(), src.count(name)))
    if src.count(ANCHOR) != 1:
        sys.exit("REFUSING: the anchor %r occurs %d times, expected exactly 1. "
                 "Install S224_MARG_PURCHASES first." % (ANCHOR, src.count(ANCHOR)))
    if not os.path.exists(os.path.join(os.path.dirname(TARGET) or ".", "clinic_day_pdf.py")):
        sys.exit("REFUSING: clinic_day_pdf.py is not beside %s -- copy it first, or the app will "
                 "not import after the restart" % TARGET)
    new = src.replace(ANCHOR, BLOCK, 1)
    bak = TARGET + ".bak_S224_daypdf_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as e:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: syntax error after patch (%s); restored %s" % (e, bak))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % from_md5)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % got)
    print("next     restart clinic-finance.service, then GET /finance/clinic/share -> 302")


if __name__ == "__main__":
    main()
