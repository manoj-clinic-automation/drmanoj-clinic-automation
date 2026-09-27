# Claude Code brief — S427_LOSS_DESK_RULINGS (the Loss desk under the owner's rulings of 27-Sep: one nomenclature, piles by turnover, no recount pile, the staff block)

Written 27-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S427 · decision D632 · fault F-642** (claimed on the
System Board). Runs AFTER S418 (installed live 27-Sep 05:48 IST). **Owner-facing English; Darpan's page Hindi. Sanjeevni-owned**
(loss_piles.py, stock_loss.html, stock_app.py, stock_hub.html, stockmatch.py/html). No parent file. S428 runs after this one.

## 1 · The owner's words (27-Sep morning, on the live S418 desk)
"The recount pile says 50 or more units — we agreed ONE nomenclature, strips and tablets, everywhere; this keeps recurring." "Recount
should be Darpan's option, not pushed on him — the staff say the count was accurate." "The ₹1,000 rule puts slow items like VFER and
G Dress in write-off; big fast sellers land in Recount instead of the loss pile." "Leukocrepe, Leukoband, G Dress are sold on bills —
they are not clinic consumption." And on what staff should see: "It is a loss — carelessness or theft, why think of so many things.
Boldly: these are the major losses in this count, this much has been written off. No details of 1% or whatever. A block: total loss,
out of it this written off, and this is the worrisome one because it is large. That keeps the staff alert." Every threshold a setting.

