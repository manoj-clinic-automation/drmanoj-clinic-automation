#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s593.py -- kit S593_ORDER_ENGINE_ONE_SOURCE: the builder. Anchored edits on the LIVE bytes of six files, plus the clone's
DUTY_MAP.json (one arm, one version); no new file, no data step.

    python3 -B make_s593.py --finance /root/finance --map /root/deploy/repo/claude_code_briefs/DUTY_MAP.json --out DIR

Every file is pinned (FROM md5, the brief's section 1); every anchor must occur exactly once in the live text, else STOP (exit 2, nothing
written). Writes the six files (spine_read.py under spine/) and DUTY_MAP.json into DIR and prints each md5 -- the installer compares them
with PINS.sh. DUTY_MAP.json already at its TO pin (the publish has landed) is copied through unchanged and said so.
The brief: claude_code_briefs/S593_ORDER_ENGINE_ONE_SOURCE.md (v2, 18-Oct-2026, Sanjeevni session 328) under D743; the independent read
R1 (03_WORKING_PAPERS/S328/S593_R1_REVIEW.md) is folded in. Closes F-916, F-717, F-738, F-739.
"""
import argparse
import hashlib
import json
import os
import sys

FROM = {
    "order_rules.py": "79f21c1ee1f763b1ac06b370e3d77b79",
    "porders.py": "a5a823bf30661a4bf65ced39b2355500",
    "porders_s454.py": "8307976393e6ea161f8d3a94bcb0692c",
    "order_sheet.py": "f00f0163bdd66a074c5af261c9b80a49",
    "darpan_kal.py": "8128598f745fca48a08472905f47da97",
    "spine/spine_read.py": "712a1e4ef827f6be4e8b23415c3ceb62",
}
MAP_FROM = "891defd8431e291b1a152f9e3c85f8c6"

# =============================================================================================================== order_rules.py (3.1, 3.3, 3.5)
OR = []
OR.append(("R1 the kit name and the S593 head note", '''VERSION = "1.0"
KIT = "S410_MEDICINE_ORDERING"
''', '''VERSION = "1.0"
KIT = "S593_ORDER_ENGINE_ONE_SOURCE"                            # the kit that last changed this file; v1.0 was S410_MEDICINE_ORDERING
#  S593 (19-Oct-2026, D743; S308 i, ii, iii, viii and Part A; charter rules 1, 2, 3, 9, 13, 14): THE ENGINE ON THE ONE STOCK FUNCTION AND
#  THE ONE ARRIVALS RULE. _s470_snap takes every item's figure from stock_figure.marg() (Marg's newest usable closing carried by the spine's
#  movements) + taps() + scan_arrivals() since that closing's capture -- the engine's own closing read, equal-share split and arrivals rule
#  (_s470_arrivals) are retired; rhythm() reads Marg's purchase bills from the spine (spine_read.purchases_by_supplier), never purchase_bill;
#  days_left() is the ONE days-left figure (Darpan's tab and his add door call it); send_proposal refuses an 'open' proposal on
#  order.source = darpan (F-738); plan() carries `inputs` (what the stock side stood on; the owner's api/day). No new setting, no new table.
''' ))
OR.append(("R2 rhythm(): the spine's purchase bills, by supplier key and day", '''    """{supplier_norm: dict(supplier, dates, bills90, gap, amount90_p, avg_month_p, cadence, how)} from 90 days of effective bills."""
    pa = _pa()
    today = today or _today()
    since = (today - dt.timedelta(days=90)).isoformat()
    out = {}
    rows = con.execute("SELECT b.supplier_norm, MAX(b.supplier), b.bill_date, SUM(b.amount_p) FROM purchase_bill b WHERE b.bill_date>=? AND b.bill_date<=? AND "
                       + pa.EFF_BILL + " GROUP BY b.supplier_norm, b.bill_date ORDER BY b.supplier_norm, b.bill_date", (since, today.isoformat())).fetchall()
    for sn, sup, d, amt in rows:
        e = out.setdefault(sn, dict(supplier=sup, dates=[], amount90_p=0, bills90=0))
        e["dates"].append(d)
        e["amount90_p"] += int(amt or 0)
        e["supplier"] = sup or e["supplier"]
    nb = con.execute("SELECT b.supplier_norm, COUNT(*) FROM purchase_bill b WHERE b.bill_date>=? AND b.bill_date<=? AND " + pa.EFF_BILL + " GROUP BY b.supplier_norm",
                     (since, today.isoformat())).fetchall()
    for sn, n in nb:
        if sn in out:
            out[sn]["bills90"] = int(n)
    minb = _int_setting(con, "order.min_bills_for_rhythm")
''', '''    """{supplier_norm: dict(supplier, dates, bills90, gap, amount90_p, avg_month_p, cadence, how)} from 90 days of Marg's purchase bills AS
    THE SPINE HOLDS THEM (S593, charter 1: the spine's bill table through spine_read.purchases_by_supplier, direction PURCHASE; the
    supplier's printed name mapped to supplier_norm by pa.supplier_key -- the same key that writes supplier_norm in the tables). amount90_p
    is the report's bill amount (the tables gave the NET amount per bill: the money basis moved, named in the kit's README)."""
    pa = _pa()
    today = today or _today()
    since = (today - dt.timedelta(days=90)).isoformat()
    out = {}
    sp = _s470_spine()
    try:
        rows = sp.purchases_by_supplier(since, today.isoformat())
    finally:
        try:
            sp.con.close()
        except Exception:                                      # noqa: BLE001
            pass
    for r in rows:
        sn = pa.supplier_key(r["supplier"]) if r["supplier"] else ""
        if not sn:
            continue
        e = out.setdefault(sn, dict(supplier=r["supplier"], dates=[], amount90_p=0, bills90=0))
        e["dates"].append(str(r["date"] or "")[:10])
        e["amount90_p"] += int(r["amount_p"] or 0)
        e["bills90"] += int(r["n_bills"] or 0)
        e["supplier"] = r["supplier"] or e["supplier"]
    minb = _int_setting(con, "order.min_bills_for_rhythm")
'''))
OR.append(("R3 lead_learned: the dead loop goes (the function stays)", '''    try:
        for sent, arr, billed in con.execute(
                "SELECT o.created_at, l.arrived_at, l.billed_date FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                "WHERE o.status IN ('sent','received') AND o.created_at>=? AND (l.arrived_at IS NOT NULL OR l.billed_date IS NOT NULL)", (since,)):
            pass
        for o in con.execute("SELECT id, vendor, created_at FROM purchase_order WHERE status IN ('sent','received') AND created_at>=?", (since,)):
''', '''    try:
        for o in con.execute("SELECT id, vendor, created_at FROM purchase_order WHERE status IN ('sent','received') AND created_at>=?", (since,)):
'''))
OR.append(("R4 ON_ORDER_DAYS retired; the docstring names the setting", '''# ------------------------------------------------------------------ the engine wrapper
ON_ORDER_DAYS = 4


def _on_order_units(con, today, basis=None):
    """{norm(item): dict(units, order_id, sent)} -- units on a SENT order of the last ON_ORDER_DAYS days whose line nobody has answered
    yet: on the way, counted as stock so the next morning's interim check does not order them twice."""
