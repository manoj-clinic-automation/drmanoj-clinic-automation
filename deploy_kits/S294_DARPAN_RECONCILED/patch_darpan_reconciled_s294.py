#!/usr/bin/env python3
"""S294_DARPAN_RECONCILED -- Darpan's list only after reconciliation, and nothing on it
but the count-day figures.

The owner, 17-Sep-2026, holding the sheet he had printed from the desk ("Hand sheet for
Darpan" -- every difference, a paragraph of instructions, NIPRO and VINTAZ on it though
he had merged them, the ankle binders on it though their swap comes first):

  "check everything in documentation and come up with the proper output ... all these
  detailed description is not required here ... only after our total reconciliation --
  the stock they counted on that date, the Marg stock export on that date in adjacent
  columns, and the difference clearly marked. That was what was finalized."

Three files, anchored edits:

stock_app.py
  1. _tranche_pool -- the lines Darpan may be asked about, after reconciliation only:
     open lines; never a consumable (NIPRO syringes are used on patients); never a line
     whose Marg figure is below zero (a STOCK RECEIVE voucher, D398); medicines only from
     the real-loss and cannot-be-real lanes (bill checks and Marg checks are Amir's,
     cleanup is dead stock, surplus is never a loss);
     no list at all while any same-salt pair or orthotic swap family still waits for his word.
  2. _tranche_hold -- says in words what is holding the list back, so the cut button never
     reads "nothing left" while a swap decision is outstanding.
pad_receipt.py (Darpan's list only)
  3. columns: Shelf counted | Marg stock | Difference (bold), then REASON no. and REMARKS;
  4. the paragraph of instructions is gone; one line says what the two figures are and
     the date; the reason legend stays (he writes a number).
stock_desk.html
  5. the footer link "Hand sheet for Darpan (PDF)" becomes "All differences -- your copy
     (not for Darpan)", and a new link "Darpan's list -- cut and print it on the loss page" (where the cut button lives).

    python3 -B patch_darpan_reconciled_s294.py --app stock_app.py --receipt pad_receipt.py \
        --desk stock_desk.html [--app-from M --receipt-from M --desk-from M]
"""
from __future__ import print_function
import argparse
import hashlib
import io
import shutil
import sys

OLD_POOL = '''def _tranche_pool(d, kind):
    """The lines Darpan may still be asked about: open (no word, or the word is
    RECOUNT), not a consumable, orthotics only for kind 'ortho' and never for 'med'."""
    out = []
    for x in d["differences"]:
        w = x.get("word")
        if w and w["action"] != "RECOUNT":
            continue
        if x["lane"] == "consume":
            continue
        is_o = x["lane"] == "ortho" or _is_orthotic(x["item"])
        if (kind == "ortho") != is_o:
            continue
        out.append(x)
    return out
'''

NEW_POOL = '''def _tranche_decided(d):
    """S294: item -> True when the owner's word stands on it (RECOUNT is not a decision)."""
    return {x["item"]: bool(x.get("word")) and x["word"]["action"] != "RECOUNT" for x in d["differences"]}


def _tranche_held(d):
    """S294: (open same-salt pairs, open orthotic swap families). A pair or a family is open
    until EVERY member that differs carries a word of the owner's -- the swap comes first.
    "Darpan counts again" is a word here: it is how he sends a paired line on to Darpan."""
    spoken = {x["item"]: bool(x.get("word")) for x in d["differences"]}
    open_pairs = [p for p in (d.get("pairs") or [])
                  if not all(spoken.get(o["item"]) for o in (p.get("over") or []) + (p.get("short") or []))]
    open_fams = [f for f in (d.get("ortho_families") or []) if f.get("short") and f.get("over")
                 and any(not spoken.get(m["item"]) for m in f.get("members") or [] if m.get("state") == "diff")]
    return open_pairs, open_fams


def _tranche_pool(d, kind):
    """The lines Darpan may be asked about -- S294, ONLY AFTER RECONCILIATION. The owner,
    17-Sep-2026: "only after our total reconciliation -- the stock they counted on that
    date and the Marg stock export on that date in adjacent columns, and the difference
    clearly marked." Nothing at all while any same-salt pair or orthotic swap family still
    waits for his word. Then: open lines only; never a consumable; never a line whose Marg
    figure is below zero (a STOCK RECEIVE voucher, D398); medicines only from the real-loss
    and cannot-be-real lanes."""
    open_pairs, open_fams = _tranche_held(d)
    if open_pairs or open_fams:
        return []
    dec = _tranche_decided(d)
    out = []
    for x in d["differences"]:
        if dec.get(x["item"]):
            continue
        if x["lane"] == "consume":
            continue
        if (x.get("marg") or 0) < 0:
            continue
        is_o = x["lane"] == "ortho" or _is_orthotic(x["item"])
        if (kind == "ortho") != is_o:
            continue
        if not is_o and x["lane"] not in ("loss", "recount"):
            continue
        out.append(x)
    return out


def _tranche_hold(d, kind):
    """S294: what is holding Darpan's list back, in words; '' when nothing is."""
    open_pairs, open_fams = _tranche_held(d)
    parts = []
    if open_pairs:
        parts.append("%d same-salt pair%s" % (len(open_pairs), "" if len(open_pairs) == 1 else "s"))
    if open_fams:
        parts.append("%d orthotic swap famil%s (%s)" % (len(open_fams), "y" if len(open_fams) == 1 else "ies",
                                                         ", ".join(f["key"] for f in open_fams[:4])))
    if not parts:
        return ""
    return "Darpan's list comes after the swaps. Still waiting for your word on the desk: " + " and ".join(parts) + "."
'''

