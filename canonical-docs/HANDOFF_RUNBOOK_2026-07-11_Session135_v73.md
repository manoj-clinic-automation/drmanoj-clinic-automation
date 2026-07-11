# HANDOFF RUNBOOK — 11 July 2026 — Session 135 — v73
**Dr. Manoj Agarwal Clinic · Bareilly · Orthopaedic surgery · Solo practice**
**Session type: FULL EOS — two Apps Script deploys the same day (v18.22 then v18.23: `Callconsole.gs`, `Dashboard.html`, `OutcomeLog.gs`), two PC files changed + one added (`push_patient_mirror.py`, `processor.py`, `clean_visit_ledger_junk.py`), mirror re-pushed (7,407 rows), visit ledger cleaned (831→829). No D34 waiver — `WebApp.gs` untouched. Supersedes v72.**

> **v73 — the owner caught it on one tile.** Raj Rani's follow-up showed **Ekta's Clinic ID and Ekta's
> last-visit date** — one root cause (mirror collapsed families to one row per phone; dashboard painted
> that row onto every relative), two symptoms, **zero corrupted records**. **F-34 raised and CLOSED the
> same day (D208)**: mirror keyed by UID, dashboard enrichment name-aware, "ID ⚠ verify" beats a guess.
> Live-verified: Raj Rani = **7361 · 04-Jul**; J P Singh / Manjeet Kaur no longer share an identity.
>
> **The Session-35 drawer finally opened (F-35/D209).** Review-console SEND BACKs now return to staff
> as tiles carrying the doctor's note, retiring on any newer outcome or an APPROVED re-review. Tested
> on the day's real 13 outcome rows; live-verified on four tiles (reception login).
>
> **Ingest evidence rules (D210):** single-mobile matches are name-checked (demote to Medium + visible
> issue — never off the call sheets); only UID-shaped rows enter the pipeline; the 09-Jul "Credit Card"
> footer leak is out of the ledger with a backup beside it, and the guard makes the class extinct.
>
> **The clinical data report is a strict superset** — verified header-by-header against the code.
> Migration designed, deliberately unbuilt; the follow-up log keeps its Appointment-ID spine.
>
> One assistant error on the record: a from-memory claim (F000562 "should still be listed") disproved
> by the morning workbook — never issued. **D172 restated and obeyed thereafter.**

---

## §0 — WHAT HAPPENED THIS SESSION

### 0.1 The incident and its anatomy (F-34)
Owner: "Raj Rani listed as follow-up, but her clinic ID is a different patient's" — later, "her last
visit is actually her first visit." Chain established from artefacts: Docterz exports agree Raj Rani =
7361 across three visits (05-Jun, 16-Jun procedure, 04-Jul); mobile shared with Ekta = 7362.
`push_patient_mirror.py` kept **one row per phone** ("last occurrence"), so only Ekta reached the
`Patient_Master` tab; `Callconsole.gs` D52 enrichment ("first wins" per phone) painted Ekta's ID and
last-visit onto Raj Rani's tile. The "first visit" was Ekta's last. The staff Excel (no ID column),
ledger, and settle engine were never wrong.

### 0.2 The fix, in dependency order (all live)
1. `push_patient_mirror.py` — one row per **Patient UID**: `d3105f6901700bad5300ea61b014a102`. Re-pushed: 7,407 patients,
   Last Visit ← `Last_Seen_Date` (correct), Diagnosis/Age/Gender blank (master lacks them; migration item 5).
2. `Callconsole.gs` **v1.3** — `cc_patientMultiMap_` + `cc_fuEnrich_` (name match ≥ 0.7, PC rule);
   unique mobiles keep the plain key so stale pages degrade to blank, never wrong: `44330498575dc5b46f6ed623445d05c2`.
3. `Dashboard.html` — `fuLookup` at six sites; "ID ⚠ verify" on unmatched shared mobiles.
Simulation passed on the real cases before install; live verification: Raj Rani 7361 · 04-Jul,
four sent-back tiles (see 0.3), J P Singh 7342 vs Manjeet Kaur 7614 confirmed by design.

