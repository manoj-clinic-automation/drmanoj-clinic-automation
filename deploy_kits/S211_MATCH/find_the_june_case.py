#!/usr/bin/env python3
"""find_the_june_case.py -- READ-ONLY. The acid test.

The owner knows of one real fault: a June bill charging 20 tubes of an ointment
when 2 were ordered and 2 were given, later hidden by a Marg stock adjustment.

If the item-anomaly detector cannot surface a bill we ALREADY KNOW ABOUT, it is
decoration. This scans the whole period, not just thirty days, and shows the
quantity outliers with their item names.

Item names are medicines, not patient data, so they are printed. Patient names
and numbers are NOT. Writes nothing.
"""
import collections, os, re, sqlite3, sys
sys.path.insert(0, "/root/finance")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")
import finance_item_anomaly as IA

DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
con.row_factory = sqlite3.Row
days = [r[0] for r in con.execute(
    "SELECT DISTINCT business_date FROM sale_line_item ORDER BY business_date")]
print("scanning %d days: %s .. %s\n" % (len(days), days[0], days[-1]))

allrows = []
tally = collections.Counter()
for d in days:
    # NORMS PER DAY, strictly from earlier days. Computing them ONCE over the
    # whole period put every outlier inside its own yardstick -- which is how
    # the 30-June ointment line cleared itself: with all four of its lines in
    # view its ceiling became 20, and 20 is not eight times 20. Third time this
    # exact mistake was made in one session; it is the caller's job too, not
    # only item_norms'.
    rows, t = IA.scan_day(con, d, "medical")
    tally.update(t)
    for r in rows:
        r["date"] = d
    allrows += rows
print("verdicts over the WHOLE period:")
for k, v in tally.most_common():
    print("   %-34s %6d" % (k, v))

print("\n" + "=" * 74)
print("THE QUANTITY OUTLIERS, worst first -- how many units against the usual")
print("=" * 74)
allrows.sort(key=lambda r: -(r["units"] or 0))
print("%-11s %-28s %8s %10s  %s" % ("date","item","units","usual","verdict"))
seen = 0
for r in allrows:
    if "QUANTITY" not in r["verdict"]: continue
    seen += 1
    if seen > 25: break
    print("%-11s %-28s %8s %10s  %s" %
          (r["date"], str(r["item"])[:28], r["units"],
           (("%g" % r["usual_p95"]) if r.get("usual_p95") else "?"),
           r["verdict"]))
print("\nquantity outliers in total: %d"
      % sum(1 for r in allrows if "QUANTITY" in r["verdict"]))

print("\n" + "=" * 74)
print("JUNE ONLY -- and anything whose name looks like the owner's case")
print("=" * 74)
june = [r for r in allrows if r["date"].startswith("2026-06")]
print("flagged lines in June: %d" % len(june))
for r in sorted(june, key=lambda x: -(x["units"] or 0))[:15]:
    print("   %-11s %-30s %6s units   %s" %
          (r["date"], str(r["item"])[:30], r["units"], r["verdict"]))
hit = [r for r in allrows if re.search(r"ENZOMAC|OINT", str(r["item"]), re.I)]
print("\nlines flagged whose item name contains ENZOMAC or OINT: %d" % len(hit))
for r in hit[:12]:
    print("   %-11s %-30s %6s units   %s" %
          (r["date"], str(r["item"])[:30], r["units"], r["verdict"]))
con.close()
