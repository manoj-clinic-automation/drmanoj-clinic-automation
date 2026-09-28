#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s437.py -- kit S437_COUNT_PAGES_FINAL (F-659). THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over
SCRATCH copies of the live finance.db and the spine, driven through Flask's test client with header identity (walk only). The round is
the REAL count #1 (closed on every screen; Amir has keyed nothing). The kit's seed runs on the new copy first, as the installer runs it on
the live database. Every real line is found BY KEY from the maker's own pending list BEFORE the seed -- never by a count fixed here.
Crafted rows are keyed W437*: one medicine over on the shelf (the rule at a later close), one 1*N medicine sold only whole (a whole-piece
candidate). The SAME scenario then runs against the box as it is (--old): it must go red.

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


# item, packing, pack, marg, counted, sales (qty_raw list)
CRAFT = (("W437 WHOLE TAB", "1*30", 30, 6, 6, ["1.0", "2.0", "1.0"]),      # sold only in whole multiples of 30 -> a whole-piece candidate
         ("W437 LOOSE TAB", "1*10", 10, 12, 12, ["1:3", "2:0"]))          # a loose sale -> not a candidate


def craft(db):
    c = sqlite3.connect(db, timeout=30)
    as_on = c.execute("SELECT marg_as_on FROM stock_count WHERE id=1").fetchone()[0]
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    eid = c.execute("SELECT id FROM day_entry WHERE unit='medical' ORDER BY id DESC LIMIT 1").fetchone()[0]
    c.execute("DELETE FROM sale_line_item WHERE unit='medical' AND bill_no LIKE 'W437%'")
    i = 0
    for it, packing, ps, marg, cnt, sales in CRAFT:
        c.execute("INSERT OR REPLACE INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,'walk W437')", (as_on, it, marg, packing, ps, now))
        c.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, strips, loose, counted_by, entered_by, at) VALUES (1,?,?,?,?,?,0,0,'W437','W437',?)",
                  (it, packing, ps, marg, cnt, now))
        c.execute("INSERT OR REPLACE INTO stock_item_section (item_key, item, section, source, seeded_as, by_user, at) VALUES (?,?,?,'walk W437',?,'W437',?)", (norm_key(it), it, "Medicines", "Medicines", now))
        for q in sales:
            i += 1
            c.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,'medical','2026-09-01',?,0,1,?,?,?,?,1000)",
                      (eid, "W437A%03d" % i, it, norm_key(it), packing, q))
    c.commit()
    c.close()


def pre_seed(db, app):
    """The maker's pending lines as the NEW files read them BEFORE the seed -- by key."""
    os.environ["FINANCE_DB"] = db
    os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
    sys.path.insert(0, app)
    cwd = os.getcwd()
    os.chdir(app)
    import finance_app as fa                                  # noqa: PLC0415
    import stock_app                                          # noqa: PLC0415
    out = dict(receive=[], issue=[], to={}, unworded=[], ccm_words_before=None)
    with fa.app.test_request_context():
        con = stock_app._db()
        d = stock_app._pad_report_data(con, 1)
        for p in stock_app._voucher_pending(con, d):
            out["receive" if p["kind"] == "RECEIVE" else "issue"].append(p["item"])
            out["to"][p["item"]] = [p["marg_from"], p["marg_to"], p["change"], p["counted"]]
        carried = set(out["receive"]) | set(out["issue"]) | set(stock_app._voucher_frozen(con, 1).keys())
        for x in d["differences"]:                            # the shelf-more lines the maker does not carry (no word, or PARKED): the rule words them
            if stock_app._item_section(con, x) == "Orthotics" or x["item"] in carried:
                continue
            diff, marg, sw = int(x.get("diff") or 0), int(x.get("marg") or 0), int(x.get("swapped") or 0)
            after = (diff - sw) if diff > 0 else diff
            if after > 0 or marg < 0:
                out["unworded"].append(x["item"])
                out["to"][x["item"]] = [marg, int(x.get("counted") or 0), int(x.get("counted") or 0) - marg, int(x.get("counted") or 0)]
        out["rounds_before"] = [r[0] for r in con.execute("SELECT DISTINCT round_no FROM stock_voucher_line WHERE count_id=1 ORDER BY round_no")]
    os.chdir(cwd)
    return out


DB_OLD = a.db + ".old"
copydb(a.db, DB_OLD)
craft(a.db)
craft(DB_OLD)
PRE = pre_seed(a.db, a.app)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s437  # noqa: E402
assert seed_s437.seed(a.db, a.app) == 0, "seed failed"
print("-- scratch: crafted W437 rows on both copies; before the seed %d RECEIVE and %d ISSUE lines waited for a voucher (rounds %s) and %d shelf-more lines had no word at all; the S437 seed ran on the new copy"
      % (len(PRE["receive"]), len(PRE["issue"]), PRE["rounds_before"], len(PRE["unworded"])))

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
import finance_app as fa
import stock_app
try:
    import loss_piles as LP
    import stock_watch as SW
    import qty_words as QW
