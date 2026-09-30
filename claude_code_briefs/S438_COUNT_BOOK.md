# Claude Code brief — S438_COUNT_BOOK (the count's presentation rebuilt once: one calculation, one data shape, every page and PDF rendered from it; the mock is the contract)

Written 30-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S438 · decision D639** (claimed on the System Board). Runs AFTER
S437 (live 28-Sep 23:09 IST). **Sanjeevni-owned.** No parent file. Restart `clinic-finance` only. **This kit REPLACES the presentation that
S418/S427/S428/S430/S431/S432/S436/S437 patched; it does not patch it again.** The owner approved the mock on 29-Sep ("these look OK"):
`claude_code_briefs\S438_COUNT_MOCK_06SEP.html` — every table there, with the real 6-Sep figures, is the acceptance picture. Where the mock
and this text differ, the mock wins.

## 1 · The owner's words (29-Sep)
"A simple tabular format is the most non-confusing way: the name of the medicine, Marg quantity briefly in strips and tablets — the strips
in numbers, then a colon, then the tablets — the physical count, the difference, the loss at MRP." "The surplus is clubbed — 'total loss
this much minus surplus'. Surplus is separate; it is not to be adjusted against the losses." "The PDF output should be multiple: an
alphabetical list as in Marg's stock for them to correlate, and a section-wise one — the write-offs, the major ones and the orthotic
section — so they get both the raw and the structured." "There are totalling differences of the amounts on different pages; that should go
away." And on the plan: "all agreed"; "it needs to be a safe method, according to the planned architecture."

## 2 · Why one module (read REPORT_S431/S432/S436/S437 for the state; do not re-read the patch history)
The same loss is valued four ways today: the desk's median-sale "MRP" (loss_piles / stock_app `_pad_report_data`), the spine's
S.RATE/MRP (stock_statement), cost (stock_watch leakage), and per-page sums (hub `_desk_totals_safe`, the S427 block, the S431 statement,
the S437 tables) — so ₹85,236 / ₹64,679 / ₹61,076 / ₹1,19,749 / ₹43,647 appear for one count, and the statement nets surplus against
loss. The fix is structural: one calculation, one shape, many renderers.

## 3 · The build (D639) — NEW `/root/finance/count_book.py` + `count_book_pdf.py` + `count_book.html` (the owner's statement page)

### 3.1 The one calculation — `book(con, spine, count_id)` → a `CountBook`
- **Lines**: every counted item of the count (373 for #1), keyed by the spine identity (`item_alias` applied), with section from
  `stock_item_section` (Medicines · Consumables · Orthotics), packing and the whole-piece word (S437's list).
- **Quantities** in smallest units, then rendered as **`strips:tabs`** ("23:4"; "0:8"; negative "-1:3") and plain numbers for pcs / bottles /
  vials / tubes / sachets (`qty_words.colon()` — one new function, the only new notation; the old words stay for the ordering/notice pages).
- **Marg** = the sealed count's Marg figure; **physical** = the sealed count (S427 accept-backs and Darpan's recounts overlay as the S418
  layer does today, shown as the physical figure with a footnote mark); **swap** = the confirmed pair quantity; **short / surplus** = after
  swaps; a Marg-negative line = "Marg correction" with the correction quantity, no goods, no money.
- **Price** = the spine's S.RATE as on the count day, else its MRP, else the S431 fallbacks — ONE function `price_on(item, day)`; the desk's
  median-sale price is not read anywhere in the book. **Money** = quantity × price, **whole rupees**, on shortage lines (loss ₹) and on
  surplus lines (surplus ₹, separate). Cost is not in the book.
- **Outcome** per line, one word, from the frozen runs and decisions already in the tables: `loss-big` · `loss-small` (allowance + small
  + earlier) · `loss-ortho` · `consumption` · `owner's use` · `old stock` · `back in store` (accept-backs and sales-test) · `surplus` ·
  `Marg correction` · `swap` · `matched`. For count #1 these come from the S427/S430/S436/S437 runs as they stand (the 3 orthotic lines the
  owner settled on 26-Sep count as `loss-ortho`, as the mock shows: 13 lines, ₹6,860).
- **Totals**, computed once from the lines: LOSS = loss-big + loss-small + loss-ortho (orthotics always shown as their own figure and
  never merged); WRITTEN OFF, NOT LOSS = consumption + owner's use + old stock; BACK IN STORE; SURPLUS (separate, never subtracted);
  CORRECTIONS (count of lines). Section totals the same way. **No "net" anywhere.**
- Frozen: `stock_statement` rows (S431) keep working — a freeze stores the book's JSON + md5; the live book is served until the owner
  freezes; every renderer takes a book, frozen or live, never the tables directly.

### 3.2 The renderers — all read the book, nothing else
1. **The one card** (mock page D): hub status card, the owner's desk header, the statement header, the Needs-you line — the same
   `CountBook.totals` table: Loss (med+cons, big + small) · Loss (orthotics) · TOTAL LOSS · Written off not loss · Back in store · Surplus ·
   Corrections. The leakage line stays on the Month table only, labelled "at cost".
