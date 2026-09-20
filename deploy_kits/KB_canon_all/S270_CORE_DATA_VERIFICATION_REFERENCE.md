# MARG CORE DATA — VERIFICATION REFERENCE (S270)

**Dated 19-Sep-2026, 05:10 IST. Session S270 (Sanjeevni project). Read-only throughout: no server table, no Marg data and no live file was changed, except one data edit on manojz (§7.1).**
*This is the sole reference for the exercise: what was checked, against what, how, what was found, what was decided, and what the new spine must hold before every screen reads it. Re-run instructions are in §9.*

---

## 1 · THE RESULT IN ONE PARAGRAPH

Every Marg sale, purchase and stock export held from **01-Apr-2026 to 17-Sep-2026** was read by self-checking readers.
- **The exports themselves are complete.** Sale bills run unbroken A000001–A003676 and CN00001–CN00216; the four numbers missing from that series are bills cancelled inside Marg. Every purchase bill agrees with its lines once returns are read as returns.
- **The server copied them almost perfectly.** It lacks 72 sale bills, holds 8 sale lines misread, and stores 5 purchase returns as purchases. The rest is exact.
- **The stock roll-forward proves the whole.** Marg's 31-Mar closing stock, plus purchases, minus returns to suppliers, minus sales, plus sale returns, equals Marg's 17-Sep closing stock **exactly on 324 of 358 items**. 5 more are explained by the owner. **29 remain as true, unexplained differences**, worth about Rs 5,400 more and Rs 6,400 less than the transactions explain, at MRP. **By the owner's decision these are reconciled in the spine, not in Marg.**

---

## 2 · INPUTS — every file, with its md5

The full list (117 files: path, md5, bytes) is `S270_INPUT_MANIFEST.csv` (§10). The principal ones:

