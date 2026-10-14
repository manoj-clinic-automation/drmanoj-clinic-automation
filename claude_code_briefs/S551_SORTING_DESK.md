# S551_SORTING_DESK — brief for the build runner (Agent SDK, the API credits) — v4

*Written 14-Oct-2026 by the Scan App project (session 315). Kit **S551** was claimed on the board `_numbers` at the S314
claim of 04:2x IST 14-Oct (D722), with its PLANNED line (D646) on `/root/assetapp/asset_register.py`,
`/root/assetapp/clinic_papers.py` and the NEW `/root/assetapp/sorting_desk.py`. This file is the whole scope. Run by
`D:\Downloads\_kbtools\agent_build\run_build.py S551_SORTING_DESK`. v4 = v1 with three independent reviews taken in (R1:
40 points, 9 blockers; R2: 5 more; R3: 1 blocker, 4 corrections, 3 notes — heal() and equipment, the join's file order,
the Waiting floors, the installer's database variable, Personal expense's subgroup, the shared folder; v3 md5 b1cadbab); line numbers below (`AR:` asset_register.py, `CP:` clinic_papers.py) are from the 14-Oct bundle and move a
little in the live file — always find the anchor by its text.*

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** It places the finished kit in
`deploy_kits\S551_SORTING_DESK\`, writes `claude_code_briefs\REPORT_S551.md`, and stops. The Scan App chat checks the kit
(pins, walk, control, a cold review, the gates); then the owner double-clicks the publish and pastes one server line. This
overrides CLAUDE.md's "install and publish without asking" for this run only. **Nothing live is placed, nothing is
restarted, no live database row is written, the build lock is not needed** (nothing is placed).

## 0 · For the owner (the report's first 3–5 lines, plain English)

He and Shavez get **one sorting desk on the laptop**: the waiting papers on the left, the scan large in the middle, what
was read (editable) and one list *Where does it go?* on the right, one **Save — next paper**. Beside it: **Bills awaited**
(challans by supplier, each supplier set once to how it bills), the **Implant stock ledger** (owed, paid, balance per
supplier) and **The month** (section by section; it replaces the two old history pages in the menus). The scan app's header
reads **Scan app & assets** and its front page carries a **Switches** card. The desk is installed **switched off for
Shavez** until the owner opens it; the owner can use it at once.

## 1 · The owner's words (D722, D719, D710, D664 — all binding)

- 13-Oct 14:37 → 14-Oct 04:14: *"Look ok, build now"* = **FINAL** on the mock-up (four boards, §2). The build follows it
  line by line. **This includes a deliberate widening of today's rules: a paper already accepted can be changed on the
  desk (lane, place, what was read), by a person, audited.**
- 13-Oct 14:50: patient-related implant bills belong to the **surgical case pack** (another system, not built here). The
  scan app keeps **only the clinic's and his own papers**; a patient's paper is **set aside here, out of every total**.
- 13-Oct 14:47: implant challans and bills **he pays** are **his inventory (Implant stock)** with a ledger per supplier.
- 13-Oct 18:16: routine challan suppliers are set once to how they bill (§3.4).
- D664: **a section, a sub-section or whose expense a paper is is never guessed by the system** — only a person's Save.
  The clinic / MK split of construction papers is his, not to be decided.
- D710: **sorted = accepted** — a Save files it and accepts it (except a challan, §3.2); the approve/reject door stays.
- Never move a paper a person placed, except by a person's own Save on the desk.

## 2 · The specification — the four boards

The four boards are copied byte for byte in **`_scratch\S551_SORTING_DESK\mockup\`** (`Main.dc.html` the desk,
`Awaited.dc.html`, `Ledger.dc.html`, `Month.dc.html`, `canvas.json`) with the plan in words,
`S314_SCANAPP_FINAL_PLAN.md`. Read all of them first. The boards are a design tool's pages (`<x-dc>` markup and a small
`Component` class holding made-up rows) — **the layout, words, buttons and colours are the specification; the rows in
them are made up and are never copied into code, and their pre-selections (Yuvika → Procedure room, Krishna →
Construction) are made-up rows, not rules.** Where the boards and the plan differ, the board wins, **except three things
the plan adds and the owner wants: *Blank — discard* (§3.6), the third switch *Sorting desk for Shavez* (§3.7), and a
routine challan supplier's paper pre-choosing *Challan* (§3.3).**

Laid out for a **laptop** (1366 × 768 must work without page scroll; wider grows the scan). English, as the boards are.
**The desk and its three pages render their own full-width HTML** (the app's colours and fonts copied from `BASE`'s CSS /
`PALETTES`), **not `AR.page()`** (its `main{max-width:1080px}` and header would not fit). Server-rendered HTML plus small
plain `fetch` script — no new library, no CDN, no build step. A flash from a helper is never relied on; results are read
from return values and the audit.

## 3 · What to build

### 3.0 Where the code goes (the consolidation — `asset_register.py` is at drift 5)

1. **Read `/root/assetapp/asset_register.py` whole first** and `clinic_papers.py` whole. Record in the report: line counts,
   the functions and routes you rely on, and every name below that differs in the real code.
2. **All new behaviour goes in ONE NEW module `/root/assetapp/sorting_desk.py`**, mounted the way `clinic_papers.py` is
   (one guarded `init(ar)` from `asset_register.py`, AR:4207-4219; a failure to import leaves the app running and is
   logged). **Routes are registered without the `/scanapp` prefix** (the WSGI middleware AR:4178-4199 strips it):
   `/desk`, `/desk/awaited`, `/desk/implants`, `/desk/month`, and JSON routes under `/desk/api/…`; script fetches use
   `url_for(...)` (script root included).
3. **The doors are Flask views that commit, flash and redirect** — `bill_lane` (AR:3629, `POST /bills/<id>/lane`),
   `set_group` (CP:854, `POST /bills/<id>/subgroup`), `set_pe_who` (CP:1521), `join_page` (CP:399), `bill_dup` (AR:3665),
   `bill_edit` (AR:3484). **The desk does not call them.** It reproduces each door's rule in one small helper per action
   inside `sorting_desk.py`, **with no commit**, and **Save commits once**. The callable helpers it reuses (no commit):
   `clinic_papers._accept(db,bid,who)` CP:889, `_challan_mark_joined(db,page,head)` CP:1313, `_supplier_key` CP:1179,
   `MONTH_OF` CP:949, `suggest` CP:224, `SUB`/`GROUP_OF`/`CONSUMABLE`/`SECTIONS`/`SORT_LANES` CP:73-92;
   `AR._audit_bill(db,bid,action,detail)` AR:2870, `_dup_by_triple` AR:2992, `_mark_dup` AR:3016,
   `_lane_kind_status` AR:2853, `_private_s544` AR:3136, `_norm_date`, `_num`, `_set_late`, `upsert_vendor`,
   `setting_or`, `checker_required` AR:710, `is_owner` AR:724.
4. **The join is shared, not copied:** a counted edit in `clinic_papers.py` moves `join_page`'s per-page loop into
   `join_pages(db, head, pages, who)` (no commit, no flash) that both `join_page` and the desk call. `join_pages` does
   exactly what the loop does today, the merge included (`S441._merge_pdf` writes a new file, then the rows record it); it
   does not commit — the desk's Save commits once after it. A Save that fails and rolls back leaves an unused merged file on
   disk, never a deleted or changed one. `join_pages` keeps the `_page_ok` check (CP:339-346): an approved paper cannot
   become a page, so *A page of another paper* is offered only for a draft or captured paper.
5. **Counted, anchored edits in `asset_register.py` only:** (a) the guarded mount; (b) the header *Asset Register* →
   *Scan app & assets* (page title and top bar; the portal's tile is the parent's and is **not** touched); (c) the bills
   list's instant lane drop-down removed (the row links to the paper); (d) the edit page's heading reads *Edit bill* when
   editing (a flag through `_bill_form_page`; `BILLFORM_TPL` AR:2410 is shared with `/bills/new`), and saving keeps `kind`
   when it is Lab, Expense, Document, Pharmacy or Challan (today the form's select, AR:2427, can only post
   Consumable/Asset/Pharmacy, so a Lab paper becomes Consumable — the Consumable/Asset choice stays on clinic-lane papers);
   (e) the Month list on a paper's page (`bill_view`, AR:2701) = the four months + the bill's own month (`bill_month`, else
   `bill_date`'s) + the 12 months before it, and `bill_month_set` (AR:3611) accepts any `YYYY-MM` from 2015-01 to this
   month — `_month_choices` / `_good_bill_month` stay unchanged for the intake; (f) the Switches card on the scan app's front
   page (§3.7); (g) the menu links to the two old history pages (bills list AR:2393-2394, dashboard tile AR:1269) point to
   *The month*, and `/purchases` carries one banner line "Replaced by The month — open it"; (h) `POST /bills/<id>/reread`
   (AR:3566) refuses a paper with `subgroup='patient_paper'`.
6. **Counted, anchored edits in `clinic_papers.py`:** add to `SUB` `implant_stock: "Implant stock"`,
   `clinic_equipment: "Clinic equipment"`, `patient_paper: "A patient's paper"`; a new tuple
   `APART_KEYS = SECTION_KEYS + (those three)` used by `month()`'s filter (CP:965) and `stand()` (CP:789-792) — **not added
   to `SECTIONS`** (the old paper page offers no button for them; only the desk sets them); `heal()` (CP:918-933) and
   `_accept()` skip `COALESCE(doc_kind,'bill')='challan'` unless `challan_state='final'`, and `heal()` also skips
   `subgroup='clinic_equipment'` (a manager's equipment Save waits for the owner's own Save, §3.1); `join_pages` (item 4); banners on
   `MONTH_TPL` (CP:737) and `CHALLANS_TPL` (CP:1226) pointing to the new pages; the papers page's links (CP:615) to them.
7. **`scanner_widget.js` is NOT touched** (seven surfaces). `claude_reader.py`, `claude_reread.py`, `sarvam_ocr.py`,
   `scan_checks_s441.py`, `packs.py` are read only.
8. **`sorting_desk.ensure()`** (run at mount, and by the installer first) creates its tables and adds its columns
   tolerating the two-gunicorn-workers race (catch "duplicate column" / "already exists", as CP:143-150 does).

### 3.1 Who may open what (roles, not usernames)

- The desk and its three pages: **`checker_required`** — role `owner` or `manager` (AR:710-721). Shavez is login
  `shavez`, role manager. A synthetic `reception` login (portal staff) gets 403; no login → the login redirect.
- **Owner-only** = role `owner` via `is_owner()` / `_private_s544`, exactly as the papers page (the seed also gives
  `bhawna` the owner role): the **Personal** section and its papers (never in a manager's list; file and reading refused —
  the F-891 guard), the *Personal (you only)* button, and the Switches.
- **Clinic equipment / Asset-kind:** a manager's Save files the paper (lane, section, fields) but leaves it unaccepted with
  the line "Waiting for Dr Manoj's Save"; the owner's Save accepts it (today's `bill_approve` rule, AR:3541-3542).
- **The switch `desk.on`** (read `setting_or('desk.on','off')`; absent = OFF): while OFF the owner uses the desk fully and
  a manager sees one line, *"The sorting desk opens when Dr Manoj switches it on."* The old papers pages keep working
  either way (the manual path).

### 3.2 The destinations — "Where does it go?" (one list, the board's six groups)

One table `DESTINATIONS` in `sorting_desk.py`. Sections and groups live in **`bills.subgroup`**. Consumable keys:
`procedure`, `xray_small`, `xray_11x14` (`xray` = size not known — on the desk neither size is pre-chosen and Save needs
one), `others`; sections `construction`, `resume`, `misc`, `personal`; new `implant_stock`, `clinic_equipment`,
`patient_paper`. `SORT_LANES` (CP:92) are `clinic`, `other_doc`, `owner_expense`; consumable groups only on `clinic`.

| group | choice | lane | subgroup | status / kind |
|---|---|---|---|---|
| Clinic consumables | Procedure room · X-ray small film · X-ray 11 × 14 · Others | `clinic` | `procedure` / `xray_small` / `xray_11x14` / `others` | `_accept` (sorted = accepted) |
| Clinic | **Implant stock** | `clinic` | `implant_stock` | `_accept`; into the ledger (§3.5); out of consumables totals |
| | **Clinic equipment** | `clinic` | `clinic_equipment` | `_accept` (owner; §3.1); no asset is created — the month row offers "+ asset record" (the bill page's existing `asset_edit?bill_item=` link, AR:2697) when none is linked |
| | Construction work | **left on its lane** (clinic, other_doc or owner_expense) | `construction` | as `set_group` does |
| Personal | Personal expense → **Dr MK / Dr Bhawna** | `owner_expense` | kept if a section (`construction`, `resume`, `misc`, `personal`); a consumable group or a new desk key is cleared (NULL), audited as `subgroup` | `Expense`/`captured`; `pe_who` NULL = Dr MK, `'bhawna'` = Dr Bhawna; Dr MK pre-chosen |
| | Personal (you only) | left on its lane (a SORT_LANE; else `other_doc`) | `personal` | owner only |
| Handed over | Pharmacy — Sanjeevni | `pharmacy` | NULL | kind `Pharmacy`, status `captured` — **kind `Challan` when the paper is a challan** (as the intake does, AR:3334-3338, so the Sanjeevni register does not take it) |
| | NK Pathology | `lab_purchase` | NULL | `Lab`/`captured` |
| Documents | Resumes / Miscellaneous | left on its lane (a SORT_LANE; else `other_doc`) | `resume` / `misc` | as `set_group` does |
| Not here | **A patient's paper — surgical case pack** | `other_doc` | `patient_paper` | `Document`/`captured`; never accepted; out of every total; never read again |

- **The desk's lane helper** (not `bill_lane`) may move an **approved** paper off the clinic lane (the owner's widening,
  §1): it sets the target lane's kind and status from `_lane_kind_status` (pharmacy → `Pharmacy`/`captured`; lab →
  `Lab`/`captured`; owner_expense → `Expense`/`captured`; other_doc → `Document`/`captured`), keeps `approved_by` /
  `approved_at` as history, and audits. Into `clinic`: status `draft`, then `_accept`. So a moved paper leaves every
  `status='approved'` spend total (the dashboard tile AR:1264, `/purchases` AR:3863-3890) and a handed-over pharmacy paper
  is seen by the Sanjeevni register (`kind='Pharmacy' AND status='captured'`).
- **Audit action names are load-bearing:** a lane change writes exactly **`relane`** and a place change exactly
  **`subgroup`**, both with the person's display name (detail `{"from","to","status_from","status","via":"desk"}`) — this
  is what makes S532's `auto_home` / `heal_auto` treat the paper as person-placed (`_audit_marks` CP:1374-1390) and never
  move it. Every desk Save also writes **`desk_saved`** on the bill.
- **A challan** (`doc_kind='challan'`, state `awaiting`) is **filed but not accepted**: Save sets its lane / subgroup and
  leaves status `draft` / `captured`, so it can still be joined (`_page_ok` CP:341 refuses an approved page). A
  `challan_state='final'` paper (paid-on-challan, §3.4) is accepted like a bill.
- **One-way handover:** the desk never lists a pharmacy-lane paper and never moves a paper **off** the pharmacy lane (the
  Sanjeevni side may have paired it; the paper page's own lane form stays the door for that).
- **Header fields of an approved paper** are corrected by the desk's own helper with `bill_edit`'s normalisation
  (`_norm_date`, `_num`, `_set_late`) — never by deleting its `bill_items`.
- **`packs.py` is the parent's and is NOT edited.** The desk changes which rows reach a pack only through the lane a person
  chooses. FOR THE PARENT (the report): the clinic lane is not in any pack yet (D710 (2) waits) — when it is, it must exclude
  `implant_stock`, `clinic_equipment`, `patient_paper`; and a construction paper left on `owner_expense` is in 8.2 today.

### 3.3 The desk — `/desk` (board `Main.dc.html`)

- **Top bar:** *Sorting desk* · "N papers waiting · newest first" · links *Bills awaited* · *Implant stock ledger* ·
  *The month* · the switches chip.
- **Left — Waiting** (folds to a 44-px strip, as the board): newest first; each row stamp, month (`MONTH_OF`), supplier,
  one hint line. **Waiting =** live papers (not rejected, `dup_of IS NULL`, `page_of IS NULL` — except an S441 set-aside
  listed under §3.6), **never a pharmacy-lane paper**, that are one of: (a) a `clinic` paper with no subgroup — a challan
  included; (b) an `other_doc` paper with no subgroup; (c) scanned on or after the floor `desk.floor` (setting; the
  installer sets it to the install day, so old scans do not flood the list), a non-pharmacy paper with a §3.6 flag not yet
  answered — misread date / nothing read: no `desk_saved` row on the bill at all; the D710 hold: no `desk_saved` after its
  latest `d710_not_accepted` (heal() re-writes that row at each start while the paper is still held); an S441 set-aside:
  no `desk_dup_same` / `desk_dup_restored` row; (d) scanned on or after `desk.floor`, a non-pharmacy bill (`doc_kind` not
  challan) with no `desk_saved` row, of a supplier key that has an awaiting challan (board: Gaurav Traders). **No paper is special-cased in code by its stamp.**
- **A box "Open B-____"** above the list loads any paper the person may see (never pharmacy; Personal only for the owner),
  so a sorted paper can be changed again.
- **Middle — the scan:** the paper's own file (`/bills/<id>/file`) in the laptop browser's own PDF viewer (an `<iframe>`;
  every page and zoom by the viewer); **Turn ↻** rotates the view only (nothing is written to the file); the line
  "B-xxxx · supplier · scanned <date>".
- **Right — What was read — correct anything:** Supplier · Bill / challan no · Date · Amount (`total_amount`, rupees,
  REAL), editable, and one line of the items with quantities. Items and the kind suggestion come from **Claude's reading**
  (`claude_reading(bill_id, at, model, ok, doc_kind, data, error)`; `data` JSON holds `made_out_to` and `items[]` with
  `name, qty, unit, rate, amount, …` — read `claude_reader.py`), **rows with `ok=1` only; tolerate the table being
  absent**; else the bill's own `bill_items`.
- **What kind of paper:** **Bill · Estimate slip · Challan**. Pre-chosen from the paper's `doc_kind`; else Claude's
  `doc_kind` mapped `tax_invoice`/`bill` → Bill, `estimate`/`quotation` → Estimate slip, `challan` → Challan, `other`/none →
  nothing; else, for a supplier set to *monthly* or *sometimes* (§3.4), Challan. Saved in `bills.doc_kind` as
  `bill` / `estimate` / `challan` (today only `'challan'` or NULL exist). Challan → `challan_state='awaiting'`
  (`'final'` for a *paid on challan* supplier). An estimate counts in money at once.
- **The supplier note** (amber, as the board) when the supplier has a billing mode or open challans.
- **This bill covers these challans** (green, as the board) when the kind is Bill and the supplier key has open challans
  (the desk's **own** rule, not `challan_for_bill`): *monthly* → the challans of the bill's month, **pre-ticked**;
  *sometimes* / no mode → every awaiting challan of the supplier, **unticked**, oldest first, with age; one line comparing
  the bill's items with the ticked challans' items on a normalised name: "N of M match · K extra on the bill · J missing".
  Save joins every ticked challan through `join_pages`.
- **Where does it go?** the board's six groups of buttons (*Personal (you only)* only for the owner); *Personal expense*
  shows **Dr MK / Dr Bhawna**; one grey line from the board's notes for the chosen destination.
- **Suggestions are shown, never saved.** Pre-selected only from: (a) the paper's own current lane / subgroup; (b)
  `suggest()` **only** when it returns `kind=='sub'` with a value in `CONSUMABLE` **and the supplier is not Yuvika**
  (`_hits(vendor, ['yuvika'])` → nothing pre-selected, ever); (c) Claude's reading `made_out_to == 'patient'` → *A patient's
  paper* pre-selected with the line "Claude read this as made out to a patient — check". A `suggest()` section or lane
  answer (construction, resume, owner_expense, pharmacy) is shown as a grey hint line only (D664).
- **"A page of another paper — join into B-____"** → `join_pages`.
- **Save — next paper** (disabled, reading *Choose where it goes*, until a destination is chosen; an X-ray paper needs its
  size): one POST — fields, kind, destination, joins, Dr MK/Bhawna, a flag's answer — **in one transaction, one commit**,
  audited, then the next waiting paper opens **without a full page reload** (JSON back; the list updates). Under it:
  *"Save files it, accepts it and opens the next paper."* / *"N saved this sitting — each can be changed again from its own
  page."*
- **Speed:** the desk under 2 s on the laptop; switching papers fetches one paper's JSON.

### 3.4 Bills awaited — challans by supplier (board `Awaited.dc.html`; `/desk/awaited`)

- NEW table `challan_supplier(supplier_key TEXT PRIMARY KEY, name TEXT, mode TEXT NOT NULL CHECK(mode IN
  ('monthly','sometimes','paid')), set_by TEXT, set_at TEXT)`. A supplier gets a card when it has an awaiting challan
  (**pharmacy-lane challans are not listed — the Sanjeevni side, D689 item 2**); its mode is one tap on the card, audited
  in `desk_audit`.
- **Monthly:** challans wait for the month's bill; **amber when there is no bill by the 10th of the next month**. **A bill
  now and then:** wait **without amber**, oldest first, with age. **Paid on challan:** the challan or estimate **is** the
  final paper (`challan_state='final'`), never waits; *Paid on · Amount · Note payment* records the payment on it (NEW
  columns `bills.paid_on TEXT`, `bills.paid_amount REAL` rupees; audited on the bill). **Any other supplier:** waits,
  amber after `setting_or('d710.challan_amber_days', 15)` days — today's rule. Setting a supplier to *paid* turns its
  awaiting challans `final` (audited each).
- `challan_state` values: `awaiting`, `joined`, `closed`, `deleted` (today) and **`final`** (new: the paper is the bill).
- **Every date rule takes `today` as an argument** (default `date.today()`), so the walk can pass a made-up today.
- Today's `/papers/challans` keeps working with one banner line pointing here.
- **Packs (fact, not to change):** `packs.py` `build_bundle` (packs.py:1777-1801) selects `lane=? AND status<>'rejected'`
  with no `doc_kind` filter — so an awaiting challan on `lab_purchase` or `owner_expense` is in the 8.1 / 8.2 bundle today
  until it is joined (the join marks it rejected). **Do not edit `packs.py`.** FOR THE PARENT (the report): `build_bundle`
  should exclude `doc_kind='challan' AND COALESCE(challan_state,'awaiting') <> 'final'`, and decide what a `final`
  paid-on-challan paper carries (its `paid_amount`).

### 3.5 Implant stock ledger (board `Ledger.dc.html`; `/desk/implants`)

- Left: every supplier key with a paper in `subgroup='implant_stock'`, with its balance. Right: **Owed (bills and priced
  challans) · Paid · Balance**; rows in date order — Date · Paper · Kind · Items · Owed · Paid. The rows are
  `subgroup='implant_stock' AND (status<>'rejected' OR challan_state='joined')`; a joined challan is shown with its items
  but owes nothing (its bill owes — never twice); an unpriced awaiting challan shows items, no amount; a `final` paper owes
  its `total_amount`.
- *Paid on · Amount · How (Bank / UPI · Cheque · Cash) · Against (bill nos) · Note payment* → NEW
  `implant_payment(id INTEGER PRIMARY KEY, supplier_key TEXT NOT NULL, day TEXT NOT NULL, amount REAL NOT NULL, how TEXT
  NOT NULL, against TEXT NOT NULL DEFAULT '', by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT
  NULL DEFAULT '')` (rupees, like `total_amount`; append-only — a mistake is voided, never updated). **Paid = live
  `implant_payment` rows + `paid_amount` of `final` papers of that supplier** (two different records, never the same paper
  twice: the ledger's Note payment writes only `implant_payment`; Bills awaited's writes only the paper).
- **Checked against their statement up to today** → NEW `implant_check(supplier_key TEXT, upto TEXT, by_whom TEXT, at
  TEXT)`; shown top right "checked up to <date>" or "not yet checked against a statement".
- A patient's paper never appears here. The foot line as the board.

### 3.6 The flags the desk shows (the safety fixes)

- **A misread date:** a `bill_date` before 2015-01-01, after 31-Dec of next year, or more than 60 days from the scan's
  `created_at` → an amber line "date looks misread — check".
- **A double shown, not silently held:**
  - (a) **the D710 hold** (`_accept` wrote `d710_not_accepted`, no `dup_flag`): "Looks like a second scan of B-xxxx" with
    *It is the same — set aside* = `_mark_dup(db, bid, first, 'desk')`; *Not the same — keep* = `dup_flag='no'`, audit
    `not_duplicate`, then accepted by the desk's helper without the triple check, audit `d710_accepted_by_person`.
  - (b) **an S441 set-aside** (`status='rejected', dup_of, dup_flag='yes'`, scan_checks_s441.py:381-386): listed only
    when set aside in the last `setting_or('desk.s441_days', 30)` days and not yet answered on the desk; *Same* = no change,
    audit `desk_dup_same`; *Not the same* = status back to the lane's status, `dup_of=NULL`, `dup_flag='no'`, audit
    `desk_dup_restored` with the old values.
  - Both inside the Save transaction.
- **Nothing read:** "Nothing could be read — type what you see".
- **Blank — discard** (the plan's choice): marks the paper `rejected` with audit `desk_blank` (never a delete); offered
  beside *A page of another paper*.

### 3.7 The month, section by section (board `Month.dc.html`; `/desk/month`) and the Switches card

- A month picker (‹ previous · month · next ›), the month = **`clinic_papers.MONTH_OF`**, supplier spellings merged by
  `_supplier_key`. One collapsible card per section: **Procedure room · X-ray films (small / 11 × 14 / size not known) ·
  Others · Implant stock · Construction work · Clinic equipment** — "N bills · N estimate slips · N challans", the total,
  and the items (Item · Quantity · Rate now · Rate before = the item's last rate in an earlier month). Awaiting challans
  count **by quantity only**; an estimate and a `final` challan count in money. Clinic-equipment rows link to their machine
  or offer "+ asset record" (owner).
- Right: **Kept apart** (Pharmacy — Sanjeevni N scans · NK Pathology N · Personal expenses Dr MK N · Dr Bhawna N · A
  patient's paper N) and **Not in the totals** (challans waiting — quantity only · papers still to sort — *open the desk*).
- **Equality:** for the three consumables groups, a month's money on this page equals the old `/papers/month` page's
  (endpoint `d664_month`) whenever the month has no `final` challan; a `final` challan adds exactly its amount.
- Replaces *Clinic consumables by month* (`/papers/month`) and *Consumption & spend* (`/purchases`, owner-only, AR:3812)
  **in the menus** (§3.0 items 5g and 6); both old pages stay reachable with a banner.
- **The Switches card** on the scan app's front page and on *The month* (owner only): *Smart scanner* (`scan.cv`;
  shows ON only when `AR._scan_cv_on()` is true, AR:3939-3944) · *Reception buttons* (`scan.lanes5`) · *Sorting desk for
  Shavez* (`desk.on`) · a link *Claude reading →* to `/admin`. Each is a small form posting to the desk's own owner-only
  route **`POST /desk/switch`** with `key` ∈ {`scan.cv`, `scan.lanes5`, `desk.on`}, `on` ∈ {1, 0} and `back`; it writes
  the statement `/admin` uses (`INSERT OR REPLACE INTO settings(key,value) VALUES(?, 'on'|'off')`), records the change in
  `desk_audit`, and redirects to `back` (checked by `AR._safe_from`). (`/admin` always redirects to itself, so the card does
  not post there.) `/admin` itself is not changed; the app has no CSRF protection and none is added.
- **Audit:** bill changes use `_audit_bill`; everything without a bill (supplier modes, payments, voids, statement checks,
  the switch) goes to NEW `desk_audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, who TEXT, action TEXT NOT NULL, detail TEXT)`.

## 4 · Pins — FROM bytes. Read each on the box first; a different byte = STOP that file and report

- `/root/assetapp/asset_register.py` **`3d5a36e3f9dc398a948f70a87f12d513`** (S550; drift 5 — read whole).
- `/root/assetapp/clinic_papers.py` **`5b197fb5718f8d28ed8de6c0cafc9ab0`** (S544.1).
- Read only, each hashed and named in the report: `/root/assetapp/scanner_widget.js` `1143c77b13ae62652d4d961a92b9a9ab`
  (**never edited**), `/root/assetapp/claude_reader.py` `3894dc2358abd875ee61ced7619e1e1b`,
  `/root/assetapp/claude_reread.py` `47548ab97c55a1f4fb8d5d1a608a1681`, `/root/shared/scan_checks_s441.py`
  `b9ba6839ec7979cb709909214d6a0b69`, `/root/finance/packs.py` `d86d351a46a1ba4da7d0e615da0deb1a` (the parent's).
- NEW `/root/assetapp/sorting_desk.py`.
- The board's `_numbers` claims cannot be read from this run (the S552 run could not): read
  `deploy_kits\KB_canon_all\START_HERE_SESSION_315.md` and the newest `REPORT_*.md` in `claude_code_briefs\` for any newer
  PLANNED line on these files, and say so in the report.

## 5 · Never

- edit `scanner_widget.js`, `packs.py`, `finance_app.py`, `portal.py`, `tile_grants.json`, the DUTY_MAP, or anything under
  `/root/finance/` (the Sanjeevni files `scan_register.py`, `purchase_app.py` included); read or write `finance.db`;
- guess a section, a sub-section or whose expense a paper is (D664); pre-select anything for Yuvika; save a suggestion
  without a person's Save; special-case a paper by its stamp;
- move a paper off the pharmacy lane; delete a file or a row (mark: `rejected`, `voided_at`, `final`);
- import the app against the live database or uploads; write a real row; place a file on the box; restart a service;
  publish; push;
- put a phone number, a key, a token, a patient's name or any real figure in the kit, the walk, the log or the report
  (made-up rows are built at run time; F-185). Patient files never leave the box.

## 6 · The walk, the control, the rehearsal (BUILD_NORM_v1, binding — read `deploy_kits\KB_canon_all\BUILD_NORM_v1.md`)

- **Isolation first (on the box, in `/tmp/s551dev/`, removed at the end).** Copy the module files into
  `/tmp/s551dev/app/`. Read the service's database path from `systemctl show assetapp -p Environment` the way
  `deploy_kits/S550_CLAUDE_READS_SCAN/install_s550.sh` (lines 31-35) does — **never print the rest of that line** — and copy
  that database with SQLite's backup API to `/tmp/s551dev/assets.db`. **Before the import** set
  `ASSETS_DB=/tmp/s551dev/assets.db`, `ASSETS_UPLOADS=/tmp/s551dev/uploads`,
  `SCANAPP_ANTHROPIC_KEY_FILE=/tmp/s551dev/key/anthropic.key` (made-up content),
  `SCANAPP_ANTHROPIC_URL=https://made-up.invalid/v1/messages`, `CLINIC_PORTAL_DIR=/tmp/s551dev/no_portal` (the portal's SSO
  is then inert; the walk logs in by session as made-up local users), `FINANCE_LOCAL_URL=http://127.0.0.1:9` (nothing
  listens), `SHARED_LIB_DIR=/tmp/s551dev/shared` (a copy of `/root/shared`, so nothing on `sys.path` comes from a live
  folder), and **unset** `SARVAM_API_KEY` and `ANTHROPIC_API_KEY` (check whether `sarvam_ocr` reads a key from anywhere
  else and isolate that too). Importing runs `init_db`, migrate, the seeds and `clinic_papers.init`'s heals — on the copy
  only. `walk_s550.py` lines 70-90 is the model. Copy `asset_register.py`, `clinic_papers.py`, `claude_reader.py`,
  `claude_reread.py` (and `sorting_desk.py` for the new run) into ONE scratch folder, `sys.path.insert(0, <it>)`, import
  with `importlib.util.spec_from_file_location`, and **assert each module's `__file__` lies under that folder**. **The new
  walk and the negative control each run in their own `python3` process**, never one interpreter (Python caches
  `clinic_papers`, `claude_reader`, `sorting_desk`). Flask's test client; no port, no service. **Made-up rows are INSERTed into the copy, never created through `/intake`** (no reader thread, no paid call).
