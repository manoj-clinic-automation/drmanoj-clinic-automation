#!/usr/bin/python3
"""
units.py — say quantities the way the shop says them.

WHY THIS EXISTS
    Every figure in this project was being reported as a bare number: "TYRO BR
    279". That is meaningless on a shelf. 279 WHAT? The answer is 27 strips and
    9 loose tablets, and if you ask someone to count "279" they will either
    count tablets one by one or guess.

    This matters most on the verification form. Darpan should be asked in
    MARG'S OWN FORMAT — strips and loose, entered separately — because that is
    what the screen in front of him shows and it needs no mental arithmetic.
    Asking for a single total invites a conversion error on every single line.

MARG'S VOCABULARY, measured on the 26-Aug closing stock (378 items):
    STRI 202 · ITEM 57 · TAB. 56 · INJ 23 · BOX 11 · BTL 9 · PCS 6 · TUBE 4
    SACH/PKT/SYP/BAND/TUB/PATC 1 each

    Two shapes, and only two:
      strip-packed   packing '1*N' with N>1   ->  "27 strips + 9 tabs (279)"
      whole units    packing '1*1' or blank   ->  "83 pcs"

⚠ MARG'S UNIT LABEL IS NOT TRUSTWORTHY ON NON-PHARMA ITEMS.
    41 items carry unit 'TAB.' against packing '1*1' — including
    'ARM SLING L UNISON' and 'HARD COLLAR M BODYAID'. An arm sling is not a
    tablet. The label is whatever was typed when the item was created.
    So: derive the SHAPE from the packing (which is structural), and show
    Marg's label only as a hint. Never compute on the label.
"""

import re

PACK_RE = re.compile(r"(\d+)\s*\*\s*(\d+)\s*\.?\s*$")

# Marg labels that are already a countable whole thing.
WHOLE = {"ITEM", "PCS", "BOX", "BTL", "TUBE", "TUB", "SACH", "PKT",
         "SYP", "BAND", "PATC", "INJ", "VAIL", "NOS"}

# What one strip of this pack size is called, for the counter's benefit.
def inner_noun(unit_label, pack_size):
    u = (unit_label or "").strip().upper().rstrip(".")
    if u in ("STRI", "STR"):
        return "tabs"
    if u == "SACH":
        return "sachets"
    if u == "INJ":
        return "inj"
    return "loose"


def pack_size(packing):
    m = PACK_RE.search((packing or "").strip())
    if not m:
        return None
    try:
        return int(m.group(2))
    except ValueError:
        return None


def is_strip_packed(packing):
    n = pack_size(packing)
    return bool(n and n > 1)


def outer_noun(unit_label, packing):
    """What the counter physically picks up: strips, boxes, pieces…"""
    u = (unit_label or "").strip().upper().rstrip(".")
    if is_strip_packed(packing):
        return "strips"
    if u in WHOLE:
        return {"PCS": "pcs", "ITEM": "pcs", "BOX": "boxes", "BTL": "bottles",
                "TUBE": "tubes", "TUB": "tubes", "SACH": "sachets",
                "PKT": "packets", "SYP": "bottles", "BAND": "rolls",
                "PATC": "patches", "INJ": "vials", "VAIL": "vials"}.get(u, u.lower())
    return "pcs"


def describe(units, packing, unit_label):
    """
    A quantity, said out loud. `units` is the base count (tablets, or pieces).
        describe(279, '1*10', 'STRI')  -> '27 strips + 9 tabs  (279 tabs)'
        describe(-83, '1*1',  'PCS')   -> '-83 pcs'
    """
    if units is None:
        return "?"
    n = pack_size(packing)
    if not is_strip_packed(packing):
        return "%g %s" % (units, outer_noun(unit_label, packing))
    neg = units < 0
    a = abs(units)
    strips, loose = divmod(int(a), n)
    inner = inner_noun(unit_label, n)
    parts = []
    if strips:
        parts.append("%d strip%s" % (strips, "" if strips == 1 else "s"))
    if loose or not strips:
        parts.append("%d %s" % (loose, inner))
    core = " + ".join(parts)
    if neg:
        core = "short " + core
    return "%s  (%g %s)" % (core, units, inner)


def count_prompt(packing, unit_label):
    """
    What to put in front of a person counting this item. Two boxes for a
    strip-packed medicine, one for anything else — matching Marg's own
    `strips:loose` display so nothing has to be converted by hand.
    """
    if is_strip_packed(packing):
        n = pack_size(packing)
        return {"boxes": 2,
                "labels": ["Full strips", "Loose %s" % inner_noun(unit_label, n)],
                "hint": "1 strip = %d %s" % (n, inner_noun(unit_label, n)),
                "combine": "strips x %d + loose" % n}
    return {"boxes": 1,
            "labels": [outer_noun(unit_label, packing).capitalize()],
            "hint": "count whole %s" % outer_noun(unit_label, packing),
            "combine": "as entered"}


def label_is_suspect(packing, unit_label):
    """
    True when Marg's unit label contradicts the packing — the arm-sling case.
    Structural packing wins; the label is only ever a hint.
    """
    u = (unit_label or "").strip().upper().rstrip(".")
    if not u:
        return True
    if u in ("STRI", "STR") and not is_strip_packed(packing):
        return True
    if u == "TAB" and not is_strip_packed(packing):
        return True
    return False
