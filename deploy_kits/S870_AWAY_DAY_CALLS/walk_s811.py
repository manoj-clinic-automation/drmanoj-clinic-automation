#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s811.py <kit dir> [--control | --write-broken <dir>] -- the walk of kit S811_FEED_ON_ARRIVAL on a made-up root
(made-up files, a stand-in sync, a stand-in push, a made-up docterz_export; no patient, no number, no real store).

PART A drives <kit dir>/finance/patient_sync_on_arrival.sh with bash, a set clock (PSOA_NOW) and a stand-in sync that records
every call. The stand-in carries a name of this walk's own (PSOA_SYNC), so that the server's real finance_patient_sync.py,
should it be running while the installer walks, is not taken for it -- and the walk's stand-in is not taken for the real one.
PART B imports <kit dir>/portal/docterz_missing_alert.py and drives run() with a stand-in pusher, then through its command line
with a stand-in ring_common; the ntfy fallback is posted to a listener of the walk's own on 127.0.0.1.
Last line: 'WALK OK n/n' or 'WALK RED k of n'.
--control: the SAME walk on two deliberately broken copies it makes itself (A: the stamp moves even when the sync fails;
B: the once-per-slot guard removed). The pass is 'CONTROL: red k of n ...' naming the checks that caught them.
--write-broken <dir>: writes those two broken copies into <dir> (for a reader) and stops."""
import datetime as dt
import fcntl
import http.server
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time

sys.dont_write_bytecode = True
A_REL = os.path.join("finance", "patient_sync_on_arrival.sh")
B_REL = os.path.join("portal", "docterz_missing_alert.py")
BREAK_A = ('if [ "$RC" = 0 ]; then', 'if true; then')
BREAK_B = ('        if entry is not _NONE:', '        if False and entry is not _NONE:')
MUST_CATCH = ("A07 a failing sync does not move the stamp", "B09 the same slot run again sends nothing more")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
SYNC_NAME = "walk%d_patient_sync.py" % os.getpid()

STANDIN_SYNC = r'''import os, sys, time
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "calls.txt"), "a") as fh:
    fh.write("%s|%s|%d\n" % (" ".join(sys.argv[1:]), os.getcwd(), sys.flags.dont_write_bytecode))
print("STAND-IN SYNC ran")
s = os.path.join(here, "sleep_s")
if os.path.exists(s):
    time.sleep(float(open(s).read()))
c = os.path.join(here, "exit_code")
sys.exit(int(open(c).read()) if os.path.exists(c) else 0)
'''
STANDIN_RING = r'''import json, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
def subs_for(user, path=None):
    return [{"endpoint": "made-up-1"}, {"endpoint": "made-up-2"}] if user == "manoj" else []
def push_user(user, payload):
    if os.path.exists(os.path.join(HERE, "raise")):
        raise RuntimeError("stand-in push refuses")
    if os.path.exists(os.path.join(HERE, "sleep")):
        time.sleep(float(open(os.path.join(HERE, "sleep")).read()))
    with open(os.path.join(HERE, "pushed.txt"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps([user, payload]) + "\n")
    return 1, 0
'''


def make_broken(kit, out):
    for rel, (a, b) in ((A_REL, BREAK_A), (B_REL, BREAK_B)):
        src = open(os.path.join(kit, rel), encoding="utf-8").read()
        if src.count(a) != 1:
            raise SystemExit("WALK RED: the line the control breaks is not there exactly once in %s" % rel)
        os.makedirs(os.path.dirname(os.path.join(out, rel)), exist_ok=True)
        with open(os.path.join(out, rel), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(src.replace(a, b))


def walk(kit, tmp):
    res = []

    def chk(name, ok, got=""):
        res.append((name, bool(ok), got))

    # ================================================================= PART A
    script = os.path.join(kit, A_REL)
    base = (dt.datetime.now(IST) + dt.timedelta(days=2)).date()          # the set clock is two days ahead: every real file is old

    def at(hh, mm, plus=0):
        return int(dt.datetime(base.year, base.month, base.day, hh, mm, tzinfo=IST).timestamp()) + plus

    def mkroot(name):
        r = os.path.join(tmp, name, "root")
        os.makedirs(os.path.join(r, "finance", "_off"))
        os.makedirs(os.path.join(r, "wa", "followup-inbox"))
        with open(os.path.join(r, "finance", SYNC_NAME), "w") as fh:
            fh.write(STANDIN_SYNC)
        for n in ("Visit_Ledger_Join.xlsx", "Patient_Master_Join.xlsx"):
            put(r, n, "made-up workbook 1", at(0, 0) - 3 * 3600)        # the evening before
        return r

    def put(r, n, text, mtime):
        p = os.path.join(r, "wa", "followup-inbox", n)
        with open(p, "w") as fh:
            fh.write(text)
        os.utime(p, (mtime, mtime))

    def tick(r, now, **env):
        e = dict(os.environ, PSOA_ROOT=r, PSOA_PY=sys.executable, PSOA_NOW=str(now), PSOA_LOCK=os.path.join(r, "tick.lock"),
                 PSOA_SYNC=os.path.join(r, "finance", SYNC_NAME), TZ="Asia/Kolkata")
        e.update({k: str(v) for k, v in env.items()})
        p = subprocess.run(["bash", script], env=e, capture_output=True, text=True, timeout=60)
        return p.returncode, (p.stdout + p.stderr)

    def calls(r):
        p = os.path.join(r, "finance", "calls.txt")
        return open(p).read().splitlines() if os.path.exists(p) else []

    def log(r):
        p = os.path.join(r, "finance", "patient_sync_on_arrival.log")
        return open(p).read() if os.path.exists(p) else ""

    def stamp(r):
        p = os.path.join(r, "finance", ".patient_sync_on_arrival.stamp")
        return open(p).read() if os.path.exists(p) else None

    T = at(21, 26)
    r = mkroot("a1")
    rc, out = tick(r, T)
    chk("A01 first run, no stamp yet: the sync runs once, exit 0, stamp made", rc == 0 and len(calls(r)) == 1 and stamp(r) and
        "sync ran, exit 0 (the first run" in log(r), (rc, calls(r), log(r)))
    c0 = (calls(r) or ["||"])[0].split("|")
    chk("A02 the sync is called the cron way: no arguments, from root's home, with -B, into patient_sync.log",
        c0[0] == "" and os.path.realpath(c0[1]) == os.path.realpath(r) and c0[2] == "1" and
        "STAND-IN SYNC ran" in open(os.path.join(r, "finance", "patient_sync.log")).read(), c0)
    l1 = log(r)
    rc, out = tick(r, T + 300)
    chk("A03 unchanged workbooks: nothing runs, nothing is said, nothing is logged (the quiet tick)",
        rc == 0 and out == "" and len(calls(r)) == 1 and log(r) == l1, (rc, out, calls(r)))
    lp = os.path.join(r, "finance", "patient_sync_on_arrival.log")
    os.utime(lp, (1000000, 1000000))
    tick(r, T + 310)
    chk("A21 the quiet tick moves only the TIME of its log (job_pulse reads that as the pulse): same words, a fresh time",
        log(r) == l1 and time.time() - os.path.getmtime(lp) < 60, (log(r) == l1, os.path.getmtime(lp)))
    put(r, "Visit_Ledger_Join.xlsx", "made-up workbook 2 (newer)", T + 400)
    rc, out = tick(r, T + 600)
    chk("A04 a new visits workbook: the sync runs once more", len(calls(r)) == 2 and out == "", (calls(r), out))
    put(r, "Patient_Master_Join.xlsx", "made-up master 2", T + 700)
    tick(r, T + 900)
    tick(r, T + 1200)
    chk("A05 a new master workbook alone also starts it, once", len(calls(r)) == 3, calls(r))

    r = mkroot("a6")
    tick(r, T)
    put(r, "Visit_Ledger_Join.xlsx", "half written", T + 290)
    rc, out = tick(r, T + 300)
    chk("A06 a workbook written 10 seconds ago: it waits (and says why); 5 minutes later it runs",
        len(calls(r)) == 1 and "less than 60 seconds ago" in log(r) and out == "" and
        (tick(r, T + 600), len(calls(r)))[1] == 2, (calls(r), log(r)))

    r = mkroot("a7")
    tick(r, T)
    s0 = stamp(r)
    put(r, "Visit_Ledger_Join.xlsx", "made-up workbook 2 (newer)", T + 100)
    open(os.path.join(r, "finance", "exit_code"), "w").write("1")
    rc, out = tick(r, T + 300)
    chk("A07 a failing sync does not move the stamp", rc == 0 and len(calls(r)) == 2 and stamp(r) == s0 and
        "sync FAILED, exit 1" in log(r), (rc, len(calls(r)), stamp(r) == s0, log(r)))
    tick(r, T + 600)
    tick(r, T + 900)
    chk("A08 after a failure: no new try 5 and 10 minutes later (said in the log)",
        len(calls(r)) == 2 and log(r).count("the last sync failed") == 2, (len(calls(r)), log(r)))
    tick(r, T + 1200)
    chk("A09 15 minutes after the failure it is tried again", len(calls(r)) == 3, (len(calls(r)), log(r)))
    os.remove(os.path.join(r, "finance", "exit_code"))
    tick(r, T + 1500)
    n_before = len(calls(r))
    tick(r, T + 2100)
    chk("A10 the try that succeeds moves the stamp and clears the failure; then quiet again",
        n_before == 3 and len(calls(r)) == 4 and stamp(r) != s0 and
        not os.path.exists(os.path.join(r, "finance", ".patient_sync_on_arrival.fail")) and
        (tick(r, T + 2400), len(calls(r)))[1] == 4, (n_before, len(calls(r)), log(r)))

    r = mkroot("a11")
    lk = os.path.join(r, "tick.lock")
    fd = os.open(lk, os.O_CREAT | os.O_RDWR)
    fcntl.flock(fd, fcntl.LOCK_EX)
    rc, out = tick(r, T)
    held = (len(calls(r)), log(r))
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)
    tick(r, T + 300)
    chk("A11 the lock held by another tick: skipped and said; once free it runs",
        held[0] == 0 and "lock held" in held[1] and len(calls(r)) == 1, (held, calls(r)))

    r = mkroot("a12")
    open(os.path.join(r, "finance", "sleep_s"), "w").write("3")
    bg = subprocess.Popen([sys.executable, "-B", os.path.join(r, "finance", SYNC_NAME)], cwd=r,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        if calls(r):
            break
        time.sleep(0.05)
    rc, out = tick(r, T)
    during = (len(calls(r)), log(r))
    bg.wait()
    os.remove(os.path.join(r, "finance", "sleep_s"))
    tick(r, T + 300)
    chk("A12 a sync already running (the hourly one): this tick is skipped and says so; the next tick runs",
        during[0] == 1 and "running already" in during[1] and len(calls(r)) == 2, (during, calls(r)))

    r = mkroot("a13")
    open(os.path.join(r, "finance", "_off", "ALL_OFF"), "w").close()
    rc, out = tick(r, T)
    off1 = (rc, out, len(calls(r)), log(r))
    os.remove(os.path.join(r, "finance", "_off", "ALL_OFF"))
    open(os.path.join(r, "finance", "_off", "PATIENT_SYNC_ON_ARRIVAL_OFF"), "w").close()
    rc, out = tick(r, T)
    off2 = (rc, out, len(calls(r)), log(r))
    chk("A13 ALL_OFF, or its own off switch: nothing at all (no sync, no word, no log)",
        off1 == (0, "", 0, "") and off2 == (0, "", 0, ""), (off1, off2))

    got = []
    for i, (hh, mm) in enumerate(((1, 24), (1, 25), (1, 50), (2, 14), (2, 15))):
        r = mkroot("a14_%d" % i)
        tick(r, at(hh, mm))
        got.append((len(calls(r)), "nightly backups" in log(r)))
    chk("A14 01:25-02:15, the nightly backups' time: nothing runs (01:25, 01:50, 02:14); 01:24 and 02:15 run",
        got == [(1, False), (0, True), (0, True), (0, True), (1, False)], got)
    r = mkroot("a15")
    tick(r, at(1, 50))
    tick(r, at(2, 20))
    chk("A15 a workbook that waited through the backups' time is folded on the next tick after", len(calls(r)) == 1, calls(r))

    got = []
    for i, (hh, mm) in enumerate(((8, 20), (21, 20), (22, 20), (7, 20), (21, 25))):
        r = mkroot("a16_%d" % i)
        tick(r, at(hh, mm))
        got.append((len(calls(r)), "hourly sync's own minute" in log(r)))
    chk("A16 the hourly run's own minute (08:20, 21:20) is left to it; 22:20, 07:20 and 21:25 run",
        got == [(0, True), (0, True), (1, False), (1, False), (1, False)], got)

    r = mkroot("a17")
    open(os.path.join(r, "finance", "sleep_s"), "w").write("9")
    t0 = time.time()
    rc, out = tick(r, T, PSOA_TIMEOUT=1)
    chk("A17 a sync that hangs is stopped at its time limit: a failure, the stamp not made",
        rc == 0 and stamp(r) is None and "exit 124 (stopped after 1 seconds)" in log(r) and time.time() - t0 < 7,
        (rc, stamp(r), log(r), round(time.time() - t0, 1)))

    r = mkroot("a18")
    os.remove(os.path.join(r, "wa", "followup-inbox", "Patient_Master_Join.xlsx"))
    rc, out = tick(r, T)
    chk("A18 one workbook not in the inbox: nothing (the sync itself would refuse)", (rc, out, len(calls(r)), log(r)) == (0, "", 0, ""),
        (rc, out, calls(r), log(r)))

    r = mkroot("a19")
    lp = os.path.join(r, "finance", "patient_sync_on_arrival.log")
    with open(lp, "w") as fh:
        fh.write(("2026-01-01 00:00:00 an old made-up line to fill the log\n") * 6000)
    big = os.path.getsize(lp)
    put(r, "Visit_Ledger_Join.xlsx", "half written", T - 10)
    tick(r, T)
    chk("A19 the log is cut back before 200 KB and keeps its newest line whole",
        big > 300000 and os.path.getsize(lp) < 200000 and log(r).splitlines()[-1].endswith("it may still be arriving") and
        log(r).splitlines()[0].startswith("2026-01-01 00:00:00 an old"), (big, os.path.getsize(lp), log(r)[-120:]))

    r = mkroot("a20")
    tick(r, T)
    tick(r, T + 300)
    left = sorted(os.listdir(os.path.join(r, "finance")))
    chk("A20 what it leaves on the box: its stamp and its log only (no .next, no .fail, no .cut)",
        left == sorted([".patient_sync_on_arrival.stamp", "_off", "calls.txt", SYNC_NAME, "patient_sync.log",
                        "patient_sync_on_arrival.log"]), left)


    r = mkroot("a22")
    open(os.path.join(r, "finance", "sleep_s"), "w").write("3")
    hand = subprocess.Popen([sys.executable, "-B", SYNC_NAME], cwd=os.path.join(r, "finance"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        if calls(r):
            break
        time.sleep(0.05)
    tick(r, T)
    during = (len(calls(r)), log(r))
    hand.wait()
    chk("A22 a sync started BY HAND by its bare name (cd into the folder, python3 <name>) is seen too: the tick is skipped",
        during[0] == 1 and "running already" in during[1], during)
    r = mkroot("a23")
    ed = subprocess.Popen(["bash", "-c", "sleep 3", "editor", os.path.join(r, "finance", SYNC_NAME)])
    other = subprocess.Popen([sys.executable, "-B", "-c", "import time; time.sleep(3)", os.path.join(r, "finance", SYNC_NAME)])
    time.sleep(0.4)
    tick(r, T)
    for q in (ed, other):
        q.kill()
        q.wait()
    chk("A23 a process that merely NAMES the file -- an editor left open on it, or another python job given its name -- does not "
        "hold the tick back", len(calls(r)) == 1, (calls(r), log(r)))
    r = mkroot("a24")
    rc, out = tick(r, T, PSOA_LOCK=os.path.join(r, "no", "such", "folder", "x.lock"))
    chk("A24 a lock file that cannot be opened: exit 0, said in the log, no sync, not one word on stdout or stderr",
        rc == 0 and out == "" and len(calls(r)) == 0 and "could not be opened" in log(r), (rc, out, log(r)))
    r = mkroot("a25")
    tick(r, T)
    lp = os.path.join(r, "finance", "patient_sync_on_arrival.log")
    open(lp, "w").close()
    os.utime(lp, (1000000, 1000000))
    rc, out = tick(r, T + 300)
    chk("A25 the quiet tick moves the time of an EMPTY log too (what cron's >> makes), and writes nothing into it",
        time.time() - os.path.getmtime(lp) < 60 and os.path.getsize(lp) == 0 and out == "", (os.path.getmtime(lp), os.path.getsize(lp)))
    r = mkroot("a26")
    tick(r, T)
    put(r, "Visit_Ledger_Join.xlsx", "made-up workbook 2 (newer)", T + 3 * 3600)
    tick(r, T + 300)
    chk("A26 a workbook whose time is 3 hours AHEAD of this clock is folded all the same (not waited for all night)", len(calls(r)) == 2,
        (calls(r), log(r)))

    # ================================================================= PART B
    try:
        spec = importlib.util.spec_from_file_location("docterz_missing_alert", os.path.join(kit, B_REL))
        dma = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dma)
    except Exception as e:                                   # noqa: BLE001
        chk("B00 the alert script loads", False, repr(e))
        return res

    MON9, TUE, WED, THU, FRI, SAT, SUN, MON, TUE17 = [dt.date(2026, 11, d) for d in (9, 10, 11, 12, 13, 14, 15, 16, 17)]
    n = [0]

    def mkdb(rows=(), slips=(), no_table=False, no_slip=False):
        n[0] += 1
        p = os.path.join(tmp, "fin%d.db" % n[0])
        c = sqlite3.connect(p)
        if not no_table:
            c.execute("CREATE TABLE docterz_export (id INTEGER PRIMARY KEY AUTOINCREMENT, drive_id TEXT NOT NULL, drive_name TEXT NOT NULL "
                      "DEFAULT '', drive_mtime TEXT NOT NULL DEFAULT '', md5 TEXT NOT NULL, kind TEXT NOT NULL, business_date TEXT NOT NULL "
                      "DEFAULT '', rows INTEGER NOT NULL DEFAULT 0, stored TEXT NOT NULL DEFAULT '', status TEXT NOT NULL, note TEXT NOT NULL "
                      "DEFAULT '', taken_at TEXT NOT NULL, due_from TEXT NOT NULL DEFAULT '', due_to TEXT NOT NULL DEFAULT '')")
            add(c, "consultation", dt.date(2026, 10, 1))             # the first export the server ever took
            for row in rows:
                add(c, *row)
        if not no_slip:
            c.execute("CREATE TABLE slip (id INTEGER PRIMARY KEY AUTOINCREMENT, series TEXT NOT NULL, slip_no INTEGER NOT NULL, day TEXT NOT NULL, "
                      "state TEXT NOT NULL DEFAULT 'ok')")
            for i, (day, state) in enumerate(slips):
                c.execute("INSERT INTO slip(series, slip_no, day, state) VALUES('opd', ?, ?, ?)", (100 + i, day.isoformat(), state))
        c.commit()
        c.close()
        return p

    def add(c, kind, day, status="current", due_to=""):
        c.execute("INSERT INTO docterz_export(drive_id, md5, kind, business_date, rows, status, taken_at, due_to) VALUES(?,?,?,?,?,?,?,?)",
                  ("made-up-%s-%s-%s" % (kind, day, status), "0" * 32, kind, day.isoformat(), 5, status, day.isoformat() + " 21:20:00",
                   due_to if isinstance(due_to, str) else due_to.isoformat()))

    class Push:
        def __init__(self, ret=(1, 0), boom=False, script=None):
            self.log, self.ret, self.boom, self.script, self.calls = [], ret, boom, list(script or []), 0

        def __call__(self, who, payload):
            self.calls += 1
            if self.boom:
                raise RuntimeError("made-up push failure")
            ret = self.script.pop(0) if self.script else self.ret
            if ret[0]:
                self.log.append((who, payload["title"], payload["body"], payload.get("url"), payload.get("tag")))
            return ret

    def go(slot, day, hm, db, state=None, pusher=None, **kw):
        n[0] += 1
        state = state or os.path.join(tmp, "state%d.json" % n[0])
        pusher = pusher or Push()
        now = dt.datetime.combine(day, dt.time(*hm))
        return dma.run(slot, now=now, db=db, state=state, pusher=pusher, off_dir=os.path.join(tmp, "no_off"), **kw), pusher, state

    EVE, MORN = (21, 45), (8, 15)
    CONS = ("consultation", THU)
    FU = ("followup", THU, "current", FRI)
    S = ((THU, "ok"), (THU, "ok"), (THU, "missing"))
    SATS = ((SAT, "ok"),)
    said = []                                                           # every message of the walk, for the checks on the words

    def one(p):
        said.extend(p.log)
        return p.log[0] if len(p.log) == 1 else ("", "", "", "", "")

    r_, p, _ = go("evening", THU, EVE, mkdb([CONS, FU], S))
    chk("B01 both reports on the server: nothing sent", not p.log and r_["why"] == "both", (r_, p.log))
    r_, p, _ = go("evening", THU, EVE, mkdb([CONS], S))
    m = one(p)
    chk("B02 the consultation report only: ONE notification to the owner naming the follow-up log and the day",
        m[0] == "manoj" and m[1] == "Docterz export missing at 9:45 pm (Thu 12 Nov)" and
        m[2] == "The follow-up log has not come from reception; the consultation report has. Unless it comes tonight, tomorrow's calling "
                "list will be made from the last log.", p.log)
    r_, p, _ = go("evening", THU, EVE, mkdb([FU], S))
    m = one(p)
    chk("B03 the follow-up log only: one notification naming the consultation report",
        m[2] == "The consultation report has not come from reception; the follow-up log has. Unless it comes tonight, today's visits "
                "will not be on record tomorrow morning.", p.log)
    r_, p, _ = go("evening", THU, EVE, mkdb([], ()))
    chk("B04 neither report and no slip that day: a closed day, nothing sent", not p.log and r_["why"] == "no_work", (r_, p.log))
    r_, p, _ = go("evening", THU, EVE, mkdb([], ((THU, "missing"), (THU, "void"), (WED, "ok"))))
    chk("B05 only another day's slips, or slips that are not 'ok': still no sign of work, nothing sent", not p.log, (r_, p.log))
    r_, p, _ = go("evening", THU, EVE, mkdb([], S))
    m = one(p)
    chk("B06 neither report but slips were logged: one notification naming both",
        m[2] == "Neither the consultation report nor the follow-up log has come from reception. Unless the consultation report comes "
                "tonight, today's visits will not be on record tomorrow morning. Unless the follow-up log comes tonight, tomorrow's "
                "calling list will be made from the last log.", p.log)
    r_, p, _ = go("evening", THU, EVE, mkdb([], (), no_slip=True))
    chk("B07 no slip table at all and neither report: nothing sent, and the line says the slips could not be read",
        not p.log and "slip table could not be read" in r_["line"], (r_, p.log))
    r_, p, _ = go("evening", SUN, EVE, mkdb([], ((SUN, "ok"),)))
    chk("B08 a Sunday evening is never judged", not p.log and r_["why"] == "sunday", (r_, p.log))

    db = mkdb([CONS], S)
    r1, p1, st = go("evening", THU, EVE, db)
    r2, p2, _ = go("evening", THU, (21, 50), db, state=st)
    chk("B09 the same slot run again sends nothing more", len(p1.log) == 1 and not p2.log and r2["why"] == "told", (p1.log, p2.log, r2))
    r3, p3, _ = go("morning", FRI, MORN, db, state=st)
    m = one(p3)
    chk("B10 next morning, still missing: one more notification, naming the day it is about",
        m[1] == "Docterz export still missing (Thu 12 Nov)" and
        m[2] == "Still missing this morning from Thursday 12 Nov: the follow-up log has not come from reception; the consultation report "
                "has. Until it comes, today's calling list is made from the last log.", p3.log)
    r4, p4, _ = go("morning", FRI, (8, 20), db, state=st)
    told = json.load(open(st))["told"]
    chk("B11 the morning slot is also said once; the state holds one entry per report-day and slot",
        not p4.log and sorted(told) == ["2026-11-12|evening", "2026-11-12|morning"], (p4.log, told))
    db = mkdb([CONS], S)
    r1, p1, st = go("evening", THU, EVE, db)
    c = sqlite3.connect(db)
    add(c, *FU)
    c.commit()
    c.close()
    r2, p2, _ = go("morning", FRI, MORN, db, state=st)
    chk("B12 the log came overnight (the morning catch-up): the morning says nothing", len(p1.log) == 1 and not p2.log and r2["why"] == "both",
        (p1.log, p2.log))

    # ---- fix 10: the morning speaks about the LAST WORKING DAY; nothing on a Sunday morning
    db = mkdb([("consultation", SAT)], SATS)
    r_, p, st = go("morning", MON, MORN, db)
    m = one(p)
    chk("B13 MONDAY morning judges SATURDAY: said, about Saturday by name, under Saturday's key",
        r_["day"] == "2026-11-14" and m[1] == "Docterz export still missing (Sat 14 Nov)" and
        m[2] == "Still missing this morning from Saturday 14 Nov: the follow-up log has not come from reception; the consultation report "
                "has. Until it comes, today's calling list is made from the last log." and
        list(json.load(open(st))["told"]) == ["2026-11-14|morning"], (r_, p.log))
    r_, p, _ = go("morning", SUN, MORN, db)
    r2, p2, _ = go("morning", TUE17, MORN, mkdb([("consultation", MON)], ((MON, "ok"),)))
    r3, p3, _ = go("morning", MON, MORN, mkdb([("consultation", SAT), ("followup", SAT, "current", MON)], ((SUN, "ok"),)))
    said.extend(p2.log)
    chk("B14 no message on a SUNDAY morning (Saturday's miss waits for Monday); Tuesday morning judges Monday; a Saturday that is "
        "whole says nothing on Monday", not p.log and r_["why"] == "sunday" and len(p2.log) == 1 and "from Monday 16 Nov" in p2.log[0][2] and
        not p3.log and r3["day"] == "2026-11-14" and r3["why"] == "both", (r_, p.log, p2.log, r3))

    r_, p, _ = go("evening", SAT, EVE, mkdb([("consultation", SAT)], SATS))
    m = one(p)
    r2, p2, _ = go("evening", SAT, EVE, mkdb([("consultation", SAT), ("followup", SAT, "current", SUN)], SATS))
    m2 = one(p2)
    chk("B15 Saturday evening: the list named is Monday's, 'before Monday morning'; a Saturday log that stops on Sunday is not "
        "'reached' (the staff page's rule) and is said as short",
        m[2] == "The follow-up log has not come from reception; the consultation report has. Unless it comes before Monday morning, "
                "Monday's calling list will be made from the last log." and
        m2[2] == "The follow-up log that came from reception reaches only Sun 15 Nov; the consultation report has come. Unless a longer "
                 "one comes before Monday morning, Monday's calling list will be short.", (p.log, p2.log))
    r_, p, _ = go("evening", SAT, EVE, mkdb([("consultation", SAT), ("followup", SAT, "current", MON)], SATS))
    chk("B16 a Saturday log that reaches Monday, and one with no due date recorded, are 'reached'",
        not p.log and not go("evening", THU, EVE, mkdb([CONS, ("followup", THU, "current", "")], S))[1].log, p.log)
    r_, p, _ = go("evening", THU, EVE, mkdb([CONS, ("followup", THU, "superseded", FRI), ("followup", THU, "quarantined", FRI),
                                             ("followup", WED, "current", FRI)], S))
    m = one(p)
    chk("B17 a superseded or set-aside export, or another day's, is not 'reached'", m[2].startswith("The follow-up log has not come"), p.log)

    off = os.path.join(tmp, "off_dir")
    os.makedirs(off)
    open(os.path.join(off, "ALL_OFF"), "w").close()
    pz = Push()
    rz = dma.run("evening", now=dt.datetime.combine(THU, dt.time(*EVE)), db=mkdb([CONS], S), state=os.path.join(tmp, "st_off.json"),
                 pusher=pz, off_dir=off)
    chk("B18 ALL_OFF: nothing sent, nothing said, no state and no lock written",
        not pz.log and rz["line"] == "" and not os.path.exists(os.path.join(tmp, "st_off.json")) and
        not os.path.exists(os.path.join(tmp, "st_off.json.lock")), (rz, pz.log))

    # ---- fix 6: the words of every other branch, exactly
    want = [
        ("evening", THU, EVE, [("followup", THU, "current", THU)], S, "Docterz export missing at 9:45 pm (Thu 12 Nov)",
         "The consultation report has not come from reception, and the follow-up log that came reaches only Thu 12 Nov. Unless the "
         "consultation report comes tonight, today's visits will not be on record tomorrow morning. Unless a longer follow-up log comes "
         "tonight, tomorrow's calling list will be short."),
        ("evening", THU, EVE, [CONS, ("followup", THU, "current", THU)], S, "Docterz export missing at 9:45 pm (Thu 12 Nov)",
         "The follow-up log that came from reception reaches only Thu 12 Nov; the consultation report has come. Unless a longer one comes "
         "tonight, tomorrow's calling list will be short."),
        ("morning", FRI, MORN, [], S, "Docterz export still missing (Thu 12 Nov)",
         "Still missing this morning from Thursday 12 Nov: neither the consultation report nor the follow-up log has come from reception. "
         "Until the consultation report comes, that day's visits are not on record. Until the follow-up log comes, today's calling list is "
         "made from the last log."),
        ("morning", FRI, MORN, [FU], S, "Docterz export still missing (Thu 12 Nov)",
         "Still missing this morning from Thursday 12 Nov: the consultation report has not come from reception; the follow-up log has. "
         "Until it comes, that day's visits are not on record."),
        ("morning", FRI, MORN, [CONS, ("followup", THU, "current", THU)], S, "Docterz export still missing (Thu 12 Nov)",
         "Still missing this morning from Thursday 12 Nov: the follow-up log that came from reception reaches only Thu 12 Nov; the "
         "consultation report has come. Until a longer one comes, today's calling list is short."),
        ("morning", FRI, MORN, [("followup", THU, "current", THU)], S, "Docterz export still missing (Thu 12 Nov)",
         "Still missing this morning from Thursday 12 Nov: the consultation report has not come from reception, and the follow-up log that "
         "came reaches only Thu 12 Nov. Until the consultation report comes, that day's visits are not on record. Until a longer follow-up "
         "log comes, today's calling list is short."),
        ("evening", SAT, EVE, [], SATS, "Docterz export missing at 9:45 pm (Sat 14 Nov)",
         "Neither the consultation report nor the follow-up log has come from reception. Unless the consultation report comes tonight, "
         "today's visits will not be on record tomorrow morning. Unless the follow-up log comes before Monday morning, Monday's calling "
         "list will be made from the last log."),
    ]
    wrong = []
    for slot, day, hm, rows, sl, title, body in want:
        m = one(go(slot, day, hm, mkdb(rows, sl))[1])
        if (m[1], m[2]) != (title, body):
            wrong.append((slot, day.isoformat(), m[1], m[2]))
    chk("B19 the words of the seven other branches (short log, both missing, mornings, Saturday), each exactly as written", not wrong, wrong)
    days = r"\((Mon|Tue|Wed|Thu|Fri|Sat) \d{1,2} Nov\)$"
    bad_words = []
    for _w, t, b, u, g in said:
        sentences = [x.strip() for x in b.replace(": ", ". ").split(". ") if x.strip()]
        if not re.search(days, t):
            bad_words.append(("the title does not name the day", t))
        if any((" will " in x) and not x.startswith("Unless ") for x in sentences):
            bad_words.append(("a 'will' that is not under an 'Unless'", b))
        if any((" is made " in x or " is short" in x or " are not on record" in x) and not x.startswith("Until ") for x in sentences):
            bad_words.append(("a present claim that is not under an 'Until'", b))
        if re.search(r"\d{4,}", t + b) or not all(ord(ch) < 128 for ch in t + b) or u != "/finance/console":
            bad_words.append(("a long number, a non-ASCII letter or another link", t, b, u))
    chk("B20 over all %d messages of this walk: every title names the day and date; every 'will' stands under an 'Unless' and every "
        "present claim under an 'Until' (nothing a later export can make false); no run of 4 digits, plain letters only, the link is "
        "his console" % len(said), len(said) >= 15 and not bad_words, bad_words[:3])

    # ---- fix 5: a push nothing took is tried twice more, 60 seconds apart; then the ntfy topic; told only on a delivery
    db = mkdb([CONS], S)
    r1, pb, st = go("evening", THU, EVE, db, pusher=Push(boom=True))
    r2, p2, _ = go("evening", THU, (21, 50), db, state=st)
    chk("B21 the push itself failing (one try, no fallback): no crash, said in the line, not counted as told -- a later run still tells him",
        r1["why"] == "undelivered" and "NOT DELIVERED" in r1["line"] and pb.calls == 1 and len(p2.log) == 1, (r1, p2.log))
    naps = []
    r1, p1, st = go("evening", THU, EVE, db, pusher=Push(script=[(0, 1), (0, 0), (1, 0)]), push_tries=3, sleep=naps.append)
    chk("B22 no device took it twice, the third push is taken: three pushes, 60 seconds apart, each failed try said in its own line, "
        "counted as told once", p1.calls == 3 and naps == [60, 60] and len(r1["progress"]) == 2 and "push 1 of 3" in r1["progress"][0] and
        "push 2 of 3" in r1["progress"][1] and r1["why"] == "pushed" and "push 3 of 3" in r1["line"] and
        json.load(open(st))["told"]["2026-11-12|evening"]["sent"] == 1, (r1, naps))
    took = []

    def ntfy_ok(title, body):
        took.append((title, body))
        return True, "the ntfy topic took it"
    naps = []
    r1, p1, st = go("evening", THU, EVE, db, pusher=Push(ret=(0, 1)), push_tries=3, sleep=naps.append, ntfy=ntfy_ok)
    r2, p2, _ = go("evening", THU, (21, 50), db, state=st, ntfy=ntfy_ok)
    chk("B23 three pushes nothing took: the ntfy topic is used once, with the same words; that counts as told (a second run sends nothing)",
        p1.calls == 3 and naps == [60, 60] and len(took) == 1 and took[0][0] == "Docterz export missing at 9:45 pm (Thu 12 Nov)" and
        took[0][1].startswith("The follow-up log has not come") and r1["why"] == "ntfy" and r2["why"] == "told" and p2.calls == 0, (r1, r2, took))
    r1, p1, st = go("evening", THU, EVE, db, pusher=Push(ret=(0, 0)), push_tries=3, sleep=naps.append,
                    ntfy=lambda t, b: (False, "the ntfy topic did not take it (made up)"))
    r2, p2, st2 = go("evening", THU, EVE, db, pusher=Push(ret=(0, 0)), push_tries=3, sleep=naps.append)
    chk("B24 three pushes and the ntfy topic all fail (or there is no fallback): NOT DELIVERED, and the slot is NOT counted as told",
        r1["why"] == "undelivered" and "NOT DELIVERED" in r1["line"] and "did not take it" in r1["line"] and json.load(open(st))["told"] == {} and
        r2["why"] == "undelivered" and json.load(open(st2))["told"] == {}, (r1, r2))
    ticks = iter([0, 500, 500, 500, 500, 500])
    r1, p1, _ = go("evening", THU, EVE, db, pusher=Push(ret=(0, 1)), push_tries=3, sleep=naps.append, clock=lambda: next(ticks))
    chk("B25 the run's time is capped: once another try would pass the limit, none is begun", p1.calls == 1 and
        "no time left for another try" in r1["progress"][0] and r1["why"] == "undelivered", (p1.calls, r1))

    posts = []

    class Catch(http.server.BaseHTTPRequestHandler):
        def do_POST(self):                                                # noqa: N802
            posts.append((self.path, self.headers.get("Title"), self.headers.get("Tags"),
                          self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8")))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *a):
            pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), Catch)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    os.environ["no_proxy"] = os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    conf = os.path.join(tmp, "made_up_freshness.conf")
    with open(conf, "w") as fh:
        fh.write("# a made-up conf in the real one's shape\nSTATE_FILE=/nowhere\nNTFY_URL = http://127.0.0.1:%d/made-up-topic\n" % srv.server_address[1])
    ok1 = dma.send_ntfy("Docterz export missing at 9:45 pm (Thu 12 Nov)", "made-up words", conf)
    empty = os.path.join(tmp, "no_topic.conf")
    open(empty, "w").write("NTFY_TITLE=x\n")
    ok2 = dma.send_ntfy("t", "b", empty)
    ok3 = dma.send_ntfy("t", "b", os.path.join(tmp, "no_such.conf"))
    chk("B26 the ntfy fallback itself: NTFY_URL read from a conf in the freshness conf's shape, ONE POST with the title and the words "
        "(caught by this walk's own listener on 127.0.0.1); no topic in the conf, or no conf: nothing sent; the address is in no line",
        ok1 == (True, "the ntfy topic took it") and posts == [("/made-up-topic", "Docterz export missing at 9:45 pm (Thu 12 Nov)", "warning",
                                                                "made-up words")] and ok2[0] is False and ok3[0] is False and
        "127.0.0.1" not in (ok1[1] + ok2[1] + ok3[1]), (ok1, ok2, ok3, posts))

    r_, p, st = go("evening", THU, EVE, mkdb([CONS], S), dry=True)
    chk("B27 --dry: says what it WOULD send, sends nothing, writes no state and no lock",
        not p.log and r_["line"].startswith("DRY 2026-11-12 21:45 evening, report day 2026-11-12:") and "WOULD SEND to manoj" in r_["line"] and
        not os.path.exists(st) and not os.path.exists(st + ".lock"), (r_, p.log))
    r_, p, _ = go("evening", THU, EVE, mkdb(no_table=True))
    r2, p2, _ = go("evening", THU, EVE, os.path.join(tmp, "no_such.db"))
    chk("B28 no docterz_export table, or no finance.db: one line, nothing sent, no crash",
        not p.log and not p2.log and "could not be read" in r_["line"] and "could not be read" in r2["line"], (r_, r2))
    stbad = os.path.join(tmp, "bad_state.json")
    open(stbad, "w").write("{not json")
    r_, p, _ = go("evening", THU, EVE, mkdb([CONS], S), state=stbad)
    chk("B29 a state file that cannot be read is set aside and said; the notification still goes once",
        len(p.log) == 1 and "set aside" in r_["line"] and os.path.exists(stbad + ".unreadable") and
        list(json.load(open(stbad))["told"]) == ["2026-11-12|evening"], (r_, p.log))
    r_, p, _ = go("evening", THU, EVE, mkdb([CONS], S), state=os.path.join(tmp, "nodir", "state.json"))
    chk("B30 the state cannot be written: nothing is sent (never a second time by accident), said in the line",
        not p.log and p.calls == 0 and r_["why"] == "state", (r_, p.log))

    # ---- fix 7: a run stopped between taking the slot and the push's answer
    class Stop(BaseException):
        pass

    def killed(who, payload):
        raise Stop()
    db = mkdb([CONS], S)
    stk = os.path.join(tmp, "killed_state.json")
    try:
        dma.run("evening", now=dt.datetime.combine(THU, dt.time(*EVE)), db=db, state=stk, pusher=killed, off_dir=os.path.join(tmp, "no_off"))
    except Stop:
        pass
    r_, p, _ = go("evening", THU, (21, 50), db, state=stk)
    odd = []
    for i, content in enumerate(('{"told": {"2026-11-12|evening": "x"}}', '{"told": {"2026-11-12|evening": null}}', '{"told": {"2026-11-12|evening": 7}}')):
        sto = os.path.join(tmp, "odd%d.json" % i)
        open(sto, "w").write(content)
        try:
            ro, po, _ = go("evening", THU, EVE, db, state=sto)
            odd.append((ro["why"], po.calls))
        except Exception as e:                                           # noqa: BLE001
            odd.append(repr(e))
    chk("B31 killed after taking the slot, before the push answered: the next run says 'slot taken ..., outcome not known' -- not "
        "'already told' -- and sends nothing more; an entry that is not this script's shape is read the same way, without a crash",
        p.calls == 0 and r_["why"] == "unknown" and "outcome not known" in r_["line"] and "already told" not in r_["line"] and
        odd == [("unknown", 0)] * 3, (r_, odd))

    # ---- fix 3: two runs at the same instant
    db = mkdb([CONS], S)
    stl = os.path.join(tmp, "locked_state.json")
    fd = os.open(stl + ".lock", os.O_CREAT | os.O_RDWR)
    fcntl.flock(fd, fcntl.LOCK_EX)
    r1, p1, _ = go("evening", THU, EVE, db, state=stl)
    no_state = not os.path.exists(stl)
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)
    r2, p2, _ = go("evening", THU, EVE, db, state=stl)
    chk("B32 another run holds the state's lock: this one says so in one line and sends nothing; when the lock is free it goes, once",
        p1.calls == 0 and r1["why"] == "busy" and "holds the state" in r1["line"] and no_state and len(p2.log) == 1,
        (p1.calls, r1["why"], no_state, p2.log))

    h = lambda p_: __import__("hashlib").md5(open(p_, "rb").read()).hexdigest()      # noqa: E731
    db = mkdb([CONS], S)
    h0 = h(db)
    go("evening", THU, EVE, db)
    chk("B33 finance.db is only read (same md5 after a run that notifies)", h(db) == h0)

    # the pickup pass running at the same minute: the export lands while the alert waits for the pass's lock
    db = mkdb([CONS], S)
    lk = os.path.join(tmp, "pickup.lock")
    fd = os.open(lk, os.O_CREAT | os.O_RDWR)
    fcntl.flock(fd, fcntl.LOCK_EX)

    def land():
        time.sleep(0.6)
        c2 = sqlite3.connect(db)
        add(c2, *FU)
        c2.commit()
        c2.close()
        fcntl.flock(fd, fcntl.LOCK_UN)
    th = threading.Thread(target=land)
    th.start()
    r_, p, _ = go("evening", THU, EVE, db, settle=0.2, lock_path=lk)
    th.join()
    os.close(fd)
    chk("B34 an export landing in the pickup pass of the same minute is waited for: nothing is said", not p.log and r_["why"] == "both", (r_, p.log))

    db = mkdb([CONS], S)
    real_read, fails, naps = dma.read_day, [2], []

    def flaky(db_, day_):
        if fails[0] > 0:
            fails[0] -= 1
            raise sqlite3.OperationalError("database is locked (made up)")
        return real_read(db_, day_)
    dma.read_day = flaky
    try:
        r_, p, _ = go("evening", THU, EVE, db, tries=3, sleep=naps.append)
        fails[0] = 5
        r2, p2, _ = go("evening", THU, EVE, db, tries=3, sleep=naps.append)
    finally:
        dma.read_day = real_read
    chk("B35 a busy finance.db is read again (twice busy, then read: the notification goes); busy three times: one line, nothing sent",
        len(p.log) == 1 and naps[:2] == [5, 5] and not p2.log and r2["why"] == "unreadable", (p.log, naps, r2))

    # ---- through the command line, with a stand-in ring_common beside a made-up portal
    portal = os.path.join(tmp, "portal")
    os.makedirs(portal)
    open(os.path.join(portal, "ring_common.py"), "w").write(STANDIN_RING)
    script_b = os.path.join(kit, B_REL)
    beside = sorted(os.listdir(os.path.dirname(script_b)))
    clean = {k: v for k, v in os.environ.items() if not k.startswith("DMA_")}

    def cli(args, state, db_, **kw):
        e = dict(clean, RING_PORTAL_DIR=portal, FINANCE_DB=db_, FINANCE_OFF_DIR=os.path.join(tmp, "no_off"), DMA_SETTLE="0", DMA_PUSH_WAIT="0",
                 DMA_NTFY_CONF=os.path.join(tmp, "no_such.conf"))
        if state:
            e["DMA_STATE"] = state
        e.update(kw)
        return subprocess.run([sys.executable, "-B", script_b] + args, env=e, capture_output=True, text=True, timeout=120)

    def pushed():
        pp = os.path.join(portal, "pushed.txt")
        return [json.loads(x) for x in open(pp).read().splitlines()] if os.path.exists(pp) else []

    db = mkdb([CONS], S)
    D12 = ["--slot", "evening", "--date", "2026-11-12"]
    # ---- fix 2: a dated run sends nothing and writes nothing
    sd = os.path.join(tmp, "cli_dated.json")
    c1 = cli(D12, sd, db)
    c2 = cli(D12, None, db, DMA_TEST_SEND="1")
    chk("B36 --date WITHOUT --dry sends nothing and writes nothing (it says DRY ... WOULD SEND); so does the walk's own switch when "
        "no state file of the walk's own is named -- nothing is ever written beside the script",
        c1.returncode == 0 and c1.stdout.startswith("DRY 2026-11-12 21:45 evening") and "WOULD SEND" in c1.stdout and not pushed() and
        not os.path.exists(sd) and not os.path.exists(sd + ".lock") and c2.stdout.startswith("DRY ") and not pushed() and
        sorted(os.listdir(os.path.dirname(script_b))) == beside and c1.stderr == "" and c2.stderr == "", (c1.stdout, c2.stdout, pushed()))
    sc = os.path.join(tmp, "cli_state.json")
    c1 = cli(D12, sc, db, DMA_TEST_SEND="1")
    c2 = cli(D12, sc, db, DMA_TEST_SEND="1")
    got = pushed()
    chk("B37 the command line sending (the walk's switch, its own state, the stand-in push): exit 0, ONE line, one push to the owner "
        "through ring_common.push_user; a second call sends nothing",
        c1.returncode == 0 and c2.returncode == 0 and len(c1.stdout.splitlines()) == 1 and "told manoj (push 1 of 3): sent 1, failed 0" in c1.stdout and
        len(c2.stdout.splitlines()) == 1 and "already told" in c2.stdout and len(got) == 1 and got[0][0] == "manoj" and
        got[0][1]["title"] == "Docterz export missing at 9:45 pm (Thu 12 Nov)" and got[0][1]["url"] == "/finance/console" and c1.stderr == "",
        (c1.returncode, c1.stdout, c1.stderr, c2.stdout, got))
    # ---- fix 3, two processes at the same instant (the stand-in push takes 0.4 s, so both are inside the run together)
    open(os.path.join(portal, "sleep"), "w").write("0.4")
    twice, spoke = 0, 0
    for t in range(6):
        b0 = len(pushed())
        sr = os.path.join(tmp, "race%d.json" % t)
        e = dict(clean, RING_PORTAL_DIR=portal, FINANCE_DB=db, FINANCE_OFF_DIR=os.path.join(tmp, "no_off"), DMA_SETTLE="0", DMA_PUSH_WAIT="0",
                 DMA_NTFY_CONF=os.path.join(tmp, "no_such.conf"), DMA_STATE=sr, DMA_TEST_SEND="1")
        ps = [subprocess.Popen([sys.executable, "-B", script_b] + D12, env=e, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        outs = [q.communicate()[0] for q in ps]
        twice += (len(pushed()) - b0) != 1
        spoke += sum(("holds the state" in o) or ("already told" in o) for o in outs) == 1
    os.remove(os.path.join(portal, "sleep"))
    chk("B38 two runs started at the same instant, six times over: exactly ONE push each time; the other run says so and sends nothing",
        twice == 0 and spoke == 6, (twice, spoke))
    # ---- fix 5 through the command line: three tries, then the ntfy topic
    open(os.path.join(portal, "raise"), "w").close()
    c3 = cli(D12, os.path.join(tmp, "cli_state2.json"), db, DMA_TEST_SEND="1")
    n_posts = len(posts)
    c4 = cli(D12, os.path.join(tmp, "cli_state3.json"), db, DMA_TEST_SEND="1", DMA_NTFY_CONF=conf, no_proxy="127.0.0.1,localhost", NO_PROXY="127.0.0.1,localhost")
    os.remove(os.path.join(portal, "raise"))
    l3, l4 = c3.stdout.splitlines(), c4.stdout.splitlines()
    chk("B39 the command line with a push that raises: exit 0, a line for each of the two failed tries and one saying NOT DELIVERED, "
        "nothing on stderr; with the ntfy topic set (the walk's listener): one POST, 'told by ntfy'",
        c3.returncode == 0 and c3.stderr == "" and len(l3) == 3 and "push 1 of 3" in l3[0] and "push 2 of 3" in l3[1] and "NOT DELIVERED" in l3[2] and
        c4.returncode == 0 and c4.stderr == "" and len(l4) == 3 and "told by ntfy instead" in l4[2] and len(posts) == n_posts + 1 and
        posts[-1][1] == "Docterz export missing at 9:45 pm (Thu 12 Nov)" and "127.0.0.1" not in c4.stdout, (c3.stdout, c3.stderr, c4.stdout, c4.stderr))
    c5 = cli(D12 + ["--dry"], os.path.join(tmp, "cli_state4.json"), os.path.join(tmp, "none.db"))
    chk("B40 the command line on a finance.db that is not there: exit 0, one line, nothing sent",
        c5.returncode == 0 and "could not be read" in c5.stdout and c5.stderr == "", (c5.returncode, c5.stdout, c5.stderr))
    # ---- the installer's gate: --probe
    q1 = cli(["--probe", "--date", "2026-11-12"], None, db, DMA_NTFY_CONF=conf).stdout.strip()
    portal2 = os.path.join(tmp, "portal_old")
    os.makedirs(portal2)
    open(os.path.join(portal2, "ring_common.py"), "w").write("def push_user(user, payload):\n    return 1, 0\n")
    q2 = cli(["--probe", "--date", "2026-11-12"], None, mkdb([CONS], (), no_slip=True), RING_PORTAL_DIR=portal2).stdout.strip()
    q3 = cli(["--probe"], None, mkdb(no_table=True)).stdout.strip()
    chk("B41 --probe (the installer's gate): the run's own three reads tried on the store, the owner's devices counted through "
        "ring_common.subs_for, whether an ntfy topic is set -- and nothing sent, no address shown",
        q1 == "PROBE exports=ok slips=ok(2) devices=2 ntfy=yes" and q2 == "PROBE exports=ok slips=ERR(OperationalError) devices=? ntfy=no" and
        q3.startswith("PROBE exports=ERR(OperationalError) slips=ok(0)") and len(pushed()) == 1 + 6 and len(posts) == n_posts + 1, (q1, q2, q3, len(pushed())))
    srv.shutdown()
    srv.server_close()
    return res


def main():
    args = sys.argv[1:]
    if not args:
        print("WALK RED: walk_s811.py <kit dir> [--control | --write-broken <dir>]")
        return 1
    kit = args[0]
    if "--write-broken" in args:
        out = args[args.index("--write-broken") + 1]
        make_broken(kit, out)
        print("broken copies written to %s (A: %s ; B: %s)" % (out, BREAK_A[1], BREAK_B[1].strip()))
        return 0
    control = "--control" in args
    for rel in (A_REL, B_REL):
        if not os.path.isfile(os.path.join(kit, rel)):
            print("WALK RED: %s is not in %s" % (rel, kit))
            return 1
    tmp = tempfile.mkdtemp(prefix="s811walk")
    try:
        target = kit
        if control:
            target = os.path.join(tmp, "broken")
            make_broken(kit, target)
        res = walk(target, os.path.join(tmp, "w"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    bad = [x for x in res if not x[1]]
    if control:
        names = [x[0] for x in bad]
        caught = all(any(nm.startswith(m) for nm in names) for m in MUST_CATCH)
        for nm in names:
            print("red " + nm)
        if bad and caught:
            print("CONTROL: red %d of %d -- the two broken copies were caught (%s)" % (len(bad), len(res), "; ".join(m[:3] for m in MUST_CATCH)))
            return 0
        print("CONTROL: NOT red -- the broken copies passed %d of %d" % (len(res) - len(bad), len(res)))
        return 1
    for name, ok, got in res:
        print(("ok  " if ok else "BAD ") + name + ("" if ok else "  -> %r" % (got,)))
    print("WALK OK %d/%d" % (len(res), len(res)) if not bad else "WALK RED %d of %d" % (len(bad), len(res)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
