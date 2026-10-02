# S452_AMIR_PANEL_FIXES — what the live walk of Amir's panel found (F-686 · F-687), and the owner's rulings of 02-Oct evening

**Sanjeevni project · session 283 · 02-Oct-2026 · brief `claude_code_briefs/S452_AMIR_PANEL_FIXES.md` · runs after S446_AMIR_STAGES_BILLS
(live 02-Oct 06:15 IST) and builds on its files.** Serves D650 and D648 (no new decision). Staff pages in Hindi (Roman script), the owner's
in English.

## What was built

**3.1 The list holds only bills that are not in Marg (F-686) — `purchase_app.py` (`scans_for_amir`), `amir_day.py`.**
- A scan is listed on step 2 only when the server finds no likely Marg bill for it and its supplier is known: S440's *Marg ka intezaar*
  group as `purchase_scan_state` holds it (the matcher runs first when the scans changed). A near-match (*Yahi bill hai?*), an unread
  supplier (*Supplier chuno*), the shop's own name, a second scan — held for reception's *Scan ka kaam*.
- One grey line under the list: "N scan abhi reception ki jaanch mein hain — Marg mein mat daaliye".
- Each line: the stamp, the supplier (chosen, else matched, else as read), "scan: dd-mm, <who>", and the bill date only within 60 days of
  the scan day, else "bill ki tareekh scan par saaf nahi".
- The file: `<stamp>_<SUPPLIER>[_<billno>]_<dd-mm-yyyy>.pdf` — an unread number is left out; a date outside the 60 days becomes the scan day.
- The download guard: a scan a Marg bill has reached since the page was drawn answers "Yeh bill Marg mein aa chuka hai"; a held scan
  answers "… reception ki jaanch mein hai". The zip of today's follows the same rule.
- The owner's Scan links page: "Amir's list: N to enter · M held for reception".
- The bank's NEFT advice file (full account numbers) is the owner's and the senders' only (`supplier_msg.senders`).

**3.2 The phone key (F-687) — `supplier_msg.py`.**
- The setup page is the owner's and a checker's; a maker or viewer gets the login gate's refusal.
- The key shows to them every time, each showing audited (`purchase_audit` `phone_token_shown`: who, when). "Shown once" is retired:
  it handed the key to whoever opened the page first, and the page admitted every staff login.
- A new key at install (`s452_new_token`); the old one answers 401. The key is never printed.
- The page's first line (Hindi): when the phone last asked the queue door, with which answer, how many messages wait (recorded from now
  in `supplier_msg.phone_last`; before that, read from the app's access log).

**3.3 Step 7 in Roman Hindi — `amir_day.py`.** What keeps the day open as a list; apart from it, "(din band karne se nahi rukta)", the count's
stage line and the salt list. The owner's views (/finance/amir/day, the visit summary) keep `_left()`'s English.

**3.4 The board in Roman Hindi; every duty on his card — `stock_amir.html`, `stock_app.py`, `amir_day.py`.**
- Every fixed word of the board in Roman Hindi (46 line edits, `board_edits_s452.txt`); the board's data too (the reasons, an answer's label).
- "N item ka rate Marg mein daalna hai — kholiye" on his card while due (`stock_app.amir_rate_due`), opening the board at (b).
  An item leaves when it has a rate: in Marg's own item export (the spine: the newest S.RATE or MRP above 0 — both items read 0.0 there on
  02-Oct) or in the server's `stock_rate` (Marg's stock export does not carry rates; only the server's computed feed fills that table). What
  the spine says is mirrored into `stock_rate_marg` whenever the list is read, so `DUTY_MAP` v3's `amir.rate_entry` (one SELECT on
  finance.db) reads the same thing.
- A salt line Marg already shows leaves block (a). Step 6 carries its heading once.

**3.5 NEFT for Amir — `supplier_msg.py`, `amir_day.py`, `packs.py` (the parent's: one edit).**
- Confirmed when the bank's SMS has been read (`purchase_neft_event.source='sms'`, S405) or a statement line confirms it (`bank_line_id`,
  S407) — "NEFT August 2026 — bank ka kaam ho gaya, dd-mm"; or when the owner has entered it (`source='owner'`, provisional counts) —
  "NEFT August 2026 — payment 24-09 ko ho gaya (Doctor sahab ne darj kiya)".
