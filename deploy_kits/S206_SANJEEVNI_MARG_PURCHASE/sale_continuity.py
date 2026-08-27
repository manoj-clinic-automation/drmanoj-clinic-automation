#!/usr/bin/python3
"""
sale_continuity.py — completeness by BILL NUMBER, not by counting days.

WHY THIS REPLACES THE DAY COUNT
    Counting archived days answers the wrong question. It cannot tell a day
    with no sale from a day whose report was never taken, and it called
    Sunday 23-Aug-2026 a gap when the shop was shut.

    Marg issues sale bills in one unbroken sequence. So the sequence itself is
    the completeness test:

        · every bill inside an archived day must be present  -> no silent loss
        · the last bill of one day + 1 == the first of the next
          -> nothing between them was missed, INCLUDING across a closed day
        · the next report must begin at last_bill + 1
          -> a forward-looking check, before the file is even taken

    Proven on the real archive: 22-Aug ends A003159, 24-Aug begins A003160.
    **Contiguous across Sunday.** The shop was closed; nothing is missing. A
    day count says "23-Aug is absent" and is wrong. The sequence says
    "nothing was issued" and is right.

WHAT A GAP MEANS — and what it does NOT mean
    A gap says those bills are not in THIS archive. It does not say they are
    lost: they may have been ingested by another route (a 15-day or monthly
    report loaded straight to the clinic server). This module reports the gap
    and its exact size so the claim "those are already on the server" becomes
    a number that can be checked, instead of a memory.
"""

import re
import collections

BILL_RE = re.compile(r"^([A-Z]+)0*(\d+)$")


def parse_bill(b):
    """'A003195' -> ('A', 3195). Returns None if it is not a bill number."""
    m = BILL_RE.match((b or "").strip().upper())
    return (m.group(1), int(m.group(2))) if m else None


def chains(sale_rows):
    """
    sale_rows: dicts with 'date' and 'bill'.
    Returns {prefix: {'days': [...], 'gaps': [...], 'next_expected': 'A003216'}}
    """
    by = collections.defaultdict(lambda: collections.defaultdict(set))
    width = collections.defaultdict(int)
    for r in sale_rows:
        p = parse_bill(r.get("bill"))
        if not p:
            continue
        pref, num = p
        by[pref][r["date"]].add(num)
        width[pref] = max(width[pref], len((r["bill"] or "").strip()) - len(pref))

    out = {}
    for pref, days in by.items():
        w = width[pref]
        rows, gaps, prev = [], [], None
        for d in sorted(days):
            nums = days[d]
            lo, hi = min(nums), max(nums)
            span = hi - lo + 1
            rows.append({"date": d, "first": lo, "last": hi,
                         "count": len(nums), "span": span,
                         "missing_in_day": span - len(nums)})
            if prev is not None and lo > prev + 1:
                gaps.append({"after": prev, "before": lo, "missing": lo - prev - 1})
            prev = max(prev, hi) if prev is not None else hi
        out[pref] = {"days": rows, "gaps": gaps, "last": prev,
                     "next_expected": "%s%0*d" % (pref, w, prev + 1) if prev is not None else None}
    return out


def report(ch, out=None):
    import sys
    w = (out or sys.stdout).write
    for pref in sorted(ch):
        c = ch[pref]
        w("\nprefix %s — %d day(s) archived\n" % (pref, len(c["days"])))
        for r in c["days"]:
            flag = "" if not r["missing_in_day"] else \
                "  ** %d MISSING INSIDE THE DAY **" % r["missing_in_day"]
            w("  %s  %d..%d  count=%d%s\n"
              % (r["date"], r["first"], r["last"], r["count"], flag))
        for g in c["gaps"]:
            w("  GAP: %d bill(s) between %d and %d — not in this archive\n"
              % (g["missing"], g["after"], g["before"]))
        w("  NEXT REPORT MUST BEGIN AT: %s\n" % c["next_expected"])
    return ch
