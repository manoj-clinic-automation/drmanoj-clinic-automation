#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s928.py -- kit S928_STOCK_ONE_RULE (22-Nov-2026, Sanjeevni session 503). Builds the TO files from the live bytes (read whole:
stock_figure.py cc1cef5d, stock_watch.py 5acf3cf0 -- S927's) by EXACT anchors, each required to occur exactly once (F-472).
    python3 -B make_s928.py <live_dir with stock_figure.py and stock_watch.py> <out_dir>"""
import hashlib
import io
import os
import sys

FROM = {"stock_figure.py": "cc1cef5d", "stock_watch.py": "5acf3cf0"}


def rd(p):
    with io.open(p, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(t)


def once(t, a, what):
    n = t.count(a)
    if n != 1:
        raise SystemExit("anchor %s occurs %d times, not once" % (what, n))


def sub(t, a, b, what):
    once(t, a, what)
    return t.replace(a, b)


def main():
    live, out = sys.argv[1], sys.argv[2]
    here = os.path.dirname(os.path.abspath(__file__))
    for f, h in FROM.items():
        got = hashlib.md5(open(os.path.join(live, f), "rb").read()).hexdigest()[:8]
        if got != h:
            raise SystemExit("%s is %s, the kit was written on %s" % (f, got, h))
    # ---------------------------------------------------------------- stock_figure.py
    t = rd(os.path.join(live, "stock_figure.py"))
    t = sub(t, 'KIT = "S628_ONE_NAME_LIST"                               # v1.5 S628',
            'KIT = "S928_STOCK_ONE_RULE"                              # v1.6 S928 (the bill over the tap; a count by its time), v1.5 S628', "A1 KIT")
    t = sub(t, '        return sum(float(a["units"] or 0) for a in _sw()._arrivals(ctx.con, name, since_iso, sp, ctx=ctx)',
            '        return sum(_count_units(con, sp, a, ctx) for a in _sw()._arrivals(ctx.con, name, since_iso, sp, ctx=ctx)   # S928: the scanned bill\'s units when it speaks', "A2 taps")
    t = sub(t, '        return sum(a["units"] for a in scan_lines(con, sp, item, since_iso, ctx) if carried(con, sp, a, ctx) is None and not expired(con, sp, a, ctx))',
            '        return sum(_count_units(con, sp, a, ctx) for a in scan_lines(con, sp, item, since_iso, ctx) if carried(con, sp, a, ctx) is None and not expired(con, sp, a, ctx))   # S928', "A3 scan_arrivals")
    t = sub(t, '    if sx is not None:                                        # S613: the one helper -- the old key\'s share to the split day, its own key after\n'
               '        sold, ret, bought = split_moves(sp, sx, share, mine["day"], a, incl_from=True)\n',
            '    ev = mine["kind"] != "count" and evening_count(mine.get("at"), _s928_settings(ctx)[1], mine["day"])   # S928 (F-1564): a spot count at or after the evening hour is the END of its day (never the full count: its at is the entry moment)\n'
            '    out["base_evening"] = ev\n'
            '    if sx is not None:                                        # S613: the one helper -- the old key\'s share to the split day, its own key after\n'
            '        sold, ret, bought = split_moves(sp, sx, share, mine["day"], a, incl_from=not ev)\n', "A4a shelf split_moves")
    t = sub(t, '        sold, ret, bought = moves(sp, k, mine["day"], a, incl_from=True)\n        out.update(sold=round(share * sold, 2)',
            '        sold, ret, bought = moves(sp, k, mine["day"], a, incl_from=not ev)   # S928: the count day\'s sales in only for a count before the evening hour\n        out.update(sold=round(share * sold, 2)', "A4b shelf moves")
    t = sub(t, '    records = (float(M["figure"]) + float(M["taps"] or 0)) if M else None\n',
            '    s928_sa = scan_arrivals(con, sp, name, M["closing"]["stamp_iso"], ctx) if M else 0.0   # S928: a scan-tied delivery counts for an uncounted item too (once)\n    records = (float(M["figure"]) + float(M["taps"] or 0) + s928_sa) if M else None\n', "A6 expect_for_point")
    t = sub(t, '    arr = taps(con, sp, name, mine["at"], ctx) + scan_arrivals(con, sp, name, mine["day"], ctx)     # S583: both under the one rule, both here\n',
            '    arr = taps(con, sp, name, mine["at"], ctx) + scan_arrivals(con, sp, name, (mine["day"] if mine["kind"] == "count" else mine["at"]), ctx)   # S583: both under the one rule; S928: a spot count by its moment\n', "A5b arrivals since")
    t = sub(t, '    return dict(expected=records, basis="marg", provisional=float(M["taps"] or 0), as_on=M["closing"]["as_on"], approx=False,\n',
            '    return dict(expected=records, basis="marg", provisional=float(M["taps"] or 0) + s928_sa, as_on=M["closing"]["as_on"], approx=False,   # S928: a scan-tied delivery is provisional too\n', "A6b provisional")
    t = sub(t, '            import order_track as OT                          # noqa: PLC0415 -- beside this file\n            octx = OT.Ctx(con)\n            if not octx.ok:\n                out = None\n',
            '            import order_track as OT                          # noqa: PLC0415 -- beside this file\n            octx = _s928_octx(ctx)                            # S928: the one scan context per Ctx (s825 and bill_units share it)\n            if octx is None:\n                out = None\n', "A7 s825 shares octx")
    t = sub(t, '                for e in by.values():\n                    heads = []\n                    for sid in sorted(e["sids"]):\n                        h = octx.head(sid)\n                        if h in octx.scans and h not in heads and octx.usable(h) and octx.names(h):\n                            heads.append(h)\n                    if not heads:\n                        continue                              # no tied scan usable and read: not judged\n                    reads = [(n, octx.scans[h].get("stamp_no") or "#%d" % h) for h in heads for n in octx.names(h)]\n                    hit = OT.match_lines(con, e["sn"], list(dict.fromkeys(e["items"].values())), reads, octx.sf)\n                    for lid, it in e["items"].items():\n                        out[lid] = it in hit\n',
            '                for oid, e in by.items():\n                    M = _s928_order_match(ctx, octx, OT, oid)   # S928: ONE match per order -- s825 and bill_units read the same hit\n                    if M is None:\n                        continue                              # no tied scan usable and read: not judged\n                    for lid, it in e["items"].items():\n                        out[lid] = it in M["hit"]\n', "A7b s825 one match")
    marker = '# ------------------------------------------------------------------ the side-by-side week (witness only; 4b-2 retires the old ways)'
    t = sub(t, marker, rd(os.path.join(here, "s928_block.py")) + marker, "A5 block")
    wr(os.path.join(out, "stock_figure.py"), t)
    # ---------------------------------------------------------------- stock_watch.py
    w = rd(os.path.join(live, "stock_watch.py"))
    w = sub(w, 'VERSION = "1.8"\nKIT = "S587_MORNING_FLOW"                                     # v1.7 was S584_SMALL_FIXES',
            'VERSION = "1.9"\nKIT = "S928_STOCK_ONE_RULE"                                   # v1.9 S928 (the bill over the tap; the day\'s count line), v1.8 S587_MORNING_FLOW, v1.7 was S584_SMALL_FIXES', "B0 KIT")
    w = sub(w, '              "before the order was written up). 0 = only bills dated on or after the order day."),\n',
            '              "before the order was written up). 0 = only bills dated on or after the order day."),\n'
            '    dict(key="arrival.bill_over_tap", label="Arrival: the scanned bill over the tap", kind="choice", default="1", seed="1", choices=(("1", "on"), ("0", "off")),\n'
            '         hint="S928, the owner 22-Nov: a delivery counts by the quantity the dealer\'s scanned bill carries for the medicine, never by reception\'s tap -- a tap above the bill "\n'
            '              "is a short supply (back on that dealer\'s next order), a tapped medicine the bill does not carry counts nothing. Off: the tap stands, as before."),\n'
            '    dict(key="count.evening_hour", label="Count: the evening hour (a count at or after it ends its day)", kind="int", default="17", seed="17", lo=0, hi=23,\n'
            '         hint="S928 (F-1564): a count saved on its own day at or after this hour stands for the END of that day -- its day\'s sales are not taken off again. "\n'
            '              "Darpan\'s morning list is before it; an evening count (TYRO BR, 12-Oct 19:49) is after it."),\n', "B1 SETTINGS")
    w = sub(w, '                bill_grace_days=max(1, num("arrival.bill_grace_days", 3, int)), back_days=max(0, num("arrival.back_days", 2, int)),\n',
            '                bill_grace_days=max(1, num("arrival.bill_grace_days", 3, int)), back_days=max(0, num("arrival.back_days", 2, int)),\n'
            '                bill_over_tap=str(out.get("arrival.bill_over_tap", "1")).strip() not in ("0", "off", "no"),          # S928: stock_figure reads these two\n'
            '                evening_hour=max(0, min(23, num("count.evening_hour", 17, int))),\n', "B2 settings()")
    w = sub(w, 'if n["kind"] in ("cadence", "plan_lapsed", "trace_unexplained", "spot_missed", "close_watch", "ortho_closed", "asked_count") and n["at"][:10]',
            'if n["kind"] in ("cadence", "plan_lapsed", "trace_unexplained", "spot_missed", "close_watch", "ortho_closed", "asked_count", "count_day") and n["at"][:10]', "B3a kinds")
    w = sub(w, '                out.append(dict(cls="warn" if n["kind"] not in ("close_watch", "ortho_closed") and "matches Marg" not in (n["text"] or "") else "info",\n'
               '                                target="stock", text=n["text"]))   # S436: ortho_closed; S894: asked_count',
            '                out.append(dict(cls=_s928_cls(n), target="stock", text=n["text"]))   # S436: ortho_closed; S894: asked_count; S928: count_day', "B3b cls")
    w = sub(w, '    _s894_asked_back(con, r[1], qty_units, sp)              # S894: before the roster_id close below, which misses a carried row\n',
            '    _s894_asked_back(con, r[1], qty_units, sp)              # S894: before the roster_id close below, which misses a carried row\n'
            '    _s928_count_day(con, sp)                                 # S928: the day\'s one line on his Needs-you\n', "B4 answer_roster")
    w = sub(w, '    _s894_asked_back(con, info["item"], qty_units, sp)       # S894\n',
            '    _s894_asked_back(con, info["item"], qty_units, sp)       # S894\n    _s928_count_day(con, sp)                                 # S928\n', "B5 darpan_point")
    w = sub(w, '        _s894_refix(con, old[1], q, sp)                         # S894\n',
            '        _s894_refix(con, old[1], q, sp)                         # S894\n        _s928_count_day(con, sp)                             # S928: the day\'s line follows the corrected count\n', "B6 correct_roster")
    w = sub(w, '\ndef ask(con, item, who, sp=None):\n', '\n' + rd(os.path.join(here, "s928_watch_block.py")) + 'def ask(con, item, who, sp=None):\n', "B7 block")
    wr(os.path.join(out, "stock_watch.py"), w)
    for f in ("stock_figure.py", "stock_watch.py"):
        print("%s -> %s" % (f, hashlib.md5(open(os.path.join(out, f), "rb").read()).hexdigest()[:8]))


if __name__ == "__main__":
    main()
