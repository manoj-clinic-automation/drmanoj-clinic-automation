#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mkreg_s837.py OUT.xlsx -- kit S837: a MADE-UP Marg Stock Register in the TEXT layout the medical PC writes (no real person in it: the
patient and doctor cells say WALK PATIENT / DR WALK). Its shape follows the real export: the shop head, the title, the two-line header,
the item heading, 'Opening / Balance as on', a day's first entry on the date line with its number on the next line, the page break's
Carried / Brought Forward, the Received / Issued footers. TYRO WALK 1*10: opening 43:7, 7 entries, closing 46:8, every step its entry."""
import sys
import zipfile
from xml.sax.saxutils import escape

HEAD = [["SANJEEVNI WALK SHOP"], ["WALK ROAD, NOWHERE"], [""], ["STOCK REGISTER WHOLE FROM 01-09-2026 - 04-10-2026"]]
COLS = ["Bill No. /", "Type", "Patient Name", "Doctor Name", "Batch", "Quantity", "Value", "Balance"]
COLS2 = ["Date", "", "", "", "No.", "", "", "Quantity"]
P, D = "WALK PATIENT", "DR WALK"


def _xlsx(out, rows):
    """A minimal .xlsx written with the standard library only (shared strings, one sheet) -- no openpyxl on the box is needed."""
    strs, idx = [], {}

    def si(v):
        if v not in idx:
            idx[v] = len(strs)
            strs.append(v)
        return idx[v]
    xr = []
    for r, row in enumerate(rows, 1):
        cs = "".join('<c r="%s%d" t="s"><v>%d</v></c>' % (chr(65 + c), r, si(v)) for c, v in enumerate(row) if v != "")
        xr.append('<row r="%d">%s</row>' % (r, cs))
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             '<sheetData>%s</sheetData></worksheet>' % "".join(xr))
    sst = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
           'count="%d" uniqueCount="%d">%s</sst>' % (len(strs), len(strs), "".join("<si><t xml:space=\"preserve\">%s</t></si>" % escape(x) for x in strs)))
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
          '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
          '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    wb = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wrels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
             '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/></Relationships>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wrels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
        z.writestr("xl/sharedStrings.xml", sst)


def build(out):
    rows = HEAD + [COLS, COLS2, ["TYRO WALK 1*10"], ["Opening", "Balance as on", "01-09-2026", "", "", "", "", "43:7"],
                   ["01-09-2026", "Purchase", P, "", "LGQ1", "40:0", "5920.00", "83:7"], ["160"],
                   ["CN00194", "Sale Return", P, D, "LGQ1", "1:4", "256.46", "85:1"],
                   ["A003323", "Sale", P, D, "LGQ1", "1:2", "220.61", "83:9"],
                   ["Carried", "Forward", "", D, "54:3", "9843.9", "", ""], [""], ["SANJEEVNI WALK SHOP"],
                   ["STOCK", "REGISTER WHOLE FROM", P, D], COLS, COLS2, ["Brought", "Forward", "", D, "54:3", "9843.9", "", ""],
                   ["02-09-2026", "Sale", P, D, "LGQ1", "2:1", "388.50", "81:8"], ["A003333"],
                   ["A003335", "Stock Issue", "", "", "LGQ1", "0:5", "70.00", "81:3"],
                   ["03-09-2026", "Stock Receive", "", "", "LGQ1", "0:5", "70.00", "81:8"], ["SR-0001"],
                   ["A003340", "Sale", P, D, "LGQ1", "35:0", "6000.00", "46:8"],
                   ["", "", "", "", "Received :", "41:9", "6246.46", ""], ["", "", "", "", "Issued :", "38:8", "6679.11", ""]]
    _xlsx(out, [r + [""] * (8 - len(r)) for r in rows])


if __name__ == "__main__":
    build(sys.argv[1])
