#!/usr/bin/env python3
"""proof_s766.py -- kit S766's proof on this box, READ ONLY: porders_s454.s736_plan on a COPY of finance.db and the live assets.db (read only,
through the module's own reader), by the given porders_s454.py. Counts only.
usage: proof_s766.py <dir with porders_s454.py> <dir with scan_quality.py> <the finance folder> <finance.db copy> <label>
Last line: 'PROOF S766 <label>: open server asks N · on deleted scans D · would withdraw W (on deleted scans WD) · would ask A'"""
import importlib.util
import os
import sqlite3
import sys

POD, SQD, FIN, DBC, LABEL = sys.argv[1:6]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


sys.path.insert(0, FIN)
sq = load("scan_quality", os.path.join(SQD, "scan_quality.py"))
po = load("porders_s454", os.path.join(POD, "porders_s454.py"))
po._sq = lambda: sq
con = sqlite3.connect("file:%s?mode=ro" % DBC, uri=True, timeout=30)
con.row_factory = sqlite3.Row
p = po.s736_plan(con)
f = p.get("facts") or {}
if not p.get("ok"):
    print("PROOF S766 %s: NOT READ -- assets.db or scan_quality unreachable" % LABEL)
    sys.exit(1)
rows, kids = f.get("rows") or {}, f.get("kids") or set()
open_srv = [a for a in f.get("asks") or [] if str(a.get("asked_by") or "") == "server" and not a.get("done_at") and not a.get("withdrawn_at")]
gone = {int(a["id"]) for a in open_srv if int(a["asset_bill_id"]) not in rows and int(a["asset_bill_id"]) not in kids}
wd = p.get("withdraw") or []
print("PROOF S766 %s: open server asks %d · on deleted scans %d · would withdraw %d (on deleted scans %d) · would ask %d"
      % (LABEL, len(open_srv), len(gone), len(wd), sum(1 for i in wd if int(i) in gone), len((p.get("ask") or []) + (p.get("escalated") or []))))
