# S237_SALE_BILL — keep the sale bill's own money row

**Rung 1 of the Sanjeevni architecture work. Built 10-Sep-2026.**
**This kit is PUBLISHED, NOT INSTALLED, and it writes nothing to the database until you say so.**

---

## THE PROBLEM, IN ONE SENTENCE

Marg tells us the discount for every bill; we read it correctly, and then throw it away before it can
be stored — **₹27,375.33 across the 21 days in your archive, about ₹1,300 a day.**

Every figure that values a sale from its item lines is therefore a **gross** figure. On a
30%-discounted appliance that overstates the takings by up to **43%**.

## WHAT THIS KIT DOES

It adds **one table**, `sale_bill`, holding each bill's `GROSS · DISCOUNT · TAX · DR-CR · NET · CASH`,
and fills it from every export in the archive.

**That is all it does.** It does not attach the discount to item lines — that is Rung 2, and it needs
the ruling table T1 live first. It does not change the parser, the ingest, any CSV, or any existing
table. Written beside, never over.

**It stores no patient name, no phone and no clinic ID** — the bill's money and nothing else.
Attribution needs the money; it does not need to know whose bill it was.

## WHAT IT REFUSES TO DO

- **It never assumes the parser.** The live `/root/finance/marg_report.py` matches neither copy in
  the repository, so this module asserts the fields it needs and **refuses loudly, naming what is
  missing**, rather than writing a row of nulls from a parser it did not expect.
- **It never hides Marg's rounding.** 181 of 524 bills differ from `gross − discount` by −49 to +50
  paise, because Marg rounds a bill's net to the rupee. That residual is **stored** in `round_p`, not
  swallowed by a tolerance. Anything beyond one rupee is refused as a misread.
- **It never runs twice to a different answer.** Re-running changes nothing; where the same day
  appears in several exports the later one wins, whatever order they are read in.

## HOW IT WAS PROVEN

`py_compile` clean · **44 selftest checks, 0 failures** · and a **live-shape walk against the real
archive and a copy of the real 08-Sep database** — full record in `WALK_PROOF.md`:

- **524 bills, 21 days, ₹27,375.33 of discount recovered**
- **the six single-appliance bills of the S236 finding reproduce 6 of 6**, from the pipeline instead
  of by hand
- **it joins to the item lines: 448 of 524, and every one of the 76 that do not are days after the
  backup's last ingested line day.** Unmatched, not a credit note, inside the window: **zero**
- **idempotent** — a second identical run changed no row and no total
- `sale_line_item` and `marg_item` **unchanged** before and after

## INSTALL — one line

```
bash /root/deploy/vps_deploy.sh S237_SALE_BILL
```

It places the file, proves it, works out where the exports live on that machine, reads them, and
**prints what it would keep — writing nothing at all.** Then it prints the one line that stores it.

**Two steps on purpose.** This is a money table; the numbers should be seen before they are kept.

## TO UNDO IT COMPLETELY

```
sqlite3 /root/finance/finance.db "DROP TABLE sale_bill"
```

Nothing else reads that table yet, so dropping it returns the estate exactly to where it was.

## 🟠 ONE THING IT CANNOT GIVE YOU, AND IT SAYS SO

**27-Aug has no bill headers.** Its export was saved as `.xlsx`, and the repository's parser reads
only the older `.xls`. The live parser may well read it — `marg_backfill.py`'s own help mentions both
— so the first live run will say. Either way the day is **named, not silently missing.**

---
*S237_SALE_BILL · 10-Sep-2026 · standard library only. Nothing live was touched to build this.*
