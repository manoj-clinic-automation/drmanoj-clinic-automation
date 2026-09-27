#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s427.py -- kit S427_LOSS_DESK_RULINGS. The desk's thresholds as SETTINGS (every threshold a setting -- the owner,
27-Sep). Writes only the keys that are not there yet, never overwrites, each write audited (audit_log, table 'setting');
creates the desk's tables. The big-loss floor inherits the value of S418's pursue floor (Rs 1,000 seeded at 100000
paise -- keep the value, relabel); a blank S418 small-gap ceiling becomes Rs 1,000. The consumption list is seeded with
BLADE, ZIG ZAG cotton and every glove item. S418's retired keys (allowance_scale, recount_trigger, consume_auto,
rolling_section_items, rolling_day, pursue_floor_p) are left in the table untouched.

  seed_s427.py --app DIR --db PATH      (DIR = the finance folder carrying loss_piles.py and qty_words.py)
"""
import argparse
import sqlite3
import sys


def seed(db, app):
    sys.path.insert(0, app)
    import loss_piles                                         # noqa: PLC0415 -- the copy beside the app, never the kit's
    con = sqlite3.connect(db, timeout=30)
    loss_piles.ensure(con)
    wrote = loss_piles.seed(con, "S427")
    S = loss_piles.settings(con)
    print("   settings written: %s" % (", ".join(wrote) or "none (all already set)"))
    print("   in force: allowance %g%% (floor %d strips), small-gap ceiling %d p, big-loss floor %d p, slow %g months from %d p, "
          "%d lines a voucher, accept back by %s, staff block names %d, consumption list %d items"
          % (S["allowance_pct"], S["allowance_min_strips"], S["small_gap_ceiling_p"], S["big_loss_floor_p"], S["slow_months"], S["slow_floor_p"],
             S["voucher_batch"], ",".join(S["accept_back_by"]), S["staff_block_items"], len(S["consume_items"])))
    con.close()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    sys.exit(seed(a.db, a.app))
