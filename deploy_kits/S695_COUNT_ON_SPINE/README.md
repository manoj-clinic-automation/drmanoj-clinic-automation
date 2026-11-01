# S695_COUNT_ON_SPINE — the stock count's sale figures read from the spine

*Sanjeevni session 375 · 01-Nov-2026 · the plan's section 9, step 2; the owner's word 09:28 IST "club these and build now".*

## For the owner
The count sheet, Amir's voucher proof and your Loss desk read every sale line — what sold, what came back, the last bill the server holds,
the median selling rate — from the old sale store. Now they read the spine, the one source for what Marg says. The figures are what they
were: the lines are served in the old store's own shape and the count's own unit rule stands, so count #1 of 6-Sep reads the same to the
unit. What does change is honest: the spine holds three whole days the old store never had (19-Apr, 4-May, 27-May), so six items' median
rate and five "whole-unit" sale counts move, and three lines the old store had left unread are read whole. Nothing on any screen changes
shape or wording. If the spine cannot be opened, the old store answers as before.

## What changes — two files
`/root/finance/stock_app.py` **5433d7b7 → 5d83a852** (`make_s695.py`, nine anchored edits): `_s695_spine` / `_s695_rows_all` / `_s695_sale_rows` below
`_sale_key` (the spine's lines read once per spine build and kept in memory, keyed the old way — a count page's hundreds of asks are
dictionary look-ups, not scans); `_mrp_p`, `_r_sale`, `_r_returns`, `_item_life` (both reads), `_sales_since`, `_pursue_sales` read through them.
`/root/finance/loss_piles.py` **2b9023fd → ad0454ae** (one edit): `whole_unit_candidates` reads through stock_app's.
Two guards from the cold review: when the spine is more than a day behind the door (its gate refusing its builds, the previous spine
left in place), the old store answers and the readiness line says so; the horizon (last bill, last credit note) is whichever source is
newer, so a ten-minute spine lag never reads as a late report.
Untouched: Marg's closing figures (`stock_snapshot`) and the purchase lines — they go with the old item spine's retirement (step 5),
measured old = new again then; every table, page and word.

## The proof
- **In the device VM, on the 1-Nov database copy and the spine rebuilt from the archive:** the OLD and the NEW modules, each in its own
  process, computed for all **373 items of count #1** the sales, returns, bills and credit notes from the count's day (6-Sep) to today, the
  residue detector, the median rate, the server's horizon (last bill, last credit note), `_sales_since` whole and the whole-unit list —
  **373 of 373 items identical** in every count figure; the only differences the three extra days and the three unread lines, each named.
  **Unexplained 0.**
- `walk_s695.py`: 17 checks on made-up rows (medicines WALK…, year 2099; the count's own schema file makes its tables): the rows' shape,
  the key filter, the credit-note flag, the strict lower bound, `_pursue_sales`, `_sales_since`, the horizon, the median rate, `_item_life`,
  and the fallback to the old store — **17 of 17 green**; control on the live files **9 S695 check(s) red · 3 green**; 7 mutants (credit notes as sales, the key filter,
  both bounds, the flag, a stale cache, the horizon on the old store) all caught.
- **The installer's gate on the box:** the walk, the control, the proof on copies of the live database and spine (every count item) —
  unexplained 0 or nothing placed; after placing: finance restarted, the stock pages answer, the walk on the placed files.
  Rehearsed on a made-up root: DRY · install · ALREADY INSTALLED · a forced red at [8/8] restores both files.

## Install (the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s695kit && cp -rp /root/deploy/repo/deploy_kits/S695_COUNT_ON_SPINE /tmp/s695kit && bash /tmp/s695kit/install_S695_COUNT_ON_SPINE.sh
```
**Undo:** `\cp -p /root/finance/stock_app.py.bak_S695_5433d7b7 /root/finance/stock_app.py && \cp -p /root/finance/loss_piles.py.bak_S695_2b9023fd /root/finance/loss_piles.py && systemctl restart clinic-finance`

## Named, not done
- `purchase_app._pace` and `stock_app._alias_sale_keys` still name the old store's key shape (no read of its rows is moved by this kit);
  the old store itself is written by the ingest until step 5.
- The old store never had 19-Apr, 4-May and 27-May; the spine has them from the archive — an old fault of the ingest, recorded, not repaired.
