#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s539.py -- kit S539_NORTIMER_OUT, the data step (brief section 2): keyed, idempotent, never a DELETE, no code edited.

    /usr/bin/python3 -B data_s539.py --db /root/finance/finance.db --finance /root/finance [--dry] [--state]

  finance  the folder whose stock_app.py is S537's (it must carry _void_sql and _voucher_void); read only.
  --dry    step 2 inside ONE transaction that is rolled back; step 3 (which commits through stock_app._voucher_make) is not run on --db;
           step 4 is printed from a scratch copy on which steps 2 and 3 were applied.
  --state  prints step 4 only, from a scratch copy of --db (the installer's state BEFORE / AFTER); writes nothing.
Steps (each prints DATA_S539: lines), all through S537's doors (stock_voucher_void via stock_app._voucher_void, stock_voucher_settle,
stock_app._voucher_make):
  1  voucher 11 BY SHAPE -- count 1, round 2, ISSUE, batch 10, six lines, items exactly the six below; not entered. Anything else -> STOP
     (exit 2, nothing written). Already voided + NORTIMER settled + the five re-made -> ALREADY DONE (exit 0).
  2  ONE transaction: the void of (1, 2, ISSUE, 10) and the settle of NORTIMER TAB for count 1 (each unless present). Commit.
  3  the five re-made: _voucher_pending(con, d, items=FIVE) must be exactly the five with the 6-Sep changes (no other figure, no extra item,
     none held) -> else STOP before making (the void and the settle stay; the owner decides). Then _voucher_make(..., items=FIVE).
  4  printed after, on a scratch copy (amir_stage writes once-only stage events -- never from this step on the live file).
No person, phone or account number is printed."""
import argparse
import os
import re
import shutil
import sqlite3
import sys
import tempfile

ROOT = 1
KEY = (2, "ISSUE", 10)
NORT = "NORTIMER TAB"
FIVE = {"NIMREX P": -11, "NUROKIND LC": -5, "NURVION LC TAB": -38, "OLMETIME H 20": -45, "ONDEM MD 4": -35}
SIX = set(FIVE) | {NORT}
VOID_REASON = "owner 12-Oct 08:42: NORTIMER out of the count for now (strips with Darpan, being sold); the other five re-made"
SETTLE_NOTE = "owner 12-Oct 08:42"


class StopStep(Exception):
    pass


def say(s):
    print("DATA_S539: " + re.sub(r"\d{10,}", "##########", str(s)))


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def remade(con):
    """[(round, kind, batch)] -- the non-voided ISSUE batches of count 1 after round 2 whose lines are exactly the five with their changes."""
    out = []
    bs = {}
    for rno, kind, bno, item, ch in con.execute("SELECT round_no, kind, batch_no, item, change FROM stock_voucher_line WHERE count_id=? AND round_no>2 "
                                                "AND kind='ISSUE' ORDER BY round_no, batch_no, line_no", (ROOT,)):
        bs.setdefault((int(rno), kind, int(bno)), {})[item] = int(ch)
    voided = {(int(r[0]), r[1], int(r[2])) for r in con.execute("SELECT round_no, kind, batch_no FROM stock_voucher_void WHERE count_id=?", (ROOT,))}
    for k, lines in bs.items():
        if k not in voided and lines == FIVE:
            out.append(k)
    return out


def look(con, SA):
    """The state of the three facts, or StopStep when voucher 11 is not what the brief describes."""
    rows = con.execute("SELECT item, change FROM stock_voucher_line WHERE count_id=? AND round_no=? AND kind=? AND batch_no=? ORDER BY line_no",
                       (ROOT,) + KEY).fetchall()
    items = [r[0] for r in rows]
    if len(rows) != 6 or set(items) != SIX:
        raise StopStep("round 2 ISSUE batch 10 of count 1 holds %d line(s) %s, not exactly the six" % (len(rows), items))
    if KEY in SA._s446_entered(con, ROOT):
        raise StopStep("voucher 11 (round 2 ISSUE batch 10) carries a Marg entry -- it is in Marg; nothing written, the owner decides")
    voided = con.execute("SELECT 1 FROM stock_voucher_void WHERE count_id=? AND round_no=? AND kind=? AND batch_no=?", (ROOT,) + KEY).fetchone() is not None
    settled = con.execute("SELECT 1 FROM stock_voucher_settle WHERE count_id=? AND item=?", (ROOT, NORT)).fetchone() is not None
    rm = remade(con)
    if rm and not (voided and settled):
        raise StopStep("a batch with the five exists (%s) but voucher 11 is not voided and settled -- not the brief's state" % rm)
    return dict(lines=[(r[0], int(r[1])) for r in rows], voided=voided, settled=settled, remade=rm)


def step2(con, SA, L):
    """The void and the settle, inside the caller's transaction."""
    out = []
    if L["voided"]:
        out.append("2 voucher 11 already voided -- skipped")
    else:
        ok, w = SA._voucher_void(con, ROOT, KEY[0], KEY[1], KEY[2], "manoj", VOID_REASON)
        if not ok:
            raise StopStep("the void door refused round 2 ISSUE batch 10: %s" % w)
        out.append("2 round 2 ISSUE batch 10: %s" % ("already voided -- skipped" if w == "already" else "VOIDED (stock_voucher_void, by manoj)"))
    if L["settled"]:
        out.append("2 %s already settled for count #%d -- skipped" % (NORT, ROOT))
    else:
        con.execute("INSERT INTO stock_voucher_settle (count_id, item, by_user, at, note) VALUES (?,?,?,?,?)", (ROOT, NORT, "manoj", SA.now_iso(), SETTLE_NOTE))
        out.append("2 %s SETTLED for count #%d (stock_voucher_settle, by manoj)" % (NORT, ROOT))
    return out


