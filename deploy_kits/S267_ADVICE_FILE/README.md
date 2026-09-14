# S267_ADVICE_FILE — the workbook the bank is emailed

The advice is printed on A4 **and emailed to the bank** from the account linked
to it. So it has to exist as a file — and as **the bank's own workbook**, not a
lookalike. This generates it from the same rows the page shows.

Held to the files already sent, April–July 2026:

| | |
|---|---|
| sheet name | `Sheet2`, as every file since April is |
| letterhead | the same four lines, merged `A1:C1`, `A3:G3`, `A4:G4` |
| headers | the same seven, the first two keeping their leading newline |
| account numbers | written as **text**, so `088851000012` keeps its leading zero |
| amounts | whole numbers, General format, **no separators** |
| total | a real `=SUM()` **with its value cached**, so it shows without recalculating |
| page | the same column widths and row heights, A4 landscape, fit to page |
| filename | `NEFT ADVICE AUGUST 2026.xlsx` — the name these files have always had |

## Written with the standard library alone

A `.xlsx` is a zip of XML, and this builds it directly — `zipfile` and string
formatting, nothing else. **No openpyxl, no xlsxwriter**: nothing to install on
the box, and nothing that can be missing on the one evening of the month it is
needed. The six parts a workbook needs are written by hand and the walk opens the
result to prove they are all there and intact.

## The walk — 54 checks, and it opens the file

The workbook is generated, unzipped and its sheet XML parsed with the standard
library. Nothing is assumed:

- **the before-state is proved**: the address 404'd, there was no file at all;
- it downloads, is sent as a spreadsheet **as an attachment**, and is **named the
  way these files are named**;
- it **opens as a workbook with every part intact**, and all six parts are present;
- the sheet is named `Sheet2`; the four letterhead lines are there; the merges are
  `A1:C1`, `A3:G3`, `A4:G4`;
- the seven headers are the bank's, in its order and wording; the column widths are
  the bank's own; the page is A4 landscape, fit to page;
- one row per advice line from row 6, and **the row after the last line is the
  total row and nothing more**;
- **every account number is text** and equals the register's; **every amount is a
  number** and equals the sheet's payable; every name and IFSC is the one on the
  account row; every line says `NEFT` and `Vendor Payment`;
- the total is a **real `=SUM()` over its own lines** and **its cached value equals
  the advice's total**;
- **no cheque vendor is anywhere in the file**, and nobody without a confirmed
  account is either;
- the card offers the download and still offers the print, and neither button prints;
- `/hub`, `/scans`, `/orders`, `/book` and the purchase audit are **byte-identical**,
  and so are the advice table and the covering letter on the page.

It was also opened for real: converted by LibreOffice and read back — grid, bold
headers, 18 lines, total 353410, no errors, nothing truncated.

Fixture root: clean install, **ALREADY INSTALLED** on re-run, database untouched.

## Install — one line on the VPS

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S267_ADVICE_FILE/install_S267_ADVICE_FILE.sh
```

| pin | from | to |
|---|---|---|
| `/root/finance/purchase_app.py` | `30f6c28697eabab5beae609fa7965389` | `34628cd8de65a5fbd4440cd7f96b0f70` |

## What this closes

The month now runs end to end inside the system: the sheet is prepared, verified
against Marg's own supplier-wise statement, locked — and then the advice, the
covering letter and the attachment all come off that one sheet. Nothing is typed
twice and nothing is maintained by hand.

## Files

| file | what it is |
|---|---|
| `block.py` | the workbook writer, the filename rule, and the route |
| `patch_advice_file_s267.py` | two anchored edits and the append |
| `walk_s267.py` | the 54 checks — it opens the file and reads it back |
| `install_S267_ADVICE_FILE.sh` | pins, backup, patch, walk, restart, roll back |
