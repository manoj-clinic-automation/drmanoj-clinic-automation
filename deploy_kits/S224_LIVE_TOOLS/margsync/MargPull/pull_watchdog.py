#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""pull_watchdog.py -- A3, the pull-asleep shout (S224).

The 10-minute Marg pull leaves 'END dd-mm-yyyy h:mm:ss -- ok' in _last_pull.txt.
When that line stops moving, nothing on this PC says so: MARG_PICTURE.txt is
only rewritten BY the pull, so a dead pull leaves a picture that looks fine
for ever. On 26-Aug the feed was dark 8h40m before anyone noticed.

Every 15 minutes (Task Scheduler) this script:
  1. reads the last END time; age > 35 min = ASLEEP
  2. compares against ITS OWN last-run stamp. If the watchdog itself has not
     run for > 35 min the PC was asleep or off -- the pull is not to blame.
     That run only writes the stamp and says "just woke; rechecking".
  3. when asleep: writes _pull_alarm.txt, prepends ONE red line
        PULL ASLEEP since HH:MM IST (N min)
     to MARG_PICTURE.txt (safely: temp file + replace; never twice), and
     calls push_purchases.py --feed so the server tile shows it.
  4. when awake again: removes the alarm line and the alarm file, and
     sends --feed once more so the tile goes green.

THERE IS NO OUTBOUND SHOUT CHANNEL ON MANOJZ. The S217 15:00 shout runs in
Google Apps Script; the WhatsApp due-digest and notifier run on the VPS. No
GAS webhook URL, no wa-send token, nothing on this PC can message the owner
directly -- so nothing is invented here. The /api/feed ping IS the shout:
the server has every channel and a state of 'asleep' is what it acts on.

    python pull_watchdog.py                      the scheduled run
    python pull_watchdog.py --dry-run            no files changed, feed dry-run
    python pull_watchdog.py --pull-file X --picture Y --stamp-file Z --now ISO
                                                 the selftest's temp copies
