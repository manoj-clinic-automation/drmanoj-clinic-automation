# Claude Code brief — S431_COUNT_STATEMENT (the count of 06-09-2026 as ONE statement, section by section; orthotics at selling price)

Written 27-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S431** (claimed on the System Board; no new D/F). Runs AFTER
S430 (live 12:3x IST). **Owner-facing English; Sanjeevni-owned** (stock_app.py, a new page, section_map.py read; the spine read-only). No
parent file. Restart `clinic-finance` only. Count #1 was CLOSED by the owner at ~12:5x IST today (136 lines written off, 6 back in store);
the orthotic section is still open (2 lines unanswered, 18 not on a voucher, 22 of 23 renames unverified).

## 1 · The owner's words (27-Sep 13:0x IST)
"Better it be section-wise. Now share the complete list of 6th Sept with Marg stock, physical stock and shortages, and the excess items removed
and matched; and the orthotics, not seen by me — are its losses also done? I need orthotic losses to show separately at selling price. Give me
a link for what's ready." Then: "All prices have been worked out, probably in the spine; and Darpan's sheet was well made also."

## 2 · What exists (read live)
The sealed count (`stock_count` #1, `stock_count_item` 373 rows, `stock_diff` — the S226 report page `/finance/stock/page/report?count=1`
with its 10 lanes and the stale "33 lines still need a word / decision desk" pointer; `api/pad/result/1.xlsx`, `api/pad/diffs/1.pdf`); the
confirmed swaps (S404/S228 pairs: 13 confirmed, 2 not, 17 of 18 answered — `stock_diff` swapped quantities); the S427 close's
`stock_writeoff_run` (groups allowance / small / old / consume / owner_use / big, item by item) and `stock_shelf_fix` (accept-backs, Darpan's
recounts, the sales test); the orthotic section (S404: `section_map.py` — `stock_item_section` Medicines / Orthotics / Consumables, the
owner-editable map; Darpan's reasons on `stockmatch`, the orthotic pairs, the 18-line round not yet made); **Darpan's sheet** (S227/D389:
`stock_loss_share` frozen JSON + `_loss_share_pdf`, `/finance/stock/api/loss/share/<id>.pdf`) — the layout the owner likes; **prices**: the
spine `sp_item_fact` (MRP, S.RATE, P.RATE from the salt list, dated), `stock_rate` (last purchase net), the S235 pricing rule
(`is_ortho_priced` → cost ÷ (1 − 0.30) margin), `sale_line_discount`. `qty_words.py` (S427).

## 3 · The build — `/finance/stock/page/statement?count=<id>` + `.pdf` + `.xlsx`, owner and doctor roles
### 3.1 One statement, three sections, one price rule
Sections from `stock_item_section` (the owner's map): **Medicines · Consumables · Orthotics**, in that order, each with its own totals; within
Medicines the lines in the order of the count sheet. Per line: item (Marg's name + packing) · **Marg stock** on 06-09 · **physical** (counted)
· **swap** (the confirmed pair partner and the quantity taken out; a not-confirmed pair shows nothing) · **shortage after swaps** · **excess after
swaps** · **value at selling price** (shortage and excess separately) · **what became of it** (medicines: the S427 group — allowance / small
real gap / old stock / consumption / owner's use / big loss / back in store / sold after the count; orthotics: Darpan's reason, open, voucher
status). Every quantity through `qty_words`. Lines with no difference after swaps are listed under a collapsed "Matched — N lines" per section,
never dropped (the owner asked for the complete list).
**Selling price, one rule for every section:** the spine's `S.RATE` fact as on the count day if present, else the spine's `MRP` fact as on the
count day, else the S235 rule for `is_ortho_priced` items (last purchase rate ÷ 0.70), else `stock_rate` × the section's margin setting, else
"no price — name it". The source of each price is a small tag (spine / rule / rate). State in the report how many lines end unpriced per
section — the owner says all prices are worked out, so the residue should be near zero; if it is not, name the items.
### 3.2 The orthotic section, separately, at selling price
Its own totals block at the top of the section: **short at selling price · excess at selling price · net · lines still open (Darpan) · lines
not yet on a voucher · renames unverified** — read live from the S404 section so it changes as Darpan and Amir work. The two open lines and
the 18 unvouchered lines are marked on their rows. Nothing here decides anything; the S404 buttons stay on the hub.
### 3.3 The layout — Darpan's sheet, made for the owner
The same frozen-sheet discipline as S227: the page renders live; **"Freeze this statement"** (owner, one tap) writes a `stock_statement` row
(frozen JSON + md5 + PDF + XLSX, dated, who) and the links on the hub point at the frozen copy with "as at <time>"; a later freeze is a new
row, earlier ones listed. The PDF in the sheet's style (portrait, one section per heading, totals first, then the lines; the collapsed matched
lines at the end of each section). The XLSX: one sheet per section + a Totals sheet, the same columns.
### 3.4 The hub and the old report
The hub's first card gains **"The count statement — section by section"** (page · PDF · Excel) above "The count — full report". The old
report page keeps its route, loses the lanes' "still need a word / decision desk" block (the count is closed; say "closed on <date> — see the
statement"), and its links point at the statement. The hub status card names the S430 groups (old stock, owner's use) — the label line
REPORT_S430 left open.

## 4 · Pins — read live after S430: stock_app.py (S428's TO 0e0fc043 unless S430 moved it — read live), stock_hub.html 74ea0699,
section_map.py 9bf9b98f (read only), stockmatch.py df5501ea (read only), the S226 report page file (read live; one block removed),
NEW stock_statement.html + the statement routes in stock_app.py (or a new `stock_statement.py` mounted the S418 way — decide, say which).
Spine read-only. Restart `clinic-finance` only.

## 5 · Walk (scratch; rows keyed W431*)
Three sections, every one of the 373 counted lines appears exactly once (matched or differing); a confirmed swap reduces both partners and a
not-confirmed one reduces nothing; the medicines' "what became of it" matches the S427 run group by group and the totals equal the close's
(Rs 64,678.78 written off, 136 lines; back 6); the orthotic totals at selling price; price sources tagged and the unpriced residue counted;
a crafted orthotic with a purchase rate and no spine fact prices by the 0.30 rule; freeze writes one row with md5, PDF and XLSX, a second
freeze is a second row; bhati/darpan/shavez refused; the old report page shows "closed" and no decision-desk pointer; S427 82/82, S428 73/73,
S430 42/42, S404 65/65 re-run green · negative control.

## 6 · Done means
Kit `deploy_kits\S431_COUNT_STATEMENT\` · installed · published · `claude_code_briefs\REPORT_S431.md` — owner lines first: the three sections'
totals as they read now (short / excess / net at selling price, lines), the orthotic block (open lines, unvouchered, unpriced named), the
unpriced residue per section; ending with `https://followup.dr-manoj.in/finance/stock/page/statement?count=1`.
