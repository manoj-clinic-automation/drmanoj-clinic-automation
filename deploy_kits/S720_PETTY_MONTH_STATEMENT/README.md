# S720_PETTY_MONTH_STATEMENT — Bhati's petty book month by month; your tap for Dr Bhawna · the parent · session 390 · 06-Nov-2026

**For the owner, in one line.** The petty book's doctors' page now has a *Month statement* for any month — cash in hand at the start and the end, money received, diaries, payments by head and payee, and the expenses accrued to date — and you can confirm money Bhati says Dr Bhawna gave with your own tap.

## The owner's words (board, 08:11 IST 06-Nov)
"bhati petty book statement, month wise, and accrued expenses i cant see · i shd be able to tap for dr bhawna in petty book and elsewhere wherever needed"

## What it changes — `/root/finance/petty_book.py` d426265e → **bbbc4d82**
- **Month statement** (a section of the doctors' page; `?m=YYYY-MM` opens a month): in hand on the 1st · + received from Dr Manoj / Dr Bhawna (with how many are not yet confirmed) · − each diary · − payments by head · in hand at the month's end · a table of every payee with *this month* and *accrued to date* (from the book's start to the month's end), others grouped by name, the head totals · a monthly payee not paid that month named *due, not paid* (Rahul) · diaries since the start and Bhati's loan at the month's end. Cancelled entries count nowhere.
- The same statement as a page to print: `/finance/petty/statement?m=YYYY-MM` (the doctors only).
- The *Entries* section follows the chosen month.
- **Your tap for Dr Bhawna:** on her entries your page shows *Yes, Dr Bhawna gave it*; the entry then reads *✓ manoj for Dr Bhawna*. Her own tap is unchanged; she cannot confirm yours; Bhati cannot confirm anything. *Elsewhere:* the server has no other screen where only Dr Bhawna can confirm money; the papers desk already has her buttons.
- Bhati's Hindi screens and the viewer's line: unchanged (the walk proves them byte-identical but for the shared style sheet). No table, no setting, no new write besides that confirm.

## Cold review (independent agent, S390)
**SAFE TO INSTALL**, no blocker. Its should-fix points built: an inactive holder's top-ups and a payee under any head are never left off the statement; every month is offered, not the last twelve; a confirm that changed nothing writes no audit row and says so; `--undo` refuses when the live file is no longer this kit's. *Accrued* is read as every payment from the book's start to the month's end, with the monthly payees not paid named *due, not paid* — shown to you on the page.

## Proven
`walk_s720.py` **32 of 32** on a made-up book: every figure against an independent sum (in hand before and after the month, payments, accrued, received, heads, others by name, the due line, the months offered), the print page and its door, the five confirm cases, an inactive holder's top-ups and a payee under another head still counted, and nothing else moved. Control (the live file): **22 red**. Installer rehearsed on a made-up server: DRY, install, ALREADY, undo, the module not mounting after restart (old file back), a changed live file, a tampered kit, the lock held, the app unhealthy before.

## Install (after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s720kit && cp -rp /root/deploy/repo/deploy_kits/S720_PETTY_MONTH_STATEMENT /tmp/s720kit && bash /tmp/s720kit/install_S720_PETTY_MONTH_STATEMENT.sh
```
## Undo
```
bash /tmp/s720kit/install_S720_PETTY_MONTH_STATEMENT.sh --undo
```
