# S403_PURCHASE_ORDERS_LIVE — one screen: shortages → WhatsApp order → arrival → bill scan (orthotics first)

**Sanjeevni project · session 283 · 26-Sep-2026 · decision D618 (the owner's words, 26-Sep). Runs after S404.**

## What the owner asked for
The orthotic shortages shown to Darpan, Bhati and him; from there the order goes to **Yuvika** as a WhatsApp message from the
reception mobile; the purchase arrives; the bill is scanned; what was ordered and what was supplied is logged or detected.
Minimum typing, ONE screen of collapsible sections on the phone. The purchase scanning, dormant since S225, made operational.
Orthotics a subsection of the purchase-orders screen; reception gets the tile now. Inventory as per the 06-Sep stock check.

## The §2 finding (read on the box, read-only, 26-Sep 06:30 IST)
The match **can** reach the asset app's database (`_assets_con()` opens `/root/assetapp/assets.db` read-only; 15 scanned bills
in it, two from pharmacy vendors — Yuvika, Jugnu). It found none because the match reads only scans filed on the **pharmacy
lane** (`kind='Pharmacy'`), and every one of the 15 was filed on the reception intake's default **clinic** lane
(`kind='Consumable'`); the last re-match recorded `0 scans : 0 bills`. So: no pharmacy bill was ever scanned *as* a pharmacy
bill, and the connection was never the fault. The fix is on capture: the Purchase orders screen opens the intake with the
pharmacy lane, the vendor, the bill number, date and amount already in the link, and the intake files them on the bill row —
the match is EXACT the moment the scan lands, and it runs on the next read of any screen that lists the bills.

## What was built
**NEW `/root/finance/porders.py` + `porders.html`** — **Purchase orders** at `https://followup.dr-manoj.in/finance/porders`
(Hindi, phone-first, the owner sees it in English at the same route), tile "Purchase orders" (granted to darpan, shavez,
shivani, alisha; the doctor by role). Its own server unit `porders` (the four makers; manoj checker; **bhati holds no row** —
his view is inside Medical sale check). Senders / viewers / the orthotic vendor are **settings** (`porders.*`), so a change is a data edit.
1. **Orthotics (Yuvika) — N kam:** shelf now = 06-Sep counted + purchases since (Yuvika, 27-char exact) − sales since + returns,
   the rename memory (S404 `item_alias`) applied; `Marg: n` beside it as a cross-check, never the base. The 8 clipped families
   (`KNEE SUPPORT HINGED` ×4, `L S BELT` ×5, `SHOULDER IMMOBILISE` ×3, `TYNOR WRIST SPLINT L/R` ×2+2, `ANKLE BINDER BAMBOO` ×2,
   `BLING PELVIC TRACTIO` ×2, `KNEE IMMOBILIZER UNI` ×2): the FAMILY shelf exact, the per-size split `approx` (in proportion to
   the count) until the rename is verified; a short family orders the size with the lowest count; the sender switches the size
   with one tap. Keep-in-stock per orthotic (table `porder_keep`): seed 2 if ≥3 sold in 90 days, 1 if sold in 180, else 0; the
   owner's ± never overwritten by a re-seed (audited). On order = SENT lines nobody has answered. Shortage = keep − shelf − on order.
   **Yuvika ko order bhejo** → ONE `purchase_order` through S225's own `_staff_send` (the 04-Sep text, no rates; the wa.me link
   built server-side, returned to the sender only) → SENT (who, when) → visible on S225's `/page/orders` too. A repeat within
   10 minutes returns the order already sent. Sales/purchases come from the **spine's read door when its gate is green and the build
   fresh (< 36 h), else the tables — the payload says which**.
2. **Order aaya? (N):** per line **Aa gaya** · **Kam aaya** (supplied qty, the only typing) · **Nahi mila**; **Sab aa gaya** for the
   order. When every line is answered the order becomes RECEIVED through S225's `_arrive` (short lines carried, rev 8). **Detected
   too:** a Marg purchase line from the vendor for an ordered item after the send date marks the line billed (qty, bill no) and
   supplied by `marg` when nobody tapped; ordered / supplied / billed stored per line (new columns on `purchase_order_line`).
3. **Bill scan karo (N):** Marg purchase bills since 17-Aug with no scan link + received orders whose bill is not yet in Marg;
   one tap opens `/scanapp/intake?lane=pharmacy&vendor=…&bill_no=…&bill_date=…&amount=…`; when the scan lands the match links it
   and the line disappears. A bill unscanned 3 days after arrival turns **red** here, on the owner's purchase month page and on
   `/page/scans` (which gains the same red list).
4. **Medicines (rules ka intezaar):** the S225 proposals by supplier, send disabled until the owner approves the buying rules and
   the do-not-order list (`porders.rules_approved`, who/when) on his page — then a send per supplier through the same door.
Every save: a big green card (S394).

