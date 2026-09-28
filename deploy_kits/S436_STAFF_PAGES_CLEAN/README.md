# S436_STAFF_PAGES_CLEAN — Darpan's orthotic answers made one-option, the orthotic loss computed and the section closed by rule, the wrong-salt pairs, Amir's board reduced to his work (D638)

**Sanjeevni project · session 283 · 28-Sep-2026 · brief `claude_code_briefs/S436_STAFF_PAGES_CLEAN.md` · runs after S432.** Count #1's medicines
were closed 27-Sep (S427); its orthotic section was open — this kit closes it by rule. Staff pages Hindi, the owner's English. No parent file.

## What the owner said (28-Sep 09:5x IST, on the live pages)
Salts: "PARI CR 12.5, LINVIZ and LACTOVAX have wrong salts in Marg, so the pairs can't be matched." Darpan's Stock milaan: "for the orthotics found less
than Marg he writes 'does not know' — it should be 'sold without bill'; 'went out never came back' and 'broken or damaged' are not part of this
flow — remove; only the left option stays; then we compute the orthotic loss for the deficient items." Amir's board: "he does the vouchers, uploads
the suitable report, gets confirmation, any remaining work and any corrections; renames only when our flow is ready. I need a proper clean build."

## What was built
**3.1 Darpan's Stock milaan** — `stockmatch.py` v1.1 / `stockmatch.html` (whole): `SHORT_REASONS` = one entry (`BILLING`, "Galti se bill nahi
bana"), `OVER_REASONS` = one (`BILLED_NOT_GIVEN`, "Bill bana, diya nahi"); the old keys stay in `REASON_HI/EN` for old rows and are refused by the
door (400). A line answered by rule with no word from Darpan is `defaulted` (cause_note "rule D638 default -- Darpan ne nahi likha"): shown with the
tag "default — aapne nahi likha", still tappable by him (200, recorded as his); a closed non-defaulted line stays 409 for him; the owner's one-tap
change still lands. `seed_s436.py` 3.1 converts every open orthotic line by rule (audit `stock_diff / cause_rule` by "rule D638, 28-Sep": Darpan's
name kept, the old answer named in the note). The renames are nowhere on his page.

**3.2 The section closes by rule** — `stockmatch.close_by_rule(con, d)`: when no orthotic line is open without a reason, every short line = the
orthotic loss at **selling price** (the statement's rule, `stock_statement.Prices` / `price_for`: spine S.RATE as on the count day, else MRP, else the
0.30 rule, else the rate — none → "no price"), every extra line a book correction. Writes: the lane word on each line (`WRITE_OFF` / `MARG_FIX`,
"rule D638 …", status closed), ONE `stock_writeoff_run` of kind `ortho_close` (groups `ortho_loss` / `ortho_fix`, one row per line, the price and
its source on each), the orthotic voucher round through S404's maker (≤ `stock.voucher_batch` lines a voucher, made WITHOUT a tap), one
`stock_section_close` row (basis rule D638), one Needs-you line (`stock_watch.notice` kind `ortho_closed`, once), an audit line. Idempotent. Fired
by `_after_write` the moment Darpan's progress reads all done, and by the seed. `section_state` then reads `closed` / `closed_by_rule` / `loss`; the
verdict "Orthotics section: CLOSED by rule on <date> -- N lines short, Rs X at selling price (M without a price); the round R on Amir's board · still to
follow: …" — Amir's vouchers, the proof and the renames are follow-ups under it, they no longer keep the section open. `loss_piles.py` v2.3: the two
ortho groups titled, `_kind_text` for the run, `ortho_loss_of()`, the staff block's FOURTH line "Orthotics — Rs X (N lines, bina bill) · M without a
price" (Hindi "bina daam") in `block_view` / `block_preview`; the leakage period line, the cadence rule and the union of clears ignore the run
(allowance + small + big only) — orthotics are never merged into the medicine figures. `stock_watch.py` v1.3: the `ortho_closed` kind on the Needs-you
list (the hook `sanjeevni_approvals.needs_you` already carries — that file is untouched); the duplicate " IST" on the stored watch's time removed.
`stock_statement.py` v1.2 (anchored): an orthotic line in the run reads "orthotic loss -- sold without bill" / "book correction -- billed, not handed
over" (+ "(Darpan by default)"), `became_key` = the group, not `open`; a Marg-negative line keeps S432's text. `stock_hub.html` (anchored): the orthotic
card's loss line; the defaulted lines listed.

