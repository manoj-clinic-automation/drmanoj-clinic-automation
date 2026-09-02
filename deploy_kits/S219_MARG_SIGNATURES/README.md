# S219_MARG_SIGNATURES — M2, the router learns three report types

**No code changed.** `marg_router.py` stays `781e5ff66d4eca6b6ed4703bf692fb46`
— byte-identical to its repo copy in `S203_R1/`. This is the data edit the
router was designed for: *"signatures.json — a data edit, no code change"*.

## What was unknown, and now is not
`MargArchive\_UNKNOWN` held three reports the router could not name. The owner
named two of them for M2; **the third had never been counted**:

| title seen | taught as | samples |
|---|---|---|
| `BILL/ITEM WISE PURCHASE STATEMENT FROM … TO …` | `PURCHASE_BILLITEMWISE` | 1 (28–31 Aug) |
| `SALE RETURN FROM … TO …` | `SALE_RETURN` | 1 (full August) |
| `SALE AS ON dd-mm-yyyy` | `SALE_BOOK` / `AS_ON` | 1 (08 June) |

## The S205 trap, met head on
`PURCHASE_ITEMWISE` — whose column layout is **identical** to the new
`BILL/ITEM` type — carries `end_marker: "Digital Purchase"`. That marker is
**absent from two of the three new samples**: Marg rotates its footer advert
between *"Digital Purchase | ERP Ordering …"* and *"MARG ERP NANO for Chemist …"*.

Copying the sibling's marker would have refused every future export of both new
types as TRUNCATED — precisely the S205 failure where `"GRAND TOTAL"`, borrowed
from a sibling, matched **0 of 5** real reports.

So every marker here was derived from the files themselves. All three end in a
`TOTAL` row before the advert, and the proof script checks that in each file and
prints what each sibling marker *would* have said.

## Why `BILL/ITEM` is its own type and not a variant
Same rows, different grouping (by bill rather than by supplier). One folder
holding two groupings of the same purchase lines is how double counting starts —
this project has already paid for that lesson twice (returns subtracted twice;
the archive supersede rule). Separate folders, no ambiguity.

## `uploadable: false` on all three — stated loudly, on purpose
S212's lesson: *"`uploadable: false` is the quietest possible way for a feed not
to exist."* These three are captured, verified and archived, but **nothing is
sent to the VPS**, because there is nowhere for them to land yet: purchase
tables arrive with M3, and the sale-return register with M7. When those land,
flipping the flag is a one-word edit — and it will be a deliberate one.

## Proof carried here
`prove_signatures.py` runs the router's own `identify()` over **every**
spreadsheet in the archive, with the old registry and the new one, and reports
any file whose verdict moves. Result on 02-Sep:

```
spreadsheets found in the archive: 101
every move is UNKNOWN -> IDENTIFIED : True
no file already classified moved    : True
every end_marker proven in its file : True
unchanged: 98   moved: 3   unreadable: 0
PROVEN — safe to install
```

Then, installed on manojz and `marg_rescan.py --apply` + `--tidy --apply` run:
three reports re-filed into new type folders, index rows corrected,
**`_UNKNOWN` went from 3 files to 0**, quarantine copies moved to `_rescued`.

## Still refused, and rightly — recorded, not fixed
Twelve files remain in quarantine. None is a standard report: empty titles,
one literally titled `test`, three `LIST OF ITEMS`, one `SALT WISE ITEM LIST`
(Amir's salt worklist), and two stock exports whose *title* matches
`STOCK_CLOSING` but whose columns do not — the router refusing loudly rather
than parsing a guess, which is correct. Teaching those is a separate decision.

## Rollback
`signatures.json.bak_S219_m2_<stamp>` sits beside the live file on manojz.
Restore it and re-run `RESCAN.bat` to return to the previous registry.
