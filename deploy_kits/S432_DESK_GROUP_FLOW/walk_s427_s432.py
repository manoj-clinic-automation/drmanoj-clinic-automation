#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s427_s432.py -- S427's walk as S430 adjusted it (walk_s427_s430.py, byte-for-byte but this line), re-run by kit S432_DESK_GROUP_FLOW
on the S432 files with NO further adjustment: the desk now reads its pile cache, and every S427 assertion must still hold.
walk_s427_s430.py -- S427's walk, re-run by kit S430_DESK_FIRST_READ with THREE assertions adjusted for what S430 changes (each
named where it stands): (1) an unpriced, never-sold, never-bought crafted item (W427 NOPRICE) is now OLD STOCK in the Write-off pile,
not a Big loss; (2) the settings card carries one more key, stock.old_stock_days; (3) a close's frozen run may carry the groups
'old' and 'owner_use' beside allowance / small / consume / big. Everything else is S427's walk, verbatim.

walk_s427.py -- kit S427_LOSS_DESK_RULINGS. THE REAL finance_app.py (a copy of /root/finance carrying the kit's
files) over a SCRATCH COPY of the live finance.db AND a scratch copy of the spine (SPINE_DB), driven through Flask's
test client with header identity (walk only). The round is the real round 1; its own crafted lines are keyed W427*
and every line is found BY KEY (the item name), never by counting. The SAME scenario is then run against the box as
it is (--old) on its own scratch copies: it must go red (the negative control).

  --app NEW     a copy of /root/finance with the kit's files
  --old OLD     a copy of /root/finance as the box is
  --db PATH     the scratch copy of finance.db (PATH.old is made for the old app)
  --spine PATH  the scratch copy of spine.db (crafted sales are written into it; both apps read it)

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


# item, packing, pack, marg, counted, MRP per tab/pc (paise), spine unit_kind, sales rows [(date, units)]
CRAFT = (
    ("W427 FAST TAB", "1*10", 10, 500, 400, 5000, "LOOSE", [("2026-03-10", 67), ("2026-07-01", 6600)]),      # 100 short = 1.5% of 6667 sold, Rs 5,000 -> Big losses
    ("W427 SLOW TAB", "1*10", 10, 40, 20, 1500, "LOOSE", [("2026-03-10", 10), ("2026-07-01", 20)]),           # 20 short = 4 months of its sales, Rs 300 -> Big losses (slow)
    ("W427 ALLOW TAB", "1*10", 10, 1000, 990, 2000, "LOOSE", [("2026-03-10", 100), ("2026-07-01", 1900)]),    # 10 short = 0.5% of 2000 -> within the allowance
    ("W427 SMALL TAB", "1*10", 10, 100, 70, 2000, "LOOSE", [("2026-03-10", 100), ("2026-07-01", 500)]),       # 30 short = 5%, Rs 600, not slow -> small real gap
    ("W427 SYRUP", "200ML", 1, 6, 4, 15000, "WHOLE", [("2026-03-10", 5), ("2026-07-01", 35)]),                # 2 bottles short, Rs 300 -> small (bottles words)
    ("W427 OVER TAB", "1*10", 10, 10, 60, 1000, "LOOSE", []),                                                  # +50 -> the Over note, never a loss
    ("W427 SOLD TAB", "1*10", 10, 50, 5, 1000, "LOOSE", [("2026-09-10", 12), ("2026-09-15", 8)]),             # 20 sold after the count > 5 counted -> closed by the system
    ("W427 PARKED TAB", "1*10", 10, 40, 10, 1000, "LOOSE", []),                                                # parked -> With me; Accept back
    ("W427 NOPRICE", "1*1", 1, 5, 0, None, "WHOLE", []),                                                       # no price, no sale, no purchase -> S430: OLD STOCK (was Big losses under S427)
    ("W427 KNEE BRACE M", "1*1", 1, 5, 2, 50000, "WHOLE", []),                                                 # an orthotic -> never on this desk
)


def _fill(c, table, row):
    for cid_, name, typ, notnull, dflt, pk in c.execute("PRAGMA table_info(%s)" % table).fetchall():
        if notnull and dflt is None and not pk and name not in row:
            row[name] = 0 if "INT" in (typ or "").upper() or "REAL" in (typ or "").upper() else ""
    c.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ",".join(row), ",".join("?" * len(row))), tuple(row.values()))


def craft(db):
    c = sqlite3.connect(db, timeout=30)
    as_on = c.execute("SELECT marg_as_on FROM stock_count WHERE id=1").fetchone()[0]
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    for it, packing, ps, marg, cnt, mrp, _uk, _sales in CRAFT:
        c.execute("INSERT OR REPLACE INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,'walk W427')",
                  (as_on, it, marg, packing, ps, now))
        c.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, strips, loose, counted_by, entered_by, at) "
                  "VALUES (1,?,?,?,?,?,0,0,'W427','W427',?)", (it, packing, ps, marg, cnt, now))
        c.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, pack_size, value_p, cause, status, counted_by) "
                  "VALUES (1,?,?,?,?,?,?,NULL,'UNEXPLAINED','open','W427')", (it, as_on, marg, cnt, cnt - marg, ps))
        if mrp is not None:
            c.execute("INSERT OR REPLACE INTO stock_mrp_manual (item, mrp_p, source, set_by, set_at) VALUES (?,?,'walk W427','W427',?)", (it, mrp, now))
    c.commit()
    c.close()


