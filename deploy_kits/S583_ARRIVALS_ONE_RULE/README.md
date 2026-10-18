# S583_ARRIVALS_ONE_RULE — one rule for "Marg carries this arrival"; an arrival expires; the owner's line

**Brief:** `claude_code_briefs/S583_ARRIVALS_ONE_RULE.md` (v3, Sanjeevni session 324, 18-Oct-2026), written from `claude_code_briefs/REPORT_S580.md`.
**Charter:** `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` v1.1. No D or F number of its own. Three Sanjeevni files, no new file, no data step,
no new staff sentence. Kit shape: S577's.

## What it does

- **`stock_figure.py` — THE one arrival rule (charter 2).** Three copies of "the spine carries this arrival" (`shelf_figure.scan_arrivals`,
  `stock_watch._arrivals`, `stock_watch.bill_pending_lines`: a purchase of the item *from the same supplier key, dated on or after the order
  day*, never expiring) become one function:
  - **`carried(con, sp, line, ctx)`** → the purchase of Marg's that carries a tapped or scan-tied order line (`supplier, supkey, bill, date,
    units, how`), or None. In order: **(a)** the line's own `billed_bill_no` (Marg's answer, S537); **(b)** a bill that is the `billed_bill_no`
    of ANOTHER order line of the same key never carries this one; **(c)** a bill dated BEFORE the order day carries only from the order's own
    vendor key and within `arrival.back_days` before the order day; **(d)** the own vendor's bill dated on or after the order day (the rule as it
    was); **(e)** another supplier's bill dated on or after the order day. The first eligible, oldest date first, wins. None while `sp.ok` is
    False. A bill number is matched with spacing, case and leading zeros folded — the spine prints A.A.'s 467 as `0000467`, Marg's own line
    on the order says `467` (found by the walk's rule-(b) control on the first dry run). On the 18-Oct copy: CROCAL and PREGHYPE under (c) (Shivaaz 3463 of 01-10, order 02-10), PRETOL 8 (Kedar A000203) and POWERGESIC
    (Janta 23672) under (e). The named edge: a carrying bill dated on or before the count day still drops the arrival — the goods are in the count.
  - **`expired(con, sp, line, ctx)`** → True when `carried()` is None AND the spine's purchase reach (`reach(sp)`, read once per `Ctx`) has
    passed the arrival with its grace: `last_pur` ≥ arrival day + `arrival.bill_grace_days` AND `stamp_iso(pur_stamp)` > arrival moment + grace
    — ISO against ISO, never the `YYYYMMDD-HHMMSS` stamp against the ISO moment (charter 11). False while the spine is unread or the reach is
    empty: the arrival keeps counting (charter 1b). `covers()` is not used.
  - **`taps()`** counts a tapped line while it has no `billed_bill_no`, is not carried and not expired. **`scan_arrivals()`** (moved here from
    `shelf_figure`) counts a scan-tied unanswered line at its ordered quantity under the same rule, the arrival moment being `scan_at`;
    `scan_lines()` lists them in `_arrivals`' shape. `shelf()` adds both (its docstring says so). **`arrivals_open()`** lists every expired,
    uncarried line (item, units, moment, who or "scan", vendor, order, kind, `scan_tied`).
- **`shelf_figure.py`:** `scan_arrivals` removed; the header's "arrived, not yet in Marg" bullet points at the one rule. Nothing else.
- **`stock_watch.py`:** `_arrivals` marks `in_spine = stock_figure.carried(line) is not None` and nothing else (expiry is `taps()`' and
  `scan_arrivals()`' — `open_trace`'s finding 2 and Amir's *"arrival tapped, bill entry baaki"* fix keep seeing a tap Marg never carried); it
  carries `scan_at` and `billed_date` beside the old fields. `bill_pending_lines` replaces its own test by `carried()` (routing, words and grace
  unchanged; the walk and the installer prove its lines equal before and after). **The owner's line** `arrival_needs_you` is read by
  `needs_you_lines` — one English line per `arrivals_open` item whose order has a scan tie: *"ITEM: counted as arrived when the VENDOR bill
  was scanned dd-mm HH:MM -- not in Marg's purchases up to dd-mm"* (a tapped line on a tied order: *"... when WHO tapped it dd-mm HH:MM (VENDOR)
  ..."*; none live today). A tapped line on an untied order stays with `amir_day._d712_owner_lines` (D712, unchanged): no arrival is said twice.
  **New setting `arrival.back_days`** beside `arrival.bill_grace_days`: int, default 2, lo 0, hi 15, `seed=None` — no row written; it appears
  on the owner's "Counts & watch" settings card like the others.

## The gap this leaves (named, the brief 3.3)

An **untied tap where the same supplier has an unrelated scan**: D712 skips it (a scan from that supplier exists) and the arrival line skips
it (its order has no tie). Left for the D712 kit.

## What stays (the brief 3.4; the report's "Charter: left")

- `porders.detect_supplies` (same vendor, bill date ≥ order day, read from `purchase_line`) and `order_rules._s470_arrivals` (same vendor,
  date ≥ order day) — two remaining copies of the rule, left with the owner's closure of the ordering flow as the reason. After this kit they
  can disagree with `carried()` for an UNCOUNTED item's transit (a counted item's transit is dropped by `_s470_inputs` because it is inside
  the shelf figure). Named for the ordering kit and S486 B.
- For later: per-line arrival from the scanned bill's own lines (the Scan App's readings); units-based matching (one bill line answers at most
  its own units).
- The record: the 18-10 `s577_shelf_gap` set (12:20) keeps TOLTRIS PLUS's +500 unflagged. The next `end_day`'s set is the first correct one.
- The witness: `expected_units`' old-way column changes mid-week for these items (4b-2's start condition).

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/stock_figure.py` | cb5f24aacf7748752206619ce8bbb1e3 | 72b9135ab00db0af2fe8e54091147bb5 |
| `/root/finance/shelf_figure.py` | a544afda07b4632e9bc05e97c256dde6 | 14ef2c24e272ae8ea684615ae82b6cb5 |
| `/root/finance/stock_watch.py` | bc6885217a9f7ca7d8273021fcf6315a | 80896ce257b155f21429a559eec891b9 |

