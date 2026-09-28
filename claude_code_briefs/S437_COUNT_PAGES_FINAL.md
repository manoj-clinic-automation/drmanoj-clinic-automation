# Claude Code brief — S437_COUNT_PAGES_FINAL (the three count pages finished: Amir's vouchers only, the RECEIVE round by rule, the whole-unit items, the blocks as tables, the renames gated on the proof)

Written 28-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S437 · fault F-659** (claimed on the System Board). Runs AFTER
S436 (live 13:30 IST). **Staff pages Hindi; owner page English. Sanjeevni-owned** (stock_amir.html + its routes, stockmatch.py/html,
stock_loss.html, loss_piles.py, qty_words.py, the round maker in stock_app.py, stock_statement.py where the block/outcome is read). No parent
file. Restart `clinic-finance` only. Count #1 is closed on every screen; Amir has keyed nothing yet.

## 1 · The owner's words (28-Sep 14:2x IST, on the live pages)
Amir's board: "I can see a lot of description with the product — big loss, short loss, written off. He doesn't require anything. He simply
requires the voucher details: the product name and the quantity he needs to post in that stock issue or receive voucher; other details are not
relevant, remove them. Instead of rounds, write Stock issue voucher number one, two, three." "There is a bug: CCM — it writes goli where the
packing is a bottle of about 20 tablets." "He should get the orthotic item-name corrections only after the stock corrections match with the
server; if he sees them before, he might do the corrections earlier and spoil our flow." Darpan's page: "The Badi kami section is a paragraph —
it should be a table: Marg quantity, physical count at the count, the difference, and the amount at selling rate, with a total below as well
as the total at the top; Chhoti kami the same, collapsible. The bottom lines after the orthotics line are of no use — remove; it should end
with 'Orthotics band ho gaya' with the loss amount." The owner's desk: "the losses section must be a table, not a running paragraph."
And from the chat's own read (13:5x IST, F-659): the 30 lines where the shelf holds MORE than Marg are on no voucher round.

## 2 · What exists (read live)
Amir's board `stock_amir.html` (S436: four sections; rounds 1–4 with each line "item · Marg से → तक · <why text> · ± qty"); the round maker
(S418/S427/S436 `_voucher_make`, rounds of ≤ `stock.voucher_batch` lines, ISSUE and RECEIVE batches, `stock_writeoff_run.round_no`); the
S404 `api/pad/hub` `vouchers.pending` = 30 (the over-on-shelf lines, words "" / "parked", and the Marg-negative book corrections) —
`differences[]` on `api/pad/amir/1`; the proof (hub step 5, `proof_state`, S231/S404: the next closing export checked item by item; the
`marg_answer` path); `qty_words.py` v1.1 (strips+tabs by packing; no notion of a bottle-of-tablets item); the staff block (S427 `block`
JSON: three text lines + the S436 orthotic foot line) rendered as paragraphs on Darpan's page, the owner's desk ("The staff block — frozen"
+ "As Darpan sees it") and the record PDF; Darpan's page foot (S436): "Sab ho gaya — ab Amir ke vouchers", the answered pairs list,
"Kam kyun? 0 … Koi line baaki nahi", the verdict line "Orthotics: BAND ho gaya … · baaki: …" and four ✓/○ status lines; the S436 gating of
Naam badlo on "every earlier round entered".

## 3 · The build

### 3.1 The STOCK RECEIVE round by rule (F-659)
Every line where the shelf holds more than Marg after swaps — the over-on-shelf lines (INTACOXIA-60 +47 strips, PARI CR 12.5 +28 strips,
ZIBON EXTRA, ALCOXIB 120, ASTOFEN P, FEBUTAL, NEWTEL H, SHELCAL HD, XYCAL K2 …) and the Marg-negative book corrections (to bring Marg from
−N to the shelf) — gets a **STOCK RECEIVE** voucher line: Marg से → तक = the shelf figure. Made by rule at install for count #1 (one run,
kind `receive_close`, audited "rule F-659, 28-Sep"), and at every future close as part of the close. These lines are never a loss and never
leakage; the record and the statement read "Marg corrected — on STOCK RECEIVE voucher N". The hub's `pending` goes to 0 and says so.