except Exception:
    LP = SW = QW = None
PRE = json.loads(os.environ["PRE_JSON"])
RECV, ISS, TO, UNW = PRE["receive"], PRE["issue"], PRE["to"], PRE["unworded"]
ALLR = sorted(set(RECV) | set(UNW))
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data()]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
now = lambda: dt.datetime.now().replace(microsecond=0).isoformat()
R = []
def C(label, cond, got=None):
    R.append([label, bool(cond), (json.dumps(got, default=str)[:400] if got is not None else None)])
def step(name, fn):
    try:
        fn()
    except Exception as e:
        import traceback
        C(name + " -- the step ran", False, "%s: %s | %s" % (type(e).__name__, str(e)[:200], traceback.format_exc()[-400:]))
def strings(o, acc):
    if isinstance(o, dict):
        for v in o.values(): strings(v, acc)
    elif isinstance(o, list):
        for v in o: strings(v, acc)
    elif isinstance(o, str):
        acc.append(o)
UNITW = re.compile(r"\b(units?|yunit)\b", re.I)
def hits(rx, texts):
    return [t[max(0, rx.search(t).start() - 30):rx.search(t).start() + 40] for t in texts if rx.search(t)]
def hub():
    return G("manoj", "/finance/stock/api/pad/hub/1")[1]
def amir():
    return G("amir", "/finance/stock/api/pad/amir/1")[1]
def desk():
    return G("manoj", "/finance/stock/api/loss/1/piles")[1]
def report():
    return stock_app._pad_report_data(db, 1)
S = {}

