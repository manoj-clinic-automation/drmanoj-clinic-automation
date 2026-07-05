# clinic_writer/  — PC-local plan+vitals write-path

**Its own top-level folder — deliberately separate from `followup-tracker/`.**
These are two distinct systems and are kept demarcated in the repo:

- **`followup-tracker/`** — the follow-up calling/tracking system (VPS + local kit).
- **`clinic_writer/`** — THIS: the PC-side single writer for the plan + vitals tool.
  Runs on the clinic PC (`C:\clinic_writer\`), reads the tracker's local `data/` CSVs
  read-only, writes the two ledgers + the PDF archive locally, which then sync to Drive.

## What's here
- **`clinic_writer.py`** — the write-path library + a `--selftest` CLI.
  - `write_vitals(...)`   → appends `vitals_ledger.csv` (20-col locked schema); computes
                            BMI / BMI_Category (Indian cut-offs) / Waist_Height_Ratio for
                            every row; assigns `Vitals_ID` (`V-YYYY-NNNNNN`).
  - `write_plan(...)`     → appends `plan_ledger.csv` (14-col locked schema, D134); assigns
                            `Plan_ID` (`P-YYYY-NNNNNN`); links `Vitals_ID_Used`.
  - `archive_pdf(...)`    → text-faithful PDF via reportlab (D138) to the D132 archive path.
  - `lookup_uid_by_clinic_id(...)` → read-only Clinic_Specific_Id → Patient_UID.

## Invariants
Append-only · one-writer-per-file · NEVER writes the two read-only source CSVs ·
no network / no Drive / no VPS calls (Drive sync is Drive's own job on the folders) ·
IST timestamps explicit.

## Install / verify (clinic PC)
```
pip install reportlab
python clinic_writer.py --selftest        # expect: 20 / 20 checks passed
certutil -hashfile clinic_writer.py MD5   # expect: d4e20a51ead1aada8c07bead2b504100
```

## Decisions
D135 (staff BP page retired) · D136 (write-path PC-local; amends D121, resolves D122) ·
D137 (storage home = clinic PC → Drive sync; amends D133) · D138 (reportlab PDF engine).

## Not here yet
- Step 5 — the local front-end that imports these functions (next session).
- Step 7 — new-patient reconciliation.
