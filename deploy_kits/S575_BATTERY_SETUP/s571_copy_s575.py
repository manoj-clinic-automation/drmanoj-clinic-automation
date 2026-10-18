#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s571_copy_s575.py -- S575_BATTERY_SETUP: puts a SCRATCH copy of the scan app's database back at S571's install-day shape, for
S571's own walk only. S571's walk was written for a database before S571 (it counts the 15 seeded places, the new tables and the one
setting its mount adds, and the totals of its own made-up fittings). On the live database S571 is installed, so its walk is given a
copy without S571's three tables (their two indexes go with them) and without the setting batteries.since -- exactly the shape it
was proven on; its mount then makes them again on that copy. No line of S571's walk is changed. Never run on a live database:
refuses any path outside /tmp.

    python3 -B s571_copy_s575.py /tmp/.../snap571.db"""
import os, sqlite3, sys

if len(sys.argv) != 2:
    raise SystemExit(__doc__)
p = os.path.realpath(sys.argv[1])
if not p.startswith("/tmp/") or not os.path.isfile(p):
    raise SystemExit("REFUSED: %s is not a scratch copy under /tmp" % p)
c = sqlite3.connect(p)
try:
    for t in ("battery_fit", "battery_upkeep", "battery_place"):
        c.execute('DROP TABLE IF EXISTS "%s"' % t)
    n = c.execute("DELETE FROM settings WHERE key='batteries.since'").rowcount
    c.commit()
    left = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE name LIKE 'battery%'")]
finally:
    c.close()
print("S571's walk copy: S571's tables taken out (left: %s), batteries.since %s" % (left or "none", "taken out" if n else "was not there"))
sys.exit(1 if left else 0)