def craft_spine(db):
    c = sqlite3.connect(db, timeout=30)
    for n_, (it, packing, ps, marg, cnt, mrp, uk, sales) in enumerate(CRAFT, 1):
        c.execute("INSERT OR REPLACE INTO sp_item (k20, name, packing, unit_kind, first_seen, last_seen) VALUES (?,?,?,?,?,?)",
                  (it[:20].strip(), it, packing, uk, "2026-03-31", "2026-09-26"))
        for i, (day, units) in enumerate(sales, 1):              # one crafted bill per item and day: the key (date, bill, seq) never collides
            c.execute("INSERT OR REPLACE INTO sp_sale_line (date, bill, seq, name20, k20, pack, qty_raw, units, rate_p, batch, expiry) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (day, "W427-%02d-%s" % (n_, day.replace("-", "")), i, it[:20].strip(), it[:20].strip(), packing, "%d:%d" % divmod(units, ps) if ps > 1 else str(units),
                       float(units), int(mrp or 0), "W427", "12/28"))
    c.commit()
    c.close()


DB_OLD = a.db + ".old"
copydb(a.db, DB_OLD)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s427  # noqa: E402
assert seed_s427.seed(a.db, a.app) == 0, "seed failed"
craft(a.db)
craft(DB_OLD)
craft_spine(a.spine)
print("-- scratch seeded (the desk's S427 settings), crafted W427 lines on both scratch copies and in the scratch spine; old-app copy %s" % os.path.basename(DB_OLD))

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, hashlib, re
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
import stock_app
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data()]
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
        C(name + " -- the step ran", False, "%s: %s" % (type(e).__name__, str(e)[:300]))
W = lambda: {r["item"]: r for r in q("SELECT item, action, note, by_user, at FROM stock_diff_lane WHERE count_id=1 AND id IN (SELECT MAX(id) FROM stock_diff_lane WHERE count_id=1 GROUP BY item)")}
nrows = lambda t: q("SELECT COUNT(*) AS n FROM %s" % t)[0]["n"]
def piles():
    r = G("manoj", "/finance/stock/api/loss/1/piles")
    return r[1] if r[0] == 200 and isinstance(r[1], dict) else None
def where(D):
    out = {}
    for p in D["piles"]:
        for l in p["lines"]:
            out.setdefault(l["item"], []).append(p["key"])
    for k in ("back", "written_off"):
        for l in D["done"][k]:
            out.setdefault(l["item"], []).append(k)
    for l in D["over"]:
        out.setdefault(l["item"], []).append("over")
    return out
def line(D, item):
    for p in D["piles"]:
        for l in p["lines"]:
            if l["item"] == item:
                return l
    for k in ("back", "written_off"):
        for l in D["done"][k]:
            if l["item"] == item:
                return l
    for l in D["over"]:
        if l["item"] == item:
            return l
    return None
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
S = {}

# ---------------------------------------------------------------- 0 the gates
def s0():
    for u in ("bhati", "darpan", "shavez"):
        codes = [G(u, "/finance/stock/page/loss?count=1")[0], G(u, "/finance/stock/api/loss/1/piles")[0],
                 P(u, "/finance/stock/api/loss/1/pile/move", {"item": "W427 SMALL TAB", "pile": "bigloss"})[0],
                 P(u, "/finance/stock/api/loss/1/pile/close", {})[0], G(u, "/finance/stock/api/loss/1/record.pdf")[0],
                 P(u, "/finance/stock/api/loss/1/pile/accept", {"items": ["W427 PARKED TAB"]})[0], G(u, "/finance/stock/api/loss/1/items?q=blade")[0]]
        C("%s is refused on the desk -- page, piles, move, close, record, accept, items (%s)" % (u, codes), all(x in (401, 403, 302) for x in codes) and 404 not in codes, codes)
    pg = G("manoj", "/finance/stock/page/loss?count=1")
    C("the owner opens the desk page (200) and it is the S427 page (Close the count, Big losses, Consumption)", pg[0] == 200 and b"Close the count" in pg[1] and b"Big losses" in pg[1] and b"Consumption" in pg[1])
step("gates", s0)

