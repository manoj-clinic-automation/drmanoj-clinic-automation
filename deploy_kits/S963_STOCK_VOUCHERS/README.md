# S963_STOCK_VOUCHERS — Marg's stock vouchers read from its own two period reports (built at Sanjeevni session 530, 26-Nov-2026)

**What he asked (D1083, D1084):** stock vouchers and unexplained stock moves flagged on the Stock check and the item ledger, with Marg's
voucher number and date; the vouchers read from Marg's **Stock Issue** and **Stock Receive** reports for a period he chooses, not from
one-item Stock Registers. His **"proceed"** of 16:16 IST on mock-up v4 (`https://claude.ai/artifact/W3U9BfeW9K5QKpsgZ6YoqF`), with his
word that a voucher's lines open inline, collapsed and expandable. **This kit is the reading half**: the two reports reach the server and
are kept, name-free. The judging and the two screens are the next kit (S964), built on what this one stores.

**How he takes the reports (unchanged):** Marg (medical PC) › Transactions › Stock Issue (or Stock Receive) › Modify › Alt+P › Report ›
Detail+Items › the period › text. They land as `C:\Users\Public\MARG\17476\report.txt`; the watcher picks them up as it does every report.

## The medical PC — `D:\SendToClinic\marg_txt.py` S679 aa7baee5 → S963 `5e9d00fb`
A fourth kind, **VOUCHER**, read by its own reader (`voucher_rows`) into a thirteen-column sheet: per voucher its day, number, **"cash" or
"party" — the party's name is never written** (two issue vouchers carry a person's name), gross amount and bill value; per item line the
name, packing, batch, quantity as printed, unit, expiry, rate, value and the units it makes. Every line proved by Marg's own arithmetic:
rate × the paid units ÷ the pack = the value; where Marg takes the tax out of a line's value (seen on one voucher), Marg's own `( N )`
total under the line settles it, and a line with neither is refused. A plain quantity is packs or loose as the money proves it (CCM 1*40
"3" = 3 packs = 120). Marg cuts a name at 15, 20 or 24 letters: the split that leaves a real packing after one space — and no packing left
standing in the batch — one way only, else refused. Every voucher's lines = its gross; the vouchers = the TOTAL. Selftest 118/118 (the
95 earlier checks unchanged, 23 new). **On the two real exports of 26-Nov** (in the device VM only): issue 37 vouchers, 181 lines,
108,064.41 / 106,678.00; receive 16 vouchers, 73 lines, 38,535.38 / 38,955.00 — Marg's TOTALs to the paisa; no party name in the sheet
or the .XLS. The watcher re-reads `marg_txt.py` when it changes and retries the texts it held (S556), so the two held exports flow.

## The server — rebuilt here from the live bytes (`make_s963.py`), checked against `TO_PINS.md5`
| file | from | to |
|---|---|---|
| `/root/marg_ingest/signatures.json` | 50ca61f4 | 19eb5f91 (STOCK_VOUCHERS ISSUE / RECEIVE) |
| `/root/marg_ingest/marg_take.py` | bc621caf | 3aa1208b (one hook, the upload door) |
| `/root/marg_ingest/marg_ingest.py` | b11099ff | 09cd260a (one hook + the re-read of a failed store, the five-minute collection) |
| `/root/marg_ingest/marg_vouchers.py` | NEW | 7bc3df84 |

`marg_vouchers.py` re-proves the sheet (the PC is not trusted): units a reading of the quantity, lines = gross, vouchers = TOTAL, every
day inside the title's period, **the party cell "cash" or "party" — anything else keeps nothing**. Kept in finance.db: `mi_voucher_file`,
`mi_voucher`, `mi_voucher_line`; the views `mi_voucher_now` / `mi_voucher_line_now` show, per kind and day, the newest sound sheet
covering that day — **a later report of the same days replaces them, never doubles** (a voucher deleted or edited in Marg goes or changes).
"Newest" is the order of first storing (a running number: the door's clock reads only to the second — the walk caught two reports in one
second tying). The sheet is name-free, so the door keeps the file.

