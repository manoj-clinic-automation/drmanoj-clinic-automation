#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s432_s436.py -- S432's own walk re-run by kit S436_STAFF_PAGES_CLEAN with ONE named DATA adjustment: the negative control's
"the old box has no stock_pile_cache table" read a copy of the live database, which has carried that table since S432's install (28-Sep
07:52); the control now asserts what the old FILES lack -- loss_piles without cached() -- and that the old app's read never wrote a cache
row (the table's row count on its scratch copy stays what the copy had). Nothing else differs from deploy_kits/S432_DESK_GROUP_FLOW/walk_s432.py:
walk_s432.py -- kit S432_DESK_GROUP_FLOW (F-651). THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over
SCRATCH copies of the live finance.db and the spine, driven through Flask's test client with header identity (walk only).

  * count #1 is the REAL count (closed by the owner 27-Sep 12:58): two crafted open lines W432* on it time the read and a move
    against the brief's targets (the piles JSON under 1 s, a move under 0.5 s) and prove the cache's stamps; its frozen run is
    untouched (md5 equal before / after); the sales-after-count test runs in the first build, not on a plain read.
  * count W432 (#2, ~150 lines copied from count #1's sheet with fresh figures, Marg as on 20-09-2026) carries the GROUP FLOW:
    Tick all, an untick's pile menu writes nothing, a move re-piles and leaves the list, Clear writes off exactly the ticked lines
    with one run and the vouchers, the unticked stay open, Clear with nothing ticked refused, the 10-s arm, the LAST clear closes the
    count by itself (one staff block, the S428 points once, the leakage period line); Close the count still works as one tap.
  * the traces and the watch are never run by a read (counters prove it), run by Refresh watch and by the job.
  * 3.4: the statement's Marg-negative lines (the real PRIME CAST 4"/5", BELL CAST 5, ALCOXIB 120 ...); BELL CAST 5 in Consumables
    after the seed; qty_words carries the sign.
  * bhati / darpan / shavez refused. Then the SAME scenario on the box as it is (--old): it must go red.

  --app NEW --old OLD --db PATH --spine PATH
"""
import argparse
import datetime as dt
import json
import os
import random
import re
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--app", required=True)
ap.add_argument("--old", required=True)
ap.add_argument("--db", required=True)
ap.add_argument("--spine", required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
assert "walk" in a.spine or "scratch" in a.spine or a.spine.startswith("/tmp"), "refusing a non-scratch spine"
n, fails = 0, []


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:400] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


TODAY = dt.date.today()
D = lambda k: (TODAY + dt.timedelta(days=k)).isoformat()   # noqa: E731
AS2 = "20-09-2026"                                          # count W432's Marg day (dd-mm-yyyy, as stock_count keeps it); after count #1 (06-09), before today
# count #1: item, packing, pack, marg, counted, MRP per tab/pc (paise), spine sales [(date, units)] -- open lines on the closed count
CRAFT1 = (
    ("W432 LATE TAB", "1*10", 10, 40, 20, 1500, [(D(-100), 300), (D(-60), 300)]),          # 2 strips short, Rs 300 -> small; the move is timed on it
    ("W432 LATE2 PC", "1*1", 1, 6, 4, 20000, [(D(-80), 12)]),                              # 2 pcs short, Rs 400 -> small; stays for the one-tap close
    ("W432 SOLD TAB", "1*10", 10, 50, 5, 1000, [(D(-120), 200), ("2026-09-10", 200)]),     # counted 5, 20 strips sold after 06-09: the sales test closes it in the first build
)


def craft(db):
    c = sqlite3.connect(db, timeout=30)
    as_on1 = c.execute("SELECT marg_as_on FROM stock_count WHERE id=1").fetchone()[0]
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    for it, packing, ps, marg, cnt, mrp, _s in CRAFT1:
        c.execute("INSERT OR REPLACE INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,'walk W432')", (as_on1, it, marg, packing, ps, now))
        c.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, strips, loose, counted_by, entered_by, at) VALUES (1,?,?,?,?,?,0,0,'W432','W432',?)",
                  (it, packing, ps, marg, cnt, now))
        c.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, pack_size, value_p, cause, status, counted_by) VALUES (1,?,?,?,?,?,?,NULL,'UNEXPLAINED','open','W432')",
                  (it, as_on1, marg, cnt, cnt - marg, ps))
        c.execute("INSERT OR REPLACE INTO stock_mrp_manual (item, mrp_p, source, set_by, set_at) VALUES (?,?,'walk W432','W432',?)", (it, mrp, now))
    # count W432 (#2): ~150 lines of count #1's sheet with fresh figures; the snapshot of 20-09 copied from 06-09 so packs resolve
    c.execute("INSERT OR IGNORE INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) SELECT ?, item, qty, packing, pack_size, ?, 'walk W432' FROM stock_snapshot WHERE as_on=?", (AS2, now, as_on1))
    c.execute("INSERT INTO stock_count (unit, marg_as_on, bill_no, bill_date, started_at, submitted_at, submitted_by, items_total, items_counted, status, section) VALUES ('medical',?,?,?,?,?,?,?,?,'submitted',NULL)",
              (AS2, "W432-1", "2026-09-20", "2026-09-20T09:00:00", "2026-09-20T13:00:00", "darpan", 150, 150))
    cid = c.execute("SELECT MAX(id) FROM stock_count").fetchone()[0]
    items = [r for r in c.execute("SELECT item, packing, pack_size, marg_qty FROM stock_count_item WHERE count_id=1 AND item NOT LIKE 'W432%' ORDER BY id").fetchall()]
    want = {"BLADE", "GLOVES SURGICAL 7", "TYRO BR", "ROSIKA FORTE", "GLOCREPE", "CORTIRI"}
    pick = [r for r in items if r[0] in want] + [r for r in items if r[0] not in want][:150 - len(want)]
    random.seed(432)
    for i, (it, packing, ps, marg) in enumerate(pick):
        marg2 = max(0, int(marg))
        if it in want:
            cnt = max(0, marg2 - (2 if ps == 1 else 4))
            if it in ("TYRO BR", "ROSIKA FORTE"):
                cnt = max(0, marg2 - 5)                        # a fast seller 5 tabs short: within the allowance (the floor is one strip)
        elif i % 3 == 0:
            cnt = max(0, marg2 - random.choice([1, 2, 3, 5, 10, 20]))
        elif i % 7 == 0:
            cnt = marg2 + 2
        else:
            cnt = marg2
        c.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, strips, loose, counted_by, entered_by, at) VALUES (?,?,?,?,?,?,0,0,'darpan','darpan',?)", (cid, it, packing, ps, marg2, cnt, now))
        if cnt != marg2:
            c.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, pack_size, value_p, cause, status, counted_by) VALUES (?,?,?,?,?,?,?,NULL,'UNEXPLAINED','open','darpan')", (cid, it, AS2, marg2, cnt, cnt - marg2, ps))
    # one crafted BIG loss on count W432 (Rs 5,000 short, a fast seller) and one owner's-use candidate
    for it, packing, ps, marg, cnt, mrp in (("W432 BIG TAB", "1*10", 10, 200, 100, 5000), ("W432 HOME TAB", "1*10", 10, 30, 20, 800)):
        c.execute("INSERT OR REPLACE INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,'walk W432')", (AS2, it, marg, packing, ps, now))
        c.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, strips, loose, counted_by, entered_by, at) VALUES (?,?,?,?,?,?,0,0,'darpan','darpan',?)", (cid, it, packing, ps, marg, cnt, now))
        c.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, pack_size, value_p, cause, status, counted_by) VALUES (?,?,?,?,?,?,?,NULL,'UNEXPLAINED','open','darpan')", (cid, it, AS2, marg, cnt, cnt - marg, ps))
        c.execute("INSERT OR REPLACE INTO stock_mrp_manual (item, mrp_p, source, set_by, set_at) VALUES (?,?,'walk W432','W432',?)", (it, mrp, now))
    c.execute("UPDATE stock_snapshot SET qty=(SELECT marg_qty FROM stock_count_item WHERE count_id=? AND item=stock_snapshot.item) WHERE as_on=? AND item IN (SELECT item FROM stock_count_item WHERE count_id=?)", (cid, AS2, cid))
    c.commit()
    c.close()
    return cid


def craft_spine(db):
    c = sqlite3.connect(db, timeout=30)
    latest = c.execute("SELECT MAX(as_on) FROM sp_close").fetchone()[0]
    rows = list(CRAFT1) + [("W432 BIG TAB", "1*10", 10, 200, 100, 5000, [(D(-100), 2000), (D(-40), 2000)]), ("W432 HOME TAB", "1*10", 10, 30, 20, 800, [(D(-50), 100)])]
    for i, (it, packing, ps, marg, cnt, mrp, sales) in enumerate(rows, 1):
        k = it[:20].strip()
        c.execute("INSERT OR REPLACE INTO sp_item (k20, name, packing, unit_kind, first_seen, last_seen) VALUES (?,?,?,?,?,?)", (k, it, packing, "LOOSE" if ps > 1 else "WHOLE", "2026-03-31", latest))
        for j, (day, units) in enumerate(sales, 1):
            c.execute("INSERT OR REPLACE INTO sp_sale_line (date, bill, seq, name20, k20, pack, qty_raw, units, rate_p, batch, expiry) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (day, "W432-%02d-%s" % (i, day.replace("-", "")), j, k, k, packing, "%d:%d" % divmod(units, ps) if ps > 1 else str(units), float(units), int(mrp * ps), "W432", "12/28"))
        c.execute("INSERT OR REPLACE INTO sp_close (as_on, k20, units, source_md5) VALUES (?,?,?,?)", (latest, k, float(marg), "W432"))
    c.commit()
    c.close()


DB_OLD = a.db + ".old"
copydb(a.db, DB_OLD)
CID = craft(a.db)
CID_OLD = craft(DB_OLD)
craft_spine(a.spine)


def _cache_rows(p):                                           # S436 adjustment: the cache table's rows on the old copy before the old app reads it
    c = sqlite3.connect(p)
    r = c.execute("SELECT COUNT(*) FROM stock_pile_cache").fetchone()[0] if c.execute("SELECT name FROM sqlite_master WHERE name='stock_pile_cache'").fetchone() else None
    c.close()
    return r


CACHE_ROWS_OLD0 = _cache_rows(DB_OLD)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s432  # noqa: E402
assert seed_s432.seed(a.db, a.app) == 0, "seed failed"
print("-- scratch: crafted W432 rows on count #1 and the crafted count W432 (#%d, ~150 lines) on both copies, the spine; the S432 seed ran on the new copy (BELL CAST 5, the tables, the warm-up)" % CID)

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re, time, zipfile, io
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
CID = int(os.environ["CID"])
import finance_app as fa
import stock_app
try:
    import loss_piles as LP
    import stock_watch as SW
except Exception:
    LP = SW = None
import qty_words as QW
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(), r.headers.get("Content-Type", "")]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
R = []
def C(label, cond, got=None):
    R.append([label, bool(cond), (json.dumps(got, default=str)[:400] if got is not None else None)])
def step(name, fn):
    try:
        fn()
    except Exception as e:
        import traceback
        C(name + " -- the step ran", False, "%s: %s | %s" % (type(e).__name__, str(e)[:200], traceback.format_exc()[-400:]))
WORD = re.compile(r"\b(units?|yunit)\b", re.I)
def strings(o, acc):
    if isinstance(o, dict):
        for v in o.values(): strings(v, acc)
    elif isinstance(o, list):
        for v in o: strings(v, acc)
    elif isinstance(o, str):
        acc.append(o)
def hits(texts):
    return [t[max(0, WORD.search(t).start() - 30):WORD.search(t).start() + 40] for t in texts if WORD.search(t)]
# COUNTERS: what a read must NOT run any more (the report composer, the sales test, the traces, the watch scoring)
CNT = {"report": 0, "sales_test": 0, "trace": 0, "owner_view": 0}
_orig_report = stock_app._pad_report_data
def _report(con, root):
    CNT["report"] += 1; return _orig_report(con, root)
stock_app._pad_report_data = _report
if LP:
    _orig_st = LP.sales_test
    def _st(*a_, **k_):
        CNT["sales_test"] += 1; return _orig_st(*a_, **k_)
    LP.sales_test = _st
if SW:
    _orig_tr, _orig_ov = SW.trace_big_losses, SW.owner_view
    def _tr(*a_, **k_):
        CNT["trace"] += 1; return _orig_tr(*a_, **k_)
    def _ov(*a_, **k_):
        CNT["owner_view"] += 1; return _orig_ov(*a_, **k_)
    SW.trace_big_losses = _tr; SW.owner_view = _ov
def snap():
    return dict(CNT)
def delta(a_, b_):
    return {k: b_[k] - a_[k] for k in a_}
def timed(fn):
    t = time.time(); r = fn(); return r, int((time.time() - t) * 1000)
def piles(cid=1, extra=""):
    r = G("manoj", "/finance/stock/api/loss/%d/piles%s" % (cid, extra)); return r[1] if r[0] == 200 and isinstance(r[1], dict) else None
def where(Dd):
    out = {}
    for p in Dd["piles"]:
        for l in p["lines"]:
            out[l["item"]] = (p["key"], l.get("group"), l)
    for k in ("back", "written_off"):
        for l in (Dd.get("done") or {}).get(k, []):
            out[l["item"]] = (k, l.get("group"), l)
    for l in Dd.get("over") or []:
        out[l["item"]] = ("over", None, l)
    return out
def W(cid):
    return {r["item"]: r for r in q("SELECT item, action, note, by_user, at FROM stock_diff_lane WHERE count_id=? AND id IN (SELECT MAX(id) FROM stock_diff_lane WHERE count_id=? GROUP BY item)", cid, cid)}
S = {}
TIMES = {}

# ---------------------------------------------------------------- 1 FAST: count #1 -- the first read builds the cache (the report once, the sales test once); a plain read runs none of it
def s1():
    run0 = q("SELECT id, md5, groups, lines_n FROM stock_writeoff_run WHERE count_id=1 ORDER BY id LIMIT 1")
    S["run0"] = run0[0] if run0 else None
    c0 = snap(); D0, ms0 = timed(lambda: piles(1)); c1 = snap(); d0 = delta(c0, c1)
    TIMES["first"] = ms0
    C("count #1: the FIRST read builds the cache -- the report composed (%d), the sales test once (%d), no trace (%d), no watch scoring by the read itself; %d ms" % (d0["report"], d0["sales_test"], d0["trace"], ms0),
      bool(D0) and D0.get("cache", {}).get("built") == "full" and 1 <= d0["report"] <= 2 and d0["sales_test"] == 1 and d0["trace"] == 0, [d0, D0 and D0.get("cache")])
    wh = where(D0)
    C("the sales-after-count test ran in that build: W432 SOLD TAB (counted 5, 20 strips sold after 06-09) is closed by the system, listed under 'sold after the count'",
      wh.get("W432 SOLD TAB", (None,))[0] == "back" and any(l["item"] == "W432 SOLD TAB" for l in D0["sold_after"]) and q("SELECT COUNT(*) AS n FROM stock_sales_test WHERE item='W432 SOLD TAB'")[0]["n"] == 1, wh.get("W432 SOLD TAB", (None,))[:2])
    C("the crafted open lines sit in the piles: W432 LATE TAB and W432 LATE2 PC -> Write off, small real gap", wh.get("W432 LATE TAB", (None,))[:2] == ("writeoff", "small") and wh.get("W432 LATE2 PC", (None,))[:2] == ("writeoff", "small"), [wh.get("W432 LATE TAB", (None,))[:2], wh.get("W432 LATE2 PC", (None,))[:2]])
    C("the stored watch card came with it (built once on the first read), with its time; the piles are still the four of S427", (D0.get("watch") or {}).get("stored") and (D0["watch"].get("stored_text") or "").endswith("IST") and [p["key"] for p in D0["piles"]] == ["with_me", "writeoff", "bigloss", "consume"], D0.get("watch", {}).get("stored_text"))
    c2 = snap(); D1, ms1 = timed(lambda: piles(1)); c3 = snap(); d1 = delta(c2, c3)
    TIMES["second"] = ms1
    C("the SECOND read is served from the cache: no report, no sales test, no trace, no watch scoring -- %d ms (target under 1,000)" % ms1,
      D1.get("cache", {}).get("built") == "cache" and d1 == {"report": 0, "sales_test": 0, "trace": 0, "owner_view": 0} and ms1 < 1000, [d1, ms1])
    m0 = q("SELECT stamp, built_at FROM stock_pile_cache_meta WHERE count_id=1")[0]
    C("the stamp is stored and unchanged between the two reads; the cached rows carry every desk line (count_id, item, diff_id)", json.loads(m0["stamp"])["v"] == LP.STAMP_VERSION and q("SELECT COUNT(*) AS n FROM stock_pile_cache WHERE count_id=1")[0]["n"] == len(where(D1)) and all(r["diff_id"] for r in q("SELECT diff_id FROM stock_pile_cache WHERE count_id=1 AND item LIKE 'W432%'")), [q("SELECT COUNT(*) AS n FROM stock_pile_cache WHERE count_id=1")[0]["n"], len(where(D1))])
    C("the two reads give the same lines and totals", json.dumps(D0["totals"], sort_keys=True) == json.dumps(D1["totals"], sort_keys=True) and {k: v[:2] for k, v in where(D0).items()} == {k: v[:2] for k, v in where(D1).items()})
    Dl, msl = timed(lambda: piles(1, "?lite=1")); TIMES["lite"] = msl
    C("the light read (?lite=1): the totals, the piles' headers with their counts, the close and the block -- no lines; %d ms" % msl, Dl and Dl.get("lite") and all(p["lines"] == [] for p in Dl["piles"]) and Dl["piles"][1]["lines_n"] == len(D1["piles"][1]["lines"]) and Dl["totals"] == D1["totals"] and "close" in Dl and Dl["done"]["written_off"] == [], [msl, Dl and [p["lines_n"] for p in Dl["piles"]]])
    Dp = piles(1, "?pile=writeoff")
    C("one pile's lines (?pile=writeoff): that pile carries its lines, the others none", Dp and Dp["piles"][1]["lines"] and all(p["lines"] == [] for p in Dp["piles"] if p["key"] != "writeoff"))
step("fast", s1)

# ---------------------------------------------------------------- 2 the stamps: a move recomputes ONE line; a setting recomputes all; a spine rebuild recomputes all
def s2():
    c0 = snap(); r, ms = timed(lambda: P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W432 LATE TAB", "pile": "bigloss"})); d = delta(c0, snap())
    TIMES["move"] = ms
    pt = (r[1] or {}).get("patch") or {}
    C("a move (W432 LATE TAB -> Big losses) answers in %d ms (target under 500) with the PATCH: that line (bucket bigloss, group big), the totals, the close" % ms,
      r[0] == 200 and ms < 500 and (pt.get("lines") or {}).get("W432 LATE TAB", {}).get("bucket") == "bigloss" and pt["lines"]["W432 LATE TAB"]["group"] == "big" and pt.get("totals") and pt.get("close") and d["report"] == 0 and d["sales_test"] == 0, [ms, d, list((pt.get("lines") or {}).keys())])
    c0 = snap(); Dd, ms2 = timed(lambda: piles(1)); d2 = delta(c0, snap())
    C("the read after the move is a plain read again (the tap brought the stamp up to date): %d ms, no report" % ms2, Dd["cache"]["built"] == "cache" and d2["report"] == 0 and where(Dd)["W432 LATE TAB"][:2] == ("bigloss", "big"), [Dd["cache"]["built"], d2])
    m = q("SELECT last_partial_n FROM stock_pile_cache_meta WHERE count_id=1")[0]
    C("the move recomputed ONE line (the cache's last partial refresh: 1)", m["last_partial_n"] == 1, m)
    # a write the cache did not see (a move written straight to the table): the next read recomputes that line only
    db.execute("INSERT INTO stock_pile_move (count_id, item, pile, by_user, at) VALUES (1,'W432 LATE2 PC','with_me','walk',?)", (dt.datetime.now().replace(microsecond=0).isoformat(),)); db.commit()
    c0 = snap(); Dd = piles(1); d3 = delta(c0, snap())
    C("a stale stamp on the moves part recomputes only the touched line (W432 LATE2 PC -> With me), no report", Dd["cache"]["built"] == "partial" and Dd["cache"]["partial_n"] == 1 and "W432 LATE2 PC" in Dd["cache"]["partial_items"] and where(Dd)["W432 LATE2 PC"][0] == "with_me" and d3["report"] == 0, Dd["cache"])
    db.execute("INSERT INTO stock_pile_move (count_id, item, pile, by_user, at) VALUES (1,'W432 LATE2 PC','auto','walk',?)", (dt.datetime.now().replace(microsecond=0).isoformat(),)); db.commit()
    piles(1)
    c0 = snap(); r = P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.allowance_pct", "value": "2"}); Dd, ms3 = timed(lambda: piles(1)); d4 = delta(c0, snap())
    C("a setting change recomputes EVERYTHING once (the report composed once, no second sales test hit): built=full", r[0] == 200 and Dd["cache"]["built"] == "full" and d4["report"] >= 1 and q("SELECT COUNT(*) AS n FROM stock_sales_test WHERE item='W432 SOLD TAB'")[0]["n"] == 1, [Dd["cache"].get("built"), d4])
    P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.allowance_pct", "value": "1.0"}); piles(1)
    sp = os.environ["SPINE_DB"]; st = os.stat(sp); os.utime(sp, (st.st_atime + 5, st.st_mtime + 5))
    c0 = snap(); Dd = piles(1); d5 = delta(c0, snap())
    C("a spine rebuild (its file's stamp changed) recomputes everything and re-runs the sales test once", Dd["cache"]["built"] == "full" and d5["sales_test"] == 1 and d5["report"] >= 1, [Dd["cache"].get("built"), d5])
    c0 = snap(); Dd, ms4 = timed(lambda: piles(1)); d6 = delta(c0, snap())
    C("and the read after that is a plain read: %d ms" % ms4, Dd["cache"]["built"] == "cache" and d6["report"] == 0 and ms4 < 1000, [ms4, d6])
    C("the hub's status card reads THE SAME totals as the desk (classify on the report = the cache)", {k: v for k, v in (G("manoj", "/finance/stock/api/pad/hub/1")[1].get("desk") or {}).items() if k != "ok"} == Dd["totals"])
step("stamps", s2)

# ---------------------------------------------------------------- 3 the traces and the watch leave the read path: Refresh watch, the job
def s3():
    c0 = snap(); piles(1); piles(1); d = delta(c0, snap())
    C("two reads open no trace and score no watch (counters 0 / 0)", d["trace"] == 0 and d["owner_view"] == 0, d)
    tr0 = q("SELECT COUNT(*) AS n FROM stock_trace WHERE item='W432 LATE TAB' AND trigger='big_loss'")[0]["n"]
    c0 = snap(); r, ms = timed(lambda: P("manoj", "/finance/stock/api/watch/refresh", {"count_id": 1})); d = delta(c0, snap())
    V = (r[1] or {}).get("watch") or {}
    C("Refresh watch: the traces on the cached Big-loss lines (W432 LATE TAB gets one) and the watch scored once, stored with its time (%d ms)" % ms,
      r[0] == 200 and d["trace"] == 1 and d["owner_view"] == 1 and V.get("stored") and V.get("refreshed_by") == "manoj" and q("SELECT COUNT(*) AS n FROM stock_trace WHERE item='W432 LATE TAB' AND trigger='big_loss'")[0]["n"] == tr0 + 1
      and q("SELECT made_by FROM stock_watch_view WHERE key='owner'")[0]["made_by"] == "manoj", [r[0], d, V.get("stored_text")])
    Dd = piles(1)
    C("the desk's watch card is the stored one, refreshed by manoj, and the refresh is audited", (Dd.get("watch") or {}).get("refreshed_by") == "manoj" and q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_watch' AND action='watch_refresh'")[0]["n"] >= 1)
    r = P("manoj", "/finance/stock/api/watch/refresh", {"count_id": 1})
    C("a second refresh opens no second trace on the same line (once per item per 30 days)", r[0] == 200 and q("SELECT COUNT(*) AS n FROM stock_trace WHERE item='W432 LATE TAB' AND trigger='big_loss'")[0]["n"] == tr0 + 1)
    # the 06:30 job stores the watch too (the real job function over this scratch database)
    db.execute("DELETE FROM stock_watch_view"); db.commit()
    import io as _io, contextlib
    buf = _io.StringIO()
    with contextlib.redirect_stdout(buf):
        SW.job(os.environ["FINANCE_DB"], who="cron")
    out = buf.getvalue()
    C("the job (cron) stores the watch: 'watch stored for count #' in its line, the row made by cron", "watch stored for count #" in out and q("SELECT made_by FROM stock_watch_view WHERE key='owner'")[0]["made_by"] == "cron", out[-200:])
step("watch", s3)

# ---------------------------------------------------------------- 4 THE GROUP FLOW on count W432: tick all, the untick menu, a move, Clear this group, the unticked stay
def s4():
    Dl = piles(CID, "?lite=1"); Dd = piles(CID)
    grp = {g["key"]: g["open_n"] for g in Dd["groups"]}
    S["grp0"] = grp
    C("count W432 (#%d): the light read gives the groups with their open counts, the full read the lines; allowance / small / old / big / consume all present" % CID,
      Dl and Dl["groups"] and all(grp.get(k, 0) > 0 for k in ("allowance", "small", "old", "big", "consume")), grp)
    wh = where(Dd)
    C("W432 BIG TAB is a Big loss; BLADE is consumption; GLOCREPE is old stock; TYRO BR within the allowance", wh["W432 BIG TAB"][:2] == ("bigloss", "big") and wh["BLADE"][:2] == ("consume", "consume") and wh["GLOCREPE"][:2] == ("writeoff", "old") and wh["TYRO BR"][:2] == ("writeoff", "allowance"), {k: wh[k][:2] for k in ("W432 BIG TAB", "BLADE", "GLOCREPE", "TYRO BR")})
    allow = sorted(i for i, v in wh.items() if v[:2] == ("writeoff", "allowance"))
    S["allow"] = allow
    C("Clear with nothing ticked is refused (400); an unknown group refused; a line of another group refused (409)",
      P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"group": "allowance", "items": []})[0] == 400 and P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"group": "recount", "items": allow[:1]})[0] == 400
      and P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"group": "allowance", "items": ["W432 BIG TAB"]})[0] == 409)
    # the untick menu: unticking writes nothing (it is local); choosing a pile writes the move (audited owner) and the line leaves the group
    w0, m0 = len(W(CID)), q("SELECT COUNT(*) AS n FROM stock_pile_move WHERE count_id=?", CID)[0]["n"]
    keep = allow[0]
    r = P("manoj", "/finance/stock/api/loss/%d/pile/move" % CID, {"item": keep, "pile": "bigloss"})
    pt = r[1]["patch"]
    C("the untick menu's choice writes the move (audited 'manoj'), the line leaves the allowance list for Big losses; the patch says so; no word written",
      r[0] == 200 and pt["lines"][keep]["bucket"] == "bigloss" and pt["groups_n"]["allowance"] == grp["allowance"] - 1 and len(W(CID)) == w0 and q("SELECT by_user FROM stock_pile_move WHERE count_id=? ORDER BY id DESC LIMIT 1", CID)[0]["by_user"] == "manoj", [keep, pt["groups_n"]])
    C("the page's group list: ticks are local -- nothing in the database changes on a tick or an untick (no door exists for it)", q("SELECT COUNT(*) AS n FROM stock_pile_move WHERE count_id=?", CID)[0]["n"] == m0 + 1)
    # Tick all on 'allowance', untick ONE more (it stays open), Clear this group (N ticked): the 10-s arm and confirm
    ticked = [i for i in allow if i != keep]
    left_out = ticked.pop()
    r = P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"group": "allowance", "items": ticked}); tok = (r[1] or {}).get("arm", {}).get("token")
    C("Clear this group (%d ticked) arms: n = the ticked lines, a 10-second confirm, the group in the arm" % len(ticked), r[0] == 200 and r[1]["arm"]["n"] == len(ticked) and r[1]["arm"]["seconds"] == 10 and r[1]["arm"]["group"] == "allowance", r[1] and r[1].get("arm"))
    db.execute("UPDATE stock_pile_arm SET at=? WHERE token=?", ((dt.datetime.now() - dt.timedelta(seconds=11)).replace(microsecond=0).isoformat(), tok)); db.commit()
    w1 = W(CID)
    r = P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"token": tok})
    C("the 10-second gate: a confirm after 11 s is refused and writes nothing", r[0] == 409 and W(CID) == w1, r)
    r = P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"group": "allowance", "items": ticked}); tok = r[1]["arm"]["token"]
    P("manoj", "/finance/stock/api/loss/%d/pile/move" % CID, {"item": ticked[0], "pile": "with_me"})
    r = P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"token": tok})
    C("a ticked line that moved after the tap: the confirm is refused (409), nothing written", r[0] == 409 and W(CID) == w1, r)
    P("manoj", "/finance/stock/api/loss/%d/pile/move" % CID, {"item": ticked[0], "pile": "auto"})
    rn0 = q("SELECT COALESCE(MAX(round_no),0) AS m FROM stock_voucher_line WHERE count_id=?", CID)[0]["m"]
    r = P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"group": "allowance", "items": ticked}); tok = r[1]["arm"]["token"]
    c0 = snap(); r, ms = timed(lambda: P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"token": tok})); d = delta(c0, snap())
    done = (r[1] or {}).get("done") or {}
    w2 = W(CID)
    wrote = sorted(i for i in w2 if w2[i]["action"] == "WRITE_OFF" and (i not in w1 or w1[i] != w2[i]))
    C("Clear writes off EXACTLY the ticked lines as that group (%d, WRITE_OFF + closed), the unticked stay open; %d ms" % (len(ticked), ms), r[0] == 200 and wrote == sorted(ticked) and done.get("kind") == "clear:allowance" and not done.get("auto_closed"), [r[1] and r[1].get("message"), wrote[:3], done.get("kind")])
    run = q("SELECT id, groups, kind, round_no, lines_n FROM stock_writeoff_run WHERE count_id=? ORDER BY id DESC LIMIT 1", CID)[0]
    g = json.loads(run["groups"])
    C("ONE stock_writeoff_run for the clear, kind clear:allowance, its lines all under 'allowance', Amir's vouchers in a new round (<= voucher batch a voucher)",
      run["kind"] == "clear:allowance" and list(g) == ["allowance"] and len(g["allowance"]) == len(ticked) and run["round_no"] == rn0 + 1 and run["lines_n"] == len(ticked)
      and sorted({x["item"] for x in q("SELECT item FROM stock_voucher_line WHERE count_id=? AND round_no=?", CID, run["round_no"])}) == sorted(ticked), [run["kind"], run["round_no"]])
    vl = q("SELECT kind, batch_no, COUNT(*) AS n FROM stock_voucher_line WHERE count_id=? AND round_no=? GROUP BY kind, batch_no", CID, run["round_no"])
    C("the voucher round is in batches of at most stock.voucher_batch lines", vl and max(x["n"] for x in vl) <= 8)
    Dd = piles(CID); wh = where(Dd)
    C("after the clear: the unticked line (%s) and the moved one are still open; the cleared ones read 'written off -- Within the allowance'; the patch carried the new totals and group counts" % left_out,
      wh[left_out][:2] == ("writeoff", "allowance") and wh[keep][:2] == ("bigloss", "big") and all(wh[i][0] == "written_off" and wh[i][1] == "allowance" for i in ticked) and done["patch"]["totals"] == Dd["totals"] and done["patch"]["groups_n"].get("allowance", 0) == 1, [wh[left_out][:2], done["patch"]["groups_n"]])
    C("the clear is in the record as its own run with its time and kind ('Clear this group -- Within the allowance'); no staff block yet (the count is still open)",
      any(x["kind"] == "clear:allowance" and "Within the allowance" in x["kind_text"] for x in Dd["record"]["runs"]) and not Dd["block"] and not q("SELECT 1 FROM stock_staff_block WHERE count_id=?", CID), [x["kind_text"] for x in Dd["record"]["runs"]])
    C("the block preview counts the cleared run already ('1 clear already in it')", Dd["block_preview"].get("cleared_runs") == 1, Dd["block_preview"].get("cleared_runs"))
    S["left_out"] = left_out; S["keep"] = keep; S["ticked"] = ticked
step("group", s4)

# ---------------------------------------------------------------- 5 the LAST clear closes the count by itself: one block from the union, the points once, the period line; Close still works as one tap
def s5():
    Dd = piles(CID); wh = where(Dd)
    P("manoj", "/finance/stock/api/loss/%d/pile/move" % CID, {"item": "W432 HOME TAB", "pile": "owner_use"})
    order = ("small", "old", "consume", "owner_use", "big", "allowance")
    runs_before = q("SELECT COUNT(*) AS n FROM stock_writeoff_run WHERE count_id=?", CID)[0]["n"]
    auto, last = False, None
    for gk in order:
        Dd = piles(CID); wh = where(Dd)
        items = sorted(i for i, v in wh.items() if v[0] in ("writeoff", "bigloss", "consume") and (v[1] or ("consume" if v[0] == "consume" else ("big" if v[0] == "bigloss" else "small"))) == gk)
        if not items:
            continue
        r = P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"group": gk, "items": items}); tok = r[1]["arm"]["token"]
        r = P("manoj", "/finance/stock/api/loss/%d/pile/clear" % CID, {"token": tok})
        last = (r[1] or {}).get("done") or {}
        if last.get("auto_closed"):
            auto = gk
    runs = q("SELECT id, groups, kind FROM stock_writeoff_run WHERE count_id=? ORDER BY id", CID)
    C("every group cleared in turn (%s): one run each, %d runs in all; the LAST clear (%s) closed the count by itself" % (", ".join(r_["kind"] for r_ in runs[runs_before:]), len(runs) - runs_before, auto),
      auto and last.get("auto_closed") and last.get("block") and len(runs) - runs_before >= 5, [auto, last and last.get("message")])
    B = q("SELECT * FROM stock_staff_block WHERE count_id=?", CID)
    allg = {}
    for r_ in runs:
        for k, v in json.loads(r_["groups"]).items():
            allg.setdefault(k, []).extend(v)
    loss = sum((x["mrp_p"] or 0) for k in ("allowance", "small", "big") for x in allg.get(k, []))
    big = sum((x["mrp_p"] or 0) for x in allg.get("big", []))
    C("ONE staff block (how 'auto'), frozen from the UNION of every clear: total = allowance + small + big of all the runs (%s), big by name (W432 BIG TAB first)" % loss,
      len(B) == 1 and B[0]["how"] == "auto" and B[0]["total_p"] == loss and B[0]["big_p"] == big and json.loads(B[0]["big_lines"])[0]["item"] == "W432 BIG TAB", B and [B[0]["how"], B[0]["total_p"], loss, B[0]["big_p"]])
    Dd = piles(CID)
    C("the desk shows the frozen block 'closed by itself after the last clear'; the record lists every clear and the close with their times; the piles are empty; W432 HOME TAB went as owner's use",
      Dd["block"] and Dd["block"]["how"] == "auto" and Dd["block"]["lines_en"][0].startswith("Count of 20-09-2026") and len(Dd["record"]["runs"]) == len(runs) and Dd["record"]["closes"] and Dd["record"]["closes"][-1]["how"] == "auto"
      and Dd["close"]["n"] == 0 and "W432 HOME TAB" in [x["item"] for x in allg.get("owner_use", [])], [Dd["block"] and Dd["block"]["how_text"], Dd["close"]["n"]])
    C("the S428 full-count points were written ONCE for count W432 (one point per counted line), the leakage period line 06-Sep -> 20-Sep is there",
      q("SELECT COUNT(*) AS n FROM stock_point WHERE source='full_count' AND count_id=?", CID)[0]["n"] == q("SELECT COUNT(*) AS n FROM stock_count_item WHERE count_id=?", CID)[0]["n"]
      and any(p["frm"] == "2026-09-06" and p["to"] == "2026-09-20" for p in SW.count_periods(sqlite3.connect(os.environ["FINANCE_DB"]))), [q("SELECT COUNT(*) AS n FROM stock_point WHERE source='full_count' AND count_id=?", CID)[0]["n"]])
    C("W432 BIG TAB carries exactly ONE Big-loss trace -- opened by the job / the clear (once per item per 30 days), never by a read", q("SELECT COUNT(*) AS n FROM stock_trace WHERE item='W432 BIG TAB' AND trigger='big_loss'")[0]["n"] == 1)
    C("the auto-close is audited; 'Close the count' on the empty desk is refused (400)", q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_pile' AND row_id=? AND action='auto_close'", CID)[0]["n"] == 1 and P("manoj", "/finance/stock/api/loss/%d/pile/close" % CID, {})[0] == 400)
    am = G("amir", "/finance/stock/api/pad/amir/%d" % CID)[1]
    C("Amir's board carries every clear's round; the owner's-use line in its own round", len(am["made"]["rounds"]) >= 5 and any(all("Owner's use" in (l.get("reason") or "") for b in rd["batches"] for l in b["lines"]) for rd in am["made"]["rounds"]), [rd["round_no"] for rd in am["made"]["rounds"]])
    st = G("darpan", "/finance/stockmatch/api/state?count=%d" % CID)[1]
    K = st.get("block")
    C("the block is pinned on Stock milaan in Hindi (the S427 wording: 'Ginti 20-09-2026 · kul kami', 'Chhoti kami, likh di gayi', 'Badi kami')", K and K["lines_hi"][0].startswith("Ginti 20-09-2026 · kul kami") and K["lines_hi"][1].startswith("Chhoti kami") and K["lines_hi"][2].startswith("Badi kami") and "W432 BIG TAB" in K["lines_hi"][2], K and K["lines_hi"])
    pdf = G("manoj", "/finance/stock/api/loss/%d/record.pdf" % CID)
    b = bytes(pdf[1]) if not isinstance(pdf[1], dict) else b""
    C("the record PDF lists each clear as its own run ('Clear this group -- ...') and the close of the count", pdf[0] == 200 and b[:4] == b"%PDF" and b"EACH CLOSE / CLEAR" in b and b"Clear this group -- " in b and b"EACH CLOSE OF THE COUNT" in b and b"closed by itself" in b, [pdf[0], len(b)])
    # Close the count still works as ONE tap (count #1's two crafted open lines), the same code path
    Dd = piles(1); items = Dd["close"]["items"]
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {}); tok = r[1]["arm"]["token"]
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {"token": tok})
    done = (r[1] or {}).get("done") or {}
    run = q("SELECT kind, lines_n FROM stock_writeoff_run WHERE count_id=1 ORDER BY id DESC LIMIT 1")[0]
    C("Close the count still works as one tap (count #1: %d lines): kind 'close', a block (how 'tap'), the patch, the Big-loss trace opened once" % len(items),
      r[0] == 200 and run["kind"] == "close" and run["lines_n"] == len(items) and done.get("block") and q("SELECT how FROM stock_staff_block WHERE id=?", done["block"])[0]["how"] == "tap" and done.get("patch")
      and q("SELECT COUNT(*) AS n FROM stock_trace WHERE item='W432 LATE TAB' AND trigger='big_loss'")[0]["n"] == 1, [r[1] and r[1].get("message"), run])
    run0 = q("SELECT id, md5, groups, lines_n FROM stock_writeoff_run WHERE count_id=1 ORDER BY id LIMIT 1")[0]
    C("count #1's frozen run of 27-Sep is untouched (md5, groups and lines equal before / after)", S.get("run0") and dict(S["run0"]) == dict(run0), [S.get("run0", {}).get("md5"), run0["md5"]])
step("close", s5)

# ---------------------------------------------------------------- 6 (3.4) the statement's Marg-negative lines; BELL CAST 5; qty_words' sign
def s6():
    Dst = G("manoj", "/finance/stock/api/statement/1")[1]
    sec = {s["key"]: s for s in Dst["sections"]}
    def L(item):
        for s in Dst["sections"]:
            for l in s["lines"] + s["matched"]:
                if l["item"] == item:
                    return s["key"], l
        return None, None
    pc4 = L('PRIME CAST 4"'); pc5 = L('PRIME CAST 5"'); bc = L("BELL CAST 5"); al = L("ALCOXIB 120")
    C('PRIME CAST 4" (Marg -24, shelf 0): tagged Marg negative -- book correction, no goods; Marg reads "-24 pcs"; 24 pcs to correct; no excess money',
      pc4[1] and pc4[1].get("neg_marg") and pc4[1]["marg_text"] == "-24 pcs" and pc4[1]["correct_text"] == "24 pcs" and pc4[1]["over"] == 0 and pc4[1]["over_p"] == 0 and "book correction" in pc4[1]["became"], pc4[1] and {k: pc4[1][k] for k in ("marg_text", "correct_text", "over_p", "became")})
    C("the Consumables section: PRIME CAST 4\"/5\" and BELL CAST 5 (moved there by the seed) are its Marg-negative lines; its excess money is Rs 0 on 0 lines; short unchanged (Rs 6,109)",
      pc4[0] == "Consumables" and pc5[0] == "Consumables" and bc[0] == "Consumables" and sec["Consumables"]["totals"]["over_p"] == 0 and sec["Consumables"]["totals"]["over_lines"] == 0 and sec["Consumables"]["totals"]["neg_lines"] == 3 and sec["Consumables"]["totals"]["short_p"] == 610900, sec["Consumables"]["totals"])
    C("BELL CAST 5 sits in Consumables in the section map, source owner, by 'S432, cast material', audited", q("SELECT section, source, by_user FROM stock_item_section WHERE item='BELL CAST 5'")[0]["section"] == "Consumables" and q("SELECT by_user FROM stock_item_section WHERE item='BELL CAST 5'")[0]["by_user"] == "S432, cast material"
      and q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_item_section' AND action='section_set' AND after_json LIKE '%BELL CAST 5%'")[0]["n"] == 1)
    M = sec["Medicines"]["totals"]
    negm = [l for l in sec["Medicines"]["lines"] if l.get("neg_marg")]
    C("the Medicines section: 8 Marg-negative lines (ALCOXIB 120, DECA INSTABOLIN 50, NEWTEL 40, FLUPIVAMP 100, TRAMEF P, GLI-ME SR1, PRIME PAD 4\"/6\") carry no excess money; its excess is the other lines' sum",
      len(negm) == 8 and M["neg_lines"] == 8 and all(l["over_p"] == 0 and l["over"] == 0 for l in negm) and M["over_p"] == sum(l["over_p"] or 0 for l in sec["Medicines"]["lines"]) and M["over_p"] < 4942682 and al[1]["marg_text"] == "-1 strip + 3 tabs", [sorted(l["item"] for l in negm), M["over_p"]])
    C("the Orthotics section: CERVICAL COLLAR SOFT HOPE L (Marg -1) is its Marg-negative line; the overall carries 12 such lines and its excess money excludes them all",
      sec["Orthotics"]["totals"]["neg_lines"] == 1 and Dst["overall"]["neg_lines"] == 12 and Dst["overall"]["over_p"] == sum(s["totals"]["over_p"] for s in Dst["sections"]) and Dst["overall"]["over_p"] < 13942651, [sec["Orthotics"]["totals"]["neg_lines"], Dst["overall"]["over_p"]])
    C("the section totals name the Marg-negative lines with their quantities to correct; the count line (S431's 373 + 3 crafted: Medicines 287, Consumables 20, Orthotics 69)",
      "PRIME CAST 4\" 24 pcs" in sec["Consumables"]["totals"]["neg_text"] and sec["Medicines"]["totals"]["lines"] == 287 and sec["Consumables"]["totals"]["lines"] == 20 and sec["Orthotics"]["totals"]["lines"] == 69, [sec["Consumables"]["totals"]["neg_text"], [sec[k]["totals"]["lines"] for k in ("Medicines", "Consumables", "Orthotics")]])
    C("every other S431 figure stands: Medicines short on the real lines unchanged (Rs 1,06,780.26 + the crafted W432 SOLD TAB's day figure is not short here), Orthotics short Rs 6,860 on 13 lines; the real excess lines still read 'never a loss'",
      sec["Orthotics"]["totals"]["short_p"] == 686000 and sec["Orthotics"]["totals"]["short_lines"] == 13 and all("never a loss" in l["became"] for l in sec["Medicines"]["lines"] if l["over"]) and M["short_lines"] >= 134, [sec["Orthotics"]["totals"]["short_p"], M["short_lines"]])
    r = G("manoj", "/finance/stock/api/statement/1.pdf"); pdf = r[1] if isinstance(r[1], bytes) else b""; txt = pdf.decode("latin-1", "replace")
    C("the PDF carries the Marg-negative line under the section totals and '-24 pcs' in the Marg column; no 'unit(s)'", r[0] == 200 and "Marg negative" in txt and "book correction" in txt and "-24 pcs" in txt and not hits([txt]), hits([txt])[:2])
    r = G("manoj", "/finance/stock/api/statement/1.xlsx"); x = r[1] if isinstance(r[1], bytes) else b""
    z = zipfile.ZipFile(io.BytesIO(x)) if x[:2] == b"PK" else None
    ss = "".join(z.read(nm).decode("utf-8", "replace") for nm in z.namelist() if nm.startswith("xl/worksheets/") or nm == "xl/sharedStrings.xml") if z else ""
    C("the XLSX: the Totals sheet has the 'Marg negative' column; a Marg-negative row is flagged", z is not None and "Marg negative" in ss and "book correction" in ss, [r[0], len(x)])
    pg = G("manoj", "/finance/stock/page/statement?count=1")
    C("the statement page carries the Marg-negative cell and the 'to correct' tag", pg[0] == 200 and b"Marg negative" in pg[1] and b"to correct" in pg[1])
    C("qty_words carries the sign: words(-24, '1*1') = '-24 pcs', Hindi '-24 nag'; words(-13, '1*10') = '-1 strip + 3 tabs'; a positive figure unchanged; signed() unchanged",
      QW.words(-24, "1*1") == "-24 pcs" and QW.words(-24, "1*1", lang="hi") == "-24 nag" and QW.words(-13, "1*10") == "-1 strip + 3 tabs" and QW.words(34, "1*10") == "3 strips + 4 tabs" and QW.signed(-30, "1*10") == "-3 strips" and QW.signed(4, "1*10") == "+4 tabs" and stock_app._qw(-34, 10) == "3 strips + 4 tabs")
    fz = G("manoj", "/finance/stock/api/statement/1")[1]
    C("the frozen-copy list and the close line still answer (S431 stands)", "frozen_list" in fz and fz.get("close") and fz["close"]["written_off"] >= 136)
step("statement", s6)

# ---------------------------------------------------------------- 7 gates, the page, the word gate
def s7():
    for u in ("bhati", "darpan", "shavez"):
        codes = [G(u, "/finance/stock/api/loss/1/piles?lite=1")[0], P(u, "/finance/stock/api/loss/%d/pile/clear" % CID, {"group": "allowance", "items": ["X"]})[0], P(u, "/finance/stock/api/watch/refresh", {})[0], G(u, "/finance/stock/page/loss?count=1")[0]]
        C("%s is refused on the desk, the clear door, Refresh watch and the page (%s)" % (u, codes), all(x in (401, 403, 302) for x in codes) and 404 not in codes, codes)
    pg = G("manoj", "/finance/stock/page/loss?count=1")[1]
    C("the page: the group card ('Close the count group by group', 'Tick all', 'Clear this group'), the light read first (?lite=1), the in-place patch (applyPatch), 'Refresh watch', the collapsed piles, the S430 strings kept",
      b"Close the count group by group" in pg and b"Tick all" in pg and b"Clear this group" in pg and b"?lite=1" in pg and b"applyPatch" in pg and b"Refresh watch" in pg and b"data-pile=" in pg
      and b"Owner's use" in pg and pg.count(b"closeBtn()") >= 2 and b"one tap for all three piles, at the top and the foot" in pg and b"data-close-arm" in pg and b"Count this" in pg and b"Counts &amp; watch" in pg, None)
    acc = []
    for cid in (1, CID):
        strings(piles(cid), acc)
    strings(G("manoj", "/finance/stock/api/statement/1")[1], acc)
    acc.append(pg.decode("utf-8", "replace"))
    C("no 'unit(s)' on the desk JSON (both counts), the statement JSON or the page", not hits(acc), hits(acc)[:3])
    print("TIMES:" + json.dumps(TIMES))
step("gates", s7)

try:
    import loss_piles as _lpx                                  # S436 adjustment: what the FILES carry
    has_cache_code = hasattr(_lpx, "cached")
except Exception:
    has_cache_code = False
cache_rows = (q("SELECT COUNT(*) AS n FROM stock_pile_cache")[0]["n"] if q("SELECT name FROM sqlite_master WHERE name='stock_pile_cache'") else None)
out = dict(mode=os.environ["MODE"], R=R, has_cache=bool(q("SELECT name FROM sqlite_master WHERE name='stock_pile_cache'")), has_cache_code=has_cache_code, cache_rows=cache_rows, times=TIMES, cnt=CNT)
print("JSON:" + json.dumps(out))
'''


def run(mode, app, db, cid):
    env = dict(os.environ, APPDIR=app, MODE=mode, FINANCE_DB=db, SPINE_DB=a.spine, CID=str(cid))
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=2400)
    txt = p.stdout.decode("utf-8", "replace")
    js = [l for l in txt.splitlines() if l.startswith("JSON:")]
    if not js:
        print(txt[-4000:])
        return None
    return json.loads(js[-1][5:])


print("-- NEW (the kit's files) on the scratch copies")
N = run("new", a.app, a.db, CID)
if N is None:
    check("the new app's probe ran", False)
else:
    for label, ok, got in N["R"]:
        if label is None:
            continue
        check(label, ok, got if not ok else None)
    check("the pile cache table exists on the new copy", N["has_cache"])
    T = N.get("times") or {}
    print("   MEASURED (the test client, in-process, this box): first read %s ms (the cache built) · second read %s ms · light read %s ms · a move %s ms · targets: piles < 1,000 ms, a move < 500 ms" % (T.get("first"), T.get("second"), T.get("lite"), T.get("move")))

print("-- NEGATIVE CONTROL: the same scenario on the box as it is (must go red)")
O = run("old", a.old, DB_OLD, CID_OLD)
if O is None:
    check("NEGATIVE: the old app's probe ran", False)
else:
    red = [l for l, ok, _g in O["R"] if not ok and l]
    for l, ok, _g in O["R"]:
        if l:
            print("   old %s  %s" % ("ok  " if ok else "RED ", l[:150]))
    must = ("the SECOND read is served from the cache",)
    green = {l for l, ok, _g in O["R"] if ok and l}
    check("NEGATIVE: the old files go red (%d of %d checks red): no cache (the report on every read), no clear door, the traces on the read path, no Marg-negative rule, no sign in qty_words" % (len(red), len(O["R"])),
          not any(any(m in g for m in must) for g in green) and len(red) >= 12, red[:6])
    check("NEGATIVE: the old FILES carry no cache (loss_piles without cached()) and the old app's read wrote no cache row on its copy (S436 adjustment: the table itself exists in today's live database since S432's install; S432 asserted its absence)",
          not O["has_cache_code"] and (O["cache_rows"] is None or O["cache_rows"] == CACHE_ROWS_OLD0), (O["has_cache_code"], O["cache_rows"], CACHE_ROWS_OLD0))
    oc = O.get("cnt") or {}
    check("NEGATIVE: on the old files a read composed the report and scored the watch (counters > 0)", oc.get("report", 0) > 0 and oc.get("owner_view", 0) > 0, oc)

print("WALK_S432 %s -- %d of %d %s" % ("GREEN" if not fails else "RED", (n - len(fails)) if not fails else len(fails), n, "passed" if not fails else "failed"))
for f in fails:
    print("   red: " + f)
sys.exit(0 if not fails else 1)
