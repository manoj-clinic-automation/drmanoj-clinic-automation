# CLINIC CALLBACK TRACKER — APPS SCRIPT PROJECT AUDIT — v1.1
**Dr. Manoj Agarwal Clinic · Bareilly · Session 128 · 09 July 2026**
**Passes 1 (structure) and 2 (data flow) COMPLETE. Pass 3 (correctness) PRELIMINARY. Pass 4 (recommendations) NOT STARTED.**

> **Nothing in this audit was fixed.** No file was changed, no trigger touched, no tab written. An inventory is not a repair, and a live staff-facing system is not repaired mid-inventory.

---

## §0 — METHOD, AND WHAT IT CANNOT SEE

Source: the project's own JSON export, read from disk. Every claim below was derived by parsing that export. **Where a check failed, it is recorded as failed, not as clean** (D166, D172).

**Three checks of mine failed during this audit and were rebuilt:**
1. A regex for browser-callable functions returned `withSuccessHandler` — a handler, not a function. Rebuilt.
2. A second attempt returned `forEach` and `getElementById` — DOM calls. Rebuilt on the correct model: *in Apps Script, every global function not ending in `_` is browser-reachable, whether or not the HTML calls it.*
3. A one-writer-per-table check captured variable names (`CFG`, `name`) instead of tab names. Rebuilt with a constant-resolution table and handle binding.

**What this audit CANNOT see, and must not pretend to:**
- **Which triggers are actually armed.** Triggers are project settings, not code. They are absent from the export. `sendFollowupSummary` and `rebuildCallFeed` may or may not be scheduled. **UNKNOWN.** One screenshot of Apps Script → Triggers closes this.
- **Script Properties.** `DASH_KEY`, `STAFF_KEY`, `MYOP_TOKEN`, `SHEET_ID`, `NTFY_TOPIC_URL`, `SUMMARY_EMAIL` are referenced in code; their presence and values are **UNKNOWN** and must stay that way (D169).
- **`Dashboard.html` (2,738 lines) has not yet been audited.** Client-side logic, key handling in the browser, and the staff UI are Pass 3 work.

---

## §1 — INVENTORY

**12 server files · 4,231 lines · plus `Dashboard.html`, 2,738 lines · 51 global functions.**

| File | Lines | Role |
|---|---|---|
| `config` | 81 | `CFG` — tunables, tab names, endpoints, email schedule. No secrets (correct). |
| `MyOperator` | 176 | Search Logs API client. `fetchCallsBetween_`, `probeApi`. |
| `Netting` | 184 | Missed-call netting, `computeNetMissed_`. |
| `Sheets` | 131 | Writes the four digest tabs. |
| `Main` | 98 | Trigger entrypoints: intraday, summary, morning, `setupTriggers`. |
| `Monitor` | 324 | `Daily_Monitor` tab + the 11/15/19 summary email. |
| `CallField` | 105 | `rebuildCallFeed()` → `Call_Feed`, nightly 21:30. |
| `WebApp` | 1,651 | `doGet`, dashboard data, follow-ups, outcomes, escalations, WA thread. **Never modified (D34).** |
| `Dashboard.html` | 2,738 | The entire UI. **Canonical is the live Apps Script project, not GitHub (D160).** |
| `Probe.gs` | 163 | Ad-hoc probes. Dev scaffolding. |
| `Callconsole` | 674 | Dashboard-as-dialer: agent identity, durations, recordings. |
| `OutcomeLog` | 492 | Doctor review of outcomes; transcripts. |
| `Diagnostics` | 152 | S53 stale-list sentinel. Alerts only on failure. |
| `Health` *(added S128)* | 401 | Daily heartbeat. Alerts every day, green or not. |

**Namespace is clean.** Zero duplicate function definitions across 4,231 lines. After 128 sessions of accretion, that is a real achievement and should be said.

---

## §2 — THE DATA-FLOW MAP

This did not exist. It does now.

### Pipelines IN (nothing in this project writes these)

| Tab | Written by | Cadence |
|---|---|---|
| `Followups_Today` | `push_followups_today.py`, clinic PC | each morning |
| `Call_Durations` | `call_hook_capture.py`, VPS receiver | real time — **console-dialled (OBD) calls only** |
| `Call_Recordings` | Stage 1, VPS | ~02:00, archives *yesterday* |
| `Call_Transcripts` | Stage 2, VPS | ~03:00, archives *yesterday* |
| `Patient_Master` | clinic PC | periodic |
| `Agents` | hand-maintained | rarely |

### Tabs owned by this project

