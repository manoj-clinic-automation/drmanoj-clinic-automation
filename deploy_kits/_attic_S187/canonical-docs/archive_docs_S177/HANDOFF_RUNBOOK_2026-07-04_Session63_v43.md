# HANDOFF RUNBOOK — 2026-07-04 · Session 63 · v43

**Dr. Manoj Agarwal Clinic · Bareilly.** Read the KB (**v1.31**) + this runbook at session start.
**KB wins on any conflict.** This runbook = exactly where we stopped.

---

## §0 — WHAT HAPPENED THIS SESSION (Session 63)

**Goal: build the owner-requested "automated, monitored, reported maintenance" system + clear
per-fault procedures. We DESIGNED the whole thing safely and SHIPPED the first, lowest-risk
piece. Code changed on the VPS (a new read-only report job + its 8 AM timer). Full EOS.**

Three things came out of this session:

1. **Maintenance SOP library drafted** (documentation) — six real SOPs + one honest stub, in
   the exact shape the Maintenance_SOP_Spec requires. Files: `SOP_VPS_Services`,
   `SOP_Dashboard_AppScript`, `SOP_WhatsApp_Token` (HIGH RISK — Lokesh), `SOP_FollowUp_Tracker`,
   `SOP_MyOperator_IVR`, `SOP_Biometric_Attendance`, and `SOP_Revenue_Reconciler` (**STUB** —
   the reconciler's live status isn't confirmed in the KB, so it was NOT faked). Per spec M3,
   Drive is the master copy — owner drag-drops these into `Clinic Automation / SOPs /`.

2. **The automated-maintenance design — agreed and locked (D112–D114).** A **hybrid two-lane**
   responder:
   - **Lane 1 = NARROW-AUTO** (system fixes it itself), started deliberately TINY — only two
     proven-safe, idempotent actions: restart a dead always-on service; re-run the follow-up push.
   - **Lane 2 = ASSISTED** (Option 2a) — for everything else the background program only
     *detects + escalates*; the stepwise fixer is Claude in a confirmation-gated session,
     scripted by the register (exactly like a build session). This keeps the code that *acts*
     on the live clinic as small as possible.
   - **The S61 watchman IS the Lane-1 service responder** — we do NOT build a second restarter.
   - The **Fault → Action Register v1** is the single brain: every fault → lane → exact steps.

3. **The daily health report — BUILT, INSTALLED, LIVE-VERIFIED, ARMED (D115).** A **read-only**
   job that takes no action — it only summarises what the watchman/heartbeats/disk already
   know, and sends one digest at **08:00 IST** on **both ntfy + Gmail**. Confirmed: hand-run
   fired both channels; 8 AM timer enabled; `list-timers` shows correct NEXT = next 08:00 IST;
   box confirmed `Asia/Kolkata` so 08:00 = real 8 AM.

**Why the report first:** it's read-only (lowest possible risk), and it delivers visible value
every single morning. It also gives *positive* confirmation — health is no longer "silence =
good"; if the 08:00 report doesn't arrive, that absence is itself the alarm.

---

## §1 — CURRENT LIVE STATE (one-liners)

- **Daily health report: LIVE + self-firing 08:00 IST.** `clinic_health_report.py` + `clinic-health-report.timer` on the VPS. Read-only, both channels, reuses watchman `.env`.
- **Timer-freshness CHECKER: still built + tested, STILL NOT ARMED.** Unchanged from S62. Arming is next session's FIRST task (needs the 3 heartbeats seeded overnight first).
- **Timer-freshness heartbeats: LIVE** on all three timer jobs (followup-push proven; the two overnight seed at 2 AM / 3 AM).
- **VPS service watchman (S61): LIVE** — every 5 min, nine services, ntfy+Gmail, read-only, anti-spam, recovery, fail-loud. **This IS the Lane-1 service responder (D113).**
- **Follow-up push (S60): VPS-native**, timers 22:00/07:00/11:00 IST.
- **Attendance (S59): live.** **Dashboard v18.18 LIVE.**
- **VPS timers now (5):** clinic-followup-push, call-recording-archive, call-transcription, clinic-watchdog (every 5 min), **clinic-health-report (NEW, 08:00)**.
- Key rotation 🔴 overdue (Lokesh); AKEY_14 flagged; PHI base swap deferred.

---

## §2 — BACKLOG (next session picks from here)

