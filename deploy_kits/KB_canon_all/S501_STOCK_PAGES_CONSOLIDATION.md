# S501 — Stock pages: one source, one figure, fewer pages

*The Sanjeevni chat, session 501 · Sunday 22-Nov-2026, 07:3x–08:xx IST · read only: nothing live changed. Figures as on Marg's closing of 20-11 (taken 21-11 09:37), read from the live pages (signed in as manoj) and the 22-Nov nightly copy (03:17). Quantities in strips:tabs; pieces for orthotics, gels, sachets. Analysis only — nothing is built until the owner says so.*

---

## 1 · The answer in five lines

1. **Marg's figure already has one source** (the Marg spine, read by one function, `stock_figure`). Every page that shows "Marg's stock" agrees with every other: checked item by item, 0 differences.
2. **What diverges is everything laid on top of Marg's figure**: there are **three different "what should be on the shelf" figures** in use today, by three different rules, and the pages do not say which one they show.
3. **Two retired pipes are still running and still drawn on screens**: the medical PC's old estimate (wrong on 188 of ~240 items) and the PC's copy of Marg's stock list (correct, but a second pipe for the same thing).
4. **Five calculation faults** were found (count names, evening counts, tap over bill, batches not adding up, order–bill ties) — each makes a gap that is not a real loss, so a real loss (TYRO BR) hides among false ones.
5. **Proposal:** finish the revamp's own plan on the spine — one stock function with one arrivals rule, the retired pipes switched off, and **13 stock pages reduced to 5**. Backend first; the one screen change is the Stock check page he has already seen (mock-up v5).

---

## 2 · Every stock page in the system, and where its figure comes from

