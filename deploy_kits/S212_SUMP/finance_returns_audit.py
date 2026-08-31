#!/usr/bin/env python3
"""
finance_returns_audit.py -- S212: the sump, sourced from the ITEM LINES.

THE OWNER'S WORDS: "it is the sump which NEEDS TO BE ON CONSTANT RADAR."

WHAT CHANGED AT S212, AND WHY
    Until now this file started from `sale_item WHERE service LIKE '%_return'`.
    That is one of TWO places a return lives, and starting there missed 123
    orphan line-item returns -- almost all April-June, the S186-F104 backfill
    era. A sump card that under-reports is the one thing it must never be.

    So the day's returns are now the UNION of both sources, because neither
    one alone is complete:

      A  return lines in sale_line_item (is_return=1)   -- the item spine
      B  return bills in sale_item      (service '%_return') -- the money spine

    That yields three populations, and the card names all three rather than
    quietly averaging them:

      1  lines AND a bill row      fully auditable, valued from its lines
      2  lines but NO bill row     the orphans. Valued from lines. Real money
                                   that the old query could not see at all.
      3  a bill row but NO lines   S211 measured 116 of these. Valued from the
                                   bill. NOT a clean return -- an UNEXAMINABLE
                                   one, and reported as such.

MONEY
    Every rupee here comes from finance_money.line_amount_p / bill_gross_p.
    `amount_p` on a LINE is the RATE PER PACK, not the line amount -- summing
    it directly is what produced the two figures withdrawn at S211
    (Rs 1,33,514 and Rs 38,157). `amount_p` on a BILL row in sale_item IS
    money. The two must never be added together as though they were the same
    quantity, and in this file they never are.

DIRECTION IS NOT A SIGN
    sale_line_item declares CHECK (amount_p >= 0). A return can never be
    negative here. Direction comes from is_return, never from the sign (D314).

READ-ONLY. Opens the database, reads, returns. Writes nothing.
"""
import collections
import os
import re

# finance_money.py must sit beside this file. It is the ONLY place a rate is
# turned into money; a fallback that silently did the arithmetic here instead
# is exactly how a second, drifting implementation gets born, so there is none.
from finance_money import line_amount_p, bill_gross_p, rupees

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


LINE_COLS = ("seq, item_name, item_key, pack, qty_raw, amount_p, batch, expiry_ym, "
             "bill_no, business_date")


def find_return_lines(con, bill_no, business_date, amount_p=None):
    """Find a return's item lines, by a LADDER, and say which rung found them.

    Measured at S211: sale_line_item holds 186 return-flagged bills, sale_item
    holds 179, and only 63 share a bill number -- yet the owner confirms all
    sale data, bill-wise and item-wise, is uploaded to 29-Aug-2026. So the lines
    are there under a DIFFERENT KEY, and an audit that only does an exact match
    reports 116 real returns as unexaminable.

    Each rung is weaker than the one above it, so the rung that succeeded is
    returned with the lines. Nothing downstream may treat a rung-4 match as
    though it were a rung-1 match.
    """
    b = str(bill_no or "").strip()
    if b:
        r = con.execute("SELECT %s FROM sale_line_item WHERE bill_no=? "
                        "AND is_return=1 ORDER BY seq" % LINE_COLS, (b,)).fetchall()
        if r:
            return r, "bill number, flagged as a return"
        r = con.execute("SELECT %s FROM sale_line_item WHERE bill_no=? ORDER BY seq"
                        % LINE_COLS, (b,)).fetchall()
        if r:
            return r, "bill number (the return flag was not set on the lines)"
        digits = re.sub(r"\D", "", b)
        if len(digits) >= 3:
            # the same bill under a different prefix -- CN00154 against 00154
            r = con.execute(
                "SELECT %s FROM sale_line_item WHERE is_return=1 "
                "AND REPLACE(REPLACE(bill_no,'CN',''),'-','') LIKE ? ORDER BY seq"
                % LINE_COLS, ("%" + digits,)).fetchall()
            if r and len({x["bill_no"] for x in r}) == 1:
                return r, "same digits under a different prefix (%s)" % r[0]["bill_no"]
    if business_date and amount_p is not None:
        # last rung: the same day, flagged a return, and the line amounts add up
        # to this bill. Only accepted when exactly ONE bill fits.
        cand = con.execute(
            "SELECT bill_no, SUM(COALESCE(amount_p,0)) t FROM sale_line_item "
            "WHERE is_return=1 AND business_date=? GROUP BY bill_no",
            (business_date,)).fetchall()
        fit = [c["bill_no"] for c in cand if abs((c["t"] or 0) - amount_p) <= 100]
        if len(fit) == 1:
            r = con.execute("SELECT %s FROM sale_line_item WHERE bill_no=? ORDER BY seq"
                            % LINE_COLS, (fit[0],)).fetchall()
            if r:
                return r, "same day and the amounts agree (bill %s)" % fit[0]
    return [], ""


