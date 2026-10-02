# S446 medical part -- the text reader learns Marg's `***` (F-674) -- Sanjeevni, 02-Oct-2026

At 22:10 IST on 30-Sep the bill-wise sale text was refused by `marg_txt` at line 52:
`4 *** FINGER EXTENSION SPL 1*1  1  180.00` (bill A003920). The 01-Oct 12:55 re-export was refused the same way.
The file is whole: 24 bills, GRAND TOTAL net Rs 23,598.00.

## What changed: `marg_txt.py` only

**Which column.** The reader's own item rule is `RE_ITEM = ^\s{6,}\d+\s+\d+\s`, and its comment reads `seq code NAME<20> PACK`.
An item line has two numbers before the medicine name:
- the bill's own line number (1, 2, ... 13), right-aligned to the 13th character;
- then a three-character number column (characters 15-17), and the name from the 19th character.

Marg prints `***` in that **second** column: the "col2" the server's `marg_report` carries raw (D188).

The figure in that column is as of the moment of export. The 30-Sep and 01-Oct exports of the same sale differ there on 33 item lines and nowhere else. So `***` is Marg's overflow mark for a figure that does not fit three characters.

**The edit.** `make_marg_txt_s446.py` makes 5 anchored edits to the live bytes. Each anchor occurs exactly once, or the patcher stops.
- `RE_ITEM_STARS = ^\s{6,}\d+ \*\*\* \S`: the stars must fill that column exactly, right after the line number, one space on each side, with a name after them.
- The item branch takes such a line. Everything after the branch is unchanged.
- `VERSION` S397 -> S446.
- A docstring note.
- 5 selftest checks.

The line is read with that column empty (no figure is taken from it). Its cells are exactly what Marg prints, `4 *** FINGER EXTENSION SPL 1*1`, which is what Marg's own Excel export carries. Two server readers already handle that form:
- the spine reader `marg_read` (S331) reads col2 as `(\d+|\*+)`;
- `marg_spine.clean_raw` strips `N *** ` from Excel sale lines.

Blanking the stars would break that spine regex, so they are kept.

**Still refused, as before:**
- `***` in the line number, the quantity, the amount, a bill's money or a total;
- `**` or `****` in the column;
- stars run into the name.

The batch/expiry tail was free text before and is unchanged. Bill sums, DAY and GRAND totals and line kinds are untouched. The server's readers check those, and they pass.

## md5 FROM -> TO
| file | FROM (live, medical PC) | TO |
|---|---|---|
| `marg_txt.py` | `38d85298f1627ab22b59c9f3459d8764` (S397) | `70f920c445ec82fc8c1e069f1f758efb` (S446) |
| `KIT_MANIFEST.txt` | `8230562e3dc08d5b07b458198086c68d` | `bdd277686cb76f944d4569e666a9d89f`: only the marg_txt line's md5, plus one `# S446 (F-674)` comment above it |
| `marg_watch.py` | `81145aa7d7c8e9f7e23072cfab1ee620` (S397) | **unchanged, not delivered** (see "The refusal note") |

## Delivery order (Drive `ToMedical\_kit`, md5-gated, as S397)
1. Deliver `marg_txt.py` and `KIT_MANIFEST.txt` together. The agent installs `marg_txt.py` only when its md5 matches the manifest.
   - The running watcher re-reads `marg_txt.py` when it changes (S390), so new exports are read by S446 at once.
2. Confirm in `FromMedical\heartbeat.txt` that it shows `marg_txt.py up to date (70f920c4)`.
3. Deliver any `marg_watch.py` only after that. There is none in this kit. A watcher restarted before the reader arrives would refuse the file again, and would not retry until its next start.

**The 30-Sep sale does not arrive by itself.** Delivering the reader alone does not bring it in:
- `marg_watch` S397 offers refused texts to the reader again only **at its start** (`retry_refused`, called once in `watch()`), and only those under 3 days old (`CENSUS_DAYS`).
- The watcher last started 29-Sep 12:13:14 IST (`marg_watch_log.txt`).
- The agent restarts it only when `marg_watch.py` changes.

The windows close at these times, taken from the stamps in the refused files' names:
- the 30-Sep copies: about 03-Oct 22:10 IST;
- the 01-Oct re-export: about 04-Oct 12:55 IST.

If the watcher restarts in time (a PC restart, or any `marg_watch.py` delivery after step 2), the proof shows it takes **two** `.XLS` files of the same sale:
- 30-Sep `7818a331` (its 22:10:33 twin is the same bytes, so it is not taken twice);
- 01-Oct `72bfdba1` (other bytes, because the col2 figures differ).

