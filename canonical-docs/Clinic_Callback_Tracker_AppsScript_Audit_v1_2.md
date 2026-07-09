# CLINIC CALLBACK TRACKER — APPS SCRIPT PROJECT AUDIT — v1.2
**Dr. Manoj Agarwal Clinic · Bareilly · Sessions 128–129 · 09 July 2026**
**Passes 1 (structure) and 2 (data flow) COMPLETE. Pass 3 (correctness): `Dashboard.html` COMPLETE; the sixteen `catch (e) {}` NOT YET CLASSIFIED. Pass 4 (recommendations) NOT STARTED.**

> **Nothing in this audit was fixed.** No file was changed, no trigger touched, no tab written, no property set. An inventory is not a repair, and a live staff-facing system is not repaired mid-inventory. (**D180**)

---

## §0 — METHOD, AND WHAT IT CANNOT SEE

**Source, named by its bytes and not by its nickname (D188):**

| | |
|---|---|
| Export | Apps Script JSON, exported live by the owner, 09 Jul 2026 |
| Size | **465,195 bytes** |
| md5 | **`8bdb6d4dfdb0a331c5048b3c0fccf367`** |
| Files | **15** (`appsscript` + 13 `.gs` + `Dashboard`) |
| `Dashboard.html` | **2,738 lines · 157,611 bytes · md5 `034529a124c6bfab8aec2b675620dfec`** |

**v1.1 read a different file, and did not know it.** `Clinic_Callback_Tracker_AppsScript_S124.json` in project knowledge carries `PAGE_BUILD = 'v18.18 · S57'` and contains **no `Health.gs`**. It is a **pre-S124** export named for a session it predates. Reading it at S129 open, the assistant measured `Dashboard.html` at 2,676 lines and declared five canonical documents defective. **The documents were right.** The `Dashboard.html` md5 above is the same one already recorded in KB changelog **v1.48** for the v18.19 fix. → **D188. A filename is not provenance. Every document naming an export must carry its md5 and file count.**

Twelve `.gs` files are byte-identical across both exports. Only `Dashboard` differs; only `Health.gs` is new. **Every v1.1 finding on the `.gs` files therefore stands**, except where re-derived below.

**Checks that failed and were rebuilt.** v1.1 recorded three. v1.2 records a fourth, of the same kind: a regex intended to extract the page's server calls returned `withSuccessHandler` and yielded *"zero server functions called"* — while line 1442 plainly calls `getFollowups`. **This is the identical failure v1.1's §0 already documents, reproduced by the same author on the same file.** It was rebuilt as a chain-walker with an assertion that fails if `getFollowups` is absent, and only then used.

**What this audit CANNOT see, and must not pretend to:**
- **Which triggers are actually armed.** Triggers are project settings, not code; absent from the export. `sendFollowupSummary` and `rebuildCallFeed` may or may not be scheduled. **`UNKNOWN`.** One screenshot closes it.
- **Script Properties.** `DASH_KEY`, `STAFF_KEY`, `AKEY_<ext>`, `MYOP_TOKEN`, `SHEET_ID`, `NTFY_TOPIC_URL`, `SUMMARY_EMAIL` are referenced in code; their presence and values are **`UNKNOWN`** and must stay that way (**D169**).
- **Whether the GitHub repo is public.** F-9's bound depends on the ungated function names not being published. **`UNKNOWN`.** Must be confirmed.
- **The project's daily Apps Script execution budget.** Edition-specific. **`UNKNOWN`.** Nothing measures consumption against it.
- **`call.initiated` webhook bodies.** Never captured on this account. Relevant to any future ring-time feature.

---

## §1 — INVENTORY

**13 server files · 4,640 lines · plus `Dashboard.html`, 2,738 lines · 55 global functions.**

