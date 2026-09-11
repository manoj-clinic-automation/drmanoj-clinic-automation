#!/usr/bin/python3
"""
marg_purchase.py — read a Marg ERP 9+ "SUPPLIER/ITEM WISE PURCHASE STATEMENT"
.XLS export into normalised rows, and REFUSE anything it cannot account for.

WHY THIS EXISTS
    marg_report.py already reads the SALE side (BILL WISE SALES STATEMENT).
    Nothing reads the PURCHASE side. Q1 needs both in one normalised table:
        item · batch · expiry · qty · rate · date · direction

WHAT THIS IS NOT
    It does not recompute stock. Marg is the system of record for stock (Q1's
    own rule). This reads Marg's numbers and checks them against Marg's own
    totals. It adds no arithmetic of its own beyond that check.

THE THREE TRAPS IN THIS REPORT, ALL MEASURED ON REAL FILES
  1 · THE COLUMN SHIFT IS PER-ROW, NOT PER-MONTH.
      The queue recorded this as an April-vs-July difference. It is not.
      Within ONE file, both layouts appear, decided by whether packing+batch
      fits the print column:
          normal    col2='1*10    HT122559'   col3='5/27'
          overflow  col2='1*10'               col3='HT07256512/26'
      In the overflow form the batch and the expiry are CONCATENATED with no
      separator. Split on the trailing  M/YY  or  MM/YY , never on position.

  2 · THE SUPPLIER HEADING IS NOT ALWAYS IN COLUMN 0.
          row: col0='A.A. PHARMACEUTICALS'
          row: col0='DRUG'  col1='DEAL'  col2='BAREILLY'      <- one name, 3 cells
          row: col1='ESSENTIAL PHARMA'   col2='BAREILLY'      <- col0 EMPTY
      A reader that takes col0 as the supplier silently mis-attributes whole
      groups. Join every non-empty cell instead.

  3 · THE BILL NUMBER CAN MERGE INTO THE ITEM NAME.
          col0=''  col1='EP000476VITANSIAL PLUS'
      There is no reliable way to know where the bill number ends and the item
      begins — 'EP000476' is a plausible bill number AND a plausible SKU prefix.
      THIS MODULE DOES NOT GUESS. Such rows keep the full text as the item,
      set bill=None, and are COUNTED and REPORTED. A parser that guesses here
      would corrupt item identity, which is the one field everything else joins
      on.

REFUSAL
    A file is refused, with a reason, rather than half-parsed:
      · no header row              — not this report variant
      · a supplier group whose item AMOUNTs do not sum to its own TOTAL row
      · any row that is neither furniture, heading, item nor total
    Silence is the failure mode this project keeps paying for.
"""

import os
import re
import sys

# ---------------------------------------------------------------------------

HEADER_C0 = "BILL"
HEADER_C1 = "ITEM DESCRIPTION"
TITLE_RE = re.compile(
    r"PURCHASE STATEMENT FROM (\d{2}-\d{2}-\d{4}) TO (\d{2}-\d{2}-\d{4})", re.I)
# a trailing  M/YY  or  MM/YY  — the expiry, wherever it ended up
EXPIRY_TAIL_RE = re.compile(r"(\d{1,2}/\d{2})\s*$")
# a bill number fused onto the front of an item name (see trap 3)
MERGED_BILL_RE = re.compile(r"^([A-Z]{1,3}-?\d{5,7})([A-Z].+)$")
FURNITURE_RE = re.compile(
    r"^(SANJEEVNI|35G/15B|Phone\s*:|PAGE\b|C/F\b|GRAND\s+TOTAL|"
    r"SUPPLIER/ITEM WISE|Digital Purchase)", re.I)


class Refused(Exception):
    """The file cannot be trusted. Never returned as data."""


def _num(v):
    """A cell as float, or None. Text and numeric cells both occur."""
    if v is None:
        return None
    if isinstance(v, float):
        return v
    s = str(v).strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _txt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return str(int(v)) if v == int(v) else str(v)
    return str(v).strip()


def split_pair(cell):
    """
    'AMOUNT NET RATE' and 'LOOS PURC. ?' are TWO numbers printed in one column,
    separated by run-of-spaces:  '1895.26     9.48'  ->  (1895.26, 9.48)
    Returns (first, second); second is None when only one number is present.
    """
    s = _txt(cell)
    if not s:
        return (None, None)
    parts = s.split()
    nums = [_num(p) for p in parts]
    nums = [n for n in nums if n is not None]
    if not nums:
        return (None, None)
    if len(nums) == 1:
        return (nums[0], None)
    return (nums[0], nums[1])


