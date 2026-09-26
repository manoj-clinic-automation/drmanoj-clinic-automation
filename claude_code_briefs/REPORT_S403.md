# REPORT_S403 — S403_PURCHASE_ORDERS_LIVE (one screen: shortages → WhatsApp order → arrival → bill scan)

Installed on srv1746119 on **26-Sep-2026** (installer stamp 07:19:10 IST; database backup written 07:23 IST; verified 07:26:57 IST — times read
from the files). Ran after S404 (REPORT_S404) with every pin re-read live. Published with PUBLISH_ALL.bat.

## For Dr Manoj (plain English)
- **The scan finding, in one sentence:** the match could always reach the scan app; it found nothing because every one of the 15 scans ever made
  was filed on the intake's default *clinic* lane (two were pharmacy bills, Yuvika and Jugnu), and the match reads only the *pharmacy* lane —
  so no pharmacy bill was ever scanned *as* one. From today the "Bill scan karo" tap opens the scanner with the pharmacy lane, the vendor,
  the bill number and the amount already filled in, and the bill is matched the moment it lands.
- **Darpan, Shavez, Shivani and Alisha have a new tile, "Purchase orders"** — one Hindi screen, four collapsible sections: *Orthotics (Yuvika) — N kam*
  (the shortages from the 06-Sep count, ± on the quantity, one tap **Yuvika ko order bhejo** opens WhatsApp with the order text from the phone
  it is tapped on) · *Order aaya?* (per line Aa gaya / Kam aaya / Nahi mila; Sab aa gaya) · *Bill scan karo* (bills with no scan; red after 3 days)
  · *Medicines* (shown, sending waits for your buying rules). One tap = a big green card; a repeat within 10 minutes never sends twice.
- **You** see the same screen in English at the same address, and on your approvals page a new section **Purchase orders**: *Orthotic shortages — N*
  with a keep-in-stock ± per item (seeded 2 / 1 / 0 from what sold in 90 and 180 days; your number is never overwritten), the full 69, and the
  **buying rules for medicines as one tap to approve** — until you do, staff cannot send a medicine order. *Needs you* names the shortages with no
  order sent, the bills awaiting a scan, and the rules awaiting you.
