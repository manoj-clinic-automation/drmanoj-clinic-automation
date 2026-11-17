#!/root/wa/venv/bin/python3
"""
console_kick.py -- kit S856_CONSOLE_ON_CALL (the parent, session S478, 17-Nov-2026) -- D997 item 2

THE GAP (measured 17-Nov-2026 18:2x IST)
  The Call Console (/portal/console) reads /root/wa/console.db. Its only writer is
  /root/wa/portal_console.py --build, run from cron every 10 minutes (*/10 7-22), which reads the
  Callback Tracker's Google Sheet. The tracker's own calls land in that sheet within a second of
  hang-up (call_hook_capture.py writes its raw log line, then the Call_Durations row). One build takes
  about 1.5 minutes. So the console showed a call 1.5 to 11.5 minutes after the tracker did:
  tracker 63 calls, newest 18:22; console 62, newest 17:56, reading "as of 18:20"; the 18:30 reading
  reached the page at 18:31:4x.

THE CHANGE
  Every minute inside the console's reading window (07:00-22:50, D819), this file looks at two times:
    . the call hook's raw log for today, /root/wa/call-hook/call_hook_logs/YYYY-MM-DD.jsonl -- its
      MODIFIED TIME ONLY (the file is never opened: it carries phone numbers);
    . console.db's meta built_at (the time the last reading took the sheet).
  When the hook has written since the last reading may have taken the sheet (raw time + SLACK_S after
  built_at), and the hook has been quiet SETTLE_S seconds (its sheet row and the call's summary come
  after the raw line), it runs the SAME builder under the SAME lock as the 10-minute run:
      /root/wa/venv/bin/python3 /root/wa/portal_console.py --build --with-myop-reconcile --days 60
  That is the 10-minute run's own command without --with-transcripts: the transcript and recording
  pulls stay on the 10-minute run, and every build merges the transcripts already pulled from the
  cache, so the page loses nothing between them. No second copy of any call is made: console.db stays
  the builder's alone, built from the sheet, exactly as before.

GUARDS
  . the lock is the 10-minute run's own (/root/wa/console_cron.lock, flock): the two never overlap; a
    busy lock means a reading is running now, so this minute does nothing;
  . the minutes :X7, :X8, :X9 and :X0 are left to the 10-minute run: its `flock -n` gives up silently on a
    busy lock, so a kick holding it at :X0 would cost that run (and its transcript pull) -- a call in
    those minutes is read by the 10-minute run within 3 minutes anyway (cold review, S478);
  . at most MAX_PER_HOUR kicks in any hour (the MyOperator reconcile runs in every build); past it the
    10-minute run carries the calls, as before;
  . never within MIN_GAP_S of the last reading;
  . a hook write this file's own last good build already waited for (covered_hook in its state) is not
    built for again -- usually one call costs one extra build (two when its summary comes > 20 s late);
  . a failed kick waits RETRY_S before another (the 10-minute run stays the floor);
  . one build may take at most BUILD_TIMEOUT_S, then it is stopped (the old console.db stays: the
    builder replaces it only at its own end);
  . off: the file /root/wa/console_kick.OFF (any content) -- the minute does nothing.

WRITES ONLY its state (/root/wa/console_kick.state.json) and, through cron, one log line per minute in
which it acts. The build's own output goes to the 10-minute run's log (/root/wa/logs/console_cron.log),
so the freshness page's leg 'call console cron' keeps reading one log.

Modes: (none) = decide and act . --probe = decide and say, never build, never write.
Everything a walk needs is an environment override (CK_*); the box uses the defaults.
Pure standard library. VPS python: /root/wa/venv/bin/python3.
"""

import datetime as _dt
import fcntl
import json
import os
import sqlite3
import subprocess
import sys
import time

VERSION = "S856-CONSOLE-KICK-1"

