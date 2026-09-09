# S236_DISCOUNT — T1 of the spine: the ruling table

**09-Sep-2026.** Two files. **Nothing existing is altered, renamed or dropped** — this adds
**two** new tables and a run log, and fills them from the owner's own settled register.
Every screen keeps working exactly as it does today, because **nothing reads these tables yet.**

This is **T1**, the first rung of "finalise the spine".

---

## What it stores

**D437 — the orthotic discount register is the authority on realisable price.** All 93 products
the owner settled on 09-Sep: **66 with a discount (10–40%) · 17 at M.R.P. · 7 retired · 3 internal
consumption.** One row per product, carrying his percentage, the printed M.R.P. it applies to, the
date that M.R.P. was in force, his ruling in plain words, and the name Marg called the product when
he decided.

It replaces `MARGIN_ORTHO_DEFAULT = 0.30` **as the source of a realisable price** — but see below,
because that sentence is not quite what it looks like.

## Three things this was built around, each found by reading the real data first

**1 · `marg_item_fact.mrp_p` is not an M.R.P.** It is the **median observed sale price**, computed
from the shop's own sale lines (`marg_spine.py`, the `sale_line_item` fact block). An observed price
wearing an M.R.P. label is exactly the mislabelling the S235 derive pass exists to end, and it must
never be used as the base of a discount.

**2 · The printed M.R.P. is not in the database at all.** `stock_snapshot` has no M.R.P. column and
`stock_mrp_manual` is **empty — 0 rows**, measured on the 08-Sep copy. The M.R.P. figures the owner
ruled against came off a Marg stock report. **So the ruling has to carry its own M.R.P., with the
date that M.R.P. was in force** — which merges two of the spine's ten rungs into one table instead
of two.

**3 · `MARGIN_ORTHO_DEFAULT = 0.30` is not a discount.** It is a **cost → price gross-up** used only
for the `provisional` (ESTIMATED) rung. The S235 documents say the register "replaces" it; read
against the code, that is loose. The register is a **better rung above it**, not a replacement.
**0.30 stays**, as the fallback for a product with no M.R.P. and no ruling. Deleting it would have
silently unpriced every appliance the owner has not yet ruled on — 281 of 374 products.

## The one rule

> **A missing row means NOBODY HAS DECIDED. A row with `discount_pct = 0` means DECIDED: SELLS AT
> M.R.P. These never collapse into each other**, and the schema makes it structural rather than
> conventional: the absence is the absence of a row, `discount_pct` is `NOT NULL` for every decided
> price, and `realisable_p()` returns the word `undecided` rather than a number.

`internal_use` (D438) is the one state with no selling price at all, and it is marked by its own
column and its own state — never by a null percentage. A `CHECK` constraint enforces that
`state = 'internal'` and `discount_pct IS NULL` are the same condition, so no future writer can
blur the two.

## What it deliberately does NOT do

**It does not re-order the live price ladder.** The ruled price and the observed price are readable
side by side, so that where the counter is actually charging something other than the ruling becomes
a visible number rather than a silent overwrite. Which rung wins is a decision with money on it, and
it belongs to the owner — informed by that number, which §"What the walk found" below reports.

**It never guesses an identity.** Resolution is the spine's job. A ruling whose name does not resolve
to exactly one product is refused, reported, and opened as a `marg_task` question. Two rulings landing
on one product refuse the *second* — the first stands — because letting the later one win would make
the register depend on row order.

**It never overwrites a ruling in silence.** A changed ruling copies the old row into
`marg_item_discount_history` first, so *"what was it in September"* stays answerable after November
changes it. That is what makes rung 4 — freeze the rate onto the line at the moment of a round —
possible at all.

## Two numbers, deliberately kept apart

**Owner's ruling, 09-Sep-2026: THE STOCK REPORT IS VALUED AT M.R.P.**

So the kit exposes **two** functions and never one with a flag:

- `stock_value_p()` — what a unit **on the shelf** is worth: the printed **M.R.P.**
- `realisable_p()` — what a unit **fetches when sold**: M.R.P. less the owner's ruling.

