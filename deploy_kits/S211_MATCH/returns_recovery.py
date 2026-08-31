#!/usr/bin/env python3
"""returns_recovery.py -- read-only. How many of the 116 can the ladder reach?

MEASURED at S211, so nothing here is assumed:
  * sale_item holds 179 return bills: 63 shaped like a bill number (A+##),
    116 shaped like an INGEST REFERENCE (S186-F104-394)
  * sale_line_item holds 186 return-flagged bills, ALL shaped like a bill number
  * only 63 join; the orphans' digits appear in NO line-item bill number
  * and 123 line-item returns have no sale_item row at all

So they are two disjoint populations under incompatible keys, not one population
under two prefixes. The only rung that can bridge them is SAME DAY + AMOUNT.
This measures exactly how far that gets, and what is left over.

Counts and masked shapes only. Writes nothing.
"""
import collections, os, re, sqlite3, sys
sys.path.insert(0, "/root/finance")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import finance_returns_audit as A

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row

rets = con.execute(
    "SELECT s.source_ref bill, e.business_date d, s.amount_p, s.patient_ref_id "
    "FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
    "WHERE e.unit='medical' AND s.service LIKE '%!_return' ESCAPE '!' "
    "ORDER BY e.business_date").fetchall()
print("return bills in sale_item: %d\n" % len(rets))

by_rung = collections.Counter()
recovered_dates = collections.Counter()
lost_dates = collections.Counter()
for r in rets:
    lines, how = A.find_return_lines(con, r["bill"], r["d"], r["amount_p"])
    rung = (how.split("(")[0].strip() if how else "NOT FOUND")
    by_rung[rung] += 1
    (recovered_dates if lines else lost_dates)[r["d"][:7]] += 1

print("%-52s %6s" % ("how the item lines were found", "bills"))
for k, v in by_rung.most_common():
    print("%-52s %6d" % (k, v))
tot = sum(by_rung.values()); got = tot - by_rung.get("NOT FOUND", 0)
print("\n   examinable: %d of %d  (%.0f%%)" % (got, tot, 100.0*got/tot if tot else 0))

print("\nwhat is still NOT examinable, by month:")
for m, n in sorted(lost_dates.items()):
    print("   %-9s %4d" % (m, n))
print("\nwhat the ladder recovered, by month:")
for m, n in sorted(recovered_dates.items()):
    print("   %-9s %4d" % (m, n))

print("\n" + "=" * 70)
print("AND THE OTHER SIDE: 123 line-item returns with no sale_item row")
print("=" * 70)
orph = con.execute(
    "SELECT l.bill_no, l.business_date d, SUM(COALESCE(l.amount_p,0)) t, COUNT(*) n "
    "FROM sale_line_item l WHERE l.is_return=1 AND l.bill_no NOT IN "
    "(SELECT source_ref FROM sale_item WHERE source_ref IS NOT NULL) "
    "GROUP BY l.bill_no").fetchall()
print("   line-item returns with no parent bill : %d" % len(orph))
print("   their months:", dict(collections.Counter(o["d"][:7] for o in orph)))
print("   total value: %.2f" % (sum(o["t"] or 0 for o in orph)/100.0))
print("\n   -> these are real returns the panel would NEVER show, because the")
print("      day's returns are listed from sale_item. If they are genuine, the")
print("      day is understating its returns.")
con.close()
