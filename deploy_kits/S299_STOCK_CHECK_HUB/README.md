# S299_STOCK_CHECK_HUB — the Stock Check tile opens every step of the count; every confirmed swap becomes Marg vouchers at once

**Session 266 (Sanjeevni project) · 17-Sep-2026 evening.** This is the held S297_STOCK_CHECK_HUB (built 17-Sep, never
published) with the owner's two fixes, under a fresh kit number because a kit that sat publishable is not edited (F-512).
S297 stays in `D:\dr-manoj-git\_to_delete\S297_STOCK_CHECK_HUB_held_17Sep\` and is never to be published.

## The asks

> *"Make a stock check tile and populate the entire flow there ... follow that format only"* (the 09-Sep orthotic workbook).

and, on reviewing S297:

> (a) *I type Darpan's answers too, not only Amir.*
> (b) *Every confirmed swap must become Marg vouchers straight away — stock issue on the short item, stock receive on the
> extra item, for the swapped quantity, reason "swap confirmed". A swap only reduces the loss burden and sanitises the
> physical stock; Marg must still be corrected to the shelf.*

## The change

Everything S297 did stands:

- **The tile** (`portal.py`) opens `/finance/stock/page/hub`. Anyone who is not the checker goes on to the counting screen.
- **The page** (`stock_hub.html`, NEW) shows count #1's eight steps in order, each with its state and its door.
- **Step 2 is Try to match**, in the workbook's columns, with Yes / No per pair.
- **A Yes takes the units off both lines.** The count's own figures never change.
- **Darpan's list waits for every answer**, then carries shortages only. Its columns are Qty in Marg | Physical <day> |
  Difference.

**Fix (a).** Step 4 is now **"Darpan's answers typed — by Amir or by you"**, with a **Type Darpan's answers** button. Amir's
board (`stock_amir.html`) opens at the typing card and says "Amir or the doctor types". The server already allowed the
checker to type.

**Fix (b).** A confirmed swap now makes two voucher lines at once:

- **STOCK ISSUE** on the short item, for the swapped quantity, reason **swap confirmed**.
- **STOCK RECEIVE** on the extra item, for the same quantity and reason.

These lines appear in three places:

1. **Amir's board** — a first block, "Swaps confirmed — stock issue and stock receive", keyed as soon as you say Yes.
2. **The Marg cleanup Excel** — a new VOUCHER column, with the swap rows first.
3. **The hub's step 6** — the swap counts, and the state moves to *now* even while other lines are still open.

The two defects found in S297 are gone:

- **A part swap** gives its lines without waiting for the rest of the line. When you decide the remainder, it runs from
  *Marg after the swap* to the shelf. Keyed in order, the two rows end exactly at the shelf.
- **A whole swap** gives its full quantity and never reads CHANGE 0. A line a swap wholly settled is not repeated among
  the decided lines.

**The orthotics cleanup sheet** no longer tells Amir to "swap the figures in Marg" himself. It says the confirmed swaps are
on the cleanup list, so nothing is keyed twice.

## The proof

**`selftest_s299.py`:** 94 checks, 0 failed. It covers:

- **The files:** the five at their live pins; anchors once; refusal; idempotence; backups; compile; the desk, hub and Amir
  scripts parse.
- **S297's behaviour checks**, all kept.
- **The S299 checks:**
  - a part swap gives STOCK ISSUE 2 at once, Marg 3 → 1, before any word;
  - a whole swap gives STOCK RECEIVE 2, Marg 0 → 2;
  - a No gives nothing;
  - every swap line says "swap confirmed";
  - no cleanup row reads CHANGE 0;
  - a decided remainder runs 1 → 0 and the chain ends at the shelf;
  - the hub and board wording.

**Rehearsed on the office PC** against the 17-Sep nightly database, through the published S288 → S294 chain
(`rehearsal_s299.txt`):

- **Before any answer:** 18 pairs are proposed (the nine orthotic pairs and eleven units of 09-Sep) and 0 swap vouchers
  exist.
- **With the orthotic pairs answered Yes** in the copy: 18 voucher lines, 9 STOCK ISSUE and 9 STOCK RECEIVE, 11 units.
- **The ankle binders** are part swaps. BAMBOO L gets its STOCK ISSUE 2 (Marg 3 → 1) at once.
- **The cleanup Excel** has 45 rows, none reading CHANGE 0.
- **Amir's board** shows 18 swap lines. Step 6 reads 9 issue and 9 receive, state *now*.
- **A write-off of BAMBOO L's remainder** adds STOCK ISSUE 1 → 0. The chain ends at the shelf.
- **Taking an answer back** removes that pair's voucher lines.

**On the box, before anything is placed,** `walk_s299.py` runs the patched module against a scratch copy of the live
database. It checks, in order:

1. the hub builds;
2. one Yes takes its units off both lines and becomes STOCK ISSUE + STOCK RECEIVE on the cleanup rows, Amir's board and
   step 6;
3. taking the Yes back restores the lines;
4. a list renders.

**The installer, rehearsed on the PC** against a copy of the live chain and the 17-Sep database, passed all four runs:

- **Install:** the walk was green and all six md5s came out as predicted.
- **Rerun:** it reported ALREADY INSTALLED.
- **A file off its pin:** it refused and installed nothing.
- **A red after placing:** it restored every file byte-identically. A red walk also placed nothing.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S299_STOCK_CHECK_HUB/install_S299_STOCK_CHECK_HUB.sh
```

**Rollback:**

1. Put back the five `.bak_S299_*` files beside the originals.
2. Remove `/root/finance/stock_hub.html`.
3. Run `systemctl restart clinic-finance clinic-portal`.
