#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_setting_s284.py -- write the cheque-writer list into finance.db (D524).

    python3 -B seed_setting_s284.py --db /root/finance/finance.db --value shavez
    python3 -B seed_setting_s284.py --db /root/finance/finance.db --show
    python3 -B seed_setting_s284.py --db /root/finance/finance.db --value ""   # nobody: the undo

The row is setting.purchase.cheque_users, the same shape as purchase.phonebook_users.
An existing value is replaced only when it differs, and the old one is printed so the
change is never silent. Login names are not numbers; nothing here is masked.
"""
import argparse
import sqlite3
import sys

KEY = "purchase.cheque_users"
NOTE = "S284 / D524 -- who may write the cheque register besides maker/checker; the owner's word of 15-Sep-2026"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--value", default=None)
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args(argv)
    con = sqlite3.connect(a.db)
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    old = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()
    cur = (old[0] if old else "") or ""
    if a.show or a.value is None:
        print("   %s = %r" % (KEY, cur))
        return 0
    v = a.value.strip().lower()
    if cur.strip().lower() == v:
        print("   %s already %r -- nothing to do" % (KEY, v))
        return 0
    print("   %s was %r, now %r" % (KEY, cur, v))
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)", (KEY, v, NOTE))
    con.commit()
    back = con.execute("SELECT value FROM setting WHERE key=?", (KEY,)).fetchone()[0]
    return 0 if back == v else 4


if __name__ == "__main__":
    sys.exit(main())
