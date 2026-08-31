#!/usr/bin/env python3
"""What the OLD sourcing sees, against what the NEW sourcing sees, same data."""
import os, sqlite3, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, HERE)
import finance_money as M, finance_returns_audit as R
con = sqlite3.connect(os.path.join(HERE, "walk.db")); con.row_factory = sqlite3.Row

dates = [r[0] for r in con.execute("SELECT DISTINCT business_date FROM day_entry ORDER BY 1")]
old_n = old_p = new_n = new_p = 0
missed = []
for d in dates:
    # OLD sourcing: sale_item only -- what returns_for_day did before S212
    for r in con.execute(
            "SELECT s.source_ref bill, s.amount_p FROM sale_item s "
            "JOIN day_entry e ON e.id=s.day_entry_id WHERE e.unit='medical' "
            "AND e.business_date=? AND s.service LIKE '%!_return' ESCAPE '!'", (d,)):
        old_n += 1; old_p += abs(r["amount_p"] or 0)
    rows, s = R.returns_for_day(con, d, "medical")
    new_n += s["count"]; new_p += s["value_p"]
    for row in rows:
        if row["population"] == "orphan":
            missed.append((d, row["bill"], row["amount_p"]))

print("=" * 74)
print("OLD sourcing (sale_item only)   %3d returns   %s" % (old_n, M.rupees(old_p)))
print("NEW sourcing (the union)        %3d returns   %s" % (new_n, M.rupees(new_p)))
print("=" * 74)
print("INVISIBLE TO THE OLD CARD: %d returns worth %s"
      % (len(missed), M.rupees(sum(m[2] for m in missed))))
for d, b, p in missed:
    print("   %s  %-10s %s" % (d, b, M.rupees(p)))
