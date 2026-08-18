# FAULT → ACTION REGISTER — v2.0 (CONSOLIDATED, SELF-CONTAINED)
## Advanced Orthopaedic Surgery Centre, Bareilly
**Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Drafted Session 63 · Re-based Session 131, 09 July 2026. Supersedes v1 entirely.**

**Source of truth: `Clinic_Master_KB_SystemsRegister_v1_57.md` · `Diagnostics_Surveillance_System_Spec_v2_0.md` · `HANDOFF_RUNBOOK_..._Session131_v69.md`. The KB wins on any conflict.**

---

## §0 — WHAT THIS DOCUMENT IS, AND WHAT CHANGED

**This document is the single brain for RESPONSE.** Every fault → its lane → what the system does →
the exact procedure when a human is needed. **That is `D114`, and it stands.** It was considered for
retirement in Session 131 and **kept**: the Diagnostics Spec answers *"how do we detect it?"*; this
register answers *"what happens when it fires?"* They are not duplicates.

### §0.1 — The writer boundary (D203)

> **`Diagnostics_Surveillance_System_Spec` defines a fault code and how it is detected.**
> **This register assigns that code a lane and a procedure.**
> **A code is defined once, and laned once. Neither document restates the other.**

Where this register lists a code, it does so **to lane it**, never to redefine it. Where the
Diagnostics spec names a lane, it is quoting this register.

### §0.2 — Three things v1 said that were not true

**1. Its source-of-truth line was twenty-five versions dead.** v1 cited *"Master KB v1.30 ·
Diagnostics Spec v1.4 · Runbook Session 62 (v42)."* Current: **KB v1.57 · Diagnostics v2.0 ·
Runbook v69.**

**2. Its front page and its body contradicted each other.** The header read *"THIS IS A DESIGN
DOCUMENT — nothing here is built or armed yet"* while §2.1 was titled *"S61 watchman, **LIVE**"* and
§2.3 *"Apps Script sentinel, **LIVE**"*. Both were partly right and the reader could not tell which:
**the detectors are live; the responder is not.** Every table below now carries that distinction
explicitly.

**3. F-24 — the register describes an auto-responder that does not exist.**
Nine faults in §2.1 are marked **AUTO→ESC**, *"System does: `systemctl restart call-api`; re-check;
alert."* But the live watchman (Diagnostics **§L2**) is, in its own words:

> *"**Read-only** — reports only; **never starts/stops/changes a service.**"*

It **names** the restart command inside an alert. It has never run one. And §M1's **D113** —
*"The S61 watchman **IS** the Lane-1 service responder"* — states a design intent as a fact. §4 of
this very document lists that responder as **Deliverable 2, unbuilt.**

> **This is not academic.** During an outage, a session reading v1's §2.1 would wait for a restart
> that never comes. **Every "System does" cell below is now marked with what actually happens today.**

### §0.3 — Codes detected but never laned

Session 125 built the `CALLHOOK_*` detector family. **Six of its codes have never appeared in this
register.** They are laned in **§2.5** below.

**And the two documents name the same fault differently:** Diagnostics §L2 registers
`VPS_SERVICE_DOWN` and `WATCHDOG_SELF_FAIL`; this register lanes nine per-service codes
(`VPS_CALL_RELAY_DOWN`, `VPS_WA_RELAY_DOWN`, …). **Both are correct and neither is wrong** — the
detector emits one code with the service name attached; this register lanes the response per service.
Recorded here so nobody "fixes" one to match the other.

---

## §0.4 — READ THE STATUS COLUMN BEFORE YOU TRUST A ROW

| Marker | Meaning |
|---|---|
| 🟢 **DETECTOR LIVE · RESPONDER LIVE** | The system detects it *and* acts. |
| 🟡 **DETECTOR LIVE · RESPONDER NOT BUILT** | You are told. **Nothing is done for you.** The "System does" cell describes Deliverable 2, which does not exist. |
| ⚪ **NEITHER BUILT** | Reserved. Detection not built. |

**As of Session 131, not one row is 🟢.** The Lane-1 auto-responder has never been built. Everything
live is **detect-and-alert**.

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

---

> 🟡 **§2.1, §2.2, §2.3 — DETECTOR LIVE · RESPONDER NOT BUILT.** The watchman, the timer-freshness
> checker and the Apps Script sentinel all **detect and alert**. None of them restarts anything. Read
> every *"System does"* cell below as *"System **will** do, once Deliverable 2 is built."* Today the
> alert names the command and **you or Claude run it.**
>
> ⚪ **§2.4 — NEITHER BUILT**, except `WA_TOKEN_AGING` (still ESCALATE-ONLY, still overdue).

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


### 2.5 The `call-hook` 403 family (S125 detector LIVE · responder NOT BUILT) — **NEW in v2.0**

> These six codes were minted with the detector in Session 125 and **have never had a lane.**
> Detection: `Diagnostics_Surveillance_System_Spec_v2_0.md` **§L5**. Full incident:
> `INCIDENT_2026-07-08_CALLHOOK_403_v5_CONSOLIDATED.md`.

