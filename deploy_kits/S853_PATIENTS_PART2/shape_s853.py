#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shape_s853.py -- kit S853 (S477): the LIVE SHAPE, run by the installer on the box on COPIES of the live stores.
    python3 shape_s853.py <new_dir> <old_dir> <finance.db copy> <console.db copy> <inbox.db copy> <gmb_store.db copy> <marks db or ->
                          <calls_console.py>
Part 1 must read the same on the new files as on the live ones; every Part 2 block must read. Prints COUNTS ONLY (no number, no
name, no clinic ID) and a last line "SHAPE OK n/m"."""
import datetime as dt
import importlib.util
import os
import sqlite3
import sys
import time

NEW, OLD, FINDB, CON, INB, GMB, MARKS, CC = sys.argv[1:9]
os.environ.update(PATIENTS_CONSOLE_DB=CON, PATIENTS_INBOX_DB=INB, PATIENTS_GMB_DB=GMB, PATIENTS_CALLS_CONSOLE=CC,
                  PATIENTS_AWAIT_DB=(MARKS if MARKS != "-" else "/nonexistent/marks.db"))
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
BASE = [p for p in sys.path if not _ME or os.path.abspath(p or ".") != _ME]


def load(d):
    sys.path[:] = [d] + BASE
    for m in ("patients_page", "patients_part2"):
        sys.modules.pop(m, None)
    sp = importlib.util.spec_from_file_location("patients_page", os.path.join(d, "patients_page.py"))
    m = importlib.util.module_from_spec(sp)
    sys.modules["patients_page"] = m
    sp.loader.exec_module(m)
    return m


con = sqlite3.connect("file:%s?mode=ro" % FINDB, uri=True)
today = dt.date.today()
ro, lo = load(OLD).read(con, today)
t0 = time.time()
rn, ln = load(NEW).read(con, today)
took = time.time() - t0
res = []


def ok(nm, c, x=""):
    res.append(bool(c))
    print(("PASS " if c else "FAIL ") + nm + ("  -- " + str(x)[:200] if x else ""))


for k in ("rows", "back", "fu", "groups", "late", "cov", "glance", "months", "words"):
    ok("Part 1 '%s' the same" % k, ro.get(k) == rn.get(k))


def strip(x):
    return [dict(l, sug=("" if l["head"] == "Who came" else l["sug"])) for l in x]


ok("Part 1 lines kept, Part 2's in front", all(strip(rn["readings"][m][-len(ro["readings"][m]):]) == strip(ro["readings"][m]) for m in ro["readings"]))
ok("Part 1 lists the same (Part 2 adds fuc:* only)", all(lo[k] == ln[k] for k in lo) and all(k.startswith("fuc:") for k in ln if k not in lo))
p2 = rn.get("p2") or {}
for b in ("history", "google", "desk", "called", "reviews"):
    ok("Part 2 '%s' reads" % b, (p2.get(b) or {}).get("ok") is True, (p2.get(b) or {}).get("why"))
dk = p2.get("desk") or {}
ok("the WhatsApp inbox reads", dk.get("wa_ok") is True)
for m, d in sorted((dk.get("months") or {}).items()):
    f = d.get("fig") or {}
    print("  %s caller-days %s: first %s, again %s, back %s, later %s, never %s (no call-back %s); WhatsApp senders %s, nothing %s" % (
        m, f.get("n"), f.get("first"), f.get("again"), f.get("back"), f.get("later"), f.get("never"), f.get("nocb"), f.get("wa_n"), f.get("wa_nothing")))
cl = p2.get("called") or {}
mt = cl.get("matched") or {}
print("  call record from %s; follow-ups in the Called split %s, left out: no number %s, not yet %s, before the record %s" % (
    cl.get("calls_from"), mt.get("split"), mt.get("nophone"), mt.get("notyet"), mt.get("before")))
ok("the Called split matches numbers (fewer IDs without a number than with one)", (mt.get("nophone") or 0) <= (mt.get("split") or 0), mt)
print("  Part 2 took %ss of the reading" % p2.get("took"))
rv = p2.get("reviews") or {}
print("  reviews: %s readings; last %s" % (rv.get("n_snap"), (rv.get("last") or {}).get("taken_on")))
print("  reading took %.1fs (Part 1 alone on the live files is the bar)" % took)
ok("the reading takes under 30 s (gunicorn times out at 90)", took < 30, took)
print(("SHAPE OK %d/%d" if all(res) else "SHAPE RED %d/%d") % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
