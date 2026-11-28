

# ---- S975 (28-Nov-2026, Sanjeevni session 542, kit S975_STOCKCHECK_V10; F-1739) -----------------------------------------------------------
#  CCM (the desk's whole-unit list, 'CCM = bottle'): the count screen stores a pack of the stock record's size (40) for each bottle, while
#  Marg -- and this ledger -- count it by the bottle; the 28-11 count read '40 bottles counted, 40 bottles more' for ONE bottle. A count of a
#  whole-unit item whose stored units are whole packs is told in the item's own word: '1 bottle counted', its gap against Marg's figure at
#  the time (already in bottles), and what the screen stored. Every other count reads as before. (The record's pack itself: an F, its own kit.)
KIT5 = "S975_STOCKCHECK_V10"
VERSION = "S975-ITEM-LEDGER-1.6"
_counts_before_s975 = counts
_count_entry_before_s975 = _count_entry


def _s975_pack(con, key):
    try:
        r = con.execute("SELECT pack FROM stock_of_record WHERE k20=? ORDER BY pack DESC LIMIT 1", (key,)).fetchone()
        return int(r[0] or 1) if r else 1
    except sqlite3.Error:
        return 1


def counts(con, sp, key, d2):                                 # noqa: F811 -- S975: each count carries the record's pack
    out = _counts_before_s975(con, sp, key, d2)
    if out and con is not None:
        pk = _s975_pack(con, key)
        for c in out:
            c["pack"] = pk
    return out


def _count_entry(c, U):                                       # noqa: F811 -- S975: a whole-unit item's count in its own word
    e = _count_entry_before_s975(c, U)
    pack = int(c.get("pack") or 1)
    if pack <= 1 or c.get("qty") is None or getattr(U, "strip", True):
        return e
    try:
        import qty_words as QW                                # noqa: PLC0415
        w = QW.whole_unit_of(getattr(U, "name", "") or "")
    except Exception:                                         # noqa: BLE001
        w = None
    q = float(c["qty"])
    if not w or abs(q - round(q / pack) * pack) >= 0.5:
        return e
    n = int(round(q / pack))
    e["counted_t"] = "%d %s%s" % (n, w, "" if n == 1 else "s")
    if c.get("status") not in COUNT_STATUS and c.get("expected") is not None:
        g = n - float(c["expected"])
        e["mark"] = "agrees" if abs(g) < TOL else "%d %s%s %s" % (abs(int(round(g))), w, "" if abs(int(round(g))) == 1 else "s", "short" if g < 0 else "more")
    e["words"] = ("%s · the count screen stored %d:0 (a pack of %d per %s)" % (e.get("words") or "", n, pack, w)).lstrip(" ·")[:200]
    return e
# ---- S975 end ---------------------------------------------------------------------------------------------------------------------------
