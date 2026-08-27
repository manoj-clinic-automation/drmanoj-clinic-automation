#!/usr/bin/python3
"""selftest_manojz_agent.py — asserted against the REAL pull log."""
import sys, os, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manojz_agent as M
_f, _p = [], 0
def ck(l, c, d=""):
    global _p
    if c: _p += 1; print("  ok   %s" % l)
    else: _f.append(l); print("  FAIL %s   %s" % (l, d))

print("[1] the line format — including the fractional seconds that broke v1")
m = M.LINE.match("27-08-2026 14:51:42.68  ok")
ck("a line WITH fractional seconds parses", bool(m), "this was the v1 bug")
ck("and its verdict is read", m and m.group(7) == "ok", m.group(7) if m else None)
ck("a line without fractions still parses", bool(M.LINE.match("27-08-2026 9:00:21  ok")))
ck("a non-log line is rejected", M.LINE.match("hello world") is None)

print("\n[2] gap arithmetic")
t = dt.datetime(2026, 8, 27, 11, 40)
runs = [(t, "ok"), (t + dt.timedelta(minutes=10), "ok"), (t + dt.timedelta(minutes=191), "ok")]
g = M.gaps(runs)
ck("one gap found, not two", len(g) == 1, repr(g))
ck("and it is 181 minutes", g and abs(g[0][2] - 181) < 0.1, repr(g))
ck("a clean 10-min cadence yields no gaps", M.gaps(runs[:2]) == [])

print("\n[3] against the live log")
runs = M.pull_runs()
ck("the real log parses", len(runs) > 50, "%d runs" % len(runs))
ck("every run carries a verdict", all(r[1] for r in runs))
bad = [r for r in runs if not r[1].endswith("ok")]
print("     runs %d · not-ok %d · gaps>15min %d" % (len(runs), len(bad), len(M.gaps(runs))))
ck("the 27-Aug 3-hour gap is detected",
   any(g[2] > 180 for g in M.gaps(runs)), repr(M.gaps(runs)))

print("\n[4] IT MUST BE ABLE TO RAISE THE ALARM — and to stay quiet")
txt, alarm = M.report(now=runs[-1][0] + dt.timedelta(minutes=5))
ck("5 minutes after a run: healthy", not alarm and "ALIVE" in txt)
txt, alarm = M.report(now=runs[-1][0] + dt.timedelta(minutes=25))
ck("25 minutes after: LATE + alarm", alarm and "LATE" in txt)
txt, alarm = M.report(now=runs[-1][0] + dt.timedelta(minutes=200))
ck("200 minutes after: SILENT + alarm", alarm and "SILENT" in txt)
ck("the alarm names what to do", "NEEDS A LOOK" in txt)

print("\n[5] the router side")
newest, n, kinds = M.last_ingest()
ck("index.csv reads", newest is not None and n > 0, "%s / %d" % (newest, n))

print("\n%d passed, %d failed" % (_p, len(_f)))
for f in _f: print("  FAILED:", f)
sys.exit(1 if _f else 0)
