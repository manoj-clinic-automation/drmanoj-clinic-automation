# S570_PROOF_MORNING_WINDOW — brief for Claude Code (v1)

*Written 16-Oct-2026 by the Sanjeevni chat (session 316) at the owner's "yes" (11:08 IST) to the repair REPORT_S569 named. Read `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` (v1.1), `CLAUDE.md`, `deploy_kits/KB_canon_all/BUILD_NORM_v1.md` and `claude_code_briefs/REPORT_S569.md` (§A3–A5) first. Kit shape: S537's. Line numbers: the live bytes at S569 (stock_app.py `f58e09db…`; `_s524_tryable` 8530–8540 in the 15-Oct bundle — find by name).*

## 0 · For the owner
1. **The check of Amir's stock vouchers never gets a verdict on a normal morning.** It trusts a sale (or purchase) report only if it was exported *after* the closing stock. Every morning the sale report comes first (~05:10) and the closing second (~05:17), so the newest closing is never judged. Both reports cover the same day — the system's own rule for morning exports (before 09:00 = the end of yesterday) already says so; this one check ignores it.
2. **After this kit** a report covers a closing when, by that same morning rule, it stands for the end of a day at or after the closing's day. The check then judges as soon as the day's sale report, closing and a purchase report that reaches that day are in. A purchase report exported before the day ended (15-10 09:10 for 15-10) is still, rightly, not enough — its later purchases are missing.
3. **The owner's waiting sentence tells the truth:** it names the closing the check actually uses (16-10 05:17, not a mid-day snapshot of 15-10 10:11) and the report actually awaited (today: Amir's purchase report), never a report that has already landed.
4. No staff screen changes. Amir's card is untouched (the verdict is the owner's line only, D708).

## 1 · Numbers and pins
- Kit **S570_PROOF_MORNING_WINDOW** (board `_numbers` v453 → v454, PLANNED line). **F-905** (the reach rule), **F-906** (the waiting sentence) — repaired by this kit. Project: Sanjeevni.
- **FROM pin:** `/root/finance/stock_app.py` **f58e09db** (read the full md5 at the open; different = STOP, report).
- Read only: `/root/finance/spine/*`, `amir_day.py`. Services: `clinic-finance` restarted once. The build lock.

## 2 · The edits (stock_app.py only)
### 2.1 F-905 — `_s524_tryable(c, reach)`
Keep `last_sale >= end_day` and `last_pur >= end_day` as they are. Replace each stamp comparison by: **the export covers the closing when** `sale_stamp > c["stamp"]` **or** `_s524_end_day(<that export's covered day>, _s524_stamp_iso(sale_stamp)) >= end_day` — the estate's one capture rule (charter 11), exactly as REPORT_S569 §A4 states; the same for the purchase pair. For the sale side the covered day is `reach['last_sale']`, for the purchase side `reach['last_pur']`; `_s524_end_day` returns None for a same-day capture inside shop hours — None never covers (no `None >= str` comparison). Checked by the chat on f58e09db: sale 15-10 captured 16-10 05:10 → end 15-10 (covers); purchase to 15-10 captured 15-10 09:10 → None (does not); purchase to 16-10 captured 16-10 11:10 → None, but the old clause (stamp after the closing) covers it. Use the helpers that exist (`_s524_end_day` 8485, `_s524_stamp_iso` 8477); if their names or signatures differ from the report's, use the existing capture-rule helper the spine itself uses for closings and say which. No other change to the proof's logic, its cache key, its verdict or the S528 "newest capture says wrong" rule.
### 2.2 F-906 — the waiting sentence (`_s488_why`, `_s488_first_push`, the stage text)
- `closing_at` / `closing_day` come from the closing the proof is waiting on (the spine's clean closing `c`, its stamp), never from a `stock_feed` push the spine skips as a mid-day capture.
- The "waiting for …" words name what `_s524_tryable` reports short: `sale` → the day's sale report (Shavez); `pur` → *"a purchase report that reaches dd-mm (Amir)"*; when the sale report for that day has already landed, never say it is awaited. English, owner's lines only.

## 3 · The walk (`walk_s570.py`, S537's shape; scratch copies of finance.db and spine.db; its own rows by key)
1. **The morning order:** a made-up day D: sale export captured D+1 05:10 (covers D), closing captured D+1 05:17 (end_day D), purchase export captured D+1 06:00 (covers D) → `_s524_tryable` True; the old file → False (control red).
2. **A true "not yet":** purchase export captured D 09:10 (covers D only partly) → False, `short == 'pur'`, both files.
3. **Nothing else moves:** the earlier closings (10-10, 12-10, 13-10 on the live copy) give the same tryable answer and the same proof table as the old file; S524/S528 walks (read-only) stay green.
4. **The live case, on the copy:** count #1 stage C → with the newest purchase export as on the copy (and again with a made-up purchase export captured 16-10 11:00 covering 1–16 Oct) — the lots' state, `why`, `closing_at`; with the made-up purchase: a verdict; print the wrong rows (item, need, moved). Expected KT ROS DT and VINBACTUM DS among them (REPORT_S569 trial); say what it shows, without asserting it.
5. **The sentence:** no "10:11" and no "made when its sale report lands" while the 15-10 sale is in; `pur` short → the purchase words. Control: the old file prints both.
6. Assert no run of 10 digits in the walk's own output.

## 4 · Install, publish, report
Gates → FROM pin → compile both pythons → walk + controls → backups (`stock_app.py.bak_S570_f58e09db`, `finance.db.bak_S570_<stamp>`) → place → md5 read-back → ONE restart of `clinic-finance` → healthz 200 → read `/api/pad/hub/1`'s `proof` on the box by the app's test client on a copy (as S569 did): state, why, closing_at, and any verdict rows. The owner is exporting a purchase report at ~11:10 IST 16-Oct: if it has landed (`mi_file` PURCHASE_*, received after 11:00), read the verdict with it and print the wrong rows. Red: restore, restart, healthz, report. Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`; `claude_code_briefs/REPORT_S570.md` (3–6 plain lines on top: the rule fixed; today's verdict or what it still waits for; the wrong lines if any); publish again.
