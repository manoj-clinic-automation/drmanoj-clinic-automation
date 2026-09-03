#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_darpan_viewer_s221.py -- S221: Amir can open his own desk.

THE FAULT, found the hour Amir was onboarded.

`S218_CARDS_FINAL_CONTRACT` A12 assigns the UPI/CASH corrections desk to Amir by
name. The live code requires `checker` for it -- the owner's approval role, the
one that signs off the day's money. So the desk that is his on paper refuses him
in fact. He would have logged in on his next visit, tapped his own card, and
been turned away.

WHAT THIS DOES, AND DELIBERATELY NO MORE. Three endpoints -- the page, the list
it reads, and the tick that closes one line -- learn to accept `viewer`
alongside `checker`. Nothing else in this file moves.

WHY `viewer` AND NOT `maker`. `unit_role` allows exactly maker, checker, viewer,
and `medical.entry_role = maker` is the setting that means *files the day*.
Making Amir a maker to let him tick a correction would hand a purchase man the
day's money entry. Viewer is what this system already uses for named staff on
one desk: Reception holds `viewer` on the medical unit for the Vaapsi desk and
writes return slips with it (S214). Viewer is scoped, not read-only.

WHAT AMIR STILL CANNOT DO, and this is the point of choosing viewer:
    /finance/darpan/api/transfer      owner-only money movement   -- untouched
    /finance/darpan/api/ledger-check  the owner's ledger tool     -- untouched
    the day's entry and approval, the drawer, every other route   -- untouched
Both of those remain `checker`. If he ever taps a control for one, the server
refuses him -- the page still draws the control, which is cosmetic and is
recorded as a follow-up rather than fixed here: this kit does not touch a page.

Target: /root/finance/darpan_app.py (live pin 43abdd58..., reproduced offline
through all eight S220 patchers from the S219-close base f4161c7d -- every
intermediate matching its recorded pin -- before a line of this was written)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_darpan_viewer_s221.py
Offline:         DARPAN_PATH=./darpan_app.py python3 -B patch_darpan_viewer_s221.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('DARPAN_PATH', '/root/finance/darpan_app.py')
MARK = "S221 AMIR VIEWER"


A_OLD = '''@bp.route("/finance/darpan/corrections")
def page_corrections():
    u, err = _require("checker")
'''

A_NEW = '''@bp.route("/finance/darpan/corrections")
def page_corrections():
    # S221 AMIR VIEWER -- this desk is Amir's by the S218 contract; viewer is
    # how named staff hold one desk without unit-wide authority (S214).
    u, err = _require("checker", "viewer")
'''


B_OLD = '''@bp.route("/finance/darpan/api/corrections")
def api_corrections():
    u, err = _require("checker")
'''

B_NEW = '''@bp.route("/finance/darpan/api/corrections")
def api_corrections():
    u, err = _require("checker", "viewer")          # S221 AMIR VIEWER
'''


C_OLD = '''def api_tick(mid):
    u, err = _require("checker")
'''

C_NEW = '''def api_tick(mid):
    # S221 AMIR VIEWER -- ticking a correction he has fixed in Marg IS the job.
    # A desk he can read but not close would be worse than no desk.
    u, err = _require("checker", "viewer")
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S221_amir_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). "
                         "RESTORED from %s." % (ex, bak))
    # The money routes must not have moved. Checked here, not assumed -- and
    # checked on the FIRST _require after the def, not on a fixed window: the
    # first version of this guard used out[i:i+400] and api_transfer's require
    # begins at +392, so it was cut in half and the guard fired on a correct
    # file. A guard that cries wolf gets switched off, so it is exact now.
    for guard in ('def api_transfer(', 'def api_ledger_check('):
        i = out.find(guard)
        j = out.find('_require(', i) if i >= 0 else -1
        if i < 0 or j < 0 or not out[j:].startswith('_require("checker")'):
            shutil.copyfile(bak, TARGET)
            raise SystemExit("REFUSED: %s is no longer checker-only. "
                             "RESTORED from %s." % (guard, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("guarded  api_transfer and api_ledger_check are still checker-only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
