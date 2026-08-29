#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""bank_match.py — the bank↔bill matcher, on the server, every morning.

THE OWNER'S RULING (29-Aug-2026, final)
    The bank statement is the sole source of truth for everything that
    settles -- UPI, card, all of it. The payment mode typed into Marg is a
    claim. So matching starts from the BANK: each settled transaction asks
    "which sale bill is this?", and the amount answers -- a transaction lands
    on a bill's total exactly or within a rupee.

WHAT IT WRITES, PER DAY
    upi_match rows      one per settled transaction and one per unmatched
                        non-cash bill:
                          agreed        bank txn ↔ bill already entered non-cash
                          cash          bank txn ↔ bill RUNG AS CASH -- the
                                        feedback list, and the drawer shortfall
                          bank_orphan   settled, no bill found (part payment,
                                        split, advance, other day)
                          bill_orphan   entered non-cash, nothing settled
    upi_match_day       one row: the day's verdict and totals.

WHERE THE BILLS COME FROM (no schema invented -- both stores exist today)
    * a day still PENDING in marg_push_staging: its parsed_json carries every
      bill (lines_csv -- bill_no, amount, mode)
    * a day already APPLIED: sale_item rows (source_ref = bill no, amount_p,
      mode), returns excluded

SCHEDULE (owner): first run 09:45 IST, then every 15 minutes until 12:00.
    Each run needs BOTH feeds -- the day's MPR (an upi_statement row) and the
    day's bills. Missing feed -> exit 3, naming it, and the next run retries.
    At noon (--final): a still-missing feed becomes a FEEDS_INCOMPLETE
    data_flag; a day with NEITHER feed is recorded as no_business (a Sunday
    looks exactly like this, and is not a fault).

    python3 bank_match.py                    # yesterday, the normal cron call
    python3 bank_match.py --date 2026-08-27  # one day, by hand
    python3 bank_match.py --final            # the noon closing attempt

Idempotent: a day's rows are replaced, never appended. Standard library only.
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import sqlite3
import sys

TOLERANCE_P = 100                 # one rupee -- rounding, never a real gap
UNIT = "medical"


def ensure_schema(con):
    con.execute(
        "CREATE TABLE IF NOT EXISTS upi_match ("
        " id INTEGER PRIMARY KEY,"
        " unit TEXT NOT NULL,"
        " business_date TEXT NOT NULL,"
        " status TEXT NOT NULL CHECK (status IN "
        "   ('agreed','cash','bank_orphan','bill_orphan')),"
        " rrn TEXT,"
        " txn_amount_p INTEGER,"
        " txn_mode TEXT,"
        " txn_time TEXT,"
        " bill_no TEXT,"
        " bill_amount_p INTEGER,"
        " bill_mode TEXT,"
        " off_by_p INTEGER,"
        " resolved TEXT,"                 # NULL = open · else who ticked it off
        " resolved_at TEXT,"
        " resolution TEXT,"
        " matched_at TEXT NOT NULL)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_upi_match_day "
                "ON upi_match(unit, business_date)")
    con.execute(
        "CREATE TABLE IF NOT EXISTS upi_match_day ("
        " unit TEXT NOT NULL,"
        " business_date TEXT NOT NULL,"
        " status TEXT NOT NULL CHECK (status IN "
        "   ('matched','waiting_bank','waiting_sales','no_business',"
        "    'feeds_incomplete')),"
        " bank_p INTEGER, bank_n INTEGER,"
        " entered_noncash_p INTEGER,"
        " n_agreed INTEGER, n_cash INTEGER,"
        " n_bank_orphan INTEGER, n_bill_orphan INTEGER,"
        " run_at TEXT NOT NULL,"
        " PRIMARY KEY (unit, business_date))")


# ------------------------------------------------------------------ feeds
def bank_rows(con, unit, iso):
    """The day's settled transactions, and whether the statement ARRIVED.
    Zero transactions with a statement present is a real (quiet) day; zero
    with no statement means the feed has not come yet -- different answers."""
    st = con.execute("SELECT 1 FROM upi_statement WHERE unit=? AND statement_date=?",
                     (unit, iso)).fetchone()
    rows = [dict(r) for r in con.execute(
        "SELECT amount_p, rrn, mode, txn_time FROM upi_txn "
        "WHERE unit=? AND txn_date=? ORDER BY amount_p DESC", (unit, iso))]
    return rows, st is not None


