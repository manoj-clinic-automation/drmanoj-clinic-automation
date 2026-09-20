#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_s343.py -- kit S343_NEAR_EXPIRY (S274, Sanjeevni).

    python3 -B selftest_s343.py [--spine-dir /root/finance/spine] [--ingest /root/marg_ingest] [--archive /root/marg_ingest/archive]

The reader on a synthetic export in Marg's exact shape (written by the stdlib as .xlsx, read through the
router's own opener): units arithmetic incl. the negative sign rule, the TOTAL witness, the serial run; made
to fail on purpose three ways (TOTAL altered, a row removed, a row that is not an item).  Then the nightly
run on a scratch spine (the spine's own SCHEMA) and a scratch archive: EXPIRED / NEAR / LATER by the date
given, the spine's stock beside each batch, the sale-line cross-check, the overdue flag, the OFF flag.
When a real archive is present, its newest export must read OK.  Nothing outside the scratch folder is touched.
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS, FAILED = [], []


def ck(name, cond, detail=""):
    CHECKS.append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (("  -- " + str(detail)[:200]) if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def xlsx(path, rows):
    def cell(r, c, v):
        col, n = "", c + 1
        while n:
            n, rem = divmod(n - 1, 26)
            col = chr(65 + rem) + col
        ref = "%s%d" % (col, r + 1)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return '<c r="%s"><v>%s</v></c>' % (ref, v)
        s = str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return '<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, s)
    body = "".join('<row r="%d">%s</row>' % (i + 1, "".join(cell(i, j, v) for j, v in enumerate(row) if v not in ("", None))) for i, row in enumerate(rows))
    sheet = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>%s</sheetData></worksheet>' % body
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", sheet)


HEAD = [["SANJEEVNI MEDICOS"], ["35G/15B , RAMPUR BAGH BAREILLY"], ["Phone : x"], ["D.L.No. : x"], ["GSTIN : x"], [""],
        ["EXP. BEFORE *BA., 0"], ["S.No. Description", "Batch", "Expiry", "Stock Unit"]]
ITEMS = [["   1 ALPHA TAB                      1*10", "B1", "10/2026", "  2:3 STR"],   # 23 units, +1 month from 2026-09-20
         ["   2 BETA INJ                       1*1", "B2", "8/2026", "    4 INJ"],       # 4 units, expired
         ["   3 GAMMA SYP                      1*1", "G3", "12/2026", "    2 BOX"],      # 2 units, +3 months = NEAR (edge)
         ["   4 DELTA CAP                      1*15", "D4", "1/2027", " -1:2 STR"],     # -(15+2) = -17, +4 months = LATER
         ]
FOOT = [["TOTAL", "", "", 12.0], ["Our Software MARG Erp 1234"]]        # 23 + 4 + 2 - 17 = 12


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine-dir", default="/root/finance/spine")
    ap.add_argument("--ingest", default="/root/marg_ingest")
    ap.add_argument("--archive", default="/root/marg_ingest/archive")
    a = ap.parse_args(argv)
    td = tempfile.mkdtemp(prefix="s343_")
    ne = load(os.path.join(HERE, "near_expiry.py"), "near_expiry_s343")
    ne.INGEST = a.ingest
    sb = load(os.path.join(a.spine_dir, "spine_build.py"), "spine_build_for_s343")
    arch = os.path.join(td, "archive", "STOCK_EXPIRY", "2026-09")
    os.makedirs(arch)
    good = os.path.join(arch, "STOCK_EXPIRY_DEFAULT__2026-09-01__20260901-080000__aaaaaaaa.xlsx")
    xlsx(good, HEAD + ITEMS + FOOT)
    R = ne.read_expiry(good)
    ck("the reader reads Marg's shape: 4 rows, OK, as on 2026-09-01", R["ok"] and R["n"] == 4 and R["as_on"] == "2026-09-01", (R["failed"], R["n"]))
    u = {it["name"]: it["units"] for it in R["items"]}
    ck("units arithmetic: 2:3 of 1*10 = 23 · 4 INJ = 4 · 2 BOX = 2 · -1:2 of 1*15 = -17", u == {"ALPHA TAB": 23, "BETA INJ": 4, "GAMMA SYP": 2, "DELTA CAP": -17}, u)
    ck("expiry read as YYYY-MM and the batch as printed", R["items"][0]["expiry"] == "2026-10" and R["items"][0]["batch"] == "B1")
    bad1 = os.path.join(td, "bad1.xlsx")
    xlsx(bad1, HEAD + ITEMS + [["TOTAL", "", "", 13.0]] + FOOT[1:])
    ck("NEGATIVE: TOTAL altered by one unit -> the witness fails", not ne.read_expiry(bad1)["ok"] and "TOTAL = sum" in " ".join(ne.read_expiry(bad1)["failed"]))
    bad2 = os.path.join(td, "bad2.xlsx")
    xlsx(bad2, HEAD + ITEMS[:1] + ITEMS[2:] + [["TOTAL", "", "", 8.0]] + FOOT[1:])
    r2 = ne.read_expiry(bad2)
    ck("NEGATIVE: a row removed -> the serial run breaks even though the total was made to add", not r2["ok"] and "serial" in " ".join(r2["failed"]))
    bad3 = os.path.join(td, "bad3.xlsx")
    xlsx(bad3, HEAD + ITEMS + [["   5 EPSILON", "E5", "next year", "some"]] + [["TOTAL", "", "", 12.0]] + FOOT[1:])
    r3 = ne.read_expiry(bad3)
    ck("NEGATIVE: a row that is not an item is an anomaly -> every-row-classified fails", not r3["ok"] and "classified" in " ".join(r3["failed"]))
    # the nightly run on a scratch spine
    db = os.path.join(td, "spine.db")
    con = sqlite3.connect(db)
    con.executescript(sb.SCHEMA)
    con.execute("INSERT INTO sp_meta VALUES ('built','2026-09-20T09:00:00+05:30')")
    for k, u0 in (("ALPHA TAB", 44.0), ("BETA INJ", 0.0), ("GAMMA SYP", 2.0), ("DELTA CAP", 30.0), ("ZETA OINT", 6.0)):
        con.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (k, "2026-09-01", "opening", u0, "t"))
    con.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("2026-09-10", "A1", 1, "ZETA OINT", "ZETA OINT", "1*1", "1", 1.0, 5000, "Z9", "11/26"))
    con.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("2026-09-11", "A2", 1, "ALPHA TAB", "ALPHA TAB", "1*10", "0:2", 2.0, 1000, "B1", "10/2026"))
    con.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("2026-09-11", "A2", 2, "BETA INJ", "BETA INJ", "1*1", "1", 1.0, 1000, "B2", "8/2026"))
    con.commit()
    con.close()
    out = os.path.join(td, "expiry")
    today = dt.date(2026, 9, 20)
    logs = []
    rc = ne.run(os.path.join(td, "archive"), db, out, today, log=logs.append)
    j = json.load(open(os.path.join(out, "near_expiry_2026-09-20.json")))
    st = {r["name"]: r["status"] for r in j["rows"]}
    ck("the run writes the file: BETA EXPIRED · ALPHA and GAMMA NEAR (+1, +3 months) · DELTA LATER (+4)",
       rc == 0 and st == {"BETA INJ": "EXPIRED", "ALPHA TAB": "NEAR", "GAMMA SYP": "NEAR", "DELTA CAP": "LATER"}, st)
    sp = {r["name"]: r["spine_stock_today"] for r in j["rows"]}
    ck("the spine's stock today sits beside each batch (ALPHA 44, BETA 0)", sp["ALPHA TAB"] == 44.0 and sp["BETA INJ"] == 0.0, sp)
    ck("the export is 19 days old, not overdue", j["export"]["age_days"] == 19 and not j["export"]["overdue"], j["export"])
    fs = {r["name"]: r for r in j["from_sales"]}
    ck("the sale-line cross-check finds ZETA (batch Z9, 11/26, 6 in stock, NOT in the export) and ALPHA (in the export), not BETA (no stock)",
       set(fs) == {"ZETA OINT", "ALPHA TAB"} and not fs["ZETA OINT"]["in_export"] and fs["ALPHA TAB"]["in_export"] and fs["ZETA OINT"]["expiry"] == "2026-11", fs)
    txt = open(os.path.join(out, "near_expiry_latest.txt")).read()
    ck("the text names the window and the voucher rule, and lists the NOT IN EXPORT batch", "D409" in txt and "voucher (R6)" in txt and "NOT IN EXPORT" in txt)
    rc = ne.run(os.path.join(td, "archive"), db, out, dt.date(2026, 10, 10), log=logs.append)
    j2 = json.load(open(os.path.join(out, "near_expiry_2026-10-10.json")))
    ck("on 10-Oct the export is 39 days old -> OVERDUE, and ALPHA (10/2026) reads +0 months NEAR, GAMMA +2", j2["export"]["overdue"]
       and {r["name"]: r["months_left"] for r in j2["rows"]}["ALPHA TAB"] == 0, j2["export"])
    shutil.rmtree(os.path.join(td, "archive"))
    os.makedirs(os.path.join(td, "archive"))
    rc = ne.run(os.path.join(td, "archive"), db, out, today, log=logs.append)
    ck("NEGATIVE: no export kept -> the file says so and nothing crashes", rc == 0 and "NO EXPIRY EXPORT KEPT" in open(os.path.join(out, "near_expiry_latest.txt")).read())
    ne.OFF_FLAGS = (os.path.join(td, "OFF"),)
    open(os.path.join(td, "OFF"), "w").close()
    logs2 = []
    ck("NEGATIVE: the OFF flag stops the run", ne.run(os.path.join(td, "archive"), db, out, today, log=logs2.append) == 0 and "switched off" in logs2[0])
    ck("no 10-digit number in the written file (F-185)", not __import__("re").search(r"(?<!\d)[6-9]\d{9}(?!\d)", txt))
    real = ne.newest_export(a.archive) if os.path.isdir(a.archive) else None
    if real:
        RR = ne.read_expiry(real)
        ck("the newest REAL export on this box reads OK (%s: %d rows, TOTAL %s)" % (os.path.basename(real)[:40], RR["n"], RR["printed_total"]), RR["ok"], RR["failed"])
    else:
        print("   (no real STOCK_EXPIRY export under %s -- the real-file check did not run)" % a.archive)
    shutil.rmtree(td, ignore_errors=True)
    print("selftest: %d/%d" % (len(CHECKS) - len(FAILED), len(CHECKS)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
