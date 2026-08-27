#!/usr/bin/python3
"""
item_ledger.py — one ledger per item, 01-Apr-2026 onward, and nothing stranded.

THE IDENTITY EVERY ITEM MUST SATISFY

    opening(31-Mar)  +  purchased  -  returned to vendor  -  sold  =  closing(26-Aug)

Everything on the right of the opening is measured:
  · opening   STOCK_CLOSING as on 31-03-2026        (975 rows)
  · purchased PURCHASE_ITEMWISE, loose_qty          (5 contiguous months)
  · returned  the rows purchase_returns.py identifies
  · sold      SALE_BILLWISE item lines, deduplicated (17,177 lines, A00001-A03215)
  · closing   STOCK_CLOSING as on 26-08-2026        (375 rows)

WHERE IT DOES NOT BALANCE, THE GAP IS THE FINDING — in units, per item.

NOTHING IS DROPPED. A name that appears in one source and not another is
reported as UNMATCHED rather than silently discarded: an item quietly missing
from the join is exactly what "stranded" means, and a reconciliation that hides
its own misses is worse than none.
"""

import re
import collections


def norm(s):
    """Match key. Case, spacing and trailing punctuation only — never content."""
    s = re.sub(r"\s+", " ", (s or "").upper()).strip()
    return re.sub(r"[.\s]+$", "", s)


def build(opening, purchased, returned, sold, closing):
    """Each argument: {item_name: units}. Returns (rows, unmatched)."""
    srcs = {"opening": opening, "purchased": purchased,
            "returned": returned, "sold": sold, "closing": closing}
    keyed = {}
    display = {}
    for tag, d in srcs.items():
        k = collections.defaultdict(float)
        for name, v in d.items():
            n = norm(name)
            if not n:
                continue
            k[n] += (v or 0)
            display.setdefault(n, name)
        keyed[tag] = k

    every = set()
    for k in keyed.values():
        every |= set(k)

    rows = []
    for n in sorted(every):
        o = keyed["opening"].get(n, 0.0)
        p = keyed["purchased"].get(n, 0.0)
        r = keyed["returned"].get(n, 0.0)
        s = keyed["sold"].get(n, 0.0)
        c = keyed["closing"].get(n, 0.0)
        expect = o + p - r - s
        rows.append({
            "key": n, "item": display.get(n, n),
            "opening": o, "purchased": p, "returned": r, "sold": s,
            "expected": expect, "closing": c, "variance": round(c - expect, 3),
            "in": tuple(t for t in ("opening", "purchased", "returned", "sold", "closing")
                        if n in keyed[t]),
        })

    unmatched = {
        "sold_not_in_master": sorted(n for n in keyed["sold"]
                                     if n not in keyed["opening"] and n not in keyed["closing"]),
        "purchased_not_in_master": sorted(n for n in keyed["purchased"]
                                          if n not in keyed["opening"] and n not in keyed["closing"]),
        "closing_only": sorted(n for n in keyed["closing"]
                               if n not in keyed["opening"] and n not in keyed["purchased"]
                               and n not in keyed["sold"]),
    }
    return rows, unmatched


def summarise(rows, tol=0.5):
    bal = [r for r in rows if abs(r["variance"]) <= tol]
    off = [r for r in rows if abs(r["variance"]) > tol]
    return {
        "items": len(rows),
        "balanced": len(bal),
        "off": len(off),
        "surplus": sum(r["variance"] for r in off if r["variance"] > 0),
        "shortfall": sum(r["variance"] for r in off if r["variance"] < 0),
        "net": round(sum(r["variance"] for r in rows), 2),
    }
