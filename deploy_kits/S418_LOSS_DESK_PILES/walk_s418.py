#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s418.py -- kit S418_LOSS_DESK_PILES. THE REAL finance_app.py (a copy of /root/finance carrying the kit's
files) over a SCRATCH COPY of the live finance.db, driven through Flask's test client with header identity (walk
only). The round is the real round 1; its own crafted lines are keyed W418* and every line is found BY KEY (the
item name), never by counting. The SAME scenario is then run against the box as it is (--old) on its own scratch
copy: it must go red (the negative control).

  --app NEW   a copy of /root/finance with the kit's files
  --old OLD   a copy of /root/finance as the box is
  --db PATH   the scratch copy (PATH.old is made for the old app)

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
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
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


CRAFT = (  # item, packing, pack, marg, counted, MRP per unit (paise)
    ("W418 PARKED TAB", "1*10", 10, 40, 10, 1000),        # parked -> With me; Accept back
    ("W418 SMALL TAB", "1*10", 10, 20, 15, 500),          # Rs 25 short -> Write off, small real gap
    ("W418 BIG TAB", "1*10", 10, 30, 0, 10000),           # Rs 3,000 short -> Pursue
    ("W418 RECOUNT TAB", "1*10", 10, 100, 20, 200),       # 80 short (>= 50) -> Recount; Darpan counts 95
    ("W418 GLOVE", "1*1", 1, 50, 40, 1500),               # a consumable -> Write off, clinic consumption
    ("W418 KNEE BRACE M", "1*1", 1, 5, 2, 50000),         # an orthotic -> never on this desk
    ("W418 DIAL TAB", "1*10", 10, 50, 41, None),          # sells 40 strips a year at Rs 20 a strip: allowance 8 (wide), 10 (very wide); 9 short
)


def _fill(c, table, row):
    """INSERT with the given columns; any other NOT NULL column without a default gets '' or 0 by its type."""
    for cid_, name, typ, notnull, dflt, pk in c.execute("PRAGMA table_info(%s)" % table).fetchall():
        if notnull and dflt is None and not pk and name not in row:
            row[name] = 0 if "INT" in (typ or "").upper() or "REAL" in (typ or "").upper() else ""
    c.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ",".join(row), ",".join("?" * len(row))), tuple(row.values()))


def craft(db):
    c = sqlite3.connect(db, timeout=30)
    as_on = c.execute("SELECT marg_as_on FROM stock_count WHERE id=1").fetchone()[0]
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    for it, packing, ps, marg, cnt, mrp in CRAFT:
        c.execute("INSERT OR REPLACE INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,'walk W418')",
                  (as_on, it, marg, packing, ps, now))
        c.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, strips, loose, counted_by, entered_by, at) "
                  "VALUES (1,?,?,?,?,?,0,0,'W418','W418',?)", (it, packing, ps, marg, cnt, now))
        c.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, pack_size, value_p, cause, status, counted_by) "
                  "VALUES (1,?,?,?,?,?,?,NULL,'UNEXPLAINED','open','W418')", (it, as_on, marg, cnt, cnt - marg, ps))
        if mrp is not None:
            c.execute("INSERT OR REPLACE INTO stock_mrp_manual (item, mrp_p, source, set_by, set_at) VALUES (?,?,'walk W418','W418',?)", (it, mrp, now))
    _fill(c, "sale_line_item", dict(unit="medical", item_key="W418 DIAL TAB", qty_raw="40:0", business_date="2026-08-15", pack="1*10",
                                    is_return=0, amount_p=2000, bill_no="W418-1"))
    c.commit()
    c.close()


DB_OLD = a.db + ".old"
copydb(a.db, DB_OLD)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s418  # noqa: E402
assert seed_s418.seed(a.db, a.app) == 0, "seed failed"
craft(a.db)
craft(DB_OLD)
print("-- scratch seeded (the desk's settings), crafted W418 lines on both scratch copies; old-app copy %s" % os.path.basename(DB_OLD))

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, hashlib, inspect
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
    return None
S = {}