def step3(con, SA):
    """The five through _voucher_pending (checked) and _voucher_make. Returns (round, [(key, seq, n)])."""
    for nm in ("_S446_PROOF_CACHE", "_S524_REPORT_CACHE"):
        getattr(SA, nm, {}).clear()
    d = SA._pad_report_data(con, ROOT)
    if con.in_transaction:
        con.commit()
    pend = SA._voucher_pending(con, d, items=set(FIVE))
    held = [h for h in SA._voucher_lines(con, d, items=set(FIVE))[1]]
    got = {p["item"]: int(p["change"]) for p in pend}
    for p in pend:
        say("3 pending: %s %+d (Marg on the count day %s -> %s)" % (p["item"], int(p["change"]), p["marg_from"], p["marg_to"]))
    for h in held:
        say("3 HELD by the guard: %s %+d (Marg's closing of %s holds %s)" % (h["item"], int(h["change"]), h.get("as_on"), h.get("marg_now")))
    if got != FIVE or held or len(pend) != len(FIVE):
        raise StopStep("the five are not pending exactly as on 6-Sep (got %s, held %s) -- nothing made; the void and the settle stay, the owner decides"
                       % (got, [h["item"] for h in held]))
    rno, n = SA._voucher_make(con, d, {"user": "manoj"}, section=None, items=set(FIVE))
    if not rno:
        raise StopStep("_voucher_make made nothing -- the void and the settle stay, the owner decides")
    seqs = SA._voucher_seq(con, ROOT)
    bs = [(int(r[0]), r[1], int(r[2]), int(r[3])) for r in con.execute(
        "SELECT round_no, kind, batch_no, COUNT(*) FROM stock_voucher_line WHERE count_id=? AND round_no=? GROUP BY round_no, kind, batch_no", (ROOT, rno))]
    out = [((b[0], b[1], b[2]), (seqs.get((b[0], b[1], b[2])) or (None,))[0], b[3]) for b in bs]
    for k, sq, nn in out:
        say("3 MADE round %d %s batch %d: %d line(s) -- %s voucher %s" % (k[0], k[1], k[2], nn, SA.VOUCHER_HI.get(k[1], k[1]), sq))
    return rno, out