- **Made-up suppliers differ in their first two words** (`_supplier_key` keeps two): `WALKA MONTHLY TRADERS`,
  `WALKB SOMETIMES STORES`, `WALKC OTHER AGENCIES`, `WALKD IMPLANT SURGICALS`, plus the variant
  `Walka Monthly Traders Pvt Ltd` that must merge; never a real name. **The walk passes a made-up `today` of 2031-06-15**
  and dates rows relative to it; one row with `bill_date` in 2029 checks the misread flag.
- **Logins:** owner (a seeded owner user), manager (a made-up manager user in the copy), and reception faked by patching
  `current_user` / `_sso_user` to `{'role':'reception'}` (a `users` row cannot carry it, AR:92); no login → the redirect.
- **Cover:** every destination of §3.2 and *Blank — discard*, read back (lane, subgroup, status, kind, `pe_who`,
  `doc_kind`, `challan_state`); a pharmacy handover equal to `_lane_kind_status`'s row, and a pharmacy **challan** handed
  over as kind `Challan`; an **approved** clinic paper moved to *A patient's paper* (status `captured`, out of the
  dashboard's approved total, `relane` audited); a grouped clinic **challan** stays draft **after a re-import (heal)** and
  is then joined by a bill (monthly: pre-ticked; sometimes: unticked; the item-compare line); a paid-on-challan payment;
  the three challan modes' amber rules and the 15-day default against the made-up today; the implant ledger (owed / paid /
  balance; a joined challan counted once; a voided payment ignored; a `final` paper's `paid_amount` counted); **after the
  saves, the app is re-imported and nothing a person placed moved** (auto_home off them); the Personal section hidden from
  the manager (list, file, reading, button, Open box) and shown to the owner; a manager's Clinic-equipment Save left
  unaccepted, the owner's accepted; the switch OFF (manager gets the line, owner allowed) and ON; Yuvika never
  pre-selected; Claude's `made_out_to='patient'` pre-selects *A patient's paper* but saves nothing until Save; the D710 hold
  and an S441 set-aside each answered both ways; the month page's three consumables groups **equal** to `/papers/month`
  for a month with no `final` challan, and a `final` challan adding exactly its amount; a patient's paper absent from every
  total and counted in *Kept apart*; reread refused on it; the edit page keeps a Lab paper's kind and reads *Edit bill*;
  `bill_month_set` accepts a month 14 months back while the intake still refuses it; the bills list has no lane drop-down;
  the header reads *Scan app & assets*; a reception login gets 403 on every new route; page sizes and the desk's first-load
  time printed.
