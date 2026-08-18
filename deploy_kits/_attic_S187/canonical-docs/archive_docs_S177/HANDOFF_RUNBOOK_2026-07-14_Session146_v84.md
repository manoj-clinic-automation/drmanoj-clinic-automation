# HANDOFF RUNBOOK — 14 Jul 2026 · Session 146 · v84

Canonical reference is the **KB (v1.72)** — if anything here disagrees with it, the KB wins.
This runbook is the "where we stopped" file: §0 what happened, §1 mental models, §2 open backlog.

---

## §0 — WHAT HAPPENED THIS SESSION (Session 146, FULL EOS)

**Headline: a callback-tracker FINALISATION session. B1 shipped — the 21:30 digest now READS the Flag Investigator's results file instead of recomputing — and the project's product architecture was NAMED as a three-link lineage (D246).** One live VPS file changed; no cron touched; no new fault; no data touched.

**0.1 — B1 built, installed, proven.** `daily_digest.py` v1.4 → **v1.5** · md5 `0a4ee35b5fb7fbc0570efe3bc0cdde88` · **83/83** selftest (+8 new checks). The 21:30 digest loads `flag_investigator_results.json` and renders a new **"Recording health"** section quoting the Investigator's rolling `never_recorded_7d` / `missed_no_conversation` split + `escalate_lokesh`, with a freshness stamp — ONE source of truth, no recompute (closes the S145 §2B carryover). **Fail-loud:** a missing / unreadable / stale (>20 h) results file is said so plainly; the numbers are withheld, never a silent zero. **Additive only** — the 11:00 pulse and the same-day per-call "no recording today" alert are untouched. Read-only, writes nothing (D236); no `append_row` (D235) — both re-asserted by selftest.

**0.2 — install proof (D188).** GitHub == live confirmed by hash BEFORE edit (`daily_digest f7e05ed2…`, `flag_investigator a9baa6ca…`). After build: WinSCP → md5 match on the VPS (`0a4ee35b…dde88`) → `py_compile` OK → selftest 83/83 → live `--digest --dry-run` printed the Recording health line ("0 genuine never-recorded · 0 missed") against real data (17 calls / 9 mismatch / 0 staff-logged). Nothing sent, nothing written. **No cron change** — the 21:30 cron picks it up automatically.

**0.3 — D246: the three-product lineage named.** Followup Tracker (clinic PC, offline — SOURCE) → Callback Tracker (VPS, Sheet + Console — Product A, SYSTEM OF RECORD) → Call Intelligence (VPS, `recordings-archive` — Product B, ANALYTICS). Conceptual + contract seam, NOT separate infra (one VPS/repo/secret/EOS for A+B). Three seams; two are contracts (Callback→Intelligence; Investigator→Digest, hardened by B1); the **Followup→Callback** seam is the one still to name — its break is the chain's highest-impact failure, and the Docterz export migration (D243) lives there.

**0.4 — B2 clinical windows captured (parked for #10).** Outgoing follow-ups: LEARN the return window PER DIAGNOSIS from ~5 weeks of history (no single ± number). Incoming fresh leads + missed-call callbacks: flat **3-day** conversion window. To be minted as decisions when #10 builds.

**0.5 — housekeeping caught + fixed.** The **v1.71 CHANGELOG entry was absent** although the v1.71 end-marker promised it (an S145 EOS omission) — backfilled in the v1.72 bump. Same stale-record family the KB has caught before.

**Decisions minted:** **D246** (three-product lineage). No new finding (F-45 still free). **Fault-code changes:** none. **Fault→Action Register:** unchanged. **Diagnostics Spec:** UNCHANGED (stays v2.3 — B1 adds no fault code/check/fallback; it changes the digest's reporting line only). **Incident:** none this session.

---

## §1 — MENTAL MODELS (carry these into S147)

- **Three products, one contract, one substrate.** First triage question for any fault: which side of a seam? Operational/data problem → Product A (clinic-urgent, manual fallback). Wrong verdict / miscounted digest → Product B (calm, no clinic impact). F-44 is the proof the boundary already points true.
- **The unnamed seam is Followup→Callback.** A due patient never reaching the call list is the worst failure in the chain and the least-instrumented. The Docterz export migration is that seam's work.
- **Fail-loud beats a silent zero.** B1's rule: if the source can't be read or is stale, SAY so and withhold the number. A confident wrong zero is worse than an honest "unavailable."
- **Duration is not talk time (carry from S145/D244).** Any recording/"did-we-talk" detector reads MyOperator's top-level `status`, never talk-seconds.
- **Proof is the artefact (D172/D188).** B1 was proven by a live dry-run printing the real line, not by asserting it — same discipline as the F-41/F-44 re-baselines.

---

## §2 — OPEN BACKLOG (for Session 147)

### §2A — Owner decisions (no code)
- **The follow-up "came" window is now CAPTURED via B2** (outgoing: per-diagnosis, learned from ~5 weeks; incoming: flat 3-day) — the old S145 A1 item is resolved in principle. The residual is a **build-time recon**, not a standing decision (see §2B #10).

### §2B — Next builds (gated, offline→md5→selftest→install)
1. **D241 insights, order 10 → 1 → 2.** #10 recon first: locate the visit-ledger, the join key (phone vs clinic UID), and the diagnosis field's presence/mapping (the `Orthopedic_Diagnosis_Taxonomy_Master` may be the grouping source); then a read-only VPS-side aggregate join reporting the two funnels separately (D243). One owner decision may surface at build: how diagnoses group for the per-diagnosis return curve. #1/#2/#3 = one `call_insights.py`.
2. **Optional digest tightening (deferred):** the 20 h stale guard catches "didn't run today at all," not "ran this morning then went quiet all afternoon" (a 09:00 file at 21:30 is ~12 h old → still "ok"). A one-line tightening (e.g. 4 h) would flag an afternoon stall. Not needed now; fold in next time the digest is opened.
3. **`call_verdict.py` cosmetic relabel** — still recommended to SKIP until that file is opened for a real reason.

### §2C — Standing
- **GitHub commit owed:** `daily_digest.py` v1.5 (this file was the overdue-commit flag — now due). Commit message provided at EOS.
- **Lokesh items:** CALLHOOK secret rotation Steps 3–4, service-account key rotation (Tier A1), AKEY_14 — all await Lokesh.
- **VPS venv Python 3.9 EOL** (Tier C) — harmless FutureWarning each run; schedule a deliberate venv rebuild (retests every pipeline).
- Hindi spelling corrections in `vitals_page.html` (content correct, spelling only) · F-37 health-mail window · repo naming tidy · K toggle-removal watch (arm when one-tap usage >42% for 5 consecutive days).
- **Docterz export MIGRATION** — the Followup→Callback seam work; enhancement, not a blocker (D243/D246).
- **A8/D223 doctor-portal gist tile** — its #9 feeder (the Investigator's results file) is now read by both the Investigator and the digest; build after the Investigator has run stably.

**Next free decision number: D247. Next free finding number: F-45.**

---
**END OF HANDOFF RUNBOOK Session 146 v84.**