| Tab | Writer(s) — in project | Readers |
|---|---|---|
| `Call_Feed` | `CallField.writeCallFeed_` | `CallField`; **the clinic-PC tracker, via published CSV** |
| `Callbacks_Today` | `Sheets.upsertCallbacksToday_` | `Sheets`, `WebApp` |
| `Callbacks_Archive` | `Sheets.archiveAndResetCallbacks_` | `Sheets` |
| `Daily_Report_Log` | `Sheets.writeDailyReport_` | `Sheets` |
| `Daily_Summary` | `Monitor` | `Monitor`, `Sheets` |
| `Daily_Monitor` | `Monitor.buildMonitorTab_` | — (human only) |
| `Followup_Outcomes` | **THREE writers — see F-3** | `OutcomeLog`, `WebApp` ×4 |
| `Followup_Escalations` | `WebApp.resolveEscalation`, `WebApp.sendBackToStaff` | `WebApp` |
| `Outcomes_Log` | `Callconsole.logOutcome` — **never called; tab does not exist** | none |

### Pipeline OUT

`Call_Feed` → published as CSV → the clinic-PC tracker reads it via `data\feed_url.txt`. **This is the project's only outbound edge, and it is a published-to-web CSV.** Its access model was not examined in this pass.

---

## §3 — FINDINGS (preliminary; Pass 3 incomplete)

### 🟠 F-0 — `Call_Feed` is published to the web. Confirmed, deliberate, and mis-described.

**Confirmed by the owner, 09-Jul, from the sheet's own dialog.** `Call_Feed` is published, with *Automatically republish when changes are made* ticked. `Entire document` is **not** published — only this one tab. This is the documented, intentional mechanism by which the clinic-PC tracker pulls its feed (`CallField.gs` header; `data\feed_url.txt`).

**A UI trap worth naming.** The dialog's first line reads *"This document is not published to the web"* **while `Call_Feed` is published.** That line describes the selector above it, not the state below it. Anyone verifying this in thirty seconds reads line one and closes the box reassured. Same shape as every other fault in this project: *a confident statement that is not about the thing it appears to be about.*

**What is public**, to anyone holding the URL, with no Google account and no password:

`Date · Time · Phone10 · Direction · Agent · Duration_s · Status · Start_Unix` — **3,019 rows.**

~3,000 patient mobile numbers, each paired with the date they called an orthopaedic surgeon and the staff member who handled it, plus all six agent names. Refreshed automatically.

**`CallField.gs` line 8 reads: *"No patient names, no diagnosis — just phone + agent + status. The tracker joins this to patient identity LOCALLY, so PHI never leaves the clinic."*** The first clause is true. **The conclusion is not.** A mobile number is an identifier. The design correctly stripped names and diagnosis, then described the residue more generously than it earned. Under India's DPDP Act a mobile number is personal data, and its association with a healthcare provider is what makes it sensitive.

**Severity: bounded.** One tab. No names, no diagnoses, no Clinic IDs. The URL is unguessable and unindexed unless linked. **An accepted risk, not an incident** — but accepted knowingly, with the bound written down, rather than inherited from a docstring that overstates its own safety.

**Do not disable it.** The clinic-PC tracker depends on it. Withdrawing it mid-clinic-day breaks the outbound pipeline. Any change here is a Pass 4 decision sheet with a real trade-off (see §5).

### 🔴 F-1 — `doGet` serves the dashboard to anyone. No key.

```javascript
function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('Dashboard')...
}
```

The manifest is `access: ANYONE_ANONYMOUS`, `executeAs: USER_DEPLOYING`. Authorisation happens **inside each server function**, never at the door. Seven globals have no check:

`sendFollowupSummary` · `probeApi` · `probeRecordingField` · `probeRecordingPlayback` · `testIntradayNow` · `testMonitorNow` · `testMorningNow`

Anyone holding the `/exec` URL — **with no `?k=` at all** — loads the page, receives the `google.script.run` bridge, and can invoke those seven **executing as the deploying account**.

**Verified: none of the seven returns patient data.** They log, they email a fixed address, they rebuild tabs, they consume MyOperator API quota. So this is **unauthenticated write, send, and quota-burn — not exfiltration.** Same class as the call-hook key exposure: data-integrity and nuisance.

**But the URL is not a credential.** It sits in browser history, in Apple Notes, in whatever share once carried it. The whole purpose of `?k=` is that the URL alone should not be enough. For these seven, it is.

### 🔴 F-2 — Sixteen `catch (e) {}` blocks that swallow the error entirely

`WebApp` ×5 (L973, 1314, 1396, 1397, 1398) · `Callconsole` ×4 (L498, 539, 566, 580) · `OutcomeLog` ×3 (L117, 148, 302) · `Diagnostics` ×3 (L114, 128, 143) · `Probe` ×1.

**This is the project's own named failure mode**, in the staff-facing path. *A gate that refuses silently is indistinguishable from a world that never called.* Three of them are in `Diagnostics.gs` — the file whose docstring says *"a silent guard is worse than none."*

