#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_sheets_S240.py <before.html> <after.html> <name>

Proves that TWO pages were ADDED and that NOTHING ELSE ON THE DOCUMENT MOVED:

  * everything printed before the insertion point is byte-identical to before;
  * everything printed after it is byte-identical to before;
  * so the only difference is one inserted block -- and that block is his two pages;
  * the block carries his name, SHEET 5, the SALARY SLIP, the advance line the owner asked for,
    and the same net figure on both pages;
  * SHEET 3 and SHEET 4 keep every row, in the same order, for the same rupee.

Exits non-zero on any failure, and the installer then puts the file back."""
import io
import re
import sys

b = io.open(sys.argv[1], encoding="utf-8").read()
a = io.open(sys.argv[2], encoding="utf-8").read()
who = sys.argv[3].strip()
PAGE = '<div class="s4pg" style="page-break-before:always">'
ok = True


def ck(name, cond, extra=""):
    global ok
    print(("  ok    " if cond else "  FAIL  ") + name + (("   " + str(extra)) if not cond else ""))
    ok = ok and cond


ck("the two pages were not there before",
   ("SHEET 5" not in b) and ("SALARY SLIP" not in b))
ck("SHEET 5 appears exactly once now", a.count("SHEET 5 &middot;") + a.count("SHEET 5 ·") == 1,
   a.count("SHEET 5"))
ck("the SALARY SLIP appears exactly once now", a.count("SALARY SLIP") == 1, a.count("SALARY SLIP"))
if not ok:
    print("\nNOT PROVED")
    sys.exit(1)

i = a.index("SHEET 5")
start = a.rindex(PAGE, 0, i)
head = a[:start]
ck("everything printed BEFORE the new pages is byte-identical", b.startswith(head),
   "head %d bytes" % len(head))
rest = b[len(head):] if b.startswith(head) else None
ck("everything printed AFTER the new pages is byte-identical",
   rest is not None and a.endswith(rest), "tail %d bytes" % (len(rest) if rest else -1))
if not ok:
    print("\nNOT PROVED")
    sys.exit(1)

blk = a[len(head):len(a) - len(rest)]
print("     inserted %d bytes, and not one byte anywhere else" % len(blk))
ck("the inserted block is exactly two printed pages", blk.count(PAGE) == 2, blk.count(PAGE))
ck("it is his", who.lower() in blk.lower(), who)
ck("the advance deduction is on the owner page", "Advance adjusted this month" in blk)
ck("the advance deduction is on his own slip", "Advance kata" in blk)
ck("his leaves, late minutes and marks are on his own slip",
   ("Chhutti" in blk) and ("minute" in blk) and ("mark" in blk))
ck("no advance BALANCE on his own slip -- the history stays on the owner page",
   blk.split("SALARY SLIP")[1].count("balance") == 0
   and blk.split("SALARY SLIP")[1].count("Balance") == 0)
nets = re.findall(r"<tr class='net'><td><b>[^<]*</b></td><td class='n'><b>([-\d\.]+)</b></td>", blk)
ck("both pages show the same net figure", len(nets) == 2 and nets[0] == nets[1], nets)
print("     net on both pages: %s" % (nets[0] if nets else "?"))

S4 = re.compile(r"<tr style='height:40px'><td>(\d+)</td><td><b>(.*?)</b></td>"
                r"<td class='n'>([-\d\.]+)</td>")
S3 = re.compile(r"<tr><td><b>(.*?)</b></td>((?:<td class='n'>[-\d\.]+</td>)+)</tr>")
ck("SHEET 4 keeps every name, in order, for the same rupee", S4.findall(b) == S4.findall(a),
   "%d vs %d rows" % (len(S4.findall(b)), len(S4.findall(a))))
ck("SHEET 3 keeps every row unchanged", S3.findall(b) == S3.findall(a),
   "%d vs %d rows" % (len(S3.findall(b)), len(S3.findall(a))))

print("\n%s" % ("PROVED" if ok else "NOT PROVED"))
sys.exit(0 if ok else 1)
