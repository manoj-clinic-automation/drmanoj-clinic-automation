# SANJEEVNI BUILD CHARTER v1.1 — for Claude Code (read before any Sanjeevni brief)

*v1 written 10-Oct-2026 (session 303, D705) at the owner's word: every build follows the Sanjeevni architecture — the spine as the one source of Marg's truth, sections and subsections, no duplicates, no wrong text or data on any screen. v1.1 written 11-Oct-2026 (session 307, D707) at the owner's word "yes" to the review `S307_CHARTER_AND_NORM_REVIEW.md`: six rules widened, four added, from the faults the first builds under v1 let through. The owner-facing paper is `S307_BUILD_CHARTER_v1_1.md` in the project and in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S307\`. This file is the builder's part. It sits beside `CLAUDE.md` and `BUILD_NORM_v1.md` and does not relax any rule there.*

## The fourteen rules

1. **Three kinds of data.**
   - **What Marg says** (sales, purchases, returns, closings, items, MRP, salts, categories) is read from the **spine** (`/root/finance/spine/`, `stock_watch.Spine()` / `spine_read.Spine`).
   - **What people do** (counts, answers, approvals, cash, arrivals) is written once, to the table for that kind.
   - **What the system concludes** (expected stock, gap, loss, a flag, a verdict) is computed from those two and is never stored as truth.
   - **1b · The source's reach.** A judgment that reads the spine states the reach it needs (sales and purchases to the day it judges, `sp_export`'s `date_to` and stamps) and answers "not yet" when the spine is short — never "wrong". A kit that makes a page depend on the spine, a cron pass or a collector reads that job's state at install and refuses to place while it is red.
2. **One fact, one place.** Never add a second copy of a fact or a second way of working out a figure. Call the function that already does it. **The test:** the brief lists, by grep, every place that answers the question the build touches; the kit retires all but one. A kit that leaves two answers standing is not done, whatever its own screen says.
3. **Two stock figures, never mixed in one judgment.**
   - The **Marg figure** is Marg's closing carried forward by the spine's movements.
   - The **shelf figure** is the last physical count carried forward the same way.
   - A judgment uses one base from start to finish. If the code you are editing mixes them, do not spread the mix: name it in the report.
4. **A stored conclusion follows its inputs.** If it is kept for speed, it carries a stamp of what it was built from and is recomputed when that changes. **A verdict written as an event is a record, never a gate:** the gate recomputes from the inputs on every read. When the inputs move and the conclusion cannot be recomputed at once, the owner's line says it is stale.
5. **People's entries are never overwritten or deleted.** A correction is a new row that replaces the old one; the old row is kept and marked. A closed count is sealed.
6. **One door per action.** Do not open a second way for staff to do the same thing.
7. **One screen, one person, one job.** A staff screen shows only that person's open work. Finished work leaves the screen by its state. Never add a new feature onto a screen built for a finished job. **The install-day state:** a brief that changes what a staff member sees reads the live data as it will stand on the day of install, names that state, and writes the words for it; a state no screen has words for is a blocker, and the installer prints the state before and after placing.
8. **Words.**
   - Staff screens are Roman Hindi; owner screens are English.
   - Quantities always go through `qty_words.py`.
   - No system words on a staff screen: point, trace, round, gap, base, row, id, sync.
   - A sentence on a screen is built from the same figure the screen shows, and says the date of that figure.
   - **A line never hands staff a figure to type:** it names the thing to check (the voucher, the bill).
   - Words are built once, in the row the screen reads; a second copy of the same words in another file is a fault.
9. **Retire what you replace.** The kit's README names what it retired and what it leaves for a later build, so the chat can enter it in the Book's retirement register. **Dead code is a defect:** a function with no caller, a branch that can never run, a cache nothing invalidates, is removed by the build that finds it; the brief greps, the walk proves the grep empty.
10. **Repairs through the system's doors.**
    - A data repair is a keyed, idempotent step inside the kit, walked on a scratch copy first, with a negative control.
    - Never DELETE. Never a hand edit of the live database.
11. **Time.** One clock — the server's, in IST; stored as ISO (`now_iso()`); dd-mm-yyyy only on a screen; never compare the two shapes. A closing is placed by its **capture moment**, never by its printed day alone — the estate's one rule (`push_expected._gap_side`): captured before 09:00 = the end of the previous day; 22:00 or later = the end of its own day; between = unusable for a judgment. Days owed by a staff member are counted in that person's **visit days**, not calendar days.
12. **Identity.** An item is identified by the spine's key (`sp_item.k20`, with the spine's aliases and families), never by a bare string or a 20-letter clip; items sharing a key are judged on their net. A rename is read back from Marg's own export by that identity, tolerant of spacing and case, with one owner door to accept a sighting.
13. **The door and the line follow the screen.** What a screen hides from a person (a stage, a floor, a role), that screen's door refuses for that person. The owner's line for a staff duty counts the same set the staff screen shows — the duty map's SQL and the page read one rule.
14. **A staff page's weight.** A staff phone page is served the fields it reads and nothing else: under two seconds and under 100 KB a read. The owner's data stays on the owner's routes.

## What this means while you build

- **Before each edit, ask whether it adds a second source of a figure, a second door, a stored judgment with no stamp, a second copy of words, or system words on a staff page.** If it does and the brief did not order it, build the rest, leave that part out, and write it at the top of the report under **"Charter: left out"**.
- **If the live code already breaks a rule in a place the brief does not touch, do not fix it.** Write one line under **"Charter: seen, not touched"**. The chat turns these into the next builds.
- **Read the live state before the walk** (rule 7): the stage, the pending lines, the roles of the logins the kit affects — by key, never by counting — and assert on it; then add the walk's own made-up rows. Every control must be able to go red on the old file, and the report prints each one red.
- **Read the health of what the kit depends on at install** (rule 1b): the spine's `spine_state.json`, the cron pass, the collector; refuse to place while it is red and say so.
- **The report has a short "Charter" section:** what the kit retired, what it left for later, anything left out or seen, the dependency's state at install.
- **Another chat may be building at the same time** (the clinic chat's kits on its own files). The server build lock in `CLAUDE.md` decides who installs first: wait for it, never break it. `PUBLISH_ALL.bat` publishes everything pending, which is expected.
