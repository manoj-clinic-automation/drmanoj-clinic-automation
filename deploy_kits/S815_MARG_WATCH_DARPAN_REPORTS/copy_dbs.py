#!/usr/bin/env python3
"""copy_dbs.py SRC DST -- a consistent copy of a live SQLite database (the backup API: the live file is only read)."""
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True, timeout=60)
d = sqlite3.connect(sys.argv[2])
s.backup(d)
d.close(); s.close()
print("copied")
