#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  shelf_figure.py  ·  v1.0  ·  kit S454_BILL_REGISTER (part 3)  ·  Session 283 (Sanjeevni)  ·  D667 / F-696
#
#  ONE SHELF FIGURE (S454 9.1). The owner, 03-Oct-2026: "The order quantities worked out from 6 September count becomes a norm for future
#  stock, stock check flow also." For every item:
#       its newest physical count  +  purchases  -  sales  +  returns since that count  +  what has arrived and is not yet in Marg
#    * the newest count: the latest of a spot-count answer / "Stock batao" (stock_point, any source but the full count's own copy) and the
#      item's row in a full count -- the whole count family (stock_count, its parts in stock_count_part, the desk's corrections in
#      stock_shelf_fix: the latest winning);
#    * movements by the spine's item key (stock_watch.Spine.key: the 20-character clip with the spine's aliases), with the boundary the
#      orthotic shelf uses: the count day's sales in, its purchases out (sales date >= the count day, purchases date > the count day);
#      the spine's sale units already net the returns;
#    * arrived, not yet in Marg: tapped arrivals the spine does not carry (stock_watch._arrivals) and orders that arrived by a bill's scan
#      (S454 4.4: order_scan_tie.arrived) whose lines Marg has not answered;
#    * items that share one spine key are split as the orthotic shelf splits them (by their counted share) and marked approximate;
#    * an item with no count keeps Marg's figure (named 'no_count'); a result below zero is taken as zero (named 'below_zero').
#  Base units (tabs / pieces), the pack size beside. One function, in one place: figures(). Read only.
# =============================================================================
import datetime as dt
import os
import re
import sqlite3
import sys

VERSION = "1.0"
KIT = "S454_BILL_REGISTER"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
FULL = "full_count"


def _sw():
    import stock_watch                                        # noqa: PLC0415 -- beside this file; no stock_app import at module level there
    return stock_watch


def _pa():
    import purchase_app                                       # noqa: PLC0415
    return purchase_app


def today():
    v = os.environ.get("ORDER_TODAY", "")
    try:
        return dt.date.fromisoformat(v) if v else dt.date.today()
    except ValueError:
        return dt.date.today()


def dmy_iso(s):
    s = str(s or "").strip()
    m = re.match(r"^(\d\d)-(\d\d)-(\d{4})$", s)
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else s[:10]


