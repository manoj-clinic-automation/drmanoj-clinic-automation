# FAULT → ACTION REGISTER — v2.22 (CONSOLIDATED, SELF-CONTAINED)
## Advanced Orthopaedic Surgery Centre, Bareilly
**Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Drafted Session 63 · Re-based Session 131, 09 July 2026. Supersedes v1 entirely.**
**v2.17, Session 181, 15 August 2026 — the three owed appends applied (F-82 … F-89). §0–§6 unchanged.**
**v2.22, Session 187, 18 August 2026 — F-122 … F-126 appended THE SAME SESSION they were raised, for the second close running. Five findings from the session that closed F-117 structurally and shipped eight kits: the generator's phantom manifest attestation (F-122, closed by `S187_V1a`), twin manifests in the repo (F-123, retired at this close), a publisher that printed success over a swallowed fatal (F-124, fixed same hour), a state-asserting test broken by the first real reception push (F-125, the fourth firing of the F-106 family), and an installer whose tail died on string-surgery quoting (F-126, now guarded by a whole-file `bash -n` rule). §0–§6 and every prior finding unchanged; §7 index extended F-121 → F-126, full text in the new §7.1 S187 section. Also corrected, visibly: §7's stale *"Next free finding: F-115"* line — it had not been advanced at v2.20/v2.21 while the index rows themselves were current (the F-45/F-108 family, caught by the §2-item-9 agreement check this register itself prescribes).**
**v2.21, Session 186 post-close, 17 August 2026 — F-115 … F-121 appended in one pass: the publish method that could not publish a close-out, and the five defects in the verification chain that the first RED pin run exposed. §0–§6 and every prior finding unchanged; §7 index extended F-114 → F-121, full text in the new §7.1 S186 POST-CLOSE section.**
**v2.19, Session 185, 17 August 2026 — the four owed appends applied in one pass: F-90 … F-95 (S181, never applied), F-100 … F-104 (S183), F-105 … F-106 (S184), F-107 … F-108 (S185). §7's index extended from F-89 to F-108; three new §7.1 continued sections carry the full text. Everything above the new §7 index rows and the new §7.1 blocks is byte-identical to v2.18, apart from this line, the H1, and the two CHANGELOG rows added at the head of the table (v2.19 and the reconstructed v2.18).**
>
> *(v2.18, Session 182, 16 August 2026 — F-96 … F-99 appended to §7.1; everything above that block was byte-identical to v2.17.)*

**Source of truth: `KB_Register` v5.2 (Tier 0 · what is true now) · `KB_History_Archive` v1.28 (Tier 1 · history) · `Diagnostics_Surveillance_System_Spec` v2.3 · `HANDOFF_RUNBOOK` v114 · `CANONICAL_MANIFEST.md`, which is authoritative on which version of each is current. The KB wins on any conflict.**

> *(Source-of-truth line CORRECTED at v2.17. It had read `Clinic_Master_KB_SystemsRegister_v1_58.md` · `Diagnostics_Surveillance_System_Spec_v2_0.md` · `HANDOFF_RUNBOOK_..._Session131_v69.md` — a monolithic KB that **no longer exists** (it split into Register + Archive at **D247**, S147), a Diagnostics spec three versions back, and a runbook forty-five versions back. This is the identical fault §0.2 point 1 raises against v1, recurring. See the v2.17 CHANGELOG row.)*

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

*(This subsection is a Session-131 record. Its "current" figures are S131-era and are preserved
verbatim as history — the live source-of-truth line is the corrected one at the top of this file.)*

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

## §0.35 — D204: THE RESPONDER DOES NOT EXIST, AND IS NOT SCHEDULED *(new in v2.1)*

**D204 (Session 132).** F-24 is answered. **D113 is an intent, not a fact.** The S61 watchman detects and
alerts; it prints `systemctl restart <svc>` inside the alert and **has never run one.** Deliverable 2 is
**unbuilt and unscheduled.** Per **D112**, promotion into Lane 1 is a logged decision, and **no fault has
earned one** — no service here has been observed dying unattended.

> **Every `AUTO→ESC` row below means, today: you are told, and a human restarts.**
> **During an outage, do not wait for a restart. Read the journal.**

The `System does` column throughout §2 is therefore to be read as **`System does — once Deliverable 2
exists`**. Its present tense is a label that misdescribes its contents (**D178**), and it stays only
because rewriting nine tables would risk the procedures they carry. **This paragraph is the label.**

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

> **SEVEN rows below are marked 🔧 RECONSTRUCTED (v2.17, S181), and the seven are not all the same
> kind of gap.** **Six versions — v2.5, v2.7, v2.8, v2.13, v2.14 and v2.16 — each bumped this file and
> left no changelog entry at all**: the **F-45 family**, which this register minted at S149 for exactly
> this fault and which then recurred five more times, including at the version this one supersedes.
> **The seventh, v2.9, is a different case:** a row was present under that number but described
> Session 161, so it has moved to v2.7 where the evidence puts it, leaving v2.9 genuinely empty and
> reconstructed in turn. All seven are rebuilt from evidence, never from memory (**D172**), and each
> cites the artefact it was derived from. **A reconstructed row states what the version recorded, not
> the prose it would have used.** See the reconciliation note under the table.

