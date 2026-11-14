#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repair_s827.py -- S827 (F-1243, the owner's word 08:24 IST 14-Nov to proceed on August, a FINAL month): Deepam Pharma's bill 502 of
18-Aug-2026. Its item lines of the LIVE exports are stored under MANNAT PHARMA (the bill Amir moved to Deepam in Marg); they are moved
to DEEPAM PHARMA -- only when every condition holds: Deepam's 502 of that day is a live bill, Mannat's is not, and exactly the
expected live lines are found. One transaction; the lines' state before is written beside the database; one audit row.
    python3 -B repair_s827.py <finance.db> [--dry]
Last line: REPAIR S827: moved N | already | DRY N | REFUSED <why>"""
import datetime as dt
import json
import os
import sqlite3
import sys

SUP_FROM, SUP_TO, NO, DAY = "MANNAT PHARMA", "DEEPAM PHARMA", "502", "2026-08-18"
EFF = "EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND (e.md5=b.bw_md5 OR e.md5=b.sw_md5))"
LIVE_LINE = "EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND e.md5=l.source_md5)"


def main():
    db = sys.argv[1]
    dry = "--dry" in sys.argv[2:]
    con = sqlite3.connect(db, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        con.execute("BEGIN IMMEDIATE")
        to_live = con.execute("SELECT COUNT(*) FROM purchase_bill b WHERE supplier_norm=? AND bill_no=? AND bill_date=? AND " + EFF,
                              (SUP_TO, NO, DAY)).fetchone()[0]
        from_live = con.execute("SELECT COUNT(*) FROM purchase_bill b WHERE supplier_norm=? AND bill_no=? AND bill_date=? AND " + EFF,
                                (SUP_FROM, NO, DAY)).fetchone()[0]
        rows = [dict(r) for r in con.execute("SELECT l.* FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_no=? AND l.bill_date=? AND "
                                             + LIVE_LINE + " ORDER BY l.id", (SUP_FROM, NO, DAY))]
        have = con.execute("SELECT COUNT(*) FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_no=? AND l.bill_date=? AND " + LIVE_LINE,
                           (SUP_TO, NO, DAY)).fetchone()[0]
        if not rows and have:
            con.rollback()
            print("REPAIR S827: already (Deepam's 502 holds %d live line(s); none under Mannat)" % have)
            return 0
        why = []
        if to_live != 1:
            why.append("Deepam's 502 of 18-Aug is not one live bill (%d)" % to_live)
        if from_live != 0:
            why.append("Mannat's 502 of 18-Aug is still a live bill")
        if not (1 <= len(rows) <= 3) or any(str(r["item"]).strip().upper() != "ROSIKA FORTE" for r in rows):
            why.append("the live lines under Mannat are not the expected ROSIKA FORTE line(s) (%d)" % len(rows))
        if why:
            con.rollback()
            print("REPAIR S827: REFUSED " + "; ".join(why))
            return 1
        for r in rows:
            print("  line %s  %-13s %-12s qty %s  %s -> %s" % (r["id"], r["line_type"], r["item"], r["qty"], SUP_FROM, SUP_TO))
        if dry:
            con.rollback()
            print("REPAIR S827: DRY %d" % len(rows))
            return 0
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(os.path.dirname(os.path.abspath(db)), "s827_repair_before_%s.json" % stamp), "w") as f:
            json.dump(rows, f, indent=1, default=str)
        con.executemany("UPDATE purchase_line SET supplier_norm=? WHERE id=? AND supplier_norm=?", [(SUP_TO, r["id"], SUP_FROM) for r in rows])
        con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                    (dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "S827", "s827_repair", "%s|%s|%s" % (SUP_TO, NO, DAY),
                     json.dumps(dict(moved=[r["id"] for r in rows], frm=SUP_FROM, to=SUP_TO, why="F-1243: the bill moved to Deepam in Marg"))))
        left = con.execute("SELECT COUNT(*) FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_no=? AND l.bill_date=? AND " + LIVE_LINE,
                           (SUP_FROM, NO, DAY)).fetchone()[0]
        if left:
            con.rollback()
            print("REPAIR S827: REFUSED a line stayed under Mannat after the move -- rolled back")
            return 1
        con.commit()
        print("REPAIR S827: moved %d" % len(rows))
        return 0
    except sqlite3.Error as e:
        con.rollback()
        print("REPAIR S827: REFUSED database: %s" % e)
        return 1
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
