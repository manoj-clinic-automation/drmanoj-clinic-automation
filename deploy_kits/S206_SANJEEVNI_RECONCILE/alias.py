#!/usr/bin/python3
"""
alias.py -- find the item codes that are the SAME PHYSICAL PRODUCT.

    DISPO SYRINGE NIPRO     +574 on the shelf that was never bought
    DISPO SYRINGE NIPRO 3ML -574 bought and never sold

    One product, two codes in Marg's item master. Sales were rung up on one,
    purchases entered on the other. Neither line balances; together they are
    exact.

WHAT COUNTS AS PROOF -- and it is deliberately strict, because merging two
genuinely different products is a worse error than leaving a pair unmerged:

  1 ARITHMETIC   merging must genuinely IMPROVE the reconciliation: the
                 leftover after netting the two must be smaller than either
                 variance was on its own, |a+b| < min(|a|,|b|). Requiring an
                 exact cancellation instead was too strict and missed
                 'PARI 25' / 'PARI CR 25'; requiring nothing at all would let
                 any two names with opposite signs pair up. Whatever is left
                 after the merge is NOT absorbed -- it is classified on its
                 own, so a rename never becomes a place to hide 10 units.
  2 NAME         one name is contained in the other after removing spaces
                 and punctuation, or they are one transposed space apart
                 ('THIO Q AP' / 'THI OQ AP'), or they are the same multiset
                 of words.
  3 DISJOINT     they do not both trade. One side has the purchases and no
                 sales, or the sales and no purchases -- which is what a
                 split code looks like. A pair that both buys AND sells on
                 both codes is two products, not one.

A pair failing any test is REPORTED AS A CANDIDATE, never merged. The owner
ratifies; the machine does not get to rename his stock.
"""
import re, itertools


def squash(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def words(s):
    return tuple(sorted(re.findall(r"[A-Z0-9.]+", (s or "").upper())))


def name_related(a, b):
    sa, sb = squash(a), squash(b)
    if not sa or not sb:
        return None
    if sa == sb:
        return "identical once punctuation is removed"
    if sa in sb or sb in sa:
        return "one name contains the other"
    if words(a) == words(b):
        return "same words, different order"
    if len(sa) == len(sb) and sum(x != y for x, y in zip(sa, sb)) <= 1:
        return "one character apart"
    # A TOKEN WAS INSERTED. 'PARI 25' -> 'PARI CR 25' is the same product with
    # a strength/form word added when the code was reopened. Requiring the
    # short name to be a substring misses it, because 'CR' lands in the middle.
    # Order is preserved, so a subsequence test is exact and does not match
    # unrelated names.
    wa, wb = re.findall(r"[A-Z0-9.]+", (a or "").upper()), re.findall(r"[A-Z0-9.]+", (b or "").upper())
    short, long_ = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    if len(short) >= 2 and len(long_) - len(short) <= 2 and _subseq(short, long_):
        return "same name with '%s' added" % " ".join(w for w in long_ if w not in short)
    # a space in the wrong place: THIO Q AP / THI OQ AP squash identically,
    # so this is only reached for genuinely different letters.
    return None


def _subseq(short, long_):
    it = iter(long_)
    return all(any(w == x for x in it) for w in short)


def disjoint(a, b, tol=0.5):
    """One side carries the purchases, the other the sales."""
    ap, as_ = a["purchased"], a["sold"]
    bp, bs = b["purchased"], b["sold"]
    return (ap <= tol and bs <= tol) or (bp <= tol and as_ <= tol) or \
           (ap <= tol and bp > tol) or (bp <= tol and ap > tol)


def find(rows, tol=1.0):
    """Returns (confirmed, candidates). Nothing is merged here."""
    off = [r for r in rows if abs(r["var"]) > 0.5]
    pos = [r for r in off if r["var"] > 0]
    neg = [r for r in off if r["var"] < 0]
    used, conf, cand = set(), [], []
    for a in sorted(pos, key=lambda r: -abs(r["var"])):
        if a["key"] in used:
            continue
        best = None
        for b in sorted(neg, key=lambda r: -abs(r["var"])):
            if b["key"] in used:
                continue
            rel = name_related(a["item"], b["item"])
            if not rel:
                continue
            gap = abs(a["var"] + b["var"])
            score = (0 if gap <= tol else 1, gap, -min(abs(a["var"]), abs(b["var"])))
            if gap >= min(abs(a["var"]), abs(b["var"])) and gap > tol:
                continue
            if best is None or score < best[0]:
                best = (score, b, rel, gap)
        if not best:
            continue
        _, b, rel, gap = best
        tests = {"arithmetic": gap <= tol or gap < min(abs(a["var"]), abs(b["var"])),
                 "name": True, "disjoint": disjoint(a, b)}
        rec = {"a": a["item"], "b": b["item"], "a_var": a["var"], "b_var": b["var"],
               "residual": round(a["var"] + b["var"], 2), "why": rel, "tests": tests,
               "a_key": a["key"], "b_key": b["key"]}
        if all(tests.values()):
            conf.append(rec); used.add(a["key"]); used.add(b["key"])
        else:
            cand.append(rec)
    return conf, cand