### 3.2 Amir's board — vouchers only, numbered
- The voucher cards are named **"STOCK ISSUE — वाउचर 1"**, **"… 2"** … and **"STOCK RECEIVE — वाउचर 1"**, **"… 2"** …, numbered continuously
  across the whole count in the order Amir should key them (issue first, then receive; the internal round numbers stay in the data and in the
  owner's record, never on his page). The 6-line cap stays.
- A voucher line is **item (packing) · Marg से → तक · कितना** (patte + goli / nag / bottle …) and nothing else — no group, no reason, no
  "written off", no rule text, no English tail. The "Marg में डाल दिया" tap with Marg's voucher number stays; a keyed voucher collapses to
  one line with its Marg number.
- Section 2 (closing stock after the vouchers) and section 3 (corrections) stay as S436 built them, except: **(c) Naam badlo is shown only
  after the proof is green** — the next closing-stock export checked and "Marg = shelf" reached for this count (hub step 5 DONE). Until then
  the section shows one line "नाम बदलना — बाद में, जब Marg और shelf मिल जाएँ" and NO names. The owner's hub and record may show the rename
  list as today.

### 3.3 Whole-unit items (the CCM bug)
Setting `stock.whole_unit_items` — an owner list on the Loss desk's settings card: item → unit word (bottle / jar / pc / tube / vial / sachet).
Seed **CCM = bottle**. `qty_words` v1.2: for an item on the list every quantity is whole units in that word ("8 bottles" / "8 bottle"),
never strips/tabs, and the spine's smallest-unit figure is divided by the packing count only when the item is NOT on the list. The report
lists the candidates — items with `1*N` packing whose every sale in the spine since 01-04 is a whole multiple of N, or whose packing/name says
ML / GM / POW / SYP / SACH — for the owner to add with one tap each; the seed adds only CCM. Every page, PDF, voucher line and notice reads
through it (Amir's board included: a CCM voucher says "− 3 bottle").

### 3.4 Darpan's page — the block as tables, the foot cut
- **Badi kami** — a table: item · Marg (ginti ke din) · gina (physical) · kami · Rs (selling rate); a **total row** at the foot; the header keeps
  "Badi kami — Rs 29,314". Quantities through qty_words, Hindi words.
- **Chhoti kami, likh di gayi — Rs 31,762** — the same table, **collapsed** by default ("dikhao ▾"), total row at the foot.
- **Kul kami** stays the first line. Then ONE last line: **"Orthotics band ho gaya — kami Rs 5,420 (10 line, bina bill)"** — and the
  orthotic Badi-kami lines available as a collapsed table under it (item · Marg · gina · kami · Rs), orthotics never mixed into the medicine
  table.
- **Removed from the page**: "Sab ho gaya — ab Amir ke vouchers", the "Kam kyun? 0 / Koi line baaki nahi" empty card, the verdict tail
  "· baaki: Amir ke vouchers …; Marg ke agle …; Naam badalna …" and the four ✓/○ status lines. The answered **Adla-badli** pairs collapse to
  one line "Adla-badli 9 — ho gaya (dikhao ▾)". His working cards (Aaj ki ginti, Dobara ginna hai, Stock batao, Kuchh gadbad hai) stay
  above the block as today.
- The block's data becomes rows (a `block` JSON of tables: kul, badi[], chhoti[], ortho[], totals), frozen at the close as before; the
  record PDF renders the same tables.

### 3.5 The owner's desk — the block as tables
"The staff block — frozen" becomes the same tables in English (item · Marg · counted · short · Rs; Big losses open, Small losses collapsed,
Orthotics as its own small table) with total rows; the "As Darpan sees it" paragraph is replaced by one link "Darpan's page shows this in
Hindi". The record PDF's block section follows (tables). Nothing else on the desk moves.

## 4 · Pins — read live after S436: stock_amir.html d32f39fa, stockmatch.py f09d9516 / .html bdfb25e3, stock_loss.html (S432's TO 5ead2a32
unless S436 moved it — read live), loss_piles.py 47d6acb3 (v2.4: block rows + the receive close), qty_words.py f4c15d7e (v1.2), stock_app.py
ec9abc48 (round maker: the RECEIVE round, voucher numbering, the pending count), stock_statement.py 24a040b1 (the "on STOCK RECEIVE voucher"
outcome), stock_hub.html 7b2ea506 (pending → 0 wording). Spine read-only. No parent file. Restart `clinic-finance` only.

## 5 · Walk (scratch copy of the live database; rows keyed W437*)
The RECEIVE round: after the rule, `pending` = 0 on the hub JSON; every over/negative line has exactly one RECEIVE line with Marg से → तक =
the shelf; none is in leakage or in any loss group; the record and the statement say so · Amir's board: the cards named STOCK ISSUE वाउचर 1…N
then STOCK RECEIVE वाउचर 1…M continuously; a rendered voucher line contains the item, the से → तक figures and the ± quantity and NO other word
(a gate: none of "written off", "loss", "rule", "owner", "closed", "group" in any voucher line); Naam badlo hidden while the proof is not
green, shown when a crafted proof is green · CCM on the whole-unit list renders "bottle" everywhere (desk, Darpan, Amir, statement, PDF);
an item off the list renders strips+tabs as before; the candidates list printed · Darpan's page: Badi kami as a table with a total row
equal to the header figure; Chhoti kami collapsed with its total; the last line is the orthotics line; the removed texts absent from the
rendered page; the pairs collapsed · the owner's desk block as tables, totals equal to the frozen run · S427/S428/S430/S431/S432/S436/S404
re-run green (assertions on the block's text form and the pending count adjusted, each named; dates from today) · negative control.

## 6 · Done means
Kit `deploy_kits\S437_COUNT_PAGES_FINAL\` · installed · published · `claude_code_briefs\REPORT_S437.md` — owner lines first: the RECEIVE
vouchers made (how many, the biggest lines), Amir's board in three lines, the CCM line as it now reads, the whole-unit candidates, Darpan's
block as he sees it; ending with `https://followup.dr-manoj.in/finance/stock/page/amir?count=1`, `https://followup.dr-manoj.in/finance/stockmatch`
and `https://followup.dr-manoj.in/finance/stock/page/loss?count=1`.
