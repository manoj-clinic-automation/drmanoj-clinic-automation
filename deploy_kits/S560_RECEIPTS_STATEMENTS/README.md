# S560_RECEIPTS_STATEMENTS — receipts and statements, one payment record, the desk on one screen (D728, S315)

**Fix round 2 (15-Oct-2026, brief `S560_FIX2.md`, after review round 2's C4): `sorting_desk.py` only.**
- **C4 ? a receipt or statement saved as any other kind** (Bill, Estimate slip, Challan): in the same Save its own live payment is
  voided, and that payment's live allocation rows too (kept, with `voided_at` / `voided_by`; audited `payment_voided` on the paper
  and the bill it paid). On the clinic lane a Filed (captured) paper goes back to draft first (audited `desk_not_spend_undone`), so
  the Save's normal accept, with its duplicate check, runs. The bill the receipt had paid reads unpaid again; the new Bill counts
  once. A Save that sends no kind changes nothing here. Walk check **R6**.
- `sorting_desk.py` TO is now **`a4623438f068d8e691b797482bd942ab`** (fix round 1's `b5993236?` is superseded). The other three TO
  pins are unchanged.

**Fix round 1 (15-Oct-2026, brief `S560_FIX1.md`, after the independent review): the same kit, revised in place.**
- **B1 — a payment is recorded once.** Re-saving a receipt or a statement that already has a live payment **changes that payment**.
  Its date, amount, mode and ref are updated in place, with the old values in the audit (`payment_changed`). Its old allocation rows
  are voided (kept, with `voided_at` / `voided_by`) and new ones written. A second payment is never added. A receipt re-saved as the
  receipt of a statement voids its own payment, so the money is counted once, as the statement's.
  - On a fully paid bill, *Paid?* reads **"Paid on dd-mm-yyyy — change?"** and edits that payment, when it is one direct payment. A bill
    paid by a receipt or statement is refused with one plain line that names the paper.
  - **An allocation is capped at what the bill still owes:** a receipt, *Paid?*, and each invoice of a statement. The rest is named in
    the message, or shown as the difference.
  - `paper_payment_bill` gains `voided_at`, `voided_by`, and its key becomes `PRIMARY KEY(payment_id, bill_id, voided_at)`: one live row
    per bill per payment.
- **C1 — a construction bill goes into the pack once.** In `build_bundle`, a construction bill ticked *Send to accountant* goes only
  into 8.4. It never also goes into 8.1 / 8.2 / 8.3 by its lane.
- **C2 — a real check that the pack loaded.** After the clinic-finance restart, the installer reads that service's journal since the
  restart. It uses `grep -q`, so no line is printed. It looks for finance_app.py's own words, `packs NOT mounted`, and treats them as a
  failed health check (both services restored). The rehearsal has a sixth outcome for this.
- **C3 — never approved as spend.** The old bill page's Approve refuses `doc_kind IN ('receipt','statement')`, with one plain line
  (AR4).
- **N1 — a real laptop.** Measured in headless Chrome at a viewport of exactly **1366 × 620**: every destination, the five kinds and
  Save are on screen, with 0 px of scrolling. No spacing change was needed.

**Why.** The owner's rulings, 14-Oct-2026 18:31–19:46 IST ("GO"). On the live desk at 1366 × 768 only 2 of the destination
buttons showed (the rest sat under the Save bar with no cue); there was no paper kind for a receipt or a statement (Envirad's
receipts B-0139 / B-0140 were filed as bills — B-0140 on the lab lane, so pack 8.1 counted a receipt; B.L. Computers' ledger
statement B-0104 was stored as one ₹800 bill); Bills awaited printed `<built-in method items of dict object …>`.

**What it does.**
1. **The desk on one laptop screen.** *What was read* folds to one line (supplier · no. · date · ₹amount · *edit ▾*) that opens
   in place; the destinations are a compact grid (buttons ≥ 36 px) under the titles *Clinic consumables · Clinic expense · My
   expense — Dr MK / Dr Bhawna · Handed over · Documents · Not here* (Personal expense is shown as its two choices *Dr MK* /
   *Dr Bhawna*, beside *Personal (you only)*); the kind row sits beside its title; a *more ▾* cue appears whenever the panel
   would scroll. Measured in headless Chrome (browser walk L): all visible, nothing scrolling, at 1366 × 768, at a 1366 × 620 viewport (FIX1 N1) and at 1920 × 1080;
   at 1280 × 720 only *Not here* is below the fold, with the cue.
2. **Paper kinds: Bill · Estimate slip · Challan · Receipt · Statement** (`bills.doc_kind` takes `receipt`, `statement`). Claude's
   reading pre-chooses Receipt / Statement only when its text says so AND the reader's own kind is `other` (the reader has no
   receipt kind); else nothing is pre-chosen. Never saved without a person's Save (D664).
