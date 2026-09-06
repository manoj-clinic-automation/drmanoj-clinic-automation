#!/usr/bin/python3
"""
padwriter.py -- write the STOCK COUNT PAD (and its follow-up) with nothing installed.

WHY IT EXISTS
    The server has to HAND A SHEET BACK -- a fresh pad for a new count, and a
    follow-up pad listing only what still needs a person -- and it has to do it
    with the standard library, for the same reason padreader.py reads with the
    standard library: nothing about a stock count should depend on what happens
    to be in a venv.

WHAT IT WRITES
    One sheet, inline strings (no shared-string table to keep consistent), a
    handful of styles, real formulas for the TOTAL column, frozen header, an
    autofilter, and print titles. Enough for Excel and LibreOffice to open it
    as the same pad the counters already know.

    NO FIGURE FROM MARG goes into a pad. The owner's rule: nothing in the sheet
    may tell the counter what the answer is "supposed" to be.
"""
import datetime
import io
import zipfile
from xml.sax.saxutils import escape

# ---------------------------------------------------------------- styles
# cellXfs index: 0 normal · 1 bold · 2 INPUT (shaded, boxed) · 3 header (white on
# black) · 4 title · 5 note (grey italic) · 6 bold number · 7 boxed normal
STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="8">
 <font><sz val="10"/><name val="Arial"/></font>
 <font><b/><sz val="10"/><name val="Arial"/></font>
 <font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Arial"/></font>
 <font><b/><sz val="14"/><name val="Arial"/></font>
 <font><i/><sz val="10"/><color rgb="FF555555"/><name val="Arial"/></font>
 <font><b/><sz val="10"/><color rgb="FF8C1D18"/><name val="Arial"/></font>
 <font><sz val="10"/><color rgb="FF14532D"/><name val="Arial"/></font>
 <font><b/><sz val="11"/><name val="Arial"/></font>
</fonts>
<fills count="5">
 <fill><patternFill patternType="none"/></fill>
 <fill><patternFill patternType="gray125"/></fill>
 <fill><patternFill patternType="solid"><fgColor rgb="FFFFF3C4"/><bgColor indexed="64"/></patternFill></fill>
 <fill><patternFill patternType="solid"><fgColor rgb="FF1A1A1A"/><bgColor indexed="64"/></patternFill></fill>
 <fill><patternFill patternType="solid"><fgColor rgb="FFD9D9D9"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="2">
 <border><left/><right/><top/><bottom/><diagonal/></border>
 <border><left style="thin"><color rgb="FFBFBFBF"/></left><right style="thin"><color rgb="FFBFBFBF"/></right><top style="thin"><color rgb="FFBFBFBF"/></top><bottom style="thin"><color rgb="FFBFBFBF"/></bottom><diagonal/></border>
</borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="13">
 <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
 <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
 <xf numFmtId="0" fontId="0" fillId="2" borderId="1" xfId="0" applyFill="1" applyBorder="1"/>
 <xf numFmtId="0" fontId="2" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
 <xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>
 <xf numFmtId="0" fontId="4" fillId="0" borderId="0" xfId="0" applyFont="1"/>
 <xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"/>
 <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>
 <xf numFmtId="0" fontId="1" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" wrapText="1"/></xf>
 <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" wrapText="1"/></xf>
 <xf numFmtId="0" fontId="5" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"/>
 <xf numFmtId="0" fontId="6" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"/>
 <xf numFmtId="0" fontId="7" fillId="0" borderId="0" xfId="0" applyFont="1"/>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""

NORMAL, BOLD, INPUT, HEADER, TITLE, NOTE, BOLDBOX, BOX, GROUPGREY, GROUPYELLOW, REDBOX, GREENBOX, SUBHEAD = range(13)


def _colname(i):
    """0 -> A, 25 -> Z, 26 -> AA."""
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


