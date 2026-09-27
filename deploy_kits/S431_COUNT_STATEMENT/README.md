# S431_COUNT_STATEMENT — the count of 06-09-2026 as ONE statement, section by section; orthotics at selling price

**Sanjeevni project · session 283 · 27-Sep-2026 · brief `claude_code_briefs/S431_COUNT_STATEMENT.md` · runs after S430.**

## What the owner said (27-Sep 13:0x IST)
"Better it be section-wise. Now share the complete list of 6th Sept with Marg stock, physical stock and shortages, and the excess items
removed and matched; and the orthotics, not seen by me — are its losses also done? I need orthotic losses to show separately at selling
price. Give me a link for what's ready." "All prices have been worked out, probably in the spine; and Darpan's sheet was well made also."

## What was built
**3.1 One statement, three sections** — `stock_statement.py` (v1.0, mounted the S418 way: `stock_app.py` imports it defensively and its
routes delegate) and `stock_statement.html`. `/finance/stock/page/statement?count=<id>` (+ `/api/statement/<id>`, `.pdf`, `.xlsx`) for the
owner and the doctor (`stock_statement.DOCTORS` = bhawna); staff refused. Sections from the owner's map (`stock_item_section`) in the order
Medicines · Consumables · Orthotics, each with its own totals; within a section the count sheet's order (`stock_count_item.id`). Every
counted line once: the differing lines in the table, the matched under "Matched — N lines" (collapsed, never dropped). Per line: item +
packing · Marg stock on the count day · physical · the confirmed swap partner and the quantity taken out (a not-confirmed pair shows nothing)
· shortage after swaps · excess after swaps · value at SELLING PRICE, short and excess apart · what became of it. Medicines / consumables:
the S427 close's group ("written off — Within the allowance / Small real gap / Old stock / Clinic consumption / Owner's use / Big loss /
Written off before the piles"), "back in store" (the owner's word), "excess — Marg corrected by the vouchers, never a loss", or the open
pile. Orthotics: the owner's word, else Darpan's reason in English, else "open — Darpan's word awaited"; the voucher round or "not yet on a
voucher". Every quantity through `qty_words` (strips + tabs / pcs); the word "units" reaches no screen, PDF or sheet.

**Selling price — one rule for every section** (`price_for`): the spine's **S.RATE** fact as on the count day (the latest non-zero value
with `as_on ≤ 06-09-2026`; a 0.0 is no price), else its **MRP** fact as on the count day, else the S235 rule for `section_map.is_ortho_priced`
items (last purchase rate ÷ 0.70, tag "rule 0.30"), else `stock_rate` ÷ (1 − the section's margin: `stock.margin_ortho` 0.30 / `stock.margin_med`
0.20; tag "rate / margin"), else "no price — name it". Each priced line carries its tag; each section counts and names its unpriced residue.
Spine facts are per strip / piece; the statement divides by the pack for the per-tab price.

**3.2 The orthotic block** at the top of its section, read live from S404's `stockmatch.section_state`: short / excess / net at selling price
· lines still open (Darpan — no answer yet), named and marked on their lines · awaiting the owner's word (answered, still moving Marg
without his word) · not yet on a voucher · renames unverified · the section's verdict. Nothing on the statement decides anything.

**3.3 Freeze this statement** (the owner, one tap, `POST /api/statement/<id>/freeze`): a `stock_statement` row (count, made_at, made_by, the
frozen JSON, its md5, the totals JSON, the PDF and XLSX names) with the files under `pad_uploads/statements/<md5>.pdf|.xlsx` beside the
database (the S227 discipline), audited. The hub's links point at the latest frozen copy "as at <time> by <who>"; a later freeze is a new
row and the earlier stays listed on the page (newest first). `/api/statement/frozen/<sid>.pdf|.xlsx|.json` serve a frozen copy (rebuilt
from the frozen JSON if its file is gone). The PDF is portrait in Darpan's-sheet style (`pad_receipt._Doc`): one section a heading, its
totals first, then the differing lines with a second line each (swap · what became of it · voucher · price and its source), the matched at
the end. The XLSX (`padwriter.workbook_bytes_multi`): Totals + one sheet a section, every line (matched flagged).

**3.4 Hub and old report.** `stock_hub.html`'s first card gains "The count statement — section by section" (page · PDF · Excel, the frozen
copy "as at") above "The count — full report"; the status card's group list names old stock and owner's use (S430). `stock_report.html`
keeps its route; its "N lines still need a word — Open the decision desk" block reads "Closed on <date> by <who> — see the statement" with
the statement link, and the tools gain the link; `_pad_report_data`'s links carry `statement`.