- Before that nothing of the month reaches him. After: one line and the paid NEFT sheet as a PDF, `NEFT_paid_<yyyy-mm>.pdf` (the S408
  sheet's rows, then the total). No supplier names, no "baaki". Shavez's and the owner's pages keep theirs.
- `/finance/amir/pack/<month>/neft` answers the PDF when confirmed and the login gate's refusal when not; no .xlsx by any address.

**3.6 Medicine vouchers: 12 a visit, more on request — `stock_app.py`, `amir_day.py`.**
- `amir.vouchers_per_visit` 12 (the row is moved only if it still reads 5). "Aur voucher kholiye" (POST `/finance/stock/api/pad/amir/<count>/more`)
  opens the next 12 at once, until none is left; each tap audited in `stock_stage_event` (by, n).
- D649's order stays. The proof no longer holds a lot back: every export checks whatever he has entered so far and names an item still
  wrong, with its voucher; the next visit opens 12 more.
- The card: "Dawa voucher: aaj ke N (baaki M)" counts what is open on his board. The owner's line: "Stage C … entered · released · verified".

## Pins (FROM → TO, md5)
| live file | FROM | TO |
|---|---|---|
| /root/finance/purchase_app.py | 176fc6eac35c7a3e7d052cba96ca873e | 341c663e52076f0ee264c356b49cf49e |
| /root/finance/amir_day.py | cd8f4659cb828c09e9455d1b7543cfbd | 85f208d0d64def40fb5a02e02c531284 |
| /root/finance/supplier_msg.py | 02b4a9edc4ff6bc42ed896e7f260be72 | 5cc35d2af444b5ab1996f636db8e54cf |
| /root/finance/stock_app.py | ec6b1ce80d46b808d034b23cab032dc9 | f14a1cfaf9a47b1199a0763ac47d1006 |
| /root/finance/stock_amir.html | 1ec8663dbbad397fe46f093966352e0a | 2e41e406e3b2ef9d7ed75f9f24b923b8 |
| /root/finance/packs.py (the parent's, one edit) | 6a1cf6ceec4a58260df7352e48cdefe5 | 23fda41a19a6d4be398922e906d06702 |

**What it touches:** the six files above; **data** (finance.db, backed up first): `amir.vouchers_per_visit` 5 → 12, a new
`supplier_msg.phone_token`, the retired `supplier_msg.token_shown` row's note; rows written from now: `supplier_msg.phone_last`,
`purchase_audit` `phone_token_shown` / `phone_token_renewed`, `stock_stage_event` releases; one additive table made on first use,
`stock_rate_marg` (the spine's S.RATE / MRP of the items on the rate list). The spine itself is read only. **Restarts** `clinic-finance` only.
**Not touched:** porders.py (read only), portal.py, clinic_sso.py, tile_grants.json, finance_app.py, sanjeevni_approvals.py,
darpan_kal.py, crontab, the medical PC. The installer reads their md5s before and after.

## The files
- `make_s452.py` — the anchored patcher; its blocks `purchase_block_s452.py`, `amir_block_s452.py`, `supplier_block_s452.py`,
  `stock_block_s452.py`; the board's line edits `board_edits_s452.txt`.
- `walk_s452.py` — the walk on scratch copies (its rows keyed W452), with its negative control on the box as it is, and the staff-eye
  walk for amir, darpan, shavez and the owner (a walk-only secret and user store).
- `walks_old_s452.py` + `plan_old_s452.py` — S446's, S444's, S407's, S408's and S434's walks re-run, each twice (the box as it is / the
  box + S452); every adjustment named in the script; a red is accepted only if named and red on the baseline too.
- `apply_s452.py` — the data step and the figures.
- `install_S452_AMIR_PANEL_FIXES.sh` — gates → pins → build → compile both pythons → walk → earlier walks → (DRY stops here) → lock check →
  backups → place → md5 read-back → restart clinic-finance → health → data step (the key compared with the backup's, never shown); restores on red.
- `DUTY_MAP.md`, `DUTY_MAP.json` — v3, the copies placed in `claude_code_briefs/`.

## Run
```
bash <kit>/install_S452_AMIR_PANEL_FIXES.sh
```
(holding `/root/deploy/.claude_code_build.lock` with owner `S452_AMIR_PANEL_FIXES`; `DRY=1` places nothing; from a copy of the kit:
`KITS=/root/deploy/repo/deploy_kits DUTYMAP_OLD=/root/deploy/repo/claude_code_briefs/DUTY_MAP.json`).

## Undo
Put back `/root/finance/<file>.bak_S452_<from8>` for the six files, restart `clinic-finance`, check healthz 200 and read the md5s back.
The setting rows are harmless to the old files. The new phone key stays (the old one was readable by a staff login); `finance.db.bak_S452_<stamp>`
is used only if the data step must be reversed.
