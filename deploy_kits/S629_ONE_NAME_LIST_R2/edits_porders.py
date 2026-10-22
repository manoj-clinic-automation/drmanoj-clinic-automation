# S628 anchored edits for /root/finance/porders.py (FROM b1736494)
EDITS = []

EDITS.append(("""LINE_COLS = (("purchase_order_line", "missing", "INTEGER NOT NULL DEFAULT 0"), ("purchase_order_line", "billed_qty", "INTEGER"),""",
              """S628_COLS = (("purchase_order_line", "billed_units", "INTEGER"), ("purchase_order_line", "other_supplier", "TEXT"),   # S628 (D761)
             ("purchase_order_line", "other_bill_no", "TEXT"), ("purchase_order_line", "other_date", "TEXT"), ("purchase_order_line", "other_qty", "INTEGER"))
LINE_COLS = (("purchase_order_line", "missing", "INTEGER NOT NULL DEFAULT 0"), ("purchase_order_line", "billed_qty", "INTEGER"),"""))

EDITS.append(("""             ("purchase_order_line", "arrived_at", "TEXT"), ("purchase_order", "section", "TEXT"))
""", """             ("purchase_order_line", "arrived_at", "TEXT"), ("purchase_order", "section", "TEXT")) + S628_COLS
"""))

# detect_supplies: the whole function is replaced (anchor = its def line through the line before _close_complete_orders)
DS_OLD_HEAD = '''def detect_supplies(con):
    """Marg's purchase that carries an open order line marks the line billed (qty in PACKS, bill no, date) -- and supplied, when nobody'''
DS_OLD_TAIL = '''    if n:
        con.commit()
        _close_complete_orders(con, "marg")
    return n


def _close_complete_orders(con, who):'''