| File | Lines | Role |
|---|---|---|
| `config` | 82 | `CFG` — tunables, tab names, endpoints, email schedule. No secrets (correct). |
| `MyOperator` | 177 | Search Logs API client. `fetchCallsBetween_`, `probeApi`. |
| `Netting` | 184 | Missed-call netting, `computeNetMissed_`. |
| `Sheets` | 131 | Writes the four digest tabs. |
| `Main` | 99 | Trigger entrypoints: intraday, summary, morning, `setupTriggers`, **`removeTriggers`**. |
| `Monitor` | 324 | `Daily_Monitor` tab + the 11/15/19 summary email. |
| `CallField.gs` | 105 | `rebuildCallFeed()` → `Call_Feed`, nightly 21:30. |
| `WebApp` | 1,652 | `doGet`, dashboard data, follow-ups, outcomes, escalations, WA thread, **the two key setters**. **Never modified (D34).** |
| `Dashboard.html` | 2,738 | The entire UI. **Canonical is the live Apps Script project, not GitHub (D160).** |
| `Probe.gs` | 164 | Ad-hoc probes. Dev scaffolding. Sole user of the `documents` scope. |
| `Callconsole` | 675 | Dashboard-as-dialer: agent identity, durations, recordings. |
| `OutcomeLog` | 493 | Doctor review of outcomes; transcripts. |
| `Diagnostics` | 153 | S53 stale-list sentinel. Alerts only on failure. |
| `Health` | 401 | Daily heartbeat. Alerts every day, green or not. |

*(v1.1 reported 12 files / 4,231 lines and listed `Health` at 401 without counting it. 4,231 was the sum of `count('\n')` across the twelve non-`Health` files — correct under that convention, and stated without it. Line counts above are true line counts.)*

**Namespace is clean.** Zero duplicate function definitions. After 129 sessions of accretion, that is a real achievement and should be said.

**Reachability.** 55 globals. **24 are called by the page. 31 are not. 27 have no key check at all.**

---

## §2 — THE DATA-FLOW MAP

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

`Call_Feed` → published as CSV → the clinic-PC tracker reads it via `data\feed_url.txt`. **The project's only outbound edge, and it is a published-to-web CSV.** See F-0.

### The gap this map did not show

**Incoming calls have no inbound pipeline at all.** The VPS receives `call.end` and `call.summary` for every incoming call and **discards them** — the receiver writes only `category == "obd"` with a `client_ref_id` (**D178**). On 09-Jul: **66 webhooks accepted → 29 rows written.** Thirty-seven real calls raw-logged and dropped. → **D181.**

---

## §3 — FINDINGS

### 🔴 F-8 — the incoming "Log outcome" button is dead for every patient in `Patient_Master` *(new, S129)*

`Dashboard.html` **L912** builds the patient packet with `JSON.stringify` — which always emits `"` — and passes it through **`jsq()`**, which escapes `\` and `'` and **not** `"`. **L923** pastes the result into an `onclick` attribute delimited by `"`. The first quote inside the packet closes the attribute early.

Established by emitting the exact HTML and parsing it as a browser must:

| Row | `onclick` the browser compiles | Result |
|---|---|---|
| number **not** in `Patient_Master` | `inOpen('in_98…_0','9812345678',false,'{}')` | ✅ works |
| number **in** `Patient_Master` | `inOpen('in_98…_0','9812345678',true,'{` | ❌ **syntax error — handler never installs** |

The button renders and looks correct. Clicking does nothing, silently. **`inOpen()` is the only route to the incoming-outcome form; `saveIncomingOutcome` is invoked from nowhere else.** The breaking condition is `e.patient` being truthy — the number is in `Patient_Master` — not the `known` flag, so a patient row with only a UID also breaks.

**This collides with D153.** D153 records, from 40 incoming calls returning *"No claim logged"*, that *"staff never file outcomes for incoming calls — workflow finding, not a gap."* **That population is exactly the one whose button is dead.** A rendering defect may have been recorded as a staff habit and then used to justify the Stage-3 claim-match join.

