# clinic_writer — PC-local Vitals & Plan writer (Track 1)

Dr. Manoj Agarwal Clinic, Bareilly. Doctor-only, PC-local. No internet, no VPS.
Lives on the D: drive (`D:\clinic_writer\`) so it survives a Windows reformat.

## What this folder is

The **write-path** for the clinic's vitals + rehab/nutrition plans:

| File | Role |
|---|---|
| `clinic_writer.py` | The engine (library): `write_vitals`, `write_plan`, `archive_pdf`, `lookup_uid_by_clinic_id`, BMI/waist maths, ID assignment, bilingual PDF. Self-test: `python clinic_writer.py --selftest` → 20/20. |
| `vitals_app.py` | Small local Flask app (port 5057). Reads the tracker's CSVs, serves the page, calls the engine to save. Bound to 127.0.0.1 (this PC only). |
| `vitals_page.html` | The browser front-end — the v25 plan-tool + a "Save to records" bridge. |
| `open_vitals.bat` | Double-click launcher (mirrors the tracker's `open_tracker.bat`). |
| `clinic_menu.html` | One-bookmark menu linking the Follow-up Tracker and this tool. |
| `NotoSansDevanagari-Regular.ttf` | Hindi font, used by `archive_pdf` to render Devanagari in the archived PDFs. |

## Data flow

1. Type a Clinic ID → app reads `patient_master.csv` + `patient_diagnosis.csv`
   (READ-ONLY) from the tracker's data folder → resolves the real `Patient_UID`
   (shared-mobile pick-list if the number is shared).
2. Age / Sex / condition pre-fill from the diagnosis file (editable on screen).
3. Enter vitals + plan choices, print as usual.
4. "Save to records" → writes one `vitals_ledger.csv` row + one `plan_ledger.csv`
   row + files both sheets as PDFs under
   `plan_archive\<year>\<Patient_UID>\<date>_<Plan_ID>_{patient|physio}.pdf`
   (new patients → `plan_archive\pending\<ClinicId>_<mobile>\…`).

## Reads (never writes)
`C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\data\`
— `patient_master.csv`, `patient_diagnosis.csv`.

## Writes (its own, on D:)
`vitals_ledger.csv` (20 cols), `plan_ledger.csv` (14 cols), `plan_archive\`.

## Install / run
1. Put all 6 files in `D:\clinic_writer\`.
2. `pip install flask reportlab` (once).
3. Double-click `open_vitals.bat` → opens http://127.0.0.1:5057/vitals

## Guarantees
- One writer per file; source CSVs never modified.
- Live follow-up tracker untouched; manual print fallback always works.
- Bilingual PDF: English via Helvetica, Hindi runs via NotoDev (per-run switch).
- Diagnosis pre-fill maps the 27 taxonomy diagnoses → 12 auto-fill, 15 blank-by-design.

## Known open (next session)
Hindi **spelling** corrections in the exercise/modality library source strings
(`name_hi` / `instr_hi`). Content & rendering are correct; only spelling to tidy.
