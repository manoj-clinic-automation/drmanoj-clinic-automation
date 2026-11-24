#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
callhook_watchdog.py  --  v1.0  --  Session 125  --  Dr. Manoj Agarwal Clinic

WHAT THIS IS
    A detector for the fault code CALLHOOK_SECRET_MISMATCH_403.

    On 06-08 Jul 2026 the MyOperator call webhook was rejected 4,449 times
    over three clinic days and NOTHING in the clinic's own systems noticed.
    A receptionist found it. This script is the thing that should have found it.

WHY IT READS THE ACCESS LOG
    The receiver (call_hook_capture.py) returns 403 BEFORE it calls raw_log()
    and before it journals. A rejected delivery therefore leaves no trace
    anywhere except the web server's access log. Absence of a daily
    YYYY-MM-DD.jsonl cannot distinguish "nobody called" from "we rejected
    every call". Only the access log can tell those two apart.

WHAT IT TOUCHES
    Nothing. It opens two things read-only:
        - the web-server access logs   (glob, see ACCESS_LOG_GLOBS)
        - the raw-log directory listing (RAW_LOG_DIR)
    It writes one file, and only with --state: a small JSON state file used to
    report "new since last run". It never writes to the receiver, the .env,
    the service, or any Google Sheet. It cannot take the clinic down.

EXIT CODES  (for systemd / cron / OnFailure)
    0   OK        nothing wrong
    1   WARN      something to look at, not urgent
    2   CRITICAL  the webhook is being rejected, or the raw log is missing
                  on a clinic day past the mid-morning cutoff
    3   ERROR     the watchdog itself could not run (bad glob, unreadable log)

SECRETS
    The ?key= value is masked on every code path that can print. There is no
    flag to unmask it. Keys are compared only as opaque 6-char md5 labels.

USAGE
    /root/wa/venv/bin/python3 callhook_watchdog.py --selftest
    /root/wa/venv/bin/python3 callhook_watchdog.py
    /root/wa/venv/bin/python3 callhook_watchdog.py --json
    /root/wa/venv/bin/python3 callhook_watchdog.py --date 2026-07-07
    /root/wa/venv/bin/python3 callhook_watchdog.py --state /root/wa/call-hook/watchdog_state.json

