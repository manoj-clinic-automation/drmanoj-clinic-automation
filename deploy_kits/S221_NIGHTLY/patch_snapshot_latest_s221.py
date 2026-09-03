#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_snapshot_latest_s221.py -- S221: two exports, one date, and which one wins.

THE OWNER, 03-Sep-2026:

    "if i export one tonight, 2 will be of same date, but different, build accordingly"

He is right, and today it is undefined. `newest_full()` chooses with

    max(cands, key=(as_on_key, len(rows)))

so between two FULL exports taken on the same day -- one at midday, one after
closing -- the row counts are equal, `max` keeps whichever the filesystem
happened to list first, and the winner is decided by glob order. Two runs of the
same script on the same archive could disagree.

THE RULE, added as the last tiebreaker: for one date, THE LATEST-TAKEN full
export wins. A shelf figure taken after the last bill of the day supersedes one
taken at midday, and that is the only sensible reading of two counts of the same
shelf.

The capture stamp is already in every filename -- the third `__` field:

    STOCK_CLOSING_TOTALS__2026-09-02__20260902-172308__708b0f28.XLS
                                      ^^^^^^^^^^^^^^^

The F-235 guard is untouched: a category-filtered subset still loses on row
count before the timestamp is ever consulted, so a small late export can never
beat a full early one.

Target: D:\\dr-manoj-git\\drmanoj-clinic-automation\\deploy_kits\\S208_STOCK_LEDGER\\push_snapshot.py
        (pin 72205205230421e55e152c85838a0868) -- runs on MANOJZ, not the VPS.
Offline / on manojz:  python -B patch_snapshot_latest_s221.py
"""

import datetime as dt
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.environ.get('PS_PATH', os.path.join(HERE, 'push_snapshot.py'))
MARK = "S221 LATEST WINS"


A_OLD = '''    if not cands:
        return None, []
    best_name, best = max(cands, key=lambda c: (as_on_key(c[1].get("as_on")),
                                                len(c[1]["rows"])))
'''

A_NEW = '''    if not cands:
        return None, []

    # S221 LATEST WINS -- the third tiebreaker.
    # Two FULL exports of the same date have equal row counts, so max() used to
    # keep whichever glob listed first: the winner was decided by filesystem
    # order. The capture stamp is in the filename, so use it. A shelf counted
    # after the last bill supersedes one counted at midday.
    # Row count is still compared FIRST, so the F-235 guard stands: a
    # category-filtered subset cannot win by being late.
    def _taken(name):
        parts = str(name).split("__")
        return parts[2] if len(parts) > 2 else ""

    best_name, best = max(cands, key=lambda c: (as_on_key(c[1].get("as_on")),
                                                len(c[1]["rows"]),
                                                _taken(c[0])))
'''

PAIRS = [("A", A_OLD, A_NEW)]


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
    bak = TARGET + ".bak_S221_latest_" + stamp
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
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    return 0


if __name__ == "__main__":
    sys.exit(main())