**Darpan — Kal ka hisaab:** card `Orthotic kam hai — N` (collapsed; the list; a button to the screen). **Bhati — Medical sale check:**
the same card, view only. **Owner — approvals page:** the section **Purchase orders** with `Orthotic shortages — N` (keep ± per
item, the full 69 with keep numbers) and the **buying rules as tap-to-approve**; Needs you gains `Orthotic shortages: N items —
order not sent` / `Bill scan pending on N purchase bills` / `Buying rules for medicines await your approval`.

**Asset app (declared, smallest anchored change):** the intake reads `lane / vendor / bill_no / bill_date / amount` from the
link, pre-selects the pharmacy lane, and files the values on the bill row (`_create_intake_bill`); the scanner widget is untouched.

## Pins (FROM read on the box 26-Sep-2026 06:29 IST, after S404 → TO; built by `make_s403.py` from the live bytes)
| file | FROM | TO |
|---|---|---|
| /root/finance/purchase_app.py | 9ad508789e2821c284b48ef6a4446cfa | 7896eae4dff4427a2ebdb4f5023fd686 |
| /root/finance/darpan_kal.py | 1958ee7c620d890f10a609473b2a8f1d | 401ee01c7cbd49cea1c34665c99bab60 |
| /root/finance/darpan_kal.html | 4f115f44b9ed505f5838ef3ee0a4267a | 1bedb46991bc5b531e809519c50ee990 |
| /root/finance/sale_check.py | 92ca5cb2d3a4388bbf6a29e35af2d492 | 5a0bf9676c02f303791329c0fb744305 |
| /root/finance/sale_check.html | 9c70af26456092285a9545083365bfff | 53cf611fa9d1ba012cfec128108dda0b |
| /root/finance/sanjeevni_approvals.py | 5fdfa364dee3dd9dcef9ad5fed3233d9 | 675aab4a46ab8792f05b17cab15d17ee |
| /root/finance/finance_ui/finance_approvals.html (clinic — declared) | 6622587e47faff016bf280d380bd4564 | c319bb56d30ac960d49d4a67083a55b2 |
| /root/assetapp/asset_register.py (clinic — declared; pre-fill only) | 71bd32777b69e375e41576c7aeb7eb1d | 30b26d280c6cdf373774a94aae59f339 |
| /root/finance/finance_app.py (S404's TO; unit line + guarded mount) | 186a500a862a7f77da45e1e39b504f2e | 8055b0deddcb65234f1b9d818d56fda9 |
| /root/portal/portal.py (S404's TO; the tile) | 4a5b505e0274e37ab576fa0bc7852420 | 968ca6027ae30d67e7d18b83f35b395d |
| /root/portal/tile_grants.json (S404's TO; v27 → v28) | 9e3124e02fd79d3e1ef01e52bdc5cc76 | 0aadfc523f9ab9c59633dedcd618cee9 |

Restarts `clinic-finance`, `clinic-portal` and `assetapp`. `finance.db` is backed up first; the seed adds one `business_unit` row,
five `unit_role` rows and three settings; `porder_keep` (69 rows) and the new `purchase_order_line` columns are created on the
first read. `assets.db` is never written by this kit (the intake writes it as before, with the pre-filled fields).

## Proof
`walk_s403.py` — the REAL patched finance app AND the real patched asset app over SCRATCH copies of both databases, the real 69
orthotics, every item found by the name the API returns, crafted rows keyed W403*; never opens wa.me, no real order: the gate and
the roles · shelf = count + purchases − sales + returns for every exact item, the 8 families approx, the source (spine when green
and fresh, else tables), the newest closing by its real date (negative control: the text-max bug) · the keep tiers, the owner's
number survives a re-seed, keep 0 hidden, size switch offered · ONE order with the exact 04-Sep text and no rate, the number only
inside the link (never printed), on order removes the item, repeat within 10 minutes = the same order, bhati and an unknown item
refused · Kam aaya / Nahi mila / Aa gaya / Sab aa gaya stored and carried, the order received through S225's door, answered
lines locked · a crafted Marg purchase line auto-marks supplied with its bill no · the red list, the pre-filled intake link, the
intake's prefill parser, a crafted scan through the REAL intake code (kind Pharmacy, captured, vendor/bill/amount on the row),
the EXACT link, the bill gone from the list, the month page 'scan exact' · medicines shown (no orthotic), send 403 until the
owner's approval row, then allowed · Darpan's and Bhati's cards, the owner's three lines, the summary door · a sale line under
an un-ticked rename maps nothing, ticked it counts · the portal tile. **Negative controls** on the box as it is. Then **S404's,
S400's and S402's own walks re-run** on the patched files (their negative controls rebuilt from the `.bak_S404` / `.bak_S400` /
`.bak_S402` files). S400's frozen walk asserts Needs you "unchanged except its own line", which S403's three lines
legitimately break: that one re-run alone gets `NEEDS_YOU_WITHOUT_S403=1`, an environment switch the service never sets;
S403's own walk proves the three lines.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S403_PURCHASE_ORDERS_LIVE/install_S403_PURCHASE_ORDERS_LIVE.sh
```
Undo: put back the eleven `.bak_S403_<from8>` files, remove `porders.py` / `porders.html`, restart the three services.
The seeded rows (unit, roles, settings, keep numbers) are data and harmless; the database backup is used only if the owner says so.