# ---------------------------------------------------------------- 0 the gates
def s0():
    for u in ("bhati", "darpan", "shavez"):
        codes = [G(u, "/finance/stock/page/loss?count=1")[0], G(u, "/finance/stock/api/loss/1/piles")[0],
                 P(u, "/finance/stock/api/loss/1/pile/move", {"item": "W418 SMALL TAB", "pile": "pursue"})[0],
                 P(u, "/finance/stock/api/loss/1/pile/writeoff", {})[0], G(u, "/finance/stock/api/loss/1/record.pdf")[0],
                 P(u, "/finance/stock/api/loss/1/pile/accept", {"items": ["W418 PARKED TAB"]})[0]]
        C("%s is refused on the desk -- page, piles, move, write-off, record, accept (%s)" % (u, codes), all(x in (401, 403, 302) for x in codes) and codes[1] != 404, codes)
    C("the owner opens the desk page (200) and it is the four-pile page", G("manoj", "/finance/stock/page/loss?count=1")[0] == 200 and b"Write off this pile" in G("manoj", "/finance/stock/page/loss?count=1")[1])
step("gates", s0)

# ---------------------------------------------------------------- 1 the piles as they stand, THE five totals
def s1():
    D = piles(); S["D0"] = D
    C("the piles answer for count 1", bool(D), None if D else G("manoj", "/finance/stock/api/loss/1/piles")[0])
    wh = where(D)
    C("every line sits in exactly one place (pile, back, written off or over)", all(len(v) == 1 for v in wh.values()), [k for k, v in wh.items() if len(v) > 1][:5])
    secs = {r["item"]: r["section"] for r in q("SELECT item, section FROM stock_item_section")}
    orth = [i for i in wh if secs.get(i) == "Orthotics" or stock_app._is_orthotic(i)]
    C("no orthotic line on the desk (W418 KNEE BRACE M and the S404 section's lines are absent)", not orth and "W418 KNEE BRACE M" not in wh, orth[:5])
    C("the orthotic lines are counted as 'elsewhere'", D["orthotics_elsewhere"] > 0, D["orthotics_elsewhere"])
    wm = [l["item"] for l in [p for p in D["piles"] if p["key"] == "with_me"][0]["lines"]]
    C("With me: the three named items are the first three lines (ETOZOX 90, HYORTH XL, DOLOGESIC SP)", wm[:3] == ["ETOZOX 90", "HYORTH XL", "DOLOGESIC SP"], wm[:5])
    C("INTACOXIA-60 (+719) starts in Recount", wh.get("INTACOXIA-60") == ["recount"], wh.get("INTACOXIA-60"))
    exp = {"W418 PARKED TAB": None, "W418 SMALL TAB": "writeoff", "W418 BIG TAB": "pursue", "W418 RECOUNT TAB": "recount", "W418 GLOVE": "writeoff"}
    got = {k: (wh.get(k) or [None])[0] for k in exp}
    C("the crafted lines start in their piles (small gap -> write off, Rs 3,000 -> pursue, 80 short -> recount, glove -> write off)",
      all(got[k] == v for k, v in exp.items() if v), got)
    C("the glove is the clinic-consumption group, the small tab the small-gap group",
      (line(D, "W418 GLOVE") or {}).get("group") == "consume" and (line(D, "W418 SMALL TAB") or {}).get("group") == "small",
      [(line(D, "W418 GLOVE") or {}).get("group"), (line(D, "W418 SMALL TAB") or {}).get("group")])
    T = D["totals"]
    four = ("with_me", "writeoff", "pursue", "recount")
    C("open = with me + write-off pile + pursue + recount (lines and rupees)", T["open"]["n"] == sum(T[k]["n"] for k in four) and T["open"]["mrp_p"] == sum(T[k]["mrp_p"] for k in four), [T["open"], [T[k]["mrp_p"] for k in four]])
    C("short = open + back + written off", T["short"]["mrp_p"] == T["open"]["mrp_p"] + T["back"]["mrp_p"] + T["written_off"]["mrp_p"] and T["short"]["n"] == T["open"]["n"] + T["back"]["n"] + T["written_off"]["n"], T["short"])
    tot = sum((l["mrp_p"] or 0) for p in D["piles"] for l in p["lines"])
    C("the open figure is the sum of the lines shown", tot == T["open"]["mrp_p"], [tot, T["open"]["mrp_p"]])
    hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]
    hd = {k: v for k, v in (hub.get("desk") or {}).items() if k != "ok"}
    C("F-641: the hub's status card carries THE SAME five totals as the desk", hd == T, [hd.get("open"), T["open"]])
    rep = G("manoj", "/finance/stock/api/pad/report/1")[1]
    rd = {k: v for k, v in (rep.get("desk") or {}).items() if k != "ok"}
    C("the report carries the same five totals", rd == T, rd.get("open"))
    C("the hub still carries S404's orthotic section and the vouchers", "ortho" in hub and "vouchers" in hub and "match" in hub)
    hp = G("manoj", "/finance/stock/page/hub?count=1")[1]
    C("the hub page: a status card; 'cut the next list', 'type Darpan's answers' and the Decision desk are off its steps",
      b"deskCard(d.desk" in hp and b"Cut the next medicines list" not in hp and b"Type Darpan" not in hp and b">Decision desk<" not in hp)
    st = {s["key"]: s["value"] for s in D["settings"]}
    C("the settings are on the desk, seeded: allowance wide (2), floor Rs 1,000, recount 50, 6 a voucher, accept back by the owner, consumables on",
      st.get("stock.allowance_scale") == "2" and st.get("stock.pursue_floor_p") == "100000" and st.get("stock.recount_trigger") == "50"
      and st.get("stock.voucher_batch") == "6" and st.get("stock.accept_back_by") == "owner" and st.get("stock.consume_auto") == "1"
      and st.get("stock.rolling_section_items") == "90" and st.get("stock.rolling_day") == "Monday", st)
