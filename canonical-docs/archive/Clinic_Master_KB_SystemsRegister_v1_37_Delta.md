# Clinic Master KB / Systems Register — v1.37 (DELTA over v1.36 CONSOLIDATED)

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **v1.37 is a DELTA over v1.36 (CONSOLIDATED).** It folds in Session 73 (§73 below) and
> **amends the `plan_ledger.csv` schema locked in §67.3** (see §67.3-AMENDED). v1.36 remains
> the consolidated base; everything in it stands verbatim except the plan_ledger column list,
> which this delta supersedes. **KB wins on any conflict.**

---

## §67.3-AMENDED — `plan_ledger.csv` schema (supersedes the §67.3 plan_ledger column list)

The §67.3 `vitals_ledger.csv` schema is **UNCHANGED** (20 columns, as locked). Only `plan_ledger.csv`
is amended — **two PDF-path columns added** (D134) so each archived printout (D132) is linked from
the plan record.

**`plan_ledger.csv`** (one row per plan generation; choices-only + pointers) — **NEW 14-column order:**

`Plan_ID, Patient_UID, Clinic_Specific_Id, Patient_Name, Plan_Date, Conditions_Selected,
Comorbidities_Selected, Diet_Type, Vitals_ID_Used, Sheets_Printed, Plan_PDF_Patient,
Plan_PDF_Physio, Generated_By, Written_At`

- `Sheets_Printed` — which sheets were printed this visit: `Patient`, `Physio`, or both (`Patient; Physio`);
  blank if nothing printed yet.
- `Plan_PDF_Patient` / `Plan_PDF_Physio` — server-written archive path of each printout PDF (D132);
  blank if that sheet was not printed.
- `Vitals_ID_Used` — points at the same-visit `vitals_ledger` row (server links the real `Vitals_ID`
  at hosting); blank if the plan was made with no vitals.
- `Plan_ID`, `Patient_UID` — assigned/stitched server-side (blank at the offline front, per D129/D130).

Everything else about plan_ledger (choices-only, references vitals by pointer, no duplicated weight to
drift, single source of truth for the measurement is `vitals_ledger`) is unchanged.

---

## §73 — SESSION 73: plan_ledger row-assembly built (v26) + PDF-archiving locked (05 Jul 2026)

**Full BUILD session on Track 1. All offline — no VPS/live/GitHub code changed. Plan-tool remains an
offline Thread-A artifact.** Decisions **D132–D134**.

### §73.1 — Owner steering decision (recorded as context, not a numbered D)
The plan is now explicitly: **build the plan-tool + vitals tool fully, do all the backend write-path
work, and HOST BOTH TOGETHER at one time** — decide the "final online version" only once everything is
built and the backend actually works end-to-end. Offline builds (v26 onward) are **staging steps toward
the hosted product**, not deliverables in themselves. This does not change the locked Track-1 build
ORDER (Runbook §2); it changes when we treat a piece as "done" (hosting is the finish line, not each
offline approval).

### §73.2 — PDF archiving of printouts (D132/D133/D134)
- The tool prints two sheets (patient + physio) but kept no copy — no record of what a patient was
  actually given. **D132** fixes that: archive **both** PDFs per visit, tagged by patient.
- **Tagging (D132):** `plan_archive/<year>/<Patient_UID>/<Plan_Date>_<Plan_ID>_{patient|physio}.pdf`.
  New patients with no UID yet (D130) → `plan_archive/pending/<Clinic_Id>_<mobile>/…`; the reconciliation
  job (D131) moves them to the real UID folder when the tracker syncs. Yearly top folder so old years can
  be archived-off in one move.
- **Why a frozen PDF, not re-print-on-demand:** the sheet depends on live CSV lookups + on-screen choices
  + tool version; re-generating months later may not reproduce it. A frozen PDF is the true record.
- **Storage sizing:** ~0.4 MB per visit (both text PDFs). At the clinic's current load (**<10 printed
  plans/day**) that is **~100 MB/year** — negligible on VPS or free Drive (15 GB). Not a constraint.
- **Where PDFs are generated:** server-side at the hosting stage. A web page on the owner's laptop cannot
  silently save a PDF to a folder tree (browser security) — so real archiving needs the hosted server
  (the same write-path that hosts the vitals writer and plan_ledger writer). Offline, v26 only **previews
  the exact paths** that will be written.
