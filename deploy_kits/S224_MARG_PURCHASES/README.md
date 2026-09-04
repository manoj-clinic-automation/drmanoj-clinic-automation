# S224_MARG_PURCHASES — Marg's purchases, on the box  (rev 2)

**What it is.** The pharmacy's four Marg purchase exports (BILLWISE, SUPPLIERWISE, ITEMWISE,
BILLITEMWISE) are pushed nightly from manojz through one machine door and kept in `finance.db`.
On top of them, four pages under the finance app:

| page | what the owner sees |
|---|---|
| `/finance/purchase/page/hub` | **the tile target.** Last six months: Marg bill-wise total, item-wise total **(net, after discount)**, bills, **agree / differ / no lines**, WRONG count, PROVISIONAL/FINAL, and a one-line plain-English verdict per month. Feed health (last push, exports held per type, manojz pull ok / *asleep since HH:MM IST*). Stock verification (latest computed-vs-Marg line, link to the drift page). Scan links (unmatched scans, unscanned bills). Orders (open orders, *Make this week's order*). |
| `/finance/purchase/page/month/<yyyy-mm>` | bills grouped by supplier: date, bill no, amount, item-wise total for that bill, scan link into the asset app, **Correct / Wrong** (Wrong asks amount + reason). Undated item lines. The reconciliation **per bill**: AGREES (within ₹1) · DIFFERS (listed with the difference, gross beside net, *purchase return?* when item-wise > bill-wise) · NO ITEM LINES ("item-wise export missing for <date>") · ITEM LINES WITH NO BILL. **FINALISE** for the doctor, or the exact reasons it cannot; once FINAL, a **reopen** (doctor, with reason). |
| `/finance/purchase/page/scans` | pharmacy scans in `assets.db` with no Marg bill; Marg bills with no scan; **Re-match now**. |
| `/finance/purchase/page/orders` | the order book, and the reorder plan — the S207 engine on the newest stock snapshot, the last 28 days of sale lines and the last purchase rate, per vendor. **Save as order** (doctor), status buttons, vendor phone as a `tel:` link and a *Copy this order* block (never for a viewer). Labelled *PROVISIONAL until the stock verification has run a month* while `stock_feed` holds < 28 days. |

Nothing here writes to Marg, sends to a bank or a vendor, or leaves the server (D325).

## The contract

`S224_PURCHASE_PUSH_CONTRACT.md` (working papers, S224). Door `POST /finance/purchase/api/push`,
header `X-Finance-Marg` (the same sender token stock_app takes; F-237: never `X-Finance-Cron`).
Also `/api/vendors` (name→number pairs, stored server-side only — F-185), `/api/feed` (the manojz
pull-health ping) and `GET /api/healthz` (no auth). Responses: `200 {"ok":true,"stored":bool,
"reason":"new|duplicate|superseded_older"}` · `401` wrong token · `400` malformed with reason.

Server rules, as implemented and tested:
* idempotent on md5;
* same type + same period: the LATER `export_stamp` wins, the older is marked `superseded_by`
  and drops out of the effective set (kept, never deleted);
* bill identity = (`supplier_key`, `bill_no`); date from BILLWISE first, SUPPLIERWISE second;
* lines are dated by their bill; a line whose bill has not arrived is UNDATED, shown as such,
  and re-dated the moment its BILLWISE/SUPPLIERWISE arrives;
* **item-wise money is NET** (`net_amount_p`, after discount) everywhere it is summed or shown; gross
  (`amount_p`) appears only in a column labelled *gross*. Rev 2 — rev 1 summed gross, and the owner
  saw it on the first screen: Sep ₹72,438 vs ₹80,352, Jul ₹4,76,393 vs ₹5,08,062;
* **one line set per bill.** Where two live exports both carry the same (`supplier_key`, `bill_no`)
  — ITEMWISE 28–29 Aug and BILLITEMWISE 28–31 Aug both carry bill 370 — the export with the LATER
  `export_stamp` is the bill's set and the other export's lines for that bill are ignored (kept,
  never deleted). A BILLITEMWISE line (no supplier printed) that arrived before its bill is linked
  to it the moment (`bill_no`, date) names exactly one bill;
* FINALISE (doctor only) is refused — with the reasons on the page, naming the bills — while the
  month has (a) a bill marked WRONG, (b) an undated line, (c) a bill with NO item lines, or a DIFFERS
  bill (|bill-wise − item-wise net| > ₹1) not yet marked **Correct** (an acknowledged return or
  rounding), or (d) a line set that belongs to no bill of the month.

**A finding the contract did not anticipate.** `norm()` alone cannot join the reports:
SUPPLIERWISE prints the bare name (`JUBILEE AGENCIES`), BILLWISE and ITEMWISE print
name + city (`JUBILEE AGENCIES          BAREILLY`), and when the name is long the city overflows
into the DATE column as `BA03-08-2026`. `supplier_key()` = `norm()` minus a trailing city token,
whole or truncated; the date parser strips the overflow. With it, August 2026 joins 84 = 84 bills
to the paisa across both reports. Both `marg_purchase_rows.py` and `purchase_app.py` carry the
same function, by design.

## Roles

| who | may |
|---|---|
| machine (token) | push, vendors, feed — and nothing else |
| medical **viewer** (`unit_role`) | read every page; never a phone, never a button |
| medical **maker / checker** | verdicts Correct / Wrong, Re-match, see vendor phones |
| the **doctor** = the medical unit's checker (Dr Manoj alone, S179) | FINALISE, reopen, create and move orders |

The portal tile carries `roles ["doctor"]` in code and is granted by name in `tile_grants.json`
v6 to amir, shavez, darpan, alisha, shivani. A lost grants file leaves it with the owner alone.

## Files

| file | goes to | what |
|---|---|---|
| `purchase_app.py` | `/root/finance/` | the blueprint; `init(app, db, require, unit, marg_token, assets_db, assets_url)`; tables on first request (F-303) |
| `purchase_schema.sql` | `/root/finance/` | the eleven tables, all `CREATE IF NOT EXISTS` |
| `marg_purchase_rows.py` | `/root/finance/` (and the manojz leg) | the four exports → contract rows; `payload(path, type, read_purchase=None)` |
| `patch_finance_app_purchase_s224.py` | `/root/finance/` | mount + gate + public healthz; takes the LIVE md5 as its argument |
| `patch_portal_purchase_tile_s224.py` | `/root/portal/` | the 📦 Marg Purchases tile after Stock Check; takes the LIVE md5 as its argument |
| `tile_grants.json` | `/root/portal/` | v6 = v5 + the tile for the five named |
| `walk_purchase_gate_s224.py` | `/root/finance/` | the live-shape walk through the REAL patched app and gate, on a COPY of the db |
| `selftest_purchase_app.py`, `RENDER_TEST_purchase.py` | repo only | 169 + 115 checks on the real archived exports (rev 2 adds the net/gross, per-bill and finalise checks) |
| `INSTALL.txt`, `INSTALL_REV2.txt`, `PREDICTED_PINS.txt`, `KIT_ID.txt`, `SUMS.md5`, `EVIDENCE_*.txt` | repo only | the paste (rev 1: everything; rev 2: `purchase_app.py` only), the pins, the proof |

Env on the box (optional): `ASSETS_DB` (default `/root/assetapp/assets.db`, read `mode=ro`;
absent → "asset app not reachable" and nothing else breaks), `ASSETS_URL` (default
`https://assets.dr-manoj.in`, the scan links).

## What the manojz leg must know

`marg_purchase_rows.payload(path, type_, read_purchase=None)` returns the exact POST body.
`type_` ∈ `ITEMWISE | BILLWISE | SUPPLIERWISE | BILLITEMWISE`; for ITEMWISE pass
`marg_purchase.read_purchase` from the S206 kit. Period and stamp come from the report title and
the archive file name; `md5` is of the file. Helpers: `norm`, `supplier_key`, `billno`,
`iso_date`, `paise`, `read_billwise`, `read_supplierwise`, `read_billitemwise`, `itemwise_rows`,
`name_parts`, `md5_of`. Dependencies: `xlrd` for `.XLS`, `openpyxl` for `.xlsx`, nothing else.
Send the SUPERSEDED rule's inputs honestly: every archived export, oldest stamp first — the
server sorts out which one counts.

## Rev 2 — gross vs net (04-Sep-2026, the owner's find on the first screen)

Installed rev 1 showed *bill-wise and item-wise differing in all three months*. Measured: the app
summed `amount_p` (gross); the bill-wise report is net. With `net_amount_p`, July item-wise is
₹4,77,395.66 against bill-wise ₹4,76,393 — 101 of 103 bills agree, the two that differ are the
two purchase returns (the S212 record) — and September is ₹72,437.37 against ₹72,438, all 11
agree. **August is short for a different reason:** the archive's ITEMWISE "01–26 Aug" export
stops at 21-Aug and nothing item-wise covers 22–27 Aug, so 19 bills have no lines — a coverage
gap, not arithmetic. The hub now says so in one line: *export item-wise 01–31 Aug once and this
closes.* Rev 2 changes `purchase_app.py` only; `finance_app.py`, `portal.py` and the schema are
untouched. Install with `INSTALL_REV2.txt` (one paste, self-rollback).
