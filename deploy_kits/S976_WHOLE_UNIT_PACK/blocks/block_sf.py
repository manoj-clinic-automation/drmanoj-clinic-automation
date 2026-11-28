

# ---- S976 (28-Nov-2026, Sanjeevni session 543, kit S976_WHOLE_UNIT_PACK; F-1742) ---------------------------------------------------------
#  A whole-unit item -- on the desk's list stock.whole_unit_items ("CCM = bottle") -- is counted, sold and stocked by the WHOLE piece:
#  Marg prints its figures in bottles and every count of it is a number of bottles. Its packing (CCM 1*40: tablets IN the bottle) is not a
#  pack to divide by. pack_of() answered 40 for CCM, so the stock record read Marg's bottles as tablets (0:2) and Darpan's count screen
#  stored 40 per bottle. Now a whole-unit item's pack is 1 everywhere this reader is used (the record, shelf_figure, stock_check);
#  every other item is exactly as before. The list is read from the database on each call and handed to qty_words, so every word agrees.
KIT_S976 = "S976_WHOLE_UNIT_PACK"
_S976 = {"raw": None, "map": {}}


def _s976_whole(con, name):
    """The whole-unit word of an item ('bottle' for CCM) from the desk's setting stock.whole_unit_items, else None. Never raises."""
    if not name or con is None:
        return None
    try:
        r = con.execute("SELECT value FROM setting WHERE key='stock.whole_unit_items'").fetchone()
        raw = str((r[0] if r else "") or "[]")
        QW = _qw()
        if raw != _S976["raw"]:
            lst = json.loads(raw)
            lst = lst if isinstance(lst, list) else []
            QW.set_whole_units(lst)                           # the words (qty_words) read the same list
            _S976.update(raw=raw, map=QW.parse_whole_units(lst))
        return _S976["map"].get(QW.name_key(name))
    except Exception:                                         # noqa: BLE001 -- no setting table, a bad value: the item reads as before
        return None


_pack_of_before_s976 = pack_of


def pack_of(con, sp, name, ctx=None):                         # noqa: F811 -- S976: a whole-unit item's pack is 1
    pk, packing, src = _pack_of_before_s976(con, sp, name, ctx)
    if int(pk or 1) > 1 and _s976_whole(con, name):
        return 1, packing, src
    return pk, packing, src
# ---- S976 end ---------------------------------------------------------------------------------------------------------------------------


