# S223_DOCTERZ_READER — the clinic's day revenue, read on the VPS

**Stage 1, part one: the reader and the store. The screen is part two and is NOT in this kit.**

## What this does

Reads the `Day Revenue` sheet out of every `Staff_Action_Today_<date>.xlsx` in the clinic's Drive
folder and stores one row per business day in `finance.db`. Nothing is displayed yet — this kit
starts the data accumulating so that the screen, when it lands, has history behind it rather than
one day.

**No new export. No new push. No PC dependency.** The tracker already writes these workbooks and
Drive already syncs them, continuously, since 04-Jul-2026. Proved at the S223 open: the box's own
service account lists 147 files in that folder.

## D367 — the owner's ruling, and what it changed

> *"if totalling error is on docterz, sort it out, from individual entries, its their reporting
> method which is fixed, we can fix our side only"*

**Every figure is computed from the itemised lines.** The sheet's own SUMMARY, Cash and Online/UPI
lines are read too, but only so a disagreement can be recorded in `variance_note` where nobody has
to look at it. They are never displayed and they never win.

That ruling is not theoretical. On four of the eight days tested, **the sheet's own cash + online
does not equal its own grand total** — by ₹600 each time, and on two of them in the direction that
says the sheet declared MORE money than it billed. Computing from the lines makes all four go away:
on every one of the eight days the tender split accounts for every rupee of the row total.

## Proven before it ships — 14/14 GREEN

`EVIDENCE_selftest_s223.txt` carries the run. Eight real workbooks, 06-Jul to 03-Sep 2026:

- total = consultations + X-ray + procedures, **every day**
- the tender split accounts for **every rupee** of the row total, every day
- **19-Aug = ₹16,400 and 02-Sep = ₹20,900**, matching both the working paper and tonight's
  independent proof against the raw Docterz exports
- the F-93 phantom rows are dropped and counted, never stored as concession cases
- a second run changes nothing; of two exports of one date the later-taken wins (the S221 rule)
- **no mobile-shaped number and no patient-UID shape reaches the database** (F-185)

## The traps this reader exists to handle — each measured, none assumed

1. **Row numbers are not stable.** Blocks move with the length of the list above them, and the
   PROCEDURES block is **absent entirely** on a day with no procedures. Blocks are found by their
   banner text, never by row number.
2. **Column meaning changes per block.** Mode is column F in PAID CONSULTATIONS, column E in X-RAY,
   and column E in PROCEDURES — under a header that says `Note`, not `Mode`.
3. **F-93.** The FREE / CONCESSION list ends with three phantom rows that continue the S.N sequence
   (`nan`, `Cash`, and the day's cash total as a *string*). Column C is empty on all three and on no
   real line, so that is the discriminator.
4. **The `vs 600` cells hold the literal text `= 600`**, which Excel stores as a formula, so
   `data_only=True` returns `None`. Nothing here reads that column.
5. **Clinic ID is a string.** Never coerced, and never stored by this kit at all.
6. **The Mode vocabulary is open** — `Cash`, `Online Payment`, `Debit Card`, `Split Payment` seen so
   far. An unknown mode is carried under its own name and flagged, never folded into "online".
7. **The date comes from the sheet's own A1 banner, never from the filename.** The file dated D
   carries the last *completed* business day, which is D−1 except across a Sunday.

## ⚠ PRIOR WORK — read this before treating the kit as new

**`deploy_kits/S211_DAYREVENUE/finance_day_revenue.py` already exists** and reads this same sheet.
It was built at S211, proven across **67 workbooks**, and never installed; its own README ends
"Still to build: the screen."

It was found late, while this kit was being written — caught before shipping, not after, but the
search that should have happened first happened second. Two of its findings stand and are carried
forward here:

- **the date must come from the sheet, not the filename** — it measured 60 of 67 workbooks carrying
  a revenue date earlier than their own name;
- **18 of 65 days did not add up, ₹9,601 unexplained**, "the negative days are the interesting ones".

**This kit supersedes it** for one reason: S211's reader reports the sheet's own cash and online
figures, and **D367 now overrules them**. It predates the ruling. Its rehearsal harness across 67
files remains the stronger evidence base, and reconciling this reader against all 67 — rather than
the eight tested here — is **owed**.

## What is NOT in this kit, deliberately

- **The screen.** It mounts inside `finance_app.py`, whose live bytes descend from
  `S204_VPS_LIVE` (`7948cee0…`) through more than twenty patchers. Those bytes must be reproduced
  offline and matched against the live pin **before** any patcher is written against them
  (F-280 / F-299). That reproduction has not been attempted yet.
- **The tile.** It follows the screen.
- **The bank comparison.** It needs `upi_txn` queried for whether the ICICI MPR names the rail.
- **The split-payment breakdown.** The Day Revenue sheet carries a line's Mode but not its legs, so
  a `Split Payment` line is stored under that name rather than guessed at. The legs exist only in
  the raw export, and recovering them is the tracker-side parser fix — proven offline tonight,
  also not yet installed.

## Install

Needs `openpyxl` in the interpreter that runs it. The ingester checks and refuses with the exact
install line rather than half-working. See `INSTALL.txt`.