''', '''# ------------------------------------------------------------------ the engine wrapper
def _on_order_units(con, today, basis=None):
    """{norm(item): dict(units, order_id, sent)} -- units on a SENT order of the last order.on_order_days days (the setting; S593 retired the
    unused constant) whose line nobody has answered yet: on the way, counted as stock so the next morning's interim check does not order them twice."""
'''))
OR.append(("R5 days_left(): the one figure, before _line_out", '''def _line_out(pa, s, it, line, cost_unit, p, why_extra=None):
    unit = pa._unit_word(s.get("packing"), s["pack_size"])
''', '''def days_left(on_hand, per_day):
    """THE ONE days-left figure (S593, charter 2; S308 iii): about how many days the shelf lasts at the line's own pace -- None when the pace
    is not known, 0 when nothing is on hand, else round(on_hand / per_day). The arithmetic darpan_kal._s485_days_left had; every row that
    carries days_left (_line_out, the carried-short row, Darpan's tab and his add door) calls this and nothing else."""
    try:
        oh, pd = float(on_hand), float(per_day)
    except (TypeError, ValueError):
        return None
    if oh <= 0:
        return 0
    return int(round(oh / pd)) if pd > 0 else None


def _line_out(pa, s, it, line, cost_unit, p, why_extra=None):
    unit = pa._unit_word(s.get("packing"), s["pack_size"])
'''))
OR.append(("R6 _line_out carries days_left", '''    return dict(item=s["item"], on_hand=it["on_hand"], qty=rounded, unit=unit, pack_size=s["pack_size"], packing=s.get("packing") or "",
                rate_p=rate_p, per_day=round(p["rate_per_day"], 2), cover_after=cover_after, cover_days=line.get("cover_days"),
                value_p=int(rounded * rate_p), confirm=bool(line.get("confirm")), why=why)
''', '''    out = dict(item=s["item"], on_hand=it["on_hand"], qty=rounded, unit=unit, pack_size=s["pack_size"], packing=s.get("packing") or "",
               rate_p=rate_p, per_day=round(p["rate_per_day"], 2), cover_after=cover_after, cover_days=line.get("cover_days"),
               value_p=int(rounded * rate_p), confirm=bool(line.get("confirm")), why=why)
    out["days_left"] = days_left(out["on_hand"], out["per_day"])   # S593: the one figure, on the row the screens read
    return out
'''))
OR.append(("R7 the carried-short row carries days_left=None", '''                                   rate_p=rate_p, per_day=None, cover_after=None, cover_days=None, value_p=int(qty * rate_p), confirm=False,
''', '''                                   rate_p=rate_p, per_day=None, cover_after=None, cover_days=None, days_left=None, value_p=int(qty * rate_p), confirm=False,
'''))
OR.append(("R8 plan() returns inputs", '''    return dict(as_on=as_on, today=today.isoformat(), vendors=vendors, held_items=held_items, no_supplier=no_supplier, engine=_s470_engine(),   # S470
                no_closing=_s470_missing())
''', '''    return dict(as_on=as_on, today=today.isoformat(), vendors=vendors, held_items=held_items, no_supplier=no_supplier, engine=_s470_engine(),   # S470
                no_closing=_s470_missing(), inputs=_s470_inputs_note())   # S593: what the stock side stood on
'''))
OR.append(("R9 send_proposal: F-738, an open proposal never goes out on darpan", '''    if p["status"] not in ("open", "held", "darpan_ok"):       # S485
        return dict(ok=False, error="not_open", message="Yeh order ab %s hai." % p["status"]), 409
    r = rule_for(con, p["supplier_norm"])
''', '''    if p["status"] not in ("open", "held", "darpan_ok"):       # S485
        return dict(ok=False, error="not_open", message="Yeh order ab %s hai." % p["status"]), 409
    if p["status"] == "open" and _s454_source(con) == "darpan":   # S593 (F-738, S486 Part A): on darpan only the list he made pakka goes out
        return dict(ok=False, error="not_confirmed", message="Darpan ne yeh list abhi pakka nahi ki."), 409
    r = rule_for(con, p["supplier_norm"])
