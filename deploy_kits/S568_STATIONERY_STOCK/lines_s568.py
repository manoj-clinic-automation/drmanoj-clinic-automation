#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lines_s568.py -- a frozen earlier walk, re-run on the S568 files, with exactly the lines S568's TO pins force in their new form.

    python3 lines_s568.py s560pack|browser560 <the frozen walk> <out: a copy in /tmp (or the PC's _scratch)>

The earlier kits are never edited (a published kit is frozen); the copy is written elsewhere. Each line below must be found
exactly the counted number of times, or this refuses (exit 1) and the installer stops. Each is an INTENDED change:
  s560pack P2 -- S568 item 8 (D730 item 5; R1 C3): 8.1 now takes only bills and invoices -- made-up final challan LF leaves it
                 (September's 8.1 = the bill LB only).
  s560pack P8 -- the same: the before / after set (against packs.py before S560) now also loses LF.
  browser560  -- S568 item 1: the desk's destination list has one more button (Stationery & packaging, after Others): 16, not 15.
                 Nothing else in the browser walk changes -- every destination must still be on a 1366 x 768 screen."""
import sys

LINES = {
    "s560pack": (
        ('new[("2031-09", "lab_purchase")] == S("LB", "LF"), new[("2031-09", "lab_purchase")])',
         'new[("2031-09", "lab_purchase")] == S("LB"), new[("2031-09", "lab_purchase")])', 1),
        ('gone == S("LC", "LR", "E2") and changed',
         'gone == S("LC", "LF", "LR", "E2") and changed', 1),
    ),
    "browser560": (
        ('base = (r.get("nDest") == 15 and', 'base = (r.get("nDest") == 16 and', 1),
    ),
}


def main():
    which, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
    s = open(src, encoding="utf-8").read()
    for old, new, cnt in LINES[which]:
        n = s.count(old)
        if n != cnt:
            sys.exit("REFUSED: the %s walk line %r was found %d times, not %d" % (which, old[:60], n, cnt))
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(s)
    print("%s walk copied to %s with its %d line%s in S568's form" % (which.upper(), out, len(LINES[which]), "" if len(LINES[which]) == 1 else "s"))


if __name__ == "__main__":
    main()
