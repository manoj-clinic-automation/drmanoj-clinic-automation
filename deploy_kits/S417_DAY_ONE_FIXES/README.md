# S417_DAY_ONE_FIXES — units on the orders pages, the card shelf, the Yes Bank tile with a provisional NEFT, one item name (F-636)

**Session 283 · 26-Sep-2026 · brief `claude_code_briefs/S417_DAY_ONE_FIXES.md` · Sanjeevni, with PARENT (clinic) files declared.**
Four small, independent corrections from the owner's first day on S403–S414.

## What was built
1. **The stock in the order's own unit** (`purchase_app.py`, `porders.py`, `porders.html`, `finance_ui/finance_approvals.html`).
   `purchase_app.stock_text(units, pack_size, packing, ortho)`: 124 units of a 10-strip → `12 strips + 4`; an orthotic → `3 pcs`; a syrup
   → `3 bottles`; a cream → `tubes`; a pack size nobody knows (`1*1`, pack 1) → the raw count with its unit word (`5 units`), never a bare
   number; when the pack size says 1 but the packing prints `1*15`, the packing decides. Used on **/page/orders** (On hand), **/page/staff**
   (Stock now); `_staff_plan`'s lines carry `stock_text`. The Purchase orders screen: the engine's plan lines and the day's proposals
   (`order_rules.day_state`, read through `porders._day_s410`) carry `stock_text`; the orthotic lines and the owner's full list carry
   `shelf_text` in pieces; `porders.html` sections 1 and 4 print them; the owner's Purchase orders table prints the shelf in pieces.
   Every number stays as it was; the words sit beside it. **The WhatsApp text is untouched** (the D-decided format).
