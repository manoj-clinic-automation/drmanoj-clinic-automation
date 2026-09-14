# -*- coding: utf-8 -*-
"""S267 LIVE-SHAPE WALK -- the workbook is opened and read back, not trusted.

The file is generated, unzipped, and its sheet XML parsed with the standard
library: the sheet's name, its merges, its column widths, its headers, every
line, the account numbers' type, the amounts, and the total formula with its
cached value -- all held to the bank's own sheets and to the advice on the page.

    python3 walk_s267.py --file <patched> --before <backup> --db <copy.db>
"""
import argparse
import importlib.machinery
import importlib.util
import io as _io
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

OK = BAD = 0
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
PARTS = ["[Content_Types].xml", "_rels/.rels", "xl/workbook.xml",
         "xl/_rels/workbook.xml.rels", "xl/styles.xml", "xl/worksheets/sheet1.xml"]
HEADS = ["\nSr. No.", "\nTxn. type", "Credit Account Number", "Credit Account Name",
         "IFSC", "Amount", "Narration"]
WIDTHS = [5.5546875, 8.6640625, 25.109375, 31.88671875, 13.33203125, 10.33203125, 16.0]


def ck(name, cond, detail=""):
    global OK, BAD
    if cond:
        OK += 1
        print("    ok    %s" % name)
    else:
        BAD += 1
        print("    FAIL  %s   %s" % (name, str(detail)[:260]))


def load(path, dbpath, name):
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    import flask
    app = flask.Flask(name)
    holder = {}

    def db():
        if "con" not in holder:
            c = sqlite3.connect(dbpath)
            c.row_factory = sqlite3.Row
            holder["con"] = c
        return holder["con"]

    def require(*roles):
        return {"user": "walk", "role": "checker", "roles": ["checker"]}, None

    mod.init(app, db, require, unit="medical", url_prefix="/finance/purchase")
    return mod, app, db


