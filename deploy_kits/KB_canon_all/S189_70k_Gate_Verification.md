# S189 — the §4a ₹70,000 gate: VERIFIED OPEN (D326(c))

**Session 189 · 18 Aug 2026 · read-only on every book · no data changed anywhere.**
*Written to project knowledge at verification time; to be FILED to the repo and pinned at the S189
close (the F-107 discipline — a doc in use gets a manifest row).*

## The claim under test

Written as a SQL comment at S184, repeated at S186 §7, never checked by anyone:

> *Darpan's advances total ₹70,000 (₹40,000 S184 + ₹30,000 on 17 Aug), "tracked in salary system,
> NOT posted to Ledger."*

D326(c) blocked all salary-bridge work (Daily Flow v2 stage D3) until this was verified, because if
the same money sat in BOTH books as recoverable, his salary would recover it twice.

## What was checked, and what each check found

**1. The Staff Ledger itself** (`/root/staff_ledger/ledger.jsonl`, 16 rows, read raw). Darpan's
seven rows are exclusively the July close: the two migrated loan tranches (₹1,83,000
interest-bearing + ₹1,80,000 interest-free), the 2026-04 skip, two brought-forward school-expense
perks (₹13,000 + ₹6,000), July's ₹1,000 interest and ₹4,000 principal (balance after 1,79,000 —
D250's waterfall working exactly to spec). **No salary-advance rows. "NOT posted to Ledger" is
TRUE — there is no double-count.**

**2. The finance drawer** (read-only). The ₹40,000 is three rows — 2026-04-09 ₹15,000 ·
2026-05-30 ₹15,000 · 2026-06-18 ₹10,000 — each `Salary advance - Darpan`, each `ledger_posted=0`,
each `staff_id=None`, each carrying the untested claim in its own note.

**3. The live salary workbook** (`/root/clinic_salary/Salary_System_2026.xlsx`, read-only scan).
`Loan Master B27: Short-term advance outstanding = 0`. The Perks & ST-Advance Ledger contains **no
advance entry, ever** — only its two header rows. Consistent with the migration.

**4. The migration record** (Archive §S155, verbatim history). The 7 Aug migration carried
as-of-June balances, verified against the workbook LIVE POSITION **to the rupee**
(183,000 / 180,000 / 1 skip 2026-04 / 19,000 perks) — **no ST advances in the block**. The loan
tranches therefore do NOT contain the ₹40,000; they are the D250 structured loan.

**5. July — the ledger's first close.** Deducted exactly **−₹5,000** (₹1,000 interest + ₹4,000
principal). No advance recovery. And the pre-S152 backup workbook
(`D:\clinic_salary\Salary_System_2026_BACKUP_preS152.xlsx`, staged and scanned) shows Darpan's July
ADVANCE column **empty**, payable ₹10,928.28.

**6. The owner's confirmation — the one fact no surviving file holds.** The Apr–Jun months were
computed in the retired 23-tab workbook, whose monthly tabs are not on the VPS, the PC's
`clinic_salary` folder, or Drive. But recovering ₹40,000 against a ₹20,000/month base means Darpan
took home almost nothing for about two months — not a detail either side forgets. **Asked directly,
the owner confirmed: yes, his salary was cut.** The advances were recovered in the workbook era,
before the ledger existed.

## Verdict

**The ₹40,000 is recovered and closed. Nothing is owed on it, in either direction, in any book.**
The claim "tracked in salary system, NOT posted to Ledger" was TRUE — the salary system that
tracked it was the pre-August workbook, and it finished the job before the ledger's first close.

**The 17 Aug ₹30,000 is in NEITHER book yet** (finance has zero drawer expenses for 17 Aug; the
ledger has no August rows). It is already owner one-click item #6 with the three scans. When
entered: the **₹20,000** advance against August salary belongs in the Staff Ledger through the
app's maker-checker path so the August close recovers it; the **₹10,000**'s category is the still-
owed S186 §7 decision (free text if it settled July salary · `salary_advance` if new — the wrong
choice double-counts).

## Consequence

**D326(c) is satisfied. The salary bridge (Daily Flow v2 stage D3) is UNBLOCKED.**

*Method note: five machine checks plus one human answer, and the human answer was only trusted
after the machines had eliminated every alternative — the same shape as S186's count-beats-
derivation, applied to a question about the past.*
