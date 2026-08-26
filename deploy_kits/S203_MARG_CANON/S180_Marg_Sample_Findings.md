# S180 — Marg sample files: what the real files show

**Session:** 180 · **Date:** 2026-08-15
**Inputs:** `REPORT_1.XLS` (33,280 B, md5 `e81f97fe…`, created by Excel 15-Aug 11:45) from
`D:\MARGERP\users\61376\report\` · `report.txt` (2,420 B, md5 `da087842…`) from
`C:\Users\Public\MARG\17476\`
**Status:** ANALYSIS ONLY. No adapter built — one finding below changes the design and must be
settled first.

**PHI:** both files carry full patient names and full 10-digit phone numbers in the DESCRIPTION
column. No patient row is reproduced in this document. The files stay in the session workspace,
are not written to project knowledge, and must never enter the repo or a git kit (F-31/F-49).

---

## 1. The headline — this is NOT the report the survey documented

| | Survey's file (§4) | The file just supplied |
|---|---|---|
| Title | `BILL WISE SALES STATEMENT **FROM** 01-08-2026` | `BILL WISE SALES STATEMENT **AS ON** 14-08-2026` |
| Coverage | 14 days, 01–14 Aug | **one day**, 14 Aug |
| Size | 90,112 B, written **09:59** | 33,280 B, written **11:45** |
| Columns | **9** | **3** |
| Layout | `BILL NO. \| DESCRIPTION \| D.R. \| GROSS AMT. \| DISCOUNT \| TAX \| DR/CR \| NET AMT. \| CASH` | `BILL NO. \| DESCRIPTION \| BILL VALUE` |

**Same menu, same filename, same folder — two different reports.** The survey caught one variant;
this is the other.

### Why this matters more than it looks

**The 3-column variant cannot feed the finance module.** There is one money column, `BILL VALUE`.
There is no `CASH` column, so the rule locked at S179 —

```
cash = the CASH column
UPI  = NET AMT. − CASH        (never the mode field)
```

— **is impossible to apply.** The 3-column report knows *how much* was billed and nothing about
*how it was paid*.

The `report.txt` from `C:\Users\Public\MARG\17476\` is the **same 3-column report in text form** —
I checked bill-by-bill: same 23 bills, same 23 values, same total. It adds nothing the XLS lacks.
Neither file can produce the cash/UPI split.

---

## 2. The mode field is confirmed worthless — with proof this time

All **23 of 23** rows in this file carry the mode `.CASH`. Not one `.UPI`.

That cannot be true. The survey's own 14-day grand totals say otherwise:

```
Net  277,083.00      Cash  193,412.00      →  UPI ≈ 83,671  ≈ 30% of takings
```

Roughly three rupees in ten came in by UPI over that fortnight, yet this day's report labels every
single bill `.CASH`. So the `.CASH`/`.UPI` field is **not the tender** — it is an account or ledger
label. S179 already ruled *"never the mode field"*; this is independent confirmation of that rule
from a second file, and it is worth having, because the mode field is the obvious thing a future
build would reach for.

The trailing `#` marker is **also not the tender**: 18 of 23 rows carry it, which matches neither
the ~30% UPI share nor anything else visible. Its meaning remains unknown. **Do not build on it.**

---

## 3. What the file did settle — three good results

**(a) Credit notes are plain negatives.** Open question #1 from the design note is answered:

```
CN00167   -1150.00
CN00168     -77.00
```

Negative `BILL VALUE`, no separate sign column, no special handling. Straightforward.

**(b) A parsing trap, caught before it could bite.** In the XLS the positive rows are **numeric**
cells (type 2) but the two negative rows are **text** cells (type 1) carrying leading spaces —
`' -1150.00'` and `'   -77.00'`. A parser that trusts the cell type, or reads only numeric cells,
would **silently drop every credit note** and overstate the day. Reading each value as
`float(str(cell).strip())` handles both. This is a live example of the F-78 lesson — parse the
value, never assume its shape.

**(c) The self-checks in §3.5 of the design work exactly as intended.** Verified against this file:

```
21 sale rows          19,170.00
 2 credit notes       −1,227.00
                     ───────────
 sum                  17,943.00
 DAY TOTAL cell       17,943.00      ✓ exact
 footer "Bills: 23"        23 rows   ✓ exact
```

The file proves its own arithmetic to the rupee. The adapter can safely refuse any file that
doesn't.

---

## 4. What I now think happened, and the one question that settles it

The 09:59 file and the 11:45 file are two different runs on the same morning.

**The 09:59 one is more likely to be the staff's real daily habit** — a month-to-date run on the
morning of the 15th, covering business through the 14th, with the full 9 columns including `CASH`.
That is exactly the shape needed to fill the Google Form's cash and UPI boxes, which is what the
printout has been used for all along. The 11:45 file was made after I asked for one, and may have
been run with different options selected.

**But I am inferring, and I would rather not.** The two runs are 105 minutes apart and I cannot see
who clicked what.

### The question

**Which report do the pharmacy staff actually run each morning — and can I have that file?**

Concretely: the file that was sitting at `D:\MARGERP\users\61376\report\REPORT_1.XLS` at **09:59**,
before the 11:45 run overwrote it. If it has been overwritten, ask whoever runs it to produce their
normal daily report exactly as they always do, without changing any option, and send that.

**If their normal report is the 9-column one, nothing in the design changes** — the money rule
holds, the self-checks hold, and I build the adapter.

**If their normal report is this 3-column one, the fix is a settings change, not a code change:**
ask them to switch to the detailed option that produces the 9-column output. Same menu, same
clicks, one different selection. That is far better than trying to reconstruct a payment split that
the file simply does not contain.

---

## 5. Consequence for the design note

One conclusion holds regardless of the answer, and should go into the adapter:

> **The adapter must identify the variant before parsing.** Two different reports arrive under the
> same filename in the same folder. It must read the title row — `AS ON <date>` (single day,
> 3 columns) versus `FROM <date>` (range, 9 columns) — and the header row, then select the column
> map. On an unrecognised layout it must **refuse the file and say so**, never guess a column
> position. A file is not identified by its name or its path (D188).

Sections 3.3 (the money rule) and 3.5 (self-checks) of `S180_Marg_Feed_Transport_Design.md` are
correct **for the 9-column variant only**. I will revise that document once the variant question is
answered, rather than churn it twice.

---

*Also noted: `C:\Users\Public\MARG\17476\` is a Marg user folder (`17476`) not seen in the S180
folder survey, which found only `50018`, `61376` and `a` under `D:\MARGERP\users\`. Worth a line in
the record; it does not affect this build.*

*Nothing built, nothing installed, no live file touched.*