'''))
OR.append(("R10 api/day serves the inputs note (the owner's eyes)", '''@bp.route("/finance/porders/api/day")
def api_day():
    u, con, kind, err = _auth()
    if err:
        return err
    return jsonify(**day_state(con))
''', '''@bp.route("/finance/porders/api/day")
def api_day():
    u, con, kind, err = _auth()
    if err:
        return err
    d = day_state(con)
    d["inputs"] = _s470_inputs_note(process=True)              # S593: what the stock side of the last plan stood on (nothing of it on Darpan's tab)
    return jsonify(**d)
'''))
OR.append(("R11 _s454_shelf_snap: the engine's context rides in; marg_qty is Marg's pure figure", '''def _s454_shelf_snap(con, snap):
    """The snapshot with each item's qty replaced by its shelf figure (Marg's kept as marg_qty); fail-soft: Marg's snapshot as it is."""
    try:
        import shelf_figure                                   # noqa: PLC0415
        F = shelf_figure.figures(con, items=[s["item"] for s in snap.values()])
    except Exception:                                         # noqa: BLE001
        return snap
    out = {}
    for k, s in snap.items():
        f = F.get(s["item"]) or {}
        d = dict(s)
        if f.get("shelf") is not None and f.get("named") not in ("no_count", "no_spine"):
            d["marg_qty"] = s["qty"]
            d["qty"] = int(f["shelf"])
        out[k] = d
    return out
''', '''def _s454_shelf_snap(con, snap, ctx=None):
    """The snapshot with each item's qty replaced by its shelf figure (Marg's kept as marg_qty); fail-soft: the snapshot as it is.
    S593 (R1-C5, R1-C6): the engine's own context (stock_watch.Spine + stock_figure.Ctx) rides into shelf_figure.figures so every item is
    figured once per plan(); marg_qty is Marg's PURE figure (_s470.marg = stock_figure.marg().figure, no arrivals) -- the incoming qty only
    when the row has none (the tables engine)."""
    try:
        import shelf_figure                                   # noqa: PLC0415
        F = shelf_figure.figures(con, sp=(ctx.sp if ctx is not None else None), items=[s["item"] for s in snap.values()], ctx=ctx)
    except Exception:                                         # noqa: BLE001
        return snap
    out = {}
    for k, s in snap.items():
        f = F.get(s["item"]) or {}
        d = dict(s)
        if f.get("shelf") is not None and f.get("named") not in ("no_count", "no_spine"):
            m = (s.get("_s470") or {}).get("marg")
            d["marg_qty"] = int(round(float(m))) if m is not None else s["qty"]
            d["qty"] = int(f["shelf"])
        out[k] = d
    return out
'''))
OR.append(("R12 the S470 head note: the arrivals paragraph", '''#   ARRIVALS NOT YET IN MARG -- one rule on both bases: an order's received lines, and an order that arrived by its bill's scan, count as
#       stock until the spine shows a purchase line of that item from that supplier dated on or after THE ORDER'S OWN DAY (Marg dates
#       the bill by the supplier's date, often a day or two before the tap -- the old rule waited for a bill dated after the tap and
#       counted the goods twice until the window ended). On the count basis a counted item's arrival is inside its shelf figure.
''', '''#   ARRIVALS NOT YET IN MARG -- S593 (D743): THE ONE RULE is stock_figure's (carried / expired, rules a-e; S583). The engine's own copy
#       (_s470_arrivals) is retired: an uncounted item's figure is stock_figure.marg() + taps + scan_arrivals since its closing's capture;
#       a counted item's arrivals are inside its shelf figure. Only the sent-and-unanswered lines (_on_order_units) ride beside it.
'''))
OR.append(("R13 the process's last inputs note", '''_S470 = _s470_threading.local()                                # the last inputs' note, per thread: which source made them
_S470_MOD = {"mtime": None, "mod": None}
''', '''_S470 = _s470_threading.local()                                # the last inputs' note, per thread: which source made them
_S470_MOD = {"mtime": None, "mod": None}
_S593_INPUTS = {"val": None}                                    # S593: the process's last inputs note (the owner's api/day reads it)
'''))
OR.append(("R14 _s470_snap on the one stock function", '''def _s470_snap(con, pa, sp):
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
''', '''def _s593_sf():
    """stock_figure beside this file -- the one stock function (S577 / S583 / S587); imported at call time, as shelf_figure does."""
    import stock_figure                                        # noqa: PLC0415
    return stock_figure


def _s593_sw():
    import stock_watch                                         # noqa: PLC0415
    return stock_watch


def _s470_inputs_note(process=False):
    """plan()['inputs'] -- what the stock side of the last plan on this thread stood on; process=True: the process's last (the owner's
    api/day). None until a plan was made on the spine."""
    if process:
        return _S593_INPUTS.get("val")
    return getattr(_S470, "inputs", None)


