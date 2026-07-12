# FRONTEND / DASHBOARD DOCUMENTATION — v4
**Dr. Manoj Agarwal Clinic · Callback Tracker · Session 140 · 12 July 2026**
**(v4 = v3 verbatim + §V4 covering v18.28→v18.28f; the v2 body below describes v18.21 and remains correct except where §V3/§V4 supersede it.)**
**Source of every claim below: Apps Script export md5 `8bd1aeaa19459286566ce20abe72e4a2` (post-S134 deploy), 15 files.
Where a line number is cited it is from `Dashboard.html` (2,753 lines, md5 `5ff68c3d66a8b8d85eb31b70399a13c1`, `PAGE_BUILD v18.21 · S134`) unless another file is named.**
**Nothing here is inferred from memory. What is not in the export is marked `UNKNOWN` or `NOT IN CODE`.**
**Supersedes v1 (S130, pre-Fix-B). Every v1 line number was re-derived against the current file; none was carried blindly (D172). v1's `dataset.pat`, four-arg `inOpen`, and packet-in-markup descriptions are GONE from the page and appear below only as history.**

---

## 0. THE ONE-PARAGRAPH TRUTH

The dashboard is a **single Apps Script web app** served at one `/exec` URL. It has **one HTML file**
(`Dashboard.html`) that renders **several sections on one scrolling page** — there is no multi-tab
navigation. The header now carries **two buttons**: **↻ Refresh** and **Sign out** (S134); the login
card supplies the third interaction. Everything else is a section that appears or hides based on the
data. The page talks to the server through **24 functions** via `google.script.run` (§7, count
re-verified against this export). It reads from **two separate Google Spreadsheets** and **one Drive
folder**.

**The single most important structural fact (unchanged since v1, still true post-Fix-B):**
> **Filing an outcome and clearing a tile are two unrelated mechanisms for INCOMING tiles.** A tile
> leaves the pending list when the **`Staff Status` column of `Callbacks_Today`** is set to a "done"
> word — and **nothing in all fifteen files writes that column** (verified S131: every
> `setValue`/`setValues` searched; `Sheets.gs` preserves it, `STAFF_COL_COUNT: 2`). Only a human typing
> in the sheet has ever cleared an incoming tile. The **outcome card writes to a different tab
> (`Followup_Outcomes`) and never touches `Staff Status`.** Follow-up tiles behave the opposite way:
> logging the outcome IS what removes them. The asymmetry stands; Block D owns unifying it.

---

## 1. THE TWO SPREADSHEETS + ONE DRIVE FOLDER

The system is NOT one sheet. It is two, addressed by two different Script Properties, plus Drive.

### Spreadsheet A — the operational tracker · property `SHEET_ID`
ID `1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0` (also hard-coded as `CC_SHEET_ID_FALLBACK` in
`Callconsole.gs`). This is "Clinic Callback Tracker." Everything the staff and dashboard touch daily.
**New since v1:** the human-maintained **`Do_Not_Call`** tab (D194, S133) lives here — written by
humans only, read by the PC push script, never created by code.

### Spreadsheet B — the patient database · property `PATIENT_SHEET_ID`
A **separate** spreadsheet. `patientLookup_` (WebApp) opens `PATIENT_SHEET_ID` and reads the
`Patient_Master` tab. This is why "known vs unknown" works. **The two sheets are joined only in code,
at read time — never merged.**
*(v1 flag retained: whether `Patient_Master` physically lives in A, in B, or in both is `UNKNOWN` from
the export alone. Still unconfirmed. Flagged, not assumed.)*

### Drive — recordings & transcripts
`Call_Recordings` and `Call_Transcripts` are **tabs** (in Spreadsheet A) that hold *pointers*; the
audio and text **files** live in a **Drive folder** (`DriveApp.getFileById(...)`, Callconsole &
OutcomeLog). The dashboard fetches bytes on demand and never stores them.

---

## 2. EVERY TAB, WHICH FILE WRITES IT, WHICH READS IT