class Sheet(object):
    def __init__(self):
        self.cells = {}      # (r, c) -> (kind, value, style)   kinds: s f n
        self.widths = {}
        self.freeze = None   # e.g. "A9"
        self.filter = None   # e.g. "A8:H381"
        self.print_title_rows = None   # e.g. (8, 8)
        self.merges = []

    def text(self, r, c, v, style=NORMAL):
        self.cells[(r, c)] = ("s", "" if v is None else str(v), style)

    def num(self, r, c, v, style=NORMAL):
        if v is None or v == "":
            self.cells[(r, c)] = ("s", "", style)
        else:
            self.cells[(r, c)] = ("n", v, style)

    def formula(self, r, c, f, style=NORMAL):
        self.cells[(r, c)] = ("f", f, style)

    def xml(self):
        rows = {}
        for (r, c), v in self.cells.items():
            rows.setdefault(r, {})[c] = v
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">']
        if self.freeze:
            # split at the freeze cell: rows above it stay
            fr = int("".join(ch for ch in self.freeze if ch.isdigit()))
            out.append('<sheetViews><sheetView workbookViewId="0"><pane ySplit="%d" '
                       'topLeftCell="%s" activePane="bottomLeft" state="frozen"/>'
                       '</sheetView></sheetViews>' % (fr - 1, self.freeze))
        if self.widths:
            out.append("<cols>")
            for c in sorted(self.widths):
                out.append('<col min="%d" max="%d" width="%s" customWidth="1"/>'
                           % (c + 1, c + 1, self.widths[c]))
            out.append("</cols>")
        out.append("<sheetData>")
        for r in sorted(rows):
            out.append('<row r="%d">' % r)
            for c in sorted(rows[r]):
                kind, v, st = rows[r][c]
                ref = "%s%d" % (_colname(c), r)
                if kind == "n":
                    out.append('<c r="%s" s="%d"><v>%s</v></c>' % (ref, st, v))
                elif kind == "f":
                    out.append('<c r="%s" s="%d"><f>%s</f></c>' % (ref, st, escape(v)))
                else:
                    if v == "":
                        out.append('<c r="%s" s="%d"/>' % (ref, st))
                    else:
                        out.append('<c r="%s" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
                                   % (ref, st, escape(v)))
            out.append("</row>")
        out.append("</sheetData>")
        if self.filter:
            out.append('<autoFilter ref="%s"/>' % self.filter)
        if self.merges:
            out.append('<mergeCells count="%d">%s</mergeCells>'
                       % (len(self.merges), "".join('<mergeCell ref="%s"/>' % m for m in self.merges)))
        out.append('<pageMargins left="0.5" right="0.5" top="0.6" bottom="0.6" header="0.3" footer="0.3"/>')
        out.append("</worksheet>")
        return "\n".join(out)


def _sheet_names_xml(sheet, name, idx):
    names = []
    if sheet.print_title_rows:
        a, b = sheet.print_title_rows
        names.append('<definedName name="_xlnm.Print_Titles" localSheetId="%d">'
                     "'%s'!$%d:$%d</definedName>" % (idx, name, a, b))
    if sheet.filter:
        c1, c2 = sheet.filter.split(":")
        def _abs(ref):
            col = "".join(ch for ch in ref if ch.isalpha())
            row = "".join(ch for ch in ref if ch.isdigit())
            return "$%s$%s" % (col, row)
        names.append('<definedName name="_xlnm._FilterDatabase" localSheetId="%d" hidden="1">'
                     "'%s'!%s:%s</definedName>" % (idx, name, _abs(c1), _abs(c2)))
    return names


def workbook_bytes(sheet, name="COUNT"):
    """One sheet -- the pads."""
    return workbook_bytes_multi([(name, sheet)])


def workbook_bytes_multi(sheets):
    """sheets: [(name, Sheet)] in tab order. The result workbook."""
    names = []
    sheet_xml, rel_xml, ct_over = [], [], []
    for i, (nm, sh) in enumerate(sheets):
        names += _sheet_names_xml(sh, nm, i)
        sheet_xml.append('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (escape(nm), i + 1, i + 1))
        rel_xml.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1))
        ct_over.append('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % (i + 1))
    defined = ("<definedNames>%s</definedNames>" % "".join(names)) if names else ""
    n = len(sheets)
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
          '<sheets>%s</sheets>%s</workbook>' % ("".join(sheet_xml), defined))
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '%s<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>' % ("".join(rel_xml), n + 1))
    root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                 '</Relationships>')
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '%s<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
          '</Types>' % "".join(ct_over))
    buf = io.BytesIO()
    z = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)
    z.writestr("[Content_Types].xml", ct)
    z.writestr("_rels/.rels", root_rels)
    z.writestr("xl/workbook.xml", wb)
    z.writestr("xl/_rels/workbook.xml.rels", rels)
    z.writestr("xl/styles.xml", STYLES)
    for i, (nm, sh) in enumerate(sheets):
        z.writestr("xl/worksheets/sheet%d.xml" % (i + 1), sh.xml())
    z.close()
    return buf.getvalue()


