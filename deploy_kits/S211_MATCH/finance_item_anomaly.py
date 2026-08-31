#!/usr/bin/env python3
"""
finance_item_anomaly.py -- S211: a bill line that does not look like its item.

THE CASE THAT PROMPTED IT (owner, 31-Aug-2026)
    A June bill charged 20 tubes of an ointment. The patient ordered 2 and got 2.
    Staff "corrected" it later with Marg's stock-adjustment feature -- so the
    STOCK balanced and the BILL stayed wrong. The owner blocked that feature for
    all users on 30-Aug, which closes the future hole; it does not examine the
    past, and nothing in the system would ever have surfaced this.

TWO SIGNALS, both computable from sale_line_item alone (17,146 lines, amount_p
present on every one). Neither needs a voucher, an adjustment export, or any
cooperation from Marg -- which matters, because F-228 already records that an
in-place Marg edit can write no voucher at all.

  1  RATE THAT DOES NOT MATCH THE ITEM. For each item, the per-unit amount this
     bill implies against what that item normally costs. Billing 20 units while
     charging for 2 makes the implied rate a tenth of normal -- a very loud
     signal, and the exact footprint of the case above.

  2  QUANTITY FAR ABOVE WHAT THIS ITEM EVER SELLS AS. An ointment that leaves in
     ones and twos, leaving in twenties.

WHAT IT WILL NOT DO
  It never accuses. Both signals are relative to the item's OWN history, and a
  legitimate bulk purchase looks identical to an error -- so a flag is a row to
  look at, never a finding. And an item with too little history to have a normal
  is REPORTED AS SUCH rather than compared against a median of two.

READ-ONLY. Writes nothing.
"""
import collections
import os
import re
import statistics

MIN_HISTORY = int(os.environ.get("ITEM_MIN_HISTORY", "5"))

# THE RARE-ITEM RULE, and it is the one that finds the owner's June bill.
#
# ENZOMAC OINTMENT sold four times in five months, every line 1.0 -- except
# 30-Jun-2026, bill A001988, which billed 20. Before that day the item had ONE
# prior sale, so MIN_HISTORY=5 set the line aside as "too little history to
# judge" and the strongest signal in the whole dataset went unexamined.
#
# A twentyfold jump over everything an item has ever sold as does not need five
# observations to be worth a look. It needs one. So: below MIN_HISTORY the
# normal band is not computed at all, but a line far beyond ANY prior quantity
# is still surfaced -- and labelled as resting on thin history, so nobody reads
# more into it than it can carry.
EXTREME_MULTIPLE = float(os.environ.get("ITEM_QTY_EXTREME", "8.0"))
# THE QUANTITY YARDSTICK IS THE ITEM'S OWN CEILING, NOT ITS MEDIAN.
#
# S211, first real run: four times the median flagged 445 lines over five
# months, almost all of them tablets at 90-120 units -- six strips of a 1*15
# pack, which is a month's course and entirely normal. It also MISSED the one
# case the owner already knew about. A rule that floods on the ordinary and
# misses the known fault is worse than none.
#
# So a line is unusual when it exceeds what this item has EVER sold as. Ninety
# tablets of a drug that regularly leaves in ninety is not news; twenty of
# something that has never left in more than two is.
QTY_OVER_CEILING = float(os.environ.get("ITEM_QTY_OVER_CEILING", "1.5"))

# THE RATE TEST IS RELATIVE TO THE ITEM'S OWN SPREAD, not a fixed percentage.
#
# Owner, 31-Aug-2026: orthotics carry a defined Marg discount of up to 35% or
# higher, and some hyaluronic acid injections do too -- a 22,000 MRP item sold
# at 15,500 (30% off), a 17,600 item given 600 off (3.4%). The SAME item class
# legitimately spans 3% to 30%, so any fixed tolerance either flags every
# orthotic or misses a tenfold error on an ointment.
#
# So each item is judged against how much ITS OWN rate normally moves, using the
# median absolute deviation -- which a single outlier cannot inflate the way a
# standard deviation can. An item that always sells at one price has a spread of
# zero, and a floor applies so that a zero spread does not make every rounding
# difference an anomaly.
MAD_MULTIPLE = float(os.environ.get("ITEM_MAD_MULTIPLE", "6.0"))
RATE_FLOOR = float(os.environ.get("ITEM_RATE_FLOOR", "0.35"))   # when spread is 0


