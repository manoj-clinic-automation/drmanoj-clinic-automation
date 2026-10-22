# S618_SCAN_QUALITY — every pharmacy bill the right way up; bad scans sent back and rescanned

Brief: `claude_code_briefs/S618_SCAN_QUALITY.md` (v2, the Sanjeevni chat, session 335; R1 folded in). Runs after S613_S605_FOLLOWUP (two of
its FROM pins are S613's TO). The owner's word: "Yes" (22-Oct 07:09 IST) to the scan fixes; "they should go in before the buying model" (07:46).

## What it does
1. **Upright on the server.** After a pharmacy scan is read, Claude (Haiku; Sonnet once on an unreadable answer) is asked a short second
   question — which way each page's text runs, whether the whole bill and its total are in the scan, whether it can be read
   (`claude_reader.check_scan`, its own call path: never `read()`'s model loop, never `claude_reading`, never `read.claude_model`; every call
   counted against `cap(con)`). The answer is kept in `assets.db` table `scan_lie`, keyed by the FILE checked. A page whose text does not run
   upright is turned by its `/Rotate` into a NEW file `bill_<hex>_u.pdf` (the old file stays), set by compare-and-set
   (`UPDATE … WHERE source_stored=<the file checked>`; a join that changed the file meanwhile → the current file is checked and turned
   instead). pypdf / Pillow in the process when they import, else `/root/wa/venv/bin/python3` (S441's `_merge_pdf` pattern). `fp` / `fpc`
   are not recomputed. One `bill_audit` row `upright {pages, from, to}`.
2. **The phone stops a badly blurred photo** (`scanner_widget.js`, the OpenCV path only — `autoAddCV`'s `go()`, which camera, gallery import
   and Retake all pass through): the 3×3 Laplacian variance of the page as it will be saved, shrunk to 600 px by OpenCV's own area average.
   Below `scan.blur_min` (default **650**, the walk's calibration; sent in `SCANNER_CONFIG.blurMin`) the page is not added and the phone says
   *"Photo saaf nahi — phir se lijiye"* with Retake. Two refusals in a row of the same page slot → the third photo is kept and its upload
   carries `blur_kept=1` (→ `scan_lie.blur_kept`, listed as blurred). Not in `autoAdd`, `adjustDone` or PDF / file (named: they bypass it).
   No "whole bill" refusal (R1-B2): a cut-off bill is caught by the server. `arOK` / `guideRect` read `CFG` at call time; the intake puts
   `expectAspect` in `SCANNER_CONFIG` itself on a pharmacy link.
3. **One rule, one table of words** — `/root/shared/scan_quality.py` (new, pure): `verdict(bill, reading, lie, settings)` → `not_bill`,
   `blurred`, `cut`, `no_total`, `not_adding` (₹50 / 5 %; a challan exempt from the money rules) or nothing; computed on every read, never stored.
   Imported inside functions, fail-soft (never at the top of `porders_s454`).
4. **Send it back, rescan it.** *Scans to redo* (`/finance/porders/s454/scans`, the owner in English, `porders.rescan_askers` — default
   `shavez` — in Roman Hindi): the open asks, and every pharmacy-lane scan since `scan.redo_since` (2026-10-08) with a verdict and no ask;
   each with its thumbnail (`?v=<scan_lie.at>`), the reason's words, *Get it rescanned* (blurred · cut off · not a bill) and *Open the scan*.
   Its read writes nothing. The ask (`finance.db` `scan_rescan_ask`, made by `OS.ensure`; only `done_*` / `withdrawn_*` ever set) lands on the
   home of the logins in `porders.rescan_doers` (default `reception,alisha,shivani` — not Darpan) as *Phir se scan karo* above *Bill scan karna
   hai*; its *Scan karo* opens the intake with `rescan_of` and the old bill's month. In `_create_intake_bill`, in the same transaction as the
   INSERT and before the fingerprint guard, the new scan gets `bills.rescan_of` and the old one is set aside *"rescanned as B-xxxx"* (kept, its
   file kept). `rescan_of` rides the first Save only (cleared as S531 clears `challan`). `order_sheet.tie_pass`, before its loop: the old scan's
   order tie is re-pointed to the rescan (`scan_at` kept; never a new tie), the people's decisions copied (never moved), and every open ask
   whose scan has a rescan is closed — any lane, any kind, tie or no tie.
5. **The backfill** — `backfill_s618.py`, keyed and idempotent: every pharmacy-lane scan since 08-Oct, not set aside, not a joined page, with
   no check of its file; run once on the scratch copy (the walk) and once on live after placing (the venv python); a second run does nothing.

## Pins (FROM → TO, in PINS.sh)
| file | FROM | TO |
|---|---|---|
| /root/assetapp/asset_register.py | f29ee515 | PINS.sh |
| /root/assetapp/scanner_widget.js | 10a8bb29 | PINS.sh |
| /root/assetapp/claude_reader.py | 3894dc23 | PINS.sh |
| /root/finance/porders_s454.py | 34bab464 (S613's TO) | PINS.sh |
| /root/finance/order_sheet.py | c7fe2561 (S613's TO) | PINS.sh |
| /root/shared/scan_quality.py | (new) | PINS.sh |

Read only (STOP if moved): claude_reread ed7023d2, sorting_desk 110335ea, clinic_papers 6db07c12, purchase_app 447b745f, porders b1736494,
stock_figure 8c66b6b1, stock_watch f0d9092a, item_check 6f3faf89, darpan_kal d6ba4882. Printed: packs.py, /root/shared/scan_checks_s441.py.
Proved unmoved at the end: finance_app.py, portal.py, tile_grants.json, the crontab, every published S5*/S6* kit folder.

## Databases
`assets.db`: `bills.rescan_of INTEGER` (init_db's guarded column list) and `scan_lie` (CREATE TABLE IF NOT EXISTS in init_db) — made by the
Scan App itself at its restart. `finance.db`: `scan_rescan_ask` (order_sheet.DDL, made by OS.ensure). No DELETE, no hand edit;
`bills.status` keeps its four values. Backups: `finance.db.bak_S618_<stamp>`, `assets.db.bak_S618_<stamp>` (backup API), the uploads folder's
file list, and `<file>.bak_S618_<from8>` beside every replaced file.

## Services
`assetapp` then `clinic-finance`, each restarted once; `DOCTOR_AUTO_OFF` around the restarts; the build lock taken at the gate.

## Files
- `make_s618.py` — the anchored builder (25 edits; each anchor once, else it stops); the blocks it inserts: `s618_reader_block.txt`,
  `s618_ar_block.txt`, `s618_widget_block.txt`, `s618_os_block.txt`, `s618_p4_block.txt`; `scan_quality.py` (placed as is).
- `walk_s618.py` — the walk (scratch copies only; Claude real on the labelled set, stubbed for the synthetic scenes; `--expect-red` on OLD;
  `--facts` for the installer's live facts). `backfill_s618.py`. `install_S618_SCAN_QUALITY.sh`. `PINS.sh`. `SUMS.md5`. `KIT_ID.txt`.
- `walk/run_browser_walk_s618.py`, `walk/harness_s618.js` — the phone walk (headless Chrome on the PC; the box has no browser);
  `walk/walk_results_s618.txt` — its output.
- `DUTY_MAP.json` (v18: `reception.rescan`), `DUTY_MAP.md` — the copies the walk read (the clone's `claude_code_briefs/` carries the same).
- `S335_SCAN_VISUAL_AUDIT.json` — the eye's labels of 54 scans (stamps, vendors, orientation, sharpness, cut); no number, no image.

## Undo
Put back the five `.bak_S618_<from8>` files, move `/root/shared/scan_quality.py` aside, restart `assetapp` and `clinic-finance`, healthz 200.
A turned scan keeps its new file unless reversed from its `upright` audit (`from` / `to`) — only where `source_stored` still names the `_u`
file. The new column and tables stay, unread.

## For the parent's backlog
`/root/shared/` is in no nightly code bundle — `scan_quality.py` (and `scan_checks_s441.py`) need the bundle's list and the pin check.
