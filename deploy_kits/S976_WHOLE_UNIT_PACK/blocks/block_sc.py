

# ---- S976 (28-Nov-2026, Sanjeevni session 543, kit S976_WHOLE_UNIT_PACK; F-1742) ---------------------------------------------------------
#  Once the stock record gives a whole-unit item (CCM = bottle) its pack of 1, a count of it reads in its own word on band 2 -- "counted
#  1 bottle · Marg 2 bottles · −1 bottle" -- as S975 told it (D1107), never a bare "1". Every other row is exactly as before.
KIT_S976 = "S976_WHOLE_UNIT_PACK"
_s975_count_row_before_s976 = _s975_count_row


def _s976_w(units, item, signed=False):
    if units is None:
        return "—"
    import qty_words as _QW976                                # noqa: PLC0415
    v = float(units)
    if signed and abs(v) < 0.5:
        return "0"
    t = (_QW976.signed if signed else _QW976.words)(v, name=item)
    return ("−" + t[1:]) if t.startswith("-") else t


def _s975_count_row(con, VJ, J, RR, P, rowmap, WOP, b1items):  # noqa: F811 -- S976
    d = _s975_count_row_before_s976(con, VJ, J, RR, P, rowmap, WOP, b1items)
    try:
        if int(d.get("pack") or 1) <= 1 and _s975_whole(con, P["item"]):
            g = None if (P["qty"] is None or P["expected"] is None) else float(P["qty"]) - float(P["expected"])
            d["fig"] = "counted %s · Marg %s · %s" % (_s976_w(P["qty"], P["item"]), _s976_w(P["expected"], P["item"]),
                                                     _s976_w(g, P["item"], signed=True) if g is not None else "—")
            if d.get("path") and d["path"][0][0] == "ok" and " counted, Marg " in d["path"][0][1]:
                src = "Darpan" if P["source"] == "darpan" else "The spot morning"
                d["path"][0] = ["ok", "%s's count at %s: %s counted, Marg %s at the time." % (src, stamp(P["at"]), _s976_w(P["qty"], P["item"]),
                                                                                             _s976_w(P["expected"], P["item"]))]
    except Exception:                                         # noqa: BLE001 -- the row as S975 drew it
        pass
    return d
# ---- S976 end ---------------------------------------------------------------------------------------------------------------------------
