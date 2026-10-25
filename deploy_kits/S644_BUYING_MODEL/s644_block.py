

# ==========================================================================================================================================
# S644_BUYING_MODEL (25-Oct-2026, D678 built; brief S486 Part B as re-read by S308 and planned in claude/S350_KIT_II_PLAN.md): THE LEVELS
# MODEL BEHIND ONE SETTING.  order.model = fixed (the default: today's engine, line for line -- every hook below is a pass-through) |
# levels (five rules inside the existing plan() / interim_plan() / prepare_day / tick):
#   1 each supplier at ITS OWN RHYTHM (rhythm_mode learnt: due when today - last buy >= the interval learnt from its bill days, clamped
#     order.review_min_days..review_max_days, or the owner's review_days; rhythm_mode fixed = today's calendar -- Kedar, D626)
#   2 the shop's own LOTS (the median purchase lot of order.lot_history_days, rounded up to whole lots, capped by cover, one lot minimum;
#     a new medicine -- first bought within order.new_item_days -- one lot)
#   3 the RATE ends on the spine's last sale day, never today (long order.pace_days; short order.rate_short_days, counted when it sold on
#     order.rate_short_min_sell_days of them, capped at order.rate_short_cap_pct of the long rate); the list is MADE AGAIN once, before
#     order.relist_until, when any input moved (the sales day, the closing's day, the spine's build) and nobody touched it
#   4 the shelf keeps ONE LARGE SALE (the level is never below the largest single day's sale of order.big_day_days)
#   5 an order BETWEEN REVIEWS goes only when the stock will not last to the next review + lead + order.interim_margin_days
# The arithmetic is PURE (model_* below: no database, no clock); the kit's replay runs the same functions. Nothing of this reaches a staff
# screen: order.source is not written by this kit; the proposals carry `model`; the nightly rehearsal scores them per model (B.8).
# Charter (S308): B.6 'count it' is NOT built; B.5 'supplier not known' stays on the owner's fold; one lot (model_lot), one interval
# (model_interval, inside rhythm()), one days_left (S593); the interval is computed at read, the stored columns are display-only.
# ==========================================================================================================================================
S644_KEYS = ("order.model", "order.rate_short_days", "order.rate_short_cap_pct", "order.rate_short_min_sell_days", "order.big_day_days",
             "order.interim_margin_days", "order.relist_until", "order.new_item_days", "order.review_min_days", "order.review_max_days",
             "order.review_default_days")
SETTINGS.update({
    "order.model": ("fixed", "(S644) how the system's list is made: fixed = fixed order days, as before · levels = each supplier's own rhythm, the shop's lots, yesterday's sales"),
    "order.rate_short_days": ("7", "(S644) the short sale window, days, ending on the last sale day"),
    "order.rate_short_cap_pct": ("200", "(S644) the short rate counts up to this % of the long rate"),
    "order.rate_short_min_sell_days": ("3", "(S644) the short rate counts only when the item sold on this many of its days"),
    "order.big_day_days": ("28", "(S644) the shelf keeps the largest single day's sale of this many days (0 = off)"),
    "order.interim_margin_days": ("1", "(S644) a between-review order goes when the stock will not last to the next review + lead + this"),
    "order.relist_until": ("13:00", "(S644) an untouched list is made again when an input moves, until this time (HH:MM)"),
    "order.new_item_days": ("28", "(S644) a medicine first bought within this many days is new: one lot"),
    "order.review_min_days": ("2", "(S644) a learnt review interval is never shorter than this"),
    "order.review_max_days": ("30", "(S644) a learnt review interval is never longer than this"),
    "order.review_default_days": ("7", "(S644) the review interval while a supplier has fewer bill days than order.min_bills_for_rhythm"),
})
S470_KEYS = tuple(S470_KEYS) + S644_KEYS                         # the owner's settings card (porders_s454) reads this tuple
RULE_FIELDS = tuple(RULE_FIELDS) + ("rhythm_mode", "review_days")
S644_COLS = (("rhythm_mode", "TEXT"), ("review_days", "INTEGER"), ("bill_days90", "INTEGER"), ("rhythm_at", "TEXT"))
_S644 = _s470_threading.local()


# ------------------------------------------------------------------ the pure arithmetic (no database, no clock; the replay runs these)
def model_rate(daily_units, end, long_days, short_days, short_min_sell_days, short_cap_pct):
    """(rate, rate_long, rate_short, sell_days_long, sell_days_short, peak_long) from {date: net units} over two calendar windows that END
    on `end` (inclusive): the divisor is always the whole window (no in-stock correction -- the replay measured none)."""
    def win(w):
        u, sell, peak = 0.0, 0, 0.0
        for n in range(int(w)):
            q = float(daily_units.get(end - dt.timedelta(days=n), 0.0) or 0.0)
            u += q
            if q > 0:
                sell += 1
                peak = max(peak, q)
        return max(0.0, u) / float(w), sell, peak
    rl, sl, pk = win(long_days)
    rs, ss, _ = win(short_days)
    r = rl
    if ss >= int(short_min_sell_days) and rs > rl:
        r = min(rs, rl * float(short_cap_pct) / 100.0) if rl > 0 else rs
    return r, rl, rs, sl, ss, pk


def model_big_day(daily_units, end, days):
    """(units, date) of the largest single day's net sale in the `days` days ending on `end`; (0.0, None) when days is 0 or nothing sold."""
    best, on = 0.0, None
    for n in range(int(days or 0)):
        d = end - dt.timedelta(days=n)
        q = float(daily_units.get(d, 0.0) or 0.0)
        if q > best:
            best, on = q, d
    return best, on


