#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_salary_policy_S240.py -- two corrections to the salary sheet. NO AMOUNT CHANGES.

THE OWNER, 12-Sep-2026, after the August sheet was checked row by row against the engine:

  1. THE FOOTNOTE IS WRONG. It reads "salary / 30". The engine divides by 30.5 (D343). The line
     is built with a whole-number format, so 30.5 prints as 30. Every rupee on the sheet is
     right; the sentence under them is not -- and it is the line a member of staff reads before
     signing. Fixed by printing the divisor as it is.

  2. AMIR IS FLAT PAY, SO HIS ROW SHOWS NO WORKING. He is paid a flat Rs 2,500 and takes no
     leave charge (D459). His row nevertheless printed "31" in the Leaves column -- a number
     that is computed and then thrown away, and which also inflated the clinic's leave total by
     31 days. Part-time staff (the dates_only_staff setting) now show 0 there. His pay, his
     net, and every other person's row are untouched.

WHAT THIS DOES NOT DO: it adds no column, removes no column, and changes no amount anywhere.

It refuses rather than guesses: each anchor must occur EXACTLY ONCE, the file must be LF, and it
must compile after the edit or the backup is restored.

    /root/wa/venv/bin/python3 -B patch_salary_policy_S240.py            (on the box)
    SP_PATH=./copy.py python3 -B patch_salary_policy_S240.py           (offline)
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("SP_PATH", "/root/staff_register/salary_policy.py")
MARK = "S240: flat pay shows no working"

A1_OLD = "salary÷%d"
A1_NEW = "salary÷%s"
A2_OLD = '% (s["day_divisor"], s["free_late_min"],'
A2_NEW = '% ("%g" % s["day_divisor"], s["free_late_min"],'
B_ANCHOR = '        vals = [st["name"], st["base"], st["adv_ded"], st["leaves_total"],'
B_INSERT = (
    '        if str(st["name"]).strip().lower() in dates_only_names(res.get("settings") or {}):\n'
    '            st = dict(st); st["leaves_total"] = 0   # S240: flat pay shows no working\n'
)


def main():
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    cur = hashlib.md5(raw).hexdigest()
    if MARK in src and A1_NEW in src:
        print("ALREADY CORRECTED; pin %s -- nothing to do" % cur)
        return 0
    if b"\r\n" in raw:
        sys.exit("REFUSING: %s has CRLF line endings; this box's file is LF (F-294)" % TARGET)
    for name, anchor in (("the footnote divisor", A1_OLD),
                         ("the footnote arguments", A2_OLD),
                         ("the sheet-3 row line", B_ANCHOR)):
        n = src.count(anchor)
        if n != 1:
            sys.exit("REFUSING: %s occurs %d times, expected exactly 1. Nothing was changed."
                     % (name, n))
    if "def dates_only_names(" not in src:
        sys.exit("REFUSING: dates_only_names() is not in this file -- the part-time setting is "
                 "not there, so the second correction cannot be made. Nothing was changed.")

    new = src.replace(A1_OLD, A1_NEW, 1).replace(A2_OLD, A2_NEW, 1)
    new = new.replace(B_ANCHOR, B_INSERT + B_ANCHOR, 1)

    bak = TARGET + ".bak_S240note_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as e:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: syntax error after the edit (%s); %s restored" % (e, TARGET))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("   footnote  : salary/30  ->  salary/30.5 (printed as it is)")
    print("   flat pay  : part-time rows show no leave working")
    print("   %s : %s -> %s" % (os.path.basename(TARGET), cur[:8], got[:8]))
    print("   backup    : %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