**Not asserted.** Falsifiable in ten seconds on the live dashboard, and **the evidence expires the moment F-8 is fixed.** Until then **D153 is `UNKNOWN`.**

**Price:** 1 line, `Dashboard.html`. No server file. Staff path disturbed — it starts working. Rollback = redeploy.

### 🔴 F-9 — F-1 corrected: twenty-seven ungated globals, two of which hand out the doctor's key *(supersedes F-1)*

**v1.1's F-1 said seven, verified that none of the seven returns patient data, and concluded *"unauthenticated write, send, and quota-burn — not exfiltration."* Both halves are true of those seven. The conclusion was published over twenty-seven.** → **D186.**

Manifest, confirmed from the live export: `access: ANYONE_ANONYMOUS`, `executeAs: USER_DEPLOYING`.
**In Apps Script, every top-level function whose name does not end in `_` is callable by any browser that has loaded the page** — not only the ones the page calls. This is the fact F-1 missed.

**The twenty-seven ungated:**

`setDashboardKey` · `setStaffKey` · `keyInfo` · `sendFollowupSummary` *(WebApp)*
`setupTriggers` · `removeTriggers` · `runIntradayDigest` · `runSummaryEmail` · `runMorningReport` · `testIntradayNow` · `testMorningNow` *(Main)*
`installCallFeedTrigger` · `testCallFeedNow` · `rebuildCallFeed` *(CallField)*
`dailyHealthReport` · `installHealthTrigger` · `removeHealthTrigger` · `testHealthReportNow` *(Health)*
`checkFollowupListFresh` · `testSentinelAlert` *(Diagnostics)*
`testMonitorNow` · `testSummaryEmailNow` *(Monitor)*
`probeApi` *(MyOperator)* · `RUN_DASH_PROBE` · `probeRecordingField` · `probeRecordingPlayback` *(Probe)*
`OL_SELFTEST` *(OutcomeLog)*

**Four of them matter:**

- **`setDashboardKey(k)`** (`WebApp.gs` L48) — writes the `DASH_KEY` script property. No key, no role check.
- **`setStaffKey(k)`** (`WebApp.gs` L52) — same, for `STAFF_KEY`.
- **`removeTriggers()`** (`Main.gs` L97) — deletes **every** trigger in the project.
- **`removeHealthTrigger()`** (`Health.gs` L393) — deletes the 09:00 heartbeat specifically.

**Consequence.** A holder of the `/exec` URL, with **no `?k=` at all**, sets `DASH_KEY` to a value of their choosing, reloads with it, and is graded `full` by `dashRole_`. `full` reaches `getOutcomeLog`, `getTranscriptText`, `getFollowups` — **names, Clinic IDs, diagnoses, transcripts.** The owner's own key stops matching in the same call: **takeover and lockout together.**

**Two things soften it, and both belong in the record.**

1. **Server-side role enforcement is real and correct.** Every doctor-only function opens with `dashRole_(key) !== 'full'`. Client-side hiding of the escalations / review sections is defence-in-depth, not the gate. **A staff member holding a valid `AKEY_<ext>` genuinely cannot read the doctor's console.** The role model is sound; the setters are the single hole in it.
2. **`removeTriggers` would be caught.** `Health.gs` alerts by silence, so a disarmed heartbeat surfaces the next morning. The instrument built in S128 covers the attack on itself.

**The realistic actor is not a stranger.** It is the `/exec` URL — held by six staff, resident in browser history, **unrevocable without a redeploy that changes it everywhere.** The function names are absent from the served page but present in the GitHub repo. **Whether that repo is public is `UNKNOWN` and must be confirmed before this bound may be relied upon.**

**And a collision.** Both setters live in `WebApp.gs`. **D34 forbids touching it.** The rule written to protect a fragile file now stands in front of the only real privilege escalation in the project. → **D187: blast-radius assessed first, changed last, and NOT closed to session-start review.**