| input | where (manojz) | covers |
|---|---|---|
| server database copy | `D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz` md5 `9c3ac1da…` | server state at 19-Sep 01:40 IST |
| server code copy | `D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz` md5 `eb28f89c…` | code at 19-Sep 01:35 IST |
| opening stock | `MargArchive\STOCK_CLOSING\2026-03\…__7b9331f0.XLS` | Marg closing 31-Mar-2026 (exported from the previous financial year) |
| sale back-fill, 9 files | `D:\Downloads\MARG REPORTS CLAUDE\` (April 1–15 … August 14–15) | 01-Apr … 15-Aug |
| sale daily, 38 files | `MargArchive\SALE_BILLWISE\` | 12-Jun, 17-Aug … 17-Sep |
| purchase item-wise, 13 + bill/item-wise, 4 | `MargArchive\PURCHASE_ITEMWISE\`, `…BILLITEMWISE\` | Apr … 17-Sep |
| purchase bill-wise, 7 | `MargArchive\PURCHASE_BILLWISE\` | Apr … 17-Sep |
| closing stock, 13 | `MargArchive\STOCK_CLOSING\` | 26-Aug … 17-Sep |
| salt list · item list · category list | `MargArchive\SALT_WISE_ITEM_LIST\…fe0642b7` · `ITEM_MASTER\…0bf059f3` · `CATEGORY_WISE_ITEM_LIST\…f4a3406e` | as on 18-Sep |
| the owner's discount register | project doc `S235_ORTHOTIC_DISCOUNT_REGISTER_SETTLED.md` | 09-Sep rulings |

---

## 3 · METHOD

**3.1 · Read every report with a reader that can fail** (`MARG_REPORT_CONTRACT_v1.md`). Each row is classified positively. Each report is checked by its own witness: serial restart, printed totals, bill = Σ lines, footer bill count, balance chain. Each reader was broken on purpose at least once and caught the break (`mutations.json`).

**3.2 · Completeness of the exports:**
- Marg's bill numbering is one series, so a gap means a bill that was never printed.
- Each purchase bill's lines are held against the bill-wise amount for that bill.

**3.3 · Server against exports, row by row:** `sale_bill`, `sale_line_item`, `mi_sale_line`, `purchase_bill`, `purchase_line`, `stock_snapshot`, `stock_count_item`, `purchase_salt_marg`, `marg_item*`, `marg_item_discount`.

**3.4 · Stock roll-forward**, per item: **closing(17-Sep) = closing(31-Mar) + purchases − purchase returns − sales + sale returns.** Four rules make it fair:
1. **Purchase returns** are the bill-wise report's negative bills; their lines appear in the item-wise report as ordinary purchases.
2. **Renamed items** are joined through the spine's name table, plus six old spellings it does not know yet (THI OQ AP → THIO Q AP; VINTAZ P 4500 → VINTAZ P 4500 INJ; LEUKOCRAPE 6/8/10/15*4 → LEUKOCREPE …).
3. **Units:** strips and tablets, a strip holding the tablets its Marg packing says (1*10 = 10). The **96 items Marg keeps in whole packs** (tubes, vials, bottles such as CCM, orthotics — any item whose closing stock prints a plain number) are counted in packs everywhere.
4. **Names the sale report cuts to the same 20 characters** (the two knee immobilisers) are counted as one family.

**3.5 · Dating the differences:** the roll-forward is repeated at 27-Aug, 02-Sep, 06-Sep, 11-Sep and 17-Sep. A difference that is the same on every date happened before 27-Aug. The 02-Sep closing was exported at 17:22 mid-day, so it is not a fair date.

---

## 4 · WHAT IS VERIFIED CORRECT

| what | result |
|---|---|
| every export re-read (70 files in the archive + 9 back-fill) | all pass their witness except 5 files, each known (§5 item 12) |
| sale bills in the exports | 3,888; numbering complete apart from 4 cancelled numbers (A001339 · A001468 · A003478 · CN00203) |
| `sale_bill` (Marg bill totals on the server) | 752 of 752 exact (12-Jun and 17-Aug onwards; earlier months are not stored as Marg bills, §5 item 2) |
| `sale_line_item` | 19,110 lines on the server; 19,102 exact, 8 differ (§5 items 3–4) |
| `purchase_bill` | 509 bills, every amount exact |
| `purchase_line` | every line of every export present and exact, except the 5 returns and 1 dropped line (§5 items 5, 9) |
| `stock_snapshot` | exact against 11 closing exports, except LACTOVAX SYP on 4 dates (§5 item 7) |
| 06-Sep count baseline (`stock_count_item.marg_qty`) | 373 of 373 exact |
| discount rulings (`marg_item_discount`) | 60 of 60 checked equal the owner's register |
| pack sizes | 373 of 373 exact |
| item names | the salt list and the item list agree exactly (373); the server holds 373 of them, plus 1 stale |
| **stock roll-forward 31-Mar → 17-Sep** | **324 of 358 exact · 5 explained by the owner · 29 to reconcile** |

---

## 5 · THE FAULTS — the complete list at this date

*"Server" means our data; "Marg" means the source itself. Numbers are minted at the S270 close.*

| # | fault | where | size | repair |
|---|---|---|---|---|
| 1 | **21 items carry the salt "SANJEEVNI MEDICOS"**; renewed on every salt refresh | server `purchase_salt_marg`, `marg_item_fact` | 21 items | new salt reader (certified) in the spine |
| 2 | Marg bill totals for 01-Apr … 16-Aug are not stored as Marg bills | server | 3,136 bills | spine holds all 3,888 bills from the exports |
| 3 | **72 sale bills missing**: every bill of 04-May (35) and 27-May (36), plus A000425 of 19-Apr; the May back-fill created no day for those two dates | server | 397 lines, Rs 69,153.69 gross | load from the back-fill files already held |
| 4 | 8 sale lines misread: 7 where Marg prints `***` in the stock column, 1 carrying an old name (PARI 12.5) | server | 8 lines | certified sale reader |
| 5 | **5 purchase returns stored as purchases**: 435 RIFAGUT 550 · 670 DROTIN TAB · 121 NUCOXIA P · 4159 NEWTEL 40 · 5 JARDIANCE 25 (L.K. DRUG HOUSE, YOGENDRA AGENCIES) | server `purchase_line` | 28 strips, both ways | direction from the bill-wise report |
| 6 | "MRP" fact is the median sold-at price, not Marg's MRP: 39 wrong, 3 absurd, 171 missing | server `marg_item_fact`, `stock_app._mrp_p` | 210 items | MRP from the salt list |
| 7 | items keyed by name, but Marg has two DOLOGESIC SP (and had two LACTOVAX SYP until 05-Sep) | server | 2 items | spine key = name + packing |
| 8 | 172 sale bills loaded twice into the shadow table | server `mi_sale_line` | 172 bills | ignore or de-duplicate by latest export |
| 9 | the glued-bill line EP001731 MOTIF FORTE dropped from the August bill/item-wise set | server | 20 strips | certified purchase reader |
| 10 | 4 clipped purchase names taken for new items; one clipped name sits in `stock_rate` | server | 4 names | join clipped names to the 29-character name |
| 11 | purchase bill numbers lose leading zeros (`045754`, `004625`) | server | 4 lines | keep bill numbers as text |
| 12 | Marg's own inconsistencies: 10 sale bills whose lines do not add to the bill (5 May, 4 Jul, 1 Jun); the 16-Sep daily print drops rates; the July batch-wise closing's total | **Marg** | 10 bills | recorded; bill totals are taken as Marg prints them |
| 13 | **Marg shows negative stock on 17-Sep**: ALCOXIB 120 -13, BELL CAST 5 -14, CERVICAL COLLAR SOFT -1, FLUPIVAMP 100 -10, GLI-ME SR1 -7, NEWTEL 40 -40, PRIME CAST 4" -24, PRIME CAST 5" -45, PRIME PAD 4" -12, PRIME PAD 6" -23, TRAMEF P -20 | **Marg** | 11 items | carried as Marg shows it; to reconcile in Marg |
| 14 | **16 purchase bill numbers are used by more than one supplier**: 5, 33, 35, 80, 83, 91, 94, 126, 145, 148, 160, 182, 199, 252, 454, 1450 | **Marg** (by nature) | 16 numbers | spine key for a purchase bill = supplier + number + date |
| 15 | 6 sale names cut to 20 characters match several items (KNEE SUPPORT HINGED, L S BELT CONT GRAY U, KNEE IMMOBILIZER UNI, TYNOR WRIST SPLINT L, SHOULDER IMMOBILISE, ANKLE BINDER BAMBOO) | **Marg** report width | 67 lines, Rs 79,970 | counted by family; the S268 renames cure it after the count (D549) |
| 16 | three discount-register MRPs are stale (DISPO SYRINGE NIPRO 3ML · TYNOR WRIST SPLINT LF L / RT L ELAST) | server | 3 items | MRP from the salt list |
| 17 | VINTAZ P 4500 still active; bill 502 held twice (MANNAT / DEEPAM); numeric batches stored with `.0` | server | minor | spine build |
| 18 | **29 items whose stock moved without a sale or purchase** (§6) | **Marg** vouchers not in any export | about Rs 5,400 more / Rs 6,400 less | **reconciliation entries in the spine** (owner's decision, §7) |

---

## 6 · THE RECONCILIATION LIST — true differences, 31-Mar → 17-Sep

**Explained by the owner (no action):**
- ETOZOX 90, 47 strips more — added by the owner (S264).
- DOLOGESIC SP, 28 strips more — added by the owner (S264).
- ALGESIA CR 5 tabs · EFONOX TH 4 tabs · TOFZA TAB 4 tabs less — the June expiry removals done by hand (ruling R6, 28-Aug).

**Marg holds MORE than its transactions explain (reconcile):**

| item | difference | at MRP, Rs |
|---|---|---|
| GEMCAL 500MG | 3 strips + 7 tabs | 1,300 |
| OPTIFENAC TBR | 2 strips + 1 tab | 441 |
| PANTOCID L CAP | 2 strips + 1 tab | 525 |
| ENZOMAC OINTMENT | 18 | 2,080 |
| PANTAVIN 40 | 1 strip | 80 |
| PARI CR 12.5 | 10 tabs | 237 |
| CROCAL | 9 tabs | 51 |
| HCQS 200 | 8 tabs | 57 |
| ZIVOPREG M | 8 tabs | 101 |
| FLUPIVAMP 100 | 7 tabs | 111 |
| XYCAL K2 | 7 tabs | 154 |
| TYCOB 1500 | 3 | 211 |
| DEPOPRED 2 ML | 1 | 85 |

**Marg holds LESS than its transactions explain (reconcile):**

| item | difference | at MRP, Rs |
|---|---|---|
| INTACOXIA-60 | 26 strips + 10 tabs | 2,160 |
| FEBUWISE 40 | 4 strips | 516 |
| PANTOCID DSR | 1 strip + 6 tabs | 353 |
| PANUM L | 2 strips + 1 tab | 235 |
| BIO D3 MAX | 1 strip + 5 tabs | 590 |
| FEBUTAL | 2 strips | 220 |
| TYCOB FORTE | 1 strip | 155 |
| RUNVACE TP | 6 tabs | 114 |
| TFCT-NIB | 4 tabs | 193 |
| ANTEGY M | 3 tabs | 52 |
| CARTILOX-GO CAPS | 2 tabs | 130 |
| POWERGESIC 100 PATCH | 2 | 342 |
| CCM | 1 | 562 |
| LEUKOCREPE 15CM*6INC | 1 | 615 |
| NEUGABA M | 1 tab | 20 |
| SHIGRU 60 | 1 | 180 |

All are present unchanged at 27-Aug, 06-Sep, 11-Sep and 17-Sep, so each happened between 01-Apr and 27-Aug.

---

## 7 · DECISIONS AND RULINGS OF THIS EXERCISE (18–19 Sep 2026)

1. **Category list signature added** to `D:\Downloads\margsync\MargPull\signatures.json` (backup `signatures.json.bak_S270_b2dcb211`). Both 18-Sep copies re-filed VERIFIED at the 14:21 IST rescan. The only change made to a running system.
2. **Who exports what** (owner, 18-Sep 20:35):
   - Shavez: sale DETAIL and closing stock every morning, plus valuation and expiry on the 1st.
   - Amir: the purchase pair.
   - The owner: the salt list every Monday, and the category list and item list every month.
   Shavez's tile is planned (`SHAVEZ_MORNING_TILE_PLAN.md`), not built.
3. **The prescribed discount is in no Marg export;** the owner's register is the authority.
4. **Units are strips and tablets** (owner, 19-Sep).
5. **ETOZOX 90 and DOLOGESIC SP were the owner's additions** (owner, 19-Sep, restating S264).
6. **Marg is not changed to match the server.** The spine takes Marg as the book of record:
   - it opens at Marg's 31-Mar closing;
   - it applies every export;
   - it books **one dated reconciliation entry per §6 item**, so it equals Marg's closing stock on every date.
   A difference that appears after this is a new, dated finding. (Owner: "whatever you deem best", 19-Sep.)
7. **F-527 corrected:** purchase returns are held in the exports (negative bill-wise bills). Contract §4.7 corrected likewise.

---

## 8 · THE GATE — what the new spine must hold before any screen reads it

A spine build passes only when, re-run against the same inputs:
1. It holds all **3,888** sale bills with Marg's totals, and every line of each, with **each bill's lines re-adding to its gross** (except the 10 Marg-side bills, which are carried and flagged).
2. It holds all **509** purchase bills with their direction (purchase or return), keyed by supplier + number + date, and every line, with lines re-adding to each bill.
3. Every item is keyed by name + packing (two DOLOGESIC SP), carrying:
   - name, salt, packing and MRP from the salt list;
   - category from the category list;
   - company from the item list;
   - the old spellings as names of the same item.
4. **Its computed stock equals Marg's closing stock on 358 of 358 items on every closing date held**, 27-Aug … 17-Sep. The §6 reconciliation entries and the owner-explained items are included, and the negative Marg stocks are carried as Marg shows them.
5. The 06-Sep count baseline is untouched (373 of 373).

---

## 9 · HOW TO RE-RUN THIS (for a future session)

1. Stage the inputs listed in `S270_INPUT_MANIFEST.csv` from manojz, or newer copies of the same files.
2. Unpack the database copy as `f.db`.
3. In one folder, place `contract_harness.py` (the readers), `dump.py`, `auth.py`, `sale.py`, `union.py`, `roll.py`, `sweep.py` and `verify_all.py`.
4. Run `python verify_all.py`. It writes `verify_all.json` with every figure in §4–§6.
5. The deliberate failures are re-run with `mutate.py`; the clip widths with `clip.py`.

---

## 10 · REFERENCES

**Working papers** — `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S270\`:
- `MARG_REPORT_CONTRACT_v1.md` — the readers, the witnesses, the field authorities.
- `MARG_EXPORT_LIST.md` — who exports what, how often.
- `S270_MARG_DATA_AUDIT.md` — the first audit and the confirmation (§A–§G).
- `S270_THE_33_ITEMS.md` — the list given to the owner, and his answers.
- `SHAVEZ_MORNING_TILE_PLAN.md` — plan only.
- **This document** — `S270_CORE_DATA_VERIFICATION_REFERENCE.md`.

**Evidence** — `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S270\evidence\`:
- `S270_INPUT_MANIFEST.csv`
- `contract_harness.py`, `mutate.py`, `clip.py`, `results.json`, `mutations.json`, `clip.json`
- `audit\` — `verify_all.py`, `verify_all.json`, `roll.py`, `union.py`, `sale.py`, `auth.py`, `sl.py`, `sweep.py`, `contract_harness_final.py`

**Project knowledge:** the same documents under `claude/`.

**Earlier rulings drawn on:** S207 (R6 expiry by hand) · S235 (discount register) · S240 (Amir's day, D470) · S264 (owner's parked additions) · S268 (renames, D549; salt-reader standing rule).

*S270_CORE_DATA_VERIFICATION_REFERENCE · 19-Sep-2026 · supersedes nothing; the audit and the 33-item list remain as the working record behind it.*
