#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""heal_s627.py -- S627's data step (BUILD_NORM s1: the code heals the data it governs). Papers scanned since S625's switch-on that
were read before S627 have no 'late' mark although the rule counts them in an earlier month: they get it now -- the same test as
asset_register._set_late's S627 branch (clinic_papers.MONTH_OF, the scan month in IST). Repeatable: it only fills an EMPTY late_for,
never changes or clears one; with the rule off (no date-shaped switch row) it does nothing. One transaction.

    python3 -B heal_s627.py <assets.db> <the app folder>
"""
import datetime
import re
import sqlite3
import sys

db_path, app = sys.argv[1], sys.argv[2]
sys.path.insert(0, app)
import clinic_papers as cp                                           # noqa: E402  (module import only: no init, no app)

con = sqlite3.connect(db_path, timeout=30)
con.isolation_level = None
try:
    con.execute("BEGIN IMMEDIATE")
    sw = con.execute("SELECT value FROM settings WHERE key=?", (getattr(cp, "S625_KEY", "papers.month_from_bill_date"),)).fetchone()
    sw = (sw[0] or "") if sw else ""
    if not re.match(r"\d{4}-\d{2}-\d{2}", sw):
        con.execute("ROLLBACK")
        print("heal: the month rule is off (switch '%s') -- nothing to mark" % (sw or "absent"))
        sys.exit(0)
    rows = con.execute("SELECT b.id, b.stamp_no, b.created_at, " + cp.MONTH_OF + " FROM bills b WHERE b.late_for IS NULL "
                       "AND COALESCE(b.created_at,'') >= ? AND b.stamp_no IS NOT NULL", (sw,)).fetchall()
    done = []
    for bid, stamp, made, mo in rows:
        try:
            mi = (datetime.datetime.strptime((made or "")[:19], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=330)).strftime("%Y-%m")
        except ValueError:
            continue
        if mo and mo < mi:
            con.execute("UPDATE bills SET late_for=? WHERE id=? AND late_for IS NULL", (mo, bid))
            done.append("%s -> %s" % (stamp, mo))
    con.execute("COMMIT")
    print("heal: %d paper(s) scanned since %s UTC now marked late for their bill's month%s" % (len(done), sw, (": " + ", ".join(done)) if done else ""))
except Exception:
    if con.in_transaction:
        con.execute("ROLLBACK")
    raise
finally:
    con.close()
