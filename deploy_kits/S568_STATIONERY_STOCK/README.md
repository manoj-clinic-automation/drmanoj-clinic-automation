# S568_STATIONERY_STOCK — Stationery & packaging: the group, the item list and its stock, Add a paper from a file, the pack fix

**Why.** The owner's rulings D730 (his "Go", 09:24 IST 16-Oct-2026, to `S318_STATIONERY_PROPOSAL.md` v4). The brief:
`claude_code_briefs/S568_STATIONERY_STOCK.md` (v2), read whole with the independent review `S568_BRIEF_R1.md` (md5 `f1865e32…`) —
its replacement wording for every BLOCKER and CORRECTION is what was built. Board `_numbers` v450 → v451, PLANNED line D646.

**Fix round 1 (S568 FIX1, 16-Oct-2026 — the kit review `S568_KIT_REVIEW_K1.md` CORRECTIONS 1–3; same kit, revised in place, the FROM
pins unchanged).** (1) The stock follows where the paper is now: a paper's matched lines count only while it is still a live paper in
Stationery & packaging, or a challan / estimate joined into one — re-sorted on the papers page, re-laned, discarded as blank or set
aside, it adds nothing (computed when read: no data step). (2) "Stationery diya" follows the owner's mock-up (Issue.dc.html):
*Kya diya · Kitne · Kisko*, four large place buttons in a 2 × 2 grid, one Save, then "Ho gaya — <item> <qty> <unit>, <place> ko.
Stock mein ab <N>."; phone width first. (3) "Add a paper from a file" takes only a PDF or a photo (pdf, jpg, jpeg, png, webp, heic);
anything else is refused with one line, nothing saved. TO pins that change: `sorting_desk.py` `cd6823f1` → `695ba90b`, `stationery.py`
`3e5d5322` → `d11d7183`; the other three TO pins are unchanged.

**What changes.**
1. **"Stationery & packaging"** — a clinic consumables group beside Procedure room, X-ray films and Others (key `stationery`, in the
   eleven lists R1 C8 names): the desk's destination list (after Others), The month (its section after Others; `month_total` follows
   it), the papers page's chooser and counts, sorted = accepted (D710), the heal. **No existing paper is moved** (D664); the
   stationery words now *suggest* the new group (a suggestion only, never saved without a person — R1 note 16).
