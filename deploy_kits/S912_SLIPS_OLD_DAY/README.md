# S912_SLIPS_OLD_DAY — a missed older-day parchi (Shavez · Siddhi Patel, 14-Nov)

*The parent · S496 · 21-Nov-2026 · built by `make_s912.py` (anchored patches) from the live bytes.*

| file | pin | what changes |
|---|---|---|
| finance/slip_log.py | c2cf351a → 5cfaf728 | Writing a missed parchi reaches **31 days** back (was 7); edits, removals and radd stay at 7. An old day's form opens with the number box **empty** ("us din ki parchi ka number"), never today's next number. A number Shavez marked **Radd on that old day, his radd ask still pending**, can be written as the parchi it was: the ask is set aside ('replaced', kept) and the save says so. Kharab, an approved radd, or a radd with no ask stay refused. "Pehle se likhi hai" now names the slip's day and ID. The Din list shows 15 days, plus the day opened if older. |
| finance/parchi_desk.py | 548d68ca → 10532553 | On an old day the desk's number boxes start empty ("us din ka number"). Its own day list and window unchanged. |

## Proof
- `walk_s912.py` (made-up root): **WALK 29/29**; the live files **12/29** (red).
- `walk_s840` (the desk) the same on old and new; `walk_s844` 31/31 on the new desk; S836's walk the same old/new.
- Cold review: no MUST; its SHOULDs built in (a radd read failure refuses; only a pending radd ask is set aside, never Kharab or a radd with no ask; the wider window for writing only).
- Rehearsal: dry, install, again, undo, undo again, red rollback — green.

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s912kit && cp -rp /root/deploy/repo/deploy_kits/S912_SLIPS_OLD_DAY /tmp/s912kit && bash /tmp/s912kit/install_S912_SLIPS_OLD_DAY.sh
```
`DRY=1` before `bash`: every gate and walk, nothing changed. `--undo`: the two files back.
