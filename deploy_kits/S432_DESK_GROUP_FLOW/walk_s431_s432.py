#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s431_s432.py -- S431's walk re-run by kit S432_DESK_GROUP_FLOW with TWO assertions adjusted (named where they stand) for what S432's
3.4 changes: a Marg-negative line is a book correction (no shortage, no excess, no excess money, never 'unpriced').
walk_s431.py -- kit S431_COUNT_STATEMENT. THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over SCRATCH
copies of the live finance.db and the spine, driven through Flask's test client with header identity (walk only). The round is the
real count #1 (closed by the owner 27-Sep 12:58 IST); its own crafted rows are keyed W431* and found BY KEY. The SAME scenario then
runs against the box as it is (--old): it must go red (no statement route, the decision-desk pointer still on the report).

  --app NEW --old OLD --db PATH --spine PATH
"""
import argparse
import datetime as dt
import json
import os
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


def norm_key(name):
    s = re.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return re.sub(r"\s+", " ", s).strip()


# item, packing, pack, marg, counted, section, stock_rate (paise per unit, None = none), spine facts [(fact, value_per_strip, as_on)]
CRAFT = (
    ("W431 KNEE BRACE L", "1*1", 1, 5, 3, "Orthotics", 70000, []),                                       # no spine fact, a purchase rate -> the 0.30 rule: Rs 1,000 a pc, 2 short = Rs 2,000
    ("W431 MED TAB", "1*10", 10, 30, 10, "Medicines", 900, [("s_rate", "120.0", "2026-09-01"), ("s_rate", "0.0", "2026-09-05"), ("mrp", "150.0", "2026-09-01")]),   # S.RATE 120 a strip (the 0.0 of 05-09 is no price) -> Rs 12 a tab, 20 short = Rs 240
    ("W431 MRP TAB", "1*10", 10, 30, 20, "Medicines", None, [("mrp", "200.0", "2026-08-30"), ("s_rate", "500.0", "2026-09-07")]),   # only MRP as on the count day (the S.RATE of 07-09 came after) -> Rs 20 a tab, 10 short = Rs 200
    ("W431 NOPRICE PC", "1*1", 1, 4, 6, "Medicines", None, []),                                          # nothing prices it: 2 excess, 'no price -- name it'
)


def craft(db):
    c = sqlite3.connect(db, timeout=30)
    as_on = c.execute("SELECT marg_as_on FROM stock_count WHERE id=1").fetchone()[0]
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    for it, packing, ps, marg, cnt, sec, rate, _f in CRAFT:
        c.execute("INSERT OR REPLACE INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,'walk W431')", (as_on, it, marg, packing, ps, now))
        c.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, strips, loose, counted_by, entered_by, at) VALUES (1,?,?,?,?,?,0,0,'W431','W431',?)",
                  (it, packing, ps, marg, cnt, now))
        c.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, pack_size, value_p, cause, status, counted_by) VALUES (1,?,?,?,?,?,?,NULL,'UNEXPLAINED','open','W431')",
                  (it, as_on, marg, cnt, cnt - marg, ps))
        c.execute("INSERT OR REPLACE INTO stock_item_section (item_key, item, section, source, seeded_as, by_user, at) VALUES (?,?,?,'walk W431',?,'W431',?)", (norm_key(it), it, sec, sec, now))
        if rate is not None:
            c.execute("INSERT OR REPLACE INTO stock_rate (item, rate_p, pack_size, as_of, source) VALUES (?,?,?,?,'walk W431')", (it, rate, ps, "26-09-2026"))
    c.commit()
    c.close()


def craft_spine(db):
    c = sqlite3.connect(db, timeout=30)
    for it, packing, ps, marg, cnt, sec, rate, facts in CRAFT:
        if not facts:
            continue
        k = it[:20].strip()
        c.execute("INSERT OR REPLACE INTO sp_item (k20, name, packing, unit_kind, first_seen, last_seen) VALUES (?,?,?,?,?,?)", (k, it, packing, "LOOSE" if ps > 1 else "WHOLE", "2026-03-31", "2026-09-26"))
        for fact, val, day in facts:
            c.execute("INSERT INTO sp_item_fact (name, packing, fact, value, as_on, source_md5) VALUES (?,?,?,?,?,'W431')", (it, packing, fact, val, day))
    c.commit()
    c.close()


DB_OLD = a.db + ".old"
copydb(a.db, DB_OLD)
craft(a.db)
craft(DB_OLD)
craft_spine(a.spine)
print("-- scratch: crafted W431 rows (an orthotic priced by the 0.30 rule, a S.RATE item, an MRP-only item, an unpriced item) on both copies and in the scratch spine")

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re, zipfile, io
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
import finance_app as fa
import stock_app
try:
    import stock_statement as SS
except Exception:
    SS = None
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
        C(name + " -- the step ran", False, "%s: %s | %s" % (type(e).__name__, str(e)[:200], traceback.format_exc()[-300:]))
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
SEC = ("Medicines", "Consumables", "Orthotics")
def st():
    r = G("manoj", "/finance/stock/api/statement/1"); return r[1] if r[0] == 200 and isinstance(r[1], dict) else None
def by_item(D):
    out = {}
    for s in D["sections"]:
        for l in s["lines"]: out[l["item"]] = (s["key"], "line", l)
        for l in s["matched"]: out[l["item"]] = (s["key"], "matched", l)
    return out
def sec(D, k):
    return [s for s in D["sections"] if s["key"] == k][0]

# ---------------------------------------------------------------- 1 the statement: three sections, every counted line once, the count-sheet order
def s1():
    D = st(); S["D"] = D
    C("the statement answers the owner; three sections in the order Medicines - Consumables - Orthotics", bool(D) and [s["key"] for s in D["sections"]] == list(SEC), D and [s["key"] for s in D["sections"]])
    W = by_item(D)
    items = [r["item"] for r in q("SELECT item FROM stock_count_item WHERE count_id=1 ORDER BY id")]
    live = [i for i in items if not i.startswith("W431")]
    allrows = [l["item"] for s in D["sections"] for l in s["lines"] + s["matched"]]
    C("every one of the %d counted lines of 06-09 appears exactly once (plus the 4 crafted): %d rows, no duplicate, none missing" % (len(live), len(allrows)),
      len(allrows) == len(items) and len(set(allrows)) == len(allrows) and set(allrows) == set(items) and len(live) == 373 and D["overall"]["lines"] == len(items), [len(live), len(allrows), len(set(items) - set(allrows))])
    secmap = {r["item"]: r["section"] for r in q("SELECT item, section FROM stock_item_section")}
    C("each line sits in the section of the owner's map (stock_item_section)", all(W[i][0] == secmap.get(i, "Medicines") for i in items), [(i, W[i][0], secmap.get(i)) for i in items if W[i][0] != secmap.get(i, "Medicines")][:4])
    ids = {r["item"]: r["id"] for r in q("SELECT id, item FROM stock_count_item WHERE count_id=1")}
    med = sec(D, "Medicines")
    C("Medicines in count-sheet order (the differing lines, then the matched, each in the sheet's order)",
      [ids[l["item"]] for l in med["lines"]] == sorted(ids[l["item"]] for l in med["lines"]) and [ids[l["item"]] for l in med["matched"]] == sorted(ids[l["item"]] for l in med["matched"]))
    T = {s["key"]: s["totals"] for s in D["sections"]}
    C("the sections' line counts: Medicines %d, Consumables %d, Orthotics %d (differing + matched = lines, matched never dropped)" % (T["Medicines"]["lines"], T["Consumables"]["lines"], T["Orthotics"]["lines"]),
      all(T[k]["lines"] == T[k]["differing"] + T[k]["matched"] == len(sec(D, k)["lines"]) + len(sec(D, k)["matched"]) for k in SEC) and T["Orthotics"]["lines"] == 70 and T["Consumables"]["lines"] == 19 and T["Medicines"]["lines"] == 288, T)
    C("every line carries Marg, physical and the words for both; a short line its shortage in words, an excess line its excess",
      all(l["marg_text"] and l["counted_text"] for s in D["sections"] for l in s["lines"] + s["matched"]) and all((l["short"] > 0) == bool(l["short_text"]) and (l["over"] > 0) == bool(l["over_text"]) for s in D["sections"] for l in s["lines"]))
    C("a matched line has no shortage and no excess after the swaps; a differing line has one of the two -- or is a Marg-negative book correction (S432 adjustment 1)", all(l["short"] == 0 and l["over"] == 0 for s in D["sections"] for l in s["matched"]) and all(((l["short"] > 0) != (l["over"] > 0)) or (l.get("neg_marg") and l["short"] == 0 and l["over"] == 0 and l["correct_units"] > 0) for s in D["sections"] for l in s["lines"]))
step("sections", s1)

# ---------------------------------------------------------------- 2 swaps: a confirmed pair reduces both partners, a not-confirmed pair nothing
def s2():
    D = S["D"]; W = by_item(D)
    pairs = q("SELECT short_item, over_item, qty, answer FROM stock_match WHERE count_id=1 AND id IN (SELECT MAX(id) FROM stock_match WHERE count_id=1 GROUP BY short_item, over_item)")
    yes = [p for p in pairs if p["answer"] == "YES"]; no = [p for p in pairs if p["answer"] == "NO"]
    inyes = {p["short_item"] for p in yes} | {p["over_item"] for p in yes}
    C("the live answers: %d confirmed pairs, %d not confirmed" % (len(yes), len(no)), len(yes) >= 10 and len(no) >= 2)
    bad = []
    for p in yes:
        for me, other in ((p["short_item"], p["over_item"]), (p["over_item"], p["short_item"])):
            k, kind, l = W[me]
            want = min(abs(l["diff_day"]), sum(x["qty"] for x in yes if me in (x["short_item"], x["over_item"])))
            after = abs(l["diff_day"]) - l["swapped"]
            ok = l["swapped"] == want and other in l["swap_with"] and ((l["short"] if l["diff_day"] < 0 else l["over"]) == after) and (kind == "matched") == (after == 0) and bool(l["swap_text"])
            if not ok: bad.append((me, l["diff_day"], l["swapped"], want, l["short"], l["over"], kind))
    C("every confirmed pair: both partners show the partner and the quantity taken out; shortage / excess = the count-day gap less the swap; a line wholly explained sits under Matched with its swap", not bad, bad[:4])
    ab = W["ANKLE BINDER BAMBOO M"][2]
    C("ANKLE BINDER BAMBOO M (2 short on the count day, 1 swapped with ANKLE BINDER M TYNOR): 1 pc short after the swap, the partner named, Darpan's reason on the line",
      W["ANKLE BINDER BAMBOO M"][1] == "line" and ab["diff_day"] == -2 and ab["swapped"] == 1 and ab["swap_with"] == ["ANKLE BINDER M TYNOR"] and ab["short"] == 1 and ab["short_text"] == "1 pc" and ab["became"].startswith("Darpan: "), ab)
    full = [(i, W[i][2]) for p in yes for i in (p["short_item"], p["over_item"]) if W[i][1] == "matched"]
    C("a line wholly explained by its confirmed swap sits under Matched with the swap shown, reading 'swap confirmed' / 'explained -- no loss' (%d such)" % len(full), full and all(l["swapped"] and ("swap confirmed" in l["became"] or "no loss" in l["became"]) and l["swap_text"] for i, l in full), [(i, l["became"]) for i, l in full if not ("swap confirmed" in l["became"] or "no loss" in l["became"])][:3])
    gx = W["GEMCAL XT TABLETS"][2]
    C("GEMCAL XT TABLETS (156 swapped with ZIBON EXTRA): the swap in strips + tabs, the partner named, no 'units'", gx["swapped"] == 156 and "ZIBON EXTRA" in gx["swap_text"] and not hits([gx["swap_text"]]), gx["swap_text"])
    bad2 = [(i, W[i][2]["swapped"], W[i][2]["short"], W[i][2]["over"], W[i][2]["diff_day"]) for p in no for i in (p["short_item"], p["over_item"]) if i not in inyes and (W[i][2]["swapped"] or W[i][2]["swap_with"] or abs(W[i][2]["diff_day"]) != W[i][2]["short"] + W[i][2]["over"])]
    C("a not-confirmed pair (LACTOVAX SYP / LINVIZ 600 / FEBUTAL) shows nothing: no swap, the whole count-day gap stands", not bad2 and all(W[i][2]["swapped"] == 0 for i in ("LACTOVAX SYP", "LINVIZ 600", "FEBUTAL")), bad2[:4])
step("swaps", s2)

# ---------------------------------------------------------------- 3 what became of it: the S427 close, group by group; the totals equal the close's
def s3():
    D = S["D"]; W = by_item(D)
    run = q("SELECT id, groups, lines_n, mrp_p FROM stock_writeoff_run WHERE count_id=1 ORDER BY id LIMIT 1")[0]
    g = json.loads(run["groups"])
    bad = {}
    for grp, ls in g.items():
        for x in ls:
            k, kind, l = W[x["item"]]
            if l["became_key"] != "wo:" + grp or k == "Orthotics" or "written off" not in l["became"]:
                bad.setdefault(grp, []).append((x["item"], l["became_key"], l["became"]))
    C("the run's %d lines read 'written off -- <group>' group by group: %s" % (run["lines_n"], ", ".join("%s %d" % (k, len(v)) for k, v in sorted(g.items()))), not bad and run["lines_n"] == 122, bad)
    Cl = D["close"]
    C("the close's totals as the statement counts them: 136 lines written off, Rs 64,678.78 at the desk's MRP (the run's 122 + 14 written off before the piles), 6 back in store, closed 27-Sep by manoj",
      Cl and Cl["written_off"] == 136 and Cl["written_off_p"] == 6467878 and Cl["back"] == 6 and Cl["by"] == "manoj" and str(Cl["at"]).startswith("2026-09-27"), Cl and {k: Cl[k] for k in ("written_off", "written_off_p", "back", "open", "at", "by")})
    C("the close's groups on the statement carry the run's counts (allowance 34, small 53, big 22, old 6, consume 5, owner's use 2) and the 14 earlier lines",
      all(Cl["groups"][k]["n"] == len(v) for k, v in g.items()) and Cl["groups"].get("earlier", {}).get("n") == 14, {k: v["n"] for k, v in Cl["groups"].items()})
    back = sorted(i for i, (k, kind, l) in W.items() if l["became_key"] == "back")
    C("the 6 back in store are named on their lines: CALAPTIN 40, DOLOGESIC SP, ETOZOX 90, GEMCAL XT TABLETS, HYORTH XL, TYCOB 1500", back == ["CALAPTIN 40", "DOLOGESIC SP", "ETOZOX 90", "GEMCAL XT TABLETS", "HYORTH XL", "TYCOB 1500"], back)
    wo_lines = [l for s in D["sections"] if s["key"] != "Orthotics" for l in s["lines"] if l["became_key"].startswith("wo:")]
    C("136 written-off lines on the Medicines + Consumables sections, each with its group title in words (allowance / small real gap / old stock / clinic consumption / owner's use / big loss / before the piles)",
      len(wo_lines) == 136 and all(any(t in l["became"] for t in ("Within the allowance", "Small real gap", "Old stock", "Clinic consumption", "Owner's use", "Big loss", "before the piles")) for l in wo_lines), [l["became"] for l in wo_lines if not any(t in l["became"] for t in ("Within the allowance", "Small real gap", "Old stock", "Clinic consumption", "Owner's use", "Big loss", "before the piles"))][:3])
    ov = [l for s in D["sections"] if s["key"] != "Orthotics" for l in s["lines"] if l["over"]]
    C("an excess medicine line says the vouchers corrected Marg -- never a loss (%d such lines)" % len(ov), ov and all("never a loss" in l["became"] for l in ov), [l["became"] for l in ov if "never a loss" not in l["became"]][:3])
    med = sec(D, "Medicines")
    C("the Medicines section's group line: the groups with their counts and rupees, back 6", med["groups"] and sum(x["n"] for x in med["groups"]) + sum(x["n"] for x in sec(D, "Consumables")["groups"]) == 136 and med["back"] == 6, [(x["key"], x["n"]) for x in med["groups"]])
step("became", s3)

# ---------------------------------------------------------------- 4 selling price: the one rule, tagged; the orthotic section apart
def s4():
    D = S["D"]; W = by_item(D)
    TAGS = {"spine S.RATE", "spine MRP", "rule 0.30", "rate / margin"}
    diff = [l for s in D["sections"] for l in s["lines"]]
    C("every differing line is priced with a source tag or counted unpriced; a matched line carries no price",
      all((l["price_p"] and l["price_src"] in TAGS and l["short_p"] is not None and l["over_p"] is not None) or (l["price_p"] is None and l["price_src"] is None) for l in diff) and all(l["price_p"] is None for s in D["sections"] for l in s["matched"]),
      [(l["item"], l["price_src"]) for l in diff if l["price_p"] and l["price_src"] not in TAGS][:3])
    for s in D["sections"]:
        T = s["totals"]
        C("%s totals add up: short %s = sum of the lines, excess %s = sum, net = short - excess, unpriced %d named" % (s["key"], T["short_p"], T["over_p"], T["unpriced"]),
          T["short_p"] == sum(l["short_p"] or 0 for l in s["lines"]) and T["over_p"] == sum(l["over_p"] or 0 for l in s["lines"]) and T["net_p"] == T["short_p"] - T["over_p"]
          and T["unpriced"] == sum(1 for l in s["lines"] if l["price_p"] is None and not l.get("neg_marg")) == len(T["unpriced_items"]) and T["short_lines"] == sum(1 for l in s["lines"] if l["short"]) and T["over_lines"] == sum(1 for l in s["lines"] if l["over"])
          and T["neg_lines"] == sum(1 for l in s["lines"] if l.get("neg_marg")) and all(l["over_p"] == 0 for l in s["lines"] if l.get("neg_marg")), T)   # S432 adjustment 2: the Marg-negative lines carry no excess money and are not 'unpriced'
    O = D["overall"]
    C("the overall totals are the three sections' sums", O["short_p"] == sum(s["totals"]["short_p"] for s in D["sections"]) and O["over_p"] == sum(s["totals"]["over_p"] for s in D["sections"]) and O["unpriced"] == sum(s["totals"]["unpriced"] for s in D["sections"]) and O["lines"] == sum(s["totals"]["lines"] for s in D["sections"]))
    src = D["price_sources"]
    C("the price sources over the differing lines: spine S.RATE and spine MRP carry most; the rule and the rate fall-backs are tagged; the 'none' are the unpriced", src.get("spine S.RATE", 0) >= 40 and src.get("spine MRP", 0) >= 40 and sum(src.values()) == len(diff) and src.get("none", 0) == O["unpriced"], src)
    kb = W["W431 KNEE BRACE L"][2]
    C("crafted W431 KNEE BRACE L (orthotic, a purchase rate of Rs 700, no spine fact): priced by the 0.30 rule -> Rs 1,000 a pc, 2 short = Rs 2,000, tag 'rule 0.30'",
      W["W431 KNEE BRACE L"][0] == "Orthotics" and kb["price_p"] == 100000 and kb["price_src"] == "rule 0.30" and kb["short"] == 2 and kb["short_p"] == 200000 and kb["short_text"] == "2 pcs", kb)
    mt = W["W431 MED TAB"][2]
    C("crafted W431 MED TAB: the spine's S.RATE 120 a strip as on the count day (its 0.0 of 05-09 is no price; MRP 150 loses to S.RATE) -> Rs 12 a tab; 2 strips short = Rs 240",
      mt["price_p"] == 1200 and mt["price_src"] == "spine S.RATE" and mt["short"] == 20 and mt["short_p"] == 24000 and mt["short_text"] == "2 strips", mt)
    mr = W["W431 MRP TAB"][2]
    C("crafted W431 MRP TAB: only an MRP as on the count day (its S.RATE of 07-09 came after) -> Rs 20 a tab, 1 strip short = Rs 200, tag 'spine MRP'",
      mr["price_p"] == 2000 and mr["price_src"] == "spine MRP" and mr["short"] == 10 and mr["short_p"] == 20000, mr)
    npc = W["W431 NOPRICE PC"][2]
    C("crafted W431 NOPRICE PC: nothing prices it -> 'no price', named in the Medicines residue; its 2 pcs excess counted as a line, not a rupee",
      npc["price_p"] is None and npc["over"] == 2 and npc["over_p"] is None and "W431 NOPRICE PC" in sec(D, "Medicines")["totals"]["unpriced_items"], npc)
    ort = sec(D, "Orthotics"); T = ort["totals"]
    C("the orthotic section's totals at selling price stand apart: short %s, excess %s, net %s over %d differing lines, %d swaps" % (T["short_p"], T["over_p"], T["net_p"], T["differing"], T["swaps"]),
      T["short_p"] > 0 and T["differing"] >= 10 and T["swaps"] >= 10 and T["matched"] >= 40 and all(l["price_src"] in ("spine S.RATE", "spine MRP", "rule 0.30") for l in ort["lines"] if l["price_p"]), T)
    C("the price texts read 'Rs X a strip' / 'a pc'; every quantity in strips + tabs / pcs -- no 'unit(s)' anywhere in the statement", all(re.match(r"^(Rs [\d,.]+ a (strip|pc)|no price)$", l["price_text"]) for l in diff) and not hits([t for t in (lambda acc: (strings(D, acc), acc)[1])([])]), hits([t for t in (lambda acc: (strings(D, acc), acc)[1])([])])[:3])
step("prices", s4)

# ---------------------------------------------------------------- 5 the orthotic block, read live from the section (S404)
def s5():
    D = S["D"]; ort = sec(D, "Orthotics"); B = ort["block"]
    import stockmatch
    con = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30)
    d = stock_app._pad_report_data(con, 1)
    ss = stockmatch.section_state(con, d)
    C("the block at the top of the orthotic section: lines still open (Darpan) %d, not yet on a voucher %d, renames unverified %d of %d -- read live from section_state" % (B["open_lines"], B["not_vouchered"], B["renames_unverified"], B["renames_total"]),
      B and B["not_vouchered"] == ss["vouchers"]["pending"] and B["renames_total"] == ss["renames"]["total"] and B["renames_unverified"] == ss["renames"]["total"] - ss["renames"]["verified"] and B["verdict"] == ss["verdict_en"], B)
    darpan = {l["item"] for l in ss["lines"] if l["open"] and not l["answered"]}
    owner = set(ss["unsettled"]) - darpan
    opn = set(B["open_items"]) | set(B["await_owner_items"])
    Wd = by_item(D)
    C("the block splits the open lines: Darpan's (no answer yet: %d) and the owner's (answered, still moving Marg without his word: %d); both kinds are marked 'open' on their lines and nowhere else; the crafted W431 KNEE BRACE L is Darpan's" % (len(darpan), len(owner)),
      set(B["open_items"]) == darpan and B["open_lines"] == len(darpan) and set(B["await_owner_items"]) == owner and B["await_owner"] == len(owner) and "W431 KNEE BRACE L" in B["open_items"]
      and all(Wd[i][2]["open"] for i in opn) and not any(l["open"] for l in ort["lines"] + ort["matched"] if l["item"] not in opn), [B["open_items"], sorted(owner)[:4], [l["item"] for l in ort["lines"] if l["open"] and l["item"] not in opn][:4]])
    med_open = [l["item"] for l in sec(D, "Medicines")["lines"] if l["open"]]
    C("a medicine the desk still holds open is marked 'open' too (the crafted W431 MED TAB and W431 MRP TAB, in a pile, not yet written off)", "W431 MED TAB" in med_open and "W431 MRP TAB" in med_open and all(Wd[i][2]["became"].startswith("open -- ") for i in ("W431 MED TAB", "W431 MRP TAB")), [Wd["W431 MED TAB"][2]["became"], len(med_open)])
    C("an orthotic line answered by Darpan carries his reason in English; one with the owner's word carries the word", any(l["became"].startswith("Darpan: ") for l in ort["lines"]) and any(l["became"].startswith("the owner: ") or "swap confirmed" in l["became"] for l in ort["lines"] + ort["matched"]), [l["became"] for l in ort["lines"]][:6])
    C("nothing on the statement decides: no POST route but freeze; section_state was not changed by reading", G("manoj", "/finance/stock/api/statement/1")[0] == 200 and q("SELECT COUNT(*) AS n FROM stock_diff_lane")[0]["n"] == q("SELECT COUNT(*) AS n FROM stock_diff_lane")[0]["n"])
    con.close()
step("ortho", s5)

# ---------------------------------------------------------------- 6 the PDF, the XLSX, the freeze; the hub; the old report; access
def s6():
    D = S["D"]
    r = G("manoj", "/finance/stock/api/statement/1.pdf")
    pdf = r[1] if isinstance(r[1], bytes) else b""
    txt = pdf.decode("latin-1", "replace")
    C("the PDF (portrait, Darpan's-sheet style): one section a heading, totals first, then the lines, matched at the end", r[0] == 200 and pdf.startswith(b"%PDF") and all(k in txt for k in ("MEDICINES - ", "CONSUMABLES - ", "ORTHOTICS - ", "Short at selling price", "Medicines - matched", "Orthotics - matched", "W431 KNEE BRACE L", "Page 1 of")), [r[0], len(pdf)])
    C("the PDF: medicines before consumables before orthotics, totals before lines, no 'unit(s)'", txt.find("MEDICINES - ") < txt.find("CONSUMABLES - ") < txt.find("ORTHOTICS - ") and txt.find("Short at selling price") < txt.find("the lines that differ") and not hits([txt]), hits([txt])[:3])
    r = G("manoj", "/finance/stock/api/statement/1.xlsx")
    x = r[1] if isinstance(r[1], bytes) else b""
    z = zipfile.ZipFile(io.BytesIO(x)) if x[:2] == b"PK" else None
    wb = z.read("xl/workbook.xml").decode("utf-8") if z else ""
    sheets = re.findall(r'<sheet name="([^"]+)"', wb)
    C("the XLSX: one sheet a section + Totals, in that order", r[0] == 200 and sheets == ["Totals", "Medicines", "Consumables", "Orthotics"], sheets)
    s4 = z.read("xl/worksheets/sheet4.xml").decode("utf-8") if z else ""
    C("the orthotic sheet carries the crafted brace with its rule tag and Rs 2,000", "W431 KNEE BRACE L" in s4 and "rule 0.30" in s4 and "<v>2000" in s4)
    # freeze
    n0 = q("SELECT COUNT(*) AS n FROM stock_statement")[0]["n"] if q("SELECT name FROM sqlite_master WHERE name='stock_statement'") else 0
    r = P("manoj", "/finance/stock/api/statement/1/freeze")
    f = (r[1] or {}).get("frozen") or {}
    rows = q("SELECT id, count_id, made_by, md5, pdf, xlsx, totals FROM stock_statement ORDER BY id")
    con = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30)
    d_ = SS._dir(con); con.close()
    C("Freeze this statement (the owner): ONE stock_statement row -- frozen JSON with its md5, PDF and XLSX kept under pad_uploads/statements, dated, by manoj",
      r[0] == 200 and len(rows) == n0 + 1 and rows[-1]["made_by"] == "manoj" and len(rows[-1]["md5"]) == 32 and rows[-1]["pdf"] == rows[-1]["md5"] + ".pdf" and os.path.exists(os.path.join(d_, rows[-1]["pdf"])) and os.path.exists(os.path.join(d_, rows[-1]["xlsx"])) and f.get("md5") == rows[-1]["md5"], [r, rows[-1]["md5"] if rows else None])
    tot = json.loads(rows[-1]["totals"])
    C("the frozen totals equal the live ones at that moment (three sections + overall + the orthotic block)", tot["overall"]["short_p"] == D["overall"]["short_p"] and tot["sections"]["Orthotics"]["short_p"] == sec(D, "Orthotics")["totals"]["short_p"] and tot["block"]["not_vouchered"] == sec(D, "Orthotics")["block"]["not_vouchered"])
    sid = rows[-1]["id"]
    fp = G("manoj", "/finance/stock/api/statement/frozen/%d.pdf" % sid); fx = G("manoj", "/finance/stock/api/statement/frozen/%d.xlsx" % sid); fj = G("manoj", "/finance/stock/api/statement/frozen/%d.json" % sid)
    C("the frozen copy serves: PDF (says 'Frozen ... fingerprint'), XLSX, JSON with the data", fp[0] == 200 and fp[1].startswith(b"%PDF") and b"Frozen " in fp[1] and fx[0] == 200 and fx[1][:2] == b"PK" and fj[0] == 200 and fj[1]["data"]["overall"]["lines"] == D["overall"]["lines"] and fj[1]["md5"] == rows[-1]["md5"])
    C("the audit log carries the freeze", q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_statement' AND action='freeze' AND row_id=?", sid)[0]["n"] == 1)
    r2 = P("manoj", "/finance/stock/api/statement/1/freeze")
    rows2 = q("SELECT id, md5 FROM stock_statement ORDER BY id")
    D2 = st()
    C("a second freeze is a second row; the earlier stays listed; the page lists both, newest first", r2[0] == 200 and len(rows2) == n0 + 2 and [x["id"] for x in D2["frozen_list"]] == [rows2[-1]["id"], rows2[-2]["id"]], [x["id"] for x in D2["frozen_list"]])
    hub = G("manoj", "/finance/stock/api/pad/hub/1")[1]
    L = hub["links"]
    C("the hub's links carry the statement (page, PDF, Excel) and the latest frozen copy 'as at <time>' by manoj", L.get("statement") == "/finance/stock/page/statement?count=1" and L.get("statement_pdf") and L.get("statement_xlsx") and (L.get("statement_frozen") or {}).get("id") == rows2[-1]["id"] and "IST" in L["statement_frozen"]["as_at"] and L["statement_frozen"]["by"] == "manoj" and L["statement_frozen"]["n"] == n0 + 2, L.get("statement_frozen"))
    hp = G("manoj", "/finance/stock/page/hub?count=1")[1]
    C("the hub page: the first card gains 'The count statement -- section by section' above 'The count -- full report'; the status card names old stock and owner's use", isinstance(hp, bytes) and hp.find("The count statement — section by section".encode("utf-8")) > 0 and hp.find("The count statement — section by section".encode("utf-8")) < hp.find("The count — full report".encode("utf-8")) and b'["old","old stock"]' in hp and b"""["owner_use","owner's use"]""" in hp)
    rp = G("manoj", "/finance/stock/page/report?count=1")[1]
    rj = G("manoj", "/finance/stock/api/pad/report/1")[1]
    C("the old report keeps its route and is closed: 'Closed on <date> -- see the statement', a statement link in its tools, NO 'Open the decision desk' pointer; its JSON links carry the statement",
      isinstance(rp, bytes) and b"Closed on " in rp and b"see the statement" in rp and rp.count("The count statement — section by section".encode("utf-8")) >= 2 and b"Open the decision desk" not in rp and rj["closed"] and rj["links"].get("statement") == "/finance/stock/page/statement?count=1", rj.get("closed"))
    pg = G("manoj", "/finance/stock/page/statement?count=1")
    C("the statement page serves the owner with the Freeze button armed (can_freeze true); English; no 'unit(s)' in its source", pg[0] == 200 and b'"can_freeze": true' in pg[1] and b"Freeze this statement" in pg[1] and not hits([pg[1].decode("utf-8", "replace")]), hits([pg[1].decode("utf-8", "replace")])[:3])
    pb = G("bhawna", "/finance/stock/page/statement?count=1")
    C("the doctor (bhawna) reads the statement and its PDF, cannot freeze", pb[0] == 200 and b'"can_freeze": false' in pb[1] and G("bhawna", "/finance/stock/api/statement/1")[0] == 200 and G("bhawna", "/finance/stock/api/statement/1.pdf")[0] == 200 and P("bhawna", "/finance/stock/api/statement/1/freeze")[0] == 403, [pb[0], P("bhawna", "/finance/stock/api/statement/1/freeze")])
    C("bhati / darpan / shavez are refused on the page, the JSON, the PDF and the freeze", all(G(u, p)[0] in (401, 403, 302) for u in ("bhati", "darpan", "shavez") for p in ("/finance/stock/page/statement?count=1", "/finance/stock/api/statement/1", "/finance/stock/api/statement/1.pdf")) and all(P(u, "/finance/stock/api/statement/1/freeze")[0] in (401, 403, 302) for u in ("bhati", "darpan", "shavez")))
    C("a count that does not exist answers 404; the hub without S431 would still answer (the links are defensive)", G("manoj", "/finance/stock/api/statement/999")[0] == 404 and hub["ok"] is not False)
step("freeze", s6)

out = dict(mode=os.environ["MODE"], R=R, has_ss=bool(SS))
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
    check("stock_statement.py is beside stock_app.py", N["has_ss"])

print("-- NEGATIVE CONTROL: the same scenario on the box as it is (must go red)")
O = run("old", a.old, DB_OLD)
if O is None:
    check("NEGATIVE: the old app's probe ran", False)
else:
    red = [l for l, ok, _g in O["R"] if not ok]
    for l, ok, _g in O["R"]:
        print("   old %s  %s" % ("ok  " if ok else "RED ", l))
    must = ("the statement answers the owner; three sections in the order Medicines - Consumables - Orthotics",)
    green = {l for l, ok, _g in O["R"] if ok}
    check("NEGATIVE: the old files go red (%d of %d checks red): no statement route, no freeze, the decision-desk pointer still on the report, no statement link on the hub" % (len(red), len(O["R"])),
          not any(m in green for m in must) and len(red) >= 8, red[:8])
    check("NEGATIVE: the old box has no stock_statement.py", not O["has_ss"])

print("WALK_S431 %s -- %d of %d %s (re-run by S432 with 2 named adjustments: the Marg-negative lines)" % ("GREEN" if not fails else "RED", (n - len(fails)) if not fails else len(fails), n, "passed" if not fails else "failed"))
for f in fails:
    print("   red: " + f)
sys.exit(0 if not fails else 1)
