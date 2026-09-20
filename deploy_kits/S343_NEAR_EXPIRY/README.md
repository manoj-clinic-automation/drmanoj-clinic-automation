# S343_NEAR_EXPIRY — near-expiry from the archived expiry exports (D409)

**Project: Sanjeevni — Pharmacy & Marg · session S274 · 20-Sep-2026.** D567 **item 6**: *"Near-expiry from the archived expiry exports (D409)."* D409: *a three-month window on each batch's own expiry date.* Book §8.4: *STOCK_EXPIRY exports archive-only today* — until this kit, nothing read them.

## What it does

`/root/finance/spine/near_expiry.py` (NEW), **23:57 nightly** (one root cron line `# S343_NEAR_EXPIRY`, **declared to the parent**):

1. takes the **newest Marg expiry export the door has kept** (`/root/marg_ingest/archive/STOCK_EXPIRY/<yyyy-mm>/`) and reads it with a reader that can fail — every row classified positively (shop header · title `EXP. BEFORE …` · header · item rows `<serial> <name> <packing> | batch | M/YYYY | strips:loose UNIT` · TOTAL · Marg's footer), **witness: the serials run 1..N and TOTAL re-adds every row's units**, where a row's units are strips × pack + loose and a negative `-3:8` is −(3×pack+8). Measured on the archive: 8 of the 9 exports re-add exactly (218, 832, 781, 222, 25, 18 …); the ninth, from June 2025, fails its witness honestly (a different stock layout, rows read as 0) — the reader says so rather than guessing;
2. writes beside the spine `expiry/near_expiry_<date>.json` and `expiry/near_expiry_latest.txt`: every batch with its expiry month, months left as of tonight, **EXPIRED / NEAR (≤ 3 months) / LATER**, Marg's stock as printed, and **the spine's stock for the item today** (a batch whose item is at zero is said so); the export's age, **OVERDUE over 35 days** (the monthly export in Shavez's plan);
3. **a cross-check from the spine's own sale lines** (`sp_sale_line` carries batch and expiry per sold line): batches seen sold whose expiry is within the window and whose item still has stock per the spine, marked NOT IN EXPORT where Marg's report did not list them. The file says the caveat: a sold batch may be finished — the spine holds stock per item, not per batch.

The file's second line: *nothing here changes stock; every removal is a Marg voucher (R6).*

## Touches

Nothing existing. No screen, no tile, no table, no `finance.db`, no restart. Reads the kept exports and `spine.db` read-only. OFF: the spine's switches.

## What the first real run found (PC, 20-Sep, the 28-Aug export + the spine as of 19-Sep)

The newest export (28-Aug, 23 days old) lists **7 batches, all NEAR** (RUNVACE TP 9/2026 … RIFAVAX 550 and VOM L 11/2026), one of them (ASTOFEN R) at **−38 units in Marg** while the spine holds 44 — a Marg-side negative batch worth a look. The cross-check from the sale lines finds **35 batches seen sold expiring within 3 months with stock still on the item — 27 of them not in Marg's export**: either the export's "expire before" date was set narrower than three months, or those batches are finished. That is the question the next export answers; the file will keep asking it every night.

## Proof

- `selftest_s343.py` **16/16** on the PC: the reader on a synthetic export in Marg's exact shape (units arithmetic including the sign rule, expiry and batch as printed), **three deliberate failures** (TOTAL off by one; a row removed with the total made to add — the serial run catches it; a row that is not an item), the nightly run on a scratch spine (EXPIRED / NEAR / LATER by date, the spine's stock beside each batch, the overdue flag at 39 days, the cross-check finding a sold batch not in the export and ignoring an item at zero), no export kept, the OFF flag, no 10-digit number, and **the newest real export on the box reads OK**.
- The installer runs the selftest on the box (with the real archive), a dry run into scratch, then places the file and the cron line and runs tonight's file; red → file removed, crontab restored.

## The one line (the owner's)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S343_NEAR_EXPIRY/install_S343_NEAR_EXPIRY.sh
```
