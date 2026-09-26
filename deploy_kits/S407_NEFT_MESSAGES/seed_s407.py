#!/usr/bin/env python3
"""seed_s407.py -- kit S407_NEFT_MESSAGES (D623): the settings supplier_msg.senders (default manoj,shavez) and
neft.stmt_tolerance_p (default 0), INSERT OR IGNORE; and the reception phone's token supplier_msg.phone_token, made ONCE
(random, 48 hex) when absent -- never printed here, never in the kit or the report; the setup page shows it once.
The tables are made by supplier_msg.py on first use.
Usage: seed_s407.py DB_PATH   (imports supplier_msg.py from beside this file, or from FINANCE_DIR)
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def seed(path):
    for d in (HERE, os.environ.get("FINANCE_DIR", "/root/finance")):
        if os.path.isfile(os.path.join(d, "supplier_msg.py")) and d not in sys.path:
            sys.path.insert(0, d)
    import supplier_msg  # noqa: E402
    con = sqlite3.connect(path, timeout=30)
    supplier_msg.seed(con)
    got = {r[0]: r[1] for r in con.execute("SELECT key, value FROM setting WHERE key LIKE 'supplier_msg.%' OR key='neft.stmt_tolerance_p'")}
    con.close()
    missing = [k for k in ("supplier_msg.senders", "supplier_msg.phone_token", "neft.stmt_tolerance_p") if not got.get(k)]
    if missing:
        print("SEED WRONG: missing %s" % missing)
        return 1
    print("seed: senders=%s stmt_tolerance_p=%s phone_token=set (%d chars, not printed)"
          % (got["supplier_msg.senders"], got["neft.stmt_tolerance_p"], len(got["supplier_msg.phone_token"])))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(seed(sys.argv[1]))
