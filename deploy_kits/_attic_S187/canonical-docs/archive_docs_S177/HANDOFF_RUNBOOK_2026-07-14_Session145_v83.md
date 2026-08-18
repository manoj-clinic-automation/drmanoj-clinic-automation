# HANDOFF RUNBOOK — 14 Jul 2026 · Session 145 · v83

Canonical reference is the **KB (v1.71)** — if anything here disagrees with it, the KB wins.
This runbook is the "where we stopped" file: §0 what happened, §1 mental models, §2 open backlog.

---

## §0 — WHAT HAPPENED THIS SESSION (Session 145, FULL EOS)

**Headline: F‑44 found, fixed, and proven — the "42 never‑recorded" was 42 missed calls, and it collapsed to 0. The Lokesh escalation was a false alarm. And the AI Verdict Layer Master was written (D245), superseding the S131 design spec and retiring the S143 charter.** Two live files changed; no new fault reached the clinic; no data lost.

**0.1 — F‑44 raised (NEW FAULT).** The 21:30 digest flagged a missed call (09:37, incoming, "talked 40s, no recording") as a lost recording. Root cause: two Python consumers judged "a real conversation" from talk‑seconds and the leg `result`, ignoring MyOperator's top‑level `status` (`bridged`/`missed`/`voicemail`) — which the receiver stores truthfully. A missed call's ring/hold time was mistaken for talk time. Full sweep of the whole call chain proved the fault was **contained to exactly two files**; everything else (receiver, archiver, transcription, verdict layer, all Apps Script) was already status‑correct.

**0.2 — Two live files fixed, gated, installed.**
- `flag_investigator.py` **v1.1 → v1.2** · md5 `a9baa6ca22055bb188d5c65b93c47ba1` · 51/51 selftest. `is_lost_candidate()` drops `missed`/`voicemail` rows; `diagnose()` adds `missed_no_conversation` for Search‑Logs `status "2"` and restricts `never_recorded` to `status "1"` + blank filename.
- `daily_digest.py` **v1.3 → v1.4** · md5 `f7e05ed2a79670667fda170f3b70b9d1` · 75/75 selftest. `classify_pending()` labels a `missed`/`voicemail` row "missed — no recording expected" (not an alert).
- Both: WinSCP → md5 match on VPS → `py_compile` → selftest → (digest) dry‑run clean. No cron change.

**0.3 — Re‑baseline proven.** Investigator results backed up (`…pre_f44.json`) and rebuilt: **`never_recorded_7d` 42 → 0**, `escalate_lokesh` True → False. The old 42 broke down as **42/42 `missed (status 2)`, 0 genuine `status 1`**. So MyOperator was not losing recordings — the detector was miscounting. **The standing "take the 42 to Lokesh" action is VOID.**

**0.4 — AI Verdict Layer Master written (D245).** `AI_Verdict_Layer_Master_v1_S145.md` — canonical. Compiled from artefacts (design spec, charter, live code, runbook, API ref). Carries the invariant + asymmetry, the data‑flow spine, the three axes, the two‑phase gate (D191), per‑script contracts with live md5s, the ground rules with scars, the decisions the layer stands on, the live snapshot, and a deliberately‑not‑carried list. **Supersedes** `AI_Review_Layer_Design_Spec_v1_1_S131.md`; **retires** `AI_Verdict_Layer_Master_CHARTER_S143.md`.