Using the discounted rate to value stock understates the shelf; using the M.R.P. to value a sale
overstates the takings. Both errors have been made in this estate before, which is why they are two
named functions with two different basis strings, not one number wearing two hats.

## What the walk found — and it answers a question S235 left open

Run against the real 08-Sep database, **93 of 93 rulings placed, 0 refused, 0 unresolved**, and the
register reproduces the S235 close exactly: 66 / 17 / 7 / 3, every discount band to the product.
**Every row's `M.R.P. × (1 − discount)` reproduces the workbook's own "Rate used" to the paisa.**

Then the ruled price was compared with the observed one. **27 of the 93 have any sale history:**

| | |
|---|---|
| observed line price **equals the full printed M.R.P.** | **22 of 27** |
| observed line price equals the **ruled (discounted)** price | **0 of 27** |
| neither | 5 of 27 |

**That is not the counter failing to give the discount. It is where the discount lives.** The
`SALE_BILLWISE DETAIL` export carries the item lines at **GROSS**, and the discount as **one figure
for the whole bill** — the `DISCOUNT` column between `GROSS AMT.` and `NET AMT.`

**Measured across 446 unique bills from 19 archived exports, 17-Aug to 08-Sep.** Six bills in that
window contain nothing but a single ruled appliance, so each is an exact reading of that product:

| bill | product | ruled | actually given |
|---|---|---|---|
| A003160 | BRACE TYLOR UNISON | 30% | **31.89%** |
| A003250 | BRACE TYLOR UNISON | 30% | **29.76%** |
| A003251 | BRACE TYLOR UNISON | 30% | **29.76%** |
| A003181 | LEUKOCREPE 10CM*4IN | 25% | **25.00%** |
| A003278 | ARM SLING M UNISON | 25% | **25.53%** |
| A003136 | LEUKOBAND 4 INCH | M.R.P. | **0.00%** |

**The register describes practice, not intent.** And on mixed bills the arithmetic closes too: of the
four bills in the window carrying a discounted appliance beside medicines, **all four** have a bill
`DISCOUNT` equal to the ruled item discount — three to the rupee, one with a round-off under Rs 20.
A003333's entire bill discount of Rs 153.75 is exactly 25% of the LEUKOCREPE's Rs 615.00.

**So the conclusion is the opposite of a problem with the counter, and it is worth stating plainly:**

> **The bill-level DISCOUNT column is explained by the owner's own rulings plus a round-down to a
> round net. The discount is real, it is given, and it matches the register.**

**The gap is in our ingest, not in the shop.** `sale_line_item` stores the gross item lines and the
bill number; **the bill header's `GROSS / DISCOUNT / NET / CASH` is parsed for the day cash-UPI split
and then not retained per bill.** So the discount exists in the report, is correct, and is thrown
away before anything can attach it to the items on that bill.

**Consequence, and it is money:** every figure that values orthotic sales from the item line is a
**gross** figure. On the discounted appliances that overstates the takings by the ruling — up to 43%
on a 30% product.

`F-385`. **The fix does not need Marg:** store the bill header per bill at ingest, then attribute the
discount using this table. The Marg support request for a true per-item discount column is still
worth sending — it would remove the attribution step and cover products with no ruling — but it is
**no longer a blocker**, and that is a better place to be than where this started.

---

## To run it

Rehearse on a copy — changes nothing:

```
/root/wa/venv/bin/python3 /root/deploy/S236_DISCOUNT/marg_discount.py --db /root/finance/finance.db --dry-run
```

Install:

```
/root/wa/venv/bin/python3 /root/deploy/S236_DISCOUNT/marg_discount.py --db /root/finance/finance.db --install
```

The install takes its own timestamped backup first and prints the one-line `\cp` that undoes it.

Selftests — 37, no database needed:

```
/root/wa/venv/bin/python3 /root/deploy/S236_DISCOUNT/marg_discount.py --selftest
```

---
*S236_DISCOUNT · T1 · 09-Sep-2026. Next rungs: `internal_use` as a third product state everywhere it
matters, the naming validator, and the size-less purchase name flagged rather than assigned.*
