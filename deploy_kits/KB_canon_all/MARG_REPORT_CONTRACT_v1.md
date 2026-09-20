# MARG REPORT CONTRACT — v1

*S270 (Sanjeevni) · 18-Sep-2026, written 14:31 IST (device clock 09:01 UTC).
For every Marg report this estate reads, this document says **what the report is, what inside it proves the reader right, which fields it may be trusted for, and which it may not.**
Where it overlaps `MARG_REPORT_EXPECTATIONS.md` (S203) — its §2 cadence proposals and §3 "late" rules — **this document supersedes it.** Its §1 (the daily sale report) and §4 (what to do when a report is missing) still stand.*

**Status:** working paper at S270. It goes into `KB_canon_all\` with its manifest row at this session's close (F-537: list the folder and read the board in the minute before writing canon).

---

## 0 · THE RULE THIS CONTRACT ENFORCES

> **A report is a surface. No figure from a report enters canon unless the reader that produced it can fail, and has been made to fail on purpose at least once.** (S268 standing rule.)

For every report below there are three things: the **grammar** (every row class, named by what it *is*, never by exclusion), the **witness** (something printed in the report itself that must re-add from the rows the reader kept), and the **deliberate failure** (one row corrupted on purpose, and the check that caught it).

All figures here were measured at S270 from the archive on manojz (`D:\Downloads\margsync\MargArchive\`) by `contract_harness.py` (working papers, §8). They are stated so they can be checked, not trusted.

---

## 1 · THE EXPORT LIST — what to export from Marg, and how often

*The owner's short list, to keep beside the Marg screen. Detail per report is in §4.*

| # | Marg report | Who · how often | Why |
|---|---|---|---|
| 1 | **Sale — Bill-wise, DETAIL** | **Shavez, every morning**, for the day before | the books; every bill is now re-added from its own lines |
| 2 | **Closing stock — whole stores, totals** | **Shavez, every morning**, with #1 | the stock check reads it; its total proves every row |
| 3 | **Purchase — Supplier/Item-wise** (all columns ticked) | **Amir, every purchase day**, month to date | his lines; each supplier's total proves its lines |
| 4 | **Purchase — Bill-wise** | **Amir, with #3** | the bill totals that catch a bad item-wise export |
| 5 | **Salt-wise item list** | **the owner, every Monday** | name, salt, packing, MRP, P.RATE, S.RATE for every item |
| 6 | **Category-wise item list** — orthotics | **the owner, every month**, and whenever a new appliance is created | the only report that says which items are orthotics |
| 7 | **List of items** (item master) | **the owner, every month**. **One is due now** (the last is 28-Aug) | the only report that carries the company |
| 8 | **Stock valuation** | **Shavez, on the 1st**, as on the month's last day | the money view of the shelf |
| 9 | **Stock expiry** | **Shavez, on the 1st** | what to return before it expires |
| — | Stock register (one item's ledger) | **only when asked** | for one item under investigation |
| — | Sale — daily print (the page Darpan prints) | **no need to send** | it drops the rate on some lines; never a data source |

*Who does what: the owner's word, 18-Sep 20:35 IST. Shavez's morning tile is planned in `SHAVEZ_MORNING_TILE_PLAN.md`; Amir's is live.*

Two things never to export: **Sale bill-wise "Summary-1"** (no cash column) and **Purchase Supplier/Item-wise without the "LOOS PURC." and "AMOUNT" columns** (the 10-column form — refused by design on 17-Sep, because the supplier totals cannot be re-added without them).

**The prescribed discount is in no Marg export** (§3). Nothing to export for it; the owner's register (S235) remains the authority.

---

## 2 · WHICH REPORT IS THE AUTHORITY FOR EACH FIELD

The owner's words: *"there should be no confusion in our system as to what the item name is, what the category is, what the MRP is."*

| field | authority | also printed by (never the authority) | never from |
|---|---|---|---|
| **item name** | **Salt-wise list** (29 characters, every item, weekly) | item master, closing stock, valuation, category list — all 29 | sale reports (**20** characters) · purchase reports (**27**) — both clip, and must be *joined* to the 29-character name, never stored as a name |
| **category** | **Category-wise list** | — | anything else: no other report carries it |
| **salt** | **Salt-wise list** | — | anything else |
| **M.R.P.** (per pack) | **Salt-wise list** | category list — measured identical on all 81 shared items, 18-Sep | sale line rate (it *is* the MRP printed on the bill, but only for what was sold) |
| **packing** | **Salt-wise list** | every item report | — |
| **P.RATE / S.RATE** | **Salt-wise list** | category list (identical) | — |
| **company** | **Item master** | — | anything else |
| **purchase rate actually paid** | **Purchase Supplier/Item-wise**, the **PURC.** figure | — | its RATE column (RYCOBAL D3, April export: RATE 95.00, priced at 94.50) |
| **prescribed discount** | **the owner's register (S235)** | **no Marg report** | S.RATE (§3) |

---

## 3 · THE DISCOUNT — checked, not assumed

The owner asked: *"if the prescribed discount is also mentioned in any Marg output list such as the category list or salt-wise list, that should also be captured."*

**It is not printed in either, nor in any other export held.**

- The category list and the salt list both print exactly five columns: `DESCRIPTION · PACKING · P.RATE · S.RATE · M.R.P.` No discount column exists.
- **S.RATE is not the prescribed discount.** Measured on the 18-Sep category list against the S235 register:
  59 register items are on the list; **38 carry S.RATE = 0**; of the 21 with an S.RATE, **only 1** implies the register's discount. Examples: ANKLE BINDER BAMBOO L — register 20 %, S.RATE implies 5.5 %; ANKLE BINDER L TYNOR — register 10 %, S.RATE = MRP (0 %). Across the whole list 57 of 81 items have S.RATE = 0 and 16 have S.RATE = MRP.
- The purchase report's `DIS.` is the **supplier's** discount to the shop, not the shop's discount to the patient. The sale report's `DISCOUNT` is per **bill**, not per item (S235 §1).

So: **nothing to capture from Marg.** The register stays the authority. The vendor request already on record (S235 — an item-discount column on the bill, the export and the item master) is the only way Marg would ever carry it.

---

## 4 · THE REPORTS THAT CARRY AN ITEM NAME — one contract each

Legend — **Verdict**: *CERTIFIED* = the reader passes every file held and failed on purpose; *CERTIFIED, WITH EXCEPTIONS* = certified, and the named files fail their own witness (those files do not enter canon); *NOT A SOURCE* = the witness itself shows the report cannot be trusted for lines.

### 4.1 · Salt-wise item list — `SALT_WISE_ITEM_LIST`
- **Grammar:** furniture (shop name, title, column header, `Continued..n`, `Page No..n`, advert, blank) · `ITEM_NO_NAME` — Marg's item 1 with an empty description, admitted only before the first heading · `HEADING` (the salt) · `ITEM` — `1     BLING PELVIC TRACTION BELT L | 1*1 | 436.5 | 970 | 970`.
- **Witness:** Marg numbers items 1, 2, 3 … and **restarts at 1 under every heading**; the reader asserts it on every row. New at S270: **every heading must carry at least one item** — this catches a page header misread as a salt when the page breaks *between* salts, where the serial alone cannot.
- **Carries:** salt, name, packing, P.RATE, S.RATE, M.R.P. **No discount, no company, no category.**
- **Clip:** 29 (9 names at 29 in September). No name clipped against closing stock.
- **Held:** 6 files (28-Aug … 18-Sep). **All 6 pass.**
- **Deliberate failure:** (a) page-2 shop-name row turned into a heading — the F-536 bug re-enacted — caught by *every heading carries an item*; (b) item 2 of a three-item salt removed — caught by the serial.
- **Limit, stated:** the last item of a salt, if lost, is not detectable (nothing follows it to contradict it). No total is printed.
- **Verdict: CERTIFIED.** Trusted for: name, salt, packing, MRP, P.RATE, S.RATE.

### 4.2 · Category-wise item list — `CATEGORY_WISE_ITEM_LIST` (new at S270)
- **Grammar:** as 4.1; the heading carries a printed zero (`ORTHOTICS | 0.0`); no `ITEM_NO_NAME`.
- **Witness:** the serial restart, as 4.1, plus the empty-heading check.
- **Carries:** category, name, packing, P.RATE, S.RATE, M.R.P. **No discount** (§3).
- **Clip:** 29.
- **Held:** 2 files, both 18-Sep (07:45 and 07:48 IST), identical rows. **Both pass.** Every one of its 81 items is on the salt list with the same packing and the same three rates.
- **Router:** had no signature and refused both copies. **Signature added at S270** (a data edit in `D:\Downloads\margsync\MargPull\signatures.json`, backup `signatures.json.bak_S270_b2dcb211`); the router's own selftest passes with it (55 checks), the other 18 signatures are byte-unchanged, and **both copies re-filed themselves as VERIFIED** at the 14:21 IST rescan into `MargArchive\CATEGORY_WISE_ITEM_LIST\`.
- **Deliberate failure:** page-2 shop name as heading → serial; one item removed → serial.
- **Limit:** no total; no completeness marker (its last line is Marg's rotating advert), so a cut at the very end is not detected.
- **Verdict: CERTIFIED.** Trusted for: **category membership.** Everything else it prints is taken from the salt list.

### 4.3 · Item master — `ITEM_MASTER` ("LIST OF ITEMS")
- **Grammar:** furniture · a **second header row** `P.RATE | S.RATE | M.R.P.` · `ITEM_NO_NAME` (serial 1, company "OTHER PRODUCTS") · `ITEM` — `2     ACILOC 300 | 1*20 | CADILA`. The company is cut across two cells (`ZYDUS | HEALTHCARE`).
- **Witness:** one serial run 1 … N with no gap, and N equals the item rows.
- **Carries:** name, packing, **company**. **The rate columns are announced and never filled** — 2 stray figures in 379 rows, under the company column; they are not rates.
- **Clip:** 29.
- **Held:** 3 files, **newest 28-Aug — stale.** All 3 pass.
- **Deliberate failure:** one item removed → serial gap and count mismatch.
- **Verdict: CERTIFIED.** Trusted for: **company**, and as a second witness to the name. Not for any rate.

### 4.4 · Closing stock, totals — `STOCK_CLOSING` / `TOTALS`
- **Grammar:** furniture (the title with its date is reprinted on every page) · `ITEM` — `2.0 | ACILOC 300                    1*20 | 3:2 | STRI` · `TOTAL`.
- **Witness (new at S270):** **TOTAL = Σ (packs × pack size + loose)** over every row, where `3:2` is 3 packs and 2 loose, `-` is zero, a plain figure is taken as printed, and a pack written `1*10.` (trailing dot) is still 10. Matches Marg's total **exactly** on every September file. Plus the serial run.
- **Carries:** name, packing, stock, unit.
- **Clip:** 29.
- **Held:** 12 TOTALS files read (Aug–Sep). **All 12 pass.**
- **Deliberate failure:** one quantity `3:2` → `3:3` → total off by one; one row removed → serial.
- **Exception:** the one `DEFAULT` (batch-wise) file, 01-Jul, SCRAP STORE — its rows add to 5,112 against a printed 5,053; the reader is **not certified for that layout**. It is not a current export.
- **Verdict: CERTIFIED (TOTALS).** Trusted for: stock on hand by item.

### 4.5 · Stock valuation — `STOCK_VALUATION` (DEFAULT and STRIPS_TAB)
- **Grammar:** furniture · `ITEM` — `1 ACILOC 300                    1*20 | 3:2 | 49.288 | 152.8` · `TOTAL` (units and value).
- **Witness:** TOTAL units as 4.4; **TOTAL value = Σ row values** (to the paisa, 331,069.13); and **every row: value = packs × rate** — where a plain figure is already in packs (CCM `1*40` printed `8.0` is 8 bottles, valued 8 × 320.09).
- **Carries:** name, packing, stock, **valuation rate**, value.
- **Held:** 2 files, both 06-Sep. Both pass.
- **Deliberate failure:** one value `152.80` → `152.08` → caught by both the total and the row check.
- **Verdict: CERTIFIED.** Trusted for: stock value at Marg's valuation rate. Not for MRP.

### 4.6 · Stock expiry — `STOCK_EXPIRY`
- **Grammar:** letterhead · title `EXP. BEFORE …` · `ITEM` (serial+name+pack | batch | expiry | stock unit) · `TOTAL`.
- **Witness:** TOTAL units, as 4.4 — exact.
- **Held:** 2 files read, newest 28-Aug — **stale.** Both pass.
- **Deliberate failure:** one quantity changed → total.
- **Verdict: CERTIFIED.** Trusted for: batch, expiry, quantity to act on.

### 4.7 · Purchase, supplier/item-wise — `PURCHASE_ITEMWISE`
- **Grammar:** furniture · `SUPPLIER_HEADING` — Marg's text line **cut into one to three cells** (`DRUG | DEAL | BAREILLY`, or starting in the *second* cell) · `ITEM` · **`ITEM_GLUED`** — the bill number **fused onto the item name** in one cell (`EP000476VITANSIAL PLUS`, `T-000032RUNVACE TP`) with the first cell empty · `GROUP_TOTAL` per supplier · `GRAND TOTAL`.
  Bill numbers are not always numeric (`a000163`, `T-000032`). Packing and batch share a cell in some rows (`1*10    HT122559`); batch and expiry share one in others (`HT07266712/27`).
- **Witness:** **every supplier's TOTAL re-adds its own lines**, and GRAND TOTAL re-adds every line, on both the NET and the AMOUNT columns.
  Line law, measured: **AMOUNT = (QTY + FREE) × PURC.** — holds on 1,643 of 1,645 lines across both purchase item reports; RATE is *not* the rate AMOUNT is priced at.
- **Carries:** bill, name, packing, batch, expiry, tax, qty, free, rate, supplier discount, net amount, net rate, **PURC. rate**, amount. **No MRP.**
- **Clip:** **27** (4 names clipped in September, e.g. `TYNOR WRIST SPLINT LF L ELA`). The name must be joined to the 29-character authority.
- **Held:** 13 files. **10 pass their witness as written; 3 do not until purchase returns are read** — April, May and July. **Corrected 19-Sep (S270 roll-forward):** the lines that exceed the supplier's total are **purchase returns**. The item-wise report prints a return bill's lines exactly like a purchase (positive quantity); only the **bill-wise** report shows the bill as **negative**. There are five: L.K. DRUG HOUSE 435 (RIFAGUT 550) and 670 (DROTIN TAB) in April, YOGENDRA AGENCIES 121 (NUCOXIA P) in May, L.K. DRUG HOUSE 4159 (NEWTEL 40) and 5 (JARDIANCE 25) in July. Read as returns, every supplier total re-adds, and every one of those five items rolls forward to Marg's closing stock exactly. **So a reader of this report must take the direction of each bill from the bill-wise report.**
- **Deliberate failure:** one AMOUNT altered → supplier total and grand total; one line removed → grand totals.
- **Consequence for importers:** 29 lines across the archive are `ITEM_GLUED`. **Any reader that takes the first cell as the bill and the second as the name misses or misnames them** — that is how the alphanumeric-bill line was dropped in the first draft of this very reader, and the totals caught it.
- **Verdict: CERTIFIED** — read together with `PURCHASE_BILLWISE`, which gives each bill its direction (purchase or return). Read alone, a return is indistinguishable from a purchase.

### 4.8 · Purchase, bill/item-wise — `PURCHASE_BILLITEMWISE`
- **Grammar:** as 4.7, grouped by **date** (`DATE` rows) instead of supplier; `ITEM_GLUED` occurs here too (1 row); a single closing `TOTAL`.
- **Witness:** the closing TOTAL re-adds every line (NET and AMOUNT). **Weaker than 4.7 — no per-group total.**
- **Held:** 4 files, newest 06-Sep. All 4 pass.
- **Deliberate failure:** the `a000163` line removed → the closing total.
- **Verdict: CERTIFIED** — but **not needed**: it carries the same lines as 4.7 with a weaker witness. Dropped from the export list.

### 4.9 · Sale, bill-wise DETAIL — `SALE_BILLWISE` / `DETAIL` (the books)
- **Grammar:** furniture · `DATE` · `BILL` (a patient row — never quoted here) · `ITEM` — `1   7 BIO D3 MAX           1*15 | 0:5 | 442.40  2/29 | 18260991A`: line number, a second figure (not an item code, D188; printed `***` when it overflows), a **20-character name field**, the **pack**, qty `packs:loose`, the per-pack rate with expiry, batch · `C/F` carry rows · `DAY TOTAL` · the footer `Total No. of Bills … GRAND TOTAL`.
- **Witness:** GRAND TOTAL = Σ bill gross; footer bill count = bills read; line numbers run 1 … n in every bill; and **new at S270: every bill's GROSS = Σ (rate × units ÷ pack) of its own lines** — a credit note prints its lines positive and its gross negative. **22 files, 600 bills, 2,806 lines: every bill re-adds.** The pack is printed on every one of the 2,806 lines.
- **Carries:** name (clipped), pack, qty, rate (= MRP per pack), expiry, batch; per bill: gross, discount, net, cash.
- **Clip:** **20** (11 names clipped in September, e.g. `ANKLE BINDER BAMBOO`, `DISPO SYRINGE NIPRO`).
- **Deliberate failure:** one rate altered → that bill's gross; one line removed → line numbers and gross; one bill removed → grand total and bill count.
- **A gap in the live check, stated:** the router's `deep_verify: marg_report` checks bills → day → grand total, but **not lines → bill**. The line witness above exists only in this harness. Adding it to `marg_report.py` is a kit, named for the next step.
- **Verdict: CERTIFIED.** Trusted for: what was sold, at what printed rate, per bill. The name is a 20-character key to join, not a name.

### 4.10 · Sale, daily print — `SALE_DAILY_PRINT` / `TEXT`
- **Grammar:** one text column; rules of dashes; `BILL`; `ITEM` with the pack; a lone `Page` line; `*** End of Report ***`.
- **Witness:** as 4.9.
- **Finding:** **4 of 98 lines print no rate at all** (16-Sep; e.g. `DISPO SYRINGE NIPRO  1*1   1` with the rate missing), so 4 of 24 bills cannot be re-added. The 20 complete bills re-add exactly.
- **Deliberate failure:** one quantity altered → that bill's gross.
- **Verdict: NOT A SOURCE** for lines, as its signature already says. Keep capturing (it is the printed record), never import.

### 4.11 · Stock register, one item — `STOCK_ITEM_LEDGER` / `BATCHWISE`
- **Grammar:** the whole sheet indented one column · `ITEM_HEADING` (`MEG QCS 1*15`) · `OPENING` · `OPENING_DETAIL` / `CLOSING_DETAIL` / `BATCH_DETAIL` (per-batch balances) · `DATE` · `MOVEMENT` (a patient row — never quoted) · `Received :` / `Issued :` footers.
  **Quantities are Excel times** — hours are packs, minutes are loose — and **a negative balance is printed as text** (`-2:10`).
- **Witness:** every balance = previous balance ± the row's quantity; the Received and Issued footers = the sum of their rows; and **the per-batch opening and closing details add to the opening and closing balance.**
- **Held:** 4 files. All 4 pass — after the reader learned the text-negative balance, which had broken the chain once (MEG QCS, 01-Apr…06-Sep).
- **Deliberate failure:** one movement changed by one loose unit → the balance chain and the footers.
- **Verdict: CERTIFIED.** Trusted for: one item's movement history. On demand only.

---

## 5 · THE REPORTS THAT CARRY NO ITEM NAME

| report | what it proves | status |
|---|---|---|
| `PURCHASE_BILLWISE` | bill → supplier → amount; `TOTAL` | structural; the cross-check for 4.7's three bad months |
| `PURCHASE_SUPPLIERWISE` | supplier view of the same month | structural; not needed beside 4.7 |
| `SALE_RETURN` (DEFAULT, SUMMARY) | Marg's credit-note register | structural; the credit notes are already inside 4.9 |
| `SALE_BOOK` / `AS_ON` | one old sample, June | not needed |
| `SALE_BILLWISE` / `SUMMARY1` | three columns, no cash | never export |
| **Consolidated purchase book** (Amir, 17-Sep, **refused**) | supplier → month amount; a closing line of the total and the supplier count | no signature — the router reads its title as `Operator : AMIR` and finds no header (its header row starts with an empty cell). Not needed while 4.7 and the bill-wise exist. |
| **Purchase return / debit note** | a negative bill in `PURCHASE_BILLWISE`; its lines in the item-wise reports | **held after all (corrected 19-Sep):** five return bills Apr–Jul. F-527's \"no purchase return is stored\" was a reading of the wrong report. |

---

## 6 · WHAT S270 FOUND — for the close to mint

*Numbers are minted at the close from the board and `START_HERE_SESSION_270` (next free F-539), not here.*

1. **The category list had no signature** — fixed at S270 (data edit), both copies re-filed VERIFIED.
2. **The live sale check does not check lines against bills** (4.9). The witness exists and holds on 2,806 lines; it is not installed.
3. **Purchase item-wise: bill fused to name in 29 lines; non-numeric bill numbers; supplier names cut across cells** (4.7). Any importer reading fixed cells misses or misnames them.
4. **Purchase returns exist and are printed as purchases in the item-wise report** (4.7, corrected 19-Sep): five return bills Apr–Jul. The server stores their lines as purchases.
5. **The item master's rate columns are empty** (4.3), and it is stale (28-Aug).
6. **The daily print drops the rate on some lines** (4.10).
7. **The prescribed discount is in no Marg export; S.RATE is not it** (§3).
8. **The ledger prints negative balances as text** (4.11) — a reader that expects a number breaks the chain.

**Nothing live was changed except `signatures.json` (item 1).** No table was written; no item name was touched (D549); the 06-Sep count is untouched.

---

## 7 · WHAT COMES NEXT (step 6 — not done here)

*Work from the exports, then populate.* In this order, each a kit, each touching no count table:
1. Install the reader (from `contract_harness.py`) for the salt and category lists, replacing the old salt importer that still carries `SANJEEVNI MEDICOS` as a salt for 19 items; then re-populate `purchase_salt_marg` from a certified reader.
2. Add the line → bill witness to `marg_report.py`'s deep verify.
3. Teach the purchase importer the `ITEM_GLUED` row and the non-numeric bill.
4. Teach `MARG_PICTURE` the §1 cadences.

---

## 8 · EVIDENCE

`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S270\` — `contract_harness.py` (the readers), `sweep.py` (every held file of every family), `mutate.py` (the deliberate failures), `clip.py`, `results.json`, `mutations.json`, `clip.json`. The harness prints no patient name or phone; sale and ledger rows are described by class only.

*MARG_REPORT_CONTRACT v1 · S270 · 18-Sep-2026 · supersedes MARG_REPORT_EXPECTATIONS.md §2–§3.*
