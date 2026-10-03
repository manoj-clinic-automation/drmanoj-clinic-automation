# S454_BILL_REGISTER · part 1C — P1C_SHEET_PAGE_AND_PHONE

Session 283 (Sanjeevni), 03-Oct-2026 · the brief's section 17 (corrections to part 1, found when it was read live on 03-Oct) · D666 / D669.

## What and why

- **17.1 The printed order sheet carries the whole open order.** Under its supplier, every line not yet closed: still to be ordered; in the
  phone's WhatsApp line; ordered and awaited (everything under "Maal aaya?"); then the old pending lines. A line leaves when its goods are
  recorded (the bill's scan, or Marg) or when it lapses. What is done is drawn done: an ordered line has its Order box ticked; a supplier
  ordered by WhatsApp / by call has that band box ticked (only when nothing of it is left to order); the paper load of 02-Oct ticks only its
  lines. The head line counts what is on the page: `Order: dd-mm-yyyy · Darpan (Marg) · N supplier · M dawa: A order karna hai, B ka maal
  aana hai, C purane pending`. One page holds 33 one-line medicine rows under one supplier band; the live order of 03-Oct (10 suppliers,
  28 lines) prints on two pages, no supplier split.
- **17.2** The old-pending tag never prints over another column: it stays after the name when it fits inside the Item cell, else it has its
  own line there (the row grows). A long name wraps inside its cell, never shortened. Phone numbers that would reach the band's boxes go to a
  second line of the band.
- **17.3** The foot's instruction wraps to the page's width.
- **17.5** The owner's English reads "1 medicine" (and "1 supplier", "1 bill"); the staff's Hindi "1 dawa" was already right.
- **17.7** The owner's **Reception phone** card on `/finance/porders?old=1`: when the phone last asked, the order and payment messages
  waiting, the test number (masked to its last four), **Send a test message** (kind `test`: two lines, `Sanjeevni test · dd-mm hh:mm` and
  `Yeh sirf jaanch hai — ₹ 1,234.50`), the last test's times (queued · handed to the phone · sent, or failed with the phone's reason). The
  key is never on it. A test is handed out first, once per gap (F-702), never retried when it failed, and counted nowhere else.
- **17.9** Message id 1 (the August NEFT to A.A. Pharmaceuticals, marked sent at 15:00:27 IST by a test run of the macro although it did not
  go) is put back to waiting by the installer — only if it still reads sent at that time by `reception-phone`. Audited.
- **17.10** `order.phone_alive_min` default 720 and the live value set to 720 (audited); the owner's line says "12 hours". The phone-setup
  page's printed steps are the macro as built: every 1 minute, no loop; the exact header name `X-Phone-Token`; `{lv=msg[...]}`; URL encode;
  the POST copied from the first request; only one WhatsApp (Business); the two constraints and why; a first run by Test actions, watched.
- 17.6 asks for no code: no payment message is held, skipped or re-queued (apart from 17.9).

## Pins (FROM → TO), all in `/root/finance/`

| file | FROM | TO |
|---|---|---|
| supplier_msg.py | fc6c1724d6da4e1d04897b60d61c13b8 | 2f43af754a160376cec955f92f3aa43a |
| porders_s454.py | 05716f3c040478d09fd2016561c7c99c | c2608914e56b0f7ce049d93aeed23d39 |
| order_sheet.py | 93f55d87730e749d78ea5561de38266f | cffbeef3f4405132ab1861ffc146bea9 |
| order_sheet_pdf.py | 9c28df38435a25d7e1d65c34b8d43ec9 | 6e7a5e1a7ae68cb4548c8c8f15cf27cb (replaced whole by this folder's v1.1) |

## Files

- `make_s454p1c.py` — the anchored patcher (every anchor exactly once; FROM pins checked).
- `order_sheet_pdf.py` — v1.1 of the printed sheet (the one place its layout lives).
- `data_s454p1c.py` — the two data steps (17.9, 17.10); prints counts and ids only.
- `walk_s454p1c.py` — the walk: NEW (the built files) and OLD (the box as it is, the negative control) on backup-API copies; the page's
  text measured from the PDF's own text positions and the font's widths.
- `install_S454_P1C.sh` — gates → pins → build → compile on both pythons → walk → backup → place → md5 read-back → restart clinic-finance →
  health (healthz 200; gated pages 302) → data steps → restore on red.
- `pictures/17_reception_phone_card.html` — the owner's card as the walk saw it (the walk's own made-up number, masked).

## Touches

`/root/finance/supplier_msg.py`, `porders_s454.py`, `order_sheet.py`, `order_sheet_pdf.py`; finance.db (message 1, the setting). Restarts
clinic-finance only. Nothing else.
