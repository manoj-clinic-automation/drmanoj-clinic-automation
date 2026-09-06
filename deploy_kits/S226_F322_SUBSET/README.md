# S226_F322_SUBSET — why the merge never reached the page

The owner merged the duplicate `LACTOVAX SYP` in Marg — exactly the cleanup he
had been asked for — re-exported the closing stock at 03:04, watched the log say
**"pushed and marked (md5 523e8318)"**, and the drift page went on showing the
seven-unit gap he had just closed.

**Two faults, compounding. Both are in `push_snapshot.py` on manojz.**

## 1 · Row count was a tiebreaker, so a merge looked like a filter

`newest_full()` chose by `(as-on date, row count, capture stamp)`. A merged
export is legitimately **one row smaller**, so the 373-row merged file lost to
the 374-row pre-merge file and was refused with the F-235 message *"a category
filter, not the shop"*. It is not a category filter; it is the same shop with
one fewer item master.

The log line that says *"pushed and marked"* names the file that **triggered**
the run, not the file that was **sent**. That is why the run looked correct.

**The fix is the router's own rule, and now literally the same number.** An
export is a filtered subset only when it is at or below **60 %** of the day's
largest (`marg_router.SUBSET_MAX_FRACTION`), or under the absolute floor.
Above that it is a full store export, and among full exports **the latest
capture wins** — the owner's standing rule for sale reports, applied here too.

* 81 of 374 = 22 % → still refused, however late it is.
* 438 of 439 = 99.8 % → accepted, and it supersedes.

Row count is now a **guard**, never a tiebreaker. The day is chosen first, so a
bigger export of an older day can never win.

## 2 · Two item masters under one name, and one of them silently dropped

Worse, and it would have bitten with or without the merge. In the pre-merge
export the name `LACTOVAX SYP` appears **twice** — two item masters, `-2` and
`7`. The sender kept the first and dropped the rest **in silence**:

```
LACTOVAX SYP  -2.0
LACTOVAX SYP   7.0     <- dropped, no message
```

The server was told `-2`. Our books said `5`. The page showed a seven-unit gap
that was never on the shelf, and nothing anywhere said a row had been discarded.

The stock of a product is the **sum of its masters**. They are now added, and
the run says so out loud:

```
  two item masters under one name, added together: LACTOVAX SYP = 5
```

This is defence in depth: even without the merge, the figure would now be right.

## Proof — against the owner's own archive, read-only

`EVIDENCE_dryrun_real_archive.txt` runs both files over `D:\Downloads\margsync\MargArchive`:

| | what it picks for 05-Sep |
|---|---|
| the file that is live now | skips the merged export, sends the pre-merge one |
| this kit | sends the merged export; names the two earlier ones **superseded** |

`EVIDENCE_walk_f322_s226.txt` — **18 / 18**. Sections 1 and 2 run against the
real archive; section 3 proves the F-235 guard still refuses the orthotics shape
(81 of 374), holds the 60 % line exactly, and never lets an older day win on
size. Run it yourself from inside this folder:

    python WALK_f322_s226.py

The walk cannot pass on the file that is live — it does not even get through
section 1, because the rejection list changed shape. That is recorded here
rather than dressed up as a clean red.

## Installing

There is **nothing to paste on the VPS.** This file runs on manojz, out of the
repository working copy, at:

    D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S208_STOCK_LEDGER\push_snapshot.py

which means the swap is a live change on the owner's own machine and needs his
word first. It takes effect on the next capture — no service, no restart.
