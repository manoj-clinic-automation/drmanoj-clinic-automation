#!/usr/bin/env python3
"""tally_recent.py -- read-only. Does the matcher work on REAL bills?

Runs the D355 verdicts over the last N filed days and prints counts only.
No patient name, no number, no bill text is printed. Writes nothing.
"""
import os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
sys.path.insert(0, "/root/finance")
import finance_daily_gaps as G

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 7
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
days = [r[0] for r in con.execute(
    "SELECT business_date FROM day_entry WHERE unit='medical' "
    "ORDER BY business_date DESC LIMIT ?", (N,)).fetchall()]
if not days:
    print("no filed days found for unit 'medical'"); raise SystemExit(1)
tot = dict(bills=0, matched=0, ambiguous=0, unmatched=0)
print("%-12s %6s %8s %10s %10s   counter" % ("date","bills","matched","ambiguous","unmatched"))
for d in sorted(days):
    r = G.day_report(con, d, "medical")
    t = r["totals"]
    for k in tot: tot[k] += t[k]
    c = r["counter"]
    print("%-12s %6d %8d %10d %10d   %s (%s)"
          % (d, t["bills"], t["matched"], t["ambiguous"], t["unmatched"],
             c["seller"] or "pending", c["decided_by"]))
print("-" * 66)
pct = (100.0 * tot["matched"] / tot["bills"]) if tot["bills"] else 0
print("%-12s %6d %8d %10d %10d   matched: %.1f%%"
      % ("TOTAL", tot["bills"], tot["matched"], tot["ambiguous"], tot["unmatched"], pct))
p = G.payment_gaps(con, sorted(days)[-1], "medical")
print("\nlatest day payment check: entered digital %s | bank %s | difference %s"
      % (p["entered_digital_p"], p["bank_settled_p"], p["difference_p"]))
print("  ->", p["note"])
con.close()