**3.3 The wrong-salt pairs** — the seed answers ETOZOX 90 ↔ PARI CR 12.5, LACTOVAX SYP ↔ LINVIZ 600, LACTOVAX SYP ↔ FEBUTAL **No** with the note
"not a swap -- salt wrong in Marg (rule D638, 28-Sep)" through `stock_app.match_answer` (a new row each, the newest wins; the first was already No by the
owner at 09:37, the other two No since 18-Sep). `stock_app.py` (anchored): `_salts_less_fixes()` — the matcher's salt list minus every item with an OPEN
salt fix (`purchase_salt_task`, section change, source S436-owner…, not yet seen in Marg's list), so no pair is proposed on them until the fix lands.

**3.4 Amir's board** — `stock_amir.html` (whole, Hindi, four sections): **1 वाउचर — Marg में डालने हैं** (the rounds only, round 2 · round 1 · the
orthotic round; each voucher's lines inline; one tap "Marg में डाल दिया" with Marg's voucher number → the existing `/api/pad/vouchers/<cid>/entered`; a
finished round's card collapses); **2 वाउचर के बाद — Marg से closing stock निकालें** (the instruction; the proof's confirmation in Hindi, "अभी बाकी"
until the next export; the upload box kept as the fallback "रिपोर्ट यहाँ भी भेज सकते हैं"); **3 सुधार — Marg में ठीक करना है** (Salt theek karo — the
four seeded fixes with what Marg's list says today, each clears itself when the next salt export shows it; Rate daalo — the orthotic items without a
selling rate; Naam badlo — only when the orthotic round exists and every earlier round is entered, else "नाम बदलना — बाद में, जब वाउचर हो जाएँ");
**4 बाकी काम** (the S428 watch lines for him, else "आज कुछ नहीं"). Removed from the page: the waiting list, every Excel link, "What is behind them",
old section 1 (the S221 lookups), 3 (typed answers), 5 (families). Nothing is removed from `/api/pad/amir/<cid>`: `lookups`, `tranches`,
`ortho_families` still ride the JSON for the owner's reading; the JSON gains `salt_fix`, `rate_tasks`, `renames_ready`, `renames_wait_hi`, `rounds_order`,
`proof_hi`, `proof_state`, `ortho` (`_s436_board_extra`). `seed_s436.py` 3.4a: the four salt fixes into `purchase_salt_task` (section change, source
"S436-owner-28-Sep", b = Marg's salt today, audited `salt_fix_seed`): JARDIANCE 25 → EMPAGLIFLOZIN 25, PARI CR 12.5 → PAROXETINE CR 12.5, LACTOVAX SYP →
**LAXATIVE (LACTULOSE)** (Marg's own master gives FEBUXOSTAT 40 for it, which is wrong — the brief's fallback), LINVIZ 600 → LINEZOLID 600.

**Calls made where the brief left room** (each said in the report): the brief's "10 short lines Darpan answered 'does not know'" are 7 'does not
know' + 1 'broken or damaged' (DYNA WRIST BRACE REVER LONG) on the live rows — the owner's words cover both, all 8 convert, the 2 unanswered by
default; a Marg-negative extra line (CERVICAL COLLAR SOFT HOPE L) is a book correction in the run, its statement text stays S432's; the owner's desk
page `stock_loss.html` (not in the brief's pins) draws the block's first three lines only — the foot line shows on Darpan's page, in the record PDF
and in the JSON, the desk page is left for a later brief; `sanjeevni_approvals.py` untouched (the existing hook carries the line).

## Pins (FROM read live 28-Sep-2026 10:2x IST after S432 → TO; the whole files are the kit's, the three patched files are built by `make_s436.py`)
| file | FROM | TO |
|---|---|---|
| /root/finance/stockmatch.py (whole, v1.0 → v1.1) | df5501ea436d887dfe14ed618adce7ea | see SUMS.md5 |
| /root/finance/stockmatch.html (whole) | 4ddf0073099086f024c9e12412abf1ec | see SUMS.md5 |
| /root/finance/stock_amir.html (whole) | 3cf1f73ee707a2d3cff6781ba4c36012 | see SUMS.md5 |
| /root/finance/loss_piles.py (whole, v2.2 → v2.3) | 2501b55ad8334bf10c0c19a254d40a02 | see SUMS.md5 |
| /root/finance/stock_watch.py (whole, v1.2 → v1.3) | 5114e01f5dc70bd3f90dea3b040f8f02 | see SUMS.md5 |
| /root/finance/stock_app.py (anchored) | 02ad3d6ac3390dcf940d7a443557ac7c | see the installer's TO |
| /root/finance/stock_hub.html (anchored) | 38e0537cd7d1eb3fb40d1a5a0b7df0e5 | see the installer's TO |
| /root/finance/stock_statement.py (anchored, v1.1 → v1.2) | 05c63235a9f78c9f0f6969c683548880 | see the installer's TO |

Read only: `sanjeevni_approvals.py` 3999c4ce (the hook), `item_alias.py`, `section_map.py`, `qty_words.py`, `purchase_app.py`, the spine. Restarts
`clinic-finance` only. Data: the seed (3.1 causes, 3.3 notes, 3.4a tasks, 3.2 the run / round / notice / close row). No new settings.

## Proof
`walk_s436.py` — the REAL patched app over SCRATCH copies of the live database and the spine, the seed run on the copy first: one answer a side, the
removed words nowhere on the rendered page or in the state, the 8 + 2 + 2 conversions audited, the defaulted lines tappable (200) and a closed line
409, the owner's word 200, a removed key 400 · the section CLOSED by rule (one close row, `closed_by_rule`, the verdict), ONE `ortho_close` run with
10 `ortho_loss` rows at selling price (ANKLE BINDER BAMBOO L Rs 325, L S BELT XXX 2 × Rs 1,390; the two unpriced carry no rupee; Rs 5,420) and 2
`ortho_fix`, the lane words, all 12 closed, the orthotic round made without a tap (every line an orthotic, ≤ the batch), no orthotic line pending
while the medicines still wait, the hub CLOSED with the loss, the Needs-you line once, the statement's texts, the staff block's fourth line with the
first three unchanged, Darpan's block, the record PDF, the desk's 136 written-off lines unchanged, the period / cadence ignore the run, Make-again
idempotent · the pairs' notes; the matcher leaves out the four salt-fix items; a crafted same-salt pair W436 SALTA/SALTB proposed → not proposed with
a fix open → proposed again when Marg's list shows the new salt · Amir's JSON (the four fixes with Marg's salt today, the two rate tasks, the
rounds' order 2 · 1 · ortho, renames hidden with the wait line, "अभी बाकी"), the page (the four headings in order, "Marg में डाल दिया", the removed texts
absent, no .xlsx link, the upload fallback), every voucher entered → the rounds collapse, renames shown (23), the hub's vouchers green, no 'units' ·
the gates. **Negative control:** the same scenario on the box as it is goes red (four reasons a line, no `close_by_rule`, no loss, the old board).
Then **S430's, S427's, S428's** walks (S432's copies, unchanged), **S431's** (this kit's copy `walk_s431_s436.py`, ONE named data
adjustment: the statement's section line counts read Medicines 287 / Consumables 20, not 288 / 19 — BELL CAST 5 moved to Consumables by S432's
seed on the live database at 07:5x, after S432 had re-run this walk; nothing to do with S436), **S432's own** (this kit's copy `walk_s432_s436.py`,
ONE named data adjustment: its negative control asserted "the old box has no stock_pile_cache table" on a copy of the live database, which has
carried that table since S432's install — the control now asserts the old FILES lack the cache code and wrote no cache row) and **S404's** (this kit's copy, the S436 adjustments named: the
one-answer vocabulary in section 4 and the "answer everything" loop; section 10 — the section closes by rule as soon as Darpan has answered, no
owner's word awaited, a second round finds nothing, the verdict "CLOSED by rule") re-run on the patched files, each against its own pre-kit control.
One installer adjustment, named in the script: S430's pre-kit control (old430) now stands on the pre-S432 stock_app / statement / qty_words (the
`.bak_S432` files) under S430's own `.bak_S430` files — today's live stock_app (S432's) calls S432's loss_piles, so the control as S432 built it
raised on every step; S430's walk itself is unchanged. `figures_s436.py` prints the loss, the board and the salt tasks for the report.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S436_STAFF_PAGES_CLEAN/install_S436_STAFF_PAGES_CLEAN.sh
```
Undo: put back the eight `.bak_S436_<from8>` files, `systemctl restart clinic-finance`, healthz 200. The seed's rows (the causes by rule, the notes,
the salt tasks, the run, the round, the close row) are the owner's rulings as data; the `finance.db.bak_S436_<stamp>` is used only if he asks for
them to be reversed.
