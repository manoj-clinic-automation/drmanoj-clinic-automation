# S257 BUILD BRIEF — the dead shell removed from the path, the papers given a shelf, and the cheque register

**14-Sep-2026 · one chat · four kits `S268` … `S271`, two of them live on the VPS · D521 · F-479 … F-484.**
*Read this instead of the papers. One brief is a handover; ten papers are a record.*

## What the evening was about

Three things, and the first two were debts rather than features. **A rebuild that had been owed at
two closes because it needed a shell that has been dead since 8-Sep. A pile of paperwork on the
owner's PC that he could not track — and that was the assistant's fault, not his. And ⭐1 item 4,
the cheque register.**

## The four things a future session must not re-learn

**1 · A tool that needs a broken thing is a debt; a tool that does not is a repair.**
`MANIFEST.md5` over ~2,700 files was recorded OWED at S255 and S256 because it needs a POSIX walk.
`S268_MANIFEST_TOOL` does the walk in the Windows python already on manojz, lives **outside the tree
it measures**, and runs **nightly at 03:10**. The rebuild is owed at no future close and depends on
no shell. It found **F-480** on its first run — the manifest listed `00_INDEX.md` twice at two
different hashes, so `md5sum -c` would call the same file both OK and FAILED.

**2 · A walk is code, and its claims go stale exactly as a document's do.**
Three times in one evening a **check**, not the code, was what was wrong. A selftest that shelled out
to `md5sum` on a machine that has none. Four checks that went **green on a 500 body**, because they
asserted the *absence* of a string and an error page lacks it too. A check inherited from the
previous kit asserting the *previous* change. **Each was corrected in the walk rather than relaxed**,
and the `&&` chain stopped every time without touching anything live.

**3 · A delivery is proven by reading the bytes back (F-481).**
`device_commit_files` reported a file **written** when the copy on disk had not changed. The owner
ran the old version. It was caught only by staging the file back and hashing it. **The tool's own
success report is not evidence** — and every commit in this session was verified that way afterwards.

**4 · The most useful state of a register is the one where money is owed and nothing is written.**
S270's month strip was built from the cheques already logged, so with none logged the register
offered nothing, and September's ₹400 was unreachable. **The one state the page could not show was
the only state that mattered.** `S271` builds the strip from the purchase book instead.

## The kits

| kit | what it did | proof |
|---|---|---|
| `S268_MANIFEST_TOOL` | the Cowork manifest rebuilt in Windows python; nightly at 03:10; drop guard; F-369 diff discipline | 27 offline checks, format proved against frozen GNU `md5sum` bytes |
| `S269` (paper shelf) | `PAPERS.html` — needs-you, this session, last three, archive ledger; reads only | built from the measured inventory; nightly beside the manifest |
| `S270_CHEQUE_REGISTER` | D513's second half: number, date, payee against the month; duplicate refused; void never deletes | 50 offline · **walk 21/21** · pin `800d58a3…` |
| `S271_CHEQUE_MONTHS` | the register's months come from the purchase book, not from itself | 16 offline · **walk 25/25** · pin `3535dc978d4ec53846368c8772347a50` |

## The measurement that produced a policy

**375 working papers across 44 sessions. 193 — 51 % — appear in no index, no manifest and no
register.** Ten of S256's eleven were already in that state the next morning. Only **51 of 375** are
a build brief or a close report. `PAPER_POLICY_v1.1`: one brief written to be read, evidence never
announced, a file named in chat only when he must act on it, one shelf, three fates at each close.
**The 51 % is the scoreboard. Report it at every close; if it does not fall, the policy did not take.**

## Shapes to reuse

- **Prove a format against frozen bytes, not a live tool.** Check 5 of the manifest selftest compares
  against the exact output GNU `md5sum` produced for a fixed fixture — so it proves the format on a
  machine that has no `md5sum` at all, and says so when the live cross-check is skipped.
- **A patched copy must sit in the app's own folder.** `purchase_app.py` resolves its schema from
  beside itself.
- **A refusal is judged by what it says, not by its status code.** `_refuse()` returns 403 here.
- **Never extend the page-wide stylesheet from a feature block.** Four screens grew by exactly 1,287
  bytes the one time it happened; the patcher now refuses it.
- **Walk both files, against copies.** Patch a copy, walk it, replace the live file only if the walk
  passes. It stopped twice tonight and nothing was touched either time.

## Open into S258

The first cheque — September owes **₹400** to AGARWAL SURGICALS · the two vendors' bank details ·
KEDAR's ₹310 · August to check and lock · **whether Shavez should be able to write the cheque
register** (he is a viewer; it is an access change and the owner's call) · Club C.4 tokens · the
medical half of C.3 · the VPS-side OFF switches · **the PWA reorganisation, which needs him talking
rather than pasting.**
