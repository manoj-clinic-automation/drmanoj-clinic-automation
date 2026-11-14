# S819_LEDGER_INTEREST_WITH_PRINCIPAL — no interest without principal (S453, 14-Nov-2026, F-1367)

**The owner's ruling:** *no interest is taken, charged or capitalised on a loan in a month unless principal comes
off the same loan that month. All or nothing: a month that cannot carry the whole instalment holds it whole — no
interest, no penalty, the balance unchanged, the loan one month longer. A month that can carry it behaves exactly
as today; the last month closes the loan as today.*

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S819_LEDGER_INTEREST_WITH_PRINCIPAL/install_S819_LEDGER_INTEREST_WITH_PRINCIPAL.sh

**The fault (F-1367).** In `close_month()`'s waterfall, when the salary could not bear the whole instalment, a
CAPACITY_HOLD row was written — and then the interest was still paid first out of whatever was left: interest
alone, or interest and a part. A loan could pay Rs 1,000 interest in a month nothing came off it.

**What it does** (`/root/staff_ledger.py` 85e2ab51 → 0086a952, 5,720 → 5,768 lines, by 12 exact edits in `edits_s819.py`):
1. `close_month()` — the rule. When a person's waterfall carries a loan with interest and the salary cannot bear
   the WHOLE instalment the waterfall asks for, nothing is taken in the waterfall for that person that month: no
   LOAN_INTEREST, no ADVANCE_INSTALMENT, no LOAN_CAPITALISE. What `_take()` spent of the capacity is given back.
   ONE CAPACITY_HOLD row, against the loan, says it: *"Rs N — the WHOLE instalment HELD for <month>: the salary
   cannot carry it. No interest is taken and nothing is cut this month; the loan stands as it is and runs one
   month longer"*. `dry=True` (S609) returns the same row.
2. `hold_whole()` + `HOLD_WHOLE_MARK` — the ONE test every surface reads to know such a row (D349).
3. `plan_for_staff()` (the Statement's top box), `month_book()` (its month blocks), `advance_makeup()` (what the
   remaining is made of; New entry's box through `entry_position()`), `loans_view()` / `loans_html()` (the Loans
   page: *held this month*), `statement_months_html()` (*Every advance*: *held in <month> — nothing cut, no
   interest*), `close_report()` — a held month reads: nothing cut, no interest, the loan standing, one month longer.
4. Version → 4.3-S819-INTEREST.

**Untouched:** the owner's explicit skip and defer and their penalty (D250, D332); the order — schedule, the
month's own advance, then the waterfall; interest-free advances (a part is still taken, the rest held, as before);
a month that carries the instalment (the same rows, byte for byte); every stored row.

**Kept as it is, on purpose — NOTED, not changed:**
- A loan whose instalment equals the flat interest exactly (Rs 1,000): a carried month still takes Rs 1,000
  interest and no principal, as before. The same holds where one person has two loans with interest in the
  waterfall and the one instalment does not reach the second loan's principal. The rule above is applied to the
  month that CANNOT carry the instalment; these carried months are as they were. An owner's decision if wanted.
- New entry's label still reads "flat Rs 1,000/month at every close while open". After this kit a held month takes
  none. Wording only; left for the owner to see.
- The register's long-range plan (`project_recovery`) does not foresee a salary-capacity hold before the close —
  as its own text has always said. After the close it reads the ledger's rows and is right.

**Other readers of the ledger — read, none needs a change:**
- `/root/staff_register/salary_policy.py` — reads the ledger's ROWS (`load_ledger`, `open_advances`), never the
  close. A held month after the close: a hold mark and no interest row → the private loan page says *Held*, the
  whole instalment kept aside is paid back to him there, the balance stands, the months ahead move one later.
- `/root/staff_register/salary_engine.py` — `SALARY_EXCLUDED` guard, `load_ledger`, `ledger_closed`,
  `compute_salary`, `load_rulings`, `staff_bases`: unaffected (the excluded set is unchanged).
- `/root/finance/finance_app.py` — posts an advance through `make_entry`, reads `load_ledger` / `load_users` and
  the ceiling: unaffected.
- `/root/staff_ledger_reconcile/ledger_reconcile.py` — previews with the module's OWN `close_month` on a
  throw-away copy, so it follows the rule by itself. Its one line "(part held back …)" would be said of a whole
  hold too: wording of a hand-run tool, no change needed.
- `/root/ledger_statement.py` — stand-alone, reads the file itself, does not import the ledger: unaffected.
- `/root/state_backup/clinic_state_backup.py`, `/root/state_backup/code_bundle.py`, `/root/att_scenario.py` —
  paths and the settings file only: unaffected.
- `/root/wa/staff_ledger.py` — an old copy, not the running file: ignored.

**Proven by:** the file's own selftest (342 checks, as before); `walk_s819.py` — the S614 file against the new one
on made-up ledgers: 84 checks (a carried month; short of the instalment; nothing left; the last month; skip and
defer with and without the penalty; interest-free only; a schedule and the month's own advance ahead; two months
with the first held — the loan ends exactly one month later, interest once in every month principal came off;
dry run = close in all 32 closes; every forecasting surface for a held month, and that the close then does exactly
that), plus 6 more on the box on a scratch copy of the live ledger (counts only). **The control:** pointed at the
S614 file, 39 of the 84 go RED. The walks of S611, S612 and S614 pass on the new file exactly as on the S614 file
(23, 26, 54); S609's walk reads 9 ok / 4 not on BOTH files alike (its four are Statement wordings S611 replaced).

**The installer** (S614's, step for step): refuses unless the live file is 85e2ab51 (ALREADY INSTALLED if it is
0086a952); rebuilds the kit's file from the live bytes; selftest; walk; control; backup to `/root/s819_backup/`;
`\cp`; compile; restarts `staff-ledger` and waits for v4.3-S819-INTEREST on the login page; puts the old file back
and restarts if the file does not land, does not compile, or the ledger does not come back.

**The shape check (added after the second reader's review).** On the box the walk counts, on a scratch copy of the
live ledger, people whose loan has a shape in which a CARRIED month would still take the flat interest with no
principal off that loan (two loans with interest in one waterfall, or an instalment not above the flat interest).
Counts only. If there is even one, the walk is RED and the installer stops before the backup — nothing is changed,
and the owner decides first.

**Undo:** `--undo` puts the S614 file back (`/root/s819_backup/`) — only when the live file is this kit's file and
this kit's backup is there; `DRY=1 ... --undo` only says what it would do.
