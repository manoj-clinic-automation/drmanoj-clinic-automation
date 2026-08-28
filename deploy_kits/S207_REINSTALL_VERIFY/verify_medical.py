#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_medical.py -- rehearse REINSTALL_MEDICAL.md section 7, READ-ONLY.

S207 / Q2 of the UNATTENDED_QUEUE.  Companion to verify_manojz.py.

WHAT IT DOES
    Reads `D:\\SendToClinic\\heartbeat.txt` -- the file medical_agent.py writes
    every five minutes -- and turns it into the pass/fail table that section 7
    of `deploy_kits/S205_LIVE_TOOLS/REINSTALL_MEDICAL.md` asks for.  It changes
    nothing, sends nothing and starts nothing, so it is safe on the live PC.

WHY THE HEARTBEAT AND NOT THE THINGS THEMSELVES
    The agent has already measured all of it -- the watcher's pid, which folders
    it is watching, whether the agent matches the copy on Drive, how many files
    it cannot take, how old the newest Marg backup is.  Re-measuring it here
    would give a SECOND answer that can disagree with the one the clinic server
    is being told, and then nobody knows which is true.  D349's rule, one layer
    out: one measurement, one place.  This file READS the heartbeat and JUDGES
    it; it does not compete with it.

    The cost is that a STALE heartbeat makes every row below it unknowable --
    which is exactly right, because a stale heartbeat is the fault.  Check 2
    fails first and says so.

THREE OF SECTION 7'S SIX CHECKS RUN ON MANOJZ, NOT HERE (checks 4, 5, 6).
    They are printed as CROSS rows so the table matches the document one to one
    and nobody thinks a check was dropped.  Run VERIFY_MANOJZ.bat over there.

USAGE
      VERIFY_MEDICAL.bat                    (the wrapper -- finds python)
      D:\\SendToClinic\\pyportable\\python.exe verify_medical.py
      python verify_medical.py --selftest   prove the parsers offline

