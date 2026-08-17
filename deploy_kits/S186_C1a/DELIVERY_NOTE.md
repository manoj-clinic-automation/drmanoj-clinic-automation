# Kit S186_C1a — the Sanjeevni cash close

**Session 186 · 17 Aug 2026 · CHANGES LIVE FINANCIAL BOOKS · gated · backed up · verified · reversible**

## What it does

| | |
|---|---|
| **(A) F-112** | Removes the 13 Aug ₹75,000 bank deposit **that never happened**. The Yes Bank statement for 1 Jul – 17 Aug has its last transaction of any kind on **30 July** — there are no August entries at all. `S184_C1a` booked it as one of "16 verified" credits. Truth: **15 deposits, ₹15,70,600**. |
| **(B) D323** | Parks **₹87,205** of pre-April cash-in-hand as **one** approved, reasoned `cash_adjustment` on the earliest medical day — the schema's own stated "only way the running balance can ever move without a real transaction." |
| **(C)** | Records the 17 Aug physical count, **₹1,75,198**, in `cash_count` — which the schema keeps *out* of the computed ledger forever, on purpose. Evidence, not input. |
| **(D)** | Recomputes the `negative_cash` shouts from the corrected ledger, because nothing else recreates them — only the one-shot importer ever did (the S184 lesson: C1a left the books right and the alarms stale). |

## How ₹87,205 was arrived at

```
physical cash, 17 Aug   0 (Darpan, drawer cleared) + 18,963 (you) + 1,56,235 (Dr Bhawna) = 1,75,198
books once corrected    42,993 + 75,000 (A) − 30,000 (advances, entered through the APP)  =    87,993
PARKED                                                                                     =    87,205
```

Darpan's drawer clearing **proved itself**: copy ₹60,198 − ₹3,926 − ₹7,309 (the two counter-person handovers) = ₹48,963, paid out as ₹10,000 + ₹20,000 + ₹18,963 = ₹48,963 exactly.

## What it deliberately does NOT do

- **`day_line` — the sale money — is never written to.** The gate proves it, by sum and by row count.
- **Darpan's 17 Aug advances (₹10,000 + ₹20,000) are not here.** They are ordinary drawer expenses and belong in the app, through the maker-checker path. A migration is for what the app *cannot* do; using one for ordinary transactions hides them.
- **The ₹18,963 handed to you is not booked as cash-out.** Cash with Dr Bhawna has never been booked out either, so "cash in hand" in these books means the *whole chain*. Booking only this one handover out would make the figure mean two different things on two dates.
- **Nothing about the Staff Ledger.** The ₹70,000 of Darpan advances riding on an unverified claim stays an open check.

## Safety

- **Live-code currency gate (F-97):** refuses unless live `finance_app.py` = `c66bec2b9ea8c11af9c4a4244541e96f` — the pin we completed from the box this session.
- **Precheck refuses before anything is written** unless the phantom deposit is present exactly once, the marker is unset, and no S186 adjustment exists.
- **Whole-database backup** taken before the migration; **verify runs after**, and a red **restores it automatically**.
- The gate asserts **invariants and deltas, never absolute balances** — the F-106 lesson, so a legitimate later correction can never make it fail.

## Rehearsed offline before delivery

Against a throwaway store seeded to the real one's shape (118 days, 16 deposits, closing **₹42,993** exactly):

- precheck **4/4 green**
- verify **14/14 green**
- **idempotent** — applying twice changes nothing
- **rollback lossless** — the store returns byte-identical on every checked measure
- open `negative_cash` shouts fell 34 → 7, recomputed rather than assumed

## After it runs

Cash in hand will read **₹2,05,198**. That still includes the ₹30,000 of 17 Aug advances. Once Darpan's two drawer expenses go in through the app, it becomes **₹1,75,198** — the cash physically counted today.

## Install

```
bash /root/deploy/vps_deploy.sh S186_C1a
```

Send the output back whatever colour it comes out.
