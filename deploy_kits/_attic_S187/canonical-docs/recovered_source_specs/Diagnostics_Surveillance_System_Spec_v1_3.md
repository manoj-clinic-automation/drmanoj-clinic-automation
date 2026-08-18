# Diagnostics & Surveillance System Spec — v1.3 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward everything in v1.2 unchanged. Session 61 adds the **SECOND live check family** and the founding of the **VPS-native surveillance layer**: the service watchman. This promotes the diagnostics module from "one Apps Script sentinel" to "two complementary layers."

---

## §NEW — SECOND LIVE CHECK FAMILY: VPS SERVICE WATCHMAN (Category 1 — process liveness)

**File:** `clinic_watchdog.py` (on the VPS at `/root/wa/`; NOT Apps Script).
**Runner:** `clinic-watchdog.service` + `clinic-watchdog.timer` — **every 5 minutes**, `Persistent=true`.
**Answers:** "Are the clinic's always-on services actually running right now?"

**Detection:** `systemctl is-active <unit>` for each of the **nine always-on services**:
wa-receiver, wa-send-api, wa-notifier, call-api, call-hook, clinic-portal,
clinic-followup-receiver, attendance-dashboard, attlistener.
`active` = up. Anything else (or a probe error/timeout) = **down** (fail toward alerting).

**Deliberately excluded (Category 2 — freshness, not liveness):** the three timer jobs
`clinic-followup-push`, `call-recording-archive`, `call-transcription` are MEANT to be
`inactive dead` between runs; liveness-checking them would cry wolf. Their "did it run
on schedule?" check is the next planned build (see Growth path).

**Alert routing:** **ntfy phone-push** (clinic's existing private topic) **+ Gmail email**
(`WATCHDOG_SMTP_*` in `/root/wa/.env`, app-password masked) → drmka.ortho@gmail.com.
One alert names all newly-down services + the exact restart command for each.

**Behaviour / safety (all proven live 04 Jul 2026):**
- **Read-only** — reports only; never starts/stops/changes a service.
- **Anti-spam** — small state file (`/root/wa/watchdog_state.json`) remembers what's already
  been alerted; ONE alert per outage, not per run. One recovery note when a service returns.
- **Fail-loud** — if the watchman's own run errors, it attempts a "could not run" alert.
- **No patient data** — service names + up/down only. Plain log at `/root/wa/watchdog.log`.
- **Bug fixed before install:** emoji in the ntfy *title* HTTP header breaks the push
  (latin-1 codec) → title is now ASCII-safe; emoji kept in the UTF-8 body. Caught in offline
  behaviour-testing, which is why behaviour-tests matter beyond py_compile.

**Verified live:** all-9-healthy first auto-run logged 18:11 IST; deliberate `wa-notifier`
stop→detect→phone-buzz→restart test passed; test email delivered and owner-confirmed.

**Register entries added (per M6):**
- `VPS_SERVICE_DOWN` → detection: `systemctl is-active` every 5 min → ntfy+email naming the
  service + restart command → manual fix: `systemctl restart <service>`. Severity CRITICAL.
- `WATCHDOG_SELF_FAIL` → the watchman's own run errored → fail-loud alert. Severity CRITICAL.

## Two complementary layers now exist
- **VPS watchman** (this) — watches the box + its services (what only the VPS can see).
- **Apps Script sentinel** (v1.2, unchanged) — watches the Google Sheet's follow-up freshness.
Each watches what it can actually reach; neither duplicates the other.

## Growth path (next diagnostics sessions, one at a time)
1. **Timer-freshness** — did the three timer jobs actually run on schedule? (followup-push,
   recording-archive, transcription). `*_MISSED_RUN` codes.
2. **WhatsApp token-age** — warn 80 days, alert 90 (`WA_TOKEN_AGING`) — ties to the overdue rotation.
3. Then Patient_Master mirror freshness, Call_Feed freshness, revenue reconciler freshness.

## CHANGELOG
| v1.3 | 04 Jul 2026 (Session 61) | Second live check family: VPS service watchman (`clinic_watchdog.py`, 5-min timer, nine always-on services via `systemctl is-active`, ntfy+Gmail, read-only, anti-spam, fail-loud). Surveillance layer founded on the VPS. Register: `VPS_SERVICE_DOWN`, `WATCHDOG_SELF_FAIL`. Timer jobs excluded from liveness by design. |
| v1.2 | 03 Jul 2026 (Session 53) | First live check: `FOLLOWUPS_LIST_STALE` (`Diagnostics.gs::checkFollowupListFresh`). Diagnostics module founded. |
| v1.1 | (prior) | Fault codes, detection architecture, fallback protocols. |
