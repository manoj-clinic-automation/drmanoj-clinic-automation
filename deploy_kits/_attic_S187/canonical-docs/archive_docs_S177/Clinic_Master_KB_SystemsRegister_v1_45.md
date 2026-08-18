# Clinic Master KB / Systems Register — v1.45 (CONSOLIDATED)

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **v1.44 is a FULLY CONSOLIDATED, self-contained master** (single file, no delta chain — S100 policy). It carries everything below plus **§102 (Session 102): the staff call-sheet de-duplication build, decision D146**.
>
> **v1.42 was the prior FULLY CONSOLIDATED, self-contained master.** It folds the entire delta chain
> into one document with a single decisions index and one changelog. No earlier version file
> is needed to read this one. **KB wins on any conflict.**
>
> **What this consolidation contains, and where each piece came from:**
> - **v1.38 base** (self-contained master; itself carried v1.36's collapse of
>   v1.33 → v1.34 → v1.35 + Session 67, and folded in the **v1.37 delta = Session 73** build
>   work). §12 STATE, §65, §66, §67, §73, Surveillance Register, decisions **D121–D134**.
> - **v1.39 delta (Session 75)** — §75 PC-local write-path (`clinic_writer.py`), **D135–D138**.
> - **v1.40 delta (Session 93)** — §93 PC-local Vitals & Plan front-end (Track 1 Step 5),
>   **D139–D142**.
> - **v1.41 delta (Session 94)** — §94 call-webhook 403 outage fix + doctor-console
>   `isGenericAgent_` fix, **D143–D145**.
>
> **Note on v1.37:** no standalone `v1.37` file exists (searched Drive backup + local code
> keep; not found). Its content is not lost — it was folded into the **v1.38 base** at the
> time (per v1.38's own header: "folds in the v1.37 delta = Session 73 build work"), and is
> present in this document within §73. Nothing is reconstructed or invented here.
>
> **Consolidation method:** verbatim fold-in only. Section bodies (§12, §65–§67, §73, §75,
> §93, §94) are reproduced exactly as written in their source files; the ONLY new material is
> this header, the single unified Decisions Index, the merged Surveillance forward-notes, and
> the changelog. No wording, decision, number, hash, or fact was altered.
>
> **§12 STATE currency:** §12 below is reproduced verbatim from the v1.38 base (its own
> "unchanged since Session 64" framing is preserved for the historical record). The CURRENT
> live picture is governed by the later sections and their state-change notes — most recently
> **§94.6** (S94 close): the call-duration gate is LIVE and healthy again after the 403 outage
> was fixed; `OutcomeLog.gs` was updated (D143) and redeployed as a New version (dashboard URL
> unchanged); everything else in §12 still stands (WABA sends still BLOCKED vendor-side D120;
> `wa_approve` still nohup not systemd; key rotations still overdue). Track 1: Step 5 COMPLETE,
> Step 7 not started.

---

## §12 STATE — what is live right now (UNCHANGED since Session 64 close)

**Nothing in §12 changed at Sessions 65–67 (no live code touched in any of them).** The live picture
from v1.32 stands verbatim:

- **WABA FOLLOW-UP BRIDGE — BUILT + LIVE on VPS, but SENDS BLOCKED vendor-side (D116–D120).**
  Three components in `/root/wa/`: `plan_followups_from_xlsx.py` (dry-run planner, LIVE),
  `wa_approve.py` (approve/deselect page, 127.0.0.1:8101 via OLS `/wa-approve`, **hand-run via
  nohup — NOT yet a systemd service**), `waba.py` (template sender, copied to VPS, unchanged).
  Safety = 2 open-gates (secret key in URL + TEST-mode default) + 2 live-send gates (LIVE toggle +
  daily-cap). Config in `/root/wa/wa_approve.env`; send creds in `/root/wa/.env`.
- **🔴 WABA SENDS BLOCKED — MyOperator-side AWS API Gateway fault (D120).** Send + templates-LIST
  GET both return HTTP 500 `x-amzn-ErrorType: AuthorizerConfigurationException`. Vendor-side, not
  ours (500 not 401/403; no-payload GET fails identically). Lokesh must fix the publicapi gateway
  authorizer. Fault code `WABA_SEND_AUTHORIZER_500` (ESCALATE-ONLY, vendor). AWS request-id on file:
  `eb82db53-47b2-48f1-b744-027a754be56c`.
- **Everything else from v1.31 §12 stands verbatim** — daily health report LIVE 08:00 IST;
  timer-freshness checker built+tested but STILL NOT armed; S61 watchman LIVE; stale-list sentinel
  LIVE; follow-up push VPS-native; attendance live; Dashboard v18.18; caller-ID SOP D93; duration
  gate D82; key rotation 🔴 overdue; AKEY_14; PHI base swap deferred.

**Known open (live-systems backlog, Track 2) — unchanged, restated:**
1. **🔴 WABA authorizer fault (D120)** — Lokesh; blocks ALL WABA sends; re-fire TEST when it clears.
2. **Make `wa_approve` a systemd service** — nohup dies on SSH close.
3. **Rotate `WA_APPROVE_KEY`** + service-account key (Tier A1) + AKEY_14.
4. **Upstream watcher dup bug** (clinic-PC) — 6 true-identical rows; diagnostic `inspect_dupes.py`.
5. Arm timer-freshness checker; maintenance jobs; "Agent shows as Staff" close; GitHub commit
   (S59–S64); data pass; P1–P10.
6. `call_transcription.py` GitHub commit; Stage-3 AI verdict layer; clinic_health_report.py UTC→IST
   fix; Orthopedic_Clinic_Rehab_Nutrition_v12.xlsm audit fixes (My_Plan!B31 #NAME? etc.).

---

## §65 SESSION 65 — Plan-tool multi-condition build + patient-lookup design (05 Jul 2026)

**EOS-LIGHT. No live code changed.** Decisions **D121–D124**.

### A) The standalone HTML plan-tool (Thread A) — multi-condition build, v21 → v23
- **What it is:** `rehab_nutrition_plan_vNN.html`, a single standalone file opened in Chrome. Owner
  fills a patient's details, prints/saves a personalised Rehab/Nutrition plan (Hindi-first older ortho
  patients). A **portal artifact, NOT a live system** until the owner deploys it. Owner's real Chrome
  is the FINAL print authority; headless render is a pre-check only.
- **Library:** `library_data.json` (extracted from `Orthopedic_Clinic_Rehab_Nutrition_v11.xlsm`) =
  126 exercises (English+Hindi), 111 modalities, 13 conditions. Embedded into the HTML.
- **v22** (md5 `91da5a2ad96678c184c4e38acbcf5b4f`): multi-condition selector — up to 4 conditions,
  each block's sub-pickers correct by type (joints=Pathway+Severity; spine=Pathway inc.
  radiculopathy+Severity; Ankle=Severity only; Post-TKR/THR=Phase only).
- **v23** (md5 `68cf0c9c45c3926bacc60200e561a66d`): two output buttons — **Patient Printout**
  (Nutrition + Home Exercise Sheet, per-condition sections, patient language, no machine settings) and
  **Physio Sheet (clinic)** (per condition: Modalities first, then Exercises). Headless-verified.
- **Hindi header name 16pt** — owner confirmed OK in real Chrome. **Parked item CLOSED.**

### B) Patient-lookup design — LOCKED (D121–D124)
- **D121** — Host the plan-tool as a **VPS-portal Flask app on its own private port, key-gated, behind
  OLS** (`extprocessor` + `context`) — SAME walled-off pattern as clinic-portal (:8099), attendance
  (:8042), wa-approve (:8101).
- **D122** — **Canonical CSV source rule:** read newest `patient_master.csv` + newest
  `patient_diagnosis.csv` by modified-date, from ONE fixed VPS folder the tracker syncs to — never a
  hard-coded Drive file-ID. Exact VPS folder confirmed on the box at build time.
- **D123** — **Shared Mobile → pick-list** (name+age+ID); never auto-pick. Age shown, never trusted.
- **D124** — **Two faces:** (a) owner's full version; (b) locked-down **staff BP-entry-only** version.

---

## §66 — SESSION 66: patient-data map + shared data model (Track 1)

**EOS-LIGHT — design + read-only Drive discovery. No code, no writes.** Decisions **D125–D128**.

### §66.1 — The patient-data "nerve centre" (read-only)
**Canonical live folder (CONFIRMED):** `My Laptop / data /` (Drive folder id
`1aRKh1ecJVpVmPJMMupnNKGiabrKfsF1C`; parent "My Laptop" `1SXjt7EO2MBVrqPF1gFMkm__a-JYZZDCG`). The
Drive-sync mount from the clinic-PC follow-up tracker. Live files keep a **stable file-id** as they
update (only modifiedTime moves), so the D122/L2 "newest-by-date in one fixed folder" rule resolves
cleanly to this single folder. (Exact VPS-side sync path still confirmed on the box at build time.)

**Files (all re-synced together; last stamp seen 2026-07-04):**
- `patient_master.csv` — identity. Cols: `Patient_UID, Clinic_Specific_Id, Patient_Name, Mobile_Raw,
  Mobile_Clean, Mobile_Status, First_Seen_Date, Last_Seen_Date, Mobile_Duplicate_Count,
  Identity_Status, Added_From, Last_Updated`. (id `1KmHIoJSi7cY1JvXKepwHVWlNUH79QLPl`)
- `patient_diagnosis.csv` — clinical. 7,452 data rows. Cols: `Patient_UID, Clinic_Specific_Id,
  Patient_Name, Age, Sex, Mobile_Clean, Diagnosis_Raw, Standardized_Diagnosis, Diagnosis_Category,
  Diagnosis_Priority, Diagnosis_Status, Comorbidities, Concession_Scheme, Admin_CC, Admin_PD,
  Admin_BID, Is_VIP, Source_File, Last_Updated`. (id `19duFAoKuK32vZo52miQA_OQL7qkfEycx`)