**Calls made where the brief left room:** a new `stock_statement.py` mounted the S418 way rather than routes inside `stock_app.py` (said
here as the brief asked); the doctor role is the user `bhawna` (the medical unit's viewer beside the owner) — widen `DOCTORS` when the chat
names another; the "closed on" date on the old report is the count's own close (`stock_count_close`, 06-09-2026 by manoj) — the S427 write-off
close (27-Sep 12:58) is on the statement's own close line; the desk's MRP figures of the close (₹64,678.78 / 136 lines) are shown as the
close's line, the statement's own rupees are at selling price; a line the desk holds open is marked "open" and priced like any other.

## Pins (FROM read on the box 27-Sep-2026 20:51 IST after S430 → TO; built by `make_s431.py` from the live bytes, anchored edits)
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_app.py (S428's TO, unchanged by S430) | 0e0fc043c4bbae75c6f1fc8149547cb7 | 2a95e2543330b3efbdb0dc0106892bea |
| /root/finance/stock_hub.html (S427's TO) | 74ea06997b900e9f55c47dca473a9232 | 38e0537cd7d1eb3fb40d1a5a0b7df0e5 |
| /root/finance/stock_report.html (S226/S227) | bd750dc8a32c0ed6baf66f48d7114c90 | 610169c04c4de54724fb4e754d572eab |
| /root/finance/stock_statement.py (NEW, v1.0) | — | 85ec7619d79c7a9f311f7bed91eeabae |
| /root/finance/stock_statement.html (NEW) | — | 175f4654a88e6bb81d0fd724be6d93c4 |

Read only, not touched: `section_map.py` 9bf9b98f, `stockmatch.py` df5501ea, `loss_piles.py` 3720b2e1, `qty_words.py`, `pad_receipt.py`,
`padwriter.py`. Restarts `clinic-finance` only. `finance.db` is backed up first; no data is written by the install (the `stock_statement`
table is created on the first read; a freeze is the owner's tap).

## Proof
`walk_s431.py` — the REAL patched app over SCRATCH copies of the live database and the spine, crafted W431 rows found by key: three
sections in order; all 373 counted lines exactly once (+ 4 crafted), each in its map's section, Medicines in count-sheet order, the
sections' line counts (288 / 19 / 70); every confirmed pair reduces both partners by the quantity, a line wholly explained sits under
Matched reading "swap confirmed", GEMCAL XT ↔ ZIBON EXTRA in strips + tabs, the not-confirmed LACTOVAX pairs show nothing; the run's 122
lines read "written off — <group>" group by group, the close's totals 136 lines / ₹64,678.78 / back 6 (named) / groups 34-53-22-6-5-2 + 14
earlier, the excess lines "never a loss"; every differing line priced with a tag or counted unpriced, the sections' totals add up, the
overall is their sum, the source counts; crafted: an orthotic with a purchase rate and no spine fact → the 0.30 rule (₹1,000 a pc, ₹2,000),
a S.RATE item (its 0.0 ignored, MRP loses) → ₹12 a tab, an MRP-only item (a later S.RATE ignored) → ₹20 a tab, an unpriced item named in
the residue; the orthotic totals apart; the block equals `section_state` live, the open lines marked; the PDF (order, totals first, matched
at the end, no "units"), the XLSX (Totals + three sheets, the brace with its tag); Freeze → one row with md5, PDF and XLSX on disk, the
frozen totals equal the live, the frozen copy serves (PDF/XLSX/JSON), audited; a second freeze a second row, listed newest first; the
hub's links (live + frozen "as at"), the hub page's card and group labels; the old report closed with the statement link and no
decision-desk pointer; the owner freezes, the doctor reads and cannot freeze, bhati / darpan / shavez refused; 404 for a count that is not
there. **Negative control:** the same scenario on the box as it is goes red (no statement route, the pointer still there). Then **S430's**,
**S427's** (S430 adjustments) and **S428's** (S430 adjustment) walks on the pre-close backups and **S404's** walk re-run on the patched files,
each against its own pre-kit control. `figures_s431.py` prints the statement's figures for the report.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S431_COUNT_STATEMENT/install_S431_COUNT_STATEMENT.sh
```
Undo: put back the three `.bak_S431_<from8>` files, remove `stock_statement.py` and `stock_statement.html`, `systemctl restart clinic-finance`,
healthz 200. A frozen statement's rows and files are data and stay.
