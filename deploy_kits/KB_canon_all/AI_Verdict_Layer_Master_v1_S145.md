# AI VERDICT LAYER — MASTER (v1, Session 145 · 14 Jul 2026)

**Dr. Manoj Agarwal Clinic, Bareilly.** Maintained with Claude.
**Status: canonical.** This is a live description, not a plan.

**What this file is.** The single, self-contained account of the AI verdict layer: every script, what it owes, to whom, in which tab, under which rule, and what breaks if it lies. Compiled from artefacts, never memory (D172): the design spec, the live code, the runbook, and the MyOperator API reference. Where the as-built diverges from the S131 design, this file **names the divergence** rather than papering over it.

**Supersession / retirement (per the S143 charter).**
- This Master **replaces** `AI_Review_Layer_Design_Spec_v1_1_S131.md` in project knowledge (doc count unchanged; one Phase‑0 row swaps).
- It **retires** `AI_Verdict_Layer_Master_CHARTER_S143.md` — the charter was the build order; this file is the build.
- **D242** was the decision to write this Master, gated on the Flag Investigator being live and stable. **D245 (S145):** the owner directed the write at S145 — the Investigator is live (S144) and its first correctness proof landed this session (F‑44, the "42" collapse). The timing gate is satisfied by owner decision.

**The opening sentence, now a description, not an intention:**
> **The judge proposes. The doctor disposes. The staff act.**
> As of 13 Jul 2026 this describes what happens daily: 586 proposed · 18 disposed · the digest directs staff every morning and night.

---

## §0 — THE INVARIANT AND THE ASYMMETRY

Each clause of the governing sentence is the **writer of a different table**. That is the invariant the whole layer is built to preserve. No table ever gains a second writer.

| Clause | Writer | Table(s) |
|---|---|---|
| The judge proposes | `call_verdict.py` (VPS) | `Call_Verdicts` |
| The doctor disposes | the dashboard (Apps Script) | `Doctor_Verdicts`, `Followup_Escalations` |
| The staff act | the dashboard (Apps Script) | `Followup_Outcomes` |

**The asymmetry that governs every gate:**
> **A false bounce costs one phone call. A false settle closes a case that never connected, and is invisible.**

Wherever the layer chooses caution, that sentence is the reason. It is why the judge only *proposes*, why nothing auto‑settles a case, and why 100 doctor‑refereed cards gate any automation (D191).

---

## §1 — THE DATA-FLOW SPINE

```
MyOperator call  ──(webhook: call.end / call.summary)──►  call_hook_capture.py
                                                            │  writes Call_Durations
                                                            │  (one row per call, at hangup)
                                                            ▼
                                              drops a "kick" into the pipeline queue
                                                            │
                                                            ▼
                                            call_pipeline_worker.py  (systemd, single flock)
                                     ┌──────────────────────┼───────────────────────────┐
                                     ▼                      ▼                            ▼
                        call_recording_archive.py   call_transcription.py        call_verdict.py
                        writes Call_Recordings   →   writes Call_Transcripts  →   writes Call_Verdicts
                        (status 1 + filename only)   (Sarvam, Hindi)              (Claude judge; identity-blind)
                                                                                        │
                                                                                        ▼
                                                                        verdict_review.py → Verdict_Review tab
                                                                        (worst-first review band + referee drip)
                                                                                        │
                                                                                        ▼
                                                                        DOCTOR taps on the dashboard
                                                                        → Doctor_Verdicts (the disposition)
                                                                                        │
                                                                                        ▼
                                                        daily_digest.py  (reader of everything, writer of nothing)
                                                        → 11:00 pulse + 21:30 digest → owner's Gmail → staff act

               flag_investigator.py  ── self-healing SIDE-LOOP on lost conversations ──►  flag_investigator_results.json
               (reads Call_Durations, asks MyOperator /search, kicks the worker for TODAY recoverables)
```

**The spine's one rule:** the digest and the Investigator **read**; they never write a pipeline tab. The worker is the single orchestrator (its flock guarantees one pipeline at a time). The Investigator heals by dropping a *kick*, never by writing `Call_Durations` or `Call_Recordings`.

---

## §2 — THE THREE AXES (the judge's vocabulary)

