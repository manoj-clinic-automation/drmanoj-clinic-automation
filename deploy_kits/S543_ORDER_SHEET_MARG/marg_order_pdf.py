#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  marg_order_pdf.py  ·  v1.0  ·  kit S543_ORDER_SHEET_MARG  ·  Session 312 (Sanjeevni)  ·  D716
#
#  "MARG KA ORDER (PDF)" -- Marg's own PENDING ORDERS (PURCHASE) export, printed as Marg printed it, beside the system's order sheet
#  (order_sheet_pdf) so the staff can lay the two side by side. The owner, 13-Oct-2026 05:24 IST (D716): "Marg's own purchase-order PDF
#  beside the system's".
#    * The newest export by its own capture stamp (order_sheet.newest_sheet), read from the door's archived copy (order_sheet.sheet_file,
#      order_sheet.rows_from_file) -- the title row, Marg's eleven column heads in Marg's order, every row, the TOTAL row.
#    * Cell text: text as it is; a number with no fraction -> its integer (10.0 -> 10); the RATE column -> two decimals (110.0 -> 110.00);
#      any other number -> at most two decimals. A cell wider than its column wraps inside it.
#    * A4 landscape, Helvetica 8 pt (heads bold), the column heads repeated on every page; the foot "Marg se nikala: dd-mm-yyyy hh:mm
#      (Darpan) · chhapa: dd-mm-yyyy hh:mm · Sanjeevni" and the page number.
#    * No sheet, or its file not on the server: one page saying so (the route still answers 200).
#  The page writer is order_sheet_pdf's (_Page, width, wrap, _build -- imported, never copied); only the geometry is this file's.
#  Suppliers' phone numbers are printed because Marg prints them (a staff page); this file writes nothing anywhere.
# =============================================================================
import order_sheet as OS
import order_sheet_pdf as SP

VERSION = "1.0"
KIT = "S543_ORDER_SHEET_MARG"
MM = 72.0 / 25.4
W, H = 841.89, 595.28                                       # A4 landscape
LM, RM, TOP, BOT = 12 * MM, W - 12 * MM, H - 11 * MM, 11 * MM
SZ, TITLE_SZ, FOOT_SZ = 8.0, 12.0, 8.0
LH = 9.6                                                    # one text line inside a cell
PAD = 1.4 * MM
RATE_COL = 9
RIGHT = (6, 7, 8, 9, 10)                                    # ORDER QTY, RECEIVE, PENDING, RATE, VALUE: right-aligned, as Marg's figures
NO_FILE = "Marg ka order abhi server par nahi hai — Darpan se Marg mein PENDING ORDERS export karwaiye."
HEAD_TOP = TOP - 9 * MM                                     # the column heads start under the title
FOOT_Y = BOT + 1.5 * MM


def cell_text(v, col):
    """One cell as Marg shows it: text as it is; a whole number as an integer; RATE with two decimals; else at most two decimals."""
    if isinstance(v, bool):
        v = int(v)
    if isinstance(v, (int, float)):
        f = float(v)
        if col == RATE_COL:
            return "%.2f" % f
        if f == int(f):
            return "%d" % int(f)
        return ("%.2f" % f).rstrip("0").rstrip(".")
    return str(v if v is not None else "").strip()


def _parts(rows):
    """(title lines, heads, body rows up to and including TOTAL) of the export's rows."""
    hi = next((i for i, r in enumerate(rows) if [str(x).strip().upper() for x in r[:3]] == ["SUPPLIER", "PHONES", "ITEM NAME"]), None)
    if hi is None:
        raise ValueError("the export's heads are not where they must be")
    n = len(rows[hi])
    title = ["  ".join(cell_text(x, -1) for x in r if cell_text(x, -1)) for r in rows[:hi]]
    title = [t for t in title if t]
    heads = [cell_text(x, -1) for x in rows[hi]]
    body = []
    for r in rows[hi + 1:]:
        r = list(r) + [""] * (n - len(r))
        cells = [cell_text(r[c], c) for c in range(n)]
        if not any(cells):
            continue
        body.append(cells)
        if cells[0].upper() == "TOTAL" and not cells[2]:
            break
    return title, heads, body


def _widths(heads, body):
    """Each column's width: its widest text at 8 pt (heads bold) plus padding, scaled down together when they pass the page."""
    nat = []
    for c in range(len(heads)):
        w = SP.width(heads[c], SZ, True)
        for r in body:
            w = max(w, SP.width(r[c], SZ, r is body[-1] and r[0].upper() == "TOTAL"))
        nat.append(w + 2 * PAD + 0.5)
    tot = sum(nat)
    room = RM - LM
    if tot <= room:
        extra = (room - tot) / len(nat)
        return [w + extra for w in nat]
    return [w * room / tot for w in nat]