2. **The item list** — new module `stationery.py`, the owner-only page **Stationery** (in the scan app's one menu): name, unit, agreed
   rate, low-stock level, active / retired; "+ Add item"; edited in place; an item with moves is retired, never deleted.
3. **Received — from the desk, never twice.** With Stationery & packaging chosen, the desk shows the paper's lines (Claude's reading
   with its rate, else the paper's items): each line matched to a list item (a pre-match by name offered), **"+ Add to the list"**, or
   **"not a stock item"**; its quantity editable; a line left alone counts nothing and never blocks the Save; "nothing read" = one
   empty line to fill. A Save stores the matches as **snapshots** (never keyed on `bill_items.id`); a re-save replaces them (the old
   ones voided and kept). **Received is computed when read** (R1 B2, with FIX1): a paper counts only while it is a live paper in
   Stationery & packaging (the clinic lane, the group) — a challan and an estimate slip while live or joined into such a paper (a
   joined challan still counts); a bill only when no challan / estimate is joined into it; nothing else counts. A rate that
   differs from the list: "rate ₹x — list ₹y"; another unit: "unit differs".
4. **Issued — "Stationery diya"** (Roman Hinglish, the owner's mock-up): *Kya diya* (item), *Kitne* (quantity), *Kisko* — four large
   buttons Lab · Reception · Sanjeevni · Clinic (2 × 2) — one Save (no confirmation), then "Ho gaya — … Stock mein ab N.".
   Above the stock it is still saved, and flagged on the owner's page. The owner at once; **a manager only while
   `stationery.issue_on` is ON** (absent = OFF; a row "Stationery diya for managers" on his Switches card) — **installed OFF**; the
   reception login never. `MOCKUP_stationery_diya.html` is the screen for him to approve first (R1 C10).
5. **The inventory** (his Stationery page): per item in stock · received this month · issued this month by place · last rate paid ·
   a low-stock mark; this month's issues (above-stock flagged), the counts, the papers that fed the stock (links to the desk).
   **Count**: the first count of an item is its opening stock; a later count records the difference as "not accounted for" and sets
   the stock to the count (a manager with the switch ON counts on Stationery diya).
6. **The mixed-challan tick** "mixed: clinic + lab items" on a challan or bill (stored on the paper: `bills.mixed`, audited) —
   shown on the desk for Stationery & packaging and NK Pathology; "Mixed challans this month: N" on his page and in the supplier note.
7. **"+ Add a paper from a file"** (the desk's left column; owner and managers, managers only with the desk on): a PDF or a photo
   only (pdf, jpg, jpeg, png, webp, heic — a Word file is refused, FIX1) through `_create_intake_bill` itself (the same stamp, storage, double check, reading); the plain form offers the intake's own lanes
   and the challan tick. **One preset — "Sanjeevni pharmacy expense — paid by Dr MK's card"**: the pharmacy lane, `kind='Pharmacy
   expense'` (never 'Pharmacy') and `doc_kind='bill'` written by the intake's new optional `kind_over` **before its first commit**
   (R1 C4); paid **on the paper itself** (`bills.paid_on` / `paid_amount`, the day and amount typed) with one audit `paid {how: card,
   note: "Dr MK's card"}` — no payment row, no new mode (R1 B1). It is never moved by the system (`auto_home`, `supplier_history`,
   the heal), keeps its kind on the old edit page, and only the owner may re-lane it (audited). The Month: "Sanjeevni — pharmacy
   expenses" under Kept apart (count · total · paid by Dr MK's card), never in a section or the total; both pharmacy counts leave it out.
8. **The pack fix — THE PARENT'S `packs.py`, `build_bundle` only:** the S560 receipt/statement line and the challan line under it
   become one line, `xk_sql = " AND COALESCE(doc_kind,'bill')='bill'"` (R1 C3). Every bundle (8.1–8.4) takes bills and invoices only:
   an estimate slip and a paid-on-challan (final) challan no longer go to the accountants; a paper with no kind set stays in.

**Files and pins (FROM → TO).** `/root/assetapp/sorting_desk.py` `a053a222` → `695ba90b` (24 counted edits) · `clinic_papers.py`
`024464cc` → `6db07c12` (13) · `asset_register.py` `8b3c4551` → `e5356e0c` (9) · **new** `stationery.py` (absent → `d11d7183`) ·
**the parent's** `/root/finance/packs.py` `048d2ad8` → `e46264b8` (1). Read only, pinned: `asset_machine.py 7d4fdffc`,
`scanner_widget.js 10a8bb29`, `claude_reader.py 3894dc23`, `claude_reread.py d9b75e78`; Sanjeevni's `scan_register.py 904f07b1`
and `purchase_app.py 147201dd` (read, never edited; the walk runs the four readers' own queries). Every edit is an anchor found
exactly once in the live bytes (`make_s568.py`). **Data step** (the app's own `ensure`, additive, idempotent, after the database
backup): tables `stationery_item`, `stationery_line`, `stationery_move`, `stationery_count` (+ index `stationery_line_bill`) and the
column `bills.mixed` — no existing row changed. Restarts **assetapp**, then **clinic-finance** (S560's order and checks; only when
packs.py is placed). `stationery.py` is mounted by one guarded hook at the foot of `asset_register.py` after `sorting_desk.init`;
absent, the app runs as before.

**Kit.** `make_s568.py` (the patcher; `--cp-on` rebuilds S563's tidy comparison through S566's and S568's edits) · `stationery.py`
· `walk_s568.py` (W1, W2, I1–I8, Z1, and FIX1's I3F, I4F, I7F; `--expect-red` = the control on the live files; `--expect-red-fix1` =
the control on the round-0 kit's TO files; `--save-pages` = the Stationery diya pages; `--no-pack` when packs.py was stopped) ·
`lines_s568.py` (the earlier walks' lines S568 changes, written to copies only: S560 pack P2 / P8; the browser walk's button count) ·
`count_s568_pack.py` (the pack fix's per-bundle counts on a copy of the live data, counts only) · `install_s568.sh` ·
`rehearse_s568.sh` · `MOCKUP_stationery_diya.html` (FIX1: the built screen as rendered by the walk, in a 390 × 844 phone frame) ·
`walk/` (`browser_diya_s568.py`, FIX1's Stationery diya browser walk at 390 × 844, and the results of both PC headless-Chrome walks:
S560's frozen desk-layout walk with its one line from `lines_s568.py browser560`, and the diya walk with its round-0 control) ·
`PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Proof (16-Oct-2026, on the box in /tmp only, and in headless Chrome on the PC):** see `claude_code_briefs/REPORT_S568.md` (its
"Fix round 1" section) — S568's walk 14/14 green, the control 12 of 12 MUST_RED red, the FIX1 control on the round-0 kit I3F / I4F /
I7F red; the earlier walks through the rehearsal's outcome 1; the rehearsal's outcomes; the desk-layout browser walk 7/7 and the
Stationery diya browser walk 2/2 (its round-0 control red).

**Install (the owner, after publishing):** `bash /root/deploy/repo/deploy_kits/S568_STATIONERY_STOCK/install_s568.sh`
(`DRY=1` in front stops before placing.)

**UNDO (one line):** `\cp -p /root/assetapp/sorting_desk.py.bak_S568_a053a222 /root/assetapp/sorting_desk.py && \cp -p /root/assetapp/clinic_papers.py.bak_S568_024464cc /root/assetapp/clinic_papers.py && \cp -p /root/assetapp/asset_register.py.bak_S568_8b3c4551 /root/assetapp/asset_register.py && mv -f /root/assetapp/stationery.py /root/assetapp/stationery.py.off_S568 && \cp -p /root/finance/packs.py.bak_S568_048d2ad8 /root/finance/packs.py && systemctl restart assetapp && systemctl restart clinic-finance`
— then `/healthz` 200, `/finance/healthz` 200 and the md5s back at the FROM pins. The four new tables and `bills.mixed` stay (empty
of meaning to the old files; nothing reads them); the database backup `assets.db.bak_S568_<stamp>` is needed only if their rows
must be removed — say so before using it.