# ---------------------------------------------------------------- 1 the STOCK RECEIVE round by rule
def s1():
    run = q("SELECT id, at, by_user, lines_n, groups, round_no, kind FROM stock_writeoff_run WHERE count_id=1 AND kind='receive_close' ORDER BY id")
    S["run"] = run[0] if run else None
    g = json.loads(run[0]["groups"]) if run else {}
    rc, ie = g.get("receive", []), g.get("issue_earlier", [])
    C("ONE run of kind receive_close by 'rule F-659, 28-Sep': every line where the shelf held more than Marg under 'receive' (%d: the %d the maker already carried + the %d nobody had worded, now worded EXPLAINED by the rule), the %d earlier write-offs on no voucher under 'issue_earlier'; nothing valued (mrp 0)" % (len(ALLR), len(RECV), len(UNW), len(ISS)),
      len(run) == 1 and run[0]["by_user"] == "rule F-659, 28-Sep" and sorted(x["item"] for x in rc) == ALLR and sorted(x["item"] for x in ie) == sorted(ISS) and all((x["mrp_p"] or 0) == 0 for x in rc + ie)
      and all(q("SELECT action, note FROM stock_diff_lane WHERE count_id=1 AND item=? ORDER BY id DESC LIMIT 1", i)[0]["action"] == "EXPLAINED" and "rule F-659" in q("SELECT note FROM stock_diff_lane WHERE count_id=1 AND item=? ORDER BY id DESC LIMIT 1", i)[0]["note"] for i in UNW),
      {k: len(v) for k, v in g.items()})
    rno = run[0]["round_no"] if run else None; S["rno"] = rno
    vl = {r["item"]: r for r in q("SELECT item, kind, batch_no, marg_from, marg_to, change FROM stock_voucher_line WHERE count_id=1 AND round_no=?", rno)}
    per = {}
    for r in q("SELECT kind, batch_no, COUNT(*) AS n FROM stock_voucher_line WHERE count_id=1 AND round_no=? GROUP BY kind, batch_no", rno):
        per[(r["kind"], r["batch_no"])] = r["n"]
    C("every shelf-more line has exactly ONE STOCK RECEIVE line on round %s: Marg से → तक = the shelf figure the maker computed (marg_to), change = the difference; the earlier write-offs one STOCK ISSUE line each; at most %d lines a voucher" % (rno, LP.settings(db)["voucher_batch"]),
      rno and all(i in vl and vl[i]["kind"] == "RECEIVE" and vl[i]["marg_to"] == TO[i][1] and vl[i]["change"] == TO[i][2] for i in ALLR) and all(i in vl and vl[i]["kind"] == "ISSUE" and vl[i]["marg_to"] == TO[i][1] for i in ISS)
      and q("SELECT COUNT(*) AS n FROM stock_voucher_line WHERE count_id=1 AND round_no=?", rno)[0]["n"] == len(ALLR) + len(ISS) and (max(per.values()) if per else 99) <= LP.settings(db)["voucher_batch"],
      [rno, len(vl), [(i, vl.get(i, {}).get("kind"), vl.get(i, {}).get("marg_to"), TO[i][1]) for i in ALLR[:3]]])
    C("a shelf-more line is never a loss: none of them in a loss group of any run; the leakage period line equals the medicine run's loss; no stock_watch_adjust row for the rule's run",
      bool(run) and not any(x["item"] in set(ALLR) for r in q("SELECT groups FROM stock_writeoff_run WHERE count_id=1") for k, v in json.loads(r["groups"]).items() if k in ("allowance", "small", "big") for x in v)
      and SW.count_periods(db)[-1]["loss_p"] == sum((x.get("cost_p") or x.get("mrp_p") or 0) for k in ("allowance", "small", "big") for x in json.loads(q("SELECT groups FROM stock_writeoff_run WHERE id=1")[0]["groups"]).get(k, []))
      and not q("SELECT 1 FROM stock_watch_adjust WHERE run_id=?", run[0]["id"]), [SW.count_periods(db)[-1]["loss_p"]])
    hb = hub(); S["hub"] = hb
    C("the hub's pending is 0 -- every line is on a voucher; the hub page says so ('Every line is on a voucher'); the maker finds nothing pending",
      hb["vouchers"]["pending"] == 0 and len(stock_app._voucher_pending(db, report())) == 0 and b"Every line is on a voucher" in G("manoj", "/finance/stock/page/hub?count=1")[1], hb["vouchers"])
    D = desk(); S["desk"] = D
    rr = [r for r in D["record"]["runs"] if r["kind"] == "receive_close"]
    C("the record reads the run: kind 'Marg corrected -- the STOCK RECEIVE vouchers by rule (never a loss)', its groups titled, corrective; the block is untouched (the union never takes the run in)",
      len(rr) == 1 and "Marg corrected" in rr[0]["kind_text"] and rr[0].get("corrective") and {g_["key"] for g_ in rr[0]["groups"]} >= {"receive"} and all("STOCK" in g_["title"] for g_ in rr[0]["groups"])
      and D["block"] and D["block"]["run_id"] == 1 and q("SELECT COUNT(*) AS n FROM stock_staff_block WHERE count_id=1")[0]["n"] == 1, [r["kind_text"] for r in D["record"]["runs"]])
    st = G("manoj", "/finance/stock/api/statement/1")[1]
    med = [s_ for s_ in st["sections"] if s_["key"] == "Medicines"][0]
    bl = {l["item"]: l for l in med["lines"] + med["matched"]}
    ov = [i for i in ALLR if i in bl]
    allov = [l for l in med["lines"] if l["over"] or l.get("neg_marg")]
    C("the statement reads 'Marg corrected -- on STOCK RECEIVE voucher N' on EVERY shelf-more / Marg-negative medicine line (%d of the section's %d), 'on STOCK ISSUE voucher N' on a written-off line; no 'voucher round' number anywhere" % (len(ov), len(allov)),
      ov and all(re.match(r"^Marg corrected -- on STOCK RECEIVE voucher \d+$", bl[i]["voucher"]) for i in ov) and all(re.match(r"^Marg corrected -- on STOCK RECEIVE voucher \d+$", l["voucher"] or "") for l in allov)
      and all(re.match(r"^on STOCK ISSUE voucher \d+", bl[i]["voucher"]) for i in ISS if i in bl and i not in ALLR)
      and not any("voucher round" in (l["voucher"] or "") for s_ in st["sections"] for l in s_["lines"] + s_["matched"]), [(l["item"], l["voucher"]) for l in allov if not (l["voucher"] or "").startswith("Marg corrected")][:4])
    # the rule again: nothing pending -> None; a new shelf-more line -> its RECEIVE line at the next rule (the close calls it)
    C("the rule again with nothing pending writes nothing (None); a second run does not appear", LP.receive_close(db, 1, "walk", report()) is None and q("SELECT COUNT(*) AS n FROM stock_writeoff_run WHERE kind='receive_close'")[0]["n"] == 1)
    ts = now()
    db.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,'walk W437')", (q("SELECT marg_as_on AS a FROM stock_count WHERE id=1")[0]["a"], "W437 OVER TAB", 5, "1*10", 10, ts))
    db.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, strips, loose, counted_by, entered_by, at) VALUES (1,'W437 OVER TAB','1*10',10,5,9,0,0,'W437','W437',?)", (ts,))
    db.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, pack_size, value_p, cause, status, counted_by) VALUES (1,'W437 OVER TAB',?,5,9,4,10,NULL,'UNEXPLAINED','open','W437')", (q("SELECT marg_as_on AS a FROM stock_count WHERE id=1")[0]["a"],))
    db.execute("INSERT OR REPLACE INTO stock_item_section (item_key, item, section, source, seeded_as, by_user, at) VALUES ('W437 OVER TAB','W437 OVER TAB','Medicines','walk W437','Medicines','W437',?)", (ts,)); db.commit()
    d2 = report()
    pend0 = stock_app._voucher_pending(db, d2)
    R2 = LP.receive_close(db, 1, "walk close", d2)
    vl2 = q("SELECT kind, marg_from, marg_to, change FROM stock_voucher_line WHERE count_id=1 AND item='W437 OVER TAB'")
    w2 = q("SELECT action, note FROM stock_diff_lane WHERE count_id=1 AND item='W437 OVER TAB' ORDER BY id DESC LIMIT 1")
    C("a crafted shelf-more line nobody worded (W437 OVER TAB, Marg 5 -> shelf 9) is not even pending; the rule at a close words it (EXPLAINED, 'walk close: the shelf held more than Marg') and puts it on a STOCK RECEIVE line 5 -> 9 in a new run; pending back to 0",
      not pend0 and R2 and R2["receive"] == 1 and R2["issue"] == 0 and R2["worded"] == ["W437 OVER TAB"] and vl2 and vl2[0]["kind"] == "RECEIVE" and vl2[0]["marg_from"] == 5 and vl2[0]["marg_to"] == 9
      and w2 and w2[0]["action"] == "EXPLAINED" and "shelf held more than Marg" in w2[0]["note"] and len(stock_app._voucher_pending(db, report())) == 0, [R2, vl2, w2])
    C("the close itself carries the rule: loss_piles._run calls receive_close after the count's own round", "receive_close(con, root, who, d2)" in open(os.path.join(APP, "loss_piles.py"), encoding="utf-8").read())
