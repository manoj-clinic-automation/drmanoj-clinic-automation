#!/usr/bin/env python3
# walk_s952.py · kit S952_RECORD_JUDGES · Sanjeevni session 519 · 25-Nov-2026
# The walk on a COPY of finance.db (and the live spine, read only): python walk_s952.py CODE_DIR COPY_DB [control]
# CODE_DIR holds the finance code to test (the kit's files laid over the live ones, or the live ones alone for the CONTROL, which must go red).
# It removes its own made-up rows first, so it can run twice on one copy. Prints PASS / FAIL / INFO lines and, last, RESULT: ALL PASS | n FAIL.
import os
import sqlite3
import sys

CODE, DB = sys.argv[1], sys.argv[2]
CONTROL = len(sys.argv) > 3 and sys.argv[3] == "control"
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [CODE] + [x for x in sys.path if os.path.abspath(x or ".") != _HERE]   # never the kit's own folder: the CONTROL must not import the kit
os.environ["FINANCE_DB"] = DB
MARK = "S952WALK"
fails = []


def check(name, ok, info=""):
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, (" -- " + str(info)) if info else ""))
    if not ok:
        fails.append(name)


def info(s):
    print("INFO  " + str(s))


con = sqlite3.connect(DB, timeout=60)
import stock_watch as SW                                      # noqa: E402
import stock_record as SR                                     # noqa: E402
import stock_figure as SF                                     # noqa: E402
import porders as PO                                          # noqa: E402
try:
    import record_judges as RJ                                # noqa: E402
except Exception:                                             # noqa: BLE001 -- the control has none
    RJ = None
info("code %s · record_judges %s" % (CODE, (RJ.VERSION if RJ else "absent")))
SW.ensure(con)
if RJ:
    RJ.ensure(con)
    RJ.set_switches(con, True)                                # as the install leaves them (an earlier undo leaves them off)
# the walk's own made-up rows from an earlier run, first
pids = [r[0] for r in con.execute("SELECT id FROM stock_point WHERE by=?", (MARK,))]
for p in pids:
    con.execute("DELETE FROM stock_watch_loss_line WHERE point_id=?", (p,))
    con.execute("DELETE FROM stock_trace WHERE item_norm IN (SELECT item_norm FROM stock_point WHERE id=?) AND trigger='point' AND opened_at>=(SELECT at FROM stock_point WHERE id=?)", (p, p))
con.execute("DELETE FROM stock_watch_loss_line WHERE packing=?", (MARK,))
con.execute("DELETE FROM stock_point WHERE by=?", (MARK,))
con.commit()
sp = SW.Spine()
check("the spine reads", getattr(sp, "ok", False))
L0 = {r[0]: r[1:] for r in con.execute("SELECT id, billed_bill_no, supplied, missing, billed_qty FROM purchase_order_line")}
try:
    ao0 = len(SF.arrivals_open(con, sp))
except Exception:                                             # noqa: BLE001
    ao0 = -1

# 1 · the pairing: detect_supplies (the scan repair runs first in it), the record rebuilt, Count now judged to its bill, every count again
n = PO.detect_supplies(con)
info("detect_supplies: %s line(s) marked / righted" % n)
B = SR.build(con, sp)
check("the stock of record rebuilds", bool(B.get("ok")), "%s rows" % B.get("n"))
SW._s934_settle(con, sp)
if RJ:
    R = RJ.rejudge_all(con, sp, who=MARK, write=True)
    info("judged again: %d (moved %d, withdrawn %d, resized %d, listed %d)" % (R["n"], R["moved"], R["withdrawn"], R["resized"], len(R["listed"])))


def line(lid):
    r = con.execute("SELECT billed_bill_no, supplied, missing FROM purchase_order_line WHERE id=?", (lid,)).fetchone()
    return (str(r[0] or ""), r[1], r[2]) if r else ("?", None, None)


for lid, bill, order in ((172, "234", 69), (216, "238", 83), (261, "242", 101), (284, "250", 107)):
    check("order %d's TYRO BR line is answered by its scanned bill %s" % (order, bill), line(lid)[0] == bill, line(lid))
b139 = line(139)
check("order 58's TYRO BR line holds no bill and is not an arrival (it never came on its order's bill 226)", b139[0] == "" and int(b139[2] or 0) == 1 and int(b139[1] or 0) == 0, b139)
check("order 90's TYRO BR line (reception: missing) holds no bill", line(237)[0] == "", line(237))
p390 = con.execute("SELECT status, expected_units, gap_units, basis, %s FROM stock_point WHERE id=390" % ("judge_words" if RJ else "NULL")).fetchone()
check("TYRO BR's Count now of 23-11 (point 390) is judged about even with Marg (within a strip)", p390 is not None and p390[0] == "settled" and p390[2] is not None and abs(float(p390[2])) <= 10, p390)
ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE point_id=390 AND void_at IS NULL").fetchone()[0]
check("no loss line stands for point 390", ll == 0, ll)
check("point 390 carries its words", bool(p390 and p390[4] and "Marg" in str(p390[4])), p390[4] if p390 else None)
fz = con.execute("SELECT void_at FROM stock_watch_loss_line WHERE point_id=393").fetchone()
check("FENARIC T4's false loss of 23-11 (a tap not on its order's scanned bill) is withdrawn", fz is not None and fz[0] is not None, fz)
zb = con.execute("SELECT void_at, gap_units FROM stock_watch_loss_line WHERE point_id=384").fetchone()
check("ZIBON EXTRA's real loss of 18-11 stands, sized against Marg at that moment (15:3, not 17:4)", zb is not None and zb[0] is None and abs(float(zb[1]) - 153) < 1, zb)

