#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""patch_finance_app_pend.py — one predicate for "is this day's Marg export in?"

THE CONTRADICTION (owner, 29-Aug): /finance/review said 27-Aug was approved;
#pendCard on approvals flagged the same day "not filed". Both were reading
different predicates. pendCard's `missing_marg` demands an APPLIED ingest_batch
row -- but a pushed report that is still sitting in marg_push_staging
(ACCEPTED-FOR-REVIEW, awaiting the workbench) covers the day just as truly.
The export exists; only the apply is pending.

THE FIX: the missing_marg query also accepts a staging row (pending or
applied) whose survey covers the date. One clause, additive; the review page
was right and is untouched.

Anchored on the exact query text. If the live file's text has drifted, this
REFUSES -- and the installer treats that as a warning, not a failure, because
this fix is display-honesty, not money.

    python3 patch_finance_app_pend.py --check  <finance_app.py>
    python3 patch_finance_app_pend.py --apply  <finance_app.py>
    python3 patch_finance_app_pend.py --revert <finance_app.py>
"""
import io
import os
import sys

OLD = (
    '''        "(SELECT 1 FROM ingest_batch b WHERE b.day_entry_id=e.id "
        " AND b.adapter='marg_export' AND b.status IN ('ok','partial')) "
        "ORDER BY e.business_date DESC", (UNIT, horizon, today_iso))]''')

NEW = (
    '''        "(SELECT 1 FROM ingest_batch b WHERE b.day_entry_id=e.id "
        " AND b.adapter='marg_export' AND b.status IN ('ok','partial')) "
        # S208_PEND: a pushed report still sitting in staging covers the day
        # just as truly as an applied one -- the export exists, only the apply
        # is pending. Without this, review said "approved" while pendCard said
        # "not filed" about the same day, and both were sincere.
        "AND NOT EXISTS (SELECT 1 FROM marg_push_staging s WHERE "
        " s.unit=e.unit AND s.status IN ('pending','applied') "
        " AND s.survey_json LIKE '%\\"'||e.business_date||'\\"%') "
        "ORDER BY e.business_date DESC", (UNIT, horizon, today_iso))]''')


def main(argv):
    if len(argv) < 3 or argv[1] not in ("--check", "--apply", "--revert"):
        print(__doc__)
        return 1
    mode, path = argv[1], argv[2]
    if not os.path.isfile(path):
        print("!! not a file: %s" % path)
        return 1
    src = io.open(path, encoding="utf-8").read()
    n_old, n_new = src.count(OLD), src.count(NEW)
    if mode == "--check":
        if n_new:
            print("already patched")
            return 0
        print("anchor occurs %d time(s), expected exactly 1" % n_old)
        return 0 if n_old == 1 else 1
    if mode == "--apply":
        if n_new:
            print("already patched -- nothing written")
            return 0
        if n_old != 1:
            print("REFUSED: anchor occurs %d time(s), expected 1 -- "
                  "nothing written" % n_old)
            return 1
        out = src.replace(OLD, NEW)
    else:
        if not n_new:
            print("not patched -- nothing to revert")
            return 0
        out = src.replace(NEW, OLD)
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print("%s: done, %d -> %d bytes" % (mode, len(src), len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
