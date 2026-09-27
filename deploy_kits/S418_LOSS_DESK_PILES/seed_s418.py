#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed_s418.py -- kit S418_LOSS_DESK_PILES. The desk's rules as SETTINGS (the owner, 26-Sep: "so that we can alter
them without going back to the code"). Writes only the keys that are not there yet, never overwrites, each write
audited (audit_log, table 'setting'); creates the desk's own tables. The allowance starts WIDE for count #1 (the
owner's ruling: six months without a proper count).

  seed_s418.py --app DIR --db PATH      (DIR = the finance folder carrying loss_piles.py)
"""
import argparse
import sqlite3
import sys


def seed(db, app):
    sys.path.insert(0, app)
    import loss_piles                                         # noqa: PLC0415 -- the copy beside the app, never the kit's
    con = sqlite3.connect(db, timeout=30)
    loss_piles.ensure(con)
    wrote = loss_piles.seed(con, "S418")
    S = loss_piles.settings(con)
    print("   settings written: %s" % (", ".join(wrote) or "none (all already set)"))
    print("   in force: allowance x%s, pursue floor %s p, small-gap ceiling %s p, recount at %s units, %s lines a voucher, accept back by %s, consumables %s"
          % (S["allowance_scale"], S["pursue_floor_p"], S["small_gap_ceiling_p"], S["recount_trigger"], S["voucher_batch"],
             ",".join(S["accept_back_by"]), "on" if S["consume_auto"] else "off"))
    con.close()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--db", required=True)
    a = ap.parse_args()
    sys.exit(seed(a.db, a.app))
