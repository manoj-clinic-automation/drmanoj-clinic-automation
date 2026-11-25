#!/usr/bin/env python3
# walk_s954.py · kit S954_FULL_COUNT_PENDING · Sanjeevni session 519 · 25-Nov-2026
# On a COPY of finance.db with S952 installed: python walk_s954.py CODE_DIR COPY_DB [control]. Prints PASS / FAIL / INFO and RESULT last.
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
import record_judges as RJ                                    # noqa: E402
print("INFO  code %s · record_judges %s" % (CODE, RJ.VERSION))
sp = SW.Spine()
ctx = SF.Ctx(con, sp)
check("S952 is installed on this database (the undo tables are there)", RJ._has(con, "s952_point_undo"))
now = SW.now_iso()
fday = RJ._day_before(now[:10])
pend = {}
for (it,) in con.execute("SELECT DISTINCT item FROM stock_point WHERE source='full_count' AND gap_units<0").fetchall():
    k = SF.key_of(sp, it, ctx)
    p, _d = (RJ._fc_pending(con, sp, it, k, now, ctx) if hasattr(RJ, "_fc_pending") else RJ._pending_loss(con, sp, it, k, now, fday, None, ctx))
    if p > 0.5:
        pend[it] = p
print("INFO  items where Marg is taken to still hold the 06-Sep shortfall: %d (%s)" % (len(pend), ", ".join("%s %d" % (k, v) for k, v in sorted(pend.items(), key=lambda x: -x[1])[:8])))
for it in ("ETOZOX 90", "CALAPTIN 40", "DOLOGESIC SP"):
    check("%s: the 06-Sep shortfall was closed FOUND -- nothing pending" % it, pend.get(it, 0) < 0.5, pend.get(it))
check("AURAB L CAP / BIO D3 MAX / ROSIKA FORTE: written off by Amir's vouchers of 15-10 and Marg took them -- nothing pending",
      all(pend.get(x, 0) < 0.5 for x in ("AURAB L CAP", "BIO D3 MAX", "ROSIKA FORTE")), [(x, pend.get(x)) for x in ("AURAB L CAP", "BIO D3 MAX", "ROSIKA FORTE")])
check("KT ROS DT: voucher 14 of 15-10 keyed, Marg's stock never moved by it -- still pending (10:1)", abs(pend.get("KT ROS DT", 0) - 101) < 1, pend.get("KT ROS DT"))
check("IGURATI 25 / DOLONEX 2 ML INJ: Marg's net drop since the count is the voucher (a purchase hid it; it landed in two steps) -- nothing pending",
      pend.get("IGURATI 25", 0) < 0.5 and pend.get("DOLONEX 2 ML INJ", 0) < 0.5, [(x, pend.get(x)) for x in ("IGURATI 25", "DOLONEX 2 ML INJ")])
check("ANKLE BINDER BAMBOO L: closed BILLING (cleared by a bill) -- nothing pending", pend.get("ANKLE BINDER BAMBOO L", 0) < 0.5, pend.get("ANKLE BINDER BAMBOO L"))
check("exactly three left, each a voucher Marg never took: KT ROS DT, VINBACTUM DS, NORTIMER TAB", sorted(pend) == ["KT ROS DT", "NORTIMER TAB", "VINBACTUM DS"], sorted(pend))
if hasattr(RJ, "_fc_pending"):
    s952_rows = con.execute("SELECT COUNT(*) FROM s952_point_undo WHERE undone_at IS NULL").fetchone()[0]
    t0 = RJ.now_iso()
    R = RJ.rejudge_all(con, sp, who="S954WALK", write=True)
    print("INFO  judged again: %d (moved %d, withdrawn %d, resized %d, listed %d)" % (R["n"], R["moved"], R["withdrawn"], R["resized"], len(R["listed"])))
    k392 = con.execute("SELECT gap_units, judge_words FROM stock_point WHERE id=392").fetchone()
    check("KT ROS DT's 23-11 count still: Marg holds the older loss -- not a new loss", bool(k392 and "older loss" in str(k392[1]) and float(k392[0]) > -16), k392)
    p390 = con.execute("SELECT gap_units FROM stock_point WHERE id=390").fetchone()
    check("TYRO BR's 23-11 count unchanged (about even with Marg)", p390 is not None and p390[0] is not None and abs(float(p390[0])) <= 10, p390)
    made = con.execute("SELECT COUNT(*) FROM s952_point_undo WHERE undone_at IS NULL AND at>=?", (t0,)).fetchone()[0]
    n = RJ.undo_rejudge(con, who="S954WALK", from_at=t0)
    left = con.execute("SELECT COUNT(*) FROM s952_point_undo WHERE undone_at IS NULL").fetchone()[0]
    check("the S954 undo puts back exactly what this pass re-made (%d) and leaves S952's %d rows" % (made, s952_rows), n == made and left == s952_rows, (n, made, left, s952_rows))
else:
    check("judged again by this version", False, "no _fc_pending")
con.close()
print("RESULT: %s" % ("ALL PASS" if not fails else "%d FAIL" % len(fails)))