Read only, never edited — the installer prints their live md5 and STOPS if one moved (this kit was built reading them): `porders.py`
a5a823bf, `order_sheet.py` f00f0163, `order_rules.py` 79f21c1e, `stock_app.py` f279a3be, `amir_day.py` 73882a83, `loss_piles.py` 2b9023fd,
`purchase_app.py` 98f7d9f0, `item_alias.py` 111a8e48, `qty_words.py` 706db7cc; and, proved unmoved: `stockmatch.py`, `porders_s454.py`,
`darpan_kal.py`, `finance_app.py`, the spine's three files, `portal.py`, `tile_grants.json`, `DUTY_MAP.json` (no duty added, moved or
removed), the crontab. `finance.db`: no data step (backed up all the same). Service `clinic-finance`, restarted once. Install window
08:00–23:59 IST with the spine green and under 30 minutes old; `DOCTOR_AUTO_OFF` set around the restart, removed after healthz 200.

## The install (`install_S583_ARRIVALS_ONE_RULE.sh`)

Gates (window, lock, SUMS, KIT_ID, PINS) → the FROM pins and the read-only md5s → the spine green → build from the live bytes (18 anchored
edits, each anchor exactly once) → compile on both pythons → scratch (the finance folder twice, finance.db / assets.db / spine.db by the
backup API) → the walk on the OLD files (every control red) then on the NEW files → DRY stops → the install-day state on the OLD and the NEW
files on the same copy (Amir's lines must be equal, else STOP) → backups (`finance.db.bak_S583_<stamp>`, `<file>.bak_S583_<from8>`) →
`DOCTOR_AUTO_OFF` → the three files staged and renamed in ONE command, `stock_figure.py` first → one restart → healthz 200, the pages 302 →
journal clean → the state AFTER (the live files on a fresh copy) → nothing else moved → md5 read-back → the off-switch removed. Red after
placing: the three files put back in one command, one restart, healthz. `order_rules tick` and the 06:30 job pick the files up on their next run.

## The walk (`walk_s583.py`)

On scratch copies only, the real app in one process (the walk's own header session), its own rows by key (`W583 FIX TAB` from `W583 FIX VENDOR`,
tapped at the walk's moment; an order-32-style RYCOBAL D3 line of A.A. created 16-10 13:32:59, scan-tied 17-10 18:22). Sections as the brief's
section 4: print first (every scan-tied and tapped unanswered line with what (a)–(e) say, the 13 items of REPORT_S580 with `shelf()` and the
receipt's basis / provisional, the named edge); TOLTRIS PLUS inside the grace (grace raised to 30 on the copy, then put back) and expired under
the live export, on the owner's line with the brief's words; CROCAL / PREGHYPE by (c); PRETOL 8 and POWERGESIC by (e); the order-32-style line
NOT carried (a 7-day any-supplier rule would take 467); the raw-stamp trap (the stamp against the ISO moment calls a fresh tap "passed";
`expired()` says False; the tap counts 20); the order engine (`_s470_inputs`: LINVIZ 600 equal before and after, TOLTRIS PLUS −500); a
Marg-answered row by (a), never counted, never on the line; the spine missing (nothing dropped); the owner's lines against D712's and
`bill_pending_lines` equal; Darpan's receipt for TOLTRIS PLUS settled at once with the existing words; the grep tests; the 13 items old → new,
the guard's not-judged count, the staff screens' words against `--old-dump`; no ten-digit run. `--state` prints the install-day state (the
installer runs it before and after). `--expect-red` is the negative control.

## Charter

- **Retired:** `shelf_figure.scan_arrivals` (moved into `stock_figure` under the one rule); the supplier-key-and-date tests inside
  `stock_watch._arrivals` and `stock_watch.bill_pending_lines` (two copies of the rule); the old `stock_figure.taps` body.
- **Left (named above):** `porders.detect_supplies`, `order_rules._s470_arrivals`; the D712 gap; the 18-10 gap set's record; the witness column.
- **Dependency state at install:** the spine green and fresh (gate 13/13, under 30 minutes), `arrival.bill_grace_days` = 3 (its live row),
  `arrival.back_days` unset (default 2), `order.stock_basis` = count. The installer prints the state before and after.
