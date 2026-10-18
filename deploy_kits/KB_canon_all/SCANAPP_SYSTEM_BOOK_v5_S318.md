# SCAN APP SYSTEM BOOK — v5 — what the scan app is, where it lives, how it is changed — brought current at the S318 close (the project's fifth session, 15 → 18-Oct-2026)

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
