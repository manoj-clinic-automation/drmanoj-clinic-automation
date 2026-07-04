#!/root/wa/venv/bin/python3
# -*- coding: utf-8 -*-
"""
clinic_health_report.py  --  Daily clinic health report (READ-ONLY).

Deliverable 3, step 1 (Session 63). Takes NO action on the box. It only
READS what the other layers already know and sends one daily summary:
  - the 9 always-on services (systemctl is-active)
  - the 3 timer-job heartbeats (/root/wa/heartbeats/*.hb)
  - disk usage (df /)
  - the follow-up list freshness (followup-push heartbeat)
  - actions the watchman took in the last 24h (/root/wa/watchdog.log)

Delivery: ntfy one-liner + Gmail detail. Reuses the watchman's env
(/root/wa/.env: WATCHDOG_SMTP_*, ntfy topic). Same DNA as the watchman:
read-only, fail-loud. No PHI. No anti-spam file needed (it's a once-daily
digest, not an alerter -- it is MEANT to send every day).

Run by hand any time (safe, read-only):
    cd /root/wa && /root/wa/venv/bin/python3 clinic_health_report.py

Intended schedule: 08:00 IST daily (via its own systemd .timer, installed
later after this is proven).
"""

import os
import sys
import subprocess
import datetime
import smtplib
import urllib.request
from email.mime.text import MIMEText

# ---------------------------------------------------------------------------
# Constants (all match the live box, confirmed Session 63)
# ---------------------------------------------------------------------------
WA_DIR        = "/root/wa"
ENV_PATH      = os.path.join(WA_DIR, ".env")
HB_DIR        = os.path.join(WA_DIR, "heartbeats")
WATCHDOG_LOG  = os.path.join(WA_DIR, "watchdog.log")
NTFY_URL      = "https://ntfy.sh/drmka-yfv80gjcixa643"
LOG_PATH      = os.path.join(WA_DIR, "health_report.log")
IST           = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# The nine always-on services (per SOP_VPS_Services / KB v1.30)
SERVICES = [
    "wa-receiver",
    "wa-send-api",
    "call-api",
    "call-hook",
    "clinic-portal",
    "clinic-followup-receiver",
    "wa-notifier",
    "attendance-dashboard",
    "attlistener",
]

# The three timer jobs -> their heartbeat files + human labels
TIMER_JOBS = [
    ("clinic-followup-push",   "followup-push.hb",     "Follow-up push"),
    ("call-recording-archive", "recording-archive.hb", "Recording archive"),
    ("call-transcription",     "transcription.hb",     "Transcription"),
]

# Disk thresholds (percent used)
DISK_WARN = 80
DISK_CRIT = 90


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def log(msg):
    line = "%s  %s" % (datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


def load_env(path):
    """Read KEY=VALUE lines from .env. Never prints values."""
    env = {}
    try:
        with open(path) as f:
            for raw in f:
                s = raw.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except Exception as e:
        log("WARN could not read .env: %s" % e)
    return env


def svc_is_active(name):
    """Return True if systemctl reports the service active. Read-only."""
    try:
        r = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=15,
        )
        return r.stdout.strip() == "active"
    except Exception as e:
        log("WARN is-active %s failed: %s" % (name, e))
        return False


def read_heartbeat(fname):
    """Return (exists, iso_string, age_hours) for a heartbeat file."""
    path = os.path.join(HB_DIR, fname)
    if not os.path.exists(path):
        return (False, None, None)
    try:
        with open(path) as f:
            stamp = f.read().strip()
        # Heartbeats are UTC 'YYYY-MM-DDTHH:MM:SSZ'
        dt = datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        age = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds() / 3600.0
        return (True, stamp, age)
    except Exception as e:
        log("WARN reading heartbeat %s: %s" % (fname, e))
        return (True, "unreadable", None)


def disk_percent_used():
    """Return integer percent used on / (read-only via df)."""
    try:
        r = subprocess.run(["df", "-P", "/"], capture_output=True, text=True, timeout=15)
        last = r.stdout.strip().splitlines()[-1]
        pct = [p for p in last.split() if p.endswith("%")][0]
        return int(pct.rstrip("%"))
    except Exception as e:
        log("WARN df failed: %s" % e)
        return None


