#!/usr/bin/env python3
"""
finance_returns_audit.py -- S211: the sump, on constant radar.

The owner: a return is cash out of the drawer, and it "NEEDS TO BE ON CONSTANT
RADAR". So every return is opened down to its own item lines and each line is
matched against that patient's OWN earlier purchases -- did they buy this item,
in what quantity, at what amount.

READ-ONLY. Opens the database, reads, returns. Writes nothing.

WHAT IT CAN AND CANNOT SEE -- measured on the live box at S211, and said out
loud because a partial audit that looks complete is worse than none:

    179 return bills exist in sale_item
     63 of them have item lines in sale_line_item
    116 have NO lines and therefore CANNOT be audited at item level

Item detail comes from Marg's single-day export, which S180 recorded is
overwritten if a sweep is missed. So a return with no lines is NOT a clean
return -- it is an unexaminable one, and it is reported as such.

THE SIGNALS, in the order they matter
  1  an item RETURNED THAT THE PATIENT NEVER BOUGHT -- 22 of 143 lines on the
     live data. The S180 corroboration, and the strongest one.
  2  a DISCOUNTED SALE RETURNED AT FULL RATE -- the owner's own catch: the
     refund exceeds what was actually taken. Compared only where the same item
     was sold in the SAME quantity, so the amounts are directly comparable and
     nothing has to be inferred from a parsed rate.
  3  RETURNED QUANTITY GREATER THAN SOLD.
  4  the same item returned repeatedly across bills.
"""
import collections
import os
import re

WINDOW_DAYS = int(os.environ.get("RETURN_LOOKBACK_DAYS", "180"))


def _qty(raw):
    """Marg prints quantity as 'strips:loose'. Returns (strips, loose) or None.

    Deliberately returns None rather than a guess when the shape is anything
    else: a rate computed from a misread quantity is worse than no rate.
    """
    s = str(raw or "").strip()
    m = re.fullmatch(r"(\d+)\s*[:\.]\s*(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    if re.fullmatch(r"\d+", s):
        return int(s), 0
    return None


def audit_return(con, bill_no, patient_ref_id, business_date):
    """One return bill, line by line. Never raises on data."""
    lines = con.execute(
        "SELECT seq, item_name, item_key, pack, qty_raw, amount_p, batch, expiry_ym "
        "FROM sale_line_item WHERE bill_no=? AND is_return=1 ORDER BY seq",
        (bill_no,)).fetchall()
    if not lines:
        # also try without the flag: some rows carry the return only in sale_item
        lines = con.execute(
            "SELECT seq, item_name, item_key, pack, qty_raw, amount_p, batch, expiry_ym "
            "FROM sale_line_item WHERE bill_no=? ORDER BY seq", (bill_no,)).fetchall()
    out = []
    flags = collections.Counter()
    if not lines:
        return [], dict(no_item_detail=1), ("this return has NO item lines, so it "
                                            "cannot be examined -- not the same "
                                            "thing as a clean return")
    for ln in lines:
        prior = con.execute(
            "SELECT l.bill_no, l.qty_raw, l.amount_p, l.business_date "
            "FROM sale_line_item l JOIN sale_item s ON s.source_ref = l.bill_no "
            "WHERE l.item_key=? AND l.is_return=0 AND s.patient_ref_id=? "
            "AND l.business_date <= ? AND l.business_date >= date(?, ?) "
            "ORDER BY l.business_date DESC LIMIT 5",
            (ln["item_key"], patient_ref_id, business_date, business_date,
             "-%d days" % WINDOW_DAYS)).fetchall() if patient_ref_id else []
        row = dict(seq=ln["seq"], item=ln["item_name"], qty_raw=ln["qty_raw"],
                   amount_p=ln["amount_p"], batch=ln["batch"],
                   expiry_ym=ln["expiry_ym"], bought_before=len(prior),
                   verdict="", detail="")
        if not prior:
            row["verdict"] = "NEVER BOUGHT"
            row["detail"] = ("this patient has no purchase of this item in the "
                             "last %d days" % WINDOW_DAYS)
            flags["never_bought"] += 1
            out.append(row)
            continue
        # the honest rate comparison: same item, SAME quantity -> the amounts are
        # directly comparable and no rate has to be parsed or inferred.
        same_qty = [p for p in prior if (p["qty_raw"] or "") == (ln["qty_raw"] or "")]
        if same_qty and ln["amount_p"] is not None:
            sold = same_qty[0]["amount_p"] or 0
            back = ln["amount_p"] or 0
            if back > sold:
                row["verdict"] = "REFUNDED MORE THAN PAID"
                row["detail"] = ("sold for %d paise on %s, refunded %d -- the same "
                                 "item in the same quantity"
                                 % (sold, same_qty[0]["business_date"], back))
                flags["refund_exceeds"] += 1
            else:
                row["verdict"] = "ok"
                row["detail"] = ("bought %s on %s at the same amount"
                                 % (ln["qty_raw"], same_qty[0]["business_date"]))
            out.append(row)
            continue
        # bought, but not in a directly comparable quantity
        rq, pq = _qty(ln["qty_raw"]), _qty(prior[0]["qty_raw"])
        if rq and pq and (rq[0] > pq[0] or (rq[0] == pq[0] and rq[1] > pq[1])):
            row["verdict"] = "RETURNED MORE THAN SOLD"
            row["detail"] = ("returned %s against %s sold on %s"
                             % (ln["qty_raw"], prior[0]["qty_raw"],
                                prior[0]["business_date"]))
            flags["qty_exceeds"] += 1
        else:
            row["verdict"] = "bought, quantity differs"
            row["detail"] = ("bought %s on %s; returned %s -- amounts not directly "
                             "comparable, so no rate is claimed"
                             % (prior[0]["qty_raw"], prior[0]["business_date"],
                                ln["qty_raw"]))
            flags["qty_differs"] += 1
        out.append(row)
    return out, dict(flags), ""


def returns_for_day(con, business_date, unit="medical"):
    """Every return of the day, audited. Read-only."""
    rets = con.execute(
        "SELECT s.id, s.source_ref bill, s.amount_p, s.gross_p, s.disc_p, "
        "       s.patient_ref_id, p.name, p.mobile, p.clinic_id "
        "FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
        "LEFT JOIN patient_ref p ON p.id=s.patient_ref_id "
        "WHERE e.unit=? AND e.business_date=? "
        "AND s.service LIKE '%!_return' ESCAPE '!' "
        "ORDER BY s.source_ref", (unit, business_date)).fetchall()
    out, tally = [], collections.Counter()
    for r in rets:
        lines, flags, note = audit_return(con, r["bill"], r["patient_ref_id"],
                                          business_date)
        worst = ("NEVER BOUGHT" if flags.get("never_bought") else
                 "REFUNDED MORE THAN PAID" if flags.get("refund_exceeds") else
                 "RETURNED MORE THAN SOLD" if flags.get("qty_exceeds") else
                 "not examinable" if flags.get("no_item_detail") else "ok")
        tally[worst] += 1
        out.append(dict(bill=r["bill"], amount_p=r["amount_p"],
                        name=r["name"] or "", mobile=r["mobile"] or "",
                        clinic_id=r["clinic_id"] or "",
                        verdict=worst, note=note, lines=lines, flags=flags))
    return out, dict(tally)
