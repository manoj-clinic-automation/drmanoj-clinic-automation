# Fault → Action Register (Automated Maintenance & Incident Response)
## Advanced Orthopaedic Surgery Centre, Bareilly
**Drafted: Session 63 · 04 Jul 2026 · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Source of truth: Master KB v1.30 · Diagnostics Spec v1.4 · Runbook Session 62 (v42).**
**KB wins on any conflict. THIS IS A DESIGN DOCUMENT — nothing here is built or armed yet.**

> **What this is.** The single brain for how the clinic system responds to every fault.
> For each fault it says: which **lane** it's in, what the system does automatically, and —
> when a human is needed — the **exact stepwise procedure** to follow. Everything else
> (the narrow auto-responder, the maintenance jobs, the health report) is built *from* this
> register. Get this right and the rest is mechanical.

---

## 1. The two lanes (the whole safety model)

Every fault is assigned to exactly one lane.

### LANE 1 — NARROW-AUTO (system fixes it by itself)
The system detects the fault, runs a **proven-safe, idempotent** fix, re-checks, and reports
*"detected X → ran fix → confirmed healthy"* (or, if the fix didn't work, hands it to Lane 2).

**A fault qualifies for Lane 1 ONLY if its fix is:**
- **Idempotent** — safe to run twice with no harm, and
- **Proven harmless** — we have watched this exact action behave, and
- **Non-destructive** — it never deletes data, never touches PHI, never touches the MyOperator panel, never rotates a token.

**Starting Lane 1 deliberately TINY — only these two actions:**
| Action | Why it's safe |
|---|---|
| Restart a dead always-on service (`systemctl restart <svc>`) | systemd handles it cleanly; this is exactly what the S61 watchman already does, proven over weeks. |
| Re-run the follow-up push (`systemctl start clinic-followup-push.service`) | Replace-only / harmless — owner-confirmed it re-writes the same rows. |

Nothing else is Lane 1 until we deliberately **promote** it after watching it behave.
**Promoting a fault to Lane 1 is a decision, logged like any other.**

### LANE 2 — ASSISTED / STEPWISE (human-confirmed, session-driven)
For everything not in Lane 1, the system **never acts blindly**. It escalates to the doctor
(ntfy + Gmail) with the fault and a pointer to its procedure below. The doctor then handles
it **exactly like a coding session** — Claude presents one slice (fault → proposed action →
exact command), the doctor confirms, it runs, reports back, next slice. **No consequential
action ever runs without an explicit confirmation.**

> **How Lane 2 works in practice (Option 2a — agreed S63):** the background program only ever
> *detects and escalates* for Lane 2 — it takes no action itself. The stepwise "assistant"
> is Claude in a session, scripted by this register. This keeps the *acting-on-the-live-clinic*
> code surface as small as possible (just the two Lane-1 actions).

### The third response type inside Lane 2: AUTO-THEN-ESCALATE
Some faults get the Lane-1 fix **tried once**, and if the service does **not** recover, they
escalate to Lane 2 with the manual procedure. (This is already how the watchman behaves:
restart once → if still down, shout.) Marked below as **AUTO→ESC**.

---

## 2. THE REGISTER — every current & reserved fault

Columns: **Fault code · Detected by · Lane · What the system does · If human needed: the procedure.**

### 2.1 Always-on service liveness (S61 watchman, LIVE)

| Fault code | Lane | System does | Procedure if it doesn't self-recover |
|---|---|---|---|
| `VPS_CALL_RELAY_DOWN` (:8097 dialer) | **AUTO→ESC** | `systemctl restart call-api`; re-check; alert | 1. `systemctl status call-api -l` + `journalctl -u call-api -n 80`. 2. If Python traceback → fix cause (build session), don't loop-restart. 3. Fallback: staff dial in MyOperator panel directly. Contact: Lokesh for panel. |
| `VPS_WA_RELAY_DOWN` (:8096 send) | **AUTO→ESC** | restart `wa-send-api`; re-check; alert | Same shape. Fallback: panel-native WhatsApp automations still fire independently. |
| `VPS_WA_RECEIVER_DOWN` (:8095 inbound) | **AUTO→ESC** | restart `wa-receiver`; re-check; alert | If it won't start: `journalctl -u wa-receiver -n 80`. Effect while down: WA_Inbox stops filling → dashboard WhatsApp feed empty. |
| `call-hook.service` down (:8098) | **AUTO→ESC** | restart `call-hook`; re-check; alert | While down: `Call_Durations` stops → duration gate can't unlock. Degrade-safe by design (won't retry-storm). |
| `clinic-portal.service` down (:8099) | **AUTO→ESC** | restart; re-check; alert | Staff launcher down; low urgency. Log check if repeats. |
| `clinic-followup-receiver` down (:8100) | **AUTO→ESC** | restart; re-check; alert | Catcher for the PC workbook. While down, the PC hook can't deliver — see follow-up faults. |
| `wa-notifier` down | **AUTO→ESC** | restart; re-check; alert | ntfy name-alerts stop; not patient-facing. |
| `attendance-dashboard` down (:8042) | **AUTO→ESC** | restart; re-check; alert | Attendance view down; staff record on paper; Secureye buffers punches. Non-clinical. |
| `attlistener` down | **AUTO→ESC** | restart; re-check; alert | Punches not recorded live; device buffers and syncs on recovery. |

### 2.2 Timer-job freshness (S62 checker, heartbeats LIVE, checker arms next)

