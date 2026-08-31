#!/usr/bin/env python3
"""discount_table.py -- read-only. The sanctioned pharmacy discount, bill by bill.

The owner's shape: sanctioned percent | amount given | did it match. Over-discount
gets a rounding exemption but is still RECORDED, never dropped. The rows given a
HIGHER discount than sanctioned are called out separately -- his word for them was
"intriguing", and they are.

Prints the summary and a masked per-bill table: bill numbers and rupees only, no
name, no number, no clinic ID. Writes nothing.
"""
import collections, os, sqlite3, sys
sys.path.insert(0, "/root/finance")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import finance_daily_gaps as G

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
ROUND_P = int(os.environ.get("PD_ROUND_TOLERANCE_P", "500"))   # Rs 5, in paise
con = sqlite3.connect(DB); con.row_factory = sqlite3.Row

rows = con.execute(
    "SELECT e.business_date d, s.source_ref bill, s.gross_p, s.disc_p, "
    "       p.admin_pd_pct pct, p.clinic_id "
    "FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
    "JOIN patient_ref p ON p.id=s.patient_ref_id "
    "WHERE e.unit='medical' AND e.business_date >= ? "
    "AND s.service NOT LIKE '%\\_return' ESCAPE '\\' "
    "AND p.admin_pd_pct IS NOT NULL AND p.admin_pd_pct > 0 "
    "ORDER BY e.business_date, s.source_ref", (G.IDENTITY_ERA_START,)).fetchall()

buckets = collections.Counter(); detail = []
for r in rows:
    g = r["gross_p"] or 0
    given = r["disc_p"] or 0
    want = int(round(g * r["pct"] / 100.0))
    diff = given - want
    if g == 0:
        verdict = "no gross amount"
    elif given == 0:
        verdict = "NONE GIVEN"
    elif abs(diff) <= ROUND_P:
        verdict = "matches (within rounding)" if diff else "matches exactly"
    elif diff < 0:
        verdict = "SHORT"
    else:
        verdict = "OVER"
    buckets[verdict] += 1
    detail.append((r["d"], r["bill"], r["pct"], g, want, given, diff, verdict))

print("=" * 78)
print("SANCTIONED PHARMACY DISCOUNT -- post %s" % G.IDENTITY_ERA_START)
print("=" * 78)
print("sales to a patient holding a sanctioned discount: %d\n" % len(rows))
for k, v in buckets.most_common():
    print("   %-28s %5d" % (k, v))
print("\n   rounding tolerance applied: Rs %.2f (recorded, not hidden)" % (ROUND_P / 100.0))

print("\n" + "=" * 78)
print("EVERY ROW THAT DID NOT MATCH")
print("=" * 78)
print("%-11s %-9s %4s %10s %10s %10s %10s  %s" %
      ("date", "bill", "pct", "gross", "sanctioned", "given", "diff", "verdict"))
for d, bill, pct, g, want, given, diff, v in detail:
    if v.startswith("matches"): continue
    print("%-11s %-9s %3d%% %10.2f %10.2f %10.2f %10.2f  %s" %
          (d, bill or "-", pct, g/100.0, want/100.0, given/100.0, diff/100.0, v))

over = [x for x in detail if x[7] == "OVER"]
if over:
    print("\n" + "=" * 78)
    print("THE ONES GIVEN MORE THAN SANCTIONED -- %d of them" % len(over))
    print("=" * 78)
    tot = sum(x[6] for x in over)
    print("   total given beyond sanction: Rs %.2f" % (tot/100.0))
    pcts = collections.Counter(round(100.0 * x[5] / x[3], 0) for x in over if x[3])
    print("   the discount they ACTUALLY got, as a percentage of gross:")
    for k, n in sorted(pcts.items()):
        print("      %3.0f%%  x%d" % (k, n))
    print("   -> a cluster at one percentage suggests a different rule being")
    print("      applied, not carelessness. A scatter suggests discretion.")
con.close()
