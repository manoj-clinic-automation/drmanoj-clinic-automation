#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""liveshape_s930.py -- the Stock check record built on COPIES of the live finance.db and spine.db (the box): the page must build, with
Marg's names, in a sane time; counts only are printed (names of medicines are fine; no patient data is read -- stock tables only).
    python3 -B liveshape_s930.py <dir with the new files> <COPY of finance.db> <COPY of spine.db>"""
import os
import re
import sys
import time
import sqlite3


def say(s):
    print(re.sub(r"\d{8,}", lambda m: "#" * len(m.group(0)), str(s)), flush=True)


fin, dbp, spp = (os.path.abspath(x) for x in sys.argv[1:4])
os.environ.update(FINANCE_DB=dbp, SPINE_DB=spp, PYTHONDONTWRITEBYTECODE="1")
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != here]
sys.path.insert(0, fin)
os.chdir(fin)
import stock_check as SC                                      # noqa: E402
con = sqlite3.connect(dbp, timeout=60)
t0 = time.time()
R = SC.record(con)
dt_ = time.time() - t0
if not R.get("ok"):
    say("RESULT: FAIL -- %s" % R.get("reason"))
    sys.exit(1)
T = R["totals"]
say("INFO %d items in %.1f s: look %d, waiting %d, no shelf %d, agree %d (in stock %d), counts %d, count-only names %d; closing %s taken %s; %d items carry delivery lines" % (
    T["items"], dt_, T["look"], T["arrived"], T["noshelf"], T["agree"], T["agree_in_stock"], T["counts"], T["count_only"], R["reports"]["closing_as_on"], R["reports"]["closing_at"],
    sum(1 for r in R["rows"] if r.get("lines"))))
for r in R["rows"][:8]:
    say("   %-28s marg %-7s shelf %-7s waiting %-7s gap %s%s" % (r["item"][:28], r["marg_t"], r["core_t"], r["arrived_t"] or "-", r["gap_t"], " (evening)" if r["evening"] else ""))
for c in R["count_only"][:6]:
    say("   count-only: %s %s (%s)" % (c["item"], c["counted_t"], c["day"]))
bad = []
if T["items"] < 200:
    bad.append("fewer than 200 items -- the capture's names did not load")
if dt_ > 120:
    bad.append("the record took %.0f s" % dt_)
say("RESULT: %s" % ("ALL PASS" if not bad else "FAIL -- " + "; ".join(bad)))
sys.exit(0 if not bad else 1)
