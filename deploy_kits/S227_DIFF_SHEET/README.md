# S227_DIFF_SHEET — the differences to check by hand, and the mismatch valued at MRP

**The owner, 06-Sep-2026, after the first real count closed:** the differences sheet to be shared with the counter as a PDF so that he can fill his responses by hand, then someone assists him to fill the same data in the Excel; and the total value of the stock mismatch at MRP, item-wise, as a separate output and part of the processing.

## What changed
| file | what |
|---|---|
| `stock_app.py` | `_pad_family` differences are now 7-tuples `(item, packing, pack, marg, counted, cost_p, mrp_p)` and `R.mismatch` carries `_pad_mismatch_totals()`: lines · short/over lines · short/over/net at MRP · priced/unpriced at MRP · the same at cost · unpriced by both. `_pad_brief` carries `mismatch`, `explained`, `diffs_pdf`, `mismatch_json`. **`_mrp_p` fixed:** sale lines are keyed by `finance_returns.norm_item()` (upper, non-alphanumerics → space), so `INTACOXIA-60` was never priced by its raw name; both spellings are asked now (`_sale_key`). `_pad_match` skips a DIFFERENCES-tab row with no recount instead of calling it "not counted". `_pad_record_answers()` writes REASON / REMARKS from the tab into `stock_diff_answer` on the item's newest difference in the family (append-only, S221). `REASON_NUMBERS` 1-7 in `STAFF_REASONS` order; `_pad_reason_key()` accepts a number, the English or the Hindi label. Routes: `GET /api/pad/mismatch/<root>` (JSON, item-wise + totals, basis MRP) · `GET /api/pad/diffs/<root>.pdf` (the hand-fill sheet, inline). |
| `pad_receipt.py` | `render_diffs(d)`: landscape A4 — head, the mismatch at MRP, how to fill, the reason legend, the table (#, Item, Pack, Marg, Counted, Difference in `25s 4t` / `pc` with `short` in the word, At MRP) and four CLOSED hand-fill boxes per row (RECOUNT strips, loose, REASON, REMARKS), a reason already on record printed faintly in its box, totals bar, signature line. MRP lines at Rs 1,000+ in bold. `_PDF` takes `landscape=`. |
| `padwriter.py` | DIFFERENCES tab is the third fill-in tab: AT MRP · AT COST · **RECOUNT STRIPS · RECOUNT LOOSE · REASON (1-7) · REMARKS** (shaded), ordered by MRP value, note with the legend and "a blank row means no change", filter. SUMMARY gains **VALUE OF THE STOCK MISMATCH (at MRP)**: short, over, net, lines without an MRP, cost beside. |
| `padreader.py` | `WANT` learns RECOUNT STRIPS / RECOUNT LOOSE / REASON; a table with a REASON column is a DIFFERENCES tab: rows come back with `kind="diff"` and `reason`, and a row with nothing written is not handed on at all. |
| `stock_check_live.html` | The box and every recent count show **Stock mismatch at MRP: short Rs … (n lines) · over Rs … (n) · n lines with no MRP on record**; an amber outlined **Download DIFFERENCES TO CHECK (PDF) — for the counter to fill by hand** with one line on what happens next; small links under each recent count. |

## Decisions
- One loop, no new store (D380): the hand sheet is a picture of the DIFFERENCES tab; the tab is what comes back; a recount is a new part (sealed figures never move, D377/D381); a reason is a row on the explanation layer.
- The mismatch is stated at MRP first (the owner's basis) with cost beside and the unpriced count always in view.
- A closed count takes no sheet — its DIFFERENCES tab is refused like any other (D381); reasons for a closed count go through the finding's buttons; a recount waits for the next count.
- Not done here: the finding report / analytics layer (next kit).

## Proof
183 checks: 41 (this walk) + 65 + 34 + 30 + 13 regressions. Sub-agent screen read fixed two things before packaging (open boxes; link colour).
