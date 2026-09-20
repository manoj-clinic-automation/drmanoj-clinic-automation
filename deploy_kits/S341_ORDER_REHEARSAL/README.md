# S341_ORDER_REHEARSAL — ordering prepared offline against the spine, nightly, not switched

**Project: Sanjeevni — Pharmacy & Marg · session S274 · 20-Sep-2026.** D567 **item 5**: *"Ordering prepared offline against the live spine, rehearsed every night — not switched."*

## What it does

`/root/finance/spine/order_rehearsal.py` (NEW) runs at **23:58** every night (one root cron line, `# S341_ORDER_REHEARSAL`, **declared to the parent**), after the spine's compare. It reads **`spine.db` only** (read-only URI) and writes, beside the spine, `orders/order_rehearsal_<date>.json` and `orders/order_rehearsal_latest.txt` — **the order the S225 engine would make tomorrow**, computed from the corrected store instead of the unverified tables the live engine reads (`sale_line_item`, the latest snapshot; S270_WHAT_IS_LEFT §1 item 1).

**The rules are the engine's defaults, copied, not the owner's rulings** — `plan_line`, `cadence_for`, `confidence` and every rail reproduced from `purchase_app.py` (S207_PO/S225): lead 2 d · safety 3 d · +3 d single-source · cover ≤ 45 d · vendor cadence weekly/fortnightly/monthly by monthly value · box rounding · dead after 60 d · thin under 5 selling days · spike ≥ 40 % · lines under Rs 50 wait. The file says so in its second line: *NOT AN ORDER. Nobody acts on this file. The rules are the S225 engine's defaults, which the owner has not approved.*

**Inputs, all from the spine:** on hand = `sp_move` to date (Marg's figure at the last closing shown beside it) · rate = `sp_sale_line` units over the last 28 days · selling days, peak share, days since the last sale · last supplier, number of suppliers, cost per unit and the box (GCD of bought quantities) from `sp_purchase_line` · vendor cadence from `sp_purchase_bill` over 90 days.

**The four lists that do not exist yet** (S270 §1 item 3): `order_rules.json` beside the script — `never_reorder` · `on_demand` · `internal_use` · `orthotics_cycle` — written by the first run, empty except `internal_use` seeded with the three items the 09-Sep ruling (S235) calls internal consumption: BLADE, ZIG ZAG COTTON 500GM, GLOVES SURGICAL 7. An item on a list never goes on the order; it appears under *held back* with its reason so the effect is visible. **Filling these is the owner's sitting.**

**The score** — the two-week trial, by the machine: each night scores the proposal of **seven nights ago** against the spine's purchase lines since: *proposed and bought · proposed and not bought · bought though not proposed*.

## What it touches

Nothing existing. No screen, no tile, no table, no `finance.db`, no restart. OFF: the spine's own switches (`/root/finance/spine/OFF`, `/root/finance/_off/ALL_OFF`).

## The first real rehearsal (PC, 20-Sep 09:11 IST, against a spine built from the real archive as of 19-Sep)

**47 lines · Rs 88,541 · 33 flagged CONFIRM · 0 held back** (rules v1). The confirm flags are the rails talking: 36 lines rounded up to a box, 22 of them to a box two or more times the need (a syringe line rounded from 19 to a box of 200), 18 thin, 10 spikes. That is precisely what the owner should see before ruling on the rules.

## Proof

- `selftest_s341.py` **15/15** on a scratch spine built with the spine's own SCHEMA: a 20/day item with 50 on hand, two suppliers, monthly cadence → cover 35 d → 650 units → 65 strips → box of 10 → 70 strips, Rs 5,600, vendor and confidence right; a dead item is not reordered; a Rs 0 line is dropped while stock remains; a single-source thin item is CONFIRM; BLADE never appears; `NOT AN ORDER` in the file; an `on_demand` item is held back with its reason; the rules version is recorded; **seven nights later the score reads 1 proposed · 1 bought as proposed · 0 not bought · 1 bought not proposed**; the OFF flag stops the run; no 10-digit number in the output (F-185).
- The installer runs the selftest on the box, a dry rehearsal against the live spine into scratch, then places the file, the cron line, and runs tonight's rehearsal for real; a red at any step removes the file and restores the crontab.

## The one line (the owner's)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S341_ORDER_REHEARSAL/install_S341_ORDER_REHEARSAL.sh
```
