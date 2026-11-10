#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  purchase_unspill.py  ·  v1.1  ·  kit S775_UNSPILL_TAILS (v1.0 S773_UNSPILL_BILLS)  ·  Session 423 (Sanjeevni)  ·  10-Nov-2026  ·  F-1233
#
#  THE FAULT: Marg's SUPPLIER/ITEM WISE purchase report prints the bill number in a column eight characters wide. A longer
#  number spills: the bill column is left empty and the number's last eight characters are fused onto the item name --
#      Yuvika YS0706202627  ->  bill ''  item '06202627CAST SHOE M TYNOR'
#      Kedar   A000207_     ->  bill ''  item 'A000207_TYRO BR'
#  marg_purchase.read_purchase splits only the shape letters + 5-7 digits ('EP001498VITANSIAL PLUS') and keeps every other
#  row whole with no bill. Such lines never joined their bill: the Items check counted the bill as having no lines, the
#  scan-beside-Marg checks could not compare it, and the item name carried the number.
#
#  THE REPAIR -- by evidence, never by guess (the reader's own rule, marg_purchase TRAP 3): a line with NO bill number is split
#  only when its item text begins with a REAL bill number of the SAME supplier (purchase_bill, from the bill-wise report) --
#  the whole number or its last eight characters, at least six long -- the bill dated inside the export's own period when the
#  export is known, ONE bill only, and the character after the number not a digit (a number never cut in the middle). The line
#  gets the bill's number, date and month and the item without the number. Only a LIVE bill (its bill-wise or supplier-wise export
#  not superseded -- purchase_app's EFF_BILL) in a month not made FINAL. Anything else stays exactly as it came.
#  It runs inside every purchase push (purchase_app.api_push, before the lines are re-dated; a bill-wise push repairs the item
#  lines that arrived before their bill) and once at install over the stored lines. Every change is logged
#  (purchase_unspill_log: the old values) so undo() puts each line back.
#
#  v1.1 (S775, the owner 13:02 IST: "why are there still two bills with no lines?") -- THE OLD READER'S WRONG SPLIT. For a number
#  like GUNINA's GPPL2678591 the spill 'L2678591LEFUMED 20MG TAB' matched the reader's letters+digits shape, so the line was stored
#  with bill number 'L2678591' -- only the column's last 8 characters, a number no bill carries. Such a line is given the full
#  number (and the bill's date) when its number is EXACTLY the last 8 characters of ONE live bill of the same supplier, no bill of
#  that supplier carries the short number itself, the bill is dated in the export's period, and neither month is FINAL. The item
#  is left as it is. Logged and undone like the rest; undo(since=...) puts back only what was joined from a given time.
# =============================================================================
import datetime as dt

VERSION = "1.1"
KIT = "S775_UNSPILL_TAILS"
DDL = ("CREATE TABLE IF NOT EXISTS purchase_unspill_log (line_id INTEGER PRIMARY KEY, old_item TEXT NOT NULL, old_bill_no TEXT,"
       " old_bill_date TEXT, old_month TEXT, new_item TEXT NOT NULL, bill_id INTEGER NOT NULL, at TEXT NOT NULL, by_who TEXT)")
TAIL = 8                                                       # the width of Marg's bill column
MIN_LEN = 6


def _forms(bill_no):
    b = str(bill_no or "").strip().upper()
    out = set()
    if len(b) >= MIN_LEN:
        out.add(b)
        if len(b) > TAIL:
            out.add(b[-TAIL:])
    return out


def _periods(con, md5s):
    out = {}
    if not md5s:
        return out
    try:
        for md5, pf, pt in con.execute("SELECT md5, period_from, period_to FROM purchase_export WHERE md5 IN (%s)" % ",".join("?" * len(md5s)),
                                       list(md5s)):
            out[md5] = (pf, pt)
    except Exception:                                          # noqa: BLE001 -- no export table: the period is not used
        return {}
    return out


def plan(con):
    """[(line_id, bill_id, bill_no, bill_date, new_item, old_item)] -- the lines a repair would change; nothing written.
    v1.1: the spilled lines (no bill number) first, then the wrongly split ones (plan_tails)."""
    return _plan_spilled(con) + plan_tails(con)


