# S227_PAD_PROOF — the sheet is kept, and a receipt says what was ingested

**The owner, 06-Sep-2026:** save the uploaded Excel sheets by the stock checkers, give them a PDF
printout to save as proof of what the VPS ingested, and preserve the uploaded sheets for any
dispute resolution during the reconciliation of the stock mismatch.

**What was found:** until this kit the server kept a sheet's md5, name and size in
`stock_count_pad_file` — and threw the bytes away.

## What changed
| file | what |
|---|---|
| `stock_app.py` | `_pad_read` split into `_pad_raw` (bytes, md5, size) + `_pad_parse`, so the bytes are in hand before anything is read. `_pad_keep()` writes every upload that reaches the server to `pad_uploads/<md5>.xlsx` beside finance.db — once, `.part` then rename, fsync, read back and md5-verified — and records it in the new table `stock_count_pad_archive` (md5 · path · filename · bytes · first/last seen · times · outcome · count_id · verified) plus a line in `pad_uploads/INDEX.txt`. Kept whatever the outcome: recorded · repeat · held-need_details · refused-unreadable / -empty / -no_root / -closed / -server. A recorded sheet's standing never regresses. `_pad_receipt_data()` builds the receipt from the sealed rows; `_pad_receipt_store()` writes a frozen copy `<md5[:8]>_count<N>_STOCK_COUNT_<day>_SHEET_<n>_PROOF.pdf` the moment a sheet is recorded. New routes: `GET /api/pad/receipt/<cid>.pdf` (checker/maker/viewer, inline) · `GET /api/pad/file/<md5>.xlsx` · `GET /api/pad/archive` · `GET /api/pad/archive.zip` (checker only). `_pad_brief` carries `sheets` (one per sheet of the family, each with its receipt); the upload reply carries `receipt`, `md5`, `kept`. Recording never waits on the archive: a disk refusal leaves the count recorded and says `kept=false`. |
| `pad_receipt.py` | **NEW.** Stdlib PDF (the S224 writer): title block · recorded at (IST), uploaded by, counted by, entered by, bill, Marg as-on · the file (name, size, md5, KEPT — verified) · what this sheet did · the whole count after it (and CLOSED when it is) · DIFFERENCES FROM THIS SHEET · ROWS SENT BACK TO FIX (as written, why) · EVERY ITEM RECORDED FROM THIS SHEET (Marg, counted, strips, loose, diff) · a plain foot note. Running header and page x of y; foot with the full md5 and the time in IST. |
| `stock_check_live.html` | After a recorded (or repeated) upload, under the numbers: an outlined **Download the PROOF of this sheet (PDF) — save it or print it** link and one grey line (the file is kept on the server, unchanged; fingerprint). After a close: the FINAL RESULT sheet then *Proof of each sheet (PDF): sheet 1 · sheet 2 …*. The same proofs line under every count in Recent stock checks. The checker alone sees *Doctor: download every uploaded sheet (zip) · list* under the list. Theme tokens only, both schemes. |

## Decisions
- Content-addressed store (`<md5>.xlsx`), one file per distinct upload however often it arrives; the ledger row is the file's standing, INDEX.txt is the event log.
- The receipt is per SHEET (per count id), made from sealed rows — the one made today and the one made in a month are the same document, bar the whole-count lines at the foot which say where the count stands now.
- The originals and the zip are the checker's; the receipt is everyone's who may count. A dispute is the doctor's to settle, and the counter already holds the file.
- `pad_uploads/` lives beside the db it belongs to, found through `PRAGMA database_list` — never a hard-coded mount (S212).
- Not done here: the nightly `finance_backup.sh` does not yet tar `pad_uploads/`; the zip route is the off-box copy until it does (OWNER_TODO / Runbook).

## Proof
142 checks in a real browser at 390px: 65 (this kit's walk, the receipt read back with pdftotext and every figure compared to the sheet; bytes on disk compared to the upload) + 34 + 30 + 13 regressions unchanged. Sub-agent screen read of the receipt and the boxes: one clipped footer found and fixed before packaging.
`padreader.py` f617d7d5 and `padwriter.py` 77c43e47 are here ONLY so the walk can import them; unchanged and NOT installed by this kit.
