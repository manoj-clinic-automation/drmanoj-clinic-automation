#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_s755_cron.py -- S755: owner_notice's new part run the way CRON runs it (cwd = the finance dir, no SHARED_LIB_DIR, no walk's path),
READ ONLY (the database opened mode=ro). Prints what the daily line would say at 11:00 today and one last line:
    S755 CRON-SHAPE: ok · <n> message(s) · <titles>      or      S755 CRON-SHAPE: ERROR <why>
    cd /root/finance && /root/wa/venv/bin/python3 -B /tmp/s755kit/check_s755_cron.py /root/finance/finance.db
Need not be run by hand -- the installer runs it at [7/7]."""
import datetime as dt
import os
import sqlite3
import sys
import traceback

try:
    db = sys.argv[1]
    sys.path.insert(0, os.getcwd())
    os.environ.pop("SHARED_LIB_DIR", None)
    import owner_notice as ON
    if not hasattr(ON, "_part_summaries"):
        print("S755 CRON-SHAPE: ERROR owner_notice.py here has no _part_summaries (not the kit's file)")
        sys.exit(1)
    con = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(db), uri=True, timeout=30)
    con.row_factory = sqlite3.Row
    now = dt.datetime.now(ON.IST).replace(hour=11, minute=0, second=0, microsecond=0)
    msgs = ON._part_summaries(con, now)
    for m in msgs:
        print("  %s -- %s" % (m["title"], m["body"][:200]))
    print("S755 CRON-SHAPE: ok · %d message(s) · %s" % (len(msgs), "; ".join(m["title"] for m in msgs) or "nothing awaited"))
except SystemExit:
    raise
except Exception:                                                 # noqa: BLE001
    print(traceback.format_exc()[-1200:])
    print("S755 CRON-SHAPE: ERROR the part raised -- see above")
    sys.exit(1)