Compiled from every `getSheetByName(...)`, tab constant, and `appendRow`/`setValues` in the export.
**"One writer per table" is the stated invariant — deviations are called out.**

| Tab | Spreadsheet | Written by | Read by | Purpose |
|---|---|---|---|---|
| `Callbacks_Today` | A (`SHEET_ID`) | `Sheets.gs` (rebuild) + **staff by hand** (`Staff Status`, `Staff Notes`) | `staffStatusMap_` (WebApp) | The pending/handled engine. **No code writes `Staff Status` — manual only (S131, confirmed).** |
| `Callbacks_Archive` | A | `Sheets.gs` | reports | Prior-day rollover of `Callbacks_Today`. |
| `Daily_Report_Log` | A | `Monitor`/`Main` | morning report | Per-day report rows. |
| `Daily_Summary` | A | `Monitor` | summary email | 11/15/19h summary source. |
| `Daily_Monitor` | A | `Monitor` | monitor view | Busiest-hours / miss-rate stats. |
| `Call_Feed` | A | **VPS call-hook** (external) + `CallField.gs` rebuild | `fetchCallsBetween_` (WebApp) | The raw call event stream. THE dashboard's call source. |
| `Patient_Master` | B (`PATIENT_SHEET_ID`) | **manual / external** | `patientLookup_`, Callconsole | Patient identity. PHI. |
| `WA_Inbox` | A | WhatsApp pipeline (external) | `waLookup_` | Latest WA message per number. |
| `Agents` | A | manual | `agentInfoForKey_` | ext ↔ name ↔ key ↔ Active. |
| `Followups_Today` | A | follow-up push (PC, D194-filtered) | `getFollowups`, Health | Daily follow-up list, banded. **Filtered against `Do_Not_Call` at push (S133).** |
| `Followups_Settled` | A | `saveFollowupOutcome` (settle) | `getFollowups` | Terminal follow-ups. |
| `Followup_Outcomes` | A | **`saveFollowupOutcome` AND `saveIncomingOutcome`** | `getOutcomeLog`, Health | ⚠️ **TWO writers**, intentional. Incoming rows marked `rowKey='IN_'+phone+'_'+day`, `Section='Incoming'` — the ONLY separator between the streams. |
| `Followup_Escalations` | A | both outcome paths (escalate) | doctor queue | Escalations to the doctor. |
| `Outcomes_Log` | A | `Callconsole` (`logOutcome`) | `getOutcomeLog` | Call-Console permanent record. **Distinct from `Followup_Outcomes`.** |
| `Call_Durations` | A | VPS receiver (console-dialled OBD only) | `getCallDuration` | Per-call talk duration. |
| `Call_Recordings` | A | recording pipeline (02:00) | Callconsole, OutcomeLog | Drive audio pointers. |
| `Call_Transcripts` | A | transcription pipeline (03:00) | OutcomeLog (`getTranscriptText`, DOCTOR ONLY) | Drive transcript pointers. |
| `Do_Not_Call` | A | **humans only** (D194) | PC push script | Suppression list. Code never creates it; missing tab warns loudly, unreadable tab stops the push. |

> **⚠️ Two-writer tabs:** `Followup_Outcomes` (intentional single ledger — the `IN_`/`Section` marker
> is load-bearing) and `Callbacks_Today` (rebuild + staff columns, guarded by `STAFF_COL_COUNT`).

---

## 3. THE CALL FLOW — INCOMING (known / unknown) AND OUTGOING

### 3.1 What actually happens to an incoming call TODAY (owner-confirmed, S130; unchanged)

> **The incoming call rings on the MyOperator dialer in the receptionist's mobile. It does NOT open on
> the dashboard.** The dashboard learns about the call only after the fact, via `Call_Feed`, and
> renders a **missed-call tile** if it was missed and not yet called back.

This is the gap Block D closes (D181–D184): tile at hangup, both directions swept to the doctor 21:30.

### 3.2 Incoming — the data path, step by step

