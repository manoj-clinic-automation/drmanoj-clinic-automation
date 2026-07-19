# Clinic Master KB / Systems Register — v1.36 (CONSOLIDATED)

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **v1.36 is a FULLY CONSOLIDATED, self-contained master.** It collapses the delta chain
> **v1.33 (last full) → v1.34 (§66 delta) → v1.35 (§67 delta)** into one document and adds the
> **Session 67 build work** (plan-tool v24 lookup + v25 vitals section) and decisions **D129–D131**.
> No earlier version is needed to read this one. **KB wins on any conflict.**
>
> **Session 67 was a full build session on Track 1** (hosted plan-tool + vitals data layer): schemas
> locked, v24 (offline patient lookup) and v25 (embedded vitals section + new-patient path) built and
> owner-approved offline, and the `Patient_UID` origin VERIFIED from a live Docterz export. **No VPS /
> live-systems code changed** — the plan-tool remains an offline Thread-A artifact until hosted.

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

**`plan_ledger.csv`** (one row per plan generation; choices-only + pointer):
`Plan_ID, Patient_UID, Clinic_Specific_Id, Patient_Name, Plan_Date, Conditions_Selected,
Comorbidities_Selected, Diet_Type, Vitals_ID_Used, Sheets_Printed, Generated_By, Written_At`

- `vitals_ledger` is append-only (repeat-visit trends accumulate). Derived values (BMI, category,
  waist:height) stored IN the ledger for reproducibility (owner wants historical progress reports).
- `plan_ledger` references vitals via `Vitals_ID_Used` (no duplicated weight to drift; blank if plan
  made with no vitals). Single source of truth for the measurement is `vitals_ledger`.

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

### §67.7 — Track 1 status after this session
- Schemas LOCKED (§67.3). v24 lookup + v25 vitals section BUILT & owner-approved OFFLINE.
- NOT yet done: hosting (Flask+OLS, D121/D122 — resolve VPS folder on the box); the separate staff
  BP-only page (D124/D127/D131); the real CSV write path; plan_ledger row assembly in the tool; the
  living Clinic Data Map (§66.6).
- Plan-tool current artifact: **v25** (`rehab_nutrition_plan_v25.html`, md5 `92e3c637d0742d3ae1775ab21f871ea1`).
  Still an OFFLINE Thread-A artifact — not hosted, not committed to the live repo.

---

## SURVEILLANCE REGISTER — unchanged since Session 64

No surveillance rows changed at S65–S67 (no live component added). The v1.32 register stands verbatim,
including the WABA-send fault row (`WABA_SEND_AUTHORIZER_500`, CRITICAL·ESCALATE-ONLY) and the
wa_approve "not yet service-monitored" note.

*(Forward-looking: when the hosted plan-tool + vitals tool become live services, each gets its own
surveillance row — liveness on its port/service. Not yet applicable; not built.)*

---

## DECISIONS INDEX (D121–D131, this consolidation's additions)
- **D121** Host plan-tool as walled-off Flask+OLS VPS portal tool, key-gated.
- **D122** Canonical CSV rule: newest-by-date from one fixed VPS folder; never a Drive file-id.
- **D123** Shared mobile → pick-list; age shown not trusted.
- **D124** Two faces: owner full version + staff BP-only version.
- **D125** Pre-fill dx/comorb; review & correct; often empty by design.
- **D126** Plan-tool never writes source; choices persist to plan_ledger.
- **D127** One vitals_ledger, one writer, two front doors; tool reads vitals back.
- **D128** Patient_UID = backend join/storage key; Clinic_Specific_Id = human handle.
- **D129** Patient_UID is Docterz-generated (verified); backend field, not shown at front.
- **D130** New-patient path: Clinic ID + name + mobile only; UID blank + "pending sync".
- **D131** New-patient reconciliation: stitch UID later on Clinic ID + mobile (hosted job); staff page
  shows no calc on screen but writer still computes derived fields (complete data).
