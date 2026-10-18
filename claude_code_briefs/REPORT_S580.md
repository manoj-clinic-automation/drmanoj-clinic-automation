# REPORT S580_SHELF_EXTRA_BILL_PROBE — why the shelf figure is above Marg's by one bill (read-only probe; no repair made)

**For Dr Manoj:**
1. **The extra is not a bill counted twice.** It is a **purchase order that was marked "arrived" when a bill from that supplier was scanned**: the shelf figure then adds the whole ordered quantity of every line of that order that nobody tapped and Marg has not answered — and the test that should drop it once Marg carries the goods looks only for a bill **from the same supplier, dated on or after the order was made**.
2. So it stays wrong when the bill is dated **before** the order (CROCAL and PREGHYPE: Shivaaz bill 3463 of 01-10, the orders were entered 02-10), when the goods came **from another supplier** (PRETOL 8 ordered from Shivaaz, bought from Kedar), or when **Marg shows no such purchase at all** (TOLTRIS PLUS, FLACORT 6, THIO Q AP, LINVIZ 600 and three small Yuvika pieces: either the goods never came with that scanned bill, or the bill is not keyed in Marg).
3. **Today 13 counted items** carry such an extra (TOLTRIS PLUS +500, CROCAL +300, FLACORT 6 +200, PREGHYPE NT TAB +200, PRETOL 8 +100, THIO Q AP +100, LINVIZ 600 +100, COCYP T SYP +10, POWERGESIC +5, four orthotic pieces +1 each). Seven of the brief's thirteen (TRAMATEE, BIO D3 MAX, CHEXID D, NUCOXIA P, SYSFOL 5, FLORA BC CAP, ZIVOPREG M) **closed by themselves this morning** when Marg's export of 18-10 carried their bills — which is how the mechanism is meant to work when Marg's bill comes from the same supplier after the order.
4. **What it touches today:** the ordering pages' stock figure for those 13 items (they would be under-ordered), and a spot count of them would be judged against the inflated figure and marked provisional. **Not touched:** Amir's voucher check — it does not judge an item with an open arrival against the shelf; the gap flags on Darpan's list (no flag is raised by this); Marg's own figure.
5. The repair is a separate kit: drop an order line's "arrived by scan" quantity once Marg's purchase export covers the days after the scan without that item, match a bill by the item (any supplier, a few days before the order too), and put the unanswered scan-tied lines on Amir's "bill entry baaki" line, which today sees tapped lines only.

---

## For the chat

**Probe run:** 18-Oct-2026, 12:48–12:55 IST, on backup-API copies in `/tmp/s580probe/` (finance.db 40,255,488 bytes; spine.db built 12:40:51),
with `stock_figure` as installed by S577 (`stock_figure.py` cb5f24aa…, `shelf_figure.py` a544afda…, `stock_watch.py` bc688521…,
`spine/spine_build.py` e3d3ed85…; `porders.py` a5a823bf…, `order_rules.py` 79f21c1e…, `order_sheet.py` f00f0163…). Nothing written on the box;
`/tmp/s580probe/` removed at the end. The newest usable capture: printed 2026-10-16, taken 2026-10-17 09:20:35 (7f4d5832); the count day's
closing: capture d822f117 (printed 06-09, standing for the end of 05-09). The spine's newest checkable closing: 2026-10-16.

### 1 · The cause, by row — `shelf_figure.scan_arrivals` (class c), never the spine
For every item with an extra, `stock_figure.shelf()` shows the extra in **`arrived`**, nowhere else: `bought` equals the spine's purchase moves
to the unit, `boundary` is 0, the base is the 06-09 count row, and Marg's own move between the count's closing and the newest usable capture
equals the spine's move plus the count's vouchers (**residual 0**) — the spine and Marg agree on these items; the extra is in the shelf arithmetic.
`stock_watch._arrivals` (the tapped lines) contributes nothing to them; **`shelf_figure.scan_arrivals` contributes the whole gap**:

