#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s877.py -- kit S877 (the parent, S484, 18-Nov-2026), on a MADE-UP root: a made-up finance db (packs.ensure + a made-up
payment register), invented vendors, no real number.
    python3 walk_s877.py <dir holding packs.py + packs.html> <scratch>            last line 'WALK n/m'
Control: the live files (S875's) go red -- no layout on the sheet, target=_blank on the xlsx links."""
import io
import os
import re
import sqlite3
import sys

d, scr = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != here]          # F-1441: never the kit's own folder
sys.path.insert(0, d)
os.makedirs(scr, exist_ok=True)
for f in ("fin.db",):
    if os.path.exists(os.path.join(scr, f)):
        os.remove(os.path.join(scr, f))
os.environ["FINANCE_DB"] = os.path.join(scr, "fin.db")
os.environ["ASSETS_UPLOADS"] = os.path.join(scr, "uploads")
os.environ["PACKS_MAIL_STUB"] = os.path.join(scr, "mail")
ok, n = 0, 0


def chk(name, cond, info=""):
    global ok, n
    n += 1
    ok += bool(cond)
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(info)[:200] + "]") if (info and not cond) else ""))


try:
    import packs as p
except Exception as e:                                   # noqa: BLE001
    print("FAIL import packs: %s" % e)
    print("WALK 0/25")
    sys.exit(1)

con = sqlite3.connect(os.environ["FINANCE_DB"])
con.row_factory = sqlite3.Row
p.ensure(con)
con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT)")
con.execute("CREATE TABLE IF NOT EXISTS payment_register (row_no INTEGER, date_iso TEXT, vendor TEXT, description TEXT, amount_raw TEXT, "
            "amount_paise INTEGER, in_drive INTEGER, gmail_link TEXT)")
pr = [(1, "2031-10-05", "Hostinger & Razorpay", "Payment successful for Madeup Retail Pvt", "", 370000, 0, "g1"),
      (2, "2031-10-06", "Agilus (NK Pathology)", "Invoice for N K PATHOLOGY", "", 35000, 1, "g2"),
      (3, "2031-10-15", "Apple", "Your receipt from Apple.", "", 2110170, 0, "g4"),
      (4, "2031-10-20", "Airtel", "Here's your Airtel payment receipt!", "", 291433, 1, "g6"),
      (5, "2031-10-28", "Madeup Hotel", "Your order confirmation", "", 150000, 0, "g7"),
      (6, "2031-10-29", "Madeup Steel", "Invoice for construction material, a long description that needs wrapping to be read on one screen", "", 1234567800, 0, "g8"),
      (7, "2031-10-30", "Madeup Power", "Here's your payment receipt!", "", 0, 1, "g9"),                       # no amount read: 'see the receipt'
      (8, "2031-10-31", "Madeup Refund", "Invoice credit note", "", -250000, 0, "g10"),
      (9, "2031-10-31", "Madeup Builders", "Invoice for the October work", "", 45000000, 0, "g11")]                   # a lakh-size amount                      # a negative: the minus must show
con.executemany("INSERT INTO payment_register VALUES (?,?,?,?,?,?,?,?)", pr)
con.commit()
M = "2031-10"

