# S430_DESK_FIRST_READ — what the owner found on the first live read of the S427/S428 desk (D637, F-650)

**Sanjeevni project · session 283 · 27-Sep-2026 · brief `claude_code_briefs/S430_DESK_FIRST_READ.md` · runs after S428.**

## What the owner said (27-Sep 11:2x IST, on the live desk)
"Econorm and Pari CR were domestic consumption, not billed — I used the write-off route because there was no other route."
"Vinbactum DS also has an issue — there were probably two products — and Vintaz P: they are mostly used for consumption, rarely
sold; a mix-up to be cleared one time, not counted in the losses." "Glocrepe I do not know when it was purchased; Cortiri has been
discontinued for long; Cuflin also — old products probably." "In the write-off section I cannot locate a single button to do the
entire write-off." F-650 (the chat's brief): the S428 leakage dated by count day, the watch list full of dead orthotics, the
count-#1 traces "unexplained", the three "units" hints.

## What was built
**2.1 Owner's use** (`loss_piles.py` v2.1). The → pile menu's fifth destination "Owner's use — taken for home, unbilled". The line
joins the fourth pile, renamed **Consumption & owner's use**, as its own group `owner_use` (moved line by line, never by rule);
the pile shows its two groups. Written off by the close like consumption, **vouchered in its own Marg round** (labelled "owner's
use" on Amir's board), recorded group by group, never in the staff block, never leakage. ECONORM CAP and PARI CR 25 are moved
there by the install (audited "owner (S430, said in chat 27-Sep)"); the owner may move them back.

**2.2 The list.** `stock.consume_items` gains VINBACTUM DS, VINTAZ P 4500 INJ and VINTAZ P 4500. The two VINTAZ spellings (both on
the count and in Marg's exports) are joined in the rename memory (`marg_item_rename`, planned + ticked + verified in one row —
both names are in the exports already, so it is a fact, not a rename to do), so every import keys them to one line. VINBACTUM DS
has one spelling everywhere (the count, the spine) — no alias was needed; said so. A list item keeps its tag "on your consumption
list" even when the owner moved it (VINTAZ P).

**2.3 Old stock.** A shortage on an item with **no sale and no purchase in the spine since the opening (01-04-2026)** AND (no price
on record, or `stock.old_stock_days` = 180 passed without either) is group `old` in the Write-off pile: "old stock — no sale and
no purchase since 01-04-2026, no price on record; written off, not a loss". GLOCREPE (2 pcs), CORTIRI (5 pcs) and CUFLIN D
(2 strips + 5 tabs) land here — each verified against the spine: no sale, no purchase, no desk price. Not leakage, not on the staff
block, vouchered.

**2.4 The one Close button.** `stock_loss.html` draws the same "Close the count (N lines)" button through one function at the top
(a card under the totals) and at the foot; one arm, one confirm, one countdown on both. Each of the three piles' headers carries
"Written off by *Close the count* — one tap for all three piles, at the top and the foot." Nothing else moves.

**2.5 F-650 — leakage dated by period** (`stock_watch.py` v1.1). `count_periods()`: every closed count with a frozen run is a
period from the previous closed count's day (by day; the opening before the first) to the count's day, with its write-off
(allowance + small + big at cost) and the period's sales. `month_leak()` shows the period as ONE line in the month the count closed
("01-Apr → 06-Sep: leakage ₹X = Y% of sales · budget 1%") and spreads it pro rata by each month's share of the period's sales only
for the red-period rule (`pct`, `red`); spot-count and Darpan's loss points stay dated by their day. `auto_adjust` already read
the period. No change to `sanjeevni_approvals.py` or the approvals HTML was needed: the S428 line shows `m.leak.text`.

**2.6 F-650 — the watch list.** Every item of the orthotic section (S404 map or the word rule) is out; a costly item with no sale
in 90 days stays only from `spot.dead_high_value_p` (₹2,000): Hylastos, Hyorth XL, Bonista PF, Ryblesus 3, Bonmax PTH pen,
Cetaphil stay; Bell Cast 5, the cast shoes, the belts and braces go. The list names what it left out (`watch_left_out`).

**2.7 F-650 — first-count traces.** A trace whose anchor is the count itself (no earlier settled point) and would end
"unexplained" ends **`first_count`** ("no earlier point — first count"): no Needs-you line, no per-item trace log line (one line
per read: "N lines with no earlier point (first count)"), the owner's card lists them as one line (`first_count_n`). Explained /
partly keep their meaning from any anchor; unexplained from the first spot point onward. The 28 live count-#1 rows are re-labelled
by the install and their Needs-you lines expired.

**2.8 The "units" hints.** `order_rules.py`: a guarded `qty_words` door and `_qw(units, snapshot_row)`; "keep-in-stock 12 strips
(your rule)", "max on shelf … — cut from …", and both "… on order #N … counted as stock" hints (the plan's and the interim's —
the brief named three, the same text stood in a fourth place) read in strips / pcs by the item's packing.

