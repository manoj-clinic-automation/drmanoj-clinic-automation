# S227 BUILD BRIEF — the one document to read instead of the twelve S227 papers

**Session 227 · 06-Sep-2026, 14:15 → 22:00 IST · eight kits, all live, every pin pasted back from the box. Read `S228_BUILD_BRIEF` first — it is the owner's ruling on what comes next; this brief is what is live and why.**

## 1 · What is live (VPS `/root/finance/`, all installed by the owner from one line each)

| kit | what it did | pins after it |
|---|---|---|
| `S227_PAD_PROOF` | every uploaded count sheet kept byte for byte in `pad_uploads/` (+ `INDEX.txt`); a PDF receipt of what the server ingested for the counters; `stock_count_pad_archive`; `pad_receipt.py` NEW | stock_app · check_live · pad_receipt |
| `S227_DIFF_SHEET` | the differences as a landscape hand sheet for Darpan (recount strips/loose, reason legend, remarks, closed boxes; `(p)` provisional); the mismatch at MRP item-wise (`/api/pad/mismatch/<cid>`); padreader/padwriter with the DIFFERENCES tab | padreader `afa8da2f` · padwriter `e7546afe` |
| `S227_FINDING_REPORT` | the analytics layer: every difference against purchases, sales, returns; the inline item life (`_item_life`); Marg by export day; the residue | stock_report NEW |
| `S227_LANES` | the loss triage plan v4 built: eight lanes with a reason per line, the price ladder (`_price_p`), the allowance engine, bulk decisions on append-only `stock_diff_lane` mirrored to the S221 layer, the owner's short list, Amir's two Excel lists, D385 | — |
| `S227_DESK` | the DECISION DESK `/page/desk` (one card, one question); the report read-only; **F-334 / F-335 corrected** (`_purchase_units`, `_dead_exports`, dedupe); the PURCHASE DATA AUDIT (`/api/pad/audit[.xlsx]`); box-gap tolerance; forgiving search | stock_desk NEW |
| `S227_PINPOINT` | `_qw`/`_qws` strips-and-tabs everywhere; the residue export day by export day (`spans`); a late-keyed bill found and settled; ONE question per open span; Amir's lookup list (`/api/pad/lookups/<cid>.xlsx`); the carried-forward card | — |
| `S227_CONCLUSION` | `detector.conclusion/kind/details`; CONCLUSION first, "Show how this was decided"; `_qwd` IN/OUT; the first-write-off-candidates card; **"Send Marg's answer to the server"** (`POST /api/pad/marg_answer/<cid>`, `stock_marg_answer`, `pad_uploads/marg_answers/`) | — |
| `S227_STAFF` | spans MERGED before pinpointing (F-336); consumables lane (`_is_consumable`); orthotics lane + families (`_ortho_family`, `ortho_families`, `/api/pad/ortho/<cid>.xlsx`); Darpan's lists in turns (`stock_tranche`, `/api/pad/tranche/…`, `render_tranche` no rupee); the typing board (`/api/pad/answers/<cid>`); AMIR'S BOARD `stock_amir.html` `/page/amir` (`_amir_board`); the audit workbook actionable only (F-339); "over" explained + same-salt pairs on the desk | **stock_app `8eef6420` · check_live `3d6a2fb8` · report `9be950f2` · desk `f044a5db` · amir `56ed926f` · pad_receipt `a52751f4`** |

Tables created on first request: `stock_count_pad_archive` · `stock_mrp_manual` · `stock_diff_lane` · `stock_marg_answer` · `stock_tranche`. Settings read if present: `stock.margin_med` (0.20) · `stock.margin_ortho` (0.30) · `stock.allowance_scale` (1.0) · `stock.major_p` (100000) · `stock.consumable_words`. Backups on the box `.bak_S227{proof,diff,report,lanes,desk,pin,conc,staff}_20260906`. **`finance_backup.sh` does not include `pad_uploads/` — owed.**

## 2 · The engine, in one paragraph each

**The life and the residue.** For an item in a window, purchases (deduped, replaced exports dropped, units read as Marg means them), sales and returns by day, Marg's closing figure by export day. Between consecutive export days a span's residue = Marg's move − the documents' move. Neighbouring spans with opposite-sign residues are merged (an export taken mid-day); a residue against the window's net or under one strip is noise; a positive residue equal to a bill dated on or before the span (45 days) is a purchase entry keyed after the export — explained; what remains is ONE question for Marg's item ledger. One conclusion line (clean / explained / lookup) and the details behind it.

**The lanes.** Precedence: consume → ortho (family verdict) → recount (Marg negative, far above, strips/loose swapped, exactly one strip, a box with no bill) → bill (about N boxes with a purchase of that size) → marg (an open residue) → over → allowance → loss. Dead kinds A–D for nothing-sold items (E folded into ortho). `needs_owner` = kind B.

**The price ladder.** Sale-line median (both spellings) → `stock_mrp_manual` → purchase rate ÷ (1 − margin), provisional and marked → None. The allowance: 1 % sold + 5 % loose (min 2), × value factor, × scale, capped at a pack.

**Decisions.** `POST /api/pad/decide` {count_id, items, action, note} — WRITE_OFF · RECOVER · EXPLAINED · RECOUNT · PARKED · VERIFY_BILL · MARG_FIX · OPEN — append-only; the newest word per item wins; OPEN clears it.

## 3 · The findings and rulings of the day

F-334 loose = the whole quantity · F-335 overlapping exports · F-336 mid-day exports show a late bill twice · F-337 an item merge leaves Marg's closing stock deficient (VINTAZ P) · F-338 "CAP " in the orthotics list · F-339 a staff sheet carried the server's business. D383 one card / conclusion first · D384 one quantity vocabulary · D385 identical salt · D386 consumables = consumption · D387 Darpan in turns, no rates · D388 adjustment vouchers are the way · D389 the loss desk and the spot counts.

## 4 · Where the walks live

`deploy_kits/S227_STAFF/` holds all ten (`WALK_staff_s227` 27 · `WALK_audit_s227` 53 · `WALK_desk_s227` 47 · `WALK_lanes_s227` 46 · `WALK_report_s227` 45 · `WALK_diff_sheet_s227` 41 · `WALK_pad_proof_s227` 65 · `count_search` 34 · `submit_flow` 30 · `safestore` 13) with the fixtures shaped like the shop's own data (BIO D3 MAX, TOLTRIS, TYRO BR, ROSIKA, LACTOVAX, AXIMAL, the knee supports, the syringes). Run from the kit folder with `python3 -B`; the readiness walk needs the three schema files beside it.
