# S227_FINDING_REPORT — the count as a document, and the life of every item that differs

**The owner, 06-Sep-2026:** an analytics layer for today's stock-check report — match it against everything accumulated (purchases, sales, sale returns), flag any sudden or unexplained stock movement, and wherever the difference is major an inline expandable section of all the purchase details of that item this financial year — vendor, date, bill number, item name, quantity — for a swift reconciliation inside Marg by the Marg operators. Built to `S226_FINDING_REPORT_SPEC` (his S226 dictation), order 1-3.

## What changed
| file | what |
|---|---|
| `stock_app.py` | `_fy_start()`, `_dmy_to_iso()`, `_sale_units()`. **`_item_life(con, item, ps, since, upto)`**: purchase lines matched on the shop's own norm (`_pad_norm`, so a trailing dot or spacing on the bill still matches; the spellings met are listed), vendor from `purchase_bill`, units = (qty + free) × pack + loose, a purchase RETURN negative; sales and returns by the sale lines (`_sale_key`, `qty_raw` strips:loose); Marg's figure on every export day in the window plus the last before it; **the detector**: between the first and last export day, Marg's move against purchases − sales + returns, the residue named as "units moved with NO document behind them". `_pad_major()`: Rs 1,000+ at MRP (at cost when no MRP), else two strips / twenty units. **`_pad_report_data()`**: the family's head, frozen readiness lines, each part's seal checked now, KPIs, mismatch, differences (newest per item, largest value first, with answer / cause / decision and a `life` link), not-counted with Marg's stock and its MRP value sitting unchecked (and the total), matched, fixes, sheets, links. Routes: `GET /api/pad/report/<root>` · `GET /api/pad/item/<root>/<item>` (`?from=` overrides the FY start) · `GET /page/report[?count=]`. `_pad_brief` carries `report`. |
| `stock_report.html` | **NEW.** English, phone-first, both colour schemes, prints clean. Head (count, status OPEN/CLOSED, who, Marg as-on, after bill, finding numbers, seal line — red when a sealed figure has changed — the four readiness lines), KPI tiles (counted, agree, differ + major, not counted, explained so far), the mismatch at MRP with cost beside, tools (print / result sheet / hand sheet / mismatch data / proofs), a count picker. **1 · Differences** with filters All / Major / Short / Over / Unexplained; a tap opens the life inline (purchases as a table on a wide screen, one line per bill on the phone; totals; Marg by export day; the residue sentence, red when non-zero). **2 · Not counted** with the unchecked value. **3 · Matched** collapsed. **4 · Rows sent back**. |
| `stock_check_live.html` | "Open the STOCK CHECK REPORT" in the box; "Open the report" under each recent count. |

## Decisions
- The report reads the FAMILY (root + parts), newest figure per item — never a single part.
- The life is fetched on tap (lazy), so a 230-line report stays light on a phone.
- The financial year runs from 1 April of the count's year; the window ends on the count's Marg as-on day.
- Units on purchase lines are (qty + free) × pack + loose — Marg's BILL ITEM WISE convention (S224). Where the bill's pack differs from the shop's, the units are approximate and the bill line is shown as written so a person can judge.
- The detector needs two export days; with one it says so rather than guessing.
- Not done here: portal tiles for staff (S225 tile grants) — the report is reached from the count page for now; a per-item ledger page of its own (the life is inline instead).

## Proof
231 checks: 48 (this walk, the residue reproduced from the walk's own arithmetic) + 41 + 65 + 34 + 30 + 13 regressions. Sub-agent screen read fixed the phone-width purchase table before packaging.