| item | gap (shelf − Marg) | `arrived` | the scan-tied order line behind it (`order_scan_tie.arrived=1`, line `supplied IS NULL`, `billed_qty IS NULL`) | why "not in the spine" |
|---|---|---|---|---|
| TOLTRIS PLUS | +500 | 500 | order 28, SHIVAAZ FORMULATIONS, created 12-10 17:00, 50 strips; tie 28 scanned **14-10 12:46** | Marg has no TOLTRIS purchase after 28-09 (bill 3378); its Oct item-wise export (18-10) has none |
| CROCAL | +300 | 300 | order 10, SHIVAAZ, created 02-10 15:00, 30 strips; tie 10 scanned 03-10 18:29 | the bill is 3463 of **01-10** (240 units) — dated before the order's creation day, so `date >= created` rejects it |
| FLACORT 6 | +200 | 200 | order 25, KEDAR PHARMACEUTICAL, created 12-10 17:00, 20 strips; tie 25 scanned **13-10 11:22** | Marg has no FLACORT purchase after bill 195 of 27-09; Kedar's bills 216 (18-10), A000203, A000213 carry none |
| PREGHYPE NT TAB | +200 | 200 | order 10 (as CROCAL), 20 strips | the bill is 3463 of 01-10 (240 units), before the order's day |
| PRETOL 8 | +100 | 100 | order 10 (SHIVAAZ), 10 strips | PRETOL 8 was bought from **Kedar** (A000203 of 03-10, 90 units) — another supplier key |
| THIO Q AP | +100 | 100 | order 22, DEEPAM PHARMA, created 12-10, 10 strips; tie 22 scanned 12-10 19:37 | Marg has no THIO Q AP purchase after bill 623 of 27-09 |
| LINVIZ 600 | +100 | 100 | order 38, KEDAR, created 16-10, 10 strips; tie 38 scanned 17-10 18:18 | Kedar's bill 216 of 18-10 answered the order's other five lines; LINVIZ 600 is not on it |
| COCYP T SYP | +10 | 10 | order 18, SHIVAAZ, created 06-10, 10; tie 18 scanned 06-10 20:11 | no purchase in Marg |
| POWERGESIC 100 PATCH | +5 | 5 | order 33, DEEPAM, created 16-10, 5; tie 33 scanned 17-10 18:23 | bought under **Janta's** bill 23672 of 18-10 — another supplier key |
| FINGER COT M, SOFT COLLAR NEOLIFE L, SHOULDER IMMOBILISE UNISON L / M (family share) | +1 each | 1 | order 1, YUVIKA, created 26-09; tie 1 scanned 29-09 | Yuvika's bill 672 of 28-09 answered the order's other lines; these pieces are not on it |