- **Storage home (D133):** VPS canonical, Drive mirror DEFERRED. Owner confirmed Drive-browsing is not
  essential ("just save it reliably"). Reliable local writes; matches one-writer-per-file + D122; the
  live write-path never depends on Drive being reachable at print time. Drive mirror can be bolted on
  later (reuse the recording-archive OAuth-as-owner pattern, D36) if browse-anywhere is ever wanted.
- **Schema (D134):** two columns added to `plan_ledger` — see §67.3-AMENDED.

### §73.3 — v26 BUILT (offline, awaiting owner real-Chrome check)
`rehab_nutrition_plan_v26.html` — **md5 `6212ad8fe5072521cadb36b21f190ffa`**, built from v25
(`92e3c637d0742d3ae1775ab21f871ea1`), full-file replacement, 1211 lines / ~287 KB.

Adds a **"Plan record" section** — a collapsed `<details>` panel placed after the Doctor's-note group,
matching the other option groups so the front stays uncluttered. Design (owner-directed):
**button + on-demand preview only, NO live readout line** (plan choices are already visible on screen;
a live echo would clutter — owner said "it will clutter the front, skip it if possible").

- Click **Assemble plan record** → shows the exact 14-column `plan_ledger.csv` row (header + data line +
  field-by-field), nothing written offline.
- Reads REAL on-screen state: each condition block via its `data-cond`/`data-path`/`data-sev`/`data-phase`
  attributes → `Name [pathway/severity/phase]; …`; ticked comorbidities (`dm/htn/ckd/gout/thyroid` →
  full names); diet dropdown.
- **Print-flag mechanism (owner-approved):** each of the two existing print buttons sets a silent flag
  (`PLAN_PRINTED.patient` / `.physio`) — one added line each, no change to how printing works or looks —
  so `Sheets_Printed` + the two PDF-path fields truthfully reflect what was printed. Assemblable in any
  order (before or after printing), like the vitals section.
- `Plan_ID`, `Patient_UID`, `Vitals_ID_Used` correctly blank offline (server-assigned/linked at hosting).
- **Offline PDF path caveat (on-screen note added):** offline the path shows a `pending/` folder + a
  literal `<Plan_ID>` placeholder — expected, because the front never holds the backend UID (D129) and
  Plan_ID is server-assigned. On the hosted server both resolve to the patient's real UID folder + a
  real Plan_ID. The panel states this so the preview doesn't look wrong in Chrome.

**Testing:** Node `--check` parse of the full app script passed (no syntax error introduced). 3-scenario
headless logic test passed: (A) established patient, 2 conditions, 2 comorbidities, both sheets printed →
14-col row correct, conditions/comorbidities/sheets/PDF-paths all correct; (B) new patient, patient sheet
only → physio path correctly blank, routes to `pending/<clinicId>_<mobile>/`; (C) nothing printed / no
patient → soft-validation warnings fire, PDF paths blank. CSV escaping (`vitCsvCell`) reused from v25.

### §73.4 — Track 1 status after this session
- Schemas LOCKED (§67.3 vitals unchanged; §67.3-AMENDED plan_ledger). v24 lookup + v25 vitals + v26
  plan-record row-assembly BUILT & (v24/v25) owner-approved offline; **v26 awaiting owner real-Chrome check.**
- NOT yet done: hosting (Flask+OLS, D121/D122 — resolve VPS folder on the box); server-side vitals writer;
  staff BP-only page; new-patient reconciliation job; PDF archiving write path (D132/D133); living Clinic
  Data Map (§66.6).
- **Owner plan:** host plan-tool + vitals TOGETHER once the backend write-path is built.
- Plan-tool current artifact: **v26** (`rehab_nutrition_plan_v26.html`, md5 `6212ad8fe5072521cadb36b21f190ffa`).

### §73.5 — Decisions added this session
- **D132** — Archive both printout PDFs, tagged `plan_archive/<year>/<Patient_UID>/<Plan_Date>_<Plan_ID>_{patient|physio}.pdf`; new-patient PDFs to `pending/` bucket, stitched on reconciliation; ~100 MB/year (negligible); PDFs generated server-side at hosting.
- **D133** — Storage home: VPS canonical, Drive mirror deferred (owner: "just save it reliably").
- **D134** — `plan_ledger` schema +2 columns (`Plan_PDF_Patient`, `Plan_PDF_Physio`); new 14-col order (§67.3-AMENDED).

---

*End of v1.37 delta. Base: v1.36 CONSOLIDATED. Next canonical: fold this delta into a consolidated
v1.38 at the next housekeeping EOS-light, or carry the delta forward.*
