# S226 BUILD BRIEF — the one document to read instead of the nine S226 papers

*06-Sep-2026, 04:15 → 14:00 IST. Written at the close. Full narrative: Archive §S226; state: Register v5.75; backlog: Runbook v158 §2. The nine papers (`S226_READINESS_HEADER_BUILT` · `S226_FIRST_LIVE_LOOK` · `S226_PURCHASE_FEED_AND_SENDER_FIXED` · `S226_COUNT_PAGE_CRASH_AND_SEARCH` · `S226_FINDING_REPORT_SPEC` · `S226_COUNT_PAGE_HARDENED` · `S226_PAD_IMPORT_BUILT` · `S226_PAD_ONPAGE_BUILT` · `S226_STOCK_CLOSE_BUILT`) are the record; this is the handover.*

## 1 · What the next session inherits

**The stock check runs on ONE page**, `https://followup.dr-manoj.in/finance/stock/page/count`, as a numbered flow: **1** the four details (who counted · who is entering · last sale bill · its date) → **2** *Download SHEET 1* (comes down with the four written in B5/B6/B7/E7) → **3** *Upload the filled sheet* (one tap; processing box) → **4** the box says what was recorded and what is left — *Some stock count is left: N not counted, M to fix. Download the sheet and complete it* → SHEET 2 REMAINING, 3, 4 … → when the server verifies nothing is left, **Close the stock check** → STOCK CHECK COMPLETED → FINAL RESULT sheet; that count takes no more sheets. The checker alone sees *Doctor: close count #N as it stands*. *Recent stock checks* lists every count with its state and sheet. The old `/page/pad` redirects here. The on-screen count path is on hold as the staff route.

**At close the counters are filling the pre-prefill pad** (`STOCK_COUNT_PAD_06-09-2026.xlsx`, blank top lines): the page will ask for the four details once and record the same file on one tap. **Nothing has been uploaded.**

## 2 · What is live (every VPS pin pasted back from the box)

| file | md5 | kit |
|---|---|---|
| `/root/finance/stock_app.py` | `fdcdf873dc217284ad78563195f52a71` | `S226_STOCK_CLOSE` (chain a61af74a → d977d5b4 → c338d6ad → 02a0573f → 4578b725 → fdcdf873) |
| `/root/finance/stock_check_live.html` | `6fd3b7f96e24509a6124854946cd12b7` | `S226_STOCK_CLOSE` (chain 298005a2 → 75a53efb → cbcc1cdf → fe7d37aa → bfdf4cde → 8ed0cdf2 → d529857f → ed47601b → 6fd3b7f9) |
| `/root/finance/padwriter.py` | `77c43e470d5ffd88019c4469281690b1` | `S226_STOCK_CLOSE` |
| `/root/finance/padreader.py` | `f617d7d5198235720a768e8184b9eaa3` | `S226_PAD_ONPAGE` (F-331: the PAD_IMPORT copy dd32617b lacked `SHEET ROW`) |
| `/root/finance/stock_drift.html` · `stock_now.html` · `stock_pad.html` | `daa40ee8…` · `91cdc56d…` · `4b593dbb…` | `S226_DRIFT_TRUTH` · `S226_PAD_IMPORT` |
| manojz `deploy_kits\S208_STOCK_LEDGER\push_snapshot.py` · `push_expected.py` | `03a84524…` · `a0e47a98…` | `S226_F322_SUBSET` · `S226_PURCHASE_BILLITEM` |

Tables created on first request: `stock_check_readiness` · `stock_count_pad_issue` · `stock_count_part` · `stock_count_pad_file` · `stock_count_close`. Routes: `/api/readiness` · `/page/now` `/api/now` · `/pad.xlsx?cby&eby&bill&bdate` · `/api/pad/upload` · `/api/pad/close/<cid>` · `/api/pad/recent` · `/api/pad/followup/<cid>.xlsx` (the result workbook; family-aware) · `/api/pad/preview` + `/api/pad/commit` (kept for a console).

## 3 · The rulings that shape the next layer (D377–D382; full text Archive §S226 §2)

Accept, never reject (D377) · the five-tab result layout in strips & tabs (D378) · explanations optional and in tranches, delivery on the portal tiles, staff see rupees (D379) · **one coherent system** — spot checks anywhere are counts in this ledger; the Excel is a phase (D380) · the Excel flow lives on the count page, staff never need him (D381) · Close the stock check, server-verified; he alone closes an abandoned count so analytics run (D382).

## 4 · The next layer, in his order (Runbook v158 §2 ⭐1)

1. **The finding on screen** to the workbook's layout (`S226_FINDING_REPORT_SPEC`): a count and all its parts together; the frozen *Read first* lines on top; explanations in tranches (*"12 of 27 explained"*); Download PDF; on the portal tiles for him, Darpan, Amir. A closed count (`stock_count_close.how` = complete | incomplete) is the unit; on-screen counts (sealed at send) as before.
2. **The item ledger** behind every difference — purchases (vendor, bill, date, qty), sales, credit notes, Marg vs ours by day, the scan.
3. **The unexplained-movement detector** on that ledger.
4. **Spot checks folded in** (D380) — `stock_spot_check` and the Darpan/medicine-page checks become counts marked *spot*.
5. **Retire the Excel** after feedback; server-side autosave for the on-screen count first.
6. The server-side computation (`S226_EXPECTED_ON_SERVER`) — the gate is open.
7. The S208 kit revision (F-319 · F-323) · the wall card (three pages → one; BILL ITEM WISE naming trap; *enter a bill the day it arrives*) · the reset-password route (F-333) · Google Fonts off the count page.

## 5 · What this session taught (the rules, short)

The walk proves the kit; the counter proves the join — drive every chip, the reload, the revisit, the failure path, at 390px. A screen that opens a record never writes it (F-329). A store that can fail says so (F-330). An append-only table is read by its newest row per key (F-324); two totals that share an input cannot agree (F-326). A Marg report name is read to the letter. The walk imports the file the kit ships, from the kit folder (F-331). `find`, never `git`, on the mounted repo (F-332). A closed count is closed.

## 6 · Faults minted

F-324 … F-333 (Fault Register v2.57). Eight the assistant's own; F-327 live since S213; F-333 a stub.

## 7 · Owed to him

A Marg backup (7 days old at the heartbeat) · the 12 below-zero items are bills into Marg · the wall-card reprint after its revision · the delete lists (`_to_delete_S226\` under `D:\dr-manoj-git\` and `D:\Downloads\`).

---
*S226_BUILD_BRIEF · in three places: project knowledge · `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S226\` · `F:\ClinicBackup\DrManojClinic_Automation\03_BUILD_BRIEFS\`.*
