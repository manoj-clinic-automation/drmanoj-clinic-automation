# S226_STOCK_CLOSE — numbered flow, named sheets, Close the stock check

**The owner, 06-Sep-2026, on seeing the on-page panel:** the four details must be entered on the
page and auto-fill the sheets; subsequent sheets named in a staff-friendly way; a final *Close
stock check* button that closes the whole session with "stock check completed" and entertains no
further Excel loops — appearing only after the VPS verifies the work, before that a prompt "some
stock count left, download the sheet and complete it"; STAFF FRIENDLY ALWAYS; and if a count is
left incomplete or abandoned, the owner has the power to close it so analytics and follow-up run.

## What changed
| file | what |
|---|---|
| `stock_check_live.html` | The gate is a numbered flow: **1** the four details · **2** *Download SHEET 1* (note echoes what will be written in) · **3** *Upload the filled sheet* (processing box) · **4** the result box, under the step that explains it: "Some stock count is left … download the sheet and complete it" → *Download SHEET N REMAINING*; or "The server has checked: everything is counted" → **Close the stock check** → confirm → alert + green box **STOCK CHECK COMPLETED**, *Download the FINAL RESULT sheet*, "no more sheets … start again at step 1". The checker alone (`DATA.checker`) sees *Doctor: close count #N as it stands* on an open count with work left. **Recent stock checks** shows OPEN / everything counted, not yet closed / CLOSED, with the right sheet link; it never repeats a button for the count the box is showing. |
| `stock_app.py` | `stock_count_close(count_id, closed_at, closed_by, how complete/incomplete, left_not_counted, left_to_fix)` · `POST /api/pad/close/<cid>`: anyone who counts may close a count the server finds complete; with work left only the checker (`_may_decide`) may, and it is recorded *incomplete* with what was left · `/api/pad/upload` refuses a sheet whose PART OF COUNT is closed, in words, recording nothing · sheet names: `STOCK_COUNT_<day>_SHEET_1.xlsx`, `…_SHEET_<n>_REMAINING.xlsx`, `…_RESULT_TO_CLOSE.xlsx`, `…_FINAL_RESULT.xlsx` (day = the day the count started) · `page_count` passes `checker` and `user` to the page · brief/recent carry `closed` and `sheet_name`. |
| `padwriter.py` | SUMMARY gains a **Status** line: OPEN with what is left / OPEN everything counted, press Close / CLOSED — stock check completed on … / CLOSED by the doctor as it stood on …, with what was left. |

## Decisions
- A closed count is closed: no sheet joins it, however it arrives. A fresh SHEET 1 always starts a new count.
- "Close as it stands" is the checker's only; the server enforces it, not the page (a counter posting to the endpoint is refused: "Only the doctor can close a count with work left").
- The result box is the single place for actions; the list repeats none for the count on show.
- Not rebuilt: the native date box shows the phone's locale (browser behaviour); the note under step 2 restates the date as dd-mm-yyyy.

## Proof
169 checks in a real browser at 390px (92 + 34 + 30 + 13); LibreOffice opens the FINAL RESULT workbook. Sub-agent screen read: numbered flow clear, states unmistakable, override visibly secondary; its three findings (duplicate buttons, box above its step, bare "differ") fixed before packaging.
padreader.py f617d7d5 is here ONLY so the walk can import it; it is unchanged and NOT installed by this kit.
