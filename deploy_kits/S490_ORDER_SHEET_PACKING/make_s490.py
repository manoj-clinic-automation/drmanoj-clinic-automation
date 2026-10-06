#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s490.py -- kit S490_ORDER_SHEET_PACKING (Sanjeevni, session 296, 06-Oct-2026; F-756).

Builds marg_txt.py S490 from the medical PC's live marg_txt.py S480 (14b75012...) by anchored edits, each anchor exactly once.
The one fault: RE_ORDER_ITEM knew a packing only as N*M, so a pending-orders sheet carrying a gel (30GM) or a bottle (200ML) was
refused whole. The packing is now whatever stands in the packing's place -- and it must stand in the SAME column on every item
line of the sheet, so a line that does not fit is refused by name rather than read wrongly. Nothing else in the reader moves.

    python make_s490.py <marg_txt.py S480> <out marg_txt.py>
"""
import hashlib
import sys

FROM = "14b750120233e349d713d9de1d1edb7a"
EDITS = [
    ('VERSION = "S480"\n', 'VERSION = "S490"\n'),
    (r'(\S.*?) +(\d+\*\d+)\.? +([A-Z]{1,4}-\d+)', r'(\S.*?) +(\S+?)\.? +([A-Z]{1,4}-\d+)'),
    ("# an item line: two spaces, the name, ONE space or more, the packing's own shape (a stray full stop allowed), the entry number, the\n",
     "# an item line: two spaces, the name, ONE space or more, the packing (a stray full stop allowed), the entry number, the\n"
     "# S490 (F-756): the packing is whatever stands in its place -- 1*10, 30GM, 200ML, VAIL, 1 -- not only N*M (a sheet with a gel on it\n"
     "# was refused whole on 06-Oct-2026); it must stand in the same column on every item line of the sheet (order_rows checks).\n"),
    ("    tu = tp = tv = 0\n", "    tu = tp = tv = 0\n    pack_col = None                                             # S490: where this sheet's packing column starts\n"),
    ('                raise Refused("line %d: an item line with no supplier above it" % n)\n',
     '                raise Refused("line %d: an item line with no supplier above it" % n)\n'
     '            if pack_col is None:\n'
     '                pack_col = m.start(2)\n'
     '            elif m.start(2) != pack_col:                        # S490: read by its place; a line that does not fit is refused, never guessed\n'
     '                raise Refused("line %d: the packing does not stand in its column (col %d, the sheet\'s is %d)" % (n, m.start(2) + 1, pack_col + 1))\n'),
]


def main(src, dst):
    raw = open(src, "rb").read()
    got = hashlib.md5(raw).hexdigest()
    if got != FROM:
        raise SystemExit("!! %s is %s, not the FROM pin %s -- nothing built" % (src, got, FROM))
    t = raw.decode("utf-8")
    for old, new in EDITS:
        if t.count(old) != 1:
            raise SystemExit("!! anchor found %d times, wanted 1: %r" % (t.count(old), old[:60]))
        t = t.replace(old, new)
    out = t.encode("utf-8")
    open(dst, "wb").write(out)
    print("built %s  md5 %s  (%d -> %d bytes)" % (dst, hashlib.md5(out).hexdigest(), len(raw), len(out)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
