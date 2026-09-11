#!/usr/bin/python3
"""
packmap.py -- the pack-size dictionary, and the conflicts inside it.

WHY THIS EXISTS AND WHY IT IS FIRST

    Every quantity in this system is printed as `packs:loose`. Turning that
    into a number requires a pack size:  '2:3' with 1*10 is 23 units, with
    1*15 it is 33. Get the pack size wrong and the ledger is wrong by a
    multiple, not by a rounding.

    So the pack size cannot be assumed, taken from whichever source is handy,
    or defaulted to 10. It has to be ONE agreed number per item, and where
    the sources disagree that disagreement is a finding to be reported --
    never silently resolved by picking a winner.

THE OWNER'S TAXONOMY (his words, S206)
    "tablet or capsule come in strips commonly 10 tabs each, maybe 15 or
     rarely less or more"
    So `1*N` means a STRIP of N. Anything else -- 30GM, 200ML, VAIL, a bare
    number -- is a WHOLE unit counted one at a time. The class is decided by
    the PACKING, never by Marg's unit label: 55 of 378 items carry a label
    that contradicts their packing ('ARM SLING L UNISON' labelled 'TAB.').
"""

import re
import collections

PACK_RE = re.compile(r"^\s*(\d+)\s*\*\s*(\d+)\s*\.?\s*$")


def norm(s):
    """The one match key used everywhere. Case, inner spacing, trailing dots."""
    s = re.sub(r"\s+", " ", (s or "").upper()).strip()
    return re.sub(r"[.\s]+$", "", s)


def pack_size(packing):
    """'1*10' -> 10.  '30GM' -> None (whole unit).  '1*1' -> None."""
    m = PACK_RE.match(str(packing or ""))
    if not m:
        return None
    n = int(m.group(1)) * int(m.group(2))
    # '1*1' is a strip of one, which is the same thing as a whole unit.
    # Calling it a strip would print '6 strips' for six injections.
    return n if n > 1 else None


def build(observations):
    """
    observations: iterable of (item_name, packing_text, source_tag).
    Returns (packmap, conflicts).

    packmap[key] = {'size', 'packing', 'whole', 'sources', 'agreed', 'item'}

    A conflict is REPORTED, never resolved. Which source to trust is the
    owner's call, and the sizes involved must be visible to make it.
    """
    seen = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    display = {}
    for name, packing, tag in observations:
        k = norm(name)
        if not k:
            continue
        display.setdefault(k, re.sub(r"\s+", " ", (name or "").strip()))
        p = re.sub(r"\s+", "", str(packing or "").strip()).upper().rstrip(".")
        if not p:
            continue
        seen[k][p][tag] += 1

    packmap, conflicts = {}, []
    for k, packs in seen.items():
        ranked = sorted(packs.items(),
                        key=lambda kv: (-sum(kv[1].values()), -len(kv[1]), kv[0]))
        best, best_src = ranked[0]
        sizes = set(pack_size(p) for p in packs)
        agreed = len(sizes) <= 1
        if not agreed:
            conflicts.append({
                "key": k, "item": display[k],
                "variants": [{"packing": p, "size": pack_size(p),
                              "lines": sum(t.values()), "sources": dict(t)}
                             for p, t in ranked],
                "chosen": best, "chosen_size": pack_size(best)})
        packmap[k] = {"size": pack_size(best), "packing": best,
                      "whole": pack_size(best) is None,
                      "sources": dict(best_src), "agreed": agreed,
                      "item": display[k]}
    return packmap, conflicts


def units(packs, loose, size):
    """packs:loose -> base units. Whole-unit items have size None: loose only."""
    if size:
        return (packs or 0) * size + (loose or 0)
    return (loose or 0)


def describe(u, size, short=False):
    """
    Base units -> the owner's taxonomy.
      279 at 1*10  -> '27 strips + 9'
     -132 at 1*10  -> 'short 13 strips + 2'
        6 whole    -> '6'
    """
    if u is None:
        return "?"
    u = int(round(u))
    if not size:
        return "%d" % u
    neg = u < 0
    st, lo = divmod(abs(u), size)
    if short:
        core = "%ds" % st if not lo else "%ds+%d" % (st, lo)
    else:
        core = "%d strip%s" % (st, "" if st == 1 else "s")
        if lo:
            core += " + %d" % lo
        if st == 0:
            core = "%d" % lo
    return ("short " + core) if neg else core