**Price:** `removeTriggers` / `removeHealthTrigger` — rename to a trailing `_`, 2 lines, 2 files, no D34 waiver, no staff path. The setters — 2 lines, but they need a named D34 suspension and a rollback.

### 🟠 F-10 — two escapers, each blind where the other sees *(new, S129)*

`esc()` (L685) neutralises `& < > "` and **not** `'`. `jsq()` (L729) neutralises `\` and `'` and **not** `"`.

Twelve sites put `jsq()` output inside a **double**-quoted attribute. Twelve put `esc()` output inside a **single**-quoted one. Each held **only because the data happened never to exercise the other's blind spot** — phone digits, hex recording refs, row IDs, `escaped` row keys.

**L923 was the first field guaranteed to contain a `"`.** F-8 is not a typo; **it is the first field that tested the gap.** Same shape as F-3, which is safe by accident of layout: this is safe by accident of data. Remaining sites are fed by patient names, diagnoses, agent names, transcript file IDs — a patient named `D'Souza` reaches `esc()` inside a single-quoted attribute.

**The structural cure is not a better escaper.** Stop embedding data in markup: the button carries a row ID; the details stay in a JS object and are looked up on click. **Twenty-four fragile sites become none.**

**Price:** medium, one file, staff paths used hourly. Own commit. Approved by owner *if workflow is not compromised*.

### 🟠 F-11 — the key is stored in cleartext and there is no sign-out *(new, S129)*

`applyAccess()` (L2708) writes the key to `localStorage` as `clinicDashKey`. **Zero occurrences of a logout, a clear, or a `removeItem` in 2,738 lines.** The reception tablet holds a working key permanently, readable by any browser extension. No idle timeout. `?k=` in the URL (read at L2731) puts the key into browser history, autocomplete, and any screenshot of the address bar.

The existing control — `Active=no` on the roster row, making `dashRole_` return `none` — **is real and is the right one.** But it invalidates the **person**, never the **key**, and nothing prompts the edit.

**Price:** client-side only. Sign-out button; strip `?k=` after reading; optional expiry. No server file. Rollback = redeploy. **Cheapest item on this list with a real security return.**

### 🟡 F-12 — ~9 server calls per minute per open tab, over F-6's whole-tab reads *(new, S129)*

`REFRESH_SECONDS = 60` (L634). Each cycle: `getDashboardData`, `getFollowups`, `getFollowupLastVisits`, `getFollowupRecordings`, `getFollowupClinicIds`, `getAllCallsToday`, `getFollowupFreshness` — plus `getEscalations` and `getOutcomeLog` on the doctor's key.

**This is the client-side multiplier on F-6.** Sharpest instance: while a call is placed the tile polls `getCallDuration` **every 6 s for up to 3 min** (`FU_POLL_EVERY_MS = 6000`, `FU_POLL_TIMEOUT_MS = 180000`), and `getCallDuration` re-reads the **entire** `Call_Durations` tab each time. **One three-minute call re-reads that whole tab thirty times.**

Nothing is broken today. It degrades in proportion to accumulated history, and it degrades as *"the dashboard is slow"* and *"Reconnecting…"* — which look like the clinic's internet and are not. **The daily execution budget is `UNKNOWN` and nothing watches it.** `Health.gs` reports on tabs and freshness, not headroom. The first symptom of exhaustion arrives mid-clinic, with no warning — exactly the shape of problem `Health.gs` exists to abolish.

**Remedies, ascending disruption:** longer refresh · bundle the five follow-up calls · read last-*N* rows · pause polling on hidden tabs · **`CacheService` on the payload (six agents → one sheet read; largest saving, least change)** · quota headroom in `Health.gs`. **Escalation, if insufficient:** move the *read* path to the VPS (service account + `gspread` exist) — **a trade, not a win.** Beyond that, off Apps Script entirely — large, not recommended. → **D185: Block C precedes Block D.**

### 🟡 F-13 — the UTC-date bug D156 fixed still survives sixty lines away *(new, S129)*