def model_lot(purchase_lines, as_of, history_days):
    """The usual lot in UNITS: the median of the bought units of the PURCHASE lines dated within history_days before as_of (inclusive);
    None with no line. purchase_lines: [(date, units)] with units > 0 for a purchase."""
    since = as_of - dt.timedelta(days=int(history_days))
    lots = [float(u) for d, u in purchase_lines if u and float(u) > 0 and since <= d <= as_of]
    return statistics.median(lots) if lots else None


def model_interval(bill_dates, as_of, min_bill_days, default_days, lo, hi):
    """(interval, median_gap, bill_days) from a supplier's distinct bill days up to as_of: the median gap rounded half-up, clamped lo..hi;
    default_days while there are fewer than min_bill_days bill days (or a single one). median_gap is None with fewer than two days."""
    ds = sorted({d for d in bill_dates if d is not None and d <= as_of})
    gaps = [(b - a).days for a, b in zip(ds, ds[1:])]
    med = statistics.median(gaps) if gaps else None
    if len(ds) < int(min_bill_days) or med is None:
        iv = int(default_days)
    else:
        iv = int(math.floor(float(med) + 0.5))
    return max(int(lo), min(int(hi), iv)), med, len(ds)


def model_cap_days(interval, cap_weekly, cap_fortnightly, cap_monthly):
    return int(cap_weekly) if interval <= 7 else (int(cap_fortnightly) if interval <= 14 else int(cap_monthly))


def model_level(rate, cover_days, big_day_units):
    """The shelf's level in units: rate x cover, never below the largest day's sale."""
    return max(float(rate) * float(cover_days), float(big_day_units or 0.0))


def model_qty(need_units, lot_units, on_hand_units, rate, cap_days, is_new):
    """Units to order in whole lots: at least one lot; a new item one lot; else need rounded up to lots, then the cap as a LIMIT -- the
    largest multiple of the lot that keeps (on_hand + q) / rate within cap_days, never below one lot. (units, notes). cap_days None = no cap."""
    lot = float(lot_units)
    notes = []
    if is_new:
        return lot, ["new medicine -- one lot"]
    q = math.ceil(float(need_units) / lot) * lot
    if q < lot:
        q = lot
    capped = False
    while cap_days is not None and q > lot and rate > 0 and (float(on_hand_units) + q) / float(rate) > float(cap_days):
        q -= lot
        capped = True
    if capped:
        notes.append("cut to the cover cap")
    if rate > 0 and cap_days is not None and (float(on_hand_units) + q) / float(rate) > float(cap_days):
        notes.append("one lot is more than the cover cap")
    return q, notes


def model_interim_due(on_hand_units, rate, days_to_next_review, lead_days, margin_days):
    """True when the stock will not last to the next review + lead + margin."""
    if rate <= 0:
        return False
    return float(on_hand_units) / float(rate) < float(days_to_next_review) + float(lead_days) + float(margin_days)


# ------------------------------------------------------------------ the setting, the columns, the rhythm at read
def _s644_on(con):
    return _setting(con, "order.model", "fixed") == "levels"


def _s644_learnt(con, r):
    """levels AND this supplier's rhythm is learnt (not fixed by the owner): the calendar follows last buy + interval."""
    return _s644_on(con) and str((r or {}).get("rhythm_mode") or "learnt") == "learnt"


def _s644_columns(con):
    """The four columns, lazily (idempotent). At their creation rhythm_mode is 'fixed' for every row whose cadence is custom or whose
    owner_fields hold order_days / cadence (Kedar: the owner's ruling of 26-Sep stays), 'learnt' for the rest."""
    have = {r[1] for r in con.execute("PRAGMA table_info(order_supplier_rule)")}
    fresh = "rhythm_mode" not in have
    for col, typ in S644_COLS:
        if col not in have:
            con.execute("ALTER TABLE order_supplier_rule ADD COLUMN %s %s" % (col, typ))
    if fresh:
        for r in con.execute("SELECT supplier_norm, cadence, owner_fields FROM order_supplier_rule").fetchall():
            of = set()
            try:
                of = set(json.loads(r[2] or "[]"))
            except (TypeError, ValueError):
                pass
            mode = "fixed" if (r[1] == "custom" or of & {"order_days", "cadence"}) else "learnt"
            con.execute("UPDATE order_supplier_rule SET rhythm_mode=? WHERE supplier_norm=?", (mode, r[0]))
        con.commit()


ensure_before_s644 = ensure


def ensure(con):                                              # noqa: F811
    ensure_before_s644(con)
    try:
        _s644_columns(con)
    except sqlite3.Error:
        pass


def _s644_rhythm(con, today):
    """rhythm(con, today) once per thread per minute (one spine read for a whole plan / tick), {supplier_norm: e}."""
    key = (today.isoformat(), dt.datetime.now().strftime("%H:%M"))
    if getattr(_S644, "rh_key", None) != key:
        _S644.rh, _S644.rh_key = rhythm(con, today), key
    return _S644.rh