# ---------------------------------------------------------------- 1 the piles as they stand, the totals, the sales test
def s1():
    r = P("manoj", "/finance/stock/api/pad/decide", {"count_id": 1, "items": ["W427 PARKED TAB"], "action": "PARKED"})
    D = piles(); S["D0"] = D
    C("the piles answer with the four new piles (no recount / pursue pile)", bool(D) and [p["key"] for p in D["piles"]] == ["with_me", "writeoff", "bigloss", "consume"], None if not D else [p["key"] for p in D["piles"]])
    wh = where(D)
    C("every line sits in exactly one place (pile, back, written off or over)", all(len(v) == 1 for v in wh.values()), [k for k, v in wh.items() if len(v) > 1][:5])
    secs = {r["item"]: r["section"] for r in q("SELECT item, section FROM stock_item_section")}
    orth = [i for i in wh if secs.get(i) == "Orthotics" or stock_app._is_orthotic(i)]
    C("no orthotic line on the desk (W427 KNEE BRACE M absent); the orthotics are counted as elsewhere", not orth and "W427 KNEE BRACE M" not in wh and D["orthotics_elsewhere"] > 0, orth[:5])
    exp = {"W427 FAST TAB": ("bigloss", "big"), "W427 SLOW TAB": ("bigloss", "big"), "W427 ALLOW TAB": ("writeoff", "allowance"), "W427 SMALL TAB": ("writeoff", "small"),
           "W427 SYRUP": ("writeoff", "small"), "W427 NOPRICE": ("writeoff", "old"), "W427 PARKED TAB": ("with_me", None), "BLADE": ("consume", "consume"), "GLOVES SURGICAL 7": ("consume", "consume")}
    got = {k: ((wh.get(k) or [None])[0], (line(D, k) or {}).get("group")) for k in exp}
    C("classify: a fast seller short 1.5% of its sales (Rs 5,000) -> Big losses; a slow item (4 months of its sales, Rs 300) -> Big losses; 0.5% -> within the allowance; "
      "Rs 600 on a normal seller -> small; a syrup 2 bottles short -> small; no price, no sale, no purchase -> OLD STOCK (S430 adjustment 1); parked -> With me; BLADE and GLOVES -> Consumption",
      all(got[k] == v for k, v in exp.items()), got)
    lf = line(D, "W427 FAST TAB"); ls = line(D, "W427 SLOW TAB"); la = line(D, "W427 ALLOW TAB"); ly = line(D, "W427 SYRUP")
    C("the why of each line reads in strips words with the item's own sales: fast '10 strips short (1.5%)', slow 'months of its own sales', allowance '1 strip -- within the allowance of 2 strips'",
      lf and "1.5%" in lf["why"] and lf["short_text"] == "10 strips" and lf["sold_text"] == "666 strips + 7 tabs" and ls and "slow item" in ls["why"] and la and la["short_text"] == "1 strip" and la["allow_text"] == "2 strips" and "within the allowance" in la["why"],
      [lf and (lf["short_text"], lf["sold_text"], lf["why"][:90]), ls and ls["why"][:60], la and (la["short_text"], la["allow_text"])])
    C("a non-strip item reads in its own word: W427 SYRUP '2 bottles' short", ly and ly["short_text"] == "2 bottles", ly and ly["short_text"])
    C("LEUKOCREPE / LEUKOBAND / G DRESS are never consumption (sold on bills)", all((line(D, i) or {}).get("consumable") is False and (wh.get(i) or [None])[0] != "consume" for i in ("LEUKOCREPE 8 CM", "LEUKOCREPE 10CM*4IN", "LEUKOBAND 4 INCH", "G DRESS 10")),
      {i: wh.get(i) for i in ("LEUKOCREPE 8 CM", "LEUKOCREPE 10CM*4IN", "LEUKOBAND 4 INCH", "G DRESS 10")})
    C("TYRO BR (fast seller, Rs 4,255) and G DRESS 10 (slow) are Big losses; BIO D3 MAX (short under 1% of its sales) is within the allowance",
      wh.get("TYRO BR") == ["bigloss"] and wh.get("G DRESS 10") == ["bigloss"] and (line(D, "BIO D3 MAX") or {}).get("group") == "allowance", [wh.get("TYRO BR"), wh.get("G DRESS 10"), (line(D, "BIO D3 MAX") or {}).get("group")])
    C("a surplus is never a loss: W427 OVER TAB and INTACOXIA-60 sit under the Over note, in strips words", wh.get("W427 OVER TAB") == ["over"] and wh.get("INTACOXIA-60") == ["over"] and (line(D, "W427 OVER TAB") or {}).get("over_text") == "5 strips", [wh.get("W427 OVER TAB"), wh.get("INTACOXIA-60")])
    wm = [l["item"] for l in [p for p in D["piles"] if p["key"] == "with_me"][0]["lines"]]
    C("With me: ETOZOX 90, HYORTH XL and the parked W427 line", "ETOZOX 90" in wm and "HYORTH XL" in wm and "W427 PARKED TAB" in wm, wm[:6])
    # the sales-after-count test
    lt = line(D, "W427 SOLD TAB")
    sd = q("SELECT status, cause FROM stock_diff WHERE count_id=1 AND item='W427 SOLD TAB'")[0]
    fx = q("SELECT qty, source FROM stock_shelf_fix WHERE count_id=1 AND item='W427 SOLD TAB' ORDER BY id DESC LIMIT 1")
    w = W().get("W427 SOLD TAB") or {}
    C("sales-after-count: W427 SOLD TAB (counted 5, sold 20 since) is closed by the system -- EXPLAINED, cause FOUND, closed, shelf = Marg (50), audited 'sold after count'",
      lt and lt["bucket"] == "back" and lt.get("test") and lt["test"]["sold_after"] == 20 and sd["status"] == "closed" and sd["cause"] == "FOUND" and fx and fx[0]["qty"] == 50 and fx[0]["source"] == "sales_test"
      and w.get("action") == "EXPLAINED" and str(w.get("note", "")).startswith("system: sold after count") and q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_pile' AND action='sales_test' AND after_json LIKE '%W427 SOLD TAB%'")[0]["n"] == 1,
      [lt and lt["bucket"], lt and lt.get("test"), sd, fx, w.get("note")])
    C("it is listed under its own heading (sold after the count), with the real DOLOGESIC SP beside it", any(l["item"] == "W427 SOLD TAB" for l in D["sold_after"]) and any(l["item"] == "DOLOGESIC SP" for l in D["sold_after"]), [l["item"] for l in D["sold_after"]][:6])
    piles()
    C("a second read writes the test only once", q("SELECT COUNT(*) AS n FROM stock_sales_test WHERE item='W427 SOLD TAB'")[0]["n"] == 1 and q("SELECT COUNT(*) AS n FROM stock_diff_lane WHERE item='W427 SOLD TAB'")[0]["n"] == 1)
    T = D["totals"]
    four = ("with_me", "writeoff", "bigloss", "consume")
    C("open = with me + write off + big losses + consumption (lines and rupees)", T["open"]["n"] == sum(T[k]["n"] for k in four) and T["open"]["mrp_p"] == sum(T[k]["mrp_p"] for k in four), [T["open"], [T[k]["mrp_p"] for k in four]])
    C("short = open + back + written off", T["short"]["mrp_p"] == T["open"]["mrp_p"] + T["back"]["mrp_p"] + T["written_off"]["mrp_p"] and T["short"]["n"] == T["open"]["n"] + T["back"]["n"] + T["written_off"]["n"], T["short"])
    tot = sum((l["mrp_p"] or 0) for p in D["piles"] for l in p["lines"])
    C("the open figure is the sum of the lines shown", tot == T["open"]["mrp_p"], [tot, T["open"]["mrp_p"]])
    hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]
    hd = {k: v for k, v in (hub.get("desk") or {}).items() if k != "ok"}
    C("the hub's status card carries THE SAME totals as the desk (four new piles)", hd == T and "bigloss" in hd, [hd.get("open"), T["open"]])
    rep = G("manoj", "/finance/stock/api/pad/report/1")[1]
    rd = {k: v for k, v in (rep.get("desk") or {}).items() if k != "ok"}
    C("the report carries the same totals", rd == T, rd.get("open"))
    hp = G("manoj", "/finance/stock/page/hub?count=1")[1]
    C("the hub page: the card names Big losses and Consumption, step 3 speaks of the close; no 'to pursue', no 'recount'", b"Big losses" in hp and b"Consumption" in hp and b"closes the count" in hp and b"to pursue '+K" not in hp and b"recount '+K" not in hp)
    st = {s["key"]: s for s in D["settings"]}
    C("the settings card shows the new keys and none of the removed ones; the big-loss floor inherited Rs 1,000; the consumption list carries BLADE and the gloves",
      set(st) == {"stock.allowance_pct", "stock.allowance_min_strips", "stock.small_gap_ceiling_p", "stock.big_loss_floor_p", "stock.slow_months", "stock.slow_floor_p",
                  "stock.consume_items", "stock.voucher_batch", "stock.accept_back_by", "stock.staff_block_items", "stock.old_stock_days"}   # S430 adjustment 2
      and st["stock.big_loss_floor_p"]["value"] == "100000" and st["stock.allowance_pct"]["shown"] == "1%" and "BLADE" in st["stock.consume_items"]["items"] and "GLOVES SURGICAL 7" in st["stock.consume_items"]["items"],
      [sorted(st), st.get("stock.big_loss_floor_p", {}).get("value")])
    C("the block preview reads as Darpan will see it: 'Ginti <date> · kul kami Rs', the big losses BY NAME in patte", D["block_preview"]["lines_hi"][0].startswith("Ginti 06-09-2026") and "kul kami" in D["block_preview"]["lines_hi"][0]
      and "W427 FAST TAB 10 patte" in D["block_preview"]["lines_hi"][2] and "TYRO BR" in D["block_preview"]["lines_hi"][2], D["block_preview"]["lines_hi"])
    C("stock_app._qw speaks the one nomenclature: 34 of a 10-strip item = '3 strips + 4 tabs'; 12 of a pcs item = '12 pcs'", stock_app._qw(34, 10) == "3 strips + 4 tabs" and stock_app._qw(12, 1) == "12 pcs" and stock_app._qw(30, 10) == "3 strips", [stock_app._qw(34, 10), stock_app._qw(12, 1)])
    import qty_words
    C("qty_words: Hindi forms '3 patte + 4 goli', '12 nag', '2 botal'", qty_words.words(34, "1*10", lang="hi") == "3 patte + 4 goli" and qty_words.words(12, "1*1", lang="hi") == "12 nag" and qty_words.words(2, "200ML", lang="hi") == "2 botal")
