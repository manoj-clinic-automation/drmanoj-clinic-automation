# S302_DAILY_PRINT — the router files your daily summary sale report instead of refusing it

**Session 266 (Sanjeevni project) · 17-Sep-2026 evening**, on the owner's "proceed" on the work list. This was owed
since S262.

## What was wrong

**Your daily summary sale report was refused every time it was made.** This is the bill-wise statement Darpan prints
for the physical record and pays the day's cash against. It was refused as *unknown* each time, first seen on 16-Sep
at 23:55.

Marg writes it in its **print layout**, not its grid layout:

- one text column;
- the title *BILL WISE SALES STATEMENT AS ON*, with no date;
- the column heads as one line boxed between two rules of dashes;
- the day as a line of its own;
- *Total No. of Bills … GRAND TOTAL*, then *\*\*\* End of Report \*\*\**.

The router only knew reports whose column heads sit in separate cells, so it found no header row and no date.

## The change

- **`marg_router.py`** reads the print layout. It does so **only** when a sheet has no ordinary header row and has at
  most two columns. The boxed line becomes the header, and the rules are never taken as the title.
- **`signatures.json`** gains one block, **SALE_DAILY_PRINT / TEXT**:
  - dated from its own day line;
  - complete only with *End of Report*;
  - **never uploadable**.
- **`marg_ingest.py`** (VPS) adds SALE_DAILY_PRINT to **PHI_TYPES**. The report carries customer names and mobiles, so
  the server identifies it, records it, and deletes the raw file in the same call, as it does a sale report.

On the PC, the report is archived in `MargArchive\SALE_DAILY_PRINT\` and stays there, beside the other raw exports.

## The proof

**1. The router's own selftest:** 55 checks OK (47 before).

It covers:

- the print layout's header and title;
- identified as SALE_DAILY_PRINT, never SALE_BILLWISE;
- never uploadable;
- dated from its day line;
- a cut-off print refused as truncated;
- the DETAIL export still DETAIL;
- a sheet wider than two columns never takes the new reading.

**2. Regression on the PC (`regress302.txt`):** every export in `MargArchive`, archived and spooled, was read by the old
router and the new one.

- **359 files:** 357 judged identically.
- **2 changed:** both are the 16-Sep 23:55 print (the same file in `_REFUSED` and `_spool`). It went from UNKNOWN to
  SALE_DAILY_PRINT, dated 16-Sep, VERIFIED.

**3. The VPS door, run on the PC (`take302.txt`)** over a scratch database, fed three real files:

| file | old modules | new modules |
|---|---|---|
| the 16-Sep print | refused, deleted | SALE_DAILY_PRINT, VERIFIED, not kept |
| the 16-Sep sale DETAIL | 98 lines, not kept | 98 lines, not kept |
| the 16-Sep stock closing | kept | kept |

**With only the router and signatures new** and the old `marg_ingest.py`, the print would have been **kept, raw, on the
server**. So the installer places `marg_ingest.py` first and the signature last, under the collector's own lock.

**On the box, before anything is placed,** `walk_s302.py` checks a scratch copy of the three new files:

1. the router's selftest is green;
2. every export the box has kept is judged identically by the old and new routers;
3. the new type is never uploadable and is in PHI_TYPES.

## Install — one line on the VPS, after the publish

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S302_DAILY_PRINT/install_S302_DAILY_PRINT.sh
```

It restarts clinic-finance.

**Rollback:**

1. Put back the three `.bak_S302_*` files in `/root/marg_ingest/`.
2. Run `systemctl restart clinic-finance`.

**manojz:** the same `marg_router.py` and `signatures.json` are placed in `D:\Downloads\margsync\MargPull\` by the
session, with `.bak_S302_*` backups beside them. On its next run the pull's rescan re-reads `_REFUSED\` because the
signatures changed, so the 16-Sep print files itself.