step("piles", s1)

# ---------------------------------------------------------------- 2 the -> pile menu
def s2():
    w0, d0 = nrows("stock_diff_lane"), nrows("stock_diff_decision")
    r = P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W418 SMALL TAB", "pile": "pursue"})
    D = piles()
    l = line(D, "W418 SMALL TAB")
    mv = q("SELECT pile, by_user FROM stock_pile_move WHERE count_id=1 AND item='W418 SMALL TAB' ORDER BY id DESC LIMIT 1")
    au = q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_pile' AND action='move' AND after_json LIKE '%W418 SMALL TAB%'")[0]["n"]
    C("the -> pile menu moves a line (W418 SMALL TAB -> Pursue) and records it (move row + audit)", r[0] == 200 and where(D).get("W418 SMALL TAB") == ["pursue"] and l.get("moved") and mv and mv[0]["pile"] == "pursue" and mv[0]["by_user"] == "manoj" and au == 1, [r, mv, au])
    C("a move decides nothing (no lane word, no decision written)", nrows("stock_diff_lane") == w0 and nrows("stock_diff_decision") == d0)
    r = P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W418 SMALL TAB", "pile": "auto"})
    C("back to the system's choice -> the write-off pile again", r[0] == 200 and where(piles()).get("W418 SMALL TAB") == ["writeoff"], r)
    r = P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W418 KNEE BRACE M", "pile": "writeoff"})
    C("an orthotic line cannot be moved onto the desk", r[0] == 400, r)
step("move", s2)

# ---------------------------------------------------------------- 3 Accept back
def s3():
    r = P("manoj", "/finance/stock/api/pad/decide", {"count_id": 1, "items": ["W418 PARKED TAB"], "action": "PARKED"})
    D = piles(); T0 = D["totals"]
    C("a parked line (W418 PARKED TAB) sits in With me", r[0] == 200 and where(D).get("W418 PARKED TAB") == ["with_me"], where(D).get("W418 PARKED TAB"))
    v = line(D, "W418 PARKED TAB")["mrp_p"]
    r = P("manoj", "/finance/stock/api/loss/1/pile/accept", {"items": ["W418 PARKED TAB"]})
    D1 = piles(); T1 = D1["totals"]
    did = q("SELECT id FROM stock_diff WHERE count_id=1 AND item='W418 PARKED TAB'")[0]["id"]
    sd = q("SELECT cause, cause_by, status FROM stock_diff WHERE id=?", did)[0]
    dec = q("SELECT decision, decided_by FROM stock_diff_decision WHERE diff_id=? ORDER BY id DESC LIMIT 1", did)
    fx = q("SELECT qty, source FROM stock_shelf_fix WHERE count_id=1 AND item='W418 PARKED TAB' ORDER BY id DESC LIMIT 1")
    au = q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_pile' AND action='accept_back' AND after_json LIKE '%W418 PARKED TAB%'")[0]["n"]
    ln = line(D1, "W418 PARKED TAB")
    C("Accept back: EXPLAINED (lane word + decision), cause FOUND, status closed", r[0] == 200 and W()["W418 PARKED TAB"]["action"] == "EXPLAINED" and dec and dec[0]["decision"] == "EXPLAINED" and sd["cause"] == "FOUND" and sd["status"] == "closed", [r, sd, dec])
    C("Accept back: the shelf figure is Marg's (40) and the line reads back in store, nothing short", fx and fx[0]["qty"] == 40 and fx[0]["source"] == "accept_back" and ln and ln["counted"] == ln["marg"] == 40 and ln["diff"] == 0 and where(D1).get("W418 PARKED TAB") == ["back"], [fx, ln and [ln["counted"], ln["diff"]]])
    C("Accept back is audited", au == 1, au)
    C("the totals move by exactly its value: open -Rs 300, back +Rs 300", v == 30000 and T1["open"]["mrp_p"] == T0["open"]["mrp_p"] - 30000 and T1["back"]["mrp_p"] == T0["back"]["mrp_p"] + 30000 and T1["short"]["mrp_p"] == T0["short"]["mrp_p"], [v, T0["open"]["mrp_p"], T1["open"]["mrp_p"]])
    pend = [p["item"] for p in stock_app._voucher_pending(db, stock_app._pad_report_data(db, 1))]
    C("an accepted line puts nothing on Marg's vouchers (Marg was right)", "W418 PARKED TAB" not in pend)
    n0 = nrows("stock_diff_lane")
    r = P("manoj", "/finance/stock/api/loss/1/pile/accept", {"items": ["W418 PARKED TAB"]})
    C("a second Accept back writes nothing", r[0] == 200 and r[1]["accepted"] == 0 and nrows("stock_diff_lane") == n0, r)
    r = P("manoj", "/finance/stock/api/loss/1/pile/accept", {"items": ["W418 BIG TAB"]})
    C("Accept back refuses a line that is not in With me (writes nothing)", r[1]["accepted"] == 0 and nrows("stock_diff_lane") == n0, r)
    rep = G("manoj", "/finance/stock/api/pad/report/1")[1]
    C("the count's seal is untouched by the layer (the report still reads the count's own figures underneath)",
      q("SELECT counted_qty FROM stock_diff WHERE id=?", did)[0]["counted_qty"] == 10)
