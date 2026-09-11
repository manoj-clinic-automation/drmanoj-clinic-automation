#!/usr/bin/python3
"""selftest_clipped.py -- S240 (D466). Clipped sale names settled from the
nightly closings, on hand-made evidence. Run from the folder that holds
push_expected.py:   python -B selftest_clipped.py"""
import datetime as dt, os, sys
sys.path.insert(0, os.getcwd())
import push_expected as PE

D = lambda s: dt.datetime.strptime(s, "%d-%m-%Y").date()
ok = bad = 0
def check(name, cond):
    global ok, bad
    print(("PASS  " if cond else "FAIL  ") + name)
    ok, bad = ok + bool(cond), bad + (not cond)

FAM = {"KNEE SUPPORT HINGED": ["KNEE SUPPORT HINGED L", "KNEE SUPPORT HINGED M"]}
sz = lambda n: 1
def line(d, bill, q=1.0):
    return {"date": D(d), "bill": bill, "_key": "KNEE SUPPORT HINGED",
            "strips": None, "loose": None, "qty_raw": str(q)}
C = lambda l, m: {"KNEE SUPPORT HINGED L": l, "KNEE SUPPORT HINGED M": m}
cl = [("20260827-074818", C(4, 5)), ("20260828-060931", C(3, 4)),
      ("20260829-230000", C(3, 3))]
B, T = D("26-08-2026"), "20260827-074818"

s = [line("27-08-2026", "A1"), line("27-08-2026", "A2")]
a, done, rep, still = PE.resolve_clipped(s, FAM, cl, [], sz, B, T)
check("two sales, one of each size -> L 1 and M 1", a == {"KNEE SUPPORT HINGED L": 1, "KNEE SUPPORT HINGED M": 1})
check("both lines settled", len(done) == 2 and not still)

s = [line("29-08-2026", "A3")]
a, done, rep, still = PE.resolve_clipped(s, FAM, cl, [], sz, B, T)
check("a sale in the second gap lands on the size that fell", a == {"KNEE SUPPORT HINGED M": 1})

s = [line("27-08-2026", "A1")]
a, done, rep, still = PE.resolve_clipped(s, FAM, cl, [], sz, B, T)
check("closings that do not balance settle nothing", not a and len(still) == 1)

s = [line("30-08-2026", "A9")]
a, done, rep, still = PE.resolve_clipped(s, FAM, cl, [], sz, B, T)
check("a sale after the last closing waits", not a and "after the last closing" in still[0][3])

cl2 = [("20260827-074818", C(4, 5)), ("20260828-060931", C(4, 4))]
pur = [{"item": "KNEE SUPPORT HINGED L", "_date": D("27-08-2026"), "loose_qty": 1}]
s = [line("27-08-2026", "A1"), line("27-08-2026", "A2")]
a, done, rep, still = PE.resolve_clipped(s, FAM, cl2, pur, sz, B, T)
check("a purchase keyed in the gap is allowed for", a == {"KNEE SUPPORT HINGED L": 1, "KNEE SUPPORT HINGED M": 1})

pur = [{"item": "KNEE SUPPORT HINGED", "_date": D("27-08-2026"), "loose_qty": 1}]
a, done, rep, still = PE.resolve_clipped(s, FAM, cl2, pur, sz, B, T)
check("a purchase whose own name is clipped blocks the gap", not a)

cl3 = [("20260827-074818", C(4, 5)), ("20260827-150000", C(3, 5)), ("20260828-060931", C(3, 4))]
s = [line("27-08-2026", "A1"), line("27-08-2026", "A2")]
a, done, rep, still = PE.resolve_clipped(s, FAM, cl3, [], sz, B, T)
check("a closing taken during shop hours is not used as a boundary",
      a == {"KNEE SUPPORT HINGED L": 1, "KNEE SUPPORT HINGED M": 1})

s = [line("27-08-2026", "A1"), line("27-08-2026", "CN001")]
cl4 = [("20260827-074818", C(4, 5)), ("20260828-060931", C(4, 5))]
a, done, rep, still = PE.resolve_clipped(s, FAM, cl4, [], sz, B, T)
check("a sale and its return net to nothing", not a and len(done) == 2)

os.environ["CLIP_RESOLVE"] = "off"
a, done, rep, still = PE.resolve_clipped([line("27-08-2026", "A1")], FAM, cl, [], sz, B, T)
check("CLIP_RESOLVE=off switches it off", not a and not done)
del os.environ["CLIP_RESOLVE"]

print("\n%d passed, %d failed" % (ok, bad))
sys.exit(1 if bad else 0)