**TOMORROW — FIRST TASK (the S62 parked step, still #1):**
1. **Arm the timer-freshness checker.** Prereq: `cat /root/wa/heartbeats/*.hb` shows **three**
   recent timestamps (followup-push + the two overnight, now seeded). Then one step at a time:
   upload `clinic_timer_freshness.py` (md5 `21deacf639c1e40eed6ebad81bd46b6d`, WinSCP + md5 +
   `py_compile` gate) → run by hand (expect `all 3 timer jobs fresh`, silent) → install
   `clinic-timer-freshness.service` + `.timer` → `daemon-reload` → `enable --now` → confirm
   `active (waiting)` → one live missed-run proof (age a heartbeat → run by hand → phone+email
   fire → restore). **Same step: decide whether to switch `FOLLOWUPS_PUSH_MISSED_RUN` from
   alert-only to AUTO→ESC**, which adds the Lane-1 push re-run (per D112).

**Then — deliverable 3 (maintenance jobs), in this order:**
2. **Disk-space check** — small, self-contained, ESCALATE-ONLY (`DISK_SPACE_LOW`, warn 80/crit 90). Feeds the report.
3. **WhatsApp token-age check** — ESCALATE-ONLY (`WA_TOKEN_AGING`, warn 80/alert 90). **Needs a "token set-on" baseline date** — establish one first. Ties to 🔴 rotation.
4. **Log-pruning** — LAST of the jobs. **Inspect where logs live + how big first** (it's the one DELETE action). 30-day retention. Starts ASSISTED; promote to Lane-1 AUTO only after proven idempotent.
5. **Backup-success check** — BLOCKED until owner defines a **box-verifiable** backup (current cold backup is owner-PC→Drive, invisible to the VPS). Design a VPS-visible backup drop first, or defer.

**Then, roughly in priority:**
6. **Verify & close "Agent shows as Staff."**
7. **Commit new code to GitHub** — this session (`clinic_health_report.py` + its 2 units) + still-outstanding S62 checker+units+`.bak`s, S61 watchman, S60 follow-up-VPS, S59 attendance, `call_transcription.py`.
8. **The data pass** (owner-gated: fresh Docterz fill + PHI-strip decision). **Workflow redesign.** **P1–P10 lock (D83–D92).** **D78 sticky counter.**
9. **Parallel:** 🔴 key rotation (Lokesh); AKEY_14; PHI base swap; Sarvam retry; Call_Feed D61.

---

## §3 — KEY FACTS / GOTCHAS (this session's additions)

- **The daily report is READ-ONLY.** It restarts nothing, deletes nothing. Its only outputs
  are the ntfy push + the Gmail. Safe to hand-run any time:
  `cd /root/wa && /root/wa/venv/bin/python3 clinic_health_report.py`. Log: `/root/wa/health_report.log`.
- **Timezone check before any daily timer.** Box = `Asia/Kolkata`, so `OnCalendar=08:00` = 8 AM.
  On a UTC box it would need `02:30`. Always `timedatectl` first.
- **The report has NO anti-spam file** — it's a once-daily digest, MEANT to send every day. Its
  *absence* at 08:00 is the alarm. Do NOT add it to the timer-freshness checker.
- **Lane-1 is deliberately tiny** — only "restart a dead service" (already the watchman's job)
  and "re-run the follow-up push." Everything else is ASSISTED or ESCALATE-ONLY per the register.
  Promoting a fault to AUTO is a logged decision, only after watching it behave.
- **Overnight jobs (recording-archive, transcription) are ASSISTED, not auto-run** — never
  confirmed harmless to run off-schedule. Read the journal first, then decide.
- **Token/disk/backup are ESCALATE-ONLY** — never auto-acted (rotation is HIGH RISK/Lokesh;
  auto-deleting for disk or "fixing" a missing backup is exactly what must NOT be automated).
- Same ntfy/Gmail rules as the watchman: ntfy title ASCII-only (emoji in body only); Gmail
  app-password needs 2-Step Verification on. The report reuses the watchman's `.env` — no new secrets.

---

## §4 — FILES PRODUCED THIS SESSION

**Changed live ON THE VPS (installed + verified this session):**
- `/root/wa/clinic_health_report.py` (md5 `08e1a483ac47b8ee3e73df8ef3f1139f`) — the report. Hand-run OK, both channels fired.
- `/etc/systemd/system/clinic-health-report.service` (md5 `5ed4fd8dfea9ce8067cbb100e6e94759`) — oneshot runner.
- `/etc/systemd/system/clinic-health-report.timer` (md5 `e68b3f8b73b4a74704202dce00421406`) — 08:00 IST, Persistent. Enabled, correct NEXT.

**Design/documentation produced (Drive + project knowledge; no code):**
- `Fault_Action_Register_v1_Session63.md` — the responder brain (fault→lane→procedure).
- `Maintenance_Jobs_and_Health_Report_Design_v1_Session63.md` — deliverable-3 design + build order.
- SOP library: `SOP_VPS_Services`, `SOP_Dashboard_AppScript`, `SOP_WhatsApp_Token`,
  `SOP_FollowUp_Tracker`, `SOP_MyOperator_IVR`, `SOP_Biometric_Attendance`,
  `SOP_Revenue_Reconciler` (stub).

**GitHub note:** secrets/PHI stay gitignored. Suggested repo layout in the commit zip:
`diagnostics-vps/` (report script + 2 units, alongside the S61/S62 files), `sops/` (the SOP
library + register + design doc). Commit still-outstanding S59–S62 files at the same time.

---

## §5 — CANONICAL DOCS AFTER THIS SESSION
- KB: **Clinic_Master_KB_SystemsRegister_v1_31.md** (this EOS)
- Runbook: **HANDOFF_RUNBOOK_2026-07-04_Session63_v43.md** (this file)
- Diagnostics: **Diagnostics_Surveillance_System_Spec_v1_5.md** (this EOS — health-report + maintenance-job family added)
- NEW canonical: **Fault_Action_Register_v1_Session63.md** (the responder brain — reference each maintenance session)
- Maintenance SOP library (Drive master) + **Maintenance_Jobs_and_Health_Report_Design_v1_Session63.md**
- Unchanged: Umbrella v1.23 delta, Call_Console_Evolution_Spec v1.5, Maintenance_SOP_Spec v1.1, Followup_Taxonomy_and_Lifecycle_Design v1(S56).

**Owner-side propagation:** GitHub + project knowledge = source of truth; Notion decisions log
updated (D112–D115 block); Drive holds the current canonical set + SOP library as cold backup
via owner PC drag-drop (connector can't write). **Next session:** arm the timer-freshness
checker (first task), then build the maintenance jobs (deliverable 3).