def split_batch_expiry(c2, c3):
    """
    Recover (packing, batch, expiry) from the two cells, in either layout.
    Returns expiry as 'M/YY' exactly as Marg printed it, or None.
    """
    c2 = _txt(c2)
    c3 = _txt(c3)

    # layout A — expiry alone in col3, packing+batch in col2
    m = EXPIRY_TAIL_RE.match(c3) or (EXPIRY_TAIL_RE.search(c3)
                                     if c3 and EXPIRY_TAIL_RE.search(c3)
                                     and EXPIRY_TAIL_RE.search(c3).start() == 0
                                     else None)
    if c3 and re.fullmatch(r"\d{1,2}/\d{2}", c3):
        parts = re.split(r"\s{2,}", c2, maxsplit=1)
        packing = parts[0].strip()
        batch = parts[1].strip() if len(parts) > 1 else None
        return (packing or None, batch, c3)

    # layout B — col3 is batch+expiry concatenated, col2 is packing only
    m = EXPIRY_TAIL_RE.search(c3)
    if m:
        expiry = m.group(1)
        batch = c3[:m.start(1)].strip() or None
        return (c2.strip() or None, batch, expiry)

    # no expiry anywhere — batch may still be in col2
    parts = re.split(r"\s{2,}", c2, maxsplit=1)
    packing = parts[0].strip() or None
    batch = parts[1].strip() if len(parts) > 1 else (c3.strip() or None)
    return (packing, batch, None)


def _open_sheet(path):
    try:
        import xlrd
    except ImportError:
        raise Refused(
            "xlrd is not installed; it is needed to read Marg's legacy .xls. "
            "Install with:  pip install xlrd")
    book = xlrd.open_workbook(path)
    return book.sheet_by_index(0)


