# Diagnostics & Surveillance System Spec — v1.4 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward everything in v1.3 unchanged. Session 62 adds the
> **timer-freshness check family (Category 2 — freshness, not liveness)** — the deliberate
> next step named in v1.3's growth path. The heartbeat mechanism is INSTALLED live on the
> three timer jobs; the checker is BUILT and behaviour-verified but **armed the following
> session** (so its first run reads real heartbeats, not empties).

---

## §NEW — TIMER-FRESHNESS CHECK FAMILY (Category 2 — did the sleeping jobs run?)

**The gap this closes.** The S61 watchman checks liveness of the nine always-on services and
deliberately excludes the three timer jobs (`clinic-followup-push`, `call-recording-archive`,
`call-transcription`) because they are MEANT to be `inactive dead` between runs. But a timer
job can fail to *wake* — and nothing would report it. Example: the 07:00 follow-up push
silently misses → the day's list never lands → discovered only when staff hit an empty list.

**The question this family answers:** *"Did each timer job actually RUN when it was supposed to?"*

### Detection method — heartbeat files (NOT systemd's own record)
On this box, both systemd-native "last run" sources are **blank**: `systemctl list-timers`'
`LAST` column and the service's `ExecMainExitTimestamp` are wiped by reboots / unit reloads.
A checker reading them would false-alarm on every reboot. **Ruled out.**

Chosen instead: each timer job leaves a **heartbeat** when it finishes. One line appended to
each *service* unit (job Python code untouched):
```
ExecStartPost=/bin/sh -c 'date -u +%%Y-%%m-%%dT%%H:%%M:%%SZ > /root/wa/heartbeats/<name>.hb'
```
`ExecStartPost` runs only after `ExecStart` completes (guaranteed for `Type=oneshot`), so a
heartbeat means the job reached the end. `%` doubled to `%%` (unit-file escaping). Files:
`followup-push.hb`, `recording-archive.hb`, `transcription.hb` in `/root/wa/heartbeats/`.

### The checker — `clinic_timer_freshness.py` (`/root/wa/`)
Reads the three heartbeat files; for each job compares "last ran" to its schedule + **2 hr
grace**; alerts if overdue or the heartbeat is missing (never ran).

- `clinic-followup-push` — slots 22:00 / 07:00 / 11:00 IST; overdue = last run older than the
  most recent passed slot + 2 h.
- `call-recording-archive` — slot 02:00; overdue = last run older than ~26 h.
- `call-transcription` — slot 03:00; overdue = last run older than ~26 h.

**Same DNA as the watchman:** ntfy phone-push + Gmail email (`WATCHDOG_SMTP_*`, ntfy topic
`drmka-yfv80gjcixa643`); **read-only** (reads heartbeat files only); **anti-spam**
(`/root/wa/timer_freshness_state.json` — ONE alert per outage, recovery note on return);
**fail-loud** (own-run error → shout); **no patient data** (job names + timestamps only);
plain log at `/root/wa/timer_freshness.log`. Runner (armed next session):
`clinic-timer-freshness.timer` hourly (`*:05:00`, Persistent) → `.service` (oneshot).

**Offline behaviour-verified (5/5 before any install):** all-fresh→silent; one stale→one
alert; still-stale→no repeat (anti-spam); ran-again→recovery; missing file→alert.

**Deliberate two-phase rollout (fact worth keeping):** heartbeats installed one session,
checker armed the next — because arming before all three jobs have left a first heartbeat
would fire correct-but-false "missed run" alerts for jobs that simply haven't reached their
run time yet. Let the natural overnight runs seed the heartbeats first.

### Register entries added (per M6)
- `FOLLOWUPS_PUSH_MISSED_RUN` → follow-up push missed a scheduled slot (+2 h grace) → ntfy+email + `systemctl start clinic-followup-push.service`. Severity CRITICAL (empties the day's list).
- `RECORDING_ARCHIVE_MISSED_RUN` → 2 AM archive didn't run in ~26 h → alert + `systemctl start call-recording-archive.service`. Severity WARNING.
- `TRANSCRIPTION_MISSED_RUN` → 3 AM transcription didn't run in ~26 h → alert + `systemctl start call-transcription.service`. Severity WARNING.

## Three complementary layers now exist
- **VPS watchman** (S61) — always-on service *liveness* (`systemctl is-active`, every 5 min).
- **VPS timer-freshness** (this, S62) — sleeping-job *freshness* (heartbeat files, hourly).
- **Apps Script sentinel** (v1.2) — Google Sheet follow-up-list freshness (2–3 PM daily).

## Growth path (next diagnostics sessions, one at a time)
1. **WhatsApp token-age** — warn 80 days, alert 90 (`WA_TOKEN_AGING`) — ties to the overdue rotation.
2. Then Patient_Master mirror freshness, Call_Feed freshness, revenue reconciler freshness.

## CHANGELOG
| v1.4 | 04 Jul 2026 (Session 62) | Timer-freshness family (Category 2). Heartbeat mechanism installed live on all three timer jobs via `ExecStartPost` (job code untouched); systemd-native last-run reading ruled out (blank on this box). Checker `clinic_timer_freshness.py` built + 5/5 behaviour-verified; armed next session (two-phase rollout). Register: `FOLLOWUPS_PUSH_MISSED_RUN`, `RECORDING_ARCHIVE_MISSED_RUN`, `TRANSCRIPTION_MISSED_RUN`. Three surveillance layers now. |
| v1.3 | 04 Jul 2026 (Session 61) | Second live check family: VPS service watchman. |
| v1.2 | 03 Jul 2026 (Session 53) | First live check: `FOLLOWUPS_LIST_STALE`. Diagnostics module founded. |
| v1.1 | (prior) | Fault codes, detection architecture, fallback protocols. |