def _row_lines(cells, ws, bold):
    return [SP.wrap(cells[c], SZ, ws[c] - 2 * PAD, bold) if cells[c] else [""] for c in range(len(cells))]


def _row_h(lines):
    return 3.0 + max(len(x) for x in lines) * LH


def _draw_row(p, y, cells, ws, bold, shade=None):
    """One row at top y; returns its height. Every cell's text inside its own column."""
    lines = _row_lines(cells, ws, bold)
    h = _row_h(lines)
    if shade is not None:
        p.fill(LM, y - h, RM - LM, h, shade)
    p.box(LM, y - h, RM - LM, h, 0.5, 0.35)
    x = LM
    for c, w in enumerate(ws):
        if c:
            p.line(x, y - h, x, y, 0.4, 0.45)
        for k, s in enumerate(lines[c]):
            if not s:
                continue
            by = y - 1.5 - 0.8 * SZ - k * LH
            if c in RIGHT and not bold:
                p.text(x + w - PAD, by, s, SZ, "F1", "r")
            else:
                p.text(x + PAD, by, s, SZ, "F2" if bold else "F1")
        x += w
    return h


def _foot(con, ns):
    taken = OS._stamp_text(ns, True) if ns else ""
    return "Marg se nikala: %s (Darpan)  ·  chhapa: %s  ·  Sanjeevni" % (taken or "-", OS.now().strftime("%d-%m-%Y %H:%M"))


def _no_file_pdf():
    p = SP._Page()
    p.text(LM, TOP - 6 * MM, "Marg ka order", TITLE_SZ, "F2")
    for k, s in enumerate(SP.wrap(NO_FILE, 11, RM - LM)):
        p.text(LM, TOP - 16 * MM - k * 15, s, 11)
    p.text(LM, FOOT_Y, "chhapa: %s  ·  Sanjeevni" % OS.now().strftime("%d-%m-%Y %H:%M"), FOOT_SZ)
    return SP._build([p], "Marg ka order", size=(W, H))


def build(con):
    """The PDF bytes of Marg's newest PENDING ORDERS export, as Marg printed it -- or the one page saying it is not on the server."""
    ns = OS.newest_sheet(con)
    path = OS.sheet_file(con, ns) if ns else ""
    if not path:
        return _no_file_pdf()
    try:
        title, heads, body = _parts(OS.rows_from_file(path))
    except Exception:                                         # noqa: BLE001 -- an unreadable file reads as no file
        return _no_file_pdf()
    ws = _widths(heads, body)
    foot = _foot(con, ns)
    pages, p, y = [], None, 0.0
    floor = FOOT_Y + 5 * MM

    def new_page():
        q = SP._Page()
        ty = TOP - 5 * MM
        for t in (title or ["PENDING ORDERS (PURCHASE)"]):
            q.text(LM, ty, t, TITLE_SZ, "F2")
            ty -= 5 * MM
        return q, min(HEAD_TOP, ty + 1 * MM)
    for i, cells in enumerate(body):
        bold = cells[0].upper() == "TOTAL" and i == len(body) - 1
        h = _row_h(_row_lines(cells, ws, bold))
        if p is None or y - h < floor:
            if p is not None:
                pages.append(p)
            p, y = new_page()
            y -= _draw_row(p, y, heads, ws, True, 0.86)
        y -= _draw_row(p, y, cells, ws, bold, 0.93 if bold else None)
    if p is None:
        p, y = new_page()
        _draw_row(p, y, heads, ws, True, 0.86)
    pages.append(p)
    n = len(pages)
    for k, q in enumerate(pages, 1):
        q.line(LM, FOOT_Y + 3.6 * MM, RM, FOOT_Y + 3.6 * MM, 0.5)
        q.text(LM, FOOT_Y, foot, FOOT_SZ)
        q.text(RM, FOOT_Y, "Page %d / %d" % (k, n), FOOT_SZ, "F1", "r")
    return SP._build(pages, "Marg ka order %s" % (OS._stamp_text(ns, True) if ns else ""), size=(W, H))


def _main():
    import sqlite3                                            # noqa: PLC0415
    import sys                                                # noqa: PLC0415
    con = sqlite3.connect(sys.argv[1])
    con.row_factory = sqlite3.Row
    sys.stdout.buffer.write(build(con))


if __name__ == "__main__":
    _main()
