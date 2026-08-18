# Clinic Master KB / Systems Register — v1.31

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document for v1.31.** Carries forward everything in v1.30 (S62 timer-freshness
> heartbeats + checker built, D110–D111) and all prior versions unchanged, and adds the
> **Session 63 block (§63)** with decisions **D112–D115**, a §12 state update, and a
> surveillance-register update. **Code WAS changed this session (full EOS):** a new
> **read-only daily health report** was built, installed, live-verified on both channels,
> and armed to fire itself at **08:00 IST** via its own systemd timer. Also this session:
> the **maintenance SOP library was drafted** and the **Fault → Action Register** (the
> automated-maintenance brain) was designed and approved. **KB wins on any conflict.**

---

## §12 STATE — what is live right now (updated at Session 63 close)

- **DAILY HEALTH REPORT — LIVE and self-firing (D115).** New read-only job
  `clinic_health_report.py` on the VPS. It takes **no action** on the box — it only READS
  what the existing layers already know (the 9 always-on services via `systemctl is-active`,
  the 3 timer-job heartbeats, disk % via `df`, and the watchman's `watchdog.log`) and sends
  ONE daily digest at **08:00 IST** via **both ntfy + Gmail** (reuses the watchman's `.env`
  creds — no new secrets). Installed, hand-run, **both channels confirmed firing**, then
  armed via `clinic-health-report.timer` (`OnCalendar=08:00`, `Persistent`). `list-timers`
  shows correct NEXT = next 08:00 IST. Box confirmed on `Asia/Kolkata`, so 08:00 = real 8 AM.
  - md5s: script `08e1a483ac47b8ee3e73df8ef3f1139f`; `.service` `5ed4fd8dfea9ce8067cbb100e6e94759`; `.timer` `e68b3f8b73b4a74704202dce00421406`.
  - **Positive-confirmation property:** health is no longer "silence = good." A report that
    FAILS to arrive at 08:00 is itself the signal (reporter or box down). This is the fifth
    timer on the box; it deliberately is NOT heartbeat-monitored because its absence is the alarm.
  - Anti-spam: none by design — it is a once-daily digest MEANT to send every day (not an alerter). Fail-loud: a crash shouts via ntfy.
- **AUTOMATED-MAINTENANCE DESIGN LOCKED (D112–D114).** This session designed the preventive/
  responder half of diagnostics, approved by owner, **built from here on**:
  - **Hybrid two-lane model (D112).** LANE 1 = NARROW-AUTO (system fixes it itself), started
    deliberately TINY — only two proven-safe idempotent actions: restart a dead always-on
    service, and re-run the follow-up push. LANE 2 = ASSISTED (Option 2a) — for everything
    else the background program only DETECTS + ESCALATES; the stepwise "assistant" is Claude
    in a confirmation-gated session, scripted by the register (like a build session). A fault
    is promoted ESCALATE→AUTO only after being watched behave, as a logged decision.
  - **The S61 watchman IS the Lane-1 service responder (D113).** We do NOT build a second
    program that clones its restart. The watchman already restarts a dead service + alerts,
    proven for weeks; that IS Lane 1 for services. The only genuinely-missing Lane-1 action
    (the follow-up-push re-run) folds into the timer-freshness checker at arming (next session).
  - **Fault → Action Register v1 (D114)** — the single brain: every fault (across watchman
    liveness, timer-freshness, sentinel, + reserved maintenance faults) → lane
    (NARROW-AUTO / AUTO→ESC / ASSISTED / ESCALATE-ONLY) → exact procedure. Overnight jobs
    (recording-archive, transcription) are ASSISTED not auto-run (never confirmed harmless
    off-schedule). Token-age, disk-full, backup-missing are ESCALATE-ONLY (never auto-acted).
- **MAINTENANCE SOP LIBRARY DRAFTED (documentation).** Six real SOPs + one honest stub, in
  the shape the Maintenance_SOP_Spec requires (what it does · components · healthy indicators ·
  failure modes + fix paths · contacts · manual fallback):
  `SOP_VPS_Services`, `SOP_Dashboard_AppScript`, `SOP_WhatsApp_Token` (HIGH RISK, Lokesh),
  `SOP_FollowUp_Tracker`, `SOP_MyOperator_IVR`, `SOP_Biometric_Attendance`,
  `SOP_Revenue_Reconciler` (**STUB** — reconciler live-state unconfirmed; not faked).
  These are Drive-master per M3 (owner drag-drops to `Clinic Automation / SOPs /`).
- **Report design choices locked (owner):** 08:00 IST · both channels (ntfy + Gmail) · 30-day
  log retention (the fixed policy that later lets `LOG_ROTATION_OVERDUE` be promoted to Lane-1).
- **Maintenance jobs designed, NOT built:** disk-space check (`DISK_SPACE_LOW`, ESCALATE-ONLY,
  warn 80/alert 90), log-pruning (`LOG_ROTATION_OVERDUE`, ASSISTED-first, 30-day), backup-success
  (`BACKUP_MISSING`, ESCALATE-ONLY — **needs owner to define "what/where is a backup" a VPS job
  can verify**; current cold backup is owner-PC drag-drop, invisible to the box), WhatsApp
  token-age (`WA_TOKEN_AGING`, ESCALATE-ONLY, warn 80/alert 90 — **needs a "token set-on" baseline date**).
- **All §12 state from v1.30 stands verbatim** — S62 timer-freshness heartbeats LIVE on all
  three timer jobs; checker `clinic_timer_freshness.py` built + 5/5 tested but **still NOT armed**
  (two-phase rollout; arms next session after overnight heartbeats seed); S61 watchman LIVE
  (nine services, every 5 min); Apps Script stale-list sentinel LIVE; follow-up push VPS-native
  (D101–D105); attendance live; Dashboard v18.18; caller-ID SOP D93; duration gate D82; key
  rotation 🔴 overdue; AKEY_14; PHI base swap deferred.

**Known open (top of next backlog):**
1. **Arm the timer-freshness checker** (S62's parked step) — confirm all 3 heartbeats seeded
   (`cat /root/wa/heartbeats/*.hb` — three recent timestamps) → upload `clinic_timer_freshness.py`
   (md5 `21deacf639c1e40eed6ebad81bd46b6d`) → run by hand (expect all-fresh, silent) → install
   `.service`+`.timer` → enable → one live missed-run proof. **At the same time, decide** whether
   to switch its `FOLLOWUPS_PUSH_MISSED_RUN` from alert-only to AUTO→ESC (adds the Lane-1
   push re-run per D112).
2. **Maintenance jobs (deliverable 3 cont.):** disk-space check → token-age check → log-pruning
   (inspect where logs live first; the one delete action, treated most carefully) → backup-check
   (after owner defines a box-verifiable backup).
3. WhatsApp token-age ties to 🔴 rotation. Then "Agent shows as Staff" verify+close.
4. GitHub commit (this session + still-outstanding S59–S62 files). The data pass. Workflow
   redesign. P1–P10 lock (D83–D92 reserved). D78 sticky counter.
5. Parallel: 🔴 key rotation (Lokesh); AKEY_14; PHI base swap; Sarvam retry; Call_Feed D61.

---

## §63 SESSION 63 — daily health report LIVE; automated-maintenance designed; SOP library drafted (04 Jul 2026)

**Code changed (VPS: new read-only report job + its timer). Full EOS.** Decisions **D112–D115**.

### What this session set out to do
Owner asked for (a) a system of **automated, monitored, reported maintenance jobs**, and (b)
**clear per-fault procedures** ("if a service is down, exactly what to do"). We designed the
whole thing safely, then shipped the lowest-risk, highest-daily-value piece.

### The design (deep, one decision at a time)
- Chose a **hybrid**: narrow fully-automatic fixes + assisted stepwise handling for the rest.
- Made the assisted lane **Option 2a** (Claude-in-session, scripted by the register) rather
  than a custom interactive daemon — keeps the *acting-on-the-live-clinic* code surface minimal.
- Started Lane-1 **narrow** (2 proven-safe actions) — promoting is easy, walking back a bad
  auto-action on a live clinic is not.
- Recognised the **watchman already IS the Lane-1 service responder** — did NOT clone it.
- Built the **Fault → Action Register** first (the brain), approved it, then built the report.

### What shipped (verified between each step)
1. **SOP library** (6 real + 1 stub) drafted to the Maintenance_SOP_Spec shape.
2. **Fault → Action Register v1** — approved by owner.
3. **Maintenance jobs + daily-report design v1** — approved; build order = report first.
4. **`clinic_health_report.py`** built → `py_compile` PASS → 2 offline behaviour tests
   (ATTENTION path + ALL-GREEN path) → installed (md5-verified) → **hand-run, both ntfy +
   Gmail confirmed firing** → 8 AM `.timer` installed (md5-verified on box) → timezone
   confirmed IST → enabled → `list-timers` shows correct NEXT. LIVE.

### Decisions locked
- **D112** — Automated maintenance = **hybrid two-lane**: Lane 1 NARROW-AUTO (start tiny: 2
  proven-safe idempotent actions only); Lane 2 ASSISTED = **Option 2a** (detect+escalate;
  stepwise handling by Claude-in-session, scripted by the register). Promotion ESCALATE→AUTO
  is a logged decision made only after watching a fix behave.
- **D113** — The **S61 watchman is the Lane-1 service responder**; no second restarter is
  built. The missing Lane-1 push re-run folds into the timer-freshness checker at arming.
- **D114** — **Fault → Action Register v1** adopted as the single source of truth for
  fault→lane→procedure. Overnight jobs ASSISTED (not auto-run); token/disk/backup ESCALATE-ONLY.
- **D115** — **Daily health report LIVE**: read-only digest, 08:00 IST, both channels, reuses
  watchman `.env`, fail-loud, no anti-spam (daily digest by design). Its own absence is the
  alarm; deliberately not heartbeat-monitored.

### Gotchas captured
- Timezone check BEFORE enabling a daily timer is mandatory: box is `Asia/Kolkata`, so
  `OnCalendar=08:00` = real 8 AM. On a UTC box it would have needed `02:30`.
- The report is safe to hand-run any time (read-only): `cd /root/wa && /root/wa/venv/bin/python3 clinic_health_report.py`.
- `backup-success` check is blocked until a **box-verifiable** backup exists (current cold
  backup is owner-PC → Drive, invisible to the VPS). `token-age` needs a baseline set-on date.
- Report is the 5th timer on the box; it is NOT added to the timer-freshness checker (its
  absence is its own alarm) — don't "fix" that by monitoring it.

---

## SURVEILLANCE REGISTER — updated rows (per M6)
| Module | What is monitored | Fault codes | Severity |
|---|---|---|---|
| Daily health report (timer, 08:00) | Positive daily confirmation of all layers; absence = alarm | (report itself; no code) | INFO / self-signalling |
| Disk space (maint. job — designed) | % used on `/` | `DISK_SPACE_LOW` (warn 80 / crit 90) | WARNING→CRITICAL · ESCALATE-ONLY |
| Log rotation (maint. job — designed) | Logs older than 30d present | `LOG_ROTATION_OVERDUE` | WARNING · ASSISTED (promote later) |
| Backup success (maint. job — designed) | Recent backup exists (needs box-verifiable def.) | `BACKUP_MISSING` | WARNING · ESCALATE-ONLY |
| WhatsApp token age (maint. job — designed) | Days since token set (needs baseline) | `WA_TOKEN_AGING` (warn 80 / alert 90) | WARNING→CRITICAL · ESCALATE-ONLY |

*(Health report LIVE; the four maintenance jobs DESIGNED not built — next session's deliverable 3.)*
