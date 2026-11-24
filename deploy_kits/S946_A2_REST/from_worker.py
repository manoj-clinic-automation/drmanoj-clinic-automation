#!/usr/bin/env python3
"""
call_pipeline_worker.py -- the D200 at-hangup pipeline. Session 140.
Dr. Manoj Agarwal Clinic, Bareilly.

WHAT THIS DOES
  call_hook_capture.py v3.1 drops a tiny ".kick" file into QUEUE_DIR every
  time a call ends. This worker (a systemd service, call-pipeline.service)
  polls that directory every POLL_SECONDS. When due kicks exist it consumes
  ALL of them at once (coalescing -- ten hangups in a burst cost one run)
  and executes the three EXISTING stage scripts, unchanged, in order:

      1. call_recording_archive.py --date <today IST>   (pulls from the
         MyOperator /search API directly -- NOT the nightly Call_Feed --
         so an intraday run sees today's calls)
      2. call_transcription.py     --date <today IST>
      3. call_verdict.py           --date <today IST>

  All three are idempotent and skip work already done, so re-running them
  costs only the scan. After any run triggered by a FRESH kick, the worker
  schedules exactly ONE follow-up kick +RETRY_DELAY_SECONDS later
  (retry_*.kick): that is the D200 fetch-with-backoff -- a recording not
  yet downloadable at MyOperator when the first run fires is caught by the
  retry, and anything the retry misses is caught by the nightly sweeps
  (02:00 archive, 03:00 transcription, 03:40 verdict), which stay armed
  as the guaranteed floor. Retry kicks never spawn further retries.

WHAT THIS DELIBERATELY DOES NOT DO
  - No changes to the three stage scripts. This file is a kicker, not a
    re-implementation. One writer per table is preserved because the
    writers ARE the stage scripts.
  - No runs inside the QUIET window (01:55-04:05 IST): the nightly batch
    crons own that slot, and two concurrent copies of a stage could race.
    Kicks arriving in the window simply wait; the batches will have done
    the work by the time the window ends, so the queued run is a cheap
    no-op scan.
  - No notifications. The tracker is the surface (owner decision, S140).

CONCURRENCY
  A non-blocking flock on LOCK_PATH guards the pipeline run. If the lock
  is busy (e.g. a manual stage run), kicks are left in place and retried
  on the next poll. Kicks are consumed only AFTER the lock is held.

FAILURE POSTURE
  A stage that exits non-zero stops the chain (later stages depend on the
  earlier ones); the retry kick and the nightly sweeps recover. Every run
  and every stage result is logged with a timestamp to stdout; systemd's
  journal keeps it (journalctl -u call-pipeline).

OPERATIONS
  Selftest (offline, no network, no sheets):
      /root/wa/venv/bin/python3 call_pipeline_worker.py --selftest
  One poll cycle then exit (manual test):
      /root/wa/venv/bin/python3 call_pipeline_worker.py --once
  Service:
      systemctl status call-pipeline
      journalctl -u call-pipeline -n 30 --no-pager
"""

import datetime
import fcntl
import glob
import json
import os
import subprocess
import sys
import time

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

RA_DIR = os.environ.get("PIPELINE_RA_DIR", "").strip() \
    or "/root/wa/recordings-archive"
VENV_PY = os.environ.get("PIPELINE_PYTHON", "").strip() \
    or "/root/wa/venv/bin/python3"
QUEUE_DIR = os.environ.get("CALLHOOK_QUEUE_DIR", "").strip() \
    or os.path.join(RA_DIR, "pipeline_queue")
LOCK_PATH = os.path.join(RA_DIR, "pipeline.lock")

STAGES = [
    ("archive", "call_recording_archive.py"),
    ("transcribe", "call_transcription.py"),
    ("verdict", "call_verdict.py"),
]

POLL_SECONDS = 15
RETRY_DELAY_SECONDS = 600          # the +10 min backoff run (D200)
STAGE_TIMEOUT_SECONDS = 1800
RETRY_PREFIX = "retry_"
QUIET_START = (1, 55)              # 01:55 IST inclusive
QUIET_END = (4, 5)                 # 04:05 IST exclusive


def log(*a):
    print("[pipeline %s]" % datetime.datetime.now(IST).strftime("%d-%b %H:%M:%S"),
          *a, flush=True)


def today_ist():
    return datetime.datetime.now(IST).strftime("%Y-%m-%d")


def in_quiet_window(now=None):
    """True inside [01:55, 04:05) IST -- the nightly batch slot."""
    now = now or datetime.datetime.now(IST)
    t = (now.hour, now.minute)
    return QUIET_START <= t < QUIET_END


def kick_due(path, now_ts=None):
    """A kick is due when its embedded 'due' epoch has passed (0 = now).
    An unreadable kick counts as due: better one spare run than a stuck file."""
    now_ts = now_ts if now_ts is not None else time.time()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return float(json.load(f).get("due", 0) or 0) <= now_ts
    except Exception:                   # noqa: BLE001
        return True


def due_kicks(now_ts=None):
    return sorted(p for p in glob.glob(os.path.join(QUEUE_DIR, "*.kick"))
                  if kick_due(p, now_ts))


def consume(paths):
    n = 0
    for p in paths:
        try:
            os.unlink(p)
            n += 1
        except FileNotFoundError:
            pass
        except Exception as e:          # noqa: BLE001
            log("could not remove kick", os.path.basename(p), e)
    return n


def retry_pending():
    return bool(glob.glob(os.path.join(QUEUE_DIR, RETRY_PREFIX + "*.kick")))