# 1b · the reviewer's cases: a linked bill dated differently in the spine; the 06-Sep full count's shortfall Marg never wrote off; the switch
if RJ is not None and hasattr(SF, "_s952_keyed"):
    keep = con.execute("SELECT billed_qty, billed_bill_no, billed_date, billed_units FROM purchase_order_line WHERE id=65").fetchone()
    con.execute("UPDATE purchase_order_line SET billed_qty=NULL, billed_bill_no=NULL, billed_date=NULL, billed_units=NULL WHERE id=65")
    r = con.execute("SELECT l.id, l.item, l.order_id, o.vendor, o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.id=65").fetchone()
    h = SF.carried(con, sp, dict(line_id=r[0], item=r[1], order_id=r[2], vendor=r[3], order_at=r[4], billed_bill_no=None), SF.Ctx(con, sp))
    con.execute("UPDATE purchase_order_line SET billed_qty=?, billed_bill_no=?, billed_date=?, billed_units=? WHERE id=65", keep)
    con.commit()
    check("an order whose linked bill is dated differently in the spine (A000211: 15-10 / 13-10) is still carried by it", bool(h and SF._bill(h.get("bill")) == "A000211"), h and (h.get("bill"), h.get("date"), h.get("how")))
    k392 = con.execute("SELECT gap_units, judge_words FROM stock_point WHERE id=392").fetchone()
    check("KT ROS DT's 23-11 count: the 06-Sep full count's shortfall Marg never wrote off is not a new loss", bool(k392 and k392[1] and "older loss of 06-09" in k392[1] and float(k392[0]) > -16), k392)
    pt, _d = RJ._pending_loss(con, sp, "TYRO BR", "TYRO BR", "2026-11-23T10:07:44", "2026-11-22", 390, SF.Ctx(con, sp))
    check("TYRO BR: nothing pending -- the full count's 23:0 written off in Marg (15-10); the 12-10 line was booked against an old count, not the record", abs(pt) < 1, pt)
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('count.judge_by_record','0','walk')")
    con.commit()
    Eoff = SW._s952_judge(con, sp, "TYRO BR", SW.now_iso(), 500)
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('count.judge_by_record','1','walk')")
    con.commit()
    check("the switch count.judge_by_record=0 puts the old judgment back", Eoff is None)
else:
    check("an order whose linked bill is dated differently in the spine is still carried by it", False, "no rule 0")
    check("KT ROS DT's 23-11 count is not a new loss", False, "no record_judges")

# 1c · the second look's case: an evening count is judged to its day's end, never against the day's start
if RJ is not None and hasattr(SF, "_s952_keyed"):
    it = "TRAMATEE P TAB 15T"
    me = RJ.marg_end(con, sp, it, "2026-11-23")
    Ee = RJ.judge(con, sp, it, "2026-11-23T19:05:00", float(me["figure"]))
    check("an evening count of 23-11 exactly at Marg's end of day is judged 'matches Marg' (to the day's end)", Ee.get("mode") == "evening" and abs(float(Ee["expected"]) - float(me["figure"])) < 0.5
          and "matches Marg" in (Ee.get("words") or ""), (Ee.get("mode"), Ee.get("expected"), Ee.get("words")))
    _now = SW.now_iso
    SW.now_iso = lambda: _now()[:10] + "T19:05:00"            # the evening count being saved now: its day's sales are not in yet
    try:
        Pe = SW.write_point(con, it, float(me["figure"]), "spot", MARK, silent=True)
    finally:
        SW.now_iso = _now
    st_e = con.execute("SELECT status, expected_units FROM stock_point WHERE id=?", (Pe["id"],)).fetchone()
    check("... and one saved this evening waits for its day's sale report (no verdict against the day's start, no loss line)", st_e[0] == "awaits_sales" and st_e[1] is None
          and con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE point_id=?", (Pe["id"],)).fetchone()[0] == 0, (st_e, Pe.get("verdict")))
else:
    check("an evening count is judged to its day's end", False, "no record_judges")

# 2 · a made-up count below Marg by exactly a delivery (TYRO BR, 21-11 10:00 -- Marg's 20-11 print, bill 250 keyed after it: 663)
cur = con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status, settled_at) VALUES ('TYRO BR','TYRO BR','2026-11-21T10:00:00',163,'spot',?, 'settled','2026-11-21T10:00:00')", (MARK,))
pd = int(cur.lastrowid)
con.commit()
if RJ:
    RJ.rejudge_all(con, sp, who=MARK, write=True, since="2026-11-21", ids={pd})
