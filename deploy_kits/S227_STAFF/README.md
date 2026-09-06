# S227_STAFF — Amir's board, Darpan's lists in turns, consumables, orthotics families

**Session 227 · 06-Sep-2026 · kit B · supersedes S227_CONCLUSION**

## What the owner read on the first live lists, and what this kit does about it

**"Multiple entries for the same item — correct it."** The lookup list had TYRO BR twice: 74 strips 3 tabs
OUT (27-08→02-09) then 34 strips 3 tabs IN (02-09→03-09). That is one move seen twice: Marg's export is
taken in the middle of a day and a bill keyed after it shows as "missing" in one span and "found" in the
next. The detector now MERGES neighbouring spans whose residues have opposite signs until none is left,
then pinpoints on the merged span (TYRO: 40 strips OUT between 27-08 and 03-09 — one question). A few
tabs at a boundary, or a residue whose sign is against the window's net, are noise and say so. One row per
item on Amir's lookup list; the ROSIKA case (−60/+60) now simply reads "Marg and the documents agree".

**"Blade, gloves, fibre casts are never billed to patients."** `_is_consumable` (word list + the setting
`stock.consumable_words`) → the CONSUMABLES lane: a shortfall is consumption; the desk card's one button
is "Write off all as used"; Amir's board lists them as a consumption voucher. A surplus is a correction.

**"Orthotics — same item, different company, bought one, sold another."** `_ortho_family` strips brand and
filler words (TYNOR, UNISON, HOSPIK, ADJ, ELAS …) and keeps the size. Every orthotic in the shop
(differing, matched, uncounted) is grouped; the family's net decides: net 0 with movement = a brand swap
(Amir corrects Marg, nothing lost); part swap; short = fitted and not keyed or missing; over = an unentered
purchase. The ORTHOTICS lane, a desk card with the family verdict on each line, `ortho_families` in the
report data, the ORTHOTICS CLEANUP workbook (`/api/pad/ortho/<cid>.xlsx`), and box 5 of Amir's board.
The old "dead E" kind is folded into this lane.

**"Darpan: 5 highest-value + 5 routine at a time, quantities only, no rates; orthotics separate."**
`stock_tranche`; `POST /api/pad/tranche/<cid>/next {kind: med|ortho}` cuts the next list from the open
lines not yet given (top 5 by value, then 5 with the smallest gaps; consumables never; orthotics only on the
ortho list); refuses while a list is out; `/<tid>.pdf` (`pad_receipt.render_tranche`) prints the sheet
without a rupee on it; `/<tid>/returned`; `POST /api/pad/answers/<cid>` is the typing board (reason number
or key + note → `stock_diff_answer`, the S221 layer).

**"All uploads and downloads on the staff page meant for it — I could not find the upload button."**
`stock_amir.html` at `/page/amir?count=N` (`/api/pad/amir/<cid>` = `_amir_board`): 1 Marg's owed reports +
the upload box · 2 vouchers to post (issue / consumption / corrections) · 3 Darpan's lists + the typing
board · 4 files · 5 orthotics by family. Hindi subtitle lines. Linked from the count page (`dl report`),
the desk foot (first link) and the report's tools strip. The desk foot carries the upload box from card 1.

**"The audit should show only what needs Amir, with the exact reason."** The workbook now carries only
FREE TOO HIGH and PACKING DIFFERS (a purchase line's packing against the stock item's), each with the exact
thing to do; double entries and loose-column arithmetic are the server's business and stay in the JSON.

**"Explain this over to me … 2 items over, check with exact salts."** The desk's numbers strip says
"over = more on the shelf than Marg"; the over card's text names every identical-salt pair (D385) so the
surplus can be read against its shortage.

## Files

| file | change |
|---|---|
| `stock_app.py` | word lists; `_is_consumable`, `_is_orthotic`, `_ortho_family`; families in `_pad_report_data`; consume/ortho lanes; span merging + noise; one lookup row per item; `stock_tranche` + tranche routes; `/api/pad/answers`; `_amir_board` + `/api/pad/amir/<cid>`; `/page/amir`; `/api/pad/ortho/<cid>.xlsx`; audit `packing_conflicts`/`needs_amir`, actionable workbook; links `ortho`, `amir_page`; brief `amir` |
| `stock_amir.html` | NEW — Amir's board |
| `stock_desk.html` | consumables + orthotics cards, family verdict per line, over explained + pairs, upload box in the foot, Amir link |
| `stock_report.html` | Amir's board + orthotics links |
| `stock_check_live.html` | Amir's board link in the box and the small line |
| `pad_receipt.py` | `render_tranche` (`_TDoc`) — no rates |

## Proof

402 checks at 390 px — `INSTALL.txt` lists them; `WALK_staff_s227.py` is the new walk.