def _has(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None


def latest_snapshot(con):
    """(as_on iso, {item: dict(qty, packing, pack_size)}) -- Marg's newest closing stock."""
    if not _has(con, "stock_snapshot"):
        return None, {}
    ds = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
    if not ds:
        return None, {}
    as_on = max(ds, key=lambda d: dmy_iso(d))
    return dmy_iso(as_on), {r[0]: dict(qty=int(r[1] or 0), packing=r[2] or "", pack_size=max(1, int(r[3] or 1)))
                            for r in con.execute("SELECT item, qty, packing, pack_size FROM stock_snapshot WHERE as_on=?", (as_on,))}


def count_family(con):
    """{item: dict(qty, day iso, at, count_id, fixed)} -- the newest full count's row of every item: the count's own figure, its parts',
    and the desk's corrections (stock_shelf_fix), the latest winning."""
    out = {}
    if not _has(con, "stock_count_item"):
        return out
    try:
        parts = {}
        if _has(con, "stock_count_part"):
            parts = {int(r[0]): int(r[1]) for r in con.execute("SELECT count_id, part_of FROM stock_count_part")}
        counts = [dict(id=int(r[0]), day=dmy_iso(r[1]), at=str(r[2] or "")) for r in
                  con.execute("SELECT id, marg_as_on, COALESCE(submitted_at, started_at) FROM stock_count WHERE status='submitted' ORDER BY id")]
    except sqlite3.Error:
        return out
    for c in counts:
        for item, qty, at, mq in con.execute("SELECT item, counted_qty, at, marg_qty FROM stock_count_item WHERE count_id=? AND counted_qty IS NOT NULL", (c["id"],)):
            prev = out.get(item)
            stamp = (c["day"], str(at or c["at"]))
            if prev is None or stamp >= (prev["day"], prev["at"]):
                out[item] = dict(qty=float(qty), day=c["day"], at=str(at or c["at"]), count_id=parts.get(c["id"], c["id"]), fixed=False,
                                 marg0=(float(mq) if mq is not None else None))
    if _has(con, "stock_shelf_fix"):
        for item, qty, at, cid in con.execute("SELECT item, qty, at, count_id FROM stock_shelf_fix ORDER BY at, id"):
            e = out.get(item)
            if e is not None and qty is not None and int(cid or 0) in (e["count_id"], 0):
                e.update(qty=float(qty), fixed=True, fixed_at=str(at))
    return out


def points(con):
    """{item_norm: dict(qty, at, source, item)} -- the newest stock point that is not the full count's own copy (spot, darpan, sales_test,
    receipt), settled or provisional."""
    out = {}
    if not _has(con, "stock_point"):
        return out
    for nm, item, at, qty, src in con.execute("SELECT item_norm, item, at, qty_units, source FROM stock_point WHERE source<>? ORDER BY at, id", (FULL,)):
        out[nm] = dict(qty=float(qty or 0), at=str(at), source=src, item=item)
    return out


def movements(sp, item, d_from, d_to, incl_from=True):
    """(sold, returned, bought) units of the item's spine key between two days. A credit note (bill CN...) is a return: the spine keeps its
    units positive, so it is told apart by its bill, as the orthotic shelf does. Purchases net of purchase returns; the count day's sales
    in (incl_from), its purchases out."""
    op = ">=" if incl_from else ">"
    k = sp.key(item)
    # the spine's own movement ledger (sp_move: SALE negative, SALE_RETURN positive, PURCHASE / PURCHASE_RETURN signed) -- the one its daily
    # check against Marg's closing uses; sp_purchase_line alone misses purchases some exports carry (e.g. PANSPED L on 03-Oct)
    r = sp.q("SELECT COALESCE(SUM(CASE WHEN kind='SALE' THEN -units ELSE 0 END),0) AS s, COALESCE(SUM(CASE WHEN kind='SALE_RETURN' THEN units ELSE 0 END),0) AS r "
             "FROM sp_move WHERE k20=? AND date %s ? AND date<=?" % op, k, d_from, d_to)
    b = sp.q("SELECT COALESCE(SUM(CASE WHEN kind IN ('PURCHASE','PURCHASE_RETURN') THEN units ELSE 0 END),0) AS b FROM sp_move WHERE k20=? AND date>? AND date<=?",
             k, d_from, d_to)
    sold = float(r[0]["s"] or 0) if r else 0.0
    ret = float(r[0]["r"] or 0) if r else 0.0
    return sold, ret, (float(b[0]["b"] or 0) if b else 0.0)


BOUND_DAYS = 7


def boundary_purchases(con, sp, item, base_day, marg0, marg_now, marg_as_on, pack):
    """S454 9.1, the boundary: a purchase dated on (or up to BOUND_DAYS before) the count day that Marg did not carry yet at the count -- the bill
    entered after the count with an earlier date (PANSPED L: counted 0 at 14:41 on 06-09, its bill of 06-09 entered later; SHELCAL XT: a bill
    of 05-09). Marg's own figure at the count (marg0) tells: what Marg gained since the count beyond its sales, returns, later purchases and
    the count's vouchers filed. Such purchases are taken newest first while they fit that gain (one pack's tolerance). Units."""
    if marg0 is None or marg_now is None or not marg_as_on or not sp.ok or marg_as_on < base_day:
        return 0.0
    sold, ret, bought = movements(sp, item, base_day, marg_as_on)
    gain = float(marg_now) - (float(marg0) - sold + ret + bought) - filed_vouchers(con, item, base_day, marg_as_on)
    tol = float(max(1, pack))
    if gain < tol:
        return 0.0
    d0 = (dt.date.fromisoformat(base_day) - dt.timedelta(days=BOUND_DAYS)).isoformat()
    took = 0.0
    for r in sp.q("SELECT date, units FROM sp_move WHERE k20=? AND kind='PURCHASE' AND units>0 AND date>=? AND date<=? ORDER BY date DESC", sp.key(item), d0, base_day):
        u = float(r["units"] or 0)
        if took + u <= gain + tol:
            took += u
    return took


def scan_arrivals(con, sp, item, since_iso):
    """Units of orders that arrived by a bill's scan (S454 4.4) whose lines Marg has not answered and the spine does not carry."""
    if not _has(con, "order_scan_tie"):
        return 0.0
    sw = _sw()
    out = 0.0
    keys = {sw.pad_norm(item[:27]), sw.pad_norm(item)}
    try:
        rows = con.execute("SELECT l.item, l.packs, l.pack_size, o.vendor, o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                           "JOIN order_scan_tie t ON t.order_id=o.id WHERE t.arrived=1 AND l.supplied IS NULL AND l.billed_qty IS NULL AND COALESCE(l.missing,0)=0 "
                           "AND t.scan_at>?", (since_iso,)).fetchall()
    except sqlite3.Error:
        return 0.0
    for nm, packs, size, vendor, created in rows:
        if sw.pad_norm(str(nm)[:27]) not in keys and sw.pad_norm(nm) not in keys:
            continue
        if sp.ok:
            n = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", sp.key(item), sw.supkey(vendor), str(created)[:10])
            if n and n[0]["n"]:
                continue
        out += float(packs or 0) * float(size or 1)
    return out


def figures(con, sp=None, items=None, upto=None):
    """{item: dict(item, shelf, marg, pack_size, packing, base, base_kind, base_day, base_at, sold, bought, arrived, approx, named, key)}.
    items: the names to figure (default: Marg's newest closing plus the count's items). upto: the last day of movements (default today)."""
    sw = _sw()
    sp = sp or sw.Spine()
    t = (upto or today()).isoformat() if not isinstance(upto, str) else upto
    as_on, snap = latest_snapshot(con)
    fam = count_family(con)
    pts = points(con)
    names = list(items) if items is not None else sorted(set(snap) | set(fam))
    rows = {}
    for nm in names:
        s = snap.get(nm) or {}
        info = sw.item_info(con, sp, nm) if not s else dict(pack=s["pack_size"], packing=s["packing"])
        base, kind, day, at, marg0 = None, None, None, None, None
        f = fam.get(nm)
        if f:
            base, kind, day, at, marg0 = f["qty"], "count", f["day"], f["at"], f.get("marg0")
        p = pts.get(sw.norm_name(nm))
        if p and (day is None or p["at"][:10] > day or (p["at"][:10] == day and p["at"] > (at or ""))):
            base, kind, day, at, marg0 = p["qty"], p["source"], p["at"][:10], p["at"], None
        rows[nm] = dict(item=nm, key=(sp.key(nm) if sp.ok else nm[:20]), marg=(s.get("qty") if s else None), marg_as_on=as_on,
                        pack_size=int(s.get("pack_size") or info.get("pack") or 1), packing=s.get("packing") or info.get("packing") or "",
                        base=base, base_kind=kind, base_day=day, base_at=at, sold=0.0, returned=0.0, bought=0.0, arrived=0.0, approx=False, named=None, shelf=None,
                        marg0=marg0, boundary=0.0)
    # the families: items that share one spine key share its movements, split by their counted share
    by_key = {}
    for r in rows.values():
        by_key.setdefault(r["key"], []).append(r)
    for key, members in by_key.items():
        counted = [m for m in members if m["base"] is not None]
        if not counted or not sp.ok:
            for m in members:
                m["shelf"] = m["marg"]
                m["named"] = "no_count" if m["base"] is None else "no_spine"
            continue
        day = min(m["base_day"] for m in counted)
        sold, ret, bought = movements(sp, members[0]["item"], day, t)
        tot = sum(max(0.0, m["base"]) for m in counted)
        n = len(counted)
        for m in counted:
            share = (max(0.0, m["base"]) / tot) if tot > 0 else 1.0 / n
            arr = sum(a["units"] for a in sw._arrivals(con, m["item"], m["base_day"], sp) if not a["in_spine"]) + scan_arrivals(con, sp, m["item"], m["base_day"])
            if n > 1 and len({x["base_day"] for x in counted}) > 1:
                # different base days inside one key: each member's own window, pooled sales split by share
                s2, r2, b2 = movements(sp, m["item"], m["base_day"], t)
                m["sold"], m["returned"], m["bought"] = round(share * s2, 2), round(share * r2, 2), round(share * b2, 2)
            else:
                m["sold"], m["returned"], m["bought"] = round(share * sold, 2), round(share * ret, 2), round(share * bought, 2)
            m["arrived"] = arr
            if n == 1 and m["base_kind"] == "count":                # S454 9.1: a bill dated before the count, entered after it
                m["boundary"] = boundary_purchases(con, sp, m["item"], m["base_day"], m["marg0"], m["marg"], as_on, m["pack_size"])
            v = m["base"] - m["sold"] + m["returned"] + m["bought"] + m["boundary"] + arr
            m["approx"] = n > 1
            if v < 0:
                m["named"], v = "below_zero", 0.0
            m["shelf"] = int(round(v))
        for m in members:
            if m["base"] is None:
                m["shelf"], m["named"] = m["marg"], "no_count"
    return rows


# ------------------------------------------------------------------ S454 9.3: Marg's daily stock beside the shelf figure
GAP_DDL = ("CREATE TABLE IF NOT EXISTS s454_shelf_gap (as_on TEXT NOT NULL, item TEXT NOT NULL, shelf REAL, marg REAL, gap REAL, marg_move REAL, "
           "voucher REAL, base_day TEXT, pack INTEGER, approx INTEGER NOT NULL DEFAULT 0, flagged INTEGER NOT NULL DEFAULT 0, why TEXT, at TEXT NOT NULL, "
           "PRIMARY KEY (as_on, item))")


def _setting(con, key, default):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return str(r[0]).strip() if r and r[0] not in (None, "") else default
    except sqlite3.Error:
        return default


def filed_vouchers(con, item, d_from, d_to):
    """Units of the count's vouchers for this item that Amir filed in Marg between two closings (stock_voucher_line by round and batch,
    stock_voucher_entered.entered_on) -- the change Marg is EXPECTED to show without a sale or a purchase."""
    if not (_has(con, "stock_voucher_line") and _has(con, "stock_voucher_entered")):
        return 0.0
    try:
        r = con.execute("SELECT COALESCE(SUM(l.change),0) FROM stock_voucher_line l JOIN stock_voucher_entered e ON e.count_id=l.count_id AND e.round_no=l.round_no "
                        "AND e.kind=l.kind AND e.batch_no=l.batch_no WHERE l.item=? AND e.entered_on>? AND e.entered_on<=?", (item, d_from, d_to)).fetchone()
        return float(r[0] or 0)
    except sqlite3.Error:
        return 0.0


def record_gaps(con, sp=None):
    """At each new closing-stock report: for each item the gap between the shelf figure (movements up to that closing day) and Marg's.
    A gap that changes with no voucher -- Marg moved by more (or less) than its own sales, purchases and the vouchers Amir filed -- is a
    movement one side has and the other has not: flagged (never an approximate item; never a change under stock.gap_min_packs packs).
    On the count day the gap is the count's own correction; it stays until Amir files that item's voucher, and then closes by it.
    Idempotent: one set of rows per closing. Returns the rows written (0 when this closing is recorded already)."""
    con.execute(GAP_DDL)
    as_on, snap = latest_snapshot(con)
    if not as_on or con.execute("SELECT 1 FROM s454_shelf_gap WHERE as_on=? LIMIT 1", (as_on,)).fetchone():
        return 0
    sw = _sw()
    sp = sp or sw.Spine()
    prev = con.execute("SELECT MAX(as_on) FROM s454_shelf_gap WHERE as_on<?", (as_on,)).fetchone()[0]
    prow = {r[0]: dict(marg=r[1], gap=r[2], base_day=r[3], flagged=r[4], why=r[5]) for r in
            con.execute("SELECT item, marg, gap, base_day, flagged, why FROM s454_shelf_gap WHERE as_on=?", (prev,))} if prev else {}
    try:
        mins = float(_setting(con, "stock.gap_min_packs", "1"))
    except ValueError:
        mins = 1.0
    F = figures(con, sp=sp, items=list(snap), upto=as_on)
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    n = 0
    for item, s in snap.items():
        f = F.get(item) or {}
        if f.get("shelf") is None or f.get("named") in ("no_count", "no_spine"):
            continue
        gap = float(f["shelf"]) - float(s["qty"])
        p = prow.get(item)
        flagged, why, move, vch = 0, None, None, None
        if p and p.get("marg") is not None and sp.ok:
            sold, ret, bought = movements(sp, item, prev, as_on, incl_from=False)
            move = float(s["qty"]) - float(p["marg"]) - (bought - sold + ret)    # Marg's change its own sales, returns and purchases do not explain
            vch = filed_vouchers(con, item, prev, as_on)
            thr = mins * (s["pack_size"] if s["pack_size"] > 1 else 1)
            if f.get("approx"):
                why = "approximate (one spine key, several items) -- never flagged"
            elif p.get("base_day") != f.get("base_day"):
                why = "a new count since the last closing (rebased)"
            elif abs(move - vch) >= thr and thr > 0:
                flagged = 1
                why = "Marg moved %+g beyond its own sales and purchases on %s%s" % (round(move, 1), as_on, (" (vouchers filed: %+g)" % vch) if vch else " with no voucher filed")
            elif p.get("flagged"):                            # it stays flagged until the item is counted again (a new base)
                flagged, why = 1, p.get("why")
        con.execute("INSERT OR REPLACE INTO s454_shelf_gap (as_on, item, shelf, marg, gap, marg_move, voucher, base_day, pack, approx, flagged, why, at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (as_on, item, f["shelf"], s["qty"], gap, move, vch, f.get("base_day"), s["pack_size"],
                                                            int(bool(f.get("approx"))), flagged, why, now))
        n += 1
    con.commit()
    return n


