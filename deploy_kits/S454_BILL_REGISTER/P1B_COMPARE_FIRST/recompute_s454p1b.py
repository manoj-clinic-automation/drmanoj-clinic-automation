#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recompute_s454p1b.py -- kit S454_BILL_REGISTER, part 1B, the data step: the comparison kept for the sheets part 1 loaded "as already
ordered" (the first load of 02-Oct) is made again as it should have been -- on a backup-API scratch copy with that sheet's own paper orders
taken away -- and written into that sheet's row on the live database. Only a row that still holds part 1's figure (x = 0) is written;
an audit row names the change. Prints the figure before and after. Nothing else is written.

    recompute_s454p1b.py --db /root/finance/finance.db --finance /root/finance --marg /root/marg_ingest --work DIR
"""
import argparse
import json
import os
import sqlite3
import sys


def main():
    ap = argparse.ArgumentParser()
    for k in ("--db", "--finance", "--marg", "--work"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    for p in (a.finance, a.marg):
        sys.path.insert(0, p)
    os.makedirs(a.work, exist_ok=True)
    scratch = os.path.join(a.work, "recompute.db")
    s = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    d = sqlite3.connect(scratch)
    s.backup(d)
    d.close()
    s.close()
    os.environ["FINANCE_DB"] = scratch
    os.environ["ORDER_PUSH_STUB"] = os.path.join(a.work, "push_recompute.jsonl")
    import order_sheet as OS                                  # noqa: PLC0415
    sc = sqlite3.connect(scratch, timeout=60)
    sc.row_factory = sqlite3.Row
    done = 0
    for row in sc.execute("SELECT id, md5, newest_date, cmp FROM order_sheet WHERE as_ordered=1 ORDER BY id").fetchall():
        old = json.loads(row["cmp"] or "{}")
        if old.get("x") != 0:
            print("sheet #%d of %s: kept as it is (%s of %s)" % (row["id"], row["newest_date"], old.get("x"), old.get("y")))
            continue
        oids = [r[0] for r in sc.execute("SELECT id FROM purchase_order WHERE order_via='paper' AND sheet_id=?", (row["id"],))]
        q = ",".join("?" * len(oids))
        if oids:
            sc.execute("DELETE FROM purchase_order_line WHERE order_id IN (%s)" % q, oids)
            sc.execute("DELETE FROM purchase_order WHERE id IN (%s)" % q, oids)
            sc.commit()
        new = OS.compare(sc, row["id"])
        live = sqlite3.connect(a.db, timeout=60)
        cur = live.execute("UPDATE order_sheet SET cmp=?, cmp_at=? WHERE id=? AND md5=? AND cmp=?",      # only the row as part 1 left it
                           (json.dumps(new, ensure_ascii=False), new["at"], row["id"], row["md5"], row["cmp"]))
        if cur.rowcount == 1:
            OS.audit(live, "S454 P1B", "s454_cmp_recomputed", row["id"], dict(was="%s of %s" % (old.get("x"), old.get("y")),
                                                                               now="%s of %s" % (new["x"], new["y"]), paper_orders_set_aside=len(oids)))
            live.commit()
            done += 1
            print("sheet #%d of %s: the system agreed on %s of %s items (was %s of %s: its own %d paper orders had been counted as on the way); "
                  "in both: %s" % (row["id"], row["newest_date"], new["x"], new["y"], old.get("x"), old.get("y"), len(oids),
                                   ", ".join("%s (sheet %s, system %s)" % (b["item"], b["sheet"], b["system"]) for b in new["both"])))
        else:
            print("sheet #%d: the live row changed meanwhile -- not written" % row["id"])
        live.close()
    sc.close()
    print("S454 P1B recompute done: %d sheet row(s) written" % done)


if __name__ == "__main__":
    main()
