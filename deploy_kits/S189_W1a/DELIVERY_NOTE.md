# S189_W1a — F-137: "Where the cash is" reads custody, not movements

**App only. No page, no money, no table. Until `S189_C1a` follows, the card keeps
reading zero — which is exactly what it reads today.**

## The finding, in four lines

```
v_day_cash:    cash_out_p = SUM(cash_movement WHERE direction='out')
v_cash_ledger: closing = cash_in - noncash - expense - cash_out + cash_back + adjust
```

S188 built the card on `cash_movement`. **Every `out` row is subtracted from cash
in hand, whatever the party.** So the only way to make the card speak, as built,
was to book the doctors' holdings as money that had *left* — which would have
taken cash in hand from **₹2,05,198 to about ₹30,000** and destroyed the
agreement the 17 August physical count established.

The endpoint's own docstring stated the wrong reason out loud: *"That is also WHY
the drawer reads over two lakh: the money left the room and never left the
books."* It didn't. The drawer reads over two lakh because that is genuinely the
cash the business holds — **drawer 0, owner ₹18,963, Dr Bhawna ₹1,56,235.**

Your ruling, recorded: **cash held by either doctor is cash in hand, merely
located elsewhere.** So custody is *location* and belongs in
`cash_custody_event`, which no view in the cash ledger reads. S186 built that
table and then wrote the facts into a sentence in `cash_count.explanation`.

## What changes

- the endpoint reads `cash_custody_event`
- **a place is not a person** — `drawer`, `counter` and `bank` go negative by
  construction and are never shown as parked *with* anybody
- the payload carries the physical count the position rests on
- the docstring now records why, so the next person doesn't repeat it

The page is untouched: the new keys are additive, so `finance_entry.html` needs
no change and no page kit is required.

## Six new checks, proving both halves as one sequence

| | ledger | card |
|---|---|---|
| a `cash_custody_event` | **must not move** | **must move** |
| a `cash_movement` out | **must move** | **must not move** |

If those two ever swap again, the suite goes red. The old tests asserted a fixed
store total; the new ones assert **deltas**, because the suite's earlier stages
already write custody rows (F-106).

## Projection, written before measuring

| | before | after |
|---|---|---|
| offline rehearsal | 480 / 482 | **486 / 488** |
| your box | 482 / 482 | **488 / 488** |

Offline **measured 486/488 — held exactly.** The two failures are the same two
before and after, artefacts of the seeded store.

Built on live `16faf98caa720a662316fa235a4b35b9`, ships
`583092c015c37d97fc240d09637b5ea7`.

```
bash /root/deploy/repo/deploy_kits/S189_W1a/install_w1a.sh
```
