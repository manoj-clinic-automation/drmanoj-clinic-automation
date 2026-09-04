#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clinic_day_pdf.py -- S224: the day's revenue as a real PDF file, and a page that hands it to
WhatsApp from the owner's phone.

THE OWNER (04-Sep-2026): "give me option to share PDF of Day Revenue from my Android phone
through my WhatsApp."

WHAT IT IS. The S223 Day Revenue screen (finance_clinic_day.py) is a page that PRINTS; a phone
cannot hand a printed page to WhatsApp. This module renders the SAME day -- the same row, the
same lines, the same split legs, in the same sections and the same order -- into a PDF file the
phone's share sheet can carry. The A4 page itself is not touched (its live pin was never read
back; nothing pending is patched).

WHERE THE FIGURES COME FROM. The three SELECTs are copied verbatim from finance_clinic_day.py as
built at S223_DAY_PAGE_EDITS (md5 dceb79a06e71f7e35150c69e1f5dd175): the day row (line 166),
the lines (line 174, ORDER BY section, sn), the split legs (line 200). Sections, their order,
the shift order and the people count are the same code (lines 52-63, 246). D367 stands: the
sheet's own SUMMARY / Cash / Online figures are read from nowhere and shown nowhere.

THE PDF WRITER is here, in about a hundred lines, and needs nothing installed: gunicorn runs this
app under /usr/bin/python3, which has no reportlab and no weasyprint. Helvetica core fonts, text,
rules and a table -- no images, no compression (so the text can be searched, and tested).
The rupee sign is not in the core fonts, so amounts read "Rs 1,23,456" in Indian grouping.

WHO. `require("checker", unit="clinic")` -- the doctors. A maker sees the A4 page; the file that
leaves the building through a phone is the checker's to send.

READ-ONLY. Every route here is a SELECT. This module writes nothing, anywhere, ever.

ROUTES (all under the clinic gate, /finance/clinic/...):
    GET /finance/clinic/day/<yyyy-mm-dd>/pdf     the PDF (inline; ?dl=1 -> attachment)
    GET /finance/clinic/day/<yyyy-mm-dd>.pdf     the same file, by its filename
    GET /finance/clinic/day/<yyyy-mm-dd>/share   the phone page: Share on WhatsApp / Download
    GET /finance/clinic/share[?d=yyyy-mm-dd]     -> that day's share page; no d = yesterday