Exit 0 always unless the arguments are unusable -- a watchdog that exits red
into a scheduler log teaches nobody anything; the state is in the files.
"""
import argparse
import datetime as dt
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARGSYNC = os.path.dirname(HERE)
DEF_PULL_FILE = os.path.join(HERE, "_last_pull.txt")
DEF_PICTURE = os.path.join(MARGSYNC, "MARG_PICTURE.txt")
DEF_STAMP = os.path.join(HERE, "_watchdog_last.txt")
DEF_ALARM = os.path.join(HERE, "_pull_alarm.txt")
DEF_LOGDIR = os.path.join(HERE, "_logs")
DEF_KIT = r"D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S224_MARG_PURCHASES"
MAX_AGE_MIN = 35
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
ALARM_PREFIX = "PULL ASLEEP since "
END_RE = re.compile(r"(\d{2})-(\d{2})-(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})")


def now_ist():
    return dt.datetime.now(IST)


def last_end(path):
    """(aware IST datetime of the last END line, its note) or (None, why)."""
    try:
        with io.open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            lines = [l.strip() for l in fh if l.strip()]
    except OSError:
        return None, "no _last_pull.txt"
    ends = [l for l in lines if l.startswith("END")]
    if not ends:
        return None, "no END line"
    m = END_RE.search(ends[-1])
    if not m:
        return None, "END line without a time"
    d, mo, y, hh, mm, ss = (int(x) for x in m.groups())
    note = ends[-1].split("--", 1)[1].strip() if "--" in ends[-1] else ""
    return dt.datetime(y, mo, d, hh, mm, ss, tzinfo=IST), note


def read_stamp(path):
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            return dt.datetime.fromisoformat(fh.read().strip())
    except Exception:                                          # noqa: BLE001
        return None


def write_stamp(path, when):
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(when.isoformat(timespec="seconds") + "\n")


def alarm_line(since, age_min):
    return "%s%s IST (%d min)" % (ALARM_PREFIX, since.strftime("%H:%M"), age_min)


def set_picture_alarm(picture, line):
    """Prepend ONE alarm line; replace an existing one; temp file + replace."""
    try:
        with io.open(picture, "r", encoding="utf-8", errors="replace", newline="") as fh:
            body = fh.read()
    except OSError:
        body = ""
    nl = "\r\n" if "\r\n" in body else "\n"
    if body.startswith(ALARM_PREFIX):
        body = body.split(nl, 1)[1] if nl in body else ""
    text = line + nl + body
    tmp = picture + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    os.replace(tmp, picture)


def clear_picture_alarm(picture):
    try:
        with io.open(picture, "r", encoding="utf-8", errors="replace", newline="") as fh:
            body = fh.read()
    except OSError:
        return False
    if not body.startswith(ALARM_PREFIX):
        return False
    nl = "\r\n" if "\r\n" in body else "\n"
    rest = body.split(nl, 1)[1] if nl in body else ""
    tmp = picture + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(rest)
    os.replace(tmp, picture)
    return True


def send_feed(kit, pull_file, dry_run):
    """push_purchases.py --feed, with the same python that runs this file."""
    script = os.path.join(kit, "push_purchases.py")
    if not os.path.isfile(script):
        return "feed: kit not found at %s" % kit
    cmd = [sys.executable, "-B", script, "--feed", "--pull-file", pull_file]
    if dry_run:
        cmd.append("--dry-run")
    try:
        r = subprocess.run(cmd, cwd=kit, capture_output=True, text=True, timeout=120)
        out = (r.stdout or "").strip().replace("\n", " | ")
        return "feed rc=%d %s" % (r.returncode, out[:200])
    except Exception as e:                                     # noqa: BLE001
        return "feed: could not run (%s)" % e.__class__.__name__


def log(logdir, text):
    try:
        if not os.path.isdir(logdir):
            os.makedirs(logdir)
        p = os.path.join(logdir, "watchdog_%s.log" % now_ist().strftime("%Y-%m"))
        with io.open(p, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
    except Exception:                                          # noqa: BLE001
        pass


def check(pull_file, stamp_file, now=None, max_age=MAX_AGE_MIN):
    """The decision, with no side effects. Returns a dict."""
    now = now or now_ist()
    when, note = last_end(pull_file)
    own = read_stamp(stamp_file)
    just_woke = own is None or (now - own).total_seconds() > max_age * 60
    if when is None:
        return {"state": "unknown", "why": note, "age_min": None, "since": None,
                "just_woke": just_woke, "now": now}
    age = int((now - when).total_seconds() // 60)
    if age > max_age and not just_woke:
        st = "asleep"
    elif age > max_age:
        st = "woke"          # too old, but so is the watchdog: the PC slept
    else:
        st = "ok"
    return {"state": st, "why": note, "age_min": age, "since": when,
            "just_woke": just_woke, "now": now}


def main(argv=None):
    ap = argparse.ArgumentParser(description="shout when the Marg pull stops")
    ap.add_argument("--pull-file", default=DEF_PULL_FILE)
    ap.add_argument("--picture", default=DEF_PICTURE)
    ap.add_argument("--stamp-file", default=DEF_STAMP)
    ap.add_argument("--alarm-file", default=DEF_ALARM)
    ap.add_argument("--logdir", default=DEF_LOGDIR)
    ap.add_argument("--kit", default=DEF_KIT)
    ap.add_argument("--max-age", type=int, default=MAX_AGE_MIN)
    ap.add_argument("--now", default=None, help="ISO time with offset, for tests")
    ap.add_argument("--no-feed", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    now = dt.datetime.fromisoformat(a.now) if a.now else now_ist()

    c = check(a.pull_file, a.stamp_file, now, a.max_age)
    msg = "%s state=%s age=%s min last_end=%s%s" % (
        now.strftime("%Y-%m-%d %H:%M"), c["state"], c["age_min"],
        c["since"].strftime("%H:%M") if c["since"] else "-",
        " (watchdog just woke)" if c["just_woke"] else "")
    feed = ""
    if a.dry_run:
        print("dry run: " + msg)
        if c["state"] == "asleep":
            print("would write: " + alarm_line(c["since"], c["age_min"]))
        if not a.no_feed:
            print(send_feed(a.kit, a.pull_file, True))
        return 0

    write_stamp(a.stamp_file, now)
    if c["state"] == "asleep":
        line = alarm_line(c["since"], c["age_min"])
        with io.open(a.alarm_file, "w", encoding="utf-8") as fh:
            fh.write(line + "\n")
        set_picture_alarm(a.picture, line)
        if not a.no_feed:
            feed = send_feed(a.kit, a.pull_file, False)
        msg += " | " + line
    else:
        cleared = clear_picture_alarm(a.picture)
        had_alarm = os.path.isfile(a.alarm_file)
        if had_alarm:
            try:
                os.remove(a.alarm_file)
            except OSError:
                pass
        if (cleared or had_alarm) and not a.no_feed and c["state"] == "ok":
            feed = send_feed(a.kit, a.pull_file, False)
            msg += " | alarm cleared"
    if feed:
        msg += " | " + feed
    print(msg)
    log(a.logdir, msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
