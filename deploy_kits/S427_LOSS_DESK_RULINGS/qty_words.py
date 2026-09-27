#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  qty_words.py  ·  v1.0  ·  kit S427_LOSS_DESK_RULINGS  ·  Session 283 (Sanjeevni)  ·  D632 / F-642
#
#  ONE NOMENCLATURE FOR EVERY QUANTITY THE PHARMACY SHOWS -- the owner, 27-Sep-2026: "we agreed ONE nomenclature,
#  strips and tablets, everywhere; this keeps recurring."  A strip item reads "3 strips + 4 tabs" (Hindi "3 patte +
#  4 goli"), never a decimal and never a count of tablets alone when a strip is whole; a non-strip item reads pcs /
#  bottles / tubes / vials (Hindi nag / botal / tube / vial) by its packing word.  THE WORD "UNIT(S)" NEVER LEAVES
#  THIS FILE FOR A SCREEN: code may carry `units` as an identifier, a person never reads it.
#
#  stock_app._qw(units, pack) routes here (S427); loss_piles, the record PDF, Stock milaan and the staff block call
#  words() directly with the packing and the name, so a syrup says bottles and an injection says vials.
#
#  Pure functions, no database, no import from the estate: importable from /usr/bin/python3 and the venv alike.
# =============================================================================
import re

VERSION = "1.0"
KIT = "S427_LOSS_DESK_RULINGS"

_PACK_RE = re.compile(r"(\d+)\s*\*\s*(\d+)")

_EN = {"strip": ("strip", "strips"), "tab": ("tab", "tabs"), "pc": ("pc", "pcs"),
       "bottle": ("bottle", "bottles"), "tube": ("tube", "tubes"), "vial": ("vial", "vials")}
_HI = {"strip": "patte", "tab": "goli", "pc": "nag", "bottle": "botal", "tube": "tube", "vial": "vial"}


def pack_of(packing=None, pack=None):
    """Tablets in a strip: the given pack size first, else read from the packing ('1*10' -> 10); 1 otherwise."""
    try:
        if pack is not None and int(pack) > 1:
            return int(pack)
    except (TypeError, ValueError):
        pass
    m = _PACK_RE.search(str(packing or ""))
    if m:
        n = int(m.group(2))
        return n if 0 < n <= 1000 else 1
    return 1


def kind_of(packing=None, unit_kind=None, name=None, pack=None):
    """strip | vial | bottle | tube | pc -- what one whole piece of this item is called."""
    if pack_of(packing, pack) > 1:
        return "strip"
    p = str(packing or "").upper()
    n = " " + str(name or "").upper() + " "
    if "VAIL" in p or "VIAL" in p or " INJ" in n or " INJECTION" in n:
        return "vial"
    if "ML" in p:
        return "bottle"
    if "GM" in p or " GEL " in n or " OINT" in n or " CREAM " in n:
        return "tube"
    return "pc"


def _w(kind, n, lang):
    if lang == "hi":
        return "%d %s" % (n, _HI[kind])
    one, many = _EN[kind]
    return "%d %s" % (n, one if n == 1 else many)


def words(qty, packing=None, unit_kind=None, lang="en", pack=None, name=None):
    """The quantity in the shop's own words, unsigned: '3 strips + 4 tabs' / '4 tabs' / '12 pcs' / '2 bottles';
    Hindi (Roman): '3 patte + 4 goli' / '12 nag' / '2 botal'. The caller adds the sign or the verb."""
    try:
        n = abs(int(round(float(qty or 0))))
    except (TypeError, ValueError):
        n = 0
    ps = pack_of(packing, pack)
    if ps > 1:
        st, tb = divmod(n, ps)
        if st and tb:
            return "%s + %s" % (_w("strip", st, lang), _w("tab", tb, lang))
        if tb:
            return _w("tab", tb, lang)
        return _w("strip", st, lang)
    return _w(kind_of(packing, unit_kind, name, ps), n, lang)


def signed(qty, packing=None, unit_kind=None, lang="en", pack=None, name=None):
    """'+3 strips' / '-3 strips + 4 tabs' / '0 strips'."""
    try:
        n = int(round(float(qty or 0)))
    except (TypeError, ValueError):
        n = 0
    return ("+" if n > 0 else ("-" if n < 0 else "")) + words(n, packing, unit_kind, lang, pack, name)


def whole_word(packing=None, unit_kind=None, name=None, pack=None, lang="en", plural=True):
    """The word for one whole piece -- 'strips' / 'pcs' / 'bottles' (Hindi 'patte' / 'nag' / 'botal')."""
    k = kind_of(packing, unit_kind, name, pack)
    if lang == "hi":
        return _HI[k]
    return _EN[k][1 if plural else 0]


if __name__ == "__main__":
    for q, p in ((30, "1*10"), (34, "1*10"), (4, "1*10"), (0, "1*10"), (12, "1*1"), (2, "200ML"), (1, "30GM"), (3, "VAIL")):
        print("%5s %-6s -> %-20s %s" % (q, p, words(q, p), words(q, p, lang="hi")))
