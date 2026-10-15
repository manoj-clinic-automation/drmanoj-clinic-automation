#!/usr/bin/env python3
"""lines_s563.py -- a frozen earlier walk, re-run on the S563 files, with exactly the lines S563's TO pins force in their new form.

    python3 lines_s563.py s560|s559 <the frozen walk_s560.py / walk_s559.py> <out: a /tmp copy>

The earlier kits are never edited (a published kit is frozen); the copy is written to /tmp. Each line below must be found
exactly once, or this refuses (exit 1) and the installer stops.
  s560 K2 -- S563 item 9 (S560-N2): the receipt / statement words are matched on the vendor, the bill number and Claude's
             supplier / number only, never on an item name. K2's reading says 'Money receipt' only in an ITEM line, so it now
             pre-chooses nothing (kind ''), and the tax invoice with the same item line keeps its Bill pre-choice.
  s559 J1 -- S563 item 10: the widget's changed lines against the pre-S559 widget now also hold S563's dropSrc (marked S563, and
             its plain '}' / 'if (adjustIdx === i) adjustIdx = -1;' lines); the four lines gone are the same four.
  s559 J3 -- S563 item 10: dropSrc's C2 shift is now on two lines (the else branch also names the page on the stage button)."""
import sys

LINES = {
    "s560": (
        ("lambda: (pk[k_rc].get(\"kind\"), pk[k_rc].get(\"kind_from\")) == (\"receipt\", \"Claude's reading\") and pk[k_ti].get(\"kind\") == \"\"",
         "lambda: (pk[k_rc].get(\"kind\"), pk[k_rc].get(\"kind_from\")) == (\"\", \"\") and pk[k_ti].get(\"kind\") == \"bill\""),
    ),
    "s559": (
        ("and all(\"S559\" in a for a in added) and len(gone) == 4",
         "and all((\"S559\" in a or \"S563\" in a or a.strip() in (\"}\", \"if (adjustIdx === i) adjustIdx = -1;\")) for a in added) and len(gone) == 4"),
        ("and \"if (adjustIdx === i) adjustIdx = -1; else if (adjustIdx > i) adjustIdx--;\" in jw",
         "and \"if (adjustIdx === i) adjustIdx = -1;\\n    else if (adjustIdx > i) { adjustIdx--;\" in jw"),
    ),
}


def main():
    which, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
    s = open(src, encoding="utf-8").read()
    for old, new in LINES[which]:
        n = s.count(old)
        if n != 1:
            sys.exit("REFUSED: the %s walk line %r was found %d times, not once" % (which, old[:60], n))
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(s)
    print("%s walk copied to %s with its %d line%s in S563's form" % (which.upper(), out, len(LINES[which]), "" if len(LINES[which]) == 1 else "s"))


if __name__ == "__main__":
    main()
