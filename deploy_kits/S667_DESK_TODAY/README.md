# S667_DESK_TODAY — the parchi desk follows the real day · the parent · session 358 · 27-Oct-2026

**For the owner, in two lines.** A parchi desk left open overnight kept yesterday as "Aaj" and filed this morning's OPD 19858 and X-ray 1420 under 26-Oct. Now the desk moves to the new day by itself, and a save from an old "Aaj" is refused and the page moves to today; the two parchis are moved to 27-Oct.

## Why
The owner, 12:32 IST 27-Oct: *"Today morning we saved one, and the X-ray section says no patient or no parchi saved today, and the drop down also does not populate it."* Read live as shavez: X-ray 1420 and OPD 19858 typed 27-Oct 11:26 sat on 26-Oct; every parchi after 12:21 is on 27-Oct (the page was reloaded). Cause, in the desk's own page: `var day=S.day` fixed at load, never moved; `slip_log.log_slip` rightly treats a day that is not today as a late entry.

## File — FROM → TO
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/finance/parchi_desk.py` | db5fd07f | fb405c12 | E1 `api_save` refuses a save made on "Aaj" (`today_pick`) whose day is no longer today, returning today's state; E2 `onToday` + `fillDays()`; E3 `draw()` moves a stale "Aaj" to the new today (the 8-second poll, and on wake); E4 both saves send `today_pick`; E5 a refused save draws the state it carries. A chosen late day (Kal / a date) is exactly as before. A desk opened before the install (no `today_pick`) saving for another day is refused: *press F5 once*. |

**Data step** `fix_s667_day.py`: OPD 19858 and X-ray 1420 — only rows that are exactly (number, day 2026-10-26, state ok, typed 2026-10-27 11:26) — move to 2026-10-27, one `audit_log` row each (`slip_day_move`, by S667); the new-patient mark worked out again for 27-Oct; any other parchi typed 27-Oct on an earlier day is listed, never moved; `finance.db` backed up first; safe to run twice; the installer stops if the DRY run does not find the two rows as expected. `slip_log.py` not touched. Restarts `clinic-finance`.

**Left as it is:** X-ray 1421 shows as *chhoota* (missing) on today's list — Shavez answers it there as for any skipped number, or enters 1421 if that parchi exists.

## Proven (S358, manojz's VM, python3 + flask, on the 27-Oct bundle's bytes)
`walk_s667.py` **16 of 16 green** on a made-up slip book with the clock moved past midnight (stale "Aaj" OPD and X-ray saves refused, nothing saved, today's state returned; today's save files on 27-Oct; a deliberate late entry still files on 26-Oct; an old page's save for another day is refused (F5), for today it saves; the data step DRY / real / again; the deliberate late entries untouched). **Control** (`--old`): 6 S667 red · 0 older red · 10 green. **In a real browser** (Chromium, the rendered page, the server stood in): opened on 26-Oct "Aaj", the first 8-second poll moved it to 27-Oct, typing in the X-ray box after it did not step it back, the labels read 25-Oct, and its save sent day 27-Oct with `today_pick`; the live page under the same test stayed on 26-Oct and saved to 26-Oct (the bug, reproduced). Installer rehearsed on a made-up root: DRY, install (both rows moved, a deliberate late entry untouched), ALREADY INSTALLED, forced red restores byte-identically.

Independent cold review: SAFE TO INSTALL, 0 blockers; its six corrections built in (the data step gated; no step back; the date in the message; the label format; old open desks refused with F5; other misfiled rows listed).

## Install (on the server, after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s667kit && cp -rp /root/deploy/repo/deploy_kits/S667_DESK_TODAY /tmp/s667kit && bash /tmp/s667kit/install_S667_DESK_TODAY.sh
```
## Undo
```
\cp -p /root/finance/parchi_desk.py.bak_S667 /root/finance/parchi_desk.py && systemctl restart clinic-finance
```