## 2 · What exists (read live; S418's report is the map)
`/root/finance/loss_piles.py` 3b6554f8 — `classify()` / `_suggest()` / `_wo_group()` / `SETTINGS` / `totals_of()` / `apply_fixes()` /
the tables `stock_pile_move`, `stock_shelf_fix`, `stock_recount_ask`, `stock_pile_arm`, `stock_writeoff_run`; the desk routes in
`stock_app.py` cf464882 (`/api/loss/<cid>/piles`, `/pile/move|accept|writeoff|pursue|recount|setting`, `/record.pdf`);
`_allowance_units(sold, loose_sold, pack, unit_price_p, st)` at stock_app.py:3687 (quantity-scaled, `stock.allowance_scale`);
`_pack_units(pack)`; `stock_loss.html` 16cdddaa; `stock_hub.html` bb8741fa (status card); `stockmatch.py` d5f9392f / `stockmatch.html`
9a090e03 (Darpan's Stock milaan: *Phir se gino* blind boxes patte + goli, `recount_answer`; *Bina bill?*); the spine
`/root/finance/spine/spine.db` (`sp_item.packing / unit_kind`, `sp_sale_line`, `sp_purchase_line`, `sp_close`, `sp_move`, `sp_alias`).
F-642: the recount trigger and its settings card speak in "units"; consumption is classed by name-words; the allowance and recount
rules are by quantity, so fast sellers fell into Recount and slow items into Write off.

## 3 · The build (D632)

### 3.1 One nomenclature — a single quantity formatter, used by every pharmacy screen
NEW `/root/finance/qty_words.py`: `words(qty_units, packing, unit_kind, lang="en"|"hi")` → "3 strips + 4 tabs" / "12 pcs" / "2 bottles"
/ "3 patte + 4 goli" / "12 nag"; pack size from `sp_item.packing` (fallback `_pack_units`); a strip item with a partial strip shows both
parts, never a decimal; a non-strip item shows pcs / bottles / tubes / vials by `unit_kind` or the packing word. **The word "unit(s)" never
reaches a screen, a rule hint, a setting label, a notice, a PDF or a message.** Route every quantity the pharmacy pages show through it:
stock_loss.html (piles, totals, record), stock_hub.html, stockmatch.html (boxes and messages), stock_amir.html (vouchers), the record
PDF, the S417 orders pages and the S410 notices (they already show strips — confirm and re-point to the one function). Code identifiers
may keep `units`; user-facing strings may not. Append ONE rule line to `CLAUDE.md` under "The pharmacy": *Quantities on any screen,
notice, PDF or message: strips + tabs for strip items, pcs / bottles / tubes otherwise — never "units"; format through qty_words.py.*

### 3.2 Piles by turnover (replaces S418 §3 suggestions; S418's tables and routes stay)
Four piles, every open shortage line in exactly one, the sales-after-count test first (3.4):
1. **With me / back in store** — unchanged (Accept back).
2. **Write off** — three recorded groups, one tap: (a) *within the allowance* — gap ≤ **`stock.allowance_pct` % of the item's own sales
   quantity since the previous closed count** (first count: since the item's first sale, capped at 180 days), with a floor of
   `stock.allowance_min_strips` (1 strip, or 1 pc); (b) *small real gap* — beyond the allowance, under `stock.small_gap_ceiling_p` at MRP,
   and not a slow item (below); (c) *consumption* — items on the owner's list only (3.3).
3. **Big losses** — beyond the allowance AND any of: value ≥ `stock.big_loss_floor_p` at MRP (the old `pursue_floor_p`, relabelled);
   gap ≥ `stock.slow_months` months of the item's own sales and value ≥ `stock.slow_floor_p`; never sold in 180 days with stock on record
   and value ≥ `stock.slow_floor_p`. Tyro BR (68 strips against ~1% of its sales), VFER and G Dress (slow) land here; nothing here is
   "pursued" — it is a loss, recorded by name.
4. **Consumption** — its own pile, the owner's list; written off *as clinic consumption* by the same close.
Surpluses are never a loss: listed under a collapsed "Over on shelf" note (INTACOXIA-60 +719 is one), the shelf figure corrected to the
count by the close. **There is no Recount pile and no "Ask Darpan to recount" button.** Darpan keeps his own **"Dobara ginna hai"** on
Stock milaan for any item (search + patte/goli boxes; his figure, stamped, replaces the shelf and re-piles the line as S418 did). The
allowance dial goes; the percentage is the setting. `_allowance_units()` stays for its other callers; the desk uses a new
`allowance_for(item)` in loss_piles that reads the spine's sales since the previous count (fallback: stock_app's sold figures).

### 3.3 Consumption = the owner's list, never name-words
`stock.consume_items` — a list setting (normalised item names, matched exactly after normalisation; the alias table applies), seeded
**BLADE, ZIG ZAG (cotton), GLOVES (every size)**. Nothing else: Leukocrepe, Leukoband, G Dress and every bandage or dressing sold on
bills go to the stock piles. The owner adds or removes names on the settings card (a search box over sp_item); every change audited.

### 3.4 The sales-after-count test, automatic
A line where sales since the count day exceed counted + bought since (the spine's sp_sale_line and sp_purchase_line after `as_on`) is
closed by the system as "the stock existed — count was short" (EXPLAINED, cause FOUND, shelf = Marg, audited "system: sold after
count") before piling; it is listed in the record under its own heading. Gemcal XT, Dologesic SP and LS belt are today's cases.

### 3.5 One tap closes the count — and builds the staff block
"**Close the count**" (armed, 10-s confirm as S418): every line in piles 2, 3 and 4 → WRITE_OFF + closed, Amir's vouchers in rounds of
≤ `stock.voucher_batch` in the same call, one `stock_writeoff_run` with the four groups (allowance / small / consumption / big loss) item
by item, and the **staff block** frozen from it. The block, Hindi, pinned on Darpan's Stock milaan until the next count closes:
"**Ginti <date> · kul kami ₹X**" · "Chhoti kami, likh di gayi: ₹Y" · "**Badi kami — ₹Z:** TYRO BR 68 patte · XML 12 goli · …" (the
Big-losses pile by value, the top `stock.staff_block_items` named, then "aur N"). No reasons, no percentages, no questions; one optional
line under it, "Kuchh batana hai?" (free text, stored, shown on the owner's record card). The owner's desk shows the same block in
English as the record card; the hub status card and the PDF read the same run. With-me lines still open at the close stay open.

### 3.6 Settings card (S418's card, rewritten in strips words)
`stock.allowance_pct` 1.0 · `stock.allowance_min_strips` 1 · `stock.small_gap_ceiling_p` ₹1,000 · `stock.big_loss_floor_p` ₹1,000
(migrated from pursue_floor_p; S418 seeded it at 100000 paise — keep the value, relabel) · `stock.slow_months` 1 · `stock.slow_floor_p`
₹200 · `stock.consume_items` (list) · `stock.voucher_batch` 6 · `stock.accept_back_by` owner · `stock.staff_block_items` 20.
Removed from the card: allowance_scale, recount_trigger, consume_auto, rolling_section_items, rolling_day (rows may stay in the table;
S428 defines the counts). Every hint on the card is in strips / pcs words. A second heading "Counts & watch" is S428's.

## 4 · Pins — read live: loss_piles.py 3b6554f8, stock_app.py cf464882, stock_loss.html 16cdddaa, stock_hub.html bb8741fa,
stockmatch.py d5f9392f, stockmatch.html 9a090e03, stock_amir.html c2ea41b2 (quantity words only), CLAUDE.md (one rule line appended).
No parent file. Restart `clinic-finance` only.

## 5 · Walk (scratch copy; own count rows keyed W427*)
No "unit"/"units"/"yunit" in any user-facing string of the touched files (a grep gate over the rendered pages and the PDF) · qty_words:
30 tabs of a 10-strip item = "3 strips", 34 = "3 strips + 4 tabs", 12 of a pcs item = "12 pcs", Hindi forms · classify: a crafted fast
seller (gap 1.5% of its sales, ₹5,000) → Big losses; a slow item (gap = 2 months of sales, ₹300) → Big losses; a gap of 0.5% → within
allowance; ₹600 real gap on a normal seller → small; BLADE → consumption; LEUKOCREPE → never consumption; a surplus → the Over note ·
sales-after-count closes a crafted line and lists it · Close the count decides piles 2–4 only, makes vouchers, freezes one run with four
groups, builds the block; a repeat does nothing twice; the block renders on Stock milaan in Hindi with strips words · Darpan's own
recount re-piles a line; the S418 `/pile/recount` route answers 410 · the settings card shows the new keys and no removed key ·
bhati/darpan/shavez refused on the desk · S418 walk assertions that still apply hold · negative control on the old files.

## 6 · Done means
Kit `deploy_kits\S427_LOSS_DESK_RULINGS\` · installed · published · `claude_code_briefs\REPORT_S427.md` — owner lines first: the piles
with today's real figures under the new rules (lines and ₹ in each; where Tyro BR, VFER, G Dress, Leukocrepe now sit), the staff block
as Darpan will see it after the close (not yet closed — the owner closes); ending with
`https://followup.dr-manoj.in/finance/stock/page/loss?count=1` and `https://followup.dr-manoj.in/finance/stockmatch`.
