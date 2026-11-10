#!/usr/bin/env python3
"""proof_s775.py FILES_DIR PROOF_DB LABEL -- on ONE COPY of finance.db: what purchase_unspill would join, by the kit's module; then
applied ON THE COPY and read back (every planned line joined, nothing left to do), then undone ON THE COPY (every line back).
Never the live file. Last line: 'PROOF S775 LABEL: ...'."""
import os
import sqlite3
import sys

FILES, PDB, LABEL = sys.argv[1:4]
if os.path.abspath(PDB).startswith("/root/finance/"):
    print("REFUSED: the proof runs on a copy, never in /root/finance")
    sys.exit(2)
sys.path.insert(0, FILES)
import purchase_unspill as U  # noqa: E402

con = sqlite3.connect(PDB, timeout=30)
p = U.plan(con)
per = {}
for lid, bid, bno, bd, name, old in p:
    per.setdefault((bno, bd), []).append(name)
for (bno, bd), names in sorted(per.items(), key=lambda x: x[0][1] or ""):
    print("  bill %s (%s): %d line(s) -- %s" % (bno, bd, len(names), ", ".join(sorted(set(names)))[:150]))
import datetime as _dt  # noqa: E402
ts = _dt.datetime.now().replace(microsecond=0).isoformat()
n = U.unspill(con, by="proof")
con.commit()
left = len(U.plan(con))
u = U.undo(con, since=ts)                                      # only what this proof joined; earlier joins (S773) stay
back = con.execute("SELECT COUNT(*) FROM purchase_unspill_log WHERE at >= ?", (ts,)).fetchone()[0]
con.close()
ok = n == len(p) and left == 0 and u == n and back == 0
print("PROOF S775 %s: %d line(s) would join %d bill(s); applied on the copy %d, left %d, undone %d -- %s" % (LABEL, len(p), len(per), n, left, u, "ok" if ok else "BAD"))