def _s470_snap(con, pa, sw, ctx, today):
    """(as_on dd-mm-yyyy, {norm(item): row}, [items with no figure]) -- S593 (S308 i; charter 1, 2, 3; R1-B1, C1-C4): every item of Marg's
    list with its figure from THE ONE STOCK FUNCTION -- stock_figure.marg() (Marg's newest usable closing carried by the spine's movements to
    today) + taps() + scan_arrivals() since that closing's capture (the one arrivals rule, S583) -- never below 0. `sw` is stock_watch.Spine()
    (the handle stock_figure is written for) and `ctx` its stock_figure.Ctx. The key grouping stays only for n = the number of MASTER names
    under the key, which _s470_pace divides the key's sales by (the two must agree; R1-C2). An item no capture holds at all is left out and
    named; an item the closing did not print but the spine knew (by='absent') stands at 0 AND is named (a deliberate change: the engine may
    now list it). as_on is the capture's end day."""
    SF = _s593_sf()
    t = today.isoformat()
    cap = SF.capture_at(sw, t, ctx)
    if cap is None:
        raise RuntimeError("the spine holds no usable closing")
    fam = {}
    for item, packing, size in _s470_master(con, pa):
        fam.setdefault(sw.key(item), []).append((item, packing, size))
    snap, missing = {}, []
    for key, members in fam.items():
        n = len(members)
        for item, packing, size in members:
            m = SF.marg(con, sw, item, at=t, ctx=ctx)
            if m is None:
                missing.append(item)
                continue
            c = m["closing"]
            figure = float(m["figure"] or 0)
            taps = float(m.get("taps") or 0)
            scans = float(SF.scan_arrivals(con, sw, item, c["stamp_iso"], ctx) or 0)
            if c.get("by") == "absent":
                missing.append(item)
            snap[pa.norm(item)] = dict(item=item, qty=max(0, int(round(figure + taps + scans))), packing=packing, pack_size=size,
                                       _s470=dict(key=key, family=n, lot=None, free=None, marg=figure, by=c.get("by"), approx=bool(m.get("approx"))))
    return _s470_dmy(cap["end_day"]), snap, missing
