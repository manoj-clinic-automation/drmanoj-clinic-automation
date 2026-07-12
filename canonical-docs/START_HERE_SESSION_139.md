# START HERE — SESSION 139 (written at Session 138 close, 12 Jul 2026 morning)

Paste the standard opener; this file carries the session-specific state. Protocol unchanged:
plain language · ONE step at a time · full-file replacements · secrets masked · nothing live
rebuilt without owner OK · offline build → py_compile → owner installs · VPS python =
`/root/wa/venv/bin/python3`.

---

## PHASE 0 — verify the canonical set (md5 of the artefact, never memory — D172/D188)

| Doc | Version | Expected md5 |
|---|---|---|
| Clinic_Master_KB_SystemsRegister_v1_64.md | v1.64 | `cc4265dda4856fb2ce439347d0c181ca` |
| HANDOFF_RUNBOOK_2026-07-12_Session138_v76.md | v76 | `08988cf94b5e6ee48cfbd508b7d979e6` |
| Dr_Manoj_Clinic_Umbrella_Architecture_v1_50.md | v1.50 | `21a3b3560bc01bf37a356252fde8deff` |
| Call_Console_Evolution_Spec_v2_2.md | v2.2 | `58e18234a6f98d3f1e4fc5fa918628ee` |
| API_QUICK_REFERENCE_CARD.md | S137 | `68c4fc344bf74caaea706149cd22e64c` |
| WABA_Approved_Templates_v1_S137.md | v1 | `63dd1883ed6677bc96620c087fc1d154` |
| Clinic_Callback_Tracker_AppsScript_Audit_v1_7.md | v1.7 | `90539cb107ecb53adfe518a7eb00f8d8` |
| Diagnostics_Surveillance_System_Spec_v2_1.md | v2.1 | `7a9e83b436c39fde08118437acbbfafe` |
| Maintenance_SOP_System_Spec_v1_1.md | v1.1 | `35b257ee0c59ff2e4ba9820a6ac64d37` |

Presence also expected: Frontend Doc v2 (`c03cb71dee06155aee00ed0baa591d80`, stale read-path, v3 pending),
END_OF_SESSION_PROMPT_v3, templates snapshots, export `Clinic_Callback_Tracker__7_.json`.
Absent-check: no KB ≤ v1.63, no Runbook ≤ v75, no Umbrella ≤ v1.49, no START_HERE_SESSION_138.

**PHASE 0b — live-editor export:** verify against `__7_.json` export-form hashes (14 files, Probe absent)
unless a fresher export appears. **No Apps Script changed in S138** — the S136 hashes still hold.

**VPS live-file truth (changed S138):** `call_hook_capture.py` v3.0.1 — 827 lines, md5
`b64aee2b7b0bcc986a72e5e4f176a86c` · `backfill_call_durations.py` — 131 lines, md5
`974ae54952dbc235e5cc6af107e83eeb`.

## PHASE 1 — reads at session start (time-gated items from S138)

1. **QUOTA HEADROOM first read** — the Apps Script health mail (~09:43 IST); first real Block C gauge.
2. **D183 arrival count** — the ~21:30 digest on 12-Jul: exactly ONE = trigger healthy; TWO = duplicate
   trigger to remove.
3. **D212 WA-tile** — first natural WhatsApp-origin call verifies it.
4. **Phase 1b (weekday only):** `bash /root/wa/rotate_callhook.sh status` during traffic — 11-Jul WARN
   lines proved the panel still on the OLD key; if Monday's check is clean AND calls flowed → Step 4.
5. **New-data spot check (30 s):** confirm fresh `IN-` rows keep appearing in `Call_Durations` (first
   natural incoming call after 08:25 12-Jul proves v3.0.1 end-to-end in production traffic).

## PHASE 2 — pick ONE build (nothing owner-blocked)

- **A2 — §K K-1 one-tap staff UI** (Console Spec v2.2 §K.6; design complete; includes F-34 residue;
  K-2 now unblocked; natural moment for Frontend Doc v3).
- **A3 — D205/D213 seen-today WABA** (half-session; `wa_approve` scope; `drmanoj_post_visit`).
- **A4 — F-10 markup cure** (own commit; ~24 fragile sites).
- **A5 — incoming-verdict design pass** (new S138: verdict layer learns `IN-` rows; retires F-18's
  stale exemption; design first).

Standing/carried and parked items: Runbook v76 §2 (B and C blocks).
