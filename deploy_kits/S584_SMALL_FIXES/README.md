# S584_SMALL_FIXES — eight small faults, one read; nine settings reach the owner's card

**Brief:** `claude_code_briefs/S584_SMALL_FIXES.md` (v2, Sanjeevni session 327, 18-Oct-2026), from the Fault → Action Register v2.147
(F-875, F-881, F-913 … F-916, F-931, F-932), `S324_MORNING_FLOW_FINDINGS.md` fix E, and the Book v1.22 §10. **Charter:**
`claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` v1.1. No D or F number of its own. Nine Sanjeevni files, no new file, no data step, no
staff duty added or moved (DUTY_MAP unchanged). Kit shape: S583's. One restart.

## What it does

- **F-931 a — `stock_drift.html`:** the *Gap on the last day* cell goes through a small `num()` helper: `null` / `undefined` → `—`, a number as
  before. `api_drift` still sends `last` (None for an item with no PC estimate).
- **F-931 b — `stock_app._r_stock` and `stock_now.html`:** the readiness stock line describes the figures of record — *"Marg's closing stock:
  as on dd-mm-yyyy, taken dd-mm hh:mm (N items). The shelf figure: the count of dd-mm-yyyy carried forward to that closing through Marg's
  sales, purchases and the filed vouchers."* — read from `stock_figure.capture_at` (the capture `_s577_record` stands on) and
  `stock_figure.count_family` (the newest full count's day). `stock_feed` (the PC's `push_expected` and Marg's `push_snapshot` pushes) is no
  longer read there; `out["marg"]` keeps its shape for `readiness()`'s warning; `out["expected"]` is gone. The page's head line:
  *"Stock as on dd-mm-yyyy — Marg's closing taken dd-mm hh:mm; read hh:mm."* (`ours_at` is the read moment, never "processed").
- **F-932 — `stock_now.html`, `stock_loss.html`:** for the doctor (`pc_old_head` in the JSON) a fifth column headed by `j.pc_old_head`, drawn
  from `row.pc_old` (`—` for none), and the note *"PC's old estimate (retiring): shown to you only, retired after the side-by-side week
  (4b-2)."* — the `<th>` is appended by the same JS, never for a checker. The Loss desk draws `D.system_closed.text` (one muted English line
  above the piles) and the group **Approximate spot counts** from `W.approx_lines` after *Traces*; `watchSettings()` draws the rows grouped by
  their `heading`.
- **The nine settings — `stock_watch.py`:** `SETTINGS` gains nine rows with `heading="Amir and the reports"`, `kind="int"`, `seed=None` (no row
  written), English labels, lo/hi, and **no default of their own**: `_default(s)` reads `amir_day.S444_DEFAULTS[key]` or the `[2]` of the
  `reports_tile.OWNER_LISTS` triple whose type maps to the key in `S488_LIST_KEYS` (the two item-list types asserted equal); the seven hints
  are `amir_day.S444_NOTES[key]` through `_hint(s)`; the two list rows carry one sentence each. `settings()` and `settings_view()` read every
  row through `_default`. `PREFIXES` gains `"amir."`, `"owner."` so the desk's save door (`stock_app` `/api/loss/<cid>/pile/setting`) hands
  the nine keys to `set_setting`. `set_setting` keeps a row's existing note (`COALESCE(NULLIF(note,''), excluded.note)`): the S444 seed's
  note survives a save. `amir_day._setting` and `reports_tile._s488_list_limit` are not touched — they already read the row the card writes.
  The card is the stored watch: the installer refreshes it once after the restart (`refresh_owner_view`, no new traces), so the rows appear
  without waiting for 06:30.
- **E of D737 — `stock_app.py`:** `_s584_pur_landed(con, sp)` → the newest `received_at` (folded as `amir_day._norm_ts` folds it) of a VERIFIED
  `mi_file` purchase row (`PURCHASE_BILLWISE` / `PURCHASE_ITEMWISE` / `PURCHASE_BILLITEMWISE`) later than
  `stamp_iso(reach(sp)['pur_stamp'])`, else None; None too when the spine or its purchase reach is missing, or there is no `mi_file` table. In
  `_s521_stage_words` only: when the proof's `why == "pur_behind"` and a report has landed, `pur()` returns no suffix (Amir's *"Purchase report
  nikaaliye"* is gone) and the owner's English for stage A / C says *"purchase report landed hh:mm — judged at the spine's next build (within
  10 minutes)"*. The judgment (`tryable` / `covers` / the verdict) is unchanged. `amir_day._s488_ending` / `_s488_wait_line` are seen, not
  touched.