def print_state(SA, path, tag="4"):
    """Step 4 on a scratch copy at `path`."""
    con = sqlite3.connect(path, timeout=60)
    try:
        for nm in ("_S446_PROOF_CACHE", "_S524_REPORT_CACHE"):
            getattr(SA, nm, {}).clear()
        seqs = SA._voucher_seq(con, ROOT)
        b = SA._s446_batches(con, ROOT)
        st = SA.amir_stage(con, ROOT) or {}
        C = st.get("C") or {}
        say("%s stage %s; C released %s of %s, entered %s, today %d, unreleased %s; held %s" % (
            tag, st.get("stage"), C.get("released"), C.get("total"), C.get("entered"), len(C.get("today") or []), C.get("unreleased"),
            [(h.get("item"), h.get("seq")) for h in C.get("held") or []]))
        say("%s voucher 11 a batch: %s; NORTIMER settled: %s; the five re-made: %s" % (
            tag, KEY in b, con.execute("SELECT 1 FROM stock_voucher_settle WHERE count_id=? AND item=?", (ROOT, NORT)).fetchone() is not None,
            ["%s voucher %s" % (SA.VOUCHER_HI.get(k[1], k[1]), (seqs.get(k) or (None,))[0]) for k in remade(con)]))
        roles = {u: sorted(r[0] for r in con.execute("SELECT role FROM unit_role WHERE unit='medical' AND username=? AND active=1", (u,)))
                 for u in ("amir", "manoj")}
        bd = SA._amir_board_light(con, ROOT, dict(user="amir", role="staff", roles=roles["amir"]), st)
        say("%s AMIR'S BOARD as amir: %d voucher(s): %s" % (tag, len(bd.get("vouchers") or []), ", ".join(
            "%s %d" % (SA.VOUCHER_HI.get(v["kind"], v["kind"]), v["seq"]) for v in bd.get("vouchers") or [])))
        say("%s his line: %s" % (tag, (bd.get("proof") or {}).get("hi")))
        sw = SA._s521_stage_words(con, st)
        say("%s NEEDS-YOU: Count #%d: %s" % (tag, ROOT, sw.get("owner_en")))
        for l in sw.get("owner_lines") or []:
            if "Count #" in l["text"] or "NORTIMER" in l["text"]:
                say("%s NEEDS-YOU: %s" % (tag, l["text"]))
    finally:
        con.close()


def counts(con):
    return {t: con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] for t in ("stock_voucher_void", "stock_voucher_settle", "stock_voucher_line")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--finance", default="/root/finance")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--state", action="store_true")
    a = ap.parse_args()
    fin = os.path.abspath(a.finance)
    sys.path.insert(0, os.path.join(fin, "spine"))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_app as SA                                      # noqa: E402
    if not (os.path.abspath(SA.__file__).startswith(fin) and hasattr(SA, "_void_sql") and hasattr(SA, "_voucher_void") and hasattr(SA, "_voucher_lines")):
        say("STOP: %s is not S537's stock_app -- nothing done" % SA.__file__)
        return 2
    tmp = tempfile.mkdtemp(prefix="s539_data_")
    try:
        if a.state:
            cp = os.path.join(tmp, "state.db")
            copydb(a.db, cp)
            print_state(SA, cp, "state")
            say("STATE OK")
            return 0
        con = sqlite3.connect(a.db, timeout=60)
        say("start on %s (%s)" % (os.path.basename(a.db), "DRY -- step 2 rolled back, step 3 only on a scratch copy" if a.dry else "commits"))
        before = counts(con)
        try:
            L = look(con, SA)
            sq = SA._voucher_seq(con, ROOT).get(KEY)
            say("1 voucher by shape: count #%d round 2 ISSUE batch 10 (%s voucher %s), not entered: %s" % (
                ROOT, SA.VOUCHER_HI.get("ISSUE"), sq[0] if sq else "?", ", ".join("%s %+d" % x for x in L["lines"])))
            say("1 voided %s, %s settled %s, the five re-made %s" % (L["voided"], NORT, L["settled"], L["remade"]))
            if L["voided"] and L["settled"] and L["remade"]:
                say("ALREADY DONE -- nothing written")
                con.close()
                return 0
            if con.in_transaction:
                con.commit()
            con.isolation_level = None
            con.execute("BEGIN IMMEDIATE")
            try:
                for w in step2(con, SA, L):
                    say(w)
                if a.dry:
                    con.execute("ROLLBACK")
                    say("DRY -- step 2 rolled back")
                else:
                    con.execute("COMMIT")
                    say("step 2 committed")
            except Exception:
                if con.in_transaction:
                    con.execute("ROLLBACK")
                raise
            con.isolation_level = ""
            if not a.dry:
                step3(con, SA)
        except StopStep as e:
            say("STOP: %s" % e)
            say("rows before %s -> after %s" % (before, counts(con)))
            con.close()
            return 2
        except Exception as e:                                  # noqa: BLE001
            say("FAILED: %s: %s" % (type(e).__name__, str(e)[:300]))
            con.close()
            return 1
        say("rows before %s -> after %s" % (before, counts(con)))
        con.close()
        cp = os.path.join(tmp, "after.db")
        copydb(a.db, cp)
        if a.dry:
            c2 = sqlite3.connect(cp)
            L2 = look(c2, SA)
            c2.isolation_level = None
            c2.execute("BEGIN IMMEDIATE")
            step2(c2, SA, L2)
            c2.execute("COMMIT")
            c2.isolation_level = ""
            try:
                step3(c2, SA)
            except StopStep as e:
                say("STOP (on the dry copy): %s" % e)
                c2.close()
                return 2
            c2.close()
        print_state(SA, cp)
        say("DRY -- rolled back" if a.dry else "committed")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
