# S957_COUNT_LEFTOVERS · Sanjeevni session 522 · 26-Nov-2026 — after S952 / S954 / S956 (each CONFIRMED by the 26-Nov bundle)

**Why.** His questions of 26-Nov 08:55 on "Amir's three" (S954's list). Read on the 26-Nov database:
- **NORTIMER TAB** — he took it out of the 06-Sep count himself on 12-Oct (voucher batch 10 voided, the item settled: "strips with Darpan, being sold"). S954 still read its 1:0 as "Marg still holds the older loss". The settlement was not honoured: a fault of ours.
- **VINBACTUM DS** — his word: old residue in Marg, ignore it for now. Nothing to change in the code: it stays "Marg still holds the older loss" (true) and is no longer named to Amir.
- **KT ROS DT** — Darpan's count of 23-11: 299 tabs (19:14) against Marg's 415 (27:10). Marg never took the 06-Sep issue of 6:11 though Amir tapped done on 18-10 and 19-11; one strip short since. The judgment is right; Amir's job is one STOCK ISSUE of 7:11 as of that count.
- **The S956 review's note** — `stock_watch._s936_match` still treated every Marg line dated a morning count's day as inside the count; S956 adds the ones that came after it to the shelf. Now the recount match keeps them too (JAKMAC 5's bill 100075 of 23-11).

**Files.** `/root/finance/record_judges.py` 5c5cca26 → v1.2 (`_settled`: an item settled for a count is never pending from it; a voided voucher writes nothing off). `/root/finance/stock_figure.py` df35fc93 → v1.8 (S956's body moved to `_s956_after`, returning its bills; `s956_after_bills` for the match; the shelf figure unchanged — walked on every item counted since 18-11). `/root/finance/stock_watch.py` 401684ea → v1.13 (the match). Then every count since 18-11 judged again (on the 26-Nov copy: 19 judged, 1 moved — NORTIMER TAB 23-11: "6:0 below Marg — a loss since the last count").

**Amir's card** (his word 26-Nov 09:31, "remind ktros dt stk issue"): one tap job, key `S957:ktros:7-11` — *KT ROS DT — Marg mein STOCK ISSUE kijiye: 7 patte + 11 goli* (`amir_s957.py add`; the undo removes it unless Amir tapped it done).

**Walk** `walk_s957.py CODE COPY_DB FROM_DIR` — on a copy, twice; CONTROL (the FROM files) red. **Undo** `undo_s957.sh` (the judgments it re-made back from its own moment, then the three files).

**Split sizes** keep the old same-day rule (S956's second note) — not in this kit; a split size is shown as approximate already.
