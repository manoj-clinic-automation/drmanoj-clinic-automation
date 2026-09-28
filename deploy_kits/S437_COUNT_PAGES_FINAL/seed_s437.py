#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s437.py -- kit S437_COUNT_PAGES_FINAL (F-659). On the live database after a green restart (and on the walk's scratch copy first),
each write audited and idempotent:
  3.3  the whole-piece list: loss_piles.seed() writes stock.whole_unit_items = ["CCM = bottle"] when the key is absent (never overwrites).
  3.1  the STOCK RECEIVE round by rule for the newest root count: loss_piles.receive_close(..., all_pending=True) -- every pending line where
       the shelf holds more than Marg (RECEIVE) and, this once, the pending ISSUE lines written off before the piles that were on no voucher --
       ONE run of kind 'receive_close' by "rule F-659, 28-Sep", one voucher round. Nothing pending -> nothing written.

  seed_s437.py --app DIR --db PATH      (DIR = the finance folder carrying loss_piles.py v2.4 and qty_words.py v1.2)
"""
import argparse
import os
import sys

RULE_WHO = "rule F-659, 28-Sep"


def seed(db, app):
    sys.path.insert(0, app)
    os.environ["FINANCE_DB"] = db
    os.chdir(app)
    import finance_app as fa                                  # noqa: PLC0415 -- the copies beside the app, never the kit's
    import stock_app                                          # noqa: PLC0415
    import loss_piles                                         # noqa: PLC0415
    with fa.app.test_request_context():
        con = stock_app._db()
        stock_app.ensure_schema(con)
        stock_app._pad_ensure(con)
        loss_piles.ensure(con)
        wrote = loss_piles.seed(con, "S437")
        print("   settings seeded: %s" % (", ".join(wrote) if wrote else "nothing new (every key already set)"))
        S = loss_piles.settings(con)
        print("   whole-piece items now: %s" % (", ".join("%s = %s" % (k, v) for k, v in sorted(S.get("whole_units", {}).items())) or "none"))
        root = stock_app._newest_root(con) or 0
        if not root:
            print("   no count: no receive round")
            return 0
        d = stock_app._pad_report_data(con, root)
        pend = stock_app._voucher_pending(con, d)
        n_r = sum(1 for p in pend if p["kind"] == "RECEIVE")
        n_i = len(pend) - n_r
        R = loss_piles.receive_close(con, root, RULE_WHO, d, all_pending=True)
        if R is None:
            print("   count #%d: no line waiting for a voucher -- nothing made" % root)
        else:
            print("   count #%d: STOCK RECEIVE by rule -- run %s, round %s, %d voucher lines (%d where the shelf held more than Marg, %d of them worded by the rule: %s; %d earlier write-offs on no voucher); pending before %d+%d, after %d"
                  % (root, R["run"], R["round_no"], R["lines"], R["receive"], len(R.get("worded") or []), ", ".join(R.get("worded") or []) or "-", R["issue"], n_r, n_i,
                     len(stock_app._voucher_pending(con, stock_app._pad_report_data(con, root)))))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    sys.exit(seed(a.db, a.app))