An Excel `REPORT_2.XLS` captured at 01-Oct 12:56:31 was also taken as SALE_BILLWISE VERIFIED. It is very likely the owner's Excel re-export of 30-Sep, though its date is in the server's `mi_file`, not here. So the server must keep one copy of the 30-Sep sale. That work is on the server side, not here.

## The refusal note (READ and REPORT; nothing built)
The route:
- `marg_push.py` (566e189e) POSTs each spool file to `https://followup.dr-manoj.in/finance/api/marg-file`;
- header `X-Finance-Marg` = `D:\SendToClinic\token.txt` (the server's `FINANCE_MARG_TOKEN`);
- multipart fields `name`, `md5`, `source=push`, `f`.

It sends only `.xls/.xlsx/.pdf` from the spool. `marg_door.api_marg_file` (598ba2df) calls `marg_take.take()`.

`take()` refuses anything that is not `.xls/.xlsx/.pdf` with the matching magic bytes. It does this **before** it opens the database. So a note sent as text gets an HTTP 400 REFUSED and leaves **no `mi_file` row and no log line**. The server's Drive collector (`marg_ingest`) also lists only `.xls/.xlsx`.

The only way through unchanged would be to disguise the note as a spreadsheet. That would break the door's own rule ("refuses before it trusts"). It would also travel every route of the spool: manojz, Drive and the server's quarantine and rescan. And the server would record the router's reason, not the PC's line and reason.

So the note needs a server-side change (a note branch in `marg_door`/`marg_take`). That counts as a new door. Per the brief, the reader fix is delivered alone and `marg_watch.py` is left untouched.

## Proof -- `PROVE_S446_RESULT.txt`, GREEN 59/59 (`python -B prove_s446.py`)
- **Negative control:** the OLD reader refuses all three copies (30-Sep `1a0ec847` and `956234ff`, 01-Oct `f87d791b`) at line 52.
- **The 30-Sep sale converts with the NEW reader.** The converted `.XLS` is `7818a331`, read by the server's own readers (copies):
  - the reader's own rows: 24 bills (A003914 ... CN00230), GRAND TOTAL net 23,598.00, footer "Bills: 24", the bills' NET summing to 23,598.00;
  - finance `marg_report` (S444 copy f9370dde): clean, with every DAY TOTAL = its bills, GRAND = the days, footer = bills read; 24 bills, 134 item lines, net 2,359,800 paise;
  - router (S302): SALE_BILLWISE/DETAIL;
  - `marg_ingest.sale_lines`: 134 lines, including A003920's Rs 180.00 line;
  - spine `marg_read` (S331): every check passing, 0 anomalies, the `***` line read as seq 4, pack 1*1.
- **The 01-Oct re-export:** 24 bills, Rs 23,598.00. It is identical except the col2 figures on 33 item lines.
- **Parity, OLD and NEW side by side:** every other text there is gives the same verdict, the same reason, and the same `.XLS` bytes where it converts (15 files). That covers:
  - all of `FromMedical\refused_text`;
  - the selftest samples;
  - the S397 proof's own 24-Sep stock text, which gives exactly `451c3d57...` as PROVE_S397 recorded;
  - the three sale copies with a figure in place of `***`, where OLD and NEW give the same bytes.

  Line by line, the new rule fires only on the three line-52s.
- **Crafted refusals:** NEW refuses each of these (10 cases, plus a file cut short):
  - `***` in the quantity, the amount or the line number;
  - `**` or `****` in the column, or the stars run into the name;
  - `***` in a bill's CASH or NET, in the DAY TOTAL, or in the GRAND TOTAL.
- **The medical PC's own path:** the live `marg_watch` S397 with each reader beside it, at start:
  - with the OLD reader, 0 taken;
  - with the NEW reader, the 30-Sep sale is taken as `7818a331`, plus the 01-Oct `72bfdba1`;
  - the watcher's own selftest is 31/31 with the new reader.
- Python 3.8 grammar check passes, and the new reader's selftest is 24/24.

**Not available for parity:** the S389/S390 parity texts (22-Sep `abb7271f`, 23-Sep and 24-Sep sale texts) were on the cloud build box. They are not on this PC or in Drive (searched H:\My Drive, this repository, and the Desktop/Documents/Downloads folders).

Their place is taken by the logic of the change and by the line-by-line check. The change only adds an `or` to the item branch. A line it newly admits went, under the OLD reader, to "a line of a kind this reader does not know" and was refused. So any file the OLD reader converts converts to the same bytes with the NEW one.