Python 3.9 compatible (the VPS interpreter is past EOL; no 3.10+ syntax used).
"""

from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

# --------------------------------------------------------------------------
# CONFIGURATION  -- everything tunable lives here, nothing is hidden in logic
# --------------------------------------------------------------------------

VERSION = "1.0"
BUILD = "S125"

ACCESS_LOG_GLOBS = [
    "/home/*/logs/*access*",
]

RAW_LOG_DIR = "/root/wa/call-hook/call_hook_logs"

# The clinic is in Bareilly. Pin the timezone rather than trusting the VPS TZ,
# so a server-level TZ change can never silently shift "today".
IST = timezone(timedelta(hours=5, minutes=30))

# Weekdays the clinic runs. Monday=0 ... Sunday=6.
# Sunday excluded: a missing raw log on a closed day is not a fault.
CLINIC_WEEKDAYS = (0, 1, 2, 3, 4, 5)

# Past this hour (IST) on a clinic day, a missing/empty raw log is CRITICAL.
MID_MORNING_HOUR = 11

# A 403 seen within this many minutes of "now" means the fault is LIVE,
# not merely historical. This is what separates "we fixed it at 10:28"
# from "it is broken right now".
RECENT_403_WINDOW_MIN = 30

# Only requests to this path are ours.
ROUTE_MARKER = "mo-callhook"

FAULT_CODE = "CALLHOOK_SECRET_MISMATCH_403"

# --------------------------------------------------------------------------
# PARSING
# --------------------------------------------------------------------------

# LiteSpeed here emits lines that may be wrapped in literal double quotes,
# so anchor on the bracketed timestamp and the status after the protocol.
_TS_RE = re.compile(r"\[(\d{2}/[A-Za-z]{3}/\d{4}):(\d{2}:\d{2}:\d{2})\s*([+-]\d{4})?\]")
_STATUS_RE = re.compile(r'"\s+(\d{3})\s')
_KEY_RE = re.compile(r"[?&]key=([^&\s\"]+)")

_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def mask_key(raw_key):
    """Return an opaque, stable, non-reversible label. Never the key."""
    if raw_key is None:
        return "key_none"
    digest = hashlib.md5(raw_key.encode("utf-8", "replace")).hexdigest()
    return "key_" + digest[:6]


def parse_line(line):
    """
    Return dict(ts=aware datetime, status=int, key_label=str, key_len=int)
    or None if the line is not a parseable mo-callhook request.
    """
    if ROUTE_MARKER not in line:
        return None

    m_ts = _TS_RE.search(line)
    m_st = _STATUS_RE.search(line)
    if not m_ts or not m_st:
        return None

    datepart, timepart, offset = m_ts.group(1), m_ts.group(2), m_ts.group(3)
    try:
        dd, mon, yyyy = datepart.split("/")
        hh, mi, ss = timepart.split(":")
        month = _MONTHS.get(mon)
        if month is None:
            return None
        if offset:
            sign = 1 if offset[0] == "+" else -1
            tz = timezone(sign * timedelta(hours=int(offset[1:3]), minutes=int(offset[3:5])))
        else:
            tz = IST
        ts = datetime(int(yyyy), month, int(dd), int(hh), int(mi), int(ss), tzinfo=tz)
    except (ValueError, IndexError):
        return None

    try:
        status = int(m_st.group(1))
    except ValueError:
        return None

    m_key = _KEY_RE.search(line)
    raw_key = m_key.group(1) if m_key else None

    return {
        "ts": ts,
        "status": status,
        "key_label": mask_key(raw_key),
        "key_len": len(raw_key) if raw_key else 0,
    }


def _open_maybe_gz(path):
    if path.endswith(".gz"):
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def iter_access_lines(globs):
    """Yield lines from every matching access log. Rotated .gz included."""
    paths = []
    for g in globs:
        paths.extend(sorted(glob.glob(g)))
    if not paths:
        raise RuntimeError("no access log matched globs: %s" % (", ".join(globs),))
    for p in paths:
        try:
            with _open_maybe_gz(p) as fh:
                for line in fh:
                    yield line
        except OSError as exc:
            sys.stderr.write("warn: cannot read %s (%s)\n" % (p, exc))


# --------------------------------------------------------------------------
# ANALYSIS
# --------------------------------------------------------------------------

def collect(lines, target_date, now):
    """Fold the access log into the few numbers we actually reason about."""
    out = {
        "n_200": 0,
        "n_403": 0,
        "n_other": 0,
        "last_200": None,
        "last_403": None,
        "recent_403": 0,
        "keys_200": {},
        "keys_403": {},
    }
    cutoff = now - timedelta(minutes=RECENT_403_WINDOW_MIN)

    for line in lines:
        rec = parse_line(line)
        if rec is None:
            continue
        if rec["ts"].astimezone(IST).date() != target_date:
            continue

        st = rec["status"]
        if st == 200:
            out["n_200"] += 1
            out["keys_200"][rec["key_label"]] = out["keys_200"].get(rec["key_label"], 0) + 1
            if out["last_200"] is None or rec["ts"] > out["last_200"]:
                out["last_200"] = rec["ts"]
        elif st == 403:
            out["n_403"] += 1
            out["keys_403"][rec["key_label"]] = out["keys_403"].get(rec["key_label"], 0) + 1
            if out["last_403"] is None or rec["ts"] > out["last_403"]:
                out["last_403"] = rec["ts"]
            if rec["ts"] >= cutoff:
                out["recent_403"] += 1
        else:
            out["n_other"] += 1

    return out


def raw_log_status(raw_dir, target_date):
    """Is the day's jsonl present, and how many lines does it hold?"""
    path = os.path.join(raw_dir, "%s.jsonl" % target_date.isoformat())
    if not os.path.exists(path):
        return {"path": path, "exists": False, "lines": 0, "mtime": None}
    lines = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for _ in fh:
                lines += 1
        mtime = datetime.fromtimestamp(os.path.getmtime(path), IST).isoformat()
    except OSError as exc:
        return {"path": path, "exists": True, "lines": -1, "mtime": None, "error": str(exc)}
    return {"path": path, "exists": True, "lines": lines, "mtime": mtime}


