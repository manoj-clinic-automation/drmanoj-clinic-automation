# Claude Code brief — S404_ORTHO_STOCK_CLOSE (close the orthotic section of the 06-Sep stock check)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first — every rule binds. **Kit S404 · decisions D619, D620**
(claimed on the System Board). The owner has approved this WHAT. Build → test on a copy → install → verify → publish → report,
in one run. **This brief runs BEFORE `S403_PURCHASE_ORDERS_LIVE.md`** (the same paste); do not start S403 until S404 is
installed, verified and published.

## 1 · The owner's words (26-Sep)
"I want to close the stock check for the orthotic section first. For that, I need Darpan to have an interactive tool where he can
do the matches and whatever you have made on my page. So he gets to do it either on his mobile or on his PC. And then Amir
changes the names as you have suggested. All this happens today and tomorrow." Staff flow: taps, practically no typing.

## 2 · What exists — read it before designing (all in `/root/finance/`)
- **The count:** `stock_count` id 1 (06-Sep, status `submitted`), `stock_count_item` (373; 69 orthotics per
  `stock_item_section.section='Orthotics'`), `stock_diff` (207 rows: 188 open, 19 reconciled; columns cause / cause_note /
  cause_by / status), `stock_match` (2 rows, the owner's NO answers on two medicine pairs — LEAVE THEM).
- **The hub** `stock_app.py` (1b473fbf) `/finance/stock/page/hub?count=1` (`stock_hub.html` c4f3280b): eight steps.
  Step 2 = `POST /api/pad/match/<cid>` (Yes/No per proposed pair: same-salt pairs and the ORTHOTIC swap families paired by
  product family + nearest size — S297/S299); step 3/4 = Darpan's list (`pad_receipt.py` f06daf16, `stock_desk.html`
  485720fd), `/api/diff/<id>/cause`; step 5/6 = vouchers `/api/pad/vouchers/<cid>/make` and `/entered` (rounds of ≤ 6 lines,
  ISSUE on the short item + RECEIVE on the extra one for a confirmed swap, D541/D542, on Amir's board `stock_amir.html`
  14024b8d); step 7 = the proof (`/api/pad/mismatch`, D543: drift between the last export before the first voucher and the
  first after the last, purchases in); step 8 = the claim queue (`claim_queue.py` a61744ee, Darpan's card `darpan_app.py`
  2c22822d / `darpan_card.html` 8510c9cb). **The owner's step-2 answers already given are his and are never re-asked.**
- **Section scope** (S314): a round has an effective section; `_pad_family` measures "done" against the scope. The 06-Sep round is
  whole-shop. **Do not re-scope it.** Closing "the orthotic section" means: every orthotic line of round 1 has an answer, its
  vouchers are made and entered, and the proof is green for those lines — reported as a section verdict on the hub.
