# S533_AMIR_DAY_PAGE — Amir's page rebuilt once, under the charter (Kit 3 of D706)

**Brief:** `claude_code_briefs/S533_AMIR_DAY_PAGE.md` (v3, session 310). **Rulings:** D706, D708, D709, D712.
**Faults repaired:** F-839 (two salt rules), F-861 (the two spellings), F-863 (c4's words from the record while the stage has no B), F-864 (the bill line from a reception tap).

## What it does

- **`amir_day.py` replaced whole.** One `state()` reads every fact a page needs once per request (the stage once, its words once, the scans once,
  assets.db at most once for the paper pass); every line is built once as a `(hi, en)` pair and printed by Amir's step 7, his card, the owner's
  `/finance/amir/day`, the visit summary and Needs-you alike; every write appends (`amir_step_log`, `amir_bill_answer`) or is an audited UPDATE of
  a system record; `settle()` is the only write on a read (his corrections cleared once Marg shows them — a system row beside his, never over it;
  the one-time jobs proved; the returns count re-made only when its input stamp moves). `DUTY_SQL` holds the three duty-map SQLs and the code runs them.
- **The pages:** step 1 records which button (punched / no punch); step 4 has four heads (no green tick over a red report) and *Aage badhiye* moves
  on; step 5 shows dd-mm-yyyy, names its export and scan dates, and its three counts apart (*Aaj aaye bill · Pichhle dinon ke baaki · Flag kiye
  hue*), his corrections under their own head; step 6 holds the day only while his card holds a line of his Marg work, the salts door only while the
  sheet has rows, the second salts door gone; step 7 lists what holds the day apart from what does not; *Din phir se kholiye* is recorded, never erased.
- **D712:** the card's bill line is *Scan hua bill Marg mein baaki: N — kholiye* (the same list step 2 shows, `#scans`); an arrival with nothing
  scanned after `arrival.bill_grace_days` is the owner's line only.
- **The salt list:** one rule (the newest VERIFIED list by `received_at` against his newest tick), one card per page, owed counted in his visits.
- **Beside it:** `stock_app.py` — `amir_duties` and `_s444_renames` (and their cache) retired, two comments; `purchase_app.py` — `EXPORT_DAY_SQL`
  (the one expression of an export's day), `purchase_bill.first_seen_day` (added and back-filled in `_ensure`, set on insert by `_store_bills`),
  `scans_to_enter` retired (no caller); `stockmatch.py` — c4 reads the stage's B, `renames_wait_stage_a` added (the record `renames` stays).
- **DUTY_MAP v11:** `amir.bills_answer`, `amir.own_correction`, `amir.salt_list` carry `amir_day.DUTY_SQL` byte-equal; `amir.arrival_bill_entry`
  retired, never due; `amir.scan_files`' marker; `amir.marg_jobs` counts a reopened job as due (see *Decisions*); the .md rows and log line.

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/amir_day.py` | f90df5b2 | see PINS.sh (the kit's whole file) |
| `/root/finance/stock_app.py` | 51620064 | c626a46a |
| `/root/finance/purchase_app.py` | c29050c1 | 147201dd |
| `/root/finance/stockmatch.py` | 4a2f9fcd | 10e30d28 |
| `claude_code_briefs/DUTY_MAP.json` | 7aa2f935 | 69b8f56b (v11) |
| `claude_code_briefs/DUTY_MAP.md` | 4888a228 | 553398f3 |

Read only, never edited: `item_alias.py` 111a8e48, `stock_amir.html` 8dd65e64, `stock_watch.py` c960f6c8, `qty_words.py` 706db7cc,
`sanjeevni_approvals.py` 792f4a9a, `amir_salts.py`, `reports_tile.py`, `aaj_seed.py`, `aaj_kaam.py`, `finance_approvals.html` b32da7ff, `stock_hub.html`
a710a98a, `finance_app.py`, `portal.py`, `tile_grants.json`, the crontab (the installer proves none moved).

## The data step (`data_s533.py`; keyed, idempotent, one transaction, `--dry` rolls back, never a delete)

1. `purchase_bill.first_seen_day` — added; back-filled from the bill-wise export the row names, else the bill date. *First sight for the bills
   already on the box is the day of the newest export that carried them — the only day the data held; from install on it is the true first sight.*
2. `amir_self_wait.bill_id` — added; filled where exactly one bill carries the triple.
3. `amir_step_log` — every old step tick copied once (key day, step, done_at); step 7 as `close`; one `reopen` row per day reopened and never
   closed again (22-09). A day reopened and closed again (17-09) keeps its close row only; its reopen stays in `amir_day.reopened_at`.
4. `amir_bill_answer` — every old bill disposition copied once (key triple + at) with its `bill_id`.
5. `amir_job.reopened_at` — added.
6. The two spellings (D709): `L S BELT CONT GRAY UNISON XXX` → **`L S BELT XXXL CONT GRAY UNISO`**, `TYNOR WRIST SPLINT LF M ELAS` →
   **`TYNOR WRIST SPL LF M ELAS T`** — only after the newest VERIFIED closing on the box was read and prints them (and not the old new names);
   through item_alias's own doors (`_event 'respelt'`, `_follow`, `sight_closing`).
7. `amir.salt_owed_days`' note in visit days; the S444 settings INSERT OR IGNORE.

**Reverse (only if the chat orders it):** the new tables and columns stay (the old files never read them). To undo the spellings: per row,
`UPDATE marg_item_rename SET new_name=<was>, new20/new27 = its clips, verified_at=NULL, verified_md5=NULL, verified_as_on=NULL,
verified_captured=NULL, verified_k20=NULL WHERE old_name=…` with an `_event 'respelt'` row saying so — the `finance.db.bak_S533_<stamp>` holds the before.

## The undo (files)

Put back the four `/root/finance/<file>.bak_S533_<from8>` files, restart `clinic-finance`, healthz 200, read the md5s back. The DUTY_MAP in the
repository is reverted by a later kit (v10's SQL reads `amir_bill_disposition`, which stays, but no longer receives answers — said in the report).

## Charter

**Retired:** amir_day's rule A for the salt list (`_salt_list_state`, `_salt_prompt_amir`, `_salt_owner_line`, `_applied_line`, `SALTS_STATE`,
`_STAMP_IN_NAME`); the S444/S446/S452/S454 shims and dead code (`_s444_card`, `_s444_left`, `_s444_summary_rows`, `_s444_open`, `_s444_voucher_line`,
`_s444_duties`, `_s444_state`, `_s444_rs`, `_s444_ddmm`, `_s444_days_since`, `_s444_login`, `_s444_who_line`, `_packs_card_s408`, `_s446_bills_list`,
`_s446_summary_rows`, `_s446_left`, `_s446_voucher_line`, `_s446_owner_lines`, `_s452_extra_hi`, `_s452_left_hi`, `_s454_entry_mode`, `_left`, `_work`,
`_s446_state`, `_s446_watch`, `_s452_state`, `_s494_spine`); S488's copies (`S488_TAIL_HI`, `_s488_tail_hi`, `_s488_wait_html`, `_s488_proof` →
`stock_app._s488_stage_proof`); `S494_JOBS` (the seed tuple with a rupee figure) and `s494_seed_jobs`; `MARK_KIT` and the S243/S246 tags; the DELETE on
reopen; the INSERT OR REPLACE writes; the second salts door `/finance/purchase/page/salts`; the arrival line on his card; the env `AMIR_BILLS_FROM`
(not set in the service's environment at install); `stock_app.amir_duties`, `_s444_renames`, `_S444_RENAMES_CACHE`; `purchase_app.scans_to_enter`.
The walk greps every one over the NEW folders (word-bounded) and the installer over `/root/finance` and `/root/portal` after placing.

**Left for later:** rung 4b (F-862; `stock_snapshot`, the shelf windows), S486 Part A/B, F-802 (the medical-PC kit), the five `reports.*` settings,
F-726a, F-777, F-794; the seed line `amir.arrival_bill_entry` in `aaj_seed.PEOPLE["amir"]` (parent-owned) can be turned off.

**Product calls kept, named:** the two dates typed on step 3; *Din phir se kholiye*.

**Seen, not touched:** `reports_tile._salt_row` (rule B's third copy, parent); `scans_for_amir`'s write on read and DDL per call; `amir_view`'s
`Spine()` never closed; `_s452_marg_rates`' mirror write on read; `_report_cached`'s 600 s; S524's release-on-any-read; `_newest_root` vs `_s446_root`;
`#rest` with no target in `stock_amir.html`; `_export_state` comparing Marg's stamp with the server tick (A18); `_s444_exports_for`'s ORDER BY over two
stamp shapes (R2-33, now gone with the function: the new file reads the bill's own bw_md5 export); the 17-09 reopen left in `amir_day.reopened_at`
(R3-6); item_alias `_follow` closes only an OPEN rename task in `marg_task` (the S229 tasks were already closed at tick time, so their answer keeps
the old spelling) and leaves the old spelling's spine alias active beside the new one.

## Decisions the builder made (named for the chat)

- `amir.marg_jobs`' due_sql now reads the same "said" rule as the card (`said_at > COALESCE(reopened_at, '')`) — the brief's §2.3 reopen makes a
  reopened job due again on his card; the v10 SQL would have counted it as not due (charter 13: the map and the page read one rule).
- DUTY_MAP.md rows that named the retired tables (`amir_step`, `amir_bill_disposition`, `amir_day.closed_at`) are re-worded to `amir_step_log` /
  `amir_bill_answer` / the close row, beside the rows the brief listed.
- The collector's liveness at install is `marg_ingest/last_run.json` (finished within 30 minutes; it runs every 5) and its newest take within 72 hours;
  the spine must have passed with every gate green and been built after the collector's newest take (≤ 40 minutes behind).
- Step 7's not-ready screen also prints the three bill counts (§2.4 names them on step 7).
- The visit summary's `bills` carries `flagged` and `waiting` beside the kept keys (nested; every top-level key kept).

## Files

`KIT_ID.txt`, `PINS.sh`, `SUMS.md5`, `amir_day.py` (the whole new file), `make_s533.py` (the builder), `data_s533.py` (the data step),
`walk_s533.py` (the walk), `state_s533.py` (the install-day state, the read-back, the grep), `install_S533_AMIR_DAY_PAGE.sh` (the installer).
No `.json` in the kit folder (F-751): DUTY_MAP v11 is built by `make_s533.py` from the clone and published in `claude_code_briefs/`.
