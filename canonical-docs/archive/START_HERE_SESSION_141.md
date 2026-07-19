# START HERE — SESSION 141 (written at Session 140 close, 12 Jul 2026)

Paste the standard opener; this file carries the session-specific state. Protocol unchanged.

## PHASE 0 — verify the canonical set (md5 of the artefact, never memory — D172/D188)

| Doc | Version | Expected md5 |
|---|---|---|
| Clinic_Master_KB_SystemsRegister_v1_66.md | v1.66 | `7142e525f0b76bd226c4607b5a45f9db` |
| HANDOFF_RUNBOOK_2026-07-12_Session140_v78.md | v78 (amended, +§0.6) | `e9947d5a55f6ecb2ba5fa4247348c359` |
| Dr_Manoj_Clinic_Umbrella_Architecture_v1_52.md | v1.52 | `1c9b4875187517be52089e2ed536b89f` |
| Call_Console_Evolution_Spec_v2_4.md | v2.4 | `63978d982d1f8037f728023d15a01328` |
| Clinic_Callback_Tracker_AppsScript_Audit_v1_9.md | v1.9 | `41dd9fd6b607e59e15e3e646b775d640` |
| Frontend_Dashboard_Documentation_v4_S140.md | v4 | `02ef929b75aa77ec071c903705335375` |
| API_QUICK_REFERENCE_CARD.md | S137 | `68c4fc344bf74caaea706149cd22e64c` |
| WABA_Approved_Templates_v1_S137.md | v1 | `63dd1883ed6677bc96620c087fc1d154` |
| Diagnostics_Surveillance_System_Spec_v2_1.md | v2.1 | `7a9e83b436c39fde08118437acbbfafe` |
| Maintenance_SOP_System_Spec_v1_1.md | v1.1 | `35b257ee0c59ff2e4ba9820a6ac64d37` |

Absent-check: no KB ≤ v1.65, no Runbook ≤ v77, no Umbrella ≤ v1.51, no Console ≤ v2.3, no Audit ≤ v1.8,
no Frontend ≤ v3, no START_HERE_SESSION_140, no SESSION_140_NOTES_for_EOS.

**PHASE 0b — live-file truth (no fresh editor export yet; both Apps Script files changed S140):**
Dashboard **v18.28f** (`d528e666b258d1faf958e890e691d68a`) · Callconsole
**v1.7** (1,224 lines, `b1d49c6227ba16d0e7a57340a03d1a31`); the other 12 project files keep their `__7_`
export-form hashes. **VPS truth (S140 installs, backups `.bak_s139`):** `call_hook_capture.py` **v3.1**
(894 lines, `b8a1a293c54dfb6528e04fdf31f8d3e6`) · `call_pipeline_worker.py`
(`3c8be7f0f6f5960103fb1ed586c48cce`) under `call-pipeline.service`
(`273c578cf5ce4b2988d62e47cd0ddeec`, enabled --now) · `callhook_write_probe.py`
(`705bd4a1d82068b1ccc74a2567e2ac67`, 08:45 cron) · `call_verdict.py` **v2**
(`b7dc12613ae24afee41fdc8bd6910480`, 03:40 cron) · `verdict_review.py` **v2**
(`13e7618e563202b236659249fdacdeee`) · `wa_send_api.py` v3 unchanged.
**Repo state:** all 8 S140 code files committed to `main` and hash-verified from the tarball at EOS —
**repo == live for these 8 files** (D160 still the rule; a pre-v78-amend runbook copy with md5
`4d68d13b86d8129db0f4b95429192875` is STALE — reject it).

## PHASE 1 — reads at session start (MONDAY 13-JUL IS THE FIRST LIVE MORNING)
1. **K-1 first real staff tap** — five buttons on gate-resolve; one tap files; `source='K'` row lands.
2. **K-2 first incoming taps** — known-patient K buttons AND (if an unknown calls) the 7-button lead set;
   🌱 band populates.
3. **F-10 incoming tap** — first MISSED incoming, old "Log outcome ▾" opens and saves.
4. **Pipeline live on a natural call** — kick visible in `journalctl -u call-pipeline`; verdict lands in
   minutes; `verdict_cron.log` shows the 03:40 floor ran.
5. **Write-probe first scheduled PASS** ~08:45 in `/root/wa/call-hook/write_probe.log`.
6. **CALLHOOK weekday status** — `bash /root/wa/rotate_callhook.sh status`; clean AND calls flowed →
   Steps 3–4 with Lokesh (panel update, then clear PREV).
7. D183 digest count from 12-Jul ~21:30 = exactly ONE · D212 WA tile · quota mail (~09:43) second
   baseline point (watch K-2's read delta; expected ~zero — one-read merge).
8. Start the **K-usage counter** toward the 42 %×5-day toggle-removal rule (D228).

## PHASE 2 — pick ONE build (nothing owner-blocked)
- **A8 / Pass 6 — the D223 doctor-portal gist tile** (NEXT by plan; every S140 pass produced its data).
- **A3 — seen-today WABA** (relay half live; Docterz trigger + send loop remain; VPS scope).
- **Docterz clinical-data export migration** (blocked on one owner decision: follow-up column handling).

Standing/carried/parked: Runbook v78 §2 (B and C blocks). F-37 still open. AKEY_14 + service-account
key rotation parked (Tier A1). ClickUp parked (D17).
