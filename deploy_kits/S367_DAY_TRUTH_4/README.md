# S367_DAY_TRUTH_4 — kit README

**Project:** Sanjeevni (session 281, 22-Sep-2026) · **Touches a parent file:** no · restarts `clinic-finance` (declared) · changes one row of `finance.db` after a backup.

## Why
04-Sep was filed **automatically** at 09:03 on 05-Sep from Marg's 08:53 export: 17 bills, ₹23,675. Nobody typed it. Marg's next export (09:03, 06-Sep) carried an 18th bill for 04-Sep — **A003396, ₹200 cash**. The bills were refreshed; the filed day never was (F-613). The owner's ruling **D602** (22-Sep): Marg's bills are the day; the ₹200 belongs to 04-Sep; not a shortage; correct it visibly and build the check.

## What it does
- `/root/finance/day_resync.py` `a4e53adc` → v4: **pass 0 (Marg)** — an unapproved, autofiled, never-corrected day follows Marg's latest export (cash = Marg's net − the bank's UPI), one `resync_marg` audit row each time. An approved day that differs is never touched; it is named in the log and on the day panel's *Needs you*. Same cron line as today.
- `/root/finance/sanjeevni_day.py` `7f6ea583` → v1.1: the checks say **how the day was filed** (which Marg export, what time, "nobody typed it"; or the old form and who), every resync and correction since, and whether a later export changed the bills. A day with a pool deposit says **"confirmed in the Yes Bank statement"**, or that no statement covers it, or that the statement does not show it (then it needs him).
- `correct_0904.py` — once: 04-Sep's cash line 11,066 → 11,266 (sale 23,875), one `correct` audit row under D602, only if every figure is as read on 22-Sep. The one calculation then sends the ₹200 to the doctors' pool with the day's cash; the drawer is unchanged.

Across 17-Aug…21-Sep, 04-Sep is the only day whose filed sale differs from Marg's bills.

## Proof
`walk_s367.py` — real app, scratch copy of the live database: correction applies once and only once · the ₹200 lands in the pool and nowhere else · all 30 days answer, every drawer = the one calculation's · every day says how it was filed · 04-Sep reads 23,875, drawer 5,928, nothing needs you · 03-Sep ₹3,00,000 and 15-Sep ₹1,00,000 read confirmed in the Yes Bank statement · 15-Sep still 11,291 · staff refused · day_resync v4 finds nothing to change. 15/15 green at build. S365's walk also green on the new panel (before the correction).

## The line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S367_DAY_TRUTH_4/install_S367_DAY_TRUTH_4.sh
```
