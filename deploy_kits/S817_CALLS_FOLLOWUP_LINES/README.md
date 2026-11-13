# S817_CALLS_FOLLOWUP_LINES — the Call Console's follow-up lines · the parent · session 447 · 13-Nov-2026

**For the owner, in two lines.** On your Call Console each follow-up section now reads, folded: **"Called today N of M"** in large type, then "Reached K", then smaller "Earlier days, after the due date: x called · y reached". In Grace and older a call counts only from the day after the due date; only patients who have not come back are listed; each patient shows when they were last reached, with Play.

**F-1322.** The page kept a call when `call day >= due day`, so a call made on the appointment day counted as "called" for a patient who then did not come.

## Your rulings (13-Nov) and how each is built
| ruling | built |
|---|---|
| a. the folded line of Grace and older: today's calls large, then reached, earlier days smaller | every section's line, in the mock-up's words, sizes and colours (24 px bold; 14 px; 13 px `#4A5562`) |
| b. in Grace and older a call counts only when made on a day AFTER the due date; Today counts today's calls | `fu_row_state(strict=…)` — strict for a row 1 or more days late |
| c. only patients who have NOT visited, by D893 | `fu_return_day()` — see the rule below |
| d. each patient in Grace and older: when last reached, with Play (D899) | the last answered call of the last 60 days, the page's own player (`playJk`) and "whole transcript" (`wholeTx`) |
| e. readable | no line under 13 px; no pale grey; buttons 44 px high |

## D893 — exactly as implemented, and its fallback
A follow-up row is closed ("came") by the EARLIEST of:
1. **a visit on or after the due date** — by the row's clinic ID or by the mobile's fingerprint, among the visit days the page has always read (60 days back) — unchanged from before, except that a clinic ID written `12.0` in one store and `12` in the other is now one ID;
2. **a visit from half the advised period before the due date** (7-day advice: from 3 days before; 30-day: from 15 days before; never less than 1 day), **after the visit at which the follow-up was advised** (that visit itself never counts), **of the same clinic ID** (never on the mobile alone).

The advised period = due date − the day of the visit at which that date was advised, read **read-only from `finance.db`, table `dx_visit`** (your Clinical data report: each visit and the follow-up date given at it), matched on clinic ID + follow-up date; the latest such visit when two gave the same date.

**Fallback — THE ROW STAYS.** When the advised period cannot be read for a row (no clinic ID for that mobile; no `dx_visit` row with that clinic ID and that date — e.g. the Clinical data report for that visit has not arrived; `dx_visit` or `finance.db` unreadable), only rule 1 applies, as before. When the visits cannot be read at all, nothing is closed and the page says so (the existing line); when the advised periods cannot be read at all the page says "a patient who came a little before the due date may still show as open".

"One visit closes all of that patient's open follow-ups": the page already keeps ONE row per patient (the latest due date), so a closing visit closes the patient's only row.

## What changed in `/root/portal/calls_console.py` (and nothing else)
- `fu_row_state()` — new arguments `strict`, `hist`. Strict: only calls on a day after the due date feed "called", "reached", the pill and the row's call line. A "not coming" filed on the due day still closes the row. WhatsApps are read as before. New per-row facts: called today / reached today / called on an earlier day / reached on an earlier day; the call line; last reached.
- `fu_advice()` (new) — the advised periods from `dx_visit`, read-only, never raises.
- `fu_return_day()` (new) — D893 in one place, pure. Rule 1 sees only the days from 60 days back (as live); rule 2 the visits back to the prescribing visit.
- `followup_list()` — uses the two; calls are read 60 days back (for "last reached"); each section's figures in `fl`; the section's colour now follows TODAY's calls (all called green · none rose · some amber). The old 8-part section rows are kept. Today's top line and the strip count EVERY patient due today, also one an earlier visit closed.
- The page: the section lines and the Grace-and-older rows (`furow2`), their look, two sentences of the mock-up, one sentence of the foot. The Today rows and "Came / closed" keep their old row.
- Not touched: the WhatsApp-awaiting code (`person_state`, `wa_answer`), the people, the strip, the staff cards, every route.

## Every reader of what changed
| reader | reads `followup_list()`? | its numbers |
|---|---|---|
| your Call Console, the follow-up sections | yes | change as ruled |
| your Call Console, the strip's "follow-ups called X of Y" and the "Today: … Who called" line | yes — today's rows only | **due, called, reached and who called: unchanged** (every patient due today stays in "due", also one who came early by D893; the walk and the on-box proof compare them with the live page). Only **"came"** on that line can rise — a patient due today who came a few days early now counts as came |
| the staff cards on your page; each person's own card on Aaj ka kaam ("Mere calls": `/portal/console/api/mycard`, `/api/card/<login>`, `/api/myrec`) | no (`build_people` → `staff_cards`) | **unchanged** — the walk compares them with the live page's, identical |
| the portal tile that opens `/portal/console#followups` | a link only | — |
| the Callback Tracker, the WhatsApp lists, the old console page | no | unchanged |

