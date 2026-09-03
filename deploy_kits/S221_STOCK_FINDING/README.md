# S221_STOCK_FINDING — the stock difference becomes an audit finding

**Two live files:** `/root/finance/stock_app.py` (`83b0a1b0` → **`ed2f76ef`**) and
`/root/finance/stock_finding.html` (**new**, `8123a1cc`). The live stock files were verified
**byte-identical to the repo copies** before building, so no reproduction chain was needed.

## The brief, and the sentence that decided the design

> *"stock diff is a audit finding, its reporting shd be in proper way to me — date time, stck
> checkers involved, results, loss at mrp (loss at purchse to me), write off column where I decide
> these, and the total write offs list value, and the list which goes in for recovery from darpan.
> A hard copy … shared with darpan and amir, open the same in their mobiles or pc, and work in it."*

> *"recovery from wages — its more than that. **A blind sight is worse. When the system is in place
> its main purpose is deterrence.**"*

That second quote is the design. **Nothing is ever deducted by this code.** A recovery is *logged*
against a named person and shown to him. The deterrent is that the shelf is countable and the count
is attributable — not that money is taken by software.

## A finding is frozen; everything after it is a layer

At submit the count **seals**: a finding number, the time, the Marg export it was counted against,
both counters' names, and an md5 over the difference rows. `/api/finding/<id>` **recomputes that
md5 on every read** and says whether it still agrees. A recount is a **new** finding; the old one
stays saying what it said.

**The seal covers the counted quantities, not the values — and the walk is what settled that.**
The first version sealed the value too, and then a legitimately late rate (your D-b) made every
such finding shout *"these rows have changed"*. A warning that fires on correct behaviour is a
warning nobody reads. So the seal covers what a person could be judged by and what must never move:
item, Marg's figure, what was counted, the difference. A price may be corrected; a count may not.
The walk proves both halves — a re-valuation leaves the seal intact, and **a quantity altered
directly in the database is detected.**

Three layers sit on top, none of which rewrite the finding: the **staff answer**, the **owner's
decision** (append-only, latest shown, every earlier one kept), and the **voucher record**.

## Your rulings, as code

| | |
|---|---|
| **D-a** | recovery is valued **at MRP**, and the document says so in words on its own face |
| **D-b** | an unvalued item is **never** folded into a total — its own block, and a rate can be typed in or arrive with the next export; either way every waiting line is re-valued |
| **D-c** | **log only.** There is no ledger call in this file, and the walk measures it |
| **D-d** | a decision **closes the line**; a recovery **amount stays open** until settled |
| vouchers | recorded by number and date, with where the scan is kept, until Marg can export them |
| cost | the column is there and **empty**. Backfilled when M3 lands. No margin-derived guess |

## The document

One header, one table, three totals — composed on the server once (D349) and rendered three ways,
so no number can differ between the owner's screen, the counter's phone and the printed sheet.

**Header:** finding no · counted → submitted · Marg export counted against · **counted by / written
by** · items counted · the seal and whether it holds.

**Table:** item · Marg · counted · diff · **at MRP** · **at cost** · staff's reason · **your
decision** · the buttons.

**Then, separately:** where it stands (short · written off · marked for recovery · explained · not
yet decided) · **no-rate items, listed and loudly outside every total** · the recovery list · the
write-off list · the Marg vouchers. It prints with the controls hidden and signature lines for
*counted by · written by · seen by*.

**What each person gets is decided by the server, never by the page.** The counter sees the Hindi
reason buttons and **no decision button at all**; the owner sees the decisions and not the reasons.

## Proof

| | |
|---|---|
| **walk** | **52/52** — the real blueprint on a copy of the live db: a real export, a real count through the real `/api/count`, the seal, the staff layer, the ruling, the refusals, the re-valuation, the voucher, and a recount that makes a new finding without touching the old |
| **render** | **27/27** — headless chromium, the document opened **as the owner and as the counter**, real clicks, print stylesheet and signature lines checked |

**Two measurements rather than assurances:**

- **"Nothing is deducted"** — every table is fingerprinted before and after the owner marks a
  recovery, and only `stock_diff_decision` and the line's own status are allowed to differ. No
  ledger, advance, salary, staff or cash table may move.
- **"A recovery on a line with no rate is refused, not guessed at"** — it returns 400 and tells you
  to set a rate first.

**What the browser caught that no server test could:** the page called `/stock/...` while the
blueprint is mounted at `/finance/stock` — **the S209 mount-prefix fault exactly**, invisible to the
walk because the walk calls the API directly. The page now derives its own base from where it is
served. It also caught money rendering as *₹20* beside *₹18.50* in the same column, which is how a
reader stops trusting a total.

## What is deliberately NOT here

No ledger posting. No Marg integration. No cost figures. And **no proof from real data**: every
stock table in your database is empty — no count has ever been done — so by this project's own
standard **this kit is unproven until the first real count runs.** The page will say so.

## Before the first count

1. A **fresh Marg stock snapshot and rate export** — the live ones are 27-Aug and carry a rate for
   **187 of 376** items.
2. Two people, and the count page filling `counted_by` **and** `entered_by`.

## Files

| file | what |
|---|---|
| `patch_stock_finding_s221.py` | stock_app.py — schema, seal, document, layers, rate, voucher (4 anchors) |
| `stock_finding.html` | the document itself — owner, counter and print |
| `walk_stock_finding_s221.py` | the live-shape walk, 52 checks, runs on the box |
| `RENDER_TEST_finding_s221.py` | the browser gate, 27 checks, offline |
| `EVIDENCE_walk_finding.txt` · `EVIDENCE_render_finding.txt` | what they printed against these bytes |