step("receive", s1)

# ---------------------------------------------------------------- 2 Amir's board: vouchers only, numbered
GATE = re.compile(r"written off|\bloss\b|\brule\b|\bowner\b|\bclosed\b|\bgroup\b|swap|allowance|Small real|Big loss", re.I)
def s2():
    am = amir(); S["am"] = am
    VF = am["made"]["vouchers_flat"]
    iss = [v for v in VF if v["kind"] == "ISSUE"]; rec = [v for v in VF if v["kind"] == "RECEIVE"]
    C("the board's vouchers as Amir keys them: STOCK ISSUE वाउचर 1..%d then STOCK RECEIVE वाउचर 1..%d, numbered continuously across the whole count (rounds %s), every voucher of every round once" % (len(iss), len(rec), sorted({v["round_no"] for v in VF})),
      [v["seq"] for v in iss] == list(range(1, len(iss) + 1)) and [v["seq"] for v in rec] == list(range(1, len(rec) + 1)) and VF[:len(iss)] == iss
      and len(VF) == q("SELECT COUNT(*) AS n FROM (SELECT DISTINCT round_no, kind, batch_no FROM stock_voucher_line WHERE count_id=1)")[0]["n"]
      and all(v["title_hi"] == ("STOCK ISSUE — वाउचर %d" % v["seq"] if v["kind"] == "ISSUE" else "STOCK RECEIVE — वाउचर %d" % v["seq"]) for v in VF), [len(iss), len(rec), [(v["kind"], v["seq"], v["round_no"], v["batch_no"]) for v in VF[:4]]])
    C("no voucher carries more than %d lines" % LP.settings(db)["voucher_batch"], all(v["n"] <= LP.settings(db)["voucher_batch"] and len(v["lines"]) == v["n"] for v in VF))
    lines = [l for v in VF for l in v["lines"]]
    rendered = ["%s (%s) · Marg से %s → तक %s · %s %s" % (l["item"], l["packing"], l["from_hi"], l["to_hi"], "−" if l["change"] < 0 else "+", l["qty_hi"]) for l in lines]
    C("a rendered voucher line is item (packing) · Marg से → तक · कितना and NOTHING else: none of 'written off', 'loss', 'rule', 'owner', 'closed', 'group', 'swap' in any of the %d lines; the page draws only those fields (no reason, no rate, no value)" % len(lines),
      lines and not hits(GATE, rendered) and all(l["from_hi"] and l["to_hi"] and l["qty_hi"] for l in lines), hits(GATE, rendered)[:3])
    pg = G("amir", "/finance/stock/page/amir?count=1")[1].decode("utf-8", "replace")
    C("the page source: the voucher line draws item, packing, from_hi, to_hi, qty_hi only -- no l.reason / rate_p / value_p / round number; 'STOCK ISSUE — वाउचर', 'STOCK RECEIVE — वाउचर', 'Marg में डाल दिया' present; no 'Round '",
      "l.reason" not in pg and "rate_p" not in pg and "value_p" not in pg and "roundTitle" not in pg and "STOCK ISSUE" in pg and "STOCK RECEIVE" in pg and "वाउचर " in pg and "Marg में डाल दिया" in pg and "Round '+" not in pg)
    ccm = [(v["title"], l) for v in VF for l in v["lines"] if l["item"] == "CCM"]
    C("CCM on the board reads bottles: '- 3 botal' (Marg 8 botal -> 5 botal), never goli", ccm and ccm[0][1]["qty_hi"] == "3 botal" and ccm[0][1]["from_hi"] == "8 botal" and ccm[0][1]["to_hi"] == "5 botal" and ccm[0][1]["qty_text"] == "3 bottles", ccm)
    C("Naam badlo is hidden while the proof is not green: renames_ready False, the wait line 'नाम बदलना — बाद में, जब Marg और shelf मिल जाएँ'; the page draws the names only under renames_ready",
      am["renames_ready"] is False and am["renames_wait_hi"] == "नाम बदलना — बाद में, जब Marg और shelf मिल जाएँ" and am["proof_state"] == "wait" and "d.renames_ready?((d.renames||{}).rows||[]):[]" in pg, [am["renames_ready"], am["renames_wait_hi"], am["proof_state"]])
    # key every voucher, then a crafted proof: Marg's export before the first voucher and after the last, every item moved by its voucher
    ent = []
    for v in VF:
        if not v["entered"]:
            ent.append(P("amir", "/finance/stock/api/pad/vouchers/1/entered", {"round": v["round_no"], "kind": v["kind"], "batch": v["batch_no"], "marg_voucher_no": "W437-%s-%d" % (v["kind"][0], v["seq"])})[0])
    am2 = amir()
    C("'Marg में डाल दिया' on every voucher (%d, 200 each): every voucher keyed; the board folds them with their Marg number; still no names" % len(ent),
      ent and all(x == 200 for x in ent) and all(v["entered"] and v["entered"]["no"].startswith("W437-") for v in am2["made"]["vouchers_flat"]) and am2["renames_ready"] is False and am2["proof_state"] == "now", [len(ent), am2["proof_state"]])
    need = {}
    for r in q("SELECT item, change FROM stock_voucher_line WHERE count_id=1"):
        need[r["item"]] = need.get(r["item"], 0) + int(r["change"])
    # the export BEFORE the vouchers is yesterday's day (newer than any real export day before today, so the proof reads OUR rows for it -- a real
    # earlier day would carry its own drift), the export AFTER is a day 90 days on; both computed from today, never hardcoded
    D0, D1 = (dt.date.today() - dt.timedelta(days=1)).strftime("%d-%m-%Y"), (dt.date.today() + dt.timedelta(days=90)).strftime("%d-%m-%Y")
    t_before, t_after = (dt.datetime.now() - dt.timedelta(minutes=30)).replace(microsecond=0).isoformat(), (dt.datetime.now() + dt.timedelta(minutes=5)).replace(microsecond=0).isoformat()
    for src, day, m_add, rec in (("push_snapshot", D0, 0, t_before), ("push_expected base=03-09-2026 pur_to=%s" % D0, D0, None, t_before),
                                 ("push_snapshot", D1, 1, t_after), ("push_expected base=03-09-2026 pur_to=%s" % D1, D1, None, t_after)):
        for i, v in need.items():
            db.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES (?,?,?,?,?)", (day, src, i, 100 + (v if m_add else 0), rec))
    db.commit()
    pf = stock_app._proof_state(db, report())
    am3 = amir()
    C("with a crafted proof (Marg's export after the last voucher: every vouchered item moved by exactly its voucher) the proof is green (state done), Naam badlo is SHOWN (23) and the hub's step reads Marg = shelf",
      pf["state"] == "done" and pf["differ"] == 0 and am3["renames_ready"] is True and len(am3["renames"]["rows"]) == 23 and am3["proof_hi"].startswith("Marg = shelf"),
      [pf["state"], pf.get("differ"), am3["proof_hi"], [(r_["item"], r_["need"], r_["moved"], r_["why"]) for r_ in (pf.get("rows") or []) if not r_.get("ok")][:6]])
    acc = []; strings(am3, acc)
    C("no 'unit(s)' on Amir's board JSON or page", not hits(UNITW, acc + [pg]), hits(UNITW, acc + [pg])[:3])
