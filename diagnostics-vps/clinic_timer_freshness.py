#!/root/wa/venv/bin/python3
# -*- coding: utf-8 -*-
"""
clinic_timer_freshness.py  --  Diagnostics step 2 (Session 62)
Dr. Manoj Agarwal Clinic, Bareilly.

WHAT THIS DOES (plain language):
The Session-61 watchman checks whether always-on services are RUNNING.
It deliberately ignores the three TIMER jobs, because those are meant to
sleep between runs -- so "is it running?" is the wrong question for them.

This script asks the RIGHT question for the sleeping jobs:
    "Did each timer job actually RUN when it was supposed to?"

It does NOT read systemd's own last-run time (that field is blank on this
box and gets wiped by reboots). Instead each job leaves a tiny heartbeat
file when it finishes; this script reads those files and alerts if a job
is overdue past its schedule + a grace window.

SAFETY (same DNA as the watchman):
  - READ-ONLY: reads heartbeat files only; never starts/stops/edits anything.
  - ANTI-SPAM: a state file remembers what's already been alerted, so a
    stuck job produces ONE alert, not one every run. Recovery note when fixed.
  - FAIL-LOUD: if this script's own run errors, it tries to shout about it.
  - NO PATIENT DATA: job names + timestamps only.
"""

import os
import sys
import json
import time
import ssl
import smtplib
import traceback
import urllib.request
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta

# ---- fixed facts about this box -------------------------------------------
ENV_PATH        = "/root/wa/.env"
HEARTBEAT_DIR   = "/root/wa/heartbeats"
STATE_PATH      = "/root/wa/timer_freshness_state.json"
LOG_PATH        = "/root/wa/timer_freshness.log"
NTFY_URL        = "https://ntfy.sh/drmka-yfv80gjcixa643"

IST = timezone(timedelta(hours=5, minutes=30))   # VPS clock is IST
GRACE = timedelta(hours=2)                        # slack past a scheduled slot

# ---- the three sleeping jobs we watch -------------------------------------
# schedule = list of (hour, minute) IST slots the job is supposed to run at.
# We judge each job by its MOST RECENT slot that has already passed today
# (or yesterday's last slot, if none has passed yet today).
JOBS = [
    {
        "code": "FOLLOWUPS_PUSH_MISSED_RUN",
        "label": "Follow-up push",
        "hb": os.path.join(HEARTBEAT_DIR, "followup-push.hb"),
        "restart": "systemctl start clinic-followup-push.service",
        "slots": [(22, 0), (7, 0), (11, 0)],
    },
    {
        "code": "RECORDING_ARCHIVE_MISSED_RUN",
        "label": "Call-recording archive",
        "hb": os.path.join(HEARTBEAT_DIR, "recording-archive.hb"),
        "restart": "systemctl start call-recording-archive.service",
        "slots": [(2, 0)],
    },
    {
        "code": "TRANSCRIPTION_MISSED_RUN",
        "label": "Call transcription",
        "hb": os.path.join(HEARTBEAT_DIR, "transcription.hb"),
        "restart": "systemctl start call-transcription.service",
        "slots": [(3, 0)],
    },
]


def log(msg):
    line = "%s  %s" % (datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"), msg)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


def load_env(path):
    env = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw or raw.startswith("#") or "=" not in raw:
                    continue
                k, v = raw.split("=", 1)
                env[k.strip()] = v.strip()
    except Exception as e:
        log("WARN could not read env: %s" % e)
    return env


def load_state():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"alerted": []}


def save_state(state):
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception as e:
        log("WARN could not write state: %s" % e)


def most_recent_slot(slots, now):
    """Return the datetime of the most recent scheduled slot at or before now."""
    candidates = []
    for days_back in (0, 1):
        day = (now - timedelta(days=days_back)).date()
        for (hh, mm) in slots:
            dt = datetime(day.year, day.month, day.day, hh, mm, tzinfo=IST)
            if dt <= now:
                candidates.append(dt)
    return max(candidates) if candidates else None


