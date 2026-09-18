#!/usr/bin/env python
"""S312_CLAIM_QUEUE selftest -- claim_queue.py alone, over an in-memory
database, with negative controls.  No Flask, no live file, no network.

It tests the things a wrong claim queue would get wrong QUIETLY: a second mark
making a second claim, a withdrawn line vanishing instead of being recorded, a
14-day claim sinking to the bottom, Darpan settling his own claim, and -- the
one that matters most -- the self-close firing on evidence it does not have.
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claim_queue as cq                                          # noqa: E402

OK = FAIL = 0


def chk(cond, what):
    global OK, FAIL
    if cond:
        OK += 1
    else:
        FAIL += 1
        print("  FAIL: %s" % what)


def db():
    con = sqlite3.connect(":memory:")
    cq.ensure(con)
    return con


def main():
    # ---- 1 raising -------------------------------------------------------
    con = db()
    chk(cq.raise_for(con, 1, "TYRO BR TAB", 12, 45000, "manoj") == "new", "first mark makes a claim")
    chk(cq.raise_for(con, 1, "TYRO BR TAB", 12, 45000, "manoj") == "already", "a second mark is not a second claim")
    chk(cq.raise_for(con, 1, "tyro  br   tab", 12, 45000, "manoj") == "already",
        "spacing and case do not make a second claim (norm_key)")
    chk(con.execute("SELECT COUNT(*) FROM claim_line").fetchone()[0] == 1, "exactly one row")
    chk(cq.raise_for(con, 2, "TYRO BR TAB", 3, 900, "manoj") == "new", "a different count is a different claim")
    chk(cq.raise_for(con, 1, "", None, None, "manoj") == "already", "an empty item raises nothing")

    # ---- 2 the state machine --------------------------------------------
    con = db()
    cq.raise_for(con, 1, "ROSIKA FORTE", 7, 21000, "manoj")
    cid = con.execute("SELECT id FROM claim_line").fetchone()[0]
    ok, _ = cq.answer(con, cid, "not_an_answer", "", "darpan")
    chk(not ok, "NEGATIVE: an answer that is not on the list is refused")
    ok, _ = cq.answer(con, cid, "sold_no_bill", "yaad hai", "darpan")
    chk(ok, "Darpan's answer is taken")
    chk(con.execute("SELECT state FROM claim_line WHERE id=?", (cid,)).fetchone()[0] == "contacted",
        "open -> contacted")
    ok, _ = cq.answer(con, cid, "found", "", "darpan")
    chk(ok, "he may change his answer while it is still contacted")
    ok, _ = cq.settle(con, cid, "not_an_outcome", "", "manoj")
    chk(not ok, "NEGATIVE: an outcome that is not on the list is refused")
    ok, _ = cq.settle(con, cid, "sold_no_bill", "", "manoj")
    chk(ok and con.execute("SELECT state FROM claim_line WHERE id=?", (cid,)).fetchone()[0] == "settled",
        "the owner settles")
    ok, msg = cq.answer(con, cid, "found", "", "darpan")
    chk(not ok, "NEGATIVE: Darpan cannot reopen a settled claim")
    # THE ONE THAT MATTERS: the line is still marked RECOVER and always will be --
    # the mark is what the count recorded.  A page read must NOT resurrect the
    # settlement.  Only a word given AFTER the settlement reopens it.
    chk(cq.raise_for(con, 1, "ROSIKA FORTE", 7, 21000, "manoj") == "settled",
        "NEGATIVE: a settled claim is NOT reopened by an old mark (a page read)")
    chk(cq.raise_for(con, 1, "ROSIKA FORTE", 7, 21000, "manoj",
                     word_at="2000-01-01T00:00:00") == "settled",
        "NEGATIVE: nor by a word older than the settlement")
    chk(cq.raise_for(con, 1, "ROSIKA FORTE", 7, 21000, "manoj",
                     word_at="2099-01-01T00:00:00") == "reopened",
        "a word given AFTER the settlement reopens the SAME claim")
    chk(con.execute("SELECT COUNT(*) FROM claim_line").fetchone()[0] == 1, "still exactly one row")
    chk(con.execute("SELECT state FROM claim_line").fetchone()[0] == "open", "and it is open again")

    # ---- 3 sync_from_words, both directions ------------------------------
    con = db()
    n, r, g = cq.sync_from_words(con, 1, [dict(item="A TAB", short_qty=2, value_p=100),
                                          dict(item="B CAP", short_qty=1, value_p=50)], "hub")
    chk((n, r, g) == (2, 0, 0), "two pursued lines make two claims")
    n, r, g = cq.sync_from_words(con, 1, [dict(item="A TAB", short_qty=2, value_p=100),
                                          dict(item="B CAP", short_qty=1, value_p=50)], "hub")
    chk((n, r, g) == (0, 0, 0), "reading the page twice changes nothing (idempotent)")
    n, r, g = cq.sync_from_words(con, 1, [dict(item="A TAB", short_qty=2, value_p=100)], "hub")
    chk(g == 1, "a line no longer pursued is withdrawn")
    # settle the survivor, then read the page twice more: it must stay settled
    sid = con.execute("SELECT id FROM claim_line WHERE item='A TAB'").fetchone()[0]
    cq.settle(con, sid, "written_off", "", "manoj")
    for _ in range(2):
        cq.sync_from_words(con, 1, [dict(item="A TAB", short_qty=2, value_p=100)], "hub")
    chk(con.execute("SELECT state FROM claim_line WHERE id=?", (sid,)).fetchone()[0] == "settled",
        "NEGATIVE: reading the hub twice does NOT resurrect a settled claim")
    chk(cq.step8_state(con, 1, 1) == "done", "so step 8 STAYS done once it is done")
    row = con.execute("SELECT state, outcome FROM claim_line WHERE item='B CAP'").fetchone()
    chk(tuple(row) == ("settled", "withdrawn"), "withdrawn is RECORDED, never deleted")
    chk(con.execute("SELECT COUNT(*) FROM claim_line").fetchone()[0] == 2, "nothing was deleted")

    # ---- 4 ageing to the top (D471) --------------------------------------
    con = db()
    cq.raise_for(con, 1, "NEW ONE", 1, 10, "m", ts="2026-09-17T10:00:00")
    cq.raise_for(con, 1, "OLD ONE", 1, 10, "m", ts="2026-09-01T10:00:00")
    cq.raise_for(con, 1, "MIDDLE", 1, 10, "m", ts="2026-09-10T10:00:00")
    q = cq.queue(con, now="2026-09-18T06:00:00")
    chk([x["item"] for x in q][0] == "OLD ONE", "a 17-day claim sorts to the TOP")
    chk(q[0]["aged"] is True and q[1]["aged"] is False, "only the aged one is flagged aged")
    chk([x["item"] for x in q][1:] == ["MIDDLE", "NEW ONE"], "the rest stay oldest-first")
    chk(cq.summary(con, 1, now="2026-09-18T06:00:00")["aged"] == 1, "the summary counts one aged")

    # ---- 5 step 8 (D544) -------------------------------------------------
    con = db()
    chk(cq.step8_state(con, 1, 0) == "wait", "no pursued line -> waiting")
    cq.sync_from_words(con, 1, [dict(item="A TAB"), dict(item="B CAP")], "hub")
    chk(cq.step8_state(con, 1, 2) == "now", "claims outstanding -> now")
    ids = [r[0] for r in con.execute("SELECT id FROM claim_line").fetchall()]
    cq.settle(con, ids[0], "written_off", "", "manoj")
    chk(cq.step8_state(con, 1, 2) == "now", "one of two settled is still now")
    cq.settle(con, ids[1], "sold_no_bill", "", "manoj")
    chk(cq.step8_state(con, 1, 2) == "done", "EVERY pursued line terminal -> DONE (the whole point)")

    # ---- 6 the sweep, and what it must NOT do ----------------------------
    con = db()
    con.execute("CREATE TABLE purchase_line (item TEXT, qty INTEGER, direction TEXT)")
    con.execute("INSERT INTO purchase_line VALUES ('A TAB', 5, 'PURCHASE')")
    con.execute("CREATE TABLE purchase_bill (supplier TEXT, bill_no TEXT, bill_date TEXT, amount_p INTEGER)")
    cq.raise_for(con, 1, "A TAB", 2, 100, "m", ts="2026-09-01T10:00:00")
    chk(cq._returns_available(con) is False,
        "NEGATIVE: an ordinary PURCHASE row is not a return -- the rule stays asleep")
    s = cq.sweep(con)
    chk(s["closed_return"] == 0, "NEGATIVE: the sweep closes nothing on a purchase")
    chk(con.execute("SELECT state FROM claim_line").fetchone()[0] == "open", "the claim is untouched")
    # a credit note is a candidate, never a close
    con.execute("INSERT INTO purchase_bill VALUES ('L K DRUG','435','2026-09-05',-403300)")
    s = cq.sweep(con)
    chk(s["flagged"] == 1 and s["closed_return"] == 0, "a credit note is FLAGGED, never closes")
    chk(con.execute("SELECT state FROM claim_line").fetchone()[0] == "open",
        "NEGATIVE: the claim is STILL open after a credit note -- it names no item")
    chk("candidate only" in (con.execute("SELECT candidate FROM claim_line").fetchone()[0] or ""),
        "and the line says so in as many words")
    # now store a real return and watch the rule wake by itself
    con.execute("INSERT INTO purchase_line VALUES ('A TAB', -2, 'RETURN')")
    chk(cq._returns_available(con) is True, "a stored return wakes the rule with no code change")
    s = cq.sweep(con)
    chk(s["closed_return"] == 1, "the return closes the claim")
    row = con.execute("SELECT state, outcome, closed_auto FROM claim_line").fetchone()
    chk(tuple(row) == ("settled", "returned_supplier", 1), "settled by itself, and marked as automatic")

    # ---- 7 the sweep's live rule: a later count --------------------------
    con = db()
    con.execute("CREATE TABLE stock_diff (id INTEGER PRIMARY KEY, count_id INTEGER, item TEXT, diff INTEGER)")
    con.execute("CREATE TABLE stock_count (id INTEGER PRIMARY KEY, submitted_at TEXT)")
    cq.raise_for(con, 1, "C SYP", 1, 10, "m", ts="2026-09-01T10:00:00")
    con.execute("INSERT INTO stock_count VALUES (2,'2026-08-01T10:00:00')")
    con.execute("INSERT INTO stock_diff VALUES (1,2,'C SYP',0)")
    chk(cq.sweep(con)["closed_count"] == 0,
        "NEGATIVE: a count taken BEFORE the claim proves nothing")
    con.execute("UPDATE stock_count SET submitted_at='2026-09-20T10:00:00' WHERE id=2")
    chk(cq.sweep(con)["closed_count"] == 1, "a LATER count that finds it agreeing closes the claim")
    con2 = db()
    con2.execute("CREATE TABLE stock_diff (id INTEGER PRIMARY KEY, count_id INTEGER, item TEXT, diff INTEGER)")
    con2.execute("CREATE TABLE stock_count (id INTEGER PRIMARY KEY, submitted_at TEXT)")
    cq.raise_for(con2, 1, "C SYP", 1, 10, "m", ts="2026-09-01T10:00:00")
    con2.execute("INSERT INTO stock_count VALUES (2,'2026-09-20T10:00:00')")
    con2.execute("INSERT INTO stock_diff VALUES (1,2,'C SYP',-4)")
    chk(cq.sweep(con2)["closed_count"] == 0,
        "NEGATIVE: a later count that still finds it SHORT closes nothing")

    # ---- 8 ensure() is additive and idempotent ---------------------------
    con = db()
    cq.ensure(con); cq.ensure(con)
    chk(con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='claim_line'").fetchone()[0] == 1,
        "ensure() twice leaves one table")
    cq.raise_for(con, 1, "X", 1, 1, "m")
    cq.ensure(con)
    chk(con.execute("SELECT COUNT(*) FROM claim_line").fetchone()[0] == 1, "ensure() never loses a row")

    print("SELFTEST %d checks, %d failed" % (OK + FAIL, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
