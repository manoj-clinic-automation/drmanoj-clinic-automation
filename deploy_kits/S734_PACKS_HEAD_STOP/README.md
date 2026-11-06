# S734_PACKS_HEAD_STOP — a statement's head ends at its first row · the parent · session 394 · 06-Nov-2026

**For the owner, in one line.** Nothing you see changes: the packs page reads each bank statement's top part (bank, holder, account) and now stops at the first transaction row for ICICI and SBI too, so a payment line can never be taken for the holder or the bank.

## Why (F-1148)
`_header()` ended the head only at a row beginning dd-mm-yyyy, a B/F row or a pipe row. ICICI's rows begin with a serial number and SBI's with "1 Jul 2026", so up to 40 lines of rows could count as the head — and the holder words, and the bank read "by its head", could come from a narration. S728 and S729 only guarded their own tests.

## What it changes — `/root/finance/packs.py` fb987b27 (S729) → 7dc8c39a (make_s734.py: 1 counted edit on the live bytes)
The head also ends at a line that begins with a serial number and a date (ICICI), a d-Mon-yyyy date (SBI) or a dd/mm/yy date (HDFC) — only when the line ENDS with an amount, carries a word besides month names, and is not a 'from .. to ..' period line. A period line, a printed time, an interest-rate line, an opening balance, a card summary or an address never ends it. Nothing else.

## Proven
- `walk_s734.py` **15 of 15** on papers laid out like the real ones (`fixtures/`, made-up numbers): the ICICI and SBI heads stop before their first row and carry no narration; a period line, an address and a serial-with-no-amount stay in the head; every fixture's bank, kind, tail, period and SBI type are the live file's. Control (the live file): **8 red**.
- `shelf_s734.py` (run by the installer before placing): every readable paper on the live shelf is identified and placed by the old file and the new one; bank, kind, tail, period, SBI type, holder and slot must all be the same (the app's own Yes Bank readers loaded as in production), or nothing is installed. It prints counts and shelf row numbers only. Rehearsed on the fixtures: same 10 of 10; a broken head goes red.
- Independent cold review: SAFE TO INSTALL; its should-fix built (the amount must end the line, the line must carry words, period lines never stop the head; HDFC's two-digit-year rows; the holder compared on the shelf; undo checks its backup).
- The installer rebuilds the file from the box's own bytes first.

## Install (after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s734kit && cp -rp /root/deploy/repo/deploy_kits/S734_PACKS_HEAD_STOP /tmp/s734kit && bash /tmp/s734kit/install_S734_PACKS_HEAD_STOP.sh
```
## Undo
```
bash /tmp/s734kit/install_S734_PACKS_HEAD_STOP.sh --undo
```
