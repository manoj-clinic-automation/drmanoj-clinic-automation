# S572_TWO_MORE_LINES — README

Brief: `claude_code_briefs/S572_TWO_MORE_LINES.md` (Sanjeevni chat, session 316, owner's word 16-Oct 13:47 IST).
Report: `claude_code_briefs/REPORT_S572.md`.

## What
Data only, the S569 Part B way. Two more one-time `tap` jobs on Amir's card (*Ek baar ke kaam*, each with *Kar diya*), keyed
`fix:S572:FOLITRAX 15 MG TAB` and `fix:S572:OSTOVAXL DM`, audited `job_added` by `system` with
`{"kit": "S572", "owner_word": "16-Oct 13:47"}` (amir_day's own `_audit`). S569's two rows are not touched.

## Files
- `add_jobs_s572.py` — `walk` (scratch copies by the backup API; walk-only portal; the staff-eye walk W1–W12 and its control) and
  `live` (needs the build lock naming S572; re-reads the owner's proof on a copy; backup `finance.db.bak_S572_<stamp>`; the keyed
  insert in one transaction; read-back). Before adding, it asserts `/finance/stock/api/pad/hub/1` `proof.C.wrong` still names
  FOLITRAX 15 MG TAB (need −6, moved 0, packing 1*5) and OSTOVAXL DM (need +21, moved +25, packing 1*10); a line no longer wrong is
  not added. The quantity words come from `qty_words.words(..., lang="hi")`. A second run says ALREADY and adds nothing.

## Pins
- No `.py` on the box changed. Read only: `/root/finance/stock_app.py 050587df…`, `/root/finance/amir_day.py 73882a83…`.
- Touches: `/root/finance/finance.db` — `amir_job` +2 rows, `purchase_audit` +2 rows. Nothing else.

## Duty map
Not changed: the duty is `amir.marg_jobs` (door `/finance/amir/step/6`, marker *Ek baar ke kaam*) — it already exists.

## Undo
Never DELETE. A job left unwanted is closed through its own door (Amir's *Kar diya*), or, if the owner says so, by a new keyed step
that sets `done_at` / `done_how='withdrawn S572'` with an audit row. The database backup stays beside the database.