def review_interval(con, r, today=None):
    """THE one interval of a supplier (days): the owner's review_days when set; else the interval rhythm() learnt (model_interval over its
    90 days of bill days, clamped); else the default. Computed at read -- the stored rhythm_days / bill_days90 are the owner's words only."""
    today = today or _today()
    lo, hi = _s470_days(con, "order.review_min_days"), _s470_days(con, "order.review_max_days")
    rd = r.get("review_days")
    if rd not in (None, "", 0, "0"):
        try:
            return max(lo, min(hi, int(rd)))
        except (TypeError, ValueError):
            pass
    e = _s644_rhythm(con, today).get(r.get("supplier_norm"))
    if e and e.get("interval"):
        return max(lo, min(hi, int(e["interval"])))
    return max(lo, min(hi, _s470_days(con, "order.review_default_days")))


def last_buy(con, r, before, today=None):
    """The newest day strictly before `before` this supplier was bought from: (a) a sent/received purchase_order that is not interim-only;
    (b) a sent order_proposal of kind fixed / darpan; only when neither is within review_max_days, (c) its newest bill day the spine holds.
    None = never (due)."""
    pa = _pa()
    sn = r["supplier_norm"]
    b = before.isoformat()
    best = None
    try:
        for oid, vendor, osn, created in con.execute("SELECT id, vendor, supplier_norm, substr(created_at,1,10) FROM purchase_order WHERE status IN ('sent','received') "
                                                     "AND substr(created_at,1,10)<? ORDER BY created_at DESC LIMIT 400", (b,)).fetchall():
            key = osn or (pa.supplier_key(vendor) if vendor else "")
            if key != sn:
                continue
            kinds = [x[0] for x in con.execute("SELECT kind FROM order_proposal WHERE sent_order_id=?", (oid,)).fetchall()]
            if kinds and all(k == "interim" for k in kinds):
                continue
            best = created
            break
        pr = con.execute("SELECT MAX(substr(sent_at,1,10)) FROM order_proposal WHERE supplier_norm=? AND status='sent' AND kind IN ('fixed','darpan') "
                         "AND substr(sent_at,1,10)<?", (sn, b)).fetchone()
        if pr and pr[0] and (best is None or pr[0] > best):
            best = pr[0]
    except sqlite3.Error:
        pass
    hi = _s470_days(con, "order.review_max_days")
    if best is None or (before - dt.date.fromisoformat(best)).days > hi:
        e = _s644_rhythm(con, today or _today()).get(sn)
        if e:
            ds = [d for d in e.get("dates") or [] if d and d < b]
            if ds and (best is None or max(ds) > best):
                best = max(ds)
    try:
        return dt.date.fromisoformat(best) if best else None
    except ValueError:
        return None


def _s644_allowed(con, r, d):
    hol = _holidays(con, d, d)
    return DOW[d.weekday()] not in (_blocked_set(r) | {"SUN"}) and d.isoformat() not in hol


def _s644_forward(con, r, d):
    """The first allowed day on or after d (at most 14 days on)."""
    n = 0
    while not _s644_allowed(con, r, d) and n < 14:
        d += dt.timedelta(days=1)
        n += 1
    return d


def _s644_due(con, r, d):
    if not _s644_allowed(con, r, d):
        return False
    lb = last_buy(con, r, d)
    return lb is None or (d - lb).days >= review_interval(con, r, d)


def _s644_next(con, r, after):
    lb = last_buy(con, r, after + dt.timedelta(days=1))
    iv = review_interval(con, r, after)
    start = after + dt.timedelta(days=1)
    if lb is not None:
        start = max(start, lb + dt.timedelta(days=iv))
    return _s644_forward(con, r, start)


def cap_days(con, r, today=None):
    """The cover cap of a learnt supplier: the row's own when the owner set it, else by its interval (weekly / fortnightly / monthly caps)."""
    if "cover_cap_days" in _owner_fields(r):
        return int(r.get("cover_cap_days") or 45)
    return model_cap_days(review_interval(con, r, today), _int_setting(con, "order.cap_weekly"), _int_setting(con, "order.cap_fortnightly"), _int_setting(con, "order.cap_monthly"))


is_order_day_before_s644 = is_order_day
next_order_day_before_s644 = next_order_day
gap_days_before_s644 = gap_days
cover_days_before_s644 = cover_days
rule_words_before_s644 = rule_words


def is_order_day(con, r, d):                                    # noqa: F811
    if _s644_learnt(con, r):
        return _s644_due(con, r, d)
    return is_order_day_before_s644(con, r, d)


def next_order_day(con, r, after):                              # noqa: F811
    if _s644_learnt(con, r):
        return _s644_next(con, r, after)
    return next_order_day_before_s644(con, r, after)


def gap_days(r, con=None, today=None):                          # noqa: F811
    """Fixed: 7 / 14 / 30 / the custom cycle as before. Levels + learnt (with con): the first allowed day on or after today + interval, minus today."""
    if con is not None and _s644_learnt(con, r):
        today = today or _today()
        iv = review_interval(con, r, today)
        return (_s644_forward(con, r, today + dt.timedelta(days=iv)) - today).days
    return gap_days_before_s644(r)


def cover_days(con, r, single_source, today=None):              # noqa: F811
    if not _s644_learnt(con, r):
        return cover_days_before_s644(con, r, single_source)
    c = gap_days(r, con, today) + int(r.get("lead_days") or 1) + int(r.get("safety_days") or 3)
    if single_source and int(r.get("single_source_extra") or 0):
        c += _int_setting(con, "order.single_source_extra_days")
    return min(c, cap_days(con, r, today))


