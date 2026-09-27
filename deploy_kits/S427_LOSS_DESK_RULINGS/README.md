# S427_LOSS_DESK_RULINGS — the Loss desk under the owner's rulings of 27-Sep (D632, F-642)

**Sanjeevni project · session 283 · 27-Sep-2026 · brief `claude_code_briefs/S427_LOSS_DESK_RULINGS.md` · runs after S418.**

## What the owner said (27-Sep morning, on the live S418 desk)
"The recount pile says 50 or more units — we agreed ONE nomenclature, strips and tablets, everywhere; this keeps
recurring." "Recount should be Darpan's option, not pushed on him." "The ₹1,000 rule puts slow items like VFER and
G Dress in write-off; big fast sellers land in Recount instead of the loss pile." "Leukocrepe, Leukoband, G Dress are
sold on bills — they are not clinic consumption." "It is a loss — carelessness or theft. Boldly: these are the major
losses in this count, this much has been written off. A block: total loss, out of it this written off, and this is the
worrisome one because it is large. That keeps the staff alert." Every threshold a setting.

## What was built
**One nomenclature — `qty_words.py` (new).** `words(qty, packing, unit_kind, lang, pack, name)` → "3 strips + 4 tabs" /
"4 tabs" / "12 pcs" / "2 bottles" / "1 tube" / "3 vials"; Hindi "3 patte + 4 goli" / "12 nag" / "2 botal". A strip item
never shows a decimal; a non-strip item is named by its packing word (ML → bottle, GM → tube, VAIL / INJ → vial).
`stock_app._qw(units, pack)` routes through it, so every older page that used `_qw` now speaks the same words.
Every quantity loss_piles, the record PDF, Stock milaan and the staff block print goes through `words()`. **The word
"unit(s)" reaches no screen, hint, setting label, notice, PDF or message** — the walk greps the rendered desk, hub,
Stock milaan, Amir's board, their JSON texts and the record PDF for `unit / units / yunit`. Five stock_app texts that
carried it (the Marg cleanup Excel headers, the loose-column basis, the try-to-match Excel header) were reworded; the
hub's swap texts likewise; Amir's board's JS helper `units()` was renamed `qw()` (its words were already strips / tabs /
pcs). Code identifiers keep `units`.