# ---- A. sheet 7's layout
b, why = p.build_digest(con, M)
chk("A0 the digest builds", bool(b), why)
try:
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(b or b""))
    ws = wb.worksheets[0]
    chk("A1 two sheets: the papers and NK Pathology's", len(wb.worksheets) == 2 and wb.worksheets[1].title.startswith("NK Pathology"), [w.title for w in wb.worksheets])
    chk("A2 the header row (row 2) is frozen", str(ws.freeze_panes) == "A3", ws.freeze_panes)
    chk("A3 the title row is merged across the sheet", any(str(r) == "A1:F1" for r in ws.merged_cells.ranges), [str(r) for r in ws.merged_cells.ranges])
    chk("A4 column widths set (description wide)", (ws.column_dimensions["C"].width or 0) >= 40 and (ws.column_dimensions["B"].width or 0) >= 20, (ws.column_dimensions["B"].width, ws.column_dimensions["C"].width))
    hdr = [c.value for c in ws[2]]
    chk("A5 the header row is bold, shaded and wraps", all(c.font.bold for c in ws[2]) and ws["A2"].fill.fgColor.rgb.endswith("E7E6E6") and ws["E2"].alignment.wrap_text, hdr)
    chk("A6 the header is filtered (not the TOTAL row)", bool(ws.auto_filter.ref) and ws.auto_filter.ref.startswith("A2:F") and not ws.auto_filter.ref.endswith(str(ws.max_row)), ws.auto_filter.ref)
    a3 = ws["A3"]
    import datetime as dt
    chk("A7 dates are real dates, shown dd-mmm-yyyy", isinstance(a3.value, (dt.date, dt.datetime)) and a3.number_format == "dd-mmm-yyyy", (type(a3.value).__name__, a3.number_format))
    d3 = ws["D3"]
    chk("A8 money is Rs with Indian grouping (the lakh form for a lakh-size amount)", isinstance(d3.value, (int, float)) and d3.number_format == '"₹ "#,##0.00' and any(c.number_format == '"₹ "##\\,##\\,##0.00' for c in ws["D"] if isinstance(c.value, (int, float)) and 1e5 <= abs(c.value) < 1e7), (d3.value, d3.number_format))
    chk("A9 the description wraps", ws["C3"].alignment.wrap_text and ws["C3"].alignment.vertical == "top", ws["C3"].alignment.wrap_text)
    last = ws[ws.max_row]
    chk("A10 the TOTAL row is bold and summed with the money format", any(str(c.value or "").startswith("TOTAL") for c in last) and all(c.font.bold for c in last) and "₹" in ws.cell(row=ws.max_row, column=4).number_format, [c.value for c in last])
    big = [c for c in ws["D"] if isinstance(c.value, (int, float)) and c.value > 1e7]
    chk("A11 a crore-size amount gets the crore form", big and big[0].number_format == '"₹ "##\\,##\\,##\\,##0.00', [(c.value, c.number_format) for c in big])
    neg = [c for c in ws["D"] if isinstance(c.value, (int, float)) and c.value < 0]
    chk("A11b a negative amount keeps its sign (a one-section format)", neg and not neg[0].number_format.startswith("[") and ";" not in neg[0].number_format, [(c.value, c.number_format) for c in neg])
    nk = wb.worksheets[1]
    chk("A12 NK Pathology's sheet alike: frozen, dated, money", str(nk.freeze_panes) == "A3" and nk["A3"].number_format == "dd-mmm-yyyy" and "₹" in nk["D3"].number_format, (nk.freeze_panes, nk["A3"].number_format))
    seen = [c for c in ws["D"] if c.value == "see the receipt"]
    chk("A13 'see the receipt' stays text in the money column, General format", seen and seen[0].number_format == "General" and seen[0].alignment.horizontal == "right", [(c.value, c.number_format) for c in ws["D"]])
except Exception as e:                                   # noqa: BLE001
    chk("A-fail the sheet could be read", False, "%s: %s" % (type(e).__name__, e))

# ---- B. the other sheets are written as before (the plain writer untouched)
b2, _w = p.build_card_sheet(con, M) if hasattr(p, "build_card_sheet") else (None, None)
chk("B1 the plain writer still there and unchanged in shape", callable(getattr(p, "_xlsx", None)) and p._xlsx([("t", [("a", "b"), (1, 2)])])[:2] == b"PK")

# ---- C. the page's links
html = open(os.path.join(d, "packs.html"), encoding="utf-8").read()
chk("C1 the page builds its xlsx links through dlink", "function dlink(" in html and "function isxl(" in html and "function dlnote(" in html)
chk("C2 no xlsx preview link is built with target=_blank any more", not re.search(r'preview/(cards|income|upi|digest|bankcheck)[^<]*target="_blank"', html) and 'dlink(r.preview' in html and "preview/digest?month='+j.month,'the sheet')" in html)
chk("C3 the xlsx link carries the download attribute and the note", 'download onclick="dlnote(this)"' in html and "Downloads folder" in html)
chk("C4 PDFs and pages still open a tab", "neft_letter?month='+j.month+'\" target=\"_blank\"" in html and 'preview/bundle_\'+r.key.slice(7)+\'?month=\'+j.month+\'" target="_blank"' in html)
chk("C5 the xlsx test names only the five sheets", "(cards|income|upi|digest|bankcheck)" in html)
chk("C6 the kit adds no dialog (F-1464): two confirm( (the Send button) and eleven alert( as before, none in dlink/dlnote", html.count("confirm(") == 2 and html.count("alert(") == 11 and "confirm(" not in html[html.find("function isxl"):html.find("function post(")] and "alert(" not in html[html.find("function isxl"):html.find("function post(")])

# ---- D. the page and the route, for the owner, through the app
try:
    import flask
    app = flask.Flask("w877")
    p.init(app, lambda: sqlite3.connect(os.environ["FINANCE_DB"]), lambda *a, **kw: ({"user": "manoj"}, None))
    cl = app.test_client()
    r = cl.get("/finance/packs?month=" + M)
    page = r.get_data(as_text=True)
    chk("D1 the page renders for the owner with dlink", r.status_code == 200 and "function dlink(" in page, r.status_code)
    r = cl.get("/finance/packs/preview/digest?month=" + M)
    cd = r.headers.get("Content-Disposition", "")
    chk("D2 the digest route answers an attachment xlsx", r.status_code == 200 and cd.startswith("attachment") and "Payment digest" in cd, (r.status_code, cd))
    from openpyxl import load_workbook as lw2
    chk("D3 ... laid out (frozen header)", str(lw2(io.BytesIO(r.data)).worksheets[0].freeze_panes) == "A3")
except Exception as e:                                   # noqa: BLE001
    chk("D0 the page and route could be tried", False, "%s: %s" % (type(e).__name__, e))
print("WALK %d/%d" % (ok, n))
sys.exit(0 if ok == n else 1)