2. **The card shelf** (`packs.py`, `stmt_shelf.py`; clinic files, declared). `packs.card_read(text)` reads the decrypted card PDF's own
   statement date, billing period and card number(s): HDFC's layout (`Statement Date 15 Aug, 2026`, `Billing Period 16 Jul, 2026 - 15 Aug,
   2026`, `Credit Card No. 4572…XX…6098`), HDFC's older layout (`Statement Date:15/03/2025`, no period printed → the month up to the
   statement date; `Card No: 4572 62XX XXXX 6098`), ICICI's (`STATEMENT DATE` over `August 12, 2026`, `Statement period : July 13, 2026 to
   August 12, 2026`, the card as `4315XXXXXXXX9012`) — never the `linked savings account XX…` line that had given the old identifier a bank
   account's tail. A card's month is **the month its statement is dated in**. Each card slot learns every number its statements print, the
   newest first (the ICICI Amazon card, re-issued in Feb 2026: both forms, one card); an owner-set tail is never overwritten; `place()`
   compares tails as sets. The password-locked original's twin is the file of the **same name** in the card's Decrypted folder (the locked
   file cannot be read): with a twin it is `duplicate of decrypted`, without one its month (its name's date less a day) reads `decrypted copy
   not yet made` on pack row 4. A card's locked original is never handed to the Yes Bank unlock step. An `.xlsx` in the Credit Card
   Statements root is the running Excel: `stmt_shelf.fetch` files it as `all_txn`, `_process_once` turns an old row into `all_txn`,
   `unplaced()` never lists it; pack row 4's attachment. The electricity line reads bank slots only (never a card's tail).
3. **The Yes Bank tile** (`sanjeevni_approvals.py`, `finance_approvals.html`). `provisional_nefts()`: a `purchase_neft_event` of kind
   provisional, tapped by the owner or seen by SMS and confirmed by him, with no `bank_line_id` (S407), no NEFT debit of the same amount
   (within `neft.stmt_tolerance_p`) from 3 days before to 15 after its date in the loaded lines, and dated after the loaded statement's end
   → `− ₹X provisional NEFT (awaiting statement)` under the balance, the headline net of it and marked `incl. provisional`. The moment the
   statement confirms it the line goes; a statement that already covers its date carries the debit inside its closing balance, so nothing
   is counted twice. Read-only; no table. With no such event the Bank answer is byte-identical. Amir's board shows no balance (checked; none
   added).
4. **JIARDIANCE** — `name_search_s417.py` (read-only, facts only): every stock / sale / purchase name matching `(J|G)I?A?RDIAN` on its
   letters (JARDIANCE, JIARDIANCE, GRDIANS, GARDIAN; not GUARDIAN) with strength, packing, stock, suppliers, last purchase, last sale, salt,
   order rule. Run by the installer on the live database; its output is in the install log and the report. Nothing is renamed.

## Pins (read live 26-Sep-2026 21:00 IST; each equals the previous kit's TO pin)
| file | FROM | TO |
|---|---|---|
| /root/finance/purchase_app.py (S409's TO) | cdd4e9c069bc8ab78160349a11a4a4c7 | 9c40d13ed222addeadf97d3f352f359a |
| /root/finance/porders.py (S410's TO) | c75fc91060d127fd05c56b6b81ad9b97 | 64465af0835bdc5583ae7468cacc8c16 |
| /root/finance/porders.html (S410's TO) | 5913e99302930d9fae24c42ac630f010 | 124c4d41b9491203899f324b8a194763 |
| /root/finance/finance_ui/finance_approvals.html (S414's TO; clinic file, declared) | eba564a425c1fc844f1d8d975a1d5eca | 588975fcff2644db115b63058c4d62dc |
| /root/finance/sanjeevni_approvals.py (S410's TO) | c5b93455a69083a6b8d634014898bd30 | 64548b9b36770992dd3da2081e52ffe1 |
| /root/finance/packs.py (S412's TO; clinic file, declared) | 359403f792eaafad37d4eeac3f762641 | 938aa68fbe064b5025768ecfbff89897 |
| /root/finance/stmt_shelf.py (S412's TO; clinic file, declared) | 94f456ce0a6f469ecd7d3f16ca1e874e | 95ba0a4fadd25d9f30a67e7f99eba9f1 |

Not touched: `packs.html` (the cell already prints the tail, the period and the state it is given), `order_rules.py`, `amir_day.py`,
`finance_app.py`, `portal.py`, the cron. Restarts `clinic-finance` only.

**Data:** `seed_s417.py` on the live database after the backup — every card file (`cards`, `decrypted`) gets `read_status` cleared and
`packs.process_inbox` looks at it again with the new reader; the `.xlsx` row becomes `all_txn`. Bank-folder rows are not touched (the
walk proves the bank rows, the bank slots' tails and the four bank tables are unchanged).

## Proof
`walk_s417.py` — the real `finance_app` over scratch copies, own rows by key (W417 …), a negative control on the box as it is in every
part: (1) the unit words, `/page/orders`, `/page/staff`, the plan / proposal / orthotic lines, the pages' templates, the WhatsApp text
byte-identical; the old files print the bare 124. (2) a fixture Drive — two months of decrypted card statements in HDFC's two layouts and
ICICI's, the Amazon card re-issued between them, the locked originals (random-password AES), one locked original without a twin, the Excel
in the cards root and an old-style Excel row — cells, tails, pack row 4, the twins, the Excel; the old files learn nothing and ask about
both Excel rows. (3) the tile — byte-identical with no event; a crafted provisional NEFT shows the line and nets the headline; an SMS
event not yet confirmed, a rejected one and one carrying S407's bank line never show; a confirming statement line removes it; a statement
covering it closes lower and the headline equals the provisional headline (counted once); the old files do not move. (4) the name search
finds the crafted JIARDIANCE / GRDIANS names with their fields, not the GUARDIAN decoy; an exact search misses them; nothing written.
(5) the real shelf on a scratch copy: before, no decrypted statement dated; after `seed_s417`, every one read, the three slots' numbers
learned, the August cells and pack row 4 filled, every twin a duplicate, the Excel all_txn; the bank rows and tables unchanged.
The two pages' changed script lines were run in a browser engine with stub data in the session (the tile's HTML with no event is
byte-identical to today's). Then S414's, S412's, S411's, S410's, S409's, S408's (26/27 + the S411-declared supersession), S407's, S406's,
S405's, S404's (on the 14:04 backup, as S414 ran it), S403's, S400's and S402's own walks re-run on the patched files, with S414's
declared scratch pre-states.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S417_DAY_ONE_FIXES/install_S417_DAY_ONE_FIXES.sh
```
Undo: the seven `.bak_S417_<from8>` files back, `systemctl restart clinic-finance`, healthz 200. The card re-identification is data and
harmless (the old files read it too); `finance.db.bak_S417_<stamp>` only if the owner asks.
