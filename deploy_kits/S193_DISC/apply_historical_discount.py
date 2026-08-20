#!/usr/bin/env python3
# =====================================================================
#  S193_DISC — historical discount backfill.
#
#  Fills sale_item.gross_p / sale_item.disc_p for bills already in the
#  books, from historical_discount.csv (parsed from Dr Manoj's own Marg
#  "Bill wise sales" exports, 2026-04-01 .. 2026-08-15).
#
#  The CSV is NON-PHI: bill_date, bill_no, gross_p, disc_p, net_p only —
#  no patient names, no phones, no clinic IDs.
#
#  SAFETY:
#   * Matches on (source_ref == bill_no) AND (day's business_date) AND
#     unit='medical'.  The parse had ZERO (date,bill_no) key clashes.
#   * NEVER touches amount_p (the booked net) or any other column — it
#     only writes gross_p/disc_p, which are pure added information.
#   * Stores MAGNITUDES (abs), consistent with amount_p >= 0.
#   * Idempotent: re-running writes the same values; reports a summary.
#   * --dry (default) shows what WOULD change and writes nothing.
#     --apply performs the UPDATEs inside one transaction.
#
#  Usage:
#     python3 apply_historical_discount.py --dry     # preview
#     python3 apply_historical_discount.py --apply   # write
# =====================================================================
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import historical_discount_data as _hdd

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
UNIT = "medical"


def load_csv():
    # Data ships as a Python module (historical_discount_data.py) because the
    # repo's .gitignore blocks *.csv (patient-data guard); this file is NON-PHI.
    rows = []
    for bill_date, bill_no, gross_p, disc_p, net_p in _hdd.ROWS:
        rows.append({
            "bill_date": bill_date.strip(),
            "bill_no": bill_no.strip(),
            "gross_p": abs(int(gross_p)),
            "disc_p": abs(int(disc_p)),
            "net_p": abs(int(net_p)),
        })
    return rows


def main():
    apply = "--apply" in sys.argv
    rows = load_csv()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    # Guard: the columns must exist (migration must have run first).
    cols = {c["name"] for c in con.execute("PRAGMA table_info(sale_item)")}
    if "gross_p" not in cols or "disc_p" not in cols:
        print("*** sale_item is missing gross_p/disc_p — run the migration first. STOP.")
        sys.exit(2)

    matched = 0
    unmatched = 0
    would_set = 0
    already = 0
    net_mismatch = 0
    ambiguous = 0
    examples_unmatched = []
    examples_netmis = []

    con.execute("BEGIN")
    for r in rows:
        hits = con.execute(
            "SELECT s.id, s.amount_p, s.gross_p, s.disc_p "
            "FROM sale_item s JOIN day_entry de ON de.id = s.day_entry_id "
            "WHERE de.unit=? AND de.business_date=? AND s.source_ref=?",
            (UNIT, r["bill_date"], r["bill_no"])).fetchall()
        if not hits:
            unmatched += 1
            if len(examples_unmatched) < 8:
                examples_unmatched.append((r["bill_date"], r["bill_no"]))
            continue
        if len(hits) > 1:
            ambiguous += 1
        for h in hits:
            matched += 1
            if abs(h["amount_p"] or 0) != r["net_p"]:
                net_mismatch += 1
                if len(examples_netmis) < 8:
                    examples_netmis.append(
                        (r["bill_date"], r["bill_no"], h["amount_p"], r["net_p"]))
            if h["gross_p"] == r["gross_p"] and h["disc_p"] == r["disc_p"]:
                already += 1
            else:
                would_set += 1
                if apply:
                    con.execute(
                        "UPDATE sale_item SET gross_p=?, disc_p=? WHERE id=?",
                        (r["gross_p"], r["disc_p"], h["id"]))
    if apply:
        con.commit()
    else:
        con.rollback()

    tot_disc = sum(r["disc_p"] for r in rows) / 100.0
    print("=== historical discount backfill (%s) ===" % ("APPLY" if apply else "DRY-RUN"))
    print("  csv rows            : %d  (total discount in file ₹ %.2f)" % (len(rows), tot_disc))
    print("  matched sale_item   : %d" % matched)
    print("  would set / updated : %d" % would_set)
    print("  already correct     : %d" % already)
    print("  unmatched bills     : %d  (not in the books for that date — expected for gaps)" % unmatched)
    print("  ambiguous (>1 row)  : %d" % ambiguous)
    print("  net differs (info)  : %d  (gross/disc still added; booked net untouched)" % net_mismatch)
    if examples_unmatched:
        print("  e.g. unmatched      :", examples_unmatched)
    if examples_netmis:
        print("  e.g. net differs    :", examples_netmis)
    if not apply:
        print("  (dry-run — nothing written. Re-run with --apply to write.)")
    con.close()


if __name__ == "__main__":
    main()
