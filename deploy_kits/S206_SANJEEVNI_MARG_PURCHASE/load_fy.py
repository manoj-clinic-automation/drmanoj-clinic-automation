#!/usr/bin/python3
"""
load_fy.py — ingest EVERY sale report of the financial year, from both stores.

THE FAULT THIS FIXES
    An earlier pass in this session read only `MargArchive\\SALE_BILLWISE` and
    reported sale coverage as "6.8% of the financial year". The rest was in
    `D:\\Downloads\\MARG REPORTS CLAUDE\\` — the owner's own 15-day and monthly
    exports — and half of those are .xlsx, which the .xls reader cannot open.
    Measuring one folder and reporting it as the system is the F-199/F-200
    fault one layer out.

    Assembled, the bill chain runs A00001..A03215 with ZERO gaps: the whole
    financial year. Both 16-Aug and 23-Aug are Sundays and both boundaries
    join, so no trading day is missing either.
"""

import os
import sys
import glob
import json
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "S205_LIVE_TOOLS", "manojz"))

import marg_report as MR              # live module — read, never modified
import xlsx_sheet

MR._open_sheet = xlsx_sheet.open_sheet_any   # runtime only, this process only


def sale_sources(downloads):
    pats = [os.path.join(downloads, "margsync", "MargArchive", "SALE_BILLWISE", "*", "*.XLS"),
            os.path.join(downloads, "MARG REPORTS CLAUDE", "*.XLS"),
            os.path.join(downloads, "MARG REPORTS CLAUDE", "*.xlsx"),
            os.path.join(downloads, "MARG REPORTS CLAUDE", "SENT", "*.XLS"),
            os.path.join(downloads, "MARG REPORTS CLAUDE", "New folder", "*.XLS")]
    out = []
    for p in pats:
        out += sorted(glob.glob(p))
    return out


def load(downloads):
    seen = set()
    lines, files = [], []
    for p in sale_sources(downloads):
        try:
            rep = MR.read_report(p, keep_items=True)
        except Exception as e:
            files.append({"file": os.path.basename(p), "status": "SKIPPED: %s" % e, "new": 0})
            continue
        if not rep.get("ok"):
            files.append({"file": os.path.basename(p), "status": "NOT OK", "new": 0})
            continue
        n = 0
        for d in rep["days"]:
            for it in d.get("items") or []:
                ps = it.get("parsed") or {}
                key = (it["bill_date"], it["bill_no"], ps.get("seq"))
                if key in seen:
                    continue
                seen.add(key)
                n += 1
                # ⚠ WHOLE-UNIT ITEMS WRITE THE QUANTITY AS A PLAIN NUMBER.
                # A strip line reads  qty='0:1'  (strips:loose).
                # A tube, vial, syringe or spray reads  qty='1.0'  — and the
                # live reader returns qty_strips=None/qty_loose=None for it,
                # because it only understands the strips:loose form.
                # Left alone, EVERY non-strip item shows ZERO sales: 2,807 lines,
                # 16.3% of the year, including 356 BRUTAFLAM GEL and 234 DOLONEX
                # INJ. They then appear as "dead stock" and as unexplained
                # negatives. The number is sitting right there in `qty`.
                strips, loose = ps.get("qty_strips"), ps.get("qty_loose")
                whole = None
                if strips is None and loose is None:
                    try:
                        whole = float(str(it.get("qty", "")).strip())
                    except (TypeError, ValueError):
                        whole = None
                lines.append({"date": it["bill_date"], "bill": it["bill_no"],
                              "item": ps.get("item_name"), "pack": ps.get("pack"),
                              "strips": strips, "loose": loose,
                              "whole": whole, "qty_raw": it.get("qty"),
                              "rate_p": ps.get("amount_p"), "expiry": ps.get("expiry_ym"),
                              "batch": ps.get("batch")})
        files.append({"file": os.path.basename(p), "status": rep.get("title", "ok"), "new": n})
    return lines, files


if __name__ == "__main__":
    dl = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/mnt/Downloads")
    lines, files = load(dl)
    for f in files:
        print("  %-52s +%-6d %s" % (f["file"][:52], f["new"], f["status"][:58]))
    print("\ntotal deduplicated sale item lines : %d" % len(lines))
    print("distinct dates                     : %d" % len({l["date"] for l in lines}))
    json.dump(lines, open(os.path.expanduser("~/fy_sale.json"), "w"))