step("accept", s3)

# ---------------------------------------------------------------- 4 the allowance dial
def s4():
    D = piles(); pv = {p["scale"]: p for p in D["preview"]}
    before = {i: v[0] for i, v in where(D).items()}
    grp = lambda X: {l["item"] for p in X["piles"] if p["key"] == "writeoff" for l in p["lines"] if l["group"] == "allowance"}
    a0 = grp(D)
    val = {l["item"]: (l["mrp_p"] or 0) for p in D["piles"] for l in p["lines"]}
    # a crafted line that only the widest dial takes into the allowance: W418 DIAL TAB sells 400 units a year
    target = "3" if not pv["3"]["current"] else "1"
    w0, d0 = nrows("stock_diff_lane"), nrows("stock_diff_decision")
    r = P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.allowance_scale", "value": target})
    D2 = piles(); after = {i: v[0] for i, v in where(D2).items()}
    a1 = grp(D2)
    into, out = a1 - a0, a0 - a1
    pin = [i for i in after if after[i] == "writeoff" and before.get(i) != "writeoff"]
    pout = [i for i in after if after[i] != "writeoff" and before.get(i) == "writeoff"]
    C("the dial's preview counts right: %s would move %d lines within the allowance (%d out), %d into / %d out of the pile -- and moving it does exactly that"
      % (pv[target]["name"], pv[target]["into_n"], pv[target]["out_n"], pv[target]["pile_in_n"], pv[target]["pile_out_n"]),
      r[0] == 200 and len(into) == pv[target]["into_n"] and len(out) == pv[target]["out_n"] and sum(val.get(i, 0) for i in into) == pv[target]["into_p"]
      and len(pin) == pv[target]["pile_in_n"] and len(pout) == pv[target]["pile_out_n"] and len(a1) == pv[target]["allowance_n"],
      [len(into), len(out), len(pin), len(pout), pv[target]])
    C("the crafted W418 DIAL TAB moves between 'small real gap' (wide) and 'within the allowance' (very wide)",
      ("W418 DIAL TAB" in (a1 if target == "3" else a0)) and ("W418 DIAL TAB" not in (a0 if target == "3" else a1)), [target, "W418 DIAL TAB" in a0, "W418 DIAL TAB" in a1])
    C("moving the dial decides nothing (no lane word, no decision)", nrows("stock_diff_lane") == w0 and nrows("stock_diff_decision") == d0)
    lg = q("SELECT before_json, after_json, by_whom FROM audit_log WHERE table_name='setting' AND action='stock_setting' ORDER BY id DESC LIMIT 1")
    C("the change is audited old -> new, by the owner, and listed in the record", lg and json.loads(lg[0]["after_json"])["value"] == target and json.loads(lg[0]["before_json"])["value"] == "2" and lg[0]["by_whom"] == "manoj"
      and any(x["new"] == target and x["by"] == "manoj" for x in D2["record"]["settings_log"]), lg)
    r = P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.allowance_scale", "value": "2"})
    C("back to wide: the piles are as they were", r[0] == 200 and {i: v[0] for i, v in where(piles()).items()} == before)
    r = P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.pursue_floor_p", "value": "abc"})
    C("a bad setting value is refused", r[0] == 400, r)
