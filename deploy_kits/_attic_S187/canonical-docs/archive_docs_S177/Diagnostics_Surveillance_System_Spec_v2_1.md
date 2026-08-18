# DIAGNOSTICS & SURVEILLANCE SYSTEM SPEC — v2.1 (CONSOLIDATED, SELF-CONTAINED)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Consolidated 09 July 2026, Session 131. Supersedes v1.1 – v1.7 entirely. There is no delta chain.**

> **A single, fully self-contained master.** Section bodies are transplanted **verbatim**. The
> **S100 policy** — *"single file, no delta chain"* — is now applied to this document.

---

## §0 — PROVENANCE, AND TWO DEFECTS THE CONSOLIDATION FOUND

| Source | Sections | Bytes | md5 | Recovered from |
|---|---|---|---|---|
| v1.1 | §1 – §13 | 20,252 | `41a55f3d…` | git `docs/` |
| v1.2 (S53) | `§NEW` | 3,118 | `e7da5ddf…` | `DrManoj_Clinic_ColdKit_Session53_2026-07-03.zip` |
| v1.3 (S61) | `§NEW` | 4,293 | `9748ca2d…` | `Session61_ColdKit.zip` |
| v1.4 (S62) | `§NEW` | 5,519 | `9b2693ee…` | `Session62_ColdBackup_canonical_docs.zip` |
| v1.5 (S63) | §NEW-A · §NEW-B · §NEW-C | 5,878 | `24c4b192…` | git `canonical-docs/` |
| v1.6 (S124) | §NEW-D … §NEW-G | 7,920 | `03971673…` | git `canonical-docs/` |
| v1.7 (S125) | §NEW-D … §NEW-I | 13,989 | `eeefabd3…` | project knowledge + git |

### Defect 1 — three different sections, one name

**v1.2, v1.3 and v1.4 each define a section called `§NEW`.** Three unrelated check families —
the stale-list sentinel, the VPS watchman, and timer freshness — all under one label. A
cross-reference to `§NEW` in this chain resolved to nothing. **They are renamed here to §L1, §L2,
§L3.** Every original heading string is preserved in a provenance line beneath its new heading.
*(D178 — a label must state what an artefact contains.)*

### Defect 2 — v1.7 abridged what it said it carried forward (F-23)

v1.7's header reads: *"Carries forward v1.6 unchanged."* **It does not.** Its `§NEW-D`, `§NEW-F`
and `§NEW-G` are paraphrased compressions of v1.6's text, and **sixteen lines were dropped** —
including, in `§NEW-G`, the entire evidential basis of the verification standard:

> *"Session 94 recorded the 403 outage as 'Verified end-to-end. Outage closed.' on the strength of
> one call placed immediately after the fix. **The fix was dead seven minutes later; the panel had
> reverted.**"*

v1.7 kept the rule and deleted the reason. **A rule without its reason is the first thing a future
session argues away.**

**Therefore §M2, §M3 and §M4 below carry v1.6's full originals**, not v1.7's abridgements. Nothing
factual in v1.7's shorter text is absent from v1.6's longer text — it was compression, not
correction.

> **This is the argument against delta chains, in one document.** A delta that claims verbatim
> carry-forward, and abridges, is undetectable without both files — and one of those files was
> nowhere in project knowledge.

---

## §0.1 — HOW THIS DOCUMENT IS ORGANISED

| Part | Contains |
|---|---|
| **PART I** (§1 – §12) | The original architecture: problem, principles, detection architecture, check list, incident record, banner, fallback protocols, alert routing, escalation, file structure, sequencing, testing. |
| **PART II** (§L1 – §L5) | The live check families, in the order they were built. |
| **PART III** (§M1 – §M6) | The models and standards that govern all checks. |
| **PART IV** | The fault-code register, the planned maintenance-job family, the surveillance layers, and the growth path. |

**PART I is design. PARTS II–IV record what is running.** Where they conflict, **PARTS II–IV win.**

---

# PART I — THE ARCHITECTURE (v1.1)

## 1. The problem this solves

The clinic automation stack has seven live components running simultaneously.
Each can fail independently. Currently:

- Failures are discovered by staff noticing something is wrong
- Discovery takes minutes to hours — long after the impact has started
- When a failure is found, nobody knows what broke, why, or what to do
- The doctor is called without context — hunting begins
- Manual fallback exists but is not documented at the moment of failure

**The goal:** the system detects its own failures faster than any human can,
diagnoses the specific cause automatically, tells everyone what it found,
shows the fallback workflow immediately, and escalates with a complete
pre-packaged context — all before the doctor's phone rings.

---

## 2. Design principles

1. **Silence is the all-clear signal.** No message at 7 AM = everything
   healthy. A message means something specific is wrong. Staff learn to
   read silence as good news.

2. **Detection is continuous, not periodic.** The 7 AM check is a safety
   net. The real detection happens from the dashboard's own 30-second poll,
   all day, as a side effect of normal operation.

3. **Diagnose before alerting.** The alert message already contains the
   diagnosis. Nobody receives "something is wrong" — they receive "the
   follow-up list was not loaded (Followups_Today tab has 0 rows after 9 AM)."

4. **The banner is a doorway, not a dead end.** Every incident banner has
   three layers: what broke, how to keep working right now, and how to fix it.
   The clinic never stops because a system is down.

5. **Escalation arrives pre-packaged.** By the time the doctor sees an alert,
   it already contains: what failed, when, what was tried, and current status.
   Zero hunting required.

6. **Auto-resolution closes the loop.** When a fault clears, the system
   confirms it automatically. The banner disappears. A resolution is logged.
   Nobody has to manually confirm the system is healthy.

