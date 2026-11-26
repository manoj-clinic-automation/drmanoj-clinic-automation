#!/usr/bin/env python3
# walk_s957.py · kit S957_COUNT_LEFTOVERS · Sanjeevni session 522 · 26-Nov-2026
# On a COPY of finance.db (S952 + S954 + S956 installed): python walk_s957.py CODE_DIR COPY_DB FROM_DIR [control]
# Prints PASS / FAIL / INFO and RESULT last. Removes its own rows first; sets its own clock for the recount match.
import importlib.util
import os
import sqlite3
import sys

CODE, DB, OLD = sys.argv[1], sys.argv[2], sys.argv[3]
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [CODE] + [x for x in sys.path if os.path.abspath(x or ".") != _HERE]
os.environ["FINANCE_DB"] = DB
fails = []


def check(name, ok, info=""):
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, (" -- " + str(info)) if info else ""))
    if not ok:
        fails.append(name)


import stock_watch as SW                                      # noqa: E402
import stock_figure as SF                                     # noqa: E402
import record_judges as RJ                                    # noqa: E402
print("INFO  code %s · record_judges %s · stock_figure %s · stock_watch %s" % (CODE, RJ.VERSION, SF.VERSION, SW.VERSION))
check("the versions: record_judges 1.2 (S957) · stock_figure 1.8 · stock_watch 1.13",
      (RJ.VERSION, getattr(RJ, "KIT", ""), SF.VERSION, SW.VERSION) == ("1.2", "S957_COUNT_LEFTOVERS", "1.8", "1.13"), (RJ.VERSION, SF.VERSION, SW.VERSION))
con = sqlite3.connect(DB, timeout=60)
sp = SW.Spine()
ctx = SF.Ctx(con, sp)
now = SW.now_iso()


def pend_all():
    out = {}
    c2 = SF.Ctx(con, sp)
    for (it,) in con.execute("SELECT DISTINCT item FROM stock_point WHERE source='full_count' AND gap_units<0").fetchall():
        p, _d = RJ._fc_pending(con, sp, it, SF.key_of(sp, it, c2), now, c2)
        out[it] = round(p, 2)
    return out


P0 = pend_all()
spec0 = importlib.util.spec_from_file_location("record_judges_from", os.path.join(OLD, "record_judges.py"))
RJO = importlib.util.module_from_spec(spec0)
spec0.loader.exec_module(RJO)
PO = {}
for (it,) in con.execute("SELECT DISTINCT item FROM stock_point WHERE source='full_count' AND gap_units<0").fetchall():
    c2 = SF.Ctx(con, sp)
    PO[it] = round(RJO._fc_pending(con, sp, it, SF.key_of(sp, it, c2), now, c2)[0], 2)
moved = sorted(k for k in set(P0) | set(PO) if abs(P0.get(k, 0) - PO.get(k, 0)) > 0.01)
check("against the old file only NORTIMER TAB moved (his 12-Oct settlement honoured)", moved == ["NORTIMER TAB"], moved)
print("INFO  pending from the 06-Sep count: %s" % ", ".join("%s %g" % (k, v) for k, v in sorted(P0.items()) if v > 0.5))
check("NORTIMER TAB: settled by him 12-Oct (voucher batch voided) -- never pending", P0.get("NORTIMER TAB", 0) < 0.5, P0.get("NORTIMER TAB"))
check("VINBACTUM DS and KT ROS DT still pending (25 · 101 -- Marg holds them; VINBACTUM is his to ignore)", abs(P0.get("VINBACTUM DS", 0) - 25) < 1 and abs(P0.get("KT ROS DT", 0) - 101) < 1,
      (P0.get("VINBACTUM DS"), P0.get("KT ROS DT")))
row = con.execute("SELECT l.count_id, l.round_no, l.kind, l.batch_no FROM stock_voucher_line l WHERE l.item='AURAB L CAP' AND l.kind='ISSUE' AND l.change<0").fetchone()
if row and P0.get("AURAB L CAP", 0) < 0.5:
    con.execute("SAVEPOINT s957v")
    con.execute("INSERT INTO stock_voucher_void (count_id, round_no, kind, batch_no, by_user, at, reason) VALUES (?,?,?,?,'S957WALK',?, 'walk')", tuple(row) + (now,))
    p, _d = RJ._fc_pending(con, sp, "AURAB L CAP", SF.key_of(sp, "AURAB L CAP", ctx), now, ctx)
    con.execute("ROLLBACK TO s957v")
    con.execute("RELEASE s957v")
    con.commit()
    check("a voided voucher wrote nothing off (AURAB L CAP with its batch voided on this copy is pending again)", p > 0.5, p)
else:
    check("AURAB L CAP's voucher line is there and taken by Marg (the void case)", False, (row, P0.get("AURAB L CAP")))
