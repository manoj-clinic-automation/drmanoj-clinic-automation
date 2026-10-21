# S611_LEDGER_STATEMENT — the statement, month by month, for every staff member (S331, 21-Oct-2026)

**The owner, 21-Oct 19:57–20:16 IST:** *"when all months is selected… properly display all the months which are there
in the system so that I can view and show a non-confusing statement when the advances were taken, what amount were
taken, what were the settled advances, what was the salary cleared, what are the current advances."* The word:
**advance remaining**. For all staff. *"proceed with the build."*

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S611_LEDGER_STATEMENT/install_S611_LEDGER_STATEMENT.sh

**What the statement shows now** (`/root/staff_ledger.py` 2fc0542f → new, by 14 exact edits in `edits_s611.py`)
1. The top box (S609's), in the owner's word: **Advance remaining now · To be cut from <Month> salary (line by line) ·
   Advance remaining after <Month>**.
2. One block per month, oldest first: advances taken (date · amount · in full / Rs N a month) · cut from salary, line
   by line (which advance; cleared, or what is left on it) · other items · **salary** from the LOCKED salary sheet
   (`/root/staff_register/staff_register.db`, read only): *Base − advances − leave, late & fines = paid* · **advance
   remaining at month end**. The running month uses the close's own dry run ("to be cut", "will clear it").
3. **Every advance** on one line: taken · amount · recovered · remaining, with "settled Sep 2026" or "to be cut in
   Oct 2026", and one line on the one-monthly-amount rule (oldest first).
4. The old ledger lines and advance cards are kept, closed, under **Technical entries**. Footer in plain words.
   Version → 4.0-S611-STATEMENT.

A locked month is used only if its NET column adds up to the run's total payout; otherwise the block says so.

**Proven by:** the file's own selftest (342 checks); `walk_s611.py` — Surendra's shape made up (Aug cut 7,000 /
remaining 6,000 · Sep cut 8,500 / remaining 4,000, salary short by 980 · Oct to be cut 7,980 / 2,000 after), and on
scratch copies of the live ledger and staff register: every locked month adds up, every staff page answers, each
month's remaining = last month's + taken − recovered, and the running month equals the top box. The old file goes RED.
Phone width checked (390 px, no sideways scroll).

**Undo:** `--undo` puts the S609 file back (`/root/s611_backup/`). Nothing in the ledger or the salary register is
changed by this kit.
