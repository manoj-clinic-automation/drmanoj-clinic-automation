# SANJEEVNI BUILD CHARTER — for Claude Code (read before any Sanjeevni brief)

*Written 10-Oct-2026 by the Sanjeevni chat (session 303), at the owner's word of 20:22 IST: every build must follow the Sanjeevni architecture (the spine as the one source of Marg's truth, sections and subsections, no duplicates, no wrong text or data on any screen). The full owner-facing paper is `S303_BUILD_CHARTER.md` in the project and in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S303\`. This file is the builder's part. It sits beside `CLAUDE.md` and does not relax any rule there.*

## The ten rules

1. **Three kinds of data.**
   - **What Marg says** (sales, purchases, returns, closings, items, MRP, salts, categories) is read from the **spine** (`/root/finance/spine/`, `spine_read.Spine`).
   - **What people do** (counts, answers, approvals, cash, arrivals) is written once, to the table for that kind.
   - **What the system concludes** (expected stock, gap, loss, a flag, a verdict) is computed from those two and is never stored as truth.
2. **One fact, one place.** Never add a second copy of a fact or a second way of working out a figure. Call the function that already does it.
3. **Two stock figures, never mixed in one judgment.**
   - The **Marg figure** is Marg's closing carried forward by the spine's movements.
   - The **shelf figure** is the last physical count carried forward the same way.
   - A judgment uses one base from start to finish. If the code you are editing mixes them, do not spread the mix: name it in the report.
4. **A stored conclusion follows its inputs.** If it is kept for speed, it carries a stamp of what it was built from and is recomputed when that changes.
5. **People's entries are never overwritten or deleted.** A correction is a new row that replaces the old one; the old row is kept and marked. A closed count is sealed.
6. **One door per action.** Do not open a second way for staff to do the same thing.
7. **One screen, one person, one job.** A staff screen shows only that person's open work. Finished work leaves the screen by its state. Never add a new feature onto a screen built for a finished job.
8. **Words.**
   - Staff screens are Roman Hindi; owner screens are English.
   - Quantities always go through `qty_words.py`.
   - No system words on a staff screen: point, trace, round, gap, base, row, id, sync.
   - A sentence on a screen is built from the same figure the screen shows.
9. **Retire what you replace.** The kit's README names what it retired and what it leaves for a later build, so the chat can enter it in the Book's retirement register.
10. **Repairs through the system's doors.**
    - A data repair is a keyed, idempotent step inside the kit, walked on a scratch copy first, with a negative control.
    - Never DELETE. Never a hand edit of the live database.

## What this means while you build

- **Before each edit, ask whether it adds a second source of a figure, a second door, a stored judgment with no stamp, or system words on a staff page.** If it does and the brief did not order it, build the rest, leave that part out, and write it at the top of the report under **"Charter: left out"**.
- **If the live code already breaks a rule in a place the brief does not touch, do not fix it.** Write one line under **"Charter: seen, not touched"**. The chat turns these into the next builds.
- **The report has a short "Charter" section:** what the kit retired, what it left for later, anything left out or seen.
- **Another chat may be building at the same time** (tonight: the clinic chat's S503_PACKS_STATEMENTS, on `stmt_shelf.py`, `packs.py`, `packs.html` and `yes_branch.py`, none of them ours). The server build lock in `CLAUDE.md` decides who installs first: wait for it, never break it. `PUBLISH_ALL.bat` publishes everything pending, which is expected.