Nothing outside your own page changes.

## Decisions made in the build
- **Sections kept as they are live** (Today · Grace 1–3 · Overdue 4–14 · Lapsed 15+). The mock-up's names "Missed 4–10 / Long overdue 11–60" are the one ladder of the plan's later step (they move patients between sections and hide those past 60 days); not this kit.
- **"Reached"** = an answered call either way (a patient who rang back and was answered is reached), as the page has always counted it. **On the folded lines** (today's pair and the earlier-days pair) a patient who rang in and was answered counts as called AND reached for that day, so "Reached" can never exceed "Called". The patient's own row still says "Not called since the due date" when nobody rang them; the old section figures, today's top line and the strip count outgoing calls as before.
- **"Earlier days … x called · y reached"** = patients of the section called / reached on a day after the due date and before today (a patient called both earlier and today is in both figures).
- **A row due more than 60 days ago** is not closed by a visit older than the 60 days the page has always read — as live. (Rule 2, the visit before the due date, reads as far back as the prescribing visit.)
- **A long unbroken name** wraps inside its card; "N days late" stays on the card at 400 px.
- **"Reached K"** is not printed when nobody was called or reached today (as the mock-up's sections with 0).
- **The big line's colour**: everyone called today green · nobody red · some amber, in every section (the mock-up's green "14 of 22" is not reproduced — one rule everywhere).
- **Last reached** looks at the last 60 days whatever the due date; one made on or before the due date is shown and marked "on / before the due date" (it is information for the caller, not a counted call). None in 60 days: the row says so.
- **Each row keeps its Call button** (the mock-up row has none; the click-to-call is live and stays). The caller's first name follows the call line.
- **"Bought medicines …, has not consulted since"** (the mock-up's second example row) is the *on medicines* state of the later step (D919) — not built here.
- **A mobile shared by a family** is one row and counts any call to it — unchanged, out of scope.

## Files
| live file | FROM | TO |
|---|---|---|
| `/root/portal/calls_console.py` | 45b03731 (S762) | see `TO_MD5.txt` |

Kit: `calls_console.py` (the new file, whole) · `install_S817_CALLS_FOLLOWUP_LINES.sh` · `walk_s817.py` · `proof_s817.py` · `oldwalks_s817.sh` + `walk_s748.py`, `walk_s762.py` (unchanged from S762's kit) + `EXPECTED_REDS.txt` · `KIT_ID.txt` · `TO_MD5.txt` · `SUMS.md5`.

## Left for a later kit (known, not in this one)
- `--undo` takes no build lock and does not check the portal's health first.
- Rule 2 when the same follow-up date was advised again at a later visit (the latest advising visit is taken as the prescribing one).
- A `finance.db` that is locked at the moment of the read is not waited for (the row then keeps the old rule for that page load).
- The mock-up's ladder names (Missed 4–10 · Long overdue 11–60).

## Proven (S447, made-up data only; build 2 after the second reader's review)
- `walk_s817.py`: 48 of 48 on the new page; CONTROL on the live page red on the due-day call (38 red); 10 mutations of the new page each red (`>` to `>=`; the visit filter dropped; the prescribing visit allowed; the mobile alone allowed; the whole period instead of half; Today made strict; today's line taken from the 7-day list; rule 1 given every visit day; the folded line counting outgoing calls only; the clinic ID matched raw); 9 comparisons with the live page on stores that hold a patient due today who came early and a row due 73 days ago — the strip (with "follow-ups called 3 of 5"), the people, the staff cards, each person's own card, Call ke baad, today's line, the rows that left the list — as they must be.
- S748's walk (103) on the new page: red only where `EXPECTED_REDS.txt` names — S762's five, and F14, F15, P4 (the old section line and colours this kit replaces). S762's walk 36 of 36.
- The page in a headless browser at 400 and 1100 px, on the final bytes: no script error, nothing off-screen, the folded lines as the mock-up, a 56-letter unbroken name wraps and "1 day late" stays on its card, the player opens from a last-reached row.
- The installer rehearsed on a stand-in root: dry · install · already · undo byte-identical · a kit file altered · the live file not the pinned one · red after placing (health; journal) puts the old file back · undo refused under a later kit.

## Install (after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s817kit && cp -rp /root/deploy/repo/deploy_kits/S817_CALLS_FOLLOWUP_LINES /tmp/s817kit && bash /tmp/s817kit/install_S817_CALLS_FOLLOWUP_LINES.sh
```
## Undo
```
bash /tmp/s817kit/install_S817_CALLS_FOLLOWUP_LINES.sh --undo
```
The undo refuses when a later kit (S818) already sits on top of this file.
