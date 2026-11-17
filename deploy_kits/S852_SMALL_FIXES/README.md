# S852_SMALL_FIXES — three small fixes (AF-41 · F-1430 · F-1418)

*The parent · S474 · 17-Nov-2026 · built by `make_s852.py` (anchored patches) from the live bytes.*

| file | pin | what changes |
|---|---|---|
| finance/owner_console.py | fe5e915c → bbe47872 | **AF-41.** His Needs-you line "N days to approve" now says how long the oldest medical day has waited and names a day passed over while later days were approved (on the 17-Nov copy: 03-Nov, waiting 14 days). Every waiting day still listed. |
| finance/parchi_desk.py | de24e3a4 → 548d68ca | **F-1430.** The radd door (`/finance/slips/radd`) refuses a name typed as the clinic ID **on a slip that has no ID** (the door would write the name onto the slip), and goes back to the list the radd came from with the reason. A number goes through as before; a cancelled slip that already carries an old ID (even a name) is marked radd as before. |
| finance/month_read.py | b2d30289 → d4e5cb02 | **F-1418.** The month page's Scan App groups follow the Scan App's own rule: a receipt, statement or summary is not money; a challan counts only once final; a page joined into another paper once; a credit note is LESS, from the group of the bill it is against (its own lane if unlinked); the pharmacy count holds bills only. |

## Proof
- `walk_s852.py` (made-up root, no real number): **WALK 18/18** on the new files; the live files **6/18** (red); a mutation (credit note added, radd off the guard) red.
- `shape_s852.py` on copies of the live databases: every console section the same but the approve-days detail and the timing line; for this month and the two before, no Scan App group or lane gains, and it counts what is taken off. On the 17-Nov finance copy: **SHAPE OK** (the Scan App part runs on the box: its database is not in the nightly copy).
- S846's `walk_s846` 42/42, S851's `walk_s851` 34/34, S844's `walk_s844` OK 31/31 on the new files.

- Cold review (a fresh reader): no blocker; its two should-fix built in (the radd guard only where the slip has no ID -- 8 of the 9 radds so far were on slips already carrying an old name; an older credit-note table read without a fault).

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s852kit && cp -rp /root/deploy/repo/deploy_kits/S852_SMALL_FIXES /tmp/s852kit && bash /tmp/s852kit/install_S852_SMALL_FIXES.sh
```
`DRY=1` before `bash`: every gate and walk, nothing changed. `--undo`: the three files back.