def read_purchase(path):
    """
    Parse one PURCHASE_ITEMWISE export.

    Returns dict:
      period      (from_iso, to_iso)
      rows        list of item dicts
      suppliers   list of {name, total_amount, total_net, n_rows}
      unsplit     rows whose bill number merged into the item name
      unparsed    rows the classifier could not place  (always empty, or Refused)
      no_expiry   rows with no expiry recovered
    """
    sh = _open_sheet(path)

    def cell(r, c):
        return sh.cell_value(r, c) if c < sh.ncols else ""

    # --- header ---------------------------------------------------------
    hdr = None
    period = (None, None)
    for r in range(min(30, sh.nrows)):
        t = _txt(cell(r, 0))
        if t.upper() == HEADER_C0 and _txt(cell(r, 1)).upper() == HEADER_C1:
            hdr = r
            break
        m = TITLE_RE.search(_txt(cell(r, 0)))
        if m:
            def iso(d):
                dd, mm, yy = d.split("-")
                return "%s-%s-%s" % (yy, mm, dd)
            period = (iso(m.group(1)), iso(m.group(2)))
    if hdr is None:
        raise Refused(
            "no 'BILL | ITEM DESCRIPTION' header row in the first 30 rows — "
            "this is not a SUPPLIER/ITEM WISE PURCHASE STATEMENT")

    rows, suppliers, unsplit, unparsed, no_expiry = [], [], [], [], []
    variances = []
    grand_amount = grand_net = None
    supplier = None
    group = []

    def close_group(total_net, total_amount, row_no):
        nonlocal group
        if supplier is None and not group:
            group = []
            return
        got = round(sum(x["amount"] or 0 for x in group), 2)
        want = round(total_amount, 2) if total_amount is not None else None
        var = None
        if want is not None:
            var = round(got - want, 2)
            if abs(var) > 0.05:
                variances.append({"row": row_no, "supplier": supplier,
                                  "items_sum": got, "total_row": want,
                                  "excess": var, "n_rows": len(group)})
        suppliers.append({"name": supplier, "total_amount": want,
                          "total_net": total_net, "n_rows": len(group),
                          "items_sum": got, "variance": var})
        group = []

    for r in range(hdr + 1, sh.nrows):
        c = [_txt(cell(r, i)) for i in range(min(12, sh.ncols))]
        while len(c) < 12:
            c.append("")
        if not any(c):
            continue
        joined = " ".join(x for x in c if x)
        # ⚠ THE PAGE FOOTER IS NOT IN COLUMN 0. Marg prints it as
        #     col5='Page'  col6='No..3'
        # so a furniture test that only looks at c[0] misses it, and the row
        # then falls through to the supplier-heading branch and becomes a
        # SUPPLIER CALLED 'Page No..3'. Measured before the fix: five phantom
        # suppliers holding Rs 5,68,835 — 27.5% of all purchase value — and
        # every group split by a page break was compared against the wrong
        # TOTAL row, which is what produced the "variance" this module once
        # blamed on Marg. Test the whole row, never one cell.
        if re.match(r"^\s*Page\s*No\.", joined, re.I):
            continue
        # ⚠ 'Continued..3' IS NOT A SUPPLIER — IT IS THE SAME SUPPLIER.
        # When a supplier's lines run past a page break, Marg reprints the
        # heading as 'Continued..N'. Treating it as a new heading SPLITS the
        # group: the lines before the break stay under the real name, the lines
        # after accumulate under 'Continued..N', and the group is then closed by
        # the real supplier's TOTAL row — comparing PART of the items against
        # ALL of the total. That is what produced the "+8,745 variance" this
        # module once reported as Marg printing lines its own totals exclude.
        # Skip the row and keep both the supplier AND the open group.
        if re.match(r"^\s*Continued\s*\.\.", joined, re.I):
            continue
        if FURNITURE_RE.match(c[0]) or (c[0].upper() == HEADER_C0
                                        and c[1].upper() == HEADER_C1):
            continue

        # GRAND TOTAL — split across two cells, exactly like a supplier name
        if c[0].upper() == "GRAND" and c[1].upper() == "TOTAL":
            grand_net, _ = split_pair(c[9])
            grand_amount = _num(c[11])
            close_group(None, None, r)   # flush any open group
            supplier = None
            continue

        # TOTAL row closes the current supplier group
        if c[7].upper() == "TOTAL":
            net, _ = split_pair(c[9])
            amt = _num(c[11])
            close_group(net, amt, r)
            supplier = None
            continue

        qty = _num(c[5])
        amount = _num(c[11])

        # item row: it has a quantity AND a line amount
        if qty is not None and amount is not None:
            packing, batch, expiry = split_batch_expiry(c[2], c[3])
            net_amount, net_rate = split_pair(c[9])
            loose, purc_rate = split_pair(c[10])
            bill = c[0] or None
            item = c[1]
            merged = False
            if bill is None and item:
                # ⚠ TRAP 3, REVISED S206 — the split is now EVIDENCED, not guessed.
                # Marg fuses the bill number onto the item name when the bill
                # column overflows:  'EP001498VITANSIAL PLUS'.
                # This module used to refuse to split, on the grounds that
                # 'EP000476' is as plausible a SKU prefix as a bill number.
                # Two things settled it:
                #   1 · PURCHASE_BILLWISE — an independent report — carries
                #       'EP001498' and 'IP003546' as REAL bill numbers, and both
                #       appear as prefixes here.
                #   2 · the shape is consistent across 23 rows and 4 vendors:
                #       EP/RM/IP + 6 digits, or T- + 6 digits.
                # The prefix is split off and `bill_merged_into_item` still marks
                # the row, so nothing downstream loses the fact that it happened.
                mm = MERGED_BILL_RE.match(item)
                if mm:
                    bill = mm.group(1)
                    item = mm.group(2).strip()
                merged = True
            row = {
                "source": os.path.basename(path),
                "row": r,
                "direction": "PURCHASE",
                "supplier": supplier,
                "bill": bill,
                "item": item,
                "packing": packing,
                "batch": batch,
                "expiry": expiry,
                "tax": _num(c[4]),
                "qty": qty,
                "free": _num(c[6]),
                "rate": _num(c[7]),
                "discount_pct": _num(c[8]),
                "net_amount": net_amount,
                "net_rate": net_rate,
                "loose_qty": loose,
                "purchase_rate": purc_rate,
                "amount": amount,
                "bill_merged_into_item": merged,
            }
            rows.append(row)
            group.append(row)
            if merged:
                unsplit.append(row)
            if expiry is None:
                no_expiry.append(row)
            continue

        # otherwise: a supplier heading — join every non-empty cell (trap 2)
        name = " ".join(x for x in c if x).strip()
        if name and qty is None and amount is None:
            if group and name == supplier:
                continue          # the same heading reprinted after a page break
            if group:
                close_group(None, None, r)   # a group that ended without a TOTAL
            supplier = name
            continue

        unparsed.append({"row": r, "cells": c})

    if unparsed:
        raise Refused(
            "%d row(s) could not be classified, first at row %d: %r — "
            "a parser that drops rows silently is worse than none"
            % (len(unparsed), unparsed[0]["row"], unparsed[0]["cells"]))

    if group:
        close_group(None, None, sh.nrows)

    tot_sum = round(sum(s["total_amount"] or 0 for s in suppliers), 2)
    if grand_amount is not None and abs(tot_sum - round(grand_amount, 2)) > 0.05:
        raise Refused(
            "the supplier TOTAL rows sum to %.2f but GRAND TOTAL says %.2f — "
            "the report does not partition; nothing here can be trusted"
            % (tot_sum, grand_amount))

    return {"period": period, "rows": rows, "suppliers": suppliers,
            "unsplit": unsplit, "unparsed": unparsed, "no_expiry": no_expiry,
            "variances": variances, "grand_amount": grand_amount,
            "grand_net": grand_net, "totals_sum": tot_sum,
            "items_sum": round(sum(r["amount"] or 0 for r in rows), 2)}