| Fault code | Lane | System does | Procedure if human needed |
|---|---|---|---|
| `FOLLOWUPS_PUSH_MISSED_RUN` (CRITICAL) | **AUTO→ESC** | `systemctl start clinic-followup-push.service`; re-check heartbeat; alert | If heartbeat still stale after re-run → the **input** is missing. Check `clinic-followup-receiver` up + did Shavez run the Docterz export? Fallback: staff use last good list. |
| `RECORDING_ARCHIVE_MISSED_RUN` (WARNING) | **ASSISTED** | alert only — **NOT auto-run** | Overnight job; never confirmed harmless to run off-schedule. Stepwise: read `journalctl -u call-recording-archive -n 80` first → only then decide to `systemctl start` it. |
| `TRANSCRIPTION_MISSED_RUN` (WARNING) | **ASSISTED** | alert only — **NOT auto-run** | Same as above for `call-transcription`. Read log before acting. |

### 2.3 Follow-up list freshness (Apps Script sentinel, LIVE)

| Fault code | Lane | System does | Procedure if human needed |
|---|---|---|---|
| `FOLLOWUPS_LIST_STALE` / `FOLLOWUPS_NOT_LOADED` (CRITICAL) | **ASSISTED** | email you (sentinel) | 1. `cat /root/wa/heartbeats/followup-push.hb` — old? 2. Re-run push (safe). 3. Still empty → Docterz export missing (Shavez) or catcher down. |
| `FOLLOWUPS_DATE_MALFORMED` | **ASSISTED** | email you | Build-session fix — malformed due-dates in source; do not auto-touch data. |

### 2.4 Reserved / planned (in surveillance register; detection not all built yet)

| Fault code | Lane | System does | Procedure |
|---|---|---|---|
| `WA_TOKEN_AGING` (warn 80d → crit 90d) | **ESCALATE-ONLY** | alert only — **NEVER auto-acted** | Follow `SOP_WhatsApp_Token.md` exactly. HIGH RISK. Coordinate with Lokesh BEFORE rotating. |
| `PATIENT_MASTER_STALE` (WARNING) | **AUTO→ESC** | re-run `push_patient_mirror.py`; re-check | If still stale → source/service issue; read log. |
| `CALL_FEED_STALE` (WARNING) | **ASSISTED** | alert only | Known under-reporting (D61); investigate in build session. |
| `REVENUE_STALE` (WARNING) | **ASSISTED** | alert only | Reconciler live-state unconfirmed (see stub SOP). Verify before acting. |
| `DISK_SPACE_LOW` (planned maint. job) | **ESCALATE-ONLY** | alert only — **NEVER auto-delete** | Stepwise review of what's filling disk before removing anything. Deleting is never auto. |
| `LOG_ROTATION_OVERDUE` (planned maint. job) | **AUTO** (once built+proven) | prune per policy; report | Candidate for Lane-1 promotion *after* the prune is proven idempotent. Starts ASSISTED. |
| `BACKUP_MISSING` (planned maint. job) | **ESCALATE-ONLY** | alert only | A missing backup is never "fixed" automatically — you're told, you act. |

---

## 3. Rules that keep the responder sturdy (non-negotiable)

1. **One action per fault per outage.** Never restart-storm. Anti-spam state file, one alert
   per outage, recovery note on return. (Same DNA as watchman + checker.)
2. **Fail-loud.** If the responder itself errors, it shouts (ntfy+Gmail) — never dies silent.
3. **Read-only except the whitelisted Lane-1 actions.** The program's *only* write-actions are
   the exact `systemctl` commands in the Lane-1 list. It has no code path that deletes,
   edits data, touches PHI, or calls the MyOperator panel.
4. **Every alert names its procedure.** An alert is never just "X is down" — it carries the
   fault code, which maps here to the exact steps.
5. **Promotion is a logged decision.** Moving a fault ESCALATE→AUTO happens only after we've
   watched it behave, and is recorded as a D-decision.
6. **Log every action.** Plain log on the VPS; the daily report (deliverable 3) summarises it.

---

## 4. What gets built from this register (order)

- **Deliverable 2 — narrow auto-responder:** generalises the watchman's restart to the Lane-1
  list above (2 actions), AUTO→ESC behaviour for the service faults. Small, offline-tested,
  armed only with owner OK.
- **Deliverable 3 — maintenance jobs + daily health report:** the `DISK_SPACE_LOW`,
  `LOG_ROTATION_OVERDUE`, `BACKUP_MISSING`, `WA_TOKEN_AGING` detectors, plus a once-daily
  "everything healthy / here's what I auto-fixed today" summary to phone+email (so health is
  positively confirmed, not just silence-unless-broken).

---

## 5. Open questions for the owner (to resolve before building deliverable 2)
1. **Daily report timing** — what time should the once-a-day health summary land? (Suggest
   ~8 AM IST so it's the first thing you see, after the overnight jobs have run.)
2. **Report channel** — Gmail email, ntfy push, or both? (Suggest both: ntfy one-liner +
   Gmail with the detail.)
3. **Log-prune policy** — how many days of logs to keep before pruning? (Suggest 30 days;
   this decides whether `LOG_ROTATION_OVERDUE` can ever become Lane-1 AUTO.)

*(These are design choices, not blockers for approving the register itself.)*

---

*Nothing in this document is live. It is the specification. On approval it becomes the basis
for deliverables 2 and 3, and a copy goes to Notion "Clinic HQ" + the handoff kit.*
