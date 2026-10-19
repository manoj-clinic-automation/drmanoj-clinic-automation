# REPORT S598_ARRIVALS_BY_LINE — installed 19-Oct-2026, 09:54 IST

## For the owner

1. **A bill line now answers only the size it names.** Until this morning the system matched a delivery to an order by the first 20 letters of the item's name, so Yuvika's bill of 28-09 ("KNEE SUPPORT HINGED M ×4, L ×2") was credited to your order of KNEE SUPPORT HINGED XL ×2 as "6 came". From now each order line is matched to the bill line of its own printed name; a sibling size never takes it, and one bill line is never credited to two orders.
2. **Two wrong marks are corrected, not one.** KNEE SUPPORT HINGED XL (order of 26-09) is back to "not yet billed", as the brief said. The same check found a second one: **L S BELT CONT GRAY UNISON XXX** (order of 07-10) had been marked "came" by Yuvika's bill of 07-10, but that bill names the **XXL** size, not XXX — so it is back to "not yet billed" too. The other five marks of this morning (ANKLE BINDER BAMBOO M, CROCAL, PREGHYPE NT TAB, BRUTAFLAM GEL, CAST SHOE M TYNOR) are right by name and stay.
3. **The screens go back to how they stood before 08:03 this morning, for those two lines:** both lines show as open again on their Yuvika orders on reception's *Orders* card (the `all` button is back on each), XL ×2 and XXX ×1 count again as "on order", and both leave the orthotic shortage card (4 items → 2: ANKLE BINDER BAMBOO M 1, RIB BELT UNIVERSAL UNISON 1). No words changed on any staff screen — checked word for word for reception, Darpan, Amir and Shavez.
4. **Your Needs-you says more.** Where Marg's bill carried *other sizes* of the item, the arrival line now says so: *"KNEE SUPPORT HINGED XL: counted as arrived when the YUVIKA SURGICALS bill was scanned 29-09 19:06 -- not in Marg's purchases up to 18-10 (its bill 672 of 28-09 carried KNEE SUPPORT HINGED M, KNEE SUPPORT HINGED L, not this size)"*. You now have 13 arrival lines (were 11): the XL and the XXX lines are new, and five lines carry the clause (XXL, XL, ANKLE BINDER BAMBOO L, L S BELT XXX, KNEE IMMOBILIZER UNISON XL). All are true: those sizes are not on any Yuvika bill Marg has. Only a Marg bill naming the size can close such a line — there is no staff tap for it (the D712 gap, unchanged).
5. **Installed and working:** `clinic-finance` restarted once at 09:54:13 IST, healthz 200, every page answering. Sizes that still agree in their first 27 letters on an OLD-spelling bill (the belt family printed as `L S BELT CONT GRAY UNISON X`) stay one lump — Marg's own report cannot tell them apart.

## For the chat

### Files, FROM → TO (read back on the box after placing, 09:54 IST)

| file | FROM | TO |
|---|---|---|
| /root/finance/stock_figure.py | 92367a196b360f0cded4cda6a5ded700 | cb577821d9e1eb40110312b4331df9ef |
| /root/finance/stock_watch.py | c5f3ce21a785c45df58f21932cf920e7 | 299c3ef76b73a10e4af1cd15974c7a3f |
| /root/finance/porders.py | 78ea72be7d87a7c56c65de7d4c96a952 | e5a5c4d4dfa15c3ecd0b0cdf4786abcd |

Read-only pins printed at the open and unmoved: shelf_figure 23b2394a, order_rules 8d078dbe, porders_s454 40f1755a, order_sheet 1f1e85c1, stock_app 4f73d0b0, amir_day 3af992d9, spine/spine_build e3d3ed85, spine/spine_read 827b0040, item_alias 111a8e48, qty_words 706db7cc, marg_purchase_rows 41d68148 (the brief gave no hash; pinned to the bytes read on 19-Oct). Proved unmoved by the installer: finance_app, portal.py, tile_grants.json, the crontab (84 lines, `# S577_WITNESS` once), spine.db's schema (a66309303c25178a291ada6fb539fbe5 before and after). The four renames read from `item_alias.done_rows` at the open: all four `verified`. 13 anchored edits, each anchor exactly once; compiled on both pythons. The spine at install: passed 13/13, last success 2026-10-19T09:50:49+05:30 (2 min old). Settings: `arrival.bill_grace_days` 3, `arrival.back_days` unset (default 2), `order.source` marg_sheet, `order.stock_basis` count.

