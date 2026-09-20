#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_s336.py -- kit S336_QUARANTINE (S274, Sanjeevni).  The whole door, in a scratch copy.

    python3 -B selftest_s336.py --ingest-src /root/marg_ingest [--kit DIR]

Builds a scratch marg_ingest (a copy of the live folder's *.py, lib/, xlrd if vendored, signatures.json),
overlays this kit's four files, points the door at a scratch archive and a scratch finance.db, and pushes
synthetic Marg-shaped .xlsx files (written by the stdlib -- inline strings, no library) through
marg_take.take().  Nothing outside the scratch folder is touched, except the door's own lock file.
Ends with 'selftest: N/N' and exit 0, or lists the failures and exits 1.  Made to fail on purpose:
the last two checks run phi_scan on a file that MUST be refused and a rescan that MUST do nothing.
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import zipfile

CHECKS, FAILED = [], []


def ck(name, cond, detail=""):
    CHECKS.append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (("  -- " + str(detail)[:160]) if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


def xlsx(path, rows):
    """A minimal .xlsx: one sheet, inline strings and numbers -- exactly what xlsx_stdlib reads."""
    def cell(r, c, v):
        col = ""
        n = c + 1
        while n:
            n, rem = divmod(n - 1, 26)
            col = chr(65 + rem) + col
        ref = "%s%d" % (col, r + 1)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return '<c r="%s"><v>%s</v></c>' % (ref, v)
        s = str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return '<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, s)
    body = "".join('<row r="%d">%s</row>' % (i + 1, "".join(cell(i, j, v) for j, v in enumerate(row) if v not in ("", None)))
                   for i, row in enumerate(rows))
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>%s</sheetData></worksheet>' % body)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '</Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   '</Relationships>')
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                   '</Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return open(path, "rb").read()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ingest-src", default="/root/marg_ingest")
    ap.add_argument("--kit", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--keep", action="store_true", help="leave the scratch folder for a look")
    a = ap.parse_args(argv)
    td = tempfile.mkdtemp(prefix="s336_selftest_")
    ing = os.path.join(td, "marg_ingest")
    os.makedirs(ing)
    for n in os.listdir(a.ingest_src):
        p = os.path.join(a.ingest_src, n)
        if n.endswith(".py") or n == "signatures.json":
            shutil.copy2(p, ing)
        elif n in ("lib", "xlrd") and os.path.isdir(p):
            shutil.copytree(p, os.path.join(ing, n))
    for n in ("marg_take.py", "phi_scan.py", "marg_rescan.py", "marg_rescan_vps.py"):
        shutil.copy2(os.path.join(a.kit, n), ing)
    os.makedirs(os.path.join(ing, "work"))
    archive = os.path.join(td, "archive")
    db = os.path.join(td, "finance.db")
    sys.path.insert(0, ing)
    import marg_ingest as MI                                     # noqa: PLC0415
    import marg_take as MT                                       # noqa: PLC0415
    import marg_rescan as RS                                     # noqa: PLC0415
    import marg_rescan_vps as RV                                 # noqa: PLC0415
    import phi_scan                                              # noqa: PLC0415
    ck("the scratch door is this kit's (SOURCES has 'rescan', _quarantine_clean present)",
       "rescan" in MT.SOURCES and hasattr(MT, "_quarantine_clean") and MT.__file__.startswith(ing))
    con = sqlite3.connect(db)
    con.executescript(MI.SCHEMA)
    con.commit()
    con.close()
    sigs_path = os.path.join(ing, "signatures.json")
    RS.remember_signatures(os.makedirs(archive, exist_ok=True) or archive, RS.signatures_changed(archive, sigs_path)[1])

    def take(name, rows):
        raw = xlsx(os.path.join(td, name), rows)
        return MT.take(raw, name=name, source="test", db=db, archive=archive), raw

    def row(md5):
        cx = sqlite3.connect(db)
        try:
            r = cx.execute("SELECT type, verdict, kept, reason, server_name FROM mi_file WHERE md5=?", (md5,)).fetchone()
        finally:
            cx.close()
        return r

    def quarantine():
        return sorted(os.path.basename(p) for p in RS.quarantined_files(archive))

    def sidecar(name8):
        for q in RS.QUARANTINE + ("_rescued",):
            d = os.path.join(archive, q)
            if os.path.isdir(d):
                for n in os.listdir(d):
                    if n.endswith(".txt") and name8 in n:
                        return open(os.path.join(d, n), encoding="utf-8").read()
        return ""

    head = [["SANJEEVNI MEDICOS"], ["TEST WISE ITEM LIST"], [""], ["S.No. DESCRIPTION", "PACKING", "Compnay"]]
    # a mobile-shaped fixture, assembled at run time so no 10-digit run sits in the repository (F-185)
    MOB_TXT = "98" + "7654" + "3210"
    MOB_NUM = float("91" + "2345" + "6789")
    items = [["1 AB TABLET", "1*10", "ACME"], ["2 CD SYRUP", "100ML", "BETA"], ["3 EF CAP", "1*15", "GAMMA"]]

    # 1. an unknown report with no person's detail -> kept in quarantine
    r1, raw1 = take("REPORT_1.xlsx", head + items)
    ck("an unrecognised report is TAKEN and not VERIFIED (the router: UNKNOWN title, no dates -> REFUSED)", r1["status"] == "TAKEN" and r1["verdict"] in ("UNKNOWN", "REFUSED"), r1)
    ck("... and KEPT (kept=1) in archive/_UNKNOWN", r1["kept"] == 1 and any("_UNKNOWN" in p for p in RS.quarantined_files(archive)), quarantine())
    ck("... the mi_file row says kept=1", row(r1["md5"]) and row(r1["md5"])[2] == 1, row(r1["md5"]))
    ck("... the router's sidecar carries 'kept: yes'", "kept: yes" in sidecar(r1["md5"][:8]), sidecar(r1["md5"][:8])[-200:])

    # 2. the same shape with a mobile number in a cell -> not kept
    r2, _ = take("REPORT_2.xlsx", head + items + [["4 GH INJ", "1*1", MOB_TXT]])
    ck("a file carrying a mobile-shaped number is TAKEN, UNKNOWN, and NOT kept", r2["status"] == "TAKEN" and r2["kept"] == 0
       and not any(r2["md5"][:8] in p for p in RS.quarantined_files(archive)), r2)
    ck("... its sidecar says 'kept: no' and why", "kept: no" in sidecar(r2["md5"][:8]) and "mobile" in sidecar(r2["md5"][:8]), sidecar(r2["md5"][:8])[-200:])
    r2b, _ = take("REPORT_2b.xlsx", head + items + [["4 GH INJ", "1*1", MOB_NUM]])
    ck("... a mobile in a NUMERIC cell is caught too", r2b["kept"] == 0, r2b)

    # 3. a sale-family title whose layout does not match -> REFUSED and not kept (names people)
    r3, _ = take("REPORT_3.xlsx", [["SANJEEVNI MEDICOS"], ["BILL WISE SALES STATEMENT AS ON 15-09-2026"], [""],
                                   ["BILL NO.", "SOMETHING", "ELSE"], ["A000001", "x", 1.0]])
    ck("a sale report with a strange layout is REFUSED and NOT kept", r3["status"] == "TAKEN" and r3["verdict"] != "VERIFIED" and r3["kept"] == 0
       and not any(r3["md5"][:8] in p for p in RS.quarantined_files(archive)), r3)

    # 4. the same bytes again -> ALREADY, still kept
    r4 = MT.take(raw1, name="REPORT_1.xlsx", source="test", db=db, archive=archive)
    ck("the same bytes again answer ALREADY with kept=1", r4["status"] == "ALREADY" and r4["kept"] == 1, r4)

    # 5. rescan with unchanged signatures does nothing
    out = []
    rc = RV.run(argparse.Namespace(archive=archive, sigs=sigs_path, db=db, apply=True, if_changed=True, status=False), log=out.append)
    ck("rescan --if-signatures-changed with unchanged signatures does nothing", rc == 0 and any("unchanged" in l for l in out)
       and len(quarantine()) == 1, out)
    out = []
    RV.run(argparse.Namespace(archive=archive, sigs=sigs_path, db=db, apply=False, if_changed=False, status=True), log=out.append)
    ck("--status counts the one kept file", any("1 file(s) kept" in l for l in out), out)

    # 6. a signature is added for the test report -> the rescan rescues it, and the door re-takes it
    sigs = json.load(open(sigs_path, encoding="utf-8"))
    sigs["signatures"].append({"type": "TEST_LIST", "variant": "DEFAULT", "title_regex": r"TEST\s+WISE\s+ITEM\s+LIST",
                               "header": ["S.No. DESCRIPTION", "PACKING", "Compnay"], "dating": "file_mtime",
                               "deep_verify": "structural", "uploadable": False, "_note": "S336 selftest only"})
    json.dump(sigs, open(sigs_path, "w", encoding="utf-8"), indent=1)
    time.sleep(1.1)
    out = []
    rc = RV.run(argparse.Namespace(archive=archive, sigs=sigs_path, db=db, apply=True, if_changed=True, status=False), log=out.append)
    print("\n".join("      " + l for l in out[-6:]))
    typed = [p for p in __import__("glob").glob(os.path.join(archive, "TEST_LIST", "*", "*.xlsx"))]
    ck("after the signature lands, the rescan rescues the kept file into archive/TEST_LIST/", rc == 0 and len(typed) == 1, typed)
    rr = row(r1["md5"])
    ck("... and the door re-took it: mi_file now VERIFIED, type TEST_LIST, kept=1", rr and rr[1] == "VERIFIED" and rr[0] == "TEST_LIST" and rr[2] == 1, rr)
    ck("... quarantine is empty of files; _rescued/ keeps the sidecar only",
       quarantine() == [] and all(n.endswith(".txt") for n in os.listdir(os.path.join(archive, "_rescued"))) if os.path.isdir(os.path.join(archive, "_rescued")) else quarantine() == [],
       (quarantine(), os.listdir(os.path.join(archive, "_rescued")) if os.path.isdir(os.path.join(archive, "_rescued")) else "no _rescued"))
    ck("... the rescan remembered the signatures it judged with (a second run does nothing)",
       RV.run(argparse.Namespace(archive=archive, sigs=sigs_path, db=db, apply=True, if_changed=True, status=False), log=out.append) == 0
       and "unchanged" in out[-1])

    # 7. a VERIFIED, kept type is untouched by all this (the normal path)
    r7, _ = take("REPORT_7.xlsx", [["SANJEEVNI MEDICOS"], ["LIST OF ITEMS"], [""], ["S.No. DESCRIPTION", "PACKING", "Compnay"]] + items)
    ck("a real item master still verifies and is kept in its type folder, as before", r7["status"] == "TAKEN" and r7["verdict"] == "VERIFIED"
       and r7["type"] == "ITEM_MASTER" and r7["kept"] == 1, r7)

    # 8. made to fail on purpose
    bad = os.path.join(td, "must_refuse.xlsx")
    xlsx(bad, [["PATIENT WISE LIST"], ["S.No. DESCRIPTION", "PACKING", "Compnay"]] + items)
    ok, why = phi_scan.clean(bad)
    ck("NEGATIVE: phi_scan refuses a preamble that names people", not ok and "PATIENT" in why, why)
    ok, why = phi_scan.clean(os.path.join(td, "nothing.pdf"))
    ck("NEGATIVE: phi_scan refuses a PDF without opening it", not ok and "PDF" in why, why)
    empty = os.path.join(td, "empty.xlsx")
    xlsx(empty, [[""]])
    ok, why = phi_scan.clean(empty)
    ck("NEGATIVE: phi_scan refuses an empty sheet", not ok, why)
    ok, why = phi_scan.clean(os.path.join(td, "REPORT_1.xlsx"))
    ck("phi_scan passes the clean report", ok, why)

    print("selftest: %d/%d" % (len(CHECKS) - len(FAILED), len(CHECKS)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    if a.keep:
        print("   scratch kept at %s" % td)
    else:
        shutil.rmtree(td, ignore_errors=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