- **F-875 — `stockmatch.py`:** `P = sa.amir_stage(con, root, d=d)` moves above c2 and is reused; `held = P["A"]["held"]`;
  `c2 = (not pend) and (not not_entered) and (not held)`. A held line is counted with the pending ones in the existing words (*"N orthotic
  line(s) not yet on a voucher"* / *"Vouchers banane baaki: N line"*). Named, not changed: `amir_stage`'s own `a_is_open` ignores `held`, so
  c2 is now stricter than the stage's gate.
- **F-881 — `amir_day.py`:** `KIT = "S584_SMALL_FIXES"`; `/healthz` and the page's JSON follow.
- **F-913 — `purchase_app._s574_page`:** a name joins *also* only when `norm(x) != norm(name)` (`purchase_app.norm`: upper, spaces collapsed,
  trailing `.`/space stripped) — the record's own spelling, in any case or spacing, is never listed.
- **F-914 — `purchase_app._book_bank_cell(r, i, doctor, may_bank)`:** the *add / edit bank details* button and its form slots only when
  `may_bank` (= `_s452_may_advice(con, u)`: the owner and Shavez — the save door's own test). Darpan sees the chip and the masked lines.
  Both callers (`_s574_page`, the OFF page) pass it.
- **F-915 — `order_sheet_pdf._band_geom`:** with numbers `"Ph. " + the numbers`; with none exactly `porders_s454.T["nonum"][0]` (the screens'
  *"Number nahi hai — Dr sahab ko dijiye"*), imported inside the function (porders_s454 imports this file lazily — a top-level import would be
  a cycle). The brief names the dict `WORDS`; the live file calls it `T` (`L(en, k)` reads `T[k]`). `_latin` folds the em dash for the PDF.
  The literal `(number nahi hai)` is in no file.
- **F-916 — read, not changed:** the installer's state step prints, on a fresh copy of the live database, every supplier under both *Still to
  order* (`order_sheet.entries`) and *Done* (`porders_s454._done_today`): the card's sources and lines, the Done order's id, time and `via`, and
  the newest sheet's `taken_at`. The record goes into the report.

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/stock_app.py` | f279a3be440878bb30e418c20a5cf608 | 1883807d7c0872b805f6101e92206878 |
| `/root/finance/stock_watch.py` | 80896ce257b155f21429a559eec891b9 | 555202ce50b8df0b5111b5c56952efda |
| `/root/finance/stock_now.html` | 91cdc56db4fd2d77cf8249c777f36f6f | ff415eb22ee1ad94a95f2c87365341a3 |
| `/root/finance/stock_drift.html` | daa40ee896548b97808cab564cadeee3 | 1a379ec4bd75396b57d1e553c0b71e4b |
| `/root/finance/stock_loss.html` | 0f0dfed658d05d182811005ebce49df3 | fef9e380d22c83454e0e68756cec6aa6 |
| `/root/finance/stockmatch.py` | 10e30d28053aca3090e193502b67b1e0 | 623cb6f1db2640edd6fe2b8ef7f98837 |
| `/root/finance/amir_day.py` | 73882a8391fde24f31e07b0191c5bd89 | 3deca3b95380165d81ae4a8406a53d75 |
| `/root/finance/purchase_app.py` | 98f7d9f05bc06ef6be80181dd9be4c8c | 60f2d846155659c4eddc33e4a0d42b39 |
| `/root/finance/order_sheet_pdf.py` | bcd0cde59b916ea390b94d042627aaf9 | 7fca11db1c016ec86a0c57c5020a7079 |

Read only, never edited — the installer prints their live md5 and STOPS if one moved: `stock_figure.py` 72b9135a, `shelf_figure.py` 14ef2c24,
`loss_piles.py` 2b9023fd, `porders_s454.py` 83079763, `reports_tile.py` 535b5790, `order_sheet.py` f00f0163, `porders.py` a5a823bf; and,
proved unmoved: `order_rules.py`, `darpan_kal.py`, `item_alias.py`, `qty_words.py`, `finance_app.py`, the spine's three files, `portal.py`,
`tile_grants.json`, `DUTY_MAP.json`, the crontab. `finance.db`: no data step (backed up all the same). On the 18-Oct live copy all nine
`setting` rows already exist (the seven `amir.*` seeded by S444; `owner.salt_list_days` 8 and `owner.item_lists_days` 35 too), so every row
reads `set=True` with its row value — nothing changes until the owner saves one. Service `clinic-finance`, restarted
once. Install window 08:00–23:59 IST with the spine green and under 30 minutes old; `DOCTOR_AUTO_OFF` set around the restart, removed after
healthz 200.

## The install (`install_S584_SMALL_FIXES.sh`)

Gates (window, lock, SUMS, KIT_ID, PINS) → the FROM pins and the read-only md5s → the spine green → build from the live bytes (34 anchored
edits, each anchor exactly once) → compile on both pythons → scratch (the finance folder twice, finance.db / assets.db / spine.db by the
backup API) → the walk on the OLD files (every control red) then on the NEW files → DRY stops → the install-day state on the OLD and the NEW
files (the F-916 record, Amir's words) → backups (`finance.db.bak_S584_<stamp>`, `<file>.bak_S584_<from8>`) → `DOCTOR_AUTO_OFF` → the nine
files staged and renamed in ONE command → one restart → healthz 200, the pages 302 → journal clean → the stored watch refreshed once (the nine
rows must be on it, else restore) → the state AFTER → nothing else moved → md5 read-back → the off-switch removed. Red after placing: the nine
files put back in one command, one restart, healthz.

## The walk (`walk_s584.py`)

On scratch copies only, the real app in one process (the walk's own header session), its own rows by key (`W584 …`): the drift template; the
`_r_stock` line and `readiness()['warnings']` unchanged; `/stock/api/now` as the doctor and as a non-doctor, the template's fifth column; the
Loss desk JSON (`D.system_closed`, `D.watch.approx_lines` after a `refresh_owner_view` on the copy with a seeded `basis='approx'` point);
`settings_view`'s nine rows against the copy's own `setting` rows by key, the save door (72 accepted and read back by `amir_day._setting`,
0 and 1000 refused, the S444 note kept, the copy's value put back), the stored watch after a refresh, `owner.salt_list_days` read back by
`reports_tile._s488_list_limit`; E (a seeded VERIFIED purchase `mi_file` row after the reach: the suffix gone, the English *landed*; removed:
back; the two guards); F-875 (the stage, pending and voucher-state readers replaced by the walk's one held line: c2 off with the existing
words); F-881; F-913 (the walk's record, display name differing in case, two merged names); F-914 (darpan / shavez / the owner's book
pages, the door refusing Darpan's `bank`); F-915 (`_band_geom`, the built sheet, the file grep); the F-916 record; the staff screens
word for word against `--old-dump` (the only allowed differences: Darpan's bank button, Amir's suffix / the owner's *landed* English, the
orthotic tick while a line is held); the owner's agree / differ equal; the grep tests; no ten-digit run. `--expect-red` is the negative
control (every `C:` red on the old files); `--state` prints the install-day state.

## Charter

- **Retired:** `_r_stock`'s read of `stock_feed`; the PDF's own copy of the no-number sentence; the hard-coded card heading in
  `watchSettings()`; `KIT = "S533…"` in amir_day; `_s574_page`'s raw-string test for *also*.
- **Seen, not touched:** `amir_day._s488_ending` / `_s488_wait_line`; the sealed findings' frozen *"processed here"*; `amir_stage.a_is_open`
  ignoring `held`; `stock_drift.html` 176 *"Our computed figure"* (the 4b-2 witness); `stockmatch.KIT` still says S502 (the brief did not
  name it).
- **Left (named):** `api_drift`'s PC series (the 4b-2 witness); `porders.detect_supplies` and `order_rules._s470_arrivals` (S583's "left");
  F-916's screen (a mock-up, then the ordering kit); the D712 gap.