- **Darpan's Kal ka hisaab** and **Bhati's Medical sale check** each gain the card *Orthotic kam hai — N* (Bhati's is view only).
- On today's live data the seed rule finds **13 orthotic items short** and **108 purchase bills since 17-Aug with no scan** (all older than 3 days).
  Nothing was ordered, scanned or approved by this kit — that is the staff's and yours to do. Everything was proved on copies first.
- The screen: **https://followup.dr-manoj.in/finance/porders** · your page: **https://followup.dr-manoj.in/finance/approvals**

## For the chat
### §2 finding (read-only, 06:30 IST)
`_assets_con()` opens `/root/assetapp/assets.db` read-only and answers; `bills` holds 15 rows, all `kind='Consumable'` (13 draft, 2 approved;
vendors include YUVIKA SURGICALS ×1, JUGNU MEDICOS ×3). `_scans()` selects `kind='Pharmacy'` → 0 rows; `purchase.rematch_seen` read `0:0`.
`purchase_scan_link` 0; `purchase_bill` since 17-Aug 109, none with `scan_bill_id`. The intake's lane select defaults to *clinic*; only the
pharmacy lane files `kind='Pharmacy'`/`status='captured'`. So: the connection was never the fault; no pharmacy scan existed for the match to see.
Fix per the brief's "otherwise": on capture — the pre-filled intake (asset app, declared) + the match re-run on the next read of any screen that
lists the bills (`_rematch_if_changed`, fingerprint-cheap). The 15 existing clinic-lane scans are left as they are (named here, not re-laned).

### Live files FROM → TO (md5 read back after placing; re-read 07:26 IST identical)
| file | FROM | TO |
|---|---|---|
| /root/finance/purchase_app.py | 9ad508789e2821c284b48ef6a4446cfa | 7896eae4dff4427a2ebdb4f5023fd686 |
| /root/finance/darpan_kal.py | 1958ee7c620d890f10a609473b2a8f1d | 401ee01c7cbd49cea1c34665c99bab60 |
| /root/finance/darpan_kal.html | 4f115f44b9ed505f5838ef3ee0a4267a | 1bedb46991bc5b531e809519c50ee990 |
| /root/finance/sale_check.py (VERSION stays 1.1 — S402's frozen walk reads it) | 92ca5cb2d3a4388bbf6a29e35af2d492 | 5a0bf9676c02f303791329c0fb744305 |
| /root/finance/sale_check.html | 9c70af26456092285a9545083365bfff | 53cf611fa9d1ba012cfec128108dda0b |
| /root/finance/sanjeevni_approvals.py | 5fdfa364dee3dd9dcef9ad5fed3233d9 | 675aab4a46ab8792f05b17cab15d17ee |
| /root/finance/finance_ui/finance_approvals.html (clinic — declared) | 6622587e47faff016bf280d380bd4564 | c319bb56d30ac960d49d4a67083a55b2 |
| /root/assetapp/asset_register.py (clinic — declared; the intake pre-fill only) | 71bd32777b69e375e41576c7aeb7eb1d | 30b26d280c6cdf373774a94aae59f339 |
| /root/finance/finance_app.py (S404's TO; unit line + guarded mount only) | 186a500a862a7f77da45e1e39b504f2e | 8055b0deddcb65234f1b9d818d56fda9 |
| /root/portal/portal.py (S404's TO; the tile only) | 4a5b505e0274e37ab576fa0bc7852420 | 968ca6027ae30d67e7d18b83f35b395d |
| /root/portal/tile_grants.json (S404's TO; v27 → v28) | 9e3124e02fd79d3e1ef01e52bdc5cc76 | 0aadfc523f9ab9c59633dedcd618cee9 |

New: `/root/finance/porders.py` 78d1712a69324a06c2894c19158cd834 · `/root/finance/porders.html` 76a173af5faee643fa0d0139731b10e8.
Built on the box by `make_s403.py` from the live bytes (anchored edits, each anchor exactly once); TO pins matched the kit.

### Backups
`/root/finance/finance.db.bak_S403_20260926_071910` (backup API) · `.bak_S403_<from8>` beside each of the eleven files: `purchase_app.py.bak_S403_9ad50878`,
`darpan_kal.py.bak_S403_1958ee7c`, `darpan_kal.html.bak_S403_4f115f44`, `sale_check.py.bak_S403_92ca5cb2`, `sale_check.html.bak_S403_9c70af26`,
`sanjeevni_approvals.py.bak_S403_5fdfa364`, `finance_ui/finance_approvals.html.bak_S403_6622587e`, `assetapp/asset_register.py.bak_S403_71bd3277`,
`finance_app.py.bak_S403_186a500a`, `portal/portal.py.bak_S403_4a5b505e`, `portal/tile_grants.json.bak_S403_9e3124e0`.

### Services restarted · health
`clinic-finance`, `clinic-portal`, `assetapp` (all active). `/finance/healthz` 200; `/finance/porders`, `/finance/approvals` and `/scanapp/intake?…`
302 to a plain curl (login gates, expected); the asset app's login page 200; the journal shows no "NOT mounted" and no traceback.

### Data changes (seed, INSERT-only) · what the walk left
`business_unit` +1 (`porders`) · `unit_role` +5 (darpan, shavez, shivani, alisha makers; manoj checker; bhati none) · `setting` +3 (`porders.senders`,
`porders.viewers`, `porders.ortho_vendor` — the who and the vendor as data). `porder_keep` (69 rows) and the new `purchase_order_line` columns
(missing, billed_qty, billed_bill_no, billed_date, detected_at, arrived_by, arrived_at) + `purchase_order.section` are created on the first read of
the screen. Read back live at 07:26 IST: `purchase_order` 0, `purchase_scan_link` 0, no W403 row, no rename ticked, `stock_match` 2, `stock_voucher_line` 0,
`assets.db` 15 bills / 0 pharmacy-lane — the walk's writes stayed on the scratch copies.

### The walk (walk_s403.py — the real finance app AND the real asset app on scratch copies of both databases)
`WALK_S403 GREEN -- 52/52`. Gate and roles (the four + owner 200; bhati/amir/bhawna 302) · the state: vendor YUVIKA SURGICALS, since 06-09-2026,
source **spine** (gate green, build fresh), all 69 items, keep total 42 · the newest closing by its real date (negative control: the text-max bug) ·
shelf = counted + purchases − sales + returns on every exact item · the 8 clipped families read as families (approx per size) · 69 keep rows on
the tiers; the owner's number survives a re-seed; keep 0 hidden; darpan cannot set keep · the sender's JSON carries no 10-digit number · ONE order
(sent, by darpan, section Orthotics, two lines incl. a switched size), the wa.me link with a 12–15-digit number (never printed) and EXACTLY the 04-Sep
text, no rate; on order removes the item; repeat within 10 minutes = the same order; bhati and an unknown item refused · Kam aaya 1 / Nahi mila →
the order RECEIVED through S225's `_arrive`, the short carried (`_carried_shorts`), answered lines answer "already"; Sab aa gaya; a crafted Marg
purchase line auto-marks the ordered line billed (qty, bill no) and supplied by `marg` · the red list (Yuvika bill 540 of 24-08, 33 days), the
pre-filled intake link, the intake's parser drops an unknown lane, a crafted scan through the REAL `_create_intake_bill` lands as Pharmacy/captured
with vendor+bill+amount, the match links it EXACT, the bill leaves the list, the month page reads "scan exact" · medicines shown (no orthotic),
send 403 until the owner's approval row, then a medicine order goes (section Medicines) · Darpan's and Bhati's cards, the three Needs-you lines,
the summary door · a sale line under an un-ticked rename maps nothing, ticked it counts (tables as the source) · the portal tile.
Negative controls on the box as it was: no page, unit medical, no Needs-you lines, no cards, plain "no scan", no red list, no prefill.
**Re-runs on the patched files:** `WALK_S404 GREEN 65/65` · `WALK_S400 GREEN 63/63` · `WALK_S402 GREEN 16/16` (their negative controls rebuilt from the
`.bak_S404` / `.bak_S400` / `.bak_S402` files). Full output: the installer's log, kept in this session.

### Two frozen-walk collisions, and how they were met (say so, never work around a gate)
- S400's walk asserts Needs you "unchanged except its own line"; the brief adds three lines. A published kit is frozen, so the S403 lines carry an
  environment opt-out `NEEDS_YOU_WITHOUT_S403=1` that ONLY the S400 re-run sets (the service never does); S403's own walk proves the lines.
- S402's walk reads `sale_check.VERSION == "1.1"`; the S403 note is in the file header, the version string stays 1.1.

### What I did NOT do, and why
- The spine is read for sales/purchases only when its gate is green and its build is under 36 hours old (today: yes → "spine"); the seven clean
  nights the brief dates 27-Sep are not a gate here — the state says which source it used.
- The 15 clinic-lane scans already in the asset app were not re-laned or matched; two of them are pharmacy bills (Yuvika ×1, Jugnu ×3 rows) and
  can be re-scanned from the screen.
- `order_rules.json` and the S225 settings are shown for approval as they stand; nothing in them was edited.
- No real order, arrival, scan or approval was made on the live data.

### Outside the brief, noticed (not changed)
- Two orthotic shelves read **negative** on the live data (ANKLE BINDER BAMBOO L and M: counted 0 on 06-Sep, sold since) — the shortage then
  reads keep + 1; the family is on the S404 rename list, so its sales are still pooled. Worth a look at the count of those two.
- 108 of the 109 purchase bills since 17-Aug have no scan; all are older than 3 days, so the month page and the scan-links page are red from
  today. Not a fault of this kit: the backlog is what the brief called dormant.
- `purchase_order_line` carries S225's `supplied/short` and now S403's `missing/billed_*`; S225's `/page/staff` still works on the same rows.

### Kit
`deploy_kits\S403_PURCHASE_ORDERS_LIVE\` — porders.py, porders.html, seed_s403.py, make_s403.py, walk_s403.py, install_S403_PURCHASE_ORDERS_LIVE.sh,
README.md, KIT_ID.txt, SUMS.md5. Ran from `/tmp/s403kit/S403_PURCHASE_ORDERS_LIVE` (md5sum -c OK before the run); the repository copy is byte-identical
(SUMS verified on the box after `git pull`). No `__pycache__`/`.pyc` in the kit. NO_PHONE_NUMBERS gate: clean. Build lock held from 06:54 IST to
the publish, then removed.

### Undo (if the owner says so)
Put back the eleven `.bak_S403_<from8>` files, remove `porders.py` and `porders.html`, `systemctl restart clinic-finance clinic-portal assetapp`,
healthz 200, read the md5s back. The seeded rows are data and harmless; `finance.db.bak_S403_20260926_071910` only if the owner asks for the data
change to be reversed.
