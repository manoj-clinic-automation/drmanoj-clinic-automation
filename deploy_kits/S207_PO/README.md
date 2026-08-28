# S207_PO — the purchase order generator

**Staged. It writes a plan and a page. It sends nothing — a person sends orders.**

Implements the cadence **approved at S206**, not a new one: weekly ≥ ₹20,000/month · fortnightly
≥ ₹4,000 · monthly below, **ceiling never floor** so no vendor's ordering gets *more* frequent.
Cover = cadence + 2 days lead + 3 days safety, +3 more where only one stockist carries the item.
Quantities round **up to whole strips**, because that is how they are ordered and how they arrive.

## The rails — every one is a way to buy dead stock

*"be careful of order quantities … we can hold limited inventory in our small pharmacy"*

An order is `(rate × cover) − on hand`. **Both terms can lie.**

| rail | what it stops |
|---|---|
| **thin rate** — under 5 selling days in 133 | twelve days of "cover" computed from three sales |
| **spike** — one day carrying ≥40% of the year | one bulk sale to one customer reading as a daily rate |
| **big line** — over ₹5,000 | a single quantity nobody agreed to |
| **dead** — unsold 60 days | reordering what already isn't moving |
| **trivial** — under ₹50 and in stock | a line that costs more to handle than it is worth |
| **run cap** | the cadence is right and the total is still a decision |

A rail never silently drops a line: it either **asks**, with the reason printed, or it says why it
skipped. 13 lines are asking today.

**One rail is documented as dead.** `MAX_COVER_DAYS = 45` cannot bind under the approved tiers — the
longest reachable cover is 38 — and the selftest **asserts that it does not**. A rail that silently
cannot fire is worse than no rail, because it is believed.

## Three parser bugs, each of which produced a plausible plan that was wrong

None raised an error. Each made `TYRO BR` **32.6 a day instead of 112.6** — an order for 12 strips
where 98 were needed.

1. **Matching truncated sale names against full item-master names.** The sale report cuts at 20
   characters, so a third of the shop was invisible to the plan and nothing said so. `resolve.py`
   already solved this; it just had to be used.
2. **A hand-written `strips × size + loose` reader.** That is exactly the fault the reconciliation
   exists because of — a tube, vial or spray writes `1.0`, not `0:1`, and a reader that only knows
   the first returns **nothing** for the second. 2,807 lines, 16.3% of the year.
3. **Converting a `packs:loose` pair with a map-wide pack size** instead of the packing printed on
   that row. `s2_ledger` states the rule outright: *"Marg printed that pair against that packing;
   using a different one changes the answer by a multiple."*

**The only thing that caught them was comparing against numbers measured independently at S206.**
So those numbers are now the regression test.

## Proven

```
po_engine.py --selftest      25 checks, no data needed
selftest_po_build.py         18 checks against the real archive

  TYRO BR 112.6/day · PATOPAN DSR 66.7 · MEG QCS 63.1
  FLUXIC P 28.6 · ORICOX P 71.3 · BIO D3 MAX 36.5     all match S206 to 0.1
  17 vendors with something to order                  matches S206
```

## Today's plan, at a ₹60,000 cap

**17 stockists · 42 lines · ₹57,342 at cost.** 13 more lines are asking (₹6,230). **38 items sold
with no stockist on record** — nothing can order those until a supplier is named against them, and
they are listed rather than dropped.

Each vendor card has **Copy this order** — one WhatsApp message, against the 9.4 separate bills a
month the largest vendor sends today.

## What the stockist could not supply

Each order line carries three buttons: **ordered · out of stock · part**. An item the stockist
cannot send is the commonest cause of a stockout, and until now it lived in somebody's head until
the goods failed to arrive.

- **out of stock** strikes the line through and drops it from the copied message
- **part** takes the number actually promised, and the message carries *that* instead of what was asked
- both land in **"Could not be supplied — needs another stockist"**, which is the list the next
  order works from

Counts live on the phone and move to everyone else only when somebody taps **Share** — the same
two-copy design as the count sheet, so nothing is lost to a reload, a conflict or a flat battery.
Opened as a plain file with no capability the button reads *"On this phone only"* and recording
still works.

**No prices anywhere on this page**, deliberately. Quantities are what the counter and the stockist
need; cost is not printed where staff work. The engine keeps its thresholds and the page says *"a
large line"* instead of naming one.

