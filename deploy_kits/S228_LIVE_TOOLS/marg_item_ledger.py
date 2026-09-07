#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MARG "BATCH WISE STOCK" -- THE ITEM LEDGER, READ.

The owner exports one item's whole life from Marg over a window: every bill that
moved it, the batch, the quantity, the value and the running balance. This module
turns that .xls into figures a program can reconcile with -- and it is the reader
`S228_BUILD_BRIEF` item 1 asks for ("just ask for the ledger for this duration and
analyse here").

WHAT THE FILE LOOKS LIKE  (Marg 9+, sheet "BATCH WISE STOCK", a real BIFF .xls)

    col:   0      1                 2       3             4            5       6        7       8
    r0            SANJEEVNI MEDICOS
    r1            35G/15B , RAMPUR BAGH
    r2            BAREILLY
    r3            Mfg.Lic.No. : ... D.L.No. : ...
    r4     (blank)
    r5            STOCK REGISTER WHOLE FROM 27-08-2026 - 06-09-2026
    r6            Bill No./ Date | Type | Patient Name | Doctor Name | Batch Number | Quantity | Value | Balance Quantity
    r7            TYRO BR 1*10                                    <- the item, with its packing
    r8            Opening Balance as on 27-08-2026 TAB |                                    | 2.38125
    r9            27-08-2026                                      <- a DATE GROUP header
    r10           A003217 | Sale | AMARPAL 7840 | 1-DR MANOJ AGARWAL | LGQ0309804 | 0.125 | 548.61 | 2.25625
    ...
    r80           Received : | 4.7138888888888895 | 16977.96
    r81           Issued :   | 4.2131944444444445 | 18463.10

THE ONE THING THAT MATTERS: **EVERY QUANTITY IS AN EXCEL TIME, NOT A NUMBER.**

Marg writes a quantity as strips:loose -- "57:09" is 57 strips and 9 loose tablets
-- and Excel stores that as a fraction of a day. So 2.38125 is not "2.38 strips";
it is 57:09.  minutes = round(value * 1440); strips = minutes // 60; loose =
minutes % 60. A reader that treats the column as a plain number is wrong by a
factor of about 24 and silently so, which is why this module exists.

    0.125            -> 180 min  ->  3 strips              ->  30 tablets on a 1*10
    2.38125          -> 3429 min -> 57 strips 9 tablets     -> 579 tablets on a 1*10
    2.588888888..    -> 3728 min -> 62 strips 8 tablets     -> 938 tablets on a 1*15

The direction of a move is NOT in the quantity column -- it is unsigned. It is taken
from the running balance (balance now minus balance before), and the `Type` word is
kept beside it as the cross-check. When the two disagree the row is flagged rather
than guessed at.

read(path) -> dict. Nothing here touches a database or the network.
"""
import io
import os
import re
import sys

RE_RANGE = re.compile(r"(\d{2}-\d{2}-\d{4})\s*-\s*(\d{2}-\d{2}-\d{4})")
RE_ASON = re.compile(r"as on\s+(\d{2}-\d{2}-\d{4})", re.I)
RE_DATE = re.compile(r"^\d{2}-\d{2}-\d{4}$")
RE_PACK = re.compile(r"^(.*?)\s+(\d+\s*\*\s*\d+)\s*$")

# what the Type word means for the shelf: +1 came in, -1 went out
IN_TYPES = ("PURCHASE", "SALE RETURN", "STOCK RECEIVE", "OPENING", "RECEIPT",
            "STOCK RECEIPT", "PURCHASE ORDER RECEIPT")
OUT_TYPES = ("SALE", "PURCHASE RETURN", "STOCK ISSUE", "BREAKAGE", "EXPIRY",
             "ISSUE", "CONSUMPTION", "WRITE OFF")


def iso(dmy):
    """dd-mm-yyyy -> yyyy-mm-dd; anything else back untouched."""
    s = str(dmy or "").strip()
    return "%s-%s-%s" % (s[6:10], s[3:5], s[0:2]) if RE_DATE.match(s) else s


def dmy(iso_s):
    s = str(iso_s or "").strip()[:10]
    return "%s-%s-%s" % (s[8:10], s[5:7], s[0:4]) if re.match(r"^\d{4}-\d{2}-\d{2}$", s) else s


RE_SL = re.compile(r"^\s*(-?)\s*(\d+)\s*:\s*(\d+)\s*$")


def units(v):
    """AN EXCEL TIME -> MINUTES, where hours are strips and minutes are loose.
    Returns minutes, which IS strips*60 + loose -- never divide it by anything
    but 60."""
    try:
        return int(round(float(v or 0) * 1440.0))
    except (TypeError, ValueError):
        return 0


def qty_units(v, pack):
    """ANY OF THE THREE WAYS MARG WRITES A QUANTITY, in the item's own unit.

    1. an Excel TIME  (2.38125)        -> 57:09 -> 579 tablets on a 1*10
    2. TEXT 's:l'     ('-2:10')        -> -(2 strips 10 tabs) -> -40 on a 1*15
    3. blank                            -> 0

    The second one is the trap: when a balance goes NEGATIVE -- a sale keyed
    before the purchase that covered it -- Marg abandons the time format and
    writes a plain string. A reader that only accepts numbers scores those rows
    as zero and quietly loses them; that is exactly the 40 tablets that stopped
    the MEG QCS ledger from walking when this module was first written. A
    negative balance is also a FINDING in its own right, so it is flagged, not
    merely absorbed."""
    pack = int(pack or 1)
    if isinstance(v, str):
        m = RE_SL.match(v)
        if not m:
            return 0
        n = int(m.group(2)) * pack + int(m.group(3))
        return -n if m.group(1) == "-" else n
    strips, loose = divmod(units(v), 60)
    return strips * pack + loose


def to_units(minutes, pack):
    """strips:loose (as Marg wrote it) -> the item's own smallest unit.

    THE TRAP THIS FUNCTION EXISTS TO CLOSE: the loose part rides in the MINUTES
    slot, which carries at 60, while a strip carries at the pack (10, 15, ...).
    A single figure is safe either way because loose is always under the pack --
    but ADDING TWO FIGURES IN THE TIME DOMAIN IS NOT. 3 strips 8 tabs plus
    3 strips 8 tabs is 7 strips 6 tabs on a 1*10, and 6:16 in minutes, which
    converts back to 6 strips 16 tabs. Every quantity is therefore turned into
    the item's own unit HERE, at the point it is read, and every sum after that
    is a sum of tablets. Nothing downstream ever adds minutes."""
    strips, loose = divmod(int(minutes), 60)
    return strips * int(pack or 1) + loose


def words(qty, pack):
    """The shop's own vocabulary (D384): strips and tabs, pcs on a pack of 1.
    Takes the item's own unit -- tablets, capsules, pieces -- never minutes."""
    neg = qty < 0
    pack = int(pack or 1)
    if pack <= 1:
        n = abs(int(qty))
        s = "%d pc%s" % (n, "" if n == 1 else "s")
    else:
        strips, loose = divmod(abs(int(qty)), pack)
        bits = []
        if strips:
            bits.append("%d strip%s" % (strips, "" if strips == 1 else "s"))
        if loose:
            bits.append("%d tab%s" % (loose, "" if loose == 1 else "s"))
        s = " ".join(bits) or "0 strips"
    return ("-" if neg else "") + s


def paise(v):
    try:
        return int(round(float(v or 0) * 100))
    except (TypeError, ValueError):
        return 0


def _sheet(path):
    import xlrd                                              # noqa: PLC0415
    return xlrd.open_workbook(path).sheet_by_index(0)


def _txt(sh, r, c):
    if c >= sh.ncols:
        return ""
    v = sh.cell_value(r, c)
    return str(v).strip() if v is not None else ""


def _footer(sh, r, look=9):
    """The 'Received :' / 'Issued :' pair Marg puts at the foot. They are not in
    the Bill No. column -- they sit under Batch Number, with the quantity and the
    value in the two columns after. Found by the marker, never by a fixed column."""
    for c in range(min(sh.ncols, look)):
        t = _txt(sh, r, c).upper().replace(" ", "")
        if t.startswith("RECEIVED:") or t.startswith("ISSUED:"):
            return (("RECEIVED" if t.startswith("RECEIVED") else "ISSUED"),
                    units(sh.cell_value(r, c + 1)) if c + 1 < sh.ncols else 0,
                    paise(sh.cell_value(r, c + 2)) if c + 2 < sh.ncols else 0)
    return None


def _first_col(sh, look=12):
    """The report is indented: column 0 is empty and everything sits one column
    right. Find the first column that carries anything, rather than assuming 0 --
    this is the exact assumption that made the archive router refuse the file."""
    for c in range(min(sh.ncols, 6)):
        for r in range(min(sh.nrows, look)):
            if _txt(sh, r, c):
                return c
    return 0


def read(path):
    """Read one exported item ledger. Returns a dict; raises ValueError if the
    file is not this report."""
    sh = _sheet(path)
    c0 = _first_col(sh)
    head = None
    for r in range(min(sh.nrows, 30)):
        if _txt(sh, r, c0).lower().startswith("bill no"):
            head = r
            break
    if head is None:
        raise ValueError("not a Marg BATCH WISE STOCK export: no 'Bill No./ Date' header row")

    store, period = "", ""
    for r in range(head):
        t = _txt(sh, r, c0)
        if t and not store:
            store = t
        if "STOCK REGISTER" in t.upper():
            period = t
    m = RE_RANGE.search(period)
    p_from, p_to = (iso(m.group(1)), iso(m.group(2))) if m else (None, None)

    # the item line sits between the header and the opening balance
    item_raw, opening_min, opening_on, unit_word = "", 0, None, ""
    body_from = head + 1
    for r in range(head + 1, min(head + 6, sh.nrows)):
        t = _txt(sh, r, c0)
        if not t:
            continue
        if t.upper().startswith("OPENING BALANCE"):
            opening_min = units(sh.cell_value(r, c0 + 7))
            mo = RE_ASON.search(t)
            opening_on = iso(mo.group(1)) if mo else p_from
            mw = re.search(r"\d{2}-\d{2}-\d{4}\s+(.+)$", t)
            unit_word = (mw.group(1).strip().rstrip(".") if mw else "")
            body_from = r + 1
        elif not item_raw:
            item_raw = t
            body_from = r + 1
    if not item_raw:
        raise ValueError("not a Marg BATCH WISE STOCK export: no item line under the header")

    mp = RE_PACK.match(item_raw)
    name = (mp.group(1) if mp else item_raw).strip()
    packing = (mp.group(2).replace(" ", "") if mp else "")
    try:
        pack = int(packing.split("*")[1]) if packing else 1
    except (IndexError, ValueError):
        pack = 1

    rows, day, notes = [], None, []
    recv_min = issue_min = None
    recv_p = issue_p = 0
    opening_units = to_units(opening_min, pack)
    balance = opening_units          # the running balance is in TABLETS from the start
    for r in range(body_from, sh.nrows):
        foot = _footer(sh, r)          # "Received :" / "Issued :" sit under the Batch
        if foot:                       # column, with the Bill No. cell EMPTY -- so they
            k, q, v = foot             # must be looked for before an empty first cell
            if k == "RECEIVED":        # sends the row away
                recv_min, recv_p = q, v
            else:
                issue_min, issue_p = q, v
            continue
        a = _txt(sh, r, c0)
        if not a:
            continue
        if RE_DATE.match(a):
            day = iso(a)                                     # a DATE GROUP header
            continue
        bal = qty_units(sh.cell_value(r, c0 + 7), pack)
        qty = qty_units(sh.cell_value(r, c0 + 5), pack)
        if not qty and not bal:
            notes.append(dict(row=r + 1, text=a))
            continue
        moved = bal - balance                # what the running balance says
        kind = _txt(sh, r, c0 + 1).upper()
        want = 1 if any(k == kind or kind.startswith(k) for k in IN_TYPES) else (
            -1 if any(k == kind or kind.startswith(k) for k in OUT_TYPES) else 0)
        # THE TYPE WORD RULES, the balance is the cross-check. Marg's own
        # Received/Issued totals are sums of the QUANTITY column, so a reader that
        # scored movements off balance deltas could never tie out against them.
        signed = (want * qty) if want else moved
        rows.append(dict(
            row=r + 1, day=day, day_text=dmy(day), bill_no=a, type=_txt(sh, r, c0 + 1),
            party=_txt(sh, r, c0 + 2), doctor=_txt(sh, r, c0 + 3), batch=_txt(sh, r, c0 + 4),
            qty_units=qty, qty_text=words(qty, pack),
            moved_units=signed, balance_says=moved, negative=(bal < 0),
            moved_text=words(signed, pack) + (" IN" if signed > 0 else (" OUT" if signed < 0 else "")),
            value_p=paise(sh.cell_value(r, c0 + 6)),
            balance_units=bal, balance_text=words(bal, pack),
            direction_agrees=(want == 0 or (signed > 0) == (want > 0) or signed == 0),
            balance_agrees=(moved == signed)))
        balance = bal

    closing_units = rows[-1]["balance_units"] if rows else opening_units
    in_units = sum(r["moved_units"] for r in rows if r["moved_units"] > 0)
    out_units = -sum(r["moved_units"] for r in rows if r["moved_units"] < 0)
    recv_units = None if recv_min is None else to_units(recv_min, pack)
    issue_units = None if issue_min is None else to_units(issue_min, pack)
    d = dict(
        file=os.path.basename(path), store=store, period_text=period,
        period_from=p_from, period_to=p_to,
        item=item_raw, name=name, packing=packing, pack=pack, unit_word=unit_word,
        opening_on=opening_on, opening_units=opening_units, opening_text=words(opening_units, pack),
        closing_units=closing_units, closing_text=words(closing_units, pack),
        in_units=in_units, in_text=words(in_units, pack),
        out_units=out_units, out_text=words(out_units, pack),
        received_units=recv_units, issued_units=issue_units, received_p=recv_p, issued_p=issue_p,
        rows=rows, lines=len(rows), notes=notes,
        went_negative=[dict(row=r["row"], day=r["day_text"], bill_no=r["bill_no"], batch=r["batch"],
                            balance_text=r["balance_text"]) for r in rows if r["negative"]],
        balance_disagrees=[dict(row=r["row"], bill_no=r["bill_no"], type=r["type"],
                                qty_text=r["qty_text"], balance_says=words(r["balance_says"], pack))
                           for r in rows if not r["balance_agrees"]])
    # THE FILE MUST AGREE WITH ITSELF, and say so plainly when it does not
    d["walks"] = (opening_units + in_units - out_units == closing_units)
    d["totals_agree"] = ((recv_units is None or recv_units == in_units)
                         and (issue_units is None or issue_units == out_units))
    d["directions_agree"] = all(r["direction_agrees"] for r in rows)
    d["negatives"] = len(d["went_negative"])
    d["ok"] = d["walks"] and d["totals_agree"]
    return d


def between(d, day_from, day_to):
    """The rows inside a window (iso dates, inclusive) and what they net to --
    the question a residue always asks: what moved between these two exports?"""
    rs = [r for r in d["rows"] if r["day"] and day_from <= r["day"] <= day_to]
    net = sum(r["moved_units"] for r in rs)
    return dict(rows=rs, lines=len(rs), net_units=net,
                net_text=words(net, d["pack"]) + (" IN" if net > 0 else (" OUT" if net < 0 else "")),
                by_type=_by_type(rs, d["pack"]))


def _by_type(rs, pack):
    out = {}
    for r in rs:
        k = r["type"] or "(no type)"
        e = out.setdefault(k, dict(type=k, lines=0, units=0, value_p=0))
        e["lines"] += 1
        e["units"] += r["moved_units"]
        e["value_p"] += r["value_p"]
    for e in out.values():
        e["text"] = words(e["units"], pack) + (" IN" if e["units"] > 0 else (" OUT" if e["units"] < 0 else ""))
    return sorted(out.values(), key=lambda e: (-abs(e["units"]), e["type"]))


def rupees(p_):
    n = abs(int(p_ or 0)); whole, pa = divmod(n, 100); s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]; parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return ("-" if int(p_ or 0) < 0 else "") + "Rs %s.%02d" % (s, pa)


