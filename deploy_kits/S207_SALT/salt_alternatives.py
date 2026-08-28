#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""salt_alternatives.py — same-salt alternatives, and the filters they must pass.

WHAT THIS IS FOR
    When a stockist has none of a brand, another brand of the same molecule
    will usually do. Marg's SALT WISE ITEM LIST is the only place that mapping
    exists.

WHY IT IS FILTERED HARD, AND WHY NOTHING IS AUTOMATIC
    The owner said to expect errors. There are more than "some". Measured on
    the 28-Aug-2026 export: the group headed `ETORICOXIB 60 + THIO 4` contains
    ARM SLING M UNISON, KNEE CAP UNISON, RIB BELT and a pain patch. Those rows
    are really in the file -- it is not a parsing artefact, and it was checked
    against the raw cells before saying so.

    Three filters, each measured:

      1. PAGE FURNITURE. The report reprints its header at every page break,
         so "S.No. DESCRIPTION" reads as a salt with 29 brands under it. 40
         such rows in this export. Same fault the purchase parser met.
      2. ONE PACK FORM. A group mixing 1*1 devices with 1*10 tablets is not a
         molecule. This removes 16 groups and 113 brands.
      3. SMALL. A 376-item pharmacy does not stock six brands of one molecule.
         Groups of 2 to 4 only; the 5s and 6s were the polluted ones.

    40 groups and 90 brands survive, and roughly one in ten of THOSE is still
    wrong -- `PELVIC TRACTION BELT XL` lists a wrist brace; `TELM 80 +
    HYDROCHL 12.5` lists a pantoprazole. So:

    **NOTHING HERE IS EVER OFFERED TO STAFF UNTIL THE DOCTOR HAS APPROVED THE
    PAIR.** These are medicines. A 90%-right list is an excellent starting
    point for one person to review once, and an unacceptable thing to put in
    front of a counter.
"""
import collections, re, sys

SKIP = re.compile(r"^(SANJEEVNI MEDICOS|SALT WISE ITEM LIST|S\.No\.|D\.L\.No|GSTIN|"
                  r"Phone\s*:|\d+[A-Z]?/\d+|Print HEALTH|LIST OF ITEMS)", re.I)
ITEM = re.compile(r"^(\d+)\s+(\S.*)$")
MIN_GROUP, MAX_GROUP = 2, 4


def pack_form(pk):
    pk = (pk or "").strip().rstrip(".")
    if pk in ("1*1", "1"):
        return "single"
    if re.match(r"^\d+\*\d+$", pk):
        return "strip"
    return "other"


def _txt(v):
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v).strip()


def parse(rows):
    """[[cell,...],...] -> {salt: [(item, packing), ...]}, raw and unfiltered."""
    salt, out, furniture = None, collections.OrderedDict(), 0
    for r in rows:
        r = list(r) + ["", ""]
        # cells arrive as floats from one reader and strings from another --
        # xlrd hands back 1.0 where openpyxl hands back "1". Coerce, never assume.
        c0, c1 = _txt(r[0]), _txt(r[1])
        if not c0:
            continue
        if SKIP.match(c0):
            furniture += 1
            salt = None            # a page break ends the group cleanly
            continue
        m = ITEM.match(c0)
        if m and c1:
            if salt:
                out.setdefault(salt, []).append((m.group(2).strip(), c1))
        elif not m:
            salt = c0
            out.setdefault(salt, [])
    return out, furniture


def usable(groups):
    """The groups a human may reasonably be asked to approve."""
    keep, rejected = {}, {}
    for salt, members in groups.items():
        names = sorted({n for n, _ in members})
        if len(names) < MIN_GROUP:
            continue
        why = None
        if len(names) > MAX_GROUP:
            why = "too many brands for one molecule in a shop this size"
        elif len({pack_form(p) for _, p in members}) != 1:
            why = "mixes pack forms — devices and tablets together"
        (rejected if why else keep)[salt] = (names, why)
    return keep, rejected


def selftest():
    n = [0]

    def ck(c, m):
        n[0] += 1
        if not c:
            print("check %d FAILED: %s" % (n[0], m)); raise AssertionError(m)

    rows = [
        ["ACECLOFENAC 100 + PCM", ""], ["1     ASTOFEN P", "1*10"],
        ["2     ZERODOL P", "1*10"],
        ["SANJEEVNI MEDICOS", ""], ["S.No. DESCRIPTION", "PACKING"],
        ["ETORICOXIB + PCM", ""], ["1     ORICOX P", "1*10"],
        ["2     NUCOXIA P", "1*10"],
        ["JUNK GROUP", ""], ["1     A TABLET", "1*10"], ["2     A DEVICE", "1*1"],
        ["BIG GROUP", ""]] + [["%d     B%d" % (i, i), "1*10"] for i in range(1, 7)]
    g, furn = parse(rows)
    ck(furn == 2, "the reprinted page header is counted as furniture, not salts")
    ck("S.No. DESCRIPTION" not in g, "and never becomes a salt")
    ck(g["ACECLOFENAC 100 + PCM"] and len(g["ACECLOFENAC 100 + PCM"]) == 2,
       "a real group survives the page break above it")
    ck(len(g["ETORICOXIB + PCM"]) == 2,
       "and a group AFTER a page break attaches to its own salt, not the header")
    keep, rej = usable(g)
    ck("ACECLOFENAC 100 + PCM" in keep and "ETORICOXIB + PCM" in keep,
       "two clean groups are keepable")
    ck("JUNK GROUP" in rej and "pack forms" in rej["JUNK GROUP"][1],
       "a group mixing a tablet and a device is rejected, and says why")
    ck("BIG GROUP" in rej and "too many" in rej["BIG GROUP"][1],
       "six brands of one molecule is rejected in a shop this size")
    ck(pack_form("1*10") == "strip" and pack_form("1*1") == "single"
       and pack_form("VAIL") == "other", "pack forms are read, not guessed")
    ck(pack_form("1*10.") == "strip", "a trailing full stop is tolerated")
    ck(_txt(1.0) == "1" and _txt(None) == "" and _txt(" X ") == "X",
       "a float cell becomes a plain string -- readers disagree about the type")
    g2, _ = parse([["A SALT", ""], [1.0, "1*10"], ["2     B", "1*10"]])
    ck(g2.get("A SALT") is not None, "a float serial number does not break the parse")
    print("SALT_ALTERNATIVES SELFTEST PASSED - %d checks OK" % n[0])
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 0)
