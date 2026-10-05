#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s483.py -- kit S483_SPINE_READS_TEXT (F-734, F-735).

/root/finance/spine/marg_read.py is BUILT FROM THE LIVE BYTES (the post-S482 file, 099d6213) by anchored edits: each anchor must occur
exactly once, else the build stops and nothing is written. Nothing here opens a database or the network.

    python3 -B make_s483.py --spine /root/finance/spine --out DIR        -> DIR/marg_read.py

E.1  read_purchase_lines: a row whose non-empty cells are exactly one, and that cell is a date, is a DATE row -- wherever the cell sits.
E.2  read_grouped_list:   a heading's other cells are each empty, zero, or ONE short code; the code is kept beside the items as
                          data['code'] = {group: code} (present only when a heading carried one).
"""
import argparse
import hashlib
import io
import os
import sys

KIT = "S483_SPINE_READS_TEXT"
FROM = "099d621315f3bf9297a9b4626a5caee5"


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(name, src, pairs):
    """Anchored edits: every OLD must occur exactly once in what the edits before it left."""
    for i, (old, new) in enumerate(pairs, 1):
        n = src.count(old)
        if n != 1:
            raise SystemExit("!! %s: anchor %d occurs %d times, not once -- nothing built (%r)" % (name, i, n, old[:70]))
        src = src.replace(old, new)
    return src


def build_marg_read(src):
    return edit("marg_read.py", src, [
        # ---- E.1 (F-734): the DATE row of the BILL/ITEM WISE statement
        ('        if RE_DATE.match(c[0]) and not any(c[1:]):\n'
         '            R.cls("DATE")\n'
         '            date = iso(c[0])\n'
         '            continue\n'
         '        money = [num(c[7]), num(c[11])]\n',
         '        # S483 (F-734): a date-only row is a DATE wherever its one cell sits. Marg\'s own Excel has the day in column 0; the sheet\n'
         '        # the text cutter makes (S480) has it in column 1 -- the date is wider than the BILL head, and a word goes to the column\n'
         '        # in which it ends -- and was read as a supplier heading, so no line of that sheet carried a date.\n'
         '        only = [x for x in c if x]\n'
         '        if len(only) == 1 and RE_DATE.match(only[0]):\n'
         '            R.cls("DATE")\n'
         '            date = iso(only[0])\n'
         '            continue\n'
         '        money = [num(c[7]), num(c[11])]\n'),
        # ---- E.2 (F-735): the HEADING row of the salt / category list
        ('        if c0 and all((not x) or num(x) == 0 for x in rest):\n'
         '            R.cls("HEADING")\n'
         '            if group is not None and want == 1:\n'
         '                empty.append(group)\n'
         '            group, want = c0, 1\n'
         '            continue\n',
         '        # S483 (F-735): Marg prints a category\'s own code in a cell of its heading row (\'OTHERS | 0.0 | D98\'). A heading\'s other\n'
         '        # cells are each empty, zero, or ONE short code -- letters and digits with a letter among them, no spaces, at most 6\n'
         '        # characters, at most one such cell in the row. A row with a rate or a packing beside its name is still not a heading.\n'
         '        hcode = [x for x in rest if x and num(x) != 0]\n'
         "        if c0 and (not hcode or (len(hcode) == 1 and re.match(r'^(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{1,6}$', hcode[0]))):\n"
         '            R.cls("HEADING")\n'
         '            if group is not None and want == 1:\n'
         '                empty.append(group)\n'
         '            group, want = c0, 1\n'
         '            if hcode:\n'
         '                R.data.setdefault("code", {})[c0] = hcode[0]   # information: the group\'s code; nothing reads it yet\n'
         '            continue\n'),
        ('            not [d for d in items if d["group"].upper() in (SHOP, "SALT WISE ITEM LIST", "CATEGORY WISE ITEM LIST")])\n'
         '    R.check("at least one item read", bool(items))\n'
         '    R.data = dict(items=items)\n'
         '    return R\n',
         '            not [d for d in items if d["group"].upper() in (SHOP, "SALT WISE ITEM LIST", "CATEGORY WISE ITEM LIST")])\n'
         '    R.check("at least one item read", bool(items))\n'
         '    R.data = dict(items=items, **R.data)   # S483: with "code" {group: code} when a heading carried one, else items alone\n'
         '    return R\n'),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", default="/root/finance/spine")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with io.open(os.path.join(a.spine, "marg_read.py"), "rb") as fh:
        raw = fh.read()
    if md5(raw) != FROM:
        raise SystemExit("!! marg_read.py is %s, not its FROM pin %s -- someone changed it since the brief; nothing built" % (md5(raw), FROM))
    out = build_marg_read(raw.decode("utf-8")).encode("utf-8")
    os.makedirs(a.out, exist_ok=True)
    with io.open(os.path.join(a.out, "marg_read.py"), "wb") as fh:
        fh.write(out)
    print("built marg_read.py  %s -> %s  (%d bytes)" % (FROM[:8], md5(out)[:8], len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