def summary(d):
    """One screen a person can read, in the shop's own words."""
    L = []
    L.append("%s   %s" % (d["name"], d["packing"] or ""))
    L.append("  %s to %s   -   %d movements on record"
             % (dmy(d["period_from"]), dmy(d["period_to"]), d["lines"]))
    L.append("  opened  %s  on %s" % (d["opening_text"], dmy(d["opening_on"])))
    L.append("  in      %s        %s" % (d["in_text"], rupees(d["received_p"])))
    L.append("  out     %s        %s" % (d["out_text"], rupees(d["issued_p"])))
    L.append("  closed  %s" % d["closing_text"])
    L.append("  the ledger %s" % ("walks: opening + in - out = closing, and Marg's own"
                                  " Received/Issued totals agree to the tablet" if d["ok"] else
                                  "DOES NOT WALK -- walks=%s totals_agree=%s (in %d / Marg %s, out %d / Marg %s)"
                                  % (d["walks"], d["totals_agree"], d["in_units"], d["received_units"],
                                     d["out_units"], d["issued_units"])))
    for e in _by_type(d["rows"], d["pack"]):
        L.append("      %-16s %3d line(s)  %-22s %s" % (e["type"], e["lines"], e["text"], rupees(e["value_p"])))
    if d["went_negative"]:
        L.append("  FINDING: the stock went BELOW ZERO on %d line(s) -- a sale keyed before the"
                 " purchase that covered it:" % len(d["went_negative"]))
        for n in d["went_negative"][:6]:
            L.append("      %s  bill %s  batch %s  ->  %s" % (n["day"], n["bill_no"], n["batch"], n["balance_text"]))
    return "\n".join(L)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        d = read(p)
        sys.stdout.write(summary(d) + "\n\n")