s952_rows = con.execute("SELECT COUNT(*) FROM s952_point_undo WHERE undone_at IS NULL").fetchone()[0]
t0 = RJ.now_iso()
R = RJ.rejudge_all(con, sp, who="S957WALK", write=True)
print("INFO  judged again: %d (moved %d, withdrawn %d, resized %d, listed %d)" % (R["n"], R["moved"], R["withdrawn"], R["resized"], len(R["listed"])))
k392 = con.execute("SELECT gap_units, judge_words FROM stock_point WHERE id=392").fetchone()
print("INFO  KT ROS DT 23-11: %s" % (k392,))
check("KT ROS DT's 23-11 count unchanged: Marg still holds the older loss of 06-09 (6:11), one strip since", bool(k392 and "older loss" in str(k392[1]) and abs(float(k392[0]) + 15) <= 1), k392)
k394 = con.execute("SELECT gap_units, judge_words FROM stock_point WHERE id=394").fetchone()
print("INFO  NORTIMER TAB 23-11: %s" % (k394,))
check("NORTIMER TAB's 23-11 count: no 'older loss' (settled 12-Oct) -- 6:0 below Marg", bool(k394 and "older loss" not in str(k394[1]) and abs(float(k394[0]) + 60) <= 1), k394)
p390 = con.execute("SELECT gap_units FROM stock_point WHERE id=390").fetchone()
check("TYRO BR's 23-11 count unchanged (about even with Marg)", p390 is not None and p390[0] is not None and abs(float(p390[0])) <= 10, p390)
made = con.execute("SELECT COUNT(*) FROM s952_point_undo WHERE undone_at IS NULL AND at>=?", (t0,)).fetchone()[0]
n = RJ.undo_rejudge(con, who="S957WALK", from_at=t0)
left = con.execute("SELECT COUNT(*) FROM s952_point_undo WHERE undone_at IS NULL").fetchone()[0]
check("the undo of the judge-again puts back exactly what this pass re-made (%d), the earlier %d rows kept" % (made, s952_rows), n == made and left == s952_rows, (n, made, left, s952_rows))
# the shelf figure is unchanged by the S956 body's move (old file against new, every item counted since 18-11)
try:
    spec = importlib.util.spec_from_file_location("stock_figure_from", os.path.join(OLD, "stock_figure.py"))
    SFO = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(SFO)
    its = [r[0] for r in con.execute("SELECT DISTINCT item FROM stock_point WHERE source<>'full_count' AND at>='2026-11-18'")]
    diff = []
    for it in its:
        a = SF.shelf(con, sp, it, None, SF.Ctx(con, sp))
        b = SFO.shelf(con, sp, it, None, SFO.Ctx(con, sp))
        if (a.get("shelf"), a.get("bought"), a.get("same_day_bought")) != (b.get("shelf"), b.get("bought"), b.get("same_day_bought")):
            diff.append(it)
    check("the shelf figure of every item counted since 18-11 (%d) is the same as before (S956's rule moved, unchanged)" % len(its), not diff and len(its) > 5, diff[:5])
except Exception as ex:                                       # noqa: BLE001
    check("the shelf figure compared with the old file", False, ex)
# the recount match: a bill S956 adds after a morning count is a fresh delivery (JAKMAC 5: Darpan's 23-11 10:27 count, bill 100075 dated 23-11)
orig = SF.base
B = dict(qty=0.0, kind="darpan", day="2026-11-23", at="2026-11-23T10:27:25", count_id=None, fixed=False, marg0=None, item="JAKMAC 5", last_bill=None)
SF.base = lambda c, name, ctx=None, exclude_id=None: dict(B) if name == "JAKMAC 5" else orig(c, name, ctx, exclude_id)
con.execute("SAVEPOINT s957m")
try:
    con.execute("UPDATE purchase_order_line SET arrived_at=NULL WHERE arrived_at>='2026-11-23T10:27:25' AND arrived_at<='2026-11-25T09:00:00' AND item LIKE 'JAKMAC 5%'")
    ab = SF.s956_after_bills(con, sp, "JAKMAC 5", B) if hasattr(SF, "s956_after_bills") else set()
    H = SW._s936_match(con, sp, "JAKMAC 5", "2026-11-25T09:00:00", 200, 10, None)
    print("INFO  JAKMAC 5: after-count bills %s; match %s" % (sorted(ab), (H or {}).get("what")))
    check("JAKMAC 5 short by 200 after the 23-11 morning count: the match names bill 100075 (dated that day, added after the count by S956)",
          bool(H and H.get("bill") == "100075"), (H or {}).get("what"))
    H2 = SW._s936_match(con, sp, "JAKMAC 5", "2026-11-25T09:00:00", 130, 10, None)
    check("a shortfall not about any delivery is still no match", H2 is None, (H2 or {}).get("what"))
finally:
    con.execute("ROLLBACK TO s957m")
    con.execute("RELEASE s957m")
    con.commit()
    SF.base = orig
con.close()
print("RESULT: %s" % ("ALL PASS" if not fails else "%d FAIL" % len(fails)))
