#!/usr/bin/python3
"""
classify.py -- give every unbalanced item a NAMED cause, or say it has none.

The point of a reconciliation is not a percentage. It is that each line either
balances, or carries a reason a person can act on. A bucket called 'other' is
where discrepancies go to be forgotten, so there isn't one: an item with no
identifiable cause is labelled UNEXPLAINED and stays visible.

THE CLASSES, in the order they are tested (first match wins)

  RENAMED       a +/- pair whose names are related and whose variances cancel.
                One code was retired and a new one opened; sales landed on one
                side and purchases on the other. Nothing is missing.
                    PARI 12.5 -> PARI CR 12.5      THI OQ AP / THIO Q AP
  ZEROED        had stock on 31-Mar, no sale, no purchase, and today reads
                exactly zero WHILE STILL ON THE LIST. Nothing physical moved
                and no document records anything: the quantity was edited
                down by hand. This is the owner's own expiry-removal routine
                -- open the item, alter quantity and expiry -- and it is
                invisible to every report Marg can export, which is why the
                ledger sees it only as an absence.
  OFF_LIST      had stock on 31-Mar and is absent from today's item master
                ENTIRELY. The stock did not move -- the ITEM did. A stock-
                taker working from today's list can never count these,
                because they are not on it.
  NEG_CLEARED   opening was negative (goods received before the bill). The
                variance is the correction arriving.
  GOODS_IN      more on the shelf than the paperwork explains. Physically:
                goods received against a bill not yet entered.
  GOODS_OUT     less on the shelf than the paperwork explains. Physically:
                breakage, expiry write-off, sample, or an unbilled issue.
  UNEXPLAINED   none of the above fits.
"""
import alias


def classify(rows, tol=0.5):
    off = [r for r in rows if abs(r["var"]) > tol]
    by = {r["key"]: r for r in rows}
    conf, cand = alias.find(rows)
    paired = {}
    for c in conf:
        paired[c["a_key"]] = c
        paired[c["b_key"]] = c

    out = []
    for r in off:
        k = r["key"]
        moved = r["purchased"] or r["sold"] or r["sreturn"] or r["preturn"]
        if k in paired:
            c = paired[k]
            other = c["b"] if c["a_key"] == k else c["a"]
            left = c["residual"]
            cls = "RENAMED"
            why = "same product as '%s' (%s)%s" % (
                other, c["why"],
                "; together they are exact" if abs(left) <= tol
                else "; %+g units still unexplained after netting the two" % left)
        elif not moved and r["opening"] and not r["closing"] and not r.get("on_list", r["in_master"]):
            cls, why = "OFF_LIST", ("held %s on 31-Mar, never moved, and is not on "
                                    "today's item list at all" % _q(r["opening"], r))
        elif not moved and r["opening"] and not r["closing"]:
            cls, why = "ZEROED", ("held %s on 31-Mar, no sale and no purchase, and now "
                                  "reads zero while still on the list -- edited by hand"
                                  % _q(r["opening"], r))
        elif r["opening"] < 0 and 0 < r["var"] <= abs(r["opening"]) + tol:
            # ONLY up to the size of the negative. A -42 opening cannot account
            # for a +280 variance, and letting it try would bury 238 units in a
            # class that sounds resolved.
            cls, why = "NEG_CLEARED", ("opened %s short -- goods had arrived before the "
                                       "bill; this is the correction" % _q(-r["opening"], r))
        elif r["var"] > 0:
            cls = "GOODS_IN"
            why = "on the shelf but not on any purchase bill in the window"
            if r["opening"] < 0:
                why += " (opened %s short, which explains only part of it)" % _q(-r["opening"], r)
        elif r["var"] < 0:
            cls, why = "GOODS_OUT", "gone from the shelf but not on any sale bill or return"
        else:
            cls, why = "UNEXPLAINED", "no class fits"
        d = dict(r)
        d["class"], d["why"] = cls, why
        out.append(d)
    return out, conf, cand


def _q(u, r):
    import packmap as PM
    return PM.describe(u, r.get("size"))
