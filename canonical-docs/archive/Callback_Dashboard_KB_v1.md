# Clinic Callback Tracker — System Knowledge Base (v1.1)
**Apps Script project: "Clinic Callback Tracker"** · Dr. Manoj Agarwal Clinic, Bareilly
Built from the full 11-file project export, 29 Jun 2026 (Session 16). This is the authoritative reference for how the IVR call dashboard works and how to diagnose it. Where this disagrees with older notes, **this wins** — it is read from the live code.

---

## 0. The one-paragraph mental model
MyOperator records every phone call. A single Google Apps Script project ("Clinic Callback Tracker") does two separate jobs from that data: (A) it **emails** daily/intraday call reports and maintains worklist tabs in the Google Sheet, on a **schedule of time-triggers**; and (B) it **serves a live web dashboard** that, on each load, **fetches calls straight from the MyOperator API** and renders callbacks-needed, team activity, WhatsApp and follow-ups. **These two jobs share helper code but are independent.** The triggers do NOT feed the dashboard; the dashboard does NOT need the triggers. Confusing the two is the single biggest source of wasted debugging time.

---

## 1. Files in the project (all 11) and what each does
| File | Role | Key functions |
|---|---|---|
| `appsscript.json` | Manifest. TZ = Asia/Kolkata; web app runs **as the deploying user**, access **ANYONE_ANONYMOUS** (key-gated in code). | — |
| `config.gs` | **All tunables + the `CFG` object + `FIELD_MAP`.** No secrets (token/sheet come from Script Properties). | `CFG`, `FIELD_MAP` |
| `MyOperator.gs` | **Live call fetch** from the Search Logs API. Paginated POST with JSON body; unwraps Elasticsearch `_source`, enriches each record (phone10, duration_seconds, direction, is_missed). | `fetchCallsBetween_`, `getToken_`, `enrichRecord_`, **`probeApi`** |
| `Netting.gs` | Turns raw calls into the **net-missed callback list** (missed = status==2; resolved = any connected call same day). | `computeNetMissed_`, `normalizeCall_` |
| `Sheets.gs` | All Google-Sheet writes. **Upserts** the Callbacks_Today tab so staff notes are never wiped. | `upsertCallbacksToday_`, `getOrCreateTab_`, `getSpreadsheet_` |
| `Monitor.gs` | Stats engine + the **monitor tab** + the **summary email** HTML. Also resolves an agent NAME per call from `log_details`. | `computeMonitorStats_`, `agentRows_`, `callAgentInfo_`, `buildMonitorTab_`, `sendSummaryEmail_` |
| `Main.gs` | **Trigger entry points** + manual test runners + trigger install/remove. | `runIntradayDigest`, `runSummaryEmail`, `runMorningReport`, `setupTriggers`, `removeTriggers`, `testIntradayNow`, `dayBounds_` |
| `CallField.gs.gs` | Writes the **`Call_Feed` tab** (a 14-day phone+agent+status archive, PHI-free) for the Follow-Up Tracker to join locally. Its own ~21:30 trigger. | **`rebuildCallFeed`**, `writeCallFeed_`, `installCallFeedTrigger`, `testCallFeedNow` |
| `WebApp.gs` | **The live dashboard server.** `doGet` serves the page; `getDashboardData` builds the snapshot; access-key gate; click-to-call, WhatsApp send/thread, recordings, follow-up loop, escalations, patient 360. | `doGet`, `getDashboardData`, `computeDashboard_`, `dashRole_`, `getFollowups`, `getEscalations`, `triggerCall`, `sendReply`, `lookupPatient360` |
| `Dashboard.html` | The page UI + all client JS that renders the tiles and the expandable sections. | (client `poll()` → `getDashboardData`) |
| `Probe.gs.gs` | Scratch/diagnostic helpers (recording-field probes). Safe place to paste read-only test functions. | `probeRecordingField`, `probeRecordingPlayback` |

> **Naming note:** `CallField.gs.gs` and `Probe.gs.gs` have a **doubled `.gs`** in their displayed names. Harmless (Apps Script appends `.gs` to the stored name "CallField.gs"), but do not rename casually.

---

## 2. The two data paths (memorise this — it prevents 90% of mis-diagnosis)

### Path A — Reports & Sheet tabs (TRIGGER-DRIVEN)
```
time trigger → runIntradayDigest / runSummaryEmail / runMorningReport  (Main.gs)
            → fetchCallsBetween_  (live API)
            → computeNetMissed_ / computeMonitorStats_
            → writes Sheet tabs: Callbacks_Today, Daily_Monitor, Daily_Report_Log, Daily_Summary
            → sends summary EMAIL
```
Separately, `rebuildCallFeed` (CallField.gs.gs) on its own ~21:30 trigger writes the **Call_Feed** tab.

