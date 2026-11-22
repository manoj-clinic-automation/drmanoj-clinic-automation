# S932_ORTHO_ORDER_NAMES — an orthotic order line carries Marg's CURRENT name (F-1579)

Kit S932, 22-Nov-2026, Sanjeevni session 503 (Fable). Owner's words: the stock plan (D1037, S501_STOCK_PAGES_CONSOLIDATION → v2) and
S502's finding: the ordering lane keys the 22 ticked orthotic renames by their OLD names — ANKLE BINDER BAMBOO M was ordered under the
count's spelling three times, and each order under a name Marg no longer prints left Darpan's kept 'yes' row standing (ordered again).

## What changes
- `/root/finance/order_sheet.py` 85ce2148 → TO (make_s932.py, 2 exact anchors + one block before `_s605_ordered_since`):
  `_s932_map` ({old: new}, EXACT names only — never a clip, since orthotic sizes share their 20-letter clip; a chain X→Y→Z folds nothing on Y), `_s932_marg_name` (pad_norm-tolerant; the name itself otherwise) and `_s932_forms` (the two exact spellings);
  `entries()` writes the kept ortho line under Marg's current name (the duplicate check and reception's quantity edit read both names);
  `_s605_ordered_since` finds an order under either name — so a line ordered under the new name clears the kept row (no third order).
- `/root/finance/porders.py` ea014fbd (S925's TO) → TO (1 anchor): `_on_order` folds a line under a ticked NEW name back to the lane's own key by the
  same exact map (never item_alias.resolve, whose clipped forms would fold a never-renamed sibling), so the shortage picture counts it.
- The lane's own keys (porder_keep, the section map, Darpan's yes rows) stay as they are: only what LEAVES the lane carries the new name.
- A planned (unticked) rename changes nothing; a name with no rename is untouched. Fail-soft: item_alias unreachable → the name itself.

## Proof
`walk_s932.py <dir> <COPY of finance.db> [--control]` — a scratch database with the copy's schema only (no rows; no patient data),
one ticked rename (W932 BINDER M → W932 BINDER BAMBOO M), one planned, a chain, Darpan's yes rows, the vendor's sent order: 18 checks (the name doors,
the card line under the new name with the yes row's quantity, edits under either name, the kept row cleared by an order under the new
name, ordered_since both names and not before the yes, porders' fold, the plain item untouched, the empty card after both are ordered).
The control (the live files) goes red on 13 — T7 is the live fault itself (the kept row survives the order). The purchase flow's own
proofs S920–S926 run old vs new on copies of the live database: never worse (the S837 rule; a count inside a red label is not a new red —
walk_s924's state-bound 'every other line unchanged (N)' is red on both, and N moves by one because the fix itself moves the Needs-you:
on the 22-Nov copy 'Orthotic shortages: 10 items' reads 8, and KNEE SUPPORT HINGED XL's 'stock figure −1, not offered' line goes — the
item is on an order placed under its new name, so it is no longer a shortage; its −1 shelf still shows on the Stock check page). Installer: SUMS · KIT_ID · TO pins · FROM
pins · compiles on both pythons · the walk + control · S920–S926 not worse · place · restart · healthz 200 · the flow page and the
porders summary door (302 login-gated is fine, F-1439) · the service log clean; red → everything back. `undo_s932.sh` — the two files back.

Cold review: NOT SAFE (1 MUST: the fold by item_alias.resolve would have folded a never-renamed sibling sharing the 20-letter clip onto
the renamed one's key) → exact map + the chain guard + exact forms + pad_norm match built in (T8c–T8f) → second look.

Install: one server line (the installer's header). After S928 and S930 or before them — independent files.
