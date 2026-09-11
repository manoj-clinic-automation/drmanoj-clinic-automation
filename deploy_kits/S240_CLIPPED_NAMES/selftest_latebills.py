#!/usr/bin/python3
"""selftest_latebills.py -- S240. The keying-vs-dating rules of push_expected,
on hand-made evidence (no Marg files needed). Run from the folder that holds
push_expected.py:   python -B selftest_latebills.py"""
import datetime as dt, os, sys
sys.path.insert(0, os.getcwd())
import push_expected as PE

D = lambda s: dt.datetime.strptime(s, "%d-%m-%Y").date()
row = lambda item, q: {"item": item, "loose_qty": q, "bill_no": "x"}
ok = bad = 0
def check(name, cond):
    global ok, bad
    print(("PASS  " if cond else "FAIL  ") + name)
    ok, bad = ok + bool(cond), bad + (not cond)

def run(exports, closings, B, T_b):
    PE.bill_dates = lambda a: ({}, [], [])
    PE._item_exports = lambda a, d: exports
    PE._closings = lambda a: closings
    return PE.keyed_vs_dated("x", D(B), T_b)

K1 = (D("01-09-2026"), "571")
K2 = (D("05-09-2026"), "15521")
K3 = (D("07-09-2026"), "900")
ex = [
  ("20260903-112846", "ITEM WISE", D("01-09-2026"), D("03-09-2026"), {}, "a"),
  ("20260906-090707", "BILL ITEM WISE", D("04-09-2026"), D("06-09-2026"), {}, "b"),
  ("20260911-140731", "ITEM WISE", D("01-09-2026"), D("11-09-2026"),
   {K1: [row("SPLINT", 2)], K2: [row("SHELCAL", 300)]}, "c"),
]
cl = [("20260904-030844", {"SPLINT": 0}), ("20260906-030421", {"SPLINT": 0}),
      ("20260906-085256", {"SPLINT": 2}), ("20260912-080000", {"SPLINT": 2})]
cl = [("20260902-172308", {"SPLINT": 0})] + cl
late, lrep, early, erep, unk = run(ex, cl, "06-09-2026", "20260906-085256")
check("a bill absent from an export taken AFTER the baseline is late",
      "15521" in [r[1] for r in lrep])
late, lrep, early, erep, unk = run(ex, cl, "03-09-2026", "20260904-030844")
got = sorted(r[1] for r in lrep)
check("a straddling bill is settled by the closing step", "571" in got)
check("a bill dated after the baseline is left to the date rule", "15521" not in got)
check("late rows carry their bill date", all(r["_date"] <= D("05-09-2026") for r in late))
check("nothing called early", not early)

# keyed BEFORE the baseline: in an export taken before it -> left alone
ex2 = [("20260902-100000", "ITEM WISE", D("01-09-2026"), D("02-09-2026"),
        {K1: [row("SPLINT", 2)]}, "a")] + ex[2:]
late, lrep, early, erep, unk = run(ex2, cl, "03-09-2026", "20260904-030844")
check("a bill already in an earlier export is NOT added", "571" not in [r[1] for r in lrep])

# step in the gap BEFORE the baseline -> in the baseline
cl2 = [("20260903-000000", {"SPLINT": 0}), ("20260904-030844", {"SPLINT": 2}),
       ("20260912-080000", {"SPLINT": 2})]
late, lrep, *_ = run([ex[0], ex[2]], cl2, "03-09-2026", "20260904-030844")
check("a step before the baseline capture keeps the bill inside it", "571" not in [r[1] for r in lrep])

# no closing after the window -> unknown, named, not added
late, lrep, early, erep, unk = run(ex, cl[:4], "03-09-2026", "20260904-030844")
check("no closing on the far side -> keying time unknown, not added",
      "571" in [u[1] for u in unk] and "571" not in [r[1] for r in lrep])

# EARLY: dated after the baseline but already in an export taken before it
ex3 = [("20260906-080000", "ITEM WISE", D("07-09-2026"), D("07-09-2026"),
        {K3: [row("X", 1)]}, "e")]
late, lrep, early, erep, unk = run(ex3, cl, "06-09-2026", "20260906-085256")
check("a bill in an export taken before the baseline is not counted again", K3 in early)

os.environ["LATE_KEYED"] = "off"
late, lrep, early, erep, unk = run(ex, cl, "03-09-2026", "20260904-030844")
check("LATE_KEYED=off switches the whole rule off", not (late or early or unk))
del os.environ["LATE_KEYED"]

check("ITEM WISE cut name completes to the one full name",
      PE._complete_name("TYNOR WRIST SPLINT LF L ELA",
                        {"TYNOR WRIST SPLINT LF L ELAST": 1}) == "TYNOR WRIST SPLINT LF L ELAST")
check("a short name is never completed",
      PE._complete_name("PAN 40", {"PAN 40 DSR": 1}) == "PAN 40")
check("two candidates -> left as it is",
      PE._complete_name("TYNOR WRIST SPLINT LF L E",
                        {"TYNOR WRIST SPLINT LF L ELAST": 1, "TYNOR WRIST SPLINT LF L EXTRA": 1})
      == "TYNOR WRIST SPLINT LF L E")
print("\n%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