- `visit_ledger.csv` — attendance (NOT vitals). Cols: `Visit_ID, Visit_Date, Patient_UID,
  Clinic_Specific_Id, Patient_Name, Mobile_Raw, Mobile_Clean, Had_Procedure, Source_File,
  Processed_On`. (id `1tTHCcU8hhyGd-ciG87JDLbfrmF8-UzGP`)
- Plus `followup_ledger.csv`, `revenue_ledger.csv`, `outbound_log.csv`, `concession_log.csv`,
  `reinstatements.csv`, `confirmations.csv`, `diagnosis_source_meta.json`.
- Call recordings, transcripts, staff call outcomes flow to Drive + tracker sheet. All join on `Patient_UID`.

### §66.2 — Data-reality facts (verified)
- **`Patient_UID` is the spine** across every file (e.g. `ZOUEY49089`). Machine-stable, unique, never shown to staff.
- **Sex is coded `M`/`F`** — lookup maps `M→Male`, `F→Female`. 1 blank.
- **Age is dirty:** of 7,452 rows — 25 blank, 7 impossible (≤0 or >110), 389 under 15 (real children).
  Age is SHOWN for confirmation, never trusted.
- **Shared mobiles common:** `Mobile_Duplicate_Count` up to 5 on one number. Pick-list is a frequent path.
- **Diagnosis partly unclassified:** 47 categories, largest bucket "Other / Unclassified" (~1,922) +
  "No Diagnosis Recorded" (~293). Pre-fill frequently leaves the picker empty by design.
- **Comorbidities populated for only ~670 of 7,452 rows** (~9%) — blank pre-fill for ~91% is correct.
- **VITALS EXIST NOWHERE in synced data.** Height/weight/BP locked in Docterz only. Vitals tool is net-new.

### §66.3 — The shared data model (LOCKED)
**Write-path law:** Docterz = source of truth for diagnosis; tracker *derives* the CSVs; plan-tool and
vitals tool **only READ** Docterz-derived data and **NEVER write back**. Any tool that persists writes
into a file **it alone owns**. One-writer-per-file.

**Read-only inputs (tracker owns):** `patient_master`, `patient_diagnosis`, `visit_ledger`,
recordings/transcripts/call-outcomes.

**Write-side files (tool-owned):**
- `vitals_ledger.csv` — single vitals store. One write-function; **two front doors** (staff BP-only page +
  vitals section inside the plan-tool). Keyed `Patient_UID` + date. Append-only (one row per capture).
- `plan_ledger.csv` — plan-tool's OWN record of doctor's choices at a visit (conditions + comorbidities +
  sheets printed). Persists "I changed the diagnosis for this plan" WITHOUT touching `patient_diagnosis.csv`.

**ID rule:** `Clinic_Specific_Id` = human lookup handle (what staff TYPE). `Patient_UID` = backend
storage/join key (what everything SAVES ON). Lookup resolves Clinic ID → UID behind the scenes.

### §66.4 — Decisions (D125–D128)
- **D125** — Plan-tool pre-fills condition + comorbidities from `patient_diagnosis.csv`; doctor reviews
  & corrects on screen. ~26% Other/Unclassified, so pre-fill often leaves the picker empty — expected.
- **D126** — Plan-tool NEVER writes back to Docterz-derived files. Doctor's on-screen choices PERSIST in
  a plan-tool-owned `plan_ledger.csv`.
- **D127** — VITALS: one `vitals_ledger.csv`, one write-function, TWO front doors (staff BP-only page +
  vitals section inside the nutrition tool). Nutrition tool also READS vitals back. One writer, two interfaces.
- **D128** — JOIN KEY: `Patient_UID` = single backend storage/join key. `Clinic_Specific_Id` = human
  lookup handle only. Nothing stored keyed on Clinic ID.

### §66.5 — Still open (resolved/advanced in §67)
- Column schemas of `vitals_ledger` + `plan_ledger` → **RESOLVED in §67 (locked).**
- Build order: vitals format → nutrition tool's auto-read. Nutrition tool can ship first with manual weight/BP.
- VPS canonical-folder read path (D122/L2) — resolve on the box at build time. Still open.

### §66.6 — STANDING DIRECTIVE: living data-structure documentation
1. One exhaustive research/documentation pass of the ENTIRE data structure — every file live and
   in-construction (Drive `My Laptop/data/`, tracker outputs, Google-Sheet tabs, recordings/transcripts/
   call-outcomes, the new `vitals_ledger` + `plan_ledger`), and how they interconnect on `Patient_UID`.
   Produce one canonical "Clinic Data Map" document.
2. Keep it a LIVING document — updated on every file add / column change / writer change / new tool.
   Canonical alongside the KB. Surfaces in the Runbook backlog every session until done.

---

## §67 — SESSION 67: `Patient_UID` origin verified + schemas locked + v24/v25 built (05 Jul 2026)

**Full BUILD session on Track 1. No VPS / live-systems code changed — plan-tool remains offline Thread-A.**
Decisions **D129–D131**.

### §67.1 — `Patient_UID` origin VERIFIED: Docterz-generated (corrects §66 inference)
Owner exported a live 13-patient sample from Docterz (`clinical_data_export_docterz_sample.xlsx`,
55 columns). It has a **native column literally named `Patient UID`**, alongside `Clinic Specific Id`,
`Mobile`, `Gender`, `DOB`, `Age`, `Diagnosis`, and a present-but-empty `Vitals` column. Sample UIDs
(`RYIDM58643`, `GTYMR99882`, `YNTEP13051`) match the KB's 5-letter+5-digit format (`ZOUEY49089`).

- **`Patient_UID` is generated by DOCTERZ at registration — NOT by the tracker.** The tracker copies it
  through into the CSVs. Earlier "tracker generates it" reasoning was WRONG. Same-day patients are absent
  from the tracker CSVs only because the tracker ingests end-of-day / next-morning; the patient already
  holds their Docterz UID from registration.
- **BUT the UID is a BACKEND field — NOT visible at the front of Docterz.** Reception and owner see only
  **Clinic Specific ID + name + mobile** at the visit. The UID surfaces later (export/tracker layer).
- D128 join-key law stands and is reinforced: both keys are Docterz-native and authoritative at source.

### §67.2 — Other facts from the Docterz export
- **Docterz `Vitals` column EXISTS but is empty** in the sample — confirms vitals are net-new even at
  source. Revisit if Docterz vitals ever populate.
- **Docterz exports `DOB` + precise age** ("60 years 11 mons 21 days"). DOB is the authoritative age
  source; the plain-integer `Age` in `patient_diagnosis.csv` is a lossy downstream derivation (explains
  the dirty ages in §66.2). If age accuracy matters, DOB is the truth.
- The Docterz export is the **headwater** of the whole patient-data graph; feeds the tracker → CSVs.

### §67.3 — LOCKED SCHEMAS (Track 1 first build task)
**`vitals_ledger.csv`** (append-only, one row per capture; writer computes BMI/category/ratio for ALL
rows regardless of front door):
`Vitals_ID, Patient_UID, Clinic_Specific_Id, Patient_Name, Measured_On, Age_At_Visit, Sex, Height_cm,
Weight_kg, BMI, BMI_Category, Waist_cm, Waist_Height_Ratio, BP_Systolic, BP_Diastolic, Pulse_bpm,
Entered_By, Source_Face, Written_At, Note`

**`plan_ledger.csv`** (one row per plan generation; choices-only + pointers) — **14 columns, AMENDED at
S73 (D134): two PDF-path columns added. This is the CURRENT locked order:**
`Plan_ID, Patient_UID, Clinic_Specific_Id, Patient_Name, Plan_Date, Conditions_Selected,
Comorbidities_Selected, Diet_Type, Vitals_ID_Used, Sheets_Printed, Plan_PDF_Patient, Plan_PDF_Physio,
Generated_By, Written_At`

> **Schema-change note:** the original S67 plan_ledger was 12 columns (…`Sheets_Printed, Generated_By,
> Written_At`). S73 inserted `Plan_PDF_Patient` + `Plan_PDF_Physio` before `Generated_By` (D134). The
> `vitals_ledger.csv` schema above is UNCHANGED.

- `vitals_ledger` is append-only (repeat-visit trends accumulate). Derived values (BMI, category,
  waist:height) stored IN the ledger for reproducibility (owner wants historical progress reports).
- `plan_ledger` references vitals via `Vitals_ID_Used` (no duplicated weight to drift; blank if plan
  made with no vitals). Single source of truth for the measurement is `vitals_ledger`.
- `Sheets_Printed` = which sheets printed this visit (`Patient`, `Physio`, or both); blank if none yet.
- `Plan_PDF_Patient` / `Plan_PDF_Physio` = server-written archive path of each printout PDF (D132);
  blank if that sheet was not printed.

### §67.4 — v24 built: offline patient lookup (APPROVED offline)
`rehab_nutrition_plan_v24.html` (md5 `8c11be6b235578b5f3979448da8ba8b8`, 275,062 bytes). Adds to v23:
- "Load patient data" button → owner picks the two CSVs once per session (offline-safe; browsers can't
  auto-read disk files).
- Type Clinic ID or mobile → resolves to `Patient_UID` → auto-fills Name/Mobile/ID/Age/Sex.
- Pre-fills condition (mapped Standardized_Diagnosis → one editable condition block) + comorbidities
  (semicolon-split → editable tick boxes). Unmapped dx leaves picker empty (D125).
- Shared-mobile → pick-list (name+age+ID); never auto-picks (D123).
- Age shown, never trusted: blank/junk left blank + flagged; child/impossible ages flagged (L5/§66.2).
- Height/weight/BP stay manual with a reminder line.
- Headless-tested against a synthetic CSV pair (real headers, no real data) — 8 scenarios pass, zero JS errors.

