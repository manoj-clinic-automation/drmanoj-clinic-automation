# Daily Campaign Converter — Docterz CSV → MyOperator CSV

Replaces the paste-into-Excel converter with one command. No copy-paste, no formulas.

## What it makes
From the two CSVs Docterz already gives you:
- **Follow-up logs export**  → `Export_Followup.csv`  (appointment-reminder campaign)
- **Day's consultation export** → `Export_PostVisit.csv` (app / report-access campaign)
- `Rejected_Rows.csv` → any row with a bad/blank mobile (so nothing is silently dropped)

## How to run (staff PC, once a day)
```
python3 docterz_to_myoperator.py --followup "Followup Logs.csv" --seen "Consultation Report.csv" --outdir out
```
Then upload `out/Export_Followup.csv` and `out/Export_PostVisit.csv` as **two separate**
MyOperator campaigns. (A double-click `.bat` wrapper can be added next session, like the
existing `run_patient_mirror.bat`.)

## What it cleans (same rules as the old Excel — verified identical on your 15-May sample)
- Mobile → digits only → last 10 → prefix `91`. Bad numbers (not 10 digits, or not
  starting 6-9) go to `Rejected_Rows.csv`, never into the upload.
- Skips the `Dr. Manoj Agarwal Clinic` banner row and the `Total` footer row.
- De-dupes within each campaign on the mobile.
- The malformed `99006697956` in your sample correctly became `919006697956`.

## Edit links / templates / times in ONE place
Open the file, top section `CONFIG = {...}`: appointment link, app links, clinic
contact, template names, send times. Nothing else needs editing.

## ⚠️ One thing to confirm before a real send
`template_name` in the output is only a label — MyOperator's campaign screen is where
you actually pick the template. Make sure the template you pick there is one that is
**approved on your WABA**. Your approved API templates are the `drmanoj_*` family;
`FU_Reminder_v2` / `PV_Reports_v2` came from the older template doc. Confirm which name
the **panel campaign** path expects, then set it in `CONFIG`.
