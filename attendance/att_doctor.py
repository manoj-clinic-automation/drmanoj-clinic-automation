#!/usr/bin/env python3
"""
att_doctor.py — the attendance system's self-check + safe-repair tool.

ONE file, run three ways:

  python3 att_doctor.py            # --check (default): read-only health report, exit 0/1
  python3 att_doctor.py --fix      # check, then perform SAFE repairs, re-check
  python3 att_doctor.py --cron     # check silently; email ONLY if something needs attention

Principle (deterrent by default; judgement before consequence): the cron run only
CHECKS and TELLS you. It never auto-repairs. You read the alert and decide to run --fix.

Checks
  services        attlistener + attendance-dashboard are running        (--fix: restart)
  firewall        ports 8041 + 8042 in the PERMANENT ruleset            (--fix: re-add permanent)
  ack_health      the listener answers locally with a response_code     (--fix: restart listener)
  freshness       punches are still arriving (catches device-down)      (report only — physical)
  duplicates      repeated (user,time) rows in punches.csv              (--fix: write a cleaned COPY)
  disk_and_log    disk not full, punches.csv readable, log not runaway  (report only)

Settings (SMTP, recipients, punches.csv path) are imported from att_config.py,
so there is no second copy of any secret. Email reuses the attendance Gmail.
"""
import os, sys, shutil, subprocess, http.client
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import att_config as cfg
except Exception:
    cfg = None  # allows the pure-logic functions to be imported/tested standalone

# --- tunables -------------------------------------------------------------
SERVICES        = ["attlistener", "attendance-dashboard"]
REQUIRED_PORTS  = ["8041/tcp", "8042/tcp"]
DEADLINE_HOUR   = 13     # by this hour on a working day there should be >=1 punch today
DISK_WARN_PCT   = 90
LOG_WARN_MB     = 50
FLAG_FRESHNESS_ON_SUNDAY = False  # clinic is emergency-only on Sundays

LISTENER_PORT = int(os.environ.get("ATT_LISTENER_PORT", "8041"))
LISTENER_LOG  = os.environ.get("ATT_LISTENER_LOG", "/root/attlistener.log")
PUNCH_CSV     = (cfg.PUNCH_CSV if cfg else os.environ.get("ATT_PUNCH_CSV", "/root/punches.csv"))

# severities
FAIL, WARN, INFO, OK = "FAIL", "WARN", "INFO", "OK"


def now():
    return datetime.now()


# ---------- pure logic (unit-testable, no system calls) -------------------

def read_punch_keys_and_dates(path):
    """Return (keys, dates): keys = list of (user_id, datetime_str); dates = list of datetime."""
    keys, dates = [], []
    if not path or not os.path.exists(path):
        return keys, dates
    with open(path, "r", encoding="utf-8") as f:
        first = True
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if first:
                first = False
                if line.startswith("user_id"):
                    continue
            parts = line.split(",")
            if len(parts) >= 2:
                keys.append((parts[0], parts[1]))
                try:
                    dates.append(datetime.strptime(parts[1], "%Y-%m-%d %H:%M:%S"))
                except Exception:
                    pass
    return keys, dates


def freshness_eval(dates, n, deadline_hour=DEADLINE_HOUR,
                   flag_sunday=FLAG_FRESHNESS_ON_SUNDAY):
    """Decide punch-freshness. n = 'now'. Returns (severity, detail).

    Two signals, both weekend-proof (the clinic works Mon-Sat, Sunday is closed):
      PRIMARY   - it is a working day, we are past the morning deadline, and there
                  are ZERO punches today  -> the device is not reaching the VPS.
      SECONDARY - a whole WORKING DAY between the last punch and today had zero
                  punches  -> a multi-day capture gap. Sundays are ignored, so a
                  normal Saturday-evening-to-Monday-morning gap never false-alarms.
    """
    is_sunday = n.weekday() == 6
    if is_sunday and not flag_sunday:
        return OK, "Sunday — freshness check skipped (clinic is emergency-only)"
    if not dates:
        if n.hour >= deadline_hour:
            return FAIL, "no punches on record at all — device is not reaching the VPS"
        return OK, "no punches yet today (still before the morning deadline)"

    newest = max(dates)
    today = n.date()
    count_today = sum(1 for d in dates if d.date() == today)
    age_h = (n - newest).total_seconds() / 3600.0

    # SECONDARY: any full WORKING day strictly between the last punch and today
    # with no punch on it is a real gap. (No punch is newer than 'newest', so any
    # such day necessarily had zero punches.)
    missed = []
    d = newest.date() + timedelta(days=1)
    while d < today:
        if d.weekday() != 6:          # Mon-Sat are working days; skip Sunday
            missed.append(d)
        d += timedelta(days=1)
    if missed:
        span = f"{missed[0]}" if len(missed) == 1 else f"{missed[0]} .. {missed[-1]}"
        return FAIL, (f"no punches on working day(s) {span} — capture gap "
                      f"(newest punch {newest})")

    # PRIMARY: working day, past the deadline, nothing yet today.
    if n.hour >= deadline_hour and count_today == 0:
        return FAIL, (f"NO punches recorded today by {deadline_hour:02d}:00 — the device is "
                      f"likely not reaching the VPS (newest punch {newest}, {age_h:.0f}h ago)")

    return OK, f"fresh — newest punch {newest} ({age_h:.1f}h ago), {count_today} today"


