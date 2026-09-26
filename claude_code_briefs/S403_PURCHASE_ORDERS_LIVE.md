# Claude Code brief — S403_PURCHASE_ORDERS_LIVE (one screen: shortages → WhatsApp order → arrival → bill scan; orthotics first)

Written 26-Sep-2026 by the Sanjeevni chat (S283); **supersedes `S403_ORTHOTIC_ORDER.md` in full** (never run; already renamed to `S403_ORTHOTIC_ORDER.superseded.md.tmp`, which git ignores — leave it). Read `CLAUDE.md` first. **Kit S403 · decision D618.** The owner has approved this
WHAT. **Run only AFTER `S404_ORTHO_STOCK_CLOSE.md` is installed, verified and published** (same paste); read `REPORT_S404.md`
and re-read every FROM pin live — S404 moves several of them.

## 1 · The owner's words (26-Sep)
- Orthotic shortages shown interactively to Darpan (Kal ka hisaab), Bhati (Medical sale check) and him (Sanjeevni page); from there
  the order goes to the supplier **Yuvika** as a WhatsApp message. Very thin inventory (space).
- "As per the decided purchase-order flow: the shortage comes, the WhatsApp message goes, the purchase arrives, the bill is
  scanned, whether that item is available / out of stock is logged or detected — what was the purchase order and what was supplied."
- "Minimum or practically no typing for the staff. Frictionless. The work should occupy ONE screen as collapsible, expandable
  sections on the mobile phone. The orders were planned to be sent from the reception mobile — personal WhatsApp, not the
  business number."
- "The purchase scanning was never executed; it is lying dormant." Make it operational now with Darpan and the reception staff.
- Orthotics = a subsection of the purchase-orders screen; **reception gets the tile now, nothing parked.**
- "Inventory as per the 6-Sep stock check quantities." Keep-in-stock rule approved (§3). Both he and Darpan send; reception sends too.

## 2 · What exists — REUSE, never a second ordering system (all `/root/finance/` unless said)
- **S225 ordering (05-Sep), never used** — `purchase_app.py` (9ad50878): `/api/order`, `/page/orders`, `/page/staff`
  (Item · Stock now · Order qty), `/order/<id>/pdf`, `/page/book`+`/api/book` (phone book: two numbers, bank fields owner-verified),
  arrival with supplied/short per line; short lines ride into the next order (rev 8). WhatsApp text decided 04-Sep:
  `Sanjeevni Medicos, G 15 Rampur Garden, Bareilly` + blank line + `Item — qty unit` per line, **no rates**; `https://wa.me/<no>?text=`;
  marked SENT (who, when). `purchase_order` 0 rows, `purchase_order_line` 0 rows.
- **Scan Purchase** (asset app `/scanapp/intake`, `/root/assetapp/asset_register.py`; Sarvam OCR; tile on the staff role, masked only
  from amir and bhati): reception photographs a bill → stamp number. Purchase side: `purchase_scan_link`, `purchase_bill.scan_bill_id`,
  `/page/scans` + `Re-match` (EXACT = vendor+bill no+amount; PROBABLE = bill no+amount or vendor+date+amount). **Live today:
  0 links; 109 purchase bills since 17-Aug, none with a scan.** Either no pharmacy bill was ever scanned or the match cannot reach
  the asset app's database (`_assets_con()` → "asset app not reachable"). **First job: find out which, on the box, read-only, and
  say it in the report.**
- **Orthotics:** `stock_item_section` (`section='Orthotics'`, 69). **Supplier:** every orthotic bought this FY is `YUVIKA SURGICALS`
  (140 purchase lines); phone in `purchase_vendor_contact` (vendor_norm `YUVIKA SURGICALS`). **Never print, log, commit or return
  the number to a non-sender**; it goes only into the wa.me link built server-side for a permitted user.
- **The count (S404 done):** `stock_count_item.counted_qty` of round 1 = the 06-Sep shelf; `stock_diff` answers; the orthotic vouchers;
  the rename memory `marg_item_rename` + `item_alias.py` (or whatever S404 named it — read REPORT_S404).