**Proof:** `walk_s963.py` 11/11 on made-up reports (a scratch database; the door's lock pointed at a scratch file) — the router, `take()`,
the same bytes again (ALREADY), a receive apart, a name in the party cell keeps nothing, a later report replacing, the collection's hook;
**the control on the live files red (0/11)**; the router's own selftest unchanged. Chain on the two real reports (name-free copy): both
VERIFIED, 181 + 73 lines; AXIMAL 200 = L000008, 15-10, 286 — the figure Marg's one-item Stock Register gave independently (S526).
`rehearse_s963.sh` 12/12 on a made-up root: dry · red at [4/6] · red at [5/6] · install · backups · again · undo · install again · wrong
FROM · the lock · a corrupt kit.

**Install:** his publish, then one server line (in the installer's head). Placed under the collector's own lock (`/tmp/marg_ingest.lock`),
so no report lands half-way; clinic-finance restarted (the upload door lives in it). **Then the medical PC** — the chat, through the file
tools: Drive `ToMedical\_kit\marg_txt.py` (the FROM read first; `marg_txt_S679.py.superseded` kept beside) and the manifest's
`marg_txt.py` line → 5e9d00fb; the agent installs at its next kit check. **Undo:** `bash /root/deploy/repo/deploy_kits/S963_STOCK_VOUCHERS/undo_s963.sh`
(the three backups back, the new reader gone, clinic-finance restarted; the tables stay, nothing reads them). Medical PC: the superseded
copy back as `_kit\marg_txt.py`, the manifest line back to aa7baee5.

**Reviews.** Cold review (a separate agent): **NOT SAFE** — **M1**: an unknown packing word (1X10, PAIR) let a false 15/20-letter
split through (a wrong name and units stored as sound). Built in: the batch must stand in its own column (10 after the packing's first
letter; 11 at the 24-letter cut — measured on 205 of 205 real lines), carry a digit, hold no packing; one name width per voucher (no real
voucher mixes); the reviewer's own attack lines now all refused. SHOULDs built in: **S1** a sheet the server will not keep (a name in
the party cell, a bad cell) is not kept as a file either; **S2** every cell held to its column's shape (a name in the batch, fractional
units, a filled cell on a voucher row: not read); **S3** the newest EXPORT wins (the file's own stamp), not the latest arrival; **S4** a
packs-and-loose quantity needs Marg's ( N ) under it (170 of 170 real ones have it); **S5** the undo refuses when a later kit changed a
file, takes the build lock, checks finance after the restart; **S6** a red after placing puts files back under the collector's lock, by
rename; **S7** a store that fails half-way leaves nothing (a savepoint) and no row, and the five-minute collection reads it again from
the archive (heal). Both real reports read exactly as before the fixes (254 lines, identical).

**Second look** (a separate agent, on the fixed kit): **SAFE TO INSTALL**, no MUST; M1 proved fixed by 200,000 fuzzed Marg-shaped lines
(0 wrong readings, 0 wrong refusals); the savepoint proved safe inside both callers. Its four SHOULDs built in: the re-read (heal) of a
sheet it finds not read deletes the file and marks it not kept, as the door does; an upload with no export time in its name ranks below
every stamped export (a stale hand upload never wins); a missing or changed archive file is marked, so it never blocks the sheets behind
it; the batch needs no digit and no packing test (the column rule alone decides -- a batch NA or TYNOR is read, not refused). The
server's shape checks are a backstop; the medical PC is the guard against a name. Both real reports still identical (254 lines).

**First server run, 17:00 IST 26-Nov — stopped itself at [3/6], nothing installed:** the walk's scratch layout copied only the loose files
of `/root/marg_ingest`, not the collector's own vendored `xlrd/` folder, and the box's venv has no `xlrd` of its own -> the walk could
not open any .xls (2/11). A walk fault, not the door's: the live collector imports `xlrd` from beside itself. Fixed: the layout copies
`xlrd/`; [1/6] now proves the venv imports `xlrd` from beside `/root/marg_ingest` before anything else. Rehearsal 12/12 with a Python
that has no `xlrd` of its own (as on the box); without the vendored folder it refuses at [1/6].
