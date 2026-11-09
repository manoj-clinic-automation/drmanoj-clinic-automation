#!/usr/bin/env python3
"""seed_s406.py -- the three settings of kit S406_RETURNS_TWO_KINDS (D622): returns.noise_p (paise, default 2000 = Rs 20),
returns.noise_pct (default 2), returns.big_p (paise, default 100000 = Rs 1,000). INSERT OR IGNORE only: a value the owner
or the chat has set is never overwritten. The table cn_kind is made by returns_kinds.py on first use.
Usage: seed_s406.py DB_PATH
"""
import sqlite3
import sys

SETTINGS = {
    "returns.noise_p": ("2000", "S406 D622 -- paise below which a refund difference is rounding, not a finding"),
    "returns.noise_pct": ("2", "S406 D622 -- per cent of the return below which a refund difference is rounding"),
    "returns.big_p": ("100000", "S406 D622 -- paise from which a counter return needs the owner's OK"),
}


def seed(path):
    con = sqlite3.connect(path, timeout=30)
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for k, (v, note) in SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note))
    con.commit()
    got = {r[0]: r[1] for r in con.execute("SELECT key, value FROM setting WHERE key LIKE 'returns.%'")}
    con.close()
    missing = [k for k in SETTINGS if k not in got]
    if missing:
        print("SEED WRONG: settings missing: %s" % missing)
        return 1
    print("seed: returns.noise_p=%s returns.noise_pct=%s returns.big_p=%s" % (got["returns.noise_p"], got["returns.noise_pct"], got["returns.big_p"]))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