def watchdog_actions_last_24h():
    """Return a list of watchdog.log lines from the last 24h that mention
    an action (restart/recover/down). Read-only."""
    out = []
    if not os.path.exists(WATCHDOG_LOG):
        return out
    cutoff = datetime.datetime.now(IST) - datetime.timedelta(hours=24)
    try:
        with open(WATCHDOG_LOG) as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                low = s.lower()
                if not any(k in low for k in ("restart", "recover", "down", "alert")):
                    continue
                # try to parse the leading timestamp 'YYYY-MM-DD HH:MM:SS'
                try:
                    ts = datetime.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
                    ts = ts.replace(tzinfo=IST)
                    if ts >= cutoff:
                        out.append(s)
                except Exception:
                    # no parseable timestamp -> include it to be safe (fail-loud)
                    out.append(s)
    except Exception as e:
        log("WARN reading watchdog log: %s" % e)
    return out


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------
def build_report():
    now = datetime.datetime.now(IST)
    attention = []          # human-readable items needing the doctor
    lines = []

    # --- services ---
    down = [s for s in SERVICES if not svc_is_active(s)]
    if down:
        attention.append("Service(s) DOWN: " + ", ".join(down))
        svc_line = u"\u26a0\ufe0f  %d of %d down (%s)" % (len(down), len(SERVICES), ", ".join(down))
    else:
        svc_line = u"\u2705 all %d active" % len(SERVICES)

    # --- timer jobs ---
    timer_lines = []
    for unit, hb, label in TIMER_JOBS:
        exists, stamp, age = read_heartbeat(hb)
        if not exists:
            timer_lines.append(u"  \u2014 %s: no heartbeat yet" % label)
            # Not necessarily a fault (overnight jobs seed later) -> not attention here.
        elif age is None:
            timer_lines.append(u"  \u26a0\ufe0f %s: heartbeat unreadable" % label)
            attention.append("%s heartbeat unreadable" % label)
        else:
            timer_lines.append(u"  \u2705 %s: last ran %s UTC (%.1fh ago)" % (label, stamp, age))

    # --- disk ---
    pct = disk_percent_used()
    if pct is None:
        disk_line = u"\u26a0\ufe0f could not read disk"
        attention.append("Disk usage unreadable")
    elif pct >= DISK_CRIT:
        disk_line = u"\u26a0\ufe0f %d%% used (CRITICAL)" % pct
        attention.append("Disk %d%% used (>= %d%%)" % (pct, DISK_CRIT))
    elif pct >= DISK_WARN:
        disk_line = u"\u26a0\ufe0f %d%% used (warning)" % pct
        attention.append("Disk %d%% used (>= %d%%)" % (pct, DISK_WARN))
    else:
        disk_line = u"\u2705 %d%% used" % pct

    # --- watchman actions in last 24h ---
    actions = watchdog_actions_last_24h()

    # --- overall ---
    overall_ok = not attention
    overall = u"\u2705 ALL GREEN" if overall_ok else u"\u26a0\ufe0f ATTENTION NEEDED"

    # --- assemble email body ---
    lines.append("CLINIC HEALTH REPORT \u2014 %s IST" % now.strftime("%Y-%m-%d %H:%M"))
    lines.append("")
    lines.append("OVERALL: %s" % overall)
    lines.append("")
    lines.append("SERVICES (9 always-on) ... %s" % svc_line)
    lines.append("TIMER JOBS (3):")
    lines.extend(timer_lines)
    lines.append("DISK SPACE ............... %s" % disk_line)
    lines.append("")
    lines.append("ACTIONS TAKEN BY WATCHMAN (last 24h):")
    if actions:
        for a in actions:
            lines.append("  \u2022 %s" % a)
    else:
        lines.append("  \u2022 none")
    lines.append("")
    lines.append("ANYTHING NEEDING YOU:")
    if attention:
        for a in attention:
            lines.append("  \u2022 %s" % a)
    else:
        lines.append("  \u2022 nothing \u2014 all green")
    lines.append("")
    lines.append("(Read-only daily digest. Absence of this report = the reporter or box is down.)")

    body = "\n".join(lines)
    ntfy_one = (u"\u2705 Clinic all green" if overall_ok
                else u"\u26a0\ufe0f Clinic: %d item(s) need you \u2014 check email" % len(attention))
    subject = "Clinic health %s \u2014 %s" % (
        ("OK" if overall_ok else "ATTENTION"), now.strftime("%Y-%m-%d"))
    return subject, body, ntfy_one, overall_ok


# ---------------------------------------------------------------------------
# Delivery (reuses watchman env; same rules)
# ---------------------------------------------------------------------------
def send_ntfy(title_ascii, body):
    # ntfy title must be ASCII-only (emoji in header breaks it); emoji in body only.
    req = urllib.request.Request(
        NTFY_URL,
        data=body.encode("utf-8"),
        headers={"Title": title_ascii, "Priority": "default"},
    )
    urllib.request.urlopen(req, timeout=20).read()


def send_email(env, subject, body):
    host = env.get("WATCHDOG_SMTP_HOST", "smtp.gmail.com")
    port = int(env.get("WATCHDOG_SMTP_PORT", "587"))
    user = env.get("WATCHDOG_SMTP_USER", "")
    pw   = env.get("WATCHDOG_SMTP_PASS", "")
    to   = env.get("WATCHDOG_SMTP_TO", user)
    if not (user and pw):
        log("WARN SMTP creds missing in .env -- email skipped")
        return
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    s = smtplib.SMTP(host, port, timeout=30)
    try:
        s.starttls()
        s.login(user, pw)
        s.sendmail(user, [x.strip() for x in to.split(",")], msg.as_string())
    finally:
        s.quit()


def main():
    try:
        env = load_env(ENV_PATH)
        subject, body, ntfy_one, ok = build_report()

        # ntfy title = ASCII summary line (no emoji in header)
        ntfy_title = "Clinic health: %s" % ("OK" if ok else "ATTENTION")
        try:
            send_ntfy(ntfy_title, ntfy_one + "\n\n" + body)
        except Exception as e:
            log("WARN ntfy send failed: %s" % e)

        try:
            send_email(env, subject, body)
        except Exception as e:
            log("WARN email send failed: %s" % e)

        log("REPORT sent (%s)" % ("OK" if ok else "ATTENTION"))
    except Exception as e:
        # fail-loud: try to shout even if assembly broke
        log("ERROR health report crashed: %s" % e)
        try:
            urllib.request.urlopen(urllib.request.Request(
                NTFY_URL,
                data=("Clinic health report FAILED to run: %s" % e).encode("utf-8"),
                headers={"Title": "Clinic health report ERROR", "Priority": "high"},
            ), timeout=20).read()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
