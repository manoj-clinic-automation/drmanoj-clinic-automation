# S933_STOCK_OF_RECORD — the one stock record every page reads (Session 504, the Sanjeevni chat, 22-Nov-2026)

**The owner's word (19:28–19:33 IST):** "a single truth for stocks needs to populate system data"; "everywhere our system should read the stock from this place only." Before this kit three readers (the Stock check page, the item ledger, the count judgments) each computed stock their own way and disagreed: the Stock check showed 53 items "needing a look", about 13 of them phantoms worth the quantity of a bill Amir keyed in Marg after Shavez's morning print (S504_STOCKCHECK_FINDINGS_v1).

## What is in the kit
| file | from | what |
|---|---|---|
| `stock_record.py` | NEW | THE STOCK OF RECORD: `stock_of_record` (one row per Marg item) + `stock_record_meta`, built by `build()`, read by `rows()` / `row()`; `--build` for the cron, `--check` to read its state |
| `stock_figure.py` | 8130315e → TO | `_s928_order_match`: the `arrived=1` gate dropped — the scan tie is the fact (a tap before the scan left `arrived=0` on 41 of 99 live ties; S928's bill-over-tap rule was silent on all of them) |
| `stock_check.py` | 42118289 → TO | `record()` reads the record only; `_lines_for` kept, unlinked (one release) |
| `stock_check.html` | ae61a18c → TO | the words on a row (a bill keyed after the print, Marg moved with no record, a sale before the print), two sections (Marg behind a bill; clinic consumables), the closing's day and the record's build time |
| `item_ledger.py` | 5fbb6020 → TO | the head figures (Marg stock / Expected) from the record when it holds the item; the body ledger unchanged |
| crontab | NEW line | `*/10 5-23 * * *` … `stock_record.py --build` (`# S933_STOCK_OF_RECORD`) |

## The rules the record applies
- **Marg's figure:** the newest accepted full closing report by its print stamp. Printed for an earlier day → the end of that day. Printed on its own day before 22:00 → the end of the day before (the owner's 18-Oct rule: a morning report is the end of yesterday) — no hold, no verification wait (S587's start-capture judge is not used here). From 22:00 → its own day's end. Plus the bills Amir keyed AFTER the print: a purchase bill dated within 21 days on or before the end day whose first appearance in his export (`purchase_bill.first_seen_day`) is after the print day is added whole; one first seen ON the print day is added only when it closes the closing's shortfall against the record (the ledger's reading, made exact). Plus the spine's own movements after the end day.
- **Shelf:** `stock_figure.shelf()` minus its arrivals — the last count carried forward alone (S928's rules unchanged).
- **Waiting deliveries**, each in one state from the data: `scan_not_in_marg` (the order's scan is not linked to any Marg bill: counts by the bill's read quantity, the tap when unread; a tap above the bill is the short supply), `tap_no_scan` (no scan tied; `carried()` rules a–e say Marg does not carry it), or carried (the scan is linked to a Marg bill the spine holds, or a Marg purchase line carries the tap) — never listed.
- **States:** agree · look · waiting · no_shelf · marg_behind (the figure would be below zero: a bill is missing on Marg's side — never a gap) · consumable (the owner's consumption list — never a shop difference).
- **Freshness:** rebuilt whole, in one transaction, when a fingerprint of its inputs moves (the spine's build stamp, the newest tap, tie, scan link, count point, Marg bill, the settings) or after 6 h; a page read rebuilds it when stale and the connection is free; the cron keeps it fresh between reads. The ledger never rebuilds inside its request (`refresh="never"`).

## Proofs
- `synth_s933.py` — made-up spine with two closing reports (Sat as on Fri; Sun same-day morning), bills first seen on / after the print day, scans with `arrived=0` ties, counts, a consumable: 25 checks (R0–R19). The control on the old files: 17 red.
- `liveshape_s933.py` — the record built on COPIES of the live databases beside the old page's figures; prints MEG QCS, PATOPAN DSR, FERONES HD, TYRO BR, FLUXIC P, PRETOL 8 old → new; gates: ≥ 200 rows, under 150 s, the new page's "need a look" not above the old's.
- The installer re-runs walk_s927, synth_s928 and walk_s930 on the new files (S837 not-worse rule); two walk_s930 lines are superseded (a delivery waiting for an UNCOUNTED item is now shown) and named in the script.
- Rehearsed on a made-up server: install DONE, second run ALREADY INSTALLED, undo back to the FROM pins, a forced red at [4/6] restored everything (files, cron).

## Install (the owner's one line on the VPS, after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s933kit && cp -rp /root/deploy/repo/deploy_kits/S933_STOCK_OF_RECORD /tmp/s933kit && bash /tmp/s933kit/install_S933_STOCK_OF_RECORD.sh
```
Undo: `bash /root/deploy/repo/deploy_kits/S933_STOCK_OF_RECORD/undo_s933.sh`

## Kit 2 (next): the other readers on the record — Darpan's count judgments (`expect_for_point`), the Hub's "Darpan counted" lines, the Expiry watch's Marg figure, the ordering engine's stock position, the Loss desk; `stock_figure.marg()` / `capture_at()` themselves on the record's rule; the retired feeds off (F-1562).