**Four piles by turnover — `loss_piles.py` v2.0** (whole file; S418's tables, taps and routes stay). Every open
shortage line in exactly one pile, the sales-after-count test first:
1. **With me / back in store** — unchanged (Accept back). These stay open when the count is closed.
2. **Write off** — (a) *within the allowance*: gap ≤ `stock.allowance_pct` % (1.0) of the item's OWN sales since the
   previous closed count (first count: since its first sale, at most 180 days before the count), floor
   `stock.allowance_min_strips` (1 strip, or 1 pc); (b) *small real gap*: beyond the allowance, under
   `stock.small_gap_ceiling_p` (₹1,000) at MRP and not a slow item.
3. **Big losses** — beyond the allowance AND any of: value ≥ `stock.big_loss_floor_p` (₹1,000, the old pursue floor
   relabelled, value inherited); gap ≥ `stock.slow_months` (1) months of the item's own sales and value ≥
   `stock.slow_floor_p` (₹200); never sold in 180 days with stock on record and value ≥ `stock.slow_floor_p`; no price on
   record (a write-off is never blind — the line is named). Nothing here is "pursued": it is a loss, recorded by name.
4. **Consumption** — `stock.consume_items` only (a list setting, matched by normalised name, the alias table applies;
   seeded BLADE, ZIG ZAG cotton, every glove item). Never a word in the name: Leukocrepe, Leukoband, G Dress go to the
   stock piles. The owner adds / removes names on the settings card (a search box over the spine's items), audited.

Surpluses are never a loss ("Over on shelf" note). **There is no Recount pile and no "Ask Darpan to recount" button**;
`/pile/recount` answers 410. **Darpan's own "Dobara ginna hai"** on Stock milaan: search any item of the round, type
patte + goli (nag for a non-strip item); his figure, stamped, is a shelf fix (source `recount`) and the owner's desk
re-piles the line by the same rules. The allowance dial and its `allowance_scale` reading are gone from the desk; the
percentage is the setting. `_allowance_units()` in stock_app stays for its other callers; the desk uses
`loss_piles.allowance_for()` on the spine's `sp_sale_line` (fallback: stock_app's FY sales figure when the spine is away).

**The sales-after-count test (automatic).** A line whose spine sales since the count day exceed counted + bought since
(`sp_sale_line` / `sp_purchase_line` after `as_on`) is closed by the system before piling: `EXPLAINED`, cause `FOUND`,
shelf = Marg, audited "system: sold after count", a row in `stock_sales_test`, listed in the record under its own
heading. Idempotent. It runs when the desk is read and before every tap.

**One tap closes the count — and builds the staff block.** "Close the count" (armed, 10-s confirm): every line in
piles 2, 3 and 4 → `WRITE_OFF` + closed, Amir's Marg vouchers for exactly those lines in the same call (rounds of ≤
`stock.voucher_batch`), ONE frozen `stock_writeoff_run` with the four groups (allowance / small / consume / big) item by
item, and **the staff block** frozen from it in `stock_staff_block`: total loss = allowance + small + big at MRP
(consumption is clinic use, not a loss — it is stored beside, never in the block's figures), the small part, the big
losses by value with the top `stock.staff_block_items` (20) named, then "aur N". Hindi on Darpan's Stock milaan, pinned
on top until the next count closes: "Ginti 06-09-2026 · kul kami ₹X" · "Chhoti kami, likh di gayi: ₹Y" · "Badi kami — ₹Z:
TYRO BR 23 patte · …". No reasons, no percentages, no questions; one line "Kuchh batana hai?" under it
(`stock_staff_note`, shown on the owner's record card). The owner's desk shows the same block in English (and a live
preview before the close); the hub's status card and the record PDF read the same run.

**Settings card** (rewritten in strips words; every change audited and printed in the record): `stock.allowance_pct`
1.0 · `stock.allowance_min_strips` 1 · `stock.small_gap_ceiling_p` ₹1,000 · `stock.big_loss_floor_p` ₹1,000 ·
`stock.slow_months` 1 · `stock.slow_floor_p` ₹200 · `stock.consume_items` (list) · `stock.voucher_batch` 6 ·
`stock.accept_back_by` owner · `stock.staff_block_items` 20. Off the card: allowance_scale, recount_trigger,
consume_auto, rolling_section_items, rolling_day, pursue_floor_p (their rows stay; S428 defines the counts).

**Calls made where the brief left room** (each reason in one line): consumption is not part of the block's "kul kami"
(the owner: it is clinic use, not a loss); an unpriced shortage beyond the allowance is a Big loss (never a blind
write-off, but the count must close — it is named); a line the owner moves into Write off is grouped allowance / small by
the rules, into Big losses "big", into Consumption "consume" (four groups everywhere, no "your choice" group); S418's
RECOVER and RECOUNT words no longer choose a pile (no Pursue, no Recount) — such lines pile by the rules and keep their
claim tag; the S418 `/pile/writeoff` (the write-off pile alone) and `/pile/pursue` doors stay callable (the page no
longer shows them); Darpan may recount any item of the round, including one already closed (his figure is recorded; a
closed line stays closed); the brief's CLAUDE.md line went under a new heading "The pharmacy" (the rulebook had none).

## Pins (FROM read on the box 27-Sep-2026 → TO; built by `make_s427.py` from the live bytes, anchored edits)
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_app.py (S418's TO) | cf464882e49865f38153e1df6218301d | 24c2b5fe7cacfe238751e487e52eb6d0 |
| /root/finance/stock_hub.html (S418's TO) | bb8741fa7671399f9c495c75946d7c11 | 74ea06997b900e9f55c47dca473a9232 |
| /root/finance/stockmatch.py (S418's TO) | d5f9392fea4247b37705e865e1c242cb | e85807dab1f8672d482272e0d355fe28 |
| /root/finance/stockmatch.html (S418's TO) | 9a090e03c954bfda5a787e8d834f275c | d6a7fb38a02e066f818222de14b2e2e2 |
| /root/finance/stock_amir.html (quantity words only: the JS helper's name) | c2ea41b2db7e2b337e0a97426aaed763 | 244ac6eeb0117b14f2c3c7fa1576f728 |
| /root/finance/loss_piles.py (whole file, v2.0, in the kit) | 3b6554f86507509e0b1893129e748274 | 9dc06c9000539b6fbf3f77ddac967c7d |
| /root/finance/stock_loss.html (whole page, in the kit) | 16cdddaa6363ccc8da0278fa5d4635a3 | fdd913e75677580a7897fe2631196c4c |
| /root/finance/qty_words.py (new) | — | 1e67a3e35ce815798ef6ebd606e5b972 |

Not touched: `porders.py/html`, `order_rules.py`, `purchase_app.py` (the S417 orders pages and S410 notices already
print strips / pcs / bottles through `purchase_app.stock_text`; confirmed by reading, not re-pointed — they are not in
the brief's pins), `pad_receipt.py` (used read-only), `claim_queue.py`, `finance_app.py`, `portal.py`, the cron, the
spine (read-only). Restarts `clinic-finance` only. `finance.db` is backed up first; the tables `stock_sales_test`,
`stock_staff_block`, `stock_staff_note` are additive; `seed_s427.py` writes the settings only where absent, after a
green restart. `CLAUDE.md` in the repository gains one rule line under "The pharmacy".

## Proof
`walk_s427.py` — the REAL patched app over SCRATCH copies of the live database AND the spine (crafted W427 sales), the
real round 1, lines found by key, crafted lines keyed W427*: the gates (bhati, darpan, shavez refused on every door) ·
the four new piles, every line in exactly one place, no orthotic · classify: a fast seller short 1.5% of its sales
(₹5,000) → Big losses; a slow item (4 months of its sales, ₹300) → Big losses; 0.5% → within the allowance; ₹600 on a
normal seller → small; a syrup "2 bottles" → small; no price → Big losses; parked → With me; BLADE and GLOVES →
Consumption; LEUKOCREPE / LEUKOBAND / G DRESS never consumption; TYRO BR and G DRESS 10 in Big losses, BIO D3 MAX within
the allowance; a surplus under the Over note · the why lines in strips words with the item's own sales · the
sales-after-count test closes a crafted line (and the real DOLOGESIC SP), listed under its own heading, written once ·
the totals' identities, the hub and the report equal to the desk · the → pile menu (recount is not a pile) · Accept
back (S418 assertions still hold) · settings: 1% → 2% moves the fast seller into the allowance, audited, decides
nothing; a bad value and a retired key refused; the owner's search box; add / remove on the consumption list re-piles
LEUKOCREPE 8 CM · `/pile/recount` 410; Stock milaan carries "Dobara ginna hai", not "Phir se gino"; Darpan's search,
his figure "9 patte + 5 goli" lands and re-piles the line into the allowance; a repeat writes nothing; others refused; a
non-strip item counted in pcs · Close the count: no arm / 11 s / changed lines refused; every line of the three piles →
WRITE_OFF + closed and nothing else; the voucher round of exactly those lines ≤ 6 a voucher on Amir's board; ONE frozen
run with the four groups and the S427 rules; the staff block frozen from it (total = small + big, by value, named); a
repeat does nothing twice; the block on Stock milaan in Hindi with patte words and no percentage; "Kuchh batana hai?"
stored and shown to the owner · the record PDF · the word gate (pages, JSON texts, PDF) · the older doors kept.
**Negative control:** the same scenario on the box as it is goes red (the old piles, the old page, recount still
pushed, no Dobara ginna hai, the old `_qw` words). Then **S404's walk** (on the 14:04 backup of 26-Sep) and **S403's
walk** (on the 17:45 backup) are re-run on the patched files. `figures_s427.py` prints the desk under the new rules,
the named items, the lines the test closed, and the staff block as Darpan will see it after the close.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S427_LOSS_DESK_RULINGS/install_S427_LOSS_DESK_RULINGS.sh
```
Undo: put back the seven `.bak_S427_<from8>` files, remove `/root/finance/qty_words.py`, `systemctl restart
clinic-finance`, healthz 200. The seeded settings and the new tables are data and stay (the S418 code reads none of the
new keys; `stock.pursue_floor_p` still holds ₹1,000 for it); a line the sales-after-count test closed stays closed — say
so if it must be reopened; the database backup is used only if the owner says so.
