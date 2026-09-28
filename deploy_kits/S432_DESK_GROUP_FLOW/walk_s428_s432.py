#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s428_s432.py -- S428's walk as S430 adjusted it (walk_s428_s430.py), re-run by kit S432_DESK_GROUP_FLOW with TWO more adjustments
(each named where it stands): (1) the Big-loss traces leave the desk's read path, so the walk taps 'Refresh watch' before it looks for
them; (2) the crafted confirmed-Sunday count is pinned to the Sunday a week back (the walk's own calendar assumed a Sunday run; on a
Monday "the last Sunday" was yesterday and its crafted bills fell outside the trace window -- nothing to do with the desk).
walk_s428_s430.py -- S428's walk, re-run by kit S430_DESK_FIRST_READ with ONE assertion adjusted for what S430 changes (named where
it stands): the 'unexplained' trace cases now start from a crafted earlier point of W428 UNEX TAB, because a trace whose anchor is the
count itself ends 'no earlier point -- first count' under S430. Everything else is S428's walk, verbatim.

walk_s428.py -- kit S428_STOCK_WATCH. THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over a
SCRATCH COPY of the live finance.db AND a scratch copy of the spine (SPINE_DB), driven through Flask's test client with
header identity (walk only). Its own crafted rows are keyed W428* and found BY KEY, never by counting. The SAME scenario
is then run against the box as it is (--old) on its own scratch copies: it must go red (the negative control).

  --app NEW     a copy of /root/finance with the kit's files
  --old OLD     a copy of /root/finance as the box is
  --db PATH     the scratch copy of finance.db (PATH.old is made for the old app)
  --spine PATH  the scratch copy of spine.db (crafted rows are written into it; both apps read it)