def gap_flags(con):
    """(as_on, [dict(item, gap, marg_move, why)]) -- the items flagged at the newest recorded closing."""
    try:
        con.execute(GAP_DDL)
        as_on = con.execute("SELECT MAX(as_on) FROM s454_shelf_gap").fetchone()[0]
        if not as_on:
            return None, []
        return as_on, [dict(item=r[0], gap=r[1], marg_move=r[2], why=r[3]) for r in
                       con.execute("SELECT item, gap, marg_move, why FROM s454_shelf_gap WHERE as_on=? AND flagged=1 ORDER BY item", (as_on,))]
    except sqlite3.Error:
        return None, []


def gap_flag(con, item_norm):
    """1 when the item (stock_watch.norm_name) is flagged at the newest recorded closing -- one more reason on the spot-count roster."""
    _as_on, fl = gap_flags(con)
    sw = _sw()
    return 1 if any(sw.norm_name(x["item"]) == item_norm for x in fl) else 0


def gap_line(con):
    """The owner's one line: the count of such items and their names."""
    as_on, fl = gap_flags(con)
    if not fl:
        return None
    return dict(cls="info", target="porders", text="Marg and the shelf figure moved apart on %d item%s (closing of %s): %s -- they go up Darpan's spot-count list"
                % (len(fl), "" if len(fl) == 1 else "s", "%s-%s" % (as_on[8:10], as_on[5:7]), ", ".join(x["item"] for x in fl[:8])))