### The install (one run, one placement)

- **09:41, 09:46, 09:49** three DRY runs (every gate, the scratch sides, both walks); the first two found two faults in the kit itself (the `short` column is NOT NULL — an open line holds 0, not NULL; the screen diff had to mask times on both sides), fixed in the kit before anything was placed. **09:53:14** the build lock taken by S598; pins exact; the state BEFORE and as the NEW files read the same copy; backups; **09:54:13** the three files placed by rename in one command and `clinic-finance` restarted — healthz 200; /finance/porders, /porders/s454/order, /stockmatch, /amir, /reports/aaj, /sanjeevni/api/needs-you all 302 without a login (the gate, expected); journal clean; `rejudge_s598.py` once on the live database (below); `detect_supplies` once (wrote 0 lines); the state AFTER; nothing else moved; `DOCTOR_AUTO_OFF` removed; md5 read-back as the table above. DONE.
- The kit ran from `/tmp/s598kit` (SUMS checked on the box); the kit in the repository is byte-identical (SUMS re-checked in the clone after the publish, below).

### The walk on the box (the install run, 09:53)

`WALK OK S598: 66 checks, 29 controls green on the new files` · negative control: `every control red on the old files (25)` (the four other controls exist only against `--old-dump`, which the OLD run has none of). Every section green.

**Control 1 (bill 672) verbatim:**
```
line 3 KNEE SUPPORT HINGED XL (order 1, re-judged with billed_bill_no None): no carrying bill line; family_bill {'supplier': 'YUVIKA SURGICALS', 'supkey': 'YUVIKASU', 'bill': '672', 'date': '2026-09-28', 'sizes': ['KNEE SUPPORT HINGED M', 'KNEE SUPPORT HINGED L']}
ok   C: line 3 KNEE SUPPORT HINGED XL -> carried() None (no XL line on 672 or any Yuvika bill) with family_bill = bill 672 of 28-09 [M, L]
line 4 KNEE SUPPORT HINGED XXL UNISO: no carrying bill line; family_bill {... 'bill': '672', 'date': '2026-09-28', 'sizes': ['KNEE SUPPORT HINGED M', 'KNEE SUPPORT HINGED L']}
ok   C: line 4 KNEE SUPPORT HINGED XXL UNISO -> None with family_bill 672 [M, L] (None on OLD too, without the family bill)
line 1 ANKLE BINDER BAMBOO L (S537's mark, rule a): (a) its own bill 672 of 2026-09-28, units 1.0
ok   C: line 1 ANKLE BINDER BAMBOO L by rule (a): the L line of 672 (1 pack, units 1) -- the LINE's figure, with its seq and name27
line 3 as S593 marked it (rule a, bill 672): (a) its own bill 672 of 2026-09-28, units None
ok   C: line 3 by rule (a) as marked: carried (Marg's answer trusted) but units None -- no XL line on 672 (the OLD key sum said 6)
```
On the OLD files: line 3 → bill 672 units 6 (red); line 1's rule-(a) units are 1 on both sides (bill 672 carries only the L line of that key — the brief expected the key sum to differ; it does not), so that control is red on OLD by the absence of `seq` / `name27`, stated.

