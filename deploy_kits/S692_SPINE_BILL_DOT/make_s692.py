#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s692.py -- kit S692_SPINE_BILL_DOT (01-Nov-2026, Sanjeevni session 375).

    python3 -B make_s692.py <root> <outdir>     reads <root>/finance/spine/marg_read.py, writes <outdir>/finance/spine/marg_read.py

WHY.  The spine gate (S331) failed every build from 29-Oct 09:40 to 1-Nov (the owner's ntfy shout of 31-Oct 08:05; the parent's note
parent_S371_1).  Read from the 1-Nov bundle and the archive in the device VM: one Shivaaz purchase bill of 26-Oct was keyed in Marg as
'3920.' -- a dot after the number.  Marg prints that field as TEXT, the reader's bill-number rule ('^[A-Za-z]{0,3}-?\\d+(\\.0)?$')
refused the row as UNCLASSIFIED, the line's Rs 4,907.40 left the sum, and every October purchase-line export since fails its own
witness (printed total HIGHER than the lines -- the returns witness cannot rescue it).  Nothing on a staff screen was wrong; the spine
stayed at its last good build.  Not the A004482 party sale (S679).

WHAT.  One file, marg_read.py, five anchored edits (each anchor must occur exactly once, else the builder refuses):
  1. READER_VERSION S524.1 -> S692.1 (the readings record which reader read them).
  2. billno(v), just above rows_of: a BILL number typed with a stray trailing dot is read as its digits ('3920.' -> '3920';
     'SF-123.' -> 'SF-123'); everything else exactly as textno gives it.  Bill numbers only -- a batch keeps every character (textno).
  3. the purchase-line row rule accepts the dotted shape ('\\.0' or '\\.').
  4. the purchase-line reader stores billno(...) for the bill.
  5. the purchase bill-wise reader stores billno(...) for the bill (both sides of the tie read the same number).
Nothing else changes: every other reader, every witness check, the gate, the readings' shape.
"""
import hashlib
import os
import sys

REL = "finance/spine/marg_read.py"
FROM = "b47a1d626c36e2706879c41e2c316a69"

EDITS = [
    # 1 -- the reader version
    ('READER_VERSION = "S524.1"\n',
     'READER_VERSION = "S692.1"\n'),
    # 2 -- billno, above rows_of
    ('\n\ndef rows_of(path):\n',
     '\n\ndef billno(v):\n'
     '    """A BILL number as text. S692 (1-Nov-2026): a number typed in Marg with a stray dot after it (\'3920.\') is read as its digits --\n'
     '    Marg prints the field as text then, the reader refused the row, and every purchase-line export of that month failed the spine\n'
     '    gate (29-Oct to 1-Nov). Bill numbers only; a batch keeps every character it has (textno)."""\n'
     '    v = textno(v)\n'
     '    return v[:-1] if re.match(r\'^[A-Za-z]{0,3}-?\\d+\\.$\', v) else v\n'
     '\n\ndef rows_of(path):\n'),
    # 3 -- the row rule
    ("        if (re.match(r'^[A-Za-z]{0,3}-?\\d+(\\.0)?$', c[0]) and c[1] and money[1] is not None) or glued:\n",
     "        if (re.match(r'^[A-Za-z]{0,3}-?\\d+(\\.0|\\.)?$', c[0]) and c[1] and money[1] is not None) or glued:   # S692: '3920.'\n"),
    # 4 -- the purchase-line reader's bill
    ("            bill, name = (glued.group(1), glued.group(2).strip()) if glued else (textno(c[0]), c[1])\n",
     "            bill, name = (glued.group(1), glued.group(2).strip()) if glued else (billno(c[0]), c[1])\n"),
    # 5 -- the bill-wise reader's bill
    ("            bills.append(dict(date=date, bill=textno(c[0]), supplier=re.sub(r'\\s+', ' ', c[1]).strip(),\n",
     "            bills.append(dict(date=date, bill=billno(c[0]), supplier=re.sub(r'\\s+', ' ', c[1]).strip(),\n"),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src_bytes):
    if md5(src_bytes) != FROM:
        raise SystemExit("REFUSED: %s is %s, not the FROM pin %s" % (REL, md5(src_bytes)[:8], FROM[:8]))
    s = src_bytes.decode("utf-8")
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %d occurs %d times (must be exactly once)" % (i, n))
        s = s.replace(old, new, 1)
    return s.encode("utf-8")


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root, outdir = sys.argv[1], sys.argv[2]
    with open(os.path.join(root, REL), "rb") as fh:
        out = build(fh.read())
    dst = os.path.join(outdir, REL)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(out)
    print("built %s %s -> %s (%d edits)" % (REL, FROM[:8], md5(out)[:8], len(EDITS)))


if __name__ == "__main__":
    main()
