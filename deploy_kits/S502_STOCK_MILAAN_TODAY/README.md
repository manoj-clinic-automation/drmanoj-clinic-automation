# S502_STOCK_MILAAN_TODAY — Darpan's Stock milaan shows only today's work; a morning count corrected the same day; TRUECEPROL OD and the TYRO BR line put right

Kit S502 · **D699** · faults **F-812, F-813, F-814, F-815** · brief `claude_code_briefs/S502_STOCK_MILAAN_TODAY.md` (Sanjeevni chat, session 303, 10-Oct-2026).
Built under `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` (10-Oct-2026) — **the LAST patch on the old stock-watch layer.**

## What and why

- **D699 — only today's work on his page** (`stockmatch.html`). Kept: *Aaj ki ginti* (the morning list, an answered row with **Galat likha?
  Badlo** the same day), *Poori ginti ka Sunday* when asked, *Adla-badli?* only while a pair is unanswered and only those pairs, *Kam kyun?*
  only for the open lines he has not answered (a line the rule answered by default is finished work), *Bina bill?* only for claims without
  an answer, *Stock batao*, *Kuchh gadbad hai?*, and **Pichhle 7 din mein kam nikla** (the last seven days' shortages in plain words,
  *Sirf jaankari ke liye — aapko kuchh nahi karna*). The sub-heading says the day only (*Aaj: dd-mm-yyyy*). Gone from his page: the
  06-Sep loss tables and their note box, the progress bar, the heading *06-09-2026 ki ginti · round 1*, *Dobara ginna hai*, *System ne
  dekha*. Those stay on the owner's Loss desk. Every class and colour kept; no new design; phone and PC alike.
- **F-812 — a count can be corrected** (`stock_watch.correct_roster`, `POST /finance/stockmatch/api/spot/fix`). The same day, by the one who
  wrote it (or the owner). The old point is marked `superseded` with a note naming its replacement — never deleted; a NEW point takes its
  place, **judged against the figure the old point was judged on** (its own `expected_units`, through `write_point(expected=…)`), never a
  fresh shelf figure that would take the wrong old point itself as the base. Its loss line is voided, its open trace closed by its own id.
  Still short beyond the allowance → the new point gets its own loss line and trace, as any point would. One transaction; four values
  like `answer_roster`; a second entry of the same count says *Pehle hi likha hai — badalna ho to 'Galat likha? Badlo' dabaiye*.
- **F-813 — the 06-Sep count is sealed for staff.** `/finance/stockmatch/api/recount` refuses a non-owner (403 `moved`, *Aaj ki ginti
  'Stock batao' mein likhiye*). The owner's own recount doors on the Loss desk are untouched.
- **F-814 — a loss line can be voided, never deleted.** `stock_watch_loss_line` gains `void_at` / `void_why` (`ensure()` adds them on every
  call, `PRAGMA table_info` then `ALTER TABLE`); a voided line shows nowhere; its trace is set `seen` by `S502`. `settle_provisional` is
  NOT changed (it judges on the Marg records while `write_point` judges on the shelf figure — an automatic re-judge would mix two bases).
