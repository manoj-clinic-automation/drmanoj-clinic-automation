#!/usr/bin/env python3
"""
EQUIV_pack.py -- do the VPS lane's TWO pack parsers agree on the owner's REAL data?

finance_item_anomaly.py is LIVE on the VPS and carries its own pack_size/units.
finance_money.py (S212) carries another. Before either is pointed at the other,
the question is not "which is prettier" but "do they differ on anything that
actually occurs in this shop's data". Every (pack, qty) pair observed in the
archive is enumerated and both are run over all of them.

The two return DIFFERENT SHAPES on purpose:
    anomaly.units  -> BASE UNITS (tablets)   -- what a quantity comparison needs
    money.units    -> PACKS (fractional)     -- what money needs
so the identity under test is:  money.units * pack_size == anomaly.units
"""
import os, sys, collections
sys.path.insert(0, sys.argv[1])          # finance/  (marg_report)
sys.path.insert(0, sys.argv[2])          # S211_MATCH/ (finance_item_anomaly)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marg_report
import finance_money as M
import finance_item_anomaly as A

pairs = collections.Counter()
for root, _d, ns in os.walk(sys.argv[3]):
    for n in sorted(ns):
        if "BILLWISE_DETAIL" not in n.upper():
            continue
        try:
            rep = marg_report.read_report(os.path.join(root, n), keep_items=True)
        except Exception:
            continue
        for d in rep["days"]:
            for it in d["items"]:
                p = it["parsed"]
                pairs[(p.get("pack"), p.get("qty_raw"))] += 1

print("distinct (pack, qty) pairs observed: %d  over %d lines"
      % (len(pairs), sum(pairs.values())))

agree = disagree = 0
bad = []
for (pack, qty), cnt in sorted(pairs.items(), key=lambda x: -x[1]):
    ms, asz = M.pack_size(pack), A.pack_size(pack)
    mu, au = M.units(qty, pack), A.units(qty, pack)
    # normalise money's PACKS to BASE UNITS for comparison
    mu_base = None
    if mu is not None:
        mu_base = mu * ms if ms else mu
    same = (mu_base is None and au is None) or (
        mu_base is not None and au is not None and abs(mu_base - au) < 1e-9)
    if same:
        agree += cnt
    else:
        disagree += cnt
        bad.append((cnt, pack, qty, ms, asz, mu_base, au))

print()
print("lines where the two AGREE    : %6d" % agree)
print("lines where the two DISAGREE : %6d" % disagree)
if bad:
    print()
    print("%-8s %-10s %-8s %6s %6s %10s %10s" %
          ("lines", "pack", "qty", "M.size", "A.size", "M.base", "A.base"))
    for cnt, pack, qty, ms, asz, mb, au in bad:
        print("%-8d %-10r %-8r %6s %6s %10s %10s" % (cnt, pack, qty, ms, asz, mb, au))
print()
print("VERDICT: %s" % ("EQUIVALENT on every pair in this data -- the substitution "
                       "is a proven no-op" if not bad else
                       "THEY DIFFER -- read the table above before substituting"))