- **Stock/sales/purchases:** `stock_snapshot` (Marg closing, daily; `as_on` is `DD-MM-YYYY` TEXT — parse it, never max() the text);
  `sale_line_item` (20-char names, `qty_raw` `strips:loose` or a number, `is_return`); `purchase_line` (27-char names, qty + free);
  the spine (`/root/finance/spine/spine.db`, read door `spine_read.py`) — **from 27-Sep the spine has its seven clean nights:
  read sales and purchases from the spine's read door when its gate state is green, else from the tables above; say which.**
- Rounding rule (owner 04-Sep) is for medicines: strips rounded up to 10 then tens. **Orthotics are ordered in pieces, no rounding.**

## 3 · Rules (D618)
- **Shelf now (orthotics)** = 06-Sep counted qty + purchases since 06-Sep (Yuvika, 27-char exact) − sales since + sale returns,
  with the rename memory applied. Marg's closing is a cross-check shown beside it (`Marg: n`), never the base, until the section
  proof is green — after that the two agree by construction. For the 22 size-ambiguous names (families of 8, until their renames
  are verified): the FAMILY shelf is exact, the per-size split is `approx`; a short family orders the size with the lowest count, and
  the sender can switch the size with one tap before sending. Once a rename is verified the item is exact.
- **Keep-in-stock** per orthotic (new table, owner-editable ±, audited): seed **2** if ≥ 3 units sold in 90 days, **1** if sold at
  least once in 180 days, **0** otherwise; a re-seed never overwrites an owner-set number.
- **On order** = units on SENT orders not yet received/closed. **Shortage** = keep − shelf − on order, when > 0. Keep 0 never shows.
- **Medicines**: proposals from the S225 engine (reading the spine where green), shown in the screen's last section, **send disabled**
  until the owner approves the buying rules and the do-not-order list (`order_rules.json` S341 + the S225 settings) on his page —
  one sitting; the screen says `Doctor sahab ke rules ka intezaar`.
- **Who** (settings, so a change is a data edit): senders `manoj, darpan, shavez, shivani, alisha` · viewers `bhati` · vendor for
  orthotics `YUVIKA SURGICALS`.

## 4 · The ONE screen — "Purchase orders" (Hindi, phone-first, every section collapsed until tapped; no typing except the supplied
qty on Kam aaya). Tile **"Purchase orders"**, roles `['doctor']`, granted by name to darpan, shavez, shivani, alisha (grants v28,
note line). New unit `porders` (S400 pattern): maker rows for the four, checker manoj; bhati has NO row here (his view is inside
Medical sale check, §5). Route e.g. `/finance/porders`.
1. **Orthotics (Yuvika) — N kam**: the shortage lines (item · shelf · keep · order qty; `approx` where it applies) · ± on qty ·
   size-switch on an ambiguous family · **Yuvika ko order bhejo** → ONE `purchase_order` (vendor from the setting) with a line per
   shortage → wa.me link opens on the phone with the 04-Sep text → marked SENT (who, when). Re-opening shows `Order bheja —
   <time>, <who>`; those items read as on order. Same order visible on S225's `/page/orders`. A repeat within 10 min = no second order.
2. **Order aaya? (N)**: every SENT order, one card: per line **Aa gaya** · **Kam aaya** (then the supplied qty) · **Nahi mila**
   (out of stock at the supplier); **Sab aa gaya** for the whole order. Short/missing lines carry into the next order (S225 rev 8),
   logged as such. **Detected too:** a Marg purchase line from the vendor for an ordered item after the send date (27-char exact)
   marks the line supplied with that qty and bill no even if nobody tapped; ordered vs supplied vs billed stored per line.
3. **Bill scan karo (N)**: received orders / Marg purchase bills since 17-Aug with no scan: one tap opens `/scanapp/intake` with the
   vendor (and bill no + amount when Marg already has the bill) pre-filled — add the pre-fill parameters to the intake if it lacks
   them (asset app file, declared; smallest anchored change). When the scan exists, the match links it (fix the match if §2's
   check shows it cannot reach the asset app; otherwise run it on capture, not only on demand); the line disappears. A bill unscanned
   3 days after arrival turns red here AND on the owner's purchase month page. The owner's `/page/scans` gains the same red list.
