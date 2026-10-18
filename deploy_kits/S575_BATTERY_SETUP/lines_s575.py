#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lines_s575.py -- a frozen earlier walk, re-run on the S575 file, with exactly the lines S575 forces in their new form.

    python3 lines_s575.py browser571 <the frozen walk> <out: a copy in /tmp (or the PC's _scratch)>

The earlier kits are never edited (a published kit is frozen); the copy is written elsewhere. Each line below must be found exactly
the counted number of times, or this refuses (exit 1). Each is an INTENDED change:
  browser571 B3 -- S575 item 2 (R1 C4): New battery fitted now holds a closed fold, "Show older / other papers", with the wider list
                and "Find by stamp". A field inside a CLOSED fold has no size on the screen by design, so B3 measures the fields a
                person sees (not inside a closed <details>); every one of them and Save must still be on one 1366 x 768 screen. S575's
                own browser walk (F2) opens the fold and checks its fields too. Nothing else in the walk changes."""
import sys

LINES = {
    "browser571": (
        ("out.fields=Array.prototype.map.call(f.querySelectorAll('input,select,button'),",
         "out.fields=Array.prototype.map.call(Array.prototype.filter.call(f.querySelectorAll('input,select,button'),"
         "function(e){return !e.closest('details:not([open])');}),", 1),
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
    print("%s walk copied to %s with its %d line%s in S575's form" % (which.upper(), out, len(LINES[which]), "" if len(LINES[which]) == 1 else "s"))


if __name__ == "__main__":
    main()
