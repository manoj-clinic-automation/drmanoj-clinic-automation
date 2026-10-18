#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s583.py -- kit S583_ARRIVALS_ONE_RULE: the builder. Anchored edits on the LIVE bytes of three files; no new file.

    python3 -B make_s583.py --finance /root/finance --out DIR

Every file is pinned (FROM md5, the brief's section 1); every anchor must occur exactly once in the live text, else STOP (exit 2, nothing
written). Writes DIR/stock_figure.py, DIR/shelf_figure.py, DIR/stock_watch.py and prints each md5 -- the installer compares them with PINS.sh.
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_figure.py": "cb5f24aacf7748752206619ce8bbb1e3",
    "shelf_figure.py": "a544afda07b4632e9bc05e97c256dde6",
    "stock_watch.py": "bc6885217a9f7ca7d8273021fcf6315a",
}
EQ = "# " + "=" * 77                                        # the header rule of every file in the estate (79 characters)

# =============================================================================================================== stock_figure.py
SF = []
SF.append(("F1 header: version line", '''#  stock_figure.py  ·  v1.0  ·  kit S577_STOCK_ON_SPINE  ·  Session 324 (Sanjeevni)  ·  rung 4b of the spine plan (Book 4A, 15F.1)
''', '''#  stock_figure.py  ·  v1.1  ·  kit S583_ARRIVALS_ONE_RULE  ·  Session 324 (Sanjeevni)  ·  rung 4b of the spine plan (Book 4A, 15F.1)
#  (v1.0 was S577_STOCK_ON_SPINE)
'''))
SF.append(("F2 header: who reads the arrivals", '''#  (stock_watch), the shelf-gap flags (shelf_figure), 'bill entry baaki' and the arrivals (stock_watch / shelf_figure, through key_of),
''', '''#  (stock_watch), the shelf-gap flags (shelf_figure), 'bill entry baaki' and the arrivals (stock_watch, through carried() here -- S583),
'''))
SF.append(("F3 header: the one arrival rule", '''#  stock_watch.expected_units, the PC's push_expected and marg_shadow run beside it for one witness week: `python3 stock_figure.py witness`.
''', '''#  stock_watch.expected_units, the PC's push_expected and marg_shadow run beside it for one witness week: `python3 stock_figure.py witness`.
#  THE ONE ARRIVAL RULE (S583, charter 2): carried() names the purchase of Marg's that carries a tapped or scan-tied order line -- (a) the
#  line's own Marg bill (billed_bill_no, S537); (b) a bill that answered ANOTHER line of the key never carries this one; (c) the order's own
#  vendor's bill dated up to arrival.back_days BEFORE the order day; (d) the own vendor's bill dated on or after the order day; (e) another
#  supplier's bill dated on or after the order day; the first eligible wins. expired() says the spine's purchase reach (reach(), read once per
#  Ctx) has passed the arrival moment by arrival.bill_grace_days -- ISO against ISO, never a raw 'YYYYMMDD-HHMMSS' compare (charter 11).
#  taps() and scan_arrivals() count a line while it is neither carried nor expired (a line with a billed_bill_no never counts);
#  arrivals_open() lists the expired ones -- the owner's Needs-you line (stock_watch.arrival_needs_you) for the scan-tied orders.
#  stock_watch._arrivals marks in_spine = carried() is not None and nothing else: a trace's finding 2 still sees a tap Marg never carried.
'''))
SF.append(("F4 version", '''VERSION = "1.0"
KIT = "S577_STOCK_ON_SPINE"
''', '''VERSION = "1.1"
KIT = "S583_ARRIVALS_ONE_RULE"                                 # v1.0 was S577_STOCK_ON_SPINE
'''))
SF.append(("F5 taps -> the arrival block (carried, expired, taps, scan_lines, scan_arrivals, arrivals_open)", '''def taps(con, sp, name, since_iso, ctx=None):
    """Tapped arrivals the spine does not carry (stock_watch._arrivals, in_spine by key_of) after a moment -- reported beside a figure,
    never added to Marg's."""
    ctx = _ctx(con, sp, ctx)
    try:
        return sum(float(a["units"] or 0) for a in _sw()._arrivals(ctx.con, name, since_iso, sp, ctx=ctx) if not a["in_spine"])
    except Exception:                                         # noqa: BLE001
        return 0.0
''', '''# ------------------------------------------------------------------ the arrivals: ONE rule for "Marg carries this arrival" (S583, charter 2)
def _arr_settings(con, ctx):
    """(arrival.bill_grace_days, arrival.back_days) through stock_watch.settings -- the one settings reader -- read once per Ctx."""
    if "arrset" not in ctx.c:
        g, b = 3, 2
        try:
            S = _sw().settings(con)
            g = int(S.get("bill_grace_days") or 3)
            b = int(S["back_days"]) if S.get("back_days") is not None else 2
        except Exception:                                     # noqa: BLE001
            pass
        ctx.c["arrset"] = (max(1, g), max(0, b))
    return ctx.c["arrset"]


def _reach_once(sp, ctx):
    """reach(sp) read once per Ctx (expired() reads the spine's purchase reach, never twice in one pass)."""
    if "reach" not in ctx.c:
        try:
            ctx.c["reach"] = reach(sp) if (sp is not None and getattr(sp, "ok", False)) else {}
        except Exception:                                     # noqa: BLE001
            ctx.c["reach"] = {}
    return ctx.c["reach"]


def _bill(b):
    return re.sub(r"\\s+", "", str(b or "")).upper()


def arrival_moment(line):
    """The arrival moment as a datetime (finance.db's clock, IST): a tapped line's arrived_at, a scan-tied line's scan_at. None when unreadable."""
    s = str(line.get("arrived_at") or line.get("scan_at") or "").strip().replace(" ", "T")[:19]
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _taken_bills(sp, k20, line_id, ctx):
    """{(supplier key, bill)} -- the billed_bill_no of every OTHER order line of the key, with its order's vendor key (rule b): Marg's answer to
    another line never carries this one. Read once per key and Ctx."""
    ck = ("taken", k20)
    if ck not in ctx.c:
        out = {}
        try:
            if ctx.con is not None:
                for lid, item, bno, vendor in ctx.con.execute("SELECT l.id, l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                                               "WHERE COALESCE(l.billed_bill_no,'')<>''"):
                    if key_of(sp, item, ctx) == k20:
                        out.setdefault((_sw().supkey(vendor), _bill(bno)), set()).add(int(lid))
        except sqlite3.Error:
            out = {}
        ctx.c[ck] = out
    me = {int(line_id)} if line_id is not None else set()
    return {k for k, ids in ctx.c[ck].items() if ids - me}


def _purchases_of(sp, k20, since_day, ctx):
    """The spine's PURCHASE bills of the key dated on or after since_day, oldest first: dict(supkey, bill, date, units, supplier) -- one row per
    bill (its lines of the key summed), the supplier's name from sp_purchase_bill when the spine has it."""
    ck = ("pur", k20, since_day)
    if ck not in ctx.c:
        try:
            rows = sp.q("SELECT l.supkey AS supkey, l.bill AS bill, l.date AS date, SUM(l.units) AS units, MAX(b.supplier) AS supplier FROM sp_purchase_line l "
                        "LEFT JOIN sp_purchase_bill b ON b.supkey=l.supkey AND b.bill=l.bill AND b.date=l.date "
                        "WHERE l.k20=? AND l.direction='PURCHASE' AND l.date>=? GROUP BY l.supkey, l.bill, l.date ORDER BY l.date, l.bill", k20, since_day)
        except sqlite3.Error:
            rows = sp.q("SELECT supkey, bill, date, SUM(units) AS units, supkey AS supplier FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE' AND date>=? "
                        "GROUP BY supkey, bill, date ORDER BY date, bill", k20, since_day)
        ctx.c[ck] = rows
    return ctx.c[ck]


def carried(con, sp, line, ctx=None):
    """THE ONE RULE: the purchase of Marg's that carries an arrival line, or None. `line` is the dict stock_watch._arrivals yields (line_id, item,
    vendor, order_at, arrived_at, billed_bill_no; scan_at for a scan-tied line). Returns dict(supplier, supkey, bill, date, units, how) -- `how`
    the rule's letter. None while sp.ok is False (the spine unread: nothing is dropped). In order:
      (a) the line's own billed_bill_no (Marg's answer, S537) -> carried, whatever the spine shows;
      (b) a purchase whose bill is the billed_bill_no of ANOTHER order line of the same key never carries this line;
      (c) a purchase dated BEFORE the order day carries only from the order's own vendor key, dated within arrival.back_days before the order day;
      (d) a purchase from the order's own vendor key dated on or after the order day carries (the rule before S583);
      (e) a purchase from another supplier carries only when dated on or after the order day.
    The first eligible purchase, oldest date first, wins. A carrying bill dated on or before the item's count day still drops the arrival: the goods
    are inside the count (the brief's named edge)."""
    ctx = _ctx(con, sp, ctx)
    if sp is None or not getattr(sp, "ok", False) or not isinstance(line, dict):
        return None
    ck = ("carried", line.get("line_id"), norm(line.get("item")), _sw().supkey(line.get("vendor")), str(line.get("order_at") or "")[:10], _bill(line.get("billed_bill_no")))
    if ck in ctx.c:
        return ctx.c[ck]
    try:
        out = _carried(ctx, sp, line)
    except sqlite3.Error:
        out = None
    ctx.c[ck] = out
    return out


def _carried(ctx, sp, line):
    sw = _sw()
    k = key_of(sp, line.get("item"), ctx)
    own = sw.supkey(line.get("vendor"))
    bno = _bill(line.get("billed_bill_no"))
    if bno:                                                   # (a)
        hit = [p for p in sp.q("SELECT supkey, bill, date, SUM(units) AS units FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE' GROUP BY supkey, bill, date ORDER BY date DESC", k)
               if _bill(p["bill"]) == bno]
        p = hit[0] if hit else {}
        return dict(supplier=str(line.get("vendor") or ""), supkey=str(p.get("supkey") or own), bill=str(line.get("billed_bill_no") or ""),
                    date=str(p.get("date") or line.get("billed_date") or "")[:10], units=(float(p["units"] or 0) if p else None), how="a")
    od = str(line.get("order_at") or "")[:10]
    try:
        lo = (dt.date.fromisoformat(od) - dt.timedelta(days=_arr_settings(ctx.con, ctx)[1])).isoformat()
    except ValueError:
        return None
    taken = _taken_bills(sp, k, line.get("line_id"), ctx)
    for p in _purchases_of(sp, k, lo, ctx):
        sk, d = str(p["supkey"] or ""), str(p["date"] or "")[:10]
        if (sk, _bill(p["bill"])) in taken:                   # (b)
            continue
        if d < od:
            how = "c" if (own and sk == own) else None        # (c)
        else:
            how = "d" if (own and sk == own) else "e"         # (d) / (e)
        if how:
            return dict(supplier=str(p.get("supplier") or sk), supkey=sk, bill=str(p["bill"] or ""), date=d, units=float(p["units"] or 0), how=how)
    return None


def expired(con, sp, line, ctx=None):
    """True when carried() is None AND the spine's purchase reach has passed the arrival with its grace (arrival.bill_grace_days): last_pur is at
    or past the arrival day + grace AND stamp_iso(pur_stamp) is after the arrival moment + grace -- two ISO shapes; never a raw compare of the
    'YYYYMMDD-HHMMSS' stamp against an ISO moment (charter 11). covers() is not used. False while sp.ok is False, the reach is empty or the
    moment is unreadable: the arrival keeps counting (charter 1b)."""
    ctx = _ctx(con, sp, ctx)
    if sp is None or not getattr(sp, "ok", False) or not isinstance(line, dict):
        return False
    if carried(con, sp, line, ctx) is not None:
        return False
    R = _reach_once(sp, ctx)
    if not R or not R.get("last_pur") or not stamp_iso(R.get("pur_stamp")):
        return False
    m = arrival_moment(line)
    if m is None:
        return False
    due = m + dt.timedelta(days=_arr_settings(ctx.con, ctx)[0])
    return str(R["last_pur"])[:10] >= due.date().isoformat() and stamp_iso(R["pur_stamp"]) > due.replace(microsecond=0).isoformat()


def taps(con, sp, name, since_iso, ctx=None):
    """Units of the item's tapped arrivals after a moment that COUNT: no billed_bill_no (rule a: Marg answered), carried() None (in_spine False)
    and expired() False. stock_watch._arrivals lists the lines. Reported beside Marg's figure, added to the shelf figure."""
    ctx = _ctx(con, sp, ctx)
    try:
        return sum(float(a["units"] or 0) for a in _sw()._arrivals(ctx.con, name, since_iso, sp, ctx=ctx)
                   if not str(a.get("billed_bill_no") or "").strip() and not a["in_spine"] and not expired(con, sp, a, ctx))
    except Exception:                                         # noqa: BLE001
        return 0.0


def scan_lines(con, sp, item=None, since_iso="", ctx=None):
    """The scan-tied, unanswered order lines (S454 4.4: order_scan_tie.arrived=1; supplied and billed_qty NULL, missing 0) whose scan moment is
    after since_iso -- of one item (matched as _arrivals matches an order line: pad_norm(name[:27]) / pad_norm(name); seen, not touched, charter
    12) or of every item (None). In _arrivals' shape: arrived_at = scan_at, arrived_by 'scan', units = packs x pack_size, kind 'scan'."""
    ctx = _ctx(con, sp, ctx)
    con = ctx.con
    if con is None or not _has(con, "order_scan_tie"):
        return []
    sw = _sw()
    keys = {sw.pad_norm(str(item)[:27]), sw.pad_norm(str(item))} if item else None
    out = []
    try:
        rows = con.execute("SELECT l.id, l.item, l.packs, l.pack_size, o.vendor, o.created_at, o.id, MAX(t.scan_at) FROM purchase_order_line l "
                           "JOIN purchase_order o ON o.id=l.order_id JOIN order_scan_tie t ON t.order_id=o.id "
                           "WHERE t.arrived=1 AND l.supplied IS NULL AND l.billed_qty IS NULL AND COALESCE(l.missing,0)=0 "
                           "GROUP BY l.id HAVING MAX(t.scan_at)>? ORDER BY MAX(t.scan_at), l.id", (str(since_iso or ""),)).fetchall()
    except sqlite3.Error:
        return []
    for lid, nm, packs, size, vendor, created, oid, scan_at in rows:
        if keys is not None and sw.pad_norm(str(nm)[:27]) not in keys and sw.pad_norm(str(nm)) not in keys:
            continue
        out.append(dict(line_id=lid, item=nm, packs=int(packs or 0), pack_size=int(size or 1), supplied=0, units=float(packs or 0) * float(size or 1),
                        arrived_at=str(scan_at or ""), arrived_by="scan", billed_qty=None, billed_bill_no="", billed_date="", vendor=vendor or "",
                        supkey=sw.supkey(vendor), order_id=oid, order_at=created, scan_at=str(scan_at or ""), kind="scan"))
    return out


def scan_arrivals(con, sp, item, since_iso, ctx=None):
    """Units of the item's scan-tied, unanswered lines (scan_lines) that COUNT: carried() None and expired() False, the arrival moment being
    scan_at. Moved here from shelf_figure (S583): the one rule. Fail-soft 0.0."""
    ctx = _ctx(con, sp, ctx)
    try:
        return sum(a["units"] for a in scan_lines(con, sp, item, since_iso, ctx) if carried(con, sp, a, ctx) is None and not expired(con, sp, a, ctx))
    except Exception:                                         # noqa: BLE001
        return 0.0


def arrivals_open(con, sp, ctx=None):
    """Every tapped or scan-tied line that is EXPIRED and not carried, without a billed_bill_no: dict(line_id, item, units, at (the arrival
    moment), who ('scan' for a scan-tied line, else who tapped), vendor, order_id, kind 'tap' | 'scan', scan_tied (its order has a scan tie)).
    Sorted by item, then moment. The owner's Needs-you (stock_watch.arrival_needs_you) names the scan-tied ones; an untied tap stays with D712."""
    ctx = _ctx(con, sp, ctx)
    con = ctx.con
    out = []
    if con is None or sp is None or not getattr(sp, "ok", False):
        return out
    try:
        tied = {int(r[0]) for r in con.execute("SELECT DISTINCT order_id FROM order_scan_tie WHERE arrived=1")} if _has(con, "order_scan_tie") else set()
        items = [r[0] for r in con.execute("SELECT DISTINCT item FROM purchase_order_line WHERE arrived_at IS NOT NULL AND supplied>0 AND COALESCE(billed_bill_no,'')=''")]
    except sqlite3.Error:
        return out
    lines = []
    for it in items:
        lines.extend(a for a in _sw()._arrivals(con, it, "", sp, ctx=ctx) if not str(a.get("billed_bill_no") or "").strip())
    lines.extend(scan_lines(con, sp, None, "", ctx))
    seen = set()
    for a in lines:
        if a.get("line_id") in seen:                          # one line reached under two spellings of its name
            continue
        seen.add(a.get("line_id"))
        if carried(con, sp, a, ctx) is None and expired(con, sp, a, ctx):
            out.append(dict(line_id=a["line_id"], item=a["item"], units=float(a["units"] or 0), at=str(a.get("arrived_at") or ""),
                            who=("scan" if a.get("kind") == "scan" else (a.get("arrived_by") or "")), vendor=a.get("vendor") or "", order_id=a.get("order_id"),
                            kind=a.get("kind") or "tap", scan_tied=(int(a.get("order_id") or 0) in tied)))
    out.sort(key=lambda x: (str(x["item"]), x["at"]))
    return out
'''))
SF.append(("F6 shelf(): docstring", '''    by counted share among the FAMILY's members (family(), never the names passed in), + boundary purchases (a bill dated before the count,
    entered after it) + tapped arrivals not in Marg + scan arrivals. No count -> shelf=None, named='no_count' (never Marg's: charter 3).
''', '''    by counted share among the FAMILY's members (family(), never the names passed in), + boundary purchases (a bill dated before the count,
    entered after it) + the arrivals Marg does not carry yet (taps + scan_arrivals: ONE rule, carried / expired -- S583). No count ->
    shelf=None, named='no_count' (never Marg's: charter 3).
'''))
SF.append(("F7 shelf(): the arrivals", '''    arr = taps(con, sp, name, mine["at"], ctx)
    try:
        arr += float(_sf_shelf().scan_arrivals(con, sp, name, mine["day"], ctx=ctx) or 0)
    except Exception:                                         # noqa: BLE001
        pass
    out["arrived"] = arr
''', '''    arr = taps(con, sp, name, mine["at"], ctx) + scan_arrivals(con, sp, name, mine["day"], ctx)     # S583: both under the one rule, both here
    out["arrived"] = arr
'''))

