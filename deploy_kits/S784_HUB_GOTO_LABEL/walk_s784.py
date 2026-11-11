#!/usr/bin/env python3
"""walk_s784.py FILE LIVE_FILE [--control] -- FILE: the built (or, for the control, the live) finance_approvals.html; LIVE_FILE: the live one.
Last line: 'WALK S784 GREEN' or, with --control on the live file, 'CONTROL S784 RED as it must be'."""
import difflib
import sys

F, LIVE = sys.argv[1:3]
CONTROL = "--control" in sys.argv
a, b = open(LIVE, encoding="utf-8").read().splitlines(), open(F, encoding="utf-8").read().splitlines()
new = '<a href="/finance/purchase/page/scans">Purchase bills — in Marg · scanned · differences</a>'
diff = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and not l.startswith(("+++", "---"))]
res = [("1 the Go-to panel names the Purchase bills page by its new name, once", sum(1 for l in b if new in l) == 1),
       ("2 the link still goes to /finance/purchase/page/scans", any("/finance/purchase/page/scans" in l and new in l for l in b)),
       ("3 the old name is gone", not any("Scan register (bills ↔ Marg)" in l for l in b)),
       ("4 exactly one line differs from the live file (the label), nothing else", len(diff) == 2 and diff[0].startswith("-") and diff[1].startswith("+")),
       ("5 the link sits in the Purchases & dealers group, in the same place",
        any(new in l for l in b) and any("Scan register (bills" in l for l in a)
        and [i for i, l in enumerate(b) if new in l] == [i for i, l in enumerate(a) if "Scan register (bills" in l])]
for n, ok in res:
    print(("GREEN " if ok else "RED   ") + n)
red = [n for n, ok in res if not ok]
if CONTROL:
    print("CONTROL S784 RED as it must be" if red else "CONTROL S784 NOT RED")
    sys.exit(0)
print("WALK S784 GREEN" if not red else "WALK S784 RED: " + "; ".join(red))
