# S340 BUILD BRIEF — the Sanjeevni chat · 23-Oct-2026 04:03 IST → 06:02 IST

*The one paper for the next chat (session 344) and for you. Part A is for you, in plain words. Part B is the build's specification for the next chat. The detail is in the Archive §S340 and the Book §15W.*

## PART A — for you

### What you asked

1. F-1000 (the pack-change build): **no.**
2. Marg's monthly reports: a list first, and whether text files are accepted; the right cadence.
3. Marg blocks the expiry month; you keep a near-expiry list to prescribe from, and Darpan should know it too. Do we need the expiry, near-expiry and dump reports, or is the system's data enough?
4. Analyse the four exports you made (near expiry, batch-wise dump, not sold 60 days, Batch Stock for the whole store).
5. A simple plan for expiry, near expiry and dump stock — one build, not many refinement rounds — that cannot disturb the stock figures. Finalised.
6. Note your screenshots of how to export Batch Stock, the salt-wise list and the item list — for Amir, and for Ram Singh to add as report buttons in Shavez's Marg login.

### What we found

- **Text files:** expiry / near expiry, the item list and the salt-wise list are already read as text. Batch Stock and the batch-wise dump are kept but not read yet. The Tally export is not a report.
- **The system has batch and expiry on every sale and every purchase, but not stock by batch.** Only Marg's Batch Stock export gives that, so it is the one monthly input. Dump stock does not need Marg: the system's own sales show it, and Marg's "not sold" list misses most of it (it counts any movement, including October's stock vouchers).
- **From your whole-store Batch Stock (22-Oct):** 4 batches already blocked (CARTILOX SACHET, EXLAIN A, RUNVACE TP, VINBACTUM DS 25); **from 1-Nov:** REEBORN D, RIFAVAX 550, VOM L; **from 1-Dec:** 7 batches, led by **INTACOXIA-60 (865 tablets)**; 36 batches below zero in 30 medicines (12 sold with no batch); 76 items with no sale in 60 days.
- **One thing to watch (F-1008):** Marg titles three different exports "closing stock". The "not sold" list was filed as a closing stock; the system's own checks kept it out of the stock figure. The build will file these under their own names.

### What is settled (D771, D772) — nothing built

- **One export a month:** Marg's Batch Stock, whole store, saved as text on Amir's first visit (Shavez the backup). Also on that visit: the salt-wise list and the item list.
- **One list, every night, four parts:** blocked now (Amir writes off by voucher to the breakage/expiry ledger, or returns) · near expiry counted to the month Marg blocks (you prescribe; Darpan sells that batch first) · wrong-batch sales (Amir corrects in Marg monthly; new ones named the next day) · dump (no sale and no purchase in 60 days — your decision).
- **Where it shows:** your English page; one "do this" line for Darpan, one for Amir. No new staff screen.
- **Safe by design:** read-only; filed under its own name; never read as the closing stock; the test proves every stock figure unchanged.
- **How:** the mock-up first, your yes, then one build tested on your four files of today.

### Yours

1. The publish (this close's record):

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **Before 1-Nov:** REEBORN D (5 tablets), RIFAVAX 550 (5), VOM L (32) — Marg stops selling them on 1-Nov. **Before 1-Dec:** INTACOXIA-60 (865 tablets), DOLOGESIC SP (18 strips).
3. When you like: hand Ram Singh the export steps for Shavez's Marg login — the steps and your photographs are in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S340\` (folders `batch_stock_export` and `item_salt_export`).
4. Still from before: the two LINVIZ messages (Darpan, Amir); *Change dealer* on B-0161 / B-0167; Flemcort 6 with Kedar.

### Next

1. **The D771 build** — the mock-up first.
2. Kit II — the buying model (shadow first).
3. F-987; the purchase page's `staff_send`; `order.lead_days`; the S335 small list.

## PART B — the D771 build's specification (for the next chat)

**Inputs in hand (real files of 23-Oct, in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S340\samples\`):** `batch_stock_whole_20261023-051048.txt` (`2aab62ce…`, 362 rows, 239 items, as on 22-10, TOTAL 27,299), `dump_batchwise_20261023-043005.txt` (`942d8664…`, 147 rows), `not_sold_60d_20261023-044301.txt` (`104bd3c7…`, 26 rows), `near_expiry_20261023-042153.txt` (`001dcc68…`, 16 batches, TOTAL 1,217). They carry the shop's licence and phone numbers in the head: **never into the repository** (F-185) — a walk uses made-up files of the same shape, or reads these from the working-papers folder at test time.

**The text shape (Batch Stock):** shop head (6 lines) · `WHOLE STORES CLOSING STOCK AS ON dd-mm-yyyy` · rule · `S.No. Description … Batch … Expiry … Stock Unit` · rule · rows: serial (cols 0–4), name (6–35), packing (37–43), then batch, expiry `M/YYYY` (may be absent), stock `S:L` or `n` (negative `-S:L`), unit · `Batch TOTAL n` after a multi-batch item · page breaks `Continued..n` / `Page No..n` with the head repeated · `TOTAL` · `*** End of Report ***`. Rows with no unit exist (serial 328). The witness: serials 1..N unbroken; TOTAL = the sum of units by `strips × pack + loose` (the 23-Oct file re-adds to 27,301 against 27,299 — find the two units before trusting the witness).

**Recognition (F-1008):** by the columns — *Batch* and *Expiry* in the column heads → BATCH_STOCK (whole store when its item count is at or above the day's item-wise closing's, else a filtered batch list); item-wise *Total Stock* with fewer than `min_full_closing_items` → a list, never the day's closing (the not-sold list). Filed under its own type; `marg_router`, `push_snapshot`, `spine_build`'s closings and `stock_figure` never see it as STOCK_CLOSING.

**The list (nightly, read-only):** for each batch with stock > 0 — **blocked now** when expiry month ≤ this month; **near expiry** when the last sale day (the last day of the month before expiry) falls within 90 days; for each medicine — **wrong batch** when a batch is below zero beside another with stock, or a sale is against no batch; **dump** — stock > 0, no sale and no purchase in 60 days by the system's own sales (`sale_line_item` / `mi_sale_line`, `purchase_line`, matched by the spine's key). Between two exports, the daily sales lower a batch's figure and name a new wrong-batch sale the next day. `near_expiry.py`'s window corrected to the block month (F-1009) — or retired in favour of the new list (decide by reading it).

**Screens:** the owner's English page (four sections, each line with its batch, expiry, stock and the action); Darpan's tab one line *"in batches pehle bechein: …"* (D708 — do-this only); Amir's page one line *"Marg mein: … write-off / batch theek karein"* plus the monthly export card with the how-to from the screenshots (D772). No figure to type (charter rule 8).

**Files to read whole before any edit:** the medical PC's `marg_txt.py` (S604 `e8a60d9d`, TEXT_SPECS) · `/root/marg_ingest/marg_router.py` (`variant_for`, SUBSET) · `/root/marg_ingest/lib/push_snapshot.py` · `/root/finance/marg_door.py` (`_S454_KINDS`) · `/root/finance/spine/spine_build.py` (closings, `min_full_closing_items`) · `/root/finance/spine/near_expiry.py` · `/root/finance/darpan_kal.py` · `/root/finance/amir_day.py` · `/root/finance/stock_figure.py` (only to prove it unchanged).

**The proof before the publish:** every item's stock figure byte-identical with and without the new report in the archive (the S339 method: the live code rebuilt from the bundle, the spine rebuilt from MargArchive); the four sections recomputed from the 23-Oct file equal the figures above; a cold read by an independent agent; a control red on the old files.
