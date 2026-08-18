# START HERE — Session 147

Paste this at the top of the next session. Dr. Manoj Agarwal Clinic, Bareilly. Working protocol unchanged (plain language · one step at a time · full-file replacements · mask secrets · manual fallback stays · offline→`py_compile`(`python`)→owner installs · VPS python = `/root/wa/venv/bin/python3`).

---

## PHASE 0 — verify the canonical docs by md5 BEFORE any work (D172/D188)

| Doc | expected md5 |
|---|---|
| `Clinic_Master_KB_SystemsRegister_v1_72.md` | `27b72639de7267ccf52765d2e0ce0e58` |
| `HANDOFF_RUNBOOK_2026-07-14_Session146_v84.md` | `4da9e09f394b8d11a9da77d162164971` |
| `Dr_Manoj_Clinic_Umbrella_Architecture_v1_58.md` | `728cc64950502011ff220e1249e488ce` |
| `Call_Console_Evolution_Spec_v2_4.md` | `63978d982d1f8037f728023d15a01328` |
| `Clinic_Callback_Tracker_AppsScript_Audit_v1_9.md` | `41dd9fd6b607e59e15e3e646b775d640` |
| `Frontend_Dashboard_Documentation_v4_S140.md` | `02ef929b75aa77ec071c903705335375` |
| `API_QUICK_REFERENCE_CARD.md` | `68c4fc344bf74caaea706149cd22e64c` |
| `WABA_Approved_Templates_v1_S137.md` | `63dd1883ed6677bc96620c087fc1d154` |
| `Diagnostics_Surveillance_System_Spec_v2_3.md` | `bdd5fa5479a57dfb73fa653054a3f329` |
| `Maintenance_SOP_System_Spec_v1_1.md` | `35b257ee0c59ff2e4ba9820a6ac64d37` |
| `AI_Verdict_Layer_Master_v1_S145.md` | `bd4b67f6810cd2316eb58dfe6bf180cd` |
| `INCIDENT_2026-07-14_RECORDING_GAP_MISLABEL_F44.md` (latest incident on record) | `774898e80fac3e006d80e8c2f77488e6` |

**Absent-check:** superseded copies should NOT be present — KB ≤ v1.71, Runbook ≤ v83, Umbrella ≤ v1.57, and `START_HERE_SESSION_146`. Remove any that remain. (No new incident this session — F-44 remains the latest on record.)

**Next free decision number: D247. Next free finding number: F-45.**

---

## PHASE 1 — WHERE WE ARE (S146 closed, FULL EOS)

**A callback-tracker FINALISATION session. B1 shipped and the product architecture was named.**
- **B1 LIVE:** `daily_digest.py` **v1.5** (md5 `0a4ee35b5fb7fbc0570efe3bc0cdde88`, 83/83) — the 21:30 digest now READS `flag_investigator_results.json` and quotes the Investigator's rolling `never_recorded` / `missed_no_conversation` split + `escalate_lokesh` in a new **"Recording health"** section. ONE source of truth, no recompute; fail-loud on a missing/unreadable/stale (>20 h) file; additive only; read-only (D236). Proven by a live dry-run against real data; no cron change.
- **D246 minted — the three-product lineage:** Followup Tracker (clinic PC, offline — source) → Callback Tracker (VPS — Product A, system of record) → Call Intelligence (VPS `recordings-archive` — Product B, analytics). Two of the three seams are contracts; the **Followup→Callback** seam is the one still to name (the Docterz migration lives there).
- **B2 windows captured + parked** for the #10 build: outgoing follow-ups → learn the return window per diagnosis from ~5 weeks; incoming leads + missed-call callbacks → flat 3-day.
- **Housekeeping:** the KB's absent v1.71 changelog entry was backfilled; the Umbrella's orphaned v1.57 entry relocated into its CHANGELOG block.

---

## PHASE 2 — FIRST WORK (from Runbook §2; pick with the owner)

**Owner actions (no code):** the follow-up "came" window is now CAPTURED via B2 — no standing decision pending; the residual is build-time recon for #10.

**Builds (gated · offline→md5→selftest→install):**
1. **D241 insights, order 10 → 1 → 2.** #10 recon first (visit-ledger + join key + diagnosis field/mapping — the `Orthopedic_Diagnosis_Taxonomy_Master` may be the grouping source), then a read-only VPS-side aggregate join reporting the two funnels separately (D243); one owner call may surface on diagnosis grouping. #1/#2/#3 = one `call_insights.py`.
2. **Optional digest tightening (deferred):** the 20 h stale guard doesn't catch an afternoon stall (a 09:00 file at 21:30 is ~12 h old → still "ok"); a one-line tightening (e.g. 4 h) would. Fold in next time the digest is opened.
3. **`call_verdict.py` cosmetic relabel** — still recommended to SKIP until that file is opened for a real reason.

**Standing:** GitHub commit owed for `daily_digest.py` v1.5 (this file was the overdue-commit flag) · Lokesh items (CALLHOOK 3–4, SA-key, AKEY_14) · Python 3.9 EOL venv rebuild (Tier C) · Hindi spellings · F-37 · repo naming · K toggle watch (>42% for 5 days) · A8/D223 gist tile (feeder now stable) · Docterz export MIGRATION (the Followup→Callback seam; D243/D246).

---
**END OF START_HERE — Session 147.**
