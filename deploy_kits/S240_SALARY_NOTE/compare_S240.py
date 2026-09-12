#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_S240.py <before.html> <after.html> -- prove the correction changed what it should and
NOTHING else. Exits non-zero on any failure, and the installer then puts the file back."""
import io
import re
import sys

b = io.open(sys.argv[1], encoding="utf-8").read()
a = io.open(sys.argv[2], encoding="utf-8").read()
ok = True


def ck(name, cond, extra=""):
    global ok
    print(("  ok    " if cond else "  FAIL  ") + name + (("  " + str(extra)) if not cond else ""))
    ok = ok and cond


def sheet4(h):
    i = h.find("SHEET 4")
    return h[i:] if i >= 0 else ""


ck("the footnote said salary/30 before", "salary÷30," in b)
ck("the footnote now says salary/30.5", "salary÷30.5," in a)
ck("...and no longer says salary/30,", "salary÷30," not in a)
ck("SHEET 4 -- every name and every amount -- is byte-identical",
   sheet4(b) == sheet4(a) and len(sheet4(a)) > 100)
nb, na = b.count("<tr>"), a.count("<tr>")
ck("the same number of rows before and after (%d)" % na, nb == na, "%d vs %d" % (nb, na))
db = [x for x in re.findall(r"<td class='n'>([-\d,\.]+)</td>", b)]
da = [x for x in re.findall(r"<td class='n'>([-\d,\.]+)</td>", a)]
diff = [(i, x, y) for i, (x, y) in enumerate(zip(db, da)) if x != y]
ck("at most two numbers on the whole page changed (the leaves cell and its total)",
   len(db) == len(da) and len(diff) <= 2, diff[:6])
print("     changed cells:", diff if diff else "none")
print("\n%s" % ("PROVED" if ok else "NOT PROVED"))
sys.exit(0 if ok else 1)