"""
import datetime as dt
import json
import urllib.parse

from flask import Blueprint, Response, redirect, request

bp = Blueprint("clinic_day_pdf", __name__)
_db = None
_require = None
_unit = "clinic"
TABLE = "clinic_day_revenue"
LINES = "clinic_day_line"
TENDERS = "clinic_day_tender"
CLINIC = "Advanced Orthopaedic Surgery Centre"

# finance_clinic_day.py (S223_DAY_PAGE_EDITS) lines 52-63, verbatim.
SECTIONS = [
    ("consult", "PAID CONSULTATIONS"),
    ("xray", "X-RAY"),
    ("proc", "PROCEDURES"),
    ("revisit", "FREE REVISITS"),
    ("concession", "FREE / CONCESSION CASES"),
]
_SHIFT_ORDER = {"morning": 0, "evening": 1}
KNOWN = [("Cash", "cash"), ("Online Payment", "online"), ("Debit Card", "card"),
         ("Credit Card", "card"), ("Net Banking", "online"), ("Patient APP", "online"),
         ("Wallet", "online"), ("Split Payment", "split")]


def init(app, db_getter, require_fn, unit="clinic", url_prefix=""):
    """Mount at IMPORT time, like every other module in this app."""
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ----------------------------------------------------------------- the data (S223's queries)

def _valid(date):
    try:
        return dt.date(int(date[:4]), int(date[5:7]), int(date[8:10])).isoformat() == date
    except (ValueError, IndexError, TypeError):
        return False


def _table_exists(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                       (name,)).fetchone() is not None


def _tender(row):
    """finance_clinic_day._tender, verbatim (line 94)."""
    out = {"cash": 0, "online": 0, "card": 0, "split": 0, "other": []}
    try:
        raw = json.loads(row["tender_json"] or "{}")
    except (ValueError, TypeError):
        return out
    known = {k: v for k, v in KNOWN}
    for label, p in sorted(raw.items()):
        b = known.get(label.strip())
        if b:
            out[b] += int(p)
        else:
            out["other"].append((label, int(p)))
    return out


def _people(lines):
    """finance_clinic_day._people, verbatim (line 246)."""
    seen, anon = set(), 0
    for l in lines:
        cid = (l["clinic_id"] or "").strip()
        if cid:
            seen.add(cid)
        else:
            anon += 1
    return len(seen) + anon


def day_data(con, date):
    """Everything the A4 day page shows, as plain Python. None when no day is stored."""
    if not _table_exists(con, TABLE):
        return None
    day = con.execute("SELECT * FROM %s WHERE business_date=?" % TABLE, (date,)).fetchone()
    if day is None:
        return None
    lines = []
    if _table_exists(con, LINES):
        lines = list(con.execute(
            "SELECT * FROM clinic_day_line WHERE business_date=? ORDER BY section, sn", (date,)))
    by = {}
    for l in lines:
        by.setdefault(l["section"], []).append(l)
    sections = []
    for key, title in SECTIONS:
        rows = sorted(by.get(key, []),
                      key=lambda l: (_SHIFT_ORDER.get((l["shift"] or "").strip().lower(), 9),
                                     l["sn"]))
        if rows:
            sections.append((title, rows))
    splits = []
    if _table_exists(con, TENDERS):
        try:
            splits = list(con.execute(
                "SELECT clinic_id, invoice_no, tender, amount_p FROM clinic_day_tender "
                "WHERE business_date=? ORDER BY clinic_id, invoice_no, tender", (date,)))
        except Exception:                   # noqa: BLE001
            splits = []
    sby = {}
    for r in splits:
        sby.setdefault((r["clinic_id"], r["invoice_no"]), []).append((r["tender"], r["amount_p"]))
    return {"day": day, "lines": lines, "sections": sections, "people": _people(lines),
            "tender": _tender(day), "splits": sorted(sby.items())}


def _latest(con):
    if not _table_exists(con, TABLE):
        return None
    r = con.execute("SELECT MAX(business_date) d FROM %s" % TABLE).fetchone()
    return r["d"] if r else None


# ----------------------------------------------------------------- text helpers

def _inr(p):
    """Paise -> 'Rs 1,23,456' in Indian grouping. None -> '-'."""
    if p is None:
        return "-"
    n = int(round(p / 100.0))
    neg = n < 0
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + s


def _human(iso):
    try:
        return dt.date(int(iso[:4]), int(iso[5:7]), int(iso[8:10])).strftime("%d-%b-%Y")
    except (ValueError, TypeError, IndexError):
        return iso or "-"


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _summary_line(d):
    """One line of numbers for a WhatsApp text -- no name, no ID, no number of anyone's."""
    day = d["day"]
    return ("Day Revenue %s: Rs %s collected, %d billed entries, %d people seen. "
            "Consult Rs %s (%d), X-ray Rs %s (%d), Proc Rs %s (%d)." % (
                _human(day["business_date"]), _inr(day["total_amount_p"]), day["total_count"],
                d["people"], _inr(day["cons_amount_p"]), day["cons_count"],
                _inr(day["xray_amount_p"]), day["xray_count"],
                _inr(day["proc_amount_p"]), day["proc_count"]))


# ----------------------------------------------------------------- a small PDF writer

# Helvetica / Helvetica-Bold advance widths for chars 32..126 (Adobe core-14 AFM), /1000 em.
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