step("piles", s1)

# ---------------------------------------------------------------- 2 the -> pile menu
def s2():
    w0, d0 = nrows("stock_diff_lane"), nrows("stock_diff_decision")
    r = P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W427 SMALL TAB", "pile": "bigloss"})
    D = piles(); l = line(D, "W427 SMALL TAB")
    mv = q("SELECT pile, by_user FROM stock_pile_move WHERE count_id=1 AND item='W427 SMALL TAB' ORDER BY id DESC LIMIT 1")
    C("the -> pile menu moves a line (W427 SMALL TAB -> Big losses, group big) and records it", r[0] == 200 and where(D).get("W427 SMALL TAB") == ["bigloss"] and l.get("group") == "big" and l.get("moved") and mv and mv[0]["pile"] == "bigloss", [r, mv])
    C("a move decides nothing (no lane word, no decision written)", nrows("stock_diff_lane") == w0 and nrows("stock_diff_decision") == d0)
    r = P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W427 SMALL TAB", "pile": "auto"})
    C("back to the system's choice -> small real gap again", r[0] == 200 and (line(piles(), "W427 SMALL TAB") or {}).get("group") == "small", r)
    C("an orthotic line cannot be moved onto the desk; 'recount' is not a pile; an over line is never a loss",
      P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W427 KNEE BRACE M", "pile": "writeoff"})[0] == 400
      and P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W427 SMALL TAB", "pile": "recount"})[0] == 400
      and P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W427 OVER TAB", "pile": "bigloss"})[0] == 400)
step("move", s2)

# ---------------------------------------------------------------- 3 Accept back (S418, still holds)
def s3():
    D = piles(); T0 = D["totals"]
    v = line(D, "W427 PARKED TAB")["mrp_p"]
    r = P("manoj", "/finance/stock/api/loss/1/pile/accept", {"items": ["W427 PARKED TAB"]})
    D1 = piles(); T1 = D1["totals"]
    did = q("SELECT id FROM stock_diff WHERE count_id=1 AND item='W427 PARKED TAB'")[0]["id"]
    sd = q("SELECT cause, status FROM stock_diff WHERE id=?", did)[0]
    fx = q("SELECT qty, source FROM stock_shelf_fix WHERE count_id=1 AND item='W427 PARKED TAB' ORDER BY id DESC LIMIT 1")
    ln = line(D1, "W427 PARKED TAB")
    C("Accept back: EXPLAINED, cause FOUND, closed, shelf = Marg's (4 strips), the line reads back in store", r[0] == 200 and W()["W427 PARKED TAB"]["action"] == "EXPLAINED" and sd["cause"] == "FOUND" and sd["status"] == "closed"
      and fx and fx[0]["qty"] == 40 and fx[0]["source"] == "accept_back" and ln and ln["diff"] == 0 and where(D1).get("W427 PARKED TAB") == ["back"], [r, sd, fx])
    C("the totals move by exactly its value: open -Rs 300, back +Rs 300", v == 30000 and T1["open"]["mrp_p"] == T0["open"]["mrp_p"] - 30000 and T1["back"]["mrp_p"] == T0["back"]["mrp_p"] + 30000 and T1["short"]["mrp_p"] == T0["short"]["mrp_p"], [v, T0["open"]["mrp_p"], T1["open"]["mrp_p"]])
    n0 = nrows("stock_diff_lane")
    r = P("manoj", "/finance/stock/api/loss/1/pile/accept", {"items": ["W427 PARKED TAB"]})
    C("a second Accept back writes nothing; a line outside With me is refused", r[0] == 200 and r[1]["accepted"] == 0 and P("manoj", "/finance/stock/api/loss/1/pile/accept", {"items": ["W427 FAST TAB"]})[1]["accepted"] == 0 and nrows("stock_diff_lane") == n0, r)
step("accept", s3)

# ---------------------------------------------------------------- 4 the settings: every threshold a setting
def s4():
    w0, d0 = nrows("stock_diff_lane"), nrows("stock_diff_decision")
    r = P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.allowance_pct", "value": "2"})
    D = piles(); l = line(D, "W427 FAST TAB")
    C("allowance 1% -> 2%: the fast seller (1.5%) moves from Big losses into the allowance; the change decides nothing", r[0] == 200 and l and l["bucket"] == "writeoff" and l["group"] == "allowance" and nrows("stock_diff_lane") == w0 and nrows("stock_diff_decision") == d0, [r, l and (l["bucket"], l["group"])])
    lg = q("SELECT before_json, after_json, by_whom FROM audit_log WHERE table_name='setting' AND action='stock_setting' ORDER BY id DESC LIMIT 1")
    C("the change is audited old -> new, by the owner, and listed in the record", lg and json.loads(lg[0]["after_json"])["value"] == "2" and json.loads(lg[0]["before_json"])["value"] == "1.0" and lg[0]["by_whom"] == "manoj"
      and any(x["new"] == "2" and x["by"] == "manoj" for x in D["record"]["settings_log"]), lg)
    r = P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.allowance_pct", "value": "1.0"})
    C("back to 1%: the fast seller is a big loss again", r[0] == 200 and (line(piles(), "W427 FAST TAB") or {}).get("bucket") == "bigloss")
    C("a bad value and a retired key are refused", P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.big_loss_floor_p", "value": "abc"})[0] == 400
      and P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.recount_trigger", "value": "50"})[0] == 400)
    it = G("manoj", "/finance/stock/api/loss/1/items?q=leukocrepe 8")
    C("the owner's search box finds LEUKOCREPE 8 CM", it[0] == 200 and "LEUKOCREPE 8 CM" in it[1]["items"], it[1])
    r = P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.consume_items", "add": "LEUKOCREPE 8 CM"})
    D = piles()
    C("added to the consumption list -> LEUKOCREPE 8 CM sits in Consumption, audited", r[0] == 200 and where(D).get("LEUKOCREPE 8 CM") == ["consume"] and "LEUKOCREPE 8 CM" in [s for s in D["settings"] if s["key"] == "stock.consume_items"][0]["items"], [r, where(D).get("LEUKOCREPE 8 CM")])
    r = P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.consume_items", "remove": "LEUKOCREPE 8 CM"})
    D = piles()
    C("taken off the list -> back in the stock piles", r[0] == 200 and where(D).get("LEUKOCREPE 8 CM") != ["consume"], where(D).get("LEUKOCREPE 8 CM"))
step("settings", s4)

# ---------------------------------------------------------------- 5 Darpan's own recount -- Dobara ginna hai
def s5():
    C("the S418 'Ask Darpan to recount' door answers 410", P("manoj", "/finance/stock/api/loss/1/pile/recount", {})[0] == 410)
    pg = G("darpan", "/finance/stockmatch")
    C("Stock milaan carries 'Dobara ginna hai' and no 'Phir se gino'", pg[0] == 200 and b"Dobara ginna hai" in pg[1] and b"Phir se gino" not in pg[1])
    it = G("darpan", "/finance/stockmatch/api/items?count=1&q=w427 small")
    C("his search box finds the item with its pack (ek patte mein 10)", it[0] == 200 and any(x["item"] == "W427 SMALL TAB" and x["pack"] == 10 for x in it[1]["items"]), it[1])
    r = P("darpan", "/finance/stockmatch/api/recount?count=1", {"item": "W427 SMALL TAB", "strips": 9, "loose": 5})
    fx = q("SELECT qty, source, by_user FROM stock_shelf_fix WHERE count_id=1 AND item='W427 SMALL TAB' ORDER BY id DESC LIMIT 1")
    C("his figure lands (9 patte + 5 goli = 95), stamped and audited; the message speaks patte / goli", r[0] == 200 and fx and fx[0]["qty"] == 95 and fx[0]["source"] == "recount" and fx[0]["by_user"] == "darpan"
      and "9 patte + 5 goli" in r[1]["saved"]["message"] and q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_pile' AND action='recount' AND after_json LIKE '%W427 SMALL TAB%'")[0]["n"] == 1, [r[0], fx, r[1] and r[1].get("saved")])
    D = piles(); l = line(D, "W427 SMALL TAB")
    C("his figure replaces the shelf and the line re-piles itself: 5 tabs short -> within the allowance", l and l["counted"] == 95 and l["diff"] == -5 and l["bucket"] == "writeoff" and l["group"] == "allowance" and "recounted by darpan" in l["why"], l and [l["counted"], l["diff"], l["bucket"], l["group"]])
    st = G("darpan", "/finance/stockmatch/api/state?count=1")[1]
    C("'Aapne gina' lists it in his words", any(x["item"] == "W427 SMALL TAB" and x["qty_text"] == "9 patte + 5 goli" for x in st.get("recounts", [])), st.get("recounts"))
    r = P("darpan", "/finance/stockmatch/api/recount?count=1", {"item": "W427 SMALL TAB", "strips": 9, "loose": 5})
    C("the same figure again writes nothing", r[0] == 200 and q("SELECT COUNT(*) AS n FROM stock_shelf_fix WHERE item='W427 SMALL TAB'")[0]["n"] == 1)
    C("bhati / shavez cannot recount; an item not of the round is refused", all(P(u, "/finance/stockmatch/api/recount?count=1", {"item": "W427 SMALL TAB", "pcs": 1})[0] in (401, 403, 302) for u in ("bhati", "shavez"))
      and P("darpan", "/finance/stockmatch/api/recount?count=1", {"item": "NOT AN ITEM W427", "pcs": 1})[0] == 404)
    r = P("darpan", "/finance/stockmatch/api/recount?count=1", {"item": "W427 SYRUP", "pcs": 6})
    C("a non-strip item is counted in pcs: W427 SYRUP 6 -> shelf = Marg, the line reads back in store", r[0] == 200 and (line(piles(), "W427 SYRUP") or {}).get("bucket") == "back", r[1] and r[1].get("saved"))
step("recount", s5)

# ---------------------------------------------------------------- 6 Close the count -- and the staff block
def s6():
    D = piles()
    close_items = sorted(l["item"] for p in D["piles"] if p["key"] in ("writeoff", "bigloss", "consume") for l in p["lines"])
    outside = sorted(i for i, v in where(D).items() if v[0] in ("with_me", "over"))
    w0 = W()
    C("the desk's close counts the three piles", D["close"]["n"] == len(close_items) and D["close"]["items"] == close_items, [D["close"]["n"], len(close_items)])
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {"token": "nope"})
    C("a confirm with no arm is refused", r[0] == 400, r)
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {})
    tok = (r[1] or {}).get("arm", {}).get("token")
    C("the first tap arms: %d lines, a 10-second confirm" % len(close_items), r[0] == 200 and r[1]["arm"]["n"] == len(close_items) and r[1]["arm"]["seconds"] == 10, r[1])
    db.execute("UPDATE stock_pile_arm SET at=? WHERE token=?", ((dt.datetime.now() - dt.timedelta(seconds=11)).replace(microsecond=0).isoformat(), tok)); db.commit()
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {"token": tok})
    C("the 10-second gate: a confirm after 11 s is refused and writes nothing", r[0] == 409 and W() == w0, r)
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {}); tok = r[1]["arm"]["token"]
    P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W427 SLOW TAB", "pile": "with_me"})
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {"token": tok})
    C("lines that changed after the tap are refused (writes nothing)", r[0] == 409 and W() == w0, r)
    P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W427 SLOW TAB", "pile": "auto"})
    rn0 = q("SELECT COALESCE(MAX(round_no),0) AS m FROM stock_voucher_line WHERE count_id=1")[0]["m"]
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {}); tok = r[1]["arm"]["token"]
    r = P("manoj", "/finance/stock/api/loss/1/pile/close", {"token": tok})
    w1 = W()
    wrote = sorted(i for i in w1 if w1[i]["action"] == "WRITE_OFF" and (i not in w0 or w0[i] != w1[i]))
    C("Close the count: every line of the three piles -> WRITE_OFF (%d), and nothing else" % len(close_items), r[0] == 200 and wrote == close_items, [r[1] and r[1].get("message"), len(wrote), len(close_items), sorted(set(wrote) ^ set(close_items))[:5]])
    C("no line outside the three piles was touched (with me / over); ETOZOX 90 is still open with you", all(w1.get(i) == w0.get(i) for i in outside) and where(piles()).get("ETOZOX 90") == ["with_me"], [i for i in outside if w1.get(i) != w0.get(i)][:5])
    ids = [x["id"] for x in q("SELECT id FROM stock_diff WHERE count_id=1 AND item IN (%s)" % ",".join("?" * len(close_items)), *close_items)]
    st = q("SELECT DISTINCT status FROM stock_diff WHERE id IN (%s)" % ",".join("?" * len(ids)), *ids)
    C("each written-off line is closed", [s["status"] for s in st] == ["closed"], st)
    rno = (r[1].get("done") or {}).get("round_no")
    vl = q("SELECT item, kind, batch_no FROM stock_voucher_line WHERE count_id=1 AND round_no=?", rno)
    per = {}
    for x in vl:
        per[(x["kind"], x["batch_no"])] = per.get((x["kind"], x["batch_no"]), 0) + 1
    C("Amir's vouchers made in the same call: a new round, exactly those lines, at most 6 a voucher", rno and rno == rn0 + 1 and sorted({x["item"] for x in vl}) == close_items and max(per.values()) <= 6, [rno, len(vl), max(per.values()) if per else None])
    am = G("amir", "/finance/stock/api/pad/amir/1")[1]
    C("the round is on Amir's board", any(x["round_no"] == rno for x in am["made"]["rounds"]), [x["round_no"] for x in am["made"]["rounds"]])
    run = q("SELECT id, groups, settings, round_no, lines_n FROM stock_writeoff_run WHERE count_id=1 ORDER BY id DESC LIMIT 1")
    g = json.loads(run[0]["groups"]) if run else {}
    C("ONE frozen run with the four groups: allowance (W427 ALLOW TAB), small, consumption (BLADE), big (W427 FAST TAB, TYRO BR); the S427 rules inside",
      run and set(g) <= {"allowance", "small", "consume", "big", "old", "owner_use"} and "W427 ALLOW TAB" in [x["item"] for x in g.get("allowance", [])] and "BLADE" in [x["item"] for x in g.get("consume", [])]   # S430 adjustment 3
      and {"W427 FAST TAB", "TYRO BR"} <= {x["item"] for x in g.get("big", [])} and json.loads(run[0]["settings"]).get("allowance_pct") == 1.0 and run[0]["round_no"] == rno and run[0]["lines_n"] == len(close_items),
      {k: len(v) for k, v in g.items()})
    B = q("SELECT * FROM stock_staff_block WHERE count_id=1 ORDER BY id DESC LIMIT 1")
    bl = json.loads(B[0]["big_lines"]) if B else []
    big_p = sum((x["mrp_p"] or 0) for x in g.get("big", [])); small_p = sum((x["mrp_p"] or 0) for k in ("allowance", "small") for x in g.get(k, []))
    C("THE STAFF BLOCK is frozen from the run: total = small + big (consumption apart), the big losses by value, W427 FAST TAB (Rs 5,000) among the first",
      B and B[0]["run_id"] == run[0]["id"] and B[0]["total_p"] == small_p + big_p and B[0]["big_p"] == big_p and B[0]["small_p"] == small_p and bl and bl[0]["mrp_p"] == max(x["mrp_p"] or 0 for x in bl)
      and any(x["item"] == "W427 FAST TAB" for x in bl[:6]), B and [B[0]["total_p"], B[0]["small_p"], B[0]["big_p"], [x["item"] for x in bl[:4]]])
    n0, r0 = nrows("stock_diff_lane"), nrows("stock_voucher_line")
    r2 = P("manoj", "/finance/stock/api/loss/1/pile/close", {"token": tok})
    C("a repeat does nothing twice (same token: no word, no voucher, no second block)", r2[0] == 200 and nrows("stock_diff_lane") == n0 and nrows("stock_voucher_line") == r0 and nrows("stock_staff_block") == 1, r2)
    C("the piles are empty now: a new tap is refused", P("manoj", "/finance/stock/api/loss/1/pile/close", {})[0] == 400)
    D2 = piles()
    C("the desk shows the frozen block in English with 'Big losses --' by name; the record lists the groups", D2["block"] and D2["block"]["lines_en"][0].startswith("Count of 06-09-2026") and "W427 FAST TAB 10 strips" in D2["block"]["lines_en"][2]
      and {gr["key"] for gr in D2["record"]["groups"]} >= {"big", "consume", "allowance"}, D2["block"] and D2["block"]["lines_en"])
    hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]
    C("the hub's card reads the same written-off groups", hub["desk"]["written_off"]["groups"] == D2["totals"]["written_off"]["groups"])
    # Darpan's side
    st = G("darpan", "/finance/stockmatch/api/state?count=1")[1]
    K = st.get("block")
    C("the block is pinned on Stock milaan in Hindi with strips words: 'Ginti 06-09-2026 · kul kami', 'Chhoti kami, likh di gayi', 'Badi kami -- ... W427 FAST TAB 10 patte'",
      K and K["lines_hi"][0].startswith("Ginti 06-09-2026 · kul kami") and K["lines_hi"][1].startswith("Chhoti kami, likh di gayi") and K["lines_hi"][2].startswith("Badi kami") and "W427 FAST TAB 10 patte" in K["lines_hi"][2]
      and "%" not in "".join(K["lines_hi"]), K and K["lines_hi"])
    pg = G("darpan", "/finance/stockmatch")
    C("his page carries the block card and 'Kuchh batana hai?'", pg[0] == 200 and b"Kuchh batana hai" in pg[1] and b"s.block" in pg[1])
    r = P("darpan", "/finance/stockmatch/api/note?count=1", {"text": "Sab theek gina tha, boxes peeche rakhe the"})
    D3 = piles()
    C("his 'Kuchh batana hai?' is stored and shows on the owner's record card", r[0] == 200 and (r[1].get("block") or {}).get("notes") and r[1]["block"]["notes"][0]["by"] == "darpan"
      and any("boxes peeche" in x["text"] for x in D3["block"]["notes"]), r[1] and r[1].get("block", {}).get("notes"))
    C("bhati cannot write under the block; an empty note is refused", P("bhati", "/finance/stockmatch/api/note?count=1", {"text": "x"})[0] in (401, 403, 302) and P("darpan", "/finance/stockmatch/api/note?count=1", {"text": "  "})[0] == 400)