APP_EDITS = [
    (OLD_POOL, NEW_POOL),
    ('        return None, "Nothing left for Darpan on the %s side." % ("orthotics" if kind == "ortho" else "medicines")',
     '        return None, (_tranche_hold(d, kind) or "Nothing left for Darpan on the %s side." % ("orthotics" if kind == "ortho" else "medicines"))'),
]

RECEIPT_EDITS = [
    ('       ("Marg", _LL + 380, "r", 0), ("Shelf", _LL + 460, "r", 0), ("Difference", _LL + 550, "r", 0),',
     '       ("Shelf counted", _LL + 380, "r", 0), ("Marg stock", _LL + 460, "r", 0), ("Difference", _LL + 550, "r", 0),'),
    ('        vals = [str(i), r["item"], r.get("packing") or "-", _units(r["marg"], r["pack"]), _units(r["counted"], r["pack"]),\n'
     '                ("over " if (r["diff"] or 0) > 0 else "") + _units(r["diff"], r["pack"])]   # S293: a surplus says so\n'
     '        for (label, x, align, w), v in zip(_TC[:6], vals):\n'
     '            p.text(x, yy, _fit(v, 8.5, w) if w else _latin(v), 8.5, bold=(label == "Item"), align=align)',
     '        vals = [str(i), r["item"], r.get("packing") or "-", _units(r["counted"], r["pack"]), _units(r["marg"], r["pack"]),\n'
     '                ("over " if (r["diff"] or 0) > 0 else "") + _units(r["diff"], r["pack"])]   # S294: shelf, then Marg, then the gap\n'
     '        for (label, x, align, w), v in zip(_TC[:6], vals):\n'
     '            p.text(x, yy, _fit(v, 8.5, w) if w else _latin(v), 9.5 if label == "Difference" else 8.5,\n'
     '                   bold=(label in ("Item", "Difference")), align=align)'),
    ('    doc.line_text("Stock count #%d of %s - list given %s - %d items" % (cid, d.get("day") or "-", t.get("issued_text") or "-", len(d.get("rows") or [])), 9, gray=0.2)\n'
     '    doc.y -= 2\n'
     '    doc.para("These are the differences found at the stock count of %s. MARG is the computer\'s stock given just before the "\n'
     '             "count started; SHELF is what was counted that day; DIFFERENCE is the gap between them. For each line write the "\n'
     '             "REASON as a number from the legend, and anything you know in REMARKS (who, when, which bill). Do not count "\n'
     '             "again. Bring the sheet back; the next list comes after this one." % (d.get("day") or "-"), 8.5, 0.25)\n'
     '    doc.line_text("REASON legend:  " + "   ".join("%d = %s" % (n, en) for n, en, _hi in d.get("reasons") or []), 8.5, bold=True, gray=0.15)\n'
     '    doc.line_text("All three figures are from %s. \'short\' = less on the shelf than the computer said. 25s 4t = 25 strips and 4 tablets; pc = pieces." % (d.get("day") or "the count day"), 8, gray=0.4)',
     '    doc.line_text("Stock count of %s - shelf counted that day, Marg stock export of that day - list given %s - %d items"\n'
     '                  % (d.get("day") or "-", t.get("issued_text") or "-", len(d.get("rows") or [])), 9, gray=0.2)   # S294\n'
     '    doc.line_text("REASON:  " + "   ".join("%d = %s" % (n, en) for n, en, _hi in d.get("reasons") or []), 8.5, bold=True, gray=0.15)'),
]

DESK_EDITS = [
    ('<a href="\'+esc(D.links.diffs_pdf)+\'" target="_blank" rel="noopener">Hand sheet for Darpan (PDF)</a>',
     '<a href="\'+esc(D.links.diffs_pdf)+\'" target="_blank" rel="noopener">All differences — your copy (not for Darpan)</a>'
     '<a href="\'+esc(D.links.loss_page)+\'"><b>Darpan\\\'s list</b> — cut and print it on the loss page</a>'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_one(path, edits, from_md5, marker, dry):
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
            sys.exit("REFUSING: anchor not found exactly once in %s: %r" % (path, old[:80]))
        text = text.replace(old, new)
    new = text.encode("utf-8")
    if dry:
        print("would write %s : %s -> %s" % (path, cur, md5(new)))
        return md5(new)
    shutil.copy2(path, "%s.bak_S294_%s" % (path, cur[:8]))
    with io.open(path, "wb") as fh:
        fh.write(new)
    back = md5(io.open(path, "rb").read())
    print("patched %s : %s -> %s" % (path, cur, back))
    if back != md5(new):
        sys.exit(4)
    return back


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--desk", required=True)
    ap.add_argument("--app-from", default=None)
    ap.add_argument("--receipt-from", default=None)
    ap.add_argument("--desk-from", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    patch_one(a.app, APP_EDITS, a.app_from, "def _tranche_hold(d, kind):", a.dry_run)
    patch_one(a.receipt, RECEIPT_EDITS, a.receipt_from, "# S294: shelf, then Marg", a.dry_run)
    patch_one(a.desk, DESK_EDITS, a.desk_from, "your copy (not for Darpan)", a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