def is_clinic_day(d):
    return d.weekday() in CLINIC_WEEKDAYS


def evaluate(acc, raw, target_date, now):
    """
    Turn the numbers into findings. Each finding carries its own severity;
    the run's severity is the worst finding. Every finding says what it saw,
    not merely that something is wrong.
    """
    findings = []
    clinic = is_clinic_day(target_date)
    past_cutoff = (now.astimezone(IST).hour >= MID_MORNING_HOUR) or (now.astimezone(IST).date() > target_date)

    # -- 1. The fault itself: are we rejecting deliveries RIGHT NOW?
    if acc["recent_403"] > 0:
        findings.append((
            2, FAULT_CODE,
            "%d rejection(s) in the last %d minutes. The webhook secret does not match "
            "what MyOperator is sending. Duration data is being lost as of now."
            % (acc["recent_403"], RECENT_403_WINDOW_MIN),
        ))

    # -- 2. The blind spot: clinic day, mid-morning, and no raw log at all.
    if clinic and past_cutoff and (not raw["exists"] or raw["lines"] == 0):
        if acc["n_403"] > 0:
            detail = ("No raw log, and %d rejection(s) in today's access log. "
                      "The deliveries are arriving and being refused." % acc["n_403"])
        elif acc["n_200"] == 0:
            detail = ("No raw log, and no requests of any kind in the access log. "
                      "MyOperator is not delivering at all -- check the panel subscription, "
                      "not the secret.")
        else:
            detail = ("No raw log despite %d accepted request(s). The receiver is accepting "
                      "and not writing. Check disk, permissions, and the raw_log() path."
                      % acc["n_200"])
        findings.append((2, "CALLHOOK_RAWLOG_MISSING", detail))

    # -- 3. Clinic day, mid-morning, log exists, but nothing was ever accepted.
    if clinic and past_cutoff and raw["exists"] and raw["lines"] > 0 and acc["n_200"] == 0:
        findings.append((
            1, "CALLHOOK_NO_ACCEPTED_TODAY",
            "Raw log exists with %d line(s) but the access log shows zero 200s today. "
            "Timestamps disagree; investigate before trusting either." % raw["lines"],
        ))

    # -- 4. Historical 403s, already stopped. Informational, but say it plainly:
    #       this is the signature of a fault that was fixed today.
    if acc["n_403"] > 0 and acc["recent_403"] == 0:
        last = acc["last_403"].astimezone(IST).strftime("%H:%M:%S") if acc["last_403"] else "?"
        findings.append((
            1, "CALLHOOK_403_EARLIER_TODAY",
            "%d rejection(s) today, none in the last %d minutes (last at %s). "
            "Consistent with a fault that has since been fixed. Not currently failing."
            % (acc["n_403"], RECENT_403_WINDOW_MIN, last),
        ))

    # -- 5. More than one key in flight => more than one webhook subscription.
    #       This is the check that would have settled the S124 second-entry question.
    all_keys = set(acc["keys_200"]) | set(acc["keys_403"])
    if len(all_keys) > 1:
        findings.append((
            1, "CALLHOOK_MULTIPLE_KEYS",
            "%d distinct keys delivered today (%s). More than one webhook subscription "
            "exists in the MyOperator panel. Editing one will not fix the other."
            % (len(all_keys), ", ".join(sorted(all_keys))),
        ))

    # -- 6. Quiet day. NOT a pass and NOT a failure -- say so out loud.
    if clinic and past_cutoff and acc["n_200"] == 0 and acc["n_403"] == 0 and not raw["exists"]:
        findings.append((
            1, "CALLHOOK_SILENT",
            "No requests at all today. Cannot distinguish 'no dashboard-dialled calls' "
            "from 'webhook unsubscribed'. Place one dialler call to disambiguate.",
        ))

    severity = max([f[0] for f in findings]) if findings else 0
    return severity, findings


# --------------------------------------------------------------------------
# STATE  (optional -- only written when --state is passed)
# --------------------------------------------------------------------------