### §67.5 — v25 built: embedded vitals section + new-patient path (APPROVED offline)
`rehab_nutrition_plan_v25.html` (md5 `92e3c637d0742d3ae1775ab21f871ea1`, 281,346 bytes). Adds to v24:
- **Embedded vitals-entry section (front door 2 — owner):** reuses the tool's existing `compute()` so
  BMI/category/waist:height MATCH the printed plan exactly. Shows the values live, then "Assemble vitals
  record" builds the exact `vitals_ledger.csv` row in locked column order and shows it field-by-field.
  **Offline shows the row only; the actual CSV append is a hosted-stage job (one writer, D127, decision B).**
- **New-patient toggle** (reworded from "No Clinic ID" → "New / not-yet-synced patient"): reveals a note,
  captures Clinic ID + name + mobile (NO UID field — not visible at front, §67.1). Row written with
  `Patient_UID` blank + Note "NEW — not yet in tracker; UID pending sync".
- IST timestamp stamped explicitly (TZ-independent). Missing height/weight → warning, not a broken row.
- Headless-tested: existing + new-patient + missing-measurement cases pass, zero JS errors. Print +
  lookup regression-clean.

### §67.6 — Decisions (D129–D131)
- **D129** — `Patient_UID` is **Docterz-generated** (verified from live export), copied through by the
  tracker; it is a **backend field, not shown at the front of Docterz**. Corrects the §66 inference;
  D128 reinforced.
- **D130** — New-patient (not-yet-synced) handling: the tool captures **Clinic ID + name + mobile only**
  (front-of-Docterz visible). No UID field. `Patient_UID` left blank on the row; row marked "UID pending sync".
- **D131** — **New-patient reconciliation (refines D130):** a same-day new patient's vitals/plan row
  starts UID-blank and is later STITCHED to the real Docterz `Patient_UID` once the tracker ingests them,
  matching on `Clinic_Specific_Id` + mobile. This is a light hosted-stage reconciliation job (essentially
  the earlier "option A"), needed only for the minority same-day-new path. Schema already supports it
  (UID nullable; Clinic ID + name always present). The staff BP-only page (D124/D127) shows NO calculated
  outputs on screen, but its stored rows STILL get BMI/category/ratio computed by the one writer (complete data).

### §67.7 — Track 1 status after Session 67 (historical — superseded by §73.4)
- Schemas LOCKED (§67.3). v24 lookup + v25 vitals section BUILT & owner-approved OFFLINE.
- Plan-tool artifact at end of S67: **v25** (`92e3c637d0742d3ae1775ab21f871ea1`).

---

## §73 — SESSION 73: plan_ledger row-assembly built (v26) + printout-PDF archiving locked (05 Jul 2026)

**Full BUILD session on Track 1. All offline — no VPS/live/GitHub code changed. Plan-tool remains an
offline Thread-A artifact.** Decisions **D132–D134**. (Sessions 68–72 were the design arc that settled
these decisions; folded in here.)

### §73.1 — Owner steering decision (context, not a numbered D)
Build the plan-tool + vitals tool fully, do all the backend write-path work, and **HOST BOTH TOGETHER
at one time** — the "final online version" is locked only once everything is built and the backend
actually writes ledgers + PDFs end-to-end. Offline builds (v26 onward) are **staging steps toward the
hosted product**, not deliverables in themselves. Does not change the locked Track-1 build ORDER; it
changes when a piece is "done" (hosting = done).

### §73.2 — Printout-PDF archiving (D132/D133/D134)
- The tool prints two sheets (patient + physio) but kept no copy — no record of what a patient was
  actually given. **D132** fixes it: archive **both** PDFs per visit, tagged by patient:
  `plan_archive/<year>/<Patient_UID>/<Plan_Date>_<Plan_ID>_{patient|physio}.pdf`. New patients with no
  UID yet (D130) → `plan_archive/pending/<Clinic_Id>_<mobile>/…`; the reconciliation job (D131) moves
  them to the real UID folder on tracker sync. Yearly top folder → easy archive-off later.
- **Why a frozen PDF, not re-print-on-demand:** the sheet depends on live CSV lookups + on-screen
  choices + tool version; re-generating months later may not reproduce it. A frozen PDF is the true record.
- **Storage sizing:** ~0.4 MB per visit (both text PDFs). At current load (**<10 printed plans/day**) →
  **~100 MB/year** — negligible on VPS or free Drive. Not a constraint.
- **Generated server-side** at hosting (a browser cannot silently save a PDF to disk). Offline, v26 only
  previews the exact paths.
- **Storage home (D133):** VPS canonical, Drive mirror DEFERRED (owner: "just save it reliably").
  Reliable local writes; matches one-writer-per-file + D122; the live write-path never depends on Drive
  at print time. A Drive mirror can be bolted on later (reuse the recording-archive OAuth-as-owner
  pattern, D36) if browse-anywhere is ever wanted.
- **Schema (D134):** see the amended `plan_ledger` in §67.3 (two PDF-path columns).

