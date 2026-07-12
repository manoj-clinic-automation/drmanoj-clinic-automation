# START HERE — SESSION 140 (written at Session 139 close, 12 Jul 2026)

Paste the standard opener; this file carries the session-specific state. Protocol unchanged.

## PHASE 0 — verify the canonical set (md5 of the artefact, never memory — D172/D188)

| Doc | Version | Expected md5 |
|---|---|---|
| Clinic_Master_KB_SystemsRegister_v1_65.md | v1.65 | `3707a7f60f15482ee5f2a3f3daa9ec1d` |
| HANDOFF_RUNBOOK_2026-07-12_Session139_v77.md | v77 | `632e60d0d8dcdd7a6deca6e9912beb78` |
| Dr_Manoj_Clinic_Umbrella_Architecture_v1_51.md | v1.51 | `8f8b66b2e4c66ce41a6c60352a109dc4` |
| Call_Console_Evolution_Spec_v2_3.md | v2.3 | `360163785bd071f933a720698b68ca66` |
| Clinic_Callback_Tracker_AppsScript_Audit_v1_8.md | v1.8 | `567f3ac2e0a4aef30236568dc4c8ddf2` |
| Frontend_Dashboard_Documentation_v3_S139.md | v3 | `1652d626184cb11980b5c01e2c8b982d` |
| API_QUICK_REFERENCE_CARD.md | S137 | `68c4fc344bf74caaea706149cd22e64c` |
| WABA_Approved_Templates_v1_S137.md | v1 | `63dd1883ed6677bc96620c087fc1d154` |
| Diagnostics_Surveillance_System_Spec_v2_1.md | v2.1 | `7a9e83b436c39fde08118437acbbfafe` |
| Maintenance_SOP_System_Spec_v1_1.md | v1.1 | `35b257ee0c59ff2e4ba9820a6ac64d37` |

Absent-check: no KB ≤ v1.64, no Runbook ≤ v76, no Umbrella ≤ v1.50, no Console ≤ v2.2, no Audit ≤ v1.7,
no Frontend ≤ v2, no START_HERE_SESSION_139.

**PHASE 0b — live-editor export:** the `__7_` export is now STALE for `Dashboard` and `Callconsole`
(both changed S139). Until a fresh export is supplied, live-file truth is: Dashboard **v18.27**
(2,988 lines, `4e73682242a34d167c86e8a72a941854` as built) · Callconsole **v1.6** (1,128 lines,
`eb91034961a20545b5316b144f86075a` as built); the other 12 files keep their `__7_` export-form hashes.
**VPS truth:** `wa_send_api.py` v3 `a3ed37080aaec940226c98bf0d2c7e04` · `/root/portal/portal.py` patched
(backup `portal_BACKUP_S139_pre_https.py`) · `call_hook_capture.py` v3.0.1 unchanged.

## PHASE 1 — reads at session start (MONDAY IS THE VERIFICATION MORNING)
1. **K-1 first real staff call** — five buttons appear on gate-resolve; one tap files; undo works;
   `Followup_Outcomes` row has `source='K'`.
2. **F-10 incoming tap** — first incoming tile, "Log outcome" on a known patient opens and saves.
3. **CALLHOOK weekday status** — `bash /root/wa/rotate_callhook.sh status` during traffic; clean AND calls
   flowed → Step 4.
4. **D183 arrival count from 12-Jul ~21:30** — exactly ONE.
5. **First weekday natural `IN-` row** in `Call_Durations` · WA-tile D212 on first WhatsApp-origin call.
6. Quota mail (~09:43): second baseline point; watch for K-1's read delta (expected negligible).

## PHASE 2 — pick ONE build (nothing owner-blocked)
- **A6 — K-2 incoming one-tap** (G-1, the biggest lifecycle hole; machinery all exists).
- **A3 — seen-today WABA** (relay half live; VPS trigger+loop remain).
- **A5 — incoming-verdict pass** (retire F-18 + fix D158 + arm the Stage-3 timer).
- **A7 — D200 per-call recording download + F-38 write-probe.**

Standing/carried/parked: Runbook v77 §2 (B and C blocks).
