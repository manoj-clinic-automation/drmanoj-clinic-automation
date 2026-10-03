#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  order_sheet_pdf.py  ·  v1.0  ·  kit S454_BILL_REGISTER (part 1)  ·  Session 283 (Sanjeevni)  ·  D666 / D669
#
#  "ORDER SHEET PRINT KARO" -- the A4 page the staff were given on 03-Oct, used and accepted (the S454 mock's screen 6 and the chat's
#  S454_ORDER_SHEET_PROTOTYPE): the head (the shop, ORDER SHEET, the page number; whose order, its date, how many suppliers and
#  medicines); ONE row of column heads per page (Item · Pack · Qty · Order · Aaya · Kam aaya / nahi aaya); a shaded band per supplier
#  with the phone book's number(s) -- "(number nahi hai)" when none -- and three boxes (WhatsApp · Call · Bill scan); a row per medicine
#  with its quantity in bold and empty boxes under Order and Aaya; the old pending lines the staff still see under their supplier, tagged
#  "purana, dd-mm" with what the system knows and NO box under Order (order.sheet_print_old = 0 leaves them off); a supplier with only
#  old lines after the others, under "Sirf purane pending"; the foot's instruction and "Order kisne kiya / Maal kisne liya / Tareekh".
#  A supplier's block is never split across pages. The layout lives here, in one place: layout() is what build() draws and what the
#  walk reads. Written by hand (A4 portrait, Helvetica, uncompressed) -- the server has no PDF library.
# =============================================================================
import order_sheet as OS

MM = 72.0 / 25.4
W, H = 595.28, 841.89
LM, RM, TOP, BOT = 12 * MM, W - 12 * MM, H - 11 * MM, 11 * MM
COLS = (("Item", 66), ("Pack", 17), ("Qty", 25), ("Order", 17), ("Aaya", 17), ("Kam aaya / nahi aaya", 44))
ROW, BAND, GAP, BOX = 6.7 * MM, 7.4 * MM, 1.7 * MM, 3.6 * MM
SHOP = "SANJEEVNI MEDICOS"
FOOT1 = ("Order ho gaya to 'Order' mein tick.  Maal aaya to 'Aaya' mein tick.  Kam aaya to kitna aaya, likhiye.  Nahi aaya to X.  "
         "Purane pending: dobara order tabhi, jab zaroorat ho.")
FOOT2 = "Order kisne kiya: ____________________     Maal kisne liya: ____________________     Tareekh: ____________"


def _xs():
    xs = [LM]
    for _t, w in COLS:
        xs.append(xs[-1] + w * MM)
    return xs


def _cdp():
    import clinic_day_pdf as cdp                              # noqa: PLC0415 -- the server's own PDF writer's fonts and widths (S224)
    return cdp


def width(s, size, bold=False):
    return _cdp()._width(_cdp()._latin(s), size, bold)


