# S883_LEDGER_BATCHES — the Item ledger's batches, with expiry (18-Nov-2026, Sanjeevni session 485)

**Why.** The owner, 19:22 IST, on DISPERZYME CD's ledger: "Only one thing missing is the batch detail. I cannot confirm from here what is the
expiry of the current batches." 19:39: a compact page with folds; 19:43: "+95:0" did not read as 95 strips. 19:45: "ok" on mock-up v3
(https://claude.ai/artifact/37R4Qw5Bv2Y76emRyMTggz).

**Now** (read only; no staff screen changes):
- **Batches box** (open, under the stock figures): each batch with stock — batch, expiry mm/yy, stock, a chip (sell till / near expiry by
  `expiry.near_days` / expired / below zero), "came in" (the purchase item report's bills of that batch), and whether the batches add up to
  Marg's closing (if not, the difference named in words). From the Expiry watch's own figures: Marg's whole-shop Batch Stock less the sales
  since on their own batch plus purchases placed on their batch.
- **Each sale / sale return / purchase / purchase return line** carries its batch and expiry as Marg billed it.
- **Folded by month** (the newest open; a month with a day that needs a look opens by itself); a run of quiet days is one grey line.
- **Totals in words** ("bought 95 strips in 10 bills · sold 101 strips 5 tabs in 69 bills"); the period's purchase bills open from that line.

**Files:**
- `/root/finance/expiry_watch.py` 1ed95b6c → TO: each run also replaces a NEW table `stock_batch_now` with every batch it worked out, in its
  own transaction after the lists (a failure there is logged; the lists and Amir's fix cards stand). Nothing else changes.
- `/root/finance/item_ledger.py` b4040d8f → TO: the page (whole file, this project's own).

**Proof** (on copies of the 18-Nov database and a stock record rebuilt from Marg's archive): `synth_s883.py` 21/21 — the Expiry watch's lists
byte-for-byte the old file's (105 lines) and Amir's fix cards the same (29); every item's batch rows add up to the run's own (232 items);
pages render read-only (worst 0.54 s); DISPERZYME CD: CGD0013 12/27 5:5, CGC0262 11/27 −0:1, adds up to 5:4 = Marg. The control on the live
files: red. The earlier proofs on the new page: S845 synth 19/19, walk --box 45/45, S847 5/5, S850 26/26 (same as the live page).
**Install:** publish, then the one server line in the installer's head (it runs the Expiry watch once at the end, as the nightly does).
**Undo:** `bash /root/deploy/repo/deploy_kits/S883_LEDGER_BATCHES/undo_s883.sh`.
