# S568_STATIONERY_STOCK — brief for the build runner (Agent SDK, the API credits)

*Written 16-Oct-2026 by the Scan App project (session 318). Kit **S568** claimed on the board `_numbers` (v450 → v451)
with its PLANNED line (D646), which names the files below, the parent's `packs.py` included. The owner's word, 09:24 IST
16-Oct: "Go", to `claude/S318_STATIONERY_PROPOSAL.md` v4 (copy at
`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S318\S318_STATIONERY_PROPOSAL.md`). His rulings are **D730**.
Run by `D:\Downloads\_kbtools\agent_build\run_build.py S568_STATIONERY_STOCK`.*

**v2 — READ `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S318\S568_BRIEF_R1.md` (md5 `f1865e32…`, 2 BLOCKER · 10
CORRECTION · 9 NOTE) WHOLE BEFORE BUILDING. Its replacement wording for every BLOCKER and CORRECTION is binding and
REPLACES the text below where they differ.** In short:
- **B1** the Aumni card payment goes on the paper itself (`bills.paid_on` / `paid_amount`) plus one audit line "card" —
  no change to the payment table's allowed modes;
- **B2** received stock is computed when read, from saved line snapshots, with the review's explicit rules (joined
  challans are rows kept as rejected-but-joined, never deleted);
