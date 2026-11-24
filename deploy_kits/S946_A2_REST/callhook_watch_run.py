#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
callhook_watch_run.py -- S946 (the parent, S512, 24-Nov-2026) -- roadmap S510 A2 (C5).

WHAT THIS IS
    The daily runner of callhook_watchdog.py (the 403 detector written at S125 and
    scheduled nowhere since). It runs the watchdog once, keeps its JSON report, and
    writes ONE small state file the health page's freshness leg reads:

        last_run_iso       every run
        last_success_iso   the run ended OK or WARN  (the webhook is not being refused)
        last_fail_iso      the run ended CRITICAL or ERROR (refused deliveries, a missing
                           raw log on a clinic day, or the watchdog could not read the log)
        severity, accepted_200, rejected_403, findings (codes only)

    The leg (freshness_legs.json, kind state_json, field last_success_iso,
    fail_field last_fail_iso, 26 h) goes red the morning the webhook is refused,
    and red when the run itself stops happening.

WHAT IT TOUCHES
    Nothing of the receiver. It writes the state file and the watchdog's own
    --state file, both under /root/wa/call-hook/. Keys are never printed: the
    watchdog masks them, and this runner keeps only finding CODES.

USAGE
    /root/wa/venv/bin/python3 callhook_watch_run.py                 # one run
    /root/wa/venv/bin/python3 callhook_watch_run.py --access-glob '/home/*/logs/*access*'
    /root/wa/venv/bin/python3 callhook_watch_run.py --check         # the state in one line
    /root/wa/venv/bin/python3 callhook_watch_run.py --selftest      # offline, a made-up watchdog

ENV (tests only)   WATCH_RUN_WATCHDOG  path of the watchdog script   (--raw-log-dir and --date pass through to it)
                   WATCH_RUN_PYTHON    the interpreter to run it with
                   WATCH_RUN_STATE     the state file this writes
                   WATCH_RUN_WD_STATE  the watchdog's own --state file

Python 3.9 compatible.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

VERSION = "1.0"
BUILD = "S946"
IST = timezone(timedelta(hours=5, minutes=30))

HERE = os.path.dirname(os.path.abspath(__file__))
WATCHDOG = os.environ.get("WATCH_RUN_WATCHDOG", "").strip() or os.path.join(HERE, "callhook_watchdog.py")
PYTHON = os.environ.get("WATCH_RUN_PYTHON", "").strip() or sys.executable
STATE_PATH = os.environ.get("WATCH_RUN_STATE", "").strip() or os.path.join(HERE, "callhook_watchdog.state.json")
WD_STATE_PATH = os.environ.get("WATCH_RUN_WD_STATE", "").strip() or os.path.join(HERE, "watchdog_state.json")
TIMEOUT_S = 120
GOOD = ("OK", "WARN")


def now_iso():
    return datetime.now(IST).replace(microsecond=0).isoformat()


