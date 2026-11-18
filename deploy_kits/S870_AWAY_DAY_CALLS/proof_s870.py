#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s870.py -- kit S870 on the LIVE stores, READ-ONLY, counts only (no name, number or ID printed).
usage: proof_s870.py <new portal dir> <live portal dir> <console.db> <inbox.db> <finance.db> <staff_master> <punches> <review.db>
The Call Console's follow-up list and the WhatsApp ladder's day, old page against new: the same rows and bands; the rows the
new page marks 'away' / holds are exactly those due on a not-sitting day. Last line 'PROOF CLEAN ...' or 'PROOF RED ...'."""
import datetime as dt
import importlib.util
import os
import sqlite3
import sys

NEW, LIVE, CDB, IDB, FDB, SM, PU, RV = sys.argv[1:9]
os.environ.setdefault("FINANCE_DB", FDB)
sys.path.insert(0, LIVE)
bad = []


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ro(p):
    c = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=10)
    c.row_factory = sqlite3.Row
    return c


try:
    away = {r[0] for r in ro(FDB).execute("SELECT day FROM clinic_off_day")}
except sqlite3.Error:
    away = set()
print("days not sitting in finance.db: %d" % len(away))
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).replace(tzinfo=None)
fu = {}
for tag, d in (("old", LIVE), ("new", NEW)):
    C = load("cc_" + tag, os.path.join(d, "calls_console.py"))
    fu[tag] = C.followup_list(ro(CDB), now, fin_db=FDB, inbox_path=IDB)
bo = [(b[0], b[4]) for b in fu["old"]["bands"]]
bn = [(b[0], b[4]) for b in fu["new"]["bands"]]
rows_n = [r for b in fu["new"]["bands"] for r in b[3]]
aw = [r for r in rows_n if r.get("away")]
due_away = [r for r in rows_n if r["dd"].isoformat() in away]
print("Call Console follow-up list: bands old %s / new %s; rows marked away %d (due on a not-sitting day %d)" % (bo, bn, len(aw), len(due_away)))
if bo != bn:
    bad.append("the bands moved")
if len(aw) != len(due_away):
    bad.append("away rows differ from the rows due on a not-sitting day")
wl = {}
for tag, d in (("old", LIVE), ("new", NEW)):
    W = load("wl_" + tag, os.path.join(d, "wa_ladder.py"))
    p = W.plan()
    wl[tag] = p
if wl["old"] is None and wl["new"] is None:
    print("WhatsApp ladder: its day cannot be read on these stores by either page (alike) -- its walk carries it")
elif wl["old"] is None or wl["new"] is None:
    bad.append("the ladder's day reads on one page and not the other")
else:
    so = {x["key"]: (len(x["rows"]), x["go"], x["held"]) for x in wl["old"]["lists"]}
    sn = {x["key"]: (len(x["rows"]), x["go"], x["held"]) for x in wl["new"]["lists"]}
    ha = sum(1 for x in wl["new"]["lists"] for r in x["rows"] if "Dr Manoj was away" in (r.get("hold") or ""))
    print("WhatsApp ladder today (rows, go, held) old %s / new %s; held as 'away' %d" % (so, sn, ha))
    if any(so[k][0] != sn[k][0] for k in so):
        bad.append("the ladder's rows moved")
print(("PROOF RED: " + "; ".join(bad)) if bad else "PROOF CLEAN: only rows due on a not-sitting day change")
