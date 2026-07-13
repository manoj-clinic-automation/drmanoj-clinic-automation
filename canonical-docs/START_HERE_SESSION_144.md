# START HERE — SESSION 144 (written at Session 143 close, 13 Jul 2026)

Paste the standard opener; this file carries the session-specific state. Protocol unchanged.

## PHASE 0 — verify the canonical set (md5 of the artefact, never memory — D172/D188)

| Doc | Version | Expected md5 |
|---|---|---|
| Clinic_Master_KB_SystemsRegister_v1_69.md | v1.69 | `92b37b96d8a82f0c0e94a6186a01d462` |
| HANDOFF_RUNBOOK_2026-07-13_Session143_v81.md | v81 | `470df6eccb5b4a6e17e111b9249fe9d8` |
| Dr_Manoj_Clinic_Umbrella_Architecture_v1_55.md | v1.55 | `e2cc8dfc739cb269fe30dde0c3c049b4` |
| Call_Console_Evolution_Spec_v2_4.md | v2.4 | `63978d982d1f8037f728023d15a01328` |
| Clinic_Callback_Tracker_AppsScript_Audit_v1_9.md | v1.9 | `41dd9fd6b607e59e15e3e646b775d640` |
| Frontend_Dashboard_Documentation_v4_S140.md | v4 | `02ef929b75aa77ec071c903705335375` |
| API_QUICK_REFERENCE_CARD.md | S137 | `68c4fc344bf74caaea706149cd22e64c` |
| WABA_Approved_Templates_v1_S137.md | v1 | `63dd1883ed6677bc96620c087fc1d154` |
| Diagnostics_Surveillance_System_Spec_v2_1.md | v2.1 | `7a9e83b436c39fde08118437acbbfafe` |
| Maintenance_SOP_System_Spec_v1_1.md | v1.1 | `35b257ee0c59ff2e4ba9820a6ac64d37` |
| INCIDENT_2026-07-13_CRON_UTC_F41.md | S142 | `d253b5f16b8d423e4759bac74b9e6c5e` |

Absent-check: no KB ≤ v1.68, no Runbook ≤ v80, no Umbrella ≤ v1.54, no START_HERE_SESSION_143.

**PHASE 0b — live-file truth (S143 changes):** `verdict_review.py` **v3-S143**
(`280eb2cef9295d89f30c7b84d4c94adb`, 1,837 lines, selftest 144/144) · `call_verdict.py` v2.1+F-40-fix
(`539ea68fb4ce99f0029fdbb53bbf8ebe`, 42/42, logic byte-identical to S141 v2.1) · `daily_digest.py`
**v1.3-S143** (`63a558d2a73dc5ec22ea8bb772869353`, 74/74) · NEW `make_force_keys.py` v1.1 (one-off,
`9b44831a0a2a2003fac5c4901f7da35c`) · NEW `force_keys.txt` (41 keys) · crontab +1 (`0 21` review
redraw). **Data truth at close:** `Call_Verdicts` 586+ and growing · `Doctor_Verdicts` **18 rows (18/100
toward the D191 gate; 89% raw agreement)** · `Verdict_Review` 9,240 rows / 371 cards + 25 open band
cards. **Repo truth: the S142 commits were verified by hash, but ALL FOUR S143 files + docs are now owed**
(git kit zip was delivered at S143 close) — verify repo==live by md5 before trusting any repo file (D160).

## PHASE 1 — session-start priorities
1. **Collect the overnight proofs (FOUR):** 21:00 `verdict_review_cron.log` shows a clean scheduled
   redraw · 21:30 digest arrived (first cron-fired; spam-check once; its spot-check pair == the tab's; its
   suggestion line carries the six F-42 calls) · 08:45 `/root/wa/call-hook/write_probe.log` exists (first
   real scheduled PASS) · 11:00 pulse fired by cron.
2. **Build: Flag Investigator (D239) + F-42** — one build. Recon FIRST, from artefacts: (a) session_id in
   `Call_Durations` vs derived from `client_ref_id`; (b) Call API search shape from
   `MyOperator_Call_API_Master_Reference_23_june_.md`; (c) hook-log kick trail for the six 13-Jul events
   (incl. the odd-shaped `1206138695`). Locked defaults: self-heal ON · 30-min 09:00–20:00 · results file
   the digest READS · ≥3 never-recorded/week → Lokesh line.
3. **GitHub commits owed** (four files + S143 docs; kit staged).
4. Owner continues the referee sitting (23 open cards; nothing re-asked).
5. Standing per Runbook §2C — note the two NEW entries: VPS venv Python 3.9 EOL (Tier C) and the D241
   register (its #10 is the argument for closing the Docterz decision).
