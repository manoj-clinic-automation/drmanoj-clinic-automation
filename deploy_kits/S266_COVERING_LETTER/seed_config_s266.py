#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_config_s266.py -- write one letterhead value into the database.

The shop's printed mobile is a number, so it does not travel in the repository
(F-185). It is handed in on the install line and kept in purchase_pay_config.
Printed back masked; an existing value is replaced only when it differs, and the
old one is named so the change is never silent.

    python3 seed_config_s266.py --db /root/finance/finance.db --key debit_account --value <no>
"""
import argparse
import datetime as dt
import sqlite3
import sys


def mask(s):
    s = (s or "").strip()
    return ("*" * max(0, len(s) - 4)) + s[-4:] if s else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--value", required=True)
    a = ap.parse_args()
    v = a.value.strip()
    if not v:
        sys.exit("REFUSING: an empty value")
    con = sqlite3.connect(a.db)
    con.execute("""CREATE TABLE IF NOT EXISTS purchase_pay_config (
        key TEXT PRIMARY KEY, value TEXT, at TEXT)""")
    old = con.execute("SELECT value FROM purchase_pay_config WHERE key=?", (a.key,)).fetchone()
    if old and (old[0] or "").strip() == v:
        print("   %s already set to %s -- nothing to do" % (a.key, mask(v)))
        return
    if old and (old[0] or "").strip():
        print("   %s was %s, now %s" % (a.key, mask(old[0]), mask(v)))
    else:
        print("   %s set to %s" % (a.key, mask(v)))
    con.execute("INSERT OR REPLACE INTO purchase_pay_config (key, value, at) VALUES (?,?,?)",
                (a.key, v, dt.datetime.now().isoformat(timespec="seconds")))
    con.commit()


if __name__ == "__main__":
    main()
