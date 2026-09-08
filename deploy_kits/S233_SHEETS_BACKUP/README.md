# S233_SHEETS_BACKUP — the originals, into the bundle that already works

**Session 233 · 08-Sep-2026 · ⭐1-1 of `OWNER_TODO_LIVE` · kit at v2**

---

## 1 · WHAT THIS IS

`sheets_pull.py` writes each configured Google Sheet to one CSV per tab under
`/root/state_backup/sheets/`. `clinic_state_backup.py` **v3** is the S230 file
with **one row added to `SRC_DIRS`**, so that directory rides inside the
AES-256 bundle that has gone to Drive nightly since S230 and whose restore has
been drilled and passed. **No second key, no second destination, no second
mechanism** — the owner's instruction, and the whole design.

## 2 · v1 SHIPPED EIGHT BOOKS. v2 SHIPS FOUR. THE OWNER WAS RIGHT.

v1 was installed on 08-Sep and preflight reached all eight books. **The owner
then challenged the list itself** — *"do we really need to pull all the data
from Google Drive… what should be the reason to load the VPS with this data?"* —
and the challenge held. Four books came off, each for a reason that survives a
read:

| book | v2 | why |
|---|---|---|
| `tracker` | **kept** | 19 tabs, 21,135 rows. The callback system's working core. |
| `audit` | **kept** | 4 tabs, 13,580 rows. **The original** — `console.db` is REBUILT from this sheet (`portal_console.py` keeps the transcript cache in a separate file precisely because rebuilds wipe things), so backing up the database does **not** preserve these rows. |
| `renewals` | **kept** | 2 tabs. Owned by the personal account, fed by the personal Janitor project, **no twin in the clinic account** — verified, `Clinic_Janitor.gs` only archives inbox mail and never touches renewals. |
| `payment_register` | **kept** | 1 tab. On the box as **working data** for the payments product, not as an archive. |
| `accounting_details` | dropped | the dead Google-Forms system, unmonitored, due for retirement. |
| `daily_clinic_reports` | dropped | ICICI, UPI and the vehicle log already flow to the VPS by other routes. |
| `monthly_accounting` | dropped | same family; derived from the two above. |
| `patient_diagnosis` | dropped | **already pulled** — `portal_console.py` reads it into `console.db` as patient enrichment. Pulling it twice bought nothing. |

**Not included: the call recordings.** `Call_Recordings` holds a join key and a
Drive file id per call — **never audio**. The mp3s are downloaded from
MyOperator daily by `call_recording_archive.py` and uploaded into a **new Drive
folder every month**. Sampled 08-Sep: ten calls, 432 B to 329 KB, ~165 KB mean —
on the order of a few MB a day and under a GB a year. **They have no copy
outside Google Drive, and they are the largest unprotected thing in the estate.**
Held for the owner's decision rather than slipped into a nightly job.

## 3 · WHY CSV

A CSV per tab is readable by anything, forever, with no library and no Google;
a restore is a paste. The book's shape — tab names, dimensions, row counts, md5
per tab — sits beside the data in `_BOOK.json`. **And the export states its own
age:** `_TAKEN_AT.json` records, per book, the IST time of its last success and
its row counts, and rides *inside* the encrypted bundle, so a restored bundle
can be asked how fresh its sheets are without this script and without this box.

## 4 · THE REFUSALS — a bad day must never overwrite a good backup

| what happened | what this does |
|---|---|
| a sheet is genuinely not shared | **exit 41.** The one case that means *go to Google and share it*. |
| Google rate-limits, and retrying does not clear it | **exit 43.** **The sharing is fine — re-share nothing.** |
| a tab returns zero rows, or vanished | **exit 42.** The new pull for that book is thrown away. |
| a tab lost more than `SHRINK_GUARD_PCT` (default 20%) | **exit 42**, same. |

**None of them stops the 01:50 bundle.** It ships the last good copy on disk and
records its age. Every refusal names the book and the tab.

## 5 · TWO DEFECTS OF THE ASSISTANT'S OWN, FOUND ON THE FIRST LIVE RUN

**F-372 — no pacing, no retry.** v1 fetched every tab of every book back to
back. Preflight made ~16 calls over eight seconds and reached all eight books;
the run made ~34 in under one second and **Google refused five of them**. Sheets
quota is counted per minute and this box has other writers on the same project.
v2 paces every call (`API_MIN_INTERVAL_S`, default 1.2 s) and retries a rate
refusal with backoff (`API_MAX_RETRIES`, default 5). **A permission refusal is
never retried — a retried 403 is just a slower 403.**

