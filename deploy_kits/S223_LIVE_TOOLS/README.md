# S223 LIVE TOOLS — and the honest answer is that NOTHING WAS INSTALLED ON A PC

**A11 requires that any session touching a PC captures the current bytes and compares them against
the LIVE SOURCE, not against the kit's own sums.** This close did that, and the comparison has a
finding in it.

## What this session actually did to `manojz`

**It installed no tool.** `push_day_tenders.py` was **run**, and it was not retained on the machine.
Its output is on the disk:

```
D:\...\followup_tracker\outputs\Day_Tenders.csv
```

206 tender legs across 61 days, read out of 79 retained raw `consultation_report_*.csv` exports.
`outputs\` **is** the Drive-synced folder, which is why no new transport was needed.

## ⚠ THE FINDING

**The script that produces tomorrow's split legs is not on the machine that needs it.**
A search of the tracker tree and `D:\Downloads` finds `push_day_tenders.py` only inside this session's
kit — never at a live path. So the only trace of it on `manojz` is the CSV it wrote.

**Consequence, stated plainly:** until the tracker-side parser fix is installed, **each day's splits
need this script re-run**, and right now there is nothing on that PC to re-run. The copy captured
here is the one to install.

| file | md5 | live path | live comparison |
|---|---|---|---|
| `push_day_tenders.py` | `30244990ed4ea2675f6052ec047002f5` | **none — NOT INSTALLED** | **no live source to compare against.** Not a mismatch; an absence, recorded rather than left silent |

## What it needs when it is installed

Python on `manojz`, read access to the retained `uploads\consultation_report_*.csv` exports, and
write access to `outputs\`. **No credentials.** It reads local files and writes one CSV.

---
*Captured at the S223 close, 04-Sep-2026. A kit verified against its own copy proves nothing about
what is running — and here, nothing is running.*
