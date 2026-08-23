# Source-data retention policy — Marg, Labmate, Docterz exports
**S195 · 21 Aug 2026 · draft for owner approval**

Covers the raw export files these systems produce (the *source documents* behind the
books), not the books themselves.

## 1. Sizing — measured, not estimated
Measured on 8 real Marg sale exports: **average 68 KB**, compressing **74%**.

| Scenario | Raw / year | Zipped / year | Zipped over 8 years |
|---|---|---|---|
| 1 report type/day (today) | 25 MB | 6.5 MB | 52 MB |
| 6 types/day (Marg + Labmate + Docterz) | 152 MB | 39 MB | **314 MB** |

**Storage volume is a non-issue.** Even the pessimistic case is ~0.3 GB over eight
years. The thing that actually scales badly is **file count** — 6 types × 365 × 8 ≈
17,500 loose files, which makes any sync client slow and any folder unbrowsable.
Policy should therefore optimise for *file count and findability*, not bytes.

## 2. Where the exports live — and where they must NOT

**VPS: never.** Not because of size, but because it reverses a deliberate design.
`api_marg_push` writes the upload to a temp file and deletes it in a `finally`
block — *"THE FILE STILL DIES IN THE REQUEST (the S186 rule, kept)"* — and an
applied push has its `parsed_json` set to NULL, *"no PHI at rest"*. Storing exports
on the VPS would undo that on purpose, and would also couple the archive's fate to
the live system's disk. Keep the VPS operational-only.

**Three copies, different failure modes:**

| Copy | Where | Role | Kept |
|---|---|---|---|
| Origin | medical PC `D:\SendToClinic\Sent\` | what the sender archived | current FY, then purge |
| Working | manojz `D:\MargArchive\` | content-named, inspectable, re-ingestable | current FY loose |
| Durable | Google Drive | offsite, survives both PCs | 8 years, monthly zips |

## 3. The mechanism — no new code needed
Put `D:\MargArchive` **inside a Google Drive for Desktop synced folder**. The puller
(`PULL_FROM_MEDICAL.bat`) already writes content-named files there, so every export
reaches Drive automatically, continuously — no monthly upload job to remember, no
extra script to maintain. This is the single highest-value step.

## 4. Retention rules

- **Source exports: keep 8 years.** They are the only re-ingestable record — the
  VPS keeps nothing, so a day can only ever be rebuilt from these or from Marg.
- **`index.csv`: keep permanently.** It is tiny and it is the ledger of what was
  ever received, with type, dates, hash and verdict.
- **Current financial year: loose files** on manojz + Drive (fast to open, easy to
  re-ingest).
- **Closed financial years: one zip per month per source**, e.g.
  `MARG_SALE_2026-08.zip`. Cuts ~17,500 files to a few hundred and saves 74% space.
- **`_spool\`: purge after 7 days** — it is transient capture, already archived.
- **`_REFUSED\` / `_UNKNOWN\`: review, then purge after 90 days.** Keep only the
  `.txt` reason files, which are diagnostic history and weigh nothing.
- **Medical PC `Sent\`: purge at the end of each FY** once Drive holds that year.

> **Not tax advice.** 8 years is chosen to sit comfortably beyond the usual Indian
> statutory expectations for financial records (GST ~72 months; income-tax record
> keeping ~6 years from the end of the relevant assessment year). **Confirm the
> retention period with your CA** — I am not a chartered accountant, and if they
> want longer, only the *cold zip* tier changes.

## 5. Naming and layout (already produced by the router)
```
D:\MargArchive\                    <- inside the Drive-synced folder
  SALE_BILLWISE\2026-08\SALE_BILLWISE_DETAIL__2026-08-19__<stamp>__<hash>.xls
  STOCK\...   PURCHASE\...   LABMATE\...   DOCTERZ\...
  _UNKNOWN\   _REFUSED\   _spool\
  index.csv
```
Every file is named by the **business date inside it**, so a day is findable years
later without opening anything. New sources (Labmate, Docterz) attach by adding a
signature to `signatures.json` — a data edit, no code change — and inherit this
whole policy automatically.

## 6. What this policy does NOT cover — and matters more
`finance.db` **is the books**; the exports are only the source documents. Its backup
is a separate and higher-priority concern (`finance/finance_backup.sh` exists in the
repo). Worth confirming separately: that it runs, where it writes, and that a restore
has actually been tested. An archive of exports is no substitute for a database
backup.

## 7. Suggested decisions for the owner
1. Approve **Drive-synced `D:\MargArchive`** as the durable copy. (biggest win)
2. Confirm **8 years** with the CA, or set the number they prefer.
3. Approve the purge rules for `_spool`, `_REFUSED`/`_UNKNOWN`, and medical `Sent\`.
4. Separately: verify `finance.db` backups run and can be restored.
