#!/usr/bin/python3
"""
marg_stock.py — read Marg's CLOSING STOCK and STOCK EXPIRY exports.

TWO THINGS THE FILENAMES DO NOT TELL YOU, both measured on the real archive:

 1 · The four `STOCK_CLOSING_TOTALS__2026-08-26__*` files exported within four
     minutes of each other are NOT duplicates and NOT retries. They are FOUR
     DIFFERENT STORES, and only the title row says which:
         DTH CLOSING STOCK ...            MAIN STORE CLOSING STOCK ...
         SCRAP STORE CLOSING STOCK ...    WHOLE STORES CLOSING STOCK ...
     Picking one by timestamp or by size gets you a different warehouse.
     **Read the title. Never the filename.**

 2 · The two `STOCK_EXPIRY_DEFAULT__2026-08-23__*` files, 53 seconds apart, are
     two DIFFERENT expiry cutoffs — one lists stock already expired, the other
     lists stock expiring soon. Both carry the identical header line
     `EXP. BEFORE *BA., 0`, so **the header cannot tell them apart and the
     contents must.**

STOCK QUANTITIES
    Marg prints `packs:loose` against a packing of `1*N`:
        '4:14' with packing '1*20'  ->  4 full strips + 14 loose  =  94 units
    A bare number is loose units. '-' is nil.
    **Negative values occur and are preserved, never clamped** — a negative
    stock line is a real finding, not a parse error.
"""

import os
import re

TITLE_RE = re.compile(r"^(.*?)\s+CLOSING STOCK AS ON\s+(\d{2}-\d{2}-\d{4})", re.I)
PACKING_RE = re.compile(r"(\d+)\s*\*\s*(\d+)\s*\.?\s*$")
# ⚠ THE STOCK REPORT PUTS name AND packing IN ONE CELL, space-padded:
#     'ACILOC 300                    1*20'
#     'BRUTAFLAM GEL                 30GM'
# Stripping only the 1*N shape leaves 'BRUTAFLAM GEL 30GM' as the item NAME,
# which then looks like a SECOND item code for a product that trades under
# 'BRUTAFLAM GEL'. That is not a Marg fault — it was this parser's. Measured
# against the item master, the packing column holds 1*N, <num><unit>, VAIL and
# a few bare numbers.
# SAFETY: only a field separated by TWO OR MORE spaces can be the packing.
# 'ALCOXIB 120' ends in a number with ONE space and must never be split.
PACK_TOKEN_RE = re.compile(
    r"^(?:\d+\s*\*\s*\d+|\d+(?:\.\d+)?\s*(?:GM|ML|MG|MCG|G|KG|L|GRAM|GMS)|VAIL|VIAL|\d+(?:\.\d+)?)\.?$",
    re.I)
QTY_RE = re.compile(r"^(\d+)\s*:\s*(\d+)$")


class Refused(Exception):
    pass


def _txt(v):
    if isinstance(v, float):
        return str(int(v)) if v == int(v) else str(v)
    return str(v).strip()


def norm_name(s):
    """
    Collapse runs of spaces. Marg pads names to the print column, and the
    per-store and multi-store exports pad DIFFERENTLY: the same product arrives
    as 'C2CAL SYP<29 spaces>200ML' in one and 'C2CAL SYP' + '200ML' in the
    other. Without this, 11 real items look like 22 half-empty ones and a
    cross-check reports disagreements that are pure whitespace.
    """
    return re.sub(r"\s+", " ", (s or "")).strip()


def split_desc(cell):
    """'ACILOC 300                    1*20' -> ('ACILOC 300', '1*20', 20)"""
    s = _txt(cell)
    # In the MULTI-STORE layout the packing arrives alone in its own cell
    # ('200ML'), with the name already in the previous column. Without this,
    # a bare pack token is read as an item NAME and the cross-store identity
    # goes red on 10 items — which is how this was caught.
    if PACK_TOKEN_RE.match(s.strip()):
        m0 = PACKING_RE.search(s.strip())
        try:
            sz0 = int(m0.group(2)) if m0 else None
        except (ValueError, AttributeError):
            sz0 = None
        return (None, s.strip(), sz0)
    # split on runs of 2+ spaces — Marg pads the packing into its own column
    parts = re.split(r"\s{2,}", s.strip())
    if len(parts) > 1 and PACK_TOKEN_RE.match(parts[-1].strip()):
        packing = parts[-1].strip()
        name = norm_name(" ".join(parts[:-1]))
        m2 = PACKING_RE.search(packing)
        try:
            size = int(m2.group(2)) if m2 else None
        except (ValueError, AttributeError):
            size = None
        return (name or None, packing, size)
    m = PACKING_RE.search(s)
    if not m:
        return (norm_name(s) or None, None, None)
    packing = m.group(0).strip()
    name = norm_name(s[:m.start()])
    try:
        size = int(m.group(2))
    except ValueError:
        size = None
    return (name or None, packing, size)


