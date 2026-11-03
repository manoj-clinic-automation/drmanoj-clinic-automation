# S704_SPINE_VOUCHER_FOLD — the buying model's step 3 (display only)

*Sanjeevni session 383 · 03-Nov-2026 · the owner's word at the S380 close (11:20 IST): "build in next session" — section 9 step 3, after the first scored levels week (scored the night of 1-Nov). F-1025 and F-1028.*

## For the owner
- **The spine's line on the health page** stops saying "stock = Marg EXCEPT 198 item(s)". Those 198 are exactly the items Amir corrected in Marg with his stock vouchers (count #1, 4-Oct to 15-Oct). Marg is right; the spine simply never sees a voucher. From now on a difference that equals the vouchers Amir filed is called a VOUCHER difference and leaves the EXCEPT list. Anything else still shows.
- **Your order fold ("How the list is made")**, from the next list on (09:00 tomorrow):
  - the line **"The last list stood on: sales to … · Marg's closing of … · spine built … · N counted / N on Marg's figure / N absent"** is drawn from the list itself (before, it was mostly missing, and when shown it came from whatever page last ran a plan, not from the list);
  - the **"made again"** line is in words — *"Made again at 12:50 on newer figures, 16 supplier lists: sales to 31-Oct-2026 · Marg's closing of 31-Oct-2026 · spine built 02-Nov-2026 12:40"* — not raw code;
  - a **carried short-supplied line** (RANIMIG 150 from Kedar, LANZOL JUNIOR from L.K.) now carries the day's model word, so the weekly score no longer shows a stray "fixed" column on a levels week.
- Nothing on any staff screen changes. No order quantity, supplier or rail changes. `order.source` is not touched (D673, D785). The score's own code is not touched.

## What changes — two files
| file | from → to | what |
|---|---|---|
| `/root/finance/spine/spine_build.py` | `1cd20ead` → `67d5693f` | `filed_vouchers()` reads Amir's filed vouchers READ-ONLY (the `--finance-db` door the build already opens); a finding equal to them is `VOUCHER`, not `OPEN`; the STOCK gate row's detail says how many; `BUILD_VERSION` S704.1 |
| `/root/finance/order_rules.py` | `5e8330b3` → `bdefd058` | one S704 section appended before the script tail (the S644 wrapper pattern): `plan()` gives a word-less line the day's model word; the list's inputs kept beside `made_through` (order_notice slot `inputs_note`); the fold reads them and says relist / stale in words |

`make_s704.py` builds both from the box's own bytes by anchored edits (each anchor exactly once, the FROM pin exact, else REFUSED). The voucher rule is shelf_figure's: the newest `stock_voucher_entered` row of a batch carries a voucher number; a voided batch never counts; the day is `entered_on`, else the day of `at`. Vouchers are **never** added to `sp_move` (the shelf figure would count them twice). An `--acceptance` build still refuses any difference.

## The proof
- `walk_s704.py --new`: **40 of 40 green** on made-up rows (the selftest's own made-up store; its own scratch databases): a filed voucher (three date shapes, `at` alone, two batches summing) → VOUCHER and no EXCEPT; no number, a cleared number, a void, filed after the closing, filed on the opening day, the wrong amount, another item → OPEN; sp_move / sp_check / every stock table the same with and without vouchers; the gate row's ok and blocking unchanged; acceptance still refuses; `selftest_spine.py` green; the fold: the carried word on levels / fixed and nothing else moved, the note kept at 09:00 and on a relist (not on "same", not without a note), the newest kept list read (never a later day's), the relist / stale / 0-rows lines in words, an odd text left as it was, every other fold key unchanged, never `order.source`.
- **Control on the live files: 19 S704 check(s) red · 21 green.** Five mutants of the new files: all five caught.
- **The proof (the installer runs it on the box, under the spine's own lock):** the spine built twice from the live readings, old and new file, the same finance.db read-only — every table and gate row equal, the findings equal, only their notes may move and only to VOUCHER; each VOUCHER item's figure compared with the plain net of its filed vouchers (a difference is printed; an alias or family key can explain one), and the proof is RED if the vouchers explain nothing while open items carry a filed net change; `plan()` three times on a COPY (old, new, old) — every steady line equal but a carried line's model word, every supplier's total / held / paused equal; the fold old vs new equal but for its inputs and the two lines in words. In the device VM on the 03-Nov database copy with a made-up spine: CLEAN (6 suppliers, 10 lines, all old = new). The 03-Nov copy: **198 items** carry a filed net voucher change — the EXCEPT line reads **198**.
- Rehearsed on a made-up root: DRY · install · ALREADY INSTALLED · a forced red at [7/7] restores both files and releases the lock · a changed live file refused at [2/7].

## Install (the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s704kit && cp -rp /root/deploy/repo/deploy_kits/S704_SPINE_VOUCHER_FOLD /tmp/s704kit && bash /tmp/s704kit/install_S704_SPINE_VOUCHER_FOLD.sh
```
It takes a few minutes (the spine is built twice for the proof, then once more for real). **Undo:** the installer prints the one line (both backups `*.bak_S704_*` back, finance restarted; the spine rebuilds itself within ten minutes).

## Named, not done
- Today's fold (3-Nov) gets its "last list stood on" line only if the list is made again before 13:00; otherwise from tomorrow's 09:00 list.
- The proof holds the spine's lock while it builds twice (a few minutes): one 10-minute spine refresh may be skipped.
- The status line does not say how many differences the vouchers explain (the gate row's detail does); `spine_read.py` is not touched.
