# S763_F802_AGAIN — the same export, received again (F-802's permanent fix)

**Session 417 (the Sanjeevni chat), 09-Nov-2026. D867 / D868 / D879. No screen changes beyond a cleared duty; no mock.**

## What was wrong (F-802)
The staff export a Marg report whose bytes are the same as one the server already holds. The medical PC's watcher dropped it without a word: it hit `TXT_SEEN`, or the converted report was already in the spool. The server's `take()` would have answered ALREADY and written nothing anyway. So an unchanged **salt-wise item list**, exported after a salt correction was ticked, could never clear Amir's *salt list due* — the duty stayed open for ever.

## What changes
| where | file | from → to | what |
|---|---|---|---|
| medical PC | `D:\SendToClinic\marg_watch.py` | `df7736e9` → `afcc3fd9` | A repeat export — text **or Excel** — says so in the log (`= AGAIN …`) and in the census (*same as an earlier export (…)*). When the file was exported **after** the capture it repeats (not a copy kept in `_captured_txt`, not while the text reader is on hold), a re-receipt `{name, md5, at, from}` is kept in `_captured_txt\again\` and sent with header `X-Marg-Note: again`, by its own thread. A waiting re-receipt is tried again at every start and every census, and expires after 3 days. A restart re-reading old files sends nothing. The start line names S763. The selftest collects re-receipts and never sends them. |
| server | `/root/finance/marg_door.py` | `565ad9c8` → `fcbcfb13` | `X-Marg-Note: again` → one record row in the new table `mi_receipt` (made on first use; nothing decides on it). For a VERIFIED report, the setting `mi_again:<TYPE>` moves forward to the moment the PC says it was **exported** (never later than now, never backwards). Answer **AGAIN** *"received again, same as <stamp>"*. An md5 it does not hold → **UNKNOWN**, nothing written. Another re-receipt of the same md5 within a minute adds no record row. A locked database → **BUSY** (503; the PC tries again). `mi_file` is never touched, so its `received_at` stays the first receipt (300+ readers mean that). |
| server | `/root/finance/amir_day.py` | `c86bb8e5` → `49e1eba1` | `_SALT_LAST` = the newest of a VERIFIED salt list's first receipt and `mi_again:SALT_WISE_ITEM_LIST`. With no `setting` table (a bare test db), the old SQL is used. |
| server | `/root/finance/reports_tile.py` | `f44fe768` → `4eaeadbd` | the salt row reads the same |
| repository | `claude_code_briefs/DUTY_MAP.json` | `78b5f07e` → `fdec576c` | v21, kit S763: `amir.salt_list` due_sql = amir_day's, byte for byte. It reads only `mi_file` and `setting` (always there), so it can arrive with ANY pull before this install; with no `mi_again:` setting yet it reads exactly as v20. `manoj.salt_list` (date-based) is unchanged. The parent's `aaj_seed.REWRITE` has no salt piece, so nothing to re-fit (F-1024). |

Read only: `/root/marg_ingest/marg_take.py` 5cad2d24, `marg_ingest.py` 828c4dad, `D:\SendToClinic\marg_push.py` 3f5ed144.

## The cold review (an independent reviewer, no blocker) — what changed after it
The duty-map timing (the map read a table that might not exist yet) → the re-receipt moment now lives in the `setting` table, which is always there. The arrival time used instead of the export time → the PC's export moment, capped at now. A refused copy offered again could send a re-receipt → no longer. The text hold switch did not stop re-receipts → it does. The two proofs took two copies → one copy. `retry_refused`'s words → it now knows *same as an earlier export*. An unreadable re-receipt was never expired → it is. The Excel route of the salt list → covered. The door: the length is checked before the body is parsed, and a locked database is BUSY. **Kept by the owner's ruling (D879):** a list unchanged since the tick satisfies the duty. **Not this kit:** the owner's own weekly / monthly lists (date-based).

## Proofs
- `walk_s763.py`: **54 of 54 green** on made-up rows. It covers the door (export time, never backwards, a clock ahead, other types), the salt duty, the map and the tile. It covers the watcher too: restart cases, a kept copy, the hold switch, the Excel route, the sender's answers, and end to end through the door's own code. **CONTROL** on the live files: all 30 S763 checks red; the 19 old and guard checks green; a PC clock over 10 min ahead, or no export time: recorded, never counted.
- `marg_watch.py --selftest`: 72 OK, old and new identical. `reports_tile` selftest: 54 checks, 0 failures, old and new identical.
- Earlier walks: S749 and S750 identical old vs new. `walk_s761` is run on the box by the installer (it needs a copy of finance.db).
- `proof_s763.py` on ONE copy of finance.db (both readings): the kit's files and the live files read today **the same**. That covers the salt duty, the salt row, and every duty of the map by fingerprint. A made-up re-receipt in the copy clears the salt duty only by the kit's files.
- `rehearse_s763.sh` on a made-up root: **6 of 6** — DRY (nothing written) · a changed live file → STOP · the map not pulled → STOP · install · ALREADY INSTALLED · a forced red at [7/7] → the three files back, the lock released.

## Install — server first, then the medical PC
**Server** (the owner's paste). DRY first; it writes nothing:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s763kit && cp -rp /root/deploy/repo/deploy_kits/S763_F802_AGAIN /tmp/s763kit && DRY=1 bash /tmp/s763kit/install_S763_F802_AGAIN.sh
```
Then the install:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s763kit && cp -rp /root/deploy/repo/deploy_kits/S763_F802_AGAIN /tmp/s763kit && bash /tmp/s763kit/install_S763_F802_AGAIN.sh
```

**Medical PC** (the chat, through the file tools, F-764), only after the server says DONE: Drive `ToMedical\_kit`. The live `marg_watch.py` is read first and kept beside as `marg_watch_S722.py.superseded`. Then `marg_watch.py` (afcc3fd9) is placed and read back by hash. It is on the agent's built-in list (`KIT_FILES`), so no `KIT_MANIFEST.txt` line is needed or written. The agent installs it at its next kit check when it differs and compiles, then restarts the watcher (`RESTART_FOR`). To read on the heartbeat / log: `marg_watch.py 62caddbd`, *"marg_watch S679+S722+S763 starting"*.

## Undo
- **Server:** the installer prints the one line (the three `*.bak_S763_*` back, finance restarted). The `mi_receipt` record table and any `mi_again:` settings may stay. After an undo, the map v21 still reads a salt re-receipt the door wrote before; the old amir_day does not. So Amir's card and the console could differ until the kit is reinstalled.
- **Medical PC:** `_kit\marg_watch_S722.py.superseded` back as `_kit\marg_watch.py` (df7736e9). The agent puts it back at its next kit check.
