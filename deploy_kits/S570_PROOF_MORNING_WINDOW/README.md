# S570_PROOF_MORNING_WINDOW — the voucher proof judges on a normal morning; the owner's waiting sentence tells the truth

**Brief:** `claude_code_briefs/S570_PROOF_MORNING_WINDOW.md` (v1, Sanjeevni session 316). **The owner's word:** "yes", 16-Oct-2026 11:08 IST
(to the repair REPORT_S569 named). **Faults:** F-905 (the reach rule), F-906 (the waiting sentence). Kit shape: S537's.

## What it does (stock_app.py only)

- **F-905 — `_s524_tryable(c, reach)`.** `last_sale >= end_day` and `last_pur >= end_day` stay as they were. Each stamp comparison is
  replaced by the new `_s570_covers(day, stamp, c, d)`: the newest export of a family covers the closing when it was captured after the
  closing (`stamp > c["stamp"]`, the old clause) **or** when its own capture, read by the estate's one capture rule
  (`_s524_end_day(<the export's covered day>, _s524_stamp_iso(stamp))`, charter 11), stands for the end of a day at or after the closing's
  `end_day`. The covered day is `reach['last_sale']` for the sale side, `reach['last_pur']` for the purchase side; `None` never covers.
  The helpers used are the ones REPORT_S569 named, unchanged (`_s524_end_day`, `_s524_stamp_iso`). The proof's logic otherwise, its cache
  key, its verdict and S528's "the newest capture says wrong" rule are not touched.
  - sale 15-10 captured 16-10 05:10 → end 15-10: covers the 15-10 closing captured 16-10 05:17 (the morning order);
  - purchases to 15-10 captured 15-10 09:10 → None: does not cover (a true "not yet": later purchases of 15-10 are missing);
  - purchases to 16-10 captured 16-10 11:10 → None by the rule, but captured after the closing: covers (the old clause).
- **F-906 — the waiting sentence.** `_s488_why`: a waiting proof's `closing_at` is the capture of the spine closing the proof waits on
  (`c["stamp_iso"]`), never a `stock_feed` push of the same printed day (15-10 10:11 was a mid-day snapshot the spine skips). In the branch
  where the spine holds no clean closing after the vouchers yet, a `stock_feed` push the capture rule skips (a mid-day capture) is never named,
  each push is read by its own capture (not the day's MIN), and the purchase side short says `pur_behind`; `_s488_first_push` skips a mid-day
  capture the same way (new helpers `_s570_push_end`, `_s570_stamp`). `why` now follows what `_s524_tryable` reports short, so the owner's
  words (amir_day's `_s488_ending`, read only — not edited) read: *"Marg's closing of 15-10 arrived 16-10 05:17; waiting for a purchase export
  that reaches that day (Amir)"* instead of *"… arrived 15-10 10:11; waiting for our own figure for that day (made when its sale report lands —
  Shavez …)"*.
- **No staff code changes.** Amir's card is built by S528's unchanged `_s521_stage_words`: while the proof waits on the purchase side it adds
  its own existing do-this tail *"· Purchase report nikaaliye"* (S528 R3-11) — that is the only difference on his card, walked in W5c.

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/stock_app.py` | f58e09dbb273e8b1470aa7220da70015 | 050587dfb5951da65f95937615ddf144 |

Read only, never edited: `amir_day.py` (73882a83), `/root/finance/spine/*`, `finance_app.py`, `portal.py`, `tile_grants.json`, the crontab (the
installer proves none moved). `finance.db`: no data written; backed up before placing. Service: `clinic-finance`, restarted once.

## The walk (`walk_s570.py`)

On backup-API copies of finance.db and spine.db, NEW (the built file) and OLD (the box) sides as fresh processes; its own rows by key
(md5 `W570…`, the made-up day 2027-03-10, the made-up feed day 21-03-2027). W1 the morning order (True; OLD False — control); W2 a true
"not yet" (False/'pur' on both); W3 every closing on the live copy gives the same answer on both files except 15-10 (sale → pur), and the
proof table is the same on both for the lots' windows and one before each earlier closing; W4 the live case as on the copy and with a made-up
purchase export captured 16-10 11:00 covering 1–16 Oct (a verdict; OLD stays waiting — control); W5 the sentence (no "10:11", no "made when
its sale report lands", the purchase words; OLD prints both — control) and Amir's card; W7 the feed branch (a mid-day push never named;
OLD names it — control); W6 no run of ten digits in its output.

## The undo

Put back `/root/finance/stock_app.py.bak_S570_f58e09db`, restart `clinic-finance`, healthz 200, read the md5 back (f58e09db…). The kit writes
no data; `finance.db.bak_S570_<stamp>` is kept but never needed for the undo.

## Charter

**Retired:** the clock-only comparison in `_s524_tryable` (a second, narrower capture rule beside charter 11's); the day's-MIN read of
`stock_feed` in `_s488_why` / `_s488_first_push`. **Left for later:** amir_day's `_s488_ending` words ("a purchase export that reaches that
day" rather than the brief's "a purchase report that reaches dd-mm") — amir_day is read only in this brief, and the head of the sentence already
names the day. **Left out:** nothing.

## Files

`KIT_ID.txt`, `PINS.sh`, `SUMS.md5`, `make_s570.py` (the builder: four anchored edits), `walk_s570.py` (the walk), `state_s570.py` (the owner's
proof read back on copies), `install_S570_PROOF_MORNING_WINDOW.sh` (the installer). No `.json` in the kit folder.
