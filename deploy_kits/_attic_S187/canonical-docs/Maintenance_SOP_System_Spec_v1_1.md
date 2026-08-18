# Maintenance & SOP System — Spec
## Advanced Orthopaedic Surgery Centre, Bareilly
**Version 1.1 · 30 June 2026 · Session 19**
Owner: Dr. Manoj Agarwal · Maintained with: Claude (per session)

> **What this document is.** The specification for the clinic's third
> Claude project — a dedicated maintenance and operations centre whose
> memory holds the entire automation stack, whose connected sources hold
> all reference material, and whose purpose is to make every future
> incident, repair, and system change faster, more guided, and less
> dependent on the doctor's recall.
>
> **When to create this project:** after `Diagnostics.gs` is live and
> the incident system has run for at least one real clinic day. The
> project is created at that point — not before — so it opens with a
> live system to describe, real incidents to reference, and proven
> fallback protocols to document.
>
> **Companion documents:** Umbrella Architecture v1.4 · Master KB v1.5 ·
> Call Console Evolution Spec v1.0 · Diagnostics & Surveillance System
> Spec v1.0

---

## 1. Why a separate project

The build project ("Systems & Automation") is where new things are created.
The maintenance project is where live things are kept healthy.

These are different disciplines:

| Build project | Maintenance project |
|---|---|
| Creates new modules | Monitors running modules |
| Needs to know the full architecture | Needs to know the current live state |
| Sessions are forward-looking | Sessions are diagnostic or corrective |
| Code is the primary output | Guidance and SOPs are the primary output |
| Claude needs design context | Claude needs operational context |

Mixing them creates a project that is too large, with conflicting context,
where the assistant has to navigate build history to answer an operational
question. A dedicated maintenance project has focused memory — every fact
in it is relevant to keeping the system running.

---

## 2. Project memory — what it holds

The maintenance project's memory is the complete operational picture of
every live component. It is structured so that describing a symptom to
Claude returns an immediate, specific, guided response — not a search
through build history.

### Core documents (always in project knowledge)
| Document | Why |
|---|---|
| Master KB v1.5 (latest) | Every system, every parameter, every data contract |
| Umbrella Architecture v1.4 (latest) | The shape, principles, data bank charter |
| Diagnostics & Surveillance Spec v1.0 | The fault codes, severity levels, protocols |
| API Quick Reference Card (latest) | The three MyOperator systems + OBD |
| Troubleshooter (Callback_Dashboard_TROUBLESHOOTER_v1.1) | Decision tree for all known failure modes |
| This document | The maintenance project's own purpose and structure |

### SOPs — one per live system
Each SOP is a standalone document structured identically:
- What the system does (one paragraph)
- Components and where they live
- Normal health indicators (what "working" looks like)
- Known failure modes and their fix paths
- Emergency contacts
- Manual fallback

| SOP | System covered |
|---|---|
| `SOP_Dashboard_AppScript.md` | Dashboard, WebApp.gs, all Apps Script files |
| `SOP_VPS_Services.md` | wa-receiver, wa-notifier, call relay, WA send relay |
| `SOP_WhatsApp_Token.md` | Token rotation — high-risk, Lokesh coordination required |
| `SOP_FollowUp_Tracker.md` | Tracker core, daily push, **auto-push folder watcher + Startup auto-start (S19)**, VPS migration (when done) |
| `SOP_Revenue_Reconciler.md` | Ingest, match ladder, held-bills review |
| `SOP_Biometric_Attendance.md` | attlistener, att_dashboard, cron mailers, Secureye device |
| `SOP_MyOperator_IVR.md` | IVR routing, agent extensions, panel settings |

SOPs are written once and updated when a system changes — same session
discipline as the Master KB.

---

## 3. Connected sources

The maintenance project is connected to the same live sources as the build
project, but reads them with a different purpose — not to understand
architecture, but to find current state quickly.

### GitHub (`drmanoj-clinic-automation`)
- Read-only, connected
- When a fault involves code, Claude reads the current file directly
- No need to re-upload files or paste code into chat
- The exact running code is always available

### Google Drive (clinic account: `drmka.ortho@gmail.com`)
Connected for:

**Incident reports folder** (to be created)
Path: `Clinic Automation / Incident Reports /`
Every incident auto-generates a Google Doc here (via `Diagnostics.gs`)
containing: fault code, timeline, what was tried, resolution.
These accumulate over time — patterns become visible.

**SOP documents folder**
Path: `Clinic Automation / SOPs /`
The live SOP files. The maintenance project can read them. When a SOP
is updated, the Drive version is the master copy.

