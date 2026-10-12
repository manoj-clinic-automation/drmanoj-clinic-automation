# S536_AMIR_BOARD_D712 — Amir's board drops the reception-tap line; "ordering can start" waits for stage C

**Brief:** `claude_code_briefs/S536_AMIR_BOARD_D712.md` (v2, session 310). **Rulings:** D712, D708. **Fault:** F-864 (the tap line) — its last
staff place. The second line has no F-number. A small follow-up to S533_AMIR_DAY_PAGE (live 05:48 IST 12-Oct). No data step.

## What it does

- **`stock_app.py` — `_amir_board_light` (2.1; charter 2, 9; D712).** The two `rest = dict(...)` lose the arrival key: the board payload, for
  every login (the owner's board too), carries the Sunday and the fixes only. The arrival without a scan is the owner's Needs-you line
  (amir_day's D712 line, S533 §2.6.3) — one place. A comment line says so. Nothing else in the function moves.
- **`stock_amir.html` — `restCard` (2.2; charter 9).** The arrival row (*"… — maal aa gaya, Marg mein bill abhi nahi"*) removed whole; the
  header comment's section 4 no longer lists *bill entry baaki*. The Sunday rows, the fixes and *"Aaj kuch nahi — sab upar hai."* as today.
- **`amir_day.py` — `needs_you_lines` (2.3).** *"Orthotics verified and renamed -- live orthotic ordering can start (count #N, dd-mm)"* shows
  only when the stage is C or done; its moment is the root's first stage-C release (`SELECT MIN(at) FROM stock_stage_event WHERE count_id=?
  AND stage='C' AND event='release'`), else `B.verified_at` (a count with no medicine batch goes straight to done); shown while that moment is
  within two days. The query runs in its own try (a fault drops this one line only), on the connection `state()` just read the stage on.
  amir_day still writes no stage event. Text unchanged.

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/stock_app.py` | c626a46a | see PINS.sh |
| `/root/finance/stock_amir.html` | 8dd65e64 | see PINS.sh |
| `/root/finance/amir_day.py` | 262b0b81 | see PINS.sh |

Read only, never edited: `stock_watch.py` c960f6c8 (`amir_view` still returns `bill_pending`; amir_day's D712 owner line reads it there, and
the cron prints it), `purchase_app.py` 147201dd, `stockmatch.py` 10e30d28, `stock_hub.html`, the DUTY_MAP (v11 69b8f56b — no duty moves),
`finance_app.py`, `portal.py`, `tile_grants.json`, the crontab (the installer proves none moved). `/root/deploy/repo` is not pulled.

## The undo

Put back the three `/root/finance/<file>.bak_S536_<from8>` files, restart `clinic-finance`, healthz 200, read the md5s back. No data changed;
the `finance.db.bak_S536_<stamp>` is kept by rule and is not needed for an undo.

## Charter

**Retired:** the board's arrival row (`restCard`'s loop) and the `bill_pending` key of the board payload (`_amir_board_light`).
**Left for later / seen, not touched:** `stock_watch.py`'s three places that still call the arrival a line on Amir's board (the settings hint
101, the docstring 862, the header 22–23); `_amir_board_light` still calls `amir_view`, which computes `bill_pending` it no longer sends (R1-11);
the release moment is the first read after the orthotics cleared, not the clearing itself (R1-7).

## Files

`KIT_ID.txt`, `PINS.sh`, `SUMS.md5`, `make_s536.py` (the builder: three anchored edits), `walk_s536.py` (the walk), `state_s536.py` (the
install-day state and the live read-back), `install_S536_AMIR_BOARD_D712.sh` (the installer). No `.json` in the kit folder.
