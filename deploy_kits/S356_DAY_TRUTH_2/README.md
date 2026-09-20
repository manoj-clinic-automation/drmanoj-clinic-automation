# S356_DAY_TRUTH_2 — an unapproved pharmacy day follows the bank and carries its home / procedure bills

**Project: Sanjeevni — Pharmacy & Marg · session S275 · 20-Sep-2026.** The owner, 21:5x IST: *"APPROVAL section in Sanjeevni is showing wrong figures on multiple days — it's not subtracting the UPI and procedure meds etc. from the cash, so can't approve most Sept entries."* And: *the home and procedure medicine used to populate in Darpan's form from his own spellings; a glitch since the form was changed.*

**Supersedes `S355_DAY_TRUTH`** (copied into `deploy_kits\` at 22:02 with pass 1 only; frozen by F-512, never published — the last publish is 21:13 IST — never installed). Same file with pass 2 added.

## What was found (data: the 20-Sep 01:35 nightly `finance.db` and the PC's Marg archive)

**1 · UPI.** The D354 autofile (S210) builds a pharmacy day the moment Marg's sale report arrives: net sale from the report, **UPI from the bank as known at that moment**, cash = net − UPI — and never looks again. The bank's statement lands hours later (09:56–20:56 the next day, by the exception stamps), so the day is frozen with UPI 0. **Nine of the sixteen September days** (01, 02, 05, 09, 12, 14, 16, 17, 18) carry UPI 0 while `upi_statement` holds the bank's total for every one (₹69,444 in all); each has an open `upi_vs_statement` exception nobody could close.

**2 · Home / procedure medicine.** Darpan bills these to a label, not a person: the Marg customer text is **`HOME MEDICINE`** (earlier `HOME MEDISUN`) and **`PROSIJER <patient's name>`** — his spellings, measured across every bill-wise export since April in the PC archive. Such a bill has no clinic ID and no phone, so the ingest cannot attach a patient and **parks it in `sale_item_review`** (reason *low confidence*) — every one of them, since April. Until 18-Aug Darpan's typed day form carried them into `day_noncash_bill` (the last typed row is 21-Aug); from the autofile on (D354) nothing writes that table, the *kal* page only reads it, and the ingest's `home_med` tag has zero rows ever because the bill never reaches `sale_item`. September's eleven label bills (₹15,960 home, ₹1,337 procedure) therefore all count as cash.

## What it does

`/root/finance/day_resync.py` (NEW), **every 30 minutes 07–23** (one root cron line `# S356_DAY_TRUTH_2`, **declared to the parent**) and once at install:

- **Pass 1 — UPI.** For every pharmacy `day_entry` that is unapproved, written by the autofile (audit `autofile`) and never corrected by a person (no audit `correct`), with a bank statement: UPI line = the statement's settled total, cash line = net − UPI, one `audit_log` row (`resync_upi`, before/after), then `finance_upi.reconcile_upi` closes the exception. Bank total over the net sale → OVER_NET, left alone and named. Idempotent.
- **Pass 2 — home / procedure.** For every unapproved pharmacy day: each bill in the review queue (open or resolved) or tagged `home_med` whose customer text contains a word of `setting noncash.home_words` (seeded `HOME MEDI`) or `noncash.proc_words` (seeded `PROSIJ, PROSEJ, PROCIJ, PROCED, PROSED, PRUSIJ`) becomes one `day_noncash_bill` row — `home_medicine` / `procedure_medicine`, the bill's own number, date and amount, `entered_by day_resync` — **once** (the table's own unique key; a bill Darpan already typed is left as his). A credit note on a label (the table cannot hold a negative bill) is **said, not held** — the day's net already carries it, so the drawer reads low by that amount; one such in September (11-Sep, ₹2,300). One audit row per day added. **A new spelling is a data edit in the setting table, never code.**

Honours `/root/finance/_off/ALL_OFF`. Never touches an approved or locked day, a person's typed or corrected day (pass 1), a typed noncash row, expenses, movements, Marg, `sale_item`, the review queue, or any parent file.

## Touches

`finance.db` — `day_line` rows of the autofiled days, new `day_noncash_bill` rows, `audit_log` rows, two `setting` rows (backup first by the sqlite backup API: `finance.db.bak_S356_<stamp>`); the `recon_exception` rows re-judged by the app's own function. One root cron line. No restart, no screen, no schema change, `finance_app.py` untouched.

## What the walk found (PC, a copy of the 20-Sep nightly database)

Pass 1: **9 FIXED · 7 SAME**, every exception closed. Pass 2: **7 days ADDED, 11 bills** — 04-Sep home ₹5,338 · 07-Sep home ₹78 · 09-Sep home ₹355 + ₹2,300 · 10-Sep procedure ₹805 + home ₹1,578 · 11-Sep home ₹1,106 (+ the ₹2,300 credit note said) · 14-Sep home ₹268 + procedure ₹293 · 15-Sep procedure ₹239 — exactly the bills the PC's exports carry under those labels. Cash position 489,676 → **407,872**. Second run: nothing changes.

## Proof

- `selftest_s356.py` **28/28** (a scratch database in the live shape, nine tables): pass 1 FIXED / FIXED-with-line-inserted / SAME / NO_BANK / OVER_NET and the three days never touched; pass 2 home + procedure rows from the spellings, a person's bill not, a credit note said not held, a resolved review still counted, an approved day untouched, Darpan's typed bill not duplicated, the ingest's own tag honoured, the word lists seeded; the dry run writes nothing; the second apply changes nothing; ALL_OFF honoured; with the box's own `finance_upi.py` the exception is proven resolved.
- The installer: gates → compile on copies → selftest with the live `finance_upi` → **dry run against the live database, both passes printed, nothing written** → database backup → place + cron → the first real run (printed) → healthz 200; red → file removed, crontab restored, backup named.

## The one line (the owner's)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S356_DAY_TRUTH_2/install_S356_DAY_TRUTH_2.sh
```

## Owed / noted

- The kal page (`darpan_kal.py`) will now show these bills as *typed* rows; its own `procedure_customer_name` hook reads `sale_item.description`, which the daily push leaves empty since S243 — the hook is dead, the setting stays empty. Named, not changed.
- Parent (`finance_upi.py`): the resolution written on a closed exception is the literal `bank statement agrees (settled %d p, %d txns)` — the format was never applied. Cosmetic; an F to mint at the close.
- The root cause of pass 1 lives in the autofile inside `finance_app.py` (parent's): the bank-statement handler could call this resync on arrival. Named, not done.
