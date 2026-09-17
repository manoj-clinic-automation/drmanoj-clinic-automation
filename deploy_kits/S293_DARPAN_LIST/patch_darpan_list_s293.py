#!/usr/bin/env python3
"""S293_DARPAN_LIST -- Darpan's paper list asks for the reason, not a recount.

The owner, 17-Sep-2026: "what is needed is the Marg 6-September stock and the physical
counted stock against each other so that the actual deficit is visible -- don't take
Marg stock of a later date; you have in your record the Marg record made available
just before the count started."

The list (S227 tranche, pad_receipt.render_tranche) already prints exactly those two
figures from count #1 -- Marg's stock given just before the count, and the shelf
counted that day -- with the difference. What was wrong is what it ASKED: "go to the
shelf and count it again, write the new count in RECOUNT". Eleven days later a
recount cannot be held against the count-day Marg figure. So, in pad_receipt.py only:

  1. the columns: Marg | Shelf | Difference, then REASON and a wide REMARKS box --
     the two RECOUNT boxes (strips, loose) are gone;
  2. the header says WRITE THE REASON, not COUNT AGAIN;
  3. the instruction says what the figures are (both from the count day) and asks
     for the reason number and remarks, and says plainly: do not count again;
  4. the signature line: Answered by / Date / Returned to;
  5. a surplus line reads "over 1s", not a bare "1s".

And in stock_amir.html one label: the typing board's "Note / recount" column is "Note".

No table, no route, no data changes. The service is restarted by the installer
because pad_receipt is a Python module the running app has already imported.

    python3 -B patch_darpan_list_s293.py --receipt pad_receipt.py --amir stock_amir.html \
        --receipt-from <md5> --amir-from <md5>
"""
from __future__ import print_function
import argparse
import hashlib
import io
import shutil
import sys

RECEIPT_EDITS = [
    ('_TC = [("#", _LL + 16, "r", 0), ("Item", _LL + 22, "l", 250), ("Pack", _LL + 300, "c", 44),\n'
     '       ("Marg", _LL + 380, "r", 0), ("Counted", _LL + 460, "r", 0), ("Difference", _LL + 550, "r", 0),\n'
     '       ("RECOUNT strips", _LL + 610, "c", 0), ("loose", _LL + 660, "c", 0), ("REASON", _LL + 706, "c", 0), ("REMARKS", _LL + 740, "l", 0)]\n'
     '_TBOX = [(_LL + 586, 46), (_LL + 636, 46), (_LL + 688, 38), (_LL + 732, _LR - _LL - 734)]',
     '_TC = [("#", _LL + 16, "r", 0), ("Item", _LL + 22, "l", 250), ("Pack", _LL + 300, "c", 44),\n'
     '       ("Marg", _LL + 380, "r", 0), ("Shelf", _LL + 460, "r", 0), ("Difference", _LL + 550, "r", 0),\n'
     '       ("REASON no.", _LL + 598, "c", 0), ("REMARKS", _LL + 632, "l", 0)]\n'
     '_TBOX = [(_LL + 574, 48), (_LL + 628, _LR - _LL - 630)]   # S293: reason + remarks; no recount boxes'),
    ('"LIST %d FOR DARPAN - %s - COUNT AGAIN" % (t["no"], kind)',
     '"LIST %d FOR DARPAN - %s - WRITE THE REASON" % (t["no"], kind)'),
    ('    doc.para("Go to the shelf for each item and count it again. Write the new count in RECOUNT (strips and loose) only if it "\n'
     '             "is different. Write the REASON as a number from the legend. Anything else in REMARKS. Bring the sheet back; "\n'
     '             "the next list comes after this one.", 8.5, 0.25)',
     '    doc.para("These are the differences found at the stock count of %s. MARG is the computer\'s stock given just before the "\n'
     '             "count started; SHELF is what was counted that day; DIFFERENCE is the gap between them. For each line write the "\n'
     '             "REASON as a number from the legend, and anything you know in REMARKS (who, when, which bill). Do not count "\n'
     '             "again. Bring the sheet back; the next list comes after this one." % (d.get("day") or "-"), 8.5, 0.25)'),
    ('    doc.line_text("Marg = the computer\'s stock. Counted = the shelf. \'short\' = less on the shelf than the computer says. 25s 4t = 25 strips and 4 tablets; pc = pieces.", 8, gray=0.4)',
     '    doc.line_text("All three figures are from %s. \'short\' = less on the shelf than the computer said. 25s 4t = 25 strips and 4 tablets; pc = pieces." % (d.get("day") or "the count day"), 8, gray=0.4)'),
    ('    doc.line_text("Counted again by: ______________________    Date: ____________    Returned to: ______________________", 9, gray=0.2)\n'
     '    return doc.finish("Count #%d - list %d for Darpan',
     '    doc.line_text("Answered by: ______________________    Date: ____________    Returned to: ______________________", 9, gray=0.2)\n'
     '    return doc.finish("Count #%d - list %d for Darpan'),
]

RECEIPT_EDITS.append((
    '        vals = [str(i), r["item"], r.get("packing") or "-", _units(r["marg"], r["pack"]), _units(r["counted"], r["pack"]), _units(r["diff"], r["pack"])]',
    '        vals = [str(i), r["item"], r.get("packing") or "-", _units(r["marg"], r["pack"]), _units(r["counted"], r["pack"]),\n'
    '                ("over " if (r["diff"] or 0) > 0 else "") + _units(r["diff"], r["pack"])]   # S293: a surplus says so'))

AMIR_EDITS = [
    ('<th>Reason</th><th>Note / recount</th></tr>', '<th>Reason</th><th>Note</th></tr>'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_one(path, edits, from_md5, tag, marker, dry):
    raw = io.open(path, "rb").read()
    cur = md5(raw)
    text = raw.decode("utf-8")
    if marker in text:
        print("ALREADY PATCHED: %s is %s" % (path, cur))
        return cur
    if from_md5 and cur != from_md5.lower():
        sys.exit("REFUSING: %s is %s, expected %s" % (path, cur, from_md5))
    for old, new in edits:
        if text.count(old) != 1:
            sys.exit("REFUSING: anchor not found exactly once in %s: %r" % (path, old[:70]))
        text = text.replace(old, new)
    new = text.encode("utf-8")
    if dry:
        print("would write %s : %s -> %s" % (path, cur, md5(new)))
        return md5(new)
    shutil.copy2(path, "%s.bak_%s_%s" % (path, tag, cur[:8]))
    with io.open(path, "wb") as fh:
        fh.write(new)
    back = md5(io.open(path, "rb").read())
    print("patched %s : %s -> %s" % (path, cur, back))
    if back != md5(new):
        sys.exit(4)
    return back


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--amir", required=True)
    ap.add_argument("--receipt-from", default=None)
    ap.add_argument("--amir-from", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    patch_one(a.receipt, RECEIPT_EDITS, a.receipt_from, "S293", "WRITE THE REASON", a.dry_run)
    patch_one(a.amir, AMIR_EDITS, a.amir_from, "S293", "<th>Reason</th><th>Note</th></tr>", a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
