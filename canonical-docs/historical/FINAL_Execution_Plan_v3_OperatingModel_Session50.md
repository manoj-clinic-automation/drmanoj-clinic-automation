# FINAL EXECUTION PLAN — Follow-Up Operating Model v3
## Session 50 · July 2026 · THE single reference for the coding sessions ahead
**Dr. Manoj Agarwal Clinic · Bareilly**

Supersedes: Rollout Plan v2 (S47) §3 and Operating Model (S46) §5. Companions: Master KB v1.18 · Runbook v29 · Human-Error Audit (S46) · Call Pipeline Audit Evidence (02 Jul).

---

## PART 1 · THE END-STATE DAY (one picture)

| Time | What happens |
|---|---|
| End of day / before 2 PM | Shavez exports **consultation report** (complete, with financials) — consumed by NEXT day's generation |
| ~1:30–2:00 PM | Shavez exports **Follow-ups Due** report (fresh) |
| 2:00–3:00 PM | Staff Action Sheet generated: yesterday's consultation + today's Due + doctor-approved outcomes → dashboard by 3 PM |
| **3:00–7:00 PM** | **Calling window.** Staff work a list that only shrinks. No-answers snooze 1 hr; filed outcomes vanish; 3-strikers exit to doctor |
| Rolling | Per-call pipeline: recording (~10-min poller) → Sarvam → AI verdict 15–25 min after hang-up |
| ~7:30 PM | Doctor console ready: agreements auto-approved; only doubts, disagreements, and Unreachables await review |
| Evening | Doctor reviews in minutes; approvals suppress patients from tomorrow's 2 PM list |
| 02:00/03:00 | Nightly timers = sweeper/fallback only |

---

## PART 2 · DECISION REGISTER (D62–D66, to be logged at EOS)

**D62 — AI as independent second-filer.** Staff file at call time; AI derives its own outcome from the transcript. Agree = auto-approve; disagree/doubt = doctor console with both shown. Solves approve-all fatigue (H3) and verifies connected calls (M1).

**D63 — Per-call pipeline adopted early.** 10-minute VPS daytime poller (trusted archiver pattern; no webhook dependency for v1) fetches each recording after hang-up; transcribe + verdict per call. Cost ~₹400–700/mo accepted. Nightly batch demoted to sweeper, never deleted.

**D64 — Calling window 3–7 PM.** Operational, zero code. Staff availability (receptionist + Shavez free), patient reachability (family phones answered), doctor availability (free after 3 PM) all align. Evening walk-ins start 6:30 — minimal overlap.

**D65 (revised) — Two-clock Docterz exports.** Due report → 2 PM, drives same-day generation. Consultation report → end-of-day (canonical, financial-complete), consumed next day. Accepted gap: same-morning walk-ins self-heal via staff filing + AI confirmation. Partial 2 PM pull parked as data-driven filter option. Prior-night 01:40 generation retained as fallback during transition.

**D66 — The Living Staff List.** Full definition:
1. **No-answer → snooze:** tile greys out, shows "retry after HH:MM" (+1 hour), wakes automatically. Max **3 tries/day**, enforced spacing.
2. **3rd miss →** tile **exits the staff list** to the doctor's **"Unreachable — review" band**, carrying full attempt history (times · ring seconds · agent). Simultaneously an **automatic WhatsApp nudge** goes to the patient (approved utility template, existing wa-send plumbing): "हमने आपसे संपर्क करने की कोशिश की…" + callback number. Doctor's one-tap options: Retry tomorrow (Day 2 of 3) / Pause (normal cycle) / Remove (logged).
3. **Outcome filed → tile vanishes immediately.** 10-second toast "Outcome filed — UNDO" for mis-taps; after that, corrections happen only via the doctor's send-back (D58), which re-creates a "sent back" tile on the staff list.
4. **Only trace of finished work:** plain counter "Aaj ke completed: N". No Done strip.
5. **Agent-wise call details section (collapsed, bottom of staff dashboard) stays unchanged** — D66 governs work-queue tiles only.
6. Net effect: the staff list contains **only calls still to be made** and trends to empty by 7 PM.