The judge answers on three independent axes. The transcript has **no speaker labels** — it is one undivided Hindi block — so the judge infers cautiously and answers **UNCLEAR** rather than guess.

- **Axis 1 — CONTACT (what happened on the wire).** Was the patient reached, and how far did the conversation get? Codes include the reached/answered outcomes plus the non‑contact set (`no_answer`, `busy`, `unreachable`, `call_failed`, `voicemail`, `ivr_or_bot`, `answered_silent`, `call_dropped`, `audio_unusable`, `language_barrier`, `patient_deceased`).
- **Axis 2 — OUTCOME (what the call achieved).** The follow‑up disposition vocabulary — direction‑specific — e.g. `coming` / `confirmed` / `will_come`, `out_of_town`, `on_medication`, `needs_callback`, `escalated`, `cant_communicate` ("call connected but no meaningful conversation possible"), `resolved_on_call`, plus **UNCLEAR** always.
- **Axis 3 — CONDUCT (how the call was handled) — the interpretive axis.** Objective sub‑flags (was the clinic identified, was the next step confirmed) and interpretive ones (tone, closing). **Conduct is proposed only; the doctor's confirmation writes the record.** Per‑flag applicability is hard‑coded: *you cannot follow a script at a voicemail.* On a `wrong_number`, "did you say which clinic was calling" still applies; "did you follow the follow‑up script" does not.

**Conduct is currently collected silently.** The `script_not_followed` / `no_closing` flags are **not operable** until the owner supplies a written call script and a closing definition (design §8.7; status UNKNOWN, D166/D199). Absence of a script is itself the finding. Conduct calibration needs its own set — **40 calls the doctor has listened to himself** — separate from contact calibration.

---

## §3 — THE TWO-PHASE GATE (D191)

> **Phase 1 (now, live):** the judge proposes; the doctor reviews; nothing moves on its own.
> **Phase 2 (gated, not built):** the judge may auto‑bounce a tile **only after** 100 doctor‑refereed cards show ≥95% agreement with **zero false‑settles in the last 50**.

Phase 2 does not exist and will not until the gate is met. As of this Master: **18 of 100** refereed, raw agreement **~89%** (S143 snapshot). The gate exists because of the asymmetry in §0 — a false settle is silent and unbounded; a false bounce is one phone call.

---

## §4 — PER-SCRIPT CONTRACTS (what each owes · to whom · which tab · which rule · what breaks if it lies)

