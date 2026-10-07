# S494_AMIR_JOBS_NOTICE_FLAGS — Amir's one-time Marg jobs; the order sheet's notice sent by the tick; flags judged again; one spot line

Kit S494 · **D686** · faults **F-765, F-767, F-771** · brief `claude_code_briefs/S494_AMIR_JOBS_NOTICE_FLAGS.md` (Sanjeevni chat, session 299, 07-Oct-2026).

## What and why

- **Part A (F-767) — the arrival notice is sent by a process that can send it.** The web service runs `/usr/bin/python3`, which has no
  `pywebpush` (the venv has it), so *"Darpan ki order sheet aa gayi"* failed on every phone on 06-Oct. `order_sheet._sheet_notice` now
  keeps the text as `pending` when its process cannot push (`_can_push()`), and the ten-minute tick (`order_rules.py tick`, venv,
  05:00–21:50) sends it through `cron_pass` → `send_pending_notices` (after the sheets): never on a later day, never once
  `order.sheet_notice_max_min` (60) minutes have passed since the sheet was taken, never on another `order.source`, never more than
  twice (a send that failed everywhere is tried once more and carries `retried`). The 06-Oct row lapses at the first tick, unsent.
  A sheet taken after the day's last tick (21:50) lapses unsent — true to the rule.
- **Part B (F-771) — one spot-count line.** `stock_watch.needs_you_lines`: the first (newest) `spot_missed` notice is shown, the rest
  of the week's are skipped. Nothing else in the file moved.
- **Part C (F-765) — a flag is judged again.** `shelf_figure.rejudge(con, sp)`, called at the top of `record_gaps` (fail-soft; its return
  value and the tick's log line unchanged): every first flag of a closing within `stock.gap_rejudge_days` (7) days of the newest is worked
  out again as `record_gaps` works it, from the stored rows and today's spine; when the move is now explained it is cleared, its later
  copies with it — and it is not carried into the next closing. One direction only: it never raises a flag and never touches an unflagged
  row, an approximate row, or a flag whose origin lies before the window. The live table is re-judged by the first tick after the install.
- **Part D (D686) — Amir's one-time Marg jobs.** Table `amir_job`; eight rows seeded (4 orthotic categories, shown only with his rename
  list; 3 vendors' bills to scan for bank details; Kedar's ₹310 cash payment entry). His *Marg sudhar* card, every step, carries them
  under **"Ek baar ke kaam"** in the owner's approved words, each with its button (*Kar diya* / *Scan ho gaya* / *Bill nahi mila*) —
  a small form posting `job=<value>` to the step being shown, read FIRST in that step's POST; he stays on the step. The system closes
  what it can prove (Marg's category list read by the spine; bank details on record; a scan linked to a Marg bill) and reopens a category
  a later list still shows wrong. The owner's Needs-you gains, in English: bank details to type, a bill not found, an item the category
  list does not carry, and jobs left `amir.job_wait_days` (10) days. `GATE_STEPS`, `_ready_to_close` and the day's close are untouched.
- **The duty map** `claude_code_briefs/DUTY_MAP.json` v8 → v9 (`amir.marg_jobs`, door `/finance/amir/step/6`, marker *Ek baar ke kaam*,
  coded `amir_day._s494_owner_lines`) and `DUTY_MAP.md`, edited in place — no copy of the `.json` in this folder (F-751). The installer
  reads it beside the kit (`../../claude_code_briefs/DUTY_MAP.json`, pinned v9).

## Pins (server, `/root/finance`) — FROM → TO

| file | FROM | TO |
|---|---|---|
| order_sheet.py (Part A) | 16f21a6515a1317e1f6e31cb0a280513 | 012e21c92233d0eec4c828e15f7912e1 |
| stock_watch.py (Part B, one block) | 4fc0f6017825975e75ebacfdc2f122d2 | d78c902e0d3258fd0c615cd9715346b6 |
| shelf_figure.py (Part C) | 0d836de54672f3e624fcc763311ab22c | a1e87d1ff758e8f9a8206205a457b875 |
| amir_day.py (Part D) | 08d058a765278d6e119e70f8f0adeedd | 59b035da84a6648b94c1977d0c810b9d |
| claude_code_briefs/DUTY_MAP.json (v8 → v9) | f27423b61e50857875bb8f7ba4e5c57c | 2016244829b4c70c00f1c59b0250ee35 |
| claude_code_briefs/DUTY_MAP.md | cb78fe54f4d09fb4733dc1bac268cf9e | 7400e9ff2b047df82c81e897a06ea5ac |

Read only (md5 before = after): `order_rules.py`, `stock_app.py`, `purchase_app.py`, `sanjeevni_approvals.py`, `spine/spine_read.py`,
`/root/portal/ring_common.py`, `/root/assetapp/asset_register.py`.

`finance.db`: the table `amir_job` (made on the live database in step 3, before the gates — the brief's ruled order, because the map is live
at the pull); eight rows seeded (INSERT OR IGNORE by key); three setting rows (`order.sheet_notice_max_min` 60 by `order_sheet.ensure()`
itself; `stock.gap_rejudge_days` 7 and `amir.job_wait_days` 10 by the installer, INSERT OR IGNORE); `s454_shelf_gap` re-judged by the
first tick. One backup by the backup API before the first data write (`finance.db.bak_S494_<stamp>`); `<file>.bak_S494_<from8>` beside each
of the four files. Restarts `clinic-finance` once. The owner's settings card (`porders_s454.py`, parked) lists only the keys it knows; the
three new rows join it when that file is next opened.

## Not touched (md5 before = after, or the install is undone)

`finance_app.py`, `/root/portal/portal.py`, `tile_grants.json`, `aaj_kaam.py`, `aaj_kaam.html`, `aaj_duties.json`, `owner_console.py`,
`packs.py`, `porders_s454.py`, `darpan_kal.py`, the crontab.

## Files

| file | what |
|---|---|
| `install_S494_AMIR_JOBS_NOTICE_FLAGS.sh` | lock → DB backup → the empty table → gates → FROM pins → build → compile on both pythons → walk on scratch copies → (DRY=1 stops; then nothing is written at all) → file backups → place → md5 read-back → data → restart → healthz → read-back → nothing else moved; restore on red |
| `make_s494.py` | the anchored patcher of the four server files (each anchor exactly once) |
| `PINS.sh` | the four TO pins |
| `walk_s494.py` | the walk, sections 1–6 of the brief, each with its control on the OLD files; staff-eye signed in through a scratch portal |

Undo: put back the four `.bak_S494_<from8>` files, restart `clinic-finance`, healthz 200; set `show_from = NULL` on the rows with
`created_by = 'S494'` (the map then reads (0, NULL)). The table and the settings may stay; the database backup is used only if the brief's
data change must be reversed.

The server line, after the publish:

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S494_AMIR_JOBS_NOTICE_FLAGS/install_S494_AMIR_JOBS_NOTICE_FLAGS.sh
```

(Run once already from a byte-identical copy of this folder and of the map; run from the repository it answers ALREADY INSTALLED.)
