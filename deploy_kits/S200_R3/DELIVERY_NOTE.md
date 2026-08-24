# S200_R3 — D339: the month FIX-ABSENTS desk · and Sundays visible again on Sheet 1

## Why
Owner, after using the D338 day card for real: *"the flow for attendance correction is still
cumbersome, i couldnt do all corrections, very confusing"* and *"sundays are not highlighted in
the attendance grid"*. Both fair. 14 corrections meant 14 separate day pages, and nothing showed
progress toward the target count.

## 1 — The Fix-absents desk (NEW, D339)
`/register/fixabsents?ym=YYYY-MM` — approver-only (same `SR_PRESENT_APPROVERS` gate as D338).
Also linked from the top of Sheet 1.

ONE page for a whole month:
- every correctable machine-absence, grouped per staff, oldest first;
- a live header per person — **absent 9 · corrected 2 · still absent 7** — so you can see the
  target arriving instead of guessing;
- in-time pre-filled with that person's shift start for that date (editable);
- ONE reason box that applies to everything you tick;
- a tick-all box per person (for a whole leave block);
- submit once — every ticked day is written.

**It grants nothing new.** Every row is written through the SAME `correct_present()` the day card
uses, so all D338 guards still apply per row. The page simply refuses to *offer* a row that the
write would reject:
- future dates (never);
- clinic holidays;
- rostered-OFF days (an off-Sunday is not an absence — read through `duty_shift_for`, D253);
- days the machine already has a punch for;
- days already carrying a request/correction (those count into "corrected" instead).

**Dead punch feed = no list.** If the feed is unreadable the page says so and lists nothing,
rather than showing a clean page that would read as "nobody was absent".

A refused row is reported back ("3 refused — …"), never silently swallowed.

## 2 — Sundays on Sheet 1 (regression fix)
`att_month_report.py` has marked Sundays (`class="sun"`) since v2.x; the new Sheet 1 grid never
carried it over. Restored: the Sunday day-number header shows a purple **SUN** marker, and every
cell in a Sunday column carries a purple left border (kept when the grid scrolls sideways on a
phone). Existing cell colours (absent red, late amber, request blue) are untouched — the sun
class is added alongside them, never instead. Legend updated. The print view keeps the marking;
the fix-absents door is `noprint` and never appears on a staff's own copy.

## Files & pins
| file | was | now |
|---|---|---|
| `/root/staff_register/staff_register.py` | `e13059023b7b57fba170cb29db933119` (v0.8) | `582e17145c74e7b0cf30162658cc953c` (v0.9) |
| `/root/staff_register/salary_policy.py` | `7f86cc8702b9fa48940e31a5ed2869d4` (v1.3) | `dfe67285944ec72fa2fb698651d160bd` |

No schema change, no migration, no data write at install.

## Proof done offline
- Both patched from the hash-verified live bytes; every anchor asserted to occur EXACTLY once.
- `py_compile` clean; `pyflakes` clean apart from the one pre-existing `deg_path` note.
- One real defect caught mid-build by pyflakes: a duplicate `_valid_ym` — the base already had a
  stricter one, so mine was dropped rather than shadowing it.
- **Register selftest GREEN** including the new D339 block: maker 403 · approver 200 · an
  already-corrected day is not re-offered · an uncorrected one is · future month yields nothing ·
  dead feed yields nothing (not a clean list) · bulk apply writes through `correct_present` with
  the right timestamp · a duplicate is reported refused · nothing-ticked says so.
- **salary_policy selftest PASS**, plus a rendering proof: July 2026's four Sundays (5, 12, 19,
  26) each get the marked header, exactly four cells carry the sun class, an absent Sunday keeps
  BOTH `gA` and `sun`, the door appears on the doors view and on neither the print view nor a
  staff's own view.

## Install
    cd /root/deploy/repo && git pull
    bash /root/deploy/repo/deploy_kits/S200_R3/INSTALL_S200_R3.sh

Gates both files, backs both up, swaps, compiles, runs BOTH selftests on the box, restarts,
probes `/register/health` — and rolls BOTH files back together on any failure.

## After it's green
Open **Sheet 1 for July** → the note at the top links straight to the desk. Finish the remaining
days there, then save the print view as `D:\dr-manoj-git\July_Sheet1_verified.html`.

## Pin note
Third and fourth live-file moves of S200 (after `staff_register` at R1 and `portal.py` at R2b).
`verify_live_pins.py` drift grows until the S200 close regenerates the list — F-134 shape, not a
fault.
