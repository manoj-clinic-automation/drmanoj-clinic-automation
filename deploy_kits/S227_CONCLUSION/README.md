# S227_CONCLUSION — one conclusion per item, the workings folded

**Session 227 · 06-Sep-2026 · supersedes S227_PINPOINT**

## The owner's read of the live desk

"These narrations are confusing as to what is the final judgement." "I need only your conclusion, and
the decision metrics you took should be expandable and understandable." "Moved in, or out? clarify
inline." "Keyed after that day's export — purchase entry?" "A section for me and Amir to generate these
from Marg, for you — better as upload to the VPS than in chat." "The no-movement list is the first
candidate for write-off, for my eyes after Darpan and Amir confirm; narrow it to the actionable ones."

## What this kit does

**One conclusion.** `_item_life` now ends in `detector.conclusion` (one sentence), `detector.kind`
(clean / explained / lookup) and `detector.details` (the window line, then one line per export span).
Both pages open an item's life with the boxed CONCLUSION and a "Show how this was decided" button;
everything else — purchase lines, sales, Marg by export day, the span lines — sits behind it.

**IN / OUT in words.** `_qwd(units, ps)` → "60 strips OUT", "48 strips IN". Used in conclusions, lane
reasons ("40 strips OUT of Marg between 02-09-2026 and 03-09-2026 with no document on the server …
Amir looks up that span in Marg's item ledger before the shelf is blamed.") and Amir's lookup questions
("which voucher took 40 strips OUT?").

**A late bill seen twice.** ROSIKA FORTE: bill 545 of 01-09 was not yet in Marg at the 02-09 export,
so the span holding its date showed −60 strips and the next span +60. The engine now pairs the two —
same entry — and settles both in one sentence; the lane sees residue 0. Two spans that cancel with no
bill are read as an entry made and reversed (net zero). "Keyed after that day's export" now says "a
purchase entry keyed in Marg after that day's export".

**First write-off candidates.** The desk's last card lists the carried-forward, matched, unsold items
that still hold stock (Marg 0 lines are dropped), largest value first, with cost and MRP totals and a
value per row; the words say Darpan confirms shelf and expiry, Amir tries the vendor, what comes back
is the owner's list.

**Marg's answers, uploaded.** `POST /api/pad/marg_answer/<cid>` (multipart `file`, optional `item`,
`note`, ≤ 25 MB) keeps the file byte for byte in `pad_uploads/marg_answers/<cid>_<stamp>_<md5-8>_<name>`
and a row in `stock_marg_answer`; `_marg_answers` lists them; the report data carries `marg_answers`
and `marg_answer_url`. The box sits on the desk's closing card and the report's tools strip. The next
build (kit C) reads them.

## Files

| file | change |
|---|---|
| `stock_app.py` | `_qwd`; span pairing + net-zero; `conclusion`/`kind`/`details`; lane reason wording; `res_note` for paired bills; `dead_matched` cost + sort; `stock_marg_answer` table; `/api/pad/marg_answer/<cid>`; `_marg_answers` |
| `stock_desk.html` | conclusion box + Show/Hide workings; write-off-candidates card with values; upload box on the closing card |
| `stock_report.html` | conclusion box + Show/Hide workings; upload box in the tools strip |

## Proof

376 checks at 390 px — see `INSTALL.txt`.
