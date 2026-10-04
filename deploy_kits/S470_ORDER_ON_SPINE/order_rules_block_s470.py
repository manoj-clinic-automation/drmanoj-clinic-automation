

# ==========================================================================================================================================
# S470_ORDER_ON_SPINE (04-Oct-2026, D672 / D673; rung 4a of S272_SPINE_ARCHITECTURE): THE ENGINE'S THREE NUMBERS COME FROM THE SPINE.
#   order.engine_source = spine (the default): _snapshot_inputs reads the spine through its ONE read door (spine/spine_read.py) --
#       Marg's stock from the latest accepted closing (closing), the sale rate from the spine's sale lines with returns deducted
#       (sales_daily, last_sale), the supplier, the cost, the box and the lot from its purchase lines (purchase_lines); it reads no sale,
#       stock or purchase figure from sale_line_item, stock_snapshot, stock_feed, purchase_line or purchase_bill. Only the item list --
#       names, packings, pack sizes -- is still Marg's newest stock list (stock_snapshot): the spine keeps a closing by key, not by item.
#       The count basis stays the shelf figure (shelf_figure.figures, untouched).
#   order.engine_source = tables: the four old calls, line for line (purchase_app._latest_snapshot / _pace / _last_purchase / _in_transit).
#       Also the way taken, and said in the plan's "engine", if the spine cannot be read.
#   ARRIVALS NOT YET IN MARG -- one rule on both bases: an order's received lines, and an order that arrived by its bill's scan, count as
#       stock until the spine shows a purchase line of that item from that supplier dated on or after THE ORDER'S OWN DAY (Marg dates
#       the bill by the supplier's date, often a day or two before the tap -- the old rule waited for a bill dated after the tap and
#       counted the goods twice until the window ended). On the count basis a counted item's arrival is inside its shelf figure.
#   A FAMILY (items of Marg's stock list that share one 20-letter key, F-719): the spine knows the family's stock and the family's sales,
#       never a member's own. Each member is planned on the family's cover -- its stock and its rate both shared equally -- and its line
#       carries family = n. The members are counted in Marg's stock list, not in the spine's item table (spine_read.family): that table
#       holds a row for every packing an item ever had and for every way a report spells one.
#   Six numbers that were constants are settings (their values unchanged): order.pace_days, order.dead_after_days, order.on_order_days,
#       order.in_transit_days, order.lot_history_days, order.engine_source. plan() also returns no_supplier (a sold item never bought:
#       still ordered from nobody, but named) and engine (which source made this plan).
# ==========================================================================================================================================
import threading as _s470_threading                             # noqa: E402

SETTINGS.update({
    "order.engine_source": ("spine", "(S470) where the engine's sale rate, stock and supplier come from: spine (the one corrected store) or tables (the old reads -- the fallback)"),
    "order.pace_days": ("28", "(S470) the sale rate is what sold over this many days"),
    "order.dead_after_days": ("60", "(S470) an item with no sale for more than this many days is not reordered"),
    "order.on_order_days": ("4", "(S470) a sent order's unanswered lines count as stock for this many days"),
    "order.in_transit_days": ("14", "(S470) goods received and not yet in Marg count as stock for this many days"),
    "order.lot_history_days": ("180", "(S470) the lot and the free-per-lot are read from the purchases of this many days"),
})
S470_KEYS = ("order.engine_source", "order.pace_days", "order.dead_after_days", "order.on_order_days", "order.in_transit_days", "order.lot_history_days")
_S470 = _s470_threading.local()                                # the last inputs' note, per thread: which source made them
_S470_MOD = {"mtime": None, "mod": None}


def _s470_source(con):
    v = _setting(con, "order.engine_source")
    return v if v in ("spine", "tables") else "spine"


def _s470_days(con, key, lo=1):
    """A day-count setting, never below lo (a zero or a word in the row falls back to the default)."""
    n = _int_setting(con, key)
    return n if n >= lo else int(SETTINGS[key][0])


