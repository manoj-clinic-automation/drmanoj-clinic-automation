# S206_SANJEEVNI_RECONCILE — the item-wise stock reconciliation

**What it answers.** For every item Sanjeevni stocked between 1-Apr-2026 and
26-Aug-2026: what was there on 31-March, what came in, what went out, and
whether that lands on the shelf count. Where it does not, *why* — by name, in
units, in the owner's taxonomy.

    opening(31-Mar) + purchased − returned to vendor − sold + credit notes = closing(26-Aug)

**Result.** 285 items moved. 239 land exactly. The 46 that do not carry a
named cause each; the whole gap is 1,769 units, **0.98 % of the 181,232 units
that moved through the shop**. There is no "other" bucket and no UNEXPLAINED
item.

## Files

| file | what it is |
|---|---|
| `packmap.py` | pack sizes, and the conflicts between sources. `1*N` = strip; everything else counts singly. Class comes from the **packing**, never Marg's unit label (55 of 378 labels contradict their packing). |
| `ingest.py` | the five Marg exports in one shape. Carries the three fault notes. |
| `resolve.py` | the sale report's 20-character name truncation, and the `1 *** NAME 1*1` glued cell. |
| `alias.py` | one product under two item codes. Three tests, all must pass; nothing is merged on name alone. |
| `classify.py` | every unbalanced item gets a named cause or is labelled UNEXPLAINED. |
| `selftest_reconcile.py` | 34 checks, no Marg files needed. Each corresponds to a fault that actually occurred. |
| `s1..s16_*.py` | the stages, in order. `s16_page.py` writes the browsable ledger. |

## Three faults this kit exists to not repeat

1. **Whole-unit sales read as zero.** A strip line writes `0:1`; a tube, vial
   or spray writes `1.0`. A reader that only understands the first returned
   nothing for the second — **2,807 lines, 16.3 % of the year**. Those items
   then read as dead stock while they were selling well.
2. **Credit notes counted as sales.** Bills run `A…`, credit notes run `CN…`.
   A credit note is goods coming *back*, so subtracting it makes the error
   **twice** the quantity. That doubling is the signature: TYRO BR was out by
   +704 against 352 CN units.
3. **The sale report truncates item names at 20 characters.** `HARD COLLAR ADJ
   L HOSPIK` is rung up as `HARD COLLAR ADJ L HO`, which exists in no item
   master. 11 codes, the largest carrying **574 units**. The cut can land on a
   space and be stripped, so a `len == 20` test misses the biggest ones — the
   test compares the *truncated master name*, not the length.

## Two rules that are deliberately strict

- **A pack size is never assumed.** `2:3` is 23 tablets at `1*10` and 33 at
  `1*15`. Each quantity converts with the packing printed on its own row.
  Sources that disagree are reported, not resolved: `FOLITRAX 7.5` and
  `INTACOXIA-60` carry an older pack size on the March export.
- **A size that was never recorded is never invented.** Six sizes of
  `L S BELT CONT GRAY UNISON _` cut to the same 20 characters. Those sales
  pool at the family and say so. Assigning a size to make a line balance
  would be the worst outcome available.

## Running it

    cd deploy_kits/S206_SANJEEVNI_RECONCILE
    python selftest_reconcile.py          # 34 checks, no data needed
    python s1_pack.py && python s4_final.py && python s12_stock.py \
      && python s13_money.py && python s14_monthly.py && python s15_reorder.py \
      && python s16_page.py

Nothing here writes to a live file, to the VPS, or to `ToMedical\`. It reads
the Marg exports and writes JSON plus one HTML page.
