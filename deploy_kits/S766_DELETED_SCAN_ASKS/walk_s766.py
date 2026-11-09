#!/usr/bin/env python3
"""walk_s766.py -- kit S766_DELETED_SCAN_ASKS's walk on MADE-UP facts (nothing of the box is opened or written).
usage: python walk_s766.py <dir with porders_s454.py> <dir with scan_quality.py> <the finance folder> [--control]
Last line: 'WALK S766 GREEN' -- or with --control on the live file 'CONTROL S766 RED as it must be'."""
import datetime as dt
import importlib.util
import os
import sys

POD, SQD, FIN = (os.path.abspath(a) for a in sys.argv[1:4])
CONTROL = "--control" in sys.argv
RES = []


def ck(name, cond, new=True):
    RES.append((name, bool(cond), new))
    print(("  OK   " if cond else "  RED  ") + ("[S766] " if new else "[old]  ") + name)


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
po.month_class = lambda con, ym: "counted"
NOW = dt.datetime(2026, 11, 9, 18, 0)


def row(i, kind, lie=None):
    return dict(id=i, stamp_no="B-%04d" % i, vendor="MADE-UP", bill_no="", bill_date="2026-11-08", bill_month="2026-10", total_amount=None, submitted_at=None,
                created_at="2026-11-08 12:00:00", lane="pharmacy", kind=kind, status="captured", page_of=None, doc_kind="", source_stored="f.jpg",
                rescan_of=None, dup_of=None, ocr_status="read", at=NOW - dt.timedelta(hours=20), lie=lie)


def ask(i, sid, by="server", done=None, wd=None):
    return dict(id=i, asset_bill_id=sid, asked_by=by, done_at=done, withdrawn_at=wd)


facts = dict(ok=True, since="2026-10-08", settings={}, parent={}, kids={278}, link={}, dec={}, picked=set(), dup=set(), final=set(),
             rows={3: row(3, "Pharmacy", {"legible": 0}), 290: row(290, "Summary")}, reading={},
             asks=[ask(21, 274), ask(22, 277, by="manoj"), ask(23, 278), ask(24, 280, done="2026-11-09"), ask(25, 281, wd="2026-11-09"),
                   ask(26, 290), ask(27, 283)])
p = po.s736_plan(None, now=NOW, facts=facts)
asked = sorted(x["scan"] for x in p["ask"] + p["escalated"])
ck("the server's open ask on a DELETED scan (B-0274) is withdrawn", 21 in p["withdraw"])
ck("... and on another deleted scan (B-0283)", 27 in p["withdraw"])
ck("an ask a PERSON sent on a deleted scan stays", 22 not in p["withdraw"], new=False)
ck("a deleted scan that was RESCANNED (a newer scan names it) is left to the rescan (closed as done, not withdrawn)", 23 not in p["withdraw"], new=False)
ck("an ask already done or withdrawn is not touched again", 24 not in p["withdraw"] and 25 not in p["withdraw"], new=False)
ck("S765 stands: the server's ask on a summary paper is withdrawn", 26 in p["withdraw"], new=False)
ck("a blurred BILL that exists is still asked for", 3 in asked, new=False)
ck("each ask is withdrawn once", len(p["withdraw"]) == len(set(p["withdraw"])), new=False)
facts2 = dict(facts, ok=False)
p2 = po.s736_plan(None, now=NOW, facts=facts2)
ck("assets.db unreachable -> nothing withdrawn at all (a missing database never reads as deleted scans)", p2["withdraw"] == [] and p2["ask"] == [], new=False)
new = [r for r in RES if r[2]]
old = [r for r in RES if not r[2]]
print("\n%d checks: %d S766 (%d green), %d old (%d green)" % (len(RES), len(new), sum(r[1] for r in new), len(old), sum(r[1] for r in old)))
if CONTROL:
    good = all(not r[1] for r in new) and all(r[1] for r in old)
    print("CONTROL S766 RED as it must be" if good else "CONTROL S766 WRONG: " + "; ".join(r[0] for r in RES if (r[2] and r[1]) or (not r[2] and not r[1])))
    sys.exit(0 if good else 1)
ok = all(r[1] for r in RES)
print("WALK S766 GREEN" if ok else "WALK S766 RED")
sys.exit(0 if ok else 1)
