

# ---- S975 (28-Nov-2026, Sanjeevni session 542, kit S975_STOCKCHECK_V10; F-1738) -----------------------------------------------------------
#  A fresh count that finds MORE on the shelf than in Marg is never a loss and never 'today's gap -- waits for your call' (CCM, 28-11:
#  shelf 1:0 against Marg 0:0 was told red in box 3 while the count list said 'noted, never a loss'). The whole-item verdict 'surplus'
#  says so; a claim or an ask on it is handled as a fresh gap was (voucher_inquiry closes only on settled / held, as before).
VERSION = "1.5"
KIT_S975 = "S975_STOCKCHECK_V10"
V_WORD = dict(V_WORD, surplus="more than Marg — noted")
_whole_item_before_s975 = whole_item


def whole_item(R, item="", fresh_from=None):                   # noqa: F811 -- S975: a fresh surplus is its own verdict
    V = _whole_item_before_s975(R, item, fresh_from)
    try:                                                       # a whole-unit item (CCM = bottle): its stored count is a pack per bottle --
        import qty_words as _QW                                # never 'surplus' on that figure until the record's pack is put right (second look 3)
        wh = _QW.whole_unit_of(V.get("item") or item)
    except Exception:                                          # noqa: BLE001
        wh = None
    if V.get("v") == "fresh_gap" and V.get("gap") is not None and V["gap"] > 0 and not wh:
        V = dict(V, v="surplus", word="a fresh count of %s finds more on the shelf than in Marg (%s; Marg %s, shelf %s) -- noted, never a loss; "
                                     "nothing waits for your call" % (V.get("base"), V.get("gap_t"), V.get("marg_t"), V.get("shelf_t")))
    if wh and V.get("v") == "fresh_gap":                        # CCM: the stored count is a pack per bottle -- look, never red 'your call'
        V = dict(V, v="look", word="Marg counts %s by the %s, the stock record by a pack of %s -- this count cannot be judged yet; see the item ledger" % (
            V.get("item") or item, wh, V.get("pack")))
    return V
# ---- S975 end ---------------------------------------------------------------------------------------------------------------------------