def rule_words(con, r):                                         # noqa: F811
    s = rule_words_before_s644(con, r)
    if not _s644_on(con):
        return s
    if str(r.get("rhythm_mode") or "learnt") != "learnt":
        return s + " · fixed days (your ruling)"
    e = _s644_rhythm(con, _today()).get(r.get("supplier_norm")) or {}
    iv = review_interval(con, r)
    if r.get("review_days") not in (None, "", 0, "0"):
        how = "set by you"
    elif e.get("bill_days90", 0) >= _int_setting(con, "order.min_bills_for_rhythm") and e.get("gap") is not None:
        how = "learnt from %d bill days" % int(e["bill_days90"])
    else:
        how = "the default -- too few bills yet"
    return s + " · reviewed every %d day%s (%s), cap %d" % (iv, "" if iv == 1 else "s", how, cap_days(con, r))


# ------------------------------------------------------------------ the rate, the lot, the new item (hooks on the S470 reads)
_s470_pace_before_s644 = _s470_pace
_s470_purch_before_s644 = _s470_purch
_s470_inputs_before_s644 = _s470_inputs


def _s644_opts(con):
    """The model's numbers for this plan, read once; None on fixed."""
    if not _s644_on(con):
        return None
    return dict(short=_s470_days(con, "order.rate_short_days"), cap_pct=_s470_days(con, "order.rate_short_cap_pct", 100),
                min_sell=_s470_days(con, "order.rate_short_min_sell_days"), big=max(0, _int_setting(con, "order.big_day_days")),
                new=_s470_days(con, "order.new_item_days"), margin=max(0, _int_setting(con, "order.interim_margin_days")))


def _s470_pace(sp, snap, today, pace_days, opts=None):          # noqa: F811
    """S644: with opts (levels) the windows END on the spine's last sale day, never today; long = pace_days, short = opts['short'];
    the entry carries rate_long, rate_short, window_end, big_day, big_day_on. Without opts: S470's reads, untouched."""
    if not opts:
        return _s470_pace_before_s644(sp, snap, today, pace_days)
    try:
        lsd = sp.last_sale_day()
    except Exception:                                            # noqa: BLE001 -- an older spine_read: today - 1
        lsd = None
    end = today - dt.timedelta(days=1)
    if lsd:
        try:
            end = min(end, dt.date.fromisoformat(str(lsd)[:10]))
        except ValueError:
            pass
    reach = max(int(pace_days), int(opts["big"] or 0), int(opts["short"]))
    since = (end - dt.timedelta(days=reach)).isoformat()
    out, done = {}, {}
    for k, s in snap.items():
        x = s["_s470"]
        if x["key"] not in done:
            days = {}
            for r in sp.sales_daily(s["item"], since, end.isoformat()):
                try:
                    days[dt.date.fromisoformat(str(r["date"])[:10])] = float(r["units"] or 0)
                except ValueError:
                    pass
            done[x["key"]] = (days, sp.last_sale(s["item"]))
        days, ls = done[x["key"]]
        if not days and not ls:
            continue
        n = max(1, int(x["family"]))
        shared = {d: v / n for d, v in days.items()}
        rate, rl, rs, sl, ss, peak = model_rate(shared, end, pace_days, opts["short"], opts["min_sell"], opts["cap_pct"])
        tot = rl * pace_days
        bd, bd_on = model_big_day(shared, end, opts["big"]) if opts["big"] else (0.0, None)
        e = dict(rate_per_day=rate, sell_days=sl, peak_share=(peak / tot) if tot > 0 else 0.0, rate_long=round(rl, 4), rate_short=round(rs, 4),
                 sell_days_short=ss, window_end=end.isoformat(), big_day=bd, big_day_on=bd_on.isoformat() if bd_on else None)
        if n > 1:
            e["approx_shared"] = n
        if ls:
            try:
                e["days_since_sale"] = (today - dt.date.fromisoformat(ls["date"])).days
            except ValueError:
                e["days_since_sale"] = 999
        out[k] = e
    return out


def _s470_purch(pa, sp, snap, today, lot_days):                 # noqa: F811
    """S644: the lot through model_lot (THE one median; S470's own median line is retired into it) and first_buy -- the item's earliest
    PURCHASE line day (the new-item test). The other fields exactly as S470 read them."""
    out = _s470_purch_before_s644(pa, sp, snap, today, lot_days)
    done = {}
    for k, s in snap.items():
        e = out.get(k)
        if not e:
            continue
        x = s["_s470"]
        if x["key"] not in done:
            lines, first = [], None
            for l in sp.purchase_lines(s["item"]):
                if l["direction"] != "PURCHASE":
                    continue
                q = float(l["qty"] or 0)
                if q <= 0:
                    continue
                try:
                    d = dt.date.fromisoformat(str(l["date"])[:10])
                except ValueError:
                    continue
                first = d if first is None or d < first else first
                lines.append((d, q * s["pack_size"]))
            done[x["key"]] = (model_lot(lines, today, lot_days), first)
        lot, first = done[x["key"]]
        e["lot"], e["first_buy"] = lot, (first.isoformat() if first else None)
        x["lot"] = lot
    return out