3. **Receipt.** *Pays which bill?* — the supplier's (`_supplier_key`) bills and challans-turned-final of the last 180 days not yet
   fully paid, newest first (no. · date · ₹ · lane), the likely one pre-ticked when exactly one has the same amount within 60
   days; *No bill — paid directly*; *A statement*. Payment boxes (date, amount, Cash · Cheque · Bank / UPI, cheque / ref no.)
   pre-filled from what was read. Save records the payment and FILES the receipt in the place of the bill it pays (a lab bill's
   receipt on the NK Pathology lane), status *Filed* (captured) — never accepted, never in any total or pack. A receipt that pays
   a statement is linked as its proof — no second payment.
4. **Statement.** Period, total, payment, *Which invoices does it cover?* (pre-ticked inside the period, ± 7 days offered),
   *Ticked ₹X of statement ₹Y — difference ₹Z*, and the grey *An invoice may not be scanned yet.* when Z ≠ 0. Save records one
   payment covering the ticked invoices (each up to what it still owes, oldest first). *Paid?* on a Bill marks it paid directly.
5. **One payment record.** `paper_payment` + `paper_payment_bill` (a mistake is voided — *void* on the desk's paid line; a re-save
   changes the payment already recorded, its old allocation rows voided and kept — FIX1 B1); every bill reference carries the bill's fingerprint (`bill_created_at`; the proof paper's `proof_created_at`), so a
   re-issued id inherits nothing. Paid / Part-paid ₹x of ₹y / unpaid on the desk, the old bill page (*Paid dd-mm-yyyy · ₹ · mode ·
   no.* with the receipt's scan), All papers (a small *Paid* / *Part-paid*), the month page (*paid N / unpaid M* per section) and
   the implant ledger (its Paid adds these payments; its own *Note payment* rows stay — each record once). `bills.paid_on /
   paid_amount` of a paid-on-challan paper is read alongside.
6. **Construction's "Send to accountant"** — `bills.to_accountant` (0 by default), a tick only on a Construction-work paper whose
   kind is Bill, audited, forced off for an estimate or a challan. The month's Construction card: *N bills · M marked for the
   accountant*. **The parent's `packs.py`** (build_bundle and the item-8 list only): every bundle leaves out receipts, statements
   and challans still awaiting their bill; NEW item **8.4 · Scanned bills: Construction bills marked for the accountant**
   (`subgroup='construction'`, kind Bill, ticked, not rejected, any lane, the pack's own month rule).
7. **The papers to put right — by rule, one tap each, never a data step:** at the top of *Waiting*, with the reason: *Set aside
   as blank, but it reads as a bill — restore?* (Restore puts it back on its lane as it was, audited); *This looks like a
   receipt* (Claude's `other` paper, an amount, no goods line, and the supplier has a bill of that amount within 60 days — or its
   text says receipt); *This looks like a statement* (Claude's `other` paper, three or more priced lines, no single number or
   date — or its text says statement / ledger); a Resumes-like paper filed as a consumable when `suggest()` says resume (its
   grey hint). A person's Save or *No — leave it* takes a paper off the list. On today's copy the rules list **B-0140, B-0139
   (receipt), B-0137 (blank), B-0104 (statement)**; B-0103 is not listed (suggest() does not say resume for it).
8. **Bills awaited** prints each challan's items (`{{r['items']}}`).

**Files (FROM → TO).**
| file | FROM | TO |
|---|---|---|
| `/root/assetapp/sorting_desk.py` | `a59fa38d7c7f145c8fefa52bad5676d1` | `a4623438f068d8e691b797482bd942ab` (52 counted edits + `s560_sd_block.txt`, `s560_js.txt`) |
| `/root/assetapp/clinic_papers.py` | `80e3cd8d2ef8e8953b2ae3fec3f85203` | `88963eacee217e051ae07091648a46d7` (6) |
| `/root/assetapp/asset_register.py` | `20ef7bc6b44079f3181d9c52519e8b94` | `9daed9ea4f2a87e40b43711e472e701f` (4 + `s560_ar_block.txt`) |
| `/root/finance/packs.py` (THE PARENT'S) | `d86d351a46a1ba4da7d0e615da0deb1a` | `048d2ad81abb0271a1cddd31134544bb` (5: build_bundle and the item-8 list) |

(Before fix round 1 the TO pins were `5017fe92` / `88963eac` / `5c8b3097` / `f8d9a8f4`; after fix round 1 `sorting_desk.py` was
`b5993236`. They are superseded and were never installed.)

Read only, pinned: `asset_machine.py 0caec41e` (not edited), `scanner_widget.js 1128ac97` (not touched), `claude_reader.py 3894dc23`,
`claude_reread.py d9b75e78`, and the pre-S559 widget backup `scanner_widget.js.bak_S559_1143c77b` (S559's walk compares against it).

**Database.** Additive only, by sorting_desk's own `ensure()` (idempotent, guarded for two workers): `paper_payment`,
`paper_payment_bill`, `bills.to_accountant INTEGER NOT NULL DEFAULT 0`. The installer backs the database up with the backup
API (`assets.db.bak_S560_<stamp>`) BEFORE it runs that data step. No row is written; no existing paper is changed.

**Installer** `install_s560.sh` (S559's order): gates → the server-wide build lock → FROM pins (+ read-only pins) → rebuild from
the live bytes → TO pins → compile on both pythons → on a scratch copy: S560 walk (37) + control (34 must-be-red), the pack walk
(9) + control (7 must-be-red), S548's pack walk, S559 (43), S557 (41), S555 (19), S551 (87, through S559's three agreed lines)
— `DRY=1` stops here → backups (`.bak_S560_<from8>` ×4, the database) → the data step → place (the scan app's modules, its own
file last, then packs.py) → md5 read-back → restart **assetapp** → `/healthz` 200, `/desk` **302 only** → restart
**clinic-finance** → `/finance/healthz` 200 **and no `packs NOT mounted` in its journal since the restart** → the plain lines →
the undo line. Any red after placing restores all four files and restarts both services. **Rehearsal** `rehearse_s560.sh`: the
six outcomes on a made-up root, both services faked — GREEN.

**Server line:**
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S560_RECEIPTS_STATEMENTS/install_s560.sh`

**Undo** (printed by the installer, in this form):
`\cp -p /root/assetapp/sorting_desk.py.bak_S560_a59fa38d /root/assetapp/sorting_desk.py && \cp -p /root/assetapp/clinic_papers.py.bak_S560_80e3cd8d /root/assetapp/clinic_papers.py && \cp -p /root/assetapp/asset_register.py.bak_S560_20ef7bc6 /root/assetapp/asset_register.py && \cp -p /root/finance/packs.py.bak_S560_d86d351a /root/finance/packs.py && systemctl restart assetapp && systemctl restart clinic-finance`
(The two new tables and the column stay; nothing else reads them. The database backup is used only if a payment recorded after
install must be taken back — say so before using it.)

**Kit files.** `KIT_ID.txt`, `README.md`, `make_s560.py`, `s560_sd_block.txt`, `s560_js.txt`, `s560_ar_block.txt`, `walk_s560.py`,
`walk_s560_pack.py`, `install_s560.sh`, `rehearse_s560.sh`, 4 `PIN_FROM_*`, 4 `PIN_TO_*`, 5 `PIN_READ_*`, `walk/`
(`run_browser_walk_s560.py`, `layout.js`, `walk_results_s560.txt`), `SUMS.md5`.