def layout(con):
    """{head, line, blocks:[{name, phones, only_old, rows:[{item, pack, qty, old, tag}]}], pages:[[block index]]} -- what is printed."""
    OS.ensure(con)
    src = OS.source(con)
    es = OS.entries(con)
    print_old = OS.setting(con, "order.sheet_print_old") != "0"
    olds = OS.old_lines(con) if (print_old and src == "marg_sheet") else []
    by_old = {}
    for l in olds:
        by_old.setdefault(l["supplier_norm"], []).append(l)
    blocks = []
    for e in es:
        p1, p2 = OS._phones(con, e["vendor"])
        rows = [dict(item=l["item"], pack=(l.get("packing") or "").rstrip("."), qty=OS.line_qty_text(l), old=False, tag="") for l in e["lines"]]
        for l in by_old.pop(e["sn"], []):
            rows.append(dict(item=l["item"], pack=(l["packing"] or "").rstrip("."), qty=OS.qty_text(l["qty_raw"]), old=True,
                             tag="purana, %s · %s" % (OS.ddmm(l["line_date"]), OS.old_word(l))))
        blocks.append(dict(name=e["vendor"], phones=[x for x in (p1, p2) if x], only_old=False, rows=rows))
    blocks.sort(key=lambda b: b["name"])
    rest = []
    for sn, ls in sorted(by_old.items(), key=lambda kv: kv[1][0]["supplier"]):
        p1, p2 = OS._phones(con, ls[0]["supplier"])
        rest.append(dict(name=ls[0]["supplier"], phones=[x for x in (p1, p2) if x], only_old=True,
                         rows=[dict(item=l["item"], pack=(l["packing"] or "").rstrip("."), qty=OS.qty_text(l["qty_raw"]), old=True,
                                    tag="purana, %s · %s" % (OS.ddmm(l["line_date"]), OS.old_word(l))) for l in ls]))
    blocks += rest
    ns = OS.newest_sheet(con)
    n_new = sum(1 for b in blocks for r in b["rows"] if not r["old"])
    n_old = sum(1 for b in blocks for r in b["rows"] if r["old"])
    if src == "marg_sheet":
        date = OS.dmy(ns["newest_date"]) if ns else OS.today().strftime("%d-%m-%Y")
        whose = "Darpan (Marg)"
    else:
        date, whose = OS.today().strftime("%d-%m-%Y"), "System"
    line = "Order: %s  ·  %s  ·  %d supplier  ·  %d item" % (date, whose, len(blocks), n_new + n_old)
    if n_old:
        line += ": %d naye, %d purane pending" % (n_new, n_old)
    pages, used = [[]], 0.0
    avail = (TOP - 14 * MM - 6 * MM - GAP) - (BOT + 14 * MM)
    first_only = None
    for i, b in enumerate(blocks):
        h = BAND + ROW * len(b["rows"]) + GAP + (5 * MM if (b["only_old"] and first_only is None) else 0)
        if b["only_old"] and first_only is None:
            first_only = i
        if used + h > avail and pages[-1]:
            pages.append([])
            used = 0.0
        pages[-1].append(i)
        used += h
    return dict(line=line, date=date, blocks=blocks, pages=pages, first_only=first_only, print_old=print_old)


class _Page(object):
    def __init__(self):
        self.ops = []

    def text(self, x, y, s, size, font="F1", align="l"):
        cdp = _cdp()
        s = cdp._latin(s)
        if align == "r":
            x -= cdp._width(s, size, font == "F2")
        elif align == "c":
            x -= cdp._width(s, size, font == "F2") / 2.0
        self.ops.append(b"BT /%s %.1f Tf 0 g %.2f %.2f Td (%s) Tj ET" % (font.encode(), size, x, y, cdp._PDF._pdfstr(s)))

    def line(self, x1, y1, x2, y2, w=0.6, gray=0.0):
        self.ops.append(b"%.2f w %.3f G %.2f %.2f m %.2f %.2f l S" % (w, gray, x1, y1, x2, y2))

    def fill(self, x, y, w, h, gray):
        self.ops.append(b"%.3f g %.2f %.2f %.2f %.2f re f 0 g" % (gray, x, y, w, h))

    def box(self, x, y, w, h, lw=0.8, gray=0.0, tag=b""):
        self.ops.append(b"%.2f w %.3f G %.2f %.2f %.2f %.2f re S%s" % (lw, gray, x, y, w, h, (b" % " + tag) if tag else b""))


def _build(pages, title):
    objs = []

    def add(body):
        objs.append(body)
        return len(objs)
    cat = add(None)
    pg = add(None)
    f1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    f2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    f3 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")
    kids = []
    for p in pages:
        stream = b"\n".join(p.ops)
        c = add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        kids.append(add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] /Resources << /Font << /F1 %d 0 R /F2 %d 0 R /F3 %d 0 R >> >> /Contents %d 0 R >>"
                        % (pg, W, H, f1, f2, f3, c)))
    objs[cat - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pg
    objs[pg - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % k for k in kids), len(kids))
    info = add(b"<< /Title (%s) /Producer (order_sheet_pdf S454) >>" % _cdp()._PDF._pdfstr(title))
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offs = []
    for i, body in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs:
        out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, cat, info, xref)
    return bytes(out)


