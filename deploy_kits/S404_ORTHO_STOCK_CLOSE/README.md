# S404_ORTHO_STOCK_CLOSE — close the orthotic section of the 06-Sep stock check

**Sanjeevni project · session 283 · 26-Sep-2026 · decisions D619, D620 (the owner's words, 26-Sep).**

## What the owner asked for
"I want to close the stock check for the orthotic section first. For that, I need Darpan to have an interactive tool
where he can do the matches and whatever you have made on my page. So he gets to do it either on his mobile or on his PC.
And then Amir changes the names as you have suggested. All this happens today and tomorrow." Staff flow: taps, no typing.

## What was built
**NEW `/root/finance/stockmatch.py` + `stockmatch.html`** — Darpan's **Stock milaan** (Hindi, Roman script, phone-first,
works on the PC) at `https://followup.dr-manoj.in/finance/stockmatch`, tile **"Stock milaan"** (portal, granted to darpan;
the doctor by role). Its own server unit `stockmatch` (darpan maker, manoj checker, nobody else). Orthotics only, round 1 only.
- **Card 1 — Adla-badli? (N):** every step-2 pair of the round whose two items are orthotics and whose answer is still empty:
  short item · extra item · qty · **Haan** (billed as the other size — a swap) · **Nahi**. Lands through the same door the owner's
  Yes lands (`stock_app.match_answer` → `stock_match`, by_user darpan). A pair the owner answered is greyed with his answer and
  read-only to him; a second tap on an answered pair is refused.
- **Card 2 — Kam kyun? (N):** every open orthotic line left after the swaps: item · Marg · gina · kam/zyada · four chips
  (`Galti se bill nahi bana` · `Toota / kharab` · `Vaapas nahi aaya` · `Pata nahi`; a surplus: `Bill bana, diya nahi` ·
  `Pata nahi`) → `stock_diff.cause` (BILLING / BREAKAGE / **NOT_RETURNED** / **DONT_KNOW** / **BILLED_NOT_GIVEN** — the last
  three added to `stock_app.CAUSES` as data, nothing existing changed), cause_by / cause_at, audited in `audit_log`. One tap =
  saved (green card); a repeat within 10 minutes writes nothing; his answer stands after 10 minutes; the owner may change any
  on the hub through the same door.
- **Progress line:** `Orthotics: N mein se M ho gaye` → `Sab ho gaya — ab Amir ke vouchers`. When he reaches all-done the
  **orthotic voucher round is made by itself** (`_voucher_make(section='Orthotics')`, idempotent) — orthotic lines only,
  ≤ 6 lines a voucher, ISSUE/RECEIVE for swaps (D541/D542); the medicines' lines stay for their own round.

**The owner's hub** (`/finance/stock/page/hub?count=1`, English) gains the card **Orthotics section**: the verdict line
(`Orthotics section: CLOSED on <date>` when all four hold, else what is left), the four conditions, Darpan's progress,
**Make the orthotic round**, every open orthotic line with `Darpan: <reason>` and one-tap change chips, the rename status.
`(Darpan)` beside a pair he answered on step 2. Nothing else on the hub moves.

**NEW `/root/finance/item_alias.py` — the rename memory (D620).** Table `marg_item_rename` seeded with the 22 of
`S268_ORTHOTIC_NAME_FIX_THE_22` v2 (old_name, new_name, old20/27, new20/27, planned/done/verified, seen_n). Every new
name ≤ 29; no collision at 20/27/29 across the 373 count names (re-proved by the seed and the walk).
**Amir's board** gains **Naam badlo (22)**: old → new, one tick **"Marg mein badal diya"** each (undo until verified).
At tick time the memory follows: the new name inherits the old name's section (`section_map.inherit`), the item spine gets
the new name as an alias on the OLD item (`marg_item_name` kind `alias`; the S229 `pending_rename` spelling of that item is
retired), the S229 rename task of that name is closed.
**Applied at read time in the count/stock lanes** (`stock_app`: `_mrp_p`, `_feed_latest`, `reconcile`, `_sales_since`,
`_purchases_since`, `_item_life`, `_pursue_sales`): a ticked rename's new name — exact, 20- or 27-character clip, or their
keys — resolves to the row keyed by the old name; the snapshot keeps the new name. The spine (`spine_build.py`) reads the
ticked renames read-only as an alias new → old at the 20-character clip and records them in `sp_alias` (kind `rename`);
it applies from the spine's next nightly run (not run by this kit). An unticked rename maps nothing.
**Verification (F-529):** the first closing-stock export that carries the new name and not the old marks `verified_at`
(+ that export's md5 and date) — at both doors: `marg_take.take()` (a VERIFIED STOCK_CLOSING file, read with the spine's
certified reader, fail-soft) and `/api/snapshot` (push_snapshot). A rename ticked but not seen in two exports shows amber
on Amir's board and the hub: **Marg mein abhi dikha nahi**.

