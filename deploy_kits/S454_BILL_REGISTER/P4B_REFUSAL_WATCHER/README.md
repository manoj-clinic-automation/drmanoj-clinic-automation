# S454_BILL_REGISTER · part 4, the medical PC — P4B_REFUSAL_WATCHER

Session 283 (Sanjeevni), 03-Oct-2026 · the brief's sections 10.1 and 10.3.

## What and why

`marg_watch.py` S454 is built from the live watcher's bytes (S397, 81145aa7, the medical PC heartbeat's own md5 on 03-Oct) by
`make_s454p4b.py`, with anchored edits:

- When a text is kept as refused, the watcher sends the server a note. This covers both a reader's refusal and a finished report it does not
  know. The note holds the file's name, its md5, the kind it looked like (SALE, STOCK, ORDER) and the reason, and never a line of the file.
  A run of six or more digits in the reason (a phone number on a letterhead) is masked first.
- It sends with the address and the key `marg_push.py` already uses (`MARG_PUSH_URL`, `token.txt`). `marg_push.py` is not changed.
- It sends in a daemon thread of its own, so capture never waits. It tries three times, a minute apart.
- It sends once per file: a file already kept is never kept or noted again. That includes the retry of the last three days at a start.
- It sends nothing while sending is switched off (`_off\ALL_OFF.txt`, `_off\MARG_PUSH_OFF.txt`).
- "Why not" learns Darpan's order sheet ("an order sheet without the '*** End of Report ***' line…"). An order sheet saved under another name
  than `report*.txt` is kept and noted too.
- The selftest adds six checks. Notes are collected, never sent, in the selftest. It passes with the S454 reader beside it.

`KIT_MANIFEST.txt` is part 1's with one more comment block. The watcher is on the agent's built-in list and needs no line. The folder keeps it
with LF line endings (b8ff9568); Drive keeps it with CRLF, 9e754e5c.

## The order of delivery (§10.3): NOT BEFORE 04-Oct-2026 13:00 IST

The agent restarts the watcher when `marg_watch.py` changes. At its start the watcher offers the reader again every refused text younger than
three days. Before 04-Oct 13:00 IST that would send the refused sale texts of 30-Sep and 01-Oct once more. `deliver_S454_P4B.ps1` refuses to run
before then (tried on 03-Oct at 19:07 IST: refused, nothing delivered).

Run it on manojz from this folder, after 04-Oct 13:00 IST:

```
powershell -ExecutionPolicy Bypass -File deliver_S454_P4B.ps1
```

It does these steps in order:

1. Checks the clock (IST) and this folder's two files.
2. Pins Drive's `marg_watch.py` (81145aa7) and `KIT_MANIFEST.txt` (05fb3485).
3. Keeps a `.superseded` copy of each.
4. Places the new files and reads the md5s back. If either is red, it puts both back.

Then confirm by the heartbeat (`FromMedical\heartbeat.txt`): it should read `marg_watch.py up to date (20ec1602)`. The log should show
`marg_watch S454 starting` and what its start offered again.

## Pins

Drive `ToMedical\_kit\marg_watch.py` 81145aa7 → 20ec1602 · `KIT_MANIFEST.txt` 05fb3485 → 9e754e5c (CRLF). The walk is P4A's `walk_s454p4.py`,
section W.

## Files

- `make_s454p4b.py`
- `marg_watch.py`: the built file.
- `KIT_MANIFEST.txt`
- `deliver_S454_P4B.ps1`