### 0.3 F-35/D209 — the S35 loop closer (deploy 2, v18.23)
`getReviewSendbacks` (OutcomeLog.gs `9fc4c941bc067a40ce43eb40e8e81376`): latest 'SEND BACK' per Key → Session-52-shaped tile
with the doctor's note; retires on newer outcome or APPROVED overwrite. Page merge idempotent
(`_rsb` strip + `_sbBase` count guard), duplicates deferred to existing tiles. `Dashboard.html` v18.23
`132d62579702b5c651347af97dea2c03`. Live: Shashi Sahu, Rajni Saxena ("Call again"), J P Singh ("Galat outcome likha
hai"), Raj Rani ("Kab dikhaya tha…") all visible on reception mobile. One-writer rule intact (reader only).

### 0.4 D210 — processor hardening + ledger cleanup
`processor.py` (pre-install gate: owner's live file hash-matched base `171a0906…`; installed
`0e7c129f57b53fca2cb21ba6dcd4d381`): single-match name check (mismatch → **Medium** + "Name differs from registered owner
(…) — verify"; Medium passes every issuance filter — a demotion may never un-list a patient; the
mobile-keyed diagnosis fallback is deliberately lost on mismatch); UID-shape guard `[A-Z0-9]{8,14}`
at `parse_consultation_report`. `clean_visit_ledger_junk.py` (`535af72132149cd76bfd750417c7e8eb`): preview → `--apply` →
V000819 ("Credit Card") + V000820 ("0/7400") removed, 831→829, backup written, re-run shows 0 junk.

### 0.5 Clinical data report — evaluated, not built
Strict superset verified against the code (every header `parse_consultation_report` + `revenue.py`
read is present, identical names; `parse_date` already handles the datetime; footer = one blank-UID
Total row). Plan (KB §S135.6): both filenames accepted · additive ingest of Diagnosis / Procedures /
Follow-Up / demographics · same-day diagnosis write-through · procedure detection by the named column
(₹0 cashless) · **follow-up log remains the source of truth**, report column = reconciliation only
(owner yes/no pending) · mirror stays 8 columns, clinical fields never reach the Sheet.

### 0.6 Non-incidents, and the day's discipline record
Mid-day tile disappearance = settle model (D13) working. Session-134's project-knowledge swap found
incomplete at open (old versions present; v72/Frontend-v2/`__5_` initially reported absent — `__5_`
was in fact present and hash-verified `8bd1aeaa…` before any build). Assistant's F000562 claim
corrected by the workbook (119 keys issued; F000562 absent).

---

## §1 — MENTAL MODELS THAT HELD (or were minted)
- **The display is part of the system.** Records can be perfect while the screen lies; a confident
  wrong ID is worse than a blank (D208).
- **A verdict that doesn't move work is a note to self.** SEND BACK now moves work (D209).
- **Evidence rules at ingest:** mobile alone is not identity; UID-shape is the admission ticket; and
  no safety demotion may silently drop a patient from care (D210).
- **One writer per table; readers may multiply.** F-3's count is about writers.
- **D172 twice in one day:** the owner's eyes beat the screen; the workbook beat the assistant's memory.

## §2 — OPEN BACKLOG (Callback Tracker register read from Audit v1.6 this session)
1. **Block C** — one clock (F-13/F-5: server sends todayIST) + quota load (F-6/F-12: CacheService,
   bundled calls, bounded reads, quota headroom). **Precedes Block D (D185). Recommended next build.**
2. **Block D** — incoming-call console evolution (D181–D184, Call Console Spec v2.0).
3. **Block E** — delete `Probe.gs` + drop documents scope (F-15/F-7); finish F-10 (no patient data in markup).
4. **Clinical-data-report migration build** — plan ready; owner yes/no on the follow-up cross-check.
5. **F-0 decision sheet** — Call_Feed public URL vs service-account read (a trade, not a fix).
6. **D205** — seen-today WABA section (owner inputs pending).
7. **Bookkeeping findings:** F-3 (three writers vs documented one), F-4 (dead ledger, public writer),
   §4-Q3 (execution budget unmeasured).
8. **Docs owed to project knowledge:** Frontend Doc v2 (S134 file — owner holds the download), plus this EOS's swaps.
9. **Infra (non-tracker, chronic):** service-account key rotation (Tier-A1, highest standing risk),
   CALLHOOK steps 3–4 (Lokesh; run `bash /root/wa/rotate_callhook.sh status` at open), AKEY_14,
   Hindi spellings in `vitals_page.html`, Notion orphan cleanup. AI review layer stays parked (owner directive).

## §3 — ARTEFACT TABLE (changed this session)
| Artefact | Where | md5 |
|---|---|---|
| `Callconsole.gs` v1.3 | Apps Script | `44330498575dc5b46f6ed623445d05c2` |
| `Dashboard.html` v18.23 | Apps Script | `132d62579702b5c651347af97dea2c03` |
| `OutcomeLog.gs` (+getReviewSendbacks) | Apps Script | `9fc4c941bc067a40ce43eb40e8e81376` |
| `push_patient_mirror.py` | clinic PC | `d3105f6901700bad5300ea61b014a102` |
| `processor.py` | clinic PC | `0e7c129f57b53fca2cb21ba6dcd4d381` |
| `clean_visit_ledger_junk.py` (new) | clinic PC | `535af72132149cd76bfd750417c7e8eb` |
`Main`/`WebApp`/`Health` unchanged (`1a85166c…`/`5173c3c7…`/`9461d01b…`). Owner to export
`Clinic_Callback_Tracker__6_.json` at next session open. VPS untouched. Visit ledger 829 rows + backup.

**END OF RUNBOOK v73. §3 is the last section. If §2 is absent, this file is truncated.**
