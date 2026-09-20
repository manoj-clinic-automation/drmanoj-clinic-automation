# S355_DAY_TRUTH — an autofiled pharmacy day follows the bank

**Project: Sanjeevni — Pharmacy & Marg · session S275 · 20-Sep-2026.** The owner, 21:5x IST: *"APPROVAL section in Sanjeevni is showing wrong figures on multiple days — it's not subtracting the UPI and procedure meds etc. from the cash, so can't approve most Sept entries."*

## What was found (data, from the 20-Sep 01:35 nightly `finance.db`)

The D354 autofile (S210) builds a pharmacy day the moment Marg's sale report arrives: net sale from the report, **UPI from the bank as known at that moment**, cash = net − UPI — and never looks again. The bank's statement lands hours later (09:56–20:56 the next day, by the exception stamps), so the day is frozen with UPI 0 and cash overstated. **Nine of the sixteen September days** (01, 02, 05, 09, 12, 14, 16, 17, 18) were filed with UPI 0 while `upi_statement` now holds the bank's total for every one of them (₹643 … ₹15,058; ₹69,444 in all). The statement then opened a `upi_vs_statement` exception on each ("bank settled X but the day was entered with UPI 0") that nobody could close, and the approval section showed the frozen cash. Cash in hand was overstated by the same ₹69,444.

The second half of the owner's line — **home / procedure medicine** — is a different gap: `day_noncash_bill` has no row after 21-Aug because the autofile writes none and Darpan's *kal* page reads that table but never writes it; the ingest's own tag (`sale_item.home_med`, S194) has **zero rows ever**, and the procedure word-list setting is empty. Nothing in the data says which September bills were home or procedure medicine — that needs the Marg party names (asked of the owner) and is **not** in this kit.

## What it does

`/root/finance/day_resync.py` (NEW), **every 30 minutes 07–23** (one root cron line `# S355_DAY_TRUTH`, **declared to the parent**) and once at install:

For every pharmacy `day_entry` that is **unapproved** (submitted / draft), **written by the autofile** (audit action `autofile`) and **never corrected by a person** (no audit action `correct`), with a bank statement for its date: set the UPI line to the statement's settled total, the cash line to net − UPI, write one `audit_log` row (`resync_upi`, before / after, by `day_resync`), and re-run `finance_upi.reconcile_upi` so the exception closes itself. A day whose bank total exceeds its net sale is left alone and named (OVER_NET — a person's question). A day already equal to the bank is untouched (SAME). Idempotent; honours `/root/finance/_off/ALL_OFF`.

Never touched: approved or locked days; days a person corrected or typed; expenses, movements, noncash bills, Marg, `sale_item`; any parent file.

## Touches

`finance.db` — the two `day_line` rows of each such day (backup taken first by the sqlite backup API: `finance.db.bak_S355_<stamp>`), one `audit_log` row per day, the `recon_exception` row re-judged by the app's own function. One root cron line. No restart, no screen, no schema change, `finance_app.py` untouched.

## What the walk found (PC, on a copy of the 20-Sep nightly database)

Dry run: **16 unapproved autofiled days since 01-Sep — 9 WOULD_FIX, 7 SAME.** Apply: 9 FIXED, every exception closed, cash position 489,676 → 420,232; a second run: SAME 16. E.g. 09-Sep: UPI 0 → ₹15,058 (7 txns), cash ₹29,935 → ₹14,877.

## Proof

- `selftest_s355.py` **20/20**: a scratch database in the live shape, eight days — FIXED (UPI 0 → the bank), FIXED with the UPI line missing (inserted), SAME, NO_BANK, OVER_NET, and three the script must never touch (approved, corrected by a person, typed by a person); the dry run writes nothing; the audit row carries before/after; with the box's own `finance_upi.py` the exception is proven resolved (and the over-net one proven still open); the second apply changes nothing; ALL_OFF honoured.
- The installer: gates → compile on copies → selftest with the live `finance_upi` → **dry run against the live database (printed, nothing written)** → database backup → place + cron → the first real run (printed) → healthz 200; red → file removed, crontab restored, backup named.

## The one line (the owner's)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S355_DAY_TRUTH/install_S355_DAY_TRUTH.sh
```

## Owed / noted

- Parent (`finance_upi.py`): the resolution text written on a closed exception is the literal `bank statement agrees (settled %d p, %d txns)` — the format was never applied (cosmetic; an F to mint at the close).
- The root cause lives in the autofile inside `finance_app.py` (parent's): the bank statement handler could call this resync on arrival instead of waiting for the half-hour. Named, not done.
