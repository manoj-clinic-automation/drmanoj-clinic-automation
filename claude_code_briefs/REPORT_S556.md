# REPORT S556_REFUSED_TEXT_ROAD — 14-Oct-2026 (repairs F-893)

**For the owner**
- When the medical PC's reader cannot read a morning report, Shavez's *Aaj ki reports* no longer tells him to redo it. The row now says *"✓ Report aa gayi (09:23 baje) — Aapko ab kuch nahi karna."* and whether you have been told. His *Aaj ka kaam* line for that report goes off.
- You are told once, by the morning-reports message: *"The sale report of 12-10 came at 09:23, but the medical PC's reader could not read it (line 43); the staff were not asked to redo it."* On your login the same row also shows the reader's line number.
- Darpan's card no longer says *"Order sheet adhoori thi … dobara TEXT mein save kijiye"* for an order sheet the reader stopped on. Your own list still names it.
- When the medical PC's reader is mended, every report it refused in the last three days is offered to it again within a minute. Nobody has to export anything.
- Every other refusal keeps exactly the words it had. Tested on a copy of the live data: all checks pass, and the old files fail every check, as they should. Live since 10:49 IST (server). The medical PC has run the new watcher since 10:51 IST, and it is steady.

---

## For the chat

### Live files, FROM → TO (md5 read back on the box)
| file | FROM | TO (read back) |
|---|---|---|
| `/root/finance/reports_tile.py` | 01f67f4d034cdefd2d9254263e47828e | 535b579011004ba2e8d8c41070067b2c |
| `/root/finance/reports_watch.py` | a8bbd95e597c44418d82ae895750b9c1 | 428c389c0cbac3eab881fa99d4659b06 |
| `/root/finance/order_sheet.py` | 8c50d41eda61ba31198156b2fae2f12f | 247eeb48db8cc007faedfe14f3676893 |
| `claude_code_briefs/DUTY_MAP.json` (clone, by pull) | ead2be78869605dfd2580347f33d4017 (v13) | 891defd8431e291b1a152f9e3c85f8c6 (v14) |
| `claude_code_briefs/DUTY_MAP.md` (clone, by pull) | 96219048d76ed65422c5bafcb8f1e697 | a03b5d97ffe64d70550a90fa9c4bc28b |
| Drive `ToMedical\_kit\marg_watch.py` | 0a78ae15be60d8a0293b96ecfa38f35b (S488) | 39fa27739757ff8e9c8731f77d07b40b (S556); read back at 10:50:25 IST. Drive keeps the kit's exact bytes, so there is one md5 |

The map was shared and untouched since the brief: both FROM pins matched, so there was no re-anchor. Unchanged and at their pins: marg_door dc5c1e36, reports_guide 20a05704, aaj_seed a97cd07b, aaj_kaam cd232b1c, owner_console 2b985708, porders_s454 72e7fd56, darpan_kal.html f5e279eb, darpan_kal.py fd799a56. On Drive: marg_txt.py a59a222f, KIT_MANIFEST.txt 0bf248e4, marg_push.py 566e189e. The heartbeat at the open showed `WATCHER FILE ... md5 0a78ae15` and `marg_txt.py up to date (a59a222f)`.

