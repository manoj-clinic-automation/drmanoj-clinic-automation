

# =====================================================================
# S267 -- THE FILE FOR THE EMAIL.
#
# The advice is printed from the page and it is also EMAILED to the bank, from
# the account linked to it. So it has to exist as a workbook, and it has to be
# the bank's own workbook -- not a lookalike:
#
#   sheet named Sheet2, as every file since April 2026 is
#   the same four letterhead lines, merged the same way (A1:C1, A3:G3, A4:G4)
#   the same seven headers, the first two carrying their leading newline
#   account numbers written as TEXT, so 088851000012 keeps its leading zero
#   amounts as whole numbers, General format, no separators
#   the total as a real =SUM() formula, with its value cached so it shows
#   the same column widths, the same row heights, A4 landscape, fit to page
#
# WRITTEN WITH THE STANDARD LIBRARY ALONE. A .xlsx is a zip of XML, and this
# builds it directly -- no openpyxl, no xlsxwriter, nothing to install on the
# box and nothing to go missing at month end.
# =====================================================================

import zipfile as _zip_s267

_XLSX_CT_S267 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.spreadsheetml.styles+xml"/></Types>')

_XLSX_RELS_S267 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')

_XLSX_WB_S267 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<sheets><sheet name="Sheet2" sheetId="1" r:id="rId1"/></sheets></workbook>')

_XLSX_WBRELS_S267 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/styles" Target="styles.xml"/></Relationships>')

# 0 plain · 1 bold · 2 firm name · 3 header (bold, boxed, wrapped) · 4 boxed
# 5 boxed centred · 6 boxed right · 7 boxed bold right
_XLSX_STYLES_S267 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="3">'
    '<font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="16"/><name val="Calibri"/></font>'
    '</fonts>'
    '<fills count="2"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill></fills>'
    '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>'
    '<border><left style="thin"/><right style="thin"/><top style="thin"/>'
    '<bottom style="thin"/><diagonal/></border></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="8">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" applyBorder="1" '
    'applyAlignment="1"><alignment vertical="bottom" wrapText="1"/></xf>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" '
    'applyAlignment="1"><alignment horizontal="center"/></xf>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" '
    'applyAlignment="1"><alignment horizontal="right"/></xf>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" applyBorder="1" '
    'applyAlignment="1"><alignment horizontal="right"/></xf>'
    '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/>'
    '</cellStyles></styleSheet>')

_XLSX_COLS_S267 = ((1, 5.5546875), (2, 8.6640625), (3, 25.109375), (4, 31.88671875),
                   (5, 13.33203125), (6, 10.33203125), (7, 16.0))