**Control 2 (bill 2627) verbatim:**
```
line 2 ANKLE BINDER BAMBOO M: (d) bill YS…2627 of 2026-10-07 line 116 'ANKLE BINDER M BAMBOO', packs 1, units 1.0 -> packs 1 (S593 wrote 1 by YS…2627)
ok   C: line 2 ANKLE BINDER BAMBOO M -> bill 2627's 'ANKLE BINDER M BAMBOO' line (through the ticked rename), qty 1 -> packs 1 == S593's write (agree)
line 48 ANKLE BINDER BAMBOO L (order 20): no carrying bill line; family_bill {... 'bill': 'YS…2627', 'date': '2026-10-07', 'sizes': ['ANKLE BINDER M BAMBOO']}
ok   C: line 48 ANKLE BINDER BAMBOO L -> None with family_bill = 2627 of 07-10 [ANKLE BINDER M BAMBOO]
key_of('ANKLE BINDER BAMBOO M') = 'ANKLE BINDER BAMBOO'; forms ['ANKLE BINDER BAMBOO M', 'ANKLE BINDER M BAMBOO']
key_of('ANKLE BINDER M BAMBOO') = 'ANKLE BINDER BAMBOO'; forms ['ANKLE BINDER BAMBOO M', 'ANKLE BINDER M BAMBOO']
key_of('ANKLE BINDER BAMBOO L') = 'ANKLE BINDER BAMBOO'; forms ['ANKLE BINDER BAMBOO L', 'ANKLE BINDER L BAMBOO']
key_of('ANKLE BINDER L BAMBOO') = 'ANKLE BINDER BAMBOO'; forms ['ANKLE BINDER BAMBOO L', 'ANKLE BINDER L BAMBOO']
ok   the four spellings resolve to one key (the sp_alias fold; the per-line rule tells M and L apart)
```