def pack_size(pack):
    """Marg prints the pack as '1*10' -- ten units to a strip. Returns 10.

    S211, found on the first real run: 2,330 of 3,247 lines were being thrown
    away as 'quantity not comparable' because the loose part was non-zero. The
    pack size is the divisor that makes '0:5' comparable to '1:0', and it was
    sitting unused in its own column the whole time.
    """
    m = re.search(r"(\d+)\s*\*\s*(\d+)", str(pack or ""))
    if m:
        n = int(m.group(2))
        return n if 0 < n <= 1000 else None
    return None


def units(qty_raw, pack=None):
    """Marg prints 'strips:loose'. Returns the count in SINGLE UNITS, or None.

    strips * pack_size + loose. Without a pack size a partial strip cannot be
    expressed in the same terms as a whole one, so it returns None rather than
    a guess: a rate computed from a misread quantity would manufacture exactly
    the anomaly this module exists to find.
    """
    s = str(qty_raw or "").strip()
    m = re.fullmatch(r"(\d+)\s*[:\.]\s*(\d+)", s)
    if m:
        strips, loose = int(m.group(1)), int(m.group(2))
        if loose == 0:
            ps = pack_size(pack)
            return strips * ps if ps else strips
        ps = pack_size(pack)
        if ps:
            return strips * ps + loose
        return loose if strips == 0 else None
    if re.fullmatch(r"\d+", s):
        return int(s)
    return None


def item_norms(con, before_date=None):
    """Per item: what it usually rates and how much of it usually leaves.

    STRICTLY BEFORE the day being judged. S211: with the day included, the two
    outlier lines being examined pushed the item's own ceiling up to their own
    value and cleared themselves. A day is judged against the days before it,
    never against itself -- and the median is used, not the mean, for the same
    reason.
    """
    q = ("SELECT item_key, qty_raw, pack, amount_p FROM sale_line_item "
         "WHERE is_return=0 AND amount_p IS NOT NULL")
    a = ()
    if before_date:
        q += " AND business_date < ?"
        a = (before_date,)
    # amount_p IS THE RATE, not the line amount.
    # Proved against the Marg archive at S211: of 88 items seen at more than one
    # quantity, 71 print an IDENTICAL number every time -- PATOPAN DSR reads
    # 100.00 whether the line is one loose tablet or four. Dividing it by the
    # quantity (the first version of this module did) manufactured a spread that
    # does not exist, and produced 345 false rate flags in thirty days.
    rates, qtys = collections.defaultdict(list), collections.defaultdict(list)
    for r in con.execute(q, a):
        u = units(r["qty_raw"], r["pack"])
        if u:
            qtys[r["item_key"]].append(u)
        if r["amount_p"]:
            rates[r["item_key"]].append(float(r["amount_p"]))
    out = {}
    for k in set(list(rates) + list(qtys)):
        rl, ql = rates.get(k, []), qtys.get(k, [])
        med = statistics.median(rl) if rl else None
        mad = (statistics.median([abs(x - med) for x in rl])
               if rl and med is not None else None)
        out[k] = dict(n=len(ql),
                      rate=med, rate_mad=mad,
                      rate_lo=min(rl) if rl else None,
                      rate_hi=max(rl) if rl else None,
                      qty=statistics.median(ql) if ql else None,
                      qty_max=max(ql) if ql else None,
                      # the ceiling: the 95th percentile of what this item has
                      # ever sold as, so one freak line does not raise the bar
                      # for everything after it
                      qty_p95=(sorted(ql)[min(len(ql) - 1,
                               int(round(0.95 * (len(ql) - 1))))] if ql else None))
    return out


