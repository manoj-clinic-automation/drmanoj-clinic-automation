#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s828.py -- S828_BATCH_NOTICE_TRUE: the walk, on a COPY of a finance.db with made-up batch rows (WALK items only).
    python3 -B walk_s828.py <finance code dir> <shared dir> <finance.db to copy>
No message can leave: owner_notice._part_amir is called directly (it only builds the message). Its last line:  walk_s828: N check(s) failed"""
import datetime as dt
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import traceback

FAILS = []


def ok(cond, label):
    if not cond:
        FAILS.append(label)
    print(("ok    " if cond else "FAIL  ") + label)


def main(code, shared, src_db):
    tmp = tempfile.mkdtemp(prefix="walk_s828_")
    try:
        db = os.path.join(tmp, "finance.db")
        s = sqlite3.connect("file:%s?mode=ro" % src_db, uri=True)
        d = sqlite3.connect(db)
        s.backup(d)
        s.close()
        d.close()
        sys.path.insert(0, shared)
        sys.path.insert(0, code)
        os.environ["SHARED_LIB_DIR"] = shared
        import warnings
        warnings.simplefilter("ignore")
        import expiry_watch as EW
        import owner_notice as ON
        IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
        now = dt.datetime(2026, 11, 14, 9, 3, tzinfo=IST)
        EW.batch_stock_state = lambda con, today=None: dict(state="ok", at="06:51", items=232, as_on="2026-11-13")
        EW.now_ist = lambda: now.replace(tzinfo=None)
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        EW.fixes_ensure(con)
        con.execute("DELETE FROM stock_batch_fix")
        ON.ensure(con)
        con.commit()
        S = dict(amir_day=True, rows=[dict(key="PURCHASE_ITEMWISE", state="ok", when="2026-11-14 08:56:26"),
                                      dict(key="PURCHASE_BILLWISE", state="ok", when="2026-11-14 08:56:10")])
        since = "2026-11-01 00:00:00"

        def add(n, status, judged, done=None, note=None):
            for i in range(n):
                con.execute("INSERT INTO stock_batch_fix (kind, k20, item, pack, minus_batch, units, issue_batch, asked_run_id, asked_at, status, "
                            "judged_at, done_at, note) VALUES ('batch', ?, ?, 10, 'MB', 1, 'IB', 1, '2026-11-10T09:00:00', ?, ?, ?, ?)",
                            ("WALK%s%d" % (status, i), "WALK %s %d" % (status, i), status, judged, done, note))
            con.commit()

        def msg(t):
            r = ON._part_amir(con, S, t, since)
            return r[0]["body"] if r else None

        add(4, "done", "2026-11-14T09:05:00", "2026-11-14T09:05:00")
        add(4, "done", "2026-11-13T18:30:00", "2026-11-13T18:30:00")     # yesterday evening: inside the 24 hours, as on his card
        add(2, "done", "2026-11-10T09:00:00", "2026-11-10T09:00:00")     # days ago: not counted
        add(5, "open", "2026-11-14T09:05:00")
        add(1, "receive_only", "2026-11-14T09:05:00")
        add(7, "open", None)                                             # new rows, not judged yet
        add(3, "open", "2026-11-14T07:02:00", note="issue pending the day's sales (3919b3df)")
        m = msg(now)
        ok(m is None, "1 a row waits for the day's sales: the message waits too (09:03, reports 08:56)")
        m2 = msg(dt.datetime(2026, 11, 14, 12, 0, tzinfo=IST))
        ok(m2 is not None and "still being checked" in m2 and "0 done" not in m2, "2 past the 180 minutes: it goes, saying the check still waits")
        con.execute("UPDATE setting SET value='30' WHERE key='owner_notice.batch_hold_min'")
        con.commit()
        m3 = msg(dt.datetime(2026, 11, 14, 9, 30, tzinfo=IST))
        ok(m3 is not None and "still being checked" in m3, "3 the hold is his setting (30 minutes)")
        con.execute("UPDATE stock_batch_fix SET note=NULL, judged_at='2026-11-14T09:05:00' WHERE note LIKE 'issue pending%'")
        con.commit()
        m4 = msg(dt.datetime(2026, 11, 14, 9, 10, tzinfo=IST)) or ""
        ok("Batch fixes: 8 fixed, 9 still to do" in m4, "4 judged: 8 fixed (24 hours), 9 still to do (judged today) -- %r" % m4[-60:])
        html = repr(EW.fixes_rows(con, dt.date(2026, 11, 14)) or [])
        mm = re.search(r"(\d+) batch theek ho gaye, (\d+) abhi baaki", html)
        ok(mm is not None and (mm.group(1), mm.group(2)) == ("8", "9"), "5 the same two numbers as Amir's own card (%s)" % (str(mm.groups()) if mm else "none",))
        ok("left" not in m4 and "done today" not in m4, "6 the old wording is gone")
        con.execute("DELETE FROM stock_batch_fix")
        con.commit()
        m5 = msg(dt.datetime(2026, 11, 14, 9, 10, tzinfo=IST)) or ""
        ok(m5.startswith("Item-wise") and "Batch fixes" not in m5, "7 no batch rows: the message as before, no batch line")
        ok(ON.setting(con, "owner_notice.amir_missing_hhmm") == "23:40", "8 the other settings unchanged")
        con.close()
    except Exception:                                         # noqa: BLE001
        print(traceback.format_exc()[-1500:])
        FAILS.append("raised")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("walk_s828: %d check(s) failed" % len(FAILS))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])))