2. **Sheet 1 — Marg order** (mock page A): `/finance/stock/count/<id>/sheet1.pdf` — every item alphabetical as Marg prints; columns
   # · Item · Packing · Marg · Physical · Short · Surplus · Loss ₹ · Outcome; Medicines and Consumables then **Orthotics on their own
   pages**; section total rows (short lines · surplus lines · loss ₹); landscape A4, gridlines, one row per item, no sub-lines, header on one
   line per fact, footer "Count of <date> · sheet 1 · page x of y"; the count-day staff copy (3.3) is this sheet without the two money/outcome
   columns.
3. **Sheet 2 — Section by section** (mock page B): `/finance/stock/count/<id>/sheet2.pdf` — the summary table first (the mock's rows,
   "counts as" column), then A Big losses · B Small write-offs · C Consumption & owner's use · D Old stock · E Back in store · F **Surplus,
   its own table** · G Marg corrections · then ORTHOTICS: H Orthotic losses · I orthotic surplus and corrections. Each table with its total
   row; the section totals add up to the summary; nothing netted.
4. **Darpan's block** (mock page C): on Stock milaan and in the record — "Ginti <date> · kul kami ₹X (dawa + consumables)" · Badi kami table
   (Item · Marg · Gina · Kami · Rs) with a total row · Chhoti kami collapsed with its total · "Orthotics band ho gaya — kami ₹Y (N line, bina
   bill)" with the orthotic lines collapsed under it. The page ends there. No reasons, no percentages, no surplus, no Amir lines.
5. **The owner's statement page** `count_book.html` (replaces the S431 page at the same route): the one card, then Sheet 2's tables on
   screen (collapsible), links to the two PDFs and the Excel (one workbook: Sheet1 / Sheet2 / Totals, paise allowed), **Freeze**.
6. **The count-day sheet at sealing** (from count #2): the moment a count is sealed (S226 seal), Sheet 1 without money/outcome is written
   as the count's first attachment and offered as **Print** on the hub and on Darpan's Stock milaan (Hindi headings, English item names);
   for count #1 it is generated post facto by the install.
7. **The record PDF** (S418 `record.pdf`) = the one card + Sheet 2 + the decisions log; the S427 block paragraphs go.
- Old renderers: the S431 statement page, the S427/S437 block builders and the hub's `_desk_totals_safe` stay callable behind setting
  `count.book_off` (default 0) for one week as the fallback, then a later kit removes them.

### 3.3 Rulebook and repo changes in this kit (the owner's ruling of 29-Sep on build cost)
- `CLAUDE.md`: **one consolidated count walk** — `walk_count.py` in the kit reads the LIVE state of the count subsystem (no crafted rows
  except its own W438* lines), asserts the book's invariants (every counted line once; section totals = summary; LOSS excludes surplus;
  the four pages and two PDFs show the same totals; the word gate; the colon notation) and REPLACES the re-run of the seven earlier count
  walks (S404/S427/S428/S430/S431/S432/S436/S437 are superseded for this subsystem — say so in the README; their kits stay frozen);
  **walks compute dates from today** (never a hardcoded date); **one dry run** before the install unless a gate is red.
- `COUNT_MAP.md` in `claude_code_briefs\`: the count subsystem's files, tables, routes, settings and the book's shape, one page, updated by
  every later kit that touches it.
- The orthotic renames stay gated (S437) — the owner does them later, clubbed; nothing here shows them.

## 4 · Pins — read live after S437: stock_app.py 4f2625c0, stock_hub.html a710a98a, stock_loss.html 0f0dfed6, stock_statement.py 1a4f6c9e,
stock_statement.html (S437's TO), stockmatch.py f09d9516 / .html 0dc4d303, loss_piles.py 202bfc4e, qty_words.py 706db7cc, stock_watch.py
9cca2f2a (the Needs-you count line reads the book), CLAUDE.md (the rulebook lines above). NEW count_book.py, count_book_pdf.py,
count_book.html, walk_count.py, COUNT_MAP.md. Spine read-only. No parent file. Restart `clinic-finance` only.

## 5 · Walk — `walk_count.py` (live state on a scratch copy + W438* lines)
Book of count #1: 373 lines, each once; totals equal the mock's figures (big 22 · ₹29,658; small 101 · ₹34,006; orthotic 13 · ₹6,860; TOTAL
LOSS ₹70,524; not-loss ₹23,462; back ₹25,764; surplus 21 · ₹16,122) — print any difference with its line and stop; the hub card, the desk
header, Darpan's block, the statement header, Sheet 1, Sheet 2 and the record show the SAME totals (a gate compares the seven); no "net"
string anywhere; surplus never subtracted; orthotics never inside a medicine total; the colon notation on every quantity and no "unit(s)";
Sheet 1 alphabetical with orthotics on separate pages; Sheet 2's section totals sum to its summary; the count-day sheet has no money
column; a crafted W438 line moved between outcomes changes exactly the two totals it should; `count.book_off` = 1 restores the old pages
byte-for-byte; the freeze stores the book and the frozen pages serve it; dates computed from today; negative control (old files: netted
statement, differing totals).

## 6 · Done means
Kit `deploy_kits\S438_COUNT_BOOK\` · installed · published · `claude_code_briefs\REPORT_S438.md` — owner lines first: the one card's
figures, the two PDF links, Darpan's block in four lines, what was measured on the box for the build (dry runs, minutes); the README names
the superseded walks; ending with `https://followup.dr-manoj.in/finance/stock/page/statement?count=1`.
