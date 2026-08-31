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
QTY_MULTIPLE = float(os.environ.get("ITEM_QTY_MULTIPLE", "4.0"))

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


def units(qty_raw):
    """Marg prints 'strips:loose'. Returns a comparable unit count, or None.

    None rather than a guess: a rate computed from a misread quantity would
    manufacture exactly the anomaly this module exists to find.
    """
    s = str(qty_raw or "").strip()
    m = re.fullmatch(r"(\d+)\s*[:\.]\s*(\d+)", s)
    if m:
        strips, loose = int(m.group(1)), int(m.group(2))
        return strips if loose == 0 else None
    if re.fullmatch(r"\d+", s):
        return int(s)
    return None


def item_norms(con, upto_date=None):
    """Per item: the usual per-unit rate and the usual quantity, from its own
    history. Median, not mean -- one 20-tube line must not move the yardstick
    it is about to be measured against."""
    q = ("SELECT item_key, qty_raw, amount_p FROM sale_line_item "
         "WHERE is_return=0 AND amount_p IS NOT NULL")
    a = ()
    if upto_date:
        q += " AND business_date <= ?"
        a = (upto_date,)
    rates, qtys = collections.defaultdict(list), collections.defaultdict(list)
    for r in con.execute(q, a):
        u = units(r["qty_raw"])
        if not u:
            continue
        qtys[r["item_key"]].append(u)
        if u > 0 and r["amount_p"]:
            rates[r["item_key"]].append(r["amount_p"] / float(u))
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
                      qty_max=max(ql) if ql else None)
    return out


def scan_day(con, business_date, unit="medical", norms=None):
    """Every sale line of the day, measured against its own item's history."""
    norms = norms if norms is not None else item_norms(con, business_date)
    rows = con.execute(
        "SELECT l.bill_no, l.seq, l.item_name, l.item_key, l.qty_raw, l.amount_p, "
        "       s.patient_ref_id, p.name, p.clinic_id "
        "FROM sale_line_item l "
        "LEFT JOIN sale_item s ON s.source_ref = l.bill_no "
        "LEFT JOIN patient_ref p ON p.id = s.patient_ref_id "
        "WHERE l.business_date=? AND l.is_return=0 "
        "ORDER BY l.bill_no, l.seq", (business_date,)).fetchall()
    out, tally = [], collections.Counter()
    for r in rows:
        u = units(r["qty_raw"])
        n = norms.get(r["item_key"]) or {}
        flags, detail = [], []
        if u is None:
            tally["quantity not comparable"] += 1
            continue
        if n.get("n", 0) < MIN_HISTORY:
            tally["too little history to judge"] += 1
            continue
        if n.get("rate") and u > 0 and r["amount_p"]:
            rate = r["amount_p"] / float(u)
            if n["rate"] > 0:
                dev = (rate - n["rate"]) / n["rate"]
                mad = n.get("rate_mad") or 0.0
                # an item whose own price moves a lot must be allowed to move;
                # one that never moves is judged on a plain percentage floor.
                band = max(MAD_MULTIPLE * mad, RATE_FLOOR * n["rate"])
                if abs(rate - n["rate"]) >= band:
                    flags.append("RATE OFF")
                    detail.append("this line implies %.2f per unit; this item "
                                  "usually goes at %.2f and has ranged %.2f to "
                                  "%.2f (%+.0f%%)"
                                  % (rate / 100.0, n["rate"] / 100.0,
                                     (n.get("rate_lo") or 0) / 100.0,
                                     (n.get("rate_hi") or 0) / 100.0, dev * 100))
        if n.get("qty") and n["qty"] > 0 and u >= n["qty"] * QTY_MULTIPLE:
            flags.append("QUANTITY HIGH")
            detail.append("%d units on one line; this item usually leaves in %g, "
                          "and its highest ever was %g"
                          % (u, n["qty"], n.get("qty_max") or 0))
        if not flags:
            tally["looks normal"] += 1
            continue
        worst = "RATE OFF" if "RATE OFF" in flags else "QUANTITY HIGH"
        if len(flags) > 1:
            worst = "RATE OFF AND QUANTITY HIGH"
        tally[worst] += 1
        out.append(dict(bill=r["bill_no"], seq=r["seq"], item=r["item_name"],
                        qty_raw=r["qty_raw"], units=u, amount_p=r["amount_p"],
                        name=r["name"] or "", clinic_id=r["clinic_id"] or "",
                        verdict=worst, detail=" | ".join(detail),
                        item_seen=n.get("n")))
    return out, dict(tally)
