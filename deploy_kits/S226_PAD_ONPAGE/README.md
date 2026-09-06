# S226_PAD_ONPAGE — the Excel count, on the stock-check page

**The owner, 06-Sep-2026, after the first live count:** "Instead of creating a separate page
for the Excel part, make it a part of the stock check page, and it should start with the
details filled there itself … so that the Excel which then comes down is prefilled with all
this data and staff only have to enter the stocks. After that, the upload should be staff
friendly and a processing box should be visible. And then a prompt to download Excel for
remaining work. And this loop should go on so that staff don't have to seek me for this work."

## What changed

| file | what |
|---|---|
| `stock_check_live.html` | The gate keeps its four boxes (who counted, who is entering, bill, date). Under them, **Count on the Excel pad**: *Download the Excel pad* (shut until the four are given; the note says what will be written in) · *Upload the filled pad* (one tap: pick the file → processing box → result box) · the result box: `Recorded as count #N`, this sheet's numbers, the whole count so far, **Still to do: N not counted, M to fix**, and the big *Download the sheet for the remaining work* link, with what to do with it · **Recent counts**, each with its result sheet · the on-screen count is the second choice, *Count on this screen instead*, unchanged behind it. |
| `stock_app.py` | `/pad.xlsx?cby&eby&bill&bdate` writes the four into the pad's top lines · **`/api/pad/upload`** — ONE call: read, record what can be used, keep what cannot, answer with the family's state and the result link. Details come from the sheet's own top lines, then the page's boxes; if neither has them it answers `need_details` and the page asks, recording nothing · `stock_count_pad_file` remembers each sheet's md5 with its count: **the same file twice is the same count** · `/api/pad/recent` — the last eight root counts with their state · `_pad_family()` is the one reader behind the workbook, the upload's reply and the recent list · `/page/pad` redirects to `/page/count`. `preview`/`commit` remain for the checker's console. |
| `padwriter.py` | `fresh_pad(..., meta=)` → B5 counted by, B6 entered by, B7 bill no, E7 bill date (dd-mm-yyyy), all shaded (a person may correct them). |
| `padreader.py` | `read_meta()` — the value to the right of DATE / COUNTED BY / ENTERED BY / BILL NO / BILL DATE on any sheet; `iso_date()` accepts dd-mm-yyyy, dd/mm/yy, ISO, an Excel serial. **And the `SHEET ROW` (`ref`) column is read again** — see below. |

## A defect this kit also closes — the live padreader had no `ref`

The S226_PAD_IMPORT kit shipped `padreader.py` **dd32617b**, which does not read the
`SHEET ROW` column, while the walk that proved that kit ran against the later copy
(**38637a94**) that does. On the live server a row corrected on SENT BACK TO FIX with a
*changed name* could never be marked resolved, so it would be asked for again on every
result sheet. This kit's reader (f617d7d5) carries `ref`, and the walk here checks the
closure by original row (`left == [("CIXCEF O",)]`). Lesson recorded: **the walk must import
the file the kit ships, from the kit folder** — the walk here does (`sys.path.insert(0, HERE)`).

## Decisions
- Sheet's top lines win over the page's boxes; a follow-up takes the root count's bill. A
  pad with blank top lines (the one Amir already holds) and empty boxes is not recorded — the
  page asks for the four and re-sends the same file on one tap.
- The result link is always the family's (root) sheet.
- The native date box shows the phone's own locale; the note under the download button restates
  the date as dd-mm-yyyy. Not rebuilt — it is the live gate.

## Proof
141 checks in a real browser at 390px; LibreOffice opens and recalculates the prefilled pad and
a result workbook. See `EVIDENCE_*.txt`. Screens read by a sub-agent: no overflow, order as
intended, download links stand out; one wording nit fixed ("row(s)").
