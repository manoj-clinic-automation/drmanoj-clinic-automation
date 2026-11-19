# START HERE — SESSION 490 — written at the S485 close (the Sanjeevni chat), 19-Nov-2026 06:1x IST

**Project: Sanjeevni — Pharmacy & Marg.** Open it in a fresh chat in this project, linked to manojz. Live from S485: **batches on the item ledger** (S883 20:15 18-Nov — https://followup.dr-manoj.in/finance/sanjeevni/ledger : each item's batches with expiry, the batch on every line, month folds, totals in words). Nothing of this project is DECLARED-PENDING (the 19-Nov bundle confirmed S864 – S883).

1. **The open:** `OPEN_ROUTINE_v1` — never `git` in the device shell (F-1467); scratch in `/tmp`, removed after; `df /sessions` once. Session **490 (RESERVED at the S485 close)** — take it by a SHORT `db_str_replace` append on `board/_numbers` `session_note` (it returns the version); then ONE pinned `update` of `session_next` if it is not already past 490. **Never a `!=` probe; never `db_get` of `_numbers`** (F-1478, F-1501). The figures at this close: `D1020 · F-1503 · A-D94 · kit S891 · session 491` — the parent's S489 close will move them; read them from the append's neighbouring close line only if needed. The day's checks (`python D:\Downloads\_kbtools\day_open.py --read`, run only when the page is not today's); remind him once of the packs page (D713).
2. **The bundle:** nothing pending here. If the day page shows a MISMATCH on a `/root/finance` pharmacy file, read whose kit it is before calling it drift.
3. **THEN LIST TO HIM — short, one line each, his to order (D1012; Runbook §2B items 2–8):**
   - the buying switch — read the weekly score (server only); earliest ~22-Nov;
   - the diagnosis on the inline record — S878 is live; one read on the Hub;
   - the 20 items whose batches do not add up to Marg — after Amir's next Batch Stock;
   - ZIBON EXTRA / GEMCAL XT (Darpan's count) · Yuvika 803 and KT ROS DT (Amir);
   - Stock Register first use (Ram Singh → Shavez);
   - PARKED: the AutoHotkey runner · the order-list kit (D976).
   Then build whatever he picks.
4. **Hands off:** `records.py` (the parent's, read only); the records page's own muddle (F-1466, the parent's); `stock_batch_now` written only by the Expiry watch.

**Kit pattern reminders:** after `device_commit_files` read the PC's md5 back before use, SUMS included (F-1477, F-1500); long VM jobs in the foreground with `timeout`, or sampled (F-1479); a gated healthz answers 302 = mounted (F-1463); no confirm dialogs on his pages (F-1464); frozen proofs judged per check (F-1465); made-up numbers built at run time (F-185); patient DB copies stay in the device VM `/tmp`, removed at the close. The built-in browser is signed in as manoj (checker) — read live through `fetch` from the Hub's own origin.

**Close:** `CLOSE_ROUTINE_v1` — copy `03_WORKING_PAPERS\S485\close_parts\close.json`, change what changed; `close_build.py` then `--place`; one board batch; project knowledge gets the entry point, the brief, the close report (F-1458); the publish named once.
