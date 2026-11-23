#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""synth_s934.py -- kit S934_COUNT_NOW (23-Nov-2026, Sanjeevni session 505). MADE-UP data only, in a scratch folder.
    python3 -B synth_s934.py <dir with the files under test (a copy of /root/finance)> <schema-from: a COPY of finance.db> [--control] [--keep]
Builds in TMPDIR: a finance.db with the copy's schema and NO rows of its own; two made-up spines (spine_build.SCHEMA) -- spine 1 before the
count day's sale report, spine 2 with it (sale bills A5001..A5004 on the count day); Marg's bill chain to the day before (last bill 5000).
Checks: the two modes of an ask (T1-T6), withdraw (T7-T9), the bill check (T10-T13), a Count now to the bill (T14-T17), the judgment once
the sales are in -- shelf basis, Marg basis, a loss beyond the allowance (T18-T24), the carry forward (T25-T26), the routes (T27-T32), the
day's count line (T33). --control runs the SAME checks on the OLD files and must go red. No patient data anywhere. Prints 'RESULT: ...'."""
import datetime as dt
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time

RUN, FAILS = [0], []


def say(s):
    print(re.sub(r"\d{8,}", lambda m: "#" * len(m.group(0)), str(s)), flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("ok   " if cond else "FAIL ") + label + (("  [%s]" % str(got)[:300]) if (got is not None and not cond) else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def attempt(label, fn):
    """Run fn; an exception is a FAIL with its name (the control's old files lack the new doors)."""
    try:
        return fn()
    except Exception as e:                                    # noqa: BLE001
        check(label + " (raised %s: %s)" % (type(e).__name__, str(e)[:140]), False)
        return None


def schema_from(copy, path):
    src = sqlite3.connect("file:%s?mode=ro" % copy, uri=True)
    dst = sqlite3.connect(path)
    for (sql,) in src.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name"):
        try:
            dst.execute(sql)
        except sqlite3.Error:
            pass
    dst.commit()
    src.close()
    return dst


os.environ["TZ"] = "Asia/Kolkata"
time.tzset()
D = dt.date.today().isoformat()                               # the count day (today, IST)
Y = (dt.date.today() - dt.timedelta(days=1)).isoformat()
Z = (dt.date.today() - dt.timedelta(days=2)).isoformat()
CAP = "W934CAP00000000000000000000000001"                    # printed Y 09:30 as on Z -> stands for the end of Z
T1D = (dt.date.today() + dt.timedelta(days=1)).isoformat()   # the morning after the count day: the report covering it is taken then
ITEMS = (("W934 SHELF 10", 300.0), ("W934 MARG 10", 100.0), ("W934 LOSS 10", 100.0), ("W934 TIME 10", 50.0), ("W934 ASK 10", 40.0),
         ("W934 SWAP 10", 40.0), ("W934 ROUTE 10", 60.0), ("W934 WD 10", 20.0), ("W934 LATE 10", 100.0), ("W934 PUR 10", 100.0),
         ("W934 TWICE 10", 100.0), ("W934 RET 10", 100.0))
SALES_D = (("A005001", "W934 SHELF 10", 20.0), ("A005002", "W934 SHELF 10", 30.0), ("A005003", "W934 SHELF 10", 10.0), ("A005004", "W934 SHELF 10", 40.0),
           ("A005001", "W934 MARG 10", 10.0), ("A005003", "W934 MARG 10", 20.0),
           ("A005001", "W934 LOSS 10", 10.0),
           ("A005001", "W934 RET 10", 10.0), ("A005004", "W934 RET 10", 10.0))


def make_spine(fin, path, with_day_sales):
    sys.path.insert(0, os.path.join(fin, "spine"))
    import spine_build as SB                                  # noqa: E402
    sys.path.pop(0)
    sys.modules.pop("spine_build", None)
    sp = sqlite3.connect(path)
    sp.executescript(SB.SCHEMA)
    sp.execute("INSERT INTO sp_meta VALUES ('built', ?)", ((D if with_day_sales else Y) + "T08:00:00+05:30",))
    E = "INSERT INTO sp_export VALUES (?,?,?,?,?,?,?,?,?,?,?)"
    sp.execute(E, (CAP, "closing", "STOCK_CLOSING", Y.replace("-", "") + "-093000", None, None, Z, 1, None, "closing", "walk"))
    sp.execute(E, ("W934SALE", "sale", "SALE_BILLWISE", ((T1D if with_day_sales else D).replace("-", "") + "-074000"), "2026-11-01", (D if with_day_sales else Y), None, 1, None, "sale", "walk"))
    for name, units in ITEMS:
        k = name[:20]
        sp.execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", (k, name, "1*10", "strip", "2026-09-01", Z))
        sp.execute("INSERT INTO sp_close_name VALUES (?,?,?,?,?)", (CAP, name, "1*10", k, units))
        sp.execute("INSERT INTO sp_close VALUES (?,?,?,?)", (Z, k, units, CAP))
        sp.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (k, "2026-11-01", "OPENING", units, "OPEN"))
    if with_day_sales:
        for bill, name, units in SALES_D:
            sp.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (name[:20], D, "SALE", -units, bill))
        sp.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", ("W934 RET 10", D, "SALE_RETURN", 5.0, "CN000302"))       # a patient's return that day
        sp.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", ("W934 PUR 10", D, "PURCHASE", 30.0, "WPHARMA/K934"))     # a bill dated the count day
    sp.commit()
    sp.close()