def load_state(path):
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_state(path, payload):
    if not path:
        return
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
        os.replace(tmp, path)
        os.chmod(path, 0o600)
    except OSError as exc:
        sys.stderr.write("warn: could not write state %s (%s)\n" % (path, exc))


# --------------------------------------------------------------------------
# REPORTING
# --------------------------------------------------------------------------

SEV_NAME = {0: "OK", 1: "WARN", 2: "CRITICAL", 3: "ERROR"}
SEV_MARK = {0: "OK  ", 1: "WARN", 2: "CRIT", 3: "ERR "}


def render_text(sev, findings, acc, raw, target_date, now):
    L = []
    L.append("callhook_watchdog v%s (%s)   %s" % (VERSION, BUILD, SEV_NAME[sev]))
    L.append("clinic day : %s  (%s)%s" % (
        target_date.isoformat(),
        target_date.strftime("%A"),
        "" if is_clinic_day(target_date) else "  -- NOT a clinic day",
    ))
    L.append("checked at : %s IST" % now.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S"))
    L.append("")
    L.append("access log : %d accepted (200) / %d rejected (403) / %d other" % (
        acc["n_200"], acc["n_403"], acc["n_other"]))
    if acc["last_200"]:
        L.append("last 200   : %s IST" % acc["last_200"].astimezone(IST).strftime("%H:%M:%S"))
    if acc["last_403"]:
        L.append("last 403   : %s IST" % acc["last_403"].astimezone(IST).strftime("%H:%M:%S"))
    keys = sorted(set(acc["keys_200"]) | set(acc["keys_403"]))
    if keys:
        L.append("keys seen  : %s" % ", ".join(
            "%s (%d ok / %d rejected)" % (k, acc["keys_200"].get(k, 0), acc["keys_403"].get(k, 0))
            for k in keys))
    L.append("raw log    : %s (%s, %d lines)" % (
        raw["path"],
        "present" if raw["exists"] else "MISSING",
        max(raw["lines"], 0)))
    L.append("")
    if not findings:
        L.append("  no findings -- the call webhook is healthy.")
    for s, code, detail in sorted(findings, key=lambda f: -f[0]):
        L.append("  [%s] %s" % (SEV_MARK[s], code))
        for chunk in _wrap(detail, 70):
            L.append("         %s" % chunk)
    return "\n".join(L)


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return out


def render_json(sev, findings, acc, raw, target_date, now):
    return json.dumps({
        "version": VERSION,
        "build": BUILD,
        "severity": SEV_NAME[sev],
        "exit_code": sev,
        "date": target_date.isoformat(),
        "clinic_day": is_clinic_day(target_date),
        "checked_at": now.astimezone(IST).isoformat(),
        "accepted_200": acc["n_200"],
        "rejected_403": acc["n_403"],
        "other": acc["n_other"],
        "recent_403": acc["recent_403"],
        "last_200": acc["last_200"].astimezone(IST).isoformat() if acc["last_200"] else None,
        "last_403": acc["last_403"].astimezone(IST).isoformat() if acc["last_403"] else None,
        "keys_200": acc["keys_200"],
        "keys_403": acc["keys_403"],
        "raw_log": raw,
        "findings": [{"severity": SEV_NAME[s], "code": c, "detail": d} for s, c, d in findings],
    }, indent=2, sort_keys=True)


# --------------------------------------------------------------------------
# SELFTEST  -- offline, no filesystem, no network
# --------------------------------------------------------------------------

def _mk(ts, status, key="AbCdEf123456"):
    return ('"13.126.78.76 - - [%s +0530] "POST /mo-callhook?key=%s HTTP/2" %d 76 "-" '
            '"Go-http-client/2.0""' % (ts, key, status))


def selftest():
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("  FAIL: %s" % name)

    # -- parsing ------------------------------------------------------------
    r = parse_line(_mk("08/Jul/2026:12:06:51", 200))
    check("parses a 200", r is not None and r["status"] == 200)
    check("parses timestamp", r["ts"].hour == 12 and r["ts"].minute == 6)
    check("parses offset", r["ts"].utcoffset() == timedelta(hours=5, minutes=30))
    check("masks key", r["key_label"].startswith("key_") and len(r["key_label"]) == 10)
    check("key len", r["key_len"] == 12)

    r403 = parse_line(_mk("08/Jul/2026:10:28:02", 403))
    check("parses a 403", r403["status"] == 403)

    check("ignores unrelated route", parse_line('GET /favicon.ico HTTP/2" 200 5') is None)
    check("ignores garbage", parse_line("this is not a log line") is None)
    check("ignores truncated ts", parse_line('"1.2.3.4 [bad] "POST /mo-callhook?key=x" 200 1') is None)

    # unquoted (standard combined) format must also parse
    plain = '1.2.3.4 - - [08/Jul/2026:09:00:00 +0530] "POST /mo-callhook?key=zz HTTP/1.1" 403 33 "-" "Go"'
    check("parses unquoted format", parse_line(plain)["status"] == 403)

    # missing offset falls back to IST
    nooff = '1.2.3.4 - - [08/Jul/2026:09:00:00] "POST /mo-callhook?key=zz HTTP/1.1" 200 33'
    check("offset defaults to IST", parse_line(nooff)["ts"].utcoffset() == timedelta(hours=5, minutes=30))

    # -- masking is stable and non-reversible -------------------------------
    check("mask stable", mask_key("secret1") == mask_key("secret1"))
    check("mask distinguishes", mask_key("secret1") != mask_key("secret2"))
    check("mask hides key", "secret1" not in mask_key("secret1"))
    check("mask handles none", mask_key(None) == "key_none")

    # -- the 08-Jul reality: 403 storm that STOPPED, then 200s --------------
    day = datetime(2026, 7, 8, tzinfo=IST).date()
    now = datetime(2026, 7, 8, 12, 10, 0, tzinfo=IST)
    lines = [_mk("08/Jul/2026:10:%02d:00" % m, 403) for m in range(0, 29)]
    lines += [_mk("08/Jul/2026:1%d:00:00" % h, 200) for h in (1, 2)]
    acc = collect(lines, day, now)
    check("counts 403s", acc["n_403"] == 29)
    check("counts 200s", acc["n_200"] == 2)
    check("no recent 403", acc["recent_403"] == 0)
    raw = {"path": "/x/2026-07-08.jsonl", "exists": True, "lines": 74, "mtime": None}
    sev, f = evaluate(acc, raw, day, now)
    codes = [c for _, c, _ in f]
    check("fixed fault -> WARN not CRIT", sev == 1)
    check("reports earlier 403s", "CALLHOOK_403_EARLIER_TODAY" in codes)
    check("does not raise the fault code", FAULT_CODE not in codes)

    # -- a LIVE 403 storm ---------------------------------------------------
    lines = [_mk("08/Jul/2026:12:0%d:00" % m, 403) for m in range(0, 9)]
    acc = collect(lines, day, now)
    check("recent 403s counted", acc["recent_403"] == 9)
    sev, f = evaluate(acc, {"path": "p", "exists": False, "lines": 0, "mtime": None}, day, now)
    check("live fault -> CRITICAL", sev == 2)
    check("raises the fault code", FAULT_CODE in [c for _, c, _ in f])
    check("also raises rawlog missing", "CALLHOOK_RAWLOG_MISSING" in [c for _, c, _ in f])

    # -- two distinct keys => two subscriptions -----------------------------
    lines = [_mk("08/Jul/2026:09:00:00", 200, key="AAAA"), _mk("08/Jul/2026:09:01:00", 403, key="BBBB")]
    acc = collect(lines, day, now)
    sev, f = evaluate(acc, {"path": "p", "exists": True, "lines": 5, "mtime": None}, day, now)
    check("detects multiple keys", "CALLHOOK_MULTIPLE_KEYS" in [c for _, c, _ in f])

    # -- one key, both statuses (the ACTUAL 08-Jul case) => no false alarm --
    lines = [_mk("08/Jul/2026:09:00:00", 200, key="SAME"), _mk("08/Jul/2026:09:01:00", 403, key="SAME")]
    acc = collect(lines, day, now)
    sev, f = evaluate(acc, {"path": "p", "exists": True, "lines": 5, "mtime": None}, day, now)
    check("single key -> no multi-key alarm", "CALLHOOK_MULTIPLE_KEYS" not in [c for _, c, _ in f])

    # -- silence on a clinic day is NOT a pass ------------------------------
    acc = collect([], day, now)
    sev, f = evaluate(acc, {"path": "p", "exists": False, "lines": 0, "mtime": None}, day, now)
    codes = [c for _, c, _ in f]
    check("silent clinic day -> CRITICAL rawlog", sev == 2 and "CALLHOOK_RAWLOG_MISSING" in codes)
    check("silent clinic day names the panel", any("not delivering at all" in d for _, _, d in f))

    # -- Sunday: missing raw log is fine ------------------------------------
    sunday = datetime(2026, 7, 5, tzinfo=IST).date()
    sun_now = datetime(2026, 7, 5, 12, 0, 0, tzinfo=IST)
    check("sunday is not a clinic day", not is_clinic_day(sunday))
    sev, f = evaluate(collect([], sunday, sun_now),
                      {"path": "p", "exists": False, "lines": 0, "mtime": None}, sunday, sun_now)
    check("sunday silence -> OK", sev == 0)

    # -- before mid-morning: missing raw log is not yet a fault -------------
    early = datetime(2026, 7, 8, 8, 0, 0, tzinfo=IST)
    sev, f = evaluate(collect([], day, early),
                      {"path": "p", "exists": False, "lines": 0, "mtime": None}, day, early)
    check("pre-cutoff silence -> OK", sev == 0)

    # -- date filtering -----------------------------------------------------
    mixed = [_mk("07/Jul/2026:10:00:00", 403), _mk("08/Jul/2026:10:00:00", 200)]
    acc = collect(mixed, day, now)
    check("filters other days", acc["n_403"] == 0 and acc["n_200"] == 1)

    # -- renderers never crash and never leak -------------------------------
    acc = collect([_mk("08/Jul/2026:10:00:00", 403, key="TOPSECRETKEY")], day, now)
    raw = {"path": "p", "exists": True, "lines": 1, "mtime": None}
    sev, f = evaluate(acc, raw, day, now)
    txt = render_text(sev, f, acc, raw, day, now)
    js = render_json(sev, f, acc, raw, day, now)
    check("text renders", "callhook_watchdog" in txt)
    check("json renders", json.loads(js)["date"] == "2026-07-08")
    check("text never leaks the key", "TOPSECRETKEY" not in txt)
    check("json never leaks the key", "TOPSECRETKEY" not in js)

    print("selftest: %d/%d passed" % (passed, passed + failed))
    return 0 if failed == 0 else 3


# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Detect CALLHOOK_SECRET_MISMATCH_403.")
    ap.add_argument("--selftest", action="store_true", help="run offline tests and exit")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--date", help="YYYY-MM-DD (default: today, IST)")
    ap.add_argument("--state", help="path to a JSON state file (written; optional)")
    ap.add_argument("--raw-log-dir", default=RAW_LOG_DIR)
    ap.add_argument("--access-glob", action="append", default=None)
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    now = datetime.now(timezone.utc)
    if args.date:
        try:
            target = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            sys.stderr.write("error: --date must be YYYY-MM-DD\n")
            return 3
    else:
        target = now.astimezone(IST).date()

    globs = args.access_glob or ACCESS_LOG_GLOBS
    try:
        acc = collect(iter_access_lines(globs), target, now)
    except RuntimeError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 3

    raw = raw_log_status(args.raw_log_dir, target)
    sev, findings = evaluate(acc, raw, target, now)

    if args.json:
        print(render_json(sev, findings, acc, raw, target, now))
    else:
        print(render_text(sev, findings, acc, raw, target, now))

    if args.state:
        prev = load_state(args.state)
        save_state(args.state, {
            "last_run": now.astimezone(IST).isoformat(),
            "last_severity": SEV_NAME[sev],
            "date": target.isoformat(),
            "accepted_200": acc["n_200"],
            "rejected_403": acc["n_403"],
            "previous_severity": prev.get("last_severity"),
        })

    return sev


if __name__ == "__main__":
    sys.exit(main())