---

## 3. The detection architecture

Two detection paths feed one incident system:

### Path A — Client-side passive detection (every 30 seconds)
The dashboard poll already talks to the API and reads the data on every
refresh. It detects failures as a side effect of doing its job.

**What it detects:**
- API not responding or returning errors
- `allCalls[]` / `pending[]` / `followups[]` arrays empty when they should
  not be (e.g. after 9 AM, follow-ups should have rows)
- Three consecutive failed polls = confirmed fault (not a transient blip)
- Dashboard data structure missing expected keys (server-side crash)

**What it cannot detect:**
- VPS service health independently of an API call
- Sheet tab renames or structural changes
- Script Property drift

### Path B — Server-side active detection (periodic + on-demand)
Apps Script triggers run checks that go deeper than the poll can.

**Scheduled runs:**
- **7:00 AM daily** — full deep diagnostic suite (all checks)
- **Every 30 minutes, 8 AM–9 PM** — lightweight critical checks only
- **9:00 PM daily** — end-of-day health confirmation

**On-demand trigger (the key innovation):**
When Path A detects a fault, it immediately fires `runFullDiagnostics()` via
`google.script.run` — the same mechanism the dashboard uses for all server
calls. The full diagnostic suite runs within seconds of the fault being
detected. The incident record already has a specific cause by the time
any human sees it.

```
Path A detects anomaly (30-second poll)
        ↓
3 consecutive failures confirmed
        ↓
Fires runFullDiagnostics() immediately via google.script.run
        ↓
Diagnostics identify specific cause (seconds)
        ↓
Incident written to System_Health tab with exact cause
        ↓
All staff dashboards show red banner within 30 seconds
        ↓
30-minute watchdog confirms fault still open after 15 min
        ↓
Escalation fires to doctor with full context
        ↓
Next poll / watchdog detects resolution → auto-clears banner
```

---

## 4. The diagnostic suite — complete check list

### Category 1: API health (critical)
| Check | Pass condition | Failure label |
|---|---|---|
| MyOperator token present | `MYOP_TOKEN` Script Property set, length 32, starts `3f` | `API_TOKEN_MISSING` |
| API responding | POST to `/search` returns HTTP 200 | `API_HTTP_ERROR` |
| API returning data | Response contains ≥1 call record for last 24h window | `API_NO_DATA` |
| Token not expired | HTTP 401 / 403 = token issue specifically | `API_TOKEN_EXPIRED` |

### Category 2: Sheet integrity (critical)
| Check | Pass condition | Failure label |
|---|---|---|
| Sheet accessible | `SHEET_ID` Script Property set; sheet opens without error | `SHEET_INACCESSIBLE` |
| `Patient_Master` exists | Tab present, has rows | `TAB_MISSING_PATIENT_MASTER` |
| `Followups_Today` populated | Tab present; after 9 AM has ≥1 row | `FOLLOWUPS_NOT_LOADED` |
| `Followups_Today` dates sane | `Due Date` column values carry a 4-digit recent year (not "2001"/blank) | `FOLLOWUPS_DATE_MALFORMED` |
| `WA_Inbox` fresh | Tab present; has a row within last 12 clinic hours | `WA_INBOX_STALE` |
| `Agents` tab valid | Tab present; at least one `Active=yes` row | `AGENTS_TAB_EMPTY` |
| `Followup_Outcomes` writable | Can append a test row (immediately deleted) | `OUTCOMES_NOT_WRITABLE` |
| `System_Health` tab exists | Auto-creates if missing | `SYSTEM_HEALTH_CREATED` |

### Category 3: Script Properties (critical)
| Check | Pass condition | Failure label |
|---|---|---|
| `DASH_KEY` set | Present, length ≥ 8, no stray spaces | `DASH_KEY_MISSING` |
| `SHEET_ID` set | Present, matches expected format | `SHEET_ID_MISSING` |
| `NTFY_TOPIC` set | Present (needed for alerts) | `NTFY_TOPIC_MISSING` |
| Per-agent keys | `AKEY_11` through `AKEY_16` all present | `AKEY_MISSING` |
| OBD credentials | `MYOP_PUBLIC_IVR_ID` present | `OBD_CONFIG_MISSING` |

### Category 4: VPS services (important)
| Check | Pass condition | Failure label |
|---|---|---|
| Call relay alive | `GET https://followup.dr-manoj.in/call` returns `{"status":"alive"}` | `VPS_CALL_RELAY_DOWN` |
| WA send relay alive | `GET https://followup.dr-manoj.in/wa-send/health` returns alive | `VPS_WA_RELAY_DOWN` |
| WA receiver alive | `GET https://followup.dr-manoj.in/wa-webhook/health` returns alive | `VPS_WA_RECEIVER_DOWN` |

### Category 5: Data freshness (warning)
| Check | Pass condition | Failure label |
|---|---|---|
| Patient_Master freshness | `Patient_Master` has a row modified within last 3 days | `PATIENT_MASTER_STALE` |
| Call_Feed freshness | `Call_Feed` tab modified within last 48h | `CALL_FEED_STALE` |
| Revenue reconciler | Last run within 7 days (if `revenue_ledger` tab present) | `REVENUE_STALE` |

### Severity levels
- **CRITICAL** — clinic operations directly impaired. Immediate alert.
- **IMPORTANT** — a key feature unavailable but clinic can work around it. Alert within 5 minutes.
- **WARNING** — data staleness or degraded performance. Alert in daily digest only.

---

## 5. The incident record — `System_Health` tab

**Writer:** `Diagnostics.gs` only
**Reader:** dashboard (every poll), doctor on request

