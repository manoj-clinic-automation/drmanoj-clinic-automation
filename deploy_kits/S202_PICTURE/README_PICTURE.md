# S202_PICTURE — two faults in `marg_gate.py`, both found by using it

**manojz-side. `marg_gate.py` `f09cfe61…` → the md5 in SUMS.md5. Selftest 49 → 53, +4 exactly.**

## Fault 1 — every pushed report was called `REPORT_1.XLS`

`post_one()` built its upload without a filename, so it fell to the default — **Marg's slot name**.
Every report that has ever reached the server arrived called `REPORT_1.XLS`, and the approvals card
listed them all under that one name. The owner could only tell June from August **by decoding a
hash fragment**, which is what he was doing when he reported it.

Fixed: the upload now carries the **archived** filename, e.g.
`SALE_BILLWISE_DETAIL__2026-06-12__20260826-063137__a815063a.XLS`. The bytes are unchanged; only
the hint the server records improves. Existing staged rows keep their old name.

## Fault 2 — one deliberate old report claimed 56 missing days

The coverage window ran from **the earliest report in the archive** to yesterday. On 26-Aug one
report for **12-June** was generated on purpose, to answer a question open since S186. It dragged
the window back across two months and the picture instantly reported:

```
days with NO export : 56 -> 2026-06-13, 2026-06-15, ... (56 dates)
ACTION: someone must open Marg and run BILL WISE SALES for that exact date
```

**None were missing.** The day before, the same file read `days with NO export: 0`.

**A file that cries wolf every ten minutes stops being read — and this is the file the 60-second
health check depends on.** A false alarm is worse than no alarm.

**Fixed in two steps, because the first was not enough:**

1. Coverage is measured over an operational window (45 days, matching the server's own missing-export
   horizon), and older reports are reported as **backfill — deliberately loaded, not gaps**.
2. That alone still claimed **32 missing days across July**, a month in which no daily export was
   ever produced because the feed began on 17-Aug. **The machine must not guess when coverage
   began.** It is now told, once, in `MargArchive\_coverage_from.txt` — one date, with the reason
   written above it. Absent, it falls back to the horizon and behaves as before.

The summary line now says **which rule set the start date**, so the number is never mysterious:

```
business days covered : 2026-08-17 .. 2026-08-25 (Sundays excluded; start: declared in _coverage_from.txt)
days with NO export   : 1 -> 2026-08-25
backfill outside the window : 1 -> 2026-06-12
   (deliberately loaded older days. NOT gaps, and no action needed.)
```

**56 false alarms became one real one** — and that one is real: **25-Aug, a trading day whose Marg
sale report was never produced.**

## Install

Already applied on manojz. Backup: `marg_gate.py.bak_before_S202_picture`.
Reverse: copy that file back over `D:\Downloads\margsync\MargPull\marg_gate.py`.

## Proven

`python marg_gate.py selftest` → **53/53** (was 49/49), and the rebuilt picture was checked against
the real archive before installing.
