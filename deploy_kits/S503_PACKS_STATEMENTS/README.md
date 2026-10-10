# S503_PACKS_STATEMENTS — the statements and packs page (Club A)

Session 304 (parent), 10-Oct-2026. The owner, 09/10-Oct: the Yes Bank statements of NK Pathology, the HUF and the
others are in the mail with the right passwords, yet not read; *"seven locked statements which I do not know which"*;
*"a field to set their password in our own page so that we are not dependent upon any external source"*; for ICICI,
*"it shd read both types, branch and system and store and display both together, and use any one for accountant and
amir packs"*; the quarterly statement *"is not required when we are having monthly statement"*.

## What changes on https://followup.dr-manoj.in/finance/packs

| part | before | after |
|---|---|---|
| Yes Bank e-statements | the consolidated monthly PDF (all accounts of one customer in one file) was refused: *"does not print 'Period'"* | read, account by account; the column order is read from each page's own heading, and a page that disagrees refuses the file |
| refused files | stayed refused until someone acted | offered again by themselves whenever a reader program is newer than the refusal — the one-time correction is part of the design, not a step |
| Statement passwords | Yes Bank only | one box per Yes Bank account, per ICICI account and per card, then the three bank-wide boxes; the shelf opens the files itself |
| locked files | a count (*"7 locked"*) | each named in words — *ICICI e-statement, September 2026*, *Yes Bank quarterly statement* — its account number masked, with **Set aside — not needed**; a set-aside list with **put back** |
| ICICI | one copy per month | the bank's own e-statement and the branch / net-banking copy both kept and shown (*also on the shelf: …*); where their dates overlap a line is written only if no line of that account already has its date, amounts and running balance, so nothing is counted twice; the closing is checked against a statement held to the same day |
| card statements | waited for the CC Saver script's decrypted copy | an original with no decrypted twin is opened by the shelf with the card's own password and stands as the month's statement |
| All_Transactions.xlsx | fetched once, never again | fetched again whenever Drive's copy changes |

## The one-time data step (only after a green placing)
1. File 124 — the Yes Bank quarterly statement — is set aside in the owner's name, if it is still the closed quarterly.
2. The 05:40 cron line's own command runs once (`stmt_shelf.py run`), so the five refused statements are read now.
3. The installer prints September account by account, and how many files are still locked, set aside and refused.

## Proven before handing over (in the session, on a copy of the 10-Oct database)
- The five refused Yes Bank statements (NK Sep, clinic Aug and Sep, Sanjeevni Aug and Sep) opened with the stored
  passwords and read: NK 2 lines; clinic none (a quiet account); Sanjeevni Sep agrees with the statement held;
  Sanjeevni Aug is the duplicate of its branch copy. The old programs on the same copy: all five refused (negative control).
- A second run reads nothing again and re-offers nothing (idempotent).
- The page, in a real browser on the state the new code returns: no script error; the six closed ICICI files named;
  *Set aside* and *put back* each post once and the lists move.
- ICICI overlap: of 15 lines in a second copy, 13 already held were not written again and 2 new days were.
- All_Transactions: fetched again when its time or size changes, not otherwise.

**Not yet provable:** an ICICI e-statement or a card original opened by the shelf — no ICICI or card password is stored
yet. The first one he types is read the same morning; the assistant reads the result at the next session's open.

## Install (the owner's one line on the VPS, after PUBLISH_ALL)
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S503_PACKS_STATEMENTS/install_S503_PACKS_STATEMENTS.sh

## Undo (one line; puts the four files back and restarts the finance app; finance.db keeps what was read)
    cd /root/finance && for f in yes_monthly.py:a4270bb3 packs.py:9f897eeb packs.html:73ff8c2f stmt_shelf.py:52a5fb07; do \cp -p "${f%%:*}.bak_S503_${f##*:}" "${f%%:*}"; done && systemctl restart clinic-finance

To go back on the data too: `finance.db.bak_S503_<time>` beside finance.db is the database as it was just before the
data step (stop clinic-finance first, then copy it back).

## Files
`yes_monthly.py` `packs.py` `packs.html` `stmt_shelf.py` — the four programs, as placed.
`make_*.py` — each builds its program from the live file by exact, counted edits on the md5-pinned bytes; the installer
rebuilds all four on the box and requires the kit's bytes.
`walk_s503.py` — the walk on a scratch copy; `--control` is the negative control.
`install_S503_PACKS_STATEMENTS.sh` — gates, rebuild, walk, backups, place, health, the data step. `DRY=1` places nothing.
