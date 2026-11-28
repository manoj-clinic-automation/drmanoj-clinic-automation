

# ---- S976 (28-Nov-2026, Sanjeevni session 543, kit S976_WHOLE_UNIT_PACK; F-1742) ---------------------------------------------------------
#  Darpan's count screen for a whole-unit item (the desk's list, "CCM = bottle"): ONE box in its own word (Botal), like a gel's Tube --
#  never Patte / Goli with a pack of its packing (CCM 1*40 stored 40 per bottle on 28-11). item_info() gives such an item pack 1, so the
#  owner's asks, Abhi ginti, Stock batao and Kuchh gadbad hai read it whole; the day's morning list is put right after it is written
#  (a ranked or carried row keeps the pack it was written with). Every other item is exactly as before.
KIT_S976 = "S976_WHOLE_UNIT_PACK"


def _s976_whole(con, name):
    try:
        return _sf()._s976_whole(con, name)
    except Exception:                                         # noqa: BLE001
        return None


def _s976_pack(con, name, packing, pack=None):
    """The pack the count screen uses: 1 for a whole-unit item, else pack_of(packing) as before."""
    if _s976_whole(con, name):
        return 1
    return pack_of(packing, pack)


_item_info_before_s976 = item_info


def item_info(con, sp, name):                                 # noqa: F811 -- S976
    info = _item_info_before_s976(con, sp, name)
    if int(info.get("pack") or 1) > 1 and (_s976_whole(con, info.get("item") or name) or _s976_whole(con, name)):
        info = dict(info, pack=1)
    return info


def _s976_fix_day(con, day):
    """A whole-unit item's UNANSWERED rows of the day's morning list read pack 1 (a ranked or carried row was written with its packing's)."""
    n = 0
    try:
        for rid, item, pack in con.execute("SELECT id, item, pack FROM stock_spot_roster WHERE day=? AND answered_at IS NULL AND COALESCE(pack,1)>1",
                                           (str(day)[:10],)).fetchall():
            if _s976_whole(con, item):
                con.execute("UPDATE stock_spot_roster SET pack=1 WHERE id=? AND answered_at IS NULL", (rid,))
                n += 1
        if n:
            con.commit()
    except sqlite3.Error:
        pass
    return n


_build_roster_before_s976 = build_roster


def build_roster(con, day=None, S=None, sp=None, who="system", force=False, asks_ok=False):      # noqa: F811 -- S976
    V = _build_roster_before_s976(con, day, S, sp, who, force, asks_ok)
    if _s976_fix_day(con, (day or today()).isoformat()):
        return roster_view(con, day, S, sp)
    return V


_roster_view_before_s976 = roster_view


def roster_view(con, day=None, S=None, sp=None):              # noqa: F811 -- S976: the list's words read the whole-unit list first
    try:
        _s976_whole(con, "-")                                 # loads the desk's list into qty_words (Botal, never Patte)
    except Exception:                                         # noqa: BLE001
        pass
    return _roster_view_before_s976(con, day, S, sp)
# ---- S976 end ---------------------------------------------------------------------------------------------------------------------------