def parse_qty(cell, pack_size):
    """
    Returns (packs, loose, units, raw). units is None when it cannot be
    computed without inventing a pack size.

    ⚠ THE SIGN COVERS THE WHOLE QUANTITY, NOT THE PACKS FIELD.
    Marg prints negative stock as '-0:10' and '-4:4'. Reading the '-' as
    belonging to the packs number gives  -0*10+10 = +10  and  -4*10+4 = -36:
    both plausible, both WRONG. The true values are -10 and -44.
    Proven by Marg's own arithmetic: for BIO D3 MAX, DTH '-0:10' and MAIN '0:6'
    must sum to WHOLE STORES '-0:4'.  -10 + 6 = -4 ✓   (+10 + 6 = 16 ✗)
    The cross-store identity in the selftest is what caught this.
    """
    s = _txt(cell)
    if not s or s == "-":
        return (0, 0, 0, s or "-")
    neg = s.startswith("-")
    body = s[1:].strip() if neg else s
    m = QTY_RE.match(body)
    if m:
        packs, loose = int(m.group(1)), int(m.group(2))
        units = packs * pack_size + loose if pack_size else None
        if neg:
            packs, loose = -packs, -loose
            units = -units if units is not None else None
        return (packs, loose, units, s)
    try:
        v = float(s)
        return (0, v, v, s)
    except ValueError:
        return (None, None, None, s)


def _sheet(path):
    """Open .xls OR .xlsx.

    S207, 28-Aug-2026. This read .xls only, through xlrd, and xlrd 2.x dropped
    .xlsx entirely -- so a stock export saved as .xlsx died with
    "Excel xlsx file; not supported".

    That is not a hypothetical. Marg saves its exports by driving Excel over
    OLE, and when that channel fails ("Unable to save file, Problem in excel
    ver saving!") the working fallback is to Save As from Excel by hand --
    which produces .xlsx. So the format this could not read is exactly the
    format that arrives on the days Marg is broken, which are the days the
    reading matters most.

    xlsx_sheet.open_sheet_any already solved this for the sale side. It is the
    same fix, one module over -- and it was sitting unused here the whole time.
    """
    from xlsx_sheet import open_sheet_any
    return open_sheet_any(path)


def read_closing(path):
    """One CLOSING STOCK export. The STORE comes from the title row."""
    sh = _sheet(path)

    def c(r, i):
        return _txt(sh.cell_value(r, i)) if i < sh.ncols else ""

    store = as_on = None
    hdr = None
    for r in range(min(20, sh.nrows)):
        m = TITLE_RE.match(c(r, 0))
        if m:
            store, as_on = m.group(1).strip().upper(), m.group(2)
        if c(r, 0) == "S.No." and c(r, 1).upper() == "DESCRIPTION":
            hdr = r
            break
    if hdr is None:
        raise Refused("no 'S.No. | Description' header — not a CLOSING STOCK export")
    if store is None:
        raise Refused(
            "no '<STORE> CLOSING STOCK AS ON <date>' title row — refusing rather "
            "than guessing the store from the filename")

    rows = []
    for r in range(hdr + 1, sh.nrows):
        desc = c(r, 1)
        if not desc:
            continue
        if desc.upper() == "DESCRIPTION" or c(r, 0) == "S.No.":
            continue                      # the header reprints at page breaks
        name, packing, size = split_desc(desc)
        if not name:
            continue
        packs, loose, units, raw = parse_qty(c(r, 2), size)
        rows.append({"store": store, "as_on": as_on, "item": name,
                     "packing": packing, "pack_size": size,
                     "packs": packs, "loose": loose, "units": units,
                     "raw": raw, "unit": c(r, 3), "row": r})
    return {"store": store, "as_on": as_on, "rows": rows, "source": os.path.basename(path)}


def read_expiry(path):
    """
    One STOCK EXPIRY export. Layout: 'S.No. Description  packing' | Batch |
    Expiry M/YYYY | 'packs:loose UNIT'.
    """
    sh = _sheet(path)

    def c(r, i):
        return _txt(sh.cell_value(r, i)) if i < sh.ncols else ""

    hdr = None
    for r in range(min(20, sh.nrows)):
        if c(r, 0).startswith("S.No.") and c(r, 1).upper() == "BATCH":
            hdr = r
            break
    if hdr is None:
        raise Refused("no 'S.No. Description | Batch' header — not a STOCK EXPIRY export")

    rows = []
    for r in range(hdr + 1, sh.nrows):
        d, batch, exp, stock = c(r, 0), c(r, 1), c(r, 2), c(r, 3)
        if not batch or d.upper().startswith("TOTAL"):
            continue
        d = re.sub(r"^\s*\d+\s+", "", d)          # strip the serial number
        d = norm_name(d)
        name, packing, size = split_desc(d)
        qty_txt = stock.split()[0] if stock else ""
        unit = " ".join(stock.split()[1:]) if stock else ""
        packs, loose, units, raw = parse_qty(qty_txt, size)
        rows.append({"item": name, "packing": packing, "pack_size": size,
                     "batch": batch, "expiry": exp,
                     "packs": packs, "loose": loose, "units": units,
                     "raw": raw, "unit": unit, "row": r})
    return {"rows": rows, "source": os.path.basename(path)}


