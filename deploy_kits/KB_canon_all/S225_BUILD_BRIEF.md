# S225 BUILD BRIEF — the one document to read before S226

*Written at the S225 close, 06-Sep-2026 04:00 IST. Replaces the five S225 papers for orientation; they remain the record (`S225_OWNER_RULINGS_04SEP` · `S225_PROCEDURES_RULED` · `S225_FOLLOWUP_TRACKER_STUDY` · `S225_STOCK_CHECK_READINESS` · `OWNER_TODO_LIVE`). Lives in project knowledge, `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S225\`, and loose on the SSD.*

## WHAT S225 WAS

Fifteen attended hours over two calendar days. It built the whole staff purchase-order flow the owner dictated at S224 (seven kits, seven read-backs), put the already-verified NEFT vendor bank accounts into the new phone book at his ALL-CAPS instruction, and — when the drift page honestly said *"our computed figure: never received"* — found why from the logs, fixed it at the event instead of the clock, and read both first-day differences to the bill and the item master. It ran through a model switch (his budget) and three gate refusals of the assistant's own work, all corrected at source.

## WHAT IS LIVE, AND ITS PINS (every VPS pin read back from the box by the owner; every manojz pin hashed on manojz)

| where | file | pin | what |
|---|---|---|---|
| VPS | `/root/finance/purchase_app.py` | `3adad7f983228ea3bbb5ea635c8ce872` | **rev 12** — the §8 flow (staff order page · phone book · arrival · live cross-check + in-transit · new items · Amir's salt list with Marg's list beside it) + the inline phone book with FULL bank details to the three editors (D375) |
| VPS | `/root/staff_ledger.py` | `802577112e6db82bcf763d142efcd00c` | rev 3 — `/ledger/loans` (D371), the agreed-schedule box, approve-then-attach (D374) |
| VPS | `/root/finance/finance_clinic_day.py` | `713bdf3a9c1a8dafe076be1feb32219a` | the bank-MPR status on the Day Revenue page and month table, with the link |
| VPS | `/root/portal/portal.py` · `tile_grants.json` v8 | `7bc59115…` · `07af4daa…` | 🛒 Order Medicines tile for the five |
| VPS | `finance.db` `purchase_vendor_contact` | *(state)* | 24 NEFT vendors: full account + IFSC; 22 VERIFIED by the owner's ruling, 2 UNVERIFIED as flagged; 17 still without a phone |
| manojz | `MargPull\PULL_FROM_MEDICAL.bat` | `39bd6ac8ba7333f0e4182812fc2d2702` | the 10-minute pull runs both on-capture pushers at the end of every cycle |
| manojz | `MargPull\expected_on_capture.py` · `EXPECTED_ON_CAPTURE.bat` | `bd8565d6…` · `4dadfbe4…` | new sale **or purchase** export → `push_purchases.py`, then `PUSH_STOCK_DAILY.bat`; task *MargExpectedOnCapture* (15 min, backstop) |
| manojz | `MargPull\snapshot_on_capture.py` · `SNAPSHOT_ON_CAPTURE.bat` | `6a0c0cd4…` · `8c7df877…` | Marg's closing stock pushed on capture; task *MargSnapshotOnCapture* |
| manojz | `MARG_WALL_CARD.html` | `f2b341ddd2b60c36b432cb9ae4d3dc3b` | D376 on the card; **reprint owed (F-310)** |

`healthz` exports=18. Baseline for the computed stock: **03-09-2026** (kept, with a note).

## THE OWNER'S RULINGS (minted D371–D376; his words in the papers)

D371 advances unparked, a clean loans view first · D372 the August close terms · D373 procedures as ruled · D374 SPECIAL approve-then-attach · **D375** NEFT bank details VERIFIED as they stand and shown in full to the three editors (the one logged D370 exception) · **D376** the sale report every morning for the last two days, closing stock after purchases, negatives don't block, the baseline stays, the computation to move to the server.

## THE STOCK CHECK — WHERE IT STANDS

Arithmetic ready: 05-Sep computed vs Marg **372/373**; the two differences explained (LACTOVAX — a duplicate item master, merged by the owner; BIO D3 MAX — bill A003396 entered after its day's report; from his own Marg ledger, reconciled to the unit). Delivery fixed: on capture, inside the pull cycle, proven unattended at 02:50 06-Sep. Day 1 = 05-Sep on `https://followup.dr-manoj.in/finance/stock/page/drift`. Amir's login opens `/finance/stock/page/count`; the five named staff see it on their own card (`cards_registry.json`). Thirteen items below zero on both sides until Amir's purchase exports for 04-Sep onward. **Owed:** the data-readiness lines on the drift and count pages and the logged check-result format (his spec, `S225_STOCK_CHECK_READINESS` §7); the server-side computation after one proven morning (§8); the S208 kit revision for F-319 · F-322 · F-323.

## THE FINDINGS

F-320 (a kit reinstalled at rev 1 while rev 2 was published — closed) · F-321 (a walk that ran after the copy — closed; every walk on a probe copy now) · **F-322** (the pusher's "fewer rows = filter" rule skipped a legitimate merge — open) · **F-323** (the nightly's catch-up hung on a token read with no timeout; a hung instance blocked the next night — answered by the pull chain, code fix owed). Three gate catches of the assistant's own work (F-185 twice, the `.pyc` check) and one F-233 breach (`git status` on the mounted repo) — recorded, not minted.

## WHAT S226 DOES FIRST

Read Sunday's logs and the drift page (did Amir's purchase exports flow through within ten minutes?) → build the readiness header + logged result → then the server-side computation. Next free **D377 · F-324**.