**Columns:**
```
Incident ID | Detected At | Detected By | Failure Code | Severity |
Plain Description | Status | Acknowledged By | Acknowledged At |
Resolved At | Resolution Note | Escalated To Doctor | Doctor Alerted At
```

**Status values:** `OPEN` · `ACKNOWLEDGED` · `RESOLVING` · `RESOLVED`

**One row per incident.** If the same fault fires again within 1 hour of
resolution, it reopens the existing row rather than creating a duplicate.

---

## 6. The incident banner — what staff see

The dashboard reads `System_Health` on every poll. If any `OPEN` or
`ACKNOWLEDGED` incident exists with severity CRITICAL or IMPORTANT, the
banner appears at the top of the screen — above the KPI tiles, impossible
to miss.

### Banner structure (three layers)

```
┌─────────────────────────────────────────────────────────────┐
│  🔴 SYSTEM ALERT — [Plain description]                       │
│  Detected at 09:14 AM · [Dismiss / I'm looking into it]      │
├─────────────────────────────────────────────────────────────┤
│  📋 KEEP WORKING — How to continue normally right now:        │
│  [Fallback protocol text — specific to this fault type]      │
├─────────────────────────────────────────────────────────────┤
│  🔧 FIX STEPS — What to try:                                 │
│  [Numbered fix steps — specific to this fault type]          │
│                                                              │
│  [✅ Mark as resolved]  [🚨 Escalate to Dr. Manoj]          │
└─────────────────────────────────────────────────────────────┘
```

The `[I'm looking into it]` button sets status to `ACKNOWLEDGED` — the
banner stays visible but the escalation timer resets (giving staff time
to try the fix steps before the doctor is alerted).

---

## 7. Fallback protocols — complete reference

One protocol per failure type. These are the established manual workflows
that existed before automation — surfaced at the moment they are needed.