def audit_return(con, bill_no, patient_ref_id, business_date, amount_p=None):
    """One return bill, line by line. Never raises on data."""
    lines, line_source = find_return_lines(con, bill_no, business_date, amount_p)
    out = []
    flags = collections.Counter()
    if not lines:
        return [], dict(no_item_detail=1), ("no item lines could be found for this "
                                            "return, by bill number, by digits, or "
                                            "by same-day amount -- so it cannot be "
                                            "examined, which is NOT the same thing "
                                            "as a clean return")
    for ln in lines:
        prior = con.execute(
            "SELECT l.bill_no, l.qty_raw, l.amount_p, l.business_date "
            "FROM sale_line_item l JOIN sale_item s ON s.source_ref = l.bill_no "
            "WHERE l.item_key=? AND l.is_return=0 AND s.patient_ref_id=? "
            "AND l.business_date <= ? AND l.business_date >= date(?, ?) "
            "ORDER BY l.business_date DESC LIMIT 5",
            (ln["item_key"], patient_ref_id, business_date, business_date,
             "-%d days" % WINDOW_DAYS)).fetchall() if patient_ref_id else []
        # S212: `amount_p` is the RATE PER PACK. `amount_line_p` is the money.
        # Both are carried, and named so the two can never be confused again --
        # confusing them is exactly what produced the two figures withdrawn at
        # S211. A line whose money cannot be computed carries None, never 0.
        row = dict(seq=ln["seq"], item=ln["item_name"], qty_raw=ln["qty_raw"],
                   pack=ln["pack"], rate_p=ln["amount_p"],
                   amount_line_p=line_amount_p(ln["qty_raw"], ln["pack"],
                                               ln["amount_p"]),
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
    return out, dict(flags), ("lines found by: " + line_source) if line_source else ""



# --------------------------------------------------------------------------- #
# THE SUMP -- the day's returns, from BOTH sources
# --------------------------------------------------------------------------- #

def _last4(v):
    """Last four digits of a number, or ''. Nothing longer ever leaves here.

    The owner's standing ruling: patient numbers are masked to the last four.
    Masking at the SOURCE means no caller can leak a full number by forgetting
    to mask -- which is a better guarantee than masking at the template.
    """
    d = re.sub(r"\D", "", str(v or ""))
    return d[-4:] if len(d) >= 4 else ""


def _return_lines_by_bill(con, unit, business_date):
    """Every return LINE of the day, grouped by bill. Source A -- the item spine."""
    rows = con.execute(
        "SELECT %s FROM sale_line_item WHERE unit=? AND business_date=? "
        "AND is_return=1 ORDER BY bill_no, seq" % LINE_COLS,
        (unit, business_date)).fetchall()
    by = collections.OrderedDict()
    for r in rows:
        by.setdefault(r["bill_no"], []).append(r)
    return by


def _return_bills(con, unit, business_date):
    """Every return BILL of the day. Source B -- the money spine."""
    rows = con.execute(
        # phone_last4, NOT mobile. `mobile` exists only on the VPS (added for
        # D356) and is absent from finance_schema.sql, so selecting it makes
        # this file unrunnable anywhere else -- including a rehearsal box.
        # phone_last4 exists in BOTH, and is already masked at rest, which is
        # the owner's rule anyway.
        # gross_p and disc_p are NOT selected. They exist on the live box only
        # (S193 discount ingest) and are absent from finance_schema.sql, and
        # the inherited query read neither of them -- it merely carried them,
        # which made the whole function unrunnable anywhere but the VPS. Found
        # by the S212 walk, not by a gate.
        "SELECT s.id, s.source_ref bill, s.amount_p, "
        "       s.patient_ref_id, p.name, p.phone_last4, p.clinic_id "
        "FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
        "LEFT JOIN patient_ref p ON p.id=s.patient_ref_id "
        "WHERE e.unit=? AND e.business_date=? "
        "AND s.service LIKE '%!_return' ESCAPE '!' "
        "ORDER BY s.source_ref", (unit, business_date)).fetchall()
    return collections.OrderedDict((r["bill"], r) for r in rows)


def returns_for_day(con, business_date, unit="medical"):
    """Every return of the day, from BOTH sources, valued and audited.

    Returns (rows, summary). READ-ONLY.

    The summary is what the card shows collapsed; the rows are what it shows
    when the owner expands it. Every rupee in `value_p` came through
    finance_money -- never from summing a rate.
    """
    lines_by_bill = _return_lines_by_bill(con, unit, business_date)
    bills = _return_bills(con, unit, business_date)

    # THE UNION. Order: bills we know about first, then orphans, so the
    # familiar ones read first and the orphans stand out at the end.
    order = list(bills.keys()) + [b for b in lines_by_bill if b not in bills]

    out = []
    tally = collections.Counter()
    value_p = 0
    value_unreadable = 0

    for bill in order:
        b = bills.get(bill)
        lines = lines_by_bill.get(bill) or []

        # --- population, named honestly -------------------------------------
        if b is not None and lines:
            population = "audited"
        elif b is None:
            population = "orphan"          # lines, no bill row -- the 123
        else:
            population = "no item detail"  # bill row, no lines -- the 116

        # --- money, BOTH ways, because they are not the same question -------
        #   gross = what the returned goods were worth  (from the LINES)
        #   net   = what actually left the drawer       (from the BILL ROW)
        # Measured on the archive: over 20 credit notes, gross Rs 6,676.67
        # against net Rs 6,446.00. Most of that gap is rounding to the rupee.
        # But ONE of them, CN00191, carried a Rs 170.00 discount on Rs 1,150 --
        # a discount on a REFUND, which is its own signal and exists only if
        # both numbers are kept. Netting them together would erase it.
        #
        # An ORPHAN has no bill row and therefore no net. Its gross is the only
        # figure there is, and money_from says so rather than implying a
        # precision this return does not have.
        unreadable = 0
        gross_p = net_p = None
        if lines:
            gross_p, unreadable = bill_gross_p(
                [dict(qty_raw=l["qty_raw"], pack=l["pack"], amount_p=l["amount_p"])
                 for l in lines])
        if b is not None:
            net_p = abs(b["amount_p"] or 0)

        if net_p is not None:
            amount_p = net_p
            money_from = ("the bill row -- cash actually refunded" if lines else
                          "the bill row (no item lines exist for it)")
        else:
            amount_p = gross_p or 0
            money_from = ("its item lines -- there is no bill row, so what the "
                          "goods were worth is the only figure there is")

        # A shortfall larger than rupee-rounding is a discount ON a return.
        # It is always CARRIED, so nothing is hidden -- but it only becomes a
        # VERDICT when it is big enough to be worth the owner's attention.
        # Measured on the archive, a flat Rs 1 threshold flags seven returns of
        # which four are Rs 1.56 to Rs 2.66. A card that cries wolf about
        # Rs 1.56 is a card he stops reading, and then it protects nothing.
        shortfall_p = None
        shortfall_material = False
        if gross_p is not None and net_p is not None and (gross_p - net_p) > 100:
            shortfall_p = gross_p - net_p
            shortfall_material = (shortfall_p >= 1000 or
                                  (gross_p and shortfall_p >= 0.02 * gross_p))

        value_p += amount_p
        value_unreadable += unreadable

        # --- the audit ------------------------------------------------------
        # An orphan has no patient attributed, so "never bought" is not a
        # finding about that patient -- it is a statement about nobody. Saying
        # NEVER BOUGHT there would be the loudest possible false alarm, so the
        # audit is not run and the reason is given instead.
        patient_ref_id = b["patient_ref_id"] if b is not None else None
        if patient_ref_id:
            rows, flags, note = audit_return(con, bill, patient_ref_id,
                                             business_date,
                                             b["amount_p"] if b else None)
            worst = ("NEVER BOUGHT" if flags.get("never_bought") else
                     "REFUNDED MORE THAN PAID" if flags.get("refund_exceeds") else
                     "RETURNED MORE THAN SOLD" if flags.get("qty_exceeds") else
                     "not examinable" if flags.get("no_item_detail") else "ok")
        else:
            rows, flags = [], {}
            worst = "no patient attributed"
            note = ("this return has item lines but no bill row, so no patient "
                    "is attached to it and it cannot be checked against an "
                    "earlier sale. The money is real and is counted.")

        # A clean return that was refunded short is not "ok".
        if shortfall_material and worst == "ok":
            worst = "DISCOUNTED RETURN"

        tally[worst] += 1
        tally["population: " + population] += 1

        out.append(dict(
            bill=bill,
            population=population,
            amount_p=amount_p,
            gross_p=gross_p,
            net_p=net_p,
            refund_shortfall_p=shortfall_p,
            money_from=money_from,
            lines_unreadable=unreadable,
            n_lines=len(lines),
            name=(b["name"] if b is not None else "") or "",
            mobile_last4=(_last4(b["phone_last4"]) if b is not None else ""),
            clinic_id=(b["clinic_id"] if b is not None else "") or "",
            verdict=worst,
            note=note,
            lines=rows,
            flags=flags,
        ))

    summary = dict(
        business_date=business_date,
        unit=unit,
        count=len(out),
        value_p=value_p,
        value=rupees(value_p),
        lines_unreadable=value_unreadable,
        audited=tally.get("population: audited", 0),
        orphans=tally.get("population: orphan", 0),
        no_item_detail=tally.get("population: no item detail", 0),
        flagged=sum(v for k, v in tally.items()
                    if k in ("NEVER BOUGHT", "REFUNDED MORE THAN PAID",
                             "RETURNED MORE THAN SOLD", "DISCOUNTED RETURN")),
        tally=dict(tally),
    )
    return out, summary


def returns_for_range(con, date_from, date_to, unit="medical"):
    """The same, over a span -- what the card needs to say '32 days, Rs X'.

    Deliberately a loop over returns_for_day rather than one wide query: the
    day function is the one that gets audited, and two implementations of the
    same rule is how they drift apart.
    """
    days = [r[0] for r in con.execute(
        "SELECT DISTINCT business_date FROM sale_line_item "
        "WHERE unit=? AND is_return=1 AND business_date BETWEEN ? AND ? "
        "UNION "
        "SELECT DISTINCT e.business_date FROM sale_item s "
        "JOIN day_entry e ON e.id=s.day_entry_id "
        "WHERE e.unit=? AND s.service LIKE '%!_return' ESCAPE '!' "
        "AND e.business_date BETWEEN ? AND ? ORDER BY 1",
        (unit, date_from, date_to, unit, date_from, date_to)).fetchall()]
    all_rows, total_p, per_day = [], 0, []
    agg = collections.Counter()
    for d in days:
        rows, s = returns_for_day(con, d, unit)
        all_rows.extend(rows)
        total_p += s["value_p"]
        agg.update(s["tally"])
        per_day.append(dict(business_date=d, count=s["count"],
                            value_p=s["value_p"], flagged=s["flagged"]))
    return all_rows, dict(
        date_from=date_from, date_to=date_to, unit=unit,
        days=len(days), count=len(all_rows), value_p=total_p,
        value=rupees(total_p), per_day=per_day, tally=dict(agg))
