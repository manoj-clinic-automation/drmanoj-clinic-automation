# S228 BUILD BRIEF — the owner's rulings at the S227 close (06-Sep-2026, verbatim intent)

**Read this before anything else at S228. It replaces the staff-side design of S227_STAFF with a simpler one, and adds the owner's loss desk.**

## 1. The four live items — Marg item ledgers, analysed HERE

The owner: "just ask for the ledger for this duration and analyse here". Amir exports the item ledger from Marg as Excel and uploads it on his board; the server reads it and pinpoints the voucher. No question per span, no typing.

| item | what the owner said | what to do at S228 |
|---|---|---|
| DISPO SYRINGE NIPRO 3ML | ask for the ledger for the window, analyse here | ledger import → voucher-level analysis |
| VINTAZ P 4500 INJ | "I had merged it — it was 2 items — then sent the new stock report; so a Marg reports deficiency" | ask ledger; treat the merge as the cause; a MARG REPORT DEFICIENCY finding (the closing-stock export after an item merge) |
| TYRO BR | ask ledger, analyse here | ledger import |
| ASTOFEN SP | same | ledger import |

**Ledger import (build):** parse Marg's item-ledger Excel (date, voucher type, voucher no, party, in, out, balance); match each residue span to the vouchers inside it; name the voucher; write the conclusion. Uploaded files land in `pad_uploads/marg_answers/` (S227_CONCLUSION) — S228 reads them.

## 2. Under one strip = a stock adjustment voucher, no question

"For less than 1 strip, ask [Amir to] make a stock adjustment voucher entry — further cuts the work and the noise." Rule: |difference| < 1 strip (or 1 pc on pack-1 items) → straight to the adjustment voucher list; never a lookup, never a Darpan line.

## 3. Amir's board — simplified to TWO jobs

The owner: "so his worklist becomes simple: stock adjustment vouchers, max 8 items in a voucher, and item ledgers export and upload."

- **Box 1 "Reports the server needs"** → "Export these reports as Excel and upload here — simple, no confusion." One list of item ledgers wanted (item, from, to), one upload box. No per-span questions.
- **Box 2 "Vouchers"** → STOCK ADJUSTMENT VOUCHERS to match the physical count: the decided lines, grouped **8 items per voucher**; stock ISSUE for excess in Marg, stock RECEIVE for items to add. "He needs to export this in order to make the voucher" → one Excel per voucher batch. The Marg cleanup list, the no-movement list and the orthotics list all collapse into this: "the way to match counted stock is stock adjustment vouchers"; "all agree don't need to be there, only differences".
- **Box 3 Darpan's lists** → **move off Amir's board to the owner's page** ("move from here to a place where I own it and get it done from Darpan").
- Orthotics: no separate Excel; adjustment vouchers only for the differing lines; an orthotics stock report may be uploaded later if needed — otherwise the whole-stock report covers it.

## 4. The owner's LOSS DESK (new page, the owner's)

"A real assessment of the loss of pharmacy from my side, item and qty wise, for my record — I do the play here."

- The owner ticks items; sees loss at MRP and at purchase price; high-cost and high-volume items in an upper section.
- Shareable to Darpan on screen and printable: **A4 portrait**, core data only — item name, shortage, MRP/sale price, computed loss per item at MRP — the table builds up only from the ticked items, with a total; **saved on the VPS as the copy shared with him** (immutable, dated).
- Darpan's answers may recover some amount: the owner logs recoveries against the shared list; logs are kept for the next stock check.
- Darpan's lists in turns (S227_STAFF tranche engine) move here, under the owner.

## 5. The next system: random spot counts

"The new system will be taking physical stock counts of random items through his card and logging and matching with data; if not matched, flag him and me in addition to logging." → Darpan's card (staff page, Hindi): a few random items a day, count entered, matched against Marg + documents live; mismatch flags Darpan and the owner; every count logged; the log feeds the next full check.

## 6. Also carried from S227

Kit C (nightly Marg residue audit, pre-count readiness gate, MRP + salt import), `finance_backup.sh` + `pad_uploads/`, BLIND rows (stock_diff_lane, stock_mrp_manual, stock_count_pad_archive, stock_marg_answer, stock_tranche, setting stock.consumable_words). See `S227_STOCK_CHECK_LESSONS.md`.
