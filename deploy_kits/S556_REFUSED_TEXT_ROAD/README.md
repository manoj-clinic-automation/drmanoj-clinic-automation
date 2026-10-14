# S556_REFUSED_TEXT_ROAD — a report the medical PC's reader stopped on is held, not called wrong (F-893)

Brief: `claude_code_briefs/S556_REFUSED_TEXT_ROAD.md` (v3, Sanjeevni session 316, 14-Oct-2026). Repairs **F-893**; no D number. Project: Sanjeevni.

## What and why
On 13-Oct the medical PC's reader could not read the 12-10 sale report. Shavez's page said *"Medical PC ne file manzoor nahi ki — dobara banaiye"* —
a redo that could never cure it — and once the reader was mended (S546) the refused report waited for a fresh export.

- **The medical PC (marg_watch.py S556):** when `marg_txt.py` beside the watcher changes (its size / mtime, held still 10 s), every text it refused in
  the last three days (and not taken since) is offered to the new reader again, within a minute, with nobody exporting anything. If capture was off at
  the start, the first turn of capture from off to on runs the start's full retry. One log line:
  `reader changed (marg_txt <md5[:8]>): N text(s) refused in the last 3 days offered again, K taken`. A fault is logged once and never stops capture.
- **Aaj ki reports (reports_tile.py):** a refusal whose reason is exactly `the medical PC refused it: the reader refused it (line N)` (a *reader stop*,
  `reader_stop()`, the ONE rule) is no try and no loose line: the row reads *"✓ Report aa gayi (09:23 baje) · Aapko ab kuch nahi karna."* and who has
  been told (*khabar chali gayi hai / ja rahi hai / Doctor sahab ko bataiye*). On the owner's login the row also says *"the medical PC's reader could not
  read it (line N)"*; his summary line adds *"sale report held: the reader could not read it (line N)"*. The hold ends when any VERIFIED copy of that
  report is received after it (an ended stop is dropped). `hindi_reason` says *"Medical PC is file ko padh nahi paya — aapko kuch nahi karna."* for a stop.
- **The owner's morning message (reports_watch.py):** a held row gives one `reader` item: *"The sale report of 12-10 came at 09:23, but the medical PC's
  reader could not read it (line 43); the staff were not asked to redo it."* — never `wrong` or `late` for it.
- **Darpan's card (order_sheet.py):** `refused_sheet(con, staff=True)` (his card) does not show the newest refused sheet when it is a reader stop; the
  owner's lines still name every refusal. Both sides compared in one time shape.
- **DUTY_MAP v14:** `shavez.sale_report` / `shavez.closing_stock` do not count the newest due day while a reader stop of that report received today has
  no VERIFIED copy after it; `darpan.order_sheet` counts the newest refused sheet only when it is not a reader stop. The SQL GLOB is proved equal to the
  Python rule by the walk. DUTY_MAP.md: the three rows, the S556 log line and S543's owed line.

Every other refusal keeps today's words exactly (the walk proves nine kinds byte-identical).

## Pins (FROM → TO)
| file | FROM | TO |
|---|---|---|
| `/root/finance/reports_tile.py` | 01f67f4d034cdefd2d9254263e47828e | 535b579011004ba2e8d8c41070067b2c |
| `/root/finance/reports_watch.py` | a8bbd95e597c44418d82ae895750b9c1 | 428c389c0cbac3eab881fa99d4659b06 |
| `/root/finance/order_sheet.py` | 8c50d41eda61ba31198156b2fae2f12f | 247eeb48db8cc007faedfe14f3676893 |
| `claude_code_briefs/DUTY_MAP.json` | ead2be78869605dfd2580347f33d4017 (v13) | 891defd8431e291b1a152f9e3c85f8c6 (v14) |
| `claude_code_briefs/DUTY_MAP.md` | 96219048d76ed65422c5bafcb8f1e697 | a03b5d97ffe64d70550a90fa9c4bc28b |
| Drive `ToMedical\_kit\marg_watch.py` | 0a78ae15be60d8a0293b96ecfa38f35b (S488) | 39fa27739757ff8e9c8731f77d07b40b (S556 = this folder's `marg_watch.py`) |

Read only, pinned by the installer: marg_door.py dc5c1e36, reports_guide.py 20a05704, aaj_seed.py a97cd07b, aaj_kaam.py cd232b1c, owner_console.py
2b985708, porders_s454.py 72e7fd56, darpan_kal.html f5e279eb, darpan_kal.py fd799a56. At their pins and NOT changed on Drive: marg_txt.py a59a222f,
KIT_MANIFEST.txt 0bf248e4, marg_push.py 566e189e.

## Files
- `make_s556.py` — the anchored patcher (`--only server` from /root/finance + the clone's briefs; `--only pc` from S488's marg_watch.py).
- `walk_s556.py` — the server walk (scratch copies in /tmp; `--expect-red` on the old files and map v13 is the negative control; `--page` after placing).
- `walk_s556_pc.py` — the medical side's walk on manojz (the new watcher's selftest beside the reader S546; the control on S488's watcher).
- `state_s556.py` — the install-day state, before and after (on a copy).
- `install_S556_REFUSED_TEXT_ROAD.sh` + `PINS.sh` — the server installer (PHASE=place, then PHASE=pull after the publish). `rehearse_s556.sh` — on a made-up root.
- `deliver_S556.ps1` — the medical PC, through Drive's `_kit` only; then the heartbeat, up to 45 min.
- `marg_watch.py` — S556, built by `make_s556.py --only pc` from 0a78ae15.

## What it touches
Three files in /root/finance; `clinic-finance` restarted once; the clone's DUTY_MAP by the repository's pull; Drive's `_kit\marg_watch.py` (the
medical PC's agent installs it and restarts its watcher). finance.db is backed up and never written. Nothing is exported in Marg.

## Undo
Server: `\cp -p /root/finance/<file>.bak_S556_<from8> /root/finance/<file>` for the three files, `systemctl restart clinic-finance`, healthz 200; the
map by a new commit putting back the two v13 files (`/root/deploy/DUTY_MAP_v13.bak_S556.json` / `.md`), publish, `git -C /root/deploy/repo pull --ff-only`.
Medical PC: put `marg_watch_S488.py.superseded` back as Drive `_kit\marg_watch.py` (0a78ae15); the agent restarts the old watcher.

## Retired (charter 9)
The reader stop as a loose line and as a wrong try on the morning pair; `hindi_reason`'s *"… dobara banaiye"* for it; Darpan's *"Order sheet adhoori thi
… dobara TEXT mein save kijiye"* for a sheet the reader stopped on; the wait for a watcher restart before a mended reader sees a refused text.
