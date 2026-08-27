#!/usr/bin/python3
"""selftest_purchase_returns.py — the returns rule, asserted on all five real months."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marg_purchase as MP, purchase_returns as PR

A = os.path.expanduser("~/mnt/Downloads/margsync/MargArchive")
_f, _p = [], 0
def ck(l, c, d=""):
    global _p
    if c: _p += 1; print("  ok   %s" % l)
    else: _f.append(l); print("  FAIL %s   %s" % (l, d))

print("[1] the rule in isolation — excess is TWICE the return, never once")
rows = [{"amount": 100.0, "item": "X", "bill": "900"},
        {"amount": 40.0,  "item": "Y", "bill": "901"},
        {"amount": 40.0,  "item": "Y", "bill": "7"}]
rets, exact = PR.returns_from_variance(rows, 80.0)
ck("an excess of 80 finds a return of 40", exact and len(rets) == 1 and rets[0]["amount"] == 40.0,
   repr(rets))
ck("and picks the LOW bill number of the twin pair", rets and rets[0]["bill"] == "7",
   repr(rets[0]["bill"] if rets else None))
ck("no excess means no returns", PR.returns_from_variance(rows, 0)[0] == [])

print("\n[2] IT MUST BE ABLE TO FAIL — an excess nothing can explain")
r2, e2 = PR.returns_from_variance(rows, 33.0)
ck("an unexplainable excess reports exact=False, not a guess", not e2 and r2 == [], repr((r2, e2)))

print("\n[3] against all five archived months")
files = sorted(glob.glob(A + "/PURCHASE_ITEMWISE/*/*.XLS"))
ck("five monthly exports present", len(files) == 5, str(len(files)))
tot_ret = 0; closed = 0
for p in files:
    m = os.path.basename(os.path.dirname(p))
    rep = PR.apply(MP.read_purchase(p))
    tot_ret += rep["returns_value"]
    if rep["closes"]: closed += 1
    ck("%s closes to its own GRAND TOTAL after correction" % m, rep["closes"],
       "net %.2f vs grand %.2f" % (rep["items_sum_net"], rep["grand_amount"]))
    ck("%s return detection was exact, not approximate" % m, rep["returns_exact"])
ck("all five months close", closed == 5, str(closed))
print("     five-month returns found: Rs %.2f" % tot_ret)

print("\n[4] JULY — the month the summary reports independently confirm")
rep = PR.apply(MP.read_purchase(sorted(glob.glob(A + "/PURCHASE_ITEMWISE/2026-07/*.XLS"))[0]))
bills = sorted(str(r["bill"]) for r in rep["returns"])
ck("July finds exactly the two bills supplier-wise signs negative (5, 4159)",
   bills == ["4159", "5"], repr(bills))
ck("their combined value is 502.60 — half of the 1005.20 excess",
   abs(rep["returns_value"] - 502.60) < 0.02, str(rep["returns_value"]))

print("\n[5] the corrected five-month total")
tot = 0
for p in files:
    tot += PR.apply(MP.read_purchase(p))["grand_amount"]
ck("grand totals sum to 2,051,598.88", abs(tot - 2051598.88) < 1.0, "%.2f" % tot)

print("\n%d passed, %d failed" % (_p, len(_f)))
for f in _f: print("  FAILED:", f)
sys.exit(1 if _f else 0)
