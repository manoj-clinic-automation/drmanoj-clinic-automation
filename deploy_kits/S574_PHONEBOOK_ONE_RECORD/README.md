# S574_PHONEBOOK_ONE_RECORD — one dealer, one record in the phone book (installs switched OFF)

**Brief:** `claude_code_briefs/S574_PHONEBOOK_ONE_RECORD.md` (v2, Sanjeevni session 322). **The owner's word:** "Proceed with the build",
18-Oct-2026 06:19 IST, after mock-up v2. No D or F number of its own (rides the close). Kit shape: S570's / S561's.

## What it does

- **One reader (charter 2).** `purchase_app.book_record / book_numbers / book_number(con, name, use) / book_shown`, use = `call` (a Call
  button, a `tel:` link), `order` (where a WhatsApp order goes), `pay` (a NEFT or cheque notice). `_phone_for` stays as the one-line
  `order` wrapper, so `porders.py` and `order_rules.py` are unchanged. Every reader of a number now goes through it:
  - `purchase_app`: `/page/orders` tel: links → `call`; `_staff_plan` / `_staff_send` (via `_phone_for`) → `order`; `/page/staff` Call buttons → `book_shown`.
  - `order_sheet`: the cards (`book_card`: `phone` = Calls, `wa` = Order WhatsApp, `shown`, `book_on`; `has_phone` from the WhatsApp
    number); `_queue_message` → `order`; the has-a-number checks (≈447, ≈1726, via `_phone_for`) → `order`.
  - `order_sheet_pdf`: the band prints `book_shown` (OFF numbers 1–2; ON the Calls number, and the WhatsApp number when another).
  - `porders_s454`: *Call karo* and the done list's Call → `call`; the numbers under the name.
  - `supplier_msg._digits` (NEFT and cheque notices, read by the name on Marg's bill) → `pay`.
- **The switch `purchase.book_one_record.on`** (written `'0'` by the app on its first phone-book read). **OFF = as before, exactly:** the
  row whose `vendor_norm` is `supplier_key(name)`, its `phone`; numbers 1–2 for a list; no pick read; Marg's push is the old statement byte
  for byte; staff words as before. **ON:** a merged row's record (one hop); a bill name with no row of its own → the bank sheet's record by
  `purchase_vendor_alias` (the one intended change before any merge: RAVI MEDICAL AGENCY now finds RAVI MEDICAL AGENCIES' number); numbers
  1–4; the owner's picks (a blank pick = number 1, else the first number).
- **Schema (idempotent, in `_ensure_book`):** on `purchase_vendor_contact` `phone3`, `phone4`, `email1`, `email2`, `call_pick`,
  `order_pick`, `pay_pick`, `display_name`, `merged_into`; tables `purchase_vendor_premerge` (the two rows as they stood, for undo; never
  deleted) and `purchase_book_change` (last 4 digits only); the setting at `'0'`.
- **The merge (the owner's tap, switch ON):** for each alias pair with both rows and neither merged — the premerge copy first; the bank
  sheet's row keeps its numbers in their slots and takes Marg's numbers it lacks (by the digits) into empty slots, up to 4 (a fifth is
  listed in the changes); the name he keeps (default `_acct_name_s265('', Marg's vendor, Marg's norm)`); when the first numbers differ
  (live: KEDAR only) all three picks → the slot of Marg's number; Marg's row gets `merged_into` and nothing else. Nothing is deleted; the
  bank sheet's `vendor`, `acct_name` and bank fields are not touched. **Undo** restores the slots, picks and name from the premerge copy and
  clears `merged_into`; refused once any change other than "merged" stands for a merged record (*"Undo is closed: numbers were changed
  after the merge."*).
- **Marg's push, switch ON:** a number already in a slot → only `updated_at`; else into the first empty slot ("from Marg"); all four
  full → nothing written, one `marg_extra` line per dealer and number, and the owner's line *"Marg has another number for <name> (…1234)"*
  until he edits that dealer's numbers. Never a replace, never `vendor`, never a pick, never a row for a merged name. No record → insert as
  before. **Named behaviour change, switch ON, every dealer:** Marg's number is *added*, no longer *replaces* a non-`server` number.
- **The doors (rule 13):** `add`, `phones`, `picks`, `merge`, `unmerge`, `switch` — the doctor only, switch ON or OFF (*"Numbers are
  changed only by Dr Manoj."*). `bank` (`supplier_msg.senders`) and `verify` (the doctor) as before. Reading the page as before. The
  screen follows: Darpan and Shavez get no number, pick, add, merge or switch control on `/page/book` (OFF and ON); Shavez keeps the bank
  Add/Edit. A write posts the record's `vendor_norm`; with the switch ON a write to a merged-away row lands on its record.
- **The book page:** OFF — the page as before, plus the doctor's one line *"One record per dealer: OFF — Turn on"*. ON — the switch line,
  the merge panel (Marg's name | the bank sheet's name, last-4 numbers, *Name to keep*, Kedar's "Numbers differ" note, **Merge all N**), the
  undo link (or the closed sentence), Marg's extra numbers, a search box, one line per dealer not merged away (name, *also:* the names
  merged into it, numbers 1–4, the emails, the three drop-downs *Calls · Order WhatsApp · Payment msg* when 2+ numbers, *Edit* in place —
  10 digits starting 6–9, an email with one @ and a dot), the bank block exactly as before, *Add a supplier*, and the last 100 changes.
- **The staff card (switch ON):** `Call: <n>` and `WhatsApp: <n>` under the name; *Call karo* dials the Calls number; *Sab ko WhatsApp
  bhejo* and the queue use the Order WhatsApp number; no number → *"Number nahi hai — Dr sahab ko dijiye"* in place of `nophone` and
  `nophone_l`. OFF: as before, words included.

## Pins (FROM → TO; TO is `PINS.sh`)

| file | FROM | TO |
|---|---|---|
| `/root/finance/purchase_app.py` | 147201dd288d291323023a764df3411e | 98f7d9f05bc06ef6be80181dd9be4c8c |
| `/root/finance/order_sheet.py` | 247eeb48db8cc007faedfe14f3676893 | f00f0163bdd66a074c5af261c9b80a49 |
| `/root/finance/order_sheet_pdf.py` | b0cc86945d560e8cce842b799913e021 | bcd0cde59b916ea390b94d042627aaf9 |
| `/root/finance/porders_s454.py` | 1c3d3927163e08114e3e26c5f06052a4 | 8307976393e6ea161f8d3a94bcb0692c |
| `/root/finance/supplier_msg.py` | 2f43af754a160376cec955f92f3aa43a | 6366ed0f75e0496fcd5ea98866dbddbd |

Read only, must not move (the installer proves it): `amir_day.py` 73882a83 (with `_s494_bank`), `porders.py` a5a823bf, `order_rules.py`
79f21c1e, `finance_app.py`, `portal.py`, `tile_grants.json`, the crontab. The bank readers `_vendor_bank`, `_advice_accounts_s265`,
`_acct_name_s265` and the NEFT advice / payment sheet are not edited. `finance.db`: no data step (the app adds the schema on its first
phone-book read); backed up before placing. Service: `clinic-finance`, restarted once. The build lock.

## The walk (`walk_s574.py`)

The real finance app on backup-API copies of finance.db and assets.db (one snapshot for both sides), the walk's own header session and a
walk-only Marg token; the OLD `purchase_app.py` / `order_sheet.py` loaded beside it for the "as before" answers; its own rows by key
(`W574 …`, made-up numbers built at run time). 0 the live state (the 13 pairs by alias key, RAVI, Kedar the only pair that differs, the
switch); 1 OFF = as before (59 names × 7 readers; the doctor's book page byte for byte plus the one line; the staff order pages byte for
byte; a number 3 saved while ON nowhere after OFF); 2 ON (only RAVI differs); 3 merge (26 dealers by key, Gunina's name, Kedar by both
names, every other name as in 2, the bank readers identical, 39 rows, 13 premerge rows, idempotent); 4 picks; 5 Marg's push; 6 the doors;
7 undo; 8 staff-eye (portal homes, the order page, no control in their book page); 9 staff words (the sentence, Call / WhatsApp, no system
words, under 100 KB; OFF the old words); 10 dead code; 11 no ten digits in its output. `--expect-red` on the old files: every `C:` check red.
`--page` / `--page --after`: the owner's state read before and after placing.

## The undo

Put back the five `/root/finance/<file>.bak_S574_<from8>` files, restart `clinic-finance`, healthz 200, read the md5s back (the FROM pins).
The new columns and tables stay (the old files never read them); `finance.db.bak_S574_<stamp>` is the full copy before placing. If the
owner has already merged: the merge's own **Undo the merge** first (or switch OFF — OFF reads every row as before; Marg's rows' own fields
were never changed).

## Charter

**Retired:** `order_sheet._phones` and `purchase_app._phones_for` (no caller left — walk step 10); the four separate lookups of a number
(`_phone_for`, `_phones_for`, `_phones`, `supplier_msg._digits`' own path) are now one (`book_number`). **Left for later:** `_phone_for`
stays as the `order` wrapper by the brief's word (so `porders.py` and `order_rules.py` stay unedited). **Not a phone-book reader, not
touched:** `order_sheet.phones_new` (≈451, the numbers printed on Marg's own order sheet, shown at porders_s454 ≈1508). **Left out:** nothing.

## Files

`KIT_ID.txt`, `PINS.sh`, `SUMS.md5`, `make_s574.py` (the builder: 26 anchored edits on five files), `walk_s574.py` (the walk and the
before/after look), `install_S574_PHONEBOOK_ONE_RECORD.sh` (the installer), `README.md`. No `.json` in the kit folder.
