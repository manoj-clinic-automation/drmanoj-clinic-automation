# REPORT_S500 — S500_REPORT_CHECK installed, walked green, published (10-Oct-2026, 22:56–23:05 IST)

## For the owner

- **The test message reached your phone** at 22:57 IST (the installer's last step: *"Sanjeevni morning reports - test"*). From tomorrow you are told on the phone only when a morning report is wrong on its second try, or is not right by 10:00. A right morning sends nothing.
- **The morning page *Aaj ki reports* now carries the steps of both reports with Marg's own screens** (*Kaise banayein* on each row), says of each **Sahi hai** or **Galat hai · koshish 1 / 2** with the one step to redo and its picture, and gives a second try. On the second wrong try it says *Doosri baar bhi galat* and that you have been told.
- **A short closing stock is refused everywhere.** A list with fewer items than 90 percent of the recent closings (like the 250-item list of 06-Oct, every zero-stock item left out) is marked wrong on the page and is **not loaded** by the server: manojz's pusher is told "409 -- nothing recorded" and sends the next full export instead.
- **What the page says of today's two reports** (read back on the box at 22:57 IST): *Sale report: ok · Closing stock: ok (two tries, none wrong)* — this morning's REPORT-login exports read right.
- **Amir's renames have NOT opened yet.** His orthotic vouchers are now judged on the newest closing (09-10) instead of the first one after them (04-10). On the 09-10 closing two items still do not move by their vouchers: **L S BELT CONT GRAY UNISON L** (Marg 2, should be 3) and **L S BELT CONT GRAY UNISON XXL** (Marg 3, should be 2) — the L and XXL look swapped in Marg. The two items the old check named (ANKLE BINDER BAMBOO M, TYNOR WRIST SPLINT RT M ELAST) are now right. Once Amir sets the two belts right in Marg and the next WHOLE closing shows it, his renames open by themselves.
- Darpan, Shivani and Alisha can open the page by its address but have no *Aaj ki reports* tile on their home (the tile file is the clinic chat's; Shavez, Amir and the doctors have it).

## For the chat

**Kit** `deploy_kits/S500_REPORT_CHECK/` — published in `99d7f6a` (`PUBLISH_ALL.bat`, 23:01 IST). The clinic chat's `PUBLISH_ALL` runs of 22:4x–22:5x (`f7feb1b`, `8d160de`, their kits S509–S512) committed two in-progress copies of this kit's files while it was being built; the final kit (the one that ran) is `99d7f6a`. The clone's installer answers **ALREADY INSTALLED** (23:03 IST); `diff -r` between `/tmp/s500kit/repo/deploy_kits/S500_REPORT_CHECK` (what ran) and the clone's copy is **empty**; `md5sum -c SUMS.md5` 9 of 9 OK. `NO_PHONE_NUMBERS.py` clean over the ten files. No `__pycache__` in the kit. The four given parts are byte-identical to `claude_code_briefs/S500_parts/` (md5s in `SUMS.md5`).

**Pins read back on the box (22:56 IST)** — FROM → TO:

| file | FROM (live, before) | TO (read back) |
|---|---|---|
| `/root/finance/reports_tile.py` | 6f7cf490c949495e3e714b7dd688b7af | 01f67f4d034cdefd2d9254263e47828e |
| `/root/finance/stock_app.py` | cc06dac9e3ab60a85d76e2409815b5af | bfc2a40bff0d8f0050078ea49f990eda |
| `/root/finance/amir_day.py` | 59b035da84a6648b94c1977d0c810b9d | f1ce78e8bd788fbbb8c9774c04119af9 |
| `/root/finance/order_rules.py` | ee17c1872acd0c440868a915fa5014df | 79f21c1ee1f763b1ac06b370e3d77b79 |
| `/root/finance/reports_watch.py` | absent | a8bbd95e597c44418d82ae895750b9c1 |
| `/root/finance/reports_guide.py` | absent | 20a05704d8183af340cec4b138aa9fb1 |
| `/root/finance/reports_guide_pics.py` | absent | d7f4f3316338acf3d34502559b1ae8f9 |

Each placed file is byte-identical to the walk's NEW copy (`cmp`). Backups: `/root/finance/finance.db.bak_S500_20261010_225620` (backup API, 34,725,888 bytes, before the first data write) and `reports_tile.py.bak_S500_6f7cf490`, `stock_app.py.bak_S500_cc06dac9`, `amir_day.py.bak_S500_59b035da`, `order_rules.py.bak_S500_ee17c187` beside the files. Placed by copy-then-rename in the order: the three new files, `reports_tile.py`, `stock_app.py`, `amir_day.py`, `order_rules.py` last.

**Read only, unmoved** (md5 before = after): `aaj_floor.py 1f53b8da…`, `spine/marg_read.py 96f565a8…`, `export_watch.py f6845ec5…`, `shelf_figure.py a1e87d1f…`, `item_alias.py 5168c3c0…`, `/root/marg_ingest/marg_take.py a86a0f26…` — all at the brief's pins. **Must not move, unmoved during the install:** `finance_app.py bff362c3…`, `aaj_kaam.py`, `aaj_kaam.html`, `aaj_duties.json`, `owner_console.py`, S486's eleven (`order_sheet.py 012e21c9…`, `porders_s454.py 9c463e7c…`, `porders.py a5a823bf…`, `porders.html 7a6799ae…`, `darpan_kal.py fd799a56…`, `darpan_kal.html f5e279eb…`, `order_sheet_pdf.py 6e7a5e1a…`, `finance_approvals.html b32da7ff…`, `spine_read.py 712a1e4e…`, `order_rehearsal.py 104d366d…`, `selftest_spine.py fc63d2c6…`), the clone's `DUTY_MAP.json 20162448…` (v9), the crontab. Recorded, moved by the parent's kits BEFORE this run (not a fault of this kit): `/root/portal/portal.py` is `f8b059f61fa8b885f024f4f4ce73e4f2` (the brief read `63df9d49…`), `/root/portal/tile_grants.json` is `64f8b04937e8841c405cb9070b604aad` (the brief read `f9441311…`, v32).

**DATA_OK 5 1** (reports_watch.ensure on the live database, after the backup): the table `marg_report_alert` (0 rows) and the five rows `reports.tries 2`, `reports.late_hhmm 10:00`, `reports.closing_min_share 90`, `reports.try_gap_min 3`, `reports.alert on`. **ONE restart** of `clinic-finance` at 22:56:36 IST; healthz 200; `/finance/reports/aaj`, `/kaise/sale`, `/pic/sale_two.jpg` answer 302 to a plain curl (the gate); the journal since the restart holds no `NOT mounted`, `Traceback`, `SyntaxError`, `NameError` (its one "ERROR" line is gunicorn's own *Worker was sent SIGTERM* at the restart).

**Read-back** (the placed files, a fresh backup-API copy of the database, the live spine and archive read only): as shavez the page is 200 with *Signed in: shavez*; `/kaise/stock` 200 with six steps; `/pic/only_total.jpg` 200 image/jpeg (12,539 bytes, equal to the module's). `reports_watch.py --say` on the copy (22:57 IST):

```
Sale report: ok (tries 1, wrong 0)
Closing stock: ok (tries 2, wrong 0)
would tell the owner now: nothing
switched off by nothing; reports.alert = on; NTFY_URL is set
```

**The test message:** `test message: pushed to the owner's phone` (exit 0, 22:57 IST; the stubs unset for that one command only).

**The walk** — `WALK_S500 GREEN (83 checks)` on the real run (DRY green first, 83 checks, 22:55 IST), on backup-API copies of `finance.db`, `assets.db` and `spine.db`, a scratch spine folder, a scratch readings folder, a scratch `marg_ingest` copy, the walk day Wednesday 12-03-2031 (due day 11-03-2031), rows keyed `W500`. Every control red on the OLD files (the three new files absent from the OLD copy):

1. Selftests: `reports_watch.py --selftest` 0 failures on both pythons; NEW `reports_tile.py` **54 checks, 0 failures** on both pythons. **C:** OLD prints 40 checks.
2. F-799: two 250-item closings 25 s apart → `bad`, tries 1, wrong 1, fix `stock25`; page *Galat hai · koshish 1 / 2 · Khali stock wale item nahi aaye · Ek koshish aur hai* + link; a third ten minutes later → wrong 2, *Doosri baar bhi galat*, *Doctor sahab*, line *closing stock wrong 2 times: zero-stock items are missing (250 items came; recent closings list 379)*; a full 380 → `ok`, *Sahi hai*, *380 item, khali stock wale bhi*; a wrong closing of the afternoon before → tries 0, due, *11-03 15:02 baje wali closing stock report sahi nahi thi*. **C:** OLD gives `ok`, "250 items".
3. `DEFAULT` → bad, `stock4`; `TOTALS` with a family-less reading → bad, *WHOLE*, the second try. **C:** OLD gives arrived for both.
4. `SUMMARY1` → `refused`, `sale3`, *Step 3 dobara kijiye* with `sale_two.jpg`; a DETAIL file with a passing reading → `ok`, *Sahi hai*. **C:** OLD has no *Step 3 dobara*.
5. F-788: a medical-PC refusal (empty dates) and a 30-day range refusal → tries 0, both in `loose`, *manzoor nahi hui*, line *2 refused (not the day's report)*, row `due`; a rejected `marg_push_staging` row of today (the table exists live) → *1 refused (not the day's report)*. **C:** OLD puts the refusal on the row (`refused`).
6. The floor: `aaj.staff_on` set; floor 2026-10-01; `_s500_floor` gives the day for shavez, None for manoj; the copy held no open gap, so ONE `W500` gap on 10-Sep was put on the copy: shavez's card hides it, manoj's shows it, `api/status`'s `line` is identical for both. **C:** OLD shows shavez the September gap.
7. The guide: `/kaise/sale` and `/kaise/stock` 200, six `<li>` in `<ol class=gs>`, the real clock's due day in the sale steps, no meta refresh; all thirteen pictures 200 image/jpeg, FF D8, equal to `reports_guide.pic`, `max-age=86400`; `/pic/nope.jpg` 404; `/kaise/x` 302; `w500none` → 302 to `/portal` for all three. **C:** OLD 404 for `/kaise/sale`.
8. The snapshot door (the walk's own token): 379 as on the eve → 200; **250 → 409 `short_closing`** (items 250, reference 379, reference_day 2031-03-10), no `stock_snapshot` / `stock_feed` row; 379 → 200; `push_expected` 200 → `stock_expected`; share 0 → 250 → 200. **C:** OLD 200 and 250 rows stored.
   8b. F-801: `_s446_proof` on W500 vouchers with feeds 07-03 (before), 10-03 (wrong) and 11-03 (right) → NEW `done`, `as_after 11-03-2031`. **C:** OLD `wrong`, `as_after 10-03-2031`.
   8c. `amir_day.py` holds the new words and none of the old; Amir's step 6 with a newer salt tick shows the card with *Text ya Excel, dono chalte hain*. **C:** OLD holds *Excel mein (text nahi)*.
9. The watch (stub file): wrong twice at 08:20 → ONE line *Closing stock of 11-03 is wrong twice: zero-stock items are missing (250 items came; recent closings list 379). The sale report has not come yet.*; the same tick again → nothing, page *khabar chali gayi hai*; nothing in: 09:50 nothing, 10:00 one message naming both; two files still being checked: 10:00 and 10:20 nothing, 10:30 one message; stub unset → row made, `sent 0`, `how "a walk's push stub is set -- nothing sent"`, `sent_at NULL`, withdrawn when the report turns right; Sunday → `quiet`; `reports.alert = off` → `off`, page *Doctor sahab ko bataiye*; `REPORTS_WATCH_OFF` file → `off`, *Doctor sahab ko bataiye*, and *khabar ja rahi hai* once the file is gone; `order_rules._s500_reports(con, {})` → `{"reports": {"ok": true, ...}}`. **C:** OLD `order_rules` has no `_s500_reports`.
10. Staff-eye (eight logins through a walk-only portal store and secret; staff duties evaluated on `aaj_kaam.connect(copy, mode="staff")`, floored at 2026-10-01; doctors on the plain connection): every login signs in, same tile count NEW = OLD, every due duty visible as on OLD; only `/finance/reports/aaj` and `/api/status` differ — and Amir's card pages (`/finance/amir`, steps 3, 5, 6), which differ by the salt words and the stage-A proof rows (F-801) ALONE (equal once those are taken out: the walk proves it). shavez and amir hold the tile and open the page (*Signed in*); bhawna and manoj hold the tile by role and open it; **darpan, shivani, alisha open it by its address but hold no tile** (finding, the parent's `tile_grants.json`); reception → 302 to the portal on both sides. The bill-chain finding (`shavez.bill_chain_gap` due unfloored while floored says not) did NOT print: the live chain has no open gap tonight.

**The ten-minute job:** `order_rules.py tick` runs 05:00–21:50; the new code (and the `reports` key in its log line) first runs at 05:00 tomorrow, 11-Oct. Its last log lines tonight (21:30–21:50) are the old shape, as expected.

**Findings, one line each:**
- Darpan, Shivani, Alisha and Bhawna: the brief expected all four without the tile; bhawna HAS it (role doctor), the other three do not — the parent's `tile_grants.json` (v33 now, `64f8b049…`).
- The five `reports.*` settings are on no card yet (`porders_s454.py`, parked).
- `DUTY_MAP.json`'s `amir.salt_list` `duty_hi` and the parent's `aaj_seed.py` still say *Excel* (documentation and a switched-off list) — for the chat's next map version and for the parent.
- The sale report's tick waits for the spine's evidence job (`*/10 8-23`, the parent's crontab): a report exported at 06:00 reads *jaanch ho rahi hai* until 08:00; the watch gives a file still being checked until 10:30 before it tells the owner.
- A medical-PC refusal is not a try (its day is unknown): two of them make no *wrong twice* message — the hour does.
- `shavez.closing_stock`'s `due_sql` counts a VERIFIED-but-wrong closing (short, batch-wise, not WHOLE) as done, so the staff list ticks it while the page says *Galat hai* — a DUTY_MAP v10 question.
- A refused short push writes no `stock_feed` row, so the parent's *Marg stock feed* health leg may go red on such a day.
- **F-801, read on the live copy:** Amir's stage-A proof now judges on the 09-10 closing and names L S BELT CONT GRAY UNISON L (Marg 2, should be 3) and XXL (Marg 3, should be 2) — his renames stay closed until the next WHOLE closing after he corrects these two; the two items the 04-10 check named are right now.
- The clinic chat published S509–S512 during this build and S508 was installing when this run began (its lock was waited out); none of those kits touch this kit's files (the FROM pins held through the walk).
- The journal's one "ERROR" line since the restart is gunicorn's *Worker was sent SIGTERM* at the restart itself.

**Not done, and why:** nothing of the brief was left out. `DUTY_MAP.json` / `DUTY_MAP.md` unchanged by design (no duty moves). The 250-row 06-10 `stock_snapshot` is history, not repaired (the brief). The lock `/root/deploy/.claude_code_build.lock` is released right after this report is written.

**Charter (S303):** retired — the two morning rows' old wording and the old menu path in the how-to block (the README says so); left for later — the DUTY_MAP v10 question above, the settings card, the evidence job's hours, the *Excel* words in the map and the seed. Charter: left out — nothing. Charter: seen, not touched — `reports_tile.status` keeps its own in-process `_READ_CACHE` of readings (a stored conclusion with no stamp, process lifetime only; rule 4), as before this kit.

**Undo:** put back the four `.bak_S500_<from8>` files (`order_rules.py` first), remove `reports_watch.py`, `reports_guide.py`, `reports_guide_pics.py` and their `__pycache__` entries, `systemctl restart clinic-finance`, healthz 200, read the md5s back. The table and the five rows may stay. The database backup is used only if the data change must be reversed (it would not need to be: the table is empty and the rows are defaults).