| Version | Date | Change |
|---|---|---|
| **v2.22** | **18 Aug 2026 (Session 187)** | **F-122 … F-126 appended the same session they were raised — second consecutive close with no owed append.** Five findings: **F-122** (the generator attested to a transient whole-file manifest hash — a phantom minted at every generation — and the checker printed it as VERIFIED; closed structurally by `gen_live_pins.py`/`verify_live_pins.py` v1.2, kit `S187_V1a`: attest the stable CURRENT-row pin, prove it on the box), **F-123** (twin manifests — the `canonical-docs/` copy nine sessions stale yet self-describing as canonical; retired to the attic at this close, renamed, pointer left), **F-124** (`PUSH.bat` printed "pushed" over a swallowed `HEAD.lock` fatal; v2 verifies origin HEAD, and `PUBLISH_ALL.bat` — one whole-repo publisher with every gate — became the default method the same day, proven on its first field run), **F-125** (a state-asserting selftest went RED on the first real medical-PC push; the gate restored perfectly; check scoped to its own bytes and re-rehearsed against the failing condition — the fourth F-106-family firing), **F-126** (an installer tail syntax error after all real work; standing rule: `bash -n` the WHOLE installer before shipping). §7 index extended F-121 → **F-126**; new §7.1 S187 section carries full text; next-free advanced **F-122 → F-127**, and the stale "F-115" next-free line (unadvanced at v2.20/v2.21) corrected visibly. **F-108's agreement check was applied to this append.** No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged — all five are record-integrity, publishing and test-discipline findings. |
| **v2.20** | **17 Aug 2026 (Session 186)** | **F-109 … F-114 appended the same session they were raised — the first close since S181 that leaves this register with no owed append.** Six findings from one session: **F-109** (two characters of a hash invented at the previous fold-in), **F-110** (the live-pin checker held the box to a Register draft that never became canonical), **F-111** (the Register and its generator drifted apart because the generator was never re-run), **F-112** (a bank deposit that never happened, booked into the live books, on a row the record had itself marked unevidenced), **F-113** (a skip that was correct when made and expired unnoticed), **F-114** (a review queue holding lines no human could ever resolve). §7 index extended F-108 → **F-114**; a new §7.1 continued section carries the full text; next-free advanced **F-109 → F-115**. **F-108's own rule was applied to this append:** the next-free number and the last index row agree, and that agreement was checked. **No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged** — all six are process, record-integrity and reconciliation findings, not surveillance codes. |
| **v2.19** | **17 Aug 2026 (Session 185)** | **THE FOUR OWED APPENDS APPLIED IN ONE PASS — F-90 … F-108; the register is current again, and the gap that hid them is now a finding.** Applied: **F-90 … F-95** (S181 — *never applied to this register at all*), **F-100 … F-104** (S183, owed), **F-105 … F-106** (S184, owed), **F-107 … F-108** (S185, new). **§7 index extended from F-89 to F-108 (nineteen rows); §7.1 gains three continued sections** carrying full text for F-90–F-95, F-100–F-104 and F-105–F-108. Next-free advanced **F-90 → F-109**. **ONE version bump, not four:** this file has exactly one final state, and rewriting it three more times to simulate a version per session would be churn rather than provenance — every landed finding is itemised here and each carries its own session label. **F-108 minted from this register's own condition:** §7 read *"Next free finding: F-90"* while F-90–F-95 had never landed and F-96–F-99 sat in §7.1 with no index rows — **the F-45 family recurring**, after v2.17 had reconstructed six instances of it and named the pattern. The bodies for F-90–F-95 are **derived from evidence, never memory (D172)** — the KB Register v5.5 findings index, the v5.3 lineage row and Runbook v115/v117 — and state what the record held, not prose it never used. **No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged** — none of the nineteen is a surveillance code; they are process, security, install-integrity, reconciliation and record-keeping findings. |
| **v2.18** 🔧 | 16 Aug 2026 (Session 182) | *RECONSTRUCTED at v2.19.* **§7.1 extended — F-96, F-97, F-98 (CLOSED), F-99 recorded** as full-text blocks (the session that proved Phase 0 against git bytes and shipped the clinic portal tiles; full text also in KB History Archive §S182). **This bump left no CHANGELOG row of its own — the F-45 family, one version after v2.17 reconstructed six instances of it and named it.** It also added no §7 index rows for the four findings, which is half of **F-108**. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: this file's own §7.1 "(continued) — S182 · F-96 … F-99" section; KB Register v5.4 lineage row; CANONICAL_MANIFEST §S182 block pinning v2.18 at `ff0f020a3b645cbfa65400a51448cf0f`.* |
| **v2.17** | **15 Aug 2026 (Session 181)** | **THE THREE OWED APPENDS APPLIED — F-82 … F-89 merged; the register is current again.** This file had been carrying three unapplied appends for nine sessions, blocked from S180 only because the register itself was unreachable at Phase 0; it was **recovered by hash-search from the S171 cold kit** at the S180 close (md5 `1702b5a8e0663847eaa097919aea94d3`, matching its pin exactly) and all three could finally land. Merged: **F-82 + F-83** (owed since S172/S177), **F-84** (S179), **F-85 … F-89** (S180). **§7 index extended by eight rows; new §7.1 carries all eight findings' FULL TEXT verbatim** — the appends were full-text blocks, and §7's index-plus-Archive-pointer pattern would otherwise have discarded the text this register was handed. Next-free advanced **F-82 → F-90**. **SOURCE-OF-TRUTH LINE CORRECTED** (top of file): it had cited `Clinic_Master_KB_SystemsRegister_v1_58.md` — a monolith that **ceased to exist at D247/S147**, when the KB split into Register + Archive — plus Diagnostics v2.0 (now v2.3) and Runbook v69 (now v114). **This is §0.2 point 1's own fault, recurring**: v2.0 corrected a twenty-five-version-dead source line, and it went dead again by a restructure and forty-five runbook versions. §0.2 is preserved verbatim as the S131 record, so its "current" figures are historical, not live. **SEVEN CHANGELOG ROWS RECONSTRUCTED** — six that were never written (v2.5, v2.7, v2.8, v2.13, v2.14, v2.16 — the F-45 family recurring five times after this register minted it), plus v2.9, freed when a mislabelled row moved to the version the artefacts actually place it at. See the 🔧 rows and the reconciliation note below. **No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged** — not one of the eight new findings is a surveillance code; they are process, security, privacy, install-integrity and backup-discipline findings. |
| **v2.16** 🔧 | 12 Aug 2026 (Session 171) | *RECONSTRUCTED at v2.17.* **§7 extended — F-76 (WITHDRAWN), F-77, F-78, F-79, F-80 (all CLOSED) and F-81 (OPEN) recorded** (the session that finished the D297 console: acceptance sweep signed off, nine live installs across three files, D306–D308; full text KB History Archive §S171). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: KB Register findings index — "Full text: Fault Register v2.16 + Archive §S171"; the six F-rows themselves are present in §7 of this file carrying the S171 label.* |
| **v2.15** | **Session 170** | **§7 extended — F-75 recorded** (D297 console rev5 build-out session; full text KB History Archive §S170). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.14** 🔧 | 11 Aug 2026 (Session 168) | *RECONSTRUCTED at v2.17.* **§7 extended — F-74 recorded** (D297 Stage B1 `/portal/console` page + Stage-2a agent backfill; full text KB History Archive §S168). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: KB Register findings index — "F-65–F-74 indexed in the v2.8–v2.14 Fault Registers / Archive §S162–§S168"; F-74 carries the S168 label in §7; Archive §S168 header confirms the date.* |
| **v2.13** 🔧 | 11 Aug 2026 (Session 167) | *RECONSTRUCTED at v2.17.* **§7 extended — F-72, F-73 recorded** (D297 Stage A console.db spine built; full text KB History Archive §S167). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: the same v2.8–v2.14 / §S162–§S168 span; F-72 and F-73 carry the S167 label in §7; Archive §S167 header confirms the date.* |
| **v2.12** | **Session 166** | **§7 extended — F-71 recorded** (D297 design/vetting session; full text KB History Archive §S166). F-71 = an uploaded follow-up-tracker zip carried PHI + `.secret_key`/`.env` (kin F-56); code-only read, nothing committed, rotation check owed. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.11** | **Session 165** | **§7 extended — F-69, F-70 recorded** (D223 gist-tile build session; full text KB History Archive §S165). F-69 = `Call_Feed` dead since Apr (writer stopped); F-70 = Callback Tracker Core Dossier lags the live Sheet (diagnosis column + tab inventory). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.10** | **Session 164** | **§7 extended — F-67 CLOSED, F-68 recorded** (salary coverage fix + pending-review board + Shivani maker + portal user admin session; full text KB History Archive §S164). F-67 fix shipped (coverage keys off `day_review` approved capture, D291); F-68 = same-origin-proxy pattern for cross-app widgets. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.9** 🔧 | 10 Aug 2026 (Session 163) | *RECONSTRUCTED at v2.17.* **§7 extended — F-66, F-67 recorded** (D288 executed: standalone register salary proven to the rupee for July; register-owned EARLY-BIG rulings shipped; full text KB History Archive §S163). F-66 = WinSCP put the wrong bytes under a filename twice, caught by the md5 gate; F-67 = salary coverage keyed off the wrong table (latent under-deduction, fixed S164). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: the v2.8–v2.14 / §S162–§S168 span; F-66 and F-67 carry the S163 label in §7; Archive §S163 header confirms the date.* **See the reconciliation note below — a row previously carrying this version number described Session 161.** |
| **v2.8** 🔧 | 09 Aug 2026 (Session 162) | *RECONSTRUCTED at v2.17.* **§7 extended — F-65 recorded** (Stage-B salary APPROVE & LOCK; biometric grid; D288 consolidation directive; full text KB History Archive §S162). F-65 = a new SQLite table needs the app's `--init` **before** restart, or the page that queries it 500s. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: KB Register findings index — "F-65–F-74 indexed in the v2.8–v2.14 Fault Registers / Archive §S162–§S168"; F-65 carries the S162 label in §7; Archive §S162 header confirms the date.* |
| **v2.7** 🔧 | 09 Aug 2026 (Session 161) | *RECONSTRUCTED at v2.17.* **§7 extended — F-64 recorded** (Staff Register onboarding features + Salary Engine Stage A; the C-model salary policy locked, D272–D282; full text KB History Archive §S161). F-64 = `staff_ledger.py`'s code and data directories are different places; a same-named dir next to a module is not the module's location. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from **two independent statements in Archive §S161**: its Phase 0 records the entering set as `Fault_Action_Register v2.6` (`6e90861e…`), and its F-64 entry ends "(Full text also in Fault Register **v2.7** §7)" — so S161 entered at v2.6 and closed at v2.7.* |
| **v2.6** | **Session 160** | **§7 extended — F-62, F-63 recorded** (Case Pack → VPS decision + portal health-tiles/layout session; full text KB History Archive §S160). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.5** 🔧 | 08 Aug 2026 (Session 159) | *RECONSTRUCTED at v2.17.* **§7 extended — F-59, F-60, F-61 recorded** (portal Group D + personal tiles + GMB moved to the VPS; full text KB History Archive §S159). F-59 = Chrome refuses ports 5060/5061 as ERR_UNSAFE_PORT; F-60 = the VPS filesystem is case-sensitive; F-61 = a pasted fence label broke `portal_config.py`. No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. *Derived from: KB Register findings index — "Full text of all three: Fault Register **v2.5** + Archive §S159"; all three carry the S159 label in §7; date from the KB Register version-lineage row v3.2 · S159 · 08 Aug 2026.* |
| **v2.4** | **Session 158** | **§7 extended — F-57, F-58 recorded** (SSO-portal build + Notion catch-up session; full text in KB History Archive §S158). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.3** | **Session 157** | **§7 extended — F-54, F-55, F-56 recorded** (documentation/design session; full text in KB History Archive §S157). Title line corrected v2.1→v2.3 (it had lagged behind the v2.2 body — the F-45 title-lag family). No surveillance fault code, lane, procedure or rule added or altered; §0–§6 unchanged. |
| **v2.2** | **Session 156** | **§7 added — a Later-Findings index (F-45..F-53)** so the register is aware of the process/build findings minted from S149 on (full text lives in the KB History Archive per that era's pattern). **F-51/F-52/F-53 recorded** (S156). No surveillance fault code, lane, procedure or rule was added or altered; §0–§6 are unchanged from v2.1. |
| **v2.1** | **Session 132** *(row backfilled S149 per F-45; the v2.1 bump left no changelog entry — the same stale-record family caught at v1.71/§S131/§S143. Day not re-derived from the artefact; session is verified: D204 = S132)* | **§0.35 added — D204 (Session 132): F-24 is answered.** The Lane-1 auto-responder **does not exist and is not scheduled**; **D113** ("the S61 watchman IS the Lane-1 responder") is reclassified as **intent, not fact**. The watchman prints `systemctl restart <svc>` inside its alerts but **has never run one** — Deliverable 2 is unbuilt, and per **D112** no fault has earned Lane-1 promotion. So every `AUTO→ESC` row reads, today: *you are told, and a human restarts; during an outage do not wait for a restart — read the journal.* The `System does` column is relabelled **"System does — once Deliverable 2 exists"** (**D178**: its present tense misdescribes its contents). **No lane, procedure or rule was altered; §1–§6 are unchanged from v2.0.** |
| **v2.0** | **09 Jul 2026 (Session 131)** | **RE-BASED, self-contained, status-true.** **Not retired** — `D114` makes this the single brain for response, and Session 131 confirmed it after nearly retiring it without reading D114. **D203** states the writer boundary: Diagnostics *defines and detects* a fault code; this register *lanes* it; neither restates the other. **F-24 raised:** v1's §2.1 described an auto-responder (`systemctl restart …`) that **does not exist** — the live watchman is read-only and *"never starts/stops/changes a service."* Every table now carries a status marker; **not one row is 🟢.** Source-of-truth line corrected (was KB v1.30 · Diagnostics v1.4 · Runbook v42 — twenty-five versions dead). **§2.5 added:** the six `CALLHOOK_*` codes, detected since Session 125 and never laned. §5's Q1 and Q2 **closed** by what shipped (09:00 IST; ntfy + Gmail). **§1, §2.1–§2.4, §3, §4 and §5 are reproduced verbatim; no rule, lane or procedure was altered.** |
| v1 | 04 Jul 2026 (Session 63) | First draft. Two lanes, the register, the six sturdiness rules, the build order, three open questions. Its header said *"nothing here is built or armed yet"* while its body marked three detectors LIVE. |

### CHANGELOG reconciliation note (v2.17, S181) — one conflict, left visible

**The row that used to read `v2.9 | Session 161 | F-64` was carrying the wrong version number, and
its content now sits at v2.7.** Two independent statements inside **Archive §S161** — a session
narrative written at that close, not from memory — establish it:

1. §S161's Phase 0 records the **entering** canonical set as `Fault_Action_Register` **v2.6**
   (`6e90861e…`). A session that enters at v2.6 cannot close at v2.9 without two silent extra bumps.
2. §S161's F-64 entry ends: *"(Full text also in Fault Register **v2.7** §7.)"*

Against that, the only evidence for "v2.9 = S161" was the changelog label itself. **A label is not
provenance (D188), and a check's expected value is derived from the artefact, never predicted from
memory of it (D172)** — so the artefact wins, the row moved to v2.7, and the genuine v2.9 (Session
163, F-66 + F-67) has been reconstructed into the gap it left.

**What is NOT claimed here.** The reconstructed rows state *which findings each version recorded* and
*what session and date it belonged to*, because those are evidenced. They do **not** reproduce the
prose those rows would have carried — that text was never written and is not recoverable. **The
correct entry is sometimes UNKNOWN (D166)**, and where a row says only "§7 extended — F-## recorded",
that is the whole of what the evidence supports.

**No F-number was spent on this.** The recurrence of the F-45 family across six versions is recorded
here and flagged to the owner; minting it as a finding remains the owner's call. Next free finding
stays **F-90**.

---

## §7 — LATER FINDINGS INDEX (F-45+, recorded in full in the KB History Archive)

Findings from S149 onward are minted and described in full in their session's Archive `§S###` block; this index keeps the register aware of them. They are process/build/discipline findings, not new surveillance fault codes, so they add no lane or detector here.

**From F-82 onward the full text also lives in this file, at §7.1** — those findings arrived as
standalone append blocks and the text is carried rather than discarded.

| F-## | Session | One line | Full text |
|---|---|---|---|
| F-45 | S149 | Fault-Register v2.1 bump left no CHANGELOG row (stale-record family) — backfilled | Archive §S149 |
| F-46 | S151 | Salary column printed in-chat (header-keyed mask beaten by a title row) → whitelist-only mask rule | Archive §S151 |
| F-47 | S153 | Double-punch artefact: arrival double-punch, no out-punch — classify pairs before money math | Archive §S153 |
| F-48 | S153 | Shadow-write / diff-audit rule for owner-side workbook edits | Archive §S153 |
| F-49 | S154→S155 | Salary CSV in the git working tree → blanket `*.csv` gitignore IS the gate (CLOSED by ruling S155) | Archive §S154/§S155 |
| F-50 | S155 | Derived-everything role powers (`list(CATEGORIES.keys())`) → **a role's powers are an explicit allow-list**; every power-set gets a negative selftest | Archive §S155 |
| **F-51** | **S156** | One-tap irreversible ledger appends (contra/skip) → confirm step + void-pair display; **fixed same session** | Archive §S156 |
| **F-52** | **S156** | Repo copy of a live op-script silently stale vs the VPS (gutlog missing) — **build from the md5-verified live copy, never the repo mirror** (reinforces D160) | Archive §S156 |
| **F-53** | **S156** | Compile/selftest on a NEWER Python than the deployment target proves nothing — **VPS-Python (3.11) compile + selftest mandatory before delivery** | Archive §S156 |
| **F-54** | **S157** | `App_Service_Register_v1` carried a 07-Aug file date over **Session-63-era** content (missing the asset app, staff-ledger, the salary stack) — a "date/filename is not provenance" trap (D188); reconcile against the live KB/manifest, not the artefact that looks current | Archive §S157 |
| **F-55** | **S157** | The `drmanoj-clinic-automation` **GitHub JSON repo-dump is partial** — the export tool truncated (binary `attendance.zip` ate the budget), silently omitting `staff_ledger`, `wa-diagnostics`, `revenue-reconciliation`, `plan-tool`; use the **live repo** (codeload tarball / raw), never a dump assumed complete | Archive §S157 |
| **F-56** | **S157** | Uploaded PC "code" zips carried **live credentials (GCP service-account key, `.env`, `.secret_key`) + PHI + F-31 salary data** even after "most data files" were deleted → sanitize whole `data/`/`output/`/archive dirs + keys before aggregating anything for reuse; **the service-account key that rode through must be ROTATED** | Archive §S157 |
| **F-57** | **S158** | Notion catch-up scope taken from OUR records (claimed S150) not the live target (actually S147) — the real gap was S148–S156. **Scope a catch-up from where the external system actually is**, not from where we think we left it (reinforces D188/D260). (The 7-session "Notion absent" streak also had a mechanical cause: connector toggled OFF per-chat.) | Archive §S158 |
| **F-62** | **S160** | “Audit the artefact, not the label” — a doc filed **Surgical Case Pack** as “Website/SEO”, hiding that it is a **local PHI store** (case bundles+consents+ledger, off-Drive by design). Classify a component from its CODE/data-flow, not a doc's category tag (kin D188/F-54). | Archive §S160 |
| **F-63** | **S160** | The portal **`pc`-NameError reached production** — `py_compile` + an isolated Jinja render both passed, but the **wired route was never exercised** (the name existed only as a render kwarg). DELIVERY GATE for any live Flask change: a **test-client hit on the ACTUAL route** (200 + expected content), not just compile + isolated render. | Archive §S160 |
| **F-64** | **S161** | Reusing live code from another app: `staff_ledger.py` **code** lives at `/root/staff_ledger.py` while its **data** dir is the separate `/root/staff_ledger/` — importing the ledger's `compute_salary` from the register app required adding `/root` **and** `/root/portal` to `sys.path` (guarded). A same-named dir next to a module is not the module's location; put the module's parent on the path. Diagnosed via a `ModuleNotFoundError` surfaced by a temporary error-carrying module global. | Archive §S161 |
| **F-58** | **S158** | Flask's **test client ignores a manually-set `Cookie` header** (it manages its own cookie jar) — a valid SSO token gave a false-negative auth until switched to the client's `set_cookie` jar. Smoke-test cookie auth via `set_cookie`/`test_request_context`, never a raw header. | Archive §S158 |

| **F-59** | **S159** | Chrome refuses ports **5060/5061 (SIP)** as **ERR_UNSAFE_PORT** from every context (address bar or tile); `curl`/CLI ignore the restricted-port list, so the server looks healthy while the browser fails. Avoid Chrome's restricted ports for localhost tiles; when curl works but the browser won't open, suspect ERR_UNSAFE_PORT first. | Archive §S159 |
| **F-60** | **S159** | VPS filesystem is **case-sensitive**: `GMB.html` ≠ `gmb.html` — a path-based read fails with the app's own "not installed" message though the file is present. The filename's case must match what the code opens (kin of D188). | Archive §S159 |
| **F-61** | **S159** | Pasting a fenced code block's **language label** (```` ```python ````) into a live config put a bare `python` token in `portal_config.py` → `NameError` → whole config unreadable → portal "Setup needed" (secrets intact). Paste only lines BETWEEN the fences; diagnose a sudden "unconfigured" via `python -c "import portal_config"`. | Archive §S159 |

| **F-65** | **S162** | A new SQLite table needs the app's `--init` (migration) run **BEFORE** `systemctl restart`, or the page that queries it 500s. The Stage-B lock page queries `locked_run`; installing the code without `--init` → table missing → 500. Standing rule: when a delivery adds/alters a table, run `--init` before restart AND md5-check the file so a truncated/placeholder copy is caught. (First miss's root cause: a literal `PYBIN` placeholder in the runbook meant the venv `--init` never ran — always paste the real `/root/wa/venv/bin/python3`, never a placeholder.) | Archive §S162 |
| **F-66** | **S163** | **WinSCP silently put the WRONG bytes under a filename — twice** — during the S163 install: the "salary engine" was uploaded but the local save was actually `staff_register.py`, so `salary_engine.py` on the VPS held the register file (`md5 = ded3ae8f…`, the register's hash) though its name looked right; a later `mv`/upload shuffle also **deleted the live `staff_register.py`** (service went to `activating`/down). The **md5 gate caught the wrong bytes before any restart**, and both files were restored from the `.bak-S163eb` timestamped backups — no mis-paid run, contained downtime. Standing discipline reinforced: (a) **always keep a timestamped backup before install** (`cp file{,.bak-SNNN}`), it is the instant rollback; (b) **upload with a `.new` suffix, md5-verify the file IN PLACE, then `mv` into position** — never overwrite a live file with unverified bytes; (c) a filename is not provenance (D188) — trust only the hash. | Archive §S163 |
| **F-67** | **S163** | **Coverage detection keys off the wrong table.** `salary_engine.load_register()` sets `covered = (daily_register rowcount > 0)`, but `daily_register` only holds EXCEPTION rows — a month the register genuinely captured (day_review approved daily) but with zero logged exceptions would be mis-flagged **uncovered**, skipping the C-model base÷30 cuts on genuine absences (an under-deduction). The correct signal is **day_review capture** for the month, not exception rows. Latent (August is currently uncovered for a legitimate reason — no daily entry yet), but MUST be fixed before any register-captured month is paid. Fix + selftest were the S164 top task. **CLOSED S164 (D291):** `covered` now keys off `day_review` `status='approved'` capture (not exception rows); `salary_engine.py 5514918067243e3f39e7074144ee7db4`, selftest **CASE E** added, July parity re-verified ₹1,07,447. | Archive §S163/§S164 |

| **F-68** | **S164** | **Cross-origin credentialed fetch through OpenLiteSpeed is fragile.** The portal Staff-Register tile fetched the register's `/register/review/counts` from the browser and got nothing — OLS's reverse proxy strips/omits the `Origin`/CORS headers a credentialed cross-origin `fetch` needs, so the browser blocks the response. Pattern: don't fetch another app's origin from the browser — add a **same-origin proxy** on the calling app that server-side calls the target over localhost (here portal `GET /portal/review-counts` → `REGISTER_COUNTS_URL` = `127.0.0.1:8044/register/review/counts`, SSO cookie forwarded, 2s timeout, empty `{}` on failure). Apply to any future cross-app widget. | Archive §S164 |

| **F-69** | **S165** | **`Call_Feed` dead since 28 Apr 2026.** While binding the gist's call-volume source, `Call_Feed` (the name-free feed the Follow-Up Tracker reads; written by `CallField`/`CallFeed.gs`) was found frozen at April — 2,971 rows, newest 27–28 Apr, **0 today** — its writer stopped ~3.5 months ago. Volume was rebound to the live `Call_Durations` (1,648 rows, 79 today; `category` incoming/obd, window `ended_at_ist`, probe excluded). The Follow-Up Tracker reads `Call_Feed`, so its incoming/outgoing reconciliation is likely silently degraded since April — find and restart the `Call_Feed` writer. | Archive §S165 |
| **F-70** | **S165** | **The Callback Tracker Core Dossier lags the live Sheet (doc-not-provenance, D160/D188).** The dossier frames diagnosis as Docterz-side, but `Patient_Master` carries a live **Diagnosis** column (present for most patients) and `Followups_Today`/`Followup_Escalations` carry it too — the console's diagnosis column is buildable now, not Docterz-blocked. The dossier also lacks the real tab inventory (there is **no** "Escalations" tab; 3rd-strikes live in `K_Strikes.Tries`; the Sheet has 19 tabs incl. `Daily_Summary`, `Agents`, `Followup_Outcomes`). Owner corrected the assistant from the live Sheet. Dossier update owed. | Archive §S165 |

| **F-71** | **S166** | **An uploaded PC zip carried PHI + secrets (kin F-56).** The `followup_tracker.zip` shared to ground the D297 conversion/no-show design included `patient_master.csv`, `patient_diagnosis.csv` (PHI), revenue ledgers, and `.secret_key` + `.env` (secrets). Handled correctly: **code-only** extraction, **nothing committed** to any repo or kit, **no data printed** (numbers masked in chat). Standing rule reinforced: PC uploads must be **code-only** (drop `data/`). **Action:** treat the shared `.secret_key`/`.env` as potentially exposed → rotation check (kin F-56 service-account-key rotation). | Archive §S166 |

| **F-72** | **S167** | **Mixed tz-aware/naive datetime subtraction crashed the console builder.** `portal_console.py`'s first live dry-run died in `build_latency` — `TypeError: can't subtract offset-naive and offset-aware datetimes`: one timestamp column parses tz-aware (an ISO string carrying `+05:30`), another naive, and subtracting the two raises. Fix: `parse_ts` strips `tzinfo` so every parsed time is one **naive IST wall clock** (all sources are IST); a genuine cross-zone source would then surface as a ~constant offset in the latency stats, not a silent wrong lag (F-41 lineage). RULE: normalise datetimes to one tz stance before arithmetic; unit-test with an aware+naive mix. | Archive §S167 |
| **F-73** | **S167** | **Two live files disagreed on the MyOperator `/search` `status` vocabulary.** `Netting.gs`/`MyOperator.gs` (which produce `Daily_Summary`) read `status` as **numeric** (`status==2`=missed); the VPS sibling `flag_investigator.py` reads it as **strings** (`"missed"/"voicemail"/"bridged"`). Encoding the A2b reconcile on the wrong one would silently mis-count net-missed. Resolved by a **read-only live probe** (`--myop-probe`): the API returns numeric `status` `{1,2}` + `event` `{1,2}` — **numeric wins**; `Netting.gs` is authoritative. RULE: when two live sources disagree on a field's encoding, PROBE the live source before encoding a rule — do not pick by the file's recency or apparent authority (kin D160/D188). | Archive §S167 |

| **F-74** | **S168** | **Console call-count inflation from a one-to-many LEFT JOIN fan-out.** The first `/portal/console` render showed impossible totals (Incoming **2276** > all-calls **1651**): `LEFT JOIN verdicts` multiplied each call row by its verdict count (a re-judged call carries several — **2195** verdicts across **1651** calls), and `LEFT JOIN patients` compounded it. Fix: collapse each child to **one row per key BEFORE joining** — dedup subqueries `_DV` (verdicts: `MAX(id)` per `join_key` → newest wins) + `_DP` (patients per `phone10`); counts then reconcile (each dimension sums to the spine total). Caught in the browser at first build — nothing downstream had consumed the wrong numbers, so no incident. RULE: never `LEFT JOIN` a one-to-many child straight into a counted spine — reduce it to one-row-per-key first, and sanity-check that a dimension's parts sum to the spine. | Archive §S168 |
| **F-75** | **S170** | **`portal_console.py --build` is WINDOW-SCOPED and ATOMIC-FROM-SCRATCH — a small `--days` scheduled run silently destroys the wide-window layers every fire.** Observed at the Item-1 cron gate: a dry-verify `--days 3` run rebuilt `console.db` whole and shrank `call_agent` **1001 → 60** and reverted net-missed-open **108 → 152** — the Stage-2a attribution and the MyOperator correction only ever cover the pulled window, and there is NO incremental mode. Had the punch-list's assumed light cron been armed blind, the console would have shredded its own back-catalogue every 10 minutes while *looking* fresh. Caught because the gate ran the exact scheduled command once by hand and compared artefacts before arming (the F-41 instrument, applied forward). FIX (D303): the scheduled job is ALWAYS the full `--days 60 --with-myop-reconcile --with-transcripts` build (~32 s) under a mandatory `flock -n`. RULE: before arming any schedule, run its exact command once and diff the artefact's key invariants (row counts, watermarks) against the pre-state — a fresh timestamp alone proves nothing about what the run preserved. | Archive §S170 |

| **F-76** | **S171 · WITHDRAWN** | Builder's Google SA is read-only → `Dr_Manoj_Call_List` sheet write 403 (caught by the acceptance sweep — offline selftests never exercised the live write scope: a check that cannot fail is not a check). WITHDRAWN by **D306**: the scope is NOT widened; `console_reviews.db` on the VPS is canonical, the sheet push is removed as dead code, Drive becomes nightly-backup-only. | Archive §S171 |
| **F-77** | **S171 · CLOSED** | The training CSV `/portal/console/reviews.csv` downloaded empty / Excel-hostile; fixed with a **UTF-8 BOM** + route hardening, re-verified live. | Archive §S171 |
| **F-78** | **S171 · CLOSED** | `build_no_shows` sliced the feed's `DD-Mon-YYYY` due date with `[:10]` — a correctness bug wearing a cosmetic face: the due-vs-today lexical gate AND the calls-since-due SQL boundary were computed against the wrong format (columns unreliable, not just a chopped year). Fix: parse to ISO at build; format for humans only at display. RULE: never slice a date string by length — parse it. | Archive §S171 |
| **F-79** | **S171 · CLOSED** | A stale `details.callrow>summary{…flex…}` rule sat LATER in the stylesheet than the new grid rule — rows silently fell back to flex while headers rendered grid (the "headers don't match rows" defect). **CSS cascade regressions are invisible to string-assertion gates.** Cure: DELETE the stale rule (not out-specificity it) + the F-63 gate now asserts on the SERVED HTML, including the ABSENCE of known-stale rules (**D307c**). | Archive §S171 |
| **F-80** | **S171 · CLOSED** | gspread **6.x** `Spreadsheet.client` returns an HTTPClient WITHOUT `open_by_key`; the resulting AttributeError was swallowed by a broad except → patient enrichment reported `found=False` forever while looking like a share problem. Fix: open the enrich sheet via the base `gc` client inside `_open_clients`. RULE: never let a version-sensitive attribute path fail silently — fail loud or probe it (kin F-73). | Archive §S171 |
| **F-81** | **S171 · OPEN** | **Duplicate call rows in the live log** — same phone/time/duration appearing twice (e.g. 16:51:55 ×2, 16:50:19 ×2). Suspected MyOperator `/search` reconcile double-insert in the builder. Displayed honestly, not hidden (D236). **Builder-side investigation owed** (dedupe on a natural key or prove two genuine legs). | Archive §S171 |

| **F-82** | **S172 · OPEN (VENDOR)** | MyOperator WhatsApp Developer API returns **HTTP 500 `{"message":null}` on ALL authenticated calls** — reads and sends alike, from two independent code paths on the identical token. An unauthenticated call correctly returns 401, so the API is up and the token passes the auth gate; only **account resolution** fails → vendor-side provisioning. **WABA go-live blocked.** Escalated to Khushi + Lokesh; `PORTAL_WA_DRYRUN` returned to `"1"`. When restored: flip DRYRUN→`"0"`, restart, self-send to the doctor's own number — **no code change.** | **§7.1** + Archive §S172 |
| **F-83** | **S176 · OPEN (mitigated)** | **Asset-app intake background OCR thread is fire-and-forget** — it dies on service restart and skips non-draft bills, so a read can be lost with no visible trace (why bill B-0001 arrived blank). Mitigated LIVE by **A-D23**: visible `ocr_status`, a non-clobber "Re-read with Sarvam" button, and a server-enforced confirm when approving blank fields. **Durable fix owed** (queue + worker, or synchronous extract with a bounded timeout) — A-D25 candidate. | **§7.1** + Archive §S176 + `KB_Asset_Register` §7 |
| **F-84** | **S179 · FIXED** | **Three self-found security faults in the finance module, all the same shape — an offline-testing convenience carried into production.** (1) reads ungated → fail-closed `before_request` allow-list; (2) identity from spoofable `X-Clinic-*` headers in prod (full control, not a leak) → signed SSO cookie authoritative, header auth opt-in only, *signed-in ≠ entitled*; (3) the SSO epoch never checked → "sign out everywhere" did not revoke here → read live and fail closed, `healthz` surfaces `sso_epoch_ok`, installer auto-rolls-back. **THE LESSON: the offline-testing shortcut WAS the vulnerability.** Extends F-63/F-68. | **§7.1** + Archive §S179 |
| **F-85** | **S180 · CLOSED by correction** | **A session number was assigned by anticipation instead of by close-out.** A document headed "Session 181" was written before the S179 close-out had run; the error propagated forward one more session. Two documents carried wrong numbers and a third nearly did. **RULE: a session number is assigned by a close-out, never by anticipation.** Kin D188, F-54. | **§7.1** + Archive §S180 |
| **F-86** | **S180 · FIXED before install** | **A reader for a PHI source emitted full phone numbers, because it was written against the source's shape rather than the destination's rules.** `marg_report.py` carried the full 10-digit number into its CSV; `patient_ref` stores `phone_last4` and nothing more, and `ingest_column_map` has no phone field at all — exposure with no purpose. Now `phone_last4` only; the item CSV carries no patient identity; outputs grepped for any 10-digit string. **RULE: the destination's constraints are part of the specification.** Kin F-31/F-49, F-46. | **§7.1** + Archive §S180 |
| **F-87** | **S180 · HIGH (process) · remedied by an asset** | **A change was shipped twice to a test suite that could not be run offline** — `finance_app.py`'s smoke is written against the real store, so it would not run here, and the change went on reasoning alone. It broke two assertions on the box; the install gate rolled it back correctly. **This is F-84's own lesson repeated after this project had already minted it.** Two traps now written into the code: `ingest_day` **supersedes and deletes** the day's previous batch, and resolving a queued line **adds** a `sale_item` an earlier check counts. **The remedy is an asset: `dev_seed_smoke_db.py` + differential verification** (baseline vs modified on identical seeded data). **RULE: if a test suite cannot be run, making it runnable is the FIRST task.** | **§7.1** + Archive §S180 |
| **F-88** | **S180 · FIXED** | **A passing `md5sum -c` proved a kit internally consistent, not current.** Two install attempts ran an older download; a stale kit's checksums match its own files perfectly, so the hash gate silently permitted the wrong build twice. Fixed: the installer carries the **identity of the build it belongs to** (`KIT` name + expected md5 of the file that actually changed), checks it first, and refuses otherwise; re-issued kits take new folder/zip names. **RULE: a checksum proves integrity, never currency.** Kin D188, F-66. | **§7.1** + Archive §S180 |
| **F-89** | **S180 · HIGH · cause corrected, loss permanent** | **The cold-backup cadence lapsed for nine sessions, and three canonical documents were lost.** 26,745 files were hashed across the owner's drives (by md5, not filename); four rows recovered, three gone — `KB_Asset_Register` v1.11.0 (Tier-1 CURRENT), `KB_Register` v5.0, `KB_History_Archive` v1.26 — all **S177–S178 outputs, created nine sessions after the last cold kit (S171)**. Every document that *was* recovered came from a backup mechanism that had actually run. **The loss was not caused by the Phase 0 that found it; Phase 0 is the only reason anyone found out.** Restored at the S180 close (`KB_S180_close.zip`). **RULE: the cold kit is not discretionary — it carries a session count, checked at every close.** Consequence recorded under **D316**. | **§7.1** + Archive §S180 |

| **F-90** | **S181 · RULED (D320)** | **The GitHub repository is PUBLIC.** Raised at S181 with visibility UNKNOWN; **proven public at S182 by an anonymous clone**, which converted the suspicion into a fact and answered F-9's long-open question. Recommendation at the time: private + read-only deploy key. **Ruled at S182 (D320):** the repo stays public, knowingly, with the binding corollary that no PHI-bearing artefact may enter it. | **§7.1** + Archive §S181 |
| **F-91** | **S181 · OPEN (behavioural)** | **UPI is recorded as Cash at Docterz entry** — ₹17,900 over six weeks. **Invisible to any ledger-internal check**, because the books are internally consistent either way: only a comparison against the bank exposes it. The typed daily tab is the reconciliation anchor. The fix is the reconciliation workbench (Marg ⋈ bank ⋈ entry, cash→UPI suggestions graded like D315 and never auto-applied), designed at S184. Its shape reappeared in the pharmacy at S182 — two 100%-cash Marg days, ₹38,355 — and was settled at S183 as a Marg UPI-recording gap, bank-confirmed. | **§7.1** + Archive §S181 |
| **F-92** | **S181 · OPEN** | **Discount capture stopped on 18 Jun 2026** — ₹1,33,720 recorded up to that date, then zero. Concessions are still being given; they are simply no longer valued anywhere. Part of an 18–19 Jun regression cluster. | **§7.1** + Archive §S181 |
| **F-93** | **S181 · OPEN** | **The concession parser swallows the Docterz footer**, manufacturing three fake "patients" a day in the staff-facing sheet. Cosmetic in money terms, corrosive in trust terms — a staff-facing report that visibly contains nonsense trains people to ignore it. | **§7.1** + Archive §S181 |
| **F-94** | **S181 · CLOSED by D317's rules** | **An installer's environment assumptions are part of its specification.** The C1a/C1b/C1c red trilogy: three consecutive installer reds, each caught by a gate with nothing half-installed, each traced to an assumption about the target environment that the kit had never stated. Closed by the D317 kit-chain rules rather than by a code fix. | **§7.1** + Archive §S181 |
| **F-95** | **S181 · CLOSED by rules** | **A synthetic store proves logic, not life.** Smoke checks must print what they actually saw; invariants must be asserted as invariants; and an offline store must be enriched with live-shaped data before a first live gate is attempted. Kin of F-87 (a test suite that cannot be run) and F-106 (a test that freezes a data state). | **§7.1** + Archive §S181 |
| **F-96** | **S182 · RULED (D320)** | **The canonical set is PHI-bearing in a public repository** — 7 unmasked patient mobiles, ≥2 patient names and 1 clinic patient ID across 48 files. **A passing 48/48 conceals it:** the check proves integrity and says nothing about whether the content belongs there at all. F-88 one level up. | **§7.1** + Archive §S182 |
| **F-97** | **S182 · STRUCTURAL FIX SHIPPED S183 (D321)** | **Phase 0 verifies documents; nothing verified the Register's live-code pins.** `portal.py` was pinned `da417709…` while the box ran `34f038a765…` — stale by two sessions, with the repo agreeing byte-for-byte with the stale pin. A full-file replacement would have deleted two live finance tiles with every gate passing. Fixed structurally at S183 by `verify_live_pins.py` (D321). | **§7.1** + Archive §S182 |
| **F-98** | **S182 · CLOSED (S182_P2a)** | **The SSO broker treated a trusted device with no SSO session as *the doctor***, reaching every `@doctor_required` surface. F-84's pattern in the front door. Fixed keyed to `_sso_ready()` so D264's inert-on-failure invariant survives. Also the cause of the "missing tiles" report — with no identity, every grant-only tile vanishes. | **§7.1** + Archive §S182 |
| **F-99** | **S182 · OPEN** | **A missing-day alarm anchored on `MIN(business_date)` cannot see a unit that never files a first day** — "not started" and "gone dark" are indistinguishable. Medical was seeded with 121 legacy days and never hit it; clinic is the first unit to start empty, and lab will hit it too. *(Partly relieved at S184 by D322's holiday classifier, which stops Sundays and clinic holidays from being owed at all — but the zero-anchor blind spot itself remains.)* | **§7.1** + Archive §S182 |
| **F-100** | **S183 · CLOSED same session** | **`push_kit.bat` reported "pushed successfully" while git had silently dropped a kit file.** The pin list was named `live_pins.tsv`; `.gitignore` carries a blanket `*.tsv` (a PHI guard — F-31/F-49, D320), and `git add <folder>` says nothing about ignored files inside it. The published kit was incomplete and surfaced only as a SUMS refusal at the VPS console. **The publishing record claimed a file that was not there — F-97's shape one layer up the toolchain.** Fixed by renaming to `.txt` (**no hole punched in `.gitignore`**) + `push_kit.bat` **v4**, which lists any excluded file with the rule that excluded it and REFUSES to commit. **RULE: a publishing step that cannot prove it published everything has not published anything.** | **§7.1** + Archive §S183 |
| **F-101** | **S183 · CLOSED, corrected** | **Eight live files were recorded one directory too high.** The call-hook/verdict family lives in `/root/wa/call-hook/` and `/root/wa/recordings-archive/`; the Register said `/root/wa/`. Confirmed against three independent sources: the files, `call-hook.service`'s `WorkingDirectory`, and four live crontab lines. Seven of the eight matched their pinned md5 exactly — right bytes, wrong address. **The lesson is severity, not bookkeeping: a wrong path downgrades a DRIFT to a MISSING**, and "not there" reads as a filing error while "different from the record" reads as danger. The eighth row proved it — a genuine stale hash (F-102) was wearing a MISSING's clothes. **RULE: a pin is an address AND a hash, and the address is verified with the same seriousness as the hash.** | **§7.1** + Archive §S183 |
| **F-102** | **S183 · CLOSED, corrected** | **`call_hook_capture.py` was pinned at its S126 value while the live file had been replaced on 12 Jul 2026.** 42,409 bytes / 894 lines on the box against 31,490 / 701 in the record; stale across the whole S140→S182 run and carried unchallenged through every Register bump. **A second confirmed instance of F-97's class, and an instructive inversion of it** — at S182 the repo agreed with the stale pin and the box was right; here the repo was right and only the record was wrong. **The record is the weak point in both directions, which is why the check must interrogate the machine.** No harm done: the receiver was measured healthy in the same breath (dual-key gate ON, 26 accepted / 0 refused, service start later than the file's mtime). Found on the checker's first run — the argument for D321. | **§7.1** + Archive §S183 |
| **F-103** | **S183 · OPEN (structural)** | **The finance system reconciles UPI against ICICI but has NO cash-deposit reconciliation against Yes Bank.** Sanjeevni cash is swept ~weekly to a Yes Bank account (`CASH DEP-SELF-SANJEEVNI MEDICOS`); ICICI (…312505) receives card/UPI only. Because nothing matched cash deposits to Yes Bank, **16 real deposits (₹16,45,600, 9 Apr → 13 Aug) went unrecorded** and the drawer chain broke to an impossible −₹30,056 — read for months as missing money when nothing was missing. **FIX owed:** a Yes Bank cash-deposit reconciliation parallel to `finance_upi`, plus a named "bank deposit (Yes Bank)" movement type so a sweep is recorded and never left as a carry-forward break. *(The 16 deposits themselves were booked at S184 by `S184_C1a`; the reconciliation mechanism is still owed.)* | **§7.1** + Archive §S183 |
| **F-104** | **S183 · OPEN (owner chose the fix)** | **The S183 Marg backfill fed identity-less legacy bills through attribution**, creating ~2,062 review items + 118 `line_sum_vs_day_total` exceptions. April→mid-June bills carry a name but no clinic ID, so they route to review (D315 low-confidence), leaving the attributed sum below the day total. **No money affected** — attribution never moves `day_line` (D313). Owner ruling: **reclassify legacy no-ID bills to WALK-IN**. To build + test offline, then apply. | **§7.1** + Archive §S183 |
| **F-105** | **S184 · CLOSED — the system was right** | **The app blocked a data catch-up, and the block was correct.** Darpan's 14/15 Aug entry was refused by the Submit guard because the opening carried the −₹30,056 and the guard will not accept a negative opening. **The S183 record had explicitly said this catch-up "needs nothing above" — the record was wrong and the box was right.** The D313 invariant doing its job. **RULE: the app enforcing correctness looks like an obstacle and is a feature; when the record and a running guard disagree, believe the guard.** | **§7.1** + Archive §S184 |
| **F-106** | **S184 · FIXED (S184_F1b)** | **A self-test that asserts a DATA STATE becomes a liability the instant the data is legitimately corrected.** `finance_app.py --selftest` asserted the *pre-S184* store state — cash negative, breaks open, marg unmapped — so the session's own correct migrations read as test failures and the install gate correctly restored. Made **state-adaptive** in F1b: 314/314 on the corrected store. **Same family as F-88 (integrity ≠ currency) and F-97 (a pin agrees with a record, not reality).** **RULE: separate invariant logic from store state; the latter must be state-adaptive or fixture-based, never frozen.** Follow-up owed: split the selftest into invariant-logic vs seeded-fixture checks. | **§7.1** + Archive §S184 |
| **F-107** | **S185 · OPEN (structural) · both docs filed + pinned** | **Phase 0 is blind to a document that was never listed.** The S184 close wrote two **Tier-0** documents (`HANDOFF_RUNBOOK v118`, `START_HERE_SESSION_185`) into project knowledge only — never to the repo, never into `MD5SUMS_ALL.txt`, never as manifest rows. **So at the S185 open, the two Tier-0 documents Phase 0 is *required to read* were the two it *could not verify*.** They were read on trust and nothing complained, **because nothing looks for a missing row**: Phase 0 asks of each listed row *do these bytes still match?*, never of each document in use *are you listed?* **F-97's documentary twin — both are absence-blindness.** Remediated at S185 (both filed, hashed as delivered, pinned; hashes deliberately **not** invented). **Structural fix still owed: the inverse Phase-0 check.** | **§7.1** + Archive §S185 |
| **F-108** | **S185 · OPEN · index corrected here** | **Findings recorded in the KB Register's index were never applied to this register, and its §7 index has been stale at F-89 for four sessions.** §7 ended at F-89 and read *"Next free finding: F-90"* while **F-90 … F-95 (S181) had never landed here at all** and F-96 … F-99 (S182) existed only as §7.1 text with no index rows. The KB Register carried all of them, so nothing was lost — but **the findings register was four sessions behind and said so nowhere.** **This is the F-45 family recurring** — the fault this register minted at S149 for exactly this failure, reconstructed six times at v2.17, and committed again at v2.18 (which bumped the file and left no changelog row). **RULE: the next-free number and the last index row must agree, and that agreement is checked at every append.** | **§7.1** + Archive §S185 |

| **F-109** | **S186 · CLOSED — record corrected** | **Two characters of a hash were invented to make a partial pin look longer than the evidence.** The S184 close recorded `finance_app.py` as eight characters, `c66bec2b`; the S185 fold-in wrote it as ten, `c66bec2b76…`, in fourteen places — while stating in the same breath that the value "was NOT invented". The box and the `S184_F1b` kit both say `c66bec2b9e…`. Nothing downstream broke **because a partial pin is never machine-compared**, which is exactly why it survived a session. **RULE: a partial hash is quoted at the length the evidence supports, never rounded up; and "I did not invent this" is a claim to be checked, not trusted.** | §7.1 · Archive §S186 |
| **F-110** | **S186 · FIXED (kit `S186_V1a`)** | **The live-pin checker was holding the box to a Register draft that never became canonical.** `/root/deploy/live_pins.txt` declared `source_md5: ff509b01…` for `KB_Register_v5_5_S183.md`; canonical v5.5 is `3cad79e6…` and **no file in the repo hashes to `ff509b01…`**. Two of three DRIFT reds at the S186 open were therefore **false** — the record was right and the checker was behind it. The tool printed its own source md5 every run for three sessions and **nothing compared it to the manifest**. A third instance of F-107's absence-blindness, inside the tool built to close F-97. **RULE: a checker that can be stale must verify its own source before it verifies anything else, and refuse to run rather than report.** | §7.1 · Archive §S186 |
| **F-111** | **S186 · FIXED (kit `S186_V1a`)** | **The Register and its own generator drifted apart, and nothing noticed because nobody re-ran the generator.** `live_pins.txt` had not been rebuilt since S183, so three later changes to the Register's live-file table were never tested against the tool that consumes it: two `*(applied marker; no file md5)*` rows **halt** the generator outright, and a `*(superseded)*` rollback row would have been pinned as a **second live pin for the same path** — a red that could never go green (D316). **RULE: a generated artefact that is not regenerated every session is not a check, it is a souvenir.** | §7.1 · Archive §S186 |
| **F-112** | **S186 · FIXED (kit `S186_C1a`)** | **A bank deposit that never happened was booked into the live financial books.** `S184_C1a` booked "16 verified Yes Bank credits, ₹16,45,600". The statement for 1 Jul – 17 Aug has its **last transaction of any kind on 30 July**; the 13 Aug ₹75,000 does not exist. Truth: **15 deposits, ₹15,70,600**, and the books understated cash by ₹75,000. **S183 had flagged that exact row** — *"owner-confirmed; it falls after the statement cutoff … check when booking"* — and it was booked without the check. **RULE: a row the record itself marks as unevidenced may not be booked until it is evidenced — a caveat carried alongside a number does not travel with it into a migration.** | §7.1 · Archive §S186 |
| **F-113** | **S186 · FIXED (kit `S186_I1a`, portal path)** | **"not filed (refused, harmlessly)" is only harmless until the day is filed.** `marg_backfill.py` skips a day with no `day_entry` and reports it on the console. At the 16 Aug run, 14 and 15 Aug were not yet filed, so both were correctly skipped — and **nothing revisited them**: no flag, no exception, no marker, only a console line from a run that had already finished. Distinct from F-100/F-112, which are silence about what was never reached: **here the tool spoke, correctly, and the statement expired.** **RULE: a skip that depends on the state of the world must leave a record that outlives the run.** *(Diagnosed twice wrongly first — a short export, then a driver abort — and settled only by testing the real file and the real adapter. D172/D188 applied to a diagnosis rather than a hash.)* | §7.1 · Archive §S186 |
| **F-114** | **S186 · FIXED (kit `S186_I1a`)** | **Two records described WALK-IN attribution that the running code did not perform.** `marg_report.py` warned *"…will attribute to WALK-IN"* and `finance_ingest.resolve_patient`'s docstring said *"a line with no ID lands on WALK-IN"* — but a gate three lines above diverted the line first, so a bill with **neither ID nor name** was parked in a review queue **containing nothing a human could resolve**. 2,062 rows by S186, ~10 more every clinic day; on 14–15 Aug: WALK-IN 0, review 10. **RULE: a review queue is for lines a human can resolve; anything else is a queue that can only grow.** | §7.1 · Archive §S186 |
| **F-115** | **S186 post-close · FIXED (`PUBLISH_CLOSE.bat`)** | **The default publish method is structurally unable to publish a close-out.** `PUSH.bat` stages exactly one path — its own kit folder. `KB_canon_all` is not a kit and has no `PUSH.bat`, so no per-kit publish can ever carry the canonical set. The S186 close was pasted, pushed, and reported clean while the entire canon sat uncommitted in the working tree. |
| **F-116** | **S186 post-close · FIXED (manifest rebuilt)** | **The manifest pinned the current Register at a hash no file in the repo carries.** Its Register *row* was right (`d0da61a0…`); its own Phase-0 footer said `d5ec45a5…`, a token appearing in exactly one place in the whole repo — that footer. A phantom inside the linchpin. |
| **F-117** | **S186 post-close · list FIXED (`S186_V1c`); TOOL FIX OWED** | **The pin list attested to a manifest that does not exist, and the checker printed the claim without testing it.** `live_pins.txt` carried `manifest_md5: 04eff42c…`; the published manifest is `d1f97e1a…`. `verify_live_pins.py` v1.1 reads the word `yes` and prints "VERIFIED against the manifest (md5 …)" — it never compares that md5 to a real file. F-110 one level up, inside the tool built to close F-110. |
| **F-118** | **S186 post-close · FIXED (Register v5.12)** | **A duplicate-pin conflict was resolved toward the superseded build, and the first live-pin run went RED because of it.** `finance_workbench.html` shipped twice (`S186_R2a` `45cb85b3…`, then `S186_I1a` `18c71e63…`). The box has carried the I1a build since that kit installed. The close kept the R2a value. **The first RED in this project caused by the record rather than the box.** |
| **F-119** | **S186 post-close · FIXED (`MD5SUMS_ALL.txt` rebuilt)** | **Phase 0's only command failed, because the checksum file listed a file that does not exist.** `MD5SUMS_ALL.txt` carried a row for `KB_Register_v5_10_S186.md`, an intermediate bump not in the canon set: 70 rows OK, one "No such file", non-zero exit. The door to the next session was locked and nothing said so. |
| **F-120** | **S186 post-close · FIXED (attic)** | **Three competing checksum files described the same folder and two were stale.** `MD5SUMS_ALL.txt` (71 rows, authoritative), `SUMS.md5` (52 rows, 4 mismatches), `MD5SUMS.txt` (10 rows, 1 mismatch + a malformed line). Nothing read the latter two. D202's one-authored-source rule, broken inside the folder that rule exists to protect. |
| **F-121** | **S186 post-close · FIXED at v3, after v2 failed the same way** | **A gate widened in scope began firing on deliberate ignores.** v1 of the new publisher inherited F-100's "any excluded file is suspicious" check but widened `git add` from one kit to the whole tree; it then refused the commit over `.pyc` residue in two S182 kits and a stray `.tsv` — all correctly ignored, none in the payload. It refused for the wrong reason, and nothing was committed: a safe failure, but the kind that teaches an operator to wave gates through (D316). |
| **F-122** | **S187 · CLOSED STRUCTURALLY (kit `S187_V1a`)** | **The pin-list generator minted a phantom manifest hash at every generation, and the checker published it as a pass.** The manifest's self-row is *"recomputed last, each EOS"*, so its whole-file md5 at generation time is transient **by construction** — `S186_V1c`'s `manifest_md5: 78881ddd…` and V1b's `04eff42c…` match no file in any of the repo's 157 commits. Fixed in v1.2 of both tools: the generator writes the stable `manifest_current_register_pin`; the checker **proves the claim on the box** (hash-hunt in `/root/deploy/repo` canon + manifest CURRENT-row parse) and cannot print VERIFIED without proof. **RULE: never attest to the hash of a file whose rules say it will change after you hash it — attest to the stable value inside it that constitutes the claim.** | §7.1 · Archive §S187 |
| **F-123** | **S187 · FIXED at this close (attic'd + renamed)** | **The repo carried two divergent `CANONICAL_MANIFEST.md` copies, and the stale one still called itself canonical.** `canonical-docs/CANONICAL_MANIFEST.md` was nine sessions stale (S177) with "STATUS: canonical" in its own header, beside sixteen superseded doc versions, covered by no checksum file. F-120 one level up: rival checksum files became rival manifests. Retired: the folder moved to the attic, its manifest **renamed so it cannot pass for a live one**; a pointer README left behind. **RULE: exactly ONE file in the repo may be named `CANONICAL_MANIFEST.md`, and a superseded self-describing document must be made to say so.** | §7.1 · Archive §S187 |
| **F-124** | **S187 · FIXED same session (`PUSH.bat` v2 → `PUBLISH_ALL.bat`)** | **The publisher swallowed a fatal and printed success.** A stale `.git/HEAD.lock` blocked the commit; `\|\| echo (nothing new to commit)` read the fatal as an empty commit; "pushed" was printed with origin unchanged. The fourth publishing fault in three sessions (F-100 · F-115 · F-121), all the same shape: **the tool asserted an outcome it never verified.** v2 refuses on a lock, distinguishes empty from failed BEFORE committing, and prints success only after origin HEAD = local HEAD. **RULE: `\|\| echo` is how a fatal becomes a footnote; a publisher may print "pushed" only after comparing the remote to the local head.** | §7.1 · Archive §S187 |
| **F-125** | **S187 · FIXED (kit `S187_P1b`)** | **A selftest asserted store state and was broken by the first real datum.** The M1a-era check *"staging holds exactly one pending row"* counted ALL pending pushes; the morning's **first genuine push from the medical PC** made it two, and the P1a install went RED **388/389** — the gate restored byte-perfect, no incident. The **fourth firing of the F-106 family** (F-84's fourth lesson, F-87, F-106). Fixed by scoping the check to its own bytes (`file_md5 = md5(stub)`), then **re-rehearsed against the exact failing condition**. **RULE: a test asserts behaviour, never store population — and a fixed test is re-run against the state that broke it.** | §7.1 · Archive §S187 |
| **F-126** | **S187 · FIXED (rule standing)** | **An installer's goodbye message aborted the run after all real work had succeeded.** A sed-injected echo in `install_h1a.sh` broke shell quoting in the script's tail; the page was already placed and pinned, so the "failure" was cosmetic — but an installer that dies after acting is indistinguishable from one that died before. Cause: string-surgery on a shipped installer, syntax-checked only along the rehearsed path. **RULE: every installer is syntax-checked WHOLE (`bash -n`) before shipping — a rehearsal exercises one path; `bash -n` reads them all.** Applied to H1b/H1c the same session. | §7.1 · Archive §S187 |

*Next free finding: F-127.* *(This line read "F-115" through v2.20 and v2.21 while the index rows above it were current — the F-45/F-108 family; corrected here, not silently.)*

---

## §7.1 — FULL TEXT: F-82 … F-89

> **Why this section exists.** F-82 through F-89 arrived as three standalone **append artefacts**
> rather than as index one-liners, and they were owed to this register for nine sessions. §7's
> established pattern is *index here, full text in the Archive* — applying that pattern alone would
> have thrown away the text these appends carried. The bodies below are reproduced **verbatim** from
> the three hash-verified append files; the Archive remains the authority for the surrounding session
> narrative.
>
> Sources, all three hash-verified at the S181 Phase 0 — no filename was taken as provenance (**D188**):
> `Fault_Register_append_F82_F83_S177.md` (md5 `3393d527d7c4e65b6c0504f932babb12`, matching the
> manifest's `3393d527…` pin) · `Fault_Register_append_F84_S179.md` (md5
> `cce4009f373971fdadf8ed1f9b031d03`) · `Fault_Register_append_F85_F89_S180.md` (md5
> `80a01080c74cea66fdb8b6acf337d2ca`).

---

### F-82 (S172, OPEN — VENDOR-SIDE) — MyOperator WhatsApp Developer API returns HTTP 500 {"message":null} on ALL authenticated calls

**Symptom.** Every AUTHENTICATED call to `https://publicapi.myoperator.co` for the clinic account returns `HTTP 500` with body `{"message": null}` — reads (`GET /chat/templates`, `GET /chat/phonenumbers`) AND sends (`POST /chat/messages`). Observed identically from (a) the new portal sender `portal_wa.py` and (b) the tracker's own long-proven `wa_send.py` path, using the identical token (sha8 `d47a090a`, = tracker `WA_TOKEN`), company ID `68384350414b9847`, WABA ID `2101222617483538`, phone-number ID `1090067637530949`.

**Not our code.** An UNauthenticated call to the same endpoint correctly returns `HTTP 401` — the API is up and the token authenticates past the auth gate; only account-resolution fails. Inbound WhatsApp (webhook → `/root/wa/wa_logs/*.jsonl`) is unaffected (today's file present + populated). Two independent code paths + two different read endpoints + the send endpoint all fail identically → not a payload, header, token or portal bug. **Root cause is account-side / provisioning at MyOperator**, starting today.

**Diagnostic ladder (the reusable playbook — run in this order):**
1. `tail` the send log `/root/wa/wa_portal/wa_portal_sends.csv` for the exact error string.
2. Fingerprint the portal token vs `.env`/`wa_send.env` by **len + sha8 only** (never print the token).
3. Live-send to the doctor's OWN number via the tracker's proven `wa_send.py` path (rules out portal request-shape).
4. Do a READ call (list templates). **If a read fails too, it is not payload.**
5. Do a NO-AUTH call. **401 = API up + account not resolving (vendor); 500 everywhere = wider outage.**

**Action.** Escalated to **Khushi** (MyOperator account manager, email with full request/response detail) + **Lokesh Kumar VB** (engineer). `PORTAL_WA_DRYRUN` returned to `"1"` (SAFE). Go-live blocked pending vendor restore; when restored, flip DRYRUN→`"0"`, restart, self-send `drmanoj_post_visit` to the doctor's own number, confirm, then live — no code change.

**Lesson.** Three successive wrong diagnoses (account → config → account) were resolved only by the no-auth 401 control — **run the auth-gate control EARLY**, before theorising. Related near-miss (NOT a fault): a first install targeted `/root/wa` instead of the real portal dir `/root/portal` — caught immediately by the md5 gate; the portal is `/root/portal/portal.py`.

*Full narrative: Archive §S172. Status: OPEN (vendor).*

### F-83 (S176, OPEN — mitigated) — Asset-app intake background OCR thread is fire-and-forget

**Symptom.** The first real reception bill (B-0001, Shri Ram Enterprise, ₹1,30,003) arrived on the checker's screen BLANK although Sarvam extraction was configured and working — a later manual re-run extracted vendor, bill number, total and all 5 line items correctly.

**Root cause.** The A-D21 reception intake fires the Sarvam extract in a plain background `threading.Thread` from the request handler: fire-and-forget. The thread **dies on service restart** (an install/restart between scan and completion kills the read) and the fill deliberately **skips non-draft bills** (non-clobber), so a bill promoted or touched before the thread completes never receives its read — with no visible trace of failure.

**Mitigation shipped (A-D23, S176, LIVE):** the read is no longer silent — `ocr_status` (reading / read / empty / failed) is stamped on the draft + the Purchases list; a **"Re-read with Sarvam"** button (non-clobber, works on drafts AND approved bills) recovers any lost read; approving a bill with blank fields now requires an explicit server-enforced confirm. B-0001 was recovered via Re-read.

**Durable fix (owed, A-D25 candidate):** replace the thread with a survivable path — either a queue + worker (systemd or cron sweep over `ocr_status='reading'|'failed'` drafts) or synchronous extract with a bounded timeout at scan time. Until then, restarts of `assetapp.service` should be followed by a glance at the Purchases list for stuck "reading" badges.

**Lesson.** A background thread inside a gunicorn worker is not a job system: anything that must complete needs a durable record of "not done yet" and a path to retry — visible status first (shipped), survivable execution second (owed).

*Full narrative: Archive §S176 (fold) + `KB_Asset_Register_v1_10_3.md` §7. Status: OPEN (mitigated by A-D23); asset-app located, clinic-numbered.*

---

### F-84 — Three self-found security faults in the finance module: the offline-testing shortcut was the vulnerability (OPEN → FIXED, S179)

**Severity:** high (auth bypass reachable in production for ~2 min on an unpublicised path; header
identity was full control, not a leak). **Status:** all three FIXED and installed this session; the
installer auto-rolls-back if the epoch check fails. Recorded as a lesson to carry, not an open risk.

**Owner did not flag these — I found them after the first install, on my own review.** All three had
the **same shape:** something that made development or offline testing easier, carried into
production without asking "what does this let a stranger do?"

1. **Reads were ungated.** Identity was checked only on writes, so `/finance/api/tile`, `/month`,
   `/day` and the patient lines were readable by anyone with the URL.
   *Fixed:* a **fail-closed `before_request` gate** over an allow-list (`PUBLIC_PATHS`), so a route
   added later is protected without anyone remembering to gate it.

2. **Identity came from spoofable HTTP headers in production.** `X-Clinic-User` / `X-Clinic-Role`
   were an offline-testing convenience that reached prod; `curl -H "X-Clinic-Role: checker"` would
   have approved days and run the cutover. That is control, not a leak.
   *Fixed:* the real `clinic_sso` signed cookie is authoritative; header auth is off unless
   `FINANCE_ALLOW_HEADER_AUTH=1` (the systemd unit states in plain words why it must never be set).
   Tightened further: *signed in ≠ entitled* — a valid clinic login with **no `unit_role` row on
   `medical`** gets 403, so the manager cannot read the pharmacy's cash.

3. **The epoch was never checked.** `verify_token` ran with `current_epoch=None`, so **"Sign out
   everywhere" revoked sessions in the portal, ledger and asset app but NOT here** — a revoked token
   still opened the books. Found only because a stale epoch threw a 403 on `/portal/users` and the
   diagnosis exposed the asymmetry.
   *Fixed:* read the epoch from `clinic_users.get_epoch(clinic_users.DEFAULT_STORE)` on **every**
   request (never cached — a cached epoch keeps revoked sessions alive for the cache's life) and
   **fail closed** if it cannot be read, exactly as the portal does. `healthz` exposes
   `sso_epoch_ok` so a lockout is diagnosable without a cookie, and the installer rolls back
   automatically if that flag is false after restart.

**THE LESSON WORTH KEEPING:** *the offline testing shortcut was the vulnerability.* Anything that
grants identity for convenience must be **opt-in**, and the production default must be **closed**.

**A fourth, smaller lesson (a test defect, not a prod fault):** one install was rolled back by its
own gate because a *test asserted an environment accident* ("the epoch is unreadable here") rather
than a behaviour. Tests must assert what the code **does**, not what the machine happens to look
like. The replacement forces the epoch to be unreadable and **requires refusal** — deterministic on
any box.

**Prevention now standing:** fail-closed `before_request` allow-list on every new Flask surface;
identity only from the signed SSO cookie in prod; per-unit entitlement is the sole authority (broker
role grants nothing); epoch read live and fail-closed; `healthz` surfaces `sso_epoch_ok`; installer
gates on it. Extends F-63 (route-gate testing) and F-68 (same-origin serving).

---

### F-85 — a session number was assigned by anticipation instead of by close-out
**Raised:** S180 · **Severity:** low (documentation integrity) · **Status:** CLOSED by correction
**Kin:** D188 (a filename is not provenance), F-54 (audit the artefact, not the label)

**What happened.** Session 180 opened with a document headed *"Session: 181 (follow-on to S180)"*.
Its stated predecessor, `S180_Marg_Folder_Recon`, was written at 09:15 on 15-Aug — **before** the
S179 close-out ran at 10:50. So the recon was S179 work carrying a forward-guessed label, and the
survey that followed inherited the error and advanced it by one.

**Why it matters.** Two documents in project knowledge carried wrong session numbers, and a third
session was about to. Session numbers are how this project's history is indexed; a wrong one sends a
future reader to the wrong Archive section.

**Diagnosis.** Derived from the artefacts, not the labels: the last close-out was S179 and it named
the next session 180; no close-out had run since; therefore no number past 180 had been consumed.

**Fix.** The session was recorded as **180**. The survey was folded in as
`claude/S180_Marg_Feed_Feasibility.md` with a provenance block stating the correction, the original
upload's md5 (`c2086db25b39c02e8c29bc6cf4dc634c`), and the body byte-for-byte verbatim.

**RULE.** A session number is assigned by a **close-out**, never by anticipation. An artefact
produced mid-session carries the number of the session that is actually running.

---

### F-86 — a reader for a PHI source emitted full phone numbers, because it was written against the source's shape rather than the destination's rules
**Raised:** S180 · **Severity:** medium (privacy) · **Status:** FIXED before install
**Kin:** F-31/F-49 (PHI out of repo and kit), F-46 (whitelist-only printing)

**What happened.** `marg_report.py` was built to read Marg's `.xls` and emit bill rows for
`finance_ingest.adapter_csv`. It carried the patient's **full 10-digit phone number** into its CSV,
because the source report prints one and the reader was written to mirror the source.

**Why it matters.** The destination forbids it. `patient_ref` stores **`phone_last4` and nothing
more** — a deliberate masking design — and `ingest_column_map`'s allowed-field list has **no phone
field at all**, so the full number could never have been consumed anyway. It was exposure with no
purpose. Had that CSV been written to disk on the VPS or swept into a kit, it would have been a
fuller PHI leak than the schema's own design permits.

**Fix.** The bill CSV emits `phone_last4` only; the item CSV carries **no patient identity at all**
(the bill number is its only link). Outputs were grepped for any 10-digit string — none found. A
`last4()` helper is now the only way a phone leaves the module, with the reasoning in its docstring.

**RULE.** The destination's constraints are **part of the specification**, not a detail discovered
at install. Before writing a reader, read the schema it feeds.

---

### F-87 — a change was shipped to a test suite that could not be run offline, twice
**Raised:** S180 · **Severity:** HIGH (process) · **Status:** remedied by an asset, not a resolution
**Kin:** **F-84** — *"the offline-testing shortcut was the vulnerability"* — this project's own
lesson, repeated after it had already been minted

**What happened.** `finance_app.py`'s smoke suite is the install gate. It is written against the
real store: >100 filed days, approved and locked days, open exceptions, a legacy tail that leaves
cash negative. None of that existed offline, so the suite **could not be run** here. A test block
was added to it anyway and shipped on reasoning alone. It failed on the box with two broken
assertions — `failed ingest preserved existing lines` and `patient revenue spine populated` — both
caused by the added block. **The install gate rolled it back correctly**; nothing was left
half-installed.

**Two concrete traps, both now written into the code itself:**
1. **`ingest_day` supersedes the day's previous batch and DELETES what it produced.** Any test that
   ingests destroys what earlier tests set up. This trap was hit **twice in one session** — once in
   `finance_ingest.py`'s own selftest, then again in `finance_app.py` after the first lesson.
2. **Resolving a queued line ADDS a `sale_item`**, and an earlier check asserts the day still has
   exactly three lines.

**Fix.** The block no longer calls `/ingest` at all — it inserts its queue row directly, exercising
only the route that changed — and runs **last**, with a comment stating it must stay last and that
new checks go above it.

**The remedy that matters is an asset, not a fix.** `dev_seed_smoke_db.py` builds a database
satisfying the suite's preconditions, so the suite can be run **before** shipping. With it, the
change was verified **differentially** rather than absolutely:

```
unmodified app, seeded db    163/173
modified app,   seeded db    166/176      same 10 seeding artefacts,
                                          +3 new checks, ZERO failures added
```

Then confirmed on the box: **179/179**.

**RULE.** **If a test suite cannot be run, making it runnable is the FIRST task, not an optional
one.** And when a suite's absolute score cannot be trusted (imperfect seeding), verify
**differentially** — baseline versus modified on identical data — rather than chasing a green number.

---

### F-88 — a passing `md5sum -c` proved a kit was internally consistent, not that it was the intended kit
**Raised:** S180 · **Severity:** medium (install integrity) · **Status:** FIXED
**Kin:** D188 (a filename is not provenance), F-66 (trust the hash)

**What happened.** An install kit was corrected and re-issued. Two subsequent install attempts
**ran the older download**, because the browser had saved the new file under a different name and the
original was what reached the box. The installer's `md5sum -c SUMS.md5` **passed both times** — a
stale kit is internally consistent: its checksums match its own files perfectly.

**Why it matters.** The hash gate is the project's primary defence against installing the wrong
bytes, and it silently permitted the wrong build twice. Two debugging rounds were spent looking for
a code fault that had already been fixed.

**Fix.** The installer now carries the **identity of the build it belongs to** — a `KIT` name and
the expected md5 of the file that actually changed — checks it **first**, and refuses to run
otherwise:

```
-- kit: S180_U11c
!! STALE KIT. finance_app.py.new here is ab3dbf52...
!!            this installer expects   7b62b7ae...
!! You are running an older download. Fetch S180_U11c and unzip it again.
```

The guard was tested against the superseded module before shipping. Re-issued kits also take a new
folder and zip name (`_U11b`, `_U11c`) so a browser cannot hand over the old one.

**RULE.** A checksum proves **integrity, never currency**. An install kit states which build it is
and refuses to run if it is not that build.

---

### F-89 — the cold-backup cadence lapsed for nine sessions, and three canonical documents were lost
**Raised:** S180 · **Severity:** HIGH (irrecoverable data loss) · **Status:** cause corrected; loss permanent
**Kin:** F-87 (a discipline this project had already written down, not followed)

**What happened.** The S180 Phase 0 found seven canonical rows unreachable. A hash-based recovery
tool was written and run over the owner's `D:` and `C:` drives — searching by **md5 rather than
filename** (D188), opening `.zip` archives, and re-hashing LF-normalised copies of near-misses.
**26,745 files hashed. Four recovered. Three could not be found anywhere and are gone:**
`KB_Asset_Register` v1.11.0 (**Tier-1 CURRENT**), `KB_Register` v5.0, `KB_History_Archive` v1.26.

**Why exactly those three — this is the finding.** The newest full cold kit on the machine is
**`DrManoj_Clinic_FULL_Handoff_Session171`**. The three lost documents are **S177 and S178 outputs**.
Everything up to S171 was comfortably recoverable from disk; everything after it depended on whatever
happened to have been downloaded loose. The four that *were* recovered came from the S171 cold kit,
the S165 cold kit, and the git repo's `canonical-docs/` — all of them backup mechanisms that had run.

`END_OF_SESSION_PROMPT_v4 §E` says a full cold kit is generated *"~3–5 sessions since the last one,
or when the Register/Archive just bumped a version, or when you ask,"* and that it should be
**flagged at close if overdue rather than built unasked**. Nine sessions passed. It was not flagged,
and it was not built.

**The loss was not caused by the Phase 0 that discovered it.** It was caused nine sessions earlier,
by a backup not taken. Phase 0 did its job — it is the only reason anyone found out at all.

**Fix.** Cold-backup discipline restored at this close: `KB_S180_close.zip` contains all six canonical
documents plus `MD5SUMS.txt`, and the git kits were committed, clearing a two-session lag.

**RULE.** **The cold kit is not discretionary.** It is a standing backlog item carrying a session
count, and that count is checked at every close — not consulted only when something is already
missing. A backup regime whose failure is invisible until a document is needed is not a backup regime.

**Consequence, recorded under D316:** the two historical losses are closed **LOST-SUPERSEDED**
(v5.1 and v1.27 are verified present, nothing current depends on them). `KB_Asset_Register` v1.11.0
is closed **LOST-RECONSTRUCTABLE** — the recovered v1.10.3 plus Archive §S173–§S177 can rebuild it.
It is unbuilt, not unknowable.

---


---

## §7.1 (continued) — S182 · F-96 … F-99

### F-96 — the canonical set is PHI-bearing in a PUBLIC repository · RULED (D320)
**Found:** S182, by scanning all 48 canonical files after cloning the repo **anonymously** — which
itself re-proved F-90's open question: the repo is public, as a fact rather than a suspicion.
**What is exposed:** 7 unmasked patient mobile numbers, and — worse than S181 recorded — at least
two patient **names** and one clinic **patient ID** sitting directly beside them (the Callback-Tracker
audit; Archive v1.27/v1.28/v1.29, 14 hits in each). Six of the affected files were already in the
older `canonical-docs/` folder, so exposure is not new; the 16-Aug push multiplied it.
**Why it matters beyond the count:** a passing `md5sum -c` **conceals** it. The check proves
integrity and says nothing about whether the content belongs there at all — **F-88 one level up**.
**Ruling (D320):** the owner accepts the repo staying public, knowingly. Recorded as a decision, not
left as an open finding. **RULE (corollary, binding): no PHI-bearing artefact enters the repo** —
raw Marg exports, `finance.db`, patient CSVs and scans live on the PC and the VPS only (F-31/F-49).
Masking the canonical set is a separate and expensive decision — it would break every pin and the
Archive's prefix-proof, and must never be done as a quiet edit.

### F-97 — the Register's LIVE-CODE PINS are verified by nothing, and one was stale by two sessions · OPEN
**Found:** S182, before writing any code, by checking the obvious build path.
`portal.py` was pinned `da4177091ba9f188be6a0ff3eaf25bd8` "S176"; the repo copy matched that
**byte-for-byte**; the box was running **`34f038a7652024d49479569ed53bbfb9`** with two live finance
tiles present nowhere else. **The pin and the repo agreed with each other and both were two sessions
behind reality.** A full-file replacement built the obvious way would have deleted the medical unit's
**Daily Sale** and **Sanjeevni Medicos** tiles, and every gate would have passed — nothing asserted
their presence, and the matching hash would have actively reassured.
**The structural point:** Phase 0 verifies **documents**, beautifully. **Nothing verifies the live-code
pins in the Register at all.** The new git-clone Phase 0 makes that gap *easier* to miss, not harder,
because it feels total. A filename is not provenance (D188); **neither is a Register pin**.
**Mitigated per-kit, not structurally:** every portal kit now carries a **LIVE-FILE CURRENCY GATE** —
it refuses unless the live file is exactly the one the kit was built against, and says so having
touched nothing. **RULE: a full-file replacement states the md5 it was built on and refuses any other.**
**Owed:** something that verifies live-code pins as a class — the fix is not written.

### F-98 — the SSO broker assumed "doctor" when it could not identify the caller · CLOSED (S182_P2a)
**Found:** S182, while chasing why grant-only tiles vanished from the owner's portal.
`_authed()` accepts a valid SSO cookie **or** `_is_trusted()` (the legacy PIN-era device cookie kept
for the SSO transition), and `_is_doctor()` said, in its own docstring, *"a trusted device with no SSO
user is treated as the doctor."* So a browser holding that old cookie, **with no SSO session at all**,
was authenticated and treated as the doctor — reaching every `@doctor_required` surface: the Clinic
Gist, the Call Console, the per-staff coaching report. Patient-data surfaces. The likeliest browser in
that state is the clinic PC, shared by reception.
**This is F-84's pattern** — *anything that grants identity for convenience must be opt-in; the
production default must be closed* — minted on the finance app at S179, fixed there, and still sitting
in the broker that fronts everything else. **Defence in depth limited it:** `/portal/users` uses
`@user_admin_required`, which demands a real SSO user and 403s a trusted device; the finance app has
been fail-closed since F-84; downstream apps run their own verify-shims (D265).
**Fix:** identity is proven, never assumed — but keyed to `_sso_ready()`, **not** to the cookie. When
broker mode is available an unidentified caller is sent to sign in; when it is not available the legacy
path is untouched, so **D264's inert-on-failure invariant survives** and a config failure cannot lock
the owner out of his own front door. That branch is asserted as its own test.
**Second lesson, recorded:** this fault also produced the "my new tiles are missing" report. With no
identity, `USER_TILE_EXTRA` has no username to match and **every** grant-only tile vanishes — proven
by the *pre-existing* "Manage Users" tile vanishing alongside the new ones. **RULE: when a new thing
and an old thing fail together, the new thing is not the cause.**
**Gate:** 48 checks, including an identity matrix over all four (broker ready?, SSO user?) combinations
and **served-HTML** checks (D307c) rendering the real page for six named people, presence AND absence.
Proven to bite against the pre-fix file. Two of the gate's own assertions were wrong on first run and
the gate caught them — a bare `">Clinic<"` also matched the section header, and Darpan had been wrongly
expected to see a doctor-only tile.

### F-99 — a missing-day alarm anchored on the first filed day cannot see a unit that never files one · OPEN
**Found:** S182, from the clinic review screen showing every day 1–16 Aug as `pending`, never `missing`.
`refresh_missing_days()` anchors on `MIN(business_date)` for the unit and **returns 0 immediately when
the unit has no `day_entry` rows**; no exception is raised and the grid falls through to `pending`.
There is no `clinic.start_date` — the anchor is literally "the earliest day you ever filed."
**Consequence:** the alarm arms itself with the first filed day and is correct thereafter, but until
then **"this unit has not started" and "this unit has gone dark" are indistinguishable.** D313 commits
to missing days shouting; for a brand-new unit it cannot.
**Why it never bit before:** medical was seeded with 121 imported legacy days. **Clinic is the first
unit to start empty — and lab will hit exactly this when it launches.**
**Deliberately not fixed at S182:** a new anchor setting would mean another kit against a finance app
freshly green at 316/316, to cover a window that closes with the first filed day. **RULE: a detector
whose scope is derived from the data it monitors has a blind spot at zero, and that blind spot must be
written down when the detector is built, not discovered by a unit going dark.**


---

## §7.1 (continued) — S181 · F-90 … F-95 *(applied at the S185 close; owed since S181 — F-108)*

> **Provenance.** These six findings were minted at S181 and indexed in the **KB Register's** findings
> index, but were never applied to this register: §7 ended at F-89 and read *"Next free finding: F-90"*
> for four sessions (**F-108**). The bodies below are **derived from evidence, never from memory
> (D172)** — from `KB_Register_v5_5_S183.md` (md5 `3cad79e6361c6e1777f3bc9db983770d`) findings index
> "F-0 … F-95 (as at S181)", the v5.3 lineage row, and `HANDOFF_RUNBOOK` v115/v117. **Where the
> Register recorded a one-line finding, this entry states what the Register recorded plus what later
> sessions proved about it — it does not invent detail the record never held.** The Archive §S181
> block remains the authority for the surrounding session narrative.

### F-90 — the GitHub repository is PUBLIC · RULED (D320)
**Found:** S181, as an open question with visibility **UNKNOWN**; the recommendation was private + a
read-only deploy key. **Proven:** S182, by cloning the repo **anonymously** — which turned a suspicion
into a fact and answered F-9's long-open question in the same stroke. **Ruled:** S182, **D320** — the
repo stays public, knowingly, because the D317 chain and the git-clone Phase 0 both work unchanged
over an authenticated remote and the owner accepts the exposure. **Binding corollary: no PHI-bearing
artefact may enter the repo** — raw Marg exports, `finance.db`, patient CSVs and scans live on the PC
and the VPS only (F-31/F-49). Recorded as a decision rather than left as an open finding.

### F-91 — UPI is recorded as Cash at Docterz entry · OPEN (behavioural)
**Found:** S181, during the clinic/lab forensic analysis. ₹17,900 over six weeks was collected by UPI
and typed as Cash at the point of entry. **The reason it survived so long is the important part: it is
invisible to any ledger-internal check.** The books balance either way — cash in equals cash recorded —
so no invariant, no exception and no self-test can see it. **Only a comparison against the bank exposes
it**, and the typed daily tab is the reconciliation anchor.
**Its shape recurred:** at S182 two Marg days (11 and 14 Aug, ₹38,355) were 100% cash against 40–76%
on every other working day — F-91 appearing in the pharmacy rather than at reception. **Settled at
S183** as a Marg UPI-recording gap, bank-confirmed.
**Fix:** the reconciliation workbench designed at S184 — Marg ⋈ bank ⋈ entry on one screen, with
cash→UPI suggestions **graded like D315 and never auto-applied**, and a correction log through
`audit_log`. **RULE: a discrepancy that leaves the books internally consistent can only be found from
outside them.**

### F-92 — discount capture stopped on 18 Jun 2026 · OPEN
**Found:** S181. ₹1,33,720 of discounts were recorded up to 18 Jun 2026, and **zero after it.**
Concessions did not stop being given — they stopped being *valued*. Part of an **18–19 Jun regression
cluster** noted the same session. The money is not lost; the visibility is. Until it is restored, any
analysis of realised-versus-billed revenue after 18 Jun is quietly wrong in a direction nobody is told
about.

### F-93 — the concession parser swallows the Docterz footer · OPEN
**Found:** S181. The parser reads the report's footer as data, manufacturing **three fake "patients" a
day** in the staff-facing sheet. In money terms this is cosmetic. **In trust terms it is not:** a
staff-facing report that visibly contains nonsense teaches the people who read it that the report may
be ignored, which is expensive in a system whose entire premise is that the people at the counter
believe what it tells them.

### F-94 — an installer's environment assumptions are part of its specification · CLOSED by D317's rules
**Found:** S181, as the **C1a / C1b / C1c red trilogy** — three consecutive installer reds during the
clinic-module build. Each was caught by a gate with **nothing half-installed**, and each traced back to
an assumption about the target environment that the kit had never stated out loud. **Closed by rules,
not by a code fix:** the D317 kit chain requires a kit to declare what it needs and to refuse rather
than adapt. Kin of F-53 (which interpreter) and F-88 (which build).

### F-95 — a synthetic store proves logic, not life · CLOSED by rules
**Found:** S181, from the same build. A test database built to satisfy a suite proves that the *logic*
holds; it says nothing about whether the code survives contact with the real store's shape. **Three
rules were adopted:** smoke checks **print what they actually saw** rather than asserting silently;
invariants are **asserted as invariants**; and an offline store is **enriched with live-shaped data
before a first live gate** is attempted. Direct kin of **F-87** (a change shipped twice to a test suite
that could not be run) and the ancestor of **F-106** (a test that froze a data state).

---

## §7.1 (continued) — S183 · F-100 … F-104 *(applied at the S185 close; owed since S183)*

### F-100 — `push_kit.bat` reported success while git had silently dropped a kit file · CLOSED same session
**Found:** S183, at the VPS console, as a SUMS refusal — the only place it could surface.
The pin list was named `live_pins.tsv`, and `.gitignore` carries a blanket `*.tsv`: one of the
data-format guards that keep patient data out of a public repo (F-31/F-49, D320). **`git add <folder>`
says nothing about ignored files inside it**, so the kit was published incomplete while the publishing
step reported "pushed successfully."
**This is F-97's shape one layer up the toolchain:** the publishing record claimed a file that was not
there, exactly as a Register pin claimed bytes that were not there.
**Fixed two ways.** The file was renamed to `.txt` — **no exception was carved into `.gitignore`**,
because a blanket PHI rule with holes in it is how something eventually gets through. And
**`push_kit.bat` v4** now lists any excluded file **with the exact rule that excluded it** and REFUSES
to commit.
**RULE: a publishing step that cannot prove it published everything has not published anything.**

### F-101 — eight live files were recorded one directory too high · CLOSED, corrected
**Found:** S183, by the first run of `verify_live_pins.py`.
The call-hook/verdict family lives in `/root/wa/call-hook/` and `/root/wa/recordings-archive/`; the
Register said `/root/wa/`. Confirmed against **three independent sources** — the files themselves,
`call-hook.service`'s `WorkingDirectory`, and four live crontab lines. **Seven of the eight matched
their pinned md5 exactly: right bytes, wrong address.**
**The lesson is about severity, not bookkeeping.** A wrong path downgrades a **DRIFT** to a **MISSING**.
"Not there" reads as a filing error and gets waved through; "different from the record" reads as
danger. The eighth row proved the point — a genuine stale hash (**F-102**) was wearing a MISSING's
clothes and nearly stayed hidden behind it.
**RULE: a pin is an address AND a hash, and the address is verified with the same seriousness as the
hash.** *Recorded limitation of the checker itself: where a recorded path is wrong it reports MISSING,
and a MISSING masks a possible DRIFT until the path is chased down.*

### F-102 — a live-code pin was stale for the whole S140→S182 run · CLOSED, corrected
**Found:** S183, by the same first run.
`call_hook_capture.py` was pinned at its **S126** value while the live file had been replaced on
**12 Jul 2026 at 18:13**: 42,409 bytes / 894 lines on the box against 31,490 / 701 in the record. The
stale pin rode unchallenged through every Register bump for more than forty sessions.
**A second confirmed instance of F-97's class, and an instructive inversion of it.** At S182 the *repo*
agreed with the stale pin and the *box* was right; here the *repo* was right and only the *record* was
wrong. **The record is the weak point in both directions — which is precisely the argument for a check
that interrogates the machine rather than comparing two documents to each other.**
**No harm done, and measured rather than assumed:** the receiver was checked healthy in the same breath
— dual-key gate ON (`current=key_ea20dd previous=key_db8972`, ROTATION IN PROGRESS), 26 accepted /
0 refused — and the service's start time is later than the file's mtime, so the running worker holds
the current bytes. Corrected to `b8a1a293c54dfb6528e04fdf31f8d3e6`.

### F-103 — the finance system has no cash-deposit reconciliation against Yes Bank · OPEN (structural)
**Found:** S183, while explaining an impossible drawer balance of **−₹30,056**.
Sanjeevni cash is swept roughly weekly into a **Yes Bank** account, appearing as
`CASH DEP-SELF-SANJEEVNI MEDICOS`; **ICICI (…312505) receives card and UPI only.** `finance_upi`
reconciles the ICICI side. **Nothing reconciled the cash side at all** — so **16 real deposits totalling
₹16,45,600 between 9 Apr and 13 Aug went unrecorded**, the drawer chain broke, and the break was read
for months as missing money.
**Nothing was missing.** Reconciled: cash collected ₹17,98,033 − deposits ₹16,45,600 − expenses
₹84,442 = **+₹67,991** drawer growth.
**RULE: a break in a ledger is often an unrecorded real movement, not a loss. Before treating a
negative as missing money, ask what legitimate movement is unrecorded.** And: **the bank is the
arbiter, and here it cleared the human** — Darpan's declared UPI matched ICICI T+1.
**FIX still owed:** a Yes Bank cash-deposit reconciliation parallel to `finance_upi`, plus a named
"bank deposit (Yes Bank)" movement type so a sweep is *recorded*, never left as a carry-forward break.
*(The 16 deposits themselves were booked at S184 by `S184_C1a`; the mechanism that would prevent a
recurrence is not built.)*

### F-104 — the backfill fed identity-less legacy bills through attribution · OPEN (owner chose the fix)
**Found:** S183, in the exception counts after the 119-day Marg backfill.
April → mid-June bills carry a patient **name** but no clinic **ID**, so they route to review as
low-confidence under **D315**, leaving each day's attributed sum below its day total. Result:
**~2,062 review items and 118 `line_sum_vs_day_total` exceptions.**
**No money is affected** — attribution never moves `day_line` (**D313**, proven at scale by this very
backfill, which left the money byte-identical across 119 days). The cost is a review queue full of
legacy noise, which is how a real exception comes to be missed.
**Owner ruling: reclassify legacy no-ID bills to WALK-IN** — they attribute cleanly, the 118 exceptions
clear, and the queue empties of noise. To build and test offline, then apply.

---

## §7.1 (continued) — S184 · S185 · F-105 … F-108

### F-105 — the app blocked a data catch-up, and the block was correct · CLOSED (the system was right)
**Found:** S184, when Darpan's 14/15 Aug catch-up would not submit.
The Submit guard refused because the day's **opening carried the −₹30,056**, and the guard will not
accept a negative opening. **The S183 record had said in writing that this catch-up "needs nothing
above."** It did. **The record was wrong and the running guard was right** — the D313 invariant doing
exactly the job it was built for, at the exact moment it was inconvenient.
Resolved by fixing the *books* rather than the guard: after `S184_C1a` the two days were entered and
saved as drafts (the form requires three scans or a stated reason to Submit; the owner chose that
Darpan attaches scans and submits, with Manoj approving).
**RULE: the app enforcing correctness looks like an obstacle and is a feature. When a written record
and a running guard disagree, believe the guard** — the guard is executing, the record is remembering.

### F-106 — a self-test asserted a data state, and a legitimate correction made it fail · FIXED (S184_F1b)
**Found:** S184, when kit `S184_F1a` went RED at its install gate.
`finance_app.py --selftest` asserted the **pre-S184 store state**: cash negative, carry-forward breaks
open, marg unmapped. The session had just *corrected* all three, legitimately and deliberately — so the
session's own success registered as four test failures, and the gate correctly restored the previous
build. **The test was not wrong about the data; it was wrong about what a test is for.**
**Fixed in F1b** by making those four checks **state-adaptive**: 314/314 on the corrected store.
**Family:** F-88 (a checksum proves integrity, never currency) and F-97 (a pin proves agreement with a
record, not with reality). All three are the same error in different clothing — **a check that
validates a snapshot and presents the result as though it had validated a property.**
**RULE: separate invariant logic from store state. Invariants are asserted as invariants; state is
asserted state-adaptively or against a seeded fixture, never frozen.**
**Follow-up owed:** split the selftest into invariant-logic and seeded-fixture halves, so a data
correction can never again block a code deploy.

### F-107 — Phase 0 is blind to a document that was never listed · OPEN (structural); both docs filed + pinned at S185
**Found:** S185, at the session open, while reading the two Tier-0 documents the S184 close had produced.
`HANDOFF_RUNBOOK…v118` and `START_HERE_SESSION_185` had been written into **project knowledge only**.
They never reached the repo, never entered `MD5SUMS_ALL.txt`, and never became rows in
`CANONICAL_MANIFEST.md`.
**The consequence is exact: at the S185 open, the two Tier-0 documents Phase 0 is *required to read*
were the two documents Phase 0 *could not verify*.** They were read on trust. **Nothing reported a
problem, because nothing looks for a missing row.** Phase 0 walks the manifest and asks of each row
*"do these bytes still match?"* — it never walks the documents in use and asks *"is each of you
listed?"*
**This is F-97's documentary twin.** F-97: nothing verified the live-code pins. F-107: nothing detects
an unlisted document. **Both are absence-blindness — and absence, not corruption, is what this project
has actually lost documents to** (F-89: three canonical documents lost because a backup that was never
taken cannot fail loudly).
**Remediated at S185, honestly:** both files were written out from the project-knowledge copies, filed
into the repo, **hashed as delivered**, and pinned. Their md5s were **deliberately not invented** at the
S185 open — *"compute at freeze"* means a real hash still owed, not a placeholder to skip (D172/D188).
Those filed bytes are canonical from here.
**Structural fix still owed: the inverse Phase-0 check** — assert that every Tier-0 document about to
be read has a manifest row. Natural companion to `verify_live_pins.py`; same family of fix, one domain
over.

### F-108 — findings recorded in one register were never applied to this one · OPEN (index corrected here)
**Found:** S185, while building the owed append — by checking this register's own next-free number
against its last index row.
**§7's index ended at F-89 and read *"Next free finding: F-90."*** Meanwhile **F-90 … F-95 (S181) had
never been applied to this register at all**, and **F-96 … F-99 (S182) existed only as §7.1 full-text
blocks with no index rows**. The KB Register's findings index carried all ten, so **nothing was lost** —
but the *findings register*, the document whose entire purpose is to be the register of findings, was
four sessions behind and **announced that fact nowhere**.
**Compounding it: v2.18 bumped this file and left no CHANGELOG row** — reconstructed at this close.
**This is the F-45 family recurring.** F-45 was minted *by this register, at S149, for exactly this
failure*. v2.17 then reconstructed **six** versions that had each bumped the file and left no changelog
entry, and named the pattern explicitly. It happened again at the very next bump.
**The structural point, and it is F-107's:** a version bump that *adds* content is loud and gets
noticed. Content that was *never added* is silent, and silence is indistinguishable from success. Two
findings in one session, in two different documents, from the same blind spot.
**RULE: the next-free number and the last index row must agree, and that agreement is checked at every
append** — mechanically, not by intention.

---

## §7.1 (continued) — S186 · F-109 … F-114

**F-109 — the two invented characters.** At the S186 open the `finance_app.py` pin was completed from
the box: **`c66bec2b9ea8c11af9c4a4244541e96f`**, corroborated byte-for-byte by the `S184_F1b` kit
payload held in git, whose `KIT_ID.txt` and `SUMS.md5` carry the same value and whose installer
refuses to run unless the payload matches it. Two independent witnesses. The record carried
`c66bec2b76…` — **wrong in characters 9 and 10.** Tracing it: Runbook v118 and `START_HERE_SESSION_185`,
both written at the S184 close, record only **eight** characters. The ten-character form first appears
at the **S185 fold-in** and then in fourteen places across the canon, while that same session wrote in
its own mental models *"never invent a hash to make a table look complete."* Nothing broke, because a
partial pin is never machine-compared — which is the whole reason it survived.

**F-110 — the checker held the box to a draft.** `verify_live_pins.py` reported three DRIFT reds at
the S186 open. Its pin list declared `source: KB_Register_v5_5_S183.md · source_md5: ff509b01…`.
**Canonical v5.5 is `3cad79e6…`, and no file anywhere in the repo hashes to `ff509b01…`** — the list
had been generated mid-session from an intermediate draft that still carried pre-S183 values. So two
of the three reds were **false**: canonical v5.5 already recorded `marg_report.py` = `829f4344…` and
`marg_backfill.py` = `fa33ec8a…`, exactly what the box reported. The tool prints its own `source_md5`
on every run — the right instinct — but **nothing ever compared that md5 to the manifest**, so it
announced its own staleness for three sessions to no one. Fixed in kit `S186_V1a`:
`gen_live_pins.py` v1.1 refuses to build from a Register the manifest does not pin as CURRENT, and
`verify_live_pins.py` v1.1 refuses to *run* on a list carrying no verified-source attestation
(`yes` / `pending: <reason>` / absent → exit 2).

**A consequence worth recording:** the draft list had **no row under `/root/deploy/`**, and
`find_untracked` only scans directories containing a pinned file — so for three sessions **the checker
could not see its own directory.** Untracked rose 68 → 76 the moment it could.

**F-111 — the generator could not read the Register.** Regenerating exposed that `live_pins.txt` had
not been rebuilt since S183, so three later changes to the live-file table had never met the tool that
consumes it. All three were latent: (a) the two `*(applied marker; no file md5)*` migration rows added
at S185 **halt the generator outright** — v5.6 could not have produced a pin list at all; (b) the
`*(superseded)*` rollback row added at v5.6 would have been read as a **second live pin for the same
path**, holding `finance_app.py` to two hashes at once, one of which could only ever be DRIFT — a red
that can never go green is the halt that gets waved through (D316); (c) nothing refused two pins for
one path. Fixed in v1.1: superseded rows dropped **loudly**, duplicate paths halt the run, and a row
may declare *no file md5* **in words** (classifiable) while a **silent** omission still halts — D166,
where UNKNOWN is a correct entry provided it is written down as UNKNOWN.

**F-112 — the deposit that never happened.** The owner supplied the Yes Bank statement for
**1 Jul – 17 Aug**; its last transaction of any kind is **30 July**, and there are no August entries at
all. The 13 Aug ₹75,000 booked by `S184_C1a` as one of "16 verified" credits **did not occur**. Truth:
**15 deposits, ₹15,70,600**; the live books understated cash in hand by ₹75,000 until kit `S186_C1a`
removed it. **S183 wrote the warning itself** — *"13 Aug 75,000 is owner-confirmed; it falls after the
statement cutoff. Possible gap … check when booking"* — and S184 booked it with no check made. The
structural remedy is `finance_yesbank.py` (kit `S186_R1a`), which matches booked deposits against the
statement in both directions and, critically, reports a deposit booked where **no loaded statement
reaches** as `deposit_unevidenced` — **never as a pass**. Given the real statement and the uncorrected
store it flagged exactly the 13 Aug ₹75,000 and nothing else: 5 matched, 1 caught, zero false positives.

**F-113 — a correct statement that expired.** `marg_backfill.py` skips a day for which no `day_entry`
exists, prints `NOT FILED`, and closes with *"N of M day(s) reachable · K not filed (refused,
harmlessly)"*. At the 16 Aug run, 14 and 15 August had not yet been filed — Darpan's drafts came
afterwards — so the tool behaved correctly and reported honestly. **The skip stopped being harmless
the moment the days were filed, and nothing revisited it**: no flag, no exception, no marker; the only
trace was console output from a finished run. Remedied in kit `S186_I1a`: the portal upload path writes
a `MARG_DAY_NOT_FILED` `data_flag` for every date it skips. *(The CLI driver still lacks this — owed.)*
**This finding was diagnosed wrongly twice before it was settled** — first as a short export, then as a
driver abort. Both were plausible; both were disproved by reading the actual export with the live
parser (it contained 14 and 15 Aug, 23 and 10 bills) and by running the live adapter against it on a
throwaway store (23/23 and 10/10, `draft` no obstacle). D172 and D188 applied to a diagnosis rather
than to a hash.

**F-114 — the queue that could only grow.** `marg_report.py` warned *"10 of 33 bills carry no clinic ID
and will attribute to WALK-IN"*; `finance_ingest.resolve_patient`'s docstring said *"a line with no ID
lands on WALK-IN"*. On 14–15 August: **WALK-IN 0, review 10.** The gate three lines above
`resolve_patient` —
`if ln["confidence"] < min_conf or (not ln["clinic_id"] and not ln["patient_name"])` — diverted the
line before that function was ever reached, so a bill with **neither ID nor name** was parked in a
review queue with **nothing in it a human could resolve**: no name to look up, no ID to match. 2,062
rows by S186, ~10 more per clinic day. Fixed in kit `S186_I1a`: a line read cleanly but anonymous, from
a **structured** export, attributes to WALK-IN; **low-confidence** lines still go to review, and an
anonymous **OCR** line still goes to review because an unreadable scan looks exactly like an anonymous
one. Reversible without code: `ingest.anonymous_to_walkin = 0`. Diff: one line replaced, 17 added.
The legacy backlog was then cleared by kit `S186_W1a` (F-104): review 2,072 → **0**, flagged days
120 → **4**.

**The family these six belong to.** F-109, F-112 and F-114 are all *a record asserting something about
another component that nobody checked* — the same shape as F-97, F-107 and the S184 SQL narration
*"tracked in salary system"*. F-110 and F-111 are *a check that was never checked*. F-113 is the
subtler cousin: **a true statement with an expiry date and no way to notice it had passed.**


## §7.1 (continued) — S186 POST-CLOSE · F-115 … F-121 *(raised and fixed the same day, after the close was published)*

> **Why there is a post-close block at all.** The S186 close was built, verified, published — and then
> the first live-pin run against the published list came back **RED**. Chasing that one RED opened six
> more. Every one of them lives in the layer that is supposed to prove everything else: the publish
> step, the manifest, the checksum file, the pin list. **The findings below are not about the clinic's
> money or the clinic's code. They are about the machinery this project uses to know what is true.**

### F-115 — the method that publishes a kit cannot publish the record · FIXED

**Symptom.** The owner was told to paste `PUSH.bat` to publish the close-out. He did. It pushed, and
`HEAD` matched `origin/main` — a clean green. The last published commit was `deploy kit S186_W1a`, a
mid-session kit. The **entire close-out was still uncommitted**: three modified and seven untracked
files in `KB_canon_all/`, plus the whole `S186_V1b/` kit folder.

**Cause.** `PUSH.bat` derives its target from its own location — `for %%I in ("%~dp0.") do set
KIT_NAME=%%~nxI`, then `git add deploy_kits\%KIT_NAME%`. Correct for a kit. But `KB_canon_all` **is not
a kit**: it carries no `KIT_ID`-bearing `PUSH.bat` of its own, so no per-kit publisher can ever stage
it. The instruction "paste PUSH.bat" was unfulfillable as given.

**Why nothing caught it.** Every check passed honestly and none was asked the right question.
`PUSH.bat`'s F-100 gate proves *the kit it stages* is complete — it cannot notice a folder it was never
pointed at. `git status` said so plainly, but `PUSH.bat` does not read `git status` and the owner is
not asked to. And `HEAD == origin/main` is a true statement about the commit that exists, not about the
commit that should exist. Family: **F-107** (absence-blindness), aggravated because the absent thing is
the canonical record itself. Had it gone unnoticed, S187 would have opened Phase 0 against a repo whose
newest canon was S185 — and the manifest, itself unpublished, could not have reported its own absence.

**Fixed:** `PUBLISH_CLOSE.bat` at the repo root — stages the whole `deploy_kits` tree, prints the payload
before committing, and ends by comparing `rev-parse HEAD` to `rev-parse origin/main`, printing GREEN only
when they are the same hash.

> **RULE: the method that publishes a kit and the method that publishes the record are not the same
> method — and a publish is not verified until the record's own bytes are shown to exist on the remote.**

### F-116 — the linchpin pinned the current Register to a phantom · FIXED

`CANONICAL_MANIFEST.md`'s Register row read `d0da61a095435b1a3ef559c210788c37`, which is the real file.
Its **own Phase-0 filename footer** read `KB_Register_v5_11_S186.md` (`d5ec45a5…`). A full index of all
936 files in the repo — hashed as stored **and** with line endings normalised both ways — finds **no file
carrying `d5ec45a5`**. The token appears in exactly one place in the entire repository: that footer.

It is a leftover from one of the five v5.11 intermediate states, or it was never real. Both are the same
fault: **a hash written from something other than a file.** Direct descendant of **F-109**, where two
characters were added to a partial pin "to make it look complete" — and this time inside the document
every other document is verified against. Phase 0 hash-compares every row; at the S187 open this token
halts the session on the linchpin.

> **RULE: a hash is transcribed from a file or it is not written. A document's own footer is a claim
> about itself and gets checked like any other claim — the body being right does not acquit the footer.**

### F-117 — the pin list attests to a manifest that does not exist · list fixed, TOOL FIX OWED

`S186_V1b/live_pins.txt` header: `manifest_md5: 04eff42ce5f642e9ebadbcdfc4f7f5a2`. The published manifest
is `d1f97e1a…`. No manifest anywhere hashes to `04eff42c`. The list was generated mid-close against an
intermediate manifest that was then re-pinned twice — **the attestation was true when written and expired
without anyone being able to notice.**

The deeper fault is in the tool. `verify_live_pins.py` v1.1 was built at this same session to close F-110,
and it reads only the *word*: `register_pin_verified: yes|pending|absent`. It then **prints** the manifest
name and md5 as though verified — `source : VERIFIED against the manifest CANONICAL_MANIFEST.md (md5
04eff42c…)` — without ever comparing that md5 to a file. The live run shown to the owner printed exactly
that line while the md5 in it was fiction. **F-110 was "a checker that could be stale never checked its
own source"; F-117 is that same checker, one level up, trusting a word where it could have compared bytes.**

**Fixed for now** by regenerating the list against the corrected manifest (`S186_V1c`). **Owed at S187:**
`verify_live_pins.py` must hash the manifest it names and refuse when the md5 does not match — the check
is three lines and the failure it prevents is the one that made this finding.

> **RULE: an attestation is a promise; a hash is a proof. A tool that prints a hash it never compared
> is manufacturing confidence.**

### F-118 — a duplicate-pin conflict resolved toward the superseded build · FIXED (the RED)

The first live-pin run against the published list: **RED, 1 drift.**

```
DRIFT  /root/finance/finance_ui/finance_workbench.html
       record says : 45cb85b353ba8675114ca23eaa6afa90
       box is  now : 18c71e63e5f1790c07d7fa3df53cd24e
```

`finance_workbench.html` shipped **twice** at S186 — first in `S186_R2a` (`45cb85b3…`), then a newer build
inside `S186_I1a` (`18c71e63…`). The box carries the I1a build, correctly: I1a installed after R2a and
passed 351/351. The Register pinned the **R2a** value. `18c71e63` appeared **nowhere** in the canon.

**Cause.** At the close the duplicate-path guard — built the same morning as part of the F-111 fix — fired
because the Register pinned one path twice. The conflict was resolved by deleting a row, and **the row
deleted was the current one.** The guard did its job: it proved two pins disagreed. It cannot say which is
true. That question was then settled **from the documents instead of from the box**, which is the precise
inverse of **D321(d), "the box wins."**

**This is the first RED in the project's history caused by the record rather than by the box** — and it is
therefore the first proof that the pin checker earns its keep in the direction nobody designed it for.
Blast radius nil: no live file was ever wrong, and a full-file replacement built on the stale pin would
have overwritten the newer workbench with the older one — which is exactly **F-97**, the fault the whole
pin system exists to prevent. **The system caught the fault the system was built to catch, in its own
records.**

> **RULE: a guard that detects a conflict must never be allowed to resolve it. Two pins for one path is a
> question, and the box answers it — not the document, and not the person tidying the document.**

### F-119 — Phase 0's only command failed, and nothing said so · FIXED

`START_HERE_SESSION_187` gives the next session one mechanical command: clone the repo and run
`md5sum -c MD5SUMS_ALL.txt`. Run today, it returns **70 OK, one "No such file or directory"** for
`KB_Register_v5_10_S186.md`, and a non-zero exit. v5.10 was an intermediate bump; when v5.11 replaced it
the row was never removed. **The door to Session 187 was locked and the lock was invisible** — nobody runs
Phase 0 at the end of the session that wrote it.

Note the shape: the checksum file was *internally consistent* with itself and *inconsistent with the
folder*. That is **F-88** stated in reverse, and it is why the inverse check now runs too: every file on
disk is either listed or explicitly excluded with a reason.

> **RULE: a close-out is not finished until the next session's opening command has actually been run and
> seen to exit clean. Writing the instruction is not testing the instruction.**

### F-120 — three checksum files for one folder, two of them stale · FIXED

`KB_canon_all` shipped `MD5SUMS_ALL.txt` (71 rows, authoritative and named by `README_VERIFY.md`),
`SUMS.md5` (52 rows, **4 mismatches**) and `MD5SUMS.txt` (10 rows, **1 mismatch and a malformed line**).
Nothing reads the latter two; they are residue from earlier kit shapes. But a folder that ships three
answers to "what are the correct bytes here" has no answer — and two of the three would convict a correct
file. **D202's one-authored-source rule, broken inside the folder that rule exists to protect.**

**Fixed:** `MD5SUMS_ALL.txt` is the single authority; the other two are in `deploy_kits/_attic_S186/`,
moved and **not deleted**, so the bytes and their history survive.

> **RULE: one folder, one checksum authority. A second one is not redundancy — it is a coin toss.**

### F-121 — a gate widened in scope started crying wolf · FIXED

`PUBLISH_CLOSE.bat` v1 kept F-100's gate ("any file `.gitignore` excluded from what I staged is
suspicious") while widening `git add` from one kit folder to the whole `deploy_kits` tree. Pointed at
eleven sessions of history it immediately refused the commit — over two `__pycache__/*.pyc` files in S182
kits and a stray `live_pins.tsv` in S183. All three are ignored **on purpose**; none was in the payload.

It refused for the wrong reason, and nothing was committed or pushed — the failure was safe. But a gate
that fires on old junk is a gate the operator learns to click past, which is **D316** exactly.

**v2 narrowed the scan to folders with staged changes — and failed identically on the next run**, because
the retired junk had been moved into `_attic_S186/`, which *was* a staged folder. **Both versions were
asking a proximity question — "is anything ignored *near* what I staged?" — and proximity is not the
fault.** The fault F-100 describes is precise and content-based:

> **did `.gitignore` drop a file that the payload's own checksum list names?**

`SUMS.md5` (kits) and `MD5SUMS_ALL.txt` (the canon set) **are** that list. **v3** verifies every name in
that list against `git ls-files` — exact, and structurally blind to junk that was never payload. Ignored
files are still printed, as INFO, and do not block.

v3's own rehearsal then caught a third form of the same error before it could waste a run: the *retired*
`SUMS.md5` moved into the attic was read as though it described the attic. Two fixes, both principled —
a retired list is renamed so it cannot pass for a live one (**the F-120 lesson applied to itself**), and a
folder is treated as a payload **only if it carries `KIT_ID.txt`**, which is exactly what makes a folder
publishable. Rehearsed three ways: the real payload PASSES, an un-tracked `live_pins.txt` is REFUSED, and
restoring it PASSES again.

> **RULE: scope a check to its payload — and define "payload" by what the payload declares about itself,
> never by what happens to sit next to it. A check that fires on things outside the payload does not add
> safety; it spends the operator's willingness to stop.**

> **RULE: rehearse a gate against a real refusal before shipping it. Three versions of this one were
> written; the first two were shipped unrehearsed and both failed on the owner's screen. The third was
> rehearsed and its two remaining defects were found in the rehearsal, not by him.**

**The family these seven belong to.** F-115, F-116, F-119 and F-120 are all *a record that describes a
world it was never compared against*. F-117 is *a check that prints a proof it did not perform*. F-118 is
*a conflict resolved by preference instead of by measurement*. F-121 is the mirror of all of them — a check
so eager it stops being read. Six of the seven were found **only because one RED was taken seriously**;
the seventh was found while fixing the first. **The RED was not the problem. The RED was the only thing
working.**

---

## §7.1 (continued) — S187 · F-122 … F-126 *(appended at the S187 close, the session they were raised)*

> Session 187 shipped **eight kits in one session** — the F-117 structural fix, B5 (the pushed Marg
> export), Daily Flow v2 stage D1, the portal tile chain, and the owner's Sanjeevni Hub with the
> Clinic Design Language — and raised five findings on the way. Three are about the **publishing and
> attestation chain** (F-122, F-123, F-124: the record-keeping machinery asserting things it never
> verified), one is the **test-discipline family firing a fourth time** (F-125), and one is a new
> **installer-shipping rule** (F-126). None is a surveillance code.

### F-122 — the generator minted a phantom manifest hash at every generation, and the checker printed it as a pass · CLOSED STRUCTURALLY (kit `S187_V1a`)

**The session's first act was Runbook v121 item 0 — and the fault fired live while being fixed.**
The `S186_V1c` pin list attests `manifest_md5: 78881ddd0b73ce51ffdbaa7e35bc95e4`. An md5 index of the
full 157-commit history — all 24 committed manifest states, both line-ending normalisations — matches
it **nowhere**. V1b's `04eff42c…` is the same, and F-116's `d5ec45a5…` before that: **three phantom
manifest hashes in two sessions, all minted by the same mechanism.**

The mechanism is structural, not a slip. The manifest's own self-row reads *"recomputed last, each
EOS"* — so at the moment `gen_live_pins.py --manifest` hashes the file, it is hashing a state that
the close-out will edit again before publishing. **A true hash of a state that no longer exists is
indistinguishable from an invented one.** The Runbook's "~3-line fix" (hash the named manifest,
compare) was therefore **unbuildable as written**: there is no stable whole-file value to compare TO.

The real fix required noticing that the box **does** hold the canon: `/root/deploy/repo` is the D317
chain's clone, git-pulled at every install. **v1.2 of both tools:**
- `gen_live_pins.py` **never writes the manifest's whole-file md5 again.** It writes
  `manifest_current_register_pin` — the md5 the manifest's CURRENT `KB_Register` row carries, which
  is **stable** (it changes only when the Register version changes) and **IS the claim** being made.
- `verify_live_pins.py` **proves the claim on this machine**: it finds the file in
  `repo/deploy_kits/KB_canon_all/` that hashes to the pin list's `source_md5` (**by hash, not
  filename — D188**), parses the `CANONICAL_MANIFEST.md` beside it, extracts its CURRENT Register
  pin, and compares. **The word VERIFIED is printed only after both comparisons pass**; every other
  outcome states its reason and caps the verdict at AMBER. A stale repo clone fails the hash-hunt
  naturally, so staleness reads AMBER with a pull hint — never false-GREEN.

