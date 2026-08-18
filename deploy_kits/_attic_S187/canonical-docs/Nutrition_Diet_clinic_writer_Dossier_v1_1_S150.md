# FROZEN DOSSIER — Nutrition/Diet Write-Path (`clinic_writer`) (v1.1, S150)

**Dr. Manoj Agarwal Clinic · Bareilly · Tier 2 (frozen, D247) · built from live GitHub source `drmanoj-clinic-automation/clinic_writer/`.**

> Canonical as-built reference for the frozen "Nutrition/Diet HTML" product — which is in fact the **`clinic_writer` vitals + rehab/nutrition write-path**, not a single static file. Not read in the session loop; hash-verified only. Change requires an explicit owner waiver (D34 discipline) + version bump. **The one open item (Hindi spelling) was CLOSED at S150 under waiver D248 — see §6 + the CHANGELOG.**

---

## 1. What it is / does

The clinic's **PC-local, doctor-only write-path** for patient vitals and rehab/nutrition plans. The front-end is `vitals_page.html` ("Personalised Nutrition & Lifestyle Plan"); a small local Flask app serves it and an engine saves the results and archives a bilingual PDF. **No internet, no VPS** — it lives on `D:\clinic_writer\` (on D: so it survives a Windows/C: reformat). It reads the Follow-up Tracker's patient CSVs **read-only** and writes only its own ledgers + PDF archive. The old standalone `plan-tool/rehab_nutrition_plan_v26.html` is the reference it mirrors byte-for-byte and is now **superseded** by this.

## 2. Where it lives