**If these stall:** the *emails* stop and the *Sheet tabs* (incl. Call_Feed) go stale. **The live dashboard is unaffected.**

### Path B — Live dashboard (NOT trigger-driven)
```
browser loads /exec?k=KEY
   → doGet  (WebApp.gs)  serves Dashboard.html
   → page JS poll() → google.script.run.getDashboardData(KEY, force)
   → dashRole_(KEY) gate  (else {error:'Not authorized'})
   → 90-second CacheService snapshot (force=true bypasses it)
   → computeDashboard_():
        fetchCallsBetween_(today)         ← LIVE API, every load
        computeNetMissed_ / computeMonitorStats_
        patientLookup_  (Patient_Master tab)
        waLookup_       (WA_Inbox tab)
        agentCallsMap_ / agentRows_  (agent NAME per call via callAgentInfo_)
        staffStatusMap_ (Callbacks_Today tab)
   → returns { kpis, pending[], resolved[], handled[], recentWA[], agents[] }
   → Dashboard.html renders tiles (kpis) + expandables (the arrays)
```
**If dropdowns are empty but tiles show:** the failure is somewhere in Path B **after** the API fetch — NOT in the triggers, NOT in Call_Feed, NOT (usually) in the token.

---

## 3. Secrets & config (where everything lives)
| Item | Where | Notes |
|---|---|---|
| Call/Logs API token | Script Property **`MYOP_TOKEN`** | The "3f76…c7", 32 chars. Read by `getToken_()`. **Verified present & valid 29 Jun (probeApi: length 32, 5 records).** |
| Target Sheet ID | Script Property **`SHEET_ID`** | The "Clinic Callback Tracker" sheet `1USj…klo0`. |
| Dashboard master key | Script Property **`DASH_KEY`** (or legacy `SECRET_KEY`) | Full-access gate. URL must end `?k=THEKEY`. Stored only in Apple Notes. |
| Staff/agent keys | Script Property `STAFF_KEY` + per-agent `AKEY_<ext>` | Roster-gated via the **Agents** tab. |
| API endpoint / paths | `config.gs` `CFG` | `ENDPOINT=developers.myoperator.co/search`, `DATA_PATH=data.hits`, params in **JSON body** (not query string). |

**Token rule:** this Call/Logs token is a **different** token from the WhatsApp send token. Don't cross them.

---

## 4. The Sheet tabs and who reads/writes them
| Tab | Written by | Read by | Columns |
|---|---|---|---|
| `Callbacks_Today` | `upsertCallbacksToday_` (intraday trigger) | dashboard `staffStatusMap_` | Auto-Status, Priority, Phone, Caller Name, Attempts, First Call, Last Call, After-Hours, **Staff Status, Staff Notes** |
| `Daily_Monitor` | `buildMonitorTab_` | (human view) | monitor blocks |
| `Daily_Report_Log`, `Daily_Summary`, `Callbacks_Archive` | morning report | trend | report rows |
| `Call_Feed` | `rebuildCallFeed` (~21:30) | Follow-Up Tracker (external), not the dashboard | Date, Time, Phone10, Direction, Agent, Duration_s, Status, Start_Unix |
| `Patient_Master` | nightly mirror (external `push_patient_mirror.py`) | dashboard `patientLookup_` | Mobile, Patient Name, Diagnosis, Age, Gender, Last Visit, Patient UID |
| `WA_Inbox` | webhook ingest (external) | dashboard `waLookup_` | Timestamp, Phone, Direction, Type, Message, Message ID, Conversation ID, Status |
| `Agents` | hand-maintained roster | dashboard key-gate + roster | Ext, Name, UserId, Active |

Column matching is **tolerant** — `findCol_` accepts many header spellings — so a renamed header rarely breaks reads, but a renamed **tab** does.

---

## 5. How "agents" and "callbacks" get populated (the dropdown sources)
- **Agent name per call** comes from the API record itself: `callAgentInfo_(r)` reads `r.log_details[].received_by[].name`. **Connected** calls have a receiver name; pure-missed calls may not. So the **Clinic Team** dropdown only shows agents who had **connected** calls today. A day with only missed calls → few/no agent rows (correct behaviour, not a bug).
- **Callbacks-needed** = `computeNetMissed_`: incoming calls with status==2 that had NO connected call (either direction) the same day.
- **Resolved** = a missed caller who later connected.
- **WhatsApp** = latest message per number from WA_Inbox + a recent feed.
- The dashboard reads **today only** (`dayBounds_(0)`, local Asia/Kolkata midnight→now). Early morning legitimately shows little.