# =============================================================================================================== shelf_figure.py
SH = []
SH.append(("H1 header: the arrivals", '''#    * arrived, not yet in Marg: tapped arrivals the spine does not carry (stock_watch._arrivals) and orders that arrived by a bill's scan
#      (S454 4.4: order_scan_tie.arrived) whose lines Marg has not answered;
''', '''#    * arrived, not yet in Marg: tapped arrivals and the lines of orders that arrived by a bill's scan (S454 4.4: order_scan_tie.arrived) under
#      stock_figure's ONE rule (S583: carried / expired -- stock_figure.taps and stock_figure.scan_arrivals, added inside stock_figure.shelf);
'''))
SH.append(("H2 version", '''VERSION = "2.0"
KIT = "S577_STOCK_ON_SPINE"                                    # v1.0 was S454_BILL_REGISTER (part 3)
''', '''VERSION = "2.1"
KIT = "S583_ARRIVALS_ONE_RULE"                                 # v2.0 was S577_STOCK_ON_SPINE, v1.0 S454_BILL_REGISTER (part 3)
'''))
SH.append(("H3 scan_arrivals removed (it lives in stock_figure)", '''def scan_arrivals(con, sp, item, since_iso, ctx=None):
    """Units of orders that arrived by a bill's scan (S454 4.4) whose lines Marg has not answered and the spine does not carry (S577: the
    spine keyed by stock_figure.key_of). Seen, not touched (charter 12): the order lines are still matched by pad_norm(name[:27])."""
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
            n = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", _sf().key_of(sp, item, ctx), sw.supkey(vendor), str(created)[:10])
            if n and n[0]["n"]:
                continue
        out += float(packs or 0) * float(size or 1)
    return out


''', ''))