### `FOLLOWUPS_NOT_LOADED`
**Plain description:** "Today's follow-up list was not loaded this morning."
**Keep working:**
"Use the printed follow-up list from yesterday, or open the Follow-Up Tracker
directly on the PC. Mark outcomes in the Excel sheet as normal. This
dashboard will show the list as soon as it is loaded."
**Fix steps:**
1. Ask Shavez: has the morning Docterz export been done today?
2. If export done: run `push_followups_today.py --push` on the clinic PC.
3. If export not done: export from Docterz (Shavez's morning task), then run the push script.
4. Refresh the dashboard — the list should appear within 1 minute.

### `API_HTTP_ERROR` / `API_TOKEN_EXPIRED`
**Plain description:** "The call system is not responding. Cannot fetch today's call records."
**Keep working:**
"All calls are still being recorded by MyOperator. Use the MyOperator dialer
directly on your phone as normal. Log outcomes in the Excel call log sheet
as backup. The dashboard will recover automatically when the connection is restored."
**Fix steps:**
1. Check internet connection on the dashboard device.
2. Open MyOperator panel directly — if that also fails, it is a MyOperator outage (wait).
3. If MyOperator panel works but dashboard still fails: the call API token may have expired. Contact Dr. Manoj — do not attempt to regenerate the token without coordination.
4. Dr. Manoj to contact Lokesh Kumar VB at MyOperator if token regeneration is needed.

### `VPS_CALL_RELAY_DOWN`
**Plain description:** "The call button is temporarily unavailable."
**Keep working:**
"Use the phone number shown on each row — tap it to dial directly from your
phone (the `tel:` link below each Call button). All calls will still be
recorded by MyOperator and will appear in the dashboard once the call relay
is restored."
**Fix steps:**
1. Try the call button again in 2 minutes — short network interruptions self-resolve.
2. If still failing after 5 minutes: contact Dr. Manoj.
3. Dr. Manoj: SSH to VPS, check `systemctl status wa-call` → if dead, `systemctl restart wa-call`.

### `VPS_WA_RELAY_DOWN`
**Plain description:** "WhatsApp message sending is temporarily unavailable."
**Keep working:**
"Send WhatsApp messages directly from the MyOperator WhatsApp panel or from
the clinic WhatsApp number (9358008080) as normal."
**Fix steps:**
1. Try again in 2 minutes.
2. If still failing: contact Dr. Manoj.
3. Dr. Manoj: check `systemctl status wa-send` on VPS → restart if dead.

### `VPS_WA_RECEIVER_DOWN`
**Plain description:** "Incoming WhatsApp messages may not be appearing in the dashboard."
**Keep working:**
"Check incoming WhatsApp messages directly in the MyOperator panel or on
the clinic WhatsApp number. The dashboard WhatsApp section may be behind."
**Fix steps:**
1. Incoming calls and all other functions are unaffected — this is only WhatsApp display.
2. Contact Dr. Manoj if it persists more than 30 minutes.
3. Dr. Manoj: check `systemctl status wa-receiver` on VPS → restart if dead.

### `FOLLOWUPS_DATE_MALFORMED` (added Session 19)
**Plain description:** "Follow-up due dates are showing the wrong year (e.g. 2001)."
**Keep working:**
"The patient list, phone numbers, and Call buttons all work normally — only
the printed due-date year is wrong. Call the patients as listed; the date
issue is cosmetic and does not affect who is due."
**Fix steps:**
1. Cause: the morning push wrote yearless dates (or an old `push_followups_today.py` is in use). The fix lives in the push script's `to_full_date()` normaliser.
2. On the clinic PC, confirm the current `push_followups_today.py` (the one with `to_full_date`) is in the tracker folder, then re-run: `python push_followups_today.py --push`.
3. Hard-refresh the dashboard (Ctrl+Shift+R). Dates should read `DD Mon 2026`.
4. If still wrong after a correct re-push, contact Dr. Manoj — do not edit the live dashboard.

### `AGENTS_TAB_EMPTY`
**Plain description:** "Staff roster not found — agent names may not display correctly."
**Keep working:**
"All call and outcome functions work normally. Agent names on some rows
may show as 'Unknown' temporarily."
**Fix steps:**
1. Open the Clinic Callback Tracker Google Sheet.
2. Check the `Agents` tab — confirm it has rows with `Active=yes`.
3. If the tab is missing or empty: contact Dr. Manoj — do not edit the sheet without guidance.

### `PATIENT_MASTER_STALE` (Warning only)
**Plain description:** "Patient information may be out of date (last updated more than 3 days ago)."
**Keep working:**
"Patient names and diagnoses shown on call rows may not reflect recent visits.
All calling and outcome functions work normally."
**Fix steps:**
1. Run `push_patient_mirror.py --push` on the clinic PC (Shavez's task).
2. If the export CSV from Docterz is missing, export it first.

---

## 8. Alert routing

### Staff alert (immediate, on fault detection)
- Red banner appears on all open dashboard screens within 30 seconds
- No separate notification needed — staff are already on the dashboard

### Doctor alert (15 minutes after fault, if unresolved)
- ntfy push to `NTFY_TOPIC` — high priority (`urgent` flag)
- Title: `🔴 [Fault code] — [Plain description]`
- Body contains:
  - What failed and when
  - Severity level
  - Whether staff have acknowledged
  - Which fix steps have been tried (if staff tapped "I'm looking into it")
  - Direct instruction if doctor action is needed

### End-of-day digest (9 PM daily, regardless of faults)
- Single ntfy push or email summary
- Lists: all faults detected today, resolution times, any still open
- If all clear: "✅ All systems healthy today."
- Goes to `SUMMARY_EMAIL` + optional `SUMMARY_NTFY`

---

## 9. Escalation to doctor — message format

When the doctor receives an escalation alert, it contains:

```
🔴 SYSTEM ALERT — [Plain description]

Detected: [time]
Severity: [CRITICAL / IMPORTANT]
Status: [OPEN / Acknowledged by Shivani at 10:23 AM]

What was tried: [fix steps staff attempted, if any]

What needs to happen:
[Specific action required from doctor, e.g.:
 "Contact Lokesh Kumar VB (MyOperator) to check the Calling API token.
  His number: [from Apple Notes]."
 or "SSH to VPS: systemctl restart wa-call"]

Current fallback in use: [what staff are doing right now]
```

The doctor reads this and knows exactly what to do. No questions needed.

---

## 10. The Diagnostics.gs file — structure

```
Diagnostics.gs
│
├── runFullDiagnostics()          — master runner, all checks, any time
├── runMorningDiagnostics()       — 7 AM trigger entry point (full suite)
├── runLightweightWatchdog()      — 30-min trigger (critical checks only)
├── runEveningConfirmation()      — 9 PM trigger (full suite + day digest)
│
├── checkApiHealth_()             — Category 1 checks
├── checkSheetIntegrity_()        — Category 2 checks
├── checkScriptProperties_()      — Category 3 checks
├── checkVpsServices_()           — Category 4 checks
├── checkDataFreshness_()         — Category 5 checks
│
├── createIncident_()             — writes to System_Health tab
├── resolveIncident_()            — closes an open incident
├── alertDoctor_()                — ntfy push with pre-packaged context
├── sendEndOfDayDigest_()         — 9 PM summary
│
├── FALLBACK_PROTOCOLS            — map: fault code → { keepWorking, fixSteps }
└── installDiagnosticTriggers()   — sets up all three time triggers
```

---

## 11. Build sequencing

`Diagnostics.gs` is **Step 3** — built after the Call Console (Steps 1+2).
Reason: the console's 30-second poll is the primary detection engine; the
diagnostics layer sits on top of it. Building the poll first means
detection is already live before the full diagnostic suite is complete.

**Step 3a — Core checks + System_Health tab**
All 5 categories of checks. `System_Health` tab creation. 7 AM trigger.
No alerting yet — just logging. Verify checks produce correct PASS/WARN/FAIL
outputs against the live system.

**Step 3b — Banner integration**
Dashboard reads `System_Health` on every poll. Banner renders with correct
fallback text for each fault code. Test each fault type manually.

**Step 3c — Alert routing**
ntfy push to doctor after 15-minute unresolved threshold. End-of-day digest.
30-minute watchdog trigger. On-demand trigger from dashboard poll.

---

## 12. Testing checklist

- [ ] 7 AM trigger fires and produces correct log output
- [ ] All-clear condition = no System_Health open rows = no banner
- [ ] Simulated API failure → correct `API_HTTP_ERROR` incident created
- [ ] Banner appears on dashboard within 30 seconds of incident creation
- [ ] Correct fallback protocol text shown for each fault type
- [ ] Fix steps are specific to the fault, not generic
- [ ] "I'm looking into it" button sets status to ACKNOWLEDGED
- [ ] Doctor alert fires 15 minutes after unresolved CRITICAL fault
- [ ] Doctor alert message contains all context fields
- [ ] Fault resolution → incident status → RESOLVED → banner clears
- [ ] Resolution auto-detected on next watchdog pass (no manual confirm needed)
- [ ] End-of-day digest sends at 9 PM with correct incident summary
- [ ] 30-minute watchdog only runs critical checks (not full suite)
- [ ] On-demand diagnostic trigger fires from dashboard poll anomaly detection

---

---

# PART II — THE LIVE CHECK FAMILIES

## §L1 — FIRST LIVE CHECK: `FOLLOWUPS_LIST_STALE` (Category 1 — process liveness) — LIVE (S53)

> *Verbatim from v1.2 (Session 53). Original heading: `## §NEW — FIRST LIVE CHECK: `FOLLOWUPS_LIST_STALE` (Category 1 — process liveness)`*

**File:** `Diagnostics.gs` (new, in the dashboard Apps Script project).
**Function:** `checkFollowupListFresh` — **time-triggered, 2–3 PM daily** (before the 3 PM calling window).
**Answers:** "Did today's follow-up list actually reach the dashboard?"

**Detection (two failure modes, distinguished):**
- **GENERATION MISSING** — today's `Staff_Action_Today_<yyyy-mm-dd>.xlsx` not found in Drive (searched by exact filename via `DriveApp.getFilesByName`). Message: *check the tracker.*
- **NOT PUSHED** — the file exists but the live `Followups_Today` tab's **newest Due Date** is older than today (dates stored as `DD-Mon-YYYY`; parsed deterministically). Message: *run `python push_followups_today.py --push`.*
- **Fresh** = newest Due Date ≥ today (future "upcoming" rows count). No alert.

**Alert routing:** **email always** (`CFG.EMAIL_TO`, or a `SENTINEL_ALERT_EMAIL` Script Property) + **ntfy phone-push** if a `NTFY_TOPIC_URL` Script Property is set. **No patient data** — counts and dates only.

**Fallback protocol / safety:**
- **Read-only** — writes nothing, touches no writer; reuses `fuSheet_`, `fuReadObjects_`, `dateVal_`, `FU_TAB_TODAY`, `CFG`.
- **Degrade-safe** — if Drive scope isn't granted, the generation check is skipped but the (primary) stale-push check still works from the sheet alone.
- **Fails loud** — if the check itself errors, it emails a "Sentinel could not run" alert; a silent guard is worse than none.
- **Known rare false-positive** — a day with genuinely zero due-today AND zero upcoming rows (only overdue carry-forward, or an empty list) reads as "stale." Accepted trade: cry-wolf occasionally rather than ever miss a real stale list. A future refinement (a push-written freshness stamp) removes it.

**Verified live:** test alert delivered 03 Jul 2026 **2:37:54 PM**; daily trigger armed. Editor test entry point: `testSentinelAlert`.

**Register entry:** `FOLLOWUPS_LIST_STALE` → detection: daily freshness of `Followups_Today` vs today's generated file → owner alert (email + ntfy) → manual fix: `push_followups_today.py --push`.

## §L2 — VPS SERVICE WATCHMAN (Category 1 — process liveness) — LIVE (S61)

> *Verbatim from v1.3 (Session 61). Original heading: `## §NEW — SECOND LIVE CHECK FAMILY: VPS SERVICE WATCHMAN (Category 1 — process liveness)`*

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

## §L3 — TIMER-FRESHNESS CHECK FAMILY (Category 2 — freshness, not liveness) — LIVE (S62)

> *Verbatim from v1.4 (Session 62). Original heading: `## §NEW — TIMER-FRESHNESS CHECK FAMILY (Category 2 — did the sleeping jobs run?)`*

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

## §L4 — DAILY HEALTH REPORT (Category 3 — positive confirmation) — LIVE (D115)

> *Verbatim from v1.5 (Session 63). Original heading: `## §NEW-B — DAILY HEALTH REPORT (Category 3 — positive confirmation) — LIVE (D115)`*

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

## §L5 — DETECTOR: `CALLHOOK_SECRET_MISMATCH_403` — BUILT (S125)

> *Verbatim from v1.7 (Session 125). Original heading: `## §NEW-E — DETECTOR: `CALLHOOK_SECRET_MISMATCH_403` — **BUILT (S125)**`*

**Lane: ASSISTED (Lane 2).** Never auto-fixed — the procedure touches a secret and, potentially, the MyOperator panel. Detect + escalate only.

Both parts of the S124 spec are now built, though not exactly as specced.

**Part 1 — make the receiver speak.** Built as `call_hook_capture.py` v2 (D163). The gate now writes each refusal to `call_hook_rejects/YYYY-MM-DD.jsonl` **before** returning 403. Metadata only: timestamp, reason, masked key label, key length, source IP, method, path. Never the key, never the body. Throttled: full detail for the first **500** refusals per day, then **1 in 100** — a retry storm stays visible without being able to fill the disk. **The 403 response body and status are unchanged**, as required; MyOperator's behaviour depends on them.

*Deviation from spec:* `/healthz` was **not** built. A JSON reject log on disk is strictly more useful than an in-process counter — it survives a worker respawn, which an in-memory counter does not, and a respawn is precisely the event at the centre of this fault. If a `/healthz` endpoint is wanted later for the daily health report, it should read the reject log, not a counter.

**Part 2 — make the watchdog look.** Built as `callhook_watchdog.py` v1.0, `/root/wa/call-hook/callhook_watchdog.py`. Read-only: it opens the access-log glob and the raw-log directory, and writes nothing unless `--state` is passed. It cannot take the clinic down. Offline selftest, 37 checks. Keys are handled only as opaque `key_<md5[:6]>` labels; there is no flag to unmask.

**Not yet scheduled.** Two defects must land first (§NEW-H). Note that it exits **1** on WARN, so a naive `OnFailure=` will fire all day on already-fixed 403s.

---

---

# PART III — MODELS AND STANDARDS

## §M1 — THE RESPONSE MODEL (how faults are acted on) — LOCKED S63

> *Verbatim from v1.5 (Session 63). Original heading: `## §NEW-A — THE RESPONSE MODEL (how faults are acted on) — LOCKED S63`*

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

> ⚠️ **D113 IS AN INTENT, NOT A FACT — corrected by D204 (Session 132).** The watchman that exists is
> **read-only**; §L2's own words: *"reports only; never starts/stops/changes a service."* It **names**
> `systemctl restart <svc>` inside an alert and **has never executed one.** The Lane-1 responder is
> **Deliverable 2, unbuilt and unscheduled.** Lane 1 is empty; per **D112**, promotion is a logged
> decision and no fault has earned one. **During an outage, do not wait for a restart.**
> *This sentence stands as written because it is the record; the correction stands beneath it because
> it is the truth.*

**The single brain = `Fault_Action_Register_v1_Session63.md` (D114)** — every fault (watchman
liveness, timer-freshness, sentinel, + reserved maintenance faults) mapped to lane + exact
procedure. Reference it in every maintenance/incident session.

---

## §M2 — THE SILENT-FAILURE CLASS (S124, learned the hard way)

> *Verbatim from v1.6 (Session 124) — the FULL text, not v1.7's abridgement (F-23). Original heading: `## §NEW-D — THE SILENT-FAILURE CLASS (S124, learned the hard way)`*

`CALLHOOK_SECRET_MISMATCH_403` was named in Session 94, its detection rule was written down, and it was never built. **It recurred within thirty-six hours** and cost two clinic days of outcome data.

**Why nothing noticed. Three separate blind spots, all in one path:**
1. `call_hook_capture.py` returns **403 before `raw_log()` is called**. A rejected delivery writes no raw-log line.
2. The 403 path prints **nothing** to the journal (`log()` is never reached).
3. Therefore the *only* evidence of 4,449 rejected deliveries across three days lived in the **OpenLiteSpeed access log**, which no system reads.

Absence of `call_hook_logs/YYYY-MM-DD.jsonl` is **ambiguous**: it means "MyOperator sent nothing" *or* "MyOperator sent everything and we rejected it". Those are different faults with different fixes, and the file cannot distinguish them.

**The generalisation — a new detection category:**

> **CATEGORY 5 — REJECTED-AT-THE-DOOR.** Any component that authenticates an inbound request must *count and log its rejections*. A gate that refuses silently is indistinguishable from a world that never called. Silence is not evidence of health; it is evidence of nothing.

---

## §M3 — FAIL-OPEN REQUIREMENT FOR HUMAN-FACING CHECKS (D156)

> *Verbatim from v1.6 (Session 124) — the FULL text, not v1.7's abridgement (F-23). Original heading: `## §NEW-F — FAIL-OPEN REQUIREMENT FOR HUMAN-FACING CHECKS (D156)`*

A detection or verification mechanism that sits on a human's critical path is not a safety feature — it is a new failure mode. The duration gate proved this: a vendor-side webhook fault stopped the clinic from recording what patients said, twice in three days.

**Rule.** Any check that can block a staff action must:
- have a **terminal state** (a "cannot determine" answer, reached by a clock anchored to the *event*, never to a page load or a poll start);
- **fail open** into that terminal state, recording the outcome as unverified rather than refusing it;
- and be **reconciled in the background** afterwards, where its failure costs nothing.

A check that fails *closed* is only acceptable where it has **measured** a negative (e.g. a call the system *observed* was never answered), not where it merely failed to observe.

---

## §M4 — VERIFICATION STANDARD (hardened, S124)

> *Verbatim from v1.6 (Session 124) — the FULL text, not v1.7's abridgement (F-23). Original heading: `## §NEW-G — VERIFICATION STANDARD (hardened)`*

Session 94 recorded the 403 outage as *"Verified end-to-end. Outage closed."* on the strength of **one call placed immediately after the fix**. The fix was dead seven minutes later; the panel had reverted.

> **A fix to a webhook, secret, timer, or gate is verified only after (a) one real call, AND (b) a re-check at least one hour later on the same clinic day.** An immediate success distinguishes nothing.

Corollary: **an incident is not closed by a successful test. It is closed by a successful re-test.**

---

## §M5 — CATEGORY 6: ABSENCE OF COVERAGE IS NOT ABSENCE OF EVENTS (S125)

> *Verbatim from v1.7 (Session 125). Original heading: `## §NEW-H — CATEGORY 6: ABSENCE OF COVERAGE IS NOT ABSENCE OF EVENTS (S125)`*

The detector built to correct an absence-of-evidence error **commits the same error.**

`callhook_watchdog.py` folds the access log into counts. If the log does not span the date it was asked about — rotation, retention, a glob that misses the file, a permissions error on one path — `collect()` returns zeros. `evaluate()` then reports **CRITICAL**:

> *"No raw log, and no requests of any kind in the access log. MyOperator is not delivering at all — check the panel subscription, not the secret."*

A confident, specific, wrong diagnosis, pointing the reader **away from** the real cause. Reproduced in the sandbox by feeding it an empty log for 06-Jul.

> **CATEGORY 6 — COVERAGE.** Any check that reasons from the *absence* of records must first prove that it was *looking somewhere records would have been*. A zero must be distinguishable from a blind spot. Where it cannot be, the check must refuse to answer (exit ERROR), never guess.

**Required fix, before the watchdog is scheduled:**
- Assert that at least one parseable `mo-callhook` line exists in the access log whose timestamp falls on `target_date`, **or** that the log's time span brackets `target_date`. If neither holds, exit **3 (ERROR)** with *"access log does not cover \<date\>"* — do not evaluate.
- Until this lands, `--date` on any past day is untrustworthy, including for settling the open question of what happened on 06–07 Jul.

**Second required fix — encoding normalisation (D165).** `mask_key()` hashes the raw `?key=` string as it appears on the wire. The Go client percent-encodes `@` as `%40`; Flask decodes it before the receiver compares. **The same key therefore labels differently in the two tools** — `key_271f88` in the access log, `key_db8972` in `.env`. This produced an hour of alarm on 08 Jul, and could produce a false `CALLHOOK_MULTIPLE_KEYS` on a single subscription. Fix: `urllib.parse.unquote()` before hashing, consistently, everywhere.

---

## §M6 — THE STRUCTURAL FIX: DUAL-KEY ACCEPTANCE (D162, D163, D164)

> *Verbatim from v1.7 (Session 125). Original heading: `## §NEW-I — THE STRUCTURAL FIX: DUAL-KEY ACCEPTANCE (D162, D163, D164)`*

Detection was never sufficient. The fault could still cause an outage; it would simply be found sooner. Session 125 also removed its ability to cause one.

**D162 — dual-key acceptance.** A secret that lives in two places must be rotatable without a synchronised cutover. The receiver accepts `CALLHOOK_SECRET` **or** `CALLHOOK_SECRET_PREV`, compared in constant time (`hmac.compare_digest`). A stale worker and a fresh worker both work. The panel and the VPS may disagree for as long as they like. The disagreement surfaces as a **WARN line naming the key in use**, instead of as a receptionist reporting stuck tiles.

**Why the disagreement was dormant, and why that is the heart of the fault.** `gunicorn -w 1` with no `--preload`: the worker reads `.env` **once, at import**. An edit to `.env` therefore takes effect at the next worker respawn — an unpredictable moment, hours or days later, with no restart, no reboot, and no journal entry to connect cause to effect. On 06 Jul that respawn came at 13:41.

> **Generalise this.** Any shared secret read at import, in a single-worker process, is a mine with an unknown fuse. `WA_APPROVE_KEY` and `FU_UPLOAD_SECRET` have the same shape and should get the same treatment when they are next touched.

**D163 — refusals are recorded before they are refused.** The implementation of Category 5.

**D164 — `.env` is never edited by line number.** `sed -i '<N>s|…'` produced a 61-character run-on line: the correct key with ~49 characters of the shell command welded onto it. Use `awk` + `ENVIRON`, or `printf` to append. WinSCP transfers of `.env` and `.py` must be **Binary**, never Text — Text mode appends `\r` to every line, the same class of invisible-trailing-character fault. The receiver now emits a startup WARNING if its secret contains whitespace, an `=`, or exceeds 40 characters.

---

---

# PART IV — REGISTER, LAYERS, AND WHAT IS PLANNED

## FAULT CODES — `call-hook` family (S125)

| Code | Severity | Meaning | What to do |
|---|---|---|---|
| `CALLHOOK_SECRET_MISMATCH_403` | CRITICAL (2) | Rejections within the last 30 minutes. Failing **now**. Duration data is being lost. | Compare key labels — **normalised**. Align the VPS to the panel. Never print the key. |
| `CALLHOOK_RAWLOG_MISSING` | CRITICAL (2) | Clinic day, past 11:00 IST, no raw log. The detail line distinguishes *arriving and refused* / *not delivering at all* / *accepting and not writing*. | Read the detail line before acting; the three cases have different fixes. |
| `CALLHOOK_403_EARLIER_TODAY` | WARN (1) | Rejections today, none in the last 30 min. Signature of a fault already fixed. | Confirm the fix time. Re-check ≥1h later (§NEW-G). |
| `CALLHOOK_MULTIPLE_KEYS` | WARN (1) | More than one distinct key delivered today → more than one webhook subscription. | **First rule out the encoding trap (D165).** Then check the panel. Escalate to Lokesh. |
| `CALLHOOK_NO_ACCEPTED_TODAY` | WARN (1) | Raw log has lines; access log shows zero 200s. Timestamps disagree. | Do not trust either source until reconciled. |
| `CALLHOOK_SILENT` | WARN (1) | Nothing at all today. **Explicitly not a pass.** | Place one dialler call to disambiguate. |

Exit codes: **0** OK · **1** WARN · **2** CRITICAL · **3** the watchdog itself could not run.

**Procedure (for the Fault → Action Register)** — steps 1–6 as in v1.6, with these amendments:

- **Step 0 (new).** Run `callhook_watchdog.py`. It answers steps 1–4 in one command, without printing a secret. Trust it for *today*; do not trust `--date` on past days until §NEW-H lands.
- **Step 4 (amended).** Compare keys by hash, never by printing — and **`unquote()` before hashing**. The access log holds the wire form (`%40`); `.env` holds the literal (`@`). Comparing them raw will show a mismatch that does not exist, or hide one that does.
- **Step 6 (unchanged).** Prefer aligning the VPS to the panel. Use `awk` + `ENVIRON`. Assert exactly one matching line, only the value changed, identical line count. Restart. Re-verify — and **re-verify again an hour later**.
- **Step 7 (new).** After any `.env` edit, read the startup line from the journal and confirm the key label is the one you intended. The receiver prints it. Do not skip this: on 07 Jul a fix was declared verified by probing the server with the key the session had just written to it, which of course returned 200.

**Escalate to Lokesh only if** the panel is sending a key nobody recognises (after normalisation), or a second webhook subscription genuinely exists.

---

## §P1 — MAINTENANCE-JOB FAMILY (preventive upkeep) — DESIGNED, NOT BUILT

> *Verbatim from v1.5 (Session 63). Original heading: `## §NEW-C — MAINTENANCE-JOB FAMILY (preventive upkeep) — DESIGNED, NOT BUILT`*

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

## SURVEILLANCE LAYERS (updated)

- VPS service watchman (S61) — Lane-1 responder.
- Timer-freshness family (S62) — **still unarmed.**
- Apps Script sentinel (v1.2) — follow-up-list freshness.
- Daily health report (S63) — positive confirmation, 08:00.
- **Rejected-at-the-door (Category 5) — IMPLEMENTED in the receiver (D163).** Reject log live 08 Jul 14:49.
- **`callhook_watchdog.py` (Category 5 + 6) — BUILT, manual runs only.** Blocked on two defects before scheduling.

## Growth path (next diagnostics sessions, one at a time)

1. **Fix the two watchdog defects (§NEW-H), then schedule it.** It currently gives a wrong, confident answer for any date its log does not cover.
2. Arm the timer-freshness checker (S62's parked step).
3. Build the maintenance jobs (disk → token-age → log-prune → backup), feeding the report. **Add reject-log pruning** to that family.
4. Then Patient_Master mirror freshness, Call_Feed freshness, revenue reconciler freshness.
5. **Empty-transcript guard** — 3 of 32 transcripts on 06-Jul were 0 bytes. They surface as AI "Unclear" verdicts when they are recording/transcription faults. Count them; alert on a rising rate.
6. **Apply D162 to the other shared secrets** — `WA_APPROVE_KEY`, `FU_UPLOAD_SECRET`. Same shape, same mine, same fuse.


---

## CHANGELOG — one table, whole history

| Version | Date | Change |
|---|---|---|
| **v2.0** | **09 Jul 2026 (Session 131)** | **CONSOLIDATED, SELF-CONTAINED.** v1.1–v1.7 merged verbatim; the delta chain is retired. Two defects found and fixed in the merge: **(1)** v1.2, v1.3 and v1.4 each named their one section `§NEW` — three unrelated check families under one label, renamed §L1/§L2/§L3 (D178). **(2) F-23** — v1.7 declared *"carries forward v1.6 unchanged"* and in fact abridged §NEW-D/F/G, dropping sixteen lines including the Session-94 evidence behind the verification standard. **v1.6's full originals are restored as §M2/§M3/§M4.** v1.2, v1.3 and v1.4 had to be recovered from cold-backup zips; they were in neither git nor Drive. No design text was summarised or paraphrased in this consolidation. |
| v1.7 | 08 Jul 2026 (Session 125) | Detector `CALLHOOK_SECRET_MISMATCH_403` BUILT. Five new fault codes. Category 6 — absence of coverage is not absence of events. Dual-key structural fix (D162–D164). **Claimed to carry v1.6 forward unchanged; abridged §NEW-D/F/G — see F-23.** |
| v1.6 | 08 Jul 2026 (Session 124) | The silent-failure class; the `CALLHOOK_SECRET_MISMATCH_403` detector spec; the fail-open requirement (D156); the hardened verification standard, with the Session-94 evidence that produced it. |
| v1.5 | 04 Jul 2026 (Session 63) | Response model LOCKED (two lanes). Daily health report LIVE (D115). Maintenance-job family designed, not built. |
| v1.4 | 04 Jul 2026 (Session 62) | Timer-freshness family (Category 2). Heartbeats installed on all three timer jobs via `ExecStartPost`; systemd-native last-run reading ruled out. Checker built + 5/5 behaviour-verified; armed the next session. Register: `FOLLOWUPS_PUSH_MISSED_RUN`, `RECORDING_ARCHIVE_MISSED_RUN`, `TRANSCRIPTION_MISSED_RUN`. |
| v1.3 | 04 Jul 2026 (Session 61) | Second live check family: VPS service watchman (`clinic_watchdog.py`, 5-min timer, nine always-on services, ntfy+Gmail, read-only, anti-spam, fail-loud). Register: `VPS_SERVICE_DOWN`, `WATCHDOG_SELF_FAIL`. Timer jobs excluded from liveness by design. |
| v1.2 | 03 Jul 2026 (Session 53) | First live check: `FOLLOWUPS_LIST_STALE` (`Diagnostics.gs::checkFollowupListFresh`), armed + tested. Diagnostics module founded. |
| v1.1 | 30 Jun 2026 | Fault codes, detection architecture, fallback protocols. |

---

## WHAT THIS DOCUMENT STILL OWES

- **The fault-code register lives in two documents.** This one (PART IV) and `Fault_Action_Register_v1_Session63.md`. **Two writers, one table.** The Register also declares *"nothing here is built or armed yet"* on its front page while its own §2 marks three checks **LIVE**, and it cites *"Source of truth: Master KB v1.30 · Diagnostics Spec v1.4 · Runbook Session 62"* — twenty-five KB versions and twenty-five runbook versions out of date. **One of the two must be retired. The owner's decision.**
- **§M1's two-lane response model** and the Register's §1 two-lane model appear to be the same model, written twice. Reconcile before either is built on.
- **§P1** — the maintenance-job family — is designed and not built. The Maintenance & SOP project does not exist.
- **Growth path items 2–4** remain unbuilt: WhatsApp token-age, Patient_Master mirror freshness, `Call_Feed` freshness, revenue-reconciler freshness.

---

**END OF DIAGNOSTICS & SURVEILLANCE SYSTEM SPEC v2.1 — "WHAT THIS DOCUMENT STILL OWES" is the last section. If it is absent, this file is truncated and must not be used as canonical.**
