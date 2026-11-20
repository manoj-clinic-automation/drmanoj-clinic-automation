# S493 BUILD BRIEF — the Follow-up Tracker's move to the server, session 2 of 4 — 20-Nov-2026, 17:02 → 20:4x IST (the parent, Fable)

**For you, in one paragraph.** Your PC's call-list ledgers are now copied onto the server, with every path translated, and the server ran your last month again from them (Replay 2). The first run failed in a way nobody had tested before — the server's Python is older than your PC's — and once that was fixed with one line, 24 of 33 evenings differed on the call sheet by a handful of names at the bottom. Eight small kits later the cause was one line in the engine: when more than 120 patients are due, the engine fills the list oldest-first and, among patients tied on days overdue at the 120th place, it let the computer's chip decide the order. Your PC and the server have different chips, so they picked different tied patients. With your OK at 20:21 the sort now keeps a fixed order on both machines, and the server's output is now identical to your PC's, cell for cell, on all 24 evenings compared. Nothing has switched: your PC still makes and sends the list. Also built: the red line that goes red if the PC keeps sending after the switch, and a page on your console where any Docterz export can be uploaded by hand.

## What stands on the server tonight (runner still OFF)
- `/root/followup_tracker/` — your ledgers (12 files), 30 nightly snapshots since 19-Oct, 229 input reports, 145 archive files; `SEEDED_AT` stamped; the seed came through your Drive outputs folder (`TRACKER_SEED_20261120-173916.zip`, 32.6 MB, checksum verified).
- `pc_upload_watch.py` every 10 minutes + the freshness leg *clinic PC still sending after the switch* — green now (not switched yet).
- The owner page — any Docterz CSV, any period, counts back; a day already held with the same patients is left alone: `https://followup.dr-manoj.in/finance/console/docterz-reports`
- A Python 3.11 of its own at `/root/followup_tracker/venv` (your PC's library versions) — built, not yet the runner's; session 3's first kit moves the runner to it and takes the engine back to your PC's exact bytes.
- The engine on both machines: the dropout pick after a STABLE sort (your PC's `processor.py` 6929fc15 with a backup beside it; the server's b5b01d87).

## The proof
Content hashes (every cell of every sheet, the "Generated" stamp excluded) of the server's 24 compared runs = the VM's replay of your PC's data with the fixed engine, on all 24. Against your PC's OLD files 9 differ only in row order and 15 swap tied patients at the tail — exactly what the fix implies.

## Your question of 20:14 — over 120 calls
Nothing is dropped. 120 is the sheet's size; whoever does not fit waits for the next run (and is still on the Probable Dropouts tab). The cap stays; a line on your console will say "Call list today: 120 of 143 — 23 wait for tomorrow" (session 3, after the runner kit).

## Session 3 (495) — nothing of yours until you pick the evening
1. The runner to its own Python; the engine to your PC's bytes; the dry pass. 2. **The switch evening, when you name it:** after that evening's 21:xx run on the PC — the spare flag written on the PC by the assistant, the day's ledgers seeded again, then your one server line (`rm /root/followup_tracker/OFF`, given as a paste). From the next evening the server makes the list; your console says "server 63 · PC 63 · same" the morning after. Undo at any point: the flag off the PC and `touch /root/followup_tracker/OFF`.

## Numbers
D1027 · A-D101, A-D102, A-D103 · F-1520 – F-1527 (F-1526 the finding) · kits S897, S899 – S908 · session 495 reserved.
