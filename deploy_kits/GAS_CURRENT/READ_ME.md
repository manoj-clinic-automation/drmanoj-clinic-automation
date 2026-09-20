# GAS_CURRENT — the repository copy of the three Apps Script projects, kept CURRENT

**This is a LIVING folder, not a kit** (the `KB_canon_all` precedent). It is what `gas_export.py`'s second
comparison — *"how stale is the copy people read"* — reads every Sunday 02:20 IST, through the conf line
`GAS_REPO_COPY=/root/deploy/repo/deploy_kits/GAS_CURRENT` set by kit S352 (F-591). `S230_GAS_EXPORT/` stays
frozen as the 07-Sep-2026 photograph and is never edited again.

**The rule (S277, D583):** every Apps Script change the assistant places in the owner's signed-in browser updates the
matching file HERE in the same breath, and `SUMS.md5` is regenerated. A change that reaches Google and not this
folder is exactly what the Sunday run will report as *the repository copy is behind*.

| project | files | where each came from |
|---|---|---|
| `ClinicAccountingReports/` | `Code.gs`, `appsscript.json` | S230 photograph (07-Sep-2026), unchanged since |
| `DailyClinicReports/` | `Code.gs` (v6.1, **masked** — four MyOperator values, S230 §4), `appsscript.json` | `Code.gs` from S348 (20-Sep-2026); `appsscript.json` from S230 |
| `UPIReconciliation/` | `Code.gs`, `VPS_Push_UPI.gs`, `Bank_Statement_Filer.gs`, `Neft_Draft.gs`, `Clinic_Janitor.gs`, `appsscript.json`, `VPS_Push_Lab.gs`, `VPS_Lab_Files.gs` | six from S230; `VPS_Push_Lab.gs` from S330 (19-Sep); `VPS_Lab_Files.gs` = the S346 build (20-Sep) |

`DailyClinicReports/Code.gs` is compared on **shape** (line count and function names) because it is masked; every
other file byte for byte, trailing whitespace forgiven. Anything the Sunday run still reports as *added* or
*changed* against this folder is a photograph the repository does not yet hold — the assistant's to take.

`SUMS.md5` covers every file here; check it from inside this folder: `md5sum -c SUMS.md5`.
