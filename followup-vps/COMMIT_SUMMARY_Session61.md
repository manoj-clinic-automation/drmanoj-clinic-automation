# GitHub Commit Summary — Session 61 (04 Jul 2026)
## Goal 2 founding piece: VPS service watchman (diagnostics/surveillance)

**Repo:** drmanoj-clinic-automation · branch `main`
**Suggested location:** new folder `diagnostics-vps/` (or reuse `followup-vps/`)
**Author:** Dr. Manoj Agarwal (with Claude)

---

## What this commit adds
A VPS-native "night-watchman" that checks the nine ALWAYS-ON clinic services
every 5 minutes and alerts (ntfy phone-push + Gmail email) the moment any stops.
Read-only: it never starts/stops/changes any service. Founding piece of the
Diagnostics/Surveillance layer (Goal 2). The existing Apps Script follow-up
stale-list sentinel is untouched and remains the sheet-side check.

## Files in this commit
| File | Installed location on VPS | md5 |
|---|---|---|
| `clinic_watchdog.py` | `/root/wa/clinic_watchdog.py` | 03c39232231a7471270e76b67d8e3d86 |
| `clinic-watchdog.service` | `/etc/systemd/system/clinic-watchdog.service` | b3021bd1afa2d5a3f82a6c15b5cfac7a |
| `clinic-watchdog.timer` | `/etc/systemd/system/clinic-watchdog.timer` | 0428e045ecc97b4d3fe12f1a12f84937 |

## Services watched (nine always-on)
wa-receiver, wa-send-api, wa-notifier, call-api, call-hook, clinic-portal,
clinic-followup-receiver, attendance-dashboard, attlistener.

## Deliberately NOT liveness-watched (timer jobs — meant to be asleep)
clinic-followup-push, call-recording-archive, call-transcription.
(Their "did it run recently?" check is a later step, not this commit.)

## Behaviour (all proven live this session)
- All healthy -> silent (one quiet log line only).
- Newly down -> ONE alert naming service(s) + the exact restart command.
- Anti-spam -> will not re-alert every run for the same outage.
- Recovery -> one "back to normal" note when a down service returns.
- Fail-loud -> if the watchman itself errors, it tries to alert it could not run.

## Alert channels
- ntfy phone-push: reuses the clinic's existing private topic.
- Gmail email: drmka.ortho@gmail.com via SMTP app-password (in /root/wa/.env only).

## SECRETS — DO NOT COMMIT
- `/root/wa/.env` is gitignored and stays on the VPS only. It now also holds:
  WATCHDOG_SMTP_HOST/PORT/USER/PASS/FROM/EMAIL_TO (Gmail app-password masked).
- No token, password, or patient data appears in any committed file.

## Schedule
systemd timer: first run 2 min after boot, then every 5 minutes, Persistent=true.

## Manual fallback (unchanged philosophy)
Run by hand any time:  cd /root/wa && /root/wa/venv/bin/python3 clinic_watchdog.py
