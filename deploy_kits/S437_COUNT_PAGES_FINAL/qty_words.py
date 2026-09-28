#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  qty_words.py  ·  v1.2  ·  kit S437_COUNT_PAGES_FINAL (v1.1: S432_DESK_GROUP_FLOW; v1.0: S427_LOSS_DESK_RULINGS)  ·  Session 283 (Sanjeevni)  ·  D632 / F-642 / F-659
#
#  ONE NOMENCLATURE FOR EVERY QUANTITY THE PHARMACY SHOWS -- the owner, 27-Sep-2026: "we agreed ONE nomenclature,
#  strips and tablets, everywhere; this keeps recurring."  A strip item reads "3 strips + 4 tabs" (Hindi "3 patte +
#  4 goli"), never a decimal and never a count of tablets alone when a strip is whole; a non-strip item reads pcs /
#  bottles / tubes / vials (Hindi nag / botal / tube / vial) by its packing word.  THE WORD "UNIT(S)" NEVER LEAVES
#  THIS FILE FOR A SCREEN: code may carry `units` as an identifier, a person never reads it.
#
#  v1.1 (S432, 28-Sep-2026): words() CARRIES THE SIGN of a negative quantity -- "-24 pcs", Hindi "-24 nag". Marg holds a
#  negative stock on some items (PRIME CAST 4"/5", BELL CAST 5, ALCOXIB 120 ...) and the count statement printed the Marg
#  column through this function, so "-24 pcs" read "24 pcs" and the row looked impossible (Marg 24 · physical 0 · excess 24).
#  Every caller that shows a shortage or a gap already passes the absolute figure and puts its own verb ("short", "over",
#  "kam"); only a signed figure -- a Marg balance -- now shows its minus. signed() is unchanged in effect.
#
#  v1.2 (S437, 28-Sep-2026, the CCM bug): WHOLE-UNIT ITEMS. The owner: "CCM -- it writes goli where the packing is a bottle
#  of about 20 tablets." Marg's packing for CCM is 1*40 (tablets in the bottle) while Marg counts, sells and stocks it by the
#  BOTTLE: every figure the estate holds for it is a number of bottles, and this file read them as tablets ("3 tabs").
#  The desk's setting stock.whole_unit_items (loss_piles) names such items with their word -- "CCM = bottle" -- and hands the
#  map here through set_whole_units() (loss_piles.settings() and the S227 report composer both load it). For an item on the
#  list EVERY quantity is whole units in that word ("3 bottles", Hindi "3 botal"), never strips / tabs; the figure is never
#  divided by the packing count. An item off the list reads exactly as before. The words: bottle / jar / pc / tube / vial /
#  sachet (Hindi botal / jar / nag / tube / vial / pudiya).
#
#  stock_app._qw(units, pack) routes here (S427); loss_piles, the record PDF, Stock milaan and the staff block call
#  words() directly with the packing and the name, so a syrup says bottles and an injection says vials.
#
#  Pure functions, no database, no import from the estate: importable from /usr/bin/python3 and the venv alike.
# =============================================================================
import re

VERSION = "1.2"
KIT = "S437_COUNT_PAGES_FINAL"

_PACK_RE = re.compile(r"(\d+)\s*\*\s*(\d+)")

_EN = {"strip": ("strip", "strips"), "tab": ("tab", "tabs"), "pc": ("pc", "pcs"),
       "bottle": ("bottle", "bottles"), "tube": ("tube", "tubes"), "vial": ("vial", "vials"),
       "jar": ("jar", "jars"), "sachet": ("sachet", "sachets")}
_HI = {"strip": "patte", "tab": "goli", "pc": "nag", "bottle": "botal", "tube": "tube", "vial": "vial", "jar": "jar", "sachet": "pudiya"}
WHOLE_WORDS = ("bottle", "jar", "pc", "tube", "vial", "sachet")       # the words the owner may give a whole-unit item (S437)
_WHOLE = {}                                                            # name key -> word, loaded from the desk's setting


def name_key(name):
    """The key a whole-unit item is matched by: case, punctuation and spacing folded (item_alias.sale_key, verbatim)."""
    s = re.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return re.sub(r"\s+", " ", s).strip()


