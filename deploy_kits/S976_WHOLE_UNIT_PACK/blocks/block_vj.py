

# ---- S976 (28-Nov-2026, Sanjeevni session 543, kit S976_WHOLE_UNIT_PACK; F-1742) ---------------------------------------------------------
#  A whole-unit item (the desk's list, "CCM = bottle"): Marg's voucher prints its quantity in bottles ('3'); the reading kept from the
#  medical PC took it as 3 packs of its packing (1*40 -> 120). Such a line is read as the bottles Marg printed (per 1); the item's pack is 1; and
#  S975's 'look first -- this count cannot be judged yet' stands only while the record still gives it a pack above 1. Every other item
#  and line is exactly as before.
KIT_S976 = "S976_WHOLE_UNIT_PACK"


def _s976_whole(con, name):
    try:
        import stock_figure as _SF976                         # noqa: PLC0415
        return _SF976._s976_whole(con, name)
    except Exception:                                         # noqa: BLE001
        return None


_pack_of_before_s976 = _pack_of


def _pack_of(con, name):                                      # noqa: F811 -- S976
    p = _pack_of_before_s976(con, name)
    if int(p or 1) > 1 and _s976_whole(con, name):
        return 1
    return p


_marg_lines_before_s976 = marg_lines


def marg_lines(con):                                          # noqa: F811 -- S976: a whole-unit item's line in the bottles Marg printed
    out = _marg_lines_before_s976(con)
    for d in out:
        try:
            q = str(d.get("qty") or "").strip()
            per = int(d.get("per") or 1)
            if per > 1 and re.fullmatch(r"-?\d+", q) and int(d.get("units") or 0) == abs(int(q)) * per and _s976_whole(con, d.get("item")):
                d["units"], d["per"], d["s976"] = abs(int(q)), 1, "read in the item's whole pieces, as Marg printed it"   # per 1: told "3", never "0:3" (cold review M1)
        except (TypeError, ValueError):
            continue
    return out


_whole_item_before_s976 = whole_item


def whole_item(R, item="", fresh_from=None):                   # noqa: F811 -- S976: 'look' only while the record's pack is above 1
    V = _whole_item_before_s976(R, item, fresh_from)
    if V.get("v") == "look" and int(V.get("pack") or 1) <= 1 and str(V.get("word") or "").startswith("Marg counts "):
        V = _whole_item_before_s975(R, item, fresh_from)
        if V.get("v") == "fresh_gap" and V.get("gap") is not None and V["gap"] > 0:
            V = dict(V, v="surplus", word="a fresh count of %s finds more on the shelf than in Marg (%s; Marg %s, shelf %s) -- noted, never a loss; "
                                         "nothing waits for your call" % (V.get("base"), V.get("gap_t"), V.get("marg_t"), V.get("shelf_t")))
    return V
# ---- S976 end ---------------------------------------------------------------------------------------------------------------------------
