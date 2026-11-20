#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pc_upload_watch.py -- kit S897 (the parent, S493, 20-Nov-2026): THE RED LINE (plan S492 FINAL s6.3).

From the switch evening the server writes the call sheet into the receiver's inbox itself (X-FU-Origin: server). Any
upload to /fu-upload WITHOUT that header can only be the clinic PC still sending -- the spare feeding the readers, the one
thing the switch must not allow. S895's receiver marks such an upload in <inbox>/.last_pc_upload (its time and name).

This watcher (cron every 10 minutes, NOT gated by the runner's OFF file -- it must watch before and after the switch) turns
that mark into a freshness leg, in S830's shape (state_json with a fail_field, F-849): a state file with
  last_ok_iso       -- the time of this check, when nothing is wrong
  last_failure_iso  -- the time of this check, when the PC has uploaded AFTER the switch (within the last WINDOW_H hours)
  detail            -- one plain line for the console: not switched yet / all quiet since the switch / RED with the time
and freshness.py shows the leg red ("newest build FAILED") the moment last_failure_iso is newer than last_ok_iso.
The red stands while the stray upload is younger than WINDOW_H hours; it clears by itself after, or at once when the
upload mark is older than the switch (the undo: OFF file back on the box, the PC sending again by design -- then
SWITCHED_AT is removed by the undo and the watcher says 'not switched').

Before the switch (no /root/followup_tracker/SWITCHED_AT): every check is OK, detail 'not switched yet'. Never a name
or a number; the inbox file's name is the day's workbook name only.

    /root/wa/venv/bin/python3 -B pc_upload_watch.py            one check (cron)
    /root/wa/venv/bin/python3 -B pc_upload_watch.py --status   say the state, write nothing
    /root/wa/venv/bin/python3 -B pc_upload_watch.py --selftest made-up folders; touches nothing
"""
import os

os.environ["TZ"] = "Asia/Kolkata"
import time  # noqa: E402

time.tzset()
import argparse   # noqa: E402
import datetime as dt  # noqa: E402
import json       # noqa: E402
import sys        # noqa: E402
import tempfile   # noqa: E402

VERSION = "S897.1"
ROOT = os.environ.get("FUT_ROOT", "/root/followup_tracker")
INBOX = os.environ.get("FU_INBOX_DIR", "/root/wa/followup-inbox")
STATE = os.environ.get("PCW_STATE", os.path.join(ROOT, "pc_upload_watch.state.json"))
WINDOW_H = float(os.environ.get("PCW_WINDOW_H", "26"))


def read_mark(inbox):
    """(epoch, workbook name) of the last upload not the server's, from .last_pc_upload; (None, '') when none."""
    p = os.path.join(inbox, ".last_pc_upload")
    try:
        with open(p, encoding="utf-8") as fh:
            line = fh.readline().strip()
    except OSError:
        return None, ""
    parts = line.split(" ", 2)
    name = parts[-1] if len(parts) >= 3 else ""
    stamp = " ".join(parts[:2]) if len(parts) >= 2 else parts[0]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return time.mktime(dt.datetime.strptime(stamp[:19], fmt).timetuple()), name
        except ValueError:
            continue
    try:
        return os.path.getmtime(p), name
    except OSError:
        return None, ""


def read_switch(root):
    """epoch of the switch: the SWITCHED_AT file's first line (IST), else its mtime; None before the switch"""
    p = os.path.join(root, "SWITCHED_AT")
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            line = fh.readline().strip()
        return time.mktime(dt.datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S").timetuple())
    except (OSError, ValueError):
        return os.path.getmtime(p)


def judge(root=ROOT, inbox=INBOX, now=None, window_h=WINDOW_H):
    """(red, detail) -- the one decision"""
    now = now if now is not None else time.time()
    sw = read_switch(root)
    if sw is None:
        return False, "not switched yet -- the clinic PC still makes the list; nothing to watch"
    mark, name = read_mark(inbox)
    if mark is None or mark <= sw:
        return False, "all quiet since the switch (%s): no upload from the clinic PC" % time.strftime("%d-%b %H:%M", time.localtime(sw))
    age_h = (now - mark) / 3600.0
    when = time.strftime("%d-%b %H:%M", time.localtime(mark))
    if age_h > window_h:
        return False, "the clinic PC uploaded once after the switch (%s, %s) -- older than %d h, no longer counted" % (when, name, int(window_h))
    return True, "RED: the clinic PC uploaded %s at %s -- %.1f h ago, AFTER the switch; it is still sending (put _SPARE_MODE.txt on the PC)" % (name, when, age_h)


def write_state(path, red, detail, now=None):
    now = now if now is not None else time.time()
    st = {}
    try:
        with open(path, encoding="utf-8") as fh:
            st = json.load(fh)
    except (OSError, ValueError):
        st = {}
    iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))
    if red:
        st["last_failure_iso"] = iso
        st.setdefault("last_ok_iso", "")
    else:
        st["last_ok_iso"] = iso
    st["detail"] = detail
    st["checked_iso"] = iso
    st["version"] = VERSION
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".part")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return st


def selftest():
    fails = []

    def check(name, cond):
        if not cond:
            fails.append(name)
            print("FAIL " + name)

    with tempfile.TemporaryDirectory() as td:
        root, inbox = os.path.join(td, "fut"), os.path.join(td, "inbox")
        os.makedirs(root)
        os.makedirs(inbox)
        base = time.mktime(dt.datetime(2026, 11, 25, 21, 0, 0).timetuple())
        red, d = judge(root, inbox, now=base)
        check("before the switch: ok", not red and "not switched" in d)
        with open(os.path.join(root, "SWITCHED_AT"), "w") as fh:
            fh.write("2026-11-25 20:30:00 switched by S?\n")
        red, d = judge(root, inbox, now=base)
        check("switched, no mark: ok", not red and "all quiet" in d)
        with open(os.path.join(inbox, ".last_pc_upload"), "w") as fh:
            fh.write("2026-11-25 20:10:00 Staff_Action_Today_2026-11-26.xlsx\n")
        red, d = judge(root, inbox, now=base)
        check("mark before the switch: ok", not red and "all quiet" in d)
        with open(os.path.join(inbox, ".last_pc_upload"), "w") as fh:
            fh.write("2026-11-25 20:45:00 Staff_Action_Today_2026-11-26.xlsx\n")
        red, d = judge(root, inbox, now=base)
        check("mark after the switch: RED", red and d.startswith("RED") and "Staff_Action_Today_2026-11-26.xlsx" in d)
        red, d = judge(root, inbox, now=base + 30 * 3600)
        check("mark older than the window: ok, said", not red and "no longer counted" in d)
        st_p = os.path.join(td, "st.json")
        st = write_state(st_p, True, "x", now=base)
        check("state: failure written", st.get("last_failure_iso", "").startswith("2026-11-25T21:00") and st.get("last_ok_iso") == "")
        st = write_state(st_p, False, "y", now=base + 600)
        check("state: ok written, failure kept", st["last_ok_iso"] > st["last_failure_iso"])
        check("state: mode 600", oct(os.stat(st_p).st_mode & 0o777) == "0o600")
    print("selftest: %d failure(s)" % len(fails))
    return 0 if not fails else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    red, detail = judge()
    if a.status:
        print(("RED " if red else "ok  ") + detail)
        return 1 if red else 0
    write_state(STATE, red, detail)
    print(("RED " if red else "ok  ") + detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
