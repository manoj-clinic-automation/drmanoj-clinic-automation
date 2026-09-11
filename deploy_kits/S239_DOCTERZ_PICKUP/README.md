# S239_DOCTERZ_PICKUP — the Docterz exports, picked up by themselves

**The owner, 11-Sep-2026:** *"automatic pickup of the reports — consultation report and follow-up
logs — from my Downloads folder, and process them; then the manual system either retires or
becomes a fallback. The tracker continues at my PC only."*

## What it does
Every 5 minutes, hidden, `docterz_pickup.py` looks in `D:\Downloads` for Docterz CSVs, identifies
each by its **header** (consultation report · follow-up log · clinical data report), and:

1. **copies** each new one into `D:\Downloads\DocterzArchive\<TYPE>\<YYYY-MM>\`, named by the
   **business date read from inside it** — nothing in Downloads is moved or deleted;
2. decides per business day: new day or a late-comer → **run**; identical → skip; same patients with
   different money on a recent day and a newer export → **run (newest wins)**; an older export →
   skip; **fewer patients than the tracker holds → quarantine + shout**;
3. cuts a **multi-day** report into one file per day (the tracker's Day Revenue reader stamps every
   row with the report's latest date, so a range report fed whole would put a week's money on one day);
4. runs the tracker's own `processor.run_daily()` — exactly what `/run` calls — then, for the
   **latest** business day only, the `/run` VPS upload and `push_patient_join.py --push`;
5. rebuilds `outputs\Day_Tenders.csv` with **one row per leg** (newest export wins per bill).

`/run` stays as the fallback, untouched. If both process the same export, the second does nothing.

## Also in this kit — `revenue.py`, the S223 parser fix, finally installed
- `split_payment()` reads **all seven** Docterz tender names (was two): Wallet, Debit Card, Patient
  APP legs are no longer dropped. `online` = every non-cash tender.
- `parse_day_revenue()` keeps only **UID-shaped** rows (F-93): the payment footer's cells no longer
  reach the Day Revenue sheet as phantom visits.
- **Install gate:** the live file must hash `a15d776e9e9e070adb89a38b2a205473`. Backup kept beside it.

## Files
| file | goes to |
|---|---|
| `docterz_pickup.py`, `DOCTERZ_PICKUP.bat`, `RUN_HIDDEN.vbs`, `revenue.py` | the tracker folder |

## The one owner action — one line on manojz
```
C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\START_DOCTERZ_PICKUP_NOW.bat
```
Step 1 (`--refresh-latest`, rev 2): re-makes today's call list from the latest business day and the newest
follow-up log, sends it to the VPS (so it is the newest there) and writes it straight into the call-list tabs
with `push_followups_today.py`. Step 2: registers the `DocterzPickup` task (every 5 minutes, hidden) and runs
the first pass.

**Why rev 2 (11-Sep, 08:08):** the owner re-ran the missing 08-Sep day on `/run`; its hook sent the 08-Sep
workbook to the VPS, and the VPS pusher takes the NEWEST-ARRIVED workbook (`push_followups_vps.py`
`find_workbook()`, max by mtime) — so staff were shown 08-Sep's call list on 11-Sep. The pickup never sends an
old day; the VPS pusher should pick by the date in the name (separate one-line VPS fix).
Undo: `schtasks /Delete /TN "DocterzPickup" /F` · revenue undo: copy `revenue.py.bak_S239_a15d776e` back over `revenue.py`.

## Where to look
`D:\Downloads\DocterzArchive\_last_pass.txt` (heartbeat) · `_pickup_log.txt` · `DOCTERZ_SHOUTS.txt` · `index.csv`.
