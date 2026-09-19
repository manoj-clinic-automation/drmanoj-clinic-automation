#!/usr/bin/env python3
"""fix_s327.py -- numbers from BEFORE the tile started are not slips to ask about (owner, 19-Sep-2026:
"procedure slips up to 1136 are of the previous days and not to be considered" -- a one-time
request at the start; after it every skipped number keeps its Radd / Kharab / Baad mein question).
Every 'missing' placeholder below its book's own start number is taken off (state void, with the reason); the X-ray/Proc
book's start is held at 1137 at least. slip and slip_book only; a second run changes nothing.
Usage: fix_s327.py DB_PATH"""
import sqlite3
import sys

con = sqlite3.connect(sys.argv[1], timeout=30)
if not con.execute("SELECT 1 FROM sqlite_master WHERE name='slip_book'").fetchone():
    print("fix: no slip tables yet -- nothing to do")
    sys.exit(0)
con.execute("UPDATE slip_book SET start_no=1137 WHERE series='xp' AND (start_no IS NULL OR start_no<1137)")
n = 0
for series, start in con.execute("SELECT series, start_no FROM slip_book WHERE start_no IS NOT NULL").fetchall():
    n += con.execute("UPDATE slip SET state='void', note='before the tile started (owner, 19-Sep-2026)', "
                     "updated_by='S327', updated_at=datetime('now','localtime') "
                     "WHERE series=? AND state='missing' AND slip_no<?", (series, start)).rowcount
con.commit()
print("fix: %d number(s) from before the tile started taken off" % n)
