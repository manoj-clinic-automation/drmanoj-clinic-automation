#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_stock_viewer_s221.py -- S221: the stock pages accept a named counter.

The owner put Amir on stock count this morning ("might need 2 persons"). The
pages require `maker` -- and `medical.entry_role = maker` is the setting that
means *files the day*. Amir counting a shelf must not carry the day's money
entry with it.

FOUR endpoints learn `viewer`, and they are the four a counter needs:

    /page/count      the counting screen
    /api/count       submitting the finished count
    /page/diffs      seeing what came out of it
    /api/open        the list that page reads

DELIBERATELY NOT RELAXED, and each for a reason:

    /api/diff/<id>/cause      naming the cause closes a difference -- checker
    /api/diff/<id>/decision   write off or recover -- the owner alone
    /api/rate                 setting a price -- the owner alone
    /api/voucher              the Marg adjustment record -- maker or checker
    /page/drift, /api/drift   feed health, an owner's screen
    /api/losses               where stock goes, by cause -- an owner's report
    _snapshot_auth            the machine token path -- untouched entirely

So a counter can count and can see the difference his count produced. He cannot
value it, explain it away, or decide it. That separation is the whole reason the
finding is worth anything: the man who counted is not the man who rules on it.

Target: /root/finance/stock_app.py (pin 74825031... == S213 + FINDING +
TWO_PRICES + PURCHASE_DUE, reproduced offline and md5-proven before building)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_stock_viewer_s221.py
Offline:         SA_PATH=./stock_app.py python3 -B patch_stock_viewer_s221.py
"""

import datetime as dt
import os
import shutil
import sys

TARGET = os.environ.get('SA_PATH', '/root/finance/stock_app.py')
MARK = "S221 COUNTER VIEWER"


A_OLD = '''    stopped needing a machine to fill them.
    """
    u, err = _require("checker", "maker")
'''

A_NEW = '''    stopped needing a machine to fill them.
    """
    # S221 COUNTER VIEWER -- a named counter holds `viewer`, never `maker`:
    # maker is the day's money entry (medical.entry_role).
    u, err = _require("checker", "maker", "viewer")
'''


B_OLD = '''    of. Renders /api/open; each cause button posts /api/diff/<id>/cause."""
    u, err = _require("checker", "maker")
'''

B_NEW = '''    of. Renders /api/open; each cause button posts /api/diff/<id>/cause."""
    # S221 COUNTER VIEWER -- he may SEE the difference his count produced.
    # Naming its cause is still checker-only; that button will refuse him.
    u, err = _require("checker", "maker", "viewer")
'''


C_OLD = '''                     "loose":..,"pack_size":..,"packing":..,"counted_by":..,
                     "entered_by":..,"at":..,"batches":{...}}]}
    """
    u, err = _require("checker", "maker")
'''

C_NEW = '''                     "loose":..,"pack_size":..,"packing":..,"counted_by":..,
                     "entered_by":..,"at":..,"batches":{...}}]}
    """
    u, err = _require("checker", "maker", "viewer")     # S221 COUNTER VIEWER
'''


D_OLD = '''    # token must reach NOTHING but /api/snapshot, and this is what makes that
    # true in this file rather than in another one.
    u, err = _require("checker", "maker")
'''

D_NEW = '''    # token must reach NOTHING but /api/snapshot, and this is what makes that
    # true in this file rather than in another one.
    u, err = _require("checker", "maker", "viewer")     # S221 COUNTER VIEWER
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW),
         ("D", D_OLD, D_NEW)]

# These must still refuse a viewer when this patcher is done. Checked on the
# FIRST _require after each def, exactly -- not on a fixed window.
MUST_STAY = {"api_cause": '_require("checker")',
             "api_diff_decision": '_require("checker")',
             "api_rate": '_require("checker")',
             "api_voucher": '_require("checker", "maker")',
             "api_drift": '_require("checker", "maker")',
             "api_losses": '_require("checker", "maker")',
             "_snapshot_auth": '_require("checker", "maker")'}


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
    bak = TARGET + ".bak_S221_counter_" + stamp
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
    for fn, want in MUST_STAY.items():
        i = out.find("def %s(" % fn)
        j = out.find("_require(", i) if i >= 0 else -1
        if i < 0 or j < 0 or not out[j:].startswith(want):
            shutil.copyfile(bak, TARGET)
            raise SystemExit("REFUSED: %s should still read %s and does not. "
                             "RESTORED from %s." % (fn, want, bak))
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("guarded  %d routes verified still closed to a viewer" % len(MUST_STAY))
    return 0


if __name__ == "__main__":
    sys.exit(main())