1. Call → MyOperator dialer (mobile). Staff answer or miss. Dashboard not involved yet.
2. MyOperator posts the event → VPS call-hook → row appended to **`Call_Feed`**.
3. On load/refresh, `getDashboardData` → `computeDashboard_` (WebApp):
   `fetchCallsBetween_` reads today's `Call_Feed`; `computeNetMissed_` (Netting.gs) nets
   missed-vs-called-back, marks priority (≥3 attempts) and after-hours; `patientLookup_` matches
   against `Patient_Master` (**this match = "known"**); `staffStatusMap_` reads `Staff Status`;
   `waLookup_` attaches the latest WhatsApp message.
4. Each netted entry becomes an **incoming missed-call tile** (L909), unless its `Staff Status` is a
   "done" word → **handled** tile instead.

### 3.3 KNOWN vs UNKNOWN — the branch (POST-FIX-B mechanics, re-derived this session)

The tile build (L905–L928) computes `known = !!(e.patient && (e.patient.name || e.patient.dx))`
(L914) and stores the patient packet in a **page-level map**: `IN_PAT[inId] = {name,uid,last,dx}`
(L915). **No patient data enters button markup** — the button is
`onclick="inOpen('inId','number',known)"` (L926), a clean three-argument call. `inOpen(slotId,
number, known)` (L1263) reads the packet from `IN_PAT` by id. *(This is Fix B, shipped S132 — v1
described the old four-arg/packet-in-markup form, which no longer exists.)*

- **KNOWN incoming**: the `Log outcome ▾` card opens straight to **Reason → Resolution**.
- **UNKNOWN incoming**: the card first asks **"Who is this?"** with the five identities
  (existing-patient-new-number · new patient enquiry · 🚨 doctor/urgent (always escalates) ·
  not a patient · the blank prompt).

### 3.4 OUTGOING calls

