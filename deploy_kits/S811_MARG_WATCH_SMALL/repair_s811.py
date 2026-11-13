#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repair_s811.py --db finance.db [--apply] -- kit S811, F-1280 (the owner 06:42 IST 13-Nov: "the latest export should settle it").

On 05-Oct three purchase lists of 1 Sep - 3 Oct reached the server: an item list of 5 rows, one of 208 rows and a bill-item list of 0 rows.
All three are still LIVE. September has had its complete item list since 20-Oct (15b9d64a, 1-30 Sep) and October its month-end lists of
11-Nov, so the three only overlap. This marks them as replaced by the September list -- kept in the table, read by nothing.

PROVED FIRST, inside the same transaction, or nothing is written:
  1 every line of the three is carried by a later live list (the same supplier, bill, quantity and money; an orthotic renamed in Marg since
    counts under its new name);
  2 each bill's line set for September and October -- the set the purchase pages read (purchase_app._line_sets: per bill the live export
    with the latest stamp) -- is the same export and the same money after as before;
  3 the effective bills of September and October are the same count and the same money (the three carry no bill).
The before-state is written beside the database. Without --apply: the proof only, nothing written."""
import argparse, datetime, json, os, sqlite3, sys

OLD = ("15b48bc5a25d04f1635db6b29ad04c6d", "957b473f59d911ea4d10eea91ae4c71f", "de92f5d5185646d4de563e30d5464f6e")
TO = "15b9d64a15d554afcdef5104ae67043f"
MONTHS = ("2026-09", "2026-10")
EFF_BILL = ("EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND (e.md5=b.bw_md5 OR e.md5=b.sw_md5))")   # purchase_app.EFF_BILL


def line_sets(con, month):
    """purchase_app._line_sets, the same query and the same choice: per (supplier, bill) the live export with the latest stamp."""
    sets = {}
    for r in con.execute(
            "SELECT l.supplier_norm, l.bill_no, l.bill_date, l.line_type, l.source_md5, e.export_stamp, "
            "COALESCE(SUM(COALESCE(l.net_amount_p, l.amount_p)),0), COALESCE(SUM(l.amount_p),0), COUNT(*) FROM purchase_line l JOIN purchase_export e "
            "ON e.md5=l.source_md5 WHERE l.month=? AND e.superseded_by IS NULL "
            "GROUP BY l.supplier_norm, l.bill_no, l.bill_date, l.line_type, l.source_md5, e.export_stamp", (month,)):
        k = (r[0], r[1])
        cand = (r[5], r[4], r[6], r[7], r[8])
        if k not in sets or (cand[0], cand[1]) > (sets[k][0], sets[k][1]):
            sets[k] = cand
    return {"%s|%s" % k: v for k, v in sets.items()}


def bills(con, month):
    r = con.execute("SELECT COUNT(*), COALESCE(SUM(amount_p),0) FROM purchase_bill b WHERE b.month=? AND " + EFF_BILL, (month,)).fetchone()
    return [int(r[0]), int(r[1])]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    con = sqlite3.connect(a.db, timeout=30)
    con.isolation_level = None
    rows = {r[0]: r for r in con.execute("SELECT md5, type, period_from, period_to, export_stamp, n_rows, superseded_by FROM purchase_export "
                                         "WHERE md5 IN (?,?,?,?)", OLD + (TO,))}
    if TO not in rows or rows[TO][6] is not None:
        print("STOP: September's complete item list (%s) is not on the server or is not live -- nothing written" % TO[:8]); return 2
    if any(m not in rows for m in OLD):
        print("STOP: one of the three 05-Oct lists is not on the server -- nothing written"); return 2
    if all(rows[m][6] is not None for m in OLD):
        print("ALREADY: the three 05-Oct lists are already marked as replaced -- nothing to do"); return 0
    live = [m for m in OLD if rows[m][6] is None]
    # proof 1 -- every line of the three is in a later live list
    lone = []
    for r in con.execute("SELECT supplier_norm, bill_no, item, qty, COALESCE(net_amount_p, amount_p), COALESCE(direction,'PURCHASE') FROM purchase_line "
                         "WHERE source_md5 IN (?,?,?)", OLD):
        tw = con.execute("SELECT COUNT(*) FROM purchase_line l JOIN purchase_export e ON e.md5=l.source_md5 WHERE e.superseded_by IS NULL "
                         "AND l.source_md5 NOT IN (?,?,?) AND e.export_stamp>'20261005-075955' AND l.supplier_norm IS ? AND l.bill_no=? AND l.qty IS ? "
                         "AND COALESCE(l.net_amount_p, l.amount_p)=? AND COALESCE(l.direction,'PURCHASE')=?", OLD + (r[0], r[1], r[3], r[4], r[5])).fetchone()[0]
        if not tw:
            lone.append(r)
    n_lines = con.execute("SELECT COUNT(*) FROM purchase_line WHERE source_md5 IN (?,?,?)", OLD).fetchone()[0]
    if lone:
        for r in lone[:6]:
            print("  not in any later list: %s bill %s %s" % (r[0], r[1], r[2]))
        print("STOP: %d line(s) of the three are in no later list -- nothing written" % len(lone)); return 2
    print("  proof 1: all %d lines of the three are in a later live list" % n_lines)
    before = {m: (line_sets(con, m), bills(con, m)) for m in MONTHS}
    con.execute("BEGIN IMMEDIATE")
    try:
        con.executemany("UPDATE purchase_export SET superseded_by=? WHERE md5=? AND superseded_by IS NULL", [(TO, m) for m in live])
        after = {m: (line_sets(con, m), bills(con, m)) for m in MONTHS}
        bad = [m for m in MONTHS if before[m] != after[m]]
        if bad:
            for m in bad:
                ks = sorted(set(before[m][0]) ^ set(after[m][0]) | {k for k in before[m][0] if before[m][0].get(k) != after[m][0].get(k)})
                print("  %s differs: %s ... bills %s -> %s" % (m, ks[:4], before[m][1], after[m][1]))
            con.execute("ROLLBACK")
            print("STOP: a month's line sets or bills would change -- nothing written"); return 2
        print("  proof 2: September %d and October %d bills' line sets the same export and money after as before" % (len(after["2026-09"][0]), len(after["2026-10"][0])))
        print("  proof 3: effective bills the same -- September %d (Rs %s), October %d (Rs %s)" % (after["2026-09"][1][0], after["2026-09"][1][1] // 100,
                                                                                                   after["2026-10"][1][0], after["2026-10"][1][1] // 100))
        if not a.apply:
            con.execute("ROLLBACK")
            print("DRY: proved; nothing written (%d list(s) would be marked as replaced)" % len(live)); return 0
        snap = os.path.join(os.path.dirname(os.path.abspath(a.db)), "s811_repair_before_%s.json" % datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%Y%m%d_%H%M%S"))
        with open(snap, "w") as fh:
            json.dump(dict(kit="S811", marked=live, superseded_by=TO, before={m: rows[m][6] for m in OLD}), fh, indent=1)
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    print("DONE: %d of the three 05-Oct lists of 1 Sep - 3 Oct marked as replaced by the September list (%s); before-state %s"
          % (len(live), TO[:8], os.path.basename(snap)))
    print("undo: UPDATE purchase_export SET superseded_by=NULL WHERE md5 IN ('%s')" % "','".join(live))
    return 0


if __name__ == "__main__":
    sys.exit(main())