def _s470_inputs(con, today):                                   # noqa: F811
    """S644: on levels the pace is model-aware (the windows end on the last sale day) -- one hook, the rest of S593's read untouched."""
    opts = _s644_opts(con)
    if not opts:
        return _s470_inputs_before_s644(con, today)
    _S644.opts = opts
    pa = _pa()
    SF = _s593_sf()
    sp = _s470_spine()
    sw = _s593_sw().Spine()
    ctx = SF._ctx(con, sw, None)
    try:
        as_on, snap, missing = _s470_snap(con, pa, sw, ctx, today)
        basis = _s454_basis(con)
        if basis == "count":
            snap = _s454_shelf_snap(con, snap, ctx)
        pace = _s470_pace(sp, snap, today, _s470_days(con, "order.pace_days"), opts)
        purch = _s470_purch(pa, sp, snap, today, _s470_days(con, "order.lot_history_days"))
        cap = SF.capture_at(sw, today.isoformat(), ctx) or {}
        try:
            built = str((sw.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or "")
        except Exception:                                        # noqa: BLE001
            built = ""
        note = dict(sales_through=str((SF._reach_once(sw, ctx) or {}).get("last_sale") or ""),
                    capture=dict(md5=str(cap.get("md5") or "")[:8], as_on=cap.get("as_on"), end_day=cap.get("end_day"), stamp=cap.get("stamp")),
                    spine_built=built, counted=sum(1 for s in snap.values() if "marg_qty" in s), marg=sum(1 for s in snap.values() if "marg_qty" not in s),
                    absent=sum(1 for s in snap.values() if (s.get("_s470") or {}).get("by") == "absent"), made_at=now_iso(), model="levels",
                    window_end=next((p.get("window_end") for p in pace.values() if p.get("window_end")), None))
    finally:
        for h in (sp, sw):
            try:
                h.con.close()
            except Exception:                                    # noqa: BLE001
                pass
    transit = {}
    for k, e in _on_order_units(con, today, "count").items():
        t = transit.setdefault(k, dict(units=0, order_id=e["order_id"], vendor=""))
        t["units"] = int(t.get("units") or 0) + e["units"]
        t["on_way"] = e
    ortho = {pa.norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")} if _has(con, "stock_item_section") else set()
    _S470.missing = sorted(m for m in missing if pa.norm(m) not in ortho)
    _S470.inputs = note
    _S593_INPUTS["val"] = note
    return as_on, snap, pace, purch, transit, ortho


_on_order_units_before_s644 = _on_order_units


def _on_order_units(con, today, basis=None):                    # noqa: F811
    """S644 (B.4): on levels a sent order's unanswered lines count as stock while they are within max(order.on_order_days, the supplier's
    interval + lead) of its own supplier -- the same rows, read with the vendor, kept per supplier. Fixed: S470's read."""
    if not _s644_on(con):
        return _on_order_units_before_s644(con, today, basis)
    pa = _pa()
    base = _s470_days(con, "order.on_order_days")
    far = (today - dt.timedelta(days=_s470_days(con, "order.review_max_days") + 7)).isoformat()
    out = {}
    try:
        rows = con.execute("SELECT l.item, l.packs, l.pack_size, o.id, o.created_at, o.vendor, o.supplier_norm FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                           "WHERE (o.status='sent'" + (_s454_or_arrived(con) if basis != "count" else _s454_not_tied(con)) + ") AND o.created_at>=? "
                           "AND l.supplied IS NULL AND COALESCE(l.missing,0)=0", (far,)).fetchall()
    except sqlite3.Error:
        return out
    cache = {}
    for item, packs, size, oid, created, vendor, osn in rows:
        sn = osn or (pa.supplier_key(vendor) if vendor else "")
        if sn not in cache:
            r = rule_for(con, sn) if sn else {}
            cache[sn] = max(base, (review_interval(con, r, today) if r else 0) + int((r or {}).get("lead_days") or 1))
        try:
            age = (today - dt.date.fromisoformat(str(created)[:10])).days
        except ValueError:
            continue
        if age > cache[sn]:
            continue
        e = out.setdefault(pa.norm(item), dict(units=0, order_id=oid, sent=str(created or "")[:10]))
        e["units"] += int(packs or 0) * int(size or 1)
    return out


# ------------------------------------------------------------------ the quantity (the hook plan() calls after plan_line, before the rails)
def _s644_shape(con, s, it, p, lp, r, line, cov, dead_after, cost_unit):
    """On levels, for a line plan_line judged: the level with its floor, the need, the lot. Mutates `line` (order_strips, value_p, why,
    confirm, lot_based, and the model keys). On fixed: returns at once."""
    if not _s644_on(con):
        return
    pa = _pa()
    opts = getattr(_S644, "opts", None) or _s644_opts(con) or {}
    rate = float(p.get("rate_per_day") or 0)
    size = max(1, int(s["pack_size"] or 1))
    line["model"] = "levels"
    line["rate_long"], line["rate_short"] = p.get("rate_long"), p.get("rate_short")
    line["review_days"] = review_interval(con, r) if not r.get("_default") else None
    line["level_days"] = cov
    line["window_end"] = p.get("window_end")
    if rate <= 0:
        return
    big = float(p.get("big_day") or 0.0)
    level = model_level(rate, min(cov, pa.MAX_COVER_DAYS), big)
    on_hand = float(it["on_hand"])
    if line["order_strips"] <= 0:
        if line.get("why") or it.get("days_since_sale", 0) > (dead_after or pa.DEAD_AFTER_DAYS) or on_hand >= big or big <= 0:
            return                                             # not needed (plan_line's own judgment), dead, or no floor to meet
        line["why"] = list(line.get("why") or []) + ["kept for one large sale (%s on %s)" % (_qw(int(round(big)), s), _dmy(p.get("big_day_on")))]
    elif big > rate * min(cov, pa.MAX_COVER_DAYS):
        line["why"] = list(line.get("why") or []) + ["kept for one large sale (%s on %s)" % (_qw(int(round(big)), s), _dmy(p.get("big_day_on")))]
    need = max(0.0, level - on_hand)
    lot = (s.get("_s470") or {}).get("lot")
    fb = lp.get("first_buy")
    is_new = False
    if fb:
        try:
            is_new = (_today() - dt.date.fromisoformat(fb)).days <= int(opts.get("new", 28))
        except ValueError:
            is_new = False
    if not lot or float(lot) <= 0:
        if line["order_strips"] <= 0:                          # floor-listed, no lot: today's rails on the need
            line["order_strips"] = int(math.ceil(need / float(size)))
            line["value_p"] = int(line["order_strips"] * size * (cost_unit or 0))
        return
    cap = cap_days(con, r) if _s644_learnt(con, r) else int(r.get("cover_cap_days") or 45)
    q_units, notes = model_qty(need, float(lot), on_hand, rate, cap, is_new)
    strips = int(math.ceil(q_units / float(size)))
    if strips <= 0:
        return
    why = list(line.get("why") or [])
    why = [w for w in why if not w.startswith("rounded up from")]   # the lot replaces the box rounding
    if is_new:
        why.append("new medicine (first bought %s) -- one lot of %s" % (_dmy(fb), _qw(int(round(lot)), s)))
    elif strips != line["order_strips"]:
        why.append("usual lot %s: %s instead of %s" % (_qw(int(round(lot)), s), _qw(strips * size, s), _qw(line["order_strips"] * size, s)))
    for n in notes:
        if n == "one lot is more than the cover cap":
            line["confirm"] = True
            why.append("one lot is %s days of sale -- more than the cap of %d" % (("%.0f" % ((on_hand + q_units) / rate)) if rate > 0 else "?", cap))
        elif n == "cut to the cover cap":
            why.append("cut to the cover cap of %d days" % cap)
    fr = (s.get("_s470") or {}).get("free")
    if fr and float(fr) > 0:
        why.append("scheme: about %d free per 100 bought" % int(round(float(fr) * 100)))
    line["order_strips"], line["value_p"], line["why"], line["lot_based"] = strips, int(strips * size * (cost_unit or 0)), why, True
    line["lot_units"] = lot


def _s644_interim(con, r, s, p, on_hand, F, today, lead, safety):
    """(horizon, strips) for interim_plan. Fixed: today's test and arithmetic, line for line. Levels: fire only when the stock will not
    last to the next review + lead + margin; then size to the horizon (with safety) through the lot."""
    rate = float(p["rate_per_day"])
    horizon = (F - today).days + lead + safety
    if not _s644_on(con):
        cover = on_hand / rate
        if cover >= horizon:
            return horizon, 0
        need = rate * horizon - on_hand
        return horizon, int(math.ceil(need / float(s["pack_size"])))
    opts = getattr(_S644, "opts", None) or _s644_opts(con) or {}
    if not model_interim_due(on_hand, rate, (F - today).days, lead, opts.get("margin", 1)):
        return horizon, 0
    size = max(1, int(s["pack_size"] or 1))
    need = max(0.0, model_level(rate, horizon, float(p.get("big_day") or 0.0)) - on_hand)
    lot = (s.get("_s470") or {}).get("lot")
    if lot and float(lot) > 0:
        cap = cap_days(con, r) if _s644_learnt(con, r) else int(r.get("cover_cap_days") or 45)
        q, _ = model_qty(need, float(lot), on_hand, rate, cap, False)
        return horizon, int(math.ceil(q / float(size)))
    return horizon, int(math.ceil(need / float(size)))


def _s644_interim_keys(con, line, s, p):
    if _s644_on(con):
        line["model"] = "levels"
        line["rate_long"], line["rate_short"], line["window_end"] = p.get("rate_long"), p.get("rate_short"), p.get("window_end")
        if (s.get("_s470") or {}).get("lot"):
            line["lot_based"] = True


_line_out_before_s644 = _line_out


class _S644NoRound(object):
    """purchase_app with _staff_qty = identity: a lot-based line is NOT rounded to tens (the lot is the shop's own figure)."""
    def __init__(self, pa):
        self._pa = pa

    def __getattr__(self, name):
        if name == "_staff_qty":
            return lambda strips, unit: int(strips)
        return getattr(self._pa, name)


def _line_out(pa, s, it, line, cost_unit, p, why_extra=None):   # noqa: F811
    """S644: a lot-based line keeps its lot quantity (no 10-then-tens); the model keys ride on the row for the owner's eyes."""
    lo = _line_out_before_s644(_S644NoRound(pa) if line.get("lot_based") else pa, s, it, line, cost_unit, p, why_extra)
    for k in ("model", "rate_long", "rate_short", "review_days", "level_days", "window_end", "lot_based", "lot_units"):
        if k in line:
            lo[k] = line[k]
    if "model" not in lo:
        lo["model"] = "fixed"
    return lo


# ------------------------------------------------------------------ the day's stamp and the relist (B.2a, S308 v)
def _s644_stamp_of(note):
    if not note:
        return None
    cap = note.get("capture") or {}
    return json.dumps(dict(sales_through=note.get("sales_through") or "", end_day=cap.get("end_day") or "", spine_built=note.get("spine_built") or ""), sort_keys=True)


def _s644_stamp_day(con, today):
    """After prepare_day: the inputs the list was made from, in order_notice (slot made_through) -- on levels only."""
    if not _s644_on(con):
        return
    st = _s644_stamp_of(_s470_inputs_note())
    if not st:
        return
    con.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?) ON CONFLICT(day, slot) DO UPDATE SET text=excluded.text, at=excluded.at",
                (today.isoformat(), "made_through", st, None, now_iso()))
    con.commit()


