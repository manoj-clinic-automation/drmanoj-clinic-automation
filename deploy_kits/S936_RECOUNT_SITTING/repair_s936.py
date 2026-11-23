#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""repair_s936.py -- kit S936_RECOUNT_SITTING (23-Nov-2026, Sanjeevni session 506). THE OWNER'S D1046, its first repair: TRAMATEE P.
    python3 -B repair_s936.py <finance.db> [--dry] [--before PATH]       (run from the folder holding stock_watch.py / stock_figure.py)
Saturday 21-11 10:43 Darpan counted TRAMATEE P TAB 15T 9:4 (point 388) without Mannat's carton of bill 502 (40 strips, 20-11); it became the
shelf, booked loss line 7 and trace 35 and put 50 strips on Monday's order list. Monday 23-11 10:12 he counted 44:0. This one-off, guarded
row by row (it changes NOTHING unless every row is exactly as recorded at S505's close):
  * point 388 -> 'recounted' (never a base again), its note says why; loss line 7 voided; trace 35 closed (status 'fixed');
  * the 23-11 count (44:0 = 660 tabs) re-judged against the base before it, now that 388 is out (its expected / gap rewritten, no loss line:
    a repair, not a fresh count); the owner's two day lines (21-11, 23-11) rewritten.
The rows' values before are written to --before (JSON) for undo_s936.sh. Idempotent: a second run says ALREADY. No patient data is read or
printed (an item, its counts, a bill number). Last line: 'RESULT: REPAIRED' | 'RESULT: ALREADY' | 'RESULT: REFUSED -- why'."""
import json
import os
import sqlite3
import sys

ITEM = "TRAMATEE P TAB 15T"
P388 = dict(id=388, at="2026-11-21T10:43:41", qty=139.0)
LL, TR = 7, 35
TODAY_DAY, TODAY_QTY = "2026-11-23", 660.0
WHY = "held for a recount (S936 repair, D1046): short by about bill 502 (MANNAT PHARMA, 20-11), not a loss"


def say(s):
    print(s, flush=True)


def as_of_count(con, sp, SF, pid, at):
    """What the 23-11 10:12 count is judged against, as the system stood at that moment (the review, finding 4): the figure at the END of
    22-11 (the spine held nothing of 23-11 then) -- the shelf figure on the base before the count (388 now left out), else Marg's figure plus
    its taps -- less anything that arrived after the count. The same answer on any day the repair runs."""
    ctx = SF.Ctx(con, sp)
    day = "2026-11-22"
    S = SF.shelf(con, sp, ITEM, day, ctx, exclude_id=pid)
    M = SF.marg(con, sp, ITEM, day, ctx)
    late = float(SF.taps(con, sp, ITEM, at, ctx) or 0) + float(SF.scan_arrivals(con, sp, ITEM, at, ctx) or 0)
    if S.get("approx") or (M and M.get("approx")):
        return dict(expected=None, basis="approx")
    if S.get("shelf") is not None:
        return dict(expected=float(S["shelf"]) - late, basis="shelf")
    if M is not None:
        return dict(expected=float(M["figure"]) + float(M.get("taps") or 0) - late, basis="marg")
    return dict(expected=None, basis="marg")


def main():
    db = os.path.abspath(sys.argv[1])
    dry = "--dry" in sys.argv
    before = sys.argv[sys.argv.index("--before") + 1] if "--before" in sys.argv else None
    sys.path.insert(0, os.getcwd())
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    if not hasattr(SW, "_s936_close_recount"):
        say("RESULT: REFUSED -- stock_watch.py here is not S936's")
        return 2
    con = sqlite3.connect(db, timeout=60)
    SW.ensure(con)
    p = con.execute("SELECT id, item, at, qty_units, status, note, expected_units, gap_units FROM stock_point WHERE id=?", (P388["id"],)).fetchone()
    if not p or p[1] != ITEM or p[2] != P388["at"] or float(p[3]) != P388["qty"]:
        say("RESULT: REFUSED -- point 388 is not TRAMATEE's 9:4 of 21-11 10:43 (%s)" % (p[1:4] if p else "absent",))
        return 2
    t = con.execute("SELECT id, at, status, note, expected_units, gap_units, basis FROM stock_point WHERE item=? AND substr(at,1,10)=? AND source IN ('spot','darpan') "
                    "AND qty_units=? AND COALESCE(status,'') NOT IN ('superseded','recount','recounted')", (ITEM, TODAY_DAY, TODAY_QTY)).fetchall()
    if len(t) != 1:
        say("RESULT: REFUSED -- %d counts of 44:0 for TRAMATEE on 23-11 (exactly one expected)" % len(t))
        return 2
    t = t[0]
    later = con.execute("SELECT COUNT(*) FROM stock_point WHERE item=? AND at>? AND id<>? AND COALESCE(status,'') NOT IN ('superseded','recount','recounted')",
                        (ITEM, t[1], t[0])).fetchone()[0]
    if later and not (p[4] == "recounted" and "re-judged (S936)" in str(t[3] or "")):
        say("RESULT: REFUSED -- TRAMATEE was counted again after 23-11 %s; the 21-11 and 23-11 rows are left for Claude" % t[1][11:16])
        return 2
    if p[4] == "recounted" and "re-judged (S936)" in str(t[3] or ""):
        say("RESULT: ALREADY -- point 388 is 'recounted' and the 23-11 count was re-judged")
        return 0
    if p[4] not in ("provisional", "settled", "recount", "recounted"):
        say("RESULT: REFUSED -- point 388 has status %s" % p[4])
        return 2
    ll = con.execute("SELECT id, point_id, void_at, void_why FROM stock_watch_loss_line WHERE id=?", (LL,)).fetchone()
    if not ll or int(ll[1] or 0) != P388["id"]:
        say("RESULT: REFUSED -- loss line 7 is not point 388's (%s)" % (ll,))
        return 2
    tr = con.execute("SELECT id, status, seen_by, seen_at, json_extract(findings_json,'$.point_id') FROM stock_trace WHERE id=?", (TR,)).fetchone()
    if not tr or int(tr[4] or 0) != P388["id"]:
        say("RESULT: REFUSED -- trace 35 is not point 388's (%s)" % (tr,))
        return 2
    snap = dict(point_388=dict(status=p[4], note=p[5]), loss_line_7=dict(void_at=ll[2], void_why=ll[3]),
                trace_35=dict(status=tr[1], seen_by=tr[2], seen_at=tr[3]), point_today=dict(id=t[0], note=t[3], expected_units=t[4], gap_units=t[5], basis=t[6]))
    say("found: point 388 (%s, 9:4 of 21-11 10:43), loss line 7 (%s), trace 35 (%s); the 23-11 count %s at %s judged against %s (gap %s)"
        % (p[4], "void" if ll[2] else "standing", tr[1], t[0], t[1][11:16], t[4], t[5]))
    if dry:
        say("RESULT: DRY -- nothing written")
        return 0
    if before:
        with open(before, "w") as fh:
            json.dump(snap, fh, indent=1, default=str)
    ts = SW.now_iso()
    try:
        con.execute("UPDATE stock_point SET status='recounted', note=? WHERE id=?", ("recounted 23-11 %s -- %s" % (t[1][11:16], WHY), P388["id"]))
        con.execute("UPDATE stock_watch_loss_line SET void_at=?, void_why=? WHERE id=? AND void_at IS NULL", (ts, "a missed carton -- recounted 23-11 (S936, D1046)", LL))
        con.execute("UPDATE stock_trace SET status='fixed', seen_by='S936 recount', seen_at=? WHERE id=? AND status<>'fixed'", (ts, TR))
        sp = SW.Spine()
        E = as_of_count(con, sp, SF, t[0], t[1])
        gap = None if E.get("expected") is None else round(TODAY_QTY - float(E["expected"]), 3)
        con.execute("UPDATE stock_point SET expected_units=?, gap_units=?, basis=?, note=? WHERE id=?",
                    (E.get("expected"), gap, E.get("basis"), ((t[3] + " · ") if t[3] else "") + "re-judged (S936): the count of 21-11 was a missed carton", t[0]))
        SW._s936_touch(con)                                    # the stock of record rebuilds (its fingerprint reads the count.% rows)
        SW._audit(con, "s936_repair", dict(item=ITEM, point_388="recounted", loss_line_7="void", trace_35="fixed", point_today=t[0],
                                           expected_was=t[4], gap_was=t[5], expected_now=E.get("expected"), gap_now=gap, basis=E.get("basis")), "S936", t[0])
        con.commit()
    except Exception as e:                                    # noqa: BLE001
        con.rollback()
        say("RESULT: REFUSED -- the write failed, nothing kept (%s)" % str(e)[:160])
        return 2
    for d in ("2026-11-21", TODAY_DAY):
        SW._s928_count_day(con, sp, d)
    import qty_words                                          # noqa: E402
    w = lambda u: qty_words.words(abs(u), packing="1*15", pack=15, name=ITEM) if u is not None else "-"   # noqa: E731
    say("TRAMATEE P TAB 15T: the 21-11 count (9:4) is out of the shelf for good, loss line 7 voided, trace 35 closed; the 23-11 count (44:0) is now "
        "judged against %s (%s figure) -- %s" % (w(E.get("expected")), E.get("basis"), ("matches" if gap is not None and abs(gap) < 0.5 else
                                                                                       ("%s %s" % (w(gap), "short" if (gap or 0) < 0 else "over")) if gap is not None else "no figure")))
    say("RESULT: REPAIRED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