step("close", s6)

# ---------------------------------------------------------------- 7 the record PDF, the word gate, the untouched routes
def s7():
    r = G("manoj", "/finance/stock/api/loss/1/record.pdf")
    b = bytes(r[1]) if not isinstance(r[1], dict) else b""
    C("the record PDF: the totals, the rules, the staff block, the groups item by item, the lines sold after the count", r[0] == 200 and b[:4] == b"%PDF" and b"THE STAFF BLOCK" in b and b"BIG LOSS" in b and b"W427 FAST TAB" in b and b"SOLD AFTER THE COUNT" in b and b"THE RULES IN FORCE" in b, [r[0], len(b)])
    pdf_txt = b.decode("latin-1")
    pages = {"loss": G("manoj", "/finance/stock/page/loss?count=1")[1], "hub": G("manoj", "/finance/stock/page/hub?count=1")[1],
             "stockmatch": G("darpan", "/finance/stockmatch")[1], "amir": G("amir", "/finance/stock/page/amir?count=1")[1]}
    bad = {k: hits([v.decode("utf-8", "replace")]) for k, v in pages.items() if isinstance(v, bytes)}
    C("the word gate -- no 'unit' / 'units' / 'yunit' on the rendered desk, hub, Stock milaan and Amir's board", all(not v for v in bad.values()), {k: v[:3] for k, v in bad.items() if v})
    jsons = {"piles": G("manoj", "/finance/stock/api/loss/1/piles")[1], "stockmatch": G("darpan", "/finance/stockmatch/api/state?count=1")[1],
             "hub": G("manoj", "/finance/stock/api/pad/hub/1")[1], "amir": G("amir", "/finance/stock/api/pad/amir/1")[1]}
    badj = {}
    for k, j in jsons.items():
        acc = []; strings(j, acc); h = hits(acc)
        if h: badj[k] = h[:4]
    C("the word gate -- no 'unit(s)' in any text the desk, Stock milaan, the hub or Amir's board is given to show", not badj, badj)
    C("the word gate -- no 'unit(s)' in the record PDF", not hits([pdf_txt]), hits([pdf_txt])[:3])
    for p in ("/finance/stock/page/diffs", "/finance/stock/page/desk?count=1", "/finance/stock/api/open", "/finance/stock/api/finding/1"):
        C("kept for audit and reading: %s answers" % p, G("manoj", p)[0] in (200, 404), G("manoj", p)[0])
    C("the older doors are kept (cause, decision, decide, the S228 tick and share, the S418 writeoff and accept)", all(hasattr(stock_app, f) for f in ("api_cause", "api_diff_decision", "api_pad_decide", "api_loss_tick", "api_loss_share", "api_loss_pile_writeoff", "api_loss_pile_accept")))
