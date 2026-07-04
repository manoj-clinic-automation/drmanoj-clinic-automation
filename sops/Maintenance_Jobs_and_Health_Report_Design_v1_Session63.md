# Maintenance Jobs & Daily Health Report — Design (Deliverable 3)
## Advanced Orthopaedic Surgery Centre, Bareilly
**Drafted: Session 63 · 04 Jul 2026 · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Source of truth: Master KB v1.30 · Fault → Action Register v1 (S63) · Diagnostics Spec v1.4.**
**KB wins on any conflict. DESIGN DOCUMENT — nothing here is built or armed yet.**

> **What this is.** The plain-language design for the *preventive* half of the maintenance
> system: routine housekeeping jobs that keep the machine healthy (not just watched), and a
> once-a-day report so health is **positively confirmed**, not just "silence unless broken."
> Builds directly on the Fault → Action Register (the brain). Approve this → then code is
> built offline, tested, and installed with your OK.

---

## 1. Two gaps this closes

Your detection layers already answer *"is something broken right now?"* (watchman = liveness,
timer-freshness = did sleeping jobs run, sentinel = is the list fresh). Two things are still missing:

1. **Preventive upkeep** — nobody is pruning old logs, watching disk space, or confirming
   backups happened. These are the boring jobs that prevent a crisis rather than react to one.
2. **Positive confirmation** — today, no news is *assumed* to be good news. But "no alert"
   could also mean "the alerter itself died." A **daily health report** turns silence into a
   deliberate, visible *"checked everything at 8 AM — all green (or: here's what I did)."*

---

## 2. The maintenance jobs (four, all NEW)

Each is a small, scheduled VPS job. Lane assignments come straight from the register.

| Job | What it does | Fault code | Lane | Notes |
|---|---|---|---|---|
| **Disk-space check** | Reads free space on the VPS disk; warns before it's a crisis | `DISK_SPACE_LOW` | **ESCALATE-ONLY** | Warn at 80% used, alert at 90%. **Never auto-deletes** — you're told, you decide what goes. |
| **Log pruning** | Deletes app log files older than **30 days** (per your choice) | `LOG_ROTATION_OVERDUE` | **ASSISTED** (for now) | Starts assisted; promotes to Lane-1 AUTO later once the prune is proven idempotent. |
| **Backup-success check** | Confirms the expected cold-backup/exports actually happened recently | `BACKUP_MISSING` | **ESCALATE-ONLY** | A missing backup is never "auto-fixed" — you're alerted so you can act. |
| **WhatsApp token-age** | Tracks days since the WABA token was set; warns before 90 | `WA_TOKEN_AGING` | **ESCALATE-ONLY** | Warn 80d → alert 90d. Ties to the 🔴 overdue rotation. Follow `SOP_WhatsApp_Token.md` — HIGH RISK, Lokesh. |

**Important honesty flags (things to confirm before building each):**
- **Disk-space check** — safe and self-contained; can build immediately.
- **Log pruning** — I must first *find where the logs actually live and how big they get*
  before writing a deleter. We'll inspect, not assume. Deleting is the one action I treat
  with the most caution.
- **Backup-success check** — needs you to confirm **what "a backup" is and where it lands**
  (right now cold backups are an owner PC drag-drop to Drive — a VPS job can't see that). So
  this one may need a definition from you before it can check anything. Flagged, not assumed.
- **Token-age** — needs a **known "token set on" date** to count from. If we don't have one
  recorded, the first run establishes a baseline ("assume set today unless told otherwise")
  and counts forward. Honest limitation, stated up front.

---

## 3. The daily health report (NEW — the positive-confirmation piece)

**When:** ~**08:00 IST**, every day (after the overnight 2 AM / 3 AM / 7 AM jobs have run).
**Channels:** **both** — a one-line **ntfy** push to your phone + a **Gmail** email with detail.

**What the email contains (a single glanceable status):**
```
CLINIC HEALTH REPORT — <date> 08:00 IST

OVERALL: ✅ ALL GREEN   (or ⚠️ ATTENTION NEEDED)

SERVICES (9 always-on)........ ✅ all active
TIMER JOBS (3)................ ✅ all ran on schedule
  · followup-push  last run <time>
  · recording-archive last run <time>
  · transcription  last run <time>
FOLLOW-UP LIST................ ✅ fresh (<n> rows today)
DISK SPACE.................... ✅ 42% used
LOGS......................... ✅ pruned (kept 30d) / — nothing to prune
BACKUP....................... ✅ last backup <date>   (or ⚠️ none in Nd)
WA TOKEN AGE................. ✅ 34 days   (or ⚠️ 82 days — plan rotation)

ACTIONS TAKEN IN LAST 24H:
  · <time> restarted wa-receiver (was down) — recovered ✅
  · (or: none)

ANYTHING NEEDING YOU:
  · (nothing)   or   · <fault> — see procedure <name>
```
The **ntfy one-liner** is just the OVERALL line: `✅ Clinic all green` or
`⚠️ Clinic: 1 item needs you — check email`.

**Why this matters:** if the report *doesn't arrive* one morning, that itself is a signal
(the reporter died / the box is down) — so its absence is informative. That's the
positive-confirmation property you asked for.

---

## 4. How it all fits together (sturdiness recap)

- **Detection** stays as-is: watchman (liveness) + timer-freshness (freshness) + sentinel (list).
- **Lane-1 auto-fix** stays as-is: the **watchman IS the service responder** (your (A) decision) —
  we are NOT building a second restarter.
- **New this deliverable:** the four maintenance jobs above + the daily report that *summarises*
  everything (detection results + any auto-fixes the watchman did + maintenance job results).
- **Same DNA throughout:** read-only except where explicitly whitelisted; the only new job that
  *deletes* anything is log-pruning, and it starts ASSISTED (alert-only) until proven; fail-loud;
  anti-spam; plain logs; no PHI, no panel, no token actions ever automated.

---

## 5. Proposed build order (each its own confirmed step, offline-tested first)

1. **The daily health report FIRST** — because it's *read-only* (it only summarises what the
   other layers already know) and delivers visible value immediately. Lowest risk, highest
   daily benefit. It reads: `systemctl is-active` for the 9, the 3 heartbeat files, disk %,
   the follow-up heartbeat/list, and the watchman's action log.
2. **Disk-space check** — small, self-contained, ESCALATE-ONLY.
3. **Token-age check** — small; needs the baseline-date decision.
4. **Log pruning** — LAST, after we *inspect* where logs live and how big they get. The one
   with a delete action; treated most carefully; stays ASSISTED at first.
5. **Backup-success check** — needs your definition of "what/where is a backup" first; may be
   deferred until that's settled.

---

## 6. What I need from you to start building (after you approve this design)

- **Approve the design** (or adjust §2/§3).
- Confirm build order §5 (or reorder).
- The one real input I'll need for the report build: nothing — it's read-only and I have all
  the paths from the KB. So on approval I can build **step 1 (the daily report)** straight away,
  offline, `py_compile`-clean, for you to install.

---

*Nothing here is live. On approval this becomes the build plan; a copy goes to Notion "Clinic
HQ" + the handoff kit. Report timing 08:00 IST, both channels, 30-day log retention — locked
per owner, Session 63.*
