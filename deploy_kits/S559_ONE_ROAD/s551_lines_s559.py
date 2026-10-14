#!/usr/bin/env python3
"""s551_lines_s559.py -- the frozen S551 walk, re-run on the S559 files, with exactly three of its lines in today's agreed form.

    python3 s551_lines_s559.py <deploy_kits/S551_SORTING_DESK/walk_s551.py> <out: a /tmp copy>

The S551 kit is never edited (a published kit is frozen); the copy is written to /tmp. Each line below must be found
exactly once, or this refuses (exit 1) and the installer stops:
  1. S555 (agreed in S555, kept by S557): the ledger's date line reads dd-mm-yyyy.
  2. S559 item 4: the bills list's row for a non-pharmacy paper leads to the desk opened on it (/desk?open=<id>), not to
     /bills/<id> -- H2's other assertions (the row listed, no instant lane drop-down) are kept as they are.
  3. S559 item 7: All papers' toolbar carries ONE link to The month -- the owner's second link ("Consumption -- now The
     month") is gone; H3 still asserts the one link to /desk/month."""
import sys

LINES = (
    ("checked up to 15-Jun-2031", "checked up to 15-06-2031"),
    ("('href=\"/bills/%d\"' % h2r) in t2", "('href=\"/desk?open=%d\"' % h2r) in t2"),
    ("and \"Consumption — now The month\" in t)", "and \"Consumption — now The month\" not in t)"),
)


def main():
    src, out = sys.argv[1], sys.argv[2]
    s = open(src, encoding="utf-8").read()
    for old, new in LINES:
        n = s.count(old)
        if n != 1:
            sys.exit("REFUSED: the S551 walk line %r was found %d times, not once" % (old[:50], n))
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(s)
    print("S551 walk copied to %s with its %d agreed lines (S555's date form; S559 items 4 and 7)" % (out, len(LINES)))


if __name__ == "__main__":
    main()
