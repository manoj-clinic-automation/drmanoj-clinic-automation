#!/usr/bin/env python3
"""proof_s765.py -- kit S765's proof on this box, READ ONLY: the server's asking (porders_s454.s736_plan) on a COPY of finance.db and the
live assets.db (read only, through the module's own reader), by the given files. Counts only -- no dealer, no paper.

usage: proof_s765.py <dir with scan_quality.py> <dir with porders_s454.py> <the finance folder> <finance.db copy> <label>
Last line: 'PROOF S765 <label>: open server asks N · on summary papers S · would withdraw W (on summaries WS) · would ask A (on summaries AS)'
"""
import importlib.util
import os
import sqlite3
import sys

SQD, POD, FIN, DBC, LABEL = sys.argv[1:6]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


sys.path.insert(0, FIN)
sys.path.insert(1, os.path.dirname(os.path.abspath(SQD)))
sq = load("scan_quality", os.path.join(SQD, "scan_quality.py"))
po = load("porders_s454", os.path.join(POD, "porders_s454.py"))
po._sq = lambda: sq
con = sqlite3.connect("file:%s?mode=ro" % DBC, uri=True, timeout=30)
con.row_factory = sqlite3.Row
p = po.s736_plan(con)
f = p.get("facts") or {}
if not p.get("ok"):
    print("PROOF S765 %s: NOT READ -- assets.db or scan_quality unreachable" % LABEL)
    sys.exit(1)
rows = f.get("rows") or {}


def summ(sid):
    r = rows.get(int(sid)) or {}
    return str(r.get("kind") or "") == "Summary"


open_srv = [a for a in f.get("asks") or [] if str(a.get("asked_by") or "") == "server" and not a.get("done_at") and not a.get("withdrawn_at")]
on_s = sum(1 for a in open_srv if summ(a["asset_bill_id"]))
by_id = {int(a["id"]): a for a in f.get("asks") or []}
wd = p.get("withdraw") or []
wd_s = sum(1 for i in wd if summ(by_id.get(int(i), {}).get("asset_bill_id", 0)))
ask = (p.get("ask") or []) + (p.get("escalated") or [])
ask_s = sum(1 for x in ask if summ(x["scan"]))
print("PROOF S765 %s: open server asks %d · on summary papers %d · would withdraw %d (on summaries %d) · would ask %d (on summaries %d)"
      % (LABEL, len(open_srv), on_s, len(wd), wd_s, len(ask), ask_s))
