# S212_SUMP — sale returns on the panel, sourced from the item lines

**Built and proven offline at Session 212, 31-Aug-2026. Not yet deployed.**

> *"it is the sump which NEEDS TO BE ON CONSTANT RADAR."* — the owner

## What was wrong

`finance_returns_audit.returns_for_day()` started from
`sale_item WHERE service LIKE '%_return'`. That is **one of two places a return
lives**. Starting there missed **123 orphan line-item returns** — almost all
April–June, the `S186-F104` backfill era. A sump card that under-reports is the
one thing it must never be.

## What it does now

The day's returns are the **UNION of both sources**, because neither alone is
complete:

| source | what it is |
|---|---|
| `sale_line_item` where `is_return=1` | the item spine |
| `sale_item` where service `%_return` | the money spine |

That gives **three populations**, and the card names all three rather than
quietly averaging them:

| population | meaning |
|---|---|
| **audited** | lines *and* a bill row — fully checkable |
| **orphan** | lines but **no** bill row — the 123. Real money the old card could not see at all |
| **no item detail** | a bill row but **no** lines — S211 measured 116. Not a clean return, an **unexaminable** one, and reported as such |

## The money

Every rupee comes through `finance_money.py`, which is the **only** place a rate
becomes money. `amount_p` on a **line** is the **rate per pack**; summing it
directly is what produced the two figures withdrawn at S211 (₹1,33,514 and
₹38,157). `amount_p` on a **bill row** *is* money. They are never added together.

Both figures are carried per return:

- **gross** — what the returned goods were worth, from the lines
- **net** — what actually left the drawer, from the bill row

The headline is **net where it exists**, gross for an orphan (which has no bill
row and therefore no net). The gap between them is carried as
`refund_shortfall_p` and becomes a **DISCOUNTED RETURN** verdict when it is
material (≥ ₹10, or ≥ 2% of gross) — so a discount on a refund is flagged, never
netted away.

`sale_line_item` declares `CHECK (amount_p >= 0)`. **A return can never be
negative here. Direction comes from `is_return`, never from the sign** (D314).

## What the walk found that the gates did not

`WALK_sump.py` builds a real database from the real schema, loads the real Marg
archive, manufactures both awkward populations and runs the real function.
It found three defects that `py_compile` and an md5 gate cannot:

1. **`p.mobile` does not exist in `finance_schema.sql`.** It was added on the VPS
   only, for D356. The inherited query selected it, which made this file
   unrunnable anywhere but the live box. Now uses `phone_last4`, which exists in
   both and is already masked at rest.
2. **`s.gross_p` and `s.disc_p` do not exist in `finance_schema.sql`** either —
   live-box-only columns, selected but never read. Dropped.
3. **The pack string `1*10.` — with a trailing dot.** Two items in the Marg
   master carry one: **`FEBUWISE 40`** and **`PRETOL 8`**. A strict pack parser
   refuses it, silently dropping 6 lines and breaking **6 of 374** bills. Now
   tolerated — and only a *trailing* dot, so `1*10.5` is still refused rather
   than quietly read as a 10-pack. **Worth fixing in Marg's item master too.**

## Proof

`REHEARSAL_sump.py` re-measures the S211 money model with this implementation:

| | this kit | S211 measured |
|---|---|---|
| bills with item lines | 374 | 374 |
| of which credit notes | 29 | 29 |
| **gross reproduced exactly** | **373** | **373** |
| did not reconcile | 1 | 1 |

The one that does not reconcile is **`A001547`, 12-June, 8 lines** — the same
bill, with the same shortfall, that S211 recorded. Reproducing a measurement
*including its single failure* is the evidence that this is the same model and
not a lookalike.

`WALK_sump.py` — six checks, all clear, money reconciling to the paisa.

## Run it offline (nothing here needs the VPS)

```
python D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S212_SUMP\REHEARSAL_sump.py D:\dr-manoj-git\drmanoj-clinic-automation\finance D:\Downloads\margsync\MargArchive\SALE_BILLWISE
```

```
python D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S212_SUMP\WALK_sump.py D:\dr-manoj-git\drmanoj-clinic-automation\finance D:\Downloads\margsync\MargArchive\SALE_BILLWISE
```