*(D57/D57b/D58/D59/D60/D61 stand as locked in S45; D66 defines the full behaviour of the D57 tile rework.)*

---

## PART 3 · STAFF DASHBOARD — END-STATE SPEC

- Work queue = pending tiles only. Each tile: patient (masked no.), band, last-visit date, Call button.
- **Connected call →** outcome form on the tile: outcome code + **"Spoke with: patient / family"** + note → file → vanish (undo toast).
- **Missed call →** NO outcome dropdown (D57/D60). Only: attempt history, snoozed Retry, and two escape codes ("wrong number", "asked not to call") which route to doctor review.
- Sent-back tiles from doctor appear with the doctor's note.
- Footer: "Aaj ke completed: N" + existing collapsed agent-wise call details (untouched).

## PART 4 · DOCTOR CONSOLE — END-STATE SPEC

- v18.3 fixes: band default-open, last-visit date, 📵 missed-no-recording chip.
- **Unreachable band** (3-strikers) with attempt history + Retry/Pause/Remove.
- All outcomes flow here (D58); **auto-approve gate** slot ready for AI (D62).
- **Off-system contact** outcome source flag (doctor-only).
- Metrics tiles: filing-lag median + burst % per agent · removals-vs-connects per agent.
- Approved outcomes → next-day suppression (D59).

---

## PART 5 · THE CODING SEQUENCE (next sessions, in this exact order)

| Build # | Session-sized chunk | Files touched | Gate to proceed |
|---|---|---|---|
| **1** | **v18.3** — band default-open + last-visit date + 📵 chip | Dashboard.html only | Feature-check on live /exec |
| **2** | **Stale-list sentinel** — time-trigger ~3:15 PM, ntfy on stale Followups_Today | New standalone .gs | Test alert received on phone |
| **3** | **Generation shift** — tracker runs ~2 PM on yesterday-consultation + today-Due; runs in PARALLEL with 01:40 for ≥3 days | PC tracker timing/config | 3 clean parallel days |
| **4a** | **D57+D66 staff tile rework, part 1** — missed-call blocker, snooze/retry timer, 3-try counter, attempt history | Dashboard.html + WebApp.gs | Staff-flow walkthrough |
| **4b** | **Part 2** — vanish+undo toast, completed counter, spoke-with field, escape-code routing | Same files | Live half-day observation |
| **5** | **Unreachable handoff** — 3-strike exit to doctor band + WhatsApp nudge hook (wa-send) | WebApp.gs + small VPS endpoint | Nudge received on test number |
| **6** | **Doctor Unreachable band** + Retry/Pause/Remove actions | Dashboard.html + .gs | One full evening review cycle |
| **7** | **Filing-lag + burst metric tile** | Doctor console .gs/html | Numbers sanity-checked vs audit CSV |
| **8** | **D58 unified console** + off-system flag + auto-approve gate slot | Console files | One week stable |
| **9** | **D59 suppression** in push script | push_followups_today.py | Settled patient absent next day |
| **10** | **Stage-3 Spec v1** (document, no code) → then poller (D63) → then AI verdict (D62) | New VPS scripts | Spec approved before any code |

**Parallel track (any session):** key rotation with Lokesh (book it — highest non-feature priority) · Docterz-export sentinel (both reports) · Sarvam auto-retry in the 03:00 job · missed-incoming queue (later).

**Phase 0 (operational, starts now, no code):** announce 3–7 PM window; Shavez begins two-clock exports; staff use existing list in the new window until Build 3 lands.

---

## PART 6 · STANDING RULES FOR ALL BUILDS ABOVE

Full-file replacements only · zero-risk rule (no live file without replacement; diagnostics in temp files) · edit existing deployment → New version (URL stable) · feature-check, not stamp-check (D53) · py_compile / node --check gates · md5sum on VPS uploads · manual fallbacks never deleted · secrets never printed.

*End of document. Next fresh session opens with Build 1 (v18.3).*
