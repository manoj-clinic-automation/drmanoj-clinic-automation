#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s894_job.py -- S894_ASKED_COUNT_BACK (20-Nov-2026, Sanjeevni session 490; the owner's word 14:44 IST, "1 to be done through Amir").
Data only, idempotent:
  1. Two tap jobs on Amir's card from Darpan's counts of 18-11-2026 (ZIBON EXTRA 20:6 at 10:59, GEMCAL XT 15:12 at 11:06) against
     Marg's closing (35:9 and 16:1; no sale of either 16-18 Nov):  ZIBON EXTRA STOCK ISSUE 15:3 . GEMCAL XT TABLETS STOCK ISSUE 0:4.
     Refused (nothing added) if Amir's card already holds another open job for the item. A sale after the count is no reason
     to refuse: it moves Marg and the shelf alike (v2: v1 refused GEMCAL XT for its 19-11 sale, 241 -> 234, on the box at [3/5]).
  2. The owner's open 'Count this' asks that Darpan has since answered (a spot/darpan point after the ask) are closed -- 14-Nov's
     ZIBON EXTRA and GEMCAL XT and 12-Oct's ANKLE BINDER L BAMBOO were answered on 18-Nov on carried rows and never closed.
    python3 -B s894_job.py <finance.db> [--dry]"""
import datetime as dt
import sqlite3
import sys

JOBS = [
    ("S894:zibon-extra:count-18nov", "ZIBON EXTRA", 206, 153,
     "ZIBON EXTRA — STOCK ISSUE 15:3 (strip:tab) Marg mein daaliye",
     "Darpan ki 18-11 ki ginti: shelf par 20:6, Marg mein 35:9. Daal kar 'Kar diya' dabaiye."),
    ("S894:gemcal-xt:count-18nov", "GEMCAL XT TABLETS", 237, 4,
     "GEMCAL XT TABLETS — STOCK ISSUE 0:4 (strip:tab) Marg mein daaliye",
     "Darpan ki 18-11 ki ginti: shelf par 15:12, Marg mein 16:1. Daal kar 'Kar diya' dabaiye."),
]


def main(db, dry):
    con = sqlite3.connect(db, timeout=30)
    try:
        for t in ("amir_job", "stock_watch_ask", "stock_point", "stock_snapshot"):
            if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone():
                print("S894: %s is not on this server -- nothing written" % t)
                return 2
        now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S")
        plan = []
        for key, item, counted, issue, text, sub in JOBS:
            if con.execute("SELECT 1 FROM amir_job WHERE key=?", (key,)).fetchone():
                print("S894: ALREADY ON HIS CARD (%s)" % key)
                continue
            r = con.execute("SELECT qty, as_on FROM stock_snapshot WHERE item=? ORDER BY substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2) DESC, rowid DESC LIMIT 1", (item,)).fetchone()
            # A sale after the count moves Marg and the shelf alike -- the gap to correct stays the same (GEMCAL XT 241 -> 234 on 19-11).
            # What would make the job wrong is a correction already on its way: another open job on Amir's card for the item.
            other = con.execute("SELECT key FROM amir_job WHERE subject=? AND done_at IS NULL AND key<>?", (item, key)).fetchone()
            if other:
                print("S894: REFUSED %s -- Amir's card already holds an open job for it (%s). Nothing added for it; tell Claude." % (item, other[0]))
                return 3
            plan.append((key, item, text, sub, r))
        asks = con.execute(
            "SELECT a.id, a.item FROM stock_watch_ask a WHERE a.done_at IS NULL AND EXISTS (SELECT 1 FROM stock_point p WHERE p.item_norm=a.item_norm "
            "AND p.source IN ('spot','darpan') AND COALESCE(p.status,'')<>'superseded' AND p.at>=a.at)").fetchall()
        if dry:
            for key, item, text, sub, r in plan:
                print("S894: DRY -- would add: %s (Marg now %s on %s)" % (text, r and r[0], r and r[1]))
            print("S894: DRY -- would close %d answered ask(s): %s" % (len(asks), ", ".join(x[1] for x in asks) or "none"))
            return 0
        with con:
            for key, item, text, sub, r in plan:
                con.execute("INSERT INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                            (key, "tap", item, text, sub, now, "S894 (the owner's word, 20-Nov 14:44)", now))
            for aid, item in asks:
                con.execute("UPDATE stock_watch_ask SET done_at=? WHERE id=? AND done_at IS NULL", (now.replace(" ", "T"), aid))
        for key, item, text, sub, r in plan:
            j = con.execute("SELECT id FROM amir_job WHERE key=?", (key,)).fetchone()
            print("S894: added job %d: %s" % (j[0], text))
        print("S894: closed %d answered ask(s): %s" % (len(asks), ", ".join(x[1] for x in asks) or "none"))
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], "--dry" in sys.argv[2:]) if len(sys.argv) > 1 else 2)
