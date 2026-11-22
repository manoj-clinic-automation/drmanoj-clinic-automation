#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""liveshape_s933.py -- the stock of record built on COPIES of the live finance.db and spine.db (the box), and read by the Stock check page; the
old page's figures beside it. Names of medicines are fine; no patient data is read (stock tables only).
    python3 -B liveshape_s933.py <dir with the new files> <dir with the old files> <COPY of finance.db> <COPY of spine.db>
Prints the record's closing, the counts old -> new, the items the owner named (MEG QCS, PATOPAN DSR, FERONES HD, TYRO BR), the first late bills.
RESULT: ALL PASS when the record builds (>= 200 rows, under 150 s) and the page's 'need a look' is not more than the old page's."""
import os
import re
import sqlite3
import sys
import time


def say(s):
    print(re.sub(r"\d{8,}", lambda m: "#" * len(m.group(0)), str(s)), flush=True)


fin, old, dbp, spp = (os.path.abspath(x) for x in sys.argv[1:5])
os.environ.update(FINANCE_DB=dbp, SPINE_DB=spp, PYTHONDONTWRITEBYTECODE="1")
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != here]
bad = []
# the OLD page's figures first (its own computation), in its own interpreter state
sys.path.insert(0, old)
os.chdir(old)
import stock_check as SC0                                     # noqa: E402
con = sqlite3.connect(dbp, timeout=60)
t0 = time.time()
R0 = SC0.record(con)
say("INFO old page: %s in %.1f s" % (("look %d, waiting %d, no shelf %d, agree %d" % (R0["totals"]["look"], R0["totals"]["arrived"], R0["totals"]["noshelf"], R0["totals"]["agree"])) if R0.get("ok") else R0.get("reason"), time.time() - t0))
old_rows = {r["item"]: r for r in R0.get("rows", [])}
for m in [k for k, v in list(sys.modules.items()) if str(getattr(v, "__file__", "") or "").startswith(old)]:
    sys.modules.pop(m, None)                                  # every module loaded from the old folder goes; the new folder's are imported fresh
sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != old]
sys.path.insert(0, fin)
os.chdir(fin)
import stock_watch as SW                                      # noqa: E402
import stock_record as SR                                     # noqa: E402
import stock_check as SC                                      # noqa: E402
assert SR.__file__.startswith(fin) and SC.__file__.startswith(fin), (SR.__file__, SC.__file__)
sp = SW.Spine(spp)
t1 = time.time()
B = SR.build(con, sp, log=say)
dt_ = time.time() - t1
if not B.get("ok"):
    say("RESULT: FAIL -- the record did not build: %s" % B.get("reason"))
    sys.exit(1)
rows, M = SR.rows(con, sp, "never")
say("INFO the record: %d rows in %.1f s (%d skipped); closing printed as on %s, taken %s, the end of %s (%s); sale to %s, purchases to %s" % (
    len(rows), dt_, int(B.get("errors") or 0), M.get("cap_as_on"), M.get("cap_stamp_iso", "")[:16], M.get("cap_end_day"), M.get("cap_kind"), M.get("sale_to"), M.get("purchase_to")))
R = SC.record(con)
if not R.get("ok"):
    say("RESULT: FAIL -- the page did not read the record: %s" % R.get("reason"))
    sys.exit(1)
T = R["totals"]
say("INFO new page: look %d, waiting %d, no shelf %d, agree %d (in stock %d), behind %d, consumables %d, items with a late bill %d" % (
    T["look"], T["arrived"], T["noshelf"], T["agree"], T["agree_in_stock"], T["behind"], T["consumable"], T["late"]))
new_rows = {r["item"]: r for r in R["rows"]}
for nm in ("MEG QCS", "PATOPAN DSR", "FERONES HD", "TYRO BR", "FLUXIC P", "PRETOL 8"):
    o, n = old_rows.get(nm), new_rows.get(nm)
    say("   %-12s old: marg %-6s shelf %-6s gap %-7s | new: marg %-6s shelf %-6s waiting %-6s gap %-7s %s%s" % (
        nm, (o or {}).get("marg_t", "—"), (o or {}).get("core_t", "—"), (o or {}).get("gap_t", "—"),
        (n or {}).get("marg_t", "—"), (n or {}).get("core_t", "—"), (n or {}).get("arrived_t", "—") or "—", (n or {}).get("gap_t", "—"), (n or {}).get("state", ""),
        (" · " + n["words"][:90]) if (n and n.get("words")) else ""))
late = [r for r in R["rows"] if r.get("late")]
for r in late[:6]:
    say("   late: %-20s %s" % (r["item"][:20], r["words"][:120]))
behind = [r["item"] for r in R["rows"] if r.get("state") == "marg_behind"]
if behind:
    say("   Marg behind a bill: %s" % ", ".join(behind[:8]))
if len(rows) < int(os.environ.get("MIN_ROWS") or 200):
    bad.append("fewer than %s rows -- the capture's names did not load" % (os.environ.get("MIN_ROWS") or 200))   # MIN_ROWS: the rehearsal's made-up spine
if dt_ > 150:
    bad.append("the record took %.0f s" % dt_)
if R0.get("ok") and T["look"] > R0["totals"]["look"]:
    bad.append("the new page needs MORE looks (%d) than the old (%d)" % (T["look"], R0["totals"]["look"]))
if any(r.get("marg_units") is None for r in rows):
    bad.append("a row without a Marg figure")
say("RESULT: %s" % ("ALL PASS" if not bad else "FAIL -- " + "; ".join(bad)))
sys.exit(0 if not bad else 1)