def _s470_engine():
    return getattr(_S470, "engine", "tables")


def _s470_spine():
    """The spine's ONE read door (spine/spine_read.py beside this file), opened read-only on SPINE_DB or spine/spine.db."""
    import importlib.util                                      # noqa: PLC0415
    p = os.path.join(SPINE_DIR, "spine_read.py")
    m = os.path.getmtime(p)
    if _S470_MOD["mod"] is None or _S470_MOD["mtime"] != m:
        spec = importlib.util.spec_from_file_location("spine_read_s470", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _S470_MOD["mod"], _S470_MOD["mtime"] = mod, m
    return _S470_MOD["mod"].Spine(os.environ.get("SPINE_DB") or os.path.join(SPINE_DIR, "spine.db"))


def _s470_pack(packing):
    m = re.match(r"^(\d+)\*(\d+)$", str(packing or "").strip().rstrip("."))
    return max(1, int(m.group(1)) * int(m.group(2))) if m else 1


def _s470_dmy(iso):
    s = str(iso or "")
    return "%s-%s-%s" % (s[8:10], s[5:7], s[0:4]) if re.match(r"^\d{4}-\d\d-\d\d", s) else s


def _s470_master(con, pa):
    """Marg's item list: the NAMES, packings and pack sizes of the newest stock list (stock_snapshot). No figure is read from it -- the
    spine keeps a closing by key only, and its own item table holds one item twice where two reports spell its packing differently."""
    if not _has(con, "stock_snapshot"):
        raise RuntimeError("no stock list on this server")
    dates = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
    if not dates:
        raise RuntimeError("the stock list is empty")
    return [(r[0], r[1] or "", max(1, int(r[2] or 1))) for r in
            con.execute("SELECT item, packing, pack_size FROM stock_snapshot WHERE as_on=? ORDER BY item", (max(dates, key=pa._as_on_key),))]


def _s470_snap(con, pa, sp):
    """(as_on dd-mm-yyyy, {norm(item): row}, [items the spine's closing does not hold]) -- every item of Marg's list with Marg's own figure
    from the spine's latest accepted closing. A family's figure (items of the list under one 20-letter key) is shared equally among
    them, the remainder to the first names. An item the spine's latest closing does not hold is left out and named."""
    fam = {}
    for item, packing, size in _s470_master(con, pa):
        fam.setdefault(sp.key(item), []).append((item, packing, size))
    closes = {key: sp.closing(members[0][0]) for key, members in fam.items()}
    held = [c["as_on"] for c in closes.values() if c]
    if not held:
        raise RuntimeError("the spine holds no closing")
    latest = max(held)
    snap, missing = {}, []
    for key, members in fam.items():
        c = closes[key]
        if not c or c["as_on"] != latest:
            missing.extend(m[0] for m in members)
            continue
        n = len(members)
        base, rem = divmod(int(round(float(c["units"] or 0))), n)
        for i, (item, packing, size) in enumerate(members):
            snap[pa.norm(item)] = dict(item=item, qty=base + (1 if i < rem else 0), packing=packing, pack_size=size,
                                       _s470=dict(key=key, family=n, lot=None, free=None))
    return _s470_dmy(latest), snap, missing


def _s470_pace(sp, snap, today, pace_days):
    """purchase_app._pace's formula on the spine's sale lines: the same window (today - pace_days .. today, both ends), returns
    deducted, units as the spine reads them; every item with any sale in the spine's history gets an entry."""
    since = (today - dt.timedelta(days=pace_days)).isoformat()
    t = today.isoformat()
    out, done = {}, {}
    for k, s in snap.items():
        x = s["_s470"]
        if x["key"] not in done:
            days = {r["date"]: float(r["units"] or 0) for r in sp.sales_daily(s["item"], since, t)}
            done[x["key"]] = (days, sp.last_sale(s["item"]))
        days, ls = done[x["key"]]
        if not days and not ls:
            continue
        n = max(1, int(x["family"]))
        total = max(0.0, sum(days.values())) / n
        peak = (max(days.values()) / n) if days else 0.0
        e = dict(rate_per_day=total / pace_days, sell_days=sum(1 for v in days.values() if v > 0), peak_share=(peak / total) if total > 0 else 0.0)
        if n > 1:
            e["approx_shared"] = n
        if ls:
            try:
                e["days_since_sale"] = (today - dt.date.fromisoformat(ls["date"])).days
            except ValueError:
                e["days_since_sale"] = 999
        out[k] = e
    return out


def _s470_purch(pa, sp, snap, today, lot_days):
    """purchase_app._last_purchase's fields from the spine's PURCHASE lines over all history: vendor (the normalised key every rule,
    proposal and phone lookup is keyed by -- never the spine's supkey), vendor_disp (the printed name), suppliers, rate_p (the latest
    line's cost per pack: net amount / quantity, else amount / quantity), box (the GCD of the quantities; 0 when none). And, from the last
    lot_days only, carried on the line and used by no rail yet: lot (the median quantity bought per line, in units) and free (the median
    free per bought)."""
    since = (today - dt.timedelta(days=lot_days)).isoformat()
    out, done = {}, {}
    for k, s in snap.items():
        x = s["_s470"]
        if x["key"] not in done:
            e = dict(vendor=None, vendor_disp=None, rate_p=None, suppliers=set(), qtys=[], packing=s["packing"])
            lots, frees = [], []
            for l in sp.purchase_lines(s["item"]):
                if l["direction"] != "PURCHASE":
                    continue
                vn = pa.supplier_key(l["supplier"]) if l["supplier"] else ""
                if vn:
                    e["suppliers"].add(vn)
                    e["vendor"], e["vendor_disp"] = vn, l["supplier"]
                q = float(l["qty"] or 0)
                if q:
                    amt = l["net_amount_p"] or l["amount_p"]
                    if amt:
                        e["rate_p"] = int(round(float(amt) / q))
                    e["qtys"].append(int(q))
                    if l["date"] >= since:
                        lots.append(q * s["pack_size"])
                        frees.append(float(l["free"] or 0) / q)
            if e["vendor"] or e["qtys"]:
                g = 0
                for q in e["qtys"]:
                    g = math.gcd(g, q)
                e["box"] = g if g > 1 else 0
                e["lot"] = statistics.median(lots) if lots else None
                e["free"] = round(statistics.median(frees), 3) if frees else None
                done[x["key"]] = e
            else:
                done[x["key"]] = None
        e = done[x["key"]]
        if e:
            out[k] = e
            x["lot"], x["free"] = e["lot"], e["free"]
    return out


def _s470_arrivals(con, pa, sp, snap, today, days):
    """{norm(item): dict(units, order_id, vendor)} -- goods that came and are not in Marg yet: the received lines of an order received in
    the last `days` days, and of an order that arrived by its bill's scan, until the spine shows a PURCHASE line of that item (by the
    spine's key) from that supplier (by supplier_key) dated on or after the order's own day."""
    since = (today - dt.timedelta(days=days)).isoformat()
    tie = _has(con, "order_scan_tie")
    tied = "(SELECT MAX(scan_at) FROM order_scan_tie WHERE order_id=o.id AND arrived=1)"
    out = {}
    try:
        rows = con.execute(
            "SELECT l.item, COALESCE(l.supplied, l.packs) AS got, l.pack_size, o.vendor, o.id AS oid, o.created_at FROM purchase_order_line l "
            "JOIN purchase_order o ON o.id=l.order_id WHERE (o.status='received'" + ((" OR %s IS NOT NULL" % tied) if tie else "")
            + ") AND COALESCE(o.received_at, " + ((tied + ", ") if tie else "") + "o.created_at) >= ? AND COALESCE(l.supplied, l.packs) > 0",
            (since,)).fetchall()
    except sqlite3.Error:
        return out
    by_key = {}
    for k, s in snap.items():
        by_key.setdefault(s["_s470"]["key"], []).append(k)
    for item, got, size, vendor, oid, created in rows:
        vk = pa.supplier_key(vendor)
        seen = any(l["direction"] == "PURCHASE" and l["supplier"] and pa.supplier_key(l["supplier"]) == vk
                   for l in sp.purchase_lines(item, date_from=str(created or "")[:10]))
        if seen:
            continue
        k = pa.norm(item)
        if k not in snap and len(by_key.get(sp.key(item), ())) == 1:
            k = by_key[sp.key(item)][0]                          # the order names it as a report clipped it: the one item under that key
        e = out.setdefault(k, dict(units=0, order_id=oid, vendor=vendor))
        e["units"] += int(got) * int(size or 1)
    return out


def _s470_inputs(con, today):
    pa = _pa()
    sp = _s470_spine()
    try:
        as_on, snap, missing = _s470_snap(con, pa, sp)
        basis = _s454_basis(con)
        if basis == "count":                                     # the shelf figure, untouched; Marg's (the spine's) kept beside it as marg_qty
            snap = _s454_shelf_snap(con, snap)
        pace = _s470_pace(sp, snap, today, _s470_days(con, "order.pace_days"))
        purch = _s470_purch(pa, sp, snap, today, _s470_days(con, "order.lot_history_days"))
        transit = _s470_arrivals(con, pa, sp, snap, today, _s470_days(con, "order.in_transit_days"))
    finally:
        try:
            sp.con.close()
        except Exception:                                        # noqa: BLE001
            pass
    if basis == "count":                                         # a counted item's arrival is inside its shelf figure
        transit = {k: v for k, v in transit.items() if "marg_qty" not in (snap.get(k) or {})}
    for k, e in _on_order_units(con, today, "count").items():    # sent, not yet arrived: on the way, counted as stock (as today)
        t = transit.setdefault(k, dict(units=0, order_id=e["order_id"], vendor=""))
        t["units"] = int(t.get("units") or 0) + e["units"]
        t["on_way"] = e
    ortho = {pa.norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")} if _has(con, "stock_item_section") else set()
    _S470.missing = sorted(m for m in missing if pa.norm(m) not in ortho)   # an orthotic is S403's, never this engine's
    return as_on, snap, pace, purch, transit, ortho


def _s470_missing():
    return list(getattr(_S470, "missing", None) or [])


_snapshot_inputs_before_s470 = _snapshot_inputs


def _snapshot_inputs(con, today):                                # noqa: F811
    """S470 (B.1): one setting decides the source. On spine the plan is made from the spine; on tables, or when the spine cannot be
    read, the old reads run exactly as they did -- and the plan says which made it."""
    _S470.missing = []
    if _s470_source(con) != "spine":
        _S470.engine = "tables"
        return _snapshot_inputs_before_s470(con, today)
    try:
        out = _s470_inputs(con, today)
        _S470.engine = "spine"
        return out
    except Exception as e:                                       # noqa: BLE001 -- ordering never stops for the spine
        _S470.engine = "tables (the spine could not be read: %s)" % (str(e) or type(e).__name__)[:120]
        return _snapshot_inputs_before_s470(con, today)


_line_out_before_s470 = _line_out


def _line_out(pa, s, it, line, cost_unit, p, why_extra=None):   # noqa: F811
    """S470 (B.5, B.6): the line carries its lot and free (read, used by no rail yet) and, for a family member, family = n."""
    lo = _line_out_before_s470(pa, s, it, line, cost_unit, p, why_extra)
    x = s.get("_s470")
    if x:
        lo["lot"], lo["free"] = x.get("lot"), x.get("free")
        if int(x.get("family") or 1) > 1:
            lo["family"] = int(x["family"])
    return lo
# ---- S470 end ---------------------------------------------------------------------------------------------------------------------------