def bills_for(con, unit, iso):
    """The day's sale bills as (bill_no, amount_p, mode), returns excluded.

    Applied day first: sale_item is the durable store. Otherwise any staging
    row (pending OR applied-and-kept) whose payload covers the day.
    """
    rows = con.execute(
        "SELECT si.source_ref bill, si.amount_p, si.mode, si.service "
        "FROM sale_item si JOIN day_entry e ON e.id=si.day_entry_id "
        "WHERE e.unit=? AND e.business_date=? AND si.source_ref IS NOT NULL",
        (unit, iso)).fetchall()
    agg = {}
    for r in rows:
        if "return" in str(r["service"] or ""):
            continue
        b = str(r["bill"]).strip().upper()
        if not b or b.startswith("CN"):
            continue
        a = agg.setdefault(b, {"bill": b, "amount_p": 0, "mode": "cash"})
        a["amount_p"] += int(r["amount_p"] or 0)
        m = str(r["mode"] or "").lower()
        if m and m != "cash":
            a["mode"] = m
    if agg:
        return list(agg.values()), True

    # not applied yet -- read the staged payload
    for row in con.execute(
            "SELECT parsed_json FROM marg_push_staging WHERE unit=? "
            "AND parsed_json IS NOT NULL ORDER BY id DESC", (unit,)):
        try:
            payload = json.loads(row["parsed_json"] or "null") or {}
        except ValueError:
            continue
        for d in payload.get("days") or []:
            if d.get("business_date") != iso and d.get("date") != iso:
                continue
            out = {}
            rd = csv.DictReader(io.StringIO(d.get("lines_csv") or ""))
            for ln in rd:
                b = str(ln.get("bill_no") or "").strip().upper()
                amt = ln.get("amount")
                if not b or b.startswith("CN") or amt in (None, ""):
                    continue
                try:
                    p = int(round(float(amt) * 100))
                except ValueError:
                    continue
                if p < 0:
                    continue                       # a credit note, belt and braces
                a = out.setdefault(b, {"bill": b, "amount_p": 0, "mode": "cash"})
                a["amount_p"] += p
                m = str(ln.get("mode") or "").lower()
                if m and m != "cash":
                    a["mode"] = m
            if out:
                return list(out.values()), True
    return [], False


# --------------------------------------------------------------- matching
def match(bank, bills):
    """Bank first; exact before near; a bill is used once; nothing forced."""
    used, matched, orphans = set(), [], []
    for t in bank:
        best = None
        for i, b in enumerate(bills):
            if i in used or b["amount_p"] <= 0:
                continue
            d = abs(b["amount_p"] - t["amount_p"])
            if d > TOLERANCE_P:
                continue
            rank = (d, 0 if b["mode"] != "cash" else 1)
            if best is None or rank < best[0]:
                best = (rank, i, d)
        if best is None:
            orphans.append(t)
            continue
        _, i, d = best
        used.add(i)
        b = bills[i]
        matched.append((t, b, d, "agreed" if b["mode"] != "cash" else "cash"))
    bill_orphans = [b for i, b in enumerate(bills)
                    if i not in used and b["mode"] != "cash"]
    return matched, orphans, bill_orphans


