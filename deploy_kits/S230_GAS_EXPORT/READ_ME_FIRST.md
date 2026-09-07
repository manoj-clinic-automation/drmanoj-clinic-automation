# READ ME FIRST — S230 Google Apps Script recovery export

**This is a RECOVERY EXPORT, not a deployable kit.**
It is a point-in-time copy of three live Google Apps Script projects that existed in
no repository and in no backup. Nothing here has been tested, linted or adapted.
Do not treat it as a kit, do not publish from it, and do not paste it back into a
script project without reading the masking section below.

Taken: **07-Sep-2026 18:56:06 IST**
Source account: `drmka.ortho@gmail.com`
Method: Drive export, `application/vnd.google-apps.script+json`

---

## The three projects

### 1 · DailyClinicReports  → `DailyClinicReports/`
- Drive file id: `1WFQrMhcDwiaTA2IHaUR8rk5dTWmvKxGs_iL8YcFZhESGCMaBgPkyTOz9`
- Title on Drive: **DailyClinicReports**
- Live `modifiedTime`: 15-Jun-2026 15:06:24 IST
- Created: 07-Jun-2026 12:55:11 IST

| file | type | lines |
|---|---|---|
| `appsscript.json` | json | 14 |
| `Code.gs` | server_js | 963 |
| **total** | | **977** |

### 2 · Clinic Accounting Reports  → `ClinicAccountingReports/`
- Drive file id: `1pjacHFl_A41CmdVrM6ex37xzqbaGe19uleBG9Osv9mDseTgcoP8S3AcI`
- Title on Drive: **Clinic Accounting Reports**
- Live `modifiedTime`: 09-Jun-2026 23:23:59 IST
- Created: 08-Jun-2026 10:20:38 IST

| file | type | lines |
|---|---|---|
| `appsscript.json` | json | 10 |
| `Code.gs` | server_js | 786 |
| **total** | | **796** |

### 3 · UPI Reconciliation  → `UPIReconciliation/`
- Drive file id: `1DPLCtvmgLrMjMdzNK8YrIHfkmF6-oJWQOuHnrGoylkG6rSyL-cNAyTHN`
- Title on Drive: **UPI Reconciliation**
- Live `modifiedTime`: 01-Sep-2026 22:54:09 IST
- Created: 09-Jun-2026 14:17:52 IST

| file | type | lines |
|---|---|---|
| `appsscript.json` | json | 7 |
| `Code.gs` | server_js | 349 |
| `VPS_Push_UPI.gs` | server_js | 263 |
| `Bank_Statement_Filer.gs` | server_js | 114 |
| `Neft_Draft.gs` | server_js | 96 |
| `Clinic_Janitor.gs` | server_js | 94 |
| **total** | | **923** |

**Grand total: 10 files, 2,696 lines** — 2,665 of them `.gs` code.

---

## MASKING — read this before restoring anything

Rule F-185 forbids any phone number in this repository, and repository policy forbids
any secret. Four values were therefore replaced. **Line counts and line positions are
unchanged** — only the value inside the quotes was substituted.

| file | line | constant | replaced with |
|---|---|---|---|
| `DailyClinicReports/Code.gs` | 587 | `API_KEY` | `«MASKED-S230»` |
| `DailyClinicReports/Code.gs` | 588 | `COMPANY_ID` | `«MASKED-S230»` |
| `DailyClinicReports/Code.gs` | 589 | `PHONE_NUMBER_ID` | `«MASKED-S230»` |
| `DailyClinicReports/Code.gs` | 590 | `WA_TO_NUMBERS` | `«MASKED-PHONE»` |

**4 values masked, in 1 file, all four inside the `MYOP_DEFAULTS` credentials block.**
No other file in this export was altered in any way. `ClinicAccountingReports/` and
`UPIReconciliation/` are byte-identical to the live source.

### ⚠ A masked file cannot be restored without re-entering the real values
If you paste `DailyClinicReports/Code.gs` back into Apps Script as it stands, the
MyOperator / WhatsApp send path **will not work**. The four real values are recorded
nowhere in this repository, by design. The live copies are inside the running script
project; the number itself lives in `D:\Downloads\margsync\_config\`.

### The permanent fix
Do not put those values back into the source file. Move them into **Script Properties**
(Apps Script editor -> Project Settings -> Script Properties) and read them at runtime:

```javascript
var SP = PropertiesService.getScriptProperties();
var MYOP_DEFAULTS = {
  API_KEY:         SP.getProperty('MYOP_API_KEY'),
  COMPANY_ID:      SP.getProperty('MYOP_COMPANY_ID'),
  PHONE_NUMBER_ID: SP.getProperty('MYOP_PHONE_NUMBER_ID'),
  WA_TO_NUMBERS:   SP.getProperty('MYOP_WA_TO')
};
```

Once that is done, **a future export of this project is clean and fully restorable** —
no masking, no manual re-entry, and no gap between the backup and the running code.
That is the real remedy; this export is only the stop-gap.

---

## What was inspected and deliberately NOT masked

Every 7+ digit run and every long opaque string in all ten files was inspected. The
following were judged not to be secrets and were kept, because masking them would
destroy the export's only purpose while protecting nothing:

- **Google Sheet / Drive file ids** (44-char) — `ClinicAccountingReports/Code.gs`
  lines 20 and 21; `UPIReconciliation/Code.gs` lines 29 and 30. Resource identifiers
  protected by Drive permissions, not credentials; 189 files already in this
  repository carry ids of the same kind, so house convention is to keep them.
- **UPI merchant ids (MIDs)**, 15 digits — `UPIReconciliation/VPS_Push_UPI.gs`
  lines 74 and 131. Merchant identifiers used to filter bank settlement rows. They
  are not phone numbers (15 digits, not 10) and they authenticate nothing.
  **Flagged for the owner:** if you would rather they were masked too, say so and
  this export will be reissued.
- **Go-live date floors** — `ClinicAccountingReports/Code.gs` line 27 and
  `UPIReconciliation/Code.gs` line 37. Plain `YYYY-MM-DD` dates.
- **`86400000`** (milliseconds per day) — `ClinicAccountingReports/Code.gs` lines
  379, 689, 690, 718; `UPIReconciliation/Code.gs` line 346.
- **Date-format examples inside comments** — `DailyClinicReports/Code.gs` lines 139, 163.
- **Year-tag arithmetic** — `UPIReconciliation/VPS_Push_UPI.gs` line 130.
- **OAuth scope URLs** — all three `appsscript.json` files.

No patient data of any kind appears in these files.

---

## Integrity

`SUMS.md5` covers every file in this folder, paths relative to this folder.
Verify from **inside this folder**:

```
md5sum -c SUMS.md5
```

---

*Produced at Session 230. Recovery export only — the live script projects and the
manual workflow remain the system of record.*