def _x_esc_s267(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _x_cell_s267(ref, value, style=0, numeric=False, formula=None, cached=None):
    st = ' s="%d"' % style if style else ""
    if formula is not None:
        return ('<c r="%s"%s><f>%s</f><v>%s</v></c>'
                % (ref, st, _x_esc_s267(formula), _x_esc_s267(cached)))
    if value is None or value == "":
        return '<c r="%s"%s/>' % (ref, st)
    if numeric:
        return '<c r="%s"%s><v>%s</v></c>' % (ref, st, _x_esc_s267(value))
    return ('<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
            % (ref, st, _x_esc_s267(value)))


def _advice_xlsx_s267(con, month):
    """The bank's workbook, byte for byte in shape with the ones already sent."""
    rows, total, missing, paise = _advice_rows_s265(con, month)
    mob = _pay_config_s265(con, "shop_mobile", "")
    cols = "".join('<col min="%d" max="%d" width="%s" customWidth="1"/>' % (i, i, w)
                   for i, w in _XLSX_COLS_S267)
    out = []
    out.append('<row r="1">' + _x_cell_s267("A1", "GSTIN: %s" % ADVICE_HEAD_S265[0][1], 1)
               + _x_cell_s267("G1", (" (M) %s" % mob) if mob else "", 1) + '</row>')
    out.append('<row r="2">' + _x_cell_s267("A2", ADVICE_DL_S265, 1) + '</row>')
    out.append('<row r="3" ht="52.8" customHeight="1">'
               + _x_cell_s267("A3", ADVICE_FIRM_S265, 2) + '</row>')
    out.append('<row r="4">' + _x_cell_s267("A4", ADVICE_ADDR_S265, 1) + '</row>')
    heads = ["\nSr. No.", "\nTxn. type", "Credit Account Number", "Credit Account Name",
             "IFSC", "Amount", "Narration"]
    out.append('<row r="5" ht="43.2" customHeight="1">'
               + "".join(_x_cell_s267("%s5" % chr(65 + i), h, 3)
                         for i, h in enumerate(heads)) + '</row>')
    r = 6
    for line in rows:
        out.append('<row r="%d">' % r
                   + _x_cell_s267("A%d" % r, line["sr"], 5, numeric=True)
                   + _x_cell_s267("B%d" % r, "NEFT", 5)
                   + _x_cell_s267("C%d" % r, line["acct"], 4)
                   + _x_cell_s267("D%d" % r, line["name"], 4)
                   + _x_cell_s267("E%d" % r, line["ifsc"], 4)
                   + _x_cell_s267("F%d" % r, line["rupees"], 6, numeric=True)
                   + _x_cell_s267("G%d" % r, "Vendor Payment", 4) + '</row>')
        r += 1
    last = r - 1
    if rows:
        out.append('<row r="%d">' % r
                   + "".join(_x_cell_s267("%s%d" % (chr(65 + i), r), "", 4) for i in range(5))
                   + _x_cell_s267("F%d" % r, None, 7, formula="SUM(F6:F%d)" % last,
                                  cached=total)
                   + _x_cell_s267("G%d" % r, "", 4) + '</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>'
        '<dimension ref="A1:G%d"/><sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/><cols>%s</cols><sheetData>%s</sheetData>'
        '<mergeCells count="3"><mergeCell ref="A1:C1"/><mergeCell ref="A3:G3"/>'
        '<mergeCell ref="A4:G4"/></mergeCells>'
        '<pageMargins left="0.7086614173228347" right="0.7086614173228347" top="0.75" '
        'bottom="0.75" header="0.3" footer="0.3"/>'
        '<pageSetup paperSize="9" orientation="landscape" fitToWidth="1" fitToHeight="1"/>'
        '</worksheet>' % (r, cols, "".join(out)))
    buf = io.BytesIO()
    with _zip_s267.ZipFile(buf, "w", _zip_s267.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _XLSX_CT_S267)
        z.writestr("_rels/.rels", _XLSX_RELS_S267)
        z.writestr("xl/workbook.xml", _XLSX_WB_S267)
        z.writestr("xl/_rels/workbook.xml.rels", _XLSX_WBRELS_S267)
        z.writestr("xl/styles.xml", _XLSX_STYLES_S267)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue(), total, missing


def _advice_filename_s267(month):
    """NEFT ADVICE AUGUST 2026.xlsx -- the name these files have always carried."""
    try:
        y, m = month.split("-")
        name = ("JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST",
                "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER")[int(m) - 1]
        return "NEFT ADVICE %s %s.xlsx" % (name, y)
    except Exception:
        return "NEFT ADVICE %s.xlsx" % month


@bp.route("/page/pay/<month>/advice.xlsx")
def page_pay_advice_xlsx(month):
    """The attachment for the email. Built from the sheet, never maintained."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not re.match(r"^\d{4}-\d{2}$", month):
        return "bad month", 400
    con = _db()
    _ensure(con)
    _pay_ensure(con)
    blob, total, missing = _advice_xlsx_s267(con, month)
    _audit(con, _who(u), "pay_advice_xlsx", month, {"total": total, "left_out": missing})
    con.commit()
    return blob, 200, {
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Cache-Control": "no-store",
        "Content-Disposition": 'attachment; filename="%s"' % _advice_filename_s267(month)}