Selftests: checker 43/43 (VERIFIED only on proof · GREEN only on proof · stale-repo → pull hint · a
manifest with two CURRENT Register rows refuses rather than guesses) · generator 22/22. Proven
against the real repo clone before shipping; the F-110 draft hash `ff509b01…` correctly refuses.

**Family:** F-109 (a hash written beyond its evidence) · F-110 (a phantom source hash) · F-116 (a
phantom self-reference) · F-117 (the checker printed an untested claim). **RULE: never attest to the
hash of a file whose rules say it will change after you hash it; attest to the stable value inside it
that constitutes the claim — and a checker may not print a claim it did not test.**

### F-123 — two manifests in one repo, the stale one still calling itself canonical · FIXED at this close

Found en route to F-122, by the hash-hunt that indexes the repo. The repo carried **two divergent
`CANONICAL_MANIFEST.md` files**: the real linchpin in `deploy_kits/KB_canon_all/` (S186 post-close,
checksum-covered), and `canonical-docs/CANONICAL_MANIFEST.md` — **nine sessions stale, "STATUS:
canonical — current at S177" in its own header**, sitting beside sixteen superseded Fault-Register
and Runbook versions, covered by **no** checksum file. Any tool or session pointed at
`canonical-docs/` would attest against S177 canon and report success.

