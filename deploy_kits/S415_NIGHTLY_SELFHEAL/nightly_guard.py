#!/usr/bin/env python3
"""nightly_guard.py -- kit S415_NIGHTLY_SELFHEAL (F-630). Called by NIGHTLY.bat when it is started by the MORNING task
(argument 'morning', 07:30 or at log-on). Exit 3 = the 03:10 run already happened today, nothing to do.
Exit 0 = no run today yet, carry on. Reads REBUILD_REPORT_LATEST.txt only; writes one line to reports\\."""
import datetime as dt, os, re, sys
tools = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(tools, "REBUILD_REPORT_LATEST.txt")
today = dt.date.today().isoformat()
when = ""
try:
    with open(p, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r"\s*when\s*:\s*(\d{4}-\d{2}-\d{2})", line)
            if m:
                when = m.group(1); break
except OSError:
    pass
note = os.path.join(tools, "reports", "MORNING_%s.txt" % dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
os.makedirs(os.path.dirname(note), exist_ok=True)
if when == today:
    open(note, "w").write("MORNING TASK %s -- the 03:10 run already happened today (%s). Nothing to do.\n" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), when))
    print("nightly already ran today (%s) -- morning task has nothing to do" % when)
    sys.exit(3)
open(note, "w").write("MORNING TASK %s -- no run today yet (last report %s). Running the nightly now.\n" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), when or "none"))
print("no nightly run today yet (last %s) -- running it now" % (when or "none"))
sys.exit(0)
