# S524_AMIR_ONE_JUDGMENT — one proof of Amir's vouchers, read from the spine (and the spine builds again)

Kit S524 · ruling **D706** · faults **F-843 F-844 F-845 F-846 F-847 F-848 F-840** and the spine gate of 08-Oct (its fault number is minted at the
chat's close) · brief `claude_code_briefs/S524_AMIR_ONE_JUDGMENT.md` (Sanjeevni chat, session 307, 11-Oct-2026). Built under
`claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md`. Kit 1 of three on Amir's page; Kit 2 rebuilds the rest of `amir_day.py` on this kit's bytes.

## What and why

**Part 0 — the spine had not built since 08-Oct 09:10.** Every ten-minute build failed its gate 11/13 on two purchase-line checks and kept the old
spine. Cause (F-800's shape): Marg's SUPPLIER/ITEM WISE purchase text prints only **8 characters of a long bill number, glued to the item name**.
The 08-Oct export (two saves, `009cb60e` and `5cdf845e`, 1st–8th Oct) carried five such rows the reader could not classify — one of KEDAR
PHARMACEUTICAL (`A000207_TYRO BR`, underscore-joined) and four of YUVIKA SURGICALS (`06202627L S BELT CONT GRAY UNISON X`, `06202627KNEE
IMMOBILISER UNISON M`, `06202627ANKLE BINDER BAMBOO M`, `06202627CAST SHOE M TYNOR`, digit-led) — so the whole export failed "every row
classified" and its totals, and was refused; and three glued GUNINA lines the reader did read (`L2678591`, `L3679039` ×2) are the LAST 8
characters of the bill-wise numbers `GPPL2678591` / `GPPPL3679039`, so the tie step found no bill for them. Two anchored edits:

- `spine/marg_read.py` (a): a glued row (`c[0]` empty, bill and item in `c[1]`, both money cells present) whose piece is a run of **6–8**
  letters/digits, then an optional `_` or space, then the item, is ITEM_GLUED with that run as the bill. The old `[A-Z]{1,3}-?\d{3,}` branch stays
  first. The run is bounded at 8 (Marg's clip) because S501's own example `06202627ANKLE BINDER BAMBOO M` would otherwise read as bill
  `06202627ANKLE`. `READER_VERSION` S331.1 → S524.1 (a reading records which reader made it).
- `spine/spine_build.py` (b): `tie_piece()` — **only when the plain match finds no bill** (never on `len(cands) > 1`: S484's shared-number cutting
  stays as it is) the ONE bill of that supplier inside the export's period (SUPPLIER grouping) or of the line's day (BILL grouping) whose number
  contains the piece (raw upper-case substring, piece ≥ 6) ties the line; otherwise untied as before. `BUILD_VERSION` S484.1 → S524.1.
- The two refused readings are **re-read** with the new reader from the collector's archive (`reread_s524.py`, spine_evidence's own machinery, the
  reading's original name and folder kept, the old reading kept beside as `<md5>.json.bak_S524_<8>`): 46 lines → 51 lines, every witness green.
  Readings are "written once" by rule; this is the one exception, for the two exports the gate named. The installer proves the repair in scratch
  first: the OLD builder on the OLD readings → 11/13 (the control); the NEW builder on the re-read readings → 13/13; each repair alone → 12/13.
  Then, on the box, OFF touched, the two files and the two readings placed, the live build run exactly as the cron runs it under the cron's own
  lock → swapped; `spine_compare.py` run; OFF removed. A later red walk leaves the live `spine.db` as the NEW build (the installer restores files,
  not the spine).

**2.1 ONE proof, read from the spine — `_s446_proof` rebuilt in place** (name, signature and return keys kept). The spine is opened through
`stock_watch.Spine()` (path `SPINE_DB`). An item's key is the spine's own (`sp_item.k20` for the name, else `sp.key`); items sharing a key (the belt
sizes, the knee supports, the wrist splints) are judged as ONE key on their net (F-843). Closings come from `sp_close` joined to `sp_export` for the
capture stamp; a closing is **clean** by `push_expected._gap_side`'s capture-hour rule — captured on a later day than it is printed for, or on its own
day at/after 22:00 (`end_day` = the printed day), or on its own day before 09:00 (it stands for the end of the day before); a same-day capture inside
shop hours is skipped. (The brief's parenthetical "end_day = as_on − 1" is the same-day-before-09:00 case; a closing printed for yesterday and
captured this morning stands for the whole of yesterday — the spine's own `sp_check` proves it, equal at every such closing.) R = the newest clean
closing captured before the first entry; `after` = the clean closings captured after the last; the tries are the first and the newest of them that
the spine's **reach** covers (`last_sale`, `last_pur` from `sp_export` as spine_build.py 377–378 reads them, and both newest exports captured after the
closing). Per key at a try: `marg_move = close(X) − close(R)`; `spine_move` = Σ `sp_move.units` for `end_day(R) < date ≤ end_day(X)` over SALE,
SALE_RETURN, PURCHASE, PURCHASE_RETURN, RECONCILIATION; `need` = Σ change of EVERY entered batch of the root with `R.stamp < at ≤ X.stamp`;
proven iff `|marg_move − spine_move − need| < 0.5`, or a late-keyed purchase of the key (dated in the 21 days up to R's day, one or two moves)
accounts for the rest (`late_purchase`). Absent at X → no verdict; absent at R while every `sp_item` row of the key is first seen after R → 0. A key in
the gate's `mixed` list → `unseen` with `why="mixed"`. Verdicts: proven at any try; wrong when False at every try that gave one; else no verdict.
`rows` carries the **ok=False rows only**; no-verdict rows go in `unseen` (printed by nothing). Row shape: item, key, family, need, need_key, moved,
marg, keys, ok, closing_day (dd-mm-yyyy), late_purchase, packing, pack, and the words `marg_hi` / `moved_hi` / `need_hi` through `qty_words`;
**`should` is always None** — nothing hands Amir a figure to type. Cache: the per-key table per (root, every entered (key, at), first_at, last_at,
`built`, `SPINE_DB`), 5 minutes; each call filters it for its keys. `_s488_why(con, sp, closings, R, after, last_at)` gives the reason only
(no_before · no_figure · pur_behind · no_closing; `rebased` never); the `stock_feed` look is for the reason, never the verdict.

**2.2 Stage A re-derived from its inputs** — `amir_stage(con, cid=None, d=None)`: `A["pending"]` = the report's pending orthotic lines
(`_voucher_pending(…, section="Orthotics")`, the report from `_report_cached` — `_pad_report_data` kept per root while its inputs stand
(MAX(id) of `stock_shelf_fix`, MAX(round_no) of the root's lines, MAX(received_at) of `stock_feed`) and 600 s at most; never handed to a route).
A is open while a voucher is open, `pending > 0`, or the proof over the orthotic batches is not done; the stored `A verified` event is a record.
When A is open again after its event, one `(A, recheck, ref)` event per distinct ref (the open keys · `pending:<n>` · the closing). While A is
open `visible` = every orthotic batch (so an orthotic batch made after the event shows — F-844's second half). Renames once released stay
(R2-2): with an `A verified` event, `renames_visible` is stage B's reading. Words for "proven, a line pending" (R2-1): the board's line
*Orthotic: sab sahi ✓*; the card *Orthotic ke 7 voucher Marg mein sahi ✓ — Ek orthotic line ka naya voucher Doctor sahab banayenge — aapko abhi kuch
nahi karna*; the owner *Stage A: all 7 orthotic vouchers proven on <day> -- 1 orthotic line(s) not yet on a voucher (make the round on the hub)*.

**2.3 The old proof retired** — `_proof_state`, `_proof_pur_to`, `_proof_basis` deleted (`_proof_day_key` kept, three callers); hub step 7 reads
`_s524_hub_proof` (state done/now/wait, English text, the ok=False rows with a why, `moved_without=0`, plus stage/A/B/C); `_s436_board_extra`'s two
blocks go (one `amir_stage` call for the renames gate; the proof line is `_s521_stage_proof`'s); `stockmatch.section_state`'s c3 is the stage proof
(F-840; the pending line stays c2's) — the orthotic section page and the statement (`stock_statement` reads `section_state`) say the same as the card.
**2.4 The door** — `api_pad_vouchers_entered`: a login that is not the checker may enter or clear only a batch in `amir_stage(...)["visible"]`,
else 403 `not_released` (F-845; fail closed). **2.5 DUTY_MAP v9 → v10** — `amir.count_vouchers.due_sql` counts the orthotic batches and the
batches of a released stage-C lot only; a released lot's `since` is its release (F-846). **2.6** `marg_take._rename_verify` skips a SHORT
closing (`reports_watch.closing_short`) before `verify_closing` (F-847). **2.7** amir_day's wrong-row sentence is the row's own words — *<closing_day>
ki closing tak Marg <moved_hi> badla — voucher <need_hi> ka tha · voucher N jaanch kijiye*, with *(ek hi naam ke N size ek saath gine gaye)* for a
family; never a figure to type. **2.8** `shelf_figure.filed_vouchers` judges a batch by its moment: it counts in (d_from, d_to] when
`capture(d_from) < at ≤ capture(d_to)` (the day's closing-stock push in `stock_feed`); with a capture missing, S488's day rule (F-848).

## Pins (server) — FROM → TO

| file | FROM | TO |
|---|---|---|
| `/root/finance/spine/marg_read.py` (+5) | 96f565a8d138d9ce75c0ed228b471495 | b47a1d626c36e2706879c41e2c316a69 |
| `/root/finance/spine/spine_build.py` (+23) | 11f8acb05c46aeaa72e1771d5c89922c | 5d8b1f94d80189c16b2ee5b1e093429c |
| `/root/finance/stock_app.py` (+299) | c0f0623f7d540bbdedb4369aa459405a (S521's TO) | b7e9880af7b81d38e7760b98d0a262b5 |
| `/root/finance/stockmatch.py` (+7) | fc1caf4496c4fd072e909b4d3e6784aa | 4a2f9fcdfe969a0ca577c34536dbf9a2 |
| `/root/finance/shelf_figure.py` (+38) | a1e87d1ff758e8f9a8206205a457b875 | 9be5eb88d1b1fc1fdb03b906c88a4265 |
| `/root/finance/amir_day.py` (+10; three places) | f1ce78e8bd788fbbb8c9774c04119af9 | 7f9803d813b59df287e9175de06f6d36 |
| `/root/marg_ingest/marg_take.py` (+5) | a86a0f26d4fc86a51e963b6a1b561323 | 5cad2d24d63344146f562fd5d441dbdf |
| `claude_code_briefs/DUTY_MAP.json` (v9 → v10) | 2016244829b4c70c00f1c59b0250ee35 | 7aa2f935677928e470454c355553210b |
| `claude_code_briefs/DUTY_MAP.md` (+2) | 7400e9ff2b047df82c81e897a06ea5ac | 4888a228282d37133bb888e474d2d63c |
| readings `5cdf845e…json`, `009cb60e…json` | the S331.1 readings (46 lines, refused) | re-read by S524.1 (51 lines, ok) — old ones kept beside as `.bak_S524_<8>` |

Must not move (read-only): `spine_read.py 712a1e4e`, `spine_evidence.py 0fcf6c64`, `spine_rules.json dd6c7616`, `stock_amir.html 2e41e406`,
`stock_hub.html`, `reports_watch.py`, `item_alias.py`, `qty_words.py`, `loss_piles.py`, `stock_watch.py`, `finance_app.py`, `portal.py`,
`tile_grants.json`, the crontab, `/root/finance/_off/ALL_OFF`. Services: `clinic-finance` restarted once; `marg_take.py` placed by rename (the
collector job); `shelf_figure.py` takes effect at `order_rules`' next pass; the spine files at its next build (the installer runs one). Backups:
`<file>.bak_S524_<from8>` beside each of the seven, `finance.db.bak_S524_<stamp>` by the backup API, the two readings beside themselves.
**No database write by the kit**; the installer's read-back may write the once-only `(A, recheck, 'pending:1')` stage event (printed before/after).

## The walk (`walk_s524.py`) — scratch copies of finance.db and the NEW spine by the backup API, every control red on the OLD files

0. Part 0's scratch builds: control 11/13 on the two purchase-line checks; 13/13 after; each repair alone 12/13; every purchase line dated to 30-Sep
   byte-identical to the live spine (S484's 01-Sep lines among them); the four bills Marg printed in part carry their lines (1 + 2 + 1 + 4);
   `selftest_spine.py` green on the new reader and builder; the greps for `_proof_state(` and `def _proof_state` empty.
1. Regression: count #1's seven orthotic batches on the rebuilt spine — the per-key table printed; the proof judges when a clean after-closing is in
   reach. 2. F-843: one SALE of the LS BELT key moves Marg and the spine alike → the key's verdict unchanged; **C** the old proof names size L wrong
   with a `should`; inverse (+1 at both tries) → the key wrong, no `should`, closing day and words present. 3. F-844: stage A, `pending` 1,
   `visible` = every orthotic batch, `renames_visible` True, one `(A, recheck, 'pending:1')` event on the first read and none after; a new orthotic
   batch listed with its own recheck event; the pending line cleared by a correcting shelf figure → `pending` 0; **C** old: stage B, the batch hidden,
   no event, the card's old words. 4. F-845 through the route, a walk-only portal session as amir: a medicine batch → 403 `not_released`, the
   released orthotic batch → 200, clear → 200; the owner → 200; **C** old 200 for amir. 5. F-846: v10 on the copy, +1 orthotic batch, +a release
   of 12 keys with `since` = the release; **C** v9 counts more. 6. F-847: a 250-name closing built at walk time from the copy's own names → skipped,
   `seen_n` unchanged; the whole one counted; **C** old counts the short one; proof side: an absent key → `unseen`, never wrong. 7. F-848: a batch
   filed at D+1 09:50 after D+1's 09:30 capture → (D+1, D+2], not (D, D+1]; a missing capture → the day rule; **C** old (D, D+1]. 8. F-840: c3 follows
   the stage proof, the inverse case names the key count, no batches → "nothing to prove yet"; **C** old judges by the feeds. 10. Staff-eye: the duty
   due on the copy, Amir's home tile, step 6's "Marg sudhar" and "Orthotic voucher baaki: 1", his board lists exactly `visible`; the hub's step 7 and
   the orthotic section render; no page reads "hona chahiye". 11. Timing reported. 12. The installer's read-back prints the stage events before/after.

## Charter (S303)

**Retired:** `_proof_state`, `_proof_pur_to`, `_proof_basis` (the whole-count proof on the stock_feed figures — a second source of the judgment),
the two `_proof_state` blocks of `_s436_board_extra`, `stockmatch`'s c3 on the old proof, `_s444_renames`' report read for `d is not None`, the
`should` figure on a wrong row, the `rebased` reason. **Left for later / seen, not touched:** (B21) the release-on-any-read — `amir_stage` writes
its once-only events on whichever read comes first, and this kit WIDENS the set of releasing reads (the hub's step 7, the orthotic section, the
statement, the door POST); (B22) the two roots (`_s446_root` = the newest count with voucher lines, `_newest_root` = the pages' count); (B3) the
board's payload; the shelf gap's windows by `as_on` DAY while the proof gives a clean closing an `end_day` — two definitions of "the closing of day D",
for rung 4b; the renames fold into the spine only at its next build (R1-B18); `push_expected.py` on manojz stays (the shelf page and Shavez's tile
read its pushes; its retirement is rung 4b's later kit); `amir_day`'s `_s446_voucher_line` ("Count vouchers waiting (Stage A, orthotic)") still
counts `A.open` (correct by the new stage) and `amir_vouchers_open` still counts every un-entered batch for its own card line. **Seen in the data
(the walk's regression, for the chat):** (i) the key TYNOR WRIST SPLINT R (sizes RT L, RT M) moved +1 in Marg by the 05-10 and 07-10 closings
against +2 on voucher 4 (3|RECEIVE|2); the second unit reached Marg on 08-10 (closing 4, then 3 after the 09-10 sale) -- the 08-10 and 09-10
closings are not yet in the spine's reach (the purchase export of 08-10 09:03 was taken before them), so the card names voucher 4 until Amir's next
purchase export, when the proof turns green by itself; S520's per-item feed proof had read it green on 08-10. (ii) The brief's late-purchase rule
(one or two purchases of the key dated in the 21 days up to R's day) can explain away a residue of that size whenever such a purchase exists --
LS BELT at the 05-10 try (+1 against YUVIKA's 1 of 28-Sep) and ANKLE BINDER BAMBOO likewise; a purchase dated INSIDE the window but keyed after the
try's capture (LS BELT's +1 of 07-10, keyed before the 08-10 22:30 push) reads as -u at that try and is covered by the other try. (iii) LS BELT
XXL rose 2 -> 3 in Marg on 08-10 with no document in the spine (sp_check 10-08: Marg 8, spine 9 -> -1 after the voucher's -2) -- the shelf gap's
business, not this kit's. **Calls made without
asking:** the 6–8 bound on the glued piece; `end_day` by `_gap_side` with the printed day as the day of a closing printed for an earlier day;
the stage stays A only when an orthotic batch exists (`bool(ortho)`), as today; `_s444_renames` reads `renames_visible` too (the board's rule);
the hub's English text for stages B/C/done written here; `READER_VERSION` / `BUILD_VERSION` bumped so a reading and a spine carry their maker.

Undo: put back the seven `.bak_S524_<from8>` files, restart `clinic-finance`, healthz 200, read the md5s back; the spine stays (the next cron build
with the old builder fails its gate and keeps it); the two readings' `.bak_S524_<8>` copies are put back only if the chat says so. The database
backup is not needed (the kit wrote no business row).

The server line, after the publish:

```
cd /root/deploy/repo && git pull --ff-only && bash deploy_kits/S524_AMIR_ONE_JUDGMENT/install_S524_AMIR_ONE_JUDGMENT.sh
```