def parse_whole_units(entries):
    """The setting's entries ("CCM = bottle", "SOME SYP = bottle") -> {name key: word}; an entry without a known word reads 'pc'."""
    out = {}
    for e in entries or []:
        t = str(e or "").strip()
        if not t:
            continue
        if "=" in t:
            nm, w = t.split("=", 1)
        else:
            nm, w = t, "pc"
        w = str(w or "").strip().lower().rstrip("s") or "pc"
        w = {"piece": "pc", "bottl": "bottle", "vial": "vial", "tub": "tube", "sachet": "sachet", "jar": "jar"}.get(w, w)
        if w not in WHOLE_WORDS:
            w = "pc"
        k = name_key(nm)
        if k:
            out[k] = w
    return out


def set_whole_units(mapping):
    """Load the whole-unit map (a dict {name key: word}, or the setting's list of entries). Replaces the map; never raises."""
    global _WHOLE
    try:
        if isinstance(mapping, dict):
            _WHOLE = {name_key(k): (v if v in WHOLE_WORDS else "pc") for k, v in mapping.items() if name_key(k)}
        else:
            _WHOLE = parse_whole_units(mapping)
    except Exception:                                         # noqa: BLE001
        _WHOLE = {}
    return dict(_WHOLE)


def whole_units():
    return dict(_WHOLE)


def whole_unit_of(name):
    """The word of a whole-unit item ('bottle' for CCM), or None when the item is not on the list."""
    if not name or not _WHOLE:
        return None
    return _WHOLE.get(name_key(name))


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
    """strip | vial | bottle | tube | jar | sachet | pc -- what one whole piece of this item is called.
    S437: a whole-unit item answers with its own word, whatever its packing says."""
    w = whole_unit_of(name)
    if w:
        return w
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


def _unsigned(n, packing, unit_kind, lang, pack, name):
    w = whole_unit_of(name)
    if w:                                                     # S437: whole units in the item's own word, never divided by the packing
        return _w(w, n, lang)
    ps = pack_of(packing, pack)
    if ps > 1:
        st, tb = divmod(n, ps)
        if st and tb:
            return "%s + %s" % (_w("strip", st, lang), _w("tab", tb, lang))
        if tb:
            return _w("tab", tb, lang)
        return _w("strip", st, lang)
    return _w(kind_of(packing, unit_kind, name, ps), n, lang)


def words(qty, packing=None, unit_kind=None, lang="en", pack=None, name=None):
    """The quantity in the shop's own words: '3 strips + 4 tabs' / '4 tabs' / '12 pcs' / '2 bottles';
    Hindi (Roman): '3 patte + 4 goli' / '12 nag' / '2 botal'. A NEGATIVE quantity carries its minus (S432):
    '-24 pcs' / '-2 strips + 4 tabs' -- a Marg balance below zero reads as what it is. A shortage or a gap is
    passed as its absolute figure by every caller, which adds the verb (short / over / kam).
    S437: an item on the whole-unit list reads whole units in its word ('3 bottles' / '3 botal')."""
    try:
        v = int(round(float(qty or 0)))
    except (TypeError, ValueError):
        v = 0
    return ("-" if v < 0 else "") + _unsigned(abs(v), packing, unit_kind, lang, pack, name)


def signed(qty, packing=None, unit_kind=None, lang="en", pack=None, name=None):
    """'+3 strips' / '-3 strips + 4 tabs' / '0 strips'."""
    try:
        n = int(round(float(qty or 0)))
    except (TypeError, ValueError):
        n = 0
    return ("+" if n > 0 else ("-" if n < 0 else "")) + _unsigned(abs(n), packing, unit_kind, lang, pack, name)


def whole_word(packing=None, unit_kind=None, name=None, pack=None, lang="en", plural=True):
    """The word for one whole piece -- 'strips' / 'pcs' / 'bottles' (Hindi 'patte' / 'nag' / 'botal')."""
    k = kind_of(packing, unit_kind, name, pack)
    if lang == "hi":
        return _HI[k]
    return _EN[k][1 if plural else 0]


if __name__ == "__main__":
    for q, p in ((30, "1*10"), (34, "1*10"), (4, "1*10"), (0, "1*10"), (12, "1*1"), (2, "200ML"), (1, "30GM"), (3, "VAIL"), (-24, "1*1"), (-13, "1*10")):
        print("%5s %-6s -> %-20s %s" % (q, p, words(q, p), words(q, p, lang="hi")))
    set_whole_units(["CCM = bottle"])
    print("CCM 3 (1*40) ->", words(3, "1*40", pack=40, name="CCM"), "|", words(3, "1*40", pack=40, name="CCM", lang="hi"), "| off the list:", words(3, "1*40", pack=40, name="CCM2"))
