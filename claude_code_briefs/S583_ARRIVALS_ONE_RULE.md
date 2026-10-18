# S583_ARRIVALS_ONE_RULE — brief for Claude Code (v3)

*v3: written after an independent read against the post-S577 code (R1 on v1: 4 blockers, 12 corrections; R1 on v2: 2 blockers, 4 corrections; both in `03_WORKING_PAPERS\S324\S583_R1_REVIEW.md`), all folded in below; this text governs. Written 18-Oct-2026 by the Sanjeevni chat (session 324), from `claude_code_briefs/REPORT_S580.md`. Read `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` first. Three Sanjeevni files. No new staff words. The ordering flow (Marg's open order, S543/S561) is not touched.*

## 0 · For the owner

1. **The extra stock goes, in time.** When reception scans a supplier's bill, its order's items count as arrived. That stays, because the ordering side needs it: without it, goods already received would be ordered again. What changes is that each item now **stops counting**:
   - when Marg's purchases show it, by the line's own Marg bill or a matching bill under one rule; or
   - when a purchase report taken a few days later still does not show it.

   TOLTRIS PLUS (+500), FLACORT 6 and THIO Q AP then drop at install. LINVIZ 600 drops when its few days run out on 20-10. CROCAL and PREGHYPE drop because Shivaaz's bill of 01-10 is recognised; PRETOL 8 because Kedar's bill is.
2. **An item that never shows in Marg becomes one line for you, on Needs-you:** *"ITEM: counted as arrived when the VENDOR bill was scanned dd-mm — not in Marg's purchases up to dd-mm"*.
3. **What changes:** the shelf figure of about 13 items, and so their stock on the ordering pages and what a spot count of them is judged against. No staff sentence is new. A spot count that used to be marked "provisional" for such an item can now be judged at once. The install prints each case.

## 1 · Numbers and pins

- Kit **S583_ARRIVALS_ONE_RULE** (board `_numbers` v482 → v483, PLANNED line). No D or F number of its own.
- **FROM pins** (S577's TO pins, installed 12:14 IST 18-Oct; different = STOP):
  - `/root/finance/stock_figure.py` **cb5f24aacf7748752206619ce8bbb1e3**
  - `/root/finance/shelf_figure.py` **a544afda07b4632e9bc05e97c256dde6**
  - `/root/finance/stock_watch.py` **bc6885217a9f7ca7d8273021fcf6315a**
- **Read only — read each live md5 at the open and print it** (the bundle is older than S574/S577):
  - `porders.py` (`detect_supplies`)
  - `order_sheet.py` (the scan tie)
  - `order_rules.py` (`_s470_inputs` ≈2068, `_s470_arrivals` ≈2021–2050)
  - `stock_app.py` (f279a3be)
  - `amir_day.py` (`_d712_owner_lines`)
  - `loss_piles.py` (2b9023fd)
- Service `clinic-finance`, restarted once. The build lock. 08:00–23:59 IST, with the spine green. The parent's `DOCTOR_AUTO_OFF` is set around the restart and removed after healthz 200.

## 2 · What is there now (REPORT_S580 §4 and R1; re-read at the open)

- **`shelf_figure.scan_arrivals`** adds every unanswered line of a scan-tied order at the ordered quantity. It keeps a line only while no spine purchase **from that supplier's key, dated ≥ the order day** exists, and it never expires.
- **`stock_watch._arrivals`** (`in_spine`) and **`bill_pending_lines`** repeat the same test. That is three copies of one rule (charter 2).
- **The order engine on `order.stock_basis=count` (live) relies on the shelf figure.** `order_rules._s470_inputs` (≈2068) drops a counted item's in-transit goods because they are inside its shelf figure. So scan arrivals must stay in the shelf figure (R1-B1).
- **These read `_arrivals.in_spine`, the taps or the arrival** — each is walked:
  - `stock_figure.taps()` → `marg()['taps']` → `expect_for_point`'s marg basis;
  - `stock_figure.shelf()['arrived']` → `expect_for_point`'s provisional and the voucher guard's "open arrival → not judged" (`stock_app` ≈5289);
  - `stock_watch.open_trace`'s finding 2 and its fix *"arrival tapped, bill entry baaki: VENDOR"* (≈1304–1322), shown on Amir's board (`stock_app` ≈8945);
  - `settle_provisional` (≈858);
  - `stock_watch.expected_units` (the S577 witness);
  - `bill_pending_lines`.
- **Marg-answered lines look like taps.** `porders.detect_supplies` sets `supplied`, `arrived_by='marg'` and `arrived_at` (the detection time) and `billed_bill_no`. 49 of 53 `supplied>0` rows are of this kind.
- **An owner line already exists.** `amir_day._d712_owner_lines` names a tapped arrival with nothing scanned (D712).

## 3 · The edits

### 3.1 `stock_figure.py` — ONE rule for "Marg carries this arrival"

- **`carried(con, sp, line, ctx=None)`**. `line` is the dict `_arrivals` yields: `line_id`, `item`, `vendor`, `order_at`, `arrived_at`, `billed_bill_no`, plus `scan_at` for a scan-tied line. It returns the purchase that carries the line (supplier, bill, date, `how`), or None. It reads the spine (`sp_purchase_line`, `ok`-safe); while `sp.ok` is False it returns None. The rule, in order:
  - **(a)** The line's own `billed_bill_no`, Marg's answer by S537 → carried.
  - **(b)** A purchase whose bill is the `billed_bill_no` of **another** order line of the same key never carries this line.
  - **(c)** A purchase of `key_of(item)` dated **before** the order day carries the line only when it is from the order's own vendor key and dated within `arrival.back_days` before the order day.
  - **(d)** A purchase from the order's own vendor key dated **on or after** the order day carries the line, as today.
  - **(e)** A purchase from **another** supplier carries the line only when it is dated **on or after** the order day.
  - The first eligible purchase wins.
  - On the 18-Oct copy this leaves exactly CROCAL and PREGHYPE under (c), and PRETOL 8 and POWERGESIC under (e). The walk prints every line that each of (a)–(e) carries.
- **`expired(con, sp, line, ctx=None)`** → True when `carried()` is None **and** the spine's purchase reach (`reach(sp)`, read once per `Ctx`) has passed the arrival with its grace. That means both:
  - `last_pur` ≥ the arrival day + `arrival.bill_grace_days` (the existing setting);
  - **`stamp_iso(pur_stamp)`** > the arrival moment + that grace. **Never a raw compare of the two clock shapes** (charter 11, R1-C2).

  `covers()` is not used for this. While `sp.ok` is False or `reach` is empty, `expired()` returns False and the arrival keeps counting (charter 1b).
- **`taps(con, sp, name, since_iso, ctx)`:** a tapped line counts while `carried()` is None and `expired()` is False. **A line with `billed_bill_no` is never counted** — Marg answered it (rule a).
- **Edge, named:** a carrying bill dated on or before the count day is already inside the count's base. `carried()` still drops the arrival, which is right: the goods are in the count. Print any such line in the walk.
- **`scan_arrivals` moves here** (from `shelf_figure`) under the same rule. A scan-tied, unanswered line counts its ordered quantity while `carried()` is None and `expired()` is False, the arrival moment being `scan_at`. `shelf()` adds both. Its docstring is updated.
- **`arrivals_open(con, sp, ctx=None)`** → every tapped or scan-tied line that is expired and not carried, without a `billed_bill_no`, with item, units, the arrival moment, who (or "scan"), and vendor.
- **The setting `arrival.back_days`** goes in `stock_watch.SETTINGS` (≈97–106), beside `arrival.bill_grace_days`: kind int, default **2**, lo 0, hi 15, `seed=None`. No row is written. This keeps the kit to three files (R1-C5).

### 3.2 `shelf_figure.py`

- **`scan_arrivals` is removed here.** Its one rule now lives in `stock_figure`. The header (lines 15–16) is updated.
- No other caller remains. Grep `scan_arrivals` across the three files (R1-C9).

### 3.3 `stock_watch.py`

- **`_arrivals`:** `in_spine` = `stock_figure.carried(...) is not None` **only** (R1 on v2, B1). Expiry lives in `taps()` and the scan count, never in `in_spine`. So `open_trace`'s finding 2 and Amir's *"arrival tapped, bill entry baaki"* fix keep seeing a tap that Marg never carried. The other fields are unchanged.
- **`bill_pending_lines`:** its own test is replaced by `carried()`. Its routing, words and grace are unchanged; the walk proves its lines equal for every live line.
- **The owner's line, in `stock_watch.needs_you_lines`** (the Needs-you the owner reads — not `owner_view`, which no page draws; R1-B4). One English line per `arrivals_open` item:
  - *"ITEM: counted as arrived when the VENDOR bill was scanned dd-mm HH:MM — not in Marg's purchases up to dd-mm"*.
- **No duplicate (R1 on v2, B2):** this line names **only lines whose order has a scan tie** (`order_scan_tie`). A tapped line on an untied order stays with `amir_day._d712_owner_lines` (D712), which is not changed.
  - **The gap this leaves, named in the README:** an untied tap where the same supplier has an unrelated scan. D712 skips it and so does this line. It is left for the D712 kit.
  - The walk prints both sets.
- **`open_trace` and Amir's board are unchanged in state** (`in_spine` means carried only). Print that no trace or board fix moves.

### 3.4 What stays (README, and the report's "Charter: left out")

- **Left, with the owner's closure of the ordering flow as the reason:**
  - `porders.detect_supplies` — same vendor, bill date ≥ order day, read from `purchase_line`;
  - `order_rules._s470_arrivals` — same vendor, date ≥ order day.

  These are two remaining copies of the rule. After this kit they can disagree with `carried()` for an uncounted item's transit. Name it for the ordering kit and S486 B.
- **For later:**
  - per-line arrival from the scanned bill's own lines — the Scan App's bill readings;
  - units-based matching, where one bill line answers at most its own units.
- **The record:** the 18-10 `s577_shelf_gap` set (written 12:20) keeps TOLTRIS's +500 as a record, unflagged. The next `end_day`'s set is the first correct one (charter 4, R1-C10).
- **The witness:** `expected_units`' old-way column changes mid-week. Say so in the README; this is 4b-2's start condition.

## 4 · The walk (scratch copies of the live finance.db and spine; never the live files)

**Print first:** every scan-tied unanswered line and every tapped line not answered, each with what (a)–(e) say; the 13 items of REPORT_S580 with `shelf()` before; Darpan's receipt state for each.

**Controls** (red on the old files, green on the new):

1. TOLTRIS PLUS (order 28, scan 14-10, no Marg purchase):
   - counted while inside the grace;
   - **expired** once a purchase export captured after scan + grace reaches past it — it leaves the shelf and is on the owner's line with the words above;
   - the 18-10 09:27 export does this live: print it.
2. CROCAL / PREGHYPE (Shivaaz 3463 of 01-10, order 02-10) → carried by (c).
3. PRETOL 8 (ordered from Shivaaz, Kedar A000203 of 03-10) → carried by (e).
4. **An order-32-style line** whose only earlier bill (467) is order 21's `billed_bill_no` → **not** carried. It goes red on a 7-day any-supplier rule.
5. **A raw-stamp compare goes red** (the `YYYYMMDD-HHMMSS` against the ISO `arrived_at` trap). A tap inside its grace still counts.
6. **The order engine (R1-B1):** for a counted item with a genuine scan-tied line inside its grace, `order_rules`' quantity is equal before and after. For an expired one, the change is printed.
7. **A Marg-answered row** (`arrived_by='marg'`, `billed_bill_no` set) is never counted and never on the owner's line.
8. **`spine` missing:** `carried()` None, `expired()` False, arrivals keep counting.
9. **Owner lines:** no overlap with `_d712_owner_lines`. `bill_pending_lines` is equal before and after for every live line.
10. Darpan's receipt for an item whose arrival expired: rendered and printed (the words are the existing ones; the state may move from provisional to judged).
11. **Grep:** these are empty — `scan_arrivals` in `shelf_figure.py`; a supplier-key test in `_arrivals` / `bill_pending_lines`; a second "carried" rule in the three files.

**Also:**
- the 13 items' shelf figures, old → new;
- the voucher guard's "not judged against the shelf" count, old → new;
- every staff screen's words for amir, darpan, shavez and reception — unchanged, apart from the state changes printed above;
- `py_compile` on both pythons.

## 5 · Install

1. Take the build lock.
2. Check the FROM pins, and print the live md5s of the read-only files.
3. Confirm the spine is green.
4. Back up each file as `.bak_S583_<old8>`.
5. Print the install-day state.
6. Inside `DOCTOR_AUTO_OFF`, place the three files in ONE move (`stock_figure.py` first in the staging).
7. Restart `clinic-finance` once; healthz 200.
8. Read the md5s back.
9. Print the state again. The `order_rules tick` and the 06:30 stock_watch job pick up the new files on their next run.

**Rollback:** restore the three files and restart once.

## 6 · Report — `claude_code_briefs/REPORT_S583.md`

- The usual header.
- The 13 items, old → new.
- The owner's new lines at install (TOLTRIS PLUS and the others expected — print what is).
- The charter section: what is retired (two copies of the rule, `scan_arrivals` moved), what is left (`detect_supplies`, `_s470_arrivals`), and what is left for later.
- Then publish.

*S583 brief v3 · session 324 · 18-Oct-2026 · v1 → R1 (4 blockers, 12 corrections) → v2 → R1 on v2 (2 blockers, 4 corrections) → v3.*