def shelf_map(con, names):
    """{item: shelf figure} for a count about to be recorded -- worked out BEFORE the count becomes the newest base (stock_app)."""
    try:
        F = figures(con, items=[n for n in names if n])
        return {k: v["shelf"] for k, v in F.items()}
    except Exception:                                         # noqa: BLE001 -- a count is never refused for it
        return {}


def boundary_report(con):
    """S454 9.1: counts whose clock time makes the boundary (the count day's sales in) wrong -- a base taken after the shop opened
    (09:00 IST) on a day that already had sales before it."""
    out = []
    sw = _sw()
    sp = sw.Spine()
    seen = set()
    for item, f in count_family(con).items():
        key = (f["day"], f["at"][11:16])
        if key in seen:
            continue
        seen.add(key)
        hh = f["at"][11:16]
        if hh and hh > "09:00":
            n = sp.q("SELECT COUNT(DISTINCT bill) AS n FROM sp_sale_line WHERE date=?", f["day"]) if sp.ok else []
            out.append(dict(kind="count", day=f["day"], at=f["at"], sales_that_day=(n[0]["n"] if n else None)))
    if _has(con, "stock_point"):
        for at, src, nm in con.execute("SELECT at, source, item FROM stock_point WHERE source<>? AND substr(at,12,5)>'09:00' ORDER BY at", (FULL,)):
            out.append(dict(kind=src, day=str(at)[:10], at=str(at), item=nm))
    return out