**Why each started on the day the old series shows:** the extra appears in the gap set written after the order's scan tie (`order_scan_tie.scan_at`):
FLACORT 6 tie scanned 13-10 11:22 → the 13-10 set (the brief: 87 on 12-10, 277 on 13-10); TOLTRIS PLUS tie scanned 14-10 12:46 → the 15-10 set
(139 on 13-10 was Marg's own lag of the day, 603 on 15-10 is the +500 plus it). The brief's seven items whose gaps **closed this morning**
(TRAMATEE P TAB 15T, BIO D3 MAX, CHEXID D, NUCOXIA P, SYSFOL 5, FLORA BC CAP, ZIVOPREG M) were scan-tied on 16-10 17:45–18:03 (ties 36, 37, 40,
43, 44); Marg's item-wise export of 18-10 09:27 carried their bills (439, 83768, 83907, 19612, 23638, 10807) from the same suppliers dated after the
orders, `porders.detect_supplies` answered the lines (`billed_qty`, `supplied`, `arrived_by='marg'` at 09:40:02) and the spine now carries the
purchases — gap 0 today. That is the mechanism working as S454 4.4 meant it; the thirteen above are the cases it cannot close.

**Equality with "one bill" is partly coincidence.** The extra is always the ORDERED quantity (packs × pack size), not a bill's units: TOLTRIS 50 strips
ordered = bill 3051's 50 strips (the bill also had 10 free, 600 units, so the match was never exact); CROCAL 30 strips ordered = 300, the matched bills
3159 / 3290 were 25 + 5 free each; FLACORT's 20 strips ordered = bill 195's 20 strips.

**Not the causes (a), (b), (d), (e):** no purchase move or line is duplicated for any of the 18 items (the only repeated bill number, Dolonex's 15496,
is two genuine lines of one bill; the KNEE SUPPORT "bill 634 twice" is two sizes of one family on one bill, split by counted share); `boundary` is 0
for all; the base is the count row for all but FENARIC T4 TAB and TYRO BR (spot points, by design); units are tabs throughout (packing × qty + free).

### 2 · How widespread (every counted item, 373)
Gap 0 today: **327**. Gap ≠ 0: **46**, of which:
- **13 from `scan_arrivals`** (the table above; `arrived` > 0, residual 0) — the subject of this probe;
- **16 family shares** (approx; one key, several sizes: the knee immobilisers, LS belts, splints, binders, shoulder immobilisers) — a size's share of
  the family's movement is not that size's own, by design (S577 marks them approx, no verdict);
- **7 spot-point bases** (TYRO BR −328, FENARIC T4 TAB −34, TENDOZAC −14, MEG QCS −10, ONKET DT −9, ZUPRINOR −2, RIB BELT −1): a count after 06-09
  carried forward — the gap is Marg's own open difference since that count (TYRO BR: Marg's residual +200 at 16-10 is the spine's open finding);
- **10 Marg residuals** (DEFVAX 6 −120, KT ROS DT −101, NEWTEL H 40 +30, GLI-ME SR1 +27, VINBACTUM DS −25, ZIBON EXTRA +21, FOLITRAX −6, OSTOVAXL
  DM −4, NORTIMER +4, CCM +1, ANKLE BINDER TYNOR XL +2): Marg moved beyond its sales, purchases and the filed vouchers — KT ROS DT and VINBACTUM DS
  are the two vouchers Marg has not carried (stage C's "do not agree"), DEFVAX / NEWTEL / GLI-ME are open spine findings at 16-10 (190 keys open there).
  These are not this probe's cause; they are the spine's own `sp_finding` rows and the voucher proof's "wrong" rows.
Of the 8 items whose gap equals exactly one of their own post-count bills, 5 are `scan_arrivals` cases and 3 are the KNEE SUPPORT family share.

### 3 · The spine itself
`sp_check` at 2026-10-16 for the 13 items: the spine and Marg differ by exactly the count's filed voucher (TOLTRIS −18, FLACORT −65, CROCAL −48,
PREGHYPE −112, PRETOL 8 0, THIO Q AP 0 …) — the difference S524's proof expects, "OPEN at the latest closing" in `sp_finding` only because the voucher
is not a Marg movement. **The extra is not in the spine**: `sp_move`'s purchases equal `sp_purchase_line`'s to the unit for every item, each bill once,
from the authoritative export (PURCHASE_ITEMWISE 957b473f 01-09..03-10 for September, a8b323b6 01-10..18-10 for October).

### 4 · The functions and lines responsible (live md5s)
- `shelf_figure.py` a544afda07b4632e9bc05e97c256dde6, **`scan_arrivals`** (def line 127): line 137 selects `order_scan_tie.arrived=1 AND l.supplied IS NULL
  AND l.billed_qty IS NULL AND COALESCE(l.missing,0)=0 AND t.scan_at > since` — every untapped, unanswered line of a scan-tied order, for the ORDERED packs
  (`packs × pack_size`, line 150); line 145 drops a line only when `sp_purchase_line` has the key **from that supplier's key, dated ≥ the order's creation
  day**. No expiry: a line stays "arrived, not in Marg" for ever.
- `stock_figure.py` cb5f24aacf7748752206619ce8bbb1e3, `shelf()` (def 599): line 632 `arr = taps(...)` (the tapped lines, `stock_watch._arrivals`), line 634
  `arr += scan_arrivals(...)`, line 646 `v = base − sold + returned + bought + boundary + arr`; `expect_for_point()` line 675 makes the point provisional
  by that `arrived`.
- `stock_watch.py` bc6885217a9f7ca7d8273021fcf6315a, `_arrivals` (def 725): the same supplier-and-date test at line 745 for TAPPED lines (not the cause
  today — every tapped line is answered — but the same narrowness); `bill_pending_lines` (def 896) line 904 reads `l.supplied > 0` only, so a scan-tied
  line with no tap never reaches Amir's "bill entry baaki".
- `porders.py` a5a823bf30661a4bf65ced39b2355500, `detect_supplies` (459–489): answers a line (`billed_qty`, `billed_bill_no`, `supplied`, `arrived_by='marg'`)
  only from a `purchase_line` of the **same vendor key with `bill_date >= the order's creation day`** — the same two blind spots (a bill dated before the
  order; another supplier), so the scan-tied line is never closed by Marg's own bill.
- `order_sheet.py` f00f0163bdd66a074c5af261c9b80a49, line 1594: the tie is written per ORDER (`order_scan_tie.arrived=1`) when a bill of that supplier is
  scanned — it says nothing about which lines came.

### 5 · What a repair must change (no repair made)
1. **An expiry for a scan arrival:** once Marg's purchase exports reach past the scan day (the spine's `reach(sp)['last_pur']` ≥ scan day) and show no
   purchase of the item, the line is "not come / not keyed", not "arrived": its units leave the shelf figure and the line goes to a person (Amir's
   "bill entry baaki" or the owner's line), as `bill_pending_lines` does for tapped lines — extend that reader to `supplied IS NULL` scan-tied lines.
2. **Match the bill by the item, not the supplier and the order day:** `scan_arrivals`, `_arrivals` and `detect_supplies` should accept a purchase of the
   key from any supplier dated within a few days before the order's creation (bill 3463 of 01-10 for orders entered 02-10 15:00) — the order ledger's
   vendor is who was asked, not always who billed.
3. **Per-line, not per-order:** a scan tie marks the order; the shelf should add only lines the scanned bill actually names (the scan's own lines, when the
   asset's bill lines are read), else nothing — the whole-order assumption is the +500 of TOLTRIS.
4. Charter 2: `scan_arrivals`, `_arrivals` and `detect_supplies` carry three copies of the "does Marg carry this arrival" rule; one function in
   `stock_figure` (through `key_of`) should answer all three.

### 6 · Other figures in `stock_figure` the same cause touches
- `shelf()` → `arrived`, `shelf`, `named` for the 13 items; `figures()` (the ordering pages' `_s454_shelf_snap`, the shelf-gap sets' `shelf` and `gap` columns —
  the 12:20 set stores gap +500 for TOLTRIS PLUS, unflagged, because a flag needs Marg's own unexplained move).
- `expect_for_point()` → basis `shelf`, `expected` inflated, `provisional` = the arrived units: a spot count of these items would be written
  provisional and judged high.
- The voucher guard: an item with `arrived != 0` is **not judged against the shelf** (`_voucher_guard`, "not judged" set) — it is counted in the owner's
  "not judged against the shelf for N item(s)" line, never held wrongly. `marg()` and `closing()` are untouched (taps are reported beside the figure,
  never added).
- `stock_watch.expected_units` (the witness) is untouched (no arrivals of these lines: they are untapped).

### Charter
Read only; nothing placed, nothing written outside `/tmp/s580probe/` (removed). Seen, not touched: the whole-order scan tie (S454 4.4) and the three
copies of the "Marg carries it" rule named above; the 190 open spine findings at 16-10 (Marg ≠ spine by the filed vouchers and the known residuals)
are the proof's business, not this probe's.
