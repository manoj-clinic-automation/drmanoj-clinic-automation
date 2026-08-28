# S207_RETURNS — the purchase-return loop

**Staged, not installed.** Nothing here has run against the live server, and the VPS was not
touched. Installing is two lines in `finance_app.py` and a restart, which is yours to do.

---

## Why it exists

A purchase return is the one transaction where **the goods leave the building before the paperwork
exists**. Between "set aside for return" and "credit note entered" the stock is off our shelf, off
Marg's books in nobody's account, and in the hands of a person whose name nobody wrote down.

Five months of history holds five returns worth **₹6,919** — one of them **₹4,042 on its own**.
There is currently no record anywhere of who carried any of them out of the door.

**An uncredited return is not a discrepancy. It is money the vendor owes us and nobody is
counting.**

---

## The stages, and why they cannot be skipped

```
BOOKED -> NOTIFIED -> AT_RECEPTION -> HANDED -> AWAITING_NOTE -> CLOSED
```

Every stage records **a named person**, and refuses to be recorded without one. `NOTIFIED` may be
skipped — a vendor is often told when his man is already at the counter — and **nothing else may
be**. A return that jumps from booked to closed is the exact shape of the loss this exists to
prevent, so it is refused with a sentence saying which hand-off nobody recorded.

**Every hand-off is a row, not an edit.** `pret_event` is append-only, and the status column is
only a cache of it. `/api/trail` rebuilds the status from the events and reports whether the two
agree — so a status that has been changed behind the trail's back is **detected rather than
trusted**. A lifecycle whose history can be quietly edited is one nobody can rely on three months
later, which is exactly when a return gets chased.

## The daily reminder

Patience per stage, deliberately short at the start and long at the end — goods sitting in a corner
marked "to return" is how a return becomes a write-off, while a vendor genuinely does take weeks
over a credit note:

| stage | chased after |
|---|---|
| set aside | 3 days |
| supplier told | 3 days |
| at reception | 2 days |
| handed over | 1 day |
| waiting for the credit note | 21 days |

`/api/chase` is that list as data; whatever sends the mail reads it. A reminder can be silenced,
but **only with a reason, and the silencing itself goes on the record**. The return stays open and
stays counted.

## Closing

`/api/credits` takes credit notes read out of Marg and matches them on item, batch and quantity.
**A line closes only when a credit note actually covers it** — not "about right". A part-credit
leaves the remainder open under the same reference, because a vendor who credits half is exactly
the case worth seeing. Loading the same note twice does not double-count it.

**Nobody ticks anything off.** A manual "mark as done" step is the step that stops being done in
week three.

---

## The list of what to return

`returns_data.py` builds it from Marg's own exports, so **Darpan does not have to remember what
needs returning**. Marg's expiry export already knows, and has been right and unread for a long
time.

**As at 27-Aug-2026: 28 flagged items are still on the shelf, and 14 of them expired before 2026.**
The oldest is `VINBACTUM DS`, batch 6347, **expired 2/2025 — twenty-five vials, eighteen months
ago**. A blank form would never have found that. A list with a button on it does.

Three limits, all shown on the page rather than hidden:

1. **The expiry export is a narrow window somebody chose in Marg.** The newest one we hold carries
   seven items. This is not the whole near-expiry picture and never claims to be.
2. **Only 15 of the 28 have a supplier on record.** Old stock is what gets returned, and old stock
   is exactly what has no purchase this year. Where the supplier is unknown the page says so
   instead of guessing.
3. **Some rows show negative stock** (`ASTOFEN R` is −3 strips 8). Those cannot be returned until
   the count is resolved, and the page must say so rather than accept a quantity.

---

## Four ways this went wrong while it was being written

None of them raised an error. Each produced a plausible answer.

1. Reading the closing-stock quantity with `float()` **dropped every strip-packed row** — 128 of
   377 — leaving a stock list made almost entirely of orthotics.
2. Marg's Description column is **the name, padded, with the pack glued on the end** —
   `VINBACTUM DS   1*1` — in **both** the stock and the expiry export. Matching them raw matched
   nothing: 57 flagged items, **0 found on the shelf**. The page would have reported *"nothing needs
   returning."* **A wrong answer that reads like good news is the one nobody questions**, so the
   check for it is written as a floor: if this list ever comes back empty, that is a fault until
   proved otherwise.
3. A hand-written supplier reader returned the report's own title,
   `/ITEM WISE PURCHASE STATEMENT`, as the supplier of seven items. It now delegates to
   `marg_purchase.read_purchase`, the parser the reconciliation was measured on.
4. `-` for nil was skipped rather than recorded as zero — and "absent from the file" and "none
   left" mean different things when the question is whether an expired batch is still here.

**One more, worth writing down because it destroyed a file:** `io.open(path, "w", newline="\n")`
inside a `<<'PY'` heredoc — the shell passed `\n` through literally, Python rejected the newline
value **after** the file had already been truncated to zero bytes. Read first, validate, then open
for writing.

---

## Install (yours to do, when you want it)

```python
import returns_app
returns_app.init(app, get_db, require, unit="medical")
```

Copy `returns_app.py` and `returns_schema.sql` beside `finance_app.py`, add the two lines, restart.
The schema builds itself on first call and is safe to run twice.

## Selftests

```
python selftest_returns_app.py     44 checks   (needs Flask; use /root/wa/venv/bin/python3 on the VPS)
python selftest_returns_data.py    26 checks   (needs D:\Downloads connected)
```

`selftest_returns_app.py` drives a real Flask app with a real sqlite file through the real auth
gate — including proving that a caller with no role is refused — because a test that imports a
function and calls it would have passed every silent defect this session produced.