**`have` and `order` are both in strips** — `42+2` is forty-two strips and two loose, the same way
the shelf is counted. The first version printed a bare unit count beside an order in strips: one row,
two units, neither labelled.

## "Who sends us this?" — the shop knows what the data cannot

**38 items sell and nothing in the last five months says who supplies them.** They were bought
before 1-Apr-2026, or under another item code. I checked every item export on the machine — none
carries Marg's Company field, so it cannot be derived; it can only be **asked**.

**Then the LIST OF ITEMS export arrived, and it changes the answer.** Marg's column — spelled
`Compnay` — holds the **manufacturer**: CADILA, VINTECH, ACCUSURE, TYNOR. That is *not* the stockist.
CADILA makes ACILOC 300; KEDAR PHARMACEUTICAL is who the shop buys it from. Putting one in the other's
place would send a purchase order to a factory.

**But distributors carry particular companies**, so the shop's own buying history turns one into the
other. For every item whose stockist *is* known, note its company. KEDAR supplies **135** HI CURE
items — so a HI CURE item with no purchase history is very probably KEDAR.

**All 38 have a company. 32 get a suggested stockist**, each carrying the evidence behind it:

```
likely   17   ten or more of that company's items come from them
possible 12   three to nine
weak      3   one or two — shown, and it says so
none      6   nothing has ever been bought from that company at all
```

So each row now offers a guess to **tap**, not a blank to fill. Type over it when it is wrong.
**Out of stock first**, because there the missing name is already costing a sale.
`NIPRO 3 ML DISPO SYRINGE` leads it at −83, and `FLUPIVAMP 100` — 403 sold, none left — comes with
SHIVAAZ offered on the strength of 76 other KIRTI items.

A name typed once is shared like everything else, and from then on the item can enter the ordering
plan on its own. Nobody has to remember, and nobody has to be asked twice.

**Note the syringe while you are there.** `DISPO SYRINGE NIPRO 3ML` holds **199** and
`NIPRO 3 ML DISPO SYRINGE` holds **−83** — the same product under two item codes, one carrying the
stock and the purchases, the other going negative as it sells. Merging them in Marg fixes the item
and the supplier question together.

## Still open, from S206 §7 — none of it blocks running the plan in shadow

1. Approve the tiering. 2. Name a supplier for the orphan items. 3. Decide the catch-up: all at
once, or the urgent lines first. 4. Pick a day of the week per vendor — *"weekly" is not a schedule
until it says Tuesday.* 5. **The vendor sheet: lead time is the last placeholder in the whole model.**

**Run it in shadow beside your current ordering for a fortnight before anything is sent.**

*S207_PO · staged 28-Aug-2026 · nothing sent, nothing live touched.*

## Stockist phone numbers

Nineteen numbers came from the sheet Shavez filled in and are **built into the page**, so the
Call button is already live for twelve of the fifteen vendors in the current order — nobody
types a number to place a normal order.

The box under each vendor stays, for two reasons: a number that changes can be corrected in
place, and the three vendors below still have none. A number typed there **wins over the
built-in one** and travels with Share, so a correction reaches everyone once.

Still without a number, from Marg's own party list:

    MANNAT PHARMA · RAVI MEDICAL AGENCY · ESSENTIAL PHARMA BAREILLY
    KUSHAGRA MEDICAL AGENCY · SEHGAL MEDICOSE BAREILLY

One match was a judgement call rather than an exact name match and should be confirmed before
it is trusted: the sheet's **SCIENTIFIC MEDICOS** was matched to Marg's **SCIENTIFIC&MEDICAL AID
CENTRE BAREILLY** on similarity alone (0.57). If that is a different firm, correct it in the box
on the page and the built-in number is overridden.

The numbers are supplier business numbers held in `stockist_phones.json` in this kit. No patient
number is anywhere in this kit.

### The bug this seeding uncovered

The Call button was emitted as `class="call hide"` while the script revealed it by adding
`class="on"`. `.hide{display:none !important}` beat `.call.on{display:flex}`, so twelve numbers
sat correctly in the HTML and not one button appeared — no console error, nothing to notice.
`selftest_po_build.py` §5 now fails if anything is emitted wearing an `!important`-hidden class
the script later tries to switch on. The check was confirmed to go red on the real bug before
the fix was kept.