DS_NEW = '''def _s628_cols(con):
    """S628: the five columns of S628_COLS, added when absent (ensure_schema adds them too; detect_supplies does not wait for a page)."""
    for table, col, typ in S628_COLS:
        try:
            if col not in {r[1] for r in con.execute("PRAGMA table_info(%s)" % table)}:
                con.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, typ))
        except sqlite3.Error:
            pass


def _s628_packs(hit, ps):
    """S628 (D761, LINVIZ 600): the order's packs that a matched bill line brings -> (packs, units or None). When the bill line's packing and the
    order line's pack size are both read (1*N) and differ, the tablets decide: floor(tablets / the order's pack size), the tablets kept beside it;
    else qty + free as S598 (two batches of one item on one bill summed by carried())."""
    q = float(hit.get("qty") or 0) + float(hit.get("free") or 0)
    try:
        import med_names                                      # noqa: PLC0415
        nb = med_names.packn(hit.get("packing"))
    except Exception:                                         # noqa: BLE001
        nb = None
    try:
        ps = int(ps or 1)
    except (TypeError, ValueError):
        ps = 1
    if nb and ps > 1 and nb != ps:
        units = int(round(q * nb))
        return units // ps, units
    return int(round(q)), None


def detect_supplies(con):
    """Marg's purchase that carries an open order line marks the line billed (qty in PACKS, bill no, date) -- and supplied, when nobody
    tapped. S593 (D743; S583's 'two copies' closed): WHICH bill carries the line is THE ONE RULE, stock_figure.carried() on the spine by the
    spine's key -- accepted here only by rule (c) (the order's own vendor, dated up to arrival.back_days before the order day) or (d) (the own
    vendor on or after the order day); (a) cannot occur (billed_bill_no is NULL here); (e), another supplier's bill, counts for stock only and
    never marks this line billed. The packs are THE MATCHED BILL LINE's own: qty + free as carried() returns them (S598, F-942: the line of
    the order line's own printed name, never the family's sum for the key; two batches of one item on one bill arrive summed; never
    units / pack_size: a 'whole' key's units are its qty). A fresh Ctx per row, so rule (b) sees each write (two lines of one key, two bills).
    The spine unread (sw.ok False): nothing written, one stderr line. The tables (purchase_line) and the 20-letter clip are read no more. Idempotent.
    S628 (D761): (0) the one name list learns first (med_names.learn, fail-soft) -- so a Marg item that is the ordered medicine under another name
    (THIO Q AP TAB for THIO Q AP) carries the line through carried(); (1) the packs by tablets when the bill's packing differs from the order's
    pack size (_s628_packs; billed_units kept); (2) a billed line below its packs is read again by rule (a) on every pass and RAISED when the bill's
    matching lines now give more (F-990: the two ZUPRINOR 5 lines of JP23217), never lowered, audited line_redetected; (3) after every own-dealer
    line is marked, a line still unbilled whose medicine came on ANOTHER dealer's bill (rule e) dated within names.window_days of the order day
    gets other_supplier / other_bill_no / other_date / other_qty (F-991) -- it is NOT marked billed (D743 stands: stock only), audited
    line_other_dealer. Returns the count of lines marked or raised."""
    n = 0
    _s628_cols(con)
    try:                                                      # S628 (0): the one name list first -- never blocks the pass
        import med_names                                      # noqa: PLC0415
        med_names.learn(con)
    except Exception as _ex_mn:                               # noqa: BLE001
        print("porders.detect_supplies: med_names.learn failed (%s) -- the pass runs on the list as it stands" % _ex_mn, file=sys.stderr)
    try:
        rows = con.execute("SELECT l.id, l.item, l.packs, l.supplied, l.missing, o.vendor, o.created_at, l.pack_size FROM purchase_order_line l "
                           "JOIN purchase_order o ON o.id=l.order_id WHERE o.status IN ('sent','received') AND l.billed_qty IS NULL").fetchall()
        again = con.execute("SELECT l.id, l.item, l.packs, l.supplied, l.missing, o.vendor, o.created_at, l.pack_size, l.billed_qty, l.billed_bill_no, "
                            "l.billed_date, l.arrived_by FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                            "WHERE o.status IN ('sent','received') AND l.billed_qty IS NOT NULL AND COALESCE(l.billed_bill_no,'')<>'' "
                            "AND l.billed_qty < l.packs").fetchall()
    except sqlite3.Error:
        return 0
    if not rows and not again:
        return 0
    import stock_figure as SF                                 # noqa: PLC0415 -- beside this file: the one stock function (S577 / S583 / S587)
    import stock_watch as SW                                  # noqa: PLC0415
    sw = SW.Spine()
    if not getattr(sw, "ok", False):
        print("porders.detect_supplies: the spine could not be read -- no order line marked billed (S593)", file=sys.stderr)
        return 0
    try:
        win = int(float(_setting(con, "names.window_days", "7") or 7))
    except (TypeError, ValueError):
        win = 7
    try:
        for r in rows:
            lid, item, packs, supplied, missing, vendor, created, ps = r[0], r[1], int(r[2] or 0), r[3], r[4], r[5], str(r[6] or ""), r[7]
            line = dict(line_id=lid, item=item, vendor=vendor, order_at=created, billed_bill_no=None, own_only=True)   # S628: the own dealer first
            ctx = SF._ctx(con, sw, None)                      # R1-C10: a fresh context per row -- the per-key taken-bills cache must see each write
            hit = SF.carried(con, sw, line, ctx)
            if not hit or hit.get("how") not in ("c", "d"):
                continue
            q, units = _s628_packs(hit, ps)                   # S598: the matched bill LINE's packs; S628: by tablets when the packings differ
            if q <= 0 and not units:
                continue
            bno, bdate = hit["bill"], hit["date"]
            con.execute("UPDATE purchase_order_line SET billed_qty=?, billed_bill_no=?, billed_date=?, detected_at=?, billed_units=? WHERE id=?",
                        (q, str(bno or ""), bdate, now_iso(), units, lid))
            if supplied is None and not missing:
                con.execute("UPDATE purchase_order_line SET supplied=?, short=?, arrived_by='marg', arrived_at=? WHERE id=?",
                            (q, 1 if q < packs else 0, now_iso(), lid))
                _audit(con, "marg", "line_detected", lid, dict(item=item, ordered=packs, billed=q, bill=str(bno or ""), units=units))
            n += 1
        for r in again:                                       # S628 (2): F-990 -- a billed line read again by rule (a); raised, never lowered
            lid, item, packs, supplied, missing, vendor, created, ps, bq, bno, bdate, aby = (r[0], r[1], int(r[2] or 0), r[3], r[4], r[5], str(r[6] or ""),
                                                                                         r[7], int(r[8] or 0), r[9], r[10], r[11])
            ctx = SF._ctx(con, sw, None)
            hit = SF.carried(con, sw, dict(line_id=lid, item=item, vendor=vendor, order_at=created, billed_bill_no=bno, billed_date=bdate), ctx)
            if not hit or hit.get("how") != "a" or hit.get("qty") is None or str(hit.get("supkey") or "") != SW.supkey(vendor):
                continue                                      # rule (a) reads a bill number across dealers: only the order's own dealer's bill raises
            q, units = _s628_packs(hit, ps)
            if q <= bq:
                continue                                      # never lowered (LINVIZ: 6 strips of 6 read by tablets stays 3)
            con.execute("UPDATE purchase_order_line SET billed_qty=?, billed_units=COALESCE(?, billed_units) WHERE id=?", (q, units, lid))
            if str(aby or "") == "marg":                      # Marg wrote supplied / short itself: both follow (a tap's answer is the person's)
                con.execute("UPDATE purchase_order_line SET supplied=?, short=? WHERE id=?", (q, 1 if q < packs else 0, lid))
            _audit(con, "marg", "line_redetected", lid, dict(item=item, ordered=packs, was=bq, billed=q, bill=str(bno or ""), kit="S628"))
            n += 1
        if n:
            con.commit()
        since = str(_setting(con, "order.track_since", "2026-10-12") or "2026-10-12")[:10]     # the order list's own window (S619)
        rows2 = con.execute("SELECT l.id, l.item, l.packs, o.vendor, o.created_at, l.pack_size FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                            "WHERE o.status IN ('sent','received') AND l.billed_qty IS NULL AND COALESCE(l.other_bill_no,'')='' "
                            "AND substr(o.created_at,1,10)>=?", (since,)).fetchall()
        m = 0
        for r in rows2:                                       # S628 (3): F-991 -- another dealer's bill, after every own-dealer line is marked
            lid, item, packs, vendor, created, ps = r[0], r[1], int(r[2] or 0), r[3], str(r[4] or ""), r[5]
            ctx = SF._ctx(con, sw, None)
            hit = SF.carried(con, sw, dict(line_id=lid, item=item, vendor=vendor, order_at=created, billed_bill_no=None), ctx)
            if not hit or hit.get("how") != "e":
                continue
            try:
                late = (dt.date.fromisoformat(str(hit["date"])[:10]) - dt.date.fromisoformat(created[:10])).days > win
            except ValueError:
                late = True
            if late:
                continue
            q, units = _s628_packs(hit, ps)
            if q <= 0:
                continue
            con.execute("UPDATE purchase_order_line SET other_supplier=?, other_bill_no=?, other_date=?, other_qty=? WHERE id=? AND COALESCE(other_bill_no,'')=''",
                        (str(hit.get("supplier") or hit.get("supkey") or ""), str(hit["bill"] or ""), str(hit["date"])[:10], q, lid))
            _audit(con, "marg", "line_other_dealer", lid, dict(item=item, ordered=packs, came=q, dealer=str(hit.get("supplier") or ""), bill=str(hit["bill"] or ""), kit="S628"))
            m += 1
        if m:
            con.commit()
        n += m
    finally:
        try:
            sw.con.close()
        except Exception:                                     # noqa: BLE001
            pass
    if n:
        con.commit()
        _close_complete_orders(con, "marg")
    return n


def _close_complete_orders(con, who):'''
