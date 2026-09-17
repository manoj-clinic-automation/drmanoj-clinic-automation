# S303_SALARY_LOCKED_TABLE

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S303_SALARY_LOCKED_TABLE/install_S303_SALARY_LOCKED_TABLE.sh
```

## Why (F-519)

The August lock desk showed two totals. The green card is the **locked run** — frozen when August was locked on 13-Sep at 12:44, the figures approved and paid. The table under it was **recomputed from today's data**, and today's data has moved since the lock:

- the lock itself closed July's improvement holds, so a recompute no longer deducts them;
- Pravesh was marked as left today, and the month report drops a person who has left from every month, so he vanished from the recomputed August table;
- ledger entries corrected after the lock move a person's advance.

## What changes

For a **locked** month the desk shows the **locked table** — read back from what the lock saved — and its TOTAL is the card's. Under it, only when today's recompute differs, a short list: staff, locked NET, today, difference, and what moved. It is for information; nothing is paid or changed. A link opens the locked sheets exactly as printed at the lock.

For a month **not yet locked** nothing changes.

If the saved table ever cannot be read back, or does not add up to the card, the desk says so and shows no second total.

## Proof

- `staff_register.py --selftest` — green.
- `test_s303.py` — the real `salary_policy.sheets34_html` writes the frozen report exactly as a lock does; the desk reads it back: 23 checks (reader, differences, the page, the frozen sheets route, damaged report, staff login refused). The S300 file fails it; removing the add-up guard fails it.
- `walk_s303.py` — on the box: this file over a scratch copy of the live register with the live salary engine computing read-only; every locked month's desk answers, August must read back and add up to the card, and it **prints who differs today and why** — the F-519 answer.
