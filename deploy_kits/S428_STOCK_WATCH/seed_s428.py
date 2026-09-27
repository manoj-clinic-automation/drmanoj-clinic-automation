#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s428.py -- kit S428_STOCK_WATCH. The watch's thresholds as SETTINGS (count.*, spot.*, arrival.*, leak.*), written only
where absent, each write audited (audit_log, table 'setting'); the watch's tables created. Nothing else is written: the plan
opens by itself when a count falls due, the roster is written by the 06:30 job.

  seed_s428.py --app DIR --db PATH      (DIR = the finance folder carrying stock_watch.py)
"""
import argparse
import sqlite3
import sys


def seed(db, app):
    sys.path.insert(0, app)
    import stock_watch                                        # noqa: PLC0415 -- the copy beside the app, never the kit's
    con = sqlite3.connect(db, timeout=30)
    stock_watch.ensure(con)
    wrote = stock_watch.seed(con, "S428")
    S = stock_watch.settings(con)
    print("   settings written: %s" % (", ".join(wrote) or "none (all already set)"))
    print("   in force: full count every %g months, %d Sundays offered, auto-adjust %s (good <= %g%%, bad >= %g%%); spot mornings %s, cap %d, "
          "watch list %d, costly from %d p, no repeat %d days, arrival window %d days; bill grace %d days; leakage budget %g%%, red months %d"
          % (S["cadence_months"], S["window_sundays"], "on" if S["auto_adjust"] else "off", S["good_pct"], S["bad_pct"], ",".join(S["spot_days"]), S["cap"],
             S["watch_size"], S["high_value_p"], S["repeat_gap_days"], S["arrival_days"], S["bill_grace_days"], S["budget_pct"], S["red_periods"]))
    con.close()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    sys.exit(seed(a.db, a.app))
