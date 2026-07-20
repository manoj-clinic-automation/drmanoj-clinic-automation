# Surgical Case Pack — clinic-PC install (the vitals-app way)

One-time setup, 6 steps, ~5 minutes. Nothing touches the tracker's data\ folder,
the Vitals tool, or Google Drive. Everything this tool writes stays in
`D:\surgical_casepack\` (local PC only — NOT Drive-synced, by design).

## Install (one time)

1. On the clinic PC, make the folder:  `D:\surgical_casepack`
2. Copy these 3 files into it:
   - `casepack_app.py`
   - `casepack_page.html`
   - `open_casepack.bat`
3. Open `casepack_app.py` in Notepad and check ONE line near the top:
   `DATA_DIR = r"C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\data"`
   If your tracker data folder is elsewhere, correct this path. Save, close.
4. Flask is already installed (Vitals tool uses it). If a fresh PC ever needs it:  `pip install flask`
5. Double-click `open_casepack.bat`. Browser opens `http://127.0.0.1:5058/case`.
6. Test: Case pack → type a Clinic ID in the patient box → pick the patient →
   press **Save case** → confirm `case_ledger.csv` and a folder under
   `case_archive\2026\<UID>\` appeared. Done.

## Daily use

- Keep the black window minimized (same habit as Vitals).
- Phone/offline: the SAME `casepack_page.html` file still works opened directly —
  there, Save case downloads a `*_case.json`; drop such files into
  `D:\surgical_casepack\case_archive\inbox\` when convenient.

## What goes where

| File | Written by | Contains |
|---|---|---|
| `case_ledger.csv` | this app only | one row per saved case (IDs, procedure, estimate total, file paths) |
| `case_archive\YYYY\UID\..._bundle.json` | this app only | frozen full case: estimate + OT list + consent + notes |
| `case_archive\YYYY\UID\..._consent.html` | this app only | printable consent exactly as edited |
| tracker `patient_master.csv` / `patient_diagnosis.csv` | READ-ONLY here | never modified by this tool |

## Ports (never clash)
tracker 5000 · vitals 5057 · **case pack 5058**

## Later (separate session, Clinic Systems & Automation project)
- Tracker app.py "Cases" page reading this ledger for per-patient history
- Consent library evolution ships as new casepack_page.html full-file replacements
