#!/usr/bin/env python3
"""
finance_money.py -- S212: the one place that turns a Marg item line into money.

WHY THIS FILE EXISTS
    `amount_p` on a line is the RATE PER PACK, not the line amount. That was
    proven at S211 against 374 real bills (373 reproduce their printed gross
    exactly, 99.7%). Two figures were withdrawn at S211 -- Rs 1,33,514 and
    Rs 38,157 -- and BOTH came from summing amount_p as though it were money.

    So the model lives in exactly one function, and everything that needs money
    calls it. A second implementation is how the third wrong figure gets made.

THE MODEL (S211, proven -- do not re-derive)

    strip pack  'N*M'   line amount = (strips + loose / M) x rate
    non-strip   '5GM', '2ML', '1*1'
                        line amount = qty x rate

    bill GROSS = sum of its line amounts
    A credit note prints GROSS negative. In the DATABASE the magnitude is
    stored positive and the direction is carried separately -- sale_line_item
    declares CHECK (amount_p >= 0), so a return can NEVER be negative here.
    Direction comes from is_return, never from the sign. (D314)
"""
import re

RE_PACK_STRIP = re.compile(r"^\s*(\d+)\s*\*\s*(\d+)\s*$")
RE_QTY_PAIR = re.compile(r"^\s*(\d+)\s*:\s*(\d+)\s*$")


def pack_size(pack):
    """'1*10' -> 10.  '1*1' -> 1.  '5GM'/'2ML'/None -> None (not a strip pack).

    Returns None rather than guessing 1, so the caller must decide what a
    non-strip pack means instead of silently getting a wrong divisor.

    A TRAILING DOT IS TOLERATED -- '1*10.' -> 10. Two items in the Marg master
    carry one (FEBUWISE 40 and PRETOL 8); it is a typing artifact in the pack
    string and carries no information. Found at S212 by re-measuring the S211
    model: refusing it silently dropped 6 lines and broke 6 of 374 bills.
    Only a trailing dot is stripped, so '1*10.5' is still refused rather than
    quietly read as a 10-pack.
    """
    p = re.sub(r"\.$", "", str(pack or "").strip())
    m = RE_PACK_STRIP.match(p)
    if not m:
        return None
    n = int(m.group(2))
    return n if n > 0 else None


def units(qty_raw, pack):
    """How many PACKS this line is, as a float. None when it cannot be read.

    'strips:loose' against a strip pack -> strips + loose/pack_size
    a plain number (non-strip pack, or a strip pack Marg printed plainly)
                                        -> the number itself

    Deliberately returns None on any other shape: a quantity that was misread
    produces money that is wrong without looking wrong.
    """
    q = str(qty_raw or "").strip()
    if not q:
        return None
    size = pack_size(pack)
    m = RE_QTY_PAIR.match(q)
    if m:
        strips, loose = int(m.group(1)), int(m.group(2))
        if size is None:
            # 'a:b' on a non-strip pack -- Marg should not print this. Say so
            # by refusing rather than by inventing a divisor.
            return None
        if size == 1:
            return float(strips + loose)
        return strips + (loose / float(size))
    try:
        return float(q)
    except (TypeError, ValueError):
        return None


def base_units(qty_raw, pack):
    """The same quantity counted in SINGLE UNITS (tablets), not packs.

    Money needs packs; a quantity COMPARISON needs base units -- '0:5' and
    '1:0' are only comparable once both are tablets. Two callers, two views,
    but ONE parser underneath, which is the whole point of this file.

    `finance_item_anomaly.py` carries its own copy of this rule today. The two
    were measured against every (pack, qty) pair that occurs in the owner's
    archive -- 97 distinct pairs over 1,649 lines -- and agree on all of them
    (`EQUIV_pack.py`). Pointing that file here is therefore a proven no-op, to
    be done when the anomaly card is built rather than as a change to a live
    file that is currently producing results.
    """
    u = units(qty_raw, pack)
    if u is None:
        return None
    size = pack_size(pack)
    return u * size if size else u


def line_amount_p(qty_raw, pack, amount_p):
    """The line's money in paise, rounded to the paisa. None when unreadable.

    `amount_p` is the RATE PER PACK. This is the only place that fact is
    turned into money.
    """
    if amount_p is None:
        return None
    u = units(qty_raw, pack)
    if u is None:
        return None
    return int(round(u * float(amount_p)))


def bill_gross_p(lines):
    """Sum a bill's lines. Returns (gross_p, n_unreadable).

    A line that cannot be valued is COUNTED, never silently treated as zero --
    a total that quietly omits a line is the failure this whole file exists to
    prevent.
    """
    total, bad = 0, 0
    for ln in lines:
        a = line_amount_p(ln.get("qty_raw"), ln.get("pack"), ln.get("amount_p"))
        if a is None:
            bad += 1
        else:
            total += a
    return total, bad


def rupees(p):
    """Paise -> 'Rs 1,23,456.78' in Indian digit grouping, for display only."""
    if p is None:
        return "--"
    neg = p < 0
    p = abs(int(p))
    whole, frac = divmod(p, 100)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = head + "," + tail
    return "%sRs %s.%02d" % ("-" if neg else "", s, frac)
