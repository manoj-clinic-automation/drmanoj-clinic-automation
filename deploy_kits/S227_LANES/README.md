# S227_LANES — the report reads itself (kit A of the loss triage plan)

**The owner, 06-Sep-2026:** less time to read; assess the real store losses after months of sales; what to write off and what to pursue; the count is also a cleanup — items not sold since April marked separately and explained; his work must not grow; a provisional MRP from the data, no MRP homework; "same salt" means the identical salt (D385).

## What changed
| file | what |
|---|---|
| `stock_app.py` | **Price ladder** `_price_p()`: sale price → `stock_mrp_manual` (typed/imported) → last purchase rate ÷ (1 − margin) *provisional* (medicines 20 %, orthotics 30 % by `_is_ortho()` name words) → none. The family's differences become 8-tuples `(…, cost_p, price_p, source)`; the mismatch totals count `mrp_provisional`. **Allowance engine** `_allowance_units()`: 1 % of units sold + 5 % of loose units sold (min 2 when any loose), × a value factor (1 / ½ / ¼ / 0 at unit price < Rs 5 / 20 / 50 / above), × `stock.allowance_scale`, capped at one pack. **Lanes** `_lane_of()` with the reason in words, in this order: dead (kinds A–E) · recount (Marg negative; counted far above Marg; strips/loose swap; exactly one strip) · bill (a multiple of 10 strips with a purchase of that size in the window) · marg (residue ≥ a pack) · over · allowance · loss. **Pairs** (D385): the same `purchase_salt_marg` salt string, one short and one over — proposals only. `_pad_report_data()` carries lanes with totals, pairs, `dead_matched` (matched items nobody sold), `needs_owner`, the owner's running totals, settings. **Routes:** `POST /api/pad/decide` (checker; `{count_id, items[], action, note}`; append-only `stock_diff_lane`; WRITE_OFF / RECOVER / EXPLAINED mirrored to `stock_diff_decision` so the finding page agrees) · `GET /api/pad/cleanup/<root>.xlsx` (Amir's Marg cleanup list: item · Marg figure · new figure · change · decision · voucher reason) · `GET /api/pad/amir/<root>.xlsx` (the no-movement check list, kinds A–E, what to do). One pass each over sale lines and purchase lines per report; the item's residue is read only for the differences. |
| `stock_report.html` | Running totals (written off / to pursue / parked / still open) and a **search box** (filters every item row in every section; opens a lane that matches). The **"Needs your word"** card first — three buttons per item. **Section 1 as eight folding lanes** with number, title, count line and rupee totals; recount, loss and dead open by default; each line shows its reason, badges (MAJOR, kind letter, the owner's word, staff reason, salt pair, "no word yet"), and for the checker a "This line:" row of three fitting words + "more…"; each lane a highlighted "Whole lane, or the ticked lines:" row (a confirm before a whole lane). Lane 7 shows pair proposals with the D385 line. Lane 8 adds the sitting-dead matched items and Amir's two Excel links. `*` marks a provisional price, with a legend line. |
| `stock_check_live.html` | A search box over the recent counts (from 3 counts up); the mismatch line names provisional prices. |
| `pad_receipt.py` | The hand sheet marks a provisional price `(p)` with its own legend line. |

## Decisions
- One lane per line; precedence dead → recount → bill → marg → over → allowance → loss. A reason sentence on every line, so the lane is never a black box.
- Provisional prices are always marked; the unpriced count stays in view.
- The owner's word is append-only; "Reopen" is a new row; the S221 layer is mirrored, never bypassed.
- Salt pairs are proposals (D385); nothing is netted by the server.
- Settings live in `setting` (margins, allowance scale, MAJOR threshold) — nothing needs setting today.
- Not here (kit B): Darpan's paper tranches and the tranche board; (kit C): the Marg behaviour audit, trend and abnormal-purchase flags, the bill checklist, the MRP-list import.

## Proof
272 checks at 390px; see INSTALL.txt. Sub-agent screen reads fixed three things before packaging.
