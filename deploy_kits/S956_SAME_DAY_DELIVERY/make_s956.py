#!/usr/bin/env python3
# make_s956.py · kit S956_SAME_DAY_DELIVERY · Sanjeevni session 519 · 25-Nov-2026
# stock_figure.py (S952's 500a7d46) -> v1.7: a spot / Darpan count before the evening hour stands for the START of its day, so the purchases
# dated that day are added to the shelf figure after it -- except a bill an order line shows arrived (a person's tap, or its order's scan) at
# or before the count's moment. (S928 left every same-day purchase out: JAKMAC 5, counted 28:4 at 10:27 on 23-11, Gunina bill 100075 of that
# day (20:0) never reached the shelf figure -- -20:0 on the Stock check page.)   python make_s956.py FROM_DIR OUT_DIR
import hashlib
import os
import sys

FROM = "500a7d46"


def once(s, old, new):
    n = s.count(old)
    if n != 1:
        sys.exit("!! anchor found %d times: %r" % (n, old[:90]))
    return s.replace(old, new)


A1 = 'VERSION = "1.6"   '
B1 = 'VERSION = "1.7"   # v1.7 S956: a count before the evening hour -- its day\'s purchases after it (unless delivered before) ·'
A2 = '''            out["bill_cut"] = round(cut, 2)
        out.update(sold=round(share * sold, 2), returned=round(share * ret, 2), bought=round(share * bought, 2))'''
B2 = '''            out["bill_cut"] = round(cut, 2)
        if mine["kind"] != "count":                           # S956: a spot / Darpan count -- the day's deliveries that came AFTER it
            sd = _s956_same_day(ctx, sp, k, name, mine)
            bought += sd
            out["same_day_bought"] = round(sd, 2)
        out.update(sold=round(share * sold, 2), returned=round(share * ret, 2), bought=round(share * bought, 2))'''
A3 = '''def _bill_n(text):'''
B3 = '''def _s956_until(ctx):
    """count.same_day_until (the hour, 12 to start): a count saved before it is taken as before the day's deliveries."""
    if "s956h" not in ctx.c:
        h = 12
        try:
            r = ctx.con.execute("SELECT value FROM setting WHERE key='count.same_day_until'").fetchone() if ctx.con is not None else None
            h = int(float(r[0])) if (r and str(r[0] or "").strip()) else 12
        except (sqlite3.Error, TypeError, ValueError):
            h = 12
        ctx.c["s956h"] = max(0, min(23, h))
    return ctx.c["s956h"]


def _s956_same_day(ctx, sp, k20, name, mine):
    """S956: the units of the key's purchases (returns signed) dated the count's own day that reached the shelf AFTER the count. A bill whose
    delivery line (a tap, or its order's scan -- the bill read from the line's answer or from the one arrivals rule) shows when it arrived:
    added when that moment is after the count, never when at or before it. A bill with no arrival moment: added only for a count saved before
    count.same_day_until (12:00 to start: deliveries come in the afternoon) -- never for a later count, never for an evening one (S928)."""
    day, at = str(mine.get("day") or "")[:10], str(mine.get("at") or "")[:19].replace(" ", "T")
    if len(at) < 13 or evening_count(at, _s928_settings(ctx)[1], day):
        return 0.0
    try:
        rows = sp.q("SELECT supkey, bill, SUM(CASE WHEN direction IN ('RETURN','PURCHASE_RETURN') THEN -units ELSE units END) AS u FROM sp_purchase_line "
                    "WHERE k20=? AND date=? AND direction IN ('PURCHASE','RETURN','PURCHASE_RETURN') GROUP BY supkey, bill", k20, day)
    except Exception:                                         # noqa: BLE001
        return 0.0
    if not rows:
        return 0.0
    seen = {}                                                 # bill -> the earliest arrival moment of a delivery line it carries
    try:
        lines = list(_sw()._arrivals(ctx.con, name, "", sp, ctx=ctx)) + list(scan_lines(ctx.con, sp, name, "", ctx))
        for a in lines:
            b = str(a.get("billed_bill_no") or "").strip()
            if not b:
                h = carried(ctx.con, sp, a, ctx)
                b = str((h or {}).get("bill") or "").strip()
            if not b:
                continue
            by = str(a.get("arrived_by") or "")
            m = str(a.get("scan_at") or "") if by in ("marg", "", "scan") else str(a.get("arrived_at") or a.get("scan_at") or "")
            m = m.strip().replace(" ", "T")[:19]
            if m and (_bill(b) not in seen or m < seen[_bill(b)]):
                seen[_bill(b)] = m
    except Exception:                                         # noqa: BLE001
        pass
    early = int(at[11:13]) < _s956_until(ctx)
    tot = 0.0
    for r in rows:
        m = seen.get(_bill(r["bill"]))
        if m is not None:
            if m > at:
                tot += float(r["u"] or 0)
        elif early:
            tot += float(r["u"] or 0)
    return tot


def _bill_n(text):'''


def main(argv):
    src, out = argv[1], argv[2]
    b = open(os.path.join(src, "stock_figure.py"), "rb").read()
    h = hashlib.md5(b).hexdigest()
    if not h.startswith(FROM):
        sys.exit("!! stock_figure.py is %s, not the FROM pin %s" % (h[:8], FROM))
    s = b.decode("utf-8")
    for a, n in ((A1, B1), (A2, B2), (A3, B3)):
        s = once(s, a, n)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "stock_figure.py"), "wb").write(s.encode("utf-8"))
    print("stock_figure.py %s -> %s" % (h[:8], hashlib.md5(s.encode("utf-8")).hexdigest()[:8]))


if __name__ == "__main__":
    main(sys.argv)
