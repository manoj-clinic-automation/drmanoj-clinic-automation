# REPORT_S417 — day-one fixes: stock in the order's unit, the card shelf, the Yes Bank tile with a provisional NEFT, JIARDIANCE (S417_DAY_ONE_FIXES, F-636)

Installed on srv1746119 on 27-Sep-2026, 04:51–04:56 IST (installer's own clock). Kit `deploy_kits\S417_DAY_ONE_FIXES\`.

## For the owner
- **Orders pages:** stock now reads in the same unit as the order — `12 strips + 4` beside an order in strips, `3 pcs` for an orthotic,
  `3 bottles` / `5 units` for the rest (a pack size nobody knows shows the count with its word, never a bare number). This is on the
  doctor's Orders page, the staff "Order medicines" page, the Purchase orders screen and your Purchase orders section. The WhatsApp text
  is unchanged.
- **Packs page, cards:** all three card cells now fill. The 38 decrypted statements are read by their own statement date; July, August and
  September show HDFC (…6098), ICICI Amazon (…9012 / …9004, one card, re-issued Feb 2026) and ICICI Coral (…5007). Pack row 4 is ready
  for all three for August. All_Transactions.xlsx is no longer asked about; it's the pack row's attachment.
- **Yes Bank tile, August:** reads **₹1,75,897 incl. provisional**, with a line under it "**− ₹3,53,455 provisional NEFT (awaiting
  statement)** · August 2026 purchases · NEFT 24-Sep". Without it the balance would be ₹5,29,352. The line goes away by itself when
  the Yes Bank statement shows the debit, and it won't be subtracted twice.
- **JIARDIANCE:** there are **two** items, a 10 and a 25 (Marg spells both "JARDIANCE"). Nothing was renamed.

| item in Marg | strength | packing | stock | supplier | last purchase | last sale | note |
|---|---|---|---|---|---|---|---|
| JARDIANCE 10 | 10 (no unit printed) | 1*10 | 0 | L.K. Drug House | 01-Sep-2026, qty 3 | 04-Sep-2026 (6 sale lines, 4 in 90 days) | salt EMPAGLOFLIZON 10 |
| JARDIANCE 25 | 25 (no unit printed) | 1*10 | 0 | L.K. Drug House | 24-Jul-2026, qty 1 | never sold | your rule: **on demand**; salt on record is **ETOROCOXIB 90** (looks wrong) |

"GRDIANS 25 MG" is almost certainly JARDIANCE 25. If you want a rename, Amir does it in Marg (D620) and the rename memory follows.

https://followup.dr-manoj.in/finance/purchase/page/orders · https://followup.dr-manoj.in/finance/packs · https://followup.dr-manoj.in/finance/approvals

## For the chat

### Pins — FROM (read live 26-Sep 21:00 IST, each = the previous kit's TO) → TO (md5 read back after placing, 04:56 IST)
| file | FROM | TO |
|---|---|---|
| /root/finance/purchase_app.py | cdd4e9c069bc8ab78160349a11a4a4c7 | 9c40d13ed222addeadf97d3f352f359a |
| /root/finance/porders.py | c75fc91060d127fd05c56b6b81ad9b97 | 64465af0835bdc5583ae7468cacc8c16 |
| /root/finance/porders.html | 5913e99302930d9fae24c42ac630f010 | 124c4d41b9491203899f324b8a194763 |
| /root/finance/finance_ui/finance_approvals.html (parent, declared) | eba564a425c1fc844f1d8d975a1d5eca | 588975fcff2644db115b63058c4d62dc |
| /root/finance/sanjeevni_approvals.py | c5b93455a69083a6b8d634014898bd30 | 64548b9b36770992dd3da2081e52ffe1 |
| /root/finance/packs.py (parent, declared) | 359403f792eaafad37d4eeac3f762641 | 938aa68fbe064b5025768ecfbff89897 |
| /root/finance/stmt_shelf.py (parent, declared) | 94f456ce0a6f469ecd7d3f16ca1e874e | 95ba0a4fadd25d9f30a67e7f99eba9f1 |

All seven were built on the box from the live bytes by `make_s417.py` (anchored edits, every anchor exactly once) and match the kit's pins.
`packs.html`, `order_rules.py`, `amir_day.py`, `finance_app.py`, portal and cron were not touched.

