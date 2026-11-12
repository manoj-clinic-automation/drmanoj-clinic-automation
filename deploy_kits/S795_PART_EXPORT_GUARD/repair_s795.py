#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repair_s795.py --db FINANCE_DB [--apply] -- puts right every pair where a PART list retired a fuller purchase export.

A pair: a live export L and an export S that L retired (S.superseded_by = L.md5), the same type, S's period inside L's,
and L a part of S by the kit's own rule (L.n_rows < half of S.n_rows, and more than two rows short).
ONLY BILL LISTS (bill-wise, supplier-wise) are put right: a bill row exists once whatever list carries it.  A pair of LINE
lists (item-wise), or one whose period another live report of the type already covers, is listed and LEFT ALONE (making
the fuller one live again could count its rows twice).
The repair: S is live again; L is marked retired by S.  For bill-wise / supplier-wise lists the bills that hang on L are
re-hung on S -- only when S's count proves it holds them (bills on S + bills on L = S.n_rows); otherwise L stays live
beside S (a bill is effective while either list is) and the line says so.  Then the scan pairing's "seen" mark is cleared,
so the next look at the purchase pages pairs the scans again.  Without --apply it only lists.  The before-state of every
row it changes is written beside the database (s795_repair_before_<stamp>.json).  Running it twice changes nothing more."""
import datetime as dt
import json
import os
import sqlite3
import sys

HALF, GAP = 0.5, 2
COL = {"BILLWISE": "bw_md5", "SUPPLIERWISE": "sw_md5"}


def pairs(con, with_skipped=False):
    out, skipped = [], []
    for l_md5, typ, l_pf, l_pt, l_n in con.execute(
            "SELECT md5, type, period_from, period_to, COALESCE(n_rows,0) FROM purchase_export WHERE superseded_by IS NULL").fetchall():
        for s_md5, s_n, s_stamp in con.execute(
                "SELECT md5, COALESCE(n_rows,0), export_stamp FROM purchase_export WHERE superseded_by=? AND type=? AND period_from>=? "
                "AND period_to<=? ORDER BY COALESCE(n_rows,0) DESC, export_stamp DESC", (l_md5, typ, l_pf, l_pt)).fetchall():
            if l_n < HALF * s_n and s_n - l_n > GAP:
                s_pf, s_pt = con.execute("SELECT period_from, period_to FROM purchase_export WHERE md5=?", (s_md5,)).fetchone()
                other = con.execute("SELECT COUNT(*) FROM purchase_export WHERE superseded_by IS NULL AND type=? AND md5<>? "
                                    "AND period_from<=? AND period_to>=?", (typ, l_md5, s_pt, s_pf)).fetchone()[0]
                d = dict(type=typ, part=l_md5, part_rows=l_n, full=s_md5, full_rows=s_n, period="%s..%s" % (l_pf, l_pt))
                d["why"] = ("a line list -- only bill lists are put right by this kit" if typ not in COL else
                            "other live reports already cover this period" if other else "")
                (skipped if d["why"] else out).append(d)         # a bill row exists once whatever list carries it; a line does not
                break
    return (out, skipped) if with_skipped else out


def effective(con, month=None):
    q = ("SELECT COUNT(*) FROM purchase_bill b WHERE EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL "
         "AND (e.md5=b.bw_md5 OR e.md5=b.sw_md5))")
    return con.execute(q + (" AND b.month=?" if month else ""), (month,) if month else ()).fetchone()[0]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    db = argv[argv.index("--db") + 1]
    apply_ = "--apply" in argv
    con = sqlite3.connect(db, timeout=60)
    found, skipped = pairs(con, True)
    print("S795 repair: %d pair(s) where a part list retired a fuller one; effective bills now %d" % (len(found), effective(con)))
    for p in skipped:
        print("  LEFT ALONE   %-12s %s  part %s (%d rows) / full %s (%d rows): %s" % (
            p["type"], p["period"], p["part"][:8], p["part_rows"], p["full"][:8], p["full_rows"], p["why"]))
    for p in found:
        print("  %-12s %s  part %s (%d rows) retired full %s (%d rows)" % (p["type"], p["period"], p["part"][:8], p["part_rows"], p["full"][:8], p["full_rows"]))
    if not apply_ or not found:
        print("S795 repair END -- %s" % ("nothing to put right" if not found else "listed only (no --apply); nothing written"))
        return 0
    before = dict(at=dt.datetime.now().isoformat(timespec="seconds"), pairs=found, exports=[], bills=[])
    try:
        con.execute("BEGIN IMMEDIATE")
        for p in found:
            before["exports"] += [list(r) for r in con.execute("SELECT md5, superseded_by FROM purchase_export WHERE md5 IN (?,?)", (p["part"], p["full"]))]
            con.execute("UPDATE purchase_export SET superseded_by=NULL WHERE md5=?", (p["full"],))
            col = COL.get(p["type"])
            rehang = True
            if col:
                on_full = con.execute("SELECT COUNT(*) FROM purchase_bill WHERE %s=?" % col, (p["full"],)).fetchone()[0]
                on_part = con.execute("SELECT COUNT(*) FROM purchase_bill WHERE %s=?" % col, (p["part"],)).fetchone()[0]
                rehang = (on_full + on_part == p["full_rows"])
                if rehang:
                    before["bills"] += [[r[0], col, p["part"]] for r in con.execute("SELECT id FROM purchase_bill WHERE %s=?" % col, (p["part"],))]
                    con.execute("UPDATE purchase_bill SET %s=? WHERE %s=?" % (col, col), (p["full"], p["part"]))
                print("  %s: bills on the full list %d + on the part list %d %s its %d rows -> %s" % (
                    p["full"][:8], on_full, on_part, "=" if rehang else "!=", p["full_rows"],
                    "re-hung on the full list" if rehang else "the part list stays live beside it"))
            if rehang:
                con.execute("UPDATE purchase_export SET superseded_by=? WHERE md5=?", (p["full"], p["part"]))
        try:
            con.execute("DELETE FROM setting WHERE key='purchase.rematch_seen'")
        except sqlite3.Error:
            pass
        left = pairs(con)
        if left:
            raise RuntimeError("%d pair(s) still found after the repair" % len(left))
        path = os.path.join(os.path.dirname(os.path.abspath(db)), "s795_repair_before_%s.json" % dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
        json.dump(before, open(path, "w"), indent=1)
        con.commit()
    except Exception as e:                                     # noqa: BLE001
        con.rollback()
        print("S795 repair RED -- %s: %s -- rolled back, nothing changed" % (e.__class__.__name__, e))
        return 1
    print("S795 repair DONE -- %d pair(s) put right; effective bills now %d; before-state in %s" % (len(found), effective(con), path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
