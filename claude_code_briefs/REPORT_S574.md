# REPORT S574_PHONEBOOK_ONE_RECORD — one dealer, one record (installed switched OFF)

**For Dr Manoj:**
1. The phone book can now keep **one record per dealer**, with up to **4 mobile numbers and 2 emails**, and three optional picks per dealer: **Calls**, **Order WhatsApp** and **Payment message** (blank = number 1).
2. It is installed **switched OFF**: today every call button, WhatsApp order and payment message works exactly as before (proved on a copy, page for page).
3. When you open **Phone book** (Purchase → Phone book) you will see one new line at the top: *"One record per dealer: OFF — Turn on"*. After **Turn on**, a box lists the **13 dealers who are in the book twice**; one tap on **Merge all 13** joins each pair. The bank account is not touched, and **Undo the merge** works until you change a number.
4. The 13 pairs (Marg's name → bank sheet's name): Drug Deal → Drug Deals · Ess Kay Agencies Extn → Ess Kay Agencies · Gunina Pharmaceuticals Pvt Ltd → Gunina Pharmaceuticals · Jubilee Agencies → Jubli Agency · Kedar Pharmaceutical → Kedar Pharma · L.K. Drug House → LK Drug House · Radha Medical & Scientific → Radha Medical and Scientific · Saisun Pharma Pvt. Ltd → Saisun Pharma Private Limited · Scientific&Medical Aid Centre → Scientific & Medical Aid Centre · Shraddha Medicose → Shraddha Medicos · Verma Bros. and Co → Verma Bros.And Co · Yogendra Agencies → Yogendra · Yuvika Surgicals → Yuvika Surgical. Only **Kedar** has different numbers in its two rows; the merge keeps both and points all three picks at the number used today.
5. From now on **only you** change numbers or add a supplier (OFF or ON). Darpan and Shavez still read the book; Shavez still does the bank details. When ON, staff see *"Call: …"* and *"WhatsApp: …"* under each dealer, or *"Number nahi hai — Dr sahab ko dijiye"*.

---

## For the chat