'''))
OR.append(("R15 _s470_arrivals retired; _s470_inputs on two handles and one context", '''def _s470_arrivals(con, pa, sp, snap, today, days):
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
''', '''def _s470_inputs(con, today):
    """S593 (D743, R1-B1): TWO spine handles -- spine_read's (sales_daily / last_sale / purchase_lines, for _s470_pace and _s470_purch) and
    stock_watch.Spine() (the handle stock_figure is written for: it carries .ok), the latter inside ONE stock_figure.Ctx that _s470_snap and
    _s454_shelf_snap share, so every item is figured once per plan(). The engine's own arrivals rule is gone: transit holds the sent-and-
    unanswered lines only (_on_order_units); every other arrival is inside the one function's figure. The inputs note (plan()['inputs'], the
    owner's api/day) says what the stock side stood on: the sale reach, the closing's capture, the spine's build, the counted / Marg / absent
    counts."""
    pa = _pa()
    SF = _s593_sf()
    sp = _s470_spine()
    sw = _s593_sw().Spine()
    ctx = SF._ctx(con, sw, None)
    try:
        as_on, snap, missing = _s470_snap(con, pa, sw, ctx, today)
        basis = _s454_basis(con)
        if basis == "count":                                     # the shelf figure, through the same context; Marg's pure figure beside it as marg_qty
            snap = _s454_shelf_snap(con, snap, ctx)
        pace = _s470_pace(sp, snap, today, _s470_days(con, "order.pace_days"))
        purch = _s470_purch(pa, sp, snap, today, _s470_days(con, "order.lot_history_days"))
        cap = SF.capture_at(sw, today.isoformat(), ctx) or {}
        try:
            built = str((sw.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or "")
        except Exception:                                        # noqa: BLE001
            built = ""
        note = dict(sales_through=str((SF._reach_once(sw, ctx) or {}).get("last_sale") or ""),
                    capture=dict(md5=str(cap.get("md5") or "")[:8], as_on=cap.get("as_on"), end_day=cap.get("end_day"), stamp=cap.get("stamp")),
                    spine_built=built, counted=sum(1 for s in snap.values() if "marg_qty" in s), marg=sum(1 for s in snap.values() if "marg_qty" not in s),
                    absent=sum(1 for s in snap.values() if (s.get("_s470") or {}).get("by") == "absent"), made_at=now_iso())
    finally:
        for h in (sp, sw):
            try:
                h.con.close()
            except Exception:                                    # noqa: BLE001
                pass
    transit = {}
    for k, e in _on_order_units(con, today, "count").items():    # sent, not yet arrived: on the way, counted as stock (as today)
'''))
OR.append(("R16 _s470_inputs: the note kept", '''    _S470.missing = sorted(m for m in missing if pa.norm(m) not in ortho)   # an orthotic is S403's, never this engine's
    return as_on, snap, pace, purch, transit, ortho
''', '''    _S470.missing = sorted(m for m in missing if pa.norm(m) not in ortho)   # an orthotic is S403's, never this engine's
    _S470.inputs = note
    _S593_INPUTS["val"] = note
    return as_on, snap, pace, purch, transit, ortho
'''))
OR.append(("R17 _snapshot_inputs: the note reset with the missing list", '''    _S470.missing = []
    if _s470_source(con) != "spine":
''', '''    _S470.missing = []
    _S470.inputs = None
    if _s470_source(con) != "spine":
'''))

# =============================================================================================================== porders.py (3.2)
PO = []
PO.append(("P1 the head note", '''#  v1.1 (S410, D626, 26-Sep-2026): mounts order_rules (the medicine buying rules as settings, fixed order days, the ordering
#  team's day); state() carries 'today' (the day's proposals, the freeze, the contextual text); send_med refuses while frozen.
''', '''#  v1.1 (S410, D626, 26-Sep-2026): mounts order_rules (the medicine buying rules as settings, fixed order days, the ordering
#  team's day); state() carries 'today' (the day's proposals, the freeze, the contextual text); send_med refuses while frozen.
#
#  S593 (D743, 19-Oct-2026): detect_supplies asks THE ONE arrivals rule (stock_figure.carried, rules c / d, on the spine by the spine's key)
#  which Marg bill carries an open order line and writes the packs of that bill's own line -- its table read (purchase_line) and 20-letter
#  clip are gone; send_med refuses outright on order.source = darpan (F-738: that door bypasses Darpan's pakka).
'''))
PO.append(("P2 detect_supplies asks the one rule", '''def detect_supplies(con):
    """A Marg purchase line from the vendor for an ordered item after the send date marks the line billed (qty, bill no)
    -- and supplied, when nobody tapped. Idempotent."""
    ia, pa = _ia(), _pa()
    n = 0
    try:
        rows = con.execute("SELECT l.id, l.item, l.packs, l.supplied, l.missing, o.vendor, o.created_at FROM purchase_order_line l "
                           "JOIN purchase_order o ON o.id=l.order_id WHERE o.status IN ('sent','received') AND l.billed_qty IS NULL").fetchall()
    except sqlite3.Error:
        return 0
    for r in rows:
        lid, item, packs, supplied, missing, vendor, created = r[0], r[1], int(r[2] or 0), r[3], r[4], r[5], str(r[6] or "")[:10]
        keys = {ia.pad_norm(ia.clip(item, ia.PURCHASE_CLIP))} | {ia.pad_norm(ia.clip(f, ia.PURCHASE_CLIP)) for f in ia.aliases_of(con, item)}
        vn = pa.supplier_key(vendor)
        hit = None
        for pl in con.execute("SELECT l.item, l.qty, l.free, l.bill_no, l.bill_date FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_date>=? "
                              "AND " + pa.EFF_LINE + " ORDER BY l.bill_date, l.id", (vn, created)):
            if ia.pad_norm(pl[0]) in keys:
                q = int(round(float(pl[1] or 0) + float(pl[2] or 0)))
                hit = (q, pl[3], pl[4])
                break
        if not hit:
            continue
        q, bno, bdate = hit
        con.execute("UPDATE purchase_order_line SET billed_qty=?, billed_bill_no=?, billed_date=?, detected_at=? WHERE id=?",
                    (q, str(bno or ""), bdate, now_iso(), lid))
        if supplied is None and not missing:
            con.execute("UPDATE purchase_order_line SET supplied=?, short=?, arrived_by='marg', arrived_at=? WHERE id=?",
                        (q, 1 if q < packs else 0, now_iso(), lid))
            _audit(con, "marg", "line_detected", lid, dict(item=item, ordered=packs, billed=q, bill=str(bno or "")))
        n += 1
    if n:
        con.commit()
        _close_complete_orders(con, "marg")
    return n
''', '''def detect_supplies(con):
    """Marg's purchase that carries an open order line marks the line billed (qty in PACKS, bill no, date) -- and supplied, when nobody
    tapped. S593 (D743; S583's 'two copies' closed): WHICH bill carries the line is THE ONE RULE, stock_figure.carried() on the spine by the
    spine's key -- accepted here only by rule (c) (the order's own vendor, dated up to arrival.back_days before the order day) or (d) (the own
    vendor on or after the order day); (a) cannot occur (billed_bill_no is NULL here); (e), another supplier's bill, counts for stock only and
    never marks this line billed. The packs are the spine's own line: SUM(qty) + SUM(free) of that bill for the key (never units / pack_size:
    a 'whole' key's units are its qty). A fresh Ctx per row, so rule (b) sees each write (two lines of one key, two bills). The spine unread
    (sw.ok False): nothing written, one stderr line. The tables (purchase_line) and the 20-letter clip are read no more. Idempotent."""
    n = 0
    try:
        rows = con.execute("SELECT l.id, l.item, l.packs, l.supplied, l.missing, o.vendor, o.created_at FROM purchase_order_line l "
                           "JOIN purchase_order o ON o.id=l.order_id WHERE o.status IN ('sent','received') AND l.billed_qty IS NULL").fetchall()
    except sqlite3.Error:
        return 0
    if not rows:
        return 0
    import stock_figure as SF                                 # noqa: PLC0415 -- beside this file: the one stock function (S577 / S583 / S587)
    import stock_watch as SW                                  # noqa: PLC0415
    sw = SW.Spine()
    if not getattr(sw, "ok", False):
        print("porders.detect_supplies: the spine could not be read -- no order line marked billed (S593)", file=sys.stderr)
        return 0
    try:
        for r in rows:
            lid, item, packs, supplied, missing, vendor, created = r[0], r[1], int(r[2] or 0), r[3], r[4], r[5], str(r[6] or "")
            line = dict(line_id=lid, item=item, vendor=vendor, order_at=created, billed_bill_no=None)
            ctx = SF._ctx(con, sw, None)                      # R1-C10: a fresh context per row -- the per-key taken-bills cache must see each write
            hit = SF.carried(con, sw, line, ctx)
            if not hit or hit.get("how") not in ("c", "d"):
                continue
            k20 = SF.key_of(sw, item, ctx)
            pr = sw.q("SELECT COALESCE(SUM(qty),0) AS q, COALESCE(SUM(free),0) AS f FROM sp_purchase_line WHERE k20=? AND supkey=? AND bill=? AND date=? "
                      "AND direction='PURCHASE'", k20, hit["supkey"], hit["bill"], hit["date"])
            q = int(round(float(pr[0]["q"] or 0) + float(pr[0]["f"] or 0))) if pr else 0
            if q <= 0:
                continue
            bno, bdate = hit["bill"], hit["date"]
            con.execute("UPDATE purchase_order_line SET billed_qty=?, billed_bill_no=?, billed_date=?, detected_at=? WHERE id=?",
                        (q, str(bno or ""), bdate, now_iso(), lid))
            if supplied is None and not missing:
                con.execute("UPDATE purchase_order_line SET supplied=?, short=?, arrived_by='marg', arrived_at=? WHERE id=?",
                            (q, 1 if q < packs else 0, now_iso(), lid))
                _audit(con, "marg", "line_detected", lid, dict(item=item, ordered=packs, billed=q, bill=str(bno or "")))
            n += 1
    finally:
        try:
            sw.con.close()
        except Exception:                                     # noqa: BLE001
            pass
    if n:
        con.commit()
        _close_complete_orders(con, "marg")
    return n
'''))
PO.append(("P3 the order source, read for send_med", '''def state(con, u=None, kind="viewer"):
    ensure_schema(con)
    detect_supplies(con)
''', '''def _order_source_s593(con):
    """order.source as order_sheet reads it (marg_sheet | system | darpan); marg_sheet when it cannot be read."""
    try:
        import order_sheet                                    # noqa: PLC0415
        return order_sheet.source(con)
    except Exception:                                         # noqa: BLE001
        return "marg_sheet"


def state(con, u=None, kind="viewer"):
    ensure_schema(con)
    detect_supplies(con)
'''))
PO.append(("P4 api_send_med refuses on darpan (F-738)", '''    fr = _frozen_s410(con)                                    # S410 (D626): the owner's freeze
    if fr:
        return jsonify(ok=False, error="frozen", message="Medicine ordering band hai: %s" % (fr.get("reason") or "")), 423
    pa = _pa()
    b = request.get_json(silent=True) or {}
    vendor = str(b.get("vendor") or "").strip()
''', '''    fr = _frozen_s410(con)                                    # S410 (D626): the owner's freeze
    if fr:
        return jsonify(ok=False, error="frozen", message="Medicine ordering band hai: %s" % (fr.get("reason") or "")), 423
    if _order_source_s593(con) == "darpan":                   # S593 (F-738, R1-C8): this door bypasses Darpan's pakka -- refused outright on darpan
        return jsonify(ok=False, error="not_confirmed", message="Darpan ki pakki list se hi order jaata hai"), 409
    pa = _pa()
    b = request.get_json(silent=True) or {}
    vendor = str(b.get("vendor") or "").strip()
'''))

# =============================================================================================================== porders_s454.py (3.6)
PS = []
PS.append(("S1 the heading's counts (F-739) before order_list", '''def order_list():
    u, con, kind, login, err = _auth_page()
''', '''def _s593_counts(es):
    """S593 (F-739, charter 8 / 13): the heading counts the cards' own list LESS a card that is only S403's orthotic shortage, and the
    medicine lines only (a mixed card -- a supplier with both -- counts once, with its medicine lines). entries() hands sources as a list."""
    med = [e for e in es if set(e.get("sources") or []) != {"ortho"}]
    return len(med), sum(1 for e in med for l in e["lines"] if l.get("src") != "ortho")


def order_list():
    u, con, kind, login, err = _auth_page()
'''))
PS.append(("S2 the headings count the medicine cards (F-739)", '''    elif src == "system":
        h.append('<div class="mut" id="whose">%s</div>' % esc(L(en, "whose", L(en, "system"), OS.today().strftime("%d-%m"), len(es), sum(len(e["lines"]) for e in es))))
    elif src == "darpan":                                     # S485 (D677): the system's list, as Darpan made it pakka on his page
        h.append('<div class="mut" id="whose">%s</div>' % esc(re.sub(r"(?<![\\d,])1 (medicine|supplier)s\\b", r"1 \\1",
                 ("Darpan's confirmed list · %s · %d suppliers, %d medicines" if en else "Darpan ki pakki list · %s · %d supplier, %d dawa")
                 % (OS.today().strftime("%d-%m"), len(es), sum(len(e["lines"]) for e in es)))))
''', '''    elif src == "system":
        nsup, nmed = _s593_counts(es)                         # S593 (F-739): the medicine cards, less the orthotic-only card
        h.append('<div class="mut" id="whose">%s</div>' % esc(L(en, "whose", L(en, "system"), OS.today().strftime("%d-%m"), nsup, nmed)))
    elif src == "darpan":                                     # S485 (D677): the system's list, as Darpan made it pakka on his page
        nsup, nmed = _s593_counts(es)                         # S593 (F-739)
        h.append('<div class="mut" id="whose">%s</div>' % esc(re.sub(r"(?<![\\d,])1 (medicine|supplier)s\\b", r"1 \\1",
                 ("Darpan's confirmed list · %s · %d suppliers, %d medicines" if en else "Darpan ki pakki list · %s · %d supplier, %d dawa")
                 % (OS.today().strftime("%d-%m"), nsup, nmed))))
'''))
PS.append(("S3 done_all: the page's conditions read every done order", '''    done = _done_today(con)
    wa = [d for d in done if d["via"] in ("whatsapp", "whatsapp+call")]
''', '''    done_all = _done_today(con)                               # S593 (F-916, D743): the page's CONDITIONS read every done order; the block below filters
    wa = [d for d in done_all if d["via"] in ("whatsapp", "whatsapp+call")]
'''))
PS.append(("S4 the 'Abhi baaki' heading as before", '''    if done or line:
        h.append('<div class="mut" id="still">%s</div>' % L(en, "still", len(pend)))
''', '''    if done_all or line:
        h.append('<div class="mut" id="still">%s</div>' % L(en, "still", len(pend)))
'''))
PS.append(("S5 the done block: a supplier with a card is not repeated; an earlier day's line says its date (F-916)", '''    if done:
        h.append('<div class="mut" id="donehead">%s</div>' % L(en, "doneN", len(done)))
        for i, d in enumerate(done):
            if i >= 3 and not show:
                h.append('<a class="more" href="?all=1">%s</a>' % L(en, "more2", len(done) - 3))
                break
            word = {"whatsapp": "wa_gaya", "whatsapp+call": "wa_call", "call": "call_done", "scan": "scan_done"}.get(d["via"], "call_done")
            p1 = d["phone"]
            callb = ('<a class="sm" href="tel:%s" onclick="s454(\\'%s/api/s454/call\\',{sn:%s},function(){})">%s</a>' % (esc(_tel(p1)), P, esc(json.dumps(d["sn"])), L(en, "call"))
                     if p1 else "")
            h.append('<div class="ln"><div class="t"><div class="a">%s</div><div class="s grn">✓ %s</div></div>%s</div>' % (esc(d["vendor"]), L(en, word), callb))
    if not pend and not line and not done:
''', '''    pend_sn = {e["sn"] for e in pend}                         # S593 (F-916, D743): a supplier with a card above is not repeated under 'Ho chuke'
    done = [d for d in done_all if d["sn"] not in pend_sn]
    if done:
        h.append('<div class="mut" id="donehead">%s</div>' % L(en, "doneN", len(done)))
        for i, d in enumerate(done):
            if i >= 3 and not show:
                h.append('<a class="more" href="?all=1">%s</a>' % L(en, "more2", len(done) - 3))
                break
            word = {"whatsapp": "wa_gaya", "whatsapp+call": "wa_call", "call": "call_done", "scan": "scan_done"}.get(d["via"], "call_done")
            p1 = d["phone"]
            callb = ('<a class="sm" href="tel:%s" onclick="s454(\\'%s/api/s454/call\\',{sn:%s},function(){})">%s</a>' % (esc(_tel(p1)), P, esc(json.dumps(d["sn"])), L(en, "call"))
                     if p1 else "")
            mark = L(en, word)
            if OS.ddmm(d["sent_at"]) != OS.ddmm(OS.now_iso()):   # S593 (F-916): a done line of an earlier day says its own date
                mark = "%s · %s" % (esc(OS.ddmm(d["sent_at"])), mark)
            h.append('<div class="ln"><div class="t"><div class="a">%s</div><div class="s grn">✓ %s</div></div>%s</div>' % (esc(d["vendor"]), mark, callb))
    if not pend and not line and not done_all:
'''))

# =============================================================================================================== order_sheet.py (3.7, F-717)
OSH = []
OSH.append(("O1 load_pending's fallback rolls back before it goes on (F-717)", '''        try:
            load_file(con, p, md5, name or server, src or "push", stamp or "")
            out += 1
        except Exception as e:                                # noqa: BLE001
            print("order_sheet: %s not loaded (%s)" % (server, str(e)[:120]), file=sys.stderr)
''', '''        try:
            load_file(con, p, md5, name or server, src or "push", stamp or "")
            out += 1
        except Exception as e:                                # noqa: BLE001
            try:                                              # S593 (F-717): a half-loaded sheet never rides into the next one
                con.rollback()
            except sqlite3.Error:
                pass
            print("order_sheet: %s not loaded (%s)" % (server, str(e)[:120]), file=sys.stderr)
'''))

# =============================================================================================================== darpan_kal.py (3.8)
DK = []
DK.append(("D1 _s485_days_left retired; _s485_line serves named fields, days_left the one figure", '''def _s485_days_left(l):
    """About how many days the shelf lasts at the line's own pace (on_hand / per_day); None when there is no pace."""
    try:
        oh, pd = float(l.get("on_hand")), float(l.get("per_day"))
    except (TypeError, ValueError):
        return None
    if oh <= 0:
        return 0
    return int(round(oh / pd)) if pd > 0 else None


def _s485_line(pid, l):
    return dict(pid=pid, item=l.get("item") or "", packing=l.get("packing") or "", unit=_s485_unit(l), qty=int(l.get("qty") or 0),
                on_hand_text=_s485_shelf(l), cover_days=l.get("cover_days"), days_left=_s485_days_left(l),
                held=bool(l.get("held")), added=bool(l.get("added")), why=list(l.get("why") or []))
''', '''def _s485_line(pid, l):
    """S593 (S308 viii, charter 14): the tab is served the fields it reads and nothing else -- `why` and `cover_days` stay the owner's.
    days_left is THE ONE figure, order_rules.days_left: the engine wrote it on the line (S593's _line_out); a line stored before that, or
    built without it, is figured by the same function from its own on_hand and per_day."""
    OR = _s485_or()
    dl = l.get("days_left") if "days_left" in l else OR.days_left(l.get("on_hand"), l.get("per_day"))
    return dict(pid=pid, item=l.get("item") or "", packing=l.get("packing") or "", unit=_s485_unit(l), qty=int(l.get("qty") or 0),
                on_hand_text=_s485_shelf(l), days_left=dl, held=bool(l.get("held")), added=bool(l.get("added")))
'''))
DK.append(("D2 Darpan's added line carries days_left (R1-B3)", '''    try:
        on_hand = int(round(float(s.get("qty"))))
    except (TypeError, ValueError):
        on_hand = None
    line = dict(item=item, on_hand=on_hand, qty=qty, unit="strip" if strip else "unit", pack_size=ps, packing=s.get("packing") or "", rate_p=rate_p,
                per_day=(round(float(pace["rate_per_day"]), 2) if pace and pace.get("rate_per_day") is not None else None), cover_after=None, cover_days=None,
                value_p=int(qty * rate_p), confirm=False, why=["Darpan ne joda"], vendor_norm=sn, added=True, lot=(e or {}).get("lot"), free=(e or {}).get("free"))
''', '''    try:
        on_hand = int(round(float(s.get("qty"))))
    except (TypeError, ValueError):
        on_hand = None
    per_day = (round(float(pace["rate_per_day"]), 2) if pace and pace.get("rate_per_day") is not None else None)
    line = dict(item=item, on_hand=on_hand, qty=qty, unit="strip" if strip else "unit", pack_size=ps, packing=s.get("packing") or "", rate_p=rate_p,
                per_day=per_day, cover_after=None, cover_days=None, days_left=OR.days_left(on_hand, per_day),   # S593 (R1-B3): the one figure
                value_p=int(qty * rate_p), confirm=False, why=["Darpan ne joda"], vendor_norm=sn, added=True, lot=(e or {}).get("lot"), free=(e or {}).get("free"))
'''))

# =============================================================================================================== spine/spine_read.py (3.4)
SR = []
SR.append(("E1 purchases_by_supplier after purchase_lines", '''    def family(self, name):
''', '''    def purchases_by_supplier(self, date_from, date_to):
        """[{supplier, supkey, date, amount_p, n_bills}] -- one row per supplier key and bill day over [date_from, date_to], PURCHASE bills
        only (sp_purchase_bill: the report's bill amount), the supplier's printed name beside its key; by key, then day.
        S593: what order_rules.rhythm reads for a supplier's buying rhythm (charter 1 -- the spine, never purchase_bill)."""
        return self.q("SELECT MAX(b.supplier) AS supplier, b.supkey AS supkey, b.date AS date, SUM(b.amount_p) AS amount_p, COUNT(*) AS n_bills "
                      "FROM sp_purchase_bill b WHERE b.direction='PURCHASE' AND b.date>=? AND b.date<=? GROUP BY b.supkey, b.date ORDER BY b.supkey, b.date",
                      date_from, date_to)

    def family(self, name):
'''))

# =============================================================================================================== DUTY_MAP.json (3.6, F-739)
DM = []
DM.append(("M1 version 14 -> 15", ' "version": 14,\n', ' "version": 15,\n'))
DM.append(("M2 kit", ' "kit": "S556_REFUSED_TEXT_ROAD",\n', ' "kit": "S593_ORDER_ENGINE_ONE_SOURCE",\n'))
DM.append(("M3 the note", 'is laid before this map is pulled).",', 'is laid before this map is pulled). S593 (19-Oct-2026, D743; F-739): reception.medicine_orders\' due_sql gains the darpan arm -- on order.source = darpan the suppliers Darpan made pakka today (order_proposal status darpan_ok, DISTINCT supplier_norm), the same set reception\'s heading counts (charter 13: the door and the line read one rule). No duty added, moved or removed.",'))
DM.append(("M4 the duty's words", "\"duty\": \"Order from Darpan's order sheet (or, on order.source = system, the day's proposals): 'Sab ko WhatsApp bhejo', or call and tap 'Order ho gaya' -- S454 (D666): one card per supplier still to be ordered\",",
           "\"duty\": \"Order from Darpan's order sheet (on order.source = system the day's open proposals; on darpan the suppliers Darpan made pakka -- S593): 'Sab ko WhatsApp bhejo', or call and tap 'Order ho gaya' -- S454 (D666): one card per supplier still to be ordered\","))
DM.append(("M5 the darpan arm of due_sql", "WHEN COALESCE((SELECT value FROM setting WHERE key = 'order.source'), 'marg_sheet') = 'system' THEN (SELECT COUNT(DISTINCT p.supplier_norm) FROM order_proposal p WHERE p.day = date('now','localtime') AND p.status = 'open') ELSE",
           "WHEN COALESCE((SELECT value FROM setting WHERE key = 'order.source'), 'marg_sheet') = 'system' THEN (SELECT COUNT(DISTINCT p.supplier_norm) FROM order_proposal p WHERE p.day = date('now','localtime') AND p.status = 'open') WHEN COALESCE((SELECT value FROM setting WHERE key = 'order.source'), 'marg_sheet') = 'darpan' THEN (SELECT COUNT(DISTINCT p.supplier_norm) FROM order_proposal p WHERE p.day = date('now','localtime') AND p.status = 'darpan_ok') ELSE"))

EDITS = {"order_rules.py": OR, "porders.py": PO, "porders_s454.py": PS, "order_sheet.py": OSH, "darpan_kal.py": DK, "spine/spine_read.py": SR}


def apply(src, edits, label, pin):
    raw = open(src, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != pin:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (src, m, pin))
        return None
    t = raw.decode("utf-8")
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
    ap.add_argument("--map", required=True, help="the clone's claude_code_briefs/DUTY_MAP.json (at its FROM pin, or already at the kit's TO pin)")
    ap.add_argument("--map-to", default="", help="the kit's TO pin of DUTY_MAP.json (PINS.sh): a map already there is passed through")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = {}
    for label, edits in EDITS.items():
        out = apply(os.path.join(a.finance, label), edits, label, FROM[label])
        if out is None:
            return 2
        built[label] = out
    raw = open(a.map, "rb").read()
    mm = hashlib.md5(raw).hexdigest()
    if a.map_to and mm == a.map_to:
        print("DUTY_MAP.json is already the kit's (%s): passed through unchanged" % mm)
        built["DUTY_MAP.json"] = raw
    else:
        out = apply(a.map, DM, "DUTY_MAP.json", MAP_FROM)
        if out is None:
            return 2
        j = json.loads(out.decode("utf-8"))                   # the edited text is still one JSON document
        d = [x for x in j["duties"] if x["id"] == "reception.medicine_orders"][0]
        assert j["version"] == 15 and "= 'darpan' THEN" in d["due_sql"] and d["due_sql"].count("CASE WHEN") == 1, "the map's shape"
        built["DUTY_MAP.json"] = out
    os.makedirs(os.path.join(a.out, "spine"), exist_ok=True)
    for label, out in built.items():
        dst = os.path.join(a.out, label)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s md5 %s  (FROM %s)" % (dst, hashlib.md5(out).hexdigest(), FROM.get(label, MAP_FROM)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