def main():
    fin, copy = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    control = "--control" in sys.argv
    scratch = tempfile.mkdtemp(prefix="s934_", dir=os.environ.get("TMPDIR") or "/tmp")
    try:
        run(fin, copy, control, scratch)
    finally:
        if "--keep" in sys.argv:
            say("KEPT %s" % scratch)
        else:
            shutil.rmtree(scratch, ignore_errors=True)
    say("RESULT: %s" % ("ALL PASS" if not FAILS else "%d FAIL" % len(FAILS)))
    sys.exit(0 if not FAILS else 1)


def run(fin, copy, control, scratch):
    dbp, sp1p, sp2p = os.path.join(scratch, "fin.db"), os.path.join(scratch, "spine1.db"), os.path.join(scratch, "spine2.db")
    con = schema_from(copy, dbp)
    make_spine(fin, sp1p, False)
    make_spine(fin, sp2p, True)
    os.environ.update(FINANCE_DB=dbp, SPINE_DB=sp1p, ASSETS_DB=os.path.join(scratch, "assets.db"), PYTHONDONTWRITEBYTECODE="1")
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [x for x in sys.path if os.path.abspath(x or ".") != here]
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    assert SW.__file__.startswith(fin) and SF.__file__.startswith(fin), (SW.__file__, SF.__file__)
    say("-- S934 synth on the %s files: %s (stock_watch KIT %s) -- count day %s" % ("OLD (control)" if control else "new", fin, SW.KIT, D))
    SW.ensure(con)
    con.execute("INSERT INTO mi_bill_chain (series, day, first_no, last_no, n_bills, gap_before, gap_inside, empty, source_md5, computed_at) VALUES ('A',?,4980,5000,21,'','',0,'walk',?)",
                (Y, Y + "T08:00:00"))
    # SHELF: Darpan counted 300 on Z at 10:00 (before any sale) -- a counted item
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES (?,?,?,?,?,?,?)",
                (SW.norm_name("W934 SHELF 10"), "W934 SHELF 10", Z + "T10:00:00", 300, "spot", "darpan", "settled"))
    con.commit()
    sp1 = SW.Spine(sp1p)
    check("T0 the made-up spine (before the count day's sales) reads", sp1.ok)
    cols = {r[1] for r in con.execute("PRAGMA table_info(stock_watch_ask)")}
    pcols = {r[1] for r in con.execute("PRAGMA table_info(stock_point)")}
    check("T0b ensure() adds stock_watch_ask.mode / closed_how and stock_point.last_bill / ask_id", {"mode", "closed_how"} <= cols and {"last_bill", "ask_id"} <= pcols, (cols, pcols))

    # ---- the two modes
    r = attempt("T1 ask(mode='now')", lambda: SW.ask(con, "W934 SHELF 10", "manoj", sp=sp1, mode="now"))
    check("T1 ask(..., mode='now') -> ok, 'on Darpan's screen now'", bool(r) and r[0] and "screen now" in r[1], r)
    row = con.execute("SELECT mode, roster_id FROM stock_watch_ask WHERE item='W934 SHELF 10' AND done_at IS NULL").fetchone() if "mode" in cols else None
    check("T2 the ask is stored as mode 'now', not on any roster", bool(row) and row[0] == "now" and row[1] is None, row)
    r = attempt("T3 ask(mode='next')", lambda: SW.ask(con, "W934 ASK 10", "manoj", sp=sp1, mode="next"))
    check("T3 ask(..., mode='next') -> the head of the next morning list", bool(r) and r[0] and "next morning list" in r[1], r)
    R = attempt("T4 build_roster", lambda: SW.build_roster(con, dt.date.today(), SW.settings(con), sp1, force=True))
    names = [x["item"] for x in (R or {}).get("items", [])]
    check("T4 today's roster (forced) carries the Next-list ask and NOT the Count-now ask", "W934 ASK 10" in names and "W934 SHELF 10" not in names, names)
    nd = dt.date.today() + dt.timedelta(days=2)
    pv = attempt("T5 preview_roster", lambda: [x["item"] for x in SW.preview_roster(con, nd, SW.settings(con), sp1)])
    check("T5 the preview of a later list never carries a Count-now ask", pv is not None and "W934 SHELF 10" not in pv, pv)
    nv = attempt("T6 now_view", lambda: SW.now_view(con, sp1))
    check("T6 now_view(): Darpan's Abhi ginti card lists SHELF with its pack, the last bill known (5000 of the day before)",
          bool(nv) and [x["item"] for x in nv["items"]] == ["W934 SHELF 10"] and nv["items"][0]["pack"] == 10 and nv["last_no"] == 5000, nv)

    # ---- a Next ask moved to Count now; withdraw
    attempt("T7 ask next SWAP", lambda: SW.ask(con, "W934 SWAP 10", "manoj", sp=sp1, mode="next"))
    attempt("T7 roster again", lambda: SW.build_roster(con, dt.date.today(), SW.settings(con), sp1, force=True))
    rid = con.execute("SELECT roster_id FROM stock_watch_ask WHERE item='W934 SWAP 10' AND done_at IS NULL").fetchone()
    r = attempt("T7 ask now SWAP", lambda: SW.ask(con, "W934 SWAP 10", "manoj", sp=sp1, mode="now"))
    left = con.execute("SELECT COUNT(*) FROM stock_spot_roster WHERE item='W934 SWAP 10' AND answered_at IS NULL").fetchone()[0]
    m = con.execute("SELECT mode, roster_id FROM stock_watch_ask WHERE item='W934 SWAP 10' AND done_at IS NULL").fetchone() if "mode" in cols else None
    check("T7 a rostered Next ask asked again as Count now: its unanswered roster row leaves the list, the ask is 'now' with no roster",
          bool(rid and rid[0]) and bool(r) and r[0] and left == 0 and bool(m) and m[0] == "now" and m[1] is None, (rid, r, left, m))
    aid = con.execute("SELECT id, roster_id FROM stock_watch_ask WHERE item='W934 ASK 10' AND done_at IS NULL").fetchone()
    w = attempt("T8 withdraw_ask", lambda: SW.withdraw_ask(con, aid[0], "manoj"))
    gone = con.execute("SELECT COUNT(*) FROM stock_spot_roster WHERE item='W934 ASK 10' AND reason LIKE 'you asked%'").fetchone()[0]   # a system pick of the same item may stay
    st = con.execute("SELECT done_at, closed_how FROM stock_watch_ask WHERE id=?", (aid[0],)).fetchone() if "closed_how" in cols else None
    check("T8 withdraw_ask(): the ask closed as 'withdrawn'; every unanswered roster row of his ask (the forced second build's copy too) is off the list", bool(w) and w[0] and gone == 0 and bool(st) and st[0] and st[1] == "withdrawn", (w, gone, st))
    con.execute("INSERT INTO stock_spot_roster (day, item_norm, item, reason, reason_hi, rank, asked_at, pack, packing, carried) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (D, SW.norm_name("W934 WD 10"), "W934 WD 10", "the shelf figure and Marg moved apart", "", 9, D + "T07:00:00", 10, "1*10", 0))   # a system pick
    con.execute("INSERT INTO stock_spot_roster (day, item_norm, item, reason, reason_hi, rank, asked_at, pack, packing, carried) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (D, SW.norm_name("W934 ROUTE 10"), "W934 ROUTE 10", "you asked for it · carried from 20-11-2026", "", 8, D + "T07:00:00", 10, "1*10", 1))   # a carried copy
    con.execute("INSERT INTO stock_watch_ask (item_norm, item, by, at, roster_id) VALUES (?,?,?,?,?)", (SW.norm_name("W934 ROUTE 10"), "W934 ROUTE 10", "manoj", Y + "T09:00:00", 999999))
    con.commit()
    ra = con.execute("SELECT id FROM stock_watch_ask WHERE item='W934 ROUTE 10' AND done_at IS NULL").fetchone()
    w3 = attempt("T8b withdraw carried", lambda: SW.withdraw_ask(con, ra[0], "manoj"))
    left = con.execute("SELECT COUNT(*) FROM stock_spot_roster WHERE item='W934 ROUTE 10' AND reason LIKE 'you asked%'").fetchone()[0]
    pick = con.execute("SELECT COUNT(*) FROM stock_spot_roster WHERE item='W934 WD 10' AND reason='the shelf figure and Marg moved apart'").fetchone()[0]
    check("T8b an ask whose row was CARRIED onto today's list (its roster_id points elsewhere): withdrawing takes the carried copy off too; a system pick of another item stays",
          bool(w3) and w3[0] and left == 0 and pick == 1, (w3, left, pick))
    con.execute("DELETE FROM stock_spot_roster WHERE item='W934 WD 10' AND reason='the shelf figure and Marg moved apart'")
    con.commit()
    w2 = attempt("T9 withdraw again", lambda: SW.withdraw_ask(con, aid[0], "manoj"))
    check("T9 withdrawing it again says it is no longer open (404)", bool(w2) and not w2[0] and w2[2] == 404, w2)

    # ---- the bill check
    ck = lambda t: attempt("T10-13 _s934_check_bill", lambda: SW._s934_check_bill(con, t))   # noqa: E731
    a, b, c, d = ck("4999"), ck("5301"), ck("A005002"), ck("")
    check("T10 a number BEFORE the last known bill (4999 < 5000) is refused, in Hindi, naming the bill", bool(a) and not a[0] and "5000" in a[2] and "peechhe" in a[2], a)
    check("T11 a number more than 300 past it (5301) is refused as a typo", bool(b) and not b[0] and "aage" in b[2], b)
    check("T12 'A005002' reads as 5002 and is accepted", bool(c) and c[0] and c[1] == 5002, c)
    check("T13 nothing typed -> refused by the check (the caller treats blank as the time rule)", bool(d) and not d[0], d)

    # ---- Count now, to the bill
    sh_ask = con.execute("SELECT id FROM stock_watch_ask WHERE item='W934 SHELF 10' AND done_at IS NULL").fetchone()
    bad = attempt("T14 answer_now refused", lambda: SW.answer_now(con, sh_ask[0], 250, "4990", "darpan", sp=sp1))
    check("T14 answer_now with a bill before yesterday's last is refused and writes nothing", bool(bad) and not bad[0] and bad[2] == 400 and
          con.execute("SELECT COUNT(*) FROM stock_point WHERE item='W934 SHELF 10'").fetchone()[0] == 1, bad)
    ok = attempt("T15 answer_now", lambda: SW.answer_now(con, sh_ask[0], 250, "5002", "darpan", sp=sp1))
    p = con.execute("SELECT id, status, last_bill, expected_units, gap_units, source, ask_id FROM stock_point WHERE item='W934 SHELF 10' ORDER BY id DESC LIMIT 1").fetchone() if "last_bill" in pcols else None
    check("T15 answer_now(250, bill 5002): one point, source 'darpan', status 'awaits_sales', last bill 5002, no figure or gap yet, tied to the ask; the Hindi says it waits for the sale report",
          bool(ok) and ok[0] and "milaan" in ok[1] and bool(p) and p[1] == "awaits_sales" and p[2] == "5002" and p[3] is None and p[4] is None and p[5] == "darpan" and p[6] == sh_ask[0], (ok, p))
    da = con.execute("SELECT done_at, closed_how FROM stock_watch_ask WHERE id=?", (sh_ask[0],)).fetchone() if "closed_how" in cols else None
    check("T16 the ask is closed as 'counted'", bool(da) and da[0] and da[1] == "counted", da)
    mg_ask = attempt("T17 ask MARG/LOSS/TIME now", lambda: [SW.ask(con, n, "manoj", sp=sp1, mode="now") for n in ("W934 MARG 10", "W934 LOSS 10", "W934 TIME 10")])
    ids = {r[1]: r[0] for r in con.execute("SELECT id, item FROM stock_watch_ask WHERE done_at IS NULL")}
    o1 = attempt("T17 MARG", lambda: SW.answer_now(con, ids.get("W934 MARG 10"), 85, "5002", "darpan", sp=sp1))
    o2 = attempt("T17 LOSS", lambda: SW.answer_now(con, ids.get("W934 LOSS 10"), 40, "5001", "darpan", sp=sp1))
    o3 = attempt("T17 TIME", lambda: SW.answer_now(con, ids.get("W934 TIME 10"), 50, "", "darpan", sp=sp1, no_bill=True))
    check("T17b no bill number keyed: Darpan is told the count is placed by its time", bool(o3) and "samay se" in (o3[1] or ""), o3)
    attempt("T17c ask LATE/PUR/TWICE/RET now", lambda: [SW.ask(con, n, "manoj", sp=sp1, mode="now") for n in ("W934 LATE 10", "W934 PUR 10", "W934 TWICE 10", "W934 RET 10")])
    ids = {r[1]: r[0] for r in con.execute("SELECT id, item FROM stock_watch_ask WHERE done_at IS NULL")}
    attempt("T17c LATE", lambda: SW.answer_now(con, ids.get("W934 LATE 10"), 100, "5002", "darpan", sp=sp1))
    attempt("T17c PUR", lambda: SW.answer_now(con, ids.get("W934 PUR 10"), 50, "5002", "darpan", sp=sp1))
    attempt("T17c TWICE", lambda: SW.answer_now(con, ids.get("W934 TWICE 10"), 100, "5002", "darpan", sp=sp1))
    attempt("T17c RET", lambda: SW.answer_now(con, ids.get("W934 RET 10"), 95, "5002", "darpan", sp=sp1))
    later = (dt.datetime.now() + dt.timedelta(minutes=3)).replace(microsecond=0).isoformat()
    con.execute("INSERT INTO purchase_order (id, created_at, created_by, vendor, status, supplier_norm, received_at) VALUES (934,?,?,?,?,?,?)",
                (D + "T09:00:00", "walk", "W934 PHARMA", "received", "W934 PHARMA", later))
    con.execute("INSERT INTO purchase_order_line (id, order_id, item, packs, pack_size, units, supplied, arrived_at, arrived_by) VALUES (9341,934,?,?,?,?,?,?,?)",
                ("W934 LATE 10", 5, 10, 50, 5, later, "reception"))                                          # 5 strips tapped AFTER the count, not in Marg
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES (?,?,?,?,?,?,?)",
                (SW.norm_name("W934 TWICE 10"), "W934 TWICE 10", later, 90, "darpan", "darpan", "settled"))   # a later count of the same item
    con.commit()
    tp = con.execute("SELECT status, last_bill, gap_units FROM stock_point WHERE item='W934 TIME 10'").fetchone()
    check("T17 no bill number -> judged now by its time (not awaiting, no last bill), as any spot count", bool(o3) and o3[0] and bool(tp) and tp[0] != "awaits_sales" and tp[1] is None, (o3, tp))
    n0 = attempt("T18 settle before the sales", lambda: SW._s934_settle(con, sp1))
    still = con.execute("SELECT COUNT(*) FROM stock_point WHERE status='awaits_sales'").fetchone()[0]
    check("T18 before the count day's sale report: nothing judged, the seven still wait", n0 == 0 and still == 7, (n0, still))
    con.execute("INSERT INTO mi_bill_chain (series, day, first_no, last_no, n_bills, gap_before, gap_inside, empty, source_md5, computed_at) VALUES ('A',?,5001,5004,4,'','',0,'walk',?)",
                (D, D + "T23:00:00"))
    con.commit()
    n0b = attempt("T18b settle with the chain in but the spine not", lambda: SW._s934_settle(con, sp1))
    check("T18b Marg's bill chain already holds the day but the spine does not (the morning window): STILL nothing judged (cold review MUST 1)", n0b == 0, n0b)
    line = con.execute("SELECT text FROM stock_watch_notice WHERE kind='count_day' AND once_key=?", ("counted:%s" % D,)).fetchone()
    check("T19 the day's line on his Needs-you says the bill-placed counts are judged when the sale report is in", bool(line) and "judged to the bill" in line[0], line)

    # ---- the sales are in
    sp2 = SW.Spine(sp2p)
    n1 = attempt("T20 settle after the sales", lambda: SW._s934_settle(con, sp2))
    check("T20 with the count day's sales in (the report taken the morning after), the seven are judged", n1 == 7, n1)
    s = con.execute("SELECT status, basis, expected_units, gap_units FROM stock_point WHERE item='W934 SHELF 10' ORDER BY id DESC LIMIT 1").fetchone()
    check("T21 SHELF (counted before): expected = the shelf at the end of the day 300-100 = 200 + the sales after bill 5002 (10+40) = 250; counted 250 -> gap 0, basis shelf",
          bool(s) and s[0] == "settled" and s[1] == "shelf" and s[2] == 250 and s[3] == 0, s)
    s = con.execute("SELECT status, basis, expected_units, gap_units FROM stock_point WHERE item='W934 MARG 10'").fetchone()
    check("T22 MARG (never counted): expected = Marg at the end of the day 100-30 = 70 + the sales after 5002 (20) = 90; counted 85 -> gap -5, basis marg",
          bool(s) and s[0] == "settled" and s[1] == "marg" and s[2] == 90 and s[3] == -5, s)
    ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE item='W934 MARG 10'").fetchone()[0]
    check("T23 MARG's 5 tablets short are inside the allowance: no loss line", ll == 0, ll)
    s = con.execute("SELECT gap_units, id FROM stock_point WHERE item='W934 LOSS 10'").fetchone()
    ll = con.execute("SELECT gap_units, point_id FROM stock_watch_loss_line WHERE item='W934 LOSS 10'").fetchone()
    check("T24 LOSS: expected 100-10 = 90 (no sale after 5001), counted 40 -> gap -50, beyond the allowance: one loss line by name on the point",
          bool(s) and s[0] == -50 and bool(ll) and ll[0] == 50 and ll[1] == s[1], (s, ll))
    s = con.execute("SELECT gap_units, expected_units FROM stock_point WHERE item='W934 LATE 10' AND source='darpan' ORDER BY id LIMIT 1").fetchone()
    ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE item='W934 LATE 10'").fetchone()[0]
    check("T24c LATE: 5 strips tapped AFTER the count are not expected on the shelf he counted: expected 100, gap 0, no loss line (cold review MUST 2)", bool(s) and s[1] == 100 and s[0] == 0 and ll == 0, (s, ll))
    s = con.execute("SELECT gap_units, note FROM stock_point WHERE item='W934 PUR 10'").fetchone()
    ll = con.execute("SELECT COUNT(*) FROM stock_watch_loss_line WHERE item='W934 PUR 10'").fetchone()[0]
    check("T24d PUR: a purchase dated the count day (its hour unknown): the gap is shown (-80) and noted, never a loss line", bool(s) and s[0] == -80 and "purchase is dated that day" in (s[1] or "") and ll == 0, (s, ll))
    s = con.execute("SELECT status, gap_units, note FROM stock_point WHERE item='W934 TWICE 10' AND source='darpan' AND last_bill IS NOT NULL").fetchone()
    check("T24e TWICE: a later count of the item already stands: the bill-placed count is closed unjudged, said in its note (SHOULD 3)", bool(s) and s[0] == "settled" and s[1] is None and "later count" in (s[2] or ""), s)
    s = con.execute("SELECT expected_units, gap_units FROM stock_point WHERE item='W934 RET 10'").fetchone()
    check("T24f RET: a patient's return that day is taken as before the count: expected (100-20+5) + 10 after = 95, counted 95 -> gap 0", bool(s) and s[0] == 95 and s[1] == 0, s)
    n2 = attempt("T24b settle again", lambda: SW._s934_settle(con, sp2))
    check("T24b settling again judges nothing twice", n2 == 0, n2)

    # ---- the carry forward
    ctx = SF.Ctx(con, sp2)
    sh = attempt("T25 shelf", lambda: SF.shelf(con, sp2, "W934 SHELF 10", None, ctx))
    check("T25 carried forward from the bill-placed count: 250 - the day's sales billed AFTER 5002 (50) = 200 -- the sales up to 5002 not taken off again (bill_cut 50)",
          bool(sh) and sh.get("shelf") == 200 and sh.get("bill_cut") == 50 and sh.get("base") == 250, sh)
    rt = attempt("T25b shelf RET", lambda: SF.shelf(con, sp2, "W934 RET 10", None, ctx))
    check("T25b RET carried forward: 95 - the sale after 5002 (10) + no return again = 85 = Marg at the end of the day (100-20+5)", bool(rt) and rt.get("shelf") == 85, rt)
    mg = attempt("T26 marg", lambda: SF.marg(con, sp2, "W934 SHELF 10", None, ctx))
    check("T26 ... and Marg at the end of the day reads 200: the shelf and Marg agree (the old rule would read 150, a false 50 short)", bool(mg) and mg.get("figure") == 200, mg and mg.get("figure"))

    # ---- the routes
    import flask                                              # noqa: E402
    import stock_check as SC                                  # noqa: E402
    import stockmatch as SM                                   # noqa: E402
    app = flask.Flask("s934walk")
    SC._db = lambda: con
    SC._require = lambda *a, **k: (dict(user="manoj", roles=["checker"]), None)
    SM._db = lambda: con
    SM._require = lambda *a, **k: (dict(user="darpan", roles=["maker"]), None)
    app.register_blueprint(SC.bp)
    app.register_blueprint(SM.bp)
    cl = app.test_client()
    os.environ["SPINE_DB"] = sp2p
    SW.SPINE_DB = sp2p
    rv = cl.post("/finance/stockcheck/api/count", json=dict(item="W934 ROUTE 10", mode="now"))
    j = rv.get_json(silent=True) or {}
    rr = con.execute("SELECT id, mode FROM stock_watch_ask WHERE item='W934 ROUTE 10' AND done_at IS NULL").fetchone() if "mode" in cols else None
    check("T27 POST /finance/stockcheck/api/count {mode: now} -> 200, the ask is 'now'", rv.status_code == 200 and j.get("ok") and bool(rr) and rr[1] == "now", (rv.status_code, j, rr))
    kk = attempt("T27b ask() with no mode", lambda: SW.ask(con, "W934 ROUTE 10", "manoj", sp=sp2))
    rr2 = con.execute("SELECT mode FROM stock_watch_ask WHERE item='W934 ROUTE 10' AND done_at IS NULL").fetchone() if "mode" in cols else None
    check("T27b an older caller's ask() with no mode (the Loss desk's Count this) never moves an open Count now (SHOULD 6)", bool(kk) and kk[0] and "already" in kk[1] and bool(rr2) and rr2[0] == "now", (kk, rr2))
    rv = cl.post("/finance/stockcheck/api/count", json=dict(item="W934 WD 10"))
    wd = con.execute("SELECT id, mode FROM stock_watch_ask WHERE item='W934 WD 10' AND done_at IS NULL").fetchone() if "mode" in cols else None
    check("T28 POST .../api/count with no mode -> Next list (the old call still works)", rv.status_code == 200 and bool(wd) and wd[1] == "next", (rv.status_code, wd))
    rv = cl.post("/finance/stockcheck/api/withdraw", json=dict(ask_id=(wd[0] if wd else 0)))
    j = rv.get_json(silent=True) or {}
    check("T29 POST /finance/stockcheck/api/withdraw -> 200, withdrawn", rv.status_code == 200 and j.get("ok") and "withdrawn" in (j.get("message") or ""), (rv.status_code, j))
    dv = attempt("T30 darpan_view", lambda: SW.darpan_view(con))
    check("T30 darpan_view() carries the Abhi ginti card with ROUTE and SWAP", bool(dv) and dv.get("ok") and sorted(x["item"] for x in (dv.get("now") or {}).get("items", [])) == ["W934 ROUTE 10", "W934 SWAP 10"], dv and dv.get("now"))
    rv = cl.post("/finance/stockmatch/api/now", json=dict(ask_id=(rr[0] if rr else 0), strips=5, loose=3, last_bill="5004"))
    j = rv.get_json(silent=True) or {}
    rp = con.execute("SELECT qty_units, last_bill, status FROM stock_point WHERE item='W934 ROUTE 10'").fetchone() if "last_bill" in pcols else None
    check("T31 POST /finance/stockmatch/api/now {5 strips 3 tabs, bill 5004} -> 200; the point 53 tabs to bill 5004 (the day's report is in: judged at its next settle)",
          rv.status_code == 200 and j.get("ok") and bool(rp) and rp[0] == 53 and rp[1] == "5004", (rv.status_code, str(j)[:200], rp))
    rv = cl.post("/finance/stockmatch/api/now", json=dict(ask_id=(rr[0] if rr else 0), strips=5, loose=3, last_bill="5004"))
    check("T32 the same Count now answered twice -> 404 'ab khuli nahi'", rv.status_code == 404, rv.status_code)
    html1 = open(os.path.join(fin, "stock_check.html"), encoding="utf-8").read()
    html2 = open(os.path.join(fin, "stockmatch.html"), encoding="utf-8").read()
    check("T32b the pages: his Count offers 'Count now' and 'Next list' and a two-tap Withdraw; Darpan's card 'Abhi ginti' asks the last bill number and posts /api/now; no confirm() dialog",
          "'Count now'" in html1 and "'Next list'" in html1 and "Sure? Withdraw" in html1 and "/api/withdraw" in html1 and "Abhi ginti" in html2 and "Aakhri sale bill no." in html2 and "/finance/stockmatch/api/now" in html2
          and "confirm(" not in html1 and "confirm(" not in html2)
    line = con.execute("SELECT text FROM stock_watch_notice WHERE kind='count_day' AND once_key=?", ("counted:%s" % D,)).fetchone()
    check("T33 the day's line after the judgment names SHELF 'matches the records' and LOSS 'below the records'", bool(line) and "W934 SHELF 10 matches the records" in line[0] and "W934 LOSS 10 5 strips below the records" in line[0], line)


if __name__ == "__main__":
    main()
