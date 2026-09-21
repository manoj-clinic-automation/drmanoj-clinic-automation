# S363_CASH_POOL — kit README

**Project:** Sanjeevni (session 280, 21-Sep-2026) · **Supersedes** S362_CASH_SCREENS (built, never installed; frozen) · **Touches parent files:** yes, declared — `finance_app.py`, `finance_ui/finance_approvals.html`; restarts `clinic-finance`.

## The owner's ruling (21-Sep-2026)
> "Darpan handed all cash daily from 1st to 19th Sept, and Dr Bhawna's receivings and yours go to the same pool, so maintain that flow; I will mark each day of Sept in approvals and tell you if any mismatch is observed."

## What it does
- **One calculation** (`sanjeevni_cash.py` v1.1) behind every Sanjeevni cash screen — the approvals page, the day panel, the month grid, the workbench, Darpan's card and his *where is the cash*, the portal tile, the health card, the cash log and the month table.
- **The doctors hold one pool.** August stays exactly as proven (drawer 7 · Dr Bhawna 2,98,155 · Dr Manoj 79,703 = pool 3,77,858).
- **Approving a day is the record** that its cash went from Darpan's drawer to the pool. Nothing to log day by day. Until a day is approved its cash shows in the drawer, labelled as awaiting approval.
- **The pool's deposits** — 03-Sep ₹3,00,000 (Bareilly) and 15-Sep ₹1,00,000 (Moradabad), from the owner's Yes Bank statement — are their own record (`cash_pool_deposit`), never a drawer movement; the Yes Bank check treats them as booked deposits and, with the statement loaded, matches both.
- Every edit falls back to the old arithmetic when the one calculation cannot speak.

## Proof
- `selftest_s361.py` (19, unchanged, on v1.1) + `selftest_s363.py` (11: approval moves exactly the day's cash, a deposit never touches the drawer, cash is conserved, a recorded handover is never doubled, a deposit already booked as a drawer movement is refused). Two mutant modules each fail it.
- `walk_s363.py` — the real app, live files vs patched, over one scratch copy of the live database: 26 checks, incl. approving a day and loading the owner's real statement (both deposits MATCHED). With the live files as "after" it fails 24 of 26.

## The line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S363_CASH_POOL/install_S363_CASH_POOL.sh
```