### §73.3 — v26 BUILT (offline, awaiting owner real-Chrome check)
`rehab_nutrition_plan_v26.html` — **md5 `6212ad8fe5072521cadb36b21f190ffa`**, from v25
(`92e3c637d0742d3ae1775ab21f871ea1`), full-file replacement, ~287 KB.
- New **"Plan record"** collapsed `<details>` panel (placed after the Doctor's-note group) — **button +
  on-demand preview only, NO live line** (owner: "it will clutter the front, skip it if possible").
- Click **Assemble plan record** → shows the exact 14-column `plan_ledger.csv` row (header + data +
  field-by-field). Nothing written offline.
- Reads REAL on-screen state: each condition block via `data-cond`/`data-path`/`data-sev`/`data-phase`
  → `Name [pathway/severity/phase]; …`; ticked comorbidities (`dm/htn/ckd/gout/thyroid` → full names);
  diet dropdown.
- **Print-flag mechanism (owner-approved):** each of the two existing print buttons sets a silent flag
  (`PLAN_PRINTED.patient` / `.physio`) — one added line each, no change to how printing works or looks —
  so `Sheets_Printed` + the two PDF-path fields truthfully reflect what was printed. Assemblable in any
  order (before or after printing).
- `Plan_ID`, `Patient_UID`, `Vitals_ID_Used` correctly blank offline (server-assigned/linked at hosting).
- **Offline PDF-path caveat (on-screen note added):** offline the path shows a `pending/` folder + a
  literal `<Plan_ID>` placeholder — expected, because the front never holds the backend UID (D129) and
  Plan_ID is server-assigned. On the hosted server both resolve to the real UID folder + a real Plan_ID.
- **Testing:** Node `--check` parse passed; 3-scenario headless logic test passed (established patient /
  new patient / nothing-printed). CSV escaping reused from v25.

### §73.4 — Track 1 status after Session 73 (CURRENT)
- Schemas LOCKED (§67.3 vitals unchanged; plan_ledger amended, D134). v24 + v25 + v26 built; v24/v25
  owner-approved offline; **v26 awaiting owner real-Chrome check** (closes Step 1 when confirmed).
- **NOT yet done:** hosting (Flask+OLS, D121/D122 — resolve VPS folder on the box); the real server-side
  write-path (vitals writer + plan_ledger writer + PDF archiving); staff BP-only page (D124/D127/D131);
  new-patient reconciliation job (D131); living Clinic Data Map (§66.6).
- **Owner plan:** host plan-tool + vitals TOGETHER once the backend write-path is built.
- Plan-tool current artifact: **v26** (`rehab_nutrition_plan_v26.html`, md5 `6212ad8fe5072521cadb36b21f190ffa`).
  Still an OFFLINE Thread-A artifact — not hosted, not committed to the live repo.

### §73.5 — Decisions (D132–D134)
- **D132** — Archive both printout PDFs, patient-tagged (`plan_archive/<year>/<Patient_UID>/…`); new-
  patient PDFs → `pending/` bucket, stitched on reconciliation; ~100 MB/yr; PDFs generated server-side.
- **D133** — Storage home: VPS canonical, Drive mirror deferred (owner: "just save it reliably").
- **D134** — `plan_ledger` schema +2 columns (`Plan_PDF_Patient`, `Plan_PDF_Physio`); new 14-col order (§67.3).

---

## §75 — SESSION 75: PC-local write-path built (Track 1, Step 4)

### §75.1 — Three pivots (context for the decisions)
1. **PC-local, not VPS.** The plan+vitals write-path tool runs on the **clinic PC**. The
   two source CSVs (`patient_master.csv`, `patient_diagnosis.csv`) already live on the
   clinic PC — the follow-up tracker writes them there and Google Drive syncs them out.
   Hosting the writer where the data already is means no patient data spreads to a
   second machine, and it honours the earlier no-VPS-hosting lean. (D136)
2. **Staff BP-only page retired.** Owner: *"I only enter the vitals in my PC; staff hand
   me a physical vitals record."* The second front door has no user. (D135)
3. **PDF/ledger storage home = clinic PC**, then Drive sync. Archive structure unchanged.
   (D137)

### §75.2 — `clinic_writer.py` — the PC-local single writer (BUILT + INSTALLED)
One self-contained Python module on the clinic PC (`C:\clinic_writer\`). Three jobs +
one read-only helper:
- **`write_vitals(...)`** — appends one row to `vitals_ledger.csv`; computes BMI /
  BMI_Category (Indian cut-offs <18.5/<23/<27.5/else) / Waist_Height_Ratio for EVERY
  row itself (mirrors the plan-tool compute() exactly); assigns next `Vitals_ID`;
  normalises Sex → M/F; stamps IST. 20-col locked schema (§67.3).
- **`write_plan(...)`** — appends one row to `plan_ledger.csv`; assigns next `Plan_ID`;
  links `Vitals_ID_Used`; stamps IST. 14-col locked schema (§67.3, D134).
- **`archive_pdf(...)`** — renders a text-faithful PDF via **reportlab** (D138) and files
  it at the D132 path (`plan_archive/<year>/<Patient_UID>/…`; new patients → `pending/`).
- **`lookup_uid_by_clinic_id(...)`** — read-only resolve of Clinic_Specific_Id →
  Patient_UID from `patient_master.csv`. NEVER writes the source CSVs.

**ID formats:** `V-YYYY-NNNNNN` / `P-YYYY-NNNNNN` — per-year running counter, 6-pad,
gap-safe (scans existing IDs for the year, takes max+1).

**Invariants obeyed:** append-only; one-writer-per-file; never writes the two read-only
source CSVs; no network / no Drive / no VPS calls (Drive sync is Drive's own job on the
folders); IST timestamps explicit.

**Verification (both machines):**
- Sandbox (Py 3.12.3): `py_compile` clean; `--selftest` 20/20 PASS; real PDF (valid
  `%PDF-`) filed correctly.
- **Clinic PC (Py 3.14.5): owner ran `--selftest` → 20/20 PASS; certutil md5 =
  `d4e20a51ead1aada8c07bead2b504100` (matches). INSTALLED + CONFIRMED 2026-07-05.**

**Status:** this is the WRITE-PATH LIBRARY. No front-end wired yet (Step 5 next). Manual
fallback (browser print, no archive) unchanged until the front-end is live.

**Repo demarcation (kit correction, same session):** `clinic_writer.py` lives in its OWN
top-level Git folder **`clinic_writer/`** — kept deliberately separate from
`followup-tracker/` because they are two distinct systems (matching `C:\clinic_writer\`
on the PC). A `README.md` in the folder documents the split. Code md5 unchanged; only the
repo location was corrected from the first S75 kit.

### §75.3 — Amendments to earlier Track-1 decisions
- **D121 (host as VPS Flask+OLS)** — AMENDED by D136: this tool is **PC-local**, not on
  the VPS. (Other portal tools on the VPS are unaffected.)
- **D122 (canonical CSV folder)** — RESOLVED by D136: canonical source is the **clinic-PC
  local `data/` folder** the tracker writes (Drive folder id
  `1aRKh1ecJVpVmPJMMupnNKGiabrKfsF1C` is its Drive mirror). Newest-by-date rule stands.
- **D124/D127 (two front doors / staff BP page)** — the STAFF-PAGE portion is RETIRED by
  D135. The single vitals writer + one-vitals-ledger design stands (one front door now:
  the doctor).
- **D133 (storage home VPS)** — AMENDED by D137: storage home is the **clinic PC**, then
  Drive sync. Archive structure (D132) and schema (D134) unchanged.

### §75.4 — Decisions (D135–D138)
- **D135** — Staff BP-only page RETIRED from Track-1 build (only the doctor enters vitals).
- **D136** — Track-1 write-path = PC-LOCAL; reads clinic-PC local `data/` CSVs; amends
  D121, resolves D122.
- **D137** — PDF + ledger storage home = clinic PC, then Drive sync; amends D133;
  archive structure unchanged.
- **D138** — PDF engine = reportlab (pure-Python, text-faithful; durable one-command
  Windows install), over HTML-render engines.

**Reserved:** D83–D92 (P1–P10). **Next free: D139.**

## §93 — Track 1 Step 5: PC-local Vitals & Plan front-end (COMPLETE)

### §93.1 What was built
The **local front-end** that turns the S75 `clinic_writer.py` engine (write-path library)
into a usable screen. Runs only on the clinic PC, doctor-only, no internet, no VPS.
Lives on **D:** so a Windows reformat can't wipe it (D140).

Package at `D:\clinic_writer\`:

| File | Role | md5 |
|---|---|---|
| `clinic_writer.py` | Engine (updated this arc — bilingual PDF) | `0ad6d9f449addd03de40b0bfbacca659` |
| `vitals_app.py` | Flask app, port 5057, 127.0.0.1 only | `ba29a558947f7ac8489626e0df39a8ef` |
| `vitals_page.html` | v25 plan-tool + Save-to-records bridge | `24ac9af4edfd00c01e4025e88800dade` |
| `open_vitals.bat` | Double-click launcher (mirrors open_tracker.bat) | — |
| `clinic_menu.html` | One-bookmark menu → Tracker + Vitals&Plan | — |
| `NotoSansDevanagari-Regular.ttf` | Hindi font for archive PDFs | `f4ae6809bd8c31573370e8da72514012` |

### §93.2 Flow
Type Clinic ID → `/lookup` reads `patient_master.csv` + `patient_diagnosis.csv`
(READ-ONLY, from the tracker's C: data folder) → resolves real `Patient_UID`
(shared-mobile pick-list, D123) → Age/Sex/condition pre-fill (editable, D125) →
enter vitals + plan choices → print as usual → **Save to records** → `/save` calls
`write_vitals` + `write_plan` + `archive_pdf` (both sheets) → two ledger rows + two PDFs.
New patients (UID blank) route to `plan_archive\pending\` for later reconciliation (Step 7).

### §93.3 Reads / writes
- **Reads (never writes):** `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\data\`
  → `patient_master.csv`, `patient_diagnosis.csv`.
- **Writes (own, on D:):** `D:\clinic_writer\vitals_ledger.csv` (20 cols), `plan_ledger.csv`
  (14 cols), `plan_archive\<year>\<UID>\<date>_<PlanID>_{patient|physio}.pdf`.

### §93.4 Decisions D139–D142
- **D139** — Front-end is its own auto-launched Flask app importing clinic_writer,
  a SEPARATE program from the live tracker (stability/safety/maintenance); shared menu
  page; double-click `.bat` launch (mirrors the tracker). Ports 5000 (tracker) / 5057
  (vitals) never clash.
- **D140** — Whole tool + engine + ledgers + archive live on **D:** (survives a Windows
  reformat). D: is an SSD PARTITION → protects vs reformat, NOT disk death; Drive sync is
  the real off-machine backup. Source CSVs stay on C:, read across drives. New tool built
  on D: from birth; migrating the live tracker to D: is a separate later task.
- **D141** — Diagnosis pre-fill mapped from `Orthopedic_Diagnosis_Taxonomy_Master.xlsx`
  (27 canonical categories). 12 auto-fill a rehab button; 15 blank-by-design (doctor picks).
  Knee Internal Derangement blank (owner A=No); Cervical*→Cervical Disc Disease,
  Lumbar*→Lumbar PIVD (owner B=Yes). Unmapped → "dx recorded — pick the exercise set",
  never a silent Knee-OA default. (Fixes the strict-label matcher that failed on the real
  full-wording data.)
- **D142** — Bilingual archive PDF via **per-run font switching**: Helvetica for English,
  NotoDev (NotoSansDevanagari) for Devanagari runs, chosen per run within each line
  (engine helper `_mixed()`). Whole-doc Devanagari font rejected — it has digits only,
  no A–Z, so it dropped all English. ALSO: empty-physio-PDF fixed — Save bridge now builds
  BOTH sheets from the tool's own `sheetBlocks()` (physio is never an on-screen box), not
  screen-scraping. Graceful font fallback → archiving never fails. reportlab stays (D138).

### §93.5 Engine change (clinic_writer.py)
Only `archive_pdf` changed since S75: base font Helvetica + `_mixed()` per-run Devanagari
wrapping + a `_DEV_RE` regex helper. Self-test still 20/20. New md5
`0ad6d9f449addd03de40b0bfbacca659` (was `d4e20a51ead1aada8c07bead2b504100`). This is the
FIRST engine change since the S75 lock — additive, fallback-safe.

### §93.6 Status
**Step 5 COMPLETE** and owner-verified on the clinic PC. **Step 7 (reconciliation)** not
started. **Plan-tool / vitals tool are still PC-LOCAL offline systems** — not hosted, not
live-VPS.

### §93.7 Open (next session, Track 1)
**Hindi SPELLING** corrections in the exercise/modality library source strings
(`name_hi` / `instr_hi`) — content + rendering are correct; only spelling to tidy. The
strings live in the embedded `LIB` in `vitals_page.html` (originally from
`Orthopedic_Clinic_Rehab_Nutrition_v11.xlsm`). Owner explicitly scoped OUT table-formatting
rework (archive content complete; run-together tables acceptable).

## §94 — Track 2: call-webhook outage + doctor-console fix (LIVE CODE CHANGED)

Session 94 was **not** a planned build session. It opened on a manual follow-up push and
turned into two live-fault repairs, then a project examination and a six-item forward agenda.

### §94.1 Incident 1 — call-webhook 403 outage (FIXED, verified end-to-end)

**Symptom:** staff dashboard follow-up tiles stuck on "⌛ Checking the call… the outcome
unlocks once it connects" even after a genuine >15-second connected call. The outcome
dropdown never unlocked. Started ~Jul 6, all tiles at once. WhatsApp feed unaffected.

**Diagnosis chain (all read-only until the fix):**
1. `call-hook.service` (:8098) was **up and healthy** — ruled out dead service.
2. Raw-log folder `/root/wa/call-hook/call_hook_logs` had **no `2026-07-07.jsonl`** — no
   call webhook had been received all day; last body landed Jul 6 ~13:41.
3. MyOperator panel → Webhooks v2: the **Call** webhook showed **status Failed**; the
   WhatsApp webhook showed **Active** (hence WhatsApp still worked).
4. Panel Failure Logs: **every** Call Ended / Call Summary delivery returned **HTTP 403**,
   consistently, on both Jul 6 and Jul 7.
5. A local `curl` to the receiver with the correct key **also returned 403** — proving the
   rejection was the receiver's own secret-gate, not an OLS/IP/WAF block.

**Root cause:** the VPS `.env` had **two secrets mashed onto one physical line** — a lost
newline had merged `CALLHOOK_SECRET` with a trailing `FU_UPLOAD_SECRET=…` fragment, so the
receiver read `CALLHOOK_SECRET` as a long run-on string that could never match the panel's
key → every incoming call webhook 403'd → nothing written to `Call_Durations` → the duration
gate could never unlock. (A **second, clean** `FU_UPLOAD_SECRET` on the next line was the one
actually in force — last-definition-wins — so the follow-up upload catcher kept working,
which is why only calls broke.)

**Fix (owner ran, one step at a time):**
- Timestamped backup of `.env` first.
- `sed -i '17s|.*|CALLHOOK_SECRET=<new clean key>|'` — rewrote **only** line 17 to a fresh
  **plain-alphanumeric** call key (Option B, chosen to remove the `@` special-char that
  complicates URL transport). The run-on `FU_UPLOAD_SECRET=…` junk on line 17 was thereby
  deleted; the real `FU_UPLOAD_SECRET` on line 18 was untouched.
- `systemctl restart call-hook.service` → verified `active`, `secret gate: ON`, `connected
  to 'Call_Durations' — 98 rows known`.
- MyOperator panel → Webhooks v2 → **Call** webhook → Edit → updated `?key=` to the new
  clean key; Call Ended + Call Summary still ticked; Authentication None; Save.

**Verified end-to-end:** Shavez placed a real follow-up call; the tile's "Checking…"
resolved; the outcome unlocked and saved. Outage closed.

**New fault code:** `CALLHOOK_SECRET_MISMATCH_403` — **ASSISTED**. Detection idea (not yet
built): if the panel's Call webhook shows Failed OR no `YYYY-MM-DD.jsonl` raw-log file has
appeared by mid-morning on a clinic day, alert. Procedure = compare `grep CALLHOOK_SECRET
/root/wa/.env` against the panel URL's `?key=`; re-sync + restart if they differ.

### §94.2 Incident 2 — doctor console "Could not load: isGenericAgent_ is not defined" (FIXED)

**Symptom:** the doctor dashboard's **Outcome Review → Today** view showed "Could not load:
isGenericAgent_ is not defined" and a count of 0. **Yesterday** view worked (13 outcomes
listed). So saved outcomes were fine; only the Today *display* was broken.

**Diagnosis (static scan of the live Apps Script JSON export, all 14 files):**
- `OutcomeLog.gs` line ~333 calls `isGenericAgent_(by)` — a helper **defined nowhere** in
  the project. When the Today build loop reaches it, JS throws → the whole Today view dies.
- The scan flagged 5 "called-but-undefined" names; 4 (`escPick_`, `fmtLV_`, `fmtWhen_`,
  `sbPick_`) are false positives — defined as `var x = function`. **Only `isGenericAgent_`
  is genuinely undefined.** It is the sole such fault in the project.
- Today vs Yesterday difference: line 333 only bites when a live matched call with an agent
  name is present, which the Today enrichment path produces and the archive-based Yesterday
  path does not — explaining why only Today failed.

**Fix (D143):** added the one missing helper to `OutcomeLog.gs`, placed among the small
helpers after `OL_col_`. It answers the question the call site needs — *is this "Handled By"
value a generic placeholder (staff / doctor / unknown / agent / system / blank) rather than
a real name?* — so line 333 can borrow the real caller's name from the call log when the
outcome was filed under a generic label.

```
function isGenericAgent_(name) {
  var n = String(name || '').trim().toLowerCase();
  if (!n) return true;
  return (n === 'staff' || n === 'doctor' || n === 'unknown' || n === 'agent' || n === 'system');
}
```

**Delivered as a full-file replacement** (per protocol), built from the live JSON export
(21,076 → 21,690 chars; only the one function + comment added). Verified: `node --check`
PASS; exactly one definition, one call site. Owner deployed via **edit existing deployment →
New version** (URL stable). Owner confirmed: Today view loads, "all good now."

### §94.3 Project examination (no code beyond the two fixes)

Full static analysis of the live project was run from the Apps Script JSON export. Findings:
- The dashboard **does not de-duplicate** the follow-up worklist — it reads `Followups_Today`
  exactly as the PC push writes it. So **duplicate patient rows originate PC-side** (the
  tracker's list generation), not in the dashboard.
- Today's real worklist was **238 rows** (20 Due Today, 34 Grace, 52 Actionable Missed,
  **124 Probable Dropout**, plus small buckets) — confirming the ">200, not humanly callable"
  problem is dominated by the Probable-Dropout bucket.
- `Call_Feed` remains the known-unreliable feed (D55); archive is authoritative.

### §94.4 Six-item forward agenda (owner-set; DESIGN captured, not built)

Logged for sequencing. My recommended order and current standing:

1. **Duplicate patient entries in a day** — real; fix is **PC-side** (de-dupe before/inside
   `push_followups_today.py`, or in the tracker's list builder). SAFE, ready to build once
   we see why a patient doubles (same section twice vs two sections). *Next execution item.*
2. **Reconcile "didn't pick up but visited"** — auto-settle a follow-up when the patient
   actually visits (proof = new Docterz visit). HIGH VALUE. Overlaps **Track-1 Step 7**
   (new-patient reconciliation) — same match machinery (Clinic ID + mobile). Needs a design
   step (which visits qualify, what outcome to write, where it runs).
3. **Trim the staff calling list (>200)** — needs an OWNER POLICY decision (what caps the
   daily list, where the 124 dropouts go — separate low-priority queue / weekly batch).
   Partly pre-designed as **D66 "Living Staff List"** (snooze, 3-tries-escalate,
   outcome-vanishes) — designed, not fully built.
4. **Live staff-activity summary on the doctor dashboard** — today live + yesterday
   cross-verified/audited against archive + transcripts. Buildable; the "audited" half
   depends on item 5.
5. **Migrate to AI audit layer** — this is **Stage 3 (D62)**: overnight Haiku-tier batch,
   ~₹200–350/month, transcript-vs-claimed-outcome, doctor-only flags. Designed, not built.
   Doctor-only "Call Audit" sheet already exists.
6. **Historical follow-up insights across taxonomy** — analysis only, no code. **Blocked on
   a de-identified data export** (patient data is deliberately not in this project). Claude
   can deliver the analysis plan now; real numbers need the export.

**Owner stance at close:** open to doing more together when it fits limited time; delegated
sequencing to Claude ("your call"). Claude's call: do the safe/ready items (Item 0 done +
Item 1 next), design-sheet the rest — do NOT bundle policy/AI-cost decisions into a rushed
build.

### §94.5 Decisions
- **D143** — `isGenericAgent_` helper added to `OutcomeLog.gs`: generic = staff / doctor /
  unknown / agent / system / blank. Purpose: let the Today outcome view borrow the real
  caller name from the matched call when the outcome was filed under a generic label.
  Full-file replacement; node-check verified; deployed as New version (URL stable).
- **D144** — Call-hook secret standard: the `?key=` gate for `/mo-callhook` (and by
  extension similar self-chosen VPS webhook gates) shall be **plain alphanumeric, no special
  characters** (no `@ # / ? & =`), because special characters corrupt under URL transport and
  caused the S94 403 outage. Applies to future key rotations of these gates.
- **D145** (hygiene note, not yet acted) — during S94 the plain-text values of
  `CALLHOOK_SECRET` (new), `FU_UPLOAD_SECRET` (line 18), and the old junk fragment were
  visible in terminal paste. These are self-chosen VPS gate keys (NOT WABA/MyOperator
  tokens), so exposure is low-risk, but a courtesy rotation of `CALLHOOK_SECRET` +
  `FU_UPLOAD_SECRET` is advisable at a convenient time (no Lokesh coordination needed).

### §94.6 State changes to §12
- **Duration gate is LIVE and healthy again.** `call-hook.service` (:8098) up; `Call_Durations`
  filling; outcome unlock working. The S94 403 outage is CLOSED.
- **Dashboard Apps Script:** `OutcomeLog.gs` updated (D143), redeployed as a New version of
  the existing deployment; dashboard URL unchanged.
- Everything else in §12 (KB v1.40) stands verbatim: WABA sends still BLOCKED vendor-side
  (D120); `wa_approve` still nohup (not systemd); key rotations still overdue; watchman /
  health report / attendance / follow-up push all live; Track 1 Step 5 COMPLETE, Step 7 not
  started.

---

---

## §102 SESSION 102 — Staff call-sheet de-duplication (07 Jul 2026)

**FULL EOS. Live PC-side code changed** (`processor.py`, the follow-up tracker's list builder).
This is the first execution item of the owner's six-item agenda ("Item 1 — duplicate patient
entries"), and it is DONE, installed, and verified on the day's real sheet.

### §102.1 The problem (root cause, verified from real data)
The daily staff call sheet `Staff_Action_Today_*.xlsx` was showing the SAME patient two or three
times. Root cause established by reading today's real workbook, NOT assumed:
- A patient carries **several OPEN follow-ups from different visit cycles** (each with its own
  `Followup_ID` / KEY). They are all still "open" because earlier cycles were never closed, so they
  all land on the same day's sheet.
- **No KEY repeats** — these are not byte-identical rows (so it is NOT the old upstream watcher
  dup bug). They are genuinely-distinct un-collapsed multi-cycle follow-ups for one person.
- On 07-Jul: **236 follow-up rows, 22 duplicate groups.** Two sub-patterns: (A) two open
  follow-ups with different dates (most groups); (B) two with the SAME date (near-simultaneous
  double-generation for one visit).
- **Confirmed the dashboard does not de-dupe** (D-note carried from §94.3) — the fix belongs
  **PC-side at generation**, exactly where the KB already said it should.

### §102.2 The fix (owner-confirmed collapse rule, D146)
Inserted a collapse step into **`build_staff_call_workbook`** in `processor.py`, applied to the
final follow-up list (`combined`) AFTER the call overlay + reinstatement merge and BEFORE the rows
are written — so it affects ONLY the FOLLOW-UP section. Procedure call-backs and the Watch/
Unreachable section are untouched.

Collapse rule (owner-confirmed, S102):
- **Group by mobile + name + diagnosis** — so a patient's two genuinely-different clinical
  problems stay as two separate rows.
- **Keep ONLY the most recent follow-up cycle = latest `Due_Date`.** Older cycles are removed
  from the sheet **entirely, with NO note** (owner decided a note would confuse staff).
- **EXCEPTION: a reinstated ("call back & complete", amber) row always wins its group**, even if
  older — that flag means the clinic owes the patient a callback and must never be dropped.
- **Blank / invalid mobile → group by name only** (those are un-callable anyway).
- The whole block is wrapped in `try/except` → on ANY error it falls back to the full,
  un-deduped list. A de-dupe hiccup can **never** break the sheet (same defensive pattern the
  file already uses for reinstatements and procedure reconciliation).

### §102.3 The audit workbook is deliberately NOT de-duped
`processor.py` has TWO builders: `build_staff_call_workbook` → the staff CALL SHEET
(`Staff_Action_Today_*.xlsx`, fixed here) and a second builder → the doctor AUDIT workbook
(`Followup_Audit_*.xlsx`, 9 tabs). The audit's own "Staff Action Today" tab still shows every
row **by design** — it is the doctor's oversight microscope; only the staff-facing call sheet is
collapsed. (Owner may revisit if he wants the audit collapsed too.)

### §102.4 Verification (on the real regenerated sheet)
- **Follow-up rows 236 → 214** (22 removed); **zero duplicate groups remain**.
- Rakesh Kumar → single row, the 29-Jun amber "call back & complete" (reinstated WON). ✅
- Chandraprabha → single row. ✅  Satwinder Kaur → single 03-Jul row (25-day-old hidden). ✅
- `python -m py_compile processor.py` clean on the clinic PC (owner-confirmed, no output).
- New `processor.py` md5 `8813a27db66c91628153c55912612ceb`; backup kept on PC as
  `processor_BACKUP_S102.py` (manual fallback = restore it).

### §102.5 Decisions
- **D146 — Staff call-sheet de-duplication rule.** In `build_staff_call_workbook`
  (`processor.py`), the follow-up list is collapsed to **one row per patient** before writing:
  group by **mobile + name + diagnosis**; keep the **latest `Due_Date`**; **older cycles hidden
  with no note**; **reinstated rows always win their group**; blank-mobile grouped by name only;
  fail-safe `try/except` falls back to the full list. Only the FOLLOW-UP section is affected; the
  Procedure and Watch sections and the separate `Followup_Audit_*.xlsx` audit workbook are
  untouched. Verified live 07-Jul (236 → 214, zero dups).

### §102.6 Carried forward (added to priority backlog)
- **Option B — per-patient "latest state" join** (bigger task, deferred by owner to the
  console/reconciliation work): put the patient's **most-recent visit + most-recent call outcome +
  its recording + transcript + most-recent follow-up** all on the single surviving row. Needs the
  Docterz visit feed + `Call_Durations` / call-transcription sources wired in; overlaps agenda
  Items 2 & 4 and the Stage-3 audit layer. **This session's fix (Option A) is the call-sheet
  de-dupe only.**
- **Agenda Item 2 confirmed as next** — reconcile "didn't pick up but visited" (auto-settle a
  follow-up when the patient actually returns; proof = a real Docterz visit after the follow-up
  was created). Claude owes the one-page DECISION SHEET before that build. The current sheet does
  NOT yet drop patients who quietly returned — that is Item 2 by design, not a regression.

### §102.7 State changes to §12
- **`processor.py` (PC-local, follow-up tracker) is CHANGED and LIVE** — carries the D146
  de-dupe. Everything else in §12 stands: WABA sends still BLOCKED vendor-side (D120);
  `wa_approve` still nohup (not systemd); duration gate live + healthy; key rotations overdue;
  Track 1 Step 5 COMPLETE, Step 7 not started.


## §107 SESSION 108 — Data-folder / Drive-sync evaluation (07 Jul 2026)

**EOS-light finding (no code) — folded into this v1.45 full EOS.** The owner asked why the
follow-up tracker's `data\` folder shows **multiple dated CSV files**, and whether that indicates
a fault in the Item 2 auto-settle engine (which reads visits). Claude evaluated the code + folder
and found it **NORMAL BY DESIGN.**

### §107.1 The two file-types (they must not be confused)
The tracker's `data\` folder holds two different kinds of CSV that look superficially similar:
- **`consultation_report_YYYY-MM-DD.csv`** — the **daily raw Docterz input**, ONE per clinic day.
  `parse_consultation_report()` (`processor.py`) reads the day's file at ingest; then it is history.
  **These are SUPPOSED to be many and dated** — one arrives each day. Seeing a pile of them is
  correct, not a fault.
- **`visit_ledger.csv`** — the **single cumulative attendance ledger**, read from ONE fixed path
  (`DATA_DIR / "visit_ledger.csv"`). The tracker appends each day's consultations into it. It is
  **SUPPOSED to be ONE file, never dated.** Every row's `Source_File` column records which dated
  `consultation_report_*` it came from (the audit trail). Verified on the live file: 749 visits,
  04-Jun → 06-Jul-2026, cumulative, single file.

Analogy for the record: the dated `consultation_report_*` files are the **fuel** (one tank-fill a
day); `visit_ledger.csv` is the **tank**. The settle engine and everything else read the tank.

### §107.2 Drive-sync direction (owner-confirmed S108)
The `data\` folder is **Google-Drive-synced** (owner confirmed). This matches the existing record
(D122 canonical-source rule; §66.1 folder `My Laptop / data /`, Drive id
`1aRKh1ecJVpVmPJMMupnNKGiabrKfsF1C`). Direction: the **clinic-PC tracker owns/writes** these files;
Drive **mirrors them out** (off-machine backup). The canonical read is *newest-by-modified-date from
the one fixed folder*, never a hard-coded Drive file-ID.

### §107.3 The one honest dependency (not a fault today)
The Item 2 settle engine can only settle a returning patient **once that patient's row exists in
`visit_ledger.csv`** — i.e. after the day's `consultation_report_*` is ingested AND Drive has synced.
So settle freshness = sync freshness. On 07-Jul this was healthy (last visit 06-Jul, processed
07-Jul — normal one-day lag). Nothing broken; recorded as a known dependency, not a defect.

### §107.4 Decision
- **D147 — Two-file-type rule + Drive-sync direction (VERIFIED-NORMAL).** In the tracker `data\`
  folder: `consultation_report_YYYY-MM-DD.csv` = daily raw Docterz inputs, *many and dated by
  design*; `visit_ledger.csv` = single cumulative ledger, *never dated*, read from one fixed path.
  Multiple dated CSVs are expected, not a fault. The `data\` folder is Drive-synced (PC writes →
  Drive mirrors); settle-engine freshness depends on that sync. No code change; documentation only.


## §121 SESSION 121 — Item 3: staff call-list cap + Hard-to-Reach split (07 Jul 2026)

**FULL EOS. Live PC-side code changed** (`processor.py`, `build_staff_call_workbook`). This is the
third execution item of the owner's six-item agenda ("Item 3 — trim the >200 staff list"), DONE,
installed, and verified on the real generated sheet.

### §121.0 Agenda context — Items 1 & 2 status confirmed this arc
- **Item 1 (duplicates) — DONE (§102, S102).**
- **Item 2 (auto-settle "didn't pick up but visited") — found ALREADY BUILT and LIVE, verified S106.**
  The settle engine already exists in `processor.py` (`compute_followup_status`, ~line 1820): every
  follow-up is matched to a real Docterz visit keyed on `Patient_UID`, using `Followup_Log_Date`
  (the raise-date) with constant `COUNT_LOG_DATE_VISIT_AS_RETURN = False` → a visit **strictly
  after** the raise-date settles it (same-day = the prescribing visit, does NOT settle). Matched
  rows flip to terminal `Returned Early / On Time / Late` with `Matched_Visit_ID` +
  `Return_Delay_Days`, are excluded from the staff sheet, and kept tagged in the audit workbook.
  Verified on 07-Jul live data: **249 of 493 rows settled**, zero leakage to the staff Call Sheet.
  Item 2 therefore needed **no build** — only end-to-end confirmation, now done. (Owner decision on
  the design sheet: visit beats amber — a returned patient settles even if the row was reinstated.)

### §121.1 The problem
The staff Call Sheet carried ~222 rows/day — not humanly callable. Volume dominated by **Probable
Dropouts** (127 on 07-Jul; 11–60 days overdue), which crowd out the winnable fresh follow-ups
(Due Today + Grace + Actionable). It is a "wrong patients at the top" problem, not "too many people".

### §121.2 The fix (owner policy, Sessions 109–114; D148)
All changes land in **`build_staff_call_workbook`**, applied to the final follow-up list AFTER the
settle-exclusion + call overlay + D146 de-dupe and BEFORE the rows are written. Two steps, both
wrapped in `try/except` (fail-safe fallback to the pre-cap list — can never blank the sheet):

- **Step A — 3-strike Hard-to-Reach split.** Any row with `Call_Attempts ≥ 3` and still no contact
  (`Call_Resolution` not RESOLVE/DECLINE) is pulled OFF the daily list into a new **Hard-to-Reach**
  tab in the staff workbook, carrying **name · Clinic ID · mobile · diagnosis · last-visit date**
  (last-visit read read-only from `visit_ledger`) **· attempts**. Reinstated (amber) rows are
  protected — never pulled. Purpose: the doctor decides per patient — keep calling or archive. NOT
  auto-archived. *(Recording + transcript links are a planned fast follow-up — owner choice "b",
  S111 — because those live on Drive/tracker-sheet keyed on `Patient_UID`, outside `processor.py`.)*
- **Step B — 120-cap + drip + roll-to-tomorrow.** Remaining rows filled to a **DAILY_CALL_CAP = 120**
  total: winnable buckets (Due Today / Grace Period / Actionable Missed) first, in the engine's
  existing freshest-first + post-op-float order; whatever room is left under 120 back-filled with the
  **OLDEST Probable Dropouts** (most days-overdue first, the drip). When winnable alone ≥ 120, take
  the top 120 and the winnable **overflow rolls to tomorrow** (not shown today; reappears next run
  because its ledger status is unchanged); dropouts get zero room that day.

Priority order within the list is **unchanged** from before (the engine's own ranking + post-op
float stay as-is). The audit workbook (`Followup_Audit_*.xlsx`) is **untouched and stays full** —
only the staff Call Sheet is capped.

### §121.3 Verification (on the real regenerated sheet, 07-Jul)
- Staff workbook tabs: Call Sheet · Vacation Notice · Settled Follow-Ups · **Hard-to-Reach** · Day
  Revenue. New tab present. ✅
- Follow-up section capped at **exactly 120 rows** (237 callable → 110 winnable + 10 oldest-dropout
  drip). ✅
- Hard-to-Reach tab present with correct title; **0 patients today** (no one has ≥3 no-contact
  attempts yet — expected; the call-log read-back is young). ✅
- Audit workbook intact (493 ledger rows, 9 tabs). ✅
- `python -m py_compile processor.py` clean on the clinic PC (owner-confirmed, blank output).
- New `processor.py` md5 **`171a090645da130a4f4cbb0c0b102f22`**; backup kept on PC as
  **`processor_BACKUP_S115_pre_Item3.py`** (= S102 build `8813a27db66c91628153c55912612ceb`, the
  manual fallback = restore it).
- One transient install hiccup: first run raised `PermissionError [Errno 13]` at `wb.save()` because
  the target `Staff_Action_Today_*.xlsx` was open in Excel (Windows file-lock) — NOT a code fault;
  closing the file and re-running succeeded. Recorded so it isn't mistaken for a regression.

### §121.4 Decision
- **D148 — Staff call-sheet cap + Hard-to-Reach split.** In `build_staff_call_workbook`
  (`processor.py`), after de-dupe and before writing: (A) rows with `Call_Attempts ≥ 3` and no
  contact (not RESOLVE/DECLINE) are moved to a **Hard-to-Reach** tab (name · Clinic ID · mobile ·
  diagnosis · last-visit date · attempts; reinstated rows exempt) for doctor keep/archive decision;
  (B) the remaining list is capped at **120** total — winnable buckets first in existing priority
  order, leftover room drip-filled with oldest Probable Dropouts, winnable overflow rolls to
  tomorrow. Fail-safe `try/except` fallback to the full list. Audit workbook untouched/full.
  **Amendment note to D146:** "reinstated always wins its group" now holds *among rows that survive
  the settle engine and the 3-strike split* — a returned or 3-strike row is removed before de-dupe
  (visit/attempts beat amber, per owner). Verified live 07-Jul (cap = 120, drip = 10, HTR = 0).

### §121.5 Recording/transcript follow-up (owner choice "b", carried)
The Hard-to-Reach tab ships now with the four LOCAL fields. Adding **last call recording +
transcript links** is the immediate next micro-task: those live on Drive + the tracker sheet keyed
on `Patient_UID` (the VPS call-transcription job, doctor-only sheet
`1rq9VvB5L94EmmZbiUwase9HBLsJ3htispYLd1rHjSRQ`). Needs the transcript-metadata join verified before
wiring — kept out of this build to keep it clean and shippable.

### §121.6 State changes to §12
- **`processor.py` (PC-local, follow-up tracker) is CHANGED and LIVE** — now carries BOTH the D146
  de-dupe AND the D148 cap/Hard-to-Reach split. md5 `171a090645da130a4f4cbb0c0b102f22`. Everything
  else in §12 stands: WABA sends still BLOCKED vendor-side (D120); `wa_approve` still nohup (not
  systemd); duration gate live + healthy; key rotations overdue; Track 1 Step 5 COMPLETE, Step 7 not
  started.

---

## SURVEILLANCE REGISTER — unchanged since Session 64

No surveillance rows changed at S65–S67 (no live component added). The v1.32 register stands verbatim,
including the WABA-send fault row (`WABA_SEND_AUTHORIZER_500`, CRITICAL·ESCALATE-ONLY) and the
wa_approve "not yet service-monitored" note.

*(Forward-looking: when the hosted plan-tool + vitals tool become live services, each gets its own
surveillance row — liveness on its port/service, plus a freshness/disk check for the `plan_archive/`
PDF store (D132) and the two ledgers. Not yet applicable; not built.)*

---

### Surveillance forward-notes folded from later sessions
*(These are forward-looking notes recorded in the deltas; no surveillance ROW is live yet for
these Track-1 tools. Kept here so the register stays complete.)*

**From v1.39 (S75):** When the Step-5 front-end goes live on the PC it becomes a local service
— at that point add a liveness/freshness row (local app up; ledgers + `plan_archive/` writable
+ syncing). *(Step 5 is now COMPLETE per §93, but as a PC-local offline app, not a monitored
live service; no VPS surveillance row applies.)*

---

## §95–100 — DOCUMENTATION-CONSOLIDATION ARC (records-cleanup; NO live code)

Sessions 95–100 were an **EOS-light documentation arc — no live system, VPS file, dashboard
script, or Track-1 tool was touched.** Its whole purpose was to turn fragmented delta chains
into clean single-file canonical masters and to recover version files that had gone missing
from project knowledge. Logged here so the KB's own history is honest and self-explaining.

### §95.1 What was done
- **KB consolidated → v1.42 (S95):** folded v1.38 base + v1.39 + v1.40 + v1.41 into one
  self-contained master (this document's immediate predecessor). Verbatim fold-in; unified
  Decisions Index D121–D145; one changelog.
- **Missing-file hunt + recovery (S96–S97):** established that **KB v1.37 has no standalone
  file** in project knowledge but its content was already absorbed into the v1.38 base (present
  in §73) — nothing lost. Found that **GitHub `docs/`** holds an older full-history archive
  including the **KB v1.37 delta** and **Umbrella v1.27 delta** (both recoverable there). The
  one true gap — the **Umbrella v1.28 consolidated base** — was **recovered by the owner from
  cold-backup kit**, along with the deep **Umbrella v1.19 delta**. Both uploaded; gap closed.
- **Umbrella consolidated → v1.31 (S99):** folded v1.28 (consolidated base) + v1.29 (S75) +
  v1.30 (S93) into one self-contained Umbrella master. Verbatim fold-in; Track-1 decisions
  note D121–D142; one changelog. Companion to this KB.
- **Runbook refreshed → v53 (S100):** the Runbook had been stale at v52 (Session 94), predating
  the arc. Reissued as a self-contained **v53** that records the arc, carries the full live
  backlog forward verbatim, and repoints the canonical set.
- **KB history-close → v1.43 (S101, this fold):** this section + changelog entry, so the KB's
  own record references its v1.42 consolidation and the Umbrella v1.31 / Runbook v53 companions.
  No live-systems content changed; §12 STATE and every prior section stand verbatim.

### §95.2 Owner directive — CANONICAL DOCS ARE SINGLE CONSOLIDATED FILES (no delta chains)
From S100 onward, each canonical document is built as **one fully-consolidated, self-contained
file with a single changelog** — never a base-plus-stacked-deltas chain. Stacked deltas over
many sessions caused the missing-file confusion this arc had to clean up. When a new canonical
version is issued, everything folds into one master; older delta files become historical only.

### §95.3 Canonical set after this arc
- **KB `Clinic_Master_KB_SystemsRegister` v1.43** (this document) — WINS on any conflict.
- **Umbrella Architecture v1.31** (consolidated, self-contained).
- **Handoff Runbook v53** (Session 100, self-contained).
- Recovered from cold kit: **Umbrella v1.28** (consolidated base) + **v1.19** delta.
- Recoverable from GitHub `docs/`: **KB v1.37** delta, **Umbrella v1.27** delta, older history.
- **Known-stale in GitHub (commit-to-repo housekeeping task, owner pushes):** repo lacks KB
  v1.38/v1.40/v1.42/v1.43, Umbrella v1.29/v1.30/v1.31, the refreshed Runbook, Call_Console v1.5,
  and the API card. Not a lost-file problem — a sync task.

### §95.4 No decisions consumed
This arc added **no new D-numbers** (it changed no system or design). Next free decision number
is unchanged at **D146**. The §95.2 documentation directive is a working-protocol standard, not
a numbered architectural decision.

---

## DECISIONS INDEX — CONSOLIDATED (D121–D145)

**Track-1 additions (D121–D134), from v1.38 base:**
- **D121** Host plan-tool as walled-off Flask+OLS VPS portal tool, key-gated. *(AMENDED by D136 — tool is PC-local, not VPS.)*
- **D122** Canonical CSV rule: newest-by-date from one fixed folder; never a Drive file-id. *(RESOLVED by D136 — clinic-PC local `data/` folder.)*
- **D123** Shared mobile → pick-list; age shown not trusted.
- **D124** Two faces: owner full version + staff BP-only version. *(Staff-page portion RETIRED by D135.)*
- **D125** Pre-fill dx/comorb; review & correct; often empty by design.
- **D126** Plan-tool never writes source; choices persist to plan_ledger.
- **D127** One vitals_ledger, one writer, two front doors; tool reads vitals back. *(Now one front door — doctor — after D135.)*
- **D128** Patient_UID = backend join/storage key; Clinic_Specific_Id = human handle.
- **D129** Patient_UID is Docterz-generated (verified); backend field, not shown at front.
- **D130** New-patient path: Clinic ID + name + mobile only; UID blank + "pending sync".
- **D131** New-patient reconciliation: stitch UID later on Clinic ID + mobile (hosted/Step-7 job).
- **D132** Archive both printout PDFs, patient-tagged (`plan_archive/<year>/<Patient_UID>/…`); new-patient PDFs → `pending/` bucket, stitched on reconciliation; ~100 MB/yr; generated server-side at hosting.
- **D133** Ledger + PDF storage home = VPS canonical; Drive mirror deferred. *(AMENDED by D137 — storage home is the clinic PC.)*
- **D134** `plan_ledger` schema +2 PDF-path columns (`Plan_PDF_Patient`, `Plan_PDF_Physio`); new 14-col order.

**Track-1 write-path (D135–D138), from v1.39 (S75):**
- **D135** Staff BP-only page retired (doctor-only vitals entry).
- **D136** Track-1 write-path PC-local; clinic-PC `data/` CSVs canonical (amends D121, resolves D122).
- **D137** PDF/ledger storage home = clinic PC → Drive sync (amends D133; structure unchanged).
- **D138** PDF engine = reportlab (pure-Python text-faithful archive).

**Track-1 front-end (D139–D142), from v1.40 (S93):**
- **D139** Front-end is its own auto-launched Flask app importing clinic_writer, separate from the live tracker; shared menu page; double-click `.bat` launch. Ports 5000 (tracker) / 5057 (vitals) never clash.
- **D140** Whole tool + engine + ledgers + archive live on **D:** (survives a Windows reformat; Drive sync is the real off-machine backup). Source CSVs stay on C:, read across drives.
- **D141** Diagnosis pre-fill mapped from `Orthopedic_Diagnosis_Taxonomy_Master.xlsx` (27 canonical categories): 12 auto-fill a rehab button, 15 blank-by-design; unmapped → "pick the exercise set", never a silent Knee-OA default.
- **D142** Bilingual archive PDF via per-run font switching (Helvetica English / NotoSansDevanagari Devanagari, engine `_mixed()`); physio PDF built from `sheetBlocks()` not screen-scraping; graceful font fallback; reportlab stays.

**Track-2 live fixes (D143–D145), from v1.41 (S94):**
- **D143** `isGenericAgent_` helper added to `OutcomeLog.gs` (generic = staff / doctor / unknown / agent / system / blank) so the Today outcome view can borrow the real caller name from the matched call when the outcome was filed under a generic label. Full-file replacement; node-check verified; deployed as New version (URL stable).
- **D144** Call-hook secret standard: the `?key=` gate for `/mo-callhook` (and similar self-chosen VPS webhook gates) shall be **plain alphanumeric, no special characters** — special chars corrupt under URL transport and caused the S94 403 outage. Applies to future rotations of these gates.
- **D145** (hygiene note) Courtesy rotation of `CALLHOOK_SECRET` + `FU_UPLOAD_SECRET` advisable at a convenient time (self-chosen VPS gate keys, NOT WABA/MyOperator tokens; low-risk; no Lokesh coordination needed).
- **D146** Staff call-sheet de-duplication in `build_staff_call_workbook` (`processor.py`): one row per patient (group mobile+name+diagnosis, keep latest `Due_Date`, older cycles hidden no-note, reinstated rows win, blank-mobile→name-only, fail-safe fallback). Staff sheet only; audit workbook untouched. Verified 07-Jul (236→214). See §102.
- **D147** Two-file-type rule + Drive-sync direction (VERIFIED-NORMAL): `consultation_report_YYYY-MM-DD.csv` = daily raw inputs, many-and-dated by design; `visit_ledger.csv` = single cumulative ledger, never dated, one fixed path. `data\` folder Drive-synced (PC writes → Drive mirrors); settle freshness depends on sync. No code. See §107.
- **D148** Staff call-sheet cap + Hard-to-Reach split in `build_staff_call_workbook` (`processor.py`): (A) `Call_Attempts ≥ 3` + no contact → Hard-to-Reach tab (name·Clinic ID·mobile·diagnosis·last-visit·attempts; reinstated exempt) for doctor keep/archive; (B) cap **120** total — winnable first, oldest-dropout drip fills leftover room, winnable overflow rolls to tomorrow; fail-safe fallback; audit untouched. Amends D146 (reinstated wins *among rows surviving settle + 3-strike*). Verified 07-Jul (cap 120, drip 10, HTR 0). See §121.

## RESERVED / OPEN DECISION NUMBERS
- **D83–D92** remain RESERVED for the pending lifecycle proposals P1–P10 (KB §55), still awaiting lock.
- **Next free decision number for new work: D149.**

---

## OPEN BACKLOG SNAPSHOT (as of S94 close — see Runbook for the live list)

**Six-item forward agenda (owner-set S94, recommended order):** (0) console `isGenericAgent_`
fix — DONE. (1) Duplicate patient entries in a day — PC-side de-dupe, SAFE, next execution item.
(2) Reconcile "didn't pick up but visited" — auto-settle on a real Docterz visit; overlaps
Track-1 Step 7. (3) Trim the >200 staff list — **DONE (S121, D148: cap 120 + Hard-to-Reach split).** (4) Live staff-activity summary on doctor dashboard — audited half
depends on item 5. (5) AI audit layer (Stage 3, D62) — overnight Haiku batch, doctor-only flags.
(6) Historical taxonomy insights — analysis only, blocked on a de-identified export.

**Track-2 live backlog:** WABA authorizer fault (D120, Lokesh, blocks all sends) · make
`wa_approve` a systemd service · rotate `WA_APPROVE_KEY` + service-account key + AKEY_14 · arm
timer-freshness checker + maintenance jobs · `clinic_health_report.py` UTC→IST fix · courtesy
rotate `CALLHOOK_SECRET` + `FU_UPLOAD_SECRET` (D145) · consider a `CALLHOOK_SECRET_MISMATCH_403`
detector (panel Failed OR no daily raw-log by mid-morning).

**Track-1 backlog:** Hindi SPELLING corrections in `vitals_page.html` LIB strings · Step 7
new-patient reconciliation (dovetails with agenda item 2) · living Clinic Data Map (§66.6).


---

## CHANGELOG
- **v1.45 — 07 Jul 2026 (Sessions 103–121, FULL EOS — live PC-side code changed):** Added §107 (S108 data-folder / Drive-sync evaluation — VERIFIED-NORMAL, D147) and §121 (Item 3 staff call-sheet cap + Hard-to-Reach split, D148). §121.0 records that Item 2 (auto-settle on return) was found ALREADY BUILT and LIVE (verified S106, 249/493 settled). `processor.py` changed and live — now carries D146 de-dupe + D148 cap/split; new md5 `171a090645da130a4f4cbb0c0b102f22`; backup `processor_BACKUP_S115_pre_Item3.py`. Decisions **D147, D148**. Next free decision number: **D149**.
- **v1.43 — 07 Jul 2026 (Session 101, EOS-light):** Added §95–100 recording the S95–S100
  documentation-consolidation arc (KB→v1.42, Umbrella→v1.31, Runbook→v53, cold-kit recovery
  of Umbrella v1.28+v1.19, GitHub-archive findings). Recorded the owner directive that
  canonical docs are single consolidated files, not delta chains (§95.2). NO live-systems
  content changed — every prior section stands verbatim. No new decisions; next free D146.
- **v1.42 — 07 Jul 2026 (Session 95, EOS-light):** FULL CONSOLIDATION. Folded v1.38 base +
  v1.39 (S75) + v1.40 (S93) + v1.41 (S94) into one self-contained master. Single unified
  Decisions Index (D121–D145) with amendment cross-references; merged Surveillance
  forward-notes; added Open Backlog Snapshot; one changelog. No content altered — verbatim
  fold-in only. Recorded that no standalone v1.37 file exists (its content lives in the v1.38
  base, present in §73). Next free decision number: D147 (D146 used at §102).
- **v1.44 — 07 Jul 2026 (Session 102):** Added §102. **FULL EOS — live PC-side code changed.** Staff call-sheet de-duplication built into `processor.py` (`build_staff_call_workbook`): one row per patient (mobile+name+diagnosis), latest `Due_Date` kept, older cycles hidden with no note, reinstated rows win, fail-safe fallback. Verified live 07-Jul (236 → 214 follow-up rows, zero duplicates). Decision **D146**. Audit workbook left un-deduped by design. Option B (per-patient latest-state join) added to priority backlog. Next free decision number: **D147**.
- **v1.41 — 07 Jul 2026 (Session 94):** Added §94. Two live fixes: call-webhook 403 outage
  (`.env` run-on-line corruption → clean key rotation + panel re-sync, D144) and doctor
  console `isGenericAgent_` undefined-function bug (D143). New fault code
  `CALLHOOK_SECRET_MISMATCH_403`. Six-item forward agenda captured (design only). Hygiene
  note D145. Decisions index → D145.
- **v1.40 — 06 Jul 2026 (Session 93):** Added §93. Track 1 Step 5 — PC-local Vitals & Plan
  front-end COMPLETE (Flask app port 5057, bilingual archive PDFs, diagnosis pre-fill from
  taxonomy master). Decisions D139–D142. Engine `clinic_writer.py` bilingual-PDF change.
- **v1.39 — 05 Jul 2026 (Session 75):** Added §75. Track 1 Step 4 — PC-local write-path
  `clinic_writer.py` BUILT + INSTALLED (20/20 selftest). Three architecture pivots
  (PC-local not VPS; staff BP page retired; storage home = clinic PC). Decisions D135–D138.
- **v1.38 — 05 Jul 2026 (Session 74, consolidation):** Consolidated master. Carried the
  v1.36 collapse (v1.33 → v1.34 → v1.35 + S67) and folded in the v1.37 delta (S73 build:
  plan_ledger row-assembly v26 + printout-PDF archiving). Decisions D132–D134.

