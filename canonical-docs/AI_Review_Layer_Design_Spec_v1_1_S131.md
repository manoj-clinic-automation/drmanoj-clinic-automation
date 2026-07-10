# AI REVIEW LAYER — DESIGN SPECIFICATION — v1.1
**Dr. Manoj Agarwal Clinic · Bareilly · Session 131 · 09 July 2026**
**Status: DESIGNED, NOT BUILT. Nothing in this document has been implemented.**

> **v1.1 — one correction, made in the same session.** v1.0 §1.1 described F-8's blast radius as *"wider than the audit's headline."* **It was not.** Audit v1.2 said it in Session 129, in its title (*"dead for every patient in `Patient_Master`"*) and in its body (*"the breaking condition is `e.patient` being truthy … not the `known` flag"*). This specification restated an existing finding and credited itself with widening it. **The fact is unchanged; the lineage was wrong.** Corrected below, and recorded in Audit v1.3's F-8 lineage note and KB §S131.11. *Nothing in the design depends on who found it first — which is exactly why it was easy to get wrong.*

> **How to read this.** Every item carries a tag:
> **NOW** — build it in the next session.
> **PROVISION** — create the column, the tab, the empty slot. Inert. Costs nothing at runtime.
> **LATER** — designed, priced, and deliberately not built. Gated on something named.
>
> Every server-side item names the file it touches. **`WebApp.gs` is D34-protected**; §6 raises that question once and does not raise it again.

---

## §0 — THE SENTENCE THIS SPECIFICATION IMPLEMENTS

> **The judge proposes. The doctor disposes. The staff act.**

Each clause is a **writer of a different table**. That is not a slogan; it is the invariant the design is built to preserve.

| Clause | Writer | Table |
|---|---|---|
| The judge proposes | `call_verdict.py` (VPS) | `Call_Verdicts` |
| The doctor disposes | the dashboard (Apps Script) | `Doctor_Verdicts`, `Followup_Escalations` |
| The staff act | the dashboard (Apps Script) | `Followup_Outcomes` |

**No table gains a second writer anywhere in this specification.**

### The asymmetry that governs every gate

> **A false bounce costs one phone call. A false settle closes a case that never connected, and is invisible.**

Wherever this design chooses to be cautious, that sentence is the reason.

---

## §1 — F-8: THE INCOMING `Log outcome ▾` BUTTON

### 1.1 The defect, from the artefact

Two escapers, each blind exactly where the other sees (**F-10**):

| Function | Line | Escapes | Blind to |
|---|---|---|---|
| `esc()` | 685 | `&` `<` `>` `"` | `'` |
| `jsq()` | 729 | `\` `'` | `"` |

**L912** — `var pj = e.patient ? jsq(JSON.stringify({name,uid,last,dx})) : '{}';`

`JSON.stringify` **always** emits `"`. `jsq` does not touch `"`. The packet leaves L912 carrying raw double quotes.

**L923** pastes it into a button whose `onclick` attribute is delimited by `"`. The browser stops the attribute at the first `"` inside the packet and attempts to compile:

```
inOpen('in_9812345678_0','9812345678',true,'{
```

An unterminated string. **The handler is never installed.** The button renders, looks perfect, and does nothing. No error appears at click time, because the failure happened when the page was drawn.

**Blast radius — established in Audit v1.2 (S129), restated here.** The breaking condition is `e.patient` being **truthy** — *any* number matching `Patient_Master`, including a bare UID with no name. `known` (which needs a name or a diagnosis) is a strictly narrower set.

### 1.2 Fix A — one line **[NOW, if B is rejected]**

```js
var pj = e.patient ? esc(jsq(JSON.stringify({…}))) : '{}';
```

Order is not arbitrary. **The browser decodes HTML entities first, then compiles the JavaScript.** So the value must be JS-escaped on the inside (`jsq`) and HTML-escaped on the outside (`esc`).

Worked example — `Ram & Co's`:
`stringify` → `{"name":"Ram & Co's"}` → `jsq` → `{"name":"Ram & Co\'s"}` → `esc` → `{&quot;name&quot;:&quot;Ram &amp; Co\'s&quot;}`
The attribute now closes where it should; the browser decodes it back to valid JavaScript; `JSON.parse` at L1260 succeeds.

