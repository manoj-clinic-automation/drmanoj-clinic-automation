#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s537.py -- kit S537_VOUCHER_GUARD, the data step (brief section 3): keyed, idempotent, never a DELETE.

    /usr/bin/python3 -B data_s537.py --db /root/finance/finance.db --finance /root/finance [--dry] [--schema-only]

  finance        the folder whose stock_app.py / stock_watch.py are the kit's (placed before this step runs; the walk points it at its NEW
                 scratch folder). It must carry stock_app._void_sql, else nothing is done.
  --schema-only  lays the two tables through stock_app._voucher_ensure (the one door) and stops -- the installer runs this BEFORE it pulls the
                 duty map v12 that names the void table.
  --dry          steps 1 and 2 inside ONE transaction that is rolled back (the tables too, laid inside it from VOUCHER_S537_SCHEMA); step 3 is
                 skipped; step 4 is printed from a scratch copy on which steps 1 and 2 were applied.
Steps (each prints DATA_S537: lines):
  1  voucher 29 found BY SHAPE -- count 1, round_no > 5, exactly one batch in that round, kind ISSUE, exactly one line 'ANKLE BINDER BAMBOO L'
     with change -1; anything else in round >= 6 -> STOP (exit 2). Entered -> STOP (the owner decides a RECEIVE +1). Else voided through
     stock_app._voucher_void (already voided -> skipped).
  2  stock_voucher_settle for count 1, 'ANKLE BINDER BAMBOO L' unless present.  Steps 1 and 2 commit together.
  3  stock_watch.ask(con, 'ANKLE BINDER BAMBOO L', 'S537 owner 12-Oct') -- one spot count for Darpan (it commits on its own). Not on --dry.
  4  printed after, on a scratch copy (amir_stage writes once-only stage events -- never from this step on the live file): the orthotic pending
     lines, the held lines, stage A, Amir's board's batches (round 6 absent).
No person, phone or account number is printed."""
import argparse
import os
import re
import shutil
import sqlite3
import sys
import tempfile

ROOT = 1
ITEM = "ANKLE BINDER BAMBOO L"
VOID_REASON = "owner 12-Oct 07:02: Marg already 0 since 04-10, shelf counted 0; his ruling of 04-Oct"
SETTLE_NOTE = "owner 04-Oct ruling + 12-Oct 07:02"
ASK_WHO = "S537 owner 12-Oct"


class StopStep(Exception):
    pass


def say(s):
    print("DATA_S537: " + re.sub(r"\d{10,}", "##########", str(s)))


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def find_v29(con, SA):
    """(round, batch, made_by, made_at) of voucher 29 by its shape, or StopStep."""
    rows = con.execute("SELECT round_no, kind, batch_no, item, change, made_by, made_at FROM stock_voucher_line WHERE count_id=? AND round_no>5 "
                       "ORDER BY round_no, kind, batch_no, line_no", (ROOT,)).fetchall()
    if len(rows) != 1:
        raise StopStep("round >= 6 of count %d holds %d line(s), not exactly one: %s" % (ROOT, len(rows), [tuple(r[:5]) for r in rows][:6]))
    rno, kind, bno, item, ch, by, at = rows[0]
    if kind != "ISSUE" or item != ITEM or int(ch) != -1:
        raise StopStep("the one line of round %s is %s %s %s, not ISSUE %s -1" % (rno, kind, item, ch, ITEM))
    return int(rno), int(bno), by or "", at or ""


def apply(con, SA, v29):
    """Steps 1 and 2 on `con` inside the caller's transaction. Returns the words of what was done."""
    rno, bno = v29[0], v29[1]
    if (rno, "ISSUE", bno) in SA._s446_entered(con, ROOT):
        raise StopStep("voucher 29 (round %d ISSUE batch %d) is ENTERED in Marg -- Marg then holds -1 and a RECEIVE +1 is the owner's decision; nothing written" % (rno, bno))
    ok, w = SA._voucher_void(con, ROOT, rno, "ISSUE", bno, "manoj", VOID_REASON)
    if not ok:
        raise StopStep("the void door refused round %d ISSUE batch %d: %s" % (rno, bno, w))
    w1 = "1 round %d ISSUE batch %d: %s" % (rno, bno, "already voided -- skipped" if w == "already" else "VOIDED (stock_voucher_void, by manoj)")
    if con.execute("SELECT 1 FROM stock_voucher_settle WHERE count_id=? AND item=?", (ROOT, ITEM)).fetchone():
        w2 = "2 %s already settled for count #%d -- skipped" % (ITEM, ROOT)
    else:
        con.execute("INSERT INTO stock_voucher_settle (count_id, item, by_user, at, note) VALUES (?,?,?,?,?)", (ROOT, ITEM, "manoj", SA.now_iso(), SETTLE_NOTE))
        w2 = "2 %s SETTLED for count #%d (stock_voucher_settle, by manoj)" % (ITEM, ROOT)
    return [w1, w2]


def counts(con):
    out = {}
    for t in ("stock_voucher_void", "stock_voucher_settle", "stock_watch_ask", "stock_stage_event"):
        try:
            out[t] = con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        except sqlite3.Error:
            out[t] = None
    return out