# ---------------------------------------------------------------- the pads
HDR = ["#", "ITEM", "PACKING", "PACK SIZE", "STRIPS", "LOOSE", "TOTAL UNITS", "REMARKS"]
WIDTHS = {0: 5, 1: 34, 2: 11, 3: 10, 4: 9, 5: 9, 6: 12, 7: 34}


def _dmy(s):
    """2026-09-06 -> 06-09-2026 for a person; anything else as it came."""
    s = (s or "").strip()
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s[8:10] + "-" + s[5:7] + "-" + s[0:4]
    return s


def _head(sh, title, sub, date_str, part_line=None, meta=None):
    """The four details are WRITTEN IN when the pad is downloaded from the
    stock-check page (S226, the owner: "the Excel which then comes down is
    prefilled with all this data and staff only have to enter the stocks").
    They stay shaded -- a person may still correct them."""
    m = meta or {}
    sh.text(1, 0, title, TITLE)
    sh.text(2, 0, sub, NOTE)
    sh.merges.append("A2:H2")
    sh.text(4, 0, "Date", BOLD); sh.text(4, 1, date_str, INPUT)
    sh.text(5, 0, "Counted by", BOLD); sh.text(5, 1, m.get("counted_by") or "", INPUT)
    sh.text(6, 0, "Entered by", BOLD); sh.text(6, 1, m.get("entered_by") or "", INPUT)
    sh.text(7, 0, "Bill no", BOLD); sh.text(7, 1, (m.get("bill_no") or "").upper(), INPUT)
    sh.text(7, 3, "Bill date", BOLD); sh.text(7, 4, _dmy(m.get("bill_date")), INPUT)
    sh.text(4, 3, "TYPE ONLY IN THE SHADED CELLS.", BOLD)
    sh.text(5, 3, "Strips = full strips / boxes.  Loose = single tablets or pieces left over.  "
                  "Total counts itself.", NOTE)
    sh.text(6, 3, part_line or ("Example -- an item packed 1*15, you find 20 full strips and 5 loose "
                                "tablets:  Strips 20,  Loose 5,  Total shows 305."), NOTE)


def _table(sh, hr, rows, remark_col_default=None):
    """rows: [(item, packing, pack_size, strips, loose, remark)]. Returns last row."""
    for i, h in enumerate(HDR):
        sh.text(hr, i, h, HEADER)
    r = hr + 1
    for n, (item, packing, ps, st, lo, rem) in enumerate(rows, start=1):
        sh.num(r, 0, n)
        sh.text(r, 1, item, BOX)
        sh.text(r, 2, packing or "", BOX)
        sh.num(r, 3, int(ps or 1), BOX)
        sh.num(r, 4, st, INPUT)
        sh.num(r, 5, lo, INPUT)
        sh.formula(r, 6, 'IF(AND(E{0}="",F{0}=""),"",N(E{0})*D{0}+N(F{0}))'.format(r), BOLDBOX)
        sh.text(r, 7, rem if rem is not None else (remark_col_default or ""), INPUT)
        r += 1
    last = r - 1
    sh.text(r + 1, 1, "ITEMS WITH A FIGURE ENTERED", BOLD)
    sh.formula(r + 1, 6, "COUNT(G%d:G%d)" % (hr + 1, last), BOLD)
    sh.text(r + 2, 1, "TOTAL UNITS COUNTED", BOLD)
    sh.formula(r + 2, 6, "SUM(G%d:G%d)" % (hr + 1, last), BOLD)
    sh.widths.update(WIDTHS)
    sh.freeze = "A%d" % (hr + 1)
    sh.filter = "A%d:H%d" % (hr, last)
    sh.print_title_rows = (hr, hr)
    return last