step("dial", s4)

# ---------------------------------------------------------------- 5 Write off this pile
def s5():
    D = piles()
    pile = sorted(l["item"] for l in [p for p in D["piles"] if p["key"] == "writeoff"][0]["lines"])
    outside = sorted(i for i, v in where(D).items() if v[0] in ("with_me", "pursue", "recount", "over"))
    w0 = W()
    r = P("manoj", "/finance/stock/api/loss/1/pile/writeoff", {"token": "nope"})
    C("a confirm with no arm is refused", r[0] == 400, r)
    r = P("manoj", "/finance/stock/api/loss/1/pile/writeoff", {})
    tok = (r[1] or {}).get("arm", {}).get("token")
    C("the first tap arms: the pile's %d lines, a 10-second confirm" % len(pile), r[0] == 200 and r[1]["arm"]["n"] == len(pile) and r[1]["arm"]["seconds"] == 10, r[1])
    db.execute("UPDATE stock_pile_arm SET at=? WHERE token=?", ((dt.datetime.now() - dt.timedelta(seconds=11)).replace(microsecond=0).isoformat(), tok)); db.commit()
    r = P("manoj", "/finance/stock/api/loss/1/pile/writeoff", {"token": tok})
    C("the 10-second gate: a confirm after 11 s is refused and writes nothing", r[0] == 409 and W() == w0, r)
    r = P("manoj", "/finance/stock/api/loss/1/pile/writeoff", {})
    tok = r[1]["arm"]["token"]
    P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W418 SMALL TAB", "pile": "pursue"})
    r = P("manoj", "/finance/stock/api/loss/1/pile/writeoff", {"token": tok})
    C("a pile that changed after the tap is refused (writes nothing)", r[0] == 409 and W() == w0, r)
    P("manoj", "/finance/stock/api/loss/1/pile/move", {"item": "W418 SMALL TAB", "pile": "auto"})
    rn0 = q("SELECT COALESCE(MAX(round_no),0) AS m FROM stock_voucher_line WHERE count_id=1")[0]["m"]
    r = P("manoj", "/finance/stock/api/loss/1/pile/writeoff", {})
    tok = r[1]["arm"]["token"]
    r = P("manoj", "/finance/stock/api/loss/1/pile/writeoff", {"token": tok})
    w1 = W()
    wrote = sorted(i for i in w1 if w1[i]["action"] == "WRITE_OFF" and (i not in w0 or w0[i] != w1[i]))
    C("Write off this pile: every line of the pile -> WRITE_OFF (%d), and nothing else" % len(pile), r[0] == 200 and wrote == pile, [r[1], len(wrote), len(pile), sorted(set(wrote) ^ set(pile))[:5]])
    C("no line outside the pile was touched (with me / pursue / recount / over)", all(w1.get(i) == w0.get(i) for i in outside), [i for i in outside if w1.get(i) != w0.get(i)][:5])
    ids = [x["id"] for x in q("SELECT id FROM stock_diff WHERE count_id=1 AND item IN (%s)" % ",".join("?" * len(pile)), *pile)]
    st = q("SELECT DISTINCT status FROM stock_diff WHERE id IN (%s)" % ",".join("?" * len(ids)), *ids)
    dc = q("SELECT diff_id, decision FROM stock_diff_decision WHERE diff_id IN (%s) AND id IN (SELECT MAX(id) FROM stock_diff_decision GROUP BY diff_id)" % ",".join("?" * len(ids)), *ids)
    C("each written-off line carries the WRITE_OFF decision and is closed", [s["status"] for s in st] == ["closed"] and len(dc) == len(ids) and all(d["decision"] == "WRITE_OFF" for d in dc), [st, len(dc), len(ids)])
    rno = (r[1].get("done") or {}).get("round_no")
    vl = q("SELECT item, kind, batch_no, made_by FROM stock_voucher_line WHERE count_id=1 AND round_no=?", rno)
    per = {}
    for x in vl:
        per[(x["kind"], x["batch_no"])] = per.get((x["kind"], x["batch_no"]), 0) + 1
    C("Amir's vouchers made in the same call: a new round, exactly the pile's lines, at most 6 a voucher", rno and rno == rn0 + 1 and sorted({x["item"] for x in vl}) == pile and max(per.values()) <= 6 and {x["made_by"] for x in vl} == {"manoj"},
      [rno, len(vl), max(per.values()) if per else None])
    am = G("amir", "/finance/stock/api/pad/amir/1")[1]
    C("the round is on Amir's board", any(x["round_no"] == rno for x in am["made"]["rounds"]), [x["round_no"] for x in am["made"]["rounds"]])
    run = q("SELECT groups, settings, round_no, lines_n FROM stock_writeoff_run WHERE count_id=1 ORDER BY id DESC LIMIT 1")
    g = json.loads(run[0]["groups"]) if run else {}
    C("the write-off is documented: frozen groups (small gap with W418 SMALL TAB, consumption with W418 GLOVE), the rules in force, the round",
      run and "W418 SMALL TAB" in [x["item"] for x in g.get("small", [])] and "W418 GLOVE" in [x["item"] for x in g.get("consume", [])] and json.loads(run[0]["settings"])["allowance_scale"] == 2.0 and run[0]["round_no"] == rno and run[0]["lines_n"] == len(pile),
      {k: len(v) for k, v in g.items()})
    n0, r0 = nrows("stock_diff_lane"), nrows("stock_voucher_line")
    r2 = P("manoj", "/finance/stock/api/loss/1/pile/writeoff", {"token": tok})
    C("a repeat does nothing twice (same token: no word, no voucher)", r2[0] == 200 and nrows("stock_diff_lane") == n0 and nrows("stock_voucher_line") == r0, r2)
    r3 = P("manoj", "/finance/stock/api/loss/1/pile/writeoff", {})
    C("the pile is empty now: a new tap is refused", r3[0] == 400, r3)
    D2 = piles()
    rec = {g_["key"]: g_ for g_ in D2["record"]["groups"]}
    C("the record lists the groups item by item with counts and totals", "small" in rec and "consume" in rec and any(l["item"] == "W418 SMALL TAB" for l in rec["small"]["lines"]) and rec["small"]["n"] == len(rec["small"]["lines"]),
      {k: [v["n"], v["mrp_p"]] for k, v in rec.items()})
    hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]
    C("the hub's card reads the same written-off groups", hub["desk"]["written_off"]["groups"] == D2["totals"]["written_off"]["groups"])
