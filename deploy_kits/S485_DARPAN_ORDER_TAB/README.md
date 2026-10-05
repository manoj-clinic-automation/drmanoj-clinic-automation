# S485_DARPAN_ORDER_TAB — Darpan reviews the system's order list on his own page (D677)

Kit of the brief `claude_code_briefs/S485_DARPAN_ORDER_TAB.md` (Sanjeevni chat, session 295, 05-Oct-2026). K3 of the ordering plan.
No F-number.

## What, and why

Until this kit Darpan decided the day's order by printing Marg's purchase-order sheet. The system's own list (`order_proposal`,
prepared at 09:00) was made every day and shown to nobody. This kit puts that list on Darpan's own page — the second tab of
**Kal ka hisaab**, `आज का ऑर्डर` — from 09:30, and makes his **पक्का** the hand-over to reception.

- **Darpan** (three taps, nothing typed but three letters of a name): `नहीं चाहिए` / `वापस लो` on a line, `−` / `+` on a quantity,
  `+ दवा जोड़ो` (Marg's own item names; the usual supplier and lot come from the spine's purchase lines; a medicine never bought asks
  for a supplier chip), and `पक्का` per supplier or `सब पक्का`.
- **Reception**: a supplier appears on its "Order karna hai" cards only after Darpan's पक्का — through the same code path a `system`
  proposal uses (± / remove / ordered / WhatsApp, `_mark_sources`). Held lines are absent; added ones are there.
- **The owner**: his card "Who decides the order" shows three values; `order.source` reads `darpan`. One tap on that card
  ("Change to Darpan's sheet") is the way back to the Marg sheet. He can open Darpan's tab as a reader: the same list, no buttons,
  `Darpan ने पक्का किया HH:MM` per supplier.

Nothing new is computed: the lines are the engine's (S470), the order book and the call / WhatsApp / arrival flow are S454's.

## Files — patched ON THE BOX from the live bytes (`make_s485.py`, every anchor exactly once)

| file (`/root/finance/`) | FROM | TO |
|---|---|---|
| `darpan_kal.py` | 911cf637a288fad85c75e54227149633 | c45bb343ac867f322f031da94882413d |
| `darpan_kal_schema.sql` | ecc6f0c53db4ea7e48bf8e3b1120e6b4 | d7260467bd57e95d386c66cbcfa228d3 |
| `darpan_kal.html` | c20ab05d8484e37a667ddae32a4c792b | ec8b64ae8f15c232d390b5ea0b8b266d |
| `order_sheet.py` | a5408df0fac852391d5845c5ae4d8865 | 16f21a6515a1317e1f6e31cb0a280513 |
| `order_rules.py` | dac12be4c4a537d7ad2e4584a3423e6a | ee17c1872acd0c440868a915fa5014df |
| `porders_s454.py` | 3681622b11043116f40bc0d4c3b557ad | 9c463e7c326c95beb20da0829cc537cc |

- `darpan_kal.py` — `order_api_s485.py` appended: `GET /finance/darpan/kal/api/order`, `POST …/hold`, `…/qty`, `…/add`, `…/pakka`,
  `GET …/items?q=`. The page's own door (`_auth` → `_who`); writes need staff or owner. `_day_payload` is not changed.
- `darpan_kal_schema.sql` — the new table `order_darpan_edit (id, day, supplier_norm, item, action, qty, at, by)`: one row per tap.
- `darpan_kal.html` — the tab strip is live (`कल का हिसाब` · `आज का ऑर्डर` · the old greyed third tab as it was); `#order`, the
  fixed bar, the add sheet, and `order_tab_s485.js`. The owner's view keeps the two tabs, read-only.
- `order_sheet.py` — `order.source` takes `darpan`; `entries()` on `darpan` reads the day's `darpan_ok` proposals and skips a held
  line; `_mark_sources` admits `darpan_ok`.
- `order_rules.py` — the setting `order.darpan_list_time` (09:30); the tick's slot `0930` (one notice to darpan, once a day, silent
  unless `order.source = darpan` and a proposal is open); `nightly` merges a `darpan_ok` row like an `open` one; `day_summary` and
  `needs_you_lines` run on `darpan`; `send_proposal` admits `darpan_ok` and skips a held line.
- `porders_s454.py` — the "whose list" heading for `darpan`, `_valid` admits `darpan`, the owner's card shows three values.

**Data** (`finance.db`, backed up by the backup API first): the table `order_darpan_edit`; the setting `order.darpan_list_time`
seeded; **`order.source = darpan`** written through `order_rules._set_setting` (audited in `order_rule_audit`).

**Restarts** `clinic-finance` once. **Not touched:** `finance_app.py`, `porders.py`, `purchase_app.py`, `shelf_figure.py`,
`spine/spine_read.py`, `/root/portal/portal.py`, `/root/portal/tile_grants.json`, the crontab.