def _s644_inputs_now(con, today):
    """The three stamps as they stand now, without a plan: one capture read, one reach read, one sp_meta read."""
    SF = _s593_sf()
    sw = _s593_sw().Spine()
    try:
        ctx = SF._ctx(con, sw, None)
        cap = SF.capture_at(sw, today.isoformat(), ctx) or {}
        reach = SF._reach_once(sw, ctx) or {}
        try:
            built = str((sw.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or "")
        except Exception:                                        # noqa: BLE001
            built = ""
        return json.dumps(dict(sales_through=str(reach.get("last_sale") or ""), end_day=cap.get("end_day") or "", spine_built=built), sort_keys=True)
    finally:
        try:
            sw.con.close()
        except Exception:                                        # noqa: BLE001
            pass


def _s644_untouched(con, today):
    """Nobody has touched today's list: every row open / held, no darpan row, no Darpan edit, no line edit on its rows, no call, no print."""
    t = today.isoformat()
    rows = con.execute("SELECT id, status, kind FROM order_proposal WHERE day=?", (t,)).fetchall()
    if any(r[1] not in ("open", "held") or r[2] == "darpan" for r in rows):
        return False
    try:
        if _has(con, "order_darpan_edit") and con.execute("SELECT 1 FROM order_darpan_edit WHERE day=? LIMIT 1", (t,)).fetchone():
            return False
        ids = [str(r[0]) for r in rows]
        if ids and _has(con, "s454_line_edit") and con.execute("SELECT 1 FROM s454_line_edit WHERE src='proposal' AND ref IN (%s) LIMIT 1" % ",".join("?" * len(ids)), ids).fetchone():
            return False
        if _has(con, "purchase_audit") and con.execute("SELECT 1 FROM purchase_audit WHERE substr(at,1,10)=? AND action IN ('s454_call','s454_sheet_printed','s454_marg_pdf_printed','s454_whatsapp_sent','s454_ordered','order_made_s454') LIMIT 1", (t,)).fetchone():
            return False
    except sqlite3.Error:
        return False
    return True


def _s644_relist(con, today, now):
    """Every tick before order.relist_until, on levels: when the day's stamp differs from the inputs now and the list is untouched, the list is
    made again -- rows UPDATED in place by (day, supplier, kind), never deleted; a supplier no longer in the plan keeps its row; the stamp
    moves. A touched list with moved inputs is marked stale for the owner's fold (slot stale). Returns a word for the log."""
    if not _s644_on(con):
        return "off"
    t = today.isoformat()
    until = _setting(con, "order.relist_until", "13:00")
    if now.strftime("%H:%M") >= until:
        return "past %s" % until
    st = con.execute("SELECT text FROM order_notice WHERE day=? AND slot='made_through'", (t,)).fetchone()
    if not st:
        return "no list yet"
    try:
        cur = _s644_inputs_now(con, today)
    except Exception as e:                                       # noqa: BLE001
        return "inputs unreadable: %s" % str(e)[:60]
    if cur == st[0]:
        return "same"
    if not _s644_untouched(con, today):
        con.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?) ON CONFLICT(day, slot) DO UPDATE SET text=excluded.text, at=excluded.at",
                    (t, "stale", "the list was touched before newer inputs landed: " + cur, None, now_iso()))
        con.commit()
        return "touched -- stale"
    due = [r["supplier_norm"] for r in rules(con) if is_order_day(con, r, today)]
    fixed = plan(con, today, suppliers=set(due)) if due else dict(vendors={})
    ip = interim_plan(con, today)
    n = 0
    for kind, vendors in (("fixed", fixed.get("vendors") or {}), ("interim", ip.get("vendors") or {})):
        for vn, v in vendors.items():
            if kind == "fixed" and vn not in due:
                continue
            status = "held" if (v.get("held") or v.get("paused")) else "open"
            reason = v.get("paused") or v.get("held") or ("Beech ka order -- agla %s order %s ko" % (_short(v["vendor"]), _dmy(v["next_order_day"])) if kind == "interim" else "")
            row = con.execute("SELECT id, status FROM order_proposal WHERE day=? AND supplier_norm=? AND kind=?", (t, vn, kind)).fetchone()
            if row:
                if row[1] not in ("open", "held"):
                    continue
                con.execute("UPDATE order_proposal SET lines=?, total_p=?, reason=?, status=?, prepared_at=? WHERE id=?",
                            (json.dumps(v["lines"], ensure_ascii=False), v["total_p"], reason, status, now_iso(), row[0]))
            else:
                con.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, reason, prepared_at) VALUES (?,?,?,?,?,?,?,?,?)",
                            (t, vn, v["vendor"], kind, status, json.dumps(v["lines"], ensure_ascii=False), v["total_p"], reason, now_iso()))
            n += 1
    new_st = _s644_stamp_of(_s470_inputs_note()) or cur
    con.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?) ON CONFLICT(day, slot) DO UPDATE SET text=excluded.text, at=excluded.at",
                (t, "made_through", new_st, None, now_iso()))
    con.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?) ON CONFLICT(day, slot) DO UPDATE SET text=excluded.text, at=excluded.at",
                (t, "relist", "made again at %s: %d rows, inputs %s" % (now.strftime("%H:%M"), n, new_st), None, now_iso()))
    con.commit()
    return "relisted %d" % n