- **Clinic PC:** `D:\clinic_writer\` (all 6 files + the Hindi font).
- **GitHub (code):** `clinic_writer/` in `drmanoj-clinic-automation`. Folder digest md5 `df0b0c340fd0930c49bbc7437437262f`.

  | File | md5 | Role |
  |---|---|---|
  | `clinic_writer.py` | `0ad6d9f4…` | the engine (library): `write_vitals`, `write_plan`, `archive_pdf`, UID lookup, BMI/waist maths, ID assignment, bilingual PDF. Self-test `--selftest` → 20/20 |
  | `vitals_app.py` | `ba29a558…` | local Flask app, port 5057, bound **127.0.0.1** (this PC only) |
  | `vitals_page.html` | `fcedae30…` (**v28, S150**) | browser front-end: plan-tool base + "Save to records" bridge + **printable diet-chart sheet** + **screen-only comfort theme** (full md5 `fcedae303b620f3e5199f4b1e4766510`). Was `24ac9af4…` (v26). |
  | `clinic_menu.html` | `e5dc69df…` | one-bookmark menu linking the tracker + this tool |
  | `open_vitals.bat` | `9ba27c04…` | double-click launcher |
  | `README.md` | `e44b1898…` | component/flow reference |
  | `NotoSansDevanagari-Regular.ttf` | *(font asset)* | Hindi font for the archived PDFs |

- **Runs:** `open_vitals.bat` → `http://127.0.0.1:5057/vitals`. Deps: `flask`, `reportlab`.
- **Reads (never writes):** `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\data\` — `patient_master.csv`, `patient_diagnosis.csv`.
- **Writes (its own, on D:):** `vitals_ledger.csv` (20 cols), `plan_ledger.csv` (14 cols), and `plan_archive\<year>\<Patient_UID>\<date>_<Plan_ID>_{patient|physio}.pdf` (new patients → `plan_archive\pending\<ClinicId>_<mobile>\…`).

## 3. How it works

1. Type a **Clinic ID** → the app reads `patient_master.csv` + `patient_diagnosis.csv` (read-only) and resolves the real `Patient_UID` (with a shared-mobile pick-list when the number is shared).
2. Age / Sex / condition **pre-fill** from the diagnosis file (editable on screen). The diagnosis pre-fill maps the 27 taxonomy diagnoses → 12 auto-fill, 15 blank-by-design.
3. Enter vitals + plan choices, **print** as usual.
4. **"Save to records"** → the engine appends one `vitals_ledger` row + one `plan_ledger` row (linking the same-visit `Vitals_ID_Used`) and files **both** sheets as PDFs — bilingual (English via Helvetica, Hindi runs via NotoDev, per-run switch).
- The engine computes **BMI** (Indian cut-offs `<18.5 / <23 / <27.5`), waist:height, and assigns the next Vitals_ID / Plan_ID itself. Schemas are **locked** (20 / 14 cols) and match the plan-tool (v26) byte-for-byte.

## 4. Decisions & findings that shaped it (cited in the engine's own header)

- **D126** — the writer **never writes back** to Docterz-derived / patient files; source CSVs are read-only.
- **D127** — vitals: one `vitals_ledger.csv`, one write-function.
- **D128** — `Patient_UID` is the join key; `Clinic_Specific_Id` is the human handle.
- **D131** — BMI / vitals computation rules (computed per row).
- **D132** — the printed sheet is archived as a frozen PDF, filed on the patient.
- **D134** + **KB §67.3** — locked `plan_ledger` schema / Plan_ID linkage; frozen column order matching the plan-tool v26.
- **One-writer-per-file** — this module is the sole writer of the two ledgers + the PDF archive.

## 5. Known quirks / limits (read before ever reopening)

- **RESOLVED (S150, waiver D248):** the Hindi **spelling** tidy in the exercise/modality strings (`name_hi` / `instr_hi`) is done — the freeze caveat is closed. The exercise library is now **128** entries (was 126) and the tool now also renders an optional printable **diet-chart sheet** (see the CHANGELOG). No open cosmetic item remains.
- Bound to **127.0.0.1** — this PC only, by design; not reachable off-machine.
- Lives on **D:** so it survives a C: reformat — keep it there.
- **Schemas are locked** (20 / 14 cols) and mirror plan-tool v26 byte-for-byte — do not reorder columns.
- It reads the tracker CSVs by **absolute path** — if the tracker's data folder moves, the reader path must be updated.
- **Manual print fallback always works** (print without "Save to records").

## 6. Freeze note

**FROZEN as of S147 / D247 — owner-confirmed: freeze as-is.** Artefact = the `clinic_writer/` folder (digest `df0b0c340fd0930c49bbc7437437262f`) + the PC-local deployment on `D:\clinic_writer\`. Superseded reference: `plan-tool/rehab_nutrition_plan_v26.html` (historical).

**Waiver exercised at S150 (D248).** The carried Hindi-spelling tidy was completed under an explicit owner waiver, together with a small owner-approved batch, then the product was re-frozen with a version bump. `vitals_page.html` **v26 → v28** (md5 `fcedae303b620f3e5199f4b1e4766510`), **installed live** on `D:\clinic_writer\` (owner-confirmed). The engine, Flask app, ledger schemas and archived-PDF/print output are untouched and byte-identical. **Artefact hashes owed at install:** the `clinic_writer/` folder digest (`df0b0c34…`) must be **recomputed** on the installed folder now that `vitals_page.html` changed — until then the specific file md5 above is the pinned truth (D188: compute at freeze, don't placeholder). Absent a further waiver, no edits in the session loop.

---

## CHANGELOG

- **v1 (S147, D247)** — as-built freeze of the `clinic_writer` write-path; artefact = `clinic_writer/` folder (digest `df0b0c34…`) + PC deployment on `D:\clinic_writer\`. One open cosmetic caveat: Hindi spelling in the LIB strings.
- **v1.1 (S150, waiver D248)** — the caveat is CLOSED. `vitals_page.html` v26 → **v28** (md5 `fcedae303b620f3e5199f4b1e4766510`), installed live. Batch, all in `vitals_page.html`: (a) Hindi spelling/grammar tidy in `name_hi`/`instr_hi`; (b) exercise library 126 → **128** (Frozen-Shoulder Internal-Rotation towel; Rotator-Cuff Cross-Body) + PIVD knee-to-chest stop-rule + bottle-roll dose fix; (c) Excel `Diet_Chart` tab ported as an optional printable diet sheet (“Include diet chart” checkbox, default ON) — diet-aware meal schedule, no weekly shopping list, sections A/B/C + comorbidity (D), fed to the existing text-only archive seam with zero engine change; (d) a **screen-only** reading-comfort theme (`@media screen`; print fully isolated + byte-identical). A build-time `cond`-scope `ReferenceError` was caught by the node smoke test before delivery and fixed. Engine/app/schemas untouched. **Folder digest recompute owed at install.**

---

**END — Nutrition/Diet Write-Path (`clinic_writer`) Dossier v1.1 (S150).**
