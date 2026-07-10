#!/usr/bin/env python3
# watch_and_push_followups.py
# -----------------------------------------------------------------------------
# AUTO-PUSH watcher for the Follow-Up Tracker.
#
# WHAT IT DOES (plain language):
#   It quietly watches the tracker's "outputs" folder. The moment a NEW
#   "Staff_Action_Today_*.xlsx" appears (i.e. the moment you process the
#   tracker), it waits a few seconds for the file to finish saving, then runs
#   the SAME push you ran by hand:
#        python push_followups_today.py --push --file "<that new file>"
#   so today's follow-up calls reach the dashboard automatically. You never
#   type a command again — just process the tracker as usual.
#
# WHY POLLING (not OS file events):
#   The outputs folder is synced to Google Drive. Drive sync fires noisy,
#   duplicated file events, which makes OS event-hooks unreliable. A simple
#   "look every few seconds" loop is rock-solid for a once-a-day file and
#   needs no extra libraries.
#
# SAFETY MODEL (matches the push script's own discipline):
#   - It only ever RUNS the push script; it never writes to the Sheet itself.
#   - It never modifies your local xlsx (the push script reads it read-only).
#   - It remembers which files it already pushed (a tiny .seen file), so a
#     watcher restart or a Drive re-sync of the same file can't double-push.
#   - It MASKS nothing of its own (it prints no patient data); the push script
#     it calls already masks phones in its console output.
#   - Pure Python standard library. No new packages to install.
#
# -----------------------------------------------------------------------------
# FAILURE MAP (per D19 discipline)
# -----------------------------------------------------------------------------
# Depends on:
#   - The push script `push_followups_today.py` sitting in PUSH_DIR with the
#     service-account .json beside it (already proven working manually).
#   - The Python on PATH being able to run that script (already proven).
# Fault behaviours / fallbacks:
#   - Push script missing            -> logs a clear STOP line, keeps watching.
#   - Push run fails (network etc.)  -> logs the failure, does NOT mark the file
#                                       as pushed, so it retries on next poll.
#   - Watcher not running at all      -> fallback is the manual command you
#                                       already know:  python push_followups_today.py --push
#   - Folder missing                 -> logs once, keeps trying (Drive may be
#                                       mid-sync at boot).
# -----------------------------------------------------------------------------
#
# HOW TO RUN:
#   Foreground (to test):   python watch_and_push_followups.py
#   It then runs forever, checking every few seconds. Ctrl+C to stop.
#   (Auto-start-on-login setup is provided separately, after you test it.)
# -----------------------------------------------------------------------------

import os
import sys
import time
import glob
import subprocess
from datetime import datetime

# =============================== CONFIG ======================================
# The tracker folder that holds push_followups_today.py + the .json key.
PUSH_DIR = r"C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker"

# The folder the tracker drops Staff_Action_Today_*.xlsx into.
WATCH_DIR = os.path.join(PUSH_DIR, "outputs")

# The push script (already proven working manually).
PUSH_SCRIPT = os.path.join(PUSH_DIR, "push_followups_today.py")

# The file pattern the tracker writes.
PATTERN = "Staff_Action_Today_*.xlsx"

# How often to look (seconds). 5s is plenty for a once-a-day file.
POLL_SECONDS = 5

# After spotting a new file, wait this long so the tracker finishes writing
# and Drive sync settles, before pushing.
SETTLE_SECONDS = 10

# Small bookkeeping files (next to this watcher).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(BASE_DIR, "watch_pushed.seen")   # files already pushed
LOG_FILE  = os.path.join(BASE_DIR, "watch_followups.log")  # plain run log
# =============================================================================


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    line = "[%s] %s" % (now(), msg)
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_seen():
    """Set of file SIGNATURES already pushed (name + size + mtime)."""
    seen = set()
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                for ln in f:
                    ln = ln.strip()
                    if ln:
                        seen.add(ln)
        except Exception:
            pass
    return seen


def mark_seen(sig):
    try:
        with open(SEEN_FILE, "a", encoding="utf-8") as f:
            f.write(sig + "\n")
    except Exception:
        pass


def signature(path):
    """A signature that changes if the file is genuinely re-generated."""
    try:
        st = os.stat(path)
        return "%s|%d|%d" % (os.path.basename(path), st.st_size, int(st.st_mtime))
    except Exception:
        return os.path.basename(path)


def run_push(filepath):
    """Run the proven push script against this exact file. Return True on success."""
    if not os.path.exists(PUSH_SCRIPT):
        log("STOP: push script not found at %s — cannot push. Will keep watching."
            % PUSH_SCRIPT)
        return False
    cmd = [sys.executable, PUSH_SCRIPT, "--push", "--file", filepath]
    log("Pushing: %s" % os.path.basename(filepath))
    try:
        # Run from PUSH_DIR so the script finds its key beside it.
        result = subprocess.run(
            cmd, cwd=PUSH_DIR, capture_output=True, text=True, timeout=300
        )
    except Exception as e:
        log("Push FAILED to launch: %s" % e)
        return False

    # Surface the push script's own last lines (already phone-masked by it).
    tail = (result.stdout or "").strip().splitlines()[-3:]
    for ln in tail:
        log("   " + ln)
    if result.returncode == 0 and "DONE." in (result.stdout or ""):
        log("Push OK.")
        return True
    log("Push did NOT confirm success (return code %s). Will retry next time."
        % result.returncode)
    if result.stderr:
        log("   stderr: " + result.stderr.strip().splitlines()[-1:][0]
            if result.stderr.strip() else "")
    return False


def newest_matching():
    cands = glob.glob(os.path.join(WATCH_DIR, PATTERN))
    if not cands:
        return None
    return max(cands, key=os.path.getmtime)


def main():
    log("=" * 60)
    log("Follow-up auto-push watcher STARTED.")
    log("Watching: %s" % WATCH_DIR)
    log("Pattern : %s" % PATTERN)
    log("Push     : %s" % PUSH_SCRIPT)
    log("(Fallback if this ever stops: run manually -> "
        "python push_followups_today.py --push)")
    log("=" * 60)

    seen = load_seen()
    warned_missing = False

    while True:
        try:
            if not os.path.isdir(WATCH_DIR):
                if not warned_missing:
                    log("Outputs folder not found yet (Drive may be syncing): %s"
                        % WATCH_DIR)
                    warned_missing = True
                time.sleep(POLL_SECONDS)
                continue
            warned_missing = False

            newest = newest_matching()
            if newest:
                sig = signature(newest)
                if sig not in seen:
                    log("New file detected: %s" % os.path.basename(newest))
                    log("Waiting %ds for the file to settle..." % SETTLE_SECONDS)
                    time.sleep(SETTLE_SECONDS)
                    # Re-check signature in case it's still being written.
                    sig2 = signature(newest)
                    if sig2 != sig:
                        log("File still changing — will re-evaluate next poll.")
                    else:
                        if run_push(newest):
                            mark_seen(sig2)
                            seen.add(sig2)
        except KeyboardInterrupt:
            log("Watcher stopped by user (Ctrl+C). Bye.")
            return
        except Exception as e:
            log("Unexpected error (will keep watching): %s" % e)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
