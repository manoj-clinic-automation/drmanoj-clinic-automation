#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clinic_watchdog.py  —  The VPS "night-watchman"
Dr. Manoj Agarwal Clinic · Bareilly · Session 61 (Goal 2, Diagnostics/Surveillance)

WHAT IT DOES (plain language)
  Every time it runs, it asks Linux directly whether each of the clinic's
  ALWAYS-ON services is still running. If all are healthy it stays silent.
  If any has stopped, it sends ONE phone-push (ntfy) + ONE email naming the
  service(s) that went down and the exact command to bring each back. When a
  down service recovers, it sends one "recovered" note. It NEVER starts, stops
  or changes any service — it only reads status. If the watchman itself hits an
  error, it tries to alert that it could not run (a silent guard is worse than none).

SAFETY
  - Read-only. Uses `systemctl is-active <svc>` only. Cannot break anything.
  - Anti-spam: remembers what it already alerted about (a small state file) so it
    warns ONCE per outage, not every run. Sends a recovery note once, then resets.
  - Fail-loud: if the run itself errors, it attempts a "watchman could not run" alert.
  - No patient data ever touched or logged. Service names + up/down only.

FIRST PASS SCOPE (Session 61)
  Liveness only, for the nine always-on services confirmed live on the server.
  The three TIMER jobs (clinic-followup-push, call-recording-archive,
  call-transcription) are deliberately NOT liveness-checked here — they are
  MEANT to be asleep ("inactive dead") between runs, so checking them for
  "running" would cry wolf. Their "did it run recently?" check is a later step.

RUN
  Preview / one-off (safe, from the VPS):
    /root/wa/venv/bin/python3 /root/wa/clinic_watchdog.py
  It is meant to be run every few minutes by its own systemd timer (installed
  in a later step). Runs fine on plain python3 too — no gspread needed.
"""

import os
import sys
import json
import time
import smtplib
import subprocess
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText

# ----------------------------------------------------------------------------
# CONFIG — the nine ALWAYS-ON services the watchman guards.
# Each entry: the systemd unit name, a plain-English label, and the one-line
# command the owner (or Claude) uses to bring it back if it is down.
# This list was built from the server's own `systemctl` output (Session 61),
# NOT from memory. Timer jobs are intentionally excluded (see note above).
# ----------------------------------------------------------------------------
SERVICES = [
    ("wa-receiver.service",              "WhatsApp inbound receiver",        "systemctl restart wa-receiver"),
    ("wa-send-api.service",              "WhatsApp send relay (Reply box)",  "systemctl restart wa-send-api"),
    ("wa-notifier.service",              "WhatsApp -> phone notifier",       "systemctl restart wa-notifier"),
    ("call-api.service",                 "Click-to-call relay",              "systemctl restart call-api"),
    ("call-hook.service",                "Call-outcome webhook capture",     "systemctl restart call-hook"),
    ("clinic-portal.service",            "Clinic launcher portal",           "systemctl restart clinic-portal"),
    ("clinic-followup-receiver.service", "Follow-up workbook receiver",      "systemctl restart clinic-followup-receiver"),
    ("attendance-dashboard.service",     "Attendance dashboard (web view)",  "systemctl restart attendance-dashboard"),
    ("attlistener.service",              "Attendance device capture",        "systemctl restart attlistener"),
]

# Where the watchman keeps its small memory of what it already alerted about,
# and its plain log. Both are harmless text files. No secrets, no patient data.
STATE_FILE = os.environ.get("WATCHDOG_STATE_FILE", "/root/wa/watchdog_state.json")
LOG_FILE   = os.environ.get("WATCHDOG_LOG_FILE",   "/root/wa/watchdog.log")

# Alert routing.
# ntfy: reuse the clinic's existing private topic (already on the owner's phone).
NTFY_TOPIC_URL = os.environ.get("WATCHDOG_NTFY_URL", "https://ntfy.sh/drmka-yfv80gjcixa643")
# email: goes to the clinic Google account. SMTP settings are read from the
# environment if present; if email cannot be sent, ntfy still fires (never both fail silently).
ALERT_EMAIL_TO = os.environ.get("WATCHDOG_EMAIL_TO", "drmka.ortho@gmail.com")
SMTP_HOST = os.environ.get("WATCHDOG_SMTP_HOST", "")   # e.g. smtp.gmail.com
SMTP_PORT = int(os.environ.get("WATCHDOG_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("WATCHDOG_SMTP_USER", "")
SMTP_PASS = os.environ.get("WATCHDOG_SMTP_PASS", "")   # app password, from .env only
SMTP_FROM = os.environ.get("WATCHDOG_SMTP_FROM", SMTP_USER or ALERT_EMAIL_TO)


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(line):
    """Append one line to the plain log. Never raises."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("[%s] %s\n" % (now_str(), line))
    except Exception:
        pass  # logging must never break the watchman


def is_active(unit):
    """
    Ask Linux directly: is this service running?
    Returns True only if systemctl reports exactly 'active'.
    Any error / timeout counts as NOT active (fail toward alerting, which is
    the safe direction for a watchman).
    """
    try:
        out = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True, text=True, timeout=15,
        )
        return out.stdout.strip() == "active"
    except Exception:
        return False