def load_state(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(path, payload):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def run_watchdog(access_globs, date=None, raw_log_dir=None):
    """Run the watchdog once. Returns (exit_code, report_dict_or_None, stderr_tail)."""
    cmd = [PYTHON, "-B", WATCHDOG, "--json", "--state", WD_STATE_PATH]
    for g in access_globs or []:
        cmd += ["--access-glob", g]
    if date:
        cmd += ["--date", date]
    if raw_log_dir:
        cmd += ["--raw-log-dir", raw_log_dir]
    try:
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return 3, None, "watchdog timed out after %d s" % TIMEOUT_S
    except OSError as exc:
        return 3, None, "could not start the watchdog: %s" % exc
    rep = None
    try:
        rep = json.loads(r.stdout or "")
        if not isinstance(rep, dict):
            rep = None
    except ValueError:
        rep = None
    err = "\n".join((r.stderr or "").strip().splitlines()[-2:])
    return r.returncode, rep, err


def judge(code, rep, err):
    """The state record from one run. Severity from the report when it has one,
    else from the exit code (3 = the watchdog itself could not run)."""
    # no JSON = the watchdog did not run to its report (bad glob, missing file, a crash): ERROR, whatever the exit code
    sev = rep.get("severity") if rep else "ERROR"
    if sev not in ("OK", "WARN", "CRITICAL", "ERROR"):
        sev = {0: "OK", 1: "WARN", 2: "CRITICAL"}.get(code, "ERROR")
    rec = {
        "version": VERSION, "build": BUILD,
        "last_run_iso": now_iso(),
        "severity": sev,
        "exit_code": code,
        "accepted_200": (rep or {}).get("accepted_200"),
        "rejected_403": (rep or {}).get("rejected_403"),
        "date": (rep or {}).get("date"),
        "findings": [str(f.get("code", "")) for f in (rep or {}).get("findings", []) if isinstance(f, dict)],
        "error": (err or "")[:200] if sev == "ERROR" else "",
    }
    return rec


def one_run(access_globs, date=None, raw_log_dir=None):
    prev = load_state(STATE_PATH)
    code, rep, err = run_watchdog(access_globs, date, raw_log_dir)
    rec = judge(code, rep, err)
    rec["last_success_iso"] = rec["last_run_iso"] if rec["severity"] in GOOD else prev.get("last_success_iso", "")
    rec["last_fail_iso"] = rec["last_run_iso"] if rec["severity"] not in GOOD else prev.get("last_fail_iso", "")
    save_state(STATE_PATH, rec)
    print("WATCH %s  accepted %s  rejected %s  findings %s%s" % (
        rec["severity"], rec["accepted_200"], rec["rejected_403"],
        ",".join(rec["findings"]) or "none",
        ("  (" + rec["error"] + ")") if rec["error"] else ""))
    return 0 if rec["severity"] in GOOD else (2 if rec["severity"] == "CRITICAL" else 3)


def check():
    st = load_state(STATE_PATH)
    if not st:
        print("WATCH STATE missing (%s)" % STATE_PATH)
        return 1
    print("WATCH STATE %s  last run %s  last good %s  last bad %s  accepted %s  rejected %s" % (
        st.get("severity"), st.get("last_run_iso"), st.get("last_success_iso") or "-",
        st.get("last_fail_iso") or "-", st.get("accepted_200"), st.get("rejected_403")))
    return 0 if st.get("severity") in GOOD else 1


# ---------------------------------------------------------------------------
FAKE_WATCHDOG = r'''
import json, sys
if sys.argv[-1].endswith("=err"):
    sys.stderr.write("error: no access log matched globs: /nowhere/*\n"); sys.exit(3)
sev = {"ok": ("OK", 0), "warn": ("WARN", 1), "crit": ("CRITICAL", 2)}[sys.argv[-1].split("=")[-1]]
print(json.dumps({"severity": sev[0], "exit_code": sev[1], "accepted_200": 12, "rejected_403": 0 if sev[1] < 2 else 7,
                  "date": "2026-11-24", "keys_200": {"key_abc123": 12},
                  "findings": [] if sev[1] == 0 else [{"severity": sev[0], "code": "CALLHOOK_SECRET_MISMATCH_403" if sev[1] == 2 else "CALLHOOK_SILENT", "detail": "x"}]}))
sys.exit(sev[1])
'''


def selftest():
    global WATCHDOG, STATE_PATH, WD_STATE_PATH, PYTHON
    passed = failed = 0

    def check_(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("  FAIL: %s" % name)

    with tempfile.TemporaryDirectory() as td:
        fake = os.path.join(td, "fake_watchdog.py")
        with open(fake, "w", encoding="utf-8") as fh:
            fh.write(FAKE_WATCHDOG)
        WATCHDOG, PYTHON = fake, sys.executable
        STATE_PATH = os.path.join(td, "state.json")
        WD_STATE_PATH = os.path.join(td, "wd.json")
        check_("check before any run says missing", check() == 1)
        rc = one_run(["mode=ok"])
        st = load_state(STATE_PATH)
        check_("OK run exits 0", rc == 0)
        check_("OK run sets last_success", bool(st.get("last_success_iso")) and st["last_success_iso"] == st["last_run_iso"])
        check_("OK run leaves last_fail empty", st.get("last_fail_iso") == "")
        check_("state file is owner-only", (os.stat(STATE_PATH).st_mode & 0o777) == 0o600)
        good = st["last_success_iso"]
        rc = one_run(["mode=crit"])
        st = load_state(STATE_PATH)
        check_("CRITICAL run exits 2", rc == 2)
        check_("CRITICAL sets last_fail", st.get("last_fail_iso") == st["last_run_iso"])
        check_("CRITICAL keeps the earlier last_success", st.get("last_success_iso") == good)
        check_("finding code kept, no key", st.get("findings") == ["CALLHOOK_SECRET_MISMATCH_403"] and "key_" not in json.dumps(st))
        check_("rejected count carried", st.get("rejected_403") == 7)
        rc = one_run(["mode=warn"])
        st = load_state(STATE_PATH)
        check_("WARN run exits 0 and is a success", rc == 0 and st["last_success_iso"] == st["last_run_iso"])
        check_("check after a good run exits 0", check() == 0)
        rc = one_run(["mode=err"])
        st = load_state(STATE_PATH)
        check_("ERROR (exit 3, no JSON) exits 3", rc == 3 and st["severity"] == "ERROR")
        check_("ERROR sets last_fail and keeps the error text", st["last_fail_iso"] == st["last_run_iso"] and "no access log" in st["error"])
        WATCHDOG = os.path.join(td, "absent.py")
        rc = one_run([])
        check_("a missing watchdog is an ERROR, not a crash", rc == 3)
    print("SELFTEST %d/%d" % (passed, passed + failed))
    return 0 if failed == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="S946: run callhook_watchdog once and keep its state for the health page.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check", action="store_true", help="the state in one line")
    ap.add_argument("--access-glob", action="append", default=None, help="passed to the watchdog (repeatable)")
    ap.add_argument("--date", default=None)
    ap.add_argument("--raw-log-dir", default=None, help="passed to the watchdog (tests; the box uses its default)")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.check:
        return check()
    return one_run(a.access_glob or [], a.date, a.raw_log_dir)


if __name__ == "__main__":
    sys.exit(main())