`fuDayKey()` (L1603) was rewritten in S124 to use the **local** date, precisely because a UTC day key stranded call state. **L1800 still calls `new Date().toISOString().slice(0,10)`** — UTC — to stamp the follow-up progress line. Display-only; the clinic is shut 00:00–05:30 IST. **But it is the same bug, in the same file, left behind by the commit that fixed its twin.**

**And "local" is not "IST."** Three clocks: `Session.getScriptTimeZone()` (IST, 15× in `WebApp.gs`) · `CC_TZ` (18×, `Callconsole` + `OutcomeLog` — **F-5**) · the browser's device clock. **A tablet with a wrong time zone can corrupt follow-up state.** Cure: the server sends `todayIST`; the client computes no dates. **Closes F-5 and F-13 together.**

### ⚪ F-14 — three of seventeen client-side silent catches are wrong *(new, S129)*

Swallowing a `localStorage` write, a `.focus()`, a `revokeObjectURL` is right — fourteen are. **L1260** and **L1364** swallow a `JSON.parse` of the patient packet, so a malformed packet silently becomes an empty outcome payload. **L1128** swallows `openThread`.

**L1260 parses the very packet F-8 corrupts. The catch that would have reported F-8 is the catch that hid it.**

### ⚪ F-15 — the `documents` OAuth scope is held for one dev file *(new, S129)*

`DocumentApp` appears **exactly once** in the project: `Probe.gs`. The scope is granted to the whole deployment. Deleting `Probe.gs` removes three ungated globals (F-9) and this scope together. Sibling of **F-7**.

---

### 🟠 F-0 — `Call_Feed` is published to the web. Confirmed, deliberate, and mis-described. *(unchanged from v1.1)*

Confirmed by the owner, 09-Jul, from the sheet's own dialog: published, *auto-republish* on, **`Call_Feed` only** — `Entire document` is **not** published. This is the documented, intentional mechanism by which the clinic-PC tracker pulls its feed.

**A UI trap worth naming.** The dialog's first line reads *"This document is not published to the web"* **while `Call_Feed` is published.** That line describes the selector above it, not the state below it.

**What is public**, to anyone holding the URL, with no Google account: `Date · Time · Phone10 · Direction · Agent · Duration_s · Status · Start_Unix` — **3,019 rows.** ~3,000 patient mobiles, each paired with the date they called an orthopaedic surgeon and the staff member who handled it, plus all six agent names. Refreshed automatically.

**`CallField.gs` line 8 reads *"…so PHI never leaves the clinic."*** The first clause (no names, no diagnosis) is true. **The conclusion is not.** A mobile number is an identifier; under the DPDP Act it is personal data, and its association with a healthcare provider is what makes it sensitive.

**Severity: bounded. An accepted risk, not an incident** — accepted knowingly, with the bound written down, rather than inherited from a docstring that overstates its own safety. **Do not disable it.** The clinic-PC tracker depends on it.

### 🟠 F-3 — `Followup_Outcomes` has three writers, and the code says it has one *(unchanged)*

Writers: `WebApp.saveFollowupOutcome` (append) · `WebApp.saveIncomingOutcome` (append) · `OutcomeLog.reviewOutcome` (cell writes) · `OutcomeLog.OL_ensureReviewCols_` (header). `WebApp.gs` L1152 comments *"one-writer tab."*

Mitigating: writes are **column-disjoint**, appends do not shift row indices, nothing deletes rows, and `reviewOutcome` carries an `fp` fingerprint guard. **Very probably safe today — safe by accident of layout, not by design.** One `deleteRow` anywhere, ever, and the review columns write to the wrong patient.

### 🟠 F-4 — a dead ledger with a public writer *(unchanged)*

