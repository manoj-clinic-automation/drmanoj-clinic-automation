#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""day_resync.py -- S355_DAY_TRUTH: an autofiled pharmacy day follows the bank.

THE FAULT (S275, 20-Sep-2026, read from the 01:35 nightly database)
    The D354 autofile builds a pharmacy day the moment Marg's sale report
    arrives: net sale from the report, UPI from the bank AS KNOWN AT THAT
    MOMENT, cash = net - UPI.  The bank's statement usually lands hours
    later, so the day is frozen with UPI 0 and cash overstated; the
    statement then opens a 'upi_vs_statement' exception that nobody can
    close, and the approval section shows a cash figure that is not true.
    Nine of the sixteen September days were filed this way.

WHAT THIS DOES
    For every pharmacy day_entry that is (a) not yet approved, (b) written
    by the autofile and never corrected by a person, and (c) has a bank
    statement: set the UPI line to the bank's settled total, the cash line
    to net - UPI, write one audit_log row (before / after), and re-run
    finance_upi.reconcile_upi so the exception closes itself.  A day whose
    bank total exceeds its net sale is left alone and named (it needs a
    person).  Idempotent: a day already equal to the bank is untouched.

WHAT IT NEVER DOES
    Touch an approved or locked day.  Touch a day a person has corrected
    (audit action 'correct' on the entry).  Touch expenses, movements,
    noncash bills, Marg, sale_item.  Change any parent file.

RUN
    /root/wa/venv/bin/python3 -B /root/finance/day_resync.py            # apply
    /root/wa/venv/bin/python3 -B /root/finance/day_resync.py --dry-run  # say only
    --db PATH   another database (the walk)     --since YYYY-MM-DD (default 2026-09-01)
    Honours /root/finance/_off/ALL_OFF (sanjeevni_switch.sh).  Cron: every
    30 minutes 07-23 under flock.
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys

