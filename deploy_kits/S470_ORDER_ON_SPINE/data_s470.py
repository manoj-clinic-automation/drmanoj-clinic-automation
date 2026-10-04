#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s470.py -- kit S470_ORDER_ON_SPINE, the install's data step (after the files are placed and finance.db is backed up):

  settings   the six rows order_rules.ensure() inserts (INSERT OR IGNORE: a row that exists is left as it is), read back and printed
  the trial  what the kept files of orders/ hold after the install's backfill (order_rehearsal.py --from 2026-09-28, run by the installer):
             each day kept, its proposals and lines, and the week's score as it stands

    data_s470.py --fin /root/finance --db /root/finance/finance.db settings
    data_s470.py --orders /root/finance/spine/orders kept
spine.db is never written. Idempotent.
"""
import argparse
import json
import os
import sqlite3
import sys

KEYS = ("order.engine_source", "order.pace_days", "order.dead_after_days", "order.on_order_days", "order.in_transit_days", "order.lot_history_days")


def settings(fin, db):
    sys.path.insert(0, fin)
    os.chdir(fin)
    import order_rules                                         # noqa: PLC0415
    assert os.path.dirname(os.path.abspath(order_rules.__file__)) == os.path.abspath(fin)
    con = sqlite3.connect(db, timeout=60)
    con.row_factory = sqlite3.Row
    before = {r[0]: r[1] for r in con.execute("SELECT key, value FROM setting WHERE key IN (%s)" % ",".join("?" * len(KEYS)), KEYS)}
    order_rules.ensure(con)
    after = {r[0]: r[1] for r in con.execute("SELECT key, value FROM setting WHERE key IN (%s)" % ",".join("?" * len(KEYS)), KEYS)}
    con.close()
    for k in KEYS:
        print("   %-26s %s%s" % (k, after.get(k), "" if k in before else "   (new row)"))
    ok = all(k in after for k in KEYS) and all(after[k] == order_rules.SETTINGS[k][0] or k in before for k in KEYS)
    print("DATA_S470 settings %s -- %d of 6 rows, %d new" % ("DONE" if ok else "RED", len(after), len(set(after) - set(before))))
    return 0 if ok else 1


def kept(orders):
    days = sorted(n[len("order_rehearsal_"):-5] for n in os.listdir(orders) if n.startswith("order_rehearsal_2") and n.endswith(".json"))
    n_own = 0
    for d in days:
        try:
            j = json.load(open(os.path.join(orders, "order_rehearsal_%s.json" % d), encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if j.get("source") != "order_proposal":
            continue
        n_own += 1
        t = j.get("totals") or {}
        sc = j.get("score")
        print("   %s  kept: %d proposal(s) (%d fixed, %d interim), %d line(s), Rs %s%s" % (
            d, t.get("proposals", 0), t.get("fixed", 0), t.get("interim", 0), t.get("lines", 0), "{:,}".format(int(t.get("value_p") or 0) // 100),
            ("   · score of %s: proposed %d, bought %d, not bought %d, bought not proposed %d" % (
                sc["proposal_date"], sc["proposed"], sc["bought_as_proposed"], sc["proposed_not_bought"], sc["bought_not_proposed"])) if sc else ""))
    aside = os.path.join(orders, "before_S470")
    print("   S341's files of those nights kept aside in before_S470/: %d" % (len(os.listdir(aside)) if os.path.isdir(aside) else 0))
    try:
        w = json.load(open(os.path.join(orders, "order_score_latest.json"), encoding="utf-8"))
    except (OSError, ValueError):
        w = {}
    print("   order_score_latest.json (%s): bought on list %s%% · listed and bought within 14 days %s%% · stock-outs %s, listed in time %s · not bought Rs %s · "
          "days scored at 7: %s, at 14: %s · the first week is scored on the night of %s" % (
              w.get("date"), w.get("bought_on_list_pct"), w.get("listed_bought_pct"), w.get("stockouts"), w.get("stockouts_listed_in_time"),
              None if w.get("value_not_bought_p") is None else "{:,}".format(w["value_not_bought_p"] // 100), w.get("days_scored_7"), w.get("days_scored_14"),
              w.get("first_score_on")))
    print("DATA_S470 kept %s -- %d day(s) kept from order_proposal" % ("DONE" if n_own and w else "RED", n_own))
    return 0 if n_own and w else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=("settings", "kept"))
    ap.add_argument("--fin", default="/root/finance")
    ap.add_argument("--db", default="/root/finance/finance.db")
    ap.add_argument("--orders", default="/root/finance/spine/orders")
    a = ap.parse_args()
    return settings(a.fin, a.db) if a.what == "settings" else kept(a.orders)


if __name__ == "__main__":
    sys.exit(main())