### 1.3 Fix B — six lines **[NOW — RECOMMENDED]**

Stop putting the patient in the markup at all.

```js
// at render, per tile:
IN_PAT[inId] = e.patient || {};
// the button carries digits and our own id, nothing else:
onclick="inOpen('in_98…_0','9812345678',true)"
// inOpen looks the packet up:
function inOpen(slotId, number, known){ var pat = IN_PAT[slotId] || {}; … }
```

| | Fix A | Fix B |
|---|---|---|
| F-8 closed | ✅ | ✅ |
| The `catch(e){}` at **L1260** — A-3's first item, the one that hid F-8 | remains | **removed** — no `JSON.parse` left to fail |
| **Block E**: *stop embedding patient data in button markup* | untouched | **delivered** |
| Patient name / UID / diagnosis present in the page's HTML source | yes | **no** |
| Lines changed | 1 | ~6 |

### 1.4 Price

**Files touched:** `Dashboard.html` **only**. No server file. **No D34 question.**
**Staff path disturbed:** yes — it starts working.
**Rollback:** redeploy the previous version. `/exec` URL unchanged (never a new deployment).
**Verification:** a known patient's `Log outcome ▾` opens the card; an `IN_` row with a real name reaches `Followup_Outcomes`. The two `non_patient` rows of 29 Jun / 1 Jul remain the only pre-fix incoming outcomes in the tab (**D190**'s evidence — do not disturb it).

---

## §2 — THE TILE-REMOVAL CONTRACT (D195)

### 2.1 Why a working button is not enough

A **follow-up** tile leaves because `saveFollowupOutcome` classifies the outcome `settle` / `escalate` / `retry` (**WebApp L1140–41**), settling rows land in `Followups_Settled`, the reader excludes them, and the client hides the row at once with an undo window (`fuPending`). **The same system decides and clears.**

An **incoming** tile leaves at **WebApp L247**:

```js
if (isDoneStatus_(st)) handled.push(item); else pending.push(item);
```

…where `st` is `Callbacks_Today.Staff Status`.

**Established, not assumed:** every `setValue` and `setValues` in all fifteen files was searched. **Nothing in this project has ever written `Staff Status`.** `Sheets.gs` preserves it deliberately (`STAFF_COL_COUNT: 2` — the last two columns are staff-owned) and writes only `Auto-Status`.

**So the only thing that has ever cleared an incoming tile is a human typing a word into the Google Sheet by hand.** Ship a working button on its own and it will log without clearing — its own confusion.

### 2.2 What already exists, unused

**WebApp L1252–55:**

```js
var settle = escalate ? 'escalate' : (IN_NONSETTLING[resolution] ? 'retry' : 'settle');
```

`IN_NONSETTLING = { needs_callback: 1, cant_communicate: 1 }`. The verdict is already written to `Followup_Outcomes`. The client at **L1382** already renders *"saved — stays for callback"* on `retry`.

**The machine is built. Nobody consumes its output.**

### 2.3 The change **[NOW — gated on §6]**

- The pending builder **excludes** numbers with a same-day `Section='Incoming'` row in `Followup_Outcomes` whose `Settle` is `settle` or `escalate`.
- `retry` rows **deliberately keep their tile.** That is the bounce-back path.
- The client hides the tile on save with an undo window — `fuPending`'s exact shape, renamed `inPending`.
- **`Staff Status` is never written by the dashboard.** Removal is driven by *reading* `Followup_Outcomes`, exactly as follow-up removal is driven by reading `Followups_Settled`. **`Callbacks_Today` keeps precisely one writer.**
- `Staff Status` survives as a **manual override that still clears** — one mechanism for the machine, one for a human who wants the last word.

### 2.4 Attempt caps

- **3 attempts** on Groups A and B (§4).
- On the 4th, the case becomes **`exhausted`** and goes to the **doctor**, not back to staff.
- **Exception:** `voicemail ×3` routes to the **doctor**, not to `exhausted`. Three voicemails is a different fact from three busy signals.
- **`wrong_number` and `number_invalid` are exempt.** A cap is meaningless on a number that was never the patient's.

