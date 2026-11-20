# make_s894.py -- builds stock_watch.py S894 from the live bytes (f0d9092a) by exact anchors.
import hashlib, sys
FROM_MD5 = "f0d9092a051c4cd043645e4510ef4cee"
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest() == FROM_MD5, "not the FROM bytes"
s = b.decode("utf-8")
def rep(a, c):
    global s
    assert s.count(a) == 1, ("anchor count %d" % s.count(a), a[:80])
    s = s.replace(a, c)

# 1 -- answer_roster: the asked item's answer goes back to the owner, before the old roster_id close
rep('''    P = write_point(con, r[1], qty_units, "spot", who, roster_id=r[0], sp=sp)
    con.execute("UPDATE stock_spot_roster SET answered_at=?, qty_units=?, point_id=? WHERE id=?", (now_iso(), float(qty_units), P["id"], r[0]))
    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE roster_id=? AND done_at IS NULL", (now_iso(), r[0]))''',
'''    P = write_point(con, r[1], qty_units, "spot", who, roster_id=r[0], sp=sp)
    con.execute("UPDATE stock_spot_roster SET answered_at=?, qty_units=?, point_id=? WHERE id=?", (now_iso(), float(qty_units), P["id"], r[0]))
    _s894_asked_back(con, r[1], qty_units, sp)              # S894: before the roster_id close below, which misses a carried row
    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE roster_id=? AND done_at IS NULL", (now_iso(), r[0]))''')

# 2 -- darpan_point ('Stock batao') on an asked item: the same
rep('''    P = write_point(con, info["item"], qty_units, "darpan", who, sp=sp)
    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL", (now_iso(), norm_name(info["item"])))''',
'''    P = write_point(con, info["item"], qty_units, "darpan", who, sp=sp)
    _s894_asked_back(con, info["item"], qty_units, sp)       # S894
    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL", (now_iso(), norm_name(info["item"])))''')

# 3 -- the owner's Needs-you shows the asked count (info when it matches Marg)
rep('''            if n["kind"] in ("cadence", "plan_lapsed", "trace_unexplained", "spot_missed", "close_watch", "ortho_closed") and n["at"][:10] >= (today() - dt.timedelta(days=7)).isoformat():''',
'''            if n["kind"] in ("cadence", "plan_lapsed", "trace_unexplained", "spot_missed", "close_watch", "ortho_closed", "asked_count") and n["at"][:10] >= (today() - dt.timedelta(days=7)).isoformat():''')
rep('''                out.append(dict(cls="warn" if n["kind"] not in ("close_watch", "ortho_closed") else "info", target="stock", text=n["text"]))   # S436: ortho_closed''',
'''                out.append(dict(cls="warn" if n["kind"] not in ("close_watch", "ortho_closed") and "matches Marg" not in (n["text"] or "") else "info",
                                target="stock", text=n["text"]))   # S436: ortho_closed; S894: asked_count''')

# 3b -- correct_roster: the owner's line follows a same-day correction
rep('''        _audit(con, "spot_fix", dict(item=old[1], old_qty=float(old[2]), new_qty=q, old_point=old[0], new_point=P["id"]), who, P["id"])
        con.commit()''',
'''        _audit(con, "spot_fix", dict(item=old[1], old_qty=float(old[2]), new_qty=q, old_point=old[0], new_point=P["id"]), who, P["id"])
        con.commit()
        _s894_refix(con, old[1], q, sp)                         # S894''')

# 4 -- the function, placed before ask()
rep('''def ask(con, item, who, sp=None):
    """The owner's 'Count this' -> the head of the next roster."""''',
'''def _s894_text(con, item, qty_units, sp=None):
    """S894: the owner's line for an asked count, against Marg's newest closing (by its date, as item_info reads it)."""
    info = item_info(con, sp or Spine(), item)
    name = info.get("item") or item
    pack, packing = int(info.get("pack") or 1), info.get("packing") or ""
    q = float(qty_units)
    txt = "Darpan counted %s (you asked): %s" % (name, qw(q, pack, packing, name))
    snap = con.execute("SELECT qty, as_on FROM stock_snapshot WHERE item=? ORDER BY substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2) DESC, rowid DESC LIMIT 1",
                       (name,)).fetchone()
    if snap and snap[0] is not None:
        m = float(snap[0])
        d = q - m
        txt += " -- Marg (closing %s) %s" % (snap[1], qw(m, pack, packing, name))
        txt += " -- matches Marg" if abs(d) < 0.5 else " -- %s %s than Marg" % (qw(abs(d), pack, packing, name), "fewer" if d < 0 else "more")
    else:
        txt += " -- Marg's figure not read"
    return txt


def _s894_asked_back(con, item, qty_units, sp=None):
    """S894 (20-Nov-2026, the owner's word 14:44): a count the owner ASKED for ('Count this') reaches his Needs-you the moment it is
    entered, beside Marg's own closing figure, and every open ask for that item closes -- also when the answer came on a later day's
    list (a carried roster row), which never closed the ask before (asks 3 and 4 of 14-Nov). One line per item per day. The line is
    written FIRST, the ask closed after it (a failed line never leaves a closed ask with no word). Fail-soft: the count itself is
    already stored and is never held up by this."""
    try:
        nm = norm_name(item)
        if not con.execute("SELECT 1 FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL", (nm,)).fetchone():
            return None
        try:
            txt = _s894_text(con, item, qty_units, sp)
        except Exception:                                     # noqa: BLE001 -- the plain line, never none
            txt = "Darpan counted %s (you asked): %s units -- see the stock page" % (item, qty_units)
        notice(con, "asked_count", "owner", txt, once_key="asked:%s:%s" % (nm, today().isoformat()), days=7)
        con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL", (now_iso(), nm))
        return txt
    except Exception:                                         # noqa: BLE001
        return None


def _s894_refix(con, item, qty_units, sp=None):
    """S894: 'Galat likha? Badlo' on an asked item the same day -- the owner's line follows the corrected count. Fail-soft."""
    try:
        key = "asked:%s:%s" % (norm_name(item), today().isoformat())
        if con.execute("SELECT 1 FROM stock_watch_notice WHERE kind='asked_count' AND once_key=?", (key,)).fetchone():
            con.execute("UPDATE stock_watch_notice SET text=? WHERE kind='asked_count' AND once_key=?",
                        (_s894_text(con, item, qty_units, sp) + " (corrected)", key))
            con.commit()
    except Exception:                                         # noqa: BLE001
        pass


def ask(con, item, who, sp=None):
    """The owner's 'Count this' -> the head of the next roster."""''')
open(dst, "wb").write(s.encode("utf-8"))
print("make_s894: built", hashlib.md5(s.encode("utf-8")).hexdigest())
