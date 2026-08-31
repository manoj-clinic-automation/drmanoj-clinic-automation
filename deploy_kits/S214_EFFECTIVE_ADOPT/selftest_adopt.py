#!/usr/bin/env python3
"""selftest for S214_EFFECTIVE_ADOPT -- proves the four consumers actually
route their flow-report globs through the supersede rule. Invariant-style:
no real archive needed, so it stays green as the archive grows."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(KITS, "S212_SUPERSEDE"))
import marg_effective as ME   # noqa: E402

PASS = FAIL = 0


def check(name, ok):
    global PASS, FAIL
    print("%s  %s" % ("PASS" if ok else "FAIL", name))
    PASS, FAIL = PASS + ok, FAIL + (not ok)


CONSUMERS = {
    "S207_PO/po_build.py": 1,
    "S207_STOCK_VPS/push_snapshot.py": 1,
    "S208_STOCK_LEDGER/push_expected.py": 3,
    "S207_RETURNS/returns_data.py": 2,
}

for rel, n in CONSUMERS.items():
    p = os.path.join(KITS, rel)
    src = open(p, encoding="utf-8").read()
    check("%s imports marg_effective" % rel, "import marg_effective as _ME_sup" in src)
    got = len(re.findall(r"for p in _effective\(", src))
    check("%s routes %d flow-report site(s) through it" % (rel, n), got == n)
    snap = len(re.findall(r'_effective\(glob\.glob\([^)]*STOCK_(CLOSING|EXPIRY)', src))
    check("%s leaves snapshot reports on their F-235 pickers" % rel, snap == 0)
    try:
        compile(src, p, "exec")
        ok = True
    except SyntaxError:
        ok = False
    check("%s compiles" % rel, ok)

# the rule itself: the month-to-date collapse invariant
paths = ["A/SALE_BILLWISE_DETAIL__2026-08-01_to_2026-08-05__20260806-090000__aa.XLS",
         "A/SALE_BILLWISE_DETAIL__2026-08-01_to_2026-08-12__20260813-090000__bb.XLS",
         "A/SALE_BILLWISE_DETAIL__2026-08-01_to_2026-08-20__20260821-090000__cc.XLS"]
kept, sup = ME.effective(paths)
check("month-to-date chain collapses to the widest export",
      kept == [paths[2]] and len(sup) == 2)
kept, sup = ME.effective(["A/X__2026-08-02__20260802-090000__aa.XLS",
                          "A/X__2026-08-02__20260803-090000__bb.XLS"])
check("same-day re-export: later stamp wins", len(kept) == 1 and "bb" in kept[0])
kept, sup = ME.effective(["A/no_span_here.XLS"])
check("a file with no readable span is never dropped", kept == ["A/no_span_here.XLS"])

print("\n%d passed, %d failed" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
