# S503 — Stock plan v2: what is built, what waits

*The Sanjeevni chat, session 503 (Fable) · Sunday 22-Nov-2026 · supersedes the plan section (§7) of `S501_STOCK_PAGES_CONSOLIDATION` (its findings §1–§6 stand). Figures as on Marg's closing of 20-11. Nothing here is a diagnostic for the owner: it records what changed on the server today and what the next sessions build.*

---

## 1 · In five lines

1. **Steps 1, 2 (in part) and 7 of the S501 plan are LIVE** (22-Nov 16:59 IST, kits S928 · S930 · S932): the one arrivals rule **bill over tap**, **counts by their time**, **every count on his Hub**, the **Stock check page** in place of Stock drift / Stock now, and the orthotic **order lines under Marg's current name** (F-1579).
2. The three "should be on the shelf" figures (S501 §4) now share **one delivery figure** — the scanned bill's; what remains is the honest difference Marg's figure *vs* the last count carried forward, named the same way on every page.
3. **Count names through renames (step 2b)** is half done: the Stock check page lists count-only names apart; the stock function still lists them as rows — F-1563 stays open for the next kit.
4. **Retired pipes (step 3), the spine's item list (4), batches (5), order–bill ties (6), the owner's monthly line (8)** are untouched — in order, next sessions.
5. Every rule shipped today is a **setting** (his page): `arrival.bill_over_tap` (on), `count.evening_hour` (17).

---

## 2 · The S501 steps, status

| Step | S501 §7 item | Fault(s) | Kit | State 22-Nov |
|---|---|---|---|---|
| 1 | One arrivals rule, bill over tap | F-1565 (d) | **S928** | **LIVE 16:59.** `stock_figure.bill_units` / `_count_units`: a tapped line counts the bill's quantity (both batch lines summed, free goods in); a tapped medicine the bill does not carry counts 0; no usable, read scan → the tap stands; `short_supplies()` names a tap above the bill (back on the dealer's next order — the order engine reads it next session). Shelf, Darpan's judging, ordering move together. s825 and the rule read ONE match per order. |
| 2a | Counts by their time | F-1564 (c) | **S928** | **LIVE.** A spot count at or after `count.evening_hour` is the END of its day (`evening_count`); the day's sales are not taken off again. A full count never flips. |
| 2b | Count names through renames; 2 unlinked names | F-1563 (b), F-1569 | — | **OPEN.** The Stock check page lists count-only names apart ("count names Marg no longer prints") so they no longer look like losses; the stock function's rows are unchanged. Next kit: fold through `item_alias`; link ANKLE BINDER TYNOR XL and VFER 500 → V FER 500 (his tap on the S926 question does the second). |
| 3 | Retired pipes off | F-1562 (a, h) | — | **OPEN.** The drift page is retired by redirect (its code stays); the witness cron `# S577_WITNESS`, `marg_shadow`, the PC's `push_expected` (22:30) and the purchase hub's feed card still run/draw. Next kit (two files + one cron line). |
| 4 | The spine carries Marg's item list | — | — | OPEN. |
| 5 | Batches by the full batch | F-1566 (e) | — | OPEN (29 items). |
| 6 | Order–bill ties re-paired | F-1567 (f) | — | OPEN (Kedar's TYRO bills). |
| 7 | Darpan's counts to the owner; his question | F-1568 (g) | **S928 + S930** | **LIVE.** One Needs-you line a day ("Darpan counted N items on dd-mm-yyyy: …", rewritten after each count, 7 days) opening the Stock check page; the page's Darpan's-counts card (30 days, evening tag, asked/system), "Count this" on every row (no dialogs, F-1464). **His "is the delivery in your count" question on Darpan's screen: NOT yet** (stockmatch/roster_view) — next session. |
| 8 | The spine's unexplained moves, one owner line | — | — | OPEN. |
| — | Orthotic order names | **F-1579** | **S932** | **LIVE.** A kept 'yes' line leaves the lane under Marg's current name (exact map of ticked renames, never a clip; a chain X→Y→Z folds nothing on Y); an order under the new name clears the kept row; `porders._on_order` folds the new name back to the lane's key. On the 22-Nov copy: "Orthotic shortages: 10 → 8", KNEE SUPPORT HINGED XL's "−1, not offered" line gone (on order under its new name). |

---

## 3 · The pages now (S501 §7 "13 to 5", where it stands)

| Page | 22-Nov |
|---|---|
| **Stock check** `https://followup.dr-manoj.in/finance/stockcheck/` | **NEW (S930, mock-up v5).** Marg · shelf (the count carried forward, without the deliveries) · waiting by the bill · real difference; Need a look (big / under one strip / orthotics folded); deliveries waiting with the bill's word; no-shelf list; count-only names; agree; reports line; Darpan's counts + Count this; 2-minute cache with "read again"; viewer may read, checker/maker may Count. |
| Stock drift, Stock now | **RETIRED by redirect** to the Stock check page (code kept, unlinked). The purchase hub still links "Stock check" to the old drift address — works through the redirect; re-point in the retired-pipes kit. |
| Hub Go to | "Stock check — Marg against the shelf, Darpan's counts, Count this" first under Stock & expiry; "Count of 06-Sep — every step (closed)" replaces "Stock now". |
| Item ledger | unchanged — still its own Expected rule (Marg + scanned bills, counts ignored). Next: read `stock_figure` for Marg · shelf · waiting. |
| Loss desk, Expiry, Marg watch, Count #1 pages | unchanged. |

---

## 4 · What waits on the owner

- **VFER 500 = V FER 500** — his one tap on the Purchase orders flow page (S926's question) links the two names.
- **TYRO BR** on Darpan's next list (D1037) — Count this from the Stock check page, one tap.
- Ram Singh: the Stock Register button in Shavez's Marg login (standing).
- Packs page (D713, the parent's) — standing.

## 5 · Next session, in order

1. F-1563 / F-1569 count names through renames (stock_figure rows) + the item ledger on the one function.
2. Darpan's delivery question on his count screen (stockmatch + roster_view/answer_roster) and the short-supply line on the dealer's next order (order engine reads `short_supplies`).
3. F-1562: retired feeds off (witness cron, marg_shadow, push_expected, the hub's feed card re-pointed).
4. S9xx Needs-you panels remaining; S926's first days read (the rename question, keeps, substitutes).
5. Steps 4–6, 8 of S501.

## 6 · Faults of the day (minted at the close)

- S928's first box run stopped at [3/6]: the server's `/root/shared/scan_quality.py` (absent in the build VM) judged the synth's made-up bills "to redo" (no totals) — the fixtures now carry totals; the synth prints WHY lines (the judge, the scan context, the match). Rule: a synth that rides the scan half runs with `SHARED_LIB_DIR` set to a copy of `/root/shared`.
- Kit numbers: this chat built under S929 before taking it (the parent took S929 at v2035) and was refused S931 (the parent took it at v2047); nothing placed under either; S930/S932 taken by probe-miss → append → pinned integer. The board read whole three times by matching probes (F-1478's family).
- The cold reviews' MUSTs, all caught before the install: S928 (two batch lines once; a one-item match taking a sibling's quantity; the evening rule on a full count), S930 (a Marg name with an apostrophe inside an onclick JS string), S932 (the fold by `item_alias.resolve` would have folded a never-renamed sibling sharing the 20-letter clip).
- Reviewer's note on the live record: S501's "count names" fault b still inflates the stock function's rows (417 for 389 items) until F-1563 is built.