**Calls made where the brief left room:** the alias joined is VINTAZ P 4500 / VINTAZ P 4500 INJ (the data's two spellings), not
Vinbactum (one spelling); the "same bill twice" and the other trace checks are unchanged; the period line replaces the month's own
line only in the month a count closed — other months keep "Leakage ₹X = Y%" from their points plus the pro-rata share; the S427
and S428 walks are re-run from adjusted copies inside this kit (a published kit is frozen), each adjustment named in the copy's
header and in the report; S404/S403's walks were not re-run (no file they cover changed).

## Pins (FROM read on the box 27-Sep-2026 after S428 → TO; built by `make_s430.py` from the live bytes, anchored edits)
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_loss.html (S428's TO) | 29809ba1e3ce415fc43f5df614f7ea0e | ab60c341336c8c897699db18e830211d |
| /root/finance/stock_amir.html (S428's TO) | e5e229270de7a71a624505bfd0ca11b7 | 3cf1f73ee707a2d3cff6781ba4c36012 |
| /root/finance/order_rules.py (S414's TO) | b17226d4cc10d7cf9fef8a75465ac76b | 00a60efb515972313839662ff7f83495 |
| /root/finance/loss_piles.py (whole file, v2.0 → v2.1) | 9dc06c9000539b6fbf3f77ddac967c7d | 3720b2e1261fd83932b07e2a319a0687 |
| /root/finance/stock_watch.py (whole file, v1.0 → v1.1) | ec3999093387d979b754276b9911929d | 6a51e47b891b717fbb51b030d4a29f02 |

Not touched: `stock_app.py`, `stockmatch.py/html`, `sanjeevni_approvals.py`, `item_alias.py` (data only, through its table),
`finance_ui/finance_approvals.html`, `stock_hub.html`, `qty_words.py`. Restarts `clinic-finance` only. `finance.db` is backed up
first; `seed_s430.py` writes the owner's words as data after a green restart (idempotent, audited).

## Proof
`walk_s430.py` — the REAL patched app over SCRATCH copies of the live database and the spine, the kit's seed run first: the pile
renamed; ECONORM CAP and PARI CR 25 under owner's use with the audit; VINBACTUM DS and VINTAZ P on the list with the tag; the list's
three names; the VINTAZ alias verified and resolving; GLOCREPE, CORTIRI, CUFLIN D old stock with the why; crafted: an unpriced
never-sold never-bought item → old, the same with one purchase → not old (Big loss), a small line; the settings key; the page's
fifth destination, `closeBtn()` twice, the headers' line · the → pile menu: owner's use recorded and decides nothing, absent from
the block preview, a repeat says so, back to auto re-piles, a wrong destination refused · Close the count: one run with the six
groups, the owner's-use lines in their own round of exactly those lines on Amir's board (every line reads "Owner's use"), the
staff block = allowance + small + big only; leakage by PERIOD 01-Apr → 06-Sep at cost against the period's sales (owner's use and
old stock excluded), the Month section's September line reads the period, September alone never red, a spot point of today still
dates today, the approvals API carries the line · traces: the count's rows read first_count, none unexplained, one collapsed line,
their Needs-you lines gone, one log line not per item; a new trace with no earlier point → first_count; from a spot point → unexplained
as before · the watch list: no orthotic, no cast shoe, Bonista PF and Hylastos stay, what left is named, the setting on the card ·
`order_rules._qw` in strips / pcs and the four hints without "units" · the word gate · the gates. **Negative control:** the same
scenario on the box as it is goes red. Then **S427's walk** (three named adjustments) and **S428's walk** (one), **S414's** and
**S410's** walks re-run on the patched files. `figures_s430.py` prints the desk after S430 with the named items, the block, the
period line as it would read after the close, and the watch list with what left it.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S430_DESK_FIRST_READ/install_S430_DESK_FIRST_READ.sh
```
Undo: put back the five `.bak_S430_<from8>` files, `systemctl restart clinic-finance`, healthz 200. The seed's rows (the two moves,
the list's names, the alias row, the two settings, the 28 re-labelled traces) are data and stay unless the owner says otherwise.
