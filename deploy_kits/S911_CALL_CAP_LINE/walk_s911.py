#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s911.py -- kit S911 on made-up files (no live file, no patient data).
  1. call_cap_s911.py on a copy of the engine: --check 1, --apply, --check 0, --apply again 'already'; the file still compiles;
     exactly 5 lines added; a control without the anchor: exit 2, file untouched.
  2. the console's reader (the function lifted from the built owner_console.py, with stub L/FIN): no folder; no log before and
     after the switch; a log with two CALL CAP lines and stamps (the newest wins, its stamp read); wait 0 -> green; a 200 KB log.
    python3 walk_s911.py <engine processor.py (the PC's bytes)> <built owner_console.py>
"""
import datetime as dt   # noqa: F401  (the lifted function uses dt, os, re)
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
n = f = 0


def ok(name, cond):
    global n, f
    n += 1
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        f += 1


def m8(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()[:8]


def run(*a):
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "call_cap_s911.py")] + list(a), capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main(engine, console):
    tmp = tempfile.mkdtemp(prefix="s911walk_")
    try:
        eng = os.path.join(tmp, "processor.py"); shutil.copy(engine, eng); h0 = m8(eng); l0 = open(eng, "rb").read().count(b"\n")
        ok("engine --check says not there (1)", run(eng)[0] == 1)
        ok("engine --apply inserts", run(eng, "--apply")[0] == 0 and "inserted" in run(eng)[1] or run(eng)[0] == 0)
        ok("engine --check now 0", run(eng)[0] == 0)
        ok("engine --apply again 'already'", "already" in run(eng, "--apply")[1])
        ok("engine changed, 5 lines added", m8(eng) != h0 and open(eng, "rb").read().count(b"\n") == l0 + 5)
        ok("engine still compiles", subprocess.run([sys.executable, "-m", "py_compile", eng], capture_output=True).returncode == 0)
        ok("the line is inside the cap block, after 'combined = _w'",
           re.search(r"combined = _w\n\s+try:\s+# S911", open(eng, encoding="utf-8").read()) is not None)
        ctl = os.path.join(tmp, "other.py"); open(ctl, "w").write("x = 1\n"); hc = m8(ctl)
        rc, _ = run(ctl)
        ok("control without the anchor: --check exit 2", rc == 2)
        rc, _ = run(ctl, "--apply")
        ok("control: --apply refuses, file untouched", rc != 0 and m8(ctl) == hc)
        # 2. the console's reader
        src = open(console, encoding="utf-8").read()
        i = src.index("FUT_DIR = os.path.join"); j = src.index("def sec_work(con, cx):")
        lifted = src[i:j]
        lines = []
        def L(dot, text, **kw):
            d = dict(dot=dot, text=text); d.update(kw); return d
        fin = os.path.join(tmp, "root", "finance"); os.makedirs(fin)
        ns = dict(os=os, re=re, dt=dt, L=L, FIN=fin)
        exec(compile(lifted, "lifted_s911", "exec"), ns)
        fn = ns["_s911_call_cap_lines"]; fut = os.path.join(tmp, "root", "followup_tracker")
        ok("no tracker folder -> no line", fn() == [])
        os.makedirs(os.path.join(fut, "logs")); open(os.path.join(fut, "OFF"), "w").close()
        r = fn(); ok("OFF present, no log -> the PC line", len(r) == 1 and r[0]["dot"] == "n" and "clinic PC makes it" in r[0]["text"])
        log = os.path.join(fut, "logs", "runner.log")
        open(log, "w").write("CALL CAP: kept 5 of 9 due for a call -- 4 wait for tomorrow\n")
        r = fn(); ok("OFF present, a line in the log -> still the PC line (never read as current)", len(r) == 1 and "clinic PC makes it" in r[0]["text"])
        os.unlink(os.path.join(fut, "OFF")); os.unlink(log)
        r = fn(); ok("OFF absent, no log -> 'not yet reported'", len(r) == 1 and "not yet reported" in r[0]["text"])
        open(log, "w").write("[2026-11-21 21:05:01] pass starts\nCALL CAP: kept 120 of 143 due for a call -- 23 wait for tomorrow\n"
                             "[2026-11-21 21:06:40] done\n[2026-11-22 21:05:03] pass starts\nnoise line\n"
                             "CALL CAP: kept 120 of 150 due for a call -- 30 wait for tomorrow\n[2026-11-22 21:06:10] done\n")
        r = fn()
        ok("newest line wins, with its stamp", len(r) == 1 and r[0]["dot"] == "n" and "120 of 150" in r[0]["text"] and "30 wait" in r[0]["text"]
           and "22-Nov 21:05" in r[0]["text"] and r[0].get("fig") == "120 of 150")
        open(log, "a").write("[2026-11-23 21:05:00] pass starts\nCALL CAP: kept 88 of 88 due for a call -- 0 wait for tomorrow\n")
        r = fn(); ok("wait 0 -> green, 'all 88'", len(r) == 1 and r[0]["dot"] == "g" and "all 88" in r[0]["text"])
        with open(log, "a") as fh:
            for k in range(4000):
                fh.write("[2026-11-24 21:05:%02d] filler line %d\n" % (k % 60, k))
            fh.write("CALL CAP: kept 100 of 101 due for a call -- 1 wait for tomorrow\n")
        r = fn(); ok("a 200 KB log: the tail is read, newest line found", len(r) == 1 and "100 of 101" in r[0]["text"] and os.path.getsize(log) > 150000)
        open(log, "w").write("CALL CAP: kept x of y due for a call -- z wait\n")
        r = fn(); ok("a garbled line -> treated as no line", len(r) == 1 and "not yet reported" in r[0]["text"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("WALK S911: %d of %d ok, %d failed" % (n - f, n, f))
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