# ------------------------------------------------------------------ the owner's fold (api/rules/state gains `model`) and the field rules
owner_state_before_s644 = owner_state
set_rule_before_s644 = set_rule


def _s644_owner(con, today=None):
    today = today or _today()
    on = _s644_on(con)
    t = today.isoformat()
    out = dict(value="levels" if on else "fixed",
               words=("Levels -- each supplier's own rhythm, the shop's lots, yesterday's sales" if on else "Fixed days -- as before"),
               other=("fixed" if on else "levels"), other_words=("Fixed days -- as before" if on else "Levels -- each supplier's own rhythm, the shop's lots, yesterday's sales"),
               settings=[dict(key=k, value=_setting(con, k, ""), note=SETTINGS[k][1]) for k in S644_KEYS], inputs=_s470_inputs_note(process=True))
    try:
        for slot in ("made_through", "relist", "stale"):
            r = con.execute("SELECT text, at FROM order_notice WHERE day=? AND slot=?", (t, slot)).fetchone()
            out[slot] = dict(text=r[0], at=r[1]) if r else None
    except sqlite3.Error:
        pass
    try:
        import porders_s454                                      # noqa: PLC0415 -- beside this file; the score line is its (S470)
        out["score"] = porders_s454._s470_score_line()
    except Exception:                                            # noqa: BLE001
        out["score"] = ""
    if on:
        rows = []
        for r in rules(con):
            e = _s644_rhythm(con, today).get(r["supplier_norm"]) or {}
            rows.append(dict(supplier=r["short"], mode=r.get("rhythm_mode") or "learnt", interval=review_interval(con, r, today),
                             bill_days90=e.get("bill_days90", r.get("bill_days90")), median_gap=e.get("gap"), last_buy=(last_buy(con, r, today) or dt.date(1970, 1, 1)).isoformat() if _s644_learnt(con, r) else None,
                             next=next_order_day(con, r, today - dt.timedelta(days=1)).isoformat(), cap=cap_days(con, r, today)))
        out["rhythm"] = rows
    return out