def cells(sheet_xml):
    """{'A6': ('inlineStr'|'n'|'f', text)} -- read straight out of the XML."""
    root = ET.fromstring(sheet_xml)
    out = {}
    for c in root.iter(NS + "c"):
        ref = c.get("r")
        f = c.find(NS + "f")
        if f is not None:
            v = c.find(NS + "v")
            out[ref] = ("f", (f.text or "", v.text if v is not None else None))
            continue
        t = c.get("t")
        if t == "inlineStr":
            node = c.find(NS + "is/" + NS + "t")
            out[ref] = ("s", node.text if node is not None else "")
        else:
            v = c.find(NS + "v")
            out[ref] = ("n", v.text if v is not None else None)
    return out, root


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args(argv)
    tmp = tempfile.mkdtemp(prefix="s267_")
    db_b, db_a = os.path.join(tmp, "b.db"), os.path.join(tmp, "a.db")
    shutil.copy(a.db, db_b)
    shutil.copy(a.db, db_a)
    old, app0, dbf0 = load(a.before, db_b, "pa_before")
    new, app1, dbf1 = load(a.file, db_a, "pa_after")
    c0, c1 = app0.test_client(), app1.test_client()
    with app1.test_request_context("/"):
        months = new._months(dbf1(), 6)
    ck("the database has months of purchases", bool(months), months)
    if not months:
        print("\n%d ok, %d failed" % (OK, BAD))
        return 1

    ck("BEFORE: there was no file to download",
       c0.get("/finance/purchase/page/pay/%s/advice.xlsx" % months[0]).status_code == 404)

    for m in months[:2]:
        r = c1.get("/finance/purchase/page/pay/%s/advice.xlsx" % m)
        ck("%s: the file downloads" % m, r.status_code == 200, r.status_code)
        blob = r.get_data()
        ck("%s: it is sent as a spreadsheet, as an attachment" % m,
           "spreadsheetml.sheet" in (r.headers.get("Content-Type") or "")
           and "attachment;" in (r.headers.get("Content-Disposition") or ""),
           r.headers.get("Content-Type"))
        with app1.test_request_context("/"):
            want = new._advice_filename_s267(m)
            rows, total, missing, paise = new._advice_rows_s265(dbf1(), m)
            s, groups = new._pay_rows(dbf1(), m)
        ck("%s: it is named the way these files are named (%s)" % (m, want),
           want in (r.headers.get("Content-Disposition") or ""))

        # ---- it really is a workbook ------------------------------------
        try:
            z = zipfile.ZipFile(_io.BytesIO(blob))
            bad = z.testzip()
            names = z.namelist()
        except Exception as e:
            ck("%s: it opens as a workbook" % m, False, e)
            continue
        ck("%s: it opens as a workbook, every part intact" % m, bad is None)
        ck("%s: all six parts a workbook needs are there" % m,
           all(p in names for p in PARTS), [p for p in PARTS if p not in names])
        wb = z.read("xl/workbook.xml").decode("utf-8")
        ck("%s: the sheet is named Sheet2, as every file since April is" % m,
           'name="Sheet2"' in wb)
        sx = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        cl, root = cells(sx)

        # ---- the letterhead and the merges -------------------------------
        ck("%s: the four letterhead lines are there" % m,
           cl["A1"][1].startswith("GSTIN:") and cl["A2"][1].startswith("DL NO.")
           and cl["A3"][1] == "SANJEEVNI MEDICOS" and "Rampur Bagh" in cl["A4"][1])
        merges = sorted(x.get("ref") for x in root.iter(NS + "mergeCell"))
        ck("%s: merged the same way (A1:C1, A3:G3, A4:G4)" % m,
           merges == ["A1:C1", "A3:G3", "A4:G4"], merges)

        # ---- the seven headers, and the columns they sit in --------------
        got = [cl.get("%s5" % chr(65 + i), ("", ""))[1] for i in range(7)]
        ck("%s: the seven headers, in the bank's order and wording" % m, got == HEADS, got)
        w = [float(x.get("width")) for x in root.iter(NS + "col")]
        ck("%s: the column widths are the bank's own" % m, w == WIDTHS, w)
        ps = [x for x in root.iter(NS + "pageSetup")]
        ck("%s: A4 landscape, fit to the page" % m,
           bool(ps) and ps[0].get("orientation") == "landscape"
           and ps[0].get("paperSize") == "9",
           [x.attrib for x in ps])

        # ---- the lines -----------------------------------------------------
        n = len(rows)
        ck("%s: one row per advice line, starting at row 6 (%d)" % (m, n),
           all(("A%d" % (6 + i)) in cl for i in range(n))
           and all(cl["A%d" % (6 + i)][0] == "n" for i in range(n))
           and ("A%d" % (7 + n)) not in cl,
           sorted(k for k in cl if k.startswith("A"))[-3:])
        ck("%s: and the row after the last line is the total row, nothing more" % m,
           cl.get("A%d" % (6 + n), ("", ""))[1] in ("", None)
           and ("B%d" % (7 + n)) not in cl)
        ck("%s: every account number is TEXT, so a leading zero survives" % m,
           all(cl["C%d" % (6 + i)][0] == "s" for i in range(n))
           and all(cl["C%d" % (6 + i)][1] == rows[i]["acct"] for i in range(n)),
           [cl["C%d" % (6 + i)] for i in range(min(2, n))])
        ck("%s: every amount is a NUMBER, equal to the sheet's payable" % m,
           all(cl["F%d" % (6 + i)][0] == "n"
               and int(cl["F%d" % (6 + i)][1]) == rows[i]["rupees"] for i in range(n)))
        ck("%s: every name and IFSC is the one on the account row" % m,
           all(cl["D%d" % (6 + i)][1] == rows[i]["name"]
               and cl["E%d" % (6 + i)][1] == rows[i]["ifsc"] for i in range(n)))
        ck("%s: every line says NEFT and Vendor Payment" % m,
           all(cl["B%d" % (6 + i)][1] == "NEFT" for i in range(n))
           and all(cl["G%d" % (6 + i)][1] == "Vendor Payment" for i in range(n)))

        # ---- the total is a real formula, and it already shows ------------
        tr = 6 + n
        kind, val = cl.get("F%d" % tr, ("", ("", "")))
        ck("%s: the total is a real =SUM() over its own lines" % m,
           kind == "f" and val[0] == "SUM(F6:F%d)" % (tr - 1), val)
        ck("%s: and its value is cached, so it shows without recalculating" % m,
           kind == "f" and val[1] is not None and int(val[1]) == total, val)

        # ---- what must never be in the file --------------------------------
        cheq = [g["name"] for g in groups if g["route"] != "NEFT"]
        ck("%s: no cheque vendor is in the file (%d on cheques)" % (m, len(cheq)),
           not any(name in sx for name in cheq), [x for x in cheq if x in sx])
        ck("%s: nobody without a confirmed account is in it" % m,
           not any(name in sx for name in missing), missing)

    # ---- the way in ----------------------------------------------------------
    h = c1.get("/finance/purchase/page/pay/" + months[0]).get_data(as_text=True)
    ck("the advice card offers the download", "advice.xlsx" in h
       and "Download the file for the email" in h)
    ck("and still offers the print", 'onclick="window.print()"' in h)
    ck("neither button is itself printed", h.count("noprint") >= 2)

    # ---- nothing else moved ---------------------------------------------------
    for page in ("hub", "scans", "orders", "book", "month/" + months[0]):
        r1, r0 = (c1.get("/finance/purchase/page/" + page),
                  c0.get("/finance/purchase/page/" + page))
        ck("/%s is byte-identical to before" % page,
           r1.status_code == 200 and r1.get_data() == r0.get_data(), r1.status_code)
    h0 = c0.get("/finance/purchase/page/pay/" + months[0]).get_data(as_text=True)

    def blk(x, i):
        return x[x.index(i):x.index("</table>", x.index(i))]
    ck("the advice table on the page is unchanged",
       blk(h, 'id="advice_s265"') == blk(h0, 'id="advice_s265"'))
    ck("the covering letter is unchanged",
       h[h.index('id="letter_s266"'):] == h0[h0.index('id="letter_s266"'):])

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d ok, %d failed" % (OK, BAD))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
