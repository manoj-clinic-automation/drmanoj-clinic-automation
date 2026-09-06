# HANDOFF RUNBOOK — S227 close · 06-Sep-2026 · v159

*Supersedes v158 (S226 close). §0 what happened · §1 the models it earned · §2 the live backlog (the live list is `OWNER_TODO_LIVE.md`; this is the close-time snapshot) · §3 install discipline · §4 the boundary. Full narrative: Archive §S227. Pins: Register v5.76, `live_pins_S227close.txt`. The two documents to read instead of the twelve S227 papers: `S227_BUILD_BRIEF` (what is live and why) and **`S228_BUILD_BRIEF` (the owner's rulings for the next session — read this one first).***

---

## §0 · WHAT HAPPENED

**One afternoon and evening, 06-Sep 14:15 → 22:00 IST, ~8 attended hours, one compaction; eight kits, each installed by the owner from one line and every VPS pin pasted back from the box the minute it landed.**

1. **The count kept and handed back** (`S227_PAD_PROOF`): every uploaded sheet byte for byte in `pad_uploads/`, a PDF receipt for the counters. Count #1 of 06-Sep (14:41 IST) closed by the checker — the subject of the day.
2. **The hand sheet and the mismatch at MRP** (`S227_DIFF_SHEET`), then **the analytics layer** (`S227_FINDING_REPORT`): every difference against purchases, sales and returns; the inline life; the residue no document explains.
3. **The owner's brief → `S227_LOSS_TRIAGE_PLAN` v4 → `S227_LANES`**: eight lanes with a reason per line, the price ladder, the allowance engine, bulk decisions (`stock_diff_lane`, mirrored to the S221 layer), D385. His verdict on the page: *too much data in a very confusing manner … too complex and daunting for a human.*
4. **`S227_DESK`** — one card, one question, big buttons; the report a document. And in the same kit the day's real finding: **F-334** Marg's purchase LOOSE column is the whole quantity (BIO D3 MAX "20 + 300 loose" read as 600), **F-335** overlapping exports leave a bill line twice (150 double entries); the PURCHASE DATA AUDIT born.
5. **`S227_PINPOINT`** (strips and tabs everywhere — D384; the residue export day by export day; a late-keyed bill found; ONE question on Amir's lookup list) → **`S227_CONCLUSION`** (the conclusion first, workings folded — D383; IN/OUT; "Send Marg's answer to the server"; the first-write-off-candidates card).
6. **The owner with the first live lists in hand** → **`S227_STAFF`**: spans merged (F-336, the "74 strips OUT then 34 IN" narration gone); the consumables lane (D386); orthotics families; Darpan's lists in turns (D387, `stock_tranche`, no rupee on his sheet); AMIR'S BOARD with the upload box; the audit actionable only (F-339). `S227_STOCK_CHECK_LESSONS` written.
7. **At the close he ruled the S228 shape** (`S228_BUILD_BRIEF`): item-ledger exports analysed on the server for the four live residues (VINTAZ P is an item merge — **F-337**); under one strip = a voucher; **stock adjustment vouchers, 8 a voucher, are the way to match the count (D388)** — Amir's board shrinks to two jobs; Darpan's lists move to the owner's page; **the owner's LOSS DESK and the random spot counts (D389)**.

**Live at close:** `stock_app.py` `8eef6420…` · `stock_check_live.html` `3d6a2fb8…` · `stock_report.html` `9be950f2…` · `stock_desk.html` `f044a5db…` · `stock_amir.html` `56ed926f…` · `pad_receipt.py` `a52751f4…` · `padreader.py` `afa8da2f…` · `padwriter.py` `e7546afe…` · `stock_pad.html` `4b593dbb…`. manojz files unchanged since S226.

**Canon:** Archive v1.73 (§S227 appended, prefix proven) · Register v5.76 · Fault v2.58 (F-334 … F-339) · this runbook · `START_HERE_SESSION_228` · `S227_BUILD_BRIEF` · `S228_BUILD_BRIEF` · `live_pins_S227close.txt`. **Next free D390 · F-340 · Session 228.**

---

## §1 · MENTAL MODELS THAT EARNED THEIR PLACE THIS SESSION

- **The human reading one item finds what the walks cannot.** F-334 was found by the owner reading BIO D3 MAX's purchase list; F-336 by reading the first lookup list; F-339 by opening the audit workbook. Every one became a fixture in a walk the same hour. Two closes running now: the counter proves the join, the owner proves the reading.
- **A column's meaning is read from the data, never from its name.** "Loose" was the whole quantity. "Superseded" covered one period only. An export day is a boundary with a width.
- **The conclusion first; the workings behind a button.** A narration that leads three ways is not a finding. One boxed line, colour-coded, then *Show how this was decided*.
- **One vocabulary for quantity.** Strips and tabs, pcs for pack 1, IN/OUT in words. "400 units" is a remnant of the machine; "40 strips" is the shop's.
- **A staff sheet carries only what needs that person.** The server's findings about itself stay on the server. Lines that agree are never printed. A counter's sheet carries no rupee.
- **Read the family, not the line.** Orthotics differ by brand and agree by article; the family net is the finding.
- **The way to match a counted stock is a voucher, not a list.** Eight items a voucher; the cleanup, no-movement and orthotics lists were three names for one job (D388).

---

## §2 · THE LIVE BACKLOG (snapshot; `OWNER_TODO_LIVE.md` is the live truth)

**⭐0 — the owner's own actions:** VINTAZ P 4500 INJ → Write off on the desk (one tap); a Marg backup; the 12 below-zero items = bills into Marg; the wall-card reprint after its revision (F-310); the August advances on the ledger; one word on the S182 tiles; FINALISE September and August; the delete lists (`_to_delete_S224 … S227` per drive root); the SSD housekeeping list.

**⭐1 — build next, in his order — `S228_BUILD_BRIEF`:**
1. **The item-ledger import**: Amir exports Marg's item ledger as Excel for the items and windows the server names; the server reads it and names the voucher (DISPO SYRINGE · VINTAZ P · TYRO BR · ASTOFEN SP first). Under one strip → straight to a voucher, no question.
2. **Amir's board → two jobs**: (a) the ledger exports wanted + the upload box; (b) STOCK ADJUSTMENT VOUCHERS to match the physical count — decided lines grouped 8 a voucher, issue for excess, receive for additions, one Excel per batch; the cleanup / no-movement / orthotics lists collapse into it; agreeing lines never shown.
3. **Darpan's lists move to the owner's page** (the tranche engine stays; the owner cuts and owns them).
4. **The owner's LOSS DESK**: tick items; loss at MRP and at cost; high-cost and high-volume on top; an A4 portrait core-data print for Darpan (item, shortage, MRP/sale price, loss at MRP, total) saved on the VPS as the shared copy; recoveries logged for the next check.
5. **The spot-count card** (Darpan's page, Hindi): random items daily, counted, matched live, mismatches flagged to him and the owner, every count logged.
6. **Kit C**: the nightly Marg residue audit (plan §9), the pre-count readiness gate (non-overlapping purchase export; item master with MRP + salt; closing stock after the day's last entry; pending bills keyed), reading the uploaded Marg answers; `finance_backup.sh` + `pad_uploads/`.
7. **Then, unchanged from S226:** the wall card revision (F-310) · the joiner reset button (F-333) · Google Fonts off the count page · the S208 kit revision · SALT WISE · NEFT · the loans PWA view · procedures (D373) · the S223 dawn specs · the tracker parser fix, then the diagnosis upload.

**Parked by him:** the bank-name dropdown · attendance under the main domain. **Standing holds:** NEFT — nothing SENT without his word · the hub's shape not reopened · the on-screen count path second choice until the Excel phase is evaluated.

---

## §3 · INSTALL DISCIPLINE — what S227 added

- **Every real data shape the owner finds becomes a walk fixture the same hour** (BIO D3 MAX, TYRO BR, ROSIKA FORTE, LACTOVAX, the knee supports) — the walks now hold the shop's own shapes, not the assistant's.
- **A kit that changes the stock pages ships all ten walks** (staff 27 · audit 53 · desk 47 · lanes 46 · report 46 · diff_sheet 41 · pad_proof 65 · count_search 34 · submit_flow 30 · safestore 13) and its evidence names each.
- **One-line installs guard EVERY live pin they replace** (six at S227_STAFF), back each file up as `.bak_S227<kit>_<date>`, compile to `/tmp`, restart, print the sums, roll back by themselves.
- **A screen is read by a sub-agent at native resolution before packaging**; a wording slip found there is fixed before the kit is committed (one at DESK, none after).
- **Word lists that classify stock are tested against the whole shop's names** (F-338).
- All of S226's, S225's, S224's and S223's rules stand.

---

## §4 · THE BOUNDARY

- **The publish is the owner's double-click**: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
- **Patient data is not in this project. No number in the repository (F-185).** The stock papers carry item names, staff first names and bill numbers only.
- **Nothing here ever writes to Marg, sends to a bank or a vendor, or leaves the server** (D325). The adjustment vouchers are Amir's hands in Marg, from a list.
- Nothing live is rebuilt without his explicit OK; the manual workflow stays as fallback.
- **ClickUp is parked (D17).**

---
*HANDOFF_RUNBOOK v159 · S227 close · 06-Sep-2026 22:00 IST.*
