# S248_SALARY_RAISE — Awdhesh +₹500, Sandip +₹600, from the August 2026 salary

## The owner, 13-Sep-2026

> i need to increase sandeep salary , and awdhesh salary , is it an option ? give steps ,
> i need to apply from august 2026 salary

> awdhesh - increase by 500 / sandeep - inrease by 600

| | now | becomes |
|---|---:|---:|
| **Awdhesh** | 10,000 | **10,500** |
| **Sandip** | 7,400 | **8,000** |

## Why this is the whole change, and why August is the right moment

`base_salary` lives **once per person** in `/root/staff_master.csv` and carries **no
effective-from date**. Both salary engines read it live:
`staff_ledger.staff_bases()` and the register's policy engine take it from that one file.

- **July 2026 is LOCKED** (by manoj, 25-Aug, official total stored). Nothing already paid can
  move. *(The owner's ruling of 13-Sep: July was a test case — leave it. Its locked pack and the
  live recompute differ and that is not to be reconciled.)*
- **August 2026 is NOT locked** — Sheet 1 and Sheet 2 approved, "Ready to lock". So the raise
  lands in the August pack, which is exactly what he asked for, and in every month after it.
- Everything downstream follows by itself and correctly: the leave amount (salary ÷ 30.5), the
  late-minute charge rate, the day-rate divisor, and the advance ceiling (50% of base).

**There is no web page for base salary** — not on the fines & policy settings page, not in the
ledger's settings, not on the lock desk. The staff master is a file. That is why this is a kit and
not a click.

## What the kit does

`raise_salary_s248.py` — reads the master, and:

- **refuses unless each person is present exactly once and still sitting at the figure the raise
  was worked out from** (10,000 and 7,400). If anyone has moved either figure since, it writes
  **nothing at all** — not even the other person's half;
- backs the file up first (`staff_master.csv.bak_S248_SALARY_RAISE_<stamp>`), writes atomically
  through `csv.DictWriter` on the original header, so **every column, every row and the row order
  survive** and only the two `base_salary` cells move;
- reads the file back and **puts the backup in place if what it wrote is not what it reads**;
- prints before and after;
- says **ALREADY APPLIED** on a second run and touches nothing.

## Proof — `EVIDENCE_S248.txt`, verbatim. **33 checks, 33 ok.**

Real CSV files on disk, the script run as a subprocess the way the installer runs it, and the
**real `staff_ledger.py`** reading the file back afterwards.

- the dry run naming both figures and leaving the file **byte-identical**, with no backup taken;
- the raise landing, with a backup that still holds the old figures;
- **exactly two rows changed, and only the `base_salary` column** — proven cell by cell against
  the file as it was, including a name with a space, a notes column, and an inactive person;
- a second run saying ALREADY APPLIED and leaving the file byte-identical;
- five refusals — a figure someone else already moved, a missing person, a person listed twice, a
  missing file, a master with no `base_salary` column — **each writing nothing**;
- and then the salary engine itself: it reads 10,000 / 7,400 before, **10,500 / 8,000 after**,
  **nobody else moves by a rupee**, the inactive person stays out of its list, and the advance
  ceiling follows the new base.

## Install — ONE line on the VPS, after the owner's publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S248_SALARY_RAISE/install_raise_s248.sh
```

Gates: kit SUMS + KIT_ID → the master exists and has the columns → **the 33-check walk on the
box** → a **dry run against the real master, printed** → backup → apply → **read back through the
salary engine's own `staff_bases()`** → restart `staff-ledger.service` and
`staff-register.service` (both read the file per request; the restart removes any doubt). If the
engine does not read the new figures, the master is put back from the backup.

Then see it, and lock August:

```
https://attendance.dr-manoj.in/register/salary?ym=2026-08
```

Reverse: the line the installer prints —

```
\cp -f /root/staff_master.csv.bak_S248_SALARY_RAISE_<stamp> /root/staff_master.csv
```

## Worth knowing, for the next raise

Because the master has no effective-from date, a raise applied while a month is **already locked**
cannot reach that month, and a raise applied to an **unlocked** month restates it whole. Today
that is exactly what was wanted. The day a raise has to start mid-way through unlocked history —
or has to be backdated past a lock — the honest answer is a dated `base_salary` history rather
than a second copy of the figure. Not built, and not needed for this one.