def read_heartbeat(path):
    """Return the heartbeat's UTC datetime, or None if missing/unreadable."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        # format written by `date -u +%Y-%m-%dT%H:%M:%SZ`
        dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def send_ntfy(title_ascii, body):
    # title goes in an HTTP header -> MUST be ASCII (emoji breaks it).
    req = urllib.request.Request(
        NTFY_URL,
        data=body.encode("utf-8"),
        headers={"Title": title_ascii, "Priority": "high"},
        method="POST",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        return r.status


def send_email(env, subject, body):
    host = env.get("WATCHDOG_SMTP_HOST")
    port = int(env.get("WATCHDOG_SMTP_PORT", "587"))
    user = env.get("WATCHDOG_SMTP_USER")
    pw   = env.get("WATCHDOG_SMTP_PASS")
    frm  = env.get("WATCHDOG_SMTP_FROM")
    to   = env.get("WATCHDOG_EMAIL_TO", "drmka.ortho@gmail.com")
    if not (host and user and pw and frm):
        log("WARN email not configured; skipping email")
        return
    m = MIMEText(body, "plain", "utf-8")
    m["Subject"] = subject
    m["From"] = frm
    m["To"] = to
    s = smtplib.SMTP(host, port, timeout=30)
    s.starttls()
    s.login(user, pw)
    s.sendmail(frm, [to], m.as_string())
    s.quit()


def alert(env, down):
    """down = list of dicts describing each overdue job."""
    lines = []
    for d in down:
        lines.append(
            "- %s [%s]\n    expected by: %s\n    last ran:    %s\n    fix: %s"
            % (d["label"], d["code"], d["due_str"], d["last_str"], d["restart"])
        )
    body = ("A scheduled clinic job did not run on time.\n\n"
            + "\n".join(lines)
            + "\n\nThis is the timer-freshness checker (Session 62).")
    title = "Clinic timer-freshness: %d job(s) overdue" % len(down)
    try:
        send_ntfy(title, "\u26a0\ufe0f " + body)  # emoji only in body
    except Exception as e:
        log("WARN ntfy failed: %s" % e)
    try:
        send_email(env, title, body)
    except Exception as e:
        log("WARN email failed: %s" % e)


def recovery(env, recovered_labels):
    body = ("Recovered: %s ran again and is now on schedule."
            % ", ".join(recovered_labels))
    try:
        send_ntfy("Clinic timer-freshness: recovered", "\u2705 " + body)
    except Exception as e:
        log("WARN ntfy recovery failed: %s" % e)
    try:
        send_email(env, "Clinic timer-freshness: recovered", body)
    except Exception as e:
        log("WARN email recovery failed: %s" % e)


def main():
    env = load_env(ENV_PATH)
    state = load_state()
    already = set(state.get("alerted", []))
    now = datetime.now(IST)

    overdue = []
    healthy_codes = set()

    for job in JOBS:
        due = most_recent_slot(job["slots"], now)
        if due is None:
            healthy_codes.add(job["code"])
            continue
        deadline = due + GRACE
        hb = read_heartbeat(job["hb"])
        last_str = (hb.astimezone(IST).strftime("%Y-%m-%d %H:%M IST")
                    if hb else "never (no heartbeat file)")
        # Overdue if: past the grace deadline AND the last run is older than
        # this slot (i.e. the job hasn't run for the slot we're judging).
        if now > deadline and (hb is None or hb < due):
            overdue.append({
                "code": job["code"],
                "label": job["label"],
                "restart": job["restart"],
                "due_str": due.strftime("%Y-%m-%d %H:%M IST"),
                "last_str": last_str,
            })
        else:
            healthy_codes.add(job["code"])

    # anti-spam: only alert on NEWLY-overdue jobs
    new_down = [d for d in overdue if d["code"] not in already]
    now_down_codes = set(d["code"] for d in overdue)
    recovered = [c for c in already if c in healthy_codes]

    if new_down:
        alert(env, new_down)
        log("ALERT overdue: %s" % ", ".join(d["code"] for d in new_down))

    if recovered:
        labels = [j["label"] for j in JOBS if j["code"] in recovered]
        recovery(env, labels)
        log("RECOVERY: %s" % ", ".join(recovered))

    if not overdue and not recovered:
        log("CHECK all %d timer jobs fresh" % len(JOBS))

    state["alerted"] = sorted(now_down_codes)
    save_state(state)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write("SELF-FAIL\n" + err + "\n")
        except Exception:
            pass
        # fail-loud: try to shout even if the main run broke
        try:
            req = urllib.request.Request(
                NTFY_URL,
                data=("timer-freshness checker crashed:\n" + err[:800]).encode("utf-8"),
                headers={"Title": "Clinic timer-freshness SELF-FAIL", "Priority": "high"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context())
        except Exception:
            pass
        sys.exit(1)
