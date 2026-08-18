# S190_E2 — DELIVERY NOTE (D330: the menu · the ceiling · the evidence · the refill)

**Contract:** `claude/S190_Expense_Menu_Redesign_D330.md` (signed S190; supersedes D329 —
nothing of D329 was ever built, so nothing is stranded). One kit instead of the contract's
three, on the owner's "minimum steps" ruling; the E2a→E2b→E2c dependency order survives
INSIDE the kit — identity first, then the ceiling, then evidence — they simply land together.

## Payloads (all built on live bytes recovered by hash, D188)

| file | built on (live pin) | new md5 |
|---|---|---|
| `finance_app_E2.py` | `5cb73ff8…` (S189_E1b) | `02062855ccd97056c2be64ce04d606cb` |
| `finance_ui/finance_entry.html.new` | `1c7d2dc3…` (S189_E1b) | `f819bdf95de14fc331428cf6bea4c37e` |
| `finance_ui/finance_entry_clinic.html.new` | `0c64fda2…` (S182_C2a) | `1c930a3ec71873ce774770dab524ba0e` |

## The projection (written before measuring)

Live smoke **509 → 542, +33 exactly**: −2 (menu labels 5→3) +3 (E1a block: home-details
refusal, uid stored verbatim, server uid minted) +23 (D330 medical: ceiling derived/moves/
refuses/boundary · evidence refused-uploaded-survives-files · advance needs no bill ·
drawings split · page refill/menu/bill-button/reference/retired-heads) +8 (D330 clinic)
+1 (the clinic-day finder check, added during rehearsal and counted honestly here).

## Rehearsed offline on FOUR store shapes (F-140), all 542/542

1. the live shape (Sundays absent · 14/15 Aug drafts · 17 Aug unfiled)
2. **the month already AT its ceiling** — the post-sitting world. This shape caught two
   legacy check groups (F-139, E1a advances) that would have gone red on the live store
   the day after the ₹15,000 sitting; both were made delta-disciplined (the legacy blocks
   raise the ceiling on the THROWAWAY for their own posts and restore it before the
   ceiling's dedicated block).
3. a beyond-window hole 130 days back (the shape that killed E1a at S189)
4. a double run on one store (lazy-DDL idempotency)

## What the offline rehearsal caught before the box could

- **The schema's own CHECK refused `category_fixed='home'`** (only NULL/'salary_advance'
  allowed). The new categories moved to an additive `category_kind` column; the CHECK
  keeps guarding exactly what it always guarded.
- A second CHECK (`category_fixed IS NULL OR staff_id IS NOT NULL`) confirmed an advance
  row cannot exist unattributed — the server-resolved staff_id satisfies it.
- **SQLite rowid reuse**: a rehearsal day cleaned up by deleting only `day_entry` left
  child rows that silently joined the NEXT day created. Both units' selftest cleanups now
  delete children first.

## Schema (all additive, no migration file — DDL authoritative in code)

`day_expense` + `expense_uid` TEXT (the stable row identity that survives the save's
delete-and-reinsert) + `category_kind` TEXT ('home'/'other'). New table
`expense_attachment` keyed (day_entry_id, expense_uid). Settings (created on first read,
defaults in code): `advance.base_p` = 2000000 (₹20,000) · `advance.pct` = 75 → ceiling
₹15,000, floored to ₹100. **Nothing stores the rupee figure** (F-136). A salary revision
is one settings row.

## Known and stated

- **Old cached pages** keep working (uid + category absent → old path); their rows carry
  no kind, so the evidence gate does not reach them — the E1b precedent, converges on
  refresh.
- The evidence gate runs at **File**, never Save (a bill can only attach to a saved day);
  **no escape hatch** (owner ruling). Salary advances need no bill.
- The scan widget's file input was **verified on the box** (owner-run grep, S190): no
  `capture` attribute → phone offers camera AND gallery. Upload of yesterday's photo is
  the primary flow.
- `saveThenScan`'s "same figures" note now actually holds: the page refills everything,
  so the draft save on the way to the scanner carries the day's true contents.

## Install

```
cd /root/deploy/repo && git pull
bash /root/deploy/repo/deploy_kits/S190_E2/install_e2.sh
```

**Kit v2 (same payloads, two corrections).** The first kit's currency gate carried a
clinic-page hash whose tail was written from a truncated record prefix — a full value no
file has ever had (the F-109/F-116 shape). The gate refused it against the true live
`0c64fda2005e…`, proving the chain; the payloads were verified built on those exact live
bytes and are UNCHANGED. This note's install path was also wrong (`/root/deploy` for
`/root/deploy/repo`) — written from memory, not the record: the F-135 shape. Both owned
in the session log.
Expect: currency gate PASS (3 files) → old smoke 509/509 → staged 542/542 (+33) →
swap → live 542/542. Any deviation restores byte-perfect and prints why.

## After install (the sitting, Part A)

17 Aug on the new menu: ₹15,000 → *My salary advance* (the inline line will read
"Taken this month 0.00 of 15,000.00 max") · ₹5,000 → cash movement out/other with the
reference line · scans → Save → check → File. Proof line stage 1: **₹1,85,198.00**.
The ₹10,000 belongs to 31 July (Part B) — safe to enter after THIS kit is live, because
re-opening 31 July now refills everything it holds.
