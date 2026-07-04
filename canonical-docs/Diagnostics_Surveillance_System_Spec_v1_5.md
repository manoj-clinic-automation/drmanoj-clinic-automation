# Diagnostics & Surveillance System Spec — v1.5 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward everything in v1.4 unchanged (S62 timer-freshness family).
> Session 63 adds two things: the **daily health report** (Category 3 — positive confirmation,
> not detection) which is BUILT + LIVE, and the **maintenance-job family** (preventive upkeep)
> which is DESIGNED (register + design doc approved) but NOT yet built. It also records the
> **automated-response model** (two lanes) that governs how every fault is acted on.

---

## §NEW-A — THE RESPONSE MODEL (how faults are acted on) — LOCKED S63

Detection was the whole story until now. S63 defines what happens *after* detection.

**Two lanes (D112):**
- **LANE 1 — NARROW-AUTO.** System runs a proven-safe, idempotent fix itself, then re-checks
  and reports. Started deliberately tiny: only (1) restart a dead always-on service, (2) re-run
  the follow-up push. Nothing else is Lane 1 until deliberately promoted (a logged decision).
- **LANE 2 — ASSISTED (Option 2a).** For everything else, the background program only
  *detects + escalates*; the stepwise fixer is Claude in a confirmation-gated session, scripted
  by the Fault → Action Register. No consequential action runs without an explicit confirmation.
- **AUTO→ESC** = a Lane-1 fix is tried once; if the service doesn't recover, it escalates with
  the manual procedure. (This is already the watchman's behaviour.)
- **ESCALATE-ONLY** = never auto-acted (token rotation, disk-full, backup-missing, anything
  destructive / PHI / MyOperator-panel).

**The S61 watchman IS the Lane-1 service responder (D113)** — no second restarter is built.

**The single brain = `Fault_Action_Register_v1_Session63.md` (D114)** — every fault (watchman
liveness, timer-freshness, sentinel, + reserved maintenance faults) mapped to lane + exact
procedure. Reference it in every maintenance/incident session.

---

## §NEW-B — DAILY HEALTH REPORT (Category 3 — positive confirmation) — LIVE (D115)

**The gap this closes.** Detection layers only speak up when something is wrong — so "no news"
is *assumed* good, but could also mean the alerter itself died. The report makes health
**positively confirmed** every morning.

**What it is.** `clinic_health_report.py` (`/root/wa/`) — **READ-ONLY**, takes no action. Each
run it reads:
- the 9 always-on services (`systemctl is-active`),
- the 3 timer-job heartbeats (`/root/wa/heartbeats/*.hb`),
- disk usage (`df /`),
- the watchman's actions in the last 24h (`/root/wa/watchdog.log`),
and sends ONE digest: **ntfy one-liner + Gmail detail**. Overall line is ✅ ALL GREEN or
⚠️ ATTENTION NEEDED, with an "ANYTHING NEEDING YOU" section that names faults + their procedures.

**DNA:** reuses the watchman's `.env` (no new secrets); **fail-loud** (a crash shouts via ntfy);
**no anti-spam** — it is a once-daily digest MEANT to send daily; **no PHI**.

**Schedule:** `clinic-health-report.timer`, `OnCalendar=*-*-* 08:00:00` (box is `Asia/Kolkata`,
so 08:00 = real 8 AM IST), `Persistent=true` (a missed morning catches up). It is the 5th timer
on the box and is deliberately **NOT** heartbeat-monitored — because the report's own *absence*
at 08:00 is the alarm. Live-verified: hand-run fired both channels; timer enabled; correct NEXT.

md5s: script `08e1a483ac47b8ee3e73df8ef3f1139f` · `.service` `5ed4fd8dfea9ce8067cbb100e6e94759`
· `.timer` `e68b3f8b73b4a74704202dce00421406`.

---

## §NEW-C — MAINTENANCE-JOB FAMILY (preventive upkeep) — DESIGNED, NOT BUILT

Four scheduled jobs that keep the box healthy rather than only watching it. Design +
lane per the register; build order + open blockers noted.

| Job | Fault code | Lane | Status / blocker |
|---|---|---|---|
| Disk-space check | `DISK_SPACE_LOW` (warn 80 / crit 90) | ESCALATE-ONLY | Build next. Self-contained. Never auto-deletes. |
| WhatsApp token-age | `WA_TOKEN_AGING` (warn 80 / alert 90) | ESCALATE-ONLY | Needs a "token set-on" baseline date first. |
| Log-pruning (30-day) | `LOG_ROTATION_OVERDUE` | ASSISTED (promote later) | The one DELETE action — inspect where logs live + sizes BEFORE building. |
| Backup-success | `BACKUP_MISSING` | ESCALATE-ONLY | BLOCKED — needs a **box-verifiable** backup (current cold backup is owner-PC→Drive, invisible to the VPS). |

These feed the daily report once built (disk already does; the rest add lines).

---

## Complementary layers now (four)
- **VPS watchman** (S61) — always-on service *liveness* (every 5 min). Also Lane-1 responder.
- **VPS timer-freshness** (S62) — sleeping-job *freshness* (heartbeats, hourly; arms next session).
- **Apps Script sentinel** (v1.2) — follow-up-list freshness (2–3 PM daily).
- **Daily health report** (S63) — *positive confirmation* of all the above (08:00 daily). NEW.

## Growth path (next diagnostics sessions, one at a time)
1. Arm the timer-freshness checker (S62's parked step).
2. Build the maintenance jobs (disk → token-age → log-prune → backup), feeding the report.
3. Then Patient_Master mirror freshness, Call_Feed freshness, revenue reconciler freshness.

## CHANGELOG
| v1.5 | 04 Jul 2026 (Session 63) | Response model locked (two lanes, D112; watchman = Lane-1 responder, D113; Fault→Action Register = brain, D114). Daily health report BUILT + LIVE (Category 3, positive confirmation, D115). Maintenance-job family DESIGNED not built (disk/token-age/log-prune/backup). Four surveillance layers now. |
| v1.4 | 04 Jul 2026 (Session 62) | Timer-freshness family (Category 2). |
| v1.3 | 04 Jul 2026 (Session 61) | VPS service watchman. |
| v1.2 | 03 Jul 2026 (Session 53) | First live check: `FOLLOWUPS_LIST_STALE`. |
| v1.1 | (prior) | Fault codes, detection architecture, fallback protocols. |