---

## 6. Known facts established on 29 Jun 2026 (Session 16)
- `probeApi()` → token length 32 (3f…c7), **5 live records** returned, fields map correctly (e.g. number …3970, 96s, incoming, 09:27). **The API + token are HEALTHY.**
- `rebuildCallFeed` last trigger-run was 28 Jun 21:23 and hadn't re-run — but this only affects the **Call_Feed tab**, NOT the dashboard dropdowns.
- The dashboard `WebApp.gs` is multi-file and complete in the project (not the 2-file subset that was in the handoff kit). The kit's `dashboard/` folder is **missing** `config.gs, MyOperator.gs, Netting.gs, Sheets.gs, Main.gs, Monitor.gs, CallField.gs.gs, Probe.gs.gs` — only `WebApp.gs`+`Dashboard.html` were carried. **Action: commit all 11 files to GitHub.**
- Build label observed: `v17.1 · inbound` (so `WebApp.gs` server is current).
- Symptom under investigation: tiles populate, **all expandables empty, no error banner**. `getDashboardData` reportedly "finishes." Per §2 this localises to Path B after the API fetch — the next test (a read-only `getDashboardData` count probe) was not yet successfully run.

---

## 7. Golden rules (hard-won)
1. **Deploying does not run trigger code, and triggers don't power the dashboard.** Never "fix" empty dropdowns by redeploying or rolling back versions — the live data path doesn't depend on the deployment's age.
2. **Rolling back versions cannot fix a data problem.** If data is empty, the cause is upstream (API/roster/sheet/compute), not the HTML version.
3. **Always run `probeApi()` first** when calls look wrong — it isolates API+token in 5 seconds.
4. **The dashboard reads TODAY only, in IST.** "Empty early morning" can be normal.
5. **Functions ending in `_`** are private helpers; some can't be selected in the Run dropdown. Public test entry points: `probeApi`, `testIntradayNow`, `testCallFeedNow`, `testMonitorNow`, `testSummaryEmailNow`, `keyInfo`, `rebuildCallFeed`.
6. **One project, multiple files.** A function "missing" from the Run dropdown is usually because the wrong **file** is open or it's a `_`-private — not because it's deleted. Confirm with a project-wide search/export.
7. **Never paste tokens/keys into chat.** Probes read them from Script Properties and print only lengths.
8. **Apps Script deploy = edit existing deployment → New version** (keeps the URL). Never "New deployment."
9. **The handoff kit must carry all 11 Apps Script files**, or a future session is debugging half-blind (this cost hours in Session 16).

---

## 8. Quick command/function reference
| Need | Run this | In file |
|---|---|---|
| Confirm API + token live | `probeApi` | MyOperator.gs |
| See what the dashboard returns | `probeDashboardData_` (read-only, paste from troubleshooter) | Probe.gs.gs |
| Check the access keys exist | `keyInfo` | WebApp.gs |
| Rebuild today's callbacks + monitor now | `testIntradayNow` | Main.gs |
| Rebuild Call_Feed tab now | `testCallFeedNow` / `rebuildCallFeed` | CallField.gs.gs |
| Re-install ALL report triggers | `setupTriggers` | Main.gs |
| Re-install Call_Feed trigger | `installCallFeedTrigger` | CallField.gs.gs |
| Send one summary email now | `testSummaryEmailNow` | Monitor.gs |

*KB v1 · 29 Jun 2026 · built from full project export · supersedes scattered dashboard notes.*

---

## 12. Resolved incidents (see Troubleshoot Log for full detail)
Cross-reference: `Callback_Dashboard_TROUBLESHOOT_LOG.md`.

- **#1 · Empty dropdowns / good tiles (29 Jun 2026).** A `ReferenceError: i is not defined` thrown inside `Array.map` in the pending-callbacks renderer aborted the whole client render; tiles (drawn first) survived, all sections below stayed blank. Fix = add the missing `i` param: `p.map(function(e,i){`. Then a **separate** deployment step was needed — saving the HTML does not change what `/exec` serves; you must publish a **New version**. Both proven and live.
  - Diagnostic order that works: `probeApi` → `probeDashboardData_` (via plain-named wrapper) → F12 Console. If both probes pass, it's a browser render bug, not data/triggers/deploy.