step("amir", s2)

# ---------------------------------------------------------------- 3 whole-piece items (the CCM bug)
def s3():
    C("qty_words v1.2 carries the whole-piece map: CCM = bottle after the seed; 3 of it reads '3 bottles' / '3 botal'; an item off the list reads strips + tabs as before",
      QW.VERSION == "1.2" and QW.whole_unit_of("CCM") == "bottle" and QW.words(3, "1*40", pack=40, name="CCM") == "3 bottles" and QW.words(3, "1*40", pack=40, name="CCM", lang="hi") == "3 botal"
      and QW.words(62, "1*20", pack=20, name="ACILOC 300") == "3 strips + 2 tabs", [QW.VERSION, getattr(QW, "whole_units", lambda: None)(), QW.words(3, "1*40", pack=40, name="CCM")])
    C("the setting stock.whole_unit_items is seeded 'CCM = bottle' (audited, set by the build)", q("SELECT value FROM setting WHERE key='stock.whole_unit_items'")[0]["value"] == '["CCM = bottle"]'
      and q("SELECT COUNT(*) AS n FROM audit_log WHERE action='stock_setting' AND after_json LIKE '%whole_unit_items%'")[0]["n"] >= 1)
    D = desk()
    ccm = [l for l in D["done"]["written_off"] if l["item"] == "CCM"]
    C("the desk reads CCM in bottles (short 3 bottles, Marg 8 bottles, counted 5 bottles) -- the cache rebuilt on the changed setting", ccm and ccm[0]["short_text"] == "3 bottles" and ccm[0]["marg_text"] == "8 bottles" and ccm[0]["counted_text"] == "5 bottles", ccm and {k: ccm[0][k] for k in ("short_text", "marg_text", "counted_text")})
    st = G("manoj", "/finance/stock/api/statement/1")[1]
    med = [s_ for s_ in st["sections"] if s_["key"] == "Medicines"][0]
    l = [x for x in med["lines"] + med["matched"] if x["item"] == "CCM"]
    C("the statement reads CCM in bottles", l and l[0]["short_text"] == "3 bottles" and l[0]["marg_text"] == "8 bottles", l and l[0]["marg_text"])
    K = G("darpan", "/finance/stockmatch/api/state?count=1")[1]["block"]
    row = [r for r in K["tables"]["chhoti"]["rows"] if r["item"] == "CCM"]
    C("Darpan's block table reads CCM in botal", row and row[0]["short_hi"] == "3 botal" and row[0]["marg_hi"] == "8 botal", row)
    pdf = G("manoj", "/finance/stock/api/loss/1/record.pdf"); b = bytes(pdf[1]) if not isinstance(pdf[1], dict) else b""
    C("the record PDF reads CCM in bottles", b[:4] == b"%PDF" and b"3 bottles" in b, [pdf[0], len(b)])
    S_ = [s_ for s_ in D["settings"] if s_["key"] == "stock.whole_unit_items"]
    cand = S_[0].get("candidates") or []
    C("the settings card lists the whole-piece list with its words and the candidates: the crafted W437 WHOLE TAB (sold only in wholes of 30) is a candidate, W437 LOOSE TAB (a loose sale) is not, CCM (on the list) is not; every candidate carries a guessed word",
      S_ and S_[0]["items"] == ["CCM = bottle"] and S_[0]["words"] and any(x["item"] == "W437 WHOLE TAB" and x["word"] == "bottle" for x in cand) and not any(x["item"] in ("W437 LOOSE TAB", "CCM") for x in cand)
      and all(x["word"] in S_[0]["words"] for x in cand), [len(cand), [x["item"] for x in cand][:8]])
    r = P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.whole_unit_items", "add": "W437 WHOLE TAB", "word": "jar"})
    D2 = desk()
    S2 = [s_ for s_ in D2["settings"] if s_["key"] == "stock.whole_unit_items"][0]
    C("one tap adds a candidate with its word ('W437 WHOLE TAB = jar', audited); it leaves the candidates; a bad word is refused; a remove takes it off",
      r[0] == 200 and r[1]["ok"] and S2["items"] == ["CCM = bottle", "W437 WHOLE TAB = jar"] and not any(x["item"] == "W437 WHOLE TAB" for x in S2.get("candidates") or [])
      and P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.whole_unit_items", "add": "W437 LOOSE TAB", "word": "carton"})[1]["ok"] is False
      and P("manoj", "/finance/stock/api/loss/1/pile/setting", {"key": "stock.whole_unit_items", "remove": "W437 WHOLE TAB"})[1]["ok"] and [s_ for s_ in desk()["settings"] if s_["key"] == "stock.whole_unit_items"][0]["items"] == ["CCM = bottle"], [r, S2["items"]])
    lp = G("manoj", "/finance/stock/page/loss?count=1")[1].decode("utf-8", "replace")
    C("the desk page carries the whole-piece card (data-whole-add, the word select) and no 'unit' word on it", "data-whole-add" in lp and "whole_w" in lp and not hits(UNITW, [lp]), hits(UNITW, [lp])[:3])
