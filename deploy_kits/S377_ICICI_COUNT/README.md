# S377_ICICI_COUNT — kit README · F-615

**Project:** Sanjeevni (session 281, 23-Sep-2026) · **Touches a parent file:** yes, declared — `finance_ui/finance_approvals.html` · restarts `clinic-finance` · `finance.db`: one new table `bank_anchor` and one row in it, after a backup.
*Diagnosed by the parent chat (S279) and handed here with a draft, `D:\dr-manoj-git\_handover\S377_ICICI_COUNT\`; that draft is superseded by this kit, which also fixes the count itself.*

## The fault
The owner recorded his real ICICI → Yes Bank transfer of **₹40,000 on 20-Sep** and the page refused it: *"more than the 31,551 it holds"*. What ICICI "held" was counted from **zero at the 17-Aug cash anchor** — only the POS settlements credited since then, less the transfers recorded. The money the account already held is outside that count, so the count is short by exactly that balance, and **a count that is short must never refuse money the bank really moved.**

## The proof, from his own August ICICI statement
Closing **₹1,50,263.42 on 31-Aug**; the settlements credited after it come to ₹1,45,416 by 20-Sep. So ICICI held **₹2,95,679** that day, he moved **₹2,90,000** (₹2,50,000 + ₹40,000), and **₹5,679** was left. The bank was right; our count was blind to the opening balance.

## What changes
1. **The count starts at the bank's own figure.** New table `bank_anchor` — one row per account: the closing balance the bank itself printed, its date, and the statement it came from. Position = that balance + settlements credited since − transfers recorded since. With no anchor row the old reckoning stands, so an unseeded box is unaffected. `seed_icici_anchor.py` writes the one row (1,50,263.42 as on 31-Aug, source named); idempotent, and it never overwrites a different figure already on record.
2. **A statement that stops on an entry's own date proves nothing.** A credit can land up to three days late, so *"NOT in the statement"* is said only when a loaded statement reaches three days past the entry; otherwise it waits. His two 20-Sep transfers were being called missing by a statement that ends 20-Sep.
3. **A short count records, it does not refuse.** A transfer larger than the count goes in, and the answer says by how much the count was short. ICICI never reads below zero on the page; it names the shortfall and says the ICICI statement will settle it. **Every other refusal stands** — a future date, a date before the anchor, zero, the same entry twice, a route that is not his.

`sanjeevni_approvals.py` `4f98cb37` → `f52ff847` (v1.2) · `finance_ui/finance_approvals.html` `19c877e5` → `87157a85` (both by `apply_s377.py`, anchored on the live bytes).

## Proof
`walk_s377.py` on a scratch copy of the live database — **17/17**: his 2,50,000 stands and **the 40,000 that was refused is recorded**, with the shortfall named · both rows in the book · no month's sale, online or cash moves · before the anchor the page shows ICICI at 0 and names the shortfall · the seed anchors on the bank's figure and a second run changes nothing · after it, holds = balance + credited − moved out (**₹6,337**), no shortfall, and the page names the statement it counts from · future / before-anchor / zero / repeat / wrong-route / future-deposit all still refused · staff refused.
In headless Chromium: the ICICI line reads *"holds about ₹6,337 — ₹1,50,263 on the bank's own statement of 31-Aug, ₹1,46,074 collected since, ₹2,90,000 moved out"*, both transfers read *waiting for the statement* rather than missing, **zero script errors**.

## The line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S377_ICICI_COUNT/install_S377_ICICI_COUNT.sh
```
