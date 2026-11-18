# S877_PACKS_SHEET_DOWNLOADS — the parent, S484, 18-Nov-2026

**His word of 14:49 (D1011) · F-1474 and F-1476.** On the packs page the 4.4 card-spends sheet opened a tab that closed itself
(target=_blank on an attachment — the "flashing window") and sheet 7 downloaded with no sign on the page; sheet 7 had no
layout (one bold row, no widths, text dates, bare numbers).

## What changes
1. `/root/finance/packs.html` d931f746 → TO: every xlsx link of the pack table (1 the income sheet, 2 the UPI sheet and the
   clinic bank check, 4.4 the card sheet, 7 the payment papers) is built by `dlink()` — a plain same-origin link with the
   `download` attribute, no new window — and `dlnote()` shows for nine seconds beside it: *downloading… it lands in your
   browser's Downloads folder*. PDFs and pages keep their new tab. No dialog (F-1464).
2. `/root/finance/packs.py` b1174cb0 → TO: `_s877_xlsx(sheets, spec)` writes sheet 7 and the NK Pathology sheet: widths,
   wrapped text, the title merged, the header row shaded / frozen / filtered, ₹ money with Indian grouping, real dates
   (dd-mmm-yyyy), the TOTAL row bold, landscape fit-to-width for printing. No figure changes; the other sheets are written by
   the old `_xlsx` as before.

## Proof
- `walk_s877.py` 24/24 on a made-up root (made-up payment register, no real number); the live files 7/24 (control red).
- `walk_s875.py` 34/34 · `walk_s866.py` 18/18 · `walk_s873.py` 11/11 on the new files.
- Rehearsal on a made-up root: DRY, install, again (already installed), undo, undo again, a forced red at [4/5] (files back,
  pins exact), the lock held (exit 3), a tampered kit (SUMS red), a drifted live file (stop at [2/5]), a corrupt SUMS.
- The picture of October's sheet 7 as the kit writes it: `03_WORKING_PAPERS\S484\S877_sheet7_october_page1.png`.
- Reproduced before the build in his Chrome (Claude in Chrome): 4.4 opened tab 1880556338 which closed itself and the file
  landed as "(5).xlsx"; 7 downloaded with no sign. In the built-in browser neither link downloads at all (its downloads land
  as a nameless .tmp) — the fix is for his own browser.

## Install (his publish + one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s877kit && cp -rp /root/deploy/repo/deploy_kits/S877_PACKS_SHEET_DOWNLOADS /tmp/s877kit && bash /tmp/s877kit/install_S877_PACKS_SHEET_DOWNLOADS.sh
```
Undo: `bash /tmp/s877kit/install_S877_PACKS_SHEET_DOWNLOADS.sh --undo`
