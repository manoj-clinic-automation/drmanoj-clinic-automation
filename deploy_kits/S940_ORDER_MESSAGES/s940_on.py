#!/usr/bin/env python3
"""s940_on.py -- kit S940's start on the live database. argv: <kit dir> <finance.db>
order.d1053_msg_since = now: no sheet, final or arrival before the install is announced; the messages start with the next one."""
import datetime as dt, sqlite3, sys
con = sqlite3.connect(sys.argv[2], timeout=30)
now = dt.datetime.now().replace(microsecond=0).isoformat()
con.execute("INSERT INTO setting (key, value, note) VALUES ('order.d1053_msg_since', ?, 'S940: the purchase order flow messages start here') "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (now,))
con.commit()
print("S940 start: messages from %s" % now)