**F-120 recurring one level up: rival checksum files became rival manifests.** Retired at the S187
close: the `canonical-docs/` folder moved to `deploy_kits/_attic_S187/canonical-docs/` (**moved, not
deleted**), its manifest **renamed** (`CANONICAL_MANIFEST.md.RETIRED_S177_stale`) so it can never
again pass for a live one — the F-120 lesson applied to itself — and a one-line `README_RETIRED.md`
pointer left at the old location. **RULE: exactly ONE file in the repo may be named
`CANONICAL_MANIFEST.md`; a superseded copy of a self-describing document must be made to say so,
because its own STATUS line outranks its folder name in every reader's eyes.**

### F-124 — the publisher swallowed a fatal and printed success · FIXED the same hour (`PUSH.bat` v2; `PUBLISH_ALL.bat` default)

The `S187_V1a` publish failed exactly this way, live: a stale `.git/HEAD.lock` (the `.git` folder
carries a graveyard of them from S185/S186 crashes) blocked `git commit` with a **fatal error**;
`PUSH.bat` v1's `|| echo (nothing new to commit - continuing)` read the fatal as an empty commit,
pushed nothing, and printed `---- S187_V1a pushed`. Origin HEAD proved it: unchanged.

**The fourth publishing fault in three sessions** — F-100 (success while git dropped a file), F-115
(the publisher could not carry a close-out), F-121 (the widened gate cried wolf) — **all the same
shape: the tool asserted an outcome it never verified.** Fixed in v2: refuse up front on
`HEAD.lock`; run `git diff --cached --quiet` BEFORE committing so "nothing to commit" is decided
ahead of time and a commit failure can only be real; after pushing, **verify `git rev-parse HEAD`
equals `git ls-remote origin HEAD` and refuse to print success otherwise** — the projection is the
check, applied to publishing. v2 proved itself in the field the same hour: one honest refusal on the
lock, one verified publish. At the session's end the same gates were folded into
**`PUBLISH_ALL.bat`** — one whole-repo publisher (add-everything + F-100 gitignore gate + lock
refusal + real-failure commit + origin-HEAD verification), adopted as **the default publish method**
(D328) and proven on its first field run, which published kit `S187_H1c` and the sender's desktop
dressing in one verified push. **RULE: `|| echo` is how a fatal becomes a footnote; a publisher may
print "pushed" only after comparing the remote to the local head.**

