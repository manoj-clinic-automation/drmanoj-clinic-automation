# S195_MARG — Marg daily-sale: guard-and-send (Quick-Win, Method B)

This adds a **safety gate** in front of the sender you already use. Nothing that
is live is rebuilt: `SEND_TO_CLINIC.bat` is untouched, `D:\MARGERP` is never
written, and the maker/checker split (D325) is intact — the sender still only
**stages** a report; **Dr Manoj alone applies** it at the Hub.

## What it does
Before a `REPORT_1.XLS` is sent, `guard_and_send.py` runs the **same reader the
clinic server ingests with** (`marg_report.py`) and refuses to send unless the
file is:

- a **Detail** export with the 9-column layout (not the CASH-less *Summary-1*),
- **complete** — it ends with `GRAND TOTAL :` (a truncated partial has none),
- **internally consistent** — every day's bills sum to its DAY TOTAL and the
  GRAND TOTAL, and
- a **sane business date** (see date rules below).

A file that fails any check is **not sent**; the reason is shown on screen and
appended to `guard_alerts.txt`. This is exactly the "fail visibly, never a silent
partial" rule from the requirement doc.

> Proven against your real exports: the 17/18/19-Aug SENT files and the user
> 50018 / 61376 reports all pass with the right date, bill count and cash/UPI
> split; the 1–15 Aug and 14–15 Aug **range** files are refused (not single-day);
> a synthesised **truncated** file (no GRAND TOTAL), an **arithmetic** mismatch,
> a **Summary-1** file and a **stale** file are all refused.

## One-time setup on the medical PC
The guard is a small Python program (reading a legacy `.xls` needs Python; the
sender itself still uses only built-in Windows tools).

1. **Install Python** (once): https://www.python.org/downloads/ — tick
   *"Add python.exe to PATH"* during install. Check in a Command Prompt:
   ```
   python --version
   ```
2. **Install the one library it needs:**
   ```
   pip install xlrd==1.2.0
   ```
3. **Copy these three files into `D:\SendToClinic`** (next to `SEND_TO_CLINIC.bat`):
   `guard_and_send.py`, `marg_report.py`, `GUARD_AND_SEND.bat`.
   (`token.txt` stays where it is — the guard never reads it.)
4. **Test it** without sending anything:
   ```
   python D:\SendToClinic\guard_and_send.py "D:\MARGERP\users\61376\report\REPORT_1.XLS" --expect any
   ```
   You should see a green `GREEN — safe to send` line with the date and totals.

## How reception uses it (from today)
Instead of double-clicking `SEND_TO_CLINIC.bat`, double-click
**`GUARD_AND_SEND.bat`**. It checks every `REPORT_1.XLS`, and only sends the ones
that pass — otherwise it says why. Everything downstream (archive to `Sent\`,
MD5 de-dup, the ACCEPTED-FOR-REVIEW verdict, Dr Manoj's Apply) is unchanged.

## The Sent folder, filed by the date the report is FOR
On a GREEN check the guard also drops a copy into `D:\SendToClinic\Sent\` named by
the **business date it covers** — `REPORT_2026-08-19.XLS` for a single day, or
`REPORT_2026-08-01_to_2026-08-15.XLS` for a range — instead of the save-time
stamp. So you can find "the report for the 19th" at a glance. A later export for
the same day overwrites that day's copy (latest is the truth). Refused/incomplete
files are **never** archived. (`SEND_TO_CLINIC.bat` still keeps its own
timestamped copy too, for its MD5 de-dup history — that is unchanged.)

## Date rules (optional argument)
```
GUARD_AND_SEND.bat            same as: GUARD_AND_SEND.bat any
GUARD_AND_SEND.bat any        send any single-day file up to 3 days old (default)
GUARD_AND_SEND.bat yesterday  only if the file's business date is yesterday
GUARD_AND_SEND.bat today      only if the file's business date is today
GUARD_AND_SEND.bat 2026-08-19 only that exact business date (deliberate re-send)
```
`any` is the safe default for the morning "yesterday's report" rhythm: it still
blocks truncated, mis-typed-layout and **stale** (>3-day-old) files. Pin a date
when you deliberately re-run an old day.

## What is still to come (Phase 2)
- **Auto-generation** of the report inside Marg (the AutoHotkey macro that drives
  `Daily Reports → Sale Reports → BILL WISE STATEMENT`, Report Type = Detail,
  sets the date, exports to `REPORT_1.XLS`). This needs **one screen recording**
  of a real export on the medical PC (menu path → date → save → keys used).
- **Task Scheduler** unattended run. `GUARD_AND_SEND.bat any AUTO` runs with no
  prompts (the `AUTO` word suppresses the pauses) so it can be scheduled — but
  **test it once by hand on medical first**, then wire the schedule at the time
  you choose. The macro (above) generates the fresh file just before it runs.

## Files in this kit
- `guard_and_send.py` — the validator (exit 0 = safe to send).
- `marg_report.py` — the server's own report reader (bundled so the guard's
  judgment is byte-for-byte the server's). md5 in `SUMS.md5`.
- `GUARD_AND_SEND.bat` — reception/scheduler wrapper around `SEND_TO_CLINIC.bat`.
- `SETUP_S195_MARG.md` — this file.
