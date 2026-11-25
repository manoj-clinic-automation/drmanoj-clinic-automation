#!/usr/bin/env python3
# walk_s956.py · kit S956_SAME_DAY_DELIVERY · on a COPY of finance.db (S952 + S954 installed): python walk_s956.py CODE_DIR COPY_DB [control]
import os
import sqlite3
import sys

CODE, DB = sys.argv[1], sys.argv[2]
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [CODE] + [x for x in sys.path if os.path.abspath(x or ".") != _HERE]
os.environ["FINANCE_DB"] = DB
fails = []


def check(name, ok, info=""):
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, (" -- " + str(info)) if info else ""))
    if not ok:
        fails.append(name)


con = sqlite3.connect(DB, timeout=60)
import stock_watch as SW                                      # noqa: E402
import stock_figure as SF                                     # noqa: E402
import stock_record as SR                                     # noqa: E402
print("INFO  code %s · stock_figure %s" % (CODE, SF.VERSION))
sp = SW.Spine()
before = {r[0]: r[1:] for r in con.execute("SELECT item, shelf_units, gap_units FROM stock_of_record")}
B = SR.build(con, sp)
check("the stock of record rebuilds", bool(B.get("ok")), B.get("n"))
after = {r[0]: r[1:] for r in con.execute("SELECT item, shelf_units, gap_units, pack FROM stock_of_record")}
moved = sorted(k for k in after if before.get(k) is not None and tuple(before[k]) != tuple(after[k][:2]))
print("INFO  rows whose shelf moved on this rebuild: %d (%s)" % (len(moved), ", ".join(moved[:10])))
j = after.get("JAKMAC 5")
check("JAKMAC 5: Darpan's 28:4 of 23-11 10:27 + Gunina bill 100075 of that day (20:0) -- the shelf agrees with Marg", j is not None and j[1] is not None and abs(float(j[1])) < float(j[2] or 1), j)
t = after.get("TYRO BR")
check("TYRO BR's row stays within a strip of Marg", t is not None and t[1] is not None and abs(float(t[1])) <= 10, t)
ctx = SF.Ctx(con, sp)
if hasattr(SF, "_s956_same_day"):
    k = SF.key_of(sp, "TYRO BR", ctx)
    a = SF._s956_same_day(ctx, sp, k, "TYRO BR", dict(day="2026-11-20", at="2026-11-20T11:00:00"))
    b = SF._s956_same_day(SF.Ctx(con, sp), sp, k, "TYRO BR", dict(day="2026-11-20", at="2026-11-20T13:00:00"))
    check("a count at 11:00 on 20-11: Kedar's bill 250 of that day (tapped 12:25) came after it -- added (50:0)", abs(a - 500) < 1, a)
    check("a count at 13:00 on 20-11: bill 250 was tapped at 12:25, inside the count -- not added again", abs(b) < 1, b)
    c = SF._s956_same_day(SF.Ctx(con, sp), sp, k, "TYRO BR", dict(day="2026-11-20", at="2026-11-20T18:30:00"))
    check("a Count now at 18:30 (an evening count) adds nothing of its day", abs(c) < 1, c)
    j5 = SF.key_of(sp, "JAKMAC 5", ctx)
    d = SF._s956_same_day(SF.Ctx(con, sp), sp, j5, "JAKMAC 5", dict(day="2026-11-23", at="2026-11-23T14:30:00"))
    check("an afternoon count with no arrival time for the day's bill adds nothing (count.same_day_until 12:00)", abs(d) < 1, d)
else:
    check("a same-day delivery after a morning count is added", False, "no _s956_same_day")
con.close()
print("RESULT: %s" % ("ALL PASS" if not fails else "%d FAIL" % len(fails)))
