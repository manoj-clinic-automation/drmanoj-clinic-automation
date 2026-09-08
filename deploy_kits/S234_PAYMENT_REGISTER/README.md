# S234_PAYMENT_REGISTER — the Payment Register as a real table on the VPS

**Session 234 · 08-Sep-2026 · detour item 1 of D432.**
*"start next session by completing detour, followed by sanjeevni work"*

---

## What it is

`payments_register.py` reads the pulled copy of the owner's **Payment Register**
Google sheet and keeps it as a real table in `/root/finance/finance.db`, so the
payments product he wants to build has something to query.

It is **one way**. It has no Google credential, no network call, no Sheets
library, and it cannot acquire one — the selftest asserts that the file imports
no networking module and contains no http destination.

```
Gmail → Inbox Janitor (personal GAS) → Payment Register sheet
      → sheets_pull.py 01:45 → /root/state_backup/sheets/payment_register/*.csv
      → payments_register.py 02:05 → finance.db  payment_register
```

## Why it is shaped this way

`PERSONAL_GOOGLE_PLANE_v1_S233` §2 is the whole constraint:
`registerSheet_()` inside the Janitor **creates** that sheet and appends a row
per captured payment email, remembering its id in a Script Property. **The
sheet has a live writer and it is not this box.** So the sheet is an upstream
source, never shared state — a VPS table that co-authored it would diverge in
silence.

Nothing here needs a change in Apps Script, which stays under its standing
*read, never act* hold. Nothing here needs a new pull, either: S233's
`sheets_pull.py` already brings this book down nightly, and its own header says
why — *"payment_register 1 tab. Not here as an archive — the owner wants this
ON the box as working data for the payments product."*

## Files

| file | what it is |
|---|---|
| `payments_register.py` | the whole thing: ingest · status · selftest. Standard library only. |
| `install.sh` | eleven proven stages; the schedule goes on only after the real ingest succeeded. |
| `WALK_install.py` | drives `install.sh` in a sandbox and proves each refusal actually refuses. |
| `INSTALL_ONE_PASTE.txt` | the two lines for the box, and what each exit code means. |

## Proof, before it was handed over

| gate | result |
|---|---|
| `payments_register.py selftest` | **56 checks, 0 failures** |
| `WALK_install.py` | **24 checks, 0 failures** |
| `py_compile` | clean, compiled to a temp `cfile` so no `__pycache__` reaches the publish gate (F-376) |
| **live-shape walk, 250 real rows** | 250 ingested · **250 of 250 dates read** · re-run added 0, changed 0 · 72 rows legitimately carry no amount |

The live-shape walk was run against a CSV reconstructed from the owner's own
08-Sep-2026 export of the sheet, rendered exactly as `get_all_values` would
return it. That fixture holds his private payment data and **stays out of the
repository** — it lived in scratch on manojz and nowhere else.

## The two things the live-shape walk found that no green gate would have

### 1 · The sheet has silently re-dated 95 of its own rows

The Janitor writes the date as text, day first:

```
Utilities.formatDate(m.getDate(), Session.getScriptTimeZone(), 'dd-MM-yyyy')
```

read from the project's own exported source. But of the 250 rows on
08-Sep-2026, **155 are still text and every one has a day above 12**, while
**95 are real date cells and every one has a day of 12 or less.** 155/155 and
95/95 is not chance: the spreadsheet parses an appended string as a date
whenever it *can*, reading it **month-first**. `19-07-2026` has no 19th month
and stays text; `09-07-2026` is accepted — as 7 September, when 9 July was
meant.

**What saves it:** those cells are formatted `mm-dd-yyyy`, so the sheet
*displays* the exact characters the Janitor wrote, and the pull takes displayed
values. Reading every row **day-first** therefore recovers the intent for all
250. Month-first would put 91 of 250 rows wrong by up to two months, silently.

