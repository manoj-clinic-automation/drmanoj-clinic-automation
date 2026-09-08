# S233_SHEETS_BACKUP — the Google Sheets, into the bundle that already works

**Session 233 · 08-Sep-2026 · ⭐1-1 of `OWNER_TODO_LIVE`**

---

## 1 · THE FAULT THIS CLOSES

S232 measured the Google plane and found one real gap. Not the code — six of the
eight script projects holding real code already have a copy on disk. **The live
Google Sheets.** The call-duration feed, the WhatsApp inbox, the doctor-only
verdicts, the accounting books, the payment register. **Zero copies anywhere:**
not on the VPS, not in this repository, not on the SSD. Searched and confirmed.

**The code can be rewritten. These cannot.**

## 2 · WHAT WAS BUILT, AND WHAT DELIBERATELY WAS NOT

The owner's instruction was exact: *put them inside the nightly encrypted bundle
that already exists, and do not invent a second mechanism.* That bundle —
`clinic_state_backup.py`, cron 01:50 — has shipped AES-256 to Drive since S230,
55 files a night, read-back verified, September pinned forever, **and its restore
has been drilled and passed.** It is the only backup leg in this estate ever
proven rather than assumed. Its key is in three places (VPS · `F:\ClinicBackup\`
· Bitwarden, D415).

So this kit is deliberately small:

| file | what it is |
|---|---|
| `sheets_pull.py` | **new.** Pulls each configured spreadsheet to one CSV per tab under `/root/state_backup/sheets/`. No network destination, no key, no upload. It writes to a directory and stops. |
| `clinic_state_backup.py` | **v3.** The S230 file, with **one row added to `SRC_DIRS`** and its state-file kit tag updated. Same walk, same tar, same key, same two owner-owned slot files, same restore. |

**No second key. No second destination. No second cron destination.** The
exporter runs at 01:45; the bundle that already runs at 01:50 picks the
directory up as one more source, exactly as it picks up `/root/staff_ledger`.

## 3 · WHY CSV

A CSV per tab is readable by anything, forever, with no library and no Google. A
restore is a paste. The book's shape — tab names, dimensions, row counts, md5 per
tab — is preserved beside the data in `_BOOK.json`.

**And the export can state its own age.** `_TAKEN_AT.json` at the root records,
per book, the IST time of its last success, its tab count and its row counts. It
rides *inside* the encrypted bundle, so a restored bundle can be asked how fresh
its sheets are without this script and without this box.

## 4 · THE REFUSALS — a bad day must never overwrite a good backup

This is the part that matters, and it is the part the walk exists to prove.

| what happens in Google | what this does |
|---|---|
| a book cannot be opened, and it exported last run | **exit 41.** Its previous export is left exactly where it is and still ships. |
| a tab that had rows returns **zero** | **exit 42.** The whole new pull for that book is thrown away. |
| a tab loses more than `SHRINK_GUARD_PCT` (default 20%) of its rows | **exit 42**, same. |
| a tab that existed last run has vanished | **exit 42**, same. |
| an ordinary fall inside the guard | taken normally. |

**An exit 41 or 42 does not stop the 01:50 bundle.** The bundle ships whatever
good copy is on disk and records its age. A refusal is never silent: every one
names the book and the tab.

## 5 · THE PROOF — 142 checks, three walks, and the guard made to fire

**A kit is proven only by a LIVE-SHAPE walk** (S208 found two defects behind 65
green checks; S209 found a page that killed a console behind four green gates).

```
python WALK_sheets_pull.py     24 checks   the exporter, against a fake Google
python WALK_v3_seam.py         14 checks   the SEAM — see below
```

**`WALK_v3_seam.py` exists because of F-369.** `WALK_clinic_state.py` proves the
bundler with 104 checks, but it **replaces `SRC_DIRS` with its own fixture list**,
so it never once looks at the row S233 added. *A gate proves the rows it has and
says nothing about the rows it does not have.* The seam walk therefore runs the
**real** exporter against a fake Google, takes the **real** bytes it writes,
points the **real** v3 `gather()` at them, and reads the collected tree back to
prove a Google Sheet now arrives inside the bundle the way `console.db` does —
**and that a wipe upstream cannot take the good copy out of it.**

**The guard is made to fail on purpose, twice** (a selftest that cannot fail is
not a test — S232, rule 5). Check 8 wipes a tab and watches the refusal; check 9
reads the surviving rows back off disk.

**The walk found a real defect in this kit before it shipped:** a duplicate label
died *after* `.staging` had been created, leaving it behind for the next run.
Everything that can refuse now refuses before a single directory is made.

To re-run the S230 walk against v3 — it must sit beside the script it imports:

```
copy D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S230_STATE_BACKUP\WALK_clinic_state.py D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S233_SHEETS_BACKUP\
```

It passed 104 of 104 against v3 on 08-Sep-2026. The copy was **not** kept in this
kit: the same file live in two places in one repository is the exact shape of the
`VPS_Push_UPI.gs` fault (D202 / F-201) this session is meant to resolve. It is in
`D:\dr-manoj-git\_to_delete_S233\` with its `WHY_SAFE.txt`.

## 6 · THE BOOKS, AND HOW THEY WERE CHOSEN

Every id in the install line was read from **code that runs** — `gspread`
call sites on the VPS and `openById` in the live Apps Script — and then
confirmed against the clinic account's own Drive listing. None was recalled.

| label | what it holds | how it was found |
|---|---|---|
| `tracker` | Clinic Callback Tracker — `Call_Durations`, `WA_Inbox`, `Followups_Today`, `Call_Recordings`, `Followup_Outcomes` | ten `open_by_key` sites |
| `audit` | Call Audit (Doctor Only) — `Call_Verdicts` | `portal_console.py`, `call_verdict.py` |
| `accounting_details` | Accounting details — the UPI reconciliation source | `UPIReconciliation/Code.gs` |
| `daily_clinic_reports` | Daily Clinic Reports | `UPIReconciliation`, `DailyClinicReports` |
| `monthly_accounting` | Monthly Accounting Reports | `ClinicAccountingReports` |
| `payment_register` | Payment Register | Drive; owned by the personal account, shared in |
| `patient_diagnosis` | patient_diagnosis | a VPS `open_by_key` site |
| `renewals` | Renewals Master v2 — the doctor's portal tile | `portal.py`, `finance_app.py` |

**Eight books, not seven.** The S232 note counted `Call_Durations`, `WA_Inbox`
and `Call_Verdicts` as three items; they are **tabs**, and they live in two
books. Counting by book, and adding `patient_diagnosis` and `renewals` which the
S232 list did not name, the live set is eight. Backing up a book backs up every
tab in it, whatever it is called, so the unit here is the book.

⚠ **`renewals` may need a share.** Read from the clinic account on 08-Sep-2026,
that id answered *not found* — consistent with a sheet owned by the personal
account and never shared to the clinic one, which `portal.py`'s own comment
describes ("access stays gated by Google login"). **Preflight will say plainly**
whether the service account can read it. That is what preflight is for, and it
is why step 8 comes before step 9.

## 7 · WHAT IS **NOT** IN THIS KIT, and why

**`Trip.csv` is out of scope, deliberately.** It is not a Google Sheet: it is a
family of dated CSV files in a Drive folder, one per day, written by the vehicle
tracker. Covering a Drive folder of loose files is a different mechanism, and the
owner's instruction was to invent none. It also sits inside the work he set aside
on 08-Sep: the vehicle-tracker analysis has **already migrated to the VPS** and
its email part is to be retired. Recorded in `claude\S233_GAS_FUTURE_WORK.md`.

**The weekly script re-export is not in this kit either.** It is ⭐1-1's second
half — every script copy on disk today is a one-off snapshot that goes stale the
first time someone edits in the browser, and nothing says so. Separate kit.

## 8 · INSTALL

`INSTALL_ONE_PASTE.txt`, one line at a time. Sixteen lines, no substitution, no
key, no secret. **Step 8 is the gate:** it reads every book, writes nothing, and
names any sheet the service account cannot see. Do not go past it until it ends
`PREFLIGHT OK`.

**Rollback is two lines** and is in that file. Step 2 keeps the running v2 beside
it before anything is replaced.

---
*S233_SHEETS_BACKUP · built and walked offline 08-Sep-2026 · nothing installed by
the assistant · the publish is the owner's double-click.*
