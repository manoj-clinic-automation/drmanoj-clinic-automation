# Call Console Evolution Spec — v1.2 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward **everything in v1.1 unchanged** and records what was actually **built** in Session 51 for the D57/D66 tile behaviour and the doctor Escalations surface (the merge that was queued "at the start of Build 4"). Where this delta describes shipped behaviour, it is authoritative over the v1.1 design text.

---

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

## CHANGELOG
| v1.2 | 03 Jul 2026 (Session 51) | Recorded the as-built missed-call binding (D68) and the doctor Escalations-card overhaul (D69). Merge that was queued at Build 4 now done. |
| v1.1 | (Session 25) | As previously recorded. |
