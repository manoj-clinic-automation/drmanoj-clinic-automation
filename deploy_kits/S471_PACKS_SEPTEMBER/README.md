# S471_PACKS_SEPTEMBER — the month-end packs, refined (session 293, 04-Oct-2026)

**The owner's words (04-Oct):** "the accountant pack section needs refinement", "for each Yes Bank account there should be a
separate password to add", and the September road — statements arriving but not on the shelf.

## What changes
| where | from → to | what |
|---|---|---|
| `/root/finance/packs.py` | 23fda41a → 6738d65d | **stitch**: an account's two consecutive cycle statements (ICICI: 11th→10th, 15th→14th) together ARE the calendar month's statement — the cell reads *read* with two pieces, the pack row is *ready* with both PDFs as *part 1 of 2 / part 2 of 2*; a lone cycle statement is **partial** on the row and the shelf alike (one word for one file) and the row says which statement completes the month and about when it is due; **one password key per Yes Bank account** (`YES:<slot>`, the shelf's own six slots) listed before the three bank-wide keys, each row showing how many files it opened; row numbers **3.1 … 3.12, 4.1 … 4.4, 8.1, 8.2**; the electricity row says the bills are paid around the 17th and show in the ICICI statements when none is on the shelf yet |
| `/root/finance/packs.html` | 4c46cd0e → 1349b37b | the page for all of the above; the Shavez summary says *done* and *open* both; the shelf's intro names both fetch times |
| `/root/finance/stmt_shelf.py` | 95ba0a4f → 52a5fb07 | the unlock step tries an account's own password before a bank-wide one (ORDER BY on the stored keys; nothing else) |
| root crontab | + one line | a second shelf fetch at **07:30 IST**, after the personal account's relay at 07:00 — same command as S408's 05:40 line, tagged `# S471_PACKS_SEPTEMBER` |

No schema change: the account keys live in `stmt_secret.bank` (TEXT PRIMARY KEY) as `YES:<slot key>`. Values are never shown, never logged (unchanged).
Not touched: the send, Amir's pack, the checklist page, the Sanjeevni files, the database.

## How it is proven — `walk_s471.py`, hermetic (F-709)
A scratch finance folder with the edited files beside the box's own readers, an EMPTY database from `packs.ensure()`, a scratch
inbox, made-up one-page PDFs. 41 checks: stitch (A), lone cycle = partial with due words (B), whole month unchanged (C), a gap
is not stitched (D), the passwords card's keys and refusals (E), the unlock by the ACCOUNT key with a locked PDF made by pypdf
under the venv python (F), numbering and the electricity words (G), the page's words (H), SHOWN on the OLD file that the same
two cycle statements read *partial* / *missing* there. Offline 04-Oct 08:4x IST: `WALK_S471 GREEN 41 checks, 0 fail, 0 note`.

## Install (the owner's one line; the lock F-694; DRY=1 places nothing)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S471_PACKS_SEPTEMBER/install_S471_PACKS_SEPTEMBER.sh
```
Red after placing → the three files and the crontab are put back. Backups `.bak_S471_<from8>` beside each file, `crontab.bak_S471_<stamp>`.