Not every one is a defect: a swallowed failure on a *best-effort* ntfy push is correct. A swallowed failure on an outcome write is not. **Each of the sixteen needs classifying individually.** That is Pass 3 work and it has not been done.

### 🟠 F-3 — `Followup_Outcomes` has three writers, and the code says it has one

```javascript
// 1) always log the outcome (one-writer tab)      <- WebApp.gs L1152
var shO = fuEnsureTab_(ss, FU_TAB_OUTCOMES, FU_OUTCOME_HEADERS);
shO.appendRow([...]);
```

Writers: `WebApp.saveFollowupOutcome` (append) · `WebApp.saveIncomingOutcome` (append) · `OutcomeLog.reviewOutcome` (cell writes) · `OutcomeLog.OL_ensureReviewCols_` (header).

**The invariant is stated in a comment and not held in the code.**

Mitigating, and it matters: the writes are **column-disjoint** — WebApp owns rows, OutcomeLog owns the three review columns — and `reviewOutcome` carries an `fp` fingerprint guard against row drift. Appends do not shift existing row indices, and nothing deletes rows. **So this is very probably safe today.** It is safe by *accident of layout*, not by design, and nothing in the code says so. One `deleteRow` anywhere, ever, and the review columns write to the wrong patient.

### 🟠 F-4 — A dead ledger with a public writer

`Callconsole.logOutcome(key, payload)` is **called by nothing** — not by `Dashboard.html`, not by any `.gs`. Its own comment concedes: *"Outcomes_Log will be created on first logOutcome() call."* It never is. **The tab does not exist.** (Confirmed independently: `Health.gs`'s tab census does not see it.)

It remains browser-reachable and gated. It appends `patientName` and `clinicId` — **PHI** — to a tab nobody reads. A superseded design that lost to `Followup_Outcomes` and was never removed.

### 🟡 F-5 — Two sources of truth for time

`WebApp` uses `Session.getScriptTimeZone()` (15×). `OutcomeLog` (12×) and `Callconsole` (6×) use `CC_TZ`. Values are almost certainly identical today. **Latent, not active.** It becomes a defect the moment one is changed.

### 🟡 F-6 — Fifteen full-tab `getDataRange().getValues()` reads

Including `Call_Feed` at 3,019 rows, on paths the dashboard hits every refresh. Performance and quota, not correctness. Grows monotonically with the archive.

### ⚪ F-7 — Dev scaffolding in a production project

`Probe.gs` (163 lines), `RUN_DASH_PROBE`, `dumpAllProjectFiles_`, `keyInfo` ("TEMP diagnostic"). Harmless individually. Collectively they are three of the seven ungated globals in F-1.

---

## §4 — OPEN, AND HONESTLY UNKNOWN

1. **Which triggers are armed.** Not in the export. Needed to know whether `sendFollowupSummary` and `rebuildCallFeed` actually run. `Call_Feed`'s freshness (`lag=1d`, 09-Jul) is *consistent with* a live 21:30 trigger — it is not proof of one.
2. **`Dashboard.html` — 2,738 lines, unaudited.** Where the key lives client-side, how it is passed, what the staff UI can reach.
3. ~~The published `Call_Feed` CSV.~~ **RESOLVED 09-Jul — see F-0.** Confirmed published, `Call_Feed` only, auto-republish on. Deliberate. Bound stated.
4. **`OutboundLog.gs`** is described as superseded and deletable. It is **not in the export.** Already removed. Closed.
5. **D158's join defect** (`verdict_review.py`) lives outside this project. Out of scope here.

---

## §5 — WHAT PASS 4 WILL DO

Rank each finding by **blast radius**, not by severity-word. Price each fix in: lines changed, files touched, whether a live staff-facing path is disturbed, and whether it can be rolled back without a redeploy.

**F-0 has exactly one alternative, and it is a trade, not a win.** Replace the public URL with an authenticated read: the clinic-PC tracker pulls `Call_Feed` through the existing service account (`patient-mirror@...`), as the VPS receiver already does to write this sheet. That removes the public URL entirely. **The cost is a service-account key file on a Windows clinic PC** — and service-account key rotation is already an open Tier-A1 item requiring Lokesh. Swapping an unguessable URL for a private key on a shared desktop is not obviously safer. **It is a decision, not a fix.**

**Nothing above is fixed until a decision sheet is approved for it.** Two of the findings (F-1, F-4) touch a live web app used by staff during clinic hours. F-2 touches sixteen sites across five files and must be split — a swallowed ntfy error and a swallowed outcome-write error are not the same finding.

---

**END OF AUDIT v1.1 — §5 is the last section. If §5 is absent, this file is truncated.**