### The install (the server), as the installer printed it
- [1/11] gates green; build lock `/root/deploy/.claude_code_build.lock` taken by this kit (owner `S556_REFUSED_TEXT_ROAD`), and held until this report was written.
- [2/11] pins exact; [4/11] compiles on /usr/bin/python3 and the venv python (3.9.25 both); [5/11] rebuilt on the box from live bytes (16 + 3 + 2 counted edits; map 5 + md 4). Every file landed at its TO pin.
- [3/11] the state before, on a copy: sale report `ok` at 09:21, closing stock `ok` at 09:23, no reader stops today, no held rows, Darpan's card not refused, v13 counts 0 / 0 / 0. [11/11] the state after, on a copy: the same, with v14 counts 0 / 0 / 0. Today's install changes nothing anyone sees today (charter 7).
- [6/11] walk **WALK OK S556: 30 checks green**. **Negative control:** on the old three files with map v13, all **22 of 22 'C:' checks went red**.
- [6/11] S543's walk, read-only, run on the new order_sheet: 74 of 75 green. The one red check is `C: 9 heal` ("before heal_marg_cols the 26 lines … have no Marg RECEIVE / PENDING"). It is red the same way on the live files beside it: S543's install already healed those lines, so that check can no longer go green. All other S543 markers stay green.
- [7/11] backups: `/root/finance/finance.db.bak_S556_20261014_104805` (sqlite backup API, chmod 600), `reports_tile.py.bak_S556_01f67f4d`, `reports_watch.py.bak_S556_a8bbd95e`, `order_sheet.py.bak_S556_8c50d41e`, and `/root/deploy/DUTY_MAP_v13.bak_S556.json` / `.md` (the clone's v13).
- [8/11] placed; md5 read back = TO. [9/11] **clinic-finance restarted once, at 2026-10-14 10:49:04 IST**. Nothing else was restarted. healthz 200. `/finance/reports/aaj` and `/finance/darpan/kal` answered 302 to a plain curl (the login gate, as expected). The journal was clean. [10/11] On a copy of the placed files: `/finance/reports/aaj` as shavez 200, `/finance/darpan/kal` as darpan 200, its `api/day` 200.
- Publish: `PUBLISH_ALL.bat` → origin HEAD `c7e7f28`. This also published S557's pending kit folder and REPORT_S557.md, which were already waiting. Then `PHASE=pull`: `git -C /root/deploy/repo pull --ff-only`, DUTY_MAP.json v14 891defd8, .md a03b5d97, the kit in the clone byte-identical (`md5sum -c` 11/11 OK), the clone clean, healthz 200.
- The three duties' v14 SQL run read-only on the **live** database after the pull: `darpan.order_sheet (0, '2026-10-06 13:48:52')`, `shavez.sale_report (0, None)`, `shavez.closing_stock (0, None)`.
- Rehearsal first, on a made-up root (`rehearse_s556.sh`): (1) red after placing → all three files back byte-identically; (2) green; (3) ALREADY INSTALLED; (4) PHASE=pull → v14. All four passed.

### The walk's output (server, the run that installed)
```
0  the clock: SQLite date 2026-10-14 = IST date; not a Sunday. Due day 2026-10-13. received_at shape '<date>T<time>+05:30' (read from a live row)
   setup on the copy: 2 mi_file rows removed (c9138367 SALE_BILLWISE, c21b2597 STOCK_CLOSING); 0 alert rows; 24 sale_bill rows from the due day;
   382 push-snapshot rows; 1 pushed-report staging row  -> v13 sale_report n 1, closing_stock n 1, darpan.order_sheet n 0
   staff-eye: 'Aaj ki reports' on the portal home of amir, shavez (+ the owner)
1  C: sale stop 09:23 (line 43) HELD, wrong 0, no loose line · C: arrived one higher than the old file · C: all_in false, the owner's line names it
   C: as amir, shavez, manoj: held words, none of Galat hai / dobara / koshish; only manoj reads "could not read it (line 43)"
   C: decide -> ONE 'reader' item in the brief's words (09:45 and 10:45) · C: v14 sale_report n 0 (v13 n 1)
   C: Shavez's Aaj ka kaam has no sale line · C: hindi_reason's new words · C: the tick makes one 'reader' row, sent once (stub), page says 'khabar chali gayi hai'
2  then right 09:40 (a reading in the walk's own folder) -> Sahi hai, hold gone; the map's sale_report n 1 in v13 and v14
3  not stops, each its own run (bare / (line 4x) / SALE_SHORT / cut short / TODAY_NOTE / EMPTY_NOTE / PURCHASE / not known / server refusal):
   the page for shavez and manoj, every row, the owner's line, decide and hindi_reason byte-identical to the old file -- all 9 True
4  C: stop 09:23 + cut short 09:30 -> held, no loose line on a staff login · C: then a VERIFIED SUMMARY1 09:50 -> stop dropped, cut-short line back, SUMMARY1 a wrong try
5  stock stop 09:24 (line 12): the same eight C: checks, all green
6  C: cut short 08:00 + stop 08:05 -> Darpan's card nothing, v14 n 0 (v13 n 1) · C: a stop alone -> card and api/day refused False, v14 n 0
   owner_lines still names it · a cut-short sheet alone -> refused True, n 1 in v13 and v14
   C: the map's GLOB = reports_tile.reader_stop on 17 reasons, (line 4x) included · C: DUTY_MAP v14, kit S556
8  no run of 10 digits in the walk's own output
WALK OK S556: 30 checks green · negative control: 22 of 22 'C:' checks red on the old files and map v13
```

### The medical side (walk 3.1, on manojz, `python -B -I`, copies in `_scratch`, TEMP pointed inside it)
- A: the new watcher's `--selftest`: SELFTEST OK. All 61 earlier checks were green beside the reader S546. The **11 S556 checks** were green: marg_push not importable; (1) the fresh text taken with N=1 K=1 and the 4-day-old one not offered; (2) quiet on further turns; (3a) a text refused again is not kept twice; (3) a broken reader gives one log line, nothing taken and the change not marked, then a good reader takes the text; (4) capture off offers nothing, capture on offers once, and with capture off at start the first off→on runs the full retry; (5) a `taken later` / `overtaken` text is not re-opened.
- B **control:** the old watcher S488 0a78ae15, after the stub reader is mended, took 0 refused copies and has no `reader_changed_retry`. That is **red**: F-893 reproduced. The new watcher took the fresh one: green.
- C: nothing in Drive's FromMedical moved during the walk (0 moved, 0 new). Output had no 10-digit run. `WALK OK S556 PC`.
- Delivery (`deliver_S556.ps1`): pins checked, backup `marg_watch_S488.py.superseded` (0a78ae15) read back, placed and read back 39fa2773 at 10:50:25 IST. Heartbeat (Drive `FromMedical\heartbeat.json`): beat 10:46:33 on 0a78ae15 (pid 6272). Beats **10:51:09 and 10:56:11** were on **39fa2773**, both alive, the same pid 4804, restarts 0, so there was no restart loop. The watcher's log on Drive reads `2026-10-14 10:51:09  marg_watch S556 starting -- text reader S546, text route LIVE, …`. The script reported **DONE at 10:56:30 IST**.
- **The reader-change path is proven by the selftest only. It will first run live at the next reader change** (the next `marg_txt.py` delivered to Drive).

### Calls I made (no question was put to anyone)
1. **The walk's setup also clears `marg_push_staging`** rows of the due day and of today, on the copy only. The older pushed-report door is not in the brief's setup list, but on the live data it proved the 13-10 sale report's arrival. Without clearing it, the old file also counts the sale row as arrived, and "arrived one higher than the OLD file" cannot be measured.
2. **Darpan's `/finance/darpan/kal` is a script-drawn page.** Its HTML always carries *"Order sheet adhoori thi"* inside its script. So the walk checks what the page draws from instead: `/finance/darpan/kal/api/day` as darpan → `order_sheet.refused` False (the S444 rule for script-drawn pages). The page itself was checked for 200 on a copy.
3. **One rule, one place:** `order_sheet.refused_sheet` asks `reports_tile.reader_stop` (a lazy import) instead of keeping a second copy of the rule. If reports_tile could not be imported, Darpan's card would show the refusal as before (the safe side). The SQL twin is the map's GLOB, and the walk proves it equal to the Python on 17 reasons.
4. **Held-row wording:** *"Report aa gayi (09:23 baje)"* with the brackets, as in §0's words for the owner (§2.2 wrote `<small>{when}</small>`). A held row shows no loose lines on any login, the owner's included. His summary line still counts them ("N refused (not the day's report)").
5. **DUTY_MAP.md lines with no `;`:** S543's owed line as given in the brief contains a `;`, so it was written with "—": *"No duty added, moved or removed — reception's order and arrival counts read Marg's open order. `DUTY_MAP.json` is v13."* The S556 line was written the same way. The three duty rows were updated.
6. **Scratch:** the harness refused writing to the Windows `%TEMP%`, and it refused one `Remove-Item -Recurse` of an old scratch folder. Everything ran inside `_scratch\S556_REFUSED_TEXT_ROAD\` (git-ignored), which still holds the walk folders. The PC walk points TEMP/TMP there for its subprocesses.

### What the brief asked me to state (nothing was built for these)
- `marg_report_alert` is keyed `(day, key)`. If a `reader` message goes first, no later `wrong` or `late` is sent for that report that day. If a `late` went first, the `reader` message is not sent, and the held row then says *"khabar chali gayi"* although that message said "not come". Accepted per the brief.
- A text offered again at a reader change and refused again: `_keep_refused` returns early, so there is no duplicate and no new note. The server keeps its old `mi_file` row. N counts texts offered, not new ones: a text with a sent note that was taken later is offered again at every reader change and answers "already taken".

### Charter
- **Retired:** the reader stop as a loose line and as a wrong try on the morning pair; `hindi_reason`'s *"Medical PC ne file manzoor nahi ki — dobara banaiye"* for it; Darpan's *"adhoori … dobara"* for a sheet the reader stopped on; the wait for a watcher restart before a mended reader sees a refused text.
- **Left for later:** none from this brief.
- **Left out:** nothing.
- **Seen, not touched:**
  - (§2.5) `shavez.sale_report` counts from `sale_bill`, so between a right report landing and the spine writing it the line can show for minutes.
  - (§2.5) `shavez.bill_chain_gap`.
  - (§2.5) Reader stops of PURCHASE / SALT / other kinds (prefixed `KIND text --`, so not stops by the rule) still reach staff through the unknown-file card.
  - (charter 13) `darpan.order_sheet` (map, v13 and v14) measures "newest taken" by the newest VERIFIED ORDER_PENDING `mi_file` row. Darpan's card (`refused_sheet`) measures it by `order_sheet.taken_at`. These are two bases for one fact, both already there before this kit. v14 kept the map's base and only added the stop rule and the one time shape.
  - `marg_watch.py` line ~1120 carries an old `"\h"` string escape (a SyntaxWarning on Python 3.12+, harmless on the medical PC's 3.11.9).
  - The live `/root/finance/_off/` holds only `_READ_ME.txt`, so the morning message is switched on.
- **Dependency at install (1b):** the kit adds no new dependency on the spine, a cron pass or a collector. The page's tick still comes from the spine's readings as before.

### Services restarted
`clinic-finance` once (10:49:04 IST). On the medical PC, its agent restarts its own watcher when it installs the new file.

### Not done
- Nothing in the brief was left undone. Nothing was exported in Marg. The medical PC was touched only through Drive's `_kit`.
