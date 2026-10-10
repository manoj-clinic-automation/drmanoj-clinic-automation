# S500_REPORT_CHECK — the two morning Marg reports: steps with pictures, RIGHT or WRONG with the step to redo, two tries, a short closing refused, the owner told only on failure

Kit S500 · **D694** · faults **F-799, F-788, F-801** · brief `claude_code_briefs/S500_REPORT_CHECK.md` (Sanjeevni chat, session 301, 08-Oct-2026).
Built under `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` (10-Oct-2026).

## What and why

- **D694 — the page says right or wrong.** The two morning reports (yesterday's bill-wise sale report, the closing stock) are made from
  Marg's REPORT login by whoever is on morning duty. *Aaj ki reports* (`reports_tile.py`) now carries the steps of each, with Marg's own
  screens, behind **Kaise banayein** (`/finance/reports/aaj/kaise/sale` and `/stock`, their own pages, never refreshed; `reports_guide.py`,
  the thirteen pictures as hexadecimal text in `reports_guide_pics.py`). Every file for the due day received this morning is one of his
  TRIES (files within `reports.try_gap_min` minutes of each other, by the export's own capture stamp, are ONE try); the row says
  **Sahi hai** or **Galat hai · koshish N / M** with the one step to redo and *Ek koshish aur hai*; at `reports.tries` wrong tries it
  says *Doosri baar bhi galat* and that the owner has been told. A right copy, whenever it comes, wins. A wrong file received before
  today is not a try and is said under the row. The page still writes nothing.
- **F-799 — a SHORT closing is wrong, and never loaded.** `reports_watch.closing_short(con, as_on, n_items)` is ONE rule read by the page,
  by `/finance/stock/api/snapshot` (`stock_app.py`) and by the watch: a closing with fewer items than `reports.closing_min_share` percent
  (90) of the MEDIAN of the last seven closings loaded before it (within 21 days) is short. The page says *Khali stock wale item nahi
  aaye* (when the list holds no zero-stock row) with the counts; the snapshot door answers **409 `short_closing`** and writes nothing
  (no `stock_snapshot`, `stock_feed`, rate or reconcile row); manojz's pusher prints *"server said 409 -- nothing recorded"*, is not marked
  done and tries again with the next export. A closing is also wrong when it is not the totals list (`DEFAULT` → step 4), a part of the
  list (`SUBSET`), or not the WHOLE STORES totals list (the certified reader does not take it). No earlier closing → no judgement.
- **The owner's message, only on failure.** `reports_watch.tick(con)` rides the ten-minute job (`order_rules.tick` → `_s500_reports`, one
  guarded call): at most ONE row per report per day in `marg_report_alert` — kind `wrong` (wrong on `reports.tries` tries) or `late`
  (not right by `reports.late_hhmm`, 10:00; a file still being checked is given 30 more minutes). Unsent rows of today go as ONE ntfy
  message through the same private topic the freshness watch uses (`NTFY_URL` in `freshness.conf`, never printed). Never on a Sunday; a
  row not yet sent is withdrawn when the report turns right; a right morning sends nothing. A message leaves the box only when the
  connection's main database IS `/root/finance/finance.db` and no push stub is set; with `REPORTS_NTFY_STUB=<file>` it goes to that file.
- **F-788 — a refused file under no day.** A non-verified file received today that is NOT a one-day report for the due day (a range
  report; the medical PC's own refusal, whose day is not known) is shown under the row as *Aaj HH:MM baje ek bikri report manzoor nahi
  hui* and counted in the owner's line as *N refused (not the day's report)*. It is not a try and does not make the row *refused*.
- **F-801 — the voucher proof reads the NEWEST closing.** `stock_app._s446_proof`: `R, L = before[-1], after[-1]` (was `after[0]`). Amir's
  orthotic vouchers, marked entered on 04-Oct and corrected in Marg on 08-Oct, are judged on the newest closing that has both Marg's
  figure and our own — his renames open by themselves on the next morning's two reports.
- **The salt card's words** (`amir_day.py`, wording only): a Marg text export is read since S480/S483, so *"Excel mein (text nahi) … text
  file server nahi padhta"* goes; the heading is *Ek export aur: SALT WISE ITEM LIST* (the duty map's `door_marker`, unchanged), the
  sentence *Text ya Excel, dono chalte hain*; the staff line and the owner's two lines drop *(Excel)*; the page's salt-row hint too.
- **The bill-gap card is floored for a staff login** (`aaj_floor.floor_for`, the parent's rule of 07-Oct): a gap whose later day is
  before the lists' floor is not shown to staff; the owner, a doctor and `/api/status`'s English line see every gap.

## Pins (server) — FROM → TO

| file | FROM | TO |
|---|---|---|
| `/root/finance/reports_tile.py` (+498 lines) | 6f7cf490c949495e3e714b7dd688b7af | 01f67f4d034cdefd2d9254263e47828e |
| `/root/finance/stock_app.py` (+14 lines: the guard, the proof) | cc06dac9e3ab60a85d76e2409815b5af | bfc2a40bff0d8f0050078ea49f990eda |
| `/root/finance/amir_day.py` (wording only) | 59b035da84a6648b94c1977d0c810b9d | f1ce78e8bd788fbbb8c9774c04119af9 |
| `/root/finance/order_rules.py` (+14 lines: one guarded call) | ee17c1872acd0c440868a915fa5014df | 79f21c1ee1f763b1ac06b370e3d77b79 |
| `/root/finance/reports_watch.py` NEW | absent | a8bbd95e597c44418d82ae895750b9c1 |
| `/root/finance/reports_guide.py` NEW | absent | 20a05704d8183af340cec4b138aa9fb1 |
| `/root/finance/reports_guide_pics.py` NEW (data only) | absent | d7f4f3316338acf3d34502559b1ae8f9 |

The four edited files are built ON THE BOX from the live bytes by `make_s500.py` (every anchor exactly once; the two replaced spans hashed to
their own pins; nothing written unless all four build). The three new files are shipped here and placed as they are. All seven are the
chat's files, given byte for byte in `claude_code_briefs/S500_parts/` (their md5s are in `SUMS.md5`).

Read only (md5 before = after): `aaj_floor.py`, `spine/marg_read.py`, `export_watch.py`, `shelf_figure.py`, `item_alias.py`,
`/root/marg_ingest/marg_take.py`.

`finance.db`: ONE new table `marg_report_alert` (`CREATE TABLE IF NOT EXISTS`) and FIVE `setting` rows (`INSERT OR IGNORE` — a value he has
changed is never moved), both by `reports_watch.ensure(con)` in the installer, after `finance.db.bak_S500_<stamp>` (backup API):

| key | value | meaning |
|---|---|---|
| `reports.tries` | 2 | wrong tries of one report before the owner is told (1–5) |
| `reports.late_hhmm` | 10:00 | the hour by which both must be right, else he is told |
| `reports.closing_min_share` | 90 | percent of the recent lists (the median of the last seven) below which a closing is SHORT (0 = off) |
| `reports.try_gap_min` | 3 | files of one report within these minutes are one try (0–30) |
| `reports.alert` | on | the owner's phone message (on / off) |

The settings are database rows for now, as S488's four and S494's two are: the owner's settings card (`porders_s454.py`, parked) lists only
the keys it knows; these join it when that file is next opened.

## Not touched (md5 before = after, or the install is undone)

`finance_app.py`, `/root/portal/portal.py`, `/root/portal/tile_grants.json`, `aaj_kaam.py`, `aaj_kaam.html`, `aaj_duties.json`,
`owner_console.py`; S486's other eleven parked files (`porders_s454.py`, `porders.py`, `porders.html`, `darpan_kal.py`, `darpan_kal.html`,
`order_sheet.py`, `order_sheet_pdf.py`, `finance_ui/finance_approvals.html`, `spine/spine_read.py`, `spine/order_rehearsal.py`,
`spine/selftest_spine.py`); the clone's `claude_code_briefs/DUTY_MAP.json` (v9, `20162448…`); the crontab. No duty is added, moved or
removed: `DUTY_MAP.json` / `DUTY_MAP.md` are not changed (the page's three door markers stay on it). No tile, no grant. The spine is not
changed. Nothing on the medical PC or on manojz changes. `shelf_figure.py` is not touched (F-787 / F-790 stay with kit S498).

## Off switches

- `/root/finance/_off/REPORTS_WATCH_OFF` (or `ALL_OFF`) — a file; stops the owner's message (nothing to restart). The page then says
  *Doctor sahab ko bataiye* in place of *khabar ja rahi hai*.
- `reports.alert = off` — the same, from the database.
- `reports.closing_min_share = 0` — switches the short-closing rule off for the page AND for `/api/snapshot`.
- A real trim of Marg's item list by more than 10 percent would be refused until the setting is lowered (refused closings never enter the
  reference). The median can only fall when short lists are LOADED unjudged (after 21 days with no closing, or while the share is 0): after
  such a spell look at the reference before turning the rule back on. The 250-row 06-10 snapshot already in `stock_snapshot` is history;
  this kit does not repair it.

## Files

| file | what |
|---|---|
| `install_S500_REPORT_CHECK.sh` | gate 0 (ALREADY / HALF-INSTALLED) → lock → gates → FROM pins → build → compile all seven on both pythons → walk on scratch copies → (DRY=1 stops; nothing written) → file backups → DB backup → place (three new, then the four; `order_rules.py` last) → md5 read-back → data → ONE restart → healthz → gated curls → journal → read-back (`--say`) → nothing else moved → the test message LAST; restore on red (`order_rules.py` first, the three new files removed) |
| `make_s500.py` | the given builder of the four edited files (anchored edits, FROM → TO pins) |
| `reports_watch.py` · `reports_guide.py` · `reports_guide_pics.py` | the three given new files |
| `PINS.sh` | the seven TO pins |
| `walk_s500.py` | the walk, sections 1–10 of the brief's §4, each with its control on the OLD files (the three new files absent there); the staff-eye section signs in through a scratch portal as eight logins |

Undo: put back the four `.bak_S500_<from8>` files (`order_rules.py` first), remove `reports_watch.py`, `reports_guide.py`,
`reports_guide_pics.py` and their `__pycache__` entries, restart `clinic-finance`, healthz 200, read the md5s back. The table and the five
setting rows may stay (nothing reads them without the files); the database backup is used only if the brief's data change must be reversed.

## Charter (S303)

- Retired: nothing on a screen is retired; the old wording of the two morning rows (*aa gayi, jaanch poori* with a count) is replaced by
  the right / wrong wording for those two rows only — every other row is worded as before. The page's old two-line menu path
  (`Daily Reports → Sale Reports → BILL WISE STATEMENT`) is replaced by the REPORT login's path.
- Left for a later build: `shavez.closing_stock`'s `due_sql` counts a VERIFIED-but-wrong closing as done (a DUTY_MAP v10 question);
  the five settings on no card yet; the hours of the spine's evidence job (a sale report exported at 06:00 reads *jaanch ho rahi hai*
  until 08:00); `DUTY_MAP.json`'s `amir.salt_list` `duty_hi` and `aaj_seed.py` still say *Excel*.
- One fact, one place: the short rule is one function; the page reads `reports_watch`'s own setting readers; the message is sent from the
  one process that reads the page's own `status()`.

The server line, after the publish:

```
cd /root/deploy/repo && git pull --ff-only && bash deploy_kits/S500_REPORT_CHECK/install_S500_REPORT_CHECK.sh
```

(Run once already from a byte-identical copy of this folder and of the map at `/tmp/s500kit/repo/`; run from the repository it answers
ALREADY INSTALLED.)
