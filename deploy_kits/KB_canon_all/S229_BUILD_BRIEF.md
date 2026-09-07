# S229 BUILD BRIEF — the one document to read before building

*Written at the S228 close, 07-Sep-2026. Replaces reading the S228 papers.*

---

## THE SITUATION IN FOUR LINES

1. **581 purchase lines — all of April, May and June — are undated on the server and invisible to every stock calculation (F-340).**
2. **Three sale days never arrived** — 19-04, 04-05, 27-05 (397 lines) (F-341).
3. **Both are repaired by Marg exports, not by code.** `_redate_lines()` runs on every push and dates the 581 by itself.
4. **`finance.db` is readable from Google Drive** (`FinanceDB_Backups/finance_nightly.db.gz`). Never ask him to paste database output again.

**Nothing is missing from Marg's report set.** Sale returns are inside the item-wise sale reports (376 credit-note lines across all 182 CNs,
with item, pack and quantity); purchase returns are inside the item-wise purchase reports. He corrected both of those claims and was right.
**He does believe more exports exist than have been found — search again before asking him.**

---

## ⭐1 · THE SHEET, HIS WAY — the first thing to build

`D:\Downloads\margsync\_analysis\stock_check_06Sep2026.html` is good in structure and he said so. Two changes:

**a. The top must be section-wise, the way his live page is** — the sections presented first, as things to act on, not a paragraph followed
by a long list. His words: *"in the top section the all goods are listed in one list, it should be section wise as you had prepared for my
page… so that we have sections to act upon."* Find the live page he means (`/finance/stock/page/...`) and match its section presentation.

**b. The Darpan share is made FROM the sheet.** Select items on it — *"5 big losses one and five smaller medium"* — and either share them to
Darpan from there or hand him a PDF he generates himself. The loss desk already owns the frozen-sheet mechanics
(`stock_loss_tick` / `stock_loss_share` / `stock_loss_recovery`); this is the selection surface in front of it, not a second engine.

**What the sheet already does and must keep:** six sections classified by the **live server's own** `_is_consumable` / `_is_orthotic` word
lists (D390); money behind a toggle whose hidden state carries no rupee figure, no money word and no ₹ anywhere in the file, proven from the
printed PDF's text (D391); only the items that differ tabulated, the ones that matched named in an appendix (D393); MRP from the item's own
sale lines and cost from the last purchase rate, with each total's coverage said out loud (D394); alphabetical inside each section (F-345);
one quantity shape per row and "nil" for zero (F-344); "minus" spelled out for Marg's below-zero balances (F-343); A4 portrait, section name
and column headers repeating on every page, a 7 mm writing box per line.

**The generator is two scripts, kept together:** `build_table.py` (reads `finance_nightly.db` + the Marg closing-stock export, writes
`table.json`) and `make_page.py` (writes the HTML). Both were rebuilt four times against sub-agent screen reads; the reads are the test.

---

## ⭐2 · FIND THE REST OF THE MARG EXPORTS

He is confident more exist. Where to look, in order: `D:\Downloads\margsync\MargArchive\` (by type and month, including `_REFUSED`,
`_UNKNOWN`, `_rescued`, `_outbox`, `_spool`) · `D:\Downloads\margsync\marg_reports_mirror\` · `D:\Downloads\margsync\_analysis\` ·
`D:\Downloads\ClaudeCowork\02_SESSION_KITS\*\06_SOURCE_REPORTS\` (**this is where the ten hand-named fortnightly sale workbooks were
hiding** — `claude 1 april to 15 april.xlsx`, `CLAUDE MAY 2026.xlsx`, `MARG_1_15_AUG.XLS` and the rest) · Google Drive (the archive mirror
folders) · `F:\ClinicBackup\`. **A hand-named workbook in a session folder is invisible to the router and to every `find` that only looks
for canonical names. Search by content, not by filename.**

---

## ⭐3 · REPAIR, THEN RECOMPUTE

After the two exports land: recompute, then build **our own item ledger from 01-04-2026 in Marg's own shape**, per item, and match it against
the three ledger exports already proven (TYRO BR, MEG QCS, PATOPEN DSR — they walk exactly and tie to Marg's Received/Issued totals to the
tablet, via `_analysis\marg_item_ledger.py`). **That match is the acceptance test and it already exists.** Only when it passes may the
stock-check screens quote a number.

`S228_THREE_WAY` is the screen that shows whether our figure and Marg's now agree, and refuses to call a count trustworthy until they do.
It is built and waiting for one paste.

---

## ⭐4 · THE DATA MANAGEMENT SYSTEM

His words: *"we do an export to develop a data management system for this inventory and sales system… scoped for this inventory management
only, of the stock check."* Scope it exactly that far. Do not widen it.

---

## ⭐5–7 · THEN

The adjustment-voucher engine (D388, 8 items a voucher) with D397's wording — "Marg में घटाना है" → STOCK ISSUE, "Marg में बढ़ाना है" →
STOCK RECEIVE. The report-page rewrite to his display rulings. The PWA: simulate in one place first, then sub-navigation on the tile (D395),
per-role destinations, lab-staff logins with attendance and advances only (D396).

---

## THE TRAPS THIS SESSION PAID FOR

- **`_qw()` is unsigned.** Hand it a figure that can be negative and it prints a lie (F-343).
- **A CSS width set under `table-layout:fixed` is arithmetic.** 109 % is silently scaled and your fix disappears (F-346).
- **A page's sort order must be legible in the state the reader is in** — money-ordered rows in a copy with no money (F-345).
- **Marg's item ledger is Excel TIME.** Convert to tablets at the door; negative balances arrive as text (F-348).
- **Name a report missing only after reading the report that would contain it** (F-347).
- **Enumerate the attached sources before asking him for anything** (F-342).
