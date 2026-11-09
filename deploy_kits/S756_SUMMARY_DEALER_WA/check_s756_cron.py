#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_s756_cron.py -- S756 (F-1207): owner_notice.py run AS CRON RUNS IT -- the FILE executed (not imported), cwd = the finance dir,
no SHARED_LIB_DIR -- with its read-only `collect` command (the database opened mode=ro by owner_notice itself). It proves the command-line
guard stands last, so S755's morning summaries line is reached when cron runs the file. One last line:
    S756 CRON-SHAPE: ok · the guard stands last · <what collect says about the summaries>       or      S756 CRON-SHAPE: ERROR <why>
    cd /root/finance && /root/wa/venv/bin/python3 -B /tmp/s756kit/check_s756_cron.py /root/finance/finance.db
Need not be run by hand -- the installer runs it at [4/7] (by the rebuilt file) and [7/7] (by the placed one)."""
import datetime as dt
import os
import sqlite3
import subprocess
import sys
import traceback

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
try:
    db = os.path.abspath(sys.argv[1])
    here = os.getcwd()
    src = open(os.path.join(here, "owner_notice.py"), encoding="utf-8").read()
    tail = [ln for ln in src.rstrip().splitlines() if ln.strip()][-2:]
    if src.count('if __name__ == "__main__":') != 1 or not (tail and tail[0].startswith('if __name__ == "__main__":') and "sys.exit(main())" in tail[1]):
        print('S756 CRON-SHAPE: ERROR the guard does not stand once and last in %s/owner_notice.py' % here)
        sys.exit(1)
    if src.find("def _part_summaries") < 0 or src.find("def _part_summaries") > src.find('if __name__ == "__main__":'):
        print("S756 CRON-SHAPE: ERROR S755's _part_summaries is not defined before the guard")
        sys.exit(1)
    now = dt.datetime.now(IST)
    when = max(now, now.replace(hour=10, minute=31, second=0, microsecond=0))
    env = dict(os.environ)
    env.pop("SHARED_LIB_DIR", None)
    p = subprocess.run([sys.executable, "-B", "owner_notice.py", "collect", "--db", db, "--now", when.strftime("%Y-%m-%dT%H:%M:%S")],
                       cwd=here, env=env, capture_output=True, text=True, timeout=240)
    out = (p.stdout or "").strip().splitlines()
    if p.returncode != 0 or not out or not out[-1].startswith("collect:"):
        print("\n".join(((p.stdout or "") + (p.stderr or "")).strip().splitlines()[-8:]))
        print("S756 CRON-SHAPE: ERROR owner_notice.py collect, run as a file, did not finish")
        sys.exit(1)
    sl = [ln for ln in out if ln.startswith("summaries:")]
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=30)
    said = con.execute("SELECT COUNT(*) FROM owner_notice WHERE key LIKE ?", ("summaries:%%:%s" % when.strftime("%Y-%m-%d"),)).fetchone()[0]
    sys.path.insert(0, here)
    import scan_register as SR                                # noqa: E402 -- READ ONLY, to know whether anything is awaited
    aw = sum(len(SR.s755_awaited(con, m)) for m in SR._s755_ended_months(con)) if SR.s750_summary_scans(con) is not None else -1
    if aw > 0 and not sl and not said:
        print("S756 CRON-SHAPE: ERROR %d summaries are awaited, yet collect (run as a file) made no summaries line and none was said today" % aw)
        sys.exit(1)
    for ln in sl:
        print("  " + ln[:200])
    if sl:
        what = "collect says: " + "; ".join(ln.split("|")[0].split(None, 1)[-1].strip() for ln in sl)
    elif said:
        what = "said today already"
    elif aw < 0:
        what = "ASSETS UNREAD at cron's path -- the morning line could not be judged"
    else:
        what = "nothing awaited"
    print("S756 CRON-SHAPE: ok · the guard stands last · %s · %s" % (what, out[-1]))
except SystemExit:
    raise
except Exception:                                             # noqa: BLE001
    print(traceback.format_exc()[-1200:])
    print("S756 CRON-SHAPE: ERROR the check raised -- see above")
    sys.exit(1)
