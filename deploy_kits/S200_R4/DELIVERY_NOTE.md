# S200_R4 — D339b: the reason survives a submit · corrections listed · UNDO

## The fault (mine), found from the owner's saved page
Owner: *"i marked ticked days present with a reason, and on submission same is coming again
for submission."*

His saved copy of `/register/fixabsents?ym=2026-07` proved **20 corrections had already saved**
(Ranjeet 4 · Darpan 7 · Shavez 2 · Surendra 2 · Vikki 2 · Awdhesh 2 · Sandip 1), so the write
path was fine. The fault was the **Reason box**: `required`, sitting at the TOP of a long page,
and re-rendered EMPTY on every load because R3 never carried it back. Tick rows, press submit
with it empty → the browser refuses to send the form and jumps to the top → nothing saves and
the identical list is still on screen. Exactly what he described. Shivani and Alisha showing
zero corrections is that batch never leaving the browser.

**Lesson (worth keeping): a required field the user cannot see when they press the button is a
silent failure, not a validation.** Blocked in the browser means no request, no message, no
audit line — nothing to find afterwards. Either default it, keep it, or put it next to the
button.

## What changes
1. **The reason is pre-filled** (`machine missed the punch`) and **carried back after every
   save**, so the form can no longer be blocked by an empty box. A note under it says so.
2. **"Corrections already made"** — a new section listing every day currently counted present,
   per person, with the in-time it was marked at. Previously the desk showed only a count, so
   there was no way to see *which* days had been corrected.
3. **UNDO** — tick any of those days and press *Undo the ticked corrections*; the day goes back
   to whatever the machine says (absent). New `uncorrect_present()`:
   - approver-only, same gate as the correction;
   - removes ONLY a row this desk or the D338 day card wrote, proven by its `decide_note`;
   - a staff member's **own D334 request is never deletable here** — it carries a real approval
     trail and is rejected with a pointer to the normal decide door (shown greyed, no tick box);
   - every undo writes an `audit_log` row (`undo_past_day`) naming the actor and the in-time
     that was removed.

## Why the owner needs the undo right now
Cross-reading his saved page against the July grid: **Shavez 1 Jul and Surendra 13 & 14 are no
longer offered**, i.e. they have already been marked present — but he has ruled them genuine
absences. **Vikki 18 is still listed, so it is genuinely absent and needs nothing.** Without an
undo those three days would silently stay present and inflate the July sheet.

## File & pin
| file | was | now |
|---|---|---|
| `/root/staff_register/staff_register.py` | `582e17145c74e7b0cf30162658cc953c` (v0.9) | `7d62435a3a6caf5260bfc93eaf99257f` (v0.10) |

`salary_policy.py` is NOT touched by this kit.

## Proof done offline
- Patched from the hash-verified R3 bytes; every anchor asserted to occur EXACTLY once.
- `py_compile` clean; `pyflakes` clean apart from the pre-existing `deg_path` note.
- Two real defects caught by the suite during the build, both mine:
  * an R3 assertion (`"2026-08-04|6" not in page`) was too coarse once the undo list
    legitimately prints a corrected day's key — tightened to test the `pick` field itself;
  * my new audit assertion queried a table named `audit`; the real table is `audit_log`.
- **Selftest GREEN** including the new block: the reason box defaults · survives via `?r=` ·
  is echoed back in the apply redirect · maker 403 on undo · approver undo removes the row ·
  the audit line is written · a staff's own request is refused as "not a correction" ·
  nothing-ticked reports instead of silently passing.

## Install
    cd /root/deploy/repo && git pull
    bash /root/deploy/repo/deploy_kits/S200_R4/INSTALL_S200_R4.sh

Gate → backup → swap → compile → selftest on the box → restart → health probe, auto-rollback on
any failure.

## After it's green — the three fixes owed
1. Undo **Shavez 1 Jul**, **Surendra 13**, **Surendra 14** in "Corrections already made".
2. Correct **Shivani** (2 days) — her batch never saved.
3. Leave **Vikki 18** alone; it is already absent.
Then save the Sheet 1 print view as `D:\dr-manoj-git\July_Sheet1_verified.html`.

## Owner's counts vs the desk, at the time of his save
| staff | machine absent | corrected | now absent | workbook target |
|---|---|---|---|---|
| Ranjeet | 4 | 4 | 0 | 0 ✓ |
| Awdhesh | 3 | 2 | 1 | 1 ✓ |
| Shavez | 6 | 2 | 4 | 4 ✓ (but 1 Jul is one of the two — undo makes it 5) |
| Vikki | 5 | 2 | 3 | 3 ✓ |
| Sandip | 2 | 1 | 1 | 1 ✓ |
| Surendra | 6 | 2 | 4 | 5 — undo 13 & 14 gives 6, so ONE of them stays corrected |
| Shivani | 9 | 0 | 9 | 7 — 2 still owed |
| Alisha | 8 | 0 | 8 | 8 ✓ (no change ruled) |

**Surendra needs a decision at the desk:** his workbook target is 5 absents. Undoing both 13 and
14 puts him at 6. Undo the one that was genuinely absent and leave the other corrected — or tell
Claude which, and the target can be re-checked against the workbook.
