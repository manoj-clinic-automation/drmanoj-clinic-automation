# S537_VOUCHER_GUARD — voucher 29 voided; no voucher to Amir that would take Marg below zero; settled stays settled; a tied arrival is never "bill missing"

**Brief:** `claude_code_briefs/S537_VOUCHER_GUARD.md` (v3, session 310, after R1 and R2). **The owner's word:** "Yes", 12-Oct-2026 07:02 IST.
**Fault:** F-185. Kit shape: S536's, plus a keyed data step (S533's `data_s533.py` shape).

## What it does

- **`stock_app.py` — the void (2.1; charter 5, 10).** Two append-only tables, laid by `_voucher_ensure` (`VOUCHER_S537_SCHEMA`, joined onto
  `VOUCHER_SCHEMA`): `stock_voucher_void` (one row voids one whole batch) and `stock_voucher_settle`. ONE filter, `_void_sql(alias)`, on every
  reader of the voucher lines: `_voucher_frozen`, `_voucher_state`, the entered door (a stale page entering a voided batch is told
  *"Yeh voucher ab nahi hai."*), `_voucher_numbers`, `amir_vouchers_open`, `_s446_batches` (so the stage, the board, the proof), and the guard's
  own read. Not filtered, by design: `_voucher_seq` (numbers never shift — a voided batch is simply not shown), `_voucher_make`'s next round
  number, `_report_cached`'s stamp, `_s446_root`. The void door `_voucher_void` refuses an entered batch and a batch that does not exist; it
  has no route (an owner door is left for later) — the data step is its one caller.
- **`stock_app.py` — settled stays settled (2.2).** `_voucher_settled(con, root)`; the count-day loop skips a settled item.
- **`stock_app.py` — the guard (2.3; charter 1b, 12).** `_voucher_lines` is the one loop (offered, held, unread); `_voucher_pending` and
  `_voucher_held` are its two faces. A line that LOWERS Marg is held when Marg's newest closing of the item **by its full printed name**
  (`shelf_figure.latest_snapshot`: the newest closing by its real date) + the count's vouchers made but not yet in that closing (not entered,
  or first entered after the closing's day; not voided) + the line would go below zero. A name the newest closing does not print is offered
  and counted `unread` (one owner summary line). Held lines are never frozen, never pending, never Amir's. The frozen batches get the same
  test (`_voucher_held_batches`, the line's own change counted once): `amir_stage`'s stage-C release and "Aur voucher kholiye"
  (`_s452_release`) skip a held batch (the next passing one takes its place; the board's "more" count leaves it out). `amir_stage` carries
  `A["held"]`, `C["held"]` and `unread`; `_s521_stage_words` adds one owner line per held item (*"Count #N: <item> (STOCK ISSUE voucher n) — the
  count-day sum asks <qty>; Marg's closing of dd-mm holds <qty>: not given to Amir"*) and one *"closing not readable for N item(s) — guard not
  applied"*. The guard writes nothing.
- **`loss_piles.py` — `receive_close` (2.3, R1-9b).** A held item is carried, so the rule does not word it EXPLAINED again on every run.
- **`shelf_figure.py`, `stock_statement.py` (2.1).** `filed_vouchers` and the statement's rounds honour the void (through `stock_app._void_sql`).
- **`stock_watch.py` — `bill_pending_lines` (2.5).** `AND COALESCE(l.billed_bill_no,'') = ''`: an arrival tied to its bill (porders writes
  `billed_bill_no` from Marg's own purchase lines) is never listed — the Yuvika knee-immobilizer line goes, amir_day's D712 owner line with it.
- **`DUTY_MAP.json` v11 → v12, `DUTY_MAP.md` (2.6).** `amir.count_vouchers`' `due_sql` gains the void test on the batch (anchored on
  `) b WHERE NOT EXISTS`; one line, no `;`); version, kit, the note, the `.md` row and a log line.
- **`data_s537.py` (3).** Voucher 29 found by shape (count 1, round > 5, one ISSUE batch, one line ANKLE BINDER BAMBOO L −1; anything else, or
  entered → STOP) and voided; ANKLE BINDER BAMBOO L settled for count 1; steps 1–2 commit together; then `stock_watch.ask` puts it at the head
  of Darpan's next list. `--schema-only` lays the tables; `--dry` rolls back and skips the ask.

**Install order (2.6):** place the five files → `data_s537.py --schema-only` → `git pull` of `/root/deploy/repo` and the map gate at v12 (not
v12 → no void, the files restored) → `data_s537.py` → one restart of `clinic-finance`.

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/stock_app.py` | 8d55637c | see PINS.sh |
| `/root/finance/stock_watch.py` | c960f6c8 | see PINS.sh |
| `/root/finance/shelf_figure.py` | 9be5eb88 | see PINS.sh |
| `/root/finance/stock_statement.py` | 1a4f6c9e | see PINS.sh |
| `/root/finance/loss_piles.py` | 202bfc4e | see PINS.sh |
| `claude_code_briefs/DUTY_MAP.json` (the clone) | 69b8f56b (v11) | see PINS.sh (v12) |
| `claude_code_briefs/DUTY_MAP.md` (the clone) | 553398f3 | see PINS.sh |

Read only, never edited: `amir_day.py` 73882a83, `stock_amir.html` 72034c2e, `stockmatch.py` 10e30d28, `item_alias.py`, `porders.py`,
`aaj_seed.py`, `aaj_kaam.py`, `owner_console.py`, `finance_app.py`, `portal.py`, `tile_grants.json`, the spine, the crontab (the installer proves
none moved). `finance.db`: two new tables, one void row, one settle row, one spot-count ask; backup first; never a DELETE.

## The undo

Put back the five `/root/finance/<file>.bak_S537_<from8>` files, restart `clinic-finance`, healthz 200, read the md5s back. The old files never
read the two new tables, so voucher 29 is back on Amir's board at once. The DUTY_MAP v12 stays valid against the old files (the table exists);
to put v11 back, revert the map in the repository. The `finance.db.bak_S537_<stamp>` is needed only if the void and settle rows themselves must
go — say so before using it.

## Charter

**Retired:** the hand-edit way of voiding a voucher (the brief's line 141 stays as history); the count-day-only pending rule (a settled item and a
line that would take Marg below zero are no longer raised).
**Left for later:** an owner door to settle / void from the hub; the "never past the shelf figure" half of the guard and the family-key miss behind
the Yuvika line (`spine_rules.json` folds KNEE IMMOBILIZER UNI into a key absent from `sp_alias`) — rung 4b; `stock_snapshot` is the name-keyed
table rung 4b retires (F-862) and this guard moves with it then; stockmatch c2's reading of a held orthotic line as done (275, R1-9c); the
aaj_seed voucher SQL at 470 (the parent's).

## Files

`KIT_ID.txt`, `PINS.sh`, `SUMS.md5`, `make_s537.py` (the builder: anchored edits), `data_s537.py` (the data step), `walk_s537.py` (the walk),
`state_s537.py` (the install-day state and the live read-back), `install_S537_VOUCHER_GUARD.sh` (the installer). No `.json` in the kit folder.
