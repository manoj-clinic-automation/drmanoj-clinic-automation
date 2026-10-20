#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s604.py -- kit S604_PAY_SHEET_FIXES (20-Oct-2026), F-955: the ONE audited data step. Bass Pharma's bill 14538 (29-Sep,
Rs 1,597) is on the store twice: bill 542 'BASS PHARMA DISTRIBUTORS PVT LTD' (bill-wise 9032f128) and bill 579 'BASS PHARMA
DISTRIBUTORS PVT' (supplier-wise 5307d3e5 -- Marg's supplier-wise sheet clipped the name: 'BASS PHARMA DISTRIBUTORS PVT' |
'LTD29-09-2026'). The supplier-wise carrying moves to 542; 579 is kept, retired ('twin of bill 542 ...'), and stops being
effective. Nothing is deleted. One transaction; both UPDATEs must touch exactly one row, else everything rolls back.

    python3 -B data_s604.py --db <finance.db or a copy>            the step (skipped, unchanged, when twin_merge 542<-579 exists)
    python3 -B data_s604.py --db <...> --undo                       back from the audit row's JSON (audited 'twin_merge_undone')
    python3 -B data_s604.py --db <...> --show                       the two rows and the audit rows, read only
"""
import argparse
import datetime as dt
import json
import sqlite3
import sys

REAL, TWIN = 542, 579
REF = "542<-579"
SW_MD5 = "5307d3e5b82ec416cb70144a9efaeb6e"
KEY_REAL, KEY_TWIN, BILL = "BASS PHARMA DISTRIBUTORS PVT LTD", "BASS PHARMA DISTRIBUTORS PVT", "14538"
REASON = "twin of bill 542 (supplier-wise clipped the name; S604)"


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def row(con, i):
    r = con.execute("SELECT * FROM purchase_bill WHERE id=?", (i,)).fetchone()
    return dict(r) if r else None


def show(con):
    for i in (REAL, TWIN):
        r = row(con, i)
        print("   bill %d: %s" % (i, None if r is None else {k: r[k] for k in ("supplier_norm", "bill_no", "bill_date", "amount_p", "bw_amount_p",
                                                                                  "sw_amount_p", "bw_md5", "sw_md5", "date_src", "reason")}))
    for r in con.execute("SELECT id, at, who, action, ref FROM purchase_audit WHERE action IN ('twin_merge','twin_merge_undone') AND ref=? ORDER BY id", (REF,)):
        print("   audit %s %s %s %s %s" % tuple(r))


def step(con):
    if con.execute("SELECT 1 FROM purchase_audit WHERE action='twin_merge' AND ref=? AND id > COALESCE((SELECT MAX(id) FROM purchase_audit "
                   "WHERE action='twin_merge_undone' AND ref=?), 0)", (REF, REF)).fetchone():
        print("DATA S604: SKIPPED -- the audit row twin_merge %s is already there; nothing changed" % REF)
        return 0
    a, b = row(con, REAL), row(con, TWIN)
    if not a or not b or a["supplier_norm"] != KEY_REAL or b["supplier_norm"] != KEY_TWIN or a["bill_no"] != BILL or b["bill_no"] != BILL \
            or a["bill_date"] != b["bill_date"] or a["bw_amount_p"] != b["sw_amount_p"]:
        print("DATA S604: REFUSED -- bills 542 / 579 are not the two rows the brief read (keys, bill, date, amounts); nothing changed")
        return 1
    try:
        con.execute("BEGIN IMMEDIATE")
        con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                    (now_iso(), "S604 data step", "twin_merge", REF,
                     json.dumps({"why": "F-955: Marg's supplier-wise sheet clipped the 32-letter name into the date cell "
                                        "('BASS PHARMA DISTRIBUTORS PVT' | 'LTD29-09-2026'); the supplier-wise carrying of 14538 joins bill 542",
                                 "542": a, "579": b}, ensure_ascii=False, sort_keys=True)))
        n1 = con.execute("UPDATE purchase_bill SET sw_md5=?, sw_amount_p=? WHERE id=? AND sw_md5 IS NULL", (SW_MD5, b["sw_amount_p"], REAL)).rowcount
        n2 = con.execute("UPDATE purchase_bill SET sw_md5=NULL, sw_amount_p=NULL, reason=? WHERE id=? AND sw_md5=? AND bw_md5 IS NULL",
                         (REASON, TWIN, SW_MD5)).rowcount
        if n1 != 1 or n2 != 1:
            con.execute("ROLLBACK")
            print("DATA S604: REFUSED -- the UPDATEs touched %d and %d rows (must be 1 and 1); rolled back, nothing changed" % (n1, n2))
            return 1
        con.execute("COMMIT")
    except sqlite3.Error as ex:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        print("DATA S604: REFUSED -- %s; rolled back, nothing changed" % ex)
        return 1
    print("DATA S604: DONE -- audit twin_merge %s written; bill 542 carries supplier-wise %s (Rs %d); bill 579 retired (%s)"
          % (REF, SW_MD5[:8], b["sw_amount_p"] // 100, REASON))
    return 0


def undo(con):
    r = con.execute("SELECT id, detail FROM purchase_audit WHERE action='twin_merge' AND ref=? ORDER BY id DESC LIMIT 1", (REF,)).fetchone()
    if not r:
        print("DATA S604 UNDO: no twin_merge %s audit row -- nothing to undo" % REF)
        return 1
    d = json.loads(r[1])
    a, b = d["542"], d["579"]
    con.execute("BEGIN IMMEDIATE")
    con.execute("UPDATE purchase_bill SET sw_md5=?, sw_amount_p=? WHERE id=?", (a["sw_md5"], a["sw_amount_p"], REAL))
    con.execute("UPDATE purchase_bill SET sw_md5=?, sw_amount_p=?, reason=? WHERE id=?", (b["sw_md5"], b["sw_amount_p"], b["reason"], TWIN))
    con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                (now_iso(), "S604 undo", "twin_merge_undone", REF, json.dumps({"from_audit": r[0]})))
    con.execute("COMMIT")
    print("DATA S604 UNDO: DONE -- bills 542 and 579 put back from audit row %d" % r[0])
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--undo", action="store_true")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    if a.show:
        con = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=60)
        con.row_factory = sqlite3.Row
        show(con)
        return 0
    con = sqlite3.connect(a.db, timeout=60, isolation_level=None)
    con.row_factory = sqlite3.Row
    rc = undo(con) if a.undo else step(con)
    show(con)
    con.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