# ---------------------------------------------------------------------------
# The MULTI-STORE closing-stock export  (added S206, from the file the router
# REFUSED on 27-Aug-2026 — correctly, because it matched the title and not the
# layout. D188: a file is not identified by its name.)
#
# One file carries every store, and it is a DIFFERENT SHAPE from the per-store
# export in three ways, each of which silently corrupts a naive read:
#
#   1 · THE ITEM NAME IS SPLIT ACROSS TWO COLUMNS.
#         col0='ANKLE'  col1='BINDER BAMBOO L         1*1'
#       Reading col0 as the item gives you nine different products all called
#       'ANKLE'. The name is col0 + col1-minus-packing.
#
#   2 · TWO STORES ARE MERGED INTO ONE COLUMN, space-separated:
#         col2 = 'STOCK      DTH'   ->  '-0:4   -0:10'   =  WHOLE -4, DTH -10
#         col3 = 'MAIN ST'          ->  '0:6'            =  MAIN   6
#       The header spans TWO rows (col3's caption is on the row below), so a
#       one-row header read loses 'MAIN ST' entirely.
#
#   3 · The title names the stores REQUESTED, not the columns present:
#         'SCRAP STORE,WHOLE,CLOSING STOCK AS ON 26-08-2026'
#       SCRAP appears in the title and has no column at all.
#
# Verified against the four per-store exports of the same date: WHOLE, DTH and
# MAIN agree item-for-item, and WHOLE == MAIN + DTH holds inside this file too.
# ---------------------------------------------------------------------------

MULTI_TITLE_RE = re.compile(r"CLOSING STOCK AS ON\s+(\d{2}-\d{2}-\d{4})", re.I)


def read_closing_multi(path):
    """
    One multi-store CLOSING STOCK export -> {'as_on', 'rows'}, each row
    carrying whole/dth/main unit counts. Refuses anything that is not this
    exact layout rather than guessing which column is which store.
    """
    sh = _sheet(path)

    def c(r, i):
        return _txt(sh.cell_value(r, i)) if i < sh.ncols else ""

    as_on = None
    hdr = None
    for r in range(min(20, sh.nrows)):
        m = MULTI_TITLE_RE.search(c(r, 0))
        if m:
            as_on = m.group(1)
        flat = c(r, 2).replace(" ", "").upper()
        if c(r, 0).replace(" ", "").upper() == "ITEM" and flat.startswith("STOCK"):
            hdr = r
            break
    if hdr is None:
        raise Refused(
            "no 'I T E M | ... | STOCK  DTH' header — this is not the "
            "multi-store closing-stock layout")
    if "DTH" not in c(hdr, 2).replace(" ", "").upper():
        raise Refused("column 2 caption is %r — expected the merged 'STOCK DTH'"
                      % c(hdr, 2))
    main_caption = c(hdr + 1, 3).replace(" ", "").upper()
    if not main_caption.startswith("MAINST"):
        raise Refused(
            "the second header row does not caption column 3 as 'MAIN ST' "
            "(got %r) — refusing rather than assuming which store it is"
            % c(hdr + 1, 3))
    if as_on is None:
        raise Refused("no 'CLOSING STOCK AS ON <date>' title row")

    rows = []
    for r in range(hdr + 2, sh.nrows):
        a, b = c(r, 0), c(r, 1)
        if not a and not b:
            continue
        if a.replace(" ", "").upper() in ("ITEM", "TOTAL"):
            continue
        rest, packing, size = split_desc(b)
        name = norm_name(a + " " + (rest or ""))
        if not name:
            continue
        pair = c(r, 2).split()
        whole_raw = pair[0] if pair else "-"
        dth_raw = pair[1] if len(pair) > 1 else "-"
        w = parse_qty(whole_raw, size)
        d = parse_qty(dth_raw, size)
        m = parse_qty(c(r, 3), size)
        rows.append({"item": name, "packing": packing, "pack_size": size,
                     "whole": w[2], "dth": d[2], "main": m[2],
                     "whole_raw": whole_raw, "dth_raw": dth_raw,
                     "main_raw": c(r, 3), "row": r})
    return {"as_on": as_on, "rows": rows, "source": os.path.basename(path)}
