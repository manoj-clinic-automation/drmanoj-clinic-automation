# HANDOFF RUNBOOK — v160 · written at the **S228 CLOSE**, 07-Sep-2026

*(Tier 0. Supersedes v159. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the boundary.)*

---

## §0 · WHAT HAPPENED — S228

**Connected: `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` (transfer tools only).** The assistant's browser was not used.
**Google Drive was, and it changed the session.**

Three builds and then an audit that made the builds beside the point.

**`S228_LOSS_DESK`** — 39 files, 496 checks, three sub-agent screen reads, **installed by the owner from one line with all five pins as
predicted**: `stock_app.py` **c8e2a6b8** · `pad_receipt.py` **49ced287** · `stock_amir.html` **adf206b5** · `stock_desk.html` **54aeda96** ·
`stock_loss.html` **0d772034** (new). Tables `stock_loss_tick`, `stock_loss_share`, `stock_loss_recovery`; `pad_uploads/loss_shares/`.
A line on a frozen sheet keeps that sheet's figure, cannot be re-shared, and shows `back_p` when partly recovered.

**Marg's batch-wise item ledger, read and proven.** `_analysis\marg_item_ledger.py` (**01d365da**) reads the export the owner produces;
TYRO BR, MEG QCS and PATOPEN DSR all walk exactly and tie to Marg's own Received/Issued footers to the tablet. Four encoding faults on the
way, all in F-348: a balance column off by one; **base-60 aggregation** (Excel TIME carries loose at 60, not at the pack); a running balance
seeded in minutes against an accumulator in tablets; and negative balances arriving as **text** (`-2:10`). The archive router refused every
one of these files until `read_preamble` stopped assuming column A and `RE_RANGE` learned "FROM a - b" (**F-349**) — regression over 152
archived files: **148 identical, 4 changed, all four the refused ledgers**.

**`S228_THREE_WAY`** — 544 checks, four screen reads, **built and held back**. It exists because `stock_snapshot` is keyed `(as_on, item)`
and **last write wins**, with two senders pushing to it; nothing said which one a count was measured against (**F-350**).

**Then the owner stopped the build** — *"go to the very basics of the setup and check the data… name the report which is lacking"* — and the
session found the thing two sessions had been arguing about.

**F-340. 581 of 1,148 purchase lines have no bill date, and all 581 are April, May and June.** Every stock query filters
`bill_date IS NOT NULL`, so `_purchases_since()` sees 567 lines and drops the rest without a word. ITEMWISE prints no bill date;
`_store_lines()` dates a line from `purchase_bill`, which only BILLWISE / SUPPLIERWISE fills, and the earliest of those is July.
**The arithmetic was never wrong. It was running on a third of the purchase history.** `_redate_lines()` runs on every push, so **one
export — PURCHASE BILLWISE 01-04 → 30-06 — repairs all 581 with no code change.**

**F-342.** The VPS is unreachable from every shell here (`healthz` http=000, both), but `finance.db` is backed up nightly to the owner's
Drive (`FinanceDB_Backups/finance_nightly.db.gz`). It took him saying so. The session had been asking for pastes.

**F-347.** Two documents written this session were wrong and were withdrawn in writing: April–July purchases had *not* gone unexported,
and the two "missing" Marg reports — sale returns and purchase returns — are both **inside the item-wise reports** (376 credit-note lines
across all 182 CNs, with item, pack and quantity). The owner corrected both.

**The deliverable:** `D:\Downloads\margsync\_analysis\stock_check_06Sep2026.html` — the 06-09 count, six sections, Marg against the shelf,
money behind a toggle whose hidden state was proven free of every rupee, A4 portrait, 9 pages, a 7 mm writing box per line. **373 counted,
166 matched exactly, 162 short, 45 more.** Four screen reads; the first found **Marg's negative balances printing without their minus**
(F-343), which made twelve empty shelves read as full.

---

## §1 · MENTAL MODELS — what to hold in your head next session

1. **A row the system cannot date is a row the system does not have.** F-340 is the whole lesson: 581 rows arrived, parsed, and were counted
   nowhere. An ingest that accepts an undated line must say so out loud.
2. **Coverage is proven day by day against the source.** F-341's three missing sale days were invisible to every month total.
3. **Enumerate the attached sources before asking the owner for anything.** A connector that is attached but never opened is a store nobody
   checked (F-342).
4. **`_qw()` is unsigned by design.** The caller owns the sign. A formatter that cannot print a minus must never be handed a figure that can
   be negative (F-343).
5. **Green checks answer the question they were written for.** Four screen reads, four sets of real defects, all behind passing suites.
6. **Name a report missing only after reading the report that would contain it** (F-347).
7. **`stock_snapshot` is last-write-wins with two senders.** Any page quoting it must name the sender (F-350).

---

## §2 · THE LIVE BACKLOG — the owner's order

**⭐1 · the sheet, his way** — the top section-wise like his live page, sections to act on, and the **Darpan share made from the sheet**:
about five big losses and five small-to-medium, selected there, or handed to him as a PDF.
**⭐2 · find the rest of the Marg exports** — he believes more exist than have been found; the search runs again first, and he supplies what
is genuinely absent.
**⭐3 · repair and recompute** — the April–June dating (⭐0.1), the three sale days (⭐0.2), then **our own item ledger from 01-04-2026 in
Marg's shape**, matched against his three proven ledger exports.
**⭐4 · the data management system for the inventory and sales side**, scoped by him to the stock check.
**⭐5 · the adjustment-voucher engine** (D388, 8 a voucher) with D397's wording.
**⭐6 · the report-page rewrite** to his display rulings.
**⭐7 · the PWA** — simulated in one place first, then sub-navigation on the tile (D395), per-role destinations, lab-staff logins (D396),
advances.
Then unchanged: wall card · F-333 reset · Google Fonts · S208 kit revision · SALT WISE · NEFT · loans view · procedures · S223 dawn specs ·
tracker parser.

**~~Pending install: `S228_THREE_WAY`~~ — INSTALLED at the S228 post-close fold**, hours after this runbook was written. The owner read the box: `stock_app.py` **55cd610e**, `stock_report.html` **bd750dc8**, the other four unchanged, service active. **Passes, not predictions.** Corrected here in place rather than left to be read as current; Register v5.78 and `live_pins_S228fold.txt` carry it. **The live-shape read is owed at the S229 open** — the browser is still in the F-242 login loop, so nobody has looked at the installed page. **Retired unused:** `S228_CENSUS`.

---

## §3 · INSTALL DISCIPLINE — unchanged, and one addition

Pin-guarded one-line installs, self-rolling-back, gates verified **from inside the kit folder**, live-shape walks at 390 px, screens read by
sub-agents. **Added at S228:** a CSS width set under `table-layout:fixed` is an arithmetic claim — **add it up** (F-346); and a page's sort
order must be legible in the state the reader is in (F-345).

---

## §4 · THE BOUNDARY

The VPS is the owner's: every credential, every install, the publish. This environment reads `D:\Downloads`, `D:\dr-manoj-git`,
`F:\ClinicBackup` (transfer tools), the connected MCP sources — **and now the server's own database, through Drive**. It cannot reach
`followup.dr-manoj.in` over the network from either shell. The manual workflow stays as fallback; nothing live is rebuilt without his word.

---
*v160 · written at the S228 close, 07-Sep-2026. Archive v1.74 · Register v5.77 · Fault v2.59 · START_HERE_SESSION_229 ·
`live_pins_S228close.txt`. Next free: D398 · F-351 · Session 229.*