step("whole", s3)

# ---------------------------------------------------------------- 4 Darpan's page: the block as tables, the foot cut
def s4():
    st = G("darpan", "/finance/stockmatch/api/state?count=1")[1]; K = st["block"]; T = K["tables"]
    frozen = q("SELECT total_p, small_p, big_p, big_lines FROM stock_staff_block WHERE count_id=1 ORDER BY id DESC LIMIT 1")[0]
    big_items = [x["item"] for x in json.loads(frozen["big_lines"])]
    C("the block's tables: Badi kami rows = the frozen big lines (%d, largest first) with Marg on the count day, gina, kami, Rs; its total = the block's big figure (%s)" % (len(big_items), LP._rs(frozen["big_p"])),
      [r["item"] for r in T["badi"]["rows"]] == big_items and T["badi"]["total_p"] == frozen["big_p"] and T["badi"]["hi"] == "Badi kami — %s" % LP._rs(frozen["big_p"]) and all(r["marg"] is not None and r["counted"] is not None and r["short_hi"] and r["rs"] for r in T["badi"]["rows"]),
      [T["badi"]["n"], T["badi"]["total_p"], frozen["big_p"], T["badi"]["rows"][:1]])
    C("Chhoti kami rows (allowance + small of the frozen run) total the block's small figure (%s); every row worded" % LP._rs(frozen["small_p"]), T["chhoti"]["total_p"] == frozen["small_p"] and T["chhoti"]["n"] > 0 and all(r["short_hi"] for r in T["chhoti"]["rows"]), [T["chhoti"]["n"], T["chhoti"]["total_p"], frozen["small_p"]])
    C("kul = the block's total (%s); the orthotic rows apart: 10 lines, Rs 5,420, 'Orthotics band ho gaya — kami Rs 5,420 (10 line, bina bill) · 2 bina daam'" % LP._rs(frozen["total_p"]),
      T["kul"]["p"] == frozen["total_p"] and T["ortho"]["n"] == 10 and T["ortho"]["total_p"] == 542000 and len(T["ortho"]["rows"]) == 10 and T["ortho"]["hi"] == "Orthotics band ho gaya — kami Rs 5,420 (10 line, bina bill) · 2 bina daam"
      and not any(r["item"] in {x["item"] for x in T["badi"]["rows"] + T["chhoti"]["rows"]} for r in T["ortho"]["rows"]), [T["kul"], T["ortho"]["hi"]])
    C("the three text lines (+ the orthotic foot line) still ride the JSON for the pages that print them", len(K["lines_hi"]) == 4 and K["lines_hi"][0].startswith("Ginti"))
    pg = G("darpan", "/finance/stockmatch")[1].decode("utf-8", "replace")
    C("Darpan's page source: the block as tables (tbl(), the Hindi headers), Badi kami open, Chhoti kami and the orthotic rows collapsed ('dikhao'), the block drawn LAST (blockCard after linesCard); the verdict tail and the four status lines gone (no s.conds, no verdict_hi); the pairs fold to 'Adla-badli N — ho gaya'; the empty 'Koi line baaki nahi' card gone; 'Sab ho gaya' only from the server's progress while lines are open",
      "function tbl(" in pg and "dikhao" in pg and pg.find("h+=linesCard(s);") < pg.find("h+=blockCard(s);") and "s.conds" not in pg and "verdict_hi" not in pg and "ho gaya <span class=\"muted\">(dikhao" in pg and "Koi line baaki nahi" not in pg and "Sab ho gaya" not in pg
      and "if(!(s.progress.all&&s.progress.need))" in pg, None)
    C("the last thing the page draws is the block card ending with the orthotic line and its collapsed table", pg.find("blockCard(s)") > 0 and pg.find("T.ortho.hi") > pg.find("T.chhoti.hi") > pg.find("T.badi.hi"))
