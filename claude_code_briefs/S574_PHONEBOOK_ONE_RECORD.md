# S574_PHONEBOOK_ONE_RECORD — brief for Claude Code (v1)

*v2 — after an independent read against the live bytes (R1, 06:3x IST 18-Oct: 3 blockers, 14 corrections, all folded in below and governing).* *Written 18-Oct-2026 by the Sanjeevni chat (session 322) at the owner's "Proceed with the build" (06:19 IST), after mock-up v2 (artifact `7WHB53yc3gedxfyqTouCAL`; copy `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S322\S322_PHONEBOOK_MOCKUP_v2.html`) and the plan `S322_PHONEBOOK_PLAN.md` beside it. Read `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` (v1.1), `CLAUDE.md` and `deploy_kits/KB_canon_all/BUILD_NORM_v1.md` first. Kit shape: S570's. Line numbers are the 18-Oct bundle's; find everything by name.*

## 0 · For the owner
1. **One dealer, one record.** 13 dealers are in the phone book twice: once under Marg's name (no bank details) and once under the bank sheet's name (bank account checked). You linked all 13 pairs on 14-Sep, but the book still shows two entries for each. After this kit, one tap of yours joins each pair into one record. The bank account is not touched, and the tap can be undone.
2. **Up to 4 mobile numbers and 2 emails per dealer.** There are three optional picks: **Calls**, **Order WhatsApp** and **Payment message**. Any pick left blank uses number 1. The emails are kept for reference; nothing sends email.
3. **The whole book on one page, as now.** The picks are drop-downs on each dealer's line and save at once. *Edit* opens the numbers in place. Every change is listed at the foot. Bank details, *Add a supplier* and *Verify* stay on the page as they are (adding a supplier becomes yours only, point 4).
4. **Only you change numbers and add a supplier** (his word 05:57 IST: staff hand you the number). Darpan and Shavez still read the book; Shavez still does the bank details as now.
7. **One small gain:** RAVI MEDICAL AGENCY (Marg's name) has no row of its own today, so ordering finds no number for it. After the switch is on, it finds the bank sheet's Ravi record and its number.
5. **What staff see:** the call number and the WhatsApp number, to read only. A dealer with no number says *"Number nahi hai — Dr sahab ko dijiye"*.
6. **It installs switched OFF.** Until you turn it on, everything works exactly as today. Then you tap *Merge all 13*.

## 1 · Numbers and pins
- Kit **S574_PHONEBOOK_ONE_RECORD** (board `_numbers` v461 → v462, PLANNED line). Project: Sanjeevni. No D or F number of its own (rides the close).
- **FROM pins** (read the full md5 at the open; different = STOP, report):
  - `/root/finance/purchase_app.py` **147201dd288d291323023a764df3411e**
  - `/root/finance/order_sheet.py` **247eeb48db8cc007faedfe14f3676893**
  - `/root/finance/order_sheet_pdf.py` **b0cc86945d560e8cce842b799913e021**
  - `/root/finance/porders_s454.py` **1c3d3927163e08114e3e26c5f06052a4**
  - `/root/finance/supplier_msg.py` **2f43af754a160376cec955f92f3aa43a**
- **Read only, must not change:** `amir_day.py`, the bank readers `_vendor_bank`, `_advice_accounts_s265`, `_acct_name_s265`, `amir_day._s494_bank`, the NEFT advice and payment sheet. Service: `clinic-finance`, restarted once. The build lock.

## 2 · What is there now (the chat's grep of the 18-Oct bundle — re-grep at the open; a reader not listed here is a STOP-and-report)
- **The table:** `purchase_vendor_contact` (vendor_norm PK, vendor, phone, phone2, the bank fields, source, added_by, updated_at). 39 rows: 13 pairs + 13 singles. The pairs are exactly the rows of `purchase_vendor_alias` (bill_norm = Marg's name → register_norm = bank sheet's name; 14 rows; RAVI MEDICAL AGENCY has no second row).
- **Readers of a number (rule 2: there are four ways to read one; this kit leaves one):**
  - `purchase_app._phone_for` (≈1578): callers ≈3309, ≈3339, ≈3497, ≈3528; `supplier_msg._digits` (≈251), which serves the NEFT and cheque notices **by the name on Marg's bill** (`g["name"]` from `b["supplier"]`, purchase_app ≈2041 — e.g. KEDAR PHARMACEUTICAL, not KEDAR PHARMA); `porders.py` ≈832 (the WhatsApp order link); `order_sheet.py` ≈447 and ≈1726 (has-a-number checks); `order_rules.py` ≈873 and ≈941 (`has_phone`). **`_phone_for` STAYS, as the one-line `order` wrapper of `book_number`, so `porders.py` and `order_rules.py` need no edit and are not in the pins.**
  - **Not a phone-book reader, not touched, named in the README:** `order_sheet.phones_new` (≈451; the numbers printed on Marg's own order sheet, shown at porders_s454 ≈1508).
  - `purchase_app._phones_for` (≈3746): the old `/page/staff` call buttons (≈3645).
  - `order_sheet._phones` (598): `order_sheet` ≈1134 (the cards: `phone`, `phone2`, `has_phone`), ≈1263 (`_queue_message`, the order WhatsApp `to`); `order_sheet_pdf` ≈208 and ≈212; `porders_s454` ≈674, plus `e["phone"]` / `e["phone2"]` at ≈636 and ≈708–710 (the *Call karo* tel: and the numbers under it).
- **Writers:**
  - `purchase_app` push (≈590–612) — manojz posts Marg's supplier name → number pairs. It upserts by `supplier_key(name)` and keeps a `source='server'` number. This is what re-made the Marg-name rows.
  - `_book_save` (≈3776; actions add / phones / bank / verify).
- **Doors today:** reading the page and the actions `add` and `phones` — `_book_allowed` (doctor + setting `purchase.phonebook_users`, live `manoj,darpan,shavez`; purchase_app ≈3788–3817); `bank` — `_s452_may_advice`, the setting `supplier_msg.senders` (live `manoj,shavez`; ≈6849); `verify` — the doctor only (≈3838).

## 3 · The edits
### 3.1 Schema (idempotent, in `_ensure_book`)
- **New columns on `purchase_vendor_contact`:** `phone3`, `phone4`, `email1`, `email2` (TEXT); `call_pick`, `order_pick`, `pay_pick` (INTEGER 1–4 or NULL); `display_name` (TEXT); `merged_into` (TEXT, the vendor_norm of the one record).
- **New table `purchase_vendor_premerge`** (id, merged_at, merged_by, bill_norm, register_norm, bill_row_json, register_row_json, undone_at, undone_by): the two rows as they stood, kept for undo. Never deleted.
- **New table `purchase_book_change`** (id, at, who, vendor_norm, what, old4, new4): **last-4 only, never a full number** (the existing audit's rule).
- **Setting `purchase.book_one_record.on`**, default `'0'`.

### 3.2 One reader (charter rule 2)
Add to `purchase_app.py`, beside `_phone_for`:
- `book_record(con, vendor)` → the one record (dict) for a Marg name, a bill name, a bank-sheet name or a norm:
  - `k = supplier_key(vendor)`; take the row with `vendor_norm = k`;
  - if that row has `merged_into` → take that row instead (one hop);
  - if there is no row → `purchase_vendor_alias` bill_norm `k` → register_norm row (then the same hop);
  - otherwise None.
  - **Switch OFF: the row with `vendor_norm = k` and nothing else — exactly today's lookup.**
- `book_numbers(rec)` → `[(slot, number)]` for slots 1–4 that hold a number, in slot order. **Switch OFF: slots 1–2 only (`phone`, `phone2`), so numbers 3–4 saved while ON never leak in after OFF.**
- `book_number(con, vendor, use)` with use ∈ `call` · `order` · `pay` → the picked slot's number when that pick is set and its slot holds a number, else the first slot that holds one, else `""`. **Switch OFF: returns `phone` exactly as `_phone_for` does today.**
- **Intended change, switch ON:** a bill name with no row of its own but an alias row (live: RAVI MEDICAL AGENCY) now resolves to its bank record's number, where today it gives `""`.
- **Every reader in §2 calls `book_number`** (or `book_record`/`book_numbers` for a list):
  - a number under a Call button or in a `tel:` link → `call`;
  - the number a WhatsApp order goes to → `order`;
  - a NEFT or cheque notice (`supplier_msg._digits`) → `pay`;
  - the order sheet PDF prints the call number, and the WhatsApp number beside it when different.
- **Retire** `order_sheet._phones` and `purchase_app._phones_for` once nothing calls them. `_phone_for` stays as the one-line wrapper `book_number(con, vendor, 'order')`. Name what was retired in the README.

### 3.3 The merge (owner door, on his tap only; charter rule 10)
- **The pending pairs:** alias rows where both rows exist and neither has `merged_into`.
- **For each pair** (keyed, idempotent; a merged pair is skipped):
  1. Write `purchase_vendor_premerge` first.
  2. The register row's slots become its own phone, phone2, then the Marg row's phone, phone2 that are not already there (compare the digits), up to 4. More than 4 → keep the first 4 and list the pair in the owner's changes and the report (none expected).
  3. `display_name` = the name he chose: default `_acct_name_s265('', <Marg row's vendor>, <Marg row's vendor_norm>)` (≈4883 — the existing city-tail cutter; no new one, rules 2 and 8): *JUBILEE AGENCIES*, *GUNINA PHARMACEUTICALS PVT LTD* (his word 06:11 IST), *SAISUN PHARMA PVT. LTD.*
  4. **When the two rows' first numbers differ** (live: KEDAR only — bank row has two, Marg row only the second), **all three picks** (`call_pick`, `order_pick`, `pay_pick`) are set to the slot holding the Marg row's phone. Today every reader — orders, calls AND the NEFT notice, which reads by the bill name KEDAR PHARMACEUTICAL (supplier_msg ≈286; the August row went to that number) — uses the Marg row's number.
  5. The Marg row gets `merged_into = register_norm`. **Its own fields are not changed. Nothing is DELETEd. The register row's `vendor`, `acct_name` and bank fields are not touched.**
  6. One `purchase_book_change` line per pair: "merged".
- **Undo** (owner only): restores the register row's slots, picks and display_name from the premerge copy, clears the Marg row's `merged_into`, and sets `undone_at`. **Undo is refused once any `purchase_book_change` line (other than "merged") exists for a merged record after its merge** — the page then says *"Undo is closed: numbers were changed after the merge."* (rule 5: his later edits are never wiped).
- **After the merge, with the switch ON,** every number a reader returns for each of the 26 dealers equals what it returned before the merge (Kedar included, by step 4). The walk proves it.

### 3.4 Marg's push (≈590–612)
- **Switch ON and a record found by `book_record`:**
  - the pushed number (digits) is already one of its slots → only `updated_at` changes;
  - else it goes into the first empty slot, with a `purchase_book_change` line "from Marg";
  - all four slots full → nothing is written to the record; one `purchase_book_change` line `what='marg_extra'`, new4 = last-4 (once per dealer and number). The owner's book page shows *"Marg has another number for <name> (…1234)"* for each `marg_extra` line with no later `phones` line for that dealer.
  - **The push never replaces a number, never touches `vendor` (today's upsert sets `vendor=excluded.vendor` at ≈606; on a register row that would change the name the NEFT advice prints), never sets a pick, never creates a row for a merged name.**
  - **Named behaviour change, switch ON, for every dealer (singles too):** today Marg's number *replaces* a non-`server` row's number; with the switch ON it is *added* into a free slot and listed "from Marg". Only the owner replaces a number.
- **No record** → insert as today.
- **Switch OFF → today's statement, byte for byte.**

### 3.5 The book page (`/page/book`, `/api/book`) — owner's page, English
- **Doors (rule 13):**
  - New actions `picks`, `merge`, `unmerge`, `switch`, plus `add` and `phones`: **the doctor only, switch ON or OFF** (the switch itself is the doctor's). Anyone else gets *"Numbers are changed only by Dr Manoj."*
  - `bank` and `verify` stay exactly as today (`bank`: `supplier_msg.senders`; `verify`: the doctor).
  - Reading the page stays as today (`_book_allowed`).
  - **What each login sees (the screen follows the door):** the doctor — everything; Shavez — the book to read plus the bank *Add/Edit* as today, no number, pick, add, merge or switch control; Darpan — the book to read only.
  - **Every write posts the record's `vendor_norm` (the register row's key), never `display_name`** — `supplier_key("JUBILEE AGENCIES")` is the merged Marg row's key, so a save by display name would land on the hidden row. `_book_save` finds the row by that key.
- **Switch OFF:** today's page, plus one line at the top for the doctor only: *"One record per dealer: OFF — Turn on"*.
- **Switch ON — one page** (mock-up v2 screen 2; keep the live page's look):
  - A search box at the top.
  - One line per dealer not merged away: `display_name` (else `vendor`); *also:* the names merged into it; numbers 1–4; the emails.
  - **The bank block exactly as today**, with its *Add/Edit* and *Verify*.
  - The three drop-downs *Calls* · *Order WhatsApp* · *Payment msg*, only when the dealer has 2 or more numbers (else "Number 1"); each change POSTs `picks` and shows "✓ Saved".
  - *Edit* opens numbers 1–4 and emails 1–2 in place. The same checks as today: 10 digits starting 6–9; an email has one @ and a dot.
  - *Add a supplier* as today.
  - **Merge panel** at the top while pairs are pending: Marg's name | bank sheet's name, numbers, a *Name to keep* select (default as §3.3 step 3), the "numbers differ" note for Kedar, and one button **Merge all N**. After the merge, a small *Undo the merge* link.
  - **Changes** at the foot: the last 100 lines (when, who, dealer, what, …old4 → …new4).
- The staff never see this page's write controls.

### 3.6 The staff card (porders_s454 `/order`, `/order/<supplier>`; order_sheet cards) — Roman Hindi
- Switch ON: `Call: <call number>` and `WhatsApp: <order number>` under the dealer's name. *Call karo* dials the call number. *Sab ko WhatsApp bhejo* and the queue use the order number.
- No number: *"Number nahi hai — Dr sahab ko dijiye"* (owner's English: *"No number — give it to Dr Manoj"*), in place of both word keys `nophone` (≈86) and `nophone_l` (≈98) — **switch ON only**.
- No new button, no field. **Switch OFF: as today, words included.**
- The page stays under 100 KB (rule 14).

## 4 · The walk (`walk_s574.py`; scratch copy of finance.db; its own rows by key)
1. **The live state first:** the 13 pending pairs by alias key (names, slot counts, last-4 only); the 13 singles; the setting absent or `'0'`.
2. **OFF = today:** for all 39 rows and all 14 alias names, every reader's number (`order`, `call`, `pay`) equals the old file's `_phone_for` / `_phones` / `_phones_for` / `supplier_msg._digits` result. The staff order page and `/page/book` GET 200. Then save a made-up number 3 while ON, switch OFF, and assert it appears nowhere. Print the count compared.
3. **ON, before the merge:** the same equality, **except RAVI MEDICAL AGENCY**, which now gives its bank record's number (old: `""`) — assert exactly that one difference.
4. **Merge all 13:**
   - the book page lists 26 dealers;
   - Gunina's `display_name` is *GUNINA PHARMACEUTICALS PVT LTD*;
   - Kedar's order, call and pay numbers all equal the Marg row's phone, by `KEDAR PHARMACEUTICAL` and by `KEDAR PHARMA`;
   - **every reader's number for every name equals step 3's**;
   - `_vendor_bank`, `_advice_accounts_s265` and `_s494_bank` give identical results for every norm before and after;
   - no row is deleted (count 39); `purchase_vendor_premerge` has 13 rows.
   - Control: the old file has no merge (red).
5. **Picks:** set Kedar `pay_pick` to the other slot → `supplier_msg._digits('KEDAR PHARMACEUTICAL')` returns it (non-empty — `_digits` swallows errors into `""`, so assert non-empty for every dealer that has a number), and the order number is unchanged. Control red on the old file.
6. **Push:**
   - an existing number → no change;
   - a made-up new number for a merged dealer → lands in a free slot, row count still 39;
   - a made-up number for a full dealer → nothing written + the owner line;
   - a made-up new dealer → a new row.
   - Controls: the old file makes or changes rows (red).
7. **Doors:**
   - darpan and shavez POST `picks` / `phones` / `add` / `merge` → refused;
   - shavez `bank` → allowed as today;
   - doctor → allowed.
   - Controls red on the old file (shavez `phones` allowed there).
8. **Undo:** on a fresh merge with no later change, every reader returns step 3's numbers again and the Marg rows are un-merged; after a `phones` edit, undo is refused with the sentence. A save posted by the record's key lands on the register row, never the hidden Marg row.
8b. **The staff-eye walk (CLAUDE.md, S444 model):** sign in on the scratch copy as darpan, shavez and a reception login; render each one's portal home and `/finance/porders/s454/order`; assert the order page reads, and that no number, pick, add, merge or switch control is in their HTML of `/page/book` (Shavez's bank *Add/Edit* still present). No duty is added, so DUTY_MAP is not changed.
9. **Staff words:**
   - the no-number card reads the new sentence;
   - no system words (charter 8);
   - order page under 100 KB;
   - Call and WhatsApp lines present.
   - Control: the old file prints `phone number yahan nahi hai`.
10. **Dead code:** `grep` proves no caller of `order_sheet._phones` or `_phones_for` is left (or the README says why one stays).
11. Assert no run of 10 digits in the walk's own output. **The walk's made-up numbers are built at run time (e.g. `"9" + "0"*5 + "%04d" % n`), never written as 10-digit literals** (F-185); run `python -B deploy_kits\NO_PHONE_NUMBERS.py --files-from <list> .` over every file the kit adds, before publishing.

## 5 · Install, publish, report
1. Gates → FROM pins → compile all pythons with `python` → walk + controls → backups (`<file>.bak_S574_<md5-8>` each, `finance.db.bak_S574_<stamp>`).
2. Place → md5 read-back → ONE restart of `clinic-finance` → healthz 200.
3. Read by the app's test client on a copy, as the doctor and as reception: the switch OFF, the book page as today plus the *Turn on* line, the staff order page unchanged.
4. **Do not turn the switch on and do not run the merge.** Both are the owner's taps.
5. Red at any point: restore, restart, healthz, report.
6. Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`. Write `claude_code_briefs/REPORT_S574.md`: 3–6 plain lines on top — what changed; the switch is OFF; what he will see when he turns it on; the 13 pairs as the walk found them, names only. Then the Charter section (retired, left, seen). Publish again.