def print_after(SA, path, v29):
    """Step 4 on a scratch copy at `path` (steps 1-2 already on it)."""
    con = sqlite3.connect(path, timeout=60)
    try:
        sq = SA._voucher_seq(con, ROOT).get((v29[0], "ISSUE", v29[1]))
        say("4 the voided batch is %s voucher %s (the numbering never shifts)" % (SA.VOUCHER_HI.get("ISSUE"), sq[0] if sq else "?"))
        for nm in ("_S446_PROOF_CACHE", "_S524_REPORT_CACHE"):
            getattr(SA, nm, {}).clear()
        d = SA._pad_report_data(con, ROOT)
        if con.in_transaction:
            con.commit()
        pend = SA._voucher_pending(con, d, section="Orthotics")
        held = SA._voucher_held(con, d, section="Orthotics")
        say("4 orthotic pending lines: %d %s" % (len(pend), [(p["item"], p["change"]) for p in pend][:8]))
        say("4 orthotic held lines: %d %s; %s held: %s" % (len(held), [(h["item"], h["change"], h.get("marg_now")) for h in held][:8], ITEM,
                                                         any(h["item"] == ITEM for h in held)))
        st = SA.amir_stage(con, ROOT, d) or {}
        A, C = st.get("A") or {}, st.get("C") or {}
        say("4 stage %s; A total %s entered %s open %s pending %s proof %s; A held %d" % (st.get("stage"), A.get("total"), A.get("entered"), A.get("open"),
                                                                                   A.get("pending"), (A.get("proof") or {}).get("state"), len(A.get("held") or [])))
        if st.get("stage") in ("C", "done"):
            say("4 C released %s of %s, today %d, held %s" % (C.get("released"), C.get("total"), len(C.get("today") or []),
                                                             [(h.get("item"), h.get("seq")) for h in C.get("held") or []]))
        b = SA._s446_batches(con, ROOT)
        seqs = SA._voucher_seq(con, ROOT)
        vis = [tuple(k) for k in (st.get("visible") or [])]
        say("4 Amir's board batches (the stage's visible): %s" % ", ".join("%s %d" % (SA.VOUCHER_HI.get(k[1], k[1]), (seqs.get(k) or (0,))[0]) for k in vis))
        say("4 round 6 in the batches: %s; open per amir_vouchers_open: %s" % (any(k[0] >= 6 for k in b),
                                                                          [(o["count_id"], o["made"], o["open"]) for o in SA.amir_vouchers_open(con)]))
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--schema-only", action="store_true")
    a = ap.parse_args()
    fin = os.path.abspath(a.finance)
    sys.path.insert(0, os.path.join(fin, "spine"))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_app as SA                                      # noqa: E402
    import stock_watch as SW                                    # noqa: E402
    if not (os.path.abspath(SA.__file__).startswith(fin) and hasattr(SA, "_void_sql") and hasattr(SA, "_voucher_void")
            and hasattr(SA, "VOUCHER_S537_SCHEMA")):
        say("STOP: %s is not the kit's stock_app (no _void_sql) -- nothing done" % SA.__file__)
        return 2
    con = sqlite3.connect(a.db, timeout=60, isolation_level=None)
    say("start on %s (%s)" % (os.path.basename(a.db), "schema only" if a.schema_only else ("DRY -- rolled back, step 3 skipped" if a.dry else "commits steps 1-2 together")))
    if a.schema_only:
        SA._voucher_ensure(con)
        have = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('stock_voucher_void','stock_voucher_settle') ORDER BY name")]
        say("schema: %s present (via stock_app._voucher_ensure)" % ", ".join(have))
        con.close()
        if len(have) != 2:
            say("FAILED: the two tables are not both present")
            return 1
        say("schema committed")
        return 0
    if not a.dry:
        SA._voucher_ensure(con)                                 # the one door; autocommit, before the step's transaction
    before = counts(con)
    try:
        v29 = find_v29(con, SA)                                 # read only (no stock_app call that lays a table before --dry's transaction)
        say("1 voucher by shape: count #%d round %d ISSUE batch %d, one line %s -1, made by %s at %s (its number on Amir's board: step 4)"
            % (ROOT, v29[0], v29[1], ITEM, v29[2], v29[3]))
        con.execute("BEGIN IMMEDIATE")
        try:
            if a.dry:
                for stmt in SA.VOUCHER_S537_SCHEMA.split(";"):
                    if stmt.strip():
                        con.execute(stmt)
            for w in apply(con, SA, v29):
                say(w)
            if a.dry:
                con.execute("ROLLBACK")
                say("DRY -- steps 1-2 rolled back")
            else:
                con.execute("COMMIT")
                say("steps 1-2 committed")
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise
    except StopStep as e:
        say("STOP: %s" % e)
        con.close()
        return 2
    except Exception as e:                                      # noqa: BLE001
        say("FAILED and rolled back: %s: %s" % (type(e).__name__, str(e)[:300]))
        con.close()
        return 1
    if a.dry:
        say("3 skipped (--dry)")
    else:
        try:
            ok, msg, code = SW.ask(con, ITEM, ASK_WHO)
            say("3 stock_watch.ask: %s (%s)" % (msg, code))
        except Exception as e:                                  # noqa: BLE001 -- the void and the settle stand; the spot count is the owner's tap away
            say("3 stock_watch.ask FAILED: %s: %s (the void and the settle stand)" % (type(e).__name__, str(e)[:200]))
    after = counts(con)
    con.close()
    say("rows before %s -> after %s" % (before, after))
    tmp = tempfile.mkdtemp(prefix="s537_data_")
    try:
        cp = os.path.join(tmp, "after.db")
        copydb(a.db, cp)
        if a.dry:
            c2 = sqlite3.connect(cp, isolation_level=None)
            SA._voucher_ensure(c2)
            c2.execute("BEGIN IMMEDIATE")
            apply(c2, SA, v29)
            c2.execute("COMMIT")
            c2.close()
        print_after(SA, cp, v29)
    except Exception as e:                                      # noqa: BLE001
        say("4 could not be printed: %s: %s" % (type(e).__name__, str(e)[:200]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    say("DRY -- rolled back" if a.dry else "committed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