### 2.5 Price

**Files touched:** `Dashboard.html` **and `WebApp.gs`** (L247 + `saveIncomingOutcome`'s return). **Requires §6.**
**Cost booked:** the pending build gains one read of `Followup_Outcomes`. That lands on **F-6 / F-12** (whole-tab reads; ~9 server calls/min/tab). **Block C exists to make exactly this cheap.** Not a blocker; a cost recorded.
**Rollback:** redeploy previous version.

---

## §3 — THE STABLE CASE IDENTITY (D196) **[NOW — prerequisite for §5]**

`saveIncomingOutcome` keys everything `IN_<phone>_<yyyymmdd>` — a **day** key, not a **case** key.

The send-back loop clears a tile by `lastOut[key] >= sentBackWhen` (**WebApp L940**). **Cross midnight and a fresh incoming outcome takes a different key** — so a sent-back incoming tile *can never clear itself*. The follow-up loop works only because follow-ups have a stable key.

**Adopt the judge's own identity: `<phone>_<call_epoch>`** — e.g. `9690543321_1783322828`, visible in the banked `Verdict_Review` run. A call id, stable forever, already produced by Stage 3.

This sits directly on **D158's join defect** and closes it. `escPick_` (**L1395**) — which picks the call at or just before the outcome save, never one hours later — becomes a fallback rather than the join.

**Files touched:** `WebApp.gs`, `call_verdict.py`. **Requires §6.**

---

## §4 — AXIS 1: CONTACT (D192) **[PROVISION now · LATER to act]**

> *"Did a usable conversation happen, and with whom?"* — answered **separately** from *"what was said."*

**Blindness preserved (D149, D198):** every code below is decidable from **transcript + direction + duration** alone. The judge never sees the staff's claim, the patient's name, or the agent's identity.

### Group A — never connected. **No recording exists, so the AI never sees these.**

**Metadata only. Zero AI cost.** Source: `Call_Durations.customer_result`, `status`, `total_duration`, and `recording_filename` **empty**.

| Code | Meaning | Disposition |
|---|---|---|
| `no_answer` | rang, not picked up | → staff · cap 3 · then `exhausted` → doctor |
| `busy` | engaged | → staff · cap 3 |
| `unreachable` | switched off / out of coverage | → staff · cap 3 |
| `call_failed` | telecom failure, our side | → staff · cap 3 |
| `number_invalid` | disconnected / operator error message | **never to staff.** → `Do_Not_Call` (§7) |

> **Caveat, booked:** `Call_Durations` covers **console-dialled calls only** (D178, and **F-19**). `Call_Feed` covers all, on a nightly 21:30 clock. **Group A for incoming calls is blocked on F-19.**

### Group B — connected, no usable human conversation

**To staff with the reason and the recording, *and* a flagged card on the doctor's tab, in parallel.** Cap 3.

| Code | Meaning | Disposition |
|---|---|---|
| `voicemail` | answering machine / recorded greeting | → staff · **×3 → doctor**, not `exhausted` |
| `ivr_or_bot` | another company's auto-attendant answered | → staff · cap 3 |
| `answered_silent` | picked up, nobody spoke | → staff · cap 3 |
| `audio_unusable` | speech present but unintelligible; noise, breakup, one-way audio | → staff · cap 3 |
| `call_dropped` | cut off before the purpose was stated | → staff · cap 3 |
| `language_barrier` | no shared language | **doctor only.** Needs a different agent, not another attempt |

### Group C — a human answered, but not the right one. **All flag the doctor.**

| Code | Meaning | Disposition |
|---|---|---|
| `wrong_number` | not this patient's household at all | **settles the case AND flags the doctor** so the number can be corrected. Not a queue item. Cap exempt. Already a live FU outcome code |
| `spoke_other_person` | right household, patient not there | flagged card → doctor |
| `callback_requested` | right household, asked us to call at a stated time | **→ staff with the stated time.** Informational on the doctor's tab |

### Group D — the right person

| Code | Meaning | Disposition |
|---|---|---|
| `spoke_patient` | the patient themselves | outcome stands |
| `spoke_family_proxy` | family member speaking **for** the patient | outcome stands |
| `patient_deceased` | stated by the family | **settles permanently.** → `Do_Not_Call`. **Only the doctor may set this flag.** Never re-dialled |

> `spoke_family_proxy` is not a nicety. In this practice — older, Hindi-first, semi-urban patients — the son or daughter answering **is** the normal case, and the record cannot currently tell it apart from the patient speaking.
>
> `patient_deceased` **has no code anywhere in the system today.** A bereaved family can be, and will be, re-dialled by tomorrow's follow-up list.

### Group E

| Code | Disposition |
|---|---|
| `unclear` | **no default.** Waits on the doctor's tab |

### Axis 2 — OUTCOME. Unchanged.

The existing 11 follow-up codes and the incoming lists. **Meaningful only when Axis 1 is `spoke_patient` or `spoke_family_proxy`.**

Every other contact code makes the outcome field moot — **which is the invisible failure this layer closes. Today a staff member can file `coming` on a call that was a voicemail, and nothing in the system objects.**

---

## §5 — THE DOCTOR'S REVIEW SECTION

### 5.1 It is not a new mechanism

`sendBackToStaff` (**WebApp L1502**) writes `SENT_BACK` plus the doctor's free-text note into `Followup_Escalations`. `getFollowups` (**L938**) reads it back and rebuilds it as a staff tile in a section named **"Sent back by doctor"**, carrying the note, the original outcome reason, who filed it, when, and the matched call. It **auto-clears** the moment staff file a newer outcome.

`getEscalations` (**L1387–1401**, v18.6/v18.8) already attaches the **recording and the transcript** per row, via `OL_todayCallsAndMissed_`, `OL_transcriptsByKey_`, and `escPick_`.

**This loop has been live since Session 52. The AI review section is a second row source into it.**

### 5.2 The two-phase gate (D191) **[Phase 1 NOW · Phase 2 LATER]**

**Phase 1 — no machine-initiated tile movement of any kind.**
A verdict places a card on the doctor's tab: recording, highlighted transcript, contact code, outcome, conduct flags. **His click** sends the tile back to staff. **That click is the referee decision**, and it is what fills `Doctor_Verdicts`.

> This is why the design pays for itself. Today the judge's accuracy is unmeasured — 32 cards, **0 refereed**; every accuracy claim is the judge agreeing with itself. Under Phase 1 the ground-truth ledger builds itself out of a day's ordinary work.

**Phase 2 unlocks machine auto-bounce for Groups A and B only**, on all three:

1. **100 refereed cards**, and
2. **≥95% agreement** on the bounce / no-bounce call, and
3. **zero cases in the last 50** where the judge said the conversation was fine and the doctor disagreed.

**Groups C, D and `unclear` never auto-move.** Condition 3 is the asymmetry: a false bounce costs one phone call; a false settle is invisible.

### 5.3 Volume — this is a realistic queue

From the banked run (`Verdict_Review_first_run_06Jul_S124.csv`, 7-day window): **36 outgoing · 26 incoming**; 4 mismatches, 9 *"AI logged, staff didn't"*, 13 unclear, 1 suspect join. **≈ 4 cards a day.** At eighty a day the section would be dead within a week.

### 5.4 The writer flip (D193) **[NOW]**

`Call_Verdicts`, `Verdict_Review` and `Doctor_Verdicts` live in the **doctor-only "Call Audit" sheet** — *a third spreadsheet.*

**The Apps Script has no handle on it.** Its entire property list: `SHEET_ID · PATIENT_SHEET_ID · DASH_KEY · STAFF_KEY · AKEY_* · MYOP_TOKEN · NTFY_TOPIC · SUMMARY_EMAIL · SUMMARY_NTFY · CALL_API_SECRET · SEND_API_SECRET · SECRET_KEY`. **Zero references.**

- Add script property **`AUDIT_SHEET_ID`**. The dashboard now reads **three** spreadsheets.
- **The dashboard becomes the sole writer of `Doctor_Verdicts`.**
- `verdict_review.py` **retires its harvest** and its sheet-based dropdowns. Its destroy-and-redraw would otherwise erase dashboard writes.
- `call_verdict.py` **keeps sole ownership of `Call_Verdicts`.**

**One writer per table, preserved (parent D155).**

### 5.5 F-18 must be fixed before any of this is trusted **[NOW]**

`verdict_review.py` prints **D153** — overturned by **D190** — as a design justification:

> *"Incoming calls, no claim — 19 — Correct by design — staff do not log incoming…"*

**Nineteen incoming calls were excused from scrutiny on a premise that is false.** No count from that layer means anything until this is removed.

---

## §6 — THE D34 QUESTION. ASKED ONCE.

**D34: `WebApp.gs` must never be touched. New server functions go in `CallConsole.gs` or `OutcomeLog.gs`.**

Every server-side piece of this design lives in `WebApp.gs`:

| Function | Line | Needed for |
|---|---|---|
| the pending builder | 247 | §2 |
| `saveIncomingOutcome` | 1233 | §2, §3 |
| `getFollowups` | 925+ | §5 |
| `getEscalations` | 1373 | §5 |
| `sendBackToStaff` | 1502 | §5 |

**This design cannot be built without touching `WebApp.gs`.**

**D189 established the pattern:** suspend D34 **by name**, for a **bounded** edit, **resume on verification**. That precedent was set for a deletion of eight lines. This is larger.

**The owner's decision, and nobody else's:**

- **(a)** Suspend D34 by name for a bounded set of edits to `WebApp.gs`, resumed on verification against a fresh export. *This is the only route to §2, §3 and §5.*
- **(b)** Refuse. Then **§1 (F-8 Fix B) and §7 (`Do_Not_Call`) still ship** — they touch `Dashboard.html` and `push_followups_today.py` only. Everything else stops.

**Nothing server-side is built until this is answered.**

---

## §7 — `Do_Not_Call` (D194) **[NOW — no `WebApp.gs`, no waiver]**

### 7.1 Why the flag cannot live anywhere else

Established from the artefact:

- The Apps Script performs **zero writes** against `PATIENT_SHEET_ID`. It reads the patient database and nothing more.
- `Followups_Today` is **read-only** to the dashboard. It is rewritten **every morning** by `push_followups_today.py` on the clinic PC.

**A flag that lives anywhere else is overwritten before breakfast.** Mark a patient deceased in the dashboard and tomorrow's generator re-creates the row.

### 7.2 The design

- **One new tab** in the Clinic Callback Tracker: `Do_Not_Call`.
- Columns: `Phone · Reason · Set By · Set When · Note`.
- Reasons: `number_invalid` · `patient_deceased` · `asked_not_to_call`.
- **`push_followups_today.py` reads it before it writes**, and skips those numbers. One filter line in a script we own.
- **Only the doctor may set `patient_deceased`.** Staff may file the outcome; his confirmation writes the row.

### 7.3 What it closes

- `patient_deceased` — a bereaved family being re-dialled. **No code for this exists today.**
- `number_invalid` — the definitive action, in one place.
- **F-20** — `asked_not_to_call` is a **live outcome code with no enforcement anywhere.** Filed by staff, ignored by the generator, patient called again tomorrow.

**Three problems, one tab, one writer.**

---

## §8 — AXIS 3: CONDUCT (D197) **[PROVISION now · LATER to report]**

### 8.1 No composite score. Six binary checks.

A composite number — 78/100, four stars — does three bad things at once in a four-person clinic. It invites comparison between people who sit in the same room. It hides *which behaviour* needs fixing behind an average. And it is produced by a judge whose accuracy nobody has measured.

**A wrong tile-bounce costs one phone call. A wrong conduct score costs a person's standing with their employer.** The stakes rise when the subject is a person, so the caution rises too.

### 8.2 The split

| **Objective** — *did the words happen?* Verifiable from a transcript. **Auto-recorded.** | **Interpretive** — *what did it sound like?* |
|---|---|
| `no_identification` | `rude_or_curt` |
| `no_closing` | `talked_over_patient` |
| `script_not_followed` | |
| `unauthorised_promise` | |

**The interpretive column is a machine inferring tone from a Hindi transcript, sometimes over poor audio. Brusque telephone Hindi is not rudeness.** These are raised as a card. **The doctor listens. His confirmation writes the record.** Never counted as fact until then. *Machine proposes, doctor disposes — and here it matters more, not less.*

### 8.3 Per-flag applicability, hard-coded

**You cannot follow a script at a voicemail.**

No conduct assessment on: `no_answer`, `busy`, `unreachable`, `call_failed`, `voicemail`, `ivr_or_bot`, `answered_silent`, `call_dropped`, `audio_unusable`, `language_barrier`, `patient_deceased`.

**Applicability is per flag, not per call.** On a `wrong_number`: *did you say which clinic was calling* **still applies**; *did you follow the follow-up script* **does not**.

### 8.4 What gets reported

**The default report names nobody:**

> *This week: the clinic identified itself on 46 of 52 calls. The next step was confirmed on 31 of 52.*

That is standardization. It tells the doctor what to fix on Monday. It creates no league table.

**Denominator honesty (D179):** *21 of 52* — **never a bare 21.**

**The per-agent view exists and is doctor-only**, behind the same `dashRole_ === 'full'` gate as the escalations. It is opened when there is a reason, not displayed as a scoreboard.

**Not in the daily summary email.** An email is a document that leaves the system and can be forwarded.

### 8.5 The training pack **[LATER — gated on §8.7]**

Most of it exists. **D155** already renders *"the FULL TRANSCRIPT in a collapsed row-group with the AI's evidence excerpt highlighted in place."* **D152** already joins the **Recording Link** into every `Call_Verdicts` row.

What is new is the **re-grouping: by behaviour, not by call.**

> **Closing not confirmed — 21 of 52 calls this week.**
> Here are five. Last twenty seconds highlighted. Press play.

For a one-to-one, the same pack filtered to that agent's own calls. **A person can be coached on their own recordings. A group cannot be coached on someone else's.**

**Two guardrails:**
- **Play, don't export.** The pack renders on screen. It does not become a file carrying patients' voices out of the clinic.
- **Coach with the recording, not the number.** Thirty seconds of an agent's own call changes behaviour. A score produces defensiveness and gaming.

### 8.6 The owner's impression is a hypothesis, not a finding

> *"conduct is good · script is strictly not followed · closing is weakest"*

Both stated problems sit in the **objective** column — the half a machine can verify without judging tone. The **interpretive** half, the risky one, is the half the owner says is already fine. **That is a better position than expected.**

**But it is an impression, and it has D190's exact shape:** a human explanation of a gap, relied upon before the artefact was checked. *"Staff never file incoming outcomes"* felt true for months.

**The pack's first job is to test these three sentences, not to assume them.** If conduct proves **not** uniformly good, that finding outranks everything else in the pack.

### 8.7 The blocker, stated honestly

The judge can report `script_not_followed` **only if it has been told the script.** It can report `no_closing` **only if a closing has been defined.**

**Neither exists anywhere in this project.**

Both are the owner's to write. **Status: `UNKNOWN` (D166, D199).** The two flags are fully specified above and are **not operable** until they arrive.

**If there is no written script — which *"strictly not followed"* makes a live possibility — then that absence is the finding, and the first fix is a script, not a judge.**

Collected by: `AI_Review_Layer_Decision_Workbook_S131.docx`.

### 8.8 Calibration is separate

Contact calibration (§5.2) does **not** transfer to conduct. Conduct requires its own set: **40 calls the doctor has listened to himself.** Until then the flags are collected **silently** and visible only to him.

### 8.9 Storage — no new writer

| What | Where | Writer |
|---|---|---|
| Contact code, conduct flag **proposals**, evidence, confidence | columns on `Call_Verdicts` | `call_verdict.py` |
| The doctor's **confirmations** and referee decisions | `Doctor_Verdicts` | the dashboard (D193) |

**A provenance column is required (`staff` vs `machine`) — and it must NOT be named `Source`.** `FU_OUTCOME_HEADERS` already carries a `Source` column, used for *source-on-medication*. Reusing the name would be **D178** in a single word.

---

## §9 — LIVE, NOT BATCH (D200) **[LATER]**

**There is no lag to measure.**

- `MyOperator_Call_API_Master_Reference` **§9.1**: both `call.end` and `call.summary` carry **`recording_filename`** in `payload`.
- **§6**: `/recordings/link?file=…` returns a fresh link valid 24 h; *"recordings themselves persist on MyOperator's cloud indefinitely; only the link expires."*
- `call_hook_capture.py` **L183–186**: `HEADER` for `Call_Durations` **already contains `recording_filename`**. **L408** reads it out of the `call.end` payload. **It is written to the sheet in real time, at hangup.**

**The 02:00 archive and the 03:00 transcription are batch by choice, not by necessity.**

Going live means **one thing**: transcribe on demand shortly after hangup instead of at 03:00 on yesterday's pile. A **fetch-with-backoff** (try; on empty, retry in 60 s, up to N) makes the file-availability delay irrelevant to correctness. **Worth recording for `Health.gs` lag budgets. Not worth waiting for.**

### The blocker

`call_hook_capture.py` **L385**:

```python
if category != "obd" or not client_ref_id:
    return None
```

**Every incoming call, and every outgoing call not dialled from the console, is discarded at the door — `recording_filename` and all.** → **F-19**.

Block D's first line (*"receiver stops discarding incoming calls"*) is a **prerequisite** for any live incoming verdict.

---

## §10 — BUILD ORDER

| # | Item | § | Tag | Files | D34? |
|---|---|---|---|---|---|
| 0 | Owner supplies **call script** + **closing definition** | 8.7 | **GATE** | — | — |
| 0 | Owner answers the **D34 question** | 6 | **GATE** | — | — |
| 1 | **F-8 Fix B** | 1.3 | NOW | `Dashboard.html` | **no** |
| 2 | **`Do_Not_Call` tab** | 7 | NOW | new tab · `push_followups_today.py` | **no** |
| 3 | **F-18** — stop excusing incoming calls | 5.5 | NOW | `verdict_review.py` | **no** |
| 4 | A-3: the other two wrong client catches (L1364, L1128) | — | NOW | `Dashboard.html` | **no** |
| 5 | A-5: close `removeTriggers` / `removeHealthTrigger` | — | NOW | `Main.gs` · `Health.gs` | **no** |
| 6 | Stable case identity | 3 | NOW | `WebApp.gs` · `call_verdict.py` | **yes** |
| 7 | Tile-removal contract | 2 | NOW | `WebApp.gs` · `Dashboard.html` | **yes** |
| 8 | `AUDIT_SHEET_ID` + writer flip | 5.4 | NOW | property · `WebApp.gs` · `verdict_review.py` | **yes** |
| 9 | Axis 1 + Axis 3 columns, inert | 4 · 8.9 | **PROVISION** | `Call_Verdicts` | no |
| 10 | Doctor's review section, **Phase 1** | 5.2 | NOW | `Dashboard.html` · `WebApp.gs` | **yes** |
| 11 | Conduct reporting | 8.4 | LATER | — | — |
| 12 | Training pack | 8.5 | LATER | — | — |
| 13 | F-19 — receiver stops discarding incoming | 9 | LATER | `call_hook_capture.py` | no |
| 14 | Live transcription | 9 | LATER | Stage 2 | no |
| 15 | **Phase 2** auto-bounce | 5.2 | LATER | — | — |

**Items 1–5 ship without any D34 waiver.** If the owner refuses §6, that is the whole build, and it is still worth doing: F-8 dies, a bereaved family stops being called, and the verdict layer stops lying about incoming calls.

---

## §11 — WHAT THIS SPECIFICATION DOES NOT DO

- It does not fix anything. **An audit finds; it does not fix (D180).**
- It does not let a machine move a tile. **Not in Phase 1, and not until 100 refereed cards say otherwise.**
- It does not let the judge see who made the call. **D198 is a rule, not a convention. It dies the moment somebody adds the agent name to the prompt "for context."**
- It does not score a person.
- It does not export a patient's voice.

**Nothing here is built. Nothing here is live.**

---

**END OF SPECIFICATION v1.1 — §11 is the last section. If §11 is absent, this file is truncated.**
