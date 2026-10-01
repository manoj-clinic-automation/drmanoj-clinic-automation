#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""names_s444.py -- kit S444_STAFF_SAFE: BEFORE the sign-in name becomes small letters everywhere, prove no live name depends on case.

Reads, read-only: every login in the clinic_users store (names only -- never a hash), the users of tile_grants.json, unit_role,
the asset app's lane logins (user_lane_default, S409) and its local users, and the actors of pend_mark and the sale check
(sale_check_day / _issue / _cash). Every name must already be small letters with no space around it; one that is not STOPS the
install (exit 3) and is named. Prints counts only.

    names_s444.py --portal DIR --finance-db PATH --assets-db PATH
"""
import argparse
import json
import os
import sqlite3
import sys


def ro(path):
    return sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=10)


def has(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None


def cols(con, t):
    return {r[1] for r in con.execute("PRAGMA table_info(%s)" % t)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--portal", required=True)
    ap.add_argument("--finance-db", required=True)
    ap.add_argument("--assets-db", required=True)
    a = ap.parse_args()
    seen, bad = {}, []

    def take(src, names):
        k = 0
        for v in names:
            if v is None:
                continue
            s = str(v)
            if s == "":
                continue
            k += 1
            if s != s.strip().lower():
                bad.append("%s: %r" % (src, s))
        seen[src] = k

    with open(os.path.join(a.portal, "clinic_users.json"), encoding="utf-8") as fh:
        take("clinic_users store", list((json.load(fh).get("users") or {}).keys()))
    with open(os.path.join(a.portal, "tile_grants.json"), encoding="utf-8") as fh:
        take("tile_grants.json users", list((json.load(fh).get("users") or {}).keys()))
    f = ro(a.finance_db)
    try:
        take("unit_role", [r[0] for r in f.execute("SELECT DISTINCT username FROM unit_role")])
        if has(f, "pend_mark"):
            take("pend_mark actors", [r[0] for r in f.execute("SELECT DISTINCT by_user FROM pend_mark")])
        for t, cs in (("sale_check_day", ("checked_by",)), ("sale_check_issue", ("added_by", "removed_by")), ("sale_check_cash", ("entered_by",))):
            if has(f, t):
                c = cols(f, t)
                take("%s actors" % t, [r[0] for col in cs if col in c for r in f.execute("SELECT DISTINCT %s FROM %s" % (col, t))])
    finally:
        f.close()
    s = ro(a.assets_db)
    try:
        if has(s, "user_lane_default"):
            take("lane logins (user_lane_default)", [r[0] for r in s.execute("SELECT username FROM user_lane_default")])
        if has(s, "users"):
            take("asset app users", [r[0] for r in s.execute("SELECT username FROM users")])
    finally:
        s.close()
    print("S444 name check: " + " · ".join("%s %d" % (k, v) for k, v in seen.items()))
    if bad:
        print("STOP -- %d name(s) are not small letters: %s" % (len(bad), "; ".join(bad[:20])))
        return 3
    print("S444 name check GREEN -- every live name is already small letters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
