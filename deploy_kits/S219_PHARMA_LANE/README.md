# S219_PHARMA_LANE — M3 / PP0-lite: the pharmacy lane

**Reception picks the lane at the scan intake.** A pharmacy purchase bill is stored
`kind='Pharmacy'`, `status='captured'` — a **witness**: scanned, stamped, filed, and later
matched against what Marg says. It is not a clinic asset or consumable waiting for anyone's
approval, and D335 says exactly that: the pharma kind exists *"to keep the volume out of the
asset approval queue"* (~80 bills a month).

## The design decision that made it small
`status='captured'` is the whole trick. Because a pharmacy bill never carries `'draft'` or
`'approved'`:

| existing behaviour | why it is untouched |
|---|---|
| the "N pending" badge | counts `status='draft'` |
| the owner's `/purchases` rate-history page | **all eleven** of its queries filter `status='approved'` |
| `bill_approve` | refuses anything that is not `'draft'` |

So **not one of those eleven queries needed editing**, and the owner's page behaves exactly as
it does today. The alternative — a new kind flowing into the approved pool — would have meant
eleven fragile edits in one route.

## The two traps found while designing it, both closed
1. **`bill_edit` whitelists `kind` to `("Asset","Consumable")` and falls through to
   `"Consumable"`.** Editing a pharmacy bill would have **silently** moved it into the clinic
   lane. `"Pharmacy"` is now in that whitelist.
2. **`bill_edit` refuses any status but `'draft'`.** A pharmacy bill never becomes a draft, so
   a mis-read scan — wrong vendor, wrong total — could never have been corrected by anyone.
   `'captured'` now edits too. *A witness nobody can fix is worse than no witness.*

The refusal message deliberately still begins "Only draft bills" — the app's own smoke suite
asserts that substring, and changing it would have turned a passing test red for no reason.

## The scanner needed no change
The widget forwards `CFG.uploadFields` verbatim; that is how the Note has always reached the
server. The lane rides the same road, so `scanner_widget.js` stays exactly as installed.

## Proof — the real app, not a lookalike
`selftest_pharma_lane.py` drives the **patched app through its own Flask test client**: a real
intake, a real database, the real routes. **22/22**, including:
* a lane-less scan still behaves exactly as before (`Consumable`/`draft`)
* the pending badge counts 2 of 3 — pharmacy does not inflate it
* the approved-only filter behind `/purchases` cannot see a pharmacy item
* approving a captured bill does **not** approve it
* a captured bill can be corrected, and is **still Pharmacy** afterwards, not downgraded

And the app's own suite: **`smoke_test.py` 342 passed, 0 failed** — the same 342/0 recorded
against this app at S177, so nothing else moved.

## Boundaries held
Sends nothing. Touches no Marg data. Reads and writes no purchase figure. Adds no table.
**August purchase data stays provisional** under the owner's 02-Sep hold — this captures only
paper arriving from now on.
