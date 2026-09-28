#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s436.py -- kit S436_STAFF_PAGES_CLEAN (D638). THE REAL finance_app.py (a copy of /root/finance carrying the kit's files) over
SCRATCH copies of the live finance.db and the spine, driven through Flask's test client with header identity (walk only). The round is
the REAL count #1 (its medicines closed 27-Sep; its orthotic section open until this kit). The kit's seed runs on the new copy first,
as the installer runs it on the live database. Every real line is found BY KEY from the section's own state BEFORE the seed (what
Darpan had answered by then, what he had not) -- never by a count fixed in this file, because he keeps answering on the live page.
Crafted rows are keyed W436*: a same-salt medicine pair (the matcher), and one orthotic short line nobody answered (the default path).
The SAME scenario then runs against the box as it is (--old): it must go red.

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


TODAY = dt.date.today()
# two crafted medicines of one salt, one short and one over: a same-salt pair the matcher proposes -- unless the salt is on the salt-fix list
CRAFT = (("W436 SALTA TAB", "1*10", 10, 40, 20, 1000), ("W436 SALTB TAB", "1*10", 10, 20, 40, 1000))
SALT = "W436SALT 10"
# one crafted ORTHOTIC short line nobody answered (no spine fact, no rate: unpriced) -- the seed's default path, whatever Darpan has done live
ORTHO = ("W436 WRIST BAND L", "1*1", 1, 4, 3)


def craft(db):
    c = sqlite3.connect(db, timeout=30)
    as_on = c.execute("SELECT marg_as_on FROM stock_count WHERE id=1").fetchone()[0]
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    eid = c.execute("SELECT id FROM day_entry WHERE unit='medical' ORDER BY id DESC LIMIT 1").fetchone()[0]
    c.execute("DELETE FROM sale_line_item WHERE unit='medical' AND bill_no LIKE 'W436%'")
    for i, (it, packing, ps, marg, cnt, mrp) in enumerate(CRAFT, 1):
        # one sale each this financial year (before the count day): a never-sold item sits in the 'dead' lane, which the matcher leaves out by design
        c.execute("INSERT INTO sale_line_item (day_entry_id, unit, business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, amount_p) VALUES (?,'medical','2026-09-01',?,0,1,?,?,?,'1:0',?)",
                  (eid, "W436A%03d" % i, it, norm_key(it), packing, mrp * ps))
    rows = [(it, packing, ps, marg, cnt, mrp, "Medicines") for it, packing, ps, marg, cnt, mrp in CRAFT] + [ORTHO + (None, "Orthotics")]
    for it, packing, ps, marg, cnt, mrp, sec in rows:
        c.execute("INSERT OR REPLACE INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,'walk W436')", (as_on, it, marg, packing, ps, now))
        c.execute("INSERT INTO stock_count_item (count_id, item, packing, pack_size, marg_qty, counted_qty, strips, loose, counted_by, entered_by, at) VALUES (1,?,?,?,?,?,0,0,'W436','W436',?)",
                  (it, packing, ps, marg, cnt, now))
        c.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, pack_size, value_p, cause, status, counted_by) VALUES (1,?,?,?,?,?,?,NULL,'UNEXPLAINED','open','W436')",
                  (it, as_on, marg, cnt, cnt - marg, ps))
        c.execute("INSERT OR REPLACE INTO stock_item_section (item_key, item, section, source, seeded_as, by_user, at) VALUES (?,?,?,'walk W436',?,'W436',?)", (norm_key(it), it, sec, sec, now))
        if mrp is not None:
            c.execute("INSERT OR REPLACE INTO stock_mrp_manual (item, mrp_p, source, set_by, set_at) VALUES (?,?,'walk W436','W436',?)", (it, mrp, now))
            c.execute("INSERT OR REPLACE INTO purchase_salt_marg (item_norm, item, salt, as_on, source_md5) VALUES (?,?,?,?,?)", (it, it, SALT, TODAY.isoformat(), "w436"))
    c.commit()
    c.close()


def pre_seed(db, app):
    """The orthotic section's open lines as the NEW files read them BEFORE the seed -- by key, from the section's own state."""
    os.environ["FINANCE_DB"] = db
    os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
    sys.path.insert(0, app)
    cwd = os.getcwd()
    os.chdir(app)
    import finance_app as fa                                  # noqa: PLC0415
    import stock_app                                          # noqa: PLC0415
    import stockmatch                                         # noqa: PLC0415
    out = dict(short=[], over=[], unanswered=[], by={})
    with fa.app.test_request_context():
        con = stock_app._db()
        d = stock_app._pad_report_data(con, 1)
        for l in stockmatch.lines_of(con, d):
            if not l["open"]:
                continue
            out["short" if l["side"] == "short" else "over"].append(l["item"])
            if not l["reasoned"]:
                out["unanswered"].append(l["item"])
            else:
                out["by"][l["item"]] = l["cause_by"]
    os.chdir(cwd)
    return out