def _final_months(con):
    try:
        return {r[0] for r in con.execute("SELECT month FROM purchase_month WHERE status='final'")}
    except Exception:                                          # noqa: BLE001 -- no month book: nothing is final
        return set()


def _live_sql(con):
    try:
        con.execute("SELECT md5, superseded_by FROM purchase_export LIMIT 1")
        if {"bw_md5", "sw_md5"} <= {c[1] for c in con.execute("PRAGMA table_info(purchase_bill)")}:
            return " AND EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND (e.md5=b.bw_md5 OR e.md5=b.sw_md5))"
    except Exception:                                          # noqa: BLE001
        pass
    return ""


def plan_tails(con):
    """v1.1: [(line_id, bill_id, bill_no, bill_date, item, item)] -- lines whose bill number is EXACTLY the last 8 characters of ONE
    live bill of the same supplier and no bill of that supplier carries the short number; nothing written."""
    final = _final_months(con)
    live = _live_sql(con)
    rows = con.execute("SELECT l.id, l.supplier_norm, l.bill_no, l.item, l.source_md5, l.month FROM purchase_line l WHERE l.bill_no IS NOT NULL "
                       "AND length(l.bill_no)=? AND l.supplier_norm IS NOT NULL AND NOT EXISTS (SELECT 1 FROM purchase_bill x WHERE "
                       "x.supplier_norm=l.supplier_norm AND x.bill_no=l.bill_no) ORDER BY l.id", (TAIL,)).fetchall()
    if not rows:
        return []
    per = _periods(con, {r[4] for r in rows})
    out = []
    for lid, sn, bno, item, md5, lmonth in rows:
        if lmonth and lmonth in final:
            continue
        pf, pt = per.get(md5, (None, None))
        hits = [x for x in con.execute("SELECT b.id, b.bill_no, b.bill_date FROM purchase_bill b WHERE b.supplier_norm=? AND length(b.bill_no)>?" + live,
                                       (sn, TAIL)).fetchall()
                if str(x[1]).upper()[-TAIL:] == str(bno).upper() and str(x[2] or "")[:7] not in final
                and not (pf and pt and x[2] and not (pf <= x[2] <= pt))]
        if len(hits) == 1:
            bid, full, bd = hits[0]
            out.append((lid, bid, full, bd, item, item))
    return out


def _plan_spilled(con):
    rows = con.execute("SELECT id, supplier_norm, item, source_md5, month FROM purchase_line WHERE bill_no IS NULL AND supplier_norm IS NOT NULL "
                       "AND item IS NOT NULL ORDER BY id").fetchall()
    if not rows:
        return []
    per = _periods(con, {r[3] for r in rows})
    final = set()
    try:
        final = {r[0] for r in con.execute("SELECT month FROM purchase_month WHERE status='final'")}
    except Exception:                                          # noqa: BLE001 -- no month book: nothing is final
        final = set()
    live = ""
    try:
        con.execute("SELECT md5, superseded_by FROM purchase_export LIMIT 1")
        live = (" AND EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND (e.md5=b.bw_md5 OR e.md5=b.sw_md5))"
                if {"bw_md5", "sw_md5"} <= {c[1] for c in con.execute("PRAGMA table_info(purchase_bill)")} else "")
    except Exception:                                          # noqa: BLE001
        live = ""
    bills = {}
    for sn in {r[1] for r in rows}:
        bills[sn] = [x for x in con.execute("SELECT b.id, b.bill_no, b.bill_date FROM purchase_bill b WHERE b.supplier_norm=?" + live, (sn,)).fetchall()
                     if str(x[2] or "")[:7] not in final]       # a live bill (purchase_app's EFF_BILL), never in a month made FINAL
    out = []
    for lid, sn, item, md5, lmonth in rows:
        if lmonth and lmonth in final:                         # a line already counted in a FINAL month stays where it is
            continue
        up = str(item).upper()
        pf, pt = per.get(md5, (None, None))
        hits = []
        for bid, bno, bd in bills.get(sn, []):
            if pf and pt and bd and not (pf <= bd <= pt):
                continue
            best = max((f for f in _forms(bno) if up.startswith(f)), key=len, default=None)
            if not best:
                continue
            rest = str(item)[len(best):]
            if not rest or rest[0].isdigit():
                continue
            name = rest.lstrip("_ ").strip()
            if name:
                hits.append((bid, bno, bd, name, len(best)))
        if len({h[0] for h in hits}) == 1:
            bid, bno, bd, name, _n = hits[0]
            out.append((lid, bid, bno, bd, name, item))
    return out


