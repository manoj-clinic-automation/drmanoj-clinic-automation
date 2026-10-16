# S569_PROOF_REACH_AND_TWO_LINES — README

Brief: `claude_code_briefs/S569_PROOF_REACH_AND_TWO_LINES.md` (Sanjeevni chat, session 316, owner's word 16-Oct 09:33 IST).
Report: `claude_code_briefs/REPORT_S569.md`.

## What
- **Part A (diagnosis, read only).** Why stage C's proof says `export / no_figure`. No file changed, no runbook command run: the cause is
  the reach rule in `stock_app._s524_tryable` (a code change) plus a purchase export that has not come yet (a real "not yet").
- **Part B (data only).** Two one-time `tap` jobs on Amir's card (*Ek baar ke kaam*), keyed `fix:S569:KT ROS DT` and
  `fix:S569:VINBACTUM DS`, audited `job_added` by `system` with `{"kit": "S569", "owner_word": "16-Oct 09:33"}` (amir_day's own `_audit`).

## Files
- `add_jobs_s569.py` — `walk` (scratch copies by the backup API; walk-only portal; the staff-eye walk W1–W11 and its control) and
  `live` (needs the build lock naming S569; backup `finance.db.bak_S569_<stamp>`; the voucher cards re-read on a copy and asserted; the
  keyed insert in one transaction; read-back). A second run says ALREADY / adds nothing.

## Pins
- No `.py` on the box changed. Read at the open: `/root/finance/stock_app.py f58e09db…`, `/root/finance/amir_day.py 73882a83…`.
- Touches: `/root/finance/finance.db` — `amir_job` +2 rows, `purchase_audit` +2 rows. Nothing else.

## Duty map
Not changed: the duty is `amir.marg_jobs` (door `/finance/amir/step/6`, marker *Ek baar ke kaam*) — it already exists.

## Undo
Never DELETE (charter 10). A job left unwanted is closed through its own door (Amir's *Kar diya*), or, if the owner says so, by a
new keyed step that sets `done_at` / `done_how='withdrawn S569'` with an audit row. The database backup stays beside the database.
