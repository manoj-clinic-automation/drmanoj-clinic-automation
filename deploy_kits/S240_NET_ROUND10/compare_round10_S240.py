#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_round10_S240.py <before.html> <after.html>

Proves the net -- and ONLY the net -- was cut to the last Rs.10:

  * SHEET 3 keeps every name in the same order, and every column except the last is unchanged
    to the paisa;
  * every net is exactly its old value cut towards zero to the last Rs.10 -- never rounded up,
    never off by more than Rs.9.99, and an already-round net does not move;
  * the TOTAL row's net equals the sum of the rounded nets, so the sheet still adds up;
  * SHEET 4 shows the same rounded rupee for the same person, in the same order;
  * the own sheets show the rounded net on both their pages, with a round-off line to explain it.

Exits non-zero on any failure, and the installer then puts the file back."""
import io
import re
import sys

b = io.open(sys.argv[1], encoding="utf-8").read()
a = io.open(sys.argv[2], encoding="utf-8").read()
ok = True


def ck(name, cond, extra=""):
    global ok
    print(("  ok    " if cond else "  FAIL  ") + name + (("   " + str(extra)) if not cond else ""))
    ok = ok and cond


def cut(x):
    return float(int(abs(x) / 10) * 10) * (-1.0 if x < 0 else 1.0)


S4 = re.compile(r"<tr style='height:40px'><td>(\d+)</td><td><b>(.*?)</b></td>"
                r"<td class='n'>([-\d\.]+)</td>")
S3 = re.compile(r"<tr><td><b>(.*?)</b></td>((?:<td class='n'>[-\d\.]+</td>)+)</tr>")
TOT = re.compile(r'<tr class="tot"><td>TOTAL</td>((?:<td class=\'n\'>[-\d\.]+</td>)+)')
NUM = re.compile(r"<td class='n'>([-\d\.]+)</td>")
NET = re.compile(r"<tr class='net'><td><b>[^<]*</b></td><td class='n'><b>([-\d\.]+)</b></td>")

r3b = [(n.strip(), [float(x) for x in NUM.findall(c)]) for n, c in S3.findall(b)]
r3a = [(n.strip(), [float(x) for x in NUM.findall(c)]) for n, c in S3.findall(a)]
ck("SHEET 3 has rows", len(r3b) > 0 and len(r3b) == len(r3a),
   "%d vs %d" % (len(r3b), len(r3a)))
if not ok:
    print("\nNOT PROVED")
    sys.exit(1)
ck("SHEET 3 keeps every name, in the same order", [n for n, _ in r3b] == [n for n, _ in r3a])
ck("every column except the last is unchanged to the paisa",
   all(x[:-1] == y[:-1] for (_, x), (_, y) in zip(r3b, r3a)),
   [n for (n, x), (_, y) in zip(r3b, r3a) if x[:-1] != y[:-1]][:4])

bad = [(n, x[-1], y[-1]) for (n, x), (_, y) in zip(r3b, r3a) if abs(cut(x[-1]) - y[-1]) > 0.0001]
ck("every net is its old value cut towards zero to the last Rs.10", not bad, bad[:4])
big = [(n, x[-1], y[-1]) for (n, x), (_, y) in zip(r3b, r3a) if abs(x[-1] - y[-1]) >= 10]
ck("no net moved by Rs.10 or more", not big, big[:4])
up = [(n, x[-1], y[-1]) for (n, x), (_, y) in zip(r3b, r3a) if abs(y[-1]) > abs(x[-1]) + 0.0001]
ck("no net was rounded UP, in either direction", not up, up[:4])
still = [(n, x[-1]) for (n, x), (_, y) in zip(r3b, r3a)
         if abs(x[-1]) % 10 < 0.0001 and abs(x[-1] - y[-1]) > 0.0001]
ck("an already-round net did not move", not still, still[:4])
moved = sum(1 for (_, x), (_, y) in zip(r3b, r3a) if abs(x[-1] - y[-1]) > 0.0001)
print("     %d of %d nets were cut; the largest cut is Rs.%.2f"
      % (moved, len(r3b), max([abs(x[-1] - y[-1]) for (_, x), (_, y) in zip(r3b, r3a)] or [0])))

ta = [float(x) for x in NUM.findall(TOT.search(a).group(1))] if TOT.search(a) else []
tb = [float(x) for x in NUM.findall(TOT.search(b).group(1))] if TOT.search(b) else []
ck("the TOTAL row was found before and after", bool(ta) and len(ta) == len(tb))
if ta and len(ta) == len(tb):
    ck("every TOTAL except the net is unchanged", ta[:-1] == tb[:-1],
       [(i, tb[i], ta[i]) for i in range(len(tb) - 1) if tb[i] != ta[i]][:4])
    ck("the TOTAL net is the sum of the rounded nets",
       abs(sum(y[-1] for _, y in r3a) - ta[-1]) < 0.011,
       "sum %.2f vs total %.2f" % (sum(y[-1] for _, y in r3a), ta[-1]))
    print("     total net: %.2f  ->  %.2f" % (tb[-1], ta[-1]))

p4a = {n.strip(): float(v) for _, n, v in S4.findall(a)}
p4b = [(n.strip(), float(v)) for _, n, v in S4.findall(b)]
ck("SHEET 4 keeps every name, in the same order",
   [n for n, _ in p4b] == [n.strip() for _, n, _ in S4.findall(a)])
ck("SHEET 4 pays the same rounded rupee as SHEET 3 for every person",
   all(abs(p4a.get(n, 1e9) - y[-1]) < 0.0001 for (n, y) in r3a),
   [(n, p4a.get(n), y[-1]) for (n, y) in r3a if abs(p4a.get(n, 1e9) - y[-1]) > 0.0001][:4])

if "SHEET 5" in a:
    nets = [float(x) for x in NET.findall(a)]
    ck("the own sheets show a net on both pages", len(nets) == 2, nets)
    ck("both own-sheet nets are the same rounded rupee",
       len(nets) == 2 and nets[0] == nets[1] and abs(nets[0]) % 10 < 0.0001, nets)
    exact = [float(x) for x in NET.findall(b)]
    want = 2 if (exact and abs(exact[0]) % 10 > 0.0001) else 0
    ck("the round-off line explains it on both pages, and only when there is one",
       a.count("Round off") == want, "%d lines, expected %d" % (a.count("Round off"), want))
    print("     own sheets: %s" % nets)

print("\n%s" % ("PROVED" if ok else "NOT PROVED"))
sys.exit(0 if ok else 1)