step("writeoff", s5)

# ---------------------------------------------------------------- 6 Pursue -- the sheet for Darpan (S228, unchanged)
def s6():
    D = piles()
    want = sorted(l["item"] for l in [p for p in D["piles"] if p["key"] == "pursue"][0]["lines"] if not l.get("sent"))
    r = P("manoj", "/finance/stock/api/loss/1/pile/pursue", {})
    sh = q("SELECT id, no, lines, md5, total_p FROM stock_loss_share WHERE count_id=1 ORDER BY id DESC LIMIT 1")
    items = sorted(l["item"] for l in json.loads(sh[0]["lines"])) if sh else []
    C("Make the sheet for Darpan: the S228 sheet, exactly the Pursue lines not yet on one (%d, W418 BIG TAB among them)" % len(want), r[0] == 200 and items == want and "W418 BIG TAB" in items, [r[1] and r[1].get("message"), len(items)])
    C("S227/D389 hold: the frozen JSON's md5 is the sheet's fingerprint", sh and hashlib.md5(sh[0]["lines"].encode("utf-8")).hexdigest() == sh[0]["md5"])
    pdf = G("manoj", "/finance/stock/api/loss/share/%d.pdf" % sh[0]["id"])
    C("the sheet's PDF (A4, kept)", pdf[0] == 200 and bytes(pdf[1])[:4] == b"%PDF")
    w = W()
    C("the Pursue lines carry RECOVER and stay OPEN", all(w[i]["action"] == "RECOVER" for i in want) and q("SELECT status FROM stock_diff WHERE count_id=1 AND item='W418 BIG TAB'")[0]["status"] == "open")
    r2 = P("manoj", "/finance/stock/api/loss/1/pile/pursue", {})
    C("a second tap: every line is already on a sheet -- refused, no second sheet", r2[0] == 400 and q("SELECT COUNT(*) AS n FROM stock_loss_share WHERE count_id=1")[0]["n"] == 1, r2)
    lb = G("manoj", "/finance/stock/api/loss/1")
    C("the S228 board still answers and lists the sheet", lb[0] == 200 and any(s["no"] == sh[0]["no"] for s in lb[1]["shares"]))
    rc = P("manoj", "/finance/stock/api/loss/1/recovery", {"share_id": sh[0]["id"], "item": "W418 BIG TAB", "kind": "FOUND", "units": 5})
    C("the S228 recovery door still works on it", rc[0] == 200, rc[0])
    cl = q("SELECT id, state FROM claim_line WHERE count_id=1 AND item='W418 BIG TAB'")
    C("a claim is raised for it at once (the claim queue follows the word)", cl and cl[0]["state"] == "open", cl)
    stt = G("darpan", "/finance/stockmatch/api/state?count=1")[1]
    mine = [x for x in stt.get("claims", []) if x["item"] == "W418 BIG TAB"]
    C("Darpan's Stock milaan carries it under 'Bina bill?'", bool(mine), [x["item"] for x in stt.get("claims", [])][:6])
    ra = P("darpan", "/finance/stockmatch/api/claim?count=1", {"id": mine[0]["id"] if mine else 0, "answer": "not_known"})
    cl = q("SELECT state, answer, contacted_by FROM claim_line WHERE count_id=1 AND item='W418 BIG TAB'")
    C("his answer lands in the claim queue (open -> contacted), audited", ra[0] == 200 and cl[0]["state"] == "contacted" and cl[0]["answer"] == "not_known" and cl[0]["contacted_by"] == "darpan"
      and q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='claim_line' AND action='claim_answered' AND by_whom='darpan'")[0]["n"] >= 1, [ra[0], cl])
    l = line(piles(), "W418 BIG TAB")
    C("the desk shows the line on sheet N with Darpan's answer, still in Pursue", l and l["bucket"] == "pursue" and l["sent"] and l.get("claim", {}).get("answer"), l and [l["bucket"], l.get("sent"), l.get("claim")])
    C("bhati cannot answer on Stock milaan", P("bhati", "/finance/stockmatch/api/claim?count=1", {"id": 1, "answer": "found"})[0] in (401, 403, 302))
step("pursue", s6)

# ---------------------------------------------------------------- 7 Recount -- Darpan's 'Phir se gino'
def s7():
    D = piles()
    rc = sorted(l["item"] for l in [p for p in D["piles"] if p["key"] == "recount"][0]["lines"])
    r = P("manoj", "/finance/stock/api/loss/1/pile/recount", {})
    asked = sorted(x["item"] for x in q("SELECT item FROM stock_recount_ask WHERE count_id=1"))
    C("Ask Darpan to recount: every Recount line is asked (%d, W418 RECOUNT TAB and INTACOXIA-60 among them)" % len(rc), r[0] == 200 and asked == rc and "W418 RECOUNT TAB" in asked and "INTACOXIA-60" in asked, [r[1], len(asked)])
    stt = G("darpan", "/finance/stockmatch/api/state?count=1")
    rl = {x["item"]: x for x in stt[1].get("recounts", [])}
    C("the items appear on Darpan's Stock milaan as Phir se gino, blind (no Marg figure, no first count)", stt[0] == 200 and set(rc) <= set(rl) and not any(k in rl["W418 RECOUNT TAB"] for k in ("marg", "counted", "diff")), sorted(rl)[:5])
    pg = G("darpan", "/finance/stockmatch")
    C("his page carries the card", pg[0] == 200 and b"Phir se gino" in (pg[1] if isinstance(pg[1], bytes) else b""))
    r = P("darpan", "/finance/stockmatch/api/recount?count=1", {"item": "W418 RECOUNT TAB", "strips": 9, "loose": 5})
    fx = q("SELECT qty, source, by_user FROM stock_shelf_fix WHERE count_id=1 AND item='W418 RECOUNT TAB' ORDER BY id DESC LIMIT 1")
    C("his figure lands (9 strips 5 = 95 units), audited", r[0] == 200 and fx and fx[0]["qty"] == 95 and fx[0]["source"] == "recount" and fx[0]["by_user"] == "darpan"
      and q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_pile' AND action='recount' AND after_json LIKE '%W418 RECOUNT TAB%'")[0]["n"] == 1, [r[0], fx])
    D2 = piles(); l = line(D2, "W418 RECOUNT TAB")
    C("his figure replaces the shelf and the line re-piles itself: 5 short, Rs 10 -> Write off, small real gap", l and l["counted"] == 95 and l["diff"] == -5 and l["bucket"] == "writeoff" and l["group"] == "small" and l["mrp_p"] == 1000, l and [l["counted"], l["diff"], l["bucket"], l["group"], l["mrp_p"]])
    r = P("darpan", "/finance/stockmatch/api/recount?count=1", {"item": "W418 RECOUNT TAB", "strips": 9, "loose": 5})
    C("the same figure again writes nothing", r[0] == 200 and q("SELECT COUNT(*) AS n FROM stock_shelf_fix WHERE item='W418 RECOUNT TAB'")[0]["n"] == 1)
    C("bhati / shavez cannot recount", all(P(u, "/finance/stockmatch/api/recount?count=1", {"item": "W418 RECOUNT TAB", "units": 1})[0] in (401, 403, 302) for u in ("bhati", "shavez")))
    C("an item not asked is refused", P("darpan", "/finance/stockmatch/api/recount?count=1", {"item": "W418 BIG TAB", "units": 1})[0] == 404)
step("recount", s7)

# ---------------------------------------------------------------- 8 the record PDF, the untouched routes
def s8():
    r = G("manoj", "/finance/stock/api/loss/1/record.pdf")
    b = bytes(r[1]) if not isinstance(r[1], dict) else b""
    C("the record PDF: the five totals, the rules, every written-off group item by item", r[0] == 200 and b[:4] == b"%PDF" and b"SMALL REAL GAP" in b and b"W418 SMALL TAB" in b and b"THE RULES IN FORCE" in b and b"EVERY CHANGE OF A RULE" in b, [r[0], len(b)])
    for p in ("/finance/stock/page/diffs", "/finance/stock/page/desk?count=1", "/finance/stock/api/open", "/finance/stock/api/finding/1"):
        C("kept for audit and reading: %s answers" % p, G("manoj", p)[0] in (200, 404), G("manoj", p)[0])
    C("the older doors are kept (cause, decision, decide, the S228 tick and share)", all(hasattr(stock_app, f) for f in ("api_cause", "api_diff_decision", "api_pad_decide", "api_loss_tick", "api_loss_share")))
step("record", s8)

out = dict(mode=os.environ["MODE"], R=R, sig=str(inspect.signature(stock_app._voucher_make)))
print("JSON:" + json.dumps(out))
'''


def run(mode, app, db):
    env = dict(os.environ, APPDIR=app, MODE=mode, FINANCE_DB=db)
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=2400)
    txt = p.stdout.decode("utf-8", "replace")
    js = [l for l in txt.splitlines() if l.startswith("JSON:")]
    if not js:
        print(txt[-4000:])
        return None
    return json.loads(js[-1][5:])


print("-- NEW (the kit's files) on the scratch copy")
N = run("new", a.app, a.db)
if N is None:
    check("the new app's probe ran", False)
else:
    for label, ok, got in N["R"]:
        check(label, ok, got if not ok else None)
    check("the voucher round takes an item filter", "items" in N["sig"], N["sig"])

print("-- NEGATIVE CONTROL: the same scenario on the box as it is (must go red)")
O = run("old", a.old, DB_OLD)
if O is None:
    check("NEGATIVE: the old app's probe ran", False)
else:
    red = [l for l, ok, _g in O["R"] if not ok]
    for l, ok, _g in O["R"]:
        print("   old %s  %s" % ("ok  " if ok else "RED ", l))
    must = ("the piles answer for count 1", "F-641: the hub's status card carries THE SAME five totals as the desk",
            "the owner opens the desk page (200) and it is the four-pile page")
    green = {l for l, ok, _g in O["R"] if ok}
    check("NEGATIVE: the old files go red on the desk (%d of %d checks red), including: no piles, no single figure, no four-pile page" % (len(red), len(O["R"])),
          not any(m in green for m in must) and any(r == must[0] for r in red) and len(red) >= 8, red[:12])
    check("NEGATIVE: the old voucher round has no item filter", "items" not in O["sig"], O["sig"])

print("WALK_S418 %s -- %d of %d %s" % ("GREEN" if not fails else "RED", (n - len(fails)) if not fails else len(fails), n, "passed" if not fails else "failed"))
for f in fails:
    print("   red: " + f)
sys.exit(0 if not fails else 1)