def schedule_retry(delay=RETRY_DELAY_SECONDS):
    """Exactly one retry kick outstanding at any time."""
    if retry_pending():
        return False
    try:
        os.makedirs(QUEUE_DIR, exist_ok=True)
        name = os.path.join(
            QUEUE_DIR, "%s%s_%s.kick"
            % (RETRY_PREFIX,
               datetime.datetime.now(IST).strftime("%Y%m%d%H%M%S%f"),
               os.urandom(3).hex()))
        with open(name, "w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "event": "retry",
                       "due": time.time() + delay}, f)
        return True
    except Exception as e:              # noqa: BLE001
        log("schedule_retry failed (nightly sweep covers):", e)
        return False


def run_stage(name, script, date):
    path = os.path.join(RA_DIR, script)
    try:
        r = subprocess.run(
            [VENV_PY, path, "--date", date],
            cwd=RA_DIR, capture_output=True, text=True,
            timeout=STAGE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        log("stage", name, "TIMEOUT after", STAGE_TIMEOUT_SECONDS, "s")
        return False
    except Exception as e:              # noqa: BLE001
        log("stage", name, "could not start:", e)
        return False
    tail = (r.stdout or "").strip().splitlines()[-2:]
    for line in tail:
        log("  %s| %s" % (name, line))
    if r.returncode != 0:
        err = (r.stderr or "").strip().splitlines()[-2:]
        for line in err:
            log("  %s! %s" % (name, line))
        log("stage", name, "exited", r.returncode)
        return False
    return True


def run_pipeline(date):
    for name, script in STAGES:
        if not run_stage(name, script, date):
            log("chain stopped at", name,
                "(retry kick + nightly sweep recover)")
            return False
    return True


def poll_once():
    """One poll cycle. Returns True if a pipeline run happened."""
    kicks = due_kicks()
    if not kicks:
        return False
    if in_quiet_window():
        return False                    # kicks wait; batches own this slot
    lock_f = open(LOCK_PATH, "w")
    try:
        try:
            fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            log("pipeline busy; %d kick(s) wait" % len(kicks))
            return False
        kicks = due_kicks()             # re-read under the lock
        if not kicks:
            return False
        fresh = [k for k in kicks
                 if not os.path.basename(k).startswith(RETRY_PREFIX)]
        n = consume(kicks)
        log("run: %d kick(s) coalesced (%d fresh) date=%s"
            % (n, len(fresh), today_ist()))
        ok = run_pipeline(today_ist())
        log("run %s" % ("complete" if ok else "INCOMPLETE"))
        if fresh and schedule_retry():
            log("backoff run scheduled +%ds" % RETRY_DELAY_SECONDS)
        return True
    finally:
        try:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
        except Exception:               # noqa: BLE001
            pass
        lock_f.close()


def main_loop():
    os.makedirs(QUEUE_DIR, exist_ok=True)
    log("worker up. queue=%s poll=%ds retry=+%ds quiet=%02d:%02d-%02d:%02d IST"
        % (QUEUE_DIR, POLL_SECONDS, RETRY_DELAY_SECONDS,
           QUIET_START[0], QUIET_START[1], QUIET_END[0], QUIET_END[1]))
    while True:
        try:
            poll_once()
        except Exception as e:          # noqa: BLE001
            log("poll error (worker continues):", e)
        time.sleep(POLL_SECONDS)


# ---------------------------------------------------------------------------
def _selftest():
    import tempfile
    global QUEUE_DIR, LOCK_PATH
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("  FAIL:", name)

    # quiet window boundaries
    def at(h, m):
        return datetime.datetime(2026, 7, 12, h, m, tzinfo=IST)
    check("01:54 outside quiet", not in_quiet_window(at(1, 54)))
    check("01:55 inside quiet", in_quiet_window(at(1, 55)))
    check("04:04 inside quiet", in_quiet_window(at(4, 4)))
    check("04:05 outside quiet", not in_quiet_window(at(4, 5)))
    check("14:00 outside quiet", not in_quiet_window(at(14, 0)))

    check("date format", len(today_ist()) == 10 and today_ist()[4] == "-")

    with tempfile.TemporaryDirectory() as td:
        _q, _l = QUEUE_DIR, LOCK_PATH
        QUEUE_DIR = os.path.join(td, "q")
        LOCK_PATH = os.path.join(td, "pipeline.lock")
        os.makedirs(QUEUE_DIR)
        try:
            # kick due semantics
            a = os.path.join(QUEUE_DIR, "1.kick")
            json.dump({"due": 0}, open(a, "w"))
            b = os.path.join(QUEUE_DIR, "2.kick")
            json.dump({"due": time.time() + 9999}, open(b, "w"))
            c = os.path.join(QUEUE_DIR, "3.kick")
            open(c, "w").write("not json")
            due = due_kicks()
            check("due=0 is due", a in due)
            check("future due is not due", b not in due)
            check("unreadable kick counts as due", c in due)

            # coalescing consume
            check("consume removes exactly the due ones", consume(due) == 2
                  and os.path.exists(b))

            # retry dedupe
            check("first retry scheduled", schedule_retry(delay=9999) is True)
            check("second retry refused while one pends",
                  schedule_retry(delay=9999) is False)
            check("retry_pending sees it", retry_pending())
            rk = glob.glob(os.path.join(QUEUE_DIR, RETRY_PREFIX + "*.kick"))
            check("retry kick not yet due", rk and rk[0] not in due_kicks())
        finally:
            QUEUE_DIR, LOCK_PATH = _q, _l

    print("SELFTEST: %d/%d PASS" % (passed, passed + failed))
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if _selftest() else 1)
    if "--once" in sys.argv:
        os.makedirs(QUEUE_DIR, exist_ok=True)
        ran = poll_once()
        log("--once:", "ran" if ran else "nothing due")
        sys.exit(0)
    main_loop()
