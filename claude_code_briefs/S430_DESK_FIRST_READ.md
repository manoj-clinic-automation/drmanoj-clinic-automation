# Claude Code brief — S430_DESK_FIRST_READ (what the owner found on the first live read of the S427/S428 desk: Owner's use, Old stock, the list, the Close button; the S428 leakage dating, the watch list, the count-#1 traces, the three "units" hints)

Written 27-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S430 · decision D637 · fault F-650** (claimed on the System
Board; S429 is the parent's). Runs AFTER S428 (live 10:57 IST). **Sanjeevni-owned.** Read REPORT_S427 and REPORT_S428 for the pins; read every
file live. The owner has NOT closed count #1 — he waits for this kit; the first thing the report must say is that he may close.

## 1 · The owner's words (27-Sep 11:2x IST, on the live desk)
"Econorm and Pari CR were domestic consumption, not billed — I used the write-off route because there was no other route." "Vinbactum DS also
has an issue — there were probably two products — and Vintaz P: they are mostly used for consumption, rarely sold; a mix-up to be cleared one
time, not counted in the losses." "Glocrepe I do not know when it was purchased; Cortiri has been discontinued for long; Cuflin also — old
products probably." "In the write-off section I cannot locate a single button to do the entire write-off." And on F-650: "the defects are your
work" — the chat's brief, not the build; the fixes are below.

## 2 · The build (D637 + F-650)

### 2.1 A fifth destination: **Owner's use** (a recorded non-loss)
The **→ pile** menu on every line gains **"Owner's use — taken for home, unbilled"**. Such a line joins the Consumption pile as its own group
`owner_use` (the Consumption pile is renamed **"Consumption & owner's use"**; two groups inside it: *clinic consumption* (the list) and
*owner's use* (moved line by line, never by rule)). Written off by the close like consumption, vouchered on Amir's board in its own round
("Owner's use"), recorded group by group, **never counted as leakage** (3.2 of S428: leakage = allowance + small + big only — unchanged).
Seed: ECONORM CAP and PARI CR 25 are moved to owner's use by the install (audited "owner, 27-Sep, said in chat") — the owner may move them
back. The staff block does not name owner's-use lines.

### 2.2 The consumption list, and the Vinbactum mix-up
`stock.consume_items` gains **VINBACTUM DS** (every spelling on the count: the two names are one product — add the second name as an alias in
`item_alias` the D620 way, audited, so every import joins them) and **VINTAZ P 4500 INJ**. Rarely sold is still consumption when the owner
says so: a consumption-list item with sales is still consumption (no rule overrides his list). VINTAZ P (moved by him) stays; the tag now
reads "on your consumption list".

### 2.3 **Old stock** — a new write-off group, never a Big loss
A shortage on an item that has **no sale in the spine since the opening AND no purchase since the opening AND no price on record** (or
`stock.old_stock_days` = 180 without either) is group `old` in the Write-off pile: "Old stock — no sale and no purchase since 01-04-2026;
written off, not a loss". GLOCREPE, CORTIRI, CUFLIN D land here (verify each against the spine and say so in the report; a line that does
have a purchase or a sale stays where the rules put it and is named). Not leakage, not on the staff block, vouchered.

### 2.4 The one Close button — where he looks for it
The desk's **"Close the count (N lines)"** button is repeated **at the top of the page**, under the totals, and each of the three piles'
headers carries one line: "Written off by *Close the count* — one tap for all three piles, at the top and the foot." The arm/confirm and
the staff-block preview stay at the foot as built. Nothing else on the page moves.

### 2.5 F-650 — the S428 leakage line dated by period, not by count day
A closed count's write-off (allowance + small + big at cost) is leakage **of the period between the previous closed count (or the opening,
01-04-2026) and this count**, shown in the Month section as ONE line for that period — "01-Apr → 06-Sep: leakage ₹X = Y% of sales · budget
1%" — and spread pro rata by each month's sales into the monthly figures only for the cadence and the red-period rule (so count #1 ≈ 1.5%
at cost, green, not 9% on September). Spot-count and Darpan's loss points stay dated by their day. The Needs-you red-period rule reads the
pro-rata months. Re-state the walk's leakage cases on this basis.

### 2.6 F-650 — the close-watch list without dead orthotics
The watch list excludes every item of the orthotic section (S404 section map / lane `ortho` — they have their own cycle) and any "costly"
item with no sale in 90 days unless its MRP ≥ `spot.dead_high_value_p` (₹2,000 — Bonista PF, Bonmax pen stay; cast shoes and belts go).
The list's size stays `spot.watch_size`; the "costly" rule keeps high-value medicines that do sell. Say in the report which items left and
which stayed.

### 2.7 F-650 — traces on a count with no earlier point
When the anchor is the count itself (no earlier settled point), the trace's verdict is "no earlier point — first count" (not "unexplained"),
the card collapses to one line "N lines with no earlier point (first count)", and the trace log does not write one line per item. Unexplained
keeps its meaning from the first spot point onward. Existing 20 rows: re-labelled by the install.

### 2.8 The three "units" hints in `order_rules.py`
"keep-in-stock %d units (your rule)", "max on shelf %d units", "%d units on order #%d … counted as stock" → through `qty_words.py`
(strips / pcs by the item's packing). Anchored edit on the live bytes; the S410/S414 walks that still apply re-run green.

## 3 · Pins — read live after S428: loss_piles.py 9dc06c90, stock_loss.html 29809ba1, stock_app.py 0e0fc043, stock_watch.py ec399909,
stockmatch.py df5501ea / .html 4ddf0073 (block wording only if touched), stock_amir.html e5e22927 (the owner's-use round label),
sanjeevni_approvals.py 3999c4ce (the period line), item_alias (the Vinbactum alias), order_rules.py (S414's TO, read live). No parent file
(the approvals HTML line of S428 is reused as is; if the period line needs the HTML, declare it). Restart `clinic-finance` only.

## 4 · Walk (scratch; rows keyed W430*)
Owner's use: a line moved → Consumption pile, group owner_use, vouchered in its own round, absent from the staff block and from leakage;
back to the system's choice re-piles it · consumption list: VINBACTUM DS under both spellings joins one line; VINTAZ P on the list · old
stock: a crafted unpriced never-sold never-bought item → group old, never Big loss, not leakage; the same item with one purchase → not old ·
the top Close button arms and confirms exactly as the foot one; the three pile headers carry the line · leakage: a closed count of
₹44,000 at cost over 01-Apr→06-Sep against ₹29.6 L sales → the period line 1.5% green, September's month alone never red from it; a spot
point of today still dates today · watch list: no orthotic line, no cast shoe; Bonista PF stays · trace on count #1 → "first count", one
collapsed line, no per-item log rows; a trace from a spot point → unexplained as before · order hints in strips · S427 82/82 and S428 73/73
re-run green (adjusting only the assertions this brief changes, each named) · negative control.

## 5 · Done means
Kit `deploy_kits\S430_DESK_FIRST_READ\` · installed · published · `claude_code_briefs\REPORT_S430.md` — owner lines first: "You may close
the count now" (or why not), then where Econorm, Pari CR, Vinbactum DS, Vintaz P, Glocrepe, Cortiri and Cuflin D now sit and why, the
Close button at the top, the leakage period line as it will read after the close, the watch list as it stands; ending with
`https://followup.dr-manoj.in/finance/stock/page/loss?count=1`.
