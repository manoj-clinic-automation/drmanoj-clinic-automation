# START HERE — SESSION 137

**Project:** Dr. Manoj Agarwal Clinic automation · Bareilly · Owner: Dr. Manoj Agarwal
**Last session:** 136 (11 Jul 2026) — THREE deploys, all live-verified: Block C (bundle + one clock + quota
gauge) · F-36 escalation-card fix · WA call line · F-4/Block E closed · D183 sweep armed.

---

## PHASE 0 — VERIFY THE DOCUMENT SET (md5 of each file in project knowledge; any mismatch → STOP, reconcile)

| Document | Expected md5 |
|---|---|
| Clinic_Master_KB_SystemsRegister_v1_62.md | `26fae0f8fc0659a90f051e0dbae0a4cd` |
| HANDOFF_RUNBOOK_2026-07-11_Session136_v74.md | `7a17f285c261173ed2dc67e3e8f3cae6` |
| Dr_Manoj_Clinic_Umbrella_Architecture_v1_48.md | `7fa7ae2251996bdc4c5f38ac1606903b` |
| Clinic_Callback_Tracker_AppsScript_Audit_v1_7.md | `90539cb107ecb53adfe518a7eb00f8d8` |
| Call_Console_Evolution_Spec_v2_1.md | `3b29097c02eaa5397281ab5ec37dc8fc` |

Unchanged set (presence check is enough): API_QUICK_REFERENCE_CARD · Diagnostics_Surveillance_System_Spec_v2_1 ·
Maintenance_SOP_System_Spec_v1_1 · Frontend_Dashboard_Documentation_v2_S134 (**stale in read-path — v3 pending**)
· END_OF_SESSION_PROMPT_v3 · AI_Review_Layer_Design_Spec_v1_1_S131 · Fault_Action_Register_v2_1.
**Absent check:** no KB ≤1.61 · no Runbook ≤v73 · no Umbrella ≤1.47 · no Audit ≤1.6 · no Console Spec ≤2.0 ·
no START_HERE_136 · no Frontend v1 (S130) · no `Clinic_Callback_Tracker__6_.json` or older.

## PHASE 0b — VERIFY THE LIVE-EDITOR EXPORT

Current truth is **`Clinic_Callback_Tracker__7_.json`** (post-deploy-3, byte-verified in S136).
If it is still the export in project knowledge, re-verify it against this table. If the owner uploads a
fresher export (`__8_`), verify THAT against this table instead — any diff = someone edited the editor.

**HASHES ARE EXPORT-FORM: md5 of each file's source after `rstrip('\n')`.** (KB §S136.4 — the editor strips
the final newline; a one-trailing-newline difference is NOT drift.)

| File | Export-form md5 |
|---|---|
| Callconsole (v1.5) | `4c15e7a5e0ffdaa03f4274b4f947a4d5` |
| Dashboard (v18.25) | `f38aa92e7ec2289de896640709c0fc8a` |
| Health (v2.3) | `83ebfc51ebb74d7025903efb063b0187` |
| appsscript (no `documents` scope) | `7ad6f2fe7f788f5f5a830e697a140030` |
| WebApp (FROZEN, D34) | `5173c3c7a9d58e091fa8a49ee97522c9` |
| OutcomeLog | `07d05cf214543970266b6e30fcadeffe` |
| Main | `1a85166c72c624c3fa5533a3cf02c4c9` |
| config | `6107ca1a44bee57000c89b23befebd48` |
| MyOperator | `b31f47a762fabe43bad92c1b9661db07` |
| Sheets | `04242868b4a121967d781e9a3fc86b14` |
| Netting | `bce5a036d0180361f4b2f16d7052d6cf` |
| Monitor | `0884d2d310444f5e33940877ccd42a7b` |
| Diagnostics | `40d3f019d17a4f94ebddb063ebca8198` |
| CallField.gs | `11979c19f48d543e90cfa7a664410c29` |

**`Probe` must be ABSENT** (deleted S136, Block E).

## PHASE 0c — VPS RITUAL (owner runs, pastes output)

```
bash /root/wa/rotate_callhook.sh status
```
Read it properly (S136 lesson): **"0 on PREVIOUS key/30min" is evidence ONLY if calls flowed in the window**
— compare "accepted today" against the last reading. Weekday-morning check is the decisive one for Step 3.

## PHASE 1 — READ
Runbook v74 §0 (what happened) → §2 (backlog) → KB §S136. Note the QUOTA HEADROOM line in the latest 08:00
health mail — first real read of the Block C gauge — and whether the 21:30 D183 digest arrived automatically
on 11-Jul night (it should have; manual run was verified, the trigger itself was not yet observed firing).

## PHASE 2 — RECOMMENDED BUILD (owner confirms or redirects)

**Three owner answers unblock the most — collect first if still open:**
1. **D205** — which WABA template do seen-today patients get?
2. **§K wording** — approve/edit: मरीज़ आ रहे हैं · नहीं आएँगे · बात हुई — फिर call करना · बात नहीं हो पाई · डॉक्टर को दिखाना है
3. **Third attempt:** D78 (auto-drop + WABA + snooze) **vs** D195 (send to doctor) — one must win.

**Recommended build = Block D, part A1:** VPS `call_hook_capture.py` stops discarding incoming calls (F-19).
Session-start design decisions required BEFORE code: row key for incoming (no `client_ref_id` exists) and the
PHI rule (the tab stores no phone number today). Full VPS discipline: offline build → `py_compile` (VPS venv
`/root/wa/venv/bin/python3`) → selftest → WinSCP + md5 → restart → status. One build per session.
If owner answers Q2+Q3 early, §K may be designed the same session (design ≠ build).

**Standing protocol unchanged:** one step at a time · full files only · secrets masked · nothing live rebuilt
without explicit OK · py_compile/node --check before install · deploys = New version on the EXISTING deployment.