def run_day(con, unit, iso, final=False, now=None):
    """Returns (exit_code, one_line_summary)."""
    ensure_schema(con)
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()
    bank, bank_in = bank_rows(con, unit, iso)
    bills, sales_in = bills_for(con, unit, iso)

    def day_row(status, **kw):
        con.execute(
            "INSERT INTO upi_match_day (unit, business_date, status, bank_p, "
            " bank_n, entered_noncash_p, n_agreed, n_cash, n_bank_orphan, "
            " n_bill_orphan, run_at) VALUES (?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(unit, business_date) DO UPDATE SET status=excluded.status, "
            " bank_p=excluded.bank_p, bank_n=excluded.bank_n, "
            " entered_noncash_p=excluded.entered_noncash_p, "
            " n_agreed=excluded.n_agreed, n_cash=excluded.n_cash, "
            " n_bank_orphan=excluded.n_bank_orphan, "
            " n_bill_orphan=excluded.n_bill_orphan, run_at=excluded.run_at",
            (unit, iso, status, kw.get("bank_p"), kw.get("bank_n"),
             kw.get("noncash_p"), kw.get("agreed"), kw.get("cash"),
             kw.get("borph"), kw.get("iorph"), now))
        con.commit()

    if not bank_in and not sales_in:
        if final:
            day_row("no_business")
            return 0, "%s: neither feed -- recorded as no business (a Sunday " \
                      "looks exactly like this)" % iso
        return 3, "%s: waiting -- neither the bank statement nor the sale " \
                  "report has arrived yet" % iso
    if not bank_in or not sales_in:
        missing = "the bank statement (MPR)" if not bank_in else \
                  "the Marg sale report"
        if final:
            day_row("feeds_incomplete")
            con.execute(
                "INSERT INTO data_flag (unit, business_date, code, severity, detail) "
                "VALUES (?,?, 'BANKMATCH_FEED_MISSING', 'high', ?)",
                (unit, iso, "noon passed and %s never arrived; the day is "
                            "unmatched" % missing))
            con.commit()
            return 1, "%s: FEEDS INCOMPLETE -- %s never arrived" % (iso, missing)
        return 3, "%s: waiting for %s" % (iso, missing)

    matched, orphans, bill_orphans = match(bank, bills)
    con.execute("DELETE FROM upi_match WHERE unit=? AND business_date=?",
                (unit, iso))
    for t, b, d, status in matched:
        con.execute(
            "INSERT INTO upi_match (unit, business_date, status, rrn, "
            " txn_amount_p, txn_mode, txn_time, bill_no, bill_amount_p, "
            " bill_mode, off_by_p, matched_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (unit, iso, status, t.get("rrn"), t["amount_p"], t.get("mode"),
             t.get("txn_time"), b["bill"], b["amount_p"], b["mode"], d, now))
    for t in orphans:
        con.execute(
            "INSERT INTO upi_match (unit, business_date, status, rrn, "
            " txn_amount_p, txn_mode, txn_time, matched_at) "
            "VALUES (?,?, 'bank_orphan', ?,?,?,?,?)",
            (unit, iso, t.get("rrn"), t["amount_p"], t.get("mode"),
             t.get("txn_time"), now))
    for b in bill_orphans:
        con.execute(
            "INSERT INTO upi_match (unit, business_date, status, bill_no, "
            " bill_amount_p, bill_mode, matched_at) "
            "VALUES (?,?, 'bill_orphan', ?,?,?,?)",
            (unit, iso, b["bill"], b["amount_p"], b["mode"], now))
    n = dict(agreed=sum(1 for *_x, st in matched if st == "agreed"),
             cash=sum(1 for *_x, st in matched if st == "cash"),
             borph=len(orphans), iorph=len(bill_orphans))
    day_row("matched", bank_p=sum(t["amount_p"] for t in bank), bank_n=len(bank),
            noncash_p=sum(b["amount_p"] for b in bills if b["mode"] != "cash"),
            **n)
    return 0, ("%s: matched. bank %d txn(s); agreed %d · RUNG AS CASH %d · "
               "bank orphan %d · bill orphan %d"
               % (iso, len(bank), n["agreed"], n["cash"], n["borph"], n["iorph"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", default=None, help="ISO yyyy-mm-dd; default yesterday")
    ap.add_argument("--db", default=os.environ.get("FINANCE_DB", "finance.db"))
    ap.add_argument("--unit", default=UNIT)
    ap.add_argument("--final", action="store_true",
                    help="the noon attempt: close the day even if a feed is missing")
    a = ap.parse_args(argv)
    iso = a.date or (dt.date.today() - dt.timedelta(days=1)).isoformat()
    if not os.path.exists(a.db):
        print("no database at %s" % a.db)
        return 1
    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row
    try:
        code, msg = run_day(con, a.unit, iso, final=a.final)
    finally:
        con.close()
    print(msg)
    return code


if __name__ == "__main__":
    sys.exit(main())