**Kit:** `deploy_kits/S574_PHONEBOOK_ONE_RECORD/` (board `_numbers` v461 → v462 is the chat's line). Installed 18-Oct-2026: lock taken 07:01:41 IST,
`clinic-finance` restarted **07:03:26 IST** (read from the installer's output), DONE at 07:03:40 IST (the box's `date`).

### Live files — FROM → TO, md5 read back on the box

| file | FROM (pin matched at the open) | TO (read back after placing) |
|---|---|---|
| `/root/finance/purchase_app.py` | 147201dd288d291323023a764df3411e | 98f7d9f05bc06ef6be80181dd9be4c8c |
| `/root/finance/order_sheet.py` | 247eeb48db8cc007faedfe14f3676893 | f00f0163bdd66a074c5af261c9b80a49 |
| `/root/finance/order_sheet_pdf.py` | b0cc86945d560e8cce842b799913e021 | bcd0cde59b916ea390b94d042627aaf9 |
| `/root/finance/porders_s454.py` | 1c3d3927163e08114e3e26c5f06052a4 | 8307976393e6ea161f8d3a94bcb0692c |
| `/root/finance/supplier_msg.py` | 2f43af754a160376cec955f92f3aa43a | 6366ed0f75e0496fcd5ea98866dbddbd |

Read only, at their pins before and unmoved after: `amir_day.py` 73882a83…, `porders.py` a5a823bf…, `order_rules.py` 79f21c1e…, `finance_app.py`,
`portal.py`, `tile_grants.json`, the crontab. Built on the box from the live bytes by `make_s574.py` (26 anchored edits, each anchor exactly once);
each built file compiled on `/usr/bin/python3` and the venv python; the placed files are byte-identical to the walked ones (`cmp`).

### Backups
`/root/finance/<file>.bak_S574_<from8>` for all five (`purchase_app.py.bak_S574_147201dd`, `order_sheet.py.bak_S574_247eeb48`,
`order_sheet_pdf.py.bak_S574_b0cc8694`, `porders_s454.py.bak_S574_1c3d3927`, `supplier_msg.py.bak_S574_2f43af75`);
`finance.db.bak_S574_20261018_070141` and `finance.db.bak_S574_20261018_070308` (backup API, 39,460,864 bytes each — one per attempt, see below).
**Services restarted:** `clinic-finance` only — twice in all: once by the first attempt's restore, once by the install that stands.

### The first attempt went red after placing — and restored itself
Run 1 (07:01:41) placed the five files and restarted at 07:02:00; healthz 200, the pages 302, the journal clean; then the after-placing look of the
owner's page went **red**: my check "no merge panel while OFF" looked for the text `s574merge`, which the OFF page also carries inside its script
(the merge button's handler). The installer restored all five files byte-identically (md5s = FROM), restarted, healthz 200. Checked on the live
database at once: no S574 column, no new table, no switch row, 39 rows, no book write since 07:00 — the window left nothing. Fix: the look tests
the element (`id="s574merge"`), and the walk's "ordering is frozen" note now asks `order_rules._frozen` (the live `order.freeze` is blank —
ordering is open; the old note misread a blank row as frozen). The kit was not yet published, so its walk was corrected in place; the published
kit is the one that ran in run 2 (07:03:08), byte-identical by `md5sum -c SUMS.md5` on the box before the run.

### The walk (run 2, on backup-API copies of the live finance.db and assets.db; the real finance app; the walk's own session and Marg token)
```
pair DRUG DEAL | DRUG DEALS | Marg's row 1 number(s) …9821 | bank sheet's row 1 number(s) …9821 (bank: VERIFIED)
pair ESS KAY AGENCIES EXTN | ESS KAY AGENCIES | …7380 | …7380
pair GUNINA PHARMACEUTICALS PVT LTD | GUNINA PHARMACEUTICALS | …6632 …3999 | …6632 …3999
pair JUBILEE AGENCIES | JUBLI AGENCY | …5856 | …5856
pair KEDAR PHARMACEUTICAL | KEDAR PHARMA | …0679 | …5343 …0679
pair L.K. DRUG HOUSE | LK DRUG HOUSE | …1178 | …1178
pair RADHA MEDICAL & SCIENTIFIC | RADHA MEDICAL AND SCIENTIFIC | …3972 | …3972
alias RAVI MEDICAL AGENCY | RAVI MEDICAL AGENCIES | Marg's row none, bank sheet's row yes
pair SAISUN PHARMA PVT. LTD | SAISUN PHARMA PRIVATE LIMITED | …6664 | …6664
pair SCIENTIFIC&MEDICAL AID CENTRE | SCIENTIFIC & MEDICAL AID CENTRE | …5894 | …5894
pair SHRADDHA MEDICOSE | SHRADDHA MEDICOS | …6972 | …6972
pair VERMA BROS. AND CO | VERMA BROS.AND CO | …8100 | …8100
pair YOGENDRA AGENCIES | YOGENDRA | …8294 | …8294
pair YUVIKA SURGICALS | YUVIKA SURGICAL | …2525 | …2525
39 rows; 14 alias rows; 13 pending pairs; singles (no alias): 12; the switch absent
ok   the live state: the pending pairs are exactly the brief's 13, by alias key
ok   the live state: RAVI MEDICAL AGENCY has an alias row and no row of its own; its bank record exists
ok   the live state: Kedar is the only pair whose first numbers differ
ok   the live state: the switch is absent or '0'
-- 1  OFF = as before
ok   the pages answer 200: /page/book (manoj), /finance/porders/s454/order (shavez)
     compared 59 names x 7 readers with the switch OFF
ok   C: OFF -- every reader (order, call, pay, _phone_for, book_shown, book_card) for all 59 names equals the old file's
     _phone_for / _phones_for / order_sheet._phones / _wa_digits(_phone_for)
ok   OFF -- the order sheet's bands print the old numbers (14 bands)
ok   C: OFF -- the doctor's book page carries 'One record per dealer: OFF' and a Turn on button
ok   C: OFF -- the doctor's book page is the old page byte for byte, plus the one line and its script
ok   OFF -- the staff order page and 1 supplier pages (shavez) are the old ones byte for byte (the tap's moment t= aside)
ok   C: while ON, number 3 of a made-up dealer (W574 THREE) is saved and read (slot 3)
ok   after OFF the number 3 appears nowhere: no reader, neither book page (the doctor's, Darpan's)
-- 2  ON before the merge
ok   C: the doctor turns the switch ON
ok   C: ON, before the merge -- every reader for every name as before, except exactly RAVI MEDICAL AGENCY
ok   C: RAVI MEDICAL AGENCY now gives its bank record's number (…8852; the old file: none)
ok   C: the doctor's ON page shows the merge panel: '13 dealers are in the book twice' and 'Merge all 13'
ok   the panel's default names: JUBILEE AGENCIES, GUNINA PHARMACEUTICALS PVT LTD, SAISUN PHARMA PVT. LTD. selected
ok   the panel says the numbers differ for Kedar only
-- 3  merge all
ok   C: the doctor taps Merge all: 13 pairs merged
ok   C: the book page lists 26 dealers -- every record not merged away, by key (39 rows less the 13 merged)
ok   C: Gunina's record keeps the name GUNINA PHARMACEUTICALS PVT LTD
ok   C: Kedar's order, call and pay numbers equal the Marg row's phone (…0679), by KEDAR PHARMACEUTICAL and by KEDAR PHARMA
ok   C: every reader's number for every other name equals step 2's (58 names; KEDAR PHARMA itself now gives Marg's number, as the brief's step 4 orders)
ok   the bank readers (_vendor_bank, _advice_accounts_s265, amir_day._s494_bank) give the same for every norm before and after
ok   C: no row deleted (39 before, 39 after); purchase_vendor_premerge holds 13 rows
ok   Marg's rows: only merged_into set; the bank sheet's rows: vendor, account name and bank fields untouched
ok   a second Merge all merges nothing (keyed, idempotent)
-- 4  picks
ok   C: Kedar's Payment msg set to number 1 -> supplier_msg._digits('KEDAR PHARMACEUTICAL') gives it (…5343)
ok   Kedar's Order WhatsApp number unchanged (…0679)
ok   supplier_msg._digits is non-empty for every name that has a number (59 names)
ok   C: the doctor's page carries the three drop-downs on Kedar's line (2 numbers) and the pick in the changes
-- 5  Marg's push
ok   push, an existing number (DRUG DEAL BAREILLY, …9821): nothing changes but updated_at
ok   C: push, a made-up new number for a merged dealer (JUBILEE AGENCIES BAREILLY): into the record's free slot (phone2), Marg's row untouched,
     rows still 39, one 'from Marg' line
ok   C: push, a made-up number for a full dealer (W574 FULL, 4 numbers), twice: nothing written to the record, one 'marg_extra' line, and the
     owner's line 'Marg has another number for W574 FULL (…0515)'
ok   after the doctor edits W574 FULL's numbers the owner's line is gone
ok   push, a made-up new dealer (W574 NEW DEALER): a new row with its number
ok   switch OFF: the push is the old statement -- Marg's own row takes the pushed number (it is not 'server'), a new name makes a row
-- 6  the doors
ok   C: darpan posts picks / phones / add / merge / unmerge / switch: each refused 403 'Numbers are changed only by Dr Manoj.'
ok   C: shavez posts picks / phones / add / merge / unmerge / switch: each refused 403 'Numbers are changed only by Dr Manoj.'
ok   shavez saves bank details as before (allowed, UNVERIFIED)
ok   darpan's bank save refused as before ('Bank details are for Dr Manoj and Shavez.')
ok   C: the doctor's picks, phones and add are allowed
ok   a number not starting 6-9 is refused (the one-record page's check)
ok   an email without one @ and a dot is refused
-- 7  undo
ok   C: undo on a fresh merge: every reader for every name gives step 2's numbers again (Kedar PHARMA included); Marg's rows unmerged
ok   the premerge rows are kept and marked undone (13)
ok   C: a save posted by the record's key lands on the bank sheet's row (number 3), never the hidden Marg row; one by Marg's name too
ok   C: after a number edit the undo is refused: 'Undo is closed: numbers were changed after the merge.' (the API and the page)
-- 8  staff-eye
ok   staff-eye: each portal home renders its tiles, 'Purchase orders' on it, for darpan, shavez, reception (the real portal.py + the grants file, a walk-only secret)
ok   staff-eye: darpan reads /finance/porders/s454/order (200, 9438 bytes)
ok   staff-eye: shavez reads /finance/porders/s454/order (200, 9438 bytes)
ok   staff-eye: reception reads /finance/porders/s454/order (200, 12285 bytes)
ok   C: switch ON -- darpan's book page (200) has no number, pick, add, merge, undo or switch control
ok   C: switch ON -- shavez's book page (200) has no number, pick, add, merge, undo or switch control
ok   switch ON -- Shavez's book page keeps the bank Add/Edit as before
ok   C: switch OFF -- darpan's book page (200) has no number, pick, add, merge, undo or switch control
ok   C: switch OFF -- shavez's book page (200) has no number, pick, add, merge, undo or switch control
ok   switch OFF -- Shavez's book page keeps the bank Add/Edit as before
ok   a reception login does not open the book page (as before)
     no duty is added, moved or removed: DUTY_MAP is not changed by this kit
-- 9  staff words
ok   C: switch ON, a made-up dealer with no number (W574 NONUM): its page reads 'Number nahi hai — Dr sahab ko dijiye', not 'phone number yahan nahi hai'
ok   C: ... and its card on the list (pending) reads 'Number nahi hai — Dr sahab ko dijiye'
ok   C: Kedar's page (merged) carries 'Call: <the Calls number>' and 'WhatsApp: <the Order WhatsApp number>'; Call karo dials the Calls number
ok   the WhatsApp queue sends Kedar's order to the Order WhatsApp number
ok   the order sheet's band for Kedar prints the Calls number (and the WhatsApp one when another)
ok   no system words (point, trace, round, gap, base, row, id, sync) on the staff order page or Kedar's page
ok   the staff order page is under 100 KB (10273 bytes)
ok   switch OFF: the same page reads the old sentence ('Is supplier ka phone number yahan nahi hai'), words as before
-- 10 dead code
ok   C: dead code -- no definition or caller of order_sheet._phones or purchase_app._phones_for in the new folder
ok   every staff order page the walk opened: under 100 KB and under 2 s (9 reads)
ok   11 the walk's own output holds no run of 10 digits
WALK OK S574: 70 checks green (OFF as before, ON, the merge, picks, the push, the doors, undo, staff-eye, staff words, dead code)
```

### The negative control (the same walk on the OLD five files, `--expect-red`)
```
RED on the old files: C: section '1' ran to its end
RED on the old files: C: the doctor turns the switch ON
RED on the old files: C: section '2' ran to its end
RED on the old files: C: the doctor taps Merge all: 13 pairs merged
RED on the old files: C: section '3' ran to its end
RED on the old files: C: section '4' ran to its end
RED on the old files: C: section '5' ran to its end
RED on the old files: C: darpan posts picks / phones / add / merge / unmerge / switch: each refused 403 'Numbers are changed only by Dr Manoj.'
RED on the old files: C: shavez posts picks / phones / add / merge / unmerge / switch: each refused 403 'Numbers are changed only by Dr Manoj.'
RED on the old files: C: the doctor's picks, phones and add are allowed
RED on the old files: C: section '7' ran to its end
RED on the old files: C: switch ON -- darpan's book page (200) has no number, pick, add, merge, undo or switch control
RED on the old files: C: switch ON -- shavez's book page (200) has no number, pick, add, merge, undo or switch control
RED on the old files: C: switch OFF -- darpan's book page (200) has no number, pick, add, merge, undo or switch control
RED on the old files: C: switch OFF -- shavez's book page (200) has no number, pick, add, merge, undo or switch control
RED on the old files: C: switch ON, a made-up dealer with no number (W574 NONUM): its page reads 'Number nahi hai — Dr sahab ko dijiye', not 'phone number yahan nahi hai'
RED on the old files: C: ... and its card on the list (pending) reads 'Number nahi hai — Dr sahab ko dijiye'
RED on the old files: C: section '9' ran to its end
RED on the old files: C: dead code -- no definition or caller of order_sheet._phones or purchase_app._phones_for in the old folder
WALK OK negative control: every one of the 19 'C:' checks is red on the old files (20 of 38 checks red)
```
(A section that cannot start on the old files — no switch, no merge, no `book_number` — is one red control; the old run's own dump of the
doctor's book page and the staff order pages is what run 2's step 1 compared byte for byte.)

### The owner's state, before and after placing (installer steps 6 and 10; a copy of the live database; the app's test client)
```
BEFORE  switch: absent · 39 rows · 13 pairs pending · /page/book (doctor) 200, 46510 bytes, no switch line, no merge panel
        /finance/porders/s454/order: shavez 200 (9438 bytes), reception 200 (12285 bytes), the new no-number sentence absent
AFTER   switch: absent before the first read, '0' after it · 39 rows · 13 pairs pending
        /page/book (doctor) 200, 50300 bytes, 'One record per dealer: OFF -- Turn on' shown, the merge panel not there
        /finance/porders/s454/order: shavez 200 (9438 bytes), reception 200 (12285 bytes), the new no-number sentence absent
PAGE OK S574: switch OFF, the book page as before plus the doctor's line, the staff order page as before
```
healthz 200 after the restart; `/finance/purchase/page/book`, `/finance/porders/s454/order`, `/finance/purchase/page/staff` 302 to a plain curl
(the login gate, expected); the journal clean (no Traceback, no "NOT mounted"). **Not done, by the brief:** the switch is not turned on and the
merge is not run — both are the owner's taps. The schema (four new number/email columns, three picks, `display_name`, `merged_into`, the two
tables, the switch row at `'0'`) is added by the app on the first phone-book read after the install — no data step, no hand edit.

