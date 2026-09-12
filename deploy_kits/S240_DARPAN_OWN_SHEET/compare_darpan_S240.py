#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_darpan_S240.py <before.html> <after.html> <name>

Proves that ONE person left the sheets and that NOTHING else moved:
  * the name appears nowhere on the page afterwards;
  * SHEET 4 keeps every other name, in the same order, for the same rupee;
  * SHEET 3's totals each drop by exactly that person's own figure -- no more, no less.
Exits non-zero on any failure, and the installer then puts the file back."""
import io
import re
import sys

b = io.open(sys.argv[1], encoding="utf-8").read()
a = io.open(sys.argv[2], encoding="utf-8").read()
who = sys.argv[3].strip().lower()
ok = True

S4 = re.compile(r"<tr style='height:40px'><td>(\d+)</td><td><b>(.*?)</b></td>"
                r"<td class='n'>([-\d\.]+)</td>")
S3 = re.compile(r"<tr><td><b>(.*?)</b></td>((?:<td class='n'>[-\d\.]+</td>)+)</tr>")
TOT = re.compile(r'<tr class="tot"><td>TOTAL</td>((?:<td class=\'n\'>[-\d\.]+</td>)+)')
NUM = re.compile(r"<td class='n'>([-\d\.]+)</td>")


def ck(name, cond, extra=""):
    global ok
    print(("  ok    " if cond else "  FAIL  ") + name + (("   " + str(extra)) if not cond else ""))
    ok = ok and cond


p4b = [(n.strip(), amt) for _, n, amt in S4.findall(b)]
p4a = [(n.strip(), amt) for _, n, amt in S4.findall(a)]
ck("SHEET 4 had the person before", any(n.lower() == who for n, _ in p4b), p4b[:3])
ck("SHEET 4 no longer has the person", not any(n.lower() == who for n, _ in p4a))
ck("SHEET 4 keeps everyone else, same order, same rupee",
   [x for x in p4b if x[0].lower() != who] == p4a,
   "before %d, after %d" % (len(p4b), len(p4a)))
ck("exactly one person left", len(p4b) - len(p4a) == 1, "%d -> %d" % (len(p4b), len(p4a)))
ck("the name appears nowhere on the page now", who not in a.lower())

r3b = {n.strip().lower(): [float(x) for x in NUM.findall(cells)] for n, cells in S3.findall(b)}
tb = [float(x) for x in NUM.findall(TOT.search(b).group(1))] if TOT.search(b) else []
ta = [float(x) for x in NUM.findall(TOT.search(a).group(1))] if TOT.search(a) else []
his = r3b.get(who, [])
ck("SHEET 3 totals found before and after", bool(tb) and len(tb) == len(ta),
   "%d vs %d" % (len(tb), len(ta)))
if tb and len(tb) == len(ta) and len(his) == len(tb):
    bad = [(i, tb[i], his[i], ta[i]) for i in range(len(tb))
           if abs((tb[i] - his[i]) - ta[i]) > 0.011]
    ck("every SHEET 3 total drops by exactly that person's own figure, and nothing else", not bad,
       bad[:4])
    print("     totals: %s  ->  %s" % (tb[:4], ta[:4]))
else:
    ck("that person's own SHEET 3 row was found to subtract", False,
       "row cells %d, total cells %d" % (len(his), len(tb)))

print("\n%s" % ("PROVED" if ok else "NOT PROVED"))
sys.exit(0 if ok else 1)
