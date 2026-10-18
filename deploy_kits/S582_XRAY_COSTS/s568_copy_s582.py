#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s568_copy_s582.py -- S582_XRAY_COSTS: puts a SCRATCH copy of the scan app's database back at S568's install-day shape for the
stationery list, for S568's own walk only. S568's walk was written when the stationery list was empty: its I3 makes the item
'Walk A4 paper 75 GSM' and expects the desk's pre-match to offer THAT item for a line read as 'Walk A4 paper 75 GSM'. Since the morning
of 18-Oct-2026 the live list holds the owner's real items (one of them 'A4 paper (75 gsm)'), and the pre-match rightly offers the real
item -- so I3 goes red on any copy of today's database, on the FROM files as on S582's (proven: the same red on both). The copy is
given S568's stationery tables EMPTY (stationery_item, stationery_line, stationery_move, stationery_count -- rows only; the tables and
their indexes stay), exactly the shape the walk was proven on. No line of S568's walk is changed. Never run on a live database:
refuses any path outside /tmp.

    python3 -B s568_copy_s582.py /tmp/.../snap568.db"""
import os, sqlite3, sys

TABLES = ("stationery_line", "stationery_move", "stationery_count", "stationery_item")

if len(sys.argv) != 2:
    raise SystemExit(__doc__)
p = os.path.realpath(sys.argv[1])
if not p.startswith("/tmp/") or not os.path.isfile(p):
    raise SystemExit("REFUSED: %s is not a scratch copy under /tmp" % p)
c = sqlite3.connect(p)
try:
    have = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    n = {}
    for t in TABLES:
        if t in have:
            n[t] = c.execute('DELETE FROM "%s"' % t).rowcount
    c.commit()
    left = sum(c.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0] for t in TABLES if t in have)
finally:
    c.close()
print("S568's walk copy: the stationery list emptied (%s), rows left %d" % (", ".join("%s %d" % (k, v) for k, v in n.items()) or "no stationery tables", left))
sys.exit(1 if left else 0)