### Calls made (no question was put to the owner)
- **KEDAR PHARMA by its own name** now reads Marg's number after the merge (all three picks point there, as §3.3 step 4 orders); the walk's
  "every name as in step 2" therefore excludes that one name and asserts it equals Marg's phone. No reader asks by that name today (orders and
  the NEFT notice read Marg's bill name), so nothing anyone sees changes.
- **Undo is all-or-nothing:** one link undoes every standing merge; it closes as soon as any change other than "merged" stands for any merged
  record (a "from Marg" or "marg_extra" line counts, by the brief's literal rule).
- **The doors apply OFF as well** (§3.5): with the switch OFF Darpan and Shavez can no longer edit numbers or add a supplier, and the page no
  longer shows them those buttons (rule 13). Shavez's bank Add/Edit is unchanged.
- **`/page/staff`** (the old staff page) rings `book_shown`: OFF numbers 1–2 as before; ON the Calls number, then the WhatsApp number when another.
- **Picks need the switch ON** (refused while OFF, so OFF stays exactly as before); the 6–9 mobile check applies to the one-record *Edit*
  (ON); the OFF number edit keeps today's 10-digit check. Every number in the live book (numbers 1 and 2 of all 39 rows) is already a 10-digit mobile starting 6–9 (read at the open).

## Charter
- **Retired:** `order_sheet._phones`, `purchase_app._phones_for` (walk step 10: no definition or caller left). The four lookups of a number are one: `book_number`.
- **Left for later:** `_phone_for` stays as the one-line `order` wrapper (the brief's word), so `porders.py` and `order_rules.py` stay unedited.
- **Left out:** nothing.
- **Seen, not touched:**
  - Darpan's book page (OFF and ON, as before S574) shows the bank *add/edit bank details* button, which his door refuses ("Bank details are for Dr Manoj and Shavez.") — rule 13; the brief keeps the bank block exactly as today.
  - The printed order sheet still says *"(number nahi hai)"* for a dealer with no number; the brief replaced only the two screen keys `nophone` / `nophone_l`.
  - `order_sheet.phones_new` (≈451) is not a phone-book reader (the numbers on Marg's own order sheet) — named, not touched.
- **Dependency at install (rule 1b):** none scheduled — the pages read the phone book only. Marg's nightly number push last came 17-Oct 22:30:15 IST and keeps its old behaviour while the switch is OFF.
- **DUTY_MAP:** no duty added, moved or removed — not changed.

### Publish and the lock
`PUBLISH_ALL.bat` published and verified **aa9a0c3** (it also carried what the other chats had pending: the S575 brief, the S576 kit, the canon
files — expected, charter). The server clone `/root/deploy/repo` pulled to aa9a0c3; there `md5sum -c SUMS.md5` is OK for all six files and every
kit file is byte-identical (`cmp`) to the copy that ran. The five live files read back at their TO pins again, healthz 200; the build lock
(owner S574) released at **07:05:37 IST** (the box's `date`); `/tmp/s574kit`, `/tmp/s574probe` and the installer's scratch removed. This
report is published once more after this line.

### Undo (if the owner says "undo")
If he has merged, first his own **Undo the merge** (or **Turn off** — OFF reads every row as before; Marg's rows' own fields were never changed).
Then: `\cp -p` each `/root/finance/<file>.bak_S574_<from8>` back over the five files, `systemctl restart clinic-finance`, healthz 200, read the
md5s back (the FROM pins). The added columns and tables stay (the old files never read them); `finance.db.bak_S574_20261018_070308` is the full
copy from just before placing.
