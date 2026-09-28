# S437_COUNT_PAGES_FINAL — the three count pages finished: Amir's vouchers only, the STOCK RECEIVE round by rule, the whole-piece items, the blocks as tables, the renames gated on the proof (F-659)

**Sanjeevni project · session 283 · 28-Sep-2026 · brief `claude_code_briefs/S437_COUNT_PAGES_FINAL.md` · runs after S436 (live 13:30 IST).**
Count #1 is closed on every screen; Amir has keyed nothing yet. Staff pages Hindi, the owner's English. No parent file.

## What the owner said (28-Sep 14:2x IST, on the live pages)
Amir's board: "He simply requires the voucher details: the product name and the quantity he needs to post in that stock issue or receive
voucher; other details are not relevant, remove them. Instead of rounds, write Stock issue voucher number one, two, three." "CCM — it writes
goli where the packing is a bottle." "He should get the item-name corrections only after the stock corrections match with the server."
Darpan's page: "The Badi kami section is a paragraph — it should be a table … with a total below as well as the total at the top; Chhoti kami
the same, collapsible … it should end with 'Orthotics band ho gaya' with the loss amount." The desk: "the losses section must be a table."
The chat's own read (F-659): the 30 lines where the shelf holds more than Marg are on no voucher round.

## What was found live (probe on a scratch copy, 28-Sep 14:4x IST)
The 30 pending lines are **15 where the shelf held more than Marg** (ASTOFEN P +64, NEWTEL H 40 +60, FEBUTAL +28, XYCAL K2 +18, ZIBON EXTRA
+156 after its swap, the Marg-negative GLI-ME SR1 and TRAMEF P …) **and 15 short lines the owner wrote off on 06-Sep** (CEECIT MZ, JAKMAC 5,
SYSFOL 5, XGESIC LA …) before the piles existed — real losses already in the desk's "written off earlier" group, never put on a voucher. CCM:
Marg's packing 1*40 is the tablets in the bottle while Marg counts, sells and stocks it by the bottle (8 → 5, every sale a whole 1.0).

