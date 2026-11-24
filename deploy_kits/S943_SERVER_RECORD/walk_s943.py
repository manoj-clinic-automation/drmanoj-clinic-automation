#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s943.py -- kit S943 on made-up data. No live file, no network, nothing written outside a temp folder.
    python3 walk_s943.py <kit folder> <scratch dir> [--control]
  1. server_record.py --selftest (made-up df/free/ps/du; the 90-day keep; the three warnings; tools missing)
  2. the console's reader (_s943_server_lines lifted from the kit's owner_console.py, stub L/when/_env): no record; a stale
     record; a fresh quiet record (green, three figures); a fresh record with warnings (amber + sub-lines); a broken JSON
     (raises -> piece() shows 'could not be read', the section stands)
  3. freshness_legs.json: valid, 42 legs, the 'server record' leg (file_mtime, 26 h), the other 41 byte-for-byte as the FROM
  --control: the lifted reader comes from the FROM owner_console.py (no S943 in it) -> must go red.   Last line: WALK n/n
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

KDIR = os.path.abspath(sys.argv[1])
SCR = os.path.abspath(sys.argv[2])
CONTROL = "--control" in sys.argv
os.makedirs(SCR, exist_ok=True)
n = f = 0


def ok(name, cond):
    global n, f
    n += 1
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        f += 1


# 1 ----------------------------------------------------------------------------------------------------------------- selftest
r = subprocess.run([sys.executable, "-B", os.path.join(KDIR, "server_record.py"), "--selftest"], capture_output=True, text=True,
                   env=dict(os.environ, TMPDIR=SCR))
ok("server_record.py --selftest %s" % (r.stdout.strip().splitlines() or ["?"])[-1], r.returncode == 0 and r.stdout.strip().endswith("SELFTEST 10/10"))

# 2 ------------------------------------------------------------------------------------------------------------ the console
src_p = os.path.join(KDIR, "owner_console.py") if not CONTROL else os.environ.get("OC_FROM", os.path.join(KDIR, "owner_console.py"))
src = open(src_p, encoding="utf-8").read()
i = src.find("SREC = _env(")
j = src.find("def sec_system(con, cx):")
lifted = src[i:j] if (i >= 0 and j > i) else "def _s943_server_lines(cx):\n    raise RuntimeError('no S943 in this console')\n"
calls = []


def L(dot, text, **kw):
    calls.append((dot, text, kw))
    return (dot, text, kw)


def when(ts, today):
    return "at " + str(ts)[11:16]


rec_p = os.path.join(SCR, "LATEST.json")
ns = {"os": os, "json": json, "dt": dt, "L": L, "when": when, "_env": lambda k, d: rec_p, "FIN": SCR}
exec(compile(lifted, "lifted_s943", "exec"), ns)
_fn = ns["_s943_server_lines"]


def fn(cx):
    try:
        return _fn(cx)
    except Exception as e:  # noqa: BLE001 -- the control's reader has no S943: every case then reads red
        if isinstance(e, (json.JSONDecodeError, ValueError)):
            raise
        return []


now = dt.datetime(2026, 11, 25, 9, 0, 0)
cx = {"now": now, "today": "2026-11-25"}


def rec(when_iso, warn=(), pct=29, avail=71e9, ram=5.0e9, l1=0.41):
    return {"when_iso": when_iso, "disks": [{"mount": "/", "pct": pct, "avail_b": avail}], "ram": {"available_b": ram},
            "load": {"l1": l1}, "warn": list(warn), "procs": [{"comm": "python3"}, {"comm": "gunicorn"}]}


def put(obj):
    open(rec_p, "w").write(json.dumps(obj) if not isinstance(obj, str) else obj)


if os.path.exists(rec_p):
    os.remove(rec_p)
out = fn(cx)
ok("no record yet: one grey line naming 02:50", len(out) == 1 and out[0][0] == "n" and "02:50" in out[0][1])
put(rec("2026-11-22T02:50:10"))
out = fn(cx)
ok("a stale record (3 days): one amber line", len(out) == 1 and out[0][0] == "w" and "not been written since" in out[0][1])
put(rec("2026-11-25T02:50:10"))
out = fn(cx)
ok("a fresh quiet record: ONE green line", len(out) == 1 and out[0][0] == "g")
t0 = out[0][1] if out else ""
why0 = (out[0][2].get("why") or "") if out else ""
ok("  ... with disk 29% (71 GB free), RAM 5.0 GB, load 0.41, recorded at 02:50",
   "disk 29% used (71 GB free)" in t0 and "RAM 5.0 GB available" in t0 and "load 0.41" in t0 and "recorded at 02:50" in t0)
ok("  ... the processes in the why, never in the line", "python3" in why0 and "python3" not in t0)
put(rec("2026-11-25T02:50:10", warn=["disk / at 85 % (15.0 GB free)", "RAM available 667 MB (under 1 GB)"], pct=85, avail=15e9, ram=0.7e9))
out = fn(cx)
ok("a fresh record with 2 warnings: amber line + 2 sub-lines", len(out) == 3 and out[0][0] == "w" and all(x[0] == "w" and x[2].get("sub") for x in out[1:]))
ok("  ... the sub-lines are the record's own words", len(out) == 3 and out[1][1].startswith("disk / at 85 %") and "667 MB" in out[2][1])
put(rec("2026-11-25T02:50:10", warn=["a", "b", "c", "d", "e", "f"]))
ok("more than four warnings: four shown", len(fn(cx)) == 5)
put("{not json")
try:
    fn(cx)
    raised = False
except Exception:  # noqa: BLE001
    raised = True
ok("a broken record raises (piece() then says 'could not be read'; the section stands)", raised)
ok("sec_system calls the piece after the heartbeat",
   re.search(r'piece\(lines, "The reception PC\'s heartbeat", beat\)\n\s+piece\(lines, "The server record", lambda: _s943_server_lines\(cx\)\)', src) is not None)

head = src[:src.find("def sec_system(con, cx):")]
ok("the console defines every name the reader leans on (_env, FIN, dt, json, L, when) before sec_system",
   all(x in head for x in ("def _env(", "FIN =", "import datetime as dt", "import json", "def L(", "def when(")))

# 3 --------------------------------------------------------------------------------------------------------------- the legs
lg = json.load(open(os.path.join(KDIR, "freshness_legs.json"), encoding="utf-8"))
legs = lg["legs"]
mine = [l for l in legs if l.get("name") == "server record"]
ok("42 legs, one 'server record' leg", len(legs) == 42 and len(mine) == 1)
ok("the leg: file_mtime on LATEST.json, 26 h, group Watchdog",
   mine and mine[0]["kind"] == "file_mtime" and mine[0]["target"].endswith("/server_record/LATEST.json") and mine[0]["max_age_h"] == 26 and mine[0]["group"] == "Watchdog")
lf = os.environ.get("LEGS_FROM")
if lf and os.path.exists(lf):
    old = json.load(open(lf, encoding="utf-8"))
    ok("the other 41 legs and the two notes exactly as the FROM", old["legs"] == legs[:-1] and old["_about"] == lg["_about"] and old["_windows"] == lg["_windows"])
ok("no ten-digit run in any kit file", not any(re.search(r"\d{10}", open(os.path.join(KDIR, x), encoding="utf-8", errors="ignore").read())
                                              for x in os.listdir(KDIR) if x.endswith((".py", ".json", ".sh", ".md"))))
print("WALK %d/%d" % (n - f, n))
sys.exit(1 if f else 0)