def duplicates_eval(keys):
    """Returns (severity, detail, dup_count). Duplicates are INFO (engine de-dups on read)."""
    seen, dups = set(), 0
    for k in keys:
        if k in seen:
            dups += 1
        else:
            seen.add(k)
    if dups == 0:
        return OK, f"no duplicate rows ({len(keys)} punches, all unique)", 0
    return INFO, (f"{dups} duplicate (user,time) row(s) found in {len(keys)} — harmless "
                  f"(the engine de-dups on read); run --fix to write a cleaned COPY"), dups


def write_deduped_copy(path):
    """Write a de-duplicated COPY next to punches.csv. NEVER edits the original."""
    out = path + ".dedup.csv"
    seen, lines_out = set(), []
    with open(path, "r", encoding="utf-8") as f:
        header = f.readline()
        lines_out.append(header)
        for line in f:
            parts = line.rstrip("\n").split(",")
            key = (parts[0], parts[1]) if len(parts) >= 2 else (line,)
            if key in seen:
                continue
            seen.add(key)
            lines_out.append(line if line.endswith("\n") else line + "\n")
    with open(out, "w", encoding="utf-8") as f:
        f.writelines(lines_out)
    return out


# ---------- system checks (need the VPS; degrade gracefully off-box) ------

def _run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", "command-not-found"
    except Exception as e:
        return 1, "", str(e)


def check_services():
    results = []
    for svc in SERVICES:
        rc, out, err = _run(["systemctl", "is-active", svc])
        if err == "command-not-found":
            results.append((WARN, f"service {svc}: systemctl unavailable (not on VPS) — skipped"))
        elif out == "active":
            results.append((OK, f"service {svc}: active"))
        else:
            results.append((FAIL, f"service {svc}: {out or 'inactive'}"))
    return results


def fix_services():
    done = []
    for svc in SERVICES:
        rc, out, err = _run(["systemctl", "is-active", svc])
        if out != "active" and err != "command-not-found":
            _run(["systemctl", "restart", svc])
            done.append(svc)
    return done


def check_firewall():
    rc, out, err = _run(["firewall-cmd", "--permanent", "--list-ports"])
    if err == "command-not-found":
        return [(WARN, "firewall: firewall-cmd unavailable (not on VPS) — skipped")]
    ports = set(out.split())
    res = []
    for p in REQUIRED_PORTS:
        res.append((OK, f"firewall: {p} present (permanent)") if p in ports
                   else (FAIL, f"firewall: {p} MISSING from permanent ruleset"))
    return res


def fix_firewall():
    rc, out, err = _run(["firewall-cmd", "--permanent", "--list-ports"])
    if err == "command-not-found":
        return []
    ports = set(out.split())
    added = []
    for p in REQUIRED_PORTS:
        if p not in ports:
            _run(["firewall-cmd", f"--add-port={p}", "--permanent"])
            added.append(p)
    if added:
        _run(["firewall-cmd", "--reload"])
    return added


def check_ack_health(port=LISTENER_PORT):
    """Send a heartbeat (writes nothing) and confirm the listener acks locally."""
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("POST", "/", body=b"\x00\x00\x00\x00{}\x00",
                     headers={"request_code": "receive_cmd",
                              "Content-Type": "application/octet-stream"})
        r = conn.getresponse(); r.read()
        rc = dict((k.lower(), v) for k, v in r.getheaders()).get("response_code")
        conn.close()
        if r.status == 200 and rc is not None:
            return [(OK, f"ack_health: listener on :{port} acking locally (response_code={rc})")]
        return [(FAIL, f"ack_health: listener on :{port} replied {r.status} but no response_code header")]
    except Exception as e:
        return [(FAIL, f"ack_health: listener on :{port} not answering ({e})")]


def check_freshness():
    _, dates = read_punch_keys_and_dates(PUNCH_CSV)
    sev, detail = freshness_eval(dates, now())
    return [(sev, f"freshness: {detail}")]