STANDARD LIBRARY ONLY.  Runs on the bundled 3.11 embeddable interpreter.
"""

import argparse
import datetime
import io
import os
import re
import sys
import time

VERSION = "S207.2"          # S207.1 -> .2 after the first live run:
                            # the zone label, the future-dated heartbeat,
                            # and IGNORED. Bump this WITH KIT_ID.txt.

SENDTOCLINIC = r"D:\SendToClinic"
HEARTBEAT    = os.path.join(SENDTOCLINIC, "heartbeat.txt")
SPOOL        = os.path.join(SENDTOCLINIC, "_captured")
PYPORTABLE   = os.path.join(SENDTOCLINIC, "pyportable", "python.exe")

# The agent beats every 300 s. Six minutes gives one missed beat before anyone
# is told off; anything older than that and the agent is not running.
BEAT_STALE_MINUTES = 6
# A heartbeat dated slightly ahead is ordinary clock jitter. Dated MINUTES
# ahead means two different clocks, and that is a finding, not a rounding.
FUTURE_TOLERANCE_MINUTES = 2
BACKUP_WARN_DAYS = 3.0        # must match medical_agent.py's own threshold

# Section 5 of the document: all three, and C:\Users\Public\MARG is the one
# that was added last and is the one most likely to be missing after a rebuild.
WANT_WATCHING = [r"D:\MARGERP\users", r"D:\MARG REPORTS", r"C:\Users\Public\MARG"]

PASS, FAIL, WARN, MANUAL, CROSS = "PASS", "FAIL", "WARN", "MANUAL", "CROSS"


# ---------------------------------------------------------------- parsers
def parse_heartbeat(text):
    """Turn heartbeat.txt into facts. A pure function -- see the selftest.

    Every field defaults to None, never to a benign value. A heartbeat that
    does not say something must read as 'unknown' and not as 'fine': the whole
    medical-PC story is a machine that looked healthy from every angle except
    the one nobody had.
    """
    out = {"written_at": None, "agent_version": None, "computer": None,
           "watcher_alive": None, "watcher_pid": None, "watching": [],
           "agent_uptodate": None, "agent_note": "",
           "ignored": None, "captures_today": None, "newest_capture": None,
           "backup_days": None, "backup_absent": False, "disk_free_gb": None}
    t = text or ""

    m = re.search(r"MEDICAL PC HEARTBEAT\s+(\S+)", t)
    if m:
        out["written_at"] = m.group(1)
    m = re.search(r"^agent\s+(\S+)\s+on\s+(\S+)", t, re.M)
    if m:
        out["agent_version"], out["computer"] = m.group(1), m.group(2)

    m = re.search(r"^WATCHER\s*:\s*(.+)$", t, re.M)
    if m:
        w = m.group(1)
        out["watcher_alive"] = w.strip().upper().startswith("ALIVE")
        p = re.search(r"pid\s+(\d+)", w)
        if p:
            out["watcher_pid"] = int(p.group(1))
    m = re.search(r"^\s*watching:\s*(.+)$", t, re.M)
    if m:
        out["watching"] = [s.strip() for s in m.group(1).split(" + ") if s.strip()]

    if "THIS AGENT IS OUT OF DATE" in t:
        out["agent_uptodate"] = False
        out["agent_note"] = "out of date -- run INSTALL_AGENT.bat on that PC"
    else:
        m = re.search(r"^AGENT\s*:\s*(.+)$", t, re.M)
        if m:
            line = m.group(1).strip()
            if line.lower().startswith("up to date"):
                out["agent_uptodate"] = True
            else:
                out["agent_uptodate"] = None
                out["agent_note"] = line

    m = re.search(r"^IGNORED\s*:\s*(\d+)", t, re.M)
    if m:
        out["ignored"] = int(m.group(1))
    m = re.search(r"^CAPTURES\s*:\s*(\d+)\s+today;\s*newest\s+(\S+)", t, re.M)
    if m:
        out["captures_today"] = int(m.group(1))
        out["newest_capture"] = None if m.group(2) == "-" else m.group(2)

    if re.search(r"NO BACKUP FILE ON", t):
        out["backup_absent"] = True
    m = re.search(r"newest backup on the stick is\s+([0-9.]+)\s+day", t)
    if m:
        out["backup_days"] = float(m.group(1))

    m = re.search(r"^DISK\s*:\s*([0-9.]+)\s*GB", t, re.M)
    if m:
        out["disk_free_gb"] = float(m.group(1))
    return out


def beat_age_minutes(written_at, now=None):
    """Minutes since the heartbeat said it was written. None if unparseable.

    Uses the timestamp INSIDE the file, not mtime: on the medical PC the file
    is also mirrored to Drive, and a sync touching mtime would make a dead
    agent look alive. The agent writes an ISO timestamp on purpose.
    """
    if not written_at:
        return None
    try:
        then = datetime.datetime.fromisoformat(written_at)
    except (ValueError, TypeError):
        return None
    now = now or datetime.datetime.now()
    return (now - then).total_seconds() / 60.0


def missing_watch_dirs(watching, want=None):
    """Which of the three folders the heartbeat does NOT name.

    Compared case-insensitively and with trailing slashes ignored: Windows does
    not care and neither should a check that would otherwise fail on cosmetics.
    """
    want = want or WANT_WATCHING
    have = set(w.rstrip("\\/").lower() for w in (watching or []))
    return [w for w in want if w.rstrip("\\/").lower() not in have]


def newest_in(path):
    """(name, age_minutes) of the newest file in a folder, or (None, None)."""
    newest, newest_m = None, None
    try:
        for f in os.listdir(path):
            p = os.path.join(path, f)
            if not os.path.isfile(p):
                continue
            m = os.path.getmtime(p)
            if newest_m is None or m > newest_m:
                newest, newest_m = f, m
    except OSError:
        return None, None
    if newest is None:
        return None, None
    age = (datetime.datetime.now()
           - datetime.datetime.fromtimestamp(newest_m)).total_seconds() / 60.0
    return newest, age


def stamp(now=None):
    """The local time, labelled with the machine's ACTUAL zone.

    It used to hard-code "IST". That is right on manojz and on the medical PC,
    and WRONG anywhere else -- the first live run of this file printed
    "27-Aug 23:59 IST" on a box running UTC, which is exactly the mistake the
    working protocol exists to prevent. If the label is not IST, the machine is
    not the one this was written for, and that is worth seeing.
    """
    now = now or datetime.datetime.now()
    try:
        zone = time.strftime("%Z") or "local"
    except Exception:                                          # noqa: BLE001
        zone = "local"
    return "%s %s" % (now.strftime("%d-%b-%Y %H:%M:%S"), zone)


def read_text(path, limit=400000):
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return None


class Table(object):
    def __init__(self):
        self.rows = []

    def add(self, num, name, verdict, detail):
        self.rows.append((num, name, verdict, detail))

    def render(self):
        L = ["", "  #  CHECK                          RESULT   DETAIL",
             "  -- ------------------------------ -------- " + "-" * 44]
        for num, name, verdict, detail in self.rows:
            first = True
            for chunk in (detail or "").split("\n"):
                if first:
                    L.append("  %-2s %-30s %-8s %s" % (num, name[:30], verdict, chunk))
                    first = False
                else:
                    L.append("  %-2s %-30s %-8s %s" % ("", "", "", chunk))
        return "\n".join(L)

    def counts(self):
        c = {}
        for _n, _k, v, _d in self.rows:
            c[v] = c.get(v, 0) + 1
        return c


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Read-only rehearsal of REINSTALL_MEDICAL.md section 7")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=SENDTOCLINIC)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    root  = a.root
    beat  = os.path.join(root, "heartbeat.txt")
    spool = os.path.join(root, "_captured")

    t = Table()
    print("=" * 78)
    print("  VERIFY_MEDICAL  %s  read-only rehearsal of REINSTALL_MEDICAL.md 7" % VERSION)
    print("  %s" % stamp())
    print("  It changes NOTHING. Safe on the live machine, any day.")
    print("=" * 78)

    # ---- 1 -- the bundled interpreter
    py = sys.executable or "?"
    ver = sys.version.split()[0]
    if ver.startswith("3.11"):
        t.add("1", "pyportable python 3.11", PASS, "%s\n%s" % (ver, py))
    else:
        t.add("1", "pyportable python 3.11", WARN,
              "%s\n%s\nthe document expects 3.11.x from" % (ver, py) +
              "\n%s" % PYPORTABLE)

    # ---- 2 -- the heartbeat, which carries most of section 7 check 2
    txt = read_text(beat)
    hb = parse_heartbeat(txt) if txt is not None else None
    if hb is None:
        t.add("2", "Heartbeat fresh and healthy", FAIL,
              "no %s" % beat +
              "\nthe agent has never run here, or D:\\SendToClinic is not" +
              "\nwhere it is expected. Section 5: nothing on this machine" +
              "\nruns until somebody logs in.")
    else:
        age = beat_age_minutes(hb["written_at"])
        prob, warn, good = [], [], []
        if age is None:
            prob.append("cannot read the heartbeat's own timestamp")
        elif age < -FUTURE_TOLERANCE_MINUTES:
            # Caught on the first live run: reading the manojz MIRROR from a
            # box running UTC made an IST heartbeat look 325 minutes in the
            # FUTURE, and a negative age sailed through the "is it recent"
            # test as healthy. A clock that disagrees is not a clock that
            # agrees, and it must never read green.
            prob.append("DATED IN THE FUTURE by %d min. Either the two clocks "
                        "disagree,\n  or this is being run somewhere other than "
                        "the medical PC --\n  the manojz mirror is a COPY and lags "
                        "the pull by up to 10 min." % int(-age))
        elif age > BEAT_STALE_MINUTES:
            prob.append("STALE: written %d min ago (agent beats every 5)" % int(age))
        else:
            good.append("written %d min ago" % int(age))

        if hb["watcher_alive"] is True:
            good.append("WATCHER ALIVE, pid %s" % hb["watcher_pid"])
        elif hb["watcher_alive"] is False:
            prob.append("WATCHER DOWN")
        else:
            prob.append("no WATCHER line")

        miss = missing_watch_dirs(hb["watching"])
        if hb["watching"] and not miss:
            good.append("watching all 3 folders")
        elif miss:
            prob.append("NOT watching: %s" % ", ".join(miss))
        else:
            prob.append("no watching: line")

        if hb["agent_uptodate"] is True:
            good.append("AGENT up to date")
        elif hb["agent_uptodate"] is False:
            prob.append("AGENT out of date")
        else:
            prob.append("AGENT self-check skipped: %s" % (hb["agent_note"] or "?"))

        # IGNORED is a WARN, never a FAIL, and the reason is measured.
        # REINSTALL_MEDICAL.md section 7 check 2 asks for "IGNORED : 0". The
        # LIVE machine reported 33 on 28-Aug-2026, and every one of them was a
        # Marg auto-export -- sanjeevni_medicos_<date>_s_a00NNNN.csv and
        # _r_cnNNNNN.csv, written per bill into a watched folder by Marg
        # itself. They arrive every day the pharmacy sells anything, so the
        # count is never zero and the documented expectation can never be met.
        # A check that always fails gets waved through, and then it is not a
        # check (D316). So: report the number, WARN, and say what it means.
        if hb["ignored"] == 0:
            good.append("IGNORED 0")
        elif hb["ignored"] is None:
            prob.append("no IGNORED line")
        else:
            warn.append("IGNORED %d -- the document asks for 0, and 0 has not "
                        "been\n  achievable: Marg auto-writes per-bill .csv into a "
                        "watched\n  folder. Look at the NAMES in the heartbeat. All "
                        "sanjeevni_medicos_*\n  = expected noise. Anything else = a "
                        "report the watcher could not take."
                        % hb["ignored"])

        detail = "\n".join(["+ " + g for g in good]
                           + ["~ " + w for w in warn]
                           + ["! " + x for x in prob])
        t.add("2", "Heartbeat fresh and healthy",
              FAIL if prob else (WARN if warn else PASS),
              detail or "nothing readable")

    # ---- 3 -- the capture spool. A human must export a report to prove it.
    name, age = newest_in(spool)
    if name is None:
        t.add("3", "Capture spool has content", FAIL,
              "%s is empty or missing" % spool +
              "\nnothing has ever been captured on this machine")
    else:
        note = ("newest capture %s min ago" % int(age)) if age is not None else "?"
        t.add("3", "Capture spool has content", PASS if age is not None else WARN,
              "%d-char name, %s" % (len(name), note) +
              "\nFULL check needs a human: export any report in Marg and" +
              "\nwatch a new file appear here within seconds.")

    # ---- 4, 5, 6 -- the other machine
    t.add("4", "Share readable from manojz", CROSS,
          "run VERIFY_MANOJZ.bat on manojz -- its check 2")
    t.add("5", "The pull brings it through", CROSS,
          "run VERIFY_MANOJZ.bat on manojz -- its check 5" +
          "\n(and export a report first, to prove the whole leg)")
    t.add("6", "MARG_PICTURE reads yes / yes", CROSS,
          "run VERIFY_MANOJZ.bat on manojz -- its check 6")

    # ---- 7 -- the one that is not a command
    t.add("7", "Health page: watcher alive", MANUAL,
          "confirm the clinic health page shows" +
          "\n'Medical PC capture - watcher alive'." +
          "\nUntil that is true the rebuild is NOT finished.")

    # ---- extra, not in section 7, but measured and too important to drop
    if hb:
        if hb["backup_absent"]:
            t.add("E1", "Marg backup on the stick", FAIL,
                  "NO BACKUP FILE ON E:\\ -- the stick is empty or absent." +
                  "\nEverything the pharmacy has done exists in one place.")
        elif hb["backup_days"] is None:
            t.add("E1", "Marg backup on the stick", WARN,
                  "the heartbeat does not say (agent may have just started)")
        elif hb["backup_days"] > BACKUP_WARN_DAYS:
            t.add("E1", "Marg backup on the stick", WARN,
                  "newest is %.1f days old (threshold %.0f). Take one in Marg."
                  % (hb["backup_days"], BACKUP_WARN_DAYS))
        else:
            t.add("E1", "Marg backup on the stick", PASS,
                  "newest is %.1f day(s) old" % hb["backup_days"])

    print(t.render())
    c = t.counts()
    print("")
    print("  PASS %d   FAIL %d   WARN %d   MANUAL %d   CROSS %d"
          % (c.get(PASS, 0), c.get(FAIL, 0), c.get(WARN, 0),
             c.get(MANUAL, 0), c.get(CROSS, 0)))
    print("")
    print("  E1 is NOT one of section 7's six. It is added because the agent")
    print("  already measures it and F-201 was a backup nobody had scheduled.")
    if c.get(FAIL):
        print("  RESULT: FAIL -- %d check(s) did not pass." % c[FAIL])
        return 1
    if c.get(WARN):
        print("  RESULT: PASS WITH WARNINGS -- read the WARN row(s) above.")
    else:
        print("  RESULT: PASS -- every check readable on THIS machine is green.")
    print("  CROSS and MANUAL rows are not counted and are not done.")
    return 0


# ---------------------------------------------------------------- selftest
BEAT_GOOD = """MEDICAL PC HEARTBEAT   2026-08-27T09:15:00
agent S203.4 on MEDICAL (python 3.11.9)
AGENT   : up to date (matches the copy on Drive)

