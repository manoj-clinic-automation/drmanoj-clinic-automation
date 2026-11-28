# S543 — BATCH SWAP + MONTHLY EXPORT CONFIRMATIONS — the design (D1113, D1114; F-1752) — for the build in session 546 by Opus

*Written at the S543 close (the Sanjeevni chat, 28-Nov-2026). His look: mock-up v7 (final) — https://claude.ai/artifact/6hxWjVT8fH9JcsayFvShXX . Read this whole before building; study the live bytes first (F-472).*

## 1 · The problem (F-1752)

The Expiry watch's Near expiry list shows only the expiring batch. Last night (28-Nov run): 15 near items; **7 of them also hold a newer batch** in `stock_batch_now` — e.g. TRUECEPROL OD: batch 25S2GTA266 Dec-26 8 tabs, sold 0 since the export; batch 25S2GTC166 Aug-27 86 tabs, sold 4. His word (15:31): *the expiring batch exists only on paper in nearly all such cases* — the shop sells the newer batch while Marg still books stock to the old one. Left alone, the old batch expires in Marg and is written off as a false expiry loss.

## 2 · His rulings (D1113, 15:28 → 17:40)

1. **A case** = an item whose near-expiry batch has had **no sale since the last batch export** while another batch of the **same item** has stock (and sales). Found every night by the system; monitored to its close; flagged to him.
2. **Darpan reconfirms the shelf** (push + a card on his count page): **Nahi hai** (the usual) → the swap; **Hai, N** → those N are real: never swapped; the batch stays on Near expiry **as listed today**, marked *"Darpan found it — on the shelf · N"*; only a missing part is swapped. **No answer by 13:00** → the swap goes ahead anyway (paper is the norm), amber on his list "not reconfirmed".
3. **The swap is Darpan's, in Marg, at the counter — TWO bills a day:** Bill 1 **SALE**, customer name **STOCK**, non-cash, holding every case item on its **old** batch; Bill 2 **SALE RETURN**, name **STOCK**, the **same items in the same order** on their **newer** batches, **at the same rate**. Values are small. **Amir, vouchers and any extra export are out.**
4. **Closed by the next morning's sale report** (sale and return lines carry batch: 334 of 353 return lines on file): an item closes when its sale on the old batch and its return of the same quantity on the newer batch are both seen on STOCK bills. **One half missing** → the next morning a push to Darpan for the missing half and red on his list (the item is short in Marg meanwhile).
5. **STOCK is its own section wherever Home and Procedures appear** — Darpan's day / cash (never in the cash he hands over), the sale check (never "home/procedure not deducted"), his month table (total · UPI · cash · home · procedure · **stock adjustment**), the returns report (a STOCK return is not a customer return: out of the counter-return count and the return %), the bank / UPI match (never looked for). The label **STOCK is matched as the WHOLE customer name** (normalised), never as a substring.
6. **His page:** a new section **"Batch swaps" on the Expiry watch page, above Near expiry, COLLAPSED** — one line of counts (open · closed this month · red), tap to open: item · expiring batch · on paper · swap into · Darpan · shelf · Darpan · Marg (the two bills) · state; each row's path inline. A push only when a case turns red (last selling day within 2 days and the bills not made, or one half missing). **Real near-expiry stock** (single-batch items and Darpan's "Hai") **stays on Near expiry exactly as listed today** — no forecast section, no Prescribe-first list (dropped at 17:40).

## 3 · The monthly exports (D1114, 16:50 → 16:52)

- The monthly Batch Stock export **stays his** (no big deal). With it he exports the category-wise item list and the salt-wise item list. **No waiting is needed between exports**: on 09-Nov each reached the server ~4 s after Marg saved it (mi_file `stamp` vs `received_at`), all VERIFIED.
- **A push to his phone for each:** "Batch Stock received — whole shop, checked ✓" · "… refused — it came as a filtered list; export the whole list again" (the existing `expiry.whole_fraction` test, and any refusal by the door) · **one push when the month's set is in** ("All 3 monthly exports for November are in ✓"). A box "This month's exports" on the Expiry watch page.

## 4 · What the code already holds (read 28-Nov, the 28-Nov bundle + database copy)

- `expiry_watch.py` (S638 / S693 / S883): nightly `run()` → `stock_expiry_line` (section near …) and **`stock_batch_now`** (every batch of every item: units, printed, sold since the export, bought, pack). `owner_page()` draws the six sections; `darpan_sell_first()`, `amir_rows()`, `needs_you_lines()`; the fixes table `stock_batch_fix` (Amir's wrong-batch pairs — NOT used by this kit).
- **Purchases carry batch + expiry**: `purchase_line` (5,333 of 5,715 lines since 01-Apr) — used by S693 to place new stock on its batch. (The spine's `sp_purchase_line` has no batch — not the source.)
- Sale lines: `mi_sale_line` (bill_date, bill_no, is_return, item_name, qty, batch, expiry_ym). The customer's text (HOME MEDI / PROSIJ…) is read today by `sale_check._label_bills_missing` from `sale_item_review.raw_text` and the ingest's identity tables, and by `day_resync` (heads `home_medicine` / `procedure_medicine`, setting word lists `noncash.home_words` / `noncash.proc_words`) into `day_noncash_bill`. **First study:** where a bill's customer text and its batch lines meet (bill_no + date) — the STOCK pairing rides that join.
- Readers of the two heads: `day_resync.py`, `sale_check.py`, `returns_kinds.py` (`kind` counter | noncash), `sanjeevni_cash.py` (the month table), `darpan_app.py`, `darpan_kal.py`, `bank_match.py`, and the parent's **`finance_app.py`** (heads at ~2093, `api_home_medicine` ~5862) and **`finance_ingest.py`** (`is_home_medicine`). **finance_app.py and finance_ingest.py are the parent's: a PLANNED line on `board/_numbers` first (D646), the parent told at the close.**
- Darpan's count page: `stockmatch.html` / `stockmatch.py` (`/finance/stockmatch/`), his cards built in `stock_watch` (`roster_view`, `now_view`); his phone push at the morning list (S969). Owner pushes: the portal's push sender as used by S958/S969/S977.
- Medical-PC exports land through `marg_ingest` (mi_file: type BATCH_STOCK / CATEGORY_WISE_ITEM_LIST / SALT_WISE_ITEM_LIST / ITEM_MASTER, verdict, received_at).

## 5 · Kits (my call — the builder may split further)

- **Kit A — the swap:** case finder in the nightly (a new table `expiry_swap_case`: run, item, k20, old batch, expiry, last selling day, qty, new batch, darpan answer + n + at, bills_at, sale_seen, return_seen, closed_at, state; every write audited); Darpan's card + push (stock_watch / stockmatch); the closing judge on the next sale report; his collapsed section + red push (expiry_watch owner_page); Near expiry's "found on the shelf" mark.
- **Kit B — STOCK as a section:** the head `stock_adjustment` (label STOCK, whole name) through every Home/Procedures reader listed above — the parent's two files by a PLANNED line.
- **Kit C — export confirmations:** the per-export push + the month-complete push + the page's box (marg_ingest's filing hook; owner's devices only).

**Proof as always:** every input in its live shape; a walk with a control red on the FROM; the earlier walks the same on old and new; a rehearsal on a made-up root; cold review + second look + re-look by separate agents; NO_PHONE_NUMBERS; his publish + one server line; a live read (counts and item names only).