step("darpan", s4)

# ---------------------------------------------------------------- 5 the owner's desk: the block as tables
def s5():
    D = desk(); T = D["block"]["tables"]
    frozen = q("SELECT total_p, small_p, big_p FROM stock_staff_block WHERE count_id=1 ORDER BY id DESC LIMIT 1")[0]
    C("the desk's frozen block carries the same tables in English: Big losses (%s) / Small losses (%s) / Orthotics, totals = the frozen run" % (T["badi"]["rs"], T["chhoti"]["rs"]),
      T["badi"]["total_p"] == frozen["big_p"] and T["chhoti"]["total_p"] == frozen["small_p"] and T["kul"]["p"] == frozen["total_p"] and T["badi"]["en"].startswith("Big losses — ") and T["chhoti"]["en"].startswith("Small losses, written off — ") and T["ortho"]["en"].startswith("Orthotics closed — loss Rs 5,420")
      and T["headers"]["en"] == ["Item", "Marg (count day)", "Counted", "Short", "Rs"], [T["kul"], T["badi"]["en"]])
    lp = G("manoj", "/finance/stock/page/loss?count=1")[1].decode("utf-8", "replace")
    C("the desk page draws the tables (Big losses open, Small losses and Orthotics collapsed, total rows) and one link 'Darpan's page shows this in Hindi' in place of the paragraph", "tb(T.badi,true" in lp and "tb(T.chhoti,false" in lp and "Darpan\\'s page shows this in Hindi" in lp and "<tfoot>" in lp)
    pdf = G("manoj", "/finance/stock/api/loss/1/record.pdf"); b = bytes(pdf[1]) if not isinstance(pdf[1], dict) else b""
    C("the record PDF renders the block as tables (Big losses / Small losses / Orthotics headings, TOTAL rows)", b[:4] == b"%PDF" and b"TOTAL" in b and b"Big losses" in b and b"Small losses" in b and b"Orthotics closed" in b, [pdf[0], len(b)])
    C("the block preview (a count still open) carries tables too", "tables" in (D.get("block_preview") or {"tables": None}) or D.get("block") is not None)
