#!/usr/bin/env python3
# =====================================================================
#  S193_STALE — hide stale "NOT-FILED at push time" flags.
#
#  The MARG_DAY_NOT_FILED data_flag is written at push time and never
#  cleared, so a day that was later filled (e.g. 17-Aug) keeps showing
#  in the Hub's "flagged NOT-FILED" note forever. This patch makes the
#  display query SELF-HEALING: a not-filed flag is shown only for a day
#  that STILL has no successful Marg batch. A day that now has Marg data
#  drops off the note automatically; a genuinely empty day (e.g. 19-Aug
#  before its export) correctly stays flagged. No rows are deleted.
#
#  In-place patch of /root/finance/finance_app.py. Fail-loud, idempotent.
# =====================================================================
import sys

TARGET = "/root/finance/finance_app.py"

OLD = '''    not_filed_flags = [dict(date=r["business_date"], detail=r["detail"])
                       for r in con.execute(
                           "SELECT business_date, detail FROM data_flag "
                           "WHERE unit=? AND code='MARG_DAY_NOT_FILED' "
                           "ORDER BY id DESC LIMIT 15", (UNIT,))]'''

NEW = '''    not_filed_flags = [dict(date=r["business_date"], detail=r["detail"])
                       for r in con.execute(
                           "SELECT df.business_date, df.detail FROM data_flag df "
                           "WHERE df.unit=? AND df.code='MARG_DAY_NOT_FILED' "
                           "AND NOT EXISTS (SELECT 1 FROM day_entry e "
                           "  JOIN ingest_batch b ON b.day_entry_id=e.id "
                           "  WHERE e.unit=df.unit AND e.business_date=df.business_date "
                           "  AND b.adapter='marg_export' AND b.status IN ('ok','partial')) "
                           "ORDER BY df.id DESC LIMIT 15", (UNIT,))]'''


def main():
    with open(TARGET, "r", encoding="utf-8") as fh:
        src = fh.read()
    if src.count(NEW) == 1 and src.count(OLD) == 0:
        print("      ALREADY PATCHED — nothing to do."); return
    if src.count(OLD) != 1:
        print("*** PREFLIGHT FAILED: anchor found %d time(s), expected 1. Nothing written."
              % src.count(OLD)); sys.exit(2)
    src = src.replace(OLD, NEW, 1)
    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(src)
    print("      stale not-filed flags now hidden when the day has Marg data.")


if __name__ == "__main__":
    main()
