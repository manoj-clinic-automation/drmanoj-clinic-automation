# S305_EXPORT_WATCH_DOOR — the missed-export watch reads the server's own door as well

**Session 266 (Sanjeevni project) · 17-Sep-2026 evening**, on the owner's "proceed" on the work list. This is D467
phase 2c: the "no export today" alarm on the server side.

## What was wrong

**The watch depended entirely on your office PC.** `export_watch.py` (S240) checks, on every day Amir punches in,
that the day's Marg exports arrived:

- purchase bill-wise;
- the item lines;
- the stock closing;
- on the 1st–5th, last month's supplier-wise.

It looked only at what **your office PC (manojz)** had parsed and sent on. The same exports also reach the server
through its own door, pushed straight from the medical PC, but the watch never read that record. So whenever manojz
was asleep, a day came out *unknown* even though the exports had arrived. The watch would also go blind on the day
manojz's data jobs are retired.

## The change

- **Evidence from the door.** A day is judged on **either** route: the office PC's feed, **or** the door's own
  *VERIFIED* record (`mi_file`). The door's evidence counts for bill-wise, item lines, month-end supplier-wise, and a
  **whole-store** stock closing (never an orthotics-only one). A refused file is never evidence.
- **"Unknown" is narrower.** It now means **neither** the medical PC's push **nor** the office PC has reported since
  the day ended.
- **Each day names its route:** `via: pc` or `via: door`.
- **Nothing else changes:** the table, the 23:40 and 10:45 runs, the phone push, the red line on the purchases hub
  and on Amir's page.

## The proof

**Selftest: 21 checks, 0 failures.** The 15 existing checks pass, plus 6 new ones:

- both routes silent reads *unknown*;
- office PC asleep but the door has the exports reads *ok via door*;
- an orthotics-only closing is not the stock closing;
- a next-morning whole-store closing through the door counts;
- a refused file is never evidence;
- a database without the door's table judges as before.

**Rehearsed on the office PC** against the 17-Sep nightly database, with 6–16 Sep judged as if Amir had punched every
day (`rehearse303.txt`):

- **On the real data**, the old and new watches give the **same verdict every day**. Both routes carried the same
  files, and there were no exports on 15–16 Sep.
- **The deliberate silent day.** Everything the office PC sent from 11-Sep was removed from the copy.
  - The old watch reads *unknown* on every day.
  - The new watch gives **exactly the verdicts of the full data**, from the door alone: 11-Sep ok, 12-Sep red
    (bill-wise and lines), 13-Sep red (stock), 14–16 Sep red.

**On the box, before anything is placed,** the installer runs the selftest. It then judges the last ten days with the
old and new watches on a scratch copy of the live database and the real punch file. It prints one line a day and
refuses if the new watch ever finds missing something the old one had present.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S305_EXPORT_WATCH_DOOR/install_S305_EXPORT_WATCH_DOOR.sh
```

There is no restart. **Rollback:** put `/root/finance/export_watch.py.bak_S305_2920c28e` back in place.
