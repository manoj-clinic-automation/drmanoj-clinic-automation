# S513_RENEWALS_EXPIRY — a renewal counted to its real expiry (D689; closes F-775)

Session 304 (parent), 10-Oct-2026. The owner's ruling: a renewal comes up **45 days before its real expiry** and is
**red only after it**.

## What was wrong

Each row of the personal Janitor's RENEWALS list has a `dateISO` that is an **early-alert day** (the arms licence:
27-Sep), while its real expiry is written in its note (26-Dec). The health page read the alert day as the deadline and
has shown the arms licence **OVERDUE** since 27-Sep — a false red that teaches anyone to pass over the page's reds.
**An alert day and a deadline are two fields.**

## What changes

| where | what |
|---|---|
| `/root/finance/finance_app.py` | bff362c3 → ec5b3ab1 by `apply_s513.py` (read whole first; drift was 4). The window is 45 days (was 30). The push door keeps `expiryISO` beside `dateISO`; a row without a valid one keeps its alert day as its expiry, exactly as before. The Renewals row counts days to the expiry: info inside 45 days, warn inside 7 and on the expiry day, **red only the day after**. A stale feed still names what is near. One bad stored row is skipped rather than failing the whole row. The selftest's renewals block follows (and keeps the asset database out of it). |
| personal Janitor project, `Renewal_Nag.gs` v3 | placed by the assistant in the owner's signed-in browser; copy in `deploy_kits/GAS_CURRENT/PersonalJanitor/`. Works out each row's real expiry (`expiryISO` if a row has one, else the date in its note after *Expiry / Expires / valid to*, else `dateISO`; a note dated before `dateISO` is an old note and `dateISO` wins). The e-mail nag: from 45 days before the expiry weekly, inside 21 days every 3 days, inside 7 days daily, OVERDUE only after the expiry. The push sends `expiryISO`, never the note, and takes every bracket holding a number out of a name. `renewalsExpiryCheck()` is a dry run. |

Either half can go first: the old server drops `expiryISO` and behaves as before; the old script sends no `expiryISO`
and the new server reads its `dateISO` as before.

## Run

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S513_RENEWALS_EXPIRY/install_S513_RENEWALS_EXPIRY.sh

## To take it back

    \cp -p /root/finance/finance_app.py.bak_S513_bff362c3 /root/finance/finance_app.py && systemctl restart clinic-finance
