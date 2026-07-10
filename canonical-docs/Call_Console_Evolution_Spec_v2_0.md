# CALL CONSOLE EVOLUTION SPEC — v2.0 (CONSOLIDATED, SELF-CONTAINED)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Consolidated 09 July 2026, Session 131. Supersedes v1.1 – v1.6 entirely. There is no delta chain.**

> **This is a single, fully self-contained master.** Every section of every prior version is
> reproduced **verbatim** below — not summarised, not paraphrased. The **S100 policy** ("single
> file, no delta chain") is now applied to this document, thirty sessions after it was applied to
> the Master KB.
>
> **Why this document had to be rebuilt.** From Session 51 to Session 124 this spec was maintained
> as a chain of six delta files. Five of the six were never committed to git and never reached
> Google Drive. Project knowledge held **only v1.6 — a two-section fragment (§J, §K)** whose first
> sentence points the reader at *"§G, D77/D82"*, a section that existed nowhere anybody could
> reach. In Session 131 the missing files were recovered from cold-backup zips on the owner's PC.
> **Nothing was lost — but only because a backup had been made after every session for four months.**

---

## §0 — PROVENANCE

Every source file was verified by md5 before transplant. Two independent copies of v1.5 (Session 57
and Session 67 cold kits) and the Google Drive copy agree byte-for-byte.

| Source | Sections | Bytes | md5 | Recovered from |
|---|---|---|---|---|
| v1.1 (Session 25) | §1 – §12 | 28,073 | `8e4ac33d…` | git `docs/` + cold kit |
| v1.2 (Session 51) | **§A §B §C** | 4,229 | `3bb27fe1…` | `DrManoj_Clinic_FULL_Handoff_Session51_2026-07-03.zip` |
| v1.3 (Session 53) | **§D §E §F** | 4,768 | `4c063486…` | `DrManoj_Clinic_ColdKit_Session53_2026-07-03.zip` |
| v1.4 (Session 54) | **§G** | 5,313 | `bae684ed…` | `S54-55_cold_kit.zip` |
| v1.5 (Session 57) | **§H §I** | 4,742 | `9ef6ac27…` | `Session57_ColdBackup_Docs.zip` · `COLD_KIT_Session67` · Drive |
| v1.6 (Session 124) | **§J §K** | 8,025 | `aaf7d455…` | project knowledge + git |

### How to read the two section schemes

**They are not renumbered, deliberately.** v1.1 numbers its sections `§1 … §12` and cross-references
them internally (`§4.4`, `§7.5`, `§8.3`). The as-built chain letters its sections `§A … §K`.
Renumbering either would silently break every internal cross-reference in a document that records
shipped behaviour. **Both schemes are preserved and clearly parted.**

- **PART I (§1 – §11)** — the original design. Where PART II describes shipped behaviour, **PART II
  is authoritative over PART I.**
- **PART II (§A – §K)** — what was actually built, session by session.

### Supersession inside PART II

| Section | Status |
|---|---|
| **§E** — duration gate, DESIGN (D77) | **SUPERSEDED by §G** (D82, as built). Kept as the record of intent. |
| **§G.4** — tile flow (v18.16) | **AMENDED by §J** (D156, v18.19 — the gate now fails open). |
| §A's *"3rd attempt → tile leaves the staff list entirely"* | **SUPERSEDED by §F** (D78 — it drops to a bottom band instead). §F was designed and **never built**. |

### Decisions this document defines, and the KB does not

**D62, D66, D68, D69, D77, D78, D80, D81, D82, D97, D98.**

The Master KB's decisions index has never covered `D1–D120`. **D68, D78, D80 and D81 appear nowhere
in any version of the KB.** D77 and D82 appear only inside D156's phrase *"amends D77/D82"* — the KB
amends decisions it does not contain. Recorded as **F-22**; backfilled into KB v1.56 from this file.

---

# PART I — THE ORIGINAL DESIGN (Session 25, v1.1)

> Where PART II describes shipped behaviour, PART II is authoritative over everything below.

## 1. The problem this solves

Staff currently operate across three disconnected tools:

| Tool | Purpose | Friction |
|---|---|---|
| MyOperator dialer panel | Place and receive calls | Separate screen, no patient context |
| Excel sheet | Log call outcomes | Manual typing, no pre-population, quality unreliable |
| Staff Action Today sheet | Daily follow-up worklist | Separate file, printed or opened on PC, no direct calling |

Every call requires mental context-switching between at least two of these. Outcome
quality degrades because logging feels like a separate task after the work is already
done. Patient context (name, diagnosis, last visit) has to be recalled or looked up
manually.

**The goal:** one screen, always open, that is the natural consequence of doing the
work. Tapping to call. Tapping to log. Everything else automatic.

---

## 2. Design principles (specific to this console)

These extend the Umbrella Architecture's core principles for this module:

1. **The screen is the job, not a record of the job.** Outcome capture is a natural
   consequence of the call workflow, not a separate administrative step.

2. **Context arrives before the conversation starts.** Patient name, Clinic ID,
   diagnosis, and last visit are on screen before staff speak.

3. **One list, one screen, one tap to call.** All calls to make today are in one place.

4. **The fallback is always one tap away.** If OBD fails, `tel:` fires the phone. If
   the dashboard is down, the manual flow is unchanged and on the wall card.

5. **No outcome is ever lost.** A call arriving before the previous outcome is logged
   holds the pending outcome in a visible tray, never silently discarded.

6. **Identity is automatic.** Agent name, extension, timestamp come from the login
   key — never typed.

7. **★ (New in v1.1) Doctor-only surfaces stay doctor-only.** Transcripts, patient
   review notes, and the doctor's escalation queue are never rendered to a staff
   login, under any tab, at any stage. Staff surfaces carry only what staff need to
   act. (Recording link, diagnosis, and last-visit ARE allowed on the staff console —
   see §4 and C16; transcript is NOT.)

---

## 3. The screen anatomy (staff console)

```
┌──────────────────────────────────────────────────────────────┐
│  TOP BAR                                                       │
│  [Clinic logo / name]           👤 Shivani · Ext 12           │
│  Last updated 10:42:31  [↺ Refresh]   Build v15               │
├──────────────────────────────────────────────────────────────┤
│  KPI TILES                                                     │
│  Total calls · Incoming missed · Awaiting callback ·          │
│  Follow-ups due · WhatsApp unread                              │
├──────────────────────────────────────────────────────────────┤
│  ⚠ PENDING OUTCOMES TRAY  [2 outcomes not yet logged]         │  ← yellow, only when needed
├──────────────────────────────────────────────────────────────┤
│  📞 TODAY'S CALLS  (live stream, newest first)                │
│  Each row: Time · ▼IN/▲OUT · Name · Clinic ID · Diagnosis ·   │
│            Last visit · Agent · Duration · Status · 🎧 Rec     │
│  New call since last poll → orange pulse 3 sec                 │
│                                        [↑ Back to top]         │
├──────────────────────────────────────────────────────────────┤
│  🔴 CALLBACKS NEEDED  (missed, unresolved)                     │
│  [+ Dial new number ▼]                                        │
│  Each row: caller · name · Clinic ID · Diagnosis · Last visit │
│            · 🎧 Rec · Call button · outcome form              │
│                                        [↑ Back to top]         │
├──────────────────────────────────────────────────────────────┤
│  📋 TODAY'S FOLLOW-UPS  (named patients — separate section)   │
│  Each row: Name · Clinic ID · Diagnosis · Last visit · Due ·  │
│            🎧 Rec · Call button · outcome form                │
│                                        [↑ Back to top]         │
├──────────────────────────────────────────────────────────────┤
│  🚩 FLAGGED BY DOCTOR  (New in v1.1 — see §8)                 │
│  Separate top-level tab, NOT mixed into Follow-ups            │
│  Each row: caller name · date of call · IN/OUT · 🎧 Rec ·     │
│            last visit · last medicine refill ·               │
│            staff RESPONSE field + Submit                      │
│  Submit → row disappears immediately                          │
│                                        [↑ Back to top]         │
├──────────────────────────────────────────────────────────────┤
│  💬 WHATSAPP  (recent messages)                               │
│  Each row: Name · last message · time · 📞 Call button        │
│                                        [↑ Back to top]        │
└──────────────────────────────────────────────────────────────┘
                    [▲ floating back-to-top, always visible]
```

**Doctor's private screen (separate login, separate layout) is in §7 — not part of
the staff console above.**

---

## 4. Section-by-section specification (staff console)

### 4.1 Top bar
- **Agent identity badge** — server-side from `AKEY_<ext>`, never the page. Displays
  `👤 [Name] · Ext [N]` (name only on mobile).
- **Build stamp** — shows the deployed build (v15 after this build) so staff can
  confirm they're on the latest version.

### 4.2 KPI tiles
No change from v14 except: add **Follow-ups due** tile; tiles are tappable and scroll
to their section.

### 4.3 Pending outcomes tray
Yellow banner below the KPI tiles when a call was expanded but not saved before the
next poll. `⚠ [N] outcome(s) not yet logged`. Tapping expands the unsaved calls with
inline outcome forms. Clears as outcomes save. Visual only, no sound.

### 4.4 Today's calls (live stream)
**Data source:** `allCallsToday_()` — reuses `fetchCallsBetween_()`, all calls both
directions, newest-first. **Poll:** 30 seconds.

**Each row shows:** Time · direction badge (`▼ IN` green / `▲ OUT` blue) · patient
name or "Unknown" · Clinic ID (`ID 1234`, replaces "UID") · **diagnosis** ·
**last-visit date** · agent · duration · status badge · **🎧 recording button**.

- **★ v1.1 — persistent context fields.** Diagnosis and last-visit come from
  Patient_Master and show immediately on every known-patient row. Last-visit is a
  **plain date, no badge** — decision-support, not a status light.
- **★ v1.1 — recording button, two sources with a clear priority.** For **outcome
  review** (staff response + doctor review), the **permanent Drive archive link**
  (Stage 1) is the primary source, because review is often not same-day. A call's Drive
  link exists **from the next day onward** (after the 02:00 archive run) and never
  expires. For a call being listened to **the same day it happened** — before that
  night's archive — the button falls back to the existing **MyOperator on-demand
  player** (System A, `GET /recordings/link?file=<filename>.mp3`, link valid ~24h),
  which the live v14 dashboard already uses. **Rule: show the Drive link if it exists;
  else use the MyOperator player.** This guarantees a working recording whether the
  call is reviewed today, tomorrow, or weeks later. (A later backlog item — per-call
  download instead of the nightly batch — makes the Drive link appear within minutes,
  closing the same-day gap entirely.)

**New-call detection:** IDs compared each poll; new ones get a 3-sec orange pulse.
Visual only.

**Tap to expand:** opens patient card + outcome form inline. Known patient → reason +
resolution dropdowns; unknown → identity flow. Outcome dropdown uses explicit dark
text (#1d2733) on white (fixes the contrast bug). Saved → card collapses, row gets ✓,
stays in the stream.

### 4.5 Callbacks needed (missed, unresolved)
No structural change from v14. Adds:
- **Embedded number pad** — `[+ Dial new number]` expands a 12-key pad; live
  Patient_Master lookup as digits are typed; `Call` fires OBD; outcome captured in the
  live stream after.
- **★ v1.1 — persistent context fields:** diagnosis, last-visit, and the recording
  button (same MyOperator on-demand player as §4.4) show on each row.
- "UID" → "Clinic ID" (label only).

### 4.6 Today's follow-ups (separate section)
**Visual distinction:** teal/green header vs the red Callbacks header.
**Data source:** `Followups_Today` tab (loaded by `push_followups_today.py` each
morning; data contract unchanged).

**★ v1.1 — persistent context fields:** diagnosis (already present), plus last-visit
and the recording button now show on each row too (MyOperator on-demand player, §4.4).

**Row behaviour after outcome:**

| Outcome code | Row behaviour |
|---|---|
| `coming` / `out_of_town` / `on_medication` | Disappears from list |
| `not_interested` / `treatment_elsewhere` | Disappears |
| `dikha_chuke` | Disappears from staff list; escalates to doctor |
| `problem` | Disappears from staff list; escalates to doctor |
| `close_followup` | Disappears from staff list; escalates to doctor |
| `cant_communicate` | Stays — retry tag + attempt count |
| No answer / busy | Stays — attempt count |

**★ v1.1 fix — no more double-appearance.** Escalating outcomes (`dikha_chuke`,
`problem`, `close_followup`) currently leak into BOTH the regular Follow-ups list and
a top tab, because they have no dedicated home. From v1.1 an escalating outcome simply
**leaves** the staff Follow-ups list on logging and goes to the **doctor's** Pending
group (§7). It only comes *back* to staff if the doctor explicitly **flags** it — and
then it appears **only** in the new Flagged Calls tab (§8), never again in Follow-ups.

**Write-back:** outcome → `Followup_Outcomes` sheet (unchanged) + dashboard hide.
Next-morning re-push does not restore settled rows. "UID" → "Clinic ID".

### 4.7 WhatsApp section
No structural change. `📞 Call` on each row → confirmation tooltip `Call 98XX-XXXX6?`
→ second tap fires OBD → call appears in Live Calls; outcome captured there. Two taps
prevent accidental dial.

### 4.8 Floating back-to-top
A `▲` fixed bottom-right, visible after scrolling past the KPI tiles, smooth-scroll to
top; section-level `[↑ Back to top]` links at the bottom of each section. **★ v1.1:**
the same button is reused unchanged on the doctor's private screen (§7).

---

## 5. Outcome dropdown fix (applies everywhere)

**Root cause:** `<option>` elements inheriting a background matching the text colour →
invisible until selected.
**Fix:** explicit CSS on all `<select>`/`<option>`:
```css
select { color: #1d2733; background: #ffffff; }
select option { color: #1d2733; background: #ffffff; }
```
Applied globally. **Tap target:** `pointer-events` set so only the field + its arrow
trigger the dropdown, not the surrounding card.

---

## 6. Data changes

### `allCallsToday_()`  (new server function)
All calls today, both directions, enriched, newest-first. Reuses
`fetchCallsBetween_()` — no new API call. Adds `isNew` flag + Patient_Master lookup
(name, Clinic ID, **diagnosis, last-visit**).

### `getAgentIdentity_(key)`  (new server function)
`{ name, ext }` for the logged-in agent from the `Agents` tab. Used by the badge +
outcome logging.

### `Outcomes_Log`  (new sheet tab)
**Writer:** dashboard only. Columns:
```
Timestamp | Agent Name | Ext | Direction | Number (last-4) |
Patient Name | Clinic ID | Outcome | Notes | Call Duration | Recording filename
```
Permanent activity record. Staff never open or edit it.

### `getDashboardData` return object
Adds `allCalls[]` alongside existing arrays. Purely additive.

### ★ `Flagged_Queue`, `Flagged_Calls_Archive`  (new sheet tabs — LOCKED, C18/§8.3)
Both additive; no existing tab changes. See §8.3.

### ★ Recording link source (existing, reused)
The `Call_Recordings` manifest tab (Stage 1 archive) is the source for every 🎧 button
on the staff console and the doctor screen. Nightly-archive timing caveat applies
(§4.4).

### ★ "Last medicine refill" (deferred data source)
Comes from the not-yet-built pharmacy sale billing Excel. Spec'd now as a UI
placeholder ("Not available yet"); wired up when that system exists.

---

## 7. ★ NEW (v1.1) — Doctor's Escalation / Resolve screen

**Access:** doctor login only, gated as the existing Escalations view is today (role
check via `dashRole_`). Never reachable from a staff login, any URL, any tab, any
state.

**Why this section exists:** the doctor's Session-25 feedback — the current Resolve
click only *dims* the row, which is not a reliable signal it saved; plus new context
fields; plus a clear statement of why an unresolved item reappears (it's a to-do list,
§7.1).

### 7.1 The core rule: every escalation is MANUAL resolve
There is **no automatic reconciliation.** Every escalation that reaches the doctor —
`dikha_chuke`, `problem`, `close_followup`, and the incoming urgent path
(surgery/fracture/accident/severe pain, D10) — sits in **Pending** until the **doctor
clicks Resolve.** Nothing clears itself.

- **This is why an unresolved item reappears every day** — it's the doctor's to-do
  list, not a self-clearing log. Working as designed.
- The **last-visit date** shown on a `dikha_chuke` card (and to staff, §8) is
  **decision-support only** — it helps the doctor judge "recent enough?" at a glance.
  It does **not** auto-resolve anything. Plain date, no badge.

### 7.2 Two visible groups (dropdowns)
| Group | Contents | Behaviour |
|---|---|---|
| **Pending** | All escalations with Status = `OPEN` | Stays until the doctor clicks Resolve. Never shown to staff. |
| **Flagged by me** | Escalations the doctor has explicitly flagged (§7.4) | Stays until staff respond and the doctor archives (§7.5). |

**Resolved items are not a visible group** — clicking Resolve makes the item leave the
dashboard (see §7.3). Nothing to browse; it's simply gone from the active list.

### 7.3 Card fields + the Resolve action
Every Pending / Flagged card shows (doctor-view only): patient name + Clinic ID ·
last-visit date · last medicine refill ("Not available yet" until pharmacy system) ·
🎧 recording link (from Stage 1 archive) · **transcript as an expandable dropdown**
(Stage 2, doctor-only) · an open remark field (free text) · a **Resolve** button.

**Resolve confirmation (the fix):** clicking Resolve shows an immediate green
checkmark + "Resolved" overlay on the card (~1 second), then the card leaves the
Pending group and clears from the dashboard. Resolve writes `Resolution` +
`Resolved When` to the Escalations sheet (columns already exist, currently blank).

**Flag is a separate action from Resolve** — flagging does not resolve; it opens the
staff path (§7.4).

### 7.4 Flagging an item
The doctor flags instead of / before resolving. Flagging moves the item into
**Flagged by me** on the doctor's side AND creates the matching staff-side card (§8).
The doctor still sees the full card (recording + transcript + remark); flagging changes
what **staff** can see (§8), not what the doctor sees.

### 7.5 Doctor's final review (after staff responds)
When staff submit (§8), the staff card disappears and a **response-ready** marker
appears on the doctor's Flagged-by-me card. The review card then shows: 🎧 recording
(**permanent Drive archive link** — reliable for next-day-or-later review; §4.4) ·
transcript dropdown · last medicine refill · **staff's response text** · a free-text
**review notes** field. An **Archive** button writes the full record (§8.3 columns) to
`Flagged_Calls_Archive` with the doctor's review note, and removes the item from the
active Flagged-by-me group.

### 7.6 Scroll-to-top
Same floating `▲` as the staff console (§4.8).

---

## 8. ★ NEW (v1.1) — Staff-side Flagged Calls tab

**Why a separate tab, not part of Follow-ups Due:** a doctor-flagged item needs a
written response routed back to the doctor — not a routine follow-up cleared by a
normal outcome dropdown. Today, with no dedicated home, these show in BOTH the
Follow-ups list and a top tab (the duplication the doctor reported). A dedicated
top-level tab removes the duplication and signals "this needs a written reply."

### 8.1 What staff see, per card
- Caller name
- Date of call
- Direction: incoming / outgoing
- 🎧 Call recording — the **permanent Drive archive link** is the primary source for
  review (reliable from the next day onward, never expires), so staff can listen before
  writing their response whether that's the same day or later. For a call being handled
  the **same day** it happened (before that night's archive), the button falls back to
  the MyOperator same-day player. Rule + detail in §4.4.
- Date of last visit
- Date of last medicine refill ("Not available yet" until pharmacy system)
- A free-text **response** field + Submit

**Never shown to staff — here or anywhere:** the **transcript.** This holds regardless
of which doctor-side group the item is in. Transcript = doctor-only, full stop.

### 8.2 Submit behaviour
Staff type their response and tap Submit → the card **disappears from the staff Flagged
tab immediately** (instant confirmation the reply went through) → the response routes
to the doctor's review queue (§7.5).

### 8.3 Data design (LOCKED this session — C18)
- **`Flagged_Queue`** (new tab): `Key` (ties to the Escalations row) · `Flagged When`
  · `Flagged By` · `Staff Response` · `Staff Responded When` · `Status`
  (`awaiting_staff` / `awaiting_doctor_review` / `archived`).
- **`Flagged_Calls_Archive`** (new tab, written only on the doctor's Archive click):
  `Archived Date` · patient/caller identity · call date/direction · recording link ·
  transcript link · staff response · doctor review note · archived by · archived when.
- Both additive; no existing tab structure changes.

---

## 9. Build plan

| Step | File | What changes | Prerequisite |
|---|---|---|---|
| 1 | `WebApp.gs` | `allCallsToday_()`, `getAgentIdentity_()`, `logOutcome_()`, `Outcomes_Log` writer, diagnosis/last-visit in patient lookup | None |
| 2 | `Dashboard.html` | Staff UI rebuild — sections, badge, live stream, number pad, WA call button, dropdown fix, back-to-top, pending tray, persistent context fields (diagnosis/last-visit/🎧) | Step 1 |
| 3 ★ | New doctor-only file (e.g. `EscalationConsole.gs` + HTML) | Pending + Flagged-by-me groups, card fields, animated Resolve, Flag action, transcript dropdown | Steps 1–2 |
| 4 ★ | `Dashboard.html` (staff) + `Flagged_Queue` writer | Flagged Calls tab, Submit-and-disappear, routing to doctor review | Step 3 |

**Not changing:** `MyOperator.gs` · `config.gs` · `CallField.gs.gs` · `Probe.gs.gs` ·
any VPS file · any existing sheet tab (additive only).

**Deployment rule (D12):** after any `Dashboard.html` change → edit existing deployment
→ New version. Never a new deployment (new URL breaks staff bookmarks).

**Build currentness:** live build is **v14**; this rebuild publishes as **v15**.

**Status:** Steps 1–4 are **design only** in this document. No build starts until the
doctor gives explicit go-ahead. Agreed in Session 25: **build in the NEXT session**,
with this spec frozen.

---

## 10. Testing checklist (before going live)

- [ ] Agent badge shows correct name + ext for each `AKEY_`
- [ ] Live calls populate within 30 s of a test call; new-call pulse fires
- [ ] Outcome dropdown options visible (dark on white) before selection
- [ ] Outcome saves to `Outcomes_Log` with correct agent + timestamp
- [ ] Pending outcomes tray appears when a card is left open during next poll
- [ ] Follow-up row disappears after settling outcome, stays after retry outcome
- [ ] WA call button fires OBD with two-tap confirmation
- [ ] Number pad expands, patient lookup runs as digits typed
- [ ] "Clinic ID" shows (not UID) everywhere
- [ ] Back-to-top works on mobile (portrait)
- [ ] ★ Diagnosis + last-visit show on live-call, callback, and follow-up rows
- [ ] ★ Review shows the permanent Drive archive link once it exists (next day onward);
      a same-day call falls back to the MyOperator on-demand player
- [ ] ★ Doctor's Escalation screen unreachable from any staff login
- [ ] ★ Resolve click shows the checkmark confirmation, not just a dim state
- [ ] ★ Pending group never appears anywhere on the staff dashboard
- [ ] ★ Resolved items clear from the doctor dashboard on the Resolve click
- [ ] ★ Flagging creates exactly one staff-side card AND removes the item from the
      regular Follow-ups list (no duplication)
- [ ] ★ Staff Flagged tab never shows a transcript, under any condition
- [ ] ★ Staff Flagged tab DOES show recording link, last visit, last medicine refill
- [ ] ★ Staff Submit removes the card from staff's view immediately
- [ ] ★ Doctor's review card shows staff's response + all doctor-only fields
- [ ] ★ Archive writes to `Flagged_Calls_Archive` with the doctor's review note and
      clears the item from the active dashboard
- [ ] No regression in existing sections; fallback `tel:` links present behind every
      OBD button

---

## 11. Decisions locked for this spec

| # | Decision |
|---|---|
| C1 | Poll cadence = 30 seconds (not webhook). |
| C2 | New-call notification = visual pulse only, no sound. |
| C3 | Follow-up write-back = `Followup_Outcomes` sheet + dashboard hide; sheet is source of truth. |
| C4 | WhatsApp call button = fire OBD, let call appear in Live Calls; no separate WA log. |
| C5 | Agent identity badge = top-right of top bar, all screen sizes. |
| C6 | Pending outcomes tray = yellow banner, badge count, inline forms. |
| C7 | Number pad = inside Callbacks header, expandable, live patient lookup. |
| C8 | Outcome dropdown fix = global CSS. |
| C9 | `Outcomes_Log` = the permanent Excel replacement; dashboard sole writer. |
| C10 | "Clinic ID" replaces "UID" in UI labels; underlying field unchanged. |
| C11 ★ | Doctor's Escalation screen is a fully separate, private surface — never merged, never reachable from a staff login. |
| C12 ★ | Doctor screen has two visible dropdown groups: Pending and Flagged by me. Resolved items simply leave the dashboard. |
| C13 ★ | Every escalation is MANUAL resolve — no auto-reconciliation for any outcome. The doctor's click is the sole authority. |
| C14 ★ | Last-visit date on a card is decision-support only (plain date, no badge); it does not auto-resolve anything. |
| C15 ★ | "Last medicine refill" is sourced from the not-yet-built pharmacy sale billing Excel — spec'd now as a placeholder, wired later. |
| C16 ★ | Staff console persistently shows recording link, diagnosis, and last-visit across live-call / callback / follow-up rows AND the Flagged tab — but NEVER the transcript. |
| C17 ★ | Flagged Calls get their own top-level staff tab, separate from Follow-ups Due — fixes the current duplication. |
| C18 ★ | Staff Submit removes the card immediately and routes to the doctor's review queue; the doctor's Archive click writes the full record + review note to `Flagged_Calls_Archive`. `Flagged_Queue` + `Flagged_Calls_Archive` are the two new additive tabs. |
| C19 ★ | **Outcome review uses the permanent Drive archive link as the primary recording source**, because review often isn't same-day. A call's Drive link exists from the next day onward (after the 02:00 Stage-1 run) and never expires — reliable for staff response and doctor review any day later. The MyOperator on-demand player (System A, `/recordings/link`, ~24h validity) is used only as the **same-day** option, for a call being listened to the day it happened. Rule: show the Drive link if it exists; else fall back to the MyOperator player. (Later backlog item — per-call download — makes the Drive link appear within minutes, closing the same-day gap.) |

---


---

# PART II — AS BUILT, SESSION BY SESSION

## §A — Missed-call binding, AS BUILT (v18.4; D68; Execution-Plan Builds 2A + 2B)

**Staff side (2A).** Each follow-up tile has a **"No answer"** button beside Call. Tapping it writes a `no_answer` row to `Followup_Outcomes` (the single write-log — no new sheet). `fuTodaysOutcomeState_` counts today's `no_answer` rows per patient; `getFollowups` then:
- **1–2 attempts, last < 60 min ago** → tile is **snoozed**: greyed, "⏳ No answer — retry after HH:MM · try N/3", Call + dropdown disabled; **auto-wakes** on the next poll after 60 min.
- **3rd attempt** → tile **leaves the staff list** entirely.
- Connected calls are unchanged: staff pick a normal outcome and Save.

**Owner correction to v1.1 / the Execution Plan (D68):** a missed tile carries **only** the No-answer path. **"Wrong number"** and **"Asked not to call"** are **connected-call** outcomes (added to the dropdown, routed to the doctor as escalations) — they can only be known once a call connects, so they are never actions on a missed tile.

**Doctor side (2B).** Patients at 3 strikes appear in a new doctor-only **"Unreachable — review"** band (open by default) carrying attempt history (times · agent) and one-tap **Retry tomorrow / Pause / Remove**. Each action writes a settling code to `Followup_Outcomes` and the tile leaves both lists for the day.

**Deferred (not in v18.4):** the cross-day "Day 2 of 3" retry cap; permanent suppression of Pause/Remove (waits on D59); the automatic WhatsApp nudge on the 3rd miss (Execution-Plan Build 5); and the D66 "vanish-on-file + 10-s UNDO + Aaj-ke-completed counter" (Build 4b). "Couldn't communicate" remains a live fallback.

## §B — Doctor Escalations card, AS BUILT (v18.5 → v18.8; D69)

The Escalations card is a **live read**, not a filing snapshot:
- **Identity filled live** from `cc_patientMap_` by mobile — clinic ID, diagnosis, last-visit fill from the current patient record even if they were blank at filing time.
- **Layout:** reason → name + ID → `Last visit · diagnosis · 📞 mobile` → call-status line → `Outcome <agent> · <time, date>` → 🎧 Recording · 📄 Transcript.
- **Call matched** to the escalation (before-preferring, 30-min after-grace) to attach **call time + duration**, the **recording** (MyOperator same-day link → Drive archive later), and the **transcript** (from the next morning, after the 03:00 job). Agent name prefers the matched call's log; a shared reception login falls back to "Staff".
- **Explicit call status** on every card: connected (show details) · **📵 Missed call — no recording** · **— No call recorded for this patient** · **— No recording archived for this call**.
- **Transcript folds manually** — loads once, stays open across the auto-refresh, closes only on tap.

**Known open (next session):** the call-status line shows call **time + duration** but not the call **date** — to be added.

## §C — Helpers touched / added (reference)

- `WebApp.gs`: `no_answer` handling in `fuTodaysOutcomeState_`; snooze/3-strike + `unreachable` list in `getFollowups`; `wrong_number`/`asked_not_to_call` escalating codes; `getEscalations` live-enrichment + `escPick_` (before-preferring matcher) + call-status.
- `OutcomeLog.gs`: agent field on today-call records; `OL_todayCallsAndMissed_()` (connected + missed in one feed pass).
- `Dashboard.html`: No-answer button + snooze render; `renderUnreachable`/`unreachAction`; escalation-card rebuild + manual-fold `escTx`.

## §D — Vanish-on-file, AS BUILT (v18.15; D66)

- **On Save of a completing/escalating outcome:** the tile is **removed immediately**; the write is **held 10 seconds**; a bottom **UNDO** toast counts down.
- **UNDO within 10s:** tile returns exactly as it was, counter reverts, **nothing is written**. If the page closes / signal drops in the window, the write never fires and the patient **re-surfaces on the next poll** — the safe failure (never a fake "done").
- **Section-wise progress header** at the top of the follow-up card: `Today's follow-up calls — total N / (N−x) done`, a line per band (Due Today, Grace Period, …), and a timestamp. Driven by server `counts` (open + settled) plus a new **additive** `sectionDone` per-band count in `getFollowups`. Sent-back band counts in the overall total but has no breakdown line.
- **Retry outcome exception:** only **"Connected but couldn't communicate"** stays on the list (mirrors `WebApp.gs` `FU_SETTLING` + `FU_ESCALATING`); every other outcome vanishes.
- Surface: `Dashboard.html` only + the additive `getFollowups` field. No new writer.

## §E — The DURATION GATE, DESIGN (D77; supersedes the v18.14 self-declared Talked gate; build next)

**Problem:** the v18.14 gate revealed the outcome dropdown after a self-declared **✅ Talked** tap, with **no check the call connected** — so a ring-only call could reach an outcome.

**Fix:** outcome availability is driven by the call's **real duration**, read from the MyOperator **`call.end` webhook** (real-time; the KB's documented alternative to the 30-min-lag poll). No Talked/Missed buttons.

**Tile flow:**
1. Staff taps **Call** (OBD; agent leg first, then patient). The dashboard already receives the call's unique **`reference_id`**.
2. Call ends → the `call.end` webhook (received on the VPS) reports that call's **`duration`** (int seconds), **`status`** (`bridged`/`missed`), and **`ref_id`** (= our `reference_id`).
3. Tile shows **"checking call…"** briefly, then resolves by duration:
   - **< threshold (~10–15s)** → **📵 Missed call · time/date** + **↻ Call again**; **no outcome field.** Counts toward the strike tally.
   - **≥ threshold** → the outcome dropdown appears.
- **Threshold** is a config knob and doubles as a **script-adherence** check (the mandated opening line takes ~10–15s to deliver).
- **Exact-call binding** via `reference_id` — never fuzzy number+time matching.
- **Determined dead-air lies** (line held open with no real conversation) are out of scope for the gate — caught post-hoc by the **AI-verdict layer (D62)**.

**Build shape:** VPS **call-receiver** (same pattern as `wa_receiver.py`) storing `{reference_id → duration, status}` from `call.end`; a new server fn in **`CallConsole.gs`** (per D34) the tile polls after a call; `Dashboard.html` tile logic. Step 1 is **passive capture** of one real `call.end` body to confirm per-account field names (vendor examples are from a sample company) — **no test calls needed.**

## §F — STICKY-ON-STAFF 3-strike, DESIGN (D78; supersedes the v18.4 doctor-only exit; build after the gate)

- A patient at 3 misses **does not leave** the staff worklist — it drops to a distinct **bottom band** ("📵 Sampark nahi ho raha — tried N×"), out of the active-call flow but never hidden.
- **Next day and after:** the patient **reappears in that band with cross-day context** — total tries, last attempt times, WhatsApp-sent date. The **miss count accumulates across days** (no daily reset).
- **3rd strike:** fires the **WABA template** to the patient + **snoozes X days** (pre-decided). Active re-calling wakes on a patient reply, X days elapsing, or a staff "Try again now."
- One-tap staff options, nothing auto-vanishes: **Try again now · Reached another way (settles) · Send to doctor (escalates with context).**
- **Build need:** a **cross-day miss counter** in the worklist assembly (today it's per-day only).

## §G — The DURATION GATE, AS BUILT (v18.16; D82; supersedes the §E design in v1.3)

**Shipped end-to-end in three phases. Outcome availability is now driven by the call's MEASURED result, never a self-declaration.**

### G.1 The pipe (D80)
- New walled-off VPS service **`call-hook.service`** — gunicorn `-w 1` on `127.0.0.1:8098`, public route **`/mo-callhook`** (secret-gated with `?key=`, OLS-proxied via a `context /mo-callhook` block; path chosen to share no prefix with `/call`).
- MyOperator **Webhooks v2 → Add New Webhook → Call Ended (`call.end`) + Call Summary (`call.summary`)** point at it. Additive, separate from the WABA token — no vendor escalation, no token rotation.
- The service raw-logs every body (owner-only `.jsonl`), then **upserts one row** into the one-writer **`Call_Durations`** tab, keyed on **`client_ref_id`** (so call.end + call.summary collapse to one row). **No phone number is written.** Auto-creates the tab, auto-discovers the `patient-mirror` service-account key, connects at startup, and is degrade-safe (raw-log + 200 even if Sheets is down; never retry-storms). **Skips incoming / non-OBD calls.**
- Helper `peek_callhook.py` prints a captured body with the patient number auto-masked.

### G.2 The corrected field mechanics (D81 — from real captured bodies)
- **Join key = `payload.client_ref_id`** — the value our dialer stamps (`make_reference_id` in `call_api.py`) echoes back here. The webhook's **`ref_id` is MyOperator's OWN UUID** — not ours. `session_id` is a backup.
- **Gate signal = the CUSTOMER leg** (`legs[]` where `type == "customer"`): its **`talk_duration`** and **`result`**. Top-level `duration` includes agent pickup + ring time, so it is *not* the signal. The gate requires **`result == "answered"`** — a real call showed `result:"connected"` with `answered_at:null` at 11 talk-seconds (reached, not answered).
- `Call_Durations` columns: `client_ref_id, ref_id, session_id, category, status, total_duration, customer_result, customer_talk_duration, customer_ring_duration, recording_filename, ended_at_ist, captured_at_ist, source_event`.

### G.3 The gate decision (server, one const)
`CallConsole.gs::getCallDuration(key, clientRefId)` (read-only; **WebApp.gs untouched**, D34) returns:
```
allowOutcome = (status == "bridged") AND (customer_result == "answered") AND (customer_talk_duration >= CC_GATE_MIN_TALK)
```
`CC_GATE_MIN_TALK = 15` (seconds). The 15s doubles as the opening-line **script-adherence** check. Any ambiguity or missing field → `allowOutcome:false` (fail-safe).

### G.4 The tile flow (Dashboard.html v18.16)
1. Staff taps **Call** → `fuDoCall` places the OBD call and **captures that call's `reference_id`** (stored per tile, persisted per-day).
2. Tile shows **⏳ "Checking the call… the outcome unlocks once it connects"** and **polls `getCallDuration` every 6s** (fail-safe timeout 3 min).
3. When the `Call_Durations` row appears:
   - **bridged + answered + talk ≥ 15s** → the **outcome dropdown** unfolds (unchanged outcome UI).
   - **missed / not-answered / talk < 15s** → **📵 "Call didn't connect — patient talked Xs (need 15s)"** — no outcome.
   - **no row after 3 min** (webhook hiccup, rare) → **⏳ "Couldn't confirm — Call again"** — no outcome.
4. **Manual fallbacks preserved throughout:** **↻ Call again** and **📵 No answer** stay available in every not-yet-connected state. The self-declared **✅ Talked tap is removed.**
5. **Reload-safe:** a call still awaiting its result resumes polling after any full render (`fuResumePolls`).

### G.5 Scope boundary
- The gate catches **no-call / ring-only / too-short / not-answered** outcomes at the source (Layer 1, prevention).
- **Determined dead-air lies** (line held open, no real conversation) are out of scope for the gate → caught post-hoc by the **AI-verdict layer (D62)**, and flagged nearer-term by the **missed-call fabrication sentinel** over the Call-Logs register (Layer 2, detection).

### G.6 Deferred
- **PHI base swap:** `client_ref_id` currently embeds the patient mobile (the dialer's `reference_id` base = the number). Deferred (the operational sheet already holds mobiles); when done, the gate still matches on the full returned reference_id regardless of base.

## §H — WhatsApp tap-to-call, AS BUILT (D97; v18.17 → v18.17b)

**A second call surface. Same dialer, same gate.**

### H.1 The surface
- The **Recent WhatsApp** feed renders inbound + outbound messages. Each row already carries a clean `m.number` (used by Chat/Reply). Session 57 adds a green **📞 Call** button on **inbound rows only** (`inbound ? …Call… : ''`) — patients we might call back, never our own outgoing entries.

### H.2 The two taps
1. **Tap 1 → `waCall(number, name)`** opens a **custom in-page dialog** (`#waCallOverlay`): title "📞 Call this patient?", the patient's name (if known) + full number with a (…last4) hint, the reassurance line "Your phone rings first, then the patient is connected.", and **[Cancel] [📞 Call]**. Tap-outside cancels. This mirrors the `#threadOverlay` pattern.
2. **Tap 2 (📞 Call) → `waCallGo()` → the existing live `placeCall(number)`** → `triggerCall(DASH_KEY, number, number)`. Agent's phone rings first (a few seconds), then the patient is connected. Login guard (`CALLER_NAME`) enforced exactly as elsewhere.

### H.3 Why no gate risk
The call goes through the **same** OBD path as every other dashboard call. The server stamps the `reference_id`; the duration gate (§G) matches it back exactly as it does for follow-up-tile calls. No new server call path was added. A WhatsApp-feed call still produces a `Call_Durations` row + recording like any other call — it simply has no follow-up tile to unlock, which is expected and harmless.

### H.4 The native-dialog trap (the v18.17 → v18.17b fix)
The first build used the browser's native `confirm()`. In the Apps Script sandbox, the browser force-prepends the served page URL — **"An embedded page at …googleusercontent.com says"** — above the message. To a non-technical user this reads as a scary code. **No web page can remove that header from a native dialog.** Fix: a **custom in-page modal** (H.2), which has no browser header and full copy control.
**Standing rule (D97 corollary): never use native `confirm/alert/prompt` in the dashboard — always an in-page dialog.**

---

## §I — Stale-list top-bar guard, AS BUILT (D98; v18.18)

**A live on-screen twin of the 2 PM email sentinel.**

### I.1 The server signal (read-only)
`CallConsole.gs::getFollowupFreshness(key)` → `{ ok, stale, today, newestDue, rows }`:
- Key-gated (`dashRole_(key)`), read-only, **WebApp.gs untouched**.
- Reads `Followups_Today`, finds the newest `Due Date` (parser handles `DD-Mon-YYYY`, Date objects, ISO), computes `stale = !(newestDue >= today)` on yyyy-MM-dd strings.
- **Identical rule to `Diagnostics.gs::checkFollowupListFresh`** — one truth, so the bar and the email can never disagree.
- **No PHI** — returns dates + a row-count only. Fail-safe: any error → reports not-stale (never blocks the board).

### I.2 The tile
- `checkFreshness()` runs on **every poll** (load + each refresh) and, when `stale:true`, shows `#staleBar` — a **fixed red bar at the very top of the whole page** (z-index 9500), with the message "⚠️ This may be YESTERDAY'S list…" + newest-date/today sub-line + "run the follow-up push — or ask the doctor." `body.stale-on` pads the content down so nothing is hidden.
- **No recheck button** — the normal 60s auto-refresh clears the bar automatically once the push runs.

### I.3 Scope
- Catches the **stale** case (board showing an old day). The email sentinel additionally catches the **generation-missing** case (today's file never created) via Drive; the dashboard bar deliberately focuses on stale, which it can prove from the tab it already reads.

## §J — DURATION GATE: FAIL-OPEN, AS BUILT (D156; v18.18 → v18.19)

### J.1 What broke, and why it was structural
The gate (§G, D77/D82) is a **synchronous blocker** reading an **asynchronous, third-party, best-effort** signal: a `Call_Durations` row written by the VPS receiver from MyOperator's webhook. On 06–08 Jul 2026 the webhook was silently 403'd at the door (Master KB §124.3, D159). No row could ever arrive. The tile could never unlock. **No staff member could record any outcome for two clinic days.**

No repair to the webhook fixes this class of failure. The gate must not be able to stop the clinic.

### J.2 The two bugs that made "Checking…" permanent
Both found in the **live Apps Script export**, not the repo copy (D160 — the committed `Dashboard.html` has no gate at all).

- **Bug A — result states were never persisted.** Only `fuCalled` and `fuRefId` reached `localStorage`. `fuTalked` / `fuMissed` / `fuTimeout` lived in page memory. The render is `called && !talked && !missed && !timedout → "⏳ Checking the call…"`, so **every reload re-rendered the spinner and restarted a fresh 3-minute timer**. For anyone who refreshes, the spinner was permanent. This was the reported symptom.
- **Bug B — a ref-less tile spun forever, literally.** `fuMarkCalled(rid, res.reference_id||'')` persisted the tile as *called with no ref*. `fuResumePolls()` then skipped it (`if(fuRefId[rid] && …)`) and `fuStartPoll()` had a bare `if(!ref) return;`. No poll, no timeout, no escape, across every reload, until `localStorage` was cleared by hand.

### J.3 v18.19, as built
- All six gate states persist: `{date, ids, refs, placed, talked, missed, timeout}` under `dashFuCalled`.
- **The 3-minute timeout is measured from `fuPlacedAt` (when the call was placed), not from page load.** A reload can no longer restart the clock.
- Both silent `if(!ref) return;` paths now call `fuSetTimeout(rid)`.
- The day key is **local (IST)**, not `toISOString()` UTC. Side effect: the old stuck entries flush once, automatically, on first load — no console surgery for staff.
- **FAIL OPEN.** When a call **cannot be measured** within the window, the tile shows *"⚠️ Couldn't verify this call automatically — you can still log the outcome"* **and gives the staff member the outcome dropdown.** A call **measured as not-connected** (the `missed` branch) still blocks the outcome, exactly as D77 intended. Only the couldn't-measure case fails open.

`fuSave`, `triggerCall`, `getCallDuration`, `WebApp.gs` and `CallConsole.gs` are untouched. md5 `034529a124c6bfab8aec2b675620dfec`, 2,738 lines, `node --check` clean, 16/16 invariant checks. Deployed; build stamp `v18.19 · S124`.

### J.4 Standing principles added
- **No verification mechanism may stand between a staff member and recording what a patient said.** Filing is the staff's job; verifying is the system's job; they must not share a critical path.
- **A row reaches `Call_Durations` only when `category == "obd"` AND a `client_ref_id` is present** — i.e. only for calls placed through the dashboard dialer. **A hand-dialled call can never unlock the gate**, with a perfectly healthy webhook. This was always true and was never written down.
- A gate must always have a **terminal state**. `{ok:true, found:false}` means "not yet" and "never" identically; only a clock can tell them apart, and the clock must be anchored to the call.

---

## §K — THE STAFF-FACING UI PROGRAMME (designed S124, NOT built)

### K.1 The measured problem
06-Jul, from `Call_Verdicts`: **15 of 36 outgoing calls (42%) carried no outcome at all.** Of the 21 filed, **4 disagreed with the AI (19%)** — and every disagreement was between adjacent meanings (`coming` vs `on_medication`, `coming` vs `cant_communicate`). Staff file in morning batches, hours later, from memory (D150). 26 incoming calls produced nothing.

This is not carelessness. **The vocabulary asks a receptionist to make a classification that has no correct answer, at a moment when she has already forgotten the call.**

### K.2 The inversion
The eleven codes conflate **what happened** with **what happens next**. Only the second is knowable at hang-up and holdable to.

- **Staff answer "what next"** — four or five mutually exclusive, observable choices (reached & coming · reached & won't come · reached, call again · couldn't reach · needs the doctor). Owner to supply the exact wording, Hindi where it helps.
- **The machine answers "what happened"** — the 11-code vocabulary moves to `call_verdict.py`, derived from the transcript, and lands in the doctor's console.
- **The doctor adjudicates** the disagreements.

Voicemail then stops being a missing code and becomes *couldn't reach*, with the transcript recording that a machine answered.

### K.3 The five rules
1. **Never block.** (§J.4.)
2. **Ask at hang-up, one tap.** Batch filing exists because filing is expensive and deferred. Make the question appear on the tile the second the call ends; the note field stays optional forever.
3. **Never show staff the AI.** They see their own choice. Corrective action reaches them from the doctor, in his words, about the patient — never from a machine that is itself wrong one call in five.
4. **Measure completion, never accuracy.** Completion is in their control; accuracy is the vocabulary's fault. Each agent sees only their own logged-vs-made count.
5. **Undo, never confirm.** (Already the rule — D97: no native `confirm`/`alert`/`prompt`.)

### K.4 Onboarding
No training document. If the UI needs a manual it has failed. Run the new surface **alongside** the current console for a week; the deciding metric already exists — **completion rate**. When it beats 42% for five consecutive clinic days, retire the old flow. Until then the old flow stays, per the standing fallback rule.

### K.5 Honest timeline
Not days. **Weeks for the common outcome codes, months for the rare ones.** ~30 outgoing calls a day and ~4 disagreements; a code needs perhaps 20 refereed examples before its agreement rate means anything. `asked_not_to_call` may take a quarter. **And the doctor's adjudication must fit in ten minutes a day or it will quietly lapse** — only flags, disagreements and phantom calls may ever reach him.

---


---

## CHANGELOG — one table, whole history

| Version | Date | Change |
|---|---|---|
| **v2.0** | **09 Jul 2026 (Session 131)** | **CONSOLIDATED, SELF-CONTAINED.** v1.1–v1.6 merged verbatim into one file; the delta chain is retired. v1.2–v1.5 were recovered from cold-backup zips after being found absent from git, Drive and project knowledge — project knowledge held only the v1.6 fragment, whose opening sentence cross-references a §G that no reader could reach. Two section schemes preserved and parted (PART I numbered, PART II lettered) rather than renumbered, because v1.1 cross-references its own sections and this document records shipped behaviour. Supersession made explicit: §E→§G, §G.4→§J, §A's 3rd-strike→§F. **This file is the only definition of D62, D66, D68, D69, D77, D78, D80, D81, D82, D97, D98** — none of which the Master KB has ever indexed (**F-22**). **No design text was altered, summarised or paraphrased.** |
| v1.6 | 08 Jul 2026 (Session 124) | Duration gate **FAILS OPEN** as built (D156, v18.19): two persistence bugs found in the LIVE export made a stuck tile permanent; all six states now persist, the timeout is anchored to the call, both no-ref paths fail safe, the day key is local. Only the *couldn't-measure* case unlocks; a *measured not-connected* call still blocks. Principle: no verification mechanism may stand between a staff member and recording what a patient said. Recorded: only `category=="obd"` calls with a `client_ref_id` ever reach `Call_Durations` — a hand-dialled call can never unlock the gate. +§K staff-UI programme (designed, not built): staff answer "what next", the machine answers "what happened". |
| v1.5 | 04 Jul 2026 (Session 57) | +§H WhatsApp tap-to-call AS BUILT (D97; custom in-page dialog; same dialer/gate; native-dialog trap fix v18.17→v18.17b). +§I stale-list top-bar guard AS BUILT (D98; read-only `getFollowupFreshness`; shares the email sentinel's rule). |
| v1.4 | 03 Jul 2026 (Session 54) | Duration gate AS BUILT (v18.16, D82) — supersedes the §E design; real-body corrections (D81, join key = `client_ref_id`, signal = customer-leg talk/`answered`); new `call-hook` receiver + `Call_Durations` (D80). |
| v1.3 | 03 Jul 2026 (Session 53) | D66 vanish-on-file as built (v18.15); duration-gate design (D77) replacing the self-declared Talked gate; sticky-on-staff 3-strike (D78). |
| v1.2 | 03 Jul 2026 (Session 51) | Recorded the as-built missed-call binding (D68) and the doctor Escalations-card overhaul (D69). Merge that was queued at Build 4 now done. |
| v1.1 | 01 Jul 2026 (Session 25) | Added §7 (Doctor's Escalation/Resolve screen) and §8 (Staff Flagged Calls tab). Folded persistent staff-console context fields into §3–4. Removed all auto-reconciliation — every escalation is manual resolve. Corrected + refined C19: the recording for outcome review uses the permanent Drive archive link as the primary source, with the MyOperator on-demand player as the same-day-only fallback. Locked C11–C19. **Recorded a backlog item that never reached the KB (F-21): migrate Stage 1 recording archiver from nightly batch to per-call download, with a MyOperator processing-lag/retry check and a webhook trigger.** No code changed this session. |
| v1.0 | 29 Jun 2026 | First version. Full spec agreed in Session 18. |

---

## WHAT THIS DOCUMENT STILL OWES

- **§E vs §F vs D195.** §F (D78, Session 53) says the third strike drops the patient to a bottom band, fires a WABA template, and snoozes X days. **D195 (Session 131) says the third attempt sends the case to the doctor.** These disagree. **Neither is built. They must be reconciled before either is.**
- **§F's cross-day miss counter** was never built. Today's worklist assembly counts per-day only.
- **§K** (the staff-UI inversion) is designed and not built.
- **§G.6** — the PHI base swap: `client_ref_id` still embeds the patient mobile.
- **The v1.1 backlog item** — per-call recording download — was re-derived as **D200** in Session 131, 106 sessions after it was written down here. It reached no backlog because a spec changelog is not a backlog. See **F-21**.

---

**END OF CALL CONSOLE EVOLUTION SPEC v2.0 — the changelog is followed by "WHAT THIS DOCUMENT STILL OWES", which is the last section. If it is absent, this file is truncated and must not be used as canonical.**
