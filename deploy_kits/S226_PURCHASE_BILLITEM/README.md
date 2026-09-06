# S226_PURCHASE_BILLITEM — the stock figure reads the report we actually export

The owner, 06-Sep-2026: *"check data of purchase exports in file, its there and
was there in previous one also."* He was right, and the fault was ours.

`push_expected.py` read **`PURCHASE_ITEMWISE`** and nothing else. Marg has a
second report whose name differs by one word — **PURCHASE BILL ITEM WISE** — and
that is the one exported most mornings. It carries the same item, packing,
quantity and loose quantity, and unlike Item Wise it carries **the bill's own
date on every row**, so nothing has to be dated by looking it up in another
export. The server's money side has read it since S224. Only the stock side did
not. The older reader it uses cannot even parse the file — it refuses on the
`TOTAL` row.

Measured before the change: **0 purchase rows** were reaching the computation
after the 03-Sep baseline. That is why "purchases known only to 03-09-2026"
would not move however many times the report was exported.

## What it does

`billitem_after()` reads every BILL ITEM WISE export whose period reaches past
the baseline and keeps the rows whose own bill date is after it.

**One export per bill date.** Two of these overlap constantly — 01→06 Sep and
04→06 Sep both carry the 05-Sep bills — and neither supersedes the other,
because their periods differ. Row-level de-duplication is the wrong tool: one
bill can legitimately carry the same item twice, in two batches. So the choice
is made per **bill date**, the way F-322 chooses per as-on date: the export with
the latest capture stamp that covers a date owns that date, and only its rows
for that date are read. Anything ITEM WISE already covered by BILL ITEM WISE is
skipped, so a purchase can never be counted twice.

It **refuses** rather than guesses on a negative quantity: this export exposes
no variance rows, so purchase returns cannot be identified in it the way
`purchase_returns.apply()` identifies them in ITEM WISE. No negative has ever
appeared in one — every file in the archive was checked before this shipped.

## Proven against the owner's own archive

Before: `purchases_after` returned **0 rows** after 03-Sep.
After: **12 rows**, each counted once (checked specifically for doubling), from
one export, horizon **06-Sep**.

And the cross-check turned a false pass into a true one. With the old code, our
computed 05-Sep figure matched Marg's 05-Sep export **373 of 373** — but only
because *both* were blind to six bills dated 05-Sep that were entered on the
morning of the 6th. With this change our figure includes them, and it matches
**Marg's own 06-Sep closing export item for item**:

| item | ours | Marg 05-Sep export | Marg 06-Sep export |
|---|---|---|---|
| MEG QCS | 684 | 234 | **684** |
| BIO D3 MAX | 358 | 58 | **358** |
| TYRO BR | 700 | 400 | **700** |
| JAKMAC 5 | 394 | 194 | **394** |

## The rule this earned

**Closing stock must be exported every morning for the LAST TWO DAYS**, exactly
as the sale report already is (D376). A bill entered today for yesterday is
invisible to yesterday's snapshot otherwise. That is the same fault as sale bill
A003396, on the purchase side. The wall card needs the word "two" added.

## Also changed

The refusal message that read *"Get the two purchase exports for the range"* —
which named neither report — now names the one that is enough:
*"Export PURCHASE > BILL ITEM WISE for the range in Marg."*

## Installed

`D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S208_STOCK_LEDGER\push_expected.py`
(backup `.bak_S226billitem_20260906-040949` beside it). Nothing on the VPS.
