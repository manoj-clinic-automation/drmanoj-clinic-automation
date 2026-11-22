# ------------------------------------------------------------------ S928 (D1036 / D1037, 22-Nov-2026): the bill over the tap; a count by its time
#  THE OWNER'S WORD (22-Nov 07:01): "the scanned bill's quantity is relied on over reception's arrival taps, and the same rule must apply
#  everywhere in the system". So an arrival line (a tap, or a scan-tied order line) COUNTS by the quantity the dealer's scanned bill carries
#  for that medicine -- read by the tracker's own matcher (order_track.match_lines, as S825 judges "on the bill") -- whenever the order has a
#  usable, read scan tied to it: a tap above the bill is a SHORT SUPPLY (short_supplies(), the Stock check page; it rides the dealer's next
#  order through the purchase flow), a tapped medicine the bill does not carry counts NOTHING, a bill above the tap counts the bill. With no
#  usable read scan the tap stands as before (nothing is dropped, charter 1b). The switch: arrival.bill_over_tap (stock_watch.settings).
#  A COUNT BY ITS TIME (F-1564): a count saved on its own day at or after count.evening_hour (the setting, 17:00 to start) stands for the END
#  of that day -- its day's sales are not taken off again (TYRO BR, Darpan 12-10 19:49: ~18:5 strips were). A count saved before the hour, or
#  keyed in on a later day, is the start of its day as before.
def _s928_settings(ctx):
    """(arrival.bill_over_tap, count.evening_hour) through stock_watch.settings -- once per Ctx; (True, 17) when unread."""
    if "s928" not in ctx.c:
        bot, ev = True, 17
        try:
            S = _sw().settings(ctx.con)
            bot = bool(S.get("bill_over_tap", True))
            ev = int(S.get("evening_hour", 17))
        except Exception:                                     # noqa: BLE001
            pass
        ctx.c["s928"] = (bot, max(0, min(23, ev)))
    return ctx.c["s928"]


def evening_count(at, hour, day=None):
    """True when the count moment `at` (ISO) falls on `day` (its own day; at's day when None) at or after `hour` -- the count then stands
    for the END of its day. False for an unreadable moment."""
    s = str(at or "").strip().replace(" ", "T")
    if len(s) < 13 or not s[11:13].isdigit():
        return False
    if day is not None and s[:10] != str(day)[:10]:
        return False
    return int(s[11:13]) >= int(hour)


def _s928_octx(ctx):
    """order_track.Ctx (the scans and their readings) once per Ctx; None when the scan store cannot be read. The connection's row factory is
    put back as it was (as s825_bill_judged does)."""
    key = ("s928_octx",)
    if key in ctx.c:
        return ctx.c[key]
    o = None
    con = ctx.con
    if con is not None:
        rf = con.row_factory
        try:
            con.row_factory = sqlite3.Row
            import order_track as OT                          # noqa: PLC0415 -- beside this file
            o = OT.Ctx(con)
            if not getattr(o, "ok", False):
                o = None
            else:
                o._s928_OT = OT
        except Exception:                                     # noqa: BLE001
            o = None
        finally:
            con.row_factory = rf
    ctx.c[key] = o
    return o


def bill_units(con, sp, line, ctx=None):
    """S928: what the dealer's SCANNED BILL says this arrival line brought -- dict(units, qty, on_bill, read_name, scan_id) -- or None when the
    rule cannot speak (the switch off; no order; no usable, read scan tied to the order; the store unreadable): the line's own units then
    stand. on_bill False -> units 0.0 (the bill does not carry the medicine: it did not come, whatever was tapped); a matched line whose
    quantity was not read -> units None (read, but no figure: the line's own units stand). units = the read quantity x the order line's
    pack size (the unit the tap itself is counted in). Once per line per Ctx. READ ONLY."""
    ctx = _ctx(con, sp, ctx)
    if not isinstance(line, dict) or not line.get("order_id"):
        return None
    if not _s928_settings(ctx)[0]:
        return None
    ck = ("s928_bill", line.get("line_id"), int(line.get("order_id") or 0), norm(line.get("item")))
    if ck in ctx.c:
        return ctx.c[ck]
    try:
        out = _bill_units(ctx, line)
    except Exception:                                         # noqa: BLE001 -- fail-soft: the line's own units
        out = None
    ctx.c[ck] = out
    return out


