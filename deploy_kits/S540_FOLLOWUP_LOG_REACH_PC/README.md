# S540_FOLLOWUP_LOG_REACH_PC — Monday's follow-up list, and every list after a short export

Kit of session 311 (the parent), 12-Oct-2026. Numbers claimed on the System Board (`_numbers` v381): kit S540.

**The owner, 08:40 IST:** *"the default follow-up are generated for one month. Since long, check this and then see why the
Monday follow-up list did not come in the callback tracker."*

**Measured first (counts only, no names):** Saturday 10-Oct had two follow-up exports — 08:48 (Docterz's default month,
118 rows, 11 due Monday 12-Oct) and 20:40 by reception (one day, 1 row, due Sunday). manojz's pickup paired Saturday
night's run with the NEWEST log, so Monday's list (Sunday is skipped) was built from the one-day file; nothing arrived on
Sunday, so nothing re-made it. The owner was right that the default is a month; the 20:40 export was a one-day range.

## What it does — manojz `docterz_pickup.py` only (S239 rev 2 → S540)
1. **A run pairs with the newest follow-up log that REACHES its call day** (the next working day; Sunday is emergency-only,
   processor.py's own rule). A newer log that stops short never displaces one that reaches; only logs within 4 days of the
   newest are weighed; when none reaches, the newest (as before).
2. **The heal:** when the latest day's list was made with a log that stops short of its call day, and a log that reaches is
   on the shelf, the pass re-makes that list ONCE, while the call day has not passed, and sends it to the VPS (the 5-minute
   arrival push then writes the Callback Tracker). Each day remembers its log (`fu_md5`, `fu_reach`) so it never repeats.
3. A lone new log refreshes the latest day's list while its call day has not passed (was: within one calendar day — a
   Saturday list could never be refreshed on Monday).
4. `--refresh-latest` uses the same choice.

| file | from | to |
|---|---|---|
| manojz `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\docterz_pickup.py` | `d117786f435906976aafd63446d7c88e` | `cd829f5fd074e8451f027e08da2ef68d` |

## Proven
- `make_s540.py` rebuilds it from the live bytes on manojz byte for byte (7 counted anchors). The file's own `--selftest`: 0 failures.
- `walk_s540.py`: 9 checks on made-up files replaying 10 → 12 Oct (the heal once, with the month log; a second pass idle; past
  the call day nothing; the newest wins when it reaches). Negative controls: the old file fails 6; a copy without the heal fails 2.
- Read-only on manojz's real state before placing: it picks the 08:48 month log (11 due 12-Oct) for 10-Oct.
- **Live:** placed 08:46:21 IST; the 08:50 pass logged *HEAL … re-made with FOLLOWUP_LOG__2026-10-10_to_2026-11-09…*,
  wrote `Staff_Action_Today_2026-10-12.xlsx` (12 of 118 rows) and sent it to the VPS at 08:50:40.

## Undo (on manojz, by the file tools)
Copy `docterz_pickup.py.bak_S540_d117786f` (beside it) back over `docterz_pickup.py`. No task or setting was changed.
