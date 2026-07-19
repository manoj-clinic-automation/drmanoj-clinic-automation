# Diagnostics & Surveillance System — Spec
## Advanced Orthopaedic Surgery Centre, Bareilly
**Version 1.1 · 30 June 2026 · Session 19**
Owner: Dr. Manoj Agarwal · Maintained with: Claude (per session)

> **What this document is.** The complete specification for the clinic
> automation system's self-monitoring layer — continuous fault detection,
> automatic diagnosis, guided incident response, staff fallback protocols,
> and escalation to the doctor. This system watches every live module and
> is itself the foundation for the Maintenance & SOP system.
>
> **Companion documents:** Umbrella Architecture v1.4 · Master KB v1.5 ·
> Call Console Evolution Spec v1.0 · Maintenance & SOP System Spec v1.0

---

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

## 13. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 29 Jun 2026 | First version. Full spec agreed in Session 18 design discussion. |
| 1.1 | 30 Jun 2026 | Added `FOLLOWUPS_DATE_MALFORMED` check (Category 2) + fallback protocol — the "2001" due-date bug fixed at the push source in Session 19 is now a monitored fault. |

*End. Keep one copy in Notion "Clinic HQ" and one in the handoff kit.*
