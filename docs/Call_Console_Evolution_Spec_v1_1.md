# Call Console — Evolution Spec
## Advanced Orthopaedic Surgery Centre, Bareilly
**Version 1.1 · 01 July 2026 · Session 25**
Owner: Dr. Manoj Agarwal · Maintained with: Claude (per session)

> **What this document is.** The complete specification for evolving the existing
> Callback Dashboard (**current live build = v14**) into the clinic's primary call
> console — the single screen that replaces the MyOperator dialer, the Excel outcome
> log, and the Staff Action follow-up sheet. This is a living spec: update it as
> design decisions are locked and as each build step completes.
>
> **v1.1 change summary:** adds the doctor's private Escalation/Resolve screen (§7)
> and the staff-side Flagged Calls tab (§8) — the "grown scope" the Session 24
> runbook flagged as needing a spec pass before Stage 4 / Call Console Step 2 build
> begins. Also folds in three context fields (recording link, diagnosis, last visit)
> that now persist across the staff console (§4). Sections 1–3, 5, 6 carried forward
> from v1.0. No code has been written against this version — design only.
>
> **Companion documents:** Umbrella Architecture v1.10 · Master KB v1.12 ·
> Diagnostics & Surveillance System Spec (latest)

---

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

## 12. Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 29 Jun 2026 | First version. Full spec agreed in Session 18. |
| 1.1 | 01 Jul 2026 | Session 25. Added §7 (Doctor's Escalation/Resolve screen — two groups, manual-only resolve, animated confirmation, Flag action, transcript dropdown) and §8 (Staff Flagged Calls tab — fixes the duplication bug, defines staff vs doctor visibility). Folded persistent staff-console context fields (recording/diagnosis/last-visit, C16) into §3–4. Removed all auto-reconciliation (C13) — every escalation is manual resolve. **Corrected + refined C19:** the recording for outcome review uses the **permanent Drive archive link as the primary source** (reliable from the next day onward, never expires), since review is often not same-day; the MyOperator on-demand player is the same-day-only fallback. Rule: show the Drive link if it exists, else the MyOperator player. The earlier "pending until tomorrow" wording was wrong and is gone. Corrected build references to v14→v15. Locked C11–C19. **New backlog item recorded (not in this spec):** migrate Stage 1 recording archiver from nightly batch to per-call download — a later change to the live archiver, requiring a MyOperator processing-lag/retry check and a webhook trigger; when built it makes the permanent Drive copy appear within minutes and further softens the ~24h fallback. No code changed this session — design/documentation only. |

*End. Keep one copy in Notion "Clinic HQ" and one in the handoff kit.*