- **The negative control:** the same walk against the **live** (old) files must go **RED** (print which checks fail and
  how many).
- **The installer** `install_s551.sh` reads from the environment, as `install_s550.sh` lines 12-35 do:
  `S551_APP_DIR` (default `/root/assetapp`), `S551_SERVICE` (`assetapp`), `S551_HEALTH_URL`
  (`http://127.0.0.1:8030/healthz`), `S551_PYTHON` (`python3` — the system python the service runs, F-53; also compile with
  `/root/wa/venv/bin/python3`), `S551_RESTART_CMD` (`systemctl restart $S551_SERVICE`), and `S551_DB` / `S551_UPLOADS`:
  **the environment value when set**; else read quietly from `systemctl show "$S551_SERVICE" -p Environment --value`
  (`ASSETS_DB=` / `ASSETS_UPLOADS=`, never printed); else `$S551_APP_DIR/assets.db` and `$S551_APP_DIR/uploads`. Order: gates (the box, root, the files present) → FROM pins → rebuild the two edited
  files from the live bytes with `make_s551.py` (each anchor must match exactly once or it stops) and compare with the
  kit's TO pins → compile → walk + control on a scratch copy (`DRY=1` stops here) → backups `.bak_S551_<from8>` beside
  each file and `assets.db.bak_S551_<time>` by the backup API → place → `sorting_desk.ensure()` (tables, columns) and
  `desk.floor` = today if absent → restart → health 200 (a new route answers the login redirect — expected) → a
  plain-English line of what his pages now show → `desk.on` left absent (OFF) → the undo line. A second run says
  **ALREADY INSTALLED**. A failure after placing puts the backups back and restarts.