KIT = "S355_DAY_TRUTH"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
DB_DEFAULT = os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db"))
OFF_DIR = os.environ.get("SANJEEVNI_OFF_DIR", os.path.join(HERE, "_off"))
UNIT = "medical"
WHO = "day_resync"


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def rupees(p):
    return "%d.%02d" % (p // 100, p % 100) if p >= 0 else "-" + rupees(-p)


def switched_off():
    return os.path.exists(os.path.join(OFF_DIR, "ALL_OFF")) or \
        os.path.exists(os.path.join(OFF_DIR, "ALL_OFF.txt"))


def open_db(path):
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 30000")
    con.execute("PRAGMA foreign_keys = ON")
    return con


def candidates(con, since):
    """Unapproved, autofiled, never corrected by a person, statement in."""
    rows = con.execute(
        "SELECT e.id, e.business_date, e.status, e.source "
        "FROM day_entry e WHERE e.unit=? AND e.status IN ('submitted','draft') "
        "AND e.source='app' AND e.business_date>=? "
        "AND EXISTS (SELECT 1 FROM audit_log a WHERE a.table_name='day_entry' "
        "            AND a.row_id=e.id AND a.action='autofile') "
        "AND NOT EXISTS (SELECT 1 FROM audit_log a WHERE a.table_name='day_entry' "
        "            AND a.row_id=e.id AND a.action='correct') "
        "ORDER BY e.business_date", (UNIT, since)).fetchall()
    return rows


def day_lines(con, eid):
    cash = con.execute("SELECT id, amount_p FROM day_line WHERE day_entry_id=? "
                       "AND service='pharmacy_sale' AND mode='cash'", (eid,)).fetchall()
    upi = con.execute("SELECT id, amount_p FROM day_line WHERE day_entry_id=? "
                      "AND service='pharmacy_sale' AND mode='upi'", (eid,)).fetchall()
    return cash, upi


def bank_total(con, iso):
    st = con.execute("SELECT parsed_total_p, txn_count FROM upi_statement "
                     "WHERE unit=? AND statement_date=?", (UNIT, iso)).fetchone()
    if st is None:
        return None, 0
    return int(st["parsed_total_p"] or 0), int(st["txn_count"] or 0)


def resync_day(con, e, apply, reconcile):
    """Returns (verdict, line). Verdicts: SAME · FIXED · WOULD_FIX · NO_BANK ·
    OVER_NET · SHAPE."""
    eid, iso = e["id"], e["business_date"]
    bank_p, n_txn = bank_total(con, iso)
    if bank_p is None:
        return "NO_BANK", "%s  no bank statement yet" % iso
    cash, upi = day_lines(con, eid)
    if len(cash) != 1 or len(upi) > 1:
        return "SHAPE", "%s  unexpected line shape (cash %d, upi %d) -- left alone" % (
            iso, len(cash), len(upi))
    cash_p = int(cash[0]["amount_p"] or 0)
    upi_p = int(upi[0]["amount_p"] or 0) if upi else 0
    net_p = cash_p + upi_p
    if bank_p == upi_p:
        return "SAME", "%s  UPI %s already the bank's" % (iso, rupees(upi_p))
    if bank_p > net_p:
        return "OVER_NET", "%s  bank UPI %s exceeds the net sale %s -- needs a person" % (
            iso, rupees(bank_p), rupees(net_p))
    new_cash = net_p - bank_p
    line = "%s  UPI %s -> %s (%d txns) · cash %s -> %s · net %s" % (
        iso, rupees(upi_p), rupees(bank_p), n_txn, rupees(cash_p), rupees(new_cash), rupees(net_p))
    if not apply:
        return "WOULD_FIX", line
    before = dict(date=iso, cash_p=cash_p, upi_p=upi_p, net_p=net_p)
    after = dict(date=iso, cash_p=new_cash, upi_p=bank_p, net_p=net_p,
                 bank_txns=n_txn, rule="D354 marg+bank, re-read from the statement", kit=KIT)
    con.execute("UPDATE day_line SET amount_p=? WHERE id=?", (new_cash, cash[0]["id"]))
    if upi:
        con.execute("UPDATE day_line SET amount_p=? WHERE id=?", (bank_p, upi[0]["id"]))
    else:
        con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) "
                    "VALUES (?,'pharmacy_sale','upi',?)", (eid, bank_p))
    con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, "
                "by_whom, at) VALUES ('day_entry', ?, 'resync_upi', ?, ?, ?, ?)",
                (eid, json.dumps(before), json.dumps(after), WHO, now_iso()))
    con.commit()
    if reconcile is not None:
        r = reconcile(con, UNIT, iso, now=now_iso())
        if r is not None:
            line += " · exception %s" % ("closed" if r.get("match") else "still open")
    return "FIXED", line


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--since", default="2026-09-01")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-reconcile", action="store_true", help="walk only")
    a = ap.parse_args(argv)
    if switched_off():
        print("%s: Sanjeevni jobs are OFF (%s) -- nothing done" % (KIT, OFF_DIR))
        return 0
    if not os.path.exists(a.db):
        print("%s: no database at %s" % (KIT, a.db))
        return 2
    reconcile = None
    if not a.no_reconcile:
        try:
            import finance_upi  # noqa: PLC0415
            reconcile = finance_upi.reconcile_upi
        except Exception as ex:  # noqa: BLE001
            print("%s: finance_upi not importable (%s) -- lines fixed, exception left to the next bank load" % (KIT, ex))
    con = open_db(a.db)
    rows = candidates(con, a.since)
    counts = {}
    print("%s %s -- %d unapproved autofiled day(s) since %s in %s" % (
        KIT, "DRY RUN" if a.dry_run else "APPLY", len(rows), a.since, a.db))
    for e in rows:
        v, line = resync_day(con, e, apply=not a.dry_run, reconcile=reconcile)
        counts[v] = counts.get(v, 0) + 1
        print("  %-9s %s" % (v, line))
    print("summary: " + " · ".join("%s %d" % (k, counts[k]) for k in sorted(counts)) if counts else "summary: nothing to do")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