def unspill(con, by="push"):
    """Repair every line plan() names, inside a savepoint (all or none); returns how many. The caller commits."""
    con.execute(DDL)
    if not con.in_transaction:                                 # standalone: take the write lock before reading (never 'busy' mid-way)
        con.execute("BEGIN IMMEDIATE")
    todo = plan(con)
    if not todo:
        return 0
    ts = dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute("SAVEPOINT s773")
    try:
        n = 0
        for lid, bid, bno, bd, name, old in todo:
            prev = con.execute("SELECT item, bill_no, bill_date, month FROM purchase_line WHERE id=? AND item=? AND (bill_no IS NULL OR bill_no<>?)",
                               (lid, old, bno)).fetchone()
            if not prev:
                continue
            con.execute("INSERT OR REPLACE INTO purchase_unspill_log (line_id, old_item, old_bill_no, old_bill_date, old_month, new_item, bill_id, at, by_who) "
                        "VALUES (?,?,?,?,?,?,?,?,?)", (lid, prev[0], prev[1], prev[2], prev[3], name, bid, ts, by))
            n += con.execute("UPDATE purchase_line SET bill_no=?, bill_date=?, month=?, item=? WHERE id=? AND item=?",
                             (bno, bd, (bd or "")[:7] or None, name, lid, old)).rowcount or 0
        con.execute("RELEASE s773")
        return n
    except Exception:
        try:                                                   # the savepoint may be gone with the whole transaction (disk full)
            con.execute("ROLLBACK TO s773")
            con.execute("RELEASE s773")
        except Exception:                                      # noqa: BLE001 -- the first error is the one raised
            pass
        raise


UNDO_SKIPPED = {"n": 0}


def undo(con, since=None):
    """Every logged line back to what it was -- only a line still exactly as the repair left it (same id, the repaired item, a bill);
    the log emptied. Returns how many; UNDO_SKIPPED['n'] counts the lines changed since and left alone. Commits."""
    con.execute(DDL)
    n = sk = 0
    where, args = (" WHERE at >= ?", (since,)) if since else ("", ())
    for lid, it, bno, bd, mo, new in con.execute("SELECT line_id, old_item, old_bill_no, old_bill_date, old_month, new_item FROM purchase_unspill_log"
                                                 + where, args).fetchall():
        k = con.execute("UPDATE purchase_line SET item=?, bill_no=?, bill_date=?, month=? WHERE id=? AND item=? AND bill_no IS NOT NULL",
                        (it, bno, bd, mo, lid, new)).rowcount or 0
        n += k
        sk += 0 if k else 1
    con.execute("DELETE FROM purchase_unspill_log" + where, args)
    con.commit()
    UNDO_SKIPPED["n"] = sk
    return n


if __name__ == "__main__":                                     # python3 purchase_unspill.py DB [--apply | --undo]
    import sqlite3
    import sys
    c = sqlite3.connect(sys.argv[1], timeout=30)
    if "--undo" in sys.argv:
        k = undo(c, since=sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else None)
        print("UNSPILL UNDO: %d line(s) put back; %d changed since, left alone" % (k, UNDO_SKIPPED["n"]))
    elif "--apply" in sys.argv:
        k = unspill(c, by=KIT)
        c.commit()
        print("UNSPILL APPLIED: %d line(s) joined to their bill" % k)
    else:
        p = plan(c)
        for lid, bid, bno, bd, name, old in p:
            print("  line %d: %r -> bill %s (%s) item %r" % (lid, old, bno, bd, name))
        print("UNSPILL PLAN: %d line(s)" % len(p))
