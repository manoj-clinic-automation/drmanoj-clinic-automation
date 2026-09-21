# S360_YESBANK_PDF — kit README

**Project:** Sanjeevni (session 280, 21-Sep-2026) · **Fault:** F-603 · **Touches a parent file:** yes, declared — `finance_ui/finance_workbench.html`

## What it fixes
The Yes Bank statement could not be loaded at all. The page accepted only `.csv`, so the PDF could not be chosen; the CSV the bank gives today has no *Statement Period* line, so the S186 reader refused it every time. Two cash deposits the bank holds (03-Sep and 15-Sep) never reached the books.

## What it changes
| file | from | to |
|---|---|---|
| `/root/finance/finance_yesbank.py` | `5dcbdd3a` (S186 v1.0) | v1.1, see SUMS.md5 — reads the statement PDF and proves it against its own balances and totals before storing a row; the period-less CSV is refused with a message naming the rule; the `Cheque No/Reference No` column is read; a long digit run in a file name keeps its last four digits |
| `/root/finance/finance_ui/finance_workbench.html` (**parent's, declared**) | `420f82c2` (S187) | see SUMS.md5 — PDF selectable; the card says which file; the file name masked in the browser; a refusal shown in full |
| `finance.db` | — | data repair: the one rejection flag carrying the account number from the bank's file name is cut to the last four digits (F-607); backed up first |

`clinic-finance` is restarted (declared). `finance_app.py` is **not** touched. Named to the parent: `api_yesbank_statement` logs the raw file name into `data_flag` / `audit_log`; the page now masks it before sending, but the route should mask it too (one line: `fname = finance_yesbank.mask_name(fname)`).

## Proof
- `selftest_s360.py` — the S186 selftest unchanged, the PDF reader on a FAKE laid-out statement with eight deliberate failures (no period, no closing, a broken balance, a missing row, a deposit in the wrong column, totals off, a row outside the period, a row with no balance), the period-less CSV refused by name, and a real PDF generated in pure Python read through `pdftotext`. RED against the S186 module.
- `walk_s360.py` — the live app's own upload route, with the new reader and page, on a scratch copy of `finance.db`. On the PC against the owner's real statement (never in this kit): period 01-Aug to 20-Sep, 7 rows, 2 cash deposits ₹4,00,000, *in the bank but not booked*: 03-Sep ₹3,00,000 and 15-Sep ₹1,00,000. RED with the S186 module placed.
- Installer rehearsed on a fake root: install · rerun ALREADY · wrong live bytes refused · forced red restores byte-identically.

## The line
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S360_YESBANK_PDF/install_S360_YESBANK_PDF.sh
```
No real statement, account number or bank reference is in this folder.
