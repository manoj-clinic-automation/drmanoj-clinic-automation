#!/usr/bin/env python3
# =====================================================================
#  S193_DISC — historical discount backfill (two-pass).
#
#  Fills sale_item.gross_p / sale_item.disc_p for bills already in the
#  books, from historical_discount_data.py (parsed from Dr Manoj's own
#  Marg "Bill wise sales" exports, 2026-04-01 .. 2026-08-15). NON-PHI:
#  (bill_date, bill_no, gross_p, disc_p, net_p) only.
#
#  Two matching passes, per business_date, unit='medical':
#    PASS 1 — exact:  sale_item.source_ref == bill_no
#             (the Marg-push days, where the real bill number is stored).
#    PASS 2 — by net amount:  the older days were backfilled (S186/F-104)
#             with SYNTHETIC refs (e.g. 'S186-F104-576'), so the bill
#             number isn't stored. But the rows carry the SAME net, in the
#             SAME bill order. Pass 2 matches each remaining parsed bill to
#             an UNCLAIMED stored row of the SAME net_p on that day, taking
#             them in order (stored by source_ref, parsed by bill_no). Only
#             ever matches equal net; unequal never touches.
#
#  SAFETY:
#   * NEVER touches amount_p (booked net) or any column except gross_p/disc_p.
#   * Stores MAGNITUDES (abs).  Idempotent (re-run writes the same values).
#   * A stored row is claimed at most once (no double-assignment).
#   * --dry (default) writes nothing and reports the breakdown.
#     --apply performs the UPDATEs inside one transaction.
# =====================================================================
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import historical_discount_data as _hdd

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
UNIT = "medical"


def _refkey(ref):
    # natural sort: trailing number if present, else the string
    m = re.search(r"(\d+)\s*$", ref or "")
    return (int(m.group(1)) if m else 10 ** 12, ref or "")


def load_rows():
    by_day = {}
    for bill_date, bill_no, gross_p, disc_p, net_p in _hdd.ROWS:
        by_day.setdefault(bill_date.strip(), []).append({
            "bill_no": bill_no.strip(),
            "gross_p": abs(int(gross_p)),
            "disc_p": abs(int(disc_p)),
            "net_p": abs(int(net_p)),
        })
    return by_day


def main():
    apply = "--apply" in sys.argv
    by_day = load_rows()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    cols = {c["name"] for c in con.execute("PRAGMA table_info(sale_item)")}
    if "gross_p" not in cols or "disc_p" not in cols:
        print("*** sale_item is missing gross_p/disc_p — run the migration first. STOP.")
        sys.exit(2)

    n_ref = n_amt = n_unmatched = n_already = 0
    days_touched = set()
    unmatched_ex = []

    con.execute("BEGIN")
    for day, bills in by_day.items():
        stored = con.execute(
            "SELECT s.id, s.source_ref, s.amount_p, s.gross_p, s.disc_p "
            "FROM sale_item s JOIN day_entry de ON de.id = s.day_entry_id "
            "WHERE de.unit=? AND de.business_date=?", (UNIT, day)).fetchall()
        if not stored:
            n_unmatched += len(bills)
            if len(unmatched_ex) < 8:
                unmatched_ex.append((day, "no rows in books"))
            continue

        claimed = set()
        by_ref = {}
        for r in stored:
            by_ref.setdefault(r["source_ref"], r)

        def do_set(row, bill):
            nonlocal n_already
            gp, dp = bill["gross_p"], bill["disc_p"]
            if row["gross_p"] == gp and row["disc_p"] == dp:
                n_already += 1
            elif apply:
                con.execute("UPDATE sale_item SET gross_p=?, disc_p=? WHERE id=?",
                            (gp, dp, row["id"]))
            days_touched.add(day)

        # ---- PASS 1: exact bill_no == source_ref ----
        leftover_bills = []
        for b in bills:
            r = by_ref.get(b["bill_no"])
            if r is not None and r["id"] not in claimed:
                claimed.add(r["id"]); n_ref += 1; do_set(r, b)
            else:
                leftover_bills.append(b)

        # ---- PASS 2: by net amount, in order, among UNCLAIMED rows ----
        pool = {}
        for r in sorted((r for r in stored if r["id"] not in claimed), key=lambda r: _refkey(r["source_ref"])):
            pool.setdefault(r["amount_p"], []).append(r)
        for b in sorted(leftover_bills, key=lambda b: b["bill_no"]):
            lst = pool.get(b["net_p"])
            if lst:
                r = lst.pop(0); claimed.add(r["id"]); n_amt += 1; do_set(r, b)
            else:
                n_unmatched += 1
                if len(unmatched_ex) < 8:
                    unmatched_ex.append((day, b["bill_no"], "net ₹%.2f" % (b["net_p"] / 100)))

    if apply:
        con.commit()
    else:
        con.rollback()

    total = sum(len(v) for v in by_day.values())
    print("=== historical discount backfill (%s) ===" % ("APPLY" if apply else "DRY-RUN"))
    print("  parsed bills        : %d  across %d days" % (total, len(by_day)))
    print("  matched by bill_no  : %d" % n_ref)
    print("  matched by amount   : %d  (older backfilled days, synthetic refs)" % n_amt)
    print("  TOTAL matched       : %d" % (n_ref + n_amt))
    print("  already correct     : %d  (of the matched, needing no change)" % n_already)
    print("  unmatched           : %d  (genuinely not in the books — real gaps)" % n_unmatched)
    if unmatched_ex:
        print("  e.g. unmatched      :", unmatched_ex)
    print("  days that get values: %d" % len(days_touched))
    if not apply:
        print("  (dry-run — nothing written. Re-run with --apply to write.)")
    con.close()


if __name__ == "__main__":
    main()
