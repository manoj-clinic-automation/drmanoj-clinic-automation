# S433_YES_BRANCH_READ — the month-end packs read the Yes Bank branch statements

**Session 286 (parent) · 28-Sep-2026 · F-652 · kit claimed on the System Board (v121 → v122).**

## Why
The branch sends every Yes Bank account's month as an unlocked PDF in its own layout (*STATEMENT OF ACCOUNT … Period : 01-AUG-2026 To 31-AUG-2026 … A/C Number …*). The statement shelf (S408/S411/S412/S417) could give these files no month, and the Yes Bank reader (S360, built for the e-statement layout) refused them — so all six Yes Bank rows of the August accountant pack read *missing* and Amir's pack never appeared, although the files had reached the shelf. The words-placement also read the proprietor line on Sanjeevni's statement (*PROP MANOJ KUMAR AGARWAL HUF*) as the HUF account.

## What changes
- **NEW `/root/finance/yes_branch.py`** — the branch layout: identify (bank, account tail, period, holder = the left column of the *OD Limit* line, kind from *A/C type*) and read with the four-way proof S360 uses (running balance from the printed opening, the printed closing, the printed debit and credit totals, every row inside the period). Narration digit runs of 11+ keep their last four. On the **shared** Sanjeevni tables a month already held is **checked** (date + amount) and not written again.
- **`/root/finance/packs.py` 938aa68f → c3eb9db0** (full file from the live bytes, 14 anchored edits): the branch layout is identified first; the reader is chosen by layout; *M/S* dropped and single letters joined (*N K PATHOLOGY* = NK PATHOLOGY); three settings honoured.
- **Settings (the owner's rulings of 28-Sep, data):** `packs.off_shelf_tails=0460` (Yes Bank current …0460 *Bareilly Orthopaedic Centre*, to be closed — never placed, never asked about) · `packs.retired_slots=yes_cur_clinic` (that account was the list's third Yes Bank current; the row leaves the pack) · `packs.hide_locked=1` (the locked e-statement copies are counted on the passwords card, not asked about one by one — the branch copies are the source).
- **`finance_yesbank.py` (Sanjeevni's) is not touched.** No other file.

## Proof
Offline on a copy of the 28-Sep finance.db with four real August branch statements (NK, Sanjeevni, Dr Manoj, Dr Bhawna): **25/25** — each proves itself; Sanjeevni checked against the statement held (the shared tables unchanged); per-account lines NK 2 · Dr Manoj 10 · Dr Bhawna 7, no account number in any line; …0460 off; Amir's pack ready; a second pass changes nothing; a fresh branch file lands by tail with no tap; by words alone Sanjeevni's statement goes to Sanjeevni and *M/S. N K PATHOLOGY* to NK. The installer repeats the walk on a copy of the live database with the live inbox before placing anything (`walk_s433.py`).

## Install (one line on the server)
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S433_YES_BRANCH_READ/install_S433_YES_BRANCH_READ.sh`

Refuses and changes nothing if packs.py has moved from 938aa68f. Backs up packs.py and finance.db. RED after placing puts the old packs.py back.