- **The 22 renames:** the owner's list `S268_ORTHOTIC_NAME_FIX_THE_22.md` (project knowledge; a copy is in
  `deploy_kits\KB_canon_all\` if present — else its content is summarised in §3.3). Old name → new name, every new name ≤ 29
  characters, zero collisions at 20/27/29 (proved at S268). Amir renames in Marg; the system must FOLLOW the rename.
- **Where names are keyed raw** (why D549 made renames wait): `stock_count_item`, `stock_diff`, `stock_diff_lane`,
  `stock_voucher_line`, `stock_match`, `stock_item_section`, `stock_snapshot`, `sale_line_item`, `purchase_line`,
  `purchase_salt_marg`, the spine's readings. **Marg clips names**: 20 chars in the sale export, 27 in purchase, 29 in the
  master — a rename memory must match on the clipped forms too.
- **Amir's board** already has a tick-list pattern (the salt corrections page `/finance/stock/page/salts`, `marg_task`).

## 3 · The build
### 3.1 Darpan's "Stock match" (Hindi, phone-first, works on the PC too) — tile **"Stock milaan"**
- New unit `stockmatch` (S400's pattern): `unit_role` darpan **maker**, manoj **checker**; nobody else. Portal tile roles
  `['doctor']`, granted by name to `darpan` (grants file v27, note line in its own style).
- **Section: Orthotics only** (the medicines' lines are not shown to him in this kit).
- **Card 1 — "Adla-badli? (N)"**: every step-2 pair of round 1 whose two items are orthotics and whose answer is still empty:
  short item · extra item · qty · **Haan** (billed as the other size — a swap) · **Nahi**. Writes through the SAME door the owner
  uses (`/api/pad/match/<cid>` logic, by_user = darpan). A pair the owner already answered is shown greyed with his answer and
  cannot be changed by Darpan.
- **Card 2 — "Kam kyun? (N)"**: every open orthotic `stock_diff` shortage left after the swaps: item · Marg qty · counted · diff ·
  four reason chips → `cause` (map to the existing cause vocabulary in `stock_app.py`; if it has no matching value add the four
  as data, never by editing existing values): `Galti se bill nahi bana` · `Toota / kharab` · `Vaapas nahi aaya` · `Pata nahi`.
  Surplus lines: `Bill bana, diya nahi` · `Pata nahi`. One tap = saved (green card, S394 pattern; a repeat within 10 min = no
  second write). His answers stand; the owner may change any on the hub (audited).
- **Progress line** at the top: `Orthotics: N mein se M ho gaye` and, when all are answered, `Sab ho gaya — ab Amir ke vouchers`.
- **Owner's hub**: the orthotic lines show `Darpan: <answer>` beside each; a one-tap change; nothing else on the hub moves.

### 3.2 The orthotic voucher round, on Amir's board
- When every orthotic line of round 1 has an answer: **"Make the orthotic round"** (owner on the hub, or automatically when
  Darpan's progress reaches all-done — do both, idempotent): `/api/pad/vouchers/<cid>/make` restricted to ORTHOTIC lines
  (add a `section` filter to the make step; medicines' lines are not touched and stay for their own round later). ≤ 6 lines per
  voucher, ISSUE/RECEIVE for swaps, as D541/D542 already do.
- Amir's board (`stock_amir.html`): the round's vouchers with **"Marg mein daal diya"** per voucher (exists — `/entered`), in Hindi
  labels as they are today.

### 3.3 The 22 renames on Amir's board + the rename memory (D620)
- New table `marg_item_rename` (old_name, new_name, old20, old27, new20, new27, planned_by, planned_at, done_by, done_at,
  verified_at, verified_md5). Seeded with the 22 from the S268 list (read the list from canon/project; **if the file is not
  reachable, STOP this part and report — never guess names**).
- Amir's board gains **"Naam badlo (22)"**: old → new, one tick **"Marg mein badal diya"** each (done_by/at). Nothing else typed.
- **The memory is applied at every import**: `sale_bill.py`/`finance_ingest.py` (sale lines), `marg_take.py`/`marg_ingest`
  (stock closing, purchase), the spine readers (`spine/marg_read.py`) — wherever an item name is keyed, a `new_name` (exact,
  or its 20/27-char clipped form) ticked done resolves to the row keyed by `old_name` **for the count and stock lanes**, and the
  snapshot/spine keep the new name with `old_name` recorded as alias (one item, two names, never two items). `section_map.py`:
  the new name inherits the old name's section. `stock_item_section`, `marg_item_name` (kind alias) updated at tick time.
  Keep the change minimal and anchored; one helper module (e.g. `item_alias.py`) used by every lane is preferred over
  re-implementing the mapping in each file.
- **Verification (F-529's lesson — never assume):** after a rename is ticked, the first STOCK_CLOSING export that carries the new
  name and not the old marks `verified_at` (and the md5 of that export); a rename ticked but not seen in two exports shows
  amber on Amir's board and the hub: `Marg mein abhi dikha nahi`.

### 3.4 Proof and the section verdict
- Step 7 for the orthotic round exactly as D543 (last export before the first voucher, first after the last, purchases in).
- Hub step list gains a line `Orthotics section: CLOSED on <date>` when: all orthotic lines answered · orthotic round entered ·
  proof green for those lines · every orthotic rename verified. Darpan's page shows the same in Hindi. The whole-shop round stays
  open for the medicines; nothing about them changes.

## 4 · FROM pins (read live first; mismatch = stop that file and report)
| file | FROM |
|---|---|
| /root/finance/stock_app.py | 1b473fbf586dea13edd40a6a993cb2ba |
| /root/finance/stock_hub.html | c4f3280b2d005b39c02d3f6eed13c3ec |
| /root/finance/stock_amir.html | 14024b8dfc64c76959ec12f43e0a4f88 |
| /root/finance/pad_receipt.py | f06daf1621b025557b648378398c6c83 (only if needed) |
| /root/finance/section_map.py | b05b0f08ad65519675e21c9a6f4e90a0 |
| /root/finance/sale_bill.py | 16469968f68ebc6e0a9e23a3bb9001f4 |
| /root/finance/finance_ingest.py | 747b4a506042b95c862f3eafc74608f3 |
| /root/marg_ingest/marg_take.py | 75b8056cc43ad6f3034ea1fa819ed7a8 |
| /root/finance/spine/marg_read.py | 7ec9b325687de465ea6942affb25dec1 |
| /root/finance/spine/spine_build.py | 1378c87de2f8d4b3796cd92c7ca50d8d |
| /root/finance/finance_app.py | d7ee72c51564a397f4e847e98eb80ddc (clinic — path→unit line + guarded mount only) |
| /root/portal/portal.py | 592ccf99d02c361d4d5eb580995599c3 (clinic — the tile only) |
| /root/portal/tile_grants.json | 9231cefad0897a64aa127ce4a448f4fe v26 (clinic — one grant + note) |
The clinic chat may have moved `portal.py` / `tile_grants.json` / `finance_app.py` (its slips kits S398/S401): build on the live
bytes only if the change is one of its kits recorded in `deploy_kits\`; name it. Restart `clinic-finance` + `clinic-portal` only.
**The spine builds nightly under its own lock** — do not run a spine build during clinic hours from this kit; the alias applies
from its next run.

## 5 · The walk (scratch copy; own rows found by key; S400/S402 walks re-run green)
Darpan sees only orthotic pairs/lines and only round 1 · a Haan lands the same rows the owner's Yes lands (swap + voucher lines
ISSUE/RECEIVE on make) · an owner-answered pair is read-only to him · reasons store once, repeat within 10 min refused · progress
counts correct · make-round restricted to orthotics (a medicine line with a decided cause is NOT vouchered) · Amir's entered tick
works · the 22 seeded exactly (assert count 22, every new name ≤ 29 chars, no collision at 20/27/29 across all 373 names) · a
ticked rename maps a crafted sale line, purchase line and stock row under the NEW name (and its clipped forms) onto the OLD item
in the count/stock lanes, and section inherited · an unticked rename maps nothing · verification marks on a crafted stock export ·
the section verdict flips CLOSED only when all four conditions hold · darpan/bhati/shavez refused on the hub, darpan allowed on
his page (403/302 patterns per CLAUDE.md) · **negative controls** on the old files.

## 6 · Done means
Kit `deploy_kits\S404_ORTHO_STOCK_CLOSE\` · installed, md5s read back · healthz 200 · published with `PUBLISH_ALL.bat` ·
`claude_code_briefs\REPORT_S404.md` (owner lines first: what Darpan taps, what Amir ticks, what turns green; ending with
`https://followup.dr-manoj.in/finance/stock/page/hub?count=1` and Darpan's page address in full). Then go on to S403.