**F-373 — every failure wore the same words.** The quota refusal printed *"share
this sheet with the service account"*, which would have sent the owner back to
Google to re-share five sheets that were already shared correctly. **That is the
F-352 class: a message that causes a wrong action.** v2 separates the two, gives
them different exit codes, and check 28 of the walk asserts that a rate refusal
**never contains the word "share"**.

## 6 · THE PROOF — 47 checks across two walks, and the guard made to fire

```
python -B WALK_sheets_pull.py     33 checks   the exporter, against a fake Google
python -B WALK_v3_seam.py         14 checks   the SEAM — see below
```

**`WALK_v3_seam.py` exists because of F-369.** `WALK_clinic_state.py` proves the
bundler with 104 checks but **replaces `SRC_DIRS` with its own fixture list**, so
it never looks at the row S233 added. *A gate proves the rows it has and says
nothing about the rows it does not have.* The seam walk runs the **real**
exporter against a fake Google, takes the **real** bytes it writes, points the
**real** v3 `gather()` at them, and reads the collected tree back — proving a
Google Sheet now arrives inside the bundle the way `console.db` does, **and that
a wipe upstream cannot take the good copy out of it.**

**The guard is made to fail on purpose** (a selftest that cannot fail is not a
test — S232 rule 5): checks 8-9 wipe a tab and read the surviving rows back;
checks 30-31 make Google refuse twice and prove the retry carries through;
checks 32-33 make the refusal permanent and prove the good copy survives.

**Both walks found real defects before shipping:** the v1 walk caught a duplicate
label that died *after* `.staging` was created; everything that can refuse now
refuses before a single directory is made.

`WALK_clinic_state.py` passed 104 of 104 against v3 on 08-Sep. It is **not** kept
in this kit — the same file live in two places in one repository is the exact
shape of the `VPS_Push_UPI.gs` fault (D202 / F-201) this session is meant to
resolve. It is in `D:\dr-manoj-git\_to_delete_S233\` with its `WHY_SAFE.txt`. To
re-run it, copy it in beside the script it imports:

```
copy D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S230_STATE_BACKUP\WALK_clinic_state.py D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S233_SHEETS_BACKUP\
```

## 7 · THE GAP THIS KIT DOES **NOT** CLOSE — read this before believing the backup

**Measured 08-Sep-2026: `F:\ClinicBackup\S230_STATE_BACKUP\` holds
`clinic_state.key` (65 bytes) and `READ_ME_KEY.txt`. The key, and nothing else.
`ColdBackups\` holds four handoff zips and no state bundle.**

So the encrypted bundle exists **only in Google Drive**. For VPS-resident data
that is a real second home. **For a Google Sheet the chain is Google → VPS →
Google, and it never leaves the account** — which means this kit does *not*
protect against losing the Google account, the one failure Google itself cannot
cover.

**Closing that is the next kit, and it is worth more than this one.** It cannot
be a nightly job: the owner's PCs are powered off at night. It must be a
**catch-up copy that runs whenever a machine is awake** — weekly is ample, since
Drive already holds ~30 nightly revisions.

## 8 · ALSO QUEUED, NOT BUILT

- **Payment Register as a real table**, for the payments product — this kit only
  lands it as CSV.
- **The weekly script re-export** that diffs against the copy on disk — every
  script copy today is a one-off snapshot that goes stale the first time someone
  edits in the browser, and nothing says so.
- **The two personal Apps Script projects** — Janitor and the CC-statement saver.
  They run only in the personal account, feed the renewals and the Payment
  Register, and have **no second copy of any kind**. JSON exports requested.
- **Raw vehicle tracker into the VPS**, and retiring the email side of the legacy
  scripts. Recorded in `claude\S233_GAS_FUTURE_WORK.md`.

## 9 · INSTALL

`INSTALL_ONE_PASTE.txt`, one line at a time. Fifteen lines, no substitution, no
key, no secret, **and no owner action in Google** — all four books were proven
reachable by v1's preflight on 08-Sep. Step 2 keeps v1 beside it; rollback is
two lines.

---
*S233_SHEETS_BACKUP v2 · built and walked offline 08-Sep-2026 · nothing installed
by the assistant · the publish is the owner's double-click.*
