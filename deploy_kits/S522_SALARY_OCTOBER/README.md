# S522_SALARY_OCTOBER — the four salary items before October's salary

Kit of session 305 (the parent), 11-Oct-2026. Number claimed on the System Board (`_numbers` v344). D689 item 5.

## What it does — the owner's words first

- **A skipped loan month is ONE button** — *"Should show in his related ledger everywhere"* (06-Oct). On the ledger's
  Advances page each person with a long-term loan has a card at the top of his block: **Skip this month — all his
  loans**. One tap stops collection for that month on every long-term loan of that person, through the ledger's own
  DEFER (D332 — DEFER replaces SKIP as the owner's verb): each loan's schedule moves one month later, nothing is
  taken that month. **Free twice a financial year, counted in MONTHS** — one month skipped over two loans is one of the
  two (before this kit, pressing Defer on his two loans used both free defers). From the third month the loan with
  interest carries the waivable Rs 1,000, as D332 already said. A reason is required.
  It reads *skipped* on Sheet 2's month strip, on his private loan page (with the instalment paid back to him there,
  D682), on his salary slip (*Loan ki kist — is mahine skip*) and in his ledger statement (*MONTH SKIPPED — every
  long-term loan*). The old per-loan **Skip (Rs 1000 capitalises)** button (D250) is no longer shown; its route stays.
- **Sheet 4** prints a TOTAL row under the amounts and its right border inside the page; **Sheets 3 and 4** print
  rupees with Indian thousands separators (counts — leave days, late minutes, marks, dress days — stay as they were).
- **Sheet 3's footnote** on the dress / I-card fine says what the settings charge (*I-card not charged* when it is 0).
- **The slip's line for a negative month** says what is true: *Yeh Rs. … aapke naam baaki hai — agle mahine ki
  salary se yeh apne-aap nahi katega; iska hisaab alag se hoga.* Nothing carries a negative month forward (F-760).

## Files

| file | from | to |
|---|---|---|
| `/root/staff_ledger.py` | `eacd71544715ff597712aee5e6233135` | `32dfcfb9295c6ba9204a4d0d0c34daa9` |
| `/root/staff_register/salary_policy.py` | `ac603874431a43bed278f7db45d2c0f9` | `c36538963840a0258e0d25c6b950de4f` (VERSION 1.18-S522) |

`staff_register.py` (`0a098cfa…`) is read, not edited: its frozen-sheet reader already strips separators, and the walk
reads both engines' Sheet 3 through it. No data step: nothing is written to the ledger by the install.

Both files are built from their pinned FROM bytes by `make_s522.py` (11 + 13 counted edits; every anchor exactly once).

**What the one button skips, exactly:** every open advance of that person except one that comes back in full from its
own month's salary (that is the month's own money) and one booked against a later month; a scheduled advance only in a
month a step is actually due (a defer moves its whole schedule). A month already skipped the OLD way (Rs 1,000 added)
is left as recorded and the button says so. Each loan with interest carries its own Rs 1,000 from the third month,
waivable at the tap. One tap at a time (a lock); the card defaults to the first month the ledger has not closed. The
per-loan **Defer** control stays for deferring one loan alone.

## How it was proven (offline, before the publish)

- Both files' own selftests: the ledger 342 checks (19 new on the skipped month, its card, its route and a second tap),
  the engine's math selftest with the skipped month, the slip line and the two new helpers.
- `walk_s522.py` on a box-shaped tree (the 11-Oct bundle's code, the live-shape ledger fixture of S489, made-up
  attendance), with the register's reader loaded, inside the installer's rehearsal on a made-up root. The count is
  in the close report.
- **Negative controls, every one red:** 6 on the selftests (rows not months · the month's own advance offered · the
  skip mark dropped · the engine's mark dropped · no schedule-due test · no old-skip guard) and 10 on the walk (no skip
  mark · Sheet 4 total wrong · a Sheet 3 column dropped · a money figure moved · a Sheet 2 word changed · the slip's
  skip line gone · the ledger's skip flag dropped · one line only skipped · the penalty always charged · never charged).

## Independent review — two fresh readers

**First:** one blocking finding (a scheduled advance with nothing due that month was moved a month by the skip) and
eight smaller ones (an old-style skip losing its Rs 1,000; a name with an apostrophe breaking the confirm box; the
card's default month and waive box; the lock; the penalty wording; walk counts that could pass empty and a slip
comparison that could go falsely red; the dead old-skip block; the installer's ALREADY INSTALLED order). All nine
taken in, each with its own selftest or walk check.

**Second:** nothing blocking; eight small ones, seven taken in — the confirm box now names the Rs 1,000 when the
month would charge it; the walk insists the penalty path ran (or says why it could not) and tests the same month the
card offers; a second tap says *already skipped*; the partial-write wording is honest and an I/O error is reported the
same way; the slip's skipped line says *is mahine kuch nahi kata* (true for a defer and a hold alike); the installer's
header hash; the walk's temp folders. Not taken: the slip calls an ordinary per-loan Defer "skip" — that is the
owner's own word for it (D332), the private page already says the same.

## Install

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S522_SALARY_OCTOBER/install_S522_SALARY_OCTOBER.sh
```

`DRY=1` before `bash` runs every gate and the walk and writes nothing. Pasted twice, it says ALREADY INSTALLED.

## Undo

```
\cp -p /root/staff_ledger.py.bak_S522_eacd7154 /root/staff_ledger.py && \cp -p /root/staff_register/salary_policy.py.bak_S522_ac603874 /root/staff_register/salary_policy.py && systemctl restart staff-ledger staff-register
```

A month already skipped with the new button stays a recorded DEFER in the ledger (append-only); the old engine reads it
as an ordinary deferred month, which it is.
