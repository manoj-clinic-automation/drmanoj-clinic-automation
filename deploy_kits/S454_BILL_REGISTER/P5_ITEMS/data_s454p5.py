#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s454p5.py -- kit S454_BILL_REGISTER, part 5: the data step, run by the installer on finance.db after its backup and after the new files are
placed and the service is healthy. Prints counts, item names and supplier names only -- never a phone or account number, never a key.

  * the Sarvam check and the learner once (purchase_app.sarvam_compare): the names learnt from today's verified bills, and the rows of
    those suppliers' bills compared again by them
  * September's item figure (scan_register.sarvam) before and after; the items check of August, September and October (S454 11.1)

    data_s454p5.py --db /root/finance/finance.db --finance /root/finance
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
    import purchase_app as pa                                     # noqa: E402
    import scan_register as SR                                    # noqa: E402
    import item_check as IC                                       # noqa: E402
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    IC.ensure(con)
    before = SR.sarvam(con, "2026-09")
    n0 = len(IC.learnt(con))
    n = pa.sarvam_compare(con)
    after = SR.sarvam(con, "2026-09")
    L = IC.learnt(con)
    print("the Sarvam check and the learner: %d row(s) compared; item names learnt: %d (were %d)" % (n, len(L), n0))
    for x in L[:40]:
        print("   %s: '%s' = %s" % (x["supplier_norm"], x["scan_name"], x["marg_item"]))
    print("September's item figure: %d of %d item lines read right before, %d of %d after" % (before["items_right"], before["items_read"], after["items_right"],
                                                                                           after["items_read"]))
    for m in ("2026-08", "2026-09", "2026-10"):
        r = IC.items_check(con, m)
        print("items check %s: %d of %d bills with lines add up, %d do not, %d with no lines" % (m, r["adds"], r["n"] - r["nolines"], r["differs"], r["nolines"]))
    con.commit()
    print("S454 P5 data done")


if __name__ == "__main__":
    main()
