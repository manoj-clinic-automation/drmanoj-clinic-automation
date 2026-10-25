# SCAN APP SYSTEM BOOK — v10 — what the scan app is, where it lives, how it is changed — brought current at the S346 close (the project's eleventh session, 24 → 25-Oct-2026)

*v10 supersedes v9 in full. §17 below is what S346 changed; v9's text (its §16 and the older text after it) stands after it, read with §17's corrections — above all §17.6's pins. No patient number, no person's figure, no vendor's amount, no secret and no number of any kind (F-185) is in this file.*

## 17 · Added at v10 — S346 (24 → 25-Oct-2026): the procedure room's orders, month end and morning screen (D773 Kits 2 and 3, D774, D782, D783)

**17.1 · Orders on the desk (S635).** `procroom.py` gives a Procedure-room paper a role, kept in `proc_paper` (`role` slip / order, the order it is against, the book page): *Dr Manoj's order* counts nothing and keeps its lines; a slip's *Against order* is pre-chosen — his newest order at most 14 days before it with no slip yet —, and *Fill the lines from this order* copies the order's lines as suggestions (nothing saved until Save; a slip nothing could be read from is filled from its pre-chosen order by itself). `sorting_desk.py`'s panel carries the role, the order select, the book page and the fill link; `_s634_post` hands its body to `procroom.save_lines(…, extra=)`. A paper re-sorted out of Procedure room loses its role with its lines (voided, kept). No rupee and no rate on the desk.

**17.2 · Orders and deliveries on his page.** `order_state()`: *ordered n days ago* · **awaiting — n days** (no slip after his days, 3 to start, under *Your list and allowances*) · **part came** with each difference · *delivered*; **no order** for a slip of Yuvika's (or with no supplier read) scanned from the floor `procroom.orders_from` (the S635 install moment, UTC) — older slips are never called "no order". *Worth a look* names both.

**17.3 · The month end (S635, his only)** `/procroom/month?ym=YYYY-MM`. *Add photos* (JPG, PNG, WEBP or PDF; the same photo twice refused), kept in the uploads folder's `procroom_month/` (never deleted; a photo taken off the month stays, struck through) and listed in `proc_photo`. Each is read in a background thread by `claude_reader.read` (unchanged); a waiting photo is called stopped only when nothing of its month was read for 10 minutes; *Read again* per photo. Matching (`match_paper`): the slip's day and supplier, then `fits()` — a photo folds into a scan another photo was checked onto only when every product of the photo is on the scan and none in a greater quantity; a photo that does not fit is always counted. The table: day · its scan (or *not scanned*, or *scanned later as B-xxxx*) · that scan's order · quantities (*same* or each difference) · rates against the last for that product and brand · the amount; **To pay Yuvika for the month**; the month's scanned slips no photo shows. *Save* puts his rates on the scan's lines, or his changed lines replace the scan's (the old kept, voided); *not scanned* is kept as a photo slip, voided if the paper is scanned later and chosen — counted once.

**17.4 · Kal ke procedures (S637; D774)** `/procroom/morning[?day=YYYY-MM-DD]` — Roman Hinglish, a manager or the owner; for the staff only while `proc.morning` is on (**on since 07:0x IST 25-Oct, the owner's switch on his page**). It reads the parent's finance database **read only** (`sqlite3 … mode=ro`, env `FINANCE_DB_FOR_SCANS`): `slip`, `slip_item`, `owner_service`, `owner_service_item`, `clinic_day_line`, `clinic_day_revenue`, `patient_ref` — yesterday's X-ray/Proc slips with a procedure; those with a Docterz procedure line that day are to fill, the rest greyed *nahi hua* (before Docterz's report, all shown). Each procedure's kit is his rate page's items (size × count, a tick, one of two), pre-filled from the last time that procedure was entered; the gloves by his allowance per procedure (`proc.gloves_cast`, `proc.gloves_ili`; the clavicle bandage is neither). Field keys `p<idx>_<k>`, so R and L of one procedure keep their own lines (`proc_use.lkey`). **One Save** writes only the slips the page showed (`refs`, hidden); a slip written after the page opened is told back (*page dobara kholein*); an unchanged slip is not rewritten; an earlier record voided, kept. *Baaki din*: the last 7 days still to fill (`CATCHUP_DAYS`) — **to be widened to October from 01-10 (S352, the parent's ask)**. `?day=` opens any of the last 60 days. Tables `proc_use_slip` (one per slip: the slip book's own id and number, `grp` the procedure groups), `proc_use` (lines with `kitkey`, `lkey`), `proc_count` (his shelf counts). No patient detail is stored.

**17.5 · Used, stock, Order now, the match (S637).** On his page: used in the period (from the morning screen), his last shelf count, the stock now (count + bought after it − used after it; gloves in pairs, bought in boxes of `proc.gloves_box`), **Order now** under the reorder level on his list, a count to type per product; the **month-end match** — casts and slabs, injections and other procedures done, and each month-end product bought per ten procedures against the year. A slip saved before Docterz's report that Docterz then does not have is left out of every count and named in *Worth a look*.

**17.6 · The ILI rule (S643; D782).** `ili_kit()`: a procedure that reads as an injection (ILI) by its group or name and has no items of its own on his rate page takes the items of the first item-bearing procedure of his injection group — the injection, one of two, and the D600 drape tick; his rate page is untouched and an item he later adds there wins. **D782:** gloves are not compulsory on an ILI — `proc.gloves_ili` is **0** (his setting); Shavez adds gloves on a slip when used. The ILI injections are bought and billed at the Sanjeevni pharmacy, billed to the procedure — here they are a count of use by name, never a procedure-room purchase.

**17.7 · Reaching it (D783).** Today: Shavez through his portal's *Asset Register* tile → the scan app's menu → *Kal ke procedures*; the owner through *Assets & papers* → *Asset Register* → the menu (*Procedure room*). The parent's **S646_PROCROOM_TILES** (`portal.py`, `tile_grants.json`) adds a direct tile for each; its FETCH line in Shavez's *Aaj ka kaam* will read this app's count door `GET /scanapp/procroom/morning/api/open` (`{ok, open, text}`; no `open` when refused or signed out) — **to be built at S352.**

