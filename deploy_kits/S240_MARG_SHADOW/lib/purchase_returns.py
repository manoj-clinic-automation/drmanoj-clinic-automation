#!/usr/bin/python3
"""
purchase_returns.py — find the purchase RETURNS that the item-wise report hides.

THE FAULT THIS EXISTS FOR, AND IT WAS MINE
    I reported that Marg "prints item lines its own totals exclude", ₹13,839 over
    five months, and recorded July's share as unexplained. That was wrong.

    **They are purchase returns.** Marg prints a return in the ITEM-WISE report
    as an ordinary POSITIVE line — same shape, same cell types, no marker of any
    kind — while its own supplier TOTAL counts it NEGATIVE. Proven against the
    summary reports, which do sign them:

        supplier-wise, L.K. DRUG HOUSE, July:
            45067  credit  4126        4159   credit  -135
            45328  credit  1033        5      credit  -367

    So for a group holding returns worth R:

        sum(item lines) - TOTAL row  =  2 x R

    because the return is added where it should have been subtracted. Applying
    that correction closes **all five months to exactly 0.00**.

WHY THE ITEM-WISE REPORT CANNOT BE READ ALONE
    There is no signal in it. The return rows are numerically and structurally
    identical to purchases — positive quantity, positive rate, positive amount,
    same cell types. **Any total taken from the item-wise export alone
    over-states purchases by twice the value of any returns in the period.**

    Two ways to recover them, in order of trust:
      1 · CROSS-REFERENCE a bill-wise or supplier-wise export. Authoritative:
          those reports carry the minus sign. Use this whenever available.
      2 · INFER from the variance: the returns are the subset of the group whose
          amounts sum to exactly half the excess. Where two lines share an
          amount (the same item returned as bought), the subset is ambiguous —
          the LOW bill number is the return, because returns run on the vendor's
          separate credit-note series (5 and 4159 against a series of 45067,
          52393, 55027, 59178 — confirmed negative by the summary report).
"""

import itertools


def returns_from_variance(rows, excess, max_lines=4):
    """
    rows   : the item dicts of ONE supplier group
    excess : sum(amounts) - the group's TOTAL row
    Returns (return_rows, exact) — exact is False when nothing sums to half.
    """
    if not excess or excess <= 0.01:
        return ([], True)
    half = round(excess / 2.0, 2)
    amts = [(r.get("amount") or 0) for r in rows]
    for k in range(1, max_lines + 1):
        for combo in itertools.combinations(range(len(rows)), k):
            if abs(sum(amts[i] for i in combo) - half) < 0.02:
                chosen = _prefer_low_bill(rows, combo, amts)
                return ([rows[i] for i in chosen], True)
    return ([], False)


def _prefer_low_bill(rows, combo, amts):
    """
    Where another line in the group carries the SAME amount, the return is the
    one with the lower bill number — returns use the vendor's credit-note
    series, which starts low. Confirmed on July against the summary report.
    """
    out = []
    for i in combo:
        twins = [j for j, a in enumerate(amts)
                 if j != i and abs(a - amts[i]) < 0.005
                 and rows[j].get("item") == rows[i].get("item")]
        best = i
        for j in twins + [i]:
            try:
                bj = int(str(rows[j].get("bill") or "9" * 12))
                bb = int(str(rows[best].get("bill") or "9" * 12))
            except ValueError:
                continue
            if bj < bb:
                best = j
        out.append(best)
    return out


def apply(report):
    """
    Mark returns on a parsed purchase report and correct its totals.
    Adds  r['is_return']  to every row, and to the report:
        returns          list of the return rows
        returns_value    their total (positive number)
        items_sum_net    items summed with returns SUBTRACTED
        closes           True when items_sum_net equals GRAND TOTAL
    """
    for r in report["rows"]:
        r["is_return"] = False
    found, exact_all = [], True
    for v in report.get("variances", []):
        grp = [r for r in report["rows"]
               if r["supplier"] == v["supplier"] and r["row"] < v["row"]]
        grp.sort(key=lambda r: r["row"])
        rets, exact = returns_from_variance(grp, v["excess"])
        exact_all &= exact
        for r in rets:
            r["is_return"] = True
        found += rets
    val = sum((r.get("amount") or 0) for r in found)
    net = round(report["items_sum"] - 2 * val, 2)
    report["returns"] = found
    report["returns_value"] = round(val, 2)
    report["returns_exact"] = exact_all
    report["items_sum_net"] = net
    g = report.get("grand_amount")
    report["closes"] = g is not None and abs(net - g) < 0.05
    return report
