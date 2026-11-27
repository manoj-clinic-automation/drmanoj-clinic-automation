# S973_VOUCHER_SCANS — Marg stock vouchers scanned on the pharmacy lane (kit C of S534_FINAL_BUILD_PLAN, D1091 plan 2.4)

**Board:** `_numbers` v2413 → v2414 (kit S973), PLANNED line v2415 (the Scan App's `claude_reader.py` and `asset_register.py`, D646).
Built in the Sanjeevni chat, session 540, 27-Nov-2026, on his "Proceed" (18:42 IST) on `S538_KIT_C_DESIGN.md`. Every FROM is the newest
bundle's (27-Nov 03:18) or S971's placed bytes (F-472).

**What it does.** A voucher's print is asked only when it is needed (plan 2.4):
- **A claim**: Amir answers *Pehle bana chuka hoon* on a claim card (kit B). Before this kit, that went straight to the owner. Now ONE print
  card goes on Amir's page (*Voucher ka print*), and it appears at once, without waiting for the 5-minute sync. The card has two choices:
  *Print diya — reception ko* (one tap) and *Khud scan karein* (the Scan App's intake on the pharmacy lane, carrying the voucher's number
  when Amir named one).
- **A cut name**: a line in Marg's Stock Issue / Receive report whose name is cut short and fits more than one item, dated on or after
  `stock.scan_ask_from` (the install day). This raises the same print card for that voucher number. Marg's one-item Stock Register is asked
  only when no print ask is open for that voucher: either the scan was unclear, or no scan came within the question days.
- **When Amir taps *Print diya***: reception gets the line *Stock voucher scan karna hai* on *Aaj ka bill kaam* (the line joins the count
  on reception's home row), plus ONE push to the reception logins (`porders.rescan_doers`).
- **The Scan App** files the scanned paper as kind **`Stock voucher`**, doc_kind `stock_voucher`. It is never kind `Pharmacy`, so Amir's
  enter list, the bill pairing and the scanned-not-in-Marg ask never see it. There are two roads:
  - **The link:** lane pharmacy + the voucher's number + no seller. The paper is marked at once and read by the pharmacy reader. If the
    reading says it is a bill, the paper goes back to `Pharmacy` and is read on the lane's own road.
  - **The reading:** any voucher scanned on the lane is recognised by its content.

  Either way the row is lent only the voucher's number (in Marg's form) and its date, never a seller or an amount.
- **What the scan settles** (`voucher_scan.py`, which reads assets.db READ ONLY):
  - The item at the asked quantity → the claim closes as *scan B-xxxx*.
  - The voucher Amir named, scanned, but lacking the item → back to Amir as the next round.
  - The item at another quantity → his call, with the scan named.
  - No scan within `stock.inq_question_days` → his call ("no scan came").
  - A cut line → its full name is written to `mi_voucher_name` with source *scan B-xxxx*, and the line reads "the voucher's scan".
- **Switches:** `stock.voucher_scan` = off on the Stock check page puts *Pehle bana chuka hoon* back on kit B's road.
  `read.stock_voucher` = off in the scan app's settings means nothing is marked. His cut-name date is a setting too.

**Files.**

| file | FROM | TO |
|---|---|---|
| /root/finance/voucher_scan.py | NEW | see TO_PINS.md5 |
| /root/finance/voucher_inquiry.py | ac76b9d3 (S971) | |
| /root/finance/voucher_judge.py | 6c725941 (S971) → v1.4 | |
| /root/finance/amir_day.py | 27a2a128 (S971) | |
| /root/finance/porders_s454.py | 3f52d1f3 (S958) | |
| /root/assetapp/asset_register.py | a325d0f4 (S890) — the Scan App's | |
| /root/assetapp/claude_reader.py | 5b27b226 (S841) — the Scan App's | |
| /root/shared/scan_quality.py | 505a114f (S765) | |

Every change is an appended S-block (re-binding, the established pattern), apart from these anchored edits:
- two kind tuples in asset_register (the edit page keeps 'Stock voucher' — the F-1422 lesson), and its intake page's two after-Save lines
  (a seller-less link's number dropped after the first Save);
- one line in porders_s454 (the server's rescan asks treat a stock voucher like a summary);
- two lines in voucher_judge (a name's source).

`make_s973.py` builds the files from the FROM bytes and the `block_*.py` beside it, with each anchor found exactly once.

**Proof.**
- **Sanjeevni walk:** `walk_s973.py` (kit B's own fixture, then 36 checks) gives **36/36**, twice on one layout.
- **Sanjeevni control:** on the live files, P1–P3 go red.
- **Regression walks on the new files:**
  - kit B 84/85 (its version line only: an answer before the install day keeps kit B's road).
  - A2 48/49, A1 39/41 and S965 31/32 (version lines only), the same as on the FROM files.
- **Scan App walk:** `walk_s973_app.py` on the REAL app (made-up rows, the reader's answer made up) gives **26/26**. The control on the live
  files is **16 of 16 red**. S841's walk 20/20 and S754's walk (0 failed) pass on the new files.
- **Rehearsal:** 13/13 on a made-up root (see `rehearse_s973.sh`).

**Install** (his publish, then one line on the server):

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s973kit && cp -rp /root/deploy/repo/deploy_kits/S973_VOUCHER_SCANS /tmp/s973kit && bash /tmp/s973kit/install_S973_VOUCHER_SCANS.sh

**The way back:** `bash /root/deploy/repo/deploy_kits/S973_VOUCHER_SCANS/undo_s973.sh`. It:
- withdraws the open print cards;
- puts claims that are waiting back on his call;
- restores the seven files and moves voucher_scan.py aside;
- restarts both services.

Papers already marked `Stock voucher` stay so, and `scan_quality.py` stays at its new version so they are never judged as bills.

**Cold review (separate agent): NOT SAFE, 4 MUST, all built in.**
- M1: a voucher would have become a 'rescan this bill' ask for reception. Now `scan_quality` and the server's asks treat it like a summary.
- M2: a named voucher scanned without the item could loop back to Amir. Now only a scan after the card counts, and a second miss goes to his call.
- M3: the reading thread could beat the link's mark. Now the thread marks the paper itself; a dealer's bill goes back with its own number.
- M4: a red after placing left the database's S973 writes behind. The put-back now withdraws them, as the undo does.
- Also built in: a reading with no Marg voucher number is never marked; the printed number wins over the link's; '6:11' quantities are
  kept as printed; a name already there must agree; only answers on or after the install day reach Amir; the undo closes open print asks;
  the link's mark has a short timeout; the log gate reads tracebacks only.

**Second look (separate agent): NOT SAFE, 2 MUST, both built in.**
- The scanner keeps the link's number for every later Save on that page. Now only the FIRST paper carrying it is the voucher's; a later
  one has the borrowed number cleared and is read as what it is.
- An undo or put-back now leaves `scan_quality.py` at its new version, so papers already filed 'Stock voucher' are never judged as bills.
- Also: a 'stock voucher' reading with no voucher number keeps no kind ('other' would have asked reception for a rescan); reception's
  line for a named voucher waits for a scan made after the card; times compared to the minute, as the scan app stamps them.

**Re-look (separate agent): SAFE TO INSTALL, 0 MUST.** Two of its SHOULDs built in: the intake page drops a seller-less link's number
after the FIRST Save (the same pattern as S618's rescan_of: the scanner never carries it to the next paper); a database error in the
"first paper" test marks nothing.

**Not touched:** `scanner_widget.js`, `/root/shared/scan_checks_s441.py`, `sarvam_ocr.py`, `purchase_app.py`, `stock_check.py`/`.html` (the
claim rows draw through `claims_view`; the settings through `SETTINGS`). No staff screen beyond the approved words of mock-up v7.
