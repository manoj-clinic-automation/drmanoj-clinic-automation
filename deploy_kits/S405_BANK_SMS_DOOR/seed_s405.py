#!/usr/bin/env python3
"""seed_s405.py -- the one setting of kit S405_BANK_SMS_DOOR (D621): neft.sms_tolerance_p, the paise by which a Yes Bank
NEFT debit may differ from a finalised pay month's NEFT portion and still be matched (the bank's charges). Default 0.
INSERT OR IGNORE only: a value the owner or the chat has set is never overwritten. The tables themselves are made by
bank_sms.py on its first request (F-303).
Usage: seed_s405.py DB_PATH
"""
import sqlite3
import sys

SETTINGS = {"neft.sms_tolerance_p": ("0", "S405 D621 -- paise of tolerance when matching a Yes Bank NEFT SMS to a pay month; a data edit changes it")}


def seed(path):
    con = sqlite3.connect(path, timeout=30)
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for k, (v, note) in SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))
    con.commit()
    got = {r[0]: r[1] for r in con.execute("SELECT key, value FROM setting WHERE key LIKE 'neft.%'")}
    con.close()
    if "neft.sms_tolerance_p" not in got:
        print("SEED WRONG: neft.sms_tolerance_p missing")
        return 1
    print("seed: neft.sms_tolerance_p = %s paise" % got["neft.sms_tolerance_p"])
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