_MAP = {u"\u2014": "-", u"\u2013": "-", u"\u20b9": "Rs ", u"\u2018": "'", u"\u2019": "'",
        u"\u201c": '"', u"\u201d": '"', u"\u2026": "...", u"\u00a0": " "}


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
    """Greedy word wrap for the foot notes."""
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
    if _width(s, size, bold) <= maxw:
        return s
    while s and _width(s + "...", size, bold) > maxw:
        s = s[:-1]
    return s + "..."


class _PDF(object):
    """A4 portrait, Helvetica, uncompressed streams. Coordinates in points, origin bottom-left."""
    W, H = 595.28, 841.89

    def __init__(self, title):
        self.title = title
        self.pages = []
        self._cur = None

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
        objs = []                                     # 1-based, in order

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
        info = add(b"<< /Title (%s) /Producer (clinic_day_pdf S224) /CreationDate (D:%s) >>" % (
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


# ----------------------------------------------------------------- the day, laid out on A4

_L, _R, _TOP, _BOT = 40.0, 555.28, 800.0, 50.0
_ROW = 13.0
# x positions of the six columns: # | Patient | Clinic ID | Amount | Mode | Shift
_COL = {"sn": 52, "pat": 62, "pat_w": 205, "cid": 315, "amt": 395, "mode": 462, "sh": 536}


class _Doc(object):
    def __init__(self, title, date_h, who):
        self.pdf = _PDF(title)
        self.date_h, self.who = date_h, who
        self.y = _TOP
        self.pdf.new_page()
        self._pageno = 1

    def _header(self):
        p = self.pdf
        p.text(_L, _TOP + 14, CLINIC + " - Day Revenue", 9, gray=0.35)
        p.text(_R, _TOP + 14, self.date_h, 9, bold=True, align="r", gray=0.35)
        p.line(_L, _TOP + 9, _R, _TOP + 9, 0.4, 0.6)

    def need(self, h):
        if self.y - h < _BOT:
            self.pdf.new_page()
            self._pageno += 1
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

    def table_head(self, title, cont=False):
        p = self.pdf
        h = 16 + _ROW + 4
        self.need(h)
        self.gap(8)
        p.text(_L, self.y - 11, title + (" (continued)" if cont else ""), 10.5, bold=True)
        self.y -= 16
        p.rect(_L, self.y - _ROW + 3, _R - _L, _ROW, 0.92)
        yy = self.y - _ROW + 6.5
        p.text(_COL["sn"], yy, "#", 8.5, bold=True, align="r")
        p.text(_COL["pat"], yy, "Patient", 8.5, bold=True)
        p.text(_COL["cid"], yy, "Clinic ID", 8.5, bold=True, align="c")
        p.text(_COL["amt"], yy, "Amount", 8.5, bold=True, align="r")
        p.text(_COL["mode"], yy, "Mode", 8.5, bold=True, align="c")
        p.text(_COL["sh"], yy, "Shift", 8.5, bold=True, align="c")
        self.y -= _ROW
        p.line(_L, self.y + 3, _R, self.y + 3, 0.5)

    def table_row(self, i, l, title):
        if self.need(_ROW + 2):
            self.table_head(title, cont=True)
        p = self.pdf
        yy = self.y - _ROW + 6.5
        p.text(_COL["sn"], yy, str(i), 9, align="r")
        p.text(_COL["pat"], yy, _fit(_latin(l["patient"]) or "-", 9, _COL["pat_w"]), 9)
        p.text(_COL["cid"], yy, _latin(l["clinic_id"]) or "-", 9, align="c")
        p.text(_COL["amt"], yy, _inr(l["amount_p"]), 9, align="r")
        p.text(_COL["mode"], yy, _fit(_latin(l["mode"]) or "-", 8.5, 98), 8.5, align="c")
        p.text(_COL["sh"], yy, _latin(l["shift"]) or "-", 8.5, align="c")
        self.y -= _ROW
        p.line(_L, self.y + 3, _R, self.y + 3, 0.25, 0.75)

    def table_foot(self, n, tot_p):
        self.need(_ROW + 2)
        p = self.pdf
        p.rect(_L, self.y - _ROW + 3, _R - _L, _ROW, 0.95)
        yy = self.y - _ROW + 6.5
        p.text(_COL["pat"], yy, "Subtotal", 9, bold=True)
        p.text(_COL["cid"], yy, "%d" % n, 9, bold=True, align="c")
        p.text(_COL["amt"], yy, "Rs " + _inr(tot_p), 9, bold=True, align="r")
        self.y -= _ROW
        p.line(_L, self.y + 3, _R, self.y + 3, 0.5)

    def finish(self):
        n = len(self.pdf.pages)
        for i, page in enumerate(self.pdf.pages, 1):
            self.pdf._cur = page
            self.pdf.text(_R, 30, "Page %d of %d" % (i, n), 8, align="r", gray=0.45)
            self.pdf.text(_L, 30, "%s - Day Revenue %s - PDF made %s by %s" % (
                CLINIC, self.date_h, dt.datetime.now().strftime("%d-%b-%Y %H:%M"), self.who),
                8, gray=0.45)
        return self.pdf.build()


def render_pdf(d, who=""):
    """The day page, as A4. Same content, same order, same words, as finance_clinic_day."""
    day = d["day"]
    date_h = _human(day["business_date"])
    doc = _Doc("Day Revenue %s" % date_h, date_h, who)
    p = doc.pdf
    # the title block, as the page's header card
    p.text(_L, doc.y - 16, CLINIC, 16, bold=True)
    doc.y -= 22
    p.text(_L, doc.y - 12, "Day Revenue - %s" % date_h, 12.5, bold=True, gray=0.15)
    doc.y -= 22
    p.line(_L, doc.y, _R, doc.y, 0.8)
    doc.y -= 6
    doc.line_text("Rs %s collected  -  %d billed entries  -  %s morning  -  %s evening" % (
        _inr(day["total_amount_p"]), day["total_count"],
        day["morning"] if day["morning"] is not None else "-",
        day["evening"] if day["evening"] is not None else "-"), 11, bold=True)
    doc.line_text("%d people seen - %d billed, %d free revisits, %d free / concession."
                  % (d["people"], day["total_count"], day["free_revisits"], day["free_concession"]),
                  9, bold=True, gray=0.2)
    doc.line_text("A person billed for both a consultation and an X-ray is TWO entries and ONE person.",
                  8.5, gray=0.35)
    doc.gap(4)
    # the three heads, as the month page's card shows them for the day
    for label, cnt, amt in (("Consultations", day["cons_count"], day["cons_amount_p"]),
                            ("X-ray", day["xray_count"], day["xray_amount_p"]),
                            ("Procedures", day["proc_count"], day["proc_amount_p"])):
        doc.need(_ROW)
        yy = doc.y - 9.5
        p.text(_L, yy, label, 9.5)
        p.text(_L + 140, yy, "%d" % cnt, 9.5, align="r")
        p.text(_L + 230, yy, "Rs " + _inr(amt), 9.5, align="r")
        p.line(_L, doc.y - 12.5, _L + 232, doc.y - 12.5, 0.25, 0.8)
        doc.y -= _ROW
    t = d["tender"]
    bits = []
    for label, key in (("Cash", "cash"), ("Online", "online"), ("Card", "card"), ("Split", "split")):
        if t[key]:
            bits.append("%s Rs %s" % (label, _inr(t[key])))
    for label, pp in t["other"]:
        bits.append("%s Rs %s" % (label, _inr(pp)))
    doc.gap(4)
    doc.line_text("Paid as:  " + ("  -  ".join(bits) or "-"), 9.5)

    if not d["lines"]:
        doc.gap(6)
        doc.line_text("No entries were stored for this day. The day's totals above were read "
                      "before the per-entry table existed - re-run the reader with --all.", 9, gray=0.3)
    for title, rows in d["sections"]:
        doc.table_head(title)
        tot = 0
        for i, l in enumerate(rows, 1):
            tot += l["amount_p"] or 0
            doc.table_row(i, l, title)
        doc.table_foot(len(rows), tot)

    if d["splits"]:
        doc.need(16 + _ROW * 2)
        doc.gap(8)
        p.text(_L, doc.y - 11, "SPLIT PAYMENTS - how each was actually paid", 10.5, bold=True)
        doc.y -= 16
        p.rect(_L, doc.y - _ROW + 3, _R - _L, _ROW, 0.92)
        yy = doc.y - _ROW + 6.5
        p.text(_L + 40, yy, "Clinic ID", 8.5, bold=True, align="c")
        p.text(_L + 110, yy, "Invoice", 8.5, bold=True, align="c")
        p.text(_L + 150, yy, "Paid as", 8.5, bold=True)
        p.text(_R, yy, "Bill", 8.5, bold=True, align="r")
        doc.y -= _ROW
        p.line(_L, doc.y + 3, _R, doc.y + 3, 0.5)
        grand = 0
        for (cid, inv), legs in d["splits"]:
            doc.need(_ROW + 2)
            tot = sum(pp for _, pp in legs)
            grand += tot
            yy = doc.y - _ROW + 6.5
            p.text(_L + 40, yy, _latin(cid) or "-", 9, align="c")
            p.text(_L + 110, yy, _latin(inv) or "-", 9, align="c")
            p.text(_L + 150, yy, _fit("  +  ".join("%s Rs %s" % (_latin(tn), _inr(pp)) for tn, pp in legs),
                                      9, _R - _L - 220), 9)
            p.text(_R, yy, _inr(tot), 9, align="r")
            doc.y -= _ROW
            p.line(_L, doc.y + 3, _R, doc.y + 3, 0.25, 0.75)
        doc.need(_ROW + 2)
        yy = doc.y - _ROW + 6.5
        p.text(_L + 110, yy, "%d bill%s" % (len(d["splits"]), "" if len(d["splits"]) == 1 else "s"),
               9, bold=True, align="c")
        p.text(_R, yy, "Rs " + _inr(grand), 9, bold=True, align="r")
        doc.y -= _ROW

    doc.gap(10)
    for ln in _wrap("Every figure on this sheet is computed from the itemised lines of the day's own "
                    "Docterz sheet, never from its summary block - Dr Manoj's ruling of 04-Sep-2026. "
                    "A Split figure is a bill paid by more than one method; the breakdown is on the bill.",
                    8, _R - _L):
        doc.line_text(ln, 8, gray=0.35)
    return doc.finish()


# ----------------------------------------------------------------- routes

def _refuse():
    """Same words as the A4 page, so the refusal is recognisable; no figure anywhere in it."""
    return _page("Clinic - Day Revenue", """<div class="card"><h2>Not permitted</h2>
      <p>This sends the clinic's daily takings out through a phone. Your login is not a clinic
      checker, so it is not open to you. If that is wrong, ask Dr Manoj.</p></div>""")


@bp.route("/finance/clinic/day/<date>/pdf")
@bp.route("/finance/clinic/day/<date>.pdf")
def clinic_day_pdf(date):
    u, err = _require("checker", unit=_unit)
    if err:
        return err
    if not _valid(date):
        return Response("Not a date.", status=404, mimetype="text/plain")
    d = day_data(_db(), date)
    if d is None:
        return Response("No day was read for %s." % date, status=404, mimetype="text/plain")
    body = render_pdf(d, who=u.get("user", ""))
    fname = "Docterz_Revenue_%s.pdf" % date
    disp = "attachment" if (request.args.get("dl") or "") == "1" else "inline"
    return Response(body, mimetype="application/pdf", headers={
        "Content-Disposition": '%s; filename="%s"' % (disp, fname),
        "Content-Length": str(len(body)),
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff"})


@bp.route("/finance/clinic/share")
def clinic_share_today():
    """One bookmark for every day: no date -> yesterday's share page."""
    d = (request.args.get("d") or "").strip()
    if not _valid(d):
        d = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    return redirect("/finance/clinic/day/%s/share" % d, code=302)


@bp.route("/finance/clinic/day/<date>/share")
def clinic_day_share(date):
    u, err = _require("checker", unit=_unit)
    if err:
        return _refuse(), 403
    if not _valid(date):
        return _page("Clinic - Day Revenue", '<div class="card"><h2>Not a date.</h2>%s</div>'
                     % _picker(None)), 404
    con = _db()
    d = day_data(con, date)
    if d is None:
        latest = _latest(con)
        hint = ('<p>The newest day stored is <a href="/finance/clinic/day/%s/share">%s</a>.</p>'
                % (latest, _human(latest))) if latest else "<p>No day has been read yet.</p>"
        return _page("Day Revenue - %s" % _human(date), """
          <div class="card"><h2>%s</h2>
          <p>No day was read for this date. It may be a day the clinic was closed, or a day whose
          sheet has not reached Drive yet. Nothing is hidden.</p>%s%s</div>""" % (
            _human(date), hint, _picker(date)))
    day = d["day"]
    pdf_path = "/finance/clinic/day/%s/pdf" % date
    fname = "Docterz_Revenue_%s.pdf" % date
    summary = _summary_line(d)
    abs_pdf = _absolute(pdf_path)
    wa = "https://wa.me/?text=" + urllib.parse.quote(summary + "\n" + abs_pdf, safe="")
    body = """
      <div class="card">
        <div class="hd">%s</div>
        <div class="big">Rs %s</div>
        <div class="sub">%d billed entries - %d people seen - %s morning - %s evening</div>
        <table class="mini">
          <tr><td>Consultations</td><td class="n">%d</td><td class="r">Rs %s</td></tr>
          <tr><td>X-ray</td><td class="n">%d</td><td class="r">Rs %s</td></tr>
          <tr><td>Procedures</td><td class="n">%d</td><td class="r">Rs %s</td></tr>
        </table>
      </div>
      <div class="card">
        <button id="share" class="btn primary" type="button">Share PDF on WhatsApp</button>
        <a id="dl" class="btn" href="%s?dl=1" download="%s">Download PDF</a>
        <div id="status" class="status">Preparing the PDF&hellip;</div>
        <div id="fallback" class="fallback" hidden>
          <p>This browser cannot hand a file to another app. Two ways that always work:</p>
          <p>1. <b>Download PDF</b> above, then in WhatsApp tap the paper-clip and choose the file
          <code>%s</code> from Downloads.</p>
          <p>2. <a class="btn" href="%s">Send the numbers on WhatsApp</a> (a one-line text, no file).</p>
        </div>
      </div>
      %s
      <p class="foot">The PDF is the same day sheet as <a href="/finance/clinic/day/%s">the A4 page</a>:
      every entry, section by section, from the day's own Docterz lines. Signed in as <b>%s</b>.</p>
      <script>
      (function(){
        var PDF_URL=%s, FNAME=%s, TITLE=%s, TEXT=%s;
        var st=document.getElementById('status'), fb=document.getElementById('fallback'),
            btn=document.getElementById('share');
        var blobP=fetch(PDF_URL,{credentials:'same-origin',cache:'no-store'}).then(function(r){
          if(!r.ok) throw new Error('HTTP '+r.status); return r.blob();});
        blobP.then(function(b){ st.textContent='PDF ready ('+Math.round(b.size/1024)+' KB).'; },
                   function(e){ st.textContent='Could not fetch the PDF: '+e.message; });
        var canFiles = !!(window.File && navigator.share && navigator.canShare);
        if(!canFiles){ fb.hidden=false; }
        btn.addEventListener('click', function(){
          st.textContent='Opening the share sheet\u2026';
          blobP.then(function(b){
            var f=new File([b], FNAME, {type:'application/pdf'});
            if(!(navigator.canShare && navigator.canShare({files:[f]}))) throw new Error('nofiles');
            return navigator.share({files:[f], title:TITLE, text:TEXT});
          }).then(function(){ st.textContent='Shared.'; }).catch(function(e){
            if(e && e.name==='AbortError'){ st.textContent='Cancelled.'; return; }
            fb.hidden=false;
            st.textContent='This browser cannot share the file directly. Use Download PDF, or send the numbers.';
          });
        });
      })();
      </script>""" % (
        _human(day["business_date"]), _inr(day["total_amount_p"]), day["total_count"], d["people"],
        day["morning"] if day["morning"] is not None else "-",
        day["evening"] if day["evening"] is not None else "-",
        day["cons_count"], _inr(day["cons_amount_p"]), day["xray_count"], _inr(day["xray_amount_p"]),
        day["proc_count"], _inr(day["proc_amount_p"]),
        pdf_path, fname, fname, wa, _picker(date), date, _esc(u.get("user", "")),
        json.dumps(pdf_path), json.dumps(fname), json.dumps("Day Revenue %s" % _human(date)),
        json.dumps(summary))
    return _page("Day Revenue - %s" % _human(date), body)


def _absolute(path):
    host = request.headers.get("X-Forwarded-Host") or request.host or ""
    scheme = "http" if host.startswith(("127.", "localhost")) else "https"
    return "%s://%s%s" % (scheme, host, path)


def _picker(date):
    yday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    return """<form class="pick" method="get" action="/finance/clinic/share">
      <label for="d">Another day</label>
      <input type="date" id="d" name="d" value="%s" max="%s">
      <button class="btn small" type="submit">Open</button></form>""" % (
        date if _valid(date or "") else yday, dt.date.today().isoformat())


def _page(title, body):
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title><style>
:root{--ink:#111;--mut:#666;--line:#dcdcdc;--accent:#1F4E79;--soft:#eef4fb;--wa:#1f8f4e}
*{box-sizing:border-box}
body{margin:0;padding:14px;font:16px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif;color:var(--ink);background:#fafafa;max-width:520px;margin:0 auto}
h1{font-size:18px;margin:6px 0 10px;color:var(--accent)}h2{font-size:16px;margin:0 0 6px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}
.hd{font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.4px}
.big{font-size:34px;font-weight:700;color:var(--accent);margin:2px 0}
.sub{font-size:13.5px;color:var(--mut);margin-bottom:8px}
.mini{width:100%%;border-collapse:collapse;font-size:14px}.mini td{padding:3px 0;border-bottom:1px dotted var(--line)}
.n{text-align:center}.r{text-align:right;white-space:nowrap}
.btn{display:block;width:100%%;text-align:center;font-size:17px;font-weight:600;padding:14px;margin:8px 0;border:1.5px solid var(--accent);border-radius:9px;color:var(--accent);background:#fff;text-decoration:none;cursor:pointer}
.btn.primary{background:var(--wa);border-color:var(--wa);color:#fff}
.btn.small{display:inline-block;width:auto;font-size:14px;padding:8px 14px;margin:0 0 0 6px}
.status{font-size:13.5px;color:var(--mut);margin-top:6px;min-height:1.4em}
.fallback{margin-top:10px;padding-top:8px;border-top:1px dashed var(--line);font-size:14px}
.pick{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:10px 0}
.pick label{font-size:14px;color:var(--mut)}.pick input{font-size:16px;padding:8px;border:1px solid var(--line);border-radius:7px}
.foot{color:var(--mut);font-size:12.5px;margin:10px 2px}code{font-size:13px}
</style></head><body>
<h1>%s - Day Revenue</h1>
%s
</body></html>""" % (_esc(title), CLINIC, body)
