#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S227 PAD PROOF -- the upload receipt, as a printable PDF.

The owner, 06-Sep-2026: the stock checkers must get "a PDF printout to save as
proof of what the VPS ingested", and the uploaded Excel sheets must be preserved
"for any dispute resolution during the period of reconciliation of the stock
mismatch."

This module turns ONE uploaded sheet -- one count id, root or part -- into an A4
document a person can print or keep on the phone:

    · which count, which sheet of it, when (IST), who uploaded, who counted,
      who entered, the bill it was pinned to, the Marg stock it was read against
    · the file: its name, size and md5, and that the server KEPT it unchanged
    · what this sheet did: rows read · counted · agree · differ · sent back
    · every item recorded FROM THIS SHEET, with Marg's figure, the counted
      figure, strips / loose, and the difference
    · every row the server could NOT use, as written, and why
    · the whole count so far, after this sheet

Stdlib only. The same hand-rolled PDF writer as clinic_day_pdf.py (S224):
Helvetica core fonts, WinAnsi, uncompressed streams. The app runs under a venv
that has neither reportlab nor weasyprint, and a receipt is not the moment to
find out.

render(data) -> bytes. `data` is the dict stock_app._pad_receipt_data() builds;
nothing here touches the database.
"""
import datetime as dt

CLINIC = "Advanced Orthopaedic Surgery Centre"
STORE = "Medical store"

# ---------------------------------------------------------------- Helvetica widths (WinAnsi 32..126)
_W_REG = [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
          556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
          1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
          667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
          333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
          556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584]
_W_BOLD = [278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278,
           556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
           975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
           667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
           333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611,
           611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584]

_MAP = {u"—": "-", u"–": "-", u"₹": "Rs ", u"‘": "'", u"’": "'",
        u"“": '"', u"”": '"', u"…": "...", u" ": " ", u"·": "-"}


def _latin(s):
    """Core fonts are WinAnsi: fold the few typographic characters we use, replace the rest."""
    s = "" if s is None else str(s)
    for k, v in _MAP.items():
        s = s.replace(k, v)
    return s.encode("cp1252", "replace").decode("cp1252")


def _width(s, size, bold=False):
    tab = _W_BOLD if bold else _W_REG
    w = 0
    for ch in s:
        o = ord(ch)
        w += tab[o - 32] if 32 <= o <= 126 else 556
    return w * size / 1000.0


def _wrap(s, size, maxw, bold=False):
    words, lines, cur = _latin(s).split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if _width(t, size, bold) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fit(s, size, maxw, bold=False):
    s = _latin(s)
    if _width(s, size, bold) <= maxw:
        return s
    while s and _width(s + "...", size, bold) > maxw:
        s = s[:-1]
    return s + "..."


def _dmy(iso):
    """'2026-09-06' -> '06-09-2026'; anything else back as it came."""
    s = str(iso or "").strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return "%s-%s-%s" % (s[8:10], s[5:7], s[:4])
    return s


def _stamp(iso):
    """'2026-09-06T14:03:11' -> '06-09-2026 14:03'."""
    s = str(iso or "").strip()
    if len(s) >= 16 and s[10] in ("T", " "):
        return "%s %s" % (_dmy(s[:10]), s[11:16])
    return _dmy(s)


def _n(v):
    try:
        return "%d" % int(v)
    except Exception:                                         # noqa: BLE001
        return "-"


def _signed(v):
    try:
        v = int(v)
    except Exception:                                         # noqa: BLE001
        return "-"
    return "%+d" % v if v else "0"


# ---------------------------------------------------------------- the PDF writer
class _PDF(object):
    """A4 portrait, Helvetica, uncompressed streams. Points, origin bottom-left."""
    W, H = 595.28, 841.89

    def __init__(self, title, landscape=False):
        self.title = title
        self.pages = []
        self._cur = None
        if landscape:
            self.W, self.H = 841.89, 595.28

    def new_page(self):
        self._cur = []
        self.pages.append(self._cur)

    @staticmethod
    def _pdfstr(s):
        s = _latin(s)
        s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        s = "".join(ch if ch >= " " else " " for ch in s)
        return s.encode("cp1252", "replace")

    def text(self, x, y, s, size=9.5, bold=False, align="l", gray=0.0):
        s = _latin(s)
        if align == "r":
            x -= _width(s, size, bold)
        elif align == "c":
            x -= _width(s, size, bold) / 2.0
        self._cur.append(b"BT /%s %.1f Tf %.3f g %.2f %.2f Td (%s) Tj ET" % (
            b"F2" if bold else b"F1", size, gray, x, y, self._pdfstr(s)))

    def line(self, x1, y1, x2, y2, w=0.5, gray=0.0):
        self._cur.append(b"%.2f w %.3f G %.2f %.2f m %.2f %.2f l S" % (w, gray, x1, y1, x2, y2))

    def rect(self, x, y, w, h, gray=0.92):
        self._cur.append(b"%.3f g %.2f %.2f %.2f %.2f re f 0 g" % (gray, x, y, w, h))

    def build(self):
        objs = []

        def add(body):
            objs.append(body)
            return len(objs)
        cat = add(None)
        pages = add(None)
        f1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        f2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        kids = []
        for content in self.pages:
            stream = b"\n".join(content)
            c = add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
            p = add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] "
                    b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> /Contents %d 0 R >>"
                    % (pages, self.W, self.H, f1, f2, c))
            kids.append(p)
        objs[cat - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages
        objs[pages - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
            b" ".join(b"%d 0 R" % k for k in kids), len(kids))
        info = add(b"<< /Title (%s) /Producer (pad_receipt S227) /CreationDate (D:%s) >>" % (
            self._pdfstr(self.title), dt.datetime.now().strftime("%Y%m%d%H%M%S").encode()))
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offs = []
        for i, body in enumerate(objs, 1):
            offs.append(len(out))
            out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
        xref = len(out)
        out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
        for o in offs:
            out += b"%010d 00000 n \n" % o
        out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
            len(objs) + 1, cat, info, xref)
        return bytes(out)


# ---------------------------------------------------------------- the receipt, laid out on A4
_L, _R, _TOP, _BOT = 40.0, 555.28, 800.0, 50.0
_ROW = 12.5


class _Doc(object):
    def __init__(self, title, head_left, head_right):
        self.pdf = _PDF(title)
        self.head_left, self.head_right = head_left, head_right
        self.y = _TOP
        self.pdf.new_page()

    def _header(self):
        p = self.pdf
        p.text(_L, _TOP + 14, self.head_left, 9, gray=0.35)
        p.text(_R, _TOP + 14, self.head_right, 9, bold=True, align="r", gray=0.35)
        p.line(_L, _TOP + 9, _R, _TOP + 9, 0.4, 0.6)

    def need(self, h):
        if self.y - h < _BOT:
            self.pdf.new_page()
            self.y = _TOP
            self._header()
            return True
        return False

    def gap(self, h):
        self.y -= h

    def line_text(self, s, size=9.5, bold=False, gray=0.0, indent=0):
        self.need(size + 4)
        self.pdf.text(_L + indent, self.y - size, s, size, bold=bold, gray=gray)
        self.y -= size + 4

    def para(self, s, size=8.5, gray=0.3):
        for ln in _wrap(s, size, _R - _L):
            self.line_text(ln, size, gray=gray)

    def kv(self, k, v, kw=118):
        """One labelled line: label in grey, value in black, wrapped to the width."""
        size = 9.5
        lines = _wrap(v if v not in (None, "") else "-", size, _R - _L - kw) or ["-"]
        self.need((size + 4) * len(lines))
        self.pdf.text(_L, self.y - size, k, size, gray=0.4)
        for i, ln in enumerate(lines):
            if i:
                self.need(size + 4)
            self.pdf.text(_L + kw, self.y - size, ln, size, bold=(i == 0))
            self.y -= size + 4

    def heading(self, s):
        self.need(26)
        self.gap(8)
        self.pdf.text(_L, self.y - 11, s, 10.5, bold=True)
        self.y -= 16

    # -- a generic table: cols = [(label, x, align, width_for_fit)]
    def thead(self, title, cols, cont=False):
        p = self.pdf
        self.need(16 + _ROW + 4)
        self.gap(8)
        p.text(_L, self.y - 11, title + (" (continued)" if cont else ""), 10.5, bold=True)
        self.y -= 16
        p.rect(_L, self.y - _ROW + 3, _R - _L, _ROW, 0.92)
        yy = self.y - _ROW + 6
        for label, x, align, _w in cols:
            p.text(x, yy, label, 8, bold=True, align=align)
        self.y -= _ROW
        p.line(_L, self.y + 3, _R, self.y + 3, 0.5)

    def trow(self, title, cols, cells, bold=False, size=8.5):
        if self.need(_ROW + 2):
            self.thead(title, cols, cont=True)
        p = self.pdf
        yy = self.y - _ROW + 6
        for (label, x, align, w), val in zip(cols, cells):
            s = _latin(val)
            if w:
                s = _fit(s, size, w, bold)
            p.text(x, yy, s, size, bold=bold, align=align)
        self.y -= _ROW
        p.line(_L, self.y + 3, _R, self.y + 3, 0.25, 0.8)

    def finish(self, foot):
        n = len(self.pdf.pages)
        for i, page in enumerate(self.pdf.pages, 1):
            self.pdf._cur = page
            self.pdf.text(_R, 30, "Page %d of %d" % (i, n), 8, align="r", gray=0.45)
            self.pdf.text(_L, 30, _fit(foot, 8, _R - _L - 70), 8, gray=0.45)
        return self.pdf.build()


# the columns of the item table: # | Item | Pack | Marg | Counted | Strips | Loose | Diff
_ITEM_COLS = [("#", _L + 18, "r", 0), ("Item", _L + 24, "l", 236), ("Pack", _L + 300, "c", 44),
              ("Marg", _L + 350, "r", 0), ("Counted", _L + 405, "r", 0),
              ("Strips", _L + 445, "r", 0), ("Loose", _L + 482, "r", 0), ("Diff", _R, "r", 0)]
# the columns of the sent-back table: Row | Written | Figure | Why
_FIX_COLS = [("Row", _L + 22, "r", 0), ("As written on the sheet", _L + 30, "l", 190),
             ("Figure", _L + 262, "r", 0), ("Why it could not be used", _L + 272, "l", 240)]


def render(d):
    """d -- see stock_app._pad_receipt_data(). Returns the PDF bytes."""
    cid = d["count_id"]
    root = d.get("root_id") or cid
    sheet_no = d.get("sheet_no") or 1
    title = "Stock count #%d - sheet %d - upload receipt" % (root, sheet_no)
    doc = _Doc(title, "%s - %s - stock count upload receipt" % (CLINIC, STORE),
               "Count #%d - sheet %d" % (root, sheet_no))
    p = doc.pdf

    # ---- title block
    p.text(_L, doc.y - 16, CLINIC, 16, bold=True)
    doc.y -= 22
    p.text(_L, doc.y - 12, "%s - STOCK COUNT UPLOAD RECEIPT" % STORE.upper(), 12.5, bold=True, gray=0.15)
    doc.y -= 22
    p.line(_L, doc.y, _R, doc.y, 0.8)
    doc.y -= 8
    doc.line_text("Count #%d - sheet %d%s" % (root, sheet_no,
                  ("  (recorded as count #%d, part of #%d)" % (cid, root)) if cid != root else ""),
                  11, bold=True)
    doc.para("This is the server's own record of what it read from ONE uploaded sheet and what "
             "it recorded from it. Keep it: together with the sheet's md5 below it proves, "
             "later, exactly what was handed in and when.")
    doc.gap(4)

    # ---- who, when, against what
    doc.kv("Recorded at", "%s IST" % _stamp(d.get("recorded_at")))
    doc.kv("Uploaded by (login)", d.get("uploaded_by") or d.get("recorded_by") or "-")
    doc.kv("Counted by", d.get("counted_by") or "-")
    doc.kv("Entered by", d.get("entered_by") or "-")
    doc.kv("Last sale bill", "%s dated %s" % (d.get("bill_no") or "-", _dmy(d.get("bill_date"))))
    doc.kv("Marg stock as on", "%s%s" % (d.get("as_on") or "-",
                                          ("  (%s)" % d["as_on_note"]) if d.get("as_on_note") else ""))

    # ---- the file
    doc.heading("THE FILE THAT WAS UPLOADED")
    f = d.get("file") or {}
    doc.kv("File name", f.get("filename") or "-")
    doc.kv("Size", ("%s bytes" % _n(f.get("bytes"))) if f.get("bytes") else "-")
    doc.kv("md5 (fingerprint)", f.get("md5") or "-")
    doc.kv("Uploaded at", ("%s IST" % _stamp(f.get("uploaded_at"))) if f.get("uploaded_at") else "-")
    if f.get("kept"):
        doc.kv("Kept on the server", "YES - unchanged, as %s" % (f.get("kept_as") or "its md5 name"))
        doc.para("The server wrote the uploaded bytes to its archive and read them back: the md5 "
                 "matched. A copy of this sheet shown later can be checked against the md5 "
                 "above; if the fingerprints agree, it is the same file to the byte.")
    else:
        doc.kv("Kept on the server", "no copy of the file itself (uploaded before the archive existed)")
    doc.gap(2)

    # ---- what this sheet did
    doc.heading("WHAT THIS SHEET DID")
    t = d.get("this_sheet") or {}
    doc.line_text("%s rows with figures  -  %s items counted  -  %s agree with Marg  -  %s differ  -  %s row%s sent back to fix"
                  % (_n(t.get("rows")), _n(t.get("counted")), _n(t.get("agreed")), _n(t.get("differed")),
                     _n(t.get("to_fix")), "" if t.get("to_fix") == 1 else "s"), 9.5, bold=True)
    w = d.get("whole") or {}
    left = (w.get("not_counted") or 0) + (w.get("sent_back") or 0)
    doc.line_text("Whole count #%d after this sheet: %s of %s items counted, %s differ from Marg, "
                  "%s not yet counted, %s to fix%s." % (
                      root, _n(w.get("counted")), _n(w.get("items_in_shop")), _n(w.get("differed")),
                      _n(w.get("not_counted")), _n(w.get("sent_back")),
                      "  -  NOTHING LEFT" if left == 0 else ""), 9, gray=0.2)
    if w.get("closed"):
        c = w["closed"]
        doc.line_text("Count #%d is CLOSED - %s on %s IST%s." % (
            root, "completed" if c.get("how") == "complete" else "closed by the doctor as it stood",
            _stamp(c.get("at")), (" by " + c["by"]) if c.get("by") else ""), 9, gray=0.2)

    # ---- differences from this sheet, first -- they are what a dispute is about
    items = d.get("items") or []
    diffs = [it for it in items if (it.get("diff") or 0) != 0]
    if diffs:
        doc.thead("DIFFERENCES FROM THIS SHEET (%d)" % len(diffs), _ITEM_COLS)
        for i, it in enumerate(diffs, 1):
            doc.trow("DIFFERENCES FROM THIS SHEET", _ITEM_COLS,
                     [str(i), it.get("item") or "-", it.get("packing") or "-", _n(it.get("marg")),
                      _n(it.get("counted")), _n(it.get("strips")) if it.get("strips") is not None else "-",
                      _n(it.get("loose")) if it.get("loose") is not None else "-", _signed(it.get("diff"))],
                     bold=True)
    else:
        doc.gap(6)
        doc.line_text("No item on this sheet differs from Marg.", 9.5, bold=True)

    # ---- rows sent back
    fixes = d.get("fixes") or []
    if fixes:
        doc.thead("ROWS SENT BACK TO FIX (%d) - kept as written, not recorded as a count" % len(fixes), _FIX_COLS)
        for fx in fixes:
            doc.trow("ROWS SENT BACK TO FIX", _FIX_COLS,
                     [_n(fx.get("row")) if fx.get("row") else "-", fx.get("written") or "-",
                      _n(fx.get("figure")) if fx.get("figure") is not None else "-", fx.get("why") or "-"])

    # ---- every item recorded from this sheet
    if items:
        doc.thead("EVERY ITEM RECORDED FROM THIS SHEET (%d)" % len(items), _ITEM_COLS)
        for i, it in enumerate(items, 1):
            doc.trow("EVERY ITEM RECORDED FROM THIS SHEET", _ITEM_COLS,
                     [str(i), it.get("item") or "-", it.get("packing") or "-", _n(it.get("marg")),
                      _n(it.get("counted")), _n(it.get("strips")) if it.get("strips") is not None else "-",
                      _n(it.get("loose")) if it.get("loose") is not None else "-", _signed(it.get("diff"))],
                     bold=((it.get("diff") or 0) != 0))
        doc.need(_ROW + 2)
        p = doc.pdf
        p.rect(_L, doc.y - _ROW + 3, _R - _L, _ROW, 0.95)
        yy = doc.y - _ROW + 6
        p.text(_L + 24, yy, "%d items on this sheet - %d differ" % (len(items), len(diffs)), 8.5, bold=True)
        doc.y -= _ROW
    else:
        doc.gap(6)
        doc.line_text("No item was recorded from this sheet.", 9.5, bold=True)

    doc.gap(10)
    doc.para("Marg = the shop's own stock figure on the date above. Counted = what the sheet said, "
             "settled from STRIPS x pack size + LOOSE by the server. Diff = Counted - Marg; a minus "
             "is short on the shelf. A sealed count never changes: a later sheet that corrects an "
             "item is recorded as a new part of the same count, and this receipt stays as it was.")
    # the clinic's name is in the title and the running header; the foot must fit in one line
    return doc.finish("Count #%d sheet %d - md5 %s - PDF made %s IST" % (
        root, sheet_no, (f.get("md5") or "-"), dt.datetime.now().strftime("%d-%m-%Y %H:%M")))


# ---------------------------------------------------------------- S227 DIFF SHEET: the hand-fill sheet
# The owner, 06-Sep-2026: "the differences sheet to be shared with Darpan as a
# PDF so that he can fill his responses in that sheet by hand, and then someone
# will assist him to fill the same data in the Excel sheet." Landscape A4, a
# tall row per item with boxes for RECOUNT strips / loose, REASON (a number from
# the legend) and REMARKS. Same order and the same columns as the DIFFERENCES
# tab of the result workbook, so the typing-in is column for column.
_LL, _LR, _LTOP, _LBOT = 30.0, 811.89, 560.0, 40.0
_DROW = 21.0
# x positions: # | Item | Pack | Marg | Counted | Difference | At MRP | RECOUNT strips | loose | REASON | REMARKS
_DC = [("#", _LL + 16, "r", 0), ("Item", _LL + 22, "l", 168), ("Pack", _LL + 220, "c", 40),
       ("Marg", _LL + 285, "r", 0), ("Counted", _LL + 345, "r", 0), ("Difference", _LL + 435, "r", 0),
       ("At MRP", _LL + 505, "r", 0), ("RECOUNT strips", _LL + 552, "c", 0), ("loose", _LL + 602, "c", 0),
       ("REASON", _LL + 648, "c", 0), ("REMARKS", _LL + 680, "l", 0)]
_DBOX = [(_LL + 528, 46), (_LL + 578, 46), (_LL + 630, 38), (_LL + 674, _LR - _LL - 676)]   # x, width of the four hand-fill boxes


def _units(n, ps):
    """Compact strips-and-tablets for a narrow column: '25s 4t', '62 pc'; a
    shortage carries the sign in the word, never a minus on a strip."""
    try:
        n = int(n); ps = int(ps or 1)
    except Exception:                                         # noqa: BLE001
        return "-"
    if n < 0:
        return "short " + _units(-n, ps)
    if ps <= 1:
        return "%d pc" % n
    s, t = divmod(n, ps)
    bits = []
    if s:
        bits.append("%ds" % s)
    if t:
        bits.append("%dt" % t)
    return " ".join(bits) or "0"


def _rs(p_):
    if p_ is None:
        return "-"
    n = abs(int(p_)); whole, paise = divmod(n, 100); s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]; parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return ("-" if int(p_) < 0 else "") + "Rs %s" % s + ("" if paise == 0 else ".%02d" % paise)


class _LDoc(object):
    """The landscape page with its running header, the table head repeated."""
    def __init__(self, title, head_right):
        self.pdf = _PDF(title, landscape=True)
        self.head_right = head_right
        self.y = _LTOP
        self.pdf.new_page()

    def _header(self):
        p = self.pdf
        p.text(_LL, _LTOP + 14, "%s - %s - DIFFERENCES TO CHECK" % (CLINIC, STORE), 9, gray=0.35)
        p.text(_LR, _LTOP + 14, self.head_right, 9, bold=True, align="r", gray=0.35)
        p.line(_LL, _LTOP + 9, _LR, _LTOP + 9, 0.4, 0.6)

    def need(self, h):
        if self.y - h < _LBOT:
            self.pdf.new_page()
            self.y = _LTOP
            self._header()
            return True
        return False

    def line_text(self, s, size=9.5, bold=False, gray=0.0, x=None):
        self.need(size + 4)
        self.pdf.text(x if x is not None else _LL, self.y - size, s, size, bold=bold, gray=gray)
        self.y -= size + 4

    def para(self, s, size=8.5, gray=0.3):
        for ln in _wrap(s, size, _LR - _LL):
            self.line_text(ln, size, gray=gray)

    def thead(self, cont=False):
        p = self.pdf
        self.need(_DROW + 18)
        self.y -= 6
        if cont:
            p.text(_LL, self.y - 9, "DIFFERENCES (continued)", 9, bold=True)
            self.y -= 13
        p.rect(_LL, self.y - 14 + 3, _LR - _LL, 14, 0.9)
        yy = self.y - 14 + 6
        for label, x, align, _w in _DC:
            p.text(x, yy, label, 7.5, bold=True, align=align)
        self.y -= 14
        p.line(_LL, self.y + 3, _LR, self.y + 3, 0.6)

    def trow(self, i, r):
        if self.need(_DROW + 2):
            self.thead(cont=True)
        p = self.pdf
        yy = self.y - _DROW + 8
        d = r["diff"]
        bold = (r.get("mrp_p") or 0) != 0 and abs(r["mrp_p"]) >= 100000     # Rs 1,000 and above stands out
        vals = [str(i), r["item"], r.get("packing") or "-", _units(r["marg"], r["pack"]),
                _units(r["counted"], r["pack"]), _units(d, r["pack"]),
                (_rs(r["mrp_p"]) + (" (p)" if r.get("mrp_source") == "provisional" else "")) if r.get("mrp_p") is not None else "no MRP"]
        for (label, x, align, w), v in zip(_DC[:7], vals):
            s = _fit(v, 8.5, w) if w else _latin(v)
            p.text(x, yy, s, 8.5, bold=(bold and label in ("Item", "Difference", "At MRP")), align=align,
                   gray=(0.45 if (label == "At MRP" and r.get("mrp_p") is None) else 0.0))
        # the four hand-fill boxes: CLOSED frames a pen can find, a hair inside the row
        top, bot = self.y + 1.0, self.y - _DROW + 4.5
        for bx, bw in _DBOX:
            x1, x2 = bx + 1.5, bx + bw - 1.5
            p.line(x1, bot, x2, bot, 0.7, 0.45)
            p.line(x1, top, x2, top, 0.7, 0.45)
            p.line(x1, bot, x1, top, 0.7, 0.45)
            p.line(x2, bot, x2, top, 0.7, 0.45)
        a = r.get("answer")
        if a:
            # a reason already on record is printed faintly inside its box, so the pen does not repeat it
            p.text(_DBOX[3][0] + 4, yy, _fit("on record: %s%s" % (a.get("label") or a.get("reason") or "",
                                                               (" - " + a["note"]) if a.get("note") else ""),
                                         6.5, _DBOX[3][1] - 8), 6.5, gray=0.45)
        self.y -= _DROW
        p.line(_LL, self.y + 3, _LR, self.y + 3, 0.3, 0.8)

    def finish(self, foot):
        n = len(self.pdf.pages)
        for i, page in enumerate(self.pdf.pages, 1):
            self.pdf._cur = page
            self.pdf.text(_LR, 24, "Page %d of %d" % (i, n), 8, align="r", gray=0.45)
            self.pdf.text(_LL, 24, _fit(foot, 8, _LR - _LL - 70), 8, gray=0.45)
        return self.pdf.build()


def render_diffs(d):
    """d -- see stock_app._pad_diffs_data(). Returns the PDF bytes."""
    cid = d["count_id"]
    doc = _LDoc("Stock count #%d - differences to check" % cid,
                "Count #%d - %s" % (cid, d.get("day") or ""))
    p = doc.pdf
    p.text(_LL, doc.y - 15, "%s - %s" % (CLINIC, STORE), 14, bold=True)
    p.text(_LR, doc.y - 15, "STOCK COUNT #%d - DIFFERENCES TO CHECK" % cid, 12, bold=True, align="r", gray=0.15)
    doc.y -= 22
    p.line(_LL, doc.y, _LR, doc.y, 0.8)
    doc.y -= 6
    doc.line_text("Counted %s by %s, entered by %s - after bill %s dated %s - against Marg stock as on %s%s"
                  % (d.get("when") or "-", d.get("counted_by") or "-", d.get("entered_by") or "-",
                     d.get("bill_no") or "-", _dmy(d.get("bill_date")), d.get("as_on") or "-",
                     (" - %d sheets" % d["sheets"]) if (d.get("sheets") or 1) > 1 else ""), 9, gray=0.2)
    mm = d.get("mismatch") or {}
    doc.line_text("%d items counted of %d - %d agree - %d DIFFER - %d not counted - %d to fix%s"
                  % (d.get("counted") or 0, d.get("items_in_shop") or 0, d.get("agreed") or 0,
                     d.get("differed") or 0, d.get("not_counted") or 0, d.get("sent_back") or 0,
                     ("  -  %d reason%s already on record" % (d["explained"], "" if d["explained"] == 1 else "s"))
                     if d.get("explained") else ""), 9.5, bold=True)
    if mm:
        doc.line_text("VALUE OF THE MISMATCH AT MRP:  short %s (%d lines)  -  over %s (%d lines)  -  net %s  -  %d of %d lines have no MRP on record"
                      % (_rs(mm["mrp_short_p"]), mm["short_lines"], _rs(mm["mrp_over_p"]), mm["over_lines"],
                         _rs(mm["mrp_net_p"]), mm["mrp_unpriced"], mm["lines"]), 9.5, bold=True)
        doc.line_text("At cost (last purchase rate), for reference: short %s, over %s, %d lines without a rate."
                      % (_rs(mm["cost_short_p"]), _rs(mm["cost_over_p"]), mm["cost_unpriced"]), 8.5, gray=0.35)
    doc.y -= 2
    doc.para("HOW TO FILL THIS SHEET: go to the shelf for each item and count it again. Write the new count in "
             "RECOUNT (strips and loose) only if it is different from what was counted before. Write the REASON as "
             "a number from the legend. Write anything else in REMARKS. Then this sheet is typed into the "
             "DIFFERENCES tab of the Excel result sheet, column for column, and uploaded at step 3 -- the count "
             "already recorded never changes; a recount joins it as the next sheet.", 8.5, 0.25)
    doc.line_text("REASON legend:  " + "   ".join("%d = %s" % (n, en) for n, en, _hi in d.get("reasons") or []),
                  8.5, bold=True, gray=0.15)
    doc.line_text("Marg = the computer's stock. Counted = the shelf. Difference = counted minus Marg; "
                  "'short' = less on the shelf than the computer says. 25s 4t = 25 strips and 4 tablets; pc = pieces. "
                  "Lines at Rs 1,000 or more at MRP are in bold.", 8, gray=0.4)
    doc.line_text("(p) = a provisional price, from the last purchase rate: the item has not sold here, so it has no selling price of its own.", 8, gray=0.4)
    doc.thead()
    for i, r in enumerate(d.get("rows") or [], 1):
        doc.trow(i, r)
    doc.need(_DROW + 4)
    p = doc.pdf
    p.rect(_LL, doc.y - 14 + 3, _LR - _LL, 14, 0.94)
    p.text(_LL + 22, doc.y - 14 + 6, "%d differences - short at MRP %s - over at MRP %s" % (
        len(d.get("rows") or []), _rs(mm.get("mrp_short_p", 0)), _rs(mm.get("mrp_over_p", 0))), 8.5, bold=True)
    doc.y -= 14
    doc.y -= 8
    doc.line_text("Counted again by: ______________________    Date: ____________    Typed into the Excel by: ______________________",
                  9, gray=0.2)
    return doc.finish("Count #%d - differences to check - PDF made %s IST" % (
        cid, dt.datetime.now().strftime("%d-%m-%Y %H:%M")))


if __name__ == "__main__":                                   # a shape check, nothing more
    import sys
    demo = dict(count_id=7, root_id=5, sheet_no=2, recorded_at="2026-09-06T14:03:11",
                uploaded_by="amir", counted_by="Darpan", entered_by="Amir", bill_no="A003425",
                bill_date="2026-09-06", as_on="06-09-2026",
                file=dict(filename="STOCK_COUNT_06-09-2026_SHEET_2_REMAINING.xlsx", bytes=41233,
                          md5="0123456789abcdef0123456789abcdef", uploaded_at="2026-09-06T14:03:10",
                          kept=True, kept_as="0123456789abcdef0123456789abcdef.xlsx"),
                this_sheet=dict(rows=40, counted=38, agreed=30, differed=8, to_fix=2),
                whole=dict(counted=300, items_in_shop=333, differed=12, not_counted=33, sent_back=2, closed=None),
                items=[dict(item="ITEM %03d TAB 10" % i, packing="1*10", marg=40, counted=40 - (i % 5),
                            strips=4, loose=0, diff=-(i % 5)) for i in range(1, 39)],
                fixes=[dict(row=57, written="LACTOVAX SYP 200 ML.", figure=7,
                            why="this name is not in the shop list -- correct it"),
                       dict(row=61, written="-3", figure=None, why="a negative count")])
    out = render(demo)
    sys.stdout.write("%d bytes, %d pages\n" % (len(out), out.count(b"/Type /Page ")))