`Callconsole.logOutcome(key, payload)` is **called by nothing.** Its tab `Outcomes_Log` has never been created (confirmed independently: `Health.gs`'s tab census does not see it). It remains browser-reachable and **gated** (`dashRole_ !== 'none'`), and it appends `patientName` and `clinicId` — **PHI** — to a tab nobody reads.

### 🔴 F-2 — sixteen `catch (e) {}` that swallow the error entirely *(unchanged — STILL UNCLASSIFIED)*

`WebApp` ×5 (L973, 1314, 1396, 1397, 1398) · `Callconsole` ×4 (L498, 539, 566, 580) · `OutcomeLog` ×3 (L117, 148, 302) · `Diagnostics` ×3 (L114, 128, 143) · `Probe` ×1.

**The project's own named failure mode**, in the staff-facing path. Three are in `Diagnostics.gs`, whose docstring says *"a silent guard is worse than none."*

A swallowed **best-effort ntfy push** is correct. A swallowed **outcome write** is not. **Each of the sixteen needs classifying individually. They must never be fixed by one commit (D180).** **This is the outstanding item of pass 3.** F-14 shows what one unexamined silent catch cost on the client side; there is no reason to expect the server side to be cheaper.

### 🟡 F-5 — two sources of truth for time *(folded into F-13)*
### 🟡 F-6 — fifteen full-tab `getDataRange().getValues()` reads *(multiplier quantified in F-12)*
### ⚪ F-7 — dev scaffolding in production *(scope cost quantified in F-15)*

---

## §4 — OPEN, AND HONESTLY UNKNOWN

1. **Which triggers are armed.** Not in the export. One screenshot closes it. `Call_Feed`'s `lag=1d` is *consistent with* a live 21:30 trigger — **not proof of one.**
2. **Is the GitHub repo public?** F-9's bound depends on it.
3. **What is the daily Apps Script execution budget?** F-12 depends on it. Nothing measures against it.
4. **Is D153 a workflow fact or F-8?** One click. **The evidence expires when F-8 is fixed.**
5. **Does `call.initiated` fire for incoming calls, and does it carry the caller's number?** Never captured on this account. Blocks any ring-time feature.
6. ~~The published `Call_Feed` CSV.~~ **RESOLVED — F-0.**
7. ~~`Dashboard.html` unaudited.~~ **RESOLVED S129 — F-8 … F-15.**
8. **`OutboundLog.gs`** described as superseded and deletable. **Not in the export.** Already removed. Closed.
9. **D158's join defect** (`verdict_review.py`) lives outside this project. Out of scope here — **but if F-8 confirms, the incoming half of its input was never fileable.**

---

## §5 — WHAT PASS 4 WILL DO

Rank each finding by **blast radius**, not by severity-word. Price each fix in: lines changed, files touched, whether a live staff-facing path is disturbed, and whether it can be rolled back without a redeploy.

**Sequencing already set by the owner (S129):**
**Block A** — F-8 (after the evidence click), F-14, F-11, the two trigger-killers, F-2's classification, the triggers screenshot, the repo-visibility check.
**Block B** — F-9's key setters. **Blast radius assessed first; changed last; requires a named D34 suspension (D187). Parked for ordering, not for safety — do not silence it.**
**Block C** — F-13/F-5 (one clock), F-6/F-12 (bounded reads, bundled calls, `CacheService`, quota headroom). **Must not disrupt staff flow. Precedes Block D (D185).**
**Block D** — the incoming-call console (D181–D184).
**Block E** — F-15/F-7 (`Probe.gs` deleted), F-10 (stop embedding data in markup).

**F-0 has exactly one alternative, and it is a trade, not a win.** Replace the public URL with an authenticated read via the existing service account. **The cost is a service-account key file on a Windows clinic PC**, whose rotation is already an open Tier-A1 item. Swapping an unguessable URL for a private key on a shared desktop is not obviously safer. **It is a decision, not a fix.**

**Nothing above is fixed until a decision sheet is approved for it.** F-8, F-9, F-4 and F-10 touch a live web app used by staff during clinic hours. **F-2 must be split.**

---

**END OF AUDIT v1.2 — §5 is the last section. If §5 is absent, this file is truncated.**
