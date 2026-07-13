# START HERE — SESSION 143 (written at Session 142 close, 13 Jul 2026)

Paste the standard opener; this file carries the session-specific state. Protocol unchanged.

## PHASE 0 — verify the canonical set (md5 of the artefact, never memory — D172/D188)

| Doc | Version | Expected md5 |
|---|---|---|
| Clinic_Master_KB_SystemsRegister_v1_68.md | v1.68 | `f851e12d6ffcfd6fd8b95b544ab20456` |
| HANDOFF_RUNBOOK_2026-07-13_Session142_v80.md | v80 | `d8e5ebd895998d766e762ed3bff27dc1` |
| Dr_Manoj_Clinic_Umbrella_Architecture_v1_54.md | v1.54 | `be57d22bfc66d8ab06ec683c8dcdd85b` |
| Call_Console_Evolution_Spec_v2_4.md | v2.4 | `63978d982d1f8037f728023d15a01328` |
| Clinic_Callback_Tracker_AppsScript_Audit_v1_9.md | v1.9 | `41dd9fd6b607e59e15e3e646b775d640` |
| Frontend_Dashboard_Documentation_v4_S140.md | v4 | `02ef929b75aa77ec071c903705335375` |
| API_QUICK_REFERENCE_CARD.md | S137 | `68c4fc344bf74caaea706149cd22e64c` |
| WABA_Approved_Templates_v1_S137.md | v1 | `63dd1883ed6677bc96620c087fc1d154` |
| Diagnostics_Surveillance_System_Spec_v2_1.md | v2.1 | `7a9e83b436c39fde08118437acbbfafe` |
| Maintenance_SOP_System_Spec_v1_1.md | v1.1 | `35b257ee0c59ff2e4ba9820a6ac64d37` |
| INCIDENT_2026-07-13_CRON_UTC_F41.md | S142 | `d253b5f16b8d423e4759bac74b9e6c5e` |

Absent-check: no KB ≤ v1.67, no Runbook ≤ v79, no Umbrella ≤ v1.53, no START_HERE_SESSION_142.

**PHASE 0b — live-file truth (S142 changes):** NEW `daily_digest.py` **v1.2.1-S142** at
`/root/wa/recordings-archive/` (`e6df21cce507bd2d4e60dd9c5644b008`, selftest 72/72, read-only by
construction) · crontab +2 (`0 11` pulse · `30 21` digest) · **crond restarted 11:16:58 IST 13-Jul
(F-41 cure, canary-proven)** — all pre-existing crons now fire at true IST for the first time ·
`/root/wa/.env` +3 `DIGEST_` lines. Unchanged: `call_verdict.py` v2.1 (`9cb454e9…`) ·
`verdict_review.py` v2 (banner still lies "v1.3" — F-40 open) · hook v3.1 / worker / probe /
wa_send_api v3 · Apps Script Dashboard v18.28f + Callconsole v1.7.
**Data truth:** `Call_Verdicts` 566 rows at close and growing · `Verdict_Review` **8,845 rows /
378 cards (21-day window)** · `Doctor_Verdicts` 0.
**Repo truth (verified by hash S142):** repo `call_verdict.py` is STILL **v1.0-S128**
(`b7dc12613ae24afee41fdc8bd6910480`) — v2.1 commit never pushed; `daily_digest.py` has no repo copy.
Both commits owed; verify repo==live by md5 before trusting any repo file (D160).

## PHASE 1 — session-start priorities
1. **Collect the overnight proofs:** 21:30 digest arrived (first cron-fired; spam-check once) — did its
   suggestion line carry the F-42 calls? · 08:45 write-probe log exists this morning
   (`/root/wa/call-hook/write_probe.log`) — its first REAL scheduled PASS · 11:00 pulse fired by cron.
2. **Build 1: `verdict_review.py` enhancement** — force-draw full answer cards for a supplied key list
   (+ cap handling for supplied keys). Unblocks the 41-card D237 sitting (owner: Option B) AND gives the
   daily 2-spot-checks a landing cell. Then the owner referees the 41 (`D237_Referee_Set_S142.xlsx`,
   seed `D237-S142`).
3. **Build 2: Flag Investigator (D239) + F-42 investigation** — same work: MyOperator Call API by
   session_id → self-heal or label; hook-log kick check; results file the digest reads. Owner defaults
   locked: self-heal ON · 30-min 09:00–20:00 · ≥3/week provider-never-recorded → digest says call Lokesh.
4. **F-40 three one-liners** ride the same VPS touch. **GitHub commits owed** (call_verdict v2.1 +
   daily_digest v1.2.1 + S142 docs).
5. Standing security items per Runbook §2C. Watch: ai-only bucket shrinking (K-adoption) · F-42 pattern
   count once the Investigator runs.
