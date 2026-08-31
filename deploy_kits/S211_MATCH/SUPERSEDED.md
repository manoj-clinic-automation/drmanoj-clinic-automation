# SUPERSEDED — `finance_returns_audit.py` in this kit

**`deploy_kits/S211_MATCH/finance_returns_audit.py` is superseded by
`deploy_kits/S212_SUMP/finance_returns_audit.py`.** Do not install the copy in
this folder. Nothing here was ever installed — this kit's own README says so —
so nothing live changes by retiring it.

## Why

Two kits offered **different files under one name**, both targeting
`/root/finance/`:

| | bytes | md5 |
|---|---|---|
| `S211_MATCH/finance_returns_audit.py` | 9,930 | `e69d390b…` |
| `S212_SUMP/finance_returns_audit.py` | 20,101 | `a8c4d6f5…` |

That is D202 / F-201 — *no document live and editable in two stores* — applied
to code. The rule exists because the wrong copy is the one that gets installed.

## What the successor fixes

1. **Sourcing.** This version starts from `sale_item WHERE service LIKE
   '%_return'` and so cannot see the **123 orphan line-item returns**. The
   successor takes the UNION of `sale_line_item` and `sale_item`.
2. **`p.mobile`** — a column that exists on the VPS only (D356) and not in
   `finance_schema.sql`. Selecting it makes this file unrunnable anywhere but
   the live box. The successor uses `phone_last4`, present in both and already
   masked at rest.
3. **`s.gross_p`, `s.disc_p`** — also live-box-only, selected here but never
   read. Dropped.
4. **Money.** This version reports no value at all. The successor values every
   return through `finance_money.py`.

## The rest of this kit stands

`finance_item_anomaly.py`, `finance_daily_gaps.py`, `finance_patient_match.py`
and the probes are unaffected and remain current. Only the one file is retired.

⚠ **`finance_item_anomaly.py` carries its own copy of the pack rule**
(`pack_size` / `units`, lines 84–119). It was measured against
`S212_SUMP/finance_money.py` over **every (pack, qty) pair in the owner's
archive — 97 distinct pairs, 1,649 lines — and the two agree on all of them**
(`S212_SUMP/EQUIV_pack.py`). Pointing it at `finance_money` is therefore a
proven no-op, and is to be done **when the anomaly card is built**, not as a
separate change to a file that is currently producing results on the live box.

---
*Written at S212, 31-Aug-2026, before the S212 publish.*
