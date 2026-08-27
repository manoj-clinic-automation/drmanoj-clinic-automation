#!/usr/bin/python3
"""selftest_sale_continuity.py — the completeness gate, asserted on real bills."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sale_continuity as SC

_fail, _pass = [], 0
def ck(l, c, d=""):
    global _pass
    if c: _pass += 1; print("  ok   %s" % l)
    else: _fail.append(l); print("  FAIL %s   %s" % (l, d))

print("[1] bill parsing")
ck("'A003195' -> ('A',3195)", SC.parse_bill("A003195") == ("A", 3195))
ck("'CN00098' -> ('CN',98)", SC.parse_bill("CN00098") == ("CN", 98))
ck("a non-bill is rejected", SC.parse_bill("TOTAL") is None)

print("\n[2] THE SUNDAY CASE — a closed day is CONTIGUOUS, not a gap")
rows = [{"date": "2026-08-22", "bill": "A003159"},
        {"date": "2026-08-24", "bill": "A003160"}]
c = SC.chains(rows)["A"]
ck("no gap reported across the closed Sunday", not c["gaps"], repr(c["gaps"]))
ck("next expected is A003161", c["next_expected"] == "A003161", c["next_expected"])

print("\n[3] IT MUST STILL CATCH A REAL GAP — otherwise it measures nothing")
rows = [{"date": "2026-08-22", "bill": "A003159"},
        {"date": "2026-08-24", "bill": "A003165"}]
c = SC.chains(rows)["A"]
ck("a 5-bill gap IS reported",
   c["gaps"] and c["gaps"][0]["missing"] == 5, repr(c["gaps"]))

print("\n[4] a bill missing INSIDE a day is caught")
rows = [{"date": "2026-08-22", "bill": "A003159"},
        {"date": "2026-08-22", "bill": "A003161"}]
c = SC.chains(rows)["A"]
ck("in-day hole reported", c["days"][0]["missing_in_day"] == 1,
   repr(c["days"][0]))

print("\n[5] against the real archive")
p = os.path.expanduser("~/q1.json")
if not os.path.exists(p):
    print("  --   no parsed cache; run load_archive.py first")
else:
    ch = SC.chains(json.load(open(p))["sale"])
    a = ch["A"]
    ck("10 sale days archived under prefix A", len(a["days"]) == 10, str(len(a["days"])))
    ck("no bill is missing inside any archived day",
       all(d["missing_in_day"] == 0 for d in a["days"]),
       repr([d for d in a["days"] if d["missing_in_day"]]))
    ck("exactly one gap, and it is the pre-17-Aug block",
       len(a["gaps"]) == 1 and a["gaps"][0]["missing"] == 1430, repr(a["gaps"]))
    ck("17-Aug..26-Aug is one unbroken chain",
       all(a["days"][i]["last"] + 1 == a["days"][i + 1]["first"]
           for i in range(1, len(a["days"]) - 1)))
    ck("next report must begin at A003216", a["next_expected"] == "A003216",
       a["next_expected"])

print("\n%d passed, %d failed" % (_pass, len(_fail)))
for f in _fail: print("  FAILED: %s" % f)
sys.exit(1 if _fail else 0)
