#!/usr/bin/python3
"""
resolve.py -- turn what the SALE report prints into the item the shop stocks.

The sale report does not print item names the way the item master holds them.
Two faults, both measured on the real year, both of which strand stock:

TRAP A -- THE 20-CHARACTER CAP
    The sale report truncates the item name at 20 characters. 'HARD COLLAR
    ADJ L HOSPIK' is rung up as 'HARD COLLAR ADJ L HO'. The truncated form
    exists in no item master, so its sales attach to a phantom code, and the
    real item shows purchases with no sales -- reading as dead stock. 11 codes,
    the largest carrying 574 units.

    WHERE THE TRUNCATION IS AMBIGUOUS IT IS NOT GUESSED. Six sizes of
    'L S BELT CONT GRAY UNISON _' all cut to the same 20 characters. Those
    sales are pooled at the family and the size is reported as unrecoverable,
    because it is: the report did not record it. Inventing a size to make a
    line balance would be the worst possible outcome here.

TRAP B -- '1 *** PRIME CAST 5" 1*1'
    Five lines glue four fields into the name cell: the line's serial number,
    a '***' marker, the item name, and the packing. The real quantity is in
    the qty column ('2.0'), so the '1' is NOT a quantity. Left alone the name
    matches nothing.

RULE OF THE FILE: every rewrite is recorded with its reason, and a name that
cannot be resolved with certainty is passed through unchanged and reported --
never bent to fit.
"""
import re

GLUED_RE = re.compile(r'^\s*\d+\s*\*\*\*\s*(.+?)\s+(\d+\s*\*\s*\d+|\d+(?:\.\d+)?\s*'
                      r'(?:GM|ML|MG|MCG|G|KG|L)|VAIL|VIAL)\s*\.?\s*$', re.I)
TRUNC_LEN = 20


def unglue(name):
    """'1 *** PRIME CAST 5\" 1*1' -> ('PRIME CAST 5\"', '1*1'). Else (name, None)."""
    m = GLUED_RE.match(name or "")
    if not m:
        return (name, None)
    return (m.group(1).strip(), re.sub(r"\s+", "", m.group(2)))


def build_map(sale_keys, master_keys):
    """
    Returns (mapping, ambiguous, unresolved).
      mapping[sale_key]   = master_key            -- safe to rewrite
      ambiguous[sale_key] = [master_key, ...]     -- family known, size is not
      unresolved          = [sale_key, ...]       -- no master name at all
    Only keys of EXACTLY the cap length are candidates: a shorter name was not
    truncated, and rewriting it would merge two real products.
    """
    master = set(master_keys)
    # THE TEST IS EXACT, NOT LENGTH-BASED. Marg cuts at 20 characters and the
    # cut can land ON a space, which then gets stripped: 'DISPO SYRINGE NIPRO
    # 3ML' cuts to 'DISPO SYRINGE NIPRO ' and arrives as 19 characters. A
    # `len(k) == 20` test misses every one of those -- and it missed the
    # largest of them, 574 units. So the candidate must reproduce the sale
    # name by being truncated itself: cut the MASTER name and compare.
    cut = {}
    for m in master:
        if len(m) > TRUNC_LEN:
            cut.setdefault(m[:TRUNC_LEN].strip(), []).append(m)
    mapping, ambiguous, unresolved = {}, {}, []
    for k in sale_keys:
        if k in master:
            continue
        fam = sorted(cut.get(k, []))
        if len(fam) == 1:
            mapping[k] = fam[0]
        elif fam:
            ambiguous[k] = fam
        else:
            unresolved.append(k)
    return mapping, ambiguous, unresolved
