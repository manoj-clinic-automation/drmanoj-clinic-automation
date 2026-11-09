#!/usr/bin/env python3
"""walk_s765.py -- kit S765_SUMMARY_NOT_RESCAN's walk on MADE-UP rows (no database of the box is opened; nothing is written anywhere).

usage: python walk_s765.py <dir with scan_quality.py> <dir with porders_s454.py> <the finance folder (its other modules, read only)> [--control]
The last line: 'WALK S765 GREEN' -- or, with --control on the live files, 'CONTROL S765 RED as it must be'.
"""
import datetime as dt
import importlib.util
import os
import sys

SQD, POD, FIN = (os.path.abspath(a) for a in sys.argv[1:4])
CONTROL = "--control" in sys.argv
RES = []


def ck(name, cond, new=True):
    RES.append((name, bool(cond), new))
    print(("  OK   " if cond else "  RED  ") + ("[S765] " if new else "[old]  ") + name)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


sys.path.insert(0, FIN)
sq = load("scan_quality", os.path.join(SQD, "scan_quality.py"))
print("Q · scan_quality")
SUMMARY_READ = {"doc_kind": "summary", "is_summary": True, "dealer": "MADE-UP AGENCIES", "bills": [], "closing_total": None}
OTHER_READ = {"doc_kind": "other", "items": [], "total_amount": None}
BILL = dict(lane="pharmacy", status="captured", kind="Pharmacy", doc_kind="")
SUMM = dict(lane="pharmacy", status="captured", kind="Summary", doc_kind="summary")
ck("a summary paper read as a summary -> not judged (no 'bill nahi hai')", sq.detail(SUMM, SUMMARY_READ, None) is None)
ck("a summary paper whose reading came back 'other' -> not judged", sq.detail(SUMM, OTHER_READ, None) is None)
ck("a summary paper with a cut / blurred check -> not judged either", sq.detail(SUMM, None, {"legible": 0, "whole_bill": 0}) is None)
ck("a BILL whose reading guessed 'summary' (kind still Pharmacy, doc_kind summary) with a blurred check -> still 'blurred'",
   (sq.detail(dict(BILL, doc_kind="summary"), SUMMARY_READ, {"legible": 0}) or {}).get("code") == "blurred", new=False)
ck("a BILL read as 'other' -> still 'not_bill' (the rule for bills is unchanged)", (sq.detail(BILL, OTHER_READ, None) or {}).get("code") == "not_bill", new=False)
ck("a BILL with a blurred check -> still 'blurred'", (sq.detail(BILL, None, {"legible": 0}) or {}).get("code") == "blurred", new=False)
ck("a BILL with no total -> still 'no_total'", (sq.detail(BILL, {"doc_kind": "bill", "items": [{"amount": 10}], "total_amount": None}, None) or {}).get("code") == "no_total", new=False)
ck("a clinic-lane paper -> not judged (as before)", sq.detail(dict(BILL, lane="clinic"), OTHER_READ, None) is None, new=False)

print("P · porders_s454.s736_plan (the server's asking) on made-up facts")
po = load("porders_s454", os.path.join(POD, "porders_s454.py"))
po._sq = lambda: sq
po.month_class = lambda con, ym: "counted"
NOW = dt.datetime(2026, 11, 9, 17, 0)
old = NOW - dt.timedelta(hours=20)


def row(i, kind, doc_kind="", lie=None):
    return dict(id=i, stamp_no="S-%d" % i, vendor="MADE-UP AGENCIES", bill_no="", bill_date="2026-11-08", bill_month="2026-10", total_amount=None,
                submitted_at=None, created_at="2026-11-08 12:00:00", lane="pharmacy", kind=kind, status="captured", page_of=None, doc_kind=doc_kind,
                source_stored="f%d.jpg" % i, rescan_of=None, dup_of=None, ocr_status="read", at=old, lie=lie)


facts = dict(ok=True, since="2026-10-08", settings={}, parent={}, kids=set(), link={}, dec={}, picked=set(), dup=set(), final=set(),
             rows={1: row(1, "Summary", "summary"), 2: row(2, "Summary", "summary"), 3: row(3, "Pharmacy", "", {"legible": 0}),
                   4: row(4, "Summary", "summary"), 5: row(5, "Summary", "summary"), 6: row(6, "Pharmacy", "")},
             reading={1: SUMMARY_READ, 3: None, 4: SUMMARY_READ, 5: OTHER_READ, 6: OTHER_READ},
             asks=[dict(id=11, asset_bill_id=1, asked_by="server", done_at=None, withdrawn_at=None),
                   dict(id=12, asset_bill_id=2, asked_by="server", done_at=None, withdrawn_at=None),
                   dict(id=14, asset_bill_id=4, asked_by="manoj", done_at=None, withdrawn_at=None)])
p = po.s736_plan(None, now=NOW, facts=facts)
asked = sorted(x["scan"] for x in p["ask"] + p["escalated"])
ck("the server's open ask on a READ summary is withdrawn", 11 in p["withdraw"])
ck("the server's open ask on an UNREAD summary is withdrawn too", 12 in p["withdraw"])
ck("an ask a PERSON sent on a summary stays (never withdrawn by the server)", 14 not in p["withdraw"], new=False)
ck("a summary read as 'other' is never asked for", 5 not in asked)
ck("a blurred BILL is still asked for (the rule for bills is unchanged)", 3 in asked, new=False)
ck("a BILL read as 'other' is still asked for (not_bill)", 6 in asked, new=False)

new = [r for r in RES if r[2]]
old_ = [r for r in RES if not r[2]]
print("\n%d checks: %d S765 (%d green), %d old (%d green)" % (len(RES), len(new), sum(r[1] for r in new), len(old_), sum(r[1] for r in old_)))
if CONTROL:
    good = all(not r[1] for r in new) and all(r[1] for r in old_)
    print("CONTROL S765 RED as it must be" if good else "CONTROL S765 WRONG: " + "; ".join(r[0] for r in RES if (r[2] and r[1]) or (not r[2] and not r[1])))
    sys.exit(0 if good else 1)
ok = all(r[1] for r in RES)
print("WALK S765 GREEN" if ok else "WALK S765 RED")
sys.exit(0 if ok else 1)
