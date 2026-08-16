# S182_M1a — Marg fortnight backfill driver (DRY RUN BY DEFAULT)

**This kit installs no service and replaces no live file.** It places one script at
`/root/finance/marg_backfill.py` and stops. The database is not touched until you run
it *and* add `--apply`.

---

## What your export contains

Parsed by the live `marg_report.py` (`28b47d44…`), and it passed every one of its own
checks — all 15 days present, each summing exactly to its own DAY TOTAL:

**1–15 Aug · Sanjeevni Medicos · 355 bills · net ₹2,85,934** (cash ₹1,89,438 · non-cash ₹96,496)

Three warnings, all the parser working as designed: **18 credit notes** totalling
−₹9,760 (D314 returns) · **93 of 355 bills with no clinic ID** heading to WALK-IN ·
**7 bills with non-4-digit clinic IDs** scored low into review rather than attached to a
possibly wrong patient (D315).

**Worth a separate look:** 11 Aug (₹20,412, 25 bills) and 14 Aug (₹17,943, 23 bills) are
**100% cash — not one UPI or card bill**. Every other working day runs 40–76% cash. That
is the F-91 shape appearing in the pharmacy. ₹38,355 whose true tender split is unknown.
Ask Darpan before the trail goes cold; no code will recover it.

## Two live behaviours that shape this script

**It can only reach days you have already filed.** `ingest_day()` raises *"no day entry
… file the day first"* — the patient-revenue spine reads, never posts (D313). Unfiled
days are refused harmlessly and listed.

**Re-ingesting a day DELETES what the previous batch produced** (`DELETE FROM sale_item
… UPDATE ingest_batch SET status='superseded'`). Correct behaviour, and the reason the
dry run reports how many existing lines each day would lose, and the reason a backup is
taken before the first write.

## The silent-failure this script exists to prevent

`_colmap()` returns empty when no `ingest_source` row matches, and `adapter_csv` then
reads **zero rows while `ingest_day` still reports ok**. On live patient data that is the
worst available outcome: a clean-looking success that ingested nothing.

Rehearsed offline against a throwaway database, three ways, and it behaved correctly
each time:

| | result |
|---|---|
| source inactive | **REFUSED** — named, nothing written |
| map pointing at Marg-ERP display names (`"Bill No"`, `"Customer"`, `"Net Amt"`) | **REFUSED** — each mismatched field named |
| map matching the parser's real headers | wrote **37/37, 28/28, 36/36, 25/25** |

That middle case is not hypothetical: the selftest in `finance_ingest.py` configures the
map with those display names, while `marg_report.py` emits snake_case headers
(`bill_no`, `patient_name`, `amount`). **If your live map still carries the old names,
this script will refuse and tell you exactly which fields to fix** — instead of quietly
ingesting nothing.

The schema also seeds `(medical, marg_export)` **inactive**, so expect that to be the
first thing the dry run reports.

**Also asserted per day:** rows read must equal rows in the CSV. A short read aborts the
whole run, not just that day.

## Expect status `partial`, and that is fine

In rehearsal, 126 bills across 4 days became **99 lines in the spine + 27 in the review
queue** — every bill accounted for, none dropped. The batch status reads `partial`, not
`ok`, because low-confidence lines went to review. That is D315 working, not a failure.

## To run

```
bash /root/deploy/vps_deploy.sh S182_M1a
```

then put the .xls on the box (WinSCP) and:

```
/usr/bin/python3 /root/finance/marg_backfill.py <path-to.xls>            # dry run
/usr/bin/python3 /root/finance/marg_backfill.py <path-to.xls> --apply    # only if it looks right
```

**The .XLS itself must never go into git.** Every bill row carries an unmasked phone,
patient name and clinic ID (F-31, and the repo is public per D320). The CSV the parser
produces is clean — 355 rows, phones last-4 only, zero full numbers.

---

*Kit built S182 · rehearsed offline on a throwaway db, all three paths · `marg_backfill.py` places only*