Two tempting heuristics were tested and both are dead: **no row anywhere proves
month-first**, so a whole-file order detector learns nothing; and the sheet is
**not chronological** — 129 inversions in 249 consecutive pairs — so a
"neighbour fits between" rule has nothing to stand on. Day-first, uniformly, is
the answer, and `EXIT 44` is the tripwire for the day someone re-formats that
column in a browser and breaks the round-trip.

**For the owner, separately:** those 95 cells are *stored* in Google with day
and month swapped. Sorting that sheet by date inside Google sorts 95 rows
wrongly. The fix is upstream in a project under a read-only hold and is not
taken here. Raised as a finding at S234.

### 2 · A payment can be three rows, and a naive total is 25% too big

The register has a row per **email**, not per payment, and one renewal often
sends three — reminder, invoice, receipt. Measured: 178 rows carry an amount and
sum to **Rs 16,87,268.75**, but five vendor/date/amount groups hold ten of those
rows, so **Rs 4,29,411.39 — a quarter of the total — is the same money counted
twice.**

The **table is not de-duplicated**: it mirrors the sheet row for row, because a
table that quietly drops rows can never be reconciled against its source. The
judgement lives in a view, `payment_register_v`, where it is visible and can be
argued with: `counts_once = 1` on the first row of each group, 0 on its copies.
An honest total is `SUM(amount_paise) WHERE counts_once = 1`; a full listing is
still every row. On the live data that is **Rs 12,57,857.36 across 173
payments**.

## Design decisions worth keeping

- **`row_no` is the key** — the sheet's own 1-based row number, so the first
  payment is row 2. There is nothing in a row that is reliably unique; two
  identical renewals on one day are real, and a content hash would collapse
  them into one. The sheet is append-only, so position is stable. A blank line
  is skipped but **still consumes its number**, or every row beneath it would
  be re-labelled.
- **Money is integer paise, never a float.** `amount_raw` keeps the sheet's own
  characters so the parse can always be re-argued from the original.
- **A blank amount is NULL, not zero.** 72 of 250 rows have no amount; a zero
  would sum.
- **A changed row is written AND recorded**, field by field with old and new,
  in `payment_register_drift`. Nothing is overwritten in silence.
- **A shrink refuses.** An append-only sheet cannot lose rows on its own, so
  fewer rows than the table holds means a broken export or a deletion in
  Google. `--allow-shrink` exists but must be typed on purpose.
- **Rows that vanish are reported, never deleted.**
- **Every failure class has its own exit code and its own words** — one message
  for every failure is a message that lies (S233).
- **The table is derived and droppable.** No fact lives only here.

## Schema

```
payment_register        row_no PK · date_raw · date_iso · vendor · description
                        amount_raw · amount_paise · in_drive · gmail_link
                        content_md5 · first_seen · last_seen · revised_at · revisions
payment_register_v      the same rows + same_day_copies · counts_once
payment_register_meta   last_ingest_at · source_csv · source_pulled_at_ist · counts
payment_register_drift  at · row_no · field · was · now
```

## Exit codes

| code | meaning |
|---|---|
| 0 | ingested |
| 10 | no pulled copy of the sheet on the box — look at `sheets_pull.py` |
| 11 | the sheet's header changed in Google — nothing written |
| 12 | the database could not be opened or prepared |
| 42 | the sheet has fewer rows than the table — nothing written |
| 43 | the pulled copy is older than 30 hours — the pull is not running |
| 44 | the date column's format changed in Google — nothing written |

## What this kit deliberately does not do

- It does not touch Apps Script.
- It does not add a page, a tile or a route. Nothing on any screen changes.
- It does not change `sheets_pull.py` or the 01:50 bundle.
- It does not de-duplicate, correct or interpret the owner's data. It reads it,
  keeps it faithfully, and says what it found.

---
*S234_PAYMENT_REGISTER · Session 234 · built offline, walked against live
shapes, installed by the owner from two lines.*