## What was built
**3.1 The STOCK RECEIVE round by rule** — `loss_piles.py` v2.4 `receive_close(con, root, who, d, all_pending)`: every pending line where
the shelf holds more than Marg after the swaps (the maker's RECEIVE lines: over-on-shelf and the Marg-negative book corrections) goes on
Amir's vouchers in ONE run of kind `receive_close`; a shelf-more line the maker does not carry (no word at all — ALCOXIB 120, CALBERT K27,
the cast pads … — or the owner's PARKED of 06-Sep, which makes no voucher — INTACOXIA-60 +47 strips, NEWTEL 40) first gets the rule's own word EXPLAINED ("the shelf held more than Marg --
Marg corrected up to the shelf, never a loss", audited on the run) and then rides the same round (group `receive`; mrp 0 — never a loss, never leakage: `count_periods` sums allowance +
small + big only, the union of clears and the block preview skip the kind, `NON_BLOCK_KINDS`). `_run` calls it after the count's own round on
every close (tap or auto). The seed ran it once for count #1 with `all_pending=True`: the same round also carries the 15 earlier write-offs as
STOCK ISSUE lines (group `issue_earlier`) — a call made where the brief left room (see the report): without them the count could never be
proven, and the owner had already written them off. The hub's pending reads 0 and the page says "Every line is on a voucher". The record's run
reads "Marg corrected -- the STOCK RECEIVE vouchers by rule (never a loss)"; `stock_statement.py` v1.3 reads "Marg corrected -- on STOCK
RECEIVE voucher N" on those lines (`stock_app._voucher_numbers`).

**3.2 Amir's board — vouchers only, numbered** — `stock_app._voucher_state` gains `vouchers_flat`: every STOCK ISSUE voucher of every round
numbered 1..N in the order made, then every STOCK RECEIVE voucher 1..M (`_s437_flat`); each line carries its words (`_s437_line_words`:
from / to / change, Hindi and English, through qty_words with the item's name). `stock_amir.html` (whole): section 1 is the vouchers only —
"STOCK ISSUE — वाउचर 1" …, "STOCK RECEIVE — वाउचर 1" …; a line is item (packing) · Marg से X → तक Y · ± कितना and nothing else (no reason, no
rate, no value, no round number); "Marg में डाल दिया" with Marg's number stays (the same `entered` door); a keyed voucher folds to one line with
its Marg number. Sections 2–4 as S436, except **(c) Naam badlo shows only when the proof is green** (`_proof_state` = done: Marg = shelf reached):
until then the one line "नाम बदलना — बाद में, जब Marg और shelf मिल जाएँ" and no names (the page draws rows only under `renames_ready`; the JSON
keeps the rows for the owner's hub and record).

**3.3 Whole-piece items (the CCM bug)** — `qty_words.py` v1.2: `set_whole_units([...])` / `whole_unit_of(name)`; an item on the map reads whole
units in its word (bottle / jar / pc / tube / vial / sachet; Hindi botal / jar / nag / tube / vial / pudiya), never strips / tabs, never divided
by the packing; `kind_of` answers the word. `loss_piles`: the setting `stock.whole_unit_items` (kind list, entries "ITEM = word", seeded
`["CCM = bottle"]`, audited), loaded into qty_words by `settings()` on every desk read and by `stock_app._pad_report_data` (`_whole_units_load`)
before any quantity is worded; `_qw()` names the item of the lane it is wording (`_QW_ITEM`, set by `_lane_of`); `whole_unit_candidates()` — the
items with a 1*N packing sold only in whole multiples of N since 01-04, or ML / GM / POW / SYP / SACH in the packing or the name — on the desk's
settings card with a word beside each, one tap adds (`{key, add, word}` through the existing setting door; a bad word is refused).

**3.4 Darpan's page — the block as tables, the foot cut** — `loss_piles.block_tables()` (in `block_view` and `block_preview`): kul; **badi** rows
(the frozen big lines, largest first: item · Marg on the count day · gina · kami · Rs at MRP; total row = the block's big figure); **chhoti** rows
(allowance + small of the frozen runs behind the block; total = the small figure); **ortho** rows (the ortho_close run's loss lines) apart, never
in the medicine tables; Marg / counted from the classified lines (the cache), else the count sheet. `stockmatch.html` (whole): his working cards
first, the answered pairs folded to "Adla-badli 9 — ho gaya (dikhao ▾)", the Kam kyun card only while a line is open, then THE BLOCK LAST:
kul · Badi kami (open, total row) · Chhoti kami (collapsed) · **"Orthotics band ho gaya — kami Rs 5,420 (10 line, bina bill)"** with the orthotic
rows collapsed under it — the page ends there. Gone: "Sab ho gaya — ab Amir ke vouchers", the empty Kam kyun card, the verdict tail, the four
✓/○ lines. The three text lines (+ the S436 foot line) stay in the JSON for the pages that still print them.

**3.5 The owner's desk** — `stock_loss.html` (anchored): "The staff block — frozen" as the same tables in English (Big losses open, Small
losses collapsed, Orthotics apart, total rows); "As Darpan sees it" → one link "Darpan's page shows this in Hindi"; the whole-piece card on
Settings. The record PDF's block section renders the tables. Nothing else on the desk moves.

**Calls made where the brief left room** (each in the report): the 15 earlier write-offs on the rule's round (above); the run's `issue_earlier`
group is titled so in the record; the setting's label reads "Whole-piece items" (the walks' word gate refuses "unit" on a screen); the
renames' rows stay in the JSON (only the page hides them); a whole-piece item's `why` text in an already-frozen run (CCM's "short 3 tabs" in
run 1's allowance group) is frozen data and stays — every live read now says bottles.

## Pins (FROM read live 28-Sep-2026 14:4x IST after S436 → TO; the whole files are the kit's, the four patched files are built by `make_s437.py`)
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_amir.html (whole) | d32f39fad196c84a2cdf1ef5ca2f2598 | see SUMS.md5 |
| /root/finance/stockmatch.html (whole) | bdfb25e38cbc5a4c71171962089e1ccd | see SUMS.md5 |
| /root/finance/loss_piles.py (whole, v2.3 → v2.4) | 47d6acb35a84f9eb81235cad0de2b915 | see SUMS.md5 |
| /root/finance/qty_words.py (whole, v1.1 → v1.2) | f4c15d7e88c84b14c7686d5b28148877 | see SUMS.md5 |
| /root/finance/stock_app.py (anchored) | ec9abc4801599d9acd1ab34f66a21a83 | see the installer's TO |
| /root/finance/stock_statement.py (anchored, v1.2 → v1.3) | 24a040b1b58a21f043ff92ffce1e2860 | see the installer's TO |
| /root/finance/stock_hub.html (anchored) | 7b2ea5065c1b1bf110a4301ccd0384a1 | see the installer's TO |
| /root/finance/stock_loss.html (anchored) | 5ead2a32949ec6e77e95b8645db350e2 | see the installer's TO |

Pinned, read, NOT changed: `stockmatch.py` f09d9516 (the block rides `loss_piles.block_view`; the page no longer prints the verdict tail).
Read only: `stock_watch.py`, `item_alias.py`, `section_map.py`, `padwriter.py`, the spine. Restarts `clinic-finance` only. Data: the seed (the
setting; the rule's run and round for count #1). One new setting (`stock.whole_unit_items`, the brief's 3.3).

## Proof
`walk_s437.py` — the REAL patched app over SCRATCH copies of the live database and the spine, the seed run on the copy first; every real line
by key from the maker's pending list before the seed: ONE `receive_close` run by "rule F-659, 28-Sep" (15 receive + 15 issue_earlier, mrp 0),
every shelf-more line one RECEIVE line with Marg से → तक = the shelf, ≤ 6 a voucher, none in a loss group / the leakage / the block, pending 0
on the hub JSON and "Every line is on a voucher" on its page, the record's run, the statement's "Marg corrected -- on STOCK RECEIVE voucher N",
the rule idempotent, a crafted shelf-more line W437 OVER TAB put on a RECEIVE line 5 → 9 by the rule again, the close hook wired · Amir's board:
STOCK ISSUE 1..N then STOCK RECEIVE 1..M continuous across the rounds, every voucher once, ≤ 6 lines; every rendered line item · से → तक · ±
कितना with NONE of "written off / loss / rule / owner / closed / group / swap"; the page draws no reason / rate / value / round; CCM "− 3 botal"
(8 → 5); Naam badlo hidden (proof wait) and shown (23) only after a crafted proof (every voucher keyed, Marg's export after the last one
moving every item by its voucher — state done) · qty_words v1.2 with CCM = bottle: the desk (3 bottles, Marg 8 bottles), the statement,
Darpan's table (3 botal), the record PDF; an item off the list unchanged; the setting seeded and audited; the candidates (the crafted
W437 WHOLE TAB in, W437 LOOSE TAB and CCM out, a guessed word each), one tap adds with its word, a bad word refused, remove · Darpan's block
tables (badi = the frozen big lines with totals = the block's figures, chhoti, kul, the orthotic rows apart, the orthotic line's wording), the
page source (tables, dikhao, the block last, no s.conds / verdict_hi / "Koi line baaki nahi" / "Sab ho gaya", the pairs folded) · the desk's
tables (English, totals = the frozen run, the link), the record PDF's TOTAL rows · the gates as before, the whole-piece door owner-only.
**Negative control:** the same scenario on the box as it is goes red (no receive round, pending stays 30, no numbered vouchers, CCM in tabs,
no tables). Then **S430's** and **S428's** walks (S432's copy), **S427's** (this kit's copy `walk_s427_s437.py`, ONE named adjustment: the
settings card's key set now carries `stock.whole_unit_items` — the brief's 3.3), **S431's and S432's** (S436's copies), **S436's** (this kit's copy
`walk_s436_s437.py`, two named adjustments: the voucher column's wording; Naam badlo hidden until the proof) and **S404's** (S436's copy) re-run
— S431's walk (S436's copy, unchanged) runs on the 13:09 backup of 28-Sep, the database as S436 last ran it green: on today's live copy the
orthotic section is closed by S436's own seed (applied after that re-run), so its S431 texts ("Darpan: …", the close's at / by) read the rule's
outcome instead; nothing to do with S437 —
on the patched files, each against its own pre-kit control (old436 rebuilt from the `.bak_S436` files). `figures_s437.py` prints the RECEIVE
round, Amir's board, the CCM line, the candidates and Darpan's block for the report.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S437_COUNT_PAGES_FINAL/install_S437_COUNT_PAGES_FINAL.sh
```
Undo: put back the eight `.bak_S437_<from8>` files, `systemctl restart clinic-finance`, healthz 200. The seed's rows (the setting, the rule's
run and round) are data an older loss_piles ignores; `finance.db.bak_S437_<stamp>` only if the owner asks for them to be reversed — say so first.