def fresh_pad(items, as_on_text, today=None, meta=None):
    """items: [(item, packing, pack_size)] -- NO quantities, ever.
    meta: {counted_by, entered_by, bill_no, bill_date} written into the top
    lines, so the sheet carries its own anchor back to the server."""
    today = today or datetime.date.today().strftime("%d-%m-%Y")
    sh = Sheet()
    _head(sh, "SANJEEVNI MEDICOS -- STOCK COUNT PAD",
          "A rough pad, on paper terms. It holds NO figure from Marg -- nothing here can tell "
          "you what the answer is 'supposed' to be. Count the shelf, write what is on it.",
          today, meta=meta)
    last = _table(sh, 8, [(i, p, s, None, None, None) for i, p, s in items])
    sh.text(last + 4, 1, "Items in this pad -- from Marg's item list as on %s, quantities removed"
            % as_on_text, NOTE)
    sh.num(last + 4, 6, len(items), NOTE)
    return workbook_bytes(sh)


def followup_pad(count_id, count_date, fix_rows, uncounted, today=None):
    """fix_rows: [(row_no, item_as_written, figure, why)]
       uncounted: [(item, packing, pack_size)]
    The rows to FIX come first, with what was written and why it could not be
    used; then every item nobody reached. Nothing from Marg's own figures."""
    today = today or datetime.date.today().strftime("%d-%m-%Y")
    sh = Sheet()
    _head(sh, "STOCK COUNT -- FOLLOW-UP SHEET",
          "The first sheet has been recorded as count #%d. THIS sheet is only what still needs "
          "you: rows that could not be used as written, then every item not yet counted. "
          "Fill it and upload it the same way -- it joins count #%d." % (count_id, count_id),
          today, part_line="PART OF COUNT #%d  (%s)  -- do not change this line" % (count_id, count_date))
    rows = []
    for row_no, written, fig, why in fix_rows:
        rows.append((written, "", 1, None, None,
                     "FIX: %s  (you wrote %s on row %s)" % (why, fig, row_no)))
    for item, packing, ps in uncounted:
        rows.append((item, packing, ps, None, None, ""))
    _table(sh, 8, rows)
    return workbook_bytes(sh)


# ---------------------------------------------------------------- the result
def fmt_units(units, ps):
    """The shop's own convention: strips and tablets, pieces for 1*1. A shortage
    keeps the breakdown and carries the sign in the word."""
    units = int(units)
    if units < 0:
        return "short " + fmt_units(-units, ps)
    if ps <= 1:
        return "%d pc%s" % (units, "" if abs(units) == 1 else "s")
    p, l = divmod(units, ps)
    bits = []
    if p:
        bits.append("%d strip%s" % (p, "" if p == 1 else "s"))
    if l:
        bits.append("%d tablet%s" % (l, "" if l == 1 else "s"))
    return " ".join(bits) or "0 strips"


def rupees(p):
    if p is None:
        return "no rate on record"
    n = abs(int(p)); whole, paise = divmod(n, 100); s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]; parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return ("-" if int(p) < 0 else "") + "Rs %s.%02d" % (s, paise)


