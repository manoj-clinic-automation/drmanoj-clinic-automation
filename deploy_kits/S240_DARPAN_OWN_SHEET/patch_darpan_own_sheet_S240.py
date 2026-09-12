#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_darpan_own_sheet_S240.py -- keep a named person OFF the main salary sheet.

THE OWNER, 12-Sep-2026:

    "Darpan has a complicated advance history, so I should keep him out of the salary sheet and
     make his own independent salary sheet -- one for myself and one for him. Mine will include
     all his running advances, extra, everything. His will include what he actually needs,
     nothing historical, so that he understands in one line what his leaves are, the deduction
     for them, the late minutes, the marks, and the deduction for those."

This change does ONLY the first half: his line no longer appears on sheets 3 and 4. His own two
sheets are a separate build. Until they exist he is simply not on the common sheet -- which is
also what removes the -1,949.07 that would otherwise sit on a page he signs.

HOW: the staff list is filtered ONCE, at the top of the sheet 3+4 renderer, so both sheets, the
serial numbers and every total follow from the same filter. Nothing is computed differently: his
pay, his advances and his ledger are untouched, and every other person's row is byte-identical.

The names come from the setting `own_sheet_staff` when it is set, and default to Darpan -- so the
list can be changed later without touching code.

It refuses rather than guesses: each anchor must occur EXACTLY ONCE, the file must be LF, and it
must compile after the edit or the backup is restored.

    /root/wa/venv/bin/python3 -B patch_darpan_own_sheet_S240.py           (on the box)
    SP_PATH=./copy.py python3 -B patch_darpan_own_sheet_S240.py           (offline)
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("SP_PATH", "/root/staff_register/salary_policy.py")
MARK = "S240: off the common sheet"

A_ANCHOR = "def dates_only_names(s):"
A_INSERT = '''OWN_SHEET_DEFAULT = "darpan"


def own_sheet_names(s):
    """Staff kept OFF the main salary sheet and paid on a sheet of their own.

    The owner, 12-Sep-2026: Darpan's advance history is long enough that one line on a shared
    sheet cannot tell the truth about it. Set `own_sheet_staff` in the settings to change who is
    on this list; it defaults to the name the owner gave."""
    raw = str(s.get("own_sheet_staff", "") or "").strip()
    return {x.strip().lower() for x in (raw or OWN_SHEET_DEFAULT).split(",") if x.strip()}


'''

B_ANCHOR = ('    cols = ["Name", "Salary", "Advance ded.", "Leaves", "Leave amt", "Late min",')
B_INSERT = (
    '    _own = own_sheet_names(res.get("settings") or {})   # S240: off the common sheet\n'
    '    if _own:\n'
    '        res = dict(res)\n'
    '        res["staff"] = [_s for _s in res["staff"]\n'
    '                        if str(_s["name"]).strip().lower() not in _own]\n'
)


def main():
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    raw = io.open(TARGET, "rb").read()
    src = raw.decode("utf-8")
    cur = hashlib.md5(raw).hexdigest()
    if MARK in src and "def own_sheet_names(" in src:
        print("ALREADY DONE; pin %s -- nothing to do" % cur)
        return 0
    if b"\r\n" in raw:
        sys.exit("REFUSING: %s has CRLF line endings; this box's file is LF (F-294)" % TARGET)
    for name, anchor in (("dates_only_names()", A_ANCHOR), ("the sheet 3 column list", B_ANCHOR)):
        n = src.count(anchor)
        if n != 1:
            sys.exit("REFUSING: %s occurs %d times, expected exactly 1. Nothing was changed."
                     % (name, n))
    if src.index(B_ANCHOR) < src.index(A_ANCHOR):
        sys.exit("REFUSING: the column list comes before dates_only_names(); the helper would be "
                 "defined after it is used. Nothing was changed.")

    new = src.replace(A_ANCHOR, A_INSERT + A_ANCHOR, 1).replace(B_ANCHOR, B_INSERT + B_ANCHOR, 1)
    bak = TARGET + ".bak_S240darpan_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        compile(new, TARGET, "exec")
    except SyntaxError as e:
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: syntax error after the edit (%s); %s restored" % (e, TARGET))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("   off the common sheet : %s (settings key own_sheet_staff)" % OWN_NAME(new))
    print("   %s : %s -> %s" % (os.path.basename(TARGET), cur[:8], got[:8]))
    print("   backup    : %s" % bak)
    return 0


def OWN_NAME(src):
    i = src.find('OWN_SHEET_DEFAULT = "')
    return src[i + 21:src.find('"', i + 21)] if i >= 0 else "?"


if __name__ == "__main__":
    sys.exit(main())
