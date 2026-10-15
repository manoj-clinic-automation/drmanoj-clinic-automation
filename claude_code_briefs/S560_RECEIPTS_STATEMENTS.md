# S560_RECEIPTS_STATEMENTS — brief for the build runner (Agent SDK, the API credits)

*Written 14-Oct-2026 by the Scan App project (session 315). Kit **S560** and **D728** claimed on the board `_numbers`
(v427 → v428) with the PLANNED line (D646). The owner's rulings 18:31–19:46 IST ("GO"). This file is the whole scope.
Run by `D:\Downloads\_kbtools\agent_build\run_build.py S560_RECEIPTS_STATEMENTS`.*

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** Kit in
`deploy_kits\S560_RECEIPTS_STATEMENTS\`, report `claude_code_briefs\REPORT_S560.md`, then stop. Nothing live placed or
restarted; no live row written.

## 0 · What was measured on the live desk (17:4x–18:4x IST, read only, as the owner)
- **At 1366 × 768 only 2 of the 16 destination buttons are visible**: the list area shows 498 px of 858 px, the rest sits
  under the fixed Save bar with no cue that it scrolls. So the owner "could not find" his Clinic or Personal expense
  buttons — they exist (*Clinic: Implant stock · Clinic equipment · Construction work*; *Personal: Personal expense
  (→ Dr MK / Dr Bhawna) · Personal (you only)*) but are hidden.
- **No paper kind for a receipt or a statement** (only Bill · Estimate slip · Challan).
  - Envirad: **B-0139** (receipt 13826, 08-10-2026, ₹850 cheque, "Sep 26", clinic) pays **B-0138** (invoice
    EN/26-27/3773, ₹850, clinic); **B-0140** (receipt 13825, ₹850 cheque, NK Pathology) pays **B-0137** (invoice
    EN/26-27/3717, ₹850, NK Pathology) — B-0137 was set aside today as "blank" by mistake; B-0140 sits on the lab lane as
    if it were a bill, so pack 8.1 counts a receipt instead of the bill.
  - **B-0104** (B.L. Computers) is a **ledger statement** (1-Jul → 22-Sep, 5 invoices, ₹32,900, paid by one cheque) stored as
    a single ₹800 bill. Jugnu Medicos is paid the same way.
  - Shivam Communication B-0020 / B-0021: invoices with a handwritten "paid by cheque" note.
- **Bills awaited prints `<built-in method items of dict object …>`** where B-0163's items should be.

## 1 · The owner's rulings (D728) — binding
1. **Every destination on one laptop screen**, grouped **Clinic expense** (Others under Clinic consumables stays where it
   is; *Implant stock · Clinic equipment · Construction work*) and **My expense — Dr MK / Dr Bhawna** (today's "Personal
   expense" with its two sub-choices; *Personal (you only)* stays beside it).
2. **Construction is a one-time project**, logged on its own with its **existing kinds** (bill / estimate slip / challan),
   out of the clinic totals as today. **Sending to the accountants is optional and only for construction BILLS**: a
   per-paper tick **"Send to accountant"**, shown only when the paper is in Construction work AND its kind is Bill; off by
   default; never on an estimate or a challan.
3. **Receipt** is a paper kind. It is linked to the bill it pays, or marked **"No bill — paid directly"**. It is **never
   counted as spend** (the bill is). The bill shows **"Paid dd-mm-yyyy · ₹amount · mode · cheque/ref no."** with the
   receipt's scan one tap away.
4. **Statement** is a paper kind **in addition to the supplier's individual invoices** — one consolidated cheque paying
   several invoices. It ticks the invoices it covers, marks each paid by that payment, shows any difference between the
   statement's total and the ticked invoices, and is **never counted as spend**. A receipt may link to a statement instead
   of to one bill.
5. **D664 still holds:** the system never guesses a section or whose expense a paper is; suggestions are pre-selected only
   as today's rules allow and are never saved without a person's Save.

## 2 · Read first
`claude_code_briefs\S551_SORTING_DESK.md` (v4), `S555_…`, `S557_…`, `S559_ONE_ROAD.md` + `S559_FIX1.md` and their reports
— every rule and NEVER still binds. **Copy `deploy_kits\S559_ONE_ROAD\`'s kit shape exactly** (installer `S560_*`
variables; rehearsal's refusals and five outcomes; walk isolated before import; walk and control in separate processes;
made-up rows; injected `today`; the browser walk on the PC's Chrome where layout must be measured). `BUILD_NORM_v1.md`.

## 3 · Pins — FROM bytes, read on the box first; a different byte = STOP that file and report
- `/root/assetapp/sorting_desk.py` **`a59fa38d7c7f145c8fefa52bad5676d1`** (S559)
- `/root/assetapp/asset_register.py` **`20ef7bc6b44079f3181d9c52519e8b94`** (S559)
- `/root/assetapp/clinic_papers.py` **`80e3cd8d2ef8e8953b2ae3fec3f85203`** (S559)
- `/root/assetapp/asset_machine.py` **`0caec41e655cfd51c2eaf9176ee33365`** (S559) — read; edit only if a paid bill on a
  machine's Spends needs its "Paid" line
- **THE PARENT'S** `/root/finance/packs.py` **`d86d351a46a1ba4da7d0e615da0deb1a`** (S548) — `build_bundle` and the item-8
  list only (§4.6). If the live byte differs, STOP that file, build the rest, and say so in the report.
- Read only: `scanner_widget.js` `1128ac975ba2543e1fe9edf7c721d4f8` (**not touched**), `claude_reader.py`,
  `claude_reread.py`.

## 4 · What to build
1. **The desk on one screen (laptop).** At 1366 × 768 **every** destination button, the kind buttons, Save and the
   join/blank row are visible **without scrolling anything**: *What was read* folds to one summary line (supplier · no. ·
   date · ₹amount · "edit ▾") that opens in place; destinations become a compact grid (two or three columns, buttons
   ≥ 36 px high); group titles **Clinic consumables · Clinic expense · My expense — Dr MK / Dr Bhawna · Handed over ·
   Documents · Not here**; at 1280 × 720 the same, or at worst the *Documents / Not here* row is the only thing below the
   fold **with a visible "more ▾" cue**. Prove it in the PC's headless Chrome (bounding rects at 1366 × 768, 1280 × 720,
   1920 × 1080), as S559's browser walk does.
2. **Paper kinds: Bill · Estimate slip · Challan · Receipt · Statement** (`bills.doc_kind` gains `receipt`, `statement`).
   Claude's reading maps to them only as a pre-choice (never saved alone): Claude's `doc_kind` values are read from
   `claude_reader.py`; a reading whose text says receipt/money-receipt pre-chooses Receipt only if the reader's own kind
   supports it — otherwise nothing is pre-chosen.
3. **Receipt on the desk.** Choosing Receipt shows **"Pays which bill?"**: the same supplier's (by `_supplier_key`) bills
   and challans-turned-final of the last 180 days that are **not yet fully paid**, newest first, with no. · date · ₹amount ·
   lane; the likely one **pre-ticked** when exactly one bill has the same amount within 60 days (else none); **"No bill —
   paid directly"**; **"A statement"** (lists the supplier's statements). Payment fields from the receipt: date, amount,
   mode (Cash · Cheque · Bank / UPI), cheque or reference no. — pre-filled from what was read (Claude's reading first),
   editable. Save records the payment (§4.5) and files the receipt **on the lane of the bill it pays** (a lab bill's
   receipt goes to the NK Pathology lane, a clinic bill's to the clinic lane) with `doc_kind='receipt'`; it is never
   accepted as a bill and never counted in any total or pack.
4. **Statement on the desk.** Choosing Statement shows: period from–to (pre-filled from what was read), total, payment
   (date, amount, mode, cheque/ref no.), and **"Which invoices does it cover?"** — the supplier's invoices in that period
   (± 7 days) that are not fully paid, pre-ticked when inside the period; a line **"Ticked ₹X of statement ₹Y — difference
   ₹Z"**; and when the difference is not zero, one grey line *"An invoice may not be scanned yet."* Save records one
   payment covering the ticked invoices (§4.5); the statement is filed with `doc_kind='statement'`, never counted.
   A bill can also be marked paid directly (no receipt): on the desk's Bill view, a small fold **"Paid?"** with the same
   payment fields (for invoices with a handwritten "paid by cheque" note).
5. **Payments — one record.** NEW `paper_payment(id INTEGER PRIMARY KEY, paid_on TEXT NOT NULL, amount REAL NOT NULL, mode
   TEXT NOT NULL CHECK(mode IN ('cash','cheque','bank')), ref TEXT NOT NULL DEFAULT '', proof_bill_id INTEGER (the receipt
   or statement paper, NULL when marked directly), by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by
   TEXT NOT NULL DEFAULT '')` and `paper_payment_bill(payment_id INTEGER NOT NULL, bill_id INTEGER NOT NULL, amount REAL
   NOT NULL, PRIMARY KEY(payment_id, bill_id))` — append-only (a mistake is voided). **Use S557's fingerprint rule** for
   every bill reference (`bill_created_at` beside `bill_id`) so a re-issued id never inherits a payment. A bill's paid
   state = sum of live allocations vs `total_amount`: **Paid** / **Part-paid ₹x of ₹y** / unpaid. Shown on the desk,
   the old bill page, All papers (a small "Paid" mark), the month page (a "paid / unpaid" count per section) and the
   implant ledger (its Paid tile adds these payments for implant-stock bills — never twice with its own *Note payment*:
   the ledger shows both kinds of record, each once). The existing `bills.paid_on/paid_amount` of a paid-on-challan paper
   stays as it is and is read alongside.
6. **Construction's "Send to accountant".** On a Construction-work paper whose kind is Bill: a tick **"Send to
   accountant"** (off by default), saved in a NEW column `bills.to_accountant INTEGER NOT NULL DEFAULT 0`, audited; hidden
   and forced off for estimates and challans. The month page's Construction card shows "N bills · M marked for the
   accountant". **In the parent's `packs.py`** (pinned above; counted, anchored edits in `build_bundle` and the item-8 list
   only): (a) **every bundle excludes** `doc_kind IN ('receipt','statement')` and an awaiting challan
   (`doc_kind='challan' AND COALESCE(challan_state,'awaiting') <> 'final'`) — so B-0140's receipt leaves 8.1; (b) a NEW
   item **"Construction bills marked for the accountant"** — `subgroup='construction' AND COALESCE(doc_kind,'bill')='bill'
   AND to_accountant=1 AND status<>'rejected'`, whatever its lane, the month by the pack's own month rule. Read how
   `packs.py` numbers its items and add this one after the last (say the number in the report). Walk the pack: the
   September and October bundles before/after on made-up rows — only the intended rows change.
7. **Fixes on existing papers — never by a data step.** The desk lists them at the top of *Waiting* for one person's tap
   each, with the reason (no paper is special-cased by stamp in code — they qualify by rules): a paper set aside as
   *blank* whose reading has an amount and a supplier (B-0137) shows **"Set aside as blank, but it reads as a bill — restore?"**
   (*Restore* puts it back on its lane as it was, audited); a filed paper whose Claude kind or read text says receipt
   (B-0139, B-0140) shows **"This looks like a receipt"**; a single bill whose reading shows several invoice lines and a
   period (B-0104) shows **"This looks like a statement"**; a paper in *Resumes*-like text filed as a consumable (B-0103) —
   only if `suggest()` already says resume — shows the existing grey hint. **Bills awaited's items line** prints the items
   (fix the `dict.items` call).
8. **Leave as they are:** reception's intake and slip; the widget; the switches; everything S559 made.

## 5 · Never
Everything in the earlier briefs' NEVER lists, and: count a receipt or a statement as spend anywhere; move, accept or
change an existing paper by a data step; edit `packs.py` outside `build_bundle` / the item-8 list; touch any other finance or
Sanjeevni file, the widget or the DUTY_MAP; write a real row; place; restart; publish; push; print a person's name, a phone
number, a key or a token.

## 6 · Walk, control, installer, rehearsal, kit, report — S559's shape
- **Walk** (isolated; made-up suppliers differing in their first two words; made-up today): the one-screen layout (browser
  walk, the three sizes); the five kinds saved; a receipt linked to a bill → the bill Paid, the receipt in no total; a
  receipt "no bill"; a receipt to a statement; a statement covering three made-up invoices with a difference line; part-paid;
  a voided payment ignored; a re-issued bill id inherits nothing (fingerprint); a lab bill's receipt filed on the lab lane;
  "Paid?" on a bill; the construction tick only on a construction Bill, off by default, forced off for estimate/challan;
  the pack: receipts / statements / awaiting challans out of 8.1/8.2/8.3, the new construction item carries exactly the
  ticked bills; the five fix hints appear for their made-up look-alikes and *Restore* works; Bills awaited's items line; the
  implant ledger counts each payment once; **the S559 (43), S557 (41), S555 (19), S551 (87) walks still green**; the old
  `packs.py` walk (read `deploy_kits\S548_*`) still green apart from the intended rows.
- **Control** red on the live (S559) files with named checks.
- **Installer** `install_s560.sh`: S559's order and safety; the database backed up by the backup API **before**
  `ensure()` adds `paper_payment`, `paper_payment_bill`, `bills.to_accountant` (guarded for two workers); restart
  **assetapp** and — because `packs.py` changes — **clinic-finance** (the finance service; read its unit name from the box);
  health of both (`/scanapp/healthz` 200, `/desk` 302, the finance health endpoint used by earlier finance kits);
  ALREADY INSTALLED; restore on any failure (both services restarted); undo with `\cp -p`. Take the server-wide build lock
  CLAUDE.md describes **only inside the installer** (this run never installs).
- **Rehearsal** `rehearse_s560.sh` — the five outcomes on a made-up root, both services faked.
- **Kit** `deploy_kits\S560_RECEIPTS_STATEMENTS\` with SUMS, `.gitignore` last-match-wins, the contact-number gate.
- **Server line** (README): `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S560_RECEIPTS_STATEMENTS/install_s560.sh`
- **Report** `claude_code_briefs\REPORT_S560.md`: 3–5 plain lines on top (what the desk now shows on one screen; how a
  receipt and a statement are filed; the construction tick; the five papers to tap); then pins, counted edits, walk /
  control counts printed into the log, the earlier walks, the browser measurements, the pack before/after, the rehearsal,
  gates, one line FOR THE PARENT (packs.py's new pin and item number), the cost. Last line: **nothing installed, nothing
  published.**

**If anything cannot be done as written, stop at that point, write what was done and why, and end.**