**Handoff kit folder**
Path: `Clinic Automation / Handoff Kits /`
Cold backup zips. The maintenance project can reference the latest handoff
for the exact state of any system at a point in time.

**Code exports folder**
Path: `Clinic Automation / Code Exports /`
When an Apps Script file is updated, the old version is exported here
before replacement. Provides a rollback path without needing Git history.

### Notion ("Clinic HQ")
- Connected
- Tech & Systems Register — current status of every module (Live / Planned / Paused)
- Active Projects board — what is being built right now
- Decision log — why things are the way they are
- When diagnosing a fault, Claude can read the current module status from
  Notion to confirm what the expected behaviour should be

---

## 4. The incident escalation document

When an incident is escalated to the doctor, `Diagnostics.gs` creates a
Google Doc in the Incident Reports folder automatically. This is what the
doctor receives — not just a notification but a complete document.

**Document structure:**
```
INCIDENT REPORT — [Fault Code]
[Date] [Time]

SUMMARY
[Plain description of what failed]

IMPACT
[What was unavailable and for how long]

TIMELINE
[Time] Fault detected by [client poll / morning check / watchdog]
[Time] Full diagnostics triggered automatically
[Time] Specific cause identified: [cause]
[Time] Staff banner displayed
[Time] Acknowledged by [staff member] at [time]  (if applicable)
[Time] Fix steps attempted: [what was tried]
[Time] Escalated to doctor

DIAGNOSIS
[Exact cause — specific, technical, actionable]

WHAT NEEDS TO HAPPEN
[Specific action required — numbered, clear]

CURRENT FALLBACK IN USE
[What staff are doing right now while the system is down]

CONTACTS IF NEEDED
[Relevant contact for this fault type, e.g. Lokesh Kumar VB / Hostinger]

RESOLUTION (to be filled when resolved)
[What fixed it] [Time resolved] [Who resolved it]
```

This document lives permanently in Drive. Over time it becomes the clinic's
incident history — invaluable for identifying patterns, justifying
infrastructure decisions, and onboarding future technical support.

---

## 5. The surveillance scope — full stack

The diagnostics system covers every live module. This table is the
master surveillance register — updated as new modules go live.

