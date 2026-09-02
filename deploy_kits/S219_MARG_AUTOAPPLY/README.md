# S219_MARG_AUTOAPPLY — M1, the owner's first Marg job

**What it does, in one line:** an export that arrives when its day is already
filed now applies itself, every apply says what it did, and a real break in the
bill numbering raises a flag.

## Why it is this small
Most of M1 was already built. `_replay_pending_marg_for_day()` has applied a
pending export the moment its day is filed since **S194** (F-155), called from
`api_save_day`. Only the mirror-image order was missing: an export arriving
**after** the day was filed sat in `pending` until someone pressed Apply on the
workbench. This kit closes that, and adds the two things the owner asked to see
on every apply.

**The apply rule is not written twice.** The push calls the same replay the day
save calls; the summary is one helper used by both apply paths (D349 — two
copies of a rule is how two screens come to disagree about the same day).

## The four anchored changes to `/root/finance/finance_app.py`
| | change |
|---|---|
| **A** | the S219 helpers, inserted before `_replay_pending_marg_for_day`: bill-key parse, per-day series, apply summary, continuity check |
| **B** | the auto-replay reports its summary and any gaps |
| **C** | the checker's `api_marg_push_apply` reports the same summary, from the same helper |
| **D** | `api_marg_push` auto-applies any day that is ALREADY filed, via that same replay |

No page changes — **the owner's hub is FINAL** (S218_CARDS_FINAL_CONTRACT rev 2).
No new module, no schema change, no new table. The only write that did not exist
before is a `MARG_BILL_RANGE_GAP` row in `data_flag`.

## The threshold is measured, not guessed
Walked over all **135 days** of real history (2026-04-01 … 2026-09-01):

* 47 gaps existed; **22 of one bill, 18 of two, and the largest in five months was six.**
* 37 of them fall between consecutive calendar days — the ordinary texture of a
  counter that cancels a bill now and then. Nothing anybody can act on.
* So the floor is a setting, `marg.bill_gap_min`, default **10** — clear of the
  observed noise. Re-walked at that floor: **0 flags over 135 days**, while a
  fifteen-bill gap still shouts (proven in the selftest).

The range is printed in the summary on every apply regardless, so nothing is
hidden; only a real discontinuity raises a flag.

The walk also killed a defect: a looser parser read the S186 backfill's
`S186-F104-1332` refs as a bill series 3,889 numbers deep. A Marg series is now
one to three letters, and that phantom is gone.

## Proof carried in this kit
* `selftest_marg_autoapply.py` — **38/38 green**. It slices the helper block out
  of the PATCHED file and exec's it, so it tests the shipped bytes, not a copy.
* `walk_marg_autoapply.py` — the live-shape walk, run on the owner's PC against
  the real `finance.db`: summary net agreed on 10/10 days, continuity raised 0.
  It works on a COPY in a temp dir outside the mount (F-268) and writes nothing.
* `EVIDENCE_walk_02Sep.txt` — that run's output.

## Install
`INSTALL_ONE_PASTE.txt` — one line on the VPS after the publish.

## Rollback
The patcher writes `/root/finance/finance_app.py.bak_S219_m1_<stamp>` and prints
it. Copy it back and restart `clinic-finance.service`.