## Deploy — ONE line, after the publish

```
cd /root/deploy/repo && git pull && \cp deploy_kits/S212_SUMP/finance_money.py deploy_kits/S212_SUMP/finance_returns_audit.py /root/finance/ && /root/wa/venv/bin/python3 -c "import sys;sys.path.insert(0,'/root/finance');import sqlite3,finance_returns_audit as R;c=sqlite3.connect('file:/root/finance/finance.db?mode=ro',uri=True);c.row_factory=sqlite3.Row;rows,s=R.returns_for_range(c,'2026-04-01','2026-08-29');print('returns',s['count'],'value',s['value'],'days',s['days']);print({k:v for k,v in s['tally'].items()})"
```

**Expected:** a count well above what the old card would show, the orphan
population non-zero and close to 123, and no crash.

## THE OWNER'S DUPLICATION CHALLENGE — checked, and he was half right

He asked whether this duplicates the S206 Marg purchase-ingestion and stock
system he built and verified against real 26/27-Aug stock. **It does not** — but
the check found something worse than the thing he was worried about.

**Not duplication.** S206 runs on the **PC**, reads `MargArchive` exports, and
answers *"did the goods come back to the shelf"* in **units of stock**. S212
runs on the **VPS**, reads `finance.db`, and answers *"how much cash left the
drawer, for which patient, was the refund discounted"* in **paise**. Neither
reads the other's source; neither writes where the other writes; **no S206
module has ever been on the VPS.** `S206_SANJEEVNI_RECONCILE/s13_money.py`
divides a purchase line's net by base units for *cost per unit* — the opposite
direction from this file.

**But: S206 ALREADY HAD THE MONEY MODEL, and S211 re-derived it.**

    S206  load_fy.py:87       "rate_p": ps.get("amount_p")     <- renamed at ingest
    S206  build_report.py:18  un(s) * rate_p / 100.0 / n
    S206  build_report.py:72  "Sale value is units x MRP / pack size,
                               which reproduces whole bills to the paisa."
    S206  verify.py:26        "The sale line carries MRP PER PACK"

`un(s) = strips*n + loose`, so S206's `un*rate/n` is **algebraically identical**
to `line_amount_p` here. S206 named the column `rate_p` **at the door** — which
is precisely the mistake that produced the two figures withdrawn at S211
(₹1,33,514 and ₹38,157, both from summing `amount_p` as money). **The answer was
already in the repository.** S211's 374-bill proof was sound work, but it proved
something S206 had already written down and used.

**The real debt: the pack rule is written SEVEN times** — `units.py:52`,
`packmap.py:38`, `marg_stock.py:33`, `build_report.py:14`,
`S207_STOCK_CHECK/build_stock_check.py:22` (which declares the duplication in
its own docstring), `finance_item_anomaly.py:91`, and this file. Four of them
disagree on edge cases. **Measured against the owner's actual data: none of the
disagreements can fire.** Every pack string in the sale archive has outer = 1,
so `packmap`'s `outer x inner` never diverges from `units.py`'s `inner`; and no
pack of the form `N*M.5` exists, so the unanchored regexes never misread one.
**His S206 system is not wrong. Do not touch it.**

**What is being done about it, and what is not.** `finance_money.py` is the
single pack/money rule **for the VPS lane only** — the two lanes never ship to
the same machine, and `packmap.py` is load-bearing for a different return
convention. It now exposes both views over one parser: `units()` in packs for
money, `base_units()` in tablets for quantity comparison. `finance_item_anomaly.py`
will import it **when the anomaly card is built** — proven safe by
`EQUIV_pack.py` (97 distinct pack/qty pairs, 1,649 lines, zero disagreement),
but not changed today, because it is live and producing results.

## NOT in this kit

The **API pass-through** (`patch_finance_app_panel.py` drops `returns=` and
`payment=` at the `jsonify`) and the **card itself**. Those are the next two
steps and are deliberately separate — the owner's ruling is ONE card, collapsed,
expandable, no links, all data on the page, and no duplication of what the
console already shows.

---
*S212 · built offline against the owner's own Marg archive · no VPS query was
used to build or prove it.*