**17.8 · Pins at v10.** `procroom.py` `7b936d6f` (S643; DECLARED-PENDING until the 26-Oct bundle; S637's `ad0815e1` confirmed by the 25-Oct bundle) · `sorting_desk.py` `ca9fda74` (S635, confirmed) · unchanged: `asset_register.py` 068440f7 · `clinic_papers.py` 89a3cd0a · `claude_reader.py` 10118909 · `claude_reread.py` ed7023d2 · `asset_machine.py` 7dbd5e0c · `stationery.py` b6ce217a · `batteries.py` bb082b4c · `xray_costs.py` 5823bae2. Undo lines: each kit's README (`deploy_kits/S635_PROCROOM_ORDERS/`, `S637_PROCROOM_MORNING/`, `S643_ILI_KIT/`).

**17.9 · Open.** The count door and October's *Baaki din* (S352, first); F-1003 (the reader's size limit — the month end's photos too); D761's clearer duplicate; the reviews' small points (Runbook v267 §2C item 5); F-1013 (orthotics on clinic slips, flagged).

# SCAN APP SYSTEM BOOK — v9 — what the scan app is, where it lives, how it is changed — brought current at the S345 close (the project's tenth session, 23 → 24-Oct-2026)

*v9 supersedes v8 in full. §16 below is what S345 changed; v8's text (its §15 and the older text after it) stands after it, read with §16's corrections — above all §16.5's pins. No patient number, no person's figure, no vendor's amount, no secret and no number of any kind (F-185) is in this file.*

## 16 · Added at v9 — S345 (23 → 24-Oct-2026): the procedure-room goods, Kit 1 (D773)

**16.1 · The part.** `/root/assetapp/procroom.py` (S634), mounted by one guarded hook at the foot of `asset_register.py` after `sorting_desk`; absent or broken, the app runs as before (no menu item, no desk panel). Its tables (additive, its own `ensure()` at mount): `proc_item` (name, unit, how counted — per patient / month-end match / allowance —, state — in use / rarely used / retired —, brands, other spellings, reorder level, order), `proc_slip` (a slip known only from his photo: day, supplier, note; voided, never deleted), `proc_line` (a paper's line — keyed on the bill's id and `created_at`, never on `bill_items.id` — or a photo slip's: name, brand, quantity, unit, product or none, *ask*, **place**, the rate read from the paper `rate_read`, **his rate** `rate`; a re-save voids the old lines and writes new ones). His list was seeded once by the installer (30 products, the key `procroom.seed_s634`); he added *Disposable needle 18 No* (31).

**16.2 · The desk.** With *Procedure room* chosen, the box **Procedure room lines** (in English, as the desk is): each line read from the paper, pre-chosen by its words or other spellings (a suggestion; an orthotic word pre-places the line at Sanjeevni), its quantity, brand and place — Procedure room · Home use (Dr MK) · Clinic equipment · OT (surgery cases) · Sanjeevni (orthotics, flagged on his page). A Procedure room line needs a product or *Not on the list — for Dr Manoj*; a line kept elsewhere may carry its name only; *+ Add to the list* is the owner's alone. An untouched suggestion with no quantity read is left out and said so (never blocks the Save). **No rupee and no rate** in the box or in the JSON a manager receives for a paper in Procedure room, suggested to it, or Yuvika's (the stationery panel is not sent for those); an unsorted, unsuggested printed bill of another supplier still carries S568's stationery panel (by decision). His rate follows a line by its number and product across later Saves, and a rate he cleared stays clear. A paper re-sorted out of Procedure room has its lines voided.

**16.3 · What counts.** Computed when read, by `stationery._paper_sql`'s own rule for the group *procedure*: a paper's lines while it is a live paper in Procedure room or a challan / estimate joined into one; a bill only when no challan / estimate is joined into it; a photo slip's lines while it is not voided. The month is `clinic_papers.MONTH_OF` (the papers page's own); the day shown is the bill's date when it is a date, else the IST scan day.

**16.4 · His page** `https://followup.dr-manoj.in/scanapp/procroom` (the owner only; `?ym=YYYY-MM`, `?fy=YYYY`): *Worth a look* (a rate changed for a product and brand; orthotics on clinic slips; lines without a rate; lines waiting for his list) · By product · By month for the financial year (slips, scanned, only a photo, Procedure room, all places) · Kept elsewhere · Slips and their rates (a rate box per line; *Void* on a photo slip) · *+ A slip from a photo* (or *Scanned as B-xxxx*: the lines onto that paper, which must be in Procedure room) · Rarely used and retired · His list (add, edit, rarely used, retire, in use) and the gloves allowance (`proc.gloves_cast`, `proc.gloves_ili`, `proc.gloves_box`). Doors: `POST /procroom/item`, `/slip`, `/rates`, `/void`, `/allow` — all the owner's. The April–September 2026 history is in (entered through these doors from his browser).

**16.5 · Pins at v9.** `sorting_desk.py` 43658394 · `asset_register.py` 068440f7 · `procroom.py` a641f640 (new) — equal to the 24-Oct bundle; the rest as §15.6. Undo: the kit's README (`deploy_kits/S634_PROCROOM_LIST/`).

**16.6 · Open.** Kit 2 (the order scan, order ↔ delivery, the month-end WhatsApp check) and Kit 3 (Shavez's next-morning screen, use, stock, *Order now*, the month-end match) — at his word after 22:30 IST 24-Oct. B-0176 waits on the desk.

---

*(v8's header, retained:)*

# SCAN APP SYSTEM BOOK — v8 — what the scan app is, where it lives, how it is changed — brought current at the S341 close (the project's eighth session, 22 → 23-Oct-2026)

*v8 supersedes v7 in full. §15 below is what S341 changed; v7's text (its §14 and the older text after it) stands after it, read with §15's corrections — above all §15.6's pins and §15.7's open items. No patient number, no person's figure, no vendor's amount, no secret and no number of any kind (F-185) is in this file.*

## 15 · Added at v8 — S341 (22 → 23-Oct-2026): the battery page made clean, the X-ray year, the Machines list holds machines (D766 … D769; F-1003 … F-1005)

*Both kits of S341 were built, walked and rehearsed **in the chat** (D765) and read cold by an independent reviewer before the publish — S632 three times (two blockers found and fixed, the second introduced by the first fix: F-1005), S633 once with a re-read of its corrections. The data was put right through the pages' own doors in the owner's logged-in browser, at his word; sub-agents read the screens and the papers; the scans moved browser-to-server, never through the assistant's workspace (D656).*

### 15.1 · Batteries: correct or remove a saved battery; one bill for many (S632, D766)

- **`POST /batteries/fitfix`** (`fix_fit`, owner only) — the *Correct a battery entry* card on a place: a saved fitting's fitted / taken-out dates, supplier, make, Ah, set, warranty months, price and old-battery amount; only the fields sent change. Dates are checked against the page's own order of the place's fittings (neighbours taken from the list as it stood before the change).
- **Entered by mistake — remove:** sets `voided_at` (kept, never deleted); the previous entry is put back in use, or runs on to the next one's fitting.
- **One paper may be the bill of more than one battery** (the old refusal removed); its cost then reads *(the whole bill)*.
- `sup1` treats `B.L.Computers` as B.L. Computers; a fifth group **`machine` — Machine batteries** (a machine's own battery, e.g. the FDR detector's, no UPS backup check); *Change this place* takes the group, the upkeep and its months; the linked machine record's scans shown on the place (owner); *yours only* printed once; `confirm()` texts read from data attributes; a new machine-group place starts with a blank supplier; the desk's offer pre-selects a place only when one payer holds the paper.

### 15.2 · X-ray costs: the financial year from April (S633, D767)

- **This financial year** (open at the top): April (`FY_START_MONTH`) → the current month, one row per month — films, AMC and service, batteries, papers marked, total; the current month bold; the year's total.
- **Spread:** an AMC / CMC / insurance cover with a cost is spread evenly over its months (`_span`, `_s633_spread`; the last month takes the paise left over); a cover with a cost and no till-day says *not spread*. A battery's price less the old battery's amount is spread over its place's usual life, or to its taken-out month.
- **Film purchases by size** (`film_ledger`): every film bill of the year, oldest first — date, size, boxes, rupees, and the running boxes and rupees of that size; a size summary with the per-box price (none when a line has no amount — `noamt`).
- **Film lines on a Machines record** (`POST /xray/film`, owner; table `xray_film_line`, additive, made at mount): a record that looks like a film bill takes its lines and counts with its date's films; a record that is also a desk film paper counts there, once (`_desk_twin`, `_counted_film`); a film record's own bill is not counted again under Papers marked (`fa_bills`).

### 15.3 · The Machines list holds machines (D768, data)

- Before the sorting desk (August) a scan could only be kept as a Machines record, and a machine's purchase price is never counted — so consumable bills kept there were outside every count (F-1004).
- Such a bill becomes a desk paper through **Add a paper from a file** (`/desk/add` — the record's scan fetched and posted by the owner's browser), is read or typed through the paper's own Edit form, saved to its section by the desk's own Save, and only then is the record deleted at the owner's word.
- **Rule:** the Machines list holds machines; a bill of a consumable is a desk paper. An AMC record (record 13, the digital X-ray's) stays — it is a cover's record.

### 15.4 · The reader's size limit (F-1003, OPEN)

- A phone photo over about 4.5 MB returns *"read failed"* from the reader, and *Read again* fails the same way. Until a fix: type the header and lines through the paper's Edit form. The fix (a smaller copy for the reader, the stored scan unchanged — or the paper saying *too big to read*) touches the shared `claude_reader.py` / `claude_reread.py`: a PLANNED line first.

### 15.5 · Procedure-room consumables — mock-up, NOT BUILT at v8 (D769)

- The owner's need: a product list against which a challan's quantities are entered, because the handwriting is often unreadable by Claude or Sarvam.
- **Mock-up** (Design artifact `3Doc4wew9qUonpFxZtDD7W`; its files in `03_WORKING_PAPERS\S341\`): (1) on the sorting desk, for a Procedure-room paper — *Procedure room items on this paper*: a product picked from the list, the quantity typed, the unit, the rate from the bill when it comes; the reader's reading shown grey as a hint; *+ Another line*, *+ A product not on the list*; saved with the desk's own Save. (2) The owner's *Procedure room consumables* page — the year's total, products on the list, challans still without quantities; by product (unit, usual supplier, bought, rupees, last rate); each product's every purchase with its running total; *+ Add a product* (renamed or retired, never deleted once used).
- **Waiting on the owner:** only what is bought, or a shelf count too (like stationery)? the gloves' size? — then *final*. Installed switched off.

### 15.6 · Pins at the S341 close (all confirmed by the 23-Oct bundle)

`batteries.py` bb082b4c · `xray_costs.py` 5823bae2 · `asset_machine.py` 7dbd5e0c · `stationery.py` b6ce217a · `clinic_papers.py` 89a3cd0a · `asset_register.py` 2bb28600 · `sorting_desk.py` 377adbca · `scanner_widget.js` b936f0f3, `claude_reader.py` 10118909, `claude_reread.py` ed7023d2 (the Sanjeevni chat's, unchanged). **This project's DECLARED-PENDING: 0.** **Drift:** `batteries.py` 4 (the next patch reads it whole and consolidates first), `xray_costs.py` 1, `asset_register.py` 1, `sorting_desk.py` 1, `clinic_papers.py` 3, `stationery.py` 2, `asset_machine.py` 2.

**The way back:** S633 — `\cp /root/assetapp/xray_costs.py.bak_S633_22e59f5a /root/assetapp/xray_costs.py` (the `xray_film_line` rows stay; additive); S632 — `\cp /root/assetapp/batteries.py.bak_S632_b2cbb41e /root/assetapp/batteries.py` (the fixes made through `fitfix` stay as data); each then `systemctl restart assetapp`. The order back is S633 → S632, then v7's.

### 15.7 · Open at the S341 close

- **D769 — procedure-room consumables** (the next chat's first job, after the owner's two answers and *final*).
- F-1003 — the reader's size limit.
- Records 45, 46, 50 — deleted at the owner's word once his lab consumables bills from April 2026 are on the desk.
- S633's minor points: a film line with no amount; a twin that is an awaiting challan later joined; the *not spread* words; sizes in centimetres; film records with no purchase date not flagged.
- Waiting on papers, never guessed: the Vento's battery; the DTH lab's online UPS battery (B.L. Computers' bill); the second Panasonic AC's bill.
- Carried: D761's keep-the-clearer-scan rule (`_mark_dup`, `scan_checks_s441.answer`); B-0163 Rs 0 until its bill; *Many items on one screen* OFF until his tap; `misread_date` 400 days vs the month rule's 12.

---

*(v7's text follows, whole.)*

# SCAN APP SYSTEM BOOK — v7 — what the scan app is, where it lives, how it is changed — brought current at the S337 close (the project's seventh session, 22-Oct-2026)

*v7 supersedes v6 in full. §14 below is what S337 changed; v6's text (its §13 and v5's whole text after it) stands after it, read with §14's corrections — above all §14.7's pins and §14.8's open items. No patient number, no person's figure, no vendor's amount, no secret and no number of any kind (F-185) is in this file.*

## 14 · Added at v7 — S337 (22-Oct-2026): four kits built in the chat (D756, D764, D765; F-976 … F-980)

*Every kit of S337 was built, walked and rehearsed **in the chat** — not by the API-credit runner — at the owner's word (D765, 14:07 IST: "do the previous session pending build inside this chat only. Do not use API for this"). Each was read cold by an independent reviewer (a sub-agent of the chat, given the code and the requirements, not the builder's conclusion) before the publish, and every blocker and correction was fixed in place. Facts below are read from the kits in `deploy_kits/` and the session's live reads.*

### 14.1 · The Variety challans as stationery history (S623, D756; live 14:42)

- Data only, `history_s623.py` in its kit: the six Variety Stationers challans (B-0003, B-0013, B-0109, B-0114, B-0133, B-0163) as `stationery_line` rows in `save_lines`' exact shape; **one day and one 12:00 IST time per paper** (the challan date — all before the 18-Oct counts, so the nine counted stocks stand); line numbers = each paper's reading position, checked on the box by a word and the quantity; B-0013's ring file and token re-written (token 100 → 1); gates per paper; one transaction with a stock guard (every item moves exactly as its lines account for); `by_whom` *history (Variety challans, S623)*; the key `stationery.history_s623`; `--undo` (voids, never deletes; marks the key *undone*; leaves a paper a person re-saved or took off Stationery) and `--verify`.
- Live: A4 paper 21, File folder DC-217 3, X-ray envelope 500, Token 1; October fed by B-0109, B-0114, B-0133, B-0163.

### 14.2 · Batteries: *Out of warranty* (S624, F-977)

- `batteries.place_view`: a battery past its warranty and not yet at its usual life reads **Out of warranty since dd-mm-yyyy** (grey), never OK. *Due for replacement*, the 30-day warranty amber, *Bill awaited* and upkeep keep their order before it.

### 14.3 · Machines: a cover's or a part's paper afterwards (S624, F-978)

- `asset_machine._row_paper` and two routes: `POST /assets/<id>/covers/<cid>/paper` (`s624_cover_paper`) and `POST /assets/<id>/parts/<pid>/paper` (`s624_part_paper`) — the spends' link box copied; the `_writer` gate (owner; a manager only while `machine.on`); `paper_from_box`'s refusals (pharmacy, a patient's, a copy, a page); the fingerprint `bill_created_at`; a voided cover and a removed part refused. B-0203 linked to the FDR machine's AMC cover by it.

### 14.4 · Stationery: packets of N (S624, F-979)

- `stationery.pack_of`, `pack_check`: a line in pieces (or no unit) whose quantity is a whole multiple of an item counted in *packet of N* — the desk Save's words say *"Check: … type <packets> instead and Save again."*; the owner's Stationery page marks *check the quantity (B-____)* for this month's such lines. Nothing is changed in the stock; the desk's own JavaScript (in `sorting_desk.py`) is unchanged by design.

### 14.5 · The month: a bill counts in its own month; the day is kept; the late mark (S625, S627; D764)

- **The one rule** — `clinic_papers.MONTH_OF`, read by The month, the desk's lists and rates, X-ray costs and stationery. Switched by `settings papers.month_from_bill_date` (the install moment, UTC `datetime('now')` form; date-shaped only; absent or `off` = the old rule). A paper scanned since then whose `bill_month` is its IST scan month (the intake's default) and whose bill is dated in an earlier month, not more than 12 months back and never later, counts in **the bill's own month**. A person's earlier month still wins. **A person's choice of the scan month does not hold a back-dated bill there** (the owner's open question, F-1002).
- **The paper's own page** says *"Month: July 2026 (the bill's own date — scanned as October 2026; to count it elsewhere, choose an earlier month below or correct its date)"* (`asset_register._s625_counts`).
- **The day** — `asset_register._s625_keep_day` in `asset_edit`: the form's month/year dropdowns keep the record's own day when the month and year are unchanged (purchase, cover start, EMI start). A new machine, or a changed month, takes the 1st as before.
- **The late mark** (S627) — `asset_register._set_late` (run after every reading, every desk Save and every date or month change) marks a paper the rule counts in an earlier month than its IST scan month `late_for` that month; `heal_s627.py` filled the empty marks of papers scanned since the switch-on; the desk's *The month* page states the rule.
- **Seen by the reviews, not changed:** the desk's challan amber and pre-tick follow the bill's month now; `misread_date` allows 400 days back, the rule 12 months; the purchases page's late count counts scans.

### 14.6 · The real scan app in the chat's own workspace (how S337 walked)

- `asset_register.py` at its live byte is rebuilt from the kit that last moved it (S618's `make_s618.py` edits on the bundle's FROM byte gave `70e35b10` exactly); with the six parts (`clinic_papers`, `sorting_desk`, `asset_machine`, `stationery`, `batteries`, `xray_costs`) it imports and serves under Flask's test client on a made-up database (`ASSETS_DB`, `ASSETS_UPLOADS`, a made-up key file, `read.claude` off). A fresh database lacks columns later kits' data steps added on the box (`bills.page_of`, `bills.mixed`) — the walks add them on their scratch copy.
- Each kit's `walk_*_app.py` runs the same way on the box, on a COPY of the live database, with made-up rows dated 2031, and its control on the FROM files must go red.

### 14.7 · Pins at the S337 close (each the installer's read-back; DECLARED-PENDING until the 23-Oct bundle)

`batteries.py` b2cbb41e · `asset_machine.py` 7dbd5e0c · `stationery.py` b6ce217a · `clinic_papers.py` 89a3cd0a · `asset_register.py` 2bb28600 (S625 f21ae7ca → S627) · `sorting_desk.py` 377adbca · `xray_costs.py` 22e59f5a (unchanged) · `scanner_widget.js` b936f0f3 and `claude_reader.py` 10118909 (the Sanjeevni chat's S618, unchanged here). **Drift:** `asset_register.py` 1 and `sorting_desk.py` 1 (both read whole on 22-Oct by the reviews).

### 14.8 · Open at the S337 close

- **D766 — the battery page made clean** (the next chat's first job: read every place, fitting, paper and field through the owner's browser; fix data through the page's own doors; a kit for code; ask only for what no paper shows).
- Asset 12 (the retired duplicate battery record) — the owner's question; asset 7 deleted by him.
- F-1002's question (the scan month on a back-dated bill).
- D761's rule for this project's files (keep the clearer scan of a duplicate — `_mark_dup`, `scan_checks_s441.answer`), from the Sanjeevni chat.
- The handwritten challans of the clinic lanes read by Claude (from the Sanjeevni chat, 19-Oct).
- Carried from v6: the X-ray page and Jasoria's old-battery amount; B-0163 Rs 0 until its bill; *Many items on one screen* OFF until his tap.

---

*(v6's text follows, whole.)*

# SCAN APP SYSTEM BOOK — v6 — what the scan app is, where it lives, how it is changed — brought current at the S323 close (the project's sixth session, 18 → 22-Oct-2026)

*v6 supersedes v5 in full. §13 below is what S323 changed; v5's text stands whole after it, and its §12.5 (S575 "not built"), §12.6 switches, §12.8 pins and §12.10 open items are read with §13's corrections. No patient number, no person's figure, no vendor's amount, no secret and no number of any kind (F-185) is in this file.*

## 13 · Added at v6 — S323 (18 → 22-Oct-2026): the battery setup, X-ray costs, many stationery items (D736, D738, D756)

*Every kit of S323 went through the same steps as S318's: built by the parent's Agent SDK runner (`D:\Downloads\_kbtools\agent_build\run_build.py`, D727) on the owner's API credits; its brief read cold first (R1, binding in v2); the kit read cold before the publish (K1 SAFE); published by his double-click and installed by his one server line. The facts below are read from the kits in `deploy_kits/`, the runner's reports `claude_code_briefs/REPORT_S575/582/585.md`, the 22-Oct bundle and the session facts of the S323 chat.*

### 13.1 · Battery first setup (S575, 18-Oct ~09:4x; S571's open item closed)

- **Old battery — no bill** (and **no card** on the Jasoria form): stored in S571's own columns as `bill_id=NULL`, `bill_created_at='none:old-battery'`; any past date up to 15 years back, never the future. No *bill awaited* badge, no B.L. reminder, not in the awaited total; the desk does not offer it a new B.L. paper. The history reads *"no bill (old battery)"*. A bill can still be linked later from *The battery now — its papers*.
- **Show older / other papers** (any supplier, any date, the desk's visibility rules, at most 300) and **Find by stamp** (B-0162, B162, b-162 through `sorting_desk._s566_stamp_form`); one refusal line for every case; `candidates()` and `_pickable()` unchanged.
- **How many batteries? — set** for an online UPS with no count (owner only); *set of N* shows once known.
- **First setup** (owner only): every place with no battery recorded, one line each (Fitted on, Batteries in the set, Bill).
- **The data as the owner entered it (his browser, as owner):** 16 places — 14 fitted; the Vento and the DTH lab open (Y120). *Reception PC* → **Medical PC**, *Second PC* → **Lab PC**. A new place **X-ray detector (FDR) battery** in the Online UPS group (its fitting's bill is B-0204). The Digital X-ray set of 8 fitted 28-04-2026 (by his server line of 12:43 IST 18-Oct; backup `assets.db.bak_S323_xray`); the NK Pathology and DTH lab sets of 3. Each place linked to its machine record; machine records 7 and 12 retired as duplicates.

### 13.2 · X-ray costs (S582, 18-Oct ~16:1x; D736)

- **The ruling (D736):** a paper keeps its one group AND may be counted for the X-ray department; each rupee once.
- **Where:** `https://followup.dr-manoj.in/scanapp/xray` (`xray_costs.py`, NEW; mounted by `batteries.py`, guarded — a failure leaves the Batteries pages as they were). **Owner only**; in the menu right after Batteries. Routes `/xray` and `/xray/mark`.
- **The page:** *X-ray expenses — <Month YYYY>*, previous / next month, *₹ this month · ₹ since <the first month>*, and four folds:
  - **X-ray films** — The month's own *X-ray films* section, through `sorting_desk`'s own selection and sum;
  - **Papers marked for X-ray** — marked by stamp; counted only when The month counts the paper, in The month's month; otherwise listed *not counted: <why>*; a Personal paper shows but does not add;
  - **Machines marked for X-ray** — their service / repair spends and their covers (never the purchase price); a date that is not a full date is listed under *Date not read*;
  - **Batteries of the X-ray places** — each fitting's price by its fitted date.
- **The ticks:** *Machines — which count for X-ray* and *Battery places — which count for X-ray*; likely ones are listed first as *looks like X-ray — tick to count*; **the system never ticks one** (D664).
- **Each rupee once:** a counted spend, cover or fitting claims its paper only when the paper's fingerprint matches; a claimed paper shows at no amount; two rows on one paper both say *check*.
- **A mark never changes a paper, machine or battery place** — only `xray_mark` (kind, ref_id, ref_created_at; one live mark per record) is written, every mark audited in `desk_audit`.
- **The data:** marked B-0163 and the places *Digital X-ray* and *X-ray detector (FDR) battery*; the FDR AMC ticked by the owner.
- **Seen, not built:** Jasoria's old-battery amount is not netted; B-0163 adds Rs 0 until its bill comes.

### 13.3 · Stationery — many items on one screen, X-ray, Void, Shavez's sheet (S585, 18-Oct ~17:00; D738)

- **The opening stock** is the owner's first count of 18-Oct 14:5x IST (nine items: Register 192 / 104 / 72 pages, Copy — Classmate 72 pages, Small copy — Anmol 96 pages, Clear bag (economy), Clear bag (premium), Ring file RBU-400, Cheque book folder). The list holds 13 items; the two copy items carry their sizes since 22-Oct (D756). Variety Stationers is *A bill now and then*.
- ***Stationery diya*, many items** (staff, Roman Hinglish, the owner's mock-up `claude_code_briefs\S585_MOCKUP_Main.dc.html` as the specification): *1 · Kisko diya?* (Lab · Reception · Sanjeevni · Clinic · **X-ray**), *2 · Kya aur kitna diya?* (every active item with its shelf stock, − / number / +), ONE *Save karo (N)* — all or none, through the existing `issue()`. Behind **`stationery.many`, absent = OFF**; the switch is a card at the top of the owner's Stationery page (`POST /stationery/many`), not on the *Switches* card. OFF, the one-item screen is S568's byte for byte; ON, it stays at `/stationery/diya?one=1`.
- **X-ray is a place** everywhere issues are counted.
- **Void** (owner only): a line stays, struck through, audited, and leaves the stock; voiding an issue made before the latest count does not change the stock (said on the page). *Show all issues* lists earlier months.
- **Shavez's sheet:** seven history issue lines (`by_whom` `history (Shavez sheet)`, done-key `stationery.history_s585`), each one second before its item's opening count, so the opening stock stands; in their own fold *Earlier issues — from Shavez's sheet (no date)*, never in this month's figures.
- **Papers to the group (his word):** B-0003, B-0013, B-0109, B-0114, B-0133, B-0163 in *Stationery & packaging*. *Stationery diya for managers* (`stationery.issue_on`) ON.

### 13.4 · The FDR AMC and two back-dated bills (19 → 22-Oct, data only)

- The **FDR AMC cover** on machine 13 (AMC, Fujifilm India Pvt Ltd, 19-07-2026 … 18-07-2027, remind 30 days).
- **B-0203** — the Fujifilm AMC quotation standing as the bill (*Clinic equipment*, dated 14-07-2026, paid 14-07-2026 by NEFT, its month set to **July** by hand).
- **B-0204** — the Shail Healthcare battery tax invoice (dated 07-08-2026, paid 14-07-2026 by NEFT, month set to **August** by hand), linked as the FDR battery fitting's bill.
- The AMC's GST tax invoice was asked for by email from the owner's personal Gmail (~10:4x IST 22-Oct); scanning it is his (Y121).

### 13.5 · The Variety challans as history — briefed, NOT BUILT at v6 (S623, D756)

- **The ruling (D756, 22-Oct 06:31 and 12:09 IST):** the six Variety challans entered as received history dated on each challan, before the opening count; *A4 long notebook 192p* = Register 192 pages; *Copy Anmol* = Small copy — Anmol 96 pages (24 × 18 cm), the 72-page copy is Classmate (24 × 18 cm); *My Clear Bag* = Clear bag (premium); the NK Pathology estimate books stay out; the token line = 1 packet.
- **Kit S623_STATIONERY_CHALLAN_HISTORY:** brief v2 `claude_code_briefs\S623_STATIONERY_CHALLAN_HISTORY.md` (`aada3d74`); R1 `03_WORKING_PAPERS\S323\S623_BRIEF_R1.md` (`8cfeea39`, binding). PLANNED on `stationery.py` `18268ff0` + the `assets.db` data step. Prefer no code change. One stamp per paper (its challan date 12:00 IST; B-0013's two existing lines restamped to it); each new line takes its paper's own reading line number; every row marked `history (Variety challans, S623)` with an `--undo`; the token fix = void + a new line of 1; each line its item's own unit; a paper not in *Stationery & packaging* is skipped and printed; done-key `stationery.history_s623`. 13 new lines plus the token fix; the four uncounted items checked by their move.

### 13.6 · The switches at v6

| switch | where | state at v6 |
|---|---|---|
| `stationery.many` — *Many items on one screen* | the card at the top of `https://followup.dr-manoj.in/scanapp/stationery` (owner only) | **absent = OFF** (Y119) |
| `stationery.issue_on` — *Stationery diya for managers* | the *Switches* card, `https://followup.dr-manoj.in/scanapp/` | **ON** (his tap, S323) |
| `desk.on`, `machine.on`, `batteries.on` | the same card | not changed by S323's kits (v5 §12.6) |
| `scan.cv`, `scan.lanes5` | the same card | ON |
| `read.claude` — Claude reading | `https://followup.dr-manoj.in/scanapp/admin` | on while the key and the credit hold |

### 13.7 · Pins, drift and the way back at v6

| file | pin | rests on | drift |
|---|---|---|---|
| `/root/assetapp/batteries.py` | `775471e6f7f4b8356142aafccdccfddd` (S582) | equal to the 22-Oct bundle | 2 (S575, S582) |
| `/root/assetapp/xray_costs.py` | `22e59f5a275d687bae767da8bf776a6a` (S582, NEW) | equal to the 22-Oct bundle | 0 |
| `/root/assetapp/stationery.py` | `18268ff04b37af8143be1e3395ec5854` (S585) | equal to the 22-Oct bundle | 1 (S623 planned) |
| `/root/assetapp/sorting_desk.py` | `110335eac5a9792ebe52620ee676a13c` | equal to the 22-Oct bundle | **8** since S551 — read whole before the next patch |
| `/root/assetapp/clinic_papers.py` | `6db07c12a8ba5ab0123db2a5bee0fa7b` | equal to the 22-Oct bundle | 2 |
| `/root/assetapp/asset_machine.py` | `7d4fdffce01a28fd7e5cc2c4f2aeeb74` | equal to the 22-Oct bundle | 2 |
| `/root/assetapp/asset_register.py` · `scanner_widget.js` · `claude_reader.py` | moved by the Sanjeevni chat's **S618** (10:54 IST 22-Oct; its kit names TO `70e35b10…` · `b936f0f3…` · `10118909…`) | that chat's board line and the 23-Oct bundle | `asset_register.py` **8 + 1** — over the line |
| `/root/shared/scan_quality.py` | NEW by S618 (`16fb2402…`) | that chat's | — |
| `/root/assetapp/claude_reread.py` | `ed7023d22e725b5f4e0a700494059e2b` (S601) | equal to the 22-Oct bundle | — |
| `/root/finance/packs.py` (the parent's) | moved by the parent's S621 / S622 from `e46264b8` | the parent's board line | the parent's |

**The way back.** Each kit's README carries its one undo line; the order back is **S585 → S582 → S575**, then v5's. S585's undo copies `stationery.py.bak_S585_d11d7183` back — and, BEFORE it, `python3 -B /root/assetapp/stationery.py --history-void <assets.db>` voids Shavez's seven lines (`voided_by` `undo S585`, never deleted) if they must leave the page; S582's copies `batteries.py.bak_S582_40eb8a91` back and moves `xray_costs.py` aside (`xray_costs.py.undone_S582`); S575's copies `batteries.py` back. All end with `systemctl restart assetapp`, typed with `\cp -p` past the alias. `xray_mark` and the owner's entered data stay after an undo (additive).

### 13.8 · The API credit and the runner

- **USD 185.48 at 06:4x IST 18-Oct, valid to 18-Nov-2026** (v5 §12.7). The runner spent **USD 25.74** on S323's three kits by its logs: S575 8.79 · S582 9.87 · S585 7.08.

### 13.9 · Kit history, continued

S575 (18-Oct, publish `349d774a` 09:33, installed ~09:4x) · S582 (publish `52d2ed05` 16:18, installed ~16:1x) · S585 (publish `7dc19cf1` 16:59, installed ~17:00) — each after an independent cold review (K1 SAFE). S623 (22-Oct) briefed and reviewed, not built.

### 13.10 · Open at v6

- **This project's:**
  - **S623** (§13.5) — the runner line, K1, the install, the live read;
  - **F-976** the machine Edit form resets the purchase day to 01 · **F-977** a battery past its warranty shows OK · **F-978** no door to link a cover's paper afterwards · **F-979** the stationery match ignores the item's unit · **F-980** a back-dated bill counts in its scan month;
  - the X-ray page does not net Jasoria's old-battery amount; B-0163 adds Rs 0 until its bill comes;
  - `sorting_desk.py` and `asset_register.py` read whole before their next patch;
  - carried: the old `/papers/month` page's held double; F-909's note; D720; S532's placed papers.
- **The parent's:** `packs.py` (S621 / S622); the portal tile; the clinic's purchase bills into the pack (waits by his word); Shavez's sorting duty.
- **The Sanjeevni chat's:** S618's scan-app files; medicine suppliers' challans and bills (D689 item 2).
- **His:** Y119 *Many items on one screen* ON when happy · Y120 the Vento and DTH lab battery dates · Y121 Fujifilm's tax invoice · the remaining *Switches* taps for Shavez · Y83 · the DTH lab's payer, only if he raises it.

---
*(v5, retained whole below — read with §13's corrections.)*

*(v5 H1, retained:)* SCAN APP SYSTEM BOOK — v5 — what the scan app is, where it lives, how it is changed — brought current at the S318 close (the project's fifth session, 15 → 18-Oct-2026)

*v5 supersedes v4 in full. §12 below is what S318 changed; v4's text stands whole after it, and its §11.8 switches, §11.11 pins and §11.13 open items are read with §12's corrections. No patient number, no person's figure, no secret and no number of any kind (F-185) is in this file.*

## 12 · Added at v5 — S318 (15 → 18-Oct-2026): four kits live, batteries and stationery (D730)

*Every kit of S318 went through the same steps:*
- *built by the parent's Agent SDK runner (`D:\Downloads\_kbtools\agent_build\run_build.py`, D727) on the owner's API credits;*
- *its brief read cold first (R1, binding in v2);*
- *the kit read cold before the publish (K1, then a fix round in place and K2 where K1 asked for one);*
- *published by his double-click and installed by his one server line.*

*The facts below are read from the kits in `deploy_kits/`, the runner's reports `claude_code_briefs/REPORT_S563/566/568/571.md` and the 18-Oct bundle.*

### 12.1 · The tidy round (S563, 15-Oct ~19:08)

- **F-902:** a set-aside paper shows *"Already set aside on <date> — Restore?"* on the desk. One shared restore (`POST /desk/api/restore`, audit `desk_restored`) returns it to Waiting, never straight to accepted.
- **The old *Bills awaited* page** (`clinic_papers.py`) filters a patient's or a Personal challan, as the desk does.
- **The owner's Delete** of a receipt or statement voids the payment that paper proves and clears `assets.bill_id`.
- **A statement** pays the invoices, with its total first.
- **Machines:** one machine per paper, under a lock. The stamp box refuses a copy or a page. An old AMC past its own renewal date reads *lapsed*.
- **The widget's Adjust stage** after a page is deleted (N7) — inside the intake-only branch of `scanner_widget.js`; all seven surfaces were walked.
- **`clinic_papers.py`** was read whole and consolidated (drift 6 → 0).

### 12.2 · The last fixes (S566, 16-Oct ~06:59)

- **Every waiting non-pharmacy paper reaches the desk.** B-0009 (Construction, waiting since 11-Sep) had been on no list.
- **A restored set-aside paper** of a filed-straight lane (construction, personal expense) re-enters through the duplicate check (S563 N5). A held double (D710) is never counted twice on The month or home.
- **The old challan close / delete / join doors** refuse a Personal challan to a non-owner, and any patient challan, on the server (S563 N6). A closed challan's desk Save keeps it as a record and takes it off Waiting.
- ***Bills awaited*'s count equals its rows.** Home's *Spend this month* equals The month.
- **Dates:** a date is never stored half-read (no *14/10*). The old edit page refuses only a partial date that is newly typed. *Approved by* shows only when the paper was approved.
- **Machines:** the Contract column is blank, never *None*.
- **`/scanapp/desk?open=`** takes the stamp in any common form (B-0162, B162, b-162) as well as the record number.

### 12.3 · Stationery & packaging (S568, 16-Oct ~12:15; D730 (2), (3))

- **The group:** *Stationery & packaging* is a clinic-consumables group on the desk.
- **The owner's page** is `https://followup.dr-manoj.in/scanapp/stationery` (`stationery.py`, mounted by `asset_register.py`). It holds:
  - the item list with rates (*+ Add item*; also *Add to the list* from a desk line);
  - each item's stock, its low-stock level and a rate-differs flag;
  - the optional monthly count (the first count is the opening stock).
- **Stock in:** the matched lines of a bill or challan count **once** (a bill joined to its challans adds nothing twice), and **only while the paper is still a live paper in Stationery & packaging**. Re-sorted, moved, set aside or rejected, it stops adding (K1 C1). Stock is computed when read.
- **Stock out:** the staff screen ***Stationery diya*** `https://followup.dr-manoj.in/scanapp/stationery/diya`. It follows the owner's mock-up line by line (artifact `8VXHG1F62EvN6LqBEi5e9k`, *Issue*): *Kya diya* · *Kitne* · *Kisko* (2 × 2: Lab · Reception · Sanjeevni · Clinic) · one Save → *"Ho gaya — … Stock mein ab N."* It is behind `stationery.issue_on`, **absent = OFF** for managers.
- **The mixed tick:** a challan carrying clinic and lab goods together can be marked (`bills.mixed`); the owner says the mixing will stop.
- ***Add a paper from a file*** (owner / manager, on the desk) takes a PDF or a photo only.
  - **Aumni Crafts** is filed on the pharmacy lane with kind ***Pharmacy expense*** (never *Pharmacy*), marked paid by Dr MK's card.
  - Sanjeevni's four readers (`scan_register`, `purchase_app`, `porders`, `order_sheet`) read `kind='Pharmacy'` only, so it never reaches the Marg pairing. Invoices are added by hand until the Janitor picks them up from his Gmail.
- **The accountants' pack** (the parent's `/root/finance/packs.py` `048d2ad8` → `e46264b8`, `build_bundle` only): **`COALESCE(doc_kind,'bill')='bill'`** — only bills and invoices. Estimate slips and paid-on-challan papers stay internal (D730 (3)).
- **Tables (additive):** `stationery_item`, `stationery_line`, `stationery_move`, `stationery_count`; `bills.mixed`.
- **Round 0 was cut off by a PC restart at 10:15:43 IST.** It was resumed by S568_RESUME after proving nothing live had moved (F-908).

### 12.4 · Batteries (S571, 16-Oct 14:19; D730 (1))

- **Where:** `https://followup.dr-manoj.in/scanapp/batteries` (`batteries.py`, mounted by `asset_register.py`; in the menu after Machines). Its routes are `/batteries`, `/batteries/place/<id>`, `/batteries/fit/<id>`, `/batteries/link` and `/batteries/done`.
- **15 places, seeded by name only** (F-185), in four groups:
  - **Online UPS:** Digital X-ray (clinic) · NK Pathology (paid by NK Pathology) · DTH lab (payer shown *"to confirm"* — never guessed);
  - **Small UPS:** Reception PC · Second PC · Lab analysers · Home DVR + router (owner only);
  - **Generator and inverters:** Generator · Clinic inverter (2 batteries) · Home inverter (2, owner only);
  - **Vehicles** (owner only): Carnival · Wagon R · Vento · Scooty · Bike.
- **What each place carries:** its group, payer, supplier preset, warranty months (B.L. 12; Jasoria from the card), usual life (car 42, two-wheeler 30, inverter 54, UPS 30, generator 30 months; editable) and *Set of* (the batteries in the set).
- ***New battery fitted*** (one form):
  - **B.L. Computers:** the bill comes with the battery, or the battery reads *bill awaited* until a paper is linked.
  - **Jasoria:** the price, the old-battery amount, the net, and the warranty months typed from the card.
  - **Linking a paper:** the picker lists the same supplier's papers of the last 90 days. A B.L. or Jasoria paper on the desk shows *"Battery fitted at <place> on <date> — this bill?"* and one tap links it. **Linking never changes the paper's lane, section or status (D664).**
  - **On saving,** the previous battery goes into the history with its removed date.
- **Reminders** are computed when read and shown as one ***Batteries*** card on Renewals:
  - warranty ending within 30 days;
  - usual life reached;
  - a B.L. bill still awaited after 30 days;
  - upkeep — inverter water every 3 months, UPS backup check every 3 months, generator start monthly. A *done* tap resets each.
- **A new UPS, inverter or vehicle in Machines** gets its battery place by itself, once.
- **Who sees what:**
  - the owner sees all of it;
  - managers see clinic and lab places only, and only while **`batteries.on`** is ON (absent = OFF). With it off, a manager also gets no desk offer (K1 C1);
  - a paper hidden from the viewer shows no amount and no link in a place's history;
  - reception never sees it.
- **Tables (additive):** `battery_place`, `battery_fit`, `battery_upkeep`, two indexes, and the setting `batteries.since`.

### 12.5 · Battery first setup — briefed, NOT BUILT at v5 (S575)

The owner's ask of 06:02 IST 18-Oct: *"…for many UPS, I only have a date when the batteries were renewed … Online UPS has variable number of batteries…"*

- **Kit S575_BATTERY_SETUP:** brief v2 at `claude_code_briefs\S575_BATTERY_SETUP.md` (`9cf7fc7f`); R1 `03_WORKING_PAPERS\S318\S575_BRIEF_R1.md` (`99057249`, binding). It is PLANNED on `batteries.py` `9a0054ac` only. It adds:
  - ***Old battery — no bill*** (and *no card* on the Jasoria form), stored as `bill_id=NULL`, `bill_created_at='none:old-battery'`, with any past date up to 15 years back. There is no awaited badge and no B.L. reminder, and all three "awaited" decisions honour it;
  - ***Show older / other papers*** and ***Find by stamp*** (`sorting_desk._s566_stamp_form`), under the desk's visibility rules, with one refusal line for every case. `candidates()` and `_pickable()` are unchanged;
  - ***How many batteries? — set*** for an online UPS with no count (owner only; *set of N* shows even before a battery is recorded);
  - an owner-only ***First setup*** fold, listing the places with no battery recorded, one line each.
- No data step; it restarts `assetapp` only.

### 12.6 · The switches at v5

| switch | where | state at v5 |
|---|---|---|
| `desk.on` — *Sorting desk for Shavez* | the *Switches* card (owner only), scan app home `https://followup.dr-manoj.in/scanapp/` | absent = OFF |
| `machine.on` — *Machine pages for Shavez* | the same card | absent = OFF |
| `batteries.on` — *Batteries for Shavez* | the same card (S571) | **absent = OFF** |
| `stationery.issue_on` — *Stationery diya for managers* | the same card (S568) | **absent = OFF** |
| `scan.cv`, `scan.lanes5` | the same card | ON |
| `read.claude` — Claude reading | `https://followup.dr-manoj.in/scanapp/admin` | on while the key and the credit hold |

### 12.7 · The API credit

- **USD 185.48 left, valid to 18-Nov-2026** (read from the Console at 06:4x IST 18-Oct; the 15-Oct grant; the 13-Oct grant expired on 17-Oct).
- **Claude reading** stops by itself only when the credit runs out (S550), and then Sarvam reads alone. *v4 §11.10's "after 17-Oct" is superseded by this credit.*
- **The runner** spent USD 44.97 on this project's four kits, by its logs: S563 9.67 · S566 12.42 · S568 8.58 (round 0 has no cost line) · S571 14.30.

### 12.8 · Pins, drift and the way back at v5

| file | pin | rests on | drift |
|---|---|---|---|
| `/root/assetapp/sorting_desk.py` | `110335eac5a9792ebe52620ee676a13c` (S571) | equal to the 18-Oct bundle | **8** since S551 — read whole before the next patch |
| `/root/assetapp/asset_register.py` | `c39c084eabf52daa0da9cc6720fc7aa7` (S571) | equal to the 18-Oct bundle | **8** since S551 |
| `/root/assetapp/batteries.py` | `9a0054ac073ccaa1252b426c5a9d408f` (S571, NEW) | equal to the 18-Oct bundle | 0 (S575 planned) |
| `/root/assetapp/clinic_papers.py` | `6db07c12a8ba5ab0123db2a5bee0fa7b` (S568) | equal to the 18-Oct bundle | 2 since S563's consolidation |
| `/root/assetapp/stationery.py` | `d11d718392782d4a7a8b9c233363a526` (S568, NEW) | equal to the 18-Oct bundle | 0 |
| `/root/finance/packs.py` (the parent's) | `e46264b85f22563f3e0d8643597e1d58` (S568) | equal to the 18-Oct bundle | the parent's count |
| `/root/assetapp/asset_machine.py` | `7d4fdffce01a28fd7e5cc2c4f2aeeb74` (S563) | equal to the 18-Oct bundle | 2 |
| `/root/assetapp/scanner_widget.js` | `10a8bb296944542278a06827c4d09c18` (S563) | equal to the 18-Oct bundle | 5 since S441 |
| `/root/assetapp/claude_reader.py` · `claude_reread.py` | `3894dc23…` · `d9b75e78…` | equal to the 18-Oct bundle | 0 · 1 |
| `/root/assetapp/static/opencv.js` | `ff1e10e7…` (S523) | never in a bundle (F-860) | — |

**Backups on the box:**
- `.bak_S563_<from8>`, `.bak_S566_<from8>`, `.bak_S568_<from8>` and `.bak_S571_<from8>` beside each replaced file;
- `packs.py.bak_S568_048d2ad8`;
- `assets.db.bak_S563_20261015_190827`, `…_S566_20261016_065920`, `…_S568_20261016_121503` and `…_S571_*`.

**The way back.** The scan app has no all-off file of its own; each kit's README carries its one undo line. The order back is **S571 → S568 → S566 → S563**, then v4's.
- **S571's undo** copies `sorting_desk.py` and `asset_register.py` back and moves `batteries.py` aside (`batteries.py.off_S571`).
- **S568's undo** copies three files back, moves `stationery.py` aside, restores `packs.py` and restarts `clinic-finance` too.
- **S566's and S563's undos** copy their files back.

All end with `systemctl restart assetapp`, typed with `\cp -p` past the alias. New tables and columns stay after an undo (additive).

### 12.9 · Kit history, continued

S563 (15-Oct, publish `a8ca1b6b` 19:08) · S566 (16-Oct, `421014e1` 06:58) · S568 (16-Oct, installed ~12:15) · S571 (16-Oct, installed 14:19) — the publishes of 16-Oct midday are interleaved with the Sanjeevni runner's own in `.git/logs/HEAD`; each kit installed by the owner's own server line after an independent cold review (K2 SAFE for S566, S568, S571; K1 SAFE for S563).

### 12.10 · Open at v5

- **This project's:**
  - **S575** (§12.5) — the runner line, then K1 / K2, the install, and his *First setup*;
  - `sorting_desk.py` and `asset_register.py` read whole before their next patch;
  - the old `/papers/month` page (out of the menus) still counts a held double;
  - the rehearsal's end check should also leave out cron-written finance pages (F-909, S571 K2 note);
  - D720 when he asks;
  - S532's placed papers (tighten, never loosen).
- **The parent's:**
  - `packs.py` `e46264b8` — build only from that byte;
  - the portal tile *Asset Register — Clinic assets & AMC* → *Scan app & assets*;
  - the clinic's purchase bills into the pack (D710 (2), F-859 — waits by his word);
  - Shavez's sorting duty when `desk.on` is on;
  - the Aumni Crafts invoice pickup from his Gmail (the Janitor's).
- **The Sanjeevni chat's:** Aumni Crafts papers sit on its lane as kind *Pharmacy expense*, never a Marg-pairing scan; medicine suppliers' challans and bills are its side of the challan flow (D689 item 2).
- **His:**
  - the four switches for Shavez and the managers;
  - Y83;
  - after S575, recording his batteries under *First setup*;
  - the DTH lab's payer, only if he raises it.

---
*(v4, retained whole below — read with §12's corrections.)*

*(v4 H1, retained:)* SCAN APP SYSTEM BOOK — v4 — what the scan app is, where it lives, how it is changed — brought current at the S315 close (the project's fourth session, 14 → 15-Oct-2026)

*v4 supersedes v3 in full: §11 below is what S315 changed; v3's text stands whole after it (its §10.5 "to build", §10.6 pins and §10.8 open items are read with §11's corrections). No patient number, no person's figure and no secret is in this file.*

## 11 · Added at v4 — S315 (14 → 15-Oct-2026): five kits live, one road

*Every kit of S315 was built by the parent's Agent SDK runner (`D:\Downloads\_kbtools\agent_build\run_build.py`, D727) on the owner's API credits, read by an independent cold review before the publish (fix rounds revised the same kit in place), published by his double-click and installed by his one server line. The facts below are read from the kits in `deploy_kits/` and the runner's reports `claude_code_briefs/REPORT_S551/555/557/559/560.md`.*

### 11.1 · The sorting desk (S551, D722; corrected by S555, S559, S560)

- **Where:** `https://followup.dr-manoj.in/scanapp/desk` — `/root/assetapp/sorting_desk.py`, mounted by `asset_register.py`. For the owner and Shavez only; reception never.
- **The page, side by side:** the waiting papers on the left (newest first, folds away) · the scan large in the middle (the browser's own viewer; *Turn ↻* turns the view only) · on the right *What was read* (S560: folded to one line — supplier · no. · date · ₹amount · *edit ▾* — that opens in place), the paper's kind, one *Where does it go?* list, and one **Save — next paper** that files the paper, accepts it (a challan waits for its bill) and opens the next without reloading.
- **One screen (S560, D728 (1)):** the destinations are a compact grid under *Clinic consumables · Clinic expense · My expense — Dr MK / Dr Bhawna · Handed over · Documents · Not here*; a *more ▾* cue shows when the panel would scroll. Measured in headless Chrome: everything on screen at 1366 × 768, at a 1366 × 620 viewport and at 1920 × 1080; at 1280 × 720 only *Not here* is below the fold, with the cue.
- **The destinations** (D722): Procedure room · X-ray small · X-ray 11 × 14 · Others; Implant stock · Clinic equipment · Construction work; Personal expense as *Dr MK* / *Dr Bhawna* · Personal (owner only); Pharmacy — Sanjeevni · NK Pathology; Resumes · Miscellaneous; *A patient's paper — surgical case pack* (set aside, out of every total, never read again); *A page of another paper*; *Blank — discard*.
- **The kinds:** Bill · Estimate slip · Challan (S551) · **Receipt · Statement** (S560; `bills.doc_kind` takes `receipt`, `statement`). Claude's reading pre-chooses Receipt or Statement only when its text says so and its own kind is `other`; nothing is saved without a person's Save (D664).
- **Nothing is guessed:** a suggestion is shown, never saved; Yuvika is never pre-selected; a section, or whose expense a paper is, is set only by a person's Save; an accepted paper can be changed on the desk and the change is audited (`desk_audit`).
- **The corrections (S555):** Save always on screen; dates shown and typed dd-mm-yyyy (stored ISO); the misread-date flag only for a date before 2015-01-01, more than 7 days after the scan, or more than 400 days before it; the owner's own name read as the supplier pointed out (the same own-name list as `clinic_papers.suggest()`), with *Claude read: <name> — use it*; a grey *Claude read: … — use it* under Supplier, Bill no, Date and Amount when Claude's value differs (never for pharmacy, never a Personal paper to a manager, never *made out to*).
- **Opening a given paper (S559):** `/desk?open=<id>` or `?open=B-0125`, by the desk's own visibility rule (never pharmacy; Personal only for the owner); every non-pharmacy paper row in the app leads there.
- **The papers to put right (S560), at the top of *Waiting*, one tap each, by rule:** *Set aside as blank, but it reads as a bill — restore?*; *This looks like a receipt*; *This looks like a statement*; a Resumes-like paper filed as a consumable. *No — leave it* takes a paper off the list.
- **API routes:** `/desk/api/list`, `/desk/api/paper/<id>`, `/desk/api/find`, `/desk/api/save` (POST), `/desk/api/fix` (POST, S560), `/desk/api/payment/void` (POST, S560), `/desk/switch` (POST, owner).

### 11.2 · Bills awaited, the implant stock ledger, the month (S551)

- **Bills awaited** `https://followup.dr-manoj.in/scanapp/desk/awaited`: challans by supplier; each supplier set once to *Monthly bill* (Gaurav Traders — amber if no bill by the 10th of next month; a one-tap join), *A bill now and then* (Variety Stationers — no amber; tick the open challans) or *Paid on challan* (Elegans — the final paper, its payment noted); others amber after 15 days. Challans are counted by quantity; S560 prints each challan's items. A patient's challan is never here (S551 fix C2); a Personal challan never reaches a manager (C4).
- **The implant stock ledger** `https://followup.dr-manoj.in/scanapp/desk/implants`: per supplier owed · paid · balance; *Note payment* (voided, never deleted); *Checked against their statement up to today*. Since S560 its *Paid* also adds the payments recorded by receipts and statements — each record counted once.
- **The month** `https://followup.dr-manoj.in/scanapp/desk/month`: section by section (Procedure room · X-ray films · Others · Implant stock · Construction work · Clinic equipment), *Kept apart* and *Not in the totals*; since S560 *paid N / unpaid M* per section and the Construction card's *N bills · M marked for the accountant*. It replaces the two old history pages in the menus; `/papers/month`, `/papers/challans` and `/purchases` stay reachable by address with their banners.

### 11.3 · Receipts, statements and one payment record (S560, D728)

- **A receipt** answers *Pays which bill?* — the supplier's bills (and challans turned final) of the last 180 days not yet fully paid, the likely one pre-ticked only when exactly one has the same amount within 60 days; or *No bill — paid directly*; or *A statement*. Its payment boxes: date, amount, Cash · Cheque · Bank / UPI, cheque / ref no. Save records the payment and **files** the receipt beside the bill it pays (status *Filed*, captured) — **never accepted, never in a total or a pack**.
- **A statement** carries its period, total and payment, and *Which invoices does it cover?* (pre-ticked inside the period, ± 7 days offered); *Ticked ₹X of statement ₹Y — difference ₹Z*, with *An invoice may not be scanned yet.* when Z ≠ 0. Save records **one** payment covering the ticked invoices, each up to what it still owes, oldest first. A receipt may be the statement's proof — no second payment.
- **One payment record:** `paper_payment` + `paper_payment_bill` (fingerprinted by `bill_created_at` / `proof_created_at`, so a re-issued id inherits nothing). A re-save **changes** the payment already recorded (old allocation rows voided and kept, audited `payment_changed`) — never a second one (fix B1). An allocation is capped at what the bill still owes. *Paid?* on a Bill marks it paid directly (*"Paid on dd-mm-yyyy — change?"*). A receipt or statement re-saved as another kind voids its own payment (fix C4). The old bill page's Approve refuses a receipt or a statement (fix C3).
- **Where paid shows:** the desk, the old bill page (*Paid dd-mm-yyyy · ₹ · mode · no.* with the receipt's scan), All papers (*Paid* / *Part-paid*), the month, the implant ledger.

### 11.4 · Construction's tick and pack item 8.4 (S560, D728 (2) — the parent's file)

- `bills.to_accountant` (0 by default): a tick *Send to accountant* only on a Construction-work paper whose kind is Bill; audited; forced off for an estimate slip or a challan.
- **The parent's `/root/finance/packs.py`** (`build_bundle` and the item-8 list only, under a PLANNED line; RELEASED at install at `048d2ad8`): every bundle leaves out receipts, statements and challans still awaiting their bill; NEW item **8.4 · Scanned bills: Construction bills marked for the accountant** (`subgroup='construction'`, kind Bill, ticked, not rejected, any lane, the pack's own month rule); a ticked construction bill is in 8.4 only, never also in 8.1 / 8.2 / 8.3 (fix C1). The installer proves the pack loaded: `/finance/healthz` 200 and no `packs NOT mounted` in the clinic-finance journal since the restart (fix C2).

### 11.5 · Each machine's page (S557 — "the final kit"; D719 kit c)

- **Where:** `https://followup.dr-manoj.in/scanapp/assets/<id>` — `/root/assetapp/asset_machine.py`.
- **At the top:** one cover line (*Covered: AMC by <provider> till dd-mm-yyyy* · *Under warranty till …* · *No cover*; amber in the last 30 days, red once lapsed) and one line of totals (bought for · spent since on N repairs/services · cover paid; no ₹ to a manager where the price is hidden).
- **Three folds:** **Parts** (make, model, serial, fitted on, warranty, its paper; *Replaced / removed* keeps the part in a folded list, never deleted) · **Cover history** (warranty / AMC / CMC / insurance / other, newest first, cost and paper; a mistake voided, never deleted; the old single contract fields shown once, read-only) · **Spends** (from the service log, totals per year; the old *Add service* form keeps working).
- **Renewals:** every live cover and live part's warranty puts **one** reminder on Renewals (`expiries`), kept in `expiry_id`, updated, never duplicated; a heal at every start and when Renewals opens.
- **Its paper:** a *B-____* box on every form (refuses a pharmacy paper, a patient's paper, and for a manager a Personal paper); the paper's page reads *Linked to <machine> as …*; a Clinic-equipment paper offers **+ asset record** (`/bills/<id>/machine`), pre-filled from the paper and Claude's reading.
- **Re-issued ids (fix BL1):** `asset_part`, `asset_cover` carry `asset_created_at` and `bill_created_at`; `service_logs` carries `bill_created_at`; a row whose machine or paper no longer matches is detached and audited, never deleted; a reminder is the app's own only by three tests (its id, `entity='asset'` for that machine, and an own label prefix).
- **Who:** the owner and managers may add and change; reception never. **`machine.on` absent = off** for managers (they see the page as before).

### 11.6 · One menu, one road (S559)

- **One menu** on every owner and manager page and the desk's pages: *Sorting desk (N) · The month · Bills awaited (N) · Implant ledger · Machines · Renewals · All papers · Vendors · Admin · account · Logout* (`_s559_bar`; N from the desk's own `waiting()`); *Sorting desk* shows to a manager only while `desk.on` is on; *Drafts* and *Staff* out of the menu (Admin gains a Staff card).
- **The home page** opens with *N papers waiting — Open the sorting desk* and *Bills awaited N · Implant ledger · The month*.
- **The old bill page** shows the scan inline, *Open on the sorting desk* (not for pharmacy) and the true badge *Waiting · Filed · Accepted · Set aside*. *All papers* (the old Purchases) has *N waiting on the desk →*; its BACK goes to the scan app's home.
- **Reception's intake, slip and menu are unchanged** (walked byte for byte).

### 11.7 · The double-stamp repair (S559, F-897 — the shared widget)

- `/root/assetapp/scanner_widget.js` `1128ac97` (S559.1), inside the intake-only `cvScan` / `inlineStamp` branches: Save while a page is being adjusted applies the adjustment and saves once; Save always closes the stage; a leftover stage never makes a page; the same pages queued twice within 10 s are queued once; a generation counter stops a late Adjust picture reopening the stage (fix C1); a dropped earlier page keeps the adjustment on the right page (fix C2).
- **Seven surfaces:** the finance app's five and the asset page set neither branch — proven byte-identical in load and save. A finance kit that pins the widget reads `1128ac97`.
- **Left for later:** review note N7 (a page deleted while an Adjust picture still loads).

### 11.8 · The switches

| switch | where | state at v4 |
|---|---|---|
| `desk.on` — *Sorting desk for Shavez* | the *Switches* card (owner only) on the scan app's home `https://followup.dr-manoj.in/scanapp/` and on The month (`POST /desk/switch`) | **absent = OFF** for managers; the owner uses the desk at once |
| `machine.on` — *Machine pages for Shavez* | the same card (S557's fourth line) | **absent = OFF** for managers |
| `scan.cv` — *Smart scanner* | the same card | ON (his tap, 11-Oct) |
| `scan.lanes5` — *Reception buttons* | the same card | ON (his tap, 13-Oct) |
| `read.claude` — Claude reading | the card *Reading the scans — Claude* on `https://followup.dr-manoj.in/scanapp/admin` | on while the key and the credit hold |
| `desk.floor` | set by S551's installer (the install day) | older scans are not flagged on the desk |

### 11.9 · The database (additive only; nothing moved)

- **S551:** `challan_supplier`, `implant_payment`, `implant_check`, `desk_audit`; `bills.paid_on`, `bills.paid_amount`.
- **S557:** `asset_part`, `asset_cover` (with `asset_created_at`, `bill_created_at`); `service_logs.bill_id`, `service_logs.bill_created_at`.
- **S560:** `paper_payment`, `paper_payment_bill` (with `voided_at`, `voided_by`; key `(payment_id, bill_id, voided_at)`); `bills.to_accountant`.
- All inside `assets.db`, which the nightly backup (`/root/state_backup/assetapp_backup.py`) carries.

### 11.10 · The API credits and Claude reading

- Claude reads every new scan first (S550, D723), with Sarvam the fallback; since S555 it never reads a patient's paper. **The owner's API credit expires on 17-Oct-2026: after that Claude reading stops by itself** (*stopped: the credit has run out*) **and Sarvam reads alone** — S550's own switch; nothing to do. Paid credit afterwards is his choice.
- The Agent SDK runner that built S551 … S560 runs on the same credit. Its logs read USD 73.35 for this project's five kits (S551 17.22 · S555 5.28 · S557 12.60 · S559 17.53 · S560 20.72).
- The Claude-vs-Sarvam comparison (`claude_code_briefs/S315_READING_COMPARE.md`) is **parked** at his word.

### 11.11 · Pins, drift and the way back at v4

| file | pin | rests on | drift |
|---|---|---|---|
| `/root/assetapp/sorting_desk.py` | `a4623438f068d8e691b797482bd942ab` (S560) | the installer's read-back — DECLARED-PENDING until the 16-Oct bundle | 4 since written whole (S551) |
| `/root/assetapp/clinic_papers.py` | `88963eacee217e051ae07091648a46d7` (S560) | DECLARED-PENDING | **6** since S530 — read whole and consolidate before the next patch |
| `/root/assetapp/asset_register.py` | `9daed9ea4f2a87e40b43711e472e701f` (S560) | DECLARED-PENDING | 4 since S551's whole read |
| `/root/finance/packs.py` (the parent's) | `048d2ad81abb0271a1cddd31134544bb` (S560) | DECLARED-PENDING | the parent's count |
| `/root/assetapp/asset_machine.py` | `0caec41e655cfd51c2eaf9176ee33365` (S559) | equal to the 15-Oct bundle | 1 |
| `/root/assetapp/scanner_widget.js` | `1128ac975ba2543e1fe9edf7c721d4f8` (S559.1) | equal to the 15-Oct bundle | 4 since S441 |
| `/root/assetapp/claude_reread.py` | `d9b75e784c4a806e941f3d1a243990e1` (S555) | equal to the 15-Oct bundle | 1 |
| `/root/assetapp/claude_reader.py` | `3894dc2358abd875ee61ced7619e1e1b` (S550) | equal to the 15-Oct bundle | 0 |
| `/root/assetapp/static/opencv.js` | `ff1e10e731d08f505fc51eb0271c6c85` (S523) | never in a bundle (F-860) | — |

**Backups on the box:** `.bak_<kit>_<from8>` beside each replaced file (S551, S555, S557, S559, S560 — e.g. `sorting_desk.py.bak_S560_a59fa38d`, `scanner_widget.js.bak_S559_1143c77b`, `packs.py.bak_S560_d86d351a`); `assets.db.bak_S551_*`, `…_S555_*`, `…_S557_*`, `assets.db.bak_S559_20261014_171859`, `assets.db.bak_S560_20261015_125502`.

**The way back:** there is no all-off file of the scan app's own. **Each kit's README carries its one undo line** (the `.bak_` copies back with `\cp -p`, then `systemctl restart assetapp` — S560's also restores `packs.py` and restarts `clinic-finance`); the order back is S560 → S559 → S557 → S555 → S551, then S550 and earlier as v3 §10.6. New tables and columns stay after an undo (additive; nothing old reads them). A database backup is used only if data written after an install must be reversed — say so before using it. *S551's own README prints its undo with `cp -p`; type it as `\cp -p` (past the alias).*

### 11.12 · Kit history, continued

S551 (14-Oct, publish `f3cf959a`) · S555 (`fb851d88`) · S557 (`726b6b21` / `697e8509`) · S559 (`a01a9694`) · S560 (15-Oct, `b55d46d0`) — each installed by the owner's own server line, after an independent cold review.

### 11.13 · Open at v4

- **This project's:** F-902 (*"Already set aside on <date> — Restore?"*); review note N7 in the widget; `/tmp/s560fix*` on the box; the review notes *seen, not changed* in the five reports; `clinic_papers.py` read whole before its next patch; D720 (the family's documents and renewals) when he asks; S532's placed papers (tighten, never loosen).
- **The parent's:** the portal tile *Asset Register — Clinic assets & AMC* → *Scan app & assets*; the clinic's purchase bills into the pack (D710 (2), F-859 — waits by his word); Shavez's sorting duty when `desk.on` is switched on.
- **The Sanjeevni chat's:** Claude's readings of pharmacy papers sit in `claude_reading` for its use; the desk never shows a pharmacy paper; medicine suppliers' challans and bills are its side of the challan flow (D689 item 2).
- **His:** the two switches for Shavez; Y83; paid credit after 17-Oct.

---
*(v3, retained whole below — read with §11's corrections.)*

*(v3 H1, retained:)* SCAN APP SYSTEM BOOK — v3 — what the scan app is, where it lives, how it is changed — brought current at the S314 close (the project's third session, 13 → 14-Oct-2026)

*v3 supersedes v2 in full: §10 below is what S314 changed; v2's text stands whole after it (its §9.6 pins and §9.8 open items are read with §10's corrections). No patient number, no person's figure and no secret is in this file.*

## 10 · Added at v3 — S314 (13 → 14-Oct-2026): four kits live, the final shape settled

### 10.1 · Reception captures; Personal expense with Dr MK / Dr Bhawna (S544, D719 kit a; F-891)

- **The intake:** reception sees four big lane buttons and the Challan button: Clinic · Pharmacy · NK Pathology · Other document. They are behind the setting `scan.lanes5` (`_lanes5_on()`; the admin card *set_scan_lanes5*), **ON since the owner's tap of 13-Oct**. *Personal expense* is offered to him and Shavez only. When OFF, the intake is as before.
- **The lane `owner_expense`** reads **Personal expense** everywhere. Each paper's page asks **Dr MK / Dr Bhawna** (`bills.pe_who`: `'bhawna'`, or NULL = Dr MK; route `/papers/<id>/pe_who`, refused on a Personal-section paper). The papers page has a **Personal expenses** fold (`personal_expenses()`), for the owner and the checker; a manager never sees a Personal-section paper there.
- **The asset category** *Medical Equipment* is now **Dr MK Clinic Equipment** in `CATEGORIES`, and every existing asset was moved by `migrate`.
- **The owner-only guard (F-891):** `_private_s544` / `_bill_or_404` on these doors:
  - `/bills/<id>`, its file and its edit page, the month door, and every bill door that changes a paper;
  - the bills list and the supplier's history (`vendor_view`).
  
  A manager gets 403 on a paper in the `personal` section.

### 10.2 · The scanner finds the paper (S545; F-890)

- **The shared widget** `scanner_widget.js` (seven surfaces) has new code inside the smart-path block only:
  - `quadFromPaper`: the low-saturation bright region; a second Otsu split when the bright class covers more than 75 % of the frame; print required (ink 0.5–50 %); the hull reduced to four corners keeping ≥ 97 %, or `minAreaRect`;
  - `paperQuadOK`: refuses only a shape whose three corners sit on the frame's own corners;
  - `edgesSharp`: a median edge step of at least 12, so a frame-filling page is not cut on a shadow;
  - `cvUpright`: a sideways page turned by its projection profile.
  
  Every OpenCV `Mat` in the 0.3 s live loop is deleted. The finance app's five surfaces are unchanged (walked).

### 10.3 · Dr Bhawna's own file in the accountants' pack (S548, D721 — the parent's file)

- `/root/finance/packs.py` `build_bundle` carries the pseudo-lane **`owner_expense_bhawna`**. Item **8.3** *Dr Bhawna's expense-file bills* holds `owner_expense` with `pe_who='bhawna'`; **8.2** keeps Dr MK's. The file is the parent's: built under a PLANNED line and released.

### 10.4 · Claude reads every scan first (S550, D723)

- **The reader** `/root/assetapp/claude_reader.py`:
  - **How it calls:** the Messages API by `urllib`; a PDF sent as a document, a photo as an image (shrunk by Pillow when the box has it and the photo is over about 3.7 MB). Models: `claude-sonnet-5-5`, then `claude-haiku-5-5` only if Sonnet does not exist (kept in `read.claude_model`).
  - **What it keeps:** only listed fields — kind, supplier and its phone/email, number, date, amount, *made out to* as a kind (clinic / doctor / patient / other), handwritten, and items with quantity, unit, rate, amount, make, model, serial, batch, expiry and HSN. A date outside 2015 … next year is dropped. No free text and no person's name are kept. One row per paper in `claude_reading`; a later failure never replaces a good reading.
  - **When it stops:** on a refused key (`stopped:the key was refused`), on spent credit (`stopped:the credit has run out`), or at the daily limit of `read.claude_daily_cap` calls (default 400), counted per call in `read.calls.<day>`.
- **The hook:** `_bg_extract(bid, path, _reading=None)` asks `_s550_claude` first; Sarvam reads exactly as before when Claude answers nothing. The rules by kind of paper:
  - **A pharmacy paper** (the lane, or an old row's kind) is read beside Sarvam in its own thread; Sarvam fills it and never waits.
  - **The Other-document lane and the Personal and Resumes sections** are never sent.
  - **The filling** is the app's own: only what is empty, then the month, the double guard, S441 and the way home.
  - **The intake and re-read doors** open when Sarvam **or** Claude can read (`_reader_on`); the button reads *Re-read*.
- **The older scans** (`claude_reread.py`, started by the installer, one copy at a time):
  - Every paper not rejected, not Other document, Personal or Resumes, and not yet read well is read once.
  - A paper still to be sorted with something empty is filled through `_bg_extract(..., _reading=...)`.
  - An approved or pharmacy paper is read and kept aside only.
  - It leaves 50 of the day's calls for new scans and stops at a refused key.
  - Progress is in `read.reread_progress`.
- **The key:** `/root/.scanapp_secrets/anthropic.key` (folder 700, file 600, root). It is the owner's *scanapp-reader* key (30 days, his Default workspace), typed once at a hidden prompt. It is never in the repository, a backup, the database, a page or a log. A key in the environment is used only when the file is absent.
- **The owner's card:** *Reading the scans — Claude* on `https://followup.dr-manoj.in/scanapp/admin`: ON / OFF / STOPPED, today's calls and the limit, read so far, could not read, the model, the older scans' progress, Switch.

### 10.5 · The final shape — D722, the mock-up the specification (S551 to build)

- **The specification:** artifact `CTcMEXEuqvgjpZxrGgxdYw` (four boards: the desk, Bills awaited, the implant ledger, the month) and `claude/S314_SCANAPP_FINAL_PLAN.md`. Its parts:
  - **the desk:** one laptop page, side by side;
  - **the destinations**, including *A patient's paper — surgical case pack*, set aside and out of the totals;
  - **challan billing modes** by supplier;
  - **an implant stock ledger** per supplier;
  - **one month page** by section;
  - **a switches card** and the header *Scan app & assets*;
  - **five safety fixes**.
- **To be built as S551 through the parent's SDK path** (the owner, 14-Oct). It reads `asset_register.py` whole first (drift 5) and leaves `scanner_widget.js` untouched.
- **Patient implant bills belong to the surgical case pack** (another system, not built here); his own implant stock is scanned here.

### 10.6 · Pins, drift and the way back at v3

| file | pin | drift |
|---|---|---|
| `/root/assetapp/asset_register.py` | `3d5a36e3f9dc398a948f70a87f12d513` (S550; DECLARED-PENDING) | **5** (S523, S531, S532, S544, S550) — read whole and consolidate before the next patch |
| `/root/assetapp/claude_reader.py` | `3894dc2358abd875ee61ced7619e1e1b` (S550, new) | 0 |
| `/root/assetapp/claude_reread.py` | `47548ab97c55a1f4fb8d5d1a608a1681` (S550, new) | 0 |
| `/root/assetapp/clinic_papers.py` | `5b197fb5718f8d28ed8de6c0cafc9ab0` (S544.1) | 3 since S530 |
| `/root/assetapp/scanner_widget.js` | `1143c77b13ae62652d4d961a92b9a9ab` (S545.1) | 3 since S441 |
| `/root/assetapp/static/opencv.js` | `ff1e10e731d08f505fc51eb0271c6c85` (S523) | never in a bundle (F-860) |
| `/root/finance/packs.py` (the parent's) | `d86d351a46a1ba4da7d0e615da0deb1a` (S548) | the parent's count |

**Backups:**
- the app: `.bak_S544_35f9e823`, `.bak_S550_99652ff0`;
- the papers page: `.bak_S544_476e157c`;
- the widget: `.bak_S545_65127fcb`;
- the pack: `packs.py.bak_S548_ada0860a`;
- the database: `assets.db.bak_S544_*`, `.bak_S550_*` (the database by the backup API).

**The order back:** S550 (its one line: the backup back, the two new files removed, restart) → S548 → S545 → S544. Each kit's README carries its one undo line. A reading kept in `claude_reading` is read by nothing in the old files.

### 10.7 · Kit history, continued

S544 · S545 · S548 (13-Oct, publish `f1ea12a4`) · S550 (14-Oct, publish `387325fe`) — each installed by the owner's own server line.

### 10.8 · Open at v3

- **This project's:**
  - S551, the desk (D722), through the SDK path;
  - the real-photo proof of S545, from reception's scans;
  - asset kit c (parts, cover history, spends);
  - D720 (the family's documents and renewals) after;
  - S532's placed papers after a week.
- **The parent's:** `packs.py` 8.x for the clinic's purchase bills waits by his word (F-859); the portal tile's name *Asset Register* is the parent's to change to *Scan app & assets*.
- **The Sanjeevni chat's:** Claude's readings of pharmacy papers sit in `claude_reading`, for its use; nothing on its papers is written.
- **His, not to be guessed:** the clinic / MK split of construction and electrical papers (D664).

---
*(v2, retained whole below — read with §10's corrections.)*

*(v2 H1, retained:)* SCAN APP SYSTEM BOOK — v2 — what the scan app is, where it lives, how it is changed — brought current at the S306 close (the project's first session, 11-Oct-2026)

*v2 supersedes v1 in full: §9 below is what S306 changed; v1's text stands whole after it (its §2, §4, §6 step 2, §7 and §8 are read with §9's corrections). No patient number, no person's figure and no secret is in this file.*

## 9 · Added at v2 — S306 (11-Oct-2026): four kits live, the flow settled

### 9.1 · The scanner is OpenCV in the phone's own browser (S523, D711; F-842 repaired)

- **Why:** 33 of the last 40 scans (01–10 Oct) were the whole camera frame shrunk to 1400 px — the light outline finder found nothing; and every page was shrunk *before* it was looked at.
- **What:** OpenCV.js 4.10.0 (`@techstark/opencv-js` 4.10.0-release.1, md5 ff1e10e7, 10,378,215 B; gzip 3,381,659 B) at `/root/assetapp/static/opencv.js`, served at `/scanapp/scan/opencv.js` (gzip, `Cache-Control: public, max-age=31536000, immutable` — one download per phone). In `scanner_widget.js`, inside `var cvScanOn = (CFG.cvScan === true) && !!CFG.cvUrl`: the camera asked for 3264 × 2448; `cvFindQuad` (Canny → contours → approxPolyDP; a brightness/Otsu fallback; a frame-hugging box refused; the brighter inside preferred; aspect 0.38–2.7, area 10–90 %); `cvWarp` (perspective at full resolution, 3300 in, 2400 out; B&W by blur/divide/normalise); `autoAddCV` on capture and import; a live outline on the preview (`liveStart` / `liveTick`); *Adjust* (the existing corner handles) beside *Retake*; `window.__scannerCV` for a walk.
- **The switch:** the setting `scan.cv` (read by `_scan_cv_on()`; the admin card *set_scan_cv* on `/scanapp/admin`) — **one value for every phone; on since the owner's tap of 11-Oct (D711).** No per-phone check; a phone that cannot carry the library, or a download that does not arrive, keeps the old light path by itself. The admin page is too long for him (F-856): a short owner page for the switches, later.
- **Shared file:** the widget serves **seven surfaces** (two scan-app, five finance-app); only the scan app's intake sets `cvScan` / `cvUrl` (`scan_cfg`), so the finance app's five are unchanged — walked so. A finance kit that pins the widget reads `65127fcb` from now.
- **Not in the nightly bundle:** `/root/assetapp/static/` (F-860) — the pin is the kit's; it comes back from `deploy_kits/S523_SCANNER_CV/install_s523.sh` (the pinned npm package, refused on any other md5).
- **First real reading:** Monday 12-Oct 08:00 IST, a scheduled check on the 02:30 backup (smart-path scans against whole photos; three lines to the owner).

### 9.2 · The papers page: four sections, and sorted = accepted (S530, D710)

- **Sections beside the three groups** (`SUB`): `construction` *Construction work* (counted on its own, never called clinic or MK by the system — D664 stands), `resume` *Resumes*, `misc` *Miscellaneous documents*, `personal` *Personal* (the owner only; 403 to a manager). `CONSUMABLE` = the three groups; `SECTIONS` the four; the month page `/papers/month` shows a sections card; sections are excluded from the consumables' totals and the rate page.
- **Suggestions** (`suggest()`): a résumé by its words, a construction supplier by its name or items, the clinic's own name → *misc*; the lane suggestion as before. A section is **never** set by the system (D664) — a person's tap only.
- **Sorted = accepted:** `set_group()` → `_accept(db, bid, who)`: status `approved`, `approved_by` = the person; the dup rule through `AR._dup_by_triple(approved_only=True)` (a same-vendor-number-amount double is held, audit `d710_not_accepted`); the vendor upserted, the asset backfilled; audit `d710_accepted`. The approve/reject door on `/bills/<id>` stays for refusing.
- **The heal** (`heal(db)` in `init()`): at every start, every grouped draft of the backlog accepted once (8 on the box at install, 0 after) — idempotent.
- **The sort list and the stand** (`_live_sort`, `_live_sections`, `stand()`): clinic papers waiting for a group; sections at a glance.

### 9.3 · Challans (S531, D689 item 2)

- **Reception's intake:** one big button `#challan_btn` *📄 CHALLAN HAI?* → *✔ CHALLAN — bill baad mein* (`_challanSet(on)`; the hint changes; *· CHALLAN* on the lane line; reset after every Save; the hidden field `challan`); both intake doors pass `challan=(form.challan == "1")`; `_create_intake_bill(..., challan=True)` sets `doc_kind='challan'`, `challan_state='awaiting'` (and `kind='Challan'` on the pharmacy lane); the slip says CHALLAN. Columns added by the migrate: `bills.doc_kind`, `challan_state`, `challan_of`.
- **The widget:** a queued upload snapshots its upload fields at Save (`fields: Object.assign({}, CFG.uploadFields)` in `enqueue` / `enqueueFile`; `sendOnce` sends `it.fields || CFG.uploadFields`) — the toggle's reset can never alter an upload that retries later. Inside S441's `inlineStamp` block, which only the intake sets.
- **Bills awaited:** `/papers/challans` (`challans_awaiting`): amber after `d710.challan_amber_days` days (default 15 — the owner's edit on the mock-up); a new bill of the same supplier (`_supplier_key`: the first two words, hyphens and dots joined) within `CHALLAN_MATCH_DAYS` 60 suggests its challan on the bill's page (`challan_for_bill`, `challan_card`); **join** = S465's join plus `_challan_mark_joined` (state `joined`, `challan_of` = the bill), **unjoin** undoes it; `/papers/challans/<id>/close` *bill nahi aayega*; `/papers/challans/<id>/delete` after the join **moves** the file to `uploads/_deleted_challans/` (never unlinked). Challans are excluded from the sort list, the stand and the month totals.
- **A pharmacy challan** is handed to the Sanjeevni side as `kind='Challan'`, `doc_kind='challan'`, `status='captured'` — its register (`kind='Pharmacy'`) does not see it as a bill to pair until it chooses to read challans; the scan app joins no pharmacy challan (S465's join refuses the lane). Medicine suppliers' challans and bills are the Sanjeevni chat's side of the flow (D689 item 2).

### 9.4 · The system sends a scan home (S532, D710 (5))

- **Hook:** the last lines of `asset_register._bg_extract` (after S441's pass): `_clinic_papers.auto_home(db, bid)`, fail-soft. **Heal:** `heal_auto(db)` in `init()` — every live paper read by the OCR with no group gets the same one look at every start (B-0133 placed at install).
- **Evidence** (`supplier_history`): the supplier's earlier live papers (first two words of the name; challans excluded) that a **person** placed — a paper the system placed counts only once a person moved (`relane` with a name) or sorted (`subgroup` by a person) it afterwards; so the system never feeds itself.
- **Rule 1, the lane:** this paper live (draft / captured), not a challan, not a page of another, not moved by a person, not already looked at: all earlier papers on the **pharmacy** lane and **≥ 3** (`AUTO_MIN_LANE`) → pharmacy (`captured`, kind `Pharmacy`, as the lane door moves it); all on the **clinic** lane **and** a person sorted **≥ 2** (`AUTO_MIN`) into one group → clinic, then rule 2. **Never** out of, or into, `lab_purchase` and `owner_expense`; never into `other_doc`. Audit `auto_lane` with the evidence count.
- **Rule 2, the group:** on the clinic lane, a draft with no group, no person's group, not already looked at: all earlier clinic papers in **one** consumable group, ≥ 2 → that group, and `_accept` with `approved_by` *"system — from N earlier papers of this supplier"*. Audit `auto_group`. A section is never guessed (D664).
- **A supplier seen on two lanes (Yuvika) decides nothing; a person's placement is final; one look per paper.** The paper's page says *Placed by the system from N earlier papers of this supplier — change it here if wrong* (`auto_note`).
- **What to watch:** every placed paper a person later changes is a rule to tighten; the evidence rule is never loosened.

### 9.5 · The flow of the lanes — measured and settled (D710; `claude/SCANAPP_FLOW_PROPOSAL_v1.md`)

145 scans since 14-Aug (the 11-Oct backups): pharmacy 108 (89 paired with their Marg bill; September 67 of 81 bills, October 22 of 23) · clinic 31 (26 of 29 live were draft 1–47 days, 18 ungrouped, 3 ever approved — healed by S530) · lab 3 (August only) · Dr MK expense 2 (no warranty typed) · other document 1 · 12 re-lanes · the finance app's own expense-scan doors never used · Envirad bills NK Pathology though scanned on the clinic lane · Yuvika on two lanes. **The owner's rulings of 11:41 (D710):** sorted = accepted (done, S530); the accountants' pack carries the clinic's purchase bills as item 8.3 (**open — the parent's `packs.py`; F-859**); Sukhveer scans NK Pathology's purchase bills on the lab lane as a duty (**open — the parent's duty map**). Where each scan goes now: pharmacy → the Sanjeevni register; clinic → the papers page (sorted = accepted; the system places a known supplier's paper by itself) → the month page, the rate page, and — once 8.3 is built — the accountants' pack; lab → the pack's 8.1; Dr MK → the pack's 8.2 and the renewals list; other document / the sections → found by month and section; a challan → *Bills awaited* until its bill.

### 9.6 · Pins, drift and the way back at v2

| file | pin | drift |
|---|---|---|
| `/root/assetapp/asset_register.py` | `35f9e823b07830b5831efc586f48d46b` (S532) | **3** since its whole read (S523, S531, S532) — read whole at 5 |
| `/root/assetapp/clinic_papers.py` | `476e157c82f17a0af164019b04ccbb2b` (S532.1) | **2** since S530 replaced it whole (S531, S532) |
| `/root/assetapp/scanner_widget.js` | `65127fcb7c9c00ded03190c5156c7f6e` (S531) | 2 since S441, both inside intake-only branches |
| `/root/assetapp/static/opencv.js` | `ff1e10e731d08f505fc51eb0271c6c85` (S523) | never in a bundle (F-860) |

Backups `.bak_S523_e774be89`, `.bak_S531_d3f1b64e`, `.bak_S532_4e924b80` (the app); `.bak_S530_5e21f491`, `.bak_S531_c60e043c`, `.bak_S532_93d23481` (the papers page); `.bak_S523_e2bca602`, `.bak_S531_cd9c6e60` (the widget); `assets.db.bak_S530_*`, `.bak_S531_*`, `.bak_S532_*`. Each kit's README carries its one undo line; the order back is S532 → S531 → S530 → S523. A paper the system or the heal placed stays placed (as a tap would have) and is changed on its page.

### 9.7 · Kit history, continued

S523 (the smart scanner; F-842) · S530 (the four sections; sorted = accepted; the backlog healed) · S531 (the challan flow) · S532 (the system sends a scan home). All four 11-Oct-2026, the project's first session; each published by the owner's double-click and installed by his one server line.

### 9.8 · Open at v2

- **The parent's:** `packs.py` item 8.3 (D710 (2), F-859); Sukhveer's duty line (D710 (3)); `static/` in the bundle or marked by design (F-860).
- **This project's, later:** a short owner page for the switches (F-856); the Monday reading of the smart scanner and any per-phone fix; S532's placed papers after a week; a warranty date offered from the scan's reading.
- **His, not to be guessed:** the clinic / MK expense split (D664).

---
*(v1, retained whole below — read with §9's corrections: §2's pins, §6 step 2's drift, §7's history and §8's open items are v1's.)*

*(v1 H1, retained:)* SCAN APP SYSTEM BOOK — v1 — what the scan app is, where it lives, how it is changed

*Written at S305 (the parent), 11-Oct-2026, as part of the scan app's starter pack (D689 item 3). Read from the live
code in the 11-Oct 01:35 nightly bundle and the pinned Register (`live_pins_S304close.txt`). This Book is the scan-app
project's own record; the parent's Runbook describes the estate. No patient number, no person's figure and no secret is
in this file.*

## 1 · What it is, in one paragraph

Every paper that enters the clinic — a supplier's bill, a challan, a handwritten slip, a warranty card, a document that
is not a bill — is photographed on a phone by whoever holds it, in the **scan app**. Each scan gets a **stamp number at
once** (written on the paper), becomes one PDF, is read in the background (Sarvam OCR), and lands in a **lane**. The
pharmacy lane hands the bill to the Sanjeevni side (Amir's purchase pages, the bill register). The clinic lane's papers
are sorted on the **papers page** into the clinic-consumables groups. The owner's own purchases go to the **Dr MK
expense** lane, where a warranty can be kept and reminded. Everything is found again by month, by group, by supplier.

## 2 · Where it lives

| part | where | notes |
|---|---|---|
| the app | `/root/assetapp/asset_register.py` | Flask under gunicorn (2 workers, `127.0.0.1:8030`), service `assetapp`, **the system `python3`, not the venv** (F-53). Served at `https://followup.dr-manoj.in/scanapp` (the prefix of S222; the vhost forwards `/scanapp`). Pinned `e774be89…` (S465). About 4,100 lines. |
| the papers page | `/root/assetapp/clinic_papers.py` | D664, kits S464 → S465 → S466. Mounted by one guarded `init(ar)` from `asset_register.py`; every template hook sits behind `is defined`. Pinned `5e21f491…`. |
| the database | `/root/assetapp/assets.db` (env `ASSETS_DB`) | SQLite: `bills`, `bill_items`, `vendors`, `vendor_contacts`, assets, staff, files. A bill's `lane`, `kind`, `status`, month, sub-group and warranty live on its row. |
| the scanner | `/root/assetapp/scanner_widget.js` (served at `/scanapp/scan/widget.js`) | v2 since S219; S441's no-wait flow. **Seven live surfaces: the scan app's intake (2) and the finance app (5 — day scan, non-cash, expense, clinic day, clinic expense).** Both apps version its URL by the file's mtime, so a swap busts every browser cache. Pinned `e2bca602…`. |
| the reading | `/root/shared/sarvam_ocr.py` | the one OCR module; the key is in the service environment, never in code. |
| the checks | `/root/shared/scan_checks_s441.py` | S441: a forgotten page joined, a sure double set aside (never an approved bill), a near match flagged. Pinned `b9ba6839…`. |
| the backup | `/root/state_backup/assetapp_backup.py` | S286/S287: a verified archive nightly, off-site to Drive slots `assetapp_nightly.tar.gz` / `assetapp_monthly.tar.gz`. Pinned `b816504c…`. |
| the doors in | the portal's tiles (`/root/portal/portal.py`, `tile_grants.json` — the parent's) | the *Scan* tile opens `/scanapp`, the intake tile `/scanapp/intake`. |
| the service unit | `assetapp.service` | a repository copy is pinned SHORT `cd84cdc2` (S255). |

## 3 · The pages (routes under `/scanapp`)

- **Intake:** `/intake` (the scanner; doc mode; the fallback photo/PDF upload inside a fold) · `/intake/scan_submit` ·
  `/intake/submit` · `/intake/slip/<id>` and `/intake/slip/last` (the big stamp number to write on the paper).
- **Bills:** `/bills` · `/bills/<id>` with `approve`, `reject`, `reread`, `edit`, `delete`, `dup`, `lane`, `month`,
  `file`, `thumb`, `s441` · `/bills/<id>/subgroup` (D664) · `/bills/extract` · `/bills/new` · `/drafts`.
- **The papers page (D664):** `/papers` (the clinic papers to sort, each with a suggestion: Yes / Change / Skip) ·
  `/papers/<id>` · `/papers/month` (clinic consumables for a month, by group) · `/papers/<id>/join` and `/unjoin` (one
  purchase = one PDF, with an undo that names the papers) · `/papers/<id>/warranty` (what it is, warranty till, remind
  30 / 7 days before or never). All owner/checker only.
- **Lanes and purchases:** `/lanes` · `/purchases` (the owner's page: rate drift, expiry soon, consumption) · `/vendors`.
- **Assets and renewals:** `/assets` (by location, collapsible) · `/assets/<id>` with `edit`, `service`, `delete` ·
  `/renewals` (warranty / AMC / consumable expiry; since S466 a Dr MK expense's warranty too) · `/api/due` · `/staff`.
- **House:** `/healthz` · `/login`, `/logout` (the portal's SSO cookie; portal role doctor → owner, staff → reception) ·
  `/admin` · `/account`.

## 4 · The lanes (S409, D625) and the groups (D664)

Five lanes on the one intake, each login with its own default (`LANE_DEFAULTS`); a staff member can send a pharmacy scan
to another lane with *Galat lane*:

| lane key | label | kind · status at intake |
|---|---|---|
| `clinic` | Clinic bill — asset or consumable | Consumable · draft |
| `pharmacy` | Pharmacy purchase — Sanjeevni | Pharmacy · captured → the Sanjeevni side |
| `lab_purchase` | Lab purchase — NK Pathology | Lab · captured |
| `owner_expense` | Dr MK expense | Expense · captured |
| `other_doc` | Other document — not a bill | Document · captured |

**The clinic-consumables groups (D664, the owner's ruling of 03-Oct):** *Procedure room* (fibre cast, roller bandage,
cotton, tape, betadine) · *X-ray films* (then one more tap: small film or 11 x 14) · *Others* (stationery and the rest).
The sub-group is optional at scanning; Shavez or the owner sets it later; the system suggests it from the supplier and
the items, one tap to confirm or skip. **Yuvika supplies both sides** (orthotics on printed bills for the pharmacy,
procedure-room goods on handwritten slips), so the supplier alone never decides the lane.

**His rulings that bind every change here:** one purchase = one PDF (bill and warranty cards together) · a Dr MK expense
keeps its warranty and the renewals list reminds him · pathology purchases have their own lane · **the split between
clinic expenses and MK expenses is not finalised — never guess it** (electrical, plumbing and similar papers come as
bills, estimates, challans and handwritten slips, mostly MK) · the 61 test scans stay (S468, his word) · staff flows
never make staff wait or confirm twice.

## 5 · What is NOT the scan app (and is often confused with it)

- **Patient papers** — outside X-ray / MRI / CT reports, discharge papers, blood reports, the *Check karein* list — are
  the finance app's records (`/root/finance/records.py`, `records_inbox/`, the parent's; kits S333 … S346). The word
  "papers" there means a patient's papers, not the clinic's.
- **The pharmacy bill's life after the scan** — paired with its Marg bill (`/root/finance/scan_register.py`), Amir's
  steps, *Scan ka kaam* on Purchase orders (S440's server half), the month's bill register — the Sanjeevni chat's.
- **The working-paper shelf** (`D:\Downloads\_kbtools\PAPERS.bat`) — the estate's record-keeping, the parent's.

## 6 · How a change is made here

1. Take the kit number on the board before the folder is named; a PLANNED line first if the change touches
   `scanner_widget.js` (seven surfaces, two apps) or any file the parent or the Sanjeevni chat owns.
2. Read the live file from the newest bundle and hash it against its pin; **read `asset_register.py` whole before its
   next patch once its drift reaches 5.** The Register records it at 6 after S466, then **0 — read whole after D664's
   three slices, no kit since**; `clinic_papers.py` 0 (S466 replaced it whole). Count from there.
3. Build by `BUILD_NORM_v1.md`: exact counted edits; a walk on made-up rows in a scratch copy of the app and its
   database; a negative control that must go red; the installer's order (gates → pins → walk → backups `.bak_<kit>_<from8>`
   → place → `systemctl restart assetapp` only → `/scanapp/healthz` → the data step → the undo line).
4. The publish is his double-click; the server line is one line with its own pull.
5. After the install: the pins read back from the box (the installer prints them), DECLARED-PENDING until the next
   nightly bundle; the page read by a sub-agent as the person who will use it (reads only).

## 7 · Kit history (the scan app's)

S175/S177 (the asset register v1.11, the intake, Sarvam) · S195 (the non-cash scan) · S207 → S219 (scanner v2, finalised
on seven surfaces) · S222 (the app inside the portal PWA; the `/scanapp` prefix) · S286/S287 (the backup and its Drive
leg) · S409 (five lanes) · S435 (the bill's month asked at intake; the person's month beats the OCR's date) · S440 (the
Sanjeevni chat's *Scan ka kaam*, with declared edits here) · S441 (no waiting, no questions; the after-the-fact checks;
the rate page) · S464 / S465 / S466 (D664 in three slices: the papers to sort and the three groups; join with undo; the
Dr MK expense warranty on the renewals page). Each kit's README in `deploy_kits/` carries its own undo line.

## 8 · Open at the branch

- **D689 item 1** — the papers page gets four sections: *Resumes*, *Miscellaneous documents*, *Construction work*,
  *Personal* (there is no Personal section today; *Dr MK expense* is the nearest).
- **D689 item 2** — the challan flow: goods on a challan, the bill later; a challan kept as *goods received, bill
  awaited*, joined to its bill when the bill is scanned, deletable once the bill has come. Medicine suppliers' challans
  are the Sanjeevni chat's side.
- **Not built:** a warranty date offered from the scan's reading (S466 left it to a person).
- **His, open:** the clinic / MK expense split (D664) — not to be guessed.
- **Drift:** `asset_register.py` 0 and `clinic_papers.py` 0 at the branch (§6 step 2).

---
*SCANAPP_SYSTEM_BOOK — v1 · S305 (the parent), 11-Oct-2026 · the scan-app project's Book from its first session on;
each scan-app close that changes the app writes the next version into `deploy_kits/KB_canon_all/`.*

---
*SCANAPP_SYSTEM_BOOK — v2 · S306 (the Scan App project), 11-Oct-2026 · supersedes v1 (S305, the parent) in full; each scan-app close that changes the app writes the next version into `deploy_kits/KB_canon_all/`.*

---
*SCANAPP_SYSTEM_BOOK — v3 · S314 (the Scan App project), 14-Oct-2026 · supersedes v2 (S306) in full; each scan-app close that changes the app writes the next version into `deploy_kits/KB_canon_all/`.*

---
*SCANAPP_SYSTEM_BOOK — v9 · S345 (the Scan App project), 24-Oct-2026 · supersedes v8 (S341) in full; each scan-app close that changes the app writes the next version into `deploy_kits/KB_canon_all/`.*

---
*SCANAPP_SYSTEM_BOOK — v10 · S346 (the Scan App project), 25-Oct-2026 · supersedes v9 (S345) in full; each scan-app close that changes the app writes the next version into `deploy_kits/KB_canon_all/`.*
