#!/usr/bin/env python3
"""walk_s924.py -- kit S924 walked on a COPY of finance.db (never the live one). argv: <code dir with the kit's files> <copy.db> [control]
Checks: the Hub's Needs-you carries ONE purchase line with his grouped page's counts; the old 'Orders: N late' line and the line per
out-of-stock tap are gone; the wrong-dealer note stays; every other line unchanged; a CONTROL that must go red (the hook not installed)."""
import datetime as dt
import os
import shutil
import sqlite3
import sys

CODE, SRC = sys.argv[1], sys.argv[2]
CONTROL = len(sys.argv) > 3 and sys.argv[3] == "control"
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
sys.path.insert(0, CODE)
os.environ["PORDERS_SOURCE"] = "tables"
os.environ["NEEDS_YOU_WITHOUT_S408"] = "1"                         # packs' lines import the whole app (finance_app): never in a walk
DB = SRC + ".walk924"
shutil.copy(SRC, DB)
FAIL = []


def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond:
        FAIL.append(what)


import order_flow as F                                            # noqa: E402
import sanjeevni_approvals as SA                                  # noqa: E402

con = sqlite3.connect(DB, timeout=30)
con.row_factory = sqlite3.Row


def lines():
    r = SA.needs_you(con)
    ls = r.get("lines") if isinstance(r, dict) else r
    return [str(l.get("text") or "") for l in (ls or [])]


F._HUB["on"] = True                                               # the app (imported by Needs-you itself) must not hook before 'before'
before = lines()
old_oos = [t for t in before if " says " in t and ("out of stock" in t or "no longer available" in t)]
old_orders = [t for t in before if t.startswith("Orders: ")]
print("INFO before: %d lines, %d per out-of-stock tap, %d 'Orders:' line" % (len(before), len(old_oos), len(old_orders)))
if not CONTROL:                                                   # the control: the hook never installed
    F._HUB.clear()
    F.hub_lines_install()
after = lines()
G = F.groups(con, dt.datetime.now(), with_bills=False)
c = G["counts"]
mine = [t for t in after if t.startswith("Purchase orders:")]
ok(len(mine) == (1 if (c["late"] or c["gap_meds"] or c["team"]) else 0), "one purchase line (%s)" % (mine[0] if mine else "none"))
ok(not mine or (("%d out of stock" % c["team"]) in mine[0] if c["team"] else True), "its out-of-stock count is the team list's")
ok(not mine or ((("%d late" % c["late"]) in mine[0]) if c["late"] else ("late" not in mine[0])), "its late count is the grouped page's")
ok(not [t for t in after if t.startswith("Orders: ")], "the old 'Orders: N late' line is gone")
ok(not [t for t in after if " says " in t and ("out of stock" in t or "no longer available" in t)], "no line per out-of-stock tap")
wd_b = [t for t in before if t.startswith("Wrong dealer")]
ok([t for t in after if t.startswith("Wrong dealer")] == wd_b, "the wrong-dealer note unchanged")
rest_b = [t for t in before if t not in old_oos and t not in old_orders]
rest_a = [t for t in after if not t.startswith("Purchase orders:")]
ok(rest_b == rest_a, "every other line unchanged (%d)" % len(rest_a))
F.hub_lines_install()
ok(len([t for t in lines() if t.startswith("Purchase orders:")]) == len(mine), "installing twice adds nothing")
con.close()
os.remove(DB)
ok("finance_app" not in sys.modules, "the walk never loaded the whole app (no path to the live database)")
print("RESULT:", "ALL PASS" if not FAIL else "%d FAIL" % len(FAIL))
sys.exit(1 if FAIL else 0)