RAW_DIR = os.environ.get("CK_RAW_DIR", "/root/wa/call-hook/call_hook_logs")
DB = os.environ.get("CK_DB", "/root/wa/console.db")
LOCK = os.environ.get("CK_LOCK", "/root/wa/console_cron.lock")
STATE = os.environ.get("CK_STATE", "/root/wa/console_kick.state.json")
OFF = os.environ.get("CK_OFF", "/root/wa/console_kick.OFF")
BUILD_LOG = os.environ.get("CK_BUILD_LOG", "/root/wa/logs/console_cron.log")
VPY = "/root/wa/venv/bin/python3"
BUILDER = "/root/wa/portal_console.py"
BUILD_CMD = [VPY, BUILDER, "--build", "--with-myop-reconcile", "--days", "60"]
if os.environ.get("CK_BUILD"):
    BUILD_CMD = json.loads(os.environ["CK_BUILD"])

SETTLE_S = int(os.environ.get("CK_SETTLE_S", "20"))
SLACK_S = int(os.environ.get("CK_SLACK_S", "120"))
MAX_PER_HOUR = int(os.environ.get("CK_MAX_PER_HOUR", "6"))
YIELD_MINUTES = (7, 8, 9, 0)  # :X7-:X0 belong to the 10-minute run (its flock -n must find the lock free; a build started at :X7 could outlast :X0)
MIN_GAP_S = int(os.environ.get("CK_MIN_GAP_S", "120"))
RETRY_S = int(os.environ.get("CK_RETRY_S", "600"))
BUILD_TIMEOUT_S = int(os.environ.get("CK_TIMEOUT_S", "540"))
WIN_FROM = (7, 0)            # D819: the reading runs 07:00-22:50
WIN_TO = (22, 50)


def now_local():
    """The box's local time (IST on this server; the builder's built_at is written the same way)."""
    fake = os.environ.get("CK_NOW")
    if fake:
        return _dt.datetime.strptime(fake, "%Y-%m-%d %H:%M:%S")
    return _dt.datetime.now().replace(microsecond=0)


def in_window(now):
    hm = (now.hour, now.minute)
    return WIN_FROM <= hm <= WIN_TO


def raw_mtime(now):
    """The modified time of today's raw hook log, as a local datetime -- os.stat only, never opened."""
    p = os.path.join(RAW_DIR, now.strftime("%Y-%m-%d") + ".jsonl")
    try:
        return _dt.datetime.fromtimestamp(os.stat(p).st_mtime).replace(microsecond=0)
    except OSError:
        return None


def built_at():
    """console.db's meta built_at, read-only; None when the db or the row is not there or unreadable."""
    if not os.path.exists(DB):
        return None
    try:
        con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=5)
        try:
            row = con.execute("SELECT v FROM meta WHERE k='built_at'").fetchone()
        finally:
            con.close()
    except sqlite3.Error:
        return None
    if not row or not row[0]:
        return None
    s = str(row[0]).strip().replace("T", " ")[:19]
    try:
        return _dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def read_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            st = json.load(f)
        return st if isinstance(st, dict) else {}
    except (OSError, ValueError):
        return {}


def write_state(st):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, sort_keys=True)
    os.replace(tmp, STATE)


def parse_iso(s):
    try:
        return _dt.datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def recent_kicks(st, now):
    """The kick times of the last hour kept in the state (for the hourly cap)."""
    out = []
    for s in st.get("kicks_last_hour") or []:
        t = parse_iso(s)
        if t is not None and 0 <= (now - t).total_seconds() < 3600:
            out.append(s)
    return out