def scan_day(con, business_date, unit="medical", norms=None):
    """Every sale line of the day, measured against its own item's history."""
    norms = norms if norms is not None else item_norms(con, business_date)
    rows = con.execute(
        "SELECT l.bill_no, l.seq, l.item_name, l.item_key, l.qty_raw, l.pack, "
        "       l.amount_p, "
        "       s.patient_ref_id, p.name, p.clinic_id "
        "FROM sale_line_item l "
        "LEFT JOIN sale_item s ON s.source_ref = l.bill_no "
        "LEFT JOIN patient_ref p ON p.id = s.patient_ref_id "
        "WHERE l.business_date=? AND l.is_return=0 "
        "ORDER BY l.bill_no, l.seq", (business_date,)).fetchall()
    out, tally = [], collections.Counter()
    for r in rows:
        u = units(r["qty_raw"], r["pack"])
        n = norms.get(r["item_key"]) or {}
        flags, detail = [], []
        if n.get("n", 0) < MIN_HISTORY:
            mx = n.get("qty_max")
            if u and mx and mx > 0 and u >= mx * EXTREME_MULTIPLE:
                tally["FAR BEYOND ANYTHING SEEN (thin history)"] += 1
                out.append(dict(bill=r["bill_no"], seq=r["seq"],
                                item=r["item_name"], qty_raw=r["qty_raw"],
                                units=u, rate_p=r["amount_p"],
                                name=r["name"] or "", clinic_id=r["clinic_id"] or "",
                                verdict="FAR BEYOND ANYTHING SEEN",
                                detail="%d units on one line. This item has sold "
                                       "only %d time(s) before and never more "
                                       "than %g -- thin history, so this is a "
                                       "flag to look at, not a finding"
                                       % (u, n.get("n", 0), mx),
                                item_seen=n.get("n")))
            else:
                tally["too little history to judge"] += 1
            continue
        if n.get("rate") and r["amount_p"]:
            rate = float(r["amount_p"])          # the printed rate, as-is
            if n["rate"] > 0:
                dev = (rate - n["rate"]) / n["rate"]
                mad = n.get("rate_mad") or 0.0
                # an item whose own price moves a lot must be allowed to move;
                # one that never moves is judged on a plain percentage floor.
                band = max(MAD_MULTIPLE * mad, RATE_FLOOR * n["rate"])
                if abs(rate - n["rate"]) >= band:
                    flags.append("RATE OFF")
                    detail.append("this line is rated %.2f; this item usually "
                                  "rates %.2f and has ranged %.2f to %.2f "
                                  "(%+.0f%%)"
                                  % (rate / 100.0, n["rate"] / 100.0,
                                     (n.get("rate_lo") or 0) / 100.0,
                                     (n.get("rate_hi") or 0) / 100.0, dev * 100))
        if u is None:
            # informational, NOT a verdict bucket: the rate can still be judged,
            # so counting it as a bucket would tally this line twice. Keys
            # beginning with "_" are notes; the verdict buckets are disjoint and
            # sum to the number of lines.
            tally["_quantity not comparable"] += 1
        elif n.get("qty_p95") and n["qty_p95"] > 0 \
                and u >= n["qty_p95"] * QTY_OVER_CEILING:
            flags.append("QUANTITY HIGH")
            detail.append("%d units on one line; this item usually leaves in %g, "
                          "its busiest lines are around %g, and its highest ever "
                          "was %g"
                          % (u, n.get("qty") or 0, n["qty_p95"],
                             n.get("qty_max") or 0))
        if not flags:
            tally["looks normal"] += 1
            continue
        worst = "RATE OFF" if "RATE OFF" in flags else "QUANTITY HIGH"
        if len(flags) > 1:
            worst = "RATE OFF AND QUANTITY HIGH"
        tally[worst] += 1
        out.append(dict(bill=r["bill_no"], seq=r["seq"], item=r["item_name"],
                        qty_raw=r["qty_raw"], units=u, rate_p=r["amount_p"],
                        name=r["name"] or "", clinic_id=r["clinic_id"] or "",
                        verdict=worst, detail=" | ".join(detail),
                        item_seen=n.get("n")))
    return out, dict(tally)
