# S438 — THE MARG WATCH, plan v4: Kit 1 (bills changed after their day) built and live; what the build found; the owner's rulings to 12-Nov evening
*The Sanjeevni chat · session 438 · 12-Nov-2026 (night) · **Kit 1 — section B — is LIVE: `S803_MARG_WATCH_BILLS`** · supersedes `S434_MARG_WATCH_PLAN_v3.md` · v4 = v3 whole (md5 c569114e; only its H1, this line and its footer replaced, v3's line retained below), with §0B added; **where §0B differs from §0A or a later section, §0B wins; where §0A and a later section differ, §0A wins** · the live page: `https://followup.dr-manoj.in/finance/sanjeevni/marg-watch`*

*(v3's line, retained:)* *The Sanjeevni chat · session 434 · 12-Nov-2026 · nothing of the watch built · supersedes `S432_MARG_WATCH_PLAN.md` (v1) and the working paper v2 · v3 = v2 whole, with §0A added; **where §0A and a later section differ, §0A wins** · the mock: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S434\screen\marg_watch_MOCK_v5.html`*

**What this paper is.** The owner's word (D918): review, analyse and refine the plan before anything is built. v1 was read whole; every "as found" line was checked against the 11-Nov code bundle and the 11-Nov database copy (in the device VM only); §12's open points are settled here. §1 (his words) is carried unchanged — nothing below contradicts it.

---

## 0 · What the review changed — ten findings **[v2, all of it]**

| # | found | proof | effect |
|---|---|---|---|
| R1 | **A and B are one story, not two sections side by side. A bill changed after the day (B) is the record behind many of A's "no record" moves.** | (a) Sale bill **A004591** (03-Nov, ₹1,760 cash) is in the 04-Nov export and gone from the 05-Nov re-export. Its six lines — BIO D3 MAX 10, TOLIVANT PLUS 30, AURAB L CAP 10, FLEMCORT 6 5, JAKMAC 5 20, TRAMAVIN GEL 1 — are exactly A's five "new" rises of 4–5 Nov (+10, +30, +10, +5, +20) and the odd +1 in TRAMAVIN's −11 / +12. (b) Purchase bill **Yogendra 19612** (16-Oct): DOLONEX 2 ML INJ 70 + 7 free in every export to 29-Oct, **63 + 7** in the 10-Nov export = A's DOLONEX −7 of 6–8 Nov. (c) Purchase bill **Deepam A000678** (15-Oct): the line was on THIO Q AP TAB to 29-Oct, on **THIO Q AP** on 10-Nov = A's −12 strips / +120 tablets of 2–4 Nov. | Section A's true count is **13 moves, +₹5,458 / −₹4,020, net +₹1,438** (v1: 18, +₹6,611, net +₹2,591). B is fed to A's engine as records; B is built **with** A (Kit 1), not after it. §5, §6, §10 |
| R2 | **The wrong explanation lines (F-1270) have two causes.** | `why_of` prints Marg before → after, "the system moved" and the shift, but not the part the engine paid from an earlier bill it was holding (OWED): THIO Q AP 28 → 268 is +240, of which 120 was bill 748 held as owed; the line shows only "nothing" and "+120". And the owner's 5-Nov table (`NOTES`) is keyed by item name alone, so the one CCM note prints on all three CCM rows. | The row stores what was paid from a held bill and prints it; notes are keyed by item **and** day. §5 |
| R3 | **The door's gap is small and exact.** | `marg_router.verify()` has no store rule; `STOCK_CLOSING` and `STOCK_VALUATION` signatures take any store's title (the store is in the title of all three reports: "`<STORE> CLOSING STOCK AS ON`", "`<STORE> STOCK VALUATION AS ON`"). `BATCH_STOCK`'s signature already demands WHOLE STORES. The staff tile already shows a refused file with the door's reason (`reports_tile._s500_stock_file`, `hindi_reason`). | One rule in `verify()`, one Hindi line. §4 |
| R4 | **B, built plainly, would drown him.** A plain export-against-export compare of September–November purchases gives **237 differences; 25 are real.** | Run on the server's own line tables (read only). The noise: one **part export** of September (about 90 bills "gone", then "new" again); bills **keyed after the export was taken** (dated the export's own day); **paise rounding** between exports (JAKMAC 5,185.80 ↔ 5,186.70); **renames** inside a bill (KNEE SUPPORT HINGED L → KNEE SUPPORT L HINGED); a bill number's **letter case** (a000163 → A000163). | Five named noise rules, each with a control. §6.4 |
| R5 | **Ask needs no new card on either staff page.** | Amir's page already has his one-time-jobs card with a tap and "seen in Marg" (`amir_job`, S494); Darpan's page already has the claims list he answers, under the rule "his answer is evidence; your tap decides" (S312, `/finance/darpan/api/claims`). | *Sawaal* is one more kind in each. §8 |
| R6 | **v1's line "no patient data is involved" is not right.** | Marg's sale exports and its Stock Register carry patient names. The door already reads a sale file into name-free lines and deletes the file (S186). | B reads only the server's name-free line tables, never a raw file; any new on-need report is read name-free at the door or not taken. §1 note, §7, §11 |
| R7 | **The best on-need report for an A row already has a signature at the door: Marg's Stock Register for one item** ("STOCK REGISTER WHOLE FROM … – …"; five files in the archive since September). It lists every entry Marg holds for the item — opening, purchase, sale, sale return, issue, receive — with bill number and running balance. | `signatures.json` (`STOCK_ITEM_LEDGER`, two variants). | It replaces "a stock voucher list" as the first report a row asks for. §7 |
| R8 | **The engine trusts a purchase export by the dates it covers, not by when it was taken.** | `pur_cov` in `compute()` is built from `date_from`–`date_to`. A bill keyed in Marg the afternoon after the morning's export, with an earlier bill date, is "covered" and yet absent. | A rise is judged only when a purchase export **taken after** that closing covers it. §5 |
| R9 | **The system still counts the deleted sale bill.** | `sale_bill` for 03-Nov holds the 13 bills of the re-export **and** A004591 from the first export (₹14,936 in all). | Right for the cash day (the first total is what was handed over, D917) — but its six items stay different between Marg and the system until he decides. The B row's close carries that decision. §6.5 |
| R10 | **One row needs the live stock engine before anything is written about it:** BIO D3 MAX +150 (6–8 Nov). v1 says "bill in Marg, not yet in the system". The bill (Gunina 92592, 04-Nov, 10 strips of 15) **has been on the server since the 08-Nov export**; the engine's row still stands on 10-Nov. | `purchase_line`, export of 08-Nov 09:44. | Read on the live spine at Kit 1's start; it may be a fault of the stock engine, not a matcher. §5 |

---
## 0A · The owner's rulings of 12-Nov-2026 on the mock, and what they change **[v3]**

| # | the owner (IST) | what it changes |
|---|---|---|
| D923 | 06:30 — he closes any flagged row **himself, on the row**, with his OK and an optional reason; the two choices for a removed sale bill must be on the row | every A and B row carries a decision box: one-tap reasons, an optional line, *Close with my OK*. Ask (§8) becomes the second road. For a removed sale bill the box holds **The sale stands** / **The sale was cancelled** (§6.5) |
| D924 | 06:30 — a flagged bill is shown **as a table, like the bill**; for a changed purchase bill the **scanned bill inline** | a sale bill: its lines as first reported (item, pack, quantity, rate, amount, back in stock). A purchase bill: the line was → now, beside the paper |
| D926 | 07:12 — a changed purchase bill that **agrees with its scanned paper settles by itself**; the settled ones are **seen too, in a collapsed section** | B settles against the paper FIRST. *Settled by the scanned bill* sits at the foot of B, each row with View and Reopen. A change that does not agree with the paper (goods sent back with the delivery, no scan) is never auto-settled. His reading of the causes: mostly Amir's entry errors; occasionally a return at delivery |
| D927 | 07:24 — the drafted **Ask message has no opener** of the name and "ji"; the **live Purchase bills comparison page** is to be used | the message starts at the matter (§8.1's example loses "Amir ji,"). **The Marg watch builds no viewer of its own for purchase bills:** View opens the live panel of `https://followup.dr-manoj.in/finance/purchase/page/scans` (the scan inline, the Scan / Marg table, its verdict) with one strip above it — what the bill WAS. "Settled" reads that page's own verdict; differences keep that page's road (*Difference → Amir*) |
| D928 | 07:40 — removing a sale bill is **his own, occasional act**; no Marg login lock; he will explore a return instead of deleting | A004591 was his. A removed sale bill's row comes to **him**, not to Darpan (the mock's example is corrected at its next edit). The better road in Marg is a **sale return (credit note)** — the server already reads it, and nothing is flagged |
| D929 | 07:40 — when several items rise together with no record, **the page itself asks** for the last days' sale reports again | the first automatic use of the request list (§7): a cluster of rises on one closing → *Sale bill-wise, the last three days, again*. The runner's nightly re-take was not ruled; not planned |

**The assistant's review, said to him at 07:35 and not objected to (A-D25) — folded in:**
1. **The page checks its own inputs first.** A strip at the top: today's closing stock, sale report, purchase list, scans — complete or not. A section whose input is short says *not judged*; it raises no flag. (11-Nov: a part list hid 25 purchase bills — F-1277, repaired by S795.)
2. **Start clean.** Everything from before the page goes live opens folded (*Before this page*), with one OK for the lot. A rupee floor he names (suggested ₹100): smaller moves are listed, never told.
3. **A count answers, not a conversation.** A no-record move puts the item on Darpan's next shelf spot-check (his page already has one).
4. **"Returned at delivery"** as a one-tap reason on the purchase page's existing difference road.

**The build order, as it now stands (replaces §10's table):**

| # | kit | what |
|---|---|---|
| 1 | **B, read-only, on the live comparison panel** | the bill compare with the five noise rules and the history fill (§6) · *Settled by the scanned bill* from the page's own verdict (D926) · his close with the reasons (D923, D924) · the inputs strip · *Before this page* · the new owner page with B and the door's store rule (§4) |
| 2 | **A** | the records, the whole-sum line, ₹, the floor (§5; F-1270, F-1271, F-1278, F-1279 first) · the spot-check tie |
| 3 | **Ask** | on the cards the staff already use (§8), the message without an opener (D927) |
| 4 | **Reports on need** | the request list, the cluster rule (D929), the Stock Register's name-free reader |
| 5 | **The runner** | trial, then shadow |

---

## 0B · Kit 1 as built and live, what the build found, and the rulings of 12-Nov (evening) **[v4]**

**The state.** Kit 1 — section B, *bills changed after their day*, read-only — is **live since 19:32 IST 12-Nov-2026**: kit `S803_MARG_WATCH_BILLS`, the module `/root/finance/marg_billwatch.py`, the page `https://followup.dr-manoj.in/finance/sanjeevni/marg-watch` (the doctor only; also *Sanjeevni Hub › Go to › Purchases & dealers*). It is described as built in `SANJEEVNI_SYSTEM_BOOK_v1_62_S438.md` §15BA. **Where this section differs from §0A or from a later section, this section wins.**

| # | ruling or finding | what it changes below |
|---|---|---|
| **D935** (the owner, 09:48 IST) | A supplier's bill and Marg agree **to the exact rupee**, so that the payment equals the vendor's total. No purchase-bill change is "small"; the rupee floor is on A's stock moves only. | §6.4 rule 3 is paise only — under one rupee. §6.5's list of "small amount changes" and the mock's *OK all 11* do not exist. |
| **D936** (the owner, 12:34 IST) | The scanned bill and its details **expand in the row** on the Marg watch page; he does not leave for the Purchase bills page. | §6.2 and §0A's D927: *View* opens, in the row, the Purchase bills page's own panel (made by `provisional_s781`'s functions — still no second viewer) under one strip: what the bill was. |
| **D943** (the owner, 17:46 IST) | The floor on stock moves with no record **starts at none** — every such move is told, so that he can observe it — and is **a figure he changes on the page**. | §5 and §0A's A-D25 ("a rupee floor he names"), mock v6's ₹100: Kit 2 ships with no floor and a field for it. |
| **D944** (the assistant's call) | The phone notice of a newly changed bill **ships OFF**; he turns it on, on the page. Then only what is found after that moment is told; one bill at most once in seven days; at most six bill messages a day; a row he closed is never pushed. | §6.5's "history: on the page, never announced" stands and is widened: nothing at all is announced until he says so. |
| **D945** (the assistant's call, on D935) | A bill is judged on **what it charges** — `purchase_line.net_amount_p`. `amount_p` is Marg's own VALUE of the stock, (quantity + free) × Marg's purchase rate, which Marg re-sets on old bills: a change there alone is kind *value*, **for the record** — never counted, never told. | §6.1 (what is compared) and §6.5 (see F-1306 below). |
| **F-1306** | §6.5's eleven "small amount changes" were read from the value column. **Ten are value-only re-sets** (LOFTYPRED 68 → 77 → 77.60, TRAMATEE 82.50 → 83, PRETOL 57 → 56 …) **and Yuvika 571 is a rename.** | §6.5's table is history of a misreading; the real first run is below. |
| the sale side | A sale line's `amount_p` (in `mi_sale_line`) is Marg's **rate per pack**; a line's money is rate × (packs + loose ÷ pack size); a removed or added bill's money is `sale_bill.net_p`. A sale bill is "added after the day's report" **only against a report taken on a later day** — A008478 / CN00203 (8-Sep) of §6.5 is not a finding. | §6.1, §6.3, §6.5. |
| identity | A bill is one supplier's number **within one financial year**; letter case and spaces never make two bills (rule 5). | §6.1. |

**The five noise rules as built (§6.4, amended).** (1) A report holding under 90% of the previous report's bills for the shared dates, and at least three short, is a **part print** — set aside whole; looking forward, a list that held under a **third** of the bills it should have is no baseline for "added late", in its own words, and is still read for removed and changed bills. (2) "Added late" needs the bill dated **3 or more days** before the earlier report was taken. (3) **Paise** — under one rupee — are for the record. (4) A **renamed** item is for the record unless both names still hold stock. (5) Case and spaces in a bill number. And the sixth kind found by the build: **value** (D945).

**"Settled by the scanned bill" as built (D926, D935).** By the Purchase bills page's own judgement (`scan_register.agree` / `verified`, `provisional_s781.differences`), read and never copied — and only when the paper agrees with Marg **to the rupee** AND the paper can tell the old entry from the new (the money moved by a rupee or more, the bill came late, or the date now agrees). Otherwise: *Marg differs from the paper*, *Marg agrees — yours to close*, *no scanned paper*, or *not judged* while the scans are unread.

**The first run on the live server (12-Nov 19:3x IST — all of it under *Before this page*, never announced).** New 0 · Before this page **14** (9 with no paper) · Settled by the scanned bill **5** · For the record **24** entries (purchase rate re-set 16 · renamed 6 · paise 2) · part lists set aside 2 (05-Oct; 11-Nov).
- **Money changed:** Essential EP003039 (Nov — VITANSIAL PLUS 20 → 10, −₹1,207.40; Marg differs from the paper) · Kedar A000211 (Oct — FLEMCORT 6, GST 5% → 0%, −₹110; differs) · Kedar 234 (the same change; on the live server its paper ₹20,570 = Marg — settled) · Kedar 195 (LOFTYPRED's rate 68 → 77, +₹243 — settled by its paper on the proof copy) · L.K. Drug House 67025 (Aug, +₹39.21, no paper) · Gunina 62695 and 60493 (Aug — free goods removed, no paper).
- **Item changed:** Deepam A000678 (Oct — the line moved from THIO Q AP TAB to THIO Q AP; open).
- **Added late, no paper (Sep):** L.K. Drug House 89411, 6708, 82195, 6115, 5851; Kedar 194.
- **Sale side:** A004591 (3-Nov, ₹1,760) removed after its day — his to decide (the sale stands / it was cancelled); A003396 (Sep) added after the day's report.

**What Kit 1 does NOT hold — and the build order now (§10, amended).**
1. **The door's store rule (§4)** — split off; **the next kit**, on the server's and manojz's `marg_router.py` and the staff tile's Hindi line.
2. **A small kit:** five cosmetic things on the page, and the link on his command console (`owner_console.py` is the parent's — a PLANNED line first).
3. **Kit 2 — section A (§5):** stock moved with no record; **no floor to start (D943)**; F-1270, F-1271, F-1278, F-1279 first; the spot-check tie; a removed sale bill's recorded decision acts on the stock here.
4. **Kit 3 — Ask (§8):** until then *Not OK* marks a row and keeps it open; it sends nothing.
5. **Kit 4 — reports on need (§7, D929)** · **the runner (§9).**

---

## 1 · What the owner asked, and what he ruled (11-Nov-2026, in his words where they matter)

| time (IST) | the owner | effect on the plan |
|---|---|---|
| 14:46 | "Yes, add this feature in the next build": refuse a **MAIN STORE** stock export on arrival — only WHOLE STORES is filed | §4 |
| 14:46 | the section *"Stock changed in Marg without a bill or voucher"* to be a **table**, period-wise, with added / subtracted totals | §5 |
| 15:03 | the section is for **UNEXPLAINED** moves only — no sale, purchase, stock-issue or stock-receive voucher. Anything with a record, even a wrong one, goes to *"Explained after all"*, not counted. Each period expands to its own moves table; "Each move" kept separately, without notes | §5 (mock v2 shape, approved) |
| 18:04 | monitor later modifications of sales, purchase bills, stock vouchers; suggest a simple system | §6 |
| 18:12 | minimum new manual exports; an AutoHotkey-style runner on the medical PC with the reports-only login, set up **without him touching the PC** (through the agent's Drive kit) | §9 |
| 20:20 | "manual is okay till AutoHotkey is set up" | then refined at 21:09 → |
| **21:09** | **no fixed weekly cadence.** Constant monitoring with the **existing** reports; a report is made **as per need** — the need is flagged, then he, Shavez or AutoHotkey makes it | §6, §7 |
| **21:12** | **money-only changes to sale bills (rate, discount, cash → UPI) carry no weight**: the day's sale report is printed and submitted, cash handed over against it the same evening, UPI matched to the POS totals and confirmed next morning by the MPR and bank SMS | §6.3 — not watched; one free safety net only |
| **21:15** | from the watch page, **send the needed finding** to the right person — a **copy block / WhatsApp** (Amir, Darpan, anyone), **and** the same item in **their own app** in the relevant place; **their answer comes back here** or where recommended | §8 |
| 21:18 | a detailed final plan, to be reviewed in the next session | this paper |

**Standing rules that bind every part:** owner pages in English, staff screens in Hindi · nothing live rebuilt without his OK; the manual path stays · a mock first for every screen, his word before every kit · no technical choice put to him · no patient data anywhere in this (none is involved: items, bills, suppliers only) · no phone number stored in the repository.

**[v2] One correction to the standing line above.** "No patient data is involved" is true of what the pages show (items, bills, suppliers) but not of every Marg file: sale exports and the Stock Register carry patient names. The rule for this build: **the watch reads only the server's name-free line tables; a raw sale-family file is never opened by it, and no new report is taken unless the door can read it name-free** (R6).

---

## 2 · The whole flow on one page **[v2: B feeds A]**

```
 MARG (medical PC)
   │  daily reports   : staff on the reports login, from the flows page  ── LATER: the runner (AutoHotkey)
   │  on-need reports : asked by a flagged row (§7) — the owner, Shavez  ── LATER: the runner reads the same request list
   ▼
 THE WATCHER on the medical PC captures every saved file → Drive → server            (live, unchanged)
   ▼
 THE DOOR — every file checked on arrival
   · stock files: WHOLE STORES only — any other single store is REFUSED, the reason said   (§4, one new rule)
   · dates, period, layout, name-free reading of sale-family files                         (live)
   ▼
 B · CHANGED AFTER THE DAY — the same bill seen in two exports of the same period          (§6, new)
   │      a bill gone · added late · a line's item, quantity or free changed · re-dated
   │      each finding is ALSO handed to A as a record  ───────────────┐
   ▼                                                                    ▼
 A · STOCK MOVED WITH NO RECORD — daily closings against sales, bills, vouchers AND B's findings   (§5)
          counted only when nothing at all stands behind the move
   ▼
 THE MARG WATCH — one owner page:  B's findings with their stock effect  ·  A's moves with no record
          each row: Open → Asked → Answered → Closed (only he closes)
   ▼
 ASK (§8) — a Hindi message (copy block + WhatsApp) AND one more line on the card Amir or Darpan already uses;
            their one-tap answer returns to the row; he is told by the existing owner notice
```

---
## 3 · The reports — final table (no new fixed-cadence export)

| report | when | made by now | later | feeds |
|---|---|---|---|---|
| Closing stock, WHOLE STORES | daily | staff, reports login (flows page) | runner | A |
| Sale bill-wise (detail) | daily | staff, reports login | runner | A, the cash day (live) |
| Purchase bill-wise + item-wise, month to date | on each of Amir's visits (as today) | Amir | Amir stays; runner may add | A (purchases), **B (free)** |
| Batch Stock (whole), Valuation (Pur. Rate, whole) | 1st – 7th of the month | Amir / Shavez (as today) | runner | expiry, value |
| Salt · Item · Category lists | as today | staff | runner | item facts |
| **Any report a flagged row asks for** (a sale day again, a stock voucher list for given dates, a purchase period) | **on need only** | **the owner or Shavez** | **runner** | A, B |
| Marg User Audit Trail (Daily Reports → Audit Trail → User Audit Trail) | **on need only**, when he wants to know *who* | owner or Shavez | runner, if the reports login may open it | the "who" note |

**Dropped from the S429 plan (owner, 21:09):** the weekly (Monday) and 1st-of-month look-back exports of sale bill-wise, purchase bill-wise and stock voucher list. The monthly sale bill-wise on the 1st was also considered and dropped (owner, 21:12).

**[v2]** One row of the table above changes: the report a flagged **stock** row asks for is first **Marg's Stock Register for that one item and those dates** (R7), not a stock voucher list.

---

## 4 · The door: any single store other than WHOLE STORES is refused on arrival **[v2: the gap, exactly]**

**As found — v1's lines confirmed, with three more:**
- The one door on the server is `marg_ingest/marg_take.py`, which calls the vendored `marg_router.py` (the same file runs on manojz for the archive). `verify()` checks dates, layout and completeness; **it has no store rule**. A refused file already goes to `_REFUSED` with a `.txt` reason and an index row; the staff tile already shows a refused closing stock with that reason in Hindi (`reports_tile._s500_stock_file` → `hindi_reason`, fix card `stock25`).
- The store is in the title row of all three stock reports. `BATCH_STOCK`'s signature already requires "WHOLE STORES"; `STOCK_CLOSING` and `STOCK_VALUATION` take any store.
- The archive's file names do not carry the store (a main-store closing is filed as `STOCK_CLOSING_TOTALS__…` like a whole one) — which is why only the title can decide, and why this belongs at the door and not in each reader.
- Every reader that matters already picks WHOLE STORES for itself (`push_expected`, `push_snapshot`, the spine's `marg_read`, `expiry_watch`). So nothing has been miscounted; the gap is that a wrong file is **filed as good**.

**The kit (small):**
1. `marg_router.verify()`: for `STOCK_CLOSING`, `BATCH_STOCK`, `STOCK_VALUATION` — a title naming one store that is not WHOLE STORES → REFUSED, reason "`<STORE>` only — the WHOLE STORES report is needed". The multi-store layout (title lists WHOLE among several, S206) passes as today. The same file is placed on the server and on manojz in one kit (one judgement, two copies).
2. `reports_tile.hindi_reason`: one line — *"Yeh sirf <STORE> ki report hai. Select Store mein WHOLE chuniye, phir dobara nikaaliye."*
3. No new owner notice: a refused file never counts as arrived, so the existing "not in yet" lines (the morning pair, `valuation_due`, Amir's three) already speak if the whole one does not follow. To be **proven in the walk**, not assumed.
4. The four old main-store files of September–October stay where they are (history; no reader takes them). Nothing is re-filed.

**Controls:** a MAIN STORE closing, a DTH valuation and a SCRAP batch stock are each refused; a WHOLE STORES file of each type and the multi-store closing pass; the tile shows the Hindi line for the refused closing.

---

## 5 · Section A — Stock moved with no record **[v2: B's findings are records; 13, not 18]**

**As found — confirmed:** `finance/marg_hand_change.py` (S706, 560 lines, read whole). The table holds **33 open rows of kind `hand` and 4 of kind `rename`** in the 11-Nov copy — v1's count is right, and so are Marg's before / after figures. `owner_notice.py` calls `refresh()` on its five-minute tick and sends `hand:<found at>` by Web Push; the page section is `_hand_section` in `expiry_watch.py` (line 1157).

**What the engine does today, and where it stops:**
- It already nets a purchase Marg had not caught up with (OWED), a step undone within three closings, and a rename whose two names hold the same letters.
- It knows only four kinds of record: the system's sales, purchases, purchase returns, and Amir's filed vouchers **on the same item**. It does not look at a sibling item, at a voucher of a different quantity, or at a bill that was changed after the day.
- Nothing before `hand.from_day` (16-Oct) is judged **except** items named in the owner's 5-Nov table — which is why three CCM rows of August–September and POWERGESIC of 5–7 Oct are on the page at all.

**The rule of the count (D914, unchanged):** counted only when there is no sale, purchase, issue or receive voucher behind the move. A record, even a wrong one, moves the row to *Explained after all*.

**The records the engine must learn — in the order it tries them [v2]:**

| # | the record | how it is recognised | rows of 11-Nov it settles |
|---|---|---|---|
| 1 | **A bill changed after the day (a B finding)** — a sale bill gone, a purchase line's quantity or item changed | B's finding names the item and the units; the move is the same units, in a window on or after the last export that still showed the old bill | A004591: BIO D3 MAX +10, TOLIVANT PLUS +30, AURAB L CAP +10, FLEMCORT 6 +5, JAKMAC 5 +20 · 19612: DOLONEX −7 · A000678: THIO Q AP TAB −12, THIO Q AP +120 |
| 2 | **A bill's timing** (in the system on one closing, in Marg on a later one) | the engine's own OWED rule — which works once record 1 has taken its unit out first: TRAMAVIN GEL −11 is bill 4100's −12 with A004591's +1 inside it | TRAMAVIN GEL −11, +12 |
| 3 | **A voucher on a sibling** — the same family, another size or form | a filed voucher of the same units, within three closings, on an item sharing the name's stem | CAST SHOE L −1 / M +1 · ENZOMAC OINTMENT +18, +2 (filed on ENZOMAC PLUS) |
| 4 | **A voucher of a different quantity** on the same item | a filed voucher in the window; what is left over is the row | CCM +5, −1, −1 |
| 5 | **A sale Marg did not take off** | the system holds a sale in the window; Marg did not move by it | KNEE IMMOBILIZER M TYNOR +1 |
| 6 | **Free goods counted, later corrected** — to be confirmed on the live spine | a rise equal to a bill's free quantity | DOLONEX +7 (16–18 Oct) |
| — | **Rename** (already live) | same units, opposite, same letters | ANKLE BINDER ×2, V FER 500 ×2 |

BIO D3 MAX +150 is **not** given a matcher until it is read on the live spine (R10).

**Left counted — 13 moves with nothing behind them:**

| period | item | Marg | moved | ₹ |
|---|---|---|---|---|
| 5 – 7 Oct | POWERGESIC 200 PATCH | −1 → 1 | +2 | +357 |
| 22 – 23 Oct | FLEMCORT 6 | 20 → 380 | +360 | +3,960 |
| 23 – 25 Oct | FLEMCORT 6 | 380 → 200 | −180 | −1,980 |
| 23 – 25 Oct | KNEE SUPPORT L HINGED | 4 → 2 | −2 | −1,060 |
| 23 – 25 Oct | KNEE IMMOBILIZER L UNISON | 0 → 1 | +1 | +645 |
| 23 – 25 Oct | KNEE SUPPORT M HINGED | 3 → 2 | −1 | −530 |
| 23 – 25 Oct | NORTIMER TAB | −9 → 81 | +90 | +431 |
| 23 – 25 Oct | CARTILOX SACHET | 3 → 0 | −3 | −248 |
| 23 – 25 Oct | GLI-ME SR1 | −27 → 0 | +27 | +65 |
| 23 – 25 Oct | EXLAIN A | 12 → 0 | −12 | −62 |
| 23 – 25 Oct | RUNVACE TP | 2 → 0 | −2 | −14 |
| 6 – 8 Nov | RIFAVAX 550 | 3 → 0 | −3 | −106 |
| 6 – 8 Nov | REEBORN D | 5 → 0 | −5 | −20 |

**Added +₹5,458 (5) · gone −₹4,020 (8) · net +₹1,438.** *A hint, never a record:* RIFAVAX 550 and REEBORN D were on his expiry list to be blocked in Marg (board Y142) — the row may say so; it stays counted until a voucher exists.

**Engine changes (all in `marg_hand_change.py`, additive):**
- New columns on `marg_hand_change`: `rec_kind`, `rec_ref`, `rec_note` (the record, when there is one), `owed_paid`, `rate_p`, `value_p`. `kind` and `status` keep their meaning; the UNIQUE key does not change. The page counts rows with no `rec_kind`.
- `why_of` prints the whole sum: Marg's move = the system's moves + paid from a held bill + the shift (R2). `NOTES` is keyed by (item, day).
- A rise waits for a purchase export **taken after** its closing (R8).
- ₹ = units × the item's newest purchase net rate per unit (`purchase_line`), else the month's valuation rate; **no rate → shown as "no rate", never as ₹0**, and named in the totals' footnote.
- Words kept apart: the engine's own status `explained` (the row vanished at a recompute) is shown as **"cleared by itself"**; **"Explained after all"** means only D914's class.
- The owner notice `hand:` speaks only of counted rows. A B finding has its own line (§6.5).

**The page:** mock v2's shape stands (period table → each period's moves; *Each move*; *Explained after all* at the bottom, grouped by the record). The page reads the table; it writes only the ask and close rows of §8.

**Controls for the kit:** each of the 13 stays counted; each of the 20 explained rows lands under its record; a made-up move with nothing behind it is counted; a made-up B finding with the wrong units explains nothing.

---

## 6 · Section B — Changed after the day **[v2: on the server's tables; five noise rules; feeds A]**

### 6.1 What it compares — settled (v1 §12.3)
The server keeps every export's lines, superseded or not, **name-free**: `mi_sale_line` (by the file's md5; 95 sale exports, 12 days exported twice) and `purchase_line` (by `source_md5`; 47 item-wise exports, 35 of them superseded), with each purchase export's period and stamp in `purchase_export`. **B reads these tables only** — no raw file, no archive walk.

**The identity of a bill across exports:** sale = bill number (upper-cased) + bill date; purchase = supplier (normalised) + bill number (upper-cased, spaces dropped). The **date is not part of a purchase bill's identity** — a re-dated bill is one finding, not a bill gone and a bill added.

### 6.2 What a B row says
bill date · bill number · supplier or "sale" · **what changed (was → now)** · ₹ effect · **stock effect in Marg (the A rows it explains, or "none seen")** · last export with the old bill · first export with the new · status. Period table and totals as section A.

### 6.3 What B does not count (D917, unchanged)
Money-only changes to **sale** bills. Listed "for the record", never counted, never told. **[v2]** The quarterly safety net is a single box: he types Marg's quarterly sale figure once a quarter; the page compares it with the sum of the first daily totals. No parent file is touched (v1 §12.4 settled).

### 6.4 The five noise rules **[v2 — without these B is unusable, R4]**
| # | noise | rule | control |
|---|---|---|---|
| 1 | **A part export** — one export of a period lists far fewer bills than its neighbours | an export with under 90% of the previous export's bills for the shared dates is set aside as a part print (the engine's own rule for a part closing) | September's 01-Oct → 05-Oct pair: ~90 "gone" and ~90 "new" become none |
| 2 | **Keyed after the export was taken** — a bill dated on or just before the earlier export's day | "added late" needs the bill's date to be **3 or more days before** the earlier export was taken | Gunina 92592 (04-Nov, first seen 08-Nov, earlier export 04-Nov) is not a finding; L.K. Drug House 5851 (08-Sep, first seen after 05-Oct) is |
| 3 | **Rounding** — the same quantity, free and rate; the amount differs by paise | quantity, free and rate equal and the amount within ₹1 or 0.1% → "for the record" | JAKMAC 5 5,185.80 ↔ 5,186.70 |
| 4 | **Rename** — a line gone and a line come in the same bill with the same quantity, free, rate and amount | paired as a rename; never counted **unless both names still hold stock in Marg** — then it is "the item was changed on the bill" and it is a finding (THIO Q AP TAB → THIO Q AP) | KNEE SUPPORT HINGED L → KNEE SUPPORT L HINGED is a rename; A000678 is a finding |
| 5 | **Letter case and spaces in a bill number** | normalised in the identity | Kedar a000163 = A000163 |

### 6.5 What the first run holds (history: on the page, never announced) **[v2 — real, from the tables]**
**Sales** (12 days exported twice; 3 differ):
- **A004591, 03-Nov, ₹1,760 cash — gone** between the 04-Nov and 05-Nov exports; six items back in Marg's stock. *Counted.*
- A003396, 04-Sep, ₹200 cash — **added** after the first export.
- A003478, 08-Sep, ₹1,150 cash **and** credit note CN00203, −₹1,150 — both added after the first export (they cancel).

**Purchases** (September – November, after the noise rules; the August cases of S429 stand beside them):
- Yogendra 19612 (16-Oct): DOLONEX 2 ML INJ **70 + 7 → 63 + 7**, ₹4,683 → ₹4,257. *Stock effect: −7.*
- Deepam A000678 (15-Oct): the line's **item changed**, THIO Q AP TAB → THIO Q AP. *Stock effect: −12 strips / +120 tablets.*
- Shivaaz 3290 (21-Sep): a line **added** in October — DEFVAX 6, 10 + 2 free, ₹934.
- Shivaaz 3854 (22-Oct): COCYP T SYP 10 + 2 **split** into 1 at another rate and 9 + 2.
- Six bills **added late** for September dates (first seen after 05-Oct): Kedar 194 (25-Sep, ₹2,960); L.K. Drug House 5851 (08-Sep, ₹117), 6115 and 82195 (15-Sep), 6708 and 89411 (30-Sep) — the last four are two pairs of the same two amounts (₹2,489 and ₹2,738), which he may want to look at.
- **Small amount changes, listed apart:** 11 bills whose amount changed by ₹4 to ₹38 with the same quantity and rate — Kedar 195, 162, A000209 (LOFTYPRED 80 INJ), 182 (PRETOL 8, ₹570 → ₹560) and A000203; Mannat 439 and A000408 (TRAMATEE P); Yuvika YS0706202627 (an L S belt, ₹523.80 → ₹485.72) and 571; Shivaaz SF003568 and 3463. Five more bills differ only by paise (rule 3).

**The first run in one line: 14 bills (4 sale, 10 purchase) and the 11 small amount changes — 25 real findings out of 237 raw differences.** On the mock the 14 are shown by the month of the bill.

**A deleted sale bill needs his decision, once (R9):** the row closes as **"The sale stands"** (goods left; Marg is short of a bill — Darpan re-enters it or Amir files a voucher) or **"The sale was cancelled"** (goods back, cash returned; the system drops the bill from that day's stock, the cash day stays as handed over). Until then the six items stay "explained by A004591", not counted.

**The notice:** one line per new B finding that is counted — *"Sale bill A004591 (3-Nov, ₹1,760) is gone from Marg; 6 items back in stock."*

---

## 7 · Reports on need — the request list **[v2: the Stock Register first; name-free]**

A row that cannot be settled from what has arrived says which report and which dates.
- **For a stock row:** *Stock Register — one item — the row's dates.* The door already knows the report; **its reader is new and reads it name-free** (the patient and doctor columns are dropped at the door, the file is not kept — the sale reader's own rule).
- **For a bill row:** the day's sale bill-wise again, or the month's purchase item-wise again — reports the staff already make.
- **Who changed it:** Marg's User Audit Trail, read by him in Marg; a one-line note on the row. Its reader waits for one real sample and the same name-free rule (v1 §12.6 stands).
- The list is one small table (report, item or period, the row, asked on, arrived on). Now: a Hindi copy block with the Marg path for Shavez. A request closes itself when the file arrives; the row is judged again. Later: the runner reads the same list.
- Whether the reports-only login may open the Stock Register and the Audit Trail is found by Shavez once, or at the runner's trial — not asked of the owner (v1 §12.5).

---

## 8 · Ask — on the cards the staff already use **[v2: no new card, R5]**

### 8.1 On the owner's page — as v1
**Ask** on every A and B row; who is suggested by the row (Amir: purchase bills, vouchers · Darpan: sales, counter stock · Shavez: reports); several rows in one message; Hindi text as a copy block and a WhatsApp button that opens with the text and no number.

### 8.2 In the staff's own app
| who | where | what is reused |
|---|---|---|
| Amir | his day page `https://followup.dr-manoj.in/finance/amir/day` — the **one-time jobs card** he already taps | `amir_job` (S494): one new kind, `ask`; its text, its tap, its "seen in Marg" close, and the owner's Needs-you line after the wait |
| Darpan | his page `https://followup.dr-manoj.in/finance/darpan` — the **claims list** he already answers | the claim queue (S312): one new source of lines; his answer is evidence, the owner's tap decides — already the rule there |
| Shavez | copy block / WhatsApp only | — |

Not on `/finance/darpan/corrections` (Amir's desk, S218) — v1's correction stands.

**The answers — one tap, an optional short line:** *Marg mein theek kar diya* · *Sahi hai, galti nahi* (with the reason) · *Pata nahi* · for purchase rows *Supplier ne bill badla*. **[v2]** For a sale bill gone: *Grahak ne maal wapas kiya* (the customer returned it) · *Bill galti se bana tha* (made by mistake) · *Pata nahi*.

### 8.3 Where the answer comes back — as v1
The same row: **Open → Asked → Answered → Closed**; only he closes. He is told by the owner notice. "Put right in Marg" is proven by the next morning's closing.

### 8.4 One table — and where the state lives **[v2]**
`marg_watch_ask` (one row per ask: section, row key, to whom, the Hindi text, asked at, the staff row it made, answer kind, answer line, answered at, closed at, the close's outcome). **The ask state is never written into `marg_hand_change.status`** — the engine rewrites that column at every recompute.
Unanswered after 2 days: amber on his page; the staff line stays at the top of their card.

---

## 9 · The runner (AutoHotkey) — as v1

- **Delivered without a visit** through the medical-PC agent's Drive kit (`G:\My Drive\Clinic Data Archive\ToMedical\_kit`); AutoHotkey in its no-install form. The owner types the reports-login password **once**, in a box on the PC, never in chat.
- **When:** at power-on in the SET account, before the counter switches user (a Hindi notice: *reports ban rahi hain, 5 minute*); again at night if the morning run was cut short. Never while the counter is billing.
- **Stops at once** if a key or the mouse is touched, a Marg screen title is not the one expected, or Windows switches user; closes Marg cleanly and says why in the heartbeat (`FromMedical\heartbeat.txt`).
- **Only the reports login.**
- **Take-over, report by report:** shadow beside staff → after **7 clean days in a row** (its file = staff's file) the report moves to the runner; staff asked only on a missed day (the existing 10:00 banner); any report can go back to staff by one switch; the flows page and buttons stay for ever.
- **New:** it also makes the **open on-need requests** of §7 (and the audit trail, if the reports login may open it).
- The WiFi dongle (from 11-Nov) is the medical PC's second road out; the heartbeat says which road was used.

**[v2]** Unchanged, with one line added: the runner's first on-need report is the **Stock Register for one item** (§7), and it is taken over like any other report — in shadow first.

---

## 10 · Build order **[v2: B moves up beside A; four kits become three]**

| # | what | touches | his part |
|---|---|---|---|
| 0 | **Mock v3** — this session: his page (B with its stock effect, A's 13, Ask, the request list), Amir's and Darpan's lines, one Hindi message | nothing live | **his word on what he sees** |
| 1 | **Kit 1 — the watch, read-only:** the door's store rule (§4) · B's compare with the five noise rules and the history fill (§6) · A's records, the whole-sum line, ₹ (§5) · the new page `https://followup.dr-manoj.in/finance/sanjeevni/marg-watch` (owner-only) with both sections · the expiry page's section stays beside it until his word | server: `marg_router.py` (and its manojz copy), `reports_tile.py` (one Hindi line), `marg_hand_change.py`, a new `marg_bill_change.py`, a new page module, `owner_notice.py` (the wording) | the install line |
| 2 | **Kit 2 — Ask:** the buttons, the Hindi message, `amir_job` kind `ask`, Darpan's claim source, the answer path, the close and its two outcomes for a deleted sale bill, the 2-day amber | server: the page module, `amir_day.py` (read whole first — drift 5), `darpan_app.py` and its claim queue, `owner_notice.py` | the install line |
| 3 | **Kit 3 — reports on need:** the request list, the Stock Register's name-free reader, the quarterly sale box | server: the door (`marg_ingest`), the page module | the install line |
| 4 | **Runner trial** on one report, one Sunday morning | medical PC, through the kit | the reports-login password, once |
| 5 | **Runner:** the daily pair in shadow → take-over; the monthly set; the open requests | medical PC + server | none |

**Why B moved up:** without B's findings A counts five moves (+₹1,153) and tells him of them as "changed by hand" — as it did on 10-Nov — when they are one deleted sale bill. A cannot be made right without B.

Each kit: the maker, the walk on made-up rows with its CONTROLS going red, the rehearsal on a copy of the live database in the device VM only (D656), the proof — then his install line; the publish is his double-click (`D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`). Kit 1 begins with a read of the live spine for R10 and record 6.

---

## 11 · Safety **[v2: three lines added]**

- **Read only on Marg**; the system never writes into Marg. The runner uses the reports-only login.
- **No staff screen changes before the mock is approved.** Staff lines are additive, on cards they already use.
- **The expiry page's live section stays** until the new page has run beside it and he says so.
- **Off switches** as today (`/root/finance/_off/ALL_OFF`, `/root/marg_ingest/OFF`, `hand.on`); each new part gets its own setting (`billchange.on`, `ask.on`, `need.on`).
- **No numbers in the repository**; no phone number anywhere (WhatsApp opens without one).
- **[v2] Name-free only:** the watch reads `mi_sale_line`, `purchase_line`, `sale_bill` (totals), the spine and the vouchers — tables that hold no patient name. No raw sale-family file is opened; a new report is read name-free at the door or refused.
- **[v2] History is never announced:** B's first run, like A's first fill, is shown on the page and told to no one.
- **[v2] Kit 1 changes what counts, not what is stored:** every row the engine holds today stays in the table; the records are added columns. Turning `billchange.on` off returns A to today's 18.
- **Files:** all Sanjeevni's own (`marg_hand_change.py`, `expiry_watch.py`, `owner_notice.py`, `reports_tile.py`, `amir_day.py`, `darpan_app.py`, `marg_ingest/`). `marg_router.py` also lives on manojz — both copies in one kit. No PLANNED line is needed: the quarterly check is a typed box, no parent file.

---

## 12 · The open points of v1 — settled **[v2]**

| # | v1 asked | settled |
|---|---|---|
| 1 | how much of the arrival refusal exists | the tile and the refusal path exist; the gap is one rule in `verify()` and one Hindi line; batch stock is already held to WHOLE by its signature (§4) |
| 2 | the rules for the "has a record" cases | six records in a fixed order, B's findings first (§5); 20 rows explained, 13 counted; controls named |
| 3 | does the archive keep superseded exports in full; the bill's identity | yes — on the server, name-free, by md5 (`mi_sale_line`, `purchase_line`); identity in §6.1 |
| 4 | where the composition-GST figure comes from | a box he types once a quarter; no parent file (§6.3) |
| 5 | the Marg path for a stock voucher list; may the reports login open it | replaced by the Stock Register for one item (§7); the login question is Shavez's once, or the runner trial's |
| 6 | a sample of the User Audit Trail | still needed before its reader; until then he reads it in Marg |
| 7 | the Hindi answer words | on the mock, for his word; one tap; lines on cards the staff already use (§8) |
| 8 | the page address | `https://followup.dr-manoj.in/finance/sanjeevni/marg-watch`, owner-only, a link on his command console |
| 9 | S429 never closed | closed by the S432 close (F-1272) |

**Still open, for Kit 1's start (not for the owner):** R10 (BIO D3 MAX +150 on the live spine) and record 6 (DOLONEX +7).

---

## 13 · Evidence and files

- Code read (11-Nov bundle, in the device VM): `finance/marg_hand_change.py` whole; `marg_ingest/lib/marg_effective.py` whole; `marg_ingest/marg_router.py` (`identify`, `verify`, the refusal path); `marg_ingest/marg_take.py` (head); `marg_ingest/signatures.json`; `finance/reports_tile.py` (`hindi_reason`, `_s500_stock_file`); `finance/owner_notice.py` (head, `_part_hand`, `tick`); `finance/expiry_watch.py` (`_hand_section`, the batch-stock title); `finance/amir_day.py` (`amir_job`, `_s494_tap`, routes); `finance/darpan_app.py` (routes, `api_claims`, `page_corrections`); `marg_ingest/lib/marg_stock.py` (the store).
- Data read (11-Nov database copy, device VM only, name-free tables): `marg_hand_change` (37 rows), `sale_bill`, `sale_line_item`, `mi_sale_line`, `purchase_line`, `purchase_export`.
- The two compares behind R1 and R4 were run read-only on those tables; their output is not kept (it is reproduced by Kit 1's history fill).
- v1's evidence stands: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S429\` (notes, working figures, `screen\stock_moved_no_record_MOCK_v2.html`).
- The mock of this session: `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S434\screen\marg_watch_MOCK_v3.html`.
- **A lapse of this review, for the close:** to see what a Stock Register file looks like, the first lines of one raw file in the archive were printed in the device shell; they carry patient names, and so passed through the chat's tool output. Nothing was copied, kept or written anywhere. The rule that comes of it is R6.

*S438_MARG_WATCH_PLAN_v4 · 12-Nov-2026 (night) · the Sanjeevni chat · Kit 1 (S803) live; the door's store rule next; sections A, Ask, reports on need and the runner not built*

*(v3's footer, retained:)* *S434_MARG_WATCH_PLAN_v3 · 12-Nov-2026 · the Sanjeevni chat · the watch not built; the repair S795 (F-1277) is live*
