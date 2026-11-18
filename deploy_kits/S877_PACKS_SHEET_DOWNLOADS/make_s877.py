#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s877.py -- kit S877_PACKS_SHEET_DOWNLOADS (the parent, S484, 18-Nov-2026). His word of 14:49 (D1011): the 4.4 and 7
sheets download with one click and no flashing window (F-1474, F-1476), and sheet 7 reads well (F-1476).

/root/finance/packs.html (S875's TO d931f746):
  every xlsx link of the pack table (4.4 the card sheet, 1 the income sheet, 2 the UPI sheet + the bank check, 7 the payment
  papers) is a plain same-origin link with the `download` attribute -- the browser saves it in place, no new window opens
  and closes (that was the flash: target=_blank on an attachment) -- and a short note appears beside the link for nine
  seconds saying it is downloading and where it lands. PDFs and pages keep their new tab.
/root/finance/packs.py (S875's TO b1174cb0):
  sheet 7 (and the NK Pathology sheet alike) written by a new _s877_xlsx: column widths, wrapped text, the title merged,
  the header row shaded, frozen and filtered, Rs money with Indian grouping, real dates (dd-mmm-yyyy), the TOTAL row bold.
  The other sheets are written as before.
Usage: python make_s877.py SRC_DIR OUT_DIR
"""
import hashlib
import os
import sys

FROM = {"packs.py": "b1174cb08c4de39c6dd28ca32aa74d34", "packs.html": "d931f746c0deda6404834106d97a298e"}

NEW_XLSX = '''

S877_RS = ('"\u20b9 "##\\\\,##\\\\,##\\\\,##0.00', '"\u20b9 "##\\\\,##\\\\,##0.00', '"\u20b9 "#,##0.00')   # S877: Rs, Indian grouping, by size (one section each, so a minus sign shows)
S877_DIGEST = {"header": 2, "widths": {"A": 13, "B": 30, "C": 54, "D": 15, "E": 38, "F": 13},
               "wrap": ("B", "C", "E"), "money": ("D",), "dates": ("A",)}


def _s877_xlsx(sheets, spec):
    """S877: the digest's sheets laid out to be read -- widths, wrapped text, the title merged, the header row shaded,
    frozen and filtered, Rs money, real dates, the TOTAL row bold. [(title, [row, ...]), ...] -> xlsx bytes."""
    from openpyxl import Workbook                        # noqa: PLC0415
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side   # noqa: PLC0415
    from openpyxl.utils import get_column_letter          # noqa: PLC0415
    wb = Workbook()
    first = True
    hdr = int(spec.get("header") or 1)
    for title, rows in sheets:
        ws = wb.active if first else wb.create_sheet()
        first = False
        ws.title = title[:30]
        for r in rows:
            ws.append(list(r))
        last, ncol = ws.max_row, ws.max_column
        for col, w in spec.get("widths", {}).items():
            ws.column_dimensions[col].width = w
        if hdr > 1 and ncol > 1:
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncol)
            c = ws.cell(row=1, column=1)
            c.font = Font(bold=True, size=12)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[1].height = 34
        for c in ws[hdr]:
            c.font = Font(bold=True)
            c.fill = PatternFill("solid", fgColor="E7E6E6")
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = Border(bottom=Side(style="thin"))
        ws.row_dimensions[hdr].height = 32
        ws.freeze_panes = ws.cell(row=hdr + 1, column=1)
        ws.page_setup.orientation = "landscape"               # prints on one page wide
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_title_rows = "%d:%d" % (hdr, hdr)
        total_row = last if last > hdr and any(isinstance(x.value, str) and x.value.startswith("TOTAL") for x in ws[last]) else 0
        body_last = (total_row - 1) if total_row else last
        if body_last > hdr:
            ws.auto_filter.ref = "A%d:%s%d" % (hdr, get_column_letter(ncol), body_last)
        for row in ws.iter_rows(min_row=hdr + 1, max_row=last):
            for c in row:
                col = c.column_letter
                c.alignment = Alignment(wrap_text=(col in spec.get("wrap", ())), vertical="top",
                                        horizontal=("right" if col in spec.get("money", ()) else None))
                if col in spec.get("money", ()) and isinstance(c.value, (int, float)) and not isinstance(c.value, bool):
                    c.number_format = S877_RS[0] if abs(c.value) >= 1e7 else (S877_RS[1] if abs(c.value) >= 1e5 else S877_RS[2])
                if col in spec.get("dates", ()) and isinstance(c.value, str) and re.match(r"^\\d{4}-\\d{2}-\\d{2}$", c.value):
                    try:
                        c.value = dt.date.fromisoformat(c.value[:10])
                        c.number_format = "dd-mmm-yyyy"
                    except ValueError:
                        pass
        if total_row:
            for c in ws[total_row]:
                c.font = Font(bold=True)
                c.border = Border(top=Side(style="thin"))
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()
'''

PY_EDITS = [
    # 1. the writer, after _xlsx
    ("""    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _tender(row):""",
     """    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()
""" + NEW_XLSX + """

def _tender(row):"""),
    # 2. build_digest writes with it
    ("""    if nk:                                                              # S875: the lab's papers on their own sheet
        sheets.append(("NK Pathology %s" % month, sheet(nk, "NK Pathology's payment papers, %s -- the lab's own books" % _month_name(month))))
    return _xlsx(sheets), None""",
     """    if nk:                                                              # S875: the lab's papers on their own sheet
        sheets.append(("NK Pathology %s" % month, sheet(nk, "NK Pathology's payment papers, %s -- the lab's own books" % _month_name(month))))
    return _s877_xlsx(sheets, S877_DIGEST), None                        # S877: laid out to be read"""),
]

HTML_EDITS = [
    ("""      var pv=r.preview?'<a href="'+esc(r.preview)+'" target="_blank">open</a>':'';
      if(r.key==="income")pv+=' · <a href="/finance/packs/preview/income?month='+j.month+'">the sheet</a>';
      if(r.key==="upi")pv+=' · <a href="/finance/packs/preview/upi?month='+j.month+'">the sheet</a> · <a href="/finance/packs/preview/bankcheck?month='+j.month+'">the clinic bank check (yours only)</a>';
      if(r.key==="digest")pv='<a href="/finance/packs/preview/digest?month='+j.month+'">the sheet</a>';""",
     """      var pv=r.preview?dlink(r.preview,'open'):'';   /* S877: a sheet downloads in place, with a note; PDFs and pages open a tab */
      if(r.key==="income")pv+=' · '+dlink('/finance/packs/preview/income?month='+j.month,'the sheet');
      if(r.key==="upi")pv+=' · '+dlink('/finance/packs/preview/upi?month='+j.month,'the sheet')+' · '+dlink('/finance/packs/preview/bankcheck?month='+j.month,'the clinic bank check (yours only)');
      if(r.key==="digest")pv=dlink('/finance/packs/preview/digest?month='+j.month,'the sheet');"""),
    ("""function post(p,b){""",
     """function isxl(h){return /\\/finance\\/packs\\/preview\\/(cards|income|upi|digest|bankcheck)(\\?|$)/.test(h)}   /* S877: the xlsx previews */
function dlink(h,t){return isxl(h)?'<a href="'+esc(h)+'" download onclick="dlnote(this)">'+t+'</a>':'<a href="'+esc(h)+'" target="_blank">'+t+'</a>'}
function dlnote(a){var s=a.nextSibling; if(s&&s.nodeType===1&&s.className==="dln mut")s.remove(); s=document.createElement("span"); s.className="dln mut"; s.textContent=" — downloading… it lands in your browser's Downloads folder (not opened here)"; a.parentNode.insertBefore(s,a.nextSibling); setTimeout(function(){if(s.parentNode)s.remove()},9000)}
function post(p,b){"""),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch(src, edits, name):
    for i, (old, new) in enumerate(edits, 1):
        n = src.count(old)
        if n != 1:
            print("!! %s edit %d: anchor found %d times (want 1)" % (name, i, n))
            sys.exit(2)
        src = src.replace(old, new)
    return src


def main():
    sd, od = sys.argv[1:3]
    os.makedirs(od, exist_ok=True)
    for name, edits in (("packs.py", PY_EDITS), ("packs.html", HTML_EDITS)):
        with open(os.path.join(sd, name), "rb") as fh:
            raw = fh.read()
        if md5(raw) != FROM[name]:
            print("!! %s is %s, not %s -- read the real file first (F-472)" % (name, md5(raw)[:8], FROM[name][:8]))
            sys.exit(2)
        out = patch(raw.decode("utf-8"), edits, name).encode("utf-8")
        with open(os.path.join(od, name), "wb") as fh:
            fh.write(out)
        print("%s %s -> %s (%d -> %d bytes)" % (name, FROM[name][:8], md5(out)[:8], len(raw), len(out)))


if __name__ == "__main__":
    main()
