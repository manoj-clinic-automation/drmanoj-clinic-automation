# BUILD NORM v1 — how every build and every correction is made (adopted S304, 10-Oct-2026)

The owner, 10-Oct-2026: *"THE PROMPT SHD BE A ONE THAT BECOMES A NORM FOR FUTURE WORKS, INCLUDING THE ONE TIME CORRECTIONS."*
This is that norm. It binds every kit, in this project and in the Sanjeevni project. It adds to the START-HERE prompt and the
engineering principles; it replaces nothing in them.

## 1. A correction is part of the build, never a separate step
- **The code heals the data it governs, by itself, on every run.** When a build changes a rule, it also brings the data already
  stored under the old rule into line — idempotently, on the normal schedule — so nobody has to run a one-off. Examples from S304:
  a reader that learns a new layout re-offers every file it refused before (S503 `_retry_refused`); new columns are filled from
  the files already kept (S507 `backfill_spans`); a patient's words are scrubbed from history on every nightly read (S510 `scrub_phi`).
- A one-off script is allowed only when the change cannot be expressed as an idempotent rule; it then ships **inside the kit's
  installer** as its data step, guarded so a second run changes nothing, and its result is printed.
- A correction **marks, never deletes** (`[NOT A PAYMENT]`, `set aside`, `superseded`, `_to_delete`), unless the owner says
  otherwise for that item. Patient details are the exception: they are removed, not marked.

## 2. Find the real cause before building
- Read the live code and the live data first (the nightly bundle, a DB copy in the session home, the pickup logs). A failure
  report from the owner is a symptom: say what actually happened, with the evidence, before proposing a fix.
- If something the owner asks for is already built, say so and build only the gap (S507: the export lines existed; the gap was
  that a file counted as done by arriving, not by being complete).
- If the owner's view and the data disagree, show the data in one or two lines, do not argue, and set a check that settles it
  (S304: the Monday call-list check).

## 3. Every kit is proven before it reaches the owner
- Built by **exact, counted edits on md5-pinned live bytes**; the installer rebuilds the files on the box and refuses if they differ.
- **A walk on a scratch copy of the live database**, on the box, before placing — with **made-up rows only** (dated far in the future,
  no patient), never real data written. **The same walk on the live files must go RED** (the negative control); a walk that cannot
  tell old from new is not a test.
- The installer: gates → pins (and the readers it depends on) → rebuild → walk + control → backups (`.bak_<kit>_<old md5>`, and the
  database before any data step) → place → restart only the service it touches → health → data step → a plain-English report
  of what the owner's pages now show → undo line in the README. Rehearsed on a made-up root before publishing, including the
  red-after-placing restore and a second run that says ALREADY INSTALLED.
- Repository gates before naming the publish: SUMS, `.gitignore` (a kit shipping a `.json` needs its own `!` line — S507), the
  number gate. A refused publish is a gate working: fix and re-name the same publish.

## 4. What reaches the owner
- One line per action only he can do (publish, one server line per kit, a sign-in, a password, a decision), with full paths in
  copy blocks. Never diagnostics or technical choices.
- What changed **in words he sees on his pages and his staff's**, and what is still not proven (S504: card originals not yet
  opened because no card password is stored).
- Owner-facing in English; staff-facing in their Roman Hindi; full patient numbers on screens, none in the repository.

## 5. Staff never get stale or misleading lines
- A line is "done" only when the work is complete, not when a file arrived; where a confirmation helps, it is shown in green with
  the facts (S508). Old work from before a floor is never shown to staff.

## 6. Recorded
- Each kit's evidence note in `ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S###\`; anything still to verify is put on a dated
  check (a scheduled task back into the session) rather than left to memory.
