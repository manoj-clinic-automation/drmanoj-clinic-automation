# S609_LEDGER_MONTH_PLAN — the statement says what this month's salary cut is, and the total (S331, 21-Oct-2026)

**The owner, 21-Oct 18:45 IST:** Surendra took a Rs 5,000 advance this month; *"looking at his statement, it's not
visible what instalment amount is due for deduction this month, and what total advance he has."*

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S609_LEDGER_MONTH_PLAN/install_S609_LEDGER_MONTH_PLAN.sh

**What was wrong** — the statement listed each open advance with its own "monthly deduction Rs 2000" and never the
month's total or what is left; the Loans page's "falling due in 2026-10" for Surendra said **Rs 8,000**, adding each
old advance's own instalment. The close takes ONE instalment across the old advances: **Rs 7,000** (Rs 5,000 this
month's advance + Rs 1,000 clearing the 15-Aug advance + Rs 1,000 on the 17-Aug one), leaving **Rs 2,000** of his
**Rs 9,000**.

**What it does** (`/root/staff_ledger.py` 32dfcfb9 → new, by 9 exact edits in `edits_s609.py`)
1. `close_month(..., dry=True)` — the close's own code, every lane, returning the rows it would write and writing
   nothing. `month_plan()` uses it for the next close (a closed month shows what was actually taken).
2. The statement (owner's and the staff member's own) opens with: **Total advance outstanding now · To be cut from
   <Month> salary (line by line) · Left after <Month>**; each open-advance card adds "<Month>: Rs N".
3. The Loans page's "falling due" is the same figure. Version → 3.9-S609-MONTH-PLAN.

**Proven by:** the file's own selftest (342 checks) on the new file; `walk_s609.py` — Surendra's shape made up (Rs
7,000 / 9,000 / 2,000; the REAL close then writes exactly the planned rows) and, on scratch copies of the live
ledger, dry run = real close and OLD close = NEW close row for row (and the same month CSV). The old file goes RED.

**Undo:** `--undo` puts the old file back (`/root/s609_backup/`). Nothing in the ledger data is changed by this kit.