| Module | What is monitored | Fault codes | Severity |
|---|---|---|---|
| Dashboard (Apps Script) | API health, sheet tabs, Script Properties, agent roster | `API_*`, `TAB_*`, `AKEY_*` | CRITICAL |
| Call relay (VPS :8097) | Health endpoint ping | `VPS_CALL_RELAY_DOWN` | CRITICAL |
| WA send relay (VPS :8096) | Health endpoint ping | `VPS_WA_RELAY_DOWN` | IMPORTANT |
| WA receiver (VPS :8095) | Health endpoint ping | `VPS_WA_RECEIVER_DOWN` | IMPORTANT |
| wa-notifier (VPS) | Indirectly — ntfy push success/fail | — | WARNING |
| Follow-up ingest | `Followups_Today` populated after 9 AM | `FOLLOWUPS_NOT_LOADED` | CRITICAL |
| Follow-up auto-push watcher (S19) | Workbook lands in `outputs\` but `Followups_Today` not refreshed (watcher process not running on clinic PC, or push failed). Also covers malformed due-dates. | `FOLLOWUPS_NOT_LOADED`, `FOLLOWUPS_DATE_MALFORMED` | CRITICAL |
| Patient_Master mirror | Tab freshness (last 3 days) | `PATIENT_MASTER_STALE` | WARNING |
| Revenue reconciler | Last run within 7 days | `REVENUE_STALE` | WARNING |
| Biometric attendance | `attlistener` health endpoint (:8041) | `ATTENDANCE_LISTENER_DOWN` | IMPORTANT |
| Call_Feed | Tab freshness (last 48h) | `CALL_FEED_STALE` | WARNING |
| WhatsApp token | Token age (warn at 80 days, alert at 90 days) | `WA_TOKEN_AGING` | WARNING→CRITICAL |

New modules added to this register in the same session they go live.

---

## 6. Maintenance SOP — the discipline

### When a system is changed (build project session)
1. The relevant SOP is updated in Drive
2. The Master KB is updated (as always)
3. If the change affects a monitored component, the fault code list in
   `Diagnostics.gs` is updated
4. The maintenance project's memory is refreshed (delete old KB → add new)

### When an incident occurs
1. `Diagnostics.gs` creates the incident record automatically
2. Staff follow the banner's fallback protocol
3. Doctor receives the pre-packaged escalation document if unresolved
4. Doctor opens the maintenance project — describes the symptom
5. Claude has the full stack in memory — responds with specific guidance
6. Fix is applied, resolution documented in the incident report
7. If the incident reveals a new failure mode, the SOP is updated

### Weekly (doctor's periodic review)
- Review `System_Health` tab: any recurring incidents? Any patterns?
- Review the Notion Tech & Systems Register: any module status that needs updating?
- If a recurring fault is found: either fix the root cause or add it to
  the diagnostics as a named check with a better fix path

### Monthly
- Confirm all SOPs are current
- Confirm VPS services are running on the latest code (check against GitHub)
- Review ntfy.sh quota (free tier 429 risk — plan for self-hosting when needed)
- Review WhatsApp token age (rotate before 90 days, coordinate with Lokesh)

---

## 7. The maintenance project setup — step by step

**Prerequisites:** `Diagnostics.gs` live, at least one real incident
documented, all SOPs drafted.

**Step 1 — Create the project in Claude**
- Name: `Dr Manoj Clinic — Maintenance & SOP`
- Custom instructions: one paragraph describing the project's purpose,
  pointing to the build project for architecture questions, and listing
  the connected sources

**Step 2 — Add core documents to project knowledge**
- Master KB (latest version)
- Umbrella Architecture (latest version)
- Diagnostics & Surveillance Spec (this document, latest version)
- API Quick Reference Card (latest version)
- Troubleshooter document (latest version)

**Step 3 — Connect sources**
- GitHub: `drmanoj-clinic-automation` (read-only)
- Google Drive: `drmka.ortho@gmail.com` account

**Step 4 — Create Drive folder structure**
```
Clinic Automation /
├── Incident Reports /    ← auto-populated by Diagnostics.gs
├── SOPs /                ← one doc per system
├── Handoff Kits /        ← cold backup zips
└── Code Exports /        ← pre-update snapshots of live files
```

**Step 5 — Write the first SOPs**
Priority order (most-used systems first):
1. `SOP_Dashboard_AppScript.md`
2. `SOP_VPS_Services.md`
3. `SOP_WhatsApp_Token.md`
4. `SOP_FollowUp_Tracker.md`

**Step 6 — Add the cross-pointer**
In the build project's custom instructions, add:
"For maintenance, incident response, and system SOPs, use the
`Dr Manoj Clinic — Maintenance & SOP` project."

In this project's custom instructions, add:
"For building new features, use the `Dr Manoj Clinic — Systems & Automation`
project. GitHub is connected here for code reference."

---

## 8. What this enables

**Before this system:**
A fault is discovered by a staff member noticing something is wrong.
The doctor is called without context. The doctor has to recall which
system is involved, where the code is, what the fix is, and who to call.
This takes 20–60 minutes on a bad day.

**After this system:**
A fault is detected automatically within 90 seconds. Staff already have
their fallback workflow. The doctor receives a complete incident document.
Opening the maintenance project, the doctor describes the symptom and
receives specific, step-by-step guidance from an assistant that already
knows the entire stack. Resolution time drops to minutes for known fault
types.

**The compounding effect:**
Each incident adds to the incident history in Drive. Over months, patterns
emerge — which systems are most fragile, which fault codes recur, where
investment in hardening would pay off. The maintenance project becomes
smarter over time, not just a reference but a learning system.

---

## 9. Decisions locked for this spec

| # | Decision |
|---|---|
| M1 | Maintenance project created AFTER Diagnostics.gs is live — not before. |
| M2 | Incident reports auto-generated as Google Docs in Drive — permanent record. |
| M3 | SOPs are Drive documents, not project knowledge — Drive is the master, project knowledge holds the KB. |
| M4 | The maintenance project reads GitHub but never writes it — same rule as the build project. |
| M5 | WhatsApp token rotation SOP flagged HIGH RISK — always requires Lokesh coordination before execution. |
| M6 | New modules added to the surveillance register in the same session they go live. |
| M7 | Monthly WhatsApp token age review — rotate before 90 days. |

---

## 10. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 29 Jun 2026 | First version. Full spec agreed in Session 18 design discussion. |
| 1.1 | 30 Jun 2026 | Session 19: added the follow-up auto-push folder watcher to the surveillance register (§5, per M6) and to the `SOP_FollowUp_Tracker.md` scope (§2). |

*End. Keep one copy in Notion "Clinic HQ" and one in the handoff kit.*
