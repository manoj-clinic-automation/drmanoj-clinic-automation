# S235_DERIVE — the derivation pass

**08-Sep-2026.** One file. **Nothing existing is altered, renamed or dropped** — this adds
**two** new tables and fills them. Every screen keeps working exactly as it does today, because
**nothing reads these tables yet.**

This is step 2+3 of the consolidation, clubbed, as agreed.

---

## Why

Measured on the 08-Sep 01:05 database, before a line of this was written:

- **Every number on every stock, purchase and sale screen is recomputed from scratch each time
  somebody opens the page.** Nothing is stored anywhere. So no two screens can be *guaranteed*
  to agree, and nobody can ask what coverage looked like last month.
- **Completeness is prose.** Twenty separate hand-written phrases across the stock screens alone
  — *"no MRP on record"*, *"at cost, for reference"*, *"N unpriced"*, *"no price"* — each written
  by a different hand at a different time. **Exactly one place in the whole estate stores a
  completeness count as data**, and it is the frozen loss sheet handed to Darpan.
- **Pricing by raw item name reaches 221 of 373 shelf products. Pricing through the item spine
  reaches 227** — and moves **8 products off an ESTIMATED price onto a real observed one.**

## The one rule

> **A figure that cannot see everything says so in a FIELD, not in a footnote a person has to
> remember. A figure that CAN see everything leaves the coverage columns empty rather than
> inventing a denominator.**

Every row carries `denom_n` (what it should have covered), `covered_n` (what it did),
`uncovered_n`, and where money is knowable, `uncovered_p` — the money it could not reach. Plus
`basis`, in plain words, and `source`, the tables it rests on.

## What it holds

**`marg_figure`** — one row per derived figure, keyed `(scope, scope_key, figure)`.
**`marg_derive_run`** — one row per pass, so any figure can say which run produced it.

On the 08-Sep data it writes **422 figures**: one price per product (374), ten estate figures,
and five per month across six months.

| figure | on 08-Sep |
|---|---|
| `items_on_shelf` | **373 products**, from 373 snapshot rows |
| `items_priced` | **227 of 373** — 146 products no price can reach |
| `items_priced_observed` / `_manual` / `_estimated` | 191 / 0 / 36 |
| `shelf_value_mrp_p` | **Rs 5,12,147.29**, covering 227 of 373 |
| `below_zero_items` / `below_zero_value_p` | **12 products · Rs 98,503.63** — D398, with a rupee figure at last |
| `shelf_name_collisions` · `merge_faults` · `typed_prices` · `sale_lines_undated` | 0 · 0 · 0 · 0 |
| `sale_value_mrp_p`, `sale_value_tied_p`, `sale_lines`, `sale_return_value_p`, `sale_return_lines`, `orthotics_value_p` | per month, six months |

**Derived only.** A person's decision — a write-off, a cause, a count, a typed salt — never lands
here. A self-test asserts the table has no column one could land in.

## What it is NOT allowed to do, and each is tested

1. Write to, alter or drop any pre-existing table.
2. Guess. An unreadable quantity is counted **once** and disclosed; a line with no price at all is
   money we cannot see, disclosed, never absorbed as zero.
3. Net a below-zero quantity into the shelf. **Stock recorded below zero is a data fault, not
   negative value** — on this data twelve products worth Rs 98,503.63 would have come off the
   shelf total, invisibly. The sign is a property of the **row**, tested before anything is summed.
4. Let a figure outlive the data it came from. Every pass **sweeps** what it did not write.
5. Disagree with itself. Running it twice gives byte-identical values.

## What five rounds of adversarial review found

An independent agent attacked it against the real database, five times. **Thirty-two defects**,
every one fixed and every one now carrying a test named after the fault:

- **v1, 15 findings, one CRITICAL:** figures were never swept, so deleting a month's data left its
  money standing under the next run's header — a shelf that no longer existed still showed
  Rs 5.12 lakh. Also: return lines charged against a non-return figure; a breakdown count
  rendering as "361 uncovered"; the estate keyed on the raw name rather than the product, so two
  spellings would have double-counted.
- **v2, 7 findings:** a **negative typed MRP** would have taken a fifth of the shelf off the total
  *while the coverage count went up*; a merge pointing at a missing product silently vaporised a
  real price and then said the product could not be priced at all.
- **v3, 8 findings, one SERIOUS:** one settings row reading *"twenty percent"* killed the entire
  pass with a traceback before a single figure was written — while every live screen carried on.
- **v4, 2 findings, one live:** the below-zero rewrite made a product that was *both* unpriced and
  below zero count as two gaps instead of one. The rupee total was right; the coverage was wrong
  on the real data, and it had been right in three earlier versions.

**The lesson, again: a green self-test suite proves the cases its author thought of.** Every
fixture in this file was written by the file's own author, which is exactly how a defect survived
24 of them at S234.

## Proof

- **86 self-tests, 0 failures** — offline, no database needed.
- **`py_compile` clean** (to a temp `cfile`, so no `.pyc` is left behind).
- **Idempotent on the real database**: built repeatedly, byte-identical across every value column.
- **Touches nothing else**: the contents of all 128 pre-existing tables hashed before and after
  three builds — only SQLite's own `sqlite_sequence` moves, which an AUTOINCREMENT table forces.
- **Reconciles with S229 exactly**: computed the same way, 17,792 lines / **Rs 32,71,053.06** tied
  and 56 lines / **Rs 68,806.00** ambiguous — to the paisa.
- **Every money figure independently recomputed** by the reviewer from the raw sale lines, all six
  months, agreeing to the paisa.
- **Rolls back whole**: a failure partway leaves no run row, no figures, no half-swept table.

## Prove it yourself

```
python marg_derive.py --selftest
```

Then, against a copy — this never opens the real database for writing:

```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S235_DERIVE/marg_derive.py --db /root/finance/finance.db --dry-run
```

## Install — ONE line, and it gates itself

After the publish, on the VPS. First the clone:

```
cd /root/deploy/repo && git pull
```

Then the whole thing, in one line. It runs the 86 self-tests, rehearses the entire pass on a
**copy**, takes a consistent, timestamped backup of the database, and only then builds — stopping
at the first doubt and touching nothing if anything fails:

```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S235_DERIVE/marg_derive.py --db /root/finance/finance.db --install
```

It prints `1/4 … 4/4` and either `DONE` or `REFUSING: … Nothing was touched.` The undo line it
prints at the end restores the database exactly.

**No service restart is needed. Nothing reads these tables yet, so no screen can change.**

**It depends on `S229_ITEM_SPINE` sitting beside it in the same deploy clone** — the spine is
imported, never copied, so there is exactly one implementation of *"how many packs did this line
move"* in the estate. If it is not there the pass refuses and says so.

## Verify this kit

Run from INSIDE this folder — its rows are rooted here:

```
md5sum -c KIT_MANIFEST.md5
```

---

## One thing it found on the way, which is not about this kit

**F-379 — the Orthotics "Amount" column on `/finance/approvals` is understated.** It sums the pack
price once per line regardless of packs sold, so a belt sold 3 packs at Rs 450 contributes Rs 450,
not Rs 1,350. Measured: **Rs 1,01,167.74 shown against Rs 1,04,917.74 true — understated by
Rs 3,750, about 3.7%.** It is a floor labelled as a total. `orthotics_value_p` in this kit is the
correct figure; **the live page is deliberately NOT patched here**, so the fix happens once, in one
place, when a screen is pointed at this table.