**Control 7 (REPORT_S593 control 3's lines replayed, OLD vs NEW) verbatim — the lines that differ or are carried:**
```
line 2    ANKLE BINDER BAMBOO M          YUVIKA SURGICALS       | OLD (d) YS…2627 packs 1       | NEW (d) YS…2627 packs 1 line 'ANKLE BINDER M BAMBOO'
line 3    KNEE SUPPORT HINGED XL         YUVIKA SURGICALS       | OLD (d) 672 packs 6           | NEW none
line 28   CROCAL                         SHIVAAZ FORMULATIONS   | OLD (c) 3463 packs 24         | NEW (c) 3463 packs 24 line 'CROCAL'
line 30   PREGHYPE NT TAB                SHIVAAZ FORMULATIONS   | OLD (c) 3463 packs 24         | NEW (c) 3463 packs 24 line 'PREGHYPE NT TAB'
line 31   PRETOL 8                       SHIVAAZ FORMULATIONS   | OLD (e) A000203 packs None    | NEW (e) A000203 packs None line 'PRETOL 8'
line 36   BRUTAFLAM GEL                  GUNINA PHARMACEUTICALS | OLD (d) GPPPL3679039 packs 24 | NEW (d) GPPPL3679039 packs 24 line 'BRUTAFLAM GEL'
line 47   CAST SHOE M TYNOR              YUVIKA SURGICALS       | OLD (d) YS…2627 packs 1       | NEW (d) YS…2627 packs 1 line 'CAST SHOE M TYNOR'
line 50   L S BELT CONT GRAY UNISON XXX  YUVIKA SURGICALS       | OLD (d) YS…2627 packs 1       | NEW none
line 77   POWERGESIC 100 PATCH           DEEPAM PHARMA          | OLD (e) 23672 packs None      | NEW (e) 23672 packs None line 'POWERGESIC 100 PATCH'
23 lines: 5 carried by the own vendor (c / d), 2 by another supplier (e), 16 no bill; open lines whose spelling is >= 27 characters: 3 (R1-C2's reach)
OLD vs NEW disagreements: [3, 50]
```
(23 lines, not S593's 24: line 15 CHYMORAL AP is `missing` and left out.) The other 14 lines are "none" on both sides. **Expected disagreements: two, not one — line 50 beside line 3 (see "Findings").**

**Control 8 (the re-judge on the copy) verbatim:**
```
line 2    ANKLE BINDER BAMBOO M          AGREE    -> (d) bill YS…2627 of 2026-10-07 line 116 'ANKLE BINDER M BAMBOO' qty 1
line 3    KNEE SUPPORT HINGED XL         DISAGREE -> no matching bill line -- the family's bill 672 of 2026-09-28 carried KNEE SUPPORT HINGED M, KNEE SUPPORT HINGED L
   -> cleared: billed_qty, billed_bill_no, billed_date, detected_at, supplied, arrived_by, arrived_at NULL and short 0 (the system's own write, S593's audit row found)
line 28   CROCAL                         AGREE    -> (c) bill 3463 of 2026-10-01 line 88 'CROCAL' qty 24
line 30   PREGHYPE NT TAB                AGREE    -> (c) bill 3463 of 2026-10-01 line 90 'PREGHYPE NT TAB' qty 24
line 36   BRUTAFLAM GEL                  AGREE    -> (d) bill GPPPL3679039 of 2026-10-06 line 22 'BRUTAFLAM GEL' qty 24
line 47   CAST SHOE M TYNOR              AGREE    -> (d) bill YS…2627 of 2026-10-07 line 117 'CAST SHOE M TYNOR' qty 1
line 50   L S BELT CONT GRAY UNISON XXX  DISAGREE -> no matching bill line -- the family's bill 738 of 2026-10-18 carried L S BELT M CONT GRAY UNISON, L S BELT XL CONT GRAY UNIS
   -> cleared: billed_qty, billed_bill_no, billed_date, detected_at, supplied, arrived_by, arrived_at NULL and short 0 (the system's own write, S593's audit row found)
purchase_order.status of (1, 10, 13, 20): {1: 'received', 10: 'received', 13: 'received', 20: 'received'} (equal before and after)
REJUDGE OK S598: 7 row(s) re-judged, 5 agree (2,28,30,36,47), 2 cleared (3,50)
cleared [3, 50]; untouched [2, 28, 30, 36, 47]; audit line_rejudged_s598 rows {2: 0, 3: 1, 28: 0, 30: 0, 36: 0, 47: 0, 50: 1}
ok   a second re-judge finds the five agreeing rows only and clears nothing (idempotent)
UNDO OK S598: 2 restored (3,50), 5 already equal (2,28,30,36,47), 0 refused as moved (-)   [the diff after: empty]
ok   C: a row whose detected_at moved since the JSON is refused by undo and said so (R1-C6); the others already equal
```
On the OLD files `rejudge_s598.py` refuses to run (not the S598 `stock_figure`) — red.

**Control 9 (the owner's lines after the re-judge) verbatim — the five with the clause (the other eight unchanged):**
```
ANKLE BINDER BAMBOO L: counted as arrived when the YUVIKA SURGICALS bill was scanned 07-10 17:14 -- not in Marg's purchases up to 18-10 (its bill YS…2627 of 07-10 carried ANKLE BINDER M BAMBOO, not this size)
KNEE IMMOBILIZER UNISON XL: counted as arrived when the YUVIKA SURGICALS bill was scanned 29-09 19:06 -- not in Marg's purchases up to 18-10 (its bill 672 of 28-09 carried KNEE IMMOBILIZER UNISON L, not this size)
KNEE SUPPORT HINGED XL: counted as arrived when the YUVIKA SURGICALS bill was scanned 29-09 19:06 -- not in Marg's purchases up to 18-10 (its bill 672 of 28-09 carried KNEE SUPPORT HINGED M, KNEE SUPPORT HINGED L, not this size)
KNEE SUPPORT HINGED XXL UNISO: counted as arrived when the YUVIKA SURGICALS bill was scanned 29-09 19:06 -- not in Marg's purchases up to 18-10 (its bill 672 of 28-09 carried KNEE SUPPORT HINGED M, KNEE SUPPORT HINGED L, not this size)
L S BELT CONT GRAY UNISON XXX: counted as arrived when the YUVIKA SURGICALS bill was scanned 07-10 17:14 -- not in Marg's purchases up to 18-10 (its bill 738 of 18-10 carried L S BELT M CONT GRAY UNISON, L S BELT XL CONT GRAY UNIS, not this size)
against the OLD files: 3 line(s) gone, 5 new; items added: ['KNEE SUPPORT HINGED XL', 'L S BELT CONT GRAY UNISON XXX']
```
The brief named three clause lines; the data gives five: KNEE IMMOBILIZER UNISON XL (the `KNEE IMMOBILI?ER UNI (family)` key, bill 672's L line) and L S BELT XXX are the rule working on two more families. The bill number in the clause is printed as Marg prints it (the full YS… number on the owner's page; masked here).

**Control 10 (the staff screens) verbatim:** every page read 200 for its login — reception (/porders, /porders/api/state, /s454/order, /s454/maal, /s454/order/YUVIKA SURGICALS), Darpan (/stockmatch, its api/state, /darpan/kal, its api/day), Amir (/amir, steps 1–7), Shavez (/reports/aaj), the owner (needs-you, /stock/api/now, /porders/api/state).
```
_orders: order 1 line 3 state open (open lines 6 -> the 'all' button shown); order 20 line 50 state open (open lines 3); the page's 20 newest received orders hold order 1: False, order 20: False; the card [('ANKLE BINDER BAMBOO M', 1), ('RIB BELT UNIVERSAL UNISON', 1)]; on order {'KNEE SUPPORT HINGED XL': 2, 'L S BELT CONT GRAY UNISON XXX': 1}
ok   C: (i) order 1's line 3 reads 'open' again in _orders (reception's Orders card) and the 'all' button is back (open_lines > 0); order 20's line 50 likewise
ok   C: (ii) on order: Yuvika KNEE SUPPORT HINGED XL x2 and L S BELT CONT GRAY UNISON XXX x1 are counted again (_on_order)
ok   C: (iii) the orthotic shortage card no longer lists KNEE SUPPORT HINGED XL 2 or L S BELT CONT GRAY UNISON XXX 1
ok   C: against the OLD files' dumps the ONLY differences are the three states ... and the owner's arrival lines; no word differs on any staff page (6 page(s) differ)
```
The six pages that differ, each by state only: reception's and the owner's `/porders/api/state` (lines 3 / 50, the card's two items, `ortho.n` 4 → 2, on order); reception's `/s454/order` ("4 dawa" → "2 dawa" on the Yuvika card's heading); reception's `/s454/order/YUVIKA SURGICALS` (the two lines `KNEE SUPPORT HINGED XL 2 nag`, `L S BELT CONT GRAY UNISON XXX 1 nag` gone); Darpan's `/darpan/kal/api/day` (the same card: `n` 4 → 2, the two items); the owner's needs-you (`Orthotic shortages: 4 items` → `2 items`, count 30 → 32, the arrival lines). The charter-7 note: the *Orders* card page lists the 20 newest received orders — orders 1 and 20 are older than those today, so the re-opened lines are in `_orders` (what the card reads) but not on the page's first screen.

**Control 11:** `figures()` for 414 names (the master and the orthotic items) equal OLD vs NEW on the copy, 0 moved (line 3's and line 50's units are scan-tied arrivals again, already expired → 0). `/stock/api/now` byte-equal. **Controls 3–6 (synthetic, on a second spine copy):** A ×4 / B ×2 under one key → each line its own (units 4 / 2); A's mark written → B still carried, both marked by the same bill (A 4, B 2 packs); two lines of one renamed item on one bill line → the second None; a single-member key with a clipped bill spelling (`W598 CLIPTEST ITM` for `W598 CLIPTEST ITEM XYZ`) → carried by the key, the second line None; two batches → one hit, qty 5 + free 1 = 6, one `billed_qty` 6. No REAL single-member pair whose bill spelling falls outside its forms exists on the copy (0 found; the synthetic pairs stand for them). **Control 12:** every grep green. **Control 13:** the spine copy's schema and bytes unchanged; `selftest_spine` 50 checks OK.

### The data step on live (09:54) — before / after

| line | item | before (S593, 08:03) | after |
|---|---|---|---|
| 2 | ANKLE BINDER BAMBOO M | billed 1 by YS…2627, supplied 1, short 1 | unchanged (agree: the `ANKLE BINDER M BAMBOO` line, qty 1) |
| 3 | KNEE SUPPORT HINGED XL | billed 6 by 672, supplied 6, short 0, arrived_by marg | **cleared:** billed_* NULL, detected_at NULL, supplied NULL, short 0, arrived_by / arrived_at NULL |
| 28 | CROCAL | billed 24 by 3463, supplied 24, short 1 | unchanged (agree) |
| 30 | PREGHYPE NT TAB | billed 24 by 3463, supplied 24 | unchanged (agree) |
| 36 | BRUTAFLAM GEL | billed 24 by GPPPL3679039, supplied 24 | unchanged (agree) |
| 47 | CAST SHOE M TYNOR | billed 1 by YS…2627, supplied 1 | unchanged (agree) |
| 50 | L S BELT CONT GRAY UNISON XXX | billed 1 by YS…2627, supplied 1, short 0, arrived_by marg | **cleared** (the same columns as line 3) |

`REJUDGE OK S598: 7 row(s) re-judged, 5 agree (2,28,30,36,47), 2 cleared (3,50)` — identical to the walk's result on the copy (the installer compares the two lines and would have restored on a difference). `purchase_order.status` of 1, 10, 13, 20 `received` before and after. Two audit rows `line_rejudged_s598` (who `s598`, refs 3 and 50, before / after and the hit inside). `detect_supplies` once after: wrote 0 lines. The state AFTER (the live files on a fresh copy): open lines 16 → 18 (3 and 50 back); order 1 open lines 5 → 6, order 20 2 → 3, the `all` button shown on both; the card 4 → 2 items; on order gains XL 2 and XXX 1; the owner's arrival lines 11 → 13.

### Backups, restarts, lock

- `finance.db.bak_S598_20261019_095314` (40,722,432 bytes, the backup API, mode 600); `stock_figure.py.bak_S598_92367a19`, `stock_watch.py.bak_S598_c5f3ce21`, `porders.py.bak_S598_78ea72be` beside the files.
- **The rows' JSON:** `/root/finance/purchase_order_line.bak_S598_20261019_095314.json` (3,705 bytes, md5 a0d31a256afd3cdabdcdf1a4b3a54166, mode 600) — the seven rows whole, as they stood at 09:54 before the re-judge. `undo_s598.py --db /root/finance/finance.db --json <that file>` puts them back (refusing a row whose `detected_at` / `arrived_at` moved since); never run.
- `clinic-finance` restarted once at 09:54:13 IST. Nothing else restarted.
- The build lock `/root/deploy/.claude_code_build.lock` taken 09:53:14 by S598, released 10:00:20 IST after the publish; `/tmp/s598kit`, `/tmp/s598probe` and the installer's scratch removed.
- **After the publish (commit 107eb68 — it also carried the chat's pending `KB_canon_all` files, as PUBLISH_ALL does):** the clone `/root/deploy/repo` pulled to 107eb68; the kit in the clone passes its SUMS and every file is byte-identical to the copy that ran from `/tmp/s598kit`. Live md5s re-read at 10:00: cb577821 299c3ef7 e5a5c4d4; healthz 200, the service active; no error line in the journal since 09:54; `DOCTOR_AUTO_OFF` absent. (This report's final text goes up in a second publish right after.)

### Not done, decisions made, and findings outside the brief

- **Not done:** `DUTY_MAP.md` / `DUTY_MAP.json` are not changed — no duty is added, moved or removed (CLAUDE.md "every duty has a door" rule 1); the family split in `shelf()` / `marg()`; the 27-letter lumps; `expected_units` and 4b-2's files; `order_sheet._every_read` was not used (it does not exist) — `detect_supplies` was run directly on live, as S593 did (`cron_pass` would also send notices).
- **Decided (the brief left it open or the data differed):**
  - **Line 50 cleared beside line 3.** The brief expected "the other six agree" and read the belt family as "one lump in 27 letters". That holds for the OLD spellings (`L S BELT CONT GRAY UNISON X`); but bill YS…2627 of 07-10 was re-exported on 18-10 under the NEW names and its belt line prints `L S BELT XXL CONT GRAY UNI` — the XXL size by name (the ticked partner of `L S BELT CONT GRAY UNISON XXL`, rename 8), not XXX (whose partner is `L S BELT XXXL CONT GRAY UNISO`, rename 9). Under the brief's own rule a bill line answers only the size it names; the re-judge clears the row the rule disagrees with (§3.5), and §7 names exactly this behaviour change. So line 50 is cleared, the walk asserts it, the installer compared the live result with the walk's, and the owner is told (§ for the owner, item 2). For the chat: either Yuvika billed XXL for an XXX order, or the XXX ↔ XXXL rename is not what Marg did — a Marg bill naming XXX / XXXL is the only thing that closes it.
  - `short` is set to 0, not NULL, on a cleared row — the column is NOT NULL and 0 is what an open line holds (found by the first DRY run; the brief said NULL).
  - `_family_bill` does NOT exclude a bill line already credited to the sibling order line (R1-C9 said "not in taken"): the brief's controls 2 and 9 expect the clause for ANKLE BINDER BAMBOO L whose only family line (the M line of 2627) is line 2's; the clause says what the bill carried, which is true either way.
  - The owner's clause names the **newest** family bill in the window, as the brief says — for L S BELT XXX that is 738 of 18-10 (M, XL), not the scanned 2627 (XXL).
  - The clause is built once (`more`) inside `arrival_needs_you` and used by both words lines — four anchored edits in stock_watch.py (the docstring, the clause, the two words lines), not one per words line; charter 8 "words built once".
  - `marg_purchase_rows.py` pinned to today's bytes (41d68148) since the brief named it without a hash.
  - Control 1's line-1 check: on bill 672 the ANKLE BINDER key has only the L line, so OLD and NEW units agree (1); the control is red on OLD by the absence of `seq` / `name27` — a weak negative, stated.
- **Finding — a fifth clause line, KNEE IMMOBILIZER UNISON XL:** its key is the rules family `KNEE IMMOBILI?ER UNI (family)`; bill 672 carried `KNEE IMMOBILIZER UNISON L` (line 7's, by S537) — the new rule names it for the XL line. True; not in the brief's list.
- **Finding — the *Orders* card's reach (charter 7):** `porders.state` serves `received[:20]`; orders 1 (26-09) and 20 (07-10) are not among the 20 newest received orders today, so the re-opened lines are in `_orders` and on reception's `/porders/api/state` only through the orthotic card and on order — not as visible order cards. Named, not changed.
- **Finding — no real key-fallback pair exists on the box** (every billed single-member line's bill spelling is inside its forms); the walk's three synthetic pairs stand for control 5. Named in the walk's output.
- **Permissions:** nothing asked or refused on the server. On this PC one PowerShell line was refused (it carried `Remove-Item -Recurse -Force` to drop a local `__pycache__`); python was run with `-B` instead and no cache was written. No memory note was saved beyond what exists.

### Charter

- **Retired:** `_purchases_of` (the by-bill lump) → `_purchase_lines_of`; `_taken_bills` (per bill) → `_taken_lines` (per bill line, keyed on the match); rule (a)'s by-bill query → the same lines read; `detect_supplies`' key-level `SUM(qty)+SUM(free)` → the matched line's packs from `carried()`. One rule, one place, one match function (`_matches`, the only place a `name27` is compared with forms).
- **Left (named):** sizes that agree in their first 27 letters on an OLD-spelling bill (R1-C3); the designed end state of a sibling line with no bill line of its own name — None → counted as arrived until expiry → the owner's line, `open` on a `received` order where every staff door says `not_sent`, closable only by a Marg bill naming the size (the D712 gap; today XL, XXL, ANKLE BINDER BAMBOO L, L S BELT XXX, KNEE IMMOBILIZER UNISON XL); the family split of a shared key's movements in `shelf()` / `marg()`; the order line's own 27-letter match in `_arrivals` / `scan_lines` (charter 12, SEEN); the stock proof's family handling (`stock_app`); 4b-2's files; S537's older marks (line 1 agrees, read-only); the *Orders* card's 20-order reach.
- **Charter 5:** the re-judge set columns NULL / 0 only on rows the SYSTEM wrote (`arrived_by='marg'` with S593's `line_detected` audit row); the JSON and the `line_rejudged_s598` audit rows are the old rows kept and marked.
- **Behaviour changes (rule 4, 1b, 7):** a sibling size with no bill line of its own name is "not in Marg's purchases" with the family's bill named; `billed_qty` is the matched line's packs, never a family sum; one bill line is credited to at most one order line of an item; two of S593's seven marks corrected on install and three screen STATES returned to their pre-08:03 shape for those two lines (no words).
- **Dependency state at install:** S593 live (porders 78ea72be), S594's crontab line in, the four renames ticked (`verified`), the spine 13/13 and 2 min old, `order.source = marg_sheet`, count basis; the 18-10 09:37 start capture `pending` (unrelated to this kit).
