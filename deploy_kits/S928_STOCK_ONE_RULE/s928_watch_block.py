# ------------------------------------------------------------------ S928 (D1037, 22-Nov-2026): every count reaches the owner -- one line a day
def _s928_cls(n):
    """The Needs-you class of a stock notice: information for a close/ortho line, a count that matches, and a day of counts with nothing below
    the records; a warning otherwise."""
    t = n.get("text") or ""
    if n.get("kind") in ("close_watch", "ortho_closed") or "matches Marg" in t:
        return "info"
    if n.get("kind") == "count_day" and "below the records" not in t:
        return "info"
    return "warn"


def _s928_count_day(con, sp=None):
    """S928 (the owner's word on mock-up v5, 22-Nov 07:49): every count Darpan writes reaches him -- ONE line per day on his Needs-you,
    'Darpan counted N items today: ...', each item with its words against the records (the figure the point was judged on: the shelf figure
    for a counted item, Marg's for an uncounted one), rewritten after every count or correction of the day (notice kind count_day, once_key
    counted:<day>). A superseded point is never read. Fail-soft: the count itself is already stored and is never held up by this."""
    try:
        d = today().isoformat()
        rows = con.execute("SELECT item, qty_units, expected_units, gap_units, basis, by FROM stock_point WHERE substr(at,1,10)=? AND source IN ('spot','darpan') "
                           "AND COALESCE(status,'')<>'superseded' ORDER BY at, id", (d,)).fetchall()
        if not rows:
            return None
        sp = sp or Spine()
        parts, whos = [], []
        for item, q, _e, g, basis, by in rows:
            info = item_info(con, sp, item)
            pack, packing = int(info.get("pack") or 1), info.get("packing") or ""
            name = info.get("item") or item
            if basis == "approx" or g is None:
                w = "%s (no figure of its own to judge it)" % qw(float(q), pack, packing, name)
            elif abs(float(g)) < 0.5:
                w = "matches the records"
            elif float(g) < 0:
                w = "%s below the records" % qw(abs(float(g)), pack, packing, name)
            else:
                w = "%s above the records" % qw(float(g), pack, packing, name)
            parts.append("%s %s" % (name, w))
            if by and by not in whos:
                whos.append(by)
        who = " and ".join(str(x).strip().title() for x in whos) or "Darpan"
        txt = "%s counted %d item%s on %s: %s" % (who, len(rows), "" if len(rows) == 1 else "s", dmy(d), " · ".join(parts))
        key = "counted:%s" % d
        con.execute("DELETE FROM stock_watch_notice WHERE kind='count_day' AND once_key=?", (key,))   # rewritten as the day's newest line (notices read newest id first)
        notice(con, "count_day", "owner", txt, once_key=key, days=7)
        con.commit()
        return txt
    except Exception:                                         # noqa: BLE001
        return None


