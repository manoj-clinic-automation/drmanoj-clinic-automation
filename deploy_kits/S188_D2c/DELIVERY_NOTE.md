# S188_D2c — F-132: what Darpan may see, and F-133: what nobody has been recording

**Session 188 · 18 Aug 2026 · built on the bytes D2b installed, rehearsed offline.**

## F-132 — the claim I never tested

When D2a closed **F-127** I gated three routes. For `/finance/api/day/<date>` I wrote — in the kit,
in the Register, and to the owner — *"payload unchanged, because it was already correctly scoped."*
**That claim was never tested, and it was wrong.**

`opening_p` comes from `v_cash_ledger`, whose window is:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
```

**Unbounded preceding** — a running total of every day since the books began. So the field the
maker's page labelled **"Opening cash · carried from the last filed day"** was the **entire unit
cash position**, rendered in 24px bold, with "Closing cash" below it in 30px.

**Worse than the disclosure: it was not true of him.** Most of that balance is parked with Dr
Bhawna (D323) and ₹87,205 of it is a pre-April adjustment (S186). A label reading "carried forward"
invited him to believe the drawer held two lakh rupees. That half predates F-127 entirely — it has
been on his page since **S179**.

**Removed:** from the page, from `/finance/api/day/<date>` for a maker, from the **save response**
(the same leak through a third door), and from the D2 mirror. The checker's payloads are unchanged.

**Nothing is weakened.** The carry-forward is safe because it is **computed on the server and never
accepted from a client** — that is what made the 36 legacy breaks impossible, not the display. The
client's "would this go negative" courtesy check goes with it; the server has always refused a
negative save with `negative_cash` and said why, and it still does.

## F-133 — the feature already exists and has never once been used

The owner asked that Darpan see money parked with him and Dr Bhawna. **I surveyed the box before
building it**, and the survey is the finding:

```
cash_movement, all time, medical:
   bank   out   n=15   Rs 15,70,600.00
   (no other rows at all)
last bank deposit : 2026-07-30, Rs 85,000   → 19 days ago (threshold 7)
custody events    : 0
```

**Not one recorded handover to either doctor. Ever.** Had this been built without looking, the page
would today have shown `Dr Manoj ₹0 · Dr Bhawna ₹0` — stated confidently, in the clinic's own
software, while roughly two lakh sits with one of them. A worse lie than the one being removed.

**And it explains the ₹2,05,198.** The money physically left the drawer; in the books it never did.
S184/S186 recorded *"cash parked with Dr Bhawna"* as **exception text**, not as **cash movements**,
so the ledger has counted parked money as in-hand ever since. The entry has existed on this very
page since S179 — *"Cash out / cash back — Bank, Dr Manoj, Dr Bhawna"*. Fifteen bank deposits went
in; not a single handover did. **The gap is practice, not code.**

## What the page now shows

A **"Where the cash is"** card, from real data only:

- **Parked with Dr Manoj / Dr Bhawna** — a **total line that expands to the two names
  individually** (the owner's shape), **current financial year only** (from 1 April; last year's
  handovers are last year's problem and would otherwise grow forever).
- **Days since the last bank trip** — today **19 days**, last 30 Jul ₹85,000, against a threshold
  of 7. Badged red. Deliberately **not** FY-scoped: "days since" must survive an April boundary.
- **When parked reads zero it is written as an instruction, not a fact:** *"Nothing has been
  recorded — not once. If cash has gone to Dr Manoj or Dr Bhawna, enter it under Cash out / cash
  back below. Until it is entered, the books count that money as still sitting in the drawer."*

That last line is the point. It turns a false zero into the thing that makes the data start
existing, and it tells him plainly why the drawer figure drifts.

## Evidence

**Smoke: 464/464 → 476/478 offline (+14 checks, zero new failures** — the same two seeded-data
artefacts). Live projection **478/478**.

The new tests assert the F-79 **absence** half as well as the presence half: no `cash_in_hand`, no
`month_to_date`, no other day's money on the new surface; a maker's day payload carries no
`opening_p`/`closing_p` while the checker's still does; and the **financial-year boundary is proven
with a real row** — a ₹12,345 handover dated before 1 April is excluded, the identical movement
inside the year is counted, both then cleaned up.

Six existing assertions were **deliberately inverted or re-pointed** (the entry page's
opening-field checks, the id-preservation list, and two ledger-arithmetic reads now taken through
the checker). Changed knowingly, and re-rehearsed against the state that broke them (F-125).

**F-87 differential — verdict CLEAN.** Removed: `opening`, `closing`, `closingBox` — all three
declared. Added: `whereBody`, `s-where`, `/where-is-the-cash`. **All 11 POSTed payload keys
untouched** — the server's contract with this page is byte-identical; only what the page is *told*
has narrowed.

`bash -n` clean. Currency gate demands `finance_app.py 3a7086f8…` and
`finance_entry.html 2c23b461…`.

## Install

```
bash /root/deploy/vps_deploy.sh S188_D2c
```

Then pin from the box (D321(d)):

- `finance_app.py` → `f06e139b7651329a72b08bbc5779077f`
- `finance_ui/finance_entry.html` → `d3844bb96a1d496e5882cfbbb695cbf4`

## The bigger question this raises, which is not a kit

**Roughly ₹2 lakh of handovers were never booked.** That is a question about your books, not about
Darpan's screen — the ledger's "cash in hand" is overstated by whatever is actually with you and Dr
Bhawna, and no record exists to net it down. F-133 records the gap. Closing it needs either the
handovers entered retrospectively, or a counted reconciliation like the one S186 did for the drawer.
