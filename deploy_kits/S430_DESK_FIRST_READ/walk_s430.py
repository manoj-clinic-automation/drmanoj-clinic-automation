#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s430.py -- kit S430_DESK_FIRST_READ. THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over SCRATCH
copies of the live finance.db and the spine, driven through Flask's test client with header identity (walk only). The round is the
real count #1; its own crafted rows are keyed W430* and found BY KEY. The kit's seed (seed_s430) runs on the scratch first, as the
installer runs it on the live database. The SAME scenario then runs against the box as it is (--old): it must go red.

  --app NEW --old OLD --db PATH --spine PATH
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
# item, packing, pack, marg, counted, MRP per tab/pc (paise; None = unpriced on the desk), spine sales [(date, units)], spine purchases [(date, qty, units)]
CRAFT = (
    ("W430 OLD PC", "1*1", 1, 3, 0, None, [], []),                                                  # no sale, no purchase, no price -> Old stock
    ("W430 OLD2 PC", "1*1", 1, 3, 0, None, [], [(D(-40), 3, 3)]),                                     # the same, with one purchase -> not old (unpriced -> Big losses)
    ("W430 USE TAB", "1*10", 10, 20, 0, 1000, [(D(-90), 100)], []),                                   # 2 strips short, Rs 200 -> small; the owner moves it to owner's use
)


def craft(db):
    c = sqlite3.connect(db, timeout=30)
    as_on = c.execute("SELECT marg_as_on FROM stock_count WHERE id=1").fetchone()[0]
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    for it, packing, ps, marg, cnt, mrp, _s, _p in CRAFT:
        c.execute("INSERT OR REPLACE INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,'walk W430')", (as_on, it, marg, packing, ps, now))
        c.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, strips, loose, counted_by, entered_by, at) VALUES (1,?,?,?,?,?,0,0,'W430','W430',?)",
                  (it, packing, ps, marg, cnt, now))
        c.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, pack_size, value_p, cause, status, counted_by) VALUES (1,?,?,?,?,?,?,NULL,'UNEXPLAINED','open','W430')",
                  (it, as_on, marg, cnt, cnt - marg, ps))
        if mrp is not None:
            c.execute("INSERT OR REPLACE INTO stock_mrp_manual (item, mrp_p, source, set_by, set_at) VALUES (?,?,'walk W430','W430',?)", (it, mrp, now))
    c.commit()
    c.close()


