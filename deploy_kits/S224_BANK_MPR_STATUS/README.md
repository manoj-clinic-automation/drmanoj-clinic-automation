# S224_BANK_MPR_STATUS — "where is the bank MPR for <date>?" stated in one line

**Owner, 04-Sep-2026 10:45:** "there is no mention of the bank MPR that was supposed to land in the
morning; the Sept 3 statement doesn't mention it — it should say applied, waiting etc. clearly."

## What the MPR is, and where it lands (reconstructed from the papers, S217–S223)

- **MPR** = ICICI Merchant Solutions' daily merchant statement, one `.xlsx` per merchant per day,
  filename `<MID>_<DDMMYYYY>_ICICI_POS_CD.xlsx`. **A file mailed on day D carries business day D-1.**
- **Since 31-Aug the mail lands ~11:15 IST** (it used to be ~08:40). The clinic-Gmail Apps Script
  `VPS_Push_UPI.gs` **v3 (S217) pushes HOURLY** to `POST /finance/api/upi-statement` and **shouts by
  mail at 15:00** if the day's mails never came (`checkUpiArrival`, Sunday-aware).
- On the VPS `finance_upi.ingest_statement` (S208 v3, pin `21eb2556`) writes **one `upi_statement`
  row per (merchant, business day)** — `ingested_at` is the moment it was **applied**, with
  `txn_count` and `parsed_total_p` — plus the per-payment `upi_txn` rows and the raw file under
  `/root/finance/upi_statements/` (`<sha10>_<filename>`). A file failing its own Grand-Total check
  is refused whole and leaves a `data_flag` row `UPI_STATEMENT_REJECTED` (`finance_app.py:1103`).

## Why 03-Sep showed nothing

The 03-Sep business day's statement is mailed on **04-Sep ~11:15** and reaches the VPS by ~12:20.
At 10:45 on 04-Sep it was simply **not yet due** — and **no page said so**:
- `finance_clinic_day.py` (the Day Revenue page, `/finance/clinic/day/<date>`) never mentions the
  bank at all — no `upi_statement`, no "MPR", no "statement" anywhere in the module.
- `clinic_register.py` (`/finance/clinic/register/<date>`, live pin `7a1e499b`) says only
  "statement not arrived" (`bank_upi()` — known only when `MAX(txn_date)` in `upi_txn` ≥ the date),
  with no expected time, no received time and no reason.

## What this kit adds

`bank_mpr_status.py` — reads, never writes, creates no table, no `<script>`:

| state | computed from | the line |
|---|---|---|
| APPLIED | `upi_statement` row, `ingested_at` ≤ 12:20 on D+1 | `Bank MPR for Thu 03-Sep-2026 (Clinic): APPLIED at 04-Sep 12:03 IST · 17 rows, ₹12,345` |
| LATE | row, `ingested_at` > 12:20 on D+1 | `… LATE — received and applied at 01-Sep 22:54 IST (expected by ~12:20 on 01-Sep) · 6 rows, ₹5,600` |
| REJECTED | no row; `UPI_STATEMENT_REJECTED` flag naming the D+1 file | `… RECEIVED, NOT APPLIED — the file for 30-Aug was refused: <parser reason>` |
| NO ROWS | no row; raw D+1 file in the store | `… RECEIVED at <time> IST — the bank's file for 28-Aug holds NO Clinic UPI on this date` |
| WAITING | nothing, now < 12:20 on D+1 | `… WAITING — ICICI mails it ~11:15 on 04-Sep and the hourly push lands it by ~12:20 IST; not received yet` |
| NOT RECEIVED | nothing, now ≥ 12:20 on D+1 | `… NOT RECEIVED — expected by ~12:20 IST on 04-Sep; if it is still missing at 15:00 the Gmail script mails Dr Manoj` |

Routes, behind the ordinary clinic login (maker/checker on the clinic unit, like the Day Revenue page):

- `/finance/clinic/bank/mpr/<YYYY-MM-DD>` — one HTML line (a fragment any page can include); `?json=1` or `.json` for JSON
- `/finance/clinic/bank/mpr` — the last 8 days, one line each (`?days=N`, `?unit=medical` for Sanjeevni)

They live under `/finance/clinic/` because the app's front gate resolves the unit **from the path**
(`_unit_for_path`, `finance_app.py:5414`): the walk proved a clinic-only login is redirected to the
portal from any other prefix before the route runs.

## What deliberately waits

The one-line include on the Day Revenue page is **not** in this kit: `finance_clinic_day.py` is
**DECLARED-PENDING** (pin `dceb79a0` declared at the S223 close, never read back from the box —
`live_pins_S223close.txt:20`). Patching it blind breaks F-299. When the owner pastes that md5sum
(OWNER_TODO ⭐0 step 4) a two-line patch adds the line to the day page; until then the status is a URL.

## Files

- `bank_mpr_status.py` — the module (NEW on the box)
- `patch_finance_app_mpr_status_s224.py` — anchor-guarded mount, live md5 as argv, self-rollback on syntax error
- `selftest_bank_mpr_status.py` — 25/25 on a throwaway db (`EVIDENCE_selftest_s224.txt`)
- `walk_mpr_status_s224.py` — 17/17 through the REAL patched app and its REAL gate (`EVIDENCE_walk_s224.txt`)
- `INSTALL.txt` · `PREDICTED_PINS.txt` · `KIT_ID.txt` · `SUMS.md5`