| Fault code | Lane | System does | Procedure if human needed |
|---|---|---|---|
| `CALLHOOK_SECRET_MISMATCH_403` (CRITICAL) | **ESCALATE-ONLY** | alert only — **NEVER auto-acted** | A secret mismatch is a key problem, not a service problem. **Never restart, never rotate automatically.** Read `INCIDENT_..._v5` §16 first. **Dual-key acceptance (D162) means a mismatch no longer causes an outage** — it means one key is stale. Coordinate with Lokesh before touching the MyOperator panel. |
| `CALLHOOK_MULTIPLE_KEYS` (WARNING) | **ESCALATE-ONLY** | alert only | More than one key seen in the access log. Expected *during* a rotation; unexpected otherwise. Check `rotate_callhook.sh status`. **The rotation is PARKED (S128).** |
| `CALLHOOK_403_EARLIER_TODAY` (WARNING) | **ASSISTED** | alert only | Deliveries were refused earlier today and are being accepted now. Read the access log before concluding it is healed. **D163's rejection logging exists precisely so this is visible.** |
| `CALLHOOK_NO_ACCEPTED_TODAY` (CRITICAL) | **ESCALATE-ONLY** | alert only | Zero accepted deliveries today. On a clinic day this is an outage. **`Call_Durations` stops → the duration gate cannot unlock → but it FAILS OPEN (D156), so staff can still file.** Diagnose; do not restart blindly. |
| `CALLHOOK_SILENT` (WARNING) | **ASSISTED** | alert only | No deliveries at all — accepted or refused. Distinguish *"no calls happened"* from *"the webhook is unplugged."* **Absence of coverage is not absence of events (§M5).** |
| `CALLHOOK_RAWLOG_MISSING` (WARNING) | **ASSISTED** | alert only | The raw `.jsonl` is missing. The receiver 403s **before** `raw_log()`, so a missing raw log and a refused delivery look identical from inside. Read the OpenLiteSpeed access log. |

**None of these is ever Lane 1.** A key, a panel, or a vendor is on the other end of every one of
them, and **rule 3 of §3 forbids the responder from touching any of the three.**


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

---

## 5. Open questions for the owner (to resolve before building deliverable 2)
1. **Daily report timing** — what time should the once-a-day health summary land? (Suggest
   ~8 AM IST so it's the first thing you see, after the overnight jobs have run.)
2. **Report channel** — Gmail email, ntfy push, or both? (Suggest both: ntfy one-liner +
   Gmail with the detail.)
3. **Log-prune policy** — how many days of logs to keep before pruning? (Suggest 30 days;
   this decides whether `LOG_ROTATION_OVERDUE` can ever become Lane-1 AUTO.)


### §5.1 — Two of these three are now CLOSED (S131)

| | v1's question | Answer, from what shipped |
|---|---|---|
| **Q1** | Daily report timing? | **CLOSED — 09:00 IST.** `Health.gs` emails ✅/not-✅ every morning. Its *absence* is the fault. |
| **Q2** | Report channel? | **CLOSED — both.** `clinic_health_report.py` (Diagnostics §L4, D115): **ntfy one-liner + Gmail detail.** |
| **Q3** | Log-prune policy — how many days? | **STILL OPEN.** This decides whether `LOG_ROTATION_OVERDUE` can ever be promoted to Lane 1. The suggestion of 30 days stands and has never been ruled on. |

*v1 suggested ~8 AM. What shipped is 09:00 IST. The document was never told.*


---

## §6 — WHAT THIS REGISTER STILL OWES

- **Deliverable 2, the narrow auto-responder, has never been built.** Every `AUTO→ESC` and `AUTO` cell
  above is a promise, not a behaviour. **F-24.**
- **D113 must be re-stated or retired.** *"The S61 watchman IS the Lane-1 service responder"* is not
  true of the watchman that exists. It is either a design intent (say so) or a decision to build
  (schedule it).
- **Q3 — the log-prune policy** — is the last open question from S63.
- **The Maintenance & SOP project does not exist.** `SOP_WhatsApp_Token.md`, referenced under
  `WA_TOKEN_AGING`, has never been written. **A procedure that points at a document nobody wrote is
  not a procedure.**

---

## CHANGELOG

| Version | Date | Change |
|---|---|---|
| **v2.0** | **09 Jul 2026 (Session 131)** | **RE-BASED, self-contained, status-true.** **Not retired** — `D114` makes this the single brain for response, and Session 131 confirmed it after nearly retiring it without reading D114. **D203** states the writer boundary: Diagnostics *defines and detects* a fault code; this register *lanes* it; neither restates the other. **F-24 raised:** v1's §2.1 described an auto-responder (`systemctl restart …`) that **does not exist** — the live watchman is read-only and *"never starts/stops/changes a service."* Every table now carries a status marker; **not one row is 🟢.** Source-of-truth line corrected (was KB v1.30 · Diagnostics v1.4 · Runbook v42 — twenty-five versions dead). **§2.5 added:** the six `CALLHOOK_*` codes, detected since Session 125 and never laned. §5's Q1 and Q2 **closed** by what shipped (09:00 IST; ntfy + Gmail). **§1, §2.1–§2.4, §3, §4 and §5 are reproduced verbatim; no rule, lane or procedure was altered.** |
| v1 | 04 Jul 2026 (Session 63) | First draft. Two lanes, the register, the six sturdiness rules, the build order, three open questions. Its header said *"nothing here is built or armed yet"* while its body marked three detectors LIVE. |

---

**END OF FAULT → ACTION REGISTER v2.0 — §6 and the CHANGELOG are the last sections. If either is absent, this file is truncated and must not be used as canonical.**
