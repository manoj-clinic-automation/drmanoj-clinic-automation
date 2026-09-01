#!/usr/bin/env python3
"""
legacy_sweep.py -- S217: close the legacy-era open differences.

THE OWNER'S RULING (01-Sep-2026, in chat): live data runs from 17-Aug-2026
(margpull `_coverage_from.txt` = 2026-08-17); the item-wise matching and the
stock/purchase reconstruction are COMPLETE for the era before it, so the old
open rows are noise on the page. His words: "all matching has been done ...
harmless to remove - its your call."

WHAT IT DOES: every recon_exception with business_date < 2026-08-17 and
status='open' -> status='resolved', with a resolution string naming this
ruling. NOTHING is deleted -- the rows and their history stay readable.
Prints every row it touches. DRY-RUN by default; --apply to write.
"""
import datetime as dt
import os
import sqlite3
import sys

DB_PATH = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
CUTOFF = os.environ.get("LEGACY_CUTOFF", "2026-08-17")
REASON = ("legacy era (before %s) - item-wise matching and stock/purchase "
          "reconstruction complete; closed on the owner's ruling, S217, "
          "01-Sep-2026" % CUTOFF)


def main():
    apply_ = "--apply" in sys.argv
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "SELECT id, unit, business_date, kind, diff_p, detail FROM recon_exception "
        "WHERE status='open' AND business_date < ? ORDER BY business_date", (CUTOFF,))]
    print("open legacy rows (before %s): %d" % (CUTOFF, len(rows)))
    for r in rows:
        print("  #%(id)s %(unit)s %(business_date)s %(kind)s diff %(diff_p)s" % r)
    if not rows:
        print("nothing to close")
        return 0
    if not apply_:
        print("\nDRY-RUN ONLY. Re-run with --apply to close them.")
        return 0
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute(
        "UPDATE recon_exception SET status='resolved', resolution=?, "
        "closed_by='manoj', closed_at=? WHERE status='open' AND business_date < ?",
        (REASON, now, CUTOFF))
    con.commit()
    left = con.execute("SELECT COUNT(*) c FROM recon_exception WHERE status='open' "
                       "AND business_date < ?", (CUTOFF,)).fetchone()["c"]
    print("closed. legacy rows still open: %d" % left)
    return 0 if left == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