def owner_state(con, today=None):                               # noqa: F811
    d = owner_state_before_s644(con, today)
    try:
        d["model"] = _s644_owner(con, today)
    except Exception as e:                                       # noqa: BLE001 -- the fold never breaks the page
        d["model"] = dict(value=_setting(con, "order.model", "fixed"), error=str(e)[:120])
    return d


def set_rule(con, who, supplier_norm, field, value):            # noqa: F811
    """S644: two more fields -- rhythm_mode (learnt | fixed) and review_days (blank = learnt, else review_min..review_max). The rest as before."""
    if field not in ("rhythm_mode", "review_days"):
        return set_rule_before_s644(con, who, supplier_norm, field, value)
    ensure(con)
    r = con.execute("SELECT * FROM order_supplier_rule WHERE supplier_norm=?", (supplier_norm,)).fetchone()
    if not r:
        return dict(ok=False, error="no_such_supplier"), 404
    r = dict(r)
    if field == "rhythm_mode":
        v = str(value or "").strip().lower()
        if v not in ("learnt", "fixed"):
            return dict(ok=False, error="bad_value", message="learnt or fixed"), 400
    else:
        sv = str(value if value is not None else "").strip()
        if sv == "":
            v = None
        else:
            try:
                v = int(sv)
            except ValueError:
                return dict(ok=False, error="bad_value", message="blank, or a whole number of days"), 400
            lo, hi = _s470_days(con, "order.review_min_days"), _s470_days(con, "order.review_max_days")
            if not (lo <= v <= hi):
                return dict(ok=False, error="bad_value", message="%d to %d days, or blank" % (lo, hi)), 400
    owner = _owner_fields(r) | {field}
    _audit(con, who, supplier_norm, field, r.get(field), v)
    con.execute("UPDATE order_supplier_rule SET %s=?, owner_fields=?, updated_at=? WHERE supplier_norm=?" % field, (v, json.dumps(sorted(owner)), now_iso(), supplier_norm))
    con.commit()
    nr = dict(con.execute("SELECT * FROM order_supplier_rule WHERE supplier_norm=?", (supplier_norm,)).fetchone())
    return dict(ok=True, supplier=supplier_norm, changed={field: v}, words=rule_words(con, nr)), 200


reseed_before_s644 = reseed


def reseed(con, today=None, who="seed"):                        # noqa: F811
    """S644: after the seed, the display columns bill_days90 and rhythm_at (the stored rhythm_days stays reseed's); rhythm_mode is never
    rewritten here (its seeding is the columns' creation, once)."""
    n = reseed_before_s644(con, today, who)
    _s644_refresh_columns(con, today)
    return n


def _s644_refresh_columns(con, today=None):
    """The display columns bill_days90 and rhythm_at from one rhythm() read (the installer runs it once; reseed on the 1st). Fail-soft."""
    try:
        rh = rhythm(con, today or _today())
        for sn, e in rh.items():
            con.execute("UPDATE order_supplier_rule SET bill_days90=?, rhythm_at=? WHERE supplier_norm=?", (e.get("bill_days90"), now_iso(), sn))
        con.commit()
        return len(rh)
    except Exception:                                            # noqa: BLE001
        return 0
# ---- S644 end ---------------------------------------------------------------------------------------------------------------------------
