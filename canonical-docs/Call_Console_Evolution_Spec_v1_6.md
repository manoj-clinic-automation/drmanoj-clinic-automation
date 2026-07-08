# Call Console Evolution Spec — v1.6 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward v1.5 unchanged. Records **Session 124: the duration gate now FAILS OPEN (D156, v18.19)**, the two persistence bugs that made a stuck tile permanent, and the staff-UI inversion designed but not built. Where this delta describes shipped behaviour it is authoritative.

---

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

## CHANGELOG
| v1.6 | 08 Jul 2026 (Session 124) | Duration gate **FAILS OPEN** as built (D156, v18.19): two persistence bugs found in the LIVE export made a stuck tile permanent; all six states now persist, the timeout is anchored to the call, both no-ref paths fail safe, the day key is local. Only the *couldn't-measure* case unlocks; a *measured not-connected* call still blocks. Principle: no verification mechanism may stand between a staff member and recording what a patient said. Recorded: only `category=="obd"` calls with a `client_ref_id` ever reach `Call_Durations` — a hand-dialled call can never unlock the gate. +§K staff-UI programme (designed, not built): staff answer "what next", the machine answers "what happened". |
| v1.5 | 04 Jul 2026 (Session 57) | +§H WhatsApp tap-to-call AS BUILT (D97). +§I stale-list top-bar guard AS BUILT (D98). |
| v1.4 | 03 Jul 2026 (Session 54) | Duration gate AS BUILT (v18.16, D82); real-body corrections (D81); call-hook receiver + Call_Durations (D80). |
| v1.3 | 03 Jul 2026 (Session 53) | D66 vanish-on-file as built; duration-gate design (D77); sticky-on-staff (D78). |
| v1.2 | 03 Jul 2026 (Session 51) | Missed-call binding (D68) + Escalations-card overhaul (D69). |
| v1.1 | (Session 25) | As previously recorded. |
