# S270_CHEQUE_REGISTER — cheque number, date and payee, against the month

**Session 257 · 14-Sep-2026 · ⭐1 item 4.** The cheque register's own screen, beside the NEFT lane.

## The half of D513 that was never built

D513 says: *a vendor not on the authorised NEFT register never enters the NEFT file; he is paid by
cheque **and the cheque is logged**.* S261–S263 built the first half — the sheet names those vendors
and keeps them out of the bank file. **Nothing logged the second half.** A cheque left the clinic and
the only record of its number was the counterfoil in a drawer.

August's cheque lane is **₹1,469** (RAMA MEDICOSE). September has **AGARWAL SURGICALS AND MEDICALS,
₹400**, not in the vendor register at all. Small money, and exactly the kind that goes unrecorded.

## Three things it does that a counterfoil cannot

1. **It refuses a number used twice.** A live cheque number is unique in the register. Two cheques on
   one number is the single error a paper book never catches and a bank always does, weeks later.
2. **It reconciles to the sheet.** The sheet says what the cheque lane owes; the register says what
   has been written. The page names the difference and the vendors still waiting. A part payment
   leaves its vendor waiting, with the shortfall stated.
3. **It is appended, never erased.** A wrong entry is **voided with a reason** and stays on the
   register for ever. Only then does its number become usable again.

## A deliberate departure, stated out loud

Every other write on this sheet refuses once the month is **FINAL**. **This one does not, and must
not** — a cheque is written *after* the month locks, which is the point of locking. Logging a cheque
records something that already happened: it moves no figure the sheet reads, and the lock is
untouched. The month it settles is on every row, so a late entry is never silent.

## The screens

| where | what |
|---|---|
| the payment sheet | the cheque card now carries, per vendor, the cheque logged against it, what is still to write, and one line to log it |
| `/finance/purchase/page/cheques` | the register — every cheque ever written, month tabs, print A4 |
| `/finance/purchase/page/cheques/<yyyy-mm>` | one month, held against that month's sheet |

Full address of the register:

```
https://followup.dr-manoj.in/finance/purchase/page/cheques
```

## Who may do what

Logging, marking handed over and voiding are **maker or checker**, the same gate as the sheet's own
typed figures. A **viewer reads the register and is offered no control** — proven by the walk.

**One thing the owner may want changed, and it is his call, not a technical one.** The S262 note says
Shavez *"writes the cheque register"*, and Shavez is a medical **viewer**, so as built he can read it
and not write it. Making him a maker is an access change to a live gate, so this kit does not make
it. Say the word and it is one line.

## What it touches

**One new table**, `purchase_cheque`, created on first request and never at import (F-303). Nothing
else in `finance.db` is read differently or written at all — proven offline (check 45) and on the box.

**Two anchored edits, no existing line changed.** The block is inserted before the purchase audit
page; one argument on the sheet's body line is repointed to the new card. The S261 `cheque_card`
string is left exactly as it is — computed, unused, undeleted — so removing this kit restores the
file byte for byte. *Wrap, don't edit.*

## The proof

- **47 offline checks, 0 failed** (`selftest_cheque_s270.py`) — the block is executed against stubs
  of the helpers `purchase_app.py` provides, so every route runs exactly as written: the day-first
  date reader (including 31 September and 29 February refused), the duplicate-number refusal, the
  void that frees the number, the reconciliation to the rupee, a part payment, the FINAL-month
  departure, the viewer gate, and that the sheet's own tables are untouched.
- **The patcher was proven end to end** against a file carrying the real anchors: it patches, parses,
  repoints the card, leaves the old string in place, and refuses on a second run.
- **`walk_s270.py` v2 runs on the box** against a **copy** of the real database: `/hub`, `/scans`,
  `/orders` and `/book` must come back **byte-identical**; every rupee figure the sheet showed before
  must still be on it; the register must not have existed before the patch; a real cheque-lane vendor
  is logged and the duplicate refused; and the live database's md5 is taken before and after and
  printed either way.

**v1 of the walk failed on the box, and the failure was the walk's, not the kit's (F-483).** It ran
the patched copy out of `/tmp`, and `purchase_app.py` resolves `purchase_schema.sql` from its OWN
folder — so every page answered 500 looking for `/tmp/purchase_schema.sql`. Two repairs: the walk
now **refuses a `--file` outside the app's own folder**, and every check that reads a page goes
through `need200()`, because **four v1 checks went green on a 500 body** — passing for the absence
of a string that an error page also lacks. A check that cannot run now fails loudly or is named as
skipped; it never quietly succeeds.

**No pin is predicted (F-472).** The patcher prints the md5 it reads back off the disk, and that
value — nothing else — goes into the record.