### F-125 — a state-asserting test, broken by the first real datum · FIXED (kit `S187_P1b`)

The `S187_P1a` install went **RED on the live store — 388/389 — and the one failure was OURS.** The
M1a-era check *"staging holds exactly one pending row"* counted ALL pending rows in
`marg_push_staging`; that very morning **reception's first genuine push from the medical PC** had
landed a real pending row (test stub + real push = 2). A test that was true until the world produced
real data — **F-106's exact pattern inside a test, and the fourth time this family has fired**
(F-84's "test asserting an environment accident" · F-87 · F-106). The D317 gate did precisely what
it exists for: restored finance byte-perfect, never touched the portal, **no incident** — the RED
was the system working.

Fix: the check is scoped to the test's **own bytes** (`file_md5 = md5(stub)`) — behaviour, not store
population. Then **re-rehearsed against the exact failing condition**: a copy of the store seeded
with a real pending push passes the full suite with the differential clean. **RULE: a test asserts
behaviour, never store population — and a fixed test is re-run against the state that broke it, not
against the state where it always passed.**

### F-126 — an installer whose goodbye died after all the real work had succeeded · FIXED (standing rule)

`install_h1a.sh` completed every real step — gates green, page placed, pins updated, 400/400 — and
then aborted on a **syntax error in its own tail**: a sed-injected echo had broken shell quoting in
the closing message. Harmless in effect, poisonous in principle: **an installer that dies after
acting is indistinguishable, at the console, from one that died before** — the operator is left to
forensically determine what applied. Cause: string-surgery on a shipped installer, verified only
along the rehearsed path (which exercised the gates, not the goodbye).

**Standing rule adopted: every installer is syntax-checked WHOLE — `bash -n install_*.sh` — before
it ships.** A rehearsal exercises one path; `bash -n` reads them all. Applied to `install_h1b.sh`
and `install_h1c.sh` the same session (both carry the check in their headers), and owed to every
future kit. Kin: F-63 (the wired route never exercised) — the same lesson at the shell layer.

---

**The family these five belong to.** F-122 and F-124 are *a tool asserting what it never verified* —
the F-88/F-97 lineage reaching the attestation and publishing layers. F-123 is *a stale record
wearing a current label* (F-45/F-108/F-120). F-125 is *a test asserting the world instead of the
behaviour* (F-84/F-87/F-106), caught by a gate built four findings earlier. F-126 is new: *the
untested path was the exit*. Four of the five were fixed the same session; the fifth (F-122) was
fixed structurally by removing the possibility of the claim, which is the only durable kind of fix
this family has ever accepted.

**END OF FAULT → ACTION REGISTER v2.22 — §7, §7.1 and the CHANGELOG are the last sections. If any of the three is absent, this file is truncated and must not be used as canonical.**
