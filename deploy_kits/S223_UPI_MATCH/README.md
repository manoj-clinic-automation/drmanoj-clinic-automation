# S223_UPI_MATCH — the clinic's online money against the bank, as a standing check

**The owner, 04-Sep-2026:** *"The counter is marking mode wrong. A bill paid by UPI gets recorded
as Cash. That would produce exactly this shape — bank always higher, never lower — agree, but
checks are a part of system and a note in report too."*

## The competing explanation was tested, not waved away

Before agreeing, one other candidate had to be killed: **card money hiding inside the feed.**

The ICICI MPR is an **acquirer** file — 22 columns including `Mode of Payment`, `Scheme Name`,
`Card Type`, `Card Number`, `Card Program`. Card *could* be in it. And `finance_upi.py` ends its
mode read with `or "UPI"`, so a card row whose Mode cell was blank would be **silently relabelled
UPI** — the F-278 shape, a default branch swallowing the truth.

Both were checked on the box:

- **all 1,115 ingested transactions read `UPI`** — no card row has ever been stored;
- the **six newest statements were opened directly**: `Mode of Payment: {UPI: 40}`,
  `Scheme Name: {UPI: 40}`, `Card Type: {'': 40}`. **The column is present and populated, so the
  fallback is not firing.**

**There is no card in this feed.** The clinic's POS card takings settle somewhere this box cannot
see. So the exclusion is correct, and the owner's explanation stands as the leading one.

*(And the project had already written his hypothesis down, for the other unit: `finance_upi.py`'s
own header, S179 — "Marg's payment-mode field is unreliable (operator habit: everything rung as
CASH)." He reached the same conclusion about the clinic counter independently.)*

## What the check does

Per day: the Docterz **Online Payment** money — with split bills resolved into their legs — against
`SUM(upi_txn.amount_p)` for `unit='clinic'`. Filed in **`recon_exception`**, kind
**`docterz_vs_upi`** — the table the existing exception screens already read, beside
`upi_vs_statement` and `line_sum_vs_day_total`. No new table, no new screen, no invented vocabulary.

**The two directions mean opposite things and never share a sentence:**

| direction | what it says |
|---|---|
| **bank ABOVE ours** | the expected shape of a bill paid by UPI and rung as CASH. **No money is missing** — that day's declared CASH is overstated by the same amount, and that is what to check at the drawer |
| **ours ABOVE bank** | the uncommon one. A **Razorpay** portal consultation (in Docterz, settles to Yes Bank, never in the MPR), or the day's statement not yet ingested |
| **split legs missing** | overrides both, severity forced to low: part of the gap is a missing INPUT, not missing money. Re-run `push_day_tenders.py` before reading anything into that day |

Severity: high at ₹2,000, medium at ₹500, low below.

**It heals** (F-275). Every run re-decides every day in the window; a day that later agrees is
closed with the reason recorded. Nothing here shouts forever.

**Days after the last statement are not compared at all** and say so — a statement that has not
arrived is not a discrepancy.

## The note that ships with every run

Printed under every report, because it is part of the finding rather than a disclaimer: card is not
in the comparison and why; Razorpay pushes the other way; and **of the clinic's four ways of taking
money — cash, UPI, card, Razorpay — only UPI can be reconciled today.** A check that does not say
so turns its own blind spots into accusations.

## Proven before it ships

Run against a real database built by the real ingester from real workbooks, with both directions
and the heal path exercised: an exception filed at `high` when the bank is above, one filed at
`medium` in the Razorpay direction with the Razorpay wording, one forced to `low` by missing split
legs, and a day made to agree afterwards was **closed with `resolution='the day now agrees with the
bank feed'`**.

A bug the test caught before it shipped: the first draft's wording assumed the bank was always the
higher side, so the uncommon direction would have printed *"bank UPI is Rs -1700 above our lines"* —
nonsense, on exactly the days that matter most.