### What changed
1. `purchase_app.stock_text()` (strips + loose from pack_size, where the packing decides if pack_size is 1; pcs for orthotics from the
   section map; bottles/tubes/units otherwise). **Every place that prints stock beside an order qty:** `/page/orders` "On hand" ·
   `/page/staff` "Stock now" · porders section 4, the day's proposals (`stock_text` added in `porders._day_s410` over `order_rules.day_state`)
   and the engine's full plan (`_staff_plan` → `_plan_meds`) · porders section 1, the orthotic shelf (`shelf_text`) · the owner's Purchase
   orders table, both the shortages and the full-list tables (`shelf_text`). Numbers in the API are unchanged; words are added next to them.
2. `packs.card_read()` covers HDFC's current layout, HDFC's older layout (no period printed, so it's the month up to the statement date),
   and ICICI's. A card's month = the month the statement is dated in. Slots learn tails newest-first (`place()` compares tail sets) and an
   owner-set tail wins. Original ↔ twin pairing is **by same file name in the same card folder** (the locked original can't be read), which
   gives `duplicate of decrypted`. A month whose original has no twin reads `decrypted copy not yet made`, month taken from the file name's
   date minus one day; this is used only for that notice and never to place a file. Card originals are no longer flagged `locked` for the
   Yes Bank unlock step. A cards-root `.xlsx` is `all_txn` (in fetch, in `_process_once` and filtered out of `unplaced()`). The electricity
   line now reads bank slots only.
3. `sanjeevni_approvals.provisional_nefts()` counts a `purchase_neft_event` as provisional when: kind provisional, source owner or
   confirmed_by set, no bank_line_id, no NEFT debit of the same amount (± `neft.stmt_tolerance_p`) in −3..+15 days, and dated after the
   loaded statement's end. It is subtracted from the headline as its own line. With no event the tile dict is identical, same keys and
   order. Read-only; no table. **Amir's board shows no bank balance** (checked in `amir_day.py`), so nothing was added there.
4. `name_search_s417.py`: read-only, pattern `(J|G)I?A?RDIAN` on the name's letters. Its output is above and in the install log.

### Seed (live database, after the backup; install log)
`card files re-read: 77 -> placed 76, read 38, refused 0, skipped 40, unplaced 5, unlocked 0` · decrypted 38/38 read with statement
date · locked originals 38 — duplicate of decrypted 38, no twin 0 · tails learned: HDFC …6098, Amazon …9012 / …9004, Coral …5007 · the
Jul/Aug/Sep card cells all read · all_txn rows 1 · unplaced now 5 (the five locked Yes Bank files, unchanged). Live tile read back at
04:57 IST: holds ₹1,75,897, `incl_provisional`, one line ₹3,53,455 (event 1, August, NEFT 24-Sep), `before_provisional` ₹5,29,352.

### The walk — `WALK_S417 GREEN -- 25/25` (install log; dry-run 24/25 earlier, the one red was my own fixture bug, fixed)
- (1) Unit words: 12 strips + 4 / 3 pcs / 5 units / 3 bottles / packing-decides / negative / whole strips / 0 units. On `/page/orders` and
  `/page/staff`, the crafted W417 items read 12 strips + 4, 3 bottles and 5 units, with order-qty cells identical to the old files. On the
  porders state, the plan, proposal and orthotic lines carry the words. No bare `on_hand` is left in the page templates, and the WhatsApp
  text is byte-identical.
- (2) Fixture Drive:
  - Decrypted statements in HDFC's two layouts plus ICICI Amazon (re-issued …1104 → …1112) and Coral, all read with statement date and
    period. Tails learned `1112,1104` / `6011` / `7001`.
  - July and August cells filled, and pack row 4 ready with "statement dated …".
  - Twins become `duplicate of decrypted` with the twin's month. The twinless September original (random-password AES) reads
    `decrypted copy not yet made` on the cell and the row.
  - Both Excel rows end up `all_txn` and not unplaced.
- (3) Tile:
  - No event: byte-identical to the old files.
  - A provisional event gives one line, the headline net of it and `incl. provisional`. The SMS-unconfirmed, rejected and bank-line
    events never show.
  - A confirming debit removes the line. A covering statement makes the headline equal the provisional headline, so the debit is
    counted once.
- (4) Name search: the crafted JIARDIANCE and GRDIANS names are found with their fields and the GUARDIAN decoy isn't. The exact-spelling
  control misses both, and the file was not written to.
- (5) Real shelf on a scratch copy: before, 0/38 dated; after the seed 38/38, with tails 1/2/1, August cells read, row 4 ready ×3, and
  38 duplicates = 38 name twins. Bank rows, bank slot tails and the four bank tables were unchanged.
- **Negative controls** (the unpatched files, same fixtures):
  - Pages print the bare 124/3/5, with no stock_text or shelf_text.
  - No tails are learned, the August Amazon/Coral cells stay empty, there are no duplicates, and both Excel rows are unplaced.
  - The tile does not move for a provisional NEFT.
- The two pages' changed script lines were also run in a browser engine with stub data. The tile HTML with no event is byte-identical
  to today's, and the provisional line and the pcs/strips cells render correctly.

### Earlier walks on the patched files
**S414 8/8, S412 17/17, S411 13/13, S410 32/32, S409 24/24, S408 26/27** (the single red is the S411-declared supersession, accepted by
name), S407 27/27, S406 27/27, S405 29/29, S404 65/65 (on the 14:04 backup, as S414 did), **S403 52/52, S400 63/63**, S402 16/16.

**New declared scratch pre-state:** the first install run (04:44) stopped at S403's walk with 7 reds, and nothing was placed. A diagnosis
showed the same 7 reds (S403) and 1 red (S400 — the "Needs you unchanged" check) on the **unpatched** files over today's data. With this
kit's files on `finance.db.bak_S414_20260926_174505` they were 52/52 and 63/63, and S402 was green either way. The cause is data made
after S414's 17:45 install:
- the owner approved the buying rules at 18:08 (S403 expects "not yet approved");
- he tapped NEFT for August at 19:49 (18 supplier messages queued, which gives a Needs-you line S400 asserts absent);
- an orthotic family's sizes moved.

S403's and S400's scratch copies are therefore copies of that 17:45 backup, the way S414 handled S404. No walk was edited. S403/S400 now
depend on that backup file staying on the box, and a later kit should revise them to plant their own rows. One earlier attempt was also
stopped by me before it placed anything, because it had been started attached to an ssh session that would time out. It was relaunched
detached.

### Backups, restart, health
- `finance.db.bak_S417_20260927_045153` (backup API, 25,686,016 bytes).
- `.bak_S417_<from8>` beside all seven files: purchase_app cdd4e9c0, porders.py c75fc910, porders.html 5913e993,
  finance_approvals.html eba564a4, sanjeevni_approvals c5b93455, packs 359403f7, stmt_shelf 94f456ce.
- `systemctl restart clinic-finance` only. It is active, local and public healthz answer 200, and /finance/approvals, /finance/packs
  and /finance/purchase/page/orders answer 302 (login gate, expected). The journal shows only the restart's two "Worker was sent
  SIGTERM" lines.
- Build lock held by S417 from 04:44 IST until this report, then removed.

### Not done / outside the brief (noticed)
- **JARDIANCE 25's salt on record is "ETOROCOXIB 90"** (`purchase_salt_marg`), which is probably a wrong salt link. I left it; it's for
  the owner or Amir to decide.
- The owner's approvals page still shows tablet counts where no order qty sits beside them: the rules block's candidate "Stock" column,
  the out-of-stock bar ("shelf N"), and the item-add autocomplete ("stock N"). These are not in this brief.
- The old `twin_missing` flag ("newest original has no decrypted twin") is S408's and was kept as-is, because S408's walk asserts it. The
  new month-specific notice sits beside it.
- `packs.html` was not touched, so the card cell shows the learned tails as "…9012 / 9004".
- No permission prompt was hit; nothing was installed on the box.

### After publish
PUBLISH_ALL at 04:58 IST gave commit `6a67a3d` (gate clean). The first version of the kit folder had already gone out in `c661376`, a
publish that swept the pending tree, much as in S414. On the box I ran `git pull` (HEAD 6a67a3d): `md5sum -c` on the repository kit gave
7/7 OK, `diff -r` of the repository kit against the kit that ran said **IDENTICAL**, and the repository installer answered ALREADY
INSTALLED. The build lock was removed, `/tmp/s417*` cleaned, and clinic-finance and clinic-portal are active.
