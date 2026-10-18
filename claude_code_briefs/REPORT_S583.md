# REPORT_S583 — kit S583_ARRIVALS_ONE_RULE (installed 18-Oct-2026, 14:06 IST)

## For the owner

1. **The extra stock from scanned bills now goes away in time.** When reception scans a supplier's bill, the order's items still count as arrived (the ordering pages need that), but each item now stops counting when Marg's purchases show it — by the line's own Marg bill, by the same supplier's bill up to two days before the order, or by another supplier's bill from the order day on — or when a purchase report taken three days after the scan still does not show it.
2. **Twelve of the thirteen items from the S580 probe dropped at install** (TOLTRIS PLUS −500, CROCAL −300, FLACORT 6 −200, PREGHYPE NT TAB −200, PRETOL 8 −100, THIO Q AP −100, COCYP T SYP −10, POWERGESIC −5, and four Yuvika pieces −1 each). LINVIZ 600 stays until its three days run out on 20-Oct evening. The ordering pages and Darpan's spot-count judgments of these items follow the corrected figures.
3. **Nine new lines on your Needs-you**, in English, one per item that was counted as arrived but never appeared in Marg's purchases: TOLTRIS PLUS, FLACORT 6, THIO Q AP, COCYP T SYP, FINGER COT M, SOFT COLLAR NEOLIFE L, KNEE IMMOBILISER UNISON M, KNEE IMMOBILIZER UNISON XL, SHOULDER IMMOBILISE UNISON XL. Each says which bill scan counted it and up to which day Marg's purchases were read.
4. **Nothing changed for the staff.** Amir's "bill entry baaki" lines are the same (none today); Darpan's, Shavez's and reception's screens read word for word as before. A spot count of one of these items is now judged at once instead of being held "provisional".
5. **It works:** the walk passed 56 checks with 30 controls on the new files and every control went red on the old files; the service restarted once and answered healthy; the install printed the state before and after.

## For the chat