Live md5s below are the GitHub copies; for the four D160‑verified files (`call_verdict`, `verdict_review`, `daily_digest`, `make_force_keys`) repo == live was proven at S144. Always re‑verify against the VPS at read time (the charter's rule; never trust this list over `md5sum` on the box).

| Script | Live md5 | Owns (writes) | Reads | The rule it lives under | What breaks if it lies |
|---|---|---|---|---|---|
| `call_hook_capture.py` (v3.1) | `b8a1a293c54dfb6528e04fdf31f8d3e6` | `Call_Durations` (sole writer) | the webhook payload | one writer per tab (F‑3/D235); explicit computed rows (F‑39) | the duration gate and every downstream reader inherit a wrong "did we talk" signal (this is exactly where F‑44's raw truth lives — it stored `status`/`customer_result` correctly; the consumers ignored it) |
| `call_pipeline_worker.py` | `3c8be7f0f6f5960103fb1ed586c48cce` | orchestration only (flock) | the kick queue | one orchestrator; idempotent stages | a call is archived/judged twice or not at all |
| `call_recording_archive.py` | *(verify on VPS)* | `Call_Recordings` (sole writer) | MyOperator `/search` | only `status "1"` + non‑empty filename is pulled | a missed call (no filename) would enter the recorded set — it cannot, by this gate |
| `call_transcription.py` | *(verify on VPS)* | `Call_Transcripts` | `Call_Recordings` | trusts the archiver; no status logic of its own | if the archiver leaked a non‑call, the transcript would be empty and the verdict would say `cant_communicate` (accurate, not a mislabel) |
| `call_verdict.py` (v2.1) | `539ea68fb4ce99f0029fdbb53bbf8ebe` | `Call_Verdicts` (sole writer; the judge) | `Call_Transcripts`, `Call_Recordings` (link only) | identity is **never** sent to the AI (D198); judge proposes only | the doctor's dispositions rest on a biased or identity‑aware judgement; D198 dies the moment an agent name is added "for context" |
| `verdict_review.py` (S124/v3) | `280eb2cef9295d89f30c7b84d4c94adb` | `Verdict_Review` (sole writer) | `Call_Verdicts`, `Doctor_Verdicts` (prefill) | ONE DECIDER for any derived pick (S143); an answered card is never re‑asked (D240b) | the doctor is shown the wrong worst‑first order or re‑asked a settled card |
| `flag_investigator.py` (**v1.2, this session**) | `a9baa6ca22055bb188d5c65b93c47ba1` | `flag_investigator_results.json` (sole writer) | `Call_Durations`, MyOperator `/search` | never writes a pipeline tab; heals by a kick, not a write; keys on provider `status`, not talk‑seconds (**F‑44**) | a missed call is counted as a "lost recording" and a false escalation reaches Lokesh — exactly the F‑44 fault, now fixed |
| `daily_digest.py` (**v1.4, this session**) | `f7e05ed2a79670667fda170f3b70b9d1` | nothing (reader of everything) | all verdict/duration/outcome tabs | writer of nothing; read‑only scope; status‑aware (**F‑44**) | the owner is told a missed call is a "connected call, no recording" (the exact confusion that opened S145) |
| `make_force_keys.py` | `9b44831a0a2a2003fac5c4901f7da35c` | one‑off (historical) | — | — | historical note only; not in the live loop |

---

## §5 — THE STANDING GROUND RULES (each with its scar)

1. **One writer per tab.** `Call_Durations` = capture; `Call_Recordings` = archiver; `Call_Verdicts` = judge; `Verdict_Review` = review; `Doctor_Verdicts`/`Followup_Outcomes` = dashboard. (Scar: **F‑3**, and **F‑39**, the append‑overwrite disaster.)
2. **Explicit computed rows, never append‑detection.** Every write targets a computed row/range. (Scar: **F‑39** — Sheets append silently landed verdicts on one within‑table row.)
3. **Placement‑independent counts.** Never infer a count from where a row sits. (Scar: **D240**.)
4. **Numeric time compares, never text.** Three files were bitten comparing "9:06" as text. (Scar: **D240g**.)
5. **Idempotent upserts, proven by running twice.** (Scar: S143 proof discipline; **F‑43**, the anti‑spam gate that must key off the durable action‑taken marker, not a derivable transition.)
6. **The answered ground truth is never re‑asked.** (Scar: **D240b**.)
7. **ONE DECIDER for any derived pick.** The review layer decides the spot‑checks; the digest only reports them. (Scar: S143.)
8. **Identity is never sent to the AI.** The judge sees a transcript, a direction, and a duration — never a name or number. (Scar: **D198**.)
9. **₹0 paths stay ₹0.** (Scar: cost discipline.)
10. **A check that cannot fail is not a check.** (Scar: `grep -c` exits 1 on zero; never chain with `&&`.)
11. **Judge from provider status, not from seconds.** A call's clock includes ring/hold; "40 talk‑seconds" can be a *missed* call. Recording‑gap detection keys off MyOperator's `status` (bridged/missed/voicemail), not talk‑duration alone. (Scar: **F‑44 / D244**, this session — the "42 never‑recorded" was 42 missed calls; it collapsed to 0.)

---

## §6 — DECISIONS RESTATED (the ones this layer stands on)

- **D62** — purpose: the layer turns raw calls into a doctor‑usable proposal, never an autonomous action.
- **D191** — the two‑phase gate (§3): 100 refereed, ≥95%, zero false‑settles in the last 50.
- **D198** — the judge never sees identity. A rule, not a convention.
- **D235** — no append‑detection; every write is an explicit computed row; one writer per tab.
- **D236 / D238** — the daily digest layer (11:00 pulse, 21:30 digest; reader‑only; AI summary from aggregate counts).
- **D237** — the referee set + daily drip (the 41‑call stratified set; the doctor referees at his pace).
- **D239** — the Flag Investigator defaults (self‑heal ON for today's recoverables; every 30 min 09:00–20:00; Lokesh escalation at ≥3 genuine never‑recorded/7d).
- **D240** — forced review cards, one decider, numeric times (and D240b: answered cards never re‑asked; D240g: numeric time compares).
- **D241** — the insight register + the five gist feeders.
- **D242** — the decision to write this Master, gated on the Investigator being live and stable.
- **D243** — two conversion pipelines, never one number: follow‑up is informational/no‑chase (metric = return around the DUE date); incoming unknown numbers are fresh leads (3‑day window).
- **D244 (NEW, S145)** — recording‑gap detection keys off the provider's top‑level `status` (bridged vs missed/voicemail), not talk‑duration alone. A missed call is never a "lost recording." The consumers must use the same connected‑vs‑missed truth the Apps Script gate already uses (`status == "bridged" && customer_result == "answered"`).
- **D245 (NEW, S145)** — this Master is written at S145 (owner override of D242's ~S145–146 timing), superseding the S131 design spec and retiring the S143 charter.

---

## §7 — LIVE SNAPSHOT (as of Session 145, 14 Jul 2026)

- **Proposed (Call_Verdicts):** 586 · **Disposed (Doctor_Verdicts):** 18 · **Refereed toward the 100 gate:** 18 / 100 · **Raw agreement:** ~89% (S143 snapshot; re‑snapshot from the artefacts each write).
- **Flag Investigator:** `never_recorded_7d = 0` after the F‑44 re‑baseline (was 42; all 42 were provider‑missed `status 2`). `escalate_lokesh = False`. The standing "take the 42 to Lokesh" action is **void** — it was a false alarm.
- **Verdict layer scripts:** all live md5s in §4; `flag_investigator.py` v1.2 and `daily_digest.py` v1.4 installed this session.

---

## §8 — DELIBERATELY NOT CARRIED (nothing falls out silently)

- **F‑8 / the incoming `Log outcome ▾` button, the tile‑removal contract (D195), stable case identity (§3 of the design spec), the Do‑Not‑Call tab (§7), the escalation groups A/B and attempt caps (§4):** these are **dashboard / Apps Script** concerns, owned by the Frontend Dashboard doc and the Call Console Evolution Spec, not this Master. They interlock with the layer but are documented there.
- **The conduct training pack (design §8.5) and Phase‑2 auto‑bounce (§5.2):** LATER, gated (script definition + the 100‑card gate). Named here, not built.
- **The Docterz export MIGRATION:** downgraded by D243 to an enhancement, not a prerequisite; owned by the follow‑up/insight track.
- **`AI_Review_Layer_Decision_Workbook_S131.docx`:** the collection vehicle for the conduct decisions; historical, superseded by this Master's §2.

---

## §9 — WHAT THIS LAYER DOES NOT DO

- It does not act on its own. **Not in Phase 1, and not until 100 refereed cards say otherwise.**
- It does not let the judge see who made the call (**D198**).
- It does not score a person. Conduct is reported as standardization ("46 of 52 calls identified the clinic"), never a league table; per‑agent view is doctor‑only, opened for a reason, never a scoreboard; denominator honesty (D179) — never a bare number.
- It does not export a patient's voice. Coaching plays the recording on screen; it never becomes a file that leaves the clinic.
- **An audit finds; it does not fix (D180).**

---

## CHANGELOG

| Version | Date | Change |
|---|---|---|
| **v1 (S145)** | **14 Jul 2026** | First Master. Compiled from the S131 design spec (superseded), the S143 charter (retired), the live code, the runbook, and the MyOperator API reference. Carries the invariant + asymmetry, the data‑flow spine, the three axes, the two‑phase gate, per‑script contracts with live md5s, the ground rules with scars, the decisions the layer stands on (incl. **D244**/**D245** minted this session), the live snapshot, and the deliberately‑not‑carried list. Written at owner direction (D245) with the Flag Investigator live (S144) and its first correctness proof landed (F‑44). |

---

**END OF AI VERDICT LAYER MASTER v1 — §9 and the CHANGELOG are the last sections. If either is absent, this file is truncated and must not be used as canonical.**