def craft_spine(db):
    c = sqlite3.connect(db, timeout=30)
    latest = c.execute("SELECT MAX(as_on) FROM sp_close").fetchone()[0]
    for i, (it, packing, ps, marg, cnt, mrp, sales, purch) in enumerate(CRAFT, 1):
        k = it[:20].strip()
        c.execute("INSERT OR REPLACE INTO sp_item (k20, name, packing, unit_kind, first_seen, last_seen) VALUES (?,?,?,?,?,?)", (k, it, packing, "LOOSE" if ps > 1 else "WHOLE", "2026-03-31", latest))
        for j, (day, units) in enumerate(sales, 1):
            c.execute("INSERT OR REPLACE INTO sp_sale_line (date, bill, seq, name20, k20, pack, qty_raw, units, rate_p, batch, expiry) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (day, "W430-%02d-%s" % (i, day.replace("-", "")), j, k, k, packing, "%d:%d" % divmod(units, ps) if ps > 1 else str(units), float(units), int((mrp or 0) * ps), "W430", "12/28"))
        for j, (day, qty, units) in enumerate(purch, 1):
            c.execute("INSERT INTO sp_purchase_line (supkey, bill, date, seq, name27, k20, packing, qty, free, units, amount_p, net_amount_p, direction, source_md5) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      ("W430SUPP", "W430-P%d" % i, day, j, k, k, packing, float(qty), 0.0, float(units), 1000, 1000, "PURCHASE", "W430"))
        c.execute("INSERT OR REPLACE INTO sp_close (as_on, k20, units, source_md5) VALUES (?,?,?,?)", (latest, k, float(marg), "W430"))
    c.commit()
    c.close()


DB_OLD = a.db + ".old"
copydb(a.db, DB_OLD)
craft(a.db)
craft(DB_OLD)
craft_spine(a.spine)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s430  # noqa: E402
assert seed_s430.seed(a.db, a.app) == 0, "seed failed"
print("-- scratch: crafted W430 rows on both copies and in the scratch spine; the S430 seed ran on the new copy (owner's use, the list, the alias, the traces)")

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
import finance_app as fa
import stock_app
try:
    import stock_watch as SW
    import loss_piles as LP
except Exception:
    SW = LP = None
try:
    import order_rules as OR
except Exception:
    OR = None
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
def piles():
    r = G("manoj", "/finance/stock/api/loss/1/piles"); return r[1] if r[0] == 200 and isinstance(r[1], dict) else None
def where(Dd):
    out = {}
    for p in Dd["piles"]:
        for l in p["lines"]:
            out[l["item"]] = (p["key"], l.get("group"), l)
    for k in ("back", "written_off"):
        for l in Dd["done"][k]:
            out[l["item"]] = (k, l.get("group"), l)
    for l in Dd["over"]:
        out[l["item"]] = ("over", None, l)
    return out
def needs():
    r = G("manoj", "/finance/sanjeevni/api/needs-you"); return [l["text"] for l in (r[1] or {}).get("lines", [])] if r[0] == 200 else []
S = {}

# ---------------------------------------------------------------- 1 the piles under S430: owner's use, the list, old stock
def s1():
    Dd = piles(); S["D0"] = Dd
    wh = where(Dd)
    C("the piles answer; the fourth pile is 'Consumption & owner's use'", bool(Dd) and [p["key"] for p in Dd["piles"]] == ["with_me", "writeoff", "bigloss", "consume"] and Dd["piles"][3]["title"] == "Consumption & owner's use", Dd and [p["title"] for p in Dd["piles"]])
    C("ECONORM CAP and PARI CR 25 sit in Consumption & owner's use, group owner's use (the seed moved them, audited as the owner's word)",
      wh.get("ECONORM CAP", (None,))[:2] == ("consume", "owner_use") and wh.get("PARI CR 25", (None,))[:2] == ("consume", "owner_use")
      and q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_pile' AND action='move' AND after_json LIKE '%ECONORM CAP%owner_use%'")[0]["n"] == 1, [wh.get("ECONORM CAP", (None,))[:2], wh.get("PARI CR 25", (None,))[:2]])
    C("their why says owner's use -- a recorded non-loss", "owner's use" in (wh.get("ECONORM CAP", (None, None, {}))[2].get("why") or ""), wh.get("ECONORM CAP", (None, None, {}))[2].get("why"))
    C("VINBACTUM DS and VINTAZ P 4500 INJ are on the consumption list -> Consumption, group clinic consumption, tag 'on your consumption list' (VINTAZ P had been moved by the owner)",
      wh.get("VINBACTUM DS", (None,))[:2] == ("consume", "consume") and wh.get("VINTAZ P 4500 INJ", (None,))[:2] == ("consume", "consume")
      and "on your consumption list" in (wh.get("VINTAZ P 4500 INJ", (None, None, {}))[2].get("why") or ""), [wh.get("VINBACTUM DS", (None,))[:2], wh.get("VINTAZ P 4500 INJ", (None, None, {}))[2].get("why")])
    lst = [s for s in Dd["settings"] if s["key"] == "stock.consume_items"][0]["items"]
    C("the list carries VINBACTUM DS, VINTAZ P 4500 INJ and VINTAZ P 4500 (the two spellings)", all(x in lst for x in ("VINBACTUM DS", "VINTAZ P 4500 INJ", "VINTAZ P 4500")), lst)
    rn = q("SELECT old_name, new_name, done_at, verified_at FROM marg_item_rename WHERE old_name='VINTAZ P 4500 INJ'")
    import item_alias
    C("the two VINTAZ spellings are joined in the rename memory (D620), verified, and 'VINTAZ P 4500' resolves to the count's line", rn and rn[0]["new_name"] == "VINTAZ P 4500" and rn[0]["verified_at"] and item_alias.resolve(db, "VINTAZ P 4500") == "VINTAZ P 4500 INJ", rn)
    C("GLOCREPE, CORTIRI and CUFLIN D (no sale, no purchase since 01-04-2026, no price) are OLD STOCK in the Write-off pile -- never a Big loss",
      all(wh.get(i, (None,))[:2] == ("writeoff", "old") for i in ("GLOCREPE", "CORTIRI", "CUFLIN D")), {i: wh.get(i, (None,))[:2] for i in ("GLOCREPE", "CORTIRI", "CUFLIN D")})
    C("the old-stock why names the opening and 'not a loss'", "since 01-04-2026" in wh["GLOCREPE"][2]["why"] and "not a loss" in wh["GLOCREPE"][2]["why"], wh["GLOCREPE"][2]["why"])
    C("crafted: W430 OLD PC (never sold, never bought, unpriced) -> old; W430 OLD2 PC (one purchase) -> not old, a Big loss as before; W430 USE TAB -> small",
      wh.get("W430 OLD PC", (None,))[:2] == ("writeoff", "old") and wh.get("W430 OLD2 PC", (None,))[:2] == ("bigloss", "big") and wh.get("W430 USE TAB", (None,))[:2] == ("writeoff", "small"),
      {i: wh.get(i, (None,))[:2] for i in ("W430 OLD PC", "W430 OLD2 PC", "W430 USE TAB")})
    st = {s["key"] for s in Dd["settings"]}
    C("the settings card carries stock.old_stock_days (180)", "stock.old_stock_days" in st and [s for s in Dd["settings"] if s["key"] == "stock.old_stock_days"][0]["value"] == "180")
    pg = G("manoj", "/finance/stock/page/loss?count=1")[1]
    C("the page: the fifth destination in the menu, the Close button drawn by one function at the top and the foot, the three headers' line",
      b"Owner's use" in pg and pg.count(b"closeBtn()") >= 2 and b"one tap for all three piles, at the top and the foot" in pg and b"data-close-arm" in pg, [pg.count(b"closeBtn()")])
step("piles", s1)

# ---------------------------------------------------------------- 2 the -> pile menu: owner's use, and back
def s2():
    w0, d0 = q("SELECT COUNT(*) AS n FROM stock_diff_lane")[0]["n"], q("SELECT COUNT(*) AS n FROM stock_diff_decision")[0]["n"]
    r = P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W430 USE TAB", "pile": "owner_use"})
    Dd = piles(); wh = where(Dd)
    C("W430 USE TAB moved to Owner's use -> the Consumption & owner's use pile, group owner's use, recorded; decides nothing",
      r[0] == 200 and wh["W430 USE TAB"][:2] == ("consume", "owner_use") and wh["W430 USE TAB"][2].get("moved") and q("SELECT COUNT(*) AS n FROM stock_diff_lane")[0]["n"] == w0 and q("SELECT COUNT(*) AS n FROM stock_diff_decision")[0]["n"] == d0, [r, wh["W430 USE TAB"][:2]])
    T = Dd["totals"]
    C("the pile's total carries it; the block preview does not (owner's use is never a loss)", any(l["item"] == "W430 USE TAB" for l in Dd["piles"][3]["lines"]) and "W430 USE TAB" not in json.dumps(Dd["block_preview"]["big_lines"]) and T["consume"]["n"] >= 5)
    C("a repeat move to the same destination says so", P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W430 USE TAB", "pile": "owner_use"})[1]["message"].startswith("Already"))
    r = P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W430 USE TAB", "pile": "auto"})
    C("back to the system's choice re-piles it (small real gap)", r[0] == 200 and where(piles())["W430 USE TAB"][:2] == ("writeoff", "small"))
    P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W430 USE TAB", "pile": "owner_use"})
    C("a wrong destination is refused", P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W430 USE TAB", "pile": "recount"})[0] == 400)
step("move", s2)

# ---------------------------------------------------------------- 3 Close the count -- the same door as the top button; the groups, the rounds, the block, leakage
def s3():
    Dd = piles()
    items = Dd["close"]["items"]
    ou = sorted(l["item"] for l in Dd["piles"][3]["lines"] if l["group"] == "owner_use")
    old = sorted(l["item"] for l in Dd["piles"][1]["lines"] if l["group"] == "old")
    C("the close counts every line of the three piles, owner's use and old stock among them", set(ou) <= set(items) and set(old) <= set(items) and "ECONORM CAP" in ou and "GLOCREPE" in old, [len(items), ou, old])
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {}); tok = r[1]["arm"]["token"]
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {"token": tok})
    run = q("SELECT id, groups, round_no FROM stock_writeoff_run WHERE count_id=1 ORDER BY id DESC LIMIT 1")[0]
    g = json.loads(run["groups"])
    C("the count closes: ONE run with the groups allowance / small / old / consume / owner_use / big, ECONORM CAP and PARI CR 25 under owner's use, GLOCREPE under old",
      r[0] == 200 and set(g) <= {"allowance", "small", "old", "consume", "owner_use", "big"} and {x["item"] for x in g.get("owner_use", [])} >= {"ECONORM CAP", "PARI CR 25", "W430 USE TAB"} and "GLOCREPE" in [x["item"] for x in g.get("old", [])], {k: len(v) for k, v in g.items()})
    done = r[1]["done"]
    vl = q("SELECT item, round_no FROM stock_voucher_line WHERE count_id=1 AND round_no=?", done["owner_use_round"]) if done.get("owner_use_round") else []
    C("the owner's-use lines are vouchered in their own round (%s), exactly those lines" % done.get("owner_use_round"), done.get("owner_use_round") and sorted({x["item"] for x in vl}) == sorted(g["owner_use"] and [x["item"] for x in g["owner_use"]]), [done.get("owner_use_round"), sorted({x["item"] for x in vl})])
    am = G("amir", "/finance/stock/api/pad/amir/1")[1]
    rd = [x for x in am["made"]["rounds"] if x["round_no"] == done["owner_use_round"]]
    C("that round is on Amir's board and every line of it reads 'Owner's use' (the label's test)", rd and all("Owner's use" in (l.get("reason") or "") for b in rd[0]["batches"] for l in b["lines"]), rd and [l.get("reason") for b in rd[0]["batches"] for l in b["lines"]][:2])
    B = q("SELECT total_p, small_p, big_p, big_lines FROM stock_staff_block WHERE count_id=1 ORDER BY id DESC LIMIT 1")[0]
    loss = sum((x["mrp_p"] or 0) for k in ("allowance", "small", "big") for x in g.get(k, []))
    C("the staff block = allowance + small + big only -- owner's use and old stock are not in it and not named", B["total_p"] == loss and not any(x["item"] in ("ECONORM CAP", "PARI CR 25", "GLOCREPE", "CORTIRI") for x in json.loads(B["big_lines"])), [B["total_p"], loss])
    # leakage: the period line
    per = SW.count_periods(db)
    L = SW.month_leak(db, TODAY.strftime("%Y-%m"))
    cost = sum((x.get("cost_p") or x.get("mrp_p") or 0) for k in ("allowance", "small", "big") for x in g.get(k, []))
    sales = spdb.execute("SELECT COALESCE(SUM(net_p),0) FROM sp_sale_bill WHERE date>'2026-04-01' AND date<='2026-09-06'").fetchone()[0]
    C("leakage is dated by PERIOD: 01-Apr -> 06-Sep, the run's allowance + small + big at cost (%s) against the period's sales (%s) -- owner's use and old stock excluded" % (cost, sales),
      per and per[-1]["frm"] == "2026-04-01" and per[-1]["to"] == "2026-09-06" and per[-1]["loss_p"] == cost and per[-1]["sales_p"] == sales and per[-1]["pct"] is not None and per[-1]["pct"] < 2.0, per and per[-1])
    C("the Month section's line for September reads the period line ('01-Apr → 06-Sep: leakage …'), green", L and L["text"].startswith("01-Apr → 06-Sep: leakage") and L["period"] and not L["red"], L and L["text"])
    C("September alone is never red from the count: its pro-rata share is a fraction of the period", L and L["share_p"] < per[-1]["loss_p"] and L["pct"] is not None and L["pct"] <= per[-1]["pct"] + 0.01, L and [L["share_p"], L["pct"], per[-1]["pct"]])
    con = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30)
    Pp = SW.write_point(con, "W430 USE TAB", 0, "spot", "walk", silent=True)
    L2 = SW.month_leak(con, TODAY.strftime("%Y-%m"))
    C("a spot point of today still dates today (it adds to this month's points, the period line keeps its own figure)", L2["points_p"] >= 0 and L2["period"]["loss_p"] == L["period"]["loss_p"], [L2["points_p"], L2["text"]])
    M = G("manoj", "/finance/sanjeevni/api/months")[1]
    row = [m for m in M.get("months", []) if m["ym"] == TODAY.strftime("%Y-%m")]
    C("the approvals API carries the period line", row and (row[0].get("leak") or {}).get("text", "").startswith("01-Apr"), row and row[0].get("leak"))
    con.close()
step("close", s3)

# ---------------------------------------------------------------- 4 traces on the first count; the watch list
def s4():
    W = G("manoj", "/finance/stock/api/watch")[1]
    fc = q("SELECT COUNT(*) AS n FROM stock_trace WHERE verdict='first_count'")[0]["n"]
    un = q("SELECT COUNT(*) AS n FROM stock_trace WHERE verdict='unexplained' AND trigger='big_loss'")[0]["n"]
    C("the count-#1 traces read 'no earlier point -- first count', none 'unexplained'; the card collapses them to one line", fc >= 20 and un == 0 and W["first_count_n"] == fc and not any(t["verdict"] == "first_count" for t in W["traces"]), [fc, un, W["first_count_n"], len(W["traces"])])
    C("their Needs-you lines are gone", not any("unexplained -- between" in t for t in needs()), [t for t in needs() if "unexplained" in t][:3])
    C("the trace log has one line for the count's own lines, not one per item", q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_watch' AND action='trace_first_count'")[0]["n"] >= 1
      and q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_watch' AND action='trace' AND after_json LIKE '%first_count%'")[0]["n"] == 0)
    con = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30)
    T0 = SW.open_trace(con, "W430 OLD2 PC", "darpan", -3, "walk")
    C("a new trace with no earlier point ends 'first_count' too (no Needs-you line)", T0["verdict"] == "first_count" and not any("W430 OLD2 PC" in t for t in needs()), T0["verdict"])
    con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("W430 OLD2 PC", "W430 OLD2 PC", D(-1) + "T07:00:00", 3, "spot", "darpan", 3, 0, "settled", D(-1) + "T07:00:00")); con.commit()
    T1 = SW.open_trace(con, "W430 OLD2 PC", "darpan", -3, "walk")
    C("a trace from a spot point onward is 'unexplained' as before, and reaches Needs you", T1["verdict"] == "unexplained" and any("W430 OLD2 PC" in t for t in needs()), T1["verdict"])
    W = G("manoj", "/finance/stock/api/watch")[1]
    wl = [x["item"] for x in W["watch"]]
    secs = {r["item"]: r["section"] for r in q("SELECT item, section FROM stock_item_section")}
    C("the watch list has no orthotic line and no cast shoe; Bonista PF and Hylastos stay (costly, unsold, over Rs 2,000)",
      not any(secs.get(i) == "Orthotics" or stock_app._is_orthotic(i) for i in wl) and not any("CAST SHOE" in i or "BELL CAST" in i for i in wl) and "BONISTA PF" in wl and "HYLASTOS" in wl, [i for i in wl if "CAST" in i or "BELT" in i][:5])
    lo = W.get("watch_left_out") or []
    C("what left is named: cast shoes / Bell Cast (no sale in 90 days, under Rs 2,000), the belts (orthotic section)", any("CAST SHOE" in x[0] for x in lo) and any("BELT" in x[0] and x[1] == "orthotic section" for x in lo), lo[:6])
    C("the dead-value setting is on the card", any(s["key"] == "spot.dead_high_value_p" and s["value"] == "200000" for s in W["settings"]))
    con.close()
step("watch", s4)

# ---------------------------------------------------------------- 5 the order hints, the word gate
def s5():
    C("order_rules speaks strips / pcs: keep-in-stock 120 of a 10-strip item = '12 strips'; 3 of a pcs item = '3 pcs'", OR and OR._qw(120, {"packing": "1*10", "pack_size": 10}) == "12 strips" and OR._qw(3, {"packing": "1*1", "pack_size": 1}) == "3 pcs")
    src = open(os.path.join(APP, "order_rules.py"), encoding="utf-8").read()
    C("the four hints no longer say 'units'", "units (your rule)" not in src and "units on order #" not in src)
    pages = {"loss": G("manoj", "/finance/stock/page/loss?count=1")[1], "stockmatch": G("darpan", "/finance/stockmatch")[1], "amir": G("amir", "/finance/stock/page/amir?count=1")[1]}
    bad = {k: hits([v.decode("utf-8", "replace")]) for k, v in pages.items() if isinstance(v, bytes)}
    C("the word gate -- no 'unit(s)' on the rendered desk, Stock milaan, Amir's board", all(not v for v in bad.values()), {k: v[:3] for k, v in bad.items() if v})
    jsons = {"piles": piles(), "watch": G("manoj", "/finance/stock/api/watch")[1], "amir": (G("amir", "/finance/stock/api/pad/amir/1")[1] or {}).get("made")}
    badj = {}
    for k, j in jsons.items():
        acc = []; strings(j, acc); h = hits(acc)
        if h: badj[k] = h[:4]
    C("the word gate -- no 'unit(s)' in the desk's, the watch's or the board's texts", not badj, badj)
    C("bhati / darpan / shavez are refused on the desk", all(G(u, "/finance/stock/api/loss/1/piles")[0] in (401, 403, 302) for u in ("bhati", "darpan", "shavez")))
step("words", s5)

out = dict(mode=os.environ["MODE"], R=R, has_owner_use=bool(LP and "owner_use" in getattr(LP, "GROUP_TITLE", {})))
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
    check("loss_piles knows owner's use", N["has_owner_use"])

print("-- NEGATIVE CONTROL: the same scenario on the box as it is (must go red)")
O = run("old", a.old, DB_OLD)
if O is None:
    check("NEGATIVE: the old app's probe ran", False)
else:
    red = [l for l, ok, _g in O["R"] if not ok]
    for l, ok, _g in O["R"]:
        print("   old %s  %s" % ("ok  " if ok else "RED ", l))
    must = ("the piles answer; the fourth pile is 'Consumption & owner's use'",
            "GLOCREPE, CORTIRI and CUFLIN D (no sale, no purchase since 01-04-2026, no price) are OLD STOCK in the Write-off pile -- never a Big loss")
    green = {l for l, ok, _g in O["R"] if ok}
    check("NEGATIVE: the old files go red (%d of %d checks red): no owner's use, no old stock, no top button, the count's traces 'unexplained', the cast shoes on the watch" % (len(red), len(O["R"])),
          not any(m in green for m in must) and len(red) >= 8, red[:8])
    check("NEGATIVE: the old loss_piles has no owner's use", not O["has_owner_use"])

print("WALK_S430 %s -- %d of %d %s" % ("GREEN" if not fails else "RED", (n - len(fails)) if not fails else len(fails), n, "passed" if not fails else "failed"))
for f in fails:
    print("   red: " + f)
sys.exit(0 if not fails else 1)