WATCHER : ALIVE, pid 8124
          watching: D:\\MARGERP\\users + D:\\MARG REPORTS + C:\\Users\\Public\\MARG
CAPTURES: 7 today; newest a1b2c3.xls at 2026-08-27T09:14:03
IGNORED : 0 file(s) in the watched folders the watcher cannot take
SLOTS   :
BACKUP  : newest backup on the stick is 1.2 day(s) old  (MARG_C18_260826.mbk)
DISK    : 143.7 GB free on D:
"""

BEAT_BAD = """MEDICAL PC HEARTBEAT   2026-08-27T02:15:00
agent S203.4 on MEDICAL (python 3.11.9)

*** THIS AGENT IS OUT OF DATE ***
    running  S203.3   (md5 aaaaaaaa)
    on Drive S203.4   (md5 bbbbbbbb)

WATCHER : DOWN  (restarted 4 time(s) since the agent started)
          watching: D:\\MARGERP\\users + D:\\MARG REPORTS
IGNORED : 3 file(s) in the watched folders the watcher cannot take
BACKUP  : NO BACKUP FILE ON E:\\ -- the stick is empty or absent
DISK    : 9.1 GB free on D:
"""


def selftest():
    n = [0]

    def ck(cond, msg):
        n[0] += 1
        if not cond:
            print("check %d FAILED: %s" % (n[0], msg))
            raise AssertionError(msg)

    g = parse_heartbeat(BEAT_GOOD)
    ck(g["written_at"] == "2026-08-27T09:15:00", "written_at is read")
    ck(g["agent_version"] == "S203.4", "the agent version is read")
    ck(g["computer"] == "MEDICAL", "the computer name is read")
    ck(g["watcher_alive"] is True, "ALIVE reads as alive")
    ck(g["watcher_pid"] == 8124, "the pid is read")
    ck(len(g["watching"]) == 3, "all three watched folders are read")
    ck(g["agent_uptodate"] is True, "'up to date' reads as up to date")
    ck(g["ignored"] == 0, "IGNORED 0 is read as 0")
    ck(g["captures_today"] == 7, "the capture count is read")
    ck(g["newest_capture"] == "a1b2c3.xls", "the newest capture is named")
    ck(abs(g["backup_days"] - 1.2) < 1e-9, "the backup age is read")
    ck(g["backup_absent"] is False, "a present backup is not absent")
    ck(abs(g["disk_free_gb"] - 143.7) < 1e-9, "free disk is read")

    b = parse_heartbeat(BEAT_BAD)
    ck(b["watcher_alive"] is False, "DOWN reads as down")
    ck(b["agent_uptodate"] is False,
       "the OUT OF DATE banner beats the AGENT line -- it is printed INSTEAD")
    ck(b["ignored"] == 3, "a non-zero IGNORED is read")
    ck(parse_heartbeat("IGNORED : 33 file(s) in the watched folders\n")["ignored"] == 33,
       "the live count (33 on 28-Aug) is read as a number, not a flag")
    ck(b["backup_absent"] is True, "an absent stick backup is flagged")
    ck(b["backup_days"] is None, "and carries no age")
    ck(len(b["watching"]) == 2, "only two folders are named")

    e = parse_heartbeat("")
    for k in ("written_at", "watcher_alive", "agent_uptodate", "ignored",
              "backup_days"):
        ck(e[k] is None, "an empty heartbeat leaves %s unknown, not benign" % k)
    ck(e["watching"] == [], "and names no folders")
    sk = parse_heartbeat("AGENT   : self-check skipped -- ToMedical folder not found\n")
    ck(sk["agent_uptodate"] is None and "skipped" in sk["agent_note"],
       "a SKIPPED self-check is unknown, NOT up to date")

    ck(missing_watch_dirs(WANT_WATCHING) == [], "all three present, none missing")
    ck(missing_watch_dirs(b["watching"]) == [r"C:\Users\Public\MARG"],
       "the missing third folder is named")
    ck(missing_watch_dirs([w.lower() for w in WANT_WATCHING]) == [],
       "the comparison is case-insensitive -- Windows does not care")
    ck(missing_watch_dirs([w + "\\" for w in WANT_WATCHING]) == [],
       "a trailing slash is not a difference")
    ck(len(missing_watch_dirs([])) == 3, "an empty list is missing all three")

    now = datetime.datetime(2026, 8, 27, 9, 20, 0)
    ck(int(beat_age_minutes("2026-08-27T09:15:00", now)) == 5, "5 minutes old")
    ck(int(beat_age_minutes("2026-08-27T02:15:00", now)) == 425, "425 minutes old")
    ck(beat_age_minutes(None) is None, "no timestamp, no age")
    ck(beat_age_minutes("not a date") is None, "a bad timestamp does not crash")
    ck(int(beat_age_minutes("2026-08-27T14:45:00", now)) == -325,
       "a heartbeat dated in the FUTURE gives a NEGATIVE age, not a small one "
       "-- this is the live-run bug: -325 was passing the 'recent' test")
    ck(beat_age_minutes("2026-08-27T09:19:00", now) < FUTURE_TOLERANCE_MINUTES,
       "a minute of ordinary jitter stays inside tolerance")

    ck(newest_in(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "_no_such_dir_")) == (None, None),
       "a missing spool is empty, not a crash")

    tb = Table()
    tb.add("1", "x", PASS, "a")
    tb.add("2", "y", FAIL, "b\nc")
    ck(tb.counts()[FAIL] == 1, "the table counts a FAIL")
    ck("c" in tb.render(), "a multi-line detail is rendered")

    print("VERIFY_MEDICAL SELFTEST PASSED - %d checks OK" % n[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