Placed from the dashboard by `triggerCall`/`placeCall` via the OBD click-to-call relay. A callback is
*detected* by `computeNetMissed_` (outgoing-after-missed = `triedOut`, shown as "↗ Outgoing not
replied"). Outgoing calls change a tile's *state*, not its logging path.

---

## 4. THE OUTCOME OPTIONS — EXACTLY, AND WHERE EACH APPEARS

Three vocabularies, not interchangeable. (Unchanged from v1; re-checked present in this export.)

### 4.1 INCOMING — KNOWN patient (`IN_REASONS`, 10 · `IN_RESOLUTIONS`, 5)
Reasons: Appointment · Reports ready? · Pharmacy/medicines · X-ray availability · Billing/payment ·
**Post-op/recovery concern\*** · **New symptom/problem\*** · Directions/timings/info ·
**Wants to speak to doctor\*** · Other.
Resolutions: Resolved on call · Appointment booked · Info given, will act · Needs callback (stays) ·
**Escalate to doctor**. `*` reasons and "Escalate" trigger doctor escalation.

### 4.2 INCOMING — UNKNOWN, "New patient"/"Doctor-urgent" (`IN_NEW_OUTCOMES`, 6 + `IN_CHANNELS`)
Appointment booked · Will come/considering · Info given/enquiry only · Needs callback · **Escalate to
doctor** · No action. Channels: Google/GMB · Referral · Hoarding/banner · Clinic app · Family/friend ·
Online/social · Other.

### 4.3 FOLLOW-UP calls (`FU_OUTCOMES`, 10) — **the one used daily**
Coming/will visit · Out of town · On medication · Already visited (dikha chuke) · Problem/needs
attention · Close follow-up · Not interested · Treatment elsewhere · Wrong number · Asked not to call.
Server routing (`saveFollowupOutcome`): **SETTLE** (`FU_SETTLING`: coming, out_of_town, on_medication,
unreach_*) → also `Followups_Settled` · **ESCALATE** (`FU_ESCALATING`: dikha_chuke, problem,
close_followup, not_interested, treatment_elsewhere, wrong_number, asked_not_to_call) → also
`Followup_Escalations` · otherwise **RETRY**. Extra fields: date (`FU_NEEDS_DATE`), medication
source/days (`FU_IS_MED`). **`wrong_number` / `asked_not_to_call` / deceased now have downstream
enforcement: a human row in `Do_Not_Call` (D194) — escalation routes the case, the tab suppresses the
number.**

### 4.4 CALL CONSOLE — `Outcomes_Log`, via `logOutcome` (Callconsole)
Separate permanent record with agent resolved server-side from the key. Its option set is defined in
`Callconsole.gs` — still not enumerated here (carried open item, see §8.2).

---

## 5. THE FATE OF EACH TILE — WITH AND WITHOUT AN OUTCOME

| Tile type | What removes it from pending | If NO outcome filed | If outcome filed |
|---|---|---|---|
| **Incoming missed — known** | `Staff Status` on `Callbacks_Today` set to a "done" word (`done/booked/resolved/complete/reached/called/spoke/connected`, not containing "callback") — **manual sheet entry only; no code writes it** | Stays pending | Card clears; `IN_` row lands in `Followup_Outcomes`; **tile persists** until status set. Escalating resolutions also write `Followup_Escalations`. **Post-Fix-B the button now actually works for known patients.** |
| **Incoming missed — unknown** | Same (status-driven) | Same | Same, with identity captured |
| **Follow-up tile** (`Followups_Today`) | `saveFollowupOutcome` — client hides the row immediately (`fuPending`), server settles/escalates/retries | Stays in its band, day after day | **Tile removed on save** — the path that behaves as staff expect |
| **Resolved-callback tile** | Read-only, informational | n/a | n/a |
| **Escalation tile** (doctor, `#secEscal`) | `resolveEscalation` **or `sendBackToStaff`** (L2482) | Sits in doctor's list | Doctor's action clears it. **`sendBackToStaff` writes `SENT_BACK`; `getFollowups` (WebApp L938 region) re-surfaces the row as a staff tile under "Sent back by doctor" with the note, auto-clearing when staff file a newer outcome — the doctor→staff loop, live since S52 (documented S131).** |
| **Handled tile** | Already handled; shown for the day | — | — |

> **The asymmetry, stated plainly (unchanged):** the follow-up tile removes itself when you log an
> outcome; the incoming tile waits on a hand-typed `Staff Status`. Fixing F-8 made the incoming button
> *work*; it did not make the tile *clear*. Unifying the two gestures is Block D's job, deliberately.

---

## 6. F-8 — HISTORY AND CURRENT STATE: **FIXED (S132, Fix B; D190 executed)**

**The defect (v18.19 era):** the old tile build passed `jsq(JSON.stringify(packet))` into a
double-quoted `onclick`; `jsq` did not escape `"`; the attribute closed at the first `"` inside the
patient JSON, so for **any `Patient_Master` match** the `Log outcome ▾` handler was never installed.
Evidence (S130, owner read the tab): 400+ `Followup_Outcomes` rows, exactly **two** with
`Section='Incoming'` — both `non_patient`, the only identity the defect permitted. **Zero named
callers ever.** D153 ("staff never file incoming outcomes — workflow finding") was overturned as D190:
an impossibility had been recorded as a habit.

**The fix (Fix B, S132):** the packet lives in the page-level `IN_PAT` map (L915); `inOpen` takes
three plain arguments (L1263) and reads the map; **no patient data in button markup** (`dataset.pat`
count in this file: **0**). The fix also removed the two client catches that had hidden the defect
(old L1260/L1364 — F-14's three wrong catches, two of them).

**Residual, by design:** a working button still does not clear the tile (§5). That is the documented
asymmetry, not a regression.

---

## 7. THE 24 SERVER CALLS THE PAGE MAKES (re-verified in this export: 24 distinct)

| Function | File | Purpose |
|---|---|---|
| `getAccess` | WebApp | Login: key → role (full/staff/none) + agent identity. **Accepts `DASH_KEY` OR `SECRET_KEY` as the full key (WebApp L148 — `SECRET_KEY` is this project's live property name, confirmed S134); `STAFF_KEY` → staff; `AKEY_<ext>` → per-agent.** |
| `getDashboardData` | WebApp | Main snapshot: pending/handled/resolved/WA/KPIs |
| `getFollowups` | WebApp | Follow-up list (banded) **+ `SENT_BACK` resurfacing** |
| `getFollowupFreshness` · `getFollowupLastVisits` · `getFollowupClinicIds` · `getFollowupRecordings` | Callconsole | Follow-up row enrichment |
| `saveFollowupOutcome` | WebApp | Log a follow-up outcome (settle/escalate/retry) |
| `saveIncomingOutcome` | WebApp | Log an incoming outcome (single caller: L1398) |
| `getEscalations` · `resolveEscalation` · `sendBackToStaff` | WebApp | Doctor escalation queue + send-back loop |
| `getAllCallsToday` | Callconsole | All-calls console feed |
| `getCallDuration` | Callconsole | Per-call duration |
| `getOutcomeLog` | OutcomeLog | Activity log view |
| `reviewOutcome` · `reviewOutcomeBatch` | OutcomeLog | Doctor review of outcomes |
| `getRecordingAudio` | WebApp | Live-feed recording bytes |
| `getArchivedRecordingAudio` | Callconsole | Archived recording bytes |
| `getTranscriptText` | OutcomeLog | **DOCTOR ONLY** transcript fetch |
| `getThread` · `sendReply` · `checkWindow` | WebApp | WhatsApp panel |
| `triggerCall` | WebApp | Place an outgoing call (OBD relay) |

Every one begins with `if (dashRole_(key) === 'none') return …` — the data gate D189 preserved.

---

## 8. SESSION & KEY HANDLING — **NEW SECTION (F-11/A-4 closed, S134)**

1. **Boot** (L2743–2749): a `clinicSignedOut` flag is checked **first**; if set, the login card shows
   and **both** the `?k=` URL parameter and the remembered key are ignored. Otherwise `?k=` (via
   `google.script.url.getLocation`) is tried, then `localStorage.clinicDashKey`, else the login card.
2. **Login** (`applyAccess`, L2713–2716): stores the key in `localStorage.clinicDashKey` and
   **clears `clinicSignedOut`** — explicit login re-arms auto-login.
3. **Sign out** (`doSignOut`, L2732–2738; header button L505): removes `clinicDashKey`, sets
   `clinicSignedOut`, zeroes `DASH_KEY`/`DASH_ROLE`, stops the refresh timer, shows the login card.
4. **Honest limitation, stated:** the Apps Script sandbox **cannot edit the parent address bar**, so a
   `?k=` already in the URL/history cannot be stripped by code. The signed-out flag *neutralises* it on
   this device; keyed URLs in shared-device browser history remain the owner's manual hygiene step, and
   staff should use the bare `/exec` URL after first login.
5. The key remains cleartext in `localStorage` while signed in — accepted; Sign out is the remedy.

**Client silent catches, counted with scope (D179):** 18 remain in the page — every one a trivial
`localStorage`/DOM guard (7 of them added by S134's own key-hygiene code, correctly). F-14's three
*wrong* catches are all gone: two removed with Fix B (S132), and the `openThread`-after-send catch now
logs to console (S134, A-3 closed). The reply is already sent when that path runs; console is the
right level.

---

## 9. WHAT IS STILL `UNKNOWN` / NOT IN CODE

1. **Which spreadsheet physically holds `Patient_Master`** (A, B, or both). Carried from v1, still
   unconfirmed by opening both files.
2. **The `Outcomes_Log` option set** — defined in `Callconsole.gs`, still not enumerated here.
3. ~~Whether `IN_` rows exist~~ — **ANSWERED S130** (two rows, both `non_patient`; §6).
4. ~~Who writes `Staff Status`~~ — **ANSWERED S131**: nothing in all fifteen files writes it;
   manual-only. WebApp L247-region clears the tile on it; the machine's own `settle/escalate/retry`
   computation for incoming (WebApp ~L1252–55 era) is written and rendered but consumed by no removal
   mechanism. Block D territory.
5. **`PAGE_BUILD` is a page-file stamp, not a server-version stamp** (F-16). Still true; the served
   page cannot tell you which `WebApp.gs` version `/exec` runs. Log, don't fix.

---

## 10. IMPLICATIONS FOR BACKEND CHANGES

- **F-8 is fixed; the tile asymmetry is not** — any Block D design must unify "log outcome" and
  "clear tile" for incoming, as it already is for follow-ups.
- **The `Followup_Outcomes` two-writer split** means any AI-verdict join on that tab must filter on
  the `IN_`/`Section` marker or conflate the streams (bears on D158).
- **"Did staff handle this incoming call?" is answered by `Callbacks_Today.Staff Status`**, not by
  `Followup_Outcomes` — and that column is hand-typed. Any report counting incoming resolution from
  the outcomes tab measures the wrong column.
- **The doctor send-back loop and the escalation queue are the insertion points** the parked AI review
  layer will reuse (second row source into an existing loop, not a new mechanism).

---

**END — Frontend Documentation v2 (S134). Complete self-contained re-base of v1; no delta (D202). §10 is the last section — if §10 is absent, this file is truncated.**


---

# §V3 — WHAT CHANGED v18.22 → v18.27 (Sessions 135–139)

## V3.1 Version ladder
| Build | Session | Change |
|---|---|---|
| v18.22 | S135 | F-34 shared-mobile fix: composite phone+name keys; "ID ⚠ verify" |
| v18.23–25 | S135b–S136b | F-35 SEND BACK loop; D211 one-trip bundle; D212 WA-tile today's-call; F-36 name-aware escalation cards |
| **v18.26** | **S139** | **F-10 CURE (D219): `dref()`/`dget()` opaque data refs — read V3.2 before touching ANY handler markup** |
| **v18.27** | **S139** | **K-1 one-tap staff UI (§K.7 of Console Spec v2.3)** |

## V3.2 THE ONE RULE EVERY FUTURE EDIT MUST FOLLOW (D219)
No data-derived value is EVER interpolated into element markup. The pattern:
```
'<button onclick="handler(dget(\''+dref(value)+'\'))">'
```
`dref(v)` → opaque key (`d17`, [a-z0-9] only, dedupe-bounded map, stable across re-renders); the handler
receives `dget(key)` = the exact original value. `esc()` stays for TEXT context; `jsq()` survives only for
values that are already our own generated literals. Adding a new button with `esc()`/`jsq()` inside an
`onclick` reintroduces the F-8/F-10 bug class and will be treated as a defect.

## V3.3 K-1 surface (client map)
- Module sits above the D66 block: `K_LABELS/K_ORDER`, `kOn/kToggleUI/kPaintToggle`,
  `kMiss/kSnoozedNow/kWakeNow`, `kBtns/kPendingHtml/kTap/kUndo/kCommit`, `kRenderComp/kRenderStrikes`.
- `fuRowHtml` branches: kSnooze band pre-empts; `talked`→`kBtns(rid,'full')`; `missed`→`kBtns(rid,'noContact')`
  (pre-highlighted single honest choice + ↻ फिर call करें); `timedout`→fail-open all five. Old flow renders
  when the ⚡ toggle is OFF (localStorage `K_UI`); per-device.
- Undo model: tap → 10 s pending (↩︎ बदलें) → `kCommit` → `google.script.run.saveKOutcome` → `pollFollowups()`.
  Undo before commit is pure-client; nothing is written until commit.
- Bundle fields consumed in `applyBundle`: `missTotals` (cross-day counter, D220), `kLogged` (completion
  numerator), `kStrikes` (doctor band; section `#secKStrikes` self-shows when non-empty).
- New ids/classes: `#kToggle #kComp #secKStrikes #kStrikes`, `.k-btns .k-btn .k-undo .k-done .k-snz .k-note`,
  per-tile `knote_<rid>`, `kundosec_<rid>`.

## V3.4 Server contract (Callconsole v1.6)
`saveKOutcome(key,{rowKey,kcode,note,name,mobile,section,diagnosis,clinicId,lastVisit,due})` →
`{ok,kcode,outcome,settle,missCount?,strike?}`. Mapping per D221 (§K.7). Bundle additions:
`missTotals`, `kLogged`, `kStrikes` (full role only). 3rd-strike relay call: `WA_SEND_URL+'/template'`,
X-Send-Key = existing `SEND_API_SECRET`; fail-open toward the save (D222).

## V3.5 The v2 stale read-path note — RESOLVED
v2 was flagged "stale read-path". The canonical read path is restated: the LIVE editor export (D160) is
the only source of `Dashboard.html` truth; GitHub lags live (proven again S139 on the portal). Verify by
export-form md5 before any edit; every edit is a guarded anchor replace with count==1 asserted.


---

# §V4 — WHAT CHANGED v18.27 → v18.28f (Session 140: K-2 + the leads band)

## V4.1 Version ladder (continues V3.1)
| Build | Session | Change |
|---|---|---|
| **v18.28** | **S140** | **K-2 incoming one-tap + 🌱 New-leads band (§K.8 of Console Spec v2.4)** |
| v18.28b–f | S140 | Dark-theme colours · `kInSlotR` on Resolved tiles · **one-tap default ON (D228)** · unknown callers show a dialable number · `.ac-name` link CSS |

Live file: `Dashboard.html` **v18.28f**, md5 `d528e666b258d1faf958e890e691d68a`, deployed as a New
version on the existing deployment; `PAGE_BUILD` stamp verified live. Server: `Callconsole.gs` **v1.7**,
1,224 lines, md5 `b1d49c6227ba16d0e7a57340a03d1a31`.

## V4.2 The K-2 client surface
- **Known patient, connected incoming tile** → the K-1 five-button set (V3.3 machinery reused), via the
  `kIn*` handlers with the same 10-s ↩︎ undo. Write path: `google.script.run.saveKOutcome` (Callconsole).
- **Unknown caller, connected incoming tile** → **7 lead buttons** (`L_LABELS`/`L_ORDER`; D225). Button 1
  "Appointment booked"; button 7 पुराने मरीज़ — नया नंबर → `inIdentity('existing_new_number')` (the existing
  v17 link-patient form). Write path: the **frozen WebApp `saveIncomingOutcome` (D34)** — no new endpoint.
- **`KIN_PAT`** patient map uses the D219 `dref`/`dget` opaque-ref pattern — **no PHI in onclick markup.**
- 🚨 `surgery_enquiry` = instant doctor push. `kInSlotR` renders the button row on Resolved tiles too.
- **Missed incoming calls keep the old "Log outcome ▾" dropdown** — K/L sets are for connected calls only.
- ⚡ one-tap now **defaults ON** (D228); localStorage `K_UI` survives as the per-device escape hatch,
  scheduled for removal at >42 % usage × 5 consecutive clinic days.

## V4.3 The 🌱 New-leads band (`secNewLeads`)
Sits ABOVE Today's calls; self-shows when the bundle's `newLeads` array (cap 30) is non-empty. A lead =
an unknown connected caller with a lead-ish outcome in the last **3 days** (`LEAD_TTL_DAYS=3`, D226).
`enquiry_only` (जानकारी दे दी) keeps the lead alive; the lead leaves the band on `Patient_Master`
conversion, a terminal outcome, or expiry; escalated leads render in the escalation queue instead.
Unknown numbers in the band are dialable.

## V4.4 Server contract (Callconsole v1.7)
`cc_outcomeScan_()` performs **ONE `Followup_Outcomes` read per bundle build** and derives all three of:
`missTotals` (D220 counter — now BOTH directions, D227), `kLogged`, and `newLeads`. This retires the S139
"Block-C read-merge" backlog item. `cc_patientMap_` is memoised per execution (`CC_PMAP_MEMO`). Bundle
additions consumed by `applyBundle`: `newLeads`. No new tabs; no new writers; no read-count increase.

## V4.5 The rule restated
V3.2 (D219) governs every K-2 site: `KIN_PAT` and every lead-button handler pass only `dref` keys through
markup. Any future edit that interpolates a name, number, or diagnosis into `onclick` markup is a defect.
