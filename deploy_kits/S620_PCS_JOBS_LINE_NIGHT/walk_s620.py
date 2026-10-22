#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s620.py -- kit S620 (S336, 22-Oct-2026): the jobs line's age rule follows the freshness check's own schedule.

    python3 walk_s620.py OLD NEW [--box]

Made-up freshness states at four clock times (IST): 08:00 after a 23:35 run -> no warning (the night gap); 08:20 after
23:35 -> none; 10:40 after 08:05 -> a warning (a missed hourly run); 08:45 after 23:35 -> a warning (08:05 did not run).
--box: this machine's real file, read only: the line reads. Exit 0 = GREEN ('WALK OK ...'); the S617 file goes RED.
"""
import calendar
import importlib.util
import json
import os
import shutil
import sys
import tempfile

old_p, new_p = sys.argv[1], sys.argv[2]
BOX = "--box" in sys.argv
passed, failed = [], []


def check(c, label):
    (passed if c else failed).append(label)
    print(("  ok   " if c else "  FAIL ") + label)
    return c


def load(p, tag):
    s = importlib.util.spec_from_file_location("sn_" + tag, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def epoch_ist(s):          # 'YYYY-mm-dd HH:MM' in IST -> epoch seconds
    import time as _t
    return calendar.timegm(_t.strptime(s, "%Y-%m-%d %H:%M")) - 19800


N = load(new_p, "n")
T = tempfile.mkdtemp(prefix="s620_walk_")
WARN = "has not reported for over three hours"
try:
    fr = os.path.join(T, "fresh.json")
    N.FRESHNESS_STATE = fr
    cases = [("2099-01-02 08:00", "2099-01-01T23:35:01", False, "08:00 after a 23:35 run: no warning (the night gap)"),
             ("2099-01-02 08:20", "2099-01-01T23:35:01", False, "08:20 after 23:35: no warning"),
             ("2099-01-02 10:40", "2099-01-02T08:05:01", True, "10:40 after 08:05: a warning (an hourly run missed)"),
             ("2099-01-02 08:45", "2099-01-01T23:35:01", True, "08:45 after 23:35: a warning (08:05 did not run)"),
             ("2099-01-02 15:10", "2099-01-02T14:35:01", False, "15:10 after 14:35: no warning")]
    ok_all = True
    for now_s, ran_iso, want, label in cases:
        json.dump({"last_run_iso": ran_iso, "legs_checked": 34, "not_ok_legs": []}, open(fr, "w"))
        line = N._jobs_line(epoch_ist(now_s))
        got = WARN in line
        ok_all = check(got == want and "all 34 on time" in line, label) and ok_all
finally:
    shutil.rmtree(T, ignore_errors=True)

if not ok_all:
    print("")
    print("WALK RED S620: %d passed, %d failed" % (len(passed), len(failed)))
    sys.exit(1)
if BOX:
    L = load(new_p, "box")
    ln = L._jobs_line()
    check("could not be read" not in ln, "on this machine the jobs line reads: %s" % ln.split(" (<a")[0][:110])
print("")
print(("WALK OK" if not failed else "WALK RED") + " S620: %d passed, %d failed" % (len(passed), len(failed)))
sys.exit(0 if not failed else 1)
