#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sheet_shapes_s906.py -- kit S906 (the parent, S493, 20-Nov-2026): what the Call Sheet's differing rows ARE.

Reads the box's replay output and the inbox workbook of ONE run (both on the box; neither leaves it) and prints:
  * the Call Sheet's header row (the row with the most text cells among the first 6) -- the sheet's own words;
  * for every differing row: the row number and, for the columns that carry no patient identity (the header decides: not
    a name, mobile, phone, patient, UID, key, id column), the two values; identity columns are shown as lengths only.
Never a name, a mobile or an ID.
    python3 sheet_shapes_s906.py <box xlsx> <inbox xlsx>
"""
import re
import sys

import openpyxl

IDENT = re.compile(r"(?i)name|mobile|phone|patient|uid|key|_id\b|^id$|clinic")


def main(a, b):
    wa, wb = openpyxl.load_workbook(a), openpyxl.load_workbook(b)
    xa, xb = wa["Call Sheet"], wb["Call Sheet"]
    cols = max(xa.max_column, xb.max_column)
    best, hdr = 0, 1
    for i in range(1, 7):
        n = sum(1 for j in range(1, cols + 1) if isinstance(xa.cell(i, j).value, str))
        if n > best:
            best, hdr = n, i
    heads = {j: str(xa.cell(hdr, j).value or "col%d" % j) for j in range(1, cols + 1)}
    print("header row %d: %s" % (hdr, " | ".join("%d=%s" % (j, heads[j][:22]) for j in range(1, cols + 1))))
    print("rows: box %d, inbox %d" % (xa.max_row, xb.max_row))
    shown = 0
    for i in range(1, max(xa.max_row, xb.max_row) + 1):
        ra = [xa.cell(i, j).value for j in range(1, cols + 1)]
        rb = [xb.cell(i, j).value for j in range(1, cols + 1)]
        if ra == rb:
            continue
        parts = []
        for j in range(1, cols + 1):
            va, vb = ra[j - 1], rb[j - 1]
            if va == vb:
                continue
            if IDENT.search(heads[j]):
                parts.append("%s: len %s/%s" % (heads[j][:14], len(str(va)) if va is not None else "-", len(str(vb)) if vb is not None else "-"))
            else:
                parts.append("%s: %r / %r" % (heads[j][:14], (str(va)[:60] if va is not None else None), (str(vb)[:60] if vb is not None else None)))
        print("r%d  %s" % (i, "  ||  ".join(parts)))
        shown += 1
        if shown >= 40:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