**Duty map** v7 (`DUTY_MAP.json` in this kit = `claude_code_briefs/DUTY_MAP.json`): one new row `darpan.order_review` — tile
"Kal ka hisaab", door `/finance/darpan/kal`, marker `आज का ऑर्डर`, due while a proposal of today is `open` on `order.source =
darpan` after the list time.

## In the kit

`make_s485.py` (the anchored patcher) · `order_api_s485.py`, `order_tab_s485.js` (the two blocks it places) · `walk_s485.py` (the
test) · `install_S485_DARPAN_ORDER_TAB.sh` · `PINS.sh` (the TO pins) · `DUTY_MAP.json` · `KIT_ID.txt` · `SUMS.md5` · this file.

## Run

On the server, holding the build lock (`/root/deploy/.claude_code_build.lock`, owner `S485_DARPAN_ORDER_TAB`):

```
bash /root/deploy/repo/deploy_kits/S485_DARPAN_ORDER_TAB/install_S485_DARPAN_ORDER_TAB.sh
```

`DRY=1` runs every gate, the build, the compiles and the whole walk and places nothing. Run again after an install it answers
`ALREADY INSTALLED`. Steps: gates → the six FROM pins → build → compile on both pythons → walk on scratch copies (red = nothing
placed) → `finance.db.bak_S485_<stamp>` and a `.bak_S485_<from8>` beside each file → place by rename → md5 read back → the table,
the list time, `order.source = darpan` → restart → healthz 200 → read back on a copy of the database as it is now → anything red:
every file back byte-identical, `order.source` back to what it was, restart, healthz.

## The walk (`walk_s485.py`, 42 checks)

On backup-API copies of `finance.db`, `assets.db` and `spine.db`, the finance app's own test client, one process per side (NEW =
the six built files, OLD = the live files). Its scratch day is today with the six real proposal rows of 03-Oct copied in as open,
found by key. Sections 1–8 and 10 of the brief and the machine half of 9; every section has a named negative control that is red
on the OLD files (the API is 404, a held line IS sent, reception's cards show the Marg sheet, no notice slot, the page has no tab).
Signed in as darpan, manoj, shavez, shivani, alisha and a login not on the unit.

Section 9 by eye (build time): the page on a scratch copy of the app, at 390 px and at desktop width, as Darpan and as the owner,
measured in a browser and read by two independent readers. What the eye found and this kit carries (the walk holds each):
- every tap on the tab is 44 px or more (`नहीं चाहिए`, `वापस लो`, `बंद करो` and the tab strip were 37–39 px);
- 12 px between `+` and `नहीं चाहिए` under it, 10 px between the supplier chips (both were about 6 px);
- `वापस लो` is no longer greyed with its held line (it looked disabled);
- the message strip sits above the fixed bar instead of over it;
- the owner's "no buttons" is decided from the answer's own `me = owner` (it had depended on which of two fetches landed first),
  and every block is open for him (a confirmed block had hidden its quantities);
- a block folds after its `पक्का` reliably (a toggle event of the blocks drawn before the tap could land while the tap was in flight
  and keep it open).

Read and left as they are (reported, not changed): the page's own header and the greyed third tab are Roman as before;
`शेल्फ 23:6` is strips:tabs as the brief rules; `मार्ग` in the add sheet's hint is the brief's word for Marg.

## Undo

Put back the six `.bak_S485_<from8>` files, restart `clinic-finance`, healthz 200, read the md5s back. To stop using the tab
without undoing the kit: the owner's card "Who decides the order" → "Change to Darpan's sheet" (`order.source = marg_sheet`);
Darpan's tab then shows the list read-only with `अभी मार्ग की शीट से ऑर्डर हो रहा है`. The table `order_darpan_edit` and the
setting `order.darpan_list_time` are harmless left in place; the database backup is needed only to remove them.

## Calls made (the brief left them open)

- `~N दिन` on a line is shelf ÷ daily sale (`days_left`); the line's own `cover_days` is the cover target and is sent beside it.
- `पत्ता` / `नग` after a count, as the brief rules (the words `returns_desk.html` uses), not `qty_words.py`.
- Supplier names stay as porders prints them (`Kedar`); more than three order-day suppliers reads `आज N सप्लायर का दिन`.
- An edit is taken only while a supplier's proposal is `open`; after पक्का the block is read-only. The engine's quantity is kept
  beside Darpan's (`qty_engine`).
- A recipient login (cash hand-over view) is refused on the order API; the owner may tap through the API, his page draws no button.
- `send_notice` gained `to`, `text`, `url`, `title`; the notice lands on `/finance/darpan/kal#order`.
- `send_proposal` skips held lines by filtering its base list once (one condition serves both loops).
- The duty row's `allowed_days` is 1.
- The read-back after placing runs the placed bytes on a fresh copy of the database (never a second process on the live one).

## Not in this kit

The three-holds-in-a-row rule (K2) that will read `order_darpan_edit`; a push subscription for Darpan (he has none today — the
notice is wired, his tab and duty row are the signal); the page's own header and the third tab, left as they were.
