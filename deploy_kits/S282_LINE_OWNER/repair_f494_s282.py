#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repair_f494_s282.py -- the one-off pass over finance.db for the lines already
stored without a supplier (F-494). The SAME rule as _line_owner_s282 in the
patched purchase_app.py, run once so the five September lines do not have to
wait for the next purchase push to arrive.

    python3 -B repair_f494_s282.py --db /root/finance/finance.db            # writes
    python3 -B repair_f494_s282.py --db /root/finance/finance.db --dry-run  # reports only

Prints what it found before, what it placed and where, and what is left. A line
it cannot place with one ITEMWISE witness among the candidates is left exactly
as it was and named in the output.
"""
import argparse
import sqlite3
import sys


def rupees(p):
    return "{:,.2f}".format((p or 0) / 100.0)


def orphans(con):
    return con.execute("SELECT COUNT(*), COALESCE(SUM(net_amount_p),0) FROM purchase_line "
                       "WHERE supplier_norm IS NULL").fetchone()


def by_no_map(con):
    by_no = {}
    for r in con.execute("SELECT supplier_norm, bill_no, bill_date FROM purchase_bill "
                         "WHERE bill_date IS NOT NULL ORDER BY bill_date"):
        by_no.setdefault(r[1], []).append((r[0], r[2]))
    return by_no


def place(con, by_no, write=True):
    """Identical to _line_owner_s282, plus a record of each decision."""
    placed, left = [], []
    for r in con.execute("SELECT id, bill_no, bill_date, item, amount_p FROM purchase_line "
                         "WHERE supplier_norm IS NULL AND bill_no IS NOT NULL AND "
                         "bill_date IS NOT NULL").fetchall():
        cands = {c[0] for c in (by_no.get(r[1]) or []) if c[1] == r[2]}
        if len(cands) < 2:
            left.append((r, "bill names %d supplier(s) -- not this fault" % len(cands)))
            continue
        w = {x[0] for x in con.execute(
            "SELECT DISTINCT supplier_norm FROM purchase_line WHERE line_type='ITEMWISE' AND "
            "supplier_norm IS NOT NULL AND bill_no=? AND bill_date=? AND item=? AND amount_p IS ?",
            (r[1], r[2], r[3], r[4])).fetchall()}
        if len(w) == 1 and w <= cands:
            sup = w.pop()
            if write:
                con.execute("UPDATE purchase_line SET supplier_norm=? WHERE id=?", (sup, r[0]))
            placed.append((r, sup))
        else:
            left.append((r, "ITEMWISE names %d owner(s) %s; candidates %s"
                         % (len(w), sorted(w), sorted(cands))))
    return placed, left


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    con = sqlite3.connect(a.db)
    n0, p0 = orphans(con)
    print("before : %d line(s) with no supplier, Rs %s" % (n0, rupees(p0)))
    placed, left = place(con, by_no_map(con), write=not a.dry_run)
    for r, sup in placed:
        print("placed : line %d  bill %s of %s  %-28s Rs %10s  -> %s"
              % (r[0], r[1], r[2], r[3][:28], rupees(r[4]), sup))
    for r, why in left:
        print("left   : line %d  bill %s of %s  %-28s -- %s" % (r[0], r[1], r[2], r[3][:28], why))
    if a.dry_run:
        con.rollback()
        print("dry run: nothing written")
    else:
        con.execute("UPDATE purchase_line SET month=substr(bill_date,1,7) WHERE bill_date IS NOT NULL")
        con.commit()
    n1, p1 = orphans(con)
    print("after  : %d line(s) with no supplier, Rs %s   (placed %d, left %d)"
          % (n1, rupees(p1), len(placed), len(left)))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