- **Superseded points are skipped** where points are picked or summed: `last_point` (also the anchor of `open_trace` and the allowance),
  `month_leak`'s points, the watch list's last three points and its monthly trend. Recency-only reads stay as they are (`_candidates`'s
  newest point, `build_roster` / `preview_roster`'s no-repeat window, `points_n`, `full_count_points`'s once-guard, `roster_view`'s
  lookup by id, `settle_provisional`'s provisional rows).
- **The data fixes** (`fix_s502.py`, keyed by content, idempotent, run twice on the walk's copy, once on the live database after its backup):
  **A** TRUECEPROL OD 10-Oct — the 12:01 count (13 patte + 7 goli) written into the sealed 06-Sep count by *Dobara ginna hai* becomes a
  new point of 137 replacing point 377 (superseded), the roster reads 137, the shelf-fix row leaves the 06-Sep count (`count_id` negated,
  a note says why; no DELETE); the Loss desk's cached line is recomputed only under the brief's guard (the stored stamp equal to the
  current one on every part but `fixes`), else left to the desk's next full rebuild. **B** TYRO BR 08-Oct — loss line 2 (70:7 short,
  Rs 13,079.50) voided with the brief's words, trace 30 set `seen`, TYRO BR asked for Darpan's next morning list; point 376 left as it is.

## Pins (server, `/root/finance`) — FROM → TO

| file | FROM | TO |
|---|---|---|
| `stock_watch.py` (+81 lines) | d78c902e0d3258fd0c615cd9715346b6 | c960f6c890e3e83c58b88d8a7f219752 |
| `stockmatch.py` (+31 lines) | f09d9516a9df73941033591af8878c3e | fc1caf4496c4fd072e909b4d3e6784aa |
| `stockmatch.html` (−51 lines) | 0dc4d303434d6f87d9e470bccb79f54c | 02826136d9cbb015dfb44c63ef5263d1 |

Built ON THE BOX from the live bytes by `make_s502.py` (every anchor exactly once; the page's active script checked for the old words).

Read only (md5 before = after): `loss_piles.py 202bfc4e…`, `shelf_figure.py a1e87d1f…`, `stock_app.py bfc2a40b…` (as S500 left it),
`qty_words.py 706db7cc…`. Must not move: `finance_app.py`, `/root/portal/portal.py`, `tile_grants.json`, `aaj_kaam.py`, `aaj_duties.json`,
S500's seven files, the crontab. No duty moves (`DUTY_MAP.json` v9 stands: `darpan.spot_count` keeps its door and marker *Aaj ki ginti*).
No tile, no grant. `loss_piles.py`, `shelf_figure.py`, `stock_app.py`, `finance_app.py` are not edited. The 06-Sep count's own rows are not
touched; one `stock_shelf_fix` row that should never have been written there is moved off the count.

`finance.db`: two columns (`ALTER TABLE … ADD COLUMN`), the data fixes above; one backup by the backup API before the first write
(`finance.db.bak_S502_<stamp>`); `<file>.bak_S502_<from8>` beside each of the three files. Restarts `clinic-finance` once.

## The walk (`walk_s502.py`) and the rendered check

On backup-API copies of `finance.db`, `assets.db` and `spine.db`; rows keyed `W502`; every control red on the OLD files: the correction
(route, the old expected figure, superseded, the trace by id, the audit row), the refusals (yesterday 409, someone else's 403, the owner 200),
superseded skipped (`last_point`, `month_leak`), the recount door closed (403 `moved`), the page server-side as darpan and manoj through the
portal (can_fix on every answered row, no voided or old loss line, the duty marker), the data fixes twice (the second run changes nothing).
**Section 6 — the rendered page — runs at BUILD time on the PC** (the server has no headless browser): `render_stub_s502.py` serves the built
page and the walk's darpan `/api/state` JSON of the fixed scratch copy at `127.0.0.1`; a headless browser renders it at phone width (375 px)
and desktop; the RENDERED TEXT is read (the head comment and the CSS keep the old words on purpose). Its result is in `REPORT_S502.md`.

## Charter (S303) — the retirement register

- **Retired:** *Dobara ginna hai* as a staff door (it wrote into the sealed 06-Sep count, F-813), and the 06-Sep sections on Darpan's page
  (the loss tables, the note box, the progress bar, *System ne dekha*): they stay on the owner's Loss desk.
- **Two stopgaps, to be removed by rung 4b (stock on the spine):** the `void_at` / `void_why` mark on `stock_watch_loss_line`, which goes
  when loss lines are computed instead of stored; and `write_point`'s `expected=` override, which goes when one module holds the two stock
  figures. This kit adds no new source of any figure: a correction is judged on the figure stored with the count it replaces.
- **Left for a later build:** the general re-judge of a loss line when `settle_provisional` changes a point's figure (the late-bills
  redesign, kit S498, F-787 / F-790); the Loss desk's pile cache of the 06-Sep count, last built 29-Sep, rebuilds fully on the owner's next
  desk read (its stamp differs on settings, spine and prices — not this kit's to force).

## Files

| file | what |
|---|---|
| `install_S502_STOCK_MILAAN_TODAY.sh` | gate 0 → lock → gates → FROM pins → build → compile on both pythons → walk on scratch copies → (DRY=1 stops) → file backups → DB backup → place → md5 read-back → the data fixes → ONE restart → healthz → journal → read-back (darpan's state on a copy) → nothing else moved; restore on red |
| `make_s502.py` | the anchored patcher of the three files (FROM → TO) |
| `fix_s502.py` | the data fixes of the brief's §3, keyed and idempotent (the walk's copy twice; the live database once) |
| `walk_s502.py` | the walk, sections 1–5 and 7, each with its control on the OLD files |
| `render_stub_s502.py` | the PC's stub server for the rendered check (section 6) |
| `PINS.sh` | the three TO pins |

Undo: put back the three `.bak_S502_<from8>` files, restart `clinic-finance`, healthz 200, read the md5s back. The two columns and the data
fixes stay (the brief's data change; reversed only if the owner says so, from `finance.db.bak_S502_<stamp>` — say so before using it).

The server line, after the publish:

```
cd /root/deploy/repo && git pull --ff-only && bash deploy_kits/S502_STOCK_MILAAN_TODAY/install_S502_STOCK_MILAAN_TODAY.sh
```
