#!/usr/bin/env python3
"""Proves the supersede rule on the OWNER'S OWN ARCHIVE, where the answer is known."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marg_effective as E

P, F = 0, 0
def ck(label, cond, extra=""):
    global P, F
    if cond: P += 1; print("  ok   %s" % label)
    else:    F += 1; print("  FAIL %s   %s" % (label, extra))

# --- the rule itself, on names alone ---------------------------------------
ck("a single date is a one-day span", E.span("X__2026-08-18__20260819-093823__a.XLS") == ("2026-08-18","2026-08-18"))
ck("a range is read whole", E.span("X__2026-08-23_to_2026-08-24__20260825-081605__b.XLS") == ("2026-08-23","2026-08-24"))
ck("a wider span covers a narrower one", E.covers(("2026-08-01","2026-08-26"), ("2026-08-18","2026-08-18")))
ck("a narrower span does not cover a wider one", not E.covers(("2026-08-18","2026-08-18"), ("2026-08-01","2026-08-26")))
ck("no span is read from a nameless file", E.span("REPORT_1.XLS") is None)

# month-to-date, the shape Amir's visits will produce
mtd = ["P__2026-08-01_to_2026-08-05__20260805-100000__a.XLS",
       "P__2026-08-01_to_2026-08-12__20260812-100000__b.XLS",
       "P__2026-08-01_to_2026-08-20__20260820-100000__c.XLS"]
kept, sup = E.effective(mtd)
ck("three month-to-date exports collapse to ONE", len(kept) == 1 and len(sup) == 2,
   "kept %d superseded %d" % (len(kept), len(sup)))
ck("and the one kept is the widest", kept and kept[0].endswith("c.XLS"), kept)

# same day exported twice -- later stamp wins, never both
same = ["S__2026-08-18__20260819-093823__x.XLS", "S__2026-08-18__20260822-092931__y.XLS"]
kept2, sup2 = E.effective(same)
ck("the same day exported twice keeps ONE", len(kept2) == 1, kept2)
ck("and it is the later export", kept2 and kept2[0].endswith("y.XLS"), kept2)

# a file we cannot read must never be silently dropped
kept3, _ = E.effective(mtd + ["REPORT_1.XLS"])
ck("a file with no readable span is KEPT, never dropped", "REPORT_1.XLS" in kept3)

# --- against the real archive ----------------------------------------------
A = os.environ.get("MARG_ARCHIVE") or r"D:\Downloads\margsync\MargArchive"
if not os.path.isdir(A):
    A = os.path.expanduser("~/mnt/Downloads/margsync/MargArchive")
if os.path.isdir(A):
    print()
    for t in ("SALE_BILLWISE", "PURCHASE_ITEMWISE", "PURCHASE_BILLWISE"):
        kept, sup = E.effective_for(A, t)
        print("  %-22s %2d files -> %2d counted, %d superseded" % (t, len(kept)+len(sup), len(kept), len(sup)))
        for p, by in sup:
            print("        superseded: %-56s" % os.path.basename(p)[:56])
            print("             by     : %-56s" % os.path.basename(by)[:56])
    ks, ss = E.effective_for(A, "SALE_BILLWISE")
    ck("the sale archive's known overlaps are caught", len(ss) >= 3,
       "%d superseded" % len(ss))
    kp, sp = E.effective_for(A, "PURCHASE_ITEMWISE")
    ck("the purchase archive is clean today -- nothing superseded", len(sp) == 0,
       "%d superseded" % len(sp))
else:
    print("\n  (archive not reachable -- name-level checks only)")

print("\n%d passed, %d failed" % (P, F))
sys.exit(1 if F else 0)
