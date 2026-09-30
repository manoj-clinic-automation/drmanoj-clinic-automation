#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figures_s440.py -- kit S440_SCAN_FLOW: what reception sees on opening Purchase orders, read through the kit's own porders.scan_work().
The installer runs it on a fresh scratch copy (DRY=1) and, after the first pass of the matcher, on the live database. It prints the
five counts, the lines of "Yahi bill hai?" / "Supplier chuno" / "Amount milao" (supplier, bill number, the scan's stamp -- no person,
no phone, no account), Marg's double entries, and whether the six near-matches the brief names have left "Scan karo".

Usage: figures_s440.py --app <a folder holding porders.py and purchase_app.py> --db finance.db --assets-db assets.db
Exit 0 when the list could be read, 1 otherwise.
"""
import argparse
import os
import sqlite3
import sys

ap = argparse.ArgumentParser()
for k in ("--app", "--db", "--assets-db"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
sys.path.insert(0, a.app)
os.chdir(a.app)
import purchase_app as pa  # noqa: E402
import porders  # noqa: E402

pa._assets_db = a.assets_db
con = sqlite3.connect(a.db, timeout=60)
con.row_factory = sqlite3.Row
porders.ensure_schema(con)
pa._ensure(con)
k = porders.scan_work(con)
if not k.get("ok") or not k.get("reachable"):
    print("S440 figures: the list could not be read (the asset app's database reachable: %s)" % k.get("reachable"))
    sys.exit(1)
c = k["counts"]


def say(line):
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode("ascii"))


say("Scan ka kaam (%d): Scan karo %d · Yahi bill hai? %d · Supplier chuno %d · Amount milao %d · Marg ka intezaar %d (no button, not counted) · second scans %d"
    % (k["n"], c["scan"], c["confirm"], c["vendor"], c["amount"], c["wait"], c["dup"]))
for x in k["scan"]:
    if x.get("double"):
        say("  Scan karo, shown ONCE (Marg mein do baar): %s bill %s" % (" ".join(str(x["vendor"]).split()), " / ".join(x["double_nos"])))
for x in k["confirm"]:
    say("  Yahi bill hai?  scan %s (reads '%s', %s) -> %s bill %s (%s)%s" % (x["stamp"], x["scan_no"] or "nothing", x["scan_amount"], x["vendor"], x["bill_no"], x["amount"],
                                                                           ("  [that bill already has scan %s]" % x["taken_stamp"]) if x.get("taken_by") else ""))
for x in k["vendor"]:
    say("  Supplier chuno  scan %s (number '%s', %s)" % (x["stamp"], x["scan_no"] or "nothing", x["scan_amount"]))
for x in k["amount"]:
    say("  Amount milao    scan %s -> %s bill %s: the scan reads %s, Marg %s" % (x["stamp"], x["vendor"], x["bill_no"], x["scan_amount"], x["amount"]))
REAL6 = [("L.K. DRUG HOUSE", "75904"), ("L.K. DRUG HOUSE", "78354"), ("ESSENTIAL PHARMA", "EP002243"), ("SAISUN PHARMA PVT. LTD", "IP006767"),
         ("A.A. PHARMACEUTICALS", "416"), ("KEDAR PHARMACEUTICAL", "189")]
found = in_scan = in_confirm = linked = 0
for sup, bno in REAL6:
    r = con.execute("SELECT b.id FROM purchase_bill b WHERE b.supplier_norm=? AND b.bill_no=? AND " + pa.EFF_BILL, (sup, bno)).fetchone()
    if not r:
        continue
    found += 1
    in_scan += any(x["bill_id"] == r[0] for x in k["scan"])
    in_confirm += any(x["bill_id"] == r[0] for x in k["confirm"])
    linked += bool(con.execute("SELECT 1 FROM purchase_scan_link WHERE bill_id=?", (r[0],)).fetchone())
say("the six near-matches of 30-Sep: %d found · %d still in Scan karo · %d in Yahi bill hai? · %d linked" % (found, in_scan, in_confirm, linked))