**The section verdict** (hub in English, Darpan's page in Hindi): CLOSED when (1) every orthotic line is answered and every
line that still moves Marg carries the owner's word · (2) no orthotic line waits for a voucher and every orthotic batch is
entered · (3) the proof (D543) is green for the orthotic vouchered items · (4) all 22 renames verified. Stored once in
`stock_section_close`. The whole-shop round stays open for the medicines.

## Pins (FROM read on the box 26-Sep-2026 05:33 IST → TO; built by `make_s404.py` from the live bytes, anchored edits)
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_app.py | 1b473fbf586dea13edd40a6a993cb2ba | 586ae78ae6437f806692c2a1e4eeeb37 |
| /root/finance/stock_hub.html | c4f3280b2d005b39c02d3f6eed13c3ec | 68d11419e7fb9a8e5fec74095b60b255 |
| /root/finance/stock_amir.html | 14024b8dfc64c76959ec12f43e0a4f88 | c2ea41b2db7e2b337e0a97426aaed763 |
| /root/finance/section_map.py | b05b0f08ad65519675e21c9a6f4e90a0 | 9bf9b98fbfe64276b46c0a56ee9719e0 |
| /root/finance/spine/spine_build.py | 1378c87de2f8d4b3796cd92c7ca50d8d | ce99bedf60194a84fe93455927a336e2 |
| /root/marg_ingest/marg_take.py | 75b8056cc43ad6f3034ea1fa819ed7a8 | 21e37b0e6fa6505a8825b32b7c24d41d |
| /root/finance/finance_app.py (unit line + guarded mount only) | d7ee72c51564a397f4e847e98eb80ddc | 186a500a862a7f77da45e1e39b504f2e |
| /root/portal/portal.py (the tile only) | 592ccf99d02c361d4d5eb580995599c3 | 4a5b505e0274e37ab576fa0bc7852420 |
| /root/portal/tile_grants.json (v26 → v27) | 9231cefad0897a64aa127ce4a448f4fe | 9e3124e02fd79d3e1ef01e52bdc5cc76 |

Not touched, and why: `sale_bill.py` keeps no item name (bill money only); `finance_ingest.py` does not write the sale
lines (`finance_returns.py` does, outside the brief) — the alias is applied where the count/stock lanes READ them;
`spine/marg_read.py` reads files and keys nothing; `pad_receipt.py` was not needed.
Restarts `clinic-finance` and `clinic-portal` only. `finance.db` is backed up first; the seed adds one `business_unit`
row, two `unit_role` rows and the 22 `marg_item_rename` rows.

## Proof
`walk_s404.py` — the REAL patched app over a SCRATCH copy of the live database, the real round 1, every pair and line found
by key (the names the API returns), crafted rows keyed W404*: the unit and every gate · Darpan sees only orthotic pairs/lines
of round 1, no medicine leaks · a Haan lands the same rows the owner's Yes lands (stock_match by darpan, swap vouchers on the
hub) · an owner-answered pair is read-only to him · reasons store once, a repeat within 10 minutes writes nothing, a change
within 10 minutes is his correction, the owner's change locks it · progress counts · all-done makes the orthotic round by
itself (orthotic lines only; the medicine lines with a decided cause are NOT vouchered) · a Medicines round on request ·
Amir's entered tick · the 22 seeded exactly (≤ 29, no collision at 20/27/29 across the 373) · a tick follows into the
section map, the spine's name table and the S229 task · a ticked rename maps a crafted sale line (20-clip), purchase line
(27) and stock row under the NEW name onto the OLD item (item life, reconcile, the feed reader); an unticked one maps
nothing · verification through `item_alias`, the snapshot door and marg_take's door on a real archived export · the verdict
flips CLOSED only when all four conditions hold, stored once · Hindi on Darpan's page · the portal tile.
**Negative controls** on the box as it is: no page, no unit, no `ortho` / `renames` blocks, DONT_KNOW refused, the old make
vouchers medicine lines too, the old reconcile does not see the new name. Then **S400's and S402's own walks are re-run** on
the patched files (their negative controls rebuilt from the `.bak_S400` / `.bak_S402` files).

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S404_ORTHO_STOCK_CLOSE/install_S404_ORTHO_STOCK_CLOSE.sh
```
Undo: put back the nine `.bak_S404_<from8>` files, remove `item_alias.py`, `stockmatch.py`, `stockmatch.html`, restart the
two services. The seeded rows (unit, roles, 22 renames) are data and stay; the database backup is used only if the owner
says so.
