# S479_YES_MONTHLY_READER — session 294, 04-Oct-2026 (the parent) — F-725

**Why.** Yes Bank mails every account its month as a locked PDF in a layout neither Yes Bank reader knew (`YOUR ACCOUNT STATEMENT FROM .. TO ..`, one `Primary Holder` line, one foot line with the opening, the two totals and the closing). The shelf opened it with the owner's password; the identifier then took its bank from a narration and gave it no period, and the net-banking reader refused it. Three such statements sat opened and refused (Sanjeevni Medicos, September; the HUF, August and September): September's shelf read 11 of 15 and the pharmacy's bank cell was empty.

**What it does**

1. **`/root/finance/yes_monthly.py` — NEW, the reader of that layout.** Same interface and the same proofs as `finance_yesbank.py` (S360) and `yes_branch.py` (S433): the opening row equals the printed opening, the running balance is followed row by row, the last balance equals the printed closing, both printed totals are met, every row is inside the period (by its value date or its transaction date — the bank posts a month's interest on the first of the next month with the last day's value date). A description is wrapped around its row and is joined as it was cut; every line inside the table that is not a row, the heading or the page's own foot block is a piece of a description wherever it starts, and a row left without any description refuses the file. It refuses, whole: two accounts in one file, a title whose period is not the account's, a missing foot line, a dated line it cannot read as a row, a description line that pairs with no row, the words `CASH DEP` anywhere but at the head of a row's description (lines glued to the wrong row). Numbers of eleven digits or more keep their last four only; the account is stored as its last four.
2. **One line once — in all three Yes Bank readers.** The three layouts key a bank row differently, so the table's own key would let the same row in once per layout. `yes_monthly.py` does not write a row another file already holds (date + withdrawal + deposit + the cash flag, counted; looked for from the period's first day to the statement's last row). A period another file *covers* is checked: agreeing, nothing is written; differing, it is **said** and the rows not held are written. And two small edits make the older readers do the same toward the other layouts: `finance_yesbank.py` (the net-banking download) does not write a row the monthly statement or the branch's print already put on the table, and `yes_branch.py` does not write a row a file of another layout holds. Without this, a net-banking download uploaded after the month's statement was read would put every row on the shared Sanjeevni table twice, and the pharmacy's cash check would raise a *bank deposit not booked* for each doubled cash deposit. Between two files of the same layout nothing changes.
3. **`/root/finance/packs.py` — eight exact-anchor edits.** The identifier names the layout (Yes Bank by the layout itself, the holder from the `Primary Holder` line — never the proprietor line above it —, the period and the tail from the account's own section line). The reader is chosen by layout: the branch's print, else the monthly e-mailed statement, else the net-banking download. The shelf row says what was written (`11 lines: 7 new, 4 already held from another file`). And **a person is handed the copy he can open**: the accountants' attachment, the owner's preview and Amir's pack take the unlocked copy of a statement the shelf opened (`_best_path`). Until now all three took the locked original, which only the owner can open. A file that was never locked goes out exactly as before.

**Files** (the three edited files are all verified before any is written; every anchor exactly once)

| file | from | to |
|---|---|---|
| `/root/finance/packs.py` | `1bc18b26` | `9f897eeb` |
| `/root/finance/finance_yesbank.py` | `3509f728` | `01b70e2b` |
| `/root/finance/yes_branch.py` | `fec5c520` | `e06ff505` |
| `/root/finance/yes_monthly.py` | (new) | `a4270bb3` |

**The owner's line (the server; it carries its own pull)**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S479_YES_MONTHLY_READER/install_S479_YES_MONTHLY_READER.sh
```

It walks first (hermetic: made-up statements, an empty database; the two older readers are walked new beside old). **Then the real shelf, before anything is placed** (`shelf_dry_s479.py`; it writes nothing — the database is opened read-only and copied into memory): every row carrying the refusal is opened from the copy the shelf itself reads. One that is the monthly layout and that the reader cannot prove is a **red, and nothing is installed**; so is one that reads but differs from a statement already held. The ones it proves go through the shelf's own pass on the memory copy, and the kit prints where each lands, its period, how many rows and cash deposits it has, and how many lines are new on the table — file ids, the slots' own labels and counts only, never a file name, an amount or a long number. Only then: backups, place, restart `clinic-finance` (about 8 seconds), the after-placing checks (among them `finance_yesbank.py`'s own selftest as placed), and the same rows given back to the shelf for real (one shelf run, as the 05:40 cron runs it), with the month's cells counted afterwards. A red after placing — or the line cut after placing — puts the three files back and removes `yes_monthly.py`. Pasted again on an installed box it repeats the after-placing checks and reads any refused monthly statement still waiting. `DRY=1` in front of `bash` places nothing.

**Undo (one line)**

```
\cp -p /root/finance/packs.py.bak_S479_1bc18b26 /root/finance/packs.py && \cp -p /root/finance/finance_yesbank.py.bak_S479_3509f728 /root/finance/finance_yesbank.py && \cp -p /root/finance/yes_branch.py.bak_S479_fec5c520 /root/finance/yes_branch.py && rm -f /root/finance/yes_monthly.py && systemctl restart clinic-finance
```

Lines the reader has written stay on the tables (they are the bank's own, proven); the shelf rows it read stay read.

**Not touched:** the parsing and the proofs of `finance_yesbank.py` and `yes_branch.py`, `reconcile_cash_deposits`, `stmt_shelf.py`, the tables' shape, the cells' rules, the password card, every page. Nothing is sent anywhere.

**Known, and left** (recorded for the close): a statement the reader has not seen is refused rather than guessed — a month with no transaction at all (no opening row printed), a balance printed with `Dr` / `Cr`; neither has been seen on the three statements read. `yes_branch.py`'s own check of a *covered* month on the shared tables is as S433 left it (it says *differs* and writes nothing).