| # | Page (address) | What it is for | Marg's figure from | "Should be on shelf" figure from | State |
|---|---|---|---|---|---|
| 1 | Stock drift `https://followup.dr-manoj.in/finance/stock/page/drift` | Marg against the shelf | spine (`stock_figure`) — sent but **not drawn** | the PC's old estimate, run after run — **drawn** | **wrong figures on screen** |
| 2 | Stock now `https://followup.dr-manoj.in/finance/stock/page/now` | today's stock, both figures | spine | count carried + taps (`stock_figure`) **and** the PC's old estimate beside it (394 rows) | duplicate of #1 |
| 3 | Item ledger `https://followup.dr-manoj.in/finance/sanjeevni/ledger` | one item's full history | spine | **its own rule**: Marg + scanned deliveries (ignores counts) | correct ledger; "Expected" means something else than #1/#2 |
| 4 | Batches box (inside #3) and Expiry `https://followup.dr-manoj.in/finance/sanjeevni/expiry` | stock by batch, expiry | Batch Stock of 13-11 + moves since | — | **29 items do not add up to Marg** |
| 5 | Loss desk `https://followup.dr-manoj.in/finance/stock/page/loss` | write-offs; "Count this"; the watch card | count #1 vs the PC's copy of Marg | count carried (`stock_figure`) | live; "Count this" lives only here |
| 6 | Darpan's spot counts (his page) and their judging | morning counts | spine | count carried + taps (`stock_figure.expect_for_point`) | live; results reach the owner only when he asked |
| 7 | Purchase orders / flow `https://followup.dr-manoj.in/finance/porders/flow` | what to order | spine | **Marg + taps + unmatched scans** (order engine) | live |
| 8 | Purchase hub stock card `https://followup.dr-manoj.in/finance/purchase/page/hub` | feeds' health | — | the PC's two old feeds | retired pipe still shown |
| 9 | Marg watch / Stock Register `https://followup.dr-manoj.in/finance/sanjeevni/marg-watch` | stock moved with no record | the PC's copy of Marg's list (names) + spine | — | live |
| 10 | Section count `https://followup.dr-manoj.in/finance/stockmatch/count` | the one-time orthotic count | the PC's copy of Marg's list | — | live, one-time |
| 11 | Stock milaan `https://followup.dr-manoj.in/finance/stockmatch` | count #1's orthotic section | spine | — | count #1 closed (28-Oct) |
| 12 | Count #1 pages: count, pad, sections, desk, diffs, finding, report, statement, Amir's board, stock hub (`/finance/stock/page/...`) | the 06-Sep count's workflow | the PC's copy of Marg's list | — | **count #1 closed — still live and linked from the Hub's Go to** |
| 13 | The nightly witness (`/root/finance/spine/stock_figure_witness_<day>.txt`) | old ways beside the new "for one week" | spine | the PC's old estimate + `marg_shadow` | **the week ended 22-Nov; still running** |

**One function exists for Marg's figure and the shelf figure** (`stock_figure`, since S577 on 18-Oct; `shelf_figure` is now only a wrapper over it). The divergence is not in that function — it is in the **arrivals rule**, in the **readers that bypass it** (#3, #7's own blend, #8, #9, #10, #12) and in the **retired feeds still drawn** (#1, #2, #8, #13).

---

## 3 · What was compared, and what agrees

| Comparison (all as on 20-11) | Items | Differ | Reading |
|---|---|---|---|
| Spine (Marg's closing as the server reads it) **vs** the PC's copy of the same Marg export (`stock_snapshot`) | 389 | **0** real (1 is a name collision: VFER 500 / V FER 500) | **Marg's figure is one figure everywhere** |
| Spine **vs** the PC's push of that copy (`stock_feed` push_snapshot) | 389 | 0 real | the same file through a third pipe |
| Stock drift page's record **vs** Stock now page | 417 | 0 | one function, two pages |
| Shelf figure **vs** the PC's old estimate (push_expected, still sent nightly at 22:30) | ~240 | **188** | e.g. TYRO BR 33:5 vs PC 84:9; ORICOX P 28:2 vs PC 98:3; TRAMATEE 9:4 vs PC 65:13. **Retired since 18-Oct; still on three screens** |
| Spine's own day-by-day rebuild **vs** Marg's printed closing (the spine's gate) | 389 | **26** at 19-11 (e.g. AURAB L CAP −34, BIO D3 MAX −39) | Marg's printed closing wins as the figure; the 26 are the spine's own unexplained moves |
| Batches (Batch Stock 13-11 + moves) **vs** Marg | 233 | **29** | e.g. TYRO BR batches add up to −33:7 while Marg holds 16:3 |

---

## 4 · The three "should be on the shelf" figures (the main divergence)

| Where | Rule | ZIBON EXTRA (counted 20:6 by Darpan on 18-11) | CROCAL (bill 20, tap 30) |
|---|---|---|---|
| Stock page, Stock now, Darpan's count judging | last count carried forward + **reception's taps** | 19:3 | 36:2 |
| Item ledger "Expected stock" | Marg + **scanned bills** (counts ignored) | 34:6 | 26:2 |
| Ordering (what to order) | Marg + **taps** + scans not tied to an order | 34:6 | 36:2 |

The same item, three answers, none labelled. The owner's ruling (22-Nov 07:01): **the scanned bill's quantity counts, never reception's tap — everywhere.** With that rule in the one arrivals rule, all three use the same delivery figure; the remaining honest difference is only *Marg's figure* versus *the last count carried forward*, which every page then names the same way.

---

## 5 · The faults found (each makes a gap that is not a loss)

| F (to be minted at the close) | Fault | Where it shows | Size today |
|---|---|---|---|
| a | **The drift page draws the PC's retired estimate**, not the figures of record; loose tablets, not strips:tabs; a 56-day verdict | Stock drift | every row |
| b | **The count's old spellings are separate rows**: the stock function lists every name in Marg's closing **plus** every name in count #1, so an orthotic renamed on 11-Oct shows twice | Stock drift, Stock now (417 rows for Marg's 389 items) | ~28 extra rows: about 17 items shown twice (incl. BLING PELVIC…, SHOULDER IMMOB L, TYNOR WRIST SPL…) and count-only names; 2 count names never linked (ANKLE BINDER TYNOR XL; VFER 500 → Marg's V FER 500) |
| c | **Every count is treated as taken before that day's sales**; an evening count has the day's sales taken off twice | shelf figure, Darpan's judging, ordering on counted items | 6 counts: TYRO BR (12-10 19:49, ~18:5 strips), TENDOZAC, MEG QCS, FENARIC T4, ONKET DT, ZUPRINOR 5 |
| d | **Reception's tap wins over the scanned bill** in the one arrivals rule (a tap tied to a scan suppresses the scan) | shelf figure, ordering | Shivaaz 21-11: CROCAL tapped 30 / bill 20; TRAMAVIN GEL 24 / 20; CEECIT MZ 10 / 20; Ess Kay FERONES HD 20 / 25 |
| e | **Batches do not add up**: Marg's purchase export carries a shortened batch ("7/107/11") where its sale export carries the full one ("LGQ07/107/11"), most likely why purchases after the 13-11 Batch Stock are not placed on their batch (the two spellings seen on TYRO BR's ledger; the matching code and the other 28 items to be read at the build) | Batches box, Expiry | 29 items, some "below zero" for weeks |
| f | **Order–bill ties shifted by one order** (Kedar's TYRO bills 238 → the 02-11 order, 242 → the 04-11 order), so the 13-11 order's 50 strips stand "arrived, no bill" though Marg has them | Purchase orders | Kedar, November |
| g | **Darpan's counts reach the owner only when the owner asked**; the system's own picks go nowhere; asks wait for weeks unseen | Hub | ANKLE BINDER L BAMBOO 35 days; PRETOL-4 32 days; 14-11 and 16-11 lists not done |
| h | **The witness's "old ways for one week" never retired** (written 15-Nov; still running 21-Nov): the PC estimate and `marg_shadow` (e.g. TYRO BR −500:7, nonsense) recomputed nightly | spine folder | nightly |

Real losses, after a–f are corrected: **TYRO BR about 14:3 strips** lost between the 06-Sep count and Darpan's 12-Oct count (23:0 already written off in September); smaller ones on the Stock check mock-up's "Need a look" list (ZIBON EXTRA −15:3 with its voucher on Amir's card; KT ROS DT; NORTIMER; FLEXURA D; JAKMAC 5; VINBACTUM DS …).

---

## 6 · The Marg spine — its state (22-Nov)

- **Built nightly** (last 21-11 23:50 IST), **gate 13/13 green**, last failure 19-11 10:10. It is the one reader of Marg's exports for stock (closings, sales, purchases, returns, vouchers, salts, MRP) and the one input of `stock_figure`, the item ledger and the order engine.
- **Its own cross-checks** (`spine_compare`, 21-11 23:55): sale bills agree on gross; one day's sale lines differ (03-11); **purchases 678 in the spine vs 681 in the live purchase book** (3 bills the spine does not hold); salts 387 = 387; **MRP differs on 44 items** between the live price facts and Marg's MRP (e.g. CETAPHIL REST MOIST Rs 1.00 vs Rs 2,561).
- **Its rebuild of stock day by day** reaches Marg's printed closing on all but **26 items** (19-11). The page figure is always Marg's printed closing, so these 26 do not reach a screen — but they are unexplained moves the spine itself has seen, and nobody reads them.
- **What it does not yet carry**: Marg's item **names with pack sizes** as a list (it keeps closings by key), which is the only reason six modules still read the PC's copy of Marg's stock list.

---

## 7 · In the revamp's frame

The revamp's own direction (D-rulings of 18-Oct onward; the owner, 28-Oct: *"the remaining architecture revamp is to be backend only"*): **sections and subsections on the spine; one fact in one place; every screen reading the one function.** For stock most of it is done — `stock_figure` exists and every Marg figure already comes from it. What is left is exactly the list above: the arrivals rule, the readers that bypass it, and the retired pipes.

**Proposed consolidation — 13 pages to 5:**

| Keep (one each) | Takes over | Retires (address kept, sends to the new page) |
|---|---|---|
| **Stock check** (mock-up v5) — Marg against the shelf, Darpan's counts, deliveries waiting, Count this | Stock drift, Stock now, the Loss desk's watch card and Count this | Stock drift, Stock now |
| **Item ledger** — one item; shows **Marg · shelf by the last count · waiting by the bill** from the one function | its own Expected rule | — |
| **Expiry** (with the Batches box fixed) | — | — |
| **Loss desk** — write-offs only | — | — |
| **Marg watch** — stock moved with no record | — | — |
| *(archive, read only)* Count #1 | count, pad, sections, desk, diffs, finding, report, statement, Amir's board, stock hub, Stock milaan | off the Hub's Go to |

**Backend, in order (no screen changes except the Stock check page):**

1. **One arrivals rule, bill over tap** (fault d) in `stock_figure` — shelf, Darpan's judging and ordering move together; the item ledger reads the same rule. A tap above the bill becomes a short supply on that dealer's next order.
2. **Counts by their time** (c) and **count names through Marg's renames** (b); the two unlinked names linked.
3. **The retired pipes off** (a, h): the PC's old estimate no longer sent or drawn; the witness ends; `marg_shadow` ends; the purchase hub's feed card reads the spine.
4. **The spine carries Marg's item list with pack sizes**; the six modules reading the PC's copy of the list move to it; the PC's copy stops (one pipe from Marg, not three).
5. **Batches by the full batch** (e): a purchase's batch matched on its shortened text against the sale's full text (or the scanned bill's batch).
6. **Order–bill ties** (f) re-paired by date and quantity; the shift cannot recur.
7. **Darpan's counts to the owner** (g): every count, every skipped list, on his Hub; his "is the delivery in your count" question.
8. **The spine's own unexplained moves** (26 items, 3 purchase bills, 44 MRPs) on one owner line, read monthly — a thing that exists to be checked gets a checker that says it need not be run.

Each step is a kit with its walk and its control, built on the newest bundle's bytes, installed by his one publish and one line. Steps 1–3 change no screen except Stock check; 4–6 change none; 7 changes his Hub line and Darpan's count screen (both in the mock-up).

---

## 8 · Sources read

- 22-Nov nightly code bundle (03:17) — `/root/finance/stock_app.py`, `stock_figure.py`, `shelf_figure.py`, `stock_watch.py`, `item_ledger.py`, `expiry_watch.py`, `order_rules.py`, `order_track.py`, `purchase_app.py`, `section_count.py`, `marg_billwatch.py`, `darpan_app.py`, `/root/finance/spine/spine_state.json`, `spine_compare_latest.txt`, `stock_figure_witness_Sat.txt`
- 22-Nov nightly database copy (in the device VM only; removed at the close)
- Live, signed in as manoj: `/finance/stock/api/drift`, `/finance/stock/api/now`, `/finance/sanjeevni/ledger` for the items named
- Mock-up: `https://claude.ai/artifact/XzqcBUHoroPyTt7xG8bNea` (v5)