def decide(now):
    """(build?, reason, facts) -- pure apart from reading the two times, the state and the switch."""
    facts = {"now": now.strftime("%H:%M:%S")}
    rm = raw_mtime(now)
    ba = built_at()
    facts["hook"] = rm.strftime("%H:%M:%S") if rm else "none today"
    if rm:
        facts["hook_iso"] = rm.strftime("%Y-%m-%d %H:%M:%S")
    facts["reading"] = ba.strftime("%Y-%m-%d %H:%M:%S") if ba else "none"
    if os.path.exists(OFF):
        return False, "off (switch %s)" % OFF, facts
    if not in_window(now):
        return False, "outside the reading window 07:00-22:50", facts
    if now.minute % 10 in YIELD_MINUTES:
        return False, "the 10-minute reading is due now or within 3 minutes -- it is left the lock", facts
    if rm is None:
        return False, "no call logged by the hook today", facts
    st = read_state()
    if len(recent_kicks(st, now)) >= MAX_PER_HOUR:
        return False, "%d kicks in the last hour already -- the 10-minute reading carries the rest" % MAX_PER_HOUR, facts
    last_try = parse_iso(st.get("last_try"))
    if st.get("last_rc") not in (0, None) and last_try and (now - last_try).total_seconds() < RETRY_S:
        return False, "the last kick failed at %s -- waiting %d min" % (last_try.strftime("%H:%M"), RETRY_S // 60), facts
    covered = parse_iso(st.get("covered_hook"))
    if covered is not None and rm <= covered and st.get("last_rc") == 0:
        return False, "the last kick already read this call", facts
    if ba is not None:
        if rm + _dt.timedelta(seconds=SLACK_S) <= ba:
            return False, "the reading is newer than the last call", facts
        if (now - ba).total_seconds() < MIN_GAP_S:
            return False, "the last reading is under %d s old" % MIN_GAP_S, facts
    if (now - rm).total_seconds() < SETTLE_S:
        return False, "a call was logged under %d s ago -- next minute" % SETTLE_S, facts
    return True, "a call logged at %s is not in the reading of %s" % (
        facts["hook"], ba.strftime("%H:%M:%S") if ba else "(none)"), facts


def run_build(now):
    """The builder under the 10-minute run's own lock. Returns (rc, note)."""
    os.makedirs(os.path.dirname(LOCK) or ".", exist_ok=True)
    fd = os.open(LOCK, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return None, "a reading is running now (lock busy)"
        os.makedirs(os.path.dirname(BUILD_LOG) or ".", exist_ok=True)
        with open(BUILD_LOG, "a", encoding="utf-8") as log:
            log.write("\n[S856 kick %s] a call came after the last reading -- the same build, now\n"
                      % now.strftime("%Y-%m-%d %H:%M:%S"))
            log.flush()
            try:
                p = subprocess.run(BUILD_CMD, stdout=log, stderr=subprocess.STDOUT,
                                   timeout=BUILD_TIMEOUT_S, close_fds=True)
                return p.returncode, "rc=%d" % p.returncode
            except subprocess.TimeoutExpired:
                log.write("[S856 kick] the build passed %d s and was stopped\n" % BUILD_TIMEOUT_S)
                return 124, "timeout after %d s" % BUILD_TIMEOUT_S
            except OSError as e:
                log.write("[S856 kick] the build could not start: %s\n" % e.__class__.__name__)
                return 127, "could not start (%s)" % e.__class__.__name__
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def main(argv):
    probe = "--probe" in argv
    now = now_local()
    go, why, facts = decide(now)
    tag = " ".join("%s=%s" % (k, v) for k, v in facts.items())
    if probe:
        print("PROBE %s would_build=%s (%s) %s" % (VERSION, "yes" if go else "no", why, tag))
        return 0
    if not go:
        return 0                      # a quiet minute writes nothing
    t0 = time.time()
    rc, note = run_build(now)
    if rc is None:
        return 0                      # the lock was busy: the running reading will be looked at next minute
    st = read_state()
    st["kicks_last_hour"] = recent_kicks(st, now) + [now.strftime("%Y-%m-%d %H:%M:%S")]
    st["last_try"] = now.strftime("%Y-%m-%d %H:%M:%S")
    st["last_rc"] = rc
    st["version"] = VERSION
    if rc == 0:
        st["last_ok"] = st["last_try"]
        st["covered_hook"] = facts.get("hook_iso", "")
        st["fails_in_a_row"] = 0
    else:
        st["fails_in_a_row"] = int(st.get("fails_in_a_row") or 0) + 1
    write_state(st)
    print("%s kick: %s -> build %s in %ds" % (now.strftime("%Y-%m-%d %H:%M:%S"), why, note, int(time.time() - t0)))
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
