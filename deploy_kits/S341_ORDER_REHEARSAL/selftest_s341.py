#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_s341.py -- kit S341_ORDER_REHEARSAL (S274, Sanjeevni).

    python3 -B selftest_s341.py [--spine-dir /root/finance/spine]

Builds a scratch spine.db with the spine's own SCHEMA (spine_build.py, read from --spine-dir), fills it with a
few made-up items, sales, purchases and closings, runs the rehearsal for a date, and checks every rail on
figures worked by hand.  Then runs it again seven days later with one real-looking purchase and checks the
score.  Made to fail on purpose: a dead item, an internal-use item, a never_reorder item and the OFF flag.
Nothing outside the scratch folder is touched.
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS, FAILED = [], []


def ck(name, cond, detail=""):
    CHECKS.append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (("  -- " + str(detail)[:200]) if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine-dir", default="/root/finance/spine")
    a = ap.parse_args(argv)
    td = tempfile.mkdtemp(prefix="s341_")
    sb = load(os.path.join(a.spine_dir, "spine_build.py"), "spine_build_for_s341")
    orr = load(os.path.join(HERE, "order_rehearsal.py"), "order_rehearsal_s341")
    ck("the spine's SCHEMA is readable from %s" % a.spine_dir, "sp_move" in sb.SCHEMA)
    db = os.path.join(td, "spine.db")
    con = sqlite3.connect(db)
    con.executescript(sb.SCHEMA)
    today = dt.date(2026, 9, 19)
    con.execute("INSERT INTO sp_meta VALUES ('built', '2026-09-19T23:50:00+05:30')")
    # items: A fast mover (pack 10), B dead, C internal, D never_reorder, E single-source small
    for k, name, pack in (("ALPHA TAB", "ALPHA TAB", "1*10"), ("BETA CAP", "BETA CAP", "1*15"), ("BLADE", "BLADE", "1*1"),
                          ("GAMMA SYP", "GAMMA SYP", "100ML"), ("DELTA INJ", "DELTA INJ", "1*1")):
        con.execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", (k, name, pack, "PACK" if pack != "1*1" else "WHOLE", "2026-04-01", "2026-09-19"))
    # sales: ALPHA 20 units/day for 28 days (2 strips), DELTA 1/day on 4 days, BETA last sold 100 days ago, GAMMA 5/day
    d = today
    for i in range(28):
        day = (d - dt.timedelta(days=i)).isoformat()
        con.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", (day, "A%05d" % i, 1, "ALPHA TAB", "ALPHA TAB", "1*10", "2:0", 20.0, 1000, "", ""))
        con.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", (day, "A%05d" % i, 2, "GAMMA SYP", "GAMMA SYP", "100ML", "5", 5.0, 5000, "", ""))
        if i < 4:
            con.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", (day, "A%05d" % i, 3, "DELTA INJ", "DELTA INJ", "1*1", "1", 1.0, 30000, "", ""))
    con.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", ((today - dt.timedelta(days=100)).isoformat(), "A00001", 1, "BETA CAP", "BETA CAP", "1*15", "1:0", 15.0, 800, "", ""))
    # stock today: ALPHA 50 units, BETA 200, BLADE 3, GAMMA 10, DELTA 0
    for k, u in (("ALPHA TAB", 50.0), ("BETA CAP", 200.0), ("BLADE", 3.0), ("GAMMA SYP", 10.0), ("DELTA INJ", 0.0)):
        con.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (k, "2026-09-01", "opening", u, "test"))
        con.execute("INSERT INTO sp_close VALUES (?,?,?,?)", ("2026-09-17", k, u, "x"))
    # purchases: ALPHA from S1 and S2 (two suppliers), 10-pack lots at Rs 80/strip; DELTA from S1 only; S1 buys ~Rs 30,000/month (fortnightly tier -> monthly)
    for j, (sup, day, amt) in enumerate((("S1", "2026-08-20", 900000), ("S2", "2026-09-01", 300000), ("S1", "2026-09-10", 1200000))):
        con.execute("INSERT INTO sp_purchase_bill VALUES (?,?,?,?,?,?,?)", ("Supplier " + sup, sup, "B%d" % j, day, amt, "PURCHASE", "x"))
        con.execute("INSERT INTO sp_purchase_line VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (sup, "B%d" % j, day, 1, "ALPHA TAB", "ALPHA TAB", "1*10", 10.0, 0.0, 100.0, 80000, 80000, "PURCHASE", "x"))
        if sup == "S1":
            con.execute("INSERT INTO sp_purchase_line VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (sup, "B%d" % j, day, 2, "DELTA INJ", "DELTA INJ", "1*1", 5.0, 0.0, 5.0, 100000, 100000, "PURCHASE", "x"))
    con.commit()
    con.close()
    out = os.path.join(td, "orders")
    rules = os.path.join(td, "order_rules.json")
    logs = []
    rc = orr.run(db, out, rules, today, log=logs.append)
    ck("the rehearsal runs and writes the default rules file", rc == 0 and os.path.exists(rules))
    r = json.load(open(os.path.join(out, "order_rehearsal_2026-09-19.json")))
    L = {l["key"]: l for l in r["lines"]}
    H = {l["key"]: l for l in r["held"]}
    # ALPHA: rate 20/day; S2 was the LAST supplier (2026-09-01)? no -- S1 bought again 09-10, so vendor S1; two suppliers -> not single;
    # S1 cadence: Rs 21,000 in 90 d -> monthly_p 7,000 -> monthly (30 d); cover 30+2+3 = 35 -> target 700 - 50 = 650 units -> 65 strips -> box GCD(10,10,10)=10 -> 70
    al = L.get("ALPHA TAB")
    ck("ALPHA: 20/day, cover 35 d, needs 650 units -> 65 strips rounded to a box of 10 = 70 strips = 700 units",
       al and al["rate_per_day"] == 20.0 and al["cover_days"] == 35 and al["order_strips"] == 70 and al["order_units"] == 700 and not al["single_source"], al)
    ck("ALPHA: value = 70 strips x 10 units x Rs 8/unit = Rs 5,600 (paise 560000); vendor S1; confidence high",
       al and al["value_p"] == 560000 and al["vendor"] == "Supplier S1" and al["confidence"] == "high", al)
    ck("BETA: nothing sold for 100 days -> not on the order", "BETA CAP" not in L and "BETA CAP" not in H)
    ck("GAMMA: 5/day, 10 on hand, no supplier known, no cost -> a line with Rs 0 value is dropped as under Rs 50 while stock remains",
       "GAMMA SYP" not in L, L.get("GAMMA SYP"))
    de = L.get("DELTA INJ")
    ck("DELTA: single source (+3 d), thin (4 sell days) -> CONFIRM, out of stock so the small-line rail does not drop it",
       de and de["single_source"] and de["cover_days"] == 38 and de["confirm"] and de["order_strips"] >= 1, de)
    ck("BLADE is internal use (S235 seed) and never on the order", "BLADE" not in L)
    txt = open(os.path.join(out, "order_rehearsal_latest.txt")).read()
    ck("the text says NOT AN ORDER and that the rules are unapproved defaults", "NOT AN ORDER" in txt and "not approved" in txt)
    ck("no score yet on the first night", r["score"] is None and "no proposal from 7 nights ago" in txt)
    # the owner's list: never_reorder GAMMA and on_demand DELTA
    json.dump({"version": 2, "never_reorder": ["GAMMA SYP"], "on_demand": ["DELTA INJ"], "internal_use": ["BLADE"], "orthotics_cycle": []}, open(rules, "w"))
    rc = orr.run(db, out, rules, today, log=logs.append)
    r2 = json.load(open(os.path.join(out, "order_rehearsal_2026-09-19.json")))
    H2 = {l["key"]: l for l in r2["held"]}
    ck("NEGATIVE: an on_demand item is held back with its reason, not ordered", "DELTA INJ" in H2 and "patient" in H2["DELTA INJ"]["held"]
       and all(l["key"] != "DELTA INJ" for l in r2["lines"]), H2.get("DELTA INJ"))
    ck("the rules version is recorded", r2["rules_version"] == 2)
    # seven nights later: ALPHA bought 500 units from S1 on the 22nd; nothing else
    con = sqlite3.connect(db)
    con.execute("INSERT INTO sp_purchase_bill VALUES (?,?,?,?,?,?,?)", ("Supplier S1", "S1", "B9", "2026-09-22", 400000, "PURCHASE", "x"))
    con.execute("INSERT INTO sp_purchase_line VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("S1", "B9", "2026-09-22", 1, "ALPHA TAB", "ALPHA TAB", "1*10", 50.0, 0.0, 500.0, 400000, 400000, "PURCHASE", "x"))
    con.execute("INSERT INTO sp_purchase_line VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("S1", "B9", "2026-09-22", 2, "BETA CAP", "BETA CAP", "1*15", 2.0, 0.0, 30.0, 20000, 20000, "PURCHASE", "x"))
    con.commit()
    con.close()
    later = today + dt.timedelta(days=7)
    rc = orr.run(db, out, rules, later, log=logs.append)
    r3 = json.load(open(os.path.join(out, "order_rehearsal_2026-09-26.json")))
    sc = r3["score"]
    ck("seven nights later the score reads the 19-Sep proposal: 1 proposed, 1 bought as proposed (ALPHA), 0 not bought, 1 bought not proposed (BETA)",
       sc and sc["proposal_date"] == "2026-09-19" and sc["proposed"] == 1 and sc["bought_as_proposed"] == 1 and sc["proposed_not_bought"] == 0 and sc["bought_not_proposed"] == 1, sc)
    # OFF flag
    open(os.path.join(a.spine_dir if False else td, "OFF"), "w").close()
    orr2 = load(os.path.join(HERE, "order_rehearsal.py"), "order_rehearsal_s341_off")
    orr2.OFF_FLAGS = (os.path.join(td, "OFF"),)
    logs2 = []
    rc = orr2.run(db, out, rules, later, log=logs2.append)
    ck("NEGATIVE: the OFF flag stops the run and says so", rc == 0 and logs2 and "switched off" in logs2[0], logs2)
    ck("no 10-digit number anywhere in the written files (F-185)", not __import__("re").search(r"(?<!\d)[6-9]\d{9}(?!\d)", open(os.path.join(out, "order_rehearsal_latest.txt")).read()))
    shutil.rmtree(td, ignore_errors=True)
    print("selftest: %d/%d" % (len(CHECKS) - len(FAILED), len(CHECKS)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
