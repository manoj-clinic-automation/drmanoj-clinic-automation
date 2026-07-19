# Dr. Manoj Clinic — Umbrella Architecture · v1.26 Delta (Session 67)

**Delta on v1.25.** Carries v1.25 forward unchanged (the shared patient-data model; WABA bridge live,
sends blocked vendor-side; D116–D128). Adds the **Session 67 verification + build layer**: the
`Patient_UID` origin is now VERIFIED (Docterz-native, backend-only), the plan-tool has an offline
lookup (v24) and an embedded vitals-entry section (v25), and the new-patient reconciliation nuance is
recorded. **No live code touched — plan-tool remains an offline Thread-A artifact.** KB v1.36 wins on
any conflict.

---

## What changed architecturally this session

### 1. The data spine is now VERIFIED at its headwater (Docterz)
v1.25 drew the model with Docterz as source of truth and `Patient_UID` as the join key. Session 67
CONFIRMED, from a live Docterz export, that **Docterz itself generates `Patient_UID`** — it is a native
Docterz column, copied through by the tracker, NOT minted downstream. Crucially it is a **backend field,
invisible at the front of Docterz** (reception/owner see only Clinic ID + name + mobile at the visit).

```
DOCTERZ (headwater — VERIFIED origin of Patient_UID)
  · 55-col export: Patient UID, Clinic Specific Id, Mobile, Gender, DOB, Age, Diagnosis, Vitals(empty)
  · Patient_UID assigned at registration, but BACKEND-only (not shown at reception)
        │  (tracker ingests end-of-day / next-morning; copies UID through)
        ▼
TRACKER (clinic PC) ── derives + Drive-syncs ──► My Laptop/data/*.csv (read-only to tools)
        │
        ▼
  HOSTED TOOLS (read-only from CSVs; write only their own files)
     · plan-tool (v25 offline): lookup + dx/comorb pre-fill + embedded vitals section
     · vitals writer (hosted, to build): one writer → vitals_ledger.csv
```

### 2. New-patient flow is now a first-class path (not an edge case)
Because the UID is backend-only, a **same-day new patient** (registered today, not yet in the tracker
CSVs) is handled by capturing **Clinic ID + name + mobile** at the visit, writing the vitals/plan row
with `Patient_UID` blank, and **reconciling later** — stitching the real Docterz UID onto the row once
the tracker ingests the patient, matched on Clinic ID + mobile. This is a light hosted-stage job, not a
temporary-key scheme. (D130, D131.)

### 3. The two front doors are now precisely specified
- **Front door 2 (owner, in the plan-tool) — BUILT offline (v25):** shows BMI/category/waist:height
  live (owner is the clinician acting on them); assembles the exact `vitals_ledger` row; write deferred
  to hosting.
- **Front door 1 (staff BP-only page) — to build:** measurement fields ONLY, **no calculated outputs on
  screen**. But the SINGLE writer still computes BMI/category/ratio for the stored row, so the ledger is
  always complete regardless of which door captured the numbers. One writer, two interfaces (D127/D131).

### 4. The ledgers now have LOCKED schemas (see KB §67.3)
`vitals_ledger.csv` (append-only, derived values stored in-row) and `plan_ledger.csv` (choices-only,
references vitals via `Vitals_ID_Used`). The single-source-of-truth-for-a-measurement principle is
honoured: the weight lives once, in vitals_ledger; the plan points at it.

---

## Growth path (register)
- **Next build:** plan_ledger row-assembly in the tool (v26) → host (Flask+OLS, D121/D122) → the real
  server-side vitals writer → staff BP-only page → new-patient reconciliation job.
- **Standing:** the living "Clinic Data Map" (KB §66.6), now including the verified Docterz headwater.
- **VPS read rule:** resolve the D122 fixed-folder sync path on the box at build time (still open).

## Decisions added this session
- **D129** — `Patient_UID` is Docterz-generated (verified); a backend field, not shown at the front.
- **D130** — New-patient path captures Clinic ID + name + mobile only; UID blank + "pending sync".
- **D131** — New-patient reconciliation stitches the real UID later (Clinic ID + mobile); staff page
  shows no on-screen calc but the one writer still computes derived fields (complete data).