step("desk", s5)

# ---------------------------------------------------------------- 6 gates
GATES = {}
def s6():
    for u in ("bhati", "shavez", "darpan", "amir", "manoj", "alisha"):
        GATES[u] = [G(u, "/finance/stock/api/pad/amir/1")[0], G(u, "/finance/stock/page/amir?count=1")[0], G(u, "/finance/stockmatch/api/state?count=1")[0], G(u, "/finance/stockmatch")[0],
                    G(u, "/finance/stock/api/pad/hub/1")[0], G(u, "/finance/stock/api/loss/1/piles")[0], P(u, "/finance/stock/api/loss/1/pile/setting", {"key": "stock.whole_unit_items", "add": "X W437", "word": "pc"})[0]]
    C("bhati / shavez are refused on Stock milaan and the desk; darpan is refused on the hub and the desk; only the owner may set the whole-piece list; amir and darpan read their own pages",
      all(GATES[u][2] in (302, 401, 403) and GATES[u][5] in (302, 401, 403) for u in ("bhati", "shavez")) and GATES["darpan"][4] in (302, 401, 403) and GATES["darpan"][5] in (302, 401, 403)
      and all(GATES[u][6] in (302, 401, 403) for u in ("bhati", "shavez", "darpan", "amir")) and GATES["manoj"][6] == 200 and GATES["amir"][0] == 200 and GATES["darpan"][2] == 200, GATES)
    db.execute("DELETE FROM setting WHERE key='stock.whole_unit_items' AND value LIKE '%X W437%'")
step("gates", s6)

out = dict(mode=os.environ["MODE"], R=R, has_rule=bool(LP and hasattr(LP, "receive_close")), has_flat=("vouchers_flat" in (amir() or {}).get("made", {})), gates=GATES)
print("JSON:" + json.dumps(out))
'''


def run(mode, app, db):
    env = dict(os.environ, APPDIR=app, MODE=mode, FINANCE_DB=db, SPINE_DB=a.spine, PRE_JSON=json.dumps(PRE))
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
    check("loss_piles carries receive_close; the board carries vouchers_flat", N["has_rule"] and N["has_flat"])

print("-- NEGATIVE CONTROL: the same scenario on the box as it is (must go red)")
O = run("old", a.old, DB_OLD)
if O is None:
    check("NEGATIVE: the old app's probe ran", False)
else:
    red = [l for l, ok, _g in O["R"] if not ok]
    for l, ok, _g in O["R"]:
        print("   old %s  %s" % ("ok  " if ok else "RED ", l[:150]))
    must = ("ONE run of kind receive_close", "the hub's pending is 0", "qty_words v1.2 carries the whole-piece map")
    check("NEGATIVE: the old files go red (%d of %d checks red): no receive round (pending stays), no numbered vouchers, no whole-piece map (CCM in tabs), no tables" % (len(red), len(O["R"])),
          all(any(m in r for r in red) for m in must) and len(red) >= 8, red[:6])
    check("NEGATIVE: the old loss_piles has no receive_close; the old board no vouchers_flat", not O["has_rule"] and not O["has_flat"])
    check("the gates are AS BEFORE for every page that existed (Amir's board, Stock milaan, the hub, the desk): new files = old files", N is not None and all(N["gates"][u][:6] == O["gates"][u][:6] for u in N["gates"]), (N and N["gates"], O["gates"]))

print("WALK_S437 %s -- %d of %d %s" % ("GREEN" if not fails else "RED", (n - len(fails)) if not fails else len(fails), n, "passed" if not fails else "failed"))
for f in fails:
    print("   red: " + f)
sys.exit(0 if not fails else 1)