def load_state():
    """Load the small memory of services we've already alerted are DOWN."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # stored as a list; return as a set of unit names currently in 'alerted-down'
            return set(data.get("down_alerted", []))
    except Exception:
        return set()


def save_state(down_alerted):
    """Persist the memory. Never raises (best-effort)."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"down_alerted": sorted(down_alerted),
                       "updated": now_str()}, f, indent=2)
    except Exception as e:
        log("WARN could not write state file: %s" % e)


def _ascii_header(text):
    """
    ntfy sends the Title/Tags as HTTP headers, which must be latin-1/ASCII-safe.
    Emojis in the title would raise a codec error and the push would silently
    fail (the worst outcome for a watchman). So we strip the title to plain ASCII
    here; the emoji still appears in the message BODY, which is UTF-8 and fine.
    """
    try:
        return text.encode("ascii", "ignore").decode("ascii").strip() or "Clinic watchman"
    except Exception:
        return "Clinic watchman"


def send_ntfy(title, body, priority="urgent"):
    """Phone-push via ntfy. Best-effort; returns True/False."""
    try:
        req = urllib.request.Request(
            NTFY_TOPIC_URL,
            data=body.encode("utf-8"),
            headers={
                "Title": _ascii_header(title),   # ASCII-safe: no emoji in header
                "Priority": priority,
                "Tags": "rotating_light",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=15)
        return True
    except Exception as e:
        log("WARN ntfy send failed: %s" % e)
        return False


def send_email(subject, body):
    """
    Email via SMTP if SMTP settings are present. Best-effort; returns True/False.
    If SMTP is not configured, we skip email quietly (ntfy is the primary channel)
    and note it in the log — the watchman still works.
    """
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        log("INFO email skipped (SMTP not configured in .env); ntfy is primary")
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = ALERT_EMAIL_TO
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_FROM, [ALERT_EMAIL_TO], msg.as_string())
        return True
    except Exception as e:
        log("WARN email send failed: %s" % e)
        return False


def alert(title, body):
    """Fire both channels. Returns a small dict of what succeeded."""
    ok_ntfy = send_ntfy(title, body)
    ok_mail = send_email(title, body)
    log("ALERT sent | ntfy=%s email=%s | %s" % (ok_ntfy, ok_mail, title))
    return {"ntfy": ok_ntfy, "email": ok_mail}


# ----------------------------------------------------------------------------
# main run
# ----------------------------------------------------------------------------
def run():
    label_by_unit = {u: lbl for (u, lbl, _cmd) in SERVICES}
    cmd_by_unit   = {u: cmd for (u, _lbl, cmd) in SERVICES}

    down_now = []
    for unit, _lbl, _cmd in SERVICES:
        if not is_active(unit):
            down_now.append(unit)

    already = load_state()          # services we previously alerted as down
    down_set = set(down_now)

    newly_down = down_set - already      # broke since last run  -> alert
    recovered  = already - down_set      # came back since last run -> recovery note

    # --- newly down: one alert naming all of them + their fix commands ---
    if newly_down:
        lines = ["\u26A0\uFE0F CLINIC SERVER: one or more services have STOPPED.\n"]
        for unit in sorted(newly_down):
            lines.append("\u2022 %s (%s) is DOWN" % (label_by_unit.get(unit, unit), unit))
            lines.append("   Fix: %s" % cmd_by_unit.get(unit, "systemctl restart " + unit.replace(".service", "")))
            lines.append("")
        lines.append("Time: %s IST" % now_str())
        lines.append("(The watchman only reports; it does not restart anything.)")
        body = "\n".join(lines)
        alert("\u26A0\uFE0F Clinic server: service DOWN", body)

    # --- recovered: one reassurance note ---
    if recovered:
        lines = ["\u2705 CLINIC SERVER: service(s) back to normal.\n"]
        for unit in sorted(recovered):
            lines.append("\u2022 %s (%s) is RUNNING again" % (label_by_unit.get(unit, unit), unit))
        lines.append("")
        lines.append("Time: %s IST" % now_str())
        body = "\n".join(lines)
        alert("\u2705 Clinic server: service recovered", body)

    # persist the new "currently alerted-down" memory
    save_state(down_set)

    # quiet heartbeat line to the log so we can see it's been running
    if down_now:
        log("CHECK %d/%d up | DOWN: %s" %
            (len(SERVICES) - len(down_now), len(SERVICES), ", ".join(sorted(down_now))))
    else:
        log("CHECK all %d services healthy" % len(SERVICES))

    # console summary (handy when run by hand)
    print("=== Clinic watchman — %s ===" % now_str())
    for unit, lbl, _cmd in SERVICES:
        state = "DOWN" if unit in down_set else "up"
        mark = "\u274C" if unit in down_set else "\u2705"
        print("  %s %-34s %s (%s)" % (mark, unit, state, lbl))
    print("---")
    if newly_down:
        print("  -> ALERT fired for newly-down: %s" % ", ".join(sorted(newly_down)))
    if recovered:
        print("  -> RECOVERY note fired for: %s" % ", ".join(sorted(recovered)))
    if not newly_down and not recovered:
        print("  -> no change since last check; no alert sent")
    return 0


def main():
    try:
        return run()
    except Exception as e:
        # fail-loud: try to shout that the watchman itself could not run
        try:
            send_ntfy("\u26A0\uFE0F Clinic watchman could NOT run",
                      "The server watchman hit an error and could not complete a check.\n"
                      "Error: %s\nTime: %s" % (e, now_str()),
                      priority="high")
        except Exception:
            pass
        log("FATAL watchman run failed: %s" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
