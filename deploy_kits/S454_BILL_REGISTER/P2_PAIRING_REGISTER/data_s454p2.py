#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s454p2.py -- kit S454_BILL_REGISTER, part 2: the data step, run by the installer on finance.db after its backup and after the new files are
placed and the service is healthy. Prints counts, bill numbers and stamps only -- never a phone or account number, never a key.

  * part 2's four settings at their defaults (order_sheet.ensure): purchase.entry_mode, purchase.total_noise_rs, purchase.scan_wait_days,
    purchase.entry_wait_days
  * one pass of the matcher under the new rules (purchase_app._rematch) -- the auto-links it makes are audited (auto_link) and listed here;
    a link that exists is never undone (the pass reports any it drops: it must be none)
  * the owner's returns rule's own count kept as setting returns.pending_ok (amir_day._s454_returns_cache) -- manoj.returns_ok reads it

    data_s454p2.py --db /root/finance/finance.db --finance /root/finance
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
    import order_sheet as OS                                      # noqa: E402
    pa._assets_db = os.environ.get("ASSETS_DB", pa._assets_db)
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    OS.ensure(con)
    for k in ("purchase.entry_mode", "purchase.total_noise_rs", "purchase.scan_wait_days", "purchase.entry_wait_days"):
        print("setting %s = %s" % (k, OS.setting(con, k)))
    before = {r[0]: r[1] for r in con.execute("SELECT bill_id, asset_bill_id FROM purchase_scan_link")}
    r = pa._rematch(con, "S454 P2 install")
    after = {r_[0]: (r_[1], r_[2]) for r_ in con.execute("SELECT bill_id, asset_bill_id, grade FROM purchase_scan_link")}
    if r is None:
        print("the matcher: the asset app's database is not reachable -- no pass made")
    else:
        print("the matcher: %d links stored (were %d) · %d new · %d dropped · reasons %s" % (r["links"], len(before), r["new"], r["dropped"],
                                                                                         dict(sorted((r.get("reasons") or {}).items()))))
    for bid, (sid, grade) in sorted(after.items()):
        if bid in before:
            continue
        b = con.execute("SELECT supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE id=?", (bid,)).fetchone()
        print("   new link (%s): %s bill %s of %s, Rs %.2f <- scan #%d" % (grade, pa.supplier_key(b[0]), b[1], b[2], (b[3] or 0) / 100.0, sid))
    gone = [b for b in before if b not in after]
    print("   links dropped: %s" % (gone or "none"))
    try:
        import amir_day                                           # noqa: E402
        amir_day._s454_returns_cache(con)
        v = con.execute("SELECT value FROM setting WHERE key='returns.pending_ok'").fetchone()
        print("returns.pending_ok = %s (n | the oldest)" % (v[0] if v else "not written"))
    except Exception as e:                                        # noqa: BLE001
        print("returns.pending_ok not written: %s" % str(e)[:120])
    con.commit()
    print("S454 P2 data done" if not gone else "S454 P2 data RED -- a link was dropped")


if __name__ == "__main__":
    main()