4. **Medicines (rules ka intezaar)**: proposals by supplier, same layout, send disabled (§3).
Every save: a large green card naming what was saved (S394). Owner's English view of the same screen at the same route.

## 5 · The other places
- **Darpan — Kal ka hisaab**: one card `Orthotic kam hai — N` (collapsed; the list; a button that opens the Purchase orders screen).
- **Bhati — Medical sale check**: the same card, **view only** (no send, no arrival, 403 on those APIs).
- **Owner — Sanjeevni approvals page**: collapsible `Orthotic shortages — N`, the keep ± per item, a link to the full 69 with keep
  numbers, and `Needs you`: `Orthotic shortages: N items — order not sent` / `Bill scan pending on N purchase bills` / `Buying
  rules for medicines await your approval` (this last with the one-sitting page: the S225 settings and the do-not-order list as
  tap-to-approve, stored with who/when).

## 6 · FROM pins — READ LIVE AFTER S404 (S404 moves stock_app.py, section_map.py, sale_bill.py, finance_ingest.py, marg_take.py,
spine files, finance_app.py, portal.py, tile_grants.json; take the TO pins from REPORT_S404.md and verify them on the box)
| file | FROM (as of 26-Sep, before S404) |
|---|---|
| /root/finance/purchase_app.py | 9ad508789e2821c284b48ef6a4446cfa |
| /root/finance/darpan_kal.py | 1958ee7c620d890f10a609473b2a8f1d |
| /root/finance/darpan_kal.html | 4f115f44b9ed505f5838ef3ee0a4267a |
| /root/finance/sale_check.py | 92ca5cb2d3a4388bbf6a29e35af2d492 |
| /root/finance/sale_check.html | 9c70af26456092285a9545083365bfff |
| /root/finance/sanjeevni_approvals.py | 5fdfa364dee3dd9dcef9ad5fed3233d9 |
| /root/finance/finance_ui/finance_approvals.html | 6622587e47faff016bf280d380bd4564 (clinic — declared) |
| /root/assetapp/asset_register.py | read live (clinic — declared; pre-fill parameters only, if needed) |
| /root/finance/finance_app.py · /root/portal/portal.py · /root/portal/tile_grants.json | S404's TO pins (clinic — declared) |
Restart `clinic-finance` + `clinic-portal` (+ `assetapp` only if its file changed) — nothing else.

## 7 · The walk (scratch copy; own rows by key; S400/S402/S404 walks re-run green; never opens wa.me; no real order)
Shelf = count + purchases − sales + returns with the alias applied (negative control: the text-max date bug; a raw un-aliased
name) · family exact / size approx / size switch · keep seed tiers, owner-set survives re-seed · on-order removes an item ·
keep 0 hidden · send creates one order + lines, text exactly the 04-Sep format, no rate, vendor number absent from every response
to a non-sender and from logs/report · repeat within 10 min refused · Aa gaya / Kam aaya / Nahi mila store and carry · a crafted
Marg purchase line auto-marks supplied with bill no · ordered/supplied/billed stored · scan: pre-filled intake link built; a crafted
scan matches and clears the line; 3-day red on the screen and the owner's month page · medicines: shown, send 403 until the
owner's approval row exists, then allowed · roles: the four + manoj allowed; bhati view-only (403 on send/arrival); darpan's card
and bhati's card render; owner's section + three Needs-you lines · negative controls on the old files.

## 8 · Done means
Kit `deploy_kits\S403_PURCHASE_ORDERS_LIVE\` · installed, md5s read back · healthz 200 · published · `claude_code_briefs\REPORT_S403.md`
(owner lines first, incl. the §2 scan finding in one sentence; ending with the Purchase orders address in full, and
`https://followup.dr-manoj.in/finance/approvals`). 