def _s928_order_match(ctx, o, OT, order_id):
    """ONE match per order, as s825_bill_judged matches: every order line's item against every read line of the order's usable, read scans,
    one-to-one (order_track.match_lines) -- {item: (read name, stamp)}, plus the reads [(name, stamp, qty, free, head)] and the heads.
    Cached per order per Ctx. None when the order has no usable, read scan."""
    key = ("s928_match", int(order_id))
    if key in ctx.c:
        return ctx.c[key]
    con = ctx.con
    out = None
    sids = sorted({int(r[0]) for r in con.execute("SELECT asset_bill_id FROM order_scan_tie WHERE order_id=? AND arrived=1 AND asset_bill_id IS NOT NULL", (int(order_id),))})
    heads = []
    for sid in sids:
        h = o.head(sid)
        if h in o.scans and h not in heads and o.usable(h) and o.names(h):
            heads.append(h)
    if heads:
        reads = []
        for h in heads:
            stp = o.scans[h].get("stamp_no") or "#%d" % h
            for it in ((o.read.get(int(h)) or {}).get("items") or []):
                if isinstance(it, dict) and it.get("name"):
                    fr = it.get("free")
                    if fr is None:
                        fr = it.get("free_qty")
                    reads.append((str(it.get("name")), stp, it.get("qty"), fr, h))
        if reads:
            orow = con.execute("SELECT vendor, supplier_norm FROM purchase_order WHERE id=?", (int(order_id),)).fetchone()
            sn = (orow[1] if (orow and orow[1]) else OT._pa().supplier_key((orow[0] if orow else "") or ""))
            items = list(dict.fromkeys(str(r[0]) for r in con.execute("SELECT item FROM purchase_order_line WHERE order_id=? ORDER BY id", (int(order_id),))))
            hit = OT.match_lines(con, sn, items, [(n, s) for (n, s, _q, _f, _h) in reads], o.sf)
            out = dict(hit=hit, reads=reads, heads=heads)
    ctx.c[key] = out
    return out


def _bill_units(ctx, line):
    con = ctx.con
    if con is None or not _has(con, "order_scan_tie"):
        return None
    o = _s928_octx(ctx)
    if o is None:
        return None
    OT = o._s928_OT
    M = _s928_order_match(ctx, o, OT, int(line["order_id"]))
    if M is None:
        return None
    item = str(line.get("item") or "")
    if item not in M["hit"]:
        return dict(units=0.0, qty=None, on_bill=False, read_name="", scan_id=M["heads"][0], scans=list(M["heads"]))
    rn, stp = M["hit"][item]
    nm = OT._nm(rn)
    qs, fs, sid = [], [], M["heads"][0]
    for n, s, qq, fr, h in M["reads"]:                        # every batch line of the medicine on that bill, summed (as carried() sums them)
        if s == stp and OT._nm(n) == nm:
            qs.append(qq)
            fs.append(fr)
            sid = h
    try:
        qf = sum(float(q) for q in qs)
        ff = sum(float(f) for f in fs if f not in (None, ""))
    except (TypeError, ValueError):
        return dict(units=None, qty=None, on_bill=True, read_name=rn, scan_id=sid, scans=list(M["heads"]))
    ps = int(line.get("pack_size") or 1) or 1
    return dict(units=(qf + ff) * ps, qty=qf, free=ff, on_bill=True, read_name=rn, scan_id=sid, scans=list(M["heads"]))


def _count_units(con, sp, a, ctx):
    """The units an arrival line COUNTS for: the scanned bill's (bill_units) when it speaks, else the line's own."""
    b = bill_units(con, sp, a, ctx)
    if b is not None and b.get("units") is not None:
        return float(b["units"])
    return float(a.get("units") or 0)


def short_supplies(con, sp, ctx=None, since_iso=""):
    """S928: every open arrival line (tapped or scan-tied; not carried by Marg's purchases, no billed_bill_no) whose tap or order quantity and
    the scanned bill's quantity DIFFER: dict(line_id, item, vendor, supkey, order_id, kind, at, tap_units, bill_units, diff_units (bill - tap:
    negative = short, the dealer sent less than was tapped / ordered; positive = over), on_bill, read_name, scan_id, pack_size). Sorted by
    item, then moment. The Stock check page's words; the purchase flow reads it for the dealer's next order. READ ONLY, fail-soft []."""
    ctx = _ctx(con, sp, ctx)
    con = ctx.con
    out = []
    if con is None or sp is None or not getattr(sp, "ok", False) or not _s928_settings(ctx)[0]:
        return out
    try:
        items = [r[0] for r in con.execute("SELECT DISTINCT item FROM purchase_order_line WHERE arrived_at IS NOT NULL AND supplied>0 AND COALESCE(billed_bill_no,'')=''")]
    except sqlite3.Error:
        return out
    lines = []
    for it in items:
        lines.extend(a for a in _sw()._arrivals(con, it, since_iso or "", sp, ctx=ctx) if not str(a.get("billed_bill_no") or "").strip())
    lines.extend(scan_lines(con, sp, None, since_iso or "", ctx))
    seen = set()
    for a in lines:
        if a.get("line_id") in seen:
            continue
        seen.add(a.get("line_id"))
        if carried(con, sp, a, ctx) is not None:
            continue
        b = bill_units(con, sp, a, ctx)
        if b is None or b.get("units") is None:
            continue
        tap = float(a.get("units") or 0)
        if abs(float(b["units"]) - tap) < 0.5:
            continue
        out.append(dict(line_id=a.get("line_id"), item=a.get("item"), vendor=a.get("vendor") or "", supkey=a.get("supkey") or _sw().supkey(a.get("vendor")),
                        order_id=a.get("order_id"), kind=a.get("kind") or "tap", at=str(a.get("arrived_at") or a.get("scan_at") or ""),
                        tap_units=tap, bill_units=float(b["units"]), diff_units=round(float(b["units"]) - tap, 3), on_bill=bool(b.get("on_bill")),
                        read_name=b.get("read_name") or "", scan_id=b.get("scan_id"), pack_size=int(a.get("pack_size") or 1)))
    out.sort(key=lambda x: (str(x["item"]), x["at"]))
    return out