DB_OLD = a.db + ".old"
copydb(a.db, DB_OLD)
craft(a.db)
craft(DB_OLD)
PRE = pre_seed(a.db, a.app)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seed_s436  # noqa: E402
assert seed_s436.seed(a.db, a.app) == 0, "seed failed"
print("-- scratch: crafted W436 rows (a same-salt pair; an unanswered orthotic short line) on both copies; before the seed the section had %d short and %d extra lines open, %d unanswered; the S436 seed ran on the new copy"
      % (len(PRE["short"]), len(PRE["over"]), len(PRE["unanswered"])))

PROBE = r'''
import json, os, sys, sqlite3, datetime as dt, re
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
import finance_app as fa
import stock_app
try:
    import stockmatch as SM
    import loss_piles as LP
    import stock_watch as SW
except Exception:
    SM = LP = SW = None
PRE = json.loads(os.environ["PRE_JSON"])
SHORT, OVER, UNANS, BY = PRE["short"], PRE["over"], PRE["unanswered"], PRE["by"]
CRAFTED = "W436 WRIST BAND L"
ANSWERED_SHORT = [i for i in SHORT if i not in UNANS]
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
        import traceback
        C(name + " -- the step ran", False, "%s: %s | %s" % (type(e).__name__, str(e)[:200], traceback.format_exc()[-400:]))
def strings(o, acc):
    if isinstance(o, dict):
        for v in o.values(): strings(v, acc)
    elif isinstance(o, list):
        for v in o: strings(v, acc)
    elif isinstance(o, str):
        acc.append(o)
REMOVED = re.compile(r"Toota\s*/?\s*kharab|Vaapas nahi aaya|Pata nahi|broken or damaged|went out, never came back|does not know|toota kharab", re.I)
UNITW = re.compile(r"\b(units?|yunit)\b", re.I)
def hits(rx, texts):
    return [t[max(0, rx.search(t).start() - 30):rx.search(t).start() + 40] for t in texts if rx.search(t)]
def state(u="darpan"):
    r = G(u, "/finance/stockmatch/api/state?count=1"); return r[1] if r[0] == 200 and isinstance(r[1], dict) else None
def hub():
    return G("manoj", "/finance/stock/api/pad/hub/1")[1]
def amir():
    return G("amir", "/finance/stock/api/pad/amir/1")[1]
def needs():
    r = G("manoj", "/finance/sanjeevni/api/needs-you"); return [l["text"] for l in (r[1] or {}).get("lines", [])] if r[0] == 200 else []
KNOWN_PRICE = {"ANKLE BINDER BAMBOO L": 32500, "L S BELT CONT GRAY UNISON XXX": 278000}     # 1 pc x Rs 325 (spine S.RATE); 2 pcs x Rs 1,390
KNOWN_UNPRICED = ["FINGER COT SPILNT REMEDE", "SOFT COLLAR BODY AID S"]
S = {}

# ---------------------------------------------------------------- 1 Darpan's page: one answer a side; the seed's conversions; the removed words gone
def s1():
    st = state(); S["st"] = st
    L = {l["item"]: l for l in st["lines"]}
    C("Stock milaan answers Darpan; every short orthotic line offers exactly ONE answer (Galti se bill nahi bana), every extra line exactly ONE (Bill bana, diya nahi)",
      bool(st) and all([r["key"] for r in l["reasons"]] == ["BILLING"] for l in st["lines"] if l["side"] == "short") and all([r["key"] for r in l["reasons"]] == ["BILLED_NOT_GIVEN"] for l in st["lines"] if l["side"] == "over"),
      [(l["item"], [r["key"] for r in l["reasons"]]) for l in st["lines"] if len(l["reasons"]) != 1][:3])
    pg = G("darpan", "/finance/stockmatch")[1]
    acc = [pg.decode("utf-8", "replace")]                       # the page as served, every button the state offers, every word on a line Darpan can still tap
    for l in st["lines"]:
        strings(l["reasons"], acc)
        if l["open"] or l["defaulted"]:
            acc += [l.get("cause_hi") or "", l.get("cause_en") or "", l.get("cause_note") or ""]
    strings({k: v for k, v in st.items() if k not in ("lines", "pairs", "block", "recounts", "claims", "claim_answers", "watch")}, acc)
    C("the removed words (Toota / kharab, Vaapas nahi aaya, Pata nahi, broken or damaged, went out never came back, does not know) appear nowhere on the rendered page, in the buttons offered or on a line Darpan can tap (an old settled row keeps its own label, as the brief says)",
      not hits(REMOVED, acc), hits(REMOVED, acc)[:3])
    allk = SHORT + OVER
    rows = {r["item"]: r for r in q("SELECT item, cause, cause_by, cause_note, status FROM stock_diff WHERE count_id=1 AND item IN (%s)" % ",".join("?" * len(allk)), *allk)}
    C("the seed converted every open short orthotic line (%d) to 'sold, no bill was made': the %d Darpan had answered keep his name with the rule in the note, the %d unanswered read 'default -- Darpan ne nahi likha'" % (len(SHORT), len(ANSWERED_SHORT), len([i for i in UNANS if i in SHORT])),
      SHORT and all(rows[i]["cause"] == "BILLING" for i in SHORT) and all(rows[i]["cause_by"] == BY[i] and rows[i]["cause_note"].startswith("rule D638, 28-Sep") for i in ANSWERED_SHORT)
      and all(rows[i]["cause_note"].startswith("rule D638 default") for i in UNANS if i in SHORT), {i: (rows[i]["cause"], rows[i]["cause_by"], rows[i]["cause_note"][:40]) for i in SHORT})
    C("the %d open extra lines (%s) read 'billed, not handed over'" % (len(OVER), ", ".join(OVER)), OVER and all(rows[i]["cause"] == "BILLED_NOT_GIVEN" for i in OVER), {i: rows[i]["cause"] for i in OVER})
    C("every conversion is audited (stock_diff / cause_rule by 'rule D638, 28-Sep'): %d rows" % len(allk), q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_diff' AND action='cause_rule' AND by_whom='rule D638, 28-Sep'")[0]["n"] == len(allk))
    d2 = [l for l in st["lines"] if l["defaulted"]]
    C("the defaulted lines (the ones nobody answered: %s) are marked on his page (defaulted, not locked) and stay tappable" % ", ".join(sorted(UNANS)), sorted(l["item"] for l in d2) == sorted(UNANS) and all(not l["locked"] for l in d2) and CRAFTED in UNANS, [(l["item"], l["locked"]) for l in d2])
    l0 = L[CRAFTED]
    other = ANSWERED_SHORT[0]
    r = P("darpan", "/finance/stockmatch/api/reason?count=1", {"diff_id": l0["diff_id"], "reason": "BILLING"})
    row = q("SELECT cause, cause_by, cause_note FROM stock_diff WHERE id=?", l0["diff_id"])[0]
    C("Darpan taps the defaulted %s: recorded as his (BILLING by darpan), no longer defaulted; a tap on a closed non-defaulted line (%s) is refused (409)" % (CRAFTED, other),
      r[0] == 200 and row["cause"] == "BILLING" and row["cause_by"] == "darpan" and not any(l["item"] == CRAFTED and l["defaulted"] for l in state()["lines"])
      and P("darpan", "/finance/stockmatch/api/reason?count=1", {"diff_id": L[other]["diff_id"], "reason": "BILLING"})[0] == 409, [r[0], row])
    other2 = ANSWERED_SHORT[-1]
    r = P("manoj", "/finance/stockmatch/api/reason?count=1", {"diff_id": L[other2]["diff_id"], "reason": "BILLING"})
    C("the owner's one-tap word still lands through the same door on any orthotic line (%s: BILLING by manoj, audited)" % other2, r[0] == 200 and q("SELECT cause_by FROM stock_diff WHERE id=?", L[other2]["diff_id"])[0]["cause_by"] == "manoj"
      and q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='stock_diff' AND row_id=? AND action='cause' AND by_whom='manoj'", L[other2]["diff_id"])[0]["n"] == 1, r)
    C("a removed reason on an orthotic line is refused (400)", P("manoj", "/finance/stockmatch/api/reason?count=1", {"diff_id": L[other]["diff_id"], "reason": "BREAKAGE"})[0] == 400)
    C("the 22 renames are nowhere on Darpan's page", b"Naam badlo" not in pg and b"rename" not in pg.lower())
step("darpan", s1)

# ---------------------------------------------------------------- 2 the section closed by rule: the loss, the run, the round, the hub, Needs you, the statement, the block
def s2():
    st = state("manoj"); S["st2"] = st
    run = q("SELECT id, at, by_user, lines_n, mrp_p, cost_p, unpriced, groups, kind, round_no FROM stock_writeoff_run WHERE count_id=1 AND kind='ortho_close'")
    C("the section CLOSED by rule: one stock_section_close row (basis rule D638), section_state.closed and closed_by_rule, the verdict reads 'CLOSED by rule'",
      len(q("SELECT * FROM stock_section_close WHERE count_id=1 AND section='Orthotics'")) == 1 and "rule" in (q("SELECT basis FROM stock_section_close WHERE count_id=1")[0]["basis"] or "")
      and st["closed"] and st["closed_by_rule"] and st["verdict_en"].startswith("Orthotics section: CLOSED by rule on"), st["verdict_en"])
    g = json.loads(run[0]["groups"]) if run else {}
    S["run"] = run[0] if run else None
    loss = g.get("ortho_loss", []); fix = g.get("ortho_fix", [])
    priced = {x["item"]: x["mrp_p"] for x in loss}
    NS, NU, RS = len(loss), sum(1 for x in loss if x["mrp_p"] is None), stock_app._loss_rs(run[0]["mrp_p"] if run else 0)
    S.update(NS=NS, NU=NU, RS=RS, unpriced=sorted(x["item"] for x in loss if x["mrp_p"] is None))
    C("ONE run of kind ortho_close: the %d short lines under ortho_loss (one row per short line, at selling price), the %d extra under ortho_fix; by 'rule D638, 28-Sep'" % (len(SHORT), len(OVER)),
      len(run) == 1 and sorted(x["item"] for x in loss) == sorted(SHORT) and sorted(x["item"] for x in fix) == sorted(OVER) and run[0]["by_user"] == "rule D638, 28-Sep", {k: len(v) for k, v in g.items()})
    C("the loss at SELLING PRICE (the statement's rule): ANKLE BINDER BAMBOO L 1 pc x Rs 325 = Rs 325 (spine S.RATE); L S BELT XXX 2 pcs x Rs 1,390 = Rs 2,780; FINGER COT SPILNT REMEDE, SOFT COLLAR BODY AID S and the crafted line carry no rupee (%d without a price); the run's total %s = the sum of its rows" % (NU, RS),
      all(priced.get(i) == p for i, p in KNOWN_PRICE.items() if i in priced) and all(priced.get(i) is None for i in KNOWN_UNPRICED + [CRAFTED] if i in priced) and CRAFTED in priced
      and run[0]["mrp_p"] == sum(x["mrp_p"] or 0 for x in loss) and run[0]["unpriced"] == NU and run[0]["mrp_p"] > 0, [priced, run[0]["mrp_p"], run[0]["unpriced"]])
    W = {r["item"]: r for r in q("SELECT item, action, note FROM stock_diff_lane WHERE count_id=1 AND id IN (SELECT MAX(id) FROM stock_diff_lane WHERE count_id=1 GROUP BY item)")}
    C("every short line carries the lane word WRITE_OFF ('rule D638 ... orthotic loss'), every extra line MARG_FIX ('book correction'); all %d stock_diff rows closed" % (len(SHORT) + len(OVER)),
      all(W.get(i, {}).get("action") == "WRITE_OFF" and "orthotic loss" in W[i]["note"] for i in SHORT) and all(W.get(i, {}).get("action") == "MARG_FIX" and "book correction" in W[i]["note"] for i in OVER)
      and all(r["status"] == "closed" for r in q("SELECT status FROM stock_diff WHERE count_id=1 AND item IN (%s)" % ",".join("?" * (len(SHORT) + len(OVER))), *(SHORT + OVER))), [(i, W.get(i, {}).get("action")) for i in SHORT + OVER if W.get(i, {}).get("action") not in ("WRITE_OFF", "MARG_FIX")])
    rno = run[0]["round_no"]; S["rno"] = rno
    vl = q("SELECT item, kind, batch_no, change FROM stock_voucher_line WHERE count_id=1 AND round_no=?", rno)
    secs = {r["item"]: r["section"] for r in q("SELECT item, section FROM stock_item_section")}
    per = {}
    for x in vl:
        per[(x["kind"], x["batch_no"])] = per.get((x["kind"], x["batch_no"]), 0) + 1
    C("the orthotic round %s was made WITHOUT a tap: every line an orthotic, every rule line in it (one line an item), at most %d lines a voucher" % (rno, LP.settings(db)["voucher_batch"]),
      rno and all(secs.get(x["item"]) == "Orthotics" for x in vl) and {x["item"] for x in vl} >= set(SHORT + OVER) and max(per.values()) <= LP.settings(db)["voucher_batch"], [rno, len(vl), max(per.values()) if per else None])
    C("no orthotic line is left to voucher; the medicines' pending lines are untouched (still waiting for their own decision)", st["vouchers"]["pending"] == 0 and len(stock_app._voucher_pending(db, stock_app._pad_report_data(db, 1))) > 0)
    hb = hub()
    C("the hub's orthotic block says CLOSED with the totals: loss text '%d lines short, %s at selling price (%d without a price); the round %s on Amir's board'" % (NS, RS, NU, rno),
      hb["ortho"]["closed"] and hb["ortho"]["loss"]["n_short"] == NS and hb["ortho"]["loss"]["rs"] == RS and hb["ortho"]["loss"]["unpriced"] == NU and "round %d" % rno in hb["ortho"]["loss"]["text"], hb["ortho"].get("loss"))
    head = "Orthotics closed: %d line%s short, %s at selling price" % (NS, "" if NS == 1 else "s", RS)
    C("Needs you carries ONE line: '%s (...); round %s of N lines on Amir's board'" % (head, rno), sum(1 for t in needs() if t.startswith(head) and ("round %d of" % rno) in t) == 1
      and q("SELECT COUNT(*) AS n FROM stock_watch_notice WHERE kind='ortho_closed'")[0]["n"] == 1, [t for t in needs() if "Orthotics" in t])
    Dst = G("manoj", "/finance/stock/api/statement/1")[1]
    ort = [s for s in Dst["sections"] if s["key"] == "Orthotics"][0]
    bl = {l["item"]: l for l in ort["lines"] + ort["matched"]}
    rx = re.compile(r"\b%d\b" % rno)
    C("the statement's Orthotics section reads the outcome: every short line 'orthotic loss -- sold without bill' on its voucher round (%s), every extra line 'book correction -- billed, not handed over' (a Marg-negative one keeps S432's book-correction text); none of them 'open'" % rno,
      all(bl[i]["became"].startswith("orthotic loss -- sold without bill") and rx.search(bl[i]["voucher"]) and not bl[i]["open"] for i in SHORT)
      and all((bl[i]["became"].startswith("book correction") or bl[i]["became"].startswith("Marg negative -- book correction")) and not bl[i]["open"] for i in OVER)
      and any(bl[i]["became"].startswith("book correction -- billed") for i in OVER), [(i, bl[i]["became"], bl[i]["voucher"]) for i in SHORT[:2] + OVER])
    C("the statement's block: no orthotic line still open with Darpan, none awaiting the owner's word", ort["block"]["open_lines"] == 0 and ort["block"]["await_owner"] == 0, ort["block"])
    B = LP.block_view(db, 1)
    frozen = q("SELECT total_p, small_p, big_p FROM stock_staff_block WHERE count_id=1 ORDER BY id DESC LIMIT 1")[0]
    en4 = "Orthotics — %s (%d line%s, bina bill)%s" % (RS, NS, "" if NS == 1 else "s", (" · %d without a price" % NU) if NU else "")
    hi4 = "Orthotics — %s (%d line, bina bill)%s" % (RS, NS, (" · %d bina daam" % NU) if NU else "")
    C("the staff block gains ONE line at its foot -- '%s' (Hindi: 'bina daam') -- and its first three lines still read the frozen medicine figures (total %s)" % (en4, frozen["total_p"]),
      len(B["lines_en"]) == 4 and B["lines_en"][3] == en4 and B["lines_hi"][3] == hi4
      and LP._rs(frozen["total_p"]) in B["lines_en"][0] and LP._rs(frozen["small_p"]) in B["lines_en"][1] and LP._rs(frozen["big_p"]) in B["lines_en"][2], B["lines_en"])
    C("Darpan's Stock milaan shows the foot line under the block", len(S["st"]["block"]["lines_hi"]) == 4 and S["st"]["block"]["lines_hi"][3].startswith("Orthotics"), S["st"]["block"]["lines_hi"])
    D = G("manoj", "/finance/stock/api/loss/1/piles")[1]
    C("the Loss desk's medicine figures are unchanged: written off 136 lines (the orthotics are never merged), count #1's medicine run untouched (122 lines)",
      D["totals"]["written_off"]["n"] == 136 and D["done"]["written_off"] and q("SELECT lines_n, mrp_p FROM stock_writeoff_run WHERE count_id=1 AND id=1")[0]["lines_n"] == 122 and D["record"]["runs"][-1]["kind"] == "ortho_close" and "Orthotics closed by rule" in D["record"]["runs"][-1]["kind_text"],
      [D["totals"]["written_off"]["n"], [r["kind"] for r in D["record"]["runs"]]])
    per_ = SW.count_periods(db)
    med = json.loads(q("SELECT groups FROM stock_writeoff_run WHERE id=1")[0]["groups"])
    med_loss = sum((x.get("cost_p") or x.get("mrp_p") or 0) for k in ("allowance", "small", "big") for x in med.get(k, []))
    C("the leakage period line and the cadence rule ignore the orthotic run (allowance + small + big only): the period's loss equals the medicine run's; no stock_watch_adjust row for the orthotic run",
      per_ and per_[-1]["loss_p"] == med_loss and not q("SELECT 1 FROM stock_watch_adjust WHERE run_id=?", run[0]["id"]), [per_ and per_[-1]["loss_p"], med_loss])
    pdf = G("manoj", "/finance/stock/api/loss/1/record.pdf"); b = bytes(pdf[1]) if not isinstance(pdf[1], dict) else b""
    C("the record PDF prints the foot line and the orthotic run", b[:4] == b"%PDF" and (("Orthotics - %s" % RS).encode("latin-1") in b.replace(b"\xe2\x80\x94", b"-") or (b"Orthotics" in b and b"closed by rule" in b)), [pdf[0], len(b)])
    r = P("manoj", "/finance/stock/api/pad/vouchers/1/make", {"section": "Orthotics"})
    C("Make the orthotic round again: nothing waiting (the rule already made it); a second close by rule finds the run (idempotent)", r[0] == 200 and r[1]["round_no"] is None and SM.close_by_rule(db, stock_app._pad_report_data(db, 1)).get("already"), r[1])
step("close", s2)

# ---------------------------------------------------------------- 3 the wrong-salt pairs; the matcher and the salt-fix list
def s3():
    m = {(r["short_item"], r["over_item"]): r for r in q("SELECT short_item, over_item, answer, note, by_user FROM stock_match WHERE count_id=1 AND id IN (SELECT MAX(id) FROM stock_match WHERE count_id=1 GROUP BY short_item, over_item)")}
    C("ETOZOX 90 <-> PARI CR 12.5 stands NO with the note 'not a swap -- salt wrong in Marg'; LACTOVAX SYP <-> LINVIZ 600 and <-> FEBUTAL the same (their NO kept)",
      all(m.get(k, {}).get("answer") == "NO" and "salt wrong in Marg" in (m.get(k, {}).get("note") or "") for k in (("ETOZOX 90", "PARI CR 12.5"), ("LACTOVAX SYP", "LINVIZ 600"), ("LACTOVAX SYP", "FEBUTAL"))),
      {"%s <-> %s" % k: (v["answer"], (v["note"] or "")[:40]) for k, v in m.items() if "LACTOVAX" in k[0] or k[0] == "ETOZOX 90"})
    d = stock_app._pad_report_data(db, 1)
    items = {x for p in d["matches"] for x in (p["short"], p["over"])}
    C("the matcher proposes no pair on an item whose salt is on the OPEN salt-fix list (PARI CR 12.5, LINVIZ 600, LACTOVAX SYP, JARDIANCE 25)", not (items & {"PARI CR 12.5", "LINVIZ 600", "LACTOVAX SYP", "JARDIANCE 25"}), sorted(items & {"PARI CR 12.5", "LINVIZ 600", "LACTOVAX SYP", "JARDIANCE 25"}))
    C("the crafted same-salt pair W436 SALTA TAB / W436 SALTB TAB IS proposed (its salt is on no fix list)", any(p["short"] == "W436 SALTA TAB" and p["over"] == "W436 SALTB TAB" for p in d["matches"]), [(p["short"], p["over"]) for p in d["matches"] if "W436" in p["short"]])
    db.execute("INSERT INTO purchase_salt_task (section, seq, a, b, c, source_md5, pushed_at) VALUES ('change', 999, 'W436 SALTA TAB', ?, 'W436 RIGHT SALT', 'S436-owner-walk', ?)", ("W436SALT 10", dt.datetime.now().isoformat())); db.commit()
    d = stock_app._pad_report_data(db, 1)
    C("a salt fix opened on W436 SALTA TAB -> the pair is no longer proposed", not any("W436" in p["short"] for p in d["matches"]))
    db.execute("UPDATE purchase_salt_marg SET salt='W436 RIGHT SALT' WHERE item_norm='W436 SALTA TAB'"); db.execute("UPDATE purchase_salt_marg SET salt='W436 RIGHT SALT' WHERE item_norm='W436 SALTB TAB'"); db.commit()
    am = amir()
    sf = {x["item"]: x for x in am["salt_fix"]}
    d = stock_app._pad_report_data(db, 1)
    C("Marg's next salt list shows the fix -> the task reads done in Marg on Amir's board and the pair is proposed again", sf.get("W436 SALTA TAB", {}).get("marg_done") and any("W436" in p["short"] for p in d["matches"]), sf.get("W436 SALTA TAB"))
    db.execute("DELETE FROM purchase_salt_task WHERE a='W436 SALTA TAB'"); db.commit()
step("pairs", s3)

# ---------------------------------------------------------------- 4 Amir's board: four sections, only his work
def s4():
    am = amir(); S["am"] = am
    sf = {x["item"]: x for x in am["salt_fix"]}
    C("the four salt fixes are seeded (purchase_salt_task, section 'change', the owner's source) with what Marg's list says today: JARDIANCE 25 ETOROCOXIB 90 -> EMPAGLIFLOZIN 25, PARI CR 12.5 -> PAROXETINE CR 12.5, LACTOVAX SYP FEBUXOSTAT 40 -> LAXATIVE (LACTULOSE), LINVIZ 600 -> LINEZOLID 600; all open",
      sorted(sf) == ["JARDIANCE 25", "LACTOVAX SYP", "LINVIZ 600", "PARI CR 12.5"] and sf["JARDIANCE 25"]["salt_new"] == "EMPAGLIFLOZIN 25" and sf["JARDIANCE 25"]["marg_now"] == "ETOROCOXIB 90" and sf["PARI CR 12.5"]["salt_new"] == "PAROXETINE CR 12.5"
      and sf["LACTOVAX SYP"]["salt_new"] == "LAXATIVE (LACTULOSE)" and sf["LACTOVAX SYP"]["marg_now"] == "FEBUXOSTAT 40" and sf["LINVIZ 600"]["salt_new"] == "LINEZOLID 600" and all(not x["marg_done"] for x in sf.values())
      and q("SELECT COUNT(*) AS n FROM audit_log WHERE table_name='purchase_salt_task' AND action='salt_fix_seed'")[0]["n"] == 4, {k: (v["marg_now"], v["salt_new"], v["state"]) for k, v in sf.items()})
    C("Rate daalo names exactly the orthotic short lines the loss could not price (%s)" % ", ".join(S["unpriced"]), sorted(x["item"] for x in am["rate_tasks"]) == S["unpriced"] and "FINGER COT SPILNT REMEDE" in S["unpriced"], am["rate_tasks"])
    orno = S["rno"]
    secs = {r["item"]: r["section"] for r in q("SELECT item, section FROM stock_item_section")}
    byr = {}
    for r in q("SELECT round_no, item FROM stock_voucher_line WHERE count_id=1"):
        byr.setdefault(r["round_no"], set()).add(secs.get(r["item"], "Medicines"))
    ortho_rounds = sorted(r for r, s in byr.items() if s == {"Orthotics"}); earlier = sorted((r for r in byr if r not in ortho_rounds), reverse=True)
    C("the rounds in the board's order: the earlier rounds newest first (%s), then the orthotic rounds (%s, the rule's round %s last); Naam badlo hidden until every earlier round is entered and the orthotic round exists" % (earlier, ortho_rounds, orno),
      am["rounds_order"] == earlier + ortho_rounds and orno in ortho_rounds and am["renames_ready"] is False and am["renames_wait_hi"].startswith("नाम बदलना — बाद में"), [am["rounds_order"], am["renames_ready"], am["renames_wait_hi"]])
    C("the closing-stock line reads 'अभी बाकी' (the vouchers are not entered yet); the orthotic loss rides the board's JSON", am["proof_hi"].startswith("अभी बाकी") and am["ortho"] and am["ortho"]["n_short"] == S["NS"] and am["ortho"]["round_no"] == orno, [am["proof_hi"], am["ortho"]])
    pg = G("amir", "/finance/stock/page/amir?count=1")[1]
    txt = pg.decode("utf-8", "replace")
    C("the page: the four Hindi sections in order (वाउचर — Marg में डालने हैं · वाउचर के बाद — Marg से closing stock निकालें · सुधार — Marg में ठीक करना है · बाकी काम), 'Marg में डाल दिया', Salt theek karo / Rate daalo / Naam badlo",
      all(w in txt for w in ("वाउचर — Marg में डालने हैं", "वाउचर के बाद — Marg से closing stock निकालें", "सुधार — Marg में ठीक करना है", "बाकी काम", "Marg में डाल दिया", "Salt theek karo", "Rate daalo", "Naam badlo"))
      and txt.find("वाउचर — Marg में डालने हैं") < txt.find("वाउचर के बाद") < txt.find("सुधार — Marg") < txt.find(">बाकी काम<"), None)
    gone = ("Waiting to go on a voucher", "What is behind them", "Reports the server still needs from Marg", "Type Darpan", "Orthotics — by family", "Orthotics by family", "This list as Excel", "Marg cleanup list", ".xlsx")
    C("removed from the page: the waiting list, the Excel links, 'What is behind them', old section 1 / 3 / 5", not [w for w in gone if w in txt], [w for w in gone if w in txt])
    C("the upload box stays as the fallback ('रिपोर्ट यहाँ भी भेज सकते हैं'); the S221 lookups, the tranches and the families still ride the JSON for the owner (the page does not show them)",
      "रिपोर्ट यहाँ भी भेज सकते हैं" in txt and "lookups" in am and "tranches" in am and "ortho_families" in am and "Reports the server" not in txt)
    # Marg mein daal diya: every voucher of every round, with Marg's number -> a finished round collapses; then Naam badlo shows
    ent, n0 = [], q("SELECT COUNT(*) AS n FROM stock_voucher_entered")[0]["n"]
    for r in am["made"]["rounds"]:
        for b in r["batches"]:
            if not b["entered"]:
                ent.append(P("amir", "/finance/stock/api/pad/vouchers/1/entered", {"round": r["round_no"], "kind": b["kind"], "batch": b["batch_no"], "marg_voucher_no": "W436-%d-%s-%d" % (r["round_no"], b["kind"][0], b["batch_no"])})[0])
    am2 = amir()
    C("'Marg में डाल दिया' records Marg's voucher number per voucher (%d entered, 200 each); every round is closed (collapses); the numbers are in stock_voucher_entered" % len(ent),
      ent and all(x == 200 for x in ent) and all(r["closed"] for r in am2["made"]["rounds"]) and q("SELECT COUNT(*) AS n FROM stock_voucher_entered")[0]["n"] == n0 + len(ent), [len(ent), [(r["round_no"], r["closed"]) for r in am2["made"]["rounds"]]])
    C("with the orthotic round made and every earlier round entered, Naam badlo (23) is shown, ready", am2["renames_ready"] is True and len(am2["renames"]["rows"]) == 23 and G("amir", "/finance/stock/page/amir?count=1")[1].decode("utf-8", "replace").count("Naam badlo") >= 1)
    hb = hub()
    C("the hub's four follow-ups after Amir's entries: vouchers green; the proof still waits for Marg's next export; the renames red; the section stays CLOSED by rule",
      [c for c in hb["ortho"]["conds"] if c["key"] == "vouchers"][0]["ok"] and not [c for c in hb["ortho"]["conds"] if c["key"] == "renames"][0]["ok"] and hb["ortho"]["closed"], [(c["key"], c["ok"]) for c in hb["ortho"]["conds"]])
    C("the closing-stock line after the entries: 'वाउचर डल गए, Marg का अगला closing stock export आने दें'", "अगला closing stock export" in am2["proof_hi"], am2["proof_hi"])
    acc = []; strings(am2, acc)
    C("no 'unit(s)' on Amir's board JSON or page", not hits(UNITW, acc + [txt]), hits(UNITW, acc + [txt])[:3])
step("amir", s4)

# ---------------------------------------------------------------- 5 gates
GATES = {}
def s5():
    for u in ("bhati", "shavez", "darpan", "amir", "manoj", "alisha"):
        GATES[u] = [G(u, "/finance/stock/api/pad/amir/1")[0], G(u, "/finance/stock/page/amir?count=1")[0], G(u, "/finance/stockmatch/api/state?count=1")[0], G(u, "/finance/stockmatch")[0],
                    G(u, "/finance/stock/api/pad/hub/1")[0], P(u, "/finance/stock/api/pad/rename/tick", {"old": "NOT A RENAME W436"})[0]]
    C("bhati / shavez are refused on Stock milaan; darpan is refused on the hub; the owner reads the hub, Stock milaan and Amir's board; amir and darpan read their own pages",
      all(GATES[u][2] in (302, 401, 403) and GATES[u][3] in (302, 401, 403) for u in ("bhati", "shavez")) and GATES["darpan"][4] in (302, 401, 403)
      and GATES["manoj"][0] == 200 and GATES["manoj"][2] == 200 and GATES["manoj"][4] == 200 and GATES["amir"][0] == 200 and GATES["amir"][1] == 200 and GATES["darpan"][2] == 200 and GATES["darpan"][3] == 200, GATES)
step("gates", s5)

out = dict(mode=os.environ["MODE"], R=R, has_rule=bool(SM and hasattr(SM, "close_by_rule")), gates=GATES)
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
    check("stockmatch carries close_by_rule", N["has_rule"])

print("-- NEGATIVE CONTROL: the same scenario on the box as it is (must go red)")
O = run("old", a.old, DB_OLD)
if O is None:
    check("NEGATIVE: the old app's probe ran", False)
else:
    red = [l for l, ok, _g in O["R"] if not ok]
    for l, ok, _g in O["R"]:
        print("   old %s  %s" % ("ok  " if ok else "RED ", l[:150]))
    must = ("Stock milaan answers Darpan; every short orthotic line offers exactly ONE answer", "the section CLOSED by rule", "ONE run of kind ortho_close")
    check("NEGATIVE: the old files go red (%d of %d checks red): four reasons a line, no close by rule, no loss, the old board with its waiting list and Excel links" % (len(red), len(O["R"])),
          all(any(m in r for r in red) for m in must) and len(red) >= 6, red[:6])
    check("NEGATIVE: the old stockmatch has no close_by_rule", not O["has_rule"])
    check("the gates are AS BEFORE: the same status for bhati / shavez / darpan / amir / manoj / alisha on Amir's board, Stock milaan, the hub and the rename tick, new files = old files", N is not None and N["gates"] == O["gates"], (N and N["gates"], O["gates"]))

print("WALK_S436 %s -- %d of %d %s" % ("GREEN" if not fails else "RED", (n - len(fails)) if not fails else len(fails), n, "passed" if not fails else "failed"))
for f in fails:
    print("   red: " + f)
sys.exit(0 if not fails else 1)