def build(con, lay=None):
    lay = lay or layout(con)
    xs = _xs()
    out = []
    np_ = len(lay["pages"])
    for pi, idxs in enumerate(lay["pages"], 1):
        p = _Page()
        y = TOP
        p.text(LM, y - 5 * MM, SHOP, 15, "F2")
        p.text(LM + 62 * MM, y - 5 * MM, "ORDER SHEET", 12.5, "F2")
        p.text(RM, y - 5 * MM, "Page %d / %d" % (pi, np_), 9.5, "F1", "r")
        p.text(LM, y - 10.2 * MM, lay["line"], 9.5)
        p.line(LM, y - 12.2 * MM, RM, y - 12.2 * MM, 1.2)
        y -= 14 * MM
        p.fill(LM, y - 6 * MM, RM - LM, 6 * MM, 0.86)
        p.box(LM, y - 6 * MM, RM - LM, 6 * MM, 0.6)
        for i, (t, _w) in enumerate(COLS):
            if i in (3, 4):
                p.text((xs[i] + xs[i + 1]) / 2, y - 4.2 * MM, t, 8.6, "F2", "c")
            else:
                p.text(xs[i] + 1.6 * MM, y - 4.2 * MM, t, 8.6, "F2")
            if i:
                p.line(xs[i], y - 6 * MM, xs[i], y)
        y -= 6 * MM + GAP
        for bi in idxs:
            b = lay["blocks"][bi]
            if bi == lay["first_only"]:
                p.text(LM, y - 3.6 * MM, "Sirf purane pending", 10, "F2")
                y -= 5 * MM
            p.fill(LM, y - BAND, RM - LM, BAND, 0.93)
            p.box(LM, y - BAND, RM - LM, BAND, 0.9)
            p.text(LM + 1.6 * MM, y - 5.1 * MM, b["name"], 10.6, "F2")
            nx = LM + 1.6 * MM + width(b["name"], 10.6, True) + 4 * MM
            p.text(nx, y - 5.1 * MM, "Ph. " + (", ".join(b["phones"]) if b["phones"] else "(number nahi hai)"), 9.6)
            x = RM - 1.6 * MM
            for lab in ("Bill scan", "Call", "WhatsApp"):
                w = width(lab, 8.8)
                x -= w
                p.text(x, y - 5.0 * MM, lab, 8.8)
                x -= 1.3 * MM + BOX
                p.box(x, y - BAND + (BAND - BOX) / 2, BOX, BOX, 0.9, tag=b"band-" + lab.split()[0].lower().encode())
                x -= 4.2 * MM
            y -= BAND
            for r in b["rows"]:
                p.box(LM, y - ROW, RM - LM, ROW, 0.5, 0.25)
                for i in range(1, len(COLS)):
                    p.line(xs[i], y - ROW, xs[i], y, 0.5, 0.25)
                p.text(xs[0] + 1.6 * MM, y - 4.7 * MM, _cdp()._fit(r["item"], 10.2, xs[1] - xs[0] - 3 * MM) if not r["old"] else r["item"], 10.2)
                if r["old"]:
                    tx = xs[0] + 1.6 * MM + width(r["item"], 10.2) + 2 * MM
                    p.text(tx, y - 4.6 * MM, r["tag"], 7.0, "F3")
                p.text(xs[1] + 1.6 * MM, y - 4.7 * MM, r["pack"], 9.2)
                p.text(xs[2] + 1.6 * MM, y - 4.7 * MM, r["qty"], 10.4, "F2")
                for i in ((4,) if r["old"] else (3, 4)):
                    p.box((xs[i] + xs[i + 1]) / 2 - BOX / 2, y - ROW + (ROW - BOX) / 2, BOX, BOX, 0.8, tag=b"col-" + COLS[i][0].lower().encode())
                y -= ROW
            y -= GAP
        fy = BOT + 9 * MM
        p.line(LM, fy + 3.4 * MM, RM, fy + 3.4 * MM, 0.6)
        p.text(LM, fy - 0.6 * MM, FOOT1, 7.6)
        p.text(LM, fy - 7.2 * MM, FOOT2, 9.5)
        out.append(p)
    if not out:
        out.append(_Page())
    return _build(out, "Sanjeevni order sheet %s" % lay["date"])


def text_of(pdf):
    """Every string drawn, in order -- what the walk reads back."""
    import re                                                 # noqa: PLC0415
    return [m.decode("cp1252").replace("\\(", "(").replace("\\)", ")").replace("\\\\", "\\") for m in re.findall(rb"\((.*?)(?<!\\)\) Tj", pdf)]


def _main():
    import sqlite3                                            # noqa: PLC0415
    import sys                                                # noqa: PLC0415
    con = sqlite3.connect(sys.argv[1])
    con.row_factory = sqlite3.Row
    sys.stdout.buffer.write(build(con))


if __name__ == "__main__":
    _main()