# =============================================================================================================== stock_watch.py
SW = []
SW.append(("W1 version", '''VERSION = "1.5"
KIT = "S577_STOCK_ON_SPINE"                                   # v1.4 was S502_STOCK_MILAAN_TODAY, v1.3 S436_STAFF_PAGES_CLEAN
# v1.5 (S577, rung 4b, 18-Oct-2026): a spot count''', '''VERSION = "1.6"
KIT = "S583_ARRIVALS_ONE_RULE"                                # v1.5 was S577_STOCK_ON_SPINE, v1.4 S502_STOCK_MILAAN_TODAY, v1.3 S436_STAFF_PAGES_CLEAN
# v1.6 (S583, 18-Oct-2026): ONE rule for "Marg carries this arrival" -- stock_figure.carried (a: the line's own Marg bill; b: a bill that answered
# another line of the key never; c: the own vendor's bill up to arrival.back_days before the order day; d: the own vendor's bill on or after it;
# e: another supplier's bill on or after it) and stock_figure.expired (the spine's purchase reach past the arrival + arrival.bill_grace_days,
# ISO against ISO). _arrivals' in_spine = carried() is not None, nothing else; bill_pending_lines tests carried(); the owner's Needs-you gains
# arrival_needs_you (an expired scan-tied arrival; the untied taps stay with amir_day._d712_owner_lines). New setting arrival.back_days (no row).
# v1.5 (S577, rung 4b, 18-Oct-2026): a spot count'''))
SW.append(("W2 SETTINGS: arrival.back_days", '''    dict(key="arrival.bill_grace_days", label="Arrival: bill entry grace (days)", kind="int", default="3", seed="3", lo=1, hi=30,
         hint="A tapped arrival with no purchase in the spine after this many days -> a line on Amir's board: bill entry baaki."),
''', '''    dict(key="arrival.bill_grace_days", label="Arrival: bill entry grace (days)", kind="int", default="3", seed="3", lo=1, hi=30,
         hint="A tapped arrival with no purchase in the spine after this many days -> a line on Amir's board: bill entry baaki."),
    dict(key="arrival.back_days", label="Arrival: a bill dated before the order (days)", kind="int", default="2", seed=None, lo=0, hi=15,
         hint="The order's own supplier's bill dated up to this many days BEFORE the order day still answers that order's arrival (the goods came "
              "before the order was written up). 0 = only bills dated on or after the order day."),
'''))
SW.append(("W3 settings(): back_days", '''                bill_grace_days=max(1, num("arrival.bill_grace_days", 3, int)), budget_pct=num("leak.budget_pct", 1.0), red_periods=max(1, num("leak.red_periods", 2, int)))
''', '''                bill_grace_days=max(1, num("arrival.bill_grace_days", 3, int)), back_days=max(0, num("arrival.back_days", 2, int)),
                budget_pct=num("leak.budget_pct", 1.0), red_periods=max(1, num("leak.red_periods", 2, int)))
'''))
SW.append(("W4 _arrivals: in_spine = carried() is not None", '''def _arrivals(con, item, since_iso, sp, ctx=None):
    """Tapped arrivals of the item after since_iso (purchase_order_line, supplied packs x pack_size) with the supplier,
    each marked whether the spine already carries a purchase of the item from that supplier after the tap's order day.
    S577: the spine is keyed by stock_figure.key_of (a renamed item reaches its family's purchases); the order line is still matched by
    pad_norm(name[:27]) -- seen, not touched (charter 12)."""
    out = []
    k20 = None
    try:
        keys = {pad_norm(item[:27]), pad_norm(item)}
        for r in con.execute("SELECT l.id, l.item, l.packs, l.pack_size, l.supplied, l.arrived_at, l.arrived_by, l.billed_qty, l.billed_bill_no, o.vendor, o.created_at, o.id "
                             "FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.arrived_at IS NOT NULL AND l.arrived_at>? AND l.supplied>0",
                             (since_iso,)):
            if pad_norm(str(r[1])[:27]) not in keys and pad_norm(r[1]) not in keys:
                continue
            units = float(r[4] or 0) * float(r[3] or 1)
            sk = supkey(r[9])
            in_spine = False
            if sp.ok:
                if k20 is None:
                    k20 = _sf().key_of(sp, item, ctx)
                rows = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", k20, sk, str(r[10])[:10])
                in_spine = bool(rows and rows[0]["n"])
            out.append(dict(line_id=r[0], item=r[1], packs=int(r[2] or 0), pack_size=int(r[3] or 1), supplied=int(r[4] or 0), units=units, arrived_at=r[5], arrived_by=r[6] or "",
                            billed_qty=r[7], billed_bill_no=r[8] or "", vendor=r[9] or "", supkey=sk, order_id=r[11], order_at=r[10], in_spine=in_spine))
    except sqlite3.Error:
        pass
    return out
''', '''def _tie_sql(con):
    """The order's scan moment as a column ('' when the tie table is not there)."""
    try:
        if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='order_scan_tie'").fetchone():
            return "(SELECT MAX(t.scan_at) FROM order_scan_tie t WHERE t.order_id=o.id AND t.arrived=1)"
    except sqlite3.Error:
        pass
    return "NULL"


def _arrivals(con, item, since_iso, sp, ctx=None):
    """Tapped arrivals of the item after since_iso (purchase_order_line, supplied packs x pack_size) with the supplier, each marked
    in_spine = stock_figure.carried(line) is not None -- THE one rule (S583, charter 2: rules a-e live in stock_figure) and nothing else: expiry
    is applied by stock_figure.taps / scan_arrivals, so open_trace's finding 2 and Amir's 'bill entry baaki' fix keep seeing a tap Marg never
    carried. scan_at = the order's scan moment ('' when untied); billed_date beside billed_bill_no. S577: the spine is keyed by
    stock_figure.key_of (a renamed item reaches its family's purchases); the order line is still matched by pad_norm(name[:27]) -- seen, not
    touched (charter 12)."""
    out = []
    try:
        keys = {pad_norm(item[:27]), pad_norm(item)}
        for r in con.execute("SELECT l.id, l.item, l.packs, l.pack_size, l.supplied, l.arrived_at, l.arrived_by, l.billed_qty, l.billed_bill_no, o.vendor, o.created_at, o.id, "
                             "l.billed_date, " + _tie_sql(con) + " FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                             "WHERE l.arrived_at IS NOT NULL AND l.arrived_at>? AND l.supplied>0", (since_iso,)):
            if pad_norm(str(r[1])[:27]) not in keys and pad_norm(r[1]) not in keys:
                continue
            a = dict(line_id=r[0], item=r[1], packs=int(r[2] or 0), pack_size=int(r[3] or 1), supplied=int(r[4] or 0), units=float(r[4] or 0) * float(r[3] or 1),
                     arrived_at=r[5], arrived_by=r[6] or "", billed_qty=r[7], billed_bill_no=r[8] or "", billed_date=r[12] or "", vendor=r[9] or "", supkey=supkey(r[9]),
                     order_id=r[11], order_at=r[10], scan_at=str(r[13] or ""), kind="tap", in_spine=False)
            a["in_spine"] = _sf().carried(con, sp, a, ctx) is not None
            out.append(a)
    except sqlite3.Error:
        pass
    return out
'''))
SW.append(("W5 bill_pending_lines: docstring", '''    """A tapped arrival with no purchase in the spine after arrival.bill_grace_days -> Amir's line 'bill entry baaki'."""
''', '''    """A tapped arrival with no purchase in the spine after arrival.bill_grace_days -> Amir's line 'bill entry baaki'. S583: 'no purchase in the
    spine' = stock_figure.carried() is None (the one rule); the routing, the words and the grace are as they were."""
'''))
SW.append(("W6 bill_pending_lines: the test", '''        sk = supkey(vendor)
        n = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", _sf().key_of(sp, item, ctx), sk, str(created)[:10])
        if n and n[0]["n"]:
            continue
''', '''        sk = supkey(vendor)
        if _sf().carried(con, sp, dict(line_id=lid, item=item, vendor=vendor, order_at=created, arrived_at=arrived, billed_bill_no=""), ctx) is not None:
            continue                                           # S583: THE one rule (stock_figure.carried)
'''))
SW.append(("W7 arrival_needs_you (after bill_pending_lines)", '''        out.append(dict(vendor=vendor or "", date=str(arrived)[:10], date_text=dmy(str(arrived)[:10]), item=item,
                        text_hi="bill entry baaki: %s %s" % (vendor or "", dmy(str(arrived)[:10])), text="bill entry pending: %s, arrival tapped %s" % (vendor or "", dmy(str(arrived)[:10]))))
    return out
''', '''        out.append(dict(vendor=vendor or "", date=str(arrived)[:10], date_text=dmy(str(arrived)[:10]), item=item,
                        text_hi="bill entry baaki: %s %s" % (vendor or "", dmy(str(arrived)[:10])), text="bill entry pending: %s, arrival tapped %s" % (vendor or "", dmy(str(arrived)[:10]))))
    return out


def arrival_needs_you(con, sp=None):
    """S583: the owner's Needs-you line for an arrival that EXPIRED (stock_figure.arrivals_open: counted as arrived, never carried by Marg's
    purchases, the spine's purchase reach past it by arrival.bill_grace_days) -- ONLY a line whose order has a scan tie (order_scan_tie); a
    tapped line on an untied order stays with amir_day._d712_owner_lines (D712), so no arrival is said twice. English, one line each. Fail-soft."""
    out = []
    try:
        sp = sp or Spine()
        if not sp.ok:
            return out
        SF = _sf()
        ctx = SF.Ctx(con, sp)
        upto = dmy(str((SF.reach(sp) or {}).get("last_pur") or "")[:10])[:5]
        for a in SF.arrivals_open(con, sp, ctx):
            if not a.get("scan_tied"):
                continue
            when = "%s %s" % (dmy(str(a["at"])[:10])[:5], str(a["at"])[11:16])
            if a.get("kind") == "scan":
                text = "%s: counted as arrived when the %s bill was scanned %s -- not in Marg's purchases up to %s" % (a["item"], a["vendor"] or "supplier's", when, upto)
            else:
                text = "%s: counted as arrived when %s tapped it %s (%s) -- not in Marg's purchases up to %s" % (a["item"], a["who"] or "staff", when, a["vendor"] or "-", upto)
            out.append(dict(cls="warn", target="porders", text=text))
    except Exception:                                         # noqa: BLE001
        return out
    return out
'''))
SW.append(("W8 needs_you_lines: the owner's arrival lines", '''        out.extend(leak_needs_you(con, S, sp))
        return out
''', '''        out.extend(leak_needs_you(con, S, sp))
        out.extend(arrival_needs_you(con, sp))                  # S583
        return out
'''))

EDITS = {"stock_figure.py": SF, "shelf_figure.py": SH, "stock_watch.py": SW}


def apply(src, edits, label):
    raw = open(src, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != FROM[label]:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (src, m, FROM[label]))
        return None
    t = raw.decode("utf-8")
    if t.count(EQ + "\n") < 2:
        print("STOP: %s has no header rule -- nothing built" % label)
        return None
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            print("STOP: %s anchor %s occurs %d times (must be exactly 1) -- nothing built" % (label, name, n))
            return None
        t = t.replace(old, new, 1)
        print("edit %s %s: anchored once, applied" % (label, name))
    return t.encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--kit", default="")                       # accepted for the installer's symmetry with S577; unused (no new file)
    a = ap.parse_args()
    built = {}
    for label, edits in EDITS.items():
        out = apply(os.path.join(a.finance, label), edits, label)
        if out is None:
            return 2
        built[label] = out
    os.makedirs(a.out, exist_ok=True)
    for label, out in built.items():
        dst = os.path.join(a.out, label)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s md5 %s  (FROM %s)" % (dst, hashlib.md5(out).hexdigest(), FROM[label]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