- **C3** the pack filter is `COALESCE(doc_kind,'bill')='bill'` (S560's pack walk lines P2 and P8 change on purpose);
- **C4** `kind` is written inside `_create_intake_bill` before its first save, through a new optional argument whose
  default is today's behaviour;
- **C5** guards in `auto_home`, `supplier_history`, the old edit page's kind list and the re-lane route;
- **C6** the two pharmacy counts leave out 'Pharmacy expense';
- **C7** line matches are stored as copies of the line, and an unmatched line never blocks Save;
- **C8** the group key `stationery` goes into the 11 lists the review names;
- **C9** managers only, with the switch ON, and never the reception login; a manager's Count is on "Stationery diya";
- **C10** the screen's mock-up is the owner's artifact `8VXHG1F62EvN6LqBEi5e9k` — follow it; the switch stays OFF;
- **C11** the walk checks all four Sanjeevni readers (`scan_register.py`, `purchase_app.py`, `porders.py` :1065,
  `order_sheet.py` :1381), read only;
- **C12** `stationery.py` as the review says: how it is mounted, where its tables come from, the installer's treatment of
  its absence, and the undo that removes it.

The review's NOTES are context, not changes.

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** The kit goes in
`deploy_kits\S568_STATIONERY_STOCK\` and the report in `claude_code_briefs\REPORT_S568.md`; then stop. Nothing live is
placed or restarted, and no live row is written. CLAUDE.md's "install and publish without asking" is overridden for this run.

## 0 · The owner's rulings (D730) — binding
1. **Printed stationery:** one paper, one place. A clinic paper goes to a new clinic consumables group **Stationery &
   packaging**; a lab paper goes to the NK Pathology lane (as today). Clinic and lab items mixed on one challan will
   stop; until then the paper is filed to the place whose bill it joins, and the sorter can tick it **"mixed: clinic + lab
   items"**.
2. **General stationery** (A4 packs, notebooks, registers, files; challans in the owner's name) is a **clinic expense**
   in Stationery & packaging. It is tracked **internally by quantity** against an **item list with rates**:
   - the list can grow at any time;
   - the owner keeps an **inventory**: received, issued and in stock.
3. **Carry bags (Elegans)** are a clinic expense in Stationery & packaging, paid on the estimate as today.
4. **Aumni Crafts medicine envelopes** are a **Sanjeevni pharmacy expense**. They are ordered online and paid by the
   owner's card. For now the invoice PDF is **added by hand**; an automatic email pickup comes later and is not in this kit.
5. **Only bills and invoices go to the accountants.** Estimates are for internal working only.

## 1 · Read first
- The S566 brief and its R1, `REPORT_S566.md`, the S563 and S560 briefs and reports, and `deploy_kits\KB_canon_all\BUILD_NORM_v1.md`.
  Every rule and NEVER in them still binds.
- **Copy `deploy_kits\S566_SCANAPP_LAST_FIXES\`'s kit shape exactly:**
  - installer `S568_*` variables, the build lock, pins before anything moves;
  - the rebuild on the box from the live bytes, compiled on both pythons;
  - the walks run on a database copy; backups; restart `assetapp` only (and `clinic-finance` for `packs.py`, as S560 did, with its health and packs-mounted check); healthz; the undo line;
  - the rehearsal on a made-up root;
  - walk and control in separate processes, made-up rows only, an injected `today`.
- Read **read-only**, to confirm the handover: Sanjeevni's `/root/finance/scan_register.py` (`904f07b1`) and
  `/root/finance/purchase_app.py` (`147201dd`). Both read pharmacy scans by `kind='Pharmacy'` only.

## 2 · Pins — FROM bytes, read on the box first; a different byte = STOP that file and report
- `/root/assetapp/sorting_desk.py` **`a053a222ee0fa8b0026aa4fc2511e8a9`** (S566)
- `/root/assetapp/clinic_papers.py` **`024464cc3d3ab5e1ead1526540904d61`** (S566)
- `/root/assetapp/asset_register.py` **`8b3c455128663db69c48232bf26c0083`** (S566)
- **THE PARENT'S** `/root/finance/packs.py` **`048d2ad81abb0271a1cddd31134544bb`** (S560): `build_bundle` only. If the live
  byte differs, STOP that file, build the rest and say so.
- NEW `/root/assetapp/stationery.py`
- Read only, **never edited:** `scanner_widget.js` `10a8bb29…`, `asset_machine.py` `7d4fdffc…`, `claude_reader.py`,
  `claude_reread.py`, every Sanjeevni file, `portal.py`, `tile_grants.json`.

## 3 · What to build

1. **The group "Stationery & packaging".** A clinic consumables group beside Procedure room, X-ray films and Others. It
   follows the same rules as those groups: the desk's destination list, The month's sections, sorted = accepted (D710),
   and the heal.
   - **No existing paper is moved** (D664). Papers already in *Others* stay there; a person can re-sort them on the desk.

2. **The item list** (new module `stationery.py`, owner-only page **"Stationery"** in the scan app's menu).
   - Each item has a name, a unit (pack / piece / ream …), an agreed rate, a low-stock level and an active/retired flag.
   - **"+ Add item"** on the page; items are edited in place. An item that has moves is retired, never deleted.

3. **Received — from the desk, never twice.**
   - On the desk, a paper in Stationery & packaging shows its item lines. Each line can be **matched** to a list item,
     **"Add to the list"** (one tap: a new item made from the line's name, unit and rate), or marked **"not a stock item"**
     (printed stationery, carry bags, envelopes).
   - A pre-match by name is offered and never saved without a person's Save (D664 spirit).
   - **Stock goes up once:**
     - from a **challan's** matched lines;
     - from a **bill's** matched lines only when the bill **joins no challan**;
     - a bill that joins challans adds nothing more;
     - an **estimate slip's** lines count like a challan's (estimates are internal).
   - Re-saving a paper replaces its own received moves; it never adds them again.
   - **A matched line whose rate differs from the item's agreed rate** is flagged on the desk: "rate ₹x — list ₹y".

4. **Issued — the staff screen, Roman Hinglish, switched OFF.**
   - One page **"Stationery diya"**:
     - item (a list of active items);
     - quantity;
     - to **Lab · Reception · Sanjeevni · Clinic**;
     - **Save**, with no confirmation tap (friction-free; the server checks behind it).
   - Stock goes **down**. A quantity above stock is still saved, and is flagged on the owner's page.
   - The owner sees and uses it at once. **Managers/staff only when the new switch `stationery.issue_on` is ON** (absent =
     OFF), a row on the scan app's **Switches** card on its home page, owner only.

5. **The inventory (the owner's "Stationery" page).** One row per item:
   - in stock · received this month · issued this month by place · last rate paid;
   - a **low-stock** mark at its level.
   - Below the rows: this month's issues, and the papers that fed the stock (links open them on the desk).
   - **"Count"** (owner or a manager with the switch ON): type what is on the shelf for any items.
     - The **first count of an item is its opening stock**.
     - A later count records any difference as **"not accounted for"** and sets the stock to the count.
   - All the owner's words are in English.

6. **The mixed-challan mark.** On the desk, a tick **"mixed: clinic + lab items"** for a challan or bill (stored on the
   paper). The owner's Stationery page and the supplier note show **"mixed challans this month: N"**, for him to raise
   with the supplier.

7. **"Add a paper from a file" on the desk** (owner and managers; managers only with the desk on as today).
   - Pick a PDF or image, a lane and a kind, then **Save**. It goes through the app's own intake code path (the same
     storage, duplicate checks and reading).
   - **One preset: "Sanjeevni pharmacy expense — paid by Dr MK's card".**
     - It files the paper on the **pharmacy** lane with **`kind='Pharmacy expense'`** (never `'Pharmacy'`, so
       Sanjeevni's registers never see it as a scan to pair with a Marg bill), status `captured`.
     - It is marked paid by card (S560's payment record, mode `Card`, note "Dr MK's card").
     - It shows on The month under a line **"Sanjeevni — pharmacy expenses"**, never in the clinic's totals.
   - The supplier is read as usual (Claude, Sarvam fallback).

8. **THE PACK FIX — the parent's `packs.py`, `build_bundle` only.** Every bundle (8.1, 8.2, 8.3, 8.4) takes **only bills
   and invoices**: a paper whose kind is an estimate slip, or a challan in any state (paid-on-challan *final* included),
   never goes to the accountants.
   - Receipts and statements stay out as now.
   - Everything else in `packs.py` stays byte-for-byte.
   - A `kind='Pharmacy expense'` paper is never in any accountants' bundle (it is not one of the four lanes' items).
   - Report which papers on a copy of the live data leave each bundle, as counts per bundle, never names.

## 4 · The walk, the controls, the rehearsal
- **`walk_s568.py`:** one named check per item 1–8. Each is **green on the TO files and red on the FROM files**
  (`--expect-red` with its MUST_RED list printed); counts are printed into the log. It must include:
  - a challan whose bill later joins it (stock rises once);
  - a re-saved paper (no double);
  - an issue above stock (saved and flagged);
  - a first count, then a second count (opening, then a difference);
  - a rate differing from the list;
  - a manager with `stationery.issue_on` absent (refused) and set (allowed);
  - an Aumni preset paper (absent from Sanjeevni's two queries, run read-only against the copy; absent from every bundle);
  - an estimate slip and a final challan (absent from every bundle after the fix, present before).
- **The earlier walks green on the new files:** S566 (12), S563 (17 + the tidy fetch), S560 (37 + pack 9), S548 (8),
  S559 (43), S557 (41), S555 (19), S551 (87 through `s551_lines_s559.py`). Any line a TO pin forces is adapted in a `/tmp`
  copy only, each change named with its reason (an intended behaviour change, such as the pack fix).
- **The S560 desk-layout browser walk** (7 checks, the PC's headless Chrome) stays green: every destination still fits
  on a 1366 × 768 screen with the new group.
- **The installer:**
  - **new tables** (the item list, the stock moves, the counts) and **one new column** on `bills` (the mixed mark);
  - additive only, idempotent, by the app's own `ensure` path;
  - **no existing row changed**;
  - `.bak_S568_<from8>` beside each replaced file, `assets.db.bak_S568_*`; `packs.py.bak_S568_048d2ad8`;
  - restart `assetapp`, then `clinic-finance` (S560's order and checks);
  - the undo line in the README.
- **The rehearsal** on a made-up root, its refusals and outcomes as S566's.
- `.gitignore` last-match-wins and the contact-number gate clean (`SANJ_CONFIG_STORE` as before); SUMS, KIT_ID, README,
  the PIN files.

## 5 · NEVER (in addition to every earlier brief's)
- change reception's intake, its lanes or words, or `scanner_widget.js`;
- move a paper a person placed, or guess a section or whose expense a paper is (D664);
- write `kind='Pharmacy'` on an Aumni paper, or touch a Sanjeevni file;
- change anything in `packs.py` outside `build_bundle`'s kind filter;
- copy a patient's file or a live database row into the kit, the report or the PC;
- install, restart or publish.

## 6 · The report
`REPORT_S568.md` contains:
- the FROM pins as read;
- every counted edit, each anchor matched exactly once on the live bytes;
- the TO pins;
- the walk and control counts, the earlier walks, and the browser walk;
- the pack fix's per-bundle counts on a copy;
- the rehearsal;
- calls you made where this brief left room, each with its reason;
- anything not done and why, and anything seen outside the brief (not touched);
- the cost, **as the runner's own log states it**.

Last line: **nothing installed, nothing published.**

**If anything cannot be done as written, stop, write what was done and why, and end.**