r = con.execute("SELECT expected_units, gap_units, %s FROM stock_point WHERE id=?" % ("judge_words" if RJ else "NULL"), (pd,)).fetchone()
check("a count below Marg by exactly a delivery is worded as such (bill 250)", r is not None and r[2] is not None and "about a delivery" in r[2] and "250" in r[2], r)
check("... and books no loss line", con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE point_id=? AND void_at IS NULL", (pd,)).fetchone()[0] == 0)

# 3 · a made-up older loss not yet written off is not booked twice (the live door: write_point, now)
item = "GEMCAL XT TABLETS"
_now0 = SW.now_iso
SW.now_iso = lambda: _now0()[:10] + "T10:30:00"               # a morning count, whatever the clock says (an evening one waits, 1c)
E0 = RJ.judge(con, sp, item, SW.now_iso(), None) if RJ else None
exp0 = float(E0["expected"]) if (E0 and E0.get("expected") is not None) else None
if exp0 is None:                                              # the control: the figure the old door judges on
    exp0 = float(SF.expect_for_point(con, sp, item).get("expected") or 0)
con.execute("INSERT INTO stock_watch_loss_line (at, item, gap_units, pack, packing, mrp_p, point_id) VALUES (?,?,?,?,?,?,NULL)",
            (SW.now_iso()[:10] + "T00:00:01", item, 50.0, 15, MARK, 0))
con.commit()
try:
    P = SW.write_point(con, item, exp0 - 50.0, "spot", MARK, silent=True, hold=False)
finally:
    SW.now_iso = _now0
w = con.execute("SELECT gap_units, %s FROM stock_point WHERE id=?" % ("judge_words" if RJ else "NULL"), (P["id"],)).fetchone()
info("made-up count %s: expected %s, gap %s, verdict '%s', words '%s'" % (item, P.get("expected"), P.get("gap"), P.get("verdict"), w[1] if w else ""))
check("a short the size of an older loss Marg still holds is NOT a new loss (no loss line)", P.get("loss_line") is None and con.execute(
    "SELECT COUNT(*) FROM stock_watch_loss_line WHERE point_id=?", (P["id"],)).fetchone()[0] == 0, P.get("verdict"))
check("... worded 'Marg still holds the older loss'", bool(w and w[1] and "older loss" in w[1]), w)

# 4 · idempotent; the Stock check page reads the words; the undo
try:
    _rj_ok = RJ is not None and hasattr(SF, "_s952_scan_bills")
except Exception:                                             # noqa: BLE001
    _rj_ok = False
if _rj_ok:
    check("a second repair pass finds nothing to do", len(RJ.plan_repair(con, sp)["actions"]) == 0)
else:
    check("a second repair pass finds nothing to do", False, "no record_judges")
try:
    import stock_check as SC                                  # noqa: PLC0415
    rec = SC.record(con)
    c390 = [c for c in rec.get("counts") or [] if c["id"] == 390]
    check("the Stock check page lists point 390 with its words", bool(c390) and "Marg" in str(c390[0].get("note") or ""), (c390[0].get("note") if c390 else None))
except Exception as ex:                                       # noqa: BLE001
    check("the Stock check page lists point 390 with its words", False, ex)
try:
    ao1 = len(SF.arrivals_open(con, sp))
except Exception:                                             # noqa: BLE001
    ao1 = -1
info("arrivals the owner is told Marg never received: %s before, %s after" % (ao0, ao1))
if _rj_ok:
    C = RJ.self_check(con, sp)
    info("self-check: %d line(s): %s" % (len(C["lines"]), "; ".join("%s %s" % (x["kind"], x["item"]) for x in C["lines"][:8])))
    check("the self-check runs and reads only", C.get("ok") is True)
    con.execute("DELETE FROM stock_watch_loss_line WHERE point_id IN (SELECT id FROM stock_point WHERE by=?)", (MARK,))
    con.execute("DELETE FROM stock_watch_loss_line WHERE packing=?", (MARK,))
    con.execute("DELETE FROM stock_point WHERE by=?", (MARK,))
    con.commit()
    n1, n2 = RJ.undo_rejudge(con), RJ.undo_repairs(con)
    L1 = {r[0]: r[1:] for r in con.execute("SELECT id, billed_bill_no, supplied, missing, billed_qty FROM purchase_order_line")}
    moved_back = all(L1.get(k) == L0.get(k) for k in (139, 172, 216, 237, 261, 284))
    check("the undo puts the order lines back (%d judgments, %d lines)" % (n1, n2), moved_back, [(k, L1.get(k)) for k in (172, 216, 237)])
    p = con.execute("SELECT gap_units FROM stock_point WHERE id=384").fetchone()
    check("the undo puts the judgments back (ZIBON EXTRA's 18-11 at its old -17:4)", p is not None and abs(float(p[0]) + 174) < 1, p)
else:
    check("the undo puts the order lines back", False, "no record_judges")
con.close()
print("RESULT: %s" % ("ALL PASS" if not fails else "%d FAIL" % len(fails)))
