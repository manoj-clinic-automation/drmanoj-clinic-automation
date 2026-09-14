# S271_CHEQUE_MONTHS — the register's months come from the book, not from itself

**Session 257 · 14-Sep-2026 · a correction to S270, found on the live screen within the hour.**

## What was wrong

S270's month strip was built from the cheques already logged:

```
SELECT DISTINCT month FROM purchase_cheque ORDER BY month DESC
```

With nothing logged yet, the register offered only *Every cheque*. **September — which owes ₹400 on
the cheque lane and has nothing written against it — could not be reached from the register at all.**

**The most useful state of a register is the one where money is owed and nothing has been written.
That was the single state the page could not show.** It is the same shape as a report that only lists
what has already been done: correct, and useless at exactly the moment you need it.

## The change

One anchored line, and one helper appended:

```
months = _cheque_months_s271(con)
```

Every month that has a cheque, **UNION** every month the purchase book knows, newest first.
`_months()` is wrapped, so a box without the book still gets a working register rather than a 500.

## What it does not do

**The cheque register is deliberately NOT added to the purchase nav bar.** It is reached from the
payment sheet, which is where a cheque is logged, and from the sheet's cheque card in one tap. A
ninth item on every screen for something used once a month is clutter, and the owner has called that
PWA cluttered in his own words. If he wants it in the nav it is one line — and it would change every
purchase page's bytes, so it would be a claimed change with its own walk.

## The proof

- **16 offline checks, 0 failed** (`selftest_months_s271.py`): the helper's own logic (a book month
  with no cheque appears; a cheque month outside the book still appears; newest first; no duplicates;
  a box that cannot read the book falls back rather than raising; empty month values dropped), and
  **the patcher applied to the real S270 block** — parses clean, the query survives only inside the
  helper, running it twice does nothing, a wrong `--from` is refused and writes nothing.
- **`walk_s271.py`** is the S270 walk plus **section 4b**: it proves the month is offered *after* the
  patch, **was not offered before it**, and that opening it shows what the sheet still owes. The four
  other screens must still come back byte-identical.

**No pin is predicted (F-472).** The patcher prints the md5 it reads off the disk.
