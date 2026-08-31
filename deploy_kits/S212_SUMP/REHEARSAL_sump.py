#!/usr/bin/env python3
"""
REHEARSAL_sump.py -- S212. Proves finance_money.py IS the S211 model.

The test is not "does it run". The test is: does this implementation reproduce
the SAME 373-of-374 that S211 measured, using the ingest's own parser?
A lookalike parser measures the lookalike (S211's own lesson), so the real
marg_report is imported, never re-implemented.
"""
import os
import sys
import collections

FIN = r"/sessions/PLACEHOLDER"
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import marg_report
import finance_money as M

ARCHIVE = sys.argv[2]

files = []
for root, _dirs, names in os.walk(ARCHIVE):
    for n in sorted(names):
        if "BILLWISE_DETAIL" in n.upper():
            files.append(os.path.join(root, n))

print("archive files found: %d" % len(files))

bills_total = cn_total = exact = off = unread = 0
worst = []
refused = []
returns_lines = 0
returns_value_p = 0

for f in files:
    try:
        rep = marg_report.read_report(f, keep_items=True)
    except Exception as e:
        refused.append((os.path.basename(f), str(e)[:70]))
        continue
    for d in rep["days"]:
        date = d.get("date") or d.get("business_date") or "?"
        by_bill = collections.defaultdict(list)
        for it in d.get("items", []):
            by_bill[it["bill_no"]].append(it["parsed"])
        for b in d.get("bills", []):
            lines = by_bill.get(b["bill_no"], [])
            if not lines:
                continue
            bills_total += 1
            gross, bad = M.bill_gross_p(lines)
            printed = abs(b["gross_p"] or 0)
            if b["is_credit_note"]:
                cn_total += 1
                returns_lines += len(lines)
                returns_value_p += gross
            if bad:
                unread += bad
            diff = gross - printed
            if abs(diff) <= 2:
                exact += 1
            else:
                off += 1
                worst.append((abs(diff), date, b["bill_no"], printed, gross, len(lines)))

print()
print("=" * 74)
print("THE MONEY MODEL, re-measured with THIS implementation")
print("=" * 74)
print("  bills with item lines        %6d   (S211 measured 374)" % bills_total)
print("  of which credit notes        %6d   (S211 measured 29)" % cn_total)
print("  gross reproduced exactly     %6d   (S211 measured 373)" % exact)
print("  did not reconcile            %6d   (S211 measured 1)" % off)
print("  individual lines unreadable  %6d" % unread)
if bills_total:
    print("  accuracy                     %6.1f%%" % (100.0 * exact / bills_total))
print()
if worst:
    print("the bills that did NOT reconcile, worst first:")
    print("  %-12s %-10s %12s %12s %6s" % ("date", "bill", "printed", "computed", "lines"))
    for d_, date, bill, printed, got, n in sorted(worst, reverse=True)[:10]:
        print("  %-12s %-10s %12s %12s %6d"
              % (date, bill, M.rupees(printed), M.rupees(got), n))
    print()
print("SALE RETURNS in this archive slice, valued with the model:")
print("  credit notes                 %6d" % cn_total)
print("  their item lines             %6d" % returns_lines)
print("  their value                  %s" % M.rupees(returns_value_p))
print()
if refused:
    print("FILES THE READER REFUSED (%d) -- not clean, unexaminable:" % len(refused))
    for n, e in refused:
        print("  %s\n     %s" % (n, e))