**Kit:** `deploy_kits/S583_ARRIVALS_ONE_RULE/` (make_s583.py 18 anchored edits, walk_s583.py, install_S583_ARRIVALS_ONE_RULE.sh, README.md, PINS.sh, KIT_ID.txt, SUMS.md5). Ran on srv1746119 from `/tmp/s583kit` (byte-identical to the repository's folder: `md5sum -c SUMS.md5` OK before the run; verified again on the server clone after publishing — see the end). Brief v3 followed as written; no D/F number.

**Live files, FROM → TO (md5 read back on the box after placing, 14:06:52 IST):**

| file | FROM | TO (read back) |
|---|---|---|
| `/root/finance/stock_figure.py` | cb5f24aacf7748752206619ce8bbb1e3 | 72b9135ab00db0af2fe8e54091147bb5 |
| `/root/finance/shelf_figure.py` | a544afda07b4632e9bc05e97c256dde6 | 14ef2c24e272ae8ea684615ae82b6cb5 |
| `/root/finance/stock_watch.py` | bc6885217a9f7ca7d8273021fcf6315a | 80896ce257b155f21429a559eec891b9 |

Read-only files, live md5 printed at the open (13:31 IST) and at the install (14:05 IST), unmoved: porders.py a5a823bf30661a4bf65ced39b2355500, order_sheet.py f00f0163bdd66a074c5af261c9b80a49, order_rules.py 79f21c1ee1f763b1ac06b370e3d77b79, stock_app.py f279a3be440878bb30e418c20a5cf608, amir_day.py 73882a8391fde24f31e07b0191c5bd89, loss_piles.py 2b9023fd06aadc0ddaef30e2f26eccb3, purchase_app.py 98f7d9f05bc06ef6be80181dd9be4c8c, item_alias.py 111a8e4877035e5a02665dd586e01b06, qty_words.py 706db7ccfa7489fb8d296f663590f107. The installer also proved stockmatch.py, porders_s454.py, darpan_kal.py, finance_app.py, the spine's three files, portal.py, tile_grants.json, DUTY_MAP.json and the crontab unmoved.

**Timeline (read from the installer's output):** build lock taken 14:05:51 IST by S583_ARRIVALS_ONE_RULE; spine passed 13/13, last success 14:00:45 (5 min before); walks green; state before/new printed; backups made; files placed; `clinic-finance` restarted 14:06:52, healthz 200 after the restart; /finance/amir, /stock/page/now, /stockmatch, /porders answered 302 to a plain curl (the login gate, expected); journal clean; state after printed; DOCTOR_AUTO_OFF removed; DONE. A DRY run (14:00–14:05) preceded it; its first pass found the bill-number fault below and was fixed before anything was placed.

**What the install changed in figures (the 13 items of REPORT_S580, `shelf()` old → new on the same copy of the live database, 14:06 IST):**

| item | arrived | shelf | receipt basis / provisional |
|---|---|---|---|
| TOLTRIS PLUS | 500 → 0 | 510 → 10 | shelf, 500 → 0 |
| CROCAL | 300 → 0 (carried by (c): Shivaaz 3463 of 01-10) | 497 → 197 | shelf, 300 → 0 |
| FLACORT 6 | 200 → 0 (expired) | 228 → 28 | shelf, 200 → 0 |
| PREGHYPE NT TAB | 200 → 0 (carried by (c): Shivaaz 3463) | 449 → 249 | shelf, 200 → 0 |
| PRETOL 8 | 100 → 0 (carried by (e): Kedar A000203 of 03-10) | 257 → 157 | shelf, 100 → 0 |
| THIO Q AP | 100 → 0 (expired) | 160 → 60 | shelf, 100 → 0 |
| LINVIZ 600 | 100 → 100 (inside its grace until 20-10 18:18) | 130 → 130 | shelf, 100 → 100 |
| COCYP T SYP | 10 → 0 (expired) | 10 → 0 | shelf, 10 → 0 |
| POWERGESIC 100 PATCH | 5 → 0 (carried by (e): Janta 23672 of 18-10) | 10 → 5 | shelf, 5 → 0 |
| FINGER COT M | 1 → 0 (expired) | 1 → 0 | shelf, 1 → 0 |
| SOFT COLLAR NEOLIFE L | 1 → 0 (expired) | 1 → 0 | shelf, 1 → 0 |
| SHOULDER IMMOBILISE UNISON L | 1 → 0 (the XL line expired; family share) | 2 → 1 | approx, 0 → 0 |
| SHOULDER IMMOBILISE UNISON M | 1 → 0 (as above) | 5 → 4 | approx, 0 → 0 |

The order engine (`_s470_inputs`, basis count) moved the same way: TOLTRIS PLUS 510 → 10, CROCAL 497 → 197, FLACORT 6 228 → 28, PREGHYPE 449 → 249, PRETOL 8 257 → 157, THIO Q AP 160 → 60, COCYP 10 → 0, POWERGESIC 10 → 5, FINGER COT M 1 → 0, SOFT COLLAR 1 → 0; LINVIZ 600 130 → 130 (equal, inside its grace). The voucher guard's "not judged against the shelf" count: A 0 → 0, C 0 → 0 (no line of count #1 is among these items). Amir's `bill_pending_lines`: 0 → 0.

**Every scan-tied unanswered line and what (a)–(e) say (21 lines; the walk's section 0):** carried by (d) — ANKLE BINDER BAMBOO M (Yuvika bill of 07-10), KNEE SUPPORT HINGED XL and XXL (Yuvika 672 of 28-09), BRUTAFLAM GEL (Gunina GPPPL3679039 of 06-10), CAST SHOE M TYNOR, ANKLE BINDER BAMBOO L, L S BELT CONT GRAY UNISON XXX (Yuvika's bill of 07-10); carried by (c) — CROCAL, PREGHYPE NT TAB; carried by (e) — PRETOL 8, POWERGESIC 100 PATCH; not carried and EXPIRED — FINGER COT M, KNEE IMMOBILIZER UNISON XL, SHOULDER IMMOBILISE UNISON XL, SOFT COLLAR NEOLIFE L (order 1, scanned 29-09), COCYP T SYP (order 18, 06-10), KNEE IMMOBILISER UNISON M (order 20, 07-10), THIO Q AP (order 22, 12-10), FLACORT 6 (order 25, 13-10), TOLTRIS PLUS (order 28, 14-10); not carried, inside its grace — LINVIZ 600 (order 38, 17-10 18:18). Tapped lines not answered by Marg: 0. Tapped lines answered by Marg (rule a): 84 — never counted, never on the owner's line. The named edge (a carrying bill dated on or before the count day): 0 lines today.

**The owner's lines at install (`stock_watch.arrival_needs_you`, 9, as printed by the state AFTER):**

- COCYP T SYP: counted as arrived when the SHIVAAZ FORMULATIONS bill was scanned 06-10 20:11 -- not in Marg's purchases up to 18-10
- FINGER COT M: counted as arrived when the YUVIKA SURGICALS bill was scanned 29-09 19:06 -- not in Marg's purchases up to 18-10
- FLACORT 6: counted as arrived when the KEDAR PHARMACEUTICAL bill was scanned 13-10 11:22 -- not in Marg's purchases up to 18-10
- KNEE IMMOBILISER UNISON M: counted as arrived when the YUVIKA SURGICALS bill was scanned 07-10 17:14 -- not in Marg's purchases up to 18-10
- KNEE IMMOBILIZER UNISON XL: counted as arrived when the YUVIKA SURGICALS bill was scanned 29-09 19:06 -- not in Marg's purchases up to 18-10
- SHOULDER IMMOBILISE UNISON XL: counted as arrived when the YUVIKA SURGICALS bill was scanned 29-09 19:06 -- not in Marg's purchases up to 18-10
- SOFT COLLAR NEOLIFE L: counted as arrived when the YUVIKA SURGICALS bill was scanned 29-09 19:06 -- not in Marg's purchases up to 18-10
- THIO Q AP: counted as arrived when the DEEPAM PHARMA bill was scanned 12-10 19:37 -- not in Marg's purchases up to 18-10
- TOLTRIS PLUS: counted as arrived when the SHIVAAZ FORMULATIONS bill was scanned 14-10 12:46 -- not in Marg's purchases up to 18-10

D712's lines (untied taps with no scan from that supplier): 0; `arrivals_open` on untied orders: 0 — no overlap. The owner's Needs-you JSON went from 22 to 31 lines (the 9 above).

**The walk (new files): `WALK OK S583: 56 checks, 30 controls green`.** Controls 1–11 of the brief, each green: TOLTRIS PLUS counted inside the grace (the grace raised to 30 on the copy and put back to 3), expired under the live export (scanned 14-10 12:46 + 3 d = 17-10 12:46; the purchase export taken 18-10 09:25:37 reaches 18-10 — past it), off the shelf, on the owner's line with the brief's words; CROCAL / PREGHYPE by (c); PRETOL 8 and POWERGESIC by (e); the order-32-style line (the walk's own third A.A. RYCOBAL D3 line, scan-tied 17-10 18:22) NOT carried — 467 answered order 21's lines, 474 order 32's — while a 7-day any-supplier rule would take 467; the raw-stamp trap (`'20261018-092537' > '2026-10-18T14:06:19'` is True — the trap says "passed"; `expired()` says False; the fresh tap counts 20); the order engine equal for LINVIZ 600 (130 → 130) and −500 for TOLTRIS PLUS (510 → 10); a Marg-answered row (RYCOBAL D3, bill 467) answered by (a), in_spine True, not in arrivals_open, not on the line; spine missing → carried None, expired False, taps 20 and the TOLTRIS scan line still 500 (nothing dropped while unread); the owner's lines one per scan-tied open arrival, no untied tap, `bill_pending_lines` equal (0 = 0); Darpan's receipt for TOLTRIS PLUS written on the copy: status settled, provisional 0, "1 patte · Marg se barabar" (the existing words; old files: provisional 500); the grep tests (no `scan_arrivals` in shelf_figure.py, no `supkey=?` in `_arrivals` / `bill_pending_lines`, `k20=? AND supkey=? AND date>=?` in none of the three files, `def carried` / `def expired` / `def scan_arrivals` once each in stock_figure.py, `_arrivals` marks in_spine by carried() only, the setting with seed=None). Staff screens: amir (/finance/amir, the pad), darpan (/stockmatch, its state, /darpan/kal), shavez (/reports/aaj), reception (/porders) — words unchanged against the old files' dump. The owner's /stock/api/now changed in the figures only (12 items' `ours` and `gap`; agree 343, differ 52); the owner's needs-you gained the 9 lines. No ten-digit run in the output.

**Negative control (the OLD files, same scratch copies): `WALK OK negative control S583: 30 controls red on the old files`** — every one of the 30 controls red, none "NOT RED".

**Found by the walk's first dry run (the kit was corrected before anything was placed):** the spine prints A.A.'s bill 467 as `0000467` while Marg's own answer on the order line says `467`; rule (b) compared them raw and did not see the bill as taken, so the order-32-style line was wrongly carried under (c). `carried()` now matches bill numbers with spacing, case and leading zeros folded (`_bill`). Also the shelf_figure header carried the word `scan_arrivals` in its pointer; reworded so the brief's grep is empty.

**Backups:** `/root/finance/finance.db.bak_S583_20261018_140551` (sqlite backup API, 40,259,584 bytes; no data step was made — the backup is the rule's), `/root/finance/stock_figure.py.bak_S583_cb5f24aa`, `/root/finance/shelf_figure.py.bak_S583_a544afda`, `/root/finance/stock_watch.py.bak_S583_bc688521`. Undo: the installer's last line (the three `.bak` files back, one restart).

**Services:** `clinic-finance` restarted once (14:06:52 IST). Nothing else. The `order_rules tick` and the 06:30 stock_watch job pick the files up on their next run. No DUTY_MAP change (no staff duty added, moved or removed). No crontab change. No data step; the new setting `arrival.back_days` has no row (default 2).

**Not done, and why:**
- `porders.detect_supplies` and `order_rules._s470_arrivals` were not touched (the brief 3.4: left with the owner's closure of the ordering flow as the reason).
- Nothing was written to the live database by the walk; the walk's own rows (W583 FIX TAB, the order-32-style line, Darpan's receipt for TOLTRIS PLUS) exist only on the /tmp copies, which the installer removed.

**Outside the brief, noticed (not touched):**
- ANKLE BINDER BAMBOO M (order 1, Yuvika, 26-09) is carried by (d) through Yuvika's bill of **07-10** (a ten-digit bill number, masked in the logs) — the key `ANKLE BINDER BAMBOO` is a family (L and M); order 1's own bill 672 answered the L line and is therefore "taken" (rule b), so the M line is carried by the later Yuvika bill that answered no order line. The rule does what the brief says; a units-based match (the brief's "for later") would decide whether that bill really held an M.
- Four of the nine owner lines are Yuvika orthotic pieces of orders 1 and 20 that were never on the 13-item list (they have no count base: KNEE IMMOBILISER UNISON M, KNEE IMMOBILIZER UNISON XL, SHOULDER IMMOBILISE UNISON XL; FINGER COT M and SOFT COLLAR NEOLIFE L were). They were counted as arrived on the ordering pages since 29-09 / 07-10 with nothing in Marg.
- The owner's `/finance/stock/api/now` summary moved from agree/differ counts that included the extra to agree 343 / differ 52 — the figures of record for 12 items changed, as the brief says they would.
- The witness file's `expected_units` column for these items changes from tonight (4b-2's start condition, named in the README).

## Charter

- **Retired:** `shelf_figure.scan_arrivals` (moved into `stock_figure` under the one rule); the supplier-key-and-date test inside `stock_watch._arrivals` and inside `stock_watch.bill_pending_lines` (two more copies of the rule); the old `stock_figure.taps` body. One rule remains: `stock_figure.carried` / `expired`.
- **Left (named):** `porders.detect_supplies`, `order_rules._s470_arrivals` — for the ordering kit and S486 B (they can now disagree with `carried()` for an UNCOUNTED item's transit); the D712 gap — an untied tap where the same supplier has an unrelated scan (D712 skips it, so does the arrival line); the 18-10 12:20 `s577_shelf_gap` set keeps TOLTRIS PLUS's +500 as a record, unflagged (the next end_day's set is the first correct one); `expected_units`' old-way column changes mid-week.
- **Left for later:** per-line arrival from the scanned bill's own lines (the Scan App's readings); units-based matching (one bill line answers at most its own units).
- **Seen, not touched:** the order line still matched by `pad_norm(name[:27])` (charter 12, as S577 left it); `amir_day._d712_owner_lines`; the ordering flow (S543/S561).
- **Dependency state at install:** spine passed 13/13 (last success 14:00:45 IST), `arrival.bill_grace_days` = 3 (its live row), `arrival.back_days` unset (default 2), `order.stock_basis` = count, Amir's `bill_pending_lines` 0, no provisional stock point, count #1 at stage C with A/C not-judged 0 / 0.

**Publish:** PUBLISH_ALL.bat run after this report; the server clone `/root/deploy/repo` pulled and the kit folder verified byte-identical to `/tmp/s583kit` that ran (`md5sum -c SUMS.md5`, `cmp` of every file). The build lock `/root/deploy/.claude_code_build.lock` (owner S583_ARRIVALS_ONE_RULE 14:05:51) released after that. `/tmp/s583probe`, `/tmp/s583_live.tgz`, `/tmp/s583kit.tgz` and `/tmp/s583kit` removed.
