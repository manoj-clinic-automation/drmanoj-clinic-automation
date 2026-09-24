# GAS_CURRENT — the repository copy of the four Apps Script projects, kept CURRENT

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
| `UPIReconciliation/` | `Code.gs`, `VPS_Push_UPI.gs`, `Bank_Statement_Filer.gs`, `Neft_Draft.gs`, `Clinic_Janitor.gs`, `appsscript.json`, `VPS_Push_Lab.gs`, `VPS_Lab_Files.gs` | six from S230; `VPS_Push_Lab.gs` from S330 (19-Sep); `VPS_Lab_Files.gs` = the S346 build (20-Sep) + **S374 (23-Sep-2026)** `_fileXray()`, the X-ray live filing + **S391 (24-Sep-2026)** `_noidCid()`, a lab report e-mailed with no clinic ID is filed once the server knows whose it is — placed in the owner's browser and re-hashed from the editor after a reload (sha256 2cd9923453457460; was 73c7edb78ddfa9e3) |
| `ClinicCallbackTracker/` | the fourteen files as the editor names them (`config.gs`, `CallField.gs.gs`, `Callconsole.gs` …), `appsscript.json` | **S279 (21-Sep-2026)**: photographed from the live editor (drmka.ortho, project *Clinic Callback Tracker*), every file sha256-matched to the editor before any change; the repository mirror `dashboard/` was byte-equal apart from a trailing newline on three files. Then `WebApp.gs` + `Dashboard.html` = the S364 build (sign in once through the Clinic app), placed in the owner's browser and re-hashed from the editor after a reload |

`DailyClinicReports/Code.gs` is compared on **shape** (line count and function names) because it is masked; every
other file byte for byte, trailing whitespace forgiven. Anything the Sunday run still reports as *added* or
*changed* against this folder is a photograph the repository does not yet hold — the assistant's to take.

`SUMS.md5` covers every file here; check it from inside this folder: `md5sum -c SUMS.md5`.
