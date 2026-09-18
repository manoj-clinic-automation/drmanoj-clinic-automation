# S313_SECTION_MAP — one stored answer to "which section is this item in" (F-528)

**Project:** Sanjeevni — Pharmacy & Marg · **Session:** S268 · **18-Sep-2026**
**Rung 1 of** `S268_COUNT2_BY_SECTION_PLAN.md`. **Requires S312_CLAIM_QUEUE live.**

## The one line, after S312's

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S313_SECTION_MAP/install_S313_SECTION_MAP.sh
```

## The page

```
https://followup.dr-manoj.in/finance/stock/page/sections
```

It is not on any tile, on purpose. Nothing in the system reads this table yet, so there is nothing
to go and use it for; it is here to be looked at and corrected *before* anything depends on it.

## What you will see

373 items, split **Medicines 280 · Orthotics 68 · Consumables 25**, and **17 rows where the system's
own rules disagree with each other** — shown first, with the reason spelled out on each line. Three
buttons per row. What you tap is marked as yours and a later re-seed never touches it; what the seed
had said is kept beside it so the disagreement does not disappear from the record.

## Why this is the first rung and not the column

S235 sized "count #2 by section" as one column, `stock_count.section`. The column is the easy part.
Underneath it, four different rules in this codebase answer *which items are orthotics* and give four
different answers — and a monthly orthotics round is a promise that **these** lines were counted and
**those** were not. Until one answer exists and is stored, that promise cannot be kept. The full
ordering, and the five things that will bite on the rungs above this one, are in the plan.

## Files

| file | what |
|---|---|
| `section_map.py` | the table, the seed rule, the dispute view. No route, no blueprint. |
| `patch_sections_s313.py` | `stock_app.py`: one page and two doors, nothing else |
| `stock_sections.html` | the owner's review page |
| `selftest_s313.py` | 35 checks with negative controls, in memory |
| `walk_s313.py` | on a scratch copy of the live database: **the hub is identical on every key** |
| `install_S313_SECTION_MAP.sh` | 7 gates; refuses if S312 is not live, walks, places, reads back, restores |
