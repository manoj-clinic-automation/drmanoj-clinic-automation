#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s582_copy_s585.py -- S585_STATIONERY_ISSUE_MANY: puts a SCRATCH copy of the scan app's database back at S582's install-day shape,
for S582's own walk only. S582's walk was proven on a database WITHOUT its table xray_mark: its Z1 checks that the mount adds exactly
the table xray_mark and its index xray_mark_live with no row. Since S582 was installed (16:18 IST 18-Oct-2026) the live database holds
that table with the three seed marks, so Z1 is red on any copy of today's database -- on S582's own files as on S585's. The copy is given
the table and its index DROPPED (the seed marks with them), exactly the shape the walk was proven on. No line of S582's walk is changed.
Never run on a live database: refuses any path outside /tmp.

    python3 -B s582_copy_s585.py /tmp/.../snap582.db"""
import os, sqlite3, sys

if len(sys.argv) != 2:
    raise SystemExit(__doc__)
p = os.path.realpath(sys.argv[1])
if not p.startswith("/tmp/") or not os.path.isfile(p):
    raise SystemExit("REFUSED: %s is not a scratch copy under /tmp" % p)
c = sqlite3.connect(p)
try:
    had = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name IN ('xray_mark', 'xray_mark_live')").fetchone()[0]
    c.execute("DROP INDEX IF EXISTS xray_mark_live")
    c.execute("DROP TABLE IF EXISTS xray_mark")
    c.commit()
    left = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name IN ('xray_mark', 'xray_mark_live')").fetchone()[0]
finally:
    c.close()
print("S582's walk copy: xray_mark and its index taken out (%d object%s there before), left %d" % (had, "" if had == 1 else "s", left))
sys.exit(1 if left else 0)