Prints item names of the shop, counts, rupees and dates. No patient, no number.
"""
import argparse
import datetime as dt
import json
import os
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
# crafted spine items: name, packing, unit_kind, mrp per strip (Rs), sales [(date, units, loose?)], close units on the latest closing
SP_ITEMS = (
    ("W428 ARRIVE TAB", "1*10", "LOOSE", 600.0, [(D(-60), 3000, 0), (D(-20), 3000, 0), (D(-3), 300, 0)], 500),
    ("W428 LOOSE TAB", "1*10", "LOOSE", 50.0, [(D(-30), 400, 1), (D(-10), 300, 1)], 200),
    ("W428 RECENT TAB", "1*10", "LOOSE", 300.0, [(D(-30), 2000, 0), (D(-10), 2000, 0)], 300),
    ("W428 ASK TAB", "1*10", "LOOSE", 40.0, [(D(-30), 100, 0)], 100),
    ("W428 TAPPED TAB", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 120),
    ("W428 GRACE TAB", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 120),
    ("W428 DUP TAB", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 300),
    ("W428 TAPNE TAB", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 300),
    ("W428 PACKM TAB", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 300),
    ("W428 TWIN A", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 300),
    ("W428 TWIN B", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 300),
    ("W428 FREE TAB", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 300),
    ("W428 SHORTDEL TAB", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 300),
    ("W428 TYPO TAB", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 50),
    ("W428 UNEX TAB", "1*10", "LOOSE", 80.0, [(D(-30), 200, 0)], 300),
    ("W428 LEAK TAB", "1*10", "LOOSE", 100.0, [(D(-30), 200, 0)], 300),
    ("W428 SYRUP", "200ML", "WHOLE", 150.0, [(D(-30), 40, 0)], 12),
)


def craft_spine(db):
    c = sqlite3.connect(db, timeout=30)
    latest = c.execute("SELECT MAX(as_on) FROM sp_close").fetchone()[0]
    for i, (name, packing, uk, mrp, sales, close) in enumerate(SP_ITEMS, 1):
        k = name[:20].strip()
        c.execute("INSERT OR REPLACE INTO sp_item (k20, name, packing, unit_kind, first_seen, last_seen) VALUES (?,?,?,?,?,?)", (k, name, packing, uk, "2026-03-31", latest))
        c.execute("INSERT INTO sp_item_fact (name, packing, fact, value, as_on, source_md5) VALUES (?,?,?,?,?,?)", (name, packing, "mrp", str(mrp), latest, "W428"))
        c.execute("INSERT INTO sp_item_fact (name, packing, fact, value, as_on, source_md5) VALUES (?,?,?,?,?,?)", (name, packing, "salt", "W428SALT" if "TWIN" in name else "W428S%d" % i, latest, "W428"))
        ps = 10 if packing == "1*10" else 1
        for j, (day, units, loose) in enumerate(sales, 1):
            qr = ("0:%d" % units) if loose else (("%d:%d" % divmod(units, ps)) if ps > 1 else str(units))
            c.execute("INSERT OR REPLACE INTO sp_sale_line (date, bill, seq, name20, k20, pack, qty_raw, units, rate_p, batch, expiry) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (day, "W428-%02d-%s" % (i, day.replace("-", "")), j, k, k, packing, qr, float(units), int(mrp * 100), "W428", "12/28"))
        c.execute("INSERT OR REPLACE INTO sp_close (as_on, k20, units, source_md5) VALUES (?,?,?,?)", (latest, k, float(close), "W428"))
    # purchases: ARRIVE TAB arrived today (spine carries it); DUP TAB the same bill twice; PACKM TAB 5 strips on one bill; FREE TAB free 2 strips
    # the supplier key the spine would give 'W428 SUPPLIERS' (letters only, 8): WSUPPLIE -- so the tapped arrival of ARRIVE TAB is found in the spine
    for k, sup, bill, day, qty, free, units, seq in (("W428 ARRIVE TAB", "WSUPPLIE", "W428-A1", TODAY.isoformat(), 8, 0, 80, 1),
                                                     ("W428 DUP TAB", "W428SUPP", "W428-D1", D(-6), 5, 0, 50, 1), ("W428 DUP TAB", "W428SUPP", "W428-D1", D(-5), 5, 0, 50, 2),
                                                     ("W428 PACKM TAB", "W428SUPP", "W428-P1", D(-4), 5, 0, 50, 1),
                                                     ("W428 FREE TAB", "W428SUPP", "W428-F1", D(-3), 10, 2, 100, 1)):   # all after the last Sunday: inside the trace's window
        c.execute("INSERT INTO sp_purchase_line (supkey, bill, date, seq, name27, k20, packing, qty, free, units, amount_p, net_amount_p, direction, source_md5) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (sup, bill, day, seq, k, k[:20].strip(), "1*10", float(qty), float(free), float(units), 1000, 1000, "PURCHASE", "W428"))
    c.commit()
    c.close()


def craft(db):
    c = sqlite3.connect(db, timeout=30)
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    # a supplier's order: TAPPED TAB arrived (tap 8, no spine entry yet -> provisional); GRACE TAB arrived 5 days ago, never entered; SHORTDEL TAB tap 6, bill 8
    oid = c.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, note, total_p, sent_by, section) VALUES (?,?,?,?,?,?,?,?)",
                    ((TODAY - dt.timedelta(days=6)).isoformat() + "T10:00:00", "manoj", "W428 SUPPLIERS", "sent", "walk", 0, "manoj", "Medicines")).lastrowid
    for item, packs, supplied, arrived, billed in (("W428 TAPPED TAB", 10, 8, D(-1) + "T09:00:00", None), ("W428 GRACE TAB", 5, 5, D(-5) + "T09:00:00", None),
                                                    ("W428 SHORTDEL TAB", 8, 6, D(-2) + "T09:00:00", 8), ("W428 ARRIVE TAB", 10, 8, D(-1) + "T09:30:00", 10)):
        c.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units, rate_p, value_p, on_hand, supplied, short, missing, arrived_by, arrived_at, billed_qty) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (oid, item, packs, 10, packs * 10, 0, 0, 0, supplied, 1 if supplied < packs else 0, 0, "shavez", arrived, billed))
    c.commit()
    c.close()


DB_OLD = a.db + ".old"
copydb(a.db, DB_OLD)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s428  # noqa: E402
assert seed_s428.seed(a.db, a.app) == 0, "seed failed"
craft(a.db)
craft(DB_OLD)
craft_spine(a.spine)
print("-- scratch seeded (the watch's settings), crafted W428 rows on both scratch copies and in the scratch spine; old-app copy %s" % os.path.basename(DB_OLD))

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
import stock_app
try:
    import stock_watch as SW
except Exception:
    SW = None
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data()]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
spdb = sqlite3.connect(os.environ["SPINE_DB"], timeout=30)
TODAY = dt.date.today()
D = lambda k: (TODAY + dt.timedelta(days=k)).isoformat()
R = []
def C(label, cond, got=None):
    R.append([label, bool(cond), (json.dumps(got, default=str)[:400] if got is not None else None)])
def step(name, fn):
    try:
        fn()
    except Exception as e:
        C(name + " -- the step ran", False, "%s: %s" % (type(e).__name__, str(e)[:300]))
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
def watch():
    r = G("manoj", "/finance/stock/api/watch"); return r[1] if r[0] == 200 and isinstance(r[1], dict) else None
def needs():
    r = G("manoj", "/finance/sanjeevni/api/needs-you"); return [l["text"] for l in (r[1] or {}).get("lines", [])] if r[0] == 200 else []
def setw(key, val):
    return P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": key, "value": val})
def dstate():
    r = G("darpan", "/finance/stockmatch/api/state?count=1"); return (r[1] or {}).get("watch") if r[0] == 200 else None
next_mon = TODAY + dt.timedelta(days=(7 - TODAY.weekday()) % 7 or 7)
next_wed = next_mon + dt.timedelta(days=2)
S = {}

# ---------------------------------------------------------------- 0 the gates and the wiring
def s0():
    for u in ("bhati", "darpan", "shavez"):
        codes = [G(u, "/finance/stock/api/watch")[0], P(u, "/finance/stock/api/watch/ask", {"item": "TYRO BR"})[0], G(u, "/finance/stock/api/watch/roster")[0],
                 P(u, "/finance/stock/api/watch/roster/build", {})[0]]
        C("%s is refused on the owner's watch (card, ask, roster, build) (%s)" % (u, codes), all(x in (401, 403, 302) for x in codes) and 404 not in codes, codes)
    W = watch()
    C("the owner's watch card answers: plan, rosters, the watch list, traces, leakage, the settings heading", bool(W) and W.get("ok") and all(k in W for k in ("plan", "roster_today", "watch", "traces", "leak", "settings")), None if not W else sorted(W))
    D0 = G("manoj", "/finance/stock/api/loss/1/piles")[1]
    C("the Loss desk's JSON carries the watch card; the piles are still the four of S427", isinstance(D0, dict) and (D0.get("watch") or {}).get("ok") and [p["key"] for p in D0["piles"]] == ["with_me", "writeoff", "bigloss", "consume"])
    pg = G("manoj", "/finance/stock/page/loss?count=1")[1]
    C("the desk page has 'Count this', the watch card and the second settings heading", b"Count this" in pg and b"Counts &amp; watch" in pg)
    st = {s["key"] for s in (D0.get("watch") or {}).get("settings", [])}
    C("the second heading 'Counts & watch' lists the watch's keys", {"count.cadence_months", "spot.days", "spot.cap", "arrival.bill_grace_days", "leak.budget_pct"} <= st, sorted(st)[:8])
    r = setw("spot.cap", "2"); r2 = setw("spot.cap", "abc"); r3 = setw("stock.voucher_batch", "6")
    lg = q("SELECT after_json FROM audit_log WHERE table_name='setting' AND action='stock_setting' AND after_json LIKE '%spot.cap%' ORDER BY id DESC LIMIT 1")
    C("a watch setting saves through the desk's door, audited; a bad value is refused; a loss-desk key still works", r[0] == 200 and r2[0] == 400 and r3[0] == 200 and lg, [r, r2, r3])
    C("the S427 walk's ground still holds: TYRO BR in Big losses, the block preview, the close count", any(l["item"] == "TYRO BR" for p in D0["piles"] if p["key"] == "bigloss" for l in p["lines"]) and D0.get("block_preview") and D0["close"]["n"] > 0)
step("wiring", s0)

# ---------------------------------------------------------------- 1 the full count's Sunday
def s1():
    r = setw("count.cadence_months", "0.5")
    W = watch(); pl = W["plan"]["plan"]
    C("a count falls due (the last closed count 06-09 + half a month): the plan opens with four Sundays", r[0] == 200 and pl and pl["status"] == "open" and len(pl["window"]) == 4 and all(dt.date.fromisoformat(w).weekday() == 6 for w in pl["window"]), pl)
    S["win"] = pl["window"]
    C("Needs you says the count is due and Amir picks", any("Full count is due" in t for t in needs()), needs()[:6])
    am = G("amir", "/finance/stock/api/pad/amir/1")[1]
    C("Amir's board carries the Sunday buttons", (am.get("watch") or {}).get("plan") and am["watch"]["plan"]["window_text"] == pl["window_text"], (am.get("watch") or {}).get("plan"))
    C("bhati and darpan cannot pick the Sunday", P("bhati", "/finance/stock/api/watch/plan/pick", {"sunday": pl["window"][1]})[0] in (401, 403, 302) and P("darpan", "/finance/stock/api/watch/plan/pick", {"sunday": pl["window"][1]})[0] == 403)
    r = P("amir", "/finance/stock/api/watch/plan/pick", {"sunday": pl["window"][1]})
    ds = dstate()
    C("Amir picks the second Sunday; Darpan's Stock milaan asks 'Theek hai?'", r[0] == 200 and r[1]["plan"]["status"] == "picked" and ds and ds.get("plan") and "Theek hai" in ds["plan"]["text_hi"] and pl["window"][1] in ds["plan"]["sunday"], [r[1], ds and ds.get("plan")])
    r = P("darpan", "/finance/stockmatch/api/plan?count=1", {"answer": "no"})
    W = watch()
    C("Darpan: 'Nahi ho payega' -> back to Amir (open, no Sunday)", r[0] == 200 and W["plan"]["plan"]["status"] == "open" and not W["plan"]["plan"]["sunday"], W["plan"]["plan"])
    P("amir", "/finance/stock/api/watch/plan/pick", {"sunday": pl["window"][2]})
    r = P("darpan", "/finance/stockmatch/api/plan?count=1", {"answer": "ok"})
    W = watch(); pl2 = W["plan"]["plan"]
    C("Amir picks the third Sunday, Darpan says 'Theek hai' -> confirmed", r[0] == 200 and pl2["status"] == "confirmed" and pl2["sunday"] == pl["window"][2] and pl2["confirmed_by"] == "darpan", pl2)
    S["sunday"] = pl2["sunday"]; S["sunday_text"] = pl2["sunday_text"]
    C("Needs you carries the confirmed date; the checklist line (shavez reads it) names it in Hindi; the checklist page fetches it",
      any(("Full count: Sunday %s" % pl2["sunday_text"]) in t for t in needs()) and G("shavez", "/finance/stock/api/watch/plan/line")[0] == 200
      and pl2["sunday_text"] in G("shavez", "/finance/stock/api/watch/plan/line")[1]["text_hi"] and b"plan428" in G("shavez", "/finance/packs/checklist")[1], [needs()[:4], G("shavez", "/finance/stock/api/watch/plan/line")[1]])
    C("a repeat 'Theek hai' writes nothing new; bhati cannot answer", P("darpan", "/finance/stockmatch/api/plan?count=1", {"answer": "ok"})[0] == 200 and P("bhati", "/finance/stockmatch/api/plan?count=1", {"answer": "ok"})[0] in (401, 403, 302))
    # a count begun on a Tuesday is a spot: the cadence is unmoved
    tue = TODAY - dt.timedelta(days=(TODAY.weekday() - 1) % 7 or 7)
    cid = db.execute("INSERT INTO stock_count (unit, marg_as_on, bill_no, bill_date, started_at, submitted_at, submitted_by, items_total, items_counted, status) VALUES ('medical',?,?,?,?,?,'W428',3,3,'submitted')",
                     (tue.strftime("%d-%m-%Y"), "W428T", tue.isoformat(), tue.isoformat() + "T10:00:00", tue.isoformat() + "T12:00:00")).lastrowid
    db.execute("INSERT INTO stock_count_close (count_id, closed_at, closed_by, how, left_not_counted, left_to_fix) VALUES (?,?,?,?,0,0)", (cid, tue.isoformat() + "T12:30:00", "W428", "complete")); db.commit()
    W = watch()
    C("a count begun on a Tuesday (%s) is closed but does not move the cadence: the last full count is still 06-09-2026" % tue.strftime("%d-%m-%Y"), W["plan"]["last"]["as_on"] == "2026-09-06", W["plan"]["last"])
    # a count on a confirmed Sunday moves it
    sun = TODAY - dt.timedelta(days=(TODAY.weekday() + 1) % 7 or 7)
    if (TODAY - sun).days < 7:                                # S432 adjustment 2: run on a Monday, "the last Sunday" was yesterday, and the crafted bills
        sun -= dt.timedelta(days=7)                           # (D(-3) .. D(-6)) fell before the confirmed-Sunday count's anchor: the Sunday a week back, as on 27-Sep
    db.execute("INSERT INTO stock_count_plan (due_from, sunday, picked_by, picked_at, confirmed_by, confirmed_at, status, window_json) VALUES (?,?,?,?,?,?,?,?)",
               ((sun - dt.timedelta(days=10)).isoformat(), sun.isoformat(), "amir", sun.isoformat(), "darpan", sun.isoformat(), "done", "[]"))
    cid2 = db.execute("INSERT INTO stock_count (unit, marg_as_on, bill_no, bill_date, started_at, submitted_at, submitted_by, items_total, items_counted, status) VALUES ('medical',?,?,?,?,?,'W428',3,3,'submitted')",
                      (sun.strftime("%d-%m-%Y"), "W428S", sun.isoformat(), sun.isoformat() + "T10:00:00", sun.isoformat() + "T12:00:00")).lastrowid
    db.execute("INSERT INTO stock_count_close (count_id, closed_at, closed_by, how, left_not_counted, left_to_fix) VALUES (?,?,?,?,0,0)", (cid2, sun.isoformat() + "T12:30:00", "W428", "complete")); db.commit()
    S["cid2"] = cid2; S["sun"] = sun.isoformat()
    W = watch()
    C("a count closed on a confirmed Sunday (%s) is the last full count; the next due date moves with it" % sun.strftime("%d-%m-%Y"), W["plan"]["last"]["as_on"] == sun.isoformat() and W["plan"]["due_from"] > sun.isoformat(), [W["plan"]["last"], W["plan"]["due_from"]])
step("plan", s1)

# ---------------------------------------------------------------- 2 auto-adjust
def s2():
    setw("count.cadence_months", "2")
    sun = dt.date.fromisoformat(S["sun"])
    def prev_iso(before_iso):
        ds = ["%s-%s-%s" % (r["marg_as_on"][6:], r["marg_as_on"][3:5], r["marg_as_on"][:2]) for r in q("SELECT c.marg_as_on FROM stock_count c JOIN stock_count_close k ON k.count_id=c.id WHERE c.id NOT IN (SELECT count_id FROM stock_count_part)")]
        ds = [d_ for d_ in ds if d_ < before_iso]
        return max(ds)
    pi = prev_iso(S["sun"])
    sales = spdb.execute("SELECT COALESCE(SUM(net_p),0) FROM sp_sale_bill WHERE date>? AND date<=?", (pi, S["sun"])).fetchone()[0]
    def run(cid, pct):
        loss = int(sales * pct / 100.0)
        g = {"big": [{"item": "W428 BAD", "short_units": 10, "short_text": "1 strip", "mrp_p": loss, "cost_p": loss, "why": "walk", "pack": 10}]}
        db.execute("INSERT INTO stock_writeoff_run (count_id, at, by_user, lines_n, mrp_p, cost_p, unpriced, groups, settings, md5) VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (cid, dt.datetime.now().isoformat(), "W428", 1, loss, loss, 0, json.dumps(g), "{}", "w428")); db.commit()
    run(S["cid2"], 2.4)
    W = watch()
    lg = q("SELECT verdict, cadence_from, cadence_to, leak_pct FROM stock_watch_adjust ORDER BY run_id DESC LIMIT 1")
    C("auto-adjust: a closed count losing 2.4%% of the period's sales (%s) moves the cadence 2 -> 1, one Needs-you line" % ("Rs %d sales" % (sales // 100)),
      sales > 0 and lg and lg[0]["verdict"] == "bad" and lg[0]["cadence_from"] == 2 and lg[0]["cadence_to"] == 1 and W["plan"]["cadence_months"] == 1 and any("moved to monthly" in t for t in needs()), [lg, W["plan"]["cadence_months"], [t for t in needs() if "Full count" in t]])
    setw("count.cadence_months", "2")
    # two counts running at 0.8% -- on weekdays 10 and 3 days before that Sunday (so each has a period of real sales behind it)
    for k, back in ((1, 10), (2, 3)):
        d = sun - dt.timedelta(days=back)
        p_iso = prev_iso(d.isoformat())
        cid = db.execute("INSERT INTO stock_count (unit, marg_as_on, bill_no, bill_date, started_at, submitted_at, submitted_by, items_total, items_counted, status) VALUES ('medical',?,?,?,?,?,'W428',3,3,'submitted')",
                         (d.strftime("%d-%m-%Y"), "W428G%d" % k, d.isoformat(), d.isoformat() + "T10:00:00", d.isoformat() + "T12:00:00")).lastrowid
        db.execute("INSERT INTO stock_count_close (count_id, closed_at, closed_by, how, left_not_counted, left_to_fix) VALUES (?,?,?,?,0,0)", (cid, d.isoformat() + "T12:30:00", "W428", "complete")); db.commit()
        sales_k = spdb.execute("SELECT COALESCE(SUM(net_p),0) FROM sp_sale_bill WHERE date>? AND date<=?", (p_iso, d.isoformat())).fetchone()[0] or 100000
        loss = int(sales_k * 0.8 / 100.0)
        g = {"small": [{"item": "W428 GOOD", "short_units": 1, "short_text": "1 tab", "mrp_p": loss, "cost_p": loss, "why": "walk", "pack": 10}]}
        db.execute("INSERT INTO stock_writeoff_run (count_id, at, by_user, lines_n, mrp_p, cost_p, unpriced, groups, settings, md5) VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (cid, dt.datetime.now().isoformat(), "W428", 1, loss, loss, 0, json.dumps(g), "{}", "w428g%d" % k)); db.commit()
        W = watch()
    lg = q("SELECT verdict, cadence_from, cadence_to FROM stock_watch_adjust ORDER BY run_id DESC LIMIT 2")
    C("two closed counts running at 0.8% move the cadence 2 -> 3 (the first good one alone moves nothing), one line each", len(lg) == 2 and lg[1]["cadence_to"] == 2 and lg[0]["verdict"] == "good" and lg[0]["cadence_to"] == 3 and W["plan"]["cadence_months"] == 3
      and any("every 3 months" in t for t in needs()), [lg, W["plan"]["cadence_months"]])
    setw("count.cadence_months", "2")
step("adjust", s2)

# ---------------------------------------------------------------- 3 the roster
def s3():
    setw("spot.cap", "2"); setw("spot.days", "MON,WED,SAT")
    con = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30)
    SW.ensure(con)
    # a point two days ago on RECENT TAB -> no repeat inside 7 days
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("W428 RECENT TAB", "W428 RECENT TAB", D(-2) + "T07:00:00", 300, "spot", "darpan", 300, 0, "settled", D(-2) + "T07:00:00")); con.commit()
    r = P("manoj", "/finance/stock/api/watch/ask", {"item": "W428 ASK TAB"})
    C("the owner's 'Count this' lands (W428 ASK TAB) and a repeat says so", r[0] == 200 and P("manoj", "/finance/stock/api/watch/ask", {"item": "W428 ASK TAB"})[1]["message"].startswith("W428 ASK TAB is already"), r)
    pv1 = SW.preview_roster(con, next_mon); pv2 = SW.preview_roster(con, next_mon)
    C("the preview of the next Monday is the same twice (a seeded tie-break)", pv1 == pv2 and pv1, [x["item"] for x in pv1])
    Rm = SW.build_roster(con, next_mon, who="walk")
    items = [x["item"] for x in Rm["items"]]
    C("on the Monday the job writes the ask first, then <= cap items: %s" % items, Rm["is_spot_day"] and items[0] == "W428 ASK TAB" and len(items) == 3, items)
    C("an arrival within 3 days with high turnover is among the chosen; a loose-heavy item never; an item counted 2 days ago never",
      "W428 ARRIVE TAB" in items[1:] and "W428 LOOSE TAB" not in items and "W428 RECENT TAB" not in items, items)
    Rm2 = SW.build_roster(con, next_mon, who="walk")
    C("a re-run on the same day writes nothing new (the same roster)", [x["id"] for x in Rm2["items"]] == [x["id"] for x in Rm["items"]])
    S["roster"] = {x["item"]: x for x in Rm["items"]}
    tue = next_mon + dt.timedelta(days=1)
    Rt = SW.build_roster(con, tue, who="walk")
    C("a Tuesday is not a spot day: nothing is written", not Rt["items"] and not Rt["is_spot_day"])
    # Darpan answers on his card (the roster of the Monday is what his page would show that morning; the walk answers through the same door)
    ask = S["roster"]["W428 ASK TAB"]; arr = S["roster"]["W428 ARRIVE TAB"]; third = [x for x in Rm["items"] if x["item"] not in ("W428 ASK TAB", "W428 ARRIVE TAB")][0]
    r = P("darpan", "/finance/stockmatch/api/spot?count=1", {"roster_id": ask["id"], "strips": 9, "loose": 9})
    pt = q("SELECT gap_units, status, source FROM stock_point WHERE item='W428 ASK TAB' ORDER BY id DESC LIMIT 1")
    ll = q("SELECT COUNT(*) AS n FROM stock_watch_loss_line WHERE item='W428 ASK TAB'")[0]["n"]
    C("Darpan's answer 9 patte + 9 goli on W428 ASK TAB (records 10 strips): 1 tab short, within the allowance -> a quiet loss point, no staff line",
      r[0] == 200 and pt and pt[0]["gap_units"] == -1 and pt[0]["source"] == "spot" and ll == 0 and "thoda" in r[1]["saved"]["message"], [r[1] and r[1].get("saved", {}).get("message"), pt])
    r = P("darpan", "/finance/stockmatch/api/spot?count=1", {"roster_id": arr["id"], "strips": 54, "loose": 0})
    pt = q("SELECT gap_units, expected_units, status FROM stock_point WHERE item='W428 ARRIVE TAB' ORDER BY id DESC LIMIT 1")
    ll = q("SELECT gap_units FROM stock_watch_loss_line WHERE item='W428 ARRIVE TAB'")
    ds = dstate()
    C("W428 ARRIVE TAB: records 58 strips (50 closing + 8 bought today), counted 54 -> 4 strips short beyond the allowance: a dated loss line under the block ('Aaj: W428 ARRIVE TAB 4 patte kam'), and a trace",
      r[0] == 200 and pt and pt[0]["expected_units"] == 580 and pt[0]["gap_units"] == -40 and ll and ll[0]["gap_units"] == 40 and ds and any("W428 ARRIVE TAB 4 patte kam" in l["text_hi"] for l in ds["losses"])
      and q("SELECT COUNT(*) AS n FROM stock_trace WHERE item='W428 ARRIVE TAB'")[0]["n"] == 1, [pt, ll, ds and [l["text_hi"] for l in ds["losses"]][:3]])
    W = watch()
    C("the owner's watch card shows the loss line's item among the traces", any(t["item"] == "W428 ARRIVE TAB" for t in W["traces"]))
    rz = P("darpan", "/finance/stockmatch/api/stock?count=1", {"item": "W428 GRACE TAB", "strips": 18, "loose": 0})
    C("a surplus is noted, never a loss: W428 GRACE TAB counted 18 strips against 12 on record (its tap came before the latest closing, so it is Marg's already) -> '6 patte zyada', no loss line",
      rz[0] == 200 and "6 patte zyada" in rz[1]["saved"]["message"] and rz[1]["saved"]["point"]["gap"] == 60 and rz[1]["saved"]["point"]["status"] == "settled"
      and q("SELECT COUNT(*) AS n FROM stock_watch_loss_line WHERE item='W428 GRACE TAB'")[0]["n"] == 0, rz[1] and rz[1].get("saved"))
    # the third item stays unanswered -> carried to the Wednesday
    Rw = SW.build_roster(con, next_wed, who="walk")
    C("unanswered on Monday -> carried to the Wednesday's roster (marked carried)", any(x["item"] == third["item"] and x["carried"] for x in Rw["items"]), [(x["item"], x["carried"]) for x in Rw["items"]])
    C("a repeat answer on the same roster item writes nothing", P("darpan", "/finance/stockmatch/api/spot?count=1", {"roster_id": ask["id"], "strips": 9, "loose": 9})[1]["saved"]["message"].startswith("Pehle hi"))
    C("bhati / shavez cannot answer the roster; an unknown roster id is refused", all(P(u, "/finance/stockmatch/api/spot?count=1", {"roster_id": ask["id"], "pcs": 1})[0] in (401, 403, 302) for u in ("bhati", "shavez")) and P("darpan", "/finance/stockmatch/api/spot?count=1", {"roster_id": 999999, "pcs": 1})[0] == 404)
    # three misses in a week -> Needs you
    for k in (1, 3, 5):
        con.execute("INSERT INTO stock_spot_roster (day, item_norm, item, reason, rank, asked_at, pack, packing) VALUES (?,?,?,?,1,?,10,'1*10')", (D(-k), "W428 MISSED", "W428 MISSED", "walk", D(-k) + "T06:30:00"))
    con.commit()
    SW.build_roster(con, TODAY, who="walk", force=True)
    C("three unanswered mornings in a week -> one Needs-you line", any("unanswered" in t for t in needs()), [t for t in needs() if "Spot" in t])
    # Stock batao (any day, any item) and the word gate on his messages
    r = P("darpan", "/finance/stockmatch/api/stock?count=1", {"item": "W428 SYRUP", "pcs": 12})
    C("'Stock batao': W428 SYRUP 12 botal -> a darpan point matching the records", r[0] == 200 and "12 botal" in r[1]["saved"]["message"] and "barabar" in r[1]["saved"]["message"], r[1] and r[1].get("saved", {}).get("message"))
    it = G("darpan", "/finance/stockmatch/api/watch-items?count=1&q=w428 syr")
    C("his search box finds the item with its whole word (botal)", it[0] == 200 and any(x["item"] == "W428 SYRUP" and x["whole"] == "botal" for x in it[1]["items"]), it[1])
    con.close()
step("roster", s3)

# ---------------------------------------------------------------- 4 arrivals as provisional stock
def s4():
    con = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30)
    P0 = SW.write_point(con, "W428 TAPPED TAB", 200, "darpan", "walk")
    C("a tapped arrival (8 strips) the spine does not carry raises the expected stock (12 -> 20 strips) and marks the point provisional",
      P0["expected"] == 200 and P0["provisional"] == 80 and P0["status"] == "provisional" and P0["gap"] == 0, P0)
    spdb.execute("INSERT INTO sp_purchase_line (supkey, bill, date, seq, name27, k20, packing, qty, free, units, amount_p, net_amount_p, direction, source_md5) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 ("WSUPPLIE", "W428-T1", TODAY.isoformat(), 1, "W428 TAPPED TAB", "W428 TAPPED TAB", "1*10", 8.0, 0.0, 80.0, 1000, 1000, "PURCHASE", "W428")); spdb.commit()
    nset = SW.settle_provisional(con)
    pt = q("SELECT status, expected_units, gap_units, provisional_units FROM stock_point WHERE id=?", P0["id"])[0]
    C("the purchase reaches the spine -> the point is re-evaluated and settled (expected 20 strips, gap 0)", nset >= 1 and pt["status"] == "settled" and pt["expected_units"] == 200 and pt["gap_units"] == 0 and pt["provisional_units"] == 0, pt)
    W = watch()
    C("tap 8 strips / bill 10 strips on W428 ARRIVE TAB -> the owner's line", any("tap 8 strips, bill 10 strips" in x["text"] for x in W["tap_vs_bill"]), [x["text"] for x in W["tap_vs_bill"]])
    am = G("amir", "/finance/stock/api/pad/amir/1")[1]
    bp = (am.get("watch") or {}).get("bill_pending") or []
    C("an arrival tapped 5 days ago with no purchase in the spine -> Amir's line 'bill entry baaki: W428 SUPPLIERS <date>'", any("bill entry baaki: W428 SUPPLIERS" in x["text_hi"] for x in bp), [x["text_hi"] for x in bp])
    C("W428 ARRIVE TAB (bill in the spine) is not on that line", not any(x["item"] == "W428 ARRIVE TAB" for x in bp))
    con.close()
step("arrivals", s4)

# ---------------------------------------------------------------- 5 the trace -- seven crafted cases, one per check
def s5():
    con = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30)
    def tr(item, gap, trig="darpan"):
        return SW.open_trace(con, item, trig, gap, "walk")
    t1 = tr("W428 DUP TAB", -50)
    C("1 the same bill twice: W428 DUP TAB 5 strips short -> explained, fix 'bill W428-D1 do baar: ek hataayein'", t1["verdict"] == "explained" and "do baar" in t1["fix"] and not t1["findings"][0]["ok"], [t1["verdict"], t1["fix"]])
    t2 = tr("W428 TAPNE TAB", 80)
    con2 = con
    if t2["verdict"] != "explained":
        # the tap for TAPNE lives on a fresh order line
        oid = con.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, note, total_p, sent_by, section) VALUES (?,?,?,?,?,?,?,?)", (D(-4) + "T10:00:00", "manoj", "W428 SUPPLIERS", "sent", "walk", 0, "manoj", "Medicines")).lastrowid
        con.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units, rate_p, value_p, on_hand, supplied, short, missing, arrived_by, arrived_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (oid, "W428 TAPNE TAB", 8, 10, 80, 0, 0, 0, 8, 0, 0, "shavez", D(-2) + "T09:00:00")); con.commit()
        t2 = tr("W428 TAPNE TAB", 80)
    C("2 an arrival tapped, no entry: W428 TAPNE TAB 8 strips over -> explained ('tapped as arrived, not yet entered')", t2["verdict"] == "explained" and "tapped as arrived" in t2["findings"][1]["text"], [t2["verdict"], t2["findings"][1]["text"]])
    t3 = tr("W428 PACKM TAB", -50)
    C("3 a pack-multiple gap: 5 strips short against a bill of 5 strips -> explained, 'boxes read as strips'", t3["verdict"] == "explained" and "boxes read as strips" in t3["findings"][2]["text"], [t3["verdict"], t3["findings"][2]["text"]])
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("W428 TWIN B", "W428 TWIN B", D(-1) + "T07:00:00", 320, "spot", "darpan", 300, 20, "settled", D(-1) + "T07:00:00")); con.commit()
    t4 = tr("W428 TWIN A", -20)
    C("4 a twin item: W428 TWIN A 2 strips short, W428 TWIN B (same salt) 2 strips over -> explained, the swap named", t4["verdict"] == "explained" and "W428 TWIN B" in t4["findings"][3]["text"] and "adla-badli" in t4["fix"], [t4["verdict"], t4["fix"]])
    t5 = tr("W428 FREE TAB", 20)
    C("5 scheme strips: 2 free strips on the bill, 2 strips over -> explained", t5["verdict"] == "explained" and "free" in t5["findings"][4]["text"], [t5["verdict"], t5["findings"][4]["text"]])
    t6 = tr("W428 SHORTDEL TAB", -20)
    C("6 short delivery: bill 8 strips, tapped 6, 2 strips short -> explained, the supplier named", t6["verdict"] == "explained" and "W428 SUPPLIERS" in t6["findings"][5]["text"] and "poochhein" in t6["fix"], [t6["verdict"], t6["fix"]])
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("W428 TYPO TAB", "W428 TYPO TAB", D(0) + "T07:00:00", 500, "spot", "darpan", 50, 450, "settled", D(0) + "T07:00:00")); con.commit()
    t7 = tr("W428 TYPO TAB", 450)
    C("7 a mistyped point: 50 strips counted against 5 on record -> 'ten times ... a typing slip?', partly", not t7["findings"][6]["ok"] and "typing slip" in t7["findings"][6]["text"] and t7["verdict"] in ("partly", "explained"), [t7["verdict"], t7["findings"][6]["text"]])
    # S430 adjustment: an earlier settled point (gap 0) on W428 UNEX TAB, so the trace measures from a point, not from the count itself
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("W428 UNEX TAB", "W428 UNEX TAB", D(-2) + "T07:00:00", 300, "spot", "darpan", 300, 0, "settled", D(-2) + "T07:00:00")); con.commit()
    tu = tr("W428 UNEX TAB", -30)
    ny = needs()
    C("an unexplained gap names its window and reaches Needs you the same day", tu["verdict"] == "unexplained" and any("W428 UNEX TAB" in t and "unexplained" in t and "between" in t for t in ny), [tu["verdict"], tu["window_text"], [t for t in ny if "UNEX" in t]])
    tu2 = tr("W428 UNEX TAB", -30)
    W = watch()
    C("two unexplained traces on one item within a month -> it joins the close-watch list", any(x["item"] == "W428 UNEX TAB" and "unexplained" in x["why"] for x in W["watch"]), [x["item"] for x in W["watch"] if "W428" in x["item"]])
    r = P("darpan", "/finance/stockmatch/api/gadbad?count=1", {"item": "W428 DUP TAB", "text": "ek dabba nahi mil raha", "strips": 25, "loose": 0})
    T = (r[1] or {}).get("saved", {}).get("trace") or {}
    ds = dstate()
    C("'Kuchh gadbad hai' through his page: a point + the trace (explained: the bill twice); Darpan sees 'Aapki baat sahi thi'", r[0] == 200 and T.get("verdict") == "explained" and ds and any(t["item"] == "W428 DUP TAB" and t["entry_error"] for t in ds["traces"]), [r[0], T.get("verdict"), ds and [t["text_hi"] for t in ds["traces"]][:3]])
    tid = T.get("id")
    r = P("darpan", "/finance/stockmatch/api/trace/%s/seen?count=1" % tid, {})
    C("'Dekh liya' marks the trace seen; bhati cannot", r[0] == 200 and q("SELECT status FROM stock_trace WHERE id=?", tid)[0]["status"] == "seen" and P("bhati", "/finance/stockmatch/api/trace/%s/seen?count=1" % tid, {})[0] in (401, 403, 302))
    am = G("amir", "/finance/stock/api/pad/amir/1")[1]
    C("Amir's board carries the fix line 'bill W428-D1 do baar: ek hataayein'", any("do baar" in x["fix"] for x in (am.get("watch") or {}).get("fixes", [])), [x["fix"] for x in (am.get("watch") or {}).get("fixes", [])][:3])
    D0 = G("manoj", "/finance/stock/api/loss/1/piles")[1]
    P("manoj", "/finance/stock/api/watch/refresh", {"count_id": 1})   # S432 adjustment: the traces leave the read path -- 'Refresh watch' (or the close) opens them
    C("a trace is open on every Big-loss line of the desk (TYRO BR among them), once (S432 adjustment: after Refresh watch, not by reading)", q("SELECT COUNT(*) AS n FROM stock_trace WHERE item='TYRO BR' AND trigger='big_loss'")[0]["n"] == 1 and all(q("SELECT COUNT(*) AS n FROM stock_trace WHERE item=? AND trigger='big_loss'", l["item"])[0]["n"] == 1 for p in D0["piles"] if p["key"] == "bigloss" for l in p["lines"][:8]))
    con.close()
step("trace", s5)

# ---------------------------------------------------------------- 6 the budget and the watch
def s6():
    con = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30)
    ym = TODAY.strftime("%Y-%m")
    con.execute("DELETE FROM stock_writeoff_run WHERE by_user='W428'"); con.commit()   # the auto-adjust's crafted runs would count as this month's loss
    sales = spdb.execute("SELECT COALESCE(SUM(net_p),0) FROM sp_sale_bill WHERE substr(date,1,7)=?", (ym,)).fetchone()[0]
    L0 = SW.month_leak(con, ym)
    base = L0["loss_p"] if L0 else 0
    per_tab = 1000  # W428 LEAK TAB: Rs 100 a strip of 10
    def add(pct_target, day):
        want = int(sales * pct_target / 100.0) - (SW.month_leak(con, day[:7]) or {}).get("loss_p", 0)
        tabs = max(1, int(round(want / per_tab)))
        con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    ("W428 LEAK TAB", "W428 LEAK TAB", day + "T07:00:00", 0, "spot", "darpan", tabs, -tabs, "settled", day + "T07:00:00")); con.commit()
    add(0.6, TODAY.isoformat())
    L1 = SW.month_leak(con, ym)
    C("the leakage line is green at 0.6%% (%s)" % L1["text"], L1 and L1["pct"] is not None and 0.5 <= L1["pct"] <= 0.75 and not L1["red"], L1)
    add(1.4, TODAY.isoformat())
    L2 = SW.month_leak(con, ym)
    C("and red at 1.4%% (%s)" % L2["text"], L2 and 1.3 <= L2["pct"] <= 1.55 and L2["red"], L2)
    M = G("manoj", "/finance/sanjeevni/api/months")[1]
    row = [m for m in M.get("months", []) if m["ym"] == ym]
    C("the approvals page's Month section carries the line for this month", row and (row[0].get("leak") or {}).get("text", "").startswith("Leakage") and row[0]["leak"]["red"], row and row[0].get("leak"))
    pg = G("manoj", "/finance/approvals")
    C("the approvals page's one anchored line is in place", pg[0] in (200, 302) and (pg[0] != 200 or b"S428: leakage" in pg[1]))
    prev = (TODAY.replace(day=1) - dt.timedelta(days=1))
    pym = prev.strftime("%Y-%m")
    sales_prev = spdb.execute("SELECT COALESCE(SUM(net_p),0) FROM sp_sale_bill WHERE substr(date,1,7)=?", (pym,)).fetchone()[0] or 1000000
    tabs = max(1, int(round(sales_prev * 1.5 / 100.0 / per_tab)))
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("W428 LEAK TAB", "W428 LEAK TAB", prev.isoformat() + "T07:00:00", 0, "spot", "darpan", tabs, -tabs, "settled", prev.isoformat() + "T07:00:00")); con.commit()
    C("two red months running -> one Needs-you line", any("Leakage over the 1% budget for 2 months running" in t for t in needs()), [t for t in needs() if "Leakage" in t])
    W = watch()
    top = [x for x in W["watch"] if x["why"] == "top by sales value"]
    C("the watch list: the top items by sales value (TYRO BR, ROSIKA FORTE among them), costly items, with their last points in strips words and a monthly trend",
      any(x["item"] == "TYRO BR" for x in top) and any(x["item"] == "ROSIKA FORTE" for x in top) and all(len(x["trend"]) == 3 for x in W["watch"]) and any("costly" in x["why"] for x in W["watch"]), [x["item"] for x in top][:6])
    con.close()
step("leak", s6)

# ---------------------------------------------------------------- 7 the word gate, the pages, the kept routes
def s7():
    pages = {"loss": G("manoj", "/finance/stock/page/loss?count=1")[1], "stockmatch": G("darpan", "/finance/stockmatch")[1], "amir": G("amir", "/finance/stock/page/amir?count=1")[1],
             "checklist": G("shavez", "/finance/packs/checklist")[1]}
    bad = {k: hits([v.decode("utf-8", "replace")]) for k, v in pages.items() if isinstance(v, bytes)}
    C("the word gate -- no 'unit(s)' on the rendered desk, Stock milaan, Amir's board, the checklist", all(not v for v in bad.values()), {k: v[:3] for k, v in bad.items() if v})
    jsons = {"watch": watch(), "stockmatch": G("darpan", "/finance/stockmatch/api/state?count=1")[1], "amir": (G("amir", "/finance/stock/api/pad/amir/1")[1] or {}).get("watch"),
             "needs": [t for t in needs() if "stock" in t.lower() or "count" in t.lower() or "Leakage" in t]}
    badj = {}
    for k, j in jsons.items():
        acc = []; strings(j, acc); h = hits(acc)
        if h: badj[k] = h[:4]
    C("the word gate -- no 'unit(s)' in any text the watch gives the desk, Stock milaan, Amir's board or Needs you", not badj, badj)
    sm = pages["stockmatch"]
    C("Stock milaan carries 'Aaj ki ginti', 'Stock batao', 'Kuchh gadbad hai', and no budget or percentage on Darpan's texts", b"Aaj ki ginti" in sm and b"Stock batao" in sm and b"Kuchh gadbad hai" in sm and "%" not in json.dumps(jsons["stockmatch"].get("watch") or {}, ensure_ascii=False).replace("%s", ""))
    C("Amir's page carries the Sunday card", b"Sunday" in pages["amir"] and b"bill entry baaki" in pages["amir"].lower() or b"Bill entry baaki" in pages["amir"])
    for p in ("/finance/stock/page/diffs", "/finance/stock/api/open", "/finance/stock/api/loss/1/record.pdf"):
        C("kept: %s answers" % p, G("manoj", p)[0] in (200, 404), G("manoj", p)[0])
    C("the S427 doors are kept (close, items, recount 410)", hasattr(stock_app, "api_loss_pile_close") and hasattr(stock_app, "api_loss_items") and P("manoj", "/finance/stock/api/loss/1/pile/recount", {})[0] == 410)
step("pages", s7)

out = dict(mode=os.environ["MODE"], R=R, has_sw=bool(SW))
print("JSON:" + json.dumps(out))
'''


def run(mode, app, db):
    env = dict(os.environ, APPDIR=app, MODE=mode, FINANCE_DB=db, SPINE_DB=a.spine)
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=2400)
    txt = p.stdout.decode("utf-8", "replace")
    js = [l for l in txt.splitlines() if l.startswith("JSON:")]
    if not js:
        print(txt[-4000:])
        return None
    return json.loads(js[-1][5:])


print("-- NEW (the kit's files) on the scratch copies")
N = run("new", a.app, a.db)
if N is None:
    check("the new app's probe ran", False)
else:
    for label, ok, got in N["R"]:
        check(label, ok, got if not ok else None)
    check("stock_watch is beside the app", N["has_sw"])

print("-- NEGATIVE CONTROL: the same scenario on the box as it is (must go red)")
O = run("old", a.old, DB_OLD)
if O is None:
    check("NEGATIVE: the old app's probe ran", False)
else:
    red = [l for l, ok, _g in O["R"] if not ok]
    for l, ok, _g in O["R"]:
        print("   old %s  %s" % ("ok  " if ok else "RED ", l))
    must = ("the owner's watch card answers: plan, rosters, the watch list, traces, leakage, the settings heading",
            "the desk page has 'Count this', the watch card and the second settings heading")
    green = {l for l, ok, _g in O["R"] if ok}
    check("NEGATIVE: the old files go red (%d of %d checks red): no watch card, no Count this, no plan, no roster, no trace" % (len(red), len(O["R"])),
          not any(m in green for m in must) and len(red) >= 10, red[:10])
    check("NEGATIVE: no stock_watch beside the old app", not O["has_sw"])

print("WALK_S428 %s -- %d of %d %s" % ("GREEN" if not fails else "RED", (n - len(fails)) if not fails else len(fails), n, "passed" if not fails else "failed"))
for f in fails:
    print("   red: " + f)
sys.exit(0 if not fails else 1)