def result_workbook(R):
    """R: dict --
      count_id, part_of, finding_no, when, counted_by, entered_by, recorded_by,
      as_on, as_on_note, bill, readiness_lines[4],
      items_in_shop, counted, agreed, differed, sent_back, not_counted, explained,
      differences [(item, packing, ps, marg, counted, value_p_or_None)],
      not_counted_rows [(item, packing, ps)],
      fixes [(row, written, figure, why)],
      matched [(item, packing, ps, qty)]
    Layout as approved by the owner, 06-Sep-2026."""
    S = []
    # ---- SUMMARY
    sh = Sheet()
    sh.text(1, 0, "SANJEEVNI MEDICOS -- STOCK CHECK RESULT", TITLE)
    fam = "count #%d" % R["count_id"] + (" (part of count #%d)" % R["part_of"] if R.get("part_of") else "")
    sh.text(2, 0, "Finding %s  -  %s" % (R.get("finding_no") or "", fam), NOTE)
    sh.text(3, 0, "PART OF COUNT #%d  (%s)  -- do not change this line"
            % (R.get("part_of") or R["count_id"], R["as_on"]), NOTE)
    r = 5
    def line(k, v, style=NORMAL):
        nonlocal r
        sh.text(r, 0, k, SUBHEAD if (k and k.isupper()) else BOLD); sh.text(r, 1, v, style); r += 1
    line("Date and time", R["when"]); line("Counted by", R["counted_by"])
    line("Entered by", R["entered_by"]); line("Recorded by", R["recorded_by"])
    line("Marg stock as on", R["as_on"] + (("  (" + R["as_on_note"] + ")") if R.get("as_on_note") else ""))
    line("After bill", R["bill"])
    cl = R.get("closed")
    left = R["sent_back"] + R["not_counted"]
    if cl:
        line("Status", ("CLOSED -- stock check completed on %s" % cl["at_text"]) if cl.get("how") == "complete"
             else ("CLOSED by the doctor as it stood on %s -- %d not counted, %d to fix were left"
                   % (cl["at_text"], cl.get("left_not_counted", 0), cl.get("left_to_fix", 0))))
    else:
        line("Status", ("OPEN -- %d not counted, %d to fix: fill the NOT COUNTED and SENT BACK TO FIX "
                        "tabs and upload this file again" % (R["not_counted"], R["sent_back"])) if left
             else "OPEN -- everything counted; press Close the stock check on the page")
    line("", "")
    line("READ FIRST -- KNOW THE DATA", "")
    for lab, txt in zip(("Sale report", "Purchases", "Marg's closing stock", "Sale returns"),
                        (R.get("readiness_lines") or ["", "", "", ""])):
        line(lab, txt)
    line("", ""); line("THE COUNT", "")
    line("Items in the shop", str(R["items_in_shop"]))
    line("Counted and accepted", str(R["counted"]))
    line("  of which agree with Marg", str(R["agreed"]))
    line("  of which differ", str(R["differed"]))
    line("Rows sent back to fix", str(R["sent_back"]))
    line("Not yet counted", str(R["not_counted"]))
    line("", ""); line("EXPLANATIONS (optional, filled in later, in tranches)", "")
    line("Differences explained so far", "%d of %d" % (R.get("explained", 0), R["differed"]))
    sh.widths = {0: 42, 1: 78}
    S.append(("SUMMARY", sh))

    # ---- DIFFERENCES
    sh = Sheet()
    sh.text(1, 0, "DIFFERENCES -- counted against Marg, in the shop's own units", TITLE)
    sh.text(2, 0, "A shortage reads 'short 1 strip 3 tablets'. Reason, cause and decision are "
                  "optional and come later, in tranches.", NOTE)
    sh.text(4, 2, "AS PER MARG (the computer's stock)", GROUPGREY)
    sh.text(4, 3, "PHYSICAL STOCK (counted on the shelf)", GROUPYELLOW)
    sh.text(4, 4, "DIFFERENCE = physical minus Marg", GROUPGREY)
    heads = ["ITEM", "PACKING", "MARG STOCK (strips & tabs)", "PHYSICAL COUNT (strips & tabs)",
             "DIFFERENCE (strips & tabs)", "AT MRP", "STAFF'S REASON", "CHECKER'S CAUSE", "DECISION"]
    for i, h in enumerate(heads):
        sh.text(5, i, h, HEADER)
    rr = 6
    diffs = sorted(R["differences"], key=lambda d: (-abs(d[5] or 0), -abs(d[4] - d[3])))
    for item, packing, ps, marg, counted, value_p in diffs:
        d = counted - marg
        sh.text(rr, 0, item, BOX); sh.text(rr, 1, packing or "", BOX)
        sh.text(rr, 2, fmt_units(marg, ps), BOX); sh.text(rr, 3, fmt_units(counted, ps), BOX)
        sh.text(rr, 4, fmt_units(d, ps), REDBOX if d < 0 else BOX)
        sh.text(rr, 5, rupees(value_p) if value_p is not None else "no rate on record", BOX)
        for c in (6, 7, 8):
            sh.text(rr, c, "", BOX)
        rr += 1
    sh.widths = {0: 30, 1: 10, 2: 24, 3: 24, 4: 24, 5: 18, 6: 22, 7: 22, 8: 18}
    sh.freeze = "A6"
    S.append(("DIFFERENCES", sh))

    # ---- NOT COUNTED (fill-in)
    sh = Sheet()
    sh.text(1, 0, "NOT YET COUNTED -- please count these and fill in the stock", TITLE)
    sh.text(2, 0, "These items were not reached in the first count. Type only in the shaded cells: "
                  "Strips = full strips / boxes, Loose = single tablets or pieces left over. "
                  "Total counts itself.", NOTE)
    sh.merges.append("A2:G2")
    for i, h in enumerate(["#", "ITEM", "PACKING", "STRIPS", "LOOSE", "TOTAL UNITS", "REMARKS"]):
        sh.text(4, i, h, HEADER)
    rr = 5
    for n, (item, packing, ps) in enumerate(R["not_counted_rows"], start=1):
        sh.num(rr, 0, n, BOX); sh.text(rr, 1, item, BOX); sh.text(rr, 2, packing or "", BOX)
        sh.num(rr, 3, None, INPUT); sh.num(rr, 4, None, INPUT)
        sh.formula(rr, 5, 'IF(AND(D{0}="",E{0}=""),"",N(D{0})*{1}+N(E{0}))'.format(rr, int(ps or 1)), BOLDBOX)
        sh.text(rr, 6, "", INPUT)
        rr += 1
    sh.widths = {0: 5, 1: 34, 2: 11, 3: 9, 4: 9, 5: 12, 6: 30}
    sh.freeze = "A5"
    if rr > 5:
        sh.filter = "A4:G%d" % (rr - 1)
    S.append(("NOT COUNTED", sh))

    # ---- SENT BACK TO FIX (fill-in: correct the name and/or the figure here)
    sh = Sheet()
    sh.text(1, 0, "ROWS SENT BACK -- could not be used as written. Correct them HERE.", TITLE)
    sh.text(2, 0, "Fix the item name in the shaded ITEM cell if it was wrong, and write the count "
                  "again in Strips / Loose. What to fix is in the last column.", NOTE)
    sh.merges.append("A2:H2")
    for i, h in enumerate(["#", "ITEM", "PACKING", "STRIPS", "LOOSE", "TOTAL UNITS", "SHEET ROW", "WHAT TO FIX"]):
        sh.text(4, i, h, HEADER)
    rr = 5
    for n, (row_no, written, fig, why) in enumerate(R["fixes"], start=1):
        sh.num(rr, 0, n, BOX); sh.text(rr, 1, written, INPUT); sh.text(rr, 2, "", BOX)
        sh.num(rr, 3, None, INPUT); sh.num(rr, 4, None, INPUT)
        sh.formula(rr, 5, 'IF(AND(D{0}="",E{0}=""),"",N(D{0})*1+N(E{0}))'.format(rr), BOLDBOX)
        sh.num(rr, 6, row_no, BOX)
        sh.text(rr, 7, "%s%s" % (why, ("  (you wrote %s)" % fig) if fig is not None else ""), BOX)
        rr += 1
    sh.widths = {0: 5, 1: 34, 2: 11, 3: 9, 4: 9, 5: 12, 6: 10, 7: 52}
    sh.freeze = "A5"
    S.append(("SENT BACK TO FIX", sh))

    # ---- MATCHED
    sh = Sheet()
    sh.text(1, 0, "MATCHED EXACTLY -- %d items" % len(R["matched"]), TITLE)
    for i, h in enumerate(["ITEM", "PACKING", "MARG = COUNTED (strips & tabs)"]):
        sh.text(3, i, h, HEADER)
    rr = 4
    for item, packing, ps, qty in R["matched"]:
        sh.text(rr, 0, item, GREENBOX); sh.text(rr, 1, packing or "", GREENBOX)
        sh.text(rr, 2, fmt_units(qty, ps), GREENBOX); rr += 1
    sh.widths = {0: 30, 1: 10, 2: 30}
    sh.freeze = "A4"
    S.append(("MATCHED", sh))
    return workbook_bytes_multi(S)
