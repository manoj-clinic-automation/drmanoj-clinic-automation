#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s454p3.py -- kit S454_BILL_REGISTER, part 3: the data step, run by the installer on finance.db after its backup and after the new files are
placed and the service is healthy. Prints counts, item names and dates only -- never a phone or account number, never a key.

  * part 3's two settings at their defaults (order_sheet.ensure): order.stock_basis (count), stock.gap_min_packs (1)
  * the first set of gap rows at Marg's newest closing (shelf_figure.record_gaps) -- the baseline the next closing is compared with; nothing is
    flagged at the first closing (there is no earlier one to compare)
  * S454 9.1's boundary report: counts or spot answers whose clock time puts the count day's sales on the wrong side of the base

    data_s454p3.py --db /root/finance/finance.db --finance /root/finance
"""
import argparse
import os
import sqlite3
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--finance", required=True)
    a = ap.parse_args()
    sys.path.insert(0, a.finance)
    os.chdir(a.finance)
    import order_sheet as OS                                      # noqa: E402
    import shelf_figure as SF                                     # noqa: E402
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    OS.ensure(con)
    for k in ("order.stock_basis", "stock.gap_min_packs"):
        print("setting %s = %s" % (k, OS.setting(con, k)))
    as_on, snap = SF.latest_snapshot(con)
    n = SF.record_gaps(con)
    rows = con.execute("SELECT COUNT(*), SUM(flagged), SUM(approx), SUM(ABS(gap) >= pack) FROM s454_shelf_gap WHERE as_on=?", (as_on,)).fetchone()
    print("gap rows at Marg's closing of %s: %d written now (%s in all) · flagged %s · approximate %s · shelf and Marg a pack or more apart %s"
          % (as_on, n, rows[0], rows[1] or 0, rows[2] or 0, rows[3] or 0))
    F = SF.figures(con, items=list(snap))
    named = {}
    for f in F.values():
        named[f.get("named") or "counted"] = named.get(f.get("named") or "counted", 0) + 1
    print("the shelf figure today, by kind: %s" % dict(sorted(named.items())))
    b = SF.boundary_report(con)
    print("the boundary (S454 9.1): %d base(s) taken after 09:00 IST" % len(b))
    for x in b[:10]:
        print("   %s %s at %s%s" % (x["kind"], x["day"], x["at"][11:16], (" -- %s bills that day" % x["sales_that_day"]) if x.get("sales_that_day") is not None else ""))
    con.commit()
    print("S454 P3 data done")


if __name__ == "__main__":
    main()
