#!/usr/bin/env python3
# roster_s958.py · kit S958_DARPAN_LISTS · run with FINANCE_DB set, from /root/finance.
#   build FILE : today's list, if none is written yet -- on a non-spot morning only his waiting asks (pushed to Darpan); the ids of the rows
#                it wrote go into FILE (so the undo never depends on a clock); prints one line.
#   undo FILE  : those rows removed while not yet counted, their asks back to waiting.
import os
import sqlite3
import sys

sys.path.insert(0, os.getcwd())
import stock_watch as SW                                      # noqa: E402

con = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
arg = sys.argv[1] if len(sys.argv) > 1 else ""
path = sys.argv[2] if len(sys.argv) > 2 else ""
t = SW.today().isoformat()
if arg == "build" and path:
    ids0 = {r[0] for r in con.execute("SELECT id FROM stock_spot_roster WHERE day=?", (t,))}
    R = dict(items=[])
    try:
        R = SW.build_roster(con, SW.today(), who="s958-install", asks_ok=True)
    finally:                                                  # the second look: the ids are written even if the build raises after its commit
        new = sorted({r[0] for r in sqlite3.connect(os.environ["FINANCE_DB"], timeout=60).execute("SELECT id FROM stock_spot_roster WHERE day=?", (t,))} - ids0)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(",".join(str(i) for i in new))
    print("S958 roster: %s -- %s" % (t, ("already written (%d)" % len(ids0)) if ids0 else ("%d item(s): %s" % (len(new), ", ".join(x["item"] for x in R["items"])) if new else "nothing waiting")))
elif arg == "undo" and path:
    try:
        ids = [int(x) for x in open(path, encoding="utf-8").read().split(",") if x.strip()]
    except (OSError, ValueError):
        ids = []
    n = 0
    for i in ids:
        n += con.execute("DELETE FROM stock_spot_roster WHERE id=? AND answered_at IS NULL", (i,)).rowcount
    con.execute("UPDATE stock_watch_ask SET roster_id=NULL WHERE roster_id IS NOT NULL AND done_at IS NULL AND roster_id NOT IN (SELECT id FROM stock_spot_roster)")
    con.commit()
    print("S958 roster undo: %d row(s) removed" % n)
else:
    print("usage: roster_s958.py build FILE | undo FILE")
    sys.exit(2)