step("record", s7)

out = dict(mode=os.environ["MODE"], R=R, qw=stock_app._qw(34, 10))
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
    check("stock_app._qw speaks the one nomenclature ('3 strips + 4 tabs')", N["qw"] == "3 strips + 4 tabs", N["qw"])

print("-- NEGATIVE CONTROL: the same scenario on the box as it is (must go red)")
O = run("old", a.old, DB_OLD)
if O is None:
    check("NEGATIVE: the old app's probe ran", False)
else:
    red = [l for l, ok, _g in O["R"] if not ok]
    for l, ok, _g in O["R"]:
        print("   old %s  %s" % ("ok  " if ok else "RED ", l))
    must = ("the piles answer with the four new piles (no recount / pursue pile)",
            "the owner opens the desk page (200) and it is the S427 page (Close the count, Big losses, Consumption)",
            "the S418 'Ask Darpan to recount' door answers 410",
            "Stock milaan carries 'Dobara ginna hai' and no 'Phir se gino'")
    green = {l for l, ok, _g in O["R"] if ok}
    check("NEGATIVE: the old files go red (%d of %d checks red), including: the old piles, the old page, recount still pushed, no Dobara ginna hai" % (len(red), len(O["R"])),
          not any(m in green for m in must) and len(red) >= 10, red[:12])
    check("NEGATIVE: the old _qw says '3 strips 4 tabs' (no one nomenclature)", O["qw"] != "3 strips + 4 tabs", O["qw"])

print("WALK_S427 %s -- %d of %d %s" % ("GREEN" if not fails else "RED", (n - len(fails)) if not fails else len(fails), n, "passed" if not fails else "failed"))
for f in fails:
    print("   red: " + f)
sys.exit(0 if not fails else 1)