- **Rehearsed** by `rehearse_s551.sh` on a made-up root under `/tmp/s551dev/root/`: it sets every `S551_*` to the made-up
  root (`S551_DB` and `S551_UPLOADS` explicitly, `S551_SERVICE` to a made-up name), `S551_RESTART_CMD=true` and a stand-in health answer (a local `python3 -m http.server` serving a file named
  `healthz` on a free port), and **refuses to run if any resolved path begins `/root/` or the restart command contains
  `systemctl`**. Three outcomes: green; ALREADY INSTALLED; a forced red after placing that restores. Nothing restarts
  during this run.
- **The kit** `deploy_kits\S551_SORTING_DESK\`: `KIT_ID.txt` (first line `kit id S551_SORTING_DESK`), `README.md` (what,
  the undo line, the server line), `install_s551.sh`, `make_s551.py`, `sorting_desk.py`, `walk_s551.py`,
  `rehearse_s551.sh`, `PIN_FROM_*.txt`, `PIN_TO_*.txt`, `SUMS.md5`. No `.json`, no database, no copy of a live file. Then
  in the repository on manojz: `SUMS.md5` checked; `.gitignore` checked **last-match-wins** for every kit file (none
  ignored); the contact-number gate run exactly as `PUBLISH_ALL.bat` runs it
  (`python -B deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> <repo>`) on every new file — clean.
- The server line the README names (for the owner, after the chat's check and his publish):
  `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S551_SORTING_DESK/install_s551.sh`

## 7 · The report — `claude_code_briefs\REPORT_S551.md`

3–5 plain lines on top for the owner (what he will see; switched off for Shavez until he opens it; the three papers of his
plan — Shri Ram B-0001, Krishna Sales B-0015, AINDOS 1952 — and what the desk will show on each). Then the proof: the FROM
pins read; the whole-read line counts and every real name that differed from this brief; each counted edit (file, anchor,
count); the TO pins; the walk (checks, all green, sizes and time) and the control (red, which checks); the rehearsal's
three outcomes; SUMS, `.gitignore`, the gate; anything left undone and why. **Lines FOR THE PARENT:** `packs.py` should
exclude awaiting challans (§3.4) and, when the clinic lane enters a pack, the three set-apart sections (§3.2); a
construction paper on `owner_expense` is in 8.2; the portal tile's name *Scan app & assets*; **no DUTY_MAP change in this
kit — Shavez's sorting duty and its door `/scanapp/desk` when the owner switches the desk on.** The run's cost. **Nothing
installed, nothing published** — say so in the last line.

**If anything in this brief cannot be done as written, stop at that point, write what was done and why in the report,
and end the run. Do not improvise around a pin, a gate or a never.**