def check_duplicates():
    keys, _ = read_punch_keys_and_dates(PUNCH_CSV)
    sev, detail, _ = duplicates_eval(keys)
    return [(sev, f"duplicates: {detail}")]


def check_disk_and_log():
    res = []
    try:
        total, used, free = shutil.disk_usage("/")
        pct = used / total * 100
        sev = WARN if pct >= DISK_WARN_PCT else OK
        res.append((sev, f"disk: {pct:.0f}% used, {free // (1024**3)} GB free"))
    except Exception as e:
        res.append((WARN, f"disk: could not read usage ({e})"))
    if os.path.exists(PUNCH_CSV):
        try:
            with open(PUNCH_CSV, "r", encoding="utf-8") as f:
                f.readline()
            res.append((OK, f"punches.csv: readable"))
        except Exception as e:
            res.append((FAIL, f"punches.csv: NOT readable ({e})"))
    else:
        res.append((WARN, f"punches.csv: not found at {PUNCH_CSV}"))
    if os.path.exists(LISTENER_LOG):
        mb = os.path.getsize(LISTENER_LOG) / (1024**2)
        sev = WARN if mb >= LOG_WARN_MB else OK
        res.append((sev, f"listener log: {mb:.1f} MB"))
    return res


# ---------- orchestration -------------------------------------------------

def run_all_checks():
    results = []
    results += check_services()
    results += check_firewall()
    results += check_ack_health()
    results += check_freshness()
    results += check_duplicates()
    results += check_disk_and_log()
    return results


def worst(results):
    if any(s == FAIL for s, _ in results):
        return FAIL
    if any(s == WARN for s, _ in results):
        return WARN
    return OK


def format_report(results):
    icon = {OK: "[ OK ]", WARN: "[WARN]", FAIL: "[FAIL]", INFO: "[INFO]"}
    lines = [f"Attendance Doctor — {now():%Y-%m-%d %H:%M:%S}", "-" * 56]
    for sev, detail in results:
        lines.append(f"{icon[sev]}  {detail}")
    lines.append("-" * 56)
    lines.append(f"Overall: {worst(results)}")
    return "\n".join(lines)


def send_alert(subject, body):
    """Email via att_config SMTP. If no SMTP password is set, write a file instead (safe preview)."""
    if not cfg or not getattr(cfg, "SMTP_PASS", ""):
        path = f"/root/att_doctor_alert_{now():%Y-%m-%d_%H%M%S}.txt"
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(subject + "\n\n" + body + "\n")
            print(f"(no SMTP password set — alert written to {path})")
        except Exception as e:
            print(f"(could not write alert file: {e})")
        return
    import smtplib
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.EMAIL_FROM
    msg["To"] = ", ".join(cfg.EMAIL_TO)
    msg.set_content(body)
    with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=30) as s:
        s.starttls()
        s.login(cfg.SMTP_USER, cfg.SMTP_PASS)
        s.send_message(msg)
    print("alert emailed.")


def main():
    args = set(sys.argv[1:])
    mode_fix = "--fix" in args
    mode_cron = "--cron" in args

    results = run_all_checks()

    if mode_fix:
        fixed = []
        if any(s == FAIL and "service" in d for s, d in results):
            r = fix_services()
            if r: fixed.append(f"restarted services: {', '.join(r)}")
        if any(s == FAIL and "firewall" in d for s, d in results):
            r = fix_firewall()
            if r: fixed.append(f"re-added firewall ports (permanent): {', '.join(r)}")
        if any(s == INFO and "duplicate" in d for s, d in results):
            if os.path.exists(PUNCH_CSV):
                out = write_deduped_copy(PUNCH_CSV)
                fixed.append(f"wrote cleaned copy: {out} (original untouched)")
        # re-check after repairs
        results = run_all_checks()
        print(format_report(results))
        if fixed:
            print("\nRepairs performed:")
            for f in fixed:
                print("  - " + f)
        else:
            print("\nNo safe auto-repairs were applicable.")
        sys.exit(1 if worst(results) == FAIL else 0)

    report = format_report(results)
    overall = worst(results)

    if mode_cron:
        # silent when healthy; speak only when something needs attention
        if overall in (FAIL, WARN):
            subject = f"[Attendance Doctor] {overall} at {now():%Y-%m-%d %H:%M} — Bareilly clinic"
            body = report + "\n\nRun `python3 /root/att_doctor.py --fix` to attempt safe repairs.\n"
            send_alert(subject, body)
            print(report)
        else:
            print(f"[{now():%Y-%m-%d %H:%M}] all healthy — no email sent.")
        sys.exit(1 if overall == FAIL else 0)

    # default: --check
    print(report)
    sys.exit(1 if overall == FAIL else 0)


if __name__ == "__main__":
    main()
