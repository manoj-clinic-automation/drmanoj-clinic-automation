# S400_MEDICAL_SALE_CHECK — Bhati checks the pharmacy days

**Sanjeevni project · session 283 · 25-Sep-2026 · decision D616 (the owner's words, 25-Sep).**

## What the owner asked for
Bhati becomes the checker of the Sanjeevni days. Next morning he gets the days **not yet approved**, checks Darpan's
paper copy and the Marg sale sheet against what the system shows. Whether Darpan did his job is **flagged**. Bhati
enters **only the amount** of cash Darpan handed over — **Dr Bhawna by default, one tap for Dr Manoj**, the **date is the
sale date**, fixed. A wrong day: minimum typing, maximum drop-downs. He must **not** see month totals or any other cash
part. The owner stays the approver and can do all of it himself exactly as today. Tile: **`Medical sale check`**.

## What was built
**NEW** `/root/finance/sale_check.py` + `/root/finance/sale_check.html` (Hindi, Roman script, phone-first) at
`https://followup.dr-manoj.in/finance/salecheck`:
- **List:** the unapproved days, oldest first — date + weekday, Marg bills count and sale, one chip
  (`Jaanch baaki` / `Sahi hai ✓` / `Galti — N`), and the red flags. An approved day disappears.
- **A day:** Marg bills (bill no, name as the system shows it, amount, tap → its medicines) · returns · UPI from the bank
  (time, last 4 of the reference) · Home/Procedure medicine · **Cash received** · what Darpan recorded as handed.
  The figures are the owner's day panel's own (`sanjeevni_day.day_view`). Never shown: drawer, pool, where it went,
  deposits, banks, months, other days.
- **`Sahi hai`** (one tap, stored once; a second tap answers "already") · **`Galti hai`** → drop-down *Kaunsa bill* (the
  day's bills + `Poora din`) → drop-down *Kya galti* (`Amount alag hai` · `Marg mein bill nahi` · `Kaagaz par bill nahi` ·
  `Home/Procedure nahi laga` · `Cash/UPI galat` · `Aur kuch`) → a note only for `Aur kuch` → `Jodo`. Stored in English keys;
  the same galti twice is refused; he removes his own while the day is unapproved.
- **Cash from Darpan:** one amount box (prefilled with Darpan's figure), toggle Dr Bhawna (default) / Dr Manoj, date = the
  sale date, `Save`. It lands through **darpan_kal's own path** (`darpan_kal_day` → `_decide()` → the ONE `cash_movement`
  `_land_movement()` keeps per day; a re-save updates the same row; every write in `darpan_kal_audit`). If Darpan had
  recorded a different amount, Bhati's figure is the checked one, the difference shows red, and the owner decides on his
  page as today.
- **Red flags** (computed): Darpan recorded no handover · handover ≠ cash received (with the difference) · Marg's sale
  report not in · a bill with no patient name · a HOME/PROSIJER bill with no deduction (the `noncash.*_words` lists).
- A large green card after every save naming what was saved (S394 pattern); a repeat answers an amber card (S393 lesson).

**Access:** a NEW server unit **`salecheck`** (`unit_role`: bhati maker, manoj checker — `seed_s400.py`). Bhati holds **no
medical row**; every other pharmacy address refuses him at the front gate; an approved day answers 403 to him on his own API.
The owner keeps everything; darpan, bhawna, shavez see no change.

**The owner's side (English):** on `/finance/approvals` each day row gains one small line — `Bhati ✓ 09:40` or
`Bhati: 2 mistakes` (tap → bill, problem, note) — with his cash entry and Darpan's differing figure; the owner can **change
the person or move the date** of Bhati's entry (only onto another unapproved day; audited). The day panel's Checks say
what Bhati found. `Needs you` gains `Bhati found mistakes on N day(s)`. Nothing is blocked if he has not checked.

## Pins (FROM → TO, all read on the box 25-Sep 20:22 IST; built by `make_s400.py` from the live bytes, anchored edits)
| file | FROM | TO |
|---|---|---|
| /root/finance/finance_app.py | 70cff4981c2ebf554308545fb071f0d4 | d7ee72c51564a397f4e847e98eb80ddc |
| /root/finance/sanjeevni_day.py | 5d16eff5b6e2f0fd561e22d91e4794ab | 22a38006a4e3be59b47ea091ea1f971f |
| /root/finance/sanjeevni_approvals.py | 7ab5fec63db83af3e11c6ac08599be93 | 5fdfa364dee3dd9dcef9ad5fed3233d9 |
| /root/finance/finance_ui/finance_approvals.html | 750f89e008a89a372af25cf7898a7d17 | 6622587e47faff016bf280d380bd4564 |
| /root/portal/portal.py | 80d6dc44acc07ebb0b974fb792507fee | 592ccf99d02c361d4d5eb580995599c3 |
| /root/portal/tile_grants.json (v25 → v26) | 7d1954760181b4e36e732a974599fd35 | 9231cefad0897a64aa127ce4a448f4fe |

`darpan_kal.py` is **not** touched (the module is mounted from `finance_app.py`, the estate's pattern; it imports darpan_kal's
functions). The `finance_app.py` edit is the allowed one: the path→unit map (`/finance/salecheck/...` → `salecheck`) plus the
guarded mount block. Restarts `clinic-finance` and `clinic-portal` only. `finance.db` is backed up first; the seed adds one
`business_unit` row and two `unit_role` rows, nothing else.

## Proof
`walk_s400.py` — 63 checks, the REAL patched app over a SCRATCH copy of the live database, own rows dated 2099-12-01..04
found by key: the list and a day; every §6 access line (bhati refused on 10 addresses, the owner 200 on all); every red flag
fires on a crafted day and stays quiet on a clean one; Sahi hai once; galti with drop-downs, `Aur kuch` refused without a
note, duplicates refused; ONE cash_movement per day through `_decide`, a re-save updates the same row, default dr_bhawna,
toggle dr_manoj, date always the sale date; the Darpan-different amount shows the difference; the owner's days API, day
panel and Needs you carry the mark; owner person/date change works, is audited, refused onto an approved day or one that
already has a handover; the owner's day panel and Needs you for a real unapproved day are unchanged except the new line;
the portal tile for bhati only. **Negative control:** the unpatched app (a copy of the box) — bhati's page does not open,
no address opens to him, no Bhati mark anywhere, `sale_check` not mounted.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S400_MEDICAL_SALE_CHECK/install_S400_MEDICAL_SALE_CHECK.sh
```
Undo: put back the six `.bak_S400_<from8>` files, remove `sale_check.py` / `sale_check.html`, restart the two services.