**0.5 — Decisions minted.** **D244** (recording‑gap detection keys off provider `status`, not talk‑duration). **D245** (Master written at S145; owner override of D242's timing gate). Finding **F‑44**.

**Fault‑code changes:** F‑44 raised + fixed. **Fault→Action Register:** unchanged — F‑44 is a fixed classifier bug, not an operational response‑lane fault; it lives in the KB, the incident file, and the Diagnostics Spec, not the response register. **Diagnostics Spec:** bumped v2.2 → v2.3 (the Investigator's classification refinement + the digest classifier). **Incident:** `INCIDENT_2026-07-14_RECORDING_GAP_MISLABEL_F44.md`.

**EOS doc batch:** KB v1.71, Umbrella v1.57, Diagnostics v2.3, and `START_HERE_SESSION_146` are the large consolidations produced in the EOS close — deliberately handed as their own verified batch so the 4,250‑line KB is complete and md5‑clean (D188/D202), never rushed.

---

## §1 — MENTAL MODELS (carry these into S146)

- **Duration is not talk time.** MyOperator's clock includes ring + hold. The connected‑vs‑missed truth is the top‑level `status` (`bridged` vs `missed`/`voicemail`), stored by the receiver. Any detector that reasons about "did we talk" must read `status`, not the seconds. (F‑44 / D244.)
- **The mislabel was contained; the data was sound.** The receiver stored the truth; only two *consumers* ignored it. When a metric looks alarming, first check its input signal means what the detector assumes.
- **"No content" verdicts are correct, not the fault.** `cant_communicate` on a genuinely connected call (hangup/silence/wrong number) is accurate. Missed calls never reach transcription or the verdict — they have no recording.
- **The Master is now the layer's truth.** For anything about the verdict pipeline — what a script owes, to whom, which tab, which rule, what breaks if it lies — read `AI_Verdict_Layer_Master_v1_S145.md`. The S131 design spec and the S143 charter are retired.
- **Proof is the artefact.** The 42→0 was proven by the backup's own `detail` text (42/42 missed), not by asserting it. (F‑41/F‑43 family.)

---

## §2 — OPEN BACKLOG (for Session 146)

### §2A — Owner actions (no code)
- **The "42 → Lokesh" item is VOID** — do not raise it. (Left here only to close the loop.)
- **Settle the follow‑up "came" window** (± days around the due date that count as returned) — the clinical‑judgement call still needed before insight #10 builds (D243).

### §2B — Next builds (gated, offline→md5→selftest→install)
1. **`call_verdict.py` cosmetic relabel (optional, deferred by owner‑recommended skip):** the AI prompt calls total call time "Talk duration"; feed the label "total call seconds (incl. ring)" instead. No verdict changes. Recommended to fold in the next time that file is opened for a real reason — not worth touching the live judge alone.
2. **Wire `daily_digest.py` to READ `flag_investigator_results.json`** (D236/§2C carryover): now that both are status‑correct, the digest's recording line can quote the Investigator's `never_recorded` vs `missed_no_conversation` split directly (single source of truth) instead of recomputing.
3. **D241 insights, order 10 → 1 → 2** (unchanged from S144): #10 two‑pipeline conversion (recon visit‑ledger + join key + diagnosis field; owner sets the return window; read‑only aggregate join). #1/#2/#3 as one `call_insights.py`.

### §2C — Standing
- **Lokesh items:** CALLHOOK secret rotation Steps 3–4, service‑account key rotation (Tier A1), AKEY_14 — all await Lokesh. *(The F‑44 Lokesh item is void, separate from these.)*
- **VPS venv Python 3.9 EOL** (Tier C) — google‑auth prints a harmless FutureWarning on every run; schedule a venv rebuild deliberately (it retests every pipeline).
- Hindi spelling corrections in `vitals_page.html` (content correct, spelling only).
- F‑37 health‑mail window · repo naming tidy · K toggle‑removal watch (arm when one‑tap usage >42% for 5 consecutive days).
- **Docterz export MIGRATION** — enhancement, not a blocker (D243).
- **A8/D223 doctor‑portal gist tile** — its #9 feeder is the Investigator's results file (now correct); build after the Investigator has run stably.
- **Cold backup** — due this EOS (KB + Umbrella bumped); produced in the EOS doc batch.

**Next free decision number: D246. Next free finding number: F‑45.**

---
**END OF HANDOFF RUNBOOK Session 145 v83.**
